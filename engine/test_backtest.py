"""Offline-Tests fuer die Backtest-Auswertung (kein Netz noetig)."""

from datetime import datetime, timezone

import backtest


def _ts(iso: str) -> int:
    return int(datetime.fromisoformat(iso + "T00:00:00+00:00").timestamp() * 1000)


def test_score_trifft_mit_toleranz():
    sigs = [
        {"ts": _ts("2025-09-24"), "type": "KAUF_1"},     # ±1 Tag zu Kauf 25.09.
        {"ts": _ts("2026-01-08"), "type": "KAUF_2"},     # exakt Kauf 08.01.
        {"ts": _ts("2026-01-14"), "type": "TEILVERKAUF_1"},  # exakt Verkauf 14.01.
        {"ts": _ts("2025-10-16"), "type": "STOPLOSS"},   # exakt Verkauf 16.10.
    ]
    sc = backtest.score(sigs)
    from datetime import date
    assert date(2025, 9, 25) in sc["hit_k"]
    assert date(2026, 1, 8) in sc["hit_k"]
    assert date(2026, 1, 14) in sc["hit_v"]
    assert date(2025, 10, 16) in sc["hit_v"]
    assert sc["precision"] == 1.0                        # alle Engine-Tage nahe Terminen


def test_score_short_zuordnung():
    # Short eroeffnen zaehlt als Verkauf-Handlung, Short decken als Kauf-Handlung
    sigs = [
        {"ts": _ts("2026-04-22"), "type": "SHORT_2"},        # Verkauf 22.04.
        {"ts": _ts("2026-02-28"), "type": "SHORT_COVER_REST"},  # Kauf 28.02.
    ]
    sc = backtest.score(sigs)
    from datetime import date
    assert date(2026, 4, 22) in sc["hit_v"]
    assert date(2026, 2, 28) in sc["hit_k"]


def test_simulate_long_zyklus_ohne_gebuehr():
    from strategy_core import Candle
    sigs = [
        {"ts": 1, "type": "KAUF_1", "price": 100.0, "tranche_pct": 25},
        {"ts": 2, "type": "KAUF_2", "price": 95.0, "tranche_pct": 50},
        {"ts": 3, "type": "TEILVERKAUF_1", "price": 110.0, "tranche_pct": 40},
        {"ts": 4, "type": "TEILVERKAUF_2", "price": 120.0, "tranche_pct": 40},
        {"ts": 5, "type": "VERKAUF_REST", "price": 115.0, "tranche_pct": 20},
    ]
    candles = [Candle(backtest.START_MS, 100, 100, 100, 100),
               Candle(backtest.START_MS + 1, 115, 115, 115, 115)]
    pnl = backtest.simulate(sigs, candles, fee=0.0)
    # 2500@100 + 5000@95 = 77.63 Einheiten; Verkaeufe 40%/40%/Rest der Spitze
    assert abs(pnl["ende"] - 11427.4) < 1.0
    assert pnl["trades"] == 3 and pnl["gewinn_trades"] == 3
    assert pnl["offene_position"] == 0.0


def test_simulate_stoploss_verlust():
    from strategy_core import Candle
    sigs = [
        {"ts": 1, "type": "KAUF_1", "price": 100.0, "tranche_pct": 25},
        {"ts": 2, "type": "STOPLOSS", "price": 90.0, "tranche_pct": 100},
    ]
    candles = [Candle(backtest.START_MS, 100, 100, 100, 100),
               Candle(backtest.START_MS + 1, 90, 90, 90, 90)]
    pnl = backtest.simulate(sigs, candles, fee=0.0)
    assert abs(pnl["ende"] - 9750.0) < 0.01           # 2500 -> 2250
    assert pnl["gewinn_trades"] == 0


def test_simulate_short_gewinn():
    from strategy_core import Candle
    sigs = [
        {"ts": 1, "type": "SHORT_2", "price": 100.0, "tranche_pct": 75},
        {"ts": 2, "type": "SHORT_COVER_REST", "price": 90.0, "tranche_pct": 100},
    ]
    candles = [Candle(backtest.START_MS, 100, 100, 100, 100),
               Candle(backtest.START_MS + 1, 90, 90, 90, 90)]
    pnl = backtest.simulate(sigs, candles, fee=0.0)
    # 7500 nominal short, 10 % Kursrueckgang -> +750
    assert abs(pnl["ende"] - 10750.0) < 0.01


def test_score_fehltreffer_druecken_praezision():
    sigs = [
        {"ts": _ts("2025-12-25"), "type": "KAUF_1"},     # weit weg von allen Terminen
        {"ts": _ts("2026-01-08"), "type": "KAUF_2"},     # Treffer
    ]
    sc = backtest.score(sigs)
    assert sc["precision"] == 0.5
