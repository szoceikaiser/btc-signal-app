"""Preregistered historical E4 grid (n=3..6 x k=2/3) on the common current basis."""
import hashlib
import itertools
import json
import math
import time
from measure import bt, sc, compact, ROOT, OUT
from book import account, selfcheck
from tolerance import corrected_simulate

def main():
    assert 'n=3/4/5/6' in (OUT/'STRUKTURPLAN.md').read_text(encoding='utf-8')
    selfcheck()
    plan=json.loads((OUT/'gitter-plan.json').read_text())
    rawpath=ROOT/'docs/e445/eingaben.json'
    assert hashlib.sha256(rawpath.read_bytes()).hexdigest()==plan['input_sha256']
    raw=json.loads(rawpath.read_text())
    pairs=[(c,f) for c,f in zip(raw['candles'],raw['flow']) if c['ts']+14400000<=raw['ende']]
    cs=[sc.Candle(**c) for c,f in pairs]
    fl=[sc.FlowPoint(**f) for c,f in pairs]
    mid=raw['start']+(raw['ende']-raw['start'])//2
    target=OUT/'struktur';target.mkdir(exist_ok=True)
    fixed=corrected_simulate(bt)
    for num,(n,k) in enumerate(itertools.product((3,4,5,6),(2.,3.))):
        identifier=f'S{num:03}'
        dest=target/(identifier+'.json')
        if dest.exists():continue
        begin=time.monotonic()
        params=dict(plan['base'],pivot_n=n,k_atr=k)
        signals=bt.run_backtest(cs,fl,params,start_ms=raw['start'])
        corrected=fixed(signals,cs,start_ms=raw['start'])
        scenarios=[dict(scenario=s,**compact(account(signals,cs,raw['start'],fee=s['fee'],slip=s['slip'],mode=s['fill']))) for s in plan['costs']]
        assert abs(scenarios[0]['end']-corrected['ende'])<.011
        halves=[]
        for start,end in ((raw['start'],mid),(mid,raw['ende'])):
            count=sum(c.ts<=end for c in cs)
            hs=bt.run_backtest(cs[:count],fl[:count],params,start_ms=start)
            halves.append(dict(start=start,end=end,independent=compact(account(hs,cs[:count],start))))
        row=dict(id=identifier,run_id='audit-20260928-06-'+identifier,params=params,
                 input_sha256=plan['input_sha256'],signals=signals,scenarios=scenarios,
                 halves=halves,tolerance=corrected,seconds=time.monotonic()-begin)
        dest.write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8')
        print(identifier,n,k,round(scenarios[0]['return_pct'],4),'seconds',round(row['seconds'],1),flush=True)
    rows=[json.loads(p.read_text()) for p in sorted(target.glob('S*.json'))]
    assert len(rows)==8
    base=json.loads((OUT/'grid/V000.json').read_text())
    assert rows[4]['params']==base['params']
    assert abs(rows[4]['scenarios'][0]['end']-base['scenarios'][0]['end'])<1e-8
    def months(row):
        result={};prior=10000.
        for m,v in row['scenarios'][0]['month_ends'].items(): result[m]=v/prior;prior=v
        return result
    bm=months(base)
    lines=['# Ergänzende Strukturprüfung: ursprüngliche E4-Werte','',
           'Vorfestlegung: [STRUKTURPLAN.md](STRUKTURPLAN.md), vor diesem Lauf committed. Acht Zeilen, davon eine identisch mit V000; sieben zusätzliche eindeutige Konfigurationen, zusammen mit dem Hauptgitter 86. Alle sonstigen Parameter auf heutiger eingefrorener Live-Basis. Keine Wiederholung des ursprünglichen E4-Triggerabgleichs und kein unberührter Test.', '',
           'Gleiche abgeschlossene Daten, unabhängige F09-Buchführung und Kostenmodelle wie [KOMBINATIONEN.md](KOMBINATIONEN.md). Level-Rendite bleibt wegen der bekannten Ausführungs-/Engine-Grenzen eine hypothetische Vergleichszahl. Schluss-DD ist nicht der maximale Intraday-Rückgang.', '',
           '| ID | n | k | Level % | H1/H2 % | Δ H1/H2 Punkte | Schluss-DD % | Gebühren USD | Orders / Null | Ø investiert % | nächste Eröffnung % | +4h, teuer % | Minimum ohne Monat, Punkte | beide ≥2 |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    comparisons=[]
    for r in rows:
        s=r['scenarios'][0];h=[x['independent']['return_pct'] for x in r['halves']]
        delta=[h[i]-base['halves'][i]['independent']['return_pct'] for i in (0,1)]
        m=months(r)
        loo=min(100*(math.prod(v for k,v in m.items() if k!=omit)-math.prod(v for k,v in bm.items() if k!=omit)) for omit in m)
        passed=all(x>=2 for x in delta)
        comparisons.append(dict(id=r['id'],half_deltas=delta,both_halves_at_least_2=passed,min_compounded_leave_one_month_out=loo,technical_release=False))
        lines.append(f'| {r["id"]} | {r["params"]["pivot_n"]} | {r["params"]["k_atr"]:.0f} | {s["return_pct"]:.2f} | {h[0]:.2f}/{h[1]:.2f} | {delta[0]:+.2f}/{delta[1]:+.2f} | {s["dd_close_pct"]:.2f} | {s["fees"]:.2f} | {s["orders"]}/{s["zero_orders"]} | {s["avg_exposure_pct"]:.2f} | {r["scenarios"][2]["return_pct"]:.2f} | {r["scenarios"][3]["return_pct"]:.2f} | {loo:+.2f} | {passed} |')
    lines+=['', '## Einordnung', '',
        'Keine Variante erreicht +2 Punkte in beiden Hälften; auch der +1-Filter würde keine neue Alternative qualifizieren. n=6 erhöht die Gesamtrendite auf 39,27 %, verliert jedoch 3,39 Punkte in H1 und gewinnt 5,72 in H2. Ohne den günstigsten einzelnen Monat kippt der Vorteil bis auf −4,34 Punkte. n=3 fällt deutlich zurück. Die ursprüngliche Nähe zu bekannten Handelsdaten rechtfertigt somit keine allgemeine Wahl eines profitableren Nachbarwerts.',
        '', '**k=2 und k=3 sind hier redundant:** `last_significant_impulse` verlangt zunächst mindestens 5 % Beinlänge, danach mindestens k×ATR **oder** 3 % Beinlänge (`strategy_core.py:236–243`). Wer die harte 5-%-Grenze erfüllt, erfüllt bereits die 3-%-Alternative. Deshalb verändert k in diesem Live-Verbund die Impulsauswahl nicht. Das ist ein logischer Zusammenhang der Regeln, keine zusätzliche empirische Bestätigung durch doppelte Renditezeilen.',
        '', 'Alle acht Detaildateien liegen unter `struktur/Sxxx.json`. Die Auswahl aus den alten Werten erweitert die Zahl der untersuchten Konfigurationen; sie liefert keine neue unabhängige Stichprobe. Ein besserer Nachbarwert wäre eine Sensitivitätswarnung, keine automatische Neu-Kalibrierung.']
    (OUT/'STRUKTUR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'struktur-vergleich.json').write_text(json.dumps(comparisons,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Both halves >=2',[r['id'] for r in comparisons if r['both_halves_at_least_2']])

if __name__=='__main__':main()
