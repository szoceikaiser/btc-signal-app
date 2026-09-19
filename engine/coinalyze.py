"""Coinalyze-Datenanbindung (E9.1): historisches OI, Funding, Liquidationen.

Nur Standardbibliothek (urllib) — laeuft ohne Zusatzpakete auf GitHub Actions.
Key aus Umgebungsvariable COINALYZE_API_KEY (GitHub-Secret). Doku:
https://api.coinalyze.net/v1/doc/  ·  Rate-Limit 40 Abrufe/Min.

STAND E9.1: Dies ist zunaechst eine PROBE — sie holt eine kleine Stichprobe und schreibt
das ROHE Antwortformat nach site/data/coinalyze_probe.json, damit das echte Format
verifiziert werden kann, bevor der Parser gebaut wird. Kein Blind-Parsen.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://api.coinalyze.net/v1"
# ACHTUNG, hier stand bis 19.09.2026 etwas Falsches: ".A" ist NICHT "aggregiert".
# In /exchanges steht A fuer BINANCE (per Probe 19.09.2026 nachgeprueft; die Liste hat
# 28 Boersen und KEINEN Code fuer ein Aggregat). Alles, was die Engine von Coinalyze
# bezieht — Open Interest, Funding, Liquidationen, Futures-CVD, Long-Short — kommt
# also von einer einzigen Boerse. Wer das aendern will, muss mehrere Symbole holen und
# selbst zusammenrechnen; siehe spot_probe() weiter unten.
SYMBOL = "BTCUSDT_PERP.A"        # BTC/USDT-Perpetual auf Binance (A = Binance)
INTERVAL = "4hour"               # beim ersten Lauf verifizieren (evtl. "H4"/"4h")
ROOT = Path(__file__).resolve().parent.parent

# Endpoints (Name -> Pfad); beim ersten Live-Lauf gegen die Antwort abgleichen.
ENDPOINTS = {
    "open_interest": "open-interest-history",
    "funding": "funding-rate-history",
    "liquidations": "liquidation-history",
}

# E15: Was bietet Coinalyze AUSSER dem, was wir schon nutzen? Zwei offene Luecken:
#   (1) Futures-CVD fehlt komplett — fapi.binance.com sperrt US-Runner (HTTP 451).
#       Wenn eine dieser Historien Taker-Kauf-/Verkaufsvolumen liefert, ist Muster 2
#       (Derivate-Pump) erstmals mit echten Daten pruefbar statt ueber Hilfsmerkmale.
#   (2) Long-Short-Verhaeltnis — bei Furkan Teil der Positionierungs-Einschaetzung.
# Kein Blind-Parsen (Projektregel): erst die ROHE Antwort holen und ansehen, dann bauen.
# Namen sind Kandidaten aus der Coinalyze-Doku; nicht existierende geben 404 und werden
# als solche protokolliert — der Lauf scheitert daran nicht.
KANDIDATEN = {
    "ohlcv": "ohlcv-history",
    "buy_sell_volume": "buy-sell-volume-history",
    "long_short_ratio": "long-short-ratio-history",
    "predicted_funding": "predicted-funding-rate-history",
    "future_markets": "future-markets",
    "exchanges": "exchanges",
}


def build_url(endpoint: str, params: dict) -> str:
    """Reine URL-Konstruktion (offline testbar)."""
    return f"{BASE}/{endpoint}?{urllib.parse.urlencode(params)}"


def get_json(endpoint: str, params: dict, api_key: str,
             opener=urllib.request.urlopen, timeout: int = 30):
    """GET auf einen Coinalyze-Endpoint; Key im Header. `opener` injizierbar (Tests)."""
    req = urllib.request.Request(build_url(endpoint, params),
                                 headers={"api_key": api_key})
    with opener(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def fetch_history(endpoint: str, api_key: str, symbol: str = SYMBOL,
                  interval: str = INTERVAL, days: int = 7,
                  frm: int | None = None, to: int | None = None, **kw):
    """Holt eine History (from/to in Unix-Sekunden). Ohne frm/to: letzte `days` Tage."""
    if to is None:
        to = int(time.time())
    if frm is None:
        frm = to - days * 86400
    params = {"symbols": symbol, "interval": interval,
              "from": frm, "to": to, "convert_to_usd": "true"}
    return get_json(endpoint, params, api_key, **kw)


# --------------------------------------------------- Parser (echtes Format)
# Antwortformat (per Test-Lauf 2026-07-24 bestaetigt): Liste je Symbol mit
#   {"symbol": "...", "history": [ {t, o, h, l, c}, ... ]}
# t = Open-Time in Unix-SEKUNDEN. open-interest-history & funding-rate-history sind
# OHLC (Close = Wert je Kerze). liquidation-history: {t, l, s} mit l=Long-Liq (USD),
# s=Short-Liq (USD). convert_to_usd=true -> OI/Liq in USD.


def _history_points(data, symbol: str = SYMBOL) -> list:
    """Zieht das history-Array fuer das Symbol aus der Coinalyze-Antwort."""
    for item in data or []:
        if isinstance(item, dict) and item.get("symbol") == symbol \
                and isinstance(item.get("history"), list):
            return item["history"]
    for item in data or []:                              # Fallback: erstes history-Array
        if isinstance(item, dict) and isinstance(item.get("history"), list):
            return item["history"]
    return []


def oi_by_ts(api_key: str, **kw) -> dict:
    """{Open-Time_ms: OI_Close_USD} aus open-interest-history (OHLC -> Close)."""
    pts = _history_points(fetch_history("open-interest-history", api_key, **kw))
    return {int(p["t"]) * 1000: float(p["c"]) for p in pts if "t" in p and "c" in p}


def funding_by_ts(api_key: str, **kw) -> dict:
    """{Open-Time_ms: Funding_Close} aus funding-rate-history (Skalierung siehe Wiring)."""
    pts = _history_points(fetch_history("funding-rate-history", api_key, **kw))
    return {int(p["t"]) * 1000: float(p["c"]) for p in pts if "t" in p and "c" in p}


def liquidations_by_ts(api_key: str, **kw) -> dict:
    """{Open-Time_ms: (Long-Liq_USD, Short-Liq_USD)} aus liquidation-history (l, s)."""
    pts = _history_points(fetch_history("liquidation-history", api_key, **kw))
    return {int(p["t"]) * 1000: (float(p.get("l", 0.0)), float(p.get("s", 0.0)))
            for p in pts if "t" in p}


def fut_delta_by_ts(api_key: str, **kw) -> dict:
    """{Open-Time_ms: Taker-Delta je Kerze} aus ohlcv-history des Futures-Marktes (E16).

    Antwortformat per Probe 2026-07-28 bestaetigt: {t, o, h, l, c, v, bv, tx, btx} mit
    v = Gesamtvolumen der Kerze, bv = davon Taker-KAEUFE. Daraus folgt
        Delta = Kaeufe - Verkaeufe = bv - (v - bv) = 2*bv - v
    — dieselbe Formel, die main.py fuer die Binance-Spotkerzen verwendet.

    DAS SCHLIESST DIE GROESSTE DATENLUECKE DES PROJEKTS: Futures-CVD gab es bisher nicht
    (fapi.binance.com sperrt US-Runner mit HTTP 451), deshalb war in classify_pattern der
    Zweig `if has_fut:` seit dem ersten Tag toter Code und Muster 2 (Derivate-Pump) lief
    nur ueber Ersatzmerkmale. Coinalyze liefert es mit Historie.

    NICHT aggregiert (Korrektur 19.09.2026): wie bei OI, Funding und Liquidationen ist
    das Symbol BTCUSDT_PERP.A der Binance-Markt, nicht ein Boersen-Durchschnitt.

    EINHEIT: Die Werte sind Kontrakt-/Basiswert-Mengen (BTC), nicht USD — anders als das
    Spot-Delta. Fuer classify_pattern ist das unerheblich: dort geht das kumulierte Delta
    nur ueber `_slope()` ein, also als RELATIVE Veraenderung, und der Vergleich
    `spot <= fut / 3` stellt zwei solche relativen Werte gegenueber. Die Einheit kuerzt
    sich heraus. Wer die Reihe je absolut auswerten will, muss sie erst mit dem Preis
    multiplizieren.
    """
    pts = _history_points(fetch_history("ohlcv-history", api_key, **kw))
    out = {}
    for p in pts:
        if "t" in p and "v" in p and "bv" in p:
            out[int(p["t"]) * 1000] = 2.0 * float(p["bv"]) - float(p["v"])
    return out


def long_short_by_ts(api_key: str, **kw) -> dict:
    """{Open-Time_ms: Long-Anteil in Prozent} aus long-short-ratio-history (E16).

    Format per Probe: {t, r, l, s} mit r = Verhaeltnis long/short, l/s = Anteile in
    Prozent (Beispiel 2026-07-28: r=1.867, l=65.12, s=34.88). Wir speichern den
    Long-Anteil `l`, weil er ohne Division auskommt und direkt lesbar ist:
    ueber 50 = mehrheitlich long positioniert. Furkan nutzt diese Groesse zur
    Einschaetzung der Positionierung ("Longueberhang").
    """
    pts = _history_points(fetch_history("long-short-ratio-history", api_key, **kw))
    return {int(p["t"]) * 1000: float(p["l"]) for p in pts if "t" in p and "l" in p}


# ------------------------------------------- E37: Spot-Maerkte (Kaisers Frage 19.09.2026)
# AUSLOESER: Furkan aggregiert sein Spot-CVD auf Velo ueber Binance, Coinbase, Bybit und
# OKX und betont es ausdruecklich ("Wir schauen nicht nur auf eine Boerse"). Die
# Velo-API scheidet aus (199 $/Monat), und ausser Binance liefert keine Boerse das
# Taker-Kaufvolumen fertig in den Kerzen — Coinalyze ist der einzige gangbare Weg.
#
# BEFUND DER ERSTEN PROBE (Lauf 19.09.2026, 17:50 UTC) — und er ist groesser als die
# Frage war: In /exchanges steht "A" fuer BINANCE. Es gibt in der ganzen Liste KEINEN
# Code fuer ein Aggregat (28 Boersen, 16 davon mit Maerkten, kein unbekannter Code).
# Damit ist der Kommentar an SYMBOL seit E9.1 falsch: BTCUSDT_PERP.A ist Binance,
# nicht "aggregiert ueber Boersen". Open Interest, Funding, Liquidationen, Futures-CVD
# und Long-Short-Verhaeltnis kommen also ALLE von einer einzigen Boerse — genau das,
# wovon Furkan abraet. Aggregieren muessen wir selbst.
#
# WAS DIE ERSTE PROBE SCHON BEWIESEN HAT: ohlcv-history liefert fuer Spot-Symbole
# 'v' (Gesamtvolumen) und 'bv' (Taker-Kaeufe), also alles fuer Delta = 2*bv - v,
# und reicht rund 334 Tage zurueck (2005 4h-Punkte). Das genuegt fuer einen Backtest.
#
# WAS DIESE ZWEITE PROBE KLAERT — wieder nur fragen, nicht bauen:
#   1. Welche BTC-Spotmaerkte gegen Dollar gibt es auf Furkans vier Boersen, und
#      welches Symbol heisst dort wie? (Die Schreibweise ist je Boerse anders:
#      "BTCARS.A" auf Binance, aber "sBTCEUR.6" auf Bybit.)
#   2. Nimmt ein Abruf MEHRERE Symbole auf einmal? Nur dann ist Aggregieren billig.
#   3. Reicht die Historie auf allen vier gleich weit? Der kuerzeste bestimmt das
#      Backtest-Fenster.
BOERSEN_CODES = {"A": "Binance", "C": "Coinbase", "6": "Bybit", "3": "OKX"}
DOLLAR_QUOTES = ("USDT", "USD", "USDC", "FDUSD", "USDE")   # Vorrang in dieser Reihenfolge
SPOT_REICHWEITE_TAGE = 365        # so weit zurueck fragen, um die ECHTE Grenze zu sehen


def _ist_btc_dollar_markt(e, codes) -> bool:
    """BTC gegen Dollar, auf einer der gesuchten Boersen, mit Kauf-/Verkaufsdaten.

    Streng nach den Feldern, die der Lauf vom 19.09.2026 gezeigt hat:
    {symbol, exchange, symbol_on_exchange, base_asset, quote_asset, has_buy_sell_data}.
    base_asset MUSS BTC sein — sonst rutschen Paare wie WLDBTC (Worldcoin gegen BTC)
    durch, die in der ersten Probe genau das getan haben.
    """
    if not isinstance(e, dict):
        return False
    return (e.get("base_asset") == "BTC"
            and e.get("quote_asset") in DOLLAR_QUOTES
            and e.get("exchange") in codes
            and bool(e.get("has_buy_sell_data")))


def _je_boerse_ein_symbol(maerkte: list, codes=BOERSEN_CODES) -> dict:
    """Pro Boerse EIN Symbol, Quote-Waehrung nach der Rangfolge in DOLLAR_QUOTES.

    Warum eine feste Rangfolge: BTC/USDT und BTC/USD sind verschiedene Maerkte mit
    verschiedenem Volumen. Wuerde die Auswahl von der Listenreihenfolge abhaengen,
    kaeme bei jedem Lauf etwas anderes heraus und die Messungen waeren nicht
    vergleichbar.
    """
    treffer: dict = {}
    for e in maerkte:
        if not _ist_btc_dollar_markt(e, codes):
            continue
        code = e["exchange"]
        rang = DOLLAR_QUOTES.index(e["quote_asset"])
        bisher = treffer.get(code)
        if bisher is None or rang < bisher["rang"]:
            treffer[code] = {"rang": rang, "symbol": e.get("symbol"),
                             "quote": e.get("quote_asset"),
                             "boerse": codes.get(code, code)}
    return {c: {k: v for k, v in d.items() if k != "rang"} for c, d in treffer.items()}


def _pruefe_symbole(api_key: str, symbole: list, **kw) -> dict:
    """EIN Abruf mit ALLEN Symbolen — beantwortet Frage 2 und 3 in einem Zug.

    Coinalyze nimmt den Parameter `symbols` (Mehrzahl). Kommt je Symbol eine eigene
    Reihe zurueck, laesst sich das Aggregat mit einem einzigen Abruf bilden; kommt nur
    eine, muessten wir je Boerse einzeln fragen (viermal so viele Abrufe).
    """
    if not symbole:
        return {"fehler": "keine Symbole zu pruefen"}
    try:
        roh = fetch_history("ohlcv-history", api_key, symbol=",".join(symbole),
                            days=SPOT_REICHWEITE_TAGE, **kw)
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode(errors="replace")[:300]}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {str(e)[:250]}"}
    if not isinstance(roh, list):
        return {"fehler": "Antwort ist keine Liste", "antwort_roh": _sample(roh)}

    je_symbol = {}
    for eintrag in roh:
        if not isinstance(eintrag, dict):
            continue
        punkte = eintrag.get("history") or []
        felder = sorted({k for p in punkte if isinstance(p, dict) for k in p})
        zeiten = [int(p["t"]) for p in punkte if isinstance(p, dict) and "t" in p]
        je_symbol[eintrag.get("symbol", "?")] = {
            "punkte": len(punkte),
            "felder": felder,
            "hat_v_und_bv": ("v" in felder and "bv" in felder),
            "reichweite_tage": round((max(zeiten) - min(zeiten)) / 86400.0, 1)
                               if len(zeiten) > 1 else 0.0,
            "von": time.strftime("%Y-%m-%d %H:%M", time.gmtime(min(zeiten))) if zeiten else "",
            "letzter_punkt": punkte[-1] if punkte else None,
        }
    return {"angefragt": len(symbole), "zurueck": len(je_symbol),
            "mehrfachabruf_geht": len(je_symbol) > 1, "je_symbol": je_symbol}


def spot_probe(api_key: str, **kw) -> dict:
    """Klaert, ob sich ein ueber Boersen aggregiertes Spot-CVD bauen laesst.

    Es wird nichts gebaut und nichts entschieden — nur gefragt und berichtet.
    """
    out: dict = {"_frage": ("Gibt es BTC-Dollar-Spotmaerkte auf Binance, Coinbase, Bybit "
                            "und OKX mit Kauf-/Verkaufsdaten, laesst sich alles in EINEM "
                            "Abruf holen, und wie weit reicht die Historie?")}
    try:
        maerkte_roh = get_json("spot-markets", {}, api_key, **kw)
    except urllib.error.HTTPError as e:
        out["spot_markets"] = {"http_error": e.code,
                               "body": e.read().decode(errors="replace")[:300]}
        out["_ergebnis"] = ("Der Endpunkt /spot-markets hat NICHT geantwortet (siehe "
                            "http_error). Damit faellt der Coinalyze-Weg aus.")
        return out
    except Exception as e:  # noqa: BLE001
        out["spot_markets"] = {"error": f"{type(e).__name__}: {str(e)[:250]}"}
        out["_ergebnis"] = "Abruf gescheitert (kein HTTP-Fehler) — siehe 'error'."
        return out

    maerkte = maerkte_roh if isinstance(maerkte_roh, list) else []
    passend = [e for e in maerkte if _ist_btc_dollar_markt(e, BOERSEN_CODES)]
    gewaehlt = _je_boerse_ein_symbol(maerkte)
    out["spot_markets"] = {
        "anzahl_gesamt": len(maerkte),
        "btc_dollar_auf_furkans_boersen": len(passend),
        "alle_passenden_roh": passend[:40],       # roh, zum Nachsehen
    }
    out["gewaehlt_je_boerse"] = gewaehlt

    symbole = [d["symbol"] for d in gewaehlt.values() if d.get("symbol")]
    out["mehrfachabruf"] = _pruefe_symbole(api_key, symbole, **kw)

    fehlend = [name for code, name in BOERSEN_CODES.items() if code not in gewaehlt]
    je = out["mehrfachabruf"].get("je_symbol", {})
    brauchbar = [s for s, d in je.items() if d.get("hat_v_und_bv")]
    weiten = [d["reichweite_tage"] for d in je.values()
              if isinstance(d.get("reichweite_tage"), (int, float)) and d["reichweite_tage"]]

    if not gewaehlt:
        ergebnis = ("NEIN: auf keiner der vier Boersen wurde ein BTC-Dollar-Spotmarkt "
                    "mit Kauf-/Verkaufsdaten gefunden.")
    elif not brauchbar:
        ergebnis = ("NEIN: Symbole gefunden, aber keines liefert 'v' UND 'bv'. Ohne "
                    "beide Zahlen gibt es kein Kauf-/Verkaufs-Delta.")
    else:
        ergebnis = (f"JA fuer {len(brauchbar)} von {len(BOERSEN_CODES)} Boersen: "
                    f"{', '.join(brauchbar)} liefern Gesamtvolumen und Taker-Kaeufe. "
                    "Aggregiert wird von UNS, nicht von Coinalyze — dort gibt es kein "
                    "Aggregat-Symbol.")
        ergebnis += (" Ein Abruf liefert alle Reihen auf einmal."
                     if out["mehrfachabruf"].get("mehrfachabruf_geht")
                     else " ACHTUNG: der Mehrfachabruf gab nur eine Reihe zurueck — je "
                          "Boerse muss einzeln gefragt werden.")
    if fehlend:
        ergebnis += f" Ohne passenden Markt: {', '.join(fehlend)}."
    if weiten:
        ergebnis += (f" Historie: {min(weiten):.0f} bis {max(weiten):.0f} Tage — der "
                     "KUERZESTE bestimmt das Backtest-Fenster.")
    out["_ergebnis"] = ergebnis
    return out



SAMPLE_MAX_EINTRAEGE = 40    # Listenlaenge in der Probe-Datei (siehe unten)


def _sample(data):
    """Behaelt nur die letzten 3 Punkte je Symbol (kleine Probe fuers Log/JSON).

    Deckelt ausserdem die Laenge der Liste selbst. Grund (19.09.2026): die
    Metadaten-Endpunkte geben Tausende Eintraege zurueck — future-markets 5436,
    spot-markets 5953 — und die Probe-Datei wuchs dadurch auf 2 MB, die bei JEDEM
    Lauf ins Repo committet wurden. Wie viele weggelassen wurden, steht als letzter
    Eintrag drin, damit niemand eine gekuerzte Liste fuer die ganze haelt.
    """
    try:
        if isinstance(data, list):
            slim = []
            for item in data[:SAMPLE_MAX_EINTRAEGE]:
                it = dict(item) if isinstance(item, dict) else item
                if isinstance(it, dict) and isinstance(it.get("history"), list):
                    it = dict(it)
                    it["history"] = it["history"][-3:]
                slim.append(it)
            if len(data) > SAMPLE_MAX_EINTRAEGE:
                slim.append({"_gekuerzt": f"{len(data) - SAMPLE_MAX_EINTRAEGE} weitere "
                                          f"Eintraege weggelassen (von {len(data)})"})
            return slim
        return data
    except Exception:  # noqa: BLE001 — Probe soll nie hart scheitern
        return data


def probe():
    """Holt Mini-Stichproben und schreibt das rohe Format nach coinalyze_probe.json."""
    api_key = os.environ.get("COINALYZE_API_KEY", "")
    out = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "symbol": SYMBOL,
        "interval": INTERVAL,
    }
    if not api_key:
        out["error"] = "COINALYZE_API_KEY fehlt (Secret nicht gesetzt?)"
    else:
        def _hole(ep, ohne_zeitraum=False):
            if ohne_zeitraum:                      # Metadaten-Endpunkte kennen kein from/to
                return _sample(get_json(ep, {}, api_key))
            return _sample(fetch_history(ep, api_key))

        def _versuch(ep, ohne_zeitraum=False):
            try:
                return _hole(ep, ohne_zeitraum), None
            except urllib.error.HTTPError as e:
                return {"http_error": e.code,
                        "body": e.read().decode(errors="replace")[:400]}, e.code
            except Exception as e:  # noqa: BLE001
                return {"error": f"{type(e).__name__}: {str(e)[:300]}"}, "exc"

        for name, ep in ENDPOINTS.items():
            out[name], _ = _versuch(ep)

        # --- E15: Kandidaten-Endpunkte abklopfen (fuer Futures-CVD + Long-Short) -------
        gefunden, fehlt = [], []
        kand = {}
        for name, ep in KANDIDATEN.items():
            time.sleep(1.6)                        # Rate-Limit 40/Min respektieren
            daten, fehler = _versuch(ep, ohne_zeitraum=name in ("future_markets", "exchanges"))
            kand[name] = {"pfad": ep, "antwort": daten}
            (fehlt if fehler else gefunden).append(f"{name} ({ep})")
        out["kandidaten"] = kand

        # --- E37: Spot-Maerkte (Kaisers Frage nach Furkans Aggregation) --------------
        time.sleep(1.6)
        try:
            out["spot"] = spot_probe(api_key)
        except Exception as e:  # noqa: BLE001 — Probe soll nie hart scheitern
            out["spot"] = {"error": f"{type(e).__name__}: {str(e)[:300]}"}

        out["_ergebnis"] = {
            "nutzbar": gefunden or ["— keiner"],
            "nicht_vorhanden": fehlt or ["— keiner"],
            "_lesehilfe": ("'nutzbar' = Endpunkt existiert und hat geantwortet; jetzt im "
                           "Feld 'kandidaten' nachsehen, WELCHE Felder drin sind. Fuer "
                           "Futures-CVD brauchen wir Taker-Kauf- und -Verkaufsvolumen "
                           "getrennt (oft 'bv'/'sv' oder 'buy_volume'/'sell_volume'). "
                           "Nur wenn beides da ist, laesst sich ein echtes Futures-CVD "
                           "bilden."),
        }
        print("\nNUTZBAR:", ", ".join(gefunden) or "keiner")
        print("NICHT VORHANDEN:", ", ".join(fehlt) or "keiner")
        print("\nSPOT (E37):", out.get("spot", {}).get("_ergebnis", "— nicht gelaufen"))
    path = ROOT / "site" / "data" / "coinalyze_probe.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("Probe geschrieben:", path)
    print(json.dumps(out, indent=1, ensure_ascii=False)[:2500])


if __name__ == "__main__":
    probe()
