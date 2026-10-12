"""Exactly one separately approved public synthetic root upload; default offline."""
import sys
if __name__ == '__main__':
    from p3_public_root import main
    try:sys.exit(main())
    except Exception:
        print('HALT: Public-Root-Bindung, Freigabe oder Abschluss fehlt. Nicht erneut starten.',file=sys.stderr);sys.exit(2)

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import urllib.parse
import p3_github_probe as p
import p3_rules403 as r
import p3_reader401_continue as c

PHASE=p.PUBLIC_ROOT
REPO='szoceikaiser/btc-p3-store-probe';RID=1414013858
SEED='c78a4d1283aabdf187a65f628bd2882277b168e7'
SEED_SHA='0bb72c1a5fb9d6e77cd5579a6083c5cf6033e502c9c2b001cc3719079c56f53a'
BASE='648e7eda497433c1d1810f98a3de917defb76a07';TREE='5b6db7504f5fef109406955b900a6a4f079f52f3'
SCOPE='public-synthetic-original-blocked-root-only-no-activation'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def template():
    return {'schema':'p3-public-root-amendment-v1','phase':PHASE,'scope':SCOPE,
        'original_plan_sha256':None,'original_expires_utc':None,'root':{'directory':None,'files_sha256':None},
        'history':{'inspection':None,'grant':None,'operator_script':{'path':None,'sha256':None},'code_materialization':None},
        'visibility':{'acceptance_path':None,'files_sha256':None},
        'execution_code':{'code_head':None,'code_tree':None,'code_pins':None},
        'predecessor':{'journal':'inspect.jsonl','frontier_hash':None,'frontier_rows':35,'highwater':None,
            'counts':{'GET':7,'PUT':0,'GIT_PUSH':0},'files_sha256':None},
        'review':deepcopy(r.template(r.RESUME)['review']),
        'not_before_utc':None,'expires_utc':None,'time_authorization_sha256':None}

def window(plan,a,current=True):
    start,end=c.parse_utc(a['not_before_utc']),c.parse_utc(a['expires_utc'])
    p.require(c.parse_utc(plan['expires_utc'])<=start<end and end-start<=p.timedelta(hours=20)
        and a['time_authorization_sha256']==a['review']['evidence_sha256']
        and re.fullmatch('[0-9a-f]{64}',a['time_authorization_sha256'] or ''),'Bound public window max20h required')
    if current:p.require(start<=p.datetime.now(p.timezone.utc)<end,'Public window not started or expired')
    return start,end

def shape(plan,a):
    p.validate_plan_structure(plan);t=template()
    p.require(set(a)==set(t) and a['schema']==t['schema'] and a['phase']==PHASE and a['scope']==SCOPE
        and a['original_plan_sha256']==p.digest(plan) and a['original_expires_utc']==plan['expires_utc'], 'Exact public scope required')
    for k in ('root','history','visibility','execution_code','predecessor','review'):
        p.require(isinstance(a[k],dict) and set(a[k])==set(t[k]),'Incomplete public binding')
    p.require((plan['repo'],plan['repository_id'],plan['branch'],plan['path'],plan['seed_commit'],plan['seed_sha256'])
        ==(REPO,RID,'p3-synthetic-only','delivery/stream.json',SEED,SEED_SHA),'Only exact public synthetic root target')
    h=a['history'];i=h['inspection'];parent=i['parent_amendment']
    p.require(a['root']==i['root']==parent['root'],'Original root changed')
    r.validate_shape(plan,parent);r.verify_historical_code(plan,parent)
    r.validate_grant(plan,i['parent_grant'],r.RESUME,p.digest(parent))
    code=i['execution_code']
    p.require(code==parent['execution_code'] and code['code_head']==BASE and code['code_tree']==TREE
        and set(code['code_pins'])>=set(plan['code_pins'])|set(c.git(p.ROOT,'diff','--name-only',c.ORIGINAL_HEAD,BASE).decode().splitlines())
        and h['code_materialization']==r.materialization(code),'Complete historical648 code required')
    p.require(set(h['operator_script'])=={'path','sha256'}
        and c.sha(h['operator_script']['path'])==h['operator_script']['sha256']==i['operator_script_sha256'],'Historical inspector code differs')
    p.require(set(a['execution_code']['code_pins'])>=set(code['code_pins'])|{'tools/p3_public_root.py','tools/p3_public_root_start.ps1'},'Complete new public executor required')
    p.require(c.git(p.ROOT,'rev-parse',BASE+'^{tree}').decode().strip()==TREE,'Historical648 tree differs')
    c.git(p.ROOT,'merge-base','--is-ancestor',BASE,a['execution_code']['code_head'])
    window(plan,a,current=False)
    v=a['visibility'];folder=Path(v['acceptance_path']).parent
    p.require(set(v['files_sha256'])=={'ACCEPTANCE.json','PUBLIC-CONFIRMED.png','ACTIONS-DISABLED.png','PAGES-DISABLED.png','RULESETS-EMPTY.png'}
        and Path(v['acceptance_path']).name=='ACCEPTANCE.json'
        and all(c.sha(folder/n)==sha for n,sha in v['files_sha256'].items()),'Exact visibility evidence required')
    evidence=read(v['acceptance_path'])
    p.require(evidence['status']=='public_visibility_changed_and_UI_verified'
        and evidence['repository']==REPO and evidence['repository_id']==RID and evidence['visibility_mutations']==1
        and isinstance(evidence['human_authorization'],str) and evidence['human_authorization']
        and evidence['general_UI_result']=='This repository is currently public.' and evidence['repository_still_empty'] is True
        and evidence['actual_store_upload'] is False and evidence['other_repository_visibility_changes']==0,'Explicit public visibility approval differs')

def history(plan,rows,a):
    i=a['history']['inspection'];parent=i['parent_amendment'];grant=i['parent_grant'];tail=rows[21:24]
    p.require(len(rows)==35 and [x['event'] for x in tail]==['phase_start','reader_validity','phase_halt']
        and all(x['phase']==r.RESUME and x['counts']=={'GET':5,'PUT':0,'GIT_PUSH':0} for x in tail),'Exact24 input cancellation required')
    r.validate_history(plan,rows,parent);r.validate_interrupted(plan,rows[:21],parent)
    p.require(tail[0]['predecessor']==rows[20]['hash'] and tail[0]['journal']==r.RESUME+'.jsonl'
        and tail[1]['amendment_sha256']==p.digest(parent) and tail[1]['grant_sha256']==p.digest(grant)
        and tail[1]['validity']==parent['reader_validity'] and tail[1]['validity_sha256']==p.digest(parent['reader_validity'])
        and tail[1]['execution_code']==parent['execution_code'] and tail[2]['result']=='incomplete-no-retry-no-release'
        and tail[2]['category']=='incomplete-or-expired'
        and all(c.parse_utc(parent['reader_validity']['not_before_utc'])<=c.parse_utc(x['utc'])<min(c.parse_utc(grant['expires_utc']),c.parse_utc(parent['expires_utc'])) for x in tail),'Historical Reader cancellation binding differs')
    g=a['history']['grant'];r.validate_grant(plan,g,'inspect',p.digest(i))
    p.require(i['schema']=='p3-input-cancel-inspection-v2-20h' and i['original_plan_sha256']==p.digest(plan)
        and i['original_expires_utc']==plan['expires_utc'] and i['journal']==r.RESUME+'.jsonl'
        and i['frontier_hash']==rows[23]['hash'] and i['terminal_keyboard_interrupt_report_checked'] is True
        and i['explicit_user_twenty_hours'] is True and i['time_authorization_sha256']==i['review_evidence_sha256']
        and c.parse_utc(i['expires_utc'])-c.parse_utc(i['not_before_utc'])<=p.timedelta(hours=20),'Historical inspector contract differs')
    events=['phase_start','authorization','input_cancel_inspection','inspection_route','request','response',
        'inspection_route','request','response','inspection_error','phase_halt']
    rest=rows[24:]
    p.require([x['event'] for x in rest]==events and all(x['phase']=='inspect' and x['run'] is None for x in rest)
        and rest[0]['journal']=='inspect.jsonl' and rest[0]['predecessor']==rows[23]['hash']
        and rest[1]['grant_sha256']==p.digest(g) and rest[1]['review_sha256']==p.digest(i)
        and rest[1]['grant_expires_utc']==g['expires_utc'] and rest[1]['expiry_policy']==plan['expiry_policy']
        and rest[2]['amendment_sha256']==p.digest(i) and rest[2]['review_evidence_sha256']==i['review_evidence_sha256']
        and rest[2]['scope']==i['scope']=='reader-inspect-after-input-cancel-exact24-two-GET-no-write','Exact inspector history differs')
    for offset,count,route,status in ((3,6,r.routes(plan)[0],'http-200'),(6,7,r.routes(plan)[3],'http-403')):
        before,req,resp=rest[offset:offset+3]
        p.require(before['route']==route and req['method']=='GET' and req['bytes']==0
            and all(req.get(k) is None for k in ('write_id','old_blob','revision','parent_digest'))
            and req['counts']==resp['counts']=={'GET':count,'PUT':0,'GIT_PUSH':0} and resp['result']==status,'Inspector request/outcome differs')
    p.require(rest[-2]['route']==r.routes(plan)[3] and rest[-2]['diagnostic']==rest[8]['diagnostic']
        and rest[-2]['diagnostic']['category']=='feature-unavailable-hint' and rest[-2]['diagnostic']['feature_absence_proved'] is False
        and rest[-1]['category']=='feature-unavailable-hint' and rest[-1]['result']=='incomplete-no-retry-no-release'
        and all(c.parse_utc(i['not_before_utc'])<=c.parse_utc(x['utc'])<min(c.parse_utc(i['expires_utc']),c.parse_utc(g['expires_utc'])) for x in rest), 'Not the exact known feature403 inspector halt')
    p.require(all(x['counts']['PUT']==x['counts']['GIT_PUSH']==0 for x in rows),'Earlier mutation or uncertain write forbidden')

def verify_state(plan,a,*,ledger=None):
    root=Path(plan['journal_directory']);pred=a['predecessor'];rr=p.Ledger.verify(root/pred['journal'],p.digest(plan))
    history(plan,rr,a)
    p.require(pred['journal']=='inspect.jsonl' and pred['frontier_rows']==len(rr)==35
        and pred['frontier_hash']==rr[-1]['hash'] and pred['highwater']==rr[-1]['utc']
        and pred['counts']==rr[-1]['counts']=={'GET':7,'PUT':0,'GIT_PUSH':0}
        and set(pred['files_sha256'])==r.session_files(rr),'Exact latest35 frontier required')
    for name,sha in pred['files_sha256'].items():
        if ledger and name=='probe-session.lock':
            ledger.lock_handle.seek(0);actual=hashlib.sha256(ledger.lock_handle.read()).hexdigest();ledger.lock_handle.seek(0)
        else:actual=c.sha(root/name)
        p.require(actual==sha,'Session bytes changed')
    db=ledger.db if ledger else sqlite3.connect((root/'probe-session.sqlite3').as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        p.require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            and [json.loads(x[0]) for x in db.execute('SELECT body FROM events ORDER BY seq')]==rr
            and db.execute('SELECT plan,journal,published,highwater FROM frontier').fetchone()==(p.digest(plan),pred['journal'],pred['frontier_hash'],pred['highwater']), 'Central frontier mismatch')
    finally:
        if not ledger:db.close()
    starts=[j for j,x in enumerate(rr) if x['event']=='phase_start']
    for index,j in enumerate(starts):
        stop=starts[index+1] if index+1<len(starts) else len(rr)
        p.require((root/rr[j]['journal']).read_bytes()==''.join(p.canonical(x)+'\n' for x in rr[:stop]).encode(),'Historical prefix changed')
        p.require(read(root/('attempt-'+rr[j]['phase']+'.json'))=={k:rr[j][k] for k in ('plan_sha256','phase','journal','pid','predecessor')},'Historical marker differs')
    p.require(not any((root/n).exists() for n in ('probe-session.sqlite3-wal','probe-session.sqlite3-journal',PHASE+'.jsonl','attempt-'+PHASE+'.json')),'Unpublished attempt/replay forbidden')
    review=a['review'];latest=rr[24]
    p.require(review['end_basis']==r.END_BASIS and review['original_pid']==latest['pid']
        and all(review[k] is True for k in ('human_review','terminal_code_path_checked','human_terminal_end_report','all_workers_ended','triggers_paused'))
        and isinstance(review['reviewer'],str) and review['reviewer'] and re.fullmatch('[0-9a-f]{64}',review['evidence_sha256'] or '')
        and c.parse_utc(rr[-1]['utc'])<=c.parse_utc(review['observed_utc'])<=p.datetime.now(p.timezone.utc),'Positive current process-end/Freeze review required')
    ended=c.process_ended(review['original_pid'])
    p.require(c.root_files(a['root']['directory'])==a['root']['files_sha256'],'Root or prior push preparation changed')
    c.verify_root(plan,a['root']['directory']);window(plan,a)
    if ledger:ledger.public_end_observation=ended
    return rr

def validate_locked(ledger,rows,state,a):
    p.require(ledger.phase==PHASE and ledger.path.name==PHASE+'.jsonl' and rows==verify_state(ledger.p,a,ledger=ledger),'Public latest frontier differs')

class PublicGuard(p.GrantGuard):
    def __init__(self,plan,grant,a):
        self.a=deepcopy(a);self.a_hash=p.digest(a);self.writer_authenticated=False
        self.tree_sha=c.git(Path(a['root']['directory']),'rev-parse',SEED+'^{tree}').decode().strip()
        super().__init__(plan,grant,PHASE)
    def deadlines(self):
        _,end=window(self.p,self.a)
        return [end,c.parse_utc(self.grant['expires_utc'])]
    def check(self,ledger=None):
        super().check(ledger)
        p.require(p.digest(self.a)==self.a_hash==self.grant['review_sha256'] and self.a['original_plan_sha256']==self.plan_hash
            and self.a['scope']==SCOPE and self.phase==PHASE,'Live public review differs')
        if ledger:
            p.require(ledger.public_root_hash==self.a_hash and ledger.counts['PUT']==0 and ledger.counts['GIT_PUSH']<=1,'Public live budget/review differs')
            c.root_matches(self.a)
    def validate_route(self,method,route):
        p.require(method=='GET','Public bootstrap forbids PUT')
        base=r.routes(self.p)[0];branch=urllib.parse.quote(self.p['branch'],safe='')
        p.require(route in r.routes(self.p) or route==base+'/git/ref/heads/'+branch
            or route==base+'/contents/delivery/stream.json?ref='+SEED
            or route==base+'/git/commits/'+SEED
            or route==base+'/git/trees/'+self.tree_sha+'?recursive=1','Public route not pinned')

def authorize(plan,a,g,approved):
    shape(plan,a);window(plan,a)
    p.require(p.digest(a)==approved,'Independent public amendment hash differs')
    r.validate_grant(plan,g,PHASE,approved)
    p.require(c.parse_utc(g['expires_utc'])<=c.parse_utc(a['expires_utc']),'Grant exceeds public window')
    guard=PublicGuard(plan,g,a);r.verify_execution_code(a['execution_code']);verify_state(plan,a)
    return guard

class PublicBoundary(r.RulesBoundary):
    def identity(self,value):
        p.require(isinstance(value,dict) and value.get('id')==RID and value.get('full_name')==REPO
            and value.get('private') is False and value.get('has_pages') is False and value.get('archived') is False
            and value.get('permissions',{}).get('admin') is True,'Public exact identity/Pages/admin differs')
    def preflight(self,empty=False):
        fixed=r.routes(self.p);self.identity(self.request('GET',fixed[0]))
        p.require(self.request('GET',fixed[1]).get('enabled') is False,'Actions must be disabled')
        for index in (2,):
            try:self.request('GET',fixed[index])
            except p.HTTPStatus as exc:p.require(exc.status==404,'Pages unavailable')
            else:raise ValueError('Pages exists')
        p.require(self.request('GET',fixed[3])==[] and self.request('GET',fixed[4])==[],'Positive200 empty rules/rulesets required')
        branches=self.request('GET',fixed[5])
        p.require(branches==[] if empty else isinstance(branches,list) and len(branches)==1
            and branches[0].get('name')==self.p['branch'] and branches[0].get('protected') is False
            and branches[0].get('commit',{}).get('sha')==SEED, 'Empty repo or exact sole branch required')
        try:self.request('GET',fixed[6])
        except p.HTTPStatus as exc:p.require(exc.status==404,'Classic protection unavailable')
        else:raise ValueError('Classic protection present')
        self.ledger.emit('public_preflight',result='confirmed-public-empty' if empty else 'confirmed-public-original-root',scope=SCOPE)
    def writer_identity(self):
        original=self.reader;self.reader=self.writer
        try:self.identity(self.request('GET',r.routes(self.p)[0]))
        finally:self.reader=original
        self.ledger.emit('public_writer_auth',result='authenticated-read-only-no-write-rights-guarantee',repository_id=RID)
        self.guard.writer_authenticated=True

def push(client,a):
    b=client.boundary;l=b.ledger;d=Path(a['root']['directory']);b.guard.check(l)
    p.require(b.guard.writer_authenticated and b.writer,'Writer authentication required')
    l.emit('public_push_prepare',commit=SEED,bytes=1981,parents=[],amendment_sha256=p.digest(a))
    b.guard.check(l)
    helper=d/'synthetic-askpass.py';helper.write_text("import os,sys\nprint('x-access-token' if 'username' in sys.argv[1].lower() else os.environ['P3_EXPLICIT_BOOTSTRAP_TOKEN'])\n",encoding='utf-8')
    ask=d/'synthetic-askpass.cmd';ask.write_text('@echo off\r\n"'+sys.executable+'" "'+str(helper)+'" %*\r\n',encoding='utf-8')
    env=p.git_environment();env.update(GIT_TERMINAL_PROMPT='0',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,
        GIT_ASKPASS=str(ask),P3_EXPLICIT_BOOTSTRAP_TOKEN=b.writer)
    b.guard.check(l);l.charge('GIT_PUSH',commit=SEED,bytes=1981,parents=[],write_id='synthetic-explicit-blocked-seed-v1',revision=0,old_blob=None)
    b.before_outbound('GIT_PUSH')
    try:subprocess.run(['git','-c','safe.directory='+d.as_posix(),'-c','core.hooksPath='+str(d/'empty-hooks'),'-C',str(d),
        '-c','credential.helper=','-c','http.followRedirects=false','push','--no-verify','--porcelain','https://github.com/'+REPO+'.git',SEED+':refs/heads/p3-synthetic-only'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15,check=True)
    except (subprocess.SubprocessError,OSError):
        l.emit('public_push_response',result='unknown-no-retry-no-readback');raise ValueError('Push outcome unknown') from None
    b.guard.check(l);l.emit('public_push_response',result='returned-success-not-yet-confirmed')
    head=p.verify_history(client,full=True)
    p.require(head['commit_sha']==SEED and head['body']==p.synthetic_seed(b.p) and len(head['body'])==1981,'Exact public root readback differs')
    b.preflight(empty=False);l.emit('phase_end',result='confirmed',scope=SCOPE,activation_allowed=False)

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--template');cli.add_argument('--real',action='store_true')
    for k in ('plan','amendment','grant','approved-amendment-sha256'):cli.add_argument('--'+k)
    args=cli.parse_args()
    if args.template:
        p.require(not args.real,'Template offline only')
        with Path(args.template).open('x',encoding='utf-8') as f:json.dump(template(),f,indent=2)
        return 0
    p.require(args.real and all((args.plan,args.amendment,args.grant,args.approved_amendment_sha256)),'Default offline; full independent public review/grant required')
    plan,a,g=[read(x) for x in (args.plan,args.amendment,args.grant)]
    guard=authorize(plan,a,g,args.approved_amendment_sha256)
    try:reader=p.read_token('Reader')
    except (KeyboardInterrupt,ValueError):
        print('Reader-Eingabe abgebrochen/ungueltig. Kein Sessionversuch/Request gestartet.');return 3
    guard.check();verify_state(plan,a)
    root=Path(plan['journal_directory']);l=p.Ledger(plan,root/(PHASE+'.jsonl'),PHASE,root/'inspect.jsonl',public_root_amendment=a)
    try:
        b=PublicBoundary(plan,l,reader,'',guard=guard);client=p.Client(b)
        l.emit('public_root_review',amendment_sha256=p.digest(a),grant_sha256=p.digest(g),scope=SCOPE,
            execution_code=a['execution_code'],original_expires_utc=plan['expires_utc'],not_before_utc=a['not_before_utc'],expires_utc=a['expires_utc'])
        b.preflight(empty=True);guard.check(l)
        b.writer=p.read_token('Writer');guard.check(l);b.writer_identity();push(client,a)
        print('Urspruenglicher synthetischer blocked-Root bestaetigt. Keine Aktivierung.');return 0
    except BaseException:
        if not l.poisoned:l.emit('phase_halt',result='incomplete-no-retry-no-release',category='public-root-incomplete')
        print('HALT: Public-Root nicht vollstaendig bestaetigt. Nicht erneut starten. Ergebnis: '+str(l.path));return 2
    finally:l.close()
