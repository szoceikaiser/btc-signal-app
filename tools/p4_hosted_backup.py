"""Bounded GitHub hosted backup protocol. No discovery, bootstrap or resend.

Secrets enter through four distinct environment roles only. Both Git smart
HTTP and REST credentials stay in memory, exclusively in request headers.
Only dedicated full source refs are fetched, never a mirror or --all.
"""
import argparse
import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import p3_backup_chain as b
import p4_backup_pair as pair
import actions_schedule as slots
import actions_delivery as actions
import github_delivery as github
from production_contract import canonical,digest
from production_confirmation import ProductionContentsClient
from produktion_actions_runner import check_code_pin,deployment

SCHEMA='btc-hosted-backup-v1'
MIB=1024*1024
MAX_HTTP=4096
MAX_MUTATIONS=2048
MAX_TRANSFER=512*MIB
MAX_PAYLOAD=128*MIB
MAX_DISK=1024*MIB
MAX_SOURCE_DISK=128*MIB
MAX_FILES=4096
MAX_GIT_STEPS=8192
MAX_RESPONSE=28*MIB  # base64 of a <=20MiB segment; not Contents API
REQUEST_SECONDS=15
MANIFEST='pair-manifest.json'
RECEIPT='receipt.json'
ROLES={'producer':('source_read','backup_write','receipt_read','metadata_read'),
       'verifier':('backup_read','receipt_write','source_read','metadata_read')}
ENV={r:'BTC_HOSTED_'+r.upper()+'_TOKEN' for r in set(sum((list(v) for v in ROLES.values()),[]))}


class Inaccessible(RuntimeError):
    pass


def wire(client,request,budget,limit):
    """One bounded HTTP operation with an actual wall-clock deadline.

    A socket timeout alone does not bound a trickling response. Timed-out worker
    is never reused/retried; only an independent GET may reconcile a ref PATCH.
    Workers are daemon threads, so DNS/read stalls cannot hold the CLI alive.
    """
    finished=threading.Event();values=[];responses=[]
    seconds=min(REQUEST_SECONDS,b.TOTAL_SECONDS-(time.monotonic()-budget.start))
    began=time.monotonic()
    def work():
        try:
            with client.open_request(request,timeout=seconds) as response:
                responses.append(response);raw=response.read(limit+1)
                if len(raw)>limit: raise ValueError('Response byte limit')
                values.append(raw)
        except BaseException as exc: values.append(exc)
        finally: finished.set()
    worker=threading.Thread(target=work,daemon=True);worker.start()
    try:
        while not finished.wait(.05):
            budget.check()
            if time.monotonic()-began>=seconds: raise TimeoutError('Bounded HTTP wall deadline')
        budget.check()
        if time.monotonic()-began>seconds: raise TimeoutError('Bounded HTTP wall deadline')
        value=values[0]
        if isinstance(value,BaseException): raise value
        return value
    except BaseException:
        if responses:
            threading.Thread(target=responses[0].close,daemon=True).start()
        raise


def oid(kind,raw):
    return hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def safe_path(value):
    if (not isinstance(value,str) or not value or len(value)>240 or
            not re.fullmatch(r'[A-Za-z0-9._/-]+',value) or
            any(x in ('','.','..','.git') for x in value.split('/'))):
        raise ValueError('Unsafe bounded path')
    return value


def validate_target(t):
    if (set(t)!={'repository','id','branch'} or
            not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+',t['repository'] or '') or
            type(t['id']) is not int or t['id']<=0 or
            not re.fullmatch(r'[A-Za-z0-9_-]+',t['branch'] or '')):
        raise ValueError('Reviewed repository ID/ref required')


class Budget(b.Budget):
    def __init__(self,root):
        super().__init__();self.root=Path(root);self.http=self.mutations=self.transfer=0
        self.deadline_ms=None;self.source_roots=[]
        self.disk_lock=threading.Lock();self.last_scan=0

    def check(self):
        super().check()
        if self.steps>MAX_GIT_STEPS: raise ValueError('Git process count limit')
        if self.deadline_ms and int(time.time()*1000)>self.deadline_ms:
            raise ValueError('Original backup occurrence expired')
        # Called by the existing Git watchdog every 50ms. POSIX fetch also has
        # RLIMIT_FSIZE; per-source object and total disk ceilings are fail-closed.
        with self.disk_lock:
            if time.monotonic()-self.last_scan<.1: return
            self.last_scan=time.monotonic()
            for root,limit in [(self.root,MAX_DISK),*[(p,MAX_SOURCE_DISK) for p in self.source_roots]]:
                total=count=0;pending=[root]
                while pending:
                    with os.scandir(pending.pop()) as entries:
                        for item in entries:
                            if item.is_symlink(): raise ValueError('Workspace symlink')
                            if item.is_dir(follow_symlinks=False): pending.append(item.path);continue
                            try: total+=item.stat(follow_symlinks=False).st_size
                            except FileNotFoundError: continue  # Git's own temporary rename
                            count+=1
                            if total>limit or count>32768: raise ValueError('Workspace disk/file limit')

    def reserve(self,method,request_bytes,response_limit):
        self.check()
        if (self.http>=MAX_HTTP or (method!='GET' and self.mutations>=MAX_MUTATIONS)
                or self.transfer+request_bytes+response_limit>MAX_TRANSFER):
            raise ValueError('Shared HTTP/transfer limit')
        self.http+=1;self.mutations+=method!='GET'
        self.transfer+=request_bytes+response_limit


class Client:
    open_request=staticmethod(ProductionContentsClient.open_request)

    def __init__(self,token,scope,writable,budget):
        if not token or '\n' in token or '\r' in token: raise ValueError('Injected role missing')
        self.token=token;self.scope=scope;self.writable=writable;self.budget=budget
        self.allowed=set()

    def request(self,method,repo,tail,payload=None,limit=2*MIB):
        if repo not in self.scope or (method!='GET' and repo not in self.writable):
            raise ValueError('Role scope forbids request')
        # Routes are exclusively constructed by protocol methods below.
        route=github.GitHubContentsClient._route(repo,tail)
        raw=None if payload is None else canonical(payload).encode()
        if raw and len(raw)>MAX_RESPONSE: raise ValueError('Request byte limit')
        self.budget.reserve(method,len(raw or b''),limit)
        request=urllib.request.Request('https://api.github.com'+route,data=raw,method=method,headers={
            'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json',
            'X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json','User-Agent':'btc-p4-backup'})
        try:
            body=wire(self,request,self.budget,limit)
            return json.loads(body)
        except urllib.error.HTTPError as exc:
            if exc.code==404: raise Inaccessible('Private target inaccessible') from None
            raise RuntimeError('Provider HTTP outcome unconfirmed') from None
        except (urllib.error.URLError,TimeoutError,OSError):
            raise RuntimeError('Provider outcome unconfirmed') from None

    def repository(self,t,write):
        meta=self.request('GET',t['repository'],'')
        perms=meta.get('permissions',{})
        if (meta.get('id')!=t['id'] or meta.get('full_name')!=t['repository'] or meta.get('private') is not True
                or perms.get('pull') is not True or perms.get('push') is not write
                or perms.get('admin') is not False or perms.get('maintain') is not False):
            raise ValueError('Actual private repository/least role differs')

    def protected(self,t):
        # Protocol assumption: provider must expose full protection to the role.
        # Unavailable entitlement/visibility is a hard stop, never a public fallback.
        p=self.request('GET',t['repository'],'/branches/'+t['branch']+'/protection')
        if (p.get('allow_force_pushes',{}).get('enabled') is not False
                or p.get('allow_deletions',{}).get('enabled') is not False
                or p.get('enforce_admins',{}).get('enabled') is not True
                or p.get('required_linear_history',{}).get('enabled') is not True):
            raise ValueError('Protected append-only destination required')

    def ref(self,t):
        value=self.request('GET',t['repository'],'/git/ref/heads/'+urllib.parse.quote(t['branch'],safe=''))
        if (value.get('ref')!='refs/heads/'+t['branch'] or value['object']['type']!='commit'
                or not b.HEX40.fullmatch(value['object']['sha'])): raise ValueError('Exact ref required')
        return value['object']['sha']

    def commit(self,t,pin):
        if not b.HEX40.fullmatch(pin): raise ValueError('Commit pin')
        v=self.request('GET',t['repository'],'/git/commits/'+pin)
        if v.get('sha')!=pin or not b.HEX40.fullmatch(v['tree']['sha']): raise ValueError('Immutable commit identity')
        return v

    def tree(self,t,pin):
        commit=self.commit(t,pin);tree=commit['tree']['sha']
        v=self.request('GET',t['repository'],'/git/trees/'+tree+'?recursive=1')
        if v.get('sha')!=tree or v.get('truncated') is not False or len(v['tree'])>MAX_FILES*2:
            raise ValueError('Incomplete/oversized destination tree')
        result={};total=0
        for item in v['tree']:
            safe_path(item['path'])
            if item['type']=='tree' and item['mode']=='040000': continue
            if item['type']!='blob' or item['mode']!='100644' or item['path'] in result:
                raise ValueError('Destination contains nonregular/duplicate entry')
            if not b.HEX40.fullmatch(item['sha']) or not 0<=item['size']<=b.MAX_PACKAGE:
                raise ValueError('Destination blob identity/size')
            result[item['path']]={'sha':item['sha'],'bytes':item['size']};total+=item['size']
        if len(result)>MAX_FILES or total>MAX_PAYLOAD: raise ValueError('Destination capacity')
        if tree_oid(result)!=tree: raise ValueError('Full tree object SHA differs')
        return tree,result

    def blob(self,t,item):
        # GitHub may line-wrap Base64 and JSON-escape each newline. Reserve that
        # overhead as well as metadata; exact decoded byte length remains pinned.
        limit=min(MAX_RESPONSE,(item['bytes']*7+4)//5+8192)
        v=self.request('GET',t['repository'],'/git/blobs/'+item['sha'],limit=limit)
        if v.get('encoding')!='base64' or v.get('sha')!=item['sha'] or v.get('size')!=item['bytes']:
            raise ValueError('Immutable blob metadata differs')
        raw=base64.b64decode(''.join(v['content'].split()),validate=True)
        if len(raw)!=item['bytes'] or oid('blob',raw)!=item['sha']: raise ValueError('Immutable blob bytes differ')
        return raw


def tree_oid(files):
    root={}
    for name,item in files.items():
        node=root;parts=safe_path(name).split('/')
        for part in parts[:-1]:
            node=node.setdefault(part,{})
            if not isinstance(node,dict): raise ValueError('Path collision')
        if parts[-1] in node: raise ValueError('Tree path collision')
        node[parts[-1]]=item['sha']
    def encode(node):
        rows=[]
        for name,value in node.items():
            folder=isinstance(value,dict)
            rows.append((name+('/' if folder else ''),('40000' if folder else '100644').encode()+b' '+
                         name.encode()+b'\0'+bytes.fromhex(encode(value) if folder else value)))
        return oid('tree',b''.join(raw for _,raw in sorted(rows)))
    return encode(root)


def tokens(mode):
    values={r:os.environ.get(ENV[r]) for r in ROLES[mode]}
    if not all(values.values()) or len(set(values.values()))!=len(values):
        raise ValueError('Four separately injected role credentials required')
    # A producer must not even possess the receipt writer, nor verifier the backup writer.
    forbidden=('receipt_write','backup_read') if mode=='producer' else ('backup_write','receipt_read')
    if any(os.environ.get(ENV[r]) for r in forbidden): raise ValueError('Forbidden role injection')
    return values


def validate(runtime,mode,budget=None,check_checkout=True):
    if runtime.get('enabled') is not True or runtime.get('schema')!=SCHEMA: raise ValueError('Hosted backup disabled')
    for key in ('source','backup','receipts'): validate_target(runtime[key])
    if len({runtime[k]['id'] for k in ('source','backup','receipts')})!=3: raise ValueError('Distinct role destinations required')
    d=runtime['deployment'];binding=runtime[mode]
    if (d!=deployment(d) or d['private_store_repository']!=runtime['source']['repository']
            or d['store_branch']==d['fence_branch'] or d['store_branch']!=runtime['source']['branch']
            or runtime['identity']['repo']!=runtime['source']['repository']
            or runtime['identity']['branch']!=d['store_branch'] or runtime['identity']['store_id']!=d['store_id']
            or binding['workflow']!='.github/workflows/'+('backup' if mode=='producer' else 'backup-verify')+'.yml'
            or binding['repository']!=d['code_repository'] or binding['branch']!=d['code_ref'].removeprefix('refs/heads/')
            or type(binding['repository_id']) is not int or binding['repository_id']<=0
            or not b.HEX40.fullmatch(binding['code_sha']) or not b.HEX64.fullmatch(runtime['activation_review_sha256'])
            or runtime.get('runtime_sha256')!=digest({k:v for k,v in runtime.items() if k!='runtime_sha256'})
            or sys.version_info[:3]!=tuple(runtime['python_version']) or runtime['runner_os']!='Linux'
            or platform.system()!='Linux'):
        raise ValueError('Reviewed code/runtime/source binding differs')
    expected={'GITHUB_REPOSITORY':binding['repository'],'GITHUB_REF':'refs/heads/'+binding['branch'],
        'GITHUB_WORKFLOW_REF':binding['repository']+'/'+binding['workflow']+'@refs/heads/'+binding['branch'],
        'GITHUB_RUN_ATTEMPT':'1','RUNNER_OS':'Linux','BTC_HOSTED_RUNTIME_SHA256':runtime['runtime_sha256']}
    if any(os.environ.get(k)!=v for k,v in expected.items()) or any(
            not re.fullmatch('[1-9][0-9]*',os.environ.get(k,'')) for k in ('GITHUB_RUN_ID','GITHUB_RUN_NUMBER')):
        raise ValueError('Actual hosted entry/ref/attempt differs')
    if os.environ.get('GITHUB_EVENT_NAME') not in ('schedule','workflow_dispatch'): raise ValueError('Unsupported entry event')
    if check_checkout: check_code_pin(binding['code_sha'],budget)
    return binding


def metadata(client,runtime,binding):
    rid=os.environ['GITHUB_RUN_ID'];repo=binding['repository']
    meta=client.request('GET',repo,'/actions/runs/'+rid)
    if (str(meta['id'])!=rid or meta['run_attempt']!=1 or str(meta['run_number'])!=os.environ['GITHUB_RUN_NUMBER']
            or meta['repository']['full_name']!=repo or meta['repository']['id']!=binding['repository_id']
            or meta['head_sha']!=os.environ['GITHUB_SHA']
            or meta['head_branch']!=binding['branch'] or meta['path']!=binding['workflow']
            or meta['event']!=os.environ['GITHUB_EVENT_NAME']): raise ValueError('Actual run metadata differs')
    from reviewed_actions_entry import verify
    verify(client,repo,meta['head_sha'],binding['code_sha'],binding['workflow'],binding['workflow_sha256'])
    slot=slots.bind('backup',meta,int(time.time()*1000),os.environ.get('BTC_ACTIONS_EXPLICIT_START_MS',''))
    client.budget.deadline_ms=slots.deadline('backup',slot)
    return slot


def fetch_source(client,t,pin,target,budget):
    """Full ONE-ref Git smart HTTP v0 pack, strictly bounded before Git import.

    Secrets exist only in HTTP headers; no credential-bearing child process.
    No shallow/haves/filter, so all reachable objects must arrive. No tags or
    other advertised refs are requested. Unsupported protocol is fail-closed.
    """
    if client.writable or t['repository'] not in client.scope or not b.HEX40.fullmatch(pin):
        raise ValueError('Read-only pinned Git source required')
    target=Path(target);target.mkdir(exist_ok=False);budget.source_roots.append(target)
    b.git(target,budget,'init','--bare')
    auth='Basic '+base64.b64encode(('x-access-token:'+client.token).encode()).decode()
    url='https://github.com/'+t['repository']+'.git'
    def request(method,tail,raw,limit):
        budget.reserve(method,len(raw or b''),limit)
        req=urllib.request.Request(url+tail,data=raw,method=method,headers={
            'Authorization':auth,'User-Agent':'btc-p4-backup',
            'Content-Type':'application/x-git-upload-pack-request',
            'Accept':'application/x-git-upload-pack-'+('advertisement' if method=='GET' else 'result')})
        return io.BytesIO(wire(client,req,budget,limit))
    def pkt(raw): return f'{len(raw)+4:04x}'.encode()+raw
    def packets(response,limit):
        total=0
        for _ in range(1048576):
            budget.check();header=response.read(4);total+=len(header)
            if total>limit: raise ValueError('Git wire byte limit')
            if not header: return
            if len(header)!=4 or not re.fullmatch(b'[0-9a-f]{4}',header): raise ValueError('Malformed Git pkt-line')
            size=int(header,16)
            if size==0: yield None;continue
            if not 4<=size<=65524: raise ValueError('Git packet size')
            body=response.read(size-4);total+=len(body)
            if len(body)!=size-4 or total>limit: raise ValueError('Git transfer byte/short-packet limit')
            yield body
        raise ValueError('Git packet count limit')
    try:
        with request('GET','/info/refs?service=git-upload-pack',None,2*MIB) as response:
            advertised=list(packets(response,2*MIB))
        if not advertised or advertised[0]!=b'# service=git-upload-pack\n': raise ValueError('Git smart protocol v0 required')
        refs={};capabilities=set()
        for line in advertised[1:]:
            if line is None: continue
            line=line.rstrip(b'\n')
            if b'\0' in line:
                line,caps=line.split(b'\0',1);capabilities.update(caps.decode().split())
            sha,ref=line.decode().split(' ',1)
            if not b.HEX40.fullmatch(sha): raise ValueError('Git advertisement identity')
            if ref in refs: raise ValueError('Duplicate advertised ref')
            refs[ref]=sha
        if refs.get('refs/heads/'+t['branch'])!=pin or not {'side-band-64k','ofs-delta'}.issubset(capabilities):
            raise ValueError('Allowed Git source ref moved/capability unavailable')
        body=pkt(('want '+pin+' side-band-64k ofs-delta no-progress\n').encode())+b'0000'+pkt(b'done\n')
        pack=target/'source.pack';ended=False;started=False
        with request('POST','/git-upload-pack',body,64*MIB) as response,pack.open('xb') as out:
            for line in packets(response,64*MIB):
                if line is None:
                    if started: ended=True
                    continue
                if ended: raise ValueError('Unexpected trailing Git data')
                if not started and line==b'NAK\n': continue
                if not line or line[0] not in (1,2): raise ValueError('Git upload pack refused/incomplete')
                if line[0]==1: out.write(line[1:]);started=True
            if not started or not ended: raise ValueError('Complete Git pack terminator required')
        with pack.open('rb') as inp,b.process(target,['index-pack','--stdin','--strict'],budget,file_limit=64*MIB) as proc:
            if inp.read(4)!=b'PACK': raise ValueError('Git pack header missing')
            inp.seek(0)
            for block in iter(lambda:inp.read(65536),b''): proc.stdin.write(block)
            proc.stdin.close()
            if len(proc.stdout.read(4097))>4096: raise ValueError('Git import output bound')
        b.git(target,budget,'update-ref','refs/heads/'+t['branch'],pin)
    except (urllib.error.URLError,TimeoutError,OSError):
        raise RuntimeError('Read-only Git transfer unconfirmed') from None
    if pair.head(target,t['branch'],budget)!=pin or (target/'shallow').exists(): raise ValueError('Incomplete pinned Git source')
    b.git(target,budget,'fsck','--full','--no-reflogs')
    return target


def download(client,t,pin,root,manifest_path=MANIFEST):
    _,files=client.tree(t,pin)
    if manifest_path not in files: raise ValueError('Complete manifest missing at destination')
    raw=client.blob(t,files[manifest_path]);m=json.loads(raw)
    if raw!=(canonical(m)+'\n').encode(): raise ValueError('Noncanonical paired manifest')
    pair.validate_pair(m,m['pins'])
    expected=set(m['files'])|{MANIFEST,'manifests/'+digest(m)+'.json'}
    # Older immutable manifests are retained, package paths are never discarded.
    old={n for n in files if re.fullmatch(r'manifests/[0-9a-f]{64}\.json',n)}
    if set(files)!=expected|old: raise ValueError('Foreign or incomplete backup target contents')
    if files['manifests/'+digest(m)+'.json']!=files[MANIFEST]: raise ValueError('Immutable manifest alias differs')
    root=Path(root);root.mkdir(exist_ok=False)
    for name,item in m['files'].items():
        safe_path(name)
        if not name.startswith(('stream/packages/','fence/packages/')) or files[name]['bytes']!=item['bytes']:
            raise ValueError('Foreign or missing package part')
        data=client.blob(t,files[name])
        if hashlib.sha256(data).hexdigest()!=item['sha256']: raise ValueError('Package byte SHA256 differs')
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    (root/MANIFEST).write_bytes(raw)
    return m,{'repository':t['repository'],'branch':t['branch'],'manifest_path':'manifests/'+digest(m)+'.json',
              'commit_sha':pin,'tree_sha':tree_oid(files),'blob_sha':files[MANIFEST]['sha']}


def migration(client,spec,target):
    validate_target(spec['target']);pin=spec['commit_sha']
    _,files=client.tree(spec['target'],pin)
    if files!=spec['files'] or tree_oid(files)!=spec['tree_sha']: raise ValueError('Immutable migration tree differs')
    target=Path(target);target.mkdir(exist_ok=False)
    for name,item in files.items():
        safe_path(name);p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(client.blob(spec['target'],item))
    from produktion_store import verify_package
    verify_package(target)
    return target


def publish(client,t,base,additions,replace):
    """One parent, one ref PATCH, then exact complete immutable byte readback.

    Lost PATCH response permits ONE ref read; exact proposal is required. Blob,
    tree or commit response loss stops without a ref mutation. No blind retry.
    """
    base_tree,old=client.tree(t,base);combined=deepcopy(old);changed=[]
    total=sum(v['bytes'] for v in old.values())
    for name,raw in additions.items():
        safe_path(name)
        if len(raw)>b.MAX_PACKAGE: raise ValueError('Publication part byte limit')
        item={'sha':oid('blob',raw),'bytes':len(raw)}
        if name in old and old[name]!=item and name not in replace: raise ValueError('Immutable package collision')
        total+=len(raw)-old.get(name,{}).get('bytes',0)
        combined[name]=item
    if total>MAX_PAYLOAD or len(combined)>MAX_FILES: raise ValueError('Published target capacity')
    expected_tree=tree_oid(combined)
    for name,raw in additions.items():
        item=combined[name]
        if old.get(name)==item: continue
        result=client.request('POST',t['repository'],'/git/blobs',{'encoding':'base64','content':base64.b64encode(raw).decode()})
        if result.get('sha')!=item['sha']: raise ValueError('Created blob identity differs')
        changed.append({'path':name,'mode':'100644','type':'blob','sha':item['sha']})
    tree=client.request('POST',t['repository'],'/git/trees',{'base_tree':base_tree,'tree':changed})
    if tree.get('sha')!=expected_tree: raise ValueError('Created complete tree identity differs')
    stamp=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    identity={'name':'BTC verified backup','email':'backup@example.invalid','date':stamp}
    commit=client.request('POST',t['repository'],'/git/commits',{
        'message':'verified immutable payload '+expected_tree,'tree':expected_tree,'parents':[base],
        'author':identity,'committer':identity})
    pin=commit.get('sha','')
    if not b.HEX40.fullmatch(pin): raise ValueError('Created commit identity missing')
    observed=client.commit(t,pin)
    if observed['tree']['sha']!=expected_tree or [p['sha'] for p in observed['parents']]!=[base]:
        raise ValueError('Created commit parent/tree differs')
    if client.ref(t)!=base: raise ValueError('Destination moved before publication')
    try:
        answer=client.request('PATCH',t['repository'],'/git/refs/heads/'+t['branch'],{'sha':pin,'force':False})
        if answer.get('object',{}).get('sha')!=pin: raise RuntimeError('Ref response missing')
    except RuntimeError:
        # No second mutation. A conflicting descendant is conservatively refused.
        if client.ref(t)!=pin: raise ValueError('Lost publication response remains unconfirmed') from None
    if client.ref(t)!=pin: raise ValueError('Concurrent publication not confirmed')
    tree_sha,files=client.tree(t,pin)
    if files!=combined or tree_sha!=expected_tree: raise ValueError('Published full tree differs')
    # Re-read EVERY referenced blob, including prior increments: no partial receipt.
    for name,item in files.items():
        raw=client.blob(t,item)
        if name in additions and raw!=additions[name]: raise ValueError('Publication exact bytes differ')
    if client.ref(t)!=pin: raise ValueError('Destination moved during full byte confirmation')
    return {'commit_sha':pin,'tree_sha':tree_sha,'files':files}


def roles(runtime,mode,budget):
    values=tokens(mode);repo=runtime['source']['repository'];backup=runtime['backup']['repository'];receipt=runtime['receipts']['repository']
    scopes={'source_read':{repo,runtime['migration']['target']['repository']},'backup_write':{backup},
            'backup_read':{backup},'receipt_read':{receipt},'receipt_write':{receipt},
            'metadata_read':{runtime[mode]['repository']}}
    clients={r:Client(token,scopes[r],scopes[r] if r.endswith('_write') else set(),budget) for r,token in values.items()}
    # Positive read/write checks AND negative cross-target permissions before work.
    for role,c in clients.items():
        for key in ('source','backup','receipts'):
            t=runtime[key]
            probe=Client(c.token,{t['repository']},set(),budget)
            # GitHub 404 for inaccessible private repos is also the expected denial.
            if t['repository'] not in c.scope:
                try: meta=probe.request('GET',t['repository'],'')
                except Inaccessible: continue
                perms=meta.get('permissions',{})
                if any(perms.get(k) is not False for k in ('push','admin','maintain')):
                    raise ValueError('Cross-target writer role refused')
            else: c.repository(t,role.endswith('_write'))
    c=clients['source_read'];spec=runtime['migration'];validate_target(spec['target'])
    c.repository(spec['target'],False)
    clients['backup_write' if mode=='producer' else 'backup_read'].protected(runtime['backup'])
    clients['receipt_read' if mode=='producer' else 'receipt_write'].protected(runtime['receipts'])
    return clients


def run(runtime,mode,root):
    budget=Budget(root);binding=validate(runtime,mode,budget);clients=roles(runtime,mode,budget)
    slot=metadata(clients['metadata_read'],runtime,binding)
    source=clients['source_read'];s=runtime['source'];f={**s,'branch':runtime['deployment']['fence_branch']}
    heads={key:source.ref(t) for t,key in ((s,'stream'),(f,'fence'))}
    backup=clients['backup_write' if mode=='producer' else 'backup_read'];bt=runtime['backup'];base=backup.ref(bt)
    if mode=='producer':
        _,existing=backup.tree(bt,base)
        previous=None
        if existing:
            previous,_=download(backup,bt,base,Path(root)/'pair')
            if previous['deployment']!=runtime['deployment']: raise ValueError('Previous backup deployment differs')
            pair.restore(Path(root)/'pair',previous,Path(root)/'previous-blocked',previous['pins'],budget)
        else: (Path(root)/'pair').mkdir()
        sr=fetch_source(source,s,heads['stream'],Path(root)/'stream-source',budget)
        fr=fetch_source(source,f,heads['fence'],Path(root)/'fence-source',budget)
        with b.batch(sr,budget) as read:
            _,stream_raw,envelope=b.inspect(read,heads['stream'],runtime['identity'],b.parser(runtime['identity']))
        with b.batch(fr,budget) as read:
            _,fence_raw,fence_value,fence_blob=pair.inspect_fence(read,heads['fence'],runtime['deployment'])
        pins={'stream':{'commit_sha':heads['stream'],'revision':envelope['revision'],
                        'blob_sha':oid('blob',stream_raw),'snapshot_digest':envelope['body_digest']},
              'fence':{'commit_sha':heads['fence'],'revision':len(list(b.commits(fr,heads['fence'],None,budget)))-1,
                       'blob_sha':fence_blob,'body_sha256':digest(fence_value)}}
        if runtime.get('pins') is not None and runtime['pins']!=pins: raise ValueError('Explicit reviewed cut differs')
        mig=migration(source,runtime['migration'],Path(root)/'migration')
        plan={'stream_source':str(sr),'fence_source':str(fr),'migration':str(mig),'identity':runtime['identity'],
              'deployment':runtime['deployment'],'pins':pins,'out':str(Path(root)/'pair')}
        result=pair.append(plan,budget=budget);m=result['manifest']
        m['hosted']={'expected_start_ms':slot,'producer':{k:binding[k] for k in ('repository','workflow','branch','code_sha')},
                     'producer_run_id':os.environ['GITHUB_RUN_ID'],'entry_sha':os.environ['GITHUB_SHA']}
        # Stamp the occurrence into the immutable manifest, then verify that exact
        # final manifest. An old package cannot earn today's verifier receipt.
        pair.restore(Path(root)/'pair',m,Path(root)/'final-manifest-blocked',pins,budget)
        raw=(canonical(m)+'\n').encode()
        additions={name:(Path(root)/'pair'/name).read_bytes() for name in m['files']}
        if any(len(additions[name])!=item['bytes'] or hashlib.sha256(additions[name]).hexdigest()!=item['sha256']
               for name,item in m['files'].items()): raise ValueError('Verified package changed before publication')
        additions.update({MANIFEST:raw,'manifests/'+digest(m)+'.json':raw})
        for t,key in ((s,'stream'),(f,'fence')):
            if source.ref(t)!=heads[key]: raise ValueError('Source cut moved before upload')
        pub=publish(backup,bt,base,additions,{MANIFEST})
        for t,key in ((s,'stream'),(f,'fence')):
            if source.ref(t)!=heads[key]: raise ValueError('Source moved during publication; no upload receipt')
        result={'schema':'btc-hosted-upload-confirmed-v1','manifest_sha256':digest(m),'pins':m['pins'],
                'expected_start_ms':slot,'destination':{**bt,**{k:pub[k] for k in ('commit_sha','tree_sha')},
                    'manifest_path':'manifests/'+digest(m)+'.json','blob_sha':oid('blob',raw)},
                'upload_readback_verified':True}
    else:
        m,dest=download(backup,bt,base,Path(root)/'download')
        if (runtime.get('pins') is not None and m['pins']!=runtime['pins']) or m['deployment']!=runtime['deployment']:
            raise ValueError('Independent cut differs')
        h=m['hosted'];producer=runtime['producer']
        if h['expected_start_ms']!=slot or h['producer']!={k:producer[k] for k in ('repository','workflow','branch','code_sha')}:
            raise ValueError('Old/foreign producer occurrence')
        meta=clients['metadata_read'].request('GET',producer['repository'],'/actions/runs/'+h['producer_run_id'])
        if (str(meta['id'])!=h['producer_run_id'] or meta['run_attempt']!=1 or meta['repository']['id']!=producer['repository_id']
                or meta['repository']['full_name']!=producer['repository'] or meta['path']!=producer['workflow']
                or meta['head_branch']!=producer['branch'] or meta['head_sha']!=h['entry_sha']
                or meta['status']!='completed' or meta['conclusion']!='success' or slots.run_slot('backup',meta)!=slot):
            raise ValueError('Actual successful producer run missing')
        from reviewed_actions_entry import verify
        verify(clients['metadata_read'],producer['repository'],h['entry_sha'],producer['code_sha'],
               producer['workflow'],producer['workflow_sha256'])
        # Authenticate each backed-up pin against the actual source repository.
        # Live sources may have advanced after the producer; no freeze is invented.
        for t,key,path in ((s,'stream',github.STORE_PATH),(f,'fence',actions.FENCE_PATH)):
            pin=m['pins'][key]['commit_sha'];v=source.request('GET',t['repository'],
                '/compare/'+pin+'...'+heads[key]+'?per_page=1')
            if v['base_commit']['sha']!=pin or v['merge_base_commit']['sha']!=pin or v['status'] not in ('ahead','identical'):
                raise ValueError('Backup pin not in authenticated source history')
            _,files=source.tree(t,pin)
            raw=source.blob(t,files[path])
            if oid('blob',raw)!=m['pins'][key]['blob_sha']: raise ValueError('Source pin bytes differ')
        verification=pair.restore(Path(root)/'download',m,Path(root)/'fresh-blocked',m['pins'],budget)
        if backup.ref(bt)!=base: raise ValueError('Backup moved during independent verification')
        for t,key in ((s,'stream'),(f,'fence')):
            if source.ref(t)!=heads[key]: raise ValueError('Source cut moved during verification')
        receipt={'schema':'p4-independent-backup-receipt-v1','manifest':m,'manifest_sha256':digest(m),
            'verification':verification,'expected_start_ms':slot,
            'verifier':{k:binding[k] for k in ('repository','workflow','branch','code_sha')},
            'verifier_run_id':os.environ['GITHUB_RUN_ID'],'destination':dest,'upload_readback_verified':True}
        raw=(canonical(receipt)+'\n').encode()
        if len(raw)>b.MAX_MANIFEST: raise ValueError('Independent receipt limit')
        rc=clients['receipt_write'];rt=runtime['receipts'];rp=rc.ref(rt)
        _,old=rc.tree(rt,rp)
        if set(old)-{RECEIPT}-{n for n in old if re.fullmatch(r'receipts/[0-9a-f]{64}\.json',n)}:
            raise ValueError('Foreign receipt destination')
        if RECEIPT in old:
            previous=json.loads(rc.blob(rt,old[RECEIPT]))
            if previous['expected_start_ms']>=slot: raise ValueError('Receipt occurrence replay/rollback')
        pub=publish(rc,rt,rp,{RECEIPT:raw,'receipts/'+digest(receipt)+'.json':raw},{RECEIPT})
        if backup.ref(bt)!=base: raise ValueError('Backup moved during receipt publication')
        result={**receipt,'receipt_publication':{**rt,'commit_sha':pub['commit_sha'],'tree_sha':pub['tree_sha'],
                                               'blob_sha':oid('blob',raw)}}
    result['metrics']={**budget.metrics(),'http':budget.http,'mutations':budget.mutations,
                       'reserved_transfer_bytes':budget.transfer}
    b.write_json(Path(root)/'confirmed.json',result)
    return result


def cli(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=tuple(ROLES));args=parser.parse_args(argv)
    try:
        raw=os.environ['BTC_HOSTED_RUNTIME_JSON'].encode()
        if len(raw)>b.MAX_MANIFEST: raise ValueError('Runtime byte bound')
        runtime=json.loads(raw)
        # Validate before reading any roles or making any provider request.
        validate(runtime,args.mode,check_checkout=False)
        if os.name=='posix':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(b.MAX_PYTHON_RSS,b.MAX_PYTHON_RSS))
        parent=Path(os.environ['RUNNER_TEMP']).resolve()
        if not parent.is_dir() or parent.is_symlink(): raise ValueError('Exclusive runner temp required')
        root=Path(tempfile.mkdtemp(prefix='btc-'+args.mode+'-',dir=parent))
        # Retain temp evidence until hosted runner teardown; no local artifact upload.
        run(runtime,args.mode,root)
        print('Hosted backup exact destination confirmation completed.')
        return 0
    except Exception:
        print('Hosted backup refused; no unconfirmed publication receipt.',file=sys.stderr)
        return 20


if __name__=='__main__': sys.exit(cli())
