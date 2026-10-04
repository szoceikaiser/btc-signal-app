"""P2 S: shared v2 gate, pinned configuration and synthetic transport."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import shutil
from unittest.mock import patch

import durable_delivery as durable
import main
import telegram_notify as tg
from test_production_migration import fixture, migrate, produktion_store


def seeded(root):
    paths=fixture(root)
    migrate.convert(*paths)
    store=Path(root)/'store'
    produktion_store.provision(paths[-1],store)
    runner=Path(root)/'runner';data=runner/'data';data.mkdir(parents=True)
    (data/'config.json').write_bytes(paths[3].read_bytes())
    return store,data,paths


@contextmanager
def active(root,store,data):
    with durable.VolumeStore(store,'synthetic-store') as volume:
        volume.snapshot['control']['mode']='active'
        volume.commit()
    env={'BTC_DELIVERY_STORE':str(store),'BTC_DELIVERY_STORE_ID':'synthetic-store',
         'BTC_DELIVERY_RUNNER_ROOT':str(data.parent),
         'BTC_DELIVERY_CODE_SHA':'a'*40,'BTC_DELIVERY_BOT_IDENTITY':'synthetic-bot',
         'BTC_DELIVERY_OPERATION_ID':'synthetic-request','TELEGRAM_BOT_TOKEN':'fake',
         'TELEGRAM_CHAT_ID':'synthetic-target'}
    with patch.dict(os.environ,env): yield


def expect(error,fn):
    try: fn()
    except error: return
    raise AssertionError('Expected '+str(error))


def test_blocked_v2_prevents_fetch_and_transport():
    with tempfile.TemporaryDirectory() as td:
        store,data,_=seeded(td)
        env={'BTC_DELIVERY_STORE':str(store),'BTC_DELIVERY_STORE_ID':'synthetic-store',
             'BTC_DELIVERY_RUNNER_ROOT':str(data.parent),'TELEGRAM_BOT_TOKEN':'fake',
             'TELEGRAM_CHAT_ID':'synthetic-target'}
        with patch.dict(os.environ,env),patch.object(main,'deliver_telegram') as send:
            expect(ValueError,lambda:main.run_engine(fetch=lambda _:(_ for _ in ()).throw(AssertionError('fetch')),data_dir=data))
            assert send.call_count==0


def test_shared_entry_never_falls_back_to_local_without_store_identity():
    import produktion_runner
    with tempfile.TemporaryDirectory() as td:
        _,data,_=seeded(td)
        with patch.dict(os.environ,{},clear=True):
            expect(ValueError,lambda:produktion_runner.run_checked('signal',data,
                fetch=lambda _:(_ for _ in ()).throw(AssertionError('fetch'))))
            expect(ValueError,lambda:produktion_runner.run_checked('test',data))


def test_uncertain_globally_blocks_new_ids_and_market_access():
    with tempfile.TemporaryDirectory() as td:
        store,data,_=seeded(td)
        with active(td,store,data),patch.object(tg,'deliver_telegram',side_effect=TimeoutError('synthetic')):
            main.send_testnachricht(data_dir=data)
            with patch.dict(os.environ,BTC_DELIVERY_OPERATION_ID='new-id'):
                expect(RuntimeError,lambda:main.send_testnachricht(data_dir=data))
            expect(RuntimeError,lambda:main.run_engine(fetch=lambda _:(_ for _ in ()).throw(AssertionError('fetch')),data_dir=data))
            expect(RuntimeError,lambda:main.lage_abruf(fetch=lambda _:(_ for _ in ()).throw(AssertionError('fetch')),data_dir=data))
            expect(RuntimeError,lambda:main.watch_flush(data_dir=data,kerzen_roh=[]))
            expect(RuntimeError,lambda:main.resend_all_signals(data_dir=data))
        with durable.VolumeStore(store,'synthetic-store') as volume:
            ms=next(iter(volume.snapshot['commands'].values()))['_delivery']['messages']
            assert len(ms)==1 and ms[0]['status']=='uncertain'


def test_receipt_requires_matching_target_and_config_is_pinned():
    with tempfile.TemporaryDirectory() as td:
        store,data,_=seeded(td)
        with active(td,store,data),patch.object(tg,'deliver_telegram',return_value={'status':'confirmed','message_id':72,'target_binding':'wrong'}):
            main.send_testnachricht(data_dir=data)
        with durable.VolumeStore(store,'synthetic-store') as volume:
            assert next(iter(volume.snapshot['commands'].values()))['_delivery']['messages'][0]['status']=='uncertain'
        with tempfile.TemporaryDirectory() as other:
            store2,data2,_=seeded(other)
            with active(other,store2,data2):
                cfg=json.loads((data2/'config.json').read_text(encoding='utf-8'))
                cfg['muster_cvd']='alt'
                (data2/'config.json').write_text(json.dumps(cfg),encoding='utf-8')
                expect(ValueError,lambda:main.run_engine(fetch=lambda _:(_ for _ in ()).throw(AssertionError('fetch')),data_dir=data2))
                (data2/'config.json').unlink()
                expect(FileNotFoundError,lambda:main.send_testnachricht(data_dir=data2))


def test_offline_runner_uses_throwaway_store_and_no_network():
    import produktion_runner
    with tempfile.TemporaryDirectory() as td:
        store,data,paths=seeded(td)
        fixture_path=Path(td)/'fixture.json'
        fixture_path.write_text(json.dumps({'synthetic':True,'candles':[],'flow':[]}),encoding='utf-8')
        with durable.VolumeStore(store,'synthetic-store') as volume: before=volume.revision
        result=produktion_runner.simulate(store,'synthetic-store',paths[3],fixture_path,'test')
        assert result['simulated_confirmed']==1 and result['real_transport'] is False
        with durable.VolumeStore(store,'synthetic-store') as volume:
            assert volume.revision==before and volume.snapshot['commands']=={}


def test_watch_boundary_and_old_flush_resolution_are_suppressed():
    from strategy_core import Candle
    from production_contract import CANDLE_MS
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);store,data,_=seeded(root)
        with durable.VolumeStore(store,'synthetic-store') as volume:
            w=volume.snapshot['control']['migration']['W']
            volume.snapshot['watch']={'gewarnt_ts':w,'aufgeloest':False,'preis':100}
            volume.commit()
        raw=[]
        for i in range(30,0,-1):
            ts=w-i*CANDLE_MS
            raw.append([ts,100,101,99,100,0,ts+CANDLE_MS-1])
        raw.append([w,100,101,99,100,0,w+CANDLE_MS-1])
        with active(root,store,data),patch.object(tg,'deliver_telegram',side_effect=AssertionError('old watch send')),\
             patch.object(main,'deliver_telegram',side_effect=AssertionError('old resolution send')):
            assert main.watch_flush(data_dir=data,now_ms=w+1000,kerzen_roh=raw) is None
            old=json.loads((data/'state.json').read_text(encoding='utf-8')) if (data/'state.json').exists() else None
            with patch.object(main,'evaluate',return_value=[]),\
                 patch.object(main,'positions_plan',return_value=None),\
                 patch.object(main,'widerstand_marken',return_value=None),\
                 patch.object(main,'zonen_vorschau',return_value=None):
                main.run_engine(fetch=lambda previous:([Candle(w,100,101,99,100)],[],previous),data_dir=data)
        with durable.VolumeStore(store,'synthetic-store') as volume:
            assert volume.snapshot['watch']['aufgeloest'] is False
            assert volume.snapshot['engine']['_delivery']['messages']==[]
            assert volume.snapshot['control']['health']['last_watch_check_ms'] is not None


def _crash_worker(root,mode):
    root=Path(root);store=root/'store';data=root/'runner/data'
    target_hash=hashlib.sha256(b'synthetic-target').hexdigest()
    original=durable.VolumeStore.commit
    def commit(volume):
        commands=volume.snapshot['commands']
        messages=next(iter(commands.values()))['_delivery']['messages'] if commands else []
        status=messages[0]['status'] if messages else None
        original(volume)
        if (mode,status) in (('after_intent','pending'),('after_sending','sending'),
                             ('after_receipt','confirmed')):
            os._exit(71)
    def send(*args):
        with (root/'transport.log').open('a',encoding='utf-8') as stream:
            stream.write('accepted\n');stream.flush();os.fsync(stream.fileno())
        if mode=='after_acceptance': os._exit(71)
        return {'status':'confirmed','message_id':73,'target_binding':target_hash}
    with patch.object(durable.VolumeStore,'commit',commit),patch.object(tg,'deliver_telegram',side_effect=send):
        main.send_testnachricht(data_dir=data)


def test_v2_child_crashes_survive_entire_runner_loss():
    for mode,expected,first,after in (
            ('after_intent','pending',0,1),('after_sending','sending',0,0),
            ('after_acceptance','sending',1,0),('after_receipt','confirmed',1,0)):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);store,data,paths=seeded(root)
            with durable.VolumeStore(store,'synthetic-store') as volume:
                volume.snapshot['control']['mode']='active';volume.commit()
            env={**os.environ,'BTC_DELIVERY_STORE':str(store),'BTC_DELIVERY_STORE_ID':'synthetic-store',
                 'BTC_DELIVERY_RUNNER_ROOT':str(root/'runner'),'BTC_DELIVERY_CODE_SHA':'a'*40,
                 'BTC_DELIVERY_BOT_IDENTITY':'synthetic-bot','BTC_DELIVERY_OPERATION_ID':'stable-id',
                 'TELEGRAM_BOT_TOKEN':'fake','TELEGRAM_CHAT_ID':'synthetic-target'}
            proc=subprocess.run([sys.executable,__file__,'--p2-worker',str(root),mode],env=env,
                                capture_output=True)
            assert proc.returncode==71,(mode,proc.stderr)
            accepted=(root/'transport.log').read_text().count('accepted') if (root/'transport.log').exists() else 0
            assert accepted==first
            shutil.rmtree(root/'runner')
            data=root/'runner/data';data.mkdir(parents=True)
            (data/'config.json').write_bytes(paths[3].read_bytes())
            target_hash=hashlib.sha256(b'synthetic-target').hexdigest()
            def send(*args):
                with (root/'transport.log').open('a',encoding='utf-8') as stream:
                    stream.write('accepted\n')
                return {'status':'confirmed','message_id':74,'target_binding':target_hash}
            with patch.dict(os.environ,env),patch.object(tg,'deliver_telegram',side_effect=send):
                if expected=='sending':
                    expect(RuntimeError,lambda:main.send_testnachricht(data_dir=data))
                else:
                    main.send_testnachricht(data_dir=data)
            accepted=(root/'transport.log').read_text().count('accepted') if (root/'transport.log').exists() else 0
            assert accepted-first==after
            with durable.VolumeStore(store,'synthetic-store') as volume:
                status=next(iter(volume.snapshot['commands'].values()))['_delivery']['messages'][0]['status']
                assert status==('uncertain' if expected=='sending' else 'confirmed')


if __name__=='__main__' and '--p2-worker' in sys.argv:
    _crash_worker(sys.argv[2],sys.argv[3])
