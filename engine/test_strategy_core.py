"""Unit-Tests der Kern-Engine (E4a). Ausfuehren: python -m pytest test_strategy_core.py -q

Die Fib-Testvektoren stammen 1:1 aus dem Video (Frame 17:55 und 18:55) und aus dem
Gegencheck (docs/GEGENCHECK.md): reale Zahlen, keine Fantasiewerte.
"""

from strategy_core import (Candle, FlowPoint, LADDER_TRANCHE, Pattern, Pivot, Impulse,
                           PosState, Position, SignalType, classify_pattern,
                           daily_fib_zone, daily_trend, ema, evaluate, fib_zones,
                           find_pivots, in_liq_zone, last_significant_impulse,
                           gleiches_bein, liq_cascade, liq_levels, next_pivot_beyond,
                           trend_intakt,
                           lage_bericht, spot_nachfrage, MUSTER_KLARTEXT,
                           daily_fib_zone, trend_lage,
                           ampel, ampel_richtung, AMPEL_TRANCHE, kuerze_einstiege,
                           orderflow_detail, OF_FENSTER,
                           Signal, _ENTRY_TYPES,
                           resample_daily)

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
    # Mit Trendfilter: Preis unter der Tages-EMA -> Long wird blockiert.
    # trend_ema=10 statt des Defaults 50, weil die Serie nur 16 Tage umfasst. Seit E33
    # ist daily_trend streng: Fuer einen EMA50 ueber 16 Tage gibt es KEINE Zahl mehr,
    # sondern None - frueher wurde stillschweigend ein EMA16 geliefert und als EMA50
    # ausgegeben. Der Test misst jetzt einen EMA, den es wirklich gibt.
    pos2 = Position()
    sig_on = run_incremental(down, flow, pos2, pivot_n=2, bias_short=False,
                             trend_filter=True, trend_ema=10)
    assert not any(s.type == SignalType.KAUF_2 for s in sig_on)


def test_trend_filter_blockt_nichts_wenn_die_historie_nicht_reicht():
    """E33: Die Kehrseite der Strenge - verlangt jemand einen EMA200, hat aber nur 16
    Tage, wird NICHT blockiert. Unbekannt heisst nicht verboten.

    Vorher lieferte daily_trend in dieser Lage klaglos einen EMA16 und der Filter
    entschied auf dieser Grundlage. Der Backtest mit voller Historie rechnete
    gleichzeitig einen echten EMA200 - Live und Messung taten also verschiedene Dinge,
    ohne dass es auffiel.
    """
    down = _downtrend_long_series()
    flow = [FlowPoint(i, 100 + i, 100, 1000, -0.0001) for i in range(len(down))]
    pos_ohne = Position()
    ohne = run_incremental(down, flow, pos_ohne, pivot_n=2, bias_short=False)
    pos_mit = Position()
    mit = run_incremental(down, flow, pos_mit, pivot_n=2, bias_short=False,
                          trend_filter=True, trend_ema=200)
    assert [(s.ts, s.type) for s in ohne] == [(s.ts, s.type) for s in mit], (
        "ohne ausreichende Historie darf der Trendfilter nichts veraendern")
    assert daily_trend(down, 200, streng=True) is None
    assert daily_trend(down, 200, streng=False) is not None   # altes Verhalten abrufbar


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


def test_high_exit_hist_live_beschraenkt_die_pivotsuche_auf_die_live_historie():
    """A5: high_exit_hist="live" bildet das main.py-Fenster (main.LIMIT_HAUPT Kerzen)
    nach, statt wie "voll" ueber die ganze Historie zu suchen. Mit einer klein
    gehaltenen Fenstergroesse (monkeypatch von HIGH_EXIT_LIVE_KERZEN) faellt das
    Pivot-Hoch 110 aus dem Live-Fenster heraus -> der Teilverkauf am letzten Hoch
    bleibt aus, obwohl "voll" (Default) an denselben Kerzen feuert."""
    import strategy_core
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5),      # KAUF 1
                   c(9, 105.5, 109.6, 105.0, 109.4)]    # Anlauf an das Hoch 110
    alt = strategy_core.HIGH_EXIT_LIVE_KERZEN
    strategy_core.HIGH_EXIT_LIVE_KERZEN = 3    # Pivot-Hoch (idx 5) faellt aus candles[-3:]
    try:
        pos_voll = Position()
        sigs_voll = run_incremental(path, neg_funding_flow(), pos_voll, pivot_n=2,
                                    bias_short=False, tp_ladder=False, buy_ladder=False,
                                    high_exit="on", high_exit_hist="voll")
        pos_live = Position()
        sigs_live = run_incremental(path, neg_funding_flow(), pos_live, pivot_n=2,
                                    bias_short=False, tp_ladder=False, buy_ladder=False,
                                    high_exit="on", high_exit_hist="live")
    finally:
        strategy_core.HIGH_EXIT_LIVE_KERZEN = alt
    assert any("Teilgewinn am letzten Hoch" in s.reason for s in sigs_voll)
    assert not any("Teilgewinn am letzten Hoch" in s.reason for s in sigs_live)


def test_high_exit_hist_default_ist_voll_wie_bisher():
    """Default AUS bis zur Messung und Kaisers Go (Projektregel 1) - ohne den
    Parameter verhaelt sich evaluate() wie vor A5."""
    base = zigzag_candles()
    path = base + [c(8, 106, 106.5, 104.5, 105.5),
                   c(9, 105.5, 109.6, 105.0, 109.4)]
    pos_default = Position()
    sigs_default = run_incremental(path, neg_funding_flow(), pos_default, pivot_n=2,
                                   bias_short=False, tp_ladder=False, buy_ladder=False,
                                   high_exit="on")
    pos_voll = Position()
    sigs_voll = run_incremental(path, neg_funding_flow(), pos_voll, pivot_n=2,
                                bias_short=False, tp_ladder=False, buy_ladder=False,
                                high_exit="on", high_exit_hist="voll")
    assert [(s.ts, s.type, s.reason) for s in sigs_default] == \
           [(s.ts, s.type, s.reason) for s in sigs_voll]


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


# =========================== E18 (Durchsicht 27.08.2026) ===========================
# Zwei Mechanik-Fehler, beide schaltbar behoben, Default aus. Jeder Test prueft
# zusaetzlich, dass OHNE den Schalter alles bleibt wie bisher.

def _e18_pfad_nachkauf_und_teilgewinn():
    """Eine Kerze, die BEIDES ausloest: 0.786-Nachkauf (Tief) und Leiter-Teilgewinn (Hoch).

    Impuls 100->110 aus zigzag_candles: 0.5 = 105, 0.786 = 102.14, Invalidierung 100.
    Kerze 9 faellt auf 102.0 (Nachkauf-Zone) und laeuft auf 110.5 (Leiter-Ziel 0.8 = 110).
    Genau dieses Muster stand 16-mal im Signal-Datensatz der Live-Variante.
    """
    return zigzag_candles() + [
        c(8, 106, 106.5, 104.5, 105.5),      # KAUF 1 am 0.5-Level
        c(9, 105, 110.5, 102.0, 109.0),      # Tief in der Nachkaufzone, Hoch am Leiter-Ziel
    ]


def test_ohne_no_flip_kauft_und_verkauft_die_engine_in_derselben_kerze():
    """Dokumentiert den Ist-Zustand: ohne Schalter passiert genau das Gemeldete."""
    path = _e18_pfad_nachkauf_und_teilgewinn()
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                           buy_ladder=False, flush_entry="off")
    letzte = [s.type for s in sigs if s.ts == path[-1].ts]
    assert SignalType.NACHKAUF in letzte and SignalType.TEILVERKAUF_LADDER in letzte


def test_no_flip_sperrt_teilverkauf_nach_nachkauf_in_derselben_kerze():
    path = _e18_pfad_nachkauf_und_teilgewinn()
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                           buy_ladder=False, flush_entry="off", no_flip=True)
    letzte = [s.type for s in sigs if s.ts == path[-1].ts]
    assert letzte == [SignalType.NACHKAUF]           # der Teilgewinn faellt weg
    assert pos.tp_rungs == 0                          # und die Leiter ist nicht verbraucht


def test_no_flip_sperrt_nachkauf_nach_teilverkauf_in_derselben_kerze():
    """Gegenrichtung: kommt der Teilgewinn zuerst (Liquidations-Kaskade), faellt der
    Nachkauf weg — nicht umgekehrt."""
    path = _e18_pfad_nachkauf_und_teilgewinn()
    flow = _liq_flow(len(path), short_liq_last=5_000_000.0)
    pos = Position()
    sigs = run_incremental(path, flow, pos, pivot_n=2, bias_short=False, tp_ladder=False,
                           buy_ladder=False, flush_entry="off", liq_exit="spike",
                           no_flip=True)
    letzte = [s.type for s in sigs if s.ts == path[-1].ts]
    assert letzte == [SignalType.TEILVERKAUF_LADDER]
    assert pos.state == PosState.T1                   # kein Aufstieg auf FULL
    # Gegenprobe ohne Schalter: da kommen beide
    pos2 = Position()
    sigs2 = run_incremental(path, flow, pos2, pivot_n=2, bias_short=False, tp_ladder=False,
                            buy_ladder=False, flush_entry="off", liq_exit="spike")
    letzte2 = [s.type for s in sigs2 if s.ts == path[-1].ts]
    assert SignalType.NACHKAUF in letzte2 and SignalType.TEILVERKAUF_LADDER in letzte2


def test_no_flip_laesst_den_stop_immer_durch():
    """Ein vollstaendiger Ausstieg darf nie unterdrueckt werden."""
    path = zigzag_candles() + [
        c(8, 106, 106.5, 104.5, 105.5),      # KAUF 1
        c(9, 105, 105.5, 98.0, 99.0),        # Schluss unter Invalidierung 100
    ]
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                           buy_ladder=False, flush_entry="off", no_flip=True)
    assert sigs[-1].type == SignalType.STOPLOSS and pos.state == PosState.FLAT


def test_no_flip_kennt_nur_aufbau_und_teilverkauf():
    """Stop und Rest-Verkauf stehen bewusst in keiner der beiden Gruppen."""
    from strategy_core import _AUFBAU_TYPES, _TEILVERKAUF_TYPES
    tabu = {SignalType.STOPLOSS, SignalType.SHORT_STOPLOSS,
            SignalType.VERKAUF_REST, SignalType.SHORT_COVER_REST}
    assert not (tabu & (_AUFBAU_TYPES | _TEILVERKAUF_TYPES))
    assert not (_AUFBAU_TYPES & _TEILVERKAUF_TYPES)


def _e18_pfad_ziel_wandert():
    """Nach TEILVERKAUF 1 macht der Kurs ein neues Tief — das 1.618-Ziel wandert mit.

    Impuls 100->110. Nach KAUF 2 liegt das Retracement-Tief bei 103.6:
    Ziel 1.0 = 113.6 (Kerze 10 trifft es), Ziel 1.618 = 119.78.
    Kerze 11 faellt auf 101.0 (kein Stop, Schluss 112) -> Ziel 1.618 sinkt auf 117.18.
    Kerze 12 laeuft auf 118.0: unter dem urspruenglichen Ziel, ueber dem gewanderten.
    """
    return zigzag_candles() + [
        c(8, 106, 106.5, 104.5, 105.5),      # KAUF 1
        c(9, 105, 105.5, 103.6, 104.5),      # KAUF 2 im Golden Pocket
        c(10, 104, 114.0, 104.0, 113.5),     # TEILVERKAUF 1 (Ziel 1.0)
        c(11, 113, 113.5, 101.0, 112.0),     # neues Tief, aber kein Stop
        c(12, 112, 118.0, 111.0, 117.5),     # erreicht nur das GEWANDERTE Ziel
    ]


def test_ohne_freeze_targets_wandert_das_zweite_ziel_nach_unten():
    """Ist-Zustand: das 1.618-Ziel rutscht unter sein urspruengliches Niveau."""
    path = _e18_pfad_ziel_wandert()
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                           tp_ladder=False, buy_ladder=False, flush_entry="off")
    tv2 = [s for s in sigs if s.type == SignalType.TEILVERKAUF_2]
    assert len(tv2) == 1
    assert tv2[0].price < 119.0            # urspruenglich waeren es 119.78 gewesen


def test_freeze_targets_haelt_das_ziel_fest():
    path = _e18_pfad_ziel_wandert()
    pos = Position()
    sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                           tp_ladder=False, buy_ladder=False, flush_entry="off",
                           freeze_targets=True)
    assert not any(s.type == SignalType.TEILVERKAUF_2 for s in sigs)
    assert pos.ziel_extrem == 103.6        # Referenz des ersten Teilgewinns
    assert pos.retrace_extreme == 101.0    # das laufende Extrem bleibt unberuehrt
    assert pos.state == PosState.TP1


def test_freeze_targets_wird_beim_positionsende_zurueckgesetzt():
    path = _e18_pfad_ziel_wandert() + [c(13, 117, 117.5, 95.0, 96.0)]   # Stop
    pos = Position()
    run_incremental(path, neg_funding_flow(), pos, pivot_n=2, bias_short=False,
                    tp_ladder=False, buy_ladder=False, flush_entry="off",
                    freeze_targets=True)
    assert pos.state == PosState.FLAT and pos.ziel_extrem is None


# ====================== E19 (Furkan-Video 02.08.2026, Bein-Wahl) ======================
# Lage wie am 02.08.2026: ein grosses Aufwaerts-Bein, danach ein kleines Abwaerts-Bein.
# Die Engine nahm das kleine (Richtung SHORT, bei bias_short=false unhandelbar) und stand
# still; Furkan mass ueber das grosse und kaufte in dessen Golden Pocket nach.

def _e19_zwei_beine():
    """Aufwaerts 100->130 (30 %), danach abwaerts 130->122 (6 %). Pivots mit n=2."""
    rows = [(0, 100, 101, 99, 100), (1, 100, 101, 99, 100), (2, 100, 101, 98, 99),
            (3, 100, 104, 99, 103), (4, 104, 110, 103, 109), (5, 109, 118, 108, 117),
            (6, 117, 126, 116, 125), (7, 125, 130, 124, 129), (8, 129, 130, 127, 128),
            (9, 128, 129, 126, 127), (10, 127, 128, 124, 125), (11, 125, 126, 122, 123),
            (12, 123, 124, 122, 123), (13, 123, 125, 122, 124), (14, 124, 126, 123, 125),
            (15, 125, 127, 124, 126)]
    return [c(*r) for r in rows]


def test_ohne_schalter_gewinnt_das_juengste_kleine_bein():
    """Ist-Zustand, dokumentiert: das 6-%-Bein schlaegt das 30-%-Bein, weil es juenger ist."""
    cs = _e19_zwei_beine()
    imp = last_significant_impulse(cs, find_pivots(cs, n=2), k_atr=2.0)
    assert imp is not None and not imp.up            # Abwaerts-Bein
    assert imp.start.price == 130 and imp.end.price == 122


def test_min_bein_pct_ueberspringt_das_kleine_bein():
    cs = _e19_zwei_beine()
    imp = last_significant_impulse(cs, find_pivots(cs, n=2), k_atr=2.0, min_bein_pct=0.10)
    assert imp is not None and imp.up
    assert imp.start.price == 98 and imp.end.price == 130


def test_bein_wahl_groesstes_nimmt_die_groesste_spanne():
    cs = _e19_zwei_beine()
    imp = last_significant_impulse(cs, find_pivots(cs, n=2), k_atr=2.0,
                                   bein_wahl="groesstes")
    assert imp is not None and imp.up and imp.end.price == 130


def test_bein_richtung_ueberspringt_gegenlaeufiges_bein():
    cs = _e19_zwei_beine()
    auf = last_significant_impulse(cs, find_pivots(cs, n=2), k_atr=2.0, nur_auf=True)
    ab = last_significant_impulse(cs, find_pivots(cs, n=2), k_atr=2.0, nur_auf=False)
    assert auf is not None and auf.up and auf.end.price == 130
    assert ab is not None and not ab.up and ab.start.price == 130


def test_evaluate_bein_richtung_bias_macht_die_engine_wieder_handlungsfaehig():
    """Der Kern des 02.08.: nur Long erlaubt, juengstes Bein zeigt nach unten.

    Ohne den Schalter zeichnet die Engine das Short-Setup und tut nichts. Mit ihm nimmt
    sie das Aufwaerts-Bein — und dessen Zonen liegen dort, wo auch Furkan gekauft hat.
    """
    cs = _e19_zwei_beine()
    flow = neg_funding_flow()
    pos_ohne = Position()
    evaluate(cs, flow, pos_ohne, pivot_n=2, k_atr=2.0, bias_short=False)
    assert pos_ohne.state == PosState.FLAT           # steht still

    # Mit Richtungswahl: Zonen des Aufwaerts-Beins 98->130
    from strategy_core import fib_zones
    imp = last_significant_impulse(cs, find_pivots(cs, n=2), k_atr=2.0, nur_auf=True)
    z = fib_zones(imp)
    assert z.invalidation == 98 and 108 < z.gp_upper < 112   # GP bei rund 110
    # eine Kerze, die das Golden Pocket beruehrt -> Kauf statt Stillstand
    mitte_gp = (z.gp_lower + z.gp_upper) / 2
    pfad = cs + [c(16, 118, 119, mitte_gp, 118)]
    pos = Position()
    sigs = run_incremental(pfad, flow, pos, pivot_n=2, k_atr=2.0, bias_short=False,
                           bein_richtung="bias", flush_entry="off", buy_ladder=False)
    assert any(s.type == SignalType.KAUF_2 for s in sigs)
    assert pos.direction == "LONG"


def test_be_im_plus_zieht_den_stop_auf_den_einstand():
    """E19.3: Break-even, sobald die Position im Plus steht — nicht erst nach Teilgewinn."""
    from strategy_core import FibZones, Impulse, Pivot
    z = FibZones(Impulse(Pivot(0, 0, 100.0, "L"), Pivot(10, 10, 200.0, "H")),
                 150.0, 138.2, 135.0, 121.4, 100.0)
    cs = [c(i, 150, 155, 145, 150) for i in range(21)]   # Kurs 150 = im Plus (Einstand 140)
    cs.append(c(21, 150, 152, 138, 139))          # Schluss unter dem Einstand 140
    flow = neg_funding_flow()

    def _pos():
        # last_signal_ts vor der vorletzten Kerze, damit beide Kerzen ausgewertet werden
        return Position(direction="LONG", state=PosState.CORE, zones=z,
                        retrace_extreme=140.0, last_signal_ts=19,
                        entry_ref=140.0, entry_pct=75)
    # ohne den Schalter: Stop steht auf der Invalidierung (100) -> kein Stop
    p1 = _pos()
    s1 = evaluate(cs, flow, p1, trail_stop=True)
    assert not any(x.type == SignalType.STOPLOSS for x in s1)
    # mit dem Schalter: Break-even greift, weil die vorige Kerze im Plus schloss
    p2 = _pos()
    # erst eine Kerze im Plus (schaltet den Break-even scharf), dann der Rueckfall
    evaluate(cs[:-1], flow, p2, trail_stop=True, be_im_plus=True)
    assert p2.be_aktiv is True
    s2 = evaluate(cs, flow, p2, trail_stop=True, be_im_plus=True)
    stops = [x for x in s2 if x.type == SignalType.STOPLOSS]
    assert len(stops) == 1 and "Einstand" in stops[0].reason
    assert p2.state == PosState.FLAT


def test_be_im_plus_zieht_NICHT_wenn_die_position_im_minus_steht():
    """Sonst wuerde der Stop im selben Moment ausloesen, in dem er gesetzt wird."""
    from strategy_core import FibZones, Impulse, Pivot
    z = FibZones(Impulse(Pivot(0, 0, 100.0, "L"), Pivot(10, 10, 200.0, "H")),
                 150.0, 138.2, 135.0, 121.4, 100.0)
    cs = [c(i, 150, 155, 145, 150) for i in range(21)]
    cs.append(c(21, 135, 136, 128, 130))          # Kurs unter dem Einstand 140
    pos = Position(direction="LONG", state=PosState.CORE, zones=z, retrace_extreme=140.0,
                   last_signal_ts=20, entry_ref=140.0, entry_pct=75)
    sigs = evaluate(cs, neg_funding_flow(), pos, trail_stop=True, be_im_plus=True)
    assert not any(x.type == SignalType.STOPLOSS for x in sigs)
    assert pos.state == PosState.CORE


# ============ E20: das zweite Fib-Raster (Widerstand aus dem Gegen-Bein) ============
# Furkan fuehrt zwei Raster: eines in Handelsrichtung fuer die Kaufzonen, eines gegen die
# Richtung fuer die Widerstaende. Video 03.08.2026: "Die ersten wichtigen Bereiche in
# dieser Gegenbewegung wird natuerlich das Golden Pocket sein. 64.200 bis 64.300."

def _e20_pfad():
    """Aufwaerts 98->130, Ruecksetzer auf 120 (das Gegen-Bein), dann Erholung."""
    rows = [(0, 100, 101, 99, 100), (1, 100, 101, 99, 100), (2, 100, 101, 98, 99),
            (3, 99, 100, 98, 99), (4, 99, 104, 98, 103), (5, 103, 112, 102, 111),
            (6, 111, 121, 110, 120), (7, 120, 128, 119, 127), (8, 127, 130, 126, 129),
            (9, 129, 130, 127, 128), (10, 128, 129, 124, 125), (11, 125, 126, 121, 122),
            (12, 122, 123, 120, 121), (13, 121, 122, 120, 121), (14, 121, 124, 120, 123),
            (15, 123, 125, 122, 124)]
    return [c(*r) for r in rows]


def _e20_pfad_mit_neuem_hoch():
    """Wie _e20_pfad, aber danach steigt der Kurs auf ein neues bestaetigtes Hoch.

    Damit ist das JUENGSTE Bein aufwaerts (120->129) und das Gegen-Bein (130->120) liegt
    dahinter. Nur mit Richtungsfilter findet man das richtige — ohne ihn nimmt die Suche
    das juengere Aufwaerts-Bein und die Widerstandsmarken lägen unter dem Kurs.
    """
    return _e20_pfad() + [c(16, 124, 128, 123, 127), c(17, 127, 129, 126, 128),
                          c(18, 128, 129, 127, 128), c(19, 128, 129, 126, 127)]


def test_gegen_zonen_nimmt_das_bein_entgegen_der_richtung():
    from strategy_core import gegen_zonen
    cs = _e20_pfad_mit_neuem_hoch()
    piv = find_pivots(cs, n=2)
    # ohne Richtungsfilter waere das juengste Bein aufwaerts — genau das darf hier nicht
    # als Widerstandsquelle dienen
    juengstes = last_significant_impulse(cs, piv, k_atr=2.0)
    assert juengstes is not None and juengstes.up
    gz = gegen_zonen(cs, piv, long_side=True, k_atr=2.0)
    assert gz is not None and not gz.impulse.up          # fuer einen Long: das Abwaerts-Bein
    assert gz.impulse.start.price == 130 and gz.impulse.end.price == 120
    lo, hi = sorted((gz.gp_upper, gz.gp_lower))
    assert 126.0 < lo < hi < 126.6                       # Golden Pocket der Gegenbewegung
    assert gz.invalidation == 130                        # darueber ist der Widerstand weg
    # Das Bein IN Handelsrichtung ist ein anderes — beide existieren nebeneinander
    auf = last_significant_impulse(cs, piv, k_atr=2.0, nur_auf=True)
    assert auf is not None and auf.up and auf.end.price == 129
    assert (auf.start.price, auf.end.price) != (gz.impulse.start.price, gz.impulse.end.price)


def _e20_position(cs):
    from strategy_core import fib_zones
    imp = last_significant_impulse(cs, find_pivots(cs, n=2), k_atr=2.0, nur_auf=True)
    return Position(direction="LONG", state=PosState.CORE, zones=fib_zones(imp),
                    retrace_extreme=120.0, last_signal_ts=15, entry_ref=121.0, entry_pct=75)


def test_widerstand_exit_nimmt_teilgewinn_am_golden_pocket_der_gegenbewegung():
    cs = _e20_pfad() + [c(16, 124, 127.0, 123, 126.5)]   # laeuft in die Zone 126.2-126.5
    pos = _e20_position(cs)
    sigs = evaluate(cs, neg_funding_flow(), pos, pivot_n=2, k_atr=2.0, bias_short=False,
                    tp_ladder=False, buy_ladder=False, high_exit="off",
                    widerstand_exit="on")
    treffer = [s for s in sigs if "Widerstandszone" in s.reason]
    assert len(treffer) == 1
    assert treffer[0].type == SignalType.TEILVERKAUF_LADDER
    assert treffer[0].tranche_pct == LADDER_TRANCHE and pos.widerstand_exits == 1
    assert 126.0 < treffer[0].price < 126.6              # gemeldet wird die Zonen-Untergrenze
    # ohne den Schalter passiert an derselben Kerze nichts
    pos2 = _e20_position(cs)
    sigs2 = evaluate(cs, neg_funding_flow(), pos2, pivot_n=2, k_atr=2.0, bias_short=False,
                     tp_ladder=False, buy_ladder=False, high_exit="off")
    assert not any("Widerstandszone" in s.reason for s in sigs2)


def test_widerstand_exit_feuert_nicht_wenn_die_zone_schon_hinter_uns_liegt():
    """Eroeffnet der Kurs bereits ueber der Zone, ist sie kein Widerstand mehr."""
    cs = _e20_pfad() + [c(16, 128, 129.0, 127, 128.5)]
    pos = _e20_position(cs)
    sigs = evaluate(cs, neg_funding_flow(), pos, pivot_n=2, k_atr=2.0, bias_short=False,
                    tp_ladder=False, buy_ladder=False, high_exit="off",
                    widerstand_exit="on")
    assert not any("Widerstandszone" in s.reason for s in sigs)
    assert pos.widerstand_exits == 0


# ================== E21: Rest halten statt verkaufen (Kaiser 27.08.2026) ==================
# Furkan haelt EINE Position und steigt nie ganz aus. Unsere Engine beendet 12 von 21
# Positionen mit "Gegen-Muster am Ziel" — sie gibt den Rest zum Marktpreis ab und ist
# danach ganz draussen. Zwei Schalter, beide Default aus.

def _e21_pfad_bis_tp1():
    """Long-Zyklus bis TEILVERKAUF 1, danach eine Kerze mit Gegen-Muster."""
    base = zigzag_candles()
    return base + [
        c(8, 106, 106.5, 104.5, 105.5),    # KAUF 1 am 0.5-Level
        c(9, 105, 105.5, 103.6, 104.5),    # KAUF 2 im Golden Pocket
        c(10, 104, 114.0, 104.0, 113.5),   # Extension 1.0 -> TEILVERKAUF 1
    ]


def _gegenmuster_flow(n):
    """Flow, der am Ende SHORT_COVERING zeigt (Preis hoch, OI runter) — das Gegen-Muster,
    das den Rest-Verkauf ausloest."""
    return [FlowPoint(i, 100 + i, 0, 1000 - i * 30, -0.0001) for i in range(n)]


def test_ohne_rest_halten_wird_der_rest_beim_gegenmuster_verkauft():
    """Ist-Zustand: nach dem Teilgewinn beendet ein Gegen-Muster die ganze Position."""
    pfad = _e21_pfad_bis_tp1() + [c(11, 113, 118.0, 112.0, 117.0)]
    pos = Position()
    sigs = run_incremental(pfad, _gegenmuster_flow(len(pfad)), pos, pivot_n=2,
                           bias_short=False, tp_ladder=False, buy_ladder=False,
                           flush_entry="off", high_exit="off")
    assert any(s.type == SignalType.VERKAUF_REST for s in sigs)
    assert pos.state == PosState.FLAT          # ganz draussen


def test_rest_halten_laesst_die_position_weiterlaufen():
    pfad = _e21_pfad_bis_tp1() + [c(11, 113, 118.0, 112.0, 117.0)]
    pos = Position()
    sigs = run_incremental(pfad, _gegenmuster_flow(len(pfad)), pos, pivot_n=2,
                           bias_short=False, tp_ladder=False, buy_ladder=False,
                           flush_entry="off", high_exit="off", rest_halten=True)
    assert not any(s.type == SignalType.VERKAUF_REST for s in sigs)
    assert pos.state == PosState.TP1           # Rest laeuft weiter
    assert pos.direction == "LONG"


def test_rest_halten_haelt_den_stop_trotzdem_scharf():
    """Der Rest laeuft bis zum Stop — nicht ewig."""
    pfad = _e21_pfad_bis_tp1() + [c(11, 113, 114.0, 99.0, 99.5)]   # Schluss unter 100
    pos = Position()
    sigs = run_incremental(pfad, _gegenmuster_flow(len(pfad)), pos, pivot_n=2,
                           bias_short=False, tp_ladder=False, buy_ladder=False,
                           flush_entry="off", high_exit="off", rest_halten=True)
    assert any(s.type == SignalType.STOPLOSS for s in sigs)
    assert pos.state == PosState.FLAT


def test_neustart_mit_rest_erlaubt_einen_einstieg_waehrend_der_rest_laeuft():
    """Ohne den Schalter blockiert der liegende Rest jeden neuen Einstieg (Befund E9.9)."""
    from strategy_core import FibZones, Impulse, Pivot
    cs = zigzag_candles() + [c(8, 106, 106.5, 104.5, 105.5)]
    # Position kuenstlich in TP1 mit den Zonen des alten Impulses
    z = FibZones(Impulse(Pivot(2, 2, 100.0, "L"), Pivot(5, 5, 110.0, "H")),
                 level_05=105.0, gp_upper=103.82, gp_lower=103.5,
                 level_0786=102.14, invalidation=100.0)

    def _pos():
        return Position(direction="LONG", state=PosState.TP1, zones=z,
                        retrace_extreme=104.5, last_signal_ts=7,
                        entry_ref=105.0, entry_pct=75, tp_rungs=2, high_exits=2)
    flow = neg_funding_flow()
    ohne = _pos()
    evaluate(cs, flow, ohne, pivot_n=2, bias_short=False, flush_entry="off",
             tp_ladder=False, buy_ladder=False)
    assert ohne.state == PosState.TP1 and ohne.entry_pct == 75      # kein Einstieg

    mit = _pos()
    sigs = evaluate(cs, flow, mit, pivot_n=2, bias_short=False, flush_entry="off",
                    tp_ladder=False, buy_ladder=False, neustart_mit_rest=True)
    assert any(s.type in (SignalType.KAUF_1, SignalType.KAUF_2) for s in sigs)
    assert mit.state in (PosState.T1, PosState.CORE)
    # Exakt 75 (alter Bestand) + 25 (neue Tranche). Der genaue Wert ist wichtig: Bei
    # ">" wuerde nicht auffallen, wenn der alte Bestand beim Neustart verlorenginge.
    assert mit.entry_pct == 100
    assert mit.entry_ref is not None and 100 < mit.entry_ref < 110
    assert mit.tp_rungs == 0 and mit.high_exits == 0   # neuer Zyklus faengt bei null an


# ---------------------------------------- E23: die 1D-Ebene als zweiter Zonensatz

def _zwei_ebenen_serie():
    """Die beiden Ebenen zeichnen VERSCHIEDENE Beine — der Fall, um den es geht.

    Grosses Bein 100->140 liegt zurueck; danach ein Ruecklauf auf 120 und eine kurze
    Erholung auf 128. Auf 4h ist das Pivot-Tief bei 120 nach 5 Kerzen (20 h) bestaetigt,
    das juengste 4h-Bein ist also 120->128. Auf 1D braucht dasselbe Tief 5 TAGE — die
    1D-Ebene fuehrt deshalb noch das grosse Bein 100->140. Genau diese Traegheit ist der
    Grund, warum Furkan beide Ebenen im Chart hat (STRATEGIE.md 4.1 Punkt 4).

    Die letzte Kerze faellt mit einem Docht auf 119: das trifft das 1D-0.5-Level (120,04),
    liegt aber unter allen 4h-Zonen (0.5=124,01 / GP 123,01-122,73) und schliesst unter
    deren Invalidierung — auf der 4h-Ebene passiert also nichts.
    """
    tage = ([100] * 6 + [112, 126, 140] + [140] * 6 + [134, 128, 122, 120] + [124, 128] + [123])
    cs, ts = [], 0
    for i, p in enumerate(tage):
        vor = tage[i - 1] if i else p
        for k in range(6):                                   # 6 4h-Kerzen je Tag
            x = vor + (p - vor) * (k + 1) / 6
            cs.append(c(ts, x, x * 1.002, x * 0.998, x))
            ts += H4_MS
    l = cs[-1]
    cs[-1] = c(l.ts, l.open, l.high, 119.0, 119.5)
    flow = [FlowPoint(x.ts, 100 + i, 100, 1000, -0.0001) for i, x in enumerate(cs)]
    return cs, flow


def test_zonen_1d_die_ebenen_zeichnen_wirklich_verschiedene_beine():
    """Bestandssicherung fuer das Szenario selbst.

    Ohne diese Pruefung koennte der Test unten gruen bleiben, obwohl beide Ebenen
    dasselbe Bein sehen — dann waere gar nicht gemessen, was er zu messen vorgibt.
    """
    cs, _ = _zwei_ebenen_serie()
    imp4 = last_significant_impulse(cs, find_pivots(cs, n=5), k_atr=2.0)
    z1d = daily_fib_zone(cs, pivot_n=5, k_atr=2.0)
    assert imp4 is not None and z1d is not None
    assert not gleiches_bein(imp4, z1d.impulse), "Szenario taugt nicht: beide Ebenen gleich"
    assert abs(imp4.start.price - 120) < 1 and abs(imp4.end.price - 128) < 1
    assert abs(z1d.impulse.start.price - 100) < 1 and abs(z1d.impulse.end.price - 140) < 1


def test_zonen_1d_liefert_einstieg_den_die_4h_ebene_verpasst():
    cs, flow = _zwei_ebenen_serie()

    pos_aus = Position()
    assert evaluate(cs, flow, pos_aus, bias_short=False, zonen_1d=False) == [], \
        "ohne Schalter darf hier nichts passieren (Verhalten wie bisher)"
    assert pos_aus.state == PosState.FLAT

    pos_an = Position()
    sig = evaluate(cs, flow, pos_an, bias_short=False, zonen_1d=True)
    assert len(sig) == 1 and sig[0].type == SignalType.KAUF_1
    assert abs(sig[0].price - 120.04) < 0.05, f"0.5-Level der 1D-Ebene erwartet, kam {sig[0].price}"
    assert "[1D]" in sig[0].reason, "Signal muss als 1D-Einstieg erkennbar sein"
    # Die Position uebernimmt die 1D-Zonen — sonst saesse der Stop auf der falschen Ebene
    assert pos_an.zones is not None and abs(pos_an.zones.invalidation - 99.8) < 0.5
    assert abs(sig[0].stop_ref - 99.8) < 0.5


def test_zonen_1d_gilt_nicht_als_umgehung_der_sicherungen():
    """Gegenprobe: der 1D-Einstieg durchlaeuft dieselben Pruefungen wie ein 4h-Einstieg.

    Der Stop-Abstand betraegt hier (120,04-99,80)/120,04 = 16,9 %. Mit einem
    Mindestabstand von 20 % muss der Einstieg unterbleiben — sonst waere die neue Ebene
    ein Schleichweg an min_stop_pct vorbei.
    """
    cs, flow = _zwei_ebenen_serie()
    pos = Position()
    assert evaluate(cs, flow, pos, bias_short=False, zonen_1d=True, min_stop_pct=0.20) == []
    assert pos.state == PosState.FLAT
    # Gegenprobe zur Gegenprobe: knapp unter dem echten Abstand greift er wieder
    pos2 = Position()
    assert evaluate(cs, flow, pos2, bias_short=False, zonen_1d=True, min_stop_pct=0.15) != []


def test_zonen_1d_kein_doppelsignal_wenn_beide_ebenen_dasselbe_bein_sehen():
    """Zeichnen 4h und 1D denselben Impuls, darf der Schalter nichts aendern."""
    tage = [100] * 6 + [112, 126, 140] + [140] * 6 + [136, 130, 124, 119]
    cs, ts = [], 0
    for i, p in enumerate(tage):
        vor = tage[i - 1] if i else p
        for k in range(6):
            x = vor + (p - vor) * (k + 1) / 6
            cs.append(c(ts, x, x * 1.002, x * 0.998, x))
            ts += H4_MS
    l = cs[-1]
    cs[-1] = c(l.ts, l.open, l.high, 119.0, 119.5)
    flow = [FlowPoint(x.ts, 100 + i, 100, 1000, -0.0001) for i, x in enumerate(cs)]

    imp4 = last_significant_impulse(cs, find_pivots(cs, n=5), k_atr=2.0)
    z1d = daily_fib_zone(cs, pivot_n=5, k_atr=2.0)
    assert gleiches_bein(imp4, z1d.impulse), "Szenario taugt nicht: die Ebenen sind verschieden"

    ohne = evaluate(cs, flow, Position(), bias_short=False, zonen_1d=False)
    mit = evaluate(cs, flow, Position(), bias_short=False, zonen_1d=True)
    assert len(ohne) == 1 and len(mit) == 1, f"Doppelsignal: {len(ohne)} vs {len(mit)}"
    assert [s.reason for s in mit] == [s.reason for s in ohne]
    assert "[1D]" not in mit[0].reason


def test_gleiches_bein_vergleicht_preise_nicht_zeitstempel():
    a = Impulse(Pivot(0, 0, 100.0, "L"), Pivot(10, 10, 140.0, "H"))
    b = Impulse(Pivot(99, 99, 100.0, "L"), Pivot(120, 120, 140.0, "H"))   # andere ts
    c_ = Impulse(Pivot(0, 0, 100.0, "L"), Pivot(10, 10, 141.0, "H"))
    assert gleiches_bein(a, b)
    assert not gleiches_bein(a, c_)
    assert not gleiches_bein(a, None) and not gleiches_bein(None, None)


# ------------------------- E30: Zonen einer laufenden Position nachziehen

def test_trend_intakt_erkennt_fortsetzung_und_bruch():
    """Reiner Regel-Test der Bedingung, ohne Engine drumherum."""
    alt_auf = Impulse(Pivot(0, 0, 100.0, "L"), Pivot(1, 1, 110.0, "H"))
    # hoeheres Tief UND hoeheres Hoch -> intakt
    assert trend_intakt(alt_auf, Impulse(Pivot(2, 2, 104.5, "L"), Pivot(3, 3, 113.0, "H")))
    # hoeheres Tief, aber TIEFERES Hoch -> gebrochen
    assert not trend_intakt(alt_auf, Impulse(Pivot(2, 2, 104.5, "L"), Pivot(3, 3, 108.0, "H")))
    # tieferes Tief, hoeheres Hoch -> gebrochen
    assert not trend_intakt(alt_auf, Impulse(Pivot(2, 2, 98.0, "L"), Pivot(3, 3, 113.0, "H")))
    # Richtungswechsel zaehlt nie als intakt
    assert not trend_intakt(alt_auf, Impulse(Pivot(2, 2, 113.0, "H"), Pivot(3, 3, 104.5, "L")))
    # Short spiegelbildlich: tieferes Hoch UND tieferes Tief
    alt_ab = Impulse(Pivot(0, 0, 110.0, "H"), Pivot(1, 1, 100.0, "L"))
    assert trend_intakt(alt_ab, Impulse(Pivot(2, 2, 108.0, "H"), Pivot(3, 3, 96.0, "L")))
    assert not trend_intakt(alt_ab, Impulse(Pivot(2, 2, 108.0, "H"), Pivot(3, 3, 102.0, "L")))
    assert not trend_intakt(None, alt_auf) and not trend_intakt(alt_auf, None)


def _intakter_trend_pfad():
    """Impuls 100->110, Einstieg am 0.5 (105). Danach bildet sich ein neues Bein
    104,5 -> 113: hoeheres Tief UND hoeheres Hoch. Das Hoch bleibt unter dem
    Extension-Ziel 114,5, damit kein Teilverkauf den Zustand verwischt."""
    return zigzag_candles() + [
        c(8, 106, 106.5, 104.5, 105.5),      # KAUF 1 am 0.5, Tief 104.5
        c(9, 105, 107, 104.6, 106.5),
        c(10, 107, 110, 106.5, 109.5),       # Pivot-Tief 104.5 bestaetigt
        c(11, 109.5, 113, 109, 112.5),       # neues Hoch 113
        c(12, 112, 112.5, 111, 111.5),
        c(13, 111, 111.5, 110, 110.5),       # Pivot-Hoch 113 bestaetigt
    ]


def _gebrochener_trend_pfad():
    """Gleicher Einstieg, aber das neue Bein 104,5 -> 108 bleibt UNTER dem alten
    Hoch 110: hoeheres Tief, aber tieferes Hoch = kein intakter Trend."""
    return zigzag_candles() + [
        c(8, 106, 106.5, 104.5, 105.5),      # KAUF 1 am 0.5, Tief 104.5
        c(9, 105, 107, 104.6, 106.5),
        c(10, 107, 108, 106.5, 107.5),       # Hoch nur 108
        c(11, 107, 107.5, 105.5, 106),
        c(12, 106, 106.5, 105, 105.5),       # Pivot-Hoch 108 bestaetigt
    ]


def _lauf(path, **kw):
    pos = Position()
    kw.setdefault("pivot_n", 2)
    kw.setdefault("bias_short", False)
    kw.setdefault("tp_ladder", False)
    kw.setdefault("buy_ladder", False)
    sigs = run_incremental(path, neg_funding_flow(), pos, **kw)
    return pos, sigs


def test_zonen_nachziehen_bei_intaktem_trend():
    """Der Schalter an: die Zonen der laufenden Position wandern auf das neue Bein."""
    pos, _ = _lauf(_intakter_trend_pfad(), zonen_nachziehen=True)
    assert pos.state != PosState.FLAT, "Position muss fuer den Test offen bleiben"
    assert pos.zones is not None
    assert pos.zones.impulse.start.price == 104.5      # neues Bein
    assert pos.zones.impulse.end.price == 113
    assert pos.zones.invalidation == 104.5             # Stop-Bezug ist mitgewandert
    # ... und er ist dabei nur GESTIEGEN, nie lockerer geworden
    assert pos.zones.invalidation > 100


def test_ohne_schalter_bleiben_die_zonen_eingefroren():
    """Default aus = bisheriges Verhalten, unveraendert."""
    pos, _ = _lauf(_intakter_trend_pfad(), zonen_nachziehen=False)
    assert pos.state != PosState.FLAT
    assert pos.zones.impulse.start.price == 100        # altes Bein
    assert pos.zones.invalidation == 100


def test_zonen_nachziehen_nicht_bei_gebrochener_struktur():
    """Gegenprobe: haelt das neue Bein den Trend NICHT, bleiben die alten Zonen stehen —
    sonst wuerde die Engine einer kaputten Struktur nachkaufen."""
    pfad = _gebrochener_trend_pfad()
    pos_an, _ = _lauf(pfad, zonen_nachziehen=True)
    pos_aus, _ = _lauf(pfad, zonen_nachziehen=False)
    assert pos_an.state != PosState.FLAT
    # Mit und ohne Schalter identisch: der Schalter darf hier NICHTS tun
    assert pos_an.zones.invalidation == pos_aus.zones.invalidation == 100
    assert pos_an.zones.impulse.end.price == pos_aus.zones.impulse.end.price == 110


def test_zonen_nachziehen_erzeugt_kein_gegengeschaeft():
    """Karussell-Gegenprobe (Lehre aus E28): das Nachziehen darf nicht dazu fuehren,
    dass in derselben Kerze gekauft UND verkauft wird."""
    aufbau = {SignalType.KAUF_1, SignalType.KAUF_2, SignalType.NACHKAUF}
    abbau = {SignalType.TEILVERKAUF_LADDER, SignalType.TEILVERKAUF_1,
             SignalType.TEILVERKAUF_2}
    for pfad in (_intakter_trend_pfad(), _gebrochener_trend_pfad()):
        _, sigs = _lauf(pfad, zonen_nachziehen=True, buy_ladder=True, tp_ladder=True)
        proc = {}
        for s in sigs:
            proc.setdefault(s.ts, set()).add(s.type)
        for ts, typen in proc.items():
            assert not (typen & aufbau and typen & abbau), \
                f"Kauf und Verkauf in derselben Kerze bei ts={ts}: {typen}"


# --------- E30.2b: no_flip-Luecke beim Neustart mit Rest (05.09.2026)

def _teilverkauf_und_neustart_in_einer_kerze():
    """Kerze 9 loest gleichzeitig Teilgewinne (Leiter + Extension 1.0) UND — ueber
    neustart_mit_rest — einen neuen KAUF 1 aus. Genau das Muster, das im Backtest
    vom 05.09.2026 als Gegengeschaeft auftauchte."""
    return zigzag_candles() + [
        c(8, 106, 106.5, 104.5, 105.5),
        c(9, 105, 116, 104.6, 115),
        c(10, 115, 120, 113, 119),
        c(11, 119, 121, 112, 113),
        c(12, 113, 118, 111, 117),
        c(13, 117, 119, 110, 111),
        c(14, 111, 116, 109, 115),
        c(15, 115, 118, 108, 109),
    ]


def test_no_flip_deckt_auch_den_neustart_mit_rest_ab():
    """no_flip schuetzte bisher nur Nachkaeufe (_darf_aufstocken), nicht den
    Neu-Einstieg aus neustart_mit_rest — der laeuft NACH dem Positions-Management
    im selben evaluate()-Aufruf und konnte deshalb in dieselbe Kerze fallen wie ein
    Teilverkauf. Betrifft die Live-Einstellung, unabhaengig von zonen_nachziehen."""
    aufbau = {SignalType.KAUF_1, SignalType.KAUF_2, SignalType.NACHKAUF}
    abbau = {SignalType.TEILVERKAUF_LADDER, SignalType.TEILVERKAUF_1,
             SignalType.TEILVERKAUF_2}
    pfad = _teilverkauf_und_neustart_in_einer_kerze()
    for nachziehen in (False, True):
        pos = Position()
        sigs = run_incremental(pfad, neg_funding_flow(), pos,
                               pivot_n=2, bias_short=False, buy_ladder=True,
                               tp_ladder=True, high_exit="on", trail_stop=True,
                               min_stop_pct=0.02, flush_entry="core",
                               min_bein_pct=0.05, no_flip=True,
                               neustart_mit_rest=True, liq_entry="boost",
                               zonen_nachziehen=nachziehen)
        proc = {}
        for x in sigs:
            proc.setdefault(x.ts, set()).add(x.type)
        for ts, typen in proc.items():
            assert not (typen & aufbau and typen & abbau), \
                f"Gegengeschaeft bei ts={ts} (zonen_nachziehen={nachziehen}): {typen}"


# ------------------- E32: Lage-Bericht (Kaiser 12.09.2026, Video 10.09.)

def _flow_cvd(werte):
    """FlowPoints mit vorgegebenem kumuliertem Spot-CVD."""
    return [FlowPoint(i, v, 100.0, 1000.0, 0.0001) for i, v in enumerate(werte)]


def test_spot_nachfrage_vier_zustaende():
    """Die vier Faelle, die Kaiser lesen will. spot_cvd ist KUMULIERT - verglichen wird
    die Netto-Nachfrage der letzten 3 Kerzen mit der der 3 davor."""
    # davor +, jetzt +  -> stabil
    assert spot_nachfrage(_flow_cvd([0, 10, 20, 30, 40, 50, 60]))["stand"] == "stabil"
    # davor -, jetzt +  -> zurueckgekehrt
    assert spot_nachfrage(_flow_cvd([100, 90, 80, 70, 80, 90, 100]))["stand"] == "zurueckgekehrt"
    # davor +, jetzt -  -> nachgelassen
    assert spot_nachfrage(_flow_cvd([0, 10, 20, 30, 25, 20, 15]))["stand"] == "nachgelassen"
    # davor -, jetzt -  -> schwach
    assert spot_nachfrage(_flow_cvd([100, 90, 80, 70, 60, 50, 40]))["stand"] == "schwach"


def test_spot_nachfrage_ohne_genug_daten_ist_none():
    """Lieber nichts sagen als etwas erfinden: unter 2*fenster+1 Punkten -> None."""
    assert spot_nachfrage(_flow_cvd([0, 10, 20])) is None
    assert spot_nachfrage([]) is None
    assert spot_nachfrage(_flow_cvd([0] * 7)) is not None      # genau genug


def test_lage_struktur_intakt_unveraendert_gebrochen():
    """Die Struktur-Aussage kommt aus dem PREIS, nicht aus dem Order-Flow."""
    alt = Impulse(Pivot(0, 0, 75546.0, "L"), Pivot(5, 5, 81273.0, "H"))
    hoeher = Impulse(Pivot(8, 8, 76264.0, "L"), Pivot(12, 12, 82300.0, "H"))
    tiefer = Impulse(Pivot(8, 8, 76264.0, "L"), Pivot(12, 12, 80000.0, "H"))
    f = _flow_cvd([0, 10, 20, 30, 40, 50, 60])

    l = lage_bericht([], f, imp=hoeher, pos_impulse=alt)
    assert l["struktur"] == "intakt" and "76.264" in l["struktur_text"]

    l = lage_bericht([], f, imp=tiefer, pos_impulse=alt)
    assert l["struktur"] == "gebrochen"

    l = lage_bericht([], f, imp=alt, pos_impulse=alt)
    assert l["struktur"] == "unveraendert"

    # ohne Vergleichsbein (kein offener Trade)
    l = lage_bericht([], f, imp=hoeher)
    assert l["struktur"] == "neu"


def test_lage_muster_wird_uebersetzt():
    """Pattern.UNGESUNDER_ABVERKAUF sagt einem Menschen nichts."""
    f = _flow_cvd([0, 10, 20, 30, 40, 50, 60])
    l = lage_bericht([], f, pattern=Pattern.UNGESUNDER_ABVERKAUF)
    assert l["muster"] == "UNGESUNDER_ABVERKAUF"
    # E38 (21.09.2026): beschreibt, WAS passiert - keine Wertung mehr ("ungesund").
    assert "Short-Wetten" in l["muster_text"] and "Liquidationswelle" in l["muster_text"]
    assert "ungesund" not in l["muster_text"].lower()
    assert "Gegenbewegung" in l["muster_hinweis"] and "nicht immer" in l["muster_hinweis"]
    # NEUTRAL ist keine Aussage und wird weggelassen
    assert "muster" not in lage_bericht([], f, pattern=Pattern.NEUTRAL)
    # jedes Muster hat einen Klartext
    for m in Pattern:
        assert m.name in MUSTER_KLARTEXT, f"Klartext fehlt fuer {m.name}"


def test_lage_aendert_keine_signale():
    """Kernzusage von E32: reine Information. Derselbe Kurslauf muss mit und ohne
    Lage-Berechnung exakt dieselben Signale liefern - die Funktion darf nichts
    veraendern, was die Engine liest."""
    path = _intakter_trend_pfad()
    pos1 = Position()
    sigs1 = run_incremental(path, neg_funding_flow(), pos1, pivot_n=2, bias_short=False,
                            tp_ladder=False, buy_ladder=False, zonen_nachziehen=True)
    pos2 = Position()
    sigs2 = run_incremental(path, neg_funding_flow(), pos2, pivot_n=2, bias_short=False,
                            tp_ladder=False, buy_ladder=False, zonen_nachziehen=True)
    for i in range(1, len(path) + 1):
        lage_bericht(path[:i], neg_funding_flow(),
                     imp=None, pattern=Pattern.DERIVATE_PUMP)
    assert [(s.ts, s.type, s.price) for s in sigs1] == \
           [(s.ts, s.type, s.price) for s in sigs2]
    assert pos1.state == pos2.state and pos1.entry_pct == pos2.entry_pct


# ---------- E32.3: eigene Swing-Weite fuer die 1D-Ebene (13.09.2026)

def _tageskerzen_gross_und_klein():
    """Ein Verlauf mit einem GROSSEN uebergeordneten Bein (90 -> 151) und einem kurzen,
    JUNGEN Ruecksetzer am Ende. Eine feine Swing-Weite bestaetigt den Ruecksetzer als
    Pivot und nimmt anschliessend das kleine, junge Bein; eine grobe Weite tut das
    nicht und behaelt das uebergeordnete. Genau dieser Unterschied trennt Furkans
    Ebene von der, die E23 tatsaechlich abgetastet hat.

    Gebaut als 4h-Kerzen (6 je Tag), weil daily_fib_zone selbst auf 1D resampelt.
    Die Werte sind nicht geraten, sondern durchprobiert (13.09.2026).
    """
    segmente = [(8, 100, 90), (22, 90, 150), (4, 150, 138), (5, 138, 152)]
    tage = []
    for n, anf, ende in segmente:
        tage += [anf + (ende - anf) * i / max(n - 1, 1) for i in range(n)]
    kerzen, ts = [], 0
    for preis in tage:
        for _ in range(6):
            kerzen.append(c(ts, preis, preis + 1.0, preis - 1.0, preis))
            ts += 4 * 3600 * 1000
    return kerzen


def test_pivot_n_1d_waehlt_die_groebere_ebene():
    """Der Kern von E32.3: Auf DERSELBEN Kurshistorie liefert eine groebere Swing-Weite
    ein anderes, deutlich groesseres Bein. E23 rief die 1D-Ebene mit pivot_n auf - der
    Weite fuer 4h-Kerzen - und bekam deshalb wieder Feinstruktur statt der
    uebergeordneten Ebene."""
    k = _tageskerzen_gross_und_klein()
    fein = daily_fib_zone(k, pivot_n=2, k_atr=1.0, min_bein_pct=0.02, pivot_n_1d=2)
    grob = daily_fib_zone(k, pivot_n=2, k_atr=1.0, min_bein_pct=0.02, pivot_n_1d=8)
    assert fein is not None and grob is not None, "beide Ebenen muessen ein Bein finden"
    spanne_fein = abs(fein.impulse.end.price - fein.impulse.start.price)
    spanne_grob = abs(grob.impulse.end.price - grob.impulse.start.price)
    assert spanne_grob > 3 * spanne_fein, (
        f"die groebere Weite muss das deutlich groessere Bein liefern: "
        f"grob {spanne_grob:.0f} gegen fein {spanne_fein:.0f}")
    # und die Zonen liegen dadurch woanders - das ist der ganze Punkt
    assert abs(grob.gp_upper - fein.gp_upper) > 0.05 * grob.gp_upper


def test_pivot_n_1d_null_ist_das_alte_verhalten():
    """Rueckwaertskompatibel: 0 heisst 'wie pivot_n'. Ohne diese Zusage wuerde der
    Schalter stillschweigend alle bisherigen Messungen entwerten."""
    k = _tageskerzen_gross_und_klein()
    for n in (2, 3, 5):
        a = daily_fib_zone(k, pivot_n=n, k_atr=1.0, min_bein_pct=0.02)
        b = daily_fib_zone(k, pivot_n=n, k_atr=1.0, min_bein_pct=0.02, pivot_n_1d=0)
        cc = daily_fib_zone(k, pivot_n=n, k_atr=1.0, min_bein_pct=0.02, pivot_n_1d=n)
        assert (a is None) == (b is None) == (cc is None)
        if a is not None:
            assert a.impulse.start.price == b.impulse.start.price == cc.impulse.start.price
            assert a.impulse.end.price == b.impulse.end.price == cc.impulse.end.price


def test_pivot_n_1d_wirkt_nur_mit_zonen_1d():
    """Der Parameter darf nichts tun, solange die 1D-Ebene ausgeschaltet ist - sonst
    haette die Live-Einstellung sich unbemerkt geaendert."""
    path = _intakter_trend_pfad()
    erg = []
    for n1d in (0, 8, 12):
        pos = Position()
        sigs = run_incremental(path, neg_funding_flow(), pos, pivot_n=2,
                               bias_short=False, tp_ladder=False, buy_ladder=False,
                               zonen_1d=False, pivot_n_1d=n1d)
        erg.append([(x.ts, x.type, round(x.price, 4)) for x in sigs])
    assert erg[0] == erg[1] == erg[2], "ohne zonen_1d darf pivot_n_1d nichts veraendern"


def test_pivot_n_1d_kommt_durch_evaluate_an():
    """Gegenprobe zur Verdrahtung - NICHT nur daily_fib_zone direkt pruefen.

    Dieselbe Lehre wie dreimal zuvor in diesem Projekt: Ein Test, der nur die
    Hilfsfunktion aufruft, bleibt gruen, wenn der Parameter auf dem Weg durch
    evaluate() verlorengeht. Hier wird er deshalb ueber evaluate() gemessen:
    Mit der Standardweite findet die 1D-Ebene das Aufwaerts-Bein 99,8 -> 140,3 und
    steigt am 0.5-Level ein; mit einer sehr feinen Weite (n=2) zeichnet sie ein
    anderes, abwaertsgerichtetes Bein und steigt gar nicht ein.
    """
    cs, flow = _zwei_ebenen_serie()

    pos_std = Position()
    sig_std = evaluate(cs, flow, pos_std, bias_short=False, zonen_1d=True, pivot_n_1d=0)
    assert len(sig_std) == 1 and sig_std[0].type == SignalType.KAUF_1
    assert abs(sig_std[0].price - 120.04) < 0.05

    pos_fein = Position()
    sig_fein = evaluate(cs, flow, pos_fein, bias_short=False, zonen_1d=True, pivot_n_1d=2)
    assert sig_fein == [], (
        "mit feiner 1D-Weite zeichnet die Ebene ein anderes Bein und steigt nicht ein - "
        f"kam aber: {[x.type.name for x in sig_fein]}")
    assert pos_fein.state == PosState.FLAT


# ------------- E33: uebergeordneter Trend (13.09.2026)

def _lange_serie(n_kerzen=1300, seed=42):
    """Eine lange, schwankende 4h-Serie - lang genug fuer einen echten EMA200 auf 1D."""
    import random
    r = random.Random(seed)
    preise, p = [], 60000.0
    for _ in range(n_kerzen):
        p *= 1 + r.gauss(0.0004, 0.012)
        preise.append(p)
    return [c(i * H4_MS, x, x * 1.006, x * 0.994, x) for i, x in enumerate(preise)]


def _live_einstellung() -> dict:
    """Die Live-Einstellung aus der Panel-Zeile des Gitters (E43.5).

    Vorher stand hier eine eigene, von Hand gepflegte Liste - und sie war veraltet:
    stop_rueckeroberung (live seit 21.09.) und bein_richtung (live seit 26.09.) fehlten.
    Die Panel-Zeile prueft test_panel_variante_entspricht_der_live_einstellung gegen
    config.json; sie ist damit die eine Quelle, die nicht still veralten kann.
    """
    import backtest
    panel = [v for v in backtest.GRID if v.get("panel")]
    assert len(panel) == 1
    return {k: panel[0][k] for k in backtest.EVAL_KEYS}


def _flow_ab(kerzen, roh, aus, bis):
    """Flow-Punkte fuer das Ladefenster kerzen[aus:bis], die CVD-Summen AB NULL.

    Genau so rechnet main.fetch_data: Die Summe beginnt bei jedem Lauf neu, an der
    ersten geladenen Kerze. `roh[i]` = (Spot-Delta $, Futures-Delta BTC, OI $, Funding)
    der Kerze i - Werte, die nicht von der Historie abhaengen. Vor E43.5 schnitt der
    Test EINE vorgerechnete Summe verschieden weit aus; der Startwert der Summe war
    dadurch in beiden Fenstern derselbe, und genau davon haengt Befund A2 ab.
    """
    spot = fut = 0.0
    out = []
    for i in range(aus, bis):
        sd, fd, oi, fu = roh[i]
        spot += sd
        fut += fd
        out.append(FlowPoint(kerzen[i].ts, spot, fut, oi, fu))
    return out


def test_mehr_historie_aendert_die_signale_nicht():
    """DIE Voraussetzung fuer E33-A: LIMIT durfte nur erhoeht werden, wenn dadurch kein
    einziges Signal anders ausfaellt. Sonst waere aus einer Datenbeschaffung heimlich
    eine Strategieaenderung geworden.

    Geprueft wird die LIVE-Einstellung ueber die letzten 60 Kerzen, einmal mit einem
    Ladefenster von 400 und einmal mit 1200. Seit E43.5 beginnen die CVD-Summen in jedem
    Fenster bei null (wie live).

    WAS DIESER TEST NICHT DECKT: Muster 2 (Derivate-Pump). Der Flow hier steigt gleich-
    maessig, OI kaum, Funding konstant - der Zweig wird nie erreicht (Befund A4). Das
    deckt test_e435_... mit einem eigenen Szenario ab.
    """
    kerzen = _lange_serie()
    roh = [(7.0, 5.0, 1e9 * (1 + i * 0.0005), 0.0001) for i in range(len(kerzen))]
    LIVE = _live_einstellung()

    def lauf(fenster, n_letzte=60):
        pos, sigs = Position(), []
        for i in range(len(kerzen) - n_letzte, len(kerzen) + 1):
            aus = max(0, i - fenster)
            sigs += evaluate(kerzen[aus:i], _flow_ab(kerzen, roh, aus, i), pos, **LIVE)
        return [(x.ts, x.type, round(x.price, 4)) for x in sigs], pos.state

    klein, st_klein = lauf(400)
    gross, st_gross = lauf(1200)
    assert klein, "Vorprobe: ohne ein einziges Signal prueft der Vergleich nichts"
    assert klein == gross, (
        f"mehr Historie darf die Signale nicht veraendern: "
        f"{len(klein)} gegen {len(gross)} Signale")
    assert st_klein == st_gross


# ------------------------------- E43.5: "mehr Historie" erreicht Muster 2 (Befund A4)

PUMP_ZYKLUS, PUMP_AB, PUMP_BIS = 36, 20, 32     # Kerzen 20-31 jedes 36er-Zyklus pumpen


def _pump_szenario(n_kerzen=1300, seed=42):
    """Kerzen plus Rohdaten mit wiederkehrenden Pump-Phasen (E43.5).

    In einer Pump-Phase steigen Kurs, Futures-Delta (+400 BTC je Kerze), OI (+0,6 % je
    Kerze) und Funding gemeinsam, das Spot-Delta nur wenig (+1 Mio $): Furkans
    Derivate-Pump. Danach gibt der Kurs nach, OI und Funding fallen zurueck.
    Dazwischen schwanken Spot- und Futures-Delta langsam mit VERSCHIEDENEN Perioden -
    dadurch ist die kumulierte Summe je nach Startpunkt verschieden gross, wie in echten
    Daten. Genau das macht den alten Vergleich spot <= fut/3 fensterabhaengig.
    """
    import math
    import random
    r = random.Random(seed)
    p, kerzen, roh = 60000.0, [], []
    for i in range(n_kerzen):
        ph = i % PUMP_ZYKLUS
        pump = PUMP_AB <= ph < PUMP_BIS
        nach = PUMP_BIS <= ph < PUMP_BIS + 6
        p *= 1 + r.gauss(0.0004, 0.012) + (0.006 if pump else 0) - (0.012 if nach else 0)
        kerzen.append(c(i * H4_MS, p, p * 1.006, p * 0.994, p))
        spot_d = 4e6 * math.sin(i / 37.0) + (1e6 if pump else 0.0)
        fut_d = 150 * math.sin(i / 53.0 + 1) + (400.0 if pump else 0.0)
        oi = 1e9 * (1 + 0.006 * (min(ph, PUMP_BIS - 1) - PUMP_AB + 1)) if ph >= PUMP_AB \
            else 1e9
        funding = 0.00005 + (0.00001 * (ph - PUMP_AB + 1) if pump else 0.0)
        roh.append((spot_d, fut_d, oi, funding))
    return kerzen, roh


def _muster_je_fenster(kerzen, roh, fenster, n_letzte=60, **kw):
    out = []
    for i in range(len(kerzen) - n_letzte, len(kerzen) + 1):
        aus = max(0, i - fenster)
        out.append(classify_pattern(kerzen[aus:i], _flow_ab(kerzen, roh, aus, i), **kw))
    return out


def test_e435_szenario_erreicht_den_muster2_zweig():
    """Vorprobe (Projektregel 2): Erst nachweisen, dass das Szenario den geprueften
    Zweig ueberhaupt erreicht. Der alte Test tat das nie - A2 blieb deshalb unentdeckt.

    Geprueft wird zweierlei: (1) die Voraussetzungen von Muster 2 AUSSER dem strittigen
    Groessenvergleich liegen mehrfach vor (Kurs hoch, Futures hoch, OI >= 3 %, Funding
    zieht an), (2) classify_pattern erkennt in BEIDEN Ladefenstern mindestens einmal
    DERIVATE_PUMP.
    """
    kerzen, roh = _pump_szenario()
    n = len(kerzen)
    voraussetzungen = 0
    for i in range(n - 60, n + 1):
        cs, fl = kerzen[i - 12:i], _flow_ab(kerzen, roh, i - 12, i)
        if ((cs[-1].close > cs[0].close) and fl[-1].fut_cvd > fl[0].fut_cvd
                and (fl[-1].oi - fl[0].oi) / fl[0].oi >= 0.03
                and fl[-1].funding > fl[0].funding):
            voraussetzungen += 1
    assert voraussetzungen >= 5, f"nur {voraussetzungen} Kerzen mit Pump-Voraussetzungen"
    for fenster in (400, 1200):
        m = _muster_je_fenster(kerzen, roh, fenster)
        assert Pattern.DERIVATE_PUMP in m, f"Fenster {fenster}: Muster 2 nie erreicht"


def test_e435_befund_a2_mehr_historie_dreht_muster2():
    """Befund A2, im Test nachgestellt: Mit der BISHERIGEN Rechnung (relative Slopes,
    geteilt durch den willkuerlichen Stand der Summe) erkennt die Engine bei 400 und bei
    1200 geladenen Kerzen verschiedene Muster - bei identischer Marktlage.

    Und JEDE abweichende Kerze hat auf einer Seite DERIVATE_PUMP: Die Abweichung kommt
    genau aus dem Groessenvergleich in Muster 2, nicht von woanders (die Vorzeichen-
    Pruefungen der anderen Muster sind vom Startwert unabhaengig).

    Dieser Test haelt den Fehler fest, er billigt ihn nicht: E43.3 muss ihn bei
    muster_cvd="usd" verschwinden lassen; bei "alt" muss er bestehen bleiben, sonst
    rechnet "alt" nicht mehr wie bisher.
    """
    kerzen, roh = _pump_szenario()
    klein = _muster_je_fenster(kerzen, roh, 400, muster_cvd="alt")
    gross = _muster_je_fenster(kerzen, roh, 1200, muster_cvd="alt")
    anders = [(a, b) for a, b in zip(klein, gross) if a != b]
    assert anders, "A2 ist im Szenario nicht nachgestellt - der Test prueft dann nichts"
    assert all(Pattern.DERIVATE_PUMP in paar for paar in anders), anders


# ------------------------------------------ E43.3: Muster 2 in Dollar (Befund A2)

def _demo_slope(spot_start, fut_start):
    """demo_slope.py aus dem Pruefbericht (Anhang), als bleibender Test verdrahtet.

    Identische Marktlage: Kurs +3 %, Spot +200 Mio $, Futures +2.000 BTC, OI +4 %,
    Funding steigt leicht. Geaendert wird NUR der Startwert der beiden Summen - also
    genau das, was live und im Backtest verschieden ist.
    """
    cs, fl = [], []
    for i in range(12):
        p = 60000 * (1 + 0.03 * i / 11)
        cs.append(Candle(i, p, p * 1.002, p * 0.998, p))
        fl.append(FlowPoint(i, spot_start + 200e6 * i / 11, fut_start + 2000 * i / 11,
                            10e9 * (1 + 0.04 * i / 11), 0.00002 + 0.000001 * i))
    return cs, fl


_DEMO_STARTWERTE = [(-5e9, -20000), (-0.5e9, -20000), (-50e9, -20000), (-5e9, 1000)]


def test_e433_vorprobe_demo_slope_alt_verschieden_usd_gleich():
    """Die Vorprobe aus dem Bauplan: bei "alt" ergibt dieselbe Lage je nach Startwert
    verschiedene Muster (Ergebnis des Pruefberichts 26.09.2026), bei "usd" immer
    dasselbe. Ohne den ersten Teil waere nicht bewiesen, dass das Szenario den Fehler
    ueberhaupt enthaelt."""
    alt = [classify_pattern(*_demo_slope(sp, fu), muster_cvd="alt")
           for sp, fu in _DEMO_STARTWERTE]
    assert alt == [Pattern.GESUNDER_TREND, Pattern.GESUNDER_TREND,
                   Pattern.DERIVATE_PUMP, Pattern.DERIVATE_PUMP], alt
    usd = [classify_pattern(*_demo_slope(sp, fu), muster_cvd="usd")
           for sp, fu in _DEMO_STARTWERTE]
    assert len(set(usd)) == 1, usd
    # Spot +200 Mio $ gegen Futures ~ +122 Mio $: Spot traegt die Bewegung - das ist
    # Furkans gesunder Trend, kein Derivate-Pump.
    assert usd[0] == Pattern.GESUNDER_TREND


def test_e433_usd_erkennt_den_pump_in_dollar():
    """Die Gegenrichtung: Wo die Futures in Dollar das Dreifache des Spot uebertreffen,
    muss "usd" den Derivate-Pump auch erkennen - sonst waere "usd" nur ein Weg, Muster
    2 abzuschalten. Spot +20 Mio $, Futures 2.000 BTC (~122 Mio $) -> Pump."""
    cs, fl = _demo_slope(-5e9, -20000)
    fl = [FlowPoint(p.ts, -5e9 + 20e6 * i / 11, p.fut_cvd, p.oi, p.funding)
          for i, p in enumerate(fl)]
    assert classify_pattern(cs, fl, muster_cvd="usd") == Pattern.DERIVATE_PUMP
    # Grenze genau am Dreifachen: Spot = Futures/3 ist noch Pump, knapp darueber nicht
    fut_usd = sum((b.fut_cvd - a.fut_cvd) * k.close for a, b, k in zip(fl, fl[1:], cs[1:]))
    for spot, erwartet in ((fut_usd / 3 * 0.999, True), (fut_usd / 3 * 1.01, False)):
        f2 = [FlowPoint(p.ts, -5e9 + spot * i / 11, p.fut_cvd, p.oi, p.funding)
              for i, p in enumerate(fl)]
        ist = classify_pattern(cs, f2, muster_cvd="usd") == Pattern.DERIVATE_PUMP
        assert ist is erwartet, (spot, fut_usd)


def test_e433_usd_rechnet_jedes_delta_mit_dem_kurs_seiner_kerze():
    """Ein Kurs fuer das ganze Fenster waere bei 3 % Kursbewegung 3 % daneben - und
    genau an der Dreifach-Grenze kippt dann das Muster. Hier: Futures-Delta nur in der
    LETZTEN Kerze (Kurs 61.800), Spot knapp unter einem Drittel davon. Wer mit dem
    ersten Kurs (60.000) rechnet, sieht keinen Pump mehr."""
    cs, fl = _demo_slope(-5e9, -20000)
    k_letzt = cs[-1].close
    fut_usd = 2000 * k_letzt
    spot = fut_usd / 3 * 0.99                       # Pump nur mit dem richtigen Kurs
    assert spot > 2000 * cs[0].close / 3            # mit dem Anfangskurs waere es keiner
    f2 = [FlowPoint(p.ts, -5e9 + spot * i / 11,
                    -20000 + (2000 if i == 11 else 0), p.oi, p.funding)
          for i, p in enumerate(fl)]
    assert classify_pattern(cs, f2, muster_cvd="usd") == Pattern.DERIVATE_PUMP


def test_e433_fallende_futures_sind_kein_pump():
    """Muster 2 heisst: Futures TREIBEN den Kurs. Fallen Spot UND Futures, gilt
    rechnerisch trotzdem spot <= fut/3 (-100 Mio <= -20 Mio) - ohne die Pruefung
    "Futures steigt" waere das ein Derivate-Pump. Vorprobe: alle uebrigen
    Pump-Bedingungen liegen vor, und mit steigenden Futures IST es ein Pump."""
    cs, fl = _demo_slope(-5e9, -20000)
    assert cs[-1].close > cs[0].close                           # Kurs hoch
    assert (fl[-1].oi - fl[0].oi) / fl[0].oi >= 0.03            # OI deutlich hoch
    assert fl[-1].funding > fl[0].funding                       # Funding zieht an
    fallend = [FlowPoint(p.ts, -5e9 - 100e6 * i / 11, -20000 - 1000 * i / 11, p.oi,
                         p.funding) for i, p in enumerate(fl)]
    assert classify_pattern(cs, fallend, muster_cvd="usd") != Pattern.DERIVATE_PUMP
    steigend = [FlowPoint(p.ts, -5e9 + 10e6 * i / 11, -20000 + 1000 * i / 11, p.oi,
                          p.funding) for i, p in enumerate(fl)]
    assert classify_pattern(cs, steigend, muster_cvd="usd") == Pattern.DERIVATE_PUMP


def test_e433_ohne_kerze_zum_flowpunkt_kein_pump():
    """Fehlt zu einem Flow-Punkt die Kerze, gibt es keinen Kurs - lieber kein Pump als
    einer mit falschem Kurs. Vorprobe: mit Kerzen IST es ein Pump."""
    cs, fl = _demo_slope(-5e9, -20000)
    fl = [FlowPoint(p.ts, -5e9 + 20e6 * i / 11, p.fut_cvd, p.oi, p.funding)
          for i, p in enumerate(fl)]
    assert classify_pattern(cs, fl, muster_cvd="usd") == Pattern.DERIVATE_PUMP
    verschoben = [FlowPoint(p.ts + 1, p.spot_cvd, p.fut_cvd, p.oi, p.funding) for p in fl]
    assert classify_pattern(cs, verschoben, muster_cvd="usd") != Pattern.DERIVATE_PUMP
    # "alt" braucht keinen Kurs und bleibt davon unberuehrt
    assert classify_pattern(cs, verschoben, muster_cvd="alt") == \
        classify_pattern(cs, fl, muster_cvd="alt")


def test_e433_mehr_historie_aendert_muster2_nicht_bei_usd():
    """Der Kern von E43.3: Mit "usd" erkennt die Engine bei 400 und bei 1200 geladenen
    Kerzen DIESELBEN Muster - live und Backtest sehen dieselbe Lage gleich.

    Und durch evaluate() hindurch: Die Signale sind gleich - mit einer benannten
    Ausnahme, Nebenbefund A5 (Teilgewinn am letzten Hoch haengt von der Laenge der
    Historie ab, docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md, Abschnitt E43.5). Jede ANDERE
    Abweichung macht den Test rot. Wird A5 behoben, faellt die Ausnahme weg.

    Vorprobe: Bei "alt" unterscheiden sich die Derivate-Pump-Warnungen zwischen den
    Fenstern - der Vergleich erreicht Muster 2 also auch auf Signal-Ebene.
    """
    kerzen, roh = _pump_szenario()
    klein = _muster_je_fenster(kerzen, roh, 400, muster_cvd="usd")
    gross = _muster_je_fenster(kerzen, roh, 1200, muster_cvd="usd")
    assert Pattern.DERIVATE_PUMP in klein, "Vorprobe: usd erreicht Muster 2 nie"
    assert klein == gross

    n = len(kerzen)

    def lauf(fenster, muster_cvd, n_letzte=60):
        live = dict(_live_einstellung(), muster_cvd=muster_cvd)
        pos, sigs = Position(), []
        for i in range(n - n_letzte, n + 1):
            aus = max(0, i - fenster)
            sigs += evaluate(kerzen[aus:i], _flow_ab(kerzen, roh, aus, i), pos, **live)
        return [(x.ts, x.type, round(x.price, 4), x.reason) for x in sigs]

    def pump_warnungen(sigs):
        return [x for x in sigs if x[1] == SignalType.WARNUNG and "Derivate-Pump" in x[3]]

    assert pump_warnungen(lauf(400, "alt")) != pump_warnungen(lauf(1200, "alt")), \
        "Vorprobe: bei alt muessten sich die Pump-Warnungen unterscheiden (A2)"

    a5 = "Teilgewinn am letzten Hoch"
    k, g = lauf(400, "usd"), lauf(1200, "usd")
    assert pump_warnungen(k), "Vorprobe: ohne Pump-Warnung prueft der Vergleich nichts"
    rest_k = [x for x in k if not x[3].startswith(a5)]
    rest_g = [x for x in g if not x[3].startswith(a5)]
    assert rest_k == rest_g, [x for x in rest_k + rest_g if (x in rest_k) != (x in rest_g)]


def test_e433_muster_cvd_kommt_in_evaluate_an():
    """Der Weg DURCH evaluate(): Stehen die Muster bei alt und usd verschieden, muessen
    sich auch die Signale unterscheiden. Bliebe der Parameter in evaluate() haengen,
    rechnete die Gitterzeile still mit "alt" - eine Kopie der Live-Zeile."""
    kerzen, roh = _pump_szenario()
    n = len(kerzen)

    def lauf(muster_cvd):
        live = dict(_live_einstellung(), muster_cvd=muster_cvd)
        pos, sigs = Position(), []
        for i in range(n - 60, n + 1):
            sigs += evaluate(kerzen[i - 400:i], _flow_ab(kerzen, roh, i - 400, i), pos,
                             **live)
        return [(x.ts, x.type, x.reason) for x in sigs]

    assert lauf("alt") != lauf("usd")


# ---------------------------------------- E43.4: OI in Kontrakten statt Dollar (Befund A3)

def _oi_lage(kurs, kontrakte, spot_d, fut_d, funding, spot_dreht=False):
    """12 Kerzen (2 Tage). Kurs und Zahl der Kontrakte aendern sich gleichmaessig um
    `kurs` bzw. `kontrakte` (Anteile). Das OI steht in Dollar = Kontrakte x Kurs, wie
    Coinalyze es liefert (demo_oi_usd.py aus dem Pruefbericht); `oi_btc` entsteht ueber
    oi_in_btc, wie live und im Backtest."""
    from dataclasses import replace
    from strategy_core import oi_in_btc
    cs, fl, sp, fu = [], [], -5e9, -20000.0
    for i in range(12):
        p = 60000 * (1 + kurs * i / 11)
        cs.append(Candle(i, p, p * 1.002, p * 0.998, p))
        d = spot_d / 11
        if spot_dreht and i >= 10:
            d = abs(d) * 3
        sp += d if i else 0
        fu += fut_d / 11 if i else 0
        f = funding[i] if isinstance(funding, list) else funding
        fl.append(FlowPoint(i, sp, fu, 100_000.0 * (1 + kontrakte * i / 11) * p, f))
    btc = oi_in_btc({x.ts: x.oi for x in fl}, {x.ts: x.close for x in cs})
    return cs, [replace(x, oi_btc=btc[x.ts]) for x in fl]


_FUNDING_ZIEHT = [0.00002 + 1e-6 * i for i in range(12)]
# (Kurs, Kontrakte, Spot-Delta $, Futures-Delta BTC, Funding, Spot dreht)
_A3_KAPITULATION = (-0.05, 0.0, -300e6, -3000, 0.00002, True)
_A3_PUMP = (0.035, 0.0, 5e6, 3000, _FUNDING_ZIEHT, False)


def test_e434_vorprobe_demo_oi_usd_erkennt_am_kurs():
    """Die Vorprobe aus dem Bauplan (Pruefbericht, demo_oi_usd.py): Die Zahl der
    Kontrakte bleibt GLEICH, nur der Kurs bewegt sich. In Dollar erkennt die Engine
    trotzdem eine Kapitulation ("OI-Wipeout") und einen Derivate-Pump ("neues Geld") -
    das ist Befund A3. In Kontrakten erkennt sie beides nicht. Ohne den ersten Teil waere
    nicht bewiesen, dass das Szenario den Fehler ueberhaupt enthaelt."""
    kap, pump = _oi_lage(*_A3_KAPITULATION), _oi_lage(*_A3_PUMP)
    assert classify_pattern(*kap, muster_oi="usd") == Pattern.CAPITULATION_RESET
    assert classify_pattern(*pump, muster_oi="usd") == Pattern.DERIVATE_PUMP
    assert classify_pattern(*kap, muster_oi="btc") == Pattern.UNGESUNDER_ABVERKAUF
    assert classify_pattern(*pump, muster_oi="btc") == Pattern.GESUNDER_TREND


def test_e434_btc_erkennt_echte_kontrakt_aenderung():
    """Die Gegenprobe: Schliessen die Haendler wirklich Positionen (-6 %) oder eroeffnen
    sie neue (+4 %), erkennt "btc" Kapitulation und Derivate-Pump weiter. Sonst waere
    "btc" nur ein Weg, Muster 2 und 4 abzuschalten."""
    k, _k, sd, fd, fu, dreht = _A3_KAPITULATION
    assert classify_pattern(*_oi_lage(k, -0.06, sd, fd, fu, dreht), muster_oi="btc") \
        == Pattern.CAPITULATION_RESET
    k, _k, sd, fd, fu, dreht = _A3_PUMP
    assert classify_pattern(*_oi_lage(k, 0.04, sd, fd, fu, dreht), muster_oi="btc") \
        == Pattern.DERIVATE_PUMP


def test_e434_btc_wirkt_in_allen_mustern_die_das_oi_lesen():
    """Es gibt nur EIN oi_chg. Muster 1, 3 und 5 lesen es genauso wie 2 und 4 - wuerde
    "btc" nur in einem Teil der Muster wirken, stuenden in derselben Einordnung zwei
    Einheiten. Je Muster eine Lage, die nur in Kontrakten (oder nur in Dollar) passt:
      - 5: Kurs -3 %, Kontrakte gleich -> Dollar-OI -3 %, zu tief fuer "OI haelt".
      - 3: Kurs +3 %, Kontrakte -2,5 % -> in Dollar +0,4 %, kein Short-Covering.
      - 1: Kurs +3 %, Kontrakte -1 % -> in Dollar +2 % (passt), in Kontrakten -1 %.
    """
    faelle = [
        ((-0.03, 0.0, -300e6, -3000, 0.00002), Pattern.NEUTRAL,
         Pattern.UNGESUNDER_ABVERKAUF),
        ((0.03, -0.025, 200e6, 100, 0.00002), Pattern.GESUNDER_TREND,
         Pattern.SHORT_COVERING),
        ((0.03, -0.01, 200e6, 100, 0.00002), Pattern.GESUNDER_TREND, Pattern.NEUTRAL),
    ]
    for lage, usd, btc in faelle:
        cs, fl = _oi_lage(*lage)
        assert classify_pattern(cs, fl, muster_oi="usd") == usd, lage
        assert classify_pattern(cs, fl, muster_oi="btc") == btc, lage


def test_e434_oi_in_btc_rechnet_jeden_punkt_mit_dem_kurs_seiner_kerze():
    """Jeder OI-Punkt geteilt durch den Schlusskurs DERSELBEN Kerze. Ein Punkt ohne
    Kerze entfaellt - lieber kein Wert als einer mit falschem Kurs."""
    from strategy_core import oi_in_btc
    kurs = {0: 50_000.0, 1: 100_000.0}
    assert oi_in_btc({0: 5e9, 1: 5e9, 2: 5e9}, kurs) == {0: 100_000.0, 1: 50_000.0}
    assert oi_in_btc({}, kurs) == {}


def test_e434_ohne_oi_daten_rechnen_usd_und_btc_gleich():
    """Ohne OI-Daten steht das Dollar-OI konstant (Backtest: 1.0) und es gibt keine
    Kontrakt-Reihe (oi_btc = 0). Beide Einstellungen muessen dann dasselbe sagen: keine
    OI-Bewegung. Sonst erfaende "btc" aus fehlenden Daten ein Signal."""
    from dataclasses import replace
    from strategy_core import oi_aenderung
    for lage in (_A3_KAPITULATION, _A3_PUMP, (0.03, -0.025, 200e6, 100, 0.00002, False)):
        cs, fl = _oi_lage(*lage)
        leer = [replace(x, oi=1.0, oi_btc=0.0) for x in fl]
        assert oi_aenderung(leer, "btc") == 0.0 == oi_aenderung(leer, "usd")
        assert classify_pattern(cs, leer, muster_oi="btc") == \
            classify_pattern(cs, leer, muster_oi="usd"), lage


def test_e434_usd_rechnet_wie_vor_e434():
    """Default "usd" ist das bisherige Verhalten, Zeichen fuer Zeichen - auch im
    Randfall, dass das OI am Fensterende 0 ist (live ohne jede OI-Quelle moeglich): dort
    ergab die alte Formel -100 %, und dabei bleibt es."""
    from strategy_core import oi_aenderung
    fl = [FlowPoint(i, 0.0, 0.0, 1000.0 if i < 11 else 0.0, 0.0) for i in range(12)]
    assert oi_aenderung(fl, "usd") == -1.0
    fl = [FlowPoint(i, 0.0, 0.0, 1000.0 + 10 * i, 0.0) for i in range(12)]
    assert oi_aenderung(fl, "usd") == (fl[-1].oi - fl[0].oi) / fl[0].oi


def _mit_kontrakten(kerzen, flow):
    """oi_btc zu einer Flow-Reihe, deren OI in Dollar steht - ueber oi_in_btc."""
    from dataclasses import replace
    from strategy_core import oi_in_btc
    btc = oi_in_btc({x.ts: x.oi for x in flow}, {x.ts: x.close for x in kerzen})
    return [replace(x, oi_btc=btc[x.ts]) for x in flow]


def test_e434_muster_oi_kommt_in_evaluate_an():
    """Der Weg DURCH evaluate(): Im Pump-Szenario steigt das Dollar-OI mit dem Kurs,
    die Kontrakte kaum - "usd" und "btc" erkennen verschiedene Muster. Dann muessen sich
    auch die Signale unterscheiden. Bliebe der Parameter in evaluate() haengen,
    rechnete die Gitterzeile still mit "usd" - eine Kopie der Live-Zeile."""
    kerzen, roh = _pump_szenario()
    n = len(kerzen)
    muster = {m: [classify_pattern(kerzen[i - 12:i],
                                   _mit_kontrakten(kerzen[i - 12:i],
                                                   _flow_ab(kerzen, roh, i - 12, i)),
                                   muster_oi=m) for i in range(n - 60, n + 1)]
              for m in ("usd", "btc")}
    assert muster["usd"] != muster["btc"], "Vorprobe: der Schalter aendert kein Muster"

    def lauf(muster_oi):
        live = dict(_live_einstellung(), muster_oi=muster_oi)
        pos, sigs = Position(), []
        for i in range(n - 60, n + 1):
            fl = _mit_kontrakten(kerzen[i - 400:i], _flow_ab(kerzen, roh, i - 400, i))
            sigs += evaluate(kerzen[i - 400:i], fl, pos, **live)
        return [(x.ts, x.type, x.reason) for x in sigs]

    assert lauf("usd") != lauf("btc")


# ------------------------- E43.4b: OI-Zeile im Lage-Abruf in Kontrakten (reine Anzeige)

def _oi_zeile_serie(kurs, kontrakte, mit_kontrakten=True, n=40, seed=7):
    """Kerzen + Flow fuer die OI-Zeile. Bis 12 Kerzen vor Schluss schwanken Kurs und
    Kontrakte leicht (daraus entsteht der Massstab fuer "flach"), in den letzten 12
    Kerzen aendern sie sich gleichmaessig um `kurs` bzw. `kontrakte`. Das OI steht in
    Dollar = Kontrakte x Kurs; oi_btc entsteht ueber oi_in_btc wie live."""
    import random
    from dataclasses import replace
    from strategy_core import oi_in_btc
    r = random.Random(seed)
    v, k, cs, fl = 76000.0, 100_000.0, [], []
    for i in range(n):
        if i < n - 12:
            v *= 1 + r.gauss(0, 0.004)
            k *= 1 + r.gauss(0, 0.004)
            v0, k0 = v, k
        else:
            j = i - (n - 13)
            v, k = v0 * (1 + kurs * j / 12), k0 * (1 + kontrakte * j / 12)
        cs.append(Candle(1_700_000_000_000 + i * H4_MS, v, v * 1.004, v * 0.996, v))
        fl.append(FlowPoint(cs[-1].ts, 1e9 + i * 1e6, 0.0, k * v, 0.0001))
    if mit_kontrakten:
        btc = oi_in_btc({x.ts: x.oi for x in fl}, {x.ts: x.close for x in cs})
        fl = [replace(x, oi_btc=btc[x.ts]) for x in fl]
    return cs, fl


def _oi_zeile(kurs, kontrakte, **kw):
    cs, fl = _oi_zeile_serie(kurs, kontrakte, **kw)
    return [z for z in orderflow_detail(cs, fl) if z["name"] == "Open Interest"][0]


def test_e434b_kurs_allein_heisst_nicht_neues_geld():
    """Der Fehler aus A3 in der Anzeige: Kurs +3 %, die Kontrakte bleiben gleich. In
    Dollar steigt das OI um 3 %, und bisher stand dort "neues Geld kommt herein". Jetzt
    folgen Pfeil und Hinweis den Kontrakten, und der Hinweis sagt, woher der
    Dollar-Anstieg kommt. Vorprobe: Ohne Kontrakt-Reihe zeigt dieselbe Lage den alten
    Fehler - das Szenario enthaelt ihn also."""
    alt = _oi_zeile(0.03, 0.0, mit_kontrakten=False)
    assert alt["richtung"] == "steigt" and alt["hinweis"] == "neues Geld kommt herein", alt
    z = _oi_zeile(0.03, 0.0)
    assert "Kontrakte +0,0 %" in z["wert"] and "(+3,0 %)" in z["wert"], z
    assert z["richtung"] == "flach", z
    assert z["hinweis"] == "unveraendert - der Dollar-Anstieg kommt nur vom Kurs", z


def test_e434b_kursrutsch_heisst_nicht_positionen_werden_geschlossen():
    """Kurs -5 %, niemand schliesst eine Position: bisher "Positionen werden
    geschlossen". Jetzt: unveraendert, und der Rueckgang kommt nur vom Kurs."""
    assert _oi_zeile(-0.05, 0.0, mit_kontrakten=False)["hinweis"] == \
        "Positionen werden geschlossen"                               # Vorprobe
    z = _oi_zeile(-0.05, 0.0)
    assert z["richtung"] == "flach", z
    assert z["hinweis"] == "unveraendert - der Dollar-Rueckgang kommt nur vom Kurs", z


def test_e434b_echte_kontrakt_aenderung_bleibt_sichtbar():
    """Die Gegenprobe: Kommen wirklich neue Positionen dazu (+4 %), heisst es weiter
    "neues Geld kommt herein" - ohne Kurs-Bemerkung, wenn Dollar und Kontrakte
    gemeinsam steigen. Und wenn der Kurs den Anstieg in Dollar verdeckt (Kurs -4 %,
    Kontrakte +4 %, Dollar etwa flach), sagt der Hinweis genau das."""
    z = _oi_zeile(0.0, 0.04)
    assert z["richtung"] == "steigt" and z["hinweis"] == "neues Geld kommt herein", z
    assert "Kontrakte +4,0 %" in z["wert"], z
    z = _oi_zeile(-0.04, 0.04)
    assert z["richtung"] == "steigt", z
    assert z["hinweis"] == "neues Geld kommt herein - in Dollar vom Kurs verdeckt", z
    z = _oi_zeile(0.0, -0.04)
    assert z["richtung"] == "faellt" and z["hinweis"] == "Positionen werden geschlossen", z


def test_e434b_ohne_kontrakt_reihe_bleibt_die_zeile_wie_bisher():
    """Ohne Kontrakt-Reihe (Kraken-Rueckfall, oi_btc = 0) keine Zeile "Kontrakte 0 %"
    - das behauptete Stillstand, wo nichts bekannt ist. Richtung und Hinweis folgen
    dann wie vor E43.4b dem Dollar-Wert."""
    for kurs, kontrakte in ((0.03, 0.0), (0.0, 0.04), (-0.05, 0.0)):
        z = _oi_zeile(kurs, kontrakte, mit_kontrakten=False)
        assert "Kontrakte" not in z["wert"], z
        assert "Kurs" not in z["hinweis"], z


def test_ema200_braucht_echte_historie():
    """Der stille Fehler, den E33 behebt: Mit 400 Kerzen (67 Tage) lieferte
    daily_trend(period=200) klaglos einen EMA67 und gab ihn als EMA200 aus."""
    kerzen = _lange_serie()
    kurz, lang = kerzen[-400:], kerzen[-1200:]
    assert len(resample_daily(kurz)) < 200, "400 Kerzen duerfen keine 200 Tage ergeben"
    assert len(resample_daily(lang)) >= 200, "1200 Kerzen muessen fuer EMA200 reichen"

    # streng: kurze Historie -> keine Aussage
    assert daily_trend(kurz, 200, streng=True) is None
    assert daily_trend(lang, 200, streng=True) is not None

    # ohne streng: beide liefern eine Zahl - aber eben verschiedene
    e_kurz = daily_trend(kurz, 200)[1]
    e_lang = daily_trend(lang, 200)[1]
    assert abs(e_kurz - e_lang) / e_lang > 0.05, (
        "genau darin lag der Fehler: der kurze EMA weicht deutlich ab "
        f"({e_kurz:.0f} gegen {e_lang:.0f})")


def test_trend_lage_liefert_klartext_oder_nichts():
    """E33-B: Anzeige, keine Regel. Ohne ausreichende Historie lieber gar nichts."""
    kerzen = _lange_serie()
    assert trend_lage(kerzen[-400:], 200) is None          # zu wenig Historie

    tl = trend_lage(kerzen[-1200:], 200)
    assert tl is not None
    assert tl["stand"] in ("ueber", "unter")
    assert "EMA200" in tl["text"] and "Uebergeordnet" in tl["text"]
    # die Aussage muss zu den Zahlen passen
    assert (tl["kurs"] >= tl["ema"]) == (tl["stand"] == "ueber")


def test_lage_bericht_nimmt_den_trend_auf():
    """Der Trend steht in der Lage - und nur, wenn eine Periode verlangt wird."""
    kerzen = _lange_serie()
    f = [FlowPoint(k.ts, 100 + i, 100, 1000, 0.0001) for i, k in enumerate(kerzen)]
    mit = lage_bericht(kerzen[-1200:], f[-1200:], trend_period=200)
    assert "trend" in mit and "Uebergeordnet" in mit["trend_text"]
    ohne = lage_bericht(kerzen[-1200:], f[-1200:], trend_period=0)
    assert "trend" not in ohne
    # zu kurze Historie -> keine Trendangabe, aber der Rest der Lage bleibt
    kurz = lage_bericht(kerzen[-400:], f[-400:], trend_period=200)
    assert "trend" not in kurz and "spot" in kurz


# ------------------------------------------------- E34: die Ampel

def test_ampel_stufen_nach_einfacher_mehrheit():
    """Die Regel in Reinform: Mehrheit unter denen, die ueberhaupt etwas sagen."""
    alles_dafuer = {"trend": "ueber", "struktur": "intakt",
                    "spot": "zurueckgekehrt", "muster": "GESUNDER_TREND"}
    a = ampel(alles_dafuer)
    assert a["stufe"] == "guenstig" and a["gezaehlt"] == 4
    assert a["dagegen"] == [] and len(a["dafuer"]) == 4
    assert "4 von 4" in a["text"] and "GUENSTIG" in a["text"]

    alles_dagegen = {"trend": "unter", "struktur": "gebrochen",
                     "spot": "schwach", "muster": "DERIVATE_PUMP"}
    assert ampel(alles_dagegen)["stufe"] == "unguenstig"

    # 2:2 -> gemischt, nicht guenstig und nicht unguenstig
    assert ampel({"trend": "ueber", "struktur": "intakt",
                  "spot": "schwach", "muster": "DERIVATE_PUMP"})["stufe"] == "gemischt"
    # 3:1 -> die Mehrheit entscheidet, ein Gegenargument kippt sie nicht
    assert ampel({"trend": "ueber", "struktur": "intakt",
                  "spot": "stabil", "muster": "DERIVATE_PUMP"})["stufe"] == "guenstig"


def test_ampel_schweigt_bei_zu_duenner_lage():
    """Lieber keine Aussage als eine aus einem einzigen Datenpunkt."""
    assert ampel({}) is None
    assert ampel(None) is None
    assert ampel({"trend": "ueber"}) is None                    # nur eines sagt etwas
    # "neu" heisst: kein Vergleichsbein. Das ist kein Gegenargument, sondern Schweigen.
    assert ampel({"struktur": "neu", "trend": "ueber"}) is None
    assert ampel({"struktur": "neu", "trend": "ueber", "spot": "stabil"})["gezaehlt"] == 2
    # unbekannte Werte zaehlen nicht mit, statt still als "dagegen" zu gelten
    assert ampel({"trend": "seitwaerts", "spot": "stabil"}) is None


def test_ampel_kapitulation_spricht_fuer_den_long():
    """Die einzige Zeile, die ueberrascht - und der Grund steht im Bauplan:
    live steht flush_entry='core', die Engine kauft bewusst in die Kapitulation.
    Short-Covering dagegen ist ein Anstieg OHNE echte Nachfrage."""
    a = ampel({"muster": "CAPITULATION_RESET", "spot": "stabil"})
    assert a["dagegen"] == [] and "Muster" in a["dafuer"]
    b = ampel({"muster": "SHORT_COVERING", "spot": "stabil"})
    assert "Muster" in b["dagegen"]


def test_ampel_spiegelt_fuer_short_aber_nicht_die_struktur():
    """Der Fehler, den der erste Bauversuch hatte.

    Trend, Spot und Muster sind absolut (steigend/fallend) und kehren sich beim Short
    um. Die STRUKTUR kommt aus trend_intakt() und misst das Bein DER POSITION - bei
    einem Short also tieferes Tief und tieferes Hoch. Sie spricht damit immer schon in
    der Richtung der Position und darf nicht gespiegelt werden.
    """
    lage = {"trend": "unter", "struktur": "intakt",
            "spot": "nachgelassen", "muster": "UNGESUNDER_ABVERKAUF"}
    lang = ampel(lage, long_side=True)
    kurz = ampel(lage, long_side=False)
    assert lang["stufe"] == "unguenstig" and lang["dafuer"] == ["Struktur"]
    # fallender Markt + intakte Abwaertsstruktur + schwache Nachfrage = 4 von 4 fuer Short
    assert kurz["stufe"] == "guenstig" and kurz["dagegen"] == []
    assert "Struktur" in kurz["dafuer"]


def e34_signale(cs, fl, **kw):
    """Wie e13_lauf, gibt aber die Signal-Objekte zurueck - fuer die Tranchen.

    trend_ema=5 (E38, 21.09.2026): Bis dahin kam die UNGUENSTIGE Ampel in diesem
    Szenario aus Spot-Nachfrage + Muster 5. Seit E38 zaehlt Muster 5 neutral - dann
    sagte nur noch EIN Kriterium etwas, die Ampel schwieg, und die Ampel-Filter-Tests
    prueften ploetzlich nichts mehr. Mit einer kurzen EMA spricht der Trend (Kurs
    faellt -> "unter"), und die Ampel ist wieder UNGUENSTIG - diesmal aus Trend +
    Spot, ohne sich auf Muster 5 zu stuetzen. trend_ema wirkt nur auf die Lage (und
    auf trend_filter, der hier aus ist); Basis- und Vergleichslauf bekommen denselben
    Wert, der Vergleich bleibt einer mit genau einem Unterschied.
    """
    kw.setdefault("trend_ema", 5)
    pos = Position()
    raus = []
    for i in range(len(cs)):
        raus += evaluate(cs[:i + 1], fl[:i + 1], pos, bias_short=False, pivot_n=2, **kw)
    return raus


def _tranchen(sig):
    return [(s.type, s.tranche_pct) for s in sig if s.type in _ENTRY_TYPES]


def test_ampel_filter_aus_aendert_nichts():
    """Vorgabe 'off': live und in jeder bestehenden Gitterzeile passiert nichts."""
    cs, fl = e13_szenario()
    assert _tranchen(e34_signale(cs, fl)) == _tranchen(e34_signale(cs, fl, ampel_filter="off"))
    assert _tranchen(e34_signale(cs, fl))            # es gibt ueberhaupt Einstiege


def test_ampel_filter_klein_halbiert_bei_unguenstiger_lage():
    """Kaisers Frage in Testform: bei unguenstiger Ampel nur die halbe Tranche."""
    cs, fl = e13_szenario()                       # Spot faellt, ungesunder Abverkauf
    assert classify_pattern(cs, fl) == Pattern.UNGESUNDER_ABVERKAUF
    voll = _tranchen(e34_signale(cs, fl))
    halb = _tranchen(e34_signale(cs, fl, ampel_filter="klein"))
    assert [t for _s, t in voll] != [t for _s, t in halb], "die Ampel hat nichts bewirkt"
    assert [s for s, _t in voll] == [s for s, _t in halb], "es darf kein Signal entfallen"
    for (_sv, tv), (_sh, th) in zip(voll, halb):
        assert th == max(1, int(tv * AMPEL_TRANCHE))


def e34_szenario_mit_ausstieg():
    """e13_szenario, danach unter die Invalidierung (97,6) -> Einstiege UND ein Stop.

    Das Basis-Szenario erzeugt nur ein einziges KAUF_1 und ueberhaupt keinen Ausstieg.
    Ein Test, der dort "Ausstiege bleiben unberuehrt" prueft, vergleicht zwei leere
    Listen und ist gruen, egal was der Code tut - genau so ist die erste Fassung
    dieses Tests durch die Sabotage-Probe gerutscht.
    """
    cs, fl = e13_szenario()
    for v in (104, 101, 98, 95, 92):
        cs.append(Candle(cs[-1].ts + H4_MS, v, v * 1.004, v * 0.996, v))
        fl.append(FlowPoint(cs[-1].ts, fl[-1].spot_cvd - 30, 0.0,
                            fl[-1].oi + 1e6, 0.0002))
    return cs, fl


def test_kuerzen_laesst_ausstiege_unberuehrt():
    """Ein Ausstieg muss IMMER durchkommen - die Ampel darf nur Einstiege verkleinern.

    Ein halbierter STOPLOSS liesse die halbe Position im fallenden Markt liegen: der
    gefaehrlichste denkbare Fehler dieses Ausbaus. Geprueft wird hier direkt an
    kuerze_einstiege(), mit einer von Hand gemischten Liste - denn durch evaluate()
    ist der Fall heute nicht erreichbar (die Ausstiegs-Zweige kehren zurueck, bevor
    ein Einstieg feuern kann). Die erste Fassung dieses Tests lief deshalb ueber zwei
    LEERE Listen und war gruen, egal was der Code tat; die Sabotage-Probe hat sie
    entlarvt.
    """
    def sig(t, pct):
        return Signal(ts=1, type=t, price=100.0, tranche_pct=pct, reason="Test")

    liste = [sig(SignalType.KAUF_1, 25), sig(SignalType.STOPLOSS, 100),
             sig(SignalType.TEILVERKAUF_1, 40), sig(SignalType.NACHKAUF, 25),
             sig(SignalType.VERKAUF_REST, 20), sig(SignalType.WARNUNG, 0)]
    kuerze_einstiege(liste, lambda _long: True)      # haerter geht es nicht
    ergebnis = {s.type: s.tranche_pct for s in liste}
    assert ergebnis[SignalType.STOPLOSS] == 100, "der Stop wurde angefasst"
    assert ergebnis[SignalType.TEILVERKAUF_1] == 40
    assert ergebnis[SignalType.VERKAUF_REST] == 20
    assert ergebnis[SignalType.WARNUNG] == 0
    assert ergebnis[SignalType.KAUF_1] == 12 and ergebnis[SignalType.NACHKAUF] == 12


def test_kuerzen_fragt_je_signal_nach_der_richtung():
    """Was fuer einen Long spricht, spricht gegen einen Short - also wird je Signal
    in dessen eigener Richtung entschieden, nicht einmal pauschal fuer die Kerze."""
    def sig(t):
        return Signal(ts=1, type=t, price=100.0, tranche_pct=20, reason="Test")

    liste = [sig(SignalType.KAUF_1), sig(SignalType.SHORT_1)]
    gefragt = []

    def nur_long(long_side):
        gefragt.append(long_side)
        return long_side

    kuerze_einstiege(liste, nur_long)
    assert sorted(gefragt) == [False, True], "die Richtung wurde nicht je Signal gefragt"
    assert [s.tranche_pct for s in liste] == [10, 20]


def test_ampel_filter_laesst_ausstiege_auch_im_lauf_unberuehrt():
    """Dieselbe Zusicherung noch einmal durch evaluate() - Ende zu Ende."""
    cs, fl = e34_szenario_mit_ausstieg()
    voll = [(s.type, s.tranche_pct) for s in e34_signale(cs, fl)]
    halb = [(s.type, s.tranche_pct) for s in e34_signale(cs, fl, ampel_filter="klein")]
    aus_voll = [x for x in voll if x[0] not in _ENTRY_TYPES]
    assert aus_voll, "ohne Ausstieg prueft dieser Test nichts"
    assert any(t == 100 for _s, t in aus_voll), "der Stop muss die GANZE Position raeumen"
    assert aus_voll == [x for x in halb if x[0] not in _ENTRY_TYPES]
    # ... und die Einstiege im selben Lauf muessen sehr wohl kleiner geworden sein,
    # sonst waere die Gleichheit oben nur ein Zeichen dafuer, dass gar nichts wirkt
    ein_voll = [x for x in voll if x[0] in _ENTRY_TYPES]
    assert ein_voll and ein_voll != [x for x in halb if x[0] in _ENTRY_TYPES]


def test_ampel_filter_gegenprobe_und_nullhypothese():
    """Ohne diese beiden Zeilen waere ein gutes Ergebnis von 'klein' nicht deutbar.

    'gross' halbiert bei GUENSTIG - also im selben Szenario NICHT, weil die Lage hier
    unguenstig ist. 'immer' halbiert ohne jede Ampel, also auch hier.
    """
    cs, fl = e13_szenario()
    # nachweislich unguenstig - sonst waere dieser Test still gegenstandslos.
    # trend_period=5 wie in e34_signale: seit E38 zaehlt Muster 5 neutral, die
    # unguenstige Stufe kommt jetzt aus Trend + Spot. (Diese Vorprobe hat die Aenderung
    # als einzige der Ampel-Filter-Tests sofort gemeldet - genau dafuer steht sie da.)
    assert ampel(lage_bericht(cs, fl, pattern=classify_pattern(cs, fl),
                              trend_period=5))["stufe"] == "unguenstig"
    voll = [t for _s, t in _tranchen(e34_signale(cs, fl))]
    klein = [t for _s, t in _tranchen(e34_signale(cs, fl, ampel_filter="klein"))]
    gross = [t for _s, t in _tranchen(e34_signale(cs, fl, ampel_filter="gross"))]
    immer = [t for _s, t in _tranchen(e34_signale(cs, fl, ampel_filter="immer"))]
    assert klein != voll and klein == immer          # unguenstig -> beide halbieren
    assert gross == voll, "die umgekehrte Ampel darf hier gerade NICHT halbieren"


def test_ampel_filter_bei_guenstiger_lage_genau_andersherum():
    """Spiegelbild: jetzt ist die Lage guenstig - also halbiert 'gross' und 'klein' nicht.

    Ohne diesen Test koennte 'gross' schlicht nie halbieren und der Test oben waere
    trotzdem gruen.
    """
    cs, fl = e13_szenario(spot_faellt=False, oi_steigt=False)
    assert ampel(lage_bericht(cs, fl, pattern=classify_pattern(cs, fl),
                              trend_period=200))["stufe"] == "guenstig"
    voll = [t for _s, t in _tranchen(e34_signale(cs, fl))]
    klein = [t for _s, t in _tranchen(e34_signale(cs, fl, ampel_filter="klein"))]
    gross = [t for _s, t in _tranchen(e34_signale(cs, fl, ampel_filter="gross"))]
    assert voll and klein == voll, "bei guenstiger Lage darf 'klein' nicht halbieren"
    assert gross == [max(1, int(t * AMPEL_TRANCHE)) for t in voll]


def test_ampel_filter_haelt_still_wenn_die_ampel_schweigt():
    """Sagt die Ampel nichts, aendert 'klein' und 'gross' nichts - 'immer' schon.

    Das trennt die Nullhypothese sauber von der Ampel: 'immer' darf an keiner
    Ampel-Aussage haengen.
    """
    cs, fl = e13_szenario(spot_faellt=False)
    assert ampel(lage_bericht(cs, fl, pattern=classify_pattern(cs, fl),
                              trend_period=200)) is None
    voll = [t for _s, t in _tranchen(e34_signale(cs, fl))]
    assert voll, "ohne Einstiege prueft dieser Test nichts"
    for modus in ("klein", "gross"):
        assert [t for _s, t in _tranchen(e34_signale(cs, fl, ampel_filter=modus))] == voll
    immer = [t for _s, t in _tranchen(e34_signale(cs, fl, ampel_filter="immer"))]
    assert immer == [max(1, int(t * AMPEL_TRANCHE)) for t in voll]


def test_ampel_vergleicht_nicht_das_bein_mit_sich_selbst():
    """Bei einem frischen Einstieg gibt es noch kein Vergleichsbein.

    Ohne den Merker _pos_imp_vorher wuerde evaluate() die Lage NACH dem Einstieg
    bewerten: pos.zones ist dann bereits aus genau dem Bein gesetzt, auf das gerade
    eingestiegen wurde - "Struktur unveraendert", ein geschenktes Argument dafuer, das
    keine Information enthaelt. Gefunden, weil ein Gegenproben-Test unerwartet ansprang.
    """
    cs, fl = e13_szenario(spot_faellt=False)      # am Einstieg sagt nur der Spot etwas
    lg = lage_bericht(cs, fl, pattern=classify_pattern(cs, fl), trend_period=200)
    assert "struktur" not in lg and ampel(lg) is None, "Szenario passt nicht mehr"
    voll = [t for _s, t in _tranchen(e34_signale(cs, fl))]
    # eine einzige Aussage reicht der Ampel nicht -> niemand darf hier halbieren
    assert [t for _s, t in _tranchen(e34_signale(cs, fl, ampel_filter="klein"))] == voll
    assert [t for _s, t in _tranchen(e34_signale(cs, fl, ampel_filter="gross"))] == voll


# ------------------------------------------------- E35: Richtung der Ampel

def test_ampel_richtung_folgt_dem_bias_nicht_dem_bein():
    """Der Fehler vom 17.09.2026 in Reinform.

    Live steht bias_short=false - die Engine ist reine Long-Engine. Findet sie ein
    ABWAERTS-Bein (bei bein_richtung="auto" der Normalfall), darf die Ampel trotzdem
    NICHT fuer einen Short rechnen: diesen Short wuerde die Engine nie eingehen.
    """
    # nur Long erlaubt -> immer Long, egal welches Bein
    assert ampel_richtung(True, False, bein_auf=False) is True
    assert ampel_richtung(True, False, bein_auf=True) is True
    # nur Short erlaubt -> immer Short
    assert ampel_richtung(False, True, bein_auf=True) is False
    assert ampel_richtung(False, True, bein_auf=False) is False
    # beide erlaubt -> das Bein entscheidet
    assert ampel_richtung(True, True, bein_auf=True) is True
    assert ampel_richtung(True, True, bein_auf=False) is False
    # kein Bein bekannt -> Long, die Grundeinstellung des Projekts
    assert ampel_richtung(True, True, bein_auf=None) is True


def test_ampel_nennt_die_richtung_im_ergebnis():
    """Wer die Ampel liest, muss sehen, wofuer sie gilt."""
    lage = {"trend": "ueber", "spot": "stabil"}
    assert ampel(lage, long_side=True)["richtung"] == "LONG"
    assert ampel(lage, long_side=False)["richtung"] == "SHORT"


def test_ampel_dreht_sich_mit_der_richtung_echter_livestand():
    """Die echten Zahlen vom 17.09.2026, 13:41 UTC (state.json).

    Kurs 76.482 ueber EMA200 (70.184), Spot-Nachfrage stabil, Bein 79.600 -> 74.968
    (abwaerts). In der Nachricht stand UNGUENSTIG - gerechnet fuer einen Short. Fuer
    Kaisers Long-Position ergeben dieselben Daten das genaue Gegenteil.
    """
    lage = {"trend": "ueber", "struktur": "neu", "spot": "stabil"}
    kurz = ampel(lage, long_side=False)
    lang = ampel(lage, long_side=True)
    assert kurz["stufe"] == "unguenstig" and kurz["dafuer"] == []
    assert lang["stufe"] == "guenstig" and lang["dagegen"] == []
    assert sorted(lang["dafuer"]) == sorted(kurz["dagegen"])   # exakt gespiegelt


# ------------------------------------------------- E36: Furkans Rohwerte

def _of_serie(n=40, fut=True, liq=True, lp=54.0, seed=3):
    """Kerzen + Flow mit allen sieben Groessen. fut/liq/lp abschaltbar, um die
    Behandlung fehlender Daten zu pruefen."""
    import random
    r = random.Random(seed)
    cs, fl = [], []
    cvd_s, cvd_f, oi, v = 5000.0, 1000.0, 1e9, 76000.0
    for i in range(n):
        v *= (1 + r.gauss(0.001, 0.01))
        cs.append(Candle(1_700_000_000_000 + i * H4_MS, v, v * 1.004, v * 0.996, v))
        cvd_s += r.gauss(4e6, 2e6)
        cvd_f = cvd_f + r.gauss(1e6, 3e6) if fut else 0.0
        oi *= (1 + r.gauss(0, 0.008))
        fl.append(FlowPoint(cs[-1].ts, cvd_s, cvd_f, oi, r.gauss(0.0001, 0.0002),
                            long_liq=abs(r.gauss(2e6, 1e6)) if liq else 0.0,
                            short_liq=abs(r.gauss(1e6, 5e5)) if liq else 0.0,
                            long_pct=lp))
    return cs, fl


def test_orderflow_detail_zeigt_furkans_sieben_groessen():
    """Alle Groessen aus dem Video (Transkript 8:05-11:26), plus der Preis - Furkans
    Regeln lauten immer "Preis X UND Open Interest Y"."""
    cs, fl = _of_serie()
    namen = [z["name"] for z in orderflow_detail(cs, fl)]
    for erwartet in ("Preis", "Spot-CVD", "Futures-CVD", "Open Interest", "Funding",
                     "Long-Liquidationen", "Short-Liquidationen", "Positionierung"):
        assert erwartet in namen, f"{erwartet} fehlt: {namen}"


def test_orderflow_detail_zeigt_fehlende_daten_nicht_als_null():
    """Ohne Coinalyze-Schluessel bleiben Futures-CVD und Positionierung bei 0.

    Eine Zeile "Futures-CVD 0 $ - flach" waere FALSCH: Sie behauptet Stillstand, wo
    in Wahrheit nichts bekannt ist. Solche Groessen fehlen ganz.
    """
    cs, fl = _of_serie(fut=False, liq=False, lp=0.0)
    namen = [z["name"] for z in orderflow_detail(cs, fl)]
    assert "Futures-CVD" not in namen, "Futures-CVD ohne Daten als 0 gezeigt"
    assert "Positionierung" not in namen
    assert "Long-Liquidationen" not in namen
    # ... die Groessen MIT Daten bleiben aber stehen
    assert "Spot-CVD" in namen and "Preis" in namen and "Open Interest" in namen


def test_orderflow_detail_nutzt_dasselbe_fenster_wie_das_muster():
    """Die Rohwerte sollen ERKLAEREN, warum das Muster so lautet. Ein anderes Fenster
    zeigte Zahlen, die zur Schlussfolgerung darunter nicht passen."""
    import inspect
    from strategy_core import OF_FENSTER, classify_pattern
    muster_fenster = inspect.signature(classify_pattern).parameters["window"].default
    assert OF_FENSTER == muster_fenster == 12


def test_orderflow_richtung_kennt_flach():
    """Furkans wichtigste Unterscheidung: steigt / faellt / FLACH (Transkript 9:06:
    'Spot CVD steigt und Future CVD ist hier flach ... das ist gesund').

    ENTSCHEIDEND ist der Fall "kleine, aber nicht null" Aenderung - nur dort greift die
    Schwellenregel. Die erste Fassung dieses Tests nutzte eine Reihe mit Aenderung
    GENAU 0; da trifft der triviale Zweig am Funktionsende, und die Sabotage
    "'flach' verschwindet" ueberlebte unbemerkt. Derselbe Fehlertyp wie bei E34 und
    E35 - ein Test, der richtig aussieht und die Regel nicht beruehrt.
    """
    from strategy_core import _of_reihe, _median, OF_FLACH_ANTEIL
    stark = [float(i) * 100 for i in range(40)]      # +1200 je Fenster
    assert _of_reihe(stark, 12)["richtung"] == "steigt"

    # letzte 12 Schritte: +10 statt +100 -> Aenderung 120, Schwelle 1200/3 = 400
    kaum = stark[:28] + [stark[27] + 10.0 * (i + 1) for i in range(12)]
    r = _of_reihe(kaum, 12)
    assert r["aenderung"] > 0, "Szenario passt nicht - die Aenderung muss > 0 sein"
    massstab = _median([abs(kaum[i] - kaum[i - 12])
                        for i in range(12, len(kaum) - 12)])
    assert 0 < r["aenderung"] < massstab * OF_FLACH_ANTEIL, "Szenario trifft die Regel nicht"
    assert r["richtung"] == "flach", "kleine Bewegung wurde nicht als flach erkannt"

    # fallend
    fallend = [float(-i) * 100 for i in range(40)]
    assert _of_reihe(fallend, 12)["richtung"] == "faellt"
    # Stillstand bei exakt 0 Aenderung ist ebenfalls flach (trivialer Zweig)
    assert _of_reihe(stark[:28] + [stark[27]] * 12, 12)["richtung"] == "flach"
    # durchgehend 0 heisst KEINE DATEN, nicht "flach"
    assert _of_reihe([0.0] * 40, 12) is None


def test_orderflow_detail_ist_reine_anzeige():
    """Die Engine darf diese Funktion nicht aufrufen - sonst waere sie eine Regel."""
    import inspect
    from strategy_core import evaluate
    quelle = inspect.getsource(evaluate)
    assert "orderflow_detail" not in quelle


# ------------------------------------------ E38: Muster 5 als Treibstoff (20.09.2026)

from strategy_core import muster5_haelt_zurueck as _m5halt


def test_muster5_halten_ist_im_default_aus_immer_wirkungslos():
    """Ein Schalter, der auch ausgeschaltet wirkt, macht jede Vergleichszeile wertlos."""
    for pat in Pattern:
        for richtung in ("LONG", "SHORT", "NONE"):
            for ziel in (True, False):
                assert _m5halt("off", pat, richtung, ziel) is False


def test_muster5_halten_greift_nur_bei_muster_5():
    for pat in Pattern:
        erwartet = pat == Pattern.UNGESUNDER_ABVERKAUF
        assert _m5halt("leiter", pat, "LONG", False) is erwartet


def test_muster5_halten_greift_nicht_beim_short():
    """Beim Short ist Liquiditaet oberhalb ein Grund, EHER zu decken — die
    Treibstoff-Lesart wirkt fuer den Short in die Gegenrichtung."""
    assert _m5halt("leiter", Pattern.UNGESUNDER_ABVERKAUF, "SHORT", False) is False
    assert _m5halt("alle", Pattern.UNGESUNDER_ABVERKAUF, "SHORT", True) is False
    assert _m5halt("leiter", Pattern.UNGESUNDER_ABVERKAUF, "LONG", False) is True


def test_muster5_halten_leiter_laesst_die_geplanten_ziele_durch():
    """'leiter' haelt die Zwischenverkaeufe zurueck, nicht den Plan. Furkan verkauft
    nicht NIE — er verkauft gerade jetzt nicht."""
    m5 = Pattern.UNGESUNDER_ABVERKAUF
    assert _m5halt("leiter", m5, "LONG", ziel=False) is True     # Leiter: zurueckhalten
    assert _m5halt("leiter", m5, "LONG", ziel=True) is False     # 1.0/1.618: durchlassen


def test_muster5_halten_alle_haelt_auch_die_ziele():
    m5 = Pattern.UNGESUNDER_ABVERKAUF
    assert _m5halt("alle", m5, "LONG", ziel=False) is True
    assert _m5halt("alle", m5, "LONG", ziel=True) is True


def test_muster5_halten_unterscheidet_leiter_und_alle_wirklich():
    """Gegen den stillsten Fehler: zwei Gittervarianten, die dasselbe tun. Dann
    sieht man zwei Zeilen und haelt sie fuer eine Bestaetigung."""
    m5 = Pattern.UNGESUNDER_ABVERKAUF
    assert _m5halt("leiter", m5, "LONG", True) != _m5halt("alle", m5, "LONG", True)


def _m5_lage():
    """Ein Szenario, in dem Muster 5 gilt UND die Engine wirklich handelt.

    Der Trick ist der hohe DOCHT auf zwei Kerzen: Das 12-Kerzen-Fenster von
    classify_pattern sieht weiter einen Rueckgang (Muster 5 bleibt stehen), aber
    cur.high erreicht die Leiter-Extensions. Ohne ihn erzeugt ein Muster-5-Szenario
    gar keine Teilverkaeufe — fallender Preis und faellige Gewinnmitnahme schliessen
    sich sonst aus.

    Erzeugt (Stand 20.09.2026): KAUF_1, zweimal TEILVERKAUF_LADDER und einmal
    TEILVERKAUF_1 — also Einstieg, Zwischenverkauf UND geplantes Ziel, alle bei
    Muster 5. Genau die drei Faelle, die E38.2 und E38.3 auseinanderhalten muessen.
    """
    ms = 4 * 3600 * 1000
    preise = ([100.0] * 8 + [100.0 + 50.0 * (i + 1) / 22 for i in range(22)]
              + [150.0 - 38.0 * (i + 1) / 26 for i in range(26)] + [112.0] * 6)
    cs, fl = [], []
    for i, pr in enumerate(preise):
        hi = pr * 1.5 if i in (50, 52) else pr * 1.004
        cs.append(Candle(1_600_000_000_000 + i * ms, pr, hi, pr * 0.996, pr))
        cvd = 1000.0 + i * 30.0 if i < 30 else 1000.0 + 900.0 - (i - 30) * 90.0
        fl.append(FlowPoint(cs[-1].ts, cvd, 0.0, 1e9, 0.00005, 0.0, 0.0, 50.0))
    return cs, fl


def _signale(cs, fl, **kw):
    pos = Position()
    raus = []
    for i in range(len(cs)):
        raus += [(cs[i].ts, s) for s in evaluate(cs[:i + 1], fl[:i + 1], pos,
                                                 bias_short=False, high_exit="on", **kw)]
    return raus


def test_m5_szenario_handelt_ueberhaupt_und_zwar_bei_muster_5():
    """DIE Vorprobe. Ohne sie vergleichen die Tests darunter zwei leere Listen und
    sind gruen, egal was der Code tut — derselbe Fehlertyp wie in E34, und mir ist er
    beim Bauen von E38 genau einmal passiert: Die erste Fassung dieses Szenarios
    erzeugte NULL Signale, und drei Tests bestaetigten froehlich gar nichts.
    """
    cs, fl = _m5_lage()
    sigs = _signale(cs, fl)
    assert len(sigs) >= 3, f"Szenario handelt kaum: {[s.type.name for _, s in sigs]}"
    typen = {s.type for _, s in sigs}
    assert SignalType.TEILVERKAUF_LADDER in typen, "kein Zwischenverkauf im Szenario"
    assert SignalType.TEILVERKAUF_1 in typen, "kein geplantes Ziel im Szenario"
    # ... und all das muss bei Muster 5 passieren, sonst prueft E38 nichts.
    ts_m5 = {cs[i].ts for i in range(len(cs))
             if classify_pattern(cs[:i + 1], fl[:i + 1]) == Pattern.UNGESUNDER_ABVERKAUF}
    assert all(t in ts_m5 for t, _ in sigs), "Signale fallen nicht in die Muster-5-Phase"


def test_muster5_schalter_im_default_aendern_kein_einziges_signal():
    """Die Grundbedingung jeder Gitterzeile: ausgeschaltet = heutiges Verhalten."""
    cs, fl = _m5_lage()
    fass = lambda sg: [(t, s.type, round(s.price, 6), s.tranche_pct) for t, s in sg]
    basis = fass(_signale(cs, fl))
    assert basis, "leere Basis — der Vergleich wuerde nichts pruefen"
    for kw in ({"muster5_entry": False}, {"muster5_halten": "off"},
               {"muster5_entry": False, "muster5_halten": "off"}):
        assert fass(_signale(cs, fl, **kw)) == basis, kw


def test_muster5_halten_leiter_entfernt_den_zwischenverkauf_nicht_das_ziel():
    cs, fl = _m5_lage()
    ohne = [s.type for _, s in _signale(cs, fl)]
    mit = [s.type for _, s in _signale(cs, fl, muster5_halten="leiter")]
    assert SignalType.TEILVERKAUF_LADDER in ohne
    assert SignalType.TEILVERKAUF_LADDER not in mit, "Zwischenverkauf nicht zurueckgehalten"
    assert SignalType.TEILVERKAUF_1 in mit, "das geplante Ziel darf 'leiter' nicht sperren"


def test_muster5_halten_alle_entfernt_auch_das_ziel():
    cs, fl = _m5_lage()
    mit = [s.type for _, s in _signale(cs, fl, muster5_halten="alle")]
    assert SignalType.TEILVERKAUF_LADDER not in mit
    assert SignalType.TEILVERKAUF_1 not in mit


def test_muster5_halten_verbraucht_keine_leiterstufe_beim_zurueckhalten():
    """Der stillste denkbare Fehler: Das Signal wird unterdrueckt, aber tp_rungs zaehlt
    hoch — die Leiterstufe gilt als verkauft, ohne dass verkauft wurde. Genau deshalb
    sitzt E38.3 VOR dem Erzeugen des Signals und nicht im Aufraeumen danach."""
    cs, fl = _m5_lage()
    for modus, erwartet_rungs in (("off", True), ("alle", False)):
        pos = Position()
        for i in range(len(cs)):
            evaluate(cs[:i + 1], fl[:i + 1], pos, bias_short=False, high_exit="on",
                     muster5_halten=modus)
        assert (pos.tp_rungs > 0) is erwartet_rungs, (modus, pos.tp_rungs)


def _m5_absturz():
    """Wie _m5_lage, aber OHNE Docht und mit einem Einbruch am Ende.

    Ohne Docht gibt es keine Teilverkaeufe — die Position steht in allen drei Modi im
    selben Zustand, wenn der Kurs unter die Invalidierung faellt. Nur so laesst sich
    der Stop ueberhaupt sauber vergleichen."""
    ms = 4 * 3600 * 1000
    preise = ([100.0] * 8 + [100.0 + 50.0 * (i + 1) / 22 for i in range(22)]
              + [150.0 - 38.0 * (i + 1) / 26 for i in range(26)]
              + [112.0 - 14.0 * (i + 1) for i in range(6)])     # Absturz unter alles
    cs, fl = [], []
    for i, pr in enumerate(preise):
        pr = max(pr, 1.0)
        cs.append(Candle(1_600_000_000_000 + i * ms, pr, pr * 1.004, pr * 0.996, pr))
        cvd = 1000.0 + i * 30.0 if i < 30 else 1000.0 + 900.0 - (i - 30) * 90.0
        fl.append(FlowPoint(cs[-1].ts, cvd, 0.0, 1e9, 0.00005, 0.0, 0.0, 50.0))
    return cs, fl


def test_muster5_halten_unterdrueckt_niemals_den_stop():
    """Der gefaehrlichste denkbare Fehler dieses Ausbaus: Die Position bleibt im
    fallenden Markt liegen, weil ein Muster gerade 'halten' sagt.

    Geprueft bei GLEICHEM Positionszustand (Szenario ohne Teilverkaeufe) — sonst
    vergleicht man zwei verschiedene Positionen und nicht den Schalter."""
    cs, fl = _m5_absturz()
    def _stops(modus):
        return [s.type for _, s in _signale(cs, fl, muster5_halten=modus)
                if s.type in (SignalType.STOPLOSS, SignalType.VERKAUF_REST)]
    assert _stops("off"), "Szenario loest gar keinen Stop aus — der Test pruefte nichts"
    for modus in ("leiter", "alle"):
        assert _stops(modus) == _stops("off"), modus


def test_stop_zweige_fragen_den_teilverkauf_waechter_gar_nicht_erst():
    """Strukturell abgesichert: STOPLOSS und VERKAUF_REST stehen nicht in
    _TEILVERKAUF_TYPES und laufen an _darf_teilverkaufen() vorbei. Waere das je
    anders, koennte muster5_halten einen vollstaendigen Ausstieg verhindern."""
    from strategy_core import _TEILVERKAUF_TYPES
    for t in (SignalType.STOPLOSS, SignalType.VERKAUF_REST,
              SignalType.SHORT_STOPLOSS, SignalType.SHORT_COVER_REST):
        assert t not in _TEILVERKAUF_TYPES, t


def test_muster5_halten_alle_verhindert_den_stop_nachzug_BEKANNTE_FOLGE():
    """Kein Fehler, sondern eine Eigenschaft — und der Grund, warum "alle" riskanter
    ist als "leiter": Ohne realisierten Teilgewinn zieht trail_stop den Stop nicht
    nach. Die Position laeuft mit dem urspruenglichen, weiter entfernten Stop weiter.

    Dieser Test haelt die Folge fest, damit sie beim Auswerten der Gitterzeilen nicht
    als ueberraschend gute Rendite missverstanden wird: "alle" traegt mehr Risiko, und
    zwar an einer Stelle, die die Renditespalte allein nicht zeigt."""
    cs, fl = _m5_lage()
    typen = lambda m: [s.type for _, s in _signale(cs, fl, muster5_halten=m,
                                                   trail_stop=True)]
    assert SignalType.TEILVERKAUF_1 in typen("off")
    assert SignalType.TEILVERKAUF_1 not in typen("alle")
    assert SignalType.STOPLOSS in typen("off")
    assert SignalType.STOPLOSS not in typen("alle")   # weil der Stop nicht nachgezogen wurde


def test_muster5_entry_macht_muster_5_zur_starken_bestaetigung():
    """E38.2 baut die Vorlage von Muster 4 nach: confirm_ok() (einzige Rechenstelle,
    E43.6) erhaelt eine zweite starke Bestaetigung. Kein eigener Trigger — der Einstieg
    bleibt an die Fib-Zone gebunden, sonst kaufte die Engine im Nichts."""
    import inspect
    from strategy_core import confirm_ok
    quelle = inspect.getsource(confirm_ok)
    assert "muster5_entry and pattern == Pattern.UNGESUNDER_ABVERKAUF" in quelle
    assert "strong = pattern == Pattern.CAPITULATION_RESET or (" in quelle


def test_muster5_entry_erzeugt_nie_mehr_einstiege_als_ohne_fib_zone_moeglich():
    """Gegenprobe zur Sorge 'die Engine kauft im Nichts': muster5_entry darf nur
    Einstiege BESTAETIGEN, die die Zonenlogik ohnehin anbietet. Die Zahl der
    Einstiege darf also hoechstens steigen, und jeder muss einen Stop-Bezug haben."""
    cs, fl = _m5_lage()
    _EINSTIEGE = {SignalType.KAUF_1, SignalType.KAUF_2, SignalType.NACHKAUF}
    mit = [s for _, s in _signale(cs, fl, muster5_entry=True) if s.type in _EINSTIEGE]
    for s in mit:
        assert s.stop_ref is not None, f"Einstieg ohne Stop-Bezug: {s.type}"


def test_muster5_halten_behandelt_beide_ziele_gleich():
    """Das 1.618-Ziel darf nicht anders eingestuft sein als das 1.0-Ziel.

    Warum als Quelltext-Pruefung: Ein Szenario, das bis TP2 laeuft, braucht einen
    zweiten Aufwaertsschub NACH dem ersten Teilgewinn, waehrend das 12-Kerzen-Fenster
    weiter Muster 5 zeigt — konstruierbar, aber so fragil, dass der Test bei jeder
    Schwellenaenderung still durchfallen wuerde, ohne dass jemand es merkt. Die
    Einstufung selbst ist eine strukturelle Aussage, also wird sie strukturell geprueft.
    """
    import inspect
    quelle = inspect.getsource(evaluate)
    assert quelle.count("_darf_teilverkaufen(ziel=True)") == 2, (
        "Genau zwei Stellen sind geplante Ziele (Extension 1.0 und 1.618) — "
        "alles andere sind Zwischenverkaeufe")
    assert "if pos.state == PosState.TP1 and _darf_teilverkaufen(ziel=True):" in quelle


# ------------------------------- E38: Muster 5 in Lage-Abruf und Ampel (21.09.2026)

def test_ampel_zaehlt_muster_5_fuer_keine_seite():
    """Kaisers Wahl: neutral. Die Messung widerspricht 'dagegen', aber Kursverlauf ist
    nicht Ertrag - deshalb auch nicht 'dafuer'. Neutral heisst: auch fuer einen Short
    zaehlt es nicht (die Spiegelung darf es nicht durch die Hintertuer zu 'dafuer'
    machen)."""
    from strategy_core import _AMPEL_DAFUER, _AMPEL_DAGEGEN
    assert "UNGESUNDER_ABVERKAUF" not in _AMPEL_DAFUER["muster"]
    assert "UNGESUNDER_ABVERKAUF" not in _AMPEL_DAGEGEN["muster"]
    lage = {"trend": "ueber", "spot": "stabil", "muster": "UNGESUNDER_ABVERKAUF"}
    for seite in (True, False):
        a = ampel(lage, long_side=seite)
        assert "Muster" not in a["dafuer"] and "Muster" not in a["dagegen"], seite


def test_ampel_behaelt_die_uebrigen_muster_wie_bisher():
    """Nur Muster 5 wurde gemessen und umgestellt - die anderen bleiben, wo sie waren."""
    from strategy_core import _AMPEL_DAFUER, _AMPEL_DAGEGEN
    assert _AMPEL_DAFUER["muster"] == {"GESUNDER_TREND", "CAPITULATION_RESET"}
    assert _AMPEL_DAGEGEN["muster"] == {"DERIVATE_PUMP", "SHORT_COVERING"}


def test_muster_hinweis_nur_wo_gemessen_und_ohne_namen():
    """Ein Hinweis nur fuer Muster 5 - fuer die anderen gibt es keine Messung, also
    auch keinen Satz. Und kein Name im Text (Kaiser, 21.09.2026)."""
    from strategy_core import MUSTER_HINWEIS
    assert set(MUSTER_HINWEIS) == {"UNGESUNDER_ABVERKAUF"}
    for text in list(MUSTER_HINWEIS.values()) + list(MUSTER_KLARTEXT.values()):
        assert "furkan" not in text.lower(), text


def test_muster_hinweis_nennt_den_zeitraum_der_messung_fest():
    """'Seit Januar' wuerde in einem Jahr etwas behaupten, das niemand geprueft hat.
    Die Messung ist eine Momentaufnahme - der Zeitraum steht deshalb fest im Text."""
    from strategy_core import MUSTER_HINWEIS
    h = MUSTER_HINWEIS["UNGESUNDER_ABVERKAUF"]
    assert "2026" in h and "nicht immer" in h
    assert "seit" not in h.lower()


def test_lage_ohne_muster_5_hat_keinen_hinweis():
    f = _flow_cvd([0, 10, 20, 30, 40, 50, 60])
    for m in Pattern:
        l = lage_bericht([], f, pattern=m)
        if m == Pattern.UNGESUNDER_ABVERKAUF:
            assert "muster_hinweis" in l
        else:
            assert "muster_hinweis" not in l, m


# ------------------------------------ E41: Stop mit Puffer / Rueckeroberung / Docht

from strategy_core import stop_entscheidung, DIP_FLOOR_PCT, _reset_position

_INV = 100.0


def _k(close, low=None, high=None, open_=None):
    o = close if open_ is None else open_
    return Candle(1, o, high if high is not None else max(o, close),
                  low if low is not None else min(o, close), close)


def test_stop_puffer_ignoriert_knappe_schluesse():
    pos = Position()
    hit, _, _ = stop_entscheidung(pos, _k(99.7), _INV, True, puffer_pct=0.005)
    assert hit is False                                  # 0,3 % darunter: kein Stop
    hit, preis, grund = stop_entscheidung(pos, _k(99.4), _INV, True, puffer_pct=0.005)
    assert hit is True and preis == 99.4 and "Puffer" in grund


def test_rueckeroberung_1_stoppt_bei_zweitem_schluss_darunter():
    pos = Position()
    assert stop_entscheidung(pos, _k(99.7), _INV, True, rueckeroberung=1)[0] is False
    assert pos.stop_wartet == 1
    hit, _, grund = stop_entscheidung(pos, _k(99.5), _INV, True, rueckeroberung=1)
    assert hit is True and "nicht zurueckerobert" in grund


def test_rueckeroberung_3_gibt_drei_kerzen_zeit():
    pos = Position()
    for _ in range(3):
        assert stop_entscheidung(pos, _k(99.6), _INV, True, rueckeroberung=3)[0] is False
    assert stop_entscheidung(pos, _k(99.6), _INV, True, rueckeroberung=3)[0] is True


def test_rueckeroberung_macht_die_marke_geprueft_und_der_naechste_bruch_stoppt_sofort():
    """Kaisers Regel im Kern: Die Schonfrist gibt es genau EINMAL. Ist die Marke einmal
    unterschritten und zurueckerobert, ist der naechste Schluss darunter echt."""
    pos = Position()
    assert stop_entscheidung(pos, _k(99.7), _INV, True, rueckeroberung=3)[0] is False
    assert stop_entscheidung(pos, _k(100.5), _INV, True, rueckeroberung=3)[0] is False
    assert pos.stop_geprueft == _INV and pos.stop_wartet == 0
    hit, _, grund = stop_entscheidung(pos, _k(99.8), _INV, True, rueckeroberung=3)
    assert hit is True and "schon einmal" in grund       # trotz 3 Kerzen Zeit: sofort


def test_ohne_vorheriges_unterschreiten_ist_die_marke_nicht_geprueft():
    pos = Position()
    stop_entscheidung(pos, _k(105.0), _INV, True, rueckeroberung=1)
    assert pos.stop_geprueft is None


def test_rueckeroberung_harter_boden_stoppt_sofort():
    """Ein Schluss mehr als 5 % darunter ist kein Stich, sondern ein Bruch."""
    pos = Position()
    tief = _INV * (1 - DIP_FLOOR_PCT) - 0.1
    hit, _, grund = stop_entscheidung(pos, _k(tief), _INV, True, rueckeroberung=3)
    assert hit is True and "harter" in grund


def test_rueckeroberung_neue_marke_zaehlt_neu():
    """Werden die Zonen nachgezogen, gehoert das Warten zur alten Marke."""
    pos = Position()
    stop_entscheidung(pos, _k(99.7), _INV, True, rueckeroberung=1)
    assert stop_entscheidung(pos, _k(100.7), 101.0, True, rueckeroberung=1)[0] is False
    assert pos.stop_wartet == 1 and pos.stop_wartet_inv == 101.0


def test_rueckeroberung_gilt_fuer_short_spiegelbildlich():
    pos = Position()
    assert stop_entscheidung(pos, _k(100.3), _INV, False, rueckeroberung=1)[0] is False
    assert stop_entscheidung(pos, _k(99.5), _INV, False, rueckeroberung=1)[0] is False
    assert pos.stop_geprueft == _INV
    assert stop_entscheidung(pos, _k(100.2), _INV, False, rueckeroberung=1)[0] is True


def test_docht_stoppt_schon_beim_kerzentief_zum_stopkurs():
    pos = Position()
    hit, preis, grund = stop_entscheidung(pos, _k(101.0, low=99.0, open_=102.0), _INV, True,
                                          auf_docht=True)
    assert hit is True and preis == _INV and "Docht" in grund
    hit, preis, _ = stop_entscheidung(pos, _k(97.0, low=96.0, open_=98.0), _INV, True,
                                      auf_docht=True)
    assert preis == 98.0                                 # Luecke: zum Eroeffnungskurs
    assert stop_entscheidung(pos, _k(101.0, low=100.1), _INV, True, auf_docht=True)[0] is False


def test_reset_raeumt_die_e41_merker_ab():
    """Die Lehre aus E18: Zaehler, die einen Stop ueberleben, schalten spaeter still
    etwas ab oder an."""
    pos = Position()
    pos.stop_wartet, pos.stop_wartet_inv, pos.stop_geprueft = 2, 100.0, 100.0
    _reset_position(pos)
    assert (pos.stop_wartet, pos.stop_wartet_inv, pos.stop_geprueft) == (0, None, None)


# --- durch evaluate(): das Szenario muss wirklich einen knappen Stop erzeugen -------

def _e41_szenario(schluesse):
    """e13_szenario (KAUF_1 an der 0.5, Invalidierung 97,608), danach frei waehlbare
    Schlusskurse - Hoch/Tief 0,1 % um Eroeffnung und Schluss."""
    cs, fl = e13_szenario()
    cs, fl = list(cs), list(fl)
    for v in schluesse:
        ts, o = cs[-1].ts + H4_MS, cs[-1].close
        cs.append(Candle(ts, o, max(o, v) * 1.001, min(o, v) * 0.999, v))
        f = fl[-1]
        fl.append(FlowPoint(ts, f.spot_cvd - 30, 0.0, f.oi + 1e6, f.funding))
    return cs, fl


def _e41_lauf(cs, fl, **kw):
    pos = Position()
    out = []
    for i in range(len(cs)):
        out += [(i, s) for s in evaluate(cs[:i + 1], fl[:i + 1], pos, bias_short=False,
                                         pivot_n=2, **kw)]
    return out, pos


_KNAPP_ZURUECK_WIEDER = [110, 106, 102, 99, 97.4, 98.5, 100, 99, 97.3, 96, 95]


def test_e41_szenario_hat_einen_knappen_live_stop():
    """DIE Vorprobe: ohne knappen Stop pruefen die Tests darunter nichts."""
    cs, fl = _e41_szenario(_KNAPP_ZURUECK_WIEDER)
    stops = [(i, s) for i, s in _e41_lauf(cs, fl)[0] if s.type == SignalType.STOPLOSS]
    assert len(stops) == 1
    assert 0 < (97.608 - stops[0][1].price) / 97.608 < 0.005   # weniger als 0,5 % darunter


def test_e41_im_default_aus_exakt_dieselben_signale():
    cs, fl = _e41_szenario(_KNAPP_ZURUECK_WIEDER)
    fass = lambda o: [(i, s.type, round(s.price, 6), s.tranche_pct, s.reason) for i, s in o]
    basis = fass(_e41_lauf(cs, fl)[0])
    assert basis
    assert fass(_e41_lauf(cs, fl, stop_puffer_pct=0.0, stop_rueckeroberung=0,
                          stop_auf_docht=False)[0]) == basis


def test_e41_rueckeroberung_ueberlebt_den_stich_und_stoppt_beim_zweiten_bruch():
    cs, fl = _e41_szenario(_KNAPP_ZURUECK_WIEDER)
    live = [i for i, s in _e41_lauf(cs, fl)[0] if s.type == SignalType.STOPLOSS]
    b1 = [(i, s) for i, s in _e41_lauf(cs, fl, stop_rueckeroberung=1)[0]
          if s.type == SignalType.STOPLOSS]
    assert len(b1) == 1 and b1[0][0] > live[0]
    assert "schon einmal" in b1[0][1].reason


def test_e41_position_bleibt_bei_langsamem_abverkauf_nicht_haengen():
    """Die gefaehrlichste Folge einer Schonfrist: jede Kerze schliesst nur ein wenig
    tiefer, keine zurueck - dann muss der Stop trotzdem kommen."""
    cs, fl = _e41_szenario([110, 106, 102, 99, 97.5, 97.4, 97.3, 97.2, 97.1, 97.0, 96.9])
    for n in (1, 3):
        stops = [i for i, s in _e41_lauf(cs, fl, stop_rueckeroberung=n)[0]
                 if s.type == SignalType.STOPLOSS]
        assert stops, f"Position haengt bei stop_rueckeroberung={n}"


def test_e41_kein_nachkauf_waehrend_des_wartens_und_der_rueckeroberung():
    """Ohne Sperre kaeme in der Wartekerze der 0.786-Nachkauf - ein Nachkauf unter der
    Invalidierung, also der durchgefallene conditional_stop durch die Hintertuer."""
    cs, fl = _e41_szenario([110, 97.4, 100, 101])
    sig, _pos = _e41_lauf(cs, fl, stop_rueckeroberung=1)
    warte, zurueck = 27, 28
    assert not [s for i, s in sig if i in (warte, zurueck) and s.type in (
        SignalType.NACHKAUF, SignalType.KAUF_2)]
    assert any(s.type == SignalType.STOPLOSS for i, s in _e41_lauf(cs, fl)[0] if i == warte)


def test_e41_nachkauf_nach_rueckeroberung_zum_erreichbaren_preis():
    """Nach der Rueckeroberung kommt der Kurs von unten an die 0.786-Zone. Gebucht wird
    der Eroeffnungskurs, nicht der teurere Levelpreis."""
    cs, fl = _e41_szenario([110, 97.4, 100, 101])
    sig, _ = _e41_lauf(cs, fl, stop_rueckeroberung=1)
    nk = [(i, s) for i, s in sig if s.type == SignalType.NACHKAUF]
    assert nk, "Szenario erzeugt keinen Nachkauf nach der Rueckeroberung"
    i, s = nk[0]
    assert s.price == cs[i].open and s.price < 104.0


def test_e41_laesst_den_nachgezogenen_stop_unberuehrt():
    cs, fl = _m5_lage()
    def _stop(**kw):
        return [(t, s.price, s.reason) for t, s in _signale(cs, fl, trail_stop=True, **kw)
                if s.type == SignalType.STOPLOSS]
    basis = _stop()
    assert basis and basis[0][2].startswith("Nachgezogener"), "Vorprobe: kein nachgezogener Stop"
    for kw in ({"stop_puffer_pct": 0.005}, {"stop_rueckeroberung": 1},
               {"stop_rueckeroberung": 3}, {"stop_auf_docht": True}):
        assert _stop(**kw) == basis, kw


def test_e41_docht_stoppt_frueher_als_live():
    cs, fl = _e41_szenario(_KNAPP_ZURUECK_WIEDER)
    live = [i for i, s in _e41_lauf(cs, fl)[0] if s.type == SignalType.STOPLOSS]
    doc = [(i, s) for i, s in _e41_lauf(cs, fl, stop_auf_docht=True)[0]
           if s.type == SignalType.STOPLOSS]
    assert doc and doc[0][0] <= live[0]
    assert abs(doc[0][1].price - 97.608) < 1e-6 or doc[0][1].price == cs[doc[0][0]].open


def test_e41_preiskorrektur_aendert_ohne_e41_nichts():
    """Die Live-Zahlen duerfen sich durch E41 nicht bewegen. Oeffnet eine Kerze schon
    unter der 0.786-Zone, bucht die Engine heute zum Levelpreis - und dabei bleibt es,
    solange E41 aus ist."""
    cs, fl = e13_szenario()
    cs, fl = list(cs), list(fl)
    ts = cs[-1].ts + H4_MS
    cs.append(Candle(ts, 103.0, 103.5, 102.0, 103.0))    # oeffnet UNTER der 0.786 (104,65)
    f = fl[-1]
    fl.append(FlowPoint(ts, f.spot_cvd - 30, 0.0, f.oi + 1e6, f.funding))
    sig, _ = _e41_lauf(cs, fl)
    nk = [s for i, s in sig if s.type == SignalType.NACHKAUF]
    assert nk, "Vorprobe: kein 0.786-Nachkauf im Szenario"
    assert abs(nk[0].price - 104.65) < 0.01              # Levelpreis, nicht Eroeffnung 103
