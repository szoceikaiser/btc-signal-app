# Etappe 6: eingefrorene Reproduktion und Bestätigungsdesign

29.09.2026. Ausschließlich Etappe 6; Basis aus der lokalen
`audit-backups/5b-abschluss-bb86220/ABSCHLUSS.json` exakt
`bb862204c97c6bb4c0da49cb6f1de90dd58af663`.
Eigener Zweig `codex/etappe-6-reproduktion-design`, Arbeitsbaum
`C:/Users/oeztu/BTC-Trading/etappe-6-work`, direkt aus dieser SHA.
Die exakte Abschluss-SHA/Remote-CI-/Restore-Abnahme steht lokal in
`audit-backups/6-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.

## Reproduktion: vollständig identisch

Vor den Läufen wurden 5b-ABSCHLUSS.json, exakte SHA und bisherige CI-/Restore-
Belege, Bundle-/ZIP-SHA256, sämtliche **215 Git-Dateiblobs**, manifestierte
Änderungsdateien und alle vier eingefrorenen externen Dateien geprüft.
Remotes/Zweige/Arbeitsbäume geprüft. Fremde ungetrackte E44-Protokolle sowie
private Änderungen/Transkripte erhalten; privates Backup-Repo nicht committet.

Nur die beiden vorhandenen Zeilen × Slippage 0/0,1/0,5 %, Gebühr jeweils 0,1 %,
10.000 USD Startkapital, dieselben Inputs und derselbe Stichtag:
`start=1768766400000`, `cutoff=1790497748840` (UTC-Millisekunden).
D01 lässt 2.480 von 2.481 Inputkerzen zu; je Fall 1.509 Handels-Closes.
Input-SHA256: `ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a`.
Keine neue Zeile, keine Schwellenwahl und kein neues Gitter.

| Zeile | Slippage je Seite | Endwert USD | Schluss-DD % | obere Intrabar-Grenze % | Fills |
|---|---:|---:|---:|---:|---:|
| Live-Basis | 0 % | 13.418,88 | 7,9166 | 9,9428 | 171 |
| Live-Basis | 0,1 % | 12.852,01 | 8,4989 | 9,9428 | 171 |
| Live-Basis | 0,5 % | 10.815,30 | 12,0534 | 12,6548 | 171 |
| E42 / 12 | 0 % | 13.299,89 | 8,4177 | 9,9428 | 196 |
| E42 / 12 | 0,1 % | 12.677,52 | 9,0636 | 10,2437 | 196 |
| E42 / 12 | 0,5 % | 10.467,26 | 13,1053 | 13,6995 | 196 |

Jeder vollständige neu gerechnete V1-Ergebnisbaum ist exakt gleich dem gesicherten
Etappe-4-Ledger, den 5a/5b erhalten haben. Alle sechs kanonischen SHA256 stimmen
auch mit den 5b-Prozessreplays überein. Differenz **0** in allen sechs Fällen.
Keine bloße Umbuchung alter Signalbänder: `backtest.run_execution` erzeugt pro
Szenario Entscheidungen, Reservierungen, Fills und Rückkopplung neu.

**1.101 Fills / 9.054 Closes** geprüft. Unverändertes unabhängiges Audit-Losbuch
prüft Mengen aus gewählten Kandidaten, Cash/BTC vor/nach Fills, Gebühren, Close-
Vermögen, Monatsstände und DD-Grenzen. Separat prüft eine Decimal-Rechnung mit
45 Stellen Restlose/Bruttokosten, abgegebene Kosten, Einstand und realisierten
Gewinn; keine Produktions-Kostenfunktion liefert deren Sollwerte. Vollständige
unabhängige Ergebnisse sind ebenfalls identisch. Grenzen der Unabhängigkeit:
das Audit-Buch übernimmt ausgewählte Kandidaten, die Kostenrechnung übernimmt
Bruttobudgets/ausgeführte Verkaufsmengen. Diese Prüfungen bestätigen weder die
Strategieauswahl noch die zeitliche Verfügbarkeit historischer Flow-Daten.

Belege: [6-ergebnis.json](6-ergebnis.json), [Messprotokoll](6-messung.log),
`6-ledger.json.gz` mit Ergebnissen/Parametern und unabhängigen Konten;
[Reproduktionsprüfer](../../tools/verify_6.py). Netzwerkverbindungen während der
Reproduktion aktiv blockiert; keine Nachrichten oder externen Orders.

## Erhaltene Verträge und Tests

**728/728 Tests**, 0 Fehler, alle 728 bisherigen unverändert, keine neuen Tests.
[Lokales Protokoll](6-tests.log). Engine, site einschließlich Daten/Chart,
Versandliste, Workflows, historische Dateien, alte Tests und F01/F12-, F03/F04/
F05/F10-, F13- und F17-Verträge identisch zur exakten 5b-Basis.
F09/D01, Next-Open, Exitpriorität, Reservierungen, Fill-Rückkopplung,
Restlose/Kosten, monotone Long-Stops, Positionsschema 2 und Checkpoint 1 erhalten.
[Scope-Prüfer](../../tools/verify_6_scope.py) prüft Arbeitsbaumblobs/Ancestry und
Workflow-Auslöser; nur automatische Unit-Tests reagieren auf diesen Zweig.
Pages bleibt main/site bzw. Signal-Engine/Backtest vorbehalten, nicht Tests.

## Retrospektives Prüfdesign, Version 2

Der Nutzer verlangt ausdrücklich eine Prüfung von der Vergangenheit bis zum
aktuellen Stichtag ohne Jahreswartezeit. Das vorgeschlagene Zukunftsfenster ist
aufgehoben. [Prüfdesign](6-BESTAETIGUNGSDESIGN.md) und
[Register](6-design-register.json) trennen historischen Modellbefund,
Stabilitätsprüfung, bedingte Unsicherheit und auswahlbereinigte Evidenz.
Die unbestätigten 2-%-Nutzenhürde und 15/20/+2-DD-Budgets sind zurückgezogen:
Effektgrößen und Risiken offen ausweisen, Dominanz oder Zielkonflikt nennen,
keine persönliche Nutzen-/Risikotoleranz als wissenschaftlichen Wert erfinden.

Bestehendes R0 bleibt bis 27.09.2026 08:29:08.840 UTC vollständig reproduziert.
R1 plant denselben Handelsstart/Warmup bis festem Stichtag
29.09.2026 12:00 UTC; neue historische Inputs bislang nicht beschafft und keine
neuen Kandidatenfälle gemessen. Paket/Code/Methoden vor der nächsten Auswertung
fixieren; keine rückwirkende Präregistrierung oder unabhängiges Fenster behaupten.
Kalendermonate und mechanische Drittel einschließlich aller schlechten Abschnitte,
Kosten-/Latenzszenarien und bedingte Bootstrap-Unsicherheit festgelegt.

Frühere E43/E44-/Audit-/Korrektur-Auswahl lesend inventarisieren. Reality-Check/
SPA und E42-spezifische simultane Aussagen benötigen eine vollständige relevante
Familie und geprüfte Implementierung. Diese Familie ist noch nicht nachgewiesen;
fehlende Auswahlbereinigung verhindert keine korrekte beschreibende Auswertung,
aber eine unqualifizierte Überlegenheitsbehauptung. Historische Vorkenntnis wird
auch bei sachlicher KI-Auswertung nicht als beseitigt dargestellt.

Schon bekannte R0-Zahlen: E42-Endwert minus Basis -118,99 / -174,48 / -348,03 USD
bei Slippage 0/0,1/0,5 %. Schluss-DD jeweils höher, obere Intrabar-Grenze gleich
oder höher. Historische Dominanz der Basis in diesen drei Kennzahlen, kein
Zukunftsbeweis und kein Ergebnis bis zum 29.09. Kein neues Ergebnis errechnet.

D6-A durch Nutzer auf retrospektives Design festgelegt; D6-B/C-Vorschläge
zurückgezogen. Keine erneute Freigabefrage zu diesen alten Vorschlägen.
Technisch offen: separates R1-Daten-/Quellen-/Vintage-Paket, Statistikcode samt
synthetischen Prüfungen, separate i+2-Umsetzung und Suchhistorieninventar.
Keine laufende Datensammlung, neue Marktabfrage oder neue Strategieauswahl.
Version 1 und Sicherung efc3b1a bleiben unverändert nachvollziehbar.

## Exakte Remote-/Sicherungsabnahme

Der [CI-Prüfer](../../tools/verify_6_ci.py) liest eigenen Remote-HEAD, automatische
Tests zur exakten SHA, main nur zur Beobachtung und unverändertes Sicherungstag-
objekt/-ziel. Kein Dispatch. Der [Restore-Prüfer](../../tools/verify_6_backup.py)
fordert erfolgreiche exakte CI als Vorbedingung für ABSCHLUSS.json und prüft:

- Bundle mit eigenem Zweig und Sicherungstag, ZIP und vollständige Baum-/Hashliste;
  frischer Bundle-Clone, `git fsck`, identischer vollständiger Git-Baum.
- 728 Restore-Tests; identische Schutzproben F17 16/16, F13 16/16,
  Etappe 4 23/23, Etappe 3b 19/19 sowie D01 6/6 und F09 3/3.
- Sechs komplette V1-Reproduktionen in der restaurierten Kopie mit identischem
  Ledger/Ergebnis und unabhängigen Konten; zusätzlich sechs identische
  Checkpoint-Fortsetzungen in neuen Python-Prozessen.
- Scope-/Entwurfsregisterprüfung und saubere Original-/Restore-Arbeitsbäume.

Die konkreten Resultate dieser Abschlussabnahme gehören in die lokale
ABSCHLUSS.json, nicht in eine selbstreferenzierende Commit-SHA im Bericht.
Originale und Sicherungstag bleiben unverändert: Tagobjekt
`7d78094c17624b90b8f7ebc387b96570ff2c8ef7`, Ziel
`469be65f65327a3b6abf2794ceba09c1fe0de9e2`.

## Grenzen und getrennter Folgeauftrag

Historische Signalbänder sind Diagnostik, V1-Fills simuliert, manueller Live-Bestand
ohne Ausführungsbeleg unbekannt. 4h-OHLC garantiert weder Liquidität noch Intrabar-
Reihenfolge; die obere DD-Grenze ist kein beobachteter Verlust und kein VaR.
F13-ID bleibt lokale Versandidentität, kein Telegram-Idempotenzschlüssel.
Unklare Zustellung blockiert, bestätigte/unklare Nachrichten werden nicht erneut
gesendet, Versandliste nicht zurückgesetzt. Keine Exactly-once-Garantie;
ephemerer Runnerverlust vor Git-Persistenz separat offen.

Keine Telegram-/Broker-Aufrufe, Orders, Deployments, Live-Schalter,
Backtest-Workflow-Dispatches, main-Push/Merges oder neueren main-/E44.4-/E44.5-
Commits übernommen. V2/Shorts/E41.6/weitere Befunde bleiben getrennt.
Kein Strategiegütebeweis und **kein Live-Go**.

Nächster ausschließlich getrennter Auftrag: [START-NACH-6.md](START-NACH-6.md),
rückblickende Umsetzung/Auswertung zum festen Stichtag. Keine automatische
Folgeetappe und keine Bestätigungsmessung im Anschluss an diesen Auftrag.
