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
SYMBOL = "BTCUSDT_PERP.A"        # aggregiert ueber Boersen (.A = aggregated)
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
    nur ueber Ersatzmerkmale. Coinalyze liefert es aggregiert ueber Boersen, mit Historie.

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


def _sample(data):
    """Behaelt nur die letzten 3 Punkte je Symbol (kleine Probe fuers Log/JSON)."""
    try:
        if isinstance(data, list):
            slim = []
            for item in data:
                it = dict(item) if isinstance(item, dict) else item
                if isinstance(it, dict) and isinstance(it.get("history"), list):
                    it = dict(it)
                    it["history"] = it["history"][-3:]
                slim.append(it)
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
    path = ROOT / "site" / "data" / "coinalyze_probe.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("Probe geschrieben:", path)
    print(json.dumps(out, indent=1, ensure_ascii=False)[:2500])


if __name__ == "__main__":
    probe()
