"""Fixed historical capital fractions and descriptive buy-and-hold controls."""
import json,sys
from pathlib import Path
from book import account
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'
sys.path.insert(0,str(ROOT/'engine'))
from strategy_core import Candle

def main():
    raw=json.loads((ROOT/'docs/e445/eingaben.json').read_text())
    cs=[Candle(**c) for c in raw['candles'] if c['ts']+14400000<=raw['ende']]
    row=json.loads((OUT/'grid/V000.json').read_text())
    results=[]
    for deploy in (1.,.6,.5):
        scenarios=[]
        for scenario in [r['scenario'] for r in row['scenarios']]:
            book=account(row['signals'],cs,raw['start'],fee=scenario['fee'],slip=scenario['slip'],mode=scenario['fill'],deploy=deploy)
            scenarios.append(dict(scenario=scenario,**{k:v for k,v in book.items() if k not in ('fills','lots','path')}))
        results.append(dict(deploy=deploy,scenarios=scenarios))
    first=next(c for c in cs if c.ts>=raw['start']);last=cs[-1]
    controls=[]
    for fraction in (1.,row['scenarios'][0]['avg_exposure_pct']/100):
        sig=[dict(ts=first.ts,type='KAUF_1',price=first.close,tranche_pct=100*fraction)]
        book=account(sig,cs,raw['start'],mode='close')
        controls.append(dict(initial_fraction=fraction,first_close=first.close,last_close=last.close,
            **{k:v for k,v in book.items() if k not in ('fills','lots','path')},
            liquidation_end=book['end']-book['path'][-1]['units']*last.close*.001))
    result=dict(run_id='audit-20260928-05-capital',prereg_commit='9b916f0',deploy_rows=results,buy_hold=controls,
        note='No signal optimization; second buy-hold allocation is descriptive after observing average exposure')
    (OUT/'kapital.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Ergänzende Kapital- und Vergleichsrechnung','',
        'Vorfestlegung [ERGAENZUNGSPLAN.md](ERGAENZUNGSPLAN.md), Commit 9b916f0. Gleiche abgeschlossene Daten, Signale V000 und unabhängige F09-bereinigte Rechnung. Keine neue Handelsregel.',
        '', '| Kapitalquote je Zyklus | Level-Rendite % | Schluss-DD % | Gebühren USD | mittlere Bindung % | nächste Eröffnung % | 4h später, teuer % |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for r in results:
        b=r['scenarios'][0]
        lines.append(f'| {100*r["deploy"]:.0f} % | {b["return_pct"]:.2f} | {b["dd_close_pct"]:.2f} | {b["fees"]:.2f} | {b["avg_exposure_pct"]:.2f} | {r["scenarios"][2]["return_pct"]:.2f} | {r["scenarios"][3]["return_pct"]:.2f} |')
    lines+=['', 'Eine reduzierte Quote kann durch spätere Nachkäufe/Verkaufsserien anders wirken als schlicht „Gesamtrendite mal Quote“. Ein geringerer absoluter Gewinn ist allein kein Gegenargument gegen eine gewünschte geringere Kapitalbindung.',
            '', '| Buy-and-Hold, anfänglicher Anteil | Rendite zum letzten Schluss % | Schluss-DD % | Rendite nach zusätzlicher Schlussverkaufsgebühr % |',
            '|---|---:|---:|---:|']
    for b in controls:lines.append(f'| {100*b["initial_fraction"]:.2f} % | {b["return_pct"]:.2f} | {b["dd_close_pct"]:.2f} | {100*(b["liquidation_end"]/10000-1):.2f} |')
    lines+=['', 'Der zweite Anteil entspricht nur **anfänglich** der historischen mittleren V000-Kapitalbindung. Er wurde nach Kenntnis dieser Bindung gesetzt, bleibt danach passiv und ist keine exakt risikogleiche oder prospektiv unabhängige Vergleichsstrategie. Das positive Engine-Ergebnis im selben schwachen Gesamtfenster ist interessant, aber Ausführungsfehler, Datenverfügbarkeit und wiederholte Variantenwahl verhindern daraus einen belastbaren erwarteten Mehrertrag abzuleiten.']
    (OUT/'KAPITAL.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines))

if __name__=='__main__':main()
