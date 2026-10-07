"""Synthetic UTC-grid prefix/start/restart cases for the native UM2 engine."""
from copy import deepcopy
from dataclasses import replace
import json
import strategy_core as sc
import execution_v1 as v
from position_state import pos_to_state, pos_from_state
from test_um2_native import aligned, unknown, level_fixture
from test_strategy_core import e13_szenario
from liquidation_evidence import collect_events


def fixture():
    cs,fs=aligned(*e13_szenario())
    for _ in range(3):
        c=replace(cs[-1],ts=cs[-1].ts+v.STEP)
        f=replace(fs[-1],ts=c.ts,provenance={k:dict(m,sample_ts=c.ts,
            available_ts=c.ts+v.STEP,decision_ts=c.ts+v.STEP) for k,m in fs[-1].provenance.items()})
        cs.append(c);fs.append(f)
    return cs,fs,dict(pivot_n=2,bias_short=False,muster5_entry=True,confirm_t1=True)


def test_native_half_start_has_fresh_book_with_indicator_prefix_only():
    cs,fs,cfg=fixture()
    seen=[]
    def decide(c,f,p,params):
        if not seen:
            assert p.state==sc.PosState.FLAT and p.lots==[] and p.buy_rungs==0
            assert len(c)>12 and c[-1].ts==cs[22].ts
        seen.append(c[-1].ts)
        return v.decide(c,f,p,params)
    r=v.run_v1(cs,fs,cfg,start_ms=cs[22].ts,end_ms=cs[-1].ts+v.STEP,decision_fn=decide)
    assert r['equity'][0]['cash']==10000 and r['equity'][0]['btc']==0
    assert all(e['candle_id']>=cs[22].ts for e in r['signals']+r['ledger'])
    assert len(r['equity'])==len(cs)-22


def test_fill_confirmation_keeps_exact_known_prefix_and_serialized_evidence():
    cs,fs,cfg=fixture()
    full=v.run_v1(cs,fs,cfg,start_ms=0,end_ms=cs[-1].ts+v.STEP)
    fill=next(e for e in full['ledger'] if e['status']=='filled')
    cp=v.run_v1(cs,fs,cfg,start_ms=0,end_ms=cs[-1].ts+v.STEP,
                checkpoint_at=fill['candle_id'])['checkpoint']
    saved=json.loads(json.dumps(cp))
    assert saved['decision']['candles'][-1]['ts']==fill['candle_id']
    assert saved['decision']['flow'][-1]['ts']==fill['candle_id']
    assert v.resume_v1(cs,fs,saved)==full
    a=v.Decision.from_state(saved['decision']);b=v.Decision.from_state(saved['decision'])
    pos1=pos_from_state(saved['position']);pos2=pos_from_state(saved['position'])
    book1=v.Book.from_state(saved['book']);book2=v.Book.from_state(saved['book'])
    idx=next(i for i,c in enumerate(cs) if c.ts==fill['fill_at'])
    executed1=[book1.fill(o,cs[idx]) for o in saved['pending']]
    # Unknown/violent future flow has no route into the already-stored decision.
    future=unknown(fs,idx)
    future[idx]=replace(future[idx],long_liq=1e99,spot_cvd=1e99,oi=1e99)
    executed2=[book2.fill(o,cs[idx]) for o in saved['pending']]
    a.confirm(pos1,executed1,book1);b.confirm(pos2,executed2,book2)
    assert pos_to_state(pos1)==pos_to_state(pos2) and a.to_state()==b.to_state()
    assert a.flow==fs[:len(a.flow)] and future[idx].ts>a.flow[-1].ts


def test_native_gates_reject_absent_negative_nonfinite_and_bool_time_both_sides():
    cs,fs=level_fixture()
    for field in ('long_liq','short_liq'):
        for bad in (-1,float('nan'),float('inf')):
            f=deepcopy(fs);f[-1]=replace(f[-1],**{field:bad})
            assert sc.liq_levels(cs,f,'long')==[] and not sc.liq_cascade(f,'short')
        for key in ('sample_ts','available_ts','decision_ts','age_ms'):
            f=deepcopy(fs);f[-1].provenance[field][key]=True
            assert sc.liq_levels(cs,f,'short')==[]
        f=deepcopy(fs);del f[-1].provenance[field]
        assert sc.liq_levels(cs,f,'long')==[]


def test_gate_diagnostics_are_context_local_and_restore_on_exception():
    cs,fs=level_fixture()
    try:
        with collect_events() as outer:
            sc.liq_levels(cs,unknown(fs,-1),'long')
            with collect_events() as inner:
                sc.liq_levels(cs,unknown(fs,-1),'short')
            assert len(outer)==len(inner)==1
            raise RuntimeError('synthetic')
    except RuntimeError: pass
    with collect_events() as fresh:
        assert sc.liq_levels(cs,fs,'long')
    assert fresh==[]
