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
    from test_production_runtime import seeded
    import durable_delivery as durable,telegram_outbox as box,run_health
    (OUT/'seed').mkdir();store,data,paths=seeded(OUT/'seed')
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
        self.fixture=fixture;self.puts=[];self.meta=None
    def local(self,branch):return OUT/('stream.git' if branch==BRANCH else 'fence.git')
    def heads(self):return [(branch,git(self.local(branch),'rev-parse','refs/heads/'+branch).decode().strip()) for branch in (BRANCH,FB)]
    def locate(self,pin,path):
        return rec(self.local(BRANCH if path==g.STORE_PATH else FB),pin,path)
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
        elif tail.startswith('/actions/runs/'):value=self.meta
        elif tail.startswith('/compare/'):
            value=dict(base_commit={'sha':CORE},merge_base_commit={'sha':CORE},status='ahead')
        elif tail.startswith('/git/ref/heads/'):value={'object':{'sha':dict(self.heads())[tail.rsplit('/',1)[1]]}}
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
    owner_slot=f['review']['stopped_at_ms']+60000
    owned_run=dict(number=2,id='4999',attempt='1',workflow='.github/workflows/watch.yml',kind='watch',
                   expected_start_ms=str(owner_slot),deadline_utc_ms=owner_slot+900000)
    opened.update(phase='open',completion=None,write_id='synthetic-generic-open',run=owned_run)
    opened['cursors'][owned_run['workflow']]={'number':2,'id':'4999'}
    openpin=commit_file(p.local(FB),FB,a.FENCE_PATH,canonical(opened).encode(),prior['commit_sha'])
    owned=g.GitHubStore(client,REPO,BRANCH,'synthetic-store','4999','1');owned.__enter__()
    observed=client.read(REPO,BRANCH);old_env=json.loads(observed['body'])
    review=dict(old_fence_commit=openpin,old_fence_sha256=hashlib.sha256(canonical(opened).encode()).hexdigest(),
        run_sha256=digest({'synthetic_completed_failure':'4999'}),jobs_sha256=digest({'synthetic_hosted_worker_terminated':True}),
        policy_sha256=digest(runtime),confirmed_at_ms=owner_slot+1000,workers_terminated=True,run_completed=True,
        old_owner=old_env['snapshot']['control']['owner'],old_revision=old_env['revision'],old_snapshot_digest=old_env['body_digest'],old_stream_commit=observed['commit_sha'])
    released,event=recover.release_owner(old_env,owned_run,d,review,'synthetic-generic-release')
    client.update(REPO,BRANCH,observed['blob_sha'],canonical(released).encode(),'synthetic-generic-release')
    saved=client.read(REPO,BRANCH);assert client.parents(REPO,saved['commit_sha'])==[observed['commit_sha']]
    recovered_store=g.read_only(client,REPO,BRANCH,'synthetic-store')
    recovered=recover.owner_candidate(opened,released,recovered_store.confirmed_record(),review,event,'synthetic-generic-close')
    fence_old=client.read(REPO,FB,a.FENCE_PATH)
    client.update(REPO,FB,fence_old['blob_sha'],canonical(recovered).encode(),'synthetic-generic-close',a.FENCE_PATH)
    final_recovery=client.read(REPO,FB,a.FENCE_PATH);assert client.parents(REPO,final_recovery['commit_sha'])==[openpin]
    assert recovered['completion']['outcome']=='aborted'
    print('PASS generic owner recovery -> two confirmed actual Git CAS writes; old historical abort preserved',flush=True)
    slot=__import__('actions_schedule').slot_at('signal',f['review']['stopped_at_ms']+4*14400000)
    code=OUT/'entry.git';code.mkdir();git(code,'init','--bare')
    (code/'objects/info/alternates').write_bytes((OUT/'core/.git/objects').as_posix().encode()+b'\n')
    production_manifest=hashlib.sha256((ROOT/'delivery-extension.json').read_bytes()).hexdigest()
    test_manifest=hashlib.sha256((OUT/'extension/delivery-extension.json').read_bytes()).hexdigest()
    yaml=(ROOT/'.github/workflows/signal.yml').read_bytes().replace(production_manifest.encode(),test_manifest.encode())
    (OUT/'synthetic-signal.yml').write_bytes(yaml)
    entry_pin=commit_file(code,'synthetic','.github/workflows/signal.yml',yaml,CORE)
    runtime['entry_workflows']={'.github/workflows/signal.yml':hashlib.sha256(yaml).hexdigest()}
    p.meta=dict(id=501,run_attempt=1,run_number=2,event='workflow_dispatch',repository={'full_name':'synthetic/code'},
        path='.github/workflows/signal.yml',head_sha=entry_pin,head_branch='synthetic',created_at=iso(slot+1000),display_title='btc-v2:signal:created')
    rt=OUT/'core/.runtime';rt.mkdir(exist_ok=True);write_json(rt/'runtime.json',runtime);(rt/'data').mkdir(exist_ok=True)
    write_json(rt/'data/config.json',store.snapshot['engine']['config'])
    env=dict(BTC_DELIVERY_ADAPTER='github',BTC_DELIVERY_GITHUB_REPO=REPO,BTC_DELIVERY_GITHUB_BRANCH=BRANCH,
        BTC_DELIVERY_FENCE_BRANCH=FB,BTC_DELIVERY_STORE_ID='synthetic-store',BTC_DELIVERY_CODE_SHA=CORE,
        BTC_DELIVERY_BOT_IDENTITY=d['bot_identity'],BTC_DELIVERY_RUN_REPOSITORY='synthetic/code',
        BTC_DELIVERY_WORKFLOW='.github/workflows/signal.yml',BTC_DELIVERY_CONFIRMATION_POLICY=a.POLICY,
        BTC_DELIVERY_RUN_ID='501',BTC_DELIVERY_RUN_ATTEMPT='1',BTC_DELIVERY_RUNNER_ROOT=str(OUT),
        GITHUB_REPOSITORY='synthetic/code',GITHUB_RUN_ID='501',GITHUB_RUN_ATTEMPT='1',GITHUB_RUN_NUMBER='2',GITHUB_SHA=entry_pin,
        GITHUB_REF='refs/heads/synthetic',GITHUB_WORKFLOW_REF='synthetic/code/.github/workflows/signal.yml@refs/heads/synthetic',
        GITHUB_EVENT_NAME='workflow_dispatch',BTC_DELIVERY_GITHUB_TOKEN='SYNTHETIC-STORE',GITHUB_TOKEN='SYNTHETIC-META',
        TELEGRAM_BOT_TOKEN='SYNTHETIC-TRANSPORT',TELEGRAM_CHAT_ID='synthetic-target')
    import production_confirmation,main
    real=entry.run_runtime
    def invoke(runtime,kind,data):return real(runtime,kind,data,fetch=lambda _:([],[],[]))
    document=yaml_parser.safe_load((OUT/'synthetic-signal.yml').read_bytes())
    command=next(step['run'] for job in document['jobs'].values() for step in job['steps'] if step.get('run','').startswith('python3 -c '))
    tokens=shlex.split(command);args=tokens[3:];args[args.index('--manifest-sha256')+1]=hashlib.sha256((OUT/'extension/delivery-extension.json').read_bytes()).hexdigest()
    before=Path.cwd()
    try:
        os.chdir(OUT)
        with patch.dict(os.environ,env),patch.object(sys,'argv',['-c']+args),patch.object(entry,'run_runtime',side_effect=invoke),\
             patch.object(production_confirmation.ProductionContentsClient,'open_request',staticmethod(p.open)),\
             patch.object(entry.time,'time',return_value=(slot+180000)/1000),\
             patch.object(main,'deliver_telegram',side_effect=AssertionError('NO SEND')):
            try:exec(tokens[2],{'__name__':'__main__'})
            except SystemExit as done:assert done.code==0,'Workflow refused'
        final=json.loads(client.read(REPO,FB,a.FENCE_PATH)['body'])
        assert final['phase']=='closed' and final['run']['id']=='501' and 'outcome' not in final['completion']
        assert closed['completion']['outcome']=='aborted'
        print('PASS actual workflow bootstrap -> fresh regular run 501 -> confirmed normal completion, no send',flush=True)
        print('PASS wrong synthetic target refused by unchanged production identity check',flush=True)
        # Exercise the real Watch workflow after the new regular Signal.
        watch_slot=__import__('actions_schedule').slot_at('watch',slot+900000)
        watch_raw=(ROOT/'.github/workflows/watch.yml').read_bytes().replace(production_manifest.encode(),test_manifest.encode())
        watch_pin=commit_file(code,'synthetic','.github/workflows/watch.yml',watch_raw,entry_pin)
        runtime['entry_workflows']['.github/workflows/watch.yml']=hashlib.sha256(watch_raw).hexdigest();write_json(rt/'runtime.json',runtime)
        p.meta=dict(id=503,run_attempt=1,run_number=3,event='workflow_dispatch',repository={'full_name':'synthetic/code'},
            path='.github/workflows/watch.yml',head_sha=watch_pin,head_branch='synthetic',created_at=iso(watch_slot+1000),display_title='btc-v2:watch:created')
        watch_env={**env,'GITHUB_RUN_ID':'503','GITHUB_RUN_NUMBER':'3','GITHUB_SHA':watch_pin,
            'GITHUB_WORKFLOW_REF':'synthetic/code/.github/workflows/watch.yml@refs/heads/synthetic',
            'BTC_DELIVERY_WORKFLOW':'.github/workflows/watch.yml','BTC_DELIVERY_RUN_ID':'503'}
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
        import runpy,produktion_pages_export as pages
        page_raw=(ROOT/'.github/workflows/pages.yml').read_bytes().replace(production_manifest.encode(),test_manifest.encode())
        page_pin=commit_file(code,'synthetic','.github/workflows/pages.yml',page_raw,watch_pin)
        page_runtime=json.loads((ROOT/'ops/produktion/pages-runtime.disabled.json').read_bytes())
        page_runtime.update(enabled=True,python_version=list(sys.version_info[:3]),deployment=d,public_access=runtime['public_access'],
            entry_workflows={'.github/workflows/pages.yml':hashlib.sha256(page_raw).hexdigest()})
        write_json(rt/'pages-runtime.json',page_runtime)
        p.meta=dict(id=504,run_attempt=1,event='workflow_dispatch',repository={'full_name':'synthetic/code'},
            path='.github/workflows/pages.yml',head_sha=page_pin,head_branch='synthetic',created_at=iso(watch_slot+240000))
        page_env=dict(GITHUB_TOKEN='SYNTHETIC-META',GITHUB_REPOSITORY='synthetic/code',GITHUB_REF='refs/heads/synthetic',
            GITHUB_RUN_ID='504',GITHUB_RUN_ATTEMPT='1',GITHUB_SHA=page_pin,GITHUB_EVENT_NAME='workflow_dispatch',
            GITHUB_WORKFLOW_REF='synthetic/code/.github/workflows/pages.yml@refs/heads/synthetic')
        page_env.update(PATH=os.environ.get('PATH',''),SystemRoot=os.environ.get('SystemRoot',''))
        with patch.dict(os.environ,page_env,clear=True),patch.object(sys,'argv',['produktion_pages_export.py','--runtime',str(rt/'pages-runtime.json'),
                '--config',str(rt/'data/config.json'),'--out',str(rt/'pages-result')]),\
             patch.object(production_confirmation.ProductionContentsClient,'open_request',staticmethod(p.open)),\
             patch.object(pages.ReadClient,'open_request',staticmethod(p.open)):
            try:runpy.run_path(str(ROOT/'tools/produktion_pages_export.py'),run_name='__main__')
            except SystemExit as done:assert done.code==0,'Actual Pages CLI refused'
        assert (rt/'pages-result/projection-manifest.json').is_file()
        print('PASS recovery -> Signal -> Watch -> actual Pages projection CLI, no deployment and no send',flush=True)
        write_json(OUT/'test-results.json',dict(synthetic=True,p4_restore=True,fresh_workflow=True,wrong_target_refused=True,
            production_module_unchanged=hashlib.sha256((ROOT/'engine/aborted_maintenance.py').read_text().encode()).hexdigest()==f['production_source_sha256']))
    finally:os.chdir(before)

if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        generate()
        raise SystemExit(subprocess.call([sys.executable,'-B',__file__,'--worker']))
