"""Stage 3b: numerical expectations from hand calculations, not book helpers.

Scripted decisions test execution independently of signal generation. Separate
real-engine probes reach candidate gates, priorities and feedback before mutations.
"""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import math
import strategy_core as sc
import execution_v1 as v


def near(a,b):
    assert math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-8),(a,b)


def bars(rows):
    cs=[sc.Candle(i*v.STEP,*row) for i,row in enumerate(rows)]
    fs=[sc.FlowPoint(c.ts,i*100.,0.,1000.,0.) for i,c in enumerate(cs)]
    return cs,fs


def position(state=sc.PosState.FULL, **kw):
    z=sc.fib_zones(sc.Impulse(sc.Pivot(0,0,80.,'L'),sc.Pivot(1,v.STEP,160.,'H')))
    return sc.Position(direction='LONG',state=state,zones=z,retrace_extreme=120.,
                       entry_ref=100.,entry_pct=100,bestand_pct=100,**kw)


def order(action,t,price=100.,pct=100):
    return dict(action=action,type=t,price=price,tranche_pct=pct,reason='hand case')


class ScriptDecision:
    def __init__(self,cs,fs,p,params,by_bar):
        self.candidates=[dict(o,ts=cs[-1].ts) for o in by_bar.get(cs[-1].ts//v.STEP,[])]
    def confirm(self,p,executed,b):
        if b.units==0: sc._reset_position(p)
        elif p.state==sc.PosState.FLAT:
            p.__dict__.update(position().__dict__)


def script(rows,by_bar,capital=10000.,units=0.,fee=0.,slip=0.,**kw):
    cs,fs=bars(rows)
    return v.run_v1(cs,fs,{},start_ms=0,end_ms=len(cs)*v.STEP,
        start_capital=capital,initial_units=units,initial_position=position() if units else None,
        fee=fee,slippage=slip,
        decision_fn=lambda cs,fs,p,params:ScriptDecision(cs,fs,p,params,by_bar),**kw)


def fills(r): return [e for e in r['ledger'] if e['status']=='filled']


def entry_fixture():
    from test_strategy_core import e13_szenario
    cs,fs=e13_szenario()
    # Existing strategy fixture uses an arbitrary epoch, V1 requires UTC 4h IDs.
    shift=cs[0].ts
    cs=[sc.Candle(c.ts-shift,c.open,c.high,c.low,c.close) for c in cs]
    fs=[sc.FlowPoint(f.ts-shift,f.spot_cvd,f.fut_cvd,f.oi,f.funding) for f in fs]
    for _ in range(2):
        c=sc.Candle(cs[-1].ts+v.STEP,114,114.1,113.9,114)
        f=fs[-1]
        cs.append(c); fs.append(sc.FlowPoint(c.ts,f.spot_cvd-30,0,f.oi+1e6,f.funding))
    return cs,fs


def test_h01_sale_after_low_has_old_inventory_risk():
    r=script([(100,100,50,100),(100,100,100,100)],{0:[order('stop','STOPLOSS')]},capital=0,units=100)
    near(r['dd_intrabar_lower_pct'],50); near(r['dd_intrabar_upper_pct'],50)
    near(r['dd_close_pct'],0); near(r['ende'],10000)
    assert fills(r)[0]['fill_at']==v.STEP


def test_h02_buy_after_low_does_not_own_old_low():
    r=script([(100,100,50,100),(100,100,100,100)],{0:[order('entry_t1','KAUF_1')]})
    near(r['btc'],100); near(r['dd_intrabar_upper_pct'],0)
    near(r['dd_close_pct'],0)


def test_h03_extremes_and_close_bounds():
    r=script([(100,200,50,100)],{},capital=0,units=100)
    near(r['dd_intrabar_lower_pct'],50); near(r['dd_intrabar_upper_pct'],75)
    near(r['dd_close_pct'],0)


def test_h04_causal_buy_gap_and_separate_reference():
    r=script([(100,100,100,100),(125,125,100,100)],{0:[order('entry_t1','KAUF_1')]})
    e=fills(r)[0]; near(e['quantity'],80); near(r['ende'],8000)
    assert e['reference_price']==100 and e['fill_price']==125
    assert e['candle_id']==0 and e['knowledge_assumed_at']==e['fill_at']==v.STEP


def test_h05_stop_gap_old_holdings_before_sale():
    r=script([(100,100,85,85),(70,70,70,70)],{0:[order('stop','STOPLOSS',90)]},capital=0,units=100)
    near(r['cash'],7000); near(r['dd_close_pct'],30)
    near(r['dd_intrabar_upper_pct'],30)
    e=fills(r)[0]; assert e['fill_price']==70 and e['before']['equity']==7000


def test_upward_gap_peak_before_sale_cost_is_preserved():
    r=script([(100,100,100,100),(200,200,200,200)],{0:[order('stop','STOPLOSS')]},capital=0,units=100,fee=.001)
    near(r['cash'],19980); near(r['dd_close_pct'],0)
    near(r['dd_intrabar_upper_pct'],.1)
    assert fills(r)[0]['before']['equity']==20000


def test_h09_full_exit_suppresses_buy_and_partial_sale():
    r=script([(100,100,100,100)]*2,{0:[order('entry_t1','KAUF_1',pct=50),
        order('tp1','TEILVERKAUF_1',pct=40),order('stop','STOPLOSS')]},capital=5000,units=50)
    assert [e['type'] for e in fills(r)]==['STOPLOSS']
    near(r['cash'],10000); assert r['btc']==0
    assert sum(e['reason']=='exit_priority' for e in r['ledger'])==2


def test_h09_partial_exit_suppresses_buy():
    r=script([(100,100,100,100)]*2,{0:[order('entry_t1','KAUF_1',pct=50),
        order('tp1','TEILVERKAUF_1',pct=40)]},capital=5000,units=50)
    near(r['cash'],7000); near(r['btc'],30)
    assert [e['type'] for e in fills(r)]==['TEILVERKAUF_1']


def test_h10_fee_once_each_fill():
    r=script([(100,100,100,100)]*3,{0:[order('entry_t1','KAUF_1')],1:[order('stop','STOPLOSS')]},fee=.001)
    near(fills(r)[0]['quantity'],99.9); near(r['cash'],9980.01)
    near(r['fees'],19.99)


def test_h11_last_signal_expires_no_phantom_fill():
    r=script([(100,100,100,100)],{0:[order('entry_t1','KAUF_1')]})
    assert r['btc']==0 and r['unfilled_end_of_data']==1 and not fills(r)
    assert r['reserved_cash']==0 and r['cash']==10000
    e=r['ledger'][-1]; assert e['before']['reserved_cash']==10000 and e['after']['reserved_cash']==0


def test_h13_open_partial_sale_inventory_during_low():
    r=script([(100,100,100,100),(100,100,50,100)],
        {0:[order('tp_ladder','TEILVERKAUF_LADDER',pct=50)]},capital=0,units=100)
    near(r['dd_intrabar_lower_pct'],25); near(r['dd_intrabar_upper_pct'],25)
    near(r['cash'],5000); near(r['btc'],50)


def test_h16_sequential_cash_reservations_partial_funding():
    r=script([(100,100,100,100)]*2,{0:[order('entry_gp','KAUF_2',pct=75),order('upgrade_full','NACHKAUF',pct=75)]})
    near(fills(r)[0]['gross_budget'],7500); near(fills(r)[1]['gross_budget'],2500)
    assert fills(r)[1]['reason']=='partial_cash'
    assert any(e['reason']=='cash_shortfall' and e['rejected_budget']==5000 for e in r['ledger'])
    assert r['cash']==0 and r['reserved_cash']==0
    for e in r['ledger']:
        assert e['after']['available_cash']>=0


def test_slippage_cost_at_unchanged_open():
    for slip in (0,.001,.005):
        r=script([(100,100,100,100)]*3,{0:[order('entry_t1','KAUF_1')],1:[order('stop','STOPLOSS')]},fee=.001,slip=slip)
        near(r['cash'],10000*.999/(100*(1+slip))*100*(1-slip)*.999)
        e=fills(r)[0]; near(e['after']['equity'],9990/(1+slip))
        assert e['valuation_price']==100


def test_zero_fee_fill_preserves_equity_at_same_price():
    r=script([(100,100,100,100)]*3,{0:[order('entry_t1','KAUF_1')],1:[order('stop','STOPLOSS')]})
    for e in fills(r): near(e['before']['equity'],e['after']['equity'])


def test_multiple_bars_carry_peaks_not_reset():
    r=script([(100,200,100,200),(100,100,50,100)],{},capital=0,units=100)
    near(r['dd_intrabar_lower_pct'],75); near(r['dd_intrabar_upper_pct'],75)
    near(r['dd_close_pct'],50)


def test_month_close_before_new_month_open_fill():
    from datetime import datetime,timezone
    origin=int(datetime(2026,1,31,20,tzinfo=timezone.utc).timestamp()*1000)
    cs=[sc.Candle(origin,100,100,100,100),sc.Candle(origin+v.STEP,200,200,200,200)]
    fs=[sc.FlowPoint(c.ts,0,0,0,0) for c in cs]
    def fn(cs,fs,p,params):
        d=ScriptDecision(cs,fs,p,params,{})
        d.candidates=[dict(order('entry_t1','KAUF_1'),ts=origin)] if len(cs)==1 else []
        return d
    r=v.run_v1(cs,fs,{},start_ms=origin,end_ms=origin+2*v.STEP,fee=0,decision_fn=fn)
    assert r['month_ends']['2026-01']['equity']==10000
    near(r['btc'],50); assert r['month_ends']['2026-02']['equity']==10000


def expect_bad(cs,fs,**kw):
    try: v.run_v1(cs,fs,{},start_ms=0,end_ms=10*v.STEP,**kw)
    except ValueError: return
    raise AssertionError('Expected invalid input rejection')


def test_gaps_and_duplicates_and_order_rejected():
    cs,fs=bars([(100,100,100,100)]*3)
    expect_bad([cs[0],cs[2]],[fs[0],fs[2]])
    expect_bad([cs[0],cs[0]],[fs[0],fs[0]])
    expect_bad(list(reversed(cs)),list(reversed(fs)))


def test_bad_pairing_and_invalid_ohlc_rejected():
    cs,fs=bars([(100,100,100,100)]*2)
    expect_bad(cs,fs[:-1]); expect_bad(cs,list(reversed(fs)))
    expect_bad([sc.Candle(0,100,99,50,100)],fs[:1])


def test_d01_cutoff_cannot_recover_unclosed_next_open():
    cs,fs=bars([(100,100,100,100),(125,130,100,100)])
    fn=lambda cs,fs,p,params:ScriptDecision(cs,fs,p,params,{0:[order('entry_t1','KAUF_1')]})
    for cutoff in (v.STEP,2*v.STEP-1):
        r=v.run_v1(cs,fs,{},start_ms=0,end_ms=cutoff,decision_fn=fn)
        assert not fills(r) and r['unfilled_end_of_data']==1
    r=v.run_v1(cs,fs,{},start_ms=0,end_ms=2*v.STEP,decision_fn=fn)
    assert len(fills(r))==1 and fills(r)[0]['fill_price']==125


def test_warmup_has_no_orders_or_holdings():
    cs,fs=bars([(100,100,100,100)]*3)
    called=[]
    def fn(cs,fs,p,params):
        called.append(cs[-1].ts)
        assert p.state==sc.PosState.FLAT
        return ScriptDecision(cs,fs,p,params,{0:[order('entry_t1','KAUF_1')]})
    r=v.run_v1(cs,fs,{},start_ms=v.STEP,end_ms=3*v.STEP,decision_fn=fn)
    assert called==[v.STEP,2*v.STEP] and not r['ledger'] and r['btc']==0


def test_fresh_halves_do_not_transfer_pending():
    cs,fs=bars([(100,100,100,100)]*3)
    fn=lambda cs,fs,p,params:ScriptDecision(cs,fs,p,params,{0:[order('entry_t1','KAUF_1')]})
    a=v.run_v1(cs,fs,{},start_ms=0,end_ms=v.STEP,decision_fn=fn)
    b=v.run_v1(cs,fs,{},start_ms=v.STEP,end_ms=3*v.STEP,decision_fn=fn)
    assert a['btc']==b['btc']==0 and not fills(b)


def test_short_scope_rejected():
    cs,fs=bars([(100,100,100,100)])
    try: v.run_v1(cs,fs,{'bias_short':True},start_ms=0,end_ms=v.STEP)
    except ValueError: pass
    else: raise AssertionError('Shorts silently accepted')


def real_decision(rows,pos,**params):
    cs,fs=bars(rows)
    with patch.object(sc,'find_pivots',return_value=[]),patch.object(sc,'confirm_ok',return_value=True):
        return v.decide(cs,fs,pos,dict(tp_ladder=False,buy_ladder=False,rest_halten=True,**params))


def test_h08_real_new_target_reference_never_same_bar_fill():
    p=position()
    d=real_decision([(140,190,90,140)],p)
    assert [(o['action'],o['price']) for o in d.candidates]==[('tp1',170)]
    assert p.state==sc.PosState.FULL and p.retrace_extreme==90
    b=v.Book(0,0,0,1,100)
    pending=b.schedule(d.candidates,140)
    assert b.units==100
    done=[b.fill(o,sc.Candle(v.STEP,130,140,120,130)) for o in pending]
    d.confirm(p,done,b)
    assert p.state==sc.PosState.TP1
    near(b.cash,5200)


def test_real_conflict_buy_ladder_and_tp1_before_priority():
    p=position(sc.PosState.CORE)
    cs,fs=bars([(140,190,90,140)])
    with patch.object(sc,'find_pivots',return_value=[]),patch.object(sc,'confirm_ok',return_value=True):
        d=v.decide(cs,fs,p,dict(tp_ladder=False,buy_ladder=True,rest_halten=True,no_flip=True))
    actions=[o['action'] for o in d.candidates]
    assert 'buy_ladder' in actions and 'tp1' in actions and 'upgrade_full' in actions
    assert p.buy_rungs==0 and p.state==sc.PosState.CORE
    b=v.Book(5000,0,0,1,50)
    pending=b.schedule(d.candidates,140)
    assert [o['action'] for o in pending]==['tp1']
    done=[b.fill(o,sc.Candle(v.STEP,100,100,100,100)) for o in pending]
    with patch.object(sc,'find_pivots',return_value=[]),patch.object(sc,'confirm_ok',return_value=True):
        d.confirm(p,done,b)
    assert p.buy_rungs==0 and p.state==sc.PosState.TP1
    near(b.units,30)


def test_real_rejected_ladder_buy_does_not_consume_rung():
    p=position(sc.PosState.CORE)
    cs,fs=bars([(120,120,110,115)])
    with patch.object(sc,'find_pivots',return_value=[]),patch.object(sc,'confirm_ok',return_value=True):
        d=v.decide(cs,fs,p,dict(tp_ladder=False,buy_ladder=True,rest_halten=True))
        assert [o['action'] for o in d.candidates]==['buy_ladder']
        b=v.Book(0,0,0,1,100)
        assert b.schedule(d.candidates,115)==[]
        d.confirm(p,[],b)
    assert p.buy_rungs==0 and p.state==sc.PosState.CORE


def test_real_partial_buy_confirmation_scales_tranche():
    p=position(sc.PosState.CORE)
    cs,fs=bars([(120,120,110,115)])
    with patch.object(sc,'find_pivots',return_value=[]),patch.object(sc,'confirm_ok',return_value=True):
        d=v.decide(cs,fs,p,dict(tp_ladder=False,buy_ladder=True,rest_halten=True))
        assert [o['action'] for o in d.candidates]==['buy_ladder']
        b=v.Book(100,0,0,1,100); b.alloc=10000
        pending=b.schedule(d.candidates,115)
        done=[b.fill(o,sc.Candle(v.STEP,100,100,100,100)) for o in pending]
        d.confirm(p,done,b)
    assert p.buy_rungs==1
    near(p.entry_pct,101); near(b.units,101)


def test_real_tp_ladder_not_consumed_on_expiry():
    p=position()
    cs,fs=bars([(140,185,120,140)])
    with patch.object(sc,'find_pivots',return_value=[]):
        d=v.decide(cs,fs,p,dict(tp_ladder=True,buy_ladder=False,rest_halten=True))
    assert [o['action'] for o in d.candidates]==['tp_ladder']
    assert p.tp_rungs==0
    b=v.Book(0,0,0,1,100)
    for o in b.schedule(d.candidates,140): b.expire(o,140)
    assert p.tp_rungs==0 and b.units==100


def test_real_e41_observation_advances_without_fill():
    p=position()
    d=real_decision([(100,100,79,79)],p,stop_rueckeroberung=1)
    assert not d.candidates and p.stop_wartet==1 and p.state==sc.PosState.FULL


def test_feedback_before_next_decision_f09_reinvestment():
    cs,fs=entry_fixture()
    cfg=dict(bias_short=False,pivot_n=2,tp_ladder=False,buy_ladder=False)
    seen=[]
    def fn(cs,fs,p,params):
        seen.append((cs[-1].ts,p.state,p.entry_pct))
        return v.decide(cs,fs,p,params)
    r=v.run_v1(cs,fs,cfg,start_ms=0,end_ms=cs[-1].ts+v.STEP,fee=0,decision_fn=fn)
    assert fills(r), 'Must reach real entry/fill'
    first=fills(r)[0]
    assert seen[first['fill_at']//v.STEP][1]!=sc.PosState.FLAT
    assert next(f for f in r['feedback'] if f['at']==first['fill_at'])['btc']>0
    near(next(f for f in r['feedback'] if f['at']==first['fill_at'])['bestand_pct'],25)


def test_real_prefix_knowledge_excludes_future_high_low_and_flow():
    cs,fs=entry_fixture()
    cfg=dict(bias_short=False,pivot_n=2,tp_ladder=False,buy_ladder=False)
    a=v.run_v1(cs,fs,cfg,start_ms=0,end_ms=cs[-1].ts+v.STEP)
    assert fills(a), 'Non-vacuous prefix probe requires real fills'
    more_cs=cs+[sc.Candle(cs[-1].ts+v.STEP,120,900,1,120)]
    more_fs=fs+[sc.FlowPoint(more_cs[-1].ts,-1e12,1e12,1e12,1.)]
    b=v.run_v1(more_cs,more_fs,cfg,start_ms=0,end_ms=more_cs[-1].ts+v.STEP)
    assert a['signals']==[o for o in b['signals'] if o['ts']<=cs[-1].ts]
    assert fills(a)==[e for e in fills(b) if e['fill_at']<=cs[-1].ts]


def test_f09_full_fractional_sales_reset_and_new_cycle_budget():
    # 20% ladder + 40% + 40%: exact fractions of filled peak, floating residue closed.
    r=script([(100,100,100,100)]*6,{0:[order('entry_gp','KAUF_2',pct=100)],
        1:[order('tp_ladder','TEILVERKAUF_LADDER',pct=20)],
        2:[order('tp1','TEILVERKAUF_1',pct=40)],3:[order('tp2','TEILVERKAUF_2',pct=40)],
        4:[order('entry_t1','KAUF_1',pct=25)]},capital=12345.67,fee=.001)
    sales=[e for e in fills(r) if e['action'] not in v.BUY_ACTIONS]
    assert sales[-1]['after']['btc']==0
    near(fills(r)[-1]['gross_budget'],sales[-1]['after']['cash']*.25)


def test_real_full_rest_generated_after_tp1_closes_all_without_phantom_buy():
    p=position()
    cs,fs=bars([(140,210,120,140)])
    with patch.object(sc,'find_pivots',return_value=[]),patch.object(sc,'classify_pattern',return_value=sc.Pattern.DERIVATE_PUMP):
        d=v.decide(cs,fs,p,dict(tp_ladder=True,buy_ladder=False,rest_halten=False))
    assert 'rest_pattern' in [o['action'] for o in d.candidates]
    b=v.Book(0,0,0,1,100)
    pending=b.schedule(d.candidates,140)
    assert [o['action'] for o in pending]==['rest_pattern']
    d.confirm(p,[b.fill(o,sc.Candle(v.STEP,100,100,100,100)) for o in pending],b)
    assert p.state==sc.PosState.FLAT and b.units==0 and p.tp_rungs==0


def test_real_e42_partial_stop_precedes_tp_and_preserves_other_lots():
    p=position(e42_teil_marke=110.)
    cs,fs=bars([(140,230,100,105)])
    with patch.object(sc,'find_pivots',return_value=[]):
        d=v.decide(cs,fs,p,dict(tp_ladder=False,buy_ladder=False,rest_halten=True))
    assert [o['action'] for o in d.candidates]==['part_stop','tp1','tp2']
    b=v.Book(0,0,0,1,100); b.rk_units=25
    pending=b.schedule(d.candidates,105)
    assert pending[0]['action']=='part_stop' and pending[0]['amount']==25
    done=[b.fill(o,sc.Candle(v.STEP,100,100,100,100)) for o in pending]
    assert done[0]['amount']==25 and done[1]['amount']==40 and done[2]['amount']==35
    d.confirm(p,done,b)
    assert b.units==0 and p.state==sc.PosState.FLAT


def test_real_main_stop_keeps_precedence_over_part_stop():
    p=position(e42_teil_marke=110.)
    d=real_decision([(100,200,50,60)],p)
    assert [o['action'] for o in d.candidates]==['stop']
    assert p.state==sc.PosState.FULL and p.e42_teil_marke==110


def test_real_e42_only_part_stop_preserves_base_holdings():
    p=position(e42_teil_marke=110.)
    d=real_decision([(140,140,100,105)],p)
    assert [o['action'] for o in d.candidates]==['part_stop']
    b=v.Book(0,0,0,1,100);b.rk_units=25
    pending=b.schedule(d.candidates,105)
    with patch.object(sc,'find_pivots',return_value=[]):
        d.confirm(p,[b.fill(o,sc.Candle(v.STEP,90,90,90,90)) for o in pending],b)
    near(b.units,75);near(b.cash,2250)
    assert p.state==sc.PosState.FULL and p.e42_teil_marke is None and b.rk_units==0


def test_real_e42_rejected_buy_preserves_unconsumed_mark():
    p=position();p.bestand_pct=50;p.e42_marke=130;p.e42_richtung='LONG'
    p.e42_start_ts=0;p.e42_ausbruch_ts=0
    cs,fs=bars([(130,131,130,131),(131,132,130,131)])
    with patch.object(sc,'find_pivots',return_value=[]):
        d=v.decide(cs,fs,p,dict(tp_ladder=False,buy_ladder=False,rest_halten=True))
        assert [o['action'] for o in d.candidates]==['e42_buy']
        assert p.e42_gekauft is None and p.e42_teil_marke is None and p.e42_marke==130
        b=v.Book(0,0,0,1,100)
        assert b.schedule(d.candidates,131)==[]
        d.confirm(p,[],b)
    assert p.e42_gekauft is None and p.e42_teil_marke is None and p.e42_marke==130


def test_real_e42_fill_confirms_exact_purchased_lot():
    p=position();p.bestand_pct=50;p.e42_marke=130;p.e42_richtung='LONG'
    p.e42_start_ts=0;p.e42_ausbruch_ts=0
    cs,fs=bars([(130,131,130,131),(131,132,130,131)])
    with patch.object(sc,'find_pivots',return_value=[]):
        d=v.decide(cs,fs,p,dict(tp_ladder=False,buy_ladder=False,rest_halten=True))
        assert [o['action'] for o in d.candidates]==['e42_buy']
        b=v.Book(5000,.001,0,1,50);b.invested_pct=50
        pending=b.schedule(d.candidates,131)
        done=[b.fill(o,sc.Candle(2*v.STEP,125,125,125,125)) for o in pending]
        d.confirm(p,done,b)
    near(b.rk_units,1250*.999/125)
    assert p.e42_gekauft==p.e42_teil_marke==130 and p.e42_marke is None


def test_real_conditional_stop_rejection_does_not_activate_hard_stop():
    p=position()
    cs,fs=bars([(100,100,79,79)])
    with patch.object(sc,'find_pivots',return_value=[]),patch.object(sc,'confirm_ok',return_value=True):
        d=v.decide(cs,fs,p,dict(conditional_stop=True,tp_ladder=False,buy_ladder=False))
        assert [o['action'] for o in d.candidates]==['dip']
        b=v.Book(0,0,0,1,100)
        assert b.schedule(d.candidates,79)==[]
        d.confirm(p,[],b)
    assert p.dip_buys==0 and p.state==sc.PosState.FULL
