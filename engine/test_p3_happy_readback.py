"""Real Python-B entry, fixture-only input/HTTP, current gates intact."""
import os,sys,json,sqlite3,subprocess,tempfile,types
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import test_p3_public_root as n
import p3_happy_readback as h
p=h.p;W=n.W

class EndModel(Exception):pass
def body_model(plan,rows):
    """Offline historical engine replay with logged IDs/parents, no Ledger/API."""
    puts=[(i,x) for i,x in enumerate(rows) if x['event']=='request' and x.get('method')=='PUT']
    records={};start=p.synthetic_seed(plan)
    def record(commit,body):return {'commit_sha':commit,'blob_sha':p.hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest(),'body':body}
    records[h.o.u.SEED]=record(h.o.u.SEED,start)
    ledger=types.SimpleNamespace(counts={'PUT':0},run=None,emit=lambda *a,**k:None)
    class Model:
        stale=None;head=h.o.u.SEED
        boundary=types.SimpleNamespace(p=plan,ledger=ledger)
        def read(self,*a):
            if self.stale is not None:v,self.stale=self.stale,None;return v
            return deepcopy(records[self.head])
        def read_at(self,repo,sha,*a):return deepcopy(records[sha])
        def parents(self,repo,sha):return self.parents_map[sha]
        def is_ancestor(self,*a):return True
        parents_map={}
        def update(self,repo,branch,blob,body,write,*a):
            index=ledger.counts['PUT'];ledger.counts['PUT']+=1;i,q=puts[index]
            env=json.loads(body)
            assert blob==q['old_blob'] and write==q['write_id'] and len(body)==q['bytes']
            assert env['parent_digest']==q['parent_digest'] and env['revision']==q['revision']
            if index==10:
                assert env['revision']==10;records['f'*40]=record('f'*40,body);self.parents_map['f'*40]=[h.OLD];raise EndModel()
            if rows[i+1]['result']=='http-409':raise p.gh.StoreConflict('fixture stale')
            parent=next(x for x in rows[i+2:puts[index+1][0]] if x['event']=='parent')
            commit=parent['commit'];records[commit]=record(commit,body)
            assert records[commit]['blob_sha']==next(x for x in rows[i+2:] if x['event']=='readback')['old_blob']
            self.parents_map[commit]=parent['parents'];self.head=commit;return commit
    client=Model()
    with patch.object(p.gh.secrets,'token_hex',side_effect=lambda *_:puts[ledger.counts['PUT']][1]['write_id']):
        p.activation(client)
        try:p.sequence(client,'happy')
        except EndModel:pass
        else:raise AssertionError('Exactly unconfirmed claim expected')
    assert ledger.counts['PUT']==11 and len(records[h.OLD]['body'])==5626 and len(records['f'*40]['body'])==5758
    return records,client.parents_map

def fixture(td):
    root=Path(td);plan,_=n.fixture(root,root_success=True);base=n.inputs()
    real=n.read_rows(base/'p3-store-happy-halt-20261013/session-snapshot/public-store-happy.jsonl')
    rows=n.read_rows(root/'session'/ (h.o.u.CONTINUE+'.jsonl'))
    old=n.read(base/'p3-public-storebetrieb-start-20261013/OPERATIONS.json');g=n.read(base/'p3-public-storebetrieb-start-20261013/INITIAL-GRANT.json')
    old.update(original_plan_sha256=p.digest(plan))
    old['root_success'].update(amendment=n.read(root/'successful-root-amendment.json'),grant=n.read(root/'successful-root-grant.json'))
    old['root_success']['code_materialization']=h.r.materialization(old['root_success']['amendment']['execution_code'])
    old['entry'].update(frontier_hash=rows[-1]['hash'],highwater=rows[-1]['utc'],files_sha256={name:h.c.sha(root/'session'/name) for name in h.r.session_files(rows)})
    g.update(plan_sha256=p.digest(plan),amendment_sha256=p.digest(old),review_sha256=p.digest(old),
        entry_frontier_hash=rows[-1]['hash'],entry_files_sha256=old['entry']['files_sha256'])
    old['review']['original_pid']=rows[53]['pid']
    # The old operations digest includes its actual fixture PID.
    g.update(amendment_sha256=p.digest(old),review_sha256=p.digest(old))
    for x in real[112:]:
        x=deepcopy(x);x.update(plan_sha256=p.digest(plan),previous_hash=rows[-1]['hash'])
        if x['event']=='phase_start':x['pid']=rows[53]['pid'];x['predecessor']=rows[-1]['hash']
        if x['event']=='authorization':x.update(grant_sha256=p.digest(g),review_sha256=p.digest(old))
        if x['event']=='operations_review':x.update(amendment_sha256=p.digest(old),grant_sha256=p.digest(g),section_grant=g)
        x.pop('hash');x['hash']=p.digest(x);rows.append(x)
    for j,stop in ((112,180),(180,375)):
        (root/'session'/rows[j]['journal']).write_text(''.join(p.canonical(x)+'\n' for x in rows[:stop]),encoding='utf-8',newline='\n')
        n.save(root/'session'/('attempt-'+rows[j]['phase']+'.json'),{k:rows[j][k] for k in ('plan_sha256','phase','journal','pid','predecessor')})
    db=sqlite3.connect(root/'session/probe-session.sqlite3');db.execute('PRAGMA synchronous=FULL');db.execute('DELETE FROM events')
    db.executemany('INSERT INTO events(body) VALUES (?)',[(p.canonical(x),) for x in rows]);db.execute('UPDATE frontier SET journal=?,published=?,highwater=?',('public-store-happy.jsonl',rows[-1]['hash'],rows[-1]['utc']));db.commit();db.close()
    a=h.template();a.update(original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],operations=old,initial_grant=g,
        historical_code_materialization=h.r.materialization(old['execution_code']),execution_code=n.s.code_for(plan),not_before_utc=n.NOW,expires_utc='2026-10-14T20:00:00Z')
    a['entry'].update(frontier_hash=rows[-1]['hash'],highwater=rows[-1]['utc'],files_sha256={name:h.c.sha(root/'session'/name) for name in h.r.session_files(rows)})
    a['review'].update(original_pid=rows[180]['pid'],observed_utc=n.NOW,reviewer='fixture-only',evidence_sha256='e'*64,
        terminal_code_path_checked=True,human_terminal_end_report=True,all_workers_ended=True,triggers_paused=True,human_review=True)
    records,parents=body_model(plan,real)
    n.save(root/'body-model.json',{'records':{k:{**v,'body':p.base64.b64encode(v['body']).decode()} for k,v in records.items()},'parents':parents,
        'only_offline_historical_fixture_replay':True,'old_blobs_lengths_parent_digests_write_ids_match':True})
    n.save(root/'375-fixture-translation.json',{'historical_paths_plan_hashes_authorization_digests_and_ended_PID_translated':True,'current_runtime_gates_unpatched':True,'source_rows':375})
    return plan,a

def direct(root,a,mode='own',grant=None):
    root=Path(root);folder=root/'attempts';folder.mkdir(exist_ok=True);out=folder/('%03d'%len(list(folder.iterdir())));out.mkdir()
    plan=n.read(root/'plan.json');g=grant or h.grant_template()
    if grant is None:g.update(plan_sha256=p.digest(plan),review_sha256=p.digest(a),human_authorization=True,approved_by='fixture-only',approval_evidence_sha256='e'*64,expires_utc=a['expires_utc'])
    for name,value in (('amendment.json',a),('grant.json',g),('config.json',{'root':str(root),'output':str(out),'mode':mode,'deadline':a['expires_utc']})):n.save(out/name,value)
    hook=out/'hook';hook.mkdir();(hook/'sitecustomize.py').write_text('import sys\nsys.path[:0]='+repr([str(W/'tools'),str(W/'engine')])+'\nimport p3_happy_fixture\np3_happy_fixture.install()\n',encoding='utf-8')
    env=p.git_environment();env.update(PYTHONPATH=str(hook),P3_HAPPY_FIXTURE=str(out/'config.json'),P3_PUBLIC_FIXTURE_INPUTS=str(n.inputs()),PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1')
    proc=subprocess.run([sys.executable,'-B',str(W/'tools/p3_happy_readback.py'),'--real','--plan',str(root/'plan.json'),'--amendment',str(out/'amendment.json'),'--grant',str(out/'grant.json'),'--approved-amendment-sha256',p.digest(a)],env=env,capture_output=True,timeout=180)
    (out/'output.txt').write_bytes(proc.stdout+proc.stderr);n.save(out/'parent-wait.json',{'returncode':proc.returncode,'actual_B_script':True})
    wire=n.read(out/'wire.json');return proc.returncode,wire,out

def test_happy_readback_own_and_old_exact13_get_real_script_no_recovery_replay():
    for mode in ('own','old'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=fixture(root);before=(root/'session/public-store-happy.jsonl').read_bytes()
            code,wire,out=direct(root,a,mode);assert code==0,(out/'output.txt').read_text()
            assert len(wire['http'])==13 and wire['prompts']==['Reader'] and all(x['method']=='GET' for x in wire['http'])
            rows=n.read_rows(root/'session'/(h.PHASE+'.jsonl'));end=rows[-1]
            assert end['counts']=={'GET':147,'PUT':11,'GIT_PUSH':1} and end['result']=='read-only-complete-recovery-forbidden' and end['recovery_authorized'] is False
            assert (root/'session/public-store-happy.jsonl').read_bytes()==before
            assert direct(root,a,mode)[1]['http']==[]
            n.save(out/'checked.json',{'mode':mode,'counts':end['counts'],'outcome':end['outcome'],'old_prefix_unchanged':True})

def test_happy_readback_unstable_foreign_parent_tree_denied_deadline():
    for mode in ('moving','foreign','bad-parent','bad-tree','403','429','lost-get','unknown404','private','late-response','input-expiry','input-cancel'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,a=fixture(root);code,w,out=direct(root,a,mode)
            assert code==(3 if mode=='input-cancel' else 2),(out/'output.txt').read_text()
            assert w['prompts']==['Reader'] and len(w['http'])<=13 and all(x['method']=='GET' for x in w['http'])
            assert not any(x['event']=='phase_end' for x in n.read_rows(root/'session'/(h.PHASE+'.jsonl'))[375:]) if (root/'session'/(h.PHASE+'.jsonl')).exists() else not w['http']
            if mode=='moving':assert len(w['http'])==10 and 'unstable-head' in (out/'output.txt').read_text()
            assert not any(x.name.startswith('attempt-public-store-lost') for x in (root/'session').iterdir())

def test_happy_readback_frontier_old_grant_code_live_process_and_history_gap_before_input():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);plan,a=fixture(root)
        for mode in ('frontier','file','grant','historical-grant','code','live','old-window'):
            changed=deepcopy(a);g=None
            if mode=='frontier':changed['entry']['frontier_hash']='f'*64
            if mode=='file':changed['entry']['files_sha256']['probe-session.sqlite3']='f'*64
            if mode=='grant':g=h.grant_template()
            if mode=='historical-grant':changed['initial_grant']['human_authorization']=False
            if mode=='code':changed['execution_code']['code_pins']['tools/p3_happy_readback.py']='f'*64
            if mode=='live':changed['review']['original_pid']=os.getpid()
            if mode=='old-window':changed['expires_utc']=changed['not_before_utc']
            code,w,out=direct(root,changed,grant=g);assert code==2 and not w['http'] and not w['prompts'],(out/'output.txt').read_text()
        rows=n.read_rows(root/'session/public-store-happy.jsonl');broken=deepcopy(rows)
        next(x for x in broken if x['event']=='parent' and x['commit']==h.OLD)['parents']=['e'*40]
        n.s.t.previous.rejects(ValueError,lambda:h.history(plan,broken,a))
