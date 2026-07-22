"""Offline-Tests fuer main.py (Orchestrierung, State-Persistenz, Dedupe).

Netzwerkzugriff wird durch eine Fake-Fetch-Funktion ersetzt.
"""

import json
import tempfile
from pathlib import Path

from strategy_core import Candle, FlowPoint
from main import pos_from_state, pos_to_state, run_engine

TS0 = 1_700_000_000_000
H4 = 4 * 3600 * 1000


def _c(i, o, h, l, cl):
    return Candle(TS0 + i * H4, o, h, l, cl)


def szenario():
    """Impuls 100->110 (Pivots mit n=5 bestaetigt), letzte Kerze beruehrt 0.5-Level."""
    rows = [
        (0, 103.5, 104.0, 103.0, 103.5), (1, 103.0, 103.5, 102.5, 103.0),
        (2, 102.6, 103.0, 102.2, 102.6), (3, 102.2, 102.6, 101.8, 102.2),
        (4, 101.8, 102.2, 101.5, 101.8), (5, 101.5, 102.0, 100.0, 101.0),
        (6, 101.5, 104.0, 101.0, 103.5), (7, 103.5, 105.0, 102.0, 104.0),
        (8, 104.0, 106.0, 103.0, 105.5), (9, 105.5, 107.0, 104.0, 106.5),
        (10, 106.5, 108.5, 105.0, 108.0), (11, 108.0, 109.5, 106.0, 109.0),
        (12, 109.0, 110.0, 107.0, 109.5), (13, 109.0, 109.0, 106.5, 107.5),
        (14, 107.5, 108.5, 106.2, 107.0), (15, 107.0, 108.0, 106.0, 106.5),
        (16, 106.5, 107.5, 105.8, 106.2), (17, 106.2, 107.0, 105.6, 106.0),
        (18, 106.0, 106.2, 104.5, 105.0),  # beruehrt 0.5 (105) -> KAUF 1
    ]
    candles = [_c(*r) for r in rows]
    flow = [FlowPoint(c.ts, 100.0, 100.0, 1000.0, 0.0) for c in candles]
    return candles, flow


def test_run_engine_erzeugt_signal_und_dateien():
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        sigs = run_engine(fetch=szenario, data_dir=data, dry_run=True)
        assert [s["type"] for s in sigs] == ["KAUF_1"]
        state = json.loads((data / "state.json").read_text())
        hist = json.loads((data / "signals.json").read_text())
        assert state["direction"] == "LONG" and state["pos_state"] == "T1"
        assert abs(state["zones"]["level_05"] - 105.0) < 0.01
        assert abs(state["zones"]["invalidation"] - 100.0) < 0.01
        assert "ext1" in state["zones"]
        assert len(hist["signals"]) == 1


def test_zweiter_lauf_ist_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        first = run_engine(fetch=szenario, data_dir=data, dry_run=True)
        second = run_engine(fetch=szenario, data_dir=data, dry_run=True)
        assert len(first) == 1 and second == []
        hist = json.loads((data / "signals.json").read_text())
        assert len(hist["signals"]) == 1                    # keine Duplikate


def test_state_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        run_engine(fetch=szenario, data_dir=data, dry_run=True)
        state = json.loads((data / "state.json").read_text())
        pos = pos_from_state(state)
        assert pos.direction == "LONG" and pos.zones is not None
        rt = pos_to_state(pos)
        assert abs(rt["zones"]["gp_upper"] - state["zones"]["gp_upper"]) < 1e-9


def test_demo_state_wird_verworfen():
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        (data / "state.json").write_text(json.dumps({"demo": True, "direction": "LONG"}))
        (data / "signals.json").write_text(json.dumps({"demo": True, "signals": [{"x": 1}]}))
        sigs = run_engine(fetch=szenario, data_dir=data, dry_run=True)
        hist = json.loads((data / "signals.json").read_text())
        assert [s["type"] for s in sigs] == ["KAUF_1"]
        assert len(hist["signals"]) == 1                    # Demo-Historie ersetzt
