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

## Bestätigungsdesign und offene Entscheidungen

Konkreter prüfbarer [Entwurf](6-BESTAETIGUNGSDESIGN.md) und
[maschinenlesbares Entwurfsregister](6-design-register.json). Einziger Kandidat
E42/12 gegen dieselbe Basis; vorgeschlagenes unabhängiges künftiges Jahresfenster
01.10.2026–01.10.2027 UTC. Primär 0,1 % Slippage, relativer Mindestvorsprung von
2 % Jahres-Endvermögen samt einseitiger 95-%-Untergrenze. Gepaarter stationärer
14-Tage-Blockbootstrap mit festen 7-/28-Tage-Sensitivitäten, Familie m=1, keine
Szenario-/Fenster-/Kennzahlenwahl. Neue vorgeschlagene Risiken: 15 % Schluss-DD,
20 % obere Intrabar-Grenze, jeweils höchstens +2 Prozentpunkte gegenüber Basis
in allen fünf Kosten-/Latenzfällen. Keine Übertragung der alten DD-Schwellen.

**D6-A/B/C sind zur fachlichen Entscheidung vorgelegt und bis zur ausdrücklichen
Antwort offen.** Status/Antworten werden im Entwurfsregister erfasst. Kein
Schweigen als Zustimmung. Das Design dokumentiert unbekannte Power, Abhängigkeits-
und Regimeannahmen, Unsicherheits-/Ungültigkeitsausgänge und Umgang mit Vorwissen.
Ein Jahr garantiert keine Signifikanz. Keine neuen Kandidatenfälle gemessen.

Technische Voraussetzungen bleiben offen: Quellen-/Vintage-Manifest mit belegter
erster Verfügbarkeit, vollständiger Warmup, separat geprüfte Open-i+2-Umsetzung,
Statistikcode mit synthetischen Prüfungen und unveränderlicher Registrierungscommit
vor dem Fenster. Späte Daten machen Null-Latenz zum idealisierten Benchmark,
nicht zu einem zeitlich erreichbaren Fill. Fehlt rechtzeitige Registrierung,
kein heimliches Verschieben oder nachträgliches historisches Bestätigungsfenster.
Diese Etappe baut keine Datensammlung oder Latenzimplementierung.

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
fachliche Festlegung/technische Registrierungsfähigkeit. Keine automatische
Folgeetappe und keine Bestätigungsmessung im Anschluss an diesen Auftrag.
