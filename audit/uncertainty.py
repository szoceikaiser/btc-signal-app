"""Prespecified paired moving-block sensitivity; fixed-parameter time folds."""
import json,math,random
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'

def main():
    cases=json.loads((OUT/'e42-faelle.json').read_text())
    # Exclude unfinished final candle and reuse independent cash paths.
    raw=json.loads((ROOT/'docs/e445/eingaben.json').read_text())
    paths={k:[v for v in rows if v['ts']+14400000<=raw['ende']] for k,rows in cases['portfolio_paths'].items()}
    logs={}
    for key,rows in paths.items():
        prev=10000.;values=[]
        for row in rows:values.append(math.log(row['equity']/prev));prev=row['equity']
        logs[key]=values
    n=len(logs['baseline']);rng=random.Random(270926)
    result=dict(seed=270926,draws=2000,bars=n,confidence='percentile 95%; descriptive conditional uncertainty, no untouched test and no multiple-search-adjusted proof',blocks=[])
    for days in (7,28):
        length=days*6;values=[];log_spreads=[]
        for _ in range(2000):
            indices=[]
            while len(indices)<n:
                a=rng.randrange(n-length+1)
                indices.extend(range(a,a+length))
            indices=indices[:n]
            a=sum(logs['e42'][i] for i in indices);b=sum(logs['baseline'][i] for i in indices)
            values.append(100*(math.exp(a)-math.exp(b)));log_spreads.append(a-b)
        values.sort();log_spreads.sort()
        result['blocks'].append(dict(days=days,nonoverlapping_blocks_approx=n/length,
            difference_return_pp_95=[values[49],values[1949]],median=values[999],
            fraction_positive=sum(x>0 for x in values)/len(values)))
    folds=[]
    for p in sorted((OUT/'grid').glob('V*.json')):
        row=json.loads(p.read_text())
        if not row['scenarios']:continue
        last=10000.;months={}
        for m,end in row['scenarios'][0]['month_ends'].items():
            months[m]=100*(end/last-1);last=end
        folds.append(dict(id=row['id'],months={m:v for m,v in months.items() if '2026-05'<=m<='2026-09'}))
    result['fixed_parameter_walk_forward']=dict(
        definition='Expanding available history, immutable parameters, continuous position/cash carried into each monthly evaluation fold. May, June, July, August, September (partial). No retraining or winning-parameter selection. Retrospective walk-forward consistency only: all data already used by developers.',rows=folds)
    (OUT/'unsicherheit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result['blocks'],indent=2))

if __name__=='__main__':main()
