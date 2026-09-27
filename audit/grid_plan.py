"""Freeze the exact audit configurations before measuring their returns."""
import hashlib
import itertools
import json
from pathlib import Path
import sys
from inventory import git

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'
sys.path.insert(0,str(ROOT/'engine'))
import backtest as bt
import main as live

def main():
    config=json.loads(git('show','89885adc9fb6d2eae60f7a64f9452760a4e33cd9:site/data/config.json'))
    base=live.eval_params(config)
    rows={}
    def add(label,changes,kind):
        p=dict(base,**changes)
        key=json.dumps(p,sort_keys=True)
        if key not in rows:
            rows[key]=dict(id=f'V{len(rows):03}',params=p,labels=[],groups=[],
                           diff={k:v for k,v in p.items() if base[k]!=v})
        rows[key]['labels'].append(label)
        rows[key]['groups'].append(kind)
    add('Live am Auditbeginn',{},'baseline')
    grids={
        'G1':{'ausbruch_ruecktest':[False,True],'verkauf_faktor':[1.,.67],'rest_halten':[False,True]},
        'G2':{'ausbruch_ruecktest':[False,True],'high_exit':['off','on'],'trail_stop':[False,True]},
        'G3':{'stop_rueckeroberung':[0,1],'bein_richtung':['auto','bias'],'zonen_nachziehen':[False,True]},
        'G4':{'buy_ladder':[False,True],'flush_entry':['off','core'],'liq_entry':['off','boost']},
        'G5':{'ausbruch_ruecktest':[False,True],'muster_cvd':['alt','usd'],'muster_oi':['usd','btc']},
    }
    for group,factors in grids.items():
        for values in itertools.product(*factors.values()):
            p=dict(zip(factors,values))
            add(group+' '+json.dumps(p,sort_keys=True),p,group)
    for key in bt.EVAL_KEYS:
        values={json.dumps(c[key]):c[key] for c in bt.GRID}
        values[json.dumps(live.EVAL_DEFAULTS[key])]=live.EVAL_DEFAULTS[key]
        if isinstance(base[key],bool):
            values[json.dumps(not base[key])]=not base[key]
        if key=='stop_puffer_pct': values['0.005']=.005
        if key=='flush_entry': values['"t1"']='t1'
        if key=='min_bein_pct': values['0.0']=0.
        if key=='min_stop_pct': values['0.0']=0.
        for v in values.values():
            if v!=base[key]:
                add(f'Einzeln {key}={v}',{key:v},'single')
    # Dependent settings: meaningful only with their parent active. Values already
    # in the historical grid; listed now before any new performance is seen.
    for n in (8,12): add(f'1D plus n={n}',dict(zonen_1d=True,pivot_n_1d=n),'dependent')
    add('Trend EMA50',dict(trend_filter=True,trend_ema=50),'dependent')
    add('E42 6 candles',dict(ausbruch_ruecktest=True,ruecktest_fenster=6),'robust')
    manifest=dict(base_main='89885adc9fb6d2eae60f7a64f9452760a4e33cd9',base=base,
                  input_sha256=hashlib.sha256((ROOT/'docs/e445/eingaben.json').read_bytes()).hexdigest(),
                  rows=list(rows.values()),grids=grids,
                  corrections=['D01: use only candles with ts+4h <= recorded ende for common grid'],
                  costs=[dict(fee=.001,slip=0,fill='level'),dict(fee=.001,slip=0,fill='close'),
                         dict(fee=.001,slip=.0005,fill='next_open'),dict(fee=.002,slip=.001,fill='delay_4h')],
                  time_checks='Original separately restarted halves; fixed walk-forward months May-Sep, no selection; 7/28 day paired block bootstrap, seed 270926, 2000 draws for prespecified E42 comparison')
    (OUT/'gitter-plan.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(len(rows),'unique configurations frozen; no returns computed')

if __name__=='__main__': main()
