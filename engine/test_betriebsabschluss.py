"""New focused offline cases only; actual entry/HTTP clients/local Git paths."""
from contextlib import contextmanager
from copy import deepcopy
from functools import lru_cache
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import urllib.parse
from unittest.mock import patch

import actions_delivery as actions
import actions_schedule as slots
import actions_freshness as monitor
import durable_delivery as durable
import github_delivery as github
import run_health
import telegram_notify as tg
import telegram_outbox as box
from production_contract import canonical,digest
from github_freshness import ReadBudget,iso
from test_actions_delivery import fixture,invoke,entry,ROOT
from test_github_delivery import fails
import p3_capacity_fixture as capacity
import p3_backup_chain as b
import p4_backup_pair as pair

ARTIFACT_ROOT=None


def blob(raw): return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def commit_file(repo,branch,path,raw,parent=None):
    repo=Path(repo);budget=b.Budget()
    if not repo.exists(): repo.mkdir();b.git(repo,budget,'init','--bare')
    text=b'synthetic local evidence\n'
    data=f'blob\nmark :1\ndata {len(raw)}\n'.encode()+raw+b'\n'
    data+=f'commit refs/heads/{branch}\nmark :2\ncommitter Offline <synthetic@example.invalid> 1700000000 +0000\ndata {len(text)}\n'.encode()+text
    if parent: data+=f'from {parent}\n'.encode()
    data+=f'M 100644 :1 {path}\n\nget-mark :2\ndone\n'.encode()
    with b.process(repo,['fast-import','--quiet'],budget) as p:
        p.stdin.write(data);p.stdin.flush();pin=p.stdout.readline().decode().strip()
    assert b.HEX40.fullmatch(pin)
    return pin


def metadata(kind,slot,rid='100',number=10,explicit=False):
    return dict(id=int(rid),run_attempt=1,run_number=number,event='workflow_dispatch',
        repository={'full_name':'synthetic/code'},path='.github/workflows/'+kind+'.yml',
        head_sha='a'*40,head_branch='synthetic',created_at=iso(slot+500),
        run_started_at=iso(slot+750),updated_at=iso(slot+3000),status='completed',conclusion='success',
        display_title='btc-v2:'+kind+':'+(str(slot) if explicit else 'created'))


@contextmanager
def actual_entry(kind='signal',phase=2,delay=1000,explicit=False):
    with fixture() as (root,data,path,runtime,http):
        slot=1791100800000+phase*slots.MINUTE
        meta=metadata(kind,slot,explicit=explicit)
        original=http.open
        def open_request(request,timeout):
            if '/actions/runs/100' in request.full_url:
                http.seen.append((request.get_method(),request.full_url,timeout))
                return io.BytesIO(json.dumps(meta).encode())
            return original(request,timeout)
        env={'BTC_DELIVERY_WORKFLOW':meta['path'],'GITHUB_WORKFLOW_REF':'synthetic/code/'+meta['path']+'@refs/heads/synthetic',
             'BTC_ACTIONS_METADATA_READ_TOKEN':'synthetic-read',
             'BTC_ACTIONS_EXPLICIT_START_MS':str(slot) if explicit else '',
             # Deliberately stale caller value: must be replaced from actual metadata.
             'BTC_DELIVERY_EXPECTED_START_MS':str(slot+4*slots.HOUR)}
        with patch.dict(os.environ,env),patch.object(actions.ActionsClient,'open_request',side_effect=open_request),\
             patch.object(entry.time,'time',return_value=(slot+delay)/1000):
            yield root,data,path,runtime,http,meta,slot


def test_entry_delayed_start_keeps_creation_slot_and_explicit_phase32():
    for phase,explicit in ((2,False),(32,True)):
        with actual_entry(phase=phase,delay=3*slots.MINUTE,explicit=explicit) as (_,data,path,_,http,meta,slot):
            result=invoke(path,data)
            f=json.loads(http.file(actions.FENCE_PATH))
            assert int(f['run']['expected_start_ms'])==slot
            assert result['get']==sum(x[0]=='GET' for x in http.seen)
            assert result['get']<=640 and result['put']<=50


def test_entry_wait_expiry_foreign_metadata_and_lost_original_phase_refused_before_put():
    with actual_entry(delay=4*slots.HOUR) as (_,data,path,_,http,_,_):
        fails(ValueError,lambda:invoke(path,data));assert http.puts==0
    for field,value in (('head_sha','f'*40),('run_attempt',2),('path','.github/workflows/watch.yml')):
        with actual_entry() as (_,data,path,_,http,meta,_):
            meta[field]=value;fails(ValueError,lambda:invoke(path,data));assert http.puts==0


def test_entry_watch_phase_real_entry_and_pending_cas_no_takeover():
    with actual_entry('watch',8,delay=2*slots.MINUTE) as (_,data,path,_,http,meta,slot):
        start=slot//(4*slots.HOUR)*(4*slots.HOUR)-30*4*slots.HOUR
        raw=[[start+i*14400000,100,101,99,100,0,start+(i+1)*14400000-1] for i in range(31)]
        entry.run_runtime(path,'watch',data,watch_raw=raw,now_ms=slot+2*slots.MINUTE)
        assert json.loads(http.file(actions.FENCE_PATH))['phase']=='closed'
    with actual_entry() as (_,data,path,_,http,_,_):
        http.mode='cas';http.selected_path=actions.FENCE_PATH
        fails(github.StoreConflict,lambda:invoke(path,data));assert http.puts==1
        assert not any('/contents/'+github.STORE_PATH in url and method=='PUT' for method,url,_ in http.seen)


def test_schedule_phases_deadline_edges_and_queue_templates():
    base=1791100800000
    assert slots.deadline('signal',base+2*slots.MINUTE)==base+45*slots.MINUTE
    assert slots.deadline('signal',base+32*slots.MINUTE)==base+45*slots.MINUTE
    assert slots.deadline('watch',base+8*slots.MINUTE)==base+23*slots.MINUTE
    assert slots.due_slots('signal',base+45*slots.MINUTE,base+2*slots.MINUTE)==[base+2*slots.MINUTE,base+32*slots.MINUTE]
    assert slots.due_slots('watch',base+23*slots.MINUTE,base+8*slots.MINUTE)==[base+8*slots.MINUTE]
    m=metadata('watch',base+8*slots.MINUTE)
    assert slots.bind('watch',m,base+23*slots.MINUTE)==base+8*slots.MINUTE
    fails(ValueError,lambda:slots.bind('watch',m,base+23*slots.MINUTE+1))
    for kind in ('signal','watch','lage','pages'):
        text=(ROOT/'ops/produktion'/f'{kind}-workflow.disabled.yml').read_text()
        assert 'queue: max' in text and 'cancel-in-progress: false' in text and 'if: ${{ false }}' in text
        assert 'now//slot' not in text
    # Provider overflow/reordering has no execution guarantee: a missing phase
    # and queued/failed runs are tested against the real monitor below.


@lru_cache(maxsize=1)
def example():
    root=Path(ARTIFACT_ROOT);root.mkdir(parents=True,exist_ok=False)
    f=capacity.create(root/'source-fixture',simple_count=2)
    budget=b.Budget();repo=Path(f['source']);end=f['pins'][-1]
    with b.batch(repo,budget) as read: _,raw,env=b.inspect(read,end['pin'],f['identity'],b.parser(f['identity']))
    w=capacity.GitWriter(repo,raw);w.revision=env['revision'];w.pin=end['pin'];w.prior_digest=env['body_digest']
    c=w.snapshot['control'];base=c['migration']['W']+2*slots.SPECS['signal'][0]
    w.snapshot['engine']['last_signal_ts']=base-4*slots.HOUR
    runtime=json.loads((ROOT/'ops/produktion/github-actions-runtime.disabled.json').read_text())
    runtime.update(code_repository='synthetic/code',code_ref='refs/heads/synthetic',
        private_store_repository=f['identity']['repo'],store_branch=f['identity']['branch'],fence_branch='actions-fence',
        store_id=f['identity']['store_id'],code_sha=c['code_sha'],config_sha256=c['config_sha256'],
        bot_identity=c['bot_identity'],activation_review_sha256='b'*64)
    from offline_test_fixtures import sender_access
    access,_,_=sender_access(runtime);runtime['public_access_sha256']=digest(access)
    d=entry.deployment(runtime)
    fence=json.loads(actions.seed_fence(d));fence_repo=root/'fence-source'
    fence_pin=commit_file(fence_repo,d['fence_branch'],actions.FENCE_PATH,canonical(fence).encode());fence_rev=0
    metas=[];numbers={'signal':0,'watch':0}
    w.start()
    # Retained command, message and receipt are part of EVERY later snapshot.
    command={'result':'synthetic-only','_delivery':{'version':1,'messages':[],'signals':{'signals':[]},'oi_history':[]}}
    box.enqueue(command['_delivery'],'test','retained',0,{'text':'synthetic receipt'},'synthetic receipt')
    command['_delivery']['messages'][0].update(status='confirmed',attempts=1,target=c['target_binding'],receipt=73)
    w.snapshot['commands']['retained-command']=command;w.commit()
    for i,(kind,minute) in enumerate((('signal',2),('watch',8),('watch',23),('signal',32),('watch',38),('watch',53))):
        slot=base+minute*slots.MINUTE;rid=str(100+i);numbers[kind]+=1
        meta=metadata(kind,slot,rid,numbers[kind]);metas.append(meta)
        run=dict(number=numbers[kind],id=rid,attempt='1',workflow=meta['path'],kind=kind,
                 expected_start_ms=str(slot),deadline_utc_ms=slot+15*slots.MINUTE)
        fence=deepcopy(fence);fence.update(phase='open',run=run,completion=None,write_id='synthetic-open-'+rid)
        fence['cursors'][meta['path']]={'number':numbers[kind],'id':rid}
        fence_pin=commit_file(fence_repo,d['fence_branch'],actions.FENCE_PATH,canonical(fence).encode(),fence_pin);fence_rev+=1
        w.owner=dict(repository='synthetic/code',run_id=rid,run_attempt='1',nonce=digest(rid)[:32])
        c['owner']=deepcopy(w.owner);w.commit()
        with patch.dict(os.environ,capacity.run_env(kind,slot,rid)):
            run_health.record_event(w,kind,'start',slot+1000,None);capacity.finish(w,kind,slot)
        c['owner']=None;w.commit()
        fence.update(phase='closed',write_id='synthetic-close-'+rid,completion={'stream':w.confirmed_record()})
        fence_pin=commit_file(fence_repo,d['fence_branch'],actions.FENCE_PATH,canonical(fence).encode(),fence_pin);fence_rev+=1
    w.stop()
    pins={'stream':{'commit_sha':w.pin,'revision':w.revision,'blob_sha':w.blob,'snapshot_digest':w.prior_digest},
          'fence':{'commit_sha':fence_pin,'revision':fence_rev,'blob_sha':blob(canonical(fence).encode()),'body_sha256':digest(fence)}}
    plan=dict(stream_source=str(repo),fence_source=str(fence_repo),migration=f['migration'],identity=f['identity'],
              deployment=d,pins=pins,out=str(root/'pair'))
    b.write_json(root/'plan.json',plan);b.write_json(root/'required-pins.json',pins)
    with patch.object(b,'MAX_COMMITS',4):
        result=pair.append(plan)
        # Fresh process-like restore from packages only, independent pins.
        restore=pair.restore(root/'pair',result['manifest'],root/'fresh-blocked',pins)
    b.write_json(root/'manifest.json',result['manifest']);b.write_json(root/'fresh-restore-result.json',restore)
    return dict(root=root,plan=plan,result=result,metas=metas,base=base,fence=fence,
                stream_body=w.body,fence_body=canonical(fence).encode())


def test_backup_real_two_histories_full_bytes_commands_cursors_and_fresh_blocked():
    f=example();root=f['root'];m=f['result']['manifest'];p=f['plan']
    assert m['stream']['history_count']==p['pins']['stream']['revision']+1
    assert m['fence']['history_count']==13 and m['stream']['package_count']>1 and m['fence']['package_count']>1
    assert (root/'fresh-blocked/actions-fence.original.json').read_bytes()==f['fence_body']
    with durable.read_only_volume(root/'fresh-blocked/stream/blocked-store',p['identity']['store_id']) as store:
        assert store.snapshot['control']['mode']=='blocked'
        assert store.snapshot['control']['health']['successful_runs']=={}
        assert store.snapshot['commands']['retained-command']['_delivery']['messages'][0]['receipt']==73
    for kind,repo in (('stream',root/'fresh-blocked/stream/verification-repository'),('fence',root/'fresh-blocked/fence-verification-repository')):
        original=Path(p[kind+'_source']);pin=p['pins'][kind]['commit_sha'];path=github.STORE_PATH if kind=='stream' else actions.FENCE_PATH
        for commit in b.commits(original,pin,None,b.Budget()):
            assert b.git(original,b.Budget(),'show',commit+':'+path)==b.git(repo,b.Budget(),'show',commit+':'+path)


def test_backup_missing_old_foreign_increments_and_tampered_hashes_refused():
    f=example();m=f['result']['manifest'];root=f['root']
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        for mode in ('missing-stream','missing-fence','foreign','old-pin','corrupt'):
            candidate=td/mode;candidate.mkdir();mm=deepcopy(m);source=root/'pair'
            if mode.startswith('missing') or mode=='corrupt':
                source=candidate/'pair';shutil.copytree(root/'pair/stream',source/'stream');shutil.copytree(root/'pair/fence',source/'fence')
                kind='stream' if mode=='missing-stream' else 'fence'
                path=source/kind/'packages/000001/history.bundle'
                if mode=='corrupt': path.write_bytes(path.read_bytes()+b'corrupt')
                else: path.rename(candidate/'retained-missing-part.bundle')
            if mode=='foreign': mm['deployment']['private_store_repository']='foreign/repo'
            pins=deepcopy(f['plan']['pins'])
            if mode=='old-pin': pins['fence']['revision']-=1
            with patch.object(b,'MAX_COMMITS',4):
                fails((ValueError,github.StoreConflict),lambda:pair.restore(source,mm,candidate/'restore',pins))


def test_backup_moved_source_and_changed_fence_cursor_refused():
    f=example()
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);plan=deepcopy(f['plan']);plan['out']=str(td/'moving')
        # Motion is injected after complete packaging and before a receipt exists.
        def move(_):
            b.git(plan['fence_source'],b.Budget(),'update-ref','refs/heads/actions-fence',plan['pins']['fence']['commit_sha']+'~1')
        try:
            with patch.object(b,'MAX_COMMITS',4): fails(ValueError,lambda:pair.append(plan,fault=move))
            assert not list((td/'moving').glob('pair-*.json'))
        finally:
            b.git(plan['fence_source'],b.Budget(),'update-ref','refs/heads/actions-fence',plan['pins']['fence']['commit_sha'])
    previous=deepcopy(f['fence']);current=deepcopy(previous);current['phase']='open';current['completion']=None
    fails(ValueError,lambda:pair.transition(previous,current))


def test_backup_continues_both_increment_chains_without_rewriting_old_packages():
    f=example();end=deepcopy(f['plan']);budget=b.Budget()
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);plan=deepcopy(end);plan['out']=str(td/'pair')
        for kind in ('stream','fence'):
            target=td/kind;shutil.copytree(plan[kind+'_source'],target);plan[kind+'_source']=str(target)
        early_fence=b.git(plan['fence_source'],budget,'rev-parse',end['pins']['fence']['commit_sha']+'~4').decode().strip()
        with b.batch(plan['fence_source'],budget) as read:
            _,raw,value,fblob=pair.inspect_fence(read,early_fence,plan['deployment'])
        loc=value['completion']['stream']
        plan['pins']['stream']={k:loc[k] for k in ('commit_sha','revision','blob_sha','snapshot_digest')}
        plan['pins']['fence']=dict(commit_sha=early_fence,revision=8,blob_sha=fblob,body_sha256=digest(value))
        b.git(plan['stream_source'],budget,'update-ref','refs/heads/'+plan['deployment']['store_branch'],loc['commit_sha'])
        b.git(plan['fence_source'],budget,'update-ref','refs/heads/'+plan['deployment']['fence_branch'],early_fence)
        with patch.object(b,'MAX_COMMITS',4): first=pair.append(plan)
        old=pair.inventory(td/'pair',budget)
        for kind,branch in (('stream',plan['deployment']['store_branch']),('fence',plan['deployment']['fence_branch'])):
            b.git(plan[kind+'_source'],budget,'update-ref','refs/heads/'+branch,end['pins'][kind]['commit_sha'])
        plan['pins']=end['pins']
        with patch.object(b,'MAX_COMMITS',4): latest=pair.append(plan)
        assert latest['manifest']['stream']['history_count']>first['manifest']['stream']['history_count']
        assert latest['manifest']['fence']['history_count']==13
        assert all(pair.inventory(td/'pair',budget)[name]==item for name,item in old.items())


def test_backup_open_sending_uncertain_preserved_and_cannot_send():
    f=example()
    for status in ('sending','uncertain'):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);plan=deepcopy(f['plan']);plan['out']=str(td/'pair')
            # Local new streams are copied, never edit the completed main example.
            repo=td/'source';shutil.copytree(plan['stream_source'],repo);plan['stream_source']=str(repo)
            env=json.loads(f['stream_body']);w=capacity.GitWriter(repo,f['stream_body']);w.revision=env['revision']
            w.pin=plan['pins']['stream']['commit_sha'];w.prior_digest=env['body_digest'];w.start()
            msg=w.snapshot['commands']['retained-command']['_delivery']['messages'][0];msg.update(status=status,receipt=None)
            w.commit();w.stop();plan['pins']['stream'].update(commit_sha=w.pin,revision=w.revision,blob_sha=w.blob,snapshot_digest=w.prior_digest)
            fr=td/'fence';shutil.copytree(plan['fence_source'],fr);plan['fence_source']=str(fr)
            opened=deepcopy(f['fence']);run=opened['run'];run.update(id='900',number=run['number']+1)
            opened['cursors'][run['workflow']]={'number':run['number'],'id':run['id']}
            opened.update(phase='open',completion=None,write_id='synthetic-crash')
            raw=canonical(opened).encode();pin=commit_file(fr,'actions-fence',actions.FENCE_PATH,raw,plan['pins']['fence']['commit_sha'])
            plan['pins']['fence'].update(commit_sha=pin,revision=13,blob_sha=blob(raw),body_sha256=digest(opened))
            with patch.object(b,'MAX_COMMITS',4): result=pair.append(plan)
            restored=Path(result['verification_path'])
            assert (restored/'actions-fence.original.json').read_bytes()==raw
            with durable.read_only_volume(restored/'stream/blocked-store',plan['identity']['store_id']) as store:
                assert store.snapshot['control']['mode']=='blocked'
                assert store.snapshot['commands']['retained-command']['_delivery']['messages'][0]['status']=='uncertain'


class HTTP:
    def __init__(self,f):
        self.f=f;self.seen=[];self.records={};self.heads={};self.parents={};self.lists={};self.jobs={};self.runs={};self.hook=None
        p=f['plan'];d=p['deployment'];budget=b.Budget()
        for kind,path in (('stream',github.STORE_PATH),('fence',actions.FENCE_PATH)):
            repo=d['private_store_repository'];branch=d['store_branch'] if kind=='stream' else d['fence_branch']
            pin=p['pins'][kind]['commit_sha'];self.heads[(repo,branch)]=pin
            with b.batch(p[kind+'_source'],budget) as read:
                for commit in b.commits(p[kind+'_source'],pin,None,budget):
                    raw=read(commit+':'+path,'blob',github.MAX_BYTES)
                    self.records[(repo,commit,path)]=raw
                    headers=read(commit,'commit',16384).split(b'\n\n',1)[0].splitlines()
                    self.parents[(repo,commit)]=[x[7:].decode() for x in headers if x.startswith(b'parent ')]
        for kind in ('signal','watch'):
            self.lists[kind]=[deepcopy(m) for m in f['metas'] if m['path'].endswith('/'+kind+'.yml')]
        for m in f['metas']:
            self.runs[str(m['id'])]=deepcopy(m)
            self.jobs[str(m['id'])]={'total_count':1,'jobs':[dict(run_id=m['id'],run_attempt=1,
                head_sha=d['code_sha'],status='completed',conclusion='success',completed_at=m['updated_at'])]}
        m=deepcopy(f['result']['manifest']);v=deepcopy(f['result']['verification']);now=f['base']+60*slots.MINUTE
        v['verified_ms']=now-5*slots.MINUTE
        verifier=dict(repository='synthetic/code',workflow='.github/workflows/backup-verify.yml',branch='synthetic',code_sha=d['code_sha'])
        self.policy=dict(schema='p4-actions-monitor-v1',enabled=True,deployment=d,
            first_start_ms={'signal':f['base']+2*slots.MINUTE,'watch':f['base']+8*slots.MINUTE,'backup':now//(24*slots.HOUR)*(24*slots.HOUR)},
            backup_target=dict(repository='synthetic/backup',branch='protected-pair',manifest_path='pair-manifest.json'),
            independent_verifier=dict(repository='synthetic/verifier',receipt_branch='protected-receipts',receipt_path='receipt.json',binding=verifier))
        raw=(canonical(m)+'\n').encode();self.add('synthetic/backup','protected-pair','pair-manifest.json','e'*40,raw)
        self.receipt=dict(schema='p4-independent-backup-receipt-v1',manifest=m,manifest_sha256=digest(m),verification=v,
            expected_start_ms=self.policy['first_start_ms']['backup'],verifier=verifier,verifier_run_id='999',
            destination={**self.policy['backup_target'],'commit_sha':'e'*40,'blob_sha':blob(raw)},upload_readback_verified=True)
        self.sync_receipt()
        self.runs['999']=dict(repository={'full_name':'synthetic/code'},id=999,path=verifier['workflow'],head_sha=d['code_sha'],
            head_branch='synthetic',run_attempt=1,status='completed',conclusion='success',
            created_at=iso(now-6*slots.MINUTE),updated_at=iso(now-4*slots.MINUTE))
        self.jobs['999']={'total_count':1,'jobs':[dict(run_id=999,run_attempt=1,head_sha=d['code_sha'],status='completed',conclusion='success')]}

    def add(self,repo,branch,path,pin,raw):
        self.heads[(repo,branch)]=pin;self.records[(repo,pin,path)]=raw;self.parents[(repo,pin)]=[]

    def sync_receipt(self):
        self.add('synthetic/verifier','protected-receipts','receipt.json','d'*40,canonical(self.receipt).encode())

    def open(self,request,timeout):
        from offline_test_fixtures import monitor_reply
        answer=monitor_reply(self,request,timeout)
        if answer is not None:return answer
        assert request.get_method()=='GET' and request.data is None and 0<timeout<=3
        url=urllib.parse.urlsplit(request.full_url);path=urllib.parse.unquote(url.path);q=urllib.parse.parse_qs(url.query)
        self.seen.append(path)
        if self.hook: self.hook(self,path)
        parts=path.split('/');repo='/'.join(parts[2:4]);tail='/'+'/'.join(parts[4:])
        if tail.startswith('/git/ref/heads/'): result={'object':{'sha':self.heads[(repo,tail[len('/git/ref/heads/'):])]}}
        elif tail.startswith('/contents/'):
            raw=self.records[(repo,q['ref'][0],tail[len('/contents/'):])]
            result={'type':'file','encoding':'base64','sha':blob(raw),'content':base64.b64encode(raw).decode()}
        elif tail.startswith('/compare/'):
            base,head=tail.rsplit('/',1)[1].split('...');cursor=head
            while cursor!=base and self.parents.get((repo,cursor)): cursor=self.parents[(repo,cursor)][0]
            result={'base_commit':{'sha':base},'merge_base_commit':{'sha':base if cursor==base else 'f'*40},'status':'identical' if base==head else 'ahead'}
        elif tail.startswith('/actions/workflows/'):
            kind=tail.split('/')[-2].removesuffix('.yml');items=self.lists[kind]
            result={'total_count':len(items),'workflow_runs':items}
        elif tail.startswith('/actions/runs/'):
            rid=tail.split('/')[3];result=self.jobs[rid] if tail.endswith('/jobs') else self.runs[rid]
        else: raise AssertionError('Unknown fixture route '+tail)
        return io.BytesIO(json.dumps(result).encode())

    def check(self,now=None):
        budget=ReadBudget();d=self.policy['deployment'];v=self.policy['independent_verifier']
        with patch.object(monitor.Reader,'open_request',side_effect=self.open),patch.object(tg,'deliver_telegram',side_effect=AssertionError('No monitor send')):
            source=monitor.Reader(os.environ['GITHUB_TOKEN'],[d['private_store_repository']],budget)
            code=monitor.Reader(os.environ['GITHUB_TOKEN'],[d['code_repository'],v['binding']['repository']],budget,metadata=True)
            backup=monitor.Reader(os.environ['GITHUB_TOKEN'],[v['repository'],self.policy['backup_target']['repository']],budget)
            result=monitor.check(source,code,backup,self.policy,now if now is not None else self.f['base']+60*slots.MINUTE)
        assert budget.requests<=64
        return result


def test_monitor_actual_http_clients_healthy_exact_completions_and_pair_receipt():
    http=HTTP(example());result=http.check();assert result['http_status']==200,result
    assert any('/compare/' in x for x in http.seen) and any('/attempts/1/jobs' in x for x in http.seen)
    b.write_json(Path(ARTIFACT_ROOT)/'monitor-success.json',dict(result=result,get=len(http.seen),put=0,transport=0))


def test_monitor_missing_queue_overflow_cancelled_skipped_and_wrong_phase_unhealthy():
    for mode in ('missing32','queued','cancelled','skipped','foreign','bad-phase','incomplete-list'):
        http=HTTP(example())
        if mode=='missing32': http.lists['signal'].pop()
        elif mode=='queued': http.lists['watch'][-1].update(status='queued',conclusion=None)
        elif mode=='cancelled': http.lists['watch'][-1]['conclusion']='cancelled'
        elif mode=='skipped': http.jobs[str(http.lists['watch'][-1]['id'])]['jobs'][0]['conclusion']='skipped'
        elif mode=='foreign': http.lists['watch'][-1]['head_sha']='f'*40
        elif mode=='bad-phase': http.lists['signal'][-1]['display_title']='btc-v2:signal:'+str(http.f['base'])
        else: http.lists['watch']*=25
        assert http.check()['http_status']==503,mode


def test_monitor_open_moving_fence_stream_runs_and_backup_ref_fail_closed():
    for mode in ('open','fence-move','stream-move','runs-move','backup-move'):
        http=HTTP(example());d=http.policy['deployment']
        if mode=='open':
            key=(d['private_store_repository'],http.heads[(d['private_store_repository'],d['fence_branch'])],actions.FENCE_PATH)
            v=json.loads(http.records[key]);v['phase']='open';http.records[key]=canonical(v).encode()
        else:
            count={}
            def hook(h,path):
                count[path]=count.get(path,0)+1
                target={'fence-move':'/git/ref/heads/'+d['fence_branch'],'stream-move':'/git/ref/heads/'+d['store_branch'],
                    'runs-move':'/actions/workflows/signal.yml/runs','backup-move':'/git/ref/heads/protected-pair'}[mode]
                threshold=3 if mode in ('fence-move','stream-move') else 2
                if path.endswith(target) and count[path]>=threshold:
                    if mode=='runs-move': h.lists['signal'][-1]['conclusion']='cancelled'
                    else:
                        repo=d['private_store_repository'] if mode!='backup-move' else 'synthetic/backup'
                        branch=d['fence_branch'] if mode=='fence-move' else d['store_branch'] if mode=='stream-move' else 'protected-pair'
                        h.heads[(repo,branch)]='f'*40
            http.hook=hook
        assert http.check()['http_status']==503,mode


def test_monitor_backup_missing_old_foreign_partial_or_unverified_refused():
    for mode in ('old','foreign','missing-fence','missing-part','unverified','bad-verifier','future','source-pin'):
        http=HTTP(example());r=http.receipt
        if mode=='old': r['expected_start_ms']-=2*24*slots.HOUR
        elif mode=='future': r['verification']['verified_ms']=http.f['base']+61*slots.MINUTE
        elif mode=='foreign': r['destination']['repository']='foreign/backup'
        elif mode=='missing-fence': r['manifest'].pop('fence')
        elif mode=='missing-part': r['manifest']['fence']['history_count']-=1
        elif mode=='unverified': r['upload_readback_verified']=False
        elif mode=='bad-verifier': http.runs['999']['conclusion']='failure'
        else: r['manifest']['pins']['fence']['commit_sha']='f'*40
        http.sync_receipt();assert http.check()['http_status']==503,mode


def test_monitor_signal_watch_and_backup_exact_freshness_boundaries():
    f=example();http=HTTP(f)
    assert http.check(f['base']+83*slots.MINUTE-1)['http_status']==200
    assert http.check(f['base']+83*slots.MINUTE)['http_status']==503
    # Test receipt's exact 26h boundary independently of unrelated next-run obligations.
    from actions_freshness import read_backup
    http=HTTP(f);slot=http.receipt['expected_start_ms'];end=slots.deadline('backup',slot)
    budget=ReadBudget()
    with patch.object(monitor.Reader,'open_request',side_effect=http.open):
        backup=monitor.Reader(os.environ['GITHUB_TOKEN'],['synthetic/verifier','synthetic/backup'],budget)
        code=monitor.Reader(os.environ['GITHUB_TOKEN'],['synthetic/code'],budget,metadata=True)
        read_backup(backup,code,http.policy,end)
        fails(ValueError,lambda:read_backup(backup,code,http.policy,end+1))


def test_reader_get_response_deadline_and_shared_request_caps():
    budget=ReadBudget();reader=monitor.Reader(os.environ['GITHUB_TOKEN'],['synthetic/code'],budget,metadata=True)
    fails(github.StoreUnavailable,lambda:reader._request('PUT','/repos/synthetic/code/contents/x',{}))
    fails(github.StoreUnavailable,lambda:reader._request('GET','/repos/foreign/code/x'))
    budget.requests=64;fails(github.StoreUnavailable,lambda:reader._request('GET','/repos/synthetic/code/x'))
    budget.requests=0;budget.started-=21;fails(github.StoreUnavailable,lambda:reader._request('GET','/repos/synthetic/code/x'))
    budget.started+=21
    with patch.object(reader,'open_request',return_value=io.BytesIO(b' '*(2*1024*1024+1))):
        fails(github.StoreUnavailable,lambda:reader._request('GET','/repos/synthetic/code/x'))


def test_readback_actual_git_blobs_independent_full_restore_and_foreign_pin_refused():
    f=example();root=f['root'];manifest=f['result']['manifest'];mirror=root/'uploaded-synthetic-mirror'
    mirror.mkdir();budget=b.Budget();b.git(mirror,budget,'init','--bare')
    payload={name:(root/'pair'/name).read_bytes() for name in manifest['files']}
    payload['pair-manifest.json']=(canonical(manifest)+'\n').encode()
    text=b'synthetic protected backup package\n'
    data=f'commit refs/heads/protected-pair\nmark :1\ncommitter Offline <synthetic@example.invalid> 1700000000 +0000\ndata {len(text)}\n'.encode()+text
    for name,raw in payload.items():
        data+=f'M 100644 inline {name}\ndata {len(raw)}\n'.encode()+raw+b'\n'
    data+=b'\nget-mark :1\ndone\n'
    with b.process(mirror,['fast-import','--quiet'],budget) as proc:
        proc.stdin.write(data);proc.stdin.flush();pin=proc.stdout.readline().decode().strip()
    now=f['base']+60*slots.MINUTE;binding=dict(repository='synthetic/code',workflow='.github/workflows/backup-verify.yml',
        branch='synthetic',code_sha=f['plan']['deployment']['code_sha'])
    plan=dict(destination=dict(repository='synthetic/backup',branch='protected-pair',manifest_path='pair-manifest.json',
        commit_sha=pin,blob_sha=blob(payload['pair-manifest.json'])),verifier=binding,manifest=str(root/'manifest.json'),
        root=str(root/'pair'),mirror=str(mirror),pins=f['plan']['pins'],expected_start_ms=now//(24*slots.HOUR)*(24*slots.HOUR),
        target=str(root/'readback-restore'),receipt_out=str(root/'independent-synthetic-receipt.json'))
    env={'GITHUB_REPOSITORY':'synthetic/code','GITHUB_SHA':binding['code_sha'],'GITHUB_REF':'refs/heads/synthetic',
         'GITHUB_WORKFLOW_REF':'synthetic/code/'+binding['workflow']+'@refs/heads/synthetic','GITHUB_RUN_ATTEMPT':'1','GITHUB_RUN_ID':'999'}
    with patch.dict(os.environ,env),patch.object(entry,'check_code_pin'),patch.object(pair.time,'time',return_value=now/1000),patch.object(b,'MAX_COMMITS',4):
        receipt=pair.verify_readback(plan)
        assert receipt['upload_readback_verified'] and receipt['verification']['enabled'] is False
        bad=deepcopy(plan);bad['destination']['commit_sha']='f'*40
        fails(ValueError,lambda:pair.verify_readback(bad))
