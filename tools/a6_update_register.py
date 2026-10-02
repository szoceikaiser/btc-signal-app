"""Carry all 22 audit findings into A6 without changing their prior decisions."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
docs = root / 'docs/audit-nacharbeit-2026-10'
path = docs / 'REGISTER.json'
data = json.loads(path.read_text(encoding='utf-8'))
assert data['stage'] == 'A5'
assert len(data['findings']) == len({r['id'] for r in data['findings']}) == 22
data['stage'] = 'A6'
data['base_commit'] = '772221ecda67dad50f6190d8e1319476eb7129e3'
for row in data['findings']:
    row['a6_regression'] = ('A6 final combined test run; T01 mapping and A1-A5 '
                            'contract mutations in A6-BERICHT.md. Prior scope preserved.')
    if row['id'] == 'T01':
        row['status'] = 'A6 Schutzproben vollständig zugeordnet und erreichte aktuelle Mutationen geprüft'
        row['scope'] = ('316 Originalfälle: 243 Assertion, 13 beabsichtigte Laufzeit-/Testfehler, '
                        '30 erreichte aktuelle Entsprechungen; 5 durch A2-Vertrag abgelöst und '
                        '25 nur am Original-Auditstand vorhanden. Sieben ursprünglich veraltete '
                        'Vorlagen aktuell 7/7 erkannt; E41-Wartekerze mit Teilverkauf.')
        row['next_stage'] = 'A7 Ergebnisfolgen, A8 Gesamtabnahme'
        row['remaining_limit'] = ('Historische E44.4/E44.5-Programme bleiben am Originalcommit; '
                                  'keine neue historische Renditemessung oder Live-Abnahme durch A6.')
        row['evidence'] = ['A6-BERICHT.md', 'A6-mapping.json', 'A6-summary.json',
                           'A6-mutations.json', 'engine/test_a6_regression.py']
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

md = docs / 'REGISTER.md'
text = md.read_text(encoding='utf-8')
text = text.replace('Stand: A5, Basis `291588946206333ca58d771f1cc96f261da1a981`.',
                    'Stand: A6, Basis `772221ecda67dad50f6190d8e1319476eb7129e3`.')
text = text.replace('A5-Status und Reichweite', 'A6-Status und Reichweite')
old = '| T01 | P3-Tabelle (ca. Z. 185); veraltete Sabotagen und fehlende E41-Reihenfolgeprobe | Etappe 5a erreichte E41-Wartekerze mit Teilverkäufen | Erhalten, durch A4 nicht geändert | A6 | Keine pauschale Schließung der übrigen alten Vorlagenlücken |'
new = ('| T01 | P3-Tabelle (ca. Z. 185); veraltete Sabotagen und fehlende E41-Reihenfolgeprobe '
       '| Etappe 5a erreichte E41-Wartekerze mit Teilverkäufen; A6 ordnet alle 316 Originalfälle zu '
       '| **A6 geprüft:** 243 aktuelle Assertions, 13 erreichte beabsichtigte Fehlerzweige, '
       '30 erreichte aktuelle Entsprechungen; sieben ursprünglich veraltete Vorlagen 7/7 erkannt. '
       'Fünf A2-Vertragswechsel und 25 am A5-Stand fehlende historische E44.4/E44.5-Fälle '
       'ausdrücklich nicht als aktuelle Treffer gezählt | A7/A8 '
       '| Historische Originalprogramme bleiben am Auditcommit; keine Renditemessung oder Live-Abnahme durch A6 |')
assert old in text
text = text.replace(old, new)
text += ('\nA6 führt sämtliche 22 IDs fort; nur T01 erhält einen neuen fachlichen Status. '
         'A1–A5-Status und Grenzen bleiben erhalten. Die [A6-Zuordnung](A6-mapping.json) '
         'und [Bilanz](A6-summary.json) trennen Treffer, ersetzte Vorlagen und '
         'historische Originalfälle. Der [A6-Bericht](A6-BERICHT.md) enthält '
         'Prüfungen, Reichweite und offene Betriebs-/Datengrenzen.\n')
md.write_text(text, encoding='utf-8')
