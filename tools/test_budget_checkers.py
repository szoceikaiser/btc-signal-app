"""Synthetic coherent policy regressions; no arbitrary-field corruption."""
import sys,json
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'engine'))
import execution_v1 as v
from test_execution_v1 import script,order,fills
import check_budget_fraction as a,check_budget_decimal as b

S=dict(fee_pct=.1,slippage_pct=0,next_open_offset=1)
ROWS=[(100,100,100,100)]*8
def check(r):
    for checker in (a,b):assert checker.verify(r,S,{})['passed']
def fail(r,rule):
    for checker in (a,b):
        try:checker.verify(r,S,{})
        except AssertionError as e:assert rule in str(e),(checker.__name__,str(e),rule)
        else:raise AssertionError('Policy corruption survived '+checker.__name__)

def test_legitimate_tiny_wallet_and_real_partial_fills():
    small=script(ROWS,{0:[order('entry_t1','KAUF_1')]},capital=1e-25,fee=.001)
    assert len(fills(small))==1 and small['btc']>0;check(small)
    r=script(ROWS,{0:[order('entry_t1','KAUF_1',pct=75),order('e42_buy','RUECKKAUF',pct=75)],
        1:[order('part_stop','RUECKKAUF_STOP')],2:[order('buy_ladder','NACHKAUF',pct=25)],
        3:[order('stop','STOPLOSS')],4:[order('entry_t1','KAUF_1')]},fee=.001)
    assert any(e['reason']=='partial_cash' for e in r['ledger']);check(r)

def test_clean_budget_and_consistent_illegal_rejection():
    by={0:[order('entry_t1','KAUF_1',pct=75)],1:[order('entry_gp','KAUF_2',pct=25)],2:[order('buy_ladder','NACHKAUF',pct=15)]}
    good=script(ROWS,by,capital=12216.407375392477,fee=.001)
    assert len(fills(good))==2 and good['cash']==0;check(good)
    # Coherent alternative execution: all balances/fees/lots remain unchanged,
    # but the scheduler rejects an available budget. This is a policy failure.
    original=v.Book.quantities
    def no_buy(self,o):return 0 if o['action'] in v.BUY_ACTIONS else original(self,o)
    original_request=v.Money.request
    with patch.object(v.Money,'request',lambda self,pct:original_request(self,0)):
        bad=script(ROWS,{0:[order('entry_t1','KAUF_1')]},fee=.001)
    assert not fills(bad) and bad['cash']==10000 and bad['fees']==0
    fail(bad,'rejected_available_budget')

def test_consistent_representable_buy_rejected_and_invisible_buy_accepted():
    # Use isolated source copies to change the actual policy branch; every
    # downstream book field is produced coherently by the corrupted model.
    import inspect
    source=inspect.getsource(v.Book.fill)
    import textwrap
    def mutant(replacement):
        namespace=dict(vars(v));code=textwrap.dedent(source).replace('if quantity <= 0 or self.units + quantity == self.units:',replacement)
        assert code!=textwrap.dedent(source);exec(code,namespace);return namespace['fill']
    by={0:[order('entry_t1','KAUF_1')]}
    good=script(ROWS,by,fee=.001);assert len(fills(good))==1;check(good)
    with patch.object(v.Book,'fill',mutant('if True:')):bad=script(ROWS,by,fee=.001)
    assert bad['cash']==10000 and bad['btc']==bad['fees']==0 and bad['ledger'][-1]['reason']=='unrepresentable_btc_increment'
    fail(bad,'rejected_representable_buy')
    # Real declared remainder (not rounding-artifact cash) after a 99.999...%
    # budget split. Its quantity disappears in the substantial existing BTC.
    by={0:[order('entry_t1','KAUF_1',pct=99.99999999999999)],1:[order('entry_gp','KAUF_2',pct=100)]}
    rows=[(9891,9891,9891,9891)]*8
    good=script(rows,by,fee=.001);assert any(e['reason']=='unrepresentable_btc_increment' for e in good['ledger']);check(good)
    with patch.object(v.Book,'fill',mutant('if False:')):bad=script(rows,by,fee=.001)
    assert len(fills(bad))==2 and fills(bad)[-1]['before']['btc']==fills(bad)[-1]['after']['btc']
    fail(bad,'accepted_invisible_buy')

def main():
    names=[n for n in globals() if n.startswith('test_')]
    for n in names:globals()[n]()
    print(json.dumps(dict(passed=True,cases=names,checkers=2,historical_starts=0)))
if __name__=='__main__':main()
