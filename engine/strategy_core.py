"""Kern-Engine der Order-Flow-Strategie (nach Furkan Yildirim).

Offline-Modul ohne Netzabhaengigkeit (E4a). Regeln: docs/STRATEGIE.md.
Alle Preise in USD. Timeframe-agnostisch: arbeitet auf einer Liste
abgeschlossener Kerzen (primaer 4h) + optionalen Order-Flow-Serien.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

# ---------------------------------------------------------------- Datentypen


@dataclass(frozen=True)
class Candle:
    ts: int          # Open-Time in ms (UTC), eindeutiger Schluessel
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class FlowPoint:
    """Order-Flow-Daten je Kerze (aggregiert ueber Boersen)."""
    ts: int
    spot_cvd: float      # kumuliertes Spot-Delta (USD)
    fut_cvd: float       # kumuliertes Futures-Delta (USD)
    oi: float            # Open Interest (USD)
    funding: float       # 8h-Funding-Rate, Durchschnitt (z. B. 0.0001 = 0.01 %)


class Pattern(Enum):
    """Der Order-Flow-Kompass (STRATEGIE.md Abschnitt 3)."""
    GESUNDER_TREND = 1
    DERIVATE_PUMP = 2
    SHORT_COVERING = 3
    CAPITULATION_RESET = 4
    NEUTRAL = 0


class SignalType(Enum):
    KAUF_1 = "KAUF 1 (Teilposition am 0.5-Level)"
    KAUF_2 = "KAUF 2 (Kernposition im Golden Pocket)"
    NACHKAUF = "NACHKAUF (0.786-Zone)"
    TEILVERKAUF_1 = "TEILVERKAUF 1 (Extension 1.0)"
    TEILVERKAUF_2 = "TEILVERKAUF 2 (Extension 1.618)"
    VERKAUF_REST = "VERKAUF Rest (Muster/Divergenz am Ziel)"
    STOPLOSS = "STOPLOSS"
    WARNUNG = "WARNUNG (Derivate-Pump aktiv)"
    # Short-Seite (spiegelbildlich)
    SHORT_1 = "SHORT 1 (Teilposition am 0.5-Level)"
    SHORT_2 = "SHORT 2 (Kernposition im Golden Pocket)"
    SHORT_NACHLEGEN = "SHORT NACHLEGEN (0.786-Zone)"
    SHORT_TP_1 = "SHORT TEILGEWINN 1 (Extension 1.0)"
    SHORT_TP_2 = "SHORT TEILGEWINN 2 (Extension 1.618)"
    SHORT_COVER_REST = "SHORT Rest schliessen"
    SHORT_STOPLOSS = "SHORT STOPLOSS"


@dataclass
class Signal:
    ts: int
    type: SignalType
    price: float
    tranche_pct: int          # Anteil der Gesamtposition in %
    reason: str               # Begruendung (Muster/Level) fuer die Telegram-Nachricht
    stop_ref: Optional[float] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.name
        d["label"] = self.type.value
        return d


@dataclass(frozen=True)
class Pivot:
    idx: int
    ts: int
    price: float
    kind: str  # "H" oder "L"


@dataclass
class Impulse:
    """Letzter signifikanter Impuls: Basis fuer Fib-Zonen."""
    start: Pivot
    end: Pivot

    @property
    def up(self) -> bool:
        return self.end.price > self.start.price

    @property
    def range(self) -> float:
        return abs(self.end.price - self.start.price)


@dataclass
class FibZones:
    """Alle relevanten Zonen eines Impulses (Richtung folgt dem Impuls)."""
    impulse: Impulse
    level_05: float
    gp_upper: float   # 0.618
    gp_lower: float   # 0.65 (bei Long unterhalb von 0.618)
    level_0786: float
    invalidation: float  # 1.0 = Startpunkt des Impulses

    def ext_target(self, retrace_extreme: float, factor: float = 1.0) -> float:
        """Extension-Ziel vom Retracement-Extrem aus (1.0 = gleiche Bewegung)."""
        sign = 1.0 if self.impulse.up else -1.0
        return retrace_extreme + sign * factor * self.impulse.range


# ------------------------------------------------------------------ Analyse


def atr(candles: list[Candle], period: int = 14) -> float:
    """Average True Range der letzten `period` Kerzen (einfacher Durchschnitt)."""
    if len(candles) < 2:
        return 0.0
    trs = []
    for prev, cur in zip(candles[-period - 1:-1], candles[-period:]):
        trs.append(max(cur.high - cur.low,
                       abs(cur.high - prev.close),
                       abs(cur.low - prev.close)))
    return sum(trs) / len(trs) if trs else 0.0


def find_pivots(candles: list[Candle], n: int = 5) -> list[Pivot]:
    """Pivot-Hochs/-Tiefs mit n Kerzen Bestaetigung links UND rechts.

    Ein Pivot gilt erst als bestaetigt, wenn n Folgekerzen vorliegen —
    dadurch 'wandern' die Zonen erst mit bestaetigter neuer Struktur
    (dynamische Golden Pockets, STRATEGIE.md 4.1).
    """
    pivots: list[Pivot] = []
    for i in range(n, len(candles) - n):
        c = candles[i]
        window = candles[i - n:i] + candles[i + 1:i + n + 1]
        if all(c.high >= w.high for w in window):
            pivots.append(Pivot(i, c.ts, c.high, "H"))
        if all(c.low <= w.low for w in window):
            pivots.append(Pivot(i, c.ts, c.low, "L"))
    # bei Duplikaten (H und L derselben Kerze) Reihenfolge stabil halten
    pivots.sort(key=lambda p: (p.idx, p.kind))
    # aufeinanderfolgende gleiche Typen: nur das Extrem behalten
    cleaned: list[Pivot] = []
    for p in pivots:
        if cleaned and cleaned[-1].kind == p.kind:
            keep = (p.price >= cleaned[-1].price) if p.kind == "H" else (p.price <= cleaned[-1].price)
            if keep:
                cleaned[-1] = p
        else:
            cleaned.append(p)
    return cleaned


def last_significant_impulse(candles: list[Candle], pivots: list[Pivot],
                             k_atr: float = 3.0, min_pct: float = 0.03) -> Optional[Impulse]:
    """Juengster abgeschlossener Impuls (Pivot->Pivot), der signifikant ist.

    Signifikant = Spanne >= k_atr * ATR(14) ODER >= min_pct des Startpreises.
    Der Zeitabschnitt ergibt sich damit aus der Swing-Struktur selbst
    (kein starres Lookback-Fenster).
    """
    if len(pivots) < 2:
        return None
    a = atr(candles)
    for i in range(len(pivots) - 1, 0, -1):
        start, end = pivots[i - 1], pivots[i]
        if start.kind == end.kind:
            continue
        rng = abs(end.price - start.price)
        if rng >= k_atr * a or rng >= min_pct * start.price:
            return Impulse(start, end)
    return None


def fib_zones(imp: Impulse) -> FibZones:
    """Fib-Retracement-Zonen des Impulses (Levels aus dem Video: 0.5/0.618/0.65/0.786)."""
    h, l = (imp.end.price, imp.start.price) if imp.up else (imp.start.price, imp.end.price)
    rng = h - l
    if imp.up:  # Retracement vom Hoch nach unten
        lv = lambda r: h - r * rng
    else:       # Short: Retracement vom Tief nach oben
        lv = lambda r: l + r * rng
    return FibZones(
        impulse=imp,
        level_05=lv(0.5),
        gp_upper=lv(0.618),
        gp_lower=lv(0.65),
        level_0786=lv(0.786),
        invalidation=imp.start.price,
    )


# --------------------------------------------------- Order-Flow-Kompass


def _slope(vals: list[float]) -> float:
    """Relative Veraenderung ueber das Fenster (robust gegen Skalenunterschiede)."""
    if len(vals) < 2 or vals[0] == 0:
        return 0.0
    return (vals[-1] - vals[0]) / abs(vals[0])


def classify_pattern(candles: list[Candle], flow: list[FlowPoint],
                     window: int = 12,
                     oi_wipeout_pct: float = 0.05,
                     sharp_move_pct: float = 0.04,
                     funding_hot: float = 0.0001) -> Pattern:
    """Ordnet die juengste Marktphase einem der 4 Kompass-Muster zu.

    `window` = Anzahl Kerzen (12 x 4h = 2 Tage). Schwellen sind Startwerte,
    Kalibrierung in E4b. Liquidations-Proxy: OI-Abfall + scharfe Preisbewegung.
    """
    if len(candles) < window or len(flow) < window:
        return Pattern.NEUTRAL
    c, f = candles[-window:], flow[-window:]
    price_chg = (c[-1].close - c[0].close) / c[0].close
    spot = _slope([p.spot_cvd for p in f])
    fut = _slope([p.fut_cvd for p in f])
    oi_chg = (f[-1].oi - f[0].oi) / f[0].oi if f[0].oi else 0.0
    funding_now = f[-1].funding
    funding_rising = f[-1].funding > f[0].funding

    # 4: Capitulation/Flush + Reset — Preis scharf runter, OI-Wipeout, Spot-CVD dreht
    if (price_chg <= -sharp_move_pct and oi_chg <= -oi_wipeout_pct):
        spot_turning = len(flow) >= 3 and flow[-1].spot_cvd > flow[-3].spot_cvd
        if spot_turning:
            return Pattern.CAPITULATION_RESET
    # 3: Short-Covering — Preis hoch, OI runter
    if price_chg >= sharp_move_pct / 2 and oi_chg <= -0.02:
        return Pattern.SHORT_COVERING
    # 2: Derivate-Pump — Futures-CVD stark hoch, Spot flach/runter, OI deutlich hoch, Funding zieht an
    has_fut = any(p.fut_cvd for p in f)
    if has_fut:
        if (price_chg > 0 and fut > 0 and spot <= fut / 3 and oi_chg >= 0.03
                and (funding_rising or funding_now >= funding_hot)):
            return Pattern.DERIVATE_PUMP
    else:
        # Ohne Futures-CVD-Quelle (US-Geo-Block): Pump-Erkennung ueber die uebrigen
        # Merkmale aus Furkans Notizen — OI deutlich hoch, Funding zieht an, Spot flach
        if (price_chg > 0 and oi_chg >= 0.03 and spot <= 0.01
                and (funding_rising or funding_now >= funding_hot)):
            return Pattern.DERIVATE_PUMP
    # 1: Gesunder Trend — Preis hoch, Spot-CVD traegt, Funding unauffaellig
    if (price_chg > 0 and spot > 0 and abs(funding_now) < funding_hot
            and 0 <= oi_chg <= 0.10):
        return Pattern.GESUNDER_TREND
    return Pattern.NEUTRAL


# --------------------------------------------------- Zustandsmaschine


class PosState(Enum):
    FLAT = "FLAT"
    T1 = "T1"        # 25 % (0.5-Level)
    CORE = "CORE"    # 75 % (Golden Pocket)
    FULL = "FULL"    # 100 % (0.786-Nachkauf)
    TP1 = "TP1"      # nach Teilverkauf 1
    TP2 = "TP2"      # nach Teilverkauf 2


@dataclass
class Position:
    direction: str = "NONE"          # "LONG" | "SHORT" | "NONE"
    state: PosState = PosState.FLAT
    zones: Optional[FibZones] = None
    retrace_extreme: Optional[float] = None  # tiefster/hoechster Punkt der Korrektur
    last_signal_ts: int = -1                 # Dedupe: nur 1 Signal-Batch je Kerze


TRANCHEN = {"T1": 25, "CORE": 50, "FULL": 25, "TP1": 40, "TP2": 40}


def evaluate(candles: list[Candle], flow: list[FlowPoint], pos: Position,
             bias_long: bool = True, bias_short: bool = True,
             pivot_n: int = 5, k_atr: float = 2.0) -> list[Signal]:
    # Defaults kalibriert per Backtest 2026-07-22 (BACKTEST.md): n=5, k=2.0 beste
    # Kombination (Recall 45 %, Kaufseite 65 %, Praezision 54 %).
    """Bewertet die juengste ABGESCHLOSSENE Kerze und liefert neue Signale.

    Idempotent: dieselbe Kerze (ts) erzeugt nie zweimal Signale (pos.last_signal_ts).
    `pos` wird mutiert (Zustandsmaschine); Aufrufer persistiert `pos` in state.json.
    """
    if not candles:
        return []
    cur = candles[-1]
    if cur.ts <= pos.last_signal_ts:
        return []

    signals: list[Signal] = []
    pattern = classify_pattern(candles, flow) if flow else Pattern.NEUTRAL
    pivots = find_pivots(candles, n=pivot_n)
    imp = last_significant_impulse(candles, pivots, k_atr=k_atr)

    # --- Einstiegs-Logik (FLAT): Referenz-Impuls noetig
    if pos.state == PosState.FLAT and imp is not None:
        z = fib_zones(imp)
        if imp.up and bias_long and pattern != Pattern.DERIVATE_PUMP:
            if cur.low <= z.level_05 and cur.low > z.gp_upper:
                pos.direction, pos.state, pos.zones = "LONG", PosState.T1, z
                pos.retrace_extreme = cur.low
                signals.append(Signal(cur.ts, SignalType.KAUF_1, z.level_05, TRANCHEN["T1"],
                                      f"0.5-Retracement des Impulses {imp.start.price:.0f}->{imp.end.price:.0f}",
                                      stop_ref=z.invalidation))
            elif z.gp_lower <= cur.low <= z.gp_upper:
                ok = (pattern == Pattern.CAPITULATION_RESET
                      or (flow and flow[-1].funding <= 0)
                      or (len(flow) >= 3 and flow[-1].spot_cvd > flow[-3].spot_cvd))
                if ok:
                    pos.direction, pos.state, pos.zones = "LONG", PosState.CORE, z
                    pos.retrace_extreme = cur.low
                    signals.append(Signal(cur.ts, SignalType.KAUF_2, z.gp_upper,
                                          TRANCHEN["T1"] + TRANCHEN["CORE"],
                                          f"Golden Pocket {z.gp_lower:.0f}-{z.gp_upper:.0f} + Bestaetigung ({pattern.name})",
                                          stop_ref=z.invalidation))
            elif cur.low < z.gp_lower and cur.close > z.invalidation:
                # Capitulation-Einstieg (E8.1): Kerze durchschlaegt das GP nach unten
                # (Flush-Tage wie 10.10./04.11.), schliesst aber ueber der Invalidierung
                ok = (pattern == Pattern.CAPITULATION_RESET
                      or (flow and flow[-1].funding <= 0)
                      or (len(flow) >= 3 and flow[-1].spot_cvd > flow[-3].spot_cvd))
                if ok:
                    pos.direction, pos.state, pos.zones = "LONG", PosState.CORE, z
                    pos.retrace_extreme = cur.low
                    signals.append(Signal(cur.ts, SignalType.KAUF_2, cur.close,
                                          TRANCHEN["T1"] + TRANCHEN["CORE"],
                                          f"Capitulation: GP durchschlagen (Tief {cur.low:.0f}), Schluss ueber Invalidierung ({pattern.name})",
                                          stop_ref=z.invalidation))
        elif (not imp.up) and bias_short and pattern != Pattern.CAPITULATION_RESET:
            if cur.high >= z.level_05 and cur.high < z.gp_upper:
                pos.direction, pos.state, pos.zones = "SHORT", PosState.T1, z
                pos.retrace_extreme = cur.high
                signals.append(Signal(cur.ts, SignalType.SHORT_1, z.level_05, TRANCHEN["T1"],
                                      f"0.5-Retracement des Abwaerts-Impulses {imp.start.price:.0f}->{imp.end.price:.0f}",
                                      stop_ref=z.invalidation))
            elif z.gp_upper <= cur.high <= z.gp_lower:  # Short: 0.65 liegt OBEN
                ok = (pattern == Pattern.DERIVATE_PUMP
                      or (flow and flow[-1].funding > 0)
                      or (len(flow) >= 3 and flow[-1].spot_cvd < flow[-3].spot_cvd))
                if ok:
                    pos.direction, pos.state, pos.zones = "SHORT", PosState.CORE, z
                    pos.retrace_extreme = cur.high
                    signals.append(Signal(cur.ts, SignalType.SHORT_2, z.gp_upper,
                                          TRANCHEN["T1"] + TRANCHEN["CORE"],
                                          f"Golden Pocket {z.gp_upper:.0f}-{z.gp_lower:.0f} + Bestaetigung ({pattern.name})",
                                          stop_ref=z.invalidation))
            elif cur.high > z.gp_lower and cur.close < z.invalidation:
                # Squeeze-Einstieg (E8.1, Spiegelbild): Kerze durchschlaegt das GP nach
                # oben, schliesst aber unter der Invalidierung
                ok = (pattern == Pattern.DERIVATE_PUMP
                      or (flow and flow[-1].funding > 0)
                      or (len(flow) >= 3 and flow[-1].spot_cvd < flow[-3].spot_cvd))
                if ok:
                    pos.direction, pos.state, pos.zones = "SHORT", PosState.CORE, z
                    pos.retrace_extreme = cur.high
                    signals.append(Signal(cur.ts, SignalType.SHORT_2, cur.close,
                                          TRANCHEN["T1"] + TRANCHEN["CORE"],
                                          f"Squeeze: GP durchschlagen (Hoch {cur.high:.0f}), Schluss unter Invalidierung ({pattern.name})",
                                          stop_ref=z.invalidation))

    # --- Positions-Management
    elif pos.state != PosState.FLAT and pos.zones is not None:
        z = pos.zones
        long_side = pos.direction == "LONG"
        # Retracement-Extrem fortschreiben (fuer Extension-Ziele)
        if long_side:
            pos.retrace_extreme = min(pos.retrace_extreme or cur.low, cur.low)
        else:
            pos.retrace_extreme = max(pos.retrace_extreme or cur.high, cur.high)
        ext1 = z.ext_target(pos.retrace_extreme, 1.0)
        ext2 = z.ext_target(pos.retrace_extreme, 1.618)

        stop_hit = (cur.close < z.invalidation) if long_side else (cur.close > z.invalidation)
        if stop_hit:
            st = SignalType.STOPLOSS if long_side else SignalType.SHORT_STOPLOSS
            signals.append(Signal(cur.ts, st, cur.close, 100,
                                  f"Kerzenschluss {'unter' if long_side else 'ueber'} Invalidierung {z.invalidation:.0f}"))
            pos.direction, pos.state, pos.zones, pos.retrace_extreme = "NONE", PosState.FLAT, None, None
        else:
            # Upgrade T1 -> CORE: Kernposition im Golden Pocket (KAUF 2 / SHORT 2)
            if pos.state == PosState.T1:
                in_gp = (z.gp_lower <= cur.low <= z.gp_upper) if long_side \
                    else (z.gp_upper <= cur.high <= z.gp_lower)
                if in_gp:
                    if long_side:
                        ok = (pattern == Pattern.CAPITULATION_RESET
                              or (flow and flow[-1].funding <= 0)
                              or (len(flow) >= 3 and flow[-1].spot_cvd > flow[-3].spot_cvd))
                        if ok:
                            signals.append(Signal(cur.ts, SignalType.KAUF_2, z.gp_upper,
                                                  TRANCHEN["CORE"],
                                                  f"Golden Pocket {z.gp_lower:.0f}-{z.gp_upper:.0f} + Bestaetigung ({pattern.name})",
                                                  stop_ref=z.invalidation))
                            pos.state = PosState.CORE
                    else:
                        ok = (pattern == Pattern.DERIVATE_PUMP
                              or (flow and flow[-1].funding > 0)
                              or (len(flow) >= 3 and flow[-1].spot_cvd < flow[-3].spot_cvd))
                        if ok:
                            signals.append(Signal(cur.ts, SignalType.SHORT_2, z.gp_upper,
                                                  TRANCHEN["CORE"],
                                                  f"Golden Pocket {z.gp_upper:.0f}-{z.gp_lower:.0f} + Bestaetigung ({pattern.name})",
                                                  stop_ref=z.invalidation))
                            pos.state = PosState.CORE
            # Nachkauf am 0.786
            if pos.state in (PosState.T1, PosState.CORE):
                touch = (cur.low <= z.level_0786) if long_side else (cur.high >= z.level_0786)
                if touch:
                    nk = SignalType.NACHKAUF if long_side else SignalType.SHORT_NACHLEGEN
                    signals.append(Signal(cur.ts, nk, z.level_0786, TRANCHEN["FULL"],
                                          "0.786-Zone erreicht, Struktur intakt",
                                          stop_ref=z.invalidation))
                    pos.state = PosState.FULL
            # Teilgewinne an Extensions
            if pos.state in (PosState.T1, PosState.CORE, PosState.FULL):
                hit1 = (cur.high >= ext1) if long_side else (cur.low <= ext1)
                if hit1:
                    tp = SignalType.TEILVERKAUF_1 if long_side else SignalType.SHORT_TP_1
                    signals.append(Signal(cur.ts, tp, ext1, TRANCHEN["TP1"],
                                          f"Extension 1.0 erreicht ({ext1:.0f})"))
                    pos.state = PosState.TP1
            if pos.state == PosState.TP1:
                hit2 = (cur.high >= ext2) if long_side else (cur.low <= ext2)
                if hit2:
                    tp = SignalType.TEILVERKAUF_2 if long_side else SignalType.SHORT_TP_2
                    signals.append(Signal(cur.ts, tp, ext2, TRANCHEN["TP2"],
                                          f"Extension 1.618 erreicht ({ext2:.0f})"))
                    pos.state = PosState.TP2
            # Rest schliessen bei Gegen-Muster/Divergenz nach TP1
            if pos.state in (PosState.TP1, PosState.TP2):
                exit_pat = (pattern in (Pattern.DERIVATE_PUMP, Pattern.SHORT_COVERING)) if long_side \
                    else (pattern in (Pattern.CAPITULATION_RESET, Pattern.GESUNDER_TREND))
                if exit_pat:
                    ex = SignalType.VERKAUF_REST if long_side else SignalType.SHORT_COVER_REST
                    signals.append(Signal(cur.ts, ex, cur.close, 20,
                                          f"Gegen-Muster am Ziel: {pattern.name}"))
                    pos.direction, pos.state, pos.zones, pos.retrace_extreme = "NONE", PosState.FLAT, None, None
            # Warnung waehrend offener Long-Position
            if long_side and pos.state in (PosState.T1, PosState.CORE, PosState.FULL) \
                    and pattern == Pattern.DERIVATE_PUMP:
                signals.append(Signal(cur.ts, SignalType.WARNUNG, cur.close, 0,
                                      "Derivate-Pump: anfaellig fuer Long-Flush"))

    pos.last_signal_ts = cur.ts
    return signals
