"""Expired original plan, exact Reader-only replacement validity, real -B child."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
import test_p3_script_start as s
p,r,t=s.p,s.r,s.t
NOW=datetime(2099,1,1,1,tzinfo=timezone.utc)


def iso(x):return x.isoformat().replace('+00:00','Z')


def fixture(root):
    plan,a=s.historical21(root)
    a['schema']=r.WINDOW_SCHEMA
    w=deepcopy(r.reader_template()['reader_validity'])
    w.update(original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],
             frontier_hash=a['predecessor']['frontier_hash'],independent_review_sha256=a['review']['evidence_sha256'],
             not_before_utc=iso(NOW-timedelta(minutes=1)),expires_utc=iso(NOW+timedelta(minutes=30)))
    a['reader_validity']=w;a['expires_utc']=w['expires_utc']
    return plan,a


def direct(root,a,*,at=NOW,expiry=None,kill=None,grant=None,mode='positive'):
    plan=t.read(Path(root)/'plan.json');g=grant or t.fixture_grant(plan,a)
    if grant is None:g['expires_utc']=a['expires_utc']
    return s.script(root,a,grant=g,mode=mode,kill=kill,fixture_config={
        'start_utc':iso(at),'deadline':a['expires_utc'],'expire_on':expiry})


def rows(root,phase=r.RESUME):
    root=Path(root);return p.Ledger.verify(root/(phase+'.jsonl'),p.digest(t.read(root/'plan.json')))


def no_input(wire):
    assert wire['prompts']==[] and wire['http']==[] and wire['pushes']==0


def test_reader_validity_actual_expired_plan_positive41_and_no_upload_or_replay():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=fixture(root);original=(root/(r.DIAG+'.jsonl')).read_bytes()
        code,wire,g,out=direct(root,a)
        assert code==0 and len(wire['http'])==7 and len(wire['prompts'])==1 and wire['pushes']==0
        end=rows(root);assert len(end)==41 and end[-1]['counts']=={'GET':12,'PUT':0,'GIT_PUSH':0}
        assert end[21]['event']=='phase_start' and end[22]['event']=='reader_validity'
        assert end[22]['validity']==a['reader_validity'] and end[22]['grant_sha256']==p.digest(g)
        assert end[-1]['result']=='confirmed' and end[-1]['upload_eligible'] is False
        assert (root/(r.DIAG+'.jsonl')).read_bytes()==original
        assert (root/(r.RESUME+'.jsonl')).read_bytes().startswith(original)
        no_input(direct(root,a)[1])
        u=s.upload_amendment(root,a,g);no_input(direct(root,u)[1])
        with patch.object(p,'datetime',type('Clock',(datetime,),{'now':classmethod(lambda cls,tz=None:NOW)})):
            t.previous.rejects(ValueError,lambda:p.validate_plan(plan))
            for phase in ('activate','inspect','takeover'):
                normal=t.sim.fixture_grant(plan,phase,expires=a['expires_utc'])
                t.previous.rejects(ValueError,lambda:p.authorize(plan,normal,phase,p.digest(plan)))
        t.save(root/'validity-result.json',{'positive':True,'rows':41,'original_plan_unchanged':t.read(root/'plan.json')==plan,
            'counts':end[-1]['counts'],'new_window_does_not_authorize_upload':True})


def test_reader_validity_bindings_absent_changed_unreviewed_and_over60_deny_before_input():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=fixture(root)
        for mode in ('missing','scope','unapproved','planhash','original-end','frontier','code','root','files','review','over60','grant'):
            x=deepcopy(a);g=None
            if mode=='missing':x=r.template(r.RESUME);x.update({k:v for k,v in a.items() if k in x and k!='schema'})
            elif mode=='scope':x['reader_validity']['phase']=r.UPLOAD
            elif mode=='unapproved':g=t.fixture_grant(plan,x);g['human_authorization']=False
            elif mode=='planhash':x['reader_validity']['original_plan_sha256']='f'*64
            elif mode=='original-end':x['reader_validity']['original_expires_utc']='2099-01-01T00:01:00Z'
            elif mode=='frontier':x['predecessor']['frontier_hash']='f'*64;x['reader_validity']['frontier_hash']='f'*64
            elif mode=='code':x['execution_code']['code_pins']['tools/p3_rules403.py']='f'*64
            elif mode=='root':x['root']['files_sha256']['HEAD']='f'*64
            elif mode=='files':x['predecessor']['files_sha256']['probe-session.sqlite3']='f'*64
            elif mode=='review':x['review']['human_review']=False
            elif mode=='over60':x['reader_validity']['expires_utc']=iso(NOW+timedelta(minutes=60));x['expires_utc']=x['reader_validity']['expires_utc']
            elif mode=='grant':g=t.fixture_grant(plan,x);g['review_sha256']='f'*64
            code,wire,_,out=direct(root,x,grant=g);assert code==2;no_input(wire)
            t.save(out/'countercase.json',{'mode':mode,'outbound':0,'credentials':0})


def test_reader_validity_original_digest_deadline_and_old_frontier_cannot_reset():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=fixture(root)
        for mode in ('deadline','foreign-id','older21'):
            changed=deepcopy(plan)
            if mode=='deadline':changed['expires_utc']='2099-01-01T00:00:01Z'
            elif mode=='foreign-id':changed['repository_id']+=1
            else:
                x=deepcopy(a);x['predecessor']=deepcopy(a['interrupted_diagnosis']['amendment']['predecessor'])
                code,wire,_,_=direct(root,x);assert code==2;no_input(wire);continue
            t.save(root/'plan.json',changed)
            try:code,wire,_,_=direct(root,a);assert code==2;no_input(wire)
            finally:t.save(root/'plan.json',plan)


def test_reader_validity_start_deadline_input_reservation_outbound_late_response_clock_and_confirm():
    cases=[('before-start',0),('exact-end',0),('before-input',0),('reader',0),('before-reservation',0),
           ('before-GET',0),('response',1),('lost-response',1),('rollback',0),('monotonic',0),('before-confirmed',7)]
    for mode,requests in cases:
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=fixture(root)
            at=NOW
            if mode=='before-start':at=datetime.fromisoformat(a['reader_validity']['not_before_utc'].replace('Z','+00:00'))-timedelta(microseconds=1)
            if mode=='exact-end':at=datetime.fromisoformat(a['expires_utc'].replace('Z','+00:00'))
            code,wire,_,out=direct(root,a,at=at,expiry=None if mode in ('before-start','exact-end') else mode)
            assert code==2 and len(wire['http'])==requests and wire['pushes']==0
            if mode in ('before-start','exact-end','before-input'):assert wire['prompts']==[]
            if (root/(r.RESUME+'.jsonl')).exists():
                end=rows(root);assert not any(x['event']=='phase_end' and x.get('result')=='confirmed' for x in end[21:])
                assert end[-1]['counts']=={'GET':5+requests+int(mode=='before-GET'),'PUT':0,'GIT_PUSH':0}
            t.save(out/'countercase.json',{'mode':mode,'requests':requests,'confirmed':False})


def test_reader_validity_new_durable_event_hard_losses_preserve_frontier_and_block_replay():
    for point in ('before_commit','after_commit','after_mirror','after_publish'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=fixture(root)
            code,wire,_,out=direct(root,a,kill=[point,'reader_validity']);assert code==71 and wire is None
            assert not (out/'outbound.jsonl').exists()
            db=sqlite3.connect(root/'probe-session.sqlite3');last=t.previous.read_latest(db);db.close()
            assert last['counts']=={'GET':5,'PUT':0,'GIT_PUSH':0}
            no_input(direct(root,a)[1])


def test_reader_validity_feature_halt_and_expired_grant_before_input():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=fixture(root)
        g=t.fixture_grant(plan,a);g['expires_utc']=iso(NOW)
        no_input(direct(root,a,grant=g)[1])
        code,wire,_,_=direct(root,a,mode='feature');assert code==2 and len(wire['http'])==7 and wire['pushes']==0
        assert rows(root)[-1]['upload_eligible'] is False
