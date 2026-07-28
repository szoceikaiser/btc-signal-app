"""Unit-Tests der Kern-Engine (E4a). Ausfuehren: python -m pytest test_strategy_core.py -q

Die Fib-Testvektoren stammen 1:1 aus dem Video (Frame 17:55 und 18:55) und aus dem
Gegencheck (docs/GEGENCHECK.md): reale Zahlen, keine Fantasiewerte.
"""

from strategy_core import (Candle, FlowPoint, LADDER_TRANCHE, Pattern, Pivot, Impulse,
                           PosState, Position, SignalType, classify_pattern,
                           daily_fib_zone, daily_trend, ema, evaluate, fib_zones,
                           find_pivots, in_liq_zone, last_significant_impulse,
                           liq_cascade, liq_levels, next_pivot_beyond, resample_daily)

DAY_MS = 86_400_000
H4_MS = 4 * 3600 * 1000


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
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2,
                           tp_ladder=False, buy_ladder=False, flush_entry="off")
    types = [s.type for s in sigs]
    assert types == [SignalType.KAUF_1, SignalType.KAUF_2,
                     SignalType.TEILVERKAUF_1, SignalType.TEILVERKAUF_2]
    assert pos.state == PosState.TP2
    k1 = sigs[0]
    assert abs(k1.price - 105.0) < 0.01 and k1.tranche_pct == 25 and k1.stop_ref == 100


def test_tp_ladder_gestaffelte_teilgewinne():
    # E8.2: Impuls 100->110, Einstieg 0.5/GP; retrace_extreme=103.6 ->
    # Ext 0.8=111.6, 0.9=112.5, 1.0=113.6. Preis steigt gestaffelt: je Kerze eine
    # Leiter-Stufe (15 %), dann das 1.0-Ziel. tp_ladder=True.
    base = zigzag_candles()
    path = base + [
        c(8, 106, 106.5, 104.5, 105.5),    # 0.5 -> KAUF 1
        c(9, 105, 105.5, 103.6, 104.5),    # GP -> KAUF 2
        c(10, 111, 112.0, 110.5, 111.8),   # >=111.6 (<112.6) -> Leiter-Stufe 0.8
        c(11, 112, 112.8, 111.5, 112.6),   # >=112.6 (<113.6) -> Leiter-Stufe 0.9
        c(12, 113, 114.0, 112.5, 113.8),   # >=113.6 -> TEILVERKAUF 1
    ]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2,
                           tp_ladder=True, buy_ladder=False, flush_entry="off")
    assert [s.type for s in sigs] == [
        SignalType.KAUF_1, SignalType.KAUF_2,
        SignalType.TEILVERKAUF_LADDER, SignalType.TEILVERKAUF_LADDER,
        SignalType.TEILVERKAUF_1]
    ladder = [s for s in sigs if s.type == SignalType.TEILVERKAUF_LADDER]
    assert [round(s.price, 1) for s in ladder] == [111.6, 112.6]
    assert all(s.tranche_pct == 15 for s in ladder) and pos.tp_rungs == 2

    # Mit tp_ladder=False: dieselben Kerzen erzeugen keine Leiter-Stufen
    pos2 = Position()
    sigs2 = run_incremental(path, neg_funding_flow(), pos2, pivot_n=2,
                            tp_ladder=False, buy_ladder=False, flush_entry="off")
    assert [s.type for s in sigs2] == [
        SignalType.KAUF_1, SignalType.KAUF_2, SignalType.TEILVERKAUF_1]


def test_capitulation_einstieg_modus_t1():
    # Flush-Kerze: Tief 101.5 durchschlaegt das GP (103.5-103.82), Schluss 104 ueber
    # der Invalidierung (100) -> Modus "t1": kleine erste Tranche (Ladder bleibt).
    # Default ist "off" (Backtest 23.07.) -> ohne Angabe kein Signal (separater Test).
    base = zigzag_candles()
    path = base + [c(8, 105.5, 106.0, 101.5, 104.0)]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, flush_entry="t1")
    assert [s.type for s in sigs] == [SignalType.KAUF_1]
    assert sigs[0].tranche_pct == 25 and "Capitulation" in sigs[0].reason
    assert pos.state == PosState.T1 and pos.retrace_extreme == 101.5


def test_flush_off_kein_signal():
    base = zigzag_candles()
    path = base + [c(8, 105.5, 106.0, 101.5, 104.0)]
    pos = Position()
    assert run_incremental(path, neg_funding_flow(), pos, pivot_n=2, flush_entry="off") == []


def test_capitulation_einstieg_modus_core_und_off():
    base = zigzag_candles()
    path = base + [c(8, 105.5, 106.0, 101.5, 104.0)]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, flush_entry="core")
    assert [s.type for s in sigs] == [SignalType.KAUF_2] and sigs[0].tranche_pct == 75
    pos2 = Position()
    sigs2 = run_incremental(path, neg_funding_flow(), pos2, pivot_n=2, flush_entry="off")
    assert sigs2 == [] and pos2.state == PosState.FLAT


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


# ------------------------------------------- E8.5-Filter (bessere Einstiege)

def test_resample_daily_und_ema():
    cs = []
    for d in range(2):
        base = 100 + d * 10
        for j in range(6):
            cs.append(c(d * DAY_MS + j * H4_MS, base, base + 2, base - 2, base + 1))
    daily = resample_daily(cs)
    assert len(daily) == 2
    assert daily[0].open == 100 and daily[0].high == 102 and daily[0].low == 98
    assert daily[1].close == 111                      # letzter 4h-Schluss von Tag 1
    assert round(ema([100, 110], 2), 2) == round(110 * 2 / 3 + 100 / 3, 2)


def test_daily_trend_richtung():
    rising = [c(d * DAY_MS, 80 + d, 81 + d, 79 + d, 80 + d) for d in range(12)]
    close, e = daily_trend(rising, 50)
    assert close > e                                  # Aufwaerts: Preis ueber EMA
    falling = [c(d * DAY_MS, 100 - d, 101 - d, 99 - d, 100 - d) for d in range(12)]
    close, e = daily_trend(falling, 50)
    assert close < e                                  # Abwaerts: Preis unter EMA


def pos_funding_cvdup_flow(n=4):
    # Spot-CVD steigt (cvd_up), aber Funding positiv -> lockere Bestaetigung passt,
    # strenge (cvd_up UND funding<=0) nicht.
    return [FlowPoint(i, 100 + i, 100, 1000, 0.0002) for i in range(n)]


def test_strict_confirm_verlangt_beide_bestaetigungen():
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5),    # 0.5 -> KAUF 1
                   c(9, 105, 105.5, 103.6, 104.5)]    # GP -> KAUF 2 (Upgrade)
    pos = Position()
    loose = run_incremental(path, pos_funding_cvdup_flow(), pos, pivot_n=2,
                            buy_ladder=False, flush_entry="off")
    assert [s.type for s in loose] == [SignalType.KAUF_1, SignalType.KAUF_2]
    pos2 = Position()
    strict = run_incremental(path, pos_funding_cvdup_flow(), pos2,
                             pivot_n=2, strict_confirm=True, buy_ladder=False, flush_entry="off")
    assert [s.type for s in strict] == [SignalType.KAUF_1]   # KAUF 2 blockiert


def _downtrend_long_series():
    """14 Tage seitwaerts auf hohem Niveau (100, kein signifikanter Impuls) -> danach
    lokaler Aufwaerts-Impuls 88->96 mit Ruecklauf ins Golden Pocket (~90.9). Der
    Tages-Schluss (~92) liegt klar UNTER der Tages-EMA (~100): 1D-Trend abwaerts."""
    cs, ts = [], 0

    def add(o, h, l, cl):
        nonlocal ts
        cs.append(c(ts, o, h, l, cl))
        ts += H4_MS

    for _ in range(14):
        for j in range(6):
            p = 100 + (0.3 if j % 2 else -0.3)        # winzige Wiggle, kein Impuls
            add(p, p + 0.4, p - 0.4, p)
    for _ in range(3):
        add(90, 90.5, 88, 88)                         # lokales Tief 88
    for _ in range(3):
        add(90, 96, 90, 96)                           # lokales Hoch 96
    add(94, 94.5, 90.9, 92)                           # Ruecklauf ins GP (88->96)
    return cs


def test_trend_filter_blockt_long_gegen_1d_trend():
    down = _downtrend_long_series()
    flow = [FlowPoint(i, 100 + i, 100, 1000, -0.0001) for i in range(len(down))]
    # Ohne Trendfilter feuert der Long (GP-Ruecklauf + Bestaetigung)
    pos = Position()
    sig_off = run_incremental(down, flow, pos, pivot_n=2, bias_short=False)
    assert any(s.type == SignalType.KAUF_2 for s in sig_off)
    # Mit Trendfilter: Preis unter der Tages-EMA -> Long wird blockiert
    pos2 = Position()
    sig_on = run_incremental(down, flow, pos2, pivot_n=2, bias_short=False,
                             trend_filter=True)
    assert not any(s.type == SignalType.KAUF_2 for s in sig_on)


def test_muster4_via_long_liq_kaskade_ohne_oi_wipeout():
    # E9.1: echte Long-Liquidations-Kaskade belegt die Kapitulation direkt,
    # auch wenn der OI-Wipeout-Schwellwert nicht erreicht ist.
    n = 12
    candles = trend_candles(n, 100000, 95000)          # -5 % (scharf runter)
    flow = [FlowPoint(i, float(i), 0.0, 1000.0, 0.0,   # OI konstant, Spot-CVD dreht hoch
                      long_liq=(1_000_000.0 if i == n - 1 else 1000.0))
            for i in range(n)]
    assert classify_pattern(candles, flow) == Pattern.CAPITULATION_RESET
    # Ohne die Kaskade (gleichmaessige Liq) und ohne OI-Wipeout: kein Muster 4
    flow_flat = [FlowPoint(i, float(i), 0.0, 1000.0, 0.0, long_liq=1000.0) for i in range(n)]
    assert classify_pattern(candles, flow_flat) != Pattern.CAPITULATION_RESET


def test_muster3_via_short_liq_kaskade():
    n = 12
    candles = trend_candles(n, 100000, 103000)         # +3 % (>= sharp/2)
    flow = [FlowPoint(i, 0.0, 0.0, 1000.0, 0.0,
                      short_liq=(1_000_000.0 if i == n - 1 else 1000.0))
            for i in range(n)]
    assert classify_pattern(candles, flow) == Pattern.SHORT_COVERING


def test_daily_fib_zone_liefert_zone():
    # Genug Tage fuer 1D-Pivots (n=5): klarer Impuls 100->140 mit Ruecklauf
    daily_closes = [100, 100, 100, 100, 100, 100, 120, 140, 140, 140,
                    140, 140, 130, 125, 120]
    cs = [c(d * DAY_MS, p, p + 1, p - 1, p) for d, p in enumerate(daily_closes)]
    z = daily_fib_zone(cs, pivot_n=5)
    assert z is not None and z.impulse.up
    assert z.gp_lower < z.level_05                    # Zonen korrekt geordnet


# ------------------------------------------- E9.3: bedingter Stop / Nachkauf

def bearish_flow(n=4):
    # Funding positiv, Spot-CVD faellt -> _confirm_long() ist False (Flow kippt)
    return [FlowPoint(i, 100 - i, 100, 1000, 0.0002) for i in range(n)]


def test_conditional_stop_nachkauf_wenn_flow_bullisch():
    base = zigzag_candles()                           # Impuls 100->110, Invalidierung 100
    path = base + [c(8, 106, 106.5, 104.5, 105.5),    # KAUF 1
                   c(9, 104, 104.5, 98.5, 99.0)]      # Schluss 99 < 100, aber Flow bullisch
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, conditional_stop=True)
    types = [s.type for s in sigs]
    assert SignalType.STOPLOSS not in types           # kein pauschaler Stop
    assert SignalType.NACHKAUF in types and pos.dip_buys >= 1
    assert pos.state != PosState.FLAT                 # Position bleibt offen
    assert any("Bedingter Nachkauf" in s.reason for s in sigs)


def test_conditional_stop_stoppt_bei_hartem_boden():
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5),
                   c(9, 104, 104.5, 93, 94)]          # Schluss 94 < 95 (harter Boden) -> Stop
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, conditional_stop=True)
    assert [s.type for s in sigs] == [SignalType.KAUF_1, SignalType.STOPLOSS]
    assert pos.state == PosState.FLAT


def test_conditional_stop_stoppt_wenn_flow_kippt():
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5),
                   c(9, 104, 104.5, 98.5, 99.0)]      # Schluss 99, aber Flow baerisch -> Stop
    pos = Position()
    sigs = run_incremental(path, bearish_flow(), pos, pivot_n=2, conditional_stop=True)
    assert [s.type for s in sigs] == [SignalType.KAUF_1, SignalType.STOPLOSS]
    assert pos.state == PosState.FLAT


# ------------------------------------------- E9.5: Mehrtages-Kaufleiter

def test_buy_ladder_nachkauf_bei_neuen_tiefkerzen_in_zone():
    # Impuls 100->110: Invalidierung 100, 0.5=105, GP-Oberkante ~103.82. Neue Tiefkerzen
    # zwischen 103.82 und 105 (in der Zone, ueber Invalidierung) -> Leiter-Nachkaeufe.
    base = zigzag_candles()
    path = base + [
        c(8, 106, 106.5, 104.5, 105.5),      # KAUF 1 (0.5), Extrem 104.5
        c(9, 105, 105.2, 104.0, 104.5),      # neues Tief 104.0 -> Leiter (Stufe 1)
        c(10, 104.5, 104.8, 103.9, 104.2),   # neues Tief 103.9 -> Leiter (Stufe 2)
        c(11, 104.2, 104.5, 103.85, 104.0),  # neues Tief 103.85 -> Leiter (Stufe 3)
    ]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, buy_ladder=True)
    ladder = [s for s in sigs if "Mehrtages-Leiter" in s.reason]
    assert len(ladder) == 3 and pos.buy_rungs == 3       # gedeckelt durch MAX_BUY_RUNGS
    assert all(s.type == SignalType.NACHKAUF and s.tranche_pct == 15 for s in ladder)
    assert sigs[0].type == SignalType.KAUF_1
    # Ohne buy_ladder: keine Leiter-Nachkaeufe
    pos2 = Position()
    sigs2 = run_incremental(path, neg_funding_flow(), pos2, pivot_n=2, buy_ladder=False)
    assert not any("Mehrtages-Leiter" in s.reason for s in sigs2)


# ------------------------------- E9.9: Rest-Freigabe bei veralteter Struktur

def _tp1_dann_neue_struktur():
    """Impuls 100->110, Einstieg am 0.5 (105), Extension 1.0 bei 114.5 -> TP1.
    Danach laeuft der Kurs weiter hoch; das Tief 104.5 (Kerze 8) wird mit n=2 als neues
    Pivot bestaetigt -> der letzte signifikante Impuls ist dann 110->104.5, also ein
    ANDERER als der, auf dem die Position sitzt."""
    return zigzag_candles() + [
        c(8, 106, 106.5, 104.5, 105.5),      # KAUF 1 am 0.5, Extrem 104.5
        c(9, 105, 115.0, 104.6, 114.8),      # >= 114.5 -> TEILVERKAUF 1, Zustand TP1
        c(10, 114, 116.0, 113.0, 115.0),     # Pivot-Tief 104.5 jetzt bestaetigt
        c(11, 115, 118.0, 114.0, 117.0),
    ]


def test_release_stale_rest_gibt_restposition_frei():
    path = _tp1_dann_neue_struktur()
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                           tp_ladder=False, buy_ladder=False, release_stale_rest=True)
    types = [s.type for s in sigs]
    assert types[:2] == [SignalType.KAUF_1, SignalType.TEILVERKAUF_1]
    frei = [s for s in sigs if "Struktur veraltet" in s.reason]
    assert len(frei) == 1 and frei[0].type == SignalType.VERKAUF_REST
    assert frei[0].tranche_pct == 20
    assert pos.state == PosState.FLAT and pos.direction == "NONE"   # Engine wieder frei


def test_ohne_release_bleibt_rest_in_tp_haengen():
    """Das alte Verhalten (Default): der Rest bleibt liegen und blockiert jeden neuen
    Einstieg, weil der Einstiegs-Block nur bei state==FLAT laeuft."""
    path = _tp1_dann_neue_struktur()
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                           tp_ladder=False, buy_ladder=False, release_stale_rest=False)
    assert not any("Struktur veraltet" in s.reason for s in sigs)
    assert pos.state in (PosState.TP1, PosState.TP2)
    assert pos.direction == "LONG"


def test_trail_stop_zieht_auf_einstand_und_sichert_gewinn():
    """E9.10: Nach TEILVERKAUF 1 wandert der Stop auf Break-even/Struktur. Ein Ruecklauf,
    der die alte Invalidierung (100) NICHT erreicht, stoppt jetzt trotzdem — mit Gewinn."""
    base = zigzag_candles()                   # Impuls 100->110, Invalidierung 100
    path = base + [
        c(8, 106, 106.5, 104.5, 105.5),       # KAUF 1 am 0.5 (105) -> Einstand 105
        c(9, 105, 115.0, 104.6, 114.8),       # Extension 1.0 (114.5) -> TEILVERKAUF 1
        c(10, 114, 115.0, 103.0, 103.5),      # Schluss 103.5: ueber 100, aber unter 105
    ]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                           tp_ladder=False, buy_ladder=False, trail_stop=True)
    assert [s.type for s in sigs] == [SignalType.KAUF_1, SignalType.TEILVERKAUF_1,
                                      SignalType.STOPLOSS]
    stop = sigs[-1]
    assert "Nachgezogener Stop" in stop.reason and "Gewinn gesichert" in stop.reason
    assert pos.state == PosState.FLAT          # Engine wieder frei fuer neue Setups

    # Ohne trail_stop bleibt dieselbe Kerze harmlos: Stop steht weiter bei 100
    pos2 = Position()
    sigs2 = run_incremental(path, neg_funding_flow(), pos2, pivot_n=2, bias_short=False,
                            tp_ladder=False, buy_ladder=False, trail_stop=False)
    assert not any(s.type == SignalType.STOPLOSS for s in sigs2)
    assert pos2.state == PosState.TP1          # genau die Blockade, um die es geht


def test_trail_stop_lockert_den_stop_nie():
    """Der nachgezogene Stop darf nie UNTER die Invalidierung rutschen (nur Ratchet)."""
    base = zigzag_candles()
    path = base + [
        c(8, 106, 106.5, 104.5, 105.5),
        c(9, 105, 115.0, 104.6, 114.8),       # TEILVERKAUF 1
        c(10, 114, 115.0, 99.0, 99.5),        # Schluss unter der Invalidierung 100
    ]
    for trail in (True, False):
        pos = Position()
        sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                               tp_ladder=False, buy_ladder=False, trail_stop=trail)
        assert any(s.type == SignalType.STOPLOSS for s in sigs), trail
        assert pos.state == PosState.FLAT


def test_einstand_ist_tranchengewichtet():
    """Der Einstand ist der gewichtete Durchschnitt aller Tranchen, nicht der erste Kauf:
    KAUF 1 (25 % @ 105) + KAUF 2 (50 % @ ~103.82) -> Einstand naeher an KAUF 2."""
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5),     # KAUF 1, 25 % @ 105
                   c(9, 105, 105.5, 103.6, 104.5)]     # KAUF 2, 50 % @ 103.82
    pos = Position()
    run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                    tp_ladder=False, buy_ladder=False)
    assert pos.entry_pct == 75
    erwartet = (105.0 * 25 + 103.82 * 50) / 75
    assert abs(pos.entry_ref - erwartet) < 0.05
    assert pos.entry_ref < 105.0                        # guenstiger als der erste Kauf


def _liq_flow(n, short_liq_last=0.0, short_liq_base=1000.0):
    """Flow mit ruhigen Short-Liquidationen und optionaler Kaskade in der letzten Kerze."""
    return [FlowPoint(i, 100 + i, 100, 1000, -0.0001,
                      short_liq=(short_liq_last if i == n - 1 else short_liq_base))
            for i in range(n)]


def test_liq_exit_spike_verkauft_in_die_kaskade():
    """E9.11: Long-Position + Short-Liquidations-Kaskade -> Teilgewinn (15 %)."""
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5),     # KAUF 1
                   c(9, 105.5, 108.0, 105.0, 107.5)]   # Kaskade laeuft
    pos = Position()
    flow = _liq_flow(len(path), short_liq_last=5_000_000.0)
    sigs = run_incremental(path, flow, pos, pivot_n=2, bias_short=False,
                           tp_ladder=False, buy_ladder=False, liq_exit="spike")
    liq = [s for s in sigs if "Teilgewinn an Liquidationen" in s.reason]
    assert len(liq) == 1 and liq[0].type == SignalType.TEILVERKAUF_LADDER
    assert liq[0].tranche_pct == LADDER_TRANCHE and pos.liq_exits == 1
    assert "Kaskade" in liq[0].reason
    # Default "off": dieselben Daten erzeugen keinen Liquidations-Teilverkauf
    pos2 = Position()
    sigs2 = run_incremental(path, flow, pos2, pivot_n=2, bias_short=False,
                            tp_ladder=False, buy_ladder=False)
    assert not any("Teilgewinn an Liquidationen" in s.reason for s in sigs2)


def test_liq_levels_findet_nur_ausreisser():
    cs = [c(i, 100, 100 + i, 99, 100) for i in range(20)]
    fl = [FlowPoint(i, 0, 0, 1000, 0.0, short_liq=(9_000_000.0 if i == 5 else 1000.0))
          for i in range(20)]
    lv = liq_levels(cs, fl, "short")
    assert len(lv) == 1 and lv[0][0] == cs[5].high          # Kerzen-Hoch als Niveau
    assert in_liq_zone(cs[5].high, lv) == cs[5].high
    assert in_liq_zone(cs[5].high * 1.05, lv) is None       # 5 % weg -> keine Zone


def test_liq_cascade_erkennt_nur_ausschlag():
    ruhig = [FlowPoint(i, 0, 0, 1000, 0.0, short_liq=1000.0) for i in range(12)]
    assert liq_cascade(ruhig, "short") is False
    kaskade = ruhig[:-1] + [FlowPoint(11, 0, 0, 1000, 0.0, short_liq=50_000.0)]
    assert liq_cascade(kaskade, "short") is True
    assert liq_cascade(kaskade, "long") is False            # falsche Seite


def test_liq_exit_zone_nutzt_keine_zukunft():
    """Kausalitaet: die Kaskade der AKTUELLEN Kerze darf keine Zone fuer sich selbst
    erzeugen — sonst wuesste der Backtest die Zukunft."""
    cs = [c(i, 100, 101, 99, 100) for i in range(20)]
    fl = [FlowPoint(i, 0, 0, 1000, 0.0, short_liq=(9_000_000.0 if i == 19 else 1000.0))
          for i in range(20)]
    # Aus allen Kerzen ausser der letzten: kein Ausreisser -> keine Zone
    assert liq_levels(cs[:-1], fl[:-1], "short") == []
    # Erst wenn die Kaskaden-Kerze in der Historie liegt, entsteht ein Niveau
    assert len(liq_levels(cs, fl, "short")) == 1


def run_incremental_flow(all_candles, flow, pos, **kw):
    """Wie run_incremental, schneidet den Flow aber PARALLEL zu den Kerzen mit — noetig,
    sobald der Flow positionsabhaengig ist (Liquidations-Kaskade in einer bestimmten
    Kerze). Genau so ruft die Produktion es auf: evaluate(candles[:i], flow[:i], ...)."""
    collected = []
    for i in range(1, len(all_candles) + 1):
        collected += evaluate(all_candles[:i], flow[:i], pos, **kw)
    return collected


def _liq_entry_pfad():
    """Impuls 100->110 (Tief der Kerze 2 = 100), danach ruhige Kerzen (damit genug
    Historie fuer liq_levels da ist, ohne neue Pivots zu erzeugen), dann Einstieg am
    0.5-Level und ein Ruecklauf auf 100,4 — also an das alte Liquidations-Tief."""
    return zigzag_candles() + [
        # Fuellkerzen: Hochs UND Tiefs leicht fallend, damit sie keine neuen Pivots
        # bilden (sonst kippt der Referenz-Impuls auf 110->105,5 nach unten). Tiefs
        # bleiben ueber dem 0.5-Level (105), also kein vorzeitiger Einstieg.
        c(8, 106.5, 106.4, 105.20, 105.6),
        c(9, 105.6, 106.3, 105.10, 105.4),
        c(10, 105.4, 106.2, 105.05, 105.3),
        c(11, 105.3, 106.5, 104.50, 105.5),   # KAUF 1 am 0.5-Level (105)
        c(12, 104.0, 104.5, 100.40, 101.0),   # zurueck an das Liq-Niveau 100
    ]


def _liq_flow_long(n, tief_kerze: int, betrag: float = 9_000_000.0):
    """Flow mit einer Long-Liquidations-Kaskade in Kerze `tief_kerze`."""
    return [FlowPoint(i, 100 + i, 100, 1000, -0.0001,
                      long_liq=(betrag if i == tief_kerze else 1000.0))
            for i in range(n)]


def test_liq_entry_boost_stockt_bei_konfluenz_auf():
    """E10.3: Fib-Zone UND historisches Long-Liquidations-Cluster fallen zusammen ->
    zusaetzliche Nachkauf-Tranche (Furkans 'hier liegt auch das Golden Pocket')."""
    path = _liq_entry_pfad()
    flow = _liq_flow_long(len(path), tief_kerze=2)      # Kaskade am Tief 100
    pos = Position()
    sigs = run_incremental_flow(path, flow, pos, pivot_n=2, bias_short=False,
                                tp_ladder=False, buy_ladder=False, liq_entry="boost")
    konf = [s for s in sigs if "Konfluenz" in s.reason]
    assert len(konf) == 1 and konf[0].type == SignalType.NACHKAUF
    assert konf[0].tranche_pct == 20 and pos.liq_entries == 1
    assert "Liquidationszone 100" in konf[0].reason
    # Ohne den Schalter: kein Konfluenz-Nachkauf
    pos2 = Position()
    sigs2 = run_incremental_flow(path, flow, pos2, pivot_n=2, bias_short=False,
                                 tp_ladder=False, buy_ladder=False)
    assert not any("Konfluenz" in s.reason for s in sigs2)


def test_liq_entry_filter_blockt_einstieg_ohne_konfluenz():
    """'filter' laesst nur noch Einstiege zu, die auf einem Liquidations-Cluster liegen."""
    path = _liq_entry_pfad()[:-1]                       # ohne den Ruecklauf: nur das 0.5-Level
    flow = _liq_flow_long(len(path), tief_kerze=2)      # Cluster liegt bei 100, nicht 104.5
    pos = Position()
    sigs = run_incremental_flow(path, flow, pos, pivot_n=2, bias_short=False,
                                tp_ladder=False, buy_ladder=False, liq_entry="filter")
    assert sigs == [] and pos.state == PosState.FLAT
    # Ohne Filter feuert derselbe Einstieg normal
    pos2 = Position()
    sigs2 = run_incremental_flow(path, flow, pos2, pivot_n=2, bias_short=False,
                                 tp_ladder=False, buy_ladder=False)
    assert [s.type for s in sigs2] == [SignalType.KAUF_1]


def test_liq_entry_nutzt_nur_vergangene_kerzen():
    """Kausalitaet auch hier: die Liquidation der AKTUELLEN Kerze darf den Einstieg
    nicht selbst rechtfertigen."""
    path = _liq_entry_pfad()
    # Kaskade liegt in der LETZTEN Kerze -> aus candles[:-1] ist sie nicht sichtbar,
    # der Ruecklauf auf 100,4 rechtfertigt sich also nicht selbst.
    flow = _liq_flow_long(len(path), tief_kerze=len(path) - 1)
    pos = Position()
    sigs = run_incremental_flow(path, flow, pos, pivot_n=2, bias_short=False,
                                tp_ladder=False, buy_ladder=False, liq_entry="filter")
    assert sigs == [] and pos.state == PosState.FLAT


def test_next_pivot_beyond():
    piv = [Pivot(0, 0, 100.0, "L"), Pivot(1, 1, 110.0, "H"), Pivot(2, 2, 120.0, "H")]
    assert next_pivot_beyond(piv, 105.0, True) == 110.0     # naechstes Hoch darueber
    assert next_pivot_beyond(piv, 115.0, True) == 120.0
    assert next_pivot_beyond(piv, 130.0, True) is None      # kein Hoch mehr darueber
    assert next_pivot_beyond(piv, 105.0, False) == 100.0    # Short: Tief darunter


def test_high_exit_verkauft_kurz_unter_dem_letzten_hoch():
    """E10.2: Impuls 100->110, Einstieg am 0.5. Das bestaetigte Pivot-Hoch liegt bei 110;
    eine Kerze, die bis 109.6 laeuft (0,4 % darunter), loest den Teilgewinn aus."""
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5),      # KAUF 1
                   c(9, 105.5, 109.6, 105.0, 109.4)]    # Anlauf an das Hoch 110
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                           tp_ladder=False, buy_ladder=False, high_exit="on")
    hoch = [s for s in sigs if "Teilgewinn am letzten Hoch" in s.reason]
    assert len(hoch) == 1 and hoch[0].type == SignalType.TEILVERKAUF_LADDER
    assert hoch[0].tranche_pct == LADDER_TRANCHE and pos.high_exits == 1
    # Default aus: dieselben Kerzen erzeugen keinen Struktur-Teilverkauf
    pos2 = Position()
    sigs2 = run_incremental(path, neg_funding_flow(), pos2, pivot_n=2, bias_short=False,
                            tp_ladder=False, buy_ladder=False)
    assert not any("Teilgewinn am letzten Hoch" in s.reason for s in sigs2)


def test_high_exit_weak_nur_ohne_spot_nachfrage():
    """"weak" verkauft nur, wenn der Anlauf OHNE steigendes Spot-CVD passiert."""
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5),
                   c(9, 105.5, 109.6, 105.0, 109.4)]
    # Spot-CVD steigt -> Ausbruch ist getragen -> "weak" verkauft NICHT
    stark = [FlowPoint(i, 100 + i * 10, 100, 1000, -0.0001) for i in range(4)]
    pos = Position()
    sigs = run_incremental(path, stark, pos, pivot_n=2, bias_short=False,
                           tp_ladder=False, buy_ladder=False, high_exit="weak")
    assert not any("Teilgewinn am letzten Hoch" in s.reason for s in sigs)
    # Spot-CVD faellt -> Anlauf ohne Nachfrage -> "weak" verkauft
    schwach = [FlowPoint(i, 100 - i * 10, 100, 1000, -0.0001) for i in range(4)]
    pos2 = Position()
    sigs2 = run_incremental(path, schwach, pos2, pivot_n=2, bias_short=False,
                            tp_ladder=False, buy_ladder=False, high_exit="weak")
    treffer = [s for s in sigs2 if "Teilgewinn am letzten Hoch" in s.reason]
    assert len(treffer) == 1 and "ohne Spot-Nachfrage" in treffer[0].reason


def test_release_stale_rest_greift_nicht_vor_teilgewinn():
    """Beim Positionsaufbau (T1/CORE/FULL) darf die Freigabe NICHT feuern — dort ist
    der Stop zustaendig, sonst wuerde jede neue Pivot-Bestaetigung die Position werfen."""
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5),      # KAUF 1 -> T1
                   c(9, 105, 105.5, 104.0, 104.8),
                   c(10, 104.8, 105.0, 104.2, 104.6)]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                           tp_ladder=False, buy_ladder=False, release_stale_rest=True)
    assert not any("Struktur veraltet" in s.reason for s in sigs)
    assert pos.state == PosState.T1


def test_stoploss_setzt_alle_zaehler_zurueck():
    """Regression: nach einem STOPLOSS muss die Position komplett FLAT sein.

    Vor dem Fix vom 27.07.2026 blieben entry_ref/entry_pct und die Zaehler
    liq_exits/high_exits/liq_entries stehen. entry_pct wuchs dadurch ueber alle
    gestoppten Positionen hinweg, der Break-even des nachgezogenen Stops rechnete
    mit dem Preis einer laengst geschlossenen Position, und die Liquidations-/
    Hoch-Mechanismen schalteten sich nach wenigen Stops still ab.
    """
    ms = 4 * 3600 * 1000
    werte = ([100, 101, 100, 102, 101, 103, 102, 104, 103, 105]
             + [110, 115, 120, 125, 130, 132, 131, 133, 132, 134]
             + [128, 122, 118, 116, 114, 112, 108, 104, 99, 95]
             + [96, 97, 96, 98, 97, 99, 98, 100, 99, 101]
             + [106, 111, 116, 121, 126, 128, 127, 129, 128, 130]
             + [124, 118, 114, 112, 110, 108, 104, 100, 95, 92])
    cs = [Candle(1_600_000_000_000 + i * ms, v, v * 1.005, v * 0.995, v)
          for i, v in enumerate(werte)]
    fl = [FlowPoint(c.ts, 1000.0 + i * 10, 0.0, 1e9, 0.0) for i, c in enumerate(cs)]

    pos = Position()
    gestoppt = False
    for i in range(len(cs)):
        for s in evaluate(cs[:i + 1], fl[:i + 1], pos, bias_short=False, trail_stop=True):
            if s.type is SignalType.STOPLOSS:
                gestoppt = True
                assert pos.state is PosState.FLAT
                assert pos.direction == "NONE"
                assert pos.entry_ref is None, f"entry_ref nicht zurueckgesetzt: {pos.entry_ref}"
                assert pos.entry_pct == 0, f"entry_pct nicht zurueckgesetzt: {pos.entry_pct}"
                assert pos.liq_exits == 0 and pos.high_exits == 0 and pos.liq_entries == 0
                assert pos.tp_rungs == 0 and pos.dip_buys == 0 and pos.buy_rungs == 0
    assert gestoppt, "Testaufbau erzeugte keinen STOPLOSS"


# ------------------------------------------------- E13: Warnlicht + drei Begrenzungen

def test_kompass_muster5_ungesunder_abverkauf():
    """Der Kurs faellt, aber der Markt ist NICHT ausgeraeumt — Furkans Nicht-Kauf-Lage.

    Spiegelbild von Muster 4: Spot-CVD faellt mit (der Dip wird nicht gekauft), Open
    Interest haelt (die gehebelten Longs sind noch drin), Funding weiter positiv
    (Long-Ueberhang unveraendert), keine Long-Liquidations-Kaskade (die Zwangsverkaeufe
    stehen noch bevor).
    """
    n = 12
    candles = trend_candles(n, 100000, 97000)                      # -3 %
    flow = flow_series(
        spot=[100 - i * 4 for i in range(n)],                      # Spot-CVD faellt mit
        fut=[0] * n,
        oi=[1000 + i * 2 for i in range(n)],                       # OI steigt sogar
        funding=[0.0002] * n)                                      # Funding positiv
    assert classify_pattern(candles, flow) == Pattern.UNGESUNDER_ABVERKAUF


def test_muster5_weicht_der_kapitulation():
    """Ist der Markt ausgeraeumt, gewinnt Muster 4 — sonst wuerde das Warnlicht genau die
    guten Dips sperren, die Furkan kauft."""
    n = 12
    candles = trend_candles(n, 100000, 93000)
    flow = flow_series(
        spot=[100] * 9 + [95, 100, 106],                           # Spot dreht hoch
        fut=[0] * n,
        oi=[1000 - i * 8 for i in range(n)],                       # OI-Wipeout
        funding=[0.0002] * n)                                      # Funding trotzdem positiv
    assert classify_pattern(candles, flow) == Pattern.CAPITULATION_RESET


def e13_szenario(spot_faellt=True, oi_steigt=True, funding_positiv=True):
    """Gemeinsamer Aufbau fuer die E13-Tests.

    Klarer Impuls 97,6 -> 130,5 (Pivots mit n=2), danach ein 16 Kerzen langer, ruhiger
    Rueckgang. Die letzte Kerze faellt in das 0.5-Retracement (114,06) — dort feuert
    KAUF 1, der einzige Einstieg, der bisher gar keine Order-Flow-Pruefung hatte.
    Ueber die drei Schalter laesst sich der Order-Flow gesund/ungesund stellen.
    """
    werte = [100, 99, 98, 99, 104, 110, 116, 122, 128, 130] + [130 - i for i in range(1, 17)]
    cs = [Candle(1_600_000_000_000 + i * H4_MS, v, v * 1.004, v * 0.996, v)
          for i, v in enumerate(werte)]
    fl = [FlowPoint(c.ts,
                    5000.0 - i * 30 if spot_faellt else 5000.0 + i * 30,
                    0.0,
                    1e9 + i * 1e6 if oi_steigt else 1e9 - i * 2e7,
                    0.0002 if funding_positiv else -0.0002)
          for i, c in enumerate(cs)]
    return cs, fl


def e13_lauf(cs, fl, **kw):
    pos = Position()
    raus = []
    for i in range(len(cs)):
        raus += [s.type for s in evaluate(cs[:i + 1], fl[:i + 1], pos,
                                          bias_short=False, pivot_n=2, **kw)]
    return raus


def test_warnlicht_sperrt_long_im_ungesunden_abverkauf():
    """Muster 5 aktiv -> kein Kauf. Das ist Kaisers Frage in Testform."""
    cs, fl = e13_szenario()
    assert classify_pattern(cs, fl) == Pattern.UNGESUNDER_ABVERKAUF
    assert SignalType.KAUF_1 in e13_lauf(cs, fl), "ohne Warnlicht muesste gekauft werden"
    assert e13_lauf(cs, fl, block_unhealthy=True) == [], "Warnlicht hat nicht gesperrt"


def test_warnlicht_sperrt_NICHT_bei_bloss_neutralem_markt():
    """Gegenprobe: Das Warnlicht darf nur Muster 5 sperren, nicht jeden ruhigen Markt.

    Gleicher Chart, gleicher fallender Spot-CVD, gleiches positives Funding — nur das
    Open Interest faellt jetzt (die gehebelten Longs sind raus). Damit ist die Lage nicht
    mehr ungesund, und der Kauf muss durchgehen.
    """
    cs, fl = e13_szenario(oi_steigt=False)
    assert classify_pattern(cs, fl) != Pattern.UNGESUNDER_ABVERKAUF
    assert SignalType.KAUF_1 in e13_lauf(cs, fl, block_unhealthy=True)


def test_confirm_t1_prueft_den_05_einstieg():
    """Ohne confirm_t1 feuert KAUF 1 allein auf Preisberuehrung — mit muss der Flow passen."""
    cs, fl = e13_szenario()                       # Flow gegen Long (Spot faellt, Funding +)
    assert SignalType.KAUF_1 in e13_lauf(cs, fl)
    assert e13_lauf(cs, fl, confirm_t1=True) == []
    # Bei gesundem Flow (Spot steigt, Funding negativ) laesst confirm_t1 den Kauf durch
    cs2, fl2 = e13_szenario(spot_faellt=False, funding_positiv=False)
    assert SignalType.KAUF_1 in e13_lauf(cs2, fl2, confirm_t1=True)


def test_min_stop_pct_verwirft_zu_enge_stops():
    """Liegt die Invalidierung zu nah am Einstieg, kommt gar kein Signal."""
    cs, fl = e13_szenario(spot_faellt=False, funding_positiv=False)
    assert SignalType.KAUF_1 in e13_lauf(cs, fl)
    # Einstieg 114,06 gegen Invalidierung 97,6 = gut 14 % Abstand
    assert SignalType.KAUF_1 in e13_lauf(cs, fl, min_stop_pct=0.10)
    assert e13_lauf(cs, fl, min_stop_pct=0.20) == []


def test_cooldown_sperrt_wiedereinstieg_nach_stop():
    """Nach einem Stop wird cooldown_h Stunden lang gar nicht eingestiegen.

    Gleicher Aufbau wie die uebrigen E13-Tests, gesunder Flow (der Kauf waere also
    faellig). Nur der Merker last_stop_ts steht kurz vor der Einstiegskerze.
    """
    cs, fl = e13_szenario(spot_faellt=False, funding_positiv=False)
    einstieg_ts = cs[-1].ts

    def lauf(stop_vor_h, **kw):
        pos = Position()
        pos.last_stop_ts = einstieg_ts - int(stop_vor_h * 3600 * 1000)
        raus = []
        for i in range(len(cs)):
            raus += [s.type for s in evaluate(cs[:i + 1], fl[:i + 1], pos,
                                              bias_short=False, pivot_n=2, **kw)]
        return raus

    # ohne Sperre: Kauf faellig
    assert SignalType.KAUF_1 in lauf(4)
    # Stop lag 4 h zurueck, Sperre 48 h -> nichts
    assert lauf(4, cooldown_h=48) == []
    # Stop lag 72 h zurueck, Sperre 48 h abgelaufen -> Kauf wieder erlaubt
    assert SignalType.KAUF_1 in lauf(72, cooldown_h=48)


def test_last_stop_ts_ueberlebt_den_positions_reset():
    """Der Merker fuer die Sperrfrist darf beim Schliessen NICHT zurueckgesetzt werden —
    sonst wuesste die Engine nach dem Stop nicht mehr, dass gerade einer war."""
    pos = Position()
    pos.last_stop_ts = 4711
    pos.entry_pct = 90
    from strategy_core import _reset_position
    _reset_position(pos)
    assert pos.entry_pct == 0, "Positionsdaten muessen zurueckgesetzt werden"
    assert pos.last_stop_ts == 4711, "last_stop_ts darf den Reset nicht verlieren"


def test_e13_hebel_sind_default_aus():
    """Sicherung: ohne ausdrueckliches Einschalten aendert E13 nichts am Verhalten."""
    ms = H4_MS
    werte = ([100, 101, 100, 102, 101, 103, 102, 104, 103, 105]
             + [110, 115, 120, 125, 130, 132, 131, 133, 132, 134]
             + [128, 122, 118, 116, 114, 112, 110, 108, 106, 104])
    cs = [Candle(1_600_000_000_000 + i * ms, v, v * 1.004, v * 0.996, v)
          for i, v in enumerate(werte)]
    fl = [FlowPoint(c.ts, 1000.0 + i * 10, 0.0, 1e9, -0.0001) for i, c in enumerate(cs)]

    def lauf(**kw):
        pos = Position()
        raus = []
        for i in range(len(cs)):
            raus += [(s.ts, s.type) for s in
                     evaluate(cs[:i + 1], fl[:i + 1], pos, bias_short=False, **kw)]
        return raus

    assert lauf() == lauf(block_unhealthy=False, confirm_t1=False,
                          cooldown_h=0, min_stop_pct=0.0)


def test_muster2_nutzt_echtes_futures_cvd_wenn_vorhanden():
    """E16: Mit echtem Futures-CVD greift der scharfe Zweig, ohne der Ersatzweg.

    Aufbau: Preis steigt, Spot-CVD flach, OI steigt maessig (+1,5 %, also UNTER der
    3-%-Schwelle des Ersatzwegs), Funding zieht an. Der Ersatzweg kann den Pump hier
    nicht erkennen — er braucht OI >= 3 %. Mit echtem Futures-CVD reicht dagegen, dass
    die Bewegung erkennbar ueber Hebel laeuft... aber auch dieser Zweig verlangt OI.
    Der Test haelt deshalb fest, was tatsaechlich passiert, statt zu behaupten, die
    Daten seien ein Freifahrtschein: Beide Zweige verlangen OI-Anstieg, der Unterschied
    liegt im Spot/Futures-VERHAELTNIS.
    """
    n = 12
    candles = trend_candles(n, 100000, 103000)                 # +3 %
    stark_oi = [1000 + i * 5 for i in range(n)]                # +5,5 %
    funding = [0.00005 + i * 0.00002 for i in range(n)]

    # (a) Futures-CVD stark hoch, Spot flach -> echter Derivate-Pump
    mit_fut = flow_series(spot=[100] * n, fut=[100 + i * 10 for i in range(n)],
                          oi=stark_oi, funding=funding)
    assert classify_pattern(candles, mit_fut) == Pattern.DERIVATE_PUMP

    # (b) Gleiche Lage, aber Spot traegt die Bewegung MIT (Spot steigt so stark wie
    #     Futures) -> mit echten Daten ist das KEIN Derivate-Pump mehr.
    spot_traegt = flow_series(spot=[100 + i * 10 for i in range(n)],
                              fut=[100 + i * 10 for i in range(n)],
                              oi=stark_oi, funding=funding)
    assert classify_pattern(candles, spot_traegt) != Pattern.DERIVATE_PUMP

    # (c) Ohne Futures-Daten (fut=0) sieht die Engine denselben Fall (b) FALSCH:
    #     Der Ersatzweg prueft nur, ob Spot flach ist — die Information, dass Spot
    #     die Bewegung traegt, hat er zwar auch, aber die Schwelle ist eine andere
    #     (spot <= 0.01 statt spot <= fut/3). Genau dieser Unterschied ist der Grund,
    #     warum echte Futures-Daten ueberhaupt etwas aendern koennen.
    ohne_fut = flow_series(spot=[100 + i for i in range(n)],    # Spot steigt leicht
                           fut=[0] * n,
                           oi=stark_oi, funding=funding)
    ersatz = classify_pattern(candles, ohne_fut)
    mit = classify_pattern(candles, flow_series(
        spot=[100 + i for i in range(n)], fut=[100 + i * 10 for i in range(n)],
        oi=stark_oi, funding=funding))
    assert mit == Pattern.DERIVATE_PUMP
    assert ersatz != mit, "Ersatzweg und echter Zweig muessen sich unterscheiden koennen"


def test_flowpoint_long_pct_ist_optional():
    """Rueckwaertskompatibel: alte Aufrufe ohne long_pct muessen weiter funktionieren."""
    p = FlowPoint(1, 100.0, 0.0, 1e9, 0.0)
    assert p.long_pct == 0.0
    q = FlowPoint(1, 100.0, 0.0, 1e9, 0.0, 0.0, 0.0, 65.12)
    assert q.long_pct == 65.12
