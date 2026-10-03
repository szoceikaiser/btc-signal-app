# START P2b – begrenzte Offline-Umsetzung nach P2a

Modell: `gpt-6-sol`; Denkaufwand: `high`. Im neuen Chat tatsächlich auswählen;
eine Promptzeile allein stellt das Modell nicht um. Budgetbegründung: P2a hat
die offenen Betriebs- und Migrationsfragen in einen konkreten Vertrag überführt;
jetzt ist begrenzte Umsetzung mit gezielten Gegenfällen gefragt. Kein pauschales
max/ultra, keine parallelen Agenten. Keine neue allgemeine Auditrunde.

Arbeitsbaum: `C:/Users/oeztu/BTC-Trading/produktion-work`
Zweig: `codex/produktion-audit-uebernahme`
P1: `7df2e20e8b68c1c7db8a5b4715fd6c1253e9165b`
Auditbasis: `881e36a6271a6e49400d47da59342755e33cf402`
P1-Produktionssnapshot: `ca8ad2fb730174ca1887791d425ae01aa6a715e6`.
main läuft unabhängig weiter. Dieser Snapshot ist keine frische Live-Migration.
Die exakte P2a-Abschluss-SHA, CI und Restorebelege stehen in der folgenden Übergabe;
HEAD vor Beginn dagegen prüfen und fremde Änderungen nicht überschreiben.

Lies zuerst nur:
1. `C:/Users/oeztu/BTC-Trading/audit-backups/produktion-p2a-20261003/UEBERGABE.md`
2. Im Arbeitsbaum `docs/produktionsuebernahme-2026-10/P2A-BETRIEBSVERTRAG.md`,
   `P2A-MIGRATIONSVERTRAG.md` und `P2B-IMPLEMENTIERUNGSPLAN.md`.
3. `P2A-GITHUB-ADAPTER.md` nur bei Auswahl des separaten Pakets G.
Weitere Dateien gezielt nach dem Dateiplan; alte Audits nicht vollständig neu lesen.

Auftrag: ausschließlich P2b offline umsetzen und belegen. Zuerst M/S/O/C aus dem
Plan: Migration, vorhandener SQLite-Teststore, gemeinsamer gesperrter Runner,
Überwachung, konsistente Sicherung/Restore, positive beleggestützte Zustellklärung
und sicherer öffentlicher Projektionsexport. P2a hat keinen Host bereitgestellt.
D1 (vorhandener Dauerläufer oder GitHub-Alternative) und D3 (Verantwortlicher,
unabhängiger Alarmweg, zweites Sicherungsziel) konkret klären; unabhängige Arbeit
fortsetzen. Ohne Antwort keine Infrastruktur-/Kostenentscheidung unterstellen.
Nur nach D1 genau H oder G zusätzlich umsetzen. G ist neuer separat zu prüfender
Adapter; das bestehende Repo ist öffentlich, private Versandjournale gehören dort
nicht hinein. Ohne D1 am Ende gemeinsame Offline-Umsetzung und offene Anbindung
klar unterscheiden, nicht den gesamten Betriebsweg als fertig erklären.

Verbindliche Grenzen:
- Dauerhaftes Intent und sending vor Transport, Quittung danach; ein Store für
  sämtliche Versandpfade, keine lokale/Git-Rückfallquelle und keine automatische
  Provisionierung. Kein automatischer Reset von uncertain, keine Exactly-once-Zusage.
  Unklarheit blockiert auch neue Operation-IDs und produktiven Entscheidungsfortschritt.
- T1 und Signalhistorie verlustfrei übernehmen, Historie auch beim Weiterlauf nicht
  abschneiden; keine historischen Nachrichten nachsenden. B/W-Schnittgrenzen und
  initiale Plan-/Vorschau-/Watch-Unterdrückung aus dem Vertrag umsetzen. P1-main
  ohne Versandjournal muss bei direkter Store-Provisionierung weiter scheitern.
- Keine alten Quittungen, Stopmaxima oder Börsenfills erfinden. Unbekannte Werte
  erhalten; D2 gehört zum späteren konkreten frischen Snapshot, nicht pauschal heute.
  Lücken/unklare letzte Alt-Läufe blockieren aktivierbare Migration.
- `muster_cvd: alt → usd`, alte eingebettete Config archivieren, neue effektive
  Config pinnen; bei fehlender/defekter Config kein Altwerte-/Default-Fallback.
  E42 und Shorts bleiben aus, keine Parameteroptimierung.
- P1-Nachweis bleibt eingefroren. Nach Engineänderungen P1-Codegleichheit nicht
  unverändert als HEAD-Abnahme ausgeben; eigenen P2-Nachweis verwenden.

Kein main-Merge, Deployment, Pages-Aufruf, Telegram, Broker, Secretabruf,
Live-Umschalten, laufende Sammlung oder alter Backtest-Dispatch. Keine realen
Store-API-Schreibvorgänge, neuen Repositories/Tokens oder Dienste einrichten.
Kein kostenpflichtiger Dienst ohne ausdrückliche Entscheidung. Alle Transporte
in Tests synthetisch und netzfrei. Aktive Produktionsworkflows nicht umstellen;
zukünftige Anbindung nur deaktiviert unter `ops/produktion/` vorbereiten.
Alte Arbeitsbäume, Rohdaten, Sicherungen und private Drittmaterialien unverändert.

Vor Push sämtliche Workflowtrigger einschließlich workflow_run und aktuelle
Default-Workflows prüfen; nur sichere branchgebundene Offline-CI und Tests.
Eigener Etappencommit, passende vollständige Engine-Regression und gezielte neue
Gegenfälle, grüne CI exakt zur Abschluss-SHA, additive Sicherung mit Hashmanifest
und verifiziertem frischem Restore. Keine Live-Freigabe. Nachweise zu fehlendem
realem Host/API-/Alarmbetrieb ehrlich offen lassen und an P3 übergeben.

RENDITEN.md samt CSV/JSON ist vorhanden: nicht erneut rechnen. Unbekannte
Halbzeiten bleiben unbekannt. Nur bei neuer belegter Änderung betroffene Nachweise
erneuern. P2a hat diese Dateien ausschließlich auf Unverändertheit geprüft.

Pflicht für diesen und jeden Folgechat: Jeden Start- oder Fortsetzungsprompt
vollständig und kopierfertig direkt in der abschließenden Chatantwort in einem
Codeblock ausgeben UND zusätzlich als Markdown-Datei speichern. Ein Link oder
eine Zusammenfassung genügt nicht. Jeder Prompt nennt konkrete Modell-ID und
Denkaufwand, begründet die budgetbewusste Wahl und gibt diese gesamte Ausgabe-
und Speicherpflicht ausdrücklich an alle weiteren Chats weiter. Voraussichtlicher
nächster Schritt P3: `gpt-6-sol` / `high` für den begrenzten Freigabekandidaten;
nicht automatisch starten. Nach endgültigem Abschluss ist kein Folgeprompt nötig.
