"""P2 M: exact pinned P1 rehearsal, source integrity, and hard negative gates."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import produktion_migrate as migrate
import produktion_store
import durable_delivery as durable
from production_contract import CANDLE_MS, digest

P1='ca8ad2fb730174ca1887791d425ae01aa6a715e6'


def _blob(name):
    return subprocess.check_output(['git','show',f'{P1}:site/data/{name}'],cwd=ROOT)


def fixture(root):
    root=Path(root); source=root/'source'; source.mkdir()
    names=('state.json','signals.json','oi_history.json','config-source.json')
    for name in names:
        (source/name).write_bytes(_blob('config.json' if name=='config-source.json' else name))
    state=json.loads((source/'state.json').read_text(encoding='utf-8'))
    b=state['last_signal_ts']; t=b+CANDLE_MS+1000
    files={name:{'sha256':hashlib.sha256((source/name).read_bytes()).hexdigest(),
                 'size':(source/name).stat().st_size} for name in names}
    files['watch.json']={'presence':'missing'}
    manifest={'schema':'produktion-source-v1','mode':'rehearsal','repository':'synthetic-p1',
              'code_sha':P1,'source_sha':P1,'git_tree':'synthetic-tree',
              'captured_at_utc':'2026-10-03T16:00:00Z','files':files}
    cutover={'freeze_at_ms':t,'last_persisted_B':b,'source_sha':P1,
             'last_runs':[{'id':'synthetic-p1','status':'complete'}],
             'synthetic':True,'writers_stopped':False,'snapshot_consistent':False,
             'stream_id':'synthetic-stream','store_id':'synthetic-store',
             'target_binding':hashlib.sha256(b'synthetic-target').hexdigest(),
             'bot_identity':'synthetic-bot','code_sha':'a'*40}
    target=json.loads((ROOT/'site/data/config.json').read_text(encoding='utf-8'))
    for name,value in [('source-manifest.json',manifest),('cutover.json',cutover),('config-target.json',target)]:
        (root/name).write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
    return source,root/'source-manifest.json',root/'cutover.json',root/'config-target.json',root/'out'


def test_p1_t1_rehearsal_preserves_position_and_history():
    with tempfile.TemporaryDirectory() as td:
        paths=fixture(td)
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths[0].iterdir()}
        report=migrate.convert(*paths)
        snap=produktion_store.verify_package(paths[-1])
        old=json.loads((paths[0]/'state.json').read_text(encoding='utf-8'))
        new=snap['engine']
        assert old['pos_state']==new['pos_state']=='T1'
        for key in ('last_signal_ts','entry_ref','entry_pct','bestand_pct','tp_rungs',
                    'dip_buys','buy_rungs','liq_exits','high_exits','liq_entries',
                    'retrace_extreme','ziel_extrem','be_aktiv','last_stop_ts',
                    'stop_wartet','stop_wartet_inv','e42_marke','e42_richtung'):
            assert old[key]==new[key],key
        assert new['inventory_source']=='signal_reference' and new['lots']==[]
        assert new['valid_stop'] is None and 'prior_stop_maximum_unknown' in report['unknowns']
        assert new['config']['muster_cvd']=='usd' and snap['control']['mode']=='blocked'
        assert snap['control']['migration']['legacy_delivery']=='unknown_no_replay'
        assert new['_delivery']['messages']==[]
        hist=json.loads((paths[0]/'signals.json').read_text(encoding='utf-8'))
        assert new['_delivery']['signals']==hist and report['signal_count']==len(hist['signals'])
        assert digest(hist)==snap['control']['migration']['history_sha256']
        assert report['activation_ready'] is False
        assert before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths[0].iterdir()}
        store=Path(td)/'store'
        produktion_store.provision(paths[-1],store)
        with durable.VolumeStore(store,'synthetic-store') as volume:
            assert volume.snapshot==snap and volume.snapshot['control']['mode']=='blocked'
        try: produktion_store.provision(paths[-1],store)
        except FileExistsError: pass
        else: raise AssertionError('Existing store overwritten')


def test_migration_rejects_gaps_foreign_journal_and_changed_source():
    for change in ('gap','journal','source','nan','history_future','run'):
        with tempfile.TemporaryDirectory() as td:
            paths=fixture(td)
            source,manifest_path,cutover_path,_,out=paths
            manifest=json.loads(manifest_path.read_text())
            cutover=json.loads(cutover_path.read_text())
            if change=='gap': cutover['freeze_at_ms']+=CANDLE_MS
            if change=='run': cutover['last_runs'][0]['status']='unknown'
            if change in ('gap','run'):
                cutover_path.write_text(json.dumps(cutover),encoding='utf-8')
            if change in ('journal','nan'):
                state=json.loads((source/'state.json').read_text())
                if change=='journal': state['_delivery']={'version':1,'messages':[]}
                else: state['entry_ref']=float('nan')
                (source/'state.json').write_text(json.dumps(state),encoding='utf-8')
            if change=='history_future':
                hist=json.loads((source/'signals.json').read_text())
                hist['signals'].append({'ts':cutover['last_persisted_B']+CANDLE_MS,'type':'TEST'})
                (source/'signals.json').write_text(json.dumps(hist),encoding='utf-8')
            if change=='source': (source/'state.json').write_bytes((source/'state.json').read_bytes()+b' ')
            if change in ('journal','nan','history_future'):
                name='signals.json' if change=='history_future' else 'state.json'
                data=(source/name).read_bytes()
                manifest['files'][name]={'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)}
                manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
            try: migrate.convert(*paths)
            except (ValueError,TypeError): pass
            else: raise AssertionError(change)
            assert not out.exists()


def test_p1_direct_store_import_still_refused():
    with tempfile.TemporaryDirectory() as td:
        old=json.loads(_blob('state.json'))
        try: durable.provision(Path(td)/'store','synthetic-store',
                              {'version':1,'engine':old,'watch':{},'commands':{}})
        except ValueError as exc: assert 'Migration requires' in str(exc)
        else: raise AssertionError('P1 direct provision accepted')


def test_more_than_500_legacy_signals_survive_first_continuation():
    from unittest.mock import patch
    import os
    import main
    from strategy_core import Candle
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);paths=fixture(root)
        source,manifest_path,_,config_path,out=paths
        old=json.loads((source/'state.json').read_text(encoding='utf-8'))
        history=json.loads((source/'signals.json').read_text(encoding='utf-8'))
        history['signals'] += [{'ts':old['last_signal_ts']-i*CANDLE_MS,'type':'WARNUNG',
                                'price':100+i,'tranche_pct':0,'reason':'synthetic'} for i in range(600)]
        (source/'signals.json').write_text(json.dumps(history),encoding='utf-8')
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        data=(source/'signals.json').read_bytes()
        manifest['files']['signals.json']={'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)}
        manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
        migrate.convert(*paths)
        store=root/'store';produktion_store.provision(out,store)
        with durable.VolumeStore(store,'synthetic-store') as volume:
            volume.snapshot['control']['mode']='active';volume.commit()
        runner=root/'runner';local=runner/'data';local.mkdir(parents=True)
        (local/'config.json').write_bytes(config_path.read_bytes())
        env={'BTC_DELIVERY_STORE':str(store),'BTC_DELIVERY_STORE_ID':'synthetic-store',
             'BTC_DELIVERY_RUN_REPOSITORY':'synthetic/code', 'BTC_DELIVERY_WORKFLOW':'.github/workflows/synthetic.yml',
             'BTC_DELIVERY_RUN_ID':'synthetic-100', 'BTC_DELIVERY_RUN_ATTEMPT':'1',
             'BTC_DELIVERY_EXPECTED_START_MS':'1791100800000',
             'BTC_DELIVERY_RUNNER_ROOT':str(runner),'BTC_DELIVERY_CODE_SHA':'a'*40,
             'BTC_DELIVERY_BOT_IDENTITY':'synthetic-bot','TELEGRAM_BOT_TOKEN':'fake',
             'TELEGRAM_CHAT_ID':'synthetic-target'}
        b=old['last_signal_ts'];c=Candle(b,80000,81000,79000,80000)
        with patch.dict(os.environ,env),patch.object(main,'positions_plan',return_value=old.get('plan')),\
             patch.object(main,'zonen_vorschau',return_value=old.get('zonen_vorschau')),\
             patch.object(main,'widerstand_marken',return_value=old.get('widerstand')),\
             patch.object(main,'deliver_telegram',side_effect=AssertionError('historical replay')):
            assert main.run_engine(fetch=lambda previous:([c],[],previous),data_dir=local)==[]
        with durable.VolumeStore(store,'synthetic-store') as volume:
            assert volume.snapshot['engine']['_delivery']['signals']==history
            assert volume.snapshot['engine']['_delivery']['messages']==[]
