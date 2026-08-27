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
    long_liq: float = 0.0   # Long-Liquidationen dieser Kerze (USD), E9.1 (Coinalyze)
    short_liq: float = 0.0  # Short-Liquidationen dieser Kerze (USD)
    long_pct: float = 0.0   # Anteil der Long-Positionierung in % (E16, Coinalyze);
                            # 0.0 = keine Daten. >50 = mehrheitlich long.


class Pattern(Enum):
    """Der Order-Flow-Kompass (STRATEGIE.md Abschnitt 3).

    Muster 1-4 stammen woertlich aus Furkans Notizen (Frame 14:50). Muster 5 ist eine
    Ergaenzung aus E13: Furkans vier Muster beschreiben drei steigende Maerkte und EINEN
    gesunden Absturz (Kapitulation). Fuer einen UNgesunden Absturz gab es keinen Begriff —
    er landete auf NEUTRAL und war damit von einem ruhigen Seitwaertsmarkt nicht zu
    unterscheiden. Genau in dieser Lage hat die Engine gekauft (16 von 34 Ersteinstiegen
    bei NEUTRAL). Muster 5 gibt der Lage einen Namen, damit man sie sperren kann.
    """
    GESUNDER_TREND = 1
    DERIVATE_PUMP = 2
    SHORT_COVERING = 3
    CAPITULATION_RESET = 4
    UNGESUNDER_ABVERKAUF = 5
    NEUTRAL = 0


class SignalType(Enum):
    KAUF_1 = "KAUF 1 (Teilposition am 0.5-Level)"
    KAUF_2 = "KAUF 2 (Kernposition im Golden Pocket)"
    NACHKAUF = "NACHKAUF (0.786-Zone)"
    TEILVERKAUF_LADDER = "TEILVERKAUF Leiter (Zwischenziel vor 1.0)"
    TEILVERKAUF_1 = "TEILVERKAUF 1 (Extension 1.0)"
    TEILVERKAUF_2 = "TEILVERKAUF 2 (Extension 1.618)"
    VERKAUF_REST = "VERKAUF Rest (Muster/Divergenz am Ziel)"
    STOPLOSS = "STOPLOSS"
    WARNUNG = "WARNUNG (Derivate-Pump aktiv)"
    # Short-Seite (spiegelbildlich)
    SHORT_1 = "SHORT 1 (Teilposition am 0.5-Level)"
    SHORT_2 = "SHORT 2 (Kernposition im Golden Pocket)"
    SHORT_NACHLEGEN = "SHORT NACHLEGEN (0.786-Zone)"
    SHORT_TP_LADDER = "SHORT TEILGEWINN Leiter (Zwischenziel vor 1.0)"
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
    tag: str = ""             # z. B. "FLUSH" = aggressiver Kapitulations-Einstieg (Kaiser entscheidet)

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


# E19 (Befund 2026-08-27, Furkan-Video vom 02.08.): Die Wahl des Referenz-Beins war der
# blinde Fleck des Projekts. Am 02.08.2026 zeichnete die Engine ein Zwei-Tage-Bein von
# 4,8 % (65.409->62.275, Richtung SHORT und damit bei bias_short=false unhandelbar),
# waehrend Furkan zur selben Stunde ueber drei Wochen und 15,8 % mass (57.800->66.956).
# Seine Zonen und unsere Formel stimmen exakt ueberein — nur das Bein nicht.
#
# Warum das blockiert: Der Abstand vom Golden Pocket zur Invalidierung betraegt immer rund
# 35-38 % der Beinlaenge. `min_stop_pct` = 2 % verlangt damit implizit ein Bein von etwa
# 5,5 % — die Auswahl liefert im Median aber 4,0 %. Gemessen an 30 Tagen (27.07.-27.08.):
# 17 Tage Richtung SHORT (gesperrt), 9 Tage LONG mit Stop-Abstand unter 2 % (verworfen),
# nur 4 Tage handelbar. Die Engine zeichnete Beine, die fuer ihre eigene Mindest-
# anforderung zu klein sind.
#
# Zwei Schalter, beide Default aus:
#   min_bein_pct  — harte Untergrenze fuer die Beinlaenge; kleinere Beine kommen als
#                   Referenz gar nicht in Frage, die Suche geht zum naechstgroesseren.
#   bein_wahl     — "juengstes" (bisher) oder "groesstes": unter den letzten
#                   `bein_pivots` Pivots das groesste signifikante Bein.
BEIN_PIVOTS = 12          # Fenster fuer bein_wahl="groesstes" (Struktur statt Uhrzeit)


def last_significant_impulse(candles: list[Candle], pivots: list[Pivot],
                             k_atr: float = 3.0, min_pct: float = 0.03,
                             min_bein_pct: float = 0.0,
                             bein_wahl: str = "juengstes",
                             bein_pivots: int = BEIN_PIVOTS,
                             nur_auf: Optional[bool] = None) -> Optional[Impulse]:
    """Referenz-Impuls (Pivot->Pivot) fuer die Fib-Zonen.

    Signifikant = Spanne >= k_atr * ATR(14) ODER >= min_pct des Startpreises.
    Zusaetzlich (E19) muss die Spanne >= min_bein_pct des Startpreises sein, wenn gesetzt.
    Der Zeitabschnitt ergibt sich aus der Swing-Struktur selbst (kein starres Fenster).

    bein_wahl="juengstes": das juengste Bein, das alle Bedingungen erfuellt (bisheriges
    Verhalten). "groesstes": unter den Beinen der letzten `bein_pivots` Pivots das mit der
    groessten Spanne — bei Gleichstand das juengere.

    nur_auf: True = nur Aufwaerts-Beine (Long-Setups), False = nur Abwaerts-Beine,
    None = beide (bisheriges Verhalten). Grundlage ist Frame 16:12/16:45 des Videos vom
    02.08.2026: Furkan fuehrt ZWEI Fib-Raster gleichzeitig — das grosse Aufwaerts-Bein
    57.802,4 -> 66.939,7 fuer seine Long-Nachkaeufe und das kleine Abwaerts-Bein von
    demselben Hoch als Widerstandszone. Unsere Engine kennt nur eins und nahm an jenem
    Tag das kleine, abwaertsgerichtete — das sie bei bias_short=false nicht handeln darf.
    """
    if len(pivots) < 2:
        return None
    a = atr(candles)

    def _taugt(start: Pivot, end: Pivot) -> bool:
        if start.kind == end.kind:
            return False
        if nur_auf is not None and (end.price > start.price) != nur_auf:
            return False
        rng = abs(end.price - start.price)
        if min_bein_pct > 0 and start.price > 0 and rng < min_bein_pct * start.price:
            return False
        return rng >= k_atr * a or rng >= min_pct * start.price

    if bein_wahl == "groesstes":
        fenster = pivots[-bein_pivots:] if bein_pivots > 0 else pivots
        bester, beste_spanne = None, -1.0
        for i in range(len(fenster) - 1, 0, -1):
            start, end = fenster[i - 1], fenster[i]
            if not _taugt(start, end):
                continue
            spanne = abs(end.price - start.price)
            if spanne > beste_spanne:          # ">" statt ">=" -> bei Gleichstand das juengere
                bester, beste_spanne = Impulse(start, end), spanne
        return bester

    for i in range(len(pivots) - 1, 0, -1):
        start, end = pivots[i - 1], pivots[i]
        if _taugt(start, end):
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


# ---------------------------------- Uebergeordneter Kontext (1D-Ebene)
# Furkans Entscheidungsprozess (Transkript 16:03-19:41): ZUERST der uebergeordnete
# Bias/Trend, DANN Orderflow+Fib nur zum Timing des Einstiegs. Die folgenden Helfer
# leiten die 1D-Ebene aus den vorhandenen 4h-Kerzen ab (Resampling), damit Live und
# Backtest dieselbe Logik nutzen.


def ema(values: list[float], period: int) -> Optional[float]:
    """Exponentieller gleitender Durchschnitt; liefert den letzten Wert."""
    if not values:
        return None
    k = 2.0 / (period + 1)
    e = values[0]
    for v in values[1:]:
        e = v * k + e * (1 - k)
    return e


def resample_daily(candles: list[Candle]) -> list[Candle]:
    """Fasst 4h-Kerzen zu Tageskerzen zusammen (UTC-Tag: Open zuerst, High/Low, Close zuletzt)."""
    days: dict[int, list[float]] = {}
    order: list[int] = []
    for c in candles:
        day = (c.ts // 86_400_000) * 86_400_000        # Mitternacht UTC in ms
        if day not in days:
            days[day] = [c.open, c.high, c.low, c.close]
            order.append(day)
        else:
            d = days[day]
            d[1] = max(d[1], c.high)
            d[2] = min(d[2], c.low)
            d[3] = c.close
    return [Candle(day, days[day][0], days[day][1], days[day][2], days[day][3]) for day in order]


def daily_trend(candles: list[Candle], period: int = 50):
    """(letzter Tages-Schluss, Tages-EMA(period)) — Basis fuer den Trendfilter.

    Live reichen ~66 Tage (400 4h-Kerzen); EMA200/1D braeuchte mehr Historie, daher
    ist period=50 ein tragfaehiger Naeherungswert fuer den uebergeordneten Trend.
    """
    daily = resample_daily(candles)
    if len(daily) < 2:
        return None
    closes = [c.close for c in daily]
    return daily[-1].close, ema(closes, min(period, len(closes)))


def daily_fib_zone(candles: list[Candle], pivot_n: int = 5,
                   k_atr: float = 3.0, min_bein_pct: float = 0.0,
                   bein_wahl: str = "juengstes") -> Optional[FibZones]:
    """Fib-Zonen des letzten signifikanten 1D-Impulses (fuer die 4h+1D-Konfluenz)."""
    daily = resample_daily(candles)
    if len(daily) < 2 * pivot_n + 2:
        return None
    piv = find_pivots(daily, n=pivot_n)
    imp = last_significant_impulse(daily, piv, k_atr=k_atr, min_bein_pct=min_bein_pct,
                                   bein_wahl=bein_wahl)
    return fib_zones(imp) if imp is not None else None


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
                     funding_hot: float = 0.0001,
                     liq_spike_mult: float = 3.0) -> Pattern:
    """Ordnet die juengste Marktphase einem der 4 Kompass-Muster zu.

    `window` = Anzahl Kerzen (12 x 4h = 2 Tage). Schwellen sind Startwerte.
    E9.1: echte Liquidationen (Coinalyze) verstaerken Muster 3/4 — eine Long-Liq-
    Kaskade belegt die Kapitulation direkt (Muster 4), eine Short-Liq-Kaskade das
    Short-Covering (Muster 3). Rueckwaertskompatibel: ohne Liq-Daten (=0) gilt die
    bisherige OI-Proxy-Logik.
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

    def _liq_spike(get) -> bool:
        vals = [get(p) for p in f]
        base = sum(vals[:-1]) / (len(vals) - 1) if len(vals) > 1 else 0.0
        return base > 0 and vals[-1] >= liq_spike_mult * base
    long_liq_spike = _liq_spike(lambda p: p.long_liq)
    short_liq_spike = _liq_spike(lambda p: p.short_liq)

    # 4: Capitulation/Flush + Reset — Preis scharf runter, Spot-CVD dreht,
    #    dazu OI-Wipeout ODER echte Long-Liquidations-Kaskade
    if price_chg <= -sharp_move_pct:
        spot_turning = len(flow) >= 3 and flow[-1].spot_cvd > flow[-3].spot_cvd
        if spot_turning and (oi_chg <= -oi_wipeout_pct or long_liq_spike):
            return Pattern.CAPITULATION_RESET
    # 5: Ungesunder Abverkauf (E13) — das Spiegelbild von Muster 4. Der Kurs faellt, aber
    #    der Markt ist NICHT ausgeraeumt: Spot-CVD faellt mit (der Dip wird nicht gekauft),
    #    OI haelt oder steigt (die gehebelten Longs sind noch drin und laden nach),
    #    Funding noch positiv (Long-Ueberhang unveraendert), keine Long-Liquidations-
    #    Kaskade (die Zwangsverkaeufe stehen noch bevor). Alle vier zusammen = Furkans
    #    Konfluenz-Prinzip, nur negativ: genau die Lage, in der er NICHT kauft.
    #    Halbe Schwelle beim Preis, weil dieser Zustand typischerweise VOR dem scharfen
    #    Einbruch vorliegt — er soll warnen, bevor der Flush kommt, nicht danach.
    if (price_chg <= -sharp_move_pct / 2 and spot < 0 and oi_chg >= -0.01
            and funding_now > 0 and not long_liq_spike):
        return Pattern.UNGESUNDER_ABVERKAUF
    # 3: Short-Covering — Preis hoch, OI runter ODER echte Short-Liquidations-Kaskade
    if price_chg >= sharp_move_pct / 2 and (oi_chg <= -0.02 or short_liq_spike):
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
    tp_rungs: int = 0                        # Anzahl gefeuerter Leiter-Zwischenverkaeufe
    dip_buys: int = 0                        # Anzahl bedingter Nachkaeufe unter Invalidierung (E9.3)
    buy_rungs: int = 0                       # Anzahl Mehrtages-Kaufleiter-Tranchen (E9.5)
    entry_ref: Optional[float] = None        # tranchengewichteter Durchschnitts-Einstand (E9.10)
    entry_pct: int = 0                       # Summe der eingestiegenen Tranchen-Prozente
    liq_exits: int = 0                       # Anzahl Teilverkaeufe an Liquidationen (E9.11)
    high_exits: int = 0                      # Anzahl Teilverkaeufe am letzten Hoch (E10.2)
    liq_entries: int = 0                     # Anzahl Konfluenz-Nachkaeufe an Liq-Zonen (E10.3)
    ziel_extrem: Optional[float] = None      # eingefrorene Zielreferenz nach dem 1. Teilgewinn (E18.3)
    be_aktiv: bool = False                   # Break-even-Stop scharf, seit die Position im Plus war (E19.3)
    # Zeitpunkt des letzten Stops (E13, cooldown_h). Gehoert BEWUSST NICHT in
    # _reset_position: Er ist die Erinnerung ZWISCHEN zwei Positionen und muss den
    # Positions-Reset ueberleben, sonst wuesste die Sperre nach dem Stop nichts mehr.
    last_stop_ts: int = -1


def _reset_position(pos: "Position") -> None:
    """Position schliessen: Zustand und alle Zaehler zurueck auf FLAT."""
    pos.direction, pos.state, pos.zones, pos.retrace_extreme = "NONE", PosState.FLAT, None, None
    pos.tp_rungs = 0
    pos.dip_buys = 0
    pos.buy_rungs = 0
    pos.entry_ref = None
    pos.entry_pct = 0
    pos.liq_exits = 0
    pos.high_exits = 0
    pos.liq_entries = 0
    pos.ziel_extrem = None
    pos.be_aktiv = False


# Einstiegs-Signaltypen je Richtung — daraus wird der Durchschnitts-Einstand gebildet
# (Basis fuer den nachgezogenen Break-even-Stop, E9.10).
_ENTRY_TYPES = {SignalType.KAUF_1, SignalType.KAUF_2, SignalType.NACHKAUF,
                SignalType.SHORT_1, SignalType.SHORT_2, SignalType.SHORT_NACHLEGEN}

# E18.2: Signale, die eine bestehende Position VERGROESSERN bzw. VERKLEINERN. Nur diese
# beiden Gruppen schliessen sich bei no_flip innerhalb einer Kerze gegenseitig aus.
# Bewusst NICHT dabei: STOPLOSS, VERKAUF_REST und ihre Short-Gegenstuecke — ein
# vollstaendiger Ausstieg darf nie unterdrueckt werden, egal was vorher in der Kerze
# passiert ist. Ersteinstiege aus FLAT sind ebenfalls nicht betroffen (anderer Zweig).
_AUFBAU_TYPES = {SignalType.NACHKAUF, SignalType.SHORT_NACHLEGEN,
                 SignalType.KAUF_2, SignalType.SHORT_2}
_TEILVERKAUF_TYPES = {SignalType.TEILVERKAUF_LADDER, SignalType.TEILVERKAUF_1,
                      SignalType.TEILVERKAUF_2, SignalType.SHORT_TP_LADDER,
                      SignalType.SHORT_TP_1, SignalType.SHORT_TP_2}


TRANCHEN = {"T1": 25, "CORE": 50, "FULL": 25, "TP1": 40, "TP2": 40}

# Bedingter Stop/Nachkauf (E9.3): statt pauschalem Stop bei Verlust nachkaufen, solange
# der Order-Flow den Trend bestaetigt (Furkan: "bei Verlust nachgekauft, weil vom
# Aufwaertstrend ueberzeugt"). MAX_DIP_BUYS begrenzt die Leiter; DIP_FLOOR_PCT ist der
# harte Boden — bricht der Kurs so weit durch, wird trotz Flow gestoppt (echter Bruch).
MAX_DIP_BUYS = 2
DIP_FLOOR_PCT = 0.05
DIP_TRANCHE = 20

# Mehrtages-Kaufleiter (E9.5): Furkan kauft in Tranchen ueber mehrere Tage in die
# Schwaeche nach, solange die Struktur intakt ist (nie all in; z. B. 27.-30.10.,
# 29.-31.01.). Jede neue Tiefkerze IN der Retracement-Zone (ueber Invalidierung, unter
# 0.5) mit Order-Flow-Bestaetigung = eine kleine Tranche, hoechstens MAX_BUY_RUNGS.
MAX_BUY_RUNGS = 3
BUY_LADDER_TRANCHE = 15

# Gestaffelte Teilgewinne (E8.2): Zwischenziele als Extension-Faktoren VOR dem
# 1.0-Ziel — Furkan verkauft in Leitern in die Staerke (z. B. 08.-22.04.). Je Stufe
# eine kleine Tranche; max. eine Stufe je Kerze, damit sich der Abbau ueber mehrere
# Tage verteilt (nie all out). Schaltbar ueber tp_ladder, per Backtest kalibriert.
LADDER_FACTORS = (0.8, 0.9)
LADDER_TRANCHE = 15

# Teilverkaeufe an Liquidationen (E9.11). Furkan verkauft erst, wenn der Kurs die
# Liquidationszonen erreicht — nicht schon vorher an einem rechnerischen Fib-Ziel.
# Seine Heatmap (wo Liquiditaet JETZT liegt) haben wir nicht; aus Coinalyze kennen wir
# aber, WIE VIEL je 4h-Kerze liquidiert wurde. Das Preisniveau liefert die Kerze selbst:
# Shorts werden am Hoch gerissen, Longs am Tief. Daraus zwei testbare Varianten:
#   "spike" = reaktiv, in die laufende Kaskade verkaufen (nur aktuelle Daten)
#   "zone"  = Preisniveaus vergangener Kaskaden als Magnete, Kurs laeuft wieder hinein
# WICHTIG (Kausalitaet): die Zonen werden ausschliesslich aus Kerzen VOR der aktuellen
# gebildet — sonst wuesste der Backtest die Zukunft und das Ergebnis waere wertlos.
MAX_LIQ_EXITS = 3          # hoechstens so viele Liquidations-Teilverkaeufe je Position
LIQ_SPIKE_MULT = 3.0       # Kaskade = mindestens 3x der Durchschnitt des Fensters
LIQ_LOOKBACK = 180         # Kerzen fuer die Zonen-Historie (180 x 4h = 30 Tage)
LIQ_ZONE_TOL = 0.005       # 0,5 % Toleranz: so nah muss der Kurs an die Zone
LIQ_ZONE_MIN_MULT = 3.0    # Zone = Kerze mit mindestens 3x der mittleren Liquidation


# Teilverkauf am letzten Hoch (E10.2, Furkan-Update 19:52: "die weiteren Gewinne werde
# ich bei ueber 66.600 HIER UNTER DIESEM HOCH rausnehmen"). Er verkauft am Struktur-
# Niveau, nicht am rechnerischen Fib-Ziel: Am alten Hoch sitzen die Kaeufer von damals,
# die bei plus/minus null aussteigen wollen — dort staut sich Angebot.
MAX_HIGH_EXITS = 2         # hoechstens so viele Struktur-Teilverkaeufe je Position
HIGH_EXIT_TOL = 0.005      # 0,5 % darunter reicht — vor der Masse raus

# Liquidationszonen fuer den EINSTIEG (E10.3, Furkan-Update 18:27: "unter uns liegt
# deutlich mehr, viele Long-Positionen ab 61.700 runter bis 60.500 — HIER liegt dann auch
# aktuell das Golden Pocket, wo ich die Position wieder aufstocken wuerde").
# Er kauft, wo Longs liquidiert werden, und sucht die Konfluenz mit dem Golden Pocket.
# Bisher haben wir Liquidationsdaten nur fuer AUSSTIEGE getestet (E9.11) — dort kosteten
# sie Rendite. Fuer Einstiege ist es ungemessen.
MAX_LIQ_ENTRIES = 2        # hoechstens so viele Konfluenz-Nachkaeufe je Position
LIQ_ENTRY_TRANCHE = 20     # Tranche je Konfluenz-Nachkauf in %


def next_pivot_beyond(pivots: list[Pivot], price: float, long_side: bool) -> Optional[float]:
    """Naechstes bestaetigtes Pivot-Hoch UEBER dem Preis (long) bzw. Pivot-Tief darunter."""
    if long_side:
        cands = [p.price for p in pivots if p.kind == "H" and p.price > price]
        return min(cands) if cands else None
    cands = [p.price for p in pivots if p.kind == "L" and p.price < price]
    return max(cands) if cands else None


def liq_cascade(flow: list[FlowPoint], side: str, window: int = 12,
                mult: float = LIQ_SPIKE_MULT) -> bool:
    """Laeuft in der JUENGSTEN Kerze eine Liquidations-Kaskade?

    side="short" = Short-Liquidationen (Squeeze nach oben -> gut fuer Long-Teilgewinne),
    side="long"  = Long-Liquidationen (Flush nach unten -> gut fuer Short-Teilgewinne).
    """
    if len(flow) < 3:
        return False
    f = flow[-window:]
    vals = [(p.short_liq if side == "short" else p.long_liq) for p in f]
    if len(vals) < 2:
        return False
    base = sum(vals[:-1]) / (len(vals) - 1)
    return base > 0 and vals[-1] >= mult * base


def liq_levels(candles: list[Candle], flow: list[FlowPoint], side: str,
               lookback: int = LIQ_LOOKBACK,
               min_mult: float = LIQ_ZONE_MIN_MULT) -> list[tuple[float, float]]:
    """Preisniveaus, an denen historisch aussergewoehnlich viel liquidiert wurde.

    Gibt [(Preis, Liquidationsmasse USD)] zurueck, absteigend nach Masse. Der Preis ist
    das Kerzen-Hoch (side="short") bzw. -Tief (side="long") der Kaskaden-Kerze.
    Erwartet bereits beschnittene Listen (nur Kerzen VOR der Entscheidung).
    """
    n = min(len(candles), len(flow), lookback)
    if n < 10:
        return []
    cs, fs = candles[-n:], flow[-n:]
    vals = [(p.short_liq if side == "short" else p.long_liq) for p in fs]
    total = sum(vals)
    if total <= 0:
        return []
    avg = total / len(vals)
    out = [((c.high if side == "short" else c.low), v)
           for c, v in zip(cs, vals) if v >= min_mult * avg]
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def in_liq_zone(price: float, levels: list[tuple[float, float]],
                tol: float = LIQ_ZONE_TOL) -> Optional[float]:
    """Liegt `price` innerhalb der Toleranz an einem der Niveaus? Gibt das Niveau zurueck."""
    for lvl, _mass in levels:
        if lvl > 0 and abs(price - lvl) / lvl <= tol:
            return lvl
    return None


def evaluate(candles: list[Candle], flow: list[FlowPoint], pos: Position,
             bias_long: bool = True, bias_short: bool = True,
             pivot_n: int = 5, k_atr: float = 2.0,
             flush_entry: str = "core", tp_ladder: bool = True,
             trend_filter: bool = False, trend_ema: int = 50,
             strict_confirm: bool = False, confluence: bool = False,
             conditional_stop: bool = False, buy_ladder: bool = True,
             release_stale_rest: bool = False, trail_stop: bool = False,
             liq_exit: str = "off", high_exit: str = "off",
             liq_entry: str = "off", block_unhealthy: bool = False,
             confirm_t1: bool = False, cooldown_h: float = 0.0,
             min_stop_pct: float = 0.0,
             no_flip: bool = False, freeze_targets: bool = False,
             min_bein_pct: float = 0.0, bein_wahl: str = "juengstes",
             be_im_plus: bool = False, bein_richtung: str = "auto") -> list[Signal]:
    # AKTUELLE DEFAULTS (Stand 2026-07-24, gemessen im Voll-Daten-Fenster mit echtem
    # Coinalyze-OI, BACKTEST.md): n=5, k_atr=2.0, tp_ladder=True, buy_ladder=True,
    # flush_entry='core'. Beste gemessene Kombination war "nur Long + Flush core +
    # Kaufleiter": Recall 55 %, Praezision 30 %, Rendite +38,9 % (Buy&Hold -19,3 %).
    # Die RICHTUNG kommt nicht von hier, sondern aus site/data/config.json — live steht
    # bias_short=false (nur Long), weil mechanische Shorts ohne Makro-Bias verlieren.
    # HISTORIE (nicht mehr gueltig): vor E9.1 war flush_entry='off' der beste Wert —
    # damals fehlte echtes OI, Muster 4 war blind. Mit echten Liquidationsdaten dreht
    # sich das Ergebnis. tp_ladder (E8.2) bildet Furkans gestaffelte Gewinnmitnahme ab
    # (Recall/Praezision unveraendert, Rendite leicht besser). Recall != Gewinn.
    # E8.5-Filter fuer bessere Einstiege (alle Furkans Methode, schaltbar, Default aus
    # bis per Backtest gemessen): trend_filter = nur Setups in Richtung des 1D-Trends
    # (Furkans Schritt 1, Preis vs. Tages-EMA); strict_confirm = KAUF 2 nur mit
    # Konfluenz (Spot-CVD dreht UND Funding stimmt, statt eines von beiden);
    # confluence = Einstieg nur, wenn die 4h-Zone in der 1D-Retracement-Zone liegt.
    # release_stale_rest (E9.9): gibt die Restposition in TP1/TP2 frei, sobald ein NEUER
    # signifikanter Impuls bestaetigt ist — die eingefrorenen Fib-Zonen der Position sind
    # dann veraltet. Behebt die Blockade, dass ein Rest von 20 % beliebig lange liegen
    # bleibt (Stop weit weg, Gegen-Muster tritt nicht ein) und dabei JEDE neue Einstiegs-
    # pruefung verhindert, weil der Einstiegs-Block nur bei state==FLAT laeuft.
    # Deckt Grundregel 1 ab: Zonen sind dynamisch, nie starr.
    # trail_stop (E9.10): zieht den Stop nach, sobald Teilgewinne realisiert sind —
    # auf Break-even (Durchschnitts-Einstand) bzw. hinter die Struktur, je nachdem was
    # hoeher liegt. Furkan (laut Kaiser): "Stop ueber den Kauf gezogen, dann kann ich
    # nichts mehr verlieren", Motto Kapital schuetzen. Loest zugleich die TP2-Blockade,
    # ohne den Rest wie bei release_stale_rest zum Marktpreis wegzuwerfen.
    # liq_exit (E9.11, Kaisers Beobachtung "Furkan faengt erst an zu verkaufen, wenn der
    # Kurs die Liquidationszonen erreicht"): "off" | "spike" (in die laufende Kaskade
    # verkaufen) | "zone" (Preisniveaus vergangener Kaskaden als Magnete) | "both".
    # Ergaenzt die Fib-Teilgewinne, ersetzt sie nicht; hoechstens MAX_LIQ_EXITS je Position.
    # high_exit (E10.2): Teilverkauf kurz UNTER dem letzten bestaetigten Pivot-Hoch statt
    # nur am Fib-Ziel. "off" | "on" | "weak". "weak" verkauft nur, wenn der Anlauf auf das
    # Hoch OHNE Spot-Nachfrage passiert (Furkan 20:17: "bei Breakouts muesste man
    # spaetestens da Spot-Nachfrage sehen") — so wird aus einer blossen Warnung eine
    # Handlung, die man messen kann.
    # liq_entry (E10.3): Liquidationszonen auf der EINSTIEGS-Seite. "off" | "boost" |
    # "filter". "boost" = zusaetzliche Nachkauf-Tranche, wenn die Fib-Zone mit einem
    # historischen Long-Liquidations-Cluster zusammenfaellt (Furkans Konfluenz).
    # "filter" = Einstiege NUR bei dieser Konfluenz (restriktiv, Gegenprobe).
    # ---------------------------------------------------------------- E13 (alle Default aus)
    # Vier Hebel gegen Einstiege in einen ungesunden Markt bzw. gegen zu viele Trades.
    # Befund, der sie ausgeloest hat (docs/VERLUST-ANALYSE-2026-07-27.md, Abschnitt 6c):
    # von 34 Ersteinstiegen hatten 16 GAR KEINE Flow-Pruefung (0.5-Level) und 16 das
    # Muster NEUTRAL — 32 von 34 ohne ein einziges gesundes Signal.
    # block_unhealthy: sperrt Einstiege UND Nachkaeufe, solange der Order-Flow gegen die
    #   Richtung laeuft — Long bei Muster 5 (ungesunder Abverkauf), Short bei Muster 1
    #   (gesunder Trend, also echte Spot-Nachfrage; in die shortet Furkan nicht).
    # confirm_t1: verlangt auch fuer den 0.5-Level-Einstieg eine Order-Flow-Bestaetigung.
    #   Dieser Zweig hatte bisher als einziger KEINE — er feuerte allein auf Preisberuehrung.
    # cooldown_h: Sperrfrist in Stunden nach einem Stop (0 = aus). Gegen die Saegeblatt-
    #   Serien: die laengste war 10 Stops in Folge, medianer Abstand zum Wiedereinstieg 68 h,
    #   kuerzester Fall 4 h. Furkan wartet nach einem Stop auf eine neue Struktur.
    # min_stop_pct: Mindestabstand Einstieg->Invalidierung als Anteil (0 = aus). 15 von 34
    #   Positionen lagen unter 2 %, eine bei 0,02 % — solche Stops loest schon das normale
    #   Rauschen aus. Furkans eigenes Video-Beispiel liegt bei 3,59 %.
    # ------------------------------------------------- E18 (Durchsicht 27.08.2026, Default aus)
    # no_flip: In einer Kerze wird nur in EINE Richtung gehandelt. Befund: 16 von 214
    #   Signalen der Live-Variante fielen auf Kerzen, in denen gleichzeitig aufgestockt
    #   UND teilverkauft wurde — meist zum selben Preis, weil der Nachkauf das TIEF der
    #   Kerze prueft und der Teilgewinn am letzten Hoch ihr HOCH. Zwei Gebuehren fuer ein
    #   Geschaeft, das sich selbst aufhebt, dazu zwei widersprechende Telegram-Nachrichten.
    #   Es entscheidet, was zuerst kommt; vollstaendige Ausstiege sind nie betroffen.
    # freeze_targets: Haelt die Zielreferenz fest, sobald der erste Teilgewinn realisiert
    #   ist. Bisher wanderte pos.retrace_extreme weiter, wenn der Kurs danach ein tieferes
    #   Tief machte, ohne den Stop auszuloesen — ext1/ext2 sanken mit. Nachgestellt: Ziel
    #   1.618 von 301,8 auf 257,8, also unter das urspruengliche 1.0-Ziel. Passt zum Befund,
    #   dass TEILVERKAUF_2 im ganzen Messfenster genau einmal vorkam.
    # ------------------------------------------- E19 (Furkan-Video 02.08.2026, Default aus)
    # min_bein_pct / bein_wahl: siehe last_significant_impulse — die Engine zeichnete Beine,
    #   die fuer ihren eigenen Mindest-Stopabstand zu klein sind (Median 4,0 %, noetig ~5,5 %).
    # bein_richtung="bias": Es wird nur ein Bein in der HANDELBAREN Richtung gesucht. Steht
    #   bias_short=false (live), sucht die Engine also ein Aufwaerts-Bein und ignoriert das
    #   juengere Abwaerts-Bein, das sie ohnehin nicht handeln duerfte. An 17 von 30 Tagen
    #   (27.07.-27.08.2026) war genau das der Grund fuer Stillstand. Wirkt nur, wenn
    #   genau eine Richtung erlaubt ist; bei Long UND Short aendert sich nichts.
    # be_im_plus: zieht den Stop auf Break-even, sobald die Position im Plus steht — nicht
    #   erst nach einem Teilgewinn. Furkan am 02.08. (16:07-16:25): "wenn ich die Order
    #   gefuellt bekomme, wuerde ich meinen Stop hochsetzen auf das neue Entry. Mit der
    #   Position moechte ich nicht mehr in Verlust gehen." Deckt zugleich den nie gebauten
    #   Punkt 2 aus docs/VERLUST-ANALYSE-2026-07-27.md ab (44 % der Verlustsumme). Wirkt nur
    #   zusammen mit trail_stop und nur, wenn der Einstand UNTER dem Kurs liegt — sonst
    #   waere der Stop im selben Moment ausgeloest.
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

    def _darf_aufstocken() -> bool:
        """E18.2: Nach einem Teilgewinn in derselben Kerze wird nicht nachgelegt."""
        return not (no_flip and any(x.type in _TEILVERKAUF_TYPES for x in signals))

    def _darf_teilverkaufen() -> bool:
        """E18.2: Nach einem Nachkauf in derselben Kerze wird nicht teilverkauft."""
        return not (no_flip and any(x.type in _AUFBAU_TYPES for x in signals))

    pattern = classify_pattern(candles, flow) if flow else Pattern.NEUTRAL
    pivots = find_pivots(candles, n=pivot_n)
    _nur_auf = None
    if bein_richtung == "bias" and bias_long != bias_short:
        _nur_auf = bias_long                     # genau eine Richtung erlaubt -> nur deren Beine
    imp = last_significant_impulse(candles, pivots, k_atr=k_atr,
                                   min_bein_pct=min_bein_pct, bein_wahl=bein_wahl,
                                   nur_auf=_nur_auf)

    # --- E8.5-Kontext (nur berechnen, wenn ein Filter aktiv ist)
    _trend = daily_trend(candles, trend_ema) if trend_filter else None
    _dzone = daily_fib_zone(candles, min_bein_pct=min_bein_pct,
                            bein_wahl=bein_wahl) if confluence else None

    def _trend_ok(long_side: bool) -> bool:
        if not trend_filter or _trend is None or _trend[1] is None:
            return True                                  # unbekannt -> nicht blockieren
        close, e = _trend
        return close >= e if long_side else close <= e

    # Liquidations-Niveaus je Seite nur einmal je Kerze berechnen (E10.3). Ausschliesslich
    # aus Kerzen VOR der aktuellen — sonst wuesste der Backtest die Zukunft.
    _liq_cache: dict = {}

    def _liq_hit(price: float, side: str):
        if side not in _liq_cache:
            _liq_cache[side] = liq_levels(candles[:-1], flow[:-1], side)
        return in_liq_zone(price, _liq_cache[side])

    def _liq_entry_ok(price: float, long_side: bool) -> bool:
        """Nur im Modus 'filter' eine Bedingung; sonst nie blockierend."""
        if liq_entry != "filter":
            return True
        return _liq_hit(price, "long" if long_side else "short") is not None

    def _confluence_ok(price: float) -> bool:
        if not confluence or _dzone is None:
            return True                                  # 1D-Zone unbekannt -> nicht blockieren
        lo, hi = sorted((_dzone.level_05, _dzone.level_0786))
        return lo <= price <= hi

    def _confirm_long() -> bool:
        strong = pattern == Pattern.CAPITULATION_RESET
        cvd_up = len(flow) >= 3 and flow[-1].spot_cvd > flow[-3].spot_cvd
        fund_ok = bool(flow) and flow[-1].funding <= 0
        return strong or (cvd_up and fund_ok) if strict_confirm else strong or fund_ok or cvd_up

    def _confirm_short() -> bool:
        strong = pattern == Pattern.DERIVATE_PUMP
        cvd_dn = len(flow) >= 3 and flow[-1].spot_cvd < flow[-3].spot_cvd
        fund_hot = bool(flow) and flow[-1].funding > 0
        return strong or (cvd_dn and fund_hot) if strict_confirm else strong or fund_hot or cvd_dn

    # --- E13-Helfer -----------------------------------------------------------------
    def _healthy(long_side: bool) -> bool:
        """Warnlicht: laeuft der Order-Flow gerade GEGEN die geplante Richtung?"""
        if not block_unhealthy:
            return True
        if long_side:
            return pattern != Pattern.UNGESUNDER_ABVERKAUF
        return pattern != Pattern.GESUNDER_TREND      # nicht in echte Spot-Nachfrage shorten

    def _t1_ok(long_side: bool) -> bool:
        """Order-Flow-Bestaetigung auch fuer den 0.5-Level-Einstieg (sonst ungeprueft)."""
        if not confirm_t1:
            return True
        return _confirm_long() if long_side else _confirm_short()

    def _cooldown_ok() -> bool:
        """Sperrfrist nach einem Stop abgelaufen?"""
        if cooldown_h <= 0 or pos.last_stop_ts <= 0:
            return True
        return (cur.ts - pos.last_stop_ts) >= cooldown_h * 3600 * 1000

    def _stop_weit_genug(preis: float, zonen: FibZones) -> bool:
        """Liegt die Invalidierung weit genug vom Einstieg entfernt?"""
        if min_stop_pct <= 0 or preis <= 0:
            return True
        return abs(preis - zonen.invalidation) / preis >= min_stop_pct

    # --- Einstiegs-Logik (FLAT): Referenz-Impuls noetig
    if pos.state == PosState.FLAT and imp is not None and _cooldown_ok():
        z = fib_zones(imp)
        if imp.up and bias_long and pattern != Pattern.DERIVATE_PUMP and _healthy(True):
            if (cur.low <= z.level_05 and cur.low > z.gp_upper
                    and _trend_ok(True) and _confluence_ok(cur.low)
                    and _liq_entry_ok(cur.low, True)
                    and _t1_ok(True) and _stop_weit_genug(z.level_05, z)):
                pos.direction, pos.state, pos.zones = "LONG", PosState.T1, z
                pos.retrace_extreme = cur.low
                signals.append(Signal(cur.ts, SignalType.KAUF_1, z.level_05, TRANCHEN["T1"],
                                      f"0.5-Retracement des Impulses {imp.start.price:.0f}->{imp.end.price:.0f}",
                                      stop_ref=z.invalidation))
            elif z.gp_lower <= cur.low <= z.gp_upper:
                if (_confirm_long() and _trend_ok(True) and _confluence_ok(cur.low)
                        and _liq_entry_ok(cur.low, True)
                        and _stop_weit_genug(z.gp_upper, z)):
                    pos.direction, pos.state, pos.zones = "LONG", PosState.CORE, z
                    pos.retrace_extreme = cur.low
                    signals.append(Signal(cur.ts, SignalType.KAUF_2, z.gp_upper,
                                          TRANCHEN["T1"] + TRANCHEN["CORE"],
                                          f"Golden Pocket {z.gp_lower:.0f}-{z.gp_upper:.0f} + Bestaetigung ({pattern.name})",
                                          stop_ref=z.invalidation))
            elif (flush_entry != "off" and cur.low < z.gp_lower
                  and cur.close > z.invalidation):
                # Capitulation-Einstieg (E8.1): Kerze durchschlaegt das GP nach unten
                # (Flush-Tage wie 10.10./04.11.), schliesst aber ueber der Invalidierung
                if (_confirm_long() and _trend_ok(True) and _liq_entry_ok(cur.low, True)
                        and _stop_weit_genug(cur.close, z)):
                    small = flush_entry == "t1"
                    st = PosState.T1 if small else PosState.CORE
                    sig_t = SignalType.KAUF_1 if small else SignalType.KAUF_2
                    tr = TRANCHEN["T1"] if small else TRANCHEN["T1"] + TRANCHEN["CORE"]
                    pos.direction, pos.state, pos.zones = "LONG", st, z
                    pos.retrace_extreme = cur.low
                    signals.append(Signal(cur.ts, sig_t, cur.close, tr,
                                          f"Capitulation: GP durchschlagen (Tief {cur.low:.0f}), Schluss ueber Invalidierung ({pattern.name})",
                                          stop_ref=z.invalidation, tag="FLUSH"))
        elif ((not imp.up) and bias_short and pattern != Pattern.CAPITULATION_RESET
                and _healthy(False)):
            if (cur.high >= z.level_05 and cur.high < z.gp_upper
                    and _trend_ok(False) and _confluence_ok(cur.high)
                    and _liq_entry_ok(cur.high, False)
                    and _t1_ok(False) and _stop_weit_genug(z.level_05, z)):
                pos.direction, pos.state, pos.zones = "SHORT", PosState.T1, z
                pos.retrace_extreme = cur.high
                signals.append(Signal(cur.ts, SignalType.SHORT_1, z.level_05, TRANCHEN["T1"],
                                      f"0.5-Retracement des Abwaerts-Impulses {imp.start.price:.0f}->{imp.end.price:.0f}",
                                      stop_ref=z.invalidation))
            elif z.gp_upper <= cur.high <= z.gp_lower:  # Short: 0.65 liegt OBEN
                if (_confirm_short() and _trend_ok(False) and _confluence_ok(cur.high)
                        and _liq_entry_ok(cur.high, False)
                        and _stop_weit_genug(z.gp_upper, z)):
                    pos.direction, pos.state, pos.zones = "SHORT", PosState.CORE, z
                    pos.retrace_extreme = cur.high
                    signals.append(Signal(cur.ts, SignalType.SHORT_2, z.gp_upper,
                                          TRANCHEN["T1"] + TRANCHEN["CORE"],
                                          f"Golden Pocket {z.gp_upper:.0f}-{z.gp_lower:.0f} + Bestaetigung ({pattern.name})",
                                          stop_ref=z.invalidation))
            elif (flush_entry != "off" and cur.high > z.gp_lower
                  and cur.close < z.invalidation):
                # Squeeze-Einstieg (E8.1, Spiegelbild): Kerze durchschlaegt das GP nach
                # oben, schliesst aber unter der Invalidierung
                if (_confirm_short() and _trend_ok(False) and _liq_entry_ok(cur.high, False)
                        and _stop_weit_genug(cur.close, z)):
                    small = flush_entry == "t1"
                    st = PosState.T1 if small else PosState.CORE
                    sig_t = SignalType.SHORT_1 if small else SignalType.SHORT_2
                    tr = TRANCHEN["T1"] if small else TRANCHEN["T1"] + TRANCHEN["CORE"]
                    pos.direction, pos.state, pos.zones = "SHORT", st, z
                    pos.retrace_extreme = cur.high
                    signals.append(Signal(cur.ts, sig_t, cur.close, tr,
                                          f"Squeeze: GP durchschlagen (Hoch {cur.high:.0f}), Schluss unter Invalidierung ({pattern.name})",
                                          stop_ref=z.invalidation, tag="FLUSH"))

    # --- Positions-Management
    elif pos.state != PosState.FLAT and pos.zones is not None:
        z = pos.zones
        long_side = pos.direction == "LONG"
        # Retracement-Extrem fortschreiben (fuer Extension-Ziele); neues Extrem merken
        prev_extreme = pos.retrace_extreme
        if long_side:
            pos.retrace_extreme = min(pos.retrace_extreme or cur.low, cur.low)
            made_new_extreme = prev_extreme is not None and cur.low < prev_extreme
        else:
            pos.retrace_extreme = max(pos.retrace_extreme or cur.high, cur.high)
            made_new_extreme = prev_extreme is not None and cur.high > prev_extreme
        # E18.3: Nach dem ersten Teilgewinn zaehlt die eingefrorene Referenz — sonst
        # wandern die Ziele mit jedem neuen Tief nach unten. pos.retrace_extreme laeuft
        # unveraendert weiter, damit die Mehrtages-Kaufleiter davon unberuehrt bleibt.
        ziel_ref = pos.ziel_extrem if (freeze_targets and pos.ziel_extrem is not None) \
            else pos.retrace_extreme
        ext1 = z.ext_target(ziel_ref, 1.0)
        ext2 = z.ext_target(ziel_ref, 1.618)

        # Nachgezogener Stop (E9.10, Kaisers Furkan-Zitat: "Stop ueber den Kauf gezogen,
        # dann kann ich nichts mehr verlieren" — Motto Kapital schuetzen). Sobald
        # Teilgewinne realisiert sind (TP1/TP2 ODER eine Leiter-Stufe gefeuert), wandert
        # der Stop auf den hoechsten der drei Bezugspunkte: urspruengliche Invalidierung,
        # Durchschnitts-Einstand (Break-even) und letztes bestaetigtes Pivot-Tief unter
        # dem Kurs (Struktur). Er kann dadurch NUR steigen, nie lockerer werden.
        stop_level = z.invalidation
        trail_note = ""
        # E19.3: Break-even schon, sobald die Position EINMAL im Plus stand (nicht erst nach
        # einem Teilgewinn). Der Merker ist noetig, weil die Bedingung genau in der Kerze,
        # in der der Stop greifen soll, nicht mehr erfuellt waere — der Kurs ist dann ja
        # zurueck unter dem Einstand. Er wird gesetzt, solange der Kurs darueber steht.
        if be_im_plus and pos.entry_ref is not None and not pos.be_aktiv:
            if (cur.close > pos.entry_ref) if long_side else (cur.close < pos.entry_ref):
                pos.be_aktiv = True
        _im_plus = be_im_plus and pos.be_aktiv and pos.entry_ref is not None
        if trail_stop and (pos.state in (PosState.TP1, PosState.TP2)
                           or pos.tp_rungs > 0 or _im_plus):
            cands = [(z.invalidation, "Invalidierung")]
            if pos.entry_ref is not None:
                cands.append((pos.entry_ref, "Einstand"))
            if long_side:
                lows = [p.price for p in pivots if p.kind == "L" and p.price < cur.close]
                if lows:
                    cands.append((max(lows), "Struktur-Tief"))
                stop_level, trail_note = max(cands, key=lambda x: x[0])
            else:
                highs = [p.price for p in pivots if p.kind == "H" and p.price > cur.close]
                if highs:
                    cands.append((min(highs), "Struktur-Hoch"))
                stop_level, trail_note = min(cands, key=lambda x: x[0])
        stop_hit = (cur.close < stop_level) if long_side else (cur.close > stop_level)
        # Bedingter Stop (E9.3): bei Verlust nachkaufen statt stoppen, solange der
        # Order-Flow den Trend weiter bestaetigt (Furkan) — aber nur bis zum harten
        # Boden (DIP_FLOOR_PCT) und hoechstens MAX_DIP_BUYS mal.
        # Nur beim urspruenglichen Stop nachkaufen — einen nachgezogenen Gewinn-Stop
        # darf der bedingte Nachkauf nicht aushebeln.
        if stop_hit and conditional_stop and trail_note in ("", "Invalidierung"):
            if long_side:
                hard_break = cur.close < z.invalidation * (1 - DIP_FLOOR_PCT)
                flow_ok = _confirm_long()
            else:
                hard_break = cur.close > z.invalidation * (1 + DIP_FLOOR_PCT)
                flow_ok = _confirm_short()
            if flow_ok and not hard_break and pos.dip_buys < MAX_DIP_BUYS:
                nk = SignalType.NACHKAUF if long_side else SignalType.SHORT_NACHLEGEN
                signals.append(Signal(cur.ts, nk, cur.close, DIP_TRANCHE,
                                      f"Bedingter Nachkauf: Dip haelt, Order-Flow bestaetigt Trend ({pattern.name})",
                                      stop_ref=z.invalidation))
                pos.dip_buys += 1
                stop_hit = False                             # kein Stop diese Kerze
        if stop_hit:
            st = SignalType.STOPLOSS if long_side else SignalType.SHORT_STOPLOSS
            if trail_note and trail_note != "Invalidierung":
                reason = ("Nachgezogener Stop ({}) {:.0f} — Kerzenschluss {}, "
                          "Gewinn gesichert".format(trail_note, stop_level,
                                                    'darunter' if long_side else 'darueber'))
            else:
                reason = ("Kerzenschluss {} Invalidierung {:.0f}".format(
                    'unter' if long_side else 'ueber', z.invalidation)
                    + (" — harter Boden/Flow gekippt" if conditional_stop else ""))
            signals.append(Signal(cur.ts, st, cur.close, 100, reason))
            # BUGFIX 2026-07-27: hier stand eine handgeschriebene Teil-Ruecksetzung, die
            # entry_ref/entry_pct/liq_exits/high_exits/liq_entries VERGESSEN hat. Folge:
            # (1) entry_pct wuchs ueber alle gestoppten Positionen hinweg immer weiter, der
            # Durchschnitts-Einstand blieb am Preis einer laengst geschlossenen Position
            # haengen -> der nachgezogene Stop (trail_stop) rechnete mit einem falschen
            # Break-even. (2) Die Zaehler liq_exits/high_exits/liq_entries liefen gegen ihr
            # Maximum und schalteten die zugehoerigen Mechanismen still ab, bis zufaellig
            # einmal ueber VERKAUF_REST geschlossen wurde. Jetzt derselbe Reset wie ueberall.
            _reset_position(pos)
            pos.last_stop_ts = cur.ts        # E13: Merker fuer die Sperrfrist (cooldown_h)
        else:
            # Mehrtages-Kaufleiter (E9.5): neue Tiefkerze IN der Retracement-Zone (ueber
            # Invalidierung, unter 0.5) mit Flow-Bestaetigung -> kleine Tranche nachlegen.
            if buy_ladder and made_new_extreme and pos.buy_rungs < MAX_BUY_RUNGS \
                    and pos.state in (PosState.T1, PosState.CORE, PosState.FULL) \
                    and _darf_aufstocken():
                if long_side:
                    in_zone = z.invalidation < cur.low <= z.level_05
                    ladder_ok = _confirm_long()
                    nk = SignalType.NACHKAUF
                else:
                    in_zone = z.level_05 <= cur.high < z.invalidation
                    ladder_ok = _confirm_short()
                    nk = SignalType.SHORT_NACHLEGEN
                # E13: In einen ungesunden Abverkauf wird auch nicht NACHgekauft. Genau
                # das war Kaisers Beispiel 16.06.: Ersteinstieg, dann drei Nachkaeufe in
                # einen weiter fallenden Markt, dann Stop.
                if in_zone and ladder_ok and _healthy(long_side):
                    signals.append(Signal(cur.ts, nk, cur.close, BUY_LADDER_TRANCHE,
                                          f"Mehrtages-Leiter: Nachkauf in die Schwaeche, Struktur intakt ({pattern.name})",
                                          stop_ref=z.invalidation))
                    pos.buy_rungs += 1
            # Konfluenz-Nachkauf an der Liquidationszone (E10.3): Fib-Zone UND historisches
            # Liquidations-Cluster fallen zusammen — Furkans "hier liegt auch das Golden
            # Pocket, da wuerde ich aufstocken". Struktur muss intakt sein (ueber der
            # Invalidierung, im Retracement-Bereich) und der Order-Flow bestaetigen.
            if liq_entry == "boost" and pos.liq_entries < MAX_LIQ_ENTRIES \
                    and pos.state in (PosState.T1, PosState.CORE, PosState.FULL) \
                    and _darf_aufstocken():
                if long_side:
                    treffer = _liq_hit(cur.low, "long")
                    in_struct = z.invalidation < cur.low <= z.level_05
                    flow_ok = _confirm_long()
                    nk = SignalType.NACHKAUF
                else:
                    treffer = _liq_hit(cur.high, "short")
                    in_struct = z.level_05 <= cur.high < z.invalidation
                    flow_ok = _confirm_short()
                    nk = SignalType.SHORT_NACHLEGEN
                if treffer is not None and in_struct and flow_ok:
                    signals.append(Signal(cur.ts, nk, cur.close, LIQ_ENTRY_TRANCHE,
                                          f"Konfluenz: Fib-Zone + Liquidationszone {treffer:.0f} "
                                          f"— aufstocken ({pattern.name})",
                                          stop_ref=z.invalidation))
                    pos.liq_entries += 1
            # Teilverkauf an Liquidationen (E9.11): erst verkaufen, wenn der Kurs die
            # Liquidationszone erreicht — nicht schon am rechnerischen Fib-Ziel.
            if liq_exit != "off" and pos.liq_exits < MAX_LIQ_EXITS \
                    and pos.state in (PosState.T1, PosState.CORE, PosState.FULL) \
                    and _darf_teilverkaufen():
                # Long verkauft in Short-Liquidationen (Squeeze nach oben), Short in
                # Long-Liquidationen (Flush nach unten).
                seite = "short" if long_side else "long"
                grund = None
                if liq_exit in ("spike", "both") and liq_cascade(flow, seite):
                    grund = f"Liquidations-Kaskade laeuft ({pattern.name})"
                if grund is None and liq_exit in ("zone", "both"):
                    # NUR Kerzen VOR der aktuellen -> keine Kenntnis der Zukunft
                    lv = liq_levels(candles[:-1], flow[:-1], seite)
                    treffer = in_liq_zone(cur.high if long_side else cur.low, lv)
                    if treffer is not None:
                        grund = f"Liquidationszone {treffer:.0f} erreicht (historische Kaskade)"
                if grund is not None:
                    lt = SignalType.TEILVERKAUF_LADDER if long_side else SignalType.SHORT_TP_LADDER
                    signals.append(Signal(cur.ts, lt, cur.close, LADDER_TRANCHE,
                                          f"Teilgewinn an Liquidationen: {grund}"))
                    pos.liq_exits += 1
            # Teilverkauf am letzten Hoch (E10.2): Kurs laeuft an das letzte bestaetigte
            # Pivot-Hoch heran -> dort sitzt das Angebot, ein Stueck davor raus.
            if high_exit != "off" and pos.high_exits < MAX_HIGH_EXITS \
                    and pos.state in (PosState.T1, PosState.CORE, PosState.FULL) \
                    and _darf_teilverkaufen():
                ref = candles[-2].close if len(candles) >= 2 else cur.open
                lvl = next_pivot_beyond(pivots, ref, long_side)
                if lvl is not None:
                    nah = (cur.high >= lvl * (1 - HIGH_EXIT_TOL)) if long_side \
                        else (cur.low <= lvl * (1 + HIGH_EXIT_TOL))
                    # "weak": nur verkaufen, wenn der Anlauf OHNE Spot-Nachfrage passiert
                    if long_side:
                        spot_traegt = len(flow) >= 3 and flow[-1].spot_cvd > flow[-3].spot_cvd
                    else:
                        spot_traegt = len(flow) >= 3 and flow[-1].spot_cvd < flow[-3].spot_cvd
                    ok = nah and (high_exit == "on" or not spot_traegt)
                    if ok:
                        ht = SignalType.TEILVERKAUF_LADDER if long_side else SignalType.SHORT_TP_LADDER
                        zusatz = "" if high_exit == "on" else ", Anlauf ohne Spot-Nachfrage"
                        signals.append(Signal(cur.ts, ht, cur.close, LADDER_TRANCHE,
                                              f"Teilgewinn am letzten {'Hoch' if long_side else 'Tief'} "
                                              f"{lvl:.0f}{zusatz}"))
                        pos.high_exits += 1
            # Upgrade T1 -> CORE: Kernposition im Golden Pocket (KAUF 2 / SHORT 2)
            if pos.state == PosState.T1 and _darf_aufstocken():
                in_gp = (z.gp_lower <= cur.low <= z.gp_upper) if long_side \
                    else (z.gp_upper <= cur.high <= z.gp_lower)
                if in_gp:
                    if long_side:
                        if _confirm_long():
                            signals.append(Signal(cur.ts, SignalType.KAUF_2, z.gp_upper,
                                                  TRANCHEN["CORE"],
                                                  f"Golden Pocket {z.gp_lower:.0f}-{z.gp_upper:.0f} + Bestaetigung ({pattern.name})",
                                                  stop_ref=z.invalidation))
                            pos.state = PosState.CORE
                    else:
                        if _confirm_short():
                            signals.append(Signal(cur.ts, SignalType.SHORT_2, z.gp_upper,
                                                  TRANCHEN["CORE"],
                                                  f"Golden Pocket {z.gp_upper:.0f}-{z.gp_lower:.0f} + Bestaetigung ({pattern.name})",
                                                  stop_ref=z.invalidation))
                            pos.state = PosState.CORE
            # Nachkauf am 0.786
            if pos.state in (PosState.T1, PosState.CORE) and _darf_aufstocken():
                touch = (cur.low <= z.level_0786) if long_side else (cur.high >= z.level_0786)
                if touch:
                    nk = SignalType.NACHKAUF if long_side else SignalType.SHORT_NACHLEGEN
                    signals.append(Signal(cur.ts, nk, z.level_0786, TRANCHEN["FULL"],
                                          "0.786-Zone erreicht, Struktur intakt",
                                          stop_ref=z.invalidation))
                    pos.state = PosState.FULL
            # Gestaffelte Zwischen-Teilgewinne (E8.2): kleine Tranchen an 0.8/0.9-Ext
            # VOR dem 1.0-Ziel, hoechstens eine Stufe je Kerze (Leiter ueber Tage)
            if tp_ladder and pos.state in (PosState.T1, PosState.CORE, PosState.FULL) \
                    and pos.tp_rungs < len(LADDER_FACTORS) and _darf_teilverkaufen():
                rung_ext = z.ext_target(pos.retrace_extreme, LADDER_FACTORS[pos.tp_rungs])
                rung_hit = (cur.high >= rung_ext) if long_side else (cur.low <= rung_ext)
                if rung_hit:
                    lt = SignalType.TEILVERKAUF_LADDER if long_side else SignalType.SHORT_TP_LADDER
                    signals.append(Signal(cur.ts, lt, rung_ext, LADDER_TRANCHE,
                                          f"Leiter-Teilgewinn an Extension {LADDER_FACTORS[pos.tp_rungs]:.1f} ({rung_ext:.0f})"))
                    pos.tp_rungs += 1
            # Teilgewinne an Extensions
            if pos.state in (PosState.T1, PosState.CORE, PosState.FULL) \
                    and _darf_teilverkaufen():
                hit1 = (cur.high >= ext1) if long_side else (cur.low <= ext1)
                if hit1:
                    tp = SignalType.TEILVERKAUF_1 if long_side else SignalType.SHORT_TP_1
                    signals.append(Signal(cur.ts, tp, ext1, TRANCHEN["TP1"],
                                          f"Extension 1.0 erreicht ({ext1:.0f})"))
                    pos.state = PosState.TP1
            if pos.state == PosState.TP1 and _darf_teilverkaufen():
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
                    _reset_position(pos)
            # Rest freigeben, wenn die Struktur veraltet ist (E9.9). Nur nach Teilgewinnen
            # (TP1/TP2) — beim Positionsaufbau bleibt der Stop zustaendig.
            if release_stale_rest and pos.state in (PosState.TP1, PosState.TP2) \
                    and imp is not None and pos.zones is not None:
                alt = (pos.zones.impulse.start.ts, pos.zones.impulse.end.ts)
                if (imp.start.ts, imp.end.ts) != alt:
                    ex = SignalType.VERKAUF_REST if long_side else SignalType.SHORT_COVER_REST
                    signals.append(Signal(cur.ts, ex, cur.close, 20,
                                          f"Struktur veraltet: neuer Impuls bestaetigt "
                                          f"({imp.start.price:.0f}->{imp.end.price:.0f}) — Rest freigegeben"))
                    _reset_position(pos)
            # Warnung waehrend offener Long-Position
            if long_side and pos.state in (PosState.T1, PosState.CORE, PosState.FULL) \
                    and pattern == Pattern.DERIVATE_PUMP:
                signals.append(Signal(cur.ts, SignalType.WARNUNG, cur.close, 0,
                                      "Derivate-Pump: anfaellig fuer Long-Flush"))

    # Durchschnitts-Einstand fortschreiben (E9.10): tranchengewichtet ueber alle
    # Einstiegs-Signale dieser Kerze. Zentral hier, damit kein Einstiegspfad vergessen
    # wird (0.5-Level, Golden Pocket, Flush, 0.786, Kauf-/Dip-Leiter).
    for s in signals:
        if s.type in _ENTRY_TYPES and s.tranche_pct > 0:
            tot = pos.entry_pct + s.tranche_pct
            base = pos.entry_ref if pos.entry_ref is not None else s.price
            pos.entry_ref = (base * pos.entry_pct + s.price * s.tranche_pct) / tot
            pos.entry_pct = tot

    # E18.3: Mit dem ERSTEN realisierten Teilgewinn wird die Zielreferenz festgehalten.
    if freeze_targets and pos.ziel_extrem is None and pos.retrace_extreme is not None \
            and any(s.type in _TEILVERKAUF_TYPES for s in signals):
        pos.ziel_extrem = pos.retrace_extreme

    pos.last_signal_ts = cur.ts
    return signals
