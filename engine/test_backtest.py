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


def test_monatsuebersicht_zerlegt_das_ergebnis():
    """Monatsuebersicht: Kontostand je Monatsende, Summe der Monatsgewinne muss dem
    Gesamtergebnis entsprechen."""
    from datetime import datetime, timezone
    from strategy_core import Candle
    H4 = 4 * 3600 * 1000
    start = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    # gut drei Monate Kerzen, Preis steigt von 100 auf 130
    n = 550
    candles = [Candle(start + i * H4, 100 + i * 30 / n, 100 + i * 30 / n,
                      100 + i * 30 / n, 100 + i * 30 / n) for i in range(n)]
    # Position bleibt bis zum Schluss OFFEN — so faellt auf, wenn der angeschnittene
    # letzte Monat in der Uebersicht fehlt (Fehler beim ersten Bau).
    sigs = [
        {"ts": candles[10].ts, "type": "KAUF_1", "price": candles[10].close, "tranche_pct": 100},
    ]
    pnl = backtest.simulate(sigs, candles, fee=0.0, start_ms=start)
    monate = pnl["monate"]
    assert [m["monat"] for m in monate] == ["2026-01", "2026-02", "2026-03", "2026-04"]
    # Die Monatsgewinne summieren sich auf das Gesamtergebnis — inklusive Restmonat
    summe = sum(m["gewinn"] for m in monate)
    assert abs(summe - (pnl["ende"] - pnl["start"])) < 1.0
    # Bei steigendem Kurs und Long-Position ist kein Monat im Minus
    assert all(m["gewinn"] >= -0.01 for m in monate)
    # Der Kontostand des letzten Monats ist das Gesamtergebnis
    assert abs(monate[-1]["ende"] - pnl["ende"]) < 0.01


def test_run_half_schneidet_haelfte_1_hinten_ab():
    """E11: Mit end_ms werden nur Kerzen bis zu diesem Zeitpunkt ausgewertet."""
    from strategy_core import Candle
    H4 = 4 * 3600 * 1000
    candles = [Candle(backtest.START_MS + i * H4, 100, 101, 99, 100) for i in range(20)]
    flow = []
    from strategy_core import FlowPoint
    flow = [FlowPoint(c.ts, 0.0, 0.0, 1000.0, 0.0) for c in candles]
    mitte = candles[9].ts
    cfg = dict(bias_long=True, bias_short=False, pivot_n=5, k_atr=2.0)
    _s1, p1 = backtest.run_half(candles, flow, cfg, backtest.START_MS, end_ms=mitte)
    _s2, p2 = backtest.run_half(candles, flow, cfg, mitte)
    # Beide Haelften liefern ein Ergebnis, keine wirft
    assert p1 is not None and p2 is not None
    assert "rendite_pct" in p1 and "rendite_pct" in p2
    # Leeres Fenster (end_ms vor der ersten Kerze) -> sauberer Rueckfall
    leer_s, leer_p = backtest.run_half(candles, flow, cfg, backtest.START_MS,
                                       end_ms=backtest.START_MS - 1)
    assert leer_s == [] and leer_p is None


def test_deploy_pct_haelt_reserve_zurueck():
    """Furkan-Update: 'Pulver behalten'. Mit 50 % Einsatz wird je Tranche nur die
    Haelfte investiert — und am Ende ist entsprechend Bargeld uebrig."""
    from strategy_core import Candle
    sigs = [{"ts": 1, "type": "KAUF_1", "price": 100.0, "tranche_pct": 25}]
    candles = [Candle(backtest.START_MS, 100, 100, 100, 100),
               Candle(backtest.START_MS + 1, 100, 100, 100, 100)]
    voll = backtest.simulate(sigs, candles, fee=0.0, deploy_pct=1.0)
    halb = backtest.simulate(sigs, candles, fee=0.0, deploy_pct=0.5)
    # 25 % von 10.000 = 2.500 investiert vs. 25 % von 5.000 = 1.250
    assert abs(voll["offene_position"] - 2500.0) < 0.01
    assert abs(halb["offene_position"] - 1250.0) < 0.01
    assert halb["deploy_pct"] == 50


def test_reserve_laesst_geld_fuer_die_tiefere_tranche():
    """Der eigentliche Punkt: ohne Reserve fressen die ersten Tranchen das Kapital auf,
    die spaetere (guenstigere) Stufe geht leer aus. Mit Reserve kauft sie noch."""
    from strategy_core import Candle
    sigs = [
        {"ts": 1, "type": "KAUF_1", "price": 100.0, "tranche_pct": 25},
        {"ts": 2, "type": "KAUF_2", "price": 95.0, "tranche_pct": 50},
        {"ts": 3, "type": "NACHKAUF", "price": 90.0, "tranche_pct": 25},
        {"ts": 4, "type": "NACHKAUF", "price": 80.0, "tranche_pct": 15},   # tiefste Stufe
    ]
    candles = [Candle(backtest.START_MS, 100, 100, 100, 100),
               Candle(backtest.START_MS + 1, 80, 80, 80, 80)]
    voll = backtest.simulate(sigs, candles, fee=0.0, deploy_pct=1.0)
    reserve = backtest.simulate(sigs, candles, fee=0.0, deploy_pct=0.6)
    # Ohne Reserve ist die Kasse leer, bevor die 80er-Tranche kommt
    assert voll["ende"] < 10000.0
    # Mit Reserve bleibt Bargeld uebrig UND es wurde bei 80 noch gekauft
    assert reserve["offene_position"] > 0
    assert reserve["ende"] > voll["ende"]


def test_max_drawdown_wird_berechnet():
    from strategy_core import Candle
    sigs = [
        {"ts": 1, "type": "KAUF_1", "price": 100.0, "tranche_pct": 100},
        {"ts": 2, "type": "STOPLOSS", "price": 50.0, "tranche_pct": 100},
    ]
    candles = [Candle(backtest.START_MS, 100, 100, 100, 100),
               Candle(backtest.START_MS + 1, 50, 50, 50, 50)]
    pnl = backtest.simulate(sigs, candles, fee=0.0)
    assert pnl["max_drawdown_pct"] <= -49.0        # halbes Kapital weg
    assert pnl["max_drawdown_pct"] >= -51.0


def test_score_ignoriert_signale_nach_dem_letzten_trigger():
    """E9.9: Das Fenster laeuft jetzt bis heute, Kaisers Trigger enden aber im April.
    Signale danach duerfen die Praezision nicht druecken — es gibt keinen Maszstab."""
    from datetime import date, timedelta
    sigs = [
        {"ts": _ts("2026-01-08"), "type": "KAUF_2"},     # Treffer
        {"ts": _ts("2026-06-15"), "type": "KAUF_1"},     # nach dem letzten Trigger
        {"ts": _ts("2026-07-20"), "type": "STOPLOSS"},   # nach dem letzten Trigger
    ]
    sc = backtest.score(sigs)
    assert sc["precision"] == 1.0                        # nur der Januar-Tag wird gewertet
    assert sc["eval_end"] == date(2026, 4, 22) + timedelta(days=1)
    assert all(d <= sc["eval_end"] for d in sc["buy_days"] + sc["sell_days"])
