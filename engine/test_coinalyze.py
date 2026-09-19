"""Offline-Tests fuer die Coinalyze-Anbindung (E9.1). Kein Netz, kein Key noetig."""

import io
import json

import coinalyze


def test_build_url_enthaelt_endpoint_und_params():
    url = coinalyze.build_url("open-interest-history",
                              {"symbols": "BTCUSDT_PERP.A", "interval": "4hour"})
    assert url.startswith("https://api.coinalyze.net/v1/open-interest-history?")
    assert "symbols=BTCUSDT_PERP.A" in url or "symbols=BTCUSDT_PERP.A".replace(".", "%2E") in url
    assert "interval=4hour" in url


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
        return False


def test_get_json_nutzt_injizierten_opener_und_key():
    captured = {}

    def fake_opener(req, timeout=0):
        captured["url"] = req.full_url
        captured["key"] = req.headers.get("Api_key") or req.headers.get("api_key")
        return _FakeResp(json.dumps([{"symbol": "X", "history": [1, 2, 3]}]).encode())

    data = coinalyze.get_json("liquidation-history",
                              {"symbols": "BTCUSDT_PERP.A", "interval": "4hour"},
                              api_key="KEY123", opener=fake_opener)
    assert data == [{"symbol": "X", "history": [1, 2, 3]}]
    assert captured["key"] == "KEY123"
    assert "liquidation-history" in captured["url"]


def test_sample_kuerzt_history_auf_letzte_drei():
    data = [{"symbol": "X", "history": [1, 2, 3, 4, 5]}]
    assert coinalyze._sample(data) == [{"symbol": "X", "history": [3, 4, 5]}]
    # Robust gegen unerwartete Formen
    assert coinalyze._sample({"foo": "bar"}) == {"foo": "bar"}


def _fake(resp):
    def opener(req, timeout=0):
        return _FakeResp(json.dumps(resp).encode())
    return opener


# Format am 2026-07-24 per Test-Lauf bestaetigt
def test_oi_by_ts_nimmt_close_und_wandelt_in_ms():
    resp = [{"symbol": "BTCUSDT_PERP.A", "history": [
        {"t": 1784865600, "o": 1, "h": 2, "l": 0.5, "c": 6762600631.87},
        {"t": 1784880000, "o": 1, "h": 2, "l": 0.5, "c": 6787210608.47}]}]
    d = coinalyze.oi_by_ts("KEY", opener=_fake(resp))
    assert d == {1784865600000: 6762600631.87, 1784880000000: 6787210608.47}


def test_liquidations_by_ts_long_und_short():
    resp = [{"symbol": "BTCUSDT_PERP.A", "history": [
        {"t": 1784865600, "l": 281390.06, "s": 1587451.09}]}]
    d = coinalyze.liquidations_by_ts("KEY", opener=_fake(resp))
    assert d == {1784865600000: (281390.06, 1587451.09)}


def test_history_points_findet_symbol():
    resp = [{"symbol": "BTCUSDT_PERP.A", "history": [{"t": 1, "c": 9}]}]
    assert coinalyze._history_points(resp) == [{"t": 1, "c": 9}]
    assert coinalyze._history_points([]) == []


# ------------------------------------------------- E16: Futures-Delta + Positionierung
# Antwortformat 1:1 aus der echten Probe vom 28.07.2026 (site/data/coinalyze_probe.json).

ECHTE_OHLCV_ANTWORT = [{
    "symbol": "BTCUSDT_PERP.A",
    "history": [
        {"t": 1785211200, "o": 63310, "h": 63642.2, "l": 63187.2, "c": 63476.8,
         "v": 17816.541000000874, "bv": 9394.95300000063, "tx": 108788, "btx": 57349},
        {"t": 1785225600, "o": 63476.8, "h": 63569, "l": 63263.5, "c": 63430.8,
         "v": 17703.739000000947, "bv": 8049.849000000347, "tx": 109117, "btx": 53442},
    ],
}]

ECHTE_LS_ANTWORT = [{
    "symbol": "BTCUSDT_PERP.A",
    "history": [
        {"t": 1785211200, "r": 1.867, "l": 65.12, "s": 34.88},
        {"t": 1785225600, "r": 1.8868, "l": 65.36, "s": 34.64},
    ],
}]


def _mit_antwort(monkey_wert):
    """Ersetzt fetch_history durch eine feste Antwort (kein Netz im Test)."""
    original = coinalyze.fetch_history
    coinalyze.fetch_history = lambda *a, **k: monkey_wert
    return original


def test_fut_delta_rechnet_kaeufe_minus_verkaeufe():
    """Delta = Kaeufe - Verkaeufe = bv - (v - bv) = 2*bv - v."""
    orig = _mit_antwort(ECHTE_OHLCV_ANTWORT)
    try:
        d = coinalyze.fut_delta_by_ts("key")
    finally:
        coinalyze.fetch_history = orig
    assert set(d) == {1785211200 * 1000, 1785225600 * 1000}
    # Kerze 1: 2*9394.953 - 17816.541 = +973.365 (mehr Kaeufe als Verkaeufe)
    assert abs(d[1785211200 * 1000] - 973.365) < 0.01, d
    # Kerze 2: 2*8049.849 - 17703.739 = -1604.041 (mehr Verkaeufe)
    assert abs(d[1785225600 * 1000] + 1604.041) < 0.01, d
    assert d[1785211200 * 1000] > 0 > d[1785225600 * 1000], "Vorzeichen muss drehen"


def test_long_short_liest_den_long_anteil():
    orig = _mit_antwort(ECHTE_LS_ANTWORT)
    try:
        d = coinalyze.long_short_by_ts("key")
    finally:
        coinalyze.fetch_history = orig
    assert d[1785211200 * 1000] == 65.12 and d[1785225600 * 1000] == 65.36


def test_parser_ueberspringen_unvollstaendige_punkte():
    """Fehlende Felder duerfen den Lauf nicht abbrechen — lieber weniger Punkte."""
    kaputt = [{"symbol": "BTCUSDT_PERP.A", "history": [
        {"t": 1, "v": 10.0},                    # bv fehlt
        {"t": 2, "bv": 5.0},                    # v fehlt
        {"t": 3, "v": 10.0, "bv": 7.0},         # vollstaendig
    ]}]
    orig = _mit_antwort(kaputt)
    try:
        d = coinalyze.fut_delta_by_ts("key")
    finally:
        coinalyze.fetch_history = orig
    assert d == {3000: 4.0}, d


# --------------------------------------------- E37: Spot-Maerkte (Kaisers Frage 19.09.)
# Diese Tests sichern die SCHEMA-RATEREI ab. Wir kennen das Antwortformat von
# /spot-markets noch nicht; die Auswahl-Logik darf deshalb nicht an bestimmten
# Feldnamen haengen. Genau das wird hier geprueft — mit drei verschiedenen Formen.

def test_btc_spot_maerkte_findet_btc_egal_wie_die_felder_heissen():
    roh = [
        {"symbol": "BTCUSDT.A", "base_asset": "BTC"},          # BTC im Symbol
        {"market": "xbt-usd", "base": "Bitcoin", "quote": "BTC"},  # BTC nur im Quote
        {"symbol": "ETHUSDT.A", "base_asset": "ETH"},          # kein BTC -> raus
        {"symbol": "SOLUSD", "base_asset": "SOL"},             # kein BTC -> raus
    ]
    treffer = coinalyze._btc_spot_maerkte(roh)
    assert len(treffer) == 2, treffer
    assert all("btc" in coinalyze._als_text(e) for e in treffer)
    # Die Gegenprobe ist der eigentliche Punkt: ETH und SOL duerfen NICHT durchrutschen.
    assert not any("ETH" in str(e) or "SOL" in str(e) for e in treffer), treffer


def test_symbol_von_liest_verschiedene_feldnamen_und_gibt_sonst_leer():
    assert coinalyze._symbol_von({"symbol": "BTCUSDT.A"}) == "BTCUSDT.A"
    assert coinalyze._symbol_von({"market": "BTC-USD"}) == "BTC-USD"
    assert coinalyze._symbol_von({"symbol_on_exchange": "BTCUSD"}) == "BTCUSD"
    # Kein brauchbares Feld -> leerer String, nicht Absturz und kein Zahlenmuell
    assert coinalyze._symbol_von({"base_asset": "BTC"}) == ""
    assert coinalyze._symbol_von({"symbol": 17}) == ""
    assert coinalyze._symbol_von("BTCUSDT.A") == ""


def test_waehle_spot_symbole_nimmt_aggregiertes_zuerst_und_dann_je_boerse():
    maerkte = [
        {"symbol": "BTCUSD_BINANCE", "exchange": "Binance", "quote_asset": "USD"},
        {"symbol": "BTCUSDT.A", "exchange": "aggregated", "quote_asset": "USDT"},
        {"symbol": "BTCUSD_COINBASE", "exchange": "Coinbase", "quote_asset": "USD"},
        {"symbol": "BTCUSD_KRAKEN", "exchange": "Kraken", "quote_asset": "USD"},
    ]
    gewaehlt = coinalyze._waehle_spot_symbole(maerkte)
    assert gewaehlt[0] == "BTCUSDT.A", gewaehlt          # aggregiertes hat Vorrang
    assert "BTCUSD_BINANCE" in gewaehlt and "BTCUSD_COINBASE" in gewaehlt
    # Kraken gehoert nicht zu Furkans vier Boersen -> darf nicht mitkommen
    assert "BTCUSD_KRAKEN" not in gewaehlt, gewaehlt
    assert len(gewaehlt) == len(set(gewaehlt)) <= coinalyze.SPOT_TESTE_MAX


def _spot_opener(punkte):
    """Opener, der eine ohlcv-Antwort mit genau diesen Punkten liefert."""
    def fake(req, timeout=0):
        sym = "BTCUSDT.A"
        return _FakeResp(json.dumps([{"symbol": sym, "history": punkte}]).encode())
    return fake


def test_pruefe_spot_symbol_verlangt_v_UND_bv():
    """Ohne beide Zahlen gibt es kein Delta — halbe Daten duerfen nicht als 'ja' gelten."""
    vier_h = 4 * 3600
    voll = [{"t": 1_700_000_000 + i * vier_h, "v": 10.0, "bv": 6.0} for i in range(3)]
    d = coinalyze._pruefe_spot_symbol("KEY", "BTCUSDT.A", opener=_spot_opener(voll))
    assert d["punkte"] == 3 and d["hat_v_und_bv"] is True, d

    nur_v = [{"t": 1_700_000_000 + i * vier_h, "v": 10.0} for i in range(3)]
    d2 = coinalyze._pruefe_spot_symbol("KEY", "BTCUSDT.A", opener=_spot_opener(nur_v))
    assert d2["punkte"] == 3, d2
    assert d2["hat_v_und_bv"] is False, d2       # <- der entscheidende Fall


def test_pruefe_spot_symbol_misst_die_reichweite_in_tagen():
    """Die Reichweite entscheidet, ob ein Backtest ueberhaupt moeglich ist."""
    vier_h = 4 * 3600
    punkte = [{"t": 1_700_000_000 + i * vier_h, "v": 1.0, "bv": 0.5} for i in range(61)]
    d = coinalyze._pruefe_spot_symbol("KEY", "BTCUSDT.A", opener=_spot_opener(punkte))
    assert d["reichweite_tage"] == 10.0, d       # 60 Schritte a 4 h = 10 Tage


def test_spot_probe_urteil_unterscheidet_aggregiert_von_einzelboersen():
    """Das Urteil muss die drei Faelle auseinanderhalten — daran haengt der naechste Schritt."""
    vier_h = 4 * 3600
    voll = [{"t": 1_700_000_000 + i * vier_h, "v": 10.0, "bv": 6.0} for i in range(3)]

    def opener_fuer(maerkte):
        zustand = {"erster": True}

        def fake(req, timeout=0):
            if "spot-markets" in req.full_url:
                return _FakeResp(json.dumps(maerkte).encode())
            sym = "BTCUSDT.A" if "BTCUSDT.A" in req.full_url else "BTCUSD_BINANCE"
            return _FakeResp(json.dumps([{"symbol": sym, "history": voll}]).encode())
        return fake

    mit_agg = [{"symbol": "BTCUSDT.A", "exchange": "aggregated", "quote_asset": "USDT"}]
    r1 = coinalyze.spot_probe("KEY", opener=opener_fuer(mit_agg))
    assert r1["_ergebnis"].startswith("JA"), r1["_ergebnis"]

    ohne_agg = [{"symbol": "BTCUSD_BINANCE", "exchange": "Binance", "quote_asset": "USD"}]
    r2 = coinalyze.spot_probe("KEY", opener=opener_fuer(ohne_agg))
    assert r2["_ergebnis"].startswith("TEILWEISE"), r2["_ergebnis"]


def test_spot_probe_meldet_fehlenden_endpunkt_als_klares_nein():
    """Gibt es /spot-markets nicht, muss das Urteil das sagen — nicht still leer bleiben."""
    import urllib.error

    def fake(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {},
                                     io.BytesIO(b'{"message":"Not Found"}'))

    r = coinalyze.spot_probe("KEY", opener=fake)
    assert r["spot_markets"]["http_error"] == 404, r
    assert "NICHT geantwortet" in r["_ergebnis"], r["_ergebnis"]


def test_pruefe_spot_symbol_meldet_leere_history_statt_abzustuerzen():
    """Der wahrscheinlichste Fehlerfall: Symbol geraten, Antwort kommt, History leer.

    Ohne Schutz greift die Auswertung auf punkte[0] zu und wirft IndexError — dann
    verschwindet die GANZE Spot-Probe hinter einer Fehlermeldung, statt zu sagen,
    welches Symbol nichts geliefert hat.
    """
    def fake(req, timeout=0):
        return _FakeResp(json.dumps([{"symbol": "BTCUSDT.A", "history": []}]).encode())

    d = coinalyze._pruefe_spot_symbol("KEY", "BTCUSDT.A", opener=fake)
    assert d["punkte"] == 0, d
    assert "hinweis" in d, d                    # sagt, was los war
    assert "hat_v_und_bv" not in d, d           # behauptet NICHT, es sei brauchbar
