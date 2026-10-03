"""A8 independent counterexamples. Offline only; no historical optimization."""
from decimal import Decimal as D

from execution_perp_offline import PerpBook
from strategy_core import Candle, resample_daily
import coinalyze as cz


def order(typ, action, pct):
    return dict(id=typ, ts=0, type=typ, action=action, tranche_pct=pct)


def test_f08_off_grid_extra_invalidates_only_its_day():
    step = 14_400_000
    bars = [Candle(i*step, 100, 110, 90, 100) for i in range(12)]
    bad = Candle(1, 100, 999, 1, 100)
    assert resample_daily(bars+[bad]) == [Candle(86_400_000, 100, 110, 90, 100)]
    assert resample_daily([bad]+bars) == resample_daily(bars+[bad])


def test_f02_partial_exit_uses_current_cycle_peak_for_long_and_short():
    for entry, exit_all, tp in [('KAUF_1','VERKAUF_REST','TEILVERKAUF_1'),
                                ('SHORT_1','SHORT_COVER_REST','SHORT_TP_1')]:
        b = PerpBook('1000','0')
        b.fill(order(entry,'entry_t1',50),4,100,100)
        b.fill(order(exit_all,'rest_pattern',100),8,100,100)
        b.fill(order(entry,'entry_t1',25),12,100,100)
        event = b.fill(order(tp,'tp1',40),16,100,100)['event']
        assert D(event['qty']) == D('1')
        assert b.qty == D('1.5')


def test_f02_new_cycle_budget_uses_realized_wallet():
    b = PerpBook('1000','0')
    b.fill(order('KAUF_1','entry_t1',50),4,100,100)
    b.fill(order('VERKAUF_REST','rest_pattern',100),8,120,120)
    assert b.wallet == D('1100')
    b.fill(order('KAUF_1','entry_t1',50),12,100,100)
    assert b.qty == D('5.5')
    # Same-cycle adds retain its initial budget despite later mark gains.
    b.fill(order('KAUF_2','upgrade_gp',25),16,100,100)
    assert b.qty == D('8.25')


def test_f14_invalid_values_are_not_complete_measurements():
    values={'A': {0:10,1:float('nan'),2:0},'B': {0:20,1:20,2:0}}
    summed,report=cz._summiere_vollstaendig(values,['A','B'],[],'USD')
    assert summed=={0:30,2:0} and report['punkte_ausgelassen']==1
    means,report=cz.gewichtetes_mittel({'A':{0:1,1:1,2:0},'B':{0:2,1:2,2:0}},
        {'A':{0:float('nan'),1:-1,2:10},'B':{0:20,1:20,2:20}},['A','B'],[],'rate')
    assert means=={2:0} and report['punkte_ausgelassen']==2
