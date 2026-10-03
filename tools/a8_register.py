"""Write the explicit 22-ID A8 end states without erasing prior JSON evidence."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/audit-nacharbeit-2026-10'
BASE='419e3fda6494645b3c227350f1b5145bffd6271a'
# ID: current scope, code/evidence anchor, genuine remaining boundary.
REVIEWS={
'F01':('V1/i+2-Schlussrisiko und Intrabar-Bänder erhalten; alte Signalbuch-DD getrennt.', 'engine/execution_v1.py:462; engine/test_execution_v1.py:74; A7-resultindex-v1.json', 'Intrabar-Reihenfolge und reale Ausführung nicht bewiesen.'),
'F02':('A5-Handbuch, 84h-Einzelfall und kausaler Derivatpfad getrennt geprüft; A8 korrigiert Zykluspeak und Walletbudget, unabhängige Fraction-Buchung.', 'engine/execution_perp_offline.py:107; engine/test_a8_acceptance.py:21; tools/a8_perp_reference.py:20; A8-V035-causal-v2.json', 'V035 ohne historische Gesamtrendite: 13.02.19:00 UTC fehlt Zahlungssatz bei 0,0818 BTC Short. Hypothetischer Nulllauf verletzt 1x am 17.04.14:00 UTC; Mai-Long 0,1088 BTC nur ungültige Diagnose. Tarif, echte Fills und Liquidationsvertrag unbelegt.'),
'F03':('Monotone Stopgrenze und JSON-Fortsetzung erhalten und regressionsgeprüft.', 'engine/strategy_core.py:1312; engine/test_stage4.py:180', 'Nur geprüfter Long-/Stopvertrag; keine Garantie realer Stopausführung.'),
'F04':('Einstand aus tatsächlichen simulierten BTC-Losen und Kosten; unabhängige A7-Spotkonten erhalten.', 'engine/inventory.py:1; engine/execution_v1.py:143; engine/test_stage4.py:34', 'Unbekannte manuelle Live-Kostenbasis wird nicht rekonstruiert.'),
'F05':('Widerstandszähler im Positionsschema/Restart erhalten; keine Aktivierung.', 'engine/position_state.py:58; engine/strategy_core.py:1242; engine/test_stage4.py', 'Widerstandsausstieg bleibt ausgeschaltet; Aktivierungswirkung nicht belegt.'),
'F06':('Versatzinvariante USD-Fensterdeltas einschließlich aggregiertem BTC-Spotfall geprüft; A7-Ereigniswirkung getrennt.', 'engine/strategy_core.py:1097; engine/test_a2_flow.py:13; A7-intermediate-A2-S0-v1.json', 'Alte alt-Zeilen bleiben historische Diagnose; keine allgemeine Renditeverbesserung aus der Messkorrektur.'),
'F07':('Kein OI vor modellierter Verfügbarkeit; kausale Fortschreibung bis 8h mit Herkunft/Alter geprüft.', 'engine/flow_contract.py:24; engine/test_a2_flow.py:46; A7-ABLEITUNGSVERTRAG-v2.md', 'Damalige API-Veröffentlichung und Latenz unbewiesen; R0/R1 unverändert.'),
'F08':('Sechs geschlossene eindeutige UTC-Slots; A8 verwirft zusätzlich Tage mit falsch ausgerichteten Zusatzpunkten.', 'engine/strategy_core.py:319; engine/test_a8_acceptance.py:13; A8-counterexamples-v1.json', 'Eingangsadapter müssen D01-Schlussvertrag erfüllen; historische Publikation unbewiesen.'),
'F09':('Flat-/Rest- und Zyklusbehandlung im Spotbuch erhalten; begrenzte A7-Losrundung samt echtem Oversell geprüft.', 'engine/inventory.py:22; engine/execution_v1.py:278; engine/test_a7_numerical.py:8', 'Rundungstoleranz ist numerisch begrenzt; unbekannte echte Restbestände nicht umfasst.'),
'F10':('Gemeinsamer Stop-Resolver für Engine und Plan, read-only Plan und gespeicherte Stopgrenze geprüft.', 'engine/strategy_core.py:1312; engine/test_stage4.py:195', 'Kein Nachweis real platzierter oder ausgeführter Stoporders.'),
'F11':('Echte JSON-Booleans erforderlich; Text false, Zahlen und null werden abgewiesen; gültige Konfiguration erhalten.', 'engine/main.py:394; engine/test_main.py:358; A1-BERICHT.md', 'Andere numerische Konfigurationsfragen außerhalb dieser Korrektur; kein Live-Go.'),
'F12':('Kausale nächste-Open-/i+2-Modelle geprüft, alte Level-/Close-Ergebnisse ausdrücklich separat.', 'engine/execution_v1.py:93; engine/test_execution_v1.py:253; A5-VERTRAG.md:66', 'V2-Orderstrategie nicht beauftragt; damalige Orders, Intrabar-Liquidität und Fills fehlen. E41.6 und manuelle Bestände ausgeschlossen.'),
'F13':('Externe SQLite-Intents/Quittungen und Wiederherstellung nach harten Runnerabbrüchen simuliert geprüft; alle vier Einmalpfade einbezogen.', 'engine/durable_delivery.py:117; engine/test_a4_delivery.py:146; A4-BETRIEB.md', 'Geeignetes Volume, Migration und Runneranbindung real nicht bereitgestellt. Kein Schutz bei Volume-Verlust/NFS/getrennten Kopien/altem Backup; uncertain bleibt gesperrt, kein Exactly-once.'),
'F14':('Vollständiger angeforderter Korb; A8 schließt nichtendliche Messungen und ungültige OI-Gewichte punktweise aus.', 'engine/coinalyze.py:595; engine/coinalyze.py:853; engine/test_a8_acceptance.py:45', 'Historischer Point-in-time-Börsenkorb fehlt; historische Aggregatvarianten bleiben gesperrt.'),
'F15':('Volumenvergleich erst nach belegter USD-Normalisierung; BTC/USD-Handfall und fehlende Quote-Konversion geprüft.', 'engine/coinalyze.py:349; engine/test_a3_data.py:48; A3-VERTRAG.md', 'Historische Marktlisten und zeitgleiche Quote/USD-Konversion fehlen; keine historische Aggregatrangfolge.'),
'F16':('Kurzer ATR-Vorlauf gegen unabhängige True Ranges geprüft; lange Fenster erhalten.', 'engine/strategy_core.py:150; engine/test_strategy_core.py:28; A1-BERICHT.md', 'ATR-Messkorrektur belegt keine handelbare Performance.'),
'F17':('Quellengetrennte Chartidentität, Kollisionen, Reload und Modellkennzeichnung in netzfreier Regression erhalten.', 'docs/nacharbeit-2026-09-28/F17-VERTRAG.md:1; engine/test_stage5b.py:15', 'Live-Signalreferenz ist kein Brokerfill; Identität alter ununterscheidbarer Kopien bleibt begrenzt.'),
'D01':('Abgeschlossene 4h-Eingaben und unveränderter historischer Cutoff erhalten; alle eingefrorenen 2493 Kerzen geprüft.', 'engine/test_d01_kerzenschluss.py:1; tools/a8_acceptance.py:70', 'Beschaffungs-/Veröffentlichungszeitpunkt damals nicht bewiesen.'),
'D02':('Missing/stale und gemessene Null getrennt; fehlendes Funding bestätigt Long nicht; Metadaten im Checkpoint erhalten.', 'engine/flow_contract.py:49; engine/strategy_core.py:1472; engine/test_a2_flow.py:66', 'Alte metadatenlose Werte bleiben unbewiesen; vier aktive Liquidationslücken bleiben missing.'),
'M01':('76 Entscheidungen mit damaliger Basis/Fenster und 85 alte Codezeilen geprüft; keine Ersetzung alter Basis durch V000.', 'A7-M01-M02-BEWERTUNG.md:1; A7-M01-M02-zuordnung-v1.json', 'Nicht alle früheren Daten-/Basisstände rekonstruierbar; Chronik keine Replikation oder Übertragung auf heutige Basis.'),
'M02':('Zehn bedingte Paarstatistiken und mindestens 94 dokumentierte Suchen eingeordnet; Ergebnis-/Modellfamilien getrennt.', 'A7-M01-M02-BEWERTUNG.md:91; A7-paired-statistics-v1.json; docs/nach-6/search-inventory.json', 'Unbekannte vollständige Suchfamilie, wiederverwendete Monate und überlappende R0/R1-Fenster; keine Auswahlbereinigung, unabhängige Stichprobe oder Zukunftsprognose.'),
'T01':('316 Originalmutationen vollständig zugeordnet; Treffer und erreichte Fehler von Vertragsablösungen/historischen Fällen getrennt; E41-Teilverkaufsreihenfolge erhalten.', 'tools/a6_mutations.py:27; engine/test_a6_regression.py:70; tools/a8_acceptance.py:77; A6-summary.json', 'Fünf abgelöste und 25 nur historische Fälle sind keine aktuellen Treffer; keine Live- oder Performanceabnahme.')}


def main():
    path=DOC/'REGISTER.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    assert len(data['findings'])==22 and set(REVIEWS)=={x['id'] for x in data['findings']}
    data.setdefault('pre_a8_register_metadata',{k:data[k] for k in ('stage','as_of','base_commit')})
    data.update(stage='A8_fachlich_abgenommen',as_of='2026-10-03',base_commit=BASE,
                a8_base_commit=BASE,a8_live_approval=False,
                a8_completion_evidence=['A8-ABSCHLUSSBERICHT.md','A8-acceptance-v1.json','A8-V035-causal-v2.json','A8-counterexamples-v1.json'],
                a8_operational_closure='Exact final commit, CI and verified bundle restore: external A8 UEBERGABE.md/json',
                a8_status_counts={'korrigiert_geprueft':17,'teilweise_erledigt':3,'offene_grenze':2})
    lines=['# Vollständiges Befundregister – verbindlicher A8-Endstand','',
        '03.10.2026; geprüft ab `'+BASE+'`. Alle 22 Original-IDs erhalten.',
        '17 korrigiert/geprüft, 3 mit klarer Reichweite teilweise erledigt, 2 bewertete offene Grenzen.',
        'Kein Live-Go. Exakte Abschluss-SHA, finale CI und Restore stehen in der additiven A8-Übergabe.',
        'Der [A8-Bericht](A8-ABSCHLUSSBERICHT.md) und die folgenden Endstatus ersetzen die früheren aktuellen Registerformulierungen.',
        'Die Historie ist in Git und den unveränderten A1–A7-Belegen sowie den historischen JSON-Feldern erhalten.',
        'Insbesondere sind A7/v1-V035-Mengen und die Risikouhrzeit überholt; maßgeblich ist [A8/v2](A8-V035-causal-v2.json).','',
        '| ID / Priorität | Endstatus und geprüfte Reichweite | Datei/Zeile und Beleg | Verbleibende Grenze |',
        '|---|---|---|---|']
    for row in data['findings']:
        rid=row['id']; scope,refs,limit=REVIEWS[rid]
        priority='P1' if rid in {'F01','F02','F03','F04','F09','F10','F12','F13','F17'} else 'P3' if rid in {'F05','F11','F15','F16'} else 'P2'
        category='teilweise_erledigt' if rid in {'F02','F12','F13'} else 'offene_grenze' if rid in {'M01','M02'} else 'korrigiert_geprueft'
        status={'korrigiert_geprueft':'A8 korrigiert/geprüft','teilweise_erledigt':'A8 teilweise erledigt – Reichweite ausdrücklich begrenzt','offene_grenze':'A8 bewertet – nachvollziehbare offene Grenze'}[category]
        row.setdefault('pre_a8_status',{k:row.get(k) for k in ('status','scope','next_stage','remaining_limit')})
        row.update(status=status,scope=scope,remaining_limit=limit,next_stage=None,
                   a8_category=category,a8_priority=priority,a8_assessment=scope,a8_evidence=refs.split('; '),
                   a8_base_commit=BASE,a8_completion_commit='external A8 handoff; no self-referential SHA')
        lines.append(f'| {rid} / {priority} | **{status}**. {scope} | {refs} | {limit} |')
    path.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    (DOC/'REGISTER.md').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
    print('A8 register: 22 IDs; 17 checked, 3 partial, 2 open boundaries')


if __name__=='__main__': main()
