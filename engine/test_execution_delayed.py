"""Independent hand cases and real causal prefix tests for offline i+2."""
from copy import deepcopy
from unittest.mock import patch
import execution_delayed as d
import execution_v1 as v
import strategy_core as sc
from test_execution_v1 import bars, order, ScriptDecision, entry_fixture, fills, near


def scripted(rows, by_bar, **kw):
    cs, fs = bars(rows)
    return d.run_delayed(cs, fs, {}, start_ms=0, end_ms=len(cs)*v.STEP,
        decision_fn=lambda cs,fs,p,params: ScriptDecision(cs,fs,p,params,by_bar), **kw)


def test_i2_buy_waits_and_does_not_own_waiting_low():
    r = scripted([(100,100,100,100),(200,200,1,200),(125,150,125,150)],
        {0:[order('entry_t1','KAUF_1')]}, fee=0, slippage=0)
    assert fills(r)[0]['fill_at'] == 2*v.STEP
    near(r['btc'],80); near(r['dd_intrabar_upper_pct'],100*(1-125/150))
    assert r['equity'][1]['btc'] == 0
    assert r['waiting'][0]['reserved_cash'] == 10000


def test_i2_sell_keeps_waiting_risk_and_gap():
    r = scripted([(100,100,100,100)]*3+[(100,150,50,90),(70,70,70,70)],
        {0:[order('entry_t1','KAUF_1')],2:[order('stop','STOPLOSS')]}, fee=0, slippage=0)
    near(r['cash'],7000)
    near(r['dd_close_pct'],30)
    near(r['dd_intrabar_lower_pct'],max(.5,1-70/150)*100)
    near(r['dd_intrabar_upper_pct'],(1-50/150)*100)
    assert fills(r)[1]['fill_at'] == 4*v.STEP
    assert r['waiting'][-1]['reserved_btc'] == 100


def test_i2_no_intermediate_decision_and_feedback_first():
    cs,fs=bars([(100,100,100,100)]*4)
    seen=[]
    def fn(cs,fs,p,params):
        seen.append((cs[-1].ts,len(cs),p.state))
        return ScriptDecision(cs,fs,p,params,{0:[order('entry_t1','KAUF_1')],1:[order('stop','STOPLOSS')]})
    r=d.run_delayed(cs,fs,{},start_ms=0,end_ms=4*v.STEP,decision_fn=fn)
    assert [x[0] for x in seen] == [0,2*v.STEP,3*v.STEP]
    assert seen[1][1] == 3 and seen[1][2] != sc.PosState.FLAT
    assert len(fills(r)) == 1 and r['waiting'][0]['pending'][0]['amount'] == 10000


def test_i2_end_no_replacement_fill_or_consumed_state():
    for n in (1,2):
        r=scripted([(100,100,100,100)]*n,{0:[order('entry_t1','KAUF_1')]})
        assert not fills(r) and r['unfilled_end_of_data']==1
        assert r['btc']==r['reserved_cash']==0 and r['cash']==10000
        assert r['position_state']['pos_state'] == 'FLAT'
        assert r['ledger'][-1]['event_at']==n*v.STEP


def test_i2_gap_rejected_even_with_pending():
    cs,fs=bars([(100,100,100,100)]*4)
    try:
        d.run_delayed([cs[0],*cs[2:]],[fs[0],*fs[2:]],{},start_ms=0,end_ms=4*v.STEP)
    except ValueError as e: assert 'data_gap' in str(e)
    else: raise AssertionError('gap accepted')


def test_i2_cutoff_rejects_running_fill_bar():
    cs,fs=bars([(100,100,100,100)]*3)
    r=d.run_delayed(cs,fs,{},start_ms=0,end_ms=3*v.STEP-1,
        decision_fn=lambda cs,fs,p,params:ScriptDecision(cs,fs,p,params,{0:[order('entry_t1','KAUF_1')]}))
    assert not fills(r) and len(r['equity'])==2


def test_i2_roundtrip_costs():
    for slip in (.001,.005):
        r=scripted([(100,100,100,100)]*5,
            {0:[order('entry_t1','KAUF_1')],2:[order('stop','STOPLOSS')]},fee=.001,slippage=slip)
        near(r['cash'],10000*.999/(1+slip)*(1-slip)*.999)
        assert len(fills(r))==2


def test_i2_priority_and_partial_cash_reservations():
    r=scripted([(100,100,100,100)]*5,{0:[order('entry_t1','KAUF_1',pct=75),
        order('entry_gp','KAUF_2',pct=75)],2:[order('stop','STOPLOSS'),order('entry_t1','KAUF_1')]},fee=0,slippage=0)
    assert [f['gross_budget'] for f in fills(r)[:2]] == [7500,2500]
    assert len(fills(r))==3 and fills(r)[-1]['type']=='STOPLOSS'
    near(r['cash'],10000)


def test_i2_real_prefix_future_and_waiting_fields_cannot_change_reserved_fill():
    cs,fs=entry_fixture()
    cfg=dict(pivot_n=2,bias_short=False,tp_ladder=False,buy_ladder=False)
    end=cs[-1].ts+v.STEP
    a=d.run_delayed(cs,fs,cfg,start_ms=0,end_ms=end)
    assert fills(a) and a['waiting']
    first=fills(a)[0]
    changed_cs,changed_fs=deepcopy(cs),deepcopy(fs)
    j=first['fill_at']//v.STEP-1
    c=changed_cs[j]
    changed_cs[j]=sc.Candle(c.ts,c.open,1e6,1,c.close)
    f=changed_fs[j]
    changed_fs[j]=sc.FlowPoint(f.ts,1e15,-1e15,1e15,1.)
    b=d.run_delayed(changed_cs,changed_fs,cfg,start_ms=0,end_ms=end)
    assert fills(b)[0] == first
    more_cs=cs+[sc.Candle(end,120,1e6,1,120)]
    more_fs=fs+[sc.FlowPoint(end,1e15,-1e15,1e15,1.)]
    ext=d.run_delayed(more_cs,more_fs,cfg,start_ms=0,end_ms=end+v.STEP)
    assert fills(a)==[e for e in fills(ext) if e['fill_at']<end]
    assert a['signals']==[s for s in ext['signals'] if s['ts']<end]


def test_i2_real_no_decide_during_wait_and_cost_feedback():
    cs,fs=entry_fixture()
    seen=[]
    def fn(cs,fs,p,params):
        seen.append((cs[-1].ts,deepcopy(p.lots),p.entry_ref))
        return v.decide(cs,fs,p,params)
    r=d.run_delayed(cs,fs,dict(pivot_n=2,bias_short=False),start_ms=0,
        end_ms=cs[-1].ts+v.STEP,decision_fn=fn)
    assert fills(r)
    for e in fills(r):
        assert e['candle_id']+v.STEP not in [s[0] for s in seen]
        at=next(s for s in seen if s[0]==e['fill_at'])
        assert at[1]==e['after']['lots']


def test_i2_warmup_does_not_trade():
    r=scripted([(100,100,100,100)]*3,{})
    assert r['cash']==10000 and not r['ledger']
    cs,fs=entry_fixture()
    start=cs[-2].ts
    r=d.run_delayed(cs,fs,dict(pivot_n=2,bias_short=False),start_ms=start,end_ms=cs[-1].ts+v.STEP)
    assert all(s['ts']>=start for s in r['signals']) and not fills(r)


def test_i2_last_reserved_sale_rounding_does_not_create_micro_short():
    units=.014829911889147264
    amount=.014829911889147266
    lot=dict(id='e42',at=0,fill_price=69886.26645,units=amount,
        cost=1037.4446183333018,buy_fee=1.0374446183333017,kind='e42')
    b=d.DelayedBook(9395.890008018921,.001,.001,1.,units,[lot])
    b.peak_units=.03707477972286816;b.reserved_units=units
    o=dict(order('tp1','TEILVERKAUF_1',pct=40),ts=0,sequence=0,id='rounding',amount=amount,requested=amount)
    saved=deepcopy(o)
    b.fill(o,sc.Candle(2*v.STEP,73027.02,75785.82,73027.02,74510.77))
    assert o==saved and b.units==b.rk_units==b.reserved_units==0 and b.lots==[]
    near(b.cash,9395.890008018921+units*73027.02*.999*.999)
    assert b.ledger[-1]['numerical_btc_cap']==amount-units


def test_i2_real_oversale_is_rejected_not_clipped():
    b=d.DelayedBook(0,0,0,1.,1.)
    o=dict(order('tp1','TEILVERKAUF_1'),ts=0,sequence=0,id='oversale',amount=1.01,requested=1.01)
    try:b.fill(o,sc.Candle(2*v.STEP,100,100,100,100))
    except ValueError:pass
    else:raise AssertionError('Material oversale accepted')
    assert b.units==1 and b.cash==0 and not b.ledger
