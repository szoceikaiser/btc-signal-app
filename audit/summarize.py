"""Human-readable complete grid; arithmetic, costs and risk definitions made explicit."""
import json,math,random
from pathlib import Path
from book import account
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'

def monthly(row):
    prev=10000;result={}
    for m,e in row['scenarios'][0]['month_ends'].items():
        result[m]=100*(e/prev-1);prev=e
    return result

def main():
    rows=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((OUT/'grid').glob('V*.json'))]
    assert len(rows)==79
    base=rows[0]; bm=monthly(base)
    def fmt(x):return f'{x:.2f}'
    header=['# Gemeinsame Kombinationsmatrix','',
        'Vorfestlegung: `gitter-plan.json`, Commit e7e92d3, vor Beginn der Messung. 79 eindeutige Konfigurationen; fünf vollständige 2×2×2-Gitter, Einzelgegenproben und abhängige Einstellungen. Alle Zeilen gegen identische Live-Parameter von main 89885adc.',
        '', 'Eingaben: SHA-256 ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a. Zeitraum 18.01.–27.09.2026 (letzter abgeschlossener 4h-Balken beginnt 04:00 UTC). D01: laufende letzte Kerze entfernt. F09: unabhängige Buchführung entfernt winzige Bestandsreste. Unveränderte ursprüngliche Simulation steht zusätzlich in jedem `grid/Vxxx.json`.',
        '', '**Die Level-Rendite bleibt eine hypothetische Vergleichszahl:** zahlreiche Entscheidungen stehen erst am Kerzenschluss fest. Historische Berührung eines Levels beweist keine damals ausführbare Order. Schluss-DD ist der Rückgang an 4h-Schlusskursen; kein maximaler Intraday-Verlust. Für kausale Ausführungsmodelle liegen zusätzlich OHLC-Risikointervalle in den JSON-Dateien.',
        '', 'Kosten: 0,1 % pro Order. Nächste Eröffnung: zusätzlich 0,05 % ungünstigerer Preis pro Seite, Verzögerung 0 Stunden nach Signal-Verfügbarkeit. Spalte „+4h, teuer“: eine weitere Kerze Verzögerung, 0,2 % Gebühr und 0,1 % Preisabschlag/-aufschlag. Dies sind vorab bestimmte Stressannahmen, keine gemessenen Live-Ausführungen. Kaufanzahl plus Verkaufsanzahl zählt nur Orders mit positivem Volumen; Nullorders und gesamte Signale getrennt im Datensatz. H1/H2 starten jeweils mit neuem Kapital und leerem Bestand.',
        '', '| ID | Änderung gegenüber live | Gruppe | Level % | H1 / H2 % | Schluss-DD % | Gebühren USD | Orders / Null | Ø investiert % | nächste Eröffnung % | +4h, teuer % |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    comparisons=[]
    for row in rows:
        diff=', '.join(f'{k}={v}' for k,v in row['diff'].items()) or 'Live-Basis'
        if not row['long_only']:
            header.append(f'| {row["id"]} | {diff} | {", ".join(sorted(set(row["groups"])))} | {row["original"]["rendite_pct"]:.2f}* | nicht belastbar | nicht belastbar | nicht erhoben | nicht erhoben | nicht erhoben | nicht erhoben | nicht erhoben |')
            continue
        r=row['scenarios'][0]
        h=[x['independent']['return_pct'] for x in row['halves']]
        hd=[h[i]-base['halves'][i]['independent']['return_pct'] for i in (0,1)]
        m=monthly(row); deltas={k:m[k]-bm[k] for k in m}
        # Compounded difference after removing the same month from both paths.
        loo=[]
        for omit in m:
            a=math.prod(1+v/100 for k,v in m.items() if k!=omit)
            b=math.prod(1+v/100 for k,v in bm.items() if k!=omit)
            loo.append(100*(a-b))
        # Screening only; existing original DD gate is known invalid.
        half_gate=all(d>=1 for d in hd)
        comparison=dict(id=row['id'],half_deltas=hd,monthly_deltas=deltas,
            min_compounded_leave_one_month_out=min(loo),both_halves_at_least_1=half_gate,
            both_halves_at_least_2=all(d>=2 for d in hd),
            technical_release=False,reason='Known fill/stop/data-model issues; repeated development sample')
        comparisons.append(comparison)
        header.append(f'| {row["id"]} | {diff} | {", ".join(sorted(set(row["groups"])))} | {fmt(r["return_pct"])} | {fmt(h[0])} / {fmt(h[1])} | {fmt(r["dd_close_pct"])} | {fmt(r["fees"])} | {r["orders"]} / {r["zero_orders"]} | {fmt(r["avg_exposure_pct"])} | {fmt(row["scenarios"][2]["return_pct"])} | {fmt(row["scenarios"][3]["return_pct"])} |')
    header+=['','* Eine Zeile mit Short-Handel ist wegen F02 (fehlende Kapitalbindung/Margin, kein Funding) ausdrücklich keine vergleichbare unverschuldete Rendite. Alle Details und Signale: `grid/Vxxx.json`.',
             '', '## Hälften und Konzentration','', '| ID | Δ H1 Punkte | Δ H2 Punkte | Kleinster verzinster Vorteil ohne einen Monat, Punkte | beide ≥1 |','|---|---:|---:|---:|---|']
    for r in comparisons:
        header.append(f'| {r["id"]} | {fmt(r["half_deltas"][0])} | {fmt(r["half_deltas"][1])} | {fmt(r["min_compounded_leave_one_month_out"])} | {r["both_halves_at_least_1"]} |')
    header+=['','Ein bestandener Hälftenfilter ist keine Erfolgswahrscheinlichkeit. Die 79 Zeilen sind korreliert; schon früher wurden viele Varianten auf diesen Daten gewählt. 5 % pro Zeile wären bei unabhängigen 79 Nullhypothesen etwa vier zufällige Treffer. Die unbekannte Gesamtzahl historischer Versuche verhindert eine seriöse exakte nachträgliche Korrektur.',
        '', '## Getrennt vorab geplante Ergänzungen', '',
        'Das ursprüngliche E4-Gitter n=3/4/5/6 × k=2/3 wurde nach dem Vollständigkeitsabgleich separat vorab festgeschrieben (098a65d) und vollständig auf derselben Basis gemessen: [STRUKTUR.md](STRUKTUR.md). Eine Zeile ist V000; sieben Konfigurationen kommen hinzu, somit 86 eindeutige Handelskonfigurationen. Die ergänzenden Kapitalquoten 100/60/50 % sind in [KAPITAL.md](KAPITAL.md) ausgewiesen. Beide Ergänzungen werden nicht rückwirkend dem anfänglichen 79-Zeilen-Plan zugeschrieben.',
        '', 'Nicht untersucht: das vollständige kartesische Produkt aller Schalter, neue nach Ergebnis ausgewählte Schwellen, Kombinationen mit archivisch nicht verfügbaren Mehrbörsen-/On-Chain-Rohdaten, echte Tick-Ausführung, Short-Funding. Weitere Kombinationen außerhalb der fünf begründeten Gitter und der historischen E4-Ergänzung benötigen eine eigene Vorfestlegung und möglichst neue Daten.']
    (OUT/'KOMBINATIONEN.md').write_text('\n'.join(header)+'\n',encoding='utf-8')
    (OUT/'gitter-vergleich.json').write_text(json.dumps(comparisons,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Both halves >=1:',[r['id'] for r in comparisons if r['both_halves_at_least_1']])
    for row in rows[:8]:
        r=row['scenarios'][0]
        print(row['id'],row['diff'],'r',round(r['return_pct'],3),'close',round(row['scenarios'][1]['return_pct'],3),'next',round(row['scenarios'][2]['return_pct'],3),'stress',round(row['scenarios'][3]['return_pct'],3),'DD close execution',row['scenarios'][1]['dd_intrabar_range_pct'])

if __name__=='__main__':main()
