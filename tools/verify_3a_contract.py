"""Offline-Belege fuer den Vertragsentwurf; KEINE neue Ausfuehrungsengine.

Handrechnungen verwenden rationale Zahlen und keine Produktionshelfer.
Die drei Produktionsproben bestaetigen absichtlich noch vorhandene Fehler.
Keine Originaldatei wird geschrieben, keine Marktdaten werden abgerufen.
"""
from fractions import Fraction as F
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
import backtest as bt
import strategy_core as sc


def main():
    checks = {}

    def check(name, actual, expected):
        assert actual == expected, (name, actual, expected)
        checks[name] = str(actual)

    # Ausschliesslich ausgeschriebene Handidentitaeten, kein Portfolio-Replay.
    check('H01_sale_after_low_dd', 1-F(100*50, 10000), F(1, 2))
    check('H02_cash_before_buy_dd', 1-F(10000, 10000), 0)
    check('H03_low_high_close_dd', max(1-F(5000, 10000), 1-F(10000, 20000)), F(1, 2))
    check('H03_high_low_close_dd', 1-F(5000, 20000), F(3, 4))
    check('H04_next_open_buy_units', F(10000, 125), 80)
    check('H04_next_open_buy_close_equity', 80*100, 8000)
    check('H05_gap_sale_equity', 100*70, 7000)
    check('H06_buy_limit_gap_units', F(10000, 90), F(1000, 9))
    check('H06_sell_limit_gap_cash', 100*130, 13000)
    check('H07_stop_first_cash', 100*90, 9000)
    check('H07_target_first_cash', 100*110, 11000)
    check('H08_extension_before', 120+(160-80), 200)
    check('H08_extension_after', 90+(160-80), 170)
    check('H09_full_exit_cash', 5000+50*100, 10000)
    check('H09_partial_exit_cash', 5000+20*100, 7000)
    check('H09_partial_exit_units', 50-20, 30)
    check('H10_buy_units_fee', F(10000)*(1-F(1,1000))/100, F(999,10))
    check('H10_roundtrip_cash_fee', F(999,10)*100*(1-F(1,1000)), F(998001,100))
    check('H10_roundtrip_loss', 1-F(998001,1000000), F(1999,1000000))
    check('H11_no_successor_no_fill_units', 0, 0)
    check('H12_gap_stop_before_cancel_cash', 100*80, 8000)
    check('H13_half_sale_remaining_units', 100-50, 50)
    check('H13_low_after_sale_equity', 5000+50*50, 7500)
    check('H14_frozen_cohort_extra_loss', F(9000-6000,10000), F(3,10))
    check('H15_return_to_low_upper_dd', 1-F(5000,20000), F(3,4))
    check('H16_cash_cap_after_first_buy', 10000-7500, 2500)
    check('H16_second_buy_capped', min(2500,7500), 2500)

    # Gegenkontrollen muessen bei bewusst falschen Erwartungen anschlagen.
    wrong = [
        ('F01_post_sale_inventory', F(0), F(1,2)),
        ('F01_new_buy_on_old_low', F(1,2), F(0)),
        ('F01_fixed_low_high_is_exact', F(1,2), F(3,4)),
        ('F12_retroactive_level', F(100), F(80)),
        ('gap_stop_at_threshold', F(9000), F(7000)),
        ('fee_omitted', F(10000), F(998001,100)),
        ('last_signal_invented_fill', F(100), F(0)),
        ('cash_overspent', F(7500), F(2500)),
    ]
    rejected = []
    for name, actual, expected in wrong:
        try:
            assert actual == expected
        except AssertionError:
            rejected.append(name)
    assert len(rejected) == len(wrong)

    step = 14400000
    cs = [sc.Candle(0,100,100,100,100), sc.Candle(step,100,100,50,100)]
    buy = dict(ts=0,type='KAUF_1',price=100,tranche_pct=100)
    sell = dict(ts=step,type='STOPLOSS',price=100,tranche_pct=100)
    a = bt.simulate([buy,sell], cs, fee=0, start_ms=0)
    assert a['ende'] == 10000 and a['max_drawdown_pct'] == 0
    b = bt.simulate([{**buy,'ts':step}], cs, fee=0, start_ms=0)
    assert b['ende'] == 10000 and b['max_drawdown_pct'] == -50

    z = sc.fib_zones(sc.Impulse(sc.Pivot(0,0,80,'L'),sc.Pivot(1,step,160,'H')))
    pos = sc.Position(direction='LONG',state=sc.PosState.FULL,zones=z,
                      retrace_extreme=120,entry_ref=140,entry_pct=100,bestand_pct=100)
    c = sc.Candle(2*step,140,190,90,140)
    assert z.ext_target(pos.retrace_extreme,1.0) == 200 > c.high
    with patch.object(sc,'find_pivots',return_value=[]):
        sig = sc.evaluate([c],[],pos,tp_ladder=False,buy_ladder=False,
                          bias_short=False,rest_halten=True)
    assert [s.type.name for s in sig] == ['TEILVERKAUF_1']
    assert sig[0].price == 170 and sig[0].ts == c.ts
    assert pos.retrace_extreme == 90

    print(json.dumps(dict(
        scope='Etappe 3a: Handidentitaeten und gezielte Ist-Proben, keine 3b-Umsetzung',
        arithmetic_checks=len(checks), hand_cases=16, values=checks,
        negative_controls_rejected=rejected,
        production_probes=dict(
            sale_after_low=dict(actual_dd_pct=a['max_drawdown_pct'],close_fill_expected_dd_pct=-50),
            buy_after_low=dict(actual_dd_pct=b['max_drawdown_pct'],close_fill_expected_dd_pct=0),
            new_target_same_bar=dict(old_target=200,new_target=170,ohlc=[140,190,90,140],
                                     signals=[s.to_dict() for s in sig])),
        result='PASS: Rechenvertrag geprueft; Produktionsfehler weiterhin vorhanden'
    ),indent=2,ensure_ascii=False))


if __name__ == '__main__':
    main()
