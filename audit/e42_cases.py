"""Reconstruct every original E42 observation and breakout episode; separate lot P&L."""
import dataclasses,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from book import account
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'
sys.path.insert(0,str(ROOT/'engine'))
import strategy_core as sc

def date(ts): return datetime.fromtimestamp(ts/1000,timezone.utc).isoformat()
def main():
    raw=json.loads((ROOT/'docs/e445/eingaben.json').read_text())
    cs=[sc.Candle(**x) for x in raw['candles']]
    flow=[sc.FlowPoint(**x) for x in raw['flow']]
    results=json.loads((ROOT/'docs/e445/ergebnis.json').read_text())
    cfg=next(x['params'] for x in results['zeilen'] if x['rolle']=='Hauptzeile')
    pos=sc.Position()
    original_step=sc.ruecktest_schritt
    observations={}
    episodes=[]
    signals=[]
    journal=[]
    active=None
    def key(mark,start): return f'{start}:{mark}'
    def observation(mark,start):
        k=key(mark,start)
        if k not in observations:
            observations[k]=dict(id=f'O{len(observations)+1:03}',mark=mark,start=start,events=[])
        return observations[k]
    def step(mark,lang,since,cur,window):
        result=original_step(mark,lang,since,cur,window)
        if result:
            calls.append(dict(type=result,ts=cur.ts,mark=mark,start=pos.e42_start_ts,
                              since=since,open=cur.open,low=cur.low,high=cur.high,close=cur.close))
        return result
    sc.ruecktest_schritt=step
    try:
        for i,c in enumerate(cs):
            if c.ts<raw['start']:
                pos.last_signal_ts=c.ts
                continue
            before=dataclasses.asdict(pos)
            old_key=key(pos.e42_marke,pos.e42_start_ts) if pos.e42_marke is not None else None
            calls=[]
            sig=[s.to_dict() for s in sc.evaluate(cs[:i+1],flow[:i+1],pos,**cfg)]
            if pos.e42_marke is not None:
                observation(pos.e42_marke,pos.e42_start_ts)
            # Creation can itself be a breakout and is intentionally not fed through step().
            for m in pos.e42_meldungen:
                if m['art']=='ausbruch' and not any(x['type']=='ausbruch' for x in calls):
                    calls.insert(0,dict(type='ausbruch',ts=c.ts,mark=m['marke'],start=pos.e42_start_ts,
                                       since=None,open=c.open,low=c.low,high=c.high,close=c.close))
            for event in calls:
                obs=observation(event['mark'],event['start'])
                obs['events'].append(event)
                if event['type']=='ausbruch':
                    if active and active['terminal'] is None:
                        active['terminal']='ersetzt'; active['end']=c.ts
                    active=dict(id=f'B{len(episodes)+1:03}',observation=obs['id'],mark=event['mark'],
                                breakout=c.ts,first_retest=None,retest_bars=[],terminal=None,end=None)
                    episodes.append(active)
                elif active:
                    if event['type']=='ruecktest':
                        active['first_retest']=active['first_retest'] or c.ts
                        active['retest_bars'].append(c.ts)
                    else:
                        active['terminal']=event['type'];active['end']=c.ts
            for m in pos.e42_meldungen:
                if active and m['art'] in ('ohne_kauf','verfallen'):
                    active['terminal']=m['art'];active['end']=c.ts
                    active['block_reason']=m.get('grund')
            for s in sig:
                if s['type']=='RUECKKAUF':
                    s['audit_episode']=active['id'] if active else None
                    if active:
                        active['terminal']='gekauft';active['end']=c.ts;active['signal_index']=len(signals)
                signals.append(s)
            if active and active['terminal'] is None and pos.e42_marke is None:
                active['terminal']='durch_stop_beendet'; active['end']=c.ts
            new_key=key(pos.e42_marke,pos.e42_start_ts) if pos.e42_marke is not None else None
            if old_key and old_key!=new_key:
                old=observations[old_key]
                old['end']=c.ts
                old['end_reason']='neue_beobachtung' if new_key else 'beobachtung_beendet'
                if active and active['observation']==old['id'] and active['terminal'] is None:
                    active['terminal']='ersetzt';active['end']=c.ts
            if calls or sig or pos.e42_meldungen:
                journal.append(dict(ts=c.ts,calls=calls,messages=pos.e42_meldungen,signals=sig,
                    before={k:before[k] for k in ('bestand_pct','entry_ref','entry_pct','e42_start_ts','e42_teil_marke')},
                    after={k:getattr(pos,k) for k in ('bestand_pct','entry_ref','entry_pct','e42_start_ts','e42_teil_marke')}))
    finally: sc.ruecktest_schritt=original_step
    if active and active['terminal'] is None: active['terminal']='am_datenende_offen'
    for obs in observations.values():
        if 'end' not in obs: obs['end_reason']='am_datenende_offen'
    # A final state alone misses an observation created AND replaced within one bar.
    # Independently profiled nested begin/end calls provide the actual lifetime.
    trace=json.loads((OUT/'e42-ablaufkontrolle.json').read_text())
    assert trace['signals_exact']
    assert trace['input_sha256']==hashlib.sha256((ROOT/'docs/e445/eingaben.json').read_bytes()).hexdigest()
    assert trace['engine_sha256']==hashlib.sha256((ROOT/'engine/strategy_core.py').read_bytes()).hexdigest()
    traced={o['key']:o for o in trace['observations']}
    assert set(traced)==set(observations), 'Every runtime observation must be represented'
    lifetime_corrections=[]
    for k,obs in observations.items():
        checked=traced[k]
        if (obs.get('end'),obs['end_reason'])!=(checked.get('end'),checked['end_reason']):
            lifetime_corrections.append(dict(observation=obs['id'],previous_end=obs.get('end'),
                previous_reason=obs['end_reason'],end=checked.get('end'),reason=checked['end_reason']))
        obs['end_reason']=checked['end_reason']
        if 'end' in checked:obs['end']=checked['end']
    by_id={o['id']:o for o in observations.values()}
    for episode in episodes:
        obs=by_id[episode['observation']]
        if obs.get('end') is not None and episode.get('end') is not None and episode['end']>obs['end']:
            assert episode['terminal']=='ersetzt' and not episode['retest_bars']
            episode['end']=obs['end']
        episode['replaced_same_bar']=episode['terminal']=='ersetzt' and episode['end']==episode['breakout']
        assert episode['end'] is None or episode['end']>=episode['breakout']
    saved=json.loads((ROOT/'docs/e445/signale.json').read_text())
    original=saved['LIVE-heute +E42']
    clean=lambda rows:[{k:v for k,v in s.items() if k not in ('audit_episode','beobachtung_kerzen')} for s in rows]
    assert clean(signals)==clean(original),'Instrumented signals must exactly match saved original'
    book=account(signals,cs,raw['start'])
    baseline=account(saved['LIVE-heute +Bein in Handelsrichtung'],cs,raw['start'])
    lots=[x for x in book['lots'] if x['type']=='RUECKKAUF']
    for lot in lots:
        lot['episode']=signals[lot['id']]['audit_episode']
        lot['date_utc']=date(lot['ts'])
        lot['signal_known_earliest_utc']=date(lot['ts']+14400000)
        lot['old_rk_still_open']=[old['id'] for old in lots if old['ts']<lot['ts'] and
            old['units']-sum(e['units'] for e in old['exits'] if e['ts']<=lot['ts'])>1e-12]
    direct=sum(l['pnl'] for l in lots)
    difference=book['end']-baseline['end']
    result=dict(run_id='audit-20260927-03-e42',basis='Exact original saved candles; F09 independent ledger correction, no production logic edits',
        observations=list(observations.values()),episodes=episodes,journal=journal,lots=lots,
        audit_lifetime_corrections=lifetime_corrections,
        counts=dict(observations=len(observations),breakouts=len(episodes),terminal=dict(Counter(x['terminal'] for x in episodes)),
                    episodes_with_retest=sum(bool(x['first_retest']) for x in episodes),
                    retest_bars=sum(len(x['retest_bars']) for x in episodes),buys=len(lots),
                    breakouts_replaced_same_bar=sum(x['replaced_same_bar'] for x in episodes),
                    positive_lots=sum(x['pnl']>0 for x in lots),negative_lots=sum(x['pnl']<0 for x in lots)),
        portfolio=dict(e42_end=book['end'],base_end=baseline['end'],difference=difference,
                       direct_rk_pnl=direct,other_lots_difference=difference-direct,
                       e42_fees=book['fees'],baseline_fees=baseline['fees']),
        portfolio_paths=dict(e42=book['path'],baseline=baseline['path']))
    (OUT/'e42-faelle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(counts=result['counts'],portfolio=result['portfolio']),ensure_ascii=False,indent=2))
    for l in lots: print(l['episode'],l['date_utc'],round(l['pnl'],2),round(l['fees'],2),len(l['exits']),l['old_rk_still_open'])

if __name__=='__main__': main()
