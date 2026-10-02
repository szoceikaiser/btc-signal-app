"""E44.3 (27.09.2026): Tests fuer E42 "Ausbruch mit Ruecktest" (Kaisers Regel).

Regel und Werte: docs/PLAN-E44-KOMBINATIONEN.md, Abschnitt 6 K1 und 10. Kaiser hat die
drei Werte am 26.09.2026 bestaetigt (12 Kerzen Ruecktest-Fenster, 25 % Rueckkauf, Stop bei
Schluss unter der Marke) und am 27.09.2026 entschieden: der Stop an der Marke gilt NUR fuer
die zurueckgekauften 25 %.

Jeder Test prueft zuerst, dass sein Szenario den Zweig ueberhaupt erreicht (Vorprobe,
Arbeitsregel 2). Die Gegenproben stehen in sabotage_e443.py.
"""
import json
import tempfile
from pathlib import Path

import backtest
import main
from strategy_core import (Candle, FibZones, FlowPoint, Impulse, Pivot, PosState, Position,
                           RUECKKAUF_TRANCHE, RUECKTEST_FENSTER, SignalType, Signal,
                           bestand_nach, evaluate, kerzen_seit, ruecktest_schritt)
from telegram_notify import ZEILE_MAX, format_plan, format_ruecktest, format_signal
from test_strategy_core import H4_MS, e13_szenario

# --------------------------------------------------------------------- Szenarien

# e13_szenario: Impuls 97,6 -> 130,5, KAUF 1 an der 0.5 (Kerze 25). Das bestaetigte
# Pivot-Hoch ist das Kerzenhoch 130 * 1,004 = 130,52 - die Marke fuer high_exit.
MARKE = 130 * 1.004

# Die Live-Zeile (site/data/config.json), soweit sie im Kleinen etwas bewirkt.
LIVE = dict(bias_short=False, pivot_n=2, tp_ladder=True, buy_ladder=True, trail_stop=True,
            high_exit="on", no_flip=True, neustart_mit_rest=True, zonen_nachziehen=True,
            stop_rueckeroberung=1, liq_entry="boost", min_stop_pct=0.02,
            bein_richtung="bias", min_bein_pct=0.05)

# Anlauf ans Hoch; Kerze 30 verkauft am letzten Hoch und SCHLIESST darueber (= Ausbruch),
# Kerze 31 kommt bis 130,8 zurueck (Zone bis 131,17) und schliesst bei 131 (Ruecktest).
ANLAUF = [118, 122, 126, 129.5, 131.5, (131, 130.8)]
K_VERKAUF, K_RUECKKAUF = 30, 31


def bau(schritte, basis=None):
    """e13_szenario, danach Schlusskurse; ein Tupel (Schluss, Tief) setzt das Tief selbst.
    Hoch/Tief sonst 0,1 % um Eroeffnung und Schluss."""
    cs, fl = basis or e13_szenario()
    cs, fl = list(cs), list(fl)
    for st in schritte:
        ts, o = cs[-1].ts + H4_MS, cs[-1].close
        v, lo = st if isinstance(st, tuple) else (st, min(o, st) * 0.999)
        cs.append(Candle(ts, o, max(o, v) * 1.001, lo, v))
        f = fl[-1]
        fl.append(FlowPoint(ts, f.spot_cvd - 30, 0.0, f.oi + 1e6, f.funding))
    return cs, fl


def lauf(cs, fl, **kw):
    """Kerze fuer Kerze durch evaluate(). Gibt [(Kerze, Signal)], [(Kerze, Meldung)], pos."""
    pos = Position()
    sig, mel = [], []
    for i in range(len(cs)):
        sig += [(i, s) for s in evaluate(cs[:i + 1], fl[:i + 1], pos, **kw)]
        mel += [(i, m) for m in pos.e42_meldungen]
    return sig, mel, pos


def typen(sig, *t):
    return [(i, s) for i, s in sig if s.type in t]


def an(**kw):
    return {**LIVE, "ausbruch_ruecktest": True, **kw}


def spiegel(cs):
    """Short-Spiegelbild: Preis p -> 300 - p, Hoch und Tief tauschen die Rollen."""
    return [Candle(x.ts, 300 - x.open, 300 - x.low, 300 - x.high, 300 - x.close) for x in cs]


# ------------------------------------------------ ruecktest_schritt (reine Funktion)

def _k(close, low=None, high=None):
    low = close * 0.999 if low is None else low
    high = close * 1.001 if high is None else high
    return Candle(0, close, high, low, close)


def test_ausbruch_nur_bei_schluss_ueber_der_marke_nicht_beim_docht():
    assert ruecktest_schritt(100.0, True, None, _k(100.5)) == "ausbruch"
    assert ruecktest_schritt(100.0, True, None, _k(99.8, high=101.0)) == ""      # nur Docht
    assert ruecktest_schritt(100.0, True, None, _k(100.0)) == ""                 # genau drauf


def test_ruecktest_zone_und_docht_regel():
    # Zone: Tief bis Marke +0,5 % (100,5); Schluss darf nicht unter der Marke liegen
    assert ruecktest_schritt(100.0, True, 3, _k(101.0, low=100.45)) == "ruecktest"
    assert ruecktest_schritt(100.0, True, 3, _k(101.0, low=99.0)) == "ruecktest"  # Docht
    assert ruecktest_schritt(100.0, True, 3, _k(100.0, low=99.5)) == "ruecktest"  # Schluss = Marke
    assert ruecktest_schritt(100.0, True, 3, _k(101.0, low=100.6)) == ""          # nicht beruehrt
    assert ruecktest_schritt(100.0, True, 3, _k(99.9, low=99.5)) == "gescheitert"


def test_ruecktest_fenster_zaehlt_zwoelf_kerzen():
    assert RUECKTEST_FENSTER == 12                                   # Kaiser: 2 Tage
    frei = _k(105.0, low=104.0)
    assert ruecktest_schritt(100.0, True, 11, frei) == ""
    assert ruecktest_schritt(100.0, True, 12, frei) == "verfallen"   # letzte Fensterkerze bewertet
    assert ruecktest_schritt(100.0, True, 12, _k(101.0, low=100.2)) == "ruecktest"
    assert ruecktest_schritt(100.0, True, 13, _k(101.0, low=100.2)) == "verfallen"
    assert ruecktest_schritt(100.0, True, 6, frei, fenster=6) == "verfallen"   # Robustheitszeile


def test_ruecktest_schritt_short_spiegelbildlich():
    assert ruecktest_schritt(100.0, False, None, _k(99.5)) == "ausbruch"
    assert ruecktest_schritt(100.0, False, None, _k(100.2, low=99.0)) == ""
    assert ruecktest_schritt(100.0, False, 2, _k(99.0, high=99.5)) == "ruecktest"
    assert ruecktest_schritt(100.0, False, 2, _k(99.0, high=99.4)) == ""
    assert ruecktest_schritt(100.0, False, 2, _k(100.1, high=100.4)) == "gescheitert"


def test_kerzen_seit_zaehlt_in_der_liste():
    cs = [Candle(t, 1, 1, 1, 1) for t in (10, 20, 30, 40)]
    assert kerzen_seit(cs, 40, 13) == 0
    assert kerzen_seit(cs, 20, 13) == 2
    assert kerzen_seit(cs, 20, 2) == 2          # ausserhalb der Grenze -> Grenze
    assert kerzen_seit(cs, 5, 13) == 13         # nicht gefunden -> aelter als die Grenze


def test_bestand_nach_kaeufe_teilverkaeufe_und_voller_ausstieg():
    s = lambda t, p: Signal(0, t, 1.0, p, "")
    assert bestand_nach(0, [s(SignalType.KAUF_2, 75), s(SignalType.NACHKAUF, 25),
                            s(SignalType.NACHKAUF, 15)]) == 100         # nie ueber 100
    assert bestand_nach(100, [s(SignalType.TEILVERKAUF_LADDER, 15),
                              s(SignalType.RUECKKAUF, 25)]) == 100
    assert bestand_nach(50, [s(SignalType.RUECKKAUF_STOP, 25)]) == 25
    assert bestand_nach(80, [s(SignalType.VERKAUF_REST, 20)]) == 0
    assert bestand_nach(10, [s(SignalType.TEILVERKAUF_1, 40)]) == 0     # nie unter 0


# ------------------------------------------------------ durch evaluate(): Long

def test_default_aus_exakt_dieselben_signale_und_keine_beobachtung():
    cs, fl = bau(ANLAUF + [130.0, 129.8, 128])
    fass = lambda sig: [(i, s.type, round(s.price, 6), s.tranche_pct, s.reason) for i, s in sig]
    ohne, _m, pos_ohne = lauf(cs, fl, **LIVE)
    aus, _m, pos_aus = lauf(cs, fl, **LIVE, ausbruch_ruecktest=False, ruecktest_fenster=12)
    mit, _m, _p = lauf(cs, fl, **an())
    assert typen(mit, SignalType.RUECKKAUF), "Vorprobe: das Szenario erzeugt keinen Rueckkauf"
    assert fass(aus) == fass(ohne) and fass(mit) != fass(ohne)
    assert pos_aus.e42_marke is None and pos_aus.e42_teil_marke is None
    assert pos_aus.e42_gekauft is None


def test_rueckkauf_nach_teilverkauf_am_hoch_ausbruch_und_ruecktest():
    cs, fl = bau(ANLAUF)
    sig, mel, pos = lauf(cs, fl, **an())
    hoch = [(i, s) for i, s in sig if "Teilgewinn am letzten Hoch" in s.reason]
    assert hoch and hoch[0][0] == K_VERKAUF, "Vorprobe: kein Teilverkauf am letzten Hoch"
    assert "beobachte Ausbruch ueber" in hoch[0][1].reason
    assert (K_VERKAUF, "ausbruch") in [(i, m["art"]) for i, m in mel]
    rk = typen(sig, SignalType.RUECKKAUF)
    assert [i for i, _s in rk] == [K_RUECKKAUF]
    s = rk[0][1]
    assert s.tranche_pct == RUECKKAUF_TRANCHE == 25
    assert s.price == cs[K_RUECKKAUF].close                  # zum Schluss der Ruecktest-Kerze
    assert abs(s.stop_ref - MARKE) < 1e-9
    assert abs(pos.e42_teil_marke - MARKE) < 1e-9 and abs(pos.e42_gekauft - MARKE) < 1e-9
    assert pos.e42_marke is None                             # Beobachtung beendet


def test_rueckkauf_aendert_weder_einstand_noch_hauptstop():
    """Kaiser 27.09.2026: der Stop an der Marke gilt nur fuer die 25 %. Der Rest der
    Position behaelt Einstand und Stop - auch der nachgezogene Stop darf nicht wandern."""
    cs, fl = bau(ANLAUF)
    _s, _m, ohne = lauf(cs, fl, **LIVE)
    sig, _m, mit = lauf(cs, fl, **an())
    assert typen(sig, SignalType.RUECKKAUF), "Vorprobe"
    assert (mit.entry_ref, mit.entry_pct) == (ohne.entry_ref, ohne.entry_pct)
    assert mit.zones.invalidation == ohne.zones.invalidation
    assert mit.state == ohne.state
    assert mit.bestand_pct == ohne.bestand_pct + RUECKKAUF_TRANCHE


def test_die_ausbruchskerze_selbst_ist_nie_der_ruecktest():
    """Der Verkauf schliesst UNTER der Marke; die Ausbruchskerze kommt von unten und
    beruehrt die Zone dabei zwangslaeufig. Danach kein Ruecktest mehr -> kein Rueckkauf."""
    # Kerzen 30 und 31 verkaufen am Hoch und schliessen darunter (high_exit ist danach
    # verbraucht), Kerze 32 bricht von unten aus, danach nur noch hoeher.
    cs, fl = bau([118, 122, 126, 128, 130.0, 129.5, 131.6] + [133 + k for k in range(12)])
    sig, mel, pos = lauf(cs, fl, **an(tp_ladder=False))
    hoch = [i for i, s in sig if "Teilgewinn am letzten Hoch" in s.reason]
    aus = [i for i, m in mel if m["art"] == "ausbruch"]
    assert hoch == [30, 31] and aus == [32], (hoch, aus)     # Vorprobe
    assert cs[32].low <= MARKE * 1.005 and cs[32].close > MARKE   # Ausbruchskerze beruehrt
    assert not typen(sig, SignalType.RUECKKAUF)
    assert (44, "verfallen") in [(i, m["art"]) for i, m in mel]   # 12 Kerzen nach Kerze 32
    assert pos.e42_marke is None


def test_schluss_unter_der_marke_im_fenster_scheitert_dann_neuer_ausbruch():
    cs, fl = bau(ANLAUF[:-1] + [(130.0, 129.9), 132, (131.5, 130.9)])
    sig, mel, _pos = lauf(cs, fl, **an())
    arten = [(i, m["art"]) for i, m in mel]
    assert (K_VERKAUF, "ausbruch") in arten and (31, "gescheitert") in arten, arten
    assert (32, "ausbruch") in arten
    assert [i for i, _s in typen(sig, SignalType.RUECKKAUF)] == [33]


def test_die_verkaufskerze_ist_nie_der_ruecktest_auch_ohne_no_flip():
    """Schliesst die Verkaufskerze schon ueber der Marke, ist sie der Ausbruch - und damit
    nie der Ruecktest, obwohl ihr Tief die Zone beruehrt. Mit no_flip (live) verdeckt die
    Gegengeschaeft-Sperre das, deshalb hier ohne."""
    cs, fl = bau(ANLAUF)
    assert cs[K_VERKAUF].low <= MARKE * 1.005 and cs[K_VERKAUF].close > MARKE   # Vorprobe
    sig, mel, _pos = lauf(cs, fl, **an(no_flip=False))
    assert (K_VERKAUF, "ausbruch") in [(i, m["art"]) for i, m in mel]
    assert [i for i, _s in typen(sig, SignalType.RUECKKAUF)] == [K_RUECKKAUF]


def _beobachtung(cs, ausbruch_idx):
    """Offene Position (ohne Teilverkaeufe am Hoch), Marke beobachtet, Ausbruch in Kerze
    `ausbruch_idx` - damit kein neuer Verkauf die Beobachtung neu startet."""
    p = _voll_pos(cs, 60)
    p.state, p.last_signal_ts = PosState.CORE, cs[ausbruch_idx].ts
    p.e42_start_ts, p.e42_ausbruch_ts = cs[ausbruch_idx - 1].ts, cs[ausbruch_idx].ts
    return p


def test_nach_gescheitertem_ausbruch_braucht_es_einen_neuen():
    """Schluss unter der Marke beendet den Ausbruch. Die naechste Kerze, die von unten
    ueber die Marke schliesst, ist ein NEUER Ausbruch - kein Ruecktest des alten, obwohl
    ihr Tief die Zone beruehrt. Erst die Kerze danach kann der Ruecktest sein."""
    cs, fl = bau([118, 122, 126, 129.5, 131.5, (130.0, 129.9), 132, (131.5, 130.9)])
    kw = an(tp_ladder=False, high_exit="off", buy_ladder=False, liq_entry="off")
    pos = _beobachtung(cs, 30)
    arten, rk = [], []
    for i in range(31, len(cs)):
        sigs = evaluate(cs[:i + 1], fl[:i + 1], pos, **kw)
        arten += [(i, m["art"]) for m in pos.e42_meldungen]
        rk += [i for s in sigs if s.type == SignalType.RUECKKAUF]
    assert (31, "gescheitert") in arten, arten                            # Vorprobe
    assert cs[32].low <= MARKE * 1.005 and cs[32].close > MARKE           # 32 beruehrt die Zone
    assert (32, "ausbruch") in arten and rk == [33], (arten, rk)


def test_ruecktest_nach_dem_fenster_kauft_nicht():
    hoch_bleiben = [133 + k * 0.5 for k in range(12)]
    cs, fl = bau(ANLAUF[:-1] + hoch_bleiben + [(134, 130.6)])
    sig, mel, _pos = lauf(cs, fl, **an(tp_ladder=False))
    assert (K_VERKAUF + 12, "verfallen") in [(i, m["art"]) for i, m in mel]
    assert cs[-1].low <= MARKE * 1.005                                    # Vorprobe
    assert not typen(sig, SignalType.RUECKKAUF)
    # Gegenprobe: mit einer Kerze mehr Fenster waere es ein Ruecktest
    sig13, _m, _p = lauf(cs, fl, **an(tp_ladder=False, ruecktest_fenster=13))
    assert [i for i, _s in typen(sig13, SignalType.RUECKKAUF)] == [len(cs) - 1]


def test_stop_nur_fuer_den_rueckkauf_teil_mit_rueckeroberung():
    cs, fl = bau(ANLAUF + [130.0, 129.8])
    sig, mel, pos = lauf(cs, fl, **an())
    assert typen(sig, SignalType.RUECKKAUF), "Vorprobe"
    assert (32, "teil_wartet") in [(i, m["art"]) for i, m in mel]
    st = typen(sig, SignalType.RUECKKAUF_STOP)
    assert [i for i, _s in st] == [33]                     # erst die zweite Kerze darunter
    assert st[0][1].tranche_pct == 25 and "Rest der Position" in st[0][1].reason
    assert not typen(sig, SignalType.STOPLOSS)
    assert pos.state != PosState.FLAT and pos.entry_pct == 25      # Rest laeuft weiter
    assert pos.e42_teil_marke is None
    # ohne Rueckeroberungs-Regel: schon die erste Kerze darunter
    sig0, _m, _p = lauf(cs, fl, **an(stop_rueckeroberung=0))
    assert [i for i, _s in typen(sig0, SignalType.RUECKKAUF_STOP)] == [32]


def test_zurueckeroberte_marke_ist_geprueft_naechster_bruch_sofort():
    cs, fl = bau(ANLAUF + [130.0, 131.0, 130.0])
    sig, mel, _pos = lauf(cs, fl, **an())
    arten = [(i, m["art"]) for i, m in mel]
    assert (32, "teil_wartet") in arten and (33, "teil_zurueck") in arten, arten
    st = typen(sig, SignalType.RUECKKAUF_STOP)
    assert [i for i, _s in st] == [34] and "schon einmal" in st[0][1].reason


def test_teil_stop_harter_boden_sofort():
    cs, fl = bau(ANLAUF + [(123.0, 122.5)])            # mehr als 5 % unter der Marke
    sig, _m, _pos = lauf(cs, fl, **an())
    assert [i for i, _s in typen(sig, SignalType.RUECKKAUF_STOP)] == [32]


def test_kein_zweiter_rueckkauf_auf_dieselbe_marke():
    """Nach dem Stop des Teils kommt der Kurs zurueck: Ausbruch und Ruecktest an derselben
    Marke - aber auf sie wurde schon zurueckgekauft."""
    pos = Position()
    cs, fl = bau(ANLAUF + [130.0, 129.8])
    for i in range(len(cs)):
        evaluate(cs[:i + 1], fl[:i + 1], pos, **an())
    assert abs(pos.e42_gekauft - MARKE) < 1e-9, "Vorprobe"
    # dieselbe Marke erneut beobachten (wie nach einem weiteren Teilverkauf dort)
    pos.e42_marke, pos.e42_richtung = MARKE, "LONG"
    pos.e42_start_ts, pos.e42_ausbruch_ts = cs[-1].ts, cs[-1].ts
    cs2, fl2 = bau([(131.0, 130.7)], basis=(cs, fl))
    sigs = evaluate(cs2, fl2, pos, **an())
    assert not [s for s in sigs if s.type == SignalType.RUECKKAUF]
    assert [m["art"] for m in pos.e42_meldungen] == ["ohne_kauf"]


def test_keine_beobachtung_einer_marke_auf_die_schon_zurueckgekauft_wurde():
    cs, fl = bau([118, 122, 126, 129.5, 130.0])           # Kerze 30 verkauft am Hoch
    frei, schon = Position(), Position(e42_gekauft=MARKE)
    for i in range(len(cs)):
        s_frei = evaluate(cs[:i + 1], fl[:i + 1], frei, **an())
        s_schon = evaluate(cs[:i + 1], fl[:i + 1], schon, **an())
    assert abs(frei.e42_marke - MARKE) < 1e-9, "Vorprobe: ohne Rueckkauf wird beobachtet"
    assert "beobachte" in s_frei[0].reason
    assert schon.e42_marke is None and "beobachte" not in s_schon[0].reason


def test_no_flip_kein_nachkauf_in_der_kerze_des_teil_stops():
    """Der Stop des Rueckkauf-Teils ist ein Verkauf. Faellt der Kurs in derselben Kerze
    bis in die 0.786-Zone, waere der Nachkauf dort ein Gegengeschaeft."""
    cs, fl = bau([118, 122, 126, 129.5, 131.5, (110.0, 104.0)])
    kw = an(tp_ladder=False, high_exit="off", buy_ladder=False, liq_entry="off")

    def _pos():
        p = _voll_pos(cs, 50)
        p.state, p.e42_marke = PosState.CORE, None
        p.e42_teil_marke = MARKE
        return p
    ohne = _pos()
    sigs = evaluate(cs, fl, ohne, **{**kw, "no_flip": False})
    assert {s.type for s in sigs} == {SignalType.RUECKKAUF_STOP, SignalType.NACHKAUF}, \
        "Vorprobe: Teil-Stop und 0.786-Nachkauf in einer Kerze"
    mit = _pos()
    sigs = evaluate(cs, fl, mit, **kw)
    assert [s.type for s in sigs] == [SignalType.RUECKKAUF_STOP]


def _voll_pos(cs, bestand):
    """Offene Long-Position mit laufender Beobachtung, Ausbruch in der vorletzten Kerze."""
    z = FibZones(Impulse(Pivot(0, 0, 97.6, "L"), Pivot(9, cs[9].ts, MARKE, "H")),
                 level_05=114.06, gp_upper=110.2, gp_lower=109.1, level_0786=104.6,
                 invalidation=97.6)
    return Position(direction="LONG", state=PosState.FULL, zones=z, retrace_extreme=113.0,
                    last_signal_ts=cs[-2].ts, entry_ref=110.0, entry_pct=100,
                    bestand_pct=bestand, e42_marke=MARKE, e42_richtung="LONG",
                    e42_start_ts=cs[-3].ts, e42_ausbruch_ts=cs[-2].ts)


def test_nicht_wenn_schon_voll_investiert():
    cs, fl = bau([118, 122, 126, 129.5, 131.5, (131, 130.8)])
    kw = an(tp_ladder=False, high_exit="off", buy_ladder=False, liq_entry="off")
    halb = _voll_pos(cs, 85)
    sigs = evaluate(cs, fl, halb, **kw)
    assert [s.type for s in sigs] == [SignalType.RUECKKAUF], "Vorprobe: mit 85 % wird gekauft"
    voll = _voll_pos(cs, 100)
    sigs = evaluate(cs, fl, voll, **kw)
    assert not [s for s in sigs if s.type == SignalType.RUECKKAUF]
    assert voll.e42_meldungen[0]["art"] == "ohne_kauf"
    assert "voll investiert" in voll.e42_meldungen[0]["grund"]
    assert voll.e42_marke is None


def test_no_flip_kein_rueckkauf_in_einer_kerze_mit_teilverkauf():
    """Die Ruecktest-Kerze erreicht zugleich ein Leiter-Ziel. Mit no_flip (live) kein
    Gegengeschaeft: der Teilverkauf kommt, der Rueckkauf nicht - das Fenster laeuft weiter."""
    cs, fl = bau([118, 122, 126, 129.5, 131.5, (131, 130.8)])
    kw = an(high_exit="off", buy_ladder=False, liq_entry="off")
    # Leiter-Ziel 0.8: retrace_extreme + 0.8 * 32,9 -> knapp unter dem Hoch der Kerze
    p = _voll_pos(cs, 85)
    p.retrace_extreme = cs[-1].high - 0.8 * (MARKE - 97.6) - 0.01
    sigs = evaluate(cs, fl, p, **kw)
    assert [s.type for s in sigs] == [SignalType.TEILVERKAUF_LADDER], [s.type for s in sigs]
    assert p.e42_marke is not None                        # Beobachtung laeuft weiter
    q = _voll_pos(cs, 85)
    q.retrace_extreme = p.retrace_extreme
    sigs = evaluate(cs, fl, q, **{**kw, "no_flip": False})
    assert {s.type for s in sigs} == {SignalType.TEILVERKAUF_LADDER, SignalType.RUECKKAUF}


def test_hauptstop_nimmt_den_rueckkauf_teil_mit():
    """Loest der Stop der Position aus, geht der Teil mit ihr - und darf danach nicht als
    offener Teil weiterleben (er wuerde spaeter einen Stop auf nichts ausloesen)."""
    cs, fl = bau(ANLAUF + [(92.0, 91.0)])          # mehr als 5 % unter der Invalidierung
    sig, _m, pos = lauf(cs, fl, **an())
    assert typen(sig, SignalType.RUECKKAUF), "Vorprobe"
    assert [s.type for i, s in sig if i == len(cs) - 1] == [SignalType.STOPLOSS]
    assert pos.state == PosState.FLAT
    assert pos.e42_teil_marke is None and pos.bestand_pct == 0
    assert abs(pos.e42_gekauft - MARKE) < 1e-9        # die Erinnerung bleibt


def test_nach_einem_stop_keine_beobachtung():
    cs, fl = bau(ANLAUF[:-1] + [133, 134])
    pos = Position()
    for i in range(len(cs)):
        evaluate(cs[:i + 1], fl[:i + 1], pos, **an(tp_ladder=False))
    assert pos.e42_marke is not None and pos.e42_ausbruch_ts >= 0, "Vorprobe"
    cs2, fl2 = bau([(92.0, 91.0)], basis=(cs, fl))   # > 5 % unter der Invalidierung: sofort
    sigs = evaluate(cs2, fl2, pos, **an(tp_ladder=False))
    assert [s.type for s in sigs] == [SignalType.STOPLOSS]
    assert pos.e42_marke is None and pos.e42_ausbruch_ts == -1


# ------------------------------------------- aus FLAT: nach einem Rest-Verkauf

def _flat_pfad(nach):
    """Aelteres Hoch 125 (Pivot), dann Bein 100 -> 110, KAUF 1 und 2, Extension 1.0 und
    im selben Zug der Rest-Verkauf (Gegen-Muster SHORT_COVERING) bei 113,5."""
    from test_strategy_core import zigzag_candles, c
    vor = [c(0, 116, 117, 115, 116), c(1, 116, 118, 115.5, 117), c(2, 118, 125, 117.5, 120),
           c(3, 120, 121, 110, 111), c(4, 111, 112, 104.5, 105)]
    zz = [Candle(x.ts + 5, x.open, x.high, x.low, x.close) for x in zigzag_candles()]
    rest = [c(13, 106, 106.5, 104.5, 105.5), c(14, 105, 105.5, 103.6, 104.5),
            c(15, 104, 114.0, 104.0, 113.5), c(16, 113, 118.0, 112.0, 117.0)]
    cs = vor + zz + rest + [c(17 + k, *x) for k, x in enumerate(nach)]
    fl = [FlowPoint(i, 100 + i, 0, 1000 - i * 30, -0.0001) for i in range(len(cs))]
    return cs, fl


FLAT_KW = dict(pivot_n=2, bias_short=False, tp_ladder=False, buy_ladder=False,
               flush_entry="off", bein_richtung="bias", stop_rueckeroberung=1)
FLAT_NACH = [(117, 126.5, 116.5, 126), (126, 126.8, 125.3, 126.2),
             (126.2, 127, 124, 124.5), (124.5, 124.8, 123, 123.5)]


def test_aus_flat_nach_rest_verkauf_rueckkauf_eroeffnet_neue_position():
    cs, fl = _flat_pfad(FLAT_NACH[:2])
    sig, mel, pos = lauf(cs, fl, **FLAT_KW, ausbruch_ruecktest=True)
    rest = typen(sig, SignalType.VERKAUF_REST)
    assert rest and "beobachte Ausbruch ueber 125" in rest[0][1].reason, "Vorprobe"
    assert [i for i, _s in typen(sig, SignalType.RUECKKAUF)] == [18]
    assert pos.direction == "LONG" and pos.state == PosState.T1
    assert pos.zones is not None and pos.zones.impulse.up          # Ziele vom aktuellen Bein
    assert pos.retrace_extreme == cs[18].low                       # Extension vom Ruecktest aus
    assert pos.entry_pct == 0 and pos.bestand_pct == 25
    ohne, _m, pos_ohne = lauf(cs, fl, **FLAT_KW)
    assert pos_ohne.state == PosState.FLAT                         # ohne E42: draussen


def test_aus_flat_stop_des_teils_ist_voller_ausstieg():
    """Besteht die Position nur aus dem Rueckkauf, darf keine leere Position mit Zonen
    stehen bleiben - die wuerde spaeter 'aufstocken'."""
    cs, fl = _flat_pfad(FLAT_NACH)
    sig, mel, pos = lauf(cs, fl, **FLAT_KW, ausbruch_ruecktest=True)
    assert typen(sig, SignalType.RUECKKAUF), "Vorprobe"
    st = typen(sig, SignalType.STOPLOSS)
    assert [i for i, _s in st] == [20] and st[0][1].tranche_pct == 100
    assert "Rueckkauf-Teil" in st[0][1].reason
    assert not typen(sig, SignalType.RUECKKAUF_STOP)
    assert pos.state == PosState.FLAT and pos.last_stop_ts == cs[20].ts
    wartet = [m for i, m in mel if m["art"] == "teil_wartet"]
    assert [i for i, m in mel if m["art"] == "teil_wartet"] == [19]
    assert wartet[0]["nur_rueckkauf"] is True       # Telegram: "besteht nur aus diesem Teil"


def test_aus_flat_ohne_passendes_bein_kein_rueckkauf():
    cs, fl = _flat_pfad(FLAT_NACH[:2])
    kw = {**FLAT_KW, "bein_richtung": "auto"}      # juengstes Bein ist hier abwaerts
    sig, mel, _pos = lauf(cs, fl, **kw, ausbruch_ruecktest=True)
    assert (17, "ausbruch") in [(i, m["art"]) for i, m in mel], "Vorprobe"
    assert not typen(sig, SignalType.RUECKKAUF)
    assert [m["grund"] for i, m in mel if m["art"] == "ohne_kauf"] == [
        "es gibt kein Bein fuer die Ziele"]


# ---------------------------------------------------------------- Short-Spiegel

def test_short_spiegelbildlich():
    cs, fl = bau(ANLAUF + [130.0, 129.8])
    cs = spiegel(cs)
    sig, mel, pos = lauf(cs, fl, **{**an(), "bias_long": False, "bias_short": True})
    tief = [(i, s) for i, s in sig if "Teilgewinn am letzten Tief" in s.reason]
    assert tief and "Durchbruch unter" in tief[0][1].reason, "Vorprobe"
    rk = typen(sig, SignalType.SHORT_RUECKTEST)
    assert [i for i, _s in rk] == [K_RUECKKAUF]
    assert abs(rk[0][1].stop_ref - (300 - MARKE)) < 1e-9
    assert [i for i, _s in typen(sig, SignalType.SHORT_RUECKTEST_STOP)] == [33]
    assert not typen(sig, SignalType.RUECKKAUF, SignalType.RUECKKAUF_STOP)
    assert pos.direction == "SHORT" and pos.state != PosState.FLAT


# ----------------------------------------------------------- Live-Engine (main)

def test_zustand_ueberlebt_den_neustart_der_live_engine():
    pos = Position(direction="LONG", entry_pct=75)
    pos.e42_marke, pos.e42_richtung, pos.e42_start_ts, pos.e42_ausbruch_ts = 70000.0, "LONG", 5, 6
    pos.e42_gekauft, pos.e42_teil_marke = 68000.0, 69000.0
    pos.e42_teil_wartet, pos.e42_teil_wartet_inv, pos.e42_teil_geprueft = 1, 69000.0, 68500.0
    pos.bestand_pct = 60
    rt = main.pos_from_state(main.pos_to_state(pos))
    felder = ("e42_marke", "e42_richtung", "e42_start_ts", "e42_ausbruch_ts", "e42_gekauft",
              "e42_teil_marke", "e42_teil_wartet", "e42_teil_wartet_inv", "e42_teil_geprueft",
              "bestand_pct")
    assert [getattr(rt, f) for f in felder] == [getattr(pos, f) for f in felder]
    alt = main.pos_from_state({"pos_state": "CORE", "direction": "LONG", "entry_pct": 130})
    assert (alt.e42_marke, alt.e42_ausbruch_ts, alt.e42_teil_marke) == (None, -1, None)
    assert alt.bestand_pct == 100          # Altbestand: aus den Kaeufen geschaetzt, eher "voll"


def _live(cs, fl, cfg, start, schrittweise):
    """Die Live-Engine ueber die Kursfolge - am Stueck oder jede Kerze als eigener Lauf
    (neuer Prozess, Zustand aus state.json). Gibt die gesendeten Texte in Reihenfolge und
    die Signale zurueck. Plan und Vorschau kommen je LAUF, nicht je Kerze, und sind daher
    ausgenommen (wie beim E41-Pruefweg)."""
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
    finally:
        main.send_text, main.send_signals, main.send_plan, main.send_vorschau = alt
    return texte, signale


LIVE_CFG = {**LIVE, "ausbruch_ruecktest": True}


def test_live_am_stueck_gleich_kerze_fuer_kerze_nach_high_exit():
    """DER Pruefweg (Arbeitsregeln): Beobachtung, Ausbruch, Rueckkauf, Warten, Rueck-
    eroberung und Stop des Teils ueber viele Laeufe. Ginge ein Merker zwischen zwei Laeufen
    verloren, wichen Signale oder Meldungen ab."""
    cs, fl = bau(ANLAUF + [130.0, 131.0, 130.0, 128.5])
    t1, s1 = _live(cs, fl, LIVE_CFG, 24, schrittweise=False)
    t2, s2 = _live(cs, fl, LIVE_CFG, 24, schrittweise=True)
    typ = [x["type"] for x in s2]
    assert "RUECKKAUF" in typ and "RUECKKAUF_STOP" in typ, typ          # Vorprobe
    kopf = [t.splitlines()[0] for t in t2]
    for k in ("AUSBRUCH UEBER", "STOP RUECKKAUF-TEIL WARTET", "AUSBRUCHSMARKE ZURUECKEROBERT"):
        assert any(k in x for x in kopf), (k, kopf)
    fass = lambda s: [(x["ts"], x["type"], round(x["price"], 6), x["tranche_pct"], x["reason"])
                      for x in s]
    assert fass(s1) == fass(s2)
    assert t1 == t2


def test_live_am_stueck_gleich_kerze_fuer_kerze_aus_flat():
    cs, fl = _flat_pfad(FLAT_NACH)
    cfg = {**FLAT_KW, "ausbruch_ruecktest": True}
    t1, s1 = _live(cs, fl, cfg, 12, schrittweise=False)
    t2, s2 = _live(cs, fl, cfg, 12, schrittweise=True)
    assert "RUECKKAUF" in [x["type"] for x in s2], "Vorprobe"
    assert [(x["ts"], x["type"], x["reason"]) for x in s1] == \
           [(x["ts"], x["type"], x["reason"]) for x in s2]
    assert t1 == t2


def test_live_meldungen_stehen_je_kerze_vor_ihren_signalen():
    """Holt ein Lauf viele Kerzen nach, muss 'Ausbruch' vor dem Rueckkauf und 'wartet'
    vor dem Stop des Teils stehen - dieselbe Folge wie bei vier Stunden Abstand."""
    cs, fl = bau(ANLAUF + [130.0, 129.8])
    texte, _s = _live(cs, fl, LIVE_CFG, 24, schrittweise=False)
    kopf = [t.splitlines()[0] for t in texte]
    i_aus = next(i for i, k in enumerate(kopf) if "AUSBRUCH UEBER" in k)
    i_rk = next(i for i, k in enumerate(kopf) if k.endswith(SignalType.RUECKKAUF.value))
    i_w = next(i for i, k in enumerate(kopf) if "RUECKKAUF-TEIL WARTET" in k)
    i_st = next(i for i, k in enumerate(kopf) if k.endswith(SignalType.RUECKKAUF_STOP.value))
    assert i_aus < i_rk < i_w < i_st, kopf


def test_plan_nennt_den_stop_des_rueckkauf_teils():
    cs, fl = bau(ANLAUF)
    pos = Position()
    for i in range(len(cs)):
        evaluate(cs[:i + 1], fl[:i + 1], pos, **an())
    assert pos.e42_teil_marke is not None, "Vorprobe"
    plan = main.positions_plan(cs, fl, LIVE_CFG, pos)
    teil = plan["rueckkauf_teil"]
    assert abs(teil["marke"] - MARKE) < 1e-9 and teil["tranche"] == 25
    assert teil["rueckeroberung"] == 1 and teil["nur_rueckkauf"] is False
    assert plan["anteil_pct"] == pos.entry_pct + 25              # der Rueckkauf zaehlt im Kopf mit
    text = " ".join(format_plan(plan).split())
    assert "Rueckkauf-Teil (25 %): Stop 131 $" in text
    assert "Gilt nur fuer diesen Teil" in text
    # Der Plan meldet sich neu, sobald der Teil dazukommt oder verschwindet
    ohne = {k: v for k, v in plan.items() if k != "rueckkauf_teil"}
    assert main.plan_geaendert(ohne, plan) and main.plan_geaendert(plan, ohne)
    assert not main.plan_geaendert(plan, plan)


def test_plan_ohne_e42_unveraendert():
    cs, fl = bau(ANLAUF)
    pos = Position()
    for i in range(len(cs)):
        evaluate(cs[:i + 1], fl[:i + 1], pos, **LIVE)
    plan = main.positions_plan(cs, fl, LIVE, pos)
    assert plan is not None, "Vorprobe"
    assert "rueckkauf_teil" not in plan and "ruecktest" not in plan


# ------------------------------------------------------------------- Telegram

def _m(art, **kw):
    return {"art": art, "ts": 1_700_000_000_000, "kurs": 70800.0, "marke": 70000.0,
            "lang": True, "fenster": 12, "zone": 70350.0, "tranche": 25, **kw}


def test_meldungen_sagen_was_passiert_und_passen_aufs_handy():
    faelle = {
        "ausbruch": ["AUSBRUCH UEBER 70.000 $", "naechsten 12 Kerzen (2 Tage) bis 70.350 $",
                     "kauft die Engine 25 % zurueck", "Stop fuer diesen Teil: Schluss unter"],
        "gescheitert": ["AUSBRUCH GESCHEITERT", "kein Rueckkauf", "neuen Schluss ueber 70.000 $"],
        "verfallen": ["KEIN RUECKTEST", "In 12 Kerzen (2 Tage)", "Beobachtung ist beendet"],
        "ohne_kauf": ["RUECKTEST OHNE RUECKKAUF", "schon voll investiert"],
        "teil_wartet": ["STOP RUECKKAUF-TEIL WARTET", "Sonst wird der Rueckkauf-Teil verkauft",
                        "Der Rest der Position ist davon nicht betroffen"],
        "teil_zurueck": ["AUSBRUCHSMARKE ZURUECKEROBERT", "verkauft den Rueckkauf-Teil sofort"],
    }
    for art, soll in faelle.items():
        txt = format_ruecktest(_m(art, grund="die Engine ist schon voll investiert",
                                  noch=1, boden=66500.0))
        einzeilig = " ".join(txt.split())
        for s in soll:
            assert s in einzeilig, (art, s)
        zu_lang = [z for z in txt.splitlines()[1:] if len(z) > ZEILE_MAX]
        assert not zu_lang, (art, zu_lang)


def test_meldung_short_und_nur_rueckkauf():
    txt = " ".join(format_ruecktest(_m("ausbruch", lang=False, zone=69650.0)).split())
    assert "DURCHBRUCH UNTER 70.000 $" in txt and "nicht ueber 70.000 $" in txt
    w = " ".join(format_ruecktest(_m("teil_wartet", nur_rueckkauf=True, noch=1,
                                     boden=66500.0)).split())
    assert "Die Position besteht nur aus diesem Teil." in w


# ---------------------------------------------------------- Backtest-Abrechnung

def _cs(n=6, p=100.0):
    return [Candle(1_756_684_800_000 + i * H4_MS, p, p, p, p) for i in range(n)]


def _sig(i, t, preis, tr):
    return {"ts": 1_756_684_800_000 + i * H4_MS, "type": t, "price": preis, "tranche_pct": tr}


def test_simulate_stop_des_teils_verkauft_genau_den_rueckkauf():
    cs = _cs()
    s0 = backtest.simulate([_sig(0, "KAUF_1", 100.0, 25)], cs, fee=0.0,
                           start_ms=cs[0].ts)
    s1 = backtest.simulate([_sig(0, "KAUF_1", 100.0, 25), _sig(1, "RUECKKAUF", 100.0, 25),
                            _sig(2, "RUECKKAUF_STOP", 100.0, 25)], cs, fee=0.0,
                           start_ms=cs[0].ts)
    # Vorprobe: der Rueckkauf wurde wirklich gebucht (sonst beweist Gleichheit nichts)
    s_rk = backtest.simulate([_sig(0, "KAUF_1", 100.0, 25), _sig(1, "RUECKKAUF", 100.0, 25)],
                             cs, fee=0.0, start_ms=cs[0].ts)
    assert abs(s_rk["offene_position"] - 2 * s0["offene_position"]) < 1e-6
    assert abs(s1["offene_position"] - s0["offene_position"]) < 1e-6
    assert s1["trades"] == 1


def test_simulate_teilverkauf_nimmt_den_rueckkauf_anteilig_mit():
    cs = _cs()
    sig = [_sig(0, "KAUF_1", 100.0, 25), _sig(1, "RUECKKAUF", 100.0, 25),
           _sig(2, "TEILVERKAUF_1", 100.0, 40), _sig(3, "RUECKKAUF_STOP", 100.0, 25)]
    s = backtest.simulate(sig, cs, fee=0.0, start_ms=cs[0].ts)
    # 50 Einheiten-Anteile, Teilverkauf 40 % vom Hoechstbestand = 20 -> Rest 30, davon die
    # Haelfte aus dem Rueckkauf (15). Der Stop des Teils verkauft 15 -> es bleiben 15.
    voll = backtest.simulate([_sig(0, "KAUF_1", 100.0, 25)], cs, fee=0.0, start_ms=cs[0].ts)
    einheit = voll["offene_position"] / 25
    assert abs(s["offene_position"] - 15 * einheit) < 1e-6


def test_simulate_short_rueckteil():
    # A5: retain every original assertion only in explicit legacy reproduction mode.
    cs = _cs()[:-1] + [Candle(_cs()[-1].ts, 80.0, 80.0, 80.0, 80.0)]   # Schluss 80
    s0 = backtest.simulate([_sig(0, "SHORT_1", 100.0, 25)], cs, fee=0.0, start_ms=cs[0].ts, legacy_derivatives=True)
    s_rt = backtest.simulate([_sig(0, "SHORT_1", 100.0, 25),
                              _sig(1, "SHORT_RUECKTEST", 100.0, 25)], cs, fee=0.0,
                             start_ms=cs[0].ts, legacy_derivatives=True)
    s1 = backtest.simulate([_sig(0, "SHORT_1", 100.0, 25), _sig(1, "SHORT_RUECKTEST", 100.0, 25),
                            _sig(2, "SHORT_RUECKTEST_STOP", 100.0, 25)], cs, fee=0.0,
                           start_ms=cs[0].ts, legacy_derivatives=True)
    assert abs(s_rt["offene_position"] - 2 * s0["offene_position"]) < 1e-6   # Vorprobe
    assert s1["short_trades"] == 1
    # offene Short-Position wieder genau die aus SHORT_1
    assert abs(s1["offene_position"] - s0["offene_position"]) < 1e-6


def test_gegengeschaeft_zaehlt_rueckkauf_und_stop_des_teils_mit():
    ts = 1_756_684_800_000
    g = backtest.gegengeschaefte([
        {"ts": ts, "type": "RUECKKAUF", "price": 100.0},
        {"ts": ts, "type": "TEILVERKAUF_LADDER", "price": 101.0},
        {"ts": ts + H4_MS, "type": "RUECKKAUF_STOP", "price": 99.0},
        {"ts": ts + H4_MS, "type": "NACHKAUF", "price": 99.0}])
    assert g["kerzen"] == 2 and g["gleicher_preis"] == 1
