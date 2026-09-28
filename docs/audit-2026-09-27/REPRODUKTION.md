# Reproduktion, Korrekturen und Prüfprotokoll

Stand 28.09.2026. Die Originaldateien unter `docs/e445/` bleiben unverändert. Eine Neuberechnung mit anderen Daten, korrigierter Buchführung oder heutigem Parameterverbund wird ausdrücklich nicht als Reproduktion eines alten Laufs bezeichnet.

## Code, Daten und Vorfestlegung

| Bezug | Eingefrorener Stand / Beleg |
|---|---|
| main bei Beginn | `89885adc9fb6d2eae60f7a64f9452760a4e33cd9` |
| E44.4 | `eeb4eea72e3ac2baa5b713c57337801b1b8bc291` |
| E44.5 / Audit-Ausgangspunkt | `e2b0051199c2e0c38723cc3a23c00ea3bd320601` |
| Originaler E44.5-Messcode | `68e15ae`; Git-Diff der Engine gegen e2b0051 leer |
| Auditplan vor neuen Renditeläufen | Commit `f9d2e31` |
| 79 vollständig festgelegte Parameterzeilen | Commit `e7e92d30fc2c97784fdbe86079910ac27d926cec`, [gitter-plan.json](gitter-plan.json) |
| Ergebnisse des Hauptgitters gesichert | Commit `3d341ef` |
| Zusätzliche Kapitalquoten vorher festgelegt | Commit `9b916f0`, [ERGAENZUNGSPLAN.md](ERGAENZUNGSPLAN.md) |
| Originaleingaben | SHA-256 `ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a` |
| Erzeugungszeit laut Datei | 27.09.2026, 08:29:16.179427 UTC |
| Ursprüngliche GitHub-Messung | Lauf `36306294148`, Artefakt `10927810839` |
| Späteres vorhandenes Replay-Artefakt | Lauf `36321120479`, Artefakt `10931554075` |

Diese GitHub-Läufe bestanden bereits. Der Audit hat keinen Messworkflow gestartet. Die aktuelle Berechnung fand lokal auf gespeicherten Daten statt.

## Laufverzeichnis

| Lauf-ID | Inhalt | Ergebnisdateien |
|---|---|---|
| audit-20260927-00 | Zugang, Remotes, Zweige, alle Workflows, Plan | PLAN.md, inventar.json, github-metadaten.json |
| audit-20260927-01 | Bestehende Suite, Inventar, Datenvalidierung | tests-original.log, gegenproben.json/D01 |
| audit-20260927-02 | Unverändertes E44.5-Replay | reproduktion.json, reproduktion.log, replay/docs/e445/ |
| audit-20260927-03 | Unabhängige Berechnungen, Sabotagen, E42, Parität | gegenproben*.json, weitere-gegenproben.json, sabotage*, e42-faelle.json, live-backtest-paritaet.json, chart-gegenprobe.json, telegram-reihenfolge.json |
| audit-20260927-04-V000 bis V078 | Vorab definierte gemeinsame Konfigurationen, vier Ausführungsszenarien, zwei Hälften | grid/Vxxx.json, grid-run.log, gitter-vergleich.json |
| audit-20260928-05 | Vorgeplante Zusatzrechnung der Kapitalquoten und beschreibender Buy-and-Hold-Vergleich | kapital.json, KAPITAL.md |

## Exakte Reproduktion von E44.5

Laufzeit des gespeicherten Audit-Replays: 69.27 Sekunden. Alle neun Zeilen, Signalfolgen, Hälften und die ursprüngliche Entscheidungsregel wurden mit demselben Engine-Code und denselben abgeleiteten Eingaben wiederholt. Ergebnis: weiterhin keine Variante mit bestandener Originalregel.

| Datei | Bytegleich | Textgleich nach Vereinheitlichung CRLF/LF |
|---|---|---|
| BERICHT.md | False | True |
| eingaben.json | True | True |
| ergebnis.json | False | True |
| signale.json | True | True |

Die unterschiedlichen Datei-Hashes von Bericht und Ergebnis entstehen durch Zeilenenden. Es gibt dort keine inhaltliche Abweichung. Eingaben und Signale sind auch bytegleich. Alle vier ursprünglichen und vier Replay-Hashes stehen in [reproduktion.json](reproduktion.json).

## Korrekturen getrennt vom Original

Die erste Korrektur F09 entfernt ausschließlich bedeutungslose BTC-Rundungsreste bei einem vollständig geschlossenen Kapitalzyklus. Das unabhängige Losbuch verwendet keine Hilfsfunktion des Produktionssimulators. Als zweite, getrennte Änderung entfernt D01 die laufende Schlusskerze. Alle folgenden Werte sind **Endwerte in USD bei 10.000 USD Startkapital**, Gebühren 0,1 %, ursprüngliche Level-Ausführungsannahme. Diese Korrekturen beseitigen noch nicht alle Engine-/Ausführungsfehler.

| Originalzeile | Original | nur F09 korrigiert, Originalkerzen | zusätzlich D01, gemeinsame geschlossene Basis | Grid-ID |
|---|---:|---:|---:|---|
| LIVE-heute +Bein in Handelsrichtung | 13613.75 | 13613.75 | 13613.09 | V000 |
| LIVE-heute +Rest halten (E43.6) | 13541.49 | 13671.88 | 13671.51 | V001 |
| LIVE-heute +kleinere Verkaeufe | 13614.52 | 13614.52 | 13613.42 | V002 |
| LIVE-heute +kleinere Verkaeufe +Rest halten | 13791.32 | 13791.32 | 13789.62 | V003 |
| LIVE-heute +E42 | 13593.32 | 13542.22 | 13541.56 | V004 |
| LIVE-heute +E42 +Rest halten | 13457.57 | 13457.57 | 13457.21 | V005 |
| LIVE-heute +E42 +kleinere Verkaeufe | 13486.18 | 13486.18 | 13485.09 | V006 |
| LIVE-heute +E42 +kleinere Verkaeufe +Rest halten | 13467.16 | 13467.16 | 13465.51 | V007 |
| LIVE-heute +E42 (6 Kerzen, Robustheit) | 13650.87 | 13599.55 | 13598.89 | V078 |

Weitere getrennte methodische Änderungen:

- **F01:** Schluss-Drawdown und kausale OHLC-Risikogrenzen werden neu gerechnet. Der ursprüngliche Drawdown bleibt im Feld `original` erhalten. Für rückwirkende Level-Orders gibt es keine vorgetäuschte exakte Intrabar-Risikozahl.
- **Monatsprobe:** E44.5 addiert Monats-Renditedifferenzen. Der Auditbericht weist zusätzlich den verzinsten Portfoliounterschied nach Weglassen desselben Monats aus. Auch diese Kennzahl ist eine Konzentrationsdiagnose; die Strategie wird dabei nicht ohne die betreffenden Marktdaten neu gestartet.
- **F12/Kosten:** Schluss, nächste Eröffnung und zusätzliche Verzögerung sind separate Abrechnungsmodelle derselben Signalabsichten. Sie ändern nicht rückwirkend den bereits erzeugten Engine-Zustand.
- **Nicht behoben für die Renditeläufe:** insbesondere F03/F04, historische Rohdatenmängel, bedingte Intrabar-Orderlogik und Short-Margin/Funding. Ein vergleichender Auditwert ist daher keine vollständig reparierte Strategie.

**Korrektur im Audit selbst:** Die zunächst gespeicherte Beobachtung O021 wurde fälschlich als bis Datenende offen geführt; B011 erhielt zunächst den 09.04. als Ersatzdatum. Eine zusätzliche Laufzeitaufzeichnung der tatsächlichen verschachtelten Beobachtungsaufrufe zeigt die Ersetzung bereits am 07.04. 20:00 UTC, in derselben Kerze wie die Entstehung. Die Zählung 57/33/16 und sämtliche Signale/Losrenditen bleiben unverändert. Eines der 33 Ausbruchsereignisse ist daher sofort überholt, 32 bleiben über die Kerze hinaus aktiv. Frühfassung im Commit 9b916f0; Korrekturprotokoll im Feld `audit_lifetime_corrections`, unabhängige Kontrolle in `e42-ablaufkontrolle.json`. Diese Änderung ist kein Produktionsfix.

Die mathematische Hälftengrenze ist 2026-05-24T14:14:34.420000+00:00. Zuordnung nach Kerzenbeginn: H1 endet mit der Kerze 24.05., 12:00–16:00 UTC; H2 beginnt 16:00 UTC. Kein Auswertungsbalken kommt in beiden Hälften vor. H2 nutzt ältere Daten nur als Indikator-Vorlauf, beginnt aber mit frischem Kapital und leerer Position. Diese Neustarts unterscheiden sich bewusst vom kontinuierlichen Gesamtpfad.

## Bestehende Tests und Sabotagen

Die ursprüngliche Suite hat **607 bestandene Tests, null Fehler**. Konfiguration und site/data lagen vollständig neben engine. Der unveränderte Test-Workflow war auch auf den Audit-Commits f9d2e31 (Lauf 36326950218) und e7e92d3 (36339867356) erfolgreich.

Alle 14 vorhandenen Sabotageskripte wurden berücksichtigt. Zwölf scheiterten zunächst an der unter Windows fehlenden SIGALRM-Funktion. Das ist eine Umgebungsgrenze, kein gefangener Strategiefehler. Die Originalprotokolle bleiben unter `sabotage/` erhalten. Anschließend liefen die Eingriffe in isolierten Kopien; nur die äußere SIGALRM-Hülle wurde für Windows ersetzt, der Subprozess behielt seine Zeitbegrenzung. E44.3 wurde nach einer Laufunterbrechung separat vollständig beendet.

| Gruppe | Erkannte Eingriffe | Nicht passende alte Vorlagen | Überlebende erreichte Eingriffe |
|---|---:|---:|---:|
| Elf portable ältere Skripte | 243 | 6 | 0 |
| Ursprüngliche E44.3-Fälle, separater Abschluss | 41 | 1 | 0 |
| E44.4 und E44.5, originale Runner | 25 | 0 | 0 |
| Summe ursprünglich vorgesehener Fälle | **309** | **7** | **0** |
| Sieben auf heutigen Code angepasste Vorlagen, separat | **6** | **0** | **1** |

Die letzte Mutation verschiebt die E41-Wartemeldung hinter die Handelssignale derselben Kerze. Die alte Suite bleibt dabei grün. Der zusätzliche Auditfall weist zuerst nach, dass Warte- und Verkaufszweig gleichzeitig erreicht werden; er erkennt anschließend die vertauschte Reihenfolge. Der tatsächliche Produktionscode besteht diesen Zusatzfall. Der nicht-null Exitcode von `mutation_finish.py` dokumentiert die überlebende Mutation absichtlich.

Zusätzliche unabhängige Kontrollen: vorzeitig bestätigter Pivot wird erkannt; ausgelassene Gebühr im Handrechenbeispiel wird erkannt; Stop-Rückfall, falscher Einstand, verlorenes Persistenzfeld, falsche Aggregation und fehlgeschlagene Zustellung werden durch erreichte Gegenbeispiele belegt. Ein Audit-Gegenbeispiel ist ausdrücklich kein Nachweis, dass genau dieser Fehler schon in einer realen Nachricht oder einem Brokerkonto auftrat.

## Lokal wiederholen

Aus dem Wurzelordner dieses Audit-Arbeitsbaums, mit Python 3 und UTF-8. Für reine Zahlenrechnungen genügt die Standardbibliothek. Die Diagrammausgabe von e42_report.py verwendet ReportLab und pypdfium2. Die JavaScript-Gegenprobe benötigt Node. Keine folgenden Befehle senden Telegram oder rufen Marktdaten ab:

```powershell
$env:PYTHONUTF8 = "1"
python engine/run_tests.py
python audit/reproduce.py
python audit/probes.py
python audit/additional_probes.py
python audit/parity.py
python audit/e42_trace_check.py
python audit/e42_cases.py
python audit/e42_portfolio_deltas.py
python audit/measure.py
python audit/summarize.py
python audit/uncertainty.py
python audit/capital.py
python audit/telegram_order.py
node audit/chart_probe.cjs
python audit/repro_report.py
```

`measure.py` überspringt bereits vorhandene Vxxx-Dateien. Für eine vollständige unabhängige Wiederholung eine separate Kopie des Arbeitsbaums verwenden und dort den Ergebnisordner vor dem Start an einen Archivnamen verschieben; die gelieferten Originalergebnisse nicht überschreiben. Der Eingabehash wird vor dem Lauf geprüft. `grid_plan.py` nicht nach Ergebniskenntnis ändern.

Die langen Sabotageläufe sind separat mit `run_portable_sabotage.py` und `mutation_finish.py` dokumentiert. Sie bearbeiten temporäre Kopien. Die ursprünglichen Sabotageskripte nicht in einer gleichzeitig bearbeiteten Produktionskopie starten. `github_read.py` ist eine gesonderte authentifizierte Leseabfrage und wird für die Offline-Reproduktion nicht gebraucht.

## Grenzen älterer Reproduktionen

Git liefert 80 verschiedene historische Berichtstände und 38 Revisionen der Live-Konfiguration. Die Tabellen und Beleg-Commits wurden vollständig extrahiert. Ein Commit des Berichts ist nicht automatisch der Commit, den der damalige Runner vor seinem Datenabruf ausgecheckt hatte.

Unter den bei der GitHub-Abfrage noch gelisteten 14 Artefakten waren zwölf Pages-Artefakte und die beiden E44.5-Pakete. Für frühere Renditeläufe wurde kein vollständiges damaliges Eingabepaket gefunden. Das aktuelle Archiv enthält nur einen Teil der benötigten Daten und bewahrt keine vollständige Abruf-/Revisionsgeschichte. Diese älteren Zahlen sind **rekonstruiert, nicht unabhängig reproduziert**. Die 79 neuen Zeilen beantworten stattdessen die getrennte Frage nach denselben Einstellungen auf gemeinsamer Basis.
