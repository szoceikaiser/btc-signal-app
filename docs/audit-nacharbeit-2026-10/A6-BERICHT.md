# A6 – Schutzproben und Regressionen

02.10.2026. Basis `772221ecda67dad50f6190d8e1319476eb7129e3`, Zweig
`codex/a1-audit-nacharbeit`, Arbeitsbaum
`C:/Users/oeztu/BTC-Trading/a1-work`. Ausschließlich T01 und Regressionen für
A1–A5. Keine Produktionsstrategie, Datensammlung oder historische Renditerechnung
geändert. Originaltests, Fixtures und Originalaudit sind erhalten.

## Befund, Auswirkung und Abhilfe

| Priorität / ID | Datei und Zeile | Auswirkung und Abhilfe | Beleg |
|---|---|---|---|
| P2 T01 | `tools/a6_inventory.py:8`, `tools/a6_mutations.py:93` | Alle 316 Originalmutationen aus zwölf `SABOTAGEN`- und zwei `FAELLE`-Programmen übernommen und namentlich zugeordnet. Der neue Runner führt jeden Fall in einer Wegwerfkopie aus. Vor jedem Eingriff besteht derselbe unmutierte Zieltest; ein fehlender Texttreffer oder nicht ausführbarer Fall wird nicht als Treffer gewertet. | `A6-mapping.json`, `A6-mutations.json`, `A6-summary.json` |
| P2 T01 | `tools/a6_finalize_evidence.py:1` | Jede erreichte Mutation ist getrennt von ersetzten und historischen Vorlagen bilanziert. 13 absichtlich beschädigte Zweige erzeugen den erwarteten Laufzeit-/Testfehler nach grüner Gegenprobe; Traceback, Fehlertyp und Originalergebnis sind einzeln gespeichert. Kein Import-, Syntax- oder Timeoutfehler wird akzeptiert. | `A6-mutations.json`, `A6-summary.json` |
| P1 T01 / E41 | `engine/test_a6_regression.py:70`, `engine/main.py:1069` | Eine Kerze erzeugt zugleich E41-Wartemeldung und `TEILVERKAUF_LADDER`. Die vorgemerkte Wartemeldung muss vor dem Signal derselben Kerze stehen. Die umgestellte Reihenfolge wird erkannt. Die alte Suite hatte genau diese Mutation überleben lassen. | `contract:T01-E41-order`; unmutierte Probe und Mutation in `A6-mutations.json` |
| P2 T01 | `tools/a6_contract_cases.py:53`, `:81` | Sieben im Originalaudit nicht passende Vorlagen haben aktuelle Gegenstücke. Weitere durch A2/A4 verschobene Stellen erhalten aktuelle Mutationen; die Originaltexte werden nicht still als Treffer ausgegeben. | Sieben 7/7 erkannt; 23 weitere aktuelle Entsprechungen (22 Assertions, ein beabsichtigter `StopIteration`) |
| P2 A1–A5 | `tools/a6_contract_cases.py:3`, `engine/test_a6_regression.py:15` | F11/F16, F06/F07/D02, F08/F14/F15, F13 und F02/F12 wurden an die jetzigen Verträge gebunden. Zwölf Vertragsmutationen haben je eine grüne unmutierte Gegenprobe und eine Assertion im beschädigten Fall. | `contract:F11` bis `contract:F12-spot-gate` in `A6-mutations.json` |
| P2 T01 | `engine/test_a6_regression.py:25`, `:49`, `:58` | Erreichte Gegenfälle ergänzen nachgezogenen Stop ohne E41-Schonfrist, fehlendes BTC-OI ohne Division und vom CVD-Startstand unabhängige USD-Fensterdeltas. Die CVD-Erwartung `110 USD`/`22.000 USD` ist ausgeschrieben und verwendet keine Produktionsfunktion zur Ermittlung der Sollzahl. | `sabotage_e41:011`, `sabotage_e434:003`, `current:sabotage_e433:009` |

## Vollständige Bilanz der ursprünglichen Liste

Das Originalaudit (`audit-work/docs/audit-2026-09-27/REPRODUKTION.md:77–93`)
berichtete 309 gefangene Eingriffe und sieben veraltete Vorlagen. Es blieb
zusätzlich eine erreichte E41-Reihenfolgemutation mit 607 grünen Tests. A6 nimmt
die ursprünglichen 316 Vorlagen als Inventar; die neue Bilanz betrifft den
zusammengeführten A5-Ausgangsstand mit A6-Schutzproben:

| Kategorie | Zahl | Bewertung |
|---|---:|---|
| Originaltext trifft aktuellen Code; Assertion im Zieltest | 243 | Aktueller Fehlerzweig erreicht und erkannt. |
| Originaltext trifft; absichtlich beschädigter Zweig wirft erwarteten Fehler | 13 | Erreicht und erkannt; Typ/Traceback einzeln geprüft. Nicht als Assertion gezählt. |
| Originaltext veraltet; aktuelle Entsprechung trifft und wird erkannt | 30 | Neue Mutation separat belegt. Darunter alle sieben ursprünglich veralteten Vorlagen. |
| Durch A2-Default `usd` fachlich abgelöst | 2 | Alte Mutation wäre jetzt die ausdrücklich gewählte Vorgabe; kein aktueller Treffer behauptet. |
| Durch A2-As-of-Datenvertrag abgelöst | 3 | Alte Vorwärts-/Rückwärtsfüllstelle existiert nicht mehr; F07-Präfixmutation und jetzige OI-Tests decken den Ersatzvertrag ab. Kein alter Treffer behauptet. |
| E44.4/E44.5 nur am ursprünglichen Auditstand | 25 | Zielcode/Test fehlt bereits an der A5-Basis. Originalprogramme bleiben über Auditcommit und Sicherungen ausführbar. Kein aktueller Treffer behauptet. |
| **Vollständig zugeordnet** | **316** | `A6-mapping.json` enthält genau eine Zeile je Original-ID; keine unzugeordnete Zeile. |

Die **42 neuen** Mutationen sind separat gezählt: 41 Assertionstreffer und ein
erreichter, beabsichtigter Testfehler (`StopIteration` bei weggelassener
E42-Meldung). Die sieben alten Fehlvorlagen sind explizit zugeordnet:
E41-Nachkauf, fehlende Wartemeldung, Wartemeldung nach Signal, E43.3-CVD-Key,
E43.4-OI-Default und -Key sowie E44.3-Altbestand. Die alte E41-Reihenfolge wird
nicht durch bloßes Weglassen der Wartemeldung geprüft, sondern durch Umstellen der
beiden vorhandenen Nachrichtenblöcke. Alle sieben aktuellen Gegenstücke treffen.

Die maschinenlesbare [Zuordnung](A6-mapping.json) nennt für jede Original-ID
Vorlage, Test, Trefferzahl, aktuelle Zeile und, wo erforderlich, die neue
Entsprechung oder den Grund für die fachliche Ablösung. Rohresultate mit
Gegenproben und Tracebacks liegen in [A6-mutations.json](A6-mutations.json).
Die früheren fehlgeschlagenen Zuordnungsversuche bleiben in der additiven
A6-Sicherung erhalten; sie sind nicht Teil der Erfolgsbilanz.

## Gesamtregression und Erhalt

- Nach sämtlichen Testergänzungen: **789 Tests bestanden, 0 fehlgeschlagen**,
  darin fünf neue A6-Funktionen; Protokoll `A6-tests-local.log`. Sechs synthetische
  Statistikprüfungen bestanden (`A6-stats.log`). Die A5-Fraction-Kontrollrechnung,
  A4-Dauerablage-Simulation sowie A1–A3-Gegenfälle liefen in der Gesamtregression
  erneut; ihre unabhängigen Sollrechnungen wurden nicht durch Produktionshelfer
  ersetzt.
- Es wurden keine alten Tests oder Fixtures gelöscht und keine früheren
  numerischen Erwartungen entfernt. Die 25 E44.4/E44.5-Fälle fehlten schon an
  der vorgegebenen A5-Basis und sind über das ursprüngliche Audit reproduzierbar.
- Alle 22 Register-IDs fortgeführt. Nur T01 erhält in A6 einen neuen Status;
  F02/F12-Grenzen aus A5, A3-Datengrenzen und A4-Betriebsgrenzen bleiben bestehen.
- Vor Push wurden alle acht lokalen und alle acht Workflows des aktuell abgerufenen
  Default-Zweigs `55e4d7d598704c23f1aa3184b56b4805dbbaa8eb` samt
  `workflow_run` gelesen. Auf dem Audit-Zweig startet allein `tests.yml` bei
  Push; Pages hört auf Signal-Engine/Backtest, nicht auf Tests.
  Auslöser und Hashes: `A6-prepush-workflows.json`.
- Kein historischer Gesamtlauf, keine neue Short-/Orderstrategie, keine
  Parameterwahl nach Rendite. V035 bleibt historisch nicht auswertbar. Die
  E41-Wartekerze prüft Nachrichtenreihenfolge im simulierten Versand, keine reale
  Zustellung und kein Exactly-once.

## Abschlussbelege

Der Abschlusscommit, die Tests-CI zu genau dieser SHA, das Bundle, Hashmanifest
und die geprüfte Wiederherstellung stehen in `UEBERGABE.md`/`UEBERGABE.json` der
additiven A6-Sicherung. Dieser Bericht nimmt deren Ergebnis nicht vorweg.
Keine Aktivierung, kein main-Merge, Deployment, Pages, echter Telegram-/Brokeraufruf,
Secretabruf oder laufende Datensammlung.
