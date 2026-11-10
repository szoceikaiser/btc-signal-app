"""Only synthetic service responses; real Git histories persist across runners."""
import base64
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from unittest.mock import patch
import threading
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import github_recovery as r
import github_recovery_journal as j
import continuous_operations as old
import safe_recovery as safe
from production_contract import canonical,digest
from test_continuous_operations import HTTP,git,record
from test_betriebsabschluss import commit_file
from test_free_public import access_for,writer_review

class Service(HTTP):
    def __init__(self,root,owner=False):
        super().__init__(root)
        self.jrepo=root/'journal.git';self.jrepo.mkdir();git(self.jrepo,'init','--bare')
        self.seed=commit_file(self.jrepo,'recovery-journal-live','recovery/seed.json',b'{"synthetic":true}')
        repos=deepcopy(self.policy['public_access']['repositories'])
        repos[self.repo]['branches'].append('recovery-journal-live')
        access,rules,sets=access_for(repos)
        writer_review(access,'recovery_journal_write',self.repo,['recovery-journal-live'])
        from public_access import review_hash
        proof=access['credential_reviews']['recovery_journal_write'];proof['credential_reference']='github-fine-grained-pat:21186996'
        proof['sha256']=review_hash(proof)
        self.provider.rules[(self.repo,'recovery-journal-live')]=rules[(self.repo,'recovery-journal-live')]
        for key,value in sets.items():
            if key[0]==self.repo and 'refs/heads/recovery-journal-live' in value['conditions']['ref_name']['include']:
                self.provider.rulesets[key]=value
        self.policy['journal']=dict(repository=self.repo,branch='recovery-journal-live',reviewed=True,
            seed_commit=self.seed,public_access=access,credential_reference='github-fine-grained-pat:21186996',
            required_permissions={'contents':'write','metadata':'read'})
        self.self_yaml=b'SYNTHETIC independently reviewed recovery entry\n'
        self.policy['recovery_entry']=dict(repository=self.d['code_repository'],branch='synthetic',code_sha=self.d['code_sha'],
            workflow='.github/workflows/recovery.yml',workflow_sha256=__import__('hashlib').sha256(self.self_yaml).hexdigest())
        self.own=dict(id=900,path='.github/workflows/recovery.yml',run_attempt=1,head_sha=self.d['code_sha'],
            head_branch='synthetic',repository={'full_name':self.d['code_repository']},status='in_progress')
        self.environment=dict(GITHUB_REPOSITORY=self.d['code_repository'],GITHUB_REF='refs/heads/synthetic',
            GITHUB_WORKFLOW_REF=self.d['code_repository']+'/.github/workflows/recovery.yml@refs/heads/synthetic',
            GITHUB_RUN_ID='900',GITHUB_RUN_ATTEMPT='1',GITHUB_JOB='recover',GITHUB_SHA=self.d['code_sha'])
        self.foreign=False;self.business=[];self.loss_step=None;self.control_loss=False
        if owner:
            self.env['snapshot']['control']['owner']=dict(repository=self.repo,run_id='10',run_attempt='1',nonce='SYNTHETIC-OWNER')
            self.env['snapshot']['control']['health']['current_run']['status']='failed'
            self.env=self.append_stream(self.env)
    def response(self,value):
        response=io.BytesIO(canonical(value).encode());response.headers={};return response
    def open(self,request,timeout):
        u=urllib.parse.urlsplit(request.full_url);tail=u.path.removeprefix('/repos/'+self.repo)
        code=u.path.startswith('/repos/'+self.d['code_repository'])
        if code:
            ct=u.path.removeprefix('/repos/'+self.d['code_repository'])
            if ct=='/actions/runs/900':return self.response(self.own)
            if ct.startswith('/actions/runs/900/attempts/'):
                return self.response({'total_count':1,'jobs':[dict(id=901,name='recover',run_id=900,run_attempt=1,
                    head_sha=self.d['code_sha'],status='in_progress',labels=['ubuntu-24.04'])]})
            if ct=='/contents/.github/workflows/recovery.yml':
                raw=self.self_yaml;h=__import__('hashlib').sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
                return self.response(dict(type='file',encoding='base64',content=base64.b64encode(raw).decode(),sha=h))
            if ct=='/actions/runs':
                items=[self.own]
                if self.foreign:items.append({**self.own,'id':902})
                return self.response(dict(total_count=len(items),workflow_runs=items))
            request.remove_header('Authorization') # Only synthetic metadata role, not Store role.
        if tail=='/git/ref/heads/recovery-journal-live':
            return self.response({'object':{'sha':git(self.jrepo,'rev-parse','refs/heads/recovery-journal-live').decode().strip()}})
        if tail.startswith('/compare/'):
            base,head=tail[len('/compare/'):].split('...')
            try:git(self.jrepo,'cat-file','-e',base)
            except Exception:return super().open(request,timeout)
            git(self.jrepo,'merge-base','--is-ancestor',base,head)
            return self.response({'base_commit':{'sha':base},'merge_base_commit':{'sha':base},'status':'ahead'})
        if tail.startswith('/contents/recovery/incidents/'):
            path=tail[len('/contents/'):]
            if request.get_method()=='GET':
                pin=urllib.parse.parse_qs(u.query)['ref'][0]
                try:rec=record(self.jrepo,pin,path)
                except Exception:raise urllib.error.HTTPError(request.full_url,404,'synthetic absent',{},None)
                return self.response(dict(type='file',encoding='base64',sha=rec['blob_sha'],content=base64.b64encode(rec['body']).decode()))
            payload=json.loads(request.data);head=git(self.jrepo,'rev-parse','refs/heads/recovery-journal-live').decode().strip()
            try:rec=record(self.jrepo,head,path)
            except Exception:rec=None
            if payload.get('sha')!=(rec['blob_sha'] if rec else None):raise urllib.error.HTTPError(request.full_url,409,'synthetic CAS',{},None)
            pin=commit_file(self.jrepo,'recovery-journal-live',path,base64.b64decode(payload['content']),head)
            if self.control_loss:self.control_loss=False;raise TimeoutError('SYNTHETIC LOST JOURNAL REPLY')
            return self.response({'commit':{'sha':pin}})
        if request.get_method()=='PUT':
            payload=json.loads(request.data);branch=payload['branch'];self.business.append(branch)
            if tail=='/contents/delivery/stream.json':
                previous=self.head(self.d['store_branch']);old_record=record(self.source,previous,'delivery/stream.json')
                assert payload['sha']==old_record['blob_sha']
                pin=commit_file(self.source,self.d['store_branch'],'delivery/stream.json',base64.b64decode(payload['content']),previous)
                result=self.response({'commit':{'sha':pin}})
            else:result=super().open(request,timeout)
            if branch==self.loss_step:
                self.loss_step=None;raise SystemExit('SYNTHETIC RUNNER LOSS AFTER BUSINESS SAVE')
            return result
        if tail.startswith('/git/commits/'):
            pin=tail.rsplit('/',1)[1]
            for repo in (self.source,self.fence_repo):
                try:parents=git(repo,'show','-s','--format=%P',pin).decode().split()
                except Exception:continue
                return self.response({'parents':[{'sha':p} for p in parents]})
        return super().open(request,timeout)

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
    def client(self,service):
        c=r.Network(service.policy,'SYNTHETIC-STORE','SYNTHETIC-METADATA',service.open,lambda:int(service.now*1000))
        identity=r.bind_self(c,service.environment)
        return c,identity
    def test_both_classes_server_journal_and_own_worker(self):
        for owner in (False,True):
            root=self.root/str(owner);root.mkdir();s=Service(root,owner)
            c,identity=self.client(s);result=r.run(c,identity)
            self.assertEqual(result['outcome'],'aborted' if owner else 'reconciled')
            self.assertEqual(len(s.business),2 if owner else 1)
            self.assertEqual(s.meta['conclusion'],'failure')
            # A new runner sees the same server journal and no local SQLite.
            c,identity=self.client(s);identity['attempt']='2';again=r.run(c,identity)
            self.assertEqual(again['phase'],'already-confirmed-no-write')
            self.assertEqual(len(s.business),2 if owner else 1)
    def test_stream_runner_loss_resumes_fence_only(self):
        s=Service(self.root,True);s.loss_step=s.d['store_branch']
        c,identity=self.client(s)
        with self.assertRaises(SystemExit):r.run(c,identity)
        c,identity=self.client(s);identity['attempt']='2'
        r.run(c,identity)
        self.assertEqual(s.business,[s.d['store_branch'],s.d['fence_branch']])
    def test_fence_loss_and_journal_reply_loss(self):
        s=Service(self.root);s.control_loss=True;s.loss_step=s.d['fence_branch']
        c,identity=self.client(s)
        with self.assertRaises(SystemExit):r.run(c,identity)
        c,identity=self.client(s);identity['attempt']='2';r.run(c,identity)
        self.assertEqual(s.business,[s.d['fence_branch']])
    def test_foreign_worker_is_not_hidden_by_self_exception(self):
        s=Service(self.root,True);s.foreign=True;c,identity=self.client(s)
        with self.assertRaises(ValueError):r.run(c,identity)
        self.assertEqual(s.business,[])
    def test_hard_wallclock_for_trickling_response(self):
        release=threading.Event();ended=threading.Event()
        class Trickle:
            headers={}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,size):
                try:release.wait(2);return b'{}'
                finally:ended.set()
        with patch('urllib.request.OpenerDirector.open',return_value=Trickle()):
            start=time.monotonic()
            try:
                with self.assertRaises(TimeoutError):old.no_redirect_transport()(None,.05)
                self.assertLess(time.monotonic()-start,.5)
            finally:release.set();self.assertTrue(ended.wait(1))

if __name__=='__main__':unittest.main(verbosity=2)
