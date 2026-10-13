"""Separately reviewed one-CAS owner close and ordered synthetic remainder."""
import sys
if __name__=='__main__':
    from p3_happy_finish import main
    try:sys.exit(main())
    except Exception as exc:
        print('HALT: '+getattr(exc,'category','finish-binding-grant-or-publication')+'. Kein Retry.',file=sys.stderr);sys.exit(2)
import argparse,json,hashlib,re,sqlite3,os,subprocess
from pathlib import Path
from copy import deepcopy
import p3_happy_readback as h
p=h.p;o=h.o;r=h.r;c=h.c
BASE='a67a3a43ba3de1d108a7c39fb2f99983210a4e0e';TREE='149bc16b0e669a37b25884e6f534b57904834090'
CLAIM='372bda3718ca65b2e31e70aaca1d6bda1403aec6';BLOB='4f6141ad0690aea3c03571f8ad57347f025d73c7'
CLAIM_SHA='ea3f2ff9d914839349872aadc46b65df77d16e96257198d4622b5bbf26aee522'
ORDER=list(p.FINISH_PHASES);CLOSE,LOST,LOSS,TAKE,INSPECT=ORDER
SECTIONS={'close':[CLOSE],'rest':[LOST,LOSS],'takeover':[TAKE],'inspect':[INSPECT]}
SCOPE='only-confirmed412-claim-owner-null-one-CAS-ordered-rest-root-anchor-extraGET30'
read=h.read;need=h.need

def template():
    return {'schema':'p3-happy-finish-v1','scope':SCOPE,'original_plan_sha256':None,'original_expires_utc':None,
        'reader_contract':None,'reader_grant':None,'reader_code_materialization':None,
        'entry':{'journal':h.PHASE+'.jsonl','rows':412,'frontier_hash':None,'highwater':None,'counts':{'GET':147,'PUT':11,'GIT_PUSH':1},'files_sha256':None},
        'execution_code':{'code_head':None,'code_tree':None,'code_pins':None},
        'review':{**deepcopy(h.template()['review']),'reader_pid':None,'reader_ended':False},
        'not_before_utc':None,'expires_utc':None}
def grant_template(section='close'):
    return {'schema':'p3-human-finish-section-v1','section':section,'phases':SECTIONS[section],
        'plan_sha256':None,'review_sha256':None,'amendment_sha256':None,'human_authorization':False,'approved_by':None,'approval_evidence_sha256':None,
        'expires_utc':None,'entry_journal':None,'entry_rows':None,'entry_frontier_hash':None,'entry_files_sha256':None}
def window(plan,a,current=True):return h.window(plan,a,current)
def shape(plan,a):
    t=template();need(set(a)==set(t) and a['schema']==t['schema'] and a['scope']==SCOPE
        and a['original_plan_sha256']==p.digest(plan) and a['original_expires_utc']==plan['expires_utc'],'finish-original-contract')
    old=a['reader_contract'];h.shape(plan,old)
    need(old['execution_code']['code_head']==BASE and old['execution_code']['code_tree']==TREE
        and a['reader_code_materialization']==r.materialization(old['execution_code']),'finish-reader-source')
    need(set(a['execution_code']['code_pins'])>=set(old['execution_code']['code_pins'])|
        {'tools/p3_happy_finish.py','tools/p3_happy_finish_start.ps1','engine/github_delivery.py'},'finish-current-pins')
    c.git(p.ROOT,'merge-base','--is-ancestor',BASE,a['execution_code']['code_head']);window(plan,a,False)

def confirmed_reader(plan,rows,a):
    old=a['reader_contract'];g=a['reader_grant'];h.history(plan,rows[:375],old)
    t=rows[375:412];e=a['entry']
    need(len(t)==37 and all(x['phase']==h.PHASE and x['run'] is None for x in t)
        and t[0]['event']=='phase_start' and t[0]['journal']==h.PHASE+'.jsonl'
        and t[1]['event']=='authorization' and t[2]['event']=='happy_readback_review'
        and t[1]['grant_sha256']==p.digest(g) and t[1]['review_sha256']==p.digest(old)
        and t[2]['amendment_sha256']==p.digest(old) and t[2]['grant']==g
        and t[2]['execution_code']==old['execution_code'],'finish-reader-authority')
    need(set(g)==set(h.grant_template()) and g['schema']=='p3-human-happy-readback-v1' and g['phase']==h.PHASE
        and g['plan_sha256']==p.digest(plan) and g['review_sha256']==p.digest(old) and g['human_authorization'] is True
        and all(c.parse_utc(old['not_before_utc'])<=c.parse_utc(x['utc'])<min(c.parse_utc(old['expires_utc']),c.parse_utc(g['expires_utc'])) for x in t),'finish-reader-timeliness')
    req=[x for x in t if x['event']=='request'];resp=[x for x in t if x['event']=='response']
    base=r.routes(plan)[0];heads=[x['commit'] for x in t if x['event']=='happy_head'];contents=[x for x in t if x['event']=='happy_content']
    report=t[-2]
    expected=r.routes(plan)+[base+'/git/ref/heads/'+plan['branch'],base+'/contents/delivery/stream.json?ref='+CLAIM,
        base+'/git/ref/heads/'+plan['branch'],base+'/contents/delivery/stream.json?ref='+h.OLD,
        base+'/git/commits/'+CLAIM,base+'/git/trees/'+report.get('tree','')+'?recursive=1']
    need(len(req)==len(resp)==13 and all(x['method']=='GET' for x in req) and [x['route'] for x in req]==expected
        and [x['result'] for x in resp]==['http-200','http-200','http-404']+['http-200']*3+['http-404']+['http-200']*6
        and heads==[CLAIM,CLAIM] and len(contents)==2 and contents[0]['body_sha256']==CLAIM_SHA
        and contents[0]['old_blob']==BLOB and contents[0]['revision']==10 and contents[0]['write_id']==h.WRITE
        and contents[1]['commit']==h.OLD,'finish-reader-complete-requests')
    need(report['event']=='happy_reconciliation' and report['result']=='own-claim-exact-present-no-recovery'
        and report['commit']==CLAIM and report['old_blob']==BLOB and report['body_sha256']==CLAIM_SHA
        and report['parents']==[h.OLD] and report['owner']==p.owner(plan,2) and report['revision']==10
        and report['bytes']==5758 and report['write_id']==h.WRITE and report['root']==o.u.SEED
        and report['verified_journal_commits']==10 and report['recovery_authorized'] is False
        and t[-1]['event']=='phase_end' and t[-1]['result']=='read-only-complete-recovery-forbidden'
        and t[-1]['outcome']==report['result'] and t[-1]['recovery_authorized'] is False,
        'finish-exact-confirmed-claim')
    need(e['rows']==412 and e['journal']==h.PHASE+'.jsonl' and e['counts']==t[-1]['counts']=={'GET':147,'PUT':11,'GIT_PUSH':1}
        and e['frontier_hash']==t[-1]['hash'] and e['highwater']==t[-1]['utc'],'finish412-entry')

def eligible(plan,rows,a,phase,review=None):
    confirmed_reader(plan,rows,a);index=ORDER.index(phase);tail=rows[412:]
    starts=[j for j,x in enumerate(rows) if j>=412 and x['event']=='phase_start']
    need([rows[j]['phase'] for j in starts]==ORDER[:index] and not any(x['event']=='phase_halt' for x in tail),'finish-order-halt-replay')
    if index==0:need(len(rows)==412,'finish-only-at412')
    elif index==3:
        need(rows[-1]['event']=='loss_boundary' and rows[-1]['phase']==LOSS and isinstance(review,dict),'finish-takeover-positive-loss-end')
        p.validate_termination(plan,review,Path(plan['journal_directory'])/(LOSS+'.jsonl'))
        need(review['termination']['exit_code']==23 and review['termination']['journal_name']==LOSS+'.jsonl','finish-actual-loss-wait')
        c.process_ended(review['termination']['pid'])
    else:need(rows[-1]['event']=='phase_end' and rows[-1]['result']=='confirmed' and rows[-1]['phase']==ORDER[index-1],'finish-unconfirmed-predecessor')
    for k,j in enumerate(starts):
        auth,record=rows[j+1:j+3];g=record['grant'];section=next(s for s,v in SECTIONS.items() if rows[j]['phase'] in v)
        need(record['event']=='finish_review' and record['amendment_sha256']==p.digest(a) and record['execution_code']==a['execution_code']
            and set(g)==set(grant_template(section)) and g['section']==section and g['phases']==SECTIONS[section]
            and g['human_authorization'] is True and g['plan_sha256']==p.digest(plan) and g['amendment_sha256']==p.digest(a)
            and auth['event']=='authorization' and auth['grant_sha256']==p.digest(g) and auth['review_sha256']==g['review_sha256']
            and all(c.parse_utc(a['not_before_utc'])<=c.parse_utc(x['utc'])<min(c.parse_utc(a['expires_utc']),c.parse_utc(g['expires_utc'])) for x in rows[j:starts[k+1] if k+1<len(starts) else len(rows)]),'finish-historical-grant')
    if index>0:
        end=starts[1] if len(starts)>1 else len(rows);closed=rows[412:end]
        delta=[x for x in closed if x['event']=='finish_delta'];anchors=[x for x in closed if x['event']=='history'];trees=[x for x in closed if x['event']=='finish_tree'];puts=[x for x in closed if x['event']=='request' and x.get('method')=='PUT']
        need(len(delta)==len(anchors)==len(trees)==len(puts)==1,'finish-close-proof-missing')
        anchor=anchors[0];q=puts[0]
        need(anchor['result']=='complete-blocked-root-confirmed' and anchor['revision']==11 and anchor['revisions']==12
            and anchor['verified_anchor']==CLAIM and anchor['root']==o.u.SEED and anchor['snapshot_digest']==delta[0]['snapshot_digest']
            and anchor['write_id']==q['write_id'] and q['old_blob']==BLOB and q['revision']==11
            and anchor['commit']==trees[0]['commit'] and anchor['blob_sha']==trees[0]['blob_sha']
            and any(x['event']=='parent' and x['commit']==anchor['commit'] and x['parents']==[CLAIM] for x in closed)
            and any(x['event']=='readback' and x['commit']==anchor['commit'] and x['revision']==11 and x['old_blob']==anchor['blob_sha'] for x in closed), 'finish-close-anchor-invalid')
    need(sum(x['event']=='request' and x.get('confirmation_retry') is True for x in rows)<=30,'finish-additional-read-pool')
    need(not any(x['event']=='response' and x['result']=='unknown' and x['bytes']==0 for x in tail),'finish-unknown-read')

def state(plan,a,phase,review=None,ledger=None):
    root=Path(plan['journal_directory']);db=ledger.db if ledger else sqlite3.connect((root/'probe-session.sqlite3').as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        need(db.execute('PRAGMA integrity_check').fetchone()==('ok',),'finish-db-integrity')
        front=db.execute('SELECT plan,journal,published,highwater FROM frontier').fetchone();rows=[json.loads(x[0]) for x in db.execute('SELECT body FROM events ORDER BY seq')]
    finally:
        if not ledger:db.close()
    need(front==(p.digest(plan),front[1],rows[-1]['hash'],max(x['utc'] for x in rows)) and p.Ledger.verify(root/front[1],p.digest(plan))==rows,'finish-authoritative-frontier')
    eligible(plan,rows,a,phase,review)
    starts=[j for j,x in enumerate(rows) if x['event']=='phase_start']
    need({f.name for f in root.glob('attempt-*.json')}=={'attempt-'+rows[j]['phase']+'.json' for j in starts},'finish-markers')
    for k,j in enumerate(starts):
        stop=starts[k+1] if k+1<len(starts) else len(rows)
        need((root/rows[j]['journal']).read_bytes()==''.join(p.canonical(x)+'\n' for x in rows[:stop]).encode()
            and read(root/('attempt-'+rows[j]['phase']+'.json'))=={v:rows[j][v] for v in ('plan_sha256','phase','journal','pid','predecessor')},'finish-prefix-marker')
    need(not any((root/n).exists() for n in ('probe-session.sqlite3-wal','probe-session.sqlite3-journal')),'finish-unpublished')
    for name,sha in a['entry']['files_sha256'].items():
        if name=='probe-session.sqlite3' and phase!=CLOSE:continue
        if ledger and name=='probe-session.lock':ledger.lock_handle.seek(0);actual=hashlib.sha256(ledger.lock_handle.read()).hexdigest();ledger.lock_handle.seek(0)
        else:actual=c.sha(root/name)
        need(actual==sha,'finish-entry-files')
    c.root_matches(a['reader_contract']['operations']['root_success']['amendment'])
    return front,rows
def validate_locked(l,rows,front,a,review):need(l.path.name==l.phase+'.jsonl' and rows==state(l.p,a,l.phase,review,l)[1],'finish-locked-entry')

class FinishGuard(p.GrantGuard):
    def __init__(self,plan,g,a,phase):self.a=deepcopy(a);self.a_hash=p.digest(a);super().__init__(plan,g,phase)
    def validate_binding(self):
        g=self.grant
        need(set(g)==set(grant_template(g['section'])) and g['schema']=='p3-human-finish-section-v1' and self.phase in SECTIONS[g['section']]
            and g['phases']==SECTIONS[g['section']] and g['plan_sha256']==self.plan_hash and g['amendment_sha256']==self.a_hash
            and g['human_authorization'] is True and isinstance(g['approved_by'],str) and g['approved_by']
            and re.fullmatch('[0-9a-f]{64}',g['approval_evidence_sha256'] or ''),'finish-human-section-grant')
    def deadlines(self):return [window(self.p,self.a)[1],c.parse_utc(self.grant['expires_utc'])]
    def check(self,ledger=None):
        super().check(ledger);need(p.digest(self.a)==self.a_hash,'finish-contract-changed')
        if ledger:need(ledger.finish_hash==self.a_hash and ledger.counts['GIT_PUSH']==1,'finish-bound-live-scope')
    def validate_route(self,method,route):
        if method=='PUT':need(self.phase!=INSPECT and route==r.routes(self.p)[0]+'/contents/delivery/stream.json','finish-PUT-route');return
        h.HappyReadGuard.validate_route(self,method,route) if '/compare/' not in route else need(re.fullmatch(re.escape(r.routes(self.p)[0])+r'/compare/[0-9a-f]{40}\.\.\.[0-9a-f]{40}\?per_page=1',route),'finish-compare-route')
    def validate_payload(self,env):
        if self.phase==CLOSE:
            need(hasattr(self,'close_snapshot') and env['snapshot']==self.close_snapshot
                and env['revision']==11 and env['parent_digest']==self.close_parent_digest
                and env['body_digest']==p.digest(self.close_snapshot) and re.fullmatch('[0-9a-f]{32}',env['write_id']), 'finish-owner-only-payload')

def authorize(plan,a,g,section,approved,review):
    shape(plan,a);window(plan,a);r.verify_execution_code(a['execution_code'])
    need(p.digest(a)==approved and g['section']==section and c.parse_utc(g['expires_utc'])<=c.parse_utc(a['expires_utc']),'finish-independent-grant')
    guard=FinishGuard(plan,g,a,SECTIONS[section][0]);front,rows=state(plan,a,guard.phase,review)
    need(g['review_sha256']==(p.digest(review) if section=='takeover' else p.digest(a))
        and g['entry_journal']==front[1] and g['entry_rows']==len(rows) and g['entry_frontier_hash']==front[2]
        and set(g['entry_files_sha256'])==r.session_files(rows),'finish-current-section-frontier')
    for name,sha in g['entry_files_sha256'].items():need(c.sha(Path(plan['journal_directory'])/name)==sha,'finish-grant-entry-bytes')
    if section=='close':
        e=a['review'];need(set(e)==set(template()['review']) and e['original_pid']==rows[180]['pid'] and e['reader_pid']==rows[375]['pid']
            and e['end_basis']==r.END_BASIS and all(e[k] is True for k in ('human_review','terminal_code_path_checked','human_terminal_end_report','all_workers_ended','triggers_paused','reader_ended'))
            and isinstance(e['reviewer'],str) and e['reviewer'] and re.fullmatch('[0-9a-f]{64}',e['evidence_sha256'] or '')
            and c.parse_utc(rows[411]['utc'])<=c.parse_utc(e['observed_utc'])<=p.datetime.now(p.timezone.utc),'finish-positive-old-end-freeze')
        c.process_ended(e['original_pid']);c.process_ended(e['reader_pid'])
    return guard

def close(client):
    b=client.boundary;l=b.ledger;plan=b.p;l.run=p.owner(plan,2)
    record=client.read(plan['repo'],plan['branch']);env=p.check_identity(plan,record['body']);snapshot=deepcopy(env['snapshot'])
    need(record['commit_sha']==CLAIM and record['blob_sha']==BLOB and hashlib.sha256(record['body']).hexdigest()==CLAIM_SHA
        and env['revision']==10 and env['write_id']==h.WRITE and len(record['body'])==5758
        and snapshot['control']['owner']==p.owner(plan,2),'finish-fresh-claim-mismatch')
    run=plan['runs'][2]['run_id']
    need(run not in snapshot['commands'] and not any(isinstance(x,dict) and x.get('run_id')==run for x in snapshot['control'].get('health',{}).values()),'finish-second-run-has-work')
    b.writer_identity() # counted authentication at exact target, no write-right guarantee
    snapshot['control']['owner']=None
    b.guard.close_snapshot=deepcopy(snapshot);b.guard.close_parent_digest=env['body_digest']
    l.emit('finish_delta',before_body_sha256=CLAIM_SHA,before_commit=CLAIM,snapshot_digest=p.digest(snapshot),only_owner_to_null=True)
    store=p.store_for(client,2);store._record,store._envelope=record,env;store.snapshot=snapshot;store.revision=10
    store._write() # no enter/claim, no release retry, no health event or transport
    done=store._record;after=store._envelope
    need(after['snapshot']==snapshot and after['revision']==11 and after['parent_digest']==env['body_digest'],'finish-owner-only-delta')
    commit=done['commit_sha']
    # Parent request in _write already returned the full Git commit; retain only
    # its safe tree locator in the probe client, avoiding an uncounted fetch.
    tree_sha=client.last_parent_tree
    tree=b.request('GET',b.base+'/git/trees/'+tree_sha+'?recursive=1')
    need(tree.get('sha')==tree_sha and tree.get('truncated') is False
        and [(x['path'],x['type'],x.get('mode'),x['sha']) for x in tree['tree'] if x['type']!='tree']==[(plan['path'],'blob','100644',done['blob_sha'])], 'finish-full-tree')
    l.emit('finish_tree',commit=commit,tree=tree_sha,blob_sha=done['blob_sha'])
    l.emit('history',result='complete-blocked-root-confirmed',commit=commit,revision=11,revisions=12,
        independently_read_commits=1,verified_anchor=CLAIM,root=o.u.SEED,body_sha256=hashlib.sha256(done['body']).hexdigest(),
        snapshot_digest=after['body_digest'],write_id=after['write_id'],blob_sha=done['blob_sha'],tree=tree_sha)

class Boundary(o.OperationsBoundary):
    writer_identity=o.u.PublicBoundary.writer_identity
def run_phase(plan,a,g,phase,reader,writer,review):
    front,rows=state(plan,a,phase,review);guard=FinishGuard(plan,g,a,phase)
    l=p.Ledger(plan,Path(plan['journal_directory'])/(phase+'.jsonl'),phase,Path(plan['journal_directory'])/front[1],finish_amendment=a,
        reviewed_termination=review if phase==TAKE else None)
    try:
        b=Boundary(plan,l,reader,writer,guard=guard);client=p.Client(b)
        l.emit('finish_review',amendment_sha256=p.digest(a),execution_code=a['execution_code'],grant=g)
        b.preflight()
        if phase==CLOSE:close(client)
        else:
            p.verify_history(client)
            if phase==TAKE:p.takeover(client,review)
            elif phase!=INSPECT:p.sequence(client,p.FINISH_PHASES[phase])
        l.emit('phase_end',result='confirmed',scope=SCOPE)
    except SystemExit as exc:
        if phase==LOSS and exc.code==23:raise
        raise
    except BaseException as exc:
        category=getattr(exc,'category',None) or ('finish-http-'+str(exc.status) if isinstance(exc,p.HTTPStatus) else 'finish-local-or-expired')
        if not l.poisoned:l.emit('phase_halt',result='incomplete-no-retry-no-release',category=category)
        print('HALT: '+category+'. Kein Write-Retry.');raise
    finally:l.close()

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--real',action='store_true');cli.add_argument('--worker',action='store_true');cli.add_argument('--section',choices=SECTIONS,default='close')
    for key in ('plan','amendment','grant','approved-amendment-sha256','termination-review','receipt'):cli.add_argument('--'+key)
    args=cli.parse_args();need(args.real and all((args.plan,args.amendment,args.grant,args.approved_amendment_sha256)),'finish-default-offline')
    plan,a,g=[read(x) for x in (args.plan,args.amendment,args.grant)];review=read(args.termination_review) if args.termination_review else None
    guard=authorize(plan,a,g,args.section,args.approved_amendment_sha256,review)
    if args.section=='rest' and not args.worker:
        need(args.receipt and not Path(args.receipt).exists(),'finish-new-actual-loss-receipt')
        proc=subprocess.Popen([sys.executable,'-B',str(p.ROOT/'tools/p3_happy_finish.py'),*sys.argv[1:],'--worker'])
        try:code=proc.wait(timeout=1200)
        except subprocess.TimeoutExpired:print('HALT: rest-parent-timeout; PID '+str(proc.pid)+' nicht beendet belegt.');return 2
        if code!=23:print('HALT: rest-not-complete; kein Takeover.');return 3 if code==3 else 2
        receipt=o.launcher.observe_exit(proc,plan,Path(plan['journal_directory'])/(LOSS+'.jsonl'),expected_phase=LOSS)
        with Path(args.receipt).open('x',encoding='utf-8') as f:f.write(p.canonical(receipt)+'\n');f.flush();os.fsync(f.fileno())
        print('STOPP: tatsächlicher Exit23/Parentwait. Neuer exakter Takeoverreview/Grant erforderlich.');return 0
    try:reader=p.read_token('Reader');writer='' if args.section=='inspect' else p.read_token('Writer')
    except (KeyboardInterrupt,ValueError):print('Eingabeabbruch vor durablem Start; kein Versuch.');return 3
    guard.check();authorize(plan,a,g,args.section,args.approved_amendment_sha256,review)
    for phase in SECTIONS[args.section]:run_phase(plan,a,g,phase,reader,writer,review)
    print('Nur Abschnitt bestätigt. Keine automatische Folgefreigabe.');return 0
