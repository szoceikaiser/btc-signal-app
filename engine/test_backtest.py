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


def test_score_fehltreffer_druecken_praezision():
    sigs = [
        {"ts": _ts("2025-12-25"), "type": "KAUF_1"},     # weit weg von allen Terminen
        {"ts": _ts("2026-01-08"), "type": "KAUF_2"},     # Treffer
    ]
    sc = backtest.score(sigs)
    assert sc["precision"] == 0.5
