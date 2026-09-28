# Abdeckungsmatrix – Abschluss 28.09.2026

Diese Matrix wurde vor der Prüfung angelegt (f9d2e31). Hier wird der tatsächliche
Abschlussstand ausgewiesen. „Geprüft“ bezeichnet die genannte Prüffrage und ihre
vorhandenen Belege; es bedeutet keine umfassende Fehlerfreiheits- oder Renditezusage.
Nicht verfügbare historische Daten bleiben ausdrücklich offen.

| Auftragsbereich | Tatsächlicher Prüfweg / Ergebnis | Abschluss und Grenze |
|---|---|---|
| Git-Wurzel, Remotes, main und Arbeitszweige | Private Backup-Wurzel getrennt; Signal-Remote, Commit-Graph, GitHub-Rechte und eigener Audit-Worktree geprüft | Erledigt; Produktionsdateien unverändert |
| GitHub-Schreibzugriff | Authentifizierte Rechteabfrage, trockener Push, tatsächliche Zwischenstands-Pushes auf Audit-Zweig | Nachgewiesen; kein main-Push |
| Nachgelagerte Pages-/Deployment-Auslöser | Alle neun Workflow-Dateien geprüft; unbeschränkter workflow_run von Backtest/Signal-Engine erkannt | Kein solcher Workflow gestartet; nur sichere Branch-Tests |
| Erste Orientierung | 00_STAND und jüngste UEBERGABE zuerst, danach Pläne, Chronik, frühere Prüfberichte, Code und Tests | Erledigt; keine frühere Beschränkung auf Übergabedateien übernommen |
| Entscheidungen und Schalter | Chronik E1–E44.6, 45 aktuelle Engine-Parameter, weitere Daten-/Anzeige-/Kapitalschalter, feste Konstanten, 85 alte Gitterzeilen | ENTSCHEIDUNGEN/PARAMETER; damalige und heutige Basis getrennt |
| Historische Belege | 80 unterschiedliche Berichtstände und 38 Konfigurationsrevisionen aus Git; verfügbare Actions-Artefakte untersucht | Tabellen rekonstruiert; ältere Renditen ohne Originalinputs nicht als reproduziert bezeichnet |
| Haupttranskript | ORderFLow-Transkript.md vollständig lokal gelesen | Fundstellen mit Zeitmarken; Datum unbekannt gekennzeichnet |
| Alle weiteren Video-Unterordner | Sechs Transkripte insgesamt gefunden: Hauptquelle sowie 060727, 260802, 260803, 260910, 260913; alle vollständig gelesen | Quellenmatrix; kein Volltranskript veröffentlicht |
| Quelle → Regel → Code → Test → Signal | Allgemeine Regel, Situation, Rückschau und Entwicklerinterpretation getrennt; August-Originalbild mit 2h-Chart visuell geprüft | FURKAN-QUELLEN; September-Zahlenabweichung bleibt ohne Originalbilder ungeklärt |
| Pivot/Zukunftswissen | Präfixlauf und gezielte frühere Pivot-Bestätigung als Mutation | Bestätigung korrekt im geprüften Code; frühzeitige Mutation erkannt |
| Höhere Zeitebene und ATR | Aggregation des laufenden Tages und unabhängige True-Range-Rechnung | F08/F16; keine Behauptung eines zukünftigen finalen Tagesschlusses |
| Zeitstempel/Lücken/unfertige Kerzen | Alle 2.481 eingefrorenen Kerzen und Flow-Punkte geprüft | D01; genau eine laufende Kerze getrennt entfernt |
| CVD/OI/Funding/Liquidationen | Abruf-/Zuordnungscode, Einheiten, Summenstart, Ersatzdaten, Nullwerte, Aggregation und Archiv geprüft | F06/F07/F14/F15/D02; historische Veröffentlichungsstände fehlen |
| Ausführungspreise | OHLC-Erreichbarkeit aller Originalzeilen, vier feste Ausführungs-/Kostenszenarien im gemeinsamen Gitter | F12; kein Tick-Fill-Nachweis, keine vollständige Rückkopplung verspäteter Fills in die Engine |
| Reihenfolge Kauf/Verkauf/Stop | Bestehende Tests und Sabotagen, no_flip/E41/E42-Fälle, unabhängige Intrabar-Risikorechnung | Grenzen von 4h-OHLC benannt; kein scheinbar exakter Intrabar-Pfad |
| Cash/Bestand/Wiederanlage/Gebühren | Unabhängiges Losbuch, Handrechnung, Gebühren-Sabotage, Abgleich aller 78 Long-Zeilen des Hauptgitters plus sieben weiterer Strukturkonfigurationen | F01/F04/F09; Short-Zeile wegen F02 nicht als gültige unverschuldete Alternative bewertet |
| Kapitalbindung/Drawdown | Durchschnittliche Exposition, Schluss-DD, kausale OHLC-Risikospanne; ergänzend vorgeplante Quoten 100/60/50 % | KOMBINATIONEN/KAPITAL; keine Gleichsetzung von Schluss- und Intraday-Risiko |
| Backtest ↔ Live-Engine | Defaultvergleich gegen eingefrorenes main, Neustart je Kerze, rollierende 1.300 Kerzen, 90-Tage-CVD | Auf fixen Daten gleiche Signale; tatsächliche frühere API-Ausfälle/Revisionen nicht reproduzierbar |
| state ↔ Telegram ↔ Chart | Persistenz-Rundlauf, Plan-Stop, fehlgeschlagene Zustellung ohne Netz, tatsächliches Chart-Merge-JavaScript, gespeicherte Signalkollisionen | F05/F10/F13/F17; keine echte Nachricht gesendet, Zustellhistorie und tatsächliches Konto fehlen |
| Bestehende Suite | Zu Beginn und am Abschluss in vollständiger Repo-Struktur ausgeführt | 607 bestanden, null fehlgeschlagen; Tests sind keine Renditevalidierung |
| Sabotageprüfungen | 14 vorhandene Skripte; Windows-Hülle isoliert angepasst; fehlende Vorlagen separat erneuert | 309 erkannte alte Eingriffe, 7 nicht passende Vorlagen; erneuert 6 erkannt/1 Testlücke; Zusatzfall erkennt diese Lücke |
| Kritische unabhängige Orakel | Einstand, ATR, Drawdown, Margin, Losbuch und Gebühren nicht mit derselben Produktionshilfsfunktion bewertet | Erreichte Gegenfälle und Zahlen in JSON/Skripten |
| E44.5-Reproduktion | Originalcode und Originalinputs, alle vier Ausgabedateien verglichen | Inhaltlich exakt, zwei Dateien nur CRLF/LF-Unterschied |
| E42-Ereignisse | 57 Beobachtungen, 33 Ausbruchsereignisse, davon eins in derselben Kerze ersetzt; 16 Käufe, alle Abgänge | Laufzeitkontrolle verschachtelter Zustandswechsel; Korrektur einer Audit-Endzeit offen protokolliert |
| E42-Portfolio | Alle Rückkauf-Lose, voller Pfad mit/ohne E42, Cash-/Größen- und Signalunterschiede | Direkter Losgewinn und restliche Pfaddifferenz getrennt; keine erfundene kausale Einzelzuordnung |
| Neue Kombinationen | Vorher festgelegte fünf 2×2×2-Gitter plus aktive Ausschalt-/inaktive Einzel-/abhängige Proben; 79 Hauptzeilen und separat vorgeplantes frühes E4-4×2-Gitter, insgesamt 86 eindeutige Handelskonfigurationen | Alle Zeilen veröffentlicht, auch negative/neutrale; nicht getestete Kombinationen genannt |
| Mehrfachtests/Zeitabhängigkeit | Zwei frische Kapitalhälften, feste Monatsabschnitte, Monatskonzentration, gepaarte 7-/28-Tage-Blöcke | Wiederverwendete Entwicklungsdaten; kein unabhängiger OOS-Nachweis, kein exakter nachträglicher Suchkorrektur-p-Wert |
| Walk-forward | Feste Parameter, fortlaufender Zustand, spätere Monatsabschnitte Mai–September | Rückblickende Konsistenzprüfung; unabhängige prospektive Abschnitte erst zukünftig möglich |
| Bitcoin-Forschung | Elf Gruppen von Forschungs-Primärquellen plus offizielle Anbieterdokumentation; Zeitebene/Datenverfügbarkeit/Projektbezug | FORSCHUNG; keine Marketingbehauptung als Wirkungsnachweis; ein Artikel nur Zusammenfassung/Einleitung verfügbar |
| Maßnahmen, Datenlücken, Abschluss | Prioritäten mit konkreten Abnahmekriterien; Herkunft, Skripte, Hashes und Lauf-IDs gesichert | BERICHT, DATEN, REPRODUKTION; keine Live-Änderung und kein Merge-Go |

Nicht Bestandteil eines behaupteten Erfolgs: historische Brokerprüfung ohne
Abrechnungen, echte Telegram-Zustellung ohne Sendeversuch, frühere API-Versionen
ohne Archiv oder eine noch nicht vorhandene unabhängige Zukunftsstichprobe.
