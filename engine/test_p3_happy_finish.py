import os,sys,json,sqlite3,subprocess,tempfile
from pathlib import Path
from copy import deepcopy
import test_p3_happy_readback as t
import p3_happy_finish as f
n=t.n;p=f.p;W=n.W

def fixture(td):
    root=Path(td);plan,old375=t.fixture(root);base=n.inputs()
    old=n.read(base/'p3-happy-abgleich-start-20261013/READER-CONTRACT.json');g=n.read(base/'p3-happy-abgleich-start-20261013/READER-GRANT.json')
    old.update(original_plan_sha256=p.digest(plan),operations=old375['operations'],initial_grant=old375['initial_grant'],historical_code_materialization=old375['historical_code_materialization'])
    old['entry']=old375['entry'];old['review']['original_pid']=old375['review']['original_pid']
    proc=subprocess.Popen([sys.executable,'-B','-c','pass']);assert proc.wait(timeout=10)==0
    g.update(plan_sha256=p.digest(plan),review_sha256=p.digest(old))
    rows=n.read_rows(root/'session/public-store-happy.jsonl');real=n.read_rows(base/'p3-happy-claim-bestaetigt-20261013/session-snapshot'/ (f.h.PHASE+'.jsonl'))
    for x in real[375:]:
        x=deepcopy(x);x.update(plan_sha256=p.digest(plan),previous_hash=rows[-1]['hash'])
        if x['event']=='phase_start':x.update(pid=proc.pid,predecessor=rows[-1]['hash'])
        if x['event']=='authorization':x.update(grant_sha256=p.digest(g),review_sha256=p.digest(old))
        if x['event']=='happy_readback_review':x.update(amendment_sha256=p.digest(old),grant=g)
        x.pop('hash');x['hash']=p.digest(x);rows.append(x)
    (root/'session'/ (f.h.PHASE+'.jsonl')).write_text(''.join(p.canonical(x)+'\n' for x in rows),encoding='utf-8',newline='\n')
    n.save(root/'session'/ ('attempt-'+f.h.PHASE+'.json'),{k:rows[375][k] for k in ('plan_sha256','phase','journal','pid','predecessor')})
    db=sqlite3.connect(root/'session/probe-session.sqlite3');db.execute('DELETE FROM events');db.executemany('INSERT INTO events(body) VALUES (?)',[(p.canonical(x),) for x in rows]);db.execute('UPDATE frontier SET journal=?,published=?,highwater=?',(f.h.PHASE+'.jsonl',rows[-1]['hash'],rows[-1]['utc']));db.commit();db.close()
    a=f.template();a.update(original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],reader_contract=old,reader_grant=g,
        reader_code_materialization=f.r.materialization(old['execution_code']),execution_code=n.s.code_for(plan),not_before_utc=n.NOW,expires_utc='2026-10-14T20:00:00Z')
    a['entry'].update(frontier_hash=rows[-1]['hash'],highwater=rows[-1]['utc'],files_sha256={x:f.c.sha(root/'session'/x) for x in f.r.session_files(rows)})
    a['review'].update(original_pid=rows[180]['pid'],reader_pid=proc.pid,reader_ended=True,reviewer='fixture-only',evidence_sha256='e'*64,observed_utc=n.NOW,
        terminal_code_path_checked=True,human_terminal_end_report=True,all_workers_ended=True,triggers_paused=True,human_review=True)
    model=n.read(root/'body-model.json');records={}
    for sha,v in model['records'].items():
        target=f.CLAIM if sha=='f'*40 else sha
        records[target]={'body':v['body'],'blob':v['blob_sha'],'parents':model['parents'].get(sha,[]),'tree':p.hashlib.sha1(b'tree'+p.base64.b64decode(v['body'])).hexdigest()}
    records[f.CLAIM]['tree']='e215e1c7d18869bed6ad9b46127994f1f16e4b14'
    n.save(root/'api-state.json',{'records':records,'head':f.CLAIM,'accepted':0,'pending':None})
    f.confirmed_reader(plan,rows,a)
    return plan,a

def direct(root,a,section='close',mode='normal',review=None):
    root=Path(root);folder=root/'finish-attempts';folder.mkdir(exist_ok=True);out=folder/('%03d'%len(list(folder.iterdir())));out.mkdir()
    plan=n.read(root/'plan.json');db=sqlite3.connect(root/'session/probe-session.sqlite3');front=db.execute('SELECT journal,published FROM frontier').fetchone();db.close();rows=n.read_rows(root/'session'/front[0])
    g=f.grant_template(section);g.update(plan_sha256=p.digest(plan),amendment_sha256=p.digest(a),review_sha256=p.digest(review) if section=='takeover' else p.digest(a),human_authorization=True,approved_by='fixture-only',approval_evidence_sha256='e'*64,expires_utc=a['expires_utc'],entry_journal=front[0],entry_rows=len(rows),entry_frontier_hash=front[1],entry_files_sha256={x:f.c.sha(root/'session'/x) for x in f.r.session_files(rows)})
    for name,val in [('amendment.json',a),('grant.json',g),('config.json',{'root':str(root),'out':str(out),'mode':mode,'deadline':a['expires_utc']})]:n.save(out/name,val)
    if review:n.save(out/'review.json',review)
    hook=out/'hook';hook.mkdir();(hook/'sitecustomize.py').write_text('import sys\nsys.path[:0]='+repr([str(W/'tools'),str(W/'engine')])+'\nimport p3_finish_fixture\np3_finish_fixture.install()\n',encoding='utf-8')
    env=p.git_environment();env.update(PYTHONPATH=str(hook),P3_FINISH_FIXTURE=str(out/'config.json'),P3_PUBLIC_FIXTURE_INPUTS=str(n.inputs()),PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1')
    args=[sys.executable,'-B',str(W/'tools/p3_happy_finish.py'),'--real','--section',section,'--plan',str(root/'plan.json'),'--amendment',str(out/'amendment.json'),'--grant',str(out/'grant.json'),'--approved-amendment-sha256',p.digest(a)]
    if section=='rest':args+=['--receipt',str(out/'receipt.json')]
    if review:args+=['--termination-review',str(out/'review.json')]
    result=subprocess.run(args,env=env,capture_output=True,timeout=900);(out/'output.txt').write_bytes(result.stdout+result.stderr)
    n.save(out/'parent-wait.json',{'exit_code':result.returncode,'actual_B_script':True});return result.returncode,out

def test_full_finish_rest_parentwait_takeover_inspect_normal_and_worst30():
    import test_p3_public_operations as ops
    for mode in ('normal','worst30'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=fixture(root);old=(root/'session'/ (f.h.PHASE+'.jsonl')).read_bytes()
            code,out=direct(root,a,mode=mode);assert code==0,(out/'output.txt').read_text()
            assert direct(root,a,mode=mode)[0]==2
            before=n.read(root/'api-state.json');env=json.loads(p.base64.b64decode(before['records'][before['head']]['body']));assert env['revision']==11 and env['snapshot']['control']['owner'] is None
            claim=json.loads(p.base64.b64decode(before['records'][f.CLAIM]['body']));expected=deepcopy(claim['snapshot']);expected['control']['owner']=None;assert env['snapshot']==expected
            code,out2=direct(root,a,'rest',mode);assert code==0,(out2/'output.txt').read_text()
            receipt=n.read(out2/'receipt.json');assert receipt['observed_wait'] and receipt['exit_code']==23 and receipt['journal_name']==f.LOSS+'.jsonl'
            assert not (root/'session'/(f.TAKE+'.jsonl')).exists()
            review=ops.review_for(root,receipt);code,out3=direct(root,a,'takeover',mode,review);assert code==0,(out3/'output.txt').read_text()
            code,out4=direct(root,a,'inspect',mode);assert code==0,(out4/'output.txt').read_text()
            rows=n.read_rows(root/'session'/ (f.INSPECT+'.jsonl'));end=rows[-1]
            assert end['counts']['PUT']==29 and end['counts']['GIT_PUSH']==1 and end['counts']['GET']<=384
            extra=sum(x['event']=='request' and x.get('confirmation_retry') is True for x in rows);assert extra==(30 if mode=='worst30' else 0)
            assert (root/'session'/(f.h.PHASE+'.jsonl')).read_bytes()==old
            api=n.read(root/'api-state.json');final=json.loads(p.base64.b64decode(api['records'][api['head']]['body']));assert final['snapshot']['commands'][receipt['owner']['run_id']]['_delivery']['messages'][0]['status']=='uncertain'
            n.save(root/'BUDGET-RESULT.json',{'mode':mode,'counts':end['counts'],'additional_confirmation_GET':extra,'phase_counts':{phase:{m:sum(x['event']=='request' and x['phase']==phase and x['method']==m for x in rows) for m in ('GET','PUT','GIT_PUSH')} for phase in f.ORDER},'receipt':receipt,'sending_uncertain':True})

def test_close_old_moving_lost_foreign_permanent_old_deadline_CAS_and_exhaustion():
    for mode in ('old-once','moving','lost-put','foreign','old-forever','deadline-put','CAS409','pool-exhaust'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=fixture(root);code,out=direct(root,a,mode=mode)
            good=mode in ('old-once','moving','lost-put','pool-exhaust');assert code==(0 if good else 2),(out/'output.txt').read_text()
            rows=n.read_rows(root/'session'/(f.CLOSE+'.jsonl'));assert sum(x['event']=='request' and x.get('method')=='PUT' for x in rows[412:])==1
            if mode=='deadline-put':assert rows[-1]['counts']['GET']==158
            if not good:assert not any(x['event']=='phase_end' for x in rows[412:])
            if mode=='pool-exhaust':
                code,out=direct(root,a,'rest',mode);assert code==2 and not (out/'receipt.json').exists()
                rr=n.read_rows(root/'session'/(f.LOST+'.jsonl'));assert sum(x['event']=='request' and x.get('confirmation_retry') is True for x in rr)==30
