# Nächster eigener Auftrag: Etappe 5b (F17)

Empfehlung GPT-6 Sol, Aufwand mittel; bei mehrdeutigen Herkunftskollisionen hoch.
Exakten Abschlusscommit von 5a aus dem Abschlusschat oder lokaler ABSCHLUSS.json
übernehmen. Keine automatische Modellumstellung und kein automatischer Start.

```text
Bearbeite ausschließlich Etappe 5b (Audit F17) am Repository
szoceikaiser/btc-signal-app: Chart-Zusammenführung mit eindeutigen Signal-IDs
und Herkunft. Deutsch, kurze Zwischenmeldungen. Arbeite bis zum geprüften
GitHub- und Bundle-/ZIP-Abschluss samt Wiederherstellung; danach 5b beenden.

Basis: exakt gesicherter Etappe-5a-Abschluss auf codex/etappe-5a-telegram-outbox,
Arbeitsbaum C:\Users\oeztu\BTC-Trading\etappe-5a-work. Exakte SHA zuerst aus
audit-backups/5a-abschluss-<Kurz-SHA>/ABSCHLUSS.json oder Abschlusschat übernehmen,
nicht den neuesten HEAD/main. Privates BTC-Trading-Backup-Repo nicht committen.
Remotes/Zweige/Arbeitsbäume und bestehende Änderungen prüfen; eigenen Zweig und
Arbeitsbaum direkt vom exakten 5a-Abschluss erstellen. Keine neueren
main-/E44.4-/E44.5-Commits übernehmen.

Pflichtlektüre: wissens-layer/00_STAND.md, jüngster Abschnitt von
wissens-layer/02_status/UEBERGABE.md, docs/nacharbeit-2026-09-28/ETAPPEN.md,
F01-F12-VERTRAG.md, F03-F04-F05-F10-VERTRAG.md, F13-VERTRAG.md,
ETAPPE-4-ABSCHLUSS.md und ETAPPE-5A-ABSCHLUSS.md sowie lokale ABSCHLUSS.json.
Im unabhängigen Audit audit-work, codex/audit-2026-09-27,
ccf2b01c0578346f325261e72445b7375a9ac706 gezielt F17 samt zugehöriger
Chart-Gegenprobe lesen. Kein Gesamtaudit.

Vor Umsetzung Vertrag für Signalidentität, Herkunft, Kollisionen, Sortierung
und Altbestandsmigration festlegen. Live-Signalreferenz, simulierte V1-Fills
und historische Signalband-Diagnostik unterscheidbar halten. Keine Quelle
bei gleichem Zeitstempel/Typ blind zugunsten des Backtests verdrängen.
Historische IDs nicht als nachgewiesene Telegram-/Broker-Zustellung ausgeben.
F13-Nachrichten-ID ist lokale Versandidentität, kein Telegram-Idempotenzschlüssel.
Versandliste nicht zurücksetzen oder bestätigte/unklare Nachrichten erneut senden.

712 bestehende Tests erhalten oder jede notwendige Änderung einzeln begründen.
F09/D01, Next-Open-V1, Exitpriorität, Cash/BTC/Reservierungen, echte Fill-
Rückkopplung, 0,1-%-Gebühr, Slippage 0/0,1/0,5 %, Schluss-DD und obere
Intrabar-Grenze, Restlose/Kosten, monotone Long-Stops, Positionsschema 2,
V1-Checkpointschema 1 und Versandvertrag aus 5a erhalten. Keine neue
Strategieauswahl, DD-Schwelle, Live-Konfiguration oder historische Neuberechnung.

F17 netzfrei reproduzieren; betroffene Produktionszweige vor Sabotagen erreichen.
Prüfe gleichzeitige und widersprüchliche Signale, identische Typen bei verschiedener
Herkunft, mehrere Signale derselben Kerze, stabile IDs bei Neustart/Reload sowie
historische Datensätze. Keine echten Telegram-/Broker-Aufrufe, Orders,
Deployments, Live-Schalter, Backtest-Workflow-Dispatches oder main-Push/Merges.

Vertrag, Umsetzung, Gegenproben und Grenzen dokumentieren; Kurzstand, Etappen,
Übergabe aktualisieren. Workflow-Auslöser vor Push prüfen; automatische Unit-Tests
auf eigenem Zweig erlaubt. Eigenen GitHub-Zweig, Remote-HEAD und CI zur exakten
Abschluss-SHA prüfen; danach Bundle, ZIP und vollständige Wiederherstellung.
Sicherungstag sicherung/vor-audit-korrekturen-2026-09-28 auf
469be65f65327a3b6abf2794ceba09c1fe0de9e2, Originale und private Volltranskripte
unverändert lassen; keine privaten Volltranskripte hochladen.

5a-Betriebsgrenzen bleiben sichtbar: unklare Zustellung blockiert die Reihenfolge,
keine Exactly-once-Garantie; Verlust eines ephemeren GitHub-Runners vor dessen
Git-Persistenz ist nicht behoben. Diese Grenzen nicht im Chartauftrag nebenbei
zu einem Live-Go erklären. V2/Shorts/E41.6/weitere Befunde getrennt halten.

Liefere Bericht, Tests/Gegenproben, Grenzen, Zweig/Commit, Sicherungspfad und
direkt kopierbaren Startprompt mit Modell-/Aufwandsempfehlung für den danach
getrennten Auftrag. Keine Folgeetappe automatisch starten.
```
