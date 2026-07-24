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
                  interval: str = INTERVAL, days: int = 7, **kw):
    to = int(time.time())
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
        for name, ep in ENDPOINTS.items():
            try:
                out[name] = _sample(fetch_history(ep, api_key))
            except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")[:800]
                out[name] = {"http_error": e.code, "body": body}
            except Exception as e:  # noqa: BLE001
                out[name] = {"error": f"{type(e).__name__}: {str(e)[:300]}"}
    path = ROOT / "site" / "data" / "coinalyze_probe.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("Probe geschrieben:", path)
    print(json.dumps(out, indent=1, ensure_ascii=False)[:2500])


if __name__ == "__main__":
    probe()
