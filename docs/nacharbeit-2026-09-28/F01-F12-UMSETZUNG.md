# Etappe 3b: kausale Ausführung und Risikobuch V1

28.09.2026. Basis ausschließlich `67c8e624de3cc1b854a78dced755a5702b1a9c9a`
(3a, enthält F09/D01). Zweig `codex/etappe-3b-f01-f12`, Arbeitsbaum
`C:/Users/oeztu/BTC-Trading/etappe-3b-work`. Ausschließlich F01/F12 nach dem
[bestätigten Vertrag](F01-F12-VERTRAG.md); kein main-/Live-Go.

## Umsetzung und Zugang

Der neue korrigierte Offline-Pfad ist `backtest.run_execution(...)` beziehungsweise
`execution_v1.run_v1(...)`. Eingaben: Kerzen, gepaarter Flow, bestehende Konfiguration,
expliziter Handelsbeginn und **historischer eingefrorener Messstichtag**. Rückgabe:
Kandidaten, Ereignis-Ledger, echte Bestände, Rückkopplung, Monatsstände und getrennte
Risikofelder. `run_execution_half` startet mit Warmup, frischer Kasse und ohne
übernommene Absichten. Kein API-Abruf und keine Dateiausgabe aus diesen Funktionen.

`strategy_core._evaluate` besitzt interne Gates vor vollständigen Handelsblöcken.
Ein Beobachtungslauf schreibt nur zeitliche Informationen fort; getrennte Kauf- und
Verkaufsproben sehen denselben gebuchten Vorzustand und dasselbe abgeschlossene
Präfix. Virtuelle **gleichseitige** Stufenfolge erhält die vorhandenen GP/FULL- und
TP1/TP2-Kandidaten. Ein Kauf verändert die Verkaufsprobe nicht. Das bisherige
`no_flip` darf Konfliktkandidaten nicht vor der bestätigten D2-Priorisierung verstecken.
Explizite Sequenznummern folgen der bisherigen Erzeugungsreihenfolge (Action-Tabelle).

Scheduling: Hauptstop/anderer Gesamtausstieg vor E42-Teilstop vor Teilverkäufen.
Ein ausführbarer Verkauf entfernt sämtliche Käufe desselben Pakets. Kaufbudgets
reservieren Cash, Verkäufe BTC; eine Reservierung ist weder Ausgabe noch Vermögen.
Keine negative Kasse, Überverkäufe oder nicht finanzierte Phantompositionen.
Zyklusbudget = Cash am echten Zyklusbeginn × deploy; vorhandene Tranchen und
TP1/TP2 je 40 % des BTC-Höchstbestands bleiben bestehen. Ein E42-Teilstop verkauft
nur dessen tatsächliche Einheiten; gewöhnliche Teilverkäufe nehmen sie anteilig mit.

Alle handelbaren Absichten füllen ausschließlich am direkt folgenden zulässigen
4h-Open, mit 0,1 % Gebühr je Fill und separaten Slippage-Läufen 0/0,1/0,5 % je Seite.
Signalpreis ist Referenz, niemals Fill. Ein neues Extension-Ziel derselben Kerze
darf einen Schluss-Kandidaten liefern, aber keinen rückwirkenden Level-Fill.
Fehlendes Folge-Open ergibt `unfilled_end_of_data`; kein letzter-Close-Ersatz.
Fehlende, doppelte, ungeordnete 4h-Kerzen oder falsch gepaarter Flow lehnen den Lauf
ab. Eine nach D01 ausgeschlossene laufende Kerze liefert auch keinen Open-Fill.

Nach den Open-Fills bestätigt eine erneute Auswertung **desselben bekannten Präfixes**
nur tatsächlich gefüllte Handelsblöcke, bevor die nächste Entscheidung entsteht.
Teilfinanzierung meldet tatsächliche Tranche plus abgelehntes Restbudget zurück.
Verworfene Käufe/Verkäufe und Datenende verbrauchen keine Leiterstufe. Vollausstiege
bestätigen den zurückgesetzten Verkaufszustand; rechnerisch vollständige Teilverkäufe
setzen wegen F09 ebenfalls auf FLAT. Der neue Zyklus verwendet wieder neue Kasse und
neuen BTC-Höchstbestand. Der finanzierte Tranche-Anteil wird bei Verkäufen anhand der
wirklich verbleibenden BTC fortgeführt; eine erste 25-%-Tranche bedeutet nicht 100 %
investiert, nur weil sie der bisherige BTC-Höchstbestand ist.

Ledger-Felder: Ereignis-/Order-ID, Kerzen-ID, Wissensannahme, Entscheidungs-/Orderzeit,
geplanter und tatsächlicher Fillzeitpunkt, Referenzpreis, Fillpreis, Bewertungs-Open,
Status/Grund, Gebühren, Menge und Cash/BTC/Reservierungen/Marktwert/Equity vor/nach.
Kosten werden zum **unveränderten Open** bewertet. Ohne Kosten erhält Umbuchung Equity.

## Risiko und Etappe-4-Abgrenzung

Am Open wird zuerst der Altbestand einschließlich Kurslücke bewertet, danach vor/nach
jedem Fill. Der danach gebuchte Bestand gilt konstant bis Close. Schluss-Absichten
ändern ihn noch nicht. Monatsende zählt den letzten alten Monats-Close vor dem
Fill am Open des neuen Monats (UTC).

Neue Felder, positive Verlustprozente: `dd_close_pct`, `dd_intrabar_lower_pct`,
**`dd_intrabar_upper_pct`**. Close-DD enthält Start und abgeschlossene Closes.
Intrabar-Grenzen führen Peaks und Rückgänge durchgehend fort, mit Open/Ereignissen,
Low→High→Close beziehungsweise High→Low→Close. Die obere Grenze ist Risikovorsicht,
kein beobachteter Verlust oder Garantie. Bei den sechs historischen Läufen fallen
untere/obere Grenze zufällig zusammen; H03/H15 unterscheiden sie ausdrücklich.
Die alte negative `max_drawdown_pct` wird nicht umgedeutet; alte Schwellen gelten
nicht automatisch für die neuen Felder.

F04-Einstandsformel bleibt bewusst tranchengewichteter **Referenzpreis**. 3b skaliert
nur die Gewichtung einer tatsächlich teilfinanzierten Tranche. Kein neuer gebühren-
oder BTC-gewichteter Einstand, keine neue Stop-Nachzug-Regel, keine Persistenzkorrektur.
Gebuchtes Cash/BTC und Risikowert stammen unabhängig davon aus dem Ledger. Daher können
F03/F04 weiterhin die Strategieentscheidungen beeinflussen. Keine untrennbare
Etappe-4-Abhängigkeit wurde zur Buchführung benötigt; Etappe 4 bleibt offen.

Die öffentliche Live-Observer-Schnittstelle `evaluate` ist erhalten. Die bisherigen
`run_backtest`, `simulate`, `run_half` und der gewöhnliche Backtest-Berichtspfad bleiben
**ausdrücklich historische Diagnostik ohne Fill-Rückkopplung**, zur Reproduktion und
Regression. Sie sind kein V1-Abschlussbeleg. Die falsche Erläuterung „Wert/Untergrenze
der Vorab-Order“ wurde entfernt. Bestehende Webseiten-/Workflow-Ausgaben werden nicht
still durch neue Kennzahlen ersetzt. Spätere Messungen müssen den neuen Zugang nutzen;
gewöhnlicher GitHub-Backtest, Gitter und neue Schwellen sind hier nicht freigegeben.

## Prüfungen

- **638/638 Unit-Tests**: sämtliche 600 bisherigen Assertions erhalten; 38 neue.
  Zwei bestehende Quelltextprüfungen zeigen jetzt auf den ausgelagerten `_evaluate`-
  Funktionskörper. Assertions unverändert; keine fachliche Erwartung abgeschwächt.
- **16 Handfälle** unabhängig geprüft: zwölf V1-Fälle mit Produktionsassertions und
  festen Handwerten, H06/H07/H12 als ausdrücklich ausgeschlossene V2-Arithmetik,
  H14 als ausgeschlossene E41.6-Kohortenrechnung. Diese vier Fälle behaupten keine
  implementierte V2-/E41.6-Funktion. [Handfallprotokoll](3b-handfaelle.json).
- **19/19 Sabotagen**: vor jeder Mutation besteht derselbe erreichte Test. Falscher
  Signalpreis, Gebühren, Cash/Reservierung, Exitpriorität, Kauf trotz Verkauf,
  falsche Teilstop-Menge, Datenlücke, laufendes Folge-Open, Datenende-Fill,
  Risikobestand/-Peak/-Reihenfolge, fehlende Rückkopplung, Phantom-Bestätigung und
  fehlende Teilfinanzierungsablehnung werden erkannt. [Protokoll](3b-sabotage.json).
  Ein bloß entfernter Abwärtslücken-Check war redundant, weil der Verkauf den Verlust
  noch in Cash festhält. Die endgültige Probe verwendet deshalb eine **aufwärts**
  springende Eröffnung vor Verkaufskosten: 20.000 Peak, 19.980 Cash, 0,1 % Intrabar-DD.
- Echte Engine-Kandidaten erreicht: neues Ziel170 (H08), Kaufleiter + GP/FULL + TP1
  im selben Wissenspaket, Rest-Gesamtausstieg nach virtuell erreichtem TP1,
  Haupt-/E42-Teilstop, E42-Kauf mit/ohne Kapital. Rejektion/Datenende erhält Merker;
  Teilfüllung bestätigt tatsächliche Tranche. Präfixprobe hat echte Fills und verändert
  spätere OHLC/Flow drastisch; frühere Entscheidungen/Fills bleiben gleich.
- D01 **6/6** und F09 **3/3** bestehende Sabotagen erneut erkannt, einschließlich echter
  winziger Bestände. [D01](3b-d01-sabotage.log), [F09](3b-f09-sabotage.log).
- Unabhängiges Audit-Losbuch unverändert geladen: jeder historische Fill mit Zeitpunkt,
  Typ, Menge, Preis, Gebühr, Cash davor/danach geprüft; jede Close-Zeile Cash/BTC/Equity,
  Monatsstände, Gesamtkosten, Los-PnL-Summe und alle drei DD-Felder abgeglichen.
  Diese Losrechnung bestätigt Buchführung, nicht die Güte der Signalstrategie.

## Vorab begrenzte lokale Messung

Genau zwei schon vorhandene Zeilen: Live-Basis und E42 mit zwölf Kerzen, ohne
Verkaufsfaktor/Rest-halten-Zusatz. Pro Zeile drei separate kausale Kostenläufe.
Vergleich gegen exakten 3a-Code auf denselben D01-gefilterten Eingaben. Kein neues
Strategie-/Kombinationsgitter, keine Auswahl nach Rendite, keine Hälftenoptimierung.
2.481 Originalkerzen → 2.480 abgeschlossene, davon 1.509 im Handelsbereich.
Stichtag `1790497748840`. Eingaben-SHA256:
`ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a`.
Originalsignale, Originalergebnisse und unabhängiges Buch ebenfalls vorher/nachher
gehasht, unverändert. Herkunft und vollständige Ledger/Lose: [3b-ergebnis.json](3b-ergebnis.json).

| Zeile | Slippage je Seite | Endwert USD | Differenz zu 3a USD | Close-DD % | **obere Intrabar-Grenze %** |
|---|---:|---:|---:|---:|---:|
| Live-Basis | 0 % | 13.431,45 | −181,64 | 7,9166 | **9,9428** |
| Live-Basis | 0,1 % | 12.865,30 | −747,79 | 8,4989 | **9,9428** |
| Live-Basis | 0,5 % | 10.830,63 | −2.782,46 | 12,0273 | **12,6288** |
| E42 | 0 % | 13.250,88 | −290,68 | 8,4177 | **9,9428** |
| E42 | 0,1 % | 12.625,64 | −915,92 | 9,0636 | **10,2437** |
| E42 | 0,5 % | 10.407,42 | −3.134,14 | 13,6739 | **14,2642** |

Alte 3a-Endwerte 13.613,09/13.541,56 USD stammen aus dem rückwirkenden Level-Modell
und sind hier keine erreichbare Gegenleistung. Alle sechs neuen Kandidatenbänder
unterscheiden sich vom alten Band. Live-Basis hat 171 echte Fills, E42 200, je Szenario.
Es gibt sowohl prioritätsbedingte Ablehnungen als auch Restbudget-Ablehnungen nach
Teilfinanzierung. Der Erfolg ist der unabhängige Buchabgleich, keine Mindestrendite.

## Wiederholung und Sicherung

```text
python engine/run_tests.py
python tools/verify_3b_handcases.py
python engine/sabotage_3b.py
python engine/sabotage_d01.py
python engine/sabotage_f09.py
python tools/verify_3b.py --audit-root ../audit-work
python tools/verify_3b_scope.py
```

Windows: UTF-8-Ausgabe aktivieren (`PYTHONUTF8=1`). Messergebnisse ausschließlich
`docs/nacharbeit-2026-09-28/3b-*`; frühere Artefakte bleiben erhalten. Workflows
vor Push geprüft: nur `Tests` reagiert auf diesen Zweig. `Pages` reagiert auf main/site
oder Signal-Engine/Backtest, nicht Tests. Kein Dispatch und kein PR-/main-Merge.

Exakte Abschluss-SHA, Remote-HEAD/Tests-CI, unverändertes Tagobjekt/Ziel und
Wiederherstellungsnachweis stehen lokal in
`C:/Users/oeztu/BTC-Trading/audit-backups/3b-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.
Dort vollständiges Abschlussbundle, ZIP, Hashmanifest, CI-Beleg und geprüfter frischer
Clone. Das Bundle enthält nur den eigenen Zweig samt 3a-Vorfahren und bestehenden
Sicherungstag, keine neueren main-/E44.4-/E44.5-Commits.

## Grenzen und nächste getrennte Etappe

Idealisiertes Null-Latenz-Folge-Open, kein belegter Telegram-/Broker-Fill. 4h-OHLC
belegt weder Intrabar-Reihenfolge, Liquidität, Queueposition, Spreads noch tatsächliche
Teilausführungen. Historische Flow-Verfügbarkeit/Revisionen und andere Auditfehler
bleiben offen. Long/Spot ohne Hebel; V2, Shorts/Margin/Funding und E41.6 nicht umgesetzt.
F03/F04/Persistenz bleiben offen; neue DD-Schwellen vor späteren Strategieentscheidungen.
Keine Originaldaten, privaten Volltranskripte, Live-Schalter, site-Dateien, Workflows,
Telegram-Nachrichten, Orders, Deployments oder Sicherungstags verändert.

Etappe 3b nach Sicherungsabnahme beenden. Nächster getrennter Auftrag: **Etappe 4,
GPT-6 Astra / hoch** für Einstands-/Stop-/Persistenzentwurf und kritische Prüfung;
danach Sol / hoch bei klar abgegrenzter Umsetzung. Aufgabenbezogene Empfehlung wegen
Zustandskompatibilität und Risikoabhängigkeiten, keine automatische Modellumstellung.
OpenAI Docs bestätigt Astra für komplexes Reasoning/Coding und `high`:
[offizielle Modellseite](https://developers.openai.com/api/docs/models/gpt-6-astra),
28.09.2026 abgerufen. Kein automatischer Start von Etappe 4.
