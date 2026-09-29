"""Read saved evidence only; render stage-4 differences and the result table."""
from datetime import datetime, timezone
import gzip
from itertools import zip_longest
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]/'docs/nacharbeit-2026-09-28'
report = json.loads((OUT/'4-ergebnis.json').read_text(encoding='utf-8'))
prior = json.loads((OUT/'3b-ergebnis.json').read_text(encoding='utf-8'))
with gzip.open(OUT/'4-ledger.json.gz', 'rt', encoding='utf-8') as stream:
    rows = json.load(stream)
differences = []
for oldrow, newrow in zip(prior['rows'], rows):
    assert oldrow['params'] == newrow['params']
    for old, new in zip(oldrow['scenarios'], newrow['scenarios']):
        a, b = old['result'], new['result']
        def first_difference(aa, bb, keys):
            for x, y in zip_longest(aa, bb):
                xx = {k: x.get(k) for k in keys} if x else None
                yy = {k: y.get(k) for k in keys} if y else None
                if xx != yy:
                    return dict(before=xx, after=yy)
            return None
        delta = dict(name=newrow['name'], slippage_pct=b['slippage_pct'],
            first_candidate_difference=first_difference(a['signals'], b['signals'],
                ('ts', 'type', 'price', 'reason')),
            first_fill_difference=first_difference(
                [e for e in a['ledger'] if e['status']=='filled'],
                [e for e in b['ledger'] if e['status']=='filled'],
                ('fill_at', 'type', 'quantity', 'fill_price', 'fee')),
            first_entry_difference=first_difference(a['feedback'], b['feedback'],
                ('at', 'state', 'entry_ref', 'entry_pct')))
        differences.append(delta)
(OUT/'4-differenzen.json').write_text(json.dumps(differences, indent=2, ensure_ascii=False), encoding='utf-8')

def de(number, places=2):
    return f'{number:,.{places}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

table = ['| Zeile | Slippage je Seite | Endwert USD | Differenz zu 3b USD | Close-DD % | **obere Intrabar-Grenze %** | Fills |',
         '|---|---:|---:|---:|---:|---:|---:|']
for i, s in enumerate(report['summaries']):
    table.append(f"| {'Live-Basis' if i<3 else 'E42 / 12'} | {de(s['slippage_pct'],1)} % | "
                 f"{de(s['end'])} | {de(s['delta_end'])} | {de(s['dd_close'],4)} | "
                 f"**{de(s['dd_upper'],4)}** | {s['fills']} |")
p = OUT/'ETAPPE-4-ABSCHLUSS.md'
text = p.read_text(encoding='utf-8')
text = text.replace('<!-- RESULT_TABLE -->', '\n'.join(table))
text = text.replace('Abnahme in Durchführung.', 'Lokal geprüft; Remote-/Sicherungsabnahme zur exakten SHA in ABSCHLUSS.json.')
for old, new in {'in3b':'in 3b', '3b19/19':'3b 19/19', 'D016/6':'D01 6/6', 'F093/3':'F09 3/3',
    'mit45':'mit 45', 'zu220':'zu 220', 'zu172':'zu 172', 'nicht188':'nicht 188',
    'Struktur115':'Struktur 115', 'Close120':'Close 120', 'Close110':'Close 110', 'Plan115':'Plan 115',
    'Zähler1':'Zähler 1', 'auf2':'auf 2', 'Struktur145':'Struktur 145', 'Einstand140':'Einstand 140',
    'Stop145':'Stop 145', 'Struktur120':'Struktur 120', 'Einstand115':'Einstand 115',
    'Muster2':'Muster 2', 'Kerzen-ID184':'Kerzen-ID 184', 'Stop135':'Stop 135',
    'aufmain':'auf main', 'aufTests':'auf Tests', 'und3b':'und 3b', 'Objekt7':'Objekt 7',
    'auf469':'auf 469', 'bleibt5a':'bleibt 5a', 'bleibt5b':'bleibt 5b',
    'Etappe4':'Etappe 4', 'Etappe5a':'Etappe 5a', 'abgerufen28':'abgerufen 28',
    '0,1%':'0,1 %'}.items():
    text = text.replace(old,new)
p.write_text(text,encoding='utf-8')
print(json.dumps(dict(differences=len(differences), table_rows=len(report['summaries']),
    fills_checked=sum(s['fills'] for s in report['summaries']),
    closes_checked=sum(s['costs_verified']['closes'] for s in report['summaries'])), indent=2))
