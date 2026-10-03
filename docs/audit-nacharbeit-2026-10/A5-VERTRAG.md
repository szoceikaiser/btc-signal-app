# A5 – Offline-Vertrag Kapitalbindung und Funding, Version 1

Vor Implementierung festgelegt, Basis
`291588946206333ca58d771f1cc96f261da1a981`. Nur F02 und F12/V2.
Keine Renditeoptimierung, neue Short-Strategie oder historische Neuberechnung.

## Instrument und Reichweite

V1 und i+2 bleiben unverschuldete Long/Spot-Vergleichsmodelle (`spot_btc_usd`).
Ein fehlendes Instrumentfeld bedeutet dort ausschließlich den bereits vereinbarten
Spot-Modellvertrag, nicht den Nachweis eines damals tatsächlich gehandelten Produkts.
Explizite Perpetuals, fremde Instrumente und Hebel ungleich 1 werden abgewiesen,
auch bei Long-only. `bias_short=True` bleibt abgewiesen. Ein Funding-Indikator im
Flow ist kein Zahlungsbuch. Alte Signalbänder bleiben retrospektive Diagnostik.

Die neue getrennte Buchrechnung verarbeitet ausdrücklich vorgegebene hypothetische
Fills, keine Strategieentscheidungen. Unterstützt sind Spot-Long und ein synthetischer
linearer BTC/USD-Perpetual mit USD-Sicherheiten (`linear_btc_usd_perpetual`).
Dies ist kein Kraken-/Brokervertrag. Inverse/quanto Produkte, Fremdwährungssicherheiten,
Kredite, Nettomargin über Produkte und Hebel >1 sind nicht unterstützt.
Die neue Buchrechnung macht V035 nicht historisch auswertbar: Instrumentvertrag,
vollständiges Zahlungsbuch, zugehörige Bewertungsreihe und kausale Short-Fills fehlen.

## Kapital, Gebühren und Bewertung

Start ausschließlich Cash, keine unbekannten manuellen Bestände. Jeder Fill besitzt
UTC-Millisekunden, Aktion open/close, Los-ID, Richtung, BTC-Menge und USD/BTC-Preis.
Bei gleichem Zeitpunkt gilt Eingabereihenfolge; Funding kommt vor sämtlichen Fills.
Los-ID bleibt eindeutig. Teilabbau ist möglich; Überverkauf wird abgewiesen.
Keine stillen Teilfüllungen: nicht finanzierbare Eröffnung wird vollständig abgelehnt.

Bei Spot kostet q zum Preis p inklusive Gebühr f: `q*p*(1+f)`; ein Verkauf erlöst
`q*p*(1-f)`. q ist eine explizite Menge, kein V1-Bruttobudget. Der V1-Budgetvertrag
bleibt unverändert. Spot kennt keine Short-Eröffnung und keine Fundingzahlung.

Beim linearen Perpetual ist Notional `N=q*p`, initial gebundene Margin `M=N/1`.
Das Wallet W enthält die gebundene Margin bereits. Eröffnung belastet W nur mit
`N*f`, bindet zusätzlich M; freie Mittel `W-Summe(M)` dürfen nicht negativ werden.
Unrealisierte Gewinne sind kein neues verfügbares Wallet. Eröffnungserlös eines
Shorts ist kein Cashzufluss. Beim Teilabbau wird M proportional freigegeben und
`d*q*(p_exit-p_entry)-q*p_exit*f` in W gebucht, d=+1 Long/-1 Short.
Equity ist `W+Summe(d*q*(mark-p_entry))`, nicht Wallet plus Margin plus PnL.
Gross Exposure ist die Summe aller absoluten aktuellen Notionals, ohne Long/Short-
Netting. Neue Positionen müssen auch nach Gebühren Gross/Equity <=1 erfüllen.
Zwei nominelle 100-%-Shorts können deshalb nicht gemeinsam eröffnet werden.

Bei jedem Bewertungsereignis prüfen: Equity >0, Margin <= Wallet und aktuelles
Gross Exposure <= Equity. Ein durch Preis/Funding verletzter Grenzwert macht den
gesamten Replay nicht auswertbar; kein erfundener Liquidationspreis oder Margin-Call.
Ein zu großer neuer Auftrag wird nur abgelehnt. Das ist ein bewusst konservativer
Offline-Gültigkeitsbereich, keine Börsenliquidationsregel. Kein Intrabar-DD oder
fortdauernde Solvenz aus einzelnen Markpunkten ableiten. Endbewertung braucht
einen expliziten Markpreis; kein fingierter Endverkauf, keine Schlussverkaufsgebühr.

## Funding und Zeit

Perpetual-Replay verlangt einen ausdrücklich gelieferten periodischen UTC-Kalender
(Intervall in Millisekunden, Offset) sowie Quelle und dezimale Zahlungsraten pro
Termin. Kein Defaultintervall; Handfälle verwenden synthetisch 8 Stunden.
An jedem Kalendertermin mit Altbestand sind Rate und Markpreis am exakt gleichen
Zeitpunkt zwingend. Positive Rate: Long zahlt, Short erhält:
`Zahlung_ans_Wallet=-d*q*mark*rate`. Negative Rate kehrt die Richtung um.
Beobachtete Null ist zulässig; fehlend, NaN, Fortschreibung und eine bloße
8h-Indikatorrate sind kein Nullbeleg und kein Zahlungsersatz.
Eine Position mit Eröffnung t und Schließung u zahlt bei `t < Termin <= u`;
Eröffnung am Termin geschieht nach dessen Zahlung. Teilabbau am Termin ebenfalls
danach. Keine Zahlung für bereits geschlossene Lose. Doppelte/ungeordnete Fills,
Funding außerhalb des Kalenders und Daten außerhalb des Fensters werden abgewiesen.

## F12/V2

V1/Folge-Open und i+2 bleiben kausale idealisierte Vergleichsverträge. Frühere
Level-/Same-close-Ergebnisse beweisen keine vorher platzierten Orders und keine
erreichbare Live-Rendite. Ihr Preisunterschied ist weder Orderwert noch sichere
Ober-/Untergrenze. V2 erfordert vorher bekannte Order-ID, Aktivierung, Preisbedingung,
Menge, Reservierung, Gültigkeit, Storno/Ersetzung und Konfliktregeln. Ohne damalige
Order-/Intrabardaten sind Ausführung, Reihenfolge, Liquidität und Teilfills unbelegt.
Die V2-Vorschläge aus F01-F12-VERTRAG bleiben Vorschläge; A5 baut keine V2-Strategie.
E41.6 und unbekannte manuelle Live-Bestände bleiben außerhalb des Auftrags.

## Abnahme

Original-F02 vor Korrektur am Audit- und A4-Stand reproduzieren; F12-Levelgegenfall
erhalten. Neue Long-/Short-/Spot-Handrechnungen, zwei 100-%-Shorts, Gebühren,
Teilmarginfreigabe, positive/negative/Null-/fehlende Fundingzahlungen, Grenzzeiten,
Risikosperre und unabhängiges Losbuch prüfen. Historische F02-Einstufung additiv mit
Originalhash/Parametern dokumentieren, insbesondere V035, ohne Renditefelder.
Keine pauschale historische Freigabe der anderen Zeilen; A3-Datengrenzen bleiben.
