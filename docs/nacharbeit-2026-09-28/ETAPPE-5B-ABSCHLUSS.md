# Etappe 5b: Chart-Zusammenführung / F17

29.09.2026. Basis exakt `6c0c6fdd56db9bb27febaf42c56f6e33bcab0685`,
eigener Zweig `codex/etappe-5b-chart-identitaet`, Arbeitsbaum
`C:/Users/oeztu/BTC-Trading/etappe-5b-work`. Exakte Abschluss-SHA und geprüfte
Remote-/CI-/Bundle-/ZIP-/Restore-Belege stehen nach Abnahme lokal in
`audit-backups/5b-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.

Der Chart erhält widersprüchliche und gleichzeitige Ereignisse aller Quellen,
anstatt über Zeitstempel + Typ den Backtest gewinnen zu lassen. Marker nennen
L (Live-Referenz), H (historisches Signalband) oder V1 (simulierter Fill).
Die aufklappbare Ereignisliste zeigt vollständige Gründe, Tranche/Menge, Zeit,
Referenz-/Fillpreis und Chartidentität. ID-Kollisionen werden sichtbar markiert.

## Vertrag und Umsetzung

Vor Umsetzung festgelegt: [F17-VERTRAG.md](F17-VERTRAG.md).
`site/chart_signals.js` liefert dieselbe reine Projektion an Marker und Liste;
`site/index.html` verwendet diese Projektion im tatsächlichen Ladepfad.
Quellen sind Dateikontexte, keine Behauptung aus einem unkontrollierten source-Feld.
Explizite IDs werden nur innerhalb derselben Quelle bei vollständig gleichem
Inhalt dedupliziert; widersprüchliche Inhalte bleiben erhalten. Altzeilen ohne
ID erhalten kanonische, verlustfreie Schlüssel mit Vorkommensnummer. Auch identische
Altduplikate bleiben erhalten, weil ihre reale Identität nicht rekonstruierbar ist.

Migration erfolgt ausschließlich im Browser-Speicher. Kein Schreiben nach
signals.json/state.json und kein Aufruf der Versandfunktion. Chartschlüssel sind
eigenständige Anzeigeidentitäten, keine Telegram-ID oder Brokerquittung. F13-ID
bleibt lokale Versandidentität, kein Telegram-Idempotenzschlüssel.
Chronologisch sortiert, dann feste Herkunftsfolge L/H/V1, Sequenz und kanonischer
Schlüssel. Gleiche Anzeige-Kerzen nach Snap behalten alle Marker.
Details werden als Textknoten gerendert, nicht als HTML aus Signalgründen.
Ungültige Zeilen/Quellen werden mit Datenhinweisen gezählt.

Die zwei bestehenden Dateien bleiben reine Referenzen/Diagnostik. Ein optionales
lokales `site/data/execution_v1.json` kann genau ein bereits ausdrücklich gewähltes
V1-Ergebnis enthalten (`model=V1_close_to_next_open_zero_latency`, `ledger`).
Nur `status=filled` wird mit `fill_at`/`fill_price` gezeigt; Ablehnungen werden
nicht als Fills dargestellt. Fehlende Datei (404) ist normal, andere Lade-/JSON-
oder Modellfehler erzeugen sichtbare Hinweise. Es wurde keine solche Datei erstellt,
kein Szenario automatisch ausgewählt und kein Workflow verändert.

## Gegenproben und Erhalt

- Lokale 5a-ABSCHLUSS.json: exakte Basis, CI-/Restore-Abnahme, Bundle-/ZIP-SHA256
  und alle dort manifestierten Git-Dateiinhalte geprüft. Git normalisiert CRLF;
  zusätzlich wurde der 5a-Arbeitsbaum gegen dessen gespeicherte Blobs geprüft.
- Original-F17 netzfrei auf der exakten 5a-HTML-Implementierung erreicht:
  105 Live wird durch 100 historisch verdrängt. Die zwei Audit-Snapshot-Konflikte
  aus unverändertem `ccf2b01` werden separat reproduziert. In den realen beiden
  Snapshot-Paaren unterscheiden sich Grund bzw. Tranche, nicht der Preis.
  [Ausgangsbeleg](5b-baseline-f17.json), [Prüfer](../../tools/verify_5b_baseline.py).
- **728/728 Tests**, **712 alte unverändert**, 16 neue JavaScript-/Integrationsfälle:
  gleicher Typ/gleiche Zeit aus mehreren Quellen; widersprüchliche Preise;
  mehrere gleiche Kerzensignale; explizite Duplikate/ID-Kollisionen; identische
  Altzeilen; JSON-Neustart und separater Node-Prozess; Umsortieren/Hinzufügen;
  Zeit-/Sequenzordnung; V1-Zeit/Preis; ungültige Daten; Marker-/Listenpfad und
  Textinjektion. Tatsächliche `load()`-Funktion aus HTML mit netzfreien Stubs
  erreicht und beide Preise/Quellen in Markern und Liste nachgewiesen.
  [Tests](5b-tests.log), [JS-Prüfer](../../tools/chart_5b_tests.cjs).
- **16/16 F17-Sabotagen**, jeweils erst nach grüner erreichter Produktionsvorprobe:
  Quellenverlust, verlorene Altduplikate, doppelte explizite IDs, verborgene Kollision,
  verlorener Inhalt/Quellen-ID, fehlende Ordnung, Zufalls-ID, V1-Referenzzeit/-preis,
  erfundene Ablehnungsfills, unbekanntes Modell, unsichtbare Markerherkunft,
  HTML-Injektion, ungültige Zeit und verlorene Sequenz. [Beleg](5b-sabotage.json).
- Vorhandene Schutzproben: **5a 16/16**, **4 23/23**, **3b 19/19**,
  **D01 6/6**, **F09 3/3**; getrennte `5b-*`-Belege im Berichtsordner.
- Sechs unveränderte gespeicherte V1-Ledgers: **1.101 Modell-Fills** mit exakt
  gespeicherter Fillzeit/-preis, Quelle und eindeutiger Identität projiziert.
  Keine historische Neuberechnung. [Beleg](5b-v1-projection.json).

Engine-Produktionscode, komplette Versandliste/-verträge, Positionsschema 2,
V1-Checkpointschema 1, historische Daten/Ergebnisse, Konfiguration, Strategie,
Workflows und sämtliche alten Tests identisch zur Basis. Next-Open, Exitpriorität,
Cash/BTC/Reservierungen, Fill-Rückkopplung, 0,1-%-Gebühr, Slippage 0/0,1/0,5 %,
Schluss-DD/obere Intrabar-Grenze, Restlose/Kosten und monotone Stops bleiben erhalten.
[Scope-Prüfer](../../tools/verify_5b_scope.py), [Scope-Beleg](5b-scope.json).

## Sicherung und Grenzen

Vor Push: nur Tests auf eigenem Zweig; Pages reagiert ausschließlich auf main/site
oder Signal-Engine/Backtest, nicht auf Tests. Kein Dispatch, keine Nachrichten,
Orders, Deployments, Live-Schalter oder main-Push/Merges. Kein neuer main-/E44.4-/
E44.5-Commit übernommen. Private Volltranskripte nicht hochgeladen, privates
Backup-Repo nicht committet, fremde Arbeitsbäume/Originale nicht verändert.
Sicherungstagobjekt `7d78094c17624b90b8f7ebc387b96570ff2c8ef7` bleibt auf
`469be65f65327a3b6abf2794ceba09c1fe0de9e2`.

Abschluss: exakter Remote-HEAD und erfolgreiche Tests-CI, Bundle/ZIP mit allen
Git-Dateien, frischer Clone, kompletter Baum-/Hashvergleich, 728 Restore-Tests,
alle Schutzproben, identische F17-Proben und 1.101 gespeicherte Fillprojektionen.
Zusätzlich dieselben sechs schon festgelegten V1-Prozessfortsetzungen mit
unabhängigem Kostenabgleich; keine neue Strategiemessung.
[CI-Prüfer](../../tools/verify_5b_ci.py), [Restore-Prüfer](../../tools/verify_5b_backup.py).

Grenzen: IDs aus Altbestand rekonstruieren keine tatsächliche Telegram-/Broker-
Zustellung. Für identische alte Kopien bleibt nur die Schlüsselmenge stabil;
eine Einzelzuordnung nach Löschen/Ändern identischer Kopien ist unbeweisbar.
Vollständige kanonische Schlüssel sind länger als Hashes, vermeiden aber
Hashkollisionen; die Liste zeigt sie auf Nachfrage. Originaldateien bleiben
unversioniert und unverändert; die Migration ist eine deterministische Projektion.
V1 ist ein idealisiertes Modell, Live-Signalreferenz kein manueller Fill.
Keine reale Browser-Sitzung/entfernte Seite oder visuelle Darstellung behauptet;
der HTML-Ladepfad wurde mit DOM-/Chart-Stubs getestet, nicht per Screenshot.
RAW lädt weiterhin bestehende main-Signaldateien; nur die explizite optionale
V1-Datei gehört zur jeweiligen Site-Kopie. Keine Bereitstellung dieser Änderung.

5a-Grenzen bleiben sichtbar: unklare Zustellung blockiert die Reihenfolge,
keine Exactly-once-Garantie; ephemerer Runnerverlust vor Git-Persistenz bleibt
offen. Kein Live-Go. V2, Shorts, E41.6 und weitere Befunde bleiben getrennt.

Danach 5b beenden. Nächster separater Auftrag: [START-6.md](START-6.md).
Empfehlung nach Aufgabenrisiko: **GPT-6 Sol / mittel** für begrenzte Wiederholung,
**GPT-6 Astra / hoch** für statistisches Bestätigungsdesign. Keine automatische
Modellumstellung und keine automatisch gestartete Folgeetappe.
