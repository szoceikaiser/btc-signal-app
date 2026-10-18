"""Synthetic HTTP/transport fixtures through the actual production factory/runner."""
from contextlib import contextmanager, closing
from copy import deepcopy
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
from unittest.mock import patch

import durable_delivery as durable
import github_delivery as github
import production_confirmation as policy
from production_contract import canonical, digest
from test_github_delivery import fake_store, fails, REPO, BRANCH, STORE_ID, stage_message

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import produktion_runner as runner
import produktion_candidate_runner as entry


class HTTPFixture:
    def __init__(self, api, mode='happy', clock=None):
        self.api=api;self.mode=mode;self.clock=clock;self.seen=[];self.old=None;self.refs=0
        self.transport=[]

    def open(self, request, timeout):
        method=request.get_method();url=request.full_url
        self.seen.append((method,url,timeout))
        if method=='PUT':
            data=json.loads(request.data);self.old=deepcopy(self.api.record);self.refs=0
            if self.mode=='cas':
                raise urllib.error.HTTPError(url,409,'synthetic',{},None)
            if self.mode=='lost-before':raise TimeoutError('synthetic')
            commit=self.api.update(REPO,BRANCH,data['sha'],base64.b64decode(data['content']),data['message'].split()[-1],'delivery/stream.json')
            if self.mode=='lost-reply':raise TimeoutError('synthetic')
            result={'commit':{'sha':commit}}
        elif '/git/ref/heads/' in url:
            self.refs+=1
            old=(self.old is not None and (self.mode in ('old','lost-before') or self.mode=='delayed' and self.refs<=4))
            sha=(self.old if old else self.api.record)['commit_sha']
            if self.mode=='foreign-head' and self.old is not None:sha='f'*40
            if self.mode=='unstable' and self.old is not None:sha=self.old['commit_sha'] if self.refs%2 else 'f'*40
            if self.mode=='final-head' and self.old is not None and self.refs>=3:sha='f'*40
            result={'object':{'sha':sha}}
        elif '/contents/' in url:
            sha=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['ref'][0]
            record=self.api.records.get(sha,self.api.record)
            body=record['body']
            if self.mode=='foreign-bytes' and self.old is not None:body=self.old['body']
            if self.old is not None and self.mode in ('wrong-revision','wrong-write-id','wrong-lineage'):
                value=json.loads(body)
                field={'wrong-revision':'revision','wrong-write-id':'write_id','wrong-lineage':'parent_digest'}[self.mode]
                value[field]=value[field]+1 if field=='revision' else 'f'*64
                body=canonical(value).encode()
            blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
            result={'type':'file','encoding':'base64','sha':blob,'content':base64.b64encode(body).decode()}
        elif '/git/commits/' in url:
            sha=url.rsplit('/',1)[1]
            parents=self.api.parents(REPO,sha)
            if self.mode=='wrong-parent':parents=['f'*40]
            result={'parents':[{'sha':x} for x in parents]}
        elif '/compare/' in url:
            base,head=url.rsplit('/',1)[1].split('?')[0].split('...')
            result={'base_commit':{'sha':base},'merge_base_commit':{'sha':base},'status':'ahead' if base!=head else 'identical'}
        else:raise AssertionError('Unexpected synthetic route')
        if self.mode=='late' and self.old is not None:self.clock[0]+=900001
        raw=json.dumps(result).encode()
        if self.mode=='whitespace':raw=b' '*3000+raw
        return io.BytesIO(raw)


@contextmanager
def factory(mode='happy', overrides=None):
    with tempfile.TemporaryDirectory() as td, fake_store() as api:
        root=Path(td);data=root/'runner/data';data.mkdir(parents=True)
        clock=[1000000]
        cfg=json.loads((ROOT/'ops/produktion/github-runtime.disabled.json').read_text())['confirmation_budgets']
        cfg={**cfg,'deadline_utc_ms':clock[0]+900000,**(overrides or {})}
        binding={'repo':REPO,'branch':BRANCH,'store_id':STORE_ID,'run_id':'synthetic-100','run_attempt':'1','code_sha':'a'*40}
        config=root/'policy.json';config.write_text(canonical(cfg))
        journal=root/'requests.sqlite';policy.provision_journal(journal,cfg,binding,now_ms=clock[0])
        (data/'config.json').write_text(canonical(api.envelope()['snapshot']['engine']['config']))
        env={'BTC_DELIVERY_ADAPTER':'github','BTC_DELIVERY_STORE_ID':STORE_ID,
             'SYSTEMROOT':os.environ.get('SYSTEMROOT',r'C:\Windows'),
             'WINDIR':os.environ.get('WINDIR',r'C:\Windows'),
             'BTC_DELIVERY_RUNNER_ROOT':str(data.parent),'BTC_DELIVERY_GITHUB_REPO':REPO,
             'BTC_DELIVERY_GITHUB_BRANCH':BRANCH,'BTC_DELIVERY_GITHUB_TOKEN':'synthetic-only',
             'BTC_DELIVERY_RUN_ID':'synthetic-100','BTC_DELIVERY_RUN_ATTEMPT':'1',
             'BTC_DELIVERY_CODE_SHA':'a'*40,'BTC_DELIVERY_BOT_IDENTITY':'synthetic-bot',
             'BTC_DELIVERY_CONFIRMATION_POLICY':policy.POLICY,'BTC_DELIVERY_CONFIRMATION_CONFIG':str(config),
             'BTC_DELIVERY_REQUEST_JOURNAL':str(journal),'TELEGRAM_BOT_TOKEN':'synthetic-only',
             'TELEGRAM_CHAT_ID':'synthetic-target','BTC_DELIVERY_OPERATION_ID':'synthetic-request',
             'BTC_DELIVERY_RUN_REPOSITORY':'synthetic/code','BTC_DELIVERY_WORKFLOW':'.github/workflows/production-delivery.yml',
             'BTC_DELIVERY_EXPECTED_START_MS':'1791100800000','GITHUB_REPOSITORY':'synthetic/code',
             'GITHUB_RUN_ID':'synthetic-100','GITHUB_RUN_ATTEMPT':'1','GITHUB_SHA':'a'*40,
             'GITHUB_REF':'refs/heads/synthetic','GITHUB_WORKFLOW_REF':'synthetic/code/.github/workflows/production-delivery.yml@refs/heads/synthetic'}
        http=HTTPFixture(api,mode,clock)
        with patch.dict(os.environ,env,clear=True),patch.object(policy.time,'time',side_effect=lambda:clock[0]/1000),\
             patch.object(policy.ProductionContentsClient,'open_request',side_effect=http.open),\
             patch('urllib.request.urlopen',side_effect=AssertionError('Real network forbidden')):
            yield root,data,api,http,clock,cfg,binding


def journal_rows(root):
    with closing(sqlite3.connect(root/'requests.sqlite')) as db:
        return db.execute('SELECT method,request_bytes,response_reserved,response_bytes,status FROM requests').fetchall()


def test_actual_factory_delayed_third_cycle_and_lost_reply_exact_one_put():
    for mode,gets in (('happy',8),('delayed',14),('lost-reply',8)):
        with factory(mode) as (root,data,api,http,*_):
            store=durable.configured_store(data);store.__enter__()
            assert isinstance(store.client,policy.ProductionContentsClient)
            assert api.put_count==1 and store.revision==api.envelope()['revision']
            rows=journal_rows(root)
            assert sum(x[0]=='PUT' for x in rows)==1
            assert sum(x[0]=='GET' for x in rows)==gets,(mode,rows)
            assert all(x[4] in ('completed','failed') for x in rows)
            assert all(x[2]==2*1024*1024 for x in rows)


def test_old_foreign_bytes_parent_and_unstable_heads_poison_without_resend():
    for mode in ('old','lost-before','foreign-head','foreign-bytes','unstable','wrong-parent','final-head','cas','late','wrong-revision','wrong-write-id','wrong-lineage'):
        with factory(mode) as (root,data,api,http,*_):
            store=durable.configured_store(data)
            fails((github.StoreError,KeyError),store.__enter__)
            puts=sum(x[0]=='PUT' for x in http.seen)
            assert puts==1,(mode,http.seen)
            fails(github.StoreError,store._write)
            fails(github.StoreError,lambda:durable.configured_store(data))
            assert sum(x[0]=='PUT' for x in http.seen)==1


def test_deadline_run_budget_bytes_and_missing_budget_stop_before_http_or_put():
    with factory() as (root,data,api,http,clock,*_):
        clock[0]+=900000
        fails(github.StoreError,lambda:durable.configured_store(data));assert http.seen==[]
    with factory(overrides={'run_get_limit':11}) as (root,data,api,http,*_):
        fails(github.StoreError,lambda:durable.configured_store(data).__enter__())
        assert not any(x[0]=='PUT' for x in http.seen)
    with factory(overrides={'request_byte_limit':1}) as (root,data,api,http,*_):
        fails(github.StoreError,lambda:durable.configured_store(data).__enter__())
        assert not any(x[0]=='PUT' for x in http.seen)
    with factory('whitespace',{'response_byte_limit':2000}) as (root,data,api,http,*_):
        fails(github.StoreError,lambda:durable.configured_store(data).__enter__())
        assert len(http.seen)==1 and journal_rows(root)[0][3]==2001
    with factory() as (root,data,api,http,*_):
        for key,value in (('BTC_DELIVERY_CONFIRMATION_POLICY','unknown'),('BTC_DELIVERY_REQUEST_JOURNAL',''),
                          ('BTC_DELIVERY_STORE',str(root/'fallback'))):
            with patch.dict(os.environ,{key:value}):fails(ValueError,lambda:durable.configured_store(data))
        (root/'policy.json').write_text('{}')
        fails(ValueError,lambda:durable.configured_store(data));assert http.seen==[]


def test_default_one_cycle_and_no_implicit_journal_bootstrap():
    with factory() as (root,data,api,http,*_):
        with patch.dict(os.environ,{'BTC_DELIVERY_CONFIRMATION_POLICY':'','BTC_DELIVERY_CONFIRMATION_CONFIG':'','BTC_DELIVERY_REQUEST_JOURNAL':''}):
            store=durable.configured_store(data)
            assert type(store.client) is github.GitHubContentsClient
            assert getattr(store.client,'confirmation_attempts',1)==1
        missing=root/'missing.sqlite'
        with patch.dict(os.environ,{'BTC_DELIVERY_REQUEST_JOURNAL':str(missing)}):
            fails(github.StoreError,lambda:durable.configured_store(data));assert not missing.exists()
        inside=data/'journal.sqlite'
        with patch.dict(os.environ,{'BTC_DELIVERY_REQUEST_JOURNAL':str(inside)}):
            fails(ValueError,lambda:durable.configured_store(data));assert not inside.exists()
        assert http.seen==[]


def test_real_runner_test_transport_and_runtime_signal_reach_selected_factory():
    import telegram_notify as tg
    import main
    with factory('delayed') as (root,data,api,http,*_):
        sends=[]
        def send(text,token,target):
            assert token=='synthetic-only' and target=='synthetic-target';sends.append(text)
            return {'status':'confirmed','message_id':73,'target_binding':hashlib.sha256(target.encode()).hexdigest()}
        with patch.object(tg,'deliver_telegram',side_effect=send):runner.run_checked('test',data)
        assert len(sends)==1 and api.envelope()['snapshot']['control']['owner'] is None
        assert all(x[4]=='completed' for x in journal_rows(root))
    with factory() as (root,data,api,http,clock,cfg,*_):
        runtime=json.loads((ROOT/'ops/produktion/github-runtime.disabled.json').read_text())
        path=root/'runtime.json';path.write_text(canonical(runtime))
        fails(ValueError,lambda:entry.run_runtime(path,'signal',data,fetch=lambda _:([],[],[])))
        assert http.seen==[]
        runtime.update(enabled=True,activation_review_sha256='b'*64,private_store_repository=REPO,
            store_branch=BRANCH,store_id=STORE_ID,code_sha='a'*40,bot_identity='synthetic-bot',
            code_repository='synthetic/code',confirmation_config=str(root/'policy.json'),
            request_journal=str(root/'requests.sqlite'),
            config_sha256=digest(api.envelope()['snapshot']['engine']['config']))
        path.write_text(canonical(runtime))
        with patch.object(main,'deliver_telegram',side_effect=AssertionError('Unexpected send')):
            entry.run_runtime(path,'signal',data,fetch=lambda _:([],[],[]))
        assert any(x[0]=='PUT' for x in http.seen)


def test_production_policy_transport_loss_keeps_uncertain_and_never_resends():
    import telegram_notify as tg
    with factory() as (root,data,api,http,*_):
        with patch.object(tg,'deliver_telegram',side_effect=TimeoutError('synthetic-lost-transport')) as send:
            runner.run_checked('test',data)
            before=api.put_count
            with patch.dict(os.environ,{'BTC_DELIVERY_OPERATION_ID':'synthetic-new-id'}):
                fails(github.StoreConflict,lambda:runner.run_checked('test',data))
            assert send.call_count==1 and api.put_count==before
        messages=next(iter(api.envelope()['snapshot']['commands'].values()))['_delivery']['messages']
        assert messages[0]['status']=='uncertain'


def test_runtime_wrong_config_budget_and_actual_workflow_stop_before_factory_requests():
    with factory() as (root,data,api,http,clock,cfg,*_):
        runtime=json.loads((ROOT/'ops/produktion/github-runtime.disabled.json').read_text())
        runtime.update(enabled=True,activation_review_sha256='b'*64,private_store_repository=REPO,
            store_branch=BRANCH,store_id=STORE_ID,code_sha='a'*40,bot_identity='synthetic-bot',
            code_repository='synthetic/code',confirmation_config=str(root/'policy.json'),
            request_journal=str(root/'requests.sqlite'),
            config_sha256=digest(api.envelope()['snapshot']['engine']['config']))
        path=root/'runtime.json'
        for field,value in (('enabled','true'),('config_sha256','f'*64),('activation_review_sha256',None),
                            ('confirmation_budgets',{}),('private_store_repository','foreign/repo')):
            bad={**runtime,field:value};path.write_text(canonical(bad))
            fails(ValueError,lambda:entry.run_runtime(path,'signal',data,fetch=lambda _:([],[],[])))
            assert http.seen==[]
        path.write_text(canonical(runtime))
        for key in ('GITHUB_RUN_ID','GITHUB_WORKFLOW_REF','GITHUB_SHA'):
            with patch.dict(os.environ,{key:'wrong'}):
                fails(ValueError,lambda:entry.run_runtime(path,'signal',data,fetch=lambda _:([],[],[])))
            assert http.seen==[]


def test_actual_child_exit_keeps_durable_reservation_and_blocks_factory_restart():
    with factory() as (root,data,api,http,clock,cfg,binding):
        (root/'synthetic-remote.json').write_bytes(canonical(api.envelope()).encode('utf-8'))
        args=[sys.executable,'-B',__file__,'--crash-factory',str(data),str(root/'synthetic-remote.json'),str(clock[0])]
        child=subprocess.run(args,capture_output=True)
        assert child.returncode==23,child.stderr
        rows=journal_rows(root);assert len(rows)==4 and rows[-1][0]=='PUT' and rows[-1][4]=='reserved'
        stored=json.loads((root/'synthetic-remote.json').read_text(encoding='utf-8'))
        assert stored['snapshot']['control']['owner'] is not None
        assert stored['revision']==api.envelope()['revision']+1
        fails(github.StoreError,lambda:durable.configured_store(data));assert http.seen==[]


def test_completed_put_but_unfinished_case_and_wrong_run_are_not_reopened():
    with factory() as (root,data,api,http,clock,cfg,binding):
        journal=policy.RequestJournal(root/'requests.sqlite',cfg,binding,clock=lambda:clock[0])
        journal.begin_case('synthetic-unfinished',100)
        req,_=journal.reserve('PUT','/synthetic',100,'synthetic-unfinished')
        journal.finish(req,20,'completed')
        fails(github.StoreError,lambda:durable.configured_store(data));assert http.seen==[]
        with patch.dict(os.environ,{'BTC_DELIVERY_RUN_ID':'another-run'}):
            fails(github.StoreError,lambda:durable.configured_store(data))


def test_disabled_workflow_runtime_and_strategy_proposals_stay_inactive():
    runtime=json.loads((ROOT/'ops/produktion/github-runtime.disabled.json').read_text())
    assert runtime['enabled'] is False and runtime['activation_review_sha256'] is None
    for path in (ROOT/'ops/produktion/github-workflow.disabled.yml',):
        text=path.read_text();assert 'if: ${{ false }}' in text and 'schedule:' not in text
        assert 'tools/produktion_candidate_runner.py' in text and 'BTC_DELIVERY_REQUEST_JOURNAL:' in text
    c05=json.loads((ROOT/'docs/um2-engine-integration/candidates/C05-UM2.inactive.json').read_text())
    assert c05['active'] is False and digest(c05['params'])=='a99be30ae26a753f9734fbe2d67ac49f33e090a691904336421742f92420f787'
    assert c05['params']['pivot_n']==6 and c05['params']['muster5_entry'] is True and c05['params']['muster_cvd']=='usd'


if __name__=='__main__' and '--crash-factory' in sys.argv:
    from test_github_delivery import FakeAPI
    remote=Path(sys.argv[3]);api=FakeAPI(remote.read_bytes())
    http=HTTPFixture(api)
    def crash_http(request,timeout):
        if request.get_method()=='PUT':
            body=base64.b64decode(json.loads(request.data)['content'])
            with remote.open('wb') as output:
                output.write(body);output.flush();os.fsync(output.fileno())
            os._exit(23)
        return http.open(request,timeout)
    with patch.object(policy.time,'time',return_value=int(sys.argv[4])/1000),\
         patch.object(policy.ProductionContentsClient,'open_request',side_effect=crash_http),\
         patch('socket.create_connection',side_effect=AssertionError('Network forbidden')):
        durable.configured_store(Path(sys.argv[2])).__enter__()
