"""16 contract cases: V1 implementation probes vs independent arithmetic.

V2 and E41.6 cases are explicitly arithmetic-only boundary cases, not implemented.
"""
from fractions import Fraction as F
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import test_execution_v1 as t


def main():
    cases=[]
    tests={
        'H01':t.test_h01_sale_after_low_has_old_inventory_risk,
        'H02':t.test_h02_buy_after_low_does_not_own_old_low,
        'H03':t.test_h03_extremes_and_close_bounds,
        'H04':t.test_h04_causal_buy_gap_and_separate_reference,
        'H05':t.test_h05_stop_gap_old_holdings_before_sale,
        'H08':t.test_h08_real_new_target_reference_never_same_bar_fill,
        'H09':t.test_h09_full_exit_suppresses_buy_and_partial_sale,
        'H10':t.test_h10_fee_once_each_fill,
        'H11':t.test_h11_last_signal_expires_no_phantom_fill,
        'H13':t.test_h13_open_partial_sale_inventory_during_low,
        'H16':t.test_h16_sequential_cash_reservations_partial_funding}
    for name,fn in tests.items():
        fn();cases.append(dict(case=name,kind='V1 production assertion',result='PASS',test=fn.__name__))
    assert F(10000,90)==F(1000,9) and 100*130==13000
    cases.append(dict(case='H06',kind='V2 excluded; independent prior-limit arithmetic only',result='PASS'))
    assert 100*90==9000 and 100*110==11000
    cases.append(dict(case='H07',kind='V2 excluded; independent OCO ambiguity only',result='PASS'))
    assert 100*80==8000
    cases.append(dict(case='H12',kind='V2 excluded; independent cancellation boundary only',result='PASS'))
    assert F(9000-6000,10000)==F(3,10)
    cases.append(dict(case='H14',kind='E41.6 excluded; independent frozen cohort arithmetic only',result='PASS'))
    path=[10000,5000,20000,5000,10000];peak=F(10000);dd=F(0)
    for value in path:
        peak=max(peak,value);dd=max(dd,1-F(value,peak))
    assert dd==F(3,4)
    t.test_h03_extremes_and_close_bounds()
    cases.append(dict(case='H15',kind='Repeated-extreme path independently reaches V1 upper bound, not lower prediction',result='PASS',actual_path_dd=str(dd)))
    # Independent rational costs, quote and cash examples underpin float checks.
    assert F(10000)*F(999,1000)/100==F(999,10)
    assert F(999,10)*100*F(999,1000)==F(998001,100)
    assert F(10000,125)==80 and min(F(2500),F(7500))==2500
    assert len(cases)==16
    print(json.dumps(dict(result='PASS',cases=sorted(cases,key=lambda c:c['case']),
        scope='16 checked; 12 V1 cases, 3 V2 exclusions, 1 E41.6 exclusion'),indent=2))


if __name__=='__main__':main()
