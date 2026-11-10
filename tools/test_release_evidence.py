"""Two missing end-to-end witnesses. Synthetic profile in a separate directory.

Production bindings/files are never changed. The synthetic module has identical
AST except for literal binding values, and gets its own authenticated manifest.
"""
from pathlib import Path
import ast,base64,copy,hashlib,io,json,os,re,shlex,shutil,subprocess,sys
import yaml as yaml_parser
import urllib.parse
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.local-tests'/os.environ.get('BTC_RELEASE_EVIDENCE_DIR','release-evidence')
CORE='20d755a4332fb32aeab08b1973b650eeae10f31e'
REPO='synthetic/private-store';BRANCH='delivery-only';FB='actions-fence'
if '--worker' in sys.argv:
    sys.path.insert(0,str(ROOT/'tools'))
    from pinned_delivery_entry import install
    entry=install(OUT/'core',OUT/'extension',hashlib.sha256((OUT/'extension/delivery-extension.json').read_bytes()).hexdigest())
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import github_delivery as g,actions_delivery as a
from production_contract import canonical,digest
import p3_backup_chain as b,p4_backup_pair as pair
from test_betriebsabschluss import commit_file
from test_free_public import access_for,writer_review
from github_freshness import iso

def git(repo,*args,input=None):
    return subprocess.check_output(['git','-C',str(repo),*args],input=input,stderr=subprocess.PIPE)
def rec(repo,pin,path):
    body=git(repo,'show',pin+':'+path)
    return dict(body=body,commit_sha=pin,blob_sha=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest())
def write_json(path,value): path.write_bytes(canonical(value).encode())

def generate():
    OUT.mkdir(parents=True,exist_ok=False)
    from test_production_migration import fixture as legacy_fixture
    import produktion_migrate, produktion_store
    import durable_delivery as durable,telegram_outbox as box,run_health
    (OUT/'seed').mkdir();paths=legacy_fixture(OUT/'seed')
    # Synthetic legacy source, explicitly flat, and the exact published C05
    # target. No production binding or renderer constant is rewritten.
    source=paths[0];old_config=json.loads((source/'config-source.json').read_bytes())
    old_state=json.loads((source/'state.json').read_bytes())
    flat=dict(pos_state='FLAT',last_signal_ts=old_state['last_signal_ts'],
              config={k:v for k,v in old_config.items() if not k.startswith('_')},last_close=100)
    write_json(source/'state.json',flat)
    manifest=json.loads(paths[1].read_bytes());raw=(source/'state.json').read_bytes()
    manifest['files']['state.json']={'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw)}
    manifest.update(repository='synthetic-c05-source',code_sha=CORE,source_sha='d'*40,git_tree='e'*40)
    write_json(paths[1],manifest)
    target=json.loads((ROOT/'site/data/config.json').read_bytes())
    from production_contract import effective_config
    assert digest(effective_config(target))=='3efe8a17330c228a75fe879d4e7c7ed0cade766e4a07ca0c05832b88aa3d282b'
    write_json(paths[3],target)
    cutover=json.loads(paths[2].read_bytes());target=effective_config(target)
    cutover.update(code_sha=CORE,source_sha='d'*40,approved_config_differences=sorted(
        k for k in set(flat['config'])|set(target) if flat['config'].get(k)!=target.get(k)))
    write_json(paths[2],cutover)
    produktion_migrate.convert(*paths);store=OUT/'seed/store';produktion_store.provision(paths[-1],store)
    with durable.read_only_volume(store,'synthetic-store') as volume: snapshot=copy.deepcopy(volume.snapshot)
    snapshot['control']['code_sha']=CORE
    target='synthetic-target';assert snapshot['control']['target_binding']==hashlib.sha256(target.encode()).hexdigest()
    repo=OUT/'stream.git';repo.mkdir();git(repo,'init','--bare')
    seed=json.loads(g.initial_envelope(snapshot,REPO,BRANCH,'synthetic-store'))
    from p3_capacity_fixture import GitWriter
    w=GitWriter(repo,canonical(seed).encode());w.start();w.commit()
    w.snapshot['control']['mode']='active'
    delivery=w.snapshot['engine']['_delivery']
    for i in range(18):
        box.enqueue(delivery,'fixture','event-'+str(i),0,{'synthetic':i},'synthetic retained receipt')
        delivery['messages'][-1].update(status='confirmed',attempts=1,target=hashlib.sha256(target.encode()).hexdigest(),receipt=i+1)
    w.snapshot['control']['owner']=dict(repository=REPO,run_id='500',run_attempt='1',nonce='synthetic-owner')
    base=w.snapshot['control']['migration']['W']+8*14400000;slot=base+8*60000
    w.owner=w.snapshot['control']['owner'];w.commit()
    env=dict(BTC_DELIVERY_RUN_REPOSITORY='synthetic/code',BTC_DELIVERY_WORKFLOW='.github/workflows/watch.yml',
        BTC_DELIVERY_RUN_ID='500',BTC_DELIVERY_RUN_ATTEMPT='1',BTC_DELIVERY_EXPECTED_START_MS=str(slot))
    with patch.dict(os.environ,env):
        run_health.record_event(w,'watch','start',slot+1000,None)
        run_health.record_event(w,'watch','finish',slot+2000,'synthetic-aborted')
    while w.revision<1801: w.commit()
    w.stop();source=json.loads(w.body)
    runtime=json.loads((ROOT/'ops/produktion/github-actions-runtime.disabled.json').read_bytes())
    runtime.update(enabled=True,python_version=list(sys.version_info[:3]),activation_review_sha256='b'*64,
        private_store_repository=REPO,store_branch=BRANCH,fence_branch=FB,store_id='synthetic-store',
        code_sha=CORE,code_repository='synthetic/code',code_ref='refs/heads/synthetic',
        bot_identity=source['snapshot']['control']['bot_identity'],config_sha256=source['snapshot']['control']['config_sha256'])
    access,rules,sets=access_for({REPO:dict(id=1,visibility='public',branches=[BRANCH,FB]),
        'synthetic/code':dict(id=2,visibility='public',branches=['synthetic'])})
    writer_review(access,'sender_write',REPO,[BRANCH,FB]);runtime['public_access']=access;runtime['public_access_sha256']=digest(access)
    from produktion_actions_runner import deployment
    d=deployment(runtime);fence=json.loads(a.seed_fence(d));fr=OUT/'fence.git'
    fseed=commit_file(fr,FB,a.FENCE_PATH,canonical(fence).encode())
    fence.update(phase='open',run=dict(id='500',attempt='1',number=1,kind='watch',workflow='.github/workflows/watch.yml',
        expected_start_ms=str(slot),deadline_utc_ms=slot+900000),write_id='synthetic-open',completion=None)
    fence['cursors']['.github/workflows/watch.yml']=dict(id='500',number=1)
    fpin=commit_file(fr,FB,a.FENCE_PATH,canonical(fence).encode(),fseed)
    profile=dict(STREAM_PIN=w.pin,FENCE_PIN=fpin,STREAM_HASH=hashlib.sha256(w.body).hexdigest(),
        FENCE_HASH=hashlib.sha256(canonical(fence).encode()).hexdigest(),SNAPSHOT=source['body_digest'])
    original=(ROOT/'engine/aborted_maintenance.py').read_text();synthetic=original
    for key,value in profile.items(): synthetic=re.sub(r'^'+key+r" = '[^']+'",key+' = '+repr(value),synthetic,flags=re.M)
    for old,new in [('39700885866','500'),('szoceikaiser/btc-delivery-store',REPO),
                    ('delivery-stream-live',BRANCH),('btc-signal-app-live-store-20261018','synthetic-store')]:
        synthetic=synthetic.replace(old,new)
    def structure(text):
        tree=ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node,ast.Constant):node.value='<literal>'
        return ast.dump(tree)
    assert structure(original)==structure(synthetic),'Test may not change any predicate/control flow'
    extension=OUT/'extension';manifest=json.loads((ROOT/'delivery-extension.json').read_bytes())
    for path in list(manifest['files'])+['delivery-extension.json']:
        dest=extension/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dest)
    (extension/'engine/aborted_maintenance.py').write_bytes(synthetic.encode())
    manifest['files']={p:hashlib.sha256((extension/p).read_bytes()).hexdigest() for p in manifest['files']}
    write_json(extension/'delivery-extension.json',manifest)
    core=OUT/'core';core.mkdir();git(core,'init')
    objects=git(ROOT,'rev-parse','--path-format=absolute','--git-path','objects').decode().strip()
    (core/'.git/objects/info/alternates').write_bytes(Path(objects).as_posix().encode()+b'\n')
    git(core,'checkout','--detach',CORE)
    review=dict(schema='btc-aborted-watch-500-v1',reviewer='SYNTHETIC-ONLY',stream_pin=w.pin,fence_pin=fpin,failed_run='500',
        old_owner=source['snapshot']['control']['owner'],stopped_at_ms=slot+1000000,
        triggers_paused=True,workers_terminated=True,run_completed=True,
        pause_evidence_sha256='1'*64,termination_evidence_sha256='2'*64,failed_run_evidence_sha256='3'*64)
    write_json(OUT/'fixture.json',dict(runtime=runtime,review=review,slot=slot,
        source=source,fence=fence,profile=profile,identity=dict(repo=REPO,branch=BRANCH,store_id='synthetic-store',
            stream_id=source['snapshot']['control']['stream_id']),migration=str(paths[-1]),
        rules=[dict(repo=r,branch=v,body=body) for (r,v),body in rules.items()],
        sets=[dict(repo=r,id=i,body=body) for (r,i),body in sets.items()],
        production_source_sha256=hashlib.sha256(original.encode()).hexdigest(),predicate_ast_sha256=digest(structure(original))))
    print('PASS generated independent SYNTHETIC history, 1802 stream revisions and direct Git parents',flush=True)

class Provider:
    def __init__(self,fixture):
        self.fixture=fixture;self.puts=[];self.meta=None;self.metadata={};self.own_run=None;self.calls=[]
    def local(self,branch):
        return OUT/('journal.git' if branch=='recovery-journal-live' else 'stream.git' if branch==BRANCH else 'fence.git')
    def heads(self):return [(branch,git(self.local(branch),'rev-parse','refs/heads/'+branch).decode().strip()) for branch in (BRANCH,FB)]
    def locate(self,pin,path):
        return rec(self.local('recovery-journal-live' if path.startswith('recovery/') else BRANCH if path==g.STORE_PATH else FB),pin,path)
    def open(self,request,timeout):
        u=urllib.parse.urlsplit(request.full_url)
        if u.netloc=='github.com':
            from test_free_quota import advertisement
            return advertisement(self.heads())
        if u.netloc=='raw.githubusercontent.com':
            parts=u.path.split('/');path='/'.join(parts[4:])
            value=rec(OUT/'entry.git',parts[3],path) if '/'.join(parts[1:3])=='synthetic/code' else self.locate(parts[3],path)
            return io.BytesIO(value['body'])
        parts=u.path.split('/');repo='/'.join(parts[2:4]);tail='/'+'/'.join(parts[4:]) if len(parts)>4 else ''
        self.calls.append((request.get_method(),repo,tail))
        if tail.startswith('/contents/recovery/incidents/'):
            path=tail[len('/contents/'):]
            if request.get_method()=='GET':
                pin=urllib.parse.parse_qs(u.query)['ref'][0]
                try:r=self.locate(pin,path)
                except subprocess.CalledProcessError:
                    from urllib.error import HTTPError
                    raise HTTPError(request.full_url,404,'synthetic absent',{},None)
                value=dict(type='file',encoding='base64',sha=r['blob_sha'],content=base64.b64encode(r['body']).decode())
            else:
                payload=json.loads(request.data);local=self.local('recovery-journal-live')
                head=git(local,'rev-parse','refs/heads/recovery-journal-live').decode().strip()
                try:old=self.locate(head,path)
                except subprocess.CalledProcessError:old=None
                assert payload.get('sha')==(old['blob_sha'] if old else None)
                pin=commit_file(local,'recovery-journal-live',path,base64.b64decode(payload['content']),head)
                value={'commit':{'sha':pin}}
            return io.BytesIO(canonical(value).encode())
        if request.get_method()=='PUT':
            p=json.loads(request.data);branch=p['branch'];local=self.local(branch)
            old=dict(self.heads())[branch];path=tail.split('/contents/')[1]
            assert self.locate(old,path)['blob_sha']==p['sha']
            pin=commit_file(local,branch,path,base64.b64decode(p['content']),old);self.puts.append((branch,pin))
            value={'commit':{'sha':pin}}
        elif tail=='':value=dict(id=self.fixture['runtime']['public_access']['repositories'][repo]['id'],full_name=repo,private=False,visibility='public')
        elif tail.startswith('/rules/branches/'):
            branch=tail.rsplit('/',1)[1];value=next(r['body'] for r in self.fixture['rules'] if r['repo']==repo and r['branch']==branch)
        elif tail.startswith('/rulesets/'):
            i=int(tail.rsplit('/',1)[1]);value=next(r['body'] for r in self.fixture['sets'] if r['repo']==repo and r['id']==i)
        elif tail=='/actions/runs':
            values=[self.own_run] if self.own_run and urllib.parse.parse_qs(u.query)['status']==['in_progress'] else []
            value={'total_count':len(values),'workflow_runs':values}
        elif tail.startswith('/actions/runs/'):
            rid=tail.split('/')[3]
            value=self.metadata[rid]['jobs' if '/jobs' in tail else 'run'] if rid in self.metadata else self.meta
        elif tail.startswith('/compare/'):
            base,head=tail[len('/compare/'):].split('...')
            local=OUT/'entry.git' if repo=='synthetic/code' else next(p for p in (self.local(BRANCH),self.local(FB),self.local('recovery-journal-live'))
                if p.exists() and subprocess.run(['git','-C',str(p),'cat-file','-e',head],capture_output=True).returncode==0)
            ancestor=git(local,'merge-base',base,head).decode().strip()
            value=dict(base_commit={'sha':base},merge_base_commit={'sha':ancestor},status='identical' if base==head else 'ahead')
        elif tail.startswith('/git/ref/heads/'):
            branch=tail.rsplit('/',1)[1]
            value={'object':{'sha':git(self.local(branch),'rev-parse','refs/heads/'+branch).decode().strip()}}
        elif tail.startswith('/git/commits/'):
            pin=tail.rsplit('/',1)[1];local=next(p for p in (self.local(BRANCH),self.local(FB)) if subprocess.run(['git','-C',str(p),'cat-file','-e',pin],capture_output=True).returncode==0)
            parents=git(local,'show','-s','--format=%P',pin).decode().strip().split();value={'parents':[{'sha':p} for p in parents]}
        elif tail.startswith('/contents/'):
            pin=urllib.parse.parse_qs(u.query)['ref'][0]
            if repo=='synthetic/code':r=rec(OUT/'entry.git',pin,tail.split('/contents/')[1])
            else:r=self.locate(pin,tail.split('/contents/')[1])
            value=dict(type='file',encoding='base64',sha=r['blob_sha'],content=base64.b64encode(r['body']).decode())
        else:raise AssertionError('Unexpected synthetic route')
        return io.BytesIO(canonical(value).encode())

def server_recovery(p,runtime,d,owned_run,owner_slot,code,production_manifest,test_manifest):
    """Real server-journaled executor over the SAME Git-backed provider."""
    import github_recovery as recovery
    from public_access import review_hash
    watch=(ROOT/'.github/workflows/watch.yml').read_bytes().replace(production_manifest.encode(),test_manifest.encode())
    watch_pin=commit_file(code,'synthetic','.github/workflows/watch.yml',watch,CORE)
    recover_yaml=(ROOT/'.github/workflows/recovery.yml').read_bytes().replace(production_manifest.encode(),test_manifest.encode())
    recovery_pin=commit_file(code,'synthetic','.github/workflows/recovery.yml',recover_yaml,watch_pin)
    journal_repo=p.local('recovery-journal-live')
    seed=commit_file(journal_repo,'recovery-journal-live','recovery/seed.json',b'{"synthetic":true}')
    repos=copy.deepcopy(runtime['public_access']['repositories']);repos[REPO]['branches'].append('recovery-journal-live')
    access,rules,sets=access_for(repos)
    writer_review(access,'recovery_journal_write',REPO,['recovery-journal-live'])
    proof=access['credential_reviews']['recovery_journal_write'];proof['credential_reference']='github-fine-grained-pat:21186996';proof['sha256']=review_hash(proof)
    for (repo,branch),body in rules.items():
        if repo==REPO and branch=='recovery-journal-live':p.fixture['rules'].append(dict(repo=repo,branch=branch,body=body))
    for (repo,i),body in sets.items():
        if repo==REPO and 'refs/heads/recovery-journal-live' in body['conditions']['ref_name']['include']:
            p.fixture['sets'].append(dict(repo=repo,id=i,body=body))
    policy=dict(schema='btc-continuous-recovery-v1',enabled=True,activation_reviewed=True,deployment=d,
        public_access=runtime['public_access'],entry_workflows={owned_run['workflow']:hashlib.sha256(watch).hexdigest()},
        recovery_entry=dict(repository='synthetic/code',branch='synthetic',code_sha=CORE,
            workflow='.github/workflows/recovery.yml',workflow_sha256=hashlib.sha256(recover_yaml).hexdigest()),
        journal=dict(repository=REPO,branch='recovery-journal-live',reviewed=True,seed_commit=seed,public_access=access,
            credential_reference='github-fine-grained-pat:21186996',required_permissions={'contents':'write','metadata':'read'}))
    meta=dict(id=int(owned_run['id']),run_number=owned_run['number'],run_attempt=1,path=owned_run['workflow'],head_sha=watch_pin,
        repository={'full_name':'synthetic/code'},head_branch='synthetic',status='completed',conclusion='failure',
        event='workflow_dispatch',display_title='btc-v2:watch:created',created_at=iso(owner_slot+100),
        run_started_at=iso(owner_slot+200),updated_at=iso(owner_slot+500))
    p.metadata[owned_run['id']]={'run':meta,'jobs':{'total_count':1,'jobs':[dict(id=49991,run_id=int(owned_run['id']),run_attempt=1,
        head_sha=watch_pin,status='completed',conclusion='failure',labels=['ubuntu-24.04'],completed_at=iso(owner_slot+500))]}}
    own=dict(id=502,run_attempt=1,path='.github/workflows/recovery.yml',head_sha=recovery_pin,head_branch='synthetic',
        repository={'full_name':'synthetic/code'},status='in_progress')
    p.own_run=own;p.metadata['502']={'run':own,'jobs':{'total_count':1,'jobs':[dict(id=9001,name='recover',run_id=502,
        run_attempt=1,head_sha=recovery_pin,status='in_progress',labels=['ubuntu-24.04'])]}}
    environment=dict(GITHUB_REPOSITORY='synthetic/code',GITHUB_REF='refs/heads/synthetic',GITHUB_WORKFLOW_REF='synthetic/code/.github/workflows/recovery.yml@refs/heads/synthetic',
        GITHUB_RUN_ID='502',GITHUB_RUN_ATTEMPT='1',GITHUB_JOB='recover',GITHUB_SHA=recovery_pin)
    client=recovery.Network(policy,'SYNTHETIC-WRITER','SYNTHETIC-METADATA',p.open,lambda:owner_slot+1000)
    identity=recovery.bind_self(client,environment);result=recovery.run(client,identity)
    assert result['outcome']=='aborted'
    journal_path='recovery/incidents/'+result['incident']+'.json'
    pin=git(journal_repo,'rev-parse','refs/heads/recovery-journal-live').decode().strip()
    ledger=json.loads(rec(journal_repo,pin,journal_path)['body'])
    assert set(ledger['writes'])=={'stream','fence'} and all(v['status']=='confirmed' for v in ledger['writes'].values())
    assert p.metadata[owned_run['id']]['run']['conclusion']=='failure'
    write_json(OUT/'server-recovery-result.json',result);write_json(OUT/'server-recovery-journal.json',ledger)
    p.own_run=None
    return recovery_pin

def worker():
    import aborted_maintenance as m
    f=json.loads((OUT/'fixture.json').read_bytes());p=Provider(f);runtime=f['runtime'];d=entry.deployment(runtime)
    client=g.GitHubContentsClient('SYNTHETIC-WRITER');client.open_request=p.open
    s=client.read(REPO,BRANCH);old=client.read(REPO,FB,a.FENCE_PATH)
    m.preflight(s,old,f['review'])
    g.review_takeover(client,REPO,BRANCH,'synthetic-store',f['review']['old_owner'],1801,m.takeover_evidence(f['review']))
    store=g.read_only(client,REPO,BRANCH,'synthetic-store')
    closed=m.close_candidate(f['fence'],store._envelope,store.confirmed_record(),f['review'],'synthetic-aborted')
    fpin=commit_file(p.local(FB),FB,a.FENCE_PATH,canonical(closed).encode(),f['profile']['FENCE_PIN'])
    spin=store.confirmed_record();pins=dict(stream={k:spin[k] for k in ('commit_sha','revision','blob_sha','snapshot_digest')},
        fence=dict(commit_sha=fpin,revision=2,blob_sha=rec(p.local(FB),fpin,a.FENCE_PATH)['blob_sha'],body_sha256=digest(closed)))
    plan=dict(stream_source=str(p.local(BRANCH)),fence_source=str(p.local(FB)),deployment=d,identity=f['identity'],
        migration=f['migration'],pins=pins,out=str(OUT/'pair'))
    write_json(OUT/'required-independent-pins.json',pins);write_json(OUT/'plan.json',plan)
    result=pair.append(plan)
    restored=pair.restore(OUT/'pair',result['manifest'],OUT/'independent-restore',pins)
    import durable_delivery as durable
    with durable.read_only_volume(OUT/'independent-restore/stream/blocked-store','synthetic-store') as volume:
        assert volume.snapshot['control']['mode']=='blocked'
        assert volume.snapshot['engine']['_delivery']==store.snapshot['engine']['_delivery']
    original=json.loads((OUT/'independent-restore/actions-fence.original.json').read_bytes())
    assert original['completion']['outcome']=='aborted' and original['cursors']==closed['cursors']
    assert original['run']==closed['run']
    write_json(OUT/'restore-result.json',restored)
    print('PASS regular P4 append + independent full restore, aborted/18 receipts/cursors preserved; blocked',flush=True)
    # A wrong target must fail the unchanged configuration/identity gate.
    from production_contract import verify_runtime_config
    try:verify_runtime_config(store.snapshot,store.snapshot['engine']['config'],target_binding=hashlib.sha256(b'wrong-synthetic-target').hexdigest())
    except ValueError:pass
    else:raise AssertionError('Wrong target accepted')
    # A new, generic terminated-owner incident, separate from the old pinned
    # historical abort above. Persist both mutations and confirm real parents.
    import safe_recovery as recover
    prior=client.read(REPO,FB,a.FENCE_PATH);opened=copy.deepcopy(closed)
    owner_slot=__import__('actions_schedule').slot_at('watch',f['review']['stopped_at_ms']+900000)
    assert owner_slot>f['review']['stopped_at_ms']
    owned_run=dict(number=2,id='501',attempt='1',workflow='.github/workflows/watch.yml',kind='watch',
                   expected_start_ms=str(owner_slot),deadline_utc_ms=owner_slot+900000)
    opened.update(phase='open',completion=None,write_id='synthetic-generic-open',run=owned_run)
    opened['cursors'][owned_run['workflow']]={'number':2,'id':'501'}
    openpin=commit_file(p.local(FB),FB,a.FENCE_PATH,canonical(opened).encode(),prior['commit_sha'])
    owned=g.GitHubStore(client,REPO,BRANCH,'synthetic-store','501','1');owned.__enter__()
    code=OUT/'entry.git';code.mkdir();git(code,'init','--bare')
    (code/'objects/info/alternates').write_bytes((OUT/'core/.git/objects').as_posix().encode()+b'\n')
    production_manifest=hashlib.sha256((ROOT/'delivery-extension.json').read_bytes()).hexdigest()
    test_manifest=hashlib.sha256((OUT/'extension/delivery-extension.json').read_bytes()).hexdigest()
    recovery_pin=server_recovery(p,runtime,d,owned_run,owner_slot,code,production_manifest,test_manifest)
    recovered_store=g.read_only(client,REPO,BRANCH,'synthetic-store')
    final_recovery=client.read(REPO,FB,a.FENCE_PATH);recovered=json.loads(final_recovery['body'])
    assert recovered['completion']['outcome']=='aborted'
    print('PASS server-journaled generic owner recovery -> two confirmed actual Git CAS writes',flush=True)
    loc=recovered_store.confirmed_record()
    generic_pins=dict(stream={k:loc[k] for k in ('commit_sha','revision','blob_sha','snapshot_digest')},
        fence=dict(commit_sha=final_recovery['commit_sha'],revision=int(git(p.local(FB),'rev-list','--count',final_recovery['commit_sha']).decode())-1,
            blob_sha=final_recovery['blob_sha'],body_sha256=digest(recovered)))
    generic_plan={**plan,'pins':generic_pins,'out':str(OUT/'pair-generic-owner')}
    generic_backup=pair.append(generic_plan)
    generic_restore=pair.restore(OUT/'pair-generic-owner',generic_backup['manifest'],OUT/'restored-generic-owner',generic_pins)
    assert generic_restore['restore_blocked_verified'] and generic_restore['enabled'] is False
    restored_fence=json.loads((OUT/'restored-generic-owner/actions-fence.original.json').read_bytes())
    assert restored_fence==recovered and restored_fence['cursors']==recovered['cursors']
    with durable.read_only_volume(OUT/'restored-generic-owner/stream/blocked-store','synthetic-store') as volume:
        assert volume.snapshot['control']['mode']=='blocked'
        assert volume.snapshot['engine']['_delivery']==recovered_store.snapshot['engine']['_delivery']
    assert (OUT/'restored-generic-owner/RESTORE-BLOCKED.json').exists()
    for repo in (OUT/'restored-generic-owner/stream/verification-repository',OUT/'restored-generic-owner/fence-verification-repository'):
        assert not (repo/'objects/info/alternates').exists()
        assert not (repo/'.git/objects/info/alternates').exists()
    write_json(OUT/'generic-owner-restore-result.json',generic_restore)
    print('PASS full independent P4 generic owner-aborted restore, 18 receipts/cursors/marker retained; RESTORE-BLOCKED',flush=True)
    assert client.read(REPO,BRANCH)['commit_sha']==generic_pins['stream']['commit_sha']
    assert client.read(REPO,FB,a.FENCE_PATH)['commit_sha']==generic_pins['fence']['commit_sha']
    slot=__import__('actions_schedule').slot_at('signal',f['review']['stopped_at_ms']+4*14400000)
    yaml=(ROOT/'.github/workflows/signal.yml').read_bytes().replace(production_manifest.encode(),test_manifest.encode())
    (OUT/'synthetic-signal.yml').write_bytes(yaml)
    entry_pin=commit_file(code,'synthetic','.github/workflows/signal.yml',yaml,recovery_pin)
    runtime['entry_workflows']={'.github/workflows/signal.yml':hashlib.sha256(yaml).hexdigest()}
    p.meta=dict(id=503,run_attempt=1,run_number=2,event='workflow_dispatch',repository={'full_name':'synthetic/code'},
        path='.github/workflows/signal.yml',head_sha=entry_pin,head_branch='synthetic',created_at=iso(slot+1000),display_title='btc-v2:signal:created')
    rt=OUT/'core/.runtime';rt.mkdir(exist_ok=True);write_json(rt/'runtime.json',runtime);(rt/'data').mkdir(exist_ok=True)
    write_json(rt/'data/config.json',store.snapshot['engine']['config'])
    env=dict(BTC_DELIVERY_ADAPTER='github',BTC_DELIVERY_GITHUB_REPO=REPO,BTC_DELIVERY_GITHUB_BRANCH=BRANCH,
        BTC_DELIVERY_FENCE_BRANCH=FB,BTC_DELIVERY_STORE_ID='synthetic-store',BTC_DELIVERY_CODE_SHA=CORE,
        BTC_DELIVERY_BOT_IDENTITY=d['bot_identity'],BTC_DELIVERY_RUN_REPOSITORY='synthetic/code',
        BTC_DELIVERY_WORKFLOW='.github/workflows/signal.yml',BTC_DELIVERY_CONFIRMATION_POLICY=a.POLICY,
        BTC_DELIVERY_RUN_ID='503',BTC_DELIVERY_RUN_ATTEMPT='1',BTC_DELIVERY_RUNNER_ROOT=str(OUT),
        GITHUB_REPOSITORY='synthetic/code',GITHUB_RUN_ID='503',GITHUB_RUN_ATTEMPT='1',GITHUB_RUN_NUMBER='2',GITHUB_SHA=entry_pin,
        GITHUB_REF='refs/heads/synthetic',GITHUB_WORKFLOW_REF='synthetic/code/.github/workflows/signal.yml@refs/heads/synthetic',
        GITHUB_EVENT_NAME='workflow_dispatch',BTC_DELIVERY_GITHUB_TOKEN='SYNTHETIC-STORE',GITHUB_TOKEN='SYNTHETIC-META',
        TELEGRAM_BOT_TOKEN='SYNTHETIC-TRANSPORT',TELEGRAM_CHAT_ID='synthetic-target')
    import production_confirmation,main
    real=entry.run_runtime
    from strategy_core import Candle,FlowPoint
    signal_ts=slot//14400000*14400000-14400000
    candles=[Candle(ts,100,101,99,100) for ts in range(signal_ts-300*14400000,signal_ts+1,14400000)]
    from flow_contract import direct
    flow=[FlowPoint(c.ts,1000,1000,1000000,0,long_pct=50,oi_btc=10000,
        provenance={field:direct(c.ts,c.ts+14400000,'synthetic_'+field) for field in
            ('spot_cvd','fut_cvd','oi','oi_btc','funding','long_liq','short_liq','long_pct')}) for c in candles]
    oi=[{'ts':c.ts+14400000,'oi':1000000,'synthetic':True} for c in candles]
    write_json(OUT/'market-fixture.json',{'synthetic':True,'signal_ts':signal_ts,'candles':[c.__dict__ for c in candles],
        'flow':[f.__dict__ for f in flow],'oi_history':oi})
    def invoke(runtime,kind,data):return real(runtime,kind,data,fetch=lambda _:(candles,flow,oi))
    document=yaml_parser.safe_load((OUT/'synthetic-signal.yml').read_bytes())
    command=next(step['run'] for job in document['jobs'].values() for step in job['steps'] if step.get('run','').startswith('python3 -c '))
    tokens=shlex.split(command);args=tokens[3:];args[args.index('--manifest-sha256')+1]=hashlib.sha256((OUT/'extension/delivery-extension.json').read_bytes()).hexdigest()
    before=Path.cwd()
    real_gmtime=__import__('time').gmtime
    try:
        os.chdir(OUT)
        with patch.dict(os.environ,env),patch.object(sys,'argv',['-c']+args),patch.object(entry,'run_runtime',side_effect=invoke),\
             patch.object(production_confirmation.ProductionContentsClient,'open_request',staticmethod(p.open)),\
             patch.object(entry.time,'time',return_value=(slot+180000)/1000),\
             patch.object(main,'deliver_telegram',side_effect=AssertionError('NO SEND')),\
             patch.object(main.time,'gmtime',side_effect=lambda seconds=None:real_gmtime((slot+180000)/1000 if seconds is None else seconds)):
            try:exec(tokens[2],{'__name__':'__main__'})
            except SystemExit as done:assert done.code==0,'Workflow refused'
        final=json.loads(client.read(REPO,FB,a.FENCE_PATH)['body'])
        assert final['phase']=='closed' and final['run']['id']=='503' and 'outcome' not in final['completion']
        assert closed['completion']['outcome']=='aborted'
        fresh=g.read_only(client,REPO,BRANCH,'synthetic-store')
        assert fresh.snapshot['engine']['last_signal_ts']==signal_ts
        assert fresh.snapshot['control']['health']['successful_runs']['signal']['run']['last_signal_ts']==signal_ts
        print('PASS real engine persisted last_signal_ts='+str(signal_ts)+' from synthetic closed candles',flush=True)
        print('PASS actual workflow bootstrap -> fresh regular run 503 -> confirmed normal completion, no send',flush=True)
        print('PASS wrong synthetic target refused by unchanged production identity check',flush=True)
        # Exercise the real Watch workflow after the new regular Signal.
        watch_slot=__import__('actions_schedule').slot_at('watch',slot+900000)
        watch_raw=(ROOT/'.github/workflows/watch.yml').read_bytes().replace(production_manifest.encode(),test_manifest.encode())
        watch_pin=commit_file(code,'synthetic','.github/workflows/watch.yml',watch_raw,entry_pin)
        runtime['entry_workflows']['.github/workflows/watch.yml']=hashlib.sha256(watch_raw).hexdigest();write_json(rt/'runtime.json',runtime)
        p.meta=dict(id=504,run_attempt=1,run_number=3,event='workflow_dispatch',repository={'full_name':'synthetic/code'},
            path='.github/workflows/watch.yml',head_sha=watch_pin,head_branch='synthetic',created_at=iso(watch_slot+1000),display_title='btc-v2:watch:created')
        watch_env={**env,'GITHUB_RUN_ID':'504','GITHUB_RUN_NUMBER':'3','GITHUB_SHA':watch_pin,
            'GITHUB_WORKFLOW_REF':'synthetic/code/.github/workflows/watch.yml@refs/heads/synthetic',
            'BTC_DELIVERY_WORKFLOW':'.github/workflows/watch.yml','BTC_DELIVERY_RUN_ID':'504'}
        document=yaml_parser.safe_load(watch_raw);command=next(s['run'] for j in document['jobs'].values() for s in j['steps'] if s.get('run','').startswith('python3 -c '))
        watch_tokens=shlex.split(command);watch_args=watch_tokens[3:]
        candle=watch_slot//14400000*14400000
        raw=[[candle+i*14400000,'100','101','99','100','1',candle+(i+1)*14400000-1] for i in range(-35,1)]
        def watch_invoke(runtime,kind,data):return real(runtime,kind,data,watch_raw=raw,now_ms=watch_slot+180000)
        with patch.dict(os.environ,watch_env),patch.object(sys,'argv',['-c']+watch_args),patch.object(entry,'run_runtime',side_effect=watch_invoke),\
             patch.object(production_confirmation.ProductionContentsClient,'open_request',staticmethod(p.open)),\
             patch.object(entry.time,'time',return_value=(watch_slot+180000)/1000),patch.object(main,'deliver_telegram',side_effect=AssertionError('NO SEND')):
            try:exec(watch_tokens[2],{'__name__':'__main__'})
            except SystemExit as done:assert done.code==0,'Fresh Watch workflow refused'
        print('PASS recovery -> real Signal workflow -> real Watch workflow, confirmed closed fence and no send',flush=True)
        regular=g.read_only(client,REPO,BRANCH,'synthetic-store')
        assert regular.snapshot['engine']['_delivery']['messages']==recovered_store.snapshot['engine']['_delivery']['messages']
        import runpy,produktion_pages_export as pages
        renderer=OUT/'renderer';renderer.mkdir();git(renderer,'init')
        git(renderer,'config','core.autocrlf','false')
        (renderer/'.git/objects/info/alternates').write_bytes((OUT/'core/.git/objects').as_posix().encode()+b'\n')
        renderer_pin='769240621314677e13da5afbf32821d6a350c9df'
        git(renderer,'checkout','--detach',renderer_pin)
        assert hashlib.sha256((renderer/'site/c05-report.json').read_bytes()).hexdigest()=='6d64486e83917a01976296c4688fb019f6c56d6d66a0f9862df36041cafb6f19'
        page_raw=(ROOT/'.github/workflows/pages.yml').read_bytes().replace(production_manifest.encode(),test_manifest.encode())
        page_pin=commit_file(code,'synthetic','.github/workflows/pages.yml',page_raw,watch_pin)
        page_runtime=json.loads((ROOT/'ops/produktion/pages-runtime.disabled.json').read_bytes())
        page_runtime.update(enabled=True,python_version=list(sys.version_info[:3]),deployment=d,public_access=runtime['public_access'],
            entry_workflows={'.github/workflows/pages.yml':hashlib.sha256(page_raw).hexdigest()},
            renderer=dict(schema='btc-c05-renderer-v1',code_sha=renderer_pin,core_code_sha=CORE,
                runtime_config_sha256='3efe8a17330c228a75fe879d4e7c7ed0cade766e4a07ca0c05832b88aa3d282b',
                strategy_sha256='a99be30ae26a753f9734fbe2d67ac49f33e090a691904336421742f92420f787',
                report_sha256='6d64486e83917a01976296c4688fb019f6c56d6d66a0f9862df36041cafb6f19'))
        write_json(rt/'runtime.json',page_runtime)
        p.meta=dict(id=505,run_attempt=1,event='workflow_dispatch',repository={'full_name':'synthetic/code'},
            path='.github/workflows/pages.yml',head_sha=page_pin,head_branch='synthetic',created_at=iso(watch_slot+240000))
        page_env=dict(GITHUB_TOKEN='SYNTHETIC-META',GITHUB_REPOSITORY='synthetic/code',GITHUB_REF='refs/heads/synthetic',
            GITHUB_RUN_ID='505',GITHUB_RUN_ATTEMPT='1',GITHUB_SHA=page_pin,GITHUB_EVENT_NAME='workflow_dispatch',
            GITHUB_WORKFLOW_REF='synthetic/code/.github/workflows/pages.yml@refs/heads/synthetic')
        page_env.update(PATH=os.environ.get('PATH',''),SystemRoot=os.environ.get('SystemRoot',''))
        document=yaml_parser.safe_load(page_raw)
        names=('Export one closed store/fence pair (read only)','Validate exact complete C05 package before upload',
               'Verify unchanged closed pair immediately before deploy')
        page_commands=[next(step['run'] for job in document['jobs'].values() for step in job['steps'] if step.get('name')==name) for name in names]
        prior_puts=list(p.puts);page_now=(watch_slot+240000)/1000
        import reviewed_actions_entry
        os.chdir(OUT/'core')
        cases=[(name,command,page_now,0,None) for name,command in zip(names,page_commands)]
        stale=page_commands[0].replace('--out .runtime/public','--out .runtime/stale-public')
        cases.append(('Reject stale data without changing freshness guard',stale,(signal_ts+12*3600000+1)/1000,20,'Signal slice too old or in future'))
        for name,command,clock,expected,error_reason in cases:
            parsed=shlex.split(command);errors=[]
            def trace(frame,event,arg):
                if event=='exception' and frame.f_code.co_filename.endswith('c05_pages_export.py'):
                    errors.append((frame.f_code.co_name,arg[0].__name__,str(arg[1])))
                return trace
            with patch.dict(os.environ,page_env,clear=True),patch.object(sys,'argv',['-c']+parsed[3:]),\
                 patch.object(production_confirmation.ProductionContentsClient,'open_request',staticmethod(p.open)),\
                 patch.object(reviewed_actions_entry.EntryReader,'open_request',staticmethod(p.open)),\
                 patch.object(entry.time,'time',return_value=clock):
                sys.settrace(trace)
                try:
                    try:exec(parsed[2],{'__name__':'__main__'})
                    except SystemExit as done:assert done.code==expected,(name,errors[-5:])
                finally:sys.settrace(None)
            if error_reason:assert any(error_reason in item[2] for item in errors),(name,errors)
            print('PASS actual C05 Pages workflow step: '+name,flush=True)
        assert not (rt/'stale-public').exists()
        assert p.puts==prior_puts,'Pages may not write the store'
        package=rt/'public';manifest=json.loads((package/'projection-manifest.json').read_bytes())
        projection=json.loads((package/manifest['projection']).read_bytes())
        assert projection['signal_asof_ms']==signal_ts
        assert hashlib.sha256((package/'c05-report.json').read_bytes()).hexdigest()==page_runtime['renderer']['report_sha256']
        write_json(OUT/'c05-page-result.json',dict(signal_asof_ms=projection['signal_asof_ms'],simulated_now_ms=int(page_now*1000),
            package_check=True,predeploy_check=True,renderer=page_runtime['renderer'],stream_commit=client.read(REPO,BRANCH)['commit_sha'],
            fence_commit=client.read(REPO,FB,a.FENCE_PATH)['commit_sha'],store_writes=0))
        print('PASS serverjournal recovery -> fresh Signal -> Watch -> C05 renderer/package/predeploy; same states, no sends',flush=True)
        write_json(OUT/'test-results.json',dict(synthetic=True,p4_restore=True,generic_owner_restore=True,server_journal=True,
            fresh_workflow=True,watch_workflow=True,c05_workflow=True,package_check=True,predeploy_check=True,
            stale_data_refused=True,engine_persisted_signal_ts=signal_ts,retained_receipts=18,wrong_target_refused=True,
            production_module_unchanged=hashlib.sha256((ROOT/'engine/aborted_maintenance.py').read_text().encode()).hexdigest()==f['production_source_sha256']))
    finally:os.chdir(before)

if __name__=='__main__':
    if '--worker' in sys.argv:
        with patch('socket.socket.connect',side_effect=AssertionError('REAL NETWORK FORBIDDEN')):worker()
    else:
        generate()
        raise SystemExit(subprocess.call([sys.executable,'-B',__file__,'--worker']))
