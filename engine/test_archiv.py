"""E44.1: Tests fuer das Coinalyze-Archiv (kein Netz noetig)."""
import tempfile
from pathlib import Path

import archiv
import backtest

H = archiv.KERZE_MS


def test_zusammen_neu_gewinnt_alt_bleibt():
    alt = {1 * H: 10.0, 2 * H: 20.0}
    neu = {2 * H: 21.0, 3 * H: 30.0}
    # Vorprobe: beide Faelle (Ueberschneidung und nur-alt) kommen im Szenario vor
    assert set(alt) & set(neu) and set(alt) - set(neu)
    m = archiv.zusammen(alt, neu)
    assert m == {1 * H: 10.0, 2 * H: 21.0, 3 * H: 30.0}
    assert alt == {1 * H: 10.0, 2 * H: 20.0}          # Eingabe unveraendert


def test_zusammen_mit_leeren_karten():
    assert archiv.zusammen({}, {H: 1.0}) == {H: 1.0}
    assert archiv.zusammen({H: 1.0}, {}) == {H: 1.0}
    assert archiv.zusammen(None, None) == {}


def test_nur_abgeschlossene_kerzen():
    jetzt = 10 * H
    karte = {8 * H: 1.0, 9 * H: 2.0, 9 * H + 1: 3.0}
    # Vorprobe: die laufende Kerze (9H+1, endet nach jetzt) ist im Szenario enthalten
    assert any(ts + H > jetzt for ts in karte)
    assert archiv.nur_abgeschlossen(karte, jetzt) == {8 * H: 1.0, 9 * H: 2.0}


def test_speichern_und_laden_behaelt_liquidations_paare():
    with tempfile.TemporaryDirectory() as d:
        pfad = Path(d) / "unter" / "a.json"
        daten = {"oi": {H: 5.0}, "liq": {H: (1.5, 2.5)}, "fut": {H: -3.0}, "ls": {}}
        archiv.speichern(daten, pfad)
        zurueck = archiv.laden(pfad)
        assert zurueck["oi"] == {H: 5.0}
        assert zurueck["liq"] == {H: (1.5, 2.5)}
        assert isinstance(zurueck["liq"][H], tuple)    # build_series erwartet Tupel
        assert zurueck["fut"] == {H: -3.0} and zurueck["ls"] == {}


def test_fehlende_oder_kaputte_datei_ist_kein_fehler():
    with tempfile.TemporaryDirectory() as d:
        leer = archiv.laden(Path(d) / "gibtesnicht.json")
        assert leer == {r: {} for r in archiv.REIHEN}
        kaputt = Path(d) / "k.json"
        kaputt.write_text("{nicht json", encoding="utf-8")
        assert archiv.laden(kaputt) == {r: {} for r in archiv.REIHEN}


def test_backtest_mischt_das_archiv_wirklich_dazu():
    frisch_oi = {5 * H: 100.0}
    arch = {"oi": {1 * H: 90.0, 5 * H: 99.0}, "liq": {1 * H: (1.0, 0.0)},
            "fut": {}, "ls": {}}
    oi, liq, fut, ls, info = backtest.archiv_mischen(frisch_oi, {}, {}, {}, arch)
    assert oi == {1 * H: 90.0, 5 * H: 100.0}           # alt ergaenzt, frisch gewinnt
    assert liq == {1 * H: (1.0, 0.0)}
    assert info == {"oi_nur_archiv": 1}
    # Das Fenster beginnt an der ersten OI-Kerze: mit Archiv frueher als ohne
    assert min(oi) < min(frisch_oi)


def test_backtest_ruft_archiv_mischen_im_hauptlauf_auf():
    quelle = Path(backtest.__file__).read_text(encoding="utf-8")
    haupt = quelle[quelle.index("def main():"):]
    assert "archiv_mischen(" in haupt and "archiv.laden()" in haupt
    # und zwar BEVOR die Reihen gebaut werden
    assert haupt.index("archiv_mischen(") < haupt.index("build_series(raw, funding, oi_map")


def test_archiv_ohne_key_tut_nichts():
    import os
    alt = os.environ.pop("COINALYZE_API_KEY", None)
    try:
        assert archiv.main() == 0
    finally:
        if alt is not None:
            os.environ["COINALYZE_API_KEY"] = alt
