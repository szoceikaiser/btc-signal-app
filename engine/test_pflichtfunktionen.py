"""Focused offline acceptance of own Lage entry and read-only Pages export."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import actions_delivery as actions
import github_delivery as github
import telegram_notify as tg
from production_contract import canonical, digest
from strategy_core import Candle
from test_actions_delivery import fixture, invoke, entry, ROOT
from test_github_delivery import fails
import produktion_pages_export as pages
import produktion_runtime_prepare as prepare
NODE = os.environ.get('BTC_TEST_NODE')


def binding(kind, number, run_id):
    workflow = next(w for w,k in actions.WORKFLOWS.items() if k == kind)
    return patch.dict(os.environ, {
        'BTC_DELIVERY_WORKFLOW':workflow,
        'GITHUB_WORKFLOW_REF':'synthetic/code/'+workflow+'@refs/heads/synthetic',
        'GITHUB_RUN_NUMBER':str(number), 'GITHUB_RUN_ID':str(run_id),
        'BTC_DELIVERY_RUN_ID':str(run_id)})


def lage(path, data):
    candles = [Candle(1791100800000+i*14400000,100+i,103+i,99+i,102+i) for i in range(30)]
    return entry.run_runtime(path,'lage',data,fetch=lambda _: (candles,[],[]),sth=lambda:None)


def receipt(*args):
    return {'status':'confirmed', 'message_id':73, 'target_binding':hashlib.sha256(b'synthetic-target').hexdigest()}


def test_lage_actual_entry_exact_command_unchanged_state_and_no_replay():
    with fixture() as (_,data,path,runtime,http), binding('lage',1,200), patch.object(tg,'deliver_telegram',side_effect=receipt) as send:
        before = json.loads(http.file(github.STORE_PATH))['snapshot']
        assert lage(path,data)['result']['kurs'] == 131
        after = json.loads(http.file(github.STORE_PATH))['snapshot']
        assert after['engine'] == before['engine'] and after['watch'] == before['watch']
        assert after['control']['health'].get('successful_runs') == before['control']['health'].get('successful_runs')
        command = next(iter(after['commands'].values()))
        assert command['actions_completion']['run']['id'] == '200'
        assert command['_delivery']['messages'][0]['status'] == 'confirmed'
        puts = http.puts
        fails(github.StoreConflict,lambda:lage(path,data))
        with patch.dict(os.environ,{'GITHUB_RUN_ATTEMPT':'2','BTC_DELIVERY_RUN_ATTEMPT':'2'}):
            fails(ValueError,lambda:lage(path,data))
        assert send.call_count == 1 and puts == http.puts


def test_mixed_workflows_separate_numbers_old_job_after_other_workflow_and_ids_not_ordered():
    with fixture() as (_,data,path,runtime,http):
        with binding('signal',900,100): invoke(path,data)
        raw = [[1791100800000+i*14400000,100,101,99,100,0,1791100800000+(i+1)*14400000-1] for i in range(31)]
        with binding('watch',2,80):
            entry.run_runtime(path,'watch',data,watch_raw=raw,now_ms=raw[-1][0]+1000)
        with binding('lage',1,60), patch.object(tg,'deliver_telegram',side_effect=receipt): lage(path,data)
        with binding('signal',899,101): fails(github.StoreConflict,lambda:invoke(path,data))
        with binding('signal',901,40): invoke(path,data)
        fence=json.loads(http.file(actions.FENCE_PATH))
        assert [fence['cursors'][w]['number'] for w in actions.WORKFLOWS] == [901,2,1]


def test_wrong_kind_unknown_workflow_manual_required_and_old_v1_seed_refused():
    with fixture() as (_,data,path,runtime,http):
        for env in ({'BTC_DELIVERY_WORKFLOW':'.github/workflows/unknown.yml'},
                    {'BTC_DELIVERY_WORKFLOW':'.github/workflows/watch.yml'}):
            with patch.dict(os.environ,env): fails(ValueError,lambda:lage(path,data))
        with binding('lage',1,200), patch.dict(os.environ,{'GITHUB_EVENT_NAME':'schedule'}):
            fails(ValueError,lambda:lage(path,data))
        assert http.seen == []
        head=http.state['heads']['actions-fence']
        old=json.loads(http.file(actions.FENCE_PATH));old['schema']='github-actions-fence-v1'
        http.state['history'][head][actions.FENCE_PATH]=canonical(old)
        fails(github.StoreConflict,lambda:invoke(path,data));assert http.puts==0


def test_lage_uncertain_or_rejected_no_close_and_no_resend_after_other_workflow():
    for status in ('uncertain','rejected'):
        with fixture() as (_,data,path,runtime,http), binding('lage',1,200), patch.object(tg,'deliver_telegram',return_value={'status':status,'message_id':None}) as send:
            fails(RuntimeError,lambda:lage(path,data))
            assert json.loads(http.file(actions.FENCE_PATH))['phase']=='open'
            before=http.puts
            with binding('signal',1000,201): fails(github.StoreConflict,lambda:invoke(path,data))
            with binding('lage',2,202): fails(github.StoreConflict,lambda:lage(path,data))
            assert send.call_count==1 and http.puts==before


def test_lage_lost_store_response_exact_readback_and_stale_health_cannot_close():
    with fixture() as (_,data,path,runtime,http), binding('lage',1,200), patch.object(tg,'deliver_telegram',side_effect=receipt) as send:
        http.mode='lost-reply'
        lage(path,data)
        assert send.call_count==1 and json.loads(http.file(actions.FENCE_PATH))['phase']=='closed'
    with fixture() as (_,data,path,runtime,http):
        invoke(path,data)  # a valid but old signal attestation
        with binding('lage',1,200), patch.object(entry.runner,'run_checked',return_value={'synthetic':True}):
            fails(github.StoreConflict,lambda:lage(path,data))
        assert json.loads(http.file(actions.FENCE_PATH))['phase']=='open'


def test_lage_real_process_loss_before_after_send_and_close_no_replacement_resend():
    import test_actions_delivery as shared
    for mode in ('lage-before','lage-after','lage-before-close','lage-after-close'):
        with fixture() as (root,data,path,runtime,http), binding('lage',1,200):
            remote=root/'remote.json';http.remote=remote;http.persist()
            child=subprocess.run([sys.executable,'-B',shared.__file__,'--crash',str(path),str(data),
                                  str(remote),mode,'0'],capture_output=True)
            assert child.returncode==23,child.stderr.decode(errors='replace')
            http.state=json.loads(remote.read_text());http.puts=0
            snapshot=json.loads(http.file(github.STORE_PATH))['snapshot']
            if mode in ('lage-before','lage-after'):
                assert next(iter(snapshot['commands'].values()))['_delivery']['messages'][0]['status']=='sending'
                assert (root/'synthetic-delivered.txt').exists() == (mode=='lage-after')
            fresh=root/'fresh/data';fresh.mkdir(parents=True)
            (fresh/'config.json').write_bytes((data/'config.json').read_bytes())
            with patch.dict(os.environ,{'BTC_DELIVERY_RUNNER_ROOT':str(fresh.parent)}),patch.object(tg,'deliver_telegram',side_effect=AssertionError('No resend')):
                fails(github.StoreConflict,lambda:lage(path,fresh))
                if mode!='lage-after-close':
                    with binding('signal',1000,300): fails(github.StoreConflict,lambda:invoke(path,fresh))
            assert http.puts==0


def pages_runtime(root, runtime):
    p=root/'pages-runtime.json'
    p.write_text(canonical({'schema':pages.SCHEMA, 'enabled':True, 'workflow':pages.WORKFLOW,
                           'deployment_schema':actions.POLICY, 'deployment':entry.deployment(runtime)}),encoding='utf-8')
    return p


def pages_environment():
    return patch.dict(os.environ,{'GITHUB_WORKFLOW_REF':'synthetic/code/'+pages.WORKFLOW+'@refs/heads/synthetic',
                                 'BTC_PAGES_STORE_READ_TOKEN':'synthetic-read-only'})


def test_pages_actual_read_client_entry_whitelist_package_and_stable_revalidation():
    with fixture() as (root,data,path,runtime,http):
        def enrich(v):
            engine=v['snapshot']['engine']
            engine['plan']={'einstand':100,'stop':{'preis':90,'grund':'synthetic stop','secret':'PRIVATE-NESTED'},
                            'nachkauf':[{'preis':95,'tranche':10,'was':'synthetic'}], 'outbox':'PRIVATE-OUTBOX'}
            engine['zonen_vorschau']={'richtung':'LONG','impuls_start':90,'impuls_ende':110,'level_05':100}
            engine['secret']='PRIVATE-TOP'
        mutate(http,github.STORE_PATH,enrich)
        invoke(path,data)
        p=pages_runtime(root,runtime); out=root/'public'
        timestamp=json.loads(http.file(github.STORE_PATH))['snapshot']['engine']['last_signal_ts']
        before=http.puts
        with pages_environment(),patch.object(pages,'check_code_pin'),patch.object(pages.ReadClient,'open_request',side_effect=http.open),patch.object(pages.time,'time',return_value=(timestamp+14400000+1000)/1000),patch.object(tg,'deliver_telegram',side_effect=AssertionError('Export cannot send')):
            result=pages.export(p,data/'config.json',out)
            assert result['get']==12 and result['put']==0 and result['transport']==0
            manifest=json.loads((out/'projection-manifest.json').read_text())
            payload=(out/manifest['projection']).read_bytes()
            assert hashlib.sha256(payload).hexdigest()==manifest['sha256']
            value=json.loads(payload)
            assert set(value['pins'])=={'code_sha','config_sha256','projection_binding'}
            assert not (out/'data').exists()
            assert all(x not in payload for x in (b'_delivery',b'commands',b'control',b'outbox',b'receipt',b'target_binding',b'synthetic-only',b'PRIVATE-'))
            assert pages.export(p,data/'config.json',out,verify=out.with_suffix('.receipt.json'))['get']==12
            assert http.puts==before
            node=NODE
            if node:
                proc=subprocess.run([node,str(ROOT/'tools/test_pages_projection.cjs'),str(out)],capture_output=True)
                assert proc.returncode==0,proc.stdout.decode()+proc.stderr.decode()
            (out/'unreviewed.txt').write_text('private')
            fails(github.StoreConflict,lambda:pages.export(p,data/'config.json',out,verify=out.with_suffix('.receipt.json')))


def mutate(http, path, change):
    branch= 'actions-fence' if path==actions.FENCE_PATH else 'delivery-only'
    value=json.loads(http.file(path));change(value)
    if path==github.STORE_PATH: value['body_digest']=digest(value['snapshot'])
    http.state['history'][http.state['heads'][branch]][path]=canonical(value)


def test_pages_refuses_open_foreign_unconfirmed_and_moved_pairs_without_put_or_package():
    cases = ('open','foreign-deployment','wrong-completion','foreign-code','owner','rejected','moved')
    for case in cases:
        with fixture() as (root,data,path,runtime,http):
            invoke(path,data); p=pages_runtime(root,runtime); before=http.puts
            if case=='open': mutate(http,actions.FENCE_PATH,lambda v:v.update(phase='open'))
            if case=='foreign-deployment': mutate(http,actions.FENCE_PATH,lambda v:v['deployment'].update(config_sha256='f'*64))
            if case=='wrong-completion': mutate(http,actions.FENCE_PATH,lambda v:v['completion']['stream'].update(revision=0))
            if case=='foreign-code': mutate(http,github.STORE_PATH,lambda v:v['snapshot']['control'].update(code_sha='f'*40))
            if case=='owner': mutate(http,github.STORE_PATH,lambda v:v['snapshot']['control'].update(owner={'repository':'synthetic','run_id':'1','run_attempt':'1','nonce':'x'}))
            original=http.open
            def moving(request,timeout):
                result=original(request,timeout)
                if case=='moved' and '/contents/'+github.STORE_PATH in request.full_url:
                    http.state['heads']['actions-fence']='f'*40
                    http.state['history']['f'*40]=deepcopy(http.state['history']['0'*39+'2'])
                return result
            if case=='rejected':
                # An unconfirmed command blocks public output even when no owner is left.
                from telegram_outbox import enqueue
                def reject(v):
                    state={'version':1,'signals':{'signals':[]},'oi_history':[],'messages':[]}
                    enqueue(state,'lage','synthetic',0,{'text':'private'},'private')
                    state['messages'][0].update(status='rejected',attempts=1,target='x')
                    v['snapshot']['commands']['synthetic']={'_delivery':state,'result':None}
                mutate(http,github.STORE_PATH,reject)
            with pages_environment(),patch.object(pages,'check_code_pin'),patch.object(pages.ReadClient,'open_request',side_effect=moving):
                fails((ValueError,github.StoreError),lambda:pages.export(p,data/'config.json',root/'public'))
            assert http.puts==before and not (root/'public').exists()


def test_export_fixed_get_byte_deadline_and_method_bounds():
    clock=[0]
    client=pages.ReadClient('synthetic','synthetic/store',{'stream':github.STORE_PATH},clock=lambda:clock[0])
    fails(github.StoreError,lambda:client.update())
    fails(github.StoreError,lambda:client._request('PUT','anything'))
    fails(github.StoreError,lambda:client.read('foreign/store','stream'))
    client.allowed={'/synthetic'};client.gets=12
    fails(github.StoreError,lambda:client._request('GET','/synthetic'))
    client.gets=0;clock[0]=120
    fails(github.StoreError,lambda:client._request('GET','/synthetic'))


def test_fixed_disabled_templates_prepare_factory_and_legacy_workflows_preserved():
    with fixture() as (root,data,path,runtime,http):
        for kind, name in (('signal','Signal-Engine'),('watch','Flush-Wache'),('lage','Lage abrufen')):
            text=(ROOT/'ops/produktion'/f'{kind}-workflow.disabled.yml').read_text()
            workflow=next(w for w,k in actions.WORKFLOWS.items() if k==kind)
            assert f'name: {name}\n' in text and 'if: ${{ false }}' in text
            assert f'BTC_DELIVERY_WORKFLOW: {workflow}\n' in text
            assert f'--kind {kind} --data-dir .runtime/data' in text
            assert 'group: btc-delivery-single-stream' in text and 'options:' not in text
            assert ('schedule:' in text) == (kind!='lage')
            with patch.dict(os.environ,{'REVIEWED_RUNTIME_JSON':canonical(runtime),
                                       'REVIEWED_CONFIG_JSON':(data/'config.json').read_text()}):
                prepare.prepare(kind, data.parent/f'prepared-{kind}')
                fails(FileExistsError,lambda:prepare.prepare(kind,data.parent/f'prepared-{kind}'))
        with patch.dict(os.environ,{'REVIEWED_RUNTIME_JSON':canonical({**runtime,'enabled':False}),
                                   'REVIEWED_CONFIG_JSON':(data/'config.json').read_text()}):
            fails(ValueError,lambda:prepare.prepare('lage',root/'refused'))
        assert http.seen==[]
    ptext=(ROOT/'ops/produktion/pages-workflow.disabled.yml').read_text()
    assert 'if: ${{ false }}' in ptext and 'group: btc-delivery-single-stream' in ptext
    assert 'path: .runtime/public' in ptext and 'path: site' not in ptext
    assert ptext.count('--verify .runtime/public.receipt.json')==2
    assert 'TELEGRAM_' not in ptext and 'BTC_REVIEWED_STORE_TOKEN' not in ptext
    assert all(x in ptext for x in ('Signal-Engine','Flush-Wache','Lage abrufen','Backtest'))
    assert json.loads((ROOT/'ops/produktion/pages-runtime.disabled.json').read_text())['enabled'] is False
    assert subprocess.run(['git','diff','--quiet','e245ba08028fb19d2af39a7f418454f2054e3250','--','.github/workflows','site/data'],cwd=ROOT).returncode==0


def test_public_pin_failures_before_reads_and_disabled_cli_refusal():
    with fixture() as (root,data,path,runtime,http):
        p=pages_runtime(root,runtime)
        with patch.object(pages,'check_code_pin'),patch.object(pages.ReadClient,'open_request',side_effect=http.open):
            fails(ValueError,lambda:pages.export(p,data/'config.json',root/'public'))  # actual wrong Actions entry
        with pages_environment(),patch.object(pages,'check_code_pin'),patch.object(pages.ReadClient,'open_request',side_effect=http.open):
            bad=json.loads((data/'config.json').read_text());bad['muster_cvd']='alt'
            (root/'wrong-config.json').write_text(canonical(bad))
            fails(ValueError,lambda:pages.export(p,root/'wrong-config.json',root/'public'))
        assert http.seen==[]
    child=subprocess.run([sys.executable,'-B',str(ROOT/'tools/produktion_pages_export.py'),
        '--runtime',str(ROOT/'ops/produktion/pages-runtime.disabled.json'),
        '--config','missing','--out','missing'],capture_output=True)
    assert child.returncode==20 and b'no new publication' in child.stderr


def test_public_export_actual_oversize_and_stale_slice_refused():
    for mode in ('oversize','stale'):
        with fixture() as (root,data,path,runtime,http):
            invoke(path,data);p=pages_runtime(root,runtime);before=http.puts
            if mode=='oversize': http.mode='oversize'
            timestamp=json.loads(http.file(github.STORE_PATH))['snapshot']['engine']['last_signal_ts']
            with pages_environment(),patch.object(pages,'check_code_pin'),patch.object(pages.ReadClient,'open_request',side_effect=http.open),patch.object(pages.time,'time',return_value=(timestamp+14400000+8*3600000+1)/1000):
                fails(github.StoreError,lambda:pages.export(p,data/'config.json',root/'public'))
            assert http.puts==before and not (root/'public').exists()
