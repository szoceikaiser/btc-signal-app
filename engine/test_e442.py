"""E44.2: Tests fuer Wechselwirkungs-Tabelle und Monats-Probe (kein Netz noetig)."""
import backtest


def _g(label, **kw):
    return backtest.V(label, **kw)


def _mini_gitter():
    # 2x2 aus rest_halten x neustart_mit_rest, dazu eine Zeile mit ZWEI Unterschieden
    # ohne Partner und eine Kopie-Ecke in anderer Reihenfolge.
    return [
        _g("A+B", rest_halten=True, neustart_mit_rest=True),
        _g("Basis"),
        _g("A", rest_halten=True),
        _g("B", neustart_mit_rest=True),
        _g("zwei Unterschiede", rest_halten=True, no_flip=True, be_im_plus=True),
    ]


def test_vierergruppe_wird_gefunden_und_auf_die_aus_ecke_ausgerichtet():
    g = backtest.e442_vierergruppen(_mini_gitter())
    # Vorprobe: das Szenario enthaelt genau eine saubere Gruppe
    assert len(g) == 1, g
    basis, a, b, ab, ka, kb = g[0]
    assert basis == "Basis" and ab == "A+B"          # obwohl A+B im Gitter zuerst steht
    assert {a, b} == {"A", "B"} and {ka, kb} == {"rest_halten", "neustart_mit_rest"}
    assert (a == "A") == (ka == "rest_halten")


def test_zeilen_mit_zwei_unterschieden_bilden_keine_gruppe():
    gitter = [_g("Basis"), _g("A", rest_halten=True, no_flip=True),
              _g("B", neustart_mit_rest=True),
              _g("A+B", rest_halten=True, no_flip=True, neustart_mit_rest=True)]
    assert backtest.e442_vierergruppen(gitter) == []


def test_ohne_a_plus_b_keine_gruppe():
    gitter = [_g("Basis"), _g("A", rest_halten=True), _g("B", neustart_mit_rest=True)]
    assert backtest.e442_vierergruppen(gitter) == []


def test_wechselwirkung_rechnet_richtig():
    # Zahlen aus dem Lauf vom 26.09.2026 (rest_halten x neustart_mit_rest)
    assert backtest.e442_wechselwirkung(25.4, 13.8, 25.5, 27.6) == 13.7
    assert backtest.e442_wechselwirkung(10.0, 12.0, 13.0, 15.0) == 0.0   # additiv


def test_echtes_gitter_hat_die_16_gruppen_der_analyse():
    g = backtest.e442_vierergruppen(backtest.GRID)
    paare = {frozenset((x[4], x[5])) for x in g}
    assert len(g) >= 16
    for p in (("buy_ladder", "flush_entry"), ("cooldown_h", "min_stop_pct"),
              ("rest_halten", "neustart_mit_rest"), ("min_bein_pct", "bein_richtung")):
        assert frozenset(p) in paare, p


def _m(*werte):
    return [{"monat": f"2026-0{i + 1}", "rendite_pct": w} for i, w in enumerate(werte)]


def test_monats_probe_kippt_bei_einem_ausreisser():
    live = _m(1.0, 1.0, 1.0, 1.0)
    var = _m(0.5, 0.5, 0.5, 5.0)                     # Vorsprung nur aus Monat 4
    mp = backtest.monats_probe(live, var)
    assert mp["summe"] == 2.5                        # Vorprobe: Vorsprung gesamt positiv
    assert mp["kritischer_monat"] == "2026-04"
    assert mp["min_ohne_einen"] == -1.5
    assert mp["haelt"] is False


def test_monats_probe_haelt_bei_breitem_vorsprung():
    mp = backtest.monats_probe(_m(1.0, 1.0, 1.0), _m(2.0, 2.0, 2.0))
    assert mp["summe"] == 3.0 and mp["min_ohne_einen"] == 2.0 and mp["haelt"] is True


def test_monats_probe_ohne_gemeinsame_monate():
    assert backtest.monats_probe([], _m(1.0))["haelt"] is False


def test_abschnitt_zeigt_tabelle_und_probe():
    gitter = [_g("Basis"), _g("A", rest_halten=True), _g("B", neustart_mit_rest=True),
              _g("A+B", rest_halten=True, neustart_mit_rest=True),
              _g("LIVE-heute +X", panel=False, rest_halten=True)]
    gitter[0]["panel"] = True
    r = {"Basis": 10.0, "A": 8.0, "B": 11.0, "A+B": 15.0, "LIVE-heute +X": 12.0}
    results = [(c, [], {}, {"rendite_pct": r[c["label"]],
                            "monate": _m(1.0, 1.0) if c["label"] == "Basis"
                            else _m(2.0, 2.0)}) for c in gitter]
    # H1 und H2 bewusst verschieden, sonst faellt eine vertauschte Haelfte nicht auf
    halves = [(c, {"rendite_pct": r[c["label"]] / 2}, {"rendite_pct": r[c["label"]] / 4})
              for c in gitter]
    z = "\n".join(backtest.e442_abschnitt(results, halves, gitter, "Basis"))
    assert "## E44: Wechselwirkungen und Monats-Probe" in z
    assert "| `rest_halten` | `neustart_mit_rest` | +10.0 | +8.0 | +11.0 | +15.0 | **+6.0** | +3.0 | +1.5 |" in z
    assert "| LIVE-heute +X | +2.0 | +1.0 | 2026-01 | **ja** |" in z


def test_abschnitt_ist_im_bericht_verdrahtet():
    from pathlib import Path
    q = Path(backtest.__file__).read_text(encoding="utf-8")
    haupt = q[q.index("def main():"):]
    assert "e442_abschnitt(results, halves, GRID, panel_cfg[\"label\"])" in haupt
