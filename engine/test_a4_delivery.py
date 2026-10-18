"""A4: hard process exits, entire runner loss, real SQLite, simulated transport."""
from contextlib import contextmanager, redirect_stdout, closing
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from unittest.mock import patch

import durable_delivery as durable
import main
import telegram_notify as tg
import telegram_outbox as box
from test_main import szenario, _wache_szenario


def empty():
    return dict(version=1, engine={}, watch={}, commands={})


def setup(root):
    runner = root/'runner'
    data = runner/'data'
    data.mkdir(parents=True)
    (data/'config.json').write_text('{"plan_telegram":false,"vorschau_telegram":false}')
    return data


@contextmanager
def offline(root):
    env = dict(TELEGRAM_BOT_TOKEN='A4_FAKE_TOKEN', TELEGRAM_CHAT_ID='A4_FAKE_TARGET',
               BTC_DELIVERY_STORE=str(root/'volume'), BTC_DELIVERY_STORE_ID='a4-test-store',
               BTC_DELIVERY_RUNNER_ROOT=str(root/'runner'), BTC_DELIVERY_OPERATION_ID='request-1')
    with patch.dict(os.environ, env), \
         patch.object(tg.urllib.request, 'urlopen', side_effect=AssertionError('network forbidden')), \
         redirect_stdout(io.StringIO()):
        yield


def read(root):
    with durable.VolumeStore(root/'volume', 'a4-test-store') as store:
        return deepcopy(store.snapshot)


def messages(snapshot, command=None):
    state = snapshot['engine'] if command is None else next(iter(snapshot['commands'].values()))
    return state.get('_delivery', {}).get('messages', [])


def confirmed(*args):
    return dict(status='confirmed', message_id=73)


def invoke(kind, data):
    if kind == 'engine':
        return main.run_engine(fetch=szenario, data_dir=data)
    if kind == 'test':
        return main.send_testnachricht(data_dir=data)
    if kind == 'resend':
        return main.resend_all_signals(data_dir=data)
    if kind == 'lage':
        return main.lage_abruf(fetch=szenario, data_dir=data, sth=lambda: None)
    if kind == 'watch':
        raw, stamp, now = _wache_szenario(tief=95, schluss=105)
        with patch.object(main, 'zonen_vorschau', return_value=dict(richtung='LONG',gp_lower=100,invalidation=90)):
            return main.watch_flush(data_dir=data, now_ms=now, kerzen_roh=raw)
    raise AssertionError(kind)


def seed_for(kind):
    s = empty()
    if kind == 'watch':
        s['engine'] = dict(pos_state='FLAT', _delivery=dict(version=1,messages=[],signals={'signals':[]},oi_history=[]))
    if kind == 'resend':
        signal = dict(ts=14400000,type='KAUF_1',label='Offline Kauf',price=100,tranche_pct=25,reason='offline')
        s['engine'] = dict(_delivery=dict(version=1,messages=[],signals={'signals':[signal]},oi_history=[]))
    return s


def worker(root, mode, kind):
    data = root/'runner/data'
    with offline(root):
        original = durable.VolumeStore.commit
        def commit(store):
            ms = messages(store.snapshot, None if kind == 'engine' else kind)
            status = ms[0]['status'] if ms else None
            if mode == 'before_intent' and status == 'pending':
                os._exit(71)
            if mode == 'before_receipt' and status == 'confirmed':
                os._exit(71)
            original(store)
            if (mode,status) in {('after_intent','pending'),('after_sending','sending'),('after_receipt','confirmed')}:
                os._exit(71)
        def send(text,*args):
            with (root/'transport.log').open('a',encoding='utf-8') as f:
                f.write(json.dumps(text)+'\n'); f.flush(); os.fsync(f.fileno())
            if mode == 'after_acceptance':
                os._exit(71)
            return confirmed()
        with patch.object(durable.VolumeStore,'commit',commit), \
             patch.object(main,'deliver_telegram',side_effect=send), \
             patch.object(tg,'deliver_telegram',side_effect=send):
            invoke(kind,data)


def attempts(root):
    p=root/'transport.log'
    return len(p.read_text(encoding='utf-8').splitlines()) if p.exists() else 0


def crash_case(mode, expected_status, accepted, after, kind='engine'):
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); setup(root)
        durable.provision(root/'volume','a4-test-store',seed_for(kind))
        proc=subprocess.run([sys.executable,__file__,'--worker',str(root),mode,kind],capture_output=True)
        assert proc.returncode == 71, (kind,mode,proc.stdout,proc.stderr)
        ms=messages(read(root), None if kind=='engine' else kind)
        assert (ms[0]['status'] if ms else None) == expected_status
        assert attempts(root)==accepted
        # The complete temporary runner, not merely state.json, is destroyed.
        shutil.rmtree(root/'runner')
        data=setup(root)
        before=attempts(root)
        def sender(text,*args):
            with (root/'transport.log').open('a',encoding='utf-8') as f:
                f.write(json.dumps(text)+'\n')
            return confirmed()
        with offline(root), patch.object(main,'deliver_telegram',side_effect=sender), patch.object(tg,'deliver_telegram',side_effect=sender):
            if kind=='engine' and expected_status is not None:
                with patch.object(main,'evaluate',side_effect=AssertionError('old signal replayed')):
                    assert invoke(kind,data)==[]
            else:
                invoke(kind,data)
            invoke(kind,data)
        assert attempts(root)-before==after, (mode, kind, attempts(root), before, after)
        final=messages(read(root), None if kind=='engine' else kind)
        assert final[0]['status']==('uncertain' if expected_status=='sending' else 'confirmed')
        assert len(final)==(2 if kind=='resend' else 1)


def test_entire_runner_loss_at_every_engine_boundary():
    for args in [('before_intent',None,0,1),('after_intent','pending',0,1),
                 ('after_sending','sending',0,0),('after_acceptance','sending',1,0),
                 ('before_receipt','sending',1,0),('after_receipt','confirmed',1,0)]:
        crash_case(*args)


def test_all_four_excluded_commands_survive_runner_loss():
    for kind in ('test','resend','lage','watch'):
        for mode,status,count,after in [('after_intent','pending',0,2 if kind=='resend' else 1),
                                      ('after_acceptance','sending',1,0),
                                      ('after_receipt','confirmed',1,1 if kind=='resend' else 0)]:
            crash_case(mode,status,count,after,kind)


def expect(error, fn):
    try:
        fn()
    except error:
        return
    raise AssertionError('Expected '+str(error))


def test_absent_wrong_corrupt_or_runner_local_store_fails_before_fetch_and_send():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); data=setup(root)
        with offline(root), patch.object(main,'deliver_telegram') as send:
            fetch=lambda _: (_ for _ in ()).throw(AssertionError('fetch forbidden'))
            expect(sqlite3.OperationalError, lambda: main.run_engine(fetch=fetch,data_dir=data))
            durable.provision(root/'volume','wrong-id',empty())
            expect(ValueError, lambda: main.run_engine(fetch=fetch,data_dir=data))
            with patch.dict(os.environ,BTC_DELIVERY_STORE=str(root/'runner/volume')):
                expect(ValueError,lambda: main.run_engine(fetch=fetch,data_dir=data))
            with patch.dict(os.environ,BTC_DELIVERY_STORE=''):
                expect(RuntimeError,lambda: main.run_engine(fetch=fetch,data_dir=data))
            with closing(sqlite3.connect(root/'volume/snapshot.sqlite')) as db, db:
                db.execute("UPDATE snapshot SET store_id='a4-test-store',body='{}'")
            expect(ValueError,lambda: main.run_engine(fetch=fetch,data_dir=data))
            assert send.call_count==0


def test_persist_failure_before_send_and_after_acceptance_are_fail_closed():
    for boundary in ('intent','sending','receipt'):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); data=setup(root); durable.provision(root/'volume','a4-test-store',empty())
            real=durable.VolumeStore.commit
            def fail(store):
                status=messages(store.snapshot)[0]['status']
                if status=={'intent':'pending','sending':'sending','receipt':'confirmed'}[boundary]:
                    raise OSError('simulated durable failure')
                real(store)
            with offline(root), patch.object(durable.VolumeStore,'commit',fail), patch.object(main,'deliver_telegram',side_effect=confirmed) as send:
                expect(OSError,lambda: invoke('engine',data))
                assert send.call_count==(1 if boundary=='receipt' else 0)
            shutil.rmtree(root/'runner'); data=setup(root)
            with offline(root), patch.object(main,'deliver_telegram',side_effect=confirmed) as send:
                invoke('engine',data)
                assert send.call_count==(0 if boundary=='receipt' else 1)
            assert messages(read(root))[0]['status']==('uncertain' if boundary=='receipt' else 'confirmed')


def test_external_receipt_survives_failed_local_mirror():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); data=setup(root); durable.provision(root/'volume','a4-test-store',empty())
        replace=box.os.replace
        def fail(src,dst):
            if Path(dst).name=='state.json' and '"status":"confirmed"' in Path(src).read_text(encoding='utf-8'):
                raise OSError('local mirror lost')
            replace(src,dst)
        with offline(root), patch.object(box.os,'replace',fail), patch.object(main,'deliver_telegram',side_effect=confirmed) as send:
            expect(OSError,lambda: invoke('engine',data))
            assert send.call_count==1
        assert messages(read(root))[0]['status']=='confirmed'
        shutil.rmtree(root/'runner'); data=setup(root)
        with offline(root), patch.object(main,'deliver_telegram') as send:
            assert invoke('engine',data)==[] and send.call_count==0


def test_rejected_retries_before_fetch_even_with_lost_runner():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); data=setup(root); durable.provision(root/'volume','a4-test-store',empty())
        with offline(root),patch.object(main,'deliver_telegram',return_value=dict(status='rejected',message_id=None)):
            invoke('engine',data)
        mid=messages(read(root))[0]['id']
        shutil.rmtree(root/'runner'); data=setup(root)
        with offline(root),patch.object(main,'deliver_telegram',side_effect=confirmed) as send:
            def fetch(_):
                assert send.call_count==1
                raise OSError('market unavailable')
            expect(OSError,lambda: main.run_engine(fetch=fetch,data_dir=data))
        m=messages(read(root))[0]
        assert (m['id'],m['status'],m['attempts'])==(mid,'confirmed',2)


def test_concurrent_process_cannot_recover_or_send_active_attempt():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); setup(root); durable.provision(root/'volume','a4-test-store',empty())
        with durable.VolumeStore(root/'volume','a4-test-store'):
            proc=subprocess.run([sys.executable,__file__,'--worker',str(root),'normal','engine'],capture_output=True)
            assert proc.returncode!=0 and b'locked' in proc.stderr
            assert attempts(root)==0
        with offline(root),patch.object(main,'deliver_telegram',side_effect=confirmed):
            invoke('engine',root/'runner/data')
        assert messages(read(root))[0]['status']=='confirmed'


def test_uncertain_blocks_new_command_ids_and_engine_dispatch():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); data=setup(root); durable.provision(root/'volume','a4-test-store',empty())
        with offline(root),patch.object(tg,'deliver_telegram',side_effect=TimeoutError('fake')) as send:
            invoke('test',data)
            with patch.dict(os.environ,BTC_DELIVERY_OPERATION_ID='different'):
                expect(RuntimeError,lambda: invoke('test',data))
            with patch.object(main,'deliver_telegram') as engine_send:
                invoke('engine',data)
                assert engine_send.call_count==0
            assert send.call_count==1
        assert messages(read(root),'test')[0]['status']=='uncertain'


def test_manual_commands_need_stable_id_and_direct_send_cannot_bypass():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); data=setup(root); durable.provision(root/'volume','a4-test-store',empty())
        with offline(root),patch.dict(os.environ,BTC_DELIVERY_OPERATION_ID=''),patch.object(tg,'deliver_telegram') as send:
            for kind in ('test','resend','lage'):
                expect(ValueError,lambda: invoke(kind,data))
            expect(RuntimeError,lambda: tg.send_telegram('text','fake','fake'))
            assert send.call_count==0


def test_dry_run_never_touches_external_snapshot_or_dispatches():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); data=setup(root); durable.provision(root/'volume','a4-test-store',empty())
        before=(root/'volume/snapshot.sqlite').read_bytes()
        with offline(root),patch.object(main,'deliver_telegram') as a,patch.object(tg,'deliver_telegram') as b:
            main.run_engine(fetch=szenario,data_dir=data,dry_run=True)
            main.send_testnachricht(data_dir=data,dry_run=True)
            assert a.call_count==b.call_count==0
        assert (root/'volume/snapshot.sqlite').read_bytes()==before


def test_migration_requires_complete_snapshot_and_never_overwrites():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        expect(ValueError,lambda: durable.provision(root/'volume','a4-test-store',{**empty(),'engine':{'pos_state':'T1'}}))
        durable.provision(root/'volume','a4-test-store',empty())
        expect(FileExistsError,lambda: durable.provision(root/'volume','a4-test-store',empty()))


def test_command_retry_uses_frozen_batch_without_fetch_or_reformat():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); data=setup(root); durable.provision(root/'volume','a4-test-store',empty())
        with offline(root),patch.object(tg,'deliver_telegram',return_value=dict(status='rejected',message_id=None)) as send:
            original=invoke('lage',data)
            text=send.call_args.args[0]
        shutil.rmtree(root/'runner'); data=setup(root)
        with offline(root),patch.object(tg,'deliver_telegram',side_effect=confirmed) as send:
            result=main.lage_abruf(data_dir=data,fetch=lambda _: (_ for _ in ()).throw(AssertionError('re-fetch')),sth=lambda:None)
            assert result==original and send.call_count==1 and send.call_args.args[0]==text
            assert invoke('lage',data)==original and send.call_count==1
            with patch.dict(os.environ,BTC_DELIVERY_OPERATION_ID='explicit-new-request'):
                invoke('lage',data)
            assert send.call_count==2
        assert len(read(root)['commands'])==2


def test_recovery_retains_target_binding_and_active_position():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); data=setup(root); durable.provision(root/'volume','a4-test-store',empty())
        with offline(root),patch.object(main,'deliver_telegram',return_value=dict(status='rejected',message_id=None)):
            invoke('engine',data)
        before=read(root)['engine']
        assert before['pos_state']=='T1' and before['bestand_pct']>0
        shutil.rmtree(root/'runner'); data=setup(root)
        # Stale checkout state must not overrule durable position or delivery.
        (data/'state.json').write_text('{"pos_state":"FLAT","last_signal_ts":0}')
        with offline(root),patch.dict(os.environ,TELEGRAM_CHAT_ID='changed-target'),patch.object(main,'deliver_telegram') as send:
            assert invoke('engine',data)==[] and send.call_count==0
        after=read(root)['engine']
        assert after['bestand_pct']==before['bestand_pct'] and after['pos_state']==before['pos_state']
        assert after['_delivery']['messages']==before['_delivery']['messages']


def test_watch_and_engine_share_durable_resolution_after_runner_loss():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); data=setup(root); durable.provision(root/'volume','a4-test-store',seed_for('watch'))
        with offline(root),patch.object(tg,'deliver_telegram',side_effect=confirmed):
            warning=invoke('watch',data)
        assert warning and not read(root)['watch']['aufgeloest']
        shutil.rmtree(root/'runner'); data=setup(root)
        from strategy_core import Candle
        c=Candle(warning['gewarnt_ts'],105,110,95,105)
        with offline(root),patch.object(main,'deliver_telegram',side_effect=confirmed):
            main.run_engine(fetch=lambda _:([c],[],[]),data_dir=data)
        saved=read(root)
        assert saved['watch']['aufgeloest']
        assert any(m['kind']=='flush_aufloesung' and m['status']=='confirmed' for m in messages(saved))
        shutil.rmtree(root/'runner'); data=setup(root)
        with offline(root),patch.object(main,'deliver_telegram') as send:
            main.run_engine(fetch=lambda _:([c],[],[]),data_dir=data)
            assert send.call_count==0
        assert json.loads((data/'watch.json').read_text())==saved['watch']


if __name__=='__main__' and '--worker' in sys.argv:
    worker(Path(sys.argv[2]),sys.argv[3],sys.argv[4])
