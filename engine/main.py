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
from datetime import date, datetime, timedelta
from pathlib import Path

import coinalyze
from strategy_core import (HIGH_EXIT_TOL, LADDER_FACTORS, LADDER_TRANCHE, TRANCHEN,
                           Candle, FibZones, FlowPoint, Impulse, Pivot, PosState,
                           Position, evaluate, fib_zones, find_pivots, gegen_zonen,
                           ampel, ampel_richtung, classify_pattern, lage_bericht,
                           orderflow_detail, OF_FENSTER, DIP_FLOOR_PCT, SignalType,
                           last_significant_impulse, liq_levels, next_pivot_beyond,
                           oi_in_btc)
from telegram_notify import (format_flush_aufloesung, format_flush_warnung,
                             format_stop_rueckeroberung, send_lage, send_plan,
                             send_signals, send_text, send_vorschau)

ROOT = Path(__file__).resolve().parent.parent          # Repo-Wurzel (signal-app/)
DATA = ROOT / "site" / "data"
TIMEFRAME = "4h"
CANDLE_MS = 4 * 3600 * 1000
LIMIT = 400                                            # ~66 Tage - fuer die Flush-Wache
# E33 (13.09.2026): Der Hauptlauf braucht mehr Historie. daily_trend(period=200)
# resampelt auf Tageskerzen - mit 400 4h-Kerzen sind das nur 67 Tage, und der "EMA200"
# waere in Wahrheit ein EMA67 (nachgemessen: 21 % Unterschied). Der Backtest sieht das
# volle Fenster und rechnet den echten EMA200; ohne diese Erhoehung wuerden Live und
# Messung verschiedene Dinge tun. 1300 Kerzen = ~217 Tage.
# GEPRUEFT vor der Aenderung: Bei der Live-Einstellung aendert mehr Historie KEIN
# einziges Signal (Test test_mehr_historie_aendert_die_signale_nicht). Nur daily_trend
# und daily_fib_zone lesen die gesamte Historie - beide haengen an Schaltern.
LIMIT_HAUPT = 1300                                     # ~217 Tage - reicht fuer EMA200
MAX_JE_ABRUF = 1000                                    # Grenze der Binance-API
MAX_ABRUFE = 5                                         # Notbremse gegen Endlosschleifen

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


# ------------------------------------------------ STH-Kostenbasis (E40, 21.09.2026)
# Beide Quellen haben am 21.09.2026 aus GitHub Actions geantwortet. Diese Funktionen
# nutzen der Backtest (E40.1) UND der Lage-Abruf - deshalb stehen sie hier.
#   bitview.space (Bitcoin Research Kit): ab 2009, tagesaktuell, ohne Abrufgrenze.
# Reine Werteliste OHNE Datum; Index 0 = 01.01.2009 (hergeleitet aus drei Ankern: erster
# Wert 0.0 am 03.01.2009 = Genesis, naechster am 09.01.2009 = erster Block danach,
# letzter Index = Abruftag). STH = Coins juenger als 150 Tage.
#   bitcoin-data.com (BGeometrics): Datum in jedem Punkt, aber 15 Abrufe/Tag je IP
# (GitHub teilt IPs) und 7 Tage Verzug. STH = juenger als 155 Tage.
STH_BITVIEW = "https://bitview.space/api/series/sth_realized_price/day1"
STH_BITVIEW_TAG0 = date(2009, 1, 1)
STH_BGEOMETRICS = "https://bitcoin-data.com/v1/sth-realized-price"


def _sth_holen(url: str) -> tuple:
    """(status, text, fehler). Wirft nie - ein Abruf, der abstuerzt, sagt nichts."""
    import urllib.error
    req = urllib.request.Request(url, headers={
        "User-Agent": "btc-signal-app-backtest (github actions)",
        "Accept": "application/json, text/csv, */*"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "replace"), ""
    except urllib.error.HTTPError as e:
        return e.code, "", f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return None, "", f"{type(e).__name__}: {e}"


def sth_bitview(holen=_sth_holen) -> tuple:
    """{datum: wert}, fehler. Datum aus dem Index; leere und Null-Werte fallen weg."""
    status, text, fehler = holen(STH_BITVIEW)
    if status != 200 or not text:
        return {}, fehler or f"Status {status}"
    try:
        d = json.loads(text)
        werte = d["data"] if isinstance(d, dict) else d
        start = int(d.get("start", 0)) if isinstance(d, dict) else 0
    except Exception as exc:  # noqa: BLE001
        return {}, f"Antwort nicht lesbar ({exc})"
    out = {}
    for i, v in enumerate(werte):
        if isinstance(v, (int, float)) and v > 0:
            out[STH_BITVIEW_TAG0 + timedelta(days=start + i)] = float(v)
    return out, ("" if out else "keine Werte in der Antwort")


def sth_bgeometrics(holen=_sth_holen) -> tuple:
    """{datum: wert}, fehler. Die Zahlen kommen dort als TEXT - umgewandelt, sonst
    vergleicht man "71262.19" mit 71262.19 und bekommt nie eine Uebereinstimmung."""
    status, text, fehler = holen(STH_BGEOMETRICS)
    if status != 200 or not text:
        return {}, fehler or f"Status {status}"
    try:
        liste = json.loads(text)
        out = {date.fromisoformat(p["d"]): float(p["sthRealizedPrice"])
               for p in liste if p.get("sthRealizedPrice") not in (None, "")}
    except Exception as exc:  # noqa: BLE001
        return {}, f"Antwort nicht lesbar ({exc})"
    return {k: v for k, v in out.items() if v > 0}, ""


def sth_kostenbasis(holen=_sth_holen) -> dict | None:
    """Der juengste Wert der STH-Kostenbasis fuer den Lage-Abruf (Kaiser 21.09.2026).

    Erst bitview.space (tagesaktuell), sonst bitcoin-data.com (7 Tage Verzug) - das
    Datum wird deshalb immer mitgegeben. Reine Anzeige: E40.1 hat gezeigt, dass die
    Marke im Messfenster keine Entscheidung der Engine unterscheiden kann.
    Wirft nie. Ohne Wert gibt es keine Zeile, statt einer falschen.
    """
    for quelle, abruf in (("bitview.space", sth_bitview),
                          ("bitcoin-data.com", sth_bgeometrics)):
        try:
            werte, _fehler = abruf(holen)
        except Exception:  # noqa: BLE001
            werte = {}
        if werte:
            tag = max(werte)
            return {"wert": werte[tag], "datum": tag.isoformat(), "quelle": quelle}
    return None


def fetch_spot(limit: int = LIMIT) -> list:
    """Spot-Kerzen holen - paginiert, weil die Binance-API hoechstens 1000 je Abruf
    liefert (E33). Bis 1000 genau ein Abruf wie bisher; darueber wird rueckwaerts
    nachgeladen und chronologisch zusammengesetzt.
    """
    basis = ("https://data-api.binance.vision/api/v3/klines"
             f"?symbol=BTCUSDT&interval={TIMEFRAME}")
    if limit <= MAX_JE_ABRUF:
        return _get_json(f"{basis}&limit={limit}")
    out = _get_json(f"{basis}&limit={MAX_JE_ABRUF}")
    # Abbruchsicherung: Waechst `out` in einem Durchlauf nicht, wird abgebrochen. Ohne
    # das liefe die Schleife ewig, falls die API wiederholt dieselben oder gar keine
    # neuen Kerzen liefert - im 15-Minuten-Takt ein haengender Workflow. Diese Luecke
    # hat die Sabotage-Probe zu E33 aufgedeckt, nicht der normale Testlauf.
    for _ in range(MAX_ABRUFE):
        if limit - len(out) <= 0:
            break
        bis = int(out[0][0])                       # aelteste bekannte Kerze
        block = _get_json(
            f"{basis}&limit={min(limit - len(out), MAX_JE_ABRUF)}&endTime={bis - 1}")
        if not block:
            break
        aeltester = int(out[0][0])
        out = block + out
        # Fortschritt heisst: die Historie reicht jetzt WEITER ZURUECK. Die blosse
        # Listenlaenge taugt nicht - liefert die API zweimal denselben Block, waechst
        # sie trotzdem (mit Duplikaten). Genau das hat die Sabotage-Probe gezeigt.
        if int(out[0][0]) >= aeltester:
            break
        time.sleep(0.3)
    return out


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
    spot_raw = fetch_spot(LIMIT_HAUPT)
    funding = fetch_funding_8h()

    # E9.1: echtes OI + Liquidationen von Coinalyze (falls Secret gesetzt), sonst
    # Kraken-OI-Snapshot als Fallback (Liquidationen dann 0 = Proxy in classify_pattern).
    cz_oi, cz_liq, cz_fut, cz_ls = {}, {}, {}, {}
    api_key = os.environ.get("COINALYZE_API_KEY", "")
    if api_key:
        try:
            cz_oi = coinalyze.oi_by_ts(api_key, days=90)
            cz_liq = coinalyze.liquidations_by_ts(api_key, days=90)
            print(f"Coinalyze: {len(cz_oi)} OI-Punkte, {len(cz_liq)} Liq-Punkte.")
        except Exception as exc:  # noqa: BLE001
            print(f"Coinalyze nicht verfuegbar ({exc}) -> Kraken-OI-Fallback.")
        # E16: Futures-Delta + Positionierung. Bewusst in einem EIGENEN try-Block —
        # faellt nur das aus, laeuft die Engine unveraendert weiter wie vor E16
        # (fut_cvd bleibt 0 -> classify_pattern nutzt automatisch den Ersatzweg).
        try:
            cz_fut = coinalyze.fut_delta_by_ts(api_key, days=90)
            cz_ls = coinalyze.long_short_by_ts(api_key, days=90)
            print(f"Coinalyze: {len(cz_fut)} Futures-Delta-Punkte, "
                  f"{len(cz_ls)} Long-Short-Punkte.")
        except Exception as exc:  # noqa: BLE001
            print(f"Coinalyze Futures/Long-Short nicht verfuegbar ({exc}) "
                  f"-> Muster 2 wie bisher ueber Ersatzmerkmale.")

    oi_history = list(oi_history or [])
    if not cz_oi:                          # eigene Snapshot-Historie nur ohne Coinalyze
        try:
            ts, oi = fetch_oi_snapshot()
            if not oi_history or ts - oi_history[-1][0] >= 30 * 60 * 1000:
                oi_history.append([ts, oi])
            oi_history = oi_history[-2000:]
        except Exception as exc:  # noqa: BLE001
            print(f"Kraken-OI nicht verfuegbar ({exc}).")

    use_cz = bool(cz_oi)
    oi_pairs = sorted((int(t), float(v)) for t, v
                      in (cz_oi.items() if use_cz else oi_history))
    first_oi = oi_pairs[0][1] if oi_pairs else 0.0
    # E43.4: OI in Kontrakten (BTC). Jeder Coinalyze-Punkt mit dem Schlusskurs SEINER
    # Kerze umgerechnet, erst danach aufgefuellt - wie backtest.build_series. Der
    # Kraken-Rueckfall bekommt keine Kontrakt-Reihe (0.0 = keine Daten): seine Historie
    # ist lueckenhaft und im Backtest nicht nachstellbar.
    kurs = {int(k[0]): float(k[4]) for k in spot_raw if int(k[6]) <= now_ms}
    btc_pairs = sorted(oi_in_btc({int(t): float(v) for t, v in cz_oi.items()},
                                 kurs).items()) if use_cz else []
    first_btc = btc_pairs[0][1] if btc_pairs else 0.0

    candles: list[Candle] = []
    flow: list[FlowPoint] = []
    spot_cvd = 0.0
    fut_cvd = 0.0                      # E16: kumuliertes Futures-Taker-Delta
    for k in spot_raw:
        if int(k[6]) > now_ms:                                       # nur geschlossene
            continue
        c_ts = int(k[0])
        candles.append(Candle(c_ts, float(k[1]), float(k[2]), float(k[3]), float(k[4])))
        spot_cvd += 2.0 * float(k[10]) - float(k[7])                 # Taker-Delta in USD
        close_ts = c_ts + CANDLE_MS
        # Coinalyze-OI ist je 4h-Kerze (ts = Open-Time) -> direkt per c_ts; Kraken-
        # Snapshot-Historie wird wie bisher zum Kerzenschluss zugeordnet.
        oi_val = _latest_leq(oi_pairs, c_ts if use_cz else close_ts, default=first_oi)
        long_liq, short_liq = cz_liq.get(c_ts, (0.0, 0.0))
        fut_cvd += cz_fut.get(c_ts, 0.0)               # ohne Daten bleibt es 0 = wie bisher
        flow.append(FlowPoint(c_ts, spot_cvd, fut_cvd, oi_val,
                              _latest_leq(funding, close_ts), long_liq, short_liq,
                              cz_ls.get(c_ts, 0.0),
                              _latest_leq(btc_pairs, c_ts, default=first_btc)))
    return candles, flow, oi_history


# ------------------------------------------------------- Einstellungen (E18.1)

# Vorgabewerte fuer JEDEN Schalter, den strategy_core.evaluate kennt. Sie sind mit den
# Defaults dort identisch — wer nichts aendert, bekommt exakt das bisherige Verhalten.
#
# WARUM ES DIESE TABELLE GIBT (Durchsicht 27.08.2026, Befund B1): Vorher reichte
# run_engine nur 11 der Schalter durch. Wer die uebrigen — flush_entry, tp_ladder,
# buy_ladder, conditional_stop, pivot_n, k_atr — in config.json aenderte, bewirkte
# NICHTS, ohne eine Fehlermeldung zu bekommen. Gleichzeitig lasen watch_flush() und
# zonen_vorschau() dieselben Werte sehr wohl aus der Datei: Die Flush-Wache haette
# geschwiegen, waehrend die Engine weiter Flush-Signale erzeugt. Der Test
# test_alle_evaluate_parameter_werden_durchgereicht haelt die Tabelle ab jetzt
# vollstaendig und im Gleichklang mit evaluate.
EVAL_DEFAULTS = {
    "bias_long": True, "bias_short": True,
    "pivot_n": 5, "k_atr": 2.0,
    "flush_entry": "core", "tp_ladder": True,
    "strict_confirm": False, "confluence": False,
    "conditional_stop": False, "buy_ladder": True,
    "release_stale_rest": False, "trail_stop": False,
    "liq_exit": "off", "high_exit": "off", "liq_entry": "off",
    "block_unhealthy": False,
    # E38 (20.09.2026), beide Default aus — siehe strategy_core.evaluate.
    "muster5_entry": False, "muster5_halten": "off",
    # E41 (21.09.2026), alle Default aus - siehe strategy_core.evaluate.
    "stop_puffer_pct": 0.0, "stop_rueckeroberung": 0, "stop_auf_docht": False,
    "confirm_t1": False,
    "cooldown_h": 0.0, "min_stop_pct": 0.0,
    "no_flip": False, "freeze_targets": False,
    "min_bein_pct": 0.0, "bein_wahl": "juengstes", "be_im_plus": False,
    "bein_richtung": "auto", "widerstand_exit": "off",
    "rest_halten": False, "neustart_mit_rest": False,
    "zonen_1d": False, "zonen_nachziehen": False, "pivot_n_1d": 0,
    "trend_filter": False, "trend_ema": 200,
    "ampel_filter": "off",
    # E43.3 (26.09.2026), Default "alt" = bisheriges Verhalten - siehe
    # strategy_core.classify_pattern.
    "muster_cvd": "alt",
    # E43.4 (26.09.2026), Default "usd" = bisheriges Verhalten - siehe
    # strategy_core.oi_aenderung.
    "muster_oi": "usd",
    # A5 (26.09.2026), Default "voll" = bisheriges Verhalten - siehe
    # strategy_core.evaluate (high_exit_hist). Live laedt ohnehin nur main.LIMIT_HAUPT
    # Kerzen, hier also folgenlos - der Unterschied betrifft nur den Backtest.
    "high_exit_hist": "voll",
}


def eval_params(cfg: dict) -> dict:
    """Baut aus config.json die vollstaendigen Parameter fuer evaluate().

    Unbekannte Schluessel in config.json werden ignoriert (dort stehen auch die
    _hinweis-Texte und Schalter, die nur andere Programmteile betreffen). Ein Wert
    mit falschem Typ faellt auf den Vorgabewert zurueck und wird protokolliert,
    statt den ganzen Lauf abzubrechen — Kaiser bearbeitet die Datei von Hand.
    """
    out = {}
    for name, default in EVAL_DEFAULTS.items():
        wert = cfg.get(name, default)
        try:
            if isinstance(default, bool):
                wert = bool(wert)
            elif isinstance(default, int):
                wert = int(wert)
            elif isinstance(default, float):
                wert = float(wert)
        except (TypeError, ValueError):
            print(f"config.json: '{name}' = {wert!r} ist unbrauchbar "
                  f"-> Vorgabewert {default!r}.")
            wert = default
        out[name] = wert
    return out


# --------------------------------------------------------- State-Persistenz

def pos_to_state(pos: Position) -> dict:
    d = {"direction": pos.direction, "pos_state": pos.state.value,
         "last_signal_ts": pos.last_signal_ts, "retrace_extreme": pos.retrace_extreme,
         "tp_rungs": pos.tp_rungs, "dip_buys": pos.dip_buys,
         "buy_rungs": pos.buy_rungs, "entry_ref": pos.entry_ref,
         "entry_pct": pos.entry_pct, "liq_exits": pos.liq_exits,
         "high_exits": pos.high_exits, "liq_entries": pos.liq_entries,
         "last_stop_ts": pos.last_stop_ts, "ziel_extrem": pos.ziel_extrem,
         "be_aktiv": pos.be_aktiv,
         # E41: Die Live-Engine ist bei jedem Lauf ein neuer Prozess. Ohne diese drei
         # Felder finge das Warten auf die Rueckeroberung bei JEDEM Lauf neu an - der
         # Stop kaeme nie, und im Backtest fiele es nicht auf (der rechnet am Stueck).
         "stop_wartet": pos.stop_wartet, "stop_wartet_inv": pos.stop_wartet_inv,
         "stop_geprueft": pos.stop_geprueft,
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
        # E18.3: Steht eine eingefrorene Zielreferenz, zeigt der Chart deren Ziele —
        # sonst zeichnete er andere Linien, als die Engine handelt.
        ref = pos.ziel_extrem if pos.ziel_extrem is not None else pos.retrace_extreme
        if ref is not None:
            d["zones"]["ext1"] = z.ext_target(ref, 1.0)
            d["zones"]["ext2"] = z.ext_target(ref, 1.618)
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
    pos.dip_buys = d.get("dip_buys", 0)
    pos.buy_rungs = d.get("buy_rungs", 0)
    pos.entry_ref = d.get("entry_ref")
    pos.entry_pct = d.get("entry_pct", 0)
    pos.liq_exits = d.get("liq_exits", 0)
    pos.high_exits = d.get("high_exits", 0)
    pos.liq_entries = d.get("liq_entries", 0)
    pos.last_stop_ts = d.get("last_stop_ts", -1)
    pos.ziel_extrem = d.get("ziel_extrem")
    pos.be_aktiv = bool(d.get("be_aktiv", False))
    pos.stop_wartet = int(d.get("stop_wartet", 0) or 0)
    pos.stop_wartet_inv = d.get("stop_wartet_inv")
    pos.stop_geprueft = d.get("stop_geprueft")
    z = d.get("zones")
    if z and "impuls_start" in z:
        imp = Impulse(
            Pivot(0, z.get("impuls_start_ts", 0), z["impuls_start"], z.get("impuls_start_kind", "L")),
            Pivot(0, z.get("impuls_ende_ts", 0), z["impuls_ende"], z.get("impuls_ende_kind", "H")))
        pos.zones = FibZones(imp, z["level_05"], z["gp_upper"], z["gp_lower"],
                             z["level_0786"], z["invalidation"])
    return pos


def zonen_vorschau(candles: list[Candle], cfg: dict | None = None,
                   flow: list[FlowPoint] | None = None) -> dict | None:
    """Die aktuell gueltigen Fib-Zonen — UNABHAENGIG davon, ob eine Position offen ist.

    WARUM DAS NOETIG IST (Kaisers Befund 2026-07-29): Die meisten Kaufsignale nennen ein
    LEVEL, das die Kerze nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze
    gelegen haben. Wer erst nach dem Kerzenschluss reagiert, findet den genannten Preis
    oft nicht mehr am Markt. Der einzige Weg, diese Einstiege zuverlaessig zu bekommen,
    ist eine Limit-Order, die VORHER dort liegt — genau so beschreibt Furkan es im Video
    ("da koennte man dann schon erste Order platzieren").

    Dafuer muessen die Levels sichtbar sein, BEVOR der Kurs sie erreicht. Bisher schrieb
    `pos_to_state` die Zonen nur, wenn eine Position offen war (`pos.zones`); im Zustand
    FLAT stand dort `null` — also genau dann nichts, wenn man den Einstieg vorbereitet.
    Diese Funktion schliesst die Luecke: Sie rechnet die Zonen bei jedem Lauf neu aus der
    Swing-Struktur und legt sie unter `zonen_vorschau` ab. Der Chart zeichnet sie, sobald
    keine Position offen ist.

    Bewusst ein EIGENES Feld statt `zones` zu fuellen: `pos_from_state` liest `zones`,
    um die Zonen einer laufenden Position wiederherzustellen. Wuerde dort im Zustand FLAT
    etwas stehen, haette die Position Zonen, die zu keiner Position gehoeren — verwirrend
    und eine Fehlerquelle fuer spaeter.

    Gibt None zurueck, wenn (noch) kein signifikanter Impuls erkennbar ist.
    """
    # E19: dieselbe Parameter-Aufbereitung wie die Engine — sonst kuendigt die Vorschau
    # Zonen an, die die Engine gar nicht handelt (genau der Fehler aus E18.1).
    par = eval_params(cfg or {})
    piv = find_pivots(candles, n=par["pivot_n"])
    _nur_auf = None
    if par["bein_richtung"] == "bias" and par["bias_long"] != par["bias_short"]:
        _nur_auf = par["bias_long"]
    imp = last_significant_impulse(candles, piv, k_atr=par["k_atr"],
                                   min_bein_pct=par["min_bein_pct"],
                                   bein_wahl=par["bein_wahl"], nur_auf=_nur_auf)
    if imp is None:
        return None
    z = fib_zones(imp)
    # Abstand vom Kern-Einstieg (Golden Pocket) zum Stop — dieselbe Groesse, die
    # min_stop_pct prueft. So sieht man der Ankuendigung schon an, ob die Engine hier
    # ueberhaupt einsteigen wuerde, statt eine Order fuer ein Setup zu legen, das die
    # Engine spaeter verwirft.
    abstand = (abs(z.gp_upper - z.invalidation) / z.gp_upper * 100) if z.gp_upper else None
    # E32: Lage-Angabe auch hier - die Vorschau ist die Nachricht, nach der Kaiser die
    # Limit-Orders setzt. Ohne Position gibt es kein Vergleichsbein, also nur das
    # aktuelle Bein, die Spot-Nachfrage und das Muster.
    _lage = lage_bericht(candles, flow or [], imp=imp,
                         pattern=classify_pattern(candles, flow, muster_cvd=par["muster_cvd"],
                                                  muster_oi=par["muster_oi"])
                         if flow else None,
                         trend_period=par.get("trend_ema", 200))
    # E34: die Ampel fasst die Lage zu EINER Aussage zusammen. Richtung aus dem Bein,
    # denn ohne Position gibt es noch keine eigene - die Vorschau kuendigt genau dieses
    # Setup an. Reine Anzeige, unabhaengig davon, ob ampel_filter an ist.
    # E35: Die Richtung kommt aus dem BIAS, nicht aus dem Bein. Steht live
    # bias_short=false, ist die Engine reine Long-Engine - eine Ampel fuer einen Short,
    # den sie nie eingehen wuerde, waere irrefuehrend. Nur wenn beide Richtungen erlaubt
    # sind, entscheidet das Bein. Siehe docs/PLAN-E35-LAGE-ABRUF.md.
    _ampel = ampel(_lage, long_side=ampel_richtung(
        par["bias_long"], par["bias_short"], imp.up)) if _lage else None
    return {
        "richtung": "LONG" if imp.up else "SHORT",
        "lage": _lage or None,
        "ampel": _ampel,
        "impuls_start": imp.start.price, "impuls_ende": imp.end.price,
        "impuls_start_ts": imp.start.ts, "impuls_ende_ts": imp.end.ts,
        "level_05": z.level_05, "gp_upper": z.gp_upper, "gp_lower": z.gp_lower,
        "level_0786": z.level_0786, "invalidation": z.invalidation,
        "abstand_pct": round(abstand, 2) if abstand is not None else None,
    }


def widerstand_marken(candles: list[Candle], cfg: dict, pos: Position) -> dict | None:
    """Die Widerstandsmarken aus dem Gegen-Bein — das zweite Fib-Raster (E20).

    WARUM (Kaiser 2026-08-27, belegt durch Furkans Video vom 03.08.): Unser Plan nennt
    bisher nur Marken UNTER dem Kurs (Kaufzonen) und die rechnerischen Extension-Ziele
    weit darueber. Was fehlt, sind die Widerstaende dazwischen — die Zone, an der die
    laufende Gegenbewegung als erstes anlaeuft. Genau die nennt Furkan zuerst, wenn er
    ueber Teilgewinne spricht.

    Richtung: bei offener Position deren Richtung, sonst die der Vorschau (bias_long).
    Gibt None zurueck, wenn kein signifikantes Gegen-Bein erkennbar ist.
    """
    par = eval_params(cfg or {})
    long_side = (pos.direction != "SHORT") if pos.direction != "NONE" else par["bias_long"]
    piv = find_pivots(candles, n=par["pivot_n"])
    gz = gegen_zonen(candles, piv, long_side, k_atr=par["k_atr"])
    if gz is None:
        return None
    lo, hi = sorted((gz.gp_upper, gz.gp_lower))
    return {
        "richtung": "LONG" if long_side else "SHORT",
        "bein_start": gz.impulse.start.price, "bein_ende": gz.impulse.end.price,
        "level_05": gz.level_05,
        "gp_von": lo, "gp_bis": hi,
        "level_0786": gz.level_0786,
        "ausbruch": gz.invalidation,      # darueber (Long) ist der Widerstand weg
    }


def positions_plan(candles: list[Candle], flow: list[FlowPoint], cfg: dict,
                   pos: Position) -> dict | None:
    """Alle Marken der laufenden Position auf einen Blick — die Grundlage der Plan-Nachricht.

    WARUM (Kaiser 2026-08-27): Die Signale kommen nach Kerzenschluss und nennen einen Preis,
    den es dann oft nicht mehr gibt (E17: 61 von 214 Signalen betroffen). Fuer die EINSTIEGE
    loest das die Vorschau. Fuer die AUSSTIEGE gab es nichts Vergleichbares — obwohl Furkan
    genau so arbeitet: "Plan ist es, falls wir runterfallen sollten zwischen 61.300 und
    61.000, da werde ich die Position noch mal aufstocken. Wenn wir weiter nach oben gehen
    sollten, werde ich weitere Gewinne realisieren, vor allem unter der 67.000er-Marke."
    (03.08.2026). Mit diesen Zahlen lassen sich Limit-Orders vorlegen.

    ACHTUNG bei Aenderungen: Die Marken hier muessen zu dem passen, was strategy_core
    tatsaechlich ausloest. Der Test `test_plan_marken_stimmen_mit_der_engine_ueberein`
    prueft das an der Extension-1.0-Marke.
    """
    if pos.state == PosState.FLAT or pos.zones is None or not candles:
        return None
    par = eval_params(cfg or {})
    z, cur = pos.zones, candles[-1]
    lang = pos.direction == "LONG"
    piv = find_pivots(candles, n=par["pivot_n"])

    plan: dict = {"richtung": pos.direction, "anteil_pct": pos.entry_pct,
                  "einstand": pos.entry_ref, "kurs": cur.close}
    # E32: Die Lage dazu - Struktur (Preis) und Spot-Nachfrage (Order-Flow). Reine
    # Information; sie aendert keine einzige Marke des Plans. Kaiser am 12.09.2026:
    # "ich bekomme die info zur struktur nur, wenn ich eine nachricht fuer ein nachkauf
    # erhalte. doch das ist zu spaet, weil ich doch die limits vorher setze."
    _nur_auf_p = None
    if par["bein_richtung"] == "bias" and par["bias_long"] != par["bias_short"]:
        _nur_auf_p = par["bias_long"]
    _imp_jetzt = last_significant_impulse(candles, piv, k_atr=par["k_atr"],
                                          min_bein_pct=par["min_bein_pct"],
                                          bein_wahl=par["bein_wahl"], nur_auf=_nur_auf_p)
    _lage = lage_bericht(candles, flow, imp=_imp_jetzt,
                         pos_impulse=z.impulse,
                         pattern=classify_pattern(candles, flow, muster_cvd=par["muster_cvd"],
                                                  muster_oi=par["muster_oi"])
                         if flow else None,
                         trend_period=par.get("trend_ema", 200))
    if _lage:
        plan["lage"] = _lage
        # E34: Richtung aus der LAUFENDEN Position (nicht aus dem aktuellen Bein) -
        # bewertet wird, ob der Plan traegt, den Kaiser gerade abarbeitet.
        _ampel = ampel(_lage, long_side=lang)
        if _ampel:
            plan["ampel"] = _ampel

    # --- wo nachgekauft wird ---
    nach = []
    if pos.state in (PosState.T1, PosState.CORE):
        nach.append({"preis": z.level_0786, "was": "0.786-Zone", "tranche": TRANCHEN["FULL"]})
    if par["buy_ladder"]:
        lo, hi = sorted((z.invalidation, z.level_05))
        nach.append({"zone": [lo, hi], "was": "Kaufleiter: neue Tiefkerze in dieser Zone",
                     "tranche": 15})
    if par["liq_entry"] == "boost" and flow:
        seite = "long" if lang else "short"
        lv = [preis for preis, _m in liq_levels(candles[:-1], flow[:-1], seite)
              if (preis < cur.close if lang else preis > cur.close)]
        for preis in sorted(lv, reverse=lang)[:2]:
            nach.append({"preis": preis, "was": "Liquidationszone", "tranche": 20})

    # --- wo Gewinne mitgenommen werden ---
    raus = []
    gz = gegen_zonen(candles, piv, lang, k_atr=par["k_atr"])
    if gz is not None:
        # Die Widerstandszone steht IMMER im Plan — auch wenn `widerstand_exit` aus ist.
        # Sie ist die Information, wo Angebot sitzt; ob die Engine dort selbst verkauft,
        # ist eine zweite Frage. Kaiser entscheidet mit dieser Zahl selbst, ob er eine
        # Order hinlegt. (Ohne diese Unterscheidung waere die wichtigste neue Marke im
        # Normalbetrieb unsichtbar gewesen.)
        a, b = sorted((gz.gp_upper, gz.gp_lower))
        aktiv = par["widerstand_exit"] != "off"
        raus.append({"zone": [a, b],
                     "was": "Widerstand der Gegenbewegung" if aktiv
                            else "Widerstand der Gegenbewegung — nur Hinweis, die Engine verkauft dort nicht",
                     "tranche": LADDER_TRANCHE if aktiv else 0})
    if par["high_exit"] != "off":
        lvl = next_pivot_beyond(piv, cur.close, lang)
        if lvl is not None:
            ziel = lvl * (1 - HIGH_EXIT_TOL) if lang else lvl * (1 + HIGH_EXIT_TOL)
            raus.append({"preis": ziel, "was": f"kurz unter dem letzten {'Hoch' if lang else 'Tief'} "
                                               f"{lvl:,.0f}".replace(",", "."),
                         "tranche": LADDER_TRANCHE})
    ref = pos.ziel_extrem if pos.ziel_extrem is not None else pos.retrace_extreme
    if ref is not None:
        if par["tp_ladder"]:
            for f in LADDER_FACTORS[pos.tp_rungs:]:
                raus.append({"preis": z.ext_target(ref, f), "was": f"Zwischenziel (Extension {f})",
                             "tranche": LADDER_TRANCHE})
        if pos.state in (PosState.T1, PosState.CORE, PosState.FULL):
            raus.append({"preis": z.ext_target(ref, 1.0), "was": "Ziel 1.0",
                         "tranche": TRANCHEN["TP1"]})
        if pos.state in (PosState.T1, PosState.CORE, PosState.FULL, PosState.TP1):
            raus.append({"preis": z.ext_target(ref, 1.618), "was": "Ziel 1.618",
                         "tranche": TRANCHEN["TP2"]})

    # --- Stop ---
    stop, grund = z.invalidation, "Invalidierung"
    if par["trail_stop"] and (pos.state in (PosState.TP1, PosState.TP2)
                              or pos.tp_rungs > 0 or (par["be_im_plus"] and pos.be_aktiv)):
        if pos.entry_ref is not None:
            besser = pos.entry_ref > stop if lang else pos.entry_ref < stop
            if besser:
                stop, grund = pos.entry_ref, "Einstand (nachgezogen)"

    plan["nachkauf"] = sorted(nach, key=lambda x: -(x.get("preis") or x["zone"][1]) if lang
                              else (x.get("preis") or x["zone"][0]))
    plan["teilgewinn"] = sorted(raus, key=lambda x: (x.get("preis") or x["zone"][0]) * (1 if lang else -1))
    plan["stop"] = {"preis": stop, "grund": grund}
    # E41 (live seit 21.09.2026, Kaisers Rueckeroberungs-Regel): Die Plan-Nachricht sagt
    # "diese Preise kannst du hinterlegen". Stuende dort weiter "Stop bei Kerzenschluss
    # darunter", widerspraeche der Plan der Engine - sie stoppt beim ersten Schluss
    # darunter eben NICHT mehr. Nur fuer den urspruenglichen Stop an der Invalidierung.
    n = int(par.get("stop_rueckeroberung", 0) or 0)
    if n > 0 and grund == "Invalidierung":
        plan["stop"].update({
            "rueckeroberung": n,
            "boden": stop * (1 - DIP_FLOOR_PCT) if lang else stop * (1 + DIP_FLOOR_PCT),
            "geprueft": pos.stop_geprueft == stop,
            "wartet": pos.stop_wartet})
    return plan


def plan_geaendert(alt: dict | None, neu: dict | None, toleranz: float = 0.0025) -> bool:
    """Hat sich am Plan etwas geaendert, das eine neue Nachricht rechtfertigt?

    Nur Preise vergleichen, und die mit Toleranz — die Extension-Ziele wandern mit jedem
    neuen Tief ein Stueck, daraus soll nicht sechsmal am Tag eine Nachricht werden.
    """
    if (alt is None) != (neu is None):
        return neu is not None
    if neu is None:
        return False

    def _marken(p):
        out = []
        for eintrag in p.get("nachkauf", []) + p.get("teilgewinn", []):
            out.append((eintrag["was"], tuple(eintrag.get("zone") or [eintrag["preis"]])))
        out.append(("stop", (p["stop"]["preis"],)))
        return out
    a, n = _marken(alt), _marken(neu)
    # Bewusst NICHT verglichen: der investierte Anteil. Er aendert sich bei jedem Nachkauf
    # und jedem Teilgewinn — das waeren 21 zusaetzliche Nachrichten im Monat, obwohl die
    # MARKEN dieselben geblieben sind. Wie viel investiert ist, steht ohnehin in der
    # Signal-Nachricht. Der Plan meldet sich nur, wenn sich Marken verschieben.
    if [x[0] for x in a] != [x[0] for x in n]:
        return True
    for (_wa, va), (_wn, vn) in zip(a, n):
        for x, y in zip(va, vn):
            if x and abs(y - x) / abs(x) > toleranz:
                return True
    return False


def watch_flush(data_dir: Path = DATA, dry_run: bool = False,
                now_ms: int | None = None, kerzen_roh=None) -> dict | None:
    """Leichter Zwischenlauf: Entwickelt sich in der LAUFENDEN Kerze gerade ein Flush?

    Kaisers Anforderung (2026-07-29): Flushs sind schnelle Bewegungen, oft innerhalb
    einer 4h-Kerze vorbei. Sie lassen sich — anders als die Kaeufe an den Fib-Levels —
    NICHT als Limit-Order vorbereiten. Man muss hinschauen. Die Engine meldet sie aber
    erst nach Kerzenschluss, plus GitHub-Verzoegerung.

    Diese Funktion laeuft alle 15 Minuten und schaut nur nach. Sie erzeugt KEIN Signal,
    fasst state.json NICHT an und taucht im Backtest NICHT auf — die Engine bleibt bei
    ihrem Grundsatz "nur abgeschlossene Kerzen". Der Grund fuer diese Trennung: Die
    Flush-Bedingung verlangt einen Schlusskurs ueber der Invalidierung. Bei einer
    laufenden Kerze steht der nicht fest; ein Signal daraus koennte sich spaeter wieder
    aufloesen. Ein Hinweis darf das, ein Signal nicht.

    Warnt hoechstens EINMAL je Kerze (Merker in watch.json) — sonst kaeme sie bei einem
    laengeren Flush 15-mal. Schreibt watch.json nur, wenn tatsaechlich gewarnt wird;
    ohne Warnung bleibt das Repo unberuehrt.

    Prueft dieselben Bedingungen wie die Engine, damit nicht vor etwas gewarnt wird,
    das die Engine spaeter ohnehin verwirft: nur bei FLAT, nur Long, nur wenn
    flush_entry aktiv ist und der Stop-Mindestabstand eingehalten waere.
    """
    now_ms = now_ms or int(time.time() * 1000)
    raw = kerzen_roh if kerzen_roh is not None else _get_json(SPOT_URL)

    def _c(k):
        return Candle(int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]))

    fertig = [_c(k) for k in raw if int(k[6]) <= now_ms]
    laufend = next((_c(k) for k in raw if int(k[6]) > now_ms), None)
    if laufend is None or len(fertig) < 30:
        return None

    cfg = {}
    cfg_path = data_dir / "config.json"
    if cfg_path.exists():
        try:
            cfg = {k: v for k, v in json.loads(cfg_path.read_text(encoding="utf-8")).items()
                   if not k.startswith("_")}
        except Exception as exc:  # noqa: BLE001
            print(f"config.json nicht lesbar ({exc}) -> Standardwerte.")
    if cfg.get("flush_entry", "core") == "off" or not cfg.get("flush_wache", True):
        return None

    # Nur wenn KEINE Position offen ist — der Flush-Einstieg feuert nur aus FLAT.
    state_path = data_dir / "state.json"
    if state_path.exists():
        try:
            if json.loads(state_path.read_text(encoding="utf-8")).get("pos_state") != "FLAT":
                return None
        except Exception:  # noqa: BLE001
            pass

    z = zonen_vorschau(fertig, cfg)
    if z is None or z["richtung"] != "LONG" or not cfg.get("bias_long", True):
        return None

    # Dieselbe Bedingung wie in strategy_core.evaluate, nur auf der laufenden Kerze:
    # Tief durchschlaegt das Golden Pocket, Kurs noch ueber der Invalidierung.
    if not (laufend.low < z["gp_lower"] and laufend.close > z["invalidation"]):
        return None
    # Mindest-Stopabstand wie die Engine pruefen (sonst Warnung vor einem Setup,
    # das die Engine anschliessend verwirft).
    mind = float(cfg.get("min_stop_pct", 0) or 0)
    puffer = (laufend.close - z["invalidation"]) / laufend.close
    if mind > 0 and puffer < mind:
        return None

    watch_path = data_dir / "watch.json"
    alt = {}
    if watch_path.exists():
        try:
            alt = json.loads(watch_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    if alt.get("gewarnt_ts") == laufend.ts:
        return None                                      # fuer diese Kerze schon gewarnt

    schluss_ms = laufend.ts + CANDLE_MS
    w = {
        "gewarnt_ts": laufend.ts,
        "gewarnt_um": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "preis": laufend.close,
        "gp_lower": z["gp_lower"],
        "invalidation": z["invalidation"],
        "puffer_pct": round(puffer * 100, 2),
        "schluss_utc": datetime.utcfromtimestamp(schluss_ms / 1000).strftime("%H:%M UTC"),
        "aufgeloest": False,
    }
    send_text(format_flush_warnung(w), dry_run=dry_run)
    watch_path.write_text(json.dumps(w, indent=1), encoding="utf-8")
    print(f"Flush-Warnung gesendet: Kurs {laufend.close:.0f}, GP {z['gp_lower']:.0f}, "
          f"Puffer {w['puffer_pct']} %")
    return w


# ------------------------------------------------------------ Orchestrierung

def lage_abruf(fetch=fetch_market_data, data_dir: Path = DATA,
               dry_run: bool = False, sth=sth_kostenbasis) -> dict | None:
    """Die Lage auf Knopfdruck — unter der Annahme einer LONG-Position (E35).

    Anlass (Kaiser 17.09.2026): *"Zuletzt wurde der Plan ausgestoppt ... Ich habe aber
    den Stoploss nicht als Limit eingestellt und mein Trade laeuft jetzt weiter. Jetzt
    wuerde ich gerne zwischendurch sehen, wie die Struktur aussieht."*

    Die Engine steht auf FLAT, er ist noch drin. Dieser Abruf schliesst die Luecke,
    ohne den Zustand zu verbiegen: Er rechnet ausdruecklich unter einer ANNAHME und
    sagt das in der Nachricht auch.

    Drei Zusicherungen, damit der Abruf nie Schaden anrichten kann:
      - Er sucht gezielt ein AUFWAERTS-Bein (nur_auf=True), unabhaengig davon, was
        bein_richtung sagt. Ein Abwaerts-Bein bedeutet fuer einen Long nichts; findet
        sich kein Aufwaerts-Bein, sagt die Nachricht genau das.
      - Er fasst state.json NICHT an und erzeugt KEIN Signal — wie `--watch`.
      - Er sendet IMMER, ohne Dedupe. Der Abruf ist ja gerade der Wunsch, jetzt zu
        sehen, wie es steht.
    """
    cfg = {}
    cfg_path = data_dir / "config.json"
    if cfg_path.exists():
        try:
            cfg = {k: v for k, v in json.loads(cfg_path.read_text(encoding="utf-8")).items()
                   if not k.startswith("_")}
        except Exception as exc:  # noqa: BLE001
            print(f"config.json nicht lesbar ({exc}) -> Standardwerte.")

    candles, flow, _oi = fetch(None)
    if not candles:
        print("Keine Kerzen erhalten — Abbruch.")
        return None

    par = eval_params(cfg)
    piv = find_pivots(candles, n=par["pivot_n"])
    # nur_auf=True: gesucht wird das Bein, auf dem eine LONG-Position laeuft.
    imp = last_significant_impulse(candles, piv, k_atr=par["k_atr"],
                                   min_bein_pct=par["min_bein_pct"],
                                   bein_wahl=par["bein_wahl"], nur_auf=True)
    lage = lage_bericht(candles, flow or [], imp=imp,
                        pattern=classify_pattern(candles, flow, muster_cvd=par["muster_cvd"],
                                                 muster_oi=par["muster_oi"])
                        if flow else None,
                        trend_period=par.get("trend_ema", 200))
    out = {
        "kurs": candles[-1].close,
        "bein": None,
        # E36: Furkans Rohwerte - dieselben Groessen, aus denen das Muster entsteht.
        # Reine Anzeige; evaluate() sieht davon nichts.
        "orderflow": orderflow_detail(candles, flow or []),
        "fenster_h": OF_FENSTER * 4,

        "lage": lage or None,
        # Die Annahme ist Long — deshalb hier fest, nicht ueber den Bias.
        "ampel": ampel(lage, long_side=True) if lage else None,
        # E40 (Kaiser 21.09.2026): STH-Kostenbasis als Zeile - Anzeige, keine Regel.
        "sth": None,
    }
    try:
        out["sth"] = sth()
    except Exception as exc:  # noqa: BLE001
        print(f"STH-Kostenbasis nicht abrufbar ({exc}) - Zeile entfaellt.")
    if imp is not None:
        z = fib_zones(imp)
        out.update({
            "bein": [imp.start.price, imp.end.price],
            "level_05": z.level_05, "gp_upper": z.gp_upper, "gp_lower": z.gp_lower,
            "level_0786": z.level_0786, "invalidation": z.invalidation,
        })
    send_lage(out, candles[-1].ts, dry_run=dry_run)
    return out


def e41_meldung(pos: Position, wartete_vorher: int, sigs: list, kerze: Candle,
                rueckeroberung: int, marke_vorher: float | None = None) -> dict | None:
    """E41: Was hat die Rueckeroberungs-Regel in dieser Kerze getan? (fuer Telegram)

    Ohne diese Meldung sieht man bei einem knappen Schluss unter der Marke: nichts. Kein
    Stop, keine Nachricht - und wuesste nicht, ob die Engine wartet oder etwas uebersehen
    hat. Zwei Faelle werden gemeldet:
      "wartet"  Schluss unter der Marke, noch kein Stop.
      "zurueck" Die Marke wurde zurueckerobert und gilt ab jetzt als geprueft.
    Der Stop selbst braucht keine eigene Meldung - seine Signalnachricht nennt den Grund.
    `marke_vorher` ist die Marke, auf deren Rueckeroberung gewartet wurde: Nur wenn
    GENAU sie jetzt als geprueft gilt, war es eine Rueckeroberung - nicht, wenn das
    Warten nur endete, weil die Zonen nachgezogen wurden.
    """
    if any(s.type in (SignalType.STOPLOSS, SignalType.SHORT_STOPLOSS) for s in sigs):
        return None
    lang = pos.direction != "SHORT"
    if pos.stop_wartet > wartete_vorher and pos.stop_wartet_inv:
        marke = pos.stop_wartet_inv
        return {"art": "wartet", "ts": kerze.ts, "kurs": kerze.close, "marke": marke,
                "lang": lang, "kerze_nr": pos.stop_wartet, "von": rueckeroberung,
                "noch": rueckeroberung - pos.stop_wartet + 1,
                "boden": marke * (1 - DIP_FLOOR_PCT) if lang else marke * (1 + DIP_FLOOR_PCT)}
    if (wartete_vorher > 0 and pos.stop_wartet == 0 and pos.state != PosState.FLAT
            and pos.stop_geprueft is not None
            and (marke_vorher is None or pos.stop_geprueft == marke_vorher)):
        return {"art": "zurueck", "ts": kerze.ts, "kurs": kerze.close,
                "marke": pos.stop_geprueft, "lang": lang}
    return None


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

    # Einstellungen: bevorzugt aus config.json (wird von der Engine NIE ueberschrieben ->
    # konfliktfrei aenderbar), sonst aus dem alten state, sonst Default.
    cfg = old_state.get("config", {"bias_long": True, "bias_short": True})
    cfg_path = data_dir / "config.json"
    if cfg_path.exists():
        try:
            loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg = {**cfg, **{k: v for k, v in loaded.items() if not k.startswith("_")}}
        except Exception as exc:  # noqa: BLE001
            print(f"config.json nicht lesbar ({exc}) -> alte Einstellungen.")
    new_signals: list[dict] = []
    params = eval_params(cfg)
    # Nachholen: alle Kerzen, die neuer sind als der letzte verarbeitete Stand
    e41_meldungen: list[dict] = []
    for i, c in enumerate(candles):
        if c.ts <= pos.last_signal_ts:
            continue
        _wartete, _marke = pos.stop_wartet, pos.stop_wartet_inv
        sigs = evaluate(candles[:i + 1], flow[:i + 1], pos, **params)
        new_signals += [s.to_dict() for s in sigs]
        m = e41_meldung(pos, _wartete, sigs, c, int(params.get("stop_rueckeroberung", 0)),
                        marke_vorher=_marke)
        if m:
            e41_meldungen.append(m)

    # Historie fortschreiben
    hist = {"signals": []}
    if signals_path.exists():
        h = json.loads(signals_path.read_text(encoding="utf-8"))
        if not h.get("demo"):
            hist = h
    hist["signals"] = (hist.get("signals", []) + new_signals)[-500:]

    state = pos_to_state(pos)
    state["widerstand"] = widerstand_marken(candles, cfg, pos)
    # Plan zur laufenden Position (E20). Wird nur gesendet, wenn sich eine Marke aendert —
    # sonst kaeme sechsmal taeglich dieselbe Liste.
    plan = positions_plan(candles, flow, cfg, pos)
    state["plan"] = plan
    if cfg.get("plan_telegram", True) and plan_geaendert((old_state or {}).get("plan"), plan):
        send_plan(plan, dry_run=dry_run)
        print(f"Plan gesendet: {len(plan.get('nachkauf', []))} Nachkauf-, "
              f"{len(plan.get('teilgewinn', []))} Teilgewinn-Marken.")
    state["config"] = cfg
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    state["last_close"] = candles[-1].close
    vorschau = zonen_vorschau(candles, cfg, flow)
    state["zonen_vorschau"] = vorschau

    # --- Vorschau-Ankuendigung per Telegram (2026-07-29) -----------------------------
    # Nur bei NEUER Struktur, nicht bei jedem Lauf — sonst kaeme sechsmal taeglich
    # dieselbe Nachricht. Als "neu" gilt ein anderer Referenz-Impuls (andere Pivots).
    # Erkennung ueber die Zeitstempel der Pivots, nicht ueber die Preise: Zwei Impulse
    # koennen zufaellig aehnliche Preise haben, aber nie dieselben Zeitpunkte.
    alt = (old_state or {}).get("zonen_vorschau") or {}
    neue_struktur = vorschau is not None and (
        alt.get("impuls_start_ts"), alt.get("impuls_ende_ts")
    ) != (vorschau["impuls_start_ts"], vorschau["impuls_ende_ts"])
    if neue_struktur and cfg.get("vorschau_telegram", True):
        send_vorschau(vorschau, candles[-1].ts, dry_run=dry_run)
        print(f"Vorschau gesendet: {vorschau['richtung']}, GP "
              f"{vorschau['gp_lower']:.0f}-{vorschau['gp_upper']:.0f}, "
              f"Stop-Abstand {vorschau['abstand_pct']} %")

    state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
    signals_path.write_text(json.dumps(hist, indent=1), encoding="utf-8")
    oi_path.write_text(json.dumps(oi_history), encoding="utf-8")

    # --- Aufloesung einer offenen Flush-Warnung (Kaiser 2026-07-29) ------------------
    # Ohne diese Rueckmeldung bliebe jede Warnung in der Luft haengen: Man wuesste nie,
    # ob man etwas verpasst hat oder ob sich die Sache erledigt hat. Ausgeloest wird sie,
    # sobald die gewarnte Kerze abgeschlossen ist.
    watch_path = data_dir / "watch.json"
    if watch_path.exists():
        try:
            w = json.loads(watch_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            w = {}
        offen = w and not w.get("aufgeloest") and w.get("gewarnt_ts") is not None
        if offen and any(c.ts == w["gewarnt_ts"] for c in candles):
            # Die gewarnte Kerze ist jetzt abgeschlossen -> Ergebnis feststellen.
            bestaetigt = any(s["ts"] == w["gewarnt_ts"] and s.get("tag") == "FLUSH"
                             for s in new_signals)
            send_text(format_flush_aufloesung(w, bestaetigt), dry_run=dry_run)
            w["aufgeloest"] = True
            w["bestaetigt"] = bestaetigt
            watch_path.write_text(json.dumps(w, indent=1), encoding="utf-8")
            print(f"Flush-Warnung aufgeloest: {'bestaetigt' if bestaetigt else 'nicht bestaetigt'}")

    # E41: VOR den Signalen - holt ein Lauf mehrere Kerzen nach, steht die Wartemeldung
    # vor dem Stop, der ihr folgt.
    for m in e41_meldungen:
        send_text(format_stop_rueckeroberung(m), dry_run=dry_run)
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


def resend_all_signals(data_dir: Path = DATA):
    """Sendet ALLE gespeicherten Kauf-/Verkaufstrigger erneut an Telegram (auf Knopfdruck)."""
    signals_path = data_dir / "signals.json"
    if not signals_path.exists():
        print("Keine signals.json vorhanden — nichts zu senden.")
        return []
    hist = json.loads(signals_path.read_text(encoding="utf-8"))
    sigs = sorted(hist.get("signals", []), key=lambda s: s["ts"])
    dry = not (os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))
    send_signals([{"ts": int(time.time() * 1000), "type": "WARNUNG",
                   "label": f"NEUSENDUNG: {len(sigs)} Trigger (Historie, keine neuen Signale)",
                   "price": 0.0, "tranche_pct": 0,
                   "reason": "Ab hier folgen alle bisherigen Kauf-/Verkaufstrigger noch einmal."}],
                  dry_run=dry)
    send_signals(sigs, dry_run=dry)
    print(f"{len(sigs)} Trigger erneut gesendet (dry_run={dry}).")
    return sigs


if __name__ == "__main__":
    if "--test-telegram" in sys.argv:
        send_testnachricht()
    elif "--watch" in sys.argv:
        # Leichter Zwischenlauf (alle 15 Min): nur nach sich entwickelnden Flushs
        # schauen. Fasst state.json nicht an, erzeugt keine Signale.
        watch_flush(dry_run="--dry-run" in sys.argv or not os.environ.get("TELEGRAM_BOT_TOKEN"))
    elif "--lage" in sys.argv:
        # E35: Lage auf Knopfdruck, unter Annahme einer Long-Position. Erzeugt kein
        # Signal, fasst state.json nicht an.
        lage_abruf(dry_run="--dry-run" in sys.argv or not os.environ.get("TELEGRAM_BOT_TOKEN"))
    elif "--resend-all" in sys.argv:
        resend_all_signals()
    else:
        run_engine(dry_run="--dry-run" in sys.argv or not os.environ.get("TELEGRAM_BOT_TOKEN"))
