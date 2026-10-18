"""Offline, predeclared two-row measurement and independent proportional lot book.

Frozen input, original signals/results and audit book are hashed before/after.
Never dispatches a workflow or changes an original artifact.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT=Path(__file__).resolve().parents[1]
BASE='67c8e624de3cc1b854a78dced755a5702b1a9c9a'
AUDIT='ccf2b01c0578346f325261e72445b7375a9ac706'
sys.path.insert(0,str(ROOT/'engine'))
import backtest as bt
import strategy_core as sc


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root,*args):
    return subprocess.run(['git','-c',f'safe.directory={root.as_posix()}',*args],cwd=root,
                          capture_output=True,check=True).stdout


def close(a,b):
    assert abs(a-b)<=max(1e-7,abs(a)*1e-10),(a,b)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--audit-root',type=Path,required=True)
    args=parser.parse_args(); audit=args.audit_root.resolve()
    assert git(audit,'rev-parse','HEAD').decode().strip()==AUDIT
    paths=[audit/'docs/e445'/n for n in ('eingaben.json','signale.json','ergebnis.json')]+[audit/'audit/book.py']
    git(audit,'diff','--exit-code',AUDIT,'--','docs/e445','audit/book.py')
    hashes={p.name:sha(p) for p in paths}
    assert hashes['eingaben.json']=='ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a'
    data=json.loads(paths[0].read_text(encoding='utf-8'))
    saved=json.loads(paths[2].read_text(encoding='utf-8'))
    cs=[sc.Candle(**c) for c in data['candles']]
    fs=[sc.FlowPoint(**f) for f in data['flow']]
    closed,flow=bt.closed_series(cs,fs,end_ms=data['ende'])
    spec=importlib.util.spec_from_file_location('independent_3b_book',paths[3])
    book=importlib.util.module_from_spec(spec);spec.loader.exec_module(book);book.selfcheck()
    old_sc=types.ModuleType('stage3a_strategy');sys.modules[old_sc.__name__]=old_sc
    exec(compile(git(ROOT,'show',BASE+':engine/strategy_core.py'),'<3a-strategy>','exec'),old_sc.__dict__)
    ns=dict(__name__='stage3a_backtest',__file__=str(ROOT/'engine/backtest.py'))
    sys.modules['strategy_core']=old_sc
    try: exec(compile(git(ROOT,'show',BASE+':engine/backtest.py'),'<3a-backtest>','exec'),ns)
    finally: sys.modules['strategy_core']=sc
    # Two EXACT existing rows fixed before any outcome, no sale factor or new grid.
    selected=[r for r in saved['zeilen'] if r['rolle']=='Basis' or
              (r['params'].get('ausbruch_ruecktest') and not r['params'].get('rest_halten')
               and r['params'].get('ruecktest_fenster')==12 and r['params'].get('verkauf_faktor',1)==1)]
    assert len(selected)==2,[r['label'] for r in selected]
    results=[]
    for row in selected:
        cfg={k:value for k,value in row['params'].items() if k!='verkauf_faktor'}
        old_signals=ns['run_backtest'](closed,flow,cfg,start_ms=data['start'])
        old=ns['simulate'](old_signals,closed,start_ms=data['start'])
        scenarios=[]
        for slip in (0.,.001,.005):
            r=bt.run_execution(cs,fs,cfg,start_ms=data['start'],end_ms=data['ende'],slippage=slip)
            orders={f"v1:{o['ts']}:{o['sequence']}":o for o in r['signals']}
            selected_signals=[orders[e['order_id']] for e in r['ledger'] if e['status']=='scheduled']
            independent=book.account(selected_signals,closed,data['start'],fee=.001,slip=slip,mode='next_open')
            close(r['ende'],independent['end']);close(r['fees'],independent['fees'])
            close(r['dd_close_pct'],-independent['dd_close_pct'])
            close(r['dd_intrabar_lower_pct'],-independent['dd_intrabar_range_pct'][1])
            close(r['dd_intrabar_upper_pct'],-independent['dd_intrabar_range_pct'][0])
            fills=[e for e in r['ledger'] if e['status']=='filled']
            independent_fills=[f for f in independent['fills'] if f['units']>1e-15]
            assert len(fills)==len(independent_fills)
            for actual,other in zip(fills,independent_fills):
                assert actual['fill_at']==other['execution_ts'] and actual['type']==other['type']
                for key,other_key in [('quantity','units'),('fill_price','price'),('fee','fee')]:close(actual[key],other[other_key])
                close(actual['before']['cash'],other['cash_before']);close(actual['after']['cash'],other['cash_after'])
            assert len(r['equity'])==len(independent['path'])
            for a,b in zip(r['equity'],independent['path']):
                close(a['cash'],b['cash']);close(a['btc'],b['units']);close(a['equity'],b['equity'])
            close(sum(l['pnl'] for l in independent['lots']),r['ende']-10000)
            for month,point in r['month_ends'].items():close(point['equity'],independent['month_ends'][month])
            # Independent lot attribution is saved, not used by the engine.
            scenarios.append(dict(result=r,independent=independent,
                delta_end_vs_3a=r['ende']-old['ende'],fills_verified=len(fills),
                candidate_count=len(r['signals']),old_signal_count=len(old_signals),
                different_signal_band=[(o['ts'],o['type'],o['price']) for o in r['signals']]!=
                                      [(o['ts'],o['type'],o['price']) for o in old_signals]))
            print(f"{row['label']} slip {slip:.3f}: {r['ende']:.2f}; DD Close {r['dd_close_pct']:.4f} / UPPER {r['dd_intrabar_upper_pct']:.4f}; {len(fills)} fills",flush=True)
        results.append(dict(name=row['label'],params=cfg,legacy_3a=old,scenarios=scenarios))
    assert hashes=={p.name:sha(p) for p in paths},'Original input or audit changed'
    report=dict(result='PASS',base_commit=BASE,audit_commit=AUDIT,hashes=hashes,
        scope='Two existing rows, three independent closed-loop cost scenarios each; no optimization',
        cutoff=data['ende'],start=data['start'],original_bars=len(cs),closed_bars=len(closed),rows=results)
    out=ROOT/'docs/nacharbeit-2026-09-28/3b-ergebnis.json'
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
