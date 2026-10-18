"""New Free-only offline cases through actual CLI/clients; no provider access."""
from contextlib import contextmanager
from copy import deepcopy
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import traceback
import urllib.parse
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import p4_hosted_backup as h
import p3_backup_chain as b
import public_access as public
import github_delivery as github
import actions_delivery as actions
import actions_freshness as monitor
import produktion_actions_runner as sender
import produktion_pages_export as pages
import produktion_actions_freshness as monitor_cli
from github_freshness import ReadBudget
from production_contract import canonical,digest
from test_hosted_backup import Provider
from test_github_delivery import fails

OUT=None


def sealed(value):
    value['sha256']=public.review_hash(value);return value


def access_for(repos):
    access={'schema':'btc-public-access-v1','enabled':True,'repositories':repos,
            'protections':{},'credential_reviews':{}}
    rules={};sets={}
    for repo,t in repos.items():
        for branch in t['branches']:
            rid=len(sets)+101
            rows=[{'type':kind,'ruleset_id':rid,'ruleset_source_type':'Repository','ruleset_source':repo}
                  for kind in ('deletion','non_fast_forward','required_linear_history')]
            rs={'id':rid,'target':'branch','enforcement':'active','source_type':'Repository','source':repo,
                'conditions':{'ref_name':{'include':['refs/heads/'+branch],'exclude':[]}},
                'rules':[{'type':r['type']} for r in rows]}
            # Anonymous response intentionally omits bypass_actors.
            proof=sealed({'schema':'btc-bypass-review-v1','status':'actually-reviewed',
                'repository':repo,'repository_id':t['id'],'branch':branch,'ruleset_id':rid,
                'public_sha256':digest(rs),'bypass_actors':[],'reviewer':'OFFLINE SYNTHETIC',
                'reviewed_at':'2026-10-14T00:00:00Z','evidence_sha256':digest(['mock bypass',repo,branch])})
            access['protections'][repo+'@'+branch]={'repository':repo,'repository_id':t['id'],
                'branch':branch,'active_rules_sha256':digest(rows),
                'rulesets':{str(rid):{'public_sha256':digest(rs),'bypass_review':proof}}}
            # Actual authenticated caller metadata; the separate bypass proof
            # above binds the public ruleset without this presentation field.
            rs['current_user_can_bypass']='never'
            rules[(repo,branch)]=rows;sets[(repo,rid)]=rs
    return access,rules,sets


def writer_review(access,role,repo,branches):
    access['credential_reviews'][role]=sealed({'schema':'btc-writer-review-v1','status':'actually-reviewed',
        'role':role,'repository_id':access['repositories'][repo]['id'],'repositories':[repo],'branches':branches,
        'permissions':{'contents':'write','metadata':'read'},'credential_type':'fine-grained-pat',
        'credential_reference':'OFFLINE-'+role,'other_repository_write':False,'reviewer':'OFFLINE SYNTHETIC',
        'reviewed_at':'2026-10-14T00:00:00Z','evidence_sha256':digest(['mock credential',role])})


class PublicProvider(Provider):
    def __init__(self,name):
        super().__init__(OUT/name)
        self.public_mode=False;self.headers=[];self.overrides={};self.drops=set();self.calls=[]
        repos={}
        for repo,branch in self.repos:
            t=next(t for t in self.targets.values() if t['repository']==repo)
            repos.setdefault(repo,{'id':t['id'],'visibility':'public','branches':[]})['branches'].append(branch)
        repos['synthetic/code']={'id':4,'visibility':'public','branches':['synthetic']}
        self.access,self.rules,self.rulesets=access_for(repos)
        for role,key in (('backup_write','backup'),('receipt_write','receipts')):
            t=self.targets[key];writer_review(self.access,role,t['repository'],[t['branch']])
        self.runtime['public_access']=self.access;self.set_digest()
        # New public binding is part of every fence revision, not a volatile hint.
        from test_betriebsabschluss import commit_file
        old=self.repos[(self.targets['source']['repository'],'fence')]
        new=self.root/'public-fence';previous=None
        for pin in b.commits(old,h.pair.head(old,'fence',b.Budget()),None,b.Budget()):
            with b.batch(old,b.Budget()) as read: value=json.loads(read(pin+':'+actions.FENCE_PATH,'blob',actions.MAX_FENCE_BYTES))
            value['deployment']=self.runtime['deployment']
            previous=commit_file(new,'fence',actions.FENCE_PATH,canonical(value).encode(),previous)
        self.repos[(self.targets['source']['repository'],'fence')]=new
        self.fence['deployment']=self.runtime['deployment']

    def set_digest(self):
        if hasattr(self,'access'): self.runtime['deployment']['public_access_sha256']=digest(self.access)
        super().set_digest()

    def invoke(self,mode='producer'):
        original=h.run;errors=[]
        def observed(*args,**kwargs):
            try: return original(*args,**kwargs)
            except Exception as exc: errors.append(exc);raise
        try:
            with patch.object(h,'run',side_effect=observed): return super().invoke(mode)
        except AssertionError:
            if errors: raise errors[0]
            raise

    def open(self,req,timeout):
        u=urllib.parse.urlsplit(req.full_url);method=req.get_method()
        self.headers.append({'method':method,'url':req.full_url,'has_authorization':bool(req.get_header('Authorization'))})
        if u.netloc=='github.com':
            assert req.get_header('Authorization') is not None
            return super().open(req,timeout)
        parts=u.path.split('/');repo='/'.join(parts[2:4]);tail='/'+('/'.join(parts[4:])) if len(parts)>4 else ''
        self.calls.append((method,repo,tail,u.query))
        if repo=='synthetic/code':
            assert req.get_header('Authorization')=='Bearer '+self.tokens['metadata_read']
        elif method=='GET': assert req.get_header('Authorization')=='Bearer '+self.tokens['metadata_read']
        elif method!='GET':
            role='backup_write' if repo=='synthetic/backup' else 'receipt_write'
            assert repo in ('synthetic/backup','synthetic/receipts')
            assert req.get_header('Authorization')=='Bearer '+self.tokens[role]
        key=(repo,tail)
        if key in self.overrides: return io.BytesIO(canonical(self.overrides[key]).encode())
        if not tail:
            result={'id':self.access['repositories'][repo]['id'],'full_name':repo,'private':False,'visibility':'public'}
        elif tail.startswith('/rules/branches/'):
            page=int(urllib.parse.parse_qs(u.query)['page'][0]);rows=self.rules[(repo,tail.rsplit('/',1)[-1])]
            result=rows[(page-1)*100:page*100]
        elif tail.startswith('/rulesets/'):
            result=self.rulesets[(repo,int(tail.rsplit('/',1)[-1]))]
        else:
            if method=='PATCH' and repo in self.drops:
                self.drops.remove(repo)
                super().open(req,timeout)  # applied exactly once, response lost
                raise TimeoutError('synthetic response loss')
            return super().open(req,timeout)
        return io.BytesIO(canonical(result).encode())


def test_public_cli_pair_and_confirmed_receipt():
    p=PublicProvider('pair');upload,producer=p.invoke();receipt,verifier=p.invoke('verifier')
    assert producer!=verifier and (verifier/'fresh-blocked/RESTORE-BLOCKED.json').is_file()
    assert receipt['verification']['restore_blocked_verified'] is True
    assert receipt['destination']['commit_sha']==upload['destination']['commit_sha']
    # Real fresh download through anonymous tree/blob client, independent of writer memory.
    budget=h.Budget(p.root);c=h.Client(os.environ['GITHUB_TOKEN'],{'synthetic/receipts'},set(),budget);c.access=p.access
    with patch.object(h.Client,'open_request',side_effect=p.open):
        t=p.targets['receipts'];pin=c.ref(t);_,files=c.tree(t,pin)
        raw=c.blob(t,files['receipt.json'])
        assert json.loads(raw)['manifest_sha256']==receipt['manifest_sha256']
        assert h.oid('blob',raw)==receipt['receipt_publication']['blob_sha']
    assert len(p.fetches)==2
    for row in p.headers:
        if row['method']=='GET': assert row['has_authorization']
    for root in (producer,verifier):
        for f in root.rglob('*'):
            if f.is_file(): assert all(t.encode() not in f.read_bytes() for t in p.tokens.values())
    b.write_json(p.root/'PUBLIC-RESULT.json',{'offline_only':True,'upload':upload,'receipt':receipt,
        'headers_without_values':p.headers,'fetches':p.fetches})


def test_public_identity_and_no_permissions_introspection():
    p=PublicProvider('identities')
    for case in ('no-permissions','owner-permissions','private','wrong-id','wrong-name','visibility'):
        t=p.targets['source'];repo=t['repository']
        meta={'id':t['id'],'full_name':repo,'private':False,'visibility':'public'}
        if case=='owner-permissions': meta['permissions']={'admin':True,'push':True}
        if case=='private': meta['private']=True
        if case=='wrong-id': meta['id']+=10
        if case=='wrong-name': meta['full_name']='foreign/repo'
        if case=='visibility': meta['visibility']='private'
        p.overrides[(repo,'')]=meta
        budget=h.Budget(p.root);client=h.Client(os.environ['GITHUB_TOKEN'],{repo},set(),budget);client.access=p.access
        with patch.object(h.Client,'open_request',side_effect=p.open):
            if case in ('no-permissions','owner-permissions'): client.repository(t,False)
            else: fails(ValueError,lambda:client.repository(t,False))
        assert not p.mutations


def test_rule_and_bypass_failures_before_cli_write():
    cases=('missing','changed','disabled','evaluate','wrong-target','missing-review','unresolved-review',
           'visible-bypass','foreign-source','truncated-pagination','hidden-review-changed')
    p=PublicProvider('rules-refusals');baseline=deepcopy((p.access,p.rules,p.rulesets))
    for case in cases:
        p.access,p.rules,p.rulesets=deepcopy(baseline);p.runtime['public_access']=p.access
        t=p.targets['source'];repo=t['repository'];branch=t['branch']
        rows=p.rules[(repo,branch)];rid=rows[0]['ruleset_id'];rs=p.rulesets[(repo,rid)]
        entry=p.access['protections'][repo+'@'+branch];item=entry['rulesets'][str(rid)]
        if case=='missing': rows.clear()
        if case=='changed': rows[0]['parameters']={'changed':True}
        if case in ('disabled','evaluate'): rs['enforcement']=case
        if case=='wrong-target': rs['conditions']['ref_name']['include']=['refs/heads/foreign']
        if case=='missing-review': item.pop('bypass_review')
        if case=='unresolved-review': item['bypass_review']['status']='pending'
        if case=='visible-bypass': rs['bypass_actors']=[{'actor_id':1,'actor_type':'Integration','bypass_mode':'always'}]
        if case=='foreign-source': rows[0]['ruleset_source']='foreign/repo'
        if case=='hidden-review-changed': item['bypass_review']['bypass_actors']=[{'actor_id':1}]
        if case=='truncated-pagination':
            p.rules[(repo,branch)]=[deepcopy(rows[0]) for _ in range(400)]
            entry['active_rules_sha256']=digest(p.rules[(repo,branch)])
        p.set_digest()
        with p.context(): assert h.cli(['producer'])==20,case
        assert not p.mutations and not p.fetches,case
        assert not list(p.root.glob('btc-producer-*/confirmed.json'))
    # Full pagination succeeds when the 101st rule and terminal page are verified.
    p=PublicProvider('rules-pagination-ok');t=p.targets['source'];key=(t['repository'],t['branch'])
    rows=p.rules[key];p.rules[key]=rows+[deepcopy(rows[0]) for _ in range(98)]
    p.access['protections']['@'.join(key)]['active_rules_sha256']=digest(p.rules[key]);p.set_digest()
    c=h.Client(os.environ['GITHUB_TOKEN'],{key[0]},set(),h.Budget(p.root));c.access=p.access
    with patch.object(h.Client,'open_request',side_effect=p.open): c.protected(t)
    assert any(q=='per_page=100&page=2' for _,_,_,q in p.calls)


def test_writer_review_separation_and_no_secret_read_cycle():
    p=PublicProvider('credentials');baseline=deepcopy(p.access)
    for case in ('missing-review','broad-review','same-reference','same-token','foreign-writer','reader-secret','sender-secret'):
        p.access=deepcopy(baseline);p.runtime['public_access']=p.access
        r=p.access['credential_reviews']['backup_write']
        if case=='missing-review': r['status']='pending'
        if case=='broad-review': r['other_repository_write']=True;r['sha256']=public.review_hash(r)
        if case=='same-reference': r['credential_reference']='OFFLINE-receipt_write';r['sha256']=public.review_hash(r)
        p.set_digest()
        with p.context():
            if case=='same-token': os.environ[h.ENV['backup_write']]=p.tokens['metadata_read']
            if case=='foreign-writer': os.environ[h.ENV['receipt_write']]=p.tokens['receipt_write']
            if case=='reader-secret': os.environ['BTC_HOSTED_SOURCE_READ_TOKEN']='synthetic-forbidden'
            if case=='sender-secret': os.environ['BTC_DELIVERY_GITHUB_TOKEN']='synthetic-forbidden'
            assert h.cli(['producer'])==20,case
        assert not p.mutations and not p.fetches
    root=OUT/'client-scope';root.mkdir();c=h.Client(os.environ['GITHUB_TOKEN'],{'synthetic/backup'},set(),h.Budget(root))
    fails(ValueError,lambda:c.request('POST','synthetic/backup','/git/blobs',{}))
    fails(ValueError,lambda:c.request('GET','foreign/repo',''))


def test_lost_response_exact_readback_without_retry():
    p=PublicProvider('lost-response');p.drops={'synthetic/backup','synthetic/receipts'}
    p.invoke();p.invoke('verifier')
    patches=[row for row in p.calls if row[0]=='PATCH']
    assert len(patches)==2 and len({row[1] for row in patches})==2
    assert all(row[3]['force'] is False for row in p.mutations if row[0]=='PATCH')
    p=PublicProvider('lost-unapplied');original=p.open
    def lost(req,timeout):
        if req.get_method()=='PATCH':
            p.calls.append(('PATCH','synthetic/backup','lost',''));raise TimeoutError()
        return original(req,timeout)
    p.open=lost
    with p.context(): assert h.cli(['producer'])==20
    assert sum(row[0]=='PATCH' for row in p.calls)==1
    assert not list(p.root.glob('btc-producer-*/confirmed.json'))


def test_anonymous_client_paths_headers_bytes_and_wall_deadline():
    root=OUT/'read-limits';root.mkdir();seen=[]
    def reply(req,timeout):
        seen.append(req);assert req.get_header('Authorization') is not None
        return io.BytesIO(b'{}')
    budget=h.Budget(root);c=h.Client(os.environ['GITHUB_TOKEN'],{'synthetic/data'},set(),budget)
    with patch.object(h.Client,'open_request',side_effect=reply):
        c.request('GET','synthetic/data','/git/blobs/'+'a'*40)
        for tail in ('/issues','/contents/../secret?ref='+'a'*40,'/git/blobs/'+'a'*40+'?evil=1'):
            fails(ValueError,lambda:c.request('GET','synthetic/data',tail))
        fails(ValueError,lambda:c.request('GET','synthetic/data','',limit=h.MAX_RESPONSE+1))
        budget.http=h.MAX_HTTP;fails(ValueError,lambda:c.request('GET','synthetic/data',''))
        budget.http=0;budget.transfer=h.MAX_TRANSFER;fails(ValueError,lambda:c.request('GET','synthetic/data',''))
    data=pages.ReadClient(os.environ['GITHUB_TOKEN'],'synthetic/data',{'stream':github.STORE_PATH})
    with patch.object(pages.ReadClient,'open_request',side_effect=reply):
        for _ in range(4):
            try:data.read('synthetic/data','stream')
            except ValueError as exc:assert str(exc)=='Git packet header'
            else:raise AssertionError('Malformed Git advertisement accepted')
        assert data.gets==4
        fails(github.StoreUnavailable,lambda:data._request('POST','/repos/synthetic/data/x',{}))
        data.gets=12;fails(github.StoreUnavailable,lambda:data.read('synthetic/data','stream'))
    fails(ValueError,lambda:pages.ReadClient('synthetic-forbidden','synthetic/data',{}))
    m=monitor.Reader(os.environ['GITHUB_TOKEN'],['synthetic/data'],ReadBudget())
    with patch.object(monitor.Reader,'open_request',side_effect=reply):
        m._request('GET','/repos/synthetic/data/git/blobs/'+'a'*40)
        fails(github.StoreUnavailable,lambda:m._request('GET','/repos/foreign/data/git/blobs/'+'a'*40))
        fails(github.StoreUnavailable,lambda:m._request('DELETE','/repos/synthetic/data/git/blobs/'+'a'*40))
        m.budget.requests=64;fails(github.StoreUnavailable,lambda:m._request('GET','/repos/synthetic/data'))
    class Slow(io.BytesIO):
        def read(self,*args): time.sleep(.2);return b'{}'
    c=h.Client(os.environ['GITHUB_TOKEN'],{'synthetic/data'},set(),h.Budget(root));began=time.monotonic()
    with patch.object(h,'REQUEST_SECONDS',.05),patch.object(h.Client,'open_request',return_value=Slow()):
        fails(RuntimeError,lambda:c.request('GET','synthetic/data',''))
    assert time.monotonic()-began<.18
    c=h.Client(os.environ['GITHUB_TOKEN'],{'synthetic/data'},set(),h.Budget(root))
    with patch.object(h.Client,'open_request',return_value=io.BytesIO(b'x'*5)):
        fails(ValueError,lambda:c.request('GET','synthetic/data','',limit=4))
    # Existing process helper strips all injected secrets before any Git child.
    original=b.subprocess.Popen;children=[]
    def popen(*args,**kwargs):
        env=kwargs['env'];assert not any('TOKEN' in k or 'SECRET' in k for k in env)
        assert all('synthetic-hidden' not in str(v) for v in (args,kwargs))
        children.append(1);return original(*args,**kwargs)
    with patch.dict(os.environ,{'GITHUB_TOKEN':'synthetic-hidden','BTC_HOSTED_BACKUP_WRITE_TOKEN':'synthetic-hidden'}),patch.object(b.subprocess,'Popen',side_effect=popen):
        b.git(ROOT,b.Budget(),'rev-parse','HEAD')
    assert children


def test_disabled_overlay_and_original_process_correction():
    from p4_install_hosted_templates import materialize
    pins=materialize(OUT/'overlay')
    assert len(pins)==7
    for path in pins:
        text=(OUT/'overlay'/path).read_text()
        assert 'if: ${{ false }}' in text and 'queue: max' in text
        assert 'actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683' in text
        assert 'persist-credentials: false' in text and 'Require Git and stop checkout network after any Git failure' in text
        assert 'GITHUB_TOKEN: ${{ github.token }}' in text
        assert not any(v in text for v in ('secrets.BTC_HOSTED_SOURCE_READ_TOKEN','secrets.BTC_PAGES_STORE_READ_TOKEN','secrets.BTC_MONITOR_'))
    # Directly compare inherited process-count implementation bytes to exact base.
    import subprocess
    base=subprocess.check_output(['git','show','9a458483f56244882954f7d2bb40b6ab5cae2128:tools/p3_backup_chain.py'],cwd=ROOT)
    import ast
    def guarded(source):
        source=source.decode().replace('\r\n','\n')
        return {node.name:ast.get_source_segment(source,node) for node in ast.parse(source).body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in ('process','ProcessTree','Budget','rss','windows_job_api','windows_memory_api')}
    assert guarded(base)==guarded((ROOT/'tools/p3_backup_chain.py').read_bytes())
    for name in ('public-access','hosted-backup-runtime','github-actions-runtime','pages-runtime','monitor-runtime'):
        value=json.loads((ROOT/'ops/produktion'/f'{name}.disabled.json').read_text())
        assert value['enabled'] is False
        access=value if name=='public-access' else value['public_access']
        assert all(t['id'] is None and t['visibility']=='public' for t in access['repositories'].values())


def test_sender_and_pages_actual_entry_share_public_bindings():
    from test_betriebsabschluss import actual_entry
    from test_actions_delivery import invoke
    from production_confirmation import ProductionContentsClient
    import telegram_notify as telegram
    @contextmanager
    def retained_temp(*args,**kwargs):
        folder=Path(tempfile.mkdtemp(prefix='sender-pages-',dir=OUT));yield str(folder)
    with patch.object(tempfile,'TemporaryDirectory',side_effect=retained_temp),actual_entry() as (root,data,path,runtime,http,meta,slot):
        repo=runtime['private_store_repository'];branches=[runtime['store_branch'],runtime['fence_branch']]
        repos={repo:{'id':51,'visibility':'public','branches':branches},
               'synthetic/code':{'id':52,'visibility':'public','branches':['synthetic']}}
        access,rules,sets=access_for(repos);writer_review(access,'sender_write',repo,branches)
        runtime['public_access']=access;runtime['public_access_sha256']=digest(access)
        value=json.loads(http.file(actions.FENCE_PATH));value['deployment']=sender.deployment(runtime)
        head=http.state['heads'][runtime['fence_branch']]
        http.state['history'][head][actions.FENCE_PATH]=canonical(value)
        path.write_text(canonical(runtime),encoding='utf-8')
        original=actions.ActionsClient.open_request;seen=[]
        def reply(req,timeout):
            u=urllib.parse.urlsplit(req.full_url);parts=u.path.split('/');r='/'.join(parts[2:4]);tail='/'+('/'.join(parts[4:])) if len(parts)>4 else ''
            seen.append((req.get_method(),r,tail,bool(req.get_header('Authorization'))))
            if r=='synthetic/code': assert req.get_header('Authorization')=='Bearer synthetic-codejob'
            elif req.get_method()=='GET': assert req.get_header('Authorization') is not None
            else: assert req.get_header('Authorization')=='Bearer synthetic-only'
            if not tail: value={'id':repos[r]['id'],'full_name':r,'private':False,'visibility':'public'}
            elif '/rules/branches/' in tail: value=rules[(r,tail.rsplit('/',1)[-1])]
            elif '/rulesets/' in tail: value=sets[(r,int(tail.rsplit('/',1)[-1]))]
            else: return original(req,timeout=timeout)
            return io.BytesIO(canonical(value).encode())
        with patch.dict(os.environ,{'GITHUB_TOKEN':'synthetic-codejob'}),patch.object(actions.ActionsClient,'open_request',side_effect=reply),patch.object(telegram,'deliver_telegram',side_effect=AssertionError('No real send')):
            missing=deepcopy(runtime);missing['public_access']['credential_reviews']['sender_write']['status']='pending'
            path.write_text(canonical(missing),encoding='utf-8');fails(ValueError,lambda:invoke(path,data));assert http.puts==0
            path.write_text(canonical(runtime),encoding='utf-8');result=invoke(path,data)
            assert result['get']<=640 and result['put']<=50
            assert json.loads(http.file(actions.FENCE_PATH))['phase']=='closed'
        pr={'schema':pages.SCHEMA,'enabled':True,'workflow':pages.WORKFLOW,'deployment_schema':actions.POLICY,
            'deployment':sender.deployment(runtime),'public_access':access}
        pp=root/'pages-runtime.json';pp.write_text(canonical(pr),encoding='utf-8');out=root/'public'
        stamp=json.loads(http.file(github.STORE_PATH))['snapshot']['engine']['last_signal_ts']
        before=http.puts
        with patch.dict(os.environ,{'GITHUB_TOKEN':'synthetic-codejob','BTC_DELIVERY_GITHUB_TOKEN':'','TELEGRAM_BOT_TOKEN':'','GITHUB_WORKFLOW_REF':'synthetic/code/'+pages.WORKFLOW+'@refs/heads/synthetic'}),\
             patch.object(pages,'check_code_pin'),patch.object(pages.ReadClient,'open_request',side_effect=reply),\
             patch.object(ProductionContentsClient,'open_request',side_effect=reply),\
             patch.object(pages.time,'time',return_value=(stamp+14400000+1000)/1000):
            exported=pages.export(pp,data/'config.json',out)
            assert exported['get']==6 and exported['preflight_get']==5
            assert pages.export(pp,data/'config.json',out,verify=out.with_suffix('.receipt.json'))['get']==6
        assert http.puts==before
        b.write_json(OUT/'SENDER-PAGES.json',{'offline_only':True,'sender':result,'pages':exported,'headers_without_values':seen})


def test_short_page_with_next_or_foreign_link_is_refused():
    repo='synthetic/data';branch='stream';access,rules,sets=access_for({repo:{'id':1,'visibility':'public','branches':[branch]}})
    fails(ValueError,lambda:public.deployment(access,{'public_access_sha256':'0'*64}))
    class Response(io.BytesIO):
        def __init__(self,raw,link): super().__init__(raw);self.headers={'Link':link}
    root=OUT/'pagination-headers';root.mkdir();c=h.Client(os.environ['GITHUB_TOKEN'],{repo},set(),h.Budget(root));c.access=access
    for url in ('https://api.github.com/repos/synthetic/data/rules/branches/stream?per_page=100&page=2',
                'https://api.github.com/repos/foreign/repo/rules/branches/stream?per_page=100&page=2'):
        with patch.object(h.Client,'open_request',return_value=Response(canonical(rules[(repo,branch)]).encode(),'<'+url+'>; rel="next"')):
            fails(ValueError,lambda:c.protected({'repository':repo,'id':1,'branch':branch}))


def test_public_checkout_real_pack_and_no_git_secret():
    import public_code_checkout as code
    from test_hosted_backup import empty_repo
    from test_betriebsabschluss import commit_file
    root=OUT/'code-bootstrap';root.mkdir();source=root/'source';base=empty_repo(source,'main')
    pin=commit_file(source,'main','README.md',b'public synthetic code\n',base)
    with b.process(source,['pack-objects','--stdout','--revs'],b.Budget()) as proc:
        proc.stdin.write((pin+'\n').encode());proc.stdin.close();pack=proc.stdout.read(64*h.MIB+1)
    def pkt(raw): return f'{len(raw)+4:04x}'.encode()+raw
    advertisement=pkt(b'# service=git-upload-pack\n')+b'0000'+pkt((pin+' refs/heads/main\0side-band-64k no-progress\n').encode())+b'0000'
    payload=pkt(b'NAK\n')+b''.join(pkt(b'\x01'+pack[i:i+65500]) for i in range(0,len(pack),65500))+b'0000'
    calls=[];children=[];real_popen=b.subprocess.Popen
    class HTTP:
        def open(self,req,timeout):
            assert req.get_header('Authorization') is None and timeout<=15
            calls.append((req.get_method(),req.full_url))
            if req.full_url.startswith('https://api.github.com/'):
                return io.BytesIO(canonical({'id':987,'full_name':code.REPOSITORY,'private':False,'visibility':'public'}).encode())
            if req.get_method()=='GET': return io.BytesIO(advertisement)
            assert req.full_url=='https://github.com/'+code.REPOSITORY+'.git/git-upload-pack'
            assert (b'want '+pin.encode()+b' ') in req.data
            return io.BytesIO(payload)
    def popen(*args,**kwargs):
        assert not any('TOKEN' in k or 'SECRET' in k for k in kwargs['env'])
        assert 'synthetic-hidden' not in str((args,kwargs));children.append(1)
        return real_popen(*args,**kwargs)
    workspace=root/'workspace';workspace.mkdir();before=Path.cwd()
    try:
        os.chdir(workspace)
        env={'GITHUB_REPOSITORY':code.REPOSITORY,'BTC_PUBLIC_CODE_SHA':pin,'BTC_PUBLIC_CODE_REPOSITORY_ID':'987',
             'GITHUB_TOKEN':'synthetic-hidden','RUNNER_TEMP':str(root)}
        with patch.dict(os.environ,env),patch.object(code.platform,'system',return_value='Linux'),\
             patch.object(code.urllib.request,'build_opener',return_value=HTTP()),patch.object(code.subprocess,'Popen',side_effect=popen):
            assert code.cli()==0
            assert (workspace/'README.md').read_bytes()==b'public synthetic code\n'
            assert b.git(workspace,b.Budget(),'rev-parse','HEAD').decode().strip()==pin
            assert code.cli()==20  # existing checkout cannot be overwritten
        assert len(calls)==3 and sum(m=='POST' for m,_ in calls)==1 and len(children)>=4
    finally: os.chdir(before)
    bootstrap=(ROOT/'tools/public_code_checkout.py').read_text()
    for kind in ('signal','watch','lage','pages','backup','backup-verify','monitor'):
        raw=(ROOT/'ops/produktion'/f'{kind}-workflow.disabled.yml').read_text()
        assert 'actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683' in raw
        assert 'persist-credentials: false' in raw and 'fetch-depth: 1' in raw


def test_preflight_cli_anonymous_and_monitor_receipt_readback():
    import p4_public_preflight as preflight
    from production_confirmation import ProductionContentsClient
    p=PublicProvider('monitor-pair');p.invoke();receipt,_=p.invoke('verifier')
    access=deepcopy(p.access)
    # Four exact operating branches only, excluding immutable migration/code branches.
    protected=[p.targets['source']['repository']+'@'+p.targets['source']['branch'],
        p.targets['source']['repository']+'@fence','synthetic/backup@packages','synthetic/receipts@receipts']
    access['protections']={k:v for k,v in access['protections'].items() if k in protected}
    access['repositories'].pop('synthetic/code')  # this preflight is anonymous, even code metadata if included
    path=p.root/'access.json';path.write_text(canonical(access),encoding='utf-8')
    with patch.object(ProductionContentsClient,'open_request',side_effect=p.open):
        assert preflight.cli(['--review',str(path),'--out',str(p.root/'read-preflight'),'--public-read'])==0
    assert not list((p.root/'read-preflight').glob('REFUSED*'))
    policy={'deployment':p.runtime['deployment'],'backup_target':{**p.targets['backup'],'manifest_prefix':'manifests/'},
        'independent_verifier':{'repository':'synthetic/receipts','receipt_branch':'receipts','receipt_path':'receipt.json',
            'binding':{k:p.runtime['verifier'][k] for k in ('repository','workflow','branch','code_sha')}},
        'first_start_ms':{'backup':p.slot}}
    def http(req,timeout):
        u=urllib.parse.urlsplit(req.full_url)
        if '/contents/' in u.path and '/synthetic/code/' not in u.path:
            assert req.get_header('Authorization') is not None
            parts=u.path.split('/');repo='/'.join(parts[2:4]);name=u.path.split('/contents/')[1]
            pin=urllib.parse.parse_qs(u.query)['ref'][0];local=p.repo(repo,pin)
            with b.batch(local,b.Budget()) as read: raw=read(pin+':'+name,'blob',b.MAX_MANIFEST)
            return io.BytesIO(canonical({'type':'file','encoding':'base64','sha':h.oid('blob',raw),'content':base64.b64encode(raw).decode()}).encode())
        if '/attempts/1/jobs' in u.path:
            assert req.get_header('Authorization')=='Bearer '+p.tokens['metadata_read']
            return io.BytesIO(canonical({'total_count':1,'jobs':[{'run_id':200,'run_attempt':1,
                'head_sha':p.runtime['verifier']['code_sha'],'status':'completed','conclusion':'success'}]}).encode())
        return p.open(req,timeout)
    budget=ReadBudget();before=len(p.mutations)
    with patch.object(monitor.Reader,'open_request',side_effect=http):
        data=monitor.Reader(os.environ['GITHUB_TOKEN'],['synthetic/backup','synthetic/receipts'],budget)
        code=monitor.Reader(p.tokens['metadata_read'],['synthetic/code'],budget,metadata=True)
        result,_,_=monitor.read_backup(data,code,policy,p.slot+60000)
        assert result['manifest_sha256']==receipt['manifest_sha256'] and budget.requests<=64
        fails(ValueError,lambda:monitor.read_backup(data,code,policy,p.slot+26*60*60*1000+1))
    assert len(p.mutations)==before
    b.write_json(p.root/'MONITOR-RESULT.json',{'offline_only':True,'get':budget.requests,'mutations':0,'receipt_sha256':digest(receipt['manifest'])})


def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--only',nargs='*');a=parser.parse_args()
    OUT=Path(a.out).resolve();OUT.mkdir(exist_ok=False)
    results=[]
    for name,fn in list(globals().items()):
        if name.startswith('test_') and callable(fn):
            if a.only and name not in a.only: continue
            try:
                import socket
                with patch.object(socket.socket,'connect',side_effect=AssertionError('Offline test forbids network')): fn()
                results.append({'test':name,'passed':True});print('PASS',name,flush=True)
            except Exception: traceback.print_exc();results.append({'test':name,'passed':False});print('FAIL',name,flush=True)
    b.write_json(OUT/'RESULTS.json',{'offline_only':True,'provider_proof':False,'results':results})
    return 0 if all(v['passed'] for v in results) else 1


if __name__=='__main__': sys.exit(main())
