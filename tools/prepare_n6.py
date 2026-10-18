"""Assemble validated R1, retaining R0 closed prefix; inventory search read-only."""
from copy import deepcopy
from datetime import datetime
import json
import math
from pathlib import Path
from historical_analysis import ROOT,DOC,digest,canonical,dump,STEP


def prepare_data():
    r0=json.loads((ROOT.parent/'audit-backups/6-abschluss-05208ce/eingefrorene-inputs/eingaben.json').read_text(encoding='utf-8'))
    rawdir=DOC/'r1-raw'
    manifest=json.loads((rawdir/'manifest.json').read_text(encoding='utf-8'))
    for s in manifest['sources']:assert digest((rawdir/(s['name']+'.json')).read_bytes())==s['sha256']
    def read(name):return json.loads((rawdir/(name+'.json')).read_text(encoding='utf-8'))
    def coinalyze(name,fields):
        rows=read(name)
        assert len(rows)==1 and rows[0]['symbol']=='BTCUSDT_PERP.A'
        points=rows[0]['history'];assert all(set(fields)<=set(p) for p in points)
        times=[int(p['t'])*1000 for p in points];assert times==sorted(set(times))
        assert all(all(math.isfinite(float(p[k])) for k in fields) for p in points)
        return dict(zip(times,points))
    oi=coinalyze('open-interest-history',['t','c'])
    liq=coinalyze('liquidation-history',['t','l','s'])
    fut=coinalyze('ohlcv-history',['t','v','bv'])
    ls=coinalyze('long-short-ratio-history',['t','l'])
    raw=read('spot');spot={int(r[0]):r for r in raw};assert len(spot)==len(raw)
    funding={int(datetime.fromisoformat(p['timestamp'].replace('Z','+00:00')).timestamp()*1000):float(p['relativeFundingRate'])*8
        for p in read('funding')['rates']}
    end=1790683200000
    cs=[c for c in r0['candles'] if c['ts']+STEP<=r0['ende']]
    fs=r0['flow'][:len(cs)]
    old_cs,old_fs=deepcopy(cs),deepcopy(fs)
    times=list(range(cs[-1]['ts']+STEP,end,STEP))
    assert len(times)==13
    # Check raw overlap, including raw delta recovered from cumulative R0.
    overlap=cs[-1]['ts'];k=spot[overlap]
    checks=dict(ohlc=cs[-1]==dict(ts=overlap,**dict(zip(['open','high','low','close'],map(float,k[1:5])))),
        oi=fs[-1]['oi']==float(oi[overlap]['c']),
        liquidations=[fs[-1]['long_liq'],fs[-1]['short_liq']]==[float(liq[overlap][x]) for x in ['l','s']],
        long_pct=fs[-1]['long_pct']==float(ls[overlap]['l']),
        spot_delta_abs_difference=abs((fs[-1]['spot_cvd']-fs[-2]['spot_cvd'])-(2*float(k[10])-float(k[7]))),
        fut_delta_abs_difference=abs((fs[-1]['fut_cvd']-fs[-2]['fut_cvd'])-(2*float(fut[overlap]['bv'])-float(fut[overlap]['v']))),
        funding_abs_difference=abs(fs[-1]['funding']-funding[overlap+STEP]))
    assert all(checks[k] for k in ['ohlc','oi','liquidations','long_pct'])
    assert checks['spot_delta_abs_difference']<1e-5 and checks['fut_delta_abs_difference']<1e-8
    assert checks['funding_abs_difference']<1e-15
    availability=[]
    for t in times:
        assert all(t in mapping for mapping in [spot,oi,liq,fut,ls]),('Missing required 4h point',t)
        assert t+STEP in funding,('Missing exact historical funding timestamp',t)
        assert all(h in funding for h in range(t,t+STEP+1,3600000)),('Funding hourly gap',t)
        k=spot[t];assert int(k[6])==t+STEP-1
        c=dict(ts=t,**dict(zip(['open','high','low','close'],map(float,k[1:5]))))
        f=dict(ts=t,spot_cvd=fs[-1]['spot_cvd']+(2*float(k[10])-float(k[7])),
            fut_cvd=fs[-1]['fut_cvd']+(2*float(fut[t]['bv'])-float(fut[t]['v'])),
            oi=float(oi[t]['c']),funding=funding[t+STEP],long_liq=float(liq[t]['l']),
            short_liq=float(liq[t]['s']),long_pct=float(ls[t]['l']),oi_btc=float(oi[t]['c'])/c['close'])
        assert all(math.isfinite(x) for x in f.values()) and 0<=f['long_pct']<=100
        assert 0<=float(fut[t]['bv'])<=float(fut[t]['v'])
        assert float(k[10])<=float(k[7])
        cs.append(c);fs.append(f)
        availability.append(dict(bar_open=t,bar_close=t+STEP,funding_timestamp=t+STEP,
            first_provable_version='See raw GET retrieval times, all later than fixed cutoff',as_of_proven=False))
    assert cs[:len(old_cs)]==old_cs and fs[:len(old_fs)]==old_fs
    r1=dict(start=r0['start'],ende=end,candles=cs,flow=fs,package='R1-frozen-prefix-extension')
    dump(DOC/'r1-inputs.json',r1)
    dump(DOC/'r1-manifest.json',dict(complete_fields=True,as_of_proven=False,
        raw_manifest=manifest,raw_artifact_sha256=digest((DOC/'raw-artifact.zip').read_bytes()),
        inputs_sha256=digest((DOC/'r1-inputs.json').read_bytes()),
        preserved_closed_prefix_bars=len(old_cs),prefix_fields_identical=True,
        prefix_sha256=digest(canonical(dict(candles=old_cs,flow=old_fs))),
        original_r0_preserved=True, discarded_r0_partial_bar=r0['candles'][-1]['ts'],
        partial_bar_policy='R0 partial bar never used; R1 adds its completed later version as first extension bar',
        overlap_checks=checks,extension_bars=13,total_bars=len(cs),
        warmup_bars=sum(c['ts']<r0['start'] for c in cs),trade_bars=sum(c['ts']>=r0['start'] for c in cs),
        cutoff=end,first_provable_availability=availability,
        transforms=dict(spot='previous frozen cumulative + (2*k[10]-k[7]), USD',
            futures='previous frozen cumulative + (2*bv-v), BTC',oi='Coinalyze USD close',
            oi_btc='OI USD / same spot close',liquidations='l,s USD',long_pct='l percent',
            funding='Kraken PF_XBTUSD hourly relativeFundingRate *8 at bar close; exact timestamp required'),
        limitations=['Original R0 raw vintages/availability not preserved',
            'Extra four hours do not prove real execution feasibility',
            'Warmup retained exactly, including original default/carried OI and funding; no warmup trading',
            'No revision of any completed R0 candle or flow value',
            'Boundary funding timestamp is an original model convention, not proof of publication before decision']))
    print('R1: 13 complete appended bars; 2480 closed prefix bars identical; all fields present')


def inventory():
    audit=ROOT.parent/'audit-work'
    e445=ROOT.parent/'e445-work'
    sources=[ROOT/'docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md',ROOT/'docs/PLAN-E44-KOMBINATIONEN.md',
        audit/'docs/audit-2026-09-27/BERICHT.md',audit/'docs/audit-2026-09-27/HISTORISCHE-BELEGE.md',
        audit/'docs/audit-2026-09-27/gitter-plan.json',audit/'docs/audit-2026-09-27/STRUKTURPLAN.md',
        e445/'docs/e445/ergebnis.json']
    source_info=[dict(path=str(p.relative_to(ROOT.parent)),sha256=digest(p.read_bytes())) for p in sources]
    entries=[]
    for family,code,source,rows,inp in [
        ('audit legacy','ccf2b01c0578346f325261e72445b7375a9ac706',sources[4],
         json.loads(sources[4].read_text(encoding='utf-8'))['rows'],'ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a'),
        ('E44.5 legacy','e2b0051199c2e0c38723cc3a23c00ea3bd320601',sources[6],
         json.loads(sources[6].read_text(encoding='utf-8'))['zeilen'],'ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a')]:
        for row in rows:
            params=row['params']
            entries.append(dict(family=family,code=code,input=inp,params=params,
                labels=row.get('labels',[row.get('label')]),
                dedup_key=digest(canonical(dict(params=params,code=code,input=inp)))))
    for stage in ['3b','4','6']:
        import gzip
        p=ROOT/f'docs/nacharbeit-2026-09-28/{stage}-ledger.json.gz'
        if stage=='3b':
            p=ROOT/'docs/nacharbeit-2026-09-28/3b-ergebnis.json'
            rows=json.loads(p.read_text(encoding='utf-8'))['rows']
        else:
            rows=json.loads(gzip.decompress(p.read_bytes()))
        code={'3b':'9606a6f555f9cdaee86f9c33a5175c5c5306b365','4':'ebc01a48057994629c021bd84ab7f9a236678b70','6':'05208cecce8d5a0e856a1ea56984b209f403ccd6'}[stage]
        source_info.append(dict(path=str(p.relative_to(ROOT)),sha256=digest(p.read_bytes())))
        for row in rows:
            entries.append(dict(family=stage+' corrected V1',code=code,input=inp,params=row['params'],labels=[row['name']],
                dedup_key=digest(canonical(dict(params=row['params'],code=code,input=inp)))))
    dump(DOC/'search-inventory.json',dict(sources=source_info,entries=entries,
        distinct_versioned_entries=len(set(e['dedup_key'] for e in entries)),
        complete_family=False,U2='Auswahlbereinigung nicht belegt',additional_measurements=0,
        gaps=['Older E43 trials: exact historical raw packages not preserved for every choice',
            'Audit 79 registered configurations plus 7 structural alternatives; not the complete development family',
            'Control selected using E43.2 known halves; E41 rule override and subsequent reevaluation',
            'E44.5 parameter grid uses later verkauf_faktor code, not imported into evaluation',
            'Legacy signal-band data cannot join corrected V1 daily return matrix'],
        decisions=[dict(stage='E43.2',choice='bein_richtung=bias',reason='known halves improved; control was selected'),
            dict(stage='E43.3/4/A5',choice='alt/usd/voll retained',reason='reported unchanged returns'),
            dict(stage='E43.6/8',choice='six tested switches off',reason='historical comparison rules not met'),
            dict(stage='E44',choice='E42 plus combinations proposed',reason='known missed rally periods and exploratory interactions'),
            dict(stage='audit/corrections',choice='same fixed pair',reason='correct bookkeeping, no retuning')]))
    print('Read-only search inventory saved; U2 incomplete, no extra strategies measured')


if __name__=='__main__':
    prepare_data()
    inventory()
