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


# --------------------------------- E37.1: Auswahl nach Volumen (Kaisers Etappenvorgabe)
# Vorgeschichte, die diese Tests erklaert: Die erste Fassung hielt ".A" fuer
# "aggregiert" und waehlte BTCARS (argentinischer Peso) und WLDBTC (Worldcoin).
# Die zweite filterte richtig, nahm aber global USDT vor USD — und griff damit auf
# Coinbase einen Markt mit 2,2 BTC je 4h ab statt des Hauptmarkts. Ab E37.1
# entscheidet das gemessene Volumen. Beide Fehlgriffe stehen unten als Gegenproben.

def _markt(sym, ex, base="BTC", quote="USDT", buysell=True):
    return {"symbol": sym, "exchange": ex, "symbol_on_exchange": sym.split(".")[0],
            "base_asset": base, "quote_asset": quote, "has_buy_sell_data": buysell}


def test_ablehnungsgrund_nennt_den_grund_statt_nur_nein():
    """Ein stiller Filter, der eine ganze Boerse verschluckt, ist genau der Fehlertyp,
    den dieses Vorhaben vermeiden soll — deshalb muss der Grund lesbar sein."""
    codes = coinalyze.BOERSEN_CODES
    assert coinalyze._ablehnungsgrund(_markt("BTCUSDT.A", "A"), codes) is None
    # Worldcoin GEGEN Bitcoin: BTC im Namen, aber als Gegenwaehrung
    g = coinalyze._ablehnungsgrund(_markt("WLDBTC.A", "A", base="WLD", quote="BTC"), codes)
    assert g and "Basiswert" in g, g
    # Derselbe Fehler isoliert: Gegenwaehrung IST Dollar, nur die Basis stimmt nicht
    g = coinalyze._ablehnungsgrund(_markt("ETHUSDT.A", "A", base="ETH"), codes)
    assert g and "Basiswert" in g, g
    # Argentinischer Peso
    g = coinalyze._ablehnungsgrund(_markt("BTCARS.A", "A", quote="ARS"), codes)
    assert g and "Gegenwaehrung" in g, g
    # Falsche Boerse
    g = coinalyze._ablehnungsgrund(_markt("BTCUSDT.K", "K"), codes)
    assert g and "Boerse" in g, g
    # Ohne Kauf-/Verkaufsdaten
    g = coinalyze._ablehnungsgrund(_markt("BTCUSDT.C", "C", buysell=False), codes)
    assert g and "Kauf-/Verkaufsdaten" in g, g


def test_kandidaten_je_boerse_behaelt_ALLE_maerkte_nicht_nur_einen():
    """Ab E37.1 entscheidet das Volumen — dafuer muessen alle Kandidaten durchkommen."""
    maerkte = [_markt("BTCUSDT.C", "C", quote="USDT"),
               _markt("BTCUSD.C", "C", quote="USD"),
               _markt("BTCUSDT.A", "A"),
               _markt("BTCUSDT.K", "K")]           # Kraken -> raus
    k = coinalyze._kandidaten_je_boerse(maerkte)
    assert len(k["C"]) == 2, k                      # BEIDE Coinbase-Maerkte
    assert len(k["A"]) == 1 and "K" not in k, k


def test_abgelehnte_je_boerse_erklaert_warum_okx_leer_ausgeht():
    """Die OKX-Frage aus E37.1: leer, weil es nichts gibt — oder weil der Filter greift?"""
    maerkte = [_markt("BTC-USDT.3", "3", buysell=False),        # OKX ohne Kauf-/Verkaufsdaten
               _markt("BTC-EUR.3", "3", quote="EUR"),           # OKX, falsche Waehrung
               _markt("ETHUSDT.3", "3", base="ETH"),            # OKX, gar kein BTC
               _markt("BTCUSDT.A", "A")]                        # passt -> darf NICHT auftauchen
    ab = coinalyze._abgelehnte_je_boerse(maerkte)
    gruende = {z["symbol"]: z["grund"] for z in ab["3"]}
    assert "Kauf-/Verkaufsdaten" in gruende["BTC-USDT.3"], gruende
    assert "Gegenwaehrung" in gruende["BTC-EUR.3"], gruende
    assert "A" not in ab, ab                        # was passt, ist keine Ablehnung
    # ETHUSDT.3 hat weder BTC als Basis noch im Namen -> gehoert nicht in die Diagnose
    assert "ETHUSDT.3" not in gruende, gruende


def test_groesster_je_boerse_schlaegt_die_alte_usdt_rangfolge():
    """Der Coinbase-Fall in Zahlen: USDT winzig, USD gross. Volumen muss gewinnen."""
    kandidaten = {"C": [_markt("BTCUSDT.C", "C", quote="USDT"),
                        _markt("BTCUSD.C", "C", quote="USD")]}
    reihen = {
        "BTCUSDT.C": {"hat_v_und_bv": True, "summe_v": 2.2, "punkte": 2005},
        "BTCUSD.C":  {"hat_v_und_bv": True, "summe_v": 1800.0, "punkte": 2005},
    }
    g = coinalyze._groesster_je_boerse(kandidaten, reihen)
    assert g["C"]["symbol"] == "BTCUSD.C", g
    assert g["C"]["quote"] == "USD", g


def test_groesster_je_boerse_nimmt_keinen_markt_den_wir_nicht_lesen_koennen():
    """Ein Markt ohne 'v'/'bv' darf nicht gewinnen, nur weil seine Zahl groesser aussieht."""
    kandidaten = {"C": [_markt("BTCUSD.C", "C", quote="USD"),
                        _markt("BTCUSDT.C", "C", quote="USDT")]}
    reihen = {
        "BTCUSD.C":  {"hat_v_und_bv": False, "summe_v": 9_999_999.0},   # unlesbar
        "BTCUSDT.C": {"hat_v_und_bv": True, "summe_v": 2.2},
    }
    g = coinalyze._groesster_je_boerse(kandidaten, reihen)
    assert g["C"]["symbol"] == "BTCUSDT.C", g
    # Gar keine lesbare Reihe -> die Boerse faellt ganz weg, statt irgendetwas zu nehmen
    leer = coinalyze._groesster_je_boerse(
        kandidaten, {"BTCUSD.C": {"hat_v_und_bv": False}, "BTCUSDT.C": {"hat_v_und_bv": False}})
    assert leer == {}, leer


def test_reihe_auswerten_summiert_das_volumen_ueber_alle_punkte():
    e = {"symbol": "X", "history": [
        {"t": 1_700_000_000, "v": 10.0, "bv": 6.0, "c": 80000},
        {"t": 1_700_014_400, "v": 5.0, "bv": 2.0, "c": 80000},
        {"t": 1_700_028_800, "bv": 1.0, "c": 80000},        # ohne v -> zaehlt nicht mit
    ]}
    r = coinalyze._reihe_auswerten(e)
    assert r["summe_v"] == 15.0, r
    assert r["punkte"] == 3 and r["hat_v_und_bv"] is True, r


def test_einheit_einschaetzen_unterscheidet_btc_von_dollar():
    """Einheiten mischen ergibt eine Zahl, die normal aussieht und Unsinn ist."""
    assert "BTC" in coinalyze._einheit_einschaetzen(1257.5, 81420)
    assert "Dollar" in coinalyze._einheit_einschaetzen(102_000_000.0, 81420)
    assert "nicht einschaetzbar" in coinalyze._einheit_einschaetzen(None, 81420)


def _punkte(n, v=10.0, mit_bv=True, start=1_700_000_000):
    vier_h = 4 * 3600
    p = [{"t": start + i * vier_h, "v": v, "c": 80000.0} for i in range(n)]
    if mit_bv:
        for e in p:
            e["bv"] = v * 0.6
    return p


def _opener(maerkte, je_symbol, fehler_bei=None):
    """Opener fuer spot-markets + ohlcv; `fehler_bei` laesst einen Block scheitern."""
    def fake(req, timeout=0):
        if "spot-markets" in req.full_url:
            return _FakeResp(json.dumps(maerkte).encode())
        if fehler_bei and fehler_bei in req.full_url:
            import urllib.error
            raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {},
                                         io.BytesIO(b'{"message":"too many symbols"}'))
        gefragt = req.full_url.split("symbols=")[1].split("&")[0]
        raus = [{"symbol": s, "history": h} for s, h in je_symbol.items()
                if s.replace(".", "%2E") in gefragt or s in gefragt]
        return _FakeResp(json.dumps(raus).encode())
    return fake


def test_pruefe_symbole_teilt_in_bloecke_und_sammelt_alle_reihen():
    """Die Symbolgrenze von Coinalyze ist nicht dokumentiert — deshalb Bloecke."""
    symbole = [f"BTC{i}.A" for i in range(10)]          # 10 > SYMBOLE_JE_ABRUF (6)
    je = {s: _punkte(3) for s in symbole}
    r = coinalyze._pruefe_symbole("KEY", symbole, opener=_opener([], je))
    assert r["angefragt"] == 10 and r["zurueck"] == 10, r
    assert len(r["bloecke"]) == 2, r["bloecke"]         # 6 + 4
    assert r["mehrfachabruf_geht"] is True, r


def test_pruefe_symbole_ein_kaputter_block_reisst_den_rest_nicht_mit():
    """Ein sichtbarer Ausfall ist besser als ein stiller Totalverlust.

    Seit dem 429-Befund (20.09.2026) wird nach einem gescheiterten Block ZUSAETZLICH
    einzeln nachgefragt: Ein einzelnes Symbol kostet weniger Kontingent und kommt oft
    durch, wo vier zusammen scheitern. Vorher fiel der ganze Block ersatzlos aus.
    """
    symbole = [f"BTC{i}.A" for i in range(10)]
    je = {s: _punkte(3) for s in symbole}
    # Der Sammelabruf des zweiten Blocks enthaelt BTC9.A -> gezielt scheitern lassen.
    # Die Einzelabrufe danach fragen je ein Symbol und kommen durch (ausser BTC9.A).
    r = coinalyze._pruefe_symbole("KEY", symbole,
                                  opener=_opener([], je, fehler_bei="BTC9"))
    assert any("http_error" in b for b in r["bloecke"]), r["bloecke"]
    # Erster Block (6) + Einzelabrufe des zweiten, die durchkamen (3 von 4)
    assert r["zurueck"] == 9, r
    assert "BTC9.A" not in r["je_symbol"], r["je_symbol"].keys()
    assert any(b.get("einzeln") for b in r["bloecke"]), r["bloecke"]


def test_spot_probe_waehlt_nach_volumen_und_nennt_fehlende_boersen():
    maerkte = [_markt("BTCUSDT.A", "A"),
               _markt("BTCUSDT.C", "C", quote="USDT"),
               _markt("BTCUSD.C", "C", quote="USD"),
               _markt("BTC-USDT.3", "3", buysell=False)]      # OKX faellt raus
    je = {
        "BTCUSDT.A":  _punkte(61, v=1257.5),                  # gewaehlt, 10 Tage
        # Winziger Markt MIT LANGER Historie (100 Tage). Genau so trennt sich, ob das
        # Urteil die Reichweite der GEWAEHLTEN Maerkte nennt oder die aller Symbole:
        # ohne diese Trennung faellt ein Fehler hier nicht auf.
        "BTCUSDT.C":  _punkte(601, v=2.2),
        "BTCUSD.C":   _punkte(31, v=900.0),                   # gewaehlt, 5 Tage
    }
    r = coinalyze.spot_probe("KEY", opener=_opener(maerkte, je))
    g = r["gewaehlt_je_boerse"]
    assert g["C"]["symbol"] == "BTCUSD.C", g              # Volumen schlaegt USDT-Vorrang
    assert g["A"]["symbol"] == "BTCUSDT.A", g
    u = r["_ergebnis"]
    assert u.startswith("JA fuer 2 von 4"), u
    assert "OKX" in u and "Bybit" in u, u                 # beide fehlen
    # Kuerzeste Historie der GEWAEHLTEN Maerkte (5 Tage), nicht die der verworfenen
    assert "5 bis 10 Tage" in u, u
    # Der Anteil muss sichtbar sein, damit der alte Fehlgriff belegt ist und nicht
    # nur behauptet: der gewaehlte Markt dominiert, der alte war Beiwerk.
    anteile = {z["symbol"]: z["anteil_prozent"]
               for z in r["volumenvergleich_je_boerse"]["Coinbase"]}
    assert anteile["BTCUSD.C"] > 90.0, anteile
    assert anteile["BTCUSDT.C"] < 10.0, anteile


def test_spot_probe_meldet_fehlenden_endpunkt_als_klares_nein():
    import urllib.error

    def fake(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {},
                                     io.BytesIO(b'{"message":"Not Found"}'))

    r = coinalyze.spot_probe("KEY", opener=fake)
    assert r["spot_markets"]["http_error"] == 404, r
    assert "NICHT geantwortet" in r["_ergebnis"], r["_ergebnis"]


def test_symbol_konstante_ist_binance_nicht_aggregiert():
    """Gegen den Irrtum, der seit E9.1 im Code stand: '.A' ist Binance."""
    assert coinalyze.SYMBOL.endswith(".A")
    assert coinalyze.BOERSEN_CODES["A"] == "Binance"
    kopf = open(coinalyze.__file__, encoding="utf-8").read().split("INTERVAL =")[0]
    assert "NICHT" in kopf, \
        "Der Warnhinweis an SYMBOL fehlt — dann glaubt der naechste wieder an ein Aggregat."


def test_sample_deckelt_lange_listen_und_sagt_wie_viele_fehlen():
    """Sonst wachsen Metadaten-Antworten (5000+ Eintraege) zur 2-MB-Datei im Repo."""
    lang = [{"symbol": f"S{i}"} for i in range(500)]
    s = coinalyze._sample(lang)
    assert len(s) == coinalyze.SAMPLE_MAX_EINTRAEGE + 1, len(s)
    assert "460" in s[-1]["_gekuerzt"] and "500" in s[-1]["_gekuerzt"], s[-1]
    kurz = [{"symbol": "X", "history": [1, 2, 3, 4, 5]}]
    assert coinalyze._sample(kurz) == [{"symbol": "X", "history": [3, 4, 5]}]


# ----------------------------------- E37.2: aggregiertes Spot-CVD ueber die Boersen

def _ohlcv_opener(je_symbol, maerkte=None):
    """Opener, der spot-markets und ohlcv-history bedient."""
    def fake(req, timeout=0):
        if "spot-markets" in req.full_url:
            return _FakeResp(json.dumps(maerkte or []).encode())
        gefragt = req.full_url.split("symbols=")[1].split("&")[0]
        raus = [{"symbol": s, "history": h} for s, h in je_symbol.items()
                if s.replace(".", "%2E") in gefragt or s in gefragt]
        return _FakeResp(json.dumps(raus).encode())
    return fake


def _pkt(ts, v, bv, c=80000.0):
    return {"t": ts, "v": v, "bv": bv, "c": c}


def test_spot_delta_summiert_ueber_die_boersen():
    """Delta = 2*bv - v je Markt, dann Summe. Dieselbe Formel wie beim Futures-CVD."""
    je = {
        "A.1": [_pkt(1000, 10.0, 7.0)],     # 2*7 - 10 = +4
        "B.2": [_pkt(1000, 20.0, 5.0)],     # 2*5 - 20 = -10
    }
    summe, b = coinalyze.spot_delta_aggregiert("KEY", ["A.1", "B.2"],
                                               opener=_ohlcv_opener(je))
    assert summe == {1000 * 1000: -6.0}, summe
    assert b["punkte_vollstaendig"] == 1 and b["punkte_ausgelassen"] == 0, b


def test_spot_delta_laesst_unvollstaendige_zeitpunkte_aus_und_zaehlt_sie():
    """DIE Kernregel: eine Teilsumme saehe aus wie ein Einbruch des Spot-Flows.

    Zeitpunkt 2000 fehlt bei B — er darf NICHT als 'nur A' in die Reihe wandern.
    """
    je = {
        "A.1": [_pkt(1000, 10.0, 7.0), _pkt(2000, 10.0, 9.0), _pkt(3000, 10.0, 7.0)],
        "B.2": [_pkt(1000, 20.0, 5.0),                        _pkt(3000, 20.0, 5.0)],
    }
    summe, b = coinalyze.spot_delta_aggregiert("KEY", ["A.1", "B.2"],
                                               opener=_ohlcv_opener(je))
    assert set(summe) == {1000 * 1000, 3000 * 1000}, summe
    assert 2000 * 1000 not in summe, "unvollstaendiger Zeitpunkt darf nicht mitzaehlen"
    assert b["punkte_gesamt"] == 3 and b["punkte_vollstaendig"] == 2, b
    assert b["punkte_ausgelassen"] == 1, b


def test_spot_delta_meldet_symbole_ohne_antwort():
    """Ein Markt, der gar nicht antwortet, darf nicht stillschweigend fehlen."""
    je = {"A.1": [_pkt(1000, 10.0, 7.0)]}
    summe, b = coinalyze.spot_delta_aggregiert("KEY", ["A.1", "FEHLT.9"],
                                               opener=_ohlcv_opener(je))
    assert b["ohne_antwort"] == ["FEHLT.9"], b
    assert b["symbole"] == ["A.1"], b
    assert summe == {1000 * 1000: 4.0}, summe       # laeuft weiter mit dem, was da ist


def test_spot_delta_ueberspringt_punkte_ohne_v_oder_bv():
    je = {"A.1": [{"t": 1000, "v": 10.0},            # bv fehlt
                  {"t": 2000, "bv": 5.0},            # v fehlt
                  _pkt(3000, 10.0, 7.0)]}
    summe, _ = coinalyze.spot_delta_aggregiert("KEY", ["A.1"], opener=_ohlcv_opener(je))
    assert summe == {3000 * 1000: 4.0}, summe


def test_spot_symbole_groesster_gegen_alle_dollar():
    """Die beiden Wahlmoeglichkeiten muessen wirklich verschiedene Mengen liefern."""
    maerkte = [_markt("BTCUSDT.A", "A", quote="USDT"),
               _markt("BTCFDUSD.A", "A", quote="FDUSD"),
               _markt("BTCUSD.C", "C", quote="USD")]
    je = {
        "BTCUSDT.A":  [_pkt(1000, 100.0, 60.0)],     # groesser
        "BTCFDUSD.A": [_pkt(1000, 30.0, 20.0)],
        "BTCUSD.C":   [_pkt(1000, 50.0, 30.0)],
    }
    op = _ohlcv_opener(je, maerkte)
    g = coinalyze.spot_symbole("KEY", wahl=coinalyze.SPOT_WAHL_GROESSTER, opener=op)
    assert g == {"A": ["BTCUSDT.A"], "C": ["BTCUSD.C"]}, g
    a = coinalyze.spot_symbole("KEY", wahl=coinalyze.SPOT_WAHL_ALLE, opener=op)
    assert sorted(a["A"]) == ["BTCFDUSD.A", "BTCUSDT.A"], a
    assert a["C"] == ["BTCUSD.C"], a


def test_spot_symbole_nimmt_bei_alle_dollar_nur_lesbare_reihen():
    """Ein Markt ohne 'bv' liefert kein Delta — er darf die Summe nicht verwaessern."""
    maerkte = [_markt("BTCUSDT.A", "A", quote="USDT"),
               _markt("BTCFDUSD.A", "A", quote="FDUSD")]
    je = {
        "BTCUSDT.A":  [_pkt(1000, 100.0, 60.0)],
        "BTCFDUSD.A": [{"t": 1000, "v": 30.0, "c": 80000.0}],     # kein bv
    }
    a = coinalyze.spot_symbole("KEY", wahl=coinalyze.SPOT_WAHL_ALLE,
                               opener=_ohlcv_opener(je, maerkte))
    assert a["A"] == ["BTCUSDT.A"], a


def test_spot_auswahl_holt_die_marktliste_nur_EINMAL():
    """Zwei getrennte Durchgaenge koennten unterschiedlich ausfallen — und kosten doppelt."""
    maerkte = [_markt("BTCUSDT.A", "A", quote="USDT"),
               _markt("BTCFDUSD.A", "A", quote="FDUSD")]
    je = {"BTCUSDT.A": [_pkt(1000, 100.0, 60.0)],
          "BTCFDUSD.A": [_pkt(1000, 30.0, 20.0)]}
    zaehler = {"markt": 0}
    inner = _ohlcv_opener(je, maerkte)

    def zaehlend(req, timeout=0):
        if "spot-markets" in req.full_url:
            zaehler["markt"] += 1
        return inner(req, timeout)

    a = coinalyze.spot_auswahl("KEY", opener=zaehlend)
    assert zaehler["markt"] == 1, zaehler
    assert a[coinalyze.SPOT_WAHL_GROESSTER] == {"A": ["BTCUSDT.A"]}, a
    assert sorted(a[coinalyze.SPOT_WAHL_ALLE]["A"]) == ["BTCFDUSD.A", "BTCUSDT.A"], a


# ------------- E37.3: Open Interest, Liquidationen, Futures-CVD ueber mehrere Boersen

def _perp(sym, ex, quote="USDT", perp=True, ohlcv=True, denom="BASE_ASSET"):
    return {"symbol": sym, "exchange": ex, "symbol_on_exchange": sym.split("_")[0],
            "base_asset": "BTC", "quote_asset": quote, "is_perpetual": perp,
            "has_ohlcv_data": ohlcv, "oi_lq_vol_denominated_in": denom}


def test_perp_ablehnungsgrund_nennt_den_grund():
    c = coinalyze.PERP_BOERSEN
    assert coinalyze._perp_ablehnungsgrund(_perp("BTCUSDT_PERP.A", "A"), c) is None
    g = coinalyze._perp_ablehnungsgrund(_perp("BTCUSDT_1231.A", "A", perp=False), c)
    assert g and "Perpetual" in g, g
    g = coinalyze._perp_ablehnungsgrund(_perp("BTCEUR_PERP.A", "A", quote="EUR"), c)
    assert g and "Gegenwaehrung" in g, g
    g = coinalyze._perp_ablehnungsgrund(_perp("BTCUSDT_PERP.K", "K"), c)
    assert g and "Boerse" in g, g
    g = coinalyze._perp_ablehnungsgrund(_perp("BTCUSDT_PERP.A", "A", ohlcv=False), c)
    assert g and "OHLCV" in g, g
    e = _perp("ETHUSDT_PERP.A", "A"); e["base_asset"] = "ETH"
    g = coinalyze._perp_ablehnungsgrund(e, c)
    assert g and "Basiswert" in g, g


def test_nach_denominierung_trennt_einheiten_und_das_volumen_entscheidet():
    """DIE Falle dieser Etappe: BTC-Mengen und USD-Kontrakte zusammenzuzaehlen ergibt
    eine voellig normal aussehende Zahl, die Unsinn ist.

    Zwei Zwergboersen duerfen Binance nicht ueberstimmen — deshalb gewinnt die Gruppe
    mit dem meisten Volumen, nicht die mit den meisten Maerkten.
    """
    gewaehlt = {
        "A": {"symbol": "BTCUSDT_PERP.A", "boerse": "Binance",
              "denominierung": "BASE_ASSET", "summe_v": 1_000_000.0},
        "3": {"symbol": "BTCUSD_PERP.3", "boerse": "OKX",
              "denominierung": "QUOTE_ASSET", "summe_v": 5.0},
        "6": {"symbol": "BTCUSD_PERP.6", "boerse": "Bybit",
              "denominierung": "QUOTE_ASSET", "summe_v": 4.0},
    }
    drin, raus = coinalyze._nach_denominierung(gewaehlt)
    assert drin == ["BTCUSDT_PERP.A"], drin          # Volumen schlaegt Mehrheit (2:1)
    assert {r["symbol"] for r in raus} == {"BTCUSD_PERP.3", "BTCUSD_PERP.6"}, raus
    assert all("mischen" in r["grund"] for r in raus), raus


def test_nach_denominierung_laesst_alle_drin_wenn_die_einheit_gleich_ist():
    gewaehlt = {c: {"symbol": f"S.{c}", "boerse": c, "denominierung": "BASE_ASSET",
                    "summe_v": 10.0} for c in ("A", "6", "3")}
    drin, raus = coinalyze._nach_denominierung(gewaehlt)
    assert sorted(drin) == ["S.3", "S.6", "S.A"], drin
    assert raus == [], raus


def _hist_opener(je_symbol, maerkte=None, endpoint=None):
    """Opener fuer future-markets + History-Endpunkte.

    `endpoint` gesetzt = NUR dieser Endpunkt liefert Daten, jeder andere eine leere
    Antwort. Ohne diese Schaerfe faellt nicht auf, wenn eine Funktion den falschen
    Endpunkt abfragt — sie bekaeme trotzdem plausible Zahlen.
    """
    def fake(req, timeout=0):
        if "future-markets" in req.full_url:
            return _FakeResp(json.dumps(maerkte or []).encode())
        if endpoint and endpoint not in req.full_url:
            return _FakeResp(json.dumps([]).encode())
        gefragt = req.full_url.split("symbols=")[1].split("&")[0]
        raus = [{"symbol": s, "history": h} for s, h in je_symbol.items()
                if s.replace(".", "%2E") in gefragt or s in gefragt]
        return _FakeResp(json.dumps(raus).encode())
    return fake


def test_oi_aggregiert_summiert_und_laesst_luecken_aus():
    """Beim Open Interest ist die Luecken-Regel besonders wichtig: eine Teilsumme
    saehe aus wie ein OI-Wipeout — also genau das Signal fuer Muster 4."""
    # 'o' bewusst weit weg von 'c': sonst faellt nicht auf, wenn jemand den
    # Eroeffnungs- statt den Schlusswert nimmt.
    je = {
        "A.1": [{"t": 1000, "o": 1.0, "c": 60.0}, {"t": 2000, "o": 2.0, "c": 61.0},
                {"t": 3000, "o": 3.0, "c": 62.0}],
        "B.2": [{"t": 1000, "o": 4.0, "c": 30.0},
                {"t": 3000, "o": 5.0, "c": 31.0}],
    }
    summe, b = coinalyze.oi_aggregiert(
        "KEY", ["A.1", "B.2"],
        opener=_hist_opener(je, endpoint="open-interest-history"))
    assert summe == {1000 * 1000: 90.0, 3000 * 1000: 93.0}, summe
    assert 2000 * 1000 not in summe, "unvollstaendiger Zeitpunkt waere ein Schein-Wipeout"
    assert b["punkte_ausgelassen"] == 1, b
    assert "USD" in b["einheit"], b


def test_liq_aggregiert_haelt_long_und_short_auf_denselben_zeitpunkten():
    """Liefen die beiden Reihen auseinander, stuende an einem Zeitpunkt eine volle
    Long-Summe neben einer halben Short-Summe — und die Kaskaden-Erkennung kippt."""
    je = {
        "A.1": [{"t": 1000, "l": 5.0, "s": 2.0}, {"t": 2000, "l": 7.0, "s": 1.0}],
        "B.2": [{"t": 1000, "l": 3.0, "s": 4.0}],
    }
    summe, b = coinalyze.liq_aggregiert(
        "KEY", ["A.1", "B.2"],
        opener=_hist_opener(je, endpoint="liquidation-history"))
    assert summe == {1000 * 1000: (8.0, 6.0)}, summe
    assert 2000 * 1000 not in summe, summe
    assert b["punkte_ausgelassen"] == 1, b


def test_fut_delta_aggregiert_rechnet_wie_das_spot_delta():
    je = {"A.1": [_pkt(1000, 10.0, 7.0)],       # +4
          "B.2": [_pkt(1000, 20.0, 5.0)]}       # -10
    summe, b = coinalyze.fut_delta_aggregiert("KEY", ["A.1", "B.2"],
                                              opener=_hist_opener(je))
    assert summe == {1000 * 1000: -6.0}, summe
    assert "Denominierung" in b["einheit"], b


def test_perp_auswahl_waehlt_nach_volumen_und_gibt_die_denominierung_mit():
    # Der groesste Markt steht bewusst NICHT an erster Stelle — sonst wuerde
    # "nimm den ersten" dasselbe Ergebnis liefern wie "nimm den groessten".
    maerkte = [_perp("BTCUSDC_PERP.A", "A", quote="USDC"),
               _perp("BTCUSDT_PERP.A", "A", quote="USDT"),
               _perp("BTCUSD_PERP.3", "3", quote="USD", denom="QUOTE_ASSET"),
               _perp("BTCUSDT_1231.A", "A", perp=False)]          # Termin -> raus
    je = {"BTCUSDT_PERP.A": _punkte(3, v=100.0),
          "BTCUSDC_PERP.A": _punkte(3, v=5.0),
          "BTCUSD_PERP.3":  _punkte(3, v=50.0)}
    pa = coinalyze.perp_auswahl("KEY", opener=_hist_opener(je, maerkte))
    g = pa["gewaehlt"]
    assert g["A"]["symbol"] == "BTCUSDT_PERP.A", g               # Volumen entscheidet
    assert g["A"]["denominierung"] == "BASE_ASSET", g
    assert g["3"]["denominierung"] == "QUOTE_ASSET", g
    gruende = {z["symbol"]: z["grund"] for z in pa["abgelehnt"].get("A", [])}
    assert "Perpetual" in gruende["BTCUSDT_1231.A"], gruende


def test_summiere_vollstaendig_ist_die_EINE_regel_fuer_alle_vier_werte():
    """Waere sie viermal geschrieben, koennte sie dreimal richtig und einmal falsch sein.

    Deshalb hier direkt: unvollstaendige Zeitpunkte raus, gezaehlt, Rest summiert.
    """
    je = {"X": {1: 1.0, 2: 2.0, 3: 3.0}, "Y": {1: 10.0, 3: 30.0}}
    summe, b = coinalyze._summiere_vollstaendig(je, ["X", "Y"], [], "Testeinheit")
    assert summe == {1: 11.0, 3: 33.0}, summe
    assert b["punkte_gesamt"] == 3 and b["punkte_ausgelassen"] == 1, b
    assert b["einheit"] == "Testeinheit", b
    # Gar keine Reihe -> klare Fehlermeldung statt leerer Erfolg
    leer, b2 = coinalyze._summiere_vollstaendig({}, ["X"], [], "Testeinheit")
    assert leer == {} and "fehler" in b2, b2


def test_perp_auswahl_liefert_die_einheiten_trennung_gleich_mit():
    """Wer die Maerkte waehlt, muss auch sagen, welche summiert werden duerfen —
    sonst muss jeder Aufrufer die Regel selbst kennen und einer macht es falsch."""
    maerkte = [_perp("BTCUSDT_PERP.A", "A", quote="USDT", denom="BASE_ASSET"),
               _perp("BTCUSD_PERP.3", "3", quote="USD", denom="QUOTE_ASSET")]
    je = {"BTCUSDT_PERP.A": _punkte(3, v=1000.0),
          "BTCUSD_PERP.3":  _punkte(3, v=5.0)}
    pa = coinalyze.perp_auswahl("KEY", opener=_hist_opener(je, maerkte))
    assert sorted(pa["alle_symbole"]) == ["BTCUSDT_PERP.A", "BTCUSD_PERP.3"], pa
    # Fuers Futures-CVD nur die Mehrheits-Denominierung (nach Volumen: Binance)
    assert pa["cvd_symbole"] == ["BTCUSDT_PERP.A"], pa
    assert [a["symbol"] for a in pa["cvd_ausgeschlossen"]] == ["BTCUSD_PERP.3"], pa
    # OI und Liquidationen dagegen duerfen ALLE — die stehen in alle_symbole
    assert len(pa["alle_symbole"]) > len(pa["cvd_symbole"]), pa


def test_auswahl_misst_nur_30_tage_die_datenabfrage_aber_das_volle_fenster():
    """Fuer die RANGFOLGE genuegen 30 Tage; ein Jahr mal zehn Symbole ist zehnmal so
    viel Last auf einer API mit 40 Abrufen je Minute. Ohne diesen Test faellt es nicht
    auf, wenn der Parameter zwar da ist, aber nirgends ankommt."""
    spannen = []

    def messend(req, timeout=0):
        if "spot-markets" in req.full_url:
            return _FakeResp(json.dumps(
                [_markt("BTCUSDT.A", "A"), _markt("BTCUSD.C", "C", quote="USD")]).encode())
        teile = dict(p.split("=") for p in req.full_url.split("?")[1].split("&"))
        spannen.append((int(teile["to"]) - int(teile["from"])) / 86400.0)
        gefragt = teile["symbols"]
        return _FakeResp(json.dumps(
            [{"symbol": s, "history": _punkte(3)} for s in ("BTCUSDT.A", "BTCUSD.C")
             if s.replace(".", "%2E") in gefragt or s in gefragt]).encode())

    coinalyze.spot_auswahl("KEY", opener=messend)
    assert spannen, "es wurde gar keine History abgefragt"
    assert all(abs(t - coinalyze.AUSWAHL_TAGE) < 1 for t in spannen), spannen

    spannen.clear()
    coinalyze.spot_delta_aggregiert("KEY", ["BTCUSDT.A"], opener=messend)
    assert all(abs(t - coinalyze.SPOT_REICHWEITE_TAGE) < 1 for t in spannen), spannen


# ---- E37.3, Nachbesserung 20.09.2026: Rueckfall auf Einzelabruf + echte Taktung

def test_hole_reihen_faellt_auf_einzelabruf_zurueck():
    """Dass EIN Abruf mehrere Reihen liefert, war nur fuer ohlcv-history belegt.

    Beim Open Interest kam am 20.09.2026 nichts zurueck und der ganze Vergleich fiel
    aus. Statt das hinzunehmen: fehlende Symbole einzeln nachfragen.
    """
    gefragt = []

    def fake(req, timeout=0):
        syms = req.full_url.split("symbols=")[1].split("&")[0]
        gefragt.append(syms)
        if "," in syms or "%2C" in syms:        # Mehrfachabruf -> leer
            return _FakeResp(json.dumps([]).encode())
        name = syms.replace("%2E", ".")
        return _FakeResp(json.dumps(
            [{"symbol": name, "history": [{"t": 1000, "c": 5.0}]}]).encode())

    summe, b = coinalyze.oi_aggregiert("KEY", ["A.1", "B.2"], opener=fake, pause=0)
    assert summe == {1000 * 1000: 10.0}, summe        # beide Reihen kamen einzeln an
    assert len(gefragt) == 3, gefragt                 # 1 Mehrfach- + 2 Einzelabrufe
    assert any(z.get("einzeln") for z in b["bloecke"]), b["bloecke"]


def test_hole_reihen_fragt_nicht_einzeln_nach_wenn_alles_kam():
    """Der Rueckfall darf nicht bei jedem Abruf mitlaufen — das waere doppelte Last."""
    gefragt = []

    def fake(req, timeout=0):
        syms = req.full_url.split("symbols=")[1].split("&")[0]
        gefragt.append(syms)
        return _FakeResp(json.dumps(
            [{"symbol": s, "history": [{"t": 1000, "c": 5.0}]}
             for s in ("A.1", "B.2")]).encode())

    coinalyze.oi_aggregiert("KEY", ["A.1", "B.2"], opener=fake, pause=0)
    assert len(gefragt) == 1, gefragt


def test_taktung_haengt_nicht_mehr_daran_ob_kw_leer_ist():
    """DER Fehler vom 20.09.2026: Die Pause hing an `not kw`. Gedacht war 'im Test
    nicht warten' — im echten Lauf sind aber frm/to gesetzt, also war kw NICHT leer
    und es wurde NIE gewartet. Genau dort, wo das Rate-Limit greift.
    """
    import inspect
    quelle = inspect.getsource(coinalyze._hole_reihen_roh)
    assert "not kw" not in quelle, \
        "Die Taktung haengt wieder an kw — im echten Lauf schaltet das die Pause ab."
    assert "PAUSE_JE_BLOCK" in quelle, quelle
    # Und ohne injizierten Opener (= echter Lauf) muss eine Pause herauskommen
    assert coinalyze.PAUSE_JE_BLOCK > 0


def test_rueckfall_greift_auch_wenn_die_ANZAHL_stimmt_aber_ein_symbol_fehlt():
    """Randfall, der die erste Fassung ausgehebelt haette: Die Antwort enthaelt zwei
    Reihen — aber eine davon ist ein Symbol, das gar nicht gefragt war. Die Anzahl
    stimmt, das gesuchte Symbol fehlt trotzdem."""
    gefragt = []

    def fake(req, timeout=0):
        syms = req.full_url.split("symbols=")[1].split("&")[0]
        gefragt.append(syms)
        if "," in syms or "%2C" in syms:
            return _FakeResp(json.dumps([                 # zwei Reihen, aber B.2 fehlt
                {"symbol": "A.1", "history": [{"t": 1000, "c": 5.0}]},
                {"symbol": "FREMD.9", "history": [{"t": 1000, "c": 99.0}]}]).encode())
        name = syms.replace("%2E", ".")
        return _FakeResp(json.dumps(
            [{"symbol": name, "history": [{"t": 1000, "c": 7.0}]}]).encode())

    summe, b = coinalyze.oi_aggregiert("KEY", ["A.1", "B.2"], opener=fake, pause=0)
    assert any(z.get("einzeln") == "B.2" for z in b["bloecke"]), b["bloecke"]
    assert summe == {1000 * 1000: 12.0}, summe        # 5.0 (A.1) + 7.0 (B.2 einzeln)


# ---- E37.3, dritter Befund: HTTP 429. Der Lauf vom 20.09.2026, 10:52 UTC meldete
# `Too Many Requests. See the "Retry-After" header.` — und bis dahin haben wir genau
# diesen Hinweis ignoriert und den ganzen Vergleich fallengelassen.

def _http429(retry_after=None):
    import urllib.error
    kopf = {"Retry-After": retry_after} if retry_after else {}
    return urllib.error.HTTPError("http://x", 429, "Too Many Requests", kopf,
                                  io.BytesIO(b'{"message":"Too Many Requests."}'))


def test_wiederholt_bei_429_und_haelt_sich_an_retry_after():
    gewartet, versuche = [], {"n": 0}
    orig_sleep = coinalyze.time.sleep
    coinalyze.time.sleep = gewartet.append
    try:
        def hole():
            versuche["n"] += 1
            if versuche["n"] < 3:
                raise _http429("7")
            return "da"
        assert coinalyze._mit_wiederholung(hole, "test") == "da"
    finally:
        coinalyze.time.sleep = orig_sleep
    assert versuche["n"] == 3, versuche
    assert gewartet == [7.0, 7.0], gewartet          # genau so lange wie verlangt


def test_ohne_retry_after_wird_die_wartezeit_verdoppelt():
    gewartet = []
    orig_sleep = coinalyze.time.sleep
    coinalyze.time.sleep = gewartet.append
    try:
        n = {"i": 0}

        def hole():
            n["i"] += 1
            if n["i"] < 4:
                raise _http429()                      # kein Header
            return "da"
        coinalyze._mit_wiederholung(hole, "test")
    finally:
        coinalyze.time.sleep = orig_sleep
    assert gewartet == [1.6, 3.2, 6.4], gewartet


def test_wartezeit_wird_gedeckelt_und_andere_fehler_fliegen_sofort():
    """Ein Server, der 'in einer Stunde' sagt, darf den Lauf nicht anhalten.
    Und ein 404 ist kein Ueberlast-Problem — da hilft Warten nichts."""
    gewartet = []
    orig_sleep = coinalyze.time.sleep
    coinalyze.time.sleep = gewartet.append
    try:
        n = {"i": 0}

        def hole():
            n["i"] += 1
            if n["i"] < 2:
                raise _http429("3600")
            return "da"
        coinalyze._mit_wiederholung(hole, "test")
        assert gewartet == [coinalyze.MAX_WARTE], gewartet

        import urllib.error

        def vierhundertvier():
            raise urllib.error.HTTPError("http://x", 404, "Not Found", {},
                                         io.BytesIO(b"{}"))
        try:
            coinalyze._mit_wiederholung(vierhundertvier, "test")
            raise AssertionError("404 haette sofort durchschlagen muessen")
        except urllib.error.HTTPError as e:
            assert e.code == 404
        assert gewartet == [coinalyze.MAX_WARTE], "bei 404 darf nicht gewartet werden"
    finally:
        coinalyze.time.sleep = orig_sleep


def test_gibt_nach_MAX_VERSUCHEN_auf_statt_ewig_zu_warten():
    orig_sleep = coinalyze.time.sleep
    coinalyze.time.sleep = lambda *_: None
    try:
        n = {"i": 0}

        def immer429():
            n["i"] += 1
            raise _http429("1")
        try:
            coinalyze._mit_wiederholung(immer429, "test")
            raise AssertionError("haette aufgeben muessen")
        except Exception as e:
            assert getattr(e, "code", None) == 429, e
    finally:
        coinalyze.time.sleep = orig_sleep
    assert n["i"] == coinalyze.MAX_VERSUCHE, n


def test_der_echte_abruf_benutzt_die_wiederholung_auch_wirklich():
    """Die Wiederholung kann fehlerfrei gebaut und trotzdem nirgends verdrahtet sein.

    Genau das war der Fall beim Auswahl-Fenster: Parameter da, kam nie an. Hier also
    nicht die Funktion testen, sondern den WEG durch _hole_reihen_roh.
    """
    versuche = {"n": 0}
    orig_sleep = coinalyze.time.sleep
    coinalyze.time.sleep = lambda *_: None
    try:
        def fake(req, timeout=0):
            versuche["n"] += 1
            if versuche["n"] == 1:
                raise _http429("1")                   # erster Abruf: ueberlastet
            return _FakeResp(json.dumps(
                [{"symbol": "A.1", "history": [{"t": 1000, "c": 5.0}]}]).encode())

        summe, b = coinalyze.oi_aggregiert("KEY", ["A.1"], opener=fake, pause=0)
    finally:
        coinalyze.time.sleep = orig_sleep
    assert versuche["n"] == 2, versuche               # einmal gescheitert, einmal geklappt
    assert summe == {1000 * 1000: 5.0}, summe
    assert not any("http_error" in z for z in b["bloecke"]), b["bloecke"]


# ------------------- E37.4: gewichtete Mittel (Funding, Long-Short)
# Anders als die Summen. Eine Funding-Rate ist ein Preis, keine Menge — zwei Boersen
# mit 0,01 % und 0,03 % haben zusammen nicht 0,04 %.

def test_gewichtetes_mittel_ist_KEIN_einfacher_durchschnitt():
    """DIE Falle dieser Etappe: Ein einfacher Durchschnitt gibt einer Zwergboerse
    dasselbe Gewicht wie Binance — und die Zahl sieht dabei voellig normal aus.

    Hier haelt 'GROSS' 90 % des Open Interest. Einfacher Durchschnitt ergaebe 0,055,
    richtig gewichtet 0,019. Faktor drei Unterschied, beide Zahlen plausibel.
    """
    werte = {"GROSS": {1: 0.01}, "ZWERG": {1: 0.10}}
    gewichte = {"GROSS": {1: 900.0}, "ZWERG": {1: 100.0}}
    m, b = coinalyze.gewichtetes_mittel(werte, gewichte, ["GROSS", "ZWERG"], [], "x")
    assert abs(m[1] - 0.019) < 1e-9, m               # (0.01*900 + 0.10*100)/1000
    assert abs(m[1] - 0.055) > 0.03, "das waere der einfache Durchschnitt"
    assert "Open Interest" in b["gewichtung"], b


def test_gewichte_werden_normiert():
    """Ohne Normierung kaeme statt eines Mittels eine mit dem Open Interest skalierte
    Zahl heraus, die je nach Marktphase um Groessenordnungen schwankt."""
    werte = {"A": {1: 0.02, 2: 0.02}}
    # Zeitpunkt 2 hat das ZEHNFACHE Open Interest — das Mittel muss gleich bleiben
    gewichte = {"A": {1: 100.0, 2: 1000.0}}
    m, _ = coinalyze.gewichtetes_mittel(werte, gewichte, ["A"], [], "x")
    assert m[1] == m[2] == 0.02, m


def test_gewichtetes_mittel_laesst_zeitpunkte_ohne_gewicht_aus():
    """Ein Markt ohne Open Interest darf nicht mit Gewicht 0 mitlaufen — rechnerisch
    waere das dasselbe wie Weglassen, aber niemand saehe es."""
    werte = {"A": {1: 0.01, 2: 0.02, 3: 0.03}, "B": {1: 0.05, 2: 0.06, 3: 0.07}}
    gewichte = {"A": {1: 10.0, 2: 10.0, 3: 10.0}, "B": {1: 10.0, 3: 10.0}}  # 2 fehlt
    m, b = coinalyze.gewichtetes_mittel(werte, gewichte, ["A", "B"], [], "x")
    assert sorted(m) == [1, 3], m
    assert b["punkte_ausgelassen"] == 1, b


def test_gewichtetes_mittel_ueberspringt_zeitpunkte_mit_gewicht_null():
    """Summe der Gewichte null -> Division durch null. Zaehlen statt abstuerzen."""
    werte = {"A": {1: 0.01, 2: 0.02}}
    gewichte = {"A": {1: 0.0, 2: 5.0}}
    m, b = coinalyze.gewichtetes_mittel(werte, gewichte, ["A"], [], "x")
    assert sorted(m) == [2], m
    assert b["punkte_ohne_gewicht"] == 1, b


def test_funding_und_long_short_holen_die_richtigen_endpunkte_und_felder():
    gefragt = []

    def fake(req, timeout=0):
        gefragt.append(req.full_url)
        if "funding-rate-history" in req.full_url:
            return _FakeResp(json.dumps([{"symbol": "A.1", "history": [
                {"t": 1000, "o": 9.0, "c": 0.0002}]}]).encode())
        if "long-short-ratio-history" in req.full_url:
            return _FakeResp(json.dumps([{"symbol": "A.1", "history": [
                {"t": 1000, "r": 1.9, "l": 65.0, "s": 35.0}]}]).encode())
        return _FakeResp(json.dumps([]).encode())

    g = {"A.1": {1000 * 1000: 500.0}}
    f, _ = coinalyze.funding_aggregiert("KEY", ["A.1"], g, opener=fake, pause=0)
    assert f == {1000 * 1000: 0.0002}, f             # 'c', nicht 'o'
    ls, _ = coinalyze.long_short_aggregiert("KEY", ["A.1"], g, opener=fake, pause=0)
    assert ls == {1000 * 1000: 65.0}, ls             # 'l', nicht 's' oder 'r'
    assert any("funding-rate-history" in u for u in gefragt), gefragt
    assert any("long-short-ratio-history" in u for u in gefragt), gefragt


def test_skalen_vergleich_findet_einen_faktor_und_das_vorzeichen():
    """Vor dem Quellentausch: In classify_pattern ist das Vorzeichen skalenunabhaengig,
    die Schwelle funding_hot = 0.0001 aber nicht."""
    kraken = {1: 0.0008, 2: -0.0004, 3: 0.0016}
    coin = {1: 0.0001, 2: -0.00005, 3: 0.0002}       # rund ein Achtel
    v = coinalyze.skalen_vergleich(kraken, coin, "kraken", "coinalyze")
    assert v["gemeinsame_punkte"] == 3, v
    assert abs(v["faktor"] - 8.0) < 0.5, v
    assert v["gleiches_vorzeichen_anteil"] == 1.0, v


def test_skalen_vergleich_meldet_wenn_es_nichts_zu_vergleichen_gibt():
    v = coinalyze.skalen_vergleich({1: 0.1}, {2: 0.2}, "a", "b")
    assert "fehler" in v, v


def test_skalen_vergleich_zeigt_abweichende_vorzeichen():
    """Drehen die Reihen gegeneinander, ist es nicht dieselbe Groesse — dann hilft
    auch kein Umrechnungsfaktor."""
    v = coinalyze.skalen_vergleich({1: 0.1, 2: 0.1}, {1: 0.1, 2: -0.1}, "a", "b")
    assert v["gleiches_vorzeichen_anteil"] == 0.5, v


def test_gewichtetes_mittel_meldet_symbole_ganz_ohne_gewichtsreihe():
    """Randfall, den die anderen Tests nicht treffen: Ein Markt liefert Werte, aber
    ueberhaupt kein Open Interest. Er darf nicht als 'vorhanden' gelten — sonst
    stolpert die Rechnung ueber ein Gewicht, das es nicht gibt."""
    werte = {"A": {1: 0.01}, "OHNE_OI": {1: 0.99}}
    gewichte = {"A": {1: 10.0}}                      # OHNE_OI fehlt komplett
    m, b = coinalyze.gewichtetes_mittel(werte, gewichte, ["A", "OHNE_OI"], [], "x")
    assert m == {1: 0.01}, m                         # nur A zaehlt
    assert b["symbole"] == ["A"], b
    assert b["ohne_antwort"] == ["OHNE_OI"], b
