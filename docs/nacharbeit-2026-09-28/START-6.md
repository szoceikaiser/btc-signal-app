# Nächster getrennter Auftrag: Etappe 6

Empfehlung: GPT-6 Sol / mittel für begrenzte Reproduktionsläufe;
GPT-6 Astra / hoch für statistisches Bestätigungsdesign. Nicht automatisch starten.
Exakte 5b-SHA zuerst aus lokaler ABSCHLUSS.json übernehmen, nicht neuesten HEAD/main.

```text
Bearbeite ausschließlich Etappe 6 am Repository szoceikaiser/btc-signal-app.
Deutsch, kurze Zwischenmeldungen. Lies zuerst wissens-layer/00_STAND.md, jüngste
Übergabe, docs/nacharbeit-2026-09-28/ETAPPEN.md, F01-F12-VERTRAG.md,
F03-F04-F05-F10-VERTRAG.md, F13-VERTRAG.md, F17-VERTRAG.md und die Abschlussberichte
4/5a/5b. Prüfe lokale audit-backups/5b-abschluss-<Kurz-SHA>/ABSCHLUSS.json und
verwende ausschließlich deren exakten gesicherten 5b-Abschlusscommit als Basis.
Prüfe Remotes/Zweige/Arbeitsbäume/Änderungen; eigener Zweig und Arbeitsbaum direkt
von dieser SHA. Privates Backup-Repo nicht committen; Originale/Transkripte und
Sicherungstag sicherung/vor-audit-korrekturen-2026-09-28 unverändert lassen.
Keine neueren main-/E44.4-/E44.5-Commits übernehmen.

Zuerst ausschließlich die bereits eingefrorenen zwei Zeilen (Live-Basis und
E42/12) × Slippage 0/0,1/0,5 %, Gebühr 0,1 %, dieselben Inputs und derselbe
Stichtag erneut reproduzieren, gegen gesicherte V1-Ledgers und unabhängige
Kosten-/Bestandsrechnung prüfen. Keine neue Strategieauswahl oder neues Gitter.
Alle 728 Tests erhalten; F09/D01, Next-Open, Exitpriorität, Reservierungen,
Fill-Rückkopplung, Restlose/Kosten, monotone Long-Stops, Positionsschema 2,
Checkpoint 1, Versandvertrag und F17-Herkunftsprojektion erhalten.

Danach ein vorab festgelegtes statistisches Bestätigungsdesign für wenige
Kandidaten als prüfbares Dokument erarbeiten: Auswahl und Hypothesen,
unabhängiges Bestätigungsfenster, Mehrfachprüfung, Mindestunterschied und
Unsicherheitsbewertung, Schluss-DD und obere Intrabar-Grenze, Datenverfügbarkeit,
Kosten-/Latenz-Szenarien sowie Umgang mit nachträglichem Wissen ausdrücklich
festlegen. Alte DD-Schwellen nicht automatisch übertragen. Noch keine neuen
Kandidaten messen und keine Live-Konfiguration ändern. Erforderliche fachliche
Entscheidungen anhand des konkreten Entwurfs klären; daraus kein Live-Go ableiten.

Keine Telegram-/Broker-Aufrufe, Orders, Deployments, Live-Schalter, Backtest-
Workflow-Dispatches oder main-Push/Merges. Historische Signalbänder sind
Diagnostik, V1-Fills simuliert, Live-Bestand ohne Beleg unbekannt. F13-ID ist
lokale Versandidentität, kein Telegram-Idempotenzschlüssel. Versandliste nicht
zurücksetzen oder bestätigte/unklare Nachrichten erneut senden. Unklare
Zustellung blockiert; keine Exactly-once-Garantie; ephemerer Runnerverlust vor
Git-Persistenz bleibt separat offen. V2/Shorts/E41.6/weitere Befunde getrennt.

Dokumentiere Reproduktion, Bestätigungsdesign, offene Entscheidungen und Grenzen;
aktualisiere Kurzstand/Übergabe/Etappen. Prüfe Workflow-Auslöser vor Push; nur
automatische Unit-Tests auf eigenem Zweig erlaubt. Abschluss mit geprüftem
GitHub-Remote-HEAD/CI zur exakten SHA, Bundle/ZIP und vollständigem Restore.
Liefere Bericht, Tests, Zweig/Commit, Sicherungspfad und Startprompt für den
danach getrennten Auftrag. Keine Folgeetappe automatisch starten.
```
