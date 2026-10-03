# A7-Nachprüfung V035 / F02

Stand: 03.10.2026. Diese additive Prüfung folgt dem abgeschlossenen A7-Commit
`27dffe79d01b089367412cb3f13379246f11638b`; sie ändert weder das vorab
festgelegte Analysemanifest noch die 85 Spot-Ergebnisse und beginnt A8 nicht.

## Befund und Reichweite

**P1 für eine V035-Gesamtrendite:** `engine/execution_v1.py:100` setzt
`bias_short=False`; `engine/derivative_accounting.py:43-167` verbucht nur
vorgegebene Fills, erzeugt aber keine kausal ausgeführten Strategieentscheidungen.
`engine/backtest.py:945-953` bezeichnet die alte Short-Reihe ausdrücklich als
retrospektive Signalkonten-Diagnostik. Sie besitzt weder tatsächliche
Short-Fills noch Funding-/Marginbuchungen. Die F02-Sperre ist deshalb eine
konkrete fachliche Auswertungsgrenze; die synthetische Buchmechanik und der
folgende historische Einzelfall wurden sehr wohl geprüft.

**Erfolgreicher begrenzter Gegenfall:** `tools/a7_v035_probe.py` nimmt den
ersten chronologischen V035-Short-Einstieg und den nächsten vollständigen
Short-Ausstieg aus dem erhaltenen Signalband. Hypothetische Orderzeitpunkte
sind die folgenden 4h-Öffnungen am 27.01.2026 00:00 und 30.01.2026 12:00 UTC.
Kraken PF_XBTUSD-Handelspreise sind 88.258 und 83.011 USD; die Menge beträgt
0,0282 BTC, die bestehende S0-Modellgebühr 0,1 % je Fill. Für alle 84
offenen Fundingstunden liegen eingefrorene Kraken-Zahlungssätze vor. Das
A5-Derivatbuch endet bei 10.144,83717053630747800577560 USD; Funding
ist +1,701556336307478005775600000 USD, Gebühren 4,8297858 USD.
Ein unabhängig formulierter geschlossener P&L-/Kosten-/Fundingausdruck liefert
dasselbe Endkapital (Abweichung 0 USD); die 1x-Risikogrenze wurde nicht
verletzt. Beleg: `A7-V035-sources/first-short-probe-v1.json`. Dieser einzelne
historisch bepreiste Fall ist **kein** geschlossener Strategiegesamtlauf:
das retrospektive Signalband erhält keine Rückmeldung über ausgeführte Fills.

**P1 Datenlücke:** Im unveränderten R1-Archiv
`docs/nach-6/r1-raw/funding.json` fehlen genau drei volle PF_XBTUSD-Stunden
innerhalb des Fensters: 04.02.2026 12:00, 13.02.2026 18:00 und
09.05.2026 06:00 UTC. Eine erneute öffentliche Kraken-Abfrage nach
`historicalfundingrates` enthielt diese Stunden ebenfalls nicht. Der
[offizielle CSV-Export](https://support.kraken.com/articles/export-historical-funding-rates)
endet für dieses Symbol am 01.02.2026 und überbrückt die Lücken nicht.
Der untersuchte ZIP-Hash und die Abdeckung stehen in
`A7-V035-sources/official-csv-probe.json`.

Die [öffentliche Kraken-Fundinggrafik](https://futures.kraken.com/api/charts/v1/analytics/PF_XBTUSD/funding?since=1771002000&interval=3600&to=1771012800)
zeigt am 13.02. und 09.05. an der fehlenden Stunde jeweils exakt den
vorherigen Satz. Die benachbarten Grafiksätze stimmen mit dem eingefrorenen
Fundingarchiv auf weniger als 10⁻¹² USD/BTC überein. Daraus folgt **nicht**,
dass der wiederholte Grafiksatz als eigene stündliche Zahlung tatsächlich
gebucht wurde; eine Fortschreibung durch die Grafik ist möglich. Am
04.02. liefert die Grafik auch mit engerem Zeitbereich, Minuten- und
Vierstundenauflösung keine Daten. Die Rohantworten, URLs, SHA-256-Hashes und
der deterministische Abgleich stehen in
`A7-V035-sources/gap-reconciliation-v1.json` und
`tools/a7_v035_reconcile.py`. Keiner der drei Sätze wurde als Null,
Vorwert oder Interpolation ins Derivatbuch eingeführt.

**P1 Ausführungsnachweis:** Die heruntergeladenen öffentlichen
[Kraken-Candles](https://docs.kraken.com/api/docs/futures-api/charts/candles/)
decken R1 für PF_XBTUSD als 4h-Handels- und 1h-Mark-/Spotreihe lückenlos ab;
Manifest, Antwort- und Datei-Hashes stehen in
`A7-V035-sources/manifest.json`. Sie belegen weder damalige API-Verfügbarkeit
noch reale Fills, Kontrakt-/Gebührenhistorie oder eine kausale Long/Short-
Strategie. Der erste erfolgreiche Einzelfall setzt ausdrücklich die alte
S0-Modellgebühr ein und behauptet keinen konkreten Kraken-Gebührentarif.

## Abschlussentscheidung dieser Nachprüfung

V035 besteht die **gezielte historische Short-Buchprobe** einschließlich
84 beobachteter Fundingstunden und unabhängigem Endbestandsabgleich.
V035 besteht **keinen vollständigen historischen R0/R1-Renditelauf**. Eine
solche Zahl wäre derzeit erfunden: Es fehlen ein eigener kausaler
Long/Short-Ausführungspfad und ein prüfbarer Zahlungsnachweis für die drei
Stunden, soweit eine Position dort offen wäre. Erst nach einem solchen
Pfad lässt sich anhand tatsächlicher Positionen entscheiden, welche Lücken
überhaupt zahlungsrelevant sind; nötige Raten müssen dann aus einem
zeitgestempelten Kraken-Archiv oder einer vergleichbar belastbaren
Abrechnung stammen. Ein GitHub-API- oder CI-Aufruf allein erzeugt diese
fehlenden historischen Zahlungen nicht. Das branchgebundene Offline-CI
prüft die eingefrorenen Quellen und die Buchprobe ohne Secrets, Sammlung,
Backtest-Dispatch oder Pages-Trigger.

Alle 22 Register-IDs bleiben erhalten; allein F02 erhält diese zusätzliche
Nachprüfung. Es gibt keine neue Rangfolge, keine Nachoptimierung und keine
Live-Freigabe.
