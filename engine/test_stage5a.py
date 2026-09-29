"""F13 reached production/transport/crash cases. All sends and fetches are offline."""
from contextlib import contextmanager, redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import urllib.error

import main
import telegram_notify as tg
import telegram_outbox as box
from test_main import szenario, _vorschau_kerzen
from strategy_core import Candle, Position, PosState, Pivot, Impulse, fib_zones

CREDS = dict(TELEGRAM_BOT_TOKEN='F13_FAKE_TOKEN', TELEGRAM_CHAT_ID='F13_FAKE_CHAT')


@contextmanager
def offline(credentials=True):
    with patch.dict(os.environ, CREDS if credentials else dict(TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='')), \
         patch.object(tg.urllib.request, 'urlopen', side_effect=AssertionError('network forbidden')), \
         redirect_stdout(io.StringIO()) as output:
        yield output


def setup(directory, **config):
    (directory/'config.json').write_text(json.dumps(dict(plan_telegram=False, vorschau_telegram=False, **config)))


def read(directory):
    return json.loads((directory/'state.json').read_text(encoding='utf-8'))


def messages(directory):
    return read(directory)['_delivery']['messages']


def confirmed(text, token, chat):
    return dict(status='confirmed', message_id=101)


def rejected(text, token, chat):
    return dict(status='rejected', message_id=None)


def run(directory, **kw):
    return main.run_engine(fetch=szenario, data_dir=directory, **kw)


def expect(exception, fn):
    try:
        fn()
    except exception:
        return
    raise AssertionError('Expected '+exception.__name__)


class Response(io.BytesIO):
    def __init__(self, body):
        super().__init__(json.dumps(body).encode())


def transport(body):
    with patch.object(tg.urllib.request, 'urlopen', return_value=Response(body)) as request:
        result = tg.deliver_telegram('offline', 'FAKE', 'FAKE')
        assert request.call_count == 1
        return result


def test_rejection_retries_same_intent_without_replaying_real_buy():
    with tempfile.TemporaryDirectory() as temp, offline():
        d = Path(temp); setup(d)
        with patch.object(main, 'deliver_telegram', side_effect=rejected) as sender:
            first = run(d)
            assert [s['type'] for s in first] == ['KAUF_1'] and sender.call_count == 1
        before = read(d); original = messages(d)[0]
        assert original['status'] == 'rejected' and before['pos_state'] == 'T1'
        with patch.object(main, 'evaluate', side_effect=AssertionError('old candle replayed')), \
             patch.object(main, 'deliver_telegram', side_effect=confirmed) as sender:
            assert run(d) == [] and sender.call_count == 1
            assert sender.call_args.args[0] == original['text']
        m = messages(d)[0]
        assert (m['id'], m['status'], m['attempts'], m['receipt']) == (original['id'], 'confirmed', 2, 101)
        assert read(d)['bestand_pct'] == before['bestand_pct']
        assert len(read(d)['_delivery']['signals']['signals']) == 1


def test_confirmed_is_never_resent_on_restart():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram', side_effect=confirmed) as sender:
        d = Path(temp); setup(d); run(d); run(d)
        assert sender.call_count == 1 and messages(d)[0]['status'] == 'confirmed'


def test_timeout_after_acceptance_is_uncertain_never_automatically_retried():
    accepted = []
    def timeout(text, *args):
        accepted.append(text)
        raise TimeoutError('F13_FAKE_TOKEN potentially accepted')
    with tempfile.TemporaryDirectory() as temp, offline() as output, patch.object(main, 'deliver_telegram', side_effect=timeout):
        d = Path(temp); setup(d); run(d); run(d)
        assert len(accepted) == 1 and messages(d)[0]['status'] == 'uncertain'
        assert 'F13_FAKE_TOKEN' not in output.getvalue()+(d/'state.json').read_text()


def test_missing_credentials_remains_pending_then_sends_once():
    with tempfile.TemporaryDirectory() as temp:
        d = Path(temp); setup(d)
        with offline(False):
            run(d)
        assert messages(d)[0]['status'] == 'pending' and messages(d)[0]['attempts'] == 0
        with offline(), patch.object(main, 'deliver_telegram', side_effect=confirmed) as sender:
            assert run(d) == [] and sender.call_count == 1
        assert messages(d)[0]['status'] == 'confirmed'


def test_dry_run_is_terminal_preview_even_when_credentials_appear():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram', side_effect=AssertionError('preview sent')):
        d = Path(temp); setup(d); run(d, dry_run=True); run(d)
        assert messages(d)[0]['status'] == 'preview' and messages(d)[0]['receipt'] is None


def test_commit_exists_before_any_transport_attempt():
    with tempfile.TemporaryDirectory() as temp, offline():
        d = Path(temp); setup(d)
        def send(text, *args):
            assert (d/'state.json').exists()
            s = read(d); m = s['_delivery']['messages'][0]
            assert s['pos_state'] == 'T1' and s['last_signal_ts'] == szenario()[0][-1].ts
            assert m['text'] == text and m['status'] == 'sending' and m['attempts'] == 1
            assert s['_delivery']['signals']['signals'][0]['type'] == 'KAUF_1'
            return confirmed(text, *args)
        with patch.object(main, 'deliver_telegram', side_effect=send):
            run(d)
        assert messages(d)[0]['status'] == 'confirmed'


def test_atomic_failure_before_commit_does_not_send_or_advance():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram') as sender:
        d = Path(temp); setup(d)
        with patch.object(box.os, 'replace', side_effect=OSError('disk error')):
            expect(OSError, lambda: run(d))
        assert not (d/'state.json').exists() and sender.call_count == 0
        with patch.object(main, 'deliver_telegram', side_effect=confirmed):
            assert len(run(d)) == 1


def test_projection_failure_after_commit_repairs_then_sends_without_signal_replay():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram', side_effect=confirmed) as sender:
        d = Path(temp); setup(d)
        atomic = box.atomic_json
        def broken(path, value):
            if Path(path).name == 'signals.json':
                raise OSError('projection disk error')
            return atomic(path, value)
        with patch.object(box, 'atomic_json', side_effect=broken):
            expect(OSError, lambda: run(d))
        assert messages(d)[0]['status'] == 'pending' and sender.call_count == 0
        assert run(d) == [] and sender.call_count == 1
        assert json.loads((d/'signals.json').read_text()) == read(d)['_delivery']['signals']


def test_sending_write_failure_makes_no_attempt_and_recovers_pending():
    with tempfile.TemporaryDirectory() as temp, offline(False):
        d = Path(temp); setup(d); run(d)
        atomic = box.atomic_json
        def broken(path, value):
            if Path(path).name == 'state.json' and value['_delivery']['messages'][0]['status'] == 'sending':
                raise OSError('before attempt')
            return atomic(path, value)
        with offline(), patch.object(box, 'atomic_json', side_effect=broken), patch.object(main, 'deliver_telegram') as sender:
            expect(OSError, lambda: run(d))
            assert sender.call_count == 0
        assert messages(d)[0]['status'] == 'pending'
        with offline(), patch.object(main, 'deliver_telegram', side_effect=confirmed):
            run(d)
        assert messages(d)[0]['status'] == 'confirmed'


def test_receipt_write_failure_keeps_sending_then_uncertain_on_restart():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram', side_effect=confirmed) as sender:
        d = Path(temp); setup(d); atomic = box.atomic_json
        def broken(path, value):
            if isinstance(value, dict) and value.get('_delivery', {}).get('messages') and value['_delivery']['messages'][0]['status'] == 'confirmed':
                raise OSError('receipt disk error')
            return atomic(path, value)
        with patch.object(box, 'atomic_json', side_effect=broken):
            expect(OSError, lambda: run(d))
        assert messages(d)[0]['status'] == 'sending' and sender.call_count == 1
        run(d)
        assert messages(d)[0]['status'] == 'uncertain' and sender.call_count == 1


def test_queue_retries_when_market_fetch_has_no_candles():
    with tempfile.TemporaryDirectory() as temp, offline(False):
        d = Path(temp); setup(d); run(d)
        with offline(), patch.object(main, 'deliver_telegram', side_effect=confirmed) as sender:
            assert main.run_engine(fetch=lambda old: ([], [], []), data_dir=d) == []
            assert sender.call_count == 1 and messages(d)[0]['status'] == 'confirmed'


def test_queue_retries_before_market_fetch_exception():
    with tempfile.TemporaryDirectory() as temp, offline(False):
        d = Path(temp); setup(d); run(d)
        def broken(old): raise RuntimeError('market unavailable')
        with offline(), patch.object(main, 'deliver_telegram', side_effect=confirmed) as sender:
            expect(RuntimeError, lambda: main.run_engine(fetch=broken, data_dir=d))
            assert sender.call_count == 1 and messages(d)[0]['status'] == 'confirmed'


def test_stable_id_is_independent_of_dict_order_and_text_is_fixed():
    a = dict(version=1, messages=[])
    box.enqueue(a, 'signal', 100, 0, dict(x=1, y=2), 'fixed')
    box.enqueue(a, 'signal', 100, 0, dict(y=2, x=1), 'fixed')
    assert len(a['messages']) == 1
    expect(ValueError, lambda: box.enqueue(a, 'signal', 100, 0, dict(x=1, y=2), 'changed'))
    box.enqueue(a, 'signal', 100, 1, dict(x=1, y=2), 'fixed')
    assert len(a['messages']) == 2 and a['messages'][0]['id'] != a['messages'][1]['id']


def test_goal_change_blocks_rejected_message_and_does_not_persist_chat_or_token():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram', side_effect=rejected) as sender:
        d = Path(temp); setup(d); run(d)
        with patch.dict(os.environ, TELEGRAM_CHAT_ID='OTHER'):
            run(d)
        assert sender.call_count == 1 and messages(d)[0]['status'] == 'rejected'
        text = (d/'state.json').read_text()
        assert 'F13_FAKE_CHAT' not in text and 'F13_FAKE_TOKEN' not in text


def multi(directory, sender):
    z = fib_zones(Impulse(Pivot(0, 0, 80, 'L'), Pivot(1, 14400000, 160, 'H')))
    p = Position(direction='LONG', state=PosState.CORE, zones=z, retrace_extreme=100,
        entry_ref=110, entry_pct=75, bestand_pct=75, last_signal_ts=14400000)
    (directory/'state.json').write_text(json.dumps(main.pos_to_state(p)))
    setup(directory, stop_rueckeroberung=1, buy_ladder=False, trail_stop=False,
          high_exit='off', bias_short=False, rest_halten=True)
    c = Candle(28800000, 120, 170, 79, 79.5)
    with patch.object(main, 'deliver_telegram', side_effect=sender):
        sigs = main.run_engine(fetch=lambda old: ([c], [], []), data_dir=directory)
    assert [s['type'] for s in sigs] == ['TEILVERKAUF_LADDER', 'TEILVERKAUF_1']
    ms = messages(directory)
    assert [m['kind'] for m in ms] == ['e41', 'signal', 'signal']
    return c


def test_real_e41_precedes_two_real_signals_and_confirmation_keeps_order():
    sent = []
    def sender(text, *args): sent.append(text); return confirmed(text, *args)
    with tempfile.TemporaryDirectory() as temp, offline():
        d = Path(temp); c = multi(d, sender)
        assert sent == [m['text'] for m in messages(d)] and 'WARTET' in sent[0]
        with patch.object(main, 'deliver_telegram', side_effect=sender):
            main.run_engine(fetch=lambda old: ([c], [], []), data_dir=d)
        assert len(sent) == 3


def test_middle_rejection_preserves_order_and_retries_only_remaining_messages():
    sent = []
    def sender(text, *args):
        sent.append(text)
        return rejected(text, *args) if len(sent) == 2 else confirmed(text, *args)
    with tempfile.TemporaryDirectory() as temp, offline():
        d = Path(temp); c = multi(d, sender)
        assert [m['status'] for m in messages(d)] == ['confirmed', 'rejected', 'pending']
        with patch.object(main, 'deliver_telegram', side_effect=sender):
            main.run_engine(fetch=lambda old: ([c], [], []), data_dir=d)
        assert len(sent) == 4 and sent[1] == sent[2]
        assert [m['status'] for m in messages(d)] == ['confirmed']*3


def test_uncertain_middle_blocks_following_messages():
    sent = []
    def sender(text, *args):
        sent.append(text)
        if len(sent) == 2: raise TimeoutError()
        return confirmed(text, *args)
    with tempfile.TemporaryDirectory() as temp, offline():
        d = Path(temp); c = multi(d, sender)
        with patch.object(main, 'deliver_telegram', side_effect=sender):
            main.run_engine(fetch=lambda old: ([c], [], []), data_dir=d)
        assert len(sent) == 2 and [m['status'] for m in messages(d)] == ['confirmed', 'uncertain', 'pending']


def test_preview_and_plan_are_persisted_before_transport():
    from test_main import _vorschau_kerzen
    from strategy_core import FlowPoint
    cs = _vorschau_kerzen(); fl = [FlowPoint(c.ts, 1000+i*10, 0, 1e9, -.0001) for i,c in enumerate(cs)]
    with tempfile.TemporaryDirectory() as temp, offline():
        d = Path(temp); (d/'config.json').write_text(json.dumps(dict(pivot_n=2)))
        def sender(text, *args):
            assert any(m['text'] == text and m['status'] == 'sending' for m in messages(d))
            return confirmed(text, *args)
        with patch.object(main, 'deliver_telegram', side_effect=sender):
            main.run_engine(fetch=lambda old: (cs, fl, []), data_dir=d)
        assert any(m['kind'] == 'vorschau' for m in messages(d))
        assert all(m['status'] == 'confirmed' for m in messages(d))
        # Independently reach an active plan in the real buy scenario.
        d2 = d/'plan'; d2.mkdir(); (d2/'config.json').write_text('{}')
        with patch.object(main, 'deliver_telegram', side_effect=confirmed): run(d2)
        assert any(m['kind'] == 'plan' for m in messages(d2))


def test_flush_resolution_commit_and_projection_recovery_do_not_duplicate():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram', side_effect=confirmed):
        d = Path(temp); setup(d)
        stamp = szenario()[0][-1].ts
        w = dict(gewarnt_ts=stamp, aufgeloest=False, preis=105, invalidation=100, ts=stamp, grund='offline')
        (d/'watch.json').write_text(json.dumps(w))
        run(d)
        assert json.loads((d/'watch.json').read_text())['aufgeloest']
        assert any(m['kind'] == 'flush_aufloesung' for m in messages(d))
        count = len(messages(d)); (d/'watch.json').write_text(json.dumps(w)); run(d)
        assert len(messages(d)) == count and json.loads((d/'watch.json').read_text())['aufgeloest']
        newer = {**w, 'gewarnt_ts': stamp+14400000}
        (d/'watch.json').write_text(json.dumps(newer)); run(d)
        assert not json.loads((d/'watch.json').read_text())['aufgeloest']


def test_legacy_active_state_and_history_are_not_replayed_or_reset():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram') as sender:
        d = Path(temp); setup(d)
        cs, fl, oi = szenario(); p = Position()
        for i in range(len(cs)): main.evaluate(cs[:i+1], fl[:i+1], p, **main.eval_params({}))
        legacy = main.pos_to_state(p); legacy.pop('position_schema_version', None)
        old = dict(signals=[dict(ts=cs[-1].ts, type='KAUF_1', price=105)])
        (d/'state.json').write_text(json.dumps(legacy)); (d/'signals.json').write_text(json.dumps(old))
        run(d)
        assert sender.call_count == 0 and messages(d) == []
        assert read(d)['pos_state'] == 'T1' and read(d)['last_signal_ts'] == p.last_signal_ts
        assert read(d)['_delivery']['signals'] == old


def test_invalid_schema_stops_before_transport_or_state_overwrite():
    with tempfile.TemporaryDirectory() as temp, offline(False):
        d = Path(temp); setup(d); run(d); s = read(d); s['_delivery']['version'] = 99
        (d/'state.json').write_text(json.dumps(s)); before = (d/'state.json').read_bytes()
        with offline(), patch.object(main, 'deliver_telegram') as sender:
            expect(ValueError, lambda: run(d)); assert sender.call_count == 0
        assert (d/'state.json').read_bytes() == before


def test_corrupt_identity_duplicate_and_missing_receipt_are_rejected():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram', side_effect=confirmed):
        d = Path(temp); setup(d); run(d); s = read(d)
        for modify in [lambda x: x['_delivery']['messages'][0].update(id='bad'),
                       lambda x: x['_delivery']['messages'].append(deepcopy(x['_delivery']['messages'][0])),
                       lambda x: x['_delivery']['messages'][0].update(receipt=None),
                       lambda x: x['_delivery'].pop('signals')]:
            bad = deepcopy(s); modify(bad); expect(ValueError, lambda: box.load_delivery(bad))


def test_transport_requires_ok_and_message_id():
    assert transport(dict(ok=True, result=dict(message_id=42))) == dict(status='confirmed', message_id=42)
    for body in [dict(ok=True), dict(ok=True,result=dict(message_id=True)), dict(ok=True,result=dict(message_id=0)), []]:
        assert transport(body)['status'] == 'uncertain'


def test_main_rejection_and_restart_reach_real_transport_parser():
    with tempfile.TemporaryDirectory() as temp, offline():
        d = Path(temp); setup(d)
        with patch.object(tg.urllib.request, 'urlopen', return_value=Response(dict(ok=False,error_code=429))) as request:
            assert len(run(d)) == 1 and request.call_count == 1
        assert messages(d)[0]['status'] == 'rejected'
        with patch.object(tg.urllib.request, 'urlopen', return_value=Response(dict(ok=True,result=dict(message_id=77)))) as request:
            assert run(d) == [] and request.call_count == 1
        assert messages(d)[0]['receipt'] == 77


def test_state_projection_damage_is_repaired_from_canonical_history_and_oi():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram', side_effect=confirmed):
        d = Path(temp); setup(d); run(d)
        original = read(d)['_delivery']
        (d/'signals.json').write_text('{broken'); (d/'oi_history.json').write_text('[999]')
        main.run_engine(fetch=lambda old: ([], [], []), data_dir=d)
        assert json.loads((d/'signals.json').read_text()) == original['signals']
        assert json.loads((d/'oi_history.json').read_text()) == original['oi_history']


def test_text_tampering_and_invalid_projection_stop_before_send():
    with tempfile.TemporaryDirectory() as temp, offline(False):
        d = Path(temp); setup(d); run(d); good = read(d)
        for modify in [lambda s: s['_delivery']['messages'][0].update(text='changed'),
                       lambda s: s['_delivery'].update(signals=[]),
                       lambda s: s['_delivery'].update(oi_history={}),
                       lambda s: s['_delivery']['messages'].append('bad')]:
            bad = deepcopy(good); modify(bad)
            (d/'state.json').write_text(json.dumps(bad))
            with offline(), patch.object(main, 'deliver_telegram') as sender:
                expect(ValueError, lambda: run(d)); assert sender.call_count == 0


def test_transport_explicit_rejection_and_server_failure_are_distinguished():
    assert transport(dict(ok=False, error_code=429))['status'] == 'rejected'
    assert transport(dict(ok=False, error_code=500))['status'] == 'uncertain'
    assert transport(dict(ok=False))['status'] == 'uncertain'


def test_http_error_requires_explicit_client_rejection():
    for code, body, expected in [(400, dict(ok=False,error_code=400), 'rejected'),
                                 (500, dict(ok=False,error_code=500), 'uncertain'),
                                 (403, {}, 'uncertain')]:
        error = urllib.error.HTTPError('https://fake/F13_FAKE_TOKEN', code, 'offline', {}, Response(body))
        with offline(), patch.object(tg.urllib.request, 'urlopen', side_effect=error):
            assert tg.deliver_telegram('test','FAKE','FAKE')['status'] == expected


def test_malformed_response_and_urlerror_are_uncertain_and_secret_free():
    with offline() as output:
        for error in [TimeoutError('F13_FAKE_TOKEN'), urllib.error.URLError('F13_FAKE_TOKEN')]:
            with patch.object(tg.urllib.request, 'urlopen', side_effect=error):
                assert tg.deliver_telegram('test','FAKE','FAKE')['status'] == 'uncertain'
        with patch.object(tg.urllib.request, 'urlopen', return_value=io.BytesIO(b'{bad')):
            assert tg.deliver_telegram('test','FAKE','FAKE')['status'] == 'uncertain'
        assert 'F13_FAKE_TOKEN' not in output.getvalue()


def test_legacy_boolean_sender_cannot_forge_confirmation():
    with tempfile.TemporaryDirectory() as temp, offline(), patch.object(main, 'deliver_telegram', return_value=True):
        d = Path(temp); setup(d); run(d)
        assert messages(d)[0]['status'] == 'uncertain' and messages(d)[0]['receipt'] is None


def worker(mode, directory):
    d = Path(directory)
    with offline():
        atomic = box.atomic_json
        def commit(path, value):
            if Path(path).name == 'state.json':
                statuses = [m['status'] for m in value['_delivery']['messages']]
                if mode == 'before_commit' and statuses == ['pending']: os._exit(71)
                atomic(path, value)
                if mode == 'after_commit' and statuses == ['pending']: os._exit(72)
                if mode == 'before_send' and statuses == ['sending']: os._exit(73)
                if mode == 'after_receipt' and statuses == ['confirmed']: os._exit(75)
                return
            atomic(path, value)
        def sender(text, *args):
            with (d/'accepted.log').open('a') as f: f.write('accepted\n'); f.flush(); os.fsync(f.fileno())
            if mode == 'after_acceptance': os._exit(74)
            return confirmed(text, *args)
        with patch.object(box, 'atomic_json', side_effect=commit), patch.object(main, 'deliver_telegram', side_effect=sender):
            run(d)


def crash_case(mode, status, accepted, expected_after):
    with tempfile.TemporaryDirectory() as temp, offline():
        d = Path(temp); setup(d)
        proc = subprocess.run([sys.executable, __file__, '--worker', mode, str(d)], capture_output=True)
        assert proc.returncode in {71,72,73,74,75}, proc.stderr.decode()
        assert (messages(d)[0]['status'] if (d/'state.json').exists() else None) == status
        assert ((d/'accepted.log').read_text().count('accepted') if (d/'accepted.log').exists() else 0) == accepted
        with patch.object(main, 'deliver_telegram', side_effect=confirmed) as sender:
            result = run(d)
            assert sender.call_count == expected_after
        assert len(result) == (1 if status is None else 0)
        assert messages(d)[0]['status'] == ('uncertain' if status == 'sending' else 'confirmed')


def test_process_crash_before_commit_restarts_real_buy(): crash_case('before_commit', None, 0, 1)
def test_process_crash_after_commit_keeps_pending_without_replay(): crash_case('after_commit', 'pending', 0, 1)
def test_process_crash_after_sending_before_call_is_conservatively_uncertain(): crash_case('before_send', 'sending', 0, 0)
def test_process_crash_after_acceptance_cannot_duplicate(): crash_case('after_acceptance', 'sending', 1, 0)
def test_process_crash_after_receipt_remains_confirmed(): crash_case('after_receipt', 'confirmed', 1, 0)


def test_concurrent_process_cannot_enter_locked_engine_and_lock_survives_release():
    with tempfile.TemporaryDirectory() as temp, offline():
        d = Path(temp); setup(d)
        with box.engine_lock(d):
            proc = subprocess.run([sys.executable, __file__, '--worker', 'normal', str(d)], capture_output=True)
        assert proc.returncode != 0 and b'bereits in Bearbeitung' in proc.stderr, (proc.returncode, proc.stderr)
        assert not (d/'state.json').exists()
        with patch.object(main, 'deliver_telegram', side_effect=confirmed): run(d)
        assert messages(d)[0]['status'] == 'confirmed'


if __name__ == '__main__' and len(sys.argv) > 1:
    worker(sys.argv[2], sys.argv[3])
