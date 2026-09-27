"""E44.4 (27.09.2026): Tests fuer verkauf_faktor (Plan E44, Abschnitt 6 K2).

Furkan (Juli-B 19:14): Verkaufs-Tranchen nach oben kleiner. Ein Faktor verkleinert jeden
Teilverkauf; der Rest bleibt groesser investiert. Default 1.0 = bisheriges Verhalten (live),
Messwert 0.67 - gemessen wird erst in E44.5.

Jeder Test prueft zuerst, dass sein Szenario den Zweig ueberhaupt erreicht (Vorprobe,
Arbeitsregel 2). Die Gegenproben stehen in sabotage_e444.py.
"""
import json
import math
import tempfile
from pathlib import Path

import backtest
import main
from strategy_core import (LADDER_TRANCHE, TRANCHEN, VERKAUF_FAKTOR, Position, Signal,
                           SignalType, evaluate, pruefe_verkauf_faktor, teilverkauf_tranche,
                           verkleinere_teilverkaeufe)
from telegram_notify import format_plan, format_signal
from test_e443 import ANLAUF, LIVE, H4_MS, an, bau, lauf, spiegel, typen

MESSWERT = 0.67

# Anlauf ans letzte Hoch (Teilverkauf am Hoch, Kerze 30), dann weiter hinauf: Leiter 0.8
# und 0.9 (Kerze 34, 35), Ziel 1.0 (36) und Ziel 1.618 (40). Damit sind alle Teilverkaufs-
# Groessen der Live-Zeile dabei: 15 % (Hoch, Leiter) und 40 % (beide Ziele).
STEIG = ANLAUF + [134, 138, 142, 146, 149, 153, 158, 163, 168, 170, 166, 160]
TEIL = (SignalType.TEILVERKAUF_LADDER, SignalType.TEILVERKAUF_1, SignalType.TEILVERKAUF_2)


def _fass(sig):
    """Was ausser der Groesse an einem Signal haengt: Kerze, Art, Preis, Begruendung."""
    return [(i, s.type, round(s.price, 9), s.reason) for i, s in sig]


# ------------------------------------------------ die Rechenstelle (reine Funktionen)

def test_teilverkauf_tranche_rundet_auf_ganze_prozent():
    assert VERKAUF_FAKTOR == 1.0                                  # Default = bisher
    assert (LADDER_TRANCHE, TRANCHEN["TP1"], TRANCHEN["TP2"]) == (15, 40, 40)
    assert teilverkauf_tranche(15) == 15 and teilverkauf_tranche(40) == 40
    assert teilverkauf_tranche(15, 1.0) == 15 and teilverkauf_tranche(40, 1.0) == 40
    # Messwert: 15 x 0,67 = 10,05 -> 10; 40 x 0,67 = 26,8 -> 27
    assert teilverkauf_tranche(15, MESSWERT) == 10
    assert teilverkauf_tranche(40, MESSWERT) == 27
    assert teilverkauf_tranche(15, 0.5) == 8                      # 7,5 -> kaufmaennisch 8
    assert teilverkauf_tranche(40, 0.5) == 20
    assert teilverkauf_tranche(15, 0.01) == 1                     # nie 0 - sonst kein Verkauf
    assert isinstance(teilverkauf_tranche(40, MESSWERT), int)     # Telegram: ganze Prozent


def test_pruefe_verkauf_faktor_nur_groesser_null_bis_eins():
    for gut in (MESSWERT, 1.0, 0.01):
        pruefe_verkauf_faktor(gut)
    for schlecht in (0.0, -0.5, 1.01, 1.5, math.nan):
        try:
            pruefe_verkauf_faktor(schlecht)
        except ValueError:
            continue
        raise AssertionError(f"{schlecht!r} haette abgelehnt werden muessen")
    cs, fl = bau([])
    try:
        evaluate(cs, fl, Position(), verkauf_faktor=1.5)
    except ValueError:
        pass
    else:
        raise AssertionError("evaluate muss einen Faktor ueber 1 ablehnen")


def test_verkleinert_nur_teilverkaeufe_long_und_short():
    s = lambda t, p: Signal(0, t, 1.0, p, "")
    sig = [s(SignalType.TEILVERKAUF_LADDER, 15), s(SignalType.TEILVERKAUF_1, 40),
           s(SignalType.TEILVERKAUF_2, 40), s(SignalType.SHORT_TP_LADDER, 15),
           s(SignalType.SHORT_TP_1, 40), s(SignalType.SHORT_TP_2, 40),
           # keine Teilverkaeufe: volle Ausstiege, Stop des Rueckkauf-Teils, Kaeufe, Warnung
           s(SignalType.STOPLOSS, 100), s(SignalType.VERKAUF_REST, 20),
           s(SignalType.SHORT_STOPLOSS, 100), s(SignalType.SHORT_COVER_REST, 20),
           s(SignalType.RUECKKAUF_STOP, 25), s(SignalType.SHORT_RUECKTEST_STOP, 25),
           s(SignalType.KAUF_1, 25), s(SignalType.NACHKAUF, 15), s(SignalType.RUECKKAUF, 25),
           s(SignalType.SHORT_1, 25), s(SignalType.WARNUNG, 0)]
    verkleinere_teilverkaeufe(sig, MESSWERT)
    assert [x.tranche_pct for x in sig] == [10, 27, 27, 10, 27, 27,
                                            100, 20, 100, 20, 25, 25, 25, 15, 25, 25, 0]
    verkleinere_teilverkaeufe(sig, 1.0)                     # 1.0 -> nichts, auch nicht runden
    assert [x.tranche_pct for x in sig][:3] == [10, 27, 27]


# --------------------------------------------------------- Einbindung in evaluate

def test_default_exakt_dieselben_signale():
    cs, fl = bau(STEIG)
    ohne, _m, pos_ohne = lauf(cs, fl, **LIVE)
    mit, _m, pos_mit = lauf(cs, fl, **LIVE, verkauf_faktor=1.0)
    assert {s.type for _i, s in ohne} >= set(TEIL), "Vorprobe: alle Teilverkaufs-Arten"
    assert [(i, s.to_dict()) for i, s in ohne] == [(i, s.to_dict()) for i, s in mit]
    assert pos_ohne.bestand_pct == pos_mit.bestand_pct


def test_faktor_aendert_nur_die_groesse_nicht_zeitpunkt_art_oder_preis():
    cs, fl = bau(STEIG)
    alt, _m, _p = lauf(cs, fl, **LIVE)
    neu, _m, _p = lauf(cs, fl, **LIVE, verkauf_faktor=MESSWERT)
    teil_alt = [(i, s) for i, s in alt if s.type in TEIL]
    assert len(teil_alt) == 5, "Vorprobe: Hoch, Leiter 0.8, Leiter 0.9, Ziel 1.0, Ziel 1.618"
    assert "Teilgewinn am letzten Hoch" in teil_alt[0][1].reason           # high_exit dabei
    assert _fass(alt) == _fass(neu)
    for (_i, a), (_j, n) in zip(alt, neu):
        erwartet = teilverkauf_tranche(a.tranche_pct, MESSWERT) if a.type in TEIL \
            else a.tranche_pct
        assert n.tranche_pct == erwartet, (a.type, a.tranche_pct, n.tranche_pct)
    assert [s.tranche_pct for _i, s in neu if s.type in TEIL] == [10, 10, 10, 27, 27]


def test_bestand_sieht_die_verkleinerte_groesse():
    """bestand_pct gilt ueber viele Kerzen (state.json) und entscheidet bei E42 ueber
    'schon voll investiert'. Er muss die Groesse zaehlen, die Telegram meldet."""
    cs, fl = bau(ANLAUF[:5])                      # KAUF 1 (25 %), Teilverkauf am Hoch (Kerze 30)
    sig, _m, pos = lauf(cs, fl, **LIVE, verkauf_faktor=MESSWERT)
    assert [s.tranche_pct for _i, s in typen(sig, SignalType.TEILVERKAUF_LADDER)] == [10], \
        "Vorprobe"
    assert pos.bestand_pct == 25 - 10
    _s, _m, pos_alt = lauf(cs, fl, **LIVE)
    assert pos_alt.bestand_pct == 25 - 15


def test_mit_e42_nur_die_groesse_anders():
    """Zusammen mit E44.3 (Rueckkauf) - so wird E44.5 die Zeile 'E42 + K2' rechnen."""
    cs, fl = bau(STEIG)
    alt, m_alt, _p = lauf(cs, fl, **an())
    neu, m_neu, _p = lauf(cs, fl, **an(verkauf_faktor=MESSWERT))
    assert typen(alt, SignalType.RUECKKAUF), "Vorprobe: Rueckkauf dabei"
    assert _fass(alt) == _fass(neu) and m_alt == m_neu
    assert [s.tranche_pct for _i, s in typen(neu, SignalType.RUECKKAUF)] == [25]  # Kauf bleibt


def test_short_spiegelbildlich():
    cs, fl = bau(STEIG)
    cs = spiegel(cs)
    kw = {**LIVE, "bias_long": False, "bias_short": True}
    alt, _m, _p = lauf(cs, fl, **kw)
    neu, _m, _p = lauf(cs, fl, **kw, verkauf_faktor=MESSWERT)
    st = (SignalType.SHORT_TP_LADDER, SignalType.SHORT_TP_1, SignalType.SHORT_TP_2)
    assert {s.type for _i, s in alt} >= set(st), "Vorprobe: alle Short-Teilgewinne"
    assert not any(s.type in TEIL for _i, s in alt)
    assert _fass(alt) == _fass(neu)
    assert [s.tranche_pct for _i, s in typen(neu, *st)] == [10, 10, 10, 27, 27]


# ------------------------------------------------------------- Live-Engine (main)

def test_eval_params_faktor_aus_config_und_unbrauchbare_werte():
    assert main.EVAL_DEFAULTS["verkauf_faktor"] == 1.0
    assert main.eval_params({})["verkauf_faktor"] == 1.0
    assert main.eval_params({"verkauf_faktor": MESSWERT})["verkauf_faktor"] == MESSWERT
    assert main.eval_params({"verkauf_faktor": "0.67"})["verkauf_faktor"] == MESSWERT
    # Kaiser bearbeitet die Datei von Hand: ein falscher Wert darf den Lauf nicht abbrechen
    for schlecht in (0, -1, 1.5, "0,67", None, "nan"):
        assert main.eval_params({"verkauf_faktor": schlecht})["verkauf_faktor"] == 1.0, schlecht


def test_config_json_noch_nicht_live():
    cfg = json.loads((Path(main.__file__).resolve().parent.parent / "site" / "data"
                      / "config.json").read_text(encoding="utf-8"))
    assert cfg["verkauf_faktor"] == 1.0                     # Kaiser: noch NICHT live schalten
    assert main.eval_params(cfg)["verkauf_faktor"] == 1.0
    h = cfg["_hinweis_verkauf_faktor"]
    assert "E44.4" in h and "0.67" in h and "E44.5" in h and "NOCH NICHT GEMESSEN" in h


def test_plan_nennt_die_verkleinerten_teilgewinne():
    """Die Plan-Nachricht sagt 'diese Preise kannst du hinterlegen' - mit Groesse. Sie muss
    dieselbe Groesse nennen, die das Signal spaeter meldet."""
    cs, fl = bau(ANLAUF[:4])                                # offen, vor dem Hoch
    pos = Position()
    for i in range(len(cs)):
        evaluate(cs[:i + 1], fl[:i + 1], pos, **LIVE, verkauf_faktor=MESSWERT)
    assert pos.direction == "LONG", "Vorprobe"
    groesse = lambda plan: {e["was"].split(" ")[0]: e["tranche"] for e in plan["teilgewinn"]}
    alt = groesse(main.positions_plan(cs, fl, LIVE, pos))
    neu_plan = main.positions_plan(cs, fl, {**LIVE, "verkauf_faktor": MESSWERT}, pos)
    neu = groesse(neu_plan)
    assert {"kurz", "Zwischenziel", "Ziel", "Widerstand"} <= set(alt), ("Vorprobe", alt)
    assert alt["kurz"] == alt["Zwischenziel"] == 15 and alt["Ziel"] == 40
    assert neu["kurz"] == neu["Zwischenziel"] == 10 and neu["Ziel"] == 27
    assert alt["Widerstand"] == neu["Widerstand"] == 0       # nur Hinweis, verkauft nicht
    text = " ".join(format_plan(neu_plan).split())
    assert "(27 %)" in text and "(10 %)" in text and "(40 %)" not in text


def test_telegram_signal_nennt_die_verkleinerte_tranche():
    cs, fl = bau(STEIG)
    sig, _m, _p = lauf(cs, fl, **LIVE, verkauf_faktor=MESSWERT)
    tp1 = typen(sig, SignalType.TEILVERKAUF_1)
    assert tp1, "Vorprobe"
    assert "Tranche: 27 % der Position" in format_signal(tp1[0][1].to_dict())


def _live(cs, fl, cfg, start, schrittweise):
    """Live-Engine ueber die Kursfolge, am Stueck oder jede Kerze als eigener Lauf (neuer
    Prozess, Zustand aus state.json). Gibt Texte, Signale und den Zustand am Ende zurueck.
    Plan und Vorschau kommen je LAUF, nicht je Kerze - ausgenommen wie beim E41-Pruefweg."""
    texte, signale = [], []
    alt = (main.send_text, main.send_signals, main.send_plan, main.send_vorschau)
    main.send_text = lambda t, dry_run=False: texte.append(t)
    main.send_signals = lambda s, dry_run=False: (
        texte.extend(format_signal(x) for x in s), signale.extend(s))
    main.send_plan = main.send_vorschau = lambda *a, **k: None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "config.json").write_text(json.dumps(cfg))
            for k in (range(start, len(cs) + 1) if schrittweise else [len(cs)]):
                main.run_engine(fetch=lambda oi=None, k=k: (cs[:k], fl[:k], []),
                                data_dir=d, dry_run=True)
            zustand = json.loads((d / "state.json").read_text(encoding="utf-8"))
    finally:
        main.send_text, main.send_signals, main.send_plan, main.send_vorschau = alt
    return texte, signale, zustand


def test_live_am_stueck_gleich_kerze_fuer_kerze_mit_faktor():
    """DER Pruefweg (Arbeitsregeln): verkauf_faktor ist eine Einstellung, kein Zustand -
    ueber Kerzen wirkt er nur ueber bestand_pct (state.json). Am Stueck und Kerze fuer
    Kerze muessen Signale, Telegram-Texte und der Zustand gleich sein, mit E42 dabei."""
    cs, fl = bau(STEIG)
    cfg = {**LIVE, "ausbruch_ruecktest": True, "verkauf_faktor": MESSWERT}
    t1, s1, z1 = _live(cs, fl, cfg, 24, schrittweise=False)
    t2, s2, z2 = _live(cs, fl, cfg, 24, schrittweise=True)
    teil = [x for x in s2 if x["type"] in {t.name for t in TEIL}]
    assert [x["tranche_pct"] for x in teil] == [10, 10, 10, 27, 27], "Vorprobe"
    assert "RUECKKAUF" in [x["type"] for x in s2], "Vorprobe: E42 dabei"
    assert sum("Tranche: 27 % der Position" in t for t in t2) == 2
    fass = lambda s: [(x["ts"], x["type"], round(x["price"], 6), x["tranche_pct"], x["reason"])
                      for x in s]
    assert fass(s1) == fass(s2)
    assert t1 == t2
    assert z1["bestand_pct"] == z2["bestand_pct"] == 0     # 25+25 gekauft, 10+10+10+27+27 verkauft
    assert {k: v for k, v in z1.items() if k != "updated_at"} == \
           {k: v for k, v in z2.items() if k != "updated_at"}


def test_live_ohne_faktor_in_der_config_wie_bisher():
    cs, fl = bau(STEIG)
    cfg = {**LIVE, "ausbruch_ruecktest": True}
    t_alt, s_alt, _z = _live(cs, fl, cfg, 24, schrittweise=False)
    t_neu, s_neu, _z = _live(cs, fl, {**cfg, "verkauf_faktor": 1.0}, 24, schrittweise=False)
    assert [x["tranche_pct"] for x in s_alt if x["type"] == "TEILVERKAUF_1"] == [40], "Vorprobe"
    assert s_alt == s_neu and t_alt == t_neu


# ---------------------------------------------------------- Backtest-Abrechnung

def _cs(n=6, p=100.0):
    from strategy_core import Candle
    return [Candle(1_756_684_800_000 + i * H4_MS, p, p, p, p) for i in range(n)]


def _sig(i, t, preis, tr=None):
    d = {"ts": 1_756_684_800_000 + i * H4_MS, "type": t, "price": preis}
    if tr is not None:
        d["tranche_pct"] = tr
    return d


def _rest(sig, cs):
    """Offene Einheiten nach den Signalen, in Einheiten des ersten Kaufs (100 %)."""
    voll = backtest.simulate([sig[0]], cs, fee=0.0, start_ms=cs[0].ts)["offene_position"]
    return backtest.simulate(sig, cs, fee=0.0, start_ms=cs[0].ts)["offene_position"] / voll


def test_simulate_bucht_die_groesse_aus_dem_signal():
    cs = _cs()
    k = _sig(0, "KAUF_1", 100.0, 25)
    # bisher: 40 % bzw. 15 % vom Hoechstbestand
    assert abs(_rest([k, _sig(1, "TEILVERKAUF_1", 100.0, 40)], cs) - 0.60) < 1e-9
    assert abs(_rest([k, _sig(1, "TEILVERKAUF_LADDER", 100.0, 15)], cs) - 0.85) < 1e-9
    # E44.4: die Groesse aus dem Signal
    assert abs(_rest([k, _sig(1, "TEILVERKAUF_1", 100.0, 27)], cs) - 0.73) < 1e-9
    assert abs(_rest([k, _sig(1, "TEILVERKAUF_2", 100.0, 27)], cs) - 0.73) < 1e-9
    assert abs(_rest([k, _sig(1, "TEILVERKAUF_LADDER", 100.0, 10)], cs) - 0.90) < 1e-9
    # vom HOECHSTbestand, nicht vom Rest: 27 % + 27 % -> 46 % bleiben
    assert abs(_rest([k, _sig(1, "TEILVERKAUF_1", 100.0, 27),
                      _sig(2, "TEILVERKAUF_2", 100.0, 27)], cs) - 0.46) < 1e-9
    # volle Ausstiege verkaufen weiter alles, egal was im Signal steht
    assert _rest([k, _sig(1, "VERKAUF_REST", 100.0, 20)], cs) == 0.0


def test_simulate_ohne_angabe_die_bisherigen_groessen():
    cs = _cs()
    k = _sig(0, "KAUF_1", 100.0, 25)
    assert abs(_rest([k, _sig(1, "TEILVERKAUF_1", 100.0)], cs) - 0.60) < 1e-9
    assert abs(_rest([k, _sig(1, "TEILVERKAUF_2", 100.0)], cs) - 0.60) < 1e-9
    assert abs(_rest([k, _sig(1, "TEILVERKAUF_LADDER", 100.0)], cs) - 0.85) < 1e-9


def test_simulate_short_bucht_die_groesse_aus_dem_signal():
    cs = _cs(p=100.0)[:-1] + _cs(p=80.0)[-1:]          # Schluss 80: der Short liegt im Plus
    k = _sig(0, "SHORT_1", 100.0, 25)
    assert abs(_rest([k, _sig(1, "SHORT_TP_1", 100.0, 27)], cs) - 0.73) < 1e-9
    assert abs(_rest([k, _sig(1, "SHORT_TP_2", 100.0, 40)], cs) - 0.60) < 1e-9
    assert abs(_rest([k, _sig(1, "SHORT_TP_LADDER", 100.0, 10)], cs) - 0.90) < 1e-9
    assert abs(_rest([k, _sig(1, "SHORT_TP_LADDER", 100.0)], cs) - 0.85) < 1e-9


def test_backtest_zeile_reicht_den_faktor_durch():
    """E44.5 baut die Gitterzeilen mit V(..., verkauf_faktor=0.67) - der Wert muss bei
    evaluate() ankommen und in der Abrechnung wirken."""
    assert "verkauf_faktor" in backtest.EVAL_KEYS and backtest._BASE["verkauf_faktor"] == 1.0
    cs, fl = bau(STEIG)
    alt = backtest.run_backtest(cs, fl, backtest.V("live", **LIVE), start_ms=cs[0].ts)
    neu = backtest.run_backtest(cs, fl, backtest.V("k2", **LIVE, verkauf_faktor=MESSWERT),
                                start_ms=cs[0].ts)
    assert [x["tranche_pct"] for x in alt if x["type"] == "TEILVERKAUF_1"] == [40], "Vorprobe"
    assert [x["tranche_pct"] for x in neu if x["type"] == "TEILVERKAUF_1"] == [27]
    p_alt = backtest.simulate(alt, cs, start_ms=cs[0].ts)
    p_neu = backtest.simulate(neu, cs, start_ms=cs[0].ts)
    assert p_neu["offene_position"] > p_alt["offene_position"]      # der Rest ist groesser
