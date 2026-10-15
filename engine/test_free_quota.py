"""New quota-path tests only. Synthetic providers; socket access forbidden."""
from contextlib import redirect_stdout,contextmanager
from copy import deepcopy
import base64
import io
import json
import os
from pathlib import Path
import runpy
import socket
import sys
import tempfile
import traceback
import urllib.error
import urllib.parse
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import test_free_public as old
import test_hosted_backup as hosted
import test_betriebsabschluss as operating
import p4_hosted_backup as h
import actions_freshness as monitor
import produktion_actions_freshness as cli
import produktion_actions_runner as sender
import produktion_pages_export as pages
import public_access as public
import job_quota
from production_confirmation import ProductionContentsClient
from production_contract import canonical,digest
from github_freshness import iso

OUT=None
TOKEN='offline-automatic-jobtoken'


class Reply(io.BytesIO):
    def __init__(self,raw,headers=None):
        super().__init__(raw);self.headers=headers or {};self.status=200


class Ledger:
    def __init__(self,limit=1000): self.rows=[];self.limit=limit;self.core=0
    def record(self,req,response):
        u=urllib.parse.urlsplit(req.full_url);method=req.get_method()
        pool='automatic-core' if u.netloc=='api.github.com' and method=='GET' else 'writer-core' if u.netloc=='api.github.com' else 'immutable-raw' if u.netloc=='raw.githubusercontent.com' else 'git-read'
        self.rows.append({'pool':pool,'method':method,'host':u.netloc,'path':u.path,'query':u.query})
        if pool=='automatic-core':
            self.core+=1
            if self.core>self.limit:
                raise urllib.error.HTTPError(req.full_url,403,'synthetic limit',{'X-RateLimit-Remaining':'0','X-RateLimit-Reset':'1791110000'},None)
        headers={'X-RateLimit-Limit':str(self.limit),'X-RateLimit-Remaining':str(max(0,self.limit-self.core)),
                 'X-RateLimit-Used':str(self.core),'X-RateLimit-Reset':'1791110000','X-RateLimit-Resource':'core'} if pool=='automatic-core' else {}
        self.rows[-1]['status']=200;self.rows[-1]['rate_headers']=headers
        return Reply(response.read(),headers)


def advertisement(heads):
    def pkt(raw): return f'{len(raw)+4:04x}'.encode()+raw
    raw=pkt(b'# service=git-upload-pack\n')+b'0000'
    for i,(branch,pin) in enumerate(heads):
        raw+=pkt((pin+' refs/heads/'+branch+('\0side-band-64k ofs-delta no-progress' if i==0 else '')+'\n').encode())
    return Reply(raw+b'0000')


class QuotaProvider(old.PublicProvider):
    def __init__(self,name,ledger=None):
        old.OUT=OUT;super().__init__(name)
        self.ledger=ledger or Ledger();self.tokens['source_read']=self.tokens['metadata_read']
        self.public_mode=False
    def open(self,req,timeout):
        u=urllib.parse.urlsplit(req.full_url);method=req.get_method()
        if u.netloc=='raw.githubusercontent.com':
            assert req.get_header('Authorization')=='Bearer '+self.tokens['metadata_read']
            parts=u.path.split('/');repo='/'.join(parts[1:3]);pin=parts[3];name='/'.join(parts[4:]);local=self.repo(repo,pin) if repo!='synthetic/code' else None
            if repo=='synthetic/code': raw=self.yaml[name]
            else:
                with h.b.batch(local,h.b.Budget()) as read: raw=read(pin+':'+name,'blob',h.b.MAX_PACKAGE)
            answer=Reply(raw)
        elif u.netloc=='github.com':
            assert base64.b64decode(req.get_header('Authorization').removeprefix('Basic ')).decode()=='x-access-token:'+self.tokens['metadata_read']
            answer=hosted.Provider.open(self,req,timeout)
        else:
            parts=u.path.split('/');repo='/'.join(parts[2:4]);tail='/'+('/'.join(parts[4:])) if len(parts)>4 else ''
            if method=='GET': assert req.get_header('Authorization')=='Bearer '+self.tokens['metadata_read']
            else:
                role='backup_write' if repo=='synthetic/backup' else 'receipt_write'
                assert req.get_header('Authorization')=='Bearer '+self.tokens[role]
            if not tail: value={'id':self.access['repositories'][repo]['id'],'full_name':repo,'private':False,'visibility':'public'}
            elif tail.startswith('/rules/branches/'):
                page=int(urllib.parse.parse_qs(u.query)['page'][0]);value=self.rules[(repo,tail.rsplit('/',1)[-1])][(page-1)*100:page*100]
            elif tail.startswith('/rulesets/'): value=self.rulesets[(repo,int(tail.rsplit('/',1)[-1]))]
            else: value=None
            answer=Reply(canonical(value).encode()) if value is not None else hosted.Provider.open(self,req,timeout)
        return self.ledger.record(req,answer)


def monitor_fixture():
    operating.ARTIFACT_ROOT=OUT/'monitor-history'
    operating.example.cache_clear()
    from test_github_delivery import REPO,BRANCH
    repos={REPO:{'id':1,'visibility':'public','branches':[BRANCH,'actions-fence']},
        'synthetic/backup':{'id':2,'visibility':'public','branches':['protected-pair']},
        'synthetic/verifier':{'id':3,'visibility':'public','branches':['protected-receipts']},
        'synthetic/code':{'id':4,'visibility':'public','branches':['synthetic']}}
    access,rules,sets=old.access_for(repos)
    original=sender.deployment
    def deployment(r): return {**original(r),'public_access_sha256':digest(access)}
    with patch.object(sender,'deployment',side_effect=deployment): f=operating.example()
    http=operating.HTTP(f);http.policy['public_access']=access
    http.access=access;http.rules=rules;http.sets=sets
    workflows=['.github/workflows/'+k+'.yml' for k in ('signal','watch','lage','backup-verify','freshness')]
    http.yaml={w:('offline reviewed '+w+'\n').encode() for w in workflows}
    http.policy['entry_workflows']={w:__import__('hashlib').sha256(raw).hexdigest() for w,raw in http.yaml.items()}
    d=http.policy['deployment'];w='.github/workflows/freshness.yml'
    http.policy['monitor_entry']={'repository':'synthetic/code','branch':'synthetic','code_sha':d['code_sha'],
        'workflow':w,'workflow_sha256':http.policy['entry_workflows'][w]}
    http.runs['9000']={'id':9000,'run_attempt':1,'repository':{'full_name':'synthetic/code'},'path':w,
        'head_sha':d['code_sha'],'head_branch':'synthetic','event':'workflow_dispatch'}
    return http


def monitor_cli(http,now,ledger=None):
    ledger=ledger or Ledger();path=OUT/'monitor-policy.json';path.write_text(canonical(http.policy))
    def reply(req,timeout):
        u=urllib.parse.urlsplit(req.full_url)
        if u.netloc=='raw.githubusercontent.com':
            assert req.get_header('Authorization')=='Bearer '+TOKEN
            parts=u.path.split('/');repo='/'.join(parts[1:3]);pin=parts[3];name='/'.join(parts[4:])
            answer=Reply(http.yaml[name] if name.startswith('.github/') else http.records[(repo,pin,name)])
        elif u.netloc=='github.com':
            assert base64.b64decode(req.get_header('Authorization').removeprefix('Basic ')).decode()=='x-access-token:'+TOKEN
            repo=u.path.split('.git/')[0].lstrip('/')
            answer=advertisement([(b,p) for (r,b),p in http.heads.items() if r==repo])
        else:
            assert req.get_header('Authorization')=='Bearer '+TOKEN
            parts=u.path.split('/');repo='/'.join(parts[2:4]);tail='/'+('/'.join(parts[4:])) if len(parts)>4 else ''
            if not tail: value={'id':http.access['repositories'][repo]['id'],'full_name':repo,'private':False,'visibility':'public'}
            elif tail.startswith('/rules/branches/'): value=http.rules[(repo,tail.rsplit('/',1)[-1])]
            elif tail.startswith('/rulesets/'): value=http.sets[(repo,int(tail.rsplit('/',1)[-1]))]
            elif tail.startswith('/contents/.github/'):
                raw=http.yaml[tail.removeprefix('/contents/')];value={'type':'file','encoding':'base64',
                    'sha':h.oid('blob',raw),'content':base64.b64encode(raw).decode()}
            else: value=None
            answer=Reply(canonical(value).encode()) if value is not None else http.open(req,timeout)
        return ledger.record(req,answer)
    env={'GITHUB_TOKEN':TOKEN,'GITHUB_REPOSITORY':'synthetic/code','GITHUB_REF':'refs/heads/synthetic',
        'GITHUB_WORKFLOW_REF':'synthetic/code/.github/workflows/freshness.yml@refs/heads/synthetic',
        'GITHUB_SHA':http.policy['deployment']['code_sha'],'GITHUB_RUN_ID':'9000','GITHUB_RUN_ATTEMPT':'1',
        'GITHUB_EVENT_NAME':'workflow_dispatch'}
    capture=io.StringIO()
    with patch.dict(os.environ,env,clear=True),patch.object(ProductionContentsClient,'open_request',side_effect=reply),\
         patch.object(monitor.Reader,'open_request',side_effect=reply),patch.object(cli,'time') as clock,\
         patch.object(sender,'check_code_pin'),patch.object(sys,'argv',['produktion_actions_freshness.py','--policy',str(path)]),redirect_stdout(capture):
        # runpy loads its own CLI module but uses the same standard time module.
        with patch('time.time',return_value=now/1000):
            try: runpy.run_path(str(ROOT/'tools/produktion_actions_freshness.py'),run_name='__main__')
            except SystemExit as e: status=e.code
    result=json.loads(capture.getvalue());return status,result,ledger


def test_full_monitor_cli_and_mutable_failure():
    http=monitor_fixture();now=http.f['base']+60*operating.slots.MINUTE
    status,result,ledger=monitor_cli(http,now)
    assert status==0 and result['http_status']==200,(status,result,len(ledger.rows),ledger.rows[-5:])
    assert result['budget']['get']==len(ledger.rows)<=64
    (OUT/'MONITOR-CLI.json').write_text(canonical({'offline_only':True,'provider_proof':False,'exit':status,'result':result,'requests':ledger.rows}))
    for fault in ('rule','bypass','completion','receipt','motion','jobs'):
        bad=deepcopy(http)
        if fault=='rule': next(iter(bad.rules.values())).clear()
        if fault=='bypass': next(iter(bad.sets.values()))['bypass_actors']=[{'actor_id':1}]
        if fault=='completion':
            d=bad.policy['deployment'];pin=bad.heads[(d['private_store_repository'],d['store_branch'])]
            snap=json.loads(bad.records[(d['private_store_repository'],pin,'delivery/stream.json')])['snapshot']
            loc=list(snap['control']['health']['completed_runs']['signal'].values())[-1]['completion']
            bad.records[(d['private_store_repository'],loc['commit_sha'],'delivery/stream.json')]=b'{}'
        if fault=='receipt': bad.receipt['verification']['history_verified']=False;bad.sync_receipt()
        if fault=='jobs': bad.jobs['105']['jobs'][0]['conclusion']='skipped'
        if fault=='motion':
            count=[0];original=bad.open
            def move(req,timeout):
                if '/actions/workflows/signal.yml/runs' in req.full_url:
                    count[0]+=1
                    if count[0]==2: bad.lists['signal'].pop()
                return original(req,timeout)
            bad.open=move
        code,refused,_=monitor_cli(bad,now)
        assert code==20 and refused['http_status']!=200,fault


def test_pair_counts_and_full_independent_restore():
    p=QuotaProvider('pair');upload,producer=p.invoke();boundary=len(p.ledger.rows);receipt,verifier=p.invoke('verifier')
    for i,row in enumerate(p.ledger.rows): row['phase']='producer' if i<boundary else 'verifier'
    assert receipt['verification']['history_verified'] and receipt['verification']['restore_blocked_verified']
    assert (verifier/'fresh-blocked/RESTORE-BLOCKED.json').is_file()
    assert receipt['destination']['commit_sha']==upload['destination']['commit_sha']
    (OUT/'PAIR-COUNTS.json').write_text(canonical({'offline_only':True,'producer':upload['metrics'],
        'verifier':receipt['metrics'],'requests':p.ledger.rows,'automatic_core':p.ledger.core}))


def test_seven_entries_and_associated_pages():
    import actions_delivery as actions
    import telegram_notify as tg
    import test_pflichtfunktionen as functions
    from reviewed_actions_entry import EntryReader
    from strategy_core import Candle
    ledger=Ledger();events=[]
    with operating.actual_entry() as (root,data,path,runtime,http,_,first):
        repo=runtime['private_store_repository'];branches=[runtime['store_branch'],runtime['fence_branch']]
        repos={repo:{'id':51,'visibility':'public','branches':branches},
            'synthetic/code':{'id':52,'visibility':'public','branches':['synthetic']}}
        access,rules,sets=old.access_for(repos);old.writer_review(access,'sender_write',repo,branches)
        runtime['public_access']=access;runtime['public_access_sha256']=digest(access)
        yaml={'.github/workflows/'+k+'.yml':('offline reviewed '+k+'\n').encode() for k in ('signal','watch','lage','pages')}
        runtime['entry_workflows']={w:__import__('hashlib').sha256(raw).hexdigest() for w,raw in yaml.items()}
        value=json.loads(http.file(actions.FENCE_PATH));value['deployment']=sender.deployment(runtime)
        http.state['history'][http.state['heads'][runtime['fence_branch']]][actions.FENCE_PATH]=canonical(value)
        path.write_text(canonical(runtime));base=first-2*operating.slots.MINUTE;current={}
        def reply(req,timeout):
            u=urllib.parse.urlsplit(req.full_url);method=req.get_method()
            if u.netloc=='raw.githubusercontent.com':
                assert req.get_header('Authorization')=='Bearer '+TOKEN
                parts=u.path.split('/');pin=parts[3];name='/'.join(parts[4:])
                answer=Reply(yaml[name] if name.startswith('.github/') else http.state['history'][pin][name].encode())
            elif u.netloc=='github.com':
                assert base64.b64decode(req.get_header('Authorization').removeprefix('Basic ')).decode()=='x-access-token:'+TOKEN
                answer=advertisement(list(http.state['heads'].items()))
            else:
                parts=u.path.split('/');r='/'.join(parts[2:4]);tail='/'+('/'.join(parts[4:])) if len(parts)>4 else ''
                assert req.get_header('Authorization')=='Bearer '+(TOKEN if method=='GET' else 'synthetic-only')
                if not tail: value={'id':repos[r]['id'],'full_name':r,'private':False,'visibility':'public'}
                elif '/rules/branches/' in tail: value=rules[(r,tail.rsplit('/',1)[-1])]
                elif '/rulesets/' in tail: value=sets[(r,int(tail.rsplit('/',1)[-1]))]
                elif tail.startswith('/actions/runs/'): value=current
                elif tail.startswith('/contents/.github/'):
                    raw=yaml[tail.removeprefix('/contents/')];value={'type':'file','encoding':'base64','sha':h.oid('blob',raw),'content':base64.b64encode(raw).decode()}
                else: value=None
                answer=Reply(canonical(value).encode()) if value is not None else http.open(req,timeout)
            return ledger.record(req,answer)
        sequence=[('signal',2),('watch',8),('watch',23),('lage',29),('signal',32),('watch',38),('watch',53)]
        numbers={'signal':0,'watch':0,'lage':0}
        with patch.dict(os.environ,{'GITHUB_TOKEN':TOKEN}),patch.object(actions.ActionsClient,'open_request',side_effect=reply),\
             patch.object(ProductionContentsClient,'open_request',side_effect=reply),patch.object(pages.ReadClient,'open_request',side_effect=reply),\
             patch.object(EntryReader,'open_request',side_effect=reply),\
             patch.object(pages,'check_code_pin'),patch.object(tg,'deliver_telegram',side_effect=functions.receipt):
            for i,(kind,minute) in enumerate(sequence):
                slot=base+minute*operating.slots.MINUTE;numbers[kind]+=1;rid=str(100+i)
                current=operating.metadata(kind,slot,rid,numbers[kind]);start=len(ledger.rows)
                env={'BTC_DELIVERY_WORKFLOW':current['path'],'GITHUB_WORKFLOW_REF':'synthetic/code/'+current['path']+'@refs/heads/synthetic',
                    'GITHUB_RUN_NUMBER':str(numbers[kind]),'GITHUB_RUN_ID':rid,'BTC_DELIVERY_RUN_ID':rid,
                    'BTC_ACTIONS_EXPLICIT_START_MS':''}
                with patch.dict(os.environ,env),patch('time.time',return_value=(slot+1500)/1000):
                    if kind=='signal': result=sender.run_runtime(path,kind,data,fetch=lambda _:([],[],[]))
                    elif kind=='watch':
                        candle=slot//(4*operating.slots.HOUR)*(4*operating.slots.HOUR)
                        raw=[[candle+(j-30)*14400000,100,101,99,100,0,candle+(j-29)*14400000-1] for j in range(31)]
                        result=sender.run_runtime(path,kind,data,watch_raw=raw,now_ms=slot+1500)
                    else:
                        candles=[Candle(base+(j-30)*14400000,100+j,103+j,99+j,102+j) for j in range(31)]
                        result=sender.run_runtime(path,kind,data,fetch=lambda _:(candles,[],[]),sth=lambda:None)
                entry_rows=ledger.rows[start:];start=len(ledger.rows)
                pr={'schema':pages.SCHEMA,'enabled':True,'workflow':pages.WORKFLOW,'deployment_schema':actions.POLICY,
                    'deployment':sender.deployment(runtime),'public_access':access,'entry_workflows':runtime['entry_workflows']}
                pp=root/'pages-runtime.json';pp.write_text(canonical(pr));target=root/('public-'+str(i))
                current=operating.metadata('pages',slot+4000,str(200+i),i+1)
                stamp=json.loads(http.file('delivery/stream.json'))['snapshot']['engine']['last_signal_ts']
                with patch.dict(os.environ,{'BTC_DELIVERY_GITHUB_TOKEN':'','TELEGRAM_BOT_TOKEN':'','GITHUB_RUN_ID':str(200+i),'GITHUB_WORKFLOW_REF':'synthetic/code/'+pages.WORKFLOW+'@refs/heads/synthetic'}),\
                     patch('time.time',return_value=(stamp+14400000+1000)/1000):
                    exported=pages.export(pp,data/'config.json',target,identities_only=True)
                    pages.export(pp,data/'config.json',target,verify=target.with_suffix('.receipt.json'))
                events.append({'minute':minute,'kind':kind,'entry':entry_rows,'entry_metrics':result,
                    'pages':ledger.rows[start:],'pages_exports':2,'pages_first_metrics':exported})
    (OUT/'ENTRIES-PAGES.json').write_text(canonical({'offline_only':True,'events':events,'automatic_core':ledger.core,'requests':ledger.rows}))


def test_shared_hour_and_header_stops():
    from p4_quota_hour import model
    report=model(OUT);(OUT/'HOUR.json').write_text(canonical(report))
    from github_freshness import ReadBudget
    cases=[({'X-RateLimit-Remaining':'0','X-RateLimit-Reset':'1'},200),
           ({'X-RateLimit-Remaining':'0','X-RateLimit-Reset':'9999999999'},200),
           ({'X-RateLimit-Remaining':'999','Retry-After':'60'},403),
           ({'X-RateLimit-Remaining':'999','Retry-After':'60'},429),
           ({'X-RateLimit-Remaining':'invalid'},200),
           ({'X-RateLimit-Limit':'invalid'},200),
           ({'X-RateLimit-Reset':'invalid'},200)]
    results=[]
    for headers,status in cases:
        seen=[];budget=ReadBudget()
        with patch.dict(os.environ,{'GITHUB_TOKEN':TOKEN},clear=True):
            reader=monitor.Reader(TOKEN,['synthetic/data'],budget)
            def reply(req,timeout):
                seen.append((req.get_method(),req.get_header('Authorization')))
                if status!=200: raise urllib.error.HTTPError(req.full_url,status,'synthetic',headers,None)
                return Reply(b'{}',headers)
            with patch.object(reader,'open_request',side_effect=reply):
                for _ in range(3):
                    try: reader._request('GET','/repos/synthetic/data')
                    except (RuntimeError,ValueError): pass
            assert len(seen)==1 and seen[0]==('GET','Bearer '+TOKEN)
            results.append({'status':status,'requests':len(seen),'headers':reader.quota_headers.observations,'stopped':reader.quota_headers.stopped})
    (OUT/'HEADER-STOPS.json').write_text(canonical({'offline_only':True,'no_retry':True,'no_fallback':True,'cases':results}))
    p=QuotaProvider('producer-quota-refusal',Ledger(limit=1))
    with p.context(): assert h.cli(['producer'])==20
    assert len(p.ledger.rows)==1 and not p.mutations
    assert not list(p.root.glob('btc-producer-*/confirmed.json'))
    (OUT/'PRODUCER-QUOTA-STOP.json').write_text(canonical({'offline_only':True,'exit':20,'requests':1,'confirmed':False,'mutations':0}))


def test_scope_cache_wall_and_disabled_overlay():
    import ast
    from github_freshness import ReadBudget
    from test_github_delivery import fails
    from p4_install_hosted_templates import materialize
    from github_delivery import GitHubContentsClient,StoreUnavailable
    with patch.dict(os.environ,{'GITHUB_TOKEN':TOKEN},clear=True):
        budget=ReadBudget();reader=monitor.Reader(TOKEN,['synthetic/data'],budget)
        seen=[]
        def reply(req,timeout): seen.append(req.full_url);return Reply(b'{}')
        with patch.object(reader,'open_request',side_effect=reply):
            route='/repos/synthetic/data/git/blobs/'+'a'*40
            reader._request('GET',route);reader._request('GET',route)
            reader._request('GET','/repos/synthetic/data');reader._request('GET','/repos/synthetic/data')
            assert len(seen)==3 and budget.requests==3
            for method,route in [('PUT','/repos/synthetic/data'),('GET','/repos/foreign/data'),('GET','/repos/synthetic/data/issues')]:
                fails(StoreUnavailable,lambda:reader._request(method,route))
            budget.requests=64;fails(StoreUnavailable,lambda:reader._request('GET','/repos/synthetic/data'))
            budget.requests=0;budget.started-=21;fails(StoreUnavailable,lambda:reader._request('GET','/repos/synthetic/data'))
            assert len(seen)==3
        fails(ValueError,lambda:monitor.Reader('writer-secret',['synthetic/data'],ReadBudget()))
        fails(ValueError,lambda:monitor.Reader(None,['synthetic/data'],ReadBudget()))
        reader=monitor.Reader(TOKEN,['synthetic/data'],ReadBudget());wire=[]
        def corrupt(req,timeout): wire.append(req.full_url);return Reply(b'corrupt')
        with patch.object(reader,'open_request',side_effect=corrupt):
            fails(ValueError,lambda:reader.read_pinned('synthetic/data','a'*40,'receipt.json',blob='b'*40))
        assert len(wire)==1 and wire[0].startswith('https://raw.githubusercontent.com/')
        with patch.dict(os.environ,{'BTC_HOSTED_BACKUP_WRITE_TOKEN':'synthetic-writer'}): fails(ValueError,job_quota.read_only_environment)
        from p4_public_preflight import cli as preflight
        access,rules,sets=old.access_for({'synthetic/data':{'id':1,'visibility':'public','branches':['one','two','three','four']}})
        path=OUT/'preflight-access.json';path.write_text(canonical(access));calls=[]
        def answer(req,timeout):
            assert req.get_header('Authorization')=='Bearer '+TOKEN;calls.append(req.full_url)
            tail=urllib.parse.urlsplit(req.full_url).path.removeprefix('/repos/synthetic/data')
            value={'id':1,'full_name':'synthetic/data','private':False,'visibility':'public'} if not tail else rules[('synthetic/data',tail.rsplit('/',1)[-1])] if '/rules/branches/' in tail else sets[('synthetic/data',int(tail.rsplit('/',1)[-1]))]
            return Reply(canonical(value).encode())
        with patch.object(ProductionContentsClient,'open_request',side_effect=answer):
            assert preflight(['--review',str(path),'--out',str(OUT/'preflight'),'--public-read'])==0
        assert len(calls)==9
    pins=materialize(OUT/'overlay');assert len(pins)==7
    for path in pins:
        text=(OUT/'overlay'/path).read_text()
        assert 'if: ${{ false }}' in text and 'persist-credentials: false' in text
        assert 'actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683' in text
        assert 'Bounded anonymous public code checkout' not in text
        assert 'if ! "$network"; then exec "$real_git" "$@"; fi' in text
        assert 'if [[ -e "$stop_file" ]]; then exit 86; fi' in text
        assert 'BTC_CHECKOUT_REAL_GIT' not in text
        if path.endswith(('pages.yml','freshness.yml')):
            assert 'secrets.' not in text
    probe=(ROOT/'ops/produktion/provider-read-probe.disabled.yml').read_text()
    assert 'if: ${{ false }}' in probe and 'timeout-minutes: 5' in probe and 'secrets.' not in probe
    embedded=probe.split("          python3 - <<'PY'\n",1)[1].rsplit('          PY',1)[0]
    assert '\n'.join(line[10:] if line.startswith('          ') else line for line in embedded.splitlines())+'\n'==(ROOT/'tools/p4_public_provider_probe.py').read_text()
    ast.parse((ROOT/'tools/p4_public_provider_probe.py').read_text())
    (OUT/'SCOPE-OVERLAY.json').write_text(canonical({'offline_only':True,'overlay_files':pins,'probe_started':False,
        'missing_wrong_tokens_rejected':True,'raw_hash_mismatch_no_fallback':True,'monitor_limits_unchanged':[64,20]}))


def main():
    global OUT
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--only',nargs='*');a=p.parse_args()
    OUT=Path(a.out).resolve();OUT.mkdir(exist_ok=False);results=[]
    @contextmanager
    def retained_temp(*args,**kwargs):
        yield tempfile.mkdtemp(prefix='retained-',dir=OUT)
    for name,fn in list(globals().items()):
        if name.startswith('test_') and callable(fn) and (not a.only or name in a.only):
            try:
                with patch.object(socket.socket,'connect',side_effect=AssertionError('Offline test forbids network')),\
                     patch.object(tempfile,'TemporaryDirectory',side_effect=retained_temp): fn()
                results.append({'test':name,'passed':True});print('PASS',name,flush=True)
            except Exception:
                traceback.print_exc();results.append({'test':name,'passed':False});print('FAIL',name,flush=True)
    (OUT/'RESULTS.json').write_text(canonical({'offline_only':True,'provider_proof':False,'results':results}))
    return 0 if results and all(r['passed'] for r in results) else 1


if __name__=='__main__': sys.exit(main())
