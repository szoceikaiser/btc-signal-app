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
    if not cfg_datei.exists():
        # LAUT ueberspringen, nicht still (E36.1, 19.09.2026): Dieser Test hat am
        # 13.09. angeschlagen (trend_ema 50 gegen 200) und SECHS TAGE lang jeden
        # GitHub-Lauf rot gemacht - waehrend er in der Arbeitskopie, wo site/data
        # fehlt, stillschweigend zurueckkehrte. Ein Test, der sich unbemerkt selbst
        # ausschaltet, ist schlimmer als keiner: Er suggeriert Deckung, die es nicht
        # gibt. Die Ausgabe steht jetzt im Protokoll.
        print("  UEBERSPRUNGEN: site/data/config.json fehlt - Panel-Zeile ungeprueft!")
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


def test_ampel_zeilen_unterscheiden_sich_von_der_live_zeile_in_genau_einem_punkt():
    """E34: Die drei Ampel-Zeilen sind nur dann deutbar, wenn sie sich von der
    Live-Zeile in GENAU EINEM benannten Punkt unterscheiden - sonst weiss man am
    Ende nicht, was den Unterschied gemacht hat.
    """
    live = next(v for v in backtest.GRID if v.get("panel"))
    erwartet = {
        "LIVE-heute +Ampel klein bei unguenstig": "klein",
        "LIVE-heute +Ampel UMGEKEHRT (Gegenprobe)": "gross",
        "LIVE-heute +immer halbe Tranche (Nullhypothese)": "immer",
    }
    for label, wert in erwartet.items():
        v = next(x for x in backtest.GRID if x["label"] == label)
        assert v["ampel_filter"] == wert
        anders = {k for k in backtest.EVAL_KEYS if live.get(k) != v.get(k)}
        assert anders == {"ampel_filter"}, f"{label}: unterscheidet sich in {anders}"
    # ... und die Live-Zeile selbst misst die Ampel NICHT
    assert live.get("ampel_filter") == "off"


def test_ampel_filter_kommt_im_backtest_ueberhaupt_an():
    """Der Weg DURCH simulate(): ein Test, der nur evaluate() aufruft, bliebe gruen,
    wenn ampel_filter aus EVAL_KEYS faellt - dann liefe die Gitterzeile stumm mit der
    Live-Einstellung und haette dasselbe Ergebnis wie sie."""
    assert "ampel_filter" in backtest.EVAL_KEYS
    import inspect
    from strategy_core import evaluate
    assert "ampel_filter" in inspect.signature(evaluate).parameters


# ------------------------------- E37.2: aggregiertes Spot-CVD im Backtest verdrahtet

def test_build_series_ohne_spot_map_rechnet_wie_bisher():
    """Rueckwaertskompatibel: ohne spot_map bleibt der Binance-Vision-Weg unveraendert.

    Rohkerze: Feld 7 = Quote-Volumen 1000, Feld 10 = Taker-Kauf-Quote 600.
    Delta = 2*600 - 1000 = +200 je Kerze, kumuliert 200 / 400 / 600.
    """
    raw = _rohkerzen(3)
    _cs, flow = backtest.build_series(raw, [], {int(raw[0][0]): 1e9}, None, None, None)
    assert [f.spot_cvd for f in flow] == [200.0, 400.0, 600.0], [f.spot_cvd for f in flow]


def test_build_series_mit_spot_map_ERSETZT_die_binance_rechnung():
    """Entweder-oder, nie beides: sonst zaehlt Binance doppelt — und in zwei Einheiten.

    Der Binance-Weg ergaebe +200 je Kerze (USD), die spot_map liefert hier ganz andere
    Zahlen (BTC). Kommt am Ende die Summe aus beiden heraus, ist die Verdrahtung falsch.
    """
    raw = _rohkerzen(3)
    ts = [int(k[0]) for k in raw]
    spot = {ts[0]: 5.0, ts[1]: -2.0, ts[2]: 3.0}
    _cs, flow = backtest.build_series(raw, [], {ts[0]: 1e9}, None, None, None,
                                      spot_map=spot)
    assert [f.spot_cvd for f in flow] == [5.0, 3.0, 6.0], [f.spot_cvd for f in flow]
    # Gegenprobe: waere der Binance-Anteil mit drin, stuende hier 205 / 403 / 606
    assert flow[0].spot_cvd != 205.0, "Binance darf nicht zusaetzlich mitgerechnet werden"


def test_build_series_leere_spot_map_haelt_das_cvd_flach_statt_binance_zu_nehmen():
    """Eine uebergebene, aber leere Karte heisst 'keine Daten' — nicht 'nimm Binance'.

    Sonst faellt ein Totalausfall der Aggregation nicht auf: der Backtest liefe
    stillschweigend wieder auf einer Boerse und der Vergleich zeigte keinen
    Unterschied, weil beide Zeilen dasselbe rechnen.
    """
    raw = _rohkerzen(3)
    _cs, flow = backtest.build_series(raw, [], {int(raw[0][0]): 1e9}, None, None, None,
                                      spot_map={})
    assert [f.spot_cvd for f in flow] == [0.0, 0.0, 0.0], [f.spot_cvd for f in flow]


def test_build_series_fehlende_kerze_in_der_spot_map_aendert_das_cvd_nicht():
    """Ausgelassene Zeitpunkte (nicht auf allen Boersen) lassen die Linie flach —
    sie duerfen sie nicht auf 0 zuruecksetzen."""
    raw = _rohkerzen(3)
    ts = [int(k[0]) for k in raw]
    spot = {ts[0]: 5.0, ts[2]: 3.0}                  # ts[1] fehlt
    _cs, flow = backtest.build_series(raw, [], {ts[0]: 1e9}, None, None, None,
                                      spot_map=spot)
    assert [f.spot_cvd for f in flow] == [5.0, 5.0, 8.0], [f.spot_cvd for f in flow]


# ------- E37.3: ein Vergleich, der nicht gerechnet werden konnte, verschwindet nicht

def test_abschnitt_oder_grund_baut_bei_daten_den_echten_abschnitt():
    gebaut = ["", "## Titel", "", "| a | b |"]
    assert backtest.abschnitt_oder_grund("Titel", {1: 2}, "", lambda: gebaut) == gebaut


def test_abschnitt_oder_grund_nennt_den_grund_statt_zu_verschwinden():
    """Der Fall vom 20.09.2026: Der Derivate-Abschnitt fiel lautlos aus dem Bericht,
    und niemand konnte sagen, ob der Abruf scheiterte oder der Code gar nicht lief."""
    z = backtest.abschnitt_oder_grund("Aggregierte Derivate-Daten", None,
                                      "HTTPError: 429 Too Many Requests", list)
    assert z, "leer heisst: der Abschnitt verschwindet doch"
    assert any(zeile.startswith("## Aggregierte Derivate-Daten") for zeile in z), z
    assert any("429" in zeile for zeile in z), z


def test_abschnitt_oder_grund_sagt_auch_wenn_niemand_einen_grund_festhielt():
    """Ohne Grund darf nicht einfach nichts dastehen — 'unbekannt' ist eine Aussage."""
    z = backtest.abschnitt_oder_grund("Titel", None, "", list)
    assert any("unbekannt" in zeile for zeile in z), z


def test_abschnitt_oder_grund_rechnet_im_fehlerfall_NICHT():
    """Die teure Rechnung darf nicht laufen, wenn es nichts zu rechnen gibt."""
    gelaufen = []

    def bauen():
        gelaufen.append(1)
        return ["x"]

    backtest.abschnitt_oder_grund("Titel", None, "Grund", bauen)
    assert gelaufen == [], "bauen() wurde trotz fehlender Daten aufgerufen"
    backtest.abschnitt_oder_grund("Titel", {1: 1}, "", bauen)
    assert gelaufen == [1], "bauen() wurde bei vorhandenen Daten NICHT aufgerufen"


# ------------------------------- E37.5: Robustheitspruefung der Datenvarianten

def test_besser_in_beiden_haelften_verlangt_BEIDE():
    """Ein Vorsprung in nur EINER Haelfte ist nicht von Zufall zu unterscheiden —
    genau deshalb gibt es die Halbierung."""
    zeilen = [
        ("heute", 10.0, 10.0),
        ("beide besser", 12.0, 11.0),
        ("nur H1 besser", 12.0, 9.0),
        ("nur H2 besser", 9.0, 11.0),
        ("beide schlechter", 8.0, 8.0),
    ]
    assert backtest.besser_in_beiden_haelften(zeilen, "heute") == ["beide besser"]


def test_besser_in_beiden_haelften_zaehlt_gleichstand_NICHT_als_besser():
    """Gleichstand ist kein Vorsprung. Sonst faende man 'Verbesserungen', die keine sind."""
    zeilen = [("heute", 10.0, 10.0), ("gleich", 10.0, 10.0), ("knapp", 10.0, 10.1)]
    assert backtest.besser_in_beiden_haelften(zeilen, "heute") == []


def test_besser_in_beiden_haelften_behauptet_nichts_ohne_basis():
    """Fehlt die Vergleichsbasis, ist die Frage nicht beantwortbar — dann lieber
    nichts sagen, als eine Rangfolge ohne Bezugspunkt zu melden."""
    zeilen = [("a", 12.0, 11.0), ("b", 9.0, 9.0)]
    assert backtest.besser_in_beiden_haelften(zeilen, "heute") == []
    assert backtest.besser_in_beiden_haelften([], "heute") == []


def test_besser_in_beiden_haelften_nennt_alle_gewinner_nicht_nur_den_ersten():
    zeilen = [("heute", 5.0, 5.0), ("a", 6.0, 6.0), ("b", 7.0, 7.0)]
    assert sorted(backtest.besser_in_beiden_haelften(zeilen, "heute")) == ["a", "b"]


# --------------------------------------------------- E38.1: Muster-Nachlauf (20.09.2026)

_H4 = 4 * 3600 * 1000


def _reihe(preise: list, ts0: int | None = None):
    """Kerzen + neutraler Flow aus einer Preisliste. Flow so, dass classify_pattern
    NEUTRAL liefert — die Musterzuordnung wird hier nicht getestet, nur die Auswertung."""
    from strategy_core import FlowPoint
    t0 = backtest.START_MS if ts0 is None else ts0
    cs = [Candle(t0 + i * _H4, p, p, p, p) for i, p in enumerate(preise)]
    fl = [FlowPoint(c.ts, 0.0, 0.0, 1000.0, 0.0, 0.0, 0.0, 50.0) for c in cs]
    return cs, fl


def _stat(median_alle=0.0, quote_alle=0.5, m5=None, horizont=6):
    """Baut eine muster_nachlauf-Struktur von Hand — inkl. der Episoden-Ebene "ep".

    Ohne "ep" waere jeder Test hier blind fuer die Gegenprobe-Tabelle, und die ist
    genau die Stelle, an der ein aufgeblasener Befund auffallen soll.
    """
    def _k(med, quote, n):
        return {"median": med, "mittel": med, "anteil_hoch": quote, "n": n}
    stat = {"ALLE": {"kerzen": 100, "episoden": 100,
                     horizont: _k(median_alle, quote_alle, 100),
                     "ep": {horizont: _k(median_alle, quote_alle, 100)}}}
    if m5 is not None:
        med, quote, kerzen, episoden = m5
        stat["UNGESUNDER_ABVERKAUF"] = {
            "kerzen": kerzen, "episoden": episoden,
            horizont: _k(med, quote, kerzen),
            "ep": {horizont: _k(med, quote, episoden)}}
    return stat


def test_muster_nachlauf_grundrate_enthaelt_jede_bewertete_kerze():
    """Ohne Grundrate ist jede Musterzeile wertlos: 'nach Muster 5 +3 %' sagt nichts,
    wenn der Kurs im Fenster ohnehin 3 % je Horizont steigt."""
    cs, fl = _reihe([100 + i for i in range(40)])
    stat = backtest.muster_nachlauf(cs, fl, backtest.START_MS, horizonte=(6,))
    ohne_alle = sum(v["kerzen"] for k, v in stat.items() if k != "ALLE")
    assert stat["ALLE"]["kerzen"] == ohne_alle


def test_muster_nachlauf_laesst_kerzen_ohne_vollen_nachlauf_aus():
    """Die letzten Kerzen haben keinen vollstaendigen Nachlauf. Wer sie mitzaehlt,
    vergleicht kurze mit langen Zeitraeumen — der Fehler faellt nicht auf."""
    cs, fl = _reihe([100.0] * 30)
    stat = backtest.muster_nachlauf(cs, fl, backtest.START_MS, horizonte=(6,))
    assert stat["ALLE"]["kerzen"] == 30 - 6          # 6 Kerzen Nachlauf fehlen hinten


def test_muster_nachlauf_alle_horizonte_teilen_dieselbe_stichprobe():
    """Sonst waere der lange Horizont ueber weniger Kerzen gerechnet als der kurze
    und die Spalten der Tabelle waeren nicht vergleichbar."""
    cs, fl = _reihe([100.0 + i * 0.1 for i in range(60)])
    stat = backtest.muster_nachlauf(cs, fl, backtest.START_MS, horizonte=(6, 12, 24))
    ns = {stat["ALLE"][h]["n"] for h in (6, 12, 24)}
    assert len(ns) == 1


def test_muster_nachlauf_wertet_kerzen_vor_dem_start_nicht():
    cs, fl = _reihe([100.0] * 40, ts0=backtest.START_MS - 20 * _H4)
    stat = backtest.muster_nachlauf(cs, fl, backtest.START_MS, horizonte=(6,))
    assert stat["ALLE"]["kerzen"] == 40 - 20 - 6


def test_muster_nachlauf_zaehlt_episoden_nicht_kerzen():
    """Aufeinanderfolgende Kerzen desselben Musters sind EIN Ereignis, kein Beleg je
    Kerze. 80 Kerzen koennen 9 Ereignisse sein — die Fallzahl waere sonst erfunden."""
    cs, fl = _reihe([100.0] * 40)
    stat = backtest.muster_nachlauf(cs, fl, backtest.START_MS, horizonte=(6,))
    neutral = stat["NEUTRAL"]
    assert neutral["kerzen"] > 1
    assert neutral["episoden"] == 1


def test_muster_nachlauf_median_widersteht_einem_ausreisser():
    """Ein einzelner Flush-Tag darf eine Musterzeile nicht kippen.

    Der Einbruch bei Kerze 25 erzeugt ZWEI Ausreisser, nicht einen: die Kerze 6 davor
    sieht -60 %, die Kerze selbst sieht +150 % (von 40 zurueck auf 100). Genau deshalb
    ist der Mittelwert hier untauglich — er laeuft weg, der Median bleibt stehen."""
    preise = [100.0] * 40
    preise[25] = 40.0                                  # ein Einbruch mittendrin
    cs, fl = _reihe(preise)
    stat = backtest.muster_nachlauf(cs, fl, backtest.START_MS, horizonte=(6,))
    d = stat["ALLE"][6]
    assert abs(d["median"]) < 0.01                      # Median bleibt bei ~0
    assert abs(d["mittel"]) > abs(d["median"]) + 0.01   # Mittelwert laeuft weg


def test_muster_abschnitt_nennt_den_abstand_zur_grundrate():
    stat = _stat(median_alle=0.02, quote_alle=0.6, m5=(0.05, 0.7, 30, 25))
    text = "\n".join(backtest.muster_abschnitt(stat, horizonte=(6,)))
    assert "+3.00 gg. Grundrate" in text                 # 5 % minus 2 % Grundrate
    assert "Grundrate" in text


def test_muster_abschnitt_warnt_bei_zu_wenigen_episoden():
    """Der gefaehrlichste Fall: eine schoene Zahl auf drei Ereignissen."""
    stat = _stat(m5=(0.09, 1.0, 30, 3))
    text = "\n".join(backtest.muster_abschnitt(stat, horizonte=(6,)))
    assert "zu duenn" in text.lower()
    assert "3 Episoden" in text


def test_muster_abschnitt_sagt_es_wenn_muster5_gar_nicht_vorkam():
    stat = _stat()
    text = "\n".join(backtest.muster_abschnitt(stat, horizonte=(6,)))
    assert "kein einziges Mal" in text


def test_muster_abschnitt_warnt_nicht_bei_genug_episoden():
    stat = _stat(m5=(0.01, 0.6, 90, 40))
    text = "\n".join(backtest.muster_abschnitt(stat, horizonte=(6,)))
    assert "zu duenn" not in text.lower()
    assert "VORZEICHEN" in text


def test_muster_abschnitt_sagt_dass_es_keine_ertragsaussage_ist():
    """Die Lehre aus zwoelf gemessenen Filtern: 'steigt danach' ist nicht 'verdient'."""
    stat = _stat(m5=(0.0, 0.5, 5, 5))
    text = "\n".join(backtest.muster_abschnitt(stat, horizonte=(6,)))
    assert "nicht den Ertrag" in text


def test_muster_abschnitt_leer_bei_leerer_statistik():
    assert backtest.muster_abschnitt({}) == []


def test_muster_nachlauf_misst_nach_vorn_nicht_nach_hinten():
    """Die gefaehrlichste denkbare Verwechslung in E38: Zeigt der Nachlauf nach hinten,
    liest sich jede Bremse als Treibstoff und umgekehrt — die Zahlen saehen dabei
    voellig normal aus. Deshalb eine Reihe, die EINDEUTIG steigt."""
    cs, fl = _reihe([100.0 + i for i in range(40)])
    stat = backtest.muster_nachlauf(cs, fl, backtest.START_MS, horizonte=(6,))
    assert stat["ALLE"][6]["median"] > 0.03            # ~6 Punkte auf ~100 = ~+5 %
    assert stat["ALLE"][6]["anteil_hoch"] == 1.0       # ausnahmslos hoeher


def test_muster_nachlauf_misst_den_rueckgang_als_rueckgang():
    """Gegenprobe zum Test darueber — eine fallende Reihe muss negativ herauskommen."""
    cs, fl = _reihe([200.0 - i for i in range(40)])
    stat = backtest.muster_nachlauf(cs, fl, backtest.START_MS, horizonte=(6,))
    assert stat["ALLE"][6]["median"] < -0.01
    assert stat["ALLE"][6]["anteil_hoch"] == 0.0


def test_median_mittelt_bei_gerader_anzahl():
    """Bei gerader Anzahl gibt es keinen mittleren Wert — wer einfach s[n//2] nimmt,
    verschiebt jede Musterzeile systematisch nach oben."""
    assert backtest._med([1.0, 2.0, 3.0, 4.0]) == 2.5
    assert backtest._med([1.0, 2.0, 3.0]) == 2.0
    assert backtest._med([]) == 0.0


# ------------------------------------------- E38: die neuen Gitterzeilen (20.09.2026)

_E38_ZEILEN = {
    "LIVE-heute +Muster 5 als Kauf-Bestaetigung": {"muster5_entry"},
    "LIVE-heute +Muster 5 haelt Zwischenverkaeufe": {"muster5_halten"},
    "LIVE-heute +Muster 5 haelt ALLE Teilverkaeufe": {"muster5_halten"},
    "LIVE-heute +Muster 5 sperrt Kaeufe (Bremse, Gegenprobe)": {"block_unhealthy"},
}


def _zeile(label: str) -> dict:
    treffer = [v for v in backtest.GRID if v["label"] == label]
    assert len(treffer) == 1, f"Gitterzeile fehlt oder ist doppelt: {label}"
    return treffer[0]


def test_e38_zeilen_unterscheiden_sich_in_genau_einem_punkt_von_live():
    """Die Lehre aus confirm_t1/cooldown_h, die dieses Projekt schon einmal teuer
    bezahlt hat: Ein Messergebnis gilt nur gegen die Basis, gegen die gemessen wurde.
    Wandert die Live-Zeile und diese Zeilen nicht mit, misst man zwei Unterschiede und
    schreibt einen davon auf."""
    panel = [v for v in backtest.GRID if v.get("panel")]
    assert len(panel) == 1
    basis = {k: panel[0][k] for k in backtest.EVAL_KEYS if k in panel[0]}
    for label, erwartet in _E38_ZEILEN.items():
        z = _zeile(label)
        hier = {k: z[k] for k in backtest.EVAL_KEYS if k in z}
        abweichend = {k for k in set(basis) | set(hier) if basis.get(k) != hier.get(k)}
        assert abweichend == erwartet, f"{label}: erwartet {erwartet}, ist {abweichend}"


def test_e43_bein_richtung_ist_live_und_das_panel_ist_mitgewandert():
    """Kaiser hat am 26.09.2026 bein_richtung="bias" live geschaltet (E43.2). Die
    Panel-Zeile muss genau diese Einstellung tragen - sonst zeigt die Webseite die
    Rendite der alten Einstellung."""
    panel = [v for v in backtest.GRID if v.get("panel")]
    assert len(panel) == 1
    assert panel[0]["bein_richtung"] == "bias"
    # Vorprobe: der Schalter wirkt nur, wenn genau EINE Richtung erlaubt ist
    # (strategy_core.evaluate). Sonst waere die Ausschalt-Probe eine Kopie der Live-Zeile.
    assert panel[0]["bias_long"] != panel[0]["bias_short"], \
        "bein_richtung wirkt bei dieser Live-Einstellung gar nicht"


def test_e43_alte_bein_richtung_unterscheidet_sich_in_genau_einem_punkt():
    """Die Ausschalt-Probe ist nur deutbar, wenn sie sich von der Live-Zeile in GENAU
    dem Schalter unterscheidet, der am 26.09.2026 umgelegt wurde."""
    panel = [v for v in backtest.GRID if v.get("panel")][0]
    basis = {k: panel[k] for k in backtest.EVAL_KEYS if k in panel}
    z = _zeile("LIVE bis 26.09.2026 (ohne Bein-Richtung)")
    hier = {k: z[k] for k in backtest.EVAL_KEYS if k in z}
    abweichend = {k for k in set(basis) | set(hier) if basis.get(k) != hier.get(k)}
    assert abweichend == {"bein_richtung"}, abweichend
    assert hier["bein_richtung"] == "auto"


def test_e38_die_beiden_halten_zeilen_messen_wirklich_verschiedenes():
    """Zwei Gitterzeilen mit demselben Wert waeren zwei Zeilen, die aussehen wie eine
    Bestaetigung — und in Wahrheit derselbe Lauf sind."""
    a = _zeile("LIVE-heute +Muster 5 haelt Zwischenverkaeufe")["muster5_halten"]
    b = _zeile("LIVE-heute +Muster 5 haelt ALLE Teilverkaeufe")["muster5_halten"]
    assert {a, b} == {"leiter", "alle"}


def test_e38_gegenprobe_bremse_ist_im_gitter():
    """Ohne die Gegenprobe bliebe offen, ob Muster 5 ueberhaupt etwas ueber den Ertrag
    sagt oder nur die eine Richtung nie geprueft wurde. block_unhealthy wurde in E13
    verworfen — aber gegen eine ANDERE Basis."""
    assert _zeile("LIVE-heute +Muster 5 sperrt Kaeufe (Bremse, Gegenprobe)"
                  )["block_unhealthy"] is True


def test_e38_schalter_stehen_in_eval_keys_und_kommen_so_ueberhaupt_an():
    """Ein Schalter, der nicht in EVAL_KEYS steht, wird von run_backtest stillschweigend
    nicht durchgereicht: Die Gitterzeile laeuft dann als exakte Kopie der Basis — und
    der Bericht zeigt eine Variante, die es nie gab."""
    for k in ("muster5_entry", "muster5_halten"):
        assert k in backtest.EVAL_KEYS, k
        assert k in backtest._BASE, k
    assert backtest._BASE["muster5_entry"] is False
    assert backtest._BASE["muster5_halten"] == "off"


def test_gegenprobe_zaehlt_nur_episodenbeginne():
    """Der Zweck der Gegenprobe ist, die Ueberlappung herauszurechnen. Nimmt sie doch
    alle Kerzen, ist sie eine zweite Kopie der Haupttabelle — und bestaetigt einen
    aufgeblasenen Befund, statt ihn aufzudecken."""
    cs, fl = _reihe([100.0] * 40)
    stat = backtest.muster_nachlauf(cs, fl, backtest.START_MS, horizonte=(6,))
    e = stat["NEUTRAL"]
    assert e["kerzen"] > 1, "Szenario ohne Serie — der Test pruefte nichts"
    assert e["ep"][6]["n"] == e["episoden"], "Gegenprobe zaehlt nicht je Episode"
    assert e["ep"][6]["n"] < e[6]["n"], "Gegenprobe ist so gross wie die Haupttabelle"


def test_gegenprobe_tabelle_nennt_die_episodenzahl_nicht_die_kerzenzahl():
    """Steht dort die Kerzenzahl, sieht die unabhaengige Stichprobe groesser aus, als
    sie ist — genau der Irrtum, den diese Tabelle ausraeumen soll."""
    stat = _stat(m5=(0.05, 0.7, 45, 26))
    text = "\n".join(backtest.muster_abschnitt(stat, horizonte=(6,)))
    gegenprobe = text.split("### Gegenprobe je Episode")[1]
    assert "| UNGESUNDER_ABVERKAUF | 26 |" in gegenprobe, gegenprobe[:400]
    assert "| UNGESUNDER_ABVERKAUF | 45 |" not in gegenprobe


def test_gegenprobe_vergleicht_gegen_dieselbe_grundrate_wie_oben():
    """Bewusste Festlegung: Der Fenster-Durchschnitt wird nicht dadurch ein anderer,
    dass man die Musterzeilen auf Episodenbeginne einschraenkt. Zwei verschiedene
    Bezugsgroessen haetten die beiden Tabellen unvergleichbar gemacht."""
    stat = _stat(median_alle=0.02, quote_alle=0.6, m5=(0.05, 0.7, 45, 26))
    text = "\n".join(backtest.muster_abschnitt(stat, horizonte=(6,)))
    haupt, gegen = text.split("### Gegenprobe je Episode")
    assert "+3.00 gg. Grundrate" in haupt          # 5 % minus 2 % Grundrate
    assert "+3.00 gg. Grundrate" in gegen          # dieselbe Bezugsgroesse


def test_gegenprobe_zeile_steht_im_gitter_und_heisst_wie_erwartet():
    """Die Gegenprobe (Bremse) ist der Grund, warum E38 ueberhaupt eine Aussage
    zulaesst: Ohne sie bliebe offen, ob Muster 5 etwas ueber den Ertrag sagt oder nur
    die eine Richtung nie geprueft wurde. Verschwindet die Zeile oder wird sie
    umbenannt, faellt das sonst niemandem auf."""
    labels = [v["label"] for v in backtest.GRID]
    assert "LIVE-heute +Muster 5 sperrt Kaeufe (Bremse, Gegenprobe)" in labels
    for lab in _E38_ZEILEN:
        assert lab in labels, f"E38-Gitterzeile fehlt oder wurde umbenannt: {lab}"


# ------------------------------------ E39: Was passiert nach einem Stop? (21.09.2026)

def _stopreihe(preise, tiefs=None):
    """Kerzen mit frei waehlbarem Tief - der tiefste Punkt nach dem Stop ist ja gerade
    die Groesse, um die es in E39 geht."""
    from strategy_core import FlowPoint
    cs = []
    for i, p in enumerate(preise):
        lo = tiefs[i] if tiefs and tiefs[i] is not None else p
        cs.append(Candle(backtest.START_MS + i * _H4, p, p, lo, p))
    fl = [FlowPoint(c.ts, 0.0, 0.0, 1000.0, 0.0, 0.0, 0.0, 50.0) for c in cs]
    return cs, fl


def _stop(cs, i, reason="Kerzenschluss unter Invalidierung 95"):
    return {"ts": cs[i].ts, "type": "STOPLOSS", "price": cs[i].close, "reason": reason}


def test_stop_nachlauf_misst_ab_dem_stop_preis_nach_vorn():
    """Steigt der Kurs nach dem Stop, muss das positiv herauskommen - die Richtung ist
    hier die ganze Aussage (vgl. die Vorzeichen-Sabotage aus E38.1)."""
    cs, fl = _stopreihe([100.0] * 5 + [100.0 + i for i in range(1, 31)])
    st = backtest.stop_nachlauf(cs, fl, [_stop(cs, 4)], horizonte=(6,))
    d = st["gruppen"]["ALLE"][6]
    assert abs(d["median"] - 0.06) < 1e-9               # 100 -> 106
    assert d["wieder_drueber"] == 1.0


def test_stop_nachlauf_tiefster_punkt_ist_das_minimum_bis_zum_horizont():
    """Der Grund fuer diese Messung: Was musste man aushalten, bevor es zurueckkam?"""
    preise = [100.0] * 5 + [100.0] * 30
    tiefs = [None] * 35
    tiefs[7] = 88.0                                      # Docht nach unten, 3 Kerzen spaeter
    cs, fl = _stopreihe(preise, tiefs)
    st = backtest.stop_nachlauf(cs, fl, [_stop(cs, 4)], horizonte=(6,))
    d = st["gruppen"]["ALLE"][6]
    assert abs(d["tief_median"] - (-0.12)) < 1e-9
    assert abs(d["tief_schlimmst"] - (-0.12)) < 1e-9
    assert d["median"] == 0.0                            # Schluss wieder bei 100


def test_stop_nachlauf_schaut_nicht_auf_die_stop_kerze_selbst():
    """Das Tief DER Stop-Kerze ist schon passiert - wer weitermacht, sitzt nur aus,
    was DANACH kommt. Sonst waere jeder tiefste Punkt kuenstlich schlimmer."""
    preise = [100.0] * 35
    tiefs = [None] * 35
    tiefs[4] = 50.0                                      # Tief IN der Stop-Kerze
    cs, fl = _stopreihe(preise, tiefs)
    st = backtest.stop_nachlauf(cs, fl, [_stop(cs, 4)], horizonte=(6,))
    assert st["gruppen"]["ALLE"][6]["tief_median"] == 0.0


def test_stop_nachlauf_zaehlt_nur_stops():
    cs, fl = _stopreihe([100.0] * 40)
    sigs = [_stop(cs, 4),
            {"ts": cs[6].ts, "type": "VERKAUF_REST", "price": 100.0, "reason": ""},
            {"ts": cs[8].ts, "type": "TEILVERKAUF_1", "price": 100.0, "reason": ""},
            {"ts": cs[9].ts, "type": "KAUF_1", "price": 100.0, "reason": ""}]
    st = backtest.stop_nachlauf(cs, fl, sigs, horizonte=(6,))
    assert st["gruppen"]["ALLE"]["n"] == 1


def test_stop_nachlauf_trennt_invalidierung_und_nachgezogenen_stop():
    """Kaisers Fall ist der urspruengliche Stop an der Invalidierung. Ein nach
    Teilgewinnen nachgezogener Stop ist eine andere Lage - da ist schon Gewinn
    gesichert. Beide in einen Topf zu werfen, verwischt genau den Unterschied."""
    cs, fl = _stopreihe([100.0] * 40)
    sigs = [_stop(cs, 4),
            _stop(cs, 10, reason="Nachgezogener Stop (Einstand) 100 — Kerzenschluss unter, "
                                  "Gewinn gesichert")]
    g = backtest.stop_nachlauf(cs, fl, sigs, horizonte=(6,))["gruppen"]
    assert g["art:Invalidierung"]["n"] == 1
    assert g["art:nachgezogen"]["n"] == 1
    assert g["ALLE"]["n"] == 2


def test_stop_nachlauf_ordnet_nach_dem_muster_in_der_stop_kerze():
    cs, fl = _stopreihe([100.0] * 40)
    g = backtest.stop_nachlauf(cs, fl, [_stop(cs, 20)], horizonte=(6,))["gruppen"]
    muster = [k for k in g if k.startswith("muster:")]
    assert muster == ["muster:NEUTRAL"]


def test_stop_nachlauf_stops_am_fensterende_zaehlen_nicht_mit_aber_nicht_still():
    cs, fl = _stopreihe([100.0] * 30)
    st = backtest.stop_nachlauf(cs, fl, [_stop(cs, 4), _stop(cs, 27)], horizonte=(6,))
    assert st["gruppen"]["ALLE"]["n"] == 1
    assert st["ohne_nachlauf"] == 1


def test_stop_nachlauf_alle_horizonte_teilen_dieselbe_stichprobe():
    """Ein Stop, der fuer 1 Tag Nachlauf hat, fuer 4 Tage aber nicht, faellt ganz raus -
    sonst stuenden in den Spalten verschiedene Stops."""
    cs, fl = _stopreihe([100.0] * 30)
    st = backtest.stop_nachlauf(cs, fl, [_stop(cs, 4), _stop(cs, 15)], horizonte=(6, 12, 24))
    assert st["gruppen"]["ALLE"]["n"] == 1               # nur der erste hat 24 Kerzen Platz
    assert st["ohne_nachlauf"] == 1


def test_stop_nachlauf_ohne_stops_liefert_keine_gruppe():
    cs, fl = _stopreihe([100.0] * 40)
    st = backtest.stop_nachlauf(cs, fl, [], horizonte=(6,))
    assert st["gruppen"] == {}
    assert backtest.stop_abschnitt(st) == []


def _stopstat(n=25, med=0.02, drueber=0.6, tief=-0.03, schlimmst=-0.09, gruppen=None):
    e = lambda n_: {"n": n_, 6: {"median": med, "wieder_drueber": drueber,
                                 "tief_median": tief, "tief_schlimmst": schlimmst}}
    g = {"ALLE": e(n)}
    for k, n_ in (gruppen or {}).items():
        g[k] = e(n_)
    return {"ohne_nachlauf": 0, "gruppen": g}


def test_stop_abschnitt_zeigt_den_tiefsten_punkt_in_jeder_zelle():
    text = "\n".join(backtest.stop_abschnitt(_stopstat(), horizonte=(6,)))
    assert "tief -3.0 % (-9.0 %)" in text
    assert "60% drueber" in text


def test_stop_abschnitt_markiert_duenne_gruppen():
    st = _stopstat(gruppen={"muster:UNGESUNDER_ABVERKAUF": 3, "art:Invalidierung": 20})
    text = "\n".join(backtest.stop_abschnitt(st, horizonte=(6,)))
    assert "Muster: UNGESUNDER_ABVERKAUF *(zu wenige)*" in text
    assert "Art: Invalidierung *(zu wenige)*" not in text


def test_stop_abschnitt_warnt_bei_zu_wenigen_stops_insgesamt():
    text = "\n".join(backtest.stop_abschnitt(_stopstat(n=4), horizonte=(6,)))
    assert "zu duenn" in text and "nur 4 Stops" in text


def test_stop_abschnitt_sagt_was_wieder_drueber_nicht_heisst():
    """Der gefaehrlichste Lesefehler dieser Tabelle: 'stand wieder drueber' als
    'Weitermachen hat sich gelohnt' zu lesen."""
    text = "\n".join(backtest.stop_abschnitt(_stopstat(), horizonte=(6,)))
    assert "nicht, dass" in text and "Weitermachen sich gelohnt" in text
    assert "Einstand" in text and "tiefsten Punkt" in text


def test_stop_abschnitt_nennt_die_grundrate_wenn_vorhanden():
    grund = {6: {"median": 0.0001, "mittel": 0.0, "anteil_hoch": 0.5, "n": 100}}
    text = "\n".join(backtest.stop_abschnitt(_stopstat(), grund=grund, horizonte=(6,)))
    assert "Grundrate" in text and "+0.01 %" in text and "50% hoeher" in text
    ohne = "\n".join(backtest.stop_abschnitt(_stopstat(), horizonte=(6,)))
    assert "Grundrate" not in ohne


def test_stop_abschnitt_nennt_keinen_namen():
    """Kaiser, 21.09.2026: kein 'Furkan' in den Texten."""
    text = "\n".join(backtest.stop_abschnitt(_stopstat(), horizonte=(6,)))
    assert "furkan" not in text.lower()


def test_e39_misst_die_live_einstellung_und_nicht_die_beste_variante():
    """Kaisers Frage betrifft die Stops, die er wirklich bekommt - die der
    Live-Einstellung (panel=True). Die rendite-beste Gitterzeile ist eine Variante,
    die nicht gefahren wird. main() braucht das Netz, deshalb wird die Verdrahtung
    im Quelltext geprueft."""
    import inspect
    quelle = inspect.getsource(backtest.main)
    assert "stop_nachlauf(candles, flow, _psigs)" in quelle
    i_panel = quelle.index("panel_cfg, _psigs, panel_sc, panel_pnl = panel_r")
    assert quelle.index("stop_nachlauf(candles, flow, _psigs)") > i_panel


def test_stop_nachlauf_schlimmster_fall_ist_das_minimum_ueber_alle_stops():
    """Der Median verdeckt genau den Fall, vor dem die Spalte warnen soll: den einen
    Stop, nach dem es erst richtig abwaerts ging."""
    preise = [100.0] * 60
    tiefs = [None] * 60
    tiefs[6] = 97.0                                      # nach Stop 1: -3 %
    tiefs[16] = 98.0                                     # nach Stop 2: -2 %
    tiefs[26] = 80.0                                     # nach Stop 3: -20 %
    cs, fl = _stopreihe(preise, tiefs)
    st = backtest.stop_nachlauf(cs, fl, [_stop(cs, 4), _stop(cs, 14), _stop(cs, 24)],
                                horizonte=(6,))
    d = st["gruppen"]["ALLE"][6]
    assert abs(d["tief_median"] - (-0.03)) < 1e-9
    assert abs(d["tief_schlimmst"] - (-0.20)) < 1e-9


def test_stop_nachlauf_gleichstand_ist_nicht_wieder_drueber():
    """Schliesst der Kurs genau auf dem Stop-Preis, ist er nicht 'wieder drueber' -
    sonst zaehlt jede Seitwaertsphase als Erholung."""
    cs, fl = _stopreihe([100.0] * 40)
    st = backtest.stop_nachlauf(cs, fl, [_stop(cs, 4)], horizonte=(6,))
    assert st["gruppen"]["ALLE"][6]["median"] == 0.0
    assert st["gruppen"]["ALLE"][6]["wieder_drueber"] == 0.0


# -------------------------- E40.1: STH-Kostenbasis, offline geprueft (21.09.2026)

import json as _json
from datetime import date as _date, timedelta as _td


def _holen(antworten: dict):
    """Ersetzt das Netz: url -> (status, text, fehler). Merkt sich jeden Abruf."""
    gefragt = []

    def holen(url):
        gefragt.append(url)
        return antworten.get(url, (404, "", "HTTP 404"))
    holen.gefragt = gefragt
    return holen


def _bitview_antwort(werte, start=0):
    return (200, _json.dumps({"index": "day1", "type": "Dollars", "start": start,
                              "end": start + len(werte), "data": werte}), "")


def test_sth_bitview_index_null_ist_der_1_januar_2009():
    """Die Datumszuordnung ist hergeleitet (Genesis-Block am 03.01.2009 = erster Wert).
    Rutscht sie um einen Tag, misst alles Weitere den falschen Tag."""
    werte = [None, None, 0.0, 5.0, 6.0]
    r, f = backtest.sth_bitview(_holen({backtest.STH_BITVIEW: _bitview_antwort(werte)}))
    assert f == ""
    assert r == {_date(2009, 1, 4): 5.0, _date(2009, 1, 5): 6.0}   # 0.0 und None fallen weg


def test_sth_bitview_beachtet_den_startindex():
    r, _ = backtest.sth_bitview(_holen({backtest.STH_BITVIEW: _bitview_antwort([7.0], start=10)}))
    assert r == {_date(2009, 1, 11): 7.0}


def test_sth_bgeometrics_wandelt_text_in_zahlen():
    """Die Werte kommen dort als Text. Ungewandelt stimmt kein Vergleich je ueberein."""
    liste = [{"d": "2026-09-14", "unixTs": "1789344000", "sthRealizedPrice": "71262.19"},
             {"d": "2026-09-13", "unixTs": "1789257600", "sthRealizedPrice": ""}]
    r, f = backtest.sth_bgeometrics(_holen({backtest.STH_BGEOMETRICS: (200, _json.dumps(liste), "")}))
    assert f == "" and r == {_date(2026, 9, 14): 71262.19}


def test_sth_quellen_halten_fehler_fest_statt_abzustuerzen():
    for fn in (backtest.sth_bitview, backtest.sth_bgeometrics):
        r, f = fn(_holen({}))
        assert r == {} and "404" in f
        r, f = fn(_holen({backtest.STH_BITVIEW: (200, "kaputt", ""),
                          backtest.STH_BGEOMETRICS: (200, "kaputt", "")}))
        assert r == {} and "nicht lesbar" in f


def test_sth_bgeometrics_wird_genau_einmal_gefragt():
    """15 Abrufe am Tag je IP, und GitHub-Runner teilen sich IPs."""
    h = _holen({})
    backtest.sth_bgeometrics(h)
    assert h.gefragt == [backtest.STH_BGEOMETRICS]


def _reihe_sth(tage=60, anfang=_date(2026, 1, 1)):
    return {anfang + _td(days=i): 70000.0 + i * 100 for i in range(tage)}


def test_sth_abgleich_findet_versatz_null_bei_gleichen_reihen():
    a = _reihe_sth()
    g = backtest.sth_abgleich(a, dict(a))
    assert g["bester_versatz"] == 0 and g["median_0"] == 0.0 and g["n"] == 60


def test_sth_abgleich_erkennt_einen_verschobenen_tag():
    """Genau dafuer gibt es den Abgleich: Ist bitview um einen Tag verrutscht, muss
    der beste Versatz das zeigen - und nicht 0."""
    a = _reihe_sth()
    b = {t + _td(days=1): v for t, v in a.items()}          # b einen Tag spaeter
    g = backtest.sth_abgleich(a, b)
    assert g["bester_versatz"] == 1
    assert g["median_0"] > 0


def test_sth_abgleich_ohne_gemeinsame_tage():
    assert backtest.sth_abgleich({_date(2026, 1, 1): 1.0}, {_date(2020, 1, 1): 1.0})["n"] == 0


def test_sth_je_kerze_nimmt_den_wert_des_vortags():
    """Der Tageswert steht erst am Tagesende fest. Wer ihn am selben Tag benutzt,
    kennt die Zukunft - der Backtest saehe besser aus, als es live je sein koennte."""
    from datetime import datetime, timezone
    ts = int(datetime(2026, 3, 10, 8, tzinfo=timezone.utc).timestamp() * 1000)
    c = Candle(ts, 1, 1, 1, 1)
    sth = {_date(2026, 3, 9): 111.0, _date(2026, 3, 10): 222.0}
    assert backtest.sth_je_kerze([c], sth) == {ts: 111.0}


def _stufen_kerzen(preise):
    return [Candle(backtest.START_MS + i * _H4, p, p, p, p) for i, p in enumerate(preise)]


def test_sth_vorfrage_trennt_unter_und_ueber():
    cs = _stufen_kerzen([90.0] * 20 + [110.0] * 40)
    sth_k = {c.ts: 100.0 for c in cs}
    v = backtest.sth_vorfrage(cs, sth_k, [], backtest.START_MS, horizonte=(6,))
    assert v["kerzen"]["unter"]["n"] == 20
    assert v["kerzen"]["ueber"]["n"] == 60 - 20 - 6          # Nachlauf hinten fehlt
    assert v["wechsel"] == 1


def test_sth_vorfrage_misst_einstiege_ab_einstiegspreis_nach_vorn():
    cs = _stufen_kerzen([100.0 + i for i in range(40)])
    sth_k = {c.ts: 105.0 for c in cs}
    sigs = [{"ts": cs[2].ts, "type": "KAUF_1", "price": 102.0},
            {"ts": cs[20].ts, "type": "NACHKAUF", "price": 120.0},
            {"ts": cs[21].ts, "type": "TEILVERKAUF_1", "price": 121.0},
            {"ts": cs[22].ts, "type": "STOPLOSS", "price": 122.0}]
    v = backtest.sth_vorfrage(cs, sth_k, sigs, backtest.START_MS, horizonte=(6,))
    e = v["einstiege"]
    assert e["unter"]["n"] == 1 and e["ueber"]["n"] == 1     # Teilverkauf zaehlt nicht
    assert abs(e["unter"][6]["median"] - (108.0 - 102.0) / 102.0) < 1e-9
    assert v["stops"] == {"unter": 0, "ueber": 1}


def test_sth_vorfrage_ohne_sth_wert_kein_raten():
    cs = _stufen_kerzen([100.0] * 30)
    v = backtest.sth_vorfrage(cs, {}, [], backtest.START_MS, horizonte=(6,))
    assert v["kerzen"]["unter"]["n"] == 0 and v["kerzen"]["ueber"]["n"] == 0
    assert v["ohne_sth"] == 30 - 6


def test_sth_abschnitt_warnt_bei_zweifelhafter_zuordnung():
    q = {"bitview.space": {"punkte": 10}, "bitcoin-data.com": {"punkte": 10}}
    schief = {"n": 50, "median_0": 0.05, "bester_versatz": 1, "median_bester": 0.001}
    text = "\n".join(backtest.sth_abschnitt(q, schief, None))
    assert "zweifelhaft" in text and "bitcoin-data.com" in text
    gut = {"n": 50, "median_0": 0.003, "bester_versatz": 0, "median_bester": 0.003}
    assert "zweifelhaft" not in "\n".join(backtest.sth_abschnitt(q, gut, None))


def test_sth_abschnitt_ohne_gegenpruefung_sagt_es():
    text = "\n".join(backtest.sth_abschnitt({"bitview.space": {"punkte": 5}}, {"n": 0}, None))
    assert "Keine Gegenpruefung" in text


def test_sth_abschnitt_nennt_vortag_und_warnt_bei_duennen_gruppen():
    cs = _stufen_kerzen([90.0] * 10 + [110.0] * 40)
    sth_k = {c.ts: 100.0 for c in cs}
    sigs = [{"ts": cs[i].ts, "type": "KAUF_1", "price": cs[i].close} for i in (2, 15, 16)]
    v = backtest.sth_vorfrage(cs, sth_k, sigs, backtest.START_MS, horizonte=(6,))
    text = "\n".join(backtest.sth_abschnitt({"bitview.space": {"punkte": 5}}, {"n": 0}, v,
                                             horizonte=(6,)))
    assert "Vortags" in text
    assert "zu duenn" in text
    assert "Nachlauf ist nicht Ertrag" in text
    assert "Was diese Messung NICHT zeigt" in text


def test_sth_vorfrage_einstiege_am_fensterende_zaehlen_nicht_still_mit():
    """Ein Einstieg ohne vollen Nachlauf hat keine vergleichbare Zahl. Er faellt raus -
    aber sichtbar, nicht still."""
    cs = _stufen_kerzen([100.0] * 30)
    sth_k = {c.ts: 105.0 for c in cs}
    sigs = [{"ts": cs[3].ts, "type": "KAUF_1", "price": 100.0},
            {"ts": cs[27].ts, "type": "KAUF_2", "price": 100.0}]
    v = backtest.sth_vorfrage(cs, sth_k, sigs, backtest.START_MS, horizonte=(6,))
    assert v["einstiege"]["unter"]["n"] == 1
    assert v["einstiege_ohne_nachlauf"] == 1


def test_sth_ist_im_bericht_verdrahtet_und_die_probe_weg():
    import inspect
    q = inspect.getsource(backtest.main)
    assert "sth_bitview()" in q and "sth_bgeometrics()" in q
    assert "sth_vorfrage(" in q and "sth_je_kerze(" in q
    assert "sth_probe" not in q                               # E40.0 ist ersetzt
    assert not hasattr(backtest, "sth_probe")


def test_sth_vorfrage_nutzt_die_live_einstellung():
    import inspect
    q = inspect.getsource(backtest.main)
    i_panel = q.index("panel_cfg, _psigs, panel_sc, panel_pnl = panel_r")
    assert q.index("sth_je_kerze(candles, _sth), _psigs, eff_start)") > i_panel


# ------------------------------------------- E41: live seit 21.09.2026 (Kaisers Regel)

def test_e41_rueckeroberung_ist_live_und_das_panel_ist_mitgewandert():
    """Kaiser hat am 21.09.2026 B1 live geschaltet. Die Panel-Zeile muss genau diese
    Einstellung tragen - sonst zeigt die Webseite die Rendite des alten Stops."""
    panel = [v for v in backtest.GRID if v.get("panel")]
    assert len(panel) == 1
    assert panel[0]["stop_rueckeroberung"] == 1
    assert panel[0]["stop_puffer_pct"] == 0.0 and panel[0]["stop_auf_docht"] is False


def test_e41_alter_stop_und_b3_unterscheiden_sich_in_genau_einem_punkt():
    """Die Ausschalt-Probe ist nur deutbar, wenn der alte Stop sich von live in GENAU
    dem Schalter unterscheidet, der umgelegt wurde."""
    panel = [v for v in backtest.GRID if v.get("panel")][0]
    basis = {k: panel[k] for k in backtest.EVAL_KEYS if k in panel}
    for label, wert in ((backtest.E41_ALTER_STOP, 0), (backtest.E41_B3, 3)):
        z = _zeile(label)
        hier = {k: z[k] for k in backtest.EVAL_KEYS if k in z}
        abw = {k for k in set(basis) | set(hier) if basis.get(k) != hier.get(k)}
        assert abw == {"stop_rueckeroberung"}, (label, abw)
        assert z["stop_rueckeroberung"] == wert, (label, z["stop_rueckeroberung"])


def test_e41_labels_stimmen_mit_dem_bericht_ueberein():
    """Der Berichtsabschnitt sucht die Zeilen ueber ihren Namen. Weicht einer ab,
    fehlt der Abschnitt - still."""
    labels = [v["label"] for v in backtest.GRID]
    assert set(backtest.E41_ZEILEN) == {backtest.E41_ALTER_STOP, backtest.E41_B3}
    for lab in backtest.E41_ZEILEN:
        assert labels.count(lab) == 1, lab


def test_alle_live_heute_zeilen_tragen_den_neuen_live_schalter():
    """Die Lehre aus confirm_t1/cooldown_h: Eine Zeile "LIVE-heute + X" misst X nur,
    solange sie die Live-Einstellung wirklich enthaelt. Nach dem Umschalten muss jede
    dieser Zeilen die Rueckeroberung tragen - ausser B3, die sie absichtlich anders
    setzt. (Die beiden aelteren Neustart-Zeilen messen gegen eine andere, feste Basis.)"""
    ausnahmen = {backtest.E41_B3, "LIVE-heute +Neustart mit Rest",
                 "LIVE-heute +Rest halten +Neustart mit Rest"}
    fehlt = [v["label"] for v in backtest.GRID
             if v["label"].startswith("LIVE-heute") and v["label"] not in ausnahmen
             and v["stop_rueckeroberung"] != 1]
    assert not fehlt, fehlt
    assert _zeile("MEINE Einstellung ohne Flush")["stop_rueckeroberung"] == 1


def test_e41_schalter_kommen_an():
    for k, v in (("stop_puffer_pct", 0.0), ("stop_rueckeroberung", 0), ("stop_auf_docht", False)):
        assert k in backtest.EVAL_KEYS and backtest._BASE[k] == v


def _kz(h1=10.0, h2=5.0, dd=-9.0, stops=10):
    return {"h1": h1, "h2": h2, "dd": dd, "stops": stops}


def test_e41_ausschalten_bleibt_an_bei_den_zahlen_vom_umschalttag():
    """Die Zahlen vom 21.09.2026: live (B1) H1 +21,3 / H2 +4,2 / Rueckgang -10,3 /
    9 Stops, alter Stop +18,7 / +4,0 / -9,4 / 10. Nach der eigenen Regel darf der
    Schalter damit nicht sofort wieder ausgehen."""
    u = backtest.e41_ausschalten(_kz(21.3, 4.2, -10.3, 9), _kz(18.7, 4.0, -9.4, 10))
    assert u == {"alt_klar_besser": False, "rueckgang_zu_tief": False, "greift": True,
                 "ausschalten": False}


def test_e41_ausschalten_alter_stop_muss_in_beiden_haelften_klar_besser_sein():
    live = _kz(10.0, 5.0)
    assert backtest.e41_ausschalten(live, _kz(11.0, 6.0))["ausschalten"] is True   # genau 1,0
    assert backtest.e41_ausschalten(live, _kz(11.0, 5.9))["ausschalten"] is False  # H2 Rauschen
    assert backtest.e41_ausschalten(live, _kz(10.9, 9.0))["ausschalten"] is False  # H1 Rauschen
    assert backtest.e41_ausschalten(live, _kz(9.0, 4.0))["ausschalten"] is False   # schlechter


def test_e41_ausschalten_bei_zu_tiefem_rueckgang():
    alt = _kz(dd=-9.0)
    assert backtest.e41_ausschalten(_kz(dd=-10.0), alt)["rueckgang_zu_tief"] is False  # Grenze
    u = backtest.e41_ausschalten(_kz(dd=-10.1), alt)
    assert u["rueckgang_zu_tief"] is True and u["ausschalten"] is True
    # ein FLACHERER Rueckgang live ist nie ein Ausschaltgrund
    assert backtest.e41_ausschalten(_kz(dd=-5.0), alt)["ausschalten"] is False


def test_e41_greift_nicht_ist_kein_ausschaltgrund():
    u = backtest.e41_ausschalten(_kz(stops=10), _kz(stops=10))
    assert u["greift"] is False and u["ausschalten"] is False


def _t(tag, stunde=0):
    from datetime import datetime, timezone
    return int(datetime(2026, 3, tag, stunde, tzinfo=timezone.utc).timestamp() * 1000)


def _e41_results(alt_h=(9.0, 4.0), alt_dd=-9.0):
    """Kuenstliche Ergebnisse: Live (B1), der alte Stop und B3."""
    alt_sigs = [{"ts": _t(1), "type": "STOPLOSS", "price": 100.0},
                {"ts": _t(8), "type": "STOPLOSS", "price": 90.0},
                {"ts": _t(8, 8), "type": "KAUF_2", "price": 92.16},
                {"ts": _t(20), "type": "STOPLOSS", "price": 80.0}]
    live_sigs = [{"ts": _t(1), "type": "STOPLOSS", "price": 100.0},
                 {"ts": _t(12), "type": "VERKAUF_REST", "price": 99.0}]
    def r(label, sigs, rend, dd):
        return ({"label": label}, sigs, {}, {"rendite_pct": rend, "max_drawdown_pct": dd})
    results = [r("LIVE", live_sigs, 20.0, -9.5), r(backtest.E41_ALTER_STOP, alt_sigs, 18.0, alt_dd),
               r(backtest.E41_B3, live_sigs, 21.0, -9.6)]
    halves = [({"label": "LIVE"}, {"rendite_pct": 10.0}, {"rendite_pct": 5.0}),
              ({"label": backtest.E41_ALTER_STOP}, {"rendite_pct": alt_h[0]},
               {"rendite_pct": alt_h[1]}),
              ({"label": backtest.E41_B3}, {"rendite_pct": 11.0}, {"rendite_pct": 4.0})]
    return results, halves


def _e41_text(**kw):
    results, halves = _e41_results(**kw)
    return "\n".join(backtest.e41_abschnitt(results, halves, "LIVE"))


def test_e41_abschnitt_vorprobe_die_zeilen_sind_da():
    """Vorprobe: Der Abschnitt muss ueberhaupt Zeilen erzeugen - sonst pruefen die
    Tests darunter leere Texte (der Fehler aus E38)."""
    text = _e41_text()
    assert "| **Live: Rueckeroberung, 1 Kerze** | +20.0 % |" in text
    assert "| Alter Stop (bis 21.09.) | +18.0 % |" in text
    assert "| B3 · 3 statt 1 Kerze | +21.0 % |" in text


def test_e41_abschnitt_bleibt_an_und_sagt_warum():
    text = _e41_text()
    assert "**Bleibt an.**" in text and "AUSSCHALTEN" not in text
    assert "(H1 -1.0, H2 -1.0 Punkte gegen live)" in text
    assert "(-0.5 Punkte gegen den alten Stop)" in text


def test_e41_abschnitt_meldet_ausschalten_bei_klar_besserem_alten_stop():
    text = _e41_text(alt_h=(11.0, 6.0))
    assert "**AUSSCHALTEN.**" in text and "**Bleibt an.**" not in text
    assert "`stop_rueckeroberung` auf 0" in text


def test_e41_abschnitt_nennt_die_ueberstimmung_nur_bei_ausschalten():
    """23.09.2026: Die Regel schlug an, Kaiser liess den Schalter an. Ohne diesen Hinweis
    liest sich jeder weitere Bericht wie ein Alarm, den niemand bemerkt hat - und in zwei
    Monaten weiss keiner mehr, ob die Meldung gesehen wurde. Die Regel selbst bleibt
    unveraendert: Sie meldet weiter AUSSCHALTEN."""
    aus = _e41_text(alt_h=(11.0, 6.0))
    assert "Bewusst ueberstimmt am 23.09.2026." in aus
    assert "docs/PLAN-E41-STOP.md" in aus
    assert "**AUSSCHALTEN.**" in aus                  # nicht abgeschwaecht
    assert "ueberstimmt" not in _e41_text()           # solange die Regel nicht anschlaegt


def test_e41_abschnitt_meldet_ausschalten_bei_zu_tiefem_rueckgang():
    text = _e41_text(alt_dd=-8.0)                    # live -9,5 -> 1,5 Punkte tiefer
    assert "**AUSSCHALTEN.**" in text


def test_e41_abschnitt_zeigt_was_aus_der_position_wurde_samt_wiedereinstieg():
    text = _e41_text()
    assert "- 01.03.2026 100 $ — live gleich gestoppt" in text
    # 08.03.: live hielt, endete am 12.03. per Restverkauf; der alte Stop kaufte
    # acht Stunden spaeter 2,4 % hoeher wieder ein (das Muster vom 08.03.2026)
    assert ("- 08.03.2026 90 $ — live stattdessen Restverkauf am 12.03.2026 bei 99 $ "
            "(+10.0 % gegen den alten Stop); der alte Stop kaufte am 08.03.2026 bei 92 $ "
            "wieder ein (+2.4 % gegen seinen Stop)") in text


def test_e41_abschnitt_wiedereinstieg_nach_dem_live_ausstieg_zaehlt_nicht():
    """Kauft der alte Stop erst wieder ein, nachdem live die Position schon beendet
    hat, ist das keine Folge des Stops mehr - und gehoert nicht in dieselbe Zeile."""
    results, halves = _e41_results()
    alt = results[1][1]
    alt[2] = {"ts": _t(13), "type": "KAUF_2", "price": 95.0}  # nach dem Live-Ausstieg 12.03.
    text = "\n".join(backtest.e41_abschnitt(results, halves, "LIVE"))
    assert "live stattdessen Restverkauf am 12.03.2026 bei 99 $ (+10.0 % gegen den alten Stop)\n" in text + "\n"
    assert "der alte Stop kaufte am" not in text


def test_e41_abschnitt_kein_ausstieg_bis_fensterende():
    text = _e41_text()
    assert "- 20.03.2026 80 $ — live kein Ausstieg bis Fensterende" in text


def test_e41_abschnitt_hinweis_wenn_die_regel_nicht_greift():
    results, halves = _e41_results()
    lv = results[0][1]
    results[0] = (results[0][0], lv + [{"ts": _t(25), "type": "STOPLOSS", "price": 1.0},
                                       {"ts": _t(26), "type": "STOPLOSS", "price": 1.0}],
                  {}, results[0][3])
    text = "\n".join(backtest.e41_abschnitt(results, halves, "LIVE"))
    assert "nicht seltener" in text
    assert "nicht seltener" not in _e41_text()


def test_e41_abschnitt_leer_ohne_basis_oder_ohne_alten_stop():
    results, halves = _e41_results()
    assert backtest.e41_abschnitt(results, halves, "GIBT ES NICHT") == []
    ohne = [r for r in results if r[0]["label"] != backtest.E41_ALTER_STOP]
    assert backtest.e41_abschnitt(ohne, halves, "LIVE") == []


def test_e41_ist_im_bericht_verdrahtet_mit_der_live_zeile_als_basis():
    import inspect
    q = inspect.getsource(backtest.main)
    assert 'e41_abschnitt(results, halves, panel_cfg["label"])' in q


# ------------------------------------------ E43.3: Muster 2 in Dollar (Befund A2)

def test_e433_zeile_unterscheidet_sich_in_genau_einem_punkt_von_live():
    """Ein Messergebnis gilt nur gegen die Basis, gegen die gemessen wurde. Genau EIN
    Unterschied zur Panel-Zeile: muster_cvd. Und die Panel-Zeile rechnet noch "alt" -
    sonst waere die Zeile eine Kopie der Live-Zeile."""
    assert "muster_cvd" in backtest.EVAL_KEYS and backtest._BASE["muster_cvd"] == "alt"
    panel = [v for v in backtest.GRID if v.get("panel")][0]
    basis = {k: panel[k] for k in backtest.EVAL_KEYS if k in panel}
    z = _zeile(backtest.E433_USD)
    hier = {k: z[k] for k in backtest.EVAL_KEYS if k in z}
    abweichend = {k for k in set(basis) | set(hier) if basis.get(k) != hier.get(k)}
    assert abweichend == {"muster_cvd"}, abweichend
    assert hier["muster_cvd"] == "usd" and basis["muster_cvd"] == "alt"


def test_e433_live_konfig_steht_auf_alt():
    """Default AUS bis zur Messung und Kaisers Go (Projektregel 1)."""
    import json
    from pathlib import Path
    cfg_datei = Path(__file__).resolve().parent.parent / "site" / "data" / "config.json"
    if not cfg_datei.exists():
        print("  UEBERSPRUNGEN: site/data/config.json fehlt - muster_cvd ungeprueft!")
        return
    cfg = json.loads(cfg_datei.read_text(encoding="utf-8"))
    assert cfg.get("muster_cvd") == "alt"
    assert "_hinweis_muster_cvd" in cfg


def _hz(h1=10.0, h2=5.0, dd=-9.0):
    return {"h1": h1, "h2": h2, "dd": dd}


def test_e433_einschalten_nur_wenn_beide_haelften_klar_besser():
    live = _hz(10.0, 5.0)
    assert backtest.e433_einschalten(live, _hz(11.0, 6.0))["einschalten"] is True   # genau 1,0
    assert backtest.e433_einschalten(live, _hz(11.0, 5.9))["einschalten"] is False  # H2 Rauschen
    assert backtest.e433_einschalten(live, _hz(10.9, 9.0))["einschalten"] is False  # H1 Rauschen
    assert backtest.e433_einschalten(live, _hz(9.0, 4.0))["einschalten"] is False   # schlechter


def test_e433_einschalten_nicht_bei_zu_tiefem_rueckgang():
    live = _hz(dd=-9.0)
    gut = dict(h1=12.0, h2=7.0)
    assert backtest.e433_einschalten(live, _hz(dd=-10.0, **gut))["einschalten"] is True  # Grenze
    u = backtest.e433_einschalten(live, _hz(dd=-10.1, **gut))
    assert u["rueckgang_ok"] is False and u["einschalten"] is False
    # ein FLACHERER Rueckgang ist nie ein Hindernis
    assert backtest.e433_einschalten(live, _hz(dd=-5.0, **gut))["einschalten"] is True


def _pump_reihe(n, alter_abfluss=0.0):
    """Das E43.5-Szenario als EINE durchgehende Reihe, summiert ab Datenbeginn - so wie
    build_series im Backtest rechnet. `alter_abfluss` = Spot-Delta je Kerze in den
    ersten 100 Kerzen: Geld, das der Backtest in seiner Summe mitschleppt, die Live-
    Engine (1.300 Kerzen) aber nie geladen hat - der Fall aus dem Pruefbericht."""
    from test_strategy_core import _flow_ab, _pump_szenario
    kerzen, roh = _pump_szenario(n_kerzen=n)
    roh = [(sd + (alter_abfluss if i < 100 else 0.0), fd, oi, fu)
           for i, (sd, fd, oi, fu) in enumerate(roh)]
    return kerzen, _flow_ab(kerzen, roh, 0, n)


def test_e433_vorprobe_im_bericht_zaehlt_umklassifizierte_kerzen():
    """e433_umklassifiziert() ist die Vorprobe im echten Datensatz: Aendert usd
    ueberhaupt ein Muster? Im Pump-Szenario muss sie solche Kerzen finden."""
    kerzen, flow = _pump_reihe(1900)
    u = backtest.e433_umklassifiziert(kerzen, flow, kerzen[1300].ts)
    assert u["kerzen"] == 600 and u["live_kerzen"] == 600, u
    assert u["verschieden"] > 0 and u["pump_usd"] > 0, u


def test_e433_vorprobe_zeigt_live_gegen_backtest():
    """Zweiter Teil der Vorprobe: Wie oft saehe die Live-Engine ein anderes Muster als
    der Backtest? Mit einem alten Spot-Abfluss (-500 Mio $ je Kerze in den ersten 100
    Kerzen, zusammen -50 Mrd $ wie im Pruefbericht) vor dem Live-Ladefenster: bei alt
    an manchen Kerzen (A2), bei usd an KEINER.

    Gezaehlt wird ab Kerze 1400 - erst dort liegt der Abfluss ganz vor dem
    Live-Fenster. Vorprobe: ohne den Abfluss liegt die Zahl im selben Szenario bei 0,
    der Abfluss ist also, was den Unterschied macht."""
    kerzen, flow = _pump_reihe(1900)
    ohne = backtest.e433_umklassifiziert(kerzen, flow, kerzen[1400].ts)
    kerzen, flow = _pump_reihe(1900, alter_abfluss=-5e8)
    mit = backtest.e433_umklassifiziert(kerzen, flow, kerzen[1400].ts)
    assert ohne["live_anders_alt"] == 0, ohne
    assert mit["live_kerzen"] == 500 and mit["live_anders_alt"] > 0, mit
    assert mit["live_anders_usd"] == 0, mit


def test_e433_vorprobe_zaehlt_nur_nachstellbare_kerzen_fuer_live():
    """Reichen die Daten keine 1.300 Kerzen vor eine Kerze zurueck, ist der Live-Stand
    dort unbekannt - diese Kerzen duerfen nicht als 'live gleich' gezaehlt werden."""
    kerzen, flow = _pump_reihe(1400)
    u = backtest.e433_umklassifiziert(kerzen, flow, kerzen[1000].ts)
    assert u["kerzen"] == 400 and u["live_kerzen"] == 100, u


def test_e433_abschnitt_meldet_urteil_und_kein_urteil_ohne_umklassifizierung():
    def r(label, rendite, dd, n=5):
        return ({"label": label}, [{}] * n, {}, {"rendite_pct": rendite,
                                                  "max_drawdown_pct": dd})

    def h(label, h1, h2):
        return ({"label": label}, {"rendite_pct": h1}, {"rendite_pct": h2})

    res = [r("LIVE", 25.0, -9.9), r(backtest.E433_USD, 28.0, -10.2)]
    hal = [h("LIVE", 20.0, 5.0), h(backtest.E433_USD, 21.5, 6.2)]
    umkl = {"kerzen": 100, "pump_alt": 7, "pump_usd": 4, "verschieden": 5,
            "live_kerzen": 50, "live_anders_alt": 3, "live_anders_usd": 0}
    text = "\n".join(backtest.e433_abschnitt(res, hal, "LIVE", umkl))
    assert "Regel erfuellt" in text and "Verschieden erkannt: 5 Kerzen" in text
    hal[1] = h(backtest.E433_USD, 21.5, 5.5)                       # H2 nur +0,5
    text = "\n".join(backtest.e433_abschnitt(res, hal, "LIVE", umkl))
    assert "bleibt auf `alt`" in text
    umkl["verschieden"] = 0
    text = "\n".join(backtest.e433_abschnitt(res, hal, "LIVE", umkl))
    assert "Kein Urteil" in text and "Regel" not in text.split("Kein Urteil")[1]


def test_e433_ist_im_bericht_verdrahtet_mit_der_live_zeile_als_basis():
    import inspect
    q = inspect.getsource(backtest.main)
    assert 'e433_abschnitt(results, halves, panel_cfg["label"], _umkl)' in q
    assert "e433_umklassifiziert(candles, flow, eff_start)" in q


# ------------------------------------ E43.4: OI in Kontrakten statt Dollar (Befund A3)

def _rohkerzen_kurs(closes, start=1_700_000_000_000):
    """Binance-Kerzenformat mit wechselndem Kurs; Eroeffnung 5 $ unter dem Schluss,
    damit auffaellt, wer mit dem falschen Kurs der Kerze rechnet."""
    ms = 4 * 3600 * 1000
    return [[start + i * ms, cl - 5.0, cl + 1.0, cl - 6.0, cl, 10.0,
             start + (i + 1) * ms, 1000.0, 50, 0, 600.0] for i, cl in enumerate(closes)]


def _e434_oi_mit_luecken(raw):
    """OI-Punkte nur fuer Kerze 1 (10 BTC bei 110 $) und 3 (12 BTC bei 130 $): Kerze 0
    liegt vor dem Datenbeginn, Kerze 2 ist eine Luecke, Kerze 4 (die juengste) hat noch
    keinen Punkt - die drei Faelle, in denen aufgefuellt wird."""
    ts = [int(k[0]) for k in raw]
    return {ts[1]: 110.0 * 10, ts[3]: 130.0 * 12}


def test_e434_build_series_rechnet_um_und_fuellt_dann_kontrakte_auf():
    """Umrechnen am Datenpunkt, dann auffuellen: Wo ein Punkt fehlt, gelten die
    Kontrakte des letzten (davor: des ersten) Punktes - nicht der alte Dollar-Wert
    geteilt durch den neuen Kurs. Das wuerde eine OI-Bewegung in Hoehe der
    Kursbewegung erfinden. Das Dollar-OI bleibt, wie es war."""
    raw = _rohkerzen_kurs([100.0, 110.0, 120.0, 130.0, 140.0])
    oi_map = _e434_oi_mit_luecken(raw)
    _cs, flow = backtest.build_series(raw, [], oi_map)
    assert [f.oi_btc for f in flow] == [10.0, 10.0, 10.0, 12.0, 12.0], flow
    assert [f.oi for f in flow] == [1100.0, 1100.0, 1100.0, 1560.0, 1560.0]
    # Vorprobe: der naive Weg (Dollar auffuellen, dann durch den Kurs der Kerze teilen)
    # ergaebe hier andere Zahlen - der Test unterscheidet die beiden Wege also.
    naiv = [f.oi / c.close for f, c in zip(flow, _cs)]
    assert naiv[0] != 10.0 and naiv[2] != 10.0 and naiv[4] != 12.0, naiv


def test_e434_build_series_ohne_oi_map_hat_keine_kontrakt_reihe():
    """Ohne Coinalyze steht das Dollar-OI konstant auf 1.0 (neutral). Die Kontrakt-
    Reihe bleibt 0.0 = keine Daten - 1.0 durch den Kurs geteilt waere eine erfundene
    Reihe, die sich gegenlaeufig zum Kurs bewegt."""
    raw = _rohkerzen_kurs([100.0, 110.0, 120.0])
    _cs, flow = backtest.build_series(raw, [], None)
    assert [f.oi for f in flow] == [1.0, 1.0, 1.0]
    assert [f.oi_btc for f in flow] == [0.0, 0.0, 0.0]


def test_e434_zeile_unterscheidet_sich_in_genau_einem_punkt_von_live():
    """Genau EIN Unterschied zur Panel-Zeile: muster_oi. Die Panel-Zeile rechnet noch
    "usd" - sonst waere die Zeile eine Kopie der Live-Zeile. muster_cvd bleibt "alt"."""
    assert "muster_oi" in backtest.EVAL_KEYS and backtest._BASE["muster_oi"] == "usd"
    panel = [v for v in backtest.GRID if v.get("panel")][0]
    basis = {k: panel[k] for k in backtest.EVAL_KEYS if k in panel}
    z = _zeile(backtest.E434_BTC)
    hier = {k: z[k] for k in backtest.EVAL_KEYS if k in z}
    abweichend = {k for k in set(basis) | set(hier) if basis.get(k) != hier.get(k)}
    assert abweichend == {"muster_oi"}, abweichend
    assert hier["muster_oi"] == "btc" and basis["muster_oi"] == "usd"


def test_e434_live_konfig_steht_auf_usd():
    """Default AUS bis zur Messung und Kaisers Go (Projektregel 1)."""
    import json
    from pathlib import Path
    cfg_datei = Path(__file__).resolve().parent.parent / "site" / "data" / "config.json"
    if not cfg_datei.exists():
        print("  UEBERSPRUNGEN: site/data/config.json fehlt - muster_oi ungeprueft!")
        return
    cfg = json.loads(cfg_datei.read_text(encoding="utf-8"))
    assert cfg.get("muster_oi") == "usd"
    assert "_hinweis_muster_oi" in cfg


def test_e434_einschalten_nur_wenn_beide_haelften_klar_besser():
    live = _hz(10.0, 5.0)
    assert backtest.e434_einschalten(live, _hz(11.0, 6.0))["einschalten"] is True   # genau 1,0
    assert backtest.e434_einschalten(live, _hz(11.0, 5.9))["einschalten"] is False  # H2 Rauschen
    assert backtest.e434_einschalten(live, _hz(10.9, 9.0))["einschalten"] is False  # H1 Rauschen
    assert backtest.e434_einschalten(live, _hz(9.0, 4.0))["einschalten"] is False   # schlechter


def test_e434_einschalten_nicht_bei_zu_tiefem_rueckgang():
    live = _hz(dd=-9.0)
    gut = dict(h1=12.0, h2=7.0)
    assert backtest.e434_einschalten(live, _hz(dd=-10.0, **gut))["einschalten"] is True  # Grenze
    u = backtest.e434_einschalten(live, _hz(dd=-10.1, **gut))
    assert u["rueckgang_ok"] is False and u["einschalten"] is False
    assert backtest.e434_einschalten(live, _hz(dd=-5.0, **gut))["einschalten"] is True


def test_e434_vorprobe_zaehlt_a3_je_muster():
    """"A3 als Zahl": In der Lage aus dem Pruefbericht (Kontrakte gleich, nur der Kurs
    bewegt sich) ist die OI-Bedingung in Dollar erfuellt, in Kontrakten nicht - fuer
    den Derivate-Pump wie fuer die Kapitulation. Und die Muster unterscheiden sich."""
    from test_strategy_core import _A3_KAPITULATION, _A3_PUMP, _oi_lage
    for lage, name, u_erw, b_erw in ((_A3_PUMP, "2 Derivate-Pump", "DERIVATE_PUMP",
                                      "GESUNDER_TREND"),
                                     (_A3_KAPITULATION, "4 Kapitulation",
                                      "CAPITULATION_RESET", "UNGESUNDER_ABVERKAUF")):
        cs, fl = _oi_lage(*lage)
        u = backtest.e434_umklassifiziert(cs, fl, cs[0].ts, {x.ts: x.oi for x in fl})
        assert u["kerzen"] == 1 and u["oi_kerzen"] == 1 and u["verschieden"] == 1, u
        assert u["a3"][name] == {"kurs": 1, "usd": 1, "btc": 0, "beide": 0}, u["a3"]
        assert u["je_muster"] == {u_erw: [1, 0], b_erw: [0, 1]}, u["je_muster"]


def test_e434_vorprobe_im_pump_szenario_findet_umklassifizierte_kerzen():
    """Im E43.5-Pump-Szenario steigt das Dollar-OI in den Pump-Phasen mit dem Kurs.
    Die Vorprobe muss dort umklassifizierte Kerzen finden, und jede Spalte der
    Mustertabelle zaehlt jede Kerze genau einmal."""
    from test_strategy_core import _mit_kontrakten
    kerzen, flow = _pump_reihe(1900)
    flow = _mit_kontrakten(kerzen, flow)
    u = backtest.e434_umklassifiziert(kerzen, flow, kerzen[1300].ts,
                                      {x.ts: x.oi for x in flow})
    assert u["kerzen"] == 600 and u["oi_kerzen"] == 600 and u["verschieden"] > 0, u
    assert sum(n[0] for n in u["je_muster"].values()) == 600
    assert sum(n[1] for n in u["je_muster"].values()) == 600


def test_e434_vorprobe_ohne_oi_daten_misst_nichts():
    """Ohne OI-Daten (kein Coinalyze-Key) aendert der Schalter nichts, und die Vorprobe
    sagt das: 0 Kerzen mit echtem OI-Punkt, 0 verschieden erkannt."""
    raw = _rohkerzen_kurs([100.0 + (i % 7) * 3 for i in range(40)])
    cs, flow = backtest.build_series(raw, [], None)
    u = backtest.e434_umklassifiziert(cs, flow, cs[0].ts, None)
    assert u["kerzen"] == 29 and u["oi_kerzen"] == 0 and u["verschieden"] == 0, u


def test_e434_abschnitt_meldet_urteil_und_kein_urteil():
    def r(label, rendite, dd, n=5):
        return ({"label": label}, [{}] * n, {}, {"rendite_pct": rendite,
                                                  "max_drawdown_pct": dd})

    def h(label, h1, h2):
        return ({"label": label}, {"rendite_pct": h1}, {"rendite_pct": h2})

    res = [r("LIVE", 25.0, -9.9), r(backtest.E434_BTC, 28.0, -10.2)]
    hal = [h("LIVE", 20.0, 5.0), h(backtest.E434_BTC, 21.5, 6.2)]
    a3 = {b[0]: {"kurs": 9, "usd": 5, "btc": 2, "beide": 2}
          for b in backtest.E434_BEDINGUNGEN}
    umkl = {"kerzen": 100, "oi_kerzen": 100, "verschieden": 5, "a3": a3,
            "je_muster": {"DERIVATE_PUMP": [7, 3], "NEUTRAL": [93, 97]}}
    text = "\n".join(backtest.e434_abschnitt(res, hal, "LIVE", umkl))
    assert "Regel erfuellt" in text and "Verschieden erkannt: 5 Kerzen" in text
    assert "| DERIVATE_PUMP | 7 | 3 |" in text and "| 2 Derivate-Pump |" in text
    hal[1] = h(backtest.E434_BTC, 21.5, 5.5)                       # H2 nur +0,5
    text = "\n".join(backtest.e434_abschnitt(res, hal, "LIVE", umkl))
    assert "bleibt auf `usd`" in text
    for feld in ("verschieden", "oi_kerzen"):               # je fuer sich: kein Urteil
        kaputt = dict(umkl, **{feld: 0})
        text = "\n".join(backtest.e434_abschnitt(res, hal, "LIVE", kaputt))
        assert "Kein Urteil" in text and "Regel" not in text.split("Kein Urteil")[1], feld


def test_e434_ist_im_bericht_verdrahtet_mit_der_live_zeile_als_basis():
    import inspect
    q = inspect.getsource(backtest.main)
    assert 'e434_abschnitt(results, halves, panel_cfg["label"], _e434)' in q
    assert "e434_umklassifiziert(candles, flow, eff_start, oi_map)" in q


# ------------------------------------------ A5: next_pivot_beyond haengt von der Historie ab

def _a5_kerzen(n: int, spike_idx: int, spike_preis: float, basis: float = 100.0) -> list:
    """n flache Kerzen um `basis`, eine einzelne Spitze bei `spike_idx` auf `spike_preis`
    (bestaetigtes Pivot-Hoch mit pivot_n=5, weil links UND rechts genug flache Kerzen
    liegen)."""
    out = []
    for i in range(n):
        preis = spike_preis if i == spike_idx else basis
        out.append(Candle(ts=1000 + i, open=preis, high=preis, low=preis, close=preis))
    return out


def test_a5_zaehlt_kerzen_ausserhalb_des_nachstellbaren_bereichs_nicht():
    """Kerzen, fuer die die Daten nicht 1.300 Kerzen zurueckreichen (i - 1300 + 1 < 0),
    werden nicht mitgezaehlt - wie bei E43.3/E43.4."""
    cs = _a5_kerzen(1305, spike_idx=2, spike_preis=200.0)
    u = backtest.a5_next_pivot_beyond(cs, cs[0].ts)
    assert u["kerzen"] == 1305 - backtest.A5_LIVE_SPOT_KERZEN + 1 == 6


def test_a5_findet_einen_unterschied_wenn_die_live_historie_das_alte_hoch_verliert():
    """Die Spitze bei Index 20 ist ein bestaetigtes Pivot-Hoch. Gegen Ende der Reihe
    faellt sie aus dem 1.300 Kerzen langen, gleitenden Live-Fenster (candles[i-1299:i+1])
    komplett heraus, waehrend die wachsende Backtest-Historie (candles[:i+1], ab
    Datenbeginn) sie weiter sieht -> next_pivot_beyond findet mit Live ein anderes (oder
    gar kein) Pivot."""
    cs = _a5_kerzen(1400, spike_idx=20, spike_preis=200.0)
    u = backtest.a5_next_pivot_beyond(cs, cs[0].ts)
    assert u["anders"] >= 1, u
    assert u["kerzen"] == 1400 - backtest.A5_LIVE_SPOT_KERZEN + 1


def test_a5_keine_kerzen_nachstellbar_ohne_1300_kerzen_vorlauf():
    cs = _a5_kerzen(50, spike_idx=2, spike_preis=200.0)
    u = backtest.a5_next_pivot_beyond(cs, cs[0].ts)
    assert u == {"kerzen": 0, "anders": 0}


def test_a5_ohne_jeden_unterschied_gleiche_pivots_ueberall():
    """Keine Spitze ausserhalb des Live-Fensters -> 0 Treffer, wie im 0-Treffer-Fall
    dokumentiert werden soll."""
    cs = _a5_kerzen(1400, spike_idx=1350, spike_preis=200.0)   # Spitze bleibt im Live-Fenster
    u = backtest.a5_next_pivot_beyond(cs, cs[0].ts)
    assert u["kerzen"] > 0
    assert u["anders"] == 0, u


def test_a5_abschnitt_meldet_null_treffer_als_kein_befund():
    text = "\n".join(backtest.a5_abschnitt({"kerzen": 1000, "anders": 0}))
    assert "0 Treffer -> kein Befund" in text
    assert "Kein Schalter, keine Gitterzeile" in text
    assert "Gitterzeile mit genau einem" not in text


def test_a5_abschnitt_meldet_treffer_ohne_gitter_als_nicht_gemessen():
    text = "\n".join(backtest.a5_abschnitt({"kerzen": 1000, "anders": 7}))
    assert "**7**" in text
    assert "nicht gemessen" in text
    assert "Kein Befund" not in text


def _a5_grid_daten():
    def r(label, rendite, dd, n=5):
        return ({"label": label}, [{}] * n, {}, {"rendite_pct": rendite,
                                                  "max_drawdown_pct": dd})

    def h(label, h1, h2):
        return ({"label": label}, {"rendite_pct": h1}, {"rendite_pct": h2})

    res = [r("LIVE", 25.0, -9.9), r(backtest.A5_LIVE, 28.0, -10.2)]
    hal = [h("LIVE", 20.0, 5.0), h(backtest.A5_LIVE, 21.5, 6.2)]
    return res, hal


def test_a5_abschnitt_meldet_urteil_und_kein_urteil():
    res, hal = _a5_grid_daten()
    umkl = {"kerzen": 1177, "anders": 53}
    text = "\n".join(backtest.a5_abschnitt(umkl, res, hal, "LIVE"))
    assert "Regel erfuellt" in text and "high_exit_hist=\"live\"" in text
    hal2 = list(hal)
    hal2[1] = ({"label": backtest.A5_LIVE}, {"rendite_pct": 21.5}, {"rendite_pct": 5.5})
    text = "\n".join(backtest.a5_abschnitt(umkl, res, hal2, "LIVE"))
    assert "bleibt auf `\"voll\"`" in text


def test_a5_abschnitt_ohne_zeile_im_gitter_sagt_nicht_gemessen():
    text = "\n".join(backtest.a5_abschnitt({"kerzen": 1000, "anders": 7}, [], [], "LIVE"))
    assert "nicht gemessen" in text


def test_a5_einschalten_folgt_derselben_regel_wie_e43():
    live = _hz(10.0, 5.0)
    assert backtest.a5_einschalten(live, _hz(11.0, 6.0))["einschalten"] is True
    assert backtest.a5_einschalten(live, _hz(11.0, 5.9))["einschalten"] is False
    assert backtest.a5_einschalten(live, _hz(9.0, 4.0))["einschalten"] is False


def test_a5_zeile_unterscheidet_sich_in_genau_einem_punkt_von_live():
    assert "high_exit_hist" in backtest.EVAL_KEYS and backtest._BASE["high_exit_hist"] == "voll"
    panel = [v for v in backtest.GRID if v.get("panel")][0]
    basis = {k: panel[k] for k in backtest.EVAL_KEYS if k in panel}
    z = _zeile(backtest.A5_LIVE)
    hier = {k: z[k] for k in backtest.EVAL_KEYS if k in z}
    abweichend = {k for k in set(basis) | set(hier) if basis.get(k) != hier.get(k)}
    assert abweichend == {"high_exit_hist"}, abweichend
    assert hier["high_exit_hist"] == "live"


def test_a5_live_konfig_steht_auf_voll():
    import json
    from pathlib import Path
    cfg_datei = Path(__file__).resolve().parent.parent / "site" / "data" / "config.json"
    if not cfg_datei.exists():
        print("  UEBERSPRUNGEN: site/data/config.json fehlt - high_exit_hist ungeprueft!")
        return
    cfg = json.loads(cfg_datei.read_text(encoding="utf-8"))
    assert cfg.get("high_exit_hist") == "voll"
    assert "_hinweis_high_exit_hist" in cfg


def test_a5_ist_im_bericht_verdrahtet():
    import inspect
    q = inspect.getsource(backtest.main)
    assert "a5_next_pivot_beyond(candles, eff_start)" in q
    assert 'a5_abschnitt(_a5, results, halves, panel_cfg["label"])' in q
