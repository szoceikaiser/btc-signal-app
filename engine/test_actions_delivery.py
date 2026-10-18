"""Net-free multi-file GitHub fixture through hosted entry, factory and runner."""
from contextlib import contextmanager
from copy import deepcopy
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
from unittest.mock import patch

import actions_delivery as actions
import durable_delivery as durable
import github_delivery as github
from production_contract import canonical, digest
from test_github_delivery import fake_store, fails, REPO, BRANCH, STORE_ID
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import produktion_actions_runner as entry
import produktion_runner as runner

ROOT = Path(__file__).resolve().parents[1]


class BranchHTTP:
    def __init__(self, files=None, state=None, remote=None):
        self.state = state or {'seq':2,
            'heads':{BRANCH:'0'*39+'1', 'actions-fence':'0'*39+'2'},
            'parents':{'0'*39+'1':[], '0'*39+'2':[]},
            'history':{'0'*39+'1':{github.STORE_PATH:files[github.STORE_PATH]},
                       '0'*39+'2':{actions.FENCE_PATH:files[actions.FENCE_PATH]}}}
        self.remote = remote
        self.seen = []
        self.mode = None
        self.selected_path = github.STORE_PATH
        self.old = None
        self.refs = 0
        self.puts = 0
        self.crash = None

    def persist(self):
        if self.remote:
            with self.remote.open('wb') as out:
                out.write(canonical(self.state).encode()); out.flush(); os.fsync(out.fileno())

    def file(self, path):
        branch = BRANCH if path==github.STORE_PATH else 'actions-fence'
        return self.state['history'][self.state['heads'][branch]][path].encode()

    def open(self, request, timeout):
        from offline_test_fixtures import branch_reply
        response=branch_reply(self,request,timeout)
        if response is not None: return response
        method = request.get_method(); url = request.full_url
        self.seen.append((method,url,timeout))
        path = urllib.parse.urlsplit(url).path
        if method == 'PUT':
            file = path.split('/contents/')[1]; data = json.loads(request.data)
            self.puts += 1
            if self.crash == ('before',self.puts) or (self.crash == ('before-close',0)
                    and file==actions.FENCE_PATH and json.loads(base64.b64decode(data['content']))['phase']=='closed'):
                os._exit(23)
            branch=data['branch'];old = self.state['heads'][branch]; files = deepcopy(self.state['history'][old])
            blob = self.blob(files[file].encode())
            if data['sha'] != blob or (self.mode=='cas' and file==self.selected_path):
                raise urllib.error.HTTPError(url,409,'synthetic',{},None)
            if self.mode=='lost-before' and file==self.selected_path: raise TimeoutError('synthetic')
            self.state['seq'] += 1; head = f"{self.state['seq']:040x}"
            files[file] = base64.b64decode(data['content']).decode()
            self.state['heads'][branch]=head; self.state['history'][head]=files; self.state['parents'][head]=[old]
            self.persist()
            if self.crash == ('after',self.puts) or (self.crash == ('after-close',0)
                    and file==actions.FENCE_PATH and json.loads(files[file])['phase']=='closed'):
                os._exit(23)
            if file==self.selected_path:
                self.old=old; self.refs=0
                if self.mode=='lost-reply': raise TimeoutError('synthetic')
            result={'commit':{'sha':head}}
        elif '/git/ref/heads/' in path:
            self.refs += 1
            branch=urllib.parse.unquote(path.split('/git/ref/heads/')[1])
            head=self.state['heads'][branch]
            selected_branch = BRANCH if self.selected_path==github.STORE_PATH else 'actions-fence'
            if self.old and branch==selected_branch and (self.mode=='old' or self.mode=='delayed' and self.refs<=4): head=self.old
            result={'object':{'sha':head}}
        elif '/contents/' in path:
            file=path.split('/contents/')[1]
            head=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['ref'][0]
            body=self.state['history'][head][file].encode()
            result={'type':'file','encoding':'base64','sha':self.blob(body),
                    'content':base64.b64encode(body).decode()}
        elif '/git/commits/' in path:
            result={'parents':[{'sha':p} for p in self.state['parents'][path.rsplit('/',1)[1]]]}
        elif '/compare/' in path:
            base,head=path.rsplit('/',1)[1].split('...')
            result={'base_commit':{'sha':base},'merge_base_commit':{'sha':base},
                    'status':'ahead' if base!=head else 'identical'}
        else: raise AssertionError('Unexpected fixture route')
        raw=json.dumps(result).encode()
        if self.mode=='oversize': raw=b' '*2097153+raw
        return io.BytesIO(raw)

    @staticmethod
    def blob(body):
        return hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as td, fake_store() as api:
        root=Path(td); data=root/'runner/data'; data.mkdir(parents=True)
        runtime=json.loads((ROOT/'ops/produktion/github-actions-runtime.disabled.json').read_text(encoding='utf-8-sig'))
        runtime.update(python_version=list(sys.version_info[:3]),enabled=True,activation_review_sha256='b'*64,private_store_repository=REPO,
                       store_branch=BRANCH,fence_branch='actions-fence',store_id=STORE_ID,code_sha='a'*40,
                       code_repository='synthetic/code',code_ref='refs/heads/synthetic',
                       bot_identity='synthetic-bot',config_sha256=digest(api.envelope()['snapshot']['engine']['config']))
        from offline_test_fixtures import sender_access
        access,rules,rulesets=sender_access(runtime)
        runtime.update(public_access=access,public_access_sha256=digest(access))
        path=root/'runtime.json';path.write_text(canonical(runtime),encoding='utf-8')
        (data/'config.json').write_text(canonical(api.envelope()['snapshot']['engine']['config']),encoding='utf-8')
        http=BranchHTTP({github.STORE_PATH:api.record['body'].decode(),
                        actions.FENCE_PATH:actions.seed_fence(entry.deployment(runtime)).decode()})
        http.access,http.rules,http.rulesets=access,rules,rulesets
        env={'GITHUB_TOKEN':'synthetic-codejob','PATH':os.environ.get('PATH',''),'BTC_OFFLINE_TEST':'1','PYTHONPATH':str(ROOT/'engine/offline_guard'),'SYSTEMROOT':os.environ.get('SYSTEMROOT',r'C:\Windows'),
             'WINDIR':os.environ.get('WINDIR',r'C:\Windows'),
             'TMP':tempfile.gettempdir(), 'TEMP':tempfile.gettempdir(),
             'PYTHONUTF8':'1',
             'BTC_DELIVERY_ADAPTER':'github','BTC_DELIVERY_STORE_ID':STORE_ID,
             'BTC_DELIVERY_RUNNER_ROOT':str(data.parent),'BTC_DELIVERY_GITHUB_REPO':REPO,
             'BTC_DELIVERY_GITHUB_BRANCH':BRANCH,'BTC_DELIVERY_GITHUB_TOKEN':'synthetic-only',
             'BTC_DELIVERY_FENCE_BRANCH':'actions-fence',
             'BTC_DELIVERY_RUN_ID':'100','BTC_DELIVERY_RUN_ATTEMPT':'1','BTC_DELIVERY_CODE_SHA':'a'*40,
             'BTC_DELIVERY_BOT_IDENTITY':'synthetic-bot','BTC_DELIVERY_CONFIRMATION_POLICY':actions.POLICY,
             'TELEGRAM_BOT_TOKEN':'synthetic-only','TELEGRAM_CHAT_ID':'synthetic-target',
             'BTC_DELIVERY_RUN_REPOSITORY':'synthetic/code',
             'BTC_DELIVERY_WORKFLOW':'.github/workflows/signal.yml',
             'BTC_DELIVERY_EXPECTED_START_MS':'1791100800000','GITHUB_REPOSITORY':'synthetic/code',
             'GITHUB_RUN_ID':'100','GITHUB_RUN_ATTEMPT':'1','GITHUB_RUN_NUMBER':'10','GITHUB_SHA':'a'*40,
             'GITHUB_REF':'refs/heads/synthetic',
             'GITHUB_WORKFLOW_REF':'synthetic/code/.github/workflows/signal.yml@refs/heads/synthetic',
             'GITHUB_EVENT_NAME':'workflow_dispatch'}
        with patch.dict(os.environ,env,clear=True), patch.object(entry,'check_code_pin'),\
             patch.object(actions.ActionsClient,'open_request',side_effect=http.open),\
             patch('urllib.request.urlopen',side_effect=AssertionError('Real HTTP forbidden')),\
             patch.object(entry.time,'time',return_value=1791100921):
            yield root,data,path,runtime,http


def invoke(path,data):
    return entry.run_runtime(path,'signal',data,fetch=lambda _:([],[],[]))


def test_success_actual_signal_entry_shared_factory_budgets_and_closed_completion():
    with fixture() as (_,data,path,runtime,http):
        result=invoke(path,data)
        fence=json.loads(http.file(actions.FENCE_PATH))
        assert fence['phase']=='closed' and fence['run']['number']==10
        assert fence['completion']['stream']['adapter']=='github'
        assert result['put']==sum(x[0]=='PUT' for x in http.seen)
        assert result['get']==sum(x[0]=='GET' for x in http.seen)
        assert result['response_reserve']==len(http.seen)*2097152
        assert json.loads(http.file(github.STORE_PATH))['snapshot']['control']['owner'] is None
        # Existing backup format: each store commit has exactly one stream;
        # fence writes cannot create duplicate stream revisions in its branch.
        streams=[]
        for sha,files in http.state['history'].items():
            if github.STORE_PATH in files:
                assert set(files)=={github.STORE_PATH}
                streams.append((sha,json.loads(files[github.STORE_PATH])))
        for (old,prior),(sha,value) in zip(streams,streams[1:]):
            assert http.state['parents'][sha]==[old]
            assert value['revision']==prior['revision']+1
            assert value['parent_digest']==prior['body_digest']
        puts=http.puts
        fails(github.StoreConflict,lambda:invoke(path,data))
        assert http.puts==puts
        with patch.dict(os.environ,{'GITHUB_RUN_ID':'101','BTC_DELIVERY_RUN_ID':'101','GITHUB_RUN_NUMBER':'11'}):
            invoke(path,data)


def test_three_cycles_and_lost_reply_one_put_per_business_write():
    for mode in ('delayed','lost-reply'):
        with fixture() as (_,data,path,runtime,http):
            http.mode=mode
            invoke(path,data)
            messages=[json.loads(http.state['history'][sha][github.STORE_PATH])['write_id']
                      for sha in http.state['history'] if github.STORE_PATH in http.state['history'][sha]]
            assert len(set(messages))==http.puts-2+1
            assert json.loads(http.file(actions.FENCE_PATH))['phase']=='closed'


def test_lost_admission_reply_and_unconfirmed_old_or_cas_never_business_mutate():
    for mode in ('lost-reply','old','cas','lost-before'):
        with fixture() as (_,data,path,runtime,http):
            http.mode=mode;http.selected_path=actions.FENCE_PATH
            original=http.file(github.STORE_PATH)
            if mode=='lost-reply': invoke(path,data)
            else:
                fails(github.StoreError,lambda:invoke(path,data))
                assert http.file(github.STORE_PATH)==original and http.puts==1


def test_business_unconfirmed_no_resend_and_new_run_keeps_open_fence():
    for mode in ('old','lost-before','cas'):
        with fixture() as (_,data,path,runtime,http):
            http.mode=mode
            fails(github.StoreError,lambda:invoke(path,data))
            assert json.loads(http.file(actions.FENCE_PATH))['phase']=='open'
            count=http.puts
            with patch.dict(os.environ,{'GITHUB_RUN_ID':'101','BTC_DELIVERY_RUN_ID':'101','GITHUB_RUN_NUMBER':'11'}):
                fails(github.StoreConflict,lambda:invoke(path,data))
            assert http.puts==count


def test_factory_outside_admitted_scope_and_wrong_binding_disabled_refused_before_http():
    with fixture() as (_,data,path,runtime,http):
        fails(ValueError,lambda:durable.configured_store(data))
        for key,value in (('GITHUB_RUN_ATTEMPT','2'),('GITHUB_RUN_ID','101'),
                          ('GITHUB_SHA','f'*40),('GITHUB_WORKFLOW_REF','wrong'),
                          ('GITHUB_REF','refs/heads/foreign'),('BTC_DELIVERY_GITHUB_BRANCH','foreign'),
                          ('GITHUB_RUN_NUMBER','0'),('BTC_DELIVERY_REQUEST_JOURNAL','local')):
            with patch.dict(os.environ,{key:value}): fails(ValueError,lambda:invoke(path,data))
            assert http.seen==[]
        for key,value in (('enabled',False),('config_sha256','f'*64),('activation_review_sha256',None)):
            path.write_text(canonical({**runtime,key:value}),encoding='utf-8')
            fails(ValueError,lambda:invoke(path,data));assert http.seen==[]


def test_budget_bytes_deadline_full_reserve_and_no_downgrade():
    for changed in ({'run_get_limit':11},{'request_byte_limit':1},
                    {'run_put_limit':1},{'run_response_byte_limit':12*2097152}):
        with fixture() as (_,data,path,runtime,http):
            runtime['confirmation_budgets'].update(changed)
            path.write_text(canonical(runtime),encoding='utf-8')
            # Rebind the synthetic seed; no real preparation.
            http.state['history'][http.state['heads']['actions-fence']][actions.FENCE_PATH]=actions.seed_fence(entry.deployment(runtime)).decode()
            fails(github.StoreError,lambda:invoke(path,data))
            assert http.puts<=1
    with fixture() as (_,data,path,runtime,http):
        http.mode='oversize'
        try:invoke(path,data)
        except ValueError as exc:assert str(exc)=='Public response byte bound'
        else:raise AssertionError('Oversize response accepted')
        assert http.puts==0
    clock=[1000]
    from production_confirmation import validate_policy
    p=json.loads((ROOT/'ops/produktion/github-actions-runtime.disabled.json').read_text())['confirmation_budgets']
    budget=actions.RunBudget({**p,'deadline_utc_ms':2000},{},clock=lambda:clock[0])
    clock[0]=2000;fails(github.StoreError,budget.guard)
    p={**p,'confirmation_cycles':1,'deadline_utc_ms':2000}
    fails(ValueError,lambda:validate_policy(p))


def test_two_contenders_same_old_blob_exactly_one_admission():
    with fixture() as (_,data,path,runtime,http):
        fields=entry.validate(runtime,'signal',data)
        binding={'repo':REPO,'branch':BRANCH,'store_id':STORE_ID}
        def client():
            p={**runtime['confirmation_budgets'],'deadline_utc_ms':int(actions.time.time()*1000)+900000}
            return actions.ActionsClient('synthetic-only',actions.RunBudget(p,binding),fields)
        first,second=client(),client(); pin=entry.deployment(runtime)
        old,value=second.fence_read(pin)
        first.acquire(pin,{'number':10,'id':'100','attempt':'1','kind':'signal','workflow':'.github/workflows/signal.yml'})
        stale={**first.fence,'phase':'open','run':{'number':11,'id':'101','attempt':'1'},'write_id':'contender'}
        fails(github.StoreConflict,lambda:second.fence_write(old,stale))
        assert json.loads(http.file(actions.FENCE_PATH))['run']['id']=='100'
        assert http.puts==2  # successful claim + denied stale CAS, no retry


def test_transport_uncertain_persists_and_blocks_replacement_without_send():
    import telegram_notify as tg
    actual=runner.run_checked
    with fixture() as (_,data,path,runtime,http):
        # Exercise the actual command runner/transport path inside the admitted
        # Actions scope; ordinary signal invocation is separately exercised above.
        def command(*args,**kwargs):
            with patch.dict(os.environ,{'BTC_DELIVERY_OPERATION_ID':'synthetic-request'}):
                return actual('test',data)
        with patch.object(runner,'run_checked',side_effect=command),\
             patch.object(tg,'deliver_telegram',side_effect=TimeoutError('synthetic')) as send:
            fails(github.StoreConflict,lambda:invoke(path,data))
            count=http.puts
            with patch.dict(os.environ,{'GITHUB_RUN_ID':'101','BTC_DELIVERY_RUN_ID':'101','GITHUB_RUN_NUMBER':'11'}):
                fails(github.StoreConflict,lambda:invoke(path,data))
            assert send.call_count==1 and http.puts==count
        states=json.loads(http.file(github.STORE_PATH))['snapshot']['commands'].values()
        assert any(m['status']=='uncertain' for s in states for m in s['_delivery']['messages'])


def test_real_child_loss_before_after_fence_and_stream_mutation_new_ephemeral_runner():
    for when,number in (('before',1),('after',1),('before',2),('after',2),('after',3),
                        ('before-close',0),('after-close',0)):
        with fixture() as (root,data,path,runtime,http):
            remote=root/'synthetic-remote.json';http.remote=remote;http.persist()
            child=subprocess.run([sys.executable,'-B',__file__,'--crash',str(path),str(data),
                                  str(remote),when,str(number)],capture_output=True)
            assert child.returncode==23,child.stderr.decode(errors='replace')
            http.state=json.loads(remote.read_text(encoding='utf-8'))
            http.puts=0;http.seen=[]
            fresh=root/'new-ephemeral-runner/data';fresh.mkdir(parents=True)
            (fresh/'config.json').write_bytes((data/'config.json').read_bytes())
            with patch.dict(os.environ,{'BTC_DELIVERY_RUNNER_ROOT':str(fresh.parent),
                'GITHUB_RUN_ATTEMPT':'2','BTC_DELIVERY_RUN_ATTEMPT':'2'}):
                fails(ValueError,lambda:invoke(path,fresh));assert http.seen==[]
            if (when,number) not in (('before',1),('after-close',0)):
                with patch.dict(os.environ,{'BTC_DELIVERY_RUNNER_ROOT':str(fresh.parent),
                    'GITHUB_RUN_ID':'101','BTC_DELIVERY_RUN_ID':'101','GITHUB_RUN_NUMBER':'11'}):
                    fails(github.StoreConflict,lambda:invoke(path,fresh))
                assert http.puts==0
            else:
                assert json.loads(http.file(actions.FENCE_PATH))['phase']=='closed'
                assert json.loads(http.file(github.STORE_PATH))['snapshot']['control']['owner'] is None
                with patch.dict(os.environ,{'BTC_DELIVERY_RUNNER_ROOT':str(fresh.parent),
                    'GITHUB_RUN_ID':'101','BTC_DELIVERY_RUN_ID':'101','GITHUB_RUN_NUMBER':'11'}):
                    invoke(path,fresh)


def test_real_child_transport_loss_before_after_delivery_no_replacement_resend():
    for mode in ('transport-before','transport-after'):
        with fixture() as (root,data,path,runtime,http):
            remote=root/'synthetic-remote.json';http.remote=remote;http.persist()
            child=subprocess.run([sys.executable,'-B',__file__,'--crash',str(path),str(data),
                                  str(remote),mode,'0'],capture_output=True)
            assert child.returncode==23,child.stderr.decode(errors='replace')
            http.state=json.loads(remote.read_text(encoding='utf-8'));http.puts=0
            delivered=(root/'synthetic-delivered.txt').exists()
            assert delivered == (mode=='transport-after')
            snapshot=json.loads(http.file(github.STORE_PATH))['snapshot']
            assert snapshot['control']['owner'] is not None
            assert any(m['status']=='sending' for state in snapshot['commands'].values()
                       for m in state['_delivery']['messages'])
            with patch.dict(os.environ,{'GITHUB_RUN_ID':'101','BTC_DELIVERY_RUN_ID':'101','GITHUB_RUN_NUMBER':'11'}):
                fails(github.StoreConflict,lambda:invoke(path,data))
            assert http.puts==0


def test_completion_lost_reply_exact_confirmed_or_failed_closed_without_success():
    for mode in ('lost-reply','old'):
        with fixture() as (_,data,path,runtime,http):
            original=http.open
            def close_fault(request,timeout):
                if request.get_method()=='PUT' and '/contents/'+actions.FENCE_PATH in request.full_url:
                    value=json.loads(base64.b64decode(json.loads(request.data)['content']))
                    if value['phase']=='closed':
                        http.mode=mode;http.selected_path=actions.FENCE_PATH
                return original(request,timeout)
            with patch.object(actions.ActionsClient,'open_request',side_effect=close_fault):
                if mode=='lost-reply': invoke(path,data)
                else: fails(github.StoreError,lambda:invoke(path,data))
            assert json.loads(http.file(actions.FENCE_PATH))['phase']=='closed'
            count=http.puts
            fails(github.StoreConflict,lambda:invoke(path,data));assert http.puts==count


def test_workflow_and_runtime_are_disabled_hosted_and_no_site_data_input():
    text=(ROOT/'ops/produktion/github-actions-workflow.disabled.yml').read_text(encoding='utf-8-sig')
    assert 'runs-on: ubuntu-24.04' in text and 'self-hosted' not in text
    assert 'if: ${{ false }}' in text and 'schedule:' not in text and 'site/data' not in text
    assert 'tools/produktion_actions_runner.py' in text
    runtime=json.loads((ROOT/'ops/produktion/github-actions-runtime.disabled.json').read_text())
    assert runtime['enabled'] is False and runtime['code_sha'] is None
    assert runtime['confirmation_budgets']['confirmation_cycles']==3
    child=subprocess.run([sys.executable,'-B',str(ROOT/'tools/produktion_actions_runner.py'),
        '--runtime',str(ROOT/'ops/produktion/github-actions-runtime.disabled.json'),
        '--kind','signal','--data-dir',str(ROOT/'.runtime/data')],capture_output=True,
        env={'SYSTEMROOT':os.environ.get('SYSTEMROOT',r'C:\Windows'),
             'WINDIR':os.environ.get('WINDIR',r'C:\Windows')})
    assert child.returncode==20 and b'operator review' in child.stderr


def test_real_clean_checkout_pin_and_offline_prepare_exclusive_seed():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    entry.check_code_pin(head)
    fails(ValueError,lambda:entry.check_code_pin('f'*40))
    with fixture() as (root,data,path,runtime,http):
        out=root/'offline-fence.json'
        baseline=root/'cursors.json'
        baseline.write_text(canonical({'schema':'actions-v2-start-cursors-v1','review_sha256':runtime['activation_review_sha256'],
                                      'cursors':{w:{'number':0,'id':None} for w in actions.WORKFLOWS}}),encoding='utf-8')
        args=[sys.executable,'-B',str(ROOT/'tools/produktion_actions_prepare.py'),
              '--runtime',str(path),'--out',str(out),'--cursors',str(baseline)]
        child=subprocess.run(args,capture_output=True)
        assert child.returncode==0,child.stderr
        assert out.read_bytes()==actions.seed_fence(entry.deployment(runtime))
        child=subprocess.run(args,capture_output=True)
        assert child.returncode!=0  # exclusive creation, never overwrite
        assert http.seen==[]


if __name__=='__main__' and '--crash' in sys.argv:
    entry.time.time=lambda:1791100921
    remote=Path(sys.argv[4]);http=BranchHTTP(state=json.loads(remote.read_text(encoding='utf-8')),remote=remote)
    http.crash=(sys.argv[5],int(sys.argv[6]))
    if sys.argv[5].startswith('lage-'):
        import telegram_notify as tg
        from test_pflichtfunktionen import lage, receipt
        if sys.argv[5] in ('lage-before-close','lage-after-close'):
            http.crash=(sys.argv[5].removeprefix('lage-'),0)
        def transport(*args):
            if sys.argv[5]=='lage-after':
                with (remote.parent/'synthetic-delivered.txt').open('wb') as out:
                    out.write(b'synthetic Lage delivery only');out.flush();os.fsync(out.fileno())
            if sys.argv[5] in ('lage-before','lage-after'):
                os._exit(23)
            return receipt(*args)
        with patch.object(tg,'deliver_telegram',side_effect=transport),\
             patch.object(entry,'check_code_pin'),patch.object(actions.ActionsClient,'open_request',side_effect=http.open),\
             patch('socket.create_connection',side_effect=AssertionError('Network forbidden')):
            lage(Path(sys.argv[2]),Path(sys.argv[3]))
        sys.exit(24)
    if sys.argv[5].startswith('transport-'):
        import telegram_notify as tg
        actual=runner.run_checked
        def command(*args,**kwargs):
            with patch.dict(os.environ,{'BTC_DELIVERY_OPERATION_ID':'synthetic-request'}):
                return actual('test',Path(sys.argv[3]))
        def transport(*args):
            if sys.argv[5]=='transport-after':
                with (remote.parent/'synthetic-delivered.txt').open('wb') as out:
                    out.write(b'synthetic delivery only');out.flush();os.fsync(out.fileno())
            os._exit(23)
        with patch.object(runner,'run_checked',side_effect=command),patch.object(tg,'deliver_telegram',side_effect=transport),\
             patch.object(entry,'check_code_pin'),patch.object(actions.ActionsClient,'open_request',side_effect=http.open),\
             patch('socket.create_connection',side_effect=AssertionError('Network forbidden')):
            invoke(Path(sys.argv[2]),Path(sys.argv[3]))
        sys.exit(24)
    with patch.object(entry,'check_code_pin'),patch.object(actions.ActionsClient,'open_request',side_effect=http.open),\
         patch('socket.create_connection',side_effect=AssertionError('Network forbidden')):
        invoke(Path(sys.argv[2]),Path(sys.argv[3]))
