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
from strategy_core import Candle, FlowPoint, LADDER_TRANCHE, Position, evaluate

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
             "SHORT_TP_LADDER", "SHORT_TP_1", "SHORT_TP_2", "SHORT_COVER_REST", "SHORT_STOPLOSS"}
# Verkauf-Handlung = Long reduzieren/schliessen ODER Short eroeffnen/aufstocken
SELL_TYPES = {"TEILVERKAUF_LADDER", "TEILVERKAUF_1", "TEILVERKAUF_2", "VERKAUF_REST", "STOPLOSS",
              "SHORT_1", "SHORT_2", "SHORT_NACHLEGEN"}

# Grid: k_atr=2.0 fix, flush='off' und tp_ladder=True (per E8.1b/E8.2 als beste
# bestaetigt). Neue Dimension: Richtung. Furkan hat in diesem Zeitraum laut Kaisers
# Ordern fast ausschliesslich LONG gehandelt (seine "Verkaeufe" waren Long-Schliessungen,
# keine Shorts) — sein uebergeordneter Bias kam aus Makro (Transkript 16:03-19:41).
# Darum vergleichen wir "ls" (Long+Short, bisher) gegen "long" (nur Long, bias_short=False),
# um zu messen, ob die von Furkan nie gehandelten Shorts uns Rendite kosten.
DIRECTIONS = {"ls": (True, True), "long": (True, False)}
GRID = [(n, 2.0, "off", True, d)
        for n in (3, 4, 5, 6) for d in ("ls", "long")]


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


def run_backtest(candles, flow, pivot_n: int, k_atr: float,
                 flush_entry: str = "off", tp_ladder: bool = True,
                 bias_long: bool = True, bias_short: bool = True) -> list[dict]:
    pos = Position()
    signals = []
    for i in range(len(candles)):
        if candles[i].ts < START_MS:
            pos.last_signal_ts = candles[i].ts                 # Warmup ohne Signale
            continue
        for s in evaluate(candles[:i + 1], flow[:i + 1], pos,
                          bias_long=bias_long, bias_short=bias_short,
                          pivot_n=pivot_n, k_atr=k_atr, flush_entry=flush_entry,
                          tp_ladder=tp_ladder):
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


def simulate(signals: list[dict], candles, fee: float = 0.001,
             start_capital: float = 10000.0) -> dict:
    """Tranchen-genaue P&L-Simulation der Signale.

    Annahmen (dokumentiert): kein Hebel; Kauf-Tranchen als %-Anteil des beim
    Ladder-Start verfuegbaren Kapitals (aus tranche_pct des Signals); Teilverkaeufe
    40 %/40 %/Rest der vollen Position; 0,1 % Gebuehr je Order; Shorts nominal
    ohne Funding-Kosten. Ergebnis inkl. Buy&Hold-Vergleich ueber denselben Zeitraum.
    """
    cash, units, peak_units, l_avg = start_capital, 0.0, 0.0, 0.0
    s_units, s_peak, s_avg = 0.0, 0.0, 0.0            # Short-Seite
    alloc = 0.0
    trades_closed = wins = 0
    equity = []

    def equity_now(price):
        return cash + units * price + s_units * (s_avg - price)

    for s in signals:
        p, t = s["price"], s["type"]
        if t in ("KAUF_1", "KAUF_2", "NACHKAUF"):
            if units == 0.0:
                alloc, peak_units, l_avg = cash, 0.0, 0.0
            spend = min(cash, alloc * s["tranche_pct"] / 100.0)
            new_u = spend * (1 - fee) / p
            l_avg = (l_avg * units + spend) / (units + new_u) if (units + new_u) else 0.0
            units += new_u
            peak_units = max(peak_units, units)
            cash -= spend
        elif t in ("TEILVERKAUF_LADDER", "TEILVERKAUF_1", "TEILVERKAUF_2", "VERKAUF_REST", "STOPLOSS"):
            if t in ("VERKAUF_REST", "STOPLOSS"):
                sell = units
            elif t == "TEILVERKAUF_LADDER":
                sell = min(units, LADDER_TRANCHE / 100.0 * peak_units)
            else:
                sell = min(units, 0.4 * peak_units)
            if sell > 0:
                proceeds = sell * p * (1 - fee)
                pnl = proceeds - sell * l_avg
                trades_closed += 1
                wins += 1 if pnl > 0 else 0
                cash += proceeds
                units -= sell
        elif t in ("SHORT_1", "SHORT_2", "SHORT_NACHLEGEN"):
            if s_units == 0.0:
                alloc, s_peak, s_avg = cash, 0.0, 0.0
            nominal = min(cash, alloc * s["tranche_pct"] / 100.0)
            new_units = nominal / p
            s_avg = (s_avg * s_units + p * new_units) / (s_units + new_units)
            s_units += new_units
            s_peak = max(s_peak, s_units)
            cash -= nominal * fee                      # Eroeffnungsgebuehr
        elif t in ("SHORT_TP_LADDER", "SHORT_TP_1", "SHORT_TP_2", "SHORT_COVER_REST", "SHORT_STOPLOSS"):
            if t in ("SHORT_COVER_REST", "SHORT_STOPLOSS"):
                cover = s_units
            elif t == "SHORT_TP_LADDER":
                cover = min(s_units, LADDER_TRANCHE / 100.0 * s_peak)
            else:
                cover = min(s_units, 0.4 * s_peak)
            if cover > 0:
                pnl = cover * (s_avg - p) - cover * p * fee
                trades_closed += 1
                wins += 1 if pnl > 0 else 0
                cash += pnl
                s_units -= cover
        equity.append({"ts": s["ts"], "equity": round(equity_now(p), 2)})

    last_price = candles[-1].close
    end_equity = equity_now(last_price)
    hold_start = next(c for c in candles if c.ts >= START_MS).close
    return {
        "start": start_capital,
        "ende": round(end_equity, 2),
        "rendite_pct": round((end_equity / start_capital - 1) * 100, 2),
        "buyhold_pct": round((last_price / hold_start - 1) * 100, 2),
        "trades": trades_closed, "gewinn_trades": wins,
        "fee_pct": fee * 100, "equity": equity,
        "offene_position": round(units * last_price + s_units * (s_avg - last_price), 2),
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
    for n, k, mode, ladder, direction in GRID:
        t0 = time.time()
        bl, bs = DIRECTIONS[direction]
        sigs = run_backtest(candles, flow, n, k, flush_entry=mode, tp_ladder=ladder,
                            bias_long=bl, bias_short=bs)
        sc = score(sigs)
        p = simulate(sigs, candles)
        results.append((n, k, mode, ladder, direction, sigs, sc, p))
        print(f"n={n} k={k} flush={mode} ladder={ladder} dir={direction}: "
              f"Recall {sc['recall']:.0%}, Praezision {sc['precision']:.0%}, "
              f"Rendite {p['rendite_pct']:+.1f} %, {len(sigs)} Signale ({time.time()-t0:.0f}s)")

    # Auswahl: primaer Rendite (das Geld-Maß), dann Recall, dann Praezision
    best = max(results, key=lambda r: (r[7]["rendite_pct"], r[6]["recall"], r[6]["precision"]))
    n, k, mode, ladder, direction, sigs, sc, pnl = best

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
        "(Leiter = gestaffelte Zwischen-Teilgewinne Ext 0.8/0.9, E8.2. Richtung: "
        "ls = Long+Short wie bisher, long = nur Long/bias_short=false. Furkan handelte "
        "in diesem Zeitraum fast nur Long. Sortiert nach Rendite = das Geld-Maß.)",
        "",
        "| pivot_n | Richtung | Leiter | Recall | Praezision | Rendite | Signale |",
        "|---|---|---|---|---|---|---|",
    ]
    for rn, rk, rm, rl, rd, rsigs, rsc, rp in results:
        mark = " **<-- beste**" if (rn, rk, rm, rl, rd) == (n, k, mode, ladder, direction) else ""
        lines.append(f"| {rn} | {rd} | {'an' if rl else 'aus'} | {rsc['recall']:.0%} | "
                     f"{rsc['precision']:.0%} | {rp['rendite_pct']:+.1f} % | {len(rsigs)}{mark} |")
    lines += [
        "",
        f"## Beste Kombination (nach Rendite): pivot_n={n}, Richtung={direction}, "
        f"Leiter={'an' if ladder else 'aus'}, flush={mode}, k_atr={k}",
        "",
        f"- Kauf-Trigger getroffen: {len(sc['hit_k'])}/{len(KAUF_DATEN)} — "
        + ", ".join(d.strftime('%d.%m.%y') for d in sc["hit_k"]),
        f"- Kauf verpasst: " + (", ".join(d.strftime('%d.%m.%y') for d in sc["miss_k"]) or "—"),
        f"- Verkauf-Trigger getroffen: {len(sc['hit_v'])}/{len(VERKAUF_DATEN)} — "
        + ", ".join(d.strftime('%d.%m.%y') for d in sc["hit_v"]),
        f"- Verkauf verpasst: " + (", ".join(d.strftime('%d.%m.%y') for d in sc["miss_v"]) or "—"),
        f"- Engine-Signal-Tage gesamt: {len(sc['buy_days'])} Kauf / {len(sc['sell_days'])} Verkauf",
        "",
        "## P&L-Simulation (beste Kombination)",
        "",
        f"Start 10.000 € -> **{pnl['ende']:,.0f} €** ({pnl['rendite_pct']:+.1f} %) · "
        f"Buy&Hold im Zeitraum: {pnl['buyhold_pct']:+.1f} % · "
        f"{pnl['trades']} Verkaufs-Vorgaenge, davon {pnl['gewinn_trades']} im Gewinn · "
        f"Gebuehr {pnl['fee_pct']:.1f} % je Order, kein Hebel.",
        "",
        "WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, "
        "KEIN Gewinn. Der Gewinn steht nur in dieser P&L-Zeile.",
        "",
        "## Einschraenkungen",
        "",
        "- Open Interest: keine kostenlose Historie fuer den Zeitraum -> OI-Muster neutral.",
        "- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).",
        "- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.",
        "",
        f"Empfehlung: pivot_n={n}, k_atr={k}, flush_entry='{mode}', tp_ladder={ladder}. "
        f"Richtung={direction}: 'long' heisst bias_short=false in site/data/state.json "
        "(kein Code-Default — der Richtungs-Bias soll dynamisch aus Makro kommen, E8.5). "
        "Schneidet 'long' hier klar besser ab, ist das die Bestaetigung von Furkans "
        "Long-Bias in diesem Zeitraum.",
    ]
    (ROOT / "BACKTEST.md").write_text("\n".join(lines), encoding="utf-8")

    # JSON fuer das Panel auf der Chart-Webseite
    panel = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "zeitraum": "01.09.2025 - 30.04.2026",
        "params": {"pivot_n": n, "k_atr": k, "flush_entry": mode, "tp_ladder": ladder,
                   "richtung": direction},
        "recall_kauf": f"{len(sc['hit_k'])}/{len(KAUF_DATEN)}",
        "recall_verkauf": f"{len(sc['hit_v'])}/{len(VERKAUF_DATEN)}",
        "recall_pct": round(sc["recall"] * 100),
        "precision_pct": round(sc["precision"] * 100),
        "pnl": {kk: vv for kk, vv in pnl.items() if kk != "equity"},
    }
    (ROOT / "site" / "data" / "backtest.json").write_text(
        json.dumps(panel, indent=1), encoding="utf-8")
    print(f"\nBericht geschrieben: BACKTEST.md + site/data/backtest.json — "
          f"n={n}, k={k}, Recall {sc['recall']:.0%}, Rendite {pnl['rendite_pct']:+.1f} %")


if __name__ == "__main__":
    main()
