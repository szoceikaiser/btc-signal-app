"""E44.5: Gitter, Entscheidungsgrenzen und vollstaendige Messwege."""
import inspect
from itertools import product
import backtest as bt
import e445


def _kz(h1=10, h2=20, dd=-5, werte=(1, 1, 1)):
    return dict(h1=h1, h2=h2, dd=dd,
                monate=[dict(monat=f"2026-{i+1:02}", rendite_pct=x) for i, x in enumerate(werte)])


def test_gitter_acht_ecken_genau_live_basis():
    live = next(c for c in bt.GRID if c["panel"])
    assert len(bt.E445_GRID) == 9
    keys = ("ausbruch_ruecktest", "verkauf_faktor", "rest_halten")
    assert {tuple(c[k] for k in keys) for c in bt.E445_GRID[:8]} == set(product((False, True), (1.0, .67), (False, True)))
    assert len({c["label"] for c in bt.GRID}) == len(bt.GRID)
    for c in bt.E445_GRID[:8]:
        assert all(c[k] == live[k] for k in bt.EVAL_KEYS if k not in keys)
        assert c in bt.GRID
    assert sum(c["panel"] for c in bt.GRID) == 1
    haupt = next(c for c in bt.E445_GRID if c["label"] == bt.E445_HAUPT)
    assert [k for k in bt.EVAL_KEYS if live[k] != haupt[k]] == ["ausbruch_ruecktest"]


def test_robustheit_nur_sechs_statt_zwoelf():
    h = next(c for c in bt.E445_GRID if c["label"] == bt.E445_HAUPT)
    r = bt.E445_GRID[-1]
    assert h["ruecktest_fenster"] == 12 and r["label"] == bt.E445_ROBUST
    assert r["ruecktest_fenster"] == 6
    assert [k for k in bt.EVAL_KEYS if h[k] != r[k]] == ["ruecktest_fenster"]


def test_hauptzeile_beide_haelften_und_exakte_grenze():
    live, var = _kz(), _kz(11, 21, -6, (2, 2, 2))
    assert e445.regel(live, var, True)["bestanden"]
    for k in ("h1", "h2"):
        schwach = dict(var, **{k: var[k] - .01})
        assert not e445.regel(live, schwach, True)["bestanden"]


def test_kombination_braucht_zwei_punkte():
    live, var = _kz(), _kz(12, 22, -6, (2, 2, 2))
    assert e445.regel(live, var)["bestanden"]
    for k in ("h1", "h2"):
        assert not e445.regel(live, dict(var, **{k: var[k] - .01}))["bestanden"]


def test_rueckgang_verhindert_positive_renditeentscheidung():
    live, var = _kz(), _kz(15, 25, -6, (2, 2, 2))
    assert e445.regel(live, var, True)["bestanden"]
    assert not e445.regel(live, dict(var, dd=-6.01), True)["bestanden"]


def test_monatsprobe_ausreisser_null_und_fehlende_monate():
    live = _kz()
    assert e445.regel(live, _kz(15, 25, -5, (2, 2, 2)), True)["bestanden"]
    for werte in ((1, 1, 9), (0, 0, 9), (2, 2)):
        assert not e445.regel(live, _kz(15, 25, -5, werte), True)["bestanden"]


def _messung():
    results, halves = [], []
    for c in bt.E445_GRID:
        k = _kz() if c["panel"] else _kz(11.5, 21.5, -5, (2, 2, 2))
        p = dict(rendite_pct=10 if c["panel"] else 15, max_drawdown_pct=k["dd"], monate=k["monate"])
        results.append((c, [], {}, p))
        halves.append((c, dict(rendite_pct=k["h1"]), dict(rendite_pct=k["h2"])))
    return results, halves


def test_auswertung_rollen_wechselwirkungen_und_bericht():
    r, h = _messung()
    m = e445.auswerten(r, h)
    assert len(m["zeilen"]) == 9 and len(m["wechselwirkungen"]) == 6
    assert m["wechselwirkungen"][0]["voll"] == -5
    for z in m["zeilen"]:
        if z["rolle"] in ("Basis", "Robustheit"):
            assert z["urteil"] is None
        else:
            assert z["urteil"]["bestanden"] == (z["label"] == bt.E445_HAUPT)
    text = e445.bericht(m)
    assert "keine Entscheidung" in text and "nicht erfuellt" in text and "| erfuellt |" in text
    assert "e445_abschnitt(results, halves)" in inspect.getsource(bt.main)


def test_fehlende_haelfte_keine_entscheidung():
    r, h = _messung()
    assert len(e445.auswerten(r, h)["zeilen"]) == 9
    for rr, hh in ((r[:-1], h), (r, h[:-1])):
        try:
            e445.auswerten(rr, hh)
        except ValueError as e:
            assert "Kein Urteil" in str(e)
        else:
            raise AssertionError("Unvollstaendige Messung akzeptiert")


def test_alter_aus_echter_engine_ohne_signalveraenderung():
    from test_e443 import bau, ANLAUF, LIVE
    cs, fl = bau(ANLAUF)
    cfg = dict(LIVE, ausbruch_ruecktest=True)
    sig = bt.run_backtest(cs, fl, cfg, start_ms=cs[0].ts, diagnose_e445=True)
    rk = [s for s in sig if s["type"] == "RUECKKAUF"]
    assert len(rk) == 1
    assert rk[0]["beobachtung_kerzen"] == 1
    ohne = bt.run_backtest(cs, fl, cfg, start_ms=cs[0].ts)
    assert [{k: v for k, v in s.items() if k != "beobachtung_kerzen"} for s in sig] == ohne


def test_alte_marken_grenze_im_bericht():
    r, h = _messung()
    c, _, sc, p = r[-1]
    r[-1] = c, [dict(type="RUECKKAUF", beobachtung_kerzen=x) for x in (1, 12, 13, 50)], sc, p
    z = e445.auswerten(r, h)["zeilen"][-1]
    assert z["rueckkaeufe"] == 4
    assert z["alte_marken"] == 2 and z["max_alter"] == 50
    assert "| 4 | 4 | 2 | 50 |" in e445.bericht(e445.auswerten(r, h))
