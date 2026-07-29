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

import coinalyze
from strategy_core import (Candle, FibZones, FlowPoint, Impulse, Pivot, PosState,
                           Position, evaluate, fib_zones, find_pivots,
                           last_significant_impulse)
from telegram_notify import (format_flush_aufloesung, format_flush_warnung,
                             send_signals, send_text, send_vorschau)

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
                              cz_ls.get(c_ts, 0.0)))
    return candles, flow, oi_history


# --------------------------------------------------------- State-Persistenz

def pos_to_state(pos: Position) -> dict:
    d = {"direction": pos.direction, "pos_state": pos.state.value,
         "last_signal_ts": pos.last_signal_ts, "retrace_extreme": pos.retrace_extreme,
         "tp_rungs": pos.tp_rungs, "dip_buys": pos.dip_buys,
         "buy_rungs": pos.buy_rungs, "entry_ref": pos.entry_ref,
         "entry_pct": pos.entry_pct, "liq_exits": pos.liq_exits,
         "high_exits": pos.high_exits, "liq_entries": pos.liq_entries,
         "last_stop_ts": pos.last_stop_ts, "zones": None}
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
    pos.dip_buys = d.get("dip_buys", 0)
    pos.buy_rungs = d.get("buy_rungs", 0)
    pos.entry_ref = d.get("entry_ref")
    pos.entry_pct = d.get("entry_pct", 0)
    pos.liq_exits = d.get("liq_exits", 0)
    pos.high_exits = d.get("high_exits", 0)
    pos.liq_entries = d.get("liq_entries", 0)
    pos.last_stop_ts = d.get("last_stop_ts", -1)
    z = d.get("zones")
    if z and "impuls_start" in z:
        imp = Impulse(
            Pivot(0, z.get("impuls_start_ts", 0), z["impuls_start"], z.get("impuls_start_kind", "L")),
            Pivot(0, z.get("impuls_ende_ts", 0), z["impuls_ende"], z.get("impuls_ende_kind", "H")))
        pos.zones = FibZones(imp, z["level_05"], z["gp_upper"], z["gp_lower"],
                             z["level_0786"], z["invalidation"])
    return pos


def zonen_vorschau(candles: list[Candle], cfg: dict | None = None) -> dict | None:
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
    cfg = cfg or {}
    piv = find_pivots(candles, n=int(cfg.get("pivot_n", 5)))
    imp = last_significant_impulse(candles, piv, k_atr=float(cfg.get("k_atr", 2.0)))
    if imp is None:
        return None
    z = fib_zones(imp)
    # Abstand vom Kern-Einstieg (Golden Pocket) zum Stop — dieselbe Groesse, die
    # min_stop_pct prueft. So sieht man der Ankuendigung schon an, ob die Engine hier
    # ueberhaupt einsteigen wuerde, statt eine Order fuer ein Setup zu legen, das die
    # Engine spaeter verwirft.
    abstand = (abs(z.gp_upper - z.invalidation) / z.gp_upper * 100) if z.gp_upper else None
    return {
        "richtung": "LONG" if imp.up else "SHORT",
        "impuls_start": imp.start.price, "impuls_ende": imp.end.price,
        "impuls_start_ts": imp.start.ts, "impuls_ende_ts": imp.end.ts,
        "level_05": z.level_05, "gp_upper": z.gp_upper, "gp_lower": z.gp_lower,
        "level_0786": z.level_0786, "invalidation": z.invalidation,
        "abstand_pct": round(abstand, 2) if abstand is not None else None,
    }


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
    # Nachholen: alle Kerzen, die neuer sind als der letzte verarbeitete Stand
    for i, c in enumerate(candles):
        if c.ts <= pos.last_signal_ts:
            continue
        sigs = evaluate(candles[:i + 1], flow[:i + 1], pos,
                        bias_long=cfg.get("bias_long", True),
                        bias_short=cfg.get("bias_short", True),
                        release_stale_rest=cfg.get("release_stale_rest", False),
                        trail_stop=cfg.get("trail_stop", False),
                        liq_exit=cfg.get("liq_exit", "off"),
                        high_exit=cfg.get("high_exit", "off"),
                        liq_entry=cfg.get("liq_entry", "off"),
                        block_unhealthy=cfg.get("block_unhealthy", False),
                        confirm_t1=cfg.get("confirm_t1", False),
                        cooldown_h=cfg.get("cooldown_h", 0),
                        min_stop_pct=cfg.get("min_stop_pct", 0))
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
    vorschau = zonen_vorschau(candles, cfg)
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
    elif "--resend-all" in sys.argv:
        resend_all_signals()
    else:
        run_engine(dry_run="--dry-run" in sys.argv or not os.environ.get("TELEGRAM_BOT_TOKEN"))
