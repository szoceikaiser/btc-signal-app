"""Generate closed-history test inputs from source contracts only.

No audit-backups reads, real journals, grants, keys or old session databases.
Named old phases model the same counterexamples; all authority is synthetic.
"""
from offline_git_objects import install as install_object_reader
install_object_reader()
from copy import deepcopy
import hashlib,json,tempfile
from pathlib import Path
import p3_github_probe as p
import p3_probe_simulation as sim
import p3_reader401_continue as c
import p3_rules403 as r
import p3_public_root as u
W=Path(__file__).resolve().parents[1]
_CACHE=None

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(p.canonical(value),encoding='utf-8')

def code(plan,head):
    names=set(plan['code_pins'])|c.EXTRA_PINS|set(c.git(W,'diff','--name-only',c.ORIGINAL_HEAD,head).decode().splitlines())
    return dict(code_head=head,code_tree=c.git(W,'rev-parse',head+'^{tree}').decode().strip(),code_pins={n:hashlib.sha256(c.git(W,'show',head+':'+n)).hexdigest() for n in sorted(names)})

class Rows:
    def __init__(self,plan):self.p=plan;self.rows=[];self.counts=dict(GET=0,PUT=0,GIT_PUSH=0);self.phase='bootstrap';self.at='2026-10-11T00:00:00Z';self.run=None
    def emit(self,event,**kw):
        row=dict(utc=self.at,repository_id=self.p['repository_id'],branch=self.p['branch'],path=self.p['path'],phase=self.phase,run=deepcopy(self.run),plan_sha256=p.digest(self.p),previous_hash=self.rows[-1]['hash'] if self.rows else '0'*64,counts=deepcopy(self.counts),event=event)
        row.update(kw)
        row['hash']=p.digest(row);self.rows.append(row);return row
    def start(self,phase):
        self.phase=phase;self.emit('phase_start',journal=phase+'.jsonl',pid=123456789,predecessor=self.rows[-1]['hash'] if self.rows else '0'*64)
    def auth(self,g):self.emit('authorization',grant_sha256=p.digest(g),grant_expires_utc=g['expires_utc'],review_sha256=g['review_sha256'],expiry_policy=self.p['expiry_policy'])
    def request(self,route,status=200,diagnostic=None,method='GET',**kw):
        self.counts[method]+=1
        fields=dict(route=route,bytes=0,write_id=None,old_blob=None,revision=None,parent_digest=None,**kw)
        self.emit('request',method=method,budget_phase='bootstrap',**fields)
        self.emit('response',result='http-'+str(status),**({'diagnostic':diagnostic} if diagnostic else {}),**fields)
    def pred(self):return dict(frontier_hash=self.rows[-1]['hash'],frontier_rows=len(self.rows),highwater=self.at,counts=deepcopy(self.counts),files_sha256={})
    def journal(self,path):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(p.canonical(x)+'\n' for x in self.rows),encoding='utf-8',newline='\n')

def grant(plan,phase,a=None,end='2026-10-12T00:00:00Z'):
    g=sim.fixture_grant(plan,phase,expires=end);g['review_sha256']=p.digest(a) if a else None;return g

def review(value,pid=123456789,at='2026-10-11T00:00:00Z'):
    value.update(reviewer='SYNTHETIC ONLY',evidence_sha256='e'*64,original_pid=pid,observed_utc=at,terminal_code_path_checked=True,all_workers_ended=True,triggers_paused=True,human_review=True)
    if 'human_terminal_end_report' in value:value['human_terminal_end_report']=True

def generate():
    global _CACHE
    if _CACHE:return _CACHE
    base=Path(tempfile.mkdtemp(prefix='p3-inputs-'));_CACHE=base
    plan=sim.plan(base/'never-open-session')
    plan.update(repo=u.REPO,repository_id=u.RID,credential_repository_ids=[u.RID],code_head=c.ORIGINAL_HEAD,code_tree=c.ORIGINAL_TREE,code_pins={'tools/p3_github_probe.py':hashlib.sha256(c.git(W,'show',c.ORIGINAL_HEAD+':tools/p3_github_probe.py')).hexdigest()},expires_utc='2026-10-12T00:00:00Z')
    execution=base/'p3-tarifbefund-20261012/root-snapshot';pins=p.build_bootstrap(plan,execution);plan.update(seed_commit=pins['seed_commit'],seed_sha256=pins['seed_sha256'])
    assert pins['seed_commit']==u.SEED and pins['seed_sha256']==u.SEED_SHA,pins
    save(base/'p3-bootstrap-freigabevorbereitung-20261011/PLAN-NOT-APPROVED.json',plan)
    rr=Rows(plan);rr.start('bootstrap');g0=grant(plan,'bootstrap');rr.auth(g0);rr.request(r.routes(plan)[0],401);rr.emit('phase_halt',result='incomplete-no-retry-no-release')
    reader=c.template();reader.update(original_plan_sha256=p.digest(plan),original_grant=g0,original_code_materialization=c.original_materialization(plan),execution_code=code(plan,r.BASE_HEAD),root=dict(directory=str(execution),files_sha256=c.root_files(execution)),expires_utc=plan['expires_utc'])
    reader['predecessor'].update(journal_sha256='a'*64,frontier_hash=rr.rows[-1]['hash'],highwater=rr.at,database_sha256='a'*64,marker_sha256='a'*64,lock_sha256='a'*64);review(reader['review'])
    gr=grant(plan,c.PHASE,reader);rr.start(c.PHASE);rr.auth(gr);rr.emit('reader401_amendment',amendment_sha256=p.digest(reader),execution_head=r.BASE_HEAD,execution_tree=r.BASE_TREE,original_code_head=plan['code_head'],original_pid=123456789,predecessor_frontier=rr.rows[4]['hash'],process_end_observation='currently-absent',result='reviewed-single-continuation')
    for route,status in zip(r.routes(plan)[:4],(200,200,404,403)):rr.request(route,status)
    rr.emit('phase_halt',result='incomplete-no-retry-no-release')
    diag=r.template(r.DIAG);diag.update(original_plan_sha256=p.digest(plan),reader401_amendment=reader,reader401_grant=gr,reader401_code_materialization=r.materialization(reader['execution_code']),root=reader['root'],routes=r.routes(plan),execution_code=code(plan,r.SCRIPT_HEAD),expires_utc=plan['expires_utc']);diag['predecessor'].update(rr.pred());review(diag['review'])
    gd=grant(plan,r.DIAG,diag);rr.start(r.DIAG);rr.auth(gd);rr.emit('rules403_amendment',amendment_sha256=p.digest(diag),execution_code=diag['execution_code'],predecessor_frontier=rr.rows[16]['hash'],process_end_observation='currently-absent',result='separately-reviewed-'+r.DIAG);rr.emit('phase_halt',result='incomplete-no-retry-no-release',category='incomplete-or-expired')
    parent=r.reader_template();parent.update(original_plan_sha256=p.digest(plan),reader401_amendment=reader,reader401_grant=gr,reader401_code_materialization=diag['reader401_code_materialization'],root=reader['root'],routes=r.routes(plan),execution_code=code(plan,u.BASE),expires_utc='2026-10-12T01:00:00Z',interrupted_diagnosis=dict(amendment=diag,grant=gd,code_materialization=r.materialization(diag['execution_code'])))
    parent['predecessor'].update(rr.pred());review(parent['review'])
    parent['reader_validity'].update(original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],frontier_hash=rr.rows[-1]['hash'],independent_review_sha256='e'*64,not_before_utc='2026-10-12T00:00:00Z',expires_utc=parent['expires_utc'])
    gp=grant(plan,r.RESUME,parent,end=parent['expires_utc']);rr.at='2026-10-12T00:00:00Z';rr.start(r.RESUME);rr.emit('reader_validity',amendment_sha256=p.digest(parent),grant_sha256=p.digest(gp),validity=parent['reader_validity'],validity_sha256=p.digest(parent['reader_validity']),execution_code=parent['execution_code']);rr.emit('phase_halt',result='incomplete-no-retry-no-release',category='incomplete-or-expired')
    script=base/'p3-reader-20h-20261012/reader_inspection.py';script.parent.mkdir(exist_ok=True);script.write_text('# Synthetic inspector evidence; never executed\n',encoding='utf-8')
    i=dict(schema='p3-input-cancel-inspection-v2-20h',original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],parent_amendment=parent,parent_grant=gp,root=reader['root'],execution_code=parent['execution_code'],operator_script_sha256=c.sha(script),journal=r.RESUME+'.jsonl',frontier_hash=rr.rows[-1]['hash'],terminal_keyboard_interrupt_report_checked=True,explicit_user_twenty_hours=True,time_authorization_sha256='e'*64,review_evidence_sha256='e'*64,not_before_utc='2026-10-12T01:00:00Z',expires_utc='2026-10-12T21:00:00Z',scope='reader-inspect-after-input-cancel-exact24-two-GET-no-write')
    gi=grant(plan,'inspect',i,end=i['expires_utc']);rr.at=i['not_before_utc'];rr.start('inspect');rr.auth(gi);rr.emit('input_cancel_inspection',amendment_sha256=p.digest(i),review_evidence_sha256='e'*64,scope=i['scope'])
    rr.emit('inspection_route',route=r.routes(plan)[0]);rr.request(r.routes(plan)[0]);rr.emit('inspection_route',route=r.routes(plan)[3]);rr.request(r.routes(plan)[3],403);rr.emit('inspection_error',route=r.routes(plan)[3],diagnostic={'category':'feature-unavailable-hint','feature_absence_proved':False});rr.emit('phase_halt',result='incomplete-no-retry-no-release',category='feature-unavailable-hint')
    assert len(rr.rows)==35
    save(base/'p3-reader-20h-20261012/INSPECTION.json',i);save(base/'p3-reader-20h-20261012/GRANT.json',gi);rr.journal(base/'p3-tarifbefund-20261012/session-snapshot/inspect.jsonl')
    folder=base/'p3-public-umstellung-20261012';save(folder/'ACCEPTANCE.json',dict(status='public_visibility_changed_and_UI_verified',repository=u.REPO,repository_id=u.RID,visibility_mutations=1,human_authorization='SYNTHETIC ONLY - no real authorization',general_UI_result='This repository is currently public.',repository_still_empty=True,actual_store_upload=False,other_repository_visibility_changes=0))
    for name in ('PUBLIC-CONFIRMED.png','ACTIONS-DISABLED.png','PAGES-DISABLED.png','RULESETS-EMPTY.png'):(folder/name).write_bytes(b'SYNTHETIC VISIBILITY FIXTURE - NOT A SCREENSHOT\n'+name.encode())
    old=u.template();old.update(original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],root=reader['root'],execution_code=code(plan,u.FAILED_HEAD),not_before_utc='2026-10-12T02:00:00Z',expires_utc='2026-10-12T22:00:00Z',time_authorization_sha256='e'*64)
    old['history'].update(inspection=i,grant=gi,operator_script=dict(path=str(script),sha256=c.sha(script)),code_materialization=r.materialization(i['execution_code']));old['visibility'].update(acceptance_path=str(folder/'ACCEPTANCE.json'),files_sha256={f.name:c.sha(f) for f in folder.iterdir()});old['predecessor'].update(rr.pred());review(old['review'],at=old['not_before_utc']);go=grant(plan,u.PHASE,old,end=old['expires_utc'])
    save(base/'p3-public-root-hauptchat-abnahme-20261012/PUBLIC-AMENDMENT.json',old);save(base/'p3-public-root-hauptchat-abnahme-20261012/PUBLIC-GRANT.json',go)
    rr.at=old['not_before_utc'];rr.start(u.PHASE);rr.auth(go);rr.emit('public_root_review',amendment_sha256=p.digest(old),grant_sha256=p.digest(go),scope=u.SCOPE,execution_code=old['execution_code'],original_expires_utc=plan['expires_utc'],not_before_utc=old['not_before_utc'],expires_utc=old['expires_utc'],bootstrap_case_counts=dict(GET=7,PUT=0,GIT_PUSH=0))
    for j,(route,status) in enumerate(zip(r.routes(plan),(200,200,404,200,200,200,404))):rr.request(route,status,{'category':'not-found' if j==2 else 'unknown-404','feature_absence_proved':False} if status==404 else None)
    rr.emit('phase_halt',result='incomplete-no-retry-no-release',category='public-root-incomplete');assert len(rr.rows)==53
    rr.journal(base/'p3-public-root-404-befund-20261012/session-snapshot/bootstrap-public-root-once.jsonl')
    successful=u.template(u.CONTINUE);successful.update(original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],root=old['root'],history=old['history'],visibility=old['visibility'],execution_code=code(plan,__import__('p3_public_operations').BASE),not_before_utc='2026-10-13T00:00:00Z',expires_utc='2026-10-13T20:00:00Z',time_authorization_sha256='e'*64,stopped_public=dict(amendment=old,grant=go,code_materialization=r.materialization(old['execution_code'])));successful['predecessor'].update(rr.pred());review(successful['review'],at=successful['not_before_utc']);gs=grant(plan,u.CONTINUE,successful,end=successful['expires_utc'])
    save(base/'p3-public-branch-hauptchat-abnahme-20261013/PUBLIC-CONTINUATION.json',successful);save(base/'p3-public-branch-hauptchat-abnahme-20261013/PUBLIC-GRANT.json',gs)
    success_rows(rr,successful,gs)
    rr.journal(base/'p3-public-root-erfolg-20261013/session-snapshot/bootstrap-public-missing-branch-once.jsonl')
    happy_inputs(base,rr,successful,gs)
    save(base/'SYNTHETIC-INPUTS.json',{'generated_from_source_only':True,'real_audit_files_read':0,'fixture_authority_only':True})
    return base

def success_rows(rr,a,g):
    plan=rr.p;base=r.routes(plan)[0];tree=c.git(Path(a['root']['directory']),'rev-parse',u.SEED+'^{tree}').decode().strip();body=p.synthetic_seed(plan);blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
    rr.at=a['not_before_utc'];rr.start(u.CONTINUE);rr.auth(g);rr.emit('public_root_review',amendment_sha256=p.digest(a),grant_sha256=p.digest(g),scope=u.SCOPE,execution_code=a['execution_code'],original_expires_utc=plan['expires_utc'],not_before_utc=a['not_before_utc'],expires_utc=a['expires_utc'],bootstrap_case_counts=dict(GET=14,PUT=0,GIT_PUSH=0))
    for j,route in enumerate(r.routes(plan)[:6]):rr.request(route,404 if j==2 else 200,dict(category='not-found',feature_absence_proved=False) if j==2 else None)
    rr.emit('public_preflight',result='confirmed-public-empty',scope=u.SCOPE);rr.request(base);rr.emit('public_writer_auth',result='authenticated-read-only-no-write-rights-guarantee',repository_id=u.RID);rr.emit('public_push_prepare',commit=u.SEED,bytes=1981,parents=[],amendment_sha256=p.digest(a));rr.counts['GIT_PUSH']+=1;rr.emit('request',method='GIT_PUSH',budget_phase='bootstrap',commit=u.SEED,bytes=1981,parents=[],write_id='synthetic-explicit-blocked-seed-v1',revision=0,old_blob=None);rr.emit('public_push_response',result='returned-success-not-yet-confirmed')
    ref=base+'/git/ref/heads/'+plan['branch'];content=base+'/contents/delivery/stream.json?ref='+u.SEED
    rb=dict(result='observed-only',commit=u.SEED,old_blob=blob,bytes=1981,revision=0,write_id='synthetic-explicit-blocked-seed-v1')
    for route in (ref,content,ref):rr.request(route)
    rr.emit('readback',**rb)
    for route in (content,base+'/git/commits/'+u.SEED,base+'/git/trees/'+tree+'?recursive=1',ref,content,ref):rr.request(route)
    rr.emit('readback',**rb);rr.emit('history',result='complete-blocked-root-confirmed',commit=u.SEED,revision=0,revisions=1,body_sha256=u.SEED_SHA,independently_read_commits=1,verified_anchor=None)
    for j,route in enumerate(r.routes(plan)):rr.request(route,404 if j in (2,6) else 200,dict(category='not-found',feature_absence_proved=False) if j in (2,6) else None)
    rr.emit('public_preflight',result='confirmed-public-original-root',scope=u.SCOPE);rr.emit('phase_end',result='confirmed',scope=u.SCOPE,activation_allowed=False,bootstrap_case_counts=deepcopy(rr.counts),phase_counts=dict(GET=23,PUT=0,GIT_PUSH=1));assert len(rr.rows)==112

def happy_inputs(base,rr,successful,gs):
    """Generate activation/happy wire history from the existing CAS engine model."""
    import p3_public_operations as o
    import p3_happy_readback as h
    from unittest.mock import patch
    from datetime import datetime
    plan=rr.p
    a=o.template();a.update(original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],execution_code=code(plan,h.BASE),not_before_utc='2026-10-13T01:00:00Z',expires_utc='2026-10-13T21:00:00Z')
    a['root_success'].update(amendment=successful,grant=gs,code_materialization=r.materialization(successful['execution_code']));a['entry'].update(frontier_hash=rr.rows[-1]['hash'],highwater=rr.at,files_sha256={});review(a['review'],at=a['not_before_utc'])
    g=o.grant_template();g.update(plan_sha256=p.digest(plan),amendment_sha256=p.digest(a),review_sha256=p.digest(a),human_authorization=True,approved_by='SYNTHETIC ONLY',approval_evidence_sha256='e'*64,expires_utc=a['expires_utc'],entry_journal=u.CONTINUE+'.jsonl',entry_frontier_hash=rr.rows[-1]['hash'],entry_rows=112,entry_files_sha256={})
    save(base/'p3-public-storebetrieb-start-20261013/OPERATIONS.json',a);save(base/'p3-public-storebetrieb-start-20261013/INITIAL-GRANT.json',g)
    class Memory:
        # Fixture data construction only; actual tests use durable real Ledger.
        p=plan;finish_hash=None;run=None
        def __init__(self):self.counts=rr.counts;self.prior_rows=deepcopy(rr.rows);self.phase='activate';self.route=None
        def emit(self,event,**kw):
            if event=='readback' and old is not None: raise p.gh.StoreConflict('Synthetic local stop before readback publication')
            rr.run=self.run
            if event in ('request','response'):kw.setdefault('route',self.route)
            rr.emit(event,**kw)
        def charge(self,method,**kw):self.counts[method]+=1;self.emit('request',method=method,budget_phase=self.phase,**kw)
        def checkpoint(self,*args):pass
        def assert_published(self):pass
        def check_time(self,*args):pass
    class TraceBoundary(p.Boundary):
        def request(self,method,route,payload=None):self.ledger.route=route;return super().request(method,route,payload)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):return cls.fromisoformat('2026-10-11T00:00:00+00:00')
    api=sim.API(plan);original_put=api.put
    def put(body,parent,commit=None):
        rev=json.loads(body)['revision']
        return original_put(body,parent,h.OLD if rev==9 else 'f'*40 if rev==10 else commit)
    api.put=put;opened=api.open;old=None
    def open_request(req,timeout):
        nonlocal old
        if req.method=='PUT' and json.loads(p.base64.b64decode(json.loads(req.data)['content']))['revision']==10:
            old=api.head
        answer=opened(req,timeout)
        if old and req.method=='GET' and '/git/ref/' in req.full_url:return sim.Response({'ref':'refs/heads/'+plan['branch'],'object':{'sha':old,'type':'commit'}})
        return answer
    sequence=[0]
    def writeid(*_):
        sequence[0]+=1
        return h.WRITE if mem.counts['PUT']==10 else f'{sequence[0]:032x}'
    with patch.object(p,'datetime',Clock),patch.object(p.gh.secrets,'token_hex',side_effect=writeid):
        mem=Memory()
        for native in ('activate','happy'):
            mem.phase=native;mem.run=None;rr.phase='public-store-'+native;rr.at=a['not_before_utc'];rr.run=None;rr.emit('phase_start',journal=rr.phase+'.jsonl',pid=123456789,predecessor=rr.rows[-1]['hash']);rr.auth(g);rr.emit('operations_review',amendment_sha256=p.digest(a),grant_sha256=p.digest(g),execution_code=a['execution_code'],section='initial',section_grant=g)
            bound=TraceBoundary(plan,mem,'synthetic-reader','synthetic-writer',open_request,guard=p.GrantGuard(plan,sim.fixture_grant(plan,native,expires=plan['expires_utc']),native));client=p.Client(bound)
            # Boundary's constructor emits a native authorization; the public
            # section authorization above is the one in the fixture contract.
            rr.rows.pop()
            bound.preflight();p.verify_history(client)
            if native=='activate':p.activation(client);rr.emit('phase_end',result='confirmed',scope=o.SCOPE);assert len(rr.rows)==180,len(rr.rows)
            else:
                try:p.sequence(client,native)
                except p.gh.StoreConflict:rr.emit('phase_halt',result='incomplete-no-retry-no-release',category='operations-local-or-expired')
                else:raise AssertionError('Synthetic final unconfirmed claim absent')
    assert len(rr.rows)==375,(len(rr.rows),rr.counts)
    rr.journal(base/'p3-store-happy-halt-20261013/session-snapshot/public-store-happy.jsonl')
    oldbody=p.base64.b64decode(api.records[h.OLD]['body']);claim=p.base64.b64decode(api.records['f'*40]['body'])
    assert len(oldbody)==5626 and len(claim)==5758,(len(oldbody),len(claim))
    anchors=dict(BLOB=api.records[h.OLD]['blob'],PARENT=json.loads(oldbody)['body_digest'],CLAIM_BLOB=api.records['f'*40]['blob'],CLAIM_SHA=hashlib.sha256(claim).hexdigest())
    save(base/'SYNTHETIC-HAPPY-ANCHORS.json',anchors)
    reader=h.template();reader.update(original_plan_sha256=p.digest(plan),original_expires_utc=plan['expires_utc'],operations=a,initial_grant=g,historical_code_materialization=r.materialization(a['execution_code']),execution_code=code(plan,__import__('p3_happy_finish').BASE),not_before_utc='2026-10-13T22:00:00Z',expires_utc='2026-10-14T18:00:00Z');reader['entry'].update(frontier_hash=rr.rows[-1]['hash'],highwater=rr.at,files_sha256={});review(reader['review'],at=reader['not_before_utc']);rg=h.grant_template();rg.update(plan_sha256=p.digest(plan),review_sha256=p.digest(reader),human_authorization=True,approved_by='SYNTHETIC ONLY',approval_evidence_sha256='e'*64,expires_utc=reader['expires_utc'])
    save(base/'p3-happy-abgleich-start-20261013/READER-CONTRACT.json',reader);save(base/'p3-happy-abgleich-start-20261013/READER-GRANT.json',rg)
    reader_rows(rr,reader,rg,api,anchors)
    rr.journal(base/'p3-happy-claim-bestaetigt-20261013/session-snapshot'/ (h.PHASE+'.jsonl'))

def bind_happy(base):
    """Replace only closed-session anchor VALUES with generated fixture values.

    Validation functions, limits, grants, locks, process and runtime gates remain
    unchanged. Source defaults continue to bind the real closed production case.
    """
    import p3_happy_readback as h
    import p3_happy_finish as f
    values=json.loads((Path(base)/'SYNTHETIC-HAPPY-ANCHORS.json').read_text())
    h.BLOB=values['BLOB'];h.PARENT=values['PARENT'];f.BLOB=values['CLAIM_BLOB'];f.CLAIM_SHA=values['CLAIM_SHA']

def reader_rows(rr,a,g,api,anchors):
    import p3_happy_readback as h
    import p3_happy_finish as f
    plan=rr.p;base=r.routes(plan)[0];rr.at=a['not_before_utc'];rr.phase=h.PHASE;rr.run=None;rr.start(h.PHASE);rr.auth(g);rr.emit('happy_readback_review',amendment_sha256=p.digest(a),grant=g,execution_code=a['execution_code'])
    for j,route in enumerate(r.routes(plan)):rr.request(route,404 if j in (2,6) else 200,dict(category='not-found',feature_absence_proved=False) if j in (2,6) else None)
    rr.emit('preflight',result='confirmed-public-existing-synthetic-store')
    claim=f.CLAIM;body=p.base64.b64decode(api.records['f'*40]['body']);env=json.loads(body);tree=api.records['f'*40]['tree'];ref=base+'/git/ref/heads/'+plan['branch']
    rr.request(ref);rr.emit('happy_head',commit=claim);rr.request(base+'/contents/delivery/stream.json?ref='+claim);rr.emit('happy_content',commit=claim,body_sha256=anchors['CLAIM_SHA'],old_blob=anchors['CLAIM_BLOB'],revision=10,write_id=h.WRITE)
    rr.request(ref);rr.emit('happy_head',commit=claim);rr.request(base+'/contents/delivery/stream.json?ref='+h.OLD);rr.emit('happy_content',commit=h.OLD,body_sha256=hashlib.sha256(p.base64.b64decode(api.records[h.OLD]['body'])).hexdigest(),old_blob=anchors['BLOB'],revision=9)
    rr.request(base+'/git/commits/'+claim);rr.emit('happy_parent',commit=claim,parents=[h.OLD],tree=tree,result='observed-only');rr.request(base+'/git/trees/'+tree+'?recursive=1')
    rr.emit('happy_reconciliation',result='own-claim-exact-present-no-recovery',commit=claim,old_blob=anchors['CLAIM_BLOB'],body_sha256=anchors['CLAIM_SHA'],parents=[h.OLD],owner=p.owner(plan,2),revision=10,bytes=len(body),write_id=h.WRITE,root=u.SEED,verified_journal_commits=10,recovery_authorized=False,tree=tree)
    rr.emit('phase_end',result='read-only-complete-recovery-forbidden',outcome='own-claim-exact-present-no-recovery',recovery_authorized=False);assert len(rr.rows)==412,len(rr.rows)
