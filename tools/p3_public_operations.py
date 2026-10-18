"""Prepared public synthetic store section; import/default offline, no grant issuer."""
import sys
if __name__=='__main__':
    from p3_public_operations import main
    try:sys.exit(main())
    except Exception:
        print('HALT: operations-local-binding-or-grant. Kein Retry, keine Schluesselwerte.',file=sys.stderr);sys.exit(2)

import argparse,json,hashlib,os,re,sqlite3,subprocess
from copy import deepcopy
from pathlib import Path
import p3_github_probe as p
import p3_public_root as u
import p3_rules403 as r
import p3_probe_launcher as launcher

BASE='1de1ad52d14c79ea44c6c8843d0795740d140ade';TREE='ecbd51e47adcc17ccddac2cbb2cc470597abf7d8'
INITIAL=['public-store-'+x for x in ('activate','happy','lost-after','process-loss')]
SECTIONS={'initial':INITIAL,'takeover':['public-store-takeover'],'inspect':['public-store-inspect']}
ORDER=[*INITIAL,'public-store-takeover','public-store-inspect']
SCOPE='public-existing-synthetic-store-only-28PUT-stop-then-separate-1PUT-takeover-inspect'

def read(f):return json.loads(Path(f).read_text(encoding='utf-8-sig'))

def template():
    return {'schema':'p3-public-operations-v1','scope':SCOPE,'original_plan_sha256':None,'original_expires_utc':None,
        'root_success':{'amendment':None,'grant':None,'code_materialization':None},
        'entry':{'journal':u.CONTINUE+'.jsonl','rows':112,'frontier_hash':None,'highwater':None,
            'counts':{'GET':37,'PUT':0,'GIT_PUSH':1},'files_sha256':None},
        'execution_code':{'code_head':None,'code_tree':None,'code_pins':None},
        'review':deepcopy(u.template()['review']),'not_before_utc':None,'expires_utc':None}

def grant_template(section='initial'):
    return {'schema':'p3-human-operations-section-v1','section':section,'phases':SECTIONS[section],
        'plan_sha256':None,'amendment_sha256':None,'human_authorization':False,'approved_by':None,
        'approval_evidence_sha256':None,'expires_utc':None,'review_sha256':None,
        'entry_journal':None,'entry_frontier_hash':None,'entry_rows':None,'entry_files_sha256':None}

def window(plan,a,current=True):
    start,end=u.c.parse_utc(a['not_before_utc']),u.c.parse_utc(a['expires_utc'])
    p.require(u.c.parse_utc(plan['expires_utc'])<=start<end and end-start<=p.timedelta(hours=20),'Operations window max20h')
    if current:p.require(start<=p.datetime.now(p.timezone.utc)<end,'Operations window expired/not started')
    return start,end

def shape(plan,a):
    p.validate_plan_structure(plan);t=template()
    p.require(set(a)==set(t) and a['schema']==t['schema'] and a['scope']==SCOPE
        and a['original_plan_sha256']==p.digest(plan) and a['original_expires_utc']==plan['expires_utc'],'Exact operations contract required')
    h=a['root_success'];prior=h['amendment'];g=h['grant']
    p.require(set(h)==set(t['root_success']) and prior['phase']==u.CONTINUE,'Exact successful public continuation required')
    u.shape(plan,prior);r.validate_grant(plan,g,u.CONTINUE,p.digest(prior))
    code=prior['execution_code']
    p.require(code['code_head']==BASE and code['code_tree']==TREE and h['code_materialization']==r.materialization(code)
        and cgit('rev-parse',BASE+'^{tree}').decode().strip()==TREE,'Confirmed upload source differs')
    p.require(set(a['execution_code']['code_pins'])>=set(code['code_pins'])|{'tools/p3_public_operations.py','tools/p3_public_operations_start.ps1','tools/p3_probe_launcher.py'},'Full current operations pins required')
    cgit('merge-base','--is-ancestor',BASE,a['execution_code']['code_head']);window(plan,a,False)

def cgit(*args):return u.c.git(p.ROOT,*args)

def root_history(plan,rows,a):
    p.require(len(rows)>=112,'Missing confirmed112 prefix')
    h=a['root_success'];prior=h['amendment'];g=h['grant'];u.history(plan,rows[:53],prior)
    tail=rows[53:112]
    events=['phase_start','authorization','public_root_review']+['request','response']*6+['public_preflight']+['request','response','public_writer_auth','public_push_prepare','request','public_push_response']+['request','response']*3+['readback']+['request','response']*6+['readback','history']+['request','response']*7+['public_preflight','phase_end']
    p.require([x['event'] for x in tail]==events and all(x['phase']==u.CONTINUE and x['run'] is None for x in tail),'Exact successful112 root events required')
    p.require(tail[0]['journal']==a['entry']['journal']==u.CONTINUE+'.jsonl' and tail[0]['predecessor']==rows[52]['hash']
        and tail[1]['grant_sha256']==p.digest(g) and tail[1]['review_sha256']==p.digest(prior)
        and tail[1]['grant_expires_utc']==g['expires_utc'] and tail[1]['expiry_policy']==plan['expiry_policy']
        and tail[2]['amendment_sha256']==p.digest(prior) and tail[2]['execution_code']==prior['execution_code'],'Root authority differs')
    hist=[x for x in tail if x['event']=='history'];end=tail[-1]
    p.require(len(hist)==1 and hist[0]['result']=='complete-blocked-root-confirmed' and hist[0]['commit']==u.SEED
        and hist[0]['body_sha256']==u.SEED_SHA and hist[0]['revision']==0 and hist[0]['revisions']==1 and hist[0]['independently_read_commits']==1
        and end['result']=='confirmed' and end['activation_allowed'] is False
        and end['counts']==end['bootstrap_case_counts']=={'GET':37,'PUT':0,'GIT_PUSH':1}
        and end['phase_counts']=={'GET':23,'PUT':0,'GIT_PUSH':1}
        and [x['result'] for x in tail if x['event']=='public_push_response']==['returned-success-not-yet-confirmed']
        and [x['result'] for x in tail if x['event']=='public_preflight']==['confirmed-public-empty','confirmed-public-original-root'], 'Root complete readback/settings/confirmation required')
    req=[x for x in tail if x['event']=='request'];resp=[x for x in tail if x['event']=='response']
    p.require(len(req)==24 and len(resp)==23 and [x['method'] for x in req]==['GET']*7+['GIT_PUSH']+['GET']*16,'Root request sequence differs')
    p.require(req[7]['commit']==u.SEED and req[7]['parents']==[] and req[7]['bytes']==1981,'Only original root Git consumed')
    expected=r.routes(plan)[:6]+[r.routes(plan)[0]]
    tree=u.c.git(Path(prior['root']['directory']),'rev-parse',u.SEED+'^{tree}').decode().strip();base=r.routes(plan)[0]
    ref=base+'/git/ref/heads/'+plan['branch'];content=base+'/contents/delivery/stream.json?ref='+u.SEED
    expected += [ref,content,ref,content,base+'/git/commits/'+u.SEED,base+'/git/trees/'+tree+'?recursive=1',ref,content,ref]+r.routes(plan)
    p.require([x['route'] for x in req if x['method']=='GET']==expected and [x['route'] for x in resp]==expected,'Root routes differ')
    for j,x in enumerate(resp):
        p.require(x['result']==('http-404' if j in (2,18,22) else 'http-200'),'Root response differs')
        if j in (2,18):p.require(x['diagnostic']['category']=='not-found','Root Pages404 unverified')
        if j==22:p.require(x['diagnostic']['category'] in ('not-found','branch-not-protected'),'Root protection response unverified')
    p.require(all(u.c.parse_utc(prior['not_before_utc'])<=u.c.parse_utc(x['utc'])<min(u.c.parse_utc(prior['expires_utc']),u.c.parse_utc(g['expires_utc'])) for x in tail),'Root not timely')
    e=a['entry'];p.require(e['rows']==112 and e['counts']==rows[111]['counts'] and e['frontier_hash']==rows[111]['hash'] and e['highwater']==rows[111]['utc'],'Wrong112 anchor')

def section_for(phase):return next(k for k,v in SECTIONS.items() if phase in v)

def eligible(plan,a,rows,phase,review=None):
    root_history(plan,rows,a)
    starts=[x for x in rows[112:] if x['event']=='phase_start']
    index=ORDER.index(phase)
    p.require([x['phase'] for x in starts]==ORDER[:index],'Wrong operations order/replay')
    p.require(not any(x['event']=='phase_halt' for x in rows[112:]),'Halted operations cannot resume')
    if index in (1,2,3,5):
        p.require(rows[-1]['event']=='phase_end' and rows[-1]['result']=='confirmed' and rows[-1]['phase']==ORDER[index-1],'Unconfirmed preceding phase')
    if index==0:p.require(len(rows)==112,'Activation only at original112')
    if index==4:
        p.require(rows[-1]['event']=='loss_boundary' and rows[-1]['phase']==INITIAL[-1] and isinstance(review,dict),'Takeover needs exact process-end review')
        p.validate_termination(plan,review,Path(plan['journal_directory'])/(INITIAL[-1]+'.jsonl'))
        p.require(review['termination']['exit_code']==23 and review['termination']['journal_name']==INITIAL[-1]+'.jsonl','Actual exited loss worker required')
        u.c.process_ended(review['termination']['pid'])
    for x in rows[112:]:
        if x['event']=='operations_review':p.require(x['amendment_sha256']==p.digest(a) and x['execution_code']==a['execution_code'],'Operations review/code changed')
        if x['event']=='response' and x['result']=='unknown':p.require(x['phase']=='public-store-lost-after' and x['bytes']>0,'Unclear write/read cannot be bypassed')
    indices=[j for j,x in enumerate(rows) if j>=112 and x['event']=='phase_start']
    for k,j in enumerate(indices):
        stop=indices[k+1] if k+1<len(indices) else len(rows)
        auth,record=rows[j+1:j+3]
        p.require(auth['event']=='authorization' and record['event']=='operations_review','Missing durable operations authorization')
        oldg=record['section_grant'];section=section_for(rows[j]['phase'])
        p.require(set(oldg)==set(grant_template(section)) and oldg['schema']=='p3-human-operations-section-v1'
            and oldg['section']==section and oldg['phases']==SECTIONS[section] and oldg['human_authorization'] is True
            and oldg['plan_sha256']==p.digest(plan) and oldg['amendment_sha256']==p.digest(a)
            and auth['grant_sha256']==record['grant_sha256']==p.digest(oldg)
            and auth['review_sha256']==oldg['review_sha256'] and auth['grant_expires_utc']==oldg['expires_utc']
            and all(u.c.parse_utc(a['not_before_utc'])<=u.c.parse_utc(x['utc'])<min(u.c.parse_utc(a['expires_utc']),u.c.parse_utc(oldg['expires_utc'])) for x in rows[j:stop]),
            'Historical operations section/grant/timeliness differs')

def latest(plan,a,phase,review=None):
    root=Path(plan['journal_directory']);db=sqlite3.connect((root/'probe-session.sqlite3').as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        p.require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Session integrity failure')
        state=db.execute('SELECT plan,journal,published,highwater FROM frontier').fetchone()
        rows=[json.loads(x[0]) for x in db.execute('SELECT body FROM events ORDER BY seq')]
    finally:db.close()
    p.require(state==(p.digest(plan),state[1],rows[-1]['hash'],max(x['utc'] for x in rows))
        and p.Ledger.verify(root/state[1],p.digest(plan))==rows,'Authoritative latest frontier required')
    p.require(not any((root/n).exists() for n in ('probe-session.sqlite3-wal','probe-session.sqlite3-journal')),'Unresolved publication')
    starts=[j for j,x in enumerate(rows) if x['event']=='phase_start']
    p.require({x.name for x in root.glob('attempt-*.json')}=={'attempt-'+rows[j]['phase']+'.json' for j in starts},'Unpublished/extra marker')
    for k,j in enumerate(starts):
        stop=starts[k+1] if k+1<len(starts) else len(rows)
        p.require((root/rows[j]['journal']).read_bytes()==''.join(p.canonical(x)+'\n' for x in rows[:stop]).encode(),'Changed cumulative prefix')
        p.require(read(root/('attempt-'+rows[j]['phase']+'.json'))=={q:rows[j][q] for q in ('plan_sha256','phase','journal','pid','predecessor')},'Marker mismatch')
    eligible(plan,a,rows,phase,review)
    return state,rows

def validate_locked(l,rows,state,a,review):
    eligible(l.p,a,rows,l.phase,review)
    p.require(l.path.name==l.phase+'.jsonl' and state[2]==rows[-1]['hash'],'Fixed latest operations journal')
    if l.phase==INITIAL[0]:
        for name,value in a['entry']['files_sha256'].items():
            if name=='probe-session.lock':l.lock_handle.seek(0);actual=hashlib.sha256(l.lock_handle.read()).hexdigest();l.lock_handle.seek(0)
            else:actual=u.c.sha(l.path.parent/name)
            p.require(actual==value,'Changed entry file')

class OperationsGuard(p.GrantGuard):
    def __init__(self,plan,g,a,phase):self.a=deepcopy(a);self.a_hash=p.digest(a);super().__init__(plan,g,phase)
    def validate_binding(self):
        g=self.grant
        p.require(set(g)==set(grant_template(g['section'])) and g['schema']=='p3-human-operations-section-v1'
            and g['plan_sha256']==self.plan_hash and g['amendment_sha256']==self.a_hash
            and g['phases']==SECTIONS[g['section']] and self.phase in g['phases'] and g['human_authorization'] is True
            and isinstance(g['approved_by'],str) and g['approved_by'] and re.fullmatch('[0-9a-f]{64}',g['approval_evidence_sha256'] or ''),'Bound human section grant required')
    def deadlines(self):return [window(self.p,self.a)[1],u.c.parse_utc(self.grant['expires_utc'])]
    def check(self,ledger=None):
        super().check(ledger)
        p.require(p.digest(self.a)==self.a_hash and self.a['scope']==SCOPE,'Operations contract changed')
        if ledger:p.require(ledger.operations_hash==self.a_hash and ledger.counts['GIT_PUSH']==1,'Bound operations review/Git budget differs')
    def validate_route(self,method,route):
        base=r.routes(self.p)[0];branch=self.p['branch']
        if method=='PUT':p.require(self.phase!='public-store-inspect' and route==base+'/contents/delivery/stream.json','Inspection/foreign PUT');return
        p.require(method=='GET' and (route in r.routes(self.p) or route==base+'/git/ref/heads/'+branch
            or re.fullmatch(re.escape(base)+r'/contents/delivery/stream\.json\?ref=[0-9a-f]{40}',route)
            or re.fullmatch(re.escape(base)+r'/git/commits/[0-9a-f]{40}',route)
            or re.fullmatch(re.escape(base)+r'/git/trees/[0-9a-f]{40}\?recursive=1',route)
            or re.fullmatch(re.escape(base)+r'/compare/[0-9a-f]{40}\.\.\.[0-9a-f]{40}\?per_page=1',route)),'Unapproved operations route')

class OperationsBoundary(u.PublicBoundary):
    def preflight(self,empty=False):
        p.require(not empty,'No root bootstrap/empty repo operations')
        fixed=r.routes(self.p);self.identity(self.request('GET',fixed[0]))
        u.ensure(self.request('GET',fixed[1]).get('enabled') is False,'public-actions-enabled')
        try:self.request('GET',fixed[2])
        except p.HTTPStatus as exc:u.ensure(exc.status==404,'public-pages-unavailable')
        else:raise u.PublicHalt('public-pages-present')
        u.ensure(self.request('GET',fixed[3])==[] and self.request('GET',fixed[4])==[],'public-rules-or-rulesets-not-empty')
        branches=self.request('GET',fixed[5]);u.ensure(isinstance(branches,list) and len(branches)==1 and branches[0].get('name')==self.p['branch']
            and branches[0].get('protected') is False and re.fullmatch('[0-9a-f]{40}',branches[0].get('commit',{}).get('sha','')),'public-branches-or-protection-mismatch')
        self.public_protection_checked=True
        try:
            try:self.request('GET',fixed[6])
            except p.HTTPStatus as exc:u.ensure(exc.status==404,'public-protection-unavailable')
            else:raise u.PublicHalt('public-protection-present')
        finally:self.public_protection_checked=False
        self.allowed=True;self.ledger.emit('preflight',result='confirmed-public-existing-synthetic-store')

def authorize(plan,a,g,section,approved,review):
    shape(plan,a);window(plan,a);r.verify_execution_code(a['execution_code'])
    p.require(p.digest(a)==approved and g['section']==section and u.c.parse_utc(g['expires_utc'])<=u.c.parse_utc(a['expires_utc']),'Section/amendment/deadline mismatch')
    guard=OperationsGuard(plan,g,a,SECTIONS[section][0]);state,rows=latest(plan,a,guard.phase,review)
    u.c.root_matches(a['root_success']['amendment']);u.c.verify_root(plan,a['root_success']['amendment']['root']['directory'])
    p.require(g['entry_journal']==state[1] and g['entry_frontier_hash']==state[2] and g['entry_rows']==len(rows)
        and set(g['entry_files_sha256'])==r.session_files(rows),'Grant must bind actual latest entry')
    for name,value in g['entry_files_sha256'].items():p.require(u.c.sha(Path(plan['journal_directory'])/name)==value,'Grant entry bytes changed')
    p.require(g['review_sha256']==(p.digest(review) if section=='takeover' else p.digest(a)),'Separate takeover review grant required')
    if section=='initial':
        e=a['review'];p.require(set(e)==set(template()['review']) and e['original_pid']==rows[53]['pid'] and e['end_basis']==r.END_BASIS
            and all(e[k] is True for k in ('human_review','terminal_code_path_checked','human_terminal_end_report','all_workers_ended','triggers_paused'))
            and re.fullmatch('[0-9a-f]{64}',e['evidence_sha256'] or '') and u.c.parse_utc(rows[111]['utc'])<=u.c.parse_utc(e['observed_utc'])<=p.datetime.now(p.timezone.utc),'Fresh root process-end/Freeze review')
        u.c.process_ended(e['original_pid'])
    return guard

def run_phase(plan,a,g,phase,reader,writer,review):
    state,rows=latest(plan,a,phase,review);guard=OperationsGuard(plan,g,a,phase)
    l=p.Ledger(plan,Path(plan['journal_directory'])/(phase+'.jsonl'),phase,Path(plan['journal_directory'])/state[1],
        reviewed_termination=review if phase=='public-store-takeover' else None,operations_amendment=a)
    try:
        b=OperationsBoundary(plan,l,reader,writer,guard=guard);client=p.Client(b)
        l.emit('operations_review',amendment_sha256=p.digest(a),grant_sha256=p.digest(g),execution_code=a['execution_code'],section=g['section'],section_grant=g)
        b.preflight();p.verify_history(client)
        native=p.OPS_PHASES[phase]
        if native=='activate':p.activation(client)
        elif native=='takeover':p.takeover(client,review)
        elif native!='inspect':p.sequence(client,native)
        l.emit('phase_end',result='confirmed',scope=SCOPE)
    except SystemExit as exc:
        if phase==INITIAL[-1] and exc.code==23:raise
        if not l.poisoned:l.emit('phase_halt',result='incomplete-no-retry-no-release');raise
    except BaseException as exc:
        category=exc.category if isinstance(exc,u.PublicHalt) else 'operations-http-'+str(exc.status) if isinstance(exc,p.HTTPStatus) else 'operations-local-or-expired'
        if not l.poisoned:l.emit('phase_halt',result='incomplete-no-retry-no-release',category=category)
        print('HALT: '+category+'. Kein Retry. Ergebnis: '+str(l.path));raise
    finally:l.close()

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--template');cli.add_argument('--real',action='store_true');cli.add_argument('--worker',action='store_true')
    cli.add_argument('--section',choices=SECTIONS,default='initial')
    for key in ('plan','amendment','grant','approved-amendment-sha256','termination-review','receipt'):cli.add_argument('--'+key)
    args=cli.parse_args()
    if args.template:
        p.require(not args.real,'Offline template only')
        with Path(args.template).open('x',encoding='utf-8') as f:json.dump(template(),f,indent=2)
        return 0
    p.require(args.real and all((args.plan,args.amendment,args.grant,args.approved_amendment_sha256)),'Default offline; complete section grant required')
    plan,a,g=[read(x) for x in (args.plan,args.amendment,args.grant)];review=read(args.termination_review) if args.termination_review else None
    guard=authorize(plan,a,g,args.section,args.approved_amendment_sha256,review)
    if args.section=='initial' and not args.worker:
        p.require(args.receipt and not Path(args.receipt).exists(),'New actual parent receipt path required')
        command=[sys.executable,'-B',str(p.ROOT/'tools/p3_public_operations.py'),*sys.argv[1:],'--worker']
        process=subprocess.Popen(command)
        try:code=process.wait(timeout=1200)
        except subprocess.TimeoutExpired:
            print('HALT: parent-wait-timeout. PID '+str(process.pid)+' nicht als beendet belegt; keine Quittung, kein Retry.');return 2
        if code==3:print('Eingabe abgebrochen: kein neuer Versuch.');return 3
        if code!=23:print('HALT: initial-section-not-complete. Kein Takeover.');return 2
        journal=Path(plan['journal_directory'])/(INITIAL[-1]+'.jsonl')
        receipt=launcher.observe_exit(process,plan,journal,expected_phase=INITIAL[-1])
        with Path(args.receipt).open('x',encoding='utf-8') as f:f.write(p.canonical(receipt)+'\n');f.flush();os.fsync(f.fileno())
        print('STOPP: echtes Prozessende belegt. Owner/Commit/Revision im Hauptchat pruefen; eigener Takeover-Grant erforderlich.');return 0
    try:
        reader=p.read_token('Reader');writer='' if args.section=='inspect' else p.read_token('Writer')
    except (KeyboardInterrupt,ValueError):print('Eingabe abgebrochen/ungueltig vor Phasenstart.');return 3
    guard.check();authorize(plan,a,g,args.section,args.approved_amendment_sha256,review)
    for phase in SECTIONS[args.section]:run_phase(plan,a,g,phase,reader,writer,review)
    print('Nur freigegebener Abschnitt bestaetigt. Keine weitere Phase/Aktivierung/P4.');return 0
