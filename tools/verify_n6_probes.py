"""Reached synthetic cases followed by deliberate offline implementation faults."""
import json
from pathlib import Path
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import execution_delayed as d
import test_execution_delayed as tests
import test_historical_stats as stats_tests
import historical_stats as stats


def main():
    cases=[
        ('early_fill', 'pending[0][\'ts\'] + 2*v.STEP', 'pending[0][\'ts\'] + v.STEP', 'test_i2_buy_waits_and_does_not_own_waiting_low'),
        ('no_reservation', 'pending = book.schedule(decision.candidates, c.close)', 'pending = []', 'test_i2_buy_waits_and_does_not_own_waiting_low'),
        ('skip_feedback', 'decision.confirm(pos, executed, book)', 'pass', 'test_i2_real_no_decide_during_wait_and_cost_feedback'),
        ('decision_while_waiting', '            continue\n        decision = decision_fn', '            pass\n        decision = decision_fn', 'test_i2_no_intermediate_decision_and_feedback_first'),
        ('wait_risk_omitted', '        risk.bar(book, c)', '        if not pending: risk.bar(book, c)', 'test_i2_sell_keeps_waiting_risk_and_gap'),
        ('fill_future_close', 'book.fill(order, c)', 'book.fill(order, sc.Candle(c.ts,c.close,c.high,c.low,c.close))', 'test_i2_buy_waits_and_does_not_own_waiting_low'),
        ('ignore_cutoff', 'v.validate(candles, flow, end_ms)', 'v.validate(candles, flow, end_ms+v.STEP)', 'test_i2_cutoff_rejects_running_fill_bar'),
        ('fee_doubled', 'DelayedBook(10000., fee, slippage, deploy)', 'DelayedBook(10000., 2*fee, slippage, deploy)', 'test_i2_roundtrip_costs'),
        ('micro_short', "adjusted['amount'] = self.units", 'pass', 'test_i2_last_reserved_sale_rounding_does_not_create_micro_short'),
        ('material_oversale', 'excess > 8*math.ulp(self.peak_units)', 'False', 'test_i2_real_oversale_is_rejected_not_clipped'),
    ]
    results=[]
    original=(ROOT/'engine/execution_delayed.py').read_text(encoding='utf-8')
    for name,old,new,test in cases:
        fn=getattr(tests,test);fn()
        assert old in original,name
        ns=dict(d.__dict__)
        exec(compile(original.replace(old,new,1),'<mutation '+name+'>','exec'),ns)
        try:
            with patch.multiple(d,run_delayed=ns['run_delayed'],DelayedBook=ns['DelayedBook']):fn()
        except (AssertionError,ValueError,StopIteration,IndexError):results.append(dict(name=name,caught=True))
        else:raise AssertionError('Survived: '+name)
    source=(ROOT/'tools/historical_stats.py').read_text(encoding='utf-8')
    for name,old,new,test in [
        ('iid_instead_of_blocks','rng.random(replicates) < 1/length','rng.random(replicates) < 1','test_geometric_dependence_wrap_and_seed'),
        ('wrong_quantile',"method='linear'","method='nearest'",'test_quantile_exact_hand_case_and_tail'),
        ('uncentered_null','(x-mu)[indices]','x[indices]','test_null_and_constant_alternatives'),
        ('wrong_tail','z >= mu','z <= mu','test_null_and_constant_alternatives'),
        ('reversed_pair','a[:, 1]-a[:, 0]','a[:, 0]-a[:, 1]','test_pairing_shared_indices_and_swap'),
    ]:
        fn=getattr(stats_tests,test);fn()
        ns=dict(stats.__dict__);assert old in source
        exec(compile(source.replace(old,new,1),'<mutation '+name+'>','exec'),ns)
        try:
            with patch.multiple(stats_tests,**{k:ns[k] for k in ['stationary_indices','paired_bootstrap','interval','daily_pair']}):fn()
        except (AssertionError,ValueError):results.append(dict(name=name,caught=True))
        else:raise AssertionError('Survived: '+name)
    print(json.dumps(dict(result='PASS',probes=results),indent=2))


if __name__=='__main__':main()
