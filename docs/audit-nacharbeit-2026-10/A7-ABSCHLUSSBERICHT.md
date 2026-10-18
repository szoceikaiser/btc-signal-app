# A7 – Abschluss der festgelegten historischen Vergleiche

Stand 02.10.2026. Ausgang ist der geprüfte A6-Commit
`8b6af70b1897e8aefff5552f878297cc0090ef26`; der tatsächliche A7-Zwischenstand
war `a056c6c0495b2b82ff6965acbbb7f6fbbf7338e1`. Dieser Bericht betrifft
ausschließlich A7. Originalaudit, ursprüngliche R0/R1-Daten, alte Berichte,
Furkan-Quellen und Forschung bleiben erhalten. Die endgültige Commit-SHA,
CI und Wiederherstellung stehen in der gesonderten A7-Übergabe.

## Vertrag und Umfang

Das [vorab gespeicherte Manifest](A7-analysemanifest-v1.json) enthält 79 alte
Gitterzeilen und acht Strukturzeilen; S004 ist identisch zu V000, also 86
eindeutige Konfigurationen. [A7-Auswertbarkeit v2](A7-auswertbarkeit-v2.json)
erlaubt 85 Spotzeilen **nur als bedingte Offline-Modellrechnung** auf der
eingefrorenen Flow-Ableitung. Die erste, strengere v1-Matrix wurde noch vor
Renditeläufen durch die Prüfung eingefrorener Quellen revidiert; sie bleibt
als Zwischenbefund sichtbar. Vier aktive Liquidationspunkte bleiben `missing`.
Weder damalige API-Verfügbarkeit noch echte Fills sind nachgewiesen
([Ableitungsvertrag](A7-ABLEITUNGSVERTRAG-v2.md)). V035 wird unten gesondert
behandelt.

Die 85 Spotzeilen wurden für R0 und R1 in jedem der fünf **kausalen** S0–S4-
Szenarien gerechnet: 850 vollständige Modellläufe. S0 hat für jede Zeile
zwei separat gestartete Hälften (340 weitere Läufe). V000/V004 haben je
Paket und Szenario zwei fortlaufende Drittel-Frischstarts (40 Läufe); V000
hat zusätzlich die vorgeplanten Kapitalquoten 0,6 und 0,5 je Paket/Szenario
(20 Läufe). Die Quote 1,0 ist der jeweilige Standardlauf. Jede Laufdatei
enthält Monate, drei fortlaufende Drittel, Zeitgrenze, Kosten, Bestände,
Risikobänder, Signale, offene Endorders und einen unabhängigen
Kosten-/Bestandsabgleich. Der [vollständige Ergebnisindex](A7-resultindex-v1.json)
verweist mit SHA-256 auf jede dieser 1.250 Dateien. Die
[kompakte Zeilentabelle](A7-ERGEBNISSE-v1.md) zeigt alle 85 Spotzeilen,
beide Pakete und alle fünf Szenarien.

Getrennt davon sind für 85 Zeilen, R0/R1 und alle vier ursprünglichen
Ausführungs-/Kostenfälle 170 alte Diagnoseobjekte berechnet. Auch die
ursprünglich geplanten separat gestarteten Level-Hälften je Zeile/Paket
liegen als 170 eigene Objekte vor. Die alten Level- und Gleichschlussfälle
sind rückblickende Preisdiagnosen. Ihre Zahlen werden **nicht** mit den
kausalen V1/i+2-Ergebnissen gemeinsam gerankt
([F12-Vertrag](A5-VERTRAG.md), [A7-Legacy-Skript](../../tools/a7_legacy.py)).

## Befunde, Wirkung und Belege

| Priorität / Bezug | Fundstelle | Wirkung und Beleg |
|---|---|---|
| P1 F02 / V035 | [A5-VERTRAG.md:21](A5-VERTRAG.md#L21), [A5-BERICHT.md:11](A5-BERICHT.md#L11), [A7-auswertbarkeit-v2.json:9](A7-auswertbarkeit-v2.json#L9) | Die Short-Variante wurde unter F02 **geprüft**: synthetische Long-/Short-Buchfälle, 1x-Margin, Gebühren, Fundingkalender, Markbewertung und Ablehnung ungültiger Derivatläufe. Für eine historische V035-Rendite fehlen jedoch ein kausaler Short-Strategiepfad, der damalige Instrumentvertrag, vollständige Fundingzahlungen und Markpreise sowie belegbare Short-Fills. Es gibt deshalb ausdrücklich keinen V035-Renditewert und keine Spot-Ersatzrendite. Eine technische Prüfung hat stattgefunden; ein valider historischer V035-Backtest nicht. |
| P1 F07/D02 / historische Verfügbarkeit | [A7-ABLEITUNGSVERTRAG-v2.md:1](A7-ABLEITUNGSVERTRAG-v2.md#L1), [A7-auswertbarkeit-v2.json:10](A7-auswertbarkeit-v2.json#L10) | Die eingefrorenen Quellen tragen die bedingte Zeit- und Herkunftsmodellierung für 85 Spotzeilen. Sie beweisen keine tatsächliche Veröffentlichung/API-Antwort am jeweiligen Schluss. Die vier fehlenden Liquidationspunkte wurden nicht mit neutralen Nullen gefüllt. Die Rückrechnung ist eine Modellrechnung, kein damals sicher ausführbarer Backtest. |
| P1 F12 / Modelltrennung | [A5-BERICHT.md:13](A5-BERICHT.md#L13), [tools/a7_legacy.py:1](../../tools/a7_legacy.py#L1), [tools/a7_batch.py:136](../../tools/a7_batch.py#L136) | Alte Level-/Gleichschlusskonten und kausale geschlossene V1/i+2-Konten haben verschiedene Signal-/Fillverträge. In R1 erreicht V000 in den vier alten Diagnosefällen 34,20 / 33,19 / 30,19 / 16,71 %, im kausalen S0 33,82 %. Daraus folgt keine Rangfolge realer Ausführbarkeit. |
| P2 F06/F07/D02 / Ereignisfolgen | [A7-events-R0/V050.json](A7-events-R0/V050.json), [A7-events-R0/V075.json](A7-events-R0/V075.json), [A7-intermediate-A2-S0-v1.json](A7-intermediate-A2-S0-v1.json) | Von Originalaudit zur heutigen numerischen Alt-Reihe unterscheiden sich 79/85 R0-Signalreihen; dieser Schritt bündelt mehrere Code-/Vertragsänderungen und ist nicht allein A2 zuzurechnen. Beim isolierten Wechsel von numerischer Alt-Reihe zur modellierten Herkunftsreihe ändern sich nur bei V050 zwei Nachkäufe. Die folgende CVD-Umstellung entfernt nur bei V075 eine Warnung, keinen Trade. Die gezielten Zwischenbilanzen quantifizieren die Wirkung unten. Alle 85 Ereignisobjekte liegen unter `A7-events-R0/`; R0/R1-Alt→Kausal-Unterschiede stehen zeilenweise im Ergebnisindex. |
| P2 F09 / numerische Buchgrenze | [engine/inventory.py:22](../../engine/inventory.py#L22), [engine/execution_v1.py:275](../../engine/execution_v1.py#L275), [engine/test_a7_numerical.py:8](../../engine/test_a7_numerical.py#L8) | Im Vollgitter traten wenige Gleitkomma-Reste nach vollständiger Losveräußerung auf. Eine auf Loszahl und früheren Bestand begrenzte Rundungstoleranz entfernt nur Rundungsstaub; echter Oversell bleibt abgewiesen. Acht unabhängige Vergleichsfälle bei S006/S007 weisen je eine Nullrundung im Gegenbuch von höchstens 1,14×10⁻¹⁷ BTC aus; der materielle Kosten-, Bestands- und Risikovergleich besteht. |
| P2 M01 | [A7-M01-M02-BEWERTUNG.md:1](A7-M01-M02-BEWERTUNG.md#L1), [A7-M01-M02-zuordnung-v1.json](A7-M01-M02-zuordnung-v1.json) | 76 dokumentierte Entscheidungen sind jeweils ihrer damaligen Basis und ihrem damaligen Fenster zugeordnet. Von 85 alten Codezeilen entspricht nur eine V000, 23 unterscheiden sich in einem Parameter, 61 in mehreren. Alte `LIVE`-Vergleiche werden nicht durch einen neuen Vergleich zu V000 ersetzt; frühe Eingaben/Basen sind teils nicht rekonstruierbar. |
| P2 M02 | [A7-M01-M02-BEWERTUNG.md:91](A7-M01-M02-BEWERTUNG.md#L91), [docs/nach-6/search-inventory.json](../nach-6/search-inventory.json) | Mindestens 94 versionierte Suchen sind dokumentiert; die vollständige Suchfamilie ist unbekannt. Alle Monate, Hälften und Drittel wurden bei der Entwicklung wiederverwendet. Die gepaarte Statistik ist nur für das vorab fixierte Paar und vollständige UTC-Tage zulässig, ohne Auswahlbereinigung oder unabhängige Validierungsbehauptung. |

## Festgelegter Basis-/E42-Vergleich

R1 läuft vom 18.01.2026 20:00 UTC bis zur Grenze 29.09.2026 12:00 UTC,
R0 bis 27.09.2026 08:29:08,840 UTC. Beide verwenden dieselben geschlossenen
4h-Slots, Modellgebühren und Risikodefinitionen. S0–S4 sind jeweils die
vorab festgelegten **kausalen** Kosten-/Ausführungsfälle. R0 und R1
werden als zwei überlappende Fenster behandelt, nicht als unabhängige
Replikationen.

| R1-Szenario | V000 % | V004/E42 % | E42 minus Basis USD | zusätzlicher Schluss-DD E42, pp |
|---|---:|---:|---:|---:|
| S0 | 33,82 | 32,63 | −118,66 | +0,50 |
| S1 | 28,14 | 26,40 | −173,96 | +0,57 |
| S2 | 7,75 | 4,28 | −346,73 | +1,05 |
| S3 | 26,76 | 27,93 | +117,27 | +0,14 |
| S4 | 7,92 | 7,36 | −56,23 | +0,02 |

Der gezielte Paarlauf reproduziert für alle zehn Paket/Szenario-Kombinationen
die jeweiligen Nach-6-Endwerte exakt (Delta 0,00 USD). In R1/S0 sind es
13.381,598027877413 USD für V000 und 13.262,942895190434 USD für V004
([Paarlauf](A7-targeted-R1-S0-summary.json)). Die R0-Ergebnisse und jede
Monats-/Drittelbilanz stehen im Ergebnisindex. Für R1/S0 gewinnt E42 nur
in der ersten separat gestarteten Hälfte um +0,122 Prozentpunkte, verliert
in der zweiten um −1,064 Punkte; jeder Leave-one-month-out-Vergleich
bleibt negativ. Unter den 85 Spotzeilen verbessert R1/S0 bei 17 die
Gesamtrendite gegenüber V000; nur V054 liegt in beiden Hälften knapp vorn
(+0,076/+0,179 Punkte), unterschreitet aber die alte Schwelle von +1 Punkt
je Hälfte und fällt bei einigen ausgelassenen Monaten zurück. Keine Zeile
erfüllt diese alte Hälftenschwelle. Das ist eine beschreibende Einordnung
des eingefrorenen Gitters, keine neue Parameterwahl.

Die getrennten Drittel-Frischstarts von V000/V004 liefern in R1 für S0
−1,148/−1,111 Punkte zugunsten V000; in S3 +1,679/+1,276 Punkte zugunsten
E42. Die übrigen Szenarien und R0-Werte stehen im Index. Ein Frischstart
setzt den Buchbestand neu und ist deshalb nicht mit einem fortlaufenden
Drittelbeitrag gleichzusetzen.

## Kapital, Benchmark und Ausführungsmodelle

Für V000/R1/S0 ergeben die vorgeplanten Quoten 1,0 / 0,6 / 0,5
Renditen von 33,82 / 29,19 / 24,60 %, Schluss-Drawdowns von
7,92 / 7,55 / 6,74 % und mittlere BTC-Exposition von
33,61 / 24,02 / 20,20 %. Geringerer Kapitaleinsatz mindert den
modellierten Rohgewinn und das Risiko; die Quoten sind eigene
Kapitalfälle, keine zusätzlichen Parametersuchen. Alle anderen
Paket/Szenario-Kapitalfälle und die vier alten Diagnosefälle mit Quoten
stehen in [A7-resultindex-v1.json](A7-resultindex-v1.json) und
[A7-legacy-capital-v1.json](A7-legacy-capital-v1.json).

Ein einfacher BTC-Kauf am R1-Start und Halten bis zum R1-Ende läge bei
−10,03 % markiert zum Schlusskurs. Der zusätzlich gerechnete
Expositionsvergleich verwendet die erst nach Sichtung von V000 bekannte
mittlere Exposition und ist ausdrücklich **post hoc**, kein fairer
Vorab-Benchmark ([A7-buyhold-v1.json](A7-buyhold-v1.json)). Auch der
positive Abstand der Modellrechnung zum Kauf-und-Halten-Pfad belegt
weder echte Handelsausführung noch zukünftige Überrendite.

## A2-Zwischenstände und gepaarte Statistik

Für V050/R1/S0 ist der numerische Alt-Endwert um 159,018561 USD niedriger
als derselbe Parameterlauf mit modellierter Verfügbarkeit; auf R0 sind es
159,461596 USD. Die korrigierte CVD ändert bei V050 danach keinen
weiteren Endwert. Bei V075 ändert die entfernte Warnung in R0 und R1
jeweils 0,00 USD. Das sind gezielte, unabhängig verbuchte
Zwischenstände, keine Aufteilung sämtlicher früherer Ergebnisänderungen
auf einzelne Fehler. Die Ursprungsreihe enthält andere Code-/Datenstände;
79 geänderte Ereignisreihen lassen sich daher nicht monokausal F06/F07/D02
zuschreiben ([A7-intermediate-A2-S0-v1.json](A7-intermediate-A2-S0-v1.json)).

Die [gepaarte Auswertung](A7-paired-statistics-v1.json) wurde für das
vorab fixierte Paar auf 251 vollständigen R0- und 253 vollständigen
R1-UTC-Tagen durchgeführt. Alle zehn S0–S4-Rechnungen reproduzieren die
jeweiligen Nach-6-U1-Werte exakt. Im R1/S0 ergibt der bedingte
14-Tage-Blockbootstrap für den E42-Vorteil ein Intervall von etwa
−3,74 bis +1,87 Prozentpunkten; acht der zehn Paket/Szenario-Intervalle
umfassen null, nur S2 liegt ganz auf der negativen Seite. Die 7-/28-Tage-
Sensitivitäten stehen im Artefakt. Wegen der früheren Auswahl, der
unbekannten vollständigen Suchfamilie und der wiederverwendeten Daten
ist dies keine auswahlbereinigte Signifikanz oder unabhängige Prognose.

## Prüfungen und Schlussfolgerung

Der v2-Auswertbarkeits-Preflight, die vollständige zehnspurige
Szenariomatrix, alle Halb-/Frischstart-/Kapitaldateien und der
Ergebnisindex wurden wiederholt geprüft. Der unabhängige Buchpfad ist
eine SHA-gleiche Kopie des Originalaudit-Buchs und gleicht jeden
kausalen Lauf einschließlich Fills, Gebühren, Monatsständen,
Beständen und DD-Bändern ab. Die lokale Engineregression bestand mit
792 Tests und 0 Fehlern ([Testlog](A7-engine-tests.log)); die drei neuen
Rundungs-Gegenfälle sind enthalten. Der separate Offline-GitHub-Workflow
hat nur Lese-/Testrechte und nutzt eingefrorene versionierte Inputs;
seinen Status zur endgültigen Commit-SHA nennt die Übergabe.

Die A7-Modellentscheidung ist begrenzt, aber klar: Die vorliegenden
bedingten Rechnungen tragen keine Aktivierung von E42 oder einer neuen
Gitterzeile. V035 hat keine valide historische Rendite. Alte
Level-Diagnosen, kausale Spotkonten und synthetische Derivat-Handfälle
haben unterschiedliche Verträge. M01 und M02 bleiben als historische
Inferenzgrenzen sichtbar. Es wurden keine neuen Kandidaten gewählt,
keine Daten gesammelt und keine Live-Funktion aktiviert. A8 ist die
anschließende unabhängige Gesamtabnahme und wurde hier nicht begonnen.
