from copy import deepcopy
from pathlib import Path
import sqlite3,tempfile
import test_p3_public_root as n
p,u,r=n.p,n.u,n.r

def test_public_exact53_positive_precreation_skips_protection_postcreation_requires_it():
    for mode in ('positive','unprotected-variant'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=n.fixture(root,continuation=True);old=(root/'session'/(u.PHASE+'.jsonl')).read_bytes()
            code,w,out=n.direct(root,a,mode=mode);assert code==0,(out/'output.txt').read_text()
            assert len(w['http'])==23 and w['pushes']==1 and w['prompts']==['Reader','Writer']
            protection=r.routes(plan)[6];assert not any(x['url'].endswith(protection) for x in w['http'][:6])
            assert sum(x['url'].endswith(protection) for x in w['http'])==1
            rr=n.read_rows(root/'session'/(u.CONTINUE+'.jsonl'));assert rr[-1]['counts']=={'GET':37,'PUT':0,'GIT_PUSH':1}
            assert rr[-1]['bootstrap_case_counts']==rr[-1]['counts'] and rr[-1]['phase_counts']=={'GET':23,'PUT':0,'GIT_PUSH':1}
            assert (root/'session'/(u.PHASE+'.jsonl')).read_bytes()==old and (root/'session'/(u.CONTINUE+'.jsonl')).read_bytes().startswith(old)
            assert n.direct(root,a)[1]['prompts']==[]
            assert n.direct(root,a['stopped_public']['amendment'])[1]['prompts']==[]

def test_public_continue_negative_rules_protection_status_and_lost_push():
    for mode in ('rules-present','403','rules404','pages-unknown','protected','protection-present','protection-unknown','protection403','lost-push'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=n.fixture(root,continuation=True);code,w,out=n.direct(root,a,mode=mode);assert code==2
            after=mode in ('protected','protection-present','protection-unknown','protection403','lost-push')
            assert w['pushes']==int(after) and w['prompts']==(['Reader','Writer'] if after else ['Reader'])
            rr=n.read_rows(root/'session'/(u.CONTINUE+'.jsonl'));assert rr[-1]['event']=='phase_halt'
            assert not any(x['event']=='phase_end' and x.get('result')=='confirmed' for x in rr[53:])
            assert 'HALT: public-' in (out/'output.txt').read_text()
            if mode=='lost-push':assert len(w['http'])==7
            assert n.direct(root,a)[1]['prompts']==[]
            n.save(out/'countercase.json',{'mode':mode,'halt_category':rr[-1]['category'],'confirmed':False})

def test_public_continue_wrong_frontier_sources_grant_and_old_push_or_unknown_stop():
    for mode in ('frontier','source','old-grant','push','unknown','missing-marker'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=n.fixture(root,continuation=True)
            if mode=='frontier':a['predecessor']['frontier_hash']='f'*64
            if mode=='source':a['stopped_public']['code_materialization']={}
            if mode=='old-grant':a['stopped_public']['grant']['review_sha256']='f'*64
            if mode=='missing-marker':(root/'session'/('attempt-'+u.PHASE+'.json')).rename(root/'session/held-marker')
            if mode in ('push','unknown'):
                session=root/'session';rr=n.read_rows(session/(u.PHASE+'.jsonl'))
                if mode=='push':rr[50]['method']='GIT_PUSH'
                else:rr[51]['result']='unknown'
                counts={'GET':0,'PUT':0,'GIT_PUSH':0};prev='0'*64
                for row in rr:
                    row.pop('hash');row['previous_hash']=prev
                    if row['event']=='request':counts[row['method']]+=1
                    row['counts']=deepcopy(counts);row['hash']=p.digest(row);prev=row['hash']
                (session/(u.PHASE+'.jsonl')).write_text(''.join(p.canonical(x)+'\n' for x in rr),encoding='utf-8',newline='\n')
                db=sqlite3.connect(session/'probe-session.sqlite3');db.execute('DELETE FROM events');db.executemany('INSERT INTO events(body) VALUES (?)',[(p.canonical(x),) for x in rr]);db.execute('UPDATE frontier SET published=?',(rr[-1]['hash'],));db.commit();db.close()
                a['predecessor'].update(frontier_hash=rr[-1]['hash'],counts=rr[-1]['counts'],files_sha256={f:u.c.sha(session/f) for f in r.session_files(rr)})
            code,w,out=n.direct(root,a);assert code==2 and not w['prompts'] and not w['http'];n.save(out/'countercase.json',{'mode':mode,'outbound':0})

def test_public_continue_input_deadline_and_context_parser_do_not_relax():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=n.fixture(root,continuation=True);before={x.name:u.c.sha(x) for x in (root/'session').iterdir()}
        assert n.direct(root,a,mode='input-cancel')[0]==3
        assert before=={x.name:u.c.sha(x) for x in (root/'session').iterdir()}
        assert n.direct(root,a,at=a['expires_utc'])[1]['prompts']==[]
    from p3_http_diagnostics import classify
    error=n.s.t.http_error('fixture',404,'Branch not protected');assert classify(error)['category']=='unknown-404'
    error=n.s.t.http_error('fixture',404,'Branch not protected');assert classify(error,protection_context=True)['category']=='branch-not-protected'
