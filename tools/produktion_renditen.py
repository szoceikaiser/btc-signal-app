"""Compile existing evidence only: no market requests, strategy runs or optimization."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT/'docs/produktionsuebernahme-2026-10'
A7 = 'docs/audit-nacharbeit-2026-10/'
OLD = 'docs/nacharbeit-2026-09-28/'
ORIGINAL = 'ccf2b01c0578346f325261e72445b7375a9ac706'
AUDIT = '881e36a6271a6e49400d47da59342755e33cf402'
SOURCES = {}


def read(path, revision=None):
    # Immutable Git blobs make source hashes independent of checkout line endings.
    raw = subprocess.check_output(['git', 'show', f'{revision or AUDIT}:{path}'], cwd=ROOT)
    if revision is None:
        actual = (ROOT/path).read_bytes()
        assert actual.replace(b'\r\n', b'\n') == raw.replace(b'\r\n', b'\n'), path
    key = f'{revision}:{path}' if revision else path
    # Text hashes are Git-blob hashes when a revision is named, local evidence otherwise.
    SOURCES[key] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def utc(ms):
    return datetime.fromtimestamp(ms/1000, timezone.utc).isoformat() if ms is not None else ''


def fmt(value):
    return '—' if value is None else f'{value:+.2f}'.replace('.', ',')


def emit(name, content, verify):
    path = DOC/name
    if verify:
        assert path.read_text(encoding='utf-8') == content, name+' differs from evidence'
    else:
        path.write_text(content, encoding='utf-8', newline='\n')


def compile_report(verify=False):
    design = read(A7+'A7-analysemanifest-v1.json')
    index = read(A7+'A7-resultindex-v1.json')
    variants, stage_rows, old_rows = [], [], {}
    defs = {x['id']: x for x in design['rows']}
    baseline = defs['V000']['params']
    assert len(defs) == 86 and 'S004' not in defs

    def label(rid):
        changes = {k: v for k, v in defs[rid]['params'].items() if baseline.get(k) != v}
        return ', '.join(f'{k}={str(v).lower()}' for k, v in changes.items()) or 'Basis'

    def record(stage, lane, package, rid, total=None, h1=None, h2=None, source='', **extra):
        row = dict(stage=stage, family=lane, package=package, id=rid,
                   configuration=label(rid), total_pct=total, half1_pct=h1, half2_pct=h2,
                   source=source, **extra)
        variants.append(row)
        return row

    for rid in defs:
        path = f'docs/audit-2026-09-27/{"struktur" if rid.startswith("S") else "grid"}/{rid}.json'
        old = read(path, ORIGINAL)
        if rid == 'V035':
            old_rows[rid] = record('Originalaudit', 'Level-Diagnose', 'R0', rid,
                                  source=f'{ORIGINAL}:{path}', status='gesperrt F02; alte Shortzahl nicht freigegeben')
            for lane in ('Level-Diagnose korrigiert', 'kausal S0'):
                for package in ('R0', 'R1'):
                    record('A7/A8', lane, package, rid, source=A7+'A8-ABSCHLUSSBERICHT.md',
                           status='gesperrt F02; keine historische Gesamtrendite')
            continue
        level = next(x for x in old['scenarios'] if x['scenario']['fill'] == 'level')
        halves = old['halves']
        old_rows[rid] = record('Originalaudit', 'Level-Diagnose', 'R0', rid, level['return_pct'],
                halves[0]['independent']['return_pct'], halves[1]['independent']['return_pct'],
                source=f'{ORIGINAL}:{path}', half1_start=utc(halves[0]['start']),
                half1_end=utc(halves[0]['end']), half2_start=utc(halves[1]['start']),
                half2_end=utc(halves[1]['end']), status='retrospektiv; keine historische Orderausführung bewiesen')
        for package, data in index['rows'][rid]['packages'].items():
            for scenario, result in data['causal'].items():
                raw = read(result['source']['file'])
                assert raw['detail']['rendite_pct'] == result['return_pct']
                assert hashlib.sha256((ROOT/result['source']['file']).read_bytes()).hexdigest() == result['source']['sha256']
                hs = data['halves_S0'] if scenario == 'S0' else None
                extra = {}
                if hs:
                    for name, h in hs.items():
                        raw_h = read(h['source']['file'])
                        assert raw_h['detail']['rendite_pct'] == h['return_pct']
                        assert SOURCES[h['source']['file']] == h['source']['sha256']
                        extra[name+'_start'] = utc(h['start_ms'])
                        extra[name+'_end'] = utc(h['cutoff_ms'])
                record('A7/A8', 'kausal '+scenario, package, rid, result['return_pct'],
                    hs['half1']['return_pct'] if hs else None, hs['half2']['return_pct'] if hs else None,
                    source=result['source']['file'], total_start=utc(result['start_ms']),
                    total_cutoff=utc(result['cutoff_ms']),
                    status='bedingtes Spotmodell; Hälften nur in S0 gerechnet' if not hs else 'bedingtes Spotmodell; getrennte Frischstarts', **extra)
            legacy = data['legacy_diagnostic']
            halves = legacy['level_fresh_halves']
            read(legacy['source']['file'])
            read(legacy['halves_source']['file'])
            record('A7/A8', 'Level-Diagnose korrigiert', package, rid,
                   legacy['cases']['level']['return_pct'], halves[0]['account']['return_pct'],
                   halves[1]['account']['return_pct'], source=legacy['source']['file'],
                   half1_start=utc(halves[0]['start_ms']), half1_end=utc(halves[0]['end_ms']),
                   half2_start=utc(halves[1]['start_ms']), half2_end=utc(halves[1]['end_ms']),
                   status='retrospektiv; keine historische Orderausführung bewiesen')

    # Old stages: keep absent half-runs absent, even when later totals match exactly.
    def stage(name, row_name, total, source, family, h1=None, h2=None, note='Keine eigenen Halbzeitläufe belegt.'):
        stage_rows.append(dict(stage=name, row=row_name, total_pct=total,
            half1_pct=h1, half2_pct=h2, source=source, family=family, note=note))

    for rid in ('V000', 'V004'):
        r = old_rows[rid]
        stage('Originalaudit', 'Basis' if rid == 'V000' else 'E42', r['total_pct'], r['source'], r['family'],
              r['half1_pct'], r['half2_pct'], 'Getrennte Frischstarts, damalige Level-Diagnose.')
    f09 = read(OLD+'f09-ergebnis.json')
    for r in f09['rows']:
        stage('1 / F09', r['name'], 100*(r['after_end']/f09['start_capital']-1), OLD+'f09-ergebnis.json',
              'alte Level-Simulation; ursprüngliche laufende Schlusskerze enthalten')
    d01 = read(OLD+'d01-ergebnis.json')
    for r in d01['rows']:
        stage('2 / D01', r['name'], r['after']['rendite_pct'], OLD+'d01-ergebnis.json', 'Level-Simulation; nur geschlossene Kerzen')
    b = read(OLD+'3b-ergebnis.json')
    for r in b['rows']:
        for s in r['scenarios']:
            v = s['result']
            stage('3b / Ausführung', r['name']+f" / Slippage {v['slippage_pct']} %", v['rendite_pct'], OLD+'3b-ergebnis.json', 'kausal V1')
    for number in ('4', '6'):
        path = OLD+number+'-ergebnis.json'
        d = read(path)
        for r in d['summaries']:
            stage(number, r['name']+f" / Slippage {r['slippage_pct']} %", 100*(r['end']/10000-1), path, 'kausal V1')
    for package in ('R0', 'R1'):
        path = f'docs/nach-6/{package}/results.json'
        d = read(path)
        for result in d['results']:
            if result['start_index'] != 0:
                continue
            for r in result['rows']:
                stage('Nach-6 '+package, r['name']+' / '+result['scenario'], r['rendite_pct'], path, r['model'],
                      note='Gesamtfenster, Drittel und Drittel-Frischstarts; keine eigenen Halbzeitläufe.')
    for r in variants:
        if r['stage'] == 'A7/A8' and r['family'] == 'kausal S0' and r['id'] in ('V000', 'V004'):
            stage('A7/A8 '+r['package'], 'Basis' if r['id'] == 'V000' else 'E42', r['total_pct'], r['source'],
                  r['family'], r['half1_pct'], r['half2_pct'], 'A8 bestätigte die unveränderten A7-Spotreihen.')

    def csv_text(rows):
        fields = list(dict.fromkeys(k for row in rows for k in row))
        out = io.StringIO(newline='')
        writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
        return out.getvalue()

    emit('RENDITEN-VARIANTEN.csv', csv_text(variants), verify)
    emit('RENDITEN-ETAPPEN.csv', csv_text(stage_rows), verify)
    def find(rid, package, family):
        return next(r for r in variants if r['stage'] == 'A7/A8' and r['id'] == rid and r['package'] == package and r['family'] == family)

    lines = ['# Renditeaufstellung der Prüfungen', '',
        'Aus vorhandenen eingefrorenen Belegen erstellt; keine neue Strategie gerechnet oder optimiert.',
        'Alle Werte sind Prozent, keine Jahresrenditen und keine Ergebnisse deines echten Kontos.',
        '**H1 und H2 starten getrennt mit neuem Kapital und leerem Bestand.** Deshalb sind sie weder',
        'zu addieren noch zu einer Gesamtrendite zu verketten. Ein Strich bedeutet fehlender bzw.',
        'nicht durchgeführter Halbzeitnachweis, niemals 0 %. V035 bleibt ausdrücklich gesperrt.', '',
        '## Etappen: Basis und E42', '',
        '| Etappe / Daten / Modell | Konfiguration | Gesamt % | H1 % | H2 % |',
        '|---|---|---:|---:|---:|']
    selected = []
    for r in stage_rows:
        # The complete 5-row/3-cost details remain in the accompanying stage CSV.
        name = r['row']
        if r['stage'] in ('Originalaudit', 'A7/A8 R0', 'A7/A8 R1'):
            selected.append(r)
        elif name.split(' / ')[0] in ('LIVE-heute +Bein in Handelsrichtung', 'LIVE-heute +E42'):
            if '/ Slippage' not in name or '/ Slippage 0.0 %' in name:
                if not r['stage'].startswith('Nach-6') or name.endswith('/ S0'):
                    selected.append(r)
    for r in selected:
        name = 'E42' if 'E42' in r['row'] else 'Basis'
        lines.append(f"| {r['stage']} / {r['family']} | {name} | {fmt(r['total_pct'])} | {fmt(r['half1_pct'])} | {fmt(r['half2_pct'])} |")
    lines += ['', 'Die frühen Schritte 1/2 verwendeten noch die alte Simulation; Originalaudit und A7-Level-',
        'Diagnose sind ebenfalls keine belegten historischen Orders. Die kausalen V1-Rechnungen ab 3b',
        'verwenden einen anderen Ausführungs-/Rückkopplungsvertrag. Unterschiede sind daher nicht',
        'pauschal zusätzliche oder verlorene Handelsgewinne durch eine einzelne Korrektur.', '',
        'Etappe 3a legte den Vertrag fest; 5a/5b betrafen Versand und Chart. A1–A6 prüften Korrekturen',
        'und Handfälle, ohne jeweils neue vollständige historische H1/H2-Reihen zu erzeugen.',
        'A7 berechnete die bedingten Reihen; A8 bestätigte die Spotreihen unverändert und erneuerte',
        'nur die betroffenen V035-Diagnosen. Die Short-Handprobe ist keine Gesamtrendite.', '',
        'R0 reicht bis zum festgehaltenen Beobachtungsschluss am 27.09.2026; R1 ergänzt 13 geschlossene',
        '4h-Kerzen bis 29.09.2026 12:00 UTC. Beide Fenster beginnen am 18.01.2026 20:00 UTC.',
        'Die exakten halboffenen Zeitgrenzen je Lauf stehen in der Varianten-CSV. Die Grenzen der',
        'ursprünglichen Hälften und der auf 4h ausgerichteten späteren Hälften sind nicht identisch.', '',
        '## Alle ursprünglichen Konfigurationen: aktuelles kausales S0-Modell', '',
        'S0: 0,1 % Gebühr je Fill, kein zusätzlicher Slippage-Aufschlag, simulierte Ausführung am',
        'nächsten 4h-Open. Historische API-Verfügbarkeit und tatsächliche Fills bleiben unbewiesen.',
        '86 eindeutige Konfigurationen einschließlich V035; S004 ist der Alias von V000.',
        'Die alten Parameterbezeichnungen bleiben zur Zuordnung erhalten; A2 übersetzt `muster_cvd=alt`',
        'im korrigierten Modell zu `usd`. Die ausgeschriebene Änderung steht relativ zum Original-V000.', '',
        '| ID | Änderung | R0 Gesamt % | R0 H1 % | R0 H2 % | R1 Gesamt % | R1 H1 % | R1 H2 % |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for rid in defs:
        a, b = find(rid, 'R0', 'kausal S0'), find(rid, 'R1', 'kausal S0')
        cells = [fmt(x[k]) for x in (a,b) for k in ('total_pct','half1_pct','half2_pct')]
        lines.append('| '+rid+' | '+label(rid)+(' — GESPERRT F02' if rid=='V035' else '')+' | '+' | '.join(cells)+' |')
    lines += ['', '## Ausführung und Kosten: feste Basis/E42-Paare', '',
        'Für S1–S4 wurden Gesamtfenster und Drittel gerechnet, keine zusätzlichen H1/H2-Reihen.',
        'Die Halbzeitergebnisse aus S0 werden nicht auf diese Szenarien übertragen.', '',
        '| Daten | Szenario | Basis gesamt % | E42 gesamt % | E42 minus Basis pp |',
        '|---|---|---:|---:|---:|']
    for package in ('R0','R1'):
        for s in range(5):
            a,b=(find(r, package, 'kausal S'+str(s)) for r in ('V000','V004'))
            lines.append(f"| {package} | S{s} | {fmt(a['total_pct'])} | {fmt(b['total_pct'])} | {fmt(b['total_pct']-a['total_pct'])} |")
    lines += ['', 'Die genauen Kosten-/Latenzverträge stehen in [Nach-6 plan.json](../nach-6/plan.json).',
        'Keine Gitterzeile erreicht im korrigierten Modell die alte Schwelle von +1 Prozentpunkt',
        'gegen die Basis in beiden getrennten Hälften. Einzelne höhere Gesamtwerte sind keine',
        'Freigabe. Beide Hälften wurden zuvor zur Entwicklung verwendet; es gibt keinen',
        'unabhängigen Zukunftsnachweis oder eine vollständige Korrektur für alle früheren Suchen.', '',
        '## Weitere Aufstellungen und Quellen', '',
        '- [Alle Modellfamilien und Szenarien als CSV](RENDITEN-VARIANTEN.csv): ursprüngliche Level-Diagnose, korrigierte Level-Diagnose und kausale S0–S4-Reihen getrennt.',
        '- [Alle gemessenen Etappenzeilen als CSV](RENDITEN-ETAPPEN.csv): einschließlich weiterer F09/D01-Zeilen und Kostenfälle.',
        '- [Frühere Entwicklungsentscheidungen E1–E44.6](../audit-nacharbeit-2026-10/A7-M01-M02-BEWERTUNG.md): 76 Entscheidungen mit damaliger Basis und damaligen Ergebnissen. Nicht archivierte frühere Hälften werden nicht erfunden.',
        '- [Maschinenlesbare Aufstellung und Quellhashes](RENDITEN.json).',
        '- [A8-Endregister](../audit-nacharbeit-2026-10/REGISTER.md).', '',
        'Diese Aufstellung dient der Nachvollziehbarkeit; sie entscheidet keine neue Einstellung und aktiviert nichts.', '']
    emit('RENDITEN.md', '\n'.join(lines), verify)
    output = {'schema':'production-return-evidence-v1','original_audit_commit':ORIGINAL,
        'remaining_source_commit':AUDIT,
        'new_backtests_run':False,'halves_independent_fresh_starts':True,
        'missing_values_are_not_zero':True,'variants':variants,'stages':stage_rows,
        'source_sha256':SOURCES}
    # Prevent the specifically misleading conclusions this report is meant to avoid.
    assert all(r['total_pct'] is None and r['half1_pct'] is None and r['half2_pct'] is None for r in variants if r['id']=='V035')
    assert all(r['half1_pct'] is None and r['half2_pct'] is None for r in variants if r['family'] in ('kausal S1','kausal S2','kausal S3','kausal S4'))
    for package in ('R0','R1'):
        base=find('V000',package,'kausal S0')
        assert not any(r['half1_pct']-base['half1_pct']>=1 and r['half2_pct']-base['half2_pct']>=1
                       for r in variants if r['family']=='kausal S0' and r['package']==package and r['half1_pct'] is not None)
    emit('RENDITEN.json',json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True)+'\n',verify)
    print(f'Renditen PASS: {len(variants)} family/scenario rows; {len(stage_rows)} stage rows; {len(SOURCES)} sources; no new backtest.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true')
    compile_report(parser.parse_args().verify)
