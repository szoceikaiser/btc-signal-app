# Etappe 4 – Einstand, Stop, Positionsplan und Persistenz

Beginn 28.09., Abschluss 29.09.2026. F03/F04/F05/F10, eigener Zweig `codex/etappe-4-bestand-stop`,
Arbeitsbaum `C:/Users/oeztu/BTC-Trading/etappe-4-work`. Basis exakt
`9606a6f555f9cdaee86f9c33a5175c5c5306b365`. Lokal geprüft; Remote-/Sicherungsabnahme zur exakten SHA in ABSCHLUSS.json.

Verbindliche Grundlage: [Korrekturvertrag](F03-F04-F05-F10-VERTRAG.md) und der
unveränderte [V1-Vertrag](F01-F12-VERTRAG.md). Keine neuen main-/E44.4-/E44.5-Commits.
Privates Backup-Repo nicht committet; fremde Änderungen erhalten. Originalaudit
`ccf2b01` nur gezielt gelesen, kein Gesamtaudit und kein neuer Strategievergleich.

## Umsetzung

`inventory.py` führt verbleibende BTC und Bruttokosten je tatsächlich simuliertem
Kauf-Fill, einschließlich Gebühren und Teilfinanzierung. Gewöhnliche Verkäufe
reduzieren alle Lose proportional; E42-Teilstop verkauft ausschließlich E42-Lose.
Verkaufskosten verändern den Erlös, nicht die Kosten des verbleibenden Bestands.
Ledger nennt abgegebene Kosten und realisierten Gewinn; jede Close-Zeile nennt
Restkosten und Gesamteinstand. Reservierte Mittel sind weiter keine Ausgaben.
F09-Restbereinigung und Wiederanlage bleiben erhalten, auch bei winzigen echten BTC.

`Decision.confirm` spiegelt die tatsächlichen Restlose in die Strategie zurück.
`entry_ref` ist in V1 jetzt **Kosten/BTC des verbleibenden Basisteils**, während
`cost_entry` den Gesamteinstand einschließlich E42 bezeichnet. Diese Trennung erhält
den bestätigten eigenen E42-Teilstop. E42-Käufe dürfen nicht still den Hauptstop der
Basisposition verändern. `entry_pct` bleibt ein historischer Tranchenmerker; es ist
kein realer BTC-Bestand, Marktanteil oder Nachweis manueller Käufe.

`resolve_stop` ist die gemeinsame Quelle für Engine und Plan. Der gespeicherte
Long-Stop samt Grund kann innerhalb einer offenen Position nur steigen. Kursbruch,
verschwundene Pivots, sinkender Einstand, Zonenwechsel und Neustart mit Rest löschen
ihn nicht. Neue Strukturkandidaten müssen bei Auswahl unter dem Close liegen;
bereits gültige Grenzen brauchen diese Bedingung nicht erneut. FLAT beendet sie.
E41-Rückeroberung bleibt nur am ursprünglichen Stop und verwendet ebenfalls die
gültige Grenze. Nachgezogene Stops erhalten keine neue Schonfrist.

Beim Übergang nach Teilverkauf wird der prospektive Stop bereits gespeichert:
im Signalmodell nach dessen Zustandsübergang, in V1 **erst nach bestätigtem Fill
und Kostenrückkopplung**, mit ausschließlich dem vorher bekannten Kerzenpräfix.
Ein abgelehnter/verfallener Teilverkauf aktiviert ihn nicht. Keine rückwirkende
Order oder Ausführung: ein späterer Schlussbruch liefert weiterhin einen
Kandidaten zum direkt folgenden zulässigen Open. Diese Korrekturen ändern
Strategiepfade; sie sind ausdrücklich kein bloßer Anzeige-Fix.

`position_state.py` ersetzt die zwei unvollständigen Feldlisten durch einen
gemeinsamen Codec, Positionsversion **2**. Alle entscheidungsrelevanten
Dataclass-Felder und vollständige Pivot-Daten werden gespeichert. Nur die
aktuellen `e42_meldungen` bleiben flüchtige Ausgabe. Insbesondere bleiben
`widerstand_exits`, gebrochene Prozentanteile, Stoppreis/-grund, E41/E42,
Herkunft und Lose erhalten. Unvollständige neue oder unbekannte künftige Versionen
werden abgewiesen; fehlende Versionsnummern in neuen Zuständen ebenfalls.

V1-Checkpointversion **1** umfasst zudem Kasse, Reservierungen, Lose, ausstehende
Absichten, vollständige bekannte Entscheidungsbasis, Parameter, Dedupe-Zeit,
Risikopeaks/Drawdowns und bisherige Ergebnisse. `backtest.run_execution` kann am
expliziten `checkpoint_at` (Kerzen-ID) einen solchen Zustand liefern;
`execution_v1.resume_v1` setzt ihn fort. Übergebener Präfix und gespeicherte
Konfiguration/Reservierungen werden abgeglichen. Das ist ein Offline-Checkpoint,
kein Broker-/Telegram-Wiederanlauf und kein Schema für alte Ergebnisaggregate.

## Signalreferenz und Altzustände

Live-Observer und historische Signalband-Diagnostik haben **keine belegten
manuellen Fills**. Ihr bisheriger tranchengewichteter Referenzanker bleibt als
Signalreferenz bestehen; er wird nicht durch erfundene BTC-Lose „repariert“ und
nicht als realer Kosteneinstand ausgewiesen. Die korrekte F04-Kostenrechnung gilt
für belegte Modell-Fills im V1-Pfad. Es gibt hier keinen Live-Bestandsimport.
Der Plan benennt Herkunft, Gesamtkosten versus Basis-Einstand und die Bedeutung
der Prozentzahl. Der Textformatter zeigt diese Unterscheidung; Versandfunktionen
und Versandzustände wurden nicht geändert. F13 bleibt Etappe 5a.

Unversionierte Zustände behalten Position, Signalanker, Dedupe, Zonen und bekannte
Merker. Fehlendes `widerstand_exits` erhält den bisherigen Default 0, nun mit
Migrationshinweis. Frühere Stopmaxima sind nicht rekonstruierbar; der Hinweis
erscheint im Plan. Keine laufende Position und keine historische Signalliste wird
zurückgesetzt. Die monotone Garantie beginnt beim ersten gespeicherten gültigen
Stop; sie behauptet keinen rückwirkenden Schutz für unbekannte Altgeschichte.

## Gegenfälle, Regression und Sabotagen

- Alle vier Auditfälle unabhängig auf unverändertem 3b-Code reproduziert:
  [Ausgangsbeleg](4-audit-gegenfaelle.json), [Skript](../../tools/verify_4_counterexamples.py).
- Tatsächlicher GP-Kaufzweig plus Fill-Rückkopplung: 25 zu 220, 50 zu 172,80 ergeben
  **186,10966057441252**, nicht 188,53333333333333. Bruttokosten und BTC unabhängig
  mit rationalen Zahlen geprüft; zusätzliche Gebühren-/Slippage-Fälle.
- Struktur 115 bei Close 120 bleibt beim folgenden Close 110 gültig, auch bei
  verschwundenem Pivot und JSON-Neustart. Der Stopkandidat entsteht; Plan 115.
- Widerstandsverkauf tatsächlich erreicht: Zähler 1 gespeichert, nächster Verkauf
  erhöht auf 2, danach kein dritter Verkauf – mit und ohne Neustart identisch.
- Teilfinanzierung, proportionale Verkäufe, gezielter E42-Losverkauf, unbekannte
  Anfangskosten, volle/tiny Verkäufe, FLAT/Wiederanlage und vollständiger Feldweg.
- Mehrkerzenpositionen mit wiederholtem JSON-Neustart; offene Kaufreservierung,
  Stop-Verkaufsreservierung, gemischter Bestand nach TP und vor E42-Stop;
  identische Kandidaten, Fills, Lose, Kasse, Zähler und Risikofelder.
- **676/676 Tests**: 638 bisherige Testfälle erhalten, 38 neue. [Protokoll](4-tests.log).
- **23/23 neue Sabotagen** nach jeweils grünem, erreichtem Ausgangsfall erkannt:
  [Protokoll](4-sabotage.json). Falsche Kosten/Gewichtung/Kohorte, gelöschte
  Stopmaxima, abweichender Plan, fehlende TP-Aktivierung, verlorene Zustandsfelder,
  abgeschnittene Bruchteile/Pivotindizes, verlorene Reservierung/Risikopeaks,
  Altpositionsreset und erfundene Live-Herkunft.
- Bestehende Schutzproben weiterhin **3b 19/19**, **D01 6/6**, **F09 3/3**:
  [3b](4-3b-sabotage.json), [D01](4-d01-sabotage.log), [F09](4-f09-sabotage.log).

Einzeln begründete Änderungen an alten Tests:

1. Zwei E42-Fixtures lieferten zuvor nur `rk_units=25` nach Konstruktion eines
   reinen Basisbuchs. Jetzt liefern sie ausdrücklich 75 Basis-/25 E42-BTC-Lose.
   Alle bisherigen Mengen-, Prioritäts- und Zustandsassertions unverändert.
2. `test_be_im_plus_zieht_den_stop_auf_den_einstand`: bestätigte Struktur 145 war
   bereits enger als Einstand 140. Statt des falschen Rückfalls wird nun Stop 145
   samt Strukturgrund erwartet; vorherige Aktivierung zusätzlich nachgewiesen.
3. `test_plan_nachgezogener_stop_bleibt_ohne_rueckeroberung`: Plan erwartet jetzt
   Struktur 120 statt Einstand 115. Die Assertion gegen eine E41-Schonfrist bleibt.
4. `test_e433_mehr_historie_aendert_muster2_nicht_bei_usd`: nur diese Testkonfiguration
   schaltet den Struktur-Nachzug aus, um Muster 2 zu isolieren. Muster-Gleichheit,
   nichtleere Pump-Warnungen, Altmodell-Gegenprobe und Signalvergleich bleiben.
   Gegenfall separat erhalten: bei Kerzen-ID 18403200000 ergibt dieselbe
   Leiterveräußerung nach 400/1200 geladenen Kerzen Stop 135679,204739/138026,388187
   bei identischem USD-Muster. Die zusätzliche Strukturhistorie ist eine reale
   Eingabedifferenz. Früher wurde ihr Stop bei Bruch wieder vergessen. Keine
   Produktionsänderung an Muster 2, high_exit oder Historienfenstern vorgenommen.

## Vorab begrenzte historische Ergebnisse

Genau zwei bereits in 3b vorhandene Zeilen, je drei getrennte Slippage-Szenarien,
0,1 % Gebühr pro Fill. Dieselben eingefrorenen Inputs/Stichtag und D01-Filter;
keine neuen Kandidaten, Halbfensteroptimierung, Schwellen oder Live-Schalter.
Jeder Fill und Close-Bestand wird mit dem unveränderten unabhängigen Audit-Buch
abgeglichen; zusätzlich Decimal-Lose mit 45 Stellen für Restkosten, Kaufgebühr,
abgegebene Kosten und realisierten Gewinn. Keine Produktions-Kostenfunktion wird
für den unabhängigen Sollwert verwendet.

| Zeile | Slippage je Seite | Endwert USD | Differenz zu 3b USD | Close-DD % | **obere Intrabar-Grenze %** | Fills |
|---|---:|---:|---:|---:|---:|---:|
| Live-Basis | 0,0 % | 13.418,88 | -12,57 | 7,9166 | **9,9428** | 171 |
| Live-Basis | 0,1 % | 12.852,01 | -13,29 | 8,4989 | **9,9428** | 171 |
| Live-Basis | 0,5 % | 10.815,30 | -15,34 | 12,0534 | **12,6548** | 171 |
| E42 / 12 | 0,0 % | 13.299,89 | 49,02 | 8,4177 | **9,9428** | 196 |
| E42 / 12 | 0,1 % | 12.677,52 | 51,89 | 9,0636 | **10,2437** | 196 |
| E42 / 12 | 0,5 % | 10.467,26 | 59,84 | 13,1053 | **13,6995** | 196 |

Alle sechs Läufe werden nach dem ersten tatsächlich gefüllten Kauf in einen
JSON-Checkpoint geschrieben und in einem **neuen Python-Prozess** fortgesetzt.
Der kanonische SHA256 über das gesamte Ergebnis muss exakt gleich sein.
Ergebnisübersicht: [4-ergebnis.json](4-ergebnis.json); vollständige Ledger und
unabhängige Lose: `4-ledger.json.gz`; sechs Checkpointdateien `4-restart-*.json.gz`.
Erste konkrete Pfad-/Einstandsdifferenzen: `4-differenzen.json`.
Originaldaten, alte Signale/Ergebnisse, Audit-Buch und 3b-Ergebnisse vor/nach gehasht.

Insgesamt **1.101 Fills und 9.054 Close-Zeilen** unabhängig geprüft. Schon der
erste echte Kauf liefert ohne Slippage Kosten-Einstand 93.766,906907 statt der
alten Signalreferenz 94.026,465. Die erste Kandidatendifferenz der Live-Basis
liegt bei Kerzen-ID 1773705600000: gültiger Strukturstop 74.604 statt TP1-Kandidat.
Der erste unterschiedliche Fill hat dort nur einen anderen Grund (STOPLOSS statt
VERKAUF_REST), noch denselben Preis und dieselbe Menge. Die Gesamtdifferenzen
entstehen entlang der danach unterschiedlichen Strategiepfade; sie sind weder
ein isolierter Slippageeffekt noch ein Nachweis besserer Strategiegüte.

## Wiederholung, Sicherung und Grenzen

```text
python engine/run_tests.py
python engine/sabotage_4.py
python engine/sabotage_3b.py
python engine/sabotage_d01.py
python engine/sabotage_f09.py
python tools/verify_4.py --audit-root ../audit-work
python tools/verify_4_scope.py
```

Windows: `PYTHONUTF8=1`. Messungen schreiben ausschließlich separate `4-*`-Dateien;
`--out-dir` erlaubt eine neue lokale Ausgabestelle. Kein API-Abruf oder Workflow.
Workflows vor Push geprüft: nur `Tests` reagiert auf den eigenen Zweig; Pages nur
auf main/site oder Signal-Engine/Backtest, niemals auf Tests. [Scope-Beleg](4-scope.json).

Exakte Abschluss-SHA, Remote-HEAD, Tests-CI und unverändertes Tagobjekt/-ziel stehen
in `C:/Users/oeztu/BTC-Trading/audit-backups/4-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.
Die Sicherung enthält Abschlussbundle, ZIP, Hashmanifest, eingefrorene externe
Inputs sowie einen frisch restaurierten Clone mit vollständigem Baumvergleich,
erneuter Testsuite/Sabotagen und sechs erneut identischen Prozessfortsetzungen.
Der Sicherungstag bleibt Objekt 7d78094… auf 469be65…; main wurde weder gemerged noch
gepusht. Keine neuen Live-Schalter, Nachrichten, Orders, Deployments oder Dispatches.

Grenzen: idealisiertes Null-Latenz-Folge-Open, keine echte Fill-Evidenz; 4h-OHLC
belegt keine Intrabar-Reihenfolge/Liquidität. Kaufkosten-Einstand enthält keine
hypothetische spätere Verkaufsgebühr und garantiert deshalb keinen Netto-Nullverlust.
Historische Signalreferenz und unbekannte Altbestandsdaten bleiben entsprechend
gekennzeichnet. Kein Rückschluss auf gewünschte Rendite/Strategiegüte; neue
DD-Schwellen erst vor späteren Entscheidungen. V2, Shorts/Margin/Funding, E41.6
und weitere Auditbefunde nicht bearbeitet. F13 bleibt 5a, F17 bleibt 5b.

Etappe 4 danach beenden. Nächster eigener Auftrag: **Etappe 5a, GPT-6 Sol / hoch**,
wegen dauerhafter Versandliste und Fehler-/Wiederanlaufsimulation. Aufgabenbezogene
Empfehlung, keine automatische Modellumstellung; Sol unterstützt anspruchsvolle
Codearbeit und `high` laut [OpenAI Docs](https://developers.openai.com/api/docs/models/gpt-6-sol),
abgerufen 28.09.2026. [Startauftrag](START-5A.md). Keine Folgeetappe automatisch starten.
