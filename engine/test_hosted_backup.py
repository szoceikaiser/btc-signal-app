"""Focused offline hosted CLI/REST/Git transport evidence, no provider access."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime,timezone
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import urllib.error
import urllib.parse
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'engine')]
import p4_hosted_backup as h
import p3_backup_chain as b
import p4_backup_pair as pair
import p3_capacity_fixture as capacity
import produktion_actions_runner as entry
import actions_delivery as actions
import actions_schedule as slots
import github_delivery as github
import durable_delivery as durable
import actions_freshness as freshness
from production_contract import canonical,digest
from test_betriebsabschluss import commit_file
from test_github_delivery import fails
from github_freshness import ReadBudget,iso

ARTIFACT_ROOT=None


def write_object(repo,kind,raw):
    with b.process(repo,['hash-object','-w','-t',kind,'--stdin'],b.Budget()) as proc:
        proc.stdin.write(raw);proc.stdin.close();pin=proc.stdout.readline().decode().strip()
    assert pin==h.oid(kind,raw)
    return pin


def write_tree(repo,files):
    node={}
    for path,item in files.items():
        cur=node;parts=path.split('/')
        for part in parts[:-1]: cur=cur.setdefault(part,{})
        cur[parts[-1]]=item['sha']
    def tree(cur):
        entries=[]
        for name,value in cur.items():
            folder=isinstance(value,dict);sha=tree(value) if folder else value
            entries.append((name+('/' if folder else ''),('40000' if folder else '100644').encode()+b' '+name.encode()+b'\0'+bytes.fromhex(sha)))
        return write_object(repo,'tree',b''.join(raw for _,raw in sorted(entries)))
    pin=tree(node);assert pin==h.tree_oid(files);return pin


def empty_repo(repo,branch):
    repo.mkdir();b.git(repo,b.Budget(),'init','--bare')
    tree=write_tree(repo,{})
    raw=f'tree {tree}\nauthor Offline <offline@example.invalid> 1700000000 +0000\ncommitter Offline <offline@example.invalid> 1700000000 +0000\n\nempty\n'.encode()
    pin=write_object(repo,'commit',raw);b.git(repo,b.Budget(),'update-ref','refs/heads/'+branch,pin)
    return pin


class Provider:
    """GitDB HTTP fake backed by real, separate local Git object databases."""
    def __init__(self,root,mode='closed'):
        self.root=Path(root);self.root.mkdir();self.seen=[];self.mutations=[];self.fetches=[];self.fault=None
        self.fixture=capacity.create(self.root/'fixture',simple_count=3);identity=self.fixture['identity']
        sr=Path(self.fixture['source']);pin=self.fixture['pins'][-1]['pin']
        with b.batch(sr,b.Budget()) as read: _,stream_raw,env=b.inspect(read,pin,identity,b.parser(identity))
        runtime=json.loads((ROOT/'ops/produktion/github-actions-runtime.disabled.json').read_text())
        c=env['snapshot']['control'];runtime.update(code_repository='synthetic/code',code_ref='refs/heads/synthetic',
            private_store_repository=identity['repo'],store_branch=identity['branch'],fence_branch='fence',store_id=identity['store_id'],
            code_sha=c['code_sha'],config_sha256=c['config_sha256'],bot_identity=c['bot_identity'],activation_review_sha256='b'*64)
        d=entry.deployment(runtime);fence=json.loads(actions.seed_fence(d));fr=self.root/'fence'
        fpin=commit_file(fr,'fence',actions.FENCE_PATH,canonical(fence).encode())
        self.slot=1791072000000  # immutable midnight UTC obligation
        run={'number':1,'id':'10','attempt':'1','workflow':'.github/workflows/signal.yml','kind':'signal',
             'expected_start_ms':str(self.slot+2*slots.MINUTE),'deadline_utc_ms':self.slot+45*slots.MINUTE}
        fence.update(phase='open',run=run,completion=None,write_id='offline-open')
        fence['cursors'][run['workflow']]={'number':1,'id':'10'}
        fpin=commit_file(fr,'fence',actions.FENCE_PATH,canonical(fence).encode(),fpin)
        if mode=='closed':
            fence.update(phase='closed',completion={'stream':{'adapter':'github',**identity,'repo':identity['repo'],
                'branch':identity['branch'],'path':github.STORE_PATH,'commit_sha':pin,'revision':env['revision'],
                'blob_sha':h.oid('blob',stream_raw),'snapshot_digest':env['body_digest']}})
            fence['completion']['stream'].pop('stream_id')
            fpin=commit_file(fr,'fence',actions.FENCE_PATH,canonical(fence).encode(),fpin)
        self.fence=fence
        self.targets={'source':{'repository':identity['repo'],'id':1,'branch':identity['branch']},
                      'backup':{'repository':'synthetic/backup','id':2,'branch':'packages'},
                      'receipts':{'repository':'synthetic/receipts','id':3,'branch':'receipts'}}
        self.repos={(identity['repo'],identity['branch']):sr,(identity['repo'],'fence'):fr}
        for key in ('backup','receipts'):
            target=self.targets[key];repo=self.root/key;empty_repo(repo,target['branch'])
            self.repos[(target['repository'],target['branch'])]=repo
        mig=self.root/'migration-git';mig.mkdir();b.git(mig,b.Budget(),'init','--bare')
        files={}
        for path in sorted(Path(self.fixture['migration']).rglob('*')):
            if path.is_file():
                raw=path.read_bytes();files[path.relative_to(self.fixture['migration']).as_posix()]={'sha':write_object(mig,'blob',raw),'bytes':len(raw)}
        tree=write_tree(mig,files)
        raw=f'tree {tree}\nauthor Offline <offline@example.invalid> 1700000000 +0000\ncommitter Offline <offline@example.invalid> 1700000000 +0000\n\nmigration\n'.encode()
        mp=write_object(mig,'commit',raw);b.git(mig,b.Budget(),'update-ref','refs/heads/migration',mp)
        self.repos[(identity['repo'],'migration')]=mig
        self.yaml={w:('reviewed offline '+w+'\n').encode() for w in ('.github/workflows/backup.yml','.github/workflows/backup-verify.yml')}
        self.runtime={'schema':h.SCHEMA,'enabled':True,**self.targets,'deployment':d,'identity':identity,
            'pins':None,'activation_review_sha256':'c'*64,'runner_os':'Linux','python_version':list(sys.version_info[:3]),
            'migration':{'target':{**self.targets['source'],'branch':'migration'},'commit_sha':mp,'tree_sha':tree,'files':files}}
        for kind,w in (('producer','.github/workflows/backup.yml'),('verifier','.github/workflows/backup-verify.yml')):
            self.runtime[kind]={'repository':'synthetic/code','repository_id':4,'branch':'synthetic','code_sha':d['code_sha'],
                               'workflow':w,'workflow_sha256':hashlib.sha256(self.yaml[w]).hexdigest()}
        self.set_digest();self.metadata={}
        for kind,rid in (('producer','100'),('verifier','200')):
            v=self.runtime[kind]
            self.metadata[rid]={'id':int(rid),'run_number':1,'run_attempt':1,'repository':{'full_name':'synthetic/code','id':4},
                'head_sha':v['code_sha'],'head_branch':'synthetic','path':v['workflow'],'event':'workflow_dispatch',
                'display_title':'btc-v2:backup:created','created_at':iso(self.slot+1000),
                'updated_at':iso(self.slot+60000),'status':'completed','conclusion':'success'}
        self.tokens={r:'offline-'+r for r in h.ENV};self.permissions={}
        for role in h.ENV:
            for target in self.targets.values():
                repo=target['repository'];write=(role=='backup_write' and repo=='synthetic/backup') or (role=='receipt_write' and repo=='synthetic/receipts')
                self.permissions[(self.tokens[role],repo)]={'pull':True,'push':write,'admin':False,'maintain':False}
        self.original_process=b.process

    def set_digest(self):
        self.runtime['runtime_sha256']=digest({k:v for k,v in self.runtime.items() if k!='runtime_sha256'})

    def repo(self,name,pin=None,branch=None):
        if branch: return self.repos[(name,branch)]
        for (r,_),repo in self.repos.items():
            if r==name:
                try: b.git(repo,b.Budget(),'cat-file','-e',pin);return repo
                except ValueError: pass
        raise ValueError('Synthetic object missing')

    def tree_files(self,repo,pin):
        tree=b.git(repo,b.Budget(),'rev-parse',pin+'^{tree}').decode().strip();items={}
        rows=b.git(repo,b.Budget(),'ls-tree','-r','-l',tree).decode().splitlines()
        for row in rows:
            header,name=row.split('\t');mode,kind,sha,size=header.split();items[name]={'sha':sha,'bytes':int(size)}
        return tree,items

    def open(self,req,timeout):
        url=urllib.parse.urlparse(req.full_url)
        if url.netloc=='github.com':
            repo=url.path.split('.git/',1)[0].removeprefix('/')
            auth=base64.b64decode(req.get_header('Authorization').removeprefix('Basic ')).decode()
            assert auth=='x-access-token:'+self.tokens['source_read']
            def pkt(raw): return f'{len(raw)+4:04x}'.encode()+raw
            if req.get_method()=='GET':
                rows=[(branch,pair.head(local,branch,b.Budget())) for (name,branch),local in self.repos.items() if name==repo]
                body=pkt(b'# service=git-upload-pack\n')+b'0000'
                for i,(branch,pin) in enumerate(rows):
                    body+=pkt((pin+' refs/heads/'+branch+('\0side-band-64k ofs-delta no-progress' if i==0 else '')+'\n').encode())
                return io.BytesIO(body+b'0000')
            assert req.get_method()=='POST' and url.path.endswith('/git-upload-pack')
            want=req.data[4:].split()[1].decode();local=self.repo(repo,want)
            branch=next(branch for (name,branch),candidate in self.repos.items() if name==repo and candidate==local)
            self.fetches.append((repo,branch,want))
            with self.original_process(local,['pack-objects','--stdout','--revs'],b.Budget()) as proc:
                proc.stdin.write((want+'\n').encode());proc.stdin.close();raw=proc.stdout.read(64*h.MIB+1)
            assert len(raw)<=64*h.MIB
            body=pkt(b'NAK\n')
            for i in range(0,len(raw),65500): body+=pkt(b'\x01'+raw[i:i+65500])
            return io.BytesIO(body+b'0000')
        assert url.netloc=='api.github.com'
        method=req.get_method();path=urllib.parse.unquote(url.path);parts=path.split('/');repo='/'.join(parts[2:4]);tail='/'+('/'.join(parts[4:])) if len(parts)>4 else ''
        token=req.get_header('Authorization').removeprefix('Bearer ');assert token in self.tokens.values()
        self.seen.append((method,repo,tail));payload=json.loads(req.data) if req.data else None
        if method!='GET': self.mutations.append((method,repo,tail,payload))
        if self.fault: self.fault(self,method,repo,tail,payload)
        if not tail:
            t=next(t for t in self.targets.values() if t['repository']==repo)
            result={'id':t['id'],'full_name':repo,'private':True,'permissions':self.permissions[(token,repo)]}
        elif tail.endswith('/protection'):
            result={k:{'enabled':v} for k,v in (('allow_force_pushes',False),('allow_deletions',False),('enforce_admins',True),('required_linear_history',True))}
        elif tail.startswith('/actions/runs/'):
            result=self.metadata[tail.rsplit('/',1)[-1]]
        elif tail.startswith('/contents/'):
            name=tail.removeprefix('/contents/');raw=self.yaml[name]
            result={'type':'file','encoding':'base64','content':base64.b64encode(raw).decode(),'sha':h.oid('blob',raw)}
        elif tail.startswith('/compare/'):
            base,head=tail.removeprefix('/compare/').split('...');local=self.repo(repo,head)
            ancestor=b.git(local,b.Budget(),'merge-base',base,head).decode().strip()
            result={'base_commit':{'sha':base},'merge_base_commit':{'sha':ancestor},'status':'identical' if base==head else 'ahead'}
        elif tail.startswith('/git/ref/heads/'):
            branch=tail.removeprefix('/git/ref/heads/');local=self.repo(repo,branch=branch)
            pin=pair.head(local,branch,b.Budget());result={'ref':'refs/heads/'+branch,'object':{'type':'commit','sha':pin}}
        elif tail.startswith('/git/commits/'):
            pin=tail.rsplit('/',1)[-1];local=self.repo(repo,pin)
            with b.batch(local,b.Budget()) as read: raw=read(pin,'commit',16384)
            headers=raw.split(b'\n\n',1)[0].splitlines()
            result={'sha':pin,'tree':{'sha':next(x[5:].decode() for x in headers if x.startswith(b'tree '))},
                    'parents':[{'sha':x[7:].decode()} for x in headers if x.startswith(b'parent ')]}
        elif tail.startswith('/git/trees/'):
            pin=tail.rsplit('/',1)[-1];local=self.repo(repo,pin);_,files=self.tree_files(local,pin)
            result={'sha':pin,'truncated':False,'tree':[{'path':n,'type':'blob','mode':'100644','sha':v['sha'],'size':v['bytes']} for n,v in files.items()]}
        elif tail.startswith('/git/blobs/'):
            pin=tail.rsplit('/',1)[-1];local=self.repo(repo,pin)
            with b.batch(local,b.Budget()) as read: raw=read(pin,'blob',b.MAX_PACKAGE)
            result={'sha':pin,'size':len(raw),'encoding':'base64','content':base64.b64encode(raw).decode()}
        elif method=='POST' and tail=='/git/blobs':
            local=self.repo(repo,branch=self.targets['backup' if repo=='synthetic/backup' else 'receipts']['branch'])
            result={'sha':write_object(local,'blob',base64.b64decode(payload['content']))}
        elif method=='POST' and tail=='/git/trees':
            local=self.repo(repo,payload['base_tree']);_,files=self.tree_files(local,payload['base_tree'])
            for v in payload['tree']:
                raw=b.git(local,b.Budget(),'cat-file','blob',v['sha']);files[v['path']]={'sha':v['sha'],'bytes':len(raw)}
            result={'sha':write_tree(local,files)}
        elif method=='POST' and tail=='/git/commits':
            local=self.repo(repo,payload['tree']);a=payload['author'];stamp=int(datetime.fromisoformat(a['date'].replace('Z','+00:00')).timestamp())
            raw=f"tree {payload['tree']}\nparent {payload['parents'][0]}\nauthor {a['name']} <{a['email']}> {stamp} +0000\ncommitter {a['name']} <{a['email']}> {stamp} +0000\n\n{payload['message']}\n".encode()
            result={'sha':write_object(local,'commit',raw)}
        elif method=='PATCH' and tail.startswith('/git/refs/heads/'):
            assert payload['force'] is False
            branch=tail.removeprefix('/git/refs/heads/');local=self.repo(repo,branch=branch);old=pair.head(local,branch,b.Budget())
            try: b.git(local,b.Budget(),'merge-base','--is-ancestor',old,payload['sha'])
            except ValueError: raise urllib.error.HTTPError(req.full_url,422,'CAS conflict',{},None)
            b.git(local,b.Budget(),'update-ref','refs/heads/'+branch,payload['sha'],old)
            result={'object':{'sha':payload['sha']}}
            if self.fault=='lost': raise TimeoutError('offline lost response')
        else: raise AssertionError((method,tail))
        return io.BytesIO(canonical(result).encode())

    @contextmanager
    def context(self,mode='producer',runtime=None):
        runtime=runtime or self.runtime;binding=runtime[mode];rid='100' if mode=='producer' else '200'
        env={'GITHUB_REPOSITORY':binding['repository'],'GITHUB_REF':'refs/heads/'+binding['branch'],
             'GITHUB_WORKFLOW_REF':binding['repository']+'/'+binding['workflow']+'@refs/heads/'+binding['branch'],
             'GITHUB_SHA':binding['code_sha'],'GITHUB_RUN_ID':rid,'GITHUB_RUN_NUMBER':'1','GITHUB_RUN_ATTEMPT':'1',
             'GITHUB_EVENT_NAME':'workflow_dispatch','RUNNER_OS':'Linux','RUNNER_TEMP':str(self.root),
             'BTC_HOSTED_RUNTIME_JSON':canonical(runtime),'BTC_HOSTED_RUNTIME_SHA256':runtime['runtime_sha256']}
        env.update({h.ENV[r]:self.tokens[r] for r in h.ROLES[mode]})
        for r in set(h.ENV)-set(h.ROLES[mode]): env[h.ENV[r]]=''
        with patch.dict(os.environ,env),patch.object(h,'check_code_pin'),patch.object(h.Client,'open_request',side_effect=self.open),\
             patch.object(h.time,'time',return_value=(self.slot+10000)/1000),\
             patch.object(h.platform,'system',return_value='Linux'):
            yield

    def invoke(self,mode='producer'):
        with self.context(mode):
            assert h.cli([mode])==0
        roots=sorted(self.root.glob('btc-'+mode+'-*'),key=lambda p:p.stat().st_mtime_ns)
        return b.read_json(roots[-1]/'confirmed.json'),roots[-1]


def fixture(name,mode='closed'):
    return Provider(Path(ARTIFACT_ROOT)/name,mode)


def test_complete_first_backup_fresh_independent_download_receipt_readback():
    p=fixture('first-complete');upload,producer=p.invoke();receipt,verifier=p.invoke('verifier')
    assert upload['upload_readback_verified'] and receipt['upload_readback_verified']
    assert producer!=verifier and (verifier/'fresh-blocked/RESTORE-BLOCKED.json').exists()
    assert receipt['destination']['commit_sha']==upload['destination']['commit_sha']
    assert any(method=='GET' and repo=='synthetic/backup' and tail.startswith('/git/blobs/') for method,repo,tail in p.seen)
    assert all(repo=='synthetic/backup' for _,repo,_,_ in p.mutations if repo!='synthetic/receipts')
    rt=p.targets['receipts'];local=p.repo(rt['repository'],branch=rt['branch']);pin=pair.head(local,rt['branch'],b.Budget())
    with b.batch(local,b.Budget()) as read:
        raw=read(pin+':receipt.json','blob',b.MAX_MANIFEST)
    assert h.oid('blob',raw)==receipt['receipt_publication']['blob_sha']
    assert json.loads(raw)['verification']['restore_blocked_verified'] is True
    for root in (producer,verifier):
        for file in root.rglob('*'):
            if file.is_file(): assert all(t.encode() not in file.read_bytes() for t in p.tokens.values())
    b.write_json(p.root/'RESULT.json',{'offline_only':True,'producer':upload,'verifier':receipt,
                                    'http_count':len(p.seen),'fetches':p.fetches})


def test_follow_backup_keeps_prior_increments_manifests_and_history():
    p=fixture('follow');first,root=p.invoke();old=pair.inventory(root/'pair',b.Budget());oldpin=first['destination']['commit_sha']
    # New stream revision + new complete fence cycle, preserving the first cut.
    d=p.runtime['deployment'];sr=p.repos[(d['private_store_repository'],d['store_branch'])]
    pin=pair.head(sr,d['store_branch'],b.Budget())
    with b.batch(sr,b.Budget()) as read: _,raw,env=b.inspect(read,pin,p.runtime['identity'],b.parser(p.runtime['identity']))
    w=capacity.GitWriter(sr,raw);w.pin=pin;w.revision=env['revision'];w.prior_digest=env['body_digest'];w.start();w.commit();w.stop()
    fr=p.repos[(d['private_store_repository'],'fence')];fpin=pair.head(fr,'fence',b.Budget())
    f=deepcopy(p.fence);f['run'].update(id='11',number=2);f['cursors'][f['run']['workflow']]={'number':2,'id':'11'}
    f.update(phase='open',completion=None,write_id='follow-open');fpin=commit_file(fr,'fence',actions.FENCE_PATH,canonical(f).encode(),fpin)
    f.update(phase='closed',completion={'stream':w.confirmed_record()},write_id='follow-close')
    commit_file(fr,'fence',actions.FENCE_PATH,canonical(f).encode(),fpin)
    p.slot+=24*slots.HOUR
    for meta in p.metadata.values(): meta.update(created_at=iso(p.slot+1000),updated_at=iso(p.slot+60000))
    second,root2=p.invoke();receipt,_=p.invoke('verifier')
    assert all(pair.inventory(root2/'pair',b.Budget())[n]==v for n,v in old.items())
    bt=p.targets['backup'];local=p.repo(bt['repository'],branch=bt['branch'])
    b.git(local,b.Budget(),'merge-base','--is-ancestor',oldpin,second['destination']['commit_sha'])
    _,files=p.tree_files(local,second['destination']['commit_sha']);assert len([n for n in files if n.startswith('manifests/')])==2
    assert receipt['manifest']['fence']['history_count']==5


def test_roles_entry_runtime_and_disabled_fail_before_mutation():
    for case in ('disabled','runtime','attempt','workflow','code','role','cross-write','protection','metadata'):
        p=fixture('role-'+case);runtime=deepcopy(p.runtime)
        if case=='disabled': runtime['enabled']=False;p.runtime=runtime;p.set_digest()
        if case=='runtime': p.runtime['python_version']=[0,0,0];p.set_digest()
        if case=='cross-write': p.permissions[(p.tokens['source_read'],'synthetic/receipts')]['push']=True
        if case=='metadata': p.metadata['100']['head_sha']='f'*40
        if case=='protection':
            original=p.open
            def bad(req,timeout):
                if req.full_url.endswith('/protection'): return io.BytesIO(b'{}')
                return original(req,timeout)
            p.open=bad
        with p.context():
            if case=='attempt': os.environ['GITHUB_RUN_ATTEMPT']='2'
            if case=='workflow': os.environ['GITHUB_WORKFLOW_REF']='synthetic/code/.github/workflows/foreign.yml@refs/heads/synthetic'
            if case=='code':
                # Real codepin check must reject the synthetic a*40 checkout claim.
                with patch.object(h,'check_code_pin',side_effect=entry.check_code_pin): assert h.cli(['producer'])==20
                continue
            if case=='role': os.environ[h.ENV['backup_write']]=p.tokens['source_read']
            assert h.cli(['producer'])==20,case
        assert not p.mutations and not p.fetches,case


def test_upload_lost_response_and_concurrent_cas_are_bounded():
    for case in ('lost-confirmed','lost-unconfirmed','cas','blob-loss','partial'):
        p=fixture('upload-'+case);patched={'n':0};original=p.open
        def transport(req,timeout):
            method=req.get_method();url=req.full_url
            if method=='PATCH':
                patched['n']+=1
                if case=='lost-unconfirmed': raise TimeoutError()
                if case=='cas':
                    target=p.targets['backup'];local=p.repo(target['repository'],branch=target['branch'])
                    base=pair.head(local,target['branch'],b.Budget());tree,_=p.tree_files(local,base)
                    competing=write_object(local,'commit',f'tree {tree}\nparent {base}\nauthor Offline <offline@example.invalid> 1700000001 +0000\ncommitter Offline <offline@example.invalid> 1700000001 +0000\n\nconcurrent sibling\n'.encode())
                    b.git(local,b.Budget(),'update-ref','refs/heads/'+target['branch'],competing,base)
                    return original(req,timeout)  # real local ancestry check rejects stale sibling
                response=original(req,timeout)
                if case=='lost-confirmed': raise TimeoutError()
                return response
            if case=='blob-loss' and method=='POST' and url.endswith('/git/blobs'): raise TimeoutError()
            if case=='partial' and method=='GET' and '/git/blobs/' in url and patched['n']:
                value=json.loads(original(req,timeout).read());value['content']=base64.b64encode(b'partial').decode()
                return io.BytesIO(canonical(value).encode())
            return original(req,timeout)
        p.open=transport
        with p.context(): assert h.cli(['producer'])==(0 if case=='lost-confirmed' else 20),case
        assert patched['n']<=1
        if case!='lost-confirmed': assert not list(p.root.glob('btc-producer-*/confirmed.json'))


def test_missing_old_foreign_moving_parts_and_receipt_confirmation_fail_closed():
    for case in ('missing','foreign','old','backup-move','source-move','receipt-loss','receipt-corrupt'):
        p=fixture('verify-'+case);p.invoke();original=p.open;count={'patch':0}
        def transport(req,timeout):
            response=original(req,timeout);url=req.full_url;method=req.get_method();raw=response.read();v=json.loads(raw)
            if method=='PATCH' and '/synthetic/receipts/' in url:
                count['patch']+=1
                if case=='receipt-loss': raise TimeoutError()
            if method=='GET' and '/git/trees/' in url and '/synthetic/backup/' in url:
                if case=='missing': v['tree'].pop()
                if case=='foreign': v['tree'][0]['path']='foreign/part'
            if method=='GET' and '/git/ref/heads/' in url:
                key='source' if case=='source-move' else 'backup'
                if case in ('source-move','backup-move') and p.targets[key]['repository'] in url:
                    counter=url;count[counter]=count.get(counter,0)+1
                    if count[counter]>1: v['object']['sha']='f'*40
            if case=='receipt-corrupt' and count['patch'] and method=='GET' and '/synthetic/receipts/git/blobs/' in url:
                v['content']=base64.b64encode(b'foreign').decode()
            return io.BytesIO(canonical(v).encode())
        p.open=transport
        if case=='old': p.slot+=24*slots.HOUR;p.metadata['200']['created_at']=iso(p.slot+1000)
        with p.context('verifier'): assert h.cli(['verifier'])==(0 if case=='receipt-loss' else 20),case
        assert count['patch']<=1
        if case!='receipt-loss': assert not list(p.root.glob('btc-verifier-*/confirmed.json'))


def test_open_sending_states_restore_blocked_without_health_claim():
    p=fixture('open-sending','open');d=p.runtime['deployment'];sr=p.repos[(d['private_store_repository'],d['store_branch'])]
    pin=pair.head(sr,d['store_branch'],b.Budget())
    with b.batch(sr,b.Budget()) as read: _,raw,env=b.inspect(read,pin,p.runtime['identity'],b.parser(p.runtime['identity']))
    import telegram_outbox as box
    w=capacity.GitWriter(sr,raw);w.pin=pin;w.revision=env['revision'];w.prior_digest=env['body_digest'];w.start()
    command={'result':'synthetic only','_delivery':{'version':1,'messages':[],'signals':{'signals':[]},'oi_history':[]}}
    box.enqueue(command['_delivery'],'test','open',0,{'text':'synthetic only'},'synthetic only')
    command['_delivery']['messages'][0].update(status='sending',attempts=1,target=w.snapshot['control']['target_binding'])
    w.snapshot['commands']['pending']=command;w.commit();w.stop()
    p.invoke();receipt,root=p.invoke('verifier')
    assert receipt['verification']['fence_phase']=='open'
    with durable.read_only_volume(root/'fresh-blocked/stream/blocked-store',p.runtime['identity']['store_id']) as store:
        assert store.snapshot['control']['mode']=='blocked'
        assert store.snapshot['commands']['pending']['_delivery']['messages'][0]['status']=='uncertain'
    assert receipt['verification']['enabled'] is False


def test_numeric_byte_time_process_and_get_only_boundaries():
    root=Path(ARTIFACT_ROOT)/'limits';root.mkdir();budget=h.Budget(root)
    c=h.Client('offline-role',{'synthetic/repo'},set(),budget)
    fails(ValueError,lambda:c.request('POST','synthetic/repo','/git/blobs',{}))
    fails(ValueError,lambda:c.request('GET','foreign/repo','/git/blobs/x'))
    budget.transfer=h.MAX_TRANSFER;fails(ValueError,lambda:budget.reserve('GET',0,1))
    budget.transfer=0;budget.http=h.MAX_HTTP;fails(ValueError,lambda:budget.reserve('GET',0,1))
    budget.http=0;budget.steps=h.MAX_GIT_STEPS+1;fails(ValueError,budget.check)
    budget.steps=0;budget.start-=1801;fails(ValueError,budget.check);budget.start+=1801
    with patch.object(h,'MAX_DISK',3):
        (root/'four-bytes').write_bytes(b'abcd');budget.last_scan=0;fails(ValueError,budget.check)
    with patch.object(h.Client,'open_request',return_value=io.BytesIO(b' '*(2*h.MIB+1))):
        fails(ValueError,lambda:c.request('GET','synthetic/repo','/git/blobs/x'))
    budget.deadline_ms=1;fails(ValueError,budget.check)


def test_reviewed_changing_entry_requires_workflow_bytes_and_ancestry():
    from reviewed_actions_entry import verify
    p=fixture('entry-pins');binding=p.runtime['producer'];client=h.Client(p.tokens['metadata_read'],{'synthetic/code'},set(),h.Budget(p.root))
    sha='e'*40;calls=[]
    def reply(req,timeout):
        calls.append(req.full_url)
        if '/compare/' in req.full_url:
            return io.BytesIO(canonical({'base_commit':{'sha':binding['code_sha']},'merge_base_commit':{'sha':binding['code_sha']},'status':'ahead'}).encode())
        return p.open(req,timeout)
    with patch.object(h.Client,'open_request',side_effect=reply):
        verify(client,'synthetic/code',sha,binding['code_sha'],binding['workflow'],binding['workflow_sha256'])
        p.yaml[binding['workflow']]+=b'changed'
        fails(ValueError,lambda:verify(client,'synthetic/code',sha,binding['code_sha'],binding['workflow'],binding['workflow_sha256']))
        fails(ValueError,lambda:verify(client,'synthetic/code',sha,binding['code_sha'],binding['workflow']))
    assert any('/compare/' in v for v in calls)


def test_real_signal_entry_keeps_production_pin_across_legacy_entry_commit():
    from test_betriebsabschluss import actual_entry
    from test_actions_delivery import invoke
    @contextmanager
    def retained_temp(*args,**kwargs):
        folder=Path(tempfile.mkdtemp(prefix='entry-',dir=ARTIFACT_ROOT))
        yield str(folder)  # retain synthetic evidence; no sandbox-temp cleanup
    for changed in (False,True):
        with patch.object(tempfile,'TemporaryDirectory',side_effect=retained_temp),actual_entry() as (_,data,path,runtime,http,meta,slot):
            raw=b'reviewed synthetic signal workflow\n';workflow=meta['path'];meta['head_sha']='e'*40
            runtime['entry_workflows']={workflow:hashlib.sha256(raw).hexdigest()};path.write_text(canonical(runtime),encoding='utf-8')
            original=actions.ActionsClient.open_request
            def reply(req,timeout):
                if '/contents/.github/workflows/' in req.full_url:
                    http.seen.append(('GET',req.full_url,timeout));body=raw+(b'changed' if changed else b'')
                    return io.BytesIO(canonical({'type':'file','encoding':'base64','content':base64.b64encode(body).decode(),'sha':h.oid('blob',body)}).encode())
                if '/compare/' in req.full_url:
                    http.seen.append(('GET',req.full_url,timeout))
                    return io.BytesIO(canonical({'base_commit':{'sha':runtime['code_sha']},'merge_base_commit':{'sha':runtime['code_sha']},'status':'ahead'}).encode())
                return original(req,timeout=timeout)
            with patch.dict(os.environ,{'GITHUB_SHA':'e'*40}),patch.object(actions.ActionsClient,'open_request',side_effect=reply):
                if changed:
                    fails(ValueError,lambda:invoke(path,data));assert http.puts==0
                else:
                    result=invoke(path,data)
                    assert result['get']==len([v for v in http.seen if v[0]=='GET'])
                    fence=json.loads(http.file(actions.FENCE_PATH));assert fence['deployment']['code_sha']==runtime['code_sha']


def test_smart_transport_bounds_short_foreign_and_incomplete_pack():
    for case in ('wrong-ref','incomplete','bytes'):
        p=fixture('smart-'+case);original=p.open
        def reply(req,timeout):
            if 'github.com/' in req.full_url:
                if case=='wrong-ref' and req.get_method()=='GET':
                    return io.BytesIO(original(req,timeout).read().replace(b'refs/heads/private-stream',b'refs/heads/foreign-stream'))
                if case=='incomplete' and req.get_method()=='POST': return io.BytesIO(original(req,timeout).read()[:-4])
                if case=='bytes' and req.get_method()=='GET': return io.BytesIO(b'x'*(2*h.MIB+1))
            return original(req,timeout)
        p.open=reply
        if case=='wrong-ref':
            # Use the actual dedicated source branch name of this fixture.
            branch=p.targets['source']['branch'];old=reply
            def corrected(req,timeout):
                if 'github.com/' in req.full_url and req.get_method()=='GET':
                    return io.BytesIO(original(req,timeout).read().replace(('refs/heads/'+branch).encode(),b'refs/heads/foreign'))
                return old(req,timeout)
            p.open=corrected
        with p.context(): assert h.cli(['producer'])==20,case
        assert not p.mutations and not list(p.root.glob('btc-producer-*/confirmed.json'))


def test_http_trickle_has_actual_wall_deadline():
    import threading
    root=Path(ARTIFACT_ROOT)/'http-wall';root.mkdir();budget=h.Budget(root)
    class Slow(io.BytesIO):
        def read(self,*args): threading.Event().wait(.4);return super().read(*args)
    c=h.Client('offline',{'synthetic/repo'},set(),budget)
    import time
    started=time.monotonic()
    with patch.object(h,'REQUEST_SECONDS',.1),patch.object(h.Client,'open_request',return_value=Slow(b'{}')):
        fails(RuntimeError,lambda:c.request('GET','synthetic/repo','/git/ref/heads/main'))
    assert time.monotonic()-started<.35 and budget.http==1


def test_materialized_workflows_disabled_paths_versions_and_legacy_preservation():
    from p4_install_hosted_templates import materialize,MAPPING
    out=Path(ARTIFACT_ROOT)/'disabled-overlay';before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for parent in (ROOT/'.github/workflows',ROOT/'site/data') for p in parent.rglob('*') if p.is_file()}
    pins=materialize(out)
    assert len(pins)==7
    for workflow,sha in pins.items():
        raw=(out/workflow).read_bytes();text=raw.decode()
        assert hashlib.sha256(raw).hexdigest()==sha and 'if: ${{ false }}' in text
        assert 'self-hosted' not in text and 'queue: max' in text and 'python-version: "3.12.14"' in text
        assert 'ref: ${{ github.sha }}' not in text
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha for path,sha in before.items())


def test_freshness_understands_immutable_published_manifest_and_actual_receipt():
    p=fixture('freshness');p.invoke();receipt,_=p.invoke('verifier');m=receipt['manifest'];v=p.runtime['verifier']
    policy={'deployment':p.runtime['deployment'],'backup_target':{**p.targets['backup'],'manifest_prefix':'manifests/'},
            'independent_verifier':{'repository':p.targets['receipts']['repository'],'receipt_branch':'receipts','receipt_path':'receipt.json',
                'binding':{k:v[k] for k in ('repository','workflow','branch','code_sha')}},'first_start_ms':{'backup':p.slot}}
    original=p.open
    def monitor_http(req,timeout):
        url=req.full_url
        if '/contents/' in url and '/synthetic/code/' not in url:
            parts=urllib.parse.urlparse(url);repo='/'.join(parts.path.split('/')[2:4]);name=parts.path.split('/contents/')[1]
            pin=urllib.parse.parse_qs(parts.query)['ref'][0];local=p.repo(repo,pin)
            with b.batch(local,b.Budget()) as read: raw=read(pin+':'+name,'blob',b.MAX_MANIFEST)
            return io.BytesIO(canonical({'type':'file','encoding':'base64','sha':h.oid('blob',raw),'content':base64.b64encode(raw).decode()}).encode())
        if '/attempts/1/jobs' in url:
            return io.BytesIO(canonical({'total_count':1,'jobs':[{'run_id':200,'run_attempt':1,'head_sha':v['code_sha'],
                'status':'completed','conclusion':'success'}]}).encode())
        # Reader's separately injected monitor token is mapped only inside this fake.
        req.add_header('Authorization','Bearer '+p.tokens['backup_read'] if '/synthetic/code/' not in url else 'Bearer '+p.tokens['metadata_read'])
        return original(req,timeout)
    budget=ReadBudget()
    with patch.object(freshness.Reader,'open_request',side_effect=monitor_http):
        backup=freshness.Reader('offline-monitor',['synthetic/backup','synthetic/receipts'],budget)
        code=freshness.Reader('offline-monitor',['synthetic/code'],budget)
        result,_,_=freshness.read_backup(backup,code,policy,p.slot+60000)
        assert result['manifest_sha256']==digest(m)
        bad=deepcopy(policy);bad['backup_target']['manifest_prefix']='foreign/'
        fails((ValueError,KeyError),lambda:freshness.read_backup(backup,code,bad,p.slot+60000))
        fails(ValueError,lambda:freshness.read_backup(backup,code,policy,p.slot+26*slots.HOUR+1))


def test_independent_reviewed_identity_and_migration_are_not_self_attested():
    for case in ('identity','migration'):
        p=fixture('review-bind-'+case);p.invoke();before=len(p.mutations)
        if case=='identity': p.runtime['identity']['stream_id']='foreign-reviewed-stream'
        else:
            name=next(iter(p.runtime['migration']['files']))
            p.runtime['migration']['files'][name]['sha']='f'*40
        p.set_digest()
        with p.context('verifier'): assert h.cli(['verifier'])==20
        assert len(p.mutations)==before and not list(p.root.glob('btc-verifier-*/confirmed.json'))
    p=fixture('migration-bytes');root=p.root/'package'
    import shutil
    folder=root/'stream/packages/000000/migration';shutil.copytree(p.fixture['migration'],folder)
    budget=h.Budget(root);h.validate_migration_bytes(root,p.runtime['migration'],budget)
    (folder/'projection/watch.json').write_bytes(b'[]\nchanged')
    fails(ValueError,lambda:h.validate_migration_bytes(root,p.runtime['migration'],budget))


def main():
    import argparse,traceback
    global ARTIFACT_ROOT
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    ARTIFACT_ROOT=Path(args.out).resolve();ARTIFACT_ROOT.mkdir(exist_ok=False)
    results=[]
    for name,fn in list(globals().items()):
        if name.startswith('test_') and callable(fn):
            try: fn();results.append({'test':name,'passed':True});print('PASS',name,flush=True)
            except Exception:
                traceback.print_exc();results.append({'test':name,'passed':False});print('FAIL',name,flush=True)
    b.write_json(ARTIFACT_ROOT/'TEST-RESULTS.json',{'offline_only':True,'results':results})
    return 0 if all(v['passed'] for v in results) else 1


if __name__=='__main__': sys.exit(main())
