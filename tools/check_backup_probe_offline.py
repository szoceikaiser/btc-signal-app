"""New preparation-focused checks; synthetic HTTP in memory, no provider access.

Does not run any old test suite or obtain data from old market fixtures.
"""
from copy import deepcopy
from datetime import datetime
import base64
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import urllib.parse
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import p4_backup_probe_prepare as prep
import p4_backup_probe as probe
import p4_hosted_backup as h
import p3_backup_chain as b
import public_access as public
from production_contract import canonical,digest
from test_free_public import access_for,writer_review


class Reply(io.BytesIO):
    status=200
    headers={}


class LocalHTTP:
    def __init__(self,root,runtime,rules,sets):
        self.root=root;self.runtime=runtime;self.rules=rules;self.sets=sets;self.rows=[];self.metadata={}
        self.repos={prep.STORE:root/'store.git',prep.BACKUP:root/'backup.git',prep.RECEIPTS:root/'receipts.git'}
        self.tokens={prep.STORE:'fake-store',prep.BACKUP:'fake-backup',prep.RECEIPTS:'fake-receipt'}

    def open(self,req,timeout):
        u=urllib.parse.urlsplit(req.full_url);method=req.get_method()
        self.rows.append({'method':method,'host':u.netloc,'path':u.path})
        def reply(v): return Reply(canonical(v).encode())
        if u.netloc=='raw.githubusercontent.com':
            parts=u.path.strip('/').split('/');repo='/'.join(parts[:2]);pin=parts[2];name='/'.join(parts[3:])
            assert req.get_header('Authorization')=='Bearer fake-job'
            if repo==prep.CODE: return Reply((self.root/'workflow-overlay'/name).read_bytes())
            return Reply(subprocess.check_output(['git','cat-file','blob',pin+':'+name],cwd=self.repos[repo]))
        if u.netloc=='github.com':
            repo=u.path.split('.git/')[0].lstrip('/');local=self.repos[repo]
            assert base64.b64decode(req.get_header('Authorization').removeprefix('Basic '))==b'x-access-token:fake-job'
            def pkt(raw): return f'{len(raw)+4:04x}'.encode()+raw
            if method=='GET':
                rows=prep.git(local,'for-each-ref','--format=%(objectname) %(refname)','refs/heads').splitlines()
                raw=pkt(b'# service=git-upload-pack\n')+b'0000'
                for i,row in enumerate(rows): raw+=pkt((row+('\0side-band-64k ofs-delta no-progress' if i==0 else '')+'\n').encode())
                return Reply(raw+b'0000')
            want=req.data[4:].split()[1].decode()
            raw=subprocess.check_output(['git','pack-objects','--stdout','--revs'],cwd=local,input=(want+'\n').encode())
            return Reply(pkt(b'NAK\n')+b''.join(pkt(b'\x01'+raw[i:i+65500]) for i in range(0,len(raw),65500))+b'0000')
        assert u.netloc=='api.github.com'
        parts=u.path.split('/');repo='/'.join(parts[2:4]);tail='/'+('/'.join(parts[4:])) if len(parts)>4 else ''
        assert req.get_header('Authorization')=='Bearer '+('fake-job' if method=='GET' else self.tokens[repo])
        if not tail: return reply({'id':prep.REPOS[repo]['id'],'full_name':repo,'private':False,'visibility':'public'})
        if tail.startswith('/rules/branches/'): return reply(self.rules[(repo,tail.rsplit('/',1)[1])])
        if tail.startswith('/rulesets/'): return reply(self.sets[(repo,int(tail.rsplit('/',1)[1]))])
        if tail.startswith('/actions/runs/'): return reply(self.metadata[tail.rsplit('/',1)[1]])
        local=self.repos[repo]
        if tail.startswith('/git/commits/'):
            pin=tail.rsplit('/',1)[1];raw=subprocess.check_output(['git','cat-file','commit',pin],cwd=local)
            rows=raw.split(b'\n\n')[0].splitlines()
            return reply({'sha':pin,'tree':{'sha':rows[0][5:].decode()},'parents':[{'sha':v[7:].decode()} for v in rows if v.startswith(b'parent ')]})
        if tail.startswith('/git/trees/'):
            pin=tail.rsplit('/',1)[1];rows=prep.git(local,'ls-tree','-r','-l',pin).splitlines();items=[]
            for row in rows:
                info,name=row.split('\t');mode,kind,sha,size=info.split()
                items.append({'path':name,'mode':mode,'type':kind,'sha':sha,'size':int(size)})
            return reply({'sha':pin,'truncated':False,'tree':items})
        if tail.startswith('/compare/'):
            left,right=tail.rsplit('/',1)[1].split('...');base=prep.git(local,'merge-base',left,right)
            return reply({'base_commit':{'sha':left},'merge_base_commit':{'sha':base},'status':'identical' if left==right else 'ahead'})
        payload=json.loads(req.data)
        if method=='POST' and tail=='/git/blobs': return reply({'sha':prep.object_write(local,'blob',base64.b64decode(payload['content']))})
        if method=='POST' and tail=='/git/trees':
            # All writes here replace the single stream/fence blob or add backup files.
            files={}
            for row in prep.git(local,'ls-tree','-r',payload['base_tree']).splitlines():
                info,name=row.split('\t');sha=info.split()[2]
                files[name]=subprocess.check_output(['git','cat-file','blob',sha],cwd=local)
            for v in payload['tree']: files[v['path']]=subprocess.check_output(['git','cat-file','blob',v['sha']],cwd=local)
            return reply({'sha':prep.tree_write(local,files)})
        if method=='POST' and tail=='/git/commits':
            a=payload['author'];stamp=int(datetime.fromisoformat(a['date'].replace('Z','+00:00')).timestamp())
            raw=(f"tree {payload['tree']}\nparent {payload['parents'][0]}\nauthor {a['name']} <{a['email']}> {stamp} +0000\n"
                 f"committer {a['name']} <{a['email']}> {stamp} +0000\n\n{payload['message']}\n").encode()
            return reply({'sha':prep.object_write(local,'commit',raw)})
        if method=='PATCH' and tail.startswith('/git/refs/heads/'):
            assert payload['force'] is False
            ref='refs/heads/'+tail.rsplit('/',1)[1];old=prep.git(local,'rev-parse',ref)
            prep.git(local,'merge-base','--is-ancestor',old,payload['sha']);prep.git(local,'update-ref',ref,payload['sha'],old)
            return reply({'object':{'sha':payload['sha']}})
        raise AssertionError((method,tail))


def check(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    pin=prep.git(ROOT,'rev-parse','HEAD');entry_pin='e'*40
    access,rules,sets=access_for(deepcopy(prep.REPOS))
    for role,repo,keys in (('sender_write',prep.STORE,('stream','fence')),('backup_write',prep.BACKUP,('backup',)),
                          ('receipt_write',prep.RECEIPTS,('receipts',))):
        writer_review(access,role,repo,[prep.BRANCHES[k] for k in keys])
    runtime=prep.prepare(out/'fixture',pin,access,entry_pin)
    http=LocalHTTP(out/'fixture',runtime,rules,sets);slot=1792022400000
    results={};roots={};checks=[]
    envs={}
    blocked=lambda *a,**kw: (_ for _ in ()).throw(AssertionError('Real network forbidden in offline check'))
    with patch.object(socket,'create_connection',side_effect=blocked),patch.object(socket.socket,'connect',side_effect=blocked),\
         patch.object(h.Client,'open_request',side_effect=http.open),patch.object(h.platform,'system',return_value='Linux'),\
         patch.object(h,'check_code_pin'),patch.object(h.time,'time',return_value=(slot+60000)/1000):
        for mode,rid,key in (('store','301','store_writer'),('producer','302','producer'),('verifier','303','verifier')):
            binding=runtime[key];root=out/mode;root.mkdir();roots[mode]=root
            meta={'id':int(rid),'run_number':1,'run_attempt':1,'repository':{'full_name':prep.CODE,'id':1309164619},
                'head_sha':entry_pin,'head_branch':'main','path':binding['workflow'],'event':'workflow_dispatch',
                'display_title':'btc-v2:backup:'+str(slot),'created_at':'2026-10-15T00:00:01Z',
                'updated_at':'2026-10-15T00:01:00Z','status':'completed','conclusion':'success'}
            http.metadata[rid]=meta
            env={**{k:os.environ[k] for k in ('PATH','SystemRoot','TEMP','TMP') if k in os.environ},
                'GITHUB_TOKEN':'fake-job','GITHUB_REPOSITORY':prep.CODE,'GITHUB_REF':'refs/heads/main',
                'GITHUB_WORKFLOW_REF':prep.CODE+'/'+binding['workflow']+'@refs/heads/main','GITHUB_SHA':entry_pin,
                'GITHUB_RUN_ID':rid,'GITHUB_RUN_NUMBER':'1','GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'workflow_dispatch',
                'RUNNER_OS':'Linux','BTC_HOSTED_RUNTIME_SHA256':runtime['runtime_sha256'],
                'BTC_ACTIONS_EXPLICIT_START_MS':str(slot)}
            env[{'store':'BTC_REVIEWED_STORE_TOKEN','producer':'BTC_HOSTED_BACKUP_WRITE_TOKEN','verifier':'BTC_HOSTED_RECEIPT_WRITE_TOKEN'}[mode]]='fake-'+{'store':'store','producer':'backup','verifier':'receipt'}[mode]
            envs[mode]=env
            start=len(http.rows)
            with patch.dict(os.environ,env,clear=True):
                if mode=='store': results[mode]=probe.store(runtime,root)
                else:
                    with patch.object(h,'Budget',probe.ProbeBudget): results[mode]=h.run(runtime,mode,root)
            for row in http.rows[start:]: row['phase']=mode
            if mode=='store':
                runtime=prep.seal_cut(runtime,results['store']);http.runtime=runtime
        v=results['verifier'];m=v['manifest']
        assert m['stream']['history_count']==2 and m['fence']['history_count']==3
        assert m['pins']==results['store']['pins']
        assert v['verification']['restore_blocked_verified'] and v['verification']['history_verified']
        assert (roots['verifier']/'fresh-blocked/RESTORE-BLOCKED.json').is_file()
        assert v['destination']['commit_sha']==results['producer']['destination']['commit_sha']
        checks+=['synthetic migration accepted','store writer: three publications, blocked source retained',
                 'full stream 2 commits + fence 3 commits + migration',
                 'producer upload and independent verifier download/blocked restore/receipt readback']
        for wrong in ('replay','writer_injection'):
            env=deepcopy(envs['store'])
            env['BTC_HOSTED_RUNTIME_SHA256']=runtime['runtime_sha256']
            if wrong=='writer_injection': env['BTC_HOSTED_RECEIPT_WRITE_TOKEN']='fake-receipt'
            start=len(http.rows)
            try:
                with patch.dict(os.environ,env,clear=True): probe.store(runtime,out)
            except ValueError: pass
            else: raise AssertionError('Store replay/role mixing accepted')
            assert not any(r['method']!='GET' for r in http.rows[start:])
        checks.append('store replay and receipt-writer injection refused without mutation')
        # Explicit negative checks around new entry binding, before any mutation.
        calls=len(http.rows)
        for mutation in ('entry','scope','hash'):
            bad=deepcopy(runtime);bind=bad['producer']
            if mutation=='entry': bind['probe_entry_sha']='invalid-anchor'
            if mutation=='scope': bad['source']['branch']='delivery-stream-v2'
            if mutation=='hash': bind['workflow_sha256']='0'*64
            try:
                with patch.dict(os.environ,{'GITHUB_TOKEN':'fake-job'},clear=True):
                    client=h.Client('fake-job',{prep.CODE},set(),probe.ProbeBudget(out),metadata=True)
                    h.verify_binding(client,bad,bind,entry_pin)
            except ValueError: pass
            else: raise AssertionError('Negative entry accepted: '+mutation)
        assert not any(r['method']!='GET' for r in http.rows[calls:])
        checks.append('wrong entry / production scope / wrong workflow hash refused without mutation')
        # Existing callers retain the old code-ancestry verification arguments.
        with patch('reviewed_actions_entry.verify') as verify:
            binding=deepcopy(runtime['producer']);del binding['probe_entry_sha']
            h.verify_binding(None,runtime,binding,entry_pin)
            assert verify.call_args.args[2:4]==(entry_pin,pin)
        checks.append('normal hosted path retains production-code ancestry contract')
    # Disabled preview cannot obtain a runtime admission, and same output is never overwritten.
    inactive=prep.prepare(out/'inactive',pin)
    try: probe.validate(inactive)
    except ValueError: pass
    else: raise AssertionError('Inactive runtime admitted')
    try: prep.prepare(out/'inactive',pin)
    except FileExistsError: pass
    else: raise AssertionError('Fixture overwritten')
    checks.append('disabled preview and existing output refused')
    prep.put(out/'RESULT.json',{'offline_only':True,'provider_proof':False,'checks':checks,
        'results':results,'requests':http.rows,'network_socket_allowed':False,
        'mocked_platform_and_checkout':True,'code_sha':pin})
    print(canonical({'passed':len(checks),'provider_proof':False,'results':str(out/'RESULT.json')}))


if __name__=='__main__': check(sys.argv[1])
