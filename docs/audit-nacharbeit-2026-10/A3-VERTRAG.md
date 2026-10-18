# A3-Vertrag: UTC-Tage und belegte Börsenreihen v1

Festgelegt vor der A3-Korrektur und ohne Ergebnismessung. Die früheren R0/R1-Eingaben
und historischen Resultate bleiben unverändert. Eine neue historische Ableitung ist
gesondert zu versionieren; heutige Marktlisten belegen keinen damaligen Börsenkorb.

## F08 – Tagesabschluss

Ein 4h-Eingabewert trägt den UTC-Open-Zeitstempel und muss bereits nach D01
abgeschlossen sein. Ein UTC-Tag `[00:00, 24:00)` gilt erst ab der folgenden
UTC-Mitternacht als abgeschlossen. Seine Tageskerze entsteht nur aus genau sechs
verschiedenen, auf 00/04/08/12/16/20 UTC ausgerichteten, abgeschlossenen
4h-Kerzen. Doppelte, fehlende oder falsch ausgerichtete Slots machen diesen Tag
nicht auswertbar. Teil- und Lückentage gehen weder in Tages-EMA noch Tages-Fib
ein. Tageswerte bleiben bei später angehängten Tagen für frühere Präfixe stabil.

## F14 – vollständiger Korb

Die angeforderte Symbolliste ist der Nenner. An einem Zeitpunkt zählt eine Summe
oder ein OI-gewichtetes Mittel nur, wenn jedes angeforderte Symbol eine gültige
Messung beziehungsweise Messung und Gewicht hat. Ein vollständig ausbleibendes
Symbol macht die ganze Reihe nicht auswertbar; Bericht und Auslassungszahlen
nennen es. Ein ausbleibender Einzelzeitpunkt wird ausgelassen, nie durch null
oder eine Teilsumme ersetzt. Leerer angeforderter Korb ist ebenfalls nicht
auswertbar.

## F15 – Instrumente und Volumen

Für die Auswahl nach Umsatz ist die Vergleichseinheit USD. `v`/`bv` von
`ohlcv-history` bleiben in der instrumenteigenen Denominierung. Nur eine
ausdrücklich belegte `BASE_ASSET`-Reihe mit BTC als Basiswert und gültigem,
positivem BTC/USD-Schlusskurs darf pro Zeitstempel mit diesem Kurs in USD
umgerechnet werden. Eine `QUOTE_ASSET`-Reihe darf nur bei expliziter
USD-Quote direkt als USD gelten. USDT/USDC/FDUSD/USDE benötigen einen belegten
zeitgleichen USD-Umrechnungskurs; 1:1 wird nicht still vorausgesetzt. `BTC` und
`USD` als bereits nachgewiesene Einheiten sind gleichbedeutende
Kompatibilitätswerte zu `BASE_ASSET` und `QUOTE_ASSET`. Fehlende Denominierung,
Kurs, Quote-Konversion oder Volumenfelder sperren die Auswahl dieser Reihe.
Rangfolgen je Börse und zwischen Denominierungsgruppen verwenden ausschließlich
normalisierte USD-Umsätze. Futures-CVD selbst wird weiterhin nur innerhalb
gleicher belegter Rohdenominierung summiert; ein ausgeschlossener Markt erscheint
mit Grund. Für Spot-CVD müssen ausgewählte Rohreihen dieselbe belegte
Basiswerteinheit BTC haben. Der heutige Auswahlkorb ist kein historischer
Point-in-time-Korb; historische Vergleiche ohne solchen Nachweis sind ausdrücklich
nicht auswertbar und werden nicht still als damals verfügbare Reihe etikettiert.

Die vorhandenen Aggregationsadapter bleiben außerhalb des aktiven Live-Flows.
