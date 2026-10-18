"""Synthetic arithmetic/state cases for N-UM2-01; no market-size minimum."""
import json, math
from copy import deepcopy
from unittest.mock import patch
import strategy_core as sc
import execution_v1 as v
import execution_delayed as delayed
from test_execution_v1 import position,bars,order,script,fills
from test_execution_delayed import scripted


def ladder_decision():
    p=position(sc.PosState.CORE)
    cs,fs=bars([(120,120,110,115)])
    with patch.object(sc,'find_pivots',return_value=[]),patch.object(sc,'confirm_ok',return_value=True):
        d=v.decide(cs,fs,p,dict(tp_ladder=False,buy_ladder=True,rest_halten=True))
    assert [o['action'] for o in d.candidates]==['buy_ladder']
    return p,d


def test_witness_like_unrepresentable_buy_keeps_money_lots_and_rung():
    p,d=ladder_decision()
    b=v.Book(9.094947017729282e-13,.001,0,1,0.16157368829412078)
    b.alloc=12877.637227390089
    pending=b.schedule(d.candidates,79150.27)
    money,units,lots=b.cash,b.units,deepcopy(b.lots)
    accepted=b.fill(pending[0],sc.Candle(v.STEP,79150.26,79150.26,79150.26,79150.26))
    assert accepted is None and b.cash==money and b.units==units and b.lots==lots
    assert b.reserved_cash==0 and b.ledger[-1]['fee']==b.ledger[-1]['quantity']==0
    assert b.ledger[-1]['reason']=='unrepresentable_btc_increment'
    with patch.object(sc,'find_pivots',return_value=[]),patch.object(sc,'confirm_ok',return_value=True):
        d.confirm(p,[],b)
    assert p.buy_rungs==0 and p.state==sc.PosState.CORE


def test_tiny_real_wallet_and_inventory_remain_tradeable_when_representable():
    # Same money scale as the witness, but no large inventory to swallow it.
    b=v.Book(9.094947017729282e-13,.001,0,1)
    o=dict(order('entry_t1','KAUF_1'),ts=0)
    pending=b.schedule([o],79150.26)
    accepted=b.fill(pending[0],sc.Candle(v.STEP,79150.26,79150.26,79150.26,79150.26))
    assert accepted is not None and b.cash==0 and b.units>0 and len(b.lots)==1
    tiny=v.Book(1e-25,0,0,1,1e-27);tiny.alloc=1e-25
    accepted=tiny.fill(tiny.schedule([o],100)[0],sc.Candle(v.STEP,100,100,100,100))
    assert accepted is not None and tiny.units==2e-27


def test_actual_open_representation_boundary_and_partial_fill():
    # No schedule-time estimate: exactly the same reservation can be executable
    # at one eligible open and unrepresentable at another. Equality at half ULP
    # follows IEEE ties-to-even rather than an arbitrary tolerance/minimum.
    for q,expected in [(math.ulp(1.)/4,False),(math.ulp(1.)/2,False),(math.ulp(1.),True)]:
        b=v.Book(q,0,0,1,1.);b.alloc=100
        o=dict(order('buy_ladder','NACHKAUF',pct=15),ts=0)
        pending=b.schedule([o],100)
        assert pending and pending[0]['amount']==q
        result=b.fill(pending[0],sc.Candle(v.STEP,1,1,1,1))
        assert (result is not None)==expected
        assert b.cash==(0 if expected else q)
        if expected: assert result['fraction']<1
    q=math.ulp(1.)
    b=v.Book(q,0,0,1,1.);b.alloc=100
    pending=b.schedule([o],1)
    assert b.fill(pending[0],sc.Candle(v.STEP,100,100,100,100)) is None


def test_rejection_survives_json_and_does_not_destroy_e42_or_other_reservations():
    lots=[dict(id='base',at=0,fill_price=100,units=.75,cost=75,buy_fee=0,kind='base'),
          dict(id='rk',at=0,fill_price=100,units=.25,cost=25,buy_fee=0,kind='e42')]
    b=v.Book(1e-15,0,0,1,1.,lots);b.alloc=100
    o=dict(order('e42_buy','RUECKKAUF',pct=25),ts=0)
    pending=b.schedule([o],100)
    restored=v.Book.from_state(json.loads(json.dumps(b.to_state())))
    for book in (b,restored):
        assert book.fill(pending[0],sc.Candle(2*v.STEP,100,100,100,100)) is None
        assert book.cash==1e-15 and book.lots==lots and book.rk_units==.25
        assert book.reserved_cash==0
        # No implicit cash mutation/deposit into an established exact history.
        # A separately declared synthetic wallet can still buy the E42 cohort.
        funded=v.Book('100.000000000000001',0,0,1,book.units,book.lots)
        funded.alloc=100
        new=funded.schedule([dict(o,ts=3*v.STEP)],100)
        assert funded.fill(new[0],sc.Candle(4*v.STEP,100,100,100,100)) is not None
        assert funded.rk_units==.5 and funded.units==1.25
    assert b.to_state()==restored.to_state()
    old=b.to_state();del old['execution_semantics']
    try: v.Book.from_state(old)
    except ValueError: pass
    else: raise AssertionError('Unversioned old execution checkpoint accepted')


def test_reservations_expiry_and_repeated_rejections_preserve_exact_cash():
    b=v.Book(1e-15,0,0,1,1.);b.alloc=100
    for i in range(10):
        orders=b.schedule([dict(order('buy_ladder','NACHKAUF',pct=15),ts=i*v.STEP)],100)
        assert b.fill(orders[0],sc.Candle((i+1)*v.STEP,100,100,100,100)) is None
        assert b.cash==1e-15 and b.units==1 and b.reserved_cash==0 and len(b.lots)==1
    pending=b.schedule([dict(order('buy_ladder','NACHKAUF',pct=15),ts=11*v.STEP)],100)
    b.expire(pending[0],100)
    assert b.cash==1e-15 and b.units==1 and b.reserved_cash==0


def test_v1_and_delayed_callers_exclude_unexecuted_fill_feedback():
    # First two real buys leave a binary residual because 75% + 25% of this
    # wallet is not exactly distributive in binary floats. Third buy is rejected.
    capital=12877.637227390089
    rows=[(100,100,100,100)]*8
    by={0:[order('entry_t1','KAUF_1',pct=75)],1:[order('entry_gp','KAUF_2',pct=25)],
        2:[order('buy_ladder','NACHKAUF',pct=15)]}
    r=script(rows,by,capital=capital,fee=.001)
    assert len(fills(r))==2
    assert r['cash']==0 and any(e['reason']=='no_cash' for e in r['ledger'])
    assert next(f for f in r['feedback'] if f['at']==3*v.STEP)['actions']==[]
    # Delayed runner has fixed 10,000 cash. Select percentages whose subtraction
    # leaves a residual without injecting any runtime cash or book reset.
    by={0:[order('entry_t1','KAUF_1',pct=64.4)],2:[order('entry_gp','KAUF_2',pct=35.6)],
        4:[order('buy_ladder','NACHKAUF',pct=15)]}
    r=scripted(rows,by,fee=.001,slippage=0)
    assert len(fills(r))==2
    assert r['cash']==0 and any(e['reason']=='no_cash' for e in r['ledger'])
    assert not any(f['actions'] for f in r['feedback'] if f['at']>=5*v.STEP)


def test_two_real_reservations_and_full_reinvestment_cycle():
    r=script([(100,100,100,100)]*5,{0:[order('entry_t1','KAUF_1',pct=75),
        order('entry_gp','KAUF_2',pct=75)],1:[order('stop','STOPLOSS')],
        2:[order('entry_t1','KAUF_1',pct=100)]},fee=.001)
    assert len(fills(r))==4 and fills(r)[0]['gross_budget']==7500 and fills(r)[1]['gross_budget']==2500
    assert r['reserved_cash']==r['reserved_btc']==0 and r['btc']>0


def test_two_unexecuted_reservations_are_released_individually():
    b=v.Book(2e-15,0,0,1,1);b.alloc=1e-15
    orders=b.schedule([dict(order('buy_ladder','NACHKAUF'),ts=0),
                       dict(order('e42_buy','RUECKKAUF'),ts=0)],100)
    assert len(orders)==2 and b.reserved_cash==2e-15
    assert b.fill(orders[0],sc.Candle(v.STEP,100,100,100,100)) is None
    assert b.reserved_cash==1e-15 and b.cash==2e-15
    assert b.fill(orders[1],sc.Candle(v.STEP,100,100,100,100)) is None
    assert b.reserved_cash==0 and b.cash==2e-15 and b.units==1


def test_native_pending_rejection_checkpoint_json_restart_exact_parity():
    cs,fs=bars([(120,120,110,115)]*3)
    fs=[sc.FlowPoint(f.ts,f.spot_cvd,f.fut_cvd,f.oi,-.0001) for f in fs]
    cfg=dict(bias_short=False,tp_ladder=False,buy_ladder=True,rest_halten=True)
    kw=dict(start_ms=0,end_ms=3*v.STEP,start_capital=1e-15,initial_units=1,
            initial_position=position(sc.PosState.CORE),fee=.001)
    r=v.run_v1(cs,fs,cfg,checkpoint_at=0,**kw)
    cp=json.loads(json.dumps(r.pop('checkpoint')))
    assert cp['pending'] and cp['book']['reserved_cash']>0
    assert any(e['reason']=='unrepresentable_btc_increment' for e in r['ledger'])
    assert all(not f['actions'] and f['buy_rungs']==0 for f in r['feedback'])
    assert v.resume_v1(cs,fs,cp)==r
    assert r['cash']==1e-15 and r['btc']==1
    del cp['execution_semantics']
    try:v.resume_v1(cs,fs,cp)
    except ValueError:pass
    else:raise AssertionError('Old unbound execution checkpoint accepted')
