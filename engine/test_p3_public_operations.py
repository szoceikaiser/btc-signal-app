import sys,os,json,subprocess,tempfile
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import test_p3_public_root as n
W=n.W;p=n.p
import p3_public_operations as o

def fixture(root):
    root=Path(root);plan,_=n.fixture(root,root_success=True);a=o.template()
    prior=n.read(root/'successful-root-amendment.json');grant=n.read(root/'successful-root-grant.json')
    rows=n.read_rows(root/'session'/(o.u.CONTINUE+'.jsonl'))
    a.update(original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],execution_code=n.s.code_for(plan),
        not_before_utc=n.NOW,expires_utc='2026-10-14T20:00:00Z')
    a['root_success'].update(amendment=prior,grant=grant,code_materialization=o.r.materialization(prior['execution_code']))
    a['entry'].update(frontier_hash=rows[-1]['hash'],highwater=rows[-1]['utc'],files_sha256={f:o.u.c.sha(root/'session'/f) for f in o.r.session_files(rows)})
    a['review'].update(reviewer='offline fixture',evidence_sha256='e'*64,original_pid=rows[53]['pid'],observed_utc=n.NOW,
        terminal_code_path_checked=True,human_terminal_end_report=True,all_workers_ended=True,triggers_paused=True,human_review=True)
    return plan,a

def direct(root,a,section='initial',*,review=None,mode='positive',grant=None):
    root=Path(root);plan=n.read(root/'plan.json');attempt=root/'ops-attempts';attempt.mkdir(exist_ok=True);out=attempt/('%03d'%len(list(attempt.iterdir())));out.mkdir()
    g=grant or o.grant_template(section)
    db=o.sqlite3.connect(root/'session/probe-session.sqlite3');state=db.execute('SELECT journal,published FROM frontier').fetchone();db.close();rr=n.read_rows(root/'session'/state[0])
    if grant is None:g.update(plan_sha256=p.digest(plan),amendment_sha256=p.digest(a),human_authorization=True,approved_by='offline-fixture',approval_evidence_sha256='e'*64,
        expires_utc=a['expires_utc'],review_sha256=p.digest(review) if section=='takeover' else p.digest(a),entry_journal=state[0],entry_frontier_hash=state[1],entry_rows=len(rr),entry_files_sha256={x:o.u.c.sha(root/'session'/x) for x in o.r.session_files(rr)})
    cfg={'root':str(root),'output':str(out),'mode':mode,'deadline':a['expires_utc']}
    for name,value in [('amendment.json',a),('grant.json',g),('config.json',cfg)]:n.save(out/name,value)
    if review:n.save(out/'review.json',review)
    hook=out/'startup';hook.mkdir();(hook/'sitecustomize.py').write_text('import sys\nsys.path[:0]='+repr([str(W/'tools'),str(W/'engine')])+'\nimport p3_operations_fixture\np3_operations_fixture.install()\n',encoding='utf-8')
    env=p.git_environment();env.update(PYTHONPATH=str(hook),P3_OPERATIONS_FIXTURE=str(out/'config.json'),P3_PUBLIC_FIXTURE_INPUTS=os.environ.get('P3_PUBLIC_FIXTURE_INPUTS',str(W.parent/'audit-backups')),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
    argv=[sys.executable,'-B',str(W/'tools/p3_public_operations.py'),'--real','--section',section,'--plan',str(root/'plan.json'),'--amendment',str(out/'amendment.json'),'--grant',str(out/'grant.json'),'--approved-amendment-sha256',p.digest(a)]
    if section=='initial':argv+=['--receipt',str(out/'receipt.json')]
    if review:argv+=['--termination-review',str(out/'review.json')]
    proc=subprocess.run(argv,env=env,capture_output=True,timeout=600);(out/'output.txt').write_bytes(proc.stdout+proc.stderr)
    n.save(out/'parent-wait.json',{'exit_code':proc.returncode,'argv':argv});assert proc.returncode in (0,2,3),proc.stderr.decode()
    return proc.returncode,out,g

def review_for(root,receipt):
    return {'expected_owner':receipt['owner'],'expected_revision':receipt['revision'],'expected_commit':receipt['commit'],
        'termination':receipt,'evidence':{'reviewer':'offline fixture','evidence_sha256':'e'*64,'old_owner':receipt['owner'],'run_completed':True,'workers_terminated':True,'triggers_paused':True}}

def test_public_operations_full_actual_section_loss_parent_stop_takeover_uncertain_inspect():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=fixture(root);original=(root/'session'/(o.u.CONTINUE+'.jsonl')).read_bytes()
        code,out,g=direct(root,a);assert code==0,(out/'output.txt').read_text()
        receipt=n.read(out/'receipt.json');assert receipt['exit_code']==23 and receipt['observed_wait'] is True
        rr=n.read_rows(root/'session'/(o.INITIAL[-1]+'.jsonl'));assert rr[-1]['event']=='loss_boundary' and rr[-1]['counts']['PUT']==28
        assert (root/'session'/(o.u.CONTINUE+'.jsonl')).read_bytes()==original
        assert not (root/'session/public-store-takeover.jsonl').exists()
        wire=[n.read(f) for f in out.glob('wire-*.json')];assert sum(len(x['prompts']) for x in wire)==2
        assert direct(root,a)[0]==2
        assert direct(root,a,'takeover')[0]==2
        review=review_for(root,receipt);code,out2,_=direct(root,a,'takeover',review=review);assert code==0,(out2/'output.txt').read_text()
        assert direct(root,a,'takeover',review=review)[0]==2
        code,out3,_=direct(root,a,'inspect');assert code==0,(out3/'output.txt').read_text()
        end=n.read_rows(root/'session/public-store-inspect.jsonl')[-1]
        assert end['counts']['PUT']==29 and end['counts']['GIT_PUSH']==1 and end['counts']['GET']<=384
        api=n.read(root/'api-state.json');body=o.p.base64.b64decode(api['records'][api['head']]['body']);env=json.loads(body)
        messages=env['snapshot']['commands'][receipt['owner']['run_id']]['_delivery']['messages'];assert messages[0]['status']=='uncertain'
        assert env['snapshot']['control']['owner'] is None and env['snapshot']['control']['mode']=='active'
        record={'body':body,'blob_sha':api['records'][api['head']]['blob'],'commit_sha':api['head']}
        class FrozenRead:
            def read(self,*a,**k):return record
            def update(self,*a,**k):raise AssertionError('Uncertain claim must not write')
        store=p.gh.GitHubStore(FrozenRead(),plan['repo'],plan['branch'],p.STORE,plan['runs'][6]['run_id'],plan['runs'][6]['run_attempt'])
        store.owner=p.owner(plan,6);n.s.t.previous.rejects(p.gh.StoreConflict,store.__enter__)
        n.save(root/'FINAL-BUDGET.json',{'counts':end['counts'],'phase_counts':{phase:{m:sum(x['event']=='request' and x.get('method')==m and x['phase']==phase for x in n.read_rows(root/'session/public-store-inspect.jsonl')) for m in ('GET','PUT','GIT_PUSH')} for phase in o.ORDER},'receipt':receipt,'sending_uncertain':True})

def test_public_operations_wrong_takeover_owner_revision_and_missing_wait_evidence():
    root=Path(os.environ['P3_OPS_COMPLETED_FIXTURE'])
    receipt=n.read(next(root.glob('ops-attempts/*/receipt.json')));plan=n.read(root/'plan.json')
    review=review_for(root,receipt)
    for mode in ('owner','revision','commit','not-waited','wrong-exit'):
        changed=deepcopy(review)
        if mode=='owner':changed['expected_owner']['nonce']='f'*32
        if mode=='revision':changed['expected_revision']+=1
        if mode=='commit':changed['expected_commit']='f'*40
        if mode=='not-waited':changed['termination']['observed_wait']=False
        if mode=='wrong-exit':changed['termination']['exit_code']=0
        if mode=='wrong-exit':n.s.t.previous.rejects(ValueError,lambda:p.require(changed['termination']['exit_code']==23,'Actual loss exit23 required'))
        else:n.s.t.previous.rejects(ValueError,lambda:p.validate_termination(plan,changed,root/'session/public-store-process-loss.jsonl'))

def test_public_operations_input_deadline_public_settings_and_false_history_stop():
    for mode in ('input-cancel','input-expiry','private','rules-present','late-put','false-history'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=fixture(root)
            if mode=='false-history':a['entry']['frontier_hash']='f'*64
            code,out,_=direct(root,a,mode=mode);assert code==(3 if mode=='input-cancel' else 2),(out/'output.txt').read_text()
            assert not (out/'receipt.json').exists()
            if mode in ('input-cancel','input-expiry','false-history'):assert not (root/'session'/(o.INITIAL[0]+'.jsonl')).exists()
