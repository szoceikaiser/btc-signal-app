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
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import coinalyze
from main import _get_json, fetch_funding_8h
from strategy_core import Candle, FlowPoint, LADDER_TRANCHE, Position, evaluate

ROOT = Path(__file__).resolve().parent.parent
CANDLE_MS = 4 * 3600 * 1000
WARMUP_MS = int(datetime(2025, 8, 10, tzinfo=timezone.utc).timestamp() * 1000)
START_MS = int(datetime(2025, 9, 1, tzinfo=timezone.utc).timestamp() * 1000)
# Ende = JETZT (E9.9). Vorher war hier 2026-05-01 hart verdrahtet — gesetzt, als das
# Projekt startete, weil Kaisers Triggerliste im April endet. Folge: Mai/Juni/Juli 2026
# wurden nie simuliert, genau der Zeitraum, in dem die Live-Engine in TP2 haengen blieb.
# Die Recall-Bewertung endet weiter beim letzten notierten Trigger (siehe score()),
# die P&L-Simulation laeuft ueber das ganze Fenster.
END_MS = int(time.time() * 1000)

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
             "conditional_stop", "buy_ladder", "release_stale_rest", "trail_stop",
             "liq_exit")
_BASE = dict(bias_long=True, bias_short=True, pivot_n=5, k_atr=2.0,
             flush_entry="off", tp_ladder=True,
             trend_filter=False, strict_confirm=False, confluence=False,
             conditional_stop=False, buy_ladder=False, release_stale_rest=False,
             trail_stop=False, liq_exit="off")


def V(label, panel=False, **kw):
    cfg = dict(_BASE)
    cfg.update(kw)
    cfg["label"] = label
    cfg["panel"] = panel          # markiert die Variante, die das Chart-Panel zeigt (Live-Einstellung)
    return cfg


# E9.5: Mehrtages-Kaufleiter (Furkan kauft in Tranchen ueber mehrere Tage in die
# Schwaeche nach). Testet, ob wir mehr von Furkans Kauf-Tagen treffen (Recall Kauf) —
# und was es mit der Rendite macht.
#
# WICHTIG (Panel-Regel): panel=True markiert die Variante, die auf der Chart-Webseite
# angezeigt wird. Sie MUSS der echten Live-Einstellung entsprechen, sonst zeigt das
# Panel eine Rendite, die die Engine nie erzielt hat. Live = nur Long
# (site/data/config.json: bias_short=false) + Kaufleiter + Flush core + tp_ladder
# (Defaults in strategy_core.evaluate). Bei jeder Aenderung an config.json oder an den
# evaluate-Defaults muss dieses Flag mitwandern.
GRID = [
    V("nur Long (Basis)", bias_short=False),
    V("+Kaufleiter", bias_short=False, buy_ladder=True),
    V("+Flush core", bias_short=False, flush_entry="core"),
    V("LIVE: nur Long +Kaufleiter +Flush core",
      bias_short=False, flush_entry="core", buy_ladder=True),
    V("+Kaufleiter +Bed.Stop", bias_short=False, buy_ladder=True, conditional_stop=True),
    # E9.9: dieselbe Live-Kombination, aber mit Rest-Freigabe bei veralteter Struktur.
    # Frage an die Messung: kostet das Freigeben Rendite (Runner werden abgeschnitten)
    # oder bringt es welche (Engine wird nicht mehr blockiert und nimmt neue Setups)?
    V("LIVE +Rest-Freigabe", bias_short=False, flush_entry="core", buy_ladder=True,
      release_stale_rest=True),
    # E9.10 (Kaisers Furkan-Zitat "Stop ueber den Kauf ziehen, Kapital schuetzen"):
    # nachgezogener Stop statt Rest-Verkauf. Messfrage: bringt das die Treffer-
    # Verbesserung der Rest-Freigabe OHNE deren Rendite-Verlust, weil Runner am Leben
    # bleiben? Und die Kombination aus beidem als Gegenprobe.
    V("LIVE +Stop nachziehen", panel=True, bias_short=False, flush_entry="core",
      buy_ladder=True, trail_stop=True),
    V("LIVE +Stop nachziehen +Rest-Freigabe", bias_short=False, flush_entry="core",
      buy_ladder=True, trail_stop=True, release_stale_rest=True),
    # E9.11 (Kaisers Beobachtung): Teilverkaeufe an Liquidationszonen statt nur an
    # Fib-Extensions. Basis ist die empfohlene Live-Einstellung inkl. Stop-Nachziehen,
    # damit der Vergleich das echte Delta des Liquidations-Ausstiegs zeigt.
    V("LIVE +Stop +Liq-Kaskade", bias_short=False, flush_entry="core", buy_ladder=True,
      trail_stop=True, liq_exit="spike"),
    V("LIVE +Stop +Liq-Zonen", bias_short=False, flush_entry="core", buy_ladder=True,
      trail_stop=True, liq_exit="zone"),
    V("LIVE +Stop +Liq beides", bias_short=False, flush_entry="core", buy_ladder=True,
      trail_stop=True, liq_exit="both"),
    # Kapital-Reserve (Furkan-Update Juli 2026: "Pulver haben zum Nachschiessen, klaren
    # Plan haben, ab welchem Niveau man wie viel Prozent seines Kapitals reinschiesst").
    # Gleiche Signale wie die Live-Variante — nur das Geld wird anders eingeteilt.
    V("LIVE +Stop, 60 % Einsatz (40 % Reserve)", bias_short=False, flush_entry="core",
      buy_ladder=True, trail_stop=True, deploy_pct=0.6),
    V("LIVE +Stop, 50 % Einsatz (50 % Reserve)", bias_short=False, flush_entry="core",
      buy_ladder=True, trail_stop=True, deploy_pct=0.5),
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


def run_backtest(candles, flow, cfg: dict, start_ms: int = START_MS) -> list[dict]:
    """Signale ab `start_ms` (Voll-Daten-Fenster). Vorher nur Warmup (kein Signal)."""
    params = {k: cfg[k] for k in EVAL_KEYS if k in cfg}
    pos = Position()
    signals = []
    for i in range(len(candles)):
        if candles[i].ts < start_ms:
            pos.last_signal_ts = candles[i].ts                 # Warmup ohne Signale
            continue
        for s in evaluate(candles[:i + 1], flow[:i + 1], pos, **params):
            signals.append(s.to_dict())
    return signals


def to_date(ts_ms: int) -> date:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date()


def score(signals: list[dict], tol_days: int = 1, start_ms: int = START_MS) -> dict:
    # Nur Furkans Trigger IM Voll-Daten-Fenster bewerten (ab start_ms) — sonst zaehlten
    # wir Tage, an denen die Engine mangels Daten gar nicht handeln konnte (E9.6).
    start_d = to_date(start_ms)
    kauf = [d for d in (date.fromisoformat(x) for x in KAUF_DATEN) if d >= start_d]
    verkauf = [d for d in (date.fromisoformat(x) for x in VERKAUF_DATEN) if d >= start_d]
    # Recall/Praezision nur bis zum letzten notierten Trigger (+Toleranz) bewerten:
    # danach gibt es keinen Maszstab mehr (Kaisers Notizen enden im April 2026), sonst
    # zaehlte jedes spaetere Engine-Signal automatisch als Fehltreffer. Die P&L-
    # Simulation laeuft trotzdem ueber das ganze Fenster (E9.9).
    eval_end = (max(kauf + verkauf) + timedelta(days=tol_days)) if (kauf or verkauf) else None

    def _days(types):
        ds = {to_date(s["ts"]) for s in signals if s["type"] in types}
        return sorted(d for d in ds if eval_end is None or d <= eval_end)
    buy_days, sell_days = _days(BUY_TYPES), _days(SELL_TYPES)

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
        "recall": (len(hit_k) + len(hit_v)) / (len(kauf) + len(verkauf)) if (kauf or verkauf) else 0.0,
        "precision": len(prec_days) / total_days if total_days else 0.0,
        "buy_days": buy_days, "sell_days": sell_days,
        "n_kauf": len(kauf), "n_verkauf": len(verkauf),   # Trigger IM Fenster
        "eval_end": eval_end,                            # Ende der Recall-Bewertung
    }


def simulate(signals: list[dict], candles, fee: float = 0.001,
             start_capital: float = 10000.0, start_ms: int | None = None,
             deploy_pct: float = 1.0) -> dict:
    """Tranchen-genaue P&L-Simulation der Signale.

    Annahmen (dokumentiert): kein Hebel; Kauf-Tranchen als %-Anteil des beim
    Ladder-Start verfuegbaren Kapitals (aus tranche_pct des Signals); Teilverkaeufe
    40 %/40 %/Rest der vollen Position; 0,1 % Gebuehr je Order; Shorts nominal
    ohne Funding-Kosten. Ergebnis inkl. Buy&Hold-Vergleich ueber denselben Zeitraum.

    `deploy_pct` (Furkan-Update Juli 2026, "Pulver behalten"): Anteil des verfuegbaren
    Kapitals, der je Position hoechstens eingesetzt wird. 1.0 = bisheriges Verhalten
    (bis zu 100 % investiert, keine Reserve). 0.6 = 40 % bleiben liegen.
    Der Effekt ist NICHT nur eine Verkleinerung: heute frisst die zuerst gefeuerte
    Tranche das Kapital auf, sodass die SPAETEREN, tieferen Stufen (Kaufleiter, 0.786,
    Dip-Nachkauf) leer ausgehen — genau die mit dem besten Preis. Mit Reserve landet
    mehr Kapital weiter unten. Deshalb zusaetzlich der maximale Rueckgang (Drawdown)
    im Bericht: eine Reserve kauft Sicherheit, das muss sichtbar sein.
    """
    cash, units, peak_units, l_avg = start_capital, 0.0, 0.0, 0.0
    s_units, s_peak, s_avg = 0.0, 0.0, 0.0            # Short-Seite
    alloc = 0.0
    trades_closed = wins = 0
    long_profit = short_profit = 0.0                 # Gewinn/Verlust je Richtung (E9.6)
    long_trades = long_wins = short_trades = short_wins = 0
    equity = []

    def equity_now(price):
        return cash + units * price + s_units * (s_avg - price)

    for s in signals:
        p, t = s["price"], s["type"]
        if t in ("KAUF_1", "KAUF_2", "NACHKAUF"):
            if units == 0.0:
                alloc, peak_units, l_avg = cash * deploy_pct, 0.0, 0.0
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
                long_profit += pnl
                long_trades += 1
                long_wins += 1 if pnl > 0 else 0
                cash += proceeds
                units -= sell
        elif t in ("SHORT_1", "SHORT_2", "SHORT_NACHLEGEN"):
            if s_units == 0.0:
                alloc, s_peak, s_avg = cash * deploy_pct, 0.0, 0.0
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
                short_profit += pnl
                short_trades += 1
                short_wins += 1 if pnl > 0 else 0
                cash += pnl
                s_units -= cover
        equity.append({"ts": s["ts"], "equity": round(equity_now(p), 2)})

    last_price = candles[-1].close
    end_equity = equity_now(last_price)
    # Maximaler Rueckgang vom jeweiligen Hoch (gemessen an den Signalzeitpunkten +
    # Endstand). Das ist die Kennzahl, auf die eine Kapital-Reserve einzahlt.
    peak_eq, max_dd = start_capital, 0.0
    for e in [x["equity"] for x in equity] + [end_equity]:
        peak_eq = max(peak_eq, e)
        max_dd = min(max_dd, e / peak_eq - 1.0)
    hs = start_ms if start_ms is not None else START_MS
    hold_start = next(c for c in candles if c.ts >= hs).close
    return {
        "start": start_capital,
        "ende": round(end_equity, 2),
        "rendite_pct": round((end_equity / start_capital - 1) * 100, 2),
        "buyhold_pct": round((last_price / hold_start - 1) * 100, 2),
        "trades": trades_closed, "gewinn_trades": wins,
        "long_profit": round(long_profit, 2), "long_trades": long_trades, "long_wins": long_wins,
        "short_profit": round(short_profit, 2), "short_trades": short_trades, "short_wins": short_wins,
        "fee_pct": fee * 100, "equity": equity,
        "deploy_pct": round(deploy_pct * 100), "max_drawdown_pct": round(max_dd * 100, 2),
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

    # E9.6 (Kaisers Vorgabe): Backtest NUR ueber das Voll-Daten-Fenster — ab der ersten
    # OI-Kerze. Vorher fehlt das OI -> dort keine Trigger (sonst schlechte Ausgangslage).
    eff_start = max(START_MS, min(oi_map)) if oi_map else START_MS
    print(f"Voll-Daten-Fenster ab {to_date(eff_start).strftime('%d.%m.%Y')} "
          f"(OI vorhanden: {'ja' if oi_map else 'nein'}).")

    results = []
    for cfg in GRID:
        t0 = time.time()
        sigs = run_backtest(candles, flow, cfg, start_ms=eff_start)
        sc = score(sigs, start_ms=eff_start)
        p = simulate(sigs, candles, start_ms=eff_start,
                     deploy_pct=cfg.get("deploy_pct", 1.0))
        results.append((cfg, sigs, sc, p))
        print(f"{cfg['label']}: Recall {sc['recall']:.0%}, "
              f"Praezision {sc['precision']:.0%}, Rendite {p['rendite_pct']:+.1f} %, "
              f"Long {p['long_profit']:+.0f}€/Short {p['short_profit']:+.0f}€, "
              f"{len(sigs)} Signale ({time.time()-t0:.0f}s)")

    # Auswahl: primaer Rendite (das Geld-Maß), dann Recall, dann Praezision
    best = max(results, key=lambda r: (r[3]["rendite_pct"], r[2]["recall"], r[2]["precision"]))
    best_cfg, sigs, sc, pnl = best

    # Panel-Variante = die als panel=True markierte (Live-Einstellung), damit die
    # Chart-Seite zeigt, was die Engine WIRKLICH tut — nicht die beste Fantasie-Variante.
    panel_r = next((r for r in results if r[0].get("panel")), best)
    panel_cfg, _psigs, panel_sc, panel_pnl = panel_r

    win = f"{to_date(eff_start).strftime('%d.%m.%Y')}-{to_date(END_MS).strftime('%d.%m.%Y')}"
    lines = [
        "# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger",
        "",
        f"**Voll-Daten-Fenster: {win}** (nur wo alle Order-Flow-Daten inkl. echtem OI "
        f"vorliegen — E9.6, Kaisers Vorgabe) · {len(candles)} 4h-Kerzen geladen · "
        f"Stand: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
        "",
        "Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; "
        "Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.",
        "",
        (f"**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur "
         f"bis {sc['eval_end'].strftime('%d.%m.%Y')} bewertet (danach endet Kaisers "
         f"Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das "
         f"komplette Fenster bis {to_date(END_MS).strftime('%d.%m.%Y')}."
         if sc.get("eval_end") else ""),
        "",
        "## Parameter-Vergleich",
        "",
        "Alle n=5. Rendite = Gesamt-Simulation. **max. Rueckgang** = groesster Einbruch vom "
        "jeweiligen Hoch (Drawdown) — je naeher an 0, desto ruhiger der Verlauf. "
        "**Einsatz** = wie viel des Kapitals je Position hoechstens investiert wird "
        "(100 % = keine Reserve, 60 % = 40 % Pulver bleibt trocken; Furkan-Update Juli 2026). "
        "Recall = Aehnlichkeit zu Furkans Terminen IM Fenster, KEIN Gewinn.",
        "",
        "| Variante | Recall | Praez. | Rendite | max. Rueckgang | Einsatz | Signale |",
        "|---|---|---|---|---|---|---|",
    ]
    for rcfg, rsigs, rsc, rp in results:
        mark = " **<-- beste**" if rcfg is best_cfg else ""
        lines.append(f"| {rcfg['label']} | {rsc['recall']:.0%} | {rsc['precision']:.0%} | "
                     f"{rp['rendite_pct']:+.1f} % | {rp['max_drawdown_pct']:.1f} % | "
                     f"{rp['deploy_pct']} % | {len(rsigs)}{mark} |")
    lines += [
        "",
        f"## Beste Kombination (nach Rendite): {best_cfg['label']}",
        "",
        f"- Kauf-Trigger getroffen: {len(sc['hit_k'])}/{sc['n_kauf']} (im Fenster) — "
        + ", ".join(d.strftime('%d.%m.%y') for d in sc["hit_k"]),
        f"- Kauf verpasst: " + (", ".join(d.strftime('%d.%m.%y') for d in sc["miss_k"]) or "—"),
        f"- Verkauf-Trigger getroffen: {len(sc['hit_v'])}/{sc['n_verkauf']} (im Fenster) — "
        + ", ".join(d.strftime('%d.%m.%y') for d in sc["hit_v"]),
        f"- Verkauf verpasst: " + (", ".join(d.strftime('%d.%m.%y') for d in sc["miss_v"]) or "—"),
        "",
        "## P&L-Simulation (beste Kombination) — getrennt nach Richtung",
        "",
        f"Start 10.000 € -> **{pnl['ende']:,.0f} €** ({pnl['rendite_pct']:+.1f} %) · "
        f"Buy&Hold im Fenster: {pnl['buyhold_pct']:+.1f} % · Gebuehr {pnl['fee_pct']:.1f} %/Order, kein Hebel.",
        "",
        f"- **LONG-Trades:** {pnl['long_profit']:+,.0f} € · {pnl['long_trades']} Abschluesse, "
        f"{pnl['long_wins']} im Gewinn",
        f"- **SHORT-Trades:** {pnl['short_profit']:+,.0f} € · {pnl['short_trades']} Abschluesse, "
        f"{pnl['short_wins']} im Gewinn",
        "",
        "WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, "
        "KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.",
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

    # JSON fuers Chart-Panel — Analyse-Variante (Long+Short), P&L getrennt nach Richtung.
    panel = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "zeitraum": win,
        "variante": panel_cfg["label"],
        "params": {k: panel_cfg[k] for k in EVAL_KEYS},
        "recall_kauf": f"{len(panel_sc['hit_k'])}/{panel_sc['n_kauf']}",
        "recall_verkauf": f"{len(panel_sc['hit_v'])}/{panel_sc['n_verkauf']}",
        "recall_pct": round(panel_sc["recall"] * 100),
        "precision_pct": round(panel_sc["precision"] * 100),
        "pnl": {kk: vv for kk, vv in panel_pnl.items() if kk != "equity"},
    }
    (ROOT / "site" / "data" / "backtest.json").write_text(
        json.dumps(panel, indent=1), encoding="utf-8")

    # Alle Long- UND Short-Signale der Analyse-Variante fuer den Chart (E9.6, Kaiser:
    # alle Einstiege/Ausstiege getrennt Long/Short zeichnen). Nur im Voll-Daten-Fenster.
    (ROOT / "site" / "data" / "backtest_signals.json").write_text(
        json.dumps({"generated_at": panel["generated_at"], "variante": panel_cfg["label"],
                    "fenster": win, "signals": _psigs}, indent=1), encoding="utf-8")
    print(f"\nGeschrieben: BACKTEST.md (beste {best_cfg['label']} {pnl['rendite_pct']:+.1f} %) "
          f"+ backtest.json + backtest_signals.json ({len(_psigs)} Signale, "
          f"{panel_cfg['label']}: Long {panel_pnl['long_profit']:+.0f}€ / "
          f"Short {panel_pnl['short_profit']:+.0f}€)")


if __name__ == "__main__":
    main()
