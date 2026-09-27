"""Record production vs independent cash after each executed order."""
import json,sys
from pathlib import Path
from book import account,BUY,SELL
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import backtest as bt
import strategy_core as sc
raw=json.loads((ROOT/'docs/e445/eingaben.json').read_text())
cs=[sc.Candle(**c) for c in raw['candles']]
rows=json.loads((ROOT/'docs/e445/signale.json').read_text())
label='LIVE-heute +Rest halten (E43.6)'
ss=rows[label]
trace=[]
def tracer(frame,event,arg):
    if frame.f_code is bt.simulate.__code__ and event=='line' and frame.f_lineno==1070:
        loc=frame.f_locals
        if loc['s']['type'] in BUY|SELL:
            trace.append({k:loc[k] for k in ('s','cash','units','alloc','peak_units')})
    return tracer
sys.settrace(tracer)
ref=bt.simulate(ss,cs,start_ms=raw['start'])
sys.settrace(None)
rr=account(ss,cs,raw['start'])
for i,(a,b) in enumerate(zip(trace,rr['fills'])):
    if abs(a['cash']-b['cash_after'])>.000001:
        print(json.dumps(dict(first_divergence=i,prior_production=trace[i-2:i],production=a,
                              independent=rr['fills'][i-2:i+1]),indent=2))
        break
