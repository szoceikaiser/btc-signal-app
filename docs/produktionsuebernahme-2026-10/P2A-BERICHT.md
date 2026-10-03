# P2a – Vertragsabschluss, keine Betriebsbereitstellung

03.10.2026. Ausgangspunkt P1 `7df2e20e8b68c1c7db8a5b4715fd6c1253e9165b`.
Ergebnis: konkreter Betriebs- und Migrationsvertrag mit Dateiplan, Gegenfällen,
Abnahmekriterien und Rückfallgrenzen für P2b. Kein neuer allgemeiner Auditlauf.

- `P2A-BETRIEBSVERTRAG.md`: vorhandene Infrastruktur, dauerhafte Schreibgrenzen,
  Sperren, Neustart, Quittungsklärung, Überwachung, Backup und D1–D3.
- `P2A-MIGRATIONSVERTRAG.md`: frische konsistente Quelle, B/W-Schnittgrenze,
  Verlustfreiheit, unbekannte Historie, Configwechsel und Ausgabeschema.
- `P2A-GITHUB-ADAPTER.md`: separat entworfene Alternative ohne eigenen Host,
  bedingtes Update vor Versand und nicht automatisch ablaufende Ownersperre.
- `P2B-IMPLEMENTIERUNGSPLAN.md`: begrenzte M/S/O/C-Pakete, bedingt H oder G,
  konkrete Dateien und Negativfälle; keine Aktivierung in P2b.
- `START-P2B.md`: vollständiger gespeicherter Folgeprompt einschließlich
  Modell-/Budget- und vererbter Ausgabe-/Speicherpflicht.

Ein geeigneter Dauerläufer ist weiterhin nicht benannt. GitHub-hosted Runner sind
vorhanden; cron-job.org ist dokumentiert, aber nicht live kontrolliert. Öffentliche
GitHub-Metadaten bestätigen ein öffentliches Code-Repository. Deshalb ist ein
privater Versandstore samt Berechtigung eine gesonderte Nutzerentscheidung.
Es wurde keine unbeantwortete Frage als Zustimmung gewertet. Ohne D1 kann der
gemeinsame Offline-Kern implementiert werden; die reale Anbindung bleibt offen.

Die Prüfung betraf nur den vorhandenen Store und seine konkreten Integrationsstellen:
main.py kann bei gesperrtem Versand bislang weiterrechnen, alte Config als Fallback
verwenden und die Historie auf 500 Einträge kürzen. Außerdem können Plan/Vorschau
ohne neue Kerze entstehen. Diese Punkte sind als gezielte P2b-Vertragsfälle erfasst;
P2a ändert dafür noch keinen produktiven Code. Keine neuen Strategiebefunde oder
Renditeberechnungen daraus abgeleitet.

Engine, Konfiguration, Chart, Laufzeitdaten, Renditedateien und bisherige Nachweise
bleiben unverändert. Einzige Workflowänderung: `Produktionsuebernahme Offline`
vergleicht Renditebelege mit P1 statt den Aufstellungsgenerator erneut aufzurufen.
Die vorhandene P1-Prüfung ist für diesen unveränderten Code weiterhin passend.
P2b muss bei beabsichtigten Engineänderungen einen eigenständigen Nachweis ergänzen.

Lokale P1-Integrationsprüfung besteht; vollständige Engine-Regression:
**796 bestanden, 0 fehlgeschlagen** mit explizitem UTF-8. Der erste Versuch hatte
15 UnicodeEncodeError bei der Windows-Logausgabe; beide Logs bleiben erhalten,
keine Engineänderung dafür. Finale CI-/Restoreergebnisse werden mit ihrem
tatsächlichen Abschluss in der externen additiven Sicherung festgehalten,
nicht hier vorweggenommen. Vor Push wurden alle
Kandidaten- und aktuellen main-Workflows einschließlich `workflow_run` gelesen.
Der main-Pages-Listener abonniert nur Signal-Engine/Backtest, nicht die beiden
zulässigen P2a-CI-Namen. Alle Einzeltexte/Hashes stehen in `P2A-WORKFLOWPRUEFUNG.json`.

Abschluss-SHA, CI-Links und Restoreprüfung:
`C:/Users/oeztu/BTC-Trading/audit-backups/produktion-p2a-20261003/UEBERGABE.md`.
Die Sicherung wird additiv erstellt. Kein main-Merge, Pages-Aufruf, Deployment,
Telegram/Broker, Secretabruf, Live-Umschalten oder Daten-/Backtest-Dispatch.

Modellvorgabe P2a: `gpt-6-astra` / `high`; keine parallelen Agenten. Die angebotenen
Werkzeuge erlaubten keine Umstellung oder verlässliche Abfrage des laufenden
Chatmodells. Es wird keine technisch erfolgte Umstellung behauptet. Im nächsten
Chat `gpt-6-sol` / `high` tatsächlich wählen; keine zusätzliche P2b-Sitzung wurde
automatisch gestartet. Die begrenzte Umsetzung nach festem Vertrag begründet
die budgetbewusste Staffelung, ohne Tarif-/Tokenversprechen. OpenAI dokumentiert
die Einstellungen in der [App-Einstellungsreferenz](https://learn.chatgpt.com/docs/reference/settings).
