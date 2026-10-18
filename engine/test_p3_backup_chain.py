"""N-P3-01: real local Git increment, continuation, fault and restore tests."""
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
import durable_delivery as durable
import github_freshness
import p3_backup_chain as b
import p3_capacity_fixture as fixture
from production_contract import canonical,digest
from test_github_delivery import fails
from test_p3_operations import healthy_fixture


@contextmanager
def setup():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);f=fixture.create(root/'fixture',simple_count=12)
        def append(target=None,fault=None):
            p=f['pins'][-1]
            return b.append_local(f['source'],f['identity']['branch'],p['pin'],p['revision'],
                f['identity'],f['migration'],target or root/'chain',fault=fault)
        with patch.object(b,'MAX_COMMITS',4):yield root,f,append


def restore(root,f,m,name='restore'):
    pin=f['pins'][-1]
    return b.restore_verified(root/'chain',m,root/name,pin['pin'],pin['revision'],f['identity'])


def test_v2_real_incremental_history_restore_and_no_old_package_rewrite():
    with setup() as (root,f,append):
        end=f['pins'][-1];budget=b.Budget();repo=f['source']
        early=b.git(repo,budget,'rev-parse',end['pin']+'~6').decode().strip()
        b.git(repo,budget,'update-ref','refs/heads/'+f['identity']['branch'],early)
        first=b.append_local(repo,f['identity']['branch'],early,5,f['identity'],f['migration'],root/'chain')
        old={p.relative_to(root/'chain').as_posix():b.sha(p) for p in (root/'chain/packages').rglob('*') if p.is_file()}
        b.git(repo,budget,'update-ref','refs/heads/'+f['identity']['branch'],end['pin'])
        m=append()['manifest']
        assert m['history_count']==12 and m['package_count']==4
        assert all(b.sha(root/'chain'/n)==h for n,h in old.items())
        r=restore(root,f,m);assert r['mode']=='blocked' and r['history_count']==12
        with durable.read_only_volume(root/'restore/blocked-store',f['identity']['store_id']) as s:
            assert s.snapshot['control']['health']['restore_requires_reconciliation']
            assert s.snapshot['control']['health']['completed_runs']=={}
        assert int(b.git(root/'restore/verification-repository',budget,'rev-list','--count',end['pin']))==12


def test_v2_missing_intermediate_and_reordered_parts_fail():
    for mode in ('missing','swapped'):
        with setup() as (root,f,append):
            m=append()['manifest'];one=root/'chain/packages/000001';two=root/'chain/packages/000002'
            one.rename(root/'removed')
            if mode=='swapped':two.rename(one);(root/'removed').rename(two)
            fails(ValueError,lambda:restore(root,f,m))
            assert not (root/'restore').exists()


def test_v2_manifest_hash_predecessor_identity_and_stale_pin_fail():
    for field,value in [('previous_manifest_sha256','f'*64),('parent_pin','f'*40),
                         ('history_sha256','e'*64),('first_revision',999)]:
        with setup() as (root,f,append):
            m=append()['manifest'];p=root/'chain/packages/000001/segment.json'
            data=b.read_json(p);data[field]=value;p.write_text(canonical(data)+'\n',encoding='utf-8',newline='\n')
            fails(ValueError,lambda:restore(root,f,m))
    with setup() as (root,f,append):
        m=append()['manifest'];end=f['pins'][-1]
        fails(ValueError,lambda:b.restore_verified(root/'chain',m,root/'old','f'*40,end['revision'],f['identity']))
        fails(ValueError,lambda:b.restore_verified(root/'chain',m,root/'old',end['pin'],end['revision']+1,f['identity']))
        wrong={**f['identity'],'repo':'foreign/repo'}
        fails(ValueError,lambda:b.restore_verified(root/'chain',m,root/'wrong',end['pin'],end['revision'],wrong))
        p=root/'chain/packages/000001/history.bundle';p.write_bytes(p.read_bytes()+b'corrupt')
        fails(ValueError,lambda:restore(root,f,m))


def test_v2_rehashed_bundle_dependency_and_digest_forgery_fail():
    with setup() as (root,f,append):
        m=append()['manifest'];p=root/'chain/packages/000001';d=b.read_json(p/'segment.json')
        raw=(p/'history.bundle').read_bytes();raw=raw.replace(d['parent_pin'].encode(),b'f'*40,1)
        (p/'history.bundle').write_bytes(raw);d['files']=b.inventory(p)
        (p/'segment.json').write_text(canonical(d)+'\n',encoding='utf-8',newline='\n')
        # Recompute outer checksums: the underlying Git prerequisite must still fail.
        n=root/'chain/packages/000002/segment.json';last=b.read_json(n);last['previous_manifest_sha256']=digest(d)
        n.write_text(canonical(last)+'\n',encoding='utf-8',newline='\n')
        manifests,total=b.load_segments(root/'chain',f['identity']);m=b.set_manifest(manifests,total)
        fails(ValueError,lambda:restore(root,f,m))


def test_v2_interrupted_publication_resumes_without_false_completion():
    for phase in ('before_package_publish','after_package_publish','before_full_restore','before_completion_publish'):
        with setup() as (root,f,append):
            def fault(event):
                if event==phase:raise InterruptedError('synthetic interruption')
            fails(InterruptedError,lambda:append(fault=fault))
            assert not list((root/'chain/completions').iterdir())
            m=append()['manifest'];assert restore(root,f,m)['history_count']==12


def test_v2_real_worker_loss_preserves_owner_and_requires_review():
    with setup() as (root,f,append):
        plan={**f,'out':str(root/'chain')};b.write_json(root/'plan.json',plan)
        script="import json,sys,os;sys.path.insert(0,sys.argv[1]);import p3_backup_chain as b;p=json.load(open(sys.argv[2]));q=p['pins'][-1];b.append_local(p['source'],p['identity']['branch'],q['pin'],q['revision'],p['identity'],p['migration'],p['out'],fault=lambda e:os._exit(71) if e=='after_package_publish' else None)"
        env={k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_','GH_','TELEGRAM_','BTC_DELIVERY_'))}
        r=subprocess.run([sys.executable,'-c',script,str(b.ROOT/'tools'),str(root/'plan.json')],env=env,capture_output=True,timeout=30)
        assert r.returncode==71,r.stderr
        assert (root/'chain/.writer-lock').exists() and not list((root/'chain/completions').iterdir())
        fails(FileExistsError,append)
        # Explicit test operator review after positively observed child exit.
        (root/'chain/.writer-lock').unlink()
        with patch.object(b,'MAX_COMMITS',256):assert append()['manifest']['history_count']==12


def test_v2_package_processing_total_memory_and_time_limits_fail_closed():
    for name,limit in [('MAX_PACKAGE',1),('MAX_UNPACKED',1),('MAX_SEGMENTS',1),
                       ('MAX_SET_BYTES',1),('MAX_PYTHON_RSS',1),('TOTAL_SECONDS',-1)]:
        with setup() as (root,f,append),patch.object(b,name,limit):
            fails(ValueError,append)
            assert not (root/'chain/completions').exists() or not list((root/'chain/completions').iterdir())
    with setup() as (root,f,append):
        with patch.object(b,'MAX_UNPACKED',35000):m=append()['manifest']
        assert m['package_count']==6 and restore(root,f,m)['history_count']==12


def test_v2_git_subprocess_deadline_kills_hung_step():
    with setup() as (root,f,append),patch.object(b,'STEP_SECONDS',.1):
        def hung():
            with b.process(f['source'],['hash-object','--stdin'],b.Budget()) as p:
                time.sleep(.25);p.stdout.read()
        fails(ValueError,hung)


def test_v2_memory_sampler_does_not_accumulate_ctypes_structures():
    before=b.rss(os.getpid())
    for _ in range(20000):b.rss(os.getpid())
    assert b.rss(os.getpid())-before<8*b.MIB


def append_body(repo,branch,body,parent=None):
    msg=b'Synthetic boundary only\n'
    stream=f'blob\nmark :1\ndata {len(body)}\n'.encode()+body+b'\n'
    stream+=f'commit refs/heads/{branch}\ncommitter Offline P3 <synthetic@example.invalid> 1800000000 +0000\ndata {len(msg)}\n'.encode()+msg
    if parent:stream+=f'from {parent}\n'.encode()
    stream+=b'M 100644 :1 delivery/stream.json\n\ndone\n'
    with b.process(repo,['fast-import','--quiet'],b.Budget()) as p:
        p.stdin.write(stream);p.stdin.close();p.stdout.read()
    return b.git(repo,b.Budget(),'rev-parse','refs/heads/'+branch).decode().strip()


def test_v2_real_body_byte_boundary_and_omitted_seed_stop():
    with setup() as (root,f,append):
        old=f['pins'][-1];repo=f['source'];identity=f['identity']
        env=json.loads(b.git(repo,b.Budget(),'show',old['pin']+':delivery/stream.json'))
        env['revision']+=1;env['parent_digest']=env['body_digest'];env['write_id']='boundary'
        env['snapshot']['control']['health']['synthetic_padding']=''
        env['body_digest']=digest(env['snapshot'])
        env['snapshot']['control']['health']['synthetic_padding']='x'*(b.github.MAX_BYTES-len(canonical(env).encode()))
        env['body_digest']=digest(env['snapshot']);body=canonical(env).encode()
        assert len(body)==b.github.MAX_BYTES
        pin=append_body(repo,identity['branch'],body,old['pin']);f['pins'][-1]=dict(pin=pin,revision=env['revision'])
        m=append()['manifest'];assert restore(root,f,m)['history_count']==13
        env['parent_digest']=env['body_digest'];env['revision']+=1
        env['snapshot']['control']['health']['synthetic_padding']+='x';env['body_digest']=digest(env['snapshot'])
        body=canonical(env).encode();assert len(body)==b.github.MAX_BYTES+1
        pin=append_body(repo,identity['branch'],body,pin);f['pins'][-1]=dict(pin=pin,revision=env['revision'])
        before=list((root/'chain/completions').iterdir());fails(ValueError,append)
        assert list((root/'chain/completions').iterdir())==before
        other=root/'omitted-seed';other.mkdir();b.git(other,b.Budget(),'init','--bare','-b',identity['branch'])
        env['snapshot']['control']['health']['synthetic_padding']='';env['body_digest']=digest(env['snapshot'])
        pin=append_body(other,identity['branch'],canonical(env).encode())
        fails(ValueError,lambda:b.append_local(other,identity['branch'],pin,env['revision'],identity,f['migration'],root/'bad-chain'))


def test_v2_restore_preserves_uncertainty_and_never_activates_delivery():
    import telegram_outbox as box
    with setup() as (root,f,append):
        old=f['pins'][-1];identity=f['identity'];repo=f['source']
        env=json.loads(b.git(repo,b.Budget(),'show',old['pin']+':delivery/stream.json'))
        env['revision']+=1;env['parent_digest']=env['body_digest'];env['write_id']='interrupted-delivery'
        d=dict(version=1,messages=[],signals={'signals':[]},oi_history=[])
        box.enqueue(d,'synthetic','uncertain',0,dict(text='fixture'),'fixture')
        d['messages'][0].update(status='sending',attempts=1,target='a'*64)
        env['snapshot']['commands']['pending']=dict(result='fixture',_delivery=d)
        env['body_digest']=digest(env['snapshot'])
        pin=append_body(repo,identity['branch'],canonical(env).encode(),old['pin'])
        f['pins'][-1]=dict(pin=pin,revision=env['revision']);m=append()['manifest'];restore(root,f,m)
        with durable.read_only_volume(root/'restore/blocked-store',identity['store_id']) as s:
            assert s.snapshot['control']['mode']=='blocked'
            assert s.snapshot['control']['owner'] is None
            assert s.snapshot['commands']['pending']['_delivery']['messages'][0]['status']=='uncertain'


def test_v2_monitor_rejects_v1_local_only_and_incomplete_chain_receipts():
    with healthy_fixture() as f:
        f['policy']['backup_store']=dict(repo='synthetic/backup',branch='only',receipt_path='receipt.json')
        with setup() as (root,fixture_data,append):
            m=append()['manifest']
            receipt=dict(schema='p3-verified-backup-receipt-v2',status='confirmed',manifest=m,
                manifest_sha256=digest(m),verified_chain_sha256=m['chain_sha256'],
                verified_source_pin=m['pin'],verified_source_revision=m['revision'],
                upload_readback_verified=True,history_verified=True,restore_blocked_verified=True,
                expected_start_ms=f['base'],verified_ms=f['now'])
            class Client:
                def read(self,*args):return dict(body=canonical(receipt).encode(),commit_sha='b'*40)
            assert github_freshness.read_backup(Client(),f['policy'])['source_revision']==11
            for field,value in [('schema','p3-verified-backup-receipt-v1'),('schema','p3-local-backup-verification-v2'),
                ('verified_chain_sha256','f'*64),('verified_source_pin','f'*40),('verified_source_revision',10),
                ('upload_readback_verified',False)]:
                old=receipt[field];receipt[field]=value
                fails(ValueError,lambda:github_freshness.read_backup(Client(),f['policy']))
                receipt[field]=old
