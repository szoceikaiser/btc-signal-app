"""E44.4: kuenstliche Kursfolgen, keine Markt-Messung. Gegenproben: sabotage_e444.py."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import backtest
import main
from strategy_core import Position, Signal, SignalType, evaluate, verkauf_tranche
from telegram_notify import format_plan, format_signal
from test_e443 import ANLAUF, LIVE, bau, lauf, spiegel, _cs, _sig

ENG = Path(__file__).resolve().parent
TEIL = {"TEILVERKAUF_LADDER", "TEILVERKAUF_1", "TEILVERKAUF_2",
        "SHORT_TP_LADDER", "SHORT_TP_1", "SHORT_TP_2"}
KW = {**LIVE, "trail_stop": False, "rest_halten": True,
      "no_flip": False, "bein_richtung": "auto"}


def pfad(short=False):
    cs, fl = bau(ANLAUF + [135, 140, 150, 160, 180, 200])
    return (spiegel(cs) if short else cs), fl


def test_defaults_und_neutraler_pfad():
    cfg = json.loads((ENG.parent / "site/data/config.json").read_text(encoding="utf-8"))
    assert "verkauf_faktor" in cfg and "verkauf_faktor" in main.EVAL_DEFAULTS
    assert cfg["verkauf_faktor"] == main.EVAL_DEFAULTS["verkauf_faktor"] == 1.0
    assert "verkauf_faktor" in backtest.EVAL_KEYS
    assert all(v["verkauf_faktor"] == 1.0 for v in backtest.GRID)
    cs, fl = pfad()
    a, _, pa = lauf(cs, fl, **KW)
    b, _, pb = lauf(cs, fl, **KW, verkauf_faktor=1.0)
    assert any(s.type.name in TEIL for _, s in a)
    assert a == b and pa == pb
    assert all(isinstance(s.tranche_pct, int) for _, s in b)


def test_faktor_validierung():
    assert main.eval_params({"verkauf_faktor": "0.67"})["verkauf_faktor"] == 0.67
    assert verkauf_tranche(15, 0.67) == 10.05
    for wert in (None, True, False, 0, -0.5, 1.01, "falsch", float("nan"), float("inf")):
        assert main.eval_params({"verkauf_faktor": wert})["verkauf_faktor"] == 1.0
        assert verkauf_tranche(15, wert) == 15


def _skalierung(short):
    cs, fl = pfad(short)
    kw = {**KW, "bias_long": not short, "bias_short": short}
    a, _, _ = lauf(cs, fl, **kw)
    b, _, _ = lauf(cs, fl, **kw, verkauf_faktor=0.67)
    teile = {s.type.name for _, s in a if s.type.name in TEIL}
    assert teile == ({"SHORT_TP_LADDER", "SHORT_TP_1", "SHORT_TP_2"} if short else
                     {"TEILVERKAUF_LADDER", "TEILVERKAUF_1", "TEILVERKAUF_2"})
    assert any("letzten" in s.reason for _, s in a)
    assert len(a) == len(b)
    for (i, s), (j, t) in zip(a, b):
        assert (i, s.type, s.price, s.reason) == (j, t.type, t.price, t.reason)
        assert t.tranche_pct == (round(s.tranche_pct * .67, 8) if s.type.name in TEIL
                                 else s.tranche_pct)


def test_long_alle_teilgewinn_typen():
    _skalierung(False)


def test_short_alle_teilgewinn_typen():
    _skalierung(True)


def test_kauf_rueckkauf_und_stops_bleiben_unskaliert():
    cs, fl = bau(ANLAUF + [130, 131, 130, 128.5, 80, 79])
    kw = {**LIVE, "ausbruch_ruecktest": True}
    a, _, _ = lauf(cs, fl, **kw)
    b, _, _ = lauf(cs, fl, **kw, verkauf_faktor=.67)
    typen = {s.type.name for _, s in b}
    assert {"KAUF_1", "RUECKKAUF", "RUECKKAUF_STOP", "STOPLOSS"} <= typen
    assert [(i, s) for i, s in a if s.type.name not in TEIL] == \
           [(i, s) for i, s in b if s.type.name not in TEIL]


def test_plan_und_telegram_nennen_die_reduzierten_mengen():
    cs, fl = bau(ANLAUF)
    pos = Position()
    for i in range(len(cs)):
        evaluate(cs[:i+1], fl[:i+1], pos, **LIVE, verkauf_faktor=.67)
    a = main.positions_plan(cs, fl, LIVE, pos)
    b = main.positions_plan(cs, fl, {**LIVE, "verkauf_faktor": .67}, pos)
    assert a["teilgewinn"] and any(x["tranche"] == 40 for x in a["teilgewinn"])
    assert [x["tranche"] for x in b["teilgewinn"]] == \
           [round(x["tranche"] * .67, 8) for x in a["teilgewinn"]]
    assert a["stop"] == b["stop"] and a["nachkauf"] == b["nachkauf"]
    assert "26.8 %" in format_plan(b)
    s = Signal(cs[-1].ts, SignalType.TEILVERKAUF_LADDER, 131, 10.05, "Test")
    assert "10.05 %" in format_signal(s.to_dict())


def test_backtest_reicht_faktor_an_engine_weiter():
    cs, fl = pfad()
    cfg = backtest.V("E444 kuenstlich", **KW, verkauf_faktor=.67)
    # Derselbe offizielle Laufweg wie das spaetere Gitter, ohne Markt-Daten.
    sig = backtest.run_backtest(cs, fl, cfg, start_ms=cs[0].ts)
    assert any(s["type"] == "TEILVERKAUF_1" for s in sig)
    assert [s["tranche_pct"] for s in sig if s["type"] == "TEILVERKAUF_1"] == [26.8]


def _abrechnung(short):
    cs = _cs()
    if short:
        from dataclasses import replace
        cs[-1] = replace(cs[-1], open=80, high=80, low=80, close=80)
    kauf = "SHORT_1" if short else "KAUF_1"
    teile = ("SHORT_TP_LADDER", "SHORT_TP_1", "SHORT_TP_2") if short else \
            ("TEILVERKAUF_LADDER", "TEILVERKAUF_1", "TEILVERKAUF_2")
    enden = ("SHORT_COVER_REST", "SHORT_STOPLOSS") if short else ("VERKAUF_REST", "STOPLOSS")
    basis = [_sig(0, kauf, 100, 100)]
    voll = backtest.simulate(basis, cs, fee=0, start_ms=cs[0].ts)["offene_position"]
    assert voll > 0
    for typ, menge in zip(teile, (10.05, 26.8, 26.8)):
        sig = basis + [_sig(1, typ, 100, menge)]
        rest = backtest.simulate(sig, cs, fee=0, start_ms=cs[0].ts)
        assert rest["trades"] == 1
        assert abs(rest["offene_position"] - voll * (1 - menge / 100)) < 1e-6
        for ende in enden:
            fertig = backtest.simulate(sig + [_sig(2, ende, 100, 20)], cs,
                                      fee=0, start_ms=cs[0].ts)
            assert fertig["offene_position"] == 0


def test_simulate_long_bucht_signalmenge_und_ganzen_rest():
    _abrechnung(False)


def test_simulate_short_bucht_signalmenge_und_ganzen_rest():
    _abrechnung(True)


def test_bruchteile_ueberleben_state_json():
    cs, fl = bau(ANLAUF[:5])
    sig, _, pos = lauf(cs, fl, **LIVE, verkauf_faktor=.67)
    assert any(s.type.name == "TEILVERKAUF_LADDER" for _, s in sig)
    assert abs(pos.bestand_pct - 14.95) < 1e-8
    gespeichert = json.loads(json.dumps(main.pos_to_state(pos)))
    assert main.pos_from_state(gespeichert).bestand_pct == pos.bestand_pct


WORKER = r'''
import contextlib, io, json, sys
from pathlib import Path
import main
from strategy_core import Candle, FlowPoint
from telegram_notify import format_signal
d = Path(sys.argv[1])
v = json.loads((d / "input.json").read_text())
cs, fl = [Candle(**x) for x in v["cs"]], [FlowPoint(**x) for x in v["fl"]]
texte, sig = [], []
main.send_text = lambda t, **kw: texte.append(t)
main.send_signals = lambda s, **kw: (sig.extend(s), texte.extend(format_signal(x) for x in s))
# Plan/Vorschau sind Zusammenfassungen je Lauf, kein Ereignis je Kerze.
main.send_plan = main.send_vorschau = lambda *a, **kw: None
with contextlib.redirect_stdout(io.StringIO()):
    main.run_engine(fetch=lambda oi=None: (cs, fl, []), data_dir=d, dry_run=True)
print(json.dumps([texte, sig, json.loads((d / "state.json").read_text())]))
'''


def _prozesse(schrittweise):
    from dataclasses import asdict
    cs, fl = bau(ANLAUF + [130, 131, 130, 128.5])
    texte, sig, staende = [], [], []
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "config.json").write_text(json.dumps({**LIVE, "ausbruch_ruecktest": True,
                                                   "verkauf_faktor": .67}))
        for k in (range(24, len(cs)+1) if schrittweise else [len(cs)]):
            (d / "input.json").write_text(json.dumps({"cs": [asdict(x) for x in cs[:k]],
                                                       "fl": [asdict(x) for x in fl[:k]]}))
            p = subprocess.run([sys.executable, "-c", WORKER, tmp], cwd=ENG,
                               env={**os.environ, "PYTHONUTF8": "1"}, capture_output=True,
                               text=True, encoding="utf-8", check=True)
            t, s, state = json.loads(p.stdout)
            texte.extend(t); sig.extend(s); staende.append(state)
    return texte, sig, staende


def test_getrennte_prozesse_gleiche_signale_telegram_und_state():
    t1, s1, z1 = _prozesse(False)
    t2, s2, z2 = _prozesse(True)
    assert {"RUECKKAUF", "RUECKKAUF_STOP", "TEILVERKAUF_LADDER"} <= {s["type"] for s in s2}
    assert any(abs(z["bestand_pct"] - 14.95) < 1e-8 for z in z2)
    assert t1 == t2 and s1 == s2
    assert z1[-1]["bestand_pct"] == z2[-1]["bestand_pct"]


def test_rest_meldung_verspricht_keine_feste_20_prozent():
    for typ in (SignalType.VERKAUF_REST, SignalType.SHORT_COVER_REST):
        s = Signal(_cs()[0].ts, typ, 100, 20, "Gegen-Muster")
        assert s.to_dict()["type"] in ("VERKAUF_REST", "SHORT_COVER_REST")
        text = format_signal(s.to_dict())
        assert "gesamter Rest der Position" in text and "20 %" not in text
