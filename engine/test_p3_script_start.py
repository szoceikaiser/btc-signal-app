"""Actual separate Python -B entrypoint tests. Current security checks stay live."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from unittest.mock import patch

W=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(W/'tools'),str(W/'engine')]
import p3_github_probe as p
import p3_rules403 as r
import test_p3_rules403 as t
from test_p3_github_probe import rejects


def execution(head=None):
    head=head or t.c.git(W,'rev-parse','HEAD').decode().strip()
    names=set(t.c.git(W,'diff','--name-only',t.c.ORIGINAL_HEAD,head).decode().splitlines())
    # Baseline execution's complete pinned file list is itself preserved in Git:
    # the fixture plan supplies original pins below, avoiding a local audit dependency.
    return {'code_head':head,'code_tree':t.c.git(W,'rev-parse',head+'^{tree}').decode().strip(),'code_pins':{name:t.c.sha(W/name) for name in names}}


def code_for(plan,head=None):
    value=execution(head);names=set(value['code_pins'])|set(plan['code_pins'])|t.c.EXTRA_PINS
    value['code_pins']={name:(hashlib.sha256(t.c.git(W,'show',head+':'+name)).hexdigest() if head else t.c.sha(W/name)) for name in names}
    return value


def historical21(td):
    root=Path(td);plan,a=t.historical_fixture(root)
    a['execution_code']=code_for(plan,r.SCRIPT_HEAD)
    t.save(root/'old-diagnosis-amendment.json',a)
    proc=subprocess.run([sys.executable,'-B',str(Path(__file__)),'--historical21',str(root)],capture_output=True,timeout=120)
    assert proc.returncode==0,proc.stderr.decode()
    rows=p.Ledger.verify(root/(r.DIAG+'.jsonl'),p.digest(plan));assert len(rows)==21
    t.save(root/'historical21-parent-wait.json',{'pid':rows[17]['pid'],'exit_code':proc.returncode,
        'historical_only_code_gate_bridge':True,'historical_only_phase_tuple_bridge':True})
    return plan,resume_amendment(root)


def resume_amendment(root):
    root=Path(root);plan=t.read(root/'plan.json');old=t.read(root/'old-diagnosis-amendment.json');a=r.template(r.RESUME)
    for key in ('original_plan_sha256','reader401_amendment','reader401_grant','reader401_code_materialization','root','routes','expires_utc'):
        a[key]=deepcopy(old[key])
    a['execution_code']=code_for(plan)
    a['interrupted_diagnosis']={'amendment':old,'grant':t.read(root/'old-diagnosis-grant.json'),
        'code_materialization':r.materialization(old['execution_code'])}
    bind_predecessor(root,a,r.DIAG)
    return a


def bind_predecessor(root,a,phase):
    rows=p.Ledger.verify(root/(phase+'.jsonl'),a['original_plan_sha256'])
    a['predecessor'].update(journal=phase+'.jsonl',frontier_hash=rows[-1]['hash'],frontier_rows=len(rows),
        highwater=rows[-1]['utc'],counts=rows[-1]['counts'],files_sha256={n:t.c.sha(root/n) for n in r.session_files(rows)})
    last=[x for x in rows if x['event']=='phase_start'][-1]
    a['review'].update(reviewer='offline-fixture-not-authorization',evidence_sha256='e'*64,original_pid=last['pid'],
        observed_utc=p.utc(),terminal_code_path_checked=True,human_terminal_end_report=True,
        all_workers_ended=True,triggers_paused=True,human_review=True)


def upload_amendment(root,a,g):
    u=r.template(r.UPLOAD)
    for key in ('original_plan_sha256','reader401_amendment','reader401_grant','reader401_code_materialization','execution_code','root','routes','expires_utc'):
        u[key]=deepcopy(a[key])
    u['diagnosis']={'amendment':a,'grant':g};bind_predecessor(root,u,r.RESUME)
    return u


def script(root,a,*,grant=None,mode='positive',kill=None,expiry=None,allow_push=False):
    root=Path(root);plan=t.read(root/'plan.json');attempts=root/'direct-attempts';attempts.mkdir(exist_ok=True)
    out=attempts/('%03d'%len(list(attempts.iterdir())));out.mkdir()
    g=grant or t.fixture_grant(plan,a)
    cfg={'root':str(root),'output':str(out),'mode':mode,'kill':kill,'allow_fixture_push':allow_push}
    if expiry:
        start=datetime.now(timezone.utc)+timedelta(seconds=1);deadline=start+timedelta(seconds=60)
        cfg.update(start_utc=start.isoformat(),deadline=deadline.isoformat(),expire_on=expiry)
        g['expires_utc']=deadline.isoformat().replace('+00:00','Z')
    for name,value in [('amendment.json',a),('grant.json',g),('config.json',cfg)]:t.save(out/name,value)
    hook=out/'startup';hook.mkdir()
    (hook/'sitecustomize.py').write_text('import sys\nsys.path[:0]='+repr([str(W/'tools'),str(W/'engine')])+'\nimport p3_script_fixture\np3_script_fixture.install()\n',encoding='utf-8')
    env=p.git_environment();env.update(PYTHONPATH=str(hook),P3_SCRIPT_FIXTURE=str(out/'config.json'),PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1')
    argv=[sys.executable,'-B',str(W/'tools/p3_rules403.py'),'--real','--phase',a['phase'],'--plan',str(root/'plan.json'),
          '--amendment',str(out/'amendment.json'),'--grant',str(out/'grant.json'),'--approved-amendment-sha256',p.digest(a)]
    proc=subprocess.run(argv,env=env,capture_output=True,timeout=120)
    (out/'output.txt').write_bytes(proc.stdout+proc.stderr)
    t.save(out/'parent-wait.json',{'returncode':proc.returncode,'actual_B_script':True})
    wire=t.read(out/'wire.json') if (out/'wire.json').exists() else None
    assert proc.returncode in (0,2,71),proc.stderr.decode()
    if wire:assert not wire['known_denial'],wire
    return proc.returncode,wire,g,out


def test_script_positive_resume_then_separate_upload_keeps_all21_and_rejects_replay():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=historical21(root);old=(root/(r.DIAG+'.jsonl')).read_bytes()
        code,wire,g,_=script(root,a);assert code==0 and len(wire['prompts'])==1 and len(wire['http'])==7 and wire['pushes']==0
        rows=p.Ledger.verify(root/(r.RESUME+'.jsonl'),p.digest(plan));assert len(rows)==40 and rows[-1]['counts']=={'GET':12,'PUT':0,'GIT_PUSH':0}
        assert (root/(r.DIAG+'.jsonl')).read_bytes()==old and (root/(r.RESUME+'.jsonl')).read_bytes().startswith(old)
        assert script(root,a)[1]['prompts']==[]
        upload=upload_amendment(root,a,g)
        assert script(root,upload,grant=g)[1]['prompts']==[]
        code,wire,_,_=script(root,upload,allow_push=True);assert code==0 and wire['pushes']==1 and len(wire['http'])==23
        assert p.Ledger.verify(root/(r.UPLOAD+'.jsonl'),p.digest(plan))[-1]['counts']=={'GET':35,'PUT':0,'GIT_PUSH':1}
        assert script(root,upload,allow_push=True)[1]['prompts']==[]
        rejects(ValueError,lambda:p.Ledger(plan,root/'activate.jsonl','activate',root/(r.UPLOAD+'.jsonl')))


def test_script_initial_and_resumed_diagnosis_positive_feature_rights_rate():
    for phase in (r.DIAG,r.RESUME):
        for mode in ('positive','feature','rights','rate'):
            with tempfile.TemporaryDirectory() as td:
                root=Path(td)
                if phase==r.RESUME:plan,a=historical21(root)
                else:plan,a=t.historical_fixture(root);a['execution_code']=code_for(plan)
                code,wire,g,_=script(root,a,mode=mode)
                assert code==(0 if mode=='positive' else 2)
                assert len(wire['prompts'])==1 and wire['pushes']==0 and len(wire['http'])==(7 if mode in ('positive','feature') else 4)
                rows=p.Ledger.verify(root/(phase+'.jsonl'),p.digest(plan))
                assert rows[-1]['counts']=={'GET':12 if mode in ('positive','feature') else 9,'PUT':0,'GIT_PUSH':0}
                if phase==r.RESUME and mode=='feature':
                    assert rows[-1]['upload_eligible'] is False
                    assert script(root,upload_amendment(root,a,g),allow_push=True)[1]['prompts']==[]


def test_script_wrong_code_plan_grant_seed_marker_and_stale_frontier_stop_before_input():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=historical21(root)
        for mode in ('code','plan','grant','old-code','frontier','old-grant'):
            changed=deepcopy(a);g=None
            if mode=='code':changed['execution_code']['code_pins']['tools/p3_rules403.py']='0'*64
            if mode=='plan':changed['original_plan_sha256']='0'*64
            if mode=='grant':g=t.fixture_grant(plan,changed);g['human_authorization']=False
            if mode=='old-code':changed['interrupted_diagnosis']['code_materialization']={}
            if mode=='frontier':changed['predecessor']=deepcopy(a['interrupted_diagnosis']['amendment']['predecessor'])
            if mode=='old-grant':changed['interrupted_diagnosis']['grant']['expires_utc']='2020-01-01T00:00:00Z'
            code,wire,_,_=script(root,changed,grant=g);assert code==2 and not wire['prompts'] and not wire['http']
        for path in (root/('attempt-'+r.DIAG+'.json'),root/'probe-session.sqlite3',root/'execution/refs/heads'/plan['branch']):
            held=path.with_name(path.name+'.held');path.rename(held)
            try:
                code,wire,_,_=script(root,a);assert code==2 and not wire['prompts'] and not wire['http']
            finally:held.rename(path)
        helper=root/'execution/synthetic-askpass.py';helper.write_text('fixture prior preparation')
        assert script(root,a)[1]['prompts']==[]


def rehash_fixture(root,rows):
    counts={'GET':0,'PUT':0,'GIT_PUSH':0};prev='0'*64
    for row in rows:
        row.pop('hash',None);row['previous_hash']=prev
        if row['event']=='request':counts[row['method']]+=1
        row['counts']=dict(counts);row['hash']=p.digest(row);prev=row['hash']
    db=sqlite3.connect(root/'probe-session.sqlite3');db.execute('DELETE FROM events')
    for row in rows:db.execute('INSERT INTO events(body) VALUES (?)',(p.canonical(row),))
    db.execute('UPDATE frontier SET published=?,highwater=?',(rows[-1]['hash'],rows[-1]['utc']));db.commit();db.close()
    (root/(r.DIAG+'.jsonl')).write_text(''.join(p.canonical(row)+'\n' for row in rows),encoding='utf-8',newline='\n')
    t.save(root/('attempt-'+r.DIAG+'.json'),{k:rows[17][k] for k in ('plan_sha256','phase','journal','pid','predecessor')})


def test_script_any_prior_reservation_unknown_live_pid_or_unpublished_frontier_denied():
    for mode in ('GET','PUT','GIT_PUSH','unknown','live-pid','unpublished'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=historical21(root);rows=p.Ledger.verify(root/(r.DIAG+'.jsonl'),p.digest(plan))
            if mode in ('GET','PUT','GIT_PUSH'):
                row=deepcopy(rows[19]);row.update(event='request',method=mode,bytes=0,budget_phase='bootstrap');rows.insert(20,row)
            elif mode=='unknown':rows[20].update(event='response',result='unknown')
            elif mode=='live-pid':rows[17]['pid']=os.getpid()
            if mode!='unpublished':rehash_fixture(root,rows);a=resume_amendment(root)
            else:
                db=sqlite3.connect(root/'probe-session.sqlite3');db.execute('UPDATE frontier SET published=?',('0'*64,));db.commit();db.close()
                a['predecessor']['files_sha256']['probe-session.sqlite3']=t.c.sha(root/'probe-session.sqlite3')
            t.save(root/'semantic-countercase.json',{'mode':mode})
            code,wire,_,_=script(root,a);assert code==2 and not wire['prompts'] and not wire['http']


def test_script_exclusivity_and_shared_diagnosis_budget():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=historical21(root)
        ledger=p.Ledger(plan,root/(r.RESUME+'.jsonl'),r.RESUME,root/(r.DIAG+'.jsonl'),rules403_amendment=a)
        try:
            assert script(root,a)[1]['prompts']==[]
            for phase in ('inspect','takeover'):
                rejects((ValueError,OSError),lambda:p.Ledger(plan,root/'other.jsonl',phase,ledger.path))
            for method in ('PUT','GIT_PUSH'):rejects(ValueError,lambda:ledger.charge(method))
            for _ in range(8):ledger.charge('GET')
            rejects(ValueError,lambda:ledger.charge('GET'))
            assert ledger.counts=={'GET':13,'PUT':0,'GIT_PUSH':0} and ledger.cases['bootstrap']['GET']==13
        finally:ledger.close()


def test_script_exact_deadline_before_requests_and_late_response():
    for where in ('reader','before-GET','response','before-GIT_PUSH','push-response'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=historical21(root)
            upload=where in ('before-GIT_PUSH','push-response')
            if upload:
                code,_,g,_=script(root,a);assert code==0;a=upload_amendment(root,a,g)
            code,wire,_,_=script(root,a,expiry=where,allow_push=upload)
            assert code==2 and len(wire['http'])=={'reader':0,'before-GET':0,'response':1,'before-GIT_PUSH':7,'push-response':7}[where]
            assert wire['pushes']==int(where=='push-response')
            rows=p.Ledger.verify(root/(a['phase']+'.jsonl'),p.digest(plan));assert rows[-1]['event']=='phase_halt'
            assert rows[-1]['counts']=={'GET':{'reader':5,'before-GET':6,'response':6,'before-GIT_PUSH':19,'push-response':19}[where],
                'PUT':0,'GIT_PUSH':int(upload)}
            assert script(root,a,allow_push=upload)[1]['prompts']==[]


def test_script_hard_process_loss_cannot_replay_or_start_before_publication():
    points=[('after_intent','phase_start')]+[(point,event) for event in ('phase_start','rules403_amendment','request')
            for point in ('before_commit','after_commit','after_mirror','after_publish')]+[('before_outbound','GET')]
    for point,event in points:
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=historical21(root);code,wire,_,out=script(root,a,kill=[point,event])
            assert code==71 and wire is None and not (out/'outbound.jsonl').exists()
            db=sqlite3.connect(root/'probe-session.sqlite3');last=t.previous.read_latest(db);db.close()
            assert last['counts']=={'GET':5+int(event in ('request','GET') and point!='before_commit'),'PUT':0,'GIT_PUSH':0}
            code,wire,_,_=script(root,a);assert code==2 and not wire['prompts'] and not wire['http']


def historical_worker(root):
    # Historical fixture only: execute the canonical old4c script bytes, bridging
    # its old code gate and old two-phase tuple. Current direct children do NOT.
    root=Path(root);a=t.read(root/'old-diagnosis-amendment.json')
    raw=t.c.git(W,'show',r.SCRIPT_HEAD+':tools/p3_rules403.py')
    def old_entry():exec(compile(raw,'historical4c157a7/p3_rules403.py','exec'),{'__name__':'__main__'})
    with patch.object(r,'main',old_entry),patch.object(p,'verify_code_pin',lambda _:None),patch.object(p,'RULES_PHASES',(r.DIAG,r.UPLOAD)):
        try:t.cli(root,a,patch_code=False)
        except SystemExit as exc:assert exc.code==2
        else:raise AssertionError('Historical script failure absent')
    t.save(root/'old-diagnosis-grant.json',t.read(root/(r.DIAG+'-grant.json')))
    assert t.read(root/'fixture-latest.json')['http']==[]


if __name__=='__main__':
    assert sys.argv[1]=='--historical21';historical_worker(sys.argv[2])
