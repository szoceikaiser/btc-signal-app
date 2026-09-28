"""Causality/restart counterchecks on frozen inputs; no strategy selection."""
import dataclasses,inspect,json,sys,types
from pathlib import Path
from inventory import git
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'
sys.path.insert(0,str(ROOT/'engine'))
import strategy_core as sc
import main as live
import backtest as bt
from book import account

def main():
    raw=json.loads((ROOT/'docs/e445/eingaben.json').read_text())
    cs=[sc.Candle(**x) for x in raw['candles'] if x['ts']+14400000<=raw['ende']]
    fl=[sc.FlowPoint(**x) for x in raw['flow'][:len(cs)]]
    cfg=json.loads((OUT/'gitter-plan.json').read_text())['base']
    reference=bt.run_backtest(cs,fl,cfg,start_ms=raw['start'])
    old=types.ModuleType('audit_main_core');sys.modules[old.__name__]=old
    source=git('show','89885adc9fb6d2eae60f7a64f9452760a4e33cd9:engine/strategy_core.py')
    exec(compile(source,'<frozen-main-core>','exec'),old.__dict__)
    oldparams={k:v for k,v in cfg.items() if k in inspect.signature(old.evaluate).parameters}
    p=old.Position();older=[]
    for i,c in enumerate(cs):
        if c.ts<raw['start']:p.last_signal_ts=c.ts;continue
        older.extend(s.to_dict() for s in old.evaluate(cs[:i+1],fl[:i+1],p,**oldparams))
    assert older==reference
    result=dict(main_default_parity='PASS: exact signals from frozen main and E44.5 default',
                cases={},description='Only frozen derived input data. Rolling emulation is not a reproduction of actual live API availability, revisions or past configuration changes.')
    for mode in ('restart_every_bar','rolling_1300','rolling_cvd_90d'):
        p=sc.Position();signals=[];pattern_diff=0
        for i,c in enumerate(cs):
            if c.ts<raw['start']:p.last_signal_ts=c.ts;continue
            start=max(0,i+1-1300) if mode.startswith('rolling') else 0
            cc=cs[start:i+1];ff=fl[start:i+1]
            if mode=='rolling_cvd_90d':
                cutoff=max(0,i+1-540)  # 90*6 closed bars, observation delay assumed zero.
                sb=fl[start-1].spot_cvd if start else 0
                fb=fl[cutoff-1].fut_cvd if cutoff else 0
                ff=[dataclasses.replace(f,spot_cvd=f.spot_cvd-sb,
                     fut_cvd=f.fut_cvd-fb if j>=cutoff else 0,
                     oi=f.oi if j>=cutoff else fl[cutoff].oi,
                     oi_btc=f.oi_btc if j>=cutoff else fl[cutoff].oi_btc,
                     long_liq=f.long_liq if j>=cutoff else 0,
                     short_liq=f.short_liq if j>=cutoff else 0,
                     long_pct=f.long_pct if j>=cutoff else 0) for j,f in enumerate(fl[start:i+1],start)]
            pattern_diff+=sc.classify_pattern(cc,ff)!=sc.classify_pattern(cs[:i+1],fl[:i+1])
            signals.extend(s.to_dict() for s in sc.evaluate(cc,ff,p,**cfg))
            if mode=='restart_every_bar':p=live.pos_from_state(live.pos_to_state(p))
        sigkey=lambda s:json.dumps(s,sort_keys=True)
        base_set=set(map(sigkey,reference));case_set=set(map(sigkey,signals))
        book=account(signals,cs,raw['start'])
        result['cases'][mode]=dict(pattern_bars_changed=pattern_diff,signals=len(signals),
            added=[json.loads(x) for x in sorted(case_set-base_set)],
            removed=[json.loads(x) for x in sorted(base_set-case_set)],return_pct=book['return_pct'])
        print(mode,pattern_diff,len(case_set-base_set),len(base_set-case_set),book['return_pct'],flush=True)
    (OUT/'live-backtest-paritaet.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
