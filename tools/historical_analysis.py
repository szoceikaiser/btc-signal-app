"""Fixed R0 pair: five cases, continuous periods, two prescribed fresh starts.

Execute only after plan.json freezes source/code/method/version hashes. Network
is disabled during evaluation. No strategy selection or U2 family measurements.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import socket
import sys
import numpy as np
from verify_4 import independent_costs, near, bt, sc
from historical_stats import daily_pair, paired_bootstrap, stationary_indices
from execution_delayed import run_delayed

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/nach-6'
STEP=14400000


def digest(raw): return hashlib.sha256(raw).hexdigest()
def canonical(obj): return json.dumps(obj,sort_keys=True,allow_nan=False).encode()
def dump(path,obj): path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def utc(t): return datetime.fromtimestamp(t/1000,timezone.utc).isoformat()


def verify_account(result, book, candles, start, offset):
    orders={f"v1:{s['ts']}:{s['sequence']}":s for s in result['signals']}
    chosen=[orders[e['order_id']] for e in result['ledger'] if e['status']=='scheduled']
    other=book.account(chosen,candles,start,fee=.001,slip=result['slippage_pct']/100,
        mode='next_open' if offset==1 else 'delay_4h')
    for a,b in [(result['ende'],other['end']),(result['fees'],other['fees']),
        (result['dd_close_pct'],-other['dd_close_pct']),
        (result['dd_intrabar_upper_pct'],-other['dd_intrabar_range_pct'][0]),
        (result['dd_intrabar_lower_pct'],-other['dd_intrabar_range_pct'][1])]: near(a,b)
    fills=[e for e in result['ledger'] if e['status']=='filled']
    expected=[f for f in other['fills'] if f['units']>1e-15]
    assert len(fills)==len(expected)
    for a,b in zip(fills,expected):
        assert a['fill_at']==b['execution_ts']==a['candle_id']+offset*STEP
        for x,y in [('quantity','units'),('fill_price','price'),('fee','fee')]:near(a[x],b[y])
        near(a['before']['cash'],b['cash_before']);near(a['after']['cash'],b['cash_after'])
    assert len(result['equity'])==len(other['path'])
    for a,b in zip(result['equity'],other['path']):
        assert a['candle_id']==b['ts']
        for x,y in [('cash','cash'),('btc','units'),('equity','equity')]:near(a[x],b[y])
    for month,p in result['month_ends'].items():near(p['equity'],other['month_ends'][month])
    assert result['unfilled_end_of_data']==len(other['unexecuted'])
    return dict(costs=independent_costs(result), audit_book=True,
        fills=len(fills), closes=len(other['path']), cycles=other['cycles'],
        avg_exposure_pct=other['avg_exposure_pct'], turnover=other['turnover'])


def risk_paths(result, candles):
    """Independent valuation event path incl. old/new holdings at same open.

    Record peak/trough for maximal drawdown and peak-to-recovery episodes.
    Low/high paths are bounds, not claims about observed intrabar order.
    """
    by=defaultdict(list)
    for e in result['ledger']:
        if e['status']=='filled':by[e['fill_at']].append(e)
    paths=[[],[],[]]
    cash,units=10000.,0.
    for c in candles:
        for j in (1,2):paths[j].append((c.ts,cash+units*c.open,'pre_open'))
        for e in by[c.ts]:
            cash,units=e['after']['cash'],e['after']['btc']
            for j in (1,2):paths[j].append((c.ts,cash+units*c.open,'post_fill'))
        for j,seq in [(1,[(c.low,'low'),(c.high,'high'),(c.close,'close')]),
                      (2,[(c.high,'high'),(c.low,'low'),(c.close,'close')])]:
            paths[j].extend((c.ts+STEP,cash+units*p,label) for p,label in seq)
        paths[0].append((c.ts+STEP,cash+units*c.close,'close'))
    return paths


def drawdown(events, start_value, start_at):
    peak=start_value;peak_at=start_at;worst=0.;peak_label='start'
    max_phase=None;episodes=[];episode=None
    for at,val,label in events:
        if val>=peak:
            if episode:
                episode['recovered_at']=at
                episodes.append(episode);episode=None
            peak=val;peak_at=at;peak_label=label
        loss=1-val/peak
        if loss>0 and (episode is None or loss>episode['dd_pct']/100):
            episode=dict(peak_at=peak_at,peak_event=peak_label,trough_at=at,
                trough_event=label,dd_pct=loss*100,recovered_at=None)
        if loss>worst:
            worst=loss;max_phase=dict(episode)
    if episode:episodes.append(episode)
    return dict(dd_pct=worst*100, maximum=max_phase,
        largest_episodes=sorted(episodes,key=lambda e:e['dd_pct'],reverse=True)[:3])


def describe(result, candles, verification):
    rows=result['equity'];active=[c for c in candles if c.ts>=rows[0]['candle_id']]
    paths=risk_paths(result,active)
    risks=[drawdown(p,10000.,active[0].ts) for p in paths]
    for r,key in zip(risks,['dd_close_pct','dd_intrabar_lower_pct','dd_intrabar_upper_pct']):near(r['dd_pct'],result[key])
    periods=[]
    n=len(rows)
    groups=[]
    months=defaultdict(list)
    for i,r in enumerate(rows):months[utc(r['at']-1)[:7]].append(i)
    groups.extend(('month',key,min(v),max(v)+1) for key,v in months.items())
    bounds=[0,n//3,2*n//3,n]
    groups.extend(('third',str(i+1),a,b) for i,(a,b) in enumerate(zip(bounds,bounds[1:])))
    for kind,label,a,b in groups:
        initial=10000. if a==0 else rows[a-1]['equity']
        lo,hi=rows[a]['candle_id'],rows[b-1]['at']
        # Intrabar event time at prior close equals this interval's open.
        # Select by candle slice, avoiding boundary ambiguity in event labels.
        segment_paths=[[] for _ in range(3)]
        selected=set(r['candle_id'] for r in rows[a:b])
        for j,path in enumerate(paths):
            segment_paths[j]=[(t,val,lab) for t,val,lab in path
                if (t if lab in ('pre_open','post_fill') else t-STEP) in selected]
        periods.append(dict(kind=kind,label=label,start_ms=lo,end_ms=hi,bars=b-a,
            partial_month=kind=='month' and (utc(lo)[8:19]!='01T00:00:00' or utc(hi)[8:19]!='01T00:00:00'),
            start_equity=initial,end_equity=rows[b-1]['equity'],
            usd_contribution=rows[b-1]['equity']-initial,
            return_pct=(rows[b-1]['equity']/initial-1)*100,
            section_dd_pct=[drawdown(p,initial,lo)['dd_pct'] for p in segment_paths],
            fees=sum(e['fee'] for e in result['ledger'] if e['status']=='filled' and lo<=e['fill_at']<hi),
            cash=rows[b-1]['cash'],btc=rows[b-1]['btc'],cost_basis=rows[b-1]['cost_basis'],
            avg_exposure_pct=100*sum(1-r['cash']/r['equity'] for r in rows[a:b])/(b-a)))
    return dict(**{k:result[k] for k in ['model','ende','rendite_pct','fees','cash','btc','cost_basis',
        'cost_entry','dd_close_pct','dd_intrabar_lower_pct','dd_intrabar_upper_pct','unfilled_end_of_data']},
        start_ms=active[0].ts,end_ms=active[-1].ts+STEP,
        verification=verification,periods=periods,risk_phases=risks,
        final_exposure_pct=100*(1-result['cash']/result['ende']),
        result_sha256=digest(canonical(result)))


def compare(b,k):
    delta=k['ende']-b['ende']
    def dominates(a,z):
        diffs=[a['ende']-z['ende'],z['dd_close_pct']-a['dd_close_pct'],z['dd_intrabar_upper_pct']-a['dd_intrabar_upper_pct']]
        eps=[.01,1e-8,1e-8]
        return all(x>=-e for x,e in zip(diffs,eps)) and any(x>e for x,e in zip(diffs,eps))
    return dict(delta_usd=delta,A_window=k['ende']/b['ende']-1,
        delta_dd_close_pp=k['dd_close_pct']-b['dd_close_pct'],
        delta_dd_upper_pp=k['dd_intrabar_upper_pct']-b['dd_intrabar_upper_pct'],
        dominance='basis' if dominates(b,k) else 'E42' if dominates(k,b) else 'tradeoff_or_tie')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--inputs',type=Path,default=ROOT.parent/'audit-backups/6-abschluss-05208ce/eingefrorene-inputs')
    parser.add_argument('--out',type=Path,default=DOC)
    parser.add_argument('--package',choices=['R0','R1'],default='R0')
    args=parser.parse_args()
    plan=json.loads((DOC/'plan.json').read_text(encoding='utf-8'))
    assert np.__version__==plan['numpy_version']
    for name,h in plan['files'].items():assert digest((ROOT/name).read_bytes().replace(b'\r\n',b'\n'))==h,name
    def blocked(*a,**kw):raise AssertionError('Network prohibited in analysis')
    socket.socket.connect=socket.create_connection=blocked
    package=plan['packages'][args.package]
    raw=(args.inputs/'eingaben.json').read_bytes() if args.package=='R0' else (DOC/'r1-inputs.json').read_bytes()
    assert digest(raw)==package['input_sha256']
    data=json.loads(raw)
    cs=[sc.Candle(**c) for c in data['candles']];fs=[sc.FlowPoint(**f) for f in data['flow']]
    cs,fs=bt.closed_series(cs,fs,end_ms=data['ende'])
    assert all(math.isfinite(x) for f in data['flow'] for x in f.values())
    active=[c for c in cs if c.ts>=data['start']]
    assert [len(active)//3,2*len(active)//3]==package['third_indices']
    spec=importlib.util.spec_from_file_location('audit_independent',args.inputs/'book.py')
    book=importlib.util.module_from_spec(spec);spec.loader.exec_module(book);book.selfcheck()
    assert digest((args.inputs/'book.py').read_bytes())==plan['book_sha256']
    saved=json.loads(gzip.decompress((ROOT/'docs/nacharbeit-2026-09-28/6-ledger.json.gz').read_bytes()))
    starts=[data['start'],*[active[i].ts for i in package['third_indices']]]
    results=[];ledgers=[]
    for si,start in enumerate(starts):
        for scenario in plan['scenarios']:
            pair=[];descriptions=[]
            for ri,row in enumerate(plan['rows']):
                fn=bt.run_execution if scenario['next_open_offset']==1 else run_delayed
                result=fn(cs,fs,row['params'],start_ms=start,end_ms=data['ende'],
                    fee=.001,slippage=scenario['slippage_pct']/100)
                if args.package=='R0' and si==0 and scenario['next_open_offset']==1:
                    old=next(s['result'] for s in saved[ri]['scenarios'] if s['result']['slippage_pct']==scenario['slippage_pct'])
                    assert result==old,'R0 original changed'
                verification=verify_account(result,book,cs,start,scenario['next_open_offset'])
                descriptions.append(dict(name=row['name'],**describe(result,cs,verification)))
                pair.append(result)
                ledgers.append(dict(start_index=si,scenario=scenario['id'],row=ri,result=result))
                print(f"start {si} {scenario['id']} row {ri}: {result['ende']:.2f}; independent checks PASS",flush=True)
            item=dict(start_index=si,scenario=scenario['id'],rows=descriptions,
                comparison=compare(*descriptions))
            if si==0:
                returns,span=daily_pair(*pair)
                item['daily_span']=span
                item['daily_returns']=returns.tolist()
                item['U1']=[paired_bootstrap(returns,length) for length in [14,7,28]]
            results.append(item)
    args.out.mkdir(parents=True,exist_ok=True)
    dump(args.out/'results.json',dict(package=args.package,cutoff=data['ende'],r1_measured=args.package=='R1',
        plan_sha256=digest((DOC/'plan.json').read_bytes().replace(b'\r\n',b'\n')),
        selection_adjusted=False,results=results,network_blocked=True))
    with open(args.out/'ledgers.json.gz','wb') as f:
        f.write(gzip.compress(canonical(ledgers),mtime=0))
    print('All 30 causal runs and independent accounts PASS',flush=True)


if __name__=='__main__':main()
