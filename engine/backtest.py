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
             "liq_exit", "high_exit", "liq_entry",
             "block_unhealthy", "confirm_t1", "cooldown_h", "min_stop_pct",
             "no_flip", "freeze_targets")
_BASE = dict(bias_long=True, bias_short=True, pivot_n=5, k_atr=2.0,
             flush_entry="off", tp_ladder=True,
             trend_filter=False, strict_confirm=False, confluence=False,
             conditional_stop=False, buy_ladder=False, release_stale_rest=False,
             trail_stop=False, liq_exit="off", high_exit="off", liq_entry="off",
             block_unhealthy=False, confirm_t1=False, cooldown_h=0.0, min_stop_pct=0.0,
             no_flip=False, freeze_targets=False)


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
    V("LIVE +Stop nachziehen", bias_short=False, flush_entry="core",
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
    # Kaisers Vergleichsvariante: seine Live-Einstellung, aber OHNE den aggressiven
    # Flush-Einstieg (der verdoppelt Rendite UND Rueckgang). Fuer die Monatsuebersicht.
    # Vergleichsspalte der Monatsuebersicht. MUSS mit der panel-Zeile identisch sein bis
    # auf flush_entry="off" — sonst vergleicht die Webseite zwei verschiedene Dinge und
    # der Unterschied waere nicht mehr "der Flush", sondern ein Sammelsurium.
    V("MEINE Einstellung ohne Flush", bias_short=False, flush_entry="off",
      buy_ladder=True, trail_stop=True, min_stop_pct=0.02, liq_entry="boost",
      high_exit="on"),
    # E10.3 (Furkan-Update B, 18:27): Liquidationszonen auf der EINSTIEGS-Seite. Nach dem
    # Befund aus E10.2 (Verkaufsseite kostet durchgehend Rendite) ist das die Seite, auf
    # der noch etwas zu holen sein koennte. "boost" = zusaetzlich aufstocken bei Konfluenz,
    # "filter" = nur noch bei Konfluenz einsteigen (Gegenprobe, vermutlich zu restriktiv).
    V("LIVE +Stop +Liq-Konfluenz aufstocken", bias_short=False, flush_entry="core",
      buy_ladder=True, trail_stop=True, liq_entry="boost"),
    V("LIVE +Stop +nur bei Liq-Konfluenz einsteigen", bias_short=False, flush_entry="core",
      buy_ladder=True, trail_stop=True, liq_entry="filter"),
    # E10.2 (Furkan-Update 19:52): Teilverkauf kurz unter dem letzten Hoch statt nur am
    # Fib-Ziel. "weak" = nur wenn der Anlauf ohne Spot-Nachfrage passiert (macht aus der
    # Breakout-Warnung eine messbare Handlung statt einer weiteren Telegram-Nachricht).
    V("LIVE +Stop +Verkauf am letzten Hoch", bias_short=False, flush_entry="core",
      buy_ladder=True, trail_stop=True, high_exit="on"),
    V("LIVE +Stop +Verkauf am schwachen Hoch", bias_short=False, flush_entry="core",
      buy_ladder=True, trail_stop=True, high_exit="weak"),
    # Kapital-Reserve (Furkan-Update Juli 2026: "Pulver haben zum Nachschiessen, klaren
    # Plan haben, ab welchem Niveau man wie viel Prozent seines Kapitals reinschiesst").
    # Gleiche Signale wie die Live-Variante — nur das Geld wird anders eingeteilt.
    V("LIVE +Stop, 60 % Einsatz (40 % Reserve)", bias_short=False, flush_entry="core",
      buy_ladder=True, trail_stop=True, deploy_pct=0.6),
    V("LIVE +Stop, 50 % Einsatz (50 % Reserve)", bias_short=False, flush_entry="core",
      buy_ladder=True, trail_stop=True, deploy_pct=0.5),
    # ---------------------------------------------------------------- E13 (Kaisers Frage:
    # "Furkan steigt nur bei gesunden Indikatoren ein — warum kauft die App trotzdem?")
    # Befund: von 34 Ersteinstiegen hatten 16 GAR KEINE Flow-Pruefung (0.5-Level) und
    # 16 das Muster NEUTRAL. Vier Hebel, jeder EINZELN und alle ZUSAMMEN gegen die
    # Live-Einstellung. Basis ist immer "LIVE +Stop", damit das Delta ablesbar ist.
    V("LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf)",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      block_unhealthy=True),
    V("LIVE +Stop +Flow-Pruefung am 0.5-Level",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      confirm_t1=True),
    V("LIVE +Stop +Sperre 48 h nach Stop",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      cooldown_h=48),
    V("LIVE +Stop +Mindest-Stopabstand 2 %",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      min_stop_pct=0.02),
    V("LIVE +Stop +Sperre 48 h +Mindestabstand 2 %",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      cooldown_h=48, min_stop_pct=0.02),
    V("LIVE +Stop +alle vier neuen Hebel",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      block_unhealthy=True, confirm_t1=True, cooldown_h=48, min_stop_pct=0.02),
    # E13, zweiter Lauf: Vertragen sich die beiden Kandidaten, die einzeln gut gemessen
    # haben? Mindest-Stopabstand (gleiche Rendite bei fast halbem Rueckgang, in beiden
    # Haelften auf Augenhoehe mit der Live-Einstellung) und liq_entry="boost" (die einzige
    # Variante, die sich zweimal hintereinander in BEIDEN Haelften unter den besten 5
    # gehalten hat). Beide greifen an derselben Stelle an — der Einstiegs-Auswahl —, also
    # ist Ueberschneidung moeglich: "Sperre + Mindestabstand" war zusammen SCHLECHTER als
    # jeder Hebel allein (+26,4 % gegen +33,9/+33,0 %). Genau das wird hier geprueft.
    V("LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      min_stop_pct=0.02, liq_entry="boost"),
    V("LIVE +Stop +Sperre 48 h +Liq-Konfluenz",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      cooldown_h=48, liq_entry="boost"),
    # ---------------------------------------------------------------- E14 (Kaiser 2026-07-28)
    # Furkan nimmt auf dem Weg nach oben Teilgewinne kurz VOR dem Widerstand: "hier unter
    # diesem Hoch rausnehmen" (Video A 19:52) und noch einmal knapp darueber, wo die
    # Short-Liquidationen sitzen (Video B 19:14). Beides wurde in E9.11/E10.2 gemessen und
    # hat Rendite gekostet — ABER gegen die DAMALIGE Basis, ohne Mindest-Stopabstand und
    # ohne Liq-Konfluenz. Seit 2026-07-28 ist die Basis eine andere: deutlich weniger,
    # dafuer bessere Positionen. Die Frage ist also offen und wird hier neu gestellt.
    # Basis = die neue LIVE-Einstellung (panel-Zeile), damit das Delta sauber ablesbar ist.
    # LIVE seit 2026-07-28 (zweite Umstellung des Tages). Gegen die ALTE Basis hatte
    # high_exit 3,9 Punkte gekostet (E10.2) — gegen die neue bringt es 1,2 und hebt den
    # Recall von 50 auf 57 %. Der Befund "die Verkaufsseite ist auserzaehlt" galt also
    # nur fuer die damalige Basis mit vielen aussichtslosen Einstiegen. Erstmals liegen
    # ZWEI Varianten in beiden Haelften unter den besten 5 (Zufallserwartung 0,8).
    V("NEU-LIVE +Verkauf unter dem letzten Hoch", panel=True,
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      min_stop_pct=0.02, liq_entry="boost", high_exit="on"),
    V("NEU-LIVE +Verkauf an den Liquidations-Niveaus",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      min_stop_pct=0.02, liq_entry="boost", liq_exit="zone"),
    V("NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      min_stop_pct=0.02, liq_entry="boost", high_exit="on", liq_exit="zone"),
    # E18 (Durchsicht 27.08.2026): zwei Mechanik-Korrekturen gegen die aktuelle
    # Live-Einstellung gemessen — einzeln und zusammen.
    #   no_flip:        in einer Kerze wird nur in EINE Richtung gehandelt. Betroffen
    #                   waren 16 der 214 Live-Signale (aufstocken UND teilverkaufen,
    #                   meist zum selben Preis). Erwartung: minimal weniger Signale,
    #                   etwas weniger Gebuehren; die Rendite zeigt, ob dabei auch
    #                   gute Nachkaeufe verloren gehen.
    #   freeze_targets: das 1.618-Ziel wandert nicht mehr mit einem spaeteren Tief
    #                   nach unten. Erwartung: WENIGER TEILVERKAUF_2 (im letzten Lauf
    #                   gab es genau einen) — die Frage ist, ob die Position dadurch
    #                   laenger laeuft und mehr bringt oder unverkauft zurueckfaellt.
    V("NEU-LIVE +kein Gegengeschaeft je Kerze",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      min_stop_pct=0.02, liq_entry="boost", high_exit="on", no_flip=True),
    V("NEU-LIVE +Ziele festhalten",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      min_stop_pct=0.02, liq_entry="boost", high_exit="on", freeze_targets=True),
    V("NEU-LIVE +kein Gegengeschaeft +Ziele festhalten",
      bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
      min_stop_pct=0.02, liq_entry="boost", high_exit="on",
      no_flip=True, freeze_targets=True),
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
                 oi_map: dict | None = None, liq_map: dict | None = None,
                 fut_map: dict | None = None, ls_map: dict | None = None):
    """OI aus oi_map (Coinalyze, E9.1) je Kerze; ohne oi_map bleibt OI konstant (neutral).
    liq_map liefert (long_liq, short_liq) je Kerzen-Open-ts.
    fut_map (E16) liefert das Futures-Taker-Delta je Kerze -> wird hier zum Futures-CVD
    aufsummiert; ohne fut_map bleibt es 0 und classify_pattern nutzt den Ersatzweg.
    ls_map (E16) liefert den Long-Anteil in Prozent."""
    candles, flow, spot_cvd, fut_cvd = [], [], 0.0, 0.0
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
        fut_cvd += (fut_map.get(ts, 0.0) if fut_map else 0.0)
        flow.append(FlowPoint(ts, spot_cvd, fut_cvd, oi_val,
                              latest_leq(funding, ts + CANDLE_MS), long_liq, short_liq,
                              (ls_map.get(ts, 0.0) if ls_map else 0.0)))
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


def run_half(candles, flow, cfg: dict, start_ms: int, end_ms: int | None = None):
    """Eine Variante ueber ein Teilfenster laufen lassen (E11, Robustheitspruefung).

    Warum das noetig ist: Inzwischen werden ~18 Varianten gegen EIN Zeitfenster
    verglichen. Bei so vielen Vergleichen sieht die beste zwangslaeufig besser aus, als
    sie ist — wie der Beste von 18 Muenzwerfern. Laeuft dieselbe Variante in zwei
    getrennten Haelften vorne, ist der Vorteil vermutlich echt; kippt die Rangfolge,
    haben wir Rauschen optimiert.

    `end_ms` schneidet die Kerzen hinten ab (Haelfte 1). Ohne `end_ms` laeuft es bis zum
    Fensterende, wobei die Kerzen VOR `start_ms` als Warmup dienen (Haelfte 2) — die
    Engine kennt die Vergangenheit, genau wie im Live-Betrieb.
    """
    cs, fl = candles, flow
    if end_ms is not None:
        cut = 0
        for i, c in enumerate(candles):
            if c.ts <= end_ms:
                cut = i + 1
            else:
                break
        cs, fl = candles[:cut], flow[:cut]
    if not cs:
        return [], None
    sigs = run_backtest(cs, fl, cfg, start_ms=start_ms)
    pnl = simulate(sigs, cs, start_ms=start_ms, deploy_pct=cfg.get("deploy_pct", 1.0))
    return sigs, pnl


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
             deploy_pct: float = 1.0, fill: str = "level") -> dict:
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

    Liefert zusaetzlich `monate`: den Kontostand am Ende jedes Kalendermonats, bewertet
    zum jeweiligen Schlusskurs (offene Positionen also mitgerechnet). Daraus entsteht die
    Monatsuebersicht im Bericht — Kaisers Frage "was haette ich Monat fuer Monat verdient
    oder verloren?".

    `fill` (E17, Kaisers Frage 2026-07-29 "was ist die Vorab-Info wert?"):
    - "level"  = zum genannten Preis abgerechnet. Das sind bei Einstiegen am 0.5-Level,
                 im Golden Pocket, an der 0.786-Zone und bei den Extension-Zielen
                 FIB-LEVELS, die die Kerze nur BERUEHRT hat — moeglicherweise in Stunde 2
                 einer 4h-Kerze. Diese Preise bekommt nur, wer die Limit-Order VORHER
                 dort liegen hat.
    - "close"  = alles zum SCHLUSSKURS der ausloesenden Kerze. Das bildet ab, dass man
                 erst nach der Telegram-Nachricht reagiert, der Kurs sich also vom Level
                 wieder wegbewegt haben kann.
    Der Unterschied beider Laeufe IST der Wert der Vorab-Order. Signale, die ohnehin zum
    Kerzenschluss feuern (Stop, Restverkauf, Flush, Kaufleiter), sind in beiden Faellen
    identisch — der Effekt isoliert also genau die Level-Signale.

    EINORDNUNG, damit die Zahl nicht ueberschaetzt wird: "close" ist noch freundlich
    gerechnet. Es unterstellt, dass man GENAU zum Kerzenschluss handelt. Tatsaechlich
    laeuft die Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026),
    der reale Preis liegt also noch einmal weiter weg. Die gemessene Luecke ist damit
    eine UNTERGRENZE fuer den Wert der Vorab-Order.
    """
    schluss_je_ts = {c.ts: c.close for c in candles}

    def _preis(s: dict) -> float:
        if fill == "level":
            return s["price"]
        return schluss_je_ts.get(s["ts"], s["price"])
    cash, units, peak_units, l_avg = start_capital, 0.0, 0.0, 0.0
    s_units, s_peak, s_avg = 0.0, 0.0, 0.0            # Short-Seite
    alloc = 0.0
    trades_closed = wins = 0
    long_profit = short_profit = 0.0                 # Gewinn/Verlust je Richtung (E9.6)
    long_trades = long_wins = short_trades = short_wins = 0
    equity = []

    def equity_now(price):
        return cash + units * price + s_units * (s_avg - price)

    # --- Monatsgrenzen vorbereiten (Monatsuebersicht) --------------------------------
    hs0 = start_ms if start_ms is not None else START_MS
    _closes = [(c.ts, c.close) for c in candles if c.ts >= hs0]
    if not _closes:
        _closes = [(candles[-1].ts, candles[-1].close)]

    def _preis_bei(ts_ms: int) -> float:
        p = _closes[0][1]
        for t, cl in _closes:
            if t <= ts_ms:
                p = cl
            else:
                break
        return p

    _grenzen = []                      # (ts des Monatsendes, "YYYY-MM" des Monats)
    _d = datetime.fromtimestamp(hs0 / 1000, tz=timezone.utc)
    _m = datetime(_d.year, _d.month, 1, tzinfo=timezone.utc)
    while True:
        _next = (_m + timedelta(days=32)).replace(day=1)
        _ts = int(_next.timestamp() * 1000) - 1
        _grenzen.append((_ts, _m.strftime("%Y-%m")))
        if _ts >= candles[-1].ts:
            break
        _m = _next
    monate, _gi, _letztes_eq = [], 0, start_capital

    def _snapshot_bis(ts_ms: int):
        nonlocal _gi, _letztes_eq
        while _gi < len(_grenzen) and _grenzen[_gi][0] <= ts_ms:
            g_ts, g_name = _grenzen[_gi]
            eq = equity_now(_preis_bei(g_ts))
            monate.append({"monat": g_name, "ende": round(eq, 2),
                           "gewinn": round(eq - _letztes_eq, 2),
                           "rendite_pct": round((eq / _letztes_eq - 1) * 100, 2)
                           if _letztes_eq else 0.0})
            _letztes_eq = eq
            _gi += 1

    for s in signals:
        _snapshot_bis(s["ts"])
        p, t = _preis(s), s["type"]
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
    _snapshot_bis(candles[-1].ts)      # abgeschlossene Monate nachtragen
    if _gi < len(_grenzen):
        # Der laufende Monat ist angeschnitten (das Fenster endet mittendrin). Ohne
        # diesen Eintrag fehlt er in der Uebersicht und die Monatssumme stimmt nicht
        # mehr mit dem Gesamtergebnis ueberein.
        monate.append({"monat": _grenzen[_gi][1], "ende": round(end_equity, 2),
                       "gewinn": round(end_equity - _letztes_eq, 2),
                       "rendite_pct": round((end_equity / _letztes_eq - 1) * 100, 2)
                       if _letztes_eq else 0.0})
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
        "monate": monate,
        "offene_position": round(units * last_price + s_units * (s_avg - last_price), 2),
    }


def furkan_pnl(candles, kauf_tage: list[str], verkauf_tage: list[str],
               kauf_pct: float, verkauf_pct: float, fee: float = 0.001,
               start_capital: float = 10000.0, start_ms: int | None = None,
               end_ms: int | None = None) -> dict:
    """Was haetten FURKANS eigene Termine verdient? (E15)

    Bisher dienten Kaisers Trigger-Listen nur als Aehnlichkeits-Massstab (Recall) — was
    sie an Geld gebracht haetten, wurde nie gerechnet. Diese Funktion schliesst die Luecke
    und macht Kaisers Frage „ist seine Methode besser?" zu einer Zahl.

    Annahmen (bewusst offengelegt, weil die Listen nur TAGE enthalten, keine Betraege):
    - Preis = Schlusskurs der letzten 4h-Kerze des jeweiligen UTC-Tages.
    - `kauf_pct` = Anteil des freien Geldes je Kauftag, `verkauf_pct` = Anteil der
      Position je Verkaufstag. Beides ist UNBEKANNT — deshalb wird ausserhalb eine
      Spanne ueber mehrere Annahmen gerechnet statt einer Scheingenauigkeit.
    - Tage mit Kauf UND Verkauf: erst verkaufen, dann kaufen (Rotation, so liest es
      docs/GEGENCHECK.md: Teilgewinn/Stop der Altposition + Neueinstieg).
    - Gleiche Gebuehr, gleiches Startkapital, gleiches Fenster wie die Engine-Simulation.
    - Offene Position wird am Fensterende zum Schlusskurs bewertet.
    """
    tage: dict[date, float] = {}
    for c in candles:
        if (start_ms is not None and c.ts < start_ms) or (end_ms is not None and c.ts > end_ms):
            continue
        tage[to_date(c.ts)] = c.close                    # letzter Schluss des Tages gewinnt
    if not tage:
        return {}
    kauf = {date.fromisoformat(d) for d in kauf_tage}
    verkauf = {date.fromisoformat(d) for d in verkauf_tage}

    cash, units, invest, peak_eq = start_capital, 0.0, 0.0, start_capital
    max_dd, n_kauf, n_verkauf = 0.0, 0, 0
    for tag in sorted(tage):
        preis = tage[tag]
        if tag in verkauf and units > 0:                 # erst raus ...
            weg = units * verkauf_pct
            cash += weg * preis * (1 - fee)
            units -= weg
            n_verkauf += 1
        if tag in kauf and cash > 0:                     # ... dann rein
            rein = cash * kauf_pct
            units += rein * (1 - fee) / preis
            cash -= rein
            invest += rein
            n_kauf += 1
        eq = cash + units * preis
        peak_eq = max(peak_eq, eq)
        max_dd = min(max_dd, eq / peak_eq - 1.0)
    ende = cash + units * tage[max(tage)]
    return {
        "kauf_pct": round(kauf_pct * 100), "verkauf_pct": round(verkauf_pct * 100),
        "ende": round(ende, 2), "rendite_pct": round((ende / start_capital - 1) * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "kauftage": n_kauf, "verkaufstage": n_verkauf,
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
    oi_map, liq_map, fut_map, ls_map = {}, {}, {}, {}
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
        try:                                   # E16, eigener Block (siehe main.py)
            fut_map = coinalyze.fut_delta_by_ts(api_key, frm=WARMUP_MS // 1000,
                                                to=END_MS // 1000)
            ls_map = coinalyze.long_short_by_ts(api_key, frm=WARMUP_MS // 1000,
                                                to=END_MS // 1000)
            print(f"Coinalyze: {len(fut_map)} Futures-Delta-Punkte, {len(ls_map)} "
                  f"Long-Short-Punkte -> Muster 2 erstmals mit echtem Futures-CVD.")
        except Exception as exc:  # noqa: BLE001
            print(f"Coinalyze Futures/Long-Short nicht verfuegbar ({exc}) -> wie bisher.")

    candles, flow = build_series(raw, funding, oi_map, liq_map, fut_map, ls_map)
    # Vergleichsreihe OHNE Futures-Daten: dieselben Kerzen, fut_cvd = 0. Damit laesst sich
    # die Wirkung der neuen Daten sauber isolieren (gleiche Variante, nur andere Daten).
    _, flow_ohne_fut = build_series(raw, funding, oi_map, liq_map, None, ls_map)

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

    # --- E17: Was ist die Vorab-Order wert? -----------------------------------------
    # Kaisers Frage: Die meisten Kaufsignale nennen ein Level, das die Kerze nur BERUEHRT
    # hat — moeglicherweise in Stunde 2. Wer erst nach der Nachricht reagiert, bekommt
    # diesen Preis nicht. Zwei Laeufe derselben Signale, nur anders abgerechnet.
    _pcfg2 = next((c for c in GRID if c.get("panel")), GRID[0])
    _vsig = run_backtest(candles, flow, _pcfg2, start_ms=eff_start)
    p_level = simulate(_vsig, candles, start_ms=eff_start, fill="level")
    p_close = simulate(_vsig, candles, start_ms=eff_start, fill="close")
    _schluss = {c.ts: c.close for c in candles}
    _abw = [abs(s["price"] - _schluss[s["ts"]]) / _schluss[s["ts"]] * 100
            for s in _vsig if s["ts"] in _schluss and _schluss[s["ts"]]
            and abs(s["price"] - _schluss[s["ts"]]) / _schluss[s["ts"]] > 0.0005]
    _abw.sort()
    _median = _abw[len(_abw) // 2] if _abw else 0.0
    vorab_zeilen = [
        "",
        "## Was ist die Vorab-Information wert?",
        "",
        "Die meisten Kauf- und Teilgewinn-Signale nennen ein **Fib-Level**, das die Kerze "
        "nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben. Wer "
        "erst auf die Telegram-Nachricht reagiert, findet diesen Preis oft nicht mehr am "
        "Markt. Beide Zeilen sind DIESELBEN Signale, nur anders abgerechnet.",
        "",
        "| Abrechnung | Rendite | max. Rueckgang |",
        "|---|---|---|",
        f"| **Limit-Order lag vorher dort** (zum genannten Level) | "
        f"**{p_level['rendite_pct']:+.1f} %** | {p_level['max_drawdown_pct']:.1f} % |",
        f"| **erst nach der Nachricht reagiert** (zum Kerzenschluss) | "
        f"**{p_close['rendite_pct']:+.1f} %** | {p_close['max_drawdown_pct']:.1f} % |",
        f"| Unterschied | **{p_level['rendite_pct'] - p_close['rendite_pct']:+.1f} Punkte** | |",
        "",
        f"Betroffen sind {len(_abw)} von {len(_vsig)} Signalen — bei den uebrigen ist der "
        "genannte Preis ohnehin der Kerzenschluss (Stop, Restverkauf, Flush-Einstieg, "
        f"Kaufleiter). Bei den betroffenen liegt der Kerzenschluss im Median "
        f"**{_median:.2f} %** vom genannten Level entfernt.",
        "",
        "**So ist das zu lesen:** Der Unterschied ist der Wert der Vorbereitung — also "
        "dessen, was die Vorschau-Nachricht und die Zonen-Linien im Chart ermoeglichen. "
        "Ist er klein, kann man entspannt auf die Signale reagieren. Ist er gross, "
        "entscheidet die vorab platzierte Order ueber einen erheblichen Teil des "
        "Ergebnisses.",
        "",
        "**Die Zahl ist eine UNTERGRENZE.** Die Zeile 'erst nach der Nachricht' "
        "unterstellt, dass man genau zum Kerzenschluss handelt. Tatsaechlich laeuft die "
        "Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026), der "
        "reale Preis liegt also noch weiter weg. Ausserdem rechnet auch die obere Zeile "
        "ohne Schlupf und ohne Teilausfuehrungen.",
    ]
    print(f"E17 Vorab-Order: Level {p_level['rendite_pct']:+.1f} % gegen Kerzenschluss "
          f"{p_close['rendite_pct']:+.1f} % ({len(_abw)} betroffene Signale, "
          f"Median-Abweichung {_median:.2f} %)")

    # --- E16: Wirkung der echten Futures-Daten isolieren ----------------------------
    # Dieselbe Variante, dieselben Kerzen — einmal MIT echtem Futures-CVD, einmal ohne.
    # Alles andere ist identisch, der Unterschied ist also allein den neuen Daten
    # zuzuschreiben. Das ist der Test der Frage, die seit neun gescheiterten
    # Order-Flow-Filtern offen ist: lag es an der Idee oder am Material?
    fut_zeilen = []
    if fut_map:
        _pcfg = next((c for c in GRID if c.get("panel")), GRID[0])
        v_mit = run_backtest(candles, flow, _pcfg, start_ms=eff_start)
        v_ohne = run_backtest(candles, flow_ohne_fut, _pcfg, start_ms=eff_start)
        p_mit = simulate(v_mit, candles, start_ms=eff_start)
        p_ohne = simulate(v_ohne, candles, start_ms=eff_start)
        s_mit, s_ohne = score(v_mit, start_ms=eff_start), score(v_ohne, start_ms=eff_start)
        fut_zeilen = [
            "",
            "## Echte Futures-Daten: was bringen sie?",
            "",
            f"Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes "
            f"({len(fut_map)} Punkte) — damit hat die Engine erstmals ein echtes "
            "Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter "
            "Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.",
            "",
            f"Beide Zeilen: Variante *{_pcfg['label']}*, dieselben Kerzen, derselbe "
            "Zeitraum. Der einzige Unterschied sind die Daten.",
            "",
            "| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |",
            "|---|---|---|---|---|---|",
            f"| ohne Futures-CVD (Stand bisher) | {s_ohne['recall']:.0%} | "
            f"{s_ohne['precision']:.0%} | {p_ohne['rendite_pct']:+.1f} % | "
            f"{p_ohne['max_drawdown_pct']:.1f} % | {len(v_ohne)} |",
            f"| **mit echtem Futures-CVD** | {s_mit['recall']:.0%} | "
            f"{s_mit['precision']:.0%} | **{p_mit['rendite_pct']:+.1f} %** | "
            f"{p_mit['max_drawdown_pct']:.1f} % | {len(v_mit)} |",
            "",
            ("**Gleiche Signalzahl = die neuen Daten aendern nichts.** Muster 2 feuert mit "
             "echten Futures-Daten an denselben Stellen wie mit den Ersatzmerkmalen — die "
             "Naeherung war also gut genug. Damit ist die Erklaerung 'unsere Order-Flow-"
             "Daten waren zu schlecht' fuer die neun gescheiterten Filter widerlegt; es "
             "liegt an der Uebersetzung in feste Regeln, nicht am Material."
             if len(v_mit) == len(v_ohne) else
             f"**{abs(len(v_mit) - len(v_ohne))} Signale Unterschied** — die echten Daten "
             "erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das "
             "hilft, sagt die Rendite-Spalte."),
        ]
        print(f"E16 Futures-CVD: mit {p_mit['rendite_pct']:+.1f} % ({len(v_mit)} Signale) "
              f"gegen ohne {p_ohne['rendite_pct']:+.1f} % ({len(v_ohne)} Signale)")

    # --- E11: Robustheitspruefung, Fenster halbiert ---------------------------------
    mid_ms = eff_start + (END_MS - eff_start) // 2
    print(f"\nRobustheitspruefung: Haelfte 1 bis {to_date(mid_ms).strftime('%d.%m.%Y')}, "
          f"Haelfte 2 danach ...")
    halves = []
    for cfg in GRID:
        _s1, p1 = run_half(candles, flow, cfg, eff_start, end_ms=mid_ms)
        _s2, p2 = run_half(candles, flow, cfg, mid_ms)
        if p1 is None or p2 is None:            # leeres Teilfenster -> ueberspringen
            continue
        halves.append((cfg, p1, p2))
        print(f"  {cfg['label']}: H1 {p1['rendite_pct']:+.1f} % | "
              f"H2 {p2['rendite_pct']:+.1f} %")

    # Auswahl: primaer Rendite (das Geld-Maß), dann Recall, dann Praezision
    best = max(results, key=lambda r: (r[3]["rendite_pct"], r[2]["recall"], r[2]["precision"]))
    best_cfg, sigs, sc, pnl = best

    # Panel-Variante = die als panel=True markierte (Live-Einstellung), damit die
    # Chart-Seite zeigt, was die Engine WIRKLICH tut — nicht die beste Fantasie-Variante.
    panel_r = next((r for r in results if r[0].get("panel")), best)
    panel_cfg, _psigs, panel_sc, panel_pnl = panel_r

    # --- Monatsuebersicht: Live-Einstellung gegen "ohne Flush" (Kaisers Frage) -------
    _of = next((r for r in results if r[0]["label"] == "MEINE Einstellung ohne Flush"), None)
    m_live = {m["monat"]: m for m in panel_pnl.get("monate", [])}
    m_ohne = {m["monat"]: m for m in (_of[3].get("monate", []) if _of else [])}
    monats_zeilen = []
    if m_live or m_ohne:
        def _z(eintrag, feld):
            if not eintrag:
                return "—"
            return (f"{eintrag[feld]:+,.0f} €" if feld == "gewinn"
                    else f"{eintrag[feld]:+.1f} %")
        monats_zeilen = [
            "",
            "## Monat fuer Monat",
            "",
            "Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen "
            "Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten "
            "(das Fenster beginnt Mitte November und endet heute).",
            "",
            f"Links die Live-Einstellung (*{panel_cfg['label']}*), rechts dieselbe "
            "Einstellung **ohne** den aggressiven Flush-Einstieg.",
            "",
            "| Monat | live € | live % | ohne Flush € | ohne Flush % |",
            "|---|---|---|---|---|",
        ]
        for name in sorted(set(m_live) | set(m_ohne)):
            a, b = m_live.get(name), m_ohne.get(name)
            monats_zeilen.append(
                f"| {name} | {_z(a, 'gewinn')} | {_z(a, 'rendite_pct')} | "
                f"{_z(b, 'gewinn')} | {_z(b, 'rendite_pct')} |")
        _pos = sum(1 for m in m_live.values() if m["gewinn"] > 0)
        _pos_o = sum(1 for m in m_ohne.values() if m["gewinn"] > 0)
        monats_zeilen += [
            "",
            f"Monate im Plus: **{_pos} von {len(m_live)}** (live) gegen "
            f"**{_pos_o} von {len(m_ohne)}** (ohne Flush).",
            "",
            "Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein "
            "spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate "
            "sind deshalb nur ueber die Prozentspalte fair vergleichbar.",
        ]

    # --- E15: Was haetten FURKANS eigene Termine verdient? ---------------------------
    # Kaisers Frage: "Wie testen wir, ob seine Methode besser ist?" Seine Trigger-Listen
    # dienten bisher nur als Aehnlichkeits-Massstab. Hier laufen sie erstmals durch
    # dieselbe P&L-Rechnung wie die Engine — gleiches Fenster, gleiche Gebuehr, gleiches
    # Startkapital. Fair vergleichbar ist nur bis zum LETZTEN notierten Trigger.
    f_ende_d = max(date.fromisoformat(x) for x in KAUF_DATEN + VERKAUF_DATEN)
    f_ende_ms = int(datetime(f_ende_d.year, f_ende_d.month, f_ende_d.day, 23, 59,
                             tzinfo=timezone.utc).timestamp() * 1000)
    f_start_d = min(date.fromisoformat(x) for x in KAUF_DATEN + VERKAUF_DATEN)
    f_start_ms = int(datetime(f_start_d.year, f_start_d.month, f_start_d.day,
                              tzinfo=timezone.utc).timestamp() * 1000)

    def _spanne(von_ms):
        """Furkans Termine ueber 12 Groessen-Annahmen; Verkauf 100 % = jeder Verkaufstag
        ist ein voller Ausstieg (so verhalten sich seine Stops)."""
        lf = [furkan_pnl(candles, KAUF_DATEN, VERKAUF_DATEN, kp, vp,
                         start_ms=von_ms, end_ms=f_ende_ms)
              for kp in (0.25, 0.33, 0.50) for vp in (0.25, 0.33, 0.50, 1.0)]
        return [x for x in lf if x]

    furkan_zeilen = []
    kurz, lang = _spanne(eff_start), _spanne(max(f_start_ms, candles[0].ts))
    _ks, e_kurz = run_half(candles, flow, panel_cfg, eff_start, end_ms=f_ende_ms)
    _ls, e_lang = run_half(candles, flow, panel_cfg, max(f_start_ms, candles[0].ts),
                           end_ms=f_ende_ms)
    if kurz and lang and e_kurz and e_lang:
        def _zeile(name, lf, eng, von_d):
            r = sorted(x["rendite_pct"] for x in lf)
            m = next(x for x in lf if x["kauf_pct"] == 33 and x["verkauf_pct"] == 33)
            return (f"| {name}<br><sub>{von_d.strftime('%d.%m.%Y')}–"
                    f"{f_ende_d.strftime('%d.%m.%Y')}</sub> | "
                    f"**{r[0]:+.1f} % bis {r[-1]:+.1f} %** | {m['rendite_pct']:+.1f} % | "
                    f"{m['max_drawdown_pct']:.1f} % | **{eng['rendite_pct']:+.1f} %** | "
                    f"{eng['max_drawdown_pct']:.1f} % | {eng['buyhold_pct']:+.1f} % |")
        m_lang = next(x for x in lang if x["kauf_pct"] == 33 and x["verkauf_pct"] == 33)
        furkan_zeilen = [
            "",
            "## Furkans eigene Termine gegen die Engine",
            "",
            "Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). "
            "Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche "
            f"Kurse, gleiche Gebuehr ({panel_pnl['fee_pct']:.1f} %/Order), 10.000 € Start, "
            "offene Position am Ende zum Schlusskurs bewertet.",
            "",
            "**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo "
            "die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem "
            "Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht "
            "kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. "
            "Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine "
            "Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das "
            "Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide "
            "Fenster zusammen ergeben ein faires Bild.**",
            "",
            "Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — "
            "daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, "
            "Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein "
            "Teil seiner Verkaufstage Stops waren, also volle Ausstiege.",
            "",
            "| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |",
            "|---|---|---|---|---|---|---|",
            _zeile("**kurz** (Engine hat alle Daten)", kurz, e_kurz, to_date(eff_start)),
            _zeile("**lang** (Furkans volle Abfolge)", lang, e_lang, f_start_d),
            "",
            f"Im langen Fenster handelte Furkan an {m_lang['kauftage']} Kauf- und "
            f"{m_lang['verkaufstage']} Verkaufstagen.",
            "",
            "**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter "
            "Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode "
            "genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am "
            "selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in "
            "beiden darueber, ist die Richtung „mehr wie Furkan werden\" die falsche und "
            "der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, "
            "entscheidet keines von beiden.",
            "",
            "**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste "
            "ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein "
            "geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. "
            "Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er "
            "handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, "
            "steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt "
            "beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag "
            "erlebt hat.",
        ]

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
        "**Lesehilfe zu den Namen:** `LIVE` ist die Abkuerzung fuer *nur Long + Kaufleiter "
        "+ Flush core* — der Flush steckt also drin. Jede Zeile, die mit `LIVE +…` beginnt, "
        "baut darauf auf. Die Zeile *+Kaufleiter* ist dagegen OHNE Flush.",
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
        *monats_zeilen,
        *vorab_zeilen,
        *fut_zeilen,
        *furkan_zeilen,
        "",
        "## Robustheitspruefung: Fenster halbiert",
        "",
        f"Warum: Oben werden {len(GRID)} Varianten gegen EIN Zeitfenster verglichen. Die "
        "beste von vielen sieht immer besser aus als sie ist — wie der Beste von "
        f"{len(GRID)} Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt "
        "in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der "
        "Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**",
        "",
        f"Haelfte 1: {to_date(eff_start).strftime('%d.%m.%Y')}–"
        f"{to_date(mid_ms).strftime('%d.%m.%Y')} · "
        f"Haelfte 2: {to_date(mid_ms).strftime('%d.%m.%Y')}–"
        f"{to_date(END_MS).strftime('%d.%m.%Y')}. "
        "Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die "
        "Rangfolge schauen, nicht auf die einzelne Zahl.",
        "",
        "| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |",
        "|---|---|---|---|---|",
    ]
    rang1 = {c["label"]: i + 1 for i, (c, _p1, _p2) in enumerate(
        sorted(halves, key=lambda r: -r[1]["rendite_pct"]))}
    rang2 = {c["label"]: i + 1 for i, (c, _p1, _p2) in enumerate(
        sorted(halves, key=lambda r: -r[2]["rendite_pct"]))}
    for hcfg, p1, p2 in halves:
        lines.append(f"| {hcfg['label']} | {p1['rendite_pct']:+.1f} % | "
                     f"{rang1[hcfg['label']]}. | {p2['rendite_pct']:+.1f} % | "
                     f"{rang2[hcfg['label']]}. |")

    top1 = {hcfg['label'] for hcfg, _p1, _p2 in
            sorted(halves, key=lambda r: -r[1]["rendite_pct"])[:5]}
    top2 = {hcfg['label'] for hcfg, _p1, _p2 in
            sorted(halves, key=lambda r: -r[2]["rendite_pct"])[:5]}
    stabil = sorted(top1 & top2)
    lines += [
        "",
        f"**In BEIDEN Haelften unter den besten 5:** "
        + (", ".join(stabil) if stabil else "keine einzige Variante"),
        "",
        # Ohne diesen Massstab wird die Zahl regelmaessig ueberschaetzt: Bei vielen
        # Varianten landet auch rein zufaellig hin und wieder eine zweimal oben.
        # Erwartungswert bei rein zufaelliger Rangfolge = (5 x 5) / Anzahl Varianten.
        (f"**Wie viel davon waere blosser Zufall?** Bei {len(halves)} Varianten und je 5 "
         f"Plaetzen liegt der Erwartungswert bei reinem Zufall bei "
         f"**{25 / len(halves):.1f}** Varianten. Gemessen: **{len(stabil)}**. "
         + ("Das ist nicht mehr als der Zufall ohnehin liefert — die Rangfolge oben ist "
            "damit KEIN Beleg. Dann nur den groben Hebeln trauen (Richtung, Kaufleiter, "
            "Flush) und die Feinheiten weglassen."
            if len(stabil) <= 25 / len(halves) + 0.5 else
            "Das ist deutlich mehr als der Zufall liefert — die Rangfolge oben traegt.")
         if len(halves) else ""),
        "",
        ("Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl "
         "und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. "
         "Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die "
         "verlaesslichere Wahl — auch wenn ihre Platzierung schwankt."),
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
    # Zweite Spalte fuer die Webseite (Kaiser 2026-07-28): dieselbe Einstellung OHNE den
    # aggressiven Flush-Einstieg. Grund: Flush-Signale sind in Telegram als solche
    # markiert und Kaiser entscheidet bei jedem einzeln, ob er ihn mitgeht. Die
    # Monatsuebersicht zeigt deshalb BEIDE Spalten — "ohne Flush" ist der Boden, den er
    # sicher umsetzt, "mit Flush" die Obergrenze, wenn er jeden mitnimmt. Sein
    # tatsaechliches Ergebnis liegt dazwischen. Die Signale selbst bleiben unveraendert:
    # Der Flush wird weiter erzeugt, gesendet und im Chart gezeichnet — nur die
    # SIMULATION zeigt zusaetzlich die konservative Rechnung.
    if _of is not None:
        panel["variante_ohne_flush"] = _of[0]["label"]
        panel["pnl_ohne_flush"] = {kk: vv for kk, vv in _of[3].items() if kk != "equity"}
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
