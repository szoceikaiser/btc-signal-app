"""Backtest + Kalibrierung (E4b): Engine gegen Kaisers notierte Furkan-Trigger.

Laeuft auf GitHub Actions (workflow_dispatch). Zeitraum: Sep 2025 - Apr 2026.
Datenbasis: Binance-Vision-Spotkerzen 4h (inkl. Taker-Volumen -> Spot-CVD) und
Kraken-Funding-Historie (stuendlich, x8). Open Interest hat fuer den Zeitraum keine
kostenlose Historie -> konstant (OI-Muster neutral; dokumentierte Einschraenkung).

Ergebnis: BACKTEST.md im Repo-Root (Tabelle aller Parameter-Kombinationen +
Detailauswertung der besten). Ausfuehren: python3 backtest.py
"""

from __future__ import annotations

import json
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from main import _get_json, fetch_funding_8h
from strategy_core import Candle, FlowPoint, Position, evaluate

ROOT = Path(__file__).resolve().parent.parent
CANDLE_MS = 4 * 3600 * 1000
WARMUP_MS = int(datetime(2025, 8, 10, tzinfo=timezone.utc).timestamp() * 1000)
START_MS = int(datetime(2025, 9, 1, tzinfo=timezone.utc).timestamp() * 1000)
END_MS = int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp() * 1000)

# Kaisers notierte Trigger (Kauftrigger.md / Verkaufstrigger.md; Duplikate entfernt,
# laut Kaiser evtl. Versehen -> tolerant gewertet)
KAUF_DATEN = [
    "2025-09-25", "2025-10-10", "2025-10-21", "2025-10-27", "2025-10-28",
    "2025-10-29", "2025-10-30", "2025-11-04", "2025-11-17", "2025-11-20",
    "2025-11-21", "2026-01-06", "2026-01-08", "2026-01-20", "2026-01-29",
    "2026-01-30", "2026-01-31", "2026-02-28", "2026-03-23", "2026-03-27",
]
VERKAUF_DATEN = [
    "2025-09-25", "2025-10-02", "2025-10-03", "2025-10-10", "2025-10-16",
    "2025-11-04", "2025-11-12", "2025-11-23", "2025-11-28", "2025-12-02",
    "2025-12-03", "2025-12-17", "2026-01-06", "2026-01-14", "2026-01-25",
    "2026-02-02", "2026-02-23", "2026-02-28", "2026-03-02", "2026-03-17",
    "2026-04-08", "2026-04-14", "2026-04-17", "2026-04-22",
]

# Kauf-Handlung = Long eroeffnen/aufstocken ODER Short zurueckkaufen
BUY_TYPES = {"KAUF_1", "KAUF_2", "NACHKAUF",
             "SHORT_TP_1", "SHORT_TP_2", "SHORT_COVER_REST", "SHORT_STOPLOSS"}
# Verkauf-Handlung = Long reduzieren/schliessen ODER Short eroeffnen/aufstocken
SELL_TYPES = {"TEILVERKAUF_1", "TEILVERKAUF_2", "VERKAUF_REST", "STOPLOSS",
              "SHORT_1", "SHORT_2", "SHORT_NACHLEGEN"}

GRID = [(n, k) for n in (3, 4, 5, 6) for k in (2.0, 3.0)]


def fetch_candles_range(start_ms: int, end_ms: int) -> list:
    """Binance-Vision-Spotkerzen 4h, paginiert (1000er-Bloecke)."""
    out, cursor = [], start_ms
    while cursor < end_ms:
        url = ("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT"
               f"&interval=4h&limit=1000&startTime={cursor}&endTime={end_ms}")
        chunk = _get_json(url)
        if not chunk:
            break
        out += chunk
        cursor = int(chunk[-1][0]) + CANDLE_MS
        if len(chunk) < 1000:
            break
        time.sleep(0.3)
    return out


def build_series(raw: list, funding: list[tuple[int, float]]):
    candles, flow, spot_cvd = [], [], 0.0

    def latest_leq(pairs, ts):
        val = 0.0
        for t, v in pairs:
            if t <= ts:
                val = v
            else:
                break
        return val

    for k in raw:
        ts = int(k[0])
        candles.append(Candle(ts, float(k[1]), float(k[2]), float(k[3]), float(k[4])))
        spot_cvd += 2.0 * float(k[10]) - float(k[7])
        flow.append(FlowPoint(ts, spot_cvd, 0.0, 1.0,          # OI konstant (neutral)
                              latest_leq(funding, ts + CANDLE_MS)))
    return candles, flow


def run_backtest(candles, flow, pivot_n: int, k_atr: float) -> list[dict]:
    pos = Position()
    signals = []
    for i in range(len(candles)):
        if candles[i].ts < START_MS:
            pos.last_signal_ts = candles[i].ts                 # Warmup ohne Signale
            continue
        for s in evaluate(candles[:i + 1], flow[:i + 1], pos,
                          pivot_n=pivot_n, k_atr=k_atr):
            signals.append(s.to_dict())
    return signals


def to_date(ts_ms: int) -> date:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date()


def score(signals: list[dict], tol_days: int = 1) -> dict:
    kauf = [date.fromisoformat(d) for d in KAUF_DATEN]
    verkauf = [date.fromisoformat(d) for d in VERKAUF_DATEN]
    buy_days = sorted({to_date(s["ts"]) for s in signals if s["type"] in BUY_TYPES})
    sell_days = sorted({to_date(s["ts"]) for s in signals if s["type"] in SELL_TYPES})

    def near(d, days):
        return any(abs((d - x).days) <= tol_days for x in days)

    hit_k = [d for d in kauf if near(d, buy_days)]
    hit_v = [d for d in verkauf if near(d, sell_days)]
    prec_days = [d for d in buy_days if near(d, kauf)] + \
                [d for d in sell_days if near(d, verkauf)]
    total_days = len(buy_days) + len(sell_days)
    return {
        "hit_k": hit_k, "miss_k": [d for d in kauf if d not in hit_k],
        "hit_v": hit_v, "miss_v": [d for d in verkauf if d not in hit_v],
        "recall": (len(hit_k) + len(hit_v)) / (len(kauf) + len(verkauf)),
        "precision": len(prec_days) / total_days if total_days else 0.0,
        "buy_days": buy_days, "sell_days": sell_days,
    }


def main():
    print("Lade Kerzen ...")
    raw = fetch_candles_range(WARMUP_MS, END_MS)
    print(f"{len(raw)} Kerzen geladen.")
    try:
        funding = fetch_funding_8h()
        print(f"{len(funding)} Funding-Punkte geladen.")
    except Exception as exc:  # noqa: BLE001
        print(f"Funding nicht verfuegbar ({exc}) -> 0 (Bestaetigungen gelockert).")
        funding = []
    candles, flow = build_series(raw, funding)

    results = []
    for n, k in GRID:
        t0 = time.time()
        sigs = run_backtest(candles, flow, n, k)
        sc = score(sigs)
        results.append((n, k, sigs, sc))
        print(f"n={n} k={k}: Recall {sc['recall']:.0%}, Praezision {sc['precision']:.0%}, "
              f"{len(sigs)} Signale ({time.time()-t0:.0f}s)")

    best = max(results, key=lambda r: (r[3]["recall"], r[3]["precision"]))
    n, k, sigs, sc = best

    lines = [
        "# Backtest-Bericht (E4b): Engine vs. Kaisers notierte Furkan-Trigger",
        "",
        f"Zeitraum: 01.09.2025-30.04.2026 (4h-Kerzen, {len(candles)} Stueck) · "
        f"Stand: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
        "",
        "Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; "
        "Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.",
        "",
        "## Parameter-Vergleich",
        "",
        "| pivot_n | k_atr | Recall (Kaisers Trigger getroffen) | Praezision (Engine-Signale nahe Kaisers Terminen) | Signale |",
        "|---|---|---|---|---|",
    ]
    for rn, rk, rsigs, rsc in results:
        mark = " **<-- beste**" if (rn, rk) == (n, k) else ""
        lines.append(f"| {rn} | {rk} | {rsc['recall']:.0%} | {rsc['precision']:.0%} | "
                     f"{len(rsigs)}{mark} |")
    lines += [
        "",
        f"## Beste Kombination: pivot_n={n}, k_atr={k}",
        "",
        f"- Kauf-Trigger getroffen: {len(sc['hit_k'])}/{len(KAUF_DATEN)} — "
        + ", ".join(d.strftime('%d.%m.%y') for d in sc["hit_k"]),
        f"- Kauf verpasst: " + (", ".join(d.strftime('%d.%m.%y') for d in sc["miss_k"]) or "—"),
        f"- Verkauf-Trigger getroffen: {len(sc['hit_v'])}/{len(VERKAUF_DATEN)} — "
        + ", ".join(d.strftime('%d.%m.%y') for d in sc["hit_v"]),
        f"- Verkauf verpasst: " + (", ".join(d.strftime('%d.%m.%y') for d in sc["miss_v"]) or "—"),
        f"- Engine-Signal-Tage gesamt: {len(sc['buy_days'])} Kauf / {len(sc['sell_days'])} Verkauf",
        "",
        "## Einschraenkungen",
        "",
        "- Open Interest: keine kostenlose Historie fuer den Zeitraum -> OI-Muster neutral.",
        "- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).",
        "- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.",
        "",
        f"Empfehlung: Engine-Standardwerte auf pivot_n={n}, k_atr={k} setzen, falls "
        "abweichend von (5, 3.0).",
    ]
    (ROOT / "BACKTEST.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nBericht geschrieben: BACKTEST.md — beste Kombination n={n}, k={k}, "
          f"Recall {sc['recall']:.0%}")


if __name__ == "__main__":
    main()
