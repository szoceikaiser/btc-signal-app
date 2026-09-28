"""Counterexamples, independent expected amounts, and data integrity evidence.

This records confirmed failures of production requirements as findings, rather than
changing production defaults or pretending the original test suite tested them.
"""
import dataclasses
import json
import math
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'
sys.path.insert(0,str(ROOT/'engine'))
import backtest as bt
import strategy_core as sc
import main as live
from book import account,selfcheck
from tolerance import corrected_simulate

def main():
    evidence={}
    raw=json.loads((ROOT/'docs/e445/eingaben.json').read_text())
    cs=[sc.Candle(**c) for c in raw['candles']]
    fl=[sc.FlowPoint(**f) for f in raw['flow']]
    step=14400000
    invalid=[i for i,c in enumerate(cs) if not(c.low<=c.open<=c.high and c.low<=c.close<=c.high)]
    gaps=[dict(a=a.ts,b=b.ts,delta=b.ts-a.ts) for a,b in zip(cs,cs[1:]) if b.ts-a.ts!=step]
    unfinished=[dataclasses.asdict(c) for c in cs if c.ts+step>raw['ende']]
    evidence['D01_inputs']=dict(candles=len(cs),flow=len(fl),gaps=gaps,invalid_ohlc=invalid,
        aligned=all(c.ts==f.ts for c,f in zip(cs,fl)),duplicates=len(cs)-len({c.ts for c in cs}),
        unfinished=unfinished,recorded_end=raw['ende'],
        funding_zeros=sum(f.funding==0 for c,f in zip(cs,fl) if c.ts>=raw['start']),
        nonfinite=sum(not math.isfinite(v) for f in raw['flow'] for v in f.values()))
    assert len(unfinished)==1 and not invalid and not gaps

    # An actual cash investment of 10,000 is worth 5,000 before the closing sale.
    c=[sc.Candle(0,100,100,100,100),sc.Candle(step,100,100,50,100)]
    s=[dict(ts=0,type='KAUF_1',price=100,tranche_pct=100),
       dict(ts=step,type='STOPLOSS',price=100,tranche_pct=100)]
    r=bt.simulate(s,c,fee=0,start_ms=0)
    expected=100*(5000/10000-1)
    evidence['F01_dd_sale_before_low']=dict(production=r['max_drawdown_pct'],expected=expected,
                                           signals=s,candles=[dataclasses.asdict(x) for x in c])
    assert r['max_drawdown_pct']==0 and expected==-50

    # Two deterministic signals are enough to falsify the advertised unlevered cap.
    short=[dict(ts=0,type='SHORT_1',price=100,tranche_pct=100),
           dict(ts=step,type='SHORT_NACHLEGEN',price=100,tranche_pct=100)]
    cc=[sc.Candle(0,100,100,100,100),sc.Candle(step,100,100,100,100),
        sc.Candle(2*step,100,100,90,90)]
    sr=bt.simulate(short,cc,fee=0,start_ms=0)
    evidence['F02_short_margin']=dict(production_return=sr['rendite_pct'],
                                      unlevered_max_return=10,implied_exposure_pct=200)
    assert sr['rendite_pct']==20

    z=sc.fib_zones(sc.Impulse(sc.Pivot(0,0,80,'L'),sc.Pivot(1,step,160,'H')))
    p=sc.Position(direction='LONG',state=sc.PosState.TP1,zones=z,retrace_extreme=100,
                  entry_ref=100,entry_pct=100,bestand_pct=50)
    low=sc.Pivot(0,0,115,'L')
    kwargs=dict(trail_stop=True,tp_ladder=False,buy_ladder=False,rest_halten=True,
                bias_short=False,high_exit='off')
    with patch.object(sc,'find_pivots',return_value=[low]):
        a=sc.evaluate([sc.Candle(2*step,120,121,119,120)],[],p,**kwargs)
        # This pivot is now the selected stop (max of 80,100,115). It is not persisted.
        b=sc.evaluate([sc.Candle(3*step,120,121,109,110)],[],p,**kwargs)
    evidence['F03_trail_can_fall']=dict(prior_stop=115,next_close=110,new_computed_stop=100,
                                      first_signals=[x.to_dict() for x in a],
                                      next_signals=[x.to_dict() for x in b],state=p.state.value)
    assert not a and not b and p.state==sc.PosState.TP1
    with patch.object(live,'find_pivots',return_value=[low]):
        plan=live.positions_plan([sc.Candle(2*step,120,121,119,120)],[],kwargs,p)
    evidence['F10_plan_stop']=dict(engine_stop_before_drop=115,telegram_plan_stop=plan['stop'])
    assert plan['stop']['preis']==100

    z2=sc.fib_zones(sc.Impulse(sc.Pivot(0,0,20,'L'),sc.Pivot(1,step,420,'H')))
    p2=sc.Position(direction='LONG',state=sc.PosState.T1,zones=z2,retrace_extreme=220,
                   entry_ref=220,entry_pct=25,bestand_pct=25)
    sig=sc.evaluate([sc.Candle(3*step,185,190,z2.gp_upper-1,185)],
                    [sc.FlowPoint(3*step,0,0,1,0)],p2,
                    buy_ladder=False,tp_ladder=False,high_exit='off',bias_short=False)
    assert [x.type for x in sig]==[sc.SignalType.KAUF_2]
    correct=75/(25/220+50/z2.gp_upper)
    evidence['F04_entry_average']=dict(production=p2.entry_ref,capital_weighted_cost_per_coin=correct,
                                      first_price=220,second_price=z2.gp_upper,
                                      capital_amounts=[25,50],fee_excluded=True)
    assert abs(correct-p2.entry_ref)>1

    saved=live.pos_to_state(sc.Position(widerstand_exits=1))
    restored=live.pos_from_state(saved)
    evidence['F05_state_missing']=dict(field='widerstand_exits',before=1,after=restored.widerstand_exits)
    assert restored.widerstand_exits==0
    evidence['F11_config_types']=dict(string_false=live.eval_params({'bias_short':'false'})['bias_short'])
    assert evidence['F11_config_types']['string_false'] is True

    candles=[sc.Candle(i*step,100+i,101+i,99+i,100+i) for i in range(12)]
    flows=[sc.FlowPoint(i*step,100000+i*10,100+i*30,100+i*.4,.00001+i*.000001) for i in range(12)]
    shifted=[dataclasses.replace(f,fut_cvd=f.fut_cvd+1000000) for f in flows]
    evidence['F06_cvd_offset']=dict(original=sc.classify_pattern(candles,flows).name,
        shifted=sc.classify_pattern(candles,shifted).name,
        corrected_original=sc.classify_pattern(candles,flows,muster_cvd='usd').name,
        corrected_shifted=sc.classify_pattern(candles,shifted,muster_cvd='usd').name)
    assert evidence['F06_cvd_offset']['original']!=evidence['F06_cvd_offset']['shifted']
    assert evidence['F06_cvd_offset']['corrected_original']==evidence['F06_cvd_offset']['corrected_shifted']

    k=[[i*step,100,101,99,100,1,(i+1)*step-1,100,1,1,50,0] for i in range(2)]
    c,f=bt.build_series(k,[],oi_map={2*step:12345})
    evidence['F07_future_fallback']=dict(first_candle=c[0].ts,first_oi_time=2*step,
                                         value_in_past=f[0].oi)
    assert f[0].oi==12345

    day=sc.resample_daily([sc.Candle(0,100,101,99,100),sc.Candle(step,100,102,99,102)])
    evidence['F08_partial_daily']=dict(hours_observed=8,returned_daily_bars=len(day),
                                       returned_close=day[-1].close)
    assert len(day)==1

    source=sc.find_pivots
    for n in (2,5):
        wave=[sc.Candle(i*step,100,100+(10 if i==10 else 0),90,95) for i in range(30)]
        for end in range(1,len(wave)+1):
            assert all(p.idx<=end-n-1 for p in source(wave[:end],n))
    evidence['P01_pivot_confirmation']='PASS: no pivot is returned before n right-hand bars'

    all_sigs=json.loads((ROOT/'docs/e445/signale.json').read_text())
    all_evidence={}
    for label,ss in all_sigs.items():
        rr=account(ss,cs,raw['start'])
        ref=bt.simulate(ss,cs,start_ms=raw['start'])
        tol=corrected_simulate(bt)(ss,cs,start_ms=raw['start'])
        assert abs(rr['end']-tol['ende'])<.011,(label,rr['end'],tol['ende'])
        cm={c.ts:c for c in cs}
        bad=[dict(s,low=cm[s['ts']].low,high=cm[s['ts']].high) for s in ss
             if s['type']!='WARNUNG' and not cm[s['ts']].low<=s['price']<=cm[s['ts']].high]
        all_evidence[label]=dict(end=rr['end'],production_end=ref['ende'],tolerance_end=tol['ende'],
                                 difference_usd=rr['end']-ref['ende'],
                                 impossible_ohlc_fills=bad,zero_orders=rr['zero_orders'],
                                 fees=rr['fees'],orders=rr['orders'],cycles=rr['cycles'],
                                 original_dd=ref['max_drawdown_pct'],dd_close=rr['dd_close_pct'])
    evidence['P02_independent_reconciliation']=all_evidence
    evidence['F09_float_dust']=dict(description='Exact units == 0 check leaves a 2.78e-17 BTC remainder after a nominal full partial sale on 2026-04-06. Next purchase incorrectly keeps the old allocation and peak BTC. See debug_book.py.',
        affected={k:v['difference_usd'] for k,v in all_evidence.items() if abs(v['difference_usd'])>.011})
    selfcheck()
    try: selfcheck(sabotage=True)
    except AssertionError: evidence['P03_independent_oracle_sabotage']='CAUGHT'
    else: raise AssertionError('Independent checker did not detect omitted fee')
    (OUT/'gegenproben.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in evidence.items() if k!='P02_independent_reconciliation'},ensure_ascii=False,indent=2))
    print('Independent reconciliation: all 9 portfolios match after isolated F09 tolerance correction within 0.011 USD; originals retained separately')

if __name__=='__main__': main()
