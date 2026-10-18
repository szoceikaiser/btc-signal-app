"""D01: feste UTC-Grenzen; Erwartungen aus vier Stunden, ohne Produktionshelfer."""
from unittest.mock import patch
from datetime import datetime, timezone
import backtest as bt
from strategy_core import Candle, FlowPoint

OPEN = int(datetime(2026, 9, 27, 8, tzinfo=timezone.utc).timestamp() * 1000)
CLOSE = int(datetime(2026, 9, 27, 12, tzinfo=timezone.utc).timestamp() * 1000)


def raw(ts, delta=10):
    return [ts, '100', '110', '90', '105', '1', ts + 14400000 - 1,
            '100', 1, '1', str((100 + delta) / 2), '0']


def at(cutoff, rows):
    with patch.object(bt, 'END_MS', cutoff):
        return bt.build_series(rows, [(CLOSE, .123), (CLOSE + 1, .999)],
                               {OPEN: 210}, {OPEN: (3, 4)}, {OPEN: 7}, {OPEN: 60})


def test_before_close_excludes_unfinished_and_all_associated_values():
    cs, fl = at(CLOSE - 1, [raw(OPEN - 14400000, 2), raw(OPEN, 1000)])
    assert [c.ts for c in cs] == [OPEN - 14400000]
    assert [f.ts for f in fl] == [OPEN - 14400000]
    assert fl[-1].spot_cvd == 2 and fl[-1].fut_cvd == 0
    assert fl[-1].funding == 0


def test_exact_close_includes_candle_and_boundary_funding():
    cs, fl = at(CLOSE, [raw(OPEN), raw(CLOSE)])
    assert [c.ts for c in cs] == [OPEN]
    assert [f.ts for f in fl] == [OPEN]
    assert (fl[0].spot_cvd, fl[0].fut_cvd, fl[0].oi, fl[0].funding) == (10, 7, 210, .123)
    assert fl[0].oi_btc == 2
    assert (fl[0].long_liq, fl[0].short_liq, fl[0].long_pct) == (3, 4, 60)


def test_after_close_still_excludes_next_candle():
    cs, fl = at(CLOSE + 1, [raw(OPEN), raw(CLOSE)])
    assert [c.ts for c in cs] == [OPEN] and [f.ts for f in fl] == [OPEN]


def test_without_closed_candle_returns_two_empty_series():
    assert at(CLOSE - 1, [raw(OPEN)]) == ([], [])


def test_fetch_filters_api_inclusive_close_timestamp():
    # Binance closeTime = Ende - 1 ms, kein bereits vollendetes Intervall.
    rows = [raw(OPEN)]
    with patch.object(bt, '_get_json', return_value=rows):
        assert bt.fetch_candles_range(OPEN, CLOSE - 1) == []
        assert bt.fetch_candles_range(OPEN, CLOSE) == rows


def test_utc_offset_represents_same_instant():
    local = datetime.fromisoformat('2026-09-27T14:00:00+02:00')
    assert int(local.timestamp() * 1000) == CLOSE
    assert [c.ts for c in at(int(local.timestamp() * 1000), [raw(OPEN)])[0]] == [OPEN]


def test_saved_cutoff_wins_over_today_and_preserves_inputs():
    cs = [Candle(OPEN, 100, 110, 90, 105), Candle(CLOSE, 100, 110, 90, 999)]
    fl = [FlowPoint(c.ts, 0, 0, 1, 0) for c in cs]
    with patch.object(bt.time, 'time', return_value=9999999999):
        kept, aligned = bt.closed_series(cs, fl, end_ms=CLOSE)
    assert kept == cs[:1] and aligned == fl[:1]
    assert len(cs) == len(fl) == 2 and cs[-1].close == 999
    assert bt.closed_series(cs, fl, end_ms=CLOSE - 1) == ([], [])


def test_saved_series_rejects_misaligned_timestamps():
    cs = [Candle(OPEN, 100, 110, 90, 105)]
    for fl in ([], [FlowPoint(CLOSE, 0, 0, 1, 0)]):
        try:
            bt.closed_series(cs, fl, end_ms=CLOSE)
        except ValueError:
            pass
        else:
            assert False, 'Zeitlich falsche Zuordnung muss scheitern'


def test_explicit_saved_raw_cutoff_and_zero():
    with patch.object(bt, 'END_MS', CLOSE + 999999999):
        cs, fl = bt.build_series([raw(OPEN), raw(CLOSE)], [], end_ms=CLOSE)
        assert [c.ts for c in cs] == [OPEN] and [f.ts for f in fl] == [OPEN]
        assert bt.build_series([raw(0)], [], end_ms=0) == ([], [])


def test_half_uses_close_not_open_and_empty_is_explicit():
    cs = [Candle(OPEN, 100, 110, 90, 105), Candle(CLOSE, 100, 110, 90, 999)]
    fl = [FlowPoint(c.ts, 0, 0, 1, 0) for c in cs]
    with patch.object(bt, 'run_backtest', return_value=[]) as run, \
            patch.object(bt, 'simulate', return_value={'ende': 10000}) as sim:
        assert bt.run_half(cs, fl, {}, OPEN, end_ms=CLOSE - 1) == ([], None)
        run.assert_not_called()
        bt.run_half(cs, fl, {}, OPEN, end_ms=CLOSE)
        assert run.call_args.args[:2] == (cs[:1], fl[:1])
        assert sim.call_args.args[1] == cs[:1]


def test_coinalyze_seconds_are_converted_to_open_milliseconds():
    import coinalyze
    answer = [{'symbol': coinalyze.SYMBOL, 'history': [{'t': OPEN // 1000, 'c': 210}]}]
    with patch.object(coinalyze, 'fetch_history', return_value=answer):
        oi = coinalyze.oi_by_ts('offline')
    assert oi == {OPEN: 210}
    cs, fl = bt.build_series([raw(OPEN)], [], oi_map=oi, end_ms=CLOSE)
    assert len(cs) == len(fl) == 1
    assert cs[0].ts == fl[0].ts == OPEN and fl[0].oi_btc == 2
