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
import os
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import coinalyze
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

# Grid (E8.5): n=5, k=2.0, flush='off', tp_ladder=True fix (kalibriert). Getestet werden
# die drei Furkan-Filter fuer bessere Long-Einstiege — einzeln UND kombiniert, damit die
# Wirkung jedes Hebels sichtbar wird. Referenz: alte Long+Short-Variante und nur-Long-Basis.
# Parameter, die evaluate() versteht (der Rest der Config sind nur Labels):
EVAL_KEYS = ("bias_long", "bias_short", "pivot_n", "k_atr", "flush_entry",
             "tp_ladder", "trend_filter", "strict_confirm", "confluence",
             "conditional_stop")
_BASE = dict(bias_long=True, bias_short=True, pivot_n=5, k_atr=2.0,
             flush_entry="off", tp_ladder=True,
             trend_filter=False, strict_confirm=False, confluence=False,
             conditional_stop=False)


def V(label, panel=False, **kw):
    cfg = dict(_BASE)
    cfg.update(kw)
    cfg["label"] = label
    cfg["panel"] = panel          # markiert die Variante, die das Chart-Panel zeigt (Live-Einstellung)
    return cfg


# E9.3: bedingter Stop (bei Verlust nachkaufen statt pauschal stoppen, solange der
# Order-Flow den Trend bestaetigt) — allein und als Absicherung fuer den aggressiven
# Flush. "nur Long (Basis)" ist die empfohlene Live-Einstellung und speist das Chart-Panel.
GRID = [
    V("nur Long (Basis)", panel=True, bias_short=False),
    V("+Flush core", bias_short=False, flush_entry="core"),
    V("+Bedingter Stop", bias_short=False, conditional_stop=True),
    V("+Flush core +Bed.Stop", bias_short=False, flush_entry="core", conditional_stop=True),
    V("+Bed.Stop +Streng", bias_short=False, conditional_stop=True, strict_confirm=True),
    V("Long+Short (Ref)"),
]


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


def build_series(raw: list, funding: list[tuple[int, float]],
                 oi_map: dict | None = None, liq_map: dict | None = None):
    """OI aus oi_map (Coinalyze, E9.1) je Kerze; ohne oi_map bleibt OI konstant (neutral).
    liq_map liefert (long_liq, short_liq) je Kerzen-Open-ts."""
    candles, flow, spot_cvd = [], [], 0.0
    oi_pairs = sorted(oi_map.items()) if oi_map else []
    first_oi = oi_pairs[0][1] if oi_pairs else 1.0

    def latest_leq(pairs, ts, default=0.0):
        val = default
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
        oi_val = latest_leq(oi_pairs, ts, first_oi) if oi_pairs else 1.0
        long_liq, short_liq = (liq_map.get(ts, (0.0, 0.0)) if liq_map else (0.0, 0.0))
        flow.append(FlowPoint(ts, spot_cvd, 0.0, oi_val,
                              latest_leq(funding, ts + CANDLE_MS), long_liq, short_liq))
    return candles, flow


def run_backtest(candles, flow, cfg: dict) -> list[dict]:
    params = {k: cfg[k] for k in EVAL_KEYS if k in cfg}
    pos = Position()
    signals = []
    for i in range(len(candles)):
        if candles[i].ts < START_MS:
            pos.last_signal_ts = candles[i].ts                 # Warmup ohne Signale
            continue
        for s in evaluate(candles[:i + 1], flow[:i + 1], pos, **params):
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

    # E9.1: echtes historisches OI + Liquidationen (Coinalyze) fuer den Zeitraum ->
    # Muster 4 (Kapitulation) wird im Backtest aktiv. Ohne Key: OI konstant (wie bisher).
    oi_map, liq_map = {}, {}
    api_key = os.environ.get("COINALYZE_API_KEY", "")
    if api_key:
        try:
            oi_map = coinalyze.oi_by_ts(api_key, frm=WARMUP_MS // 1000, to=END_MS // 1000)
            liq_map = coinalyze.liquidations_by_ts(api_key, frm=WARMUP_MS // 1000,
                                                   to=END_MS // 1000)
            print(f"Coinalyze: {len(oi_map)} OI-Punkte, {len(liq_map)} Liq-Punkte "
                  f"(4h-Historie reicht ggf. nicht bis Sep'25 zurueck -> aeltere Kerzen OI neutral).")
        except Exception as exc:  # noqa: BLE001
            print(f"Coinalyze nicht verfuegbar ({exc}) -> OI konstant/neutral.")

    candles, flow = build_series(raw, funding, oi_map, liq_map)

    results = []
    for cfg in GRID:
        t0 = time.time()
        sigs = run_backtest(candles, flow, cfg)
        sc = score(sigs)
        p = simulate(sigs, candles)
        results.append((cfg, sigs, sc, p))
        print(f"{cfg['label']}: Recall {sc['recall']:.0%}, "
              f"Praezision {sc['precision']:.0%}, Rendite {p['rendite_pct']:+.1f} %, "
              f"{len(sigs)} Signale ({time.time()-t0:.0f}s)")

    # Auswahl: primaer Rendite (das Geld-Maß), dann Recall, dann Praezision
    best = max(results, key=lambda r: (r[3]["rendite_pct"], r[2]["recall"], r[2]["precision"]))
    best_cfg, sigs, sc, pnl = best

    # Panel-Variante = die als panel=True markierte (Live-Einstellung), damit die
    # Chart-Seite zeigt, was die Engine WIRKLICH tut — nicht die beste Fantasie-Variante.
    panel_r = next((r for r in results if r[0].get("panel")), best)
    panel_cfg, _psigs, panel_sc, panel_pnl = panel_r

    lines = [
        "# Backtest-Bericht (E4b): Engine vs. Kaisers notierte Furkan-Trigger",
        "",
        f"Zeitraum: 01.09.2025-30.04.2026 (4h-Kerzen, {len(candles)} Stueck) · "
        f"Stand: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
        "",
        "Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; "
        "Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.",
        "",
        "## Parameter-Vergleich (E8.5: bessere Long-Einstiege, alle n=5 nur-Long)",
        "",
        "Drei Furkan-Filter, einzeln und kombiniert (Furkans Schritt 1 = Richtung aus Makro,"
        " dann Konfluenz-Bestaetigung): **Trendfilter** = keine Longs gegen den 1D-Trend"
        " (Preis vs. Tages-EMA). **Strenge Bestaetigung** = KAUF 2 nur wenn Spot-CVD dreht"
        " UND Funding stimmt (statt eines von beiden). **Konfluenz 4h/1D** = Einstieg nur,"
        " wenn die 4h-Zone in der 1D-Retracement-Zone liegt. Sortiert nach Rendite.",
        "",
        "| Variante | Recall | Praezision | Rendite | Signale |",
        "|---|---|---|---|---|",
    ]
    for rcfg, rsigs, rsc, rp in results:
        mark = " **<-- beste**" if rcfg is best_cfg else ""
        lines.append(f"| {rcfg['label']} | {rsc['recall']:.0%} | {rsc['precision']:.0%} | "
                     f"{rp['rendite_pct']:+.1f} % | {len(rsigs)}{mark} |")
    lines += [
        "",
        f"## Beste Kombination (nach Rendite): {best_cfg['label']} "
        f"(pivot_n={best_cfg['pivot_n']}, nur Long={not best_cfg['bias_short']}, "
        f"Trendfilter={best_cfg['trend_filter']}, strenge Best.={best_cfg['strict_confirm']}, "
        f"Konfluenz={best_cfg['confluence']})",
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
        (f"- Open Interest + Liquidationen: **echt von Coinalyze** — {len(oi_map)} OI-Punkte, "
         f"{len(liq_map)} Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv."
         if oi_map else
         "- Open Interest: keine Coinalyze-Daten (Key/Reichweite?) -> OI konstant/neutral, Muster 4 inaktiv."),
        (f"  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; "
         f"aeltere Kerzen dann OI neutral.)" if oi_map else ""),
        "- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).",
        "- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.",
        "",
        f"Empfehlung: Variante '{best_cfg['label']}' schneidet nach Rendite am besten ab. "
        "ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch "
        "rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger "
        "Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in "
        "strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.",
    ]
    (ROOT / "BACKTEST.md").write_text("\n".join(lines), encoding="utf-8")

    # JSON fuer das Panel auf der Chart-Webseite — zeigt die LIVE-Einstellung
    # (panel=True), nicht die beste Fantasie-Variante. Ehrlich zu den echten Signalen.
    panel = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "zeitraum": "01.09.2025 - 30.04.2026",
        "variante": panel_cfg["label"],
        "params": {k: panel_cfg[k] for k in EVAL_KEYS},
        "recall_kauf": f"{len(panel_sc['hit_k'])}/{len(KAUF_DATEN)}",
        "recall_verkauf": f"{len(panel_sc['hit_v'])}/{len(VERKAUF_DATEN)}",
        "recall_pct": round(panel_sc["recall"] * 100),
        "precision_pct": round(panel_sc["precision"] * 100),
        "pnl": {kk: vv for kk, vv in panel_pnl.items() if kk != "equity"},
    }
    (ROOT / "site" / "data" / "backtest.json").write_text(
        json.dumps(panel, indent=1), encoding="utf-8")
    print(f"\nBericht geschrieben: BACKTEST.md (beste: {best_cfg['label']}, "
          f"Rendite {pnl['rendite_pct']:+.1f} %) + backtest.json "
          f"(Panel-Variante: {panel_cfg['label']}, Rendite {panel_pnl['rendite_pct']:+.1f} %)")


if __name__ == "__main__":
    main()
