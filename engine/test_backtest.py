"""Offline-Tests fuer die Backtest-Auswertung (kein Netz noetig)."""

from datetime import datetime, timezone

import backtest
from strategy_core import Candle


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


# ------------------------------------------------- E15: Furkans Termine als P&L

def _tageskerzen(preise, start_tag="2026-01-01"):
    """Eine 4h-Kerze je Tag (reicht: furkan_pnl nimmt den letzten Schluss des Tages)."""
    from datetime import datetime, timezone, timedelta
    t0 = datetime.fromisoformat(start_tag).replace(tzinfo=timezone.utc)
    return [Candle(int((t0 + timedelta(days=i)).timestamp() * 1000), p, p, p, p)
            for i, p in enumerate(preise)]


def test_furkan_pnl_rechnet_kauf_und_verkauf_korrekt():
    """Ein Kauf bei 100, ein Verkauf bei 200 mit voller Position = Verdopplung minus Gebuehr."""
    cs = _tageskerzen([100, 150, 200])
    r = backtest.furkan_pnl(cs, ["2026-01-01"], ["2026-01-03"],
                            kauf_pct=1.0, verkauf_pct=1.0, fee=0.0)
    assert r["kauftage"] == 1 and r["verkaufstage"] == 1
    assert abs(r["ende"] - 20000.0) < 1e-6, r
    assert abs(r["rendite_pct"] - 100.0) < 1e-6


def test_furkan_pnl_gebuehr_wird_abgezogen():
    cs = _tageskerzen([100, 200])
    ohne = backtest.furkan_pnl(cs, ["2026-01-01"], ["2026-01-02"], 1.0, 1.0, fee=0.0)
    mit = backtest.furkan_pnl(cs, ["2026-01-01"], ["2026-01-02"], 1.0, 1.0, fee=0.01)
    assert mit["ende"] < ohne["ende"]
    # 1 % beim Kauf und 1 % beim Verkauf -> ca. 2 % weniger
    assert abs(mit["ende"] - 20000 * 0.99 * 0.99) < 1.0, mit


def test_furkan_pnl_verkauf_ohne_position_tut_nichts():
    cs = _tageskerzen([100, 200])
    r = backtest.furkan_pnl(cs, [], ["2026-01-01", "2026-01-02"], 0.5, 0.5, fee=0.0)
    assert r["verkaufstage"] == 0 and abs(r["ende"] - 10000.0) < 1e-6


def test_furkan_pnl_rotationstag_verkauft_erst_dann_kauft():
    """Tag mit Kauf UND Verkauf: erst raus, dann rein (docs/GEGENCHECK.md).

    Andernfalls wuerde am selben Tag die gerade gekaufte Tranche sofort mitverkauft und
    das Ergebnis waere ein anderes — deshalb pruefen wir die Reihenfolge fest.
    """
    cs = _tageskerzen([100, 100])
    r = backtest.furkan_pnl(cs, ["2026-01-01", "2026-01-02"], ["2026-01-02"],
                            kauf_pct=1.0, verkauf_pct=1.0, fee=0.0)
    # Tag 1: alles rein (100 Einheiten). Tag 2: erst alles raus (10.000 Cash),
    # dann alles wieder rein -> am Ende wieder voll investiert, Wert unveraendert.
    assert abs(r["ende"] - 10000.0) < 1e-6, r
    assert r["kauftage"] == 2 and r["verkaufstage"] == 1


def test_furkan_pnl_fenster_wird_beachtet():
    cs = _tageskerzen([100, 100, 100, 500])
    ganz = backtest.furkan_pnl(cs, ["2026-01-01"], ["2026-01-04"], 1.0, 1.0, fee=0.0)
    # Fenster endet vor dem Verkaufstag -> Position bleibt offen, Bewertung zum Kurs
    kurz = backtest.furkan_pnl(cs, ["2026-01-01"], ["2026-01-04"], 1.0, 1.0, fee=0.0,
                               end_ms=cs[2].ts)
    assert abs(ganz["ende"] - 50000.0) < 1e-6
    assert abs(kurz["ende"] - 10000.0) < 1e-6, kurz


def test_furkan_pnl_ohne_kerzen_im_fenster_liefert_leer():
    cs = _tageskerzen([100, 100])
    assert backtest.furkan_pnl(cs, ["2026-01-01"], [], 1.0, 1.0,
                               start_ms=cs[-1].ts + 10**9) == {}


# ------------------------------------------------- E16: Futures-Daten im Backtest

def _rohkerzen(n=3, start=1_700_000_000_000):
    """Binance-Kerzenformat (nur die Felder, die build_series liest)."""
    ms = 4 * 3600 * 1000
    return [[start + i * ms, 100.0, 101.0, 99.0, 100.0, 10.0,
             start + (i + 1) * ms, 1000.0, 50, 0, 600.0] for i in range(n)]


def test_build_series_summiert_futures_delta_auf():
    """fut_map liefert das Delta JE KERZE — daraus muss ein kumuliertes CVD werden.

    Ohne die Aufsummierung waere fut_cvd eine zappelnde Einzelwert-Reihe statt einer
    Linie, und `_slope()` in classify_pattern wuerde etwas voellig anderes messen.
    """
    raw = _rohkerzen(3)
    ts = [int(k[0]) for k in raw]
    fut = {ts[0]: 10.0, ts[1]: -4.0, ts[2]: 6.0}
    _cs, flow = backtest.build_series(raw, [], {ts[0]: 1e9}, None, fut, None)
    assert [f.fut_cvd for f in flow] == [10.0, 6.0, 12.0], [f.fut_cvd for f in flow]


def test_build_series_ohne_futures_daten_bleibt_bei_null():
    """Rueckwaertskompatibel: ohne fut_map verhaelt sich alles wie vor E16."""
    raw = _rohkerzen(3)
    _cs, flow = backtest.build_series(raw, [], {int(raw[0][0]): 1e9}, None, None, None)
    assert all(f.fut_cvd == 0.0 for f in flow)
    assert all(f.long_pct == 0.0 for f in flow)


def test_build_series_uebernimmt_long_anteil():
    raw = _rohkerzen(2)
    ts = [int(k[0]) for k in raw]
    _cs, flow = backtest.build_series(raw, [], {ts[0]: 1e9}, None, None,
                                      {ts[0]: 65.12, ts[1]: 64.0})
    assert [f.long_pct for f in flow] == [65.12, 64.0]


# ------------------------------------------------- E17: Wert der Vorab-Order

def test_simulate_fill_close_nutzt_den_kerzenschluss():
    """fill='close' muss den Schlusskurs der ausloesenden Kerze nehmen, nicht den Level.

    Aufbau: Kauf zum Level 100, aber die Kerze schliesst bei 110. Wer vorab eine
    Limit-Order bei 100 liegen hatte, kauft billiger als jemand, der erst nach der
    Nachricht zum Schlusskurs kauft.
    """
    ms = 4 * 3600 * 1000
    t0 = 1_700_000_000_000
    cs = [Candle(t0, 100, 120, 95, 110), Candle(t0 + ms, 110, 130, 105, 120)]
    sig = [{"ts": t0, "type": "KAUF_2", "price": 100.0, "tranche_pct": 100},
           {"ts": t0 + ms, "type": "VERKAUF_REST", "price": 120.0, "tranche_pct": 100}]
    billig = backtest.simulate(sig, cs, fee=0.0, start_ms=t0, fill="level")
    teuer = backtest.simulate(sig, cs, fee=0.0, start_ms=t0, fill="close")
    # Level: fuer 10.000 bei 100 gekauft = 100 Stueck -> bei 120 verkauft = 12.000
    assert abs(billig["ende"] - 12000.0) < 1.0, billig
    # Kerzenschluss: bei 110 gekauft = 90,9 Stueck -> bei 120 verkauft = 10.909
    assert abs(teuer["ende"] - 10909.09) < 1.0, teuer
    assert billig["rendite_pct"] > teuer["rendite_pct"]


def test_simulate_fill_aendert_nichts_bei_kerzenschluss_signalen():
    """Stops und Restverkaeufe feuern ohnehin zum Schlusskurs — dort darf kein
    Unterschied entstehen, sonst misst der Vergleich das Falsche."""
    ms = 4 * 3600 * 1000
    t0 = 1_700_000_000_000
    cs = [Candle(t0, 100, 120, 95, 110), Candle(t0 + ms, 110, 130, 105, 120)]
    # beide Signale exakt zum jeweiligen Schlusskurs
    sig = [{"ts": t0, "type": "KAUF_2", "price": 110.0, "tranche_pct": 100},
           {"ts": t0 + ms, "type": "STOPLOSS", "price": 120.0, "tranche_pct": 100}]
    a = backtest.simulate(sig, cs, fee=0.0, start_ms=t0, fill="level")
    b = backtest.simulate(sig, cs, fee=0.0, start_ms=t0, fill="close")
    assert abs(a["ende"] - b["ende"]) < 1e-6, (a["ende"], b["ende"])


def test_simulate_fill_default_ist_level():
    """Rueckwaertskompatibel: ohne Angabe muss sich nichts aendern."""
    ms = 4 * 3600 * 1000
    t0 = 1_700_000_000_000
    cs = [Candle(t0, 100, 120, 95, 110), Candle(t0 + ms, 110, 130, 105, 120)]
    sig = [{"ts": t0, "type": "KAUF_2", "price": 100.0, "tranche_pct": 100}]
    assert backtest.simulate(sig, cs, fee=0.0, start_ms=t0)["ende"] == \
           backtest.simulate(sig, cs, fee=0.0, start_ms=t0, fill="level")["ende"]


def test_simulate_fill_close_faellt_auf_signalpreis_zurueck():
    """Kennt die Kerzenliste den Zeitstempel nicht, darf nichts abstuerzen."""
    t0 = 1_700_000_000_000
    cs = [Candle(t0, 100, 120, 95, 110)]
    sig = [{"ts": t0 + 999, "type": "KAUF_2", "price": 100.0, "tranche_pct": 100}]
    r = backtest.simulate(sig, cs, fee=0.0, start_ms=t0, fill="close")
    assert r["ende"] > 0


def test_panel_variante_entspricht_der_live_einstellung():
    """Das Chart-Panel muss zeigen, was die Engine WIRKLICH tut.

    Der Fehler, den dieser Test verhindert: Wird eine Einstellung in config.json live
    geschaltet, aber panel=True bleibt auf der alten Gitterzeile stehen, zeigt die
    Webseite eine Rendite, die die Engine nie erzielt hat. Bisher war das eine
    Merk-Regel im Kommentar (E9.5) — jetzt ist es geprueft.
    """
    import json
    from pathlib import Path
    import backtest
    import main
    cfg_datei = Path(__file__).resolve().parent.parent / "site" / "data" / "config.json"
    if not cfg_datei.exists():                     # ohne Repo-Daten nichts zu pruefen
        return
    cfg = {k: v for k, v in json.loads(cfg_datei.read_text(encoding="utf-8")).items()
           if not k.startswith("_")}
    live = main.eval_params(cfg)
    panel = [v for v in backtest.GRID if v.get("panel")]
    assert len(panel) == 1, f"genau eine Gitterzeile muss panel=True tragen, nicht {len(panel)}"
    im_panel = {k: panel[0][k] for k in backtest.EVAL_KEYS if k in panel[0]}
    abweichend = {k: (im_panel.get(k), live.get(k))
                  for k in set(im_panel) | set(live) if im_panel.get(k) != live.get(k)}
    assert not abweichend, f"Panel-Zeile weicht von config.json ab: {abweichend}"


# ---------------------------------------- E22: Beteiligung an der Marktbewegung

def test_beteiligung_rechnet_auf_und_abwaerts_getrennt():
    from backtest import beteiligung
    monate = [
        {"monat": "2026-01", "rendite_pct": +5.0, "btc_pct": +10.0},   # steigend
        {"monat": "2026-02", "rendite_pct": +1.0, "btc_pct": +10.0},   # steigend
        {"monat": "2026-03", "rendite_pct": -2.0, "btc_pct": -20.0},   # fallend
    ]
    b = beteiligung(monate)
    assert b["auf_monate"] == 2 and b["ab_monate"] == 1
    assert b["auf_btc"] == 20.0 and b["auf_engine"] == 6.0
    assert b["auf_pct"] == 30            # 6 von 20
    assert b["ab_pct"] == 10             # -2 von -20 -> 10 %
    # zu wenige Monate -> lieber nichts als eine Scheingenauigkeit
    assert beteiligung(monate[:2]) is None
    assert beteiligung([{"monat": "x", "rendite_pct": 1.0}] * 5) is None


def test_beteiligung_erkennt_das_muster_grosser_anstiege():
    """Der Fall, der die Kennzahl ausgeloest hat: kleine Anstiege gut mitgenommen,
    grosse kaum. Die Gesamtrendite verdeckt das, die Aufwaerts-Beteiligung nicht."""
    from backtest import beteiligung
    monate = [
        {"monat": "2026-03", "rendite_pct": +6.2, "btc_pct": +2.0},    # 310 %
        {"monat": "2026-08", "rendite_pct": +3.0, "btc_pct": +27.2},   # 11 %
        {"monat": "2026-06", "rendite_pct": +0.7, "btc_pct": -20.4},
    ]
    b = beteiligung(monate)
    assert b["auf_pct"] == 32            # 9,2 von 29,2 — trotz zweier "guter" Monate
    assert b["ab_pct"] < 0               # in fallenden Monaten im Plus


def test_simulate_schreibt_die_btc_rendite_je_monat_mit():
    """Ohne btc_pct in den Monatsdaten kann der Bericht die Kennzahl nicht bilden."""
    from strategy_core import Candle
    from backtest import simulate
    H4 = 4 * 3600 * 1000
    start = 1_767_225_600_000                      # 01.01.2026
    cs = [Candle(start + i * H4, 100 + i, 101 + i, 99 + i, 100 + i) for i in range(600)]
    sigs = [{"ts": cs[10].ts, "type": "KAUF_1", "price": 110.0, "tranche_pct": 25}]
    p = simulate(sigs, cs, start_ms=start)
    assert p["monate"], "keine Monatsdaten"
    assert all("btc_pct" in m for m in p["monate"]), "btc_pct fehlt in mindestens einem Monat"
    assert p["monate"][1]["btc_pct"] > 0            # der Testkurs steigt durchgehend


# ------------------------------------------------- E25: Gegengeschaefte zaehlen

def _sig(ts, typ, preis):
    return {"ts": ts, "type": typ, "price": preis}


def test_gegengeschaeft_wird_je_kerze_gezaehlt_nicht_je_signal():
    """Drei Signale in einer Kerze sind EIN Widerspruch, nicht drei.

    Der Fall stammt aus dem Live-Betrieb (09.07. und 17.07.2026): zweimal nachgekauft
    und einmal teilverkauft, alles in derselben Kerze zum selben Preis.
    """
    sigs = [_sig(1, "NACHKAUF", 100.0), _sig(1, "NACHKAUF", 100.0),
            _sig(1, "TEILVERKAUF_LADDER", 100.0),
            _sig(2, "KAUF_1", 90.0)]
    g = backtest.gegengeschaefte(sigs)
    assert g["kerzen"] == 1, f"eine Kerze erwartet, gezaehlt {g['kerzen']}"
    assert g["gleicher_preis"] == 1
    assert g["signale"] == 3 and g["signale_gesamt"] == 4


def test_vollstaendiger_ausstieg_ist_kein_gegengeschaeft():
    """Gegenprobe: Stop und Rest-Verkauf duerfen immer feuern, auch nach einem Nachkauf.

    Wuerden sie mitgezaehlt, sperrte die Kennzahl genau die Ausstiege, die nie
    unterdrueckt werden duerfen — und no_flip saehe schlechter aus, als es ist.
    """
    for typ in ("STOPLOSS", "VERKAUF_REST"):
        g = backtest.gegengeschaefte([_sig(1, "NACHKAUF", 100.0), _sig(1, typ, 95.0)])
        assert g["kerzen"] == 0, f"{typ} darf nicht als Gegengeschaeft zaehlen"
    # ... ein echter Teilverkauf in derselben Kerze aber schon
    g = backtest.gegengeschaefte([_sig(1, "NACHKAUF", 100.0), _sig(1, "TEILVERKAUF_1", 105.0)])
    assert g["kerzen"] == 1 and g["gleicher_preis"] == 0


def test_no_flip_variante_gegen_die_live_einstellung_existiert():
    """Die Zeile, die bisher fehlte (Kaiser 28.08.2026).

    Die aeltere no_flip-Zeile laeuft ohne min_bein_pct; ein Vergleich mit der
    Live-Einstellung misst dort zwei Unterschiede auf einmal. Dieser Test haelt fest,
    dass es eine Zeile gibt, die sich von der Live-Zeile in GENAU einem Punkt
    unterscheidet — sonst ist die Messung wieder wertlos.
    """
    live = next(v for v in backtest.GRID if v["label"] == "NEU-LIVE +Mindest-Bein 5 %")
    mit = next(v for v in backtest.GRID
               if v["label"] == "NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft")
    unterschiede = {k for k in backtest.EVAL_KEYS if live.get(k) != mit.get(k)}
    assert unterschiede == {"no_flip"}, f"genau ein Unterschied erwartet, gefunden {unterschiede}"
    assert mit["no_flip"] is True and live["no_flip"] is False


# ------------------------- E26: laenger investiert bleiben, sauber vergleichbar

def test_neustart_varianten_unterscheiden_sich_nur_im_gemeinten_punkt():
    """Der Fehler, den dieser Test verhindert (zum zweiten Mal, siehe E25).

    Die aelteren Zeilen "LIVE +Neustart mit Rest" laufen ohne no_flip, das seit
    28.08.2026 live ist. Sie gegen die Live-Zeile zu halten misst zwei Aenderungen auf
    einmal — genau der Grund, warum die no_flip-Messung monatelang wertlos war.
    """
    # Bezug ist die Zeile OHNE die Neustart-Schalter, nicht die Panel-Zeile: Sobald eine
    # der Varianten live geht, wandert panel=True auf sie, und der Vergleich mit sich
    # selbst waere leer. Die Basis-Zeile bleibt dagegen stehen.
    basis = next(v for v in backtest.GRID
                 if v["label"] == "NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft")
    faelle = {
        "LIVE-heute +Neustart mit Rest": {"neustart_mit_rest"},
        "LIVE-heute +Rest halten +Neustart mit Rest": {"neustart_mit_rest", "rest_halten"},
    }
    for label, erwartet in faelle.items():
        v = next(x for x in backtest.GRID if x["label"] == label)
        gefunden = {k for k in backtest.EVAL_KEYS if basis.get(k) != v.get(k)}
        assert gefunden == erwartet, f"{label}: erwartet {erwartet}, gefunden {gefunden}"


def test_beteiligung_steht_im_pnl_dict_fuer_die_tabellenspalte():
    """Die Spalte 'Aufwaerts' liest aus simulate() — nicht aus einer zweiten Rechnung.

    Geprueft wird bewusst der Weg DURCH simulate(): ein Test, der nur beteiligung()
    aufruft, bleibt gruen, wenn das Feld aus dem pnl-Dict faellt — dann zeigte die
    Tabelle stumm ueberall '—' und niemandem faellt es auf. (Genau das ist mir beim
    ersten Anlauf passiert; die Sabotage-Probe hat es aufgedeckt.)
    """
    from strategy_core import Candle
    H4 = 4 * 3600 * 1000
    start = 1_767_225_600_000                                   # 01.01.2026
    # ueber 600 4h-Kerzen (100 Tage) steigende Kurse -> mehrere Monate mit btc_pct
    cs = [Candle(start + i * H4, 100 + i, 101 + i, 99 + i, 100 + i) for i in range(600)]
    sigs = [{"ts": cs[10].ts, "type": "KAUF_1", "price": 110.0, "tranche_pct": 25}]
    p = backtest.simulate(sigs, cs, start_ms=start)
    assert "beteiligung" in p, "simulate() muss die Kennzahl mitliefern"
    assert p["beteiligung"] is not None, "sonst zeigt die Tabellenspalte ueberall '—'"
    assert p["beteiligung"]["auf_pct"] is not None
    assert p["beteiligung"]["auf_monate"] >= 2

    # und die Rechnung selbst: 5 + 4 von 10 + 20 = 30 %
    monate = [
        {"monat": "2026-01", "ende": 10500, "gewinn": 500, "rendite_pct": 5.0, "btc_pct": 10.0},
        {"monat": "2026-02", "ende": 10800, "gewinn": 300, "rendite_pct": 3.0, "btc_pct": -8.0},
        {"monat": "2026-03", "ende": 11200, "gewinn": 400, "rendite_pct": 4.0, "btc_pct": 20.0},
    ]
    b = backtest.beteiligung(monate)
    assert b["auf_pct"] == 30 and b["ab_pct"] == -38
    assert b["auf_monate"] == 2 and b["ab_monate"] == 1


def test_tabellenkopf_und_trennlinie_haben_gleich_viele_spalten():
    """Billiger Test gegen einen Fehler, der sonst niemandem auffaellt.

    Wird eine Spalte ergaenzt und die Markdown-Trennlinie darunter vergessen, rendert
    GitHub die Tabelle gar nicht mehr oder verschiebt alle Werte um eine Spalte — die
    Zahlen stehen dann unter den falschen Ueberschriften und man liest wochenlang
    Unsinn. Die Kopfzeile entsteht als Text im Code, deshalb wird sie hier als Text
    geprueft.
    """
    from pathlib import Path
    quelle = (Path(__file__).resolve().parent / "backtest.py").read_text(encoding="utf-8")
    i = quelle.index('"| Variante | Recall |')
    block = quelle[i:i + 600]
    kopf = block[:block.index('",')]
    trenn = block[block.index('"|---|'):]
    trenn = trenn[:trenn.index('",')]
    n_kopf = kopf.count("|") - 1                    # fuehrendes und schliessendes |
    n_trenn = trenn.count("|") - 1
    assert n_kopf == n_trenn, (
        f"Kopfzeile hat {n_kopf} Spalten, Trennlinie {n_trenn} — die Tabelle bricht.")
    for pflicht in ("Auf-", "Ab-", "Gegen-", "Rendite", "max. Rueckgang"):
        assert pflicht in kopf, f"Spalte '{pflicht}' fehlt in der Kopfzeile"


# --------------------------- E27: Rueckgang lueckenlos, nicht nur an Signalen

def test_rueckgang_zwischen_den_signalen_wird_mitgemessen():
    """Der Fehler, der bis 28.08.2026 in jeder Rueckgangszahl steckte.

    Szenario: einmal gekauft, danach faellt der Kurs um 40 % und erholt sich wieder —
    ohne dass in dieser Zeit ein einziges Signal faellt. Die alte Rechnung wertete nur
    Signalzeitpunkte aus und meldete deshalb 0 % Rueckgang, obwohl das Konto zeitweise
    30 % im Minus stand (75 % investiert x 40 % Kursverlust).
    """
    from strategy_core import Candle
    H4 = 4 * 3600 * 1000
    start = 1_767_225_600_000
    cs = [Candle(start, 100, 100, 100, 100),
          Candle(start + H4, 100, 100, 100, 100),
          Candle(start + 2 * H4, 100, 100, 60, 100),      # tiefe Kerze OHNE Signal
          Candle(start + 3 * H4, 100, 100, 100, 100)]
    sigs = [{"ts": cs[0].ts, "type": "KAUF_2", "price": 100.0, "tranche_pct": 75}]
    p = backtest.simulate(sigs, cs, start_ms=start, fee=0.0)
    assert p["max_drawdown_pct"] < -25, (
        f"Rueckgang zwischen den Signalen fehlt: {p['max_drawdown_pct']} %")
    assert abs(p["max_drawdown_pct"] - (-30.0)) < 0.5
    assert abs(p["ende"] - 10000.0) < 0.01, "der Endstand darf sich nicht geaendert haben"


def test_rueckgang_nutzt_das_kerzentief_nicht_den_schluss():
    """Gegenprobe zur Gegenprobe: ein Docht nach unten zaehlt, auch wenn die Kerze
    freundlich schliesst. Genau das sieht man auf dem Konto — der Schlusskurs ist die
    geschoente Zahl."""
    from strategy_core import Candle
    H4 = 4 * 3600 * 1000
    start = 1_767_225_600_000
    cs = [Candle(start, 100, 100, 100, 100),
          Candle(start + H4, 100, 101, 80, 100),          # Docht auf 80, Schluss 100
          Candle(start + 2 * H4, 100, 100, 100, 100)]
    sigs = [{"ts": cs[0].ts, "type": "KAUF_2", "price": 100.0, "tranche_pct": 100}]
    p = backtest.simulate(sigs, cs, start_ms=start, fee=0.0)
    assert abs(p["max_drawdown_pct"] - (-20.0)) < 0.5, (
        f"Kerzentief nicht beruecksichtigt: {p['max_drawdown_pct']} %")


def test_rueckgang_short_nutzt_das_kerzenhoch():
    """Spiegelbild: bei einer Short-Position ist das Kerzenhoch der schlimmste Moment."""
    from strategy_core import Candle
    H4 = 4 * 3600 * 1000
    start = 1_767_225_600_000
    cs = [Candle(start, 100, 100, 100, 100),
          Candle(start + H4, 100, 120, 99, 100),          # Docht nach OBEN
          Candle(start + 2 * H4, 100, 100, 100, 100)]
    sigs = [{"ts": cs[0].ts, "type": "SHORT_2", "price": 100.0, "tranche_pct": 100}]
    p = backtest.simulate(sigs, cs, start_ms=start, fee=0.0)
    assert p["max_drawdown_pct"] < -15, (
        f"Kerzenhoch bei Short nicht beruecksichtigt: {p['max_drawdown_pct']} %")


def test_ohne_flush_zeile_unterscheidet_sich_nur_im_flush():
    """Die Monatsuebersicht der Webseite stellt die Live-Einstellung der Zeile
    "MEINE Einstellung ohne Flush" gegenueber. Diese Gegenueberstellung ist nur dann
    aussagekraeftig, wenn sich die beiden Zeilen in GENAU EINEM Punkt unterscheiden:
    flush_entry. Am 05.09.2026 waren es vier Punkte - no_flip, neustart_mit_rest und
    zonen_nachziehen waren live geschaltet worden, ohne dass diese Zeile mitwanderte.
    """
    panel = [v for v in backtest.GRID if v.get("panel")]
    assert len(panel) == 1, "genau eine Gitterzeile muss panel=True tragen"
    ohne = [v for v in backtest.GRID if v["label"] == "MEINE Einstellung ohne Flush"]
    assert len(ohne) == 1, "die Zeile 'MEINE Einstellung ohne Flush' fehlt"
    a = {k: panel[0][k] for k in backtest.EVAL_KEYS if k in panel[0]}
    b = {k: ohne[0][k] for k in backtest.EVAL_KEYS if k in ohne[0]}
    abweichend = {k: (a.get(k), b.get(k))
                  for k in set(a) | set(b) if a.get(k) != b.get(k)}
    assert set(abweichend) == {"flush_entry"}, (
        "Die Zeile darf sich nur in flush_entry unterscheiden, weicht aber ab in: "
        f"{abweichend}")
