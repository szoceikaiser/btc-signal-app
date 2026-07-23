"""Unit-Tests der Kern-Engine (E4a). Ausfuehren: python -m pytest test_strategy_core.py -q

Die Fib-Testvektoren stammen 1:1 aus dem Video (Frame 17:55 und 18:55) und aus dem
Gegencheck (docs/GEGENCHECK.md): reale Zahlen, keine Fantasiewerte.
"""

from strategy_core import (Candle, FlowPoint, Pattern, Pivot, Impulse, PosState,
                           Position, SignalType, classify_pattern, evaluate,
                           fib_zones, find_pivots, last_significant_impulse)


def c(ts, o, h, l, cl):
    return Candle(ts, o, h, l, cl)


# ------------------------------------------------- Fib: Zahlen aus dem Video

def video_impulse():
    # Frame 17:55: Impuls Tief 86.348,7 -> Hoch 94.764,8 (TradingView, 4h, 08.01.2026)
    return Impulse(Pivot(0, 0, 86348.7, "L"), Pivot(1, 1, 94764.8, "H"))


def test_fib_zones_gegen_video_werte():
    z = fib_zones(video_impulse())
    assert abs(z.gp_upper - 89563.6) < 1.0      # 0.618 im Video: 89.563,6
    assert abs(z.gp_lower - 89294.3) < 1.0      # 0.65  im Video: 89.294,3
    assert abs(z.level_05 - 90556.75) < 1.0     # 0.5   im Video: 90.556,x
    assert abs(z.level_0786 - 88149.7) < 1.0    # 0.786 im Video: 88.149,7
    assert z.invalidation == 86348.7


def test_extension_ziel_trifft_jan14_hoch():
    # Gegencheck: Retracement-Tief 08.01. = 89.311 -> 1:1-Ziel ~97.727;
    # reales Hoch 14.01.2026: 97.924 (Abweichung < 0,3 %)
    z = fib_zones(video_impulse())
    ziel = z.ext_target(89311.0, 1.0)
    assert abs(ziel - 97727.1) < 1.0
    assert abs(ziel - 97924.0) / 97924.0 < 0.003


def test_fib_zones_short_richtung():
    # Abwaerts-Impuls: Levels liegen OBERHALB des Tiefs
    imp = Impulse(Pivot(0, 0, 100.0, "H"), Pivot(1, 1, 90.0, "L"))
    z = fib_zones(imp)
    assert z.level_05 == 95.0
    assert abs(z.gp_upper - 96.18) < 0.01
    assert abs(z.gp_lower - 96.5) < 0.01
    assert z.invalidation == 100.0
    assert abs(z.ext_target(96.0, 1.0) - 86.0) < 0.01  # Ziel nach unten


# ------------------------------------------------------------- Swings/Impuls

def zigzag_candles():
    data = [
        (0, 104, 105, 103, 104), (1, 103, 104, 102, 103), (2, 102, 103, 100, 101),
        (3, 103, 105, 102, 104), (4, 106, 108, 105, 107), (5, 108, 110, 107, 109),
        (6, 108, 109, 106, 107), (7, 106, 107, 105.5, 106),
    ]
    return [c(*row) for row in data]


def test_find_pivots_und_impuls():
    candles = zigzag_candles()
    pivots = find_pivots(candles, n=2)
    kinds = [(p.kind, p.price) for p in pivots]
    assert ("L", 100) in kinds and ("H", 110) in kinds
    imp = last_significant_impulse(candles, pivots, k_atr=3.0, min_pct=0.03)
    assert imp is not None and imp.up
    assert imp.start.price == 100 and imp.end.price == 110


# ------------------------------------------------------------------ Kompass

def flow_series(spot, fut, oi, funding):
    return [FlowPoint(i, s, f, o, fu) for i, (s, f, o, fu)
            in enumerate(zip(spot, fut, oi, funding))]


def flat_candles(n, price):
    return [c(i, price, price * 1.001, price * 0.999, price) for i in range(n)]


def trend_candles(n, start, end):
    step = (end - start) / (n - 1)
    out = []
    for i in range(n):
        p = start + step * i
        out.append(c(i, p, p * 1.002, p * 0.998, p))
    return out


def test_kompass_muster4_capitulation():
    n = 12
    candles = trend_candles(n, 100000, 93000)                      # -7 % scharf runter
    flow = flow_series(
        spot=[100] * 9 + [95, 100, 106],                           # Spot-CVD dreht hoch
        fut=[100 - i * 3 for i in range(n)],
        oi=[1000 - i * 8 for i in range(n)],                       # OI-Wipeout (-8,8 %)
        funding=[0.0001 - i * 0.00002 for i in range(n)])
    assert classify_pattern(candles, flow) == Pattern.CAPITULATION_RESET


def test_kompass_muster2_derivate_pump():
    n = 12
    candles = trend_candles(n, 100000, 103000)                     # +3 %
    flow = flow_series(
        spot=[100] * n,                                            # Spot flach
        fut=[100 + i * 10 for i in range(n)],                      # Futures-CVD stark hoch
        oi=[1000 + i * 5 for i in range(n)],                       # OI +5,5 %
        funding=[0.00005 + i * 0.00002 for i in range(n)])         # Funding zieht an
    assert classify_pattern(candles, flow) == Pattern.DERIVATE_PUMP


def test_kompass_muster2_ohne_futures_cvd():
    # US-Geo-Block-Fall: Futures-CVD-Serie ist 0 -> Pump-Erkennung ueber OI+Funding+Spot
    n = 12
    candles = trend_candles(n, 100000, 103000)
    flow = flow_series(
        spot=[100] * n,                                            # Spot flach
        fut=[0] * n,                                               # keine Quelle
        oi=[1000 + i * 5 for i in range(n)],                       # OI +5,5 %
        funding=[0.00005 + i * 0.00002 for i in range(n)])
    assert classify_pattern(candles, flow) == Pattern.DERIVATE_PUMP


def test_kompass_muster3_short_covering():
    n = 12
    candles = trend_candles(n, 100000, 103000)                     # Preis hoch
    flow = flow_series(
        spot=[100] * n,
        fut=[100] * n,
        oi=[1000 - i * 4 for i in range(n)],                       # OI runter -> ohne Neu-Geld
        funding=[0.00002] * n)
    assert classify_pattern(candles, flow) == Pattern.SHORT_COVERING


def test_kompass_muster1_gesunder_trend():
    n = 12
    candles = trend_candles(n, 100000, 102000)                     # +2 %
    flow = flow_series(
        spot=[100 + i * 5 for i in range(n)],                      # Spot traegt
        fut=[100 + i * 5 for i in range(n)],                       # nicht ueberzogen
        oi=[1000 + i * 2 for i in range(n)],                       # moderat
        funding=[0.00005] * n)
    assert classify_pattern(candles, flow) == Pattern.GESUNDER_TREND


# ------------------------------------------------- Zustandsmaschine (Long)

def neg_funding_flow(n=4):
    return [FlowPoint(i, 100 + i, 100, 1000, -0.0001) for i in range(n)]


def run_incremental(all_candles, flow, pos, **kw):
    """Simuliert Produktionsbetrieb: evaluate nach jeder abgeschlossenen Kerze."""
    collected = []
    for i in range(1, len(all_candles) + 1):
        collected += evaluate(all_candles[:i], flow, pos, **kw)
    return collected


def test_long_lebenszyklus_kauf1_kauf2_tp1_tp2():
    base = zigzag_candles()
    # Impuls 100->110: 0.5=105, GP=103.82-103.5, ext ab retrace_extreme
    path = base + [
        c(8, 106, 106.5, 104.5, 105.5),    # beruehrt 0.5 -> KAUF 1
        c(9, 105, 105.5, 103.6, 104.5),    # Golden Pocket -> KAUF 2 (Funding negativ)
        c(10, 104, 114.0, 104.0, 113.5),   # Extension 1.0 (103.6+10=113.6) -> TEILVERKAUF 1
        c(11, 113, 120.5, 113.0, 120.0),   # Extension 1.618 (119.78) -> TEILVERKAUF 2
    ]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2)
    types = [s.type for s in sigs]
    assert types == [SignalType.KAUF_1, SignalType.KAUF_2,
                     SignalType.TEILVERKAUF_1, SignalType.TEILVERKAUF_2]
    assert pos.state == PosState.TP2
    k1 = sigs[0]
    assert abs(k1.price - 105.0) < 0.01 and k1.tranche_pct == 25 and k1.stop_ref == 100


def test_capitulation_einstieg_bei_gp_durchschlag():
    # Flush-Kerze: Tief 101.5 durchschlaegt das GP (103.5-103.82),
    # Schluss 104 liegt ueber der Invalidierung (100) -> KAUF 2 mit 75 %
    base = zigzag_candles()
    path = base + [c(8, 105.5, 106.0, 101.5, 104.0)]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2)
    assert [s.type for s in sigs] == [SignalType.KAUF_2]
    assert sigs[0].tranche_pct == 75 and "Capitulation" in sigs[0].reason
    assert pos.state == PosState.CORE and pos.retrace_extreme == 101.5


def test_kein_capitulation_einstieg_bei_schluss_unter_invalidierung():
    # Gleiche Kerze, aber Schluss UNTER der Invalidierung -> kein Einstieg
    base = zigzag_candles()
    path = base + [c(8, 105.5, 106.0, 98.0, 99.5)]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2)
    assert sigs == [] and pos.state == PosState.FLAT


def test_long_stoploss_bei_schluss_unter_invalidierung():
    base = zigzag_candles()
    path = base + [
        c(8, 106, 106.5, 104.5, 105.5),    # KAUF 1
        c(9, 104, 104.5, 98.5, 99.0),      # Schluss 99 < 100 -> STOPLOSS
    ]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2)
    assert [s.type for s in sigs] == [SignalType.KAUF_1, SignalType.STOPLOSS]
    assert pos.state == PosState.FLAT and pos.direction == "NONE"


def test_short_einstieg_am_05_level():
    data = [
        (0, 96, 97, 95, 96), (1, 97, 98, 96, 97), (2, 99, 100, 98, 99),
        (3, 97, 98, 95, 96), (4, 94, 95, 92, 93), (5, 92, 93, 90, 91),
        (6, 92, 94, 91, 93), (7, 93.5, 94.5, 93, 94),
        (8, 94, 95.5, 93.5, 95),           # beruehrt 0.5 (95) -> SHORT 1
    ]
    pos = Position()
    sigs = run_incremental([c(*row) for row in data], [], pos, pivot_n=2)
    assert [s.type for s in sigs] == [SignalType.SHORT_1]
    assert pos.direction == "SHORT" and pos.state == PosState.T1
    assert sigs[0].stop_ref == 100


def test_dedupe_gleiche_kerze_keine_doppelsignale():
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5)]
    pos = Position()
    first = run_incremental(path, neg_funding_flow(), pos, pivot_n=2)
    again = evaluate(path, neg_funding_flow(), pos, pivot_n=2)
    assert len(first) == 1 and again == []
