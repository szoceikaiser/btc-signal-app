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
# Diese Tests sichern die Auswahl der Boersen-Symbole. Das Schema ist seit dem Lauf vom
# 19.09.2026 bekannt: {symbol, exchange, symbol_on_exchange, base_asset, quote_asset,
# has_buy_sell_data}. Der erste Anlauf hatte hier ".A" faelschlich fuer "aggregiert"
# gehalten und deshalb BTCARS (argentinischer Peso) und WLDBTC (Worldcoin) gewaehlt —
# genau dagegen sind die folgenden Gegenproben gerichtet.

def _markt(sym, ex, base="BTC", quote="USDT", buysell=True):
    return {"symbol": sym, "exchange": ex, "symbol_on_exchange": sym.split(".")[0],
            "base_asset": base, "quote_asset": quote, "has_buy_sell_data": buysell}


def test_ist_btc_dollar_markt_weist_die_fallen_der_ersten_probe_ab():
    codes = coinalyze.BOERSEN_CODES
    assert coinalyze._ist_btc_dollar_markt(_markt("BTCUSDT.A", "A"), codes) is True
    # 1. Worldcoin GEGEN Bitcoin: BTC steht im Namen, ist aber der Quote, nicht die Basis
    assert coinalyze._ist_btc_dollar_markt(
        _markt("WLDBTC.A", "A", base="WLD", quote="BTC"), codes) is False
    # 1b. Derselbe Fehler, aber isoliert: Quote IST ein Dollar, nur die Basis stimmt
    #     nicht. Ohne diesen Fall wuerde ein Wegfall der base_asset-Pruefung nicht
    #     auffallen — bei WLDBTC faengt ihn schon die Quote-Pruefung ab.
    assert coinalyze._ist_btc_dollar_markt(
        _markt("ETHUSDT.A", "A", base="ETH", quote="USDT"), codes) is False
    # 2. Argentinischer Peso: BTC ist Basis, aber die Gegenwaehrung ist kein Dollar
    assert coinalyze._ist_btc_dollar_markt(
        _markt("BTCARS.A", "A", quote="ARS"), codes) is False
    # 3. Falsche Boerse (Kraken = K gehoert nicht zu Furkans vier)
    assert coinalyze._ist_btc_dollar_markt(_markt("BTCUSDT.K", "K"), codes) is False
    # 4. Ohne Kauf-/Verkaufsdaten nuetzt der Markt nichts
    assert coinalyze._ist_btc_dollar_markt(
        _markt("BTCUSDT.C", "C", buysell=False), codes) is False


def test_je_boerse_ein_symbol_folgt_fester_quote_rangfolge():
    """Ohne feste Rangfolge haengt das Ergebnis an der Listenreihenfolge — dann misst
    jeder Lauf einen anderen Markt und die Zahlen sind nicht vergleichbar."""
    maerkte = [
        _markt("BTCUSDC.A", "A", quote="USDC"),     # schlechterer Rang, kommt zuerst
        _markt("BTCUSDT.A", "A", quote="USDT"),     # bester Rang, kommt spaeter
        _markt("BTCUSD.C", "C", quote="USD"),
        _markt("BTCUSDT.K", "K"),                   # Kraken -> darf nicht auftauchen
    ]
    gewaehlt = coinalyze._je_boerse_ein_symbol(maerkte)
    assert gewaehlt["A"]["symbol"] == "BTCUSDT.A", gewaehlt     # USDT schlaegt USDC
    assert gewaehlt["C"]["symbol"] == "BTCUSD.C", gewaehlt
    assert "K" not in gewaehlt, gewaehlt
    assert gewaehlt["A"]["boerse"] == "Binance"


def _multi_opener(reihen):
    """Opener, der fuer ohlcv-history mehrere Symbol-Reihen liefert."""
    def fake(req, timeout=0):
        if "spot-markets" in req.full_url:
            return _FakeResp(json.dumps(reihen["maerkte"]).encode())
        return _FakeResp(json.dumps(reihen["ohlcv"]).encode())
    return fake


def _punkte(n, mit_bv=True, start=1_700_000_000):
    vier_h = 4 * 3600
    p = [{"t": start + i * vier_h, "v": 10.0} for i in range(n)]
    if mit_bv:
        for e in p:
            e["bv"] = 6.0
    return p


def test_pruefe_symbole_erkennt_ob_ein_abruf_mehrere_reihen_bringt():
    """Daran haengt, ob Aggregieren einen Abruf kostet oder vier."""
    viele = {"maerkte": [], "ohlcv": [
        {"symbol": "BTCUSDT.A", "history": _punkte(61)},
        {"symbol": "BTCUSD.C", "history": _punkte(61)},
    ]}
    r = coinalyze._pruefe_symbole("KEY", ["BTCUSDT.A", "BTCUSD.C"],
                                  opener=_multi_opener(viele))
    assert r["angefragt"] == 2 and r["zurueck"] == 2, r
    assert r["mehrfachabruf_geht"] is True, r
    assert r["je_symbol"]["BTCUSDT.A"]["reichweite_tage"] == 10.0, r

    eine = {"maerkte": [], "ohlcv": [{"symbol": "BTCUSDT.A", "history": _punkte(61)}]}
    r2 = coinalyze._pruefe_symbole("KEY", ["BTCUSDT.A", "BTCUSD.C"],
                                   opener=_multi_opener(eine))
    assert r2["zurueck"] == 1 and r2["mehrfachabruf_geht"] is False, r2


def test_pruefe_symbole_verlangt_v_UND_bv():
    """Halbe Daten duerfen nicht als brauchbar gelten — ohne beide gibt es kein Delta."""
    nur_v = {"maerkte": [], "ohlcv": [
        {"symbol": "BTCUSDT.A", "history": _punkte(5, mit_bv=False)},
        {"symbol": "BTCUSD.C", "history": _punkte(5, mit_bv=True)},
    ]}
    r = coinalyze._pruefe_symbole("KEY", ["BTCUSDT.A", "BTCUSD.C"],
                                  opener=_multi_opener(nur_v))
    assert r["je_symbol"]["BTCUSDT.A"]["hat_v_und_bv"] is False, r
    assert r["je_symbol"]["BTCUSD.C"]["hat_v_und_bv"] is True, r


def test_spot_probe_urteil_nennt_fehlende_boersen_und_die_kuerzeste_historie():
    maerkte = [_markt("BTCUSDT.A", "A"), _markt("BTCUSD.C", "C", quote="USD")]
    daten = {"maerkte": maerkte, "ohlcv": [
        {"symbol": "BTCUSDT.A", "history": _punkte(61)},     # 10 Tage
        {"symbol": "BTCUSD.C", "history": _punkte(31)},      # 5 Tage
    ]}
    r = coinalyze.spot_probe("KEY", opener=_multi_opener(daten))
    u = r["_ergebnis"]
    assert u.startswith("JA fuer 2 von 4"), u
    # Bybit und OKX fehlen in den Maerkten -> muessen im Urteil stehen
    assert "Bybit" in u and "OKX" in u, u
    # Die kuerzeste Historie bestimmt das Fenster und muss genannt werden
    assert "5 bis 10 Tage" in u, u
    # Und es muss klarstellen, dass WIR aggregieren, nicht Coinalyze
    assert "von UNS" in u, u


def test_spot_probe_meldet_fehlenden_endpunkt_als_klares_nein():
    import urllib.error

    def fake(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {},
                                     io.BytesIO(b'{"message":"Not Found"}'))

    r = coinalyze.spot_probe("KEY", opener=fake)
    assert r["spot_markets"]["http_error"] == 404, r
    assert "NICHT geantwortet" in r["_ergebnis"], r["_ergebnis"]


def test_symbol_konstante_ist_binance_nicht_aggregiert():
    """Gegen den Irrtum, der seit E9.1 im Code stand: '.A' ist Binance.

    Wenn jemand die Konstante spaeter wieder auf ein vermeintliches Aggregat setzt,
    faellt dieser Test — und der Kommentar daneben erklaert, warum.
    """
    assert coinalyze.SYMBOL.endswith(".A")
    assert coinalyze.BOERSEN_CODES["A"] == "Binance"
    quelle = open(coinalyze.__file__, encoding="utf-8").read()
    kopf = quelle.split("INTERVAL =")[0]
    assert ".A\" ist NICHT \"aggregiert\"" in kopf or "NICHT" in kopf, \
        "Der Warnhinweis an SYMBOL fehlt — dann glaubt der naechste wieder an ein Aggregat."


def test_sample_deckelt_lange_listen_und_sagt_wie_viele_fehlen():
    """Sonst wachsen Metadaten-Antworten (5000+ Eintraege) zur 2-MB-Datei im Repo."""
    lang = [{"symbol": f"S{i}"} for i in range(500)]
    s = coinalyze._sample(lang)
    assert len(s) == coinalyze.SAMPLE_MAX_EINTRAEGE + 1, len(s)
    assert "_gekuerzt" in s[-1], s[-1]
    assert "460" in s[-1]["_gekuerzt"] and "500" in s[-1]["_gekuerzt"], s[-1]
    # Kurze Listen bleiben unveraendert — kein Hinweis-Eintrag, der nicht hingehoert
    kurz = [{"symbol": "X", "history": [1, 2, 3, 4, 5]}]
    assert coinalyze._sample(kurz) == [{"symbol": "X", "history": [3, 4, 5]}]
