"""Engine-Hauptprogramm (E4b): Daten holen -> Strategie auswerten -> Signale senden.

Laeuft auf GitHub Actions (Cron). Nur Standardbibliothek.

Datenquellen (alle ohne API-Key, von US-Servern erreichbar):
- Kerzen + Spot-CVD: Binance Public-Data-Spiegel (data-api.binance.vision).
  Hinweis: fapi.binance.com (Futures) blockiert US-IPs (HTTP 451) -> nicht nutzbar.
- Open Interest + Funding: Kraken Futures (futures.kraken.com, PF_XBTUSD).
  OI gibt es nur als Snapshot -> die Engine baut eine eigene Historie auf
  (site/data/oi_history.json), die mit jedem Lauf waechst.

Ausgaben (fuer die Chart-Webseite, werden vom Workflow committet):
  site/data/state.json    — Position + aktuelle Fib-Zonen + Engine-Stand
  site/data/signals.json  — Signal-Historie (Chart-Marker)
  site/data/oi_history.json — selbst aufgebaute OI-Zeitreihe

Offline testbar: run_engine() akzeptiert injizierte Fetch-Funktionen (siehe test_main).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from strategy_core import (Candle, FibZones, FlowPoint, Impulse, Pivot, PosState,
                           Position, evaluate)
from telegram_notify import send_signals

ROOT = Path(__file__).resolve().parent.parent          # Repo-Wurzel (signal-app/)
DATA = ROOT / "site" / "data"
TIMEFRAME = "4h"
CANDLE_MS = 4 * 3600 * 1000
LIMIT = 400                                            # ~66 Tage Kontext

SPOT_URL = ("https://data-api.binance.vision/api/v3/klines"
            f"?symbol=BTCUSDT&interval={TIMEFRAME}&limit={LIMIT}")
KRAKEN_TICKERS_URL = "https://futures.kraken.com/derivatives/api/v3/tickers"
KRAKEN_FUNDING_URL = ("https://futures.kraken.com/derivatives/api/v4/"
                      "historicalfundingrates?symbol=PF_XBTUSD")


def _get_json(url: str, tries: int = 3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "btc-signal-app"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode())
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"Abruf fehlgeschlagen: {url} ({last})")


def _iso_to_ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


def _latest_leq(pairs, ts, default=0.0):
    val = default
    for t, v in pairs:
        if t <= ts:
            val = v
        else:
            break
    return val


# ------------------------------------------------------------- Daten-Layer

def fetch_oi_snapshot() -> tuple[int, float]:
    """Aktuelles Open Interest (USD) von Kraken Futures (PF_XBTUSD)."""
    data = _get_json(KRAKEN_TICKERS_URL)
    for t in data.get("tickers", []):
        if t.get("symbol") == "PF_XBTUSD":
            oi_usd = float(t["openInterest"]) * float(t["markPrice"])
            return int(time.time() * 1000), oi_usd
    raise RuntimeError("PF_XBTUSD nicht in Kraken-Tickers gefunden")


def fetch_funding_8h() -> list[tuple[int, float]]:
    """Kraken-Funding (stuendlich, relativ) -> auf 8h-Aequivalent skaliert."""
    data = _get_json(KRAKEN_FUNDING_URL)
    out = []
    for r in data.get("rates", []):
        out.append((_iso_to_ms(r["timestamp"]), float(r["relativeFundingRate"]) * 8.0))
    out.sort()
    return out


def fetch_market_data(oi_history: list[list] | None = None,
                      now_ms: int | None = None):
    """Holt Kerzen (Spot = Preisbasis), Spot-CVD, OI-Historie, Funding.

    Rueckgabe: (candles, flow, oi_history_neu) — nur ABGESCHLOSSENE Kerzen.
    Dokumentierte Abweichungen (docs/STRATEGIE.md §8 / ARCHITEKTUR.md):
    - Preisbasis Spot statt Perp (Differenz minimal), da Binance-Futures-API
      US-Server blockiert.
    - Futures-CVD nicht verfuegbar -> 0; der Kompass erkennt den Derivate-Pump
      stattdessen ueber OI + Funding + flaches Spot-CVD.
    - OI von Kraken (kleinere Boerse, aber gleiche Richtung); Historie waechst
      mit jedem Lauf — die ersten ~2 Tage sind die OI-Muster noch neutral.
    """
    now_ms = now_ms or int(time.time() * 1000)
    spot_raw = _get_json(SPOT_URL)
    funding = fetch_funding_8h()

    oi_history = list(oi_history or [])
    ts, oi = fetch_oi_snapshot()
    if not oi_history or ts - oi_history[-1][0] >= 30 * 60 * 1000:   # max. alle 30 Min
        oi_history.append([ts, oi])
    oi_history = oi_history[-2000:]
    oi_pairs = [(int(t), float(v)) for t, v in oi_history]

    candles: list[Candle] = []
    flow: list[FlowPoint] = []
    spot_cvd = 0.0
    first_oi = oi_pairs[0][1] if oi_pairs else 0.0
    for k in spot_raw:
        if int(k[6]) > now_ms:                                       # nur geschlossene
            continue
        c_ts = int(k[0])
        candles.append(Candle(c_ts, float(k[1]), float(k[2]), float(k[3]), float(k[4])))
        spot_cvd += 2.0 * float(k[10]) - float(k[7])                 # Taker-Delta in USD
        close_ts = c_ts + CANDLE_MS
        flow.append(FlowPoint(c_ts, spot_cvd, 0.0,
                              _latest_leq(oi_pairs, close_ts, default=first_oi),
                              _latest_leq(funding, close_ts)))
    return candles, flow, oi_history


# --------------------------------------------------------- State-Persistenz

def pos_to_state(pos: Position) -> dict:
    d = {"direction": pos.direction, "pos_state": pos.state.value,
         "last_signal_ts": pos.last_signal_ts, "retrace_extreme": pos.retrace_extreme,
         "tp_rungs": pos.tp_rungs, "zones": None}
    if pos.zones:
        z = pos.zones
        d["zones"] = {
            "impuls_start": z.impulse.start.price, "impuls_start_ts": z.impulse.start.ts,
            "impuls_start_kind": z.impulse.start.kind,
            "impuls_ende": z.impulse.end.price, "impuls_ende_ts": z.impulse.end.ts,
            "impuls_ende_kind": z.impulse.end.kind,
            "level_05": z.level_05, "gp_upper": z.gp_upper, "gp_lower": z.gp_lower,
            "level_0786": z.level_0786, "invalidation": z.invalidation,
        }
        if pos.retrace_extreme is not None:
            d["zones"]["ext1"] = z.ext_target(pos.retrace_extreme, 1.0)
            d["zones"]["ext2"] = z.ext_target(pos.retrace_extreme, 1.618)
    return d


def pos_from_state(d: dict) -> Position:
    pos = Position()
    if not d:
        return pos
    pos.direction = d.get("direction", "NONE")
    pos.state = PosState(d.get("pos_state", "FLAT"))
    pos.last_signal_ts = d.get("last_signal_ts", -1)
    pos.retrace_extreme = d.get("retrace_extreme")
    pos.tp_rungs = d.get("tp_rungs", 0)
    z = d.get("zones")
    if z and "impuls_start" in z:
        imp = Impulse(
            Pivot(0, z.get("impuls_start_ts", 0), z["impuls_start"], z.get("impuls_start_kind", "L")),
            Pivot(0, z.get("impuls_ende_ts", 0), z["impuls_ende"], z.get("impuls_ende_kind", "H")))
        pos.zones = FibZones(imp, z["level_05"], z["gp_upper"], z["gp_lower"],
                             z["level_0786"], z["invalidation"])
    return pos


# ------------------------------------------------------------ Orchestrierung

def run_engine(fetch=fetch_market_data, data_dir: Path = DATA,
               dry_run: bool = False) -> list[dict]:
    """Ein Engine-Lauf: nachholen aller neuen abgeschlossenen Kerzen, Signale senden."""
    data_dir.mkdir(parents=True, exist_ok=True)
    state_path = data_dir / "state.json"
    signals_path = data_dir / "signals.json"
    oi_path = data_dir / "oi_history.json"

    old_state = {}
    if state_path.exists():
        old_state = json.loads(state_path.read_text(encoding="utf-8"))
        if old_state.get("demo"):
            old_state = {}                                  # Demo-Daten verwerfen
    pos = pos_from_state(old_state)

    oi_history = []
    if oi_path.exists():
        oi_history = json.loads(oi_path.read_text(encoding="utf-8"))

    candles, flow, oi_history = fetch(oi_history)
    if not candles:
        print("Keine Kerzen erhalten — Abbruch.")
        return []

    cfg = old_state.get("config", {"bias_long": True, "bias_short": True})
    new_signals: list[dict] = []
    # Nachholen: alle Kerzen, die neuer sind als der letzte verarbeitete Stand
    for i, c in enumerate(candles):
        if c.ts <= pos.last_signal_ts:
            continue
        sigs = evaluate(candles[:i + 1], flow[:i + 1], pos,
                        bias_long=cfg.get("bias_long", True),
                        bias_short=cfg.get("bias_short", True))
        new_signals += [s.to_dict() for s in sigs]

    # Historie fortschreiben
    hist = {"signals": []}
    if signals_path.exists():
        h = json.loads(signals_path.read_text(encoding="utf-8"))
        if not h.get("demo"):
            hist = h
    hist["signals"] = (hist.get("signals", []) + new_signals)[-500:]

    state = pos_to_state(pos)
    state["config"] = cfg
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    state["last_close"] = candles[-1].close

    state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
    signals_path.write_text(json.dumps(hist, indent=1), encoding="utf-8")
    oi_path.write_text(json.dumps(oi_history), encoding="utf-8")

    if new_signals:
        send_signals(new_signals, dry_run=dry_run)
    print(f"Lauf ok: {len(candles)} Kerzen, {len(new_signals)} neue Signale, "
          f"OI-Punkte: {len(oi_history)}, Position: {pos.direction}/{pos.state.value}")
    return new_signals


def send_testnachricht():
    ts = int(time.time() * 1000)
    send_signals([{"ts": ts, "type": "WARNUNG", "label": "TESTNACHRICHT — Einrichtung ok",
                   "price": 0.0, "tranche_pct": 0,
                   "reason": "Telegram-Verbindung funktioniert. Ab jetzt kommen echte Trigger."}])


if __name__ == "__main__":
    if "--test-telegram" in sys.argv:
        send_testnachricht()
    else:
        run_engine(dry_run="--dry-run" in sys.argv or not os.environ.get("TELEGRAM_BOT_TOKEN"))
