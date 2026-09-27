"""Preregistered frozen-input grid. Cache every completed row; no live/network calls."""
import hashlib,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
from book import account,selfcheck
from tolerance import corrected_simulate
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'
RUN=OUT/'grid'
RUN.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'engine'))
import backtest as bt
import strategy_core as sc

def compact(book):
    return {k:v for k,v in book.items() if k not in ('fills','lots','path')}

def main():
    selfcheck()
    plan=json.loads((OUT/'gitter-plan.json').read_text())
    data=ROOT/'docs/e445/eingaben.json'
    assert hashlib.sha256(data.read_bytes()).hexdigest()==plan['input_sha256']
    raw=json.loads(data.read_text())
    keep=[i for i,c in enumerate(raw['candles']) if c['ts']+14400000<=raw['ende']]
    cs=[sc.Candle(**raw['candles'][i]) for i in keep]
    flow=[sc.FlowPoint(**raw['flow'][i]) for i in keep]
    mid=raw['start']+(raw['ende']-raw['start'])//2
    tolerance=corrected_simulate(bt)
    for row in plan['rows']:
        dest=RUN/(row['id']+'.json')
        if dest.exists(): continue
        tick=time.monotonic()
        sig=bt.run_backtest(cs,flow,row['params'],start_ms=raw['start'],diagnose_e445=True)
        long_only=not any(s['type'].startswith('SHORT') for s in sig)
        original=bt.simulate(sig,cs,start_ms=raw['start'])
        corrected=tolerance(sig,cs,start_ms=raw['start']) if long_only else None
        scenarios=[]
        for scenario in plan['costs']:
            if long_only:
                book=account(sig,cs,raw['start'],fee=scenario['fee'],slip=scenario['slip'],mode=scenario['fill'])
                scenarios.append(dict(scenario=scenario,**compact(book)))
                if scenario['fill']=='level':
                    assert abs(book['end']-corrected['ende'])<.011,(row['id'],book['end'],corrected['ende'])
        halves=[]
        for start,end in ((raw['start'],mid),(mid,raw['ende'])):
            count=sum(c.ts<=end for c in cs)
            hcs,hfl=cs[:count],flow[:count]
            hs=bt.run_backtest(hcs,hfl,row['params'],start_ms=start)
            hp=bt.simulate(hs,hcs,start_ms=start)
            hb=account(hs,hcs,start) if not any(s['type'].startswith('SHORT') for s in hs) else None
            halves.append(dict(start=start,end=end,original_return=hp['rendite_pct'],
                               independent=compact(hb) if hb else None))
        result=dict(**row,run_id='audit-20260927-04-'+row['id'],input_sha256=plan['input_sha256'],
                    candles=len(cs),start=raw['start'],last_open=cs[-1].ts,mid=mid,
                    long_only=long_only,signals=sig,original=original,tolerance=corrected,
                    scenarios=scenarios,halves=halves,seconds=time.monotonic()-tick)
        dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(row['id'],row['diff'],'original',original['rendite_pct'],
              'independent',round(scenarios[0]['return_pct'],4) if scenarios else 'SHORT-MARGIN-INVALID',
              'seconds',round(result['seconds'],1),flush=True)

if __name__=='__main__': main()
