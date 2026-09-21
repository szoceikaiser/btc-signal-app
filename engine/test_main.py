"""Offline-Tests fuer main.py (Orchestrierung, State-Persistenz, Dedupe).

Netzwerkzugriff wird durch eine Fake-Fetch-Funktion ersetzt.
"""

import json
import tempfile
from pathlib import Path

from strategy_core import Candle, FlowPoint
import main
from main import pos_from_state, pos_to_state, run_engine

TS0 = 1_700_000_000_000
H4 = 4 * 3600 * 1000


def _c(i, o, h, l, cl):
    return Candle(TS0 + i * H4, o, h, l, cl)


def szenario(oi_history=None):
    """Impuls 100->110 (Pivots mit n=5 bestaetigt), letzte Kerze beruehrt 0.5-Level.

    Signatur wie fetch_market_data: nimmt die OI-Historie, gibt sie (ergaenzt) zurueck.
    """
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
    oi_history = list(oi_history or []) + [[candles[-1].ts, 1000.0]]
    return candles, flow, oi_history


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
        # E20: die Widerstandsmarken muessen im State stehen (Schluessel vorhanden, auch
        # wenn im kleinen Testszenario kein Gegen-Bein erkennbar ist)
        assert "widerstand" in state


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


# ------------------------------------------------- Zonen-Vorschau (Kaisers Befund 29.07.)

def _vorschau_kerzen():
    """Klarer Impuls 98 -> 130, danach Rueckgang: die Zonen muessen berechenbar sein."""
    ms = 4 * 3600 * 1000
    werte = [100, 99, 98, 99, 104, 110, 116, 122, 128, 130] + [130 - i for i in range(1, 12)]
    return [Candle(1_600_000_000_000 + i * ms, v, v * 1.004, v * 0.996, v)
            for i, v in enumerate(werte)]


def test_zonen_vorschau_auch_ohne_position():
    """Die Levels muessen sichtbar sein, BEVOR eine Position offen ist.

    Sonst kann man die Limit-Order nicht vorab platzieren — und genau darauf sind die
    meisten Kaufsignale angewiesen, weil sie ein Level nennen, das die Kerze nur
    beruehrt hat (das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben).
    """
    z = main.zonen_vorschau(_vorschau_kerzen(), {"pivot_n": 2})
    assert z is not None, "keine Zonen berechnet"
    assert z["richtung"] == "LONG"
    # Impuls 97,6 -> 130,5; 0.5 dazwischen, Golden Pocket darunter, Invalidierung am Tief
    assert z["invalidation"] < z["level_0786"] < z["gp_lower"] < z["gp_upper"] < z["level_05"]
    assert abs(z["level_05"] - 114.06) < 0.5, z


def test_zonen_vorschau_ohne_impuls_ist_none():
    """Ohne erkennbaren Impuls lieber nichts anzeigen als etwas Erfundenes."""
    ms = 4 * 3600 * 1000
    flach = [Candle(1_600_000_000_000 + i * ms, 100, 100.1, 99.9, 100) for i in range(30)]
    assert main.zonen_vorschau(flach, {"pivot_n": 2}) is None


def test_state_enthaelt_vorschau_auch_im_zustand_flat():
    """Ende-zu-Ende: nach einem Lauf ohne Position steht die Vorschau im state.json."""
    cs = _vorschau_kerzen()
    fl = [FlowPoint(c.ts, 1000.0 + i * 10, 0.0, 1e9, -0.0001) for i, c in enumerate(cs)]
    with tempfile.TemporaryDirectory() as d:
        ordner = Path(d)
        (ordner / "config.json").write_text(json.dumps({"pivot_n": 2}), encoding="utf-8")
        main.run_engine(fetch=lambda oi=None: (cs, fl, []), data_dir=ordner, dry_run=True)
        state = json.loads((ordner / "state.json").read_text(encoding="utf-8"))
    assert state["zonen_vorschau"] is not None, "Vorschau fehlt im state.json"
    assert "level_05" in state["zonen_vorschau"] and "gp_upper" in state["zonen_vorschau"]


def _lauf(ordner, cs, fl, cfg=None):
    """Ein Engine-Lauf in einem Testordner; gibt den geschriebenen state zurueck."""
    if cfg is not None:
        (ordner / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    main.run_engine(fetch=lambda oi=None: (cs, fl, []), data_dir=ordner, dry_run=True)
    return json.loads((ordner / "state.json").read_text(encoding="utf-8"))


def test_vorschau_wird_nur_bei_NEUER_struktur_gesendet(capsysless=None):
    """Die Ankuendigung darf nicht bei jedem Lauf kommen — sonst 6 gleiche Nachrichten/Tag.

    Zweiter Lauf mit denselben Kerzen = dieselbe Struktur = keine zweite Nachricht.
    """
    cs = _vorschau_kerzen()
    fl = [FlowPoint(c.ts, 1000.0 + i * 10, 0.0, 1e9, -0.0001) for i, c in enumerate(cs)]
    gesendet = []
    echt = main.send_vorschau
    main.send_vorschau = lambda z, ts, dry_run=False: gesendet.append(z) or ""
    try:
        with tempfile.TemporaryDirectory() as d:
            ordner = Path(d)
            _lauf(ordner, cs, fl, {"pivot_n": 2})
            assert len(gesendet) == 1, "erste Vorschau fehlt"
            _lauf(ordner, cs, fl)                       # gleiche Kerzen, gleiche Struktur
            assert len(gesendet) == 1, "Vorschau wurde erneut gesendet, obwohl nichts neu war"
    finally:
        main.send_vorschau = echt


def test_vorschau_abschaltbar():
    cs = _vorschau_kerzen()
    fl = [FlowPoint(c.ts, 1000.0 + i * 10, 0.0, 1e9, -0.0001) for i, c in enumerate(cs)]
    gesendet = []
    echt = main.send_vorschau
    main.send_vorschau = lambda z, ts, dry_run=False: gesendet.append(z) or ""
    try:
        with tempfile.TemporaryDirectory() as d:
            _lauf(Path(d), cs, fl, {"pivot_n": 2, "vorschau_telegram": False})
            assert gesendet == [], "Vorschau trotz vorschau_telegram=false gesendet"
    finally:
        main.send_vorschau = echt


def test_vorschau_nachricht_enthaelt_die_wichtigen_zahlen():
    from telegram_notify import format_vorschau
    z = main.zonen_vorschau(_vorschau_kerzen(), {"pivot_n": 2})
    text = format_vorschau(z, 1_600_000_000_000)
    for muss in ("VORSCHAU", "KEIN Trigger", "0.5-Level", "Golden Pocket",
                 "0.786", "Ungueltig ab", "Limit-Order"):
        assert muss in text, f"'{muss}' fehlt in der Nachricht:\n{text}"
    # Die Zahlen selbst muessen drinstehen, nicht nur die Begriffe
    assert f"{z['level_05']:,.0f}".replace(",", ".") in text


def test_vorschau_warnt_bei_zu_engem_stop():
    """Liegt der Stop naeher als 2 %, steigt die Engine nicht ein — das muss dranstehen,
    sonst legt man eine Limit-Order fuer ein Setup, das nie genommen wird."""
    from telegram_notify import format_vorschau
    eng = {"richtung": "LONG", "impuls_start": 100, "impuls_ende": 101,
           "level_05": 100.5, "gp_upper": 100.4, "gp_lower": 100.35,
           "level_0786": 100.2, "invalidation": 100.0, "abstand_pct": 0.4}
    weit = dict(eng, abstand_pct=3.6)
    assert "steigt hier NICHT ein" in format_vorschau(eng, 1_600_000_000_000)
    assert "steigt hier NICHT ein" not in format_vorschau(weit, 1_600_000_000_000)


# ------------------------------------------------- Flush-Fruehwarnung (Kaiser 29.07.)

MS4H = 4 * 3600 * 1000


def _rohkerze(ts, o, h, l, c):
    """Binance-Rohformat: [open_ts, o, h, l, c, vol, close_ts, ...]"""
    return [ts, str(o), str(h), str(l), str(c), "1", ts + MS4H, "1", 1, "0.5", "1"]


def _wache_szenario(tief, schluss):
    """Fertige Kerzen mit klarem Impuls 97,6 -> 130,5, plus eine LAUFENDE Kerze.

    Golden Pocket liegt bei ~109-110, Invalidierung bei ~97,6. Ueber Tief und
    Schlusskurs der laufenden Kerze steuern die Tests die Flush-Bedingung.
    """
    t0 = 1_600_000_000_000
    werte = [100, 99, 98, 99, 104, 110, 116, 122, 128, 130] + [130 - i for i in range(1, 25)]
    roh = [_rohkerze(t0 + i * MS4H, v, v * 1.004, v * 0.996, v) for i, v in enumerate(werte)]
    lauf_ts = t0 + len(werte) * MS4H
    roh.append(_rohkerze(lauf_ts, 106, 107, tief, schluss))
    # now_ms muss INNERHALB der angehaengten Kerze liegen, sonst gilt die letzte
    # werte-Kerze als "laufend" und der Test prueft etwas anderes als gedacht.
    return roh, lauf_ts, lauf_ts + 1000                  # roh, ts der laufenden, now_ms


def _wache(ordner, roh, now_ms, cfg=None):
    (ordner / "config.json").write_text(json.dumps(cfg or {"pivot_n": 2}), encoding="utf-8")
    gesendet = []
    import telegram_notify
    echt = main.send_text
    main.send_text = lambda t, dry_run=False: gesendet.append(t) or t
    try:
        w = main.watch_flush(data_dir=ordner, dry_run=True, now_ms=now_ms, kerzen_roh=roh)
    finally:
        main.send_text = echt
    return w, gesendet


def test_flush_wache_warnt_wenn_kurs_durch_das_golden_pocket_faellt():
    roh, _lts, now = _wache_szenario(tief=100.0, schluss=106.0)   # unter GP, ueber Inval.
    with tempfile.TemporaryDirectory() as d:
        w, gesendet = _wache(Path(d), roh, now)
    assert w is not None, "keine Warnung, obwohl der Flush sich entwickelt"
    assert len(gesendet) == 1
    assert "FLUSH ENTWICKELT SICH" in gesendet[0]
    assert "noch NICHT bestaetigt" in gesendet[0]


def test_flush_wache_schweigt_ohne_durchbruch():
    roh, _lts, now = _wache_szenario(tief=120.0, schluss=125.0)   # gar nicht im GP
    with tempfile.TemporaryDirectory() as d:
        w, gesendet = _wache(Path(d), roh, now)
    assert w is None and gesendet == []


def test_flush_wache_schweigt_unter_der_invalidierung():
    """Faellt der Kurs unter die Ungueltig-Marke, gibt es keinen Einstieg — also
    auch keine Warnung, sonst weckt man jemanden fuer nichts."""
    roh, _lts, now = _wache_szenario(tief=90.0, schluss=95.0)     # unter Invalidierung
    with tempfile.TemporaryDirectory() as d:
        w, gesendet = _wache(Path(d), roh, now)
    assert w is None and gesendet == []


def test_flush_wache_warnt_nur_einmal_je_kerze():
    """Sonst kaeme die Warnung bei einem laengeren Flush alle 15 Minuten erneut."""
    roh, _lts, now = _wache_szenario(tief=100.0, schluss=106.0)
    with tempfile.TemporaryDirectory() as d:
        ordner = Path(d)
        w1, g1 = _wache(ordner, roh, now)
        w2, g2 = _wache(ordner, roh, now)
    assert w1 is not None and len(g1) == 1
    assert w2 is None and g2 == [], "zweite Warnung fuer dieselbe Kerze gesendet"


def test_flush_wache_schweigt_bei_offener_position():
    """Der Flush-Einstieg feuert nur aus FLAT — bei offener Position waere die
    Warnung irrefuehrend."""
    roh, _lts, now = _wache_szenario(tief=100.0, schluss=106.0)
    with tempfile.TemporaryDirectory() as d:
        ordner = Path(d)
        (ordner / "state.json").write_text(json.dumps({"pos_state": "CORE"}), encoding="utf-8")
        w, gesendet = _wache(ordner, roh, now)
    assert w is None and gesendet == []


def test_flush_wache_beachtet_mindest_stopabstand():
    """Waere der Stop naeher als min_stop_pct, steigt die Engine nicht ein — dann
    darf auch nicht gewarnt werden."""
    roh, _lts, now = _wache_szenario(tief=100.0, schluss=106.0)
    with tempfile.TemporaryDirectory() as d:
        w, g = _wache(Path(d), roh, now, {"pivot_n": 2, "min_stop_pct": 0.99})
    assert w is None and g == []


def test_flush_wache_abschaltbar():
    roh, _lts, now = _wache_szenario(tief=100.0, schluss=106.0)
    with tempfile.TemporaryDirectory() as d:
        w, g = _wache(Path(d), roh, now, {"pivot_n": 2, "flush_wache": False})
    assert w is None and g == []


def test_flush_aufloesung_meldet_nicht_bestaetigt():
    """Nach Kerzenschluss ohne Flush-Signal muss die Entwarnung kommen."""
    from telegram_notify import format_flush_aufloesung
    w = {"preis": 106.0, "invalidation": 97.6}
    assert "KEIN Flush-Einstieg" in format_flush_aufloesung(w, False)
    assert "BESTAETIGT" in format_flush_aufloesung(w, True)


# --------------------------------------------------------------- E18.1 (27.08.2026)

def test_alle_evaluate_parameter_werden_durchgereicht():
    """Jeder Schalter, den evaluate kennt, muss aus config.json ankommen.

    Der Fehler, den dieser Test verhindert (Durchsicht 27.08.2026): run_engine reichte
    nur 11 von 20 Parametern durch. Die uebrigen liessen sich in config.json aendern,
    ohne dass es irgendeine Wirkung hatte — und ohne Fehlermeldung. Kommt spaeter ein
    Parameter zu evaluate dazu und wird hier vergessen, wird dieser Test rot.
    """
    import inspect
    from strategy_core import evaluate
    sig = inspect.signature(evaluate)
    erwartet = {n: p.default for n, p in sig.parameters.items()
                if p.default is not inspect.Parameter.empty}
    fehlen = set(erwartet) - set(main.EVAL_DEFAULTS)
    assert not fehlen, f"nicht durchgereichte evaluate-Parameter: {sorted(fehlen)}"
    zuviel = set(main.EVAL_DEFAULTS) - set(erwartet)
    assert not zuviel, f"unbekannte Parameter in EVAL_DEFAULTS: {sorted(zuviel)}"
    # ... und mit denselben Vorgabewerten, sonst aendert das Durchreichen das Verhalten
    abweichend = {k: (main.EVAL_DEFAULTS[k], erwartet[k])
                  for k in erwartet if main.EVAL_DEFAULTS[k] != erwartet[k]}
    assert not abweichend, f"Vorgabewerte weichen von evaluate ab: {abweichend}"


def test_eval_params_uebernimmt_config_und_ignoriert_hinweise():
    p = main.eval_params({"flush_entry": "off", "pivot_n": 4, "k_atr": 3,
                          "_hinweis": "Text", "flush_wache": True})
    assert p["flush_entry"] == "off"          # war vorher wirkungslos
    assert p["pivot_n"] == 4 and isinstance(p["pivot_n"], int)
    assert p["k_atr"] == 3.0 and isinstance(p["k_atr"], float)
    assert "_hinweis" not in p and "flush_wache" not in p
    assert p["trail_stop"] is False           # nicht gesetzt -> Vorgabewert


def test_eval_params_faengt_unbrauchbare_werte_ab():
    """Ein Tippfehler in config.json darf den Lauf nicht abbrechen."""
    p = main.eval_params({"k_atr": "zwei", "cooldown_h": None})
    assert p["k_atr"] == 2.0 and p["cooldown_h"] == 0.0


def test_leere_config_ergibt_bisheriges_verhalten():
    """Ohne config.json muss exakt das herauskommen, was evaluate ohnehin tut."""
    import inspect
    from strategy_core import evaluate
    sig = inspect.signature(evaluate)
    for name, wert in main.eval_params({}).items():
        assert sig.parameters[name].default == wert, name


def test_ziel_extrem_ueberlebt_den_neustart():
    """E18.3: Die eingefrorene Zielreferenz muss in state.json stehen — sonst rechnet
    die Engine nach dem naechsten Lauf wieder mit dem gewanderten Extrem."""
    from strategy_core import Position, PosState
    pos = Position(direction="LONG", state=PosState.TP1, retrace_extreme=101.0,
                   ziel_extrem=103.6)
    d = pos_to_state(pos)
    assert d["ziel_extrem"] == 103.6
    assert pos_from_state(d).ziel_extrem == 103.6
    assert pos_from_state({}).ziel_extrem is None          # Altbestand ohne das Feld


def test_be_aktiv_ueberlebt_den_neustart():
    """E19.3: Ohne Persistenz haette die Engine bei jedem Lauf vergessen, dass der
    Break-even-Stop schon scharf ist — und die Position waere wieder ungeschuetzt."""
    from strategy_core import Position, PosState
    pos = Position(direction="LONG", state=PosState.CORE, entry_ref=140.0, be_aktiv=True)
    d = pos_to_state(pos)
    assert d["be_aktiv"] is True
    assert pos_from_state(d).be_aktiv is True
    assert pos_from_state({}).be_aktiv is False           # Altbestand ohne das Feld


def test_widerstand_marken_liefert_die_zweite_zonenreihe():
    """E20: Die Widerstandsmarken muessen im state landen, sonst kann weder der Chart
    noch die Telegram-Nachricht sie zeigen."""
    from strategy_core import Position
    import test_strategy_core as tsc
    cs = tsc._e20_pfad()
    w = main.widerstand_marken(cs, {"pivot_n": 2, "k_atr": 2.0}, Position())
    assert w is not None and w["richtung"] == "LONG"
    assert w["bein_start"] == 130 and w["bein_ende"] == 120
    assert w["gp_von"] < w["gp_bis"] < w["level_0786"] < w["ausbruch"] == 130
    # ohne erkennbares Gegen-Bein: None statt Absturz
    flach = [tsc.c(i, 100, 100.5, 99.5, 100) for i in range(20)]
    assert main.widerstand_marken(flach, {"pivot_n": 2}, Position()) is None


# ------------------------------------------- E20.2: Plan zur laufenden Position

def _plan_szenario():
    """Long-Position im Zustand CORE mit vollstaendigen Zonen."""
    from strategy_core import FibZones, Impulse, Pivot, PosState, Position
    import test_strategy_core as tsc
    cs = tsc._e20_pfad_mit_neuem_hoch()
    imp = Impulse(Pivot(4, 4, 98.0, "L"), Pivot(9, 9, 130.0, "H"))
    z = FibZones(imp, level_05=114.0, gp_upper=110.2, gp_lower=109.2,
                 level_0786=104.9, invalidation=98.0)
    pos = Position(direction="LONG", state=PosState.CORE, zones=z, retrace_extreme=120.0,
                   last_signal_ts=19, entry_ref=115.0, entry_pct=75)
    fl = [FlowPoint(c.ts, 1000 + i, 0, 1e9, -0.0001) for i, c in enumerate(cs)]
    return cs, fl, pos


def test_plan_nennt_nachkauf_teilgewinn_und_stop():
    cs, fl, pos = _plan_szenario()
    p = main.positions_plan(cs, fl, {"pivot_n": 2, "k_atr": 2.0}, pos)
    assert p is not None and p["richtung"] == "LONG" and p["anteil_pct"] == 75
    assert p["nachkauf"] and p["teilgewinn"] and p["stop"]["preis"] == 98.0
    arten = [e["was"] for e in p["teilgewinn"]]
    assert any("Ziel 1.0" in a for a in arten) and any("Ziel 1.618" in a for a in arten)
    # bei geschlossener Position gibt es keinen Plan
    from strategy_core import Position
    assert main.positions_plan(cs, fl, {}, Position()) is None


def test_plan_marken_stimmen_mit_der_engine_ueberein():
    """Die wichtigste Prüfung: Was der Plan als Ziel 1.0 nennt, muss die Engine dort auch
    ausloesen. Sonst legt Kaiser eine Order an einen Preis, den die App nie meldet."""
    from strategy_core import SignalType, evaluate
    import test_strategy_core as tsc
    cs, fl, pos = _plan_szenario()
    p = main.positions_plan(cs, fl, {"pivot_n": 2, "k_atr": 2.0}, pos)
    ziel = next(e["preis"] for e in p["teilgewinn"] if e["was"] == "Ziel 1.0")

    # (a) Eine Kerze, die knapp UNTER der Marke bleibt, darf nichts ausloesen —
    #     sonst haette der Plan zu hoch angesetzt.
    import copy
    zu_frueh = evaluate(cs + [tsc.c(20, 128, ziel * 0.995, 127, ziel * 0.994)],
                        fl + [fl[-1]], copy.deepcopy(pos), pivot_n=2, k_atr=2.0,
                        bias_short=False, tp_ladder=False, buy_ladder=False, high_exit="off")
    assert not any(s.type == SignalType.TEILVERKAUF_1 for s in zu_frueh), \
        "Engine verkauft schon unter der Marke, die der Plan nennt"

    # (b) Eine Kerze, die die Marke erreicht, loest aus — UND zwar zu genau diesem Preis.
    #     Der Preisvergleich ist der eigentliche Test: er faellt auch auf, wenn der Plan
    #     zu hoch angesetzt haette.
    sigs = evaluate(cs + [tsc.c(20, 128, ziel + 0.5, 127, ziel)], fl + [fl[-1]], pos,
                    pivot_n=2, k_atr=2.0, bias_short=False, tp_ladder=False,
                    buy_ladder=False, high_exit="off")
    treffer = [s for s in sigs if s.type == SignalType.TEILVERKAUF_1]
    assert treffer, "Plan nennt ein Ziel, das die Engine nicht ausloest"
    assert abs(treffer[0].price - ziel) < 0.01, \
        f"Plan nennt {ziel:.2f}, die Engine handelt {treffer[0].price:.2f}"


def test_plan_nachricht_wird_nur_bei_aenderung_gesendet():
    cs, fl, pos = _plan_szenario()
    cfg = {"pivot_n": 2, "k_atr": 2.0}
    p1 = main.positions_plan(cs, fl, cfg, pos)
    assert main.plan_geaendert(None, p1) is True          # erster Plan -> senden
    assert main.plan_geaendert(p1, p1) is False           # unveraendert -> schweigen
    import copy
    # erste Marke MIT Einzelpreis heranziehen (die Widerstandszone ist eine Spanne)
    idx = next(i for i, e in enumerate(p1["teilgewinn"]) if e.get("preis"))
    p2 = copy.deepcopy(p1)
    p2["teilgewinn"][idx]["preis"] *= 1.02
    assert main.plan_geaendert(p1, p2) is True            # 2 % verschoben -> senden
    p3 = copy.deepcopy(p1)
    p3["teilgewinn"][idx]["preis"] *= 1.0005              # 0,05 % -> Rauschen
    assert main.plan_geaendert(p1, p3) is False
    # Ein Nachkauf allein (mehr investiert, gleiche Marken) ist KEINE Planaenderung —
    # sonst kaeme zu jedem Signal eine zweite Nachricht.
    p4 = copy.deepcopy(p1)
    p4["anteil_pct"] = p1["anteil_pct"] + 20
    p4["einstand"] = (p1["einstand"] or 100) * 0.99
    assert main.plan_geaendert(p1, p4) is False


def test_plan_nachricht_ist_lesbar():
    from telegram_notify import format_plan
    cs, fl, pos = _plan_szenario()
    text = format_plan(main.positions_plan(cs, fl, {"pivot_n": 2, "k_atr": 2.0}, pos))
    assert "PLAN" in text and "Nachkaufen:" in text and "Teilgewinne:" in text
    assert "Stop" in text and "Limit-Order" in text


def test_plan_zeigt_die_widerstandszone_auch_ohne_aktiven_schalter():
    """E20: Die Zone ist die wichtigste neue Information — sie darf nicht davon abhaengen,
    ob die Engine dort automatisch verkauft."""
    cs, fl, pos = _plan_szenario()
    p_aus = main.positions_plan(cs, fl, {"pivot_n": 2, "k_atr": 2.0}, pos)
    eintrag = [e for e in p_aus["teilgewinn"] if "Widerstand" in e["was"]]
    assert len(eintrag) == 1 and eintrag[0]["tranche"] == 0
    assert "nur Hinweis" in eintrag[0]["was"]
    p_an = main.positions_plan(cs, fl, {"pivot_n": 2, "k_atr": 2.0,
                                        "widerstand_exit": "on"}, pos)
    eintrag_an = [e for e in p_an["teilgewinn"] if "Widerstand" in e["was"]]
    assert eintrag_an[0]["tranche"] > 0 and "nur Hinweis" not in eintrag_an[0]["was"]


def test_plan_meldet_verschobene_marken_weiterhin():
    """Gegenprobe zu der Vereinfachung von vorhin: Nur der ANTEIL zaehlt nicht mehr als
    Aenderung. Verschiebt sich eine Marke — Widerstandszone, Fib-Level, Ziel oder Stop —
    muss die Nachricht kommen."""
    import copy
    cs, fl, pos = _plan_szenario()
    p1 = main.positions_plan(cs, fl, {"pivot_n": 2, "k_atr": 2.0}, pos)
    for wo, feld in [("teilgewinn", "Widerstand"), ("teilgewinn", "Ziel 1.0"),
                     ("nachkauf", "0.786-Zone")]:
        p2 = copy.deepcopy(p1)
        treffer = [e for e in p2[wo] if feld in e["was"]]
        if not treffer:
            continue
        e = treffer[0]
        if e.get("zone"):
            e["zone"] = [e["zone"][0] * 1.01, e["zone"][1] * 1.01]
        else:
            e["preis"] *= 1.01
        assert main.plan_geaendert(p1, p2) is True, f"{feld} verschoben, aber keine Meldung"
    p3 = copy.deepcopy(p1)
    p3["stop"]["preis"] *= 1.01
    assert main.plan_geaendert(p1, p3) is True, "Stop verschoben, aber keine Meldung"


def test_fetch_spot_paginiert_ueber_1000_kerzen():
    """E33-A: Die Binance-API liefert hoechstens 1000 Kerzen je Abruf. Fuer den
    EMA200 braucht die Engine ~1300 - also muss nachgeladen und chronologisch
    zusammengesetzt werden. Ohne echten Netzzugriff geprueft, indem _get_json
    ersetzt wird.
    """
    import main as M
    aufrufe = []

    JETZT = 1_789_000_000_000        # realistischer ms-Zeitstempel, keine negativen Werte

    def fake(url):
        aufrufe.append(url)
        import re
        lim = int(re.search(r"limit=(\d+)", url).group(1))
        ende = re.search(r"endTime=(-?\d+)", url)
        bis = int(ende.group(1)) if ende else JETZT
        # Binance liefert aufsteigend sortiert, aelteste Kerze zuerst
        start = bis - lim * M.CANDLE_MS
        return [[start + i * M.CANDLE_MS, "1", "2", "0.5", "1.5", "0", 0, 0]
                for i in range(lim)]

    echt = M._get_json
    try:
        M._get_json = fake
        # bis 1000: genau ein Abruf, wie bisher
        aufrufe.clear()
        einer = M.fetch_spot(400)
        assert len(aufrufe) == 1 and len(einer) == 400

        # darueber: mehrere Abrufe, Ergebnis in voller Laenge und chronologisch
        aufrufe.clear()
        viele = M.fetch_spot(1300)
        assert len(aufrufe) >= 2, f"1300 Kerzen brauchen mehr als einen Abruf, waren {len(aufrufe)}"
        assert len(viele) >= 1300, f"es fehlen Kerzen: {len(viele)}"
        ts = [int(k[0]) for k in viele]
        assert ts == sorted(ts), "die Kerzen muessen chronologisch sortiert sein"
        assert len(set(ts)) == len(ts), "keine Kerze darf doppelt vorkommen"
    finally:
        M._get_json = echt


def test_hauptlauf_laedt_mehr_historie_als_die_flush_wache():
    """Die Flush-Wache laeuft alle 15 Minuten und braucht keinen Trend - ihre Last
    soll nicht verdoppelt werden."""
    import main as M
    assert M.LIMIT_HAUPT > M.LIMIT
    assert M.LIMIT_HAUPT >= 1200, "fuer einen echten EMA200 auf 1D noetig"
    assert f"limit={M.LIMIT}" in M.SPOT_URL, "die Flush-Wache bleibt beim kleinen Fenster"


def test_fetch_spot_bricht_ab_wenn_die_api_nicht_vorankommt():
    """Notbremse (E33): Liefert die API wiederholt dieselben Kerzen, darf fetch_spot
    NICHT endlos weiterfragen - im 15-Minuten-Takt waere das ein haengender Workflow,
    der niemandem auffaellt.

    Diese Luecke hat die Sabotage-Probe aufgedeckt: Die erste Fassung der Schleife
    pruefte nur `fehlt > 0` und haette bei ausbleibendem Fortschritt ewig gedreht.
    """
    import main as M
    aufrufe = []
    JETZT = 1_789_000_000_000

    def stur(url):
        """Gibt immer denselben Block zurueck - egal was gefragt wird."""
        aufrufe.append(url)
        return [[JETZT - (999 - i) * M.CANDLE_MS, "1", "2", "0.5", "1.5", "0", 0, 0]
                for i in range(1000)]

    echt = M._get_json
    try:
        M._get_json = stur
        out = M.fetch_spot(5000)                  # weit mehr als erreichbar
        # Zwei Abrufe: der erste holt, der zweite zeigt, dass es nicht weiter
        # zurueckgeht. Danach muss Schluss sein - NICHT erst nach MAX_ABRUFE.
        assert len(aufrufe) <= 2, (
            f"die Fortschrittspruefung hat nicht gegriffen: {len(aufrufe)} Abrufe")
        assert out, "trotz Abbruch muessen die geholten Kerzen zurueckkommen"
    finally:
        M._get_json = echt


def test_fetch_spot_gibt_zurueck_was_da_ist_wenn_die_api_versiegt():
    """Liefert ein Nachlade-Abruf nichts mehr, wird mit dem Vorhandenen gearbeitet -
    die Engine soll nicht wegen fehlender Althistorie ausfallen."""
    import main as M
    JETZT = 1_789_000_000_000
    zaehler = {"n": 0}

    def versiegt(url):
        zaehler["n"] += 1
        if zaehler["n"] > 1:
            return []                              # ab dem zweiten Abruf nichts mehr
        return [[JETZT - (999 - i) * M.CANDLE_MS, "1", "2", "0.5", "1.5", "0", 0, 0]
                for i in range(1000)]

    echt = M._get_json
    try:
        M._get_json = versiegt
        out = M.fetch_spot(1300)
        assert len(out) == 1000, f"es sollten die 1000 geholten Kerzen bleiben, sind {len(out)}"
    finally:
        M._get_json = echt


def test_eval_defaults_hat_keinen_doppelten_schluessel():
    """Ein Python-dict schluckt doppelte Schluessel still - der letzte gewinnt.

    Gefunden am 13.09.2026: EVAL_DEFAULTS enthielt trend_filter und trend_ema ZWEIMAL
    (einmal mit 50, einmal mit 200). Das Verhalten war zufaellig richtig, aber wer die
    obere Zeile geaendert haette, haette keine Wirkung gesehen und keinen Fehler.
    test_alle_evaluate_parameter_werden_durchgereicht kann das nicht finden, weil es
    das fertige dict prueft - also wird hier der QUELLTEXT gelesen.
    """
    import ast
    import inspect
    from pathlib import Path
    baum = ast.parse(Path(inspect.getfile(main)).read_text(encoding="utf-8"))
    for knoten in ast.walk(baum):
        if (isinstance(knoten, ast.Assign)
                and any(getattr(z, "id", "") == "EVAL_DEFAULTS" for z in knoten.targets)):
            namen = [s.value for s in knoten.value.keys if isinstance(s, ast.Constant)]
            doppelt = sorted({n for n in namen if namen.count(n) > 1})
            assert not doppelt, f"EVAL_DEFAULTS nennt doppelt: {doppelt}"
            return
    raise AssertionError("EVAL_DEFAULTS im Quelltext nicht gefunden")


def test_ampel_steht_in_plan_und_vorschau():
    """E34: Die Ampel ist eine ANZEIGE und haengt an keinem Schalter.

    ampel_filter steht auf 'off' (live) und darf daran nichts aendern - sonst saehe
    Kaiser die Zusammenfassung nur, wenn die Engine auch danach handelt.
    """
    import inspect
    from strategy_core import evaluate
    assert "ampel_filter" in inspect.signature(evaluate).parameters
    assert main.EVAL_DEFAULTS["ampel_filter"] == "off"

    for stelle in ("zonen_vorschau", "positions_plan"):
        fn = inspect.getsource(getattr(main, stelle))
        assert "ampel(" in fn, f"{stelle} berechnet die Ampel nicht"
        # gemeint ist ein echter Zugriff auf den Schalter, nicht das Wort im Kommentar
        for zugriff in ('par.get("ampel_filter"', 'par["ampel_filter"]',
                        "par.get('ampel_filter'", "par['ampel_filter']"):
            assert zugriff not in fn, f"{stelle} haengt die Anzeige an den Schalter"


# ------------------------------------------------- E35: Lage auf Abruf

def _lage_kerzen(auf: bool = True):
    """Kerzen mit klarem Aufwaerts- bzw. Abwaerts-Impuls, danach Ruecklauf."""
    ms = 4 * 3600 * 1000
    if auf:
        werte = [100, 99, 98, 99, 104, 110, 116, 122, 128, 130] \
            + [130 - i * 0.8 for i in range(1, 17)]
    else:
        werte = [130, 131, 132, 131, 126, 120, 114, 108, 102, 100] \
            + [100 + i * 0.8 for i in range(1, 17)]
    cs = [Candle(1_700_000_000_000 + i * ms, v, v * 1.004, v * 0.996, v)
          for i, v in enumerate(werte)]
    fl = [FlowPoint(c.ts, 5000.0 + i * 30, 0.0, 1e9 + i * 1e6, 0.0001)
          for i, c in enumerate(cs)]
    return cs, fl


def _lage_lauf(cs, fl, cfg=None):
    with tempfile.TemporaryDirectory() as d:
        ordner = Path(d)
        (ordner / "config.json").write_text(
            json.dumps(cfg or {"pivot_n": 2, "bias_short": False}), encoding="utf-8")
        out = main.lage_abruf(fetch=lambda oi=None: (cs, fl, []),
                              data_dir=ordner, dry_run=True)
        dateien = sorted(p.name for p in ordner.iterdir())
    return out, dateien


def test_lage_abruf_fasst_den_zustand_nicht_an():
    """Die wichtigste Zusicherung: der Abruf darf NICHTS veraendern.

    Kein Signal, kein state.json, keine Auswirkung auf den naechsten regulaeren Lauf -
    dasselbe Prinzip wie --watch. Sonst koennte ein Blick auf die Lage den Ablauf der
    Engine stoeren, und das waere der schlimmste denkbare Nebeneffekt eines Knopfes,
    den Kaiser jederzeit druecken darf.
    """
    cs, fl = _lage_kerzen()
    out, dateien = _lage_lauf(cs, fl)
    assert out is not None
    assert dateien == ["config.json"], f"Abruf hat Dateien angelegt: {dateien}"


def test_lage_abruf_sucht_immer_ein_aufwaerts_bein():
    """Angenommen wird eine LONG-Position - also zaehlt nur ein Aufwaerts-Bein.

    Genau das war Kaisers Lage am 17.09.2026: Die Engine fand ein Abwaerts-Bein
    (79.600 -> 74.968) und rechnete alles dafuer, waehrend er long war.
    """
    cs, fl = _lage_kerzen(auf=True)
    out, _ = _lage_lauf(cs, fl)
    assert out["bein"] is not None
    assert out["bein"][1] > out["bein"][0], "kein Aufwaerts-Bein geliefert"

    # Auch bei bein_richtung="bias" und reiner Long-Engine bleibt es dabei ...
    out2, _ = _lage_lauf(cs, fl, {"pivot_n": 2, "bias_short": False,
                                  "bein_richtung": "bias"})
    assert out2["bein"] == out["bein"]


def test_lage_abruf_erfindet_kein_bein_wenn_keins_da_ist():
    """Ohne Aufwaerts-Bein lieber gar keins als ein Abwaerts-Bein, das fuer einen
    Long nichts bedeutet. Die Nachricht sagt das dann ausdruecklich."""
    from telegram_notify import format_lage
    cs, fl = _lage_kerzen(auf=False)                  # nur ein Abwaerts-Impuls
    out, _ = _lage_lauf(cs, fl)
    assert out["bein"] is None, f"Abwaerts-Bein durchgerutscht: {out['bein']}"
    txt = format_lage(out, cs[-1].ts)
    assert "Kein signifikantes Aufwaerts-Bein" in txt
    assert "0.5-Level" not in txt, "Zonen ohne Bein ergeben keinen Sinn"


def test_lage_abruf_rechnet_die_ampel_fuer_long():
    """Die Annahme ist Long - also rechnet die Ampel fuer Long, immer.

    trend_ema=3 ist Absicht: Mit der Live-Vorgabe 200 reicht die Historie eines
    Testszenarios nie, die Ampel schwiege, und der Test pruefte NICHTS. Genau so war
    die erste Fassung - sie stand unter "if out.get('ampel')" und lief ins Leere.
    """
    cs, fl = _lage_kerzen()
    out, _ = _lage_lauf(cs, fl, {"pivot_n": 2, "bias_short": False, "trend_ema": 3})
    assert out["ampel"] is not None, "Szenario passt nicht mehr - Ampel schweigt"
    assert out["ampel"]["richtung"] == "LONG"

    from telegram_notify import format_lage
    txt = format_lage(out, cs[-1].ts)
    assert "AMPEL (fuer LONG)" in txt
    assert "LONG-Position" in txt
    assert "FLAT" in txt, "der Hinweis auf den echten Engine-Zustand fehlt"


def test_vorschau_ampel_folgt_dem_bias_nicht_dem_bein():
    """E35-Reparatur, Ende zu Ende durch zonen_vorschau().

    Der Fehler vom 17.09.2026: bei bias_short=false und einem ABWAERTS-Bein rechnete
    die Vorschau die Ampel fuer einen Short. Dieser Test geht durch dieselbe Funktion
    wie die echte Nachricht - ein Test nur auf ampel_richtung() waere gruen geblieben,
    haette man die Verdrahtung wieder geloest.
    """
    cs, fl = _lage_kerzen(auf=False)                  # Abwaerts-Bein
    nur_long = {"pivot_n": 2, "bias_short": False, "trend_ema": 3}
    z = main.zonen_vorschau(cs, nur_long, flow=fl)
    assert z is not None and z["richtung"] == "SHORT", "Szenario passt nicht mehr"
    assert z["ampel"] is not None, "Szenario passt nicht mehr - Ampel schweigt"
    assert z["ampel"]["richtung"] == "LONG", \
        "Ampel rechnet fuer einen Short, den die Engine nie eingehen wuerde"

    # Gegenprobe: sind BEIDE Richtungen erlaubt, entscheidet wieder das Bein
    beide = {"pivot_n": 2, "bias_short": True, "trend_ema": 3}
    z2 = main.zonen_vorschau(cs, beide, flow=fl)
    assert z2["ampel"] is not None and z2["ampel"]["richtung"] == "SHORT"
    # ... und die Stufen sind dann spiegelbildlich, nicht zufaellig gleich
    assert z2["ampel"]["dafuer"] == z["ampel"]["dagegen"]


def test_lage_abruf_enthaelt_furkans_rohwerte():
    """E36: Der Abruf zeigt die Groessen, aus denen das Muster entsteht - und die
    Nachricht gibt sie auch aus, nicht nur das dict."""
    from telegram_notify import format_lage
    import random
    r = random.Random(3)
    ms = 4 * 3600 * 1000
    cs, fl = [], []
    cvd_s, cvd_f, oi, v = 5000.0, 1000.0, 1e9, 76000.0
    for i in range(40):
        v *= (1 + r.gauss(0.001, 0.01))
        cs.append(Candle(1_700_000_000_000 + i * ms, v, v * 1.004, v * 0.996, v))
        cvd_s += r.gauss(4e6, 2e6); cvd_f += r.gauss(1e6, 3e6); oi *= (1 + r.gauss(0, 0.008))
        fl.append(FlowPoint(cs[-1].ts, cvd_s, cvd_f, oi, r.gauss(0.0001, 0.0002),
                            long_liq=abs(r.gauss(2e6, 1e6)),
                            short_liq=abs(r.gauss(1e6, 5e5)), long_pct=54.0))
    out, dateien = _lage_lauf(cs, fl, {"pivot_n": 5, "bias_short": False})
    assert out["orderflow"], "keine Rohwerte im Abruf"
    assert dateien == ["config.json"], "der Abruf hat etwas geschrieben"

    txt = format_lage(out, cs[-1].ts)
    assert "ORDER-FLOW" in txt
    assert "48 h" in txt, "das Fenster muss in der Nachricht stehen"
    for name in ("Spot-CVD", "Futures-CVD", "Open Interest", "Funding",
                 "Positionierung"):
        assert name in txt, f"{name} fehlt in der Nachricht"
    assert "echte Nachfrage, ohne Hebel" in txt      # Furkans Wortwahl zum Spot-CVD
    # E36.2: Beim Futures-CVD steht jetzt das VERHAELTNIS zum Spot - die
    # Groessenordnung ist die eigentliche Aussage (Furkans "gesunder Trend").
    assert "des Spot-Flows" in txt


def test_lage_nachricht_bleibt_handy_tauglich():
    """E36.2 (Kaisers Fund 19.09.2026): Keine Zeile darf auf dem Handy umbrechen.

    Telegram rendert den Text PROPORTIONAL und ohne parse_mode - eine Ausrichtung mit
    Leerzeichen kann dort gar nicht funktionieren. Die vorherige Fassung hatte Zeilen
    bis 210 Zeichen; auf dem Handy brach jede zwei- bis dreimal um und war unlesbar.

    Dieser Test misst die Laenge, statt sie zu schaetzen - und prueft BEIDE Faelle
    (mit und ohne Bein), damit kein Zweig der Nachricht ungeprueft bleibt.
    """
    from telegram_notify import format_lage, ZEILE_MAX
    # FESTE Zahl, nicht ZEILE_MAX: Ein Test, der gegen dieselbe Konstante prueft, die
    # er absichern soll, misst sich selbst - die Sabotage "ZEILE_MAX = 99" blieb
    # dadurch ungefangen. 38 Zeichen sind die Handybreite, um die es geht.
    HANDY = 38
    assert ZEILE_MAX <= HANDY, f"ZEILE_MAX ist auf {ZEILE_MAX} hochgesetzt worden"
    import random
    r = random.Random(3)
    ms = 4 * 3600 * 1000

    def _serie(aufwaerts: bool):
        cs, fl = [], []
        cvd_s, cvd_f, oi = 5000.0, 1000.0, 8.3e9
        werte = ([76264 + i * 250 for i in range(10)] + [82300 - i * 90 for i in range(1, 30)]
                 if aufwaerts else
                 [82300 - i * 250 for i in range(10)] + [76264 + i * 90 for i in range(1, 30)])
        for i, v in enumerate(werte):
            cs.append(Candle(1_700_000_000_000 + i * ms, v, v * 1.004, v * 0.996, v))
            cvd_s += r.gauss(15e6, 6e6); cvd_f += r.gauss(600, 3000)
            oi *= (1 + r.gauss(0.004, 0.006))
            fl.append(FlowPoint(cs[-1].ts, cvd_s, cvd_f, oi, 0.000038,
                                long_liq=abs(r.gauss(8e5, 4e5)),
                                short_liq=abs(r.gauss(7.5e6, 2e6)), long_pct=47.0))
        return cs, fl

    geprueft = 0
    for aufwaerts in (True, False):
        cs, fl = _serie(aufwaerts)
        out, _ = _lage_lauf(cs, fl, {"pivot_n": 5, "bias_short": False, "trend_ema": 3})
        txt = format_lage(out, cs[-1].ts)
        lang = [(len(z), z) for z in txt.split("\n") if len(z) > HANDY]
        assert not lang, f"zu lange Zeilen ({'mit' if aufwaerts else 'ohne'} Bein): {lang[:3]}"
        geprueft += 1
        # ... und der Zweig muss wirklich durchlaufen sein. "Aufwaerts-Bein" allein
        # taugt nicht als Merkmal: Es steckt auch in "Kein signifikantes
        # Aufwaerts-Bein erkennbar". Geprueft wird deshalb der Zonen-Block.
        hat_zonen = "0.5-Level:" in txt
        assert hat_zonen == (out["bein"] is not None), \
            f"Zonen-Block passt nicht zum Bein (bein={out['bein']})"
    assert geprueft == 2, "beide Zweige muessen geprueft worden sein"


def test_spot_cvd_zeigt_beide_zeitebenen_wenn_sie_sich_unterscheiden():
    """E36.2, Kaisers Fund: Der Block rechnete 48 h, die Lage-Zeile 12 h - in der
    Nachricht standen zwei Zahlen unter fast demselben Namen, die sich zu
    widersprechen schienen ('steigt' gegen 'nachgelassen'). Beides war richtig.

    Jetzt steht die kurze Ebene daneben, WENN sie in eine andere Richtung zeigt.
    Der Unterschied ist die eigentliche Information: Tempoverlust.
    """
    from strategy_core import orderflow_detail, SPOT_FENSTER
    ms = 4 * 3600 * 1000
    # 48 h stark steigend, die letzten 12 h fallend
    cvd = [float(i) * 15e6 for i in range(30)]
    cvd += [cvd[-1] - (i + 1) * 3e6 for i in range(3)]
    cs = [Candle(1_700_000_000_000 + i * ms, 80000, 80300, 79700, 80000)
          for i in range(len(cvd))]
    fl = [FlowPoint(c.ts, v, 0.0, 8e9, 0.0) for c, v in zip(cs, cvd)]

    zeilen = orderflow_detail(cs, fl)
    namen = [z["name"] for z in zeilen]
    kurz = f"... letzte {SPOT_FENSTER * 4} h"
    assert "Spot-CVD" in namen, "Szenario passt nicht - Spot-CVD fehlt"
    lang_r = next(z["richtung"] for z in zeilen if z["name"] == "Spot-CVD")
    assert lang_r == "steigt", f"Szenario passt nicht - 48 h sagt {lang_r}"
    assert kurz in namen, "die kurze Ebene fehlt, obwohl sie widerspricht"
    kurz_r = next(z["richtung"] for z in zeilen if z["name"] == kurz)
    assert kurz_r != lang_r, "die kurze Ebene zeigt dieselbe Richtung - kein Befund"

    # Gegenprobe: zeigen beide in dieselbe Richtung, entfaellt die Zusatzzeile
    cvd2 = [float(i) * 15e6 for i in range(33)]
    fl2 = [FlowPoint(c.ts, v, 0.0, 8e9, 0.0) for c, v in zip(cs, cvd2)]
    assert kurz not in [z["name"] for z in orderflow_detail(cs, fl2)]


def test_futures_cvd_zeigt_das_verhaeltnis_zum_spot():
    """E36.2: '+7 Tsd $ steigt' neben '+177,7 Mio $' verdeckt, dass der Hebel
    praktisch keine Rolle spielt - und genau das ist Furkans 'gesunder Trend'."""
    from strategy_core import orderflow_detail
    ms = 4 * 3600 * 1000
    cs = [Candle(1_700_000_000_000 + i * ms, 80000, 80300, 79700, 80000) for i in range(30)]
    fl = [FlowPoint(c.ts, float(i) * 15e6, float(i) * 600.0, 8e9, 0.0)
          for i, c in enumerate(cs)]
    fu = next(z for z in orderflow_detail(cs, fl) if z["name"] == "Futures-CVD")
    # 600 gegen 15 Mio je Kerze = 0,004 % -> unter 0,5 %, also der Klartext-Fall.
    # "0,0 % des Spot-Flows" saehe nach einem Rechenfehler aus.
    assert fu["hinweis"] == "verschwindend gegen den Spot", fu["hinweis"]

    # Gegenprobe: bei spuerbarem Futures-Anteil steht das Verhaeltnis als Zahl da
    fl2 = [FlowPoint(c.ts, float(i) * 15e6, float(i) * 3e6, 8e9, 0.0)
           for i, c in enumerate(cs)]
    fu2 = next(z for z in orderflow_detail(cs, fl2) if z["name"] == "Futures-CVD")
    assert "% des Spot-Flows" in fu2["hinweis"], fu2["hinweis"]
    assert "20" in fu2["hinweis"], f"Verhaeltnis falsch: {fu2['hinweis']}"


def test_kurze_spot_ebene_zeigt_das_vorzeichen_nicht_den_massstab():
    """E36.2: Die Zusatzzeile existiert NUR wegen der Drehung - also muss sie das
    Vorzeichen zeigen.

    Nach dem Massstab gerechnet hiesse -11 Mio nach typischen +48 Mio "flach":
    rechnerisch richtig, aber am Punkt vorbei. Dieses Szenario trennt beides,
    denn ein Test, in dem Massstab und Vorzeichen dasselbe sagen, prueft nichts
    (die Sabotage blieb genau daran zuerst ungefangen).
    """
    from strategy_core import orderflow_detail, SPOT_FENSTER, _of_reihe
    ms = 4 * 3600 * 1000
    # 48 h sehr kraeftig steigend, die letzten 3 Kerzen leicht fallend
    cvd = [float(i) * 16e6 for i in range(30)]
    cvd += [cvd[-1] - (i + 1) * 3.5e6 for i in range(SPOT_FENSTER)]
    cs = [Candle(1_700_000_000_000 + i * ms, 80000, 80300, 79700, 80000)
          for i in range(len(cvd))]
    fl = [FlowPoint(c.ts, v, 0.0, 8e9, 0.0) for c, v in zip(cs, cvd)]

    # Nachweis, dass das Szenario die Regel ueberhaupt trifft: der Massstab wuerde
    # hier "flach" sagen, das Vorzeichen aber "faellt".
    roh = _of_reihe([p.spot_cvd for p in fl], SPOT_FENSTER)
    assert roh["aenderung"] < 0, "Szenario passt nicht - die Aenderung muss negativ sein"
    assert roh["richtung"] == "flach", \
        f"Szenario trennt nicht - Massstab sagt bereits {roh['richtung']}"

    kurz = next(z for z in orderflow_detail(cs, fl)
                if z["name"] == f"... letzte {SPOT_FENSTER * 4} h")
    assert kurz["richtung"] == "faellt", \
        f"Zusatzzeile zeigt {kurz['richtung']} statt des Vorzeichens"


def test_kurze_spot_ebene_nutzt_dasselbe_fenster_wie_die_lage_zeile():
    """Die Zusatzzeile soll genau die Zahl erklaeren, die in der Lage-Zeile steht.
    Ein anderes Fenster brächte den Widerspruch zurück, den sie aufloesen soll."""
    import inspect
    from strategy_core import SPOT_FENSTER, spot_nachfrage, orderflow_detail
    assert inspect.signature(spot_nachfrage).parameters["fenster"].default == SPOT_FENSTER
    quelle = inspect.getsource(orderflow_detail)
    assert "_of_reihe([p.spot_cvd for p in flow], SPOT_FENSTER)" in quelle, \
        "die Zusatzzeile rechnet nicht mit SPOT_FENSTER"


def test_e41_warten_ueberlebt_den_neustart_der_live_engine():
    """Die Live-Engine ist bei jedem Lauf ein neuer Prozess. Ginge der Wartezaehler
    verloren, fing das Warten bei jedem Lauf neu an - der Stop kaeme nie. Im Backtest
    faellt das nicht auf, weil der am Stueck rechnet."""
    from strategy_core import Position
    pos = Position()
    pos.stop_wartet, pos.stop_wartet_inv, pos.stop_geprueft = 2, 97.6, 95.0
    rt = pos_from_state(pos_to_state(pos))
    assert (rt.stop_wartet, rt.stop_wartet_inv, rt.stop_geprueft) == (2, 97.6, 95.0)
    alt = pos_from_state({"pos_state": "FLAT"})          # Altbestand ohne die Felder
    assert (alt.stop_wartet, alt.stop_wartet_inv, alt.stop_geprueft) == (0, None, None)
