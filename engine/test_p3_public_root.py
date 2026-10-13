"""Actual -B public uploader. Fixture history is translated, never real Ledger."""
from copy import deepcopy
from datetime import datetime,timezone,timedelta
import hashlib,json,os,shutil,sqlite3,subprocess,sys,tempfile
from pathlib import Path
W=Path(__file__).resolve().parents[1];sys.path[:0]=[str(W/'tools'),str(W/'engine')]
import p3_public_root as u
import p3_github_probe as p
import p3_rules403 as r
import test_p3_script_start as s
NOW='2026-10-14T00:00:00Z'

def inputs():return Path(os.environ.get('P3_PUBLIC_FIXTURE_INPUTS',str(W.parent/'audit-backups')))
def read(f):return json.loads(Path(f).read_text(encoding='utf-8-sig'))
def save(f,x):Path(f).write_text(p.canonical(x),encoding='utf-8')

def fixture(td,*,continuation=False,root_success=False):
    root=Path(td);session=root/'session';session.mkdir();base=inputs()
    plan=read(base/'p3-bootstrap-freigabevorbereitung-20261011/PLAN-NOT-APPROVED.json')
    oldplan=deepcopy(plan);plan['journal_directory']=str(session)
    i=read(base/'p3-reader-20h-20261012/INSPECTION.json');g=read(base/'p3-reader-20h-20261012/GRANT.json')
    rows=read_rows(base/('p3-public-root-erfolg-20261013/session-snapshot/bootstrap-public-missing-branch-once.jsonl' if root_success else 'p3-public-root-404-befund-20261012/session-snapshot/bootstrap-public-root-once.jsonl' if continuation else 'p3-tarifbefund-20261012/session-snapshot/inspect.jsonl'))
    original_root=Path(i['root']['directory']);shutil.copytree(base/'p3-tarifbefund-20261012/root-snapshot',root/'execution')
    proc=subprocess.Popen([sys.executable,'-B','-c','pass']);assert proc.wait(timeout=10)==0
    mapping={p.digest(oldplan):p.digest(plan),oldplan['journal_directory']:str(session),str(original_root):str(root/'execution')}
    def transform(x,key=None):
        if isinstance(x,dict):return {k:transform(v,k) for k,v in x.items()}
        if isinstance(x,list):return [transform(v) for v in x]
        if key in ('pid','original_pid'):return proc.pid
        return mapping.get(x,x) if isinstance(x,str) else x
    parent=i['parent_amendment'];diag=parent['interrupted_diagnosis']['amendment'];reader=parent['reader401_amendment']
    def bind(obj):
        value=transform(obj);mapping[p.digest(obj)]=p.digest(value);return value
    bind(reader['original_grant'])
    translated=[];rr=dd=pp=ii=None
    for j,row in enumerate(rows):
        if j==5:bind(reader['original_grant']);rr=bind(reader);bind(parent['reader401_grant'])
        if j==17:dd=bind(diag);bind(parent['interrupted_diagnosis']['grant'])
        if j==21:bind(parent['reader_validity']);pp=bind(parent);bind(i['parent_grant'])
        if j==24:ii=bind(i);gg=bind(g)
        if j==35:
            oldpublic=bind(read(base/'p3-public-root-hauptchat-abnahme-20261012/PUBLIC-AMENDMENT.json'))
            oldgrant=bind(read(base/'p3-public-root-hauptchat-abnahme-20261012/PUBLIC-GRANT.json'))
        if j==53:
            successful=bind(read(base/'p3-public-branch-hauptchat-abnahme-20261013/PUBLIC-CONTINUATION.json'))
            successgrant=bind(read(base/'p3-public-branch-hauptchat-abnahme-20261013/PUBLIC-GRANT.json'))
        x=transform(row);x.pop('hash');x['hash']=p.digest(x);mapping[row['hash']]=x['hash'];translated.append(x)
    starts=[j for j,x in enumerate(translated) if x['event']=='phase_start']
    for n,j in enumerate(starts):
        stop=starts[n+1] if n+1<len(starts) else len(translated)
        (session/translated[j]['journal']).write_text(''.join(p.canonical(x)+'\n' for x in translated[:stop]),encoding='utf-8',newline='\n')
        save(session/('attempt-'+translated[j]['phase']+'.json'),{k:translated[j][k] for k in ('plan_sha256','phase','journal','pid','predecessor')})
    (session/'probe-session.lock').write_bytes(b'0')
    db=sqlite3.connect(session/'probe-session.sqlite3');db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE events (seq INTEGER PRIMARY KEY,body TEXT NOT NULL)')
    db.execute('CREATE TABLE frontier (id INTEGER PRIMARY KEY CHECK(id=1),plan TEXT NOT NULL,journal TEXT NOT NULL,published TEXT NOT NULL,highwater TEXT NOT NULL)')
    db.executemany('INSERT INTO events(body) VALUES (?)',[(p.canonical(x),) for x in translated])
    db.execute('INSERT INTO frontier VALUES (1,?,?,?,?)',(p.digest(plan),u.CONTINUE+'.jsonl' if root_success else u.PHASE+'.jsonl' if continuation else 'inspect.jsonl',translated[-1]['hash'],translated[-1]['utc']));db.commit();db.close()
    save(root/'plan.json',plan)
    a=u.template(u.CONTINUE if continuation else u.PHASE);a.update(original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],root=ii['root'],
        execution_code=s.code_for(plan),not_before_utc=NOW,expires_utc='2026-10-14T20:00:00Z',time_authorization_sha256='e'*64)
    script=base/'p3-reader-20h-20261012/reader_inspection.py'
    a['history'].update(inspection=ii,grant=gg,operator_script={'path':str(script),'sha256':u.c.sha(script)},code_materialization=r.materialization(ii['execution_code']))
    folder=base/'p3-public-umstellung-20261012';a['visibility'].update(acceptance_path=str(folder/'ACCEPTANCE.json'),files_sha256={n:u.c.sha(folder/n) for n in ('ACCEPTANCE.json','PUBLIC-CONFIRMED.png','ACTIONS-DISABLED.png','PAGES-DISABLED.png','RULESETS-EMPTY.png')})
    a['predecessor'].update(frontier_hash=translated[-1]['hash'],highwater=translated[-1]['utc'],files_sha256={n:u.c.sha(session/n) for n in r.session_files(translated)})
    a['review'].update(reviewer='offline-fixture-only',evidence_sha256='e'*64,original_pid=proc.pid,observed_utc=NOW,
        terminal_code_path_checked=True,human_terminal_end_report=True,all_workers_ended=True,triggers_paused=True,human_review=True)
    if continuation:a['stopped_public'].update(amendment=oldpublic,grant=oldgrant,code_materialization=r.materialization(oldpublic['execution_code']))
    save(root/'fixture-history-translation.json',{'copied_real_input_translated_to_fixture':True,'plan_directory_and_digests_rebound':True,'actual_ended_fixture_pid':proc.pid,'no_current_runtime_gate_bridged':True})
    if root_success:
        save(root/'successful-root-amendment.json',successful);save(root/'successful-root-grant.json',successgrant)
    return plan,a

def read_rows(f):return [json.loads(x) for x in Path(f).read_text(encoding='utf-8').splitlines()]

def direct(root,a,*,mode='positive',kill=None,at=NOW,expiry=None,grant=None,approved=None):
    root=Path(root);out=root/'attempts';out.mkdir(exist_ok=True);out=out/('%03d'%len(list(out.iterdir())));out.mkdir()
    plan=read(root/'plan.json');g=grant or s.t.fixture_grant(plan,a);g['phase']=a['phase']
    if grant is None:g['expires_utc']=a['expires_utc']
    g['review_sha256']=p.digest(a) if grant is None else g['review_sha256']
    cfg={'root':str(root),'output':str(out),'mode':mode,'kill':kill,'at':at,'expiry':expiry,'deadline':a['expires_utc']}
    for name,x in [('amendment.json',a),('grant.json',g),('config.json',cfg)]:save(out/name,x)
    hook=out/'startup';hook.mkdir();(hook/'sitecustomize.py').write_text('import sys\nsys.path[:0]='+repr([str(W/'tools'),str(W/'engine')])+'\nimport p3_public_fixture\np3_public_fixture.install()\n',encoding='utf-8')
    env=p.git_environment();env.update(PYTHONPATH=str(hook),P3_PUBLIC_FIXTURE=str(out/'config.json'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
    argv=[sys.executable,'-B',str(W/'tools/p3_public_root.py'),'--real','--phase',a['phase'],'--plan',str(root/'plan.json'),'--amendment',str(out/'amendment.json'),'--grant',str(out/'grant.json'),'--approved-amendment-sha256',approved or p.digest(a)]
    proc=subprocess.run(argv,env=env,capture_output=True,timeout=120);(out/'output.txt').write_bytes(proc.stdout+proc.stderr)
    save(out/'parent-wait.json',{'returncode':proc.returncode,'argv':argv});wire=read(out/'wire.json') if (out/'wire.json').exists() else None
    assert proc.returncode in (0,2,3,71),proc.stderr.decode();return proc.returncode,wire,out

def test_public_actual_positive_root_counters_no_activation_and_replay():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=fixture(root);before=(root/'session/inspect.jsonl').read_bytes()
        code,wire,out=direct(root,a);assert code==0 and len(wire['http'])==23 and wire['pushes']==1 and wire['prompts']==['Reader','Writer'],(out/'output.txt').read_text()
        rr=read_rows(root/'session'/ (u.PHASE+'.jsonl'));assert rr[-1]['counts']=={'GET':30,'PUT':0,'GIT_PUSH':1} and rr[-1]['result']=='confirmed'
        assert rr[-1]['bootstrap_case_counts']==rr[-1]['counts'] and rr[-1]['phase_counts']=={'GET':23,'PUT':0,'GIT_PUSH':1}
        req=[x for x in rr if x['event']=='request' and x['phase']==u.PHASE];assert all(x['budget_phase']=='bootstrap' for x in req)
        assert (root/'session/inspect.jsonl').read_bytes()==before and (root/'session'/(u.PHASE+'.jsonl')).read_bytes().startswith(before)
        assert direct(root,a)[1]['prompts']==[]
        save(root/'positive-result.json',{'counts':rr[-1]['counts'],'inspector_reads_in_bootstrap':2,'historical_prefix_unchanged':True})

def test_public_wrong_bindings_and_live_process_stop_before_input():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=fixture(root)
        for mode in ('scope','repo','seed','path','code','frontier','files','review','process','grant','hash','window'):
            x=deepcopy(a);original=deepcopy(plan);g=None;approved=None
            if mode=='scope':x['scope']='private'
            if mode=='repo':plan['repository_id']+=1
            if mode=='seed':plan['seed_commit']='f'*40
            if mode=='path':plan['path']='other.json'
            if mode=='code':x['execution_code']['code_pins']['tools/p3_public_root.py']='f'*64
            if mode=='frontier':x['predecessor']['frontier_hash']='f'*64
            if mode=='files':x['predecessor']['files_sha256']['probe-session.sqlite3']='f'*64
            if mode=='review':x['review']['human_review']=False
            if mode=='process':x['review']['original_pid']=os.getpid()
            if mode=='grant':g=s.t.fixture_grant(plan,x);g['human_authorization']=False
            if mode=='hash':approved='f'*64
            if mode=='window':x['expires_utc']='2026-10-14T20:00:01Z'
            save(root/'plan.json',plan)
            try:
                code,w,out=direct(root,x,grant=g,approved=approved);assert code==2 and not w['prompts'] and not w['http'];save(out/'countercase.json',{'mode':mode})
            finally:plan=original;save(root/'plan.json',plan)

def test_public_api_privacy_settings_writer_and_readback_denials():
    for mode in ('private','wrong-repo','403','rules-present','writer403','bad-parent','bad-tree','bad-body','lost-push'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=fixture(root);code,w,out=direct(root,a,mode=mode);assert code==2
            assert w['pushes']==int(mode in ('bad-parent','bad-tree','bad-body','lost-push'))
            assert w['prompts']==(['Reader','Writer'] if mode in ('writer403','bad-parent','bad-tree','bad-body','lost-push') else ['Reader'])
            rr=read_rows(root/'session'/(u.PHASE+'.jsonl'));assert not any(x['event']=='phase_end' and x.get('result')=='confirmed' for x in rr[35:])
            if mode=='lost-push':assert len(w['http'])==7
            assert direct(root,a)[1]['prompts']==[];save(out/'countercase.json',{'mode':mode,'confirmed':False})

def test_public_input_cancel_before_start_preserves_all_session_bytes():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=fixture(root);before={f.name:u.c.sha(f) for f in (root/'session').iterdir()}
        code,w,_=direct(root,a,mode='input-cancel');assert code==3 and not w['http']
        assert before=={f.name:u.c.sha(f) for f in (root/'session').iterdir()}
        assert direct(root,a)[0]==0

def test_public_deadlines_and_lost_answer_are_counted_without_confirm():
    for mode in ('before-start','exact-end','reader','before-GET','writer','before-GIT_PUSH','push-response','response','before-confirmed'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=fixture(root);at=NOW
            if mode=='before-start':at='2026-10-13T23:59:59Z'
            if mode=='exact-end':at=a['expires_utc']
            code,w,out=direct(root,a,at=at,expiry=mode);assert code==2
            if mode in ('before-start','exact-end'):assert not w['prompts'] and not w['http']
            if mode=='reader':assert not w['http'] and not (root/'session'/('attempt-'+u.PHASE+'.json')).exists()
            path=root/'session'/(u.PHASE+'.jsonl')
            if path.exists():assert not any(x['event']=='phase_end' and x.get('result')=='confirmed' for x in read_rows(path)[35:])
            save(out/'countercase.json',{'mode':mode,'confirmed':False})

def test_public_new_review_prepare_durable_hard_loss_blocks_replay():
    for event in ('public_root_review','public_push_prepare'):
        for point in ('before_commit','after_commit','after_mirror','after_publish'):
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);plan,a=fixture(root);code,w,out=direct(root,a,kill=[point,event]);assert code==71 and w is None
                trace=(out/'outbound.jsonl').read_text().splitlines() if (out/'outbound.jsonl').exists() else []
                assert len(trace)==(0 if event=='public_root_review' else 7)
                assert not any(json.loads(x)['method']=='GIT_PUSH' for x in trace)
                assert direct(root,a)[1]['prompts']==[]

def test_public_unknown_prior_mutation_missing_marker_live_exact_pid_and_kernel_lock():
    for mode in ('unknown','prior-put','prior-push','missing-marker','live-exact-pid','kernel-lock','prior-preparation'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=fixture(root);session=root/'session'
            if mode in ('unknown','prior-put','prior-push','live-exact-pid'):
                rr=read_rows(session/'inspect.jsonl')
                if mode=='unknown':rr[32]['result']='unknown'
                elif mode=='live-exact-pid':rr[24]['pid']=os.getpid();a['review']['original_pid']=os.getpid()
                else:rr[31]['method']='PUT' if mode=='prior-put' else 'GIT_PUSH'
                counts={'GET':0,'PUT':0,'GIT_PUSH':0};prior='0'*64
                for row in rr:
                    row.pop('hash');row['previous_hash']=prior
                    if row['event']=='request':counts[row['method']]+=1
                    row['counts']=deepcopy(counts);row['hash']=p.digest(row);prior=row['hash']
                (session/'inspect.jsonl').write_text(''.join(p.canonical(x)+'\n' for x in rr),encoding='utf-8',newline='\n')
                save(session/'attempt-inspect.json',{k:rr[24][k] for k in ('plan_sha256','phase','journal','pid','predecessor')})
                db=sqlite3.connect(session/'probe-session.sqlite3');db.execute('DELETE FROM events');db.executemany('INSERT INTO events(body) VALUES (?)',[(p.canonical(x),) for x in rr]);db.execute('UPDATE frontier SET published=?',(rr[-1]['hash'],));db.commit();db.close()
                a['predecessor'].update(frontier_hash=rr[-1]['hash'],counts=rr[-1]['counts'],files_sha256={n:u.c.sha(session/n) for n in r.session_files(rr)})
            if mode=='missing-marker':(session/'attempt-inspect.json').rename(session/'held-marker')
            if mode=='prior-preparation':(root/'execution/synthetic-askpass.py').write_text('fixture prior preparation')
            handle=None
            if mode=='kernel-lock':
                handle=(session/'probe-session.lock').open('r+b');handle.seek(0)
                if os.name=='nt':
                    import msvcrt;msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl;fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:
                code,w,out=direct(root,a);assert code==2 and not w['prompts'] and not w['http'];save(out/'countercase.json',{'mode':mode})
            finally:
                if handle:handle.close()
