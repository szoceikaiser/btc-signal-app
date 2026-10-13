"""One separately reviewed GET-only reconciliation of the exact happy HALT."""
import sys
if __name__=='__main__':
    from p3_happy_readback import main
    try:sys.exit(main())
    except Exception as exc:
        category=getattr(exc,'category','happy-readback-binding-grant-or-publication')
        print('HALT: '+category+'. Kein Retry; kein Write.',file=sys.stderr);sys.exit(2)

import argparse,base64,hashlib,json,re,sqlite3
from copy import deepcopy
from pathlib import Path
import p3_public_operations as o
p=o.p;r=o.r;c=o.u.c
PHASE=p.HAPPY_READ_PHASE
BASE='73cde7c30096c20eb519ead4a7cc4a3b6f49eaeb';TREE='87c4a2c96ac1a3b776e3fce65df6f36ae9bdb799'
OLD='6ac4dfe933defaff0c58ca7cc9998e90e6387be0';BLOB='cd1d663d8589f1be2e71522cc9abe64ecfb99ae3'
WRITE='5e1320a386794f5ec92c3c9d3983e7f1';PARENT='49955b2e4d4b32c8131320f6d671e7f193a12af0c5c228f9e7470b3541444626'
SCOPE='only-exact375-happy-halt-reader-13GET-no-recovery'

def read(path):return o.read(path)
def need(ok,category):
    if not ok:raise o.u.PublicHalt(category)

def template():
    return {'schema':'p3-happy-readback-v1','phase':PHASE,'scope':SCOPE,
        'original_plan_sha256':None,'original_expires_utc':None,
        'operations':None,'initial_grant':None,'historical_code_materialization':None,
        'entry':{'journal':'public-store-happy.jsonl','rows':375,'frontier_hash':None,'highwater':None,
                 'counts':{'GET':134,'PUT':11,'GIT_PUSH':1},'files_sha256':None},
        'execution_code':{'code_head':None,'code_tree':None,'code_pins':None},
        'review':deepcopy(o.template()['review']),'not_before_utc':None,'expires_utc':None}

def grant_template():
    return {'schema':'p3-human-happy-readback-v1','phase':PHASE,'plan_sha256':None,
        'review_sha256':None,'human_authorization':False,'approved_by':None,
        'approval_evidence_sha256':None,'expires_utc':None}

def window(plan,a,current=True):
    start,end=c.parse_utc(a['not_before_utc']),c.parse_utc(a['expires_utc'])
    need(c.parse_utc(a['entry']['highwater'])<=start<end and end-start<=p.timedelta(hours=20),'happy-readback-window')
    if current:need(start<=p.datetime.now(p.timezone.utc)<end,'happy-readback-expired-or-not-started')
    return start,end

def shape(plan,a):
    p.validate_plan_structure(plan);t=template()
    need(set(a)==set(t) and all(a[k]==t[k] for k in ('schema','phase','scope'))
        and a['original_plan_sha256']==p.digest(plan) and a['original_expires_utc']==plan['expires_utc'], 'happy-readback-original-contract')
    need((plan['repo'],plan['repository_id'],plan['branch'],plan['path'],plan['seed_commit'])==
        (o.u.REPO,o.u.RID,'p3-synthetic-only','delivery/stream.json',o.u.SEED),'happy-readback-target')
    old=a['operations'];o.shape(plan,old)
    need(old['execution_code']['code_head']==BASE and old['execution_code']['code_tree']==TREE
        and a['historical_code_materialization']==r.materialization(old['execution_code']), 'happy-readback-historical-code')
    need(set(a['execution_code']['code_pins'])>=set(old['execution_code']['code_pins'])|
        {'tools/p3_happy_readback.py','tools/p3_happy_readback_start.ps1'},'happy-readback-current-pins')
    c.git(p.ROOT,'merge-base','--is-ancestor',BASE,a['execution_code']['code_head'])
    need(set(a['entry'])==set(t['entry']) and a['entry']['journal']==t['entry']['journal']
        and a['entry']['rows']==375 and a['entry']['counts']==t['entry']['counts'],'happy-readback375-entry')
    window(plan,a,False)

def history(plan,rows,a):
    """Trusted old-code readback/parent evidence, never HTTP200 alone."""
    e=a['entry'];old=a['operations'];g=a['initial_grant']
    need(len(rows)==375 and rows[-1]['hash']==e['frontier_hash'] and rows[-1]['utc']==e['highwater']
        and rows[-1]['counts']==e['counts'],'happy-readback375-frontier')
    o.eligible(plan,old,rows[:112],'public-store-activate')
    o.eligible(plan,old,rows[:180],'public-store-happy')
    need(rows[180]['event']=='phase_start' and rows[180]['phase']=='public-store-happy'
        and rows[180]['journal']=='public-store-happy.jsonl'
        and all(x['phase']=='public-store-happy' for x in rows[180:]),'happy-readback-exact-phase')
    for j in (112,180):
        auth,review=rows[j+1:j+3]
        need(auth['event']=='authorization' and review['event']=='operations_review'
            and review['section_grant']==g and review['execution_code']==old['execution_code']
            and review['amendment_sha256']==p.digest(old)
            and auth['grant_sha256']==review['grant_sha256']==p.digest(g)
            and auth['review_sha256']==g['review_sha256']==p.digest(old)
            and auth['grant_expires_utc']==g['expires_utc'],'happy-readback-historical-grant')
    need(set(g)==set(o.grant_template()) and g['schema']=='p3-human-operations-section-v1'
        and g['section']=='initial' and g['phases']==o.INITIAL and g['human_authorization'] is True
        and g['plan_sha256']==p.digest(plan) and g['amendment_sha256']==p.digest(old)
        and all(c.parse_utc(old['not_before_utc'])<=c.parse_utc(x['utc'])<min(c.parse_utc(old['expires_utc']),c.parse_utc(g['expires_utc'])) for x in rows[112:]),'happy-readback-old-authority-time')
    need([x['phase'] for x in rows[112:] if x['event']=='phase_start']==o.INITIAL[:2]
        and sum(x['event']=='phase_halt' for x in rows[112:])==1
        and not any(x['event']=='response' and x['result'] in ('unknown','invalid-or-overbudget') for x in rows[112:])
        and [x['event'] for x in rows[366:]]==['request','response','request','response','request','response','request','response','phase_halt'], 'happy-readback-exact-halt-tail')
    q=rows[366]
    need(q['method']=='PUT' and q['revision']==10 and q['write_id']==WRITE and q['bytes']==5758
        and q['old_blob']==BLOB and q['parent_digest']==PARENT and q['run']==p.owner(plan,2)
        and rows[367]['result']=='http-200' and all(rows[j]['result']=='http-200' for j in (369,371,373))
        and rows[374]['result']=='incomplete-no-retry-no-release'
        and rows[374]['category']=='operations-local-or-expired','happy-readback-exact-last-attempt')
    base=r.routes(plan)[0];ref=base+'/git/ref/heads/'+plan['branch']
    need([rows[j]['route'] for j in (366,368,370,372)]==[base+'/contents/delivery/stream.json',ref,
        base+'/contents/delivery/stream.json?ref='+OLD,ref],'happy-readback-last-routes')
    # Every request, including the failed contender, is retained and counted.
    counts={m:sum(x['event']=='request' and x.get('method')==m for x in rows) for m in p.LIMITS if m in ('GET','PUT','GIT_PUSH')}
    need(counts==e['counts'],'happy-readback-counters')
    chain=[{'revision':0,'commit':o.u.SEED,'blob':p.hashlib.sha1(b'blob 1981\0'+p.synthetic_seed(plan)).hexdigest(),
            'body_digest':json.loads(p.synthetic_seed(plan))['body_digest']}]
    puts=[j for j,x in enumerate(rows) if x['event']=='request' and x.get('method')=='PUT']
    need(len(puts)==11 and puts[-1]==366,'happy-readback-write-attempts')
    conflicts=0
    for index,j in enumerate(puts[:-1]):
        req=rows[j];response=rows[j+1]
        need(response['event']=='response' and all(response[k]==req[k] for k in ('write_id','old_blob','revision','bytes','parent_digest','route','run')),'happy-readback-write-response-binding')
        if response['result']=='http-409':
            conflicts+=1
            need(req['run']==p.owner(plan,2) and req['revision']==2 and req['old_blob']==chain[1]['blob'], 'happy-readback-exact-stale-contender')
            continue
        prev=chain[-1];next_put=next(rows[k] for k in puts[index+1:] if rows[k]['revision']==req['revision']+1)
        need(response['result']=='http-200' and req['revision']==prev['revision']+1
            and req['old_blob']==prev['blob'] and req['parent_digest']==prev['body_digest'],'happy-readback-linear-write-digests')
        end=puts[index+1];segment=rows[j+2:end]
        # The pinned old _write requires its exact body, revision, readback and
        # single parent; these emitted observations are explicitly re-bound.
        pairs=[(k,x) for k,x in enumerate(segment) if x['event']=='parent']
        need(len(pairs)==1,'happy-readback-parent-gap')
        k,parent=pairs[0];observed=segment[k-3]
        need(k>=3 and observed['event']=='readback' and observed['revision']==req['revision']
            and observed['bytes']==req['bytes'] and parent['commit']==observed['commit']
            and parent['parents']==[prev['commit']] and observed['run']==req['run']==parent['run']
            and segment[k-2]['event']=='request' and segment[k-2]['method']=='GET'
            and segment[k-2]['route']==base+'/git/commits/'+parent['commit']
            and segment[k-1]['event']=='response' and segment[k-1]['result']=='http-200', 'happy-readback-parent-readback-gap')
        chain.append({'revision':req['revision'],'commit':parent['commit'],'blob':observed['old_blob'],
            'bytes':req['bytes'],'write_id':req['write_id'],'parent':prev['commit'],
            'parent_digest':req['parent_digest'],'body_digest':next_put['parent_digest']})
    need(conflicts==1 and len(chain)==10 and chain[-1]['commit']==OLD and chain[-1]['blob']==BLOB
        and chain[-1]['bytes']==5626 and chain[-1]['body_digest']==PARENT,'happy-readback-confirmed9-anchor')
    anchors=[x for x in rows if x['event']=='history' and x.get('revision')==1]
    need(len(anchors)==1 and anchors[0]['commit']==chain[1]['commit'] and anchors[0]['verified_anchor']==o.u.SEED
        and anchors[0]['independently_read_commits']==2,'happy-readback-root-history-anchor')
    activated=[x for x in rows[112:180] if x['event']=='activation']
    need(len(activated)==1 and activated[0]['result']=='confirmed-synthetic-only'
        and activated[0]['commit_sha']==chain[1]['commit'] and activated[0]['blob_sha']==chain[1]['blob']
        and activated[0]['snapshot_digest']==chain[1]['body_digest'],'happy-readback-activation-anchor')
    complete=[x for x in rows[180:] if x['event']=='run_completion']
    need(len(complete)==1 and complete[0]['run']==p.owner(plan,1)
        and complete[0]['binding']['completion']['commit_sha']==chain[7]['commit']
        and complete[0]['binding']['completion']['snapshot_digest']==chain[7]['body_digest'], 'happy-readback-first-run-binding')
    return chain

def verify_state(plan,a,ledger=None):
    root=Path(plan['journal_directory']);e=a['entry']
    rows=p.Ledger.verify(root/e['journal'],p.digest(plan));chain=history(plan,rows,a)
    need(set(e['files_sha256'])==r.session_files(rows),'happy-readback-fileset')
    for name,sha in e['files_sha256'].items():
        if ledger and name=='probe-session.lock':ledger.lock_handle.seek(0);actual=hashlib.sha256(ledger.lock_handle.read()).hexdigest();ledger.lock_handle.seek(0)
        else:actual=c.sha(root/name)
        need(actual==sha,'happy-readback-file-changed')
    db=ledger.db if ledger else sqlite3.connect((root/'probe-session.sqlite3').as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        need(db.execute('PRAGMA integrity_check').fetchone()==('ok',)
            and [json.loads(x[0]) for x in db.execute('SELECT body FROM events ORDER BY seq')]==rows
            and db.execute('SELECT plan,journal,published,highwater FROM frontier').fetchone()==(p.digest(plan),e['journal'],e['frontier_hash'],e['highwater']), 'happy-readback-central-frontier')
    finally:
        if not ledger:db.close()
    starts=[j for j,x in enumerate(rows) if x['event']=='phase_start']
    need({x.name for x in root.glob('attempt-*.json')}=={'attempt-'+rows[j]['phase']+'.json' for j in starts},'happy-readback-markers')
    for k,j in enumerate(starts):
        stop=starts[k+1] if k+1<len(starts) else len(rows)
        need((root/rows[j]['journal']).read_bytes()==''.join(p.canonical(x)+'\n' for x in rows[:stop]).encode()
            and read(root/('attempt-'+rows[j]['phase']+'.json'))=={v:rows[j][v] for v in ('plan_sha256','phase','journal','pid','predecessor')},'happy-readback-prefix-or-marker')
    need(not any((root/name).exists() for name in ('probe-session.sqlite3-wal','probe-session.sqlite3-journal',PHASE+'.jsonl','attempt-'+PHASE+'.json')),'happy-readback-publication-or-replay')
    review=a['review']
    need(set(review)==set(template()['review']) and review['end_basis']==r.END_BASIS
        and review['original_pid']==rows[180]['pid'] and isinstance(review['reviewer'],str) and review['reviewer']
        and re.fullmatch('[0-9a-f]{64}',review['evidence_sha256'] or '')
        and all(review[k] is True for k in ('human_review','terminal_code_path_checked','human_terminal_end_report','all_workers_ended','triggers_paused'))
        and c.parse_utc(rows[-1]['utc'])<=c.parse_utc(review['observed_utc'])<=p.datetime.now(p.timezone.utc),'happy-readback-positive-end-freeze')
    c.process_ended(review['original_pid']);c.root_matches(a['operations']['root_success']['amendment'])
    c.verify_root(plan,a['operations']['root_success']['amendment']['root']['directory'])
    return rows,chain

def validate_locked(l,rows,state,a):
    need(l.phase==PHASE and l.path.name==PHASE+'.jsonl' and state[2]==a['entry']['frontier_hash']
        and rows==verify_state(l.p,a,l)[0],'happy-readback-locked-entry')

class HappyReadGuard(p.GrantGuard):
    def __init__(self,plan,g,a):self.a=deepcopy(a);self.a_hash=p.digest(a);super().__init__(plan,g,PHASE)
    def validate_binding(self):
        g=self.grant
        need(set(g)==set(grant_template()) and g['schema']=='p3-human-happy-readback-v1' and g['phase']==PHASE
            and g['plan_sha256']==self.plan_hash and g['review_sha256']==self.a_hash
            and g['human_authorization'] is True and isinstance(g['approved_by'],str) and g['approved_by']
            and re.fullmatch('[0-9a-f]{64}',g['approval_evidence_sha256'] or ''),'happy-readback-human-grant')
    def deadlines(self):return [window(self.p,self.a)[1],c.parse_utc(self.grant['expires_utc'])]
    def check(self,ledger=None):
        super().check(ledger);need(p.digest(self.a)==self.a_hash,'happy-readback-live-contract')
        if ledger:need(ledger.happy_readback_hash==self.a_hash and ledger.counts['PUT']==11 and ledger.counts['GIT_PUSH']==1,'happy-readback-live-scope')
    def validate_route(self,method,route):
        base=r.routes(self.p)[0]
        need(method=='GET' and (route in r.routes(self.p) or route==base+'/git/ref/heads/'+self.p['branch']
            or re.fullmatch(re.escape(base)+r'/contents/delivery/stream\.json\?ref=[0-9a-f]{40}',route)
            or re.fullmatch(re.escape(base)+r'/git/commits/[0-9a-f]{40}',route)
            or re.fullmatch(re.escape(base)+r'/git/trees/[0-9a-f]{40}\?recursive=1',route)), 'happy-readback-route')

class HappyReadBoundary(o.OperationsBoundary):
    """Settings inherit the proven context-bound public checks; no Writer."""
    def __init__(self,plan,l,reader,guard):super().__init__(plan,l,reader,'',guard=guard)

def authorize(plan,a,g,approved):
    shape(plan,a);window(plan,a);r.verify_execution_code(a['execution_code'])
    need(p.digest(a)==approved and c.parse_utc(g['expires_utc'])<=c.parse_utc(a['expires_utc']),'happy-readback-independent-hash-deadline')
    guard=HappyReadGuard(plan,g,a);verify_state(plan,a);return guard

def ref(b):
    value=b.request('GET',b.base+'/git/ref/heads/'+b.p['branch'])
    need(isinstance(value,dict) and value.get('ref')=='refs/heads/'+b.p['branch'] and value.get('object',{}).get('type')=='commit'
        and re.fullmatch('[0-9a-f]{40}',value['object'].get('sha','')),'happy-readback-invalid-ref')
    sha=value['object']['sha'];b.ledger.emit('happy_head',commit=sha,result='observed-only');return sha

def content(b,sha):
    item=b.request('GET',b.base+'/contents/delivery/stream.json?ref='+sha)
    need(isinstance(item,dict) and item.get('type')=='file' and item.get('path')==b.p['path']
        and item.get('encoding')=='base64','happy-readback-content-shape')
    try:body=base64.b64decode(''.join(item['content'].split()),validate=True)
    except (KeyError,ValueError,TypeError):raise o.u.PublicHalt('happy-readback-content-encoding') from None
    blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
    need(len(body)<=p.LIMITS['store_bytes'] and item.get('sha')==blob and item.get('size')==len(body),'happy-readback-blob-or-size')
    env=p.check_identity(b.p,body);need(body==p.canonical(env).encode(),'happy-readback-noncanonical-body')
    b.ledger.emit('happy_content',commit=sha,old_blob=blob,bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest(),
        revision=env['revision'],write_id=env['write_id'],parent_digest=env['parent_digest'],body_digest=env['body_digest'],result='observed-only')
    return body,env,blob

def reconcile(b,chain):
    head=ref(b);body,env,blob=content(b,head);after=ref(b)
    need(head==after,'happy-readback-unstable-head')
    oldbody,oldenv,oldblob=content(b,OLD);anchor=chain[-1]
    need(oldblob==BLOB and len(oldbody)==5626 and oldenv['revision']==9 and oldenv['write_id']==anchor['write_id']
        and oldenv['parent_digest']==anchor['parent_digest'] and oldenv['body_digest']==PARENT
        and oldenv['snapshot']['control']['owner'] is None,'happy-readback-old-anchor-body')
    expected=deepcopy(oldenv);expected['snapshot']['control']['owner']=p.owner(b.p,2)
    expected.update(revision=10,write_id=WRITE,parent_digest=PARENT,body_digest=p.digest(expected['snapshot']))
    expectedbody=p.canonical(expected).encode();need(len(expectedbody)==5758,'happy-readback-expected-byte-count')
    commit=b.request('GET',b.base+'/git/commits/'+head)
    need(isinstance(commit,dict) and commit.get('sha')==head and isinstance(commit.get('parents'),list)
        and re.fullmatch('[0-9a-f]{40}',commit.get('tree',{}).get('sha','')),'happy-readback-commit-shape')
    parents=[x.get('sha') for x in commit['parents']];tree_sha=commit['tree']['sha']
    b.ledger.emit('happy_parent',commit=head,parents=parents,tree=tree_sha,result='observed-only')
    tree=b.request('GET',b.base+'/git/trees/'+tree_sha+'?recursive=1')
    need(isinstance(tree,dict) and tree.get('sha')==tree_sha and tree.get('truncated') is False
        and isinstance(tree.get('tree'),list),'happy-readback-tree-shape')
    files=tree['tree']
    need(len(files)==2 and {x.get('path') for x in files}=={'delivery','delivery/stream.json'}
        and next(x for x in files if x['path']=='delivery')['type']=='tree'
        and next(x for x in files if x['path']=='delivery')['mode']=='040000'
        and [(x['path'],x.get('type'),x.get('mode'),x.get('sha')) for x in files if x['path']!='delivery']==[(b.p['path'],'blob','100644',blob)],'happy-readback-tree-mismatch')
    if body==expectedbody:
        need(head!=OLD and parents==[OLD] and env==expected,'happy-readback-own-parent-mismatch')
        result='own-claim-exact-present-no-recovery'
    elif head==OLD and body==oldbody:
        need(parents==[anchor['parent']],'happy-readback-old-parent-mismatch')
        result='old-confirmed-only-write-outcome-still-unresolved'
    else:raise o.u.PublicHalt('happy-readback-foreign-or-different-state')
    b.guard.check(b.ledger)
    b.ledger.emit('happy_reconciliation',result=result,commit=head,parents=parents,tree=tree_sha,old_blob=blob,
        revision=env['revision'],bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest(),write_id=env['write_id'],
        owner=env['snapshot']['control']['owner'],root=o.u.SEED,verified_journal_commits=len(chain),recovery_authorized=False)
    return result

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--real',action='store_true');cli.add_argument('--template')
    for key in ('plan','amendment','grant','approved-amendment-sha256'):cli.add_argument('--'+key)
    args=cli.parse_args()
    if args.template:
        p.require(not args.real,'Offline template only')
        with Path(args.template).open('x',encoding='utf-8') as f:json.dump(template(),f,indent=2)
        return 0
    need(args.real and all((args.plan,args.amendment,args.grant,args.approved_amendment_sha256)),'happy-readback-default-offline')
    plan,a,g=[read(x) for x in (args.plan,args.amendment,args.grant)]
    guard=authorize(plan,a,g,args.approved_amendment_sha256)
    try:reader=p.read_token('Reader')
    except (KeyboardInterrupt,ValueError):print('Eingabe abgebrochen vor Sessionstart; kein Versuch.');return 3
    guard.check();authorize(plan,a,g,args.approved_amendment_sha256)
    l=p.Ledger(plan,Path(plan['journal_directory'])/(PHASE+'.jsonl'),PHASE,
        Path(plan['journal_directory'])/a['entry']['journal'],happy_readback_amendment=a)
    try:
        b=HappyReadBoundary(plan,l,reader,guard)
        l.emit('happy_readback_review',amendment_sha256=p.digest(a),execution_code=a['execution_code'],grant=g)
        b.preflight();result=reconcile(b,history(plan,l.prior_rows,a))
        l.emit('phase_end',result='read-only-complete-recovery-forbidden',outcome=result,recovery_authorized=False)
        print('Abgleich: '+result+'. STOPP fuer Hauptchat. Keine Wiederholung/Recovery.');return 0
    except BaseException as exc:
        category=exc.category if isinstance(exc,o.u.PublicHalt) else 'happy-readback-http-'+str(exc.status) if isinstance(exc,p.HTTPStatus) else 'happy-readback-local-invalid-or-expired'
        if not l.poisoned:l.emit('phase_halt',result='read-only-incomplete-no-recovery',category=category)
        print('HALT: '+category+'. Kein Retry/Write.');return 2
    finally:l.close()
