"""Declared synthetic wallets/orders; no measured market provenance asserted."""
import json
from fractions import Fraction as F
from copy import deepcopy
from unittest.mock import patch
import execution_v1 as v, execution_delayed as delayed, strategy_core as sc
from test_execution_v1 import order,script,bars,entry_fixture,fills
from test_cash_observable import ladder_decision

def buy(book,pct,at=0,kind='KAUF_1'):
    o=dict(order('e42_buy' if kind=='RUECKKAUF' else 'entry_t1',kind,pct=pct),ts=at*v.STEP)
    orders=book.schedule([o],79150.26)
    assert orders
    return book.fill(orders[0],sc.Candle((at+1)*v.STEP,*([79150.26]*4)))

def test_clean_75_25_exhaustion_has_no_third_fill_or_rung():
    for cls in (v.Book,delayed.DelayedBook):
        b=cls(12216.407375392477,.001,.001,1)
        assert buy(b,75) and buy(b,25,1)
        assert len(b.lots)==2 and b.money.spent==F('12216.407375392477')
        p,d=ladder_decision();before=deepcopy(b.lots)
        pending=b.schedule([dict(d.candidates[0],ts=2*v.STEP)],79150.26)
        assert pending==[] and b.cash==0 and b.money.cash==0 and b.lots==before
        with patch.object(sc,'find_pivots',return_value=[]),patch.object(sc,'confirm_ok',return_value=True):d.confirm(p,[],b)
        assert p.buy_rungs==0 and b.ledger[-1]['reason']=='no_cash'

def test_declared_decimal_shortfall_is_real_money_not_clamped():
    b=v.Book(10000,0,0,1)
    assert buy(b,64.4) and buy(b,100-64.4,1)
    assert b.money.cash==F('0.0000000000006') and b.cash==6e-13
    # Actual declared 35.599999999999994 differs from explicit 35.6.
    assert F(str(64.4))+F(str(100-64.4))<100
    small=v.Book('0.0000000000006',.001,0,1)
    assert buy(small,100) and small.cash==0 and small.units>0

def test_exact_multiple_reservations_partial_expiry_and_restart():
    b=v.Book(12216.407375392477,.001,.001,1)
    orders=b.schedule([dict(order('entry_t1','KAUF_1',pct=75),ts=0),dict(order('e42_buy','RUECKKAUF',pct=75),ts=0)],100)
    assert len(orders)==2 and F(orders[0]['amount_exact'])+F(orders[1]['amount_exact'])==b.money.initial
    assert F(orders[1]['amount_exact'])<F(orders[1]['requested_exact'])
    clone=v.Book.from_state(json.loads(json.dumps(b.to_state())))
    for book in (b,clone):
        assert book.fill(orders[0],sc.Candle(v.STEP,100,100,100,100))
        assert book.money.reserved==book.money.cash
        done=book.fill(orders[1],sc.Candle(v.STEP,100,100,100,100))
        assert done['fraction']==float(F(1,3)) and book.cash==0 and book.rk_units>0
    assert b.to_state()==clone.to_state()
    # An expired real reservation releases precisely its own amount.
    fresh=v.Book('1e-25',0,0,1)
    pending=fresh.schedule([dict(order('entry_t1','KAUF_1',pct=75),ts=0),dict(order('entry_gp','KAUF_2',pct=25),ts=0)],100)
    fresh.expire(pending[0],100)
    assert fresh.money.cash==F('1e-25') and fresh.money.reserved==F('2.5e-26')
    fresh.expire(pending[1],100);assert fresh.money.reserved==0

def test_sales_rebuy_same_cycle_then_new_cycle_conserve_fees():
    r=script([(100,100,100,100)]*8,{0:[order('entry_t1','KAUF_1',pct=75),order('e42_buy','RUECKKAUF',pct=25)],
        1:[order('part_stop','RUECKKAUF_STOP',pct=25)],2:[order('e42_buy','RUECKKAUF',pct=25)],
        3:[order('stop','STOPLOSS')],4:[order('entry_t1','KAUF_1',pct=100)]},fee=.001)
    events=fills(r);assert len(events)==6 and events[2]['type']=='RUECKKAUF_STOP'
    cash=F(10000);spent=proceeds=fees=F(0)
    for e in events:
        if e['action'] in v.BUY_ACTIONS:
            amount=F(e['amount_exact']);cash-=amount;spent+=amount;fees+=amount/1000
        else:
            gross=F(str(e['quantity']))*F(str(e['fill_price']));net=gross*F(999,1000)
            cash+=net;proceeds+=net;fees+=gross/1000
        assert F(e['after']['money']['cash'])==cash
    assert F(r['money']['cash'])==10000+proceeds-spent==0
    assert F(r['money']['fees'])==fees
    assert events[3]['before']['money']['alloc']=='10000'
    assert F(events[-1]['before']['money']['alloc'])==F(events[-2]['after']['money']['cash'])

def test_old_or_inconsistent_precise_checkpoint_rejected():
    b=v.Book(12216.407375392477,.001,0,1);assert buy(b,75)
    good=json.loads(json.dumps(b.to_state()));assert v.Book.from_state(good).to_state()==good
    for change in (lambda x:x.pop('money'),lambda x:x.update(version=1),
                   lambda x:x['money'].update(cash='1'),lambda x:x.update(cash=x['cash']+1),
                   lambda x:x.update(execution_semantics='V1-cash-observable-v1')):
        bad=deepcopy(good);change(bad)
        try:v.Book.from_state(bad)
        except ValueError:pass
        else:raise AssertionError('Old/corrupt exact history accepted')

def test_delayed_native_pending_and_waiting_restart_exact():
    cs,fs=entry_fixture();cfg=dict(pivot_n=2,bias_short=False)
    base=delayed.run_delayed(cs,fs,cfg,start_ms=0,end_ms=cs[-1].ts+v.STEP)
    assert base['waiting'] and fills(base)
    for at in (base['waiting'][0]['pending'][0]['ts'],base['waiting'][0]['at']-v.STEP):
        r=delayed.run_delayed(cs,fs,cfg,start_ms=0,end_ms=cs[-1].ts+v.STEP,checkpoint_at=at)
        cp=json.loads(json.dumps(r.pop('checkpoint')))
        assert cp['pending'] and cp['book']['money']['pending']
        assert delayed.resume_delayed(cs,fs,cp)==r==base
        bad=deepcopy(cp);bad['execution_semantics']='V1-cash-observable-v1'
        try:delayed.resume_delayed(cs,fs,bad)
        except ValueError:pass
        else:raise AssertionError('Old delayed checkpoint accepted')

def test_precise_pending_order_cannot_be_spent_twice_or_relabelled():
    b=v.Book(10,0,0,1);p=b.schedule([dict(order('entry_t1','KAUF_1'),ts=0)],100)[0]
    assert p['amount_exact']=='10'
    for bad in (dict(p,amount_exact='9'),dict(p,requested_exact='11'),dict(p,id='foreign')):
        state=b.to_state()
        try:b.fill(bad,sc.Candle(v.STEP,100,100,100,100))
        except ValueError:pass
        else:raise AssertionError('Foreign budget spent')
        assert b.to_state()==state
    assert b.fill(p,sc.Candle(v.STEP,100,100,100,100))
    state=b.to_state()
    try:b.fill(p,sc.Candle(v.STEP,100,100,100,100))
    except ValueError:pass
    else:raise AssertionError('Budget spent twice')
    assert b.to_state()==state

def test_real_partial_shortfall_survives_rounded_fraction_one():
    b=v.Book(1,0,0,1,1);b.alloc='1.00000000000000001'
    p=b.schedule([dict(order('buy_ladder','NACHKAUF'),ts=0)],100)
    assert F(p[0]['amount_exact'])<F(p[0]['requested_exact'])
    done=b.fill(p[0],sc.Candle(v.STEP,100,100,100,100))
    assert done['fraction']==1.0 and b.ledger[-2]['reason']=='partial_cash'
    assert b.ledger[-1]['reason']=='cash_shortfall' and b.ledger[-1]['rejected_budget']==1e-17
