"""Focused synthetic recovery integration; actual HTTP serializer and local Git.

No real identities/keys. Existing migration/backup fixtures create reproducible
independent repositories. All resulting Git commits here are SYNTHETIC.
"""
import base64
from contextlib import closing
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import continuous_operations as ops
import safe_recovery as recovery
import actions_delivery as actions
import github_delivery as g
import p4_backup_pair as pair
import p3_backup_chain as b
import actions_freshness as monitor
from production_contract import canonical,digest
from test_hosted_backup import Provider
from test_betriebsabschluss import commit_file
from github_freshness import iso

def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.PIPE)
def record(repo,pin,path):
    body=git(repo,'show',pin+':'+path)
    return dict(body=body,commit_sha=pin,blob_sha=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest())

class HTTP:
    def __init__(self,root):
        self.provider=Provider(root/'provider',mode='open')
        p=self.provider;self.d=p.runtime['deployment'];self.repo=self.d['private_store_repository']
        self.source=p.repos[(self.repo,self.d['store_branch'])]
        self.fence_repo=p.repos[(self.repo,self.d['fence_branch'])]
        self.fence=deepcopy(p.fence);self.incident=git(self.fence_repo,'rev-parse','HEAD').decode().strip() if False else git(self.fence_repo,'rev-parse','refs/heads/'+self.d['fence_branch']).decode().strip()
        self.slot=int(self.fence['run']['expected_start_ms']);self.now=(self.slot+300000)/1000
        self.yaml=(ROOT/'.github/workflows/signal.yml').read_bytes()
        self.policy={'schema':'btc-continuous-recovery-v1','enabled':True,'activation_reviewed':True,
                     'deployment':self.d,'public_access':p.access,'entry_workflows':{'.github/workflows/signal.yml':hashlib.sha256(self.yaml).hexdigest()}}
        old=record(self.source,self.head(self.d['store_branch']),g.STORE_PATH);env=json.loads(old['body'])
        self.original_revision=env['revision'];snapshot=env['snapshot']
        # A fully confirmed synthetic message, never a real target or send.
        import telegram_outbox as box
        delivery=snapshot['engine']['_delivery']
        box.enqueue(delivery,'fixture','synthetic-confirmed',0,{'synthetic':True},'SYNTHETIC ONLY')
        delivery['messages'][-1].update(status='confirmed',attempts=1,receipt=17,target=snapshot['control']['target_binding'])
        snapshot['engine']['last_signal_ts']=self.slot//14400000*14400000-14400000
        r=self.fence['run'];current=dict(repository=self.d['code_repository'],workflow=r['workflow'],run_id=r['id'],run_attempt='1',kind='signal',
            expected_start_ms=self.slot,code_sha=self.d['code_sha'],config_sha256=self.d['config_sha256'],status='completed',
            started_ms=self.slot+1000,finished_ms=self.slot+2000)
        complete={**current,'revision':env['revision']+1,'last_signal_ts':snapshot['engine']['last_signal_ts']}
        snapshot['control']['health'].update(current_run=current,completion_candidate=complete)
        env=self.append_stream(env)
        loc=self.locate(env)
        snapshot=env['snapshot'];snapshot['control']['health']['successful_runs']={'signal':{'run':complete,'completion':loc}}
        self.env=self.append_stream(env)
        self.meta=dict(id=10,run_number=r['number'],run_attempt=1,path=r['workflow'],head_sha=self.d['code_sha'],
            repository={'full_name':self.d['code_repository']},head_branch='synthetic',status='completed',conclusion='failure')
        self.jobs=dict(total_count=1,jobs=[dict(run_id=10,run_attempt=1,head_sha=self.d['code_sha'],
            status='completed',conclusion='failure',completed_at=iso(self.slot+3000),labels=['ubuntu-24.04'])])
        self.puts=[];self.requests=[];self.loss=None;self.move_on_get=None
    def head(self,branch):
        repo=self.source if branch==self.d['store_branch'] else self.fence_repo
        return git(repo,'rev-parse','refs/heads/'+branch).decode().strip()
    def append_stream(self,env):
        env=deepcopy(env);prior=self.head(self.d['store_branch'])
        env.update(revision=env['revision']+1,parent_digest=env['body_digest'],body_digest=digest(env['snapshot']),write_id='synthetic-'+str(env['revision']+1))
        commit_file(self.source,self.d['store_branch'],g.STORE_PATH,canonical(env).encode(),prior)
        return env
    def locate(self,env):
        rec=record(self.source,self.head(self.d['store_branch']),g.STORE_PATH)
        return dict(adapter='github',repo=self.repo,branch=self.d['store_branch'],path=g.STORE_PATH,
            store_id=self.d['store_id'],revision=env['revision'],commit_sha=rec['commit_sha'],blob_sha=rec['blob_sha'],snapshot_digest=env['body_digest'])
    def open(self,request,timeout):
        assert timeout==3
        u=urllib.parse.urlsplit(request.full_url);self.requests.append(request.get_method())
        code=u.path=='/repos/'+self.d['code_repository'] or u.path.startswith('/repos/'+self.d['code_repository']+'/')
        repo=self.d['code_repository'] if code else self.repo
        tail=u.path.removeprefix('/repos/'+repo)
        if tail=='':
            value=dict(id=self.policy['public_access']['repositories'][repo]['id'],full_name=repo,private=False,visibility='public')
        elif tail.startswith('/rules/branches/'):
            value=self.provider.rules[(repo,tail.rsplit('/',1)[1])]
        elif tail.startswith('/rulesets/'):
            value=self.provider.rulesets[(repo,int(tail.rsplit('/',1)[1]))]
        elif code:
            assert not request.has_header('Authorization')
            if tail=='/actions/runs/10':value=self.meta
            elif '/attempts/1/jobs' in tail:value=self.jobs
            elif tail.startswith('/actions/runs'):value={'total_count':0,'workflow_runs':[]}
            elif tail.startswith('/contents/'):
                value=dict(type='file',encoding='base64',content=base64.b64encode(self.yaml).decode(),
                    sha=hashlib.sha1(b'blob '+str(len(self.yaml)).encode()+b'\0'+self.yaml).hexdigest())
            else:raise AssertionError('Unexpected code route '+tail)
        elif request.get_method()=='PUT':
            payload=json.loads(request.data);assert tail=='/contents/'+actions.FENCE_PATH
            assert payload['branch']==self.d['fence_branch']
            old=self.head(self.d['fence_branch']);rec=record(self.fence_repo,old,actions.FENCE_PATH)
            assert rec['blob_sha']==payload['sha'];self.puts.append(payload)
            if self.loss=='before':self.loss=None;raise TimeoutError('SYNTHETIC lost before save')
            pin=commit_file(self.fence_repo,self.d['fence_branch'],actions.FENCE_PATH,base64.b64decode(payload['content']),old)
            if self.loss in ('after','crash'):
                mode=self.loss;self.loss=None
                if mode=='crash':raise SystemExit('SYNTHETIC process loss')
                raise TimeoutError('SYNTHETIC lost reply')
            value={'commit':{'sha':pin}}
        elif tail.startswith('/git/ref/heads/'):
            value={'object':{'sha':self.head(tail.rsplit('/',1)[1])}}
        elif tail.startswith('/contents/'):
            path=tail[len('/contents/'):];pin=urllib.parse.parse_qs(u.query)['ref'][0]
            rec=record(self.source if path==g.STORE_PATH else self.fence_repo,pin,path)
            value=dict(type='file',encoding='base64',sha=rec['blob_sha'],content=base64.b64encode(rec['body']).decode())
        elif tail.startswith('/git/commits/'):
            pin=tail.rsplit('/',1)[1];parents=git(self.fence_repo,'show','-s','--format=%P',pin).decode().split()
            value={'parents':[{'sha':p} for p in parents]}
        elif tail.startswith('/compare/'):
            base,head=tail[len('/compare/'):].split('...');git(self.source,'merge-base','--is-ancestor',base,head)
            value={'base_commit':{'sha':base},'merge_base_commit':{'sha':base},'status':'ahead'}
        else:raise AssertionError('Unexpected store route '+tail)
        response=io.BytesIO(canonical(value).encode());response.headers={'X-RateLimit-Resource':'core','X-RateLimit-Remaining':'59'}
        return response

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.http=HTTP(self.root);self.journal=self.root/'operation.sqlite'
        self.net=patch('urllib.request.urlopen',side_effect=AssertionError('REAL NETWORK FORBIDDEN'))
        self.net.start();self.addCleanup(self.net.stop)
    def client(self):return ops.Client('SYNTHETIC-NOT-A-KEY',self.http.policy,self.journal,self.http.incident,self.http.open,lambda:self.http.now)
    def test_close_only_normal_recovery_and_duplicate(self):
        before=self.http.head(self.http.d['store_branch'])
        result=ops.recover(self.client());self.assertEqual(result['state'],'recovered-await-fresh-regular-run')
        self.assertEqual(self.http.head(self.http.d['store_branch']),before)
        self.assertEqual(len(self.http.puts),1)
        ops.recover(self.client());self.assertEqual(len(self.http.puts),1)
        self.assertEqual(self.http.meta['conclusion'],'failure')
    def test_lost_reply_and_process_loss_after_write(self):
        for mode in ('after','crash'):
            with self.subTest(mode=mode):
                if mode=='crash':self.setUp()
                self.http.loss=mode
                if mode=='crash':
                    with self.assertRaises(SystemExit):ops.recover(self.client())
                else:ops.recover(self.client())
                self.http.requests=[];ops.recover(self.client())
                self.assertTrue(all(x=='GET' for x in self.http.requests))
                self.assertEqual(len(self.http.puts),1)
    def test_unknown_unsaved_write_consumes_budget(self):
        self.http.loss='before'
        with self.assertRaises(ValueError):ops.recover(self.client())
        with self.assertRaises(ValueError):ops.recover(self.client())
        self.assertEqual(len(self.http.puts),1)
        with closing(sqlite3.connect(self.journal)) as db:
            self.assertEqual(db.execute('SELECT sent FROM reservation').fetchone(),(1,))
    def test_foreign_owner_uncertain_live_worker_block(self):
        source=deepcopy(self.http.env)
        for case in ('owner','uncertain','worker'):
            with self.subTest(case=case):
                if case=='owner':self.http.env['snapshot']['control']['owner']={'foreign':'alive'}
                elif case=='uncertain':
                    self.http.env=deepcopy(source);self.http.env['snapshot']['engine']['_delivery']['messages'][-1]['status']='uncertain'
                else:self.http.env=deepcopy(source);self.http.jobs['jobs'][0]['status']='in_progress'
                self.http.env=self.http.append_stream(self.http.env)
                with self.assertRaises((ValueError,g.StoreConflict)):ops.recover(self.client())
        self.assertFalse(self.http.puts)
    def test_restart_does_not_extend_deadline_or_accept_other_policy(self):
        self.client();self.http.now+=901
        with self.assertRaises(ValueError):ops.recover(self.client())
        self.http.policy['activation_reviewed']=False
        with self.assertRaises(ValueError):self.client()
    def test_actual_admission_requires_new_regular_slot(self):
        ops.recover(self.client());h=self.http
        fence_rec=record(h.fence_repo,h.head(h.d['fence_branch']),actions.FENCE_PATH)
        fence=json.loads(fence_rec['body']);source=record(h.source,h.head(h.d['store_branch']),g.STORE_PATH)
        client=actions.ActionsClient.__new__(actions.ActionsClient)
        client.fence_read=lambda deployment:(fence_rec,deepcopy(fence))
        client.read=lambda *args:source
        client.parents=lambda *args:[h.incident]
        writes=[];client.fence_write=lambda old,new:writes.append(new)
        old={**fence['run'],'number':2,'id':'11'}
        with self.assertRaises(g.StoreConflict):client.acquire(h.d,old)
        self.assertFalse(writes)
        fresh={**old,'expected_start_ms':str(h.slot+14400000)}
        client.acquire(h.d,fresh)
        self.assertEqual(len(writes),1);self.assertTrue(client.admitted)
        self.assertNotIn('recovery',writes[0].get('completion') or {})
    def test_monitor_failure_is_controlled_and_never_exposes_exception(self):
        marker='NEVER-PUBLISH-EXCEPTION-CONTENT'
        class Failed:
            def read(self,*args):raise RuntimeError(marker)
        p={'enabled':True,'schema':'p4-actions-monitor-v1','deployment':{**self.http.d,'schedule_contract':'btc-actions-slots-v1'}}
        result=monitor.check(Failed(),None,None,p,int(self.http.now*1000))
        self.assertEqual(result['diagnostic']['phase'],'fence')
        self.assertEqual(result['http_status'],503)
        self.assertNotIn(marker,canonical(result))
        import pinned_delivery_entry as entry
        public=entry.public_monitor_result({**result,'secret':marker})
        self.assertEqual(public,{'phase':'fence','status':'refused_or_halted'})
        public=entry.public_monitor_result({'http_status':503,'diagnostic':{'phase':marker,'stream_commit':marker}})
        self.assertEqual(public,{'phase':'monitor','status':'refused_or_halted'})
    def test_independent_real_git_backup_restore_retains_marker(self):
        ops.recover(self.client());h=self.http;pin=h.head(h.d['store_branch']);fpin=h.head(h.d['fence_branch'])
        srec=record(h.source,pin,g.STORE_PATH);frec=record(h.fence_repo,fpin,actions.FENCE_PATH);env=json.loads(srec['body'])
        count=int(git(h.fence_repo,'rev-list','--count',fpin).decode())
        pins=dict(stream=dict(commit_sha=pin,revision=env['revision'],blob_sha=srec['blob_sha'],snapshot_digest=env['body_digest']),
            fence=dict(commit_sha=fpin,revision=count-1,blob_sha=frec['blob_sha'],body_sha256=digest(json.loads(frec['body']))))
        plan=dict(stream_source=str(h.source),fence_source=str(h.fence_repo),deployment=h.d,identity=h.provider.fixture['identity'],
                  migration=h.provider.fixture['migration'],pins=pins,out=str(self.root/'pair'))
        result=pair.append(plan)
        restored=pair.restore(self.root/'pair',result['manifest'],self.root/'fresh-independent-restore',pins)
        self.assertFalse(restored['enabled']);self.assertTrue(restored['restore_blocked_verified'])
        old=json.loads((self.root/'fresh-independent-restore/actions-fence.original.json').read_bytes())
        self.assertIn('recovery',old['completion']);self.assertEqual(old['cursors'],h.fence['cursors'])
        self.assertTrue((self.root/'fresh-independent-restore/RESTORE-BLOCKED.json').is_file())
        import produktion_pages_export as pages
        client=self.client()
        with self.assertRaises(g.StoreConflict):pages.observe(client,h.d,env['snapshot']['engine']['config'])

if __name__=='__main__':unittest.main(verbosity=2)
