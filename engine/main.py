"""Engine-Hauptprogramm (E4b): Daten holen -> Strategie auswerten -> Signale senden.

Laeuft auf GitHub Actions (Cron). Nur Standardbibliothek.
Ausgaben (fuer die Chart-Webseite, werden vom Workflow committet):
  site/data/state.json    — Position + aktuelle Fib-Zonen + Engine-Stand
  site/data/signals.json  — Signal-Historie (Chart-Marker)

Offline testbar: run_engine() akzeptiert injizierte Fetch-Funktionen (siehe smoke_test).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
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
FUT_URL = ("https://fapi.binance.com/fapi/v1/klines"
           f"?symbol=BTCUSDT&interval={TIMEFRAME}&limit={LIMIT}")
OI_URL = ("https://fapi.binance.com/futures/data/openInterestHist"
          f"?symbol=BTCUSDT&period={TIMEFRAME}&limit=200")
FUND_URL = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=100"


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


# ------------------------------------------------------------- Daten-Layer

def fetch_market_data(now_ms: int | None = None):
    """Holt Kerzen (Futures = Handelsbasis), Spot-/Futures-CVD, OI, Funding.

    Rueckgabe: (candles, flow) — nur ABGESCHLOSSENE Kerzen.
    Hinweis (dokumentierte Abweichung, STRATEGIE.md §8): V1 nutzt Binance statt
    Boersen-Aggregation; Bybit/OKX-Aggregation ist eine E4b-Verfeinerung.
    """
    now_ms = now_ms or int(time.time() * 1000)
    fut_raw = _get_json(FUT_URL)
    spot_raw = _get_json(SPOT_URL)
    oi_raw = _get_json(OI_URL)
    fund_raw = _get_json(FUND_URL)

    fut = [k for k in fut_raw if int(k[6]) <= now_ms]          # nur geschlossene
    spot = {int(k[0]): k for k in spot_raw}

    candles: list[Candle] = []
    flow: list[FlowPoint] = []
    spot_cvd = fut_cvd = 0.0
    oi_by_ts = sorted((int(o["timestamp"]), float(o["sumOpenInterestValue"]))
                      for o in oi_raw)
    fund_by_ts = sorted((int(f["fundingTime"]), float(f["fundingRate"]))
                        for f in fund_raw)

    def latest_leq(pairs, ts, default=0.0):
        val = default
        for t, v in pairs:
            if t <= ts:
                val = v
            else:
                break
        return val

    for k in fut:
        ts = int(k[0])
        candles.append(Candle(ts, float(k[1]), float(k[2]), float(k[3]), float(k[4])))
        # CVD in USD: Taker-Buy-Quote minus Taker-Sell-Quote (= quoteVol - takerBuyQuote)
        fut_cvd += 2.0 * float(k[10]) - float(k[7])
        s = spot.get(ts)
        if s is not None:
            spot_cvd += 2.0 * float(s[10]) - float(s[7])
        close_ts = ts + CANDLE_MS
        flow.append(FlowPoint(ts, spot_cvd, fut_cvd,
                              latest_leq(oi_by_ts, close_ts),
                              latest_leq(fund_by_ts, close_ts)))
    return candles, flow


# --------------------------------------------------------- State-Persistenz

def pos_to_state(pos: Position) -> dict:
    d = {"direction": pos.direction, "pos_state": pos.state.value,
         "last_signal_ts": pos.last_signal_ts, "retrace_extreme": pos.retrace_extreme,
         "zones": None}
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

    old_state = {}
    if state_path.exists():
        old_state = json.loads(state_path.read_text(encoding="utf-8"))
        if old_state.get("demo"):
            old_state = {}                                  # Demo-Daten verwerfen
    pos = pos_from_state(old_state)

    candles, flow = fetch()
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

    if new_signals:
        send_signals(new_signals, dry_run=dry_run)
    print(f"Lauf ok: {len(candles)} Kerzen, {len(new_signals)} neue Signale, "
          f"Position: {pos.direction}/{pos.state.value}")
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
