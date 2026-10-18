"""A6 reached counterexample for E41 ordering, including a partial sale."""
import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import main
import derivative_accounting as accounting
import strategy_core as core
from strategy_core import Candle, Impulse, Pivot, PosState, Position, fib_zones


def test_a6_v1_rejects_explicit_perpetual_before_replay():
    try:
        accounting.require_spot_config({'instrument': accounting.PERP,
                                        'bias_short': False, 'leverage': 1})
    except accounting.NotEvaluable as exc:
        assert 'Long/Spot only' in str(exc)
    else:
        raise AssertionError('Explicit perpetual accepted by the V1/i+2 gate')


def test_a6_e41_never_applies_waiting_rule_to_trailed_stop():
    from test_strategy_core import _m5_lage, _signale
    candles, flow = _m5_lage()
    original_resolve = core.resolve_stop
    original_decision = core.stop_entscheidung
    current = {'note': None, 'trailed': 0}

    def resolve(*args, **kwargs):
        result = original_resolve(*args, **kwargs)
        current['note'] = result[1]
        if result[1] not in ('', 'Invalidierung'):
            current['trailed'] += 1
        return result

    def decision(*args, **kwargs):
        assert current['note'] in ('', 'Invalidierung'), current['note']
        return original_decision(*args, **kwargs)

    with patch.object(core, 'resolve_stop', side_effect=resolve), \
         patch.object(core, 'stop_entscheidung', side_effect=decision):
        _signale(candles, flow, trail_stop=True, stop_rueckeroberung=1)
    assert current['trailed'] > 0, 'No trailed stop reached in the control'


def test_a6_missing_btc_oi_does_not_create_movement():
    flow = [core.FlowPoint(i, 0, 0, 0, 0, oi_btc=0) for i in range(2)]
    try:
        change = core.oi_aenderung(flow, 'btc')
    except ZeroDivisionError as exc:
        raise AssertionError('Missing BTC OI reached the division branch') from exc
    assert change == 0.0


def test_a6_cvd_window_dollars_ignore_arbitrary_start():
    from dataclasses import replace
    step = 14_400_000
    candles = [core.Candle(i * step, 100, 101, 99, 100) for i in range(12)]
    flow = [core.FlowPoint(i * step, 1_000 + i * 10, i * 20, 100, 0)
            for i in range(12)]
    baseline = core._muster2_dollar(candles, flow)
    shifted = core._muster2_dollar(
        candles, [replace(p, spot_cvd=p.spot_cvd + 1_000_000) for p in flow])
    assert baseline == shifted == (110.0, 22_000.0)


def test_a6_e41_waiting_precedes_partial_sale_in_same_candle():
    zones = fib_zones(Impulse(Pivot(0, 0, 80, 'L'),
                              Pivot(1, 14400000, 160, 'H')))
    pos = Position(direction='LONG', state=PosState.CORE, zones=zones,
                   retrace_extreme=100, entry_ref=110, entry_pct=75,
                   bestand_pct=75, last_signal_ts=14400000)
    candle = Candle(28800000, 120, 170, 79, 79.5)
    config = dict(plan_telegram=False, vorschau_telegram=False,
                  stop_rueckeroberung=1, buy_ladder=False, trail_stop=False,
                  high_exit='off', bias_short=False, rest_halten=True)
    with tempfile.TemporaryDirectory(prefix='a6-e41-') as tmp:
        dest = Path(tmp)
        (dest / 'config.json').write_text(json.dumps(config), encoding='utf-8')
        (dest / 'state.json').write_text(json.dumps(main.pos_to_state(pos)),
                                         encoding='utf-8')
        with patch.object(main.urllib.request, 'urlopen',
                          side_effect=AssertionError('network forbidden')), \
             redirect_stdout(StringIO()):
            signals = main.run_engine(fetch=lambda old: ([candle], [], []),
                                      data_dir=dest, dry_run=True)
        state = json.loads((dest / 'state.json').read_text(encoding='utf-8'))
    messages = state['_delivery']['messages']
    events = [(m['kind'], m['event']) for m in messages]
    assert any(s['type'] == 'TEILVERKAUF_LADDER' for s in signals), signals
    assert any(m['kind'] == 'e41' for m in messages), events
    wait = next(i for i, m in enumerate(messages) if m['kind'] == 'e41')
    partial = next(i for i, m in enumerate(messages)
                   if m['kind'] == 'signal' and
                   m['payload']['type'] == 'TEILVERKAUF_LADDER')
    assert messages[wait]['event'] == messages[partial]['event']
    assert wait < partial, events
