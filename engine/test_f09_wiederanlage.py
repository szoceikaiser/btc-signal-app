"""F09: vollstaendige Teilverkaeufe beenden den Kapitalzyklus (ohne Netz)."""
from decimal import Decimal

import backtest
from strategy_core import Candle

STEP = 4 * 3600 * 1000
START = 1767225600000  # 01.01.2026 UTC
D = Decimal


def _candles(prices):
    return [Candle(START + i * STEP, p, p, p, p) for i, p in enumerate(prices)]


def _signal(i, kind, price, pct):
    return dict(ts=START + i * STEP, type=kind, price=price, tranche_pct=pct)


def _closed_cycle(buy_type="KAUF_1"):
    # Vorprobe: 40 + 4*15 = 100 %, aber die binaere Rechnung hinterlaesst Rest.
    assert D("0.4") + 4 * D("0.15") == 1
    peak = 10000 * (1 - .001) / 120
    rest = peak - .4 * peak
    for _ in range(4):
        rest -= .15 * peak
    assert 0 < rest < 1e-13, "Szenario muss den positiven Rundungsrest erreichen"
    return [_signal(0, buy_type, 120, 100), _signal(1, "TEILVERKAUF_1", 240, 40)] + [
        _signal(i, "TEILVERKAUF_LADDER", 240, 15) for i in range(2, 6)]


def test_neuer_kauf_nutzt_das_kapital_nach_vollstaendigem_teilverkauf():
    signals = _closed_cycle() + [_signal(6, "KAUF_1", 120, 25)]
    result = backtest.simulate(signals, _candles([120] + [240] * 5 + [120, 240]),
                               start_ms=START)
    # Unabhaengige Dezimalrechnung: erster Zyklus komplett verkauft,
    # dann ein Viertel des NEUEN Cash investieren; jede Seite kostet 0,1 %.
    cash = D(10000) * D("0.999") * D(2) * D("0.999")
    spend = cash / 4
    holding = spend * D("0.999") / D(120) * D(240)
    assert result["trades"] == 5
    assert abs(result["offene_position"] - float(holding)) <= .0051
    assert abs(result["ende"] - float(cash - spend + holding)) <= .0051


def test_neue_verkaufsleiter_nutzt_den_hoechstbestand_des_neuen_zyklus():
    signals = _closed_cycle() + [_signal(6, "KAUF_1", 120, 25),
                                 _signal(7, "TEILVERKAUF_LADDER", 180, 15)]
    result = backtest.simulate(signals, _candles([120] + [240] * 5 + [120, 180, 120]),
                               start_ms=START)
    cash = D(10000) * D("0.999") * D(2) * D("0.999")
    spend = cash / 4
    units = spend * D("0.999") / D(120)
    proceeds = units * D("0.15") * D(180) * D("0.999")
    holding = units * D("0.85") * D(120)
    assert result["trades"] == 6
    assert abs(result["offene_position"] - float(holding)) <= .0051
    assert abs(result["ende"] - float(cash - spend + proceeds + holding)) <= .0051


def test_echte_kleine_restposition_wird_nicht_auf_null_gerundet():
    # Reine Skalierungsprobe: winzige Einheiten haben hier 6.000 Geldeinheiten Wert.
    # Eine pauschale absolute Grenze von 1e-12 wuerde diesen Bestand loeschen.
    price = 1e18
    assert 10000 / price < 1e-12
    result = backtest.simulate([_signal(0, "KAUF_1", price, 100),
                               _signal(1, "TEILVERKAUF_1", price, 40)],
                              _candles([price, price]), fee=0, start_ms=START)
    assert result["offene_position"] == 6000.0
    assert result["ende"] == 10000.0


def test_verkaufter_rueckkauf_erzeugt_keinen_zusaetzlichen_geister_stop():
    signals = _closed_cycle("RUECKKAUF") + [_signal(6, "RUECKKAUF_STOP", 240, 100)]
    result = backtest.simulate(signals, _candles([120] + [240] * 6), start_ms=START)
    assert result["trades"] == 5, "Kein sechster Verkauf eines Rundungsrestes"
    assert result["offene_position"] == 0.0
    assert result["ende"] == 19960.02
