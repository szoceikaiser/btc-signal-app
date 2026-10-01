"""A2 counterexamples use independent expected timestamps and arithmetic."""

from dataclasses import asdict, replace

import backtest
from execution_v1 import Decision
import strategy_core as sc
from flow_contract import FOUR_HOURS_MS as STEP
from test_backtest import _rohkerzen_kurs
from test_main import _e434_live_flow


def test_a2_f06_constant_offsets_do_not_change_default_pattern():
    candles = [sc.Candle(i * STEP, 100 + i, 101 + i, 99 + i, 100 + i)
               for i in range(12)]
    flow = [sc.FlowPoint(i * STEP, 100000 + i * 10, 100 + i * 30,
                         100 + i * .4, .00001 + i * .000001)
            for i in range(12)]
    baseline = sc.classify_pattern(candles, flow)
    assert baseline == sc.Pattern.DERIVATE_PUMP
    for spot_offset, fut_offset in ((0, 1e6), (1e9, 0), (-1e9, -1e6)):
        shifted = [replace(p, spot_cvd=p.spot_cvd + spot_offset,
                           fut_cvd=p.fut_cvd + fut_offset) for p in flow]
        assert sc.classify_pattern(candles, shifted) == baseline


def test_a2_f07_prefix_first_oi_and_stale_age_live_backtest():
    raw = _rohkerzen_kurs([100.0] * 7, start=0)
    oi = {2 * STEP: 500.0}
    for end in range(1, len(raw) + 1):
        _cs, bt = backtest.build_series(raw[:end], [], oi, end_ms=end * STEP)
        assert len(bt) == end
        expected = [0.0 if i < 2 else 500.0 for i in range(end)]
        assert [p.oi for p in bt] == expected
        assert [p.provenance["oi"]["coverage"] for p in bt] == [
            "missing" if i < 2 else "observed" if i == 2 else
            "carried" if i <= 4 else "stale" for i in range(end)]
        assert [p.provenance["oi"]["age_ms"] for p in bt] == [
            None if i < 2 else (i - 2) * STEP for i in range(end)]
    live = _e434_live_flow(raw, oi)
    assert [(p.oi, p.provenance["oi"]) for p in live] == [
        (p.oi, p.provenance["oi"]) for p in bt]
    assert all(p.provenance["oi"]["available_ts"] <= p.ts + STEP
               for p in bt if p.provenance["oi"]["available_ts"] is not None)


def test_a2_d02_observed_zero_missing_and_stale_funding():
    raw = _rohkerzen_kurs([100.0] * 5, start=0)
    _cs, missing = backtest.build_series(raw, [], end_ms=5 * STEP)
    _cs, zero = backtest.build_series(raw, [(STEP, 0.0)], end_ms=5 * STEP)
    missing = [replace(p, spot_cvd=0.0) for p in missing]
    zero = [replace(p, spot_cvd=0.0) for p in zero]
    assert missing[0].funding == zero[0].funding == 0.0
    assert missing[0].provenance["funding"]["coverage"] == "missing"
    assert zero[0].provenance["funding"]["coverage"] == "observed"
    assert zero[1].provenance["funding"]["coverage"] == "carried"
    assert zero[3].provenance["funding"]["coverage"] == "stale"
    assert not sc.confirm_ok(sc.Pattern.NEUTRAL, missing[:1], True)
    assert sc.confirm_ok(sc.Pattern.NEUTRAL, zero[:1], True)
    assert not sc.confirm_ok(sc.Pattern.NEUTRAL, zero[:4], True)


def test_a2_restart_preserves_field_provenance_and_gate():
    raw = _rohkerzen_kurs([100.0] * 5, start=0)
    _cs, flow = backtest.build_series(raw, [(STEP, 0.0)], {2 * STEP: 500.0},
                                       end_ms=5 * STEP)
    flow = [replace(p, spot_cvd=0.0) for p in flow]
    restored = [sc.FlowPoint(**asdict(p)) for p in flow]
    assert restored == flow
    for seq in (flow, restored):
        assert seq[0].provenance["oi"]["coverage"] == "missing"
        assert seq[-1].provenance["oi"]["coverage"] == "carried"
        assert seq[-1].provenance["funding"]["coverage"] == "stale"
        assert not sc.confirm_ok(sc.Pattern.NEUTRAL, seq, True)


def test_a2_legacy_checkpoint_without_evidence_cannot_confirm():
    original = Decision([], sc.Position(), sc.Position(), sc.Position(), [],
                        [sc.FlowPoint(0, 0, 0, 0, 0)], {})
    old_state = original.to_state()
    del old_state["flow"][0]["provenance"]
    restored = Decision.from_state(old_state)
    assert restored.flow[0].provenance["funding"]["coverage"] == "missing"
    assert not sc.confirm_ok(sc.Pattern.NEUTRAL, restored.flow, True)
