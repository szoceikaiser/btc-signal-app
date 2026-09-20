# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 12.01.2026-20.09.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2439 4h-Kerzen geladen · Stand: 2026-09-20 11:31 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 20.09.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation. **max. Rueckgang** = groesster Einbruch vom jeweiligen Hoch (Drawdown) — je naeher an 0, desto ruhiger der Verlauf. **Seit 28.08.2026 (E27) lueckenlos gemessen:** an jeder Kerze und an ihrem unguenstigsten Punkt (Tief bei Long, Hoch bei Short). Vorher zaehlten nur die Signalzeitpunkte — was das Konto zwischen zwei Signalen an Buchverlust erlebte, fehlte. **Alle Rueckgangszahlen aus Berichten vor diesem Datum sind deshalb zu freundlich und nicht mit den heutigen vergleichbar.** **Einsatz** = wie viel des Kapitals je Position hoechstens investiert wird (100 % = keine Reserve, 60 % = 40 % Pulver bleibt trocken; Furkan-Update Juli 2026). Recall = Aehnlichkeit zu Furkans Terminen IM Fenster, KEIN Gewinn.

**Lesehilfe zu den Namen:** `LIVE` ist die Abkuerzung fuer *nur Long + Kaufleiter + Flush core* — der Flush steckt also drin. Jede Zeile, die mit `LIVE +…` beginnt, baut darauf auf. Die Zeile *+Kaufleiter* ist dagegen OHNE Flush.

**Gegengeschaefte** (E25, Kaiser 28.08.2026) = Anzahl der 4h-Kerzen, in denen gleichzeitig aufgestockt UND teilverkauft wurde, meist zum selben Preis. An der Rendite ist das kaum abzulesen — der Backtest handelt beide Seiten zum exakten Signalpreis, netto bleibt die Tranchen-Differenz minus zwei Gebuehren. In der Praxis ist so ein Paar aber nicht ausfuehrbar: zwei Limit-Orders zum selben Preis heben sich auf, und die Telegram-Nachrichten widersprechen sich. Die Spalte misst also Umsetzbarkeit, nicht Gewinn. Der Schalter dagegen heisst `no_flip`.

**Aufwaerts** (E26) = Aufwaerts-Beteiligung: wie viel des Anstiegs die Variante in steigenden Monaten mitnimmt (Einzelheiten im Abschnitt weiter unten). Hoch ist gut. Die Rendite allein verraet das nicht — eine Variante kann glaenzend aussehen, weil sie in fallenden Monaten gewinnt, und in einer Rally trotzdem kaum mitkommen. Wer wissen will, ob ein Schalter grosse Anstiege besser einfaengt, schaut hier hin und nicht auf die Rendite. **Abwaerts** ist das Gegenstueck fuer fallende Monate — niedrig oder negativ ist gut. Die beiden gehoeren zusammen gelesen: Wer mehr vom Anstieg mitnimmt, ist laenger und groesser investiert und macht deshalb in aller Regel auch mehr vom Rueckgang mit. Steigt Aufwaerts, ohne dass Abwaerts mitsteigt, ist wirklich etwas gewonnen; steigen beide, wurde nur das Risiko erhoeht.

| Variante | Recall | Praez. | Rendite | max. Rueckgang | Einsatz | Signale | Gegen-
geschaefte | Auf-
waerts | Ab-
waerts |
|---|---|---|---|---|---|---|---|---|---|
| nur Long (Basis) | 50% | 36% | +9.5 % | -7.8 % | 100 % | 101 | 2 | 38 % | 16 % |
| +Kaufleiter | 50% | 33% | +14.7 % | -8.7 % | 100 % | 122 | 2 | 48 % | 16 % |
| +Flush core | 56% | 27% | +19.4 % | -14.7 % | 100 % | 180 | 2 | 60 % | 18 % |
| LIVE: nur Long +Kaufleiter +Flush core | 56% | 26% | +23.9 % | -15.5 % | 100 % | 205 | 2 | 67 % | 17 % |
| +Kaufleiter +Bed.Stop | 50% | 33% | +12.9 % | -9.6 % | 100 % | 133 | 2 | 44 % | 15 % |
| LIVE +Rest-Freigabe | 61% | 29% | +16.5 % | -15.5 % | 100 % | 216 | 2 | 61 % | 23 % |
| LIVE +Stop nachziehen | 61% | 28% | +22.2 % | -15.1 % | 100 % | 212 | 2 | 63 % | 16 % |
| LIVE +Stop nachziehen +Rest-Freigabe | 61% | 29% | +17.0 % | -15.1 % | 100 % | 218 | 2 | 61 % | 22 % |
| LIVE +Stop +Liq-Kaskade | 67% | 29% | +16.0 % | -13.2 % | 100 % | 260 | 8 | 48 % | 14 % |
| LIVE +Stop +Liq-Zonen | 72% | 29% | +14.7 % | -12.6 % | 100 % | 290 | 23 | 45 % | 13 % |
| LIVE +Stop +Liq beides | 72% | 30% | +14.9 % | -12.6 % | 100 % | 294 | 25 | 45 % | 13 % |
| MEINE Einstellung ohne Flush | 56% | 40% | +16.2 % | -9.4 % | 100 % | 217 | 0 | 32 % | 0 % |
| LIVE +Stop +Liq-Konfluenz aufstocken | 61% | 29% | +23.5 % | -15.7 % | 100 % | 257 | 4 | 65 % | 16 % |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 56% | 30% | +20.9 % | -15.4 % | 100 % | 191 | 1 | 68 % | 22 % |
| LIVE +Stop +Verkauf am letzten Hoch | 72% | 30% | +19.6 % | -13.3 % | 100 % | 270 | 17 | 52 % | 11 % |
| LIVE +Stop +Verkauf am schwachen Hoch | 67% | 30% | +19.9 % | -13.3 % | 100 % | 256 | 8 | 52 % | 11 % |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 61% | 28% | +14.3 % | -9.9 % | 60 % | 212 | 2 | 42 % | 11 % |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 61% | 28% | +11.9 % | -8.3 % | 50 % | 212 | 2 | 35 % | 9 % |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 61% | 28% | +20.9 % | -15.1 % | 100 % | 210 | 2 | 63 % | 18 % |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 56% | 28% | +24.8 % | -14.9 % | 100 % | 197 | 1 | 69 % | 17 % |
| LIVE +Stop +Sperre 48 h nach Stop | 56% | 29% | +25.9 % | -11.9 % | 100 % | 181 | 2 | 64 % | 11 % |
| LIVE +Stop +Mindest-Stopabstand 2 % | 44% | 30% | +26.6 % | -10.5 % | 100 % | 133 | 0 | 59 % | 6 % |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 44% | 33% | +20.1 % | -10.5 % | 100 % | 124 | 0 | 47 % | 6 % |
| LIVE +Stop +alle vier neuen Hebel | 39% | 32% | +16.1 % | -10.5 % | 100 % | 115 | 0 | 37 % | 4 % |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 44% | 32% | +29.4 % | -10.9 % | 100 % | 162 | 1 | 63 % | 5 % |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 56% | 28% | +28.6 % | -12.6 % | 100 % | 218 | 4 | 69 % | 11 % |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 56% | 35% | +30.6 % | -9.2 % | 100 % | 198 | 16 | 60 % | 2 % |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 56% | 33% | +23.8 % | -11.1 % | 100 % | 208 | 17 | 56 % | 8 % |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 56% | 34% | +21.5 % | -9.4 % | 100 % | 244 | 24 | 48 % | 5 % |
| NEU-LIVE +kein Gegengeschaeft je Kerze | 50% | 32% | +26.5 % | -9.5 % | 100 % | 196 | 0 | 53 % | 2 % |
| NEU-LIVE +Ziele festhalten | 56% | 36% | +29.2 % | -9.2 % | 100 % | 202 | 16 | 48 % | -6 % |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | 50% | 32% | +26.0 % | -9.5 % | 100 % | 203 | 0 | 46 % | -4 % |
| NEU-LIVE +Mindest-Bein 5 % | 61% | 36% | +26.3 % | -9.4 % | 100 % | 234 | 17 | 47 % | -3 % |
| NEU-LIVE +groesstes Bein | 28% | 75% | +8.5 % | -12.2 % | 100 % | 106 | 3 | 8 % | -10 % |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | 28% | 75% | +8.5 % | -12.2 % | 100 % | 106 | 3 | 8 % | -10 % |
| NEU-LIVE +Bein in Handelsrichtung | 50% | 32% | +27.6 % | -9.9 % | 100 % | 229 | 16 | 59 % | 5 % |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | 39% | 31% | +32.3 % | -9.9 % | 100 % | 234 | 16 | 43 % | -15 % **<-- beste** |
| NEU-LIVE +Break-even im Plus | 50% | 30% | +15.2 % | -8.0 % | 100 % | 213 | 26 | 28 % | -3 % |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | 28% | 71% | +8.6 % | -11.1 % | 100 % | 161 | 17 | 10 % | -8 % |
| LIVE +Widerstand des Gegen-Beins | 61% | 37% | +22.6 % | -8.7 % | 100 % | 261 | 17 | 42 % | -1 % |
| LIVE +Widerstand statt Verkauf am letzten Hoch | 56% | 35% | +23.6 % | -9.0 % | 100 % | 219 | 4 | 46 % | 0 % |
| LIVE +Rest halten | 33% | 50% | +14.4 % | -9.4 % | 100 % | 77 | 4 | 25 % | -3 % |
| LIVE +Rest halten +Neustart mit Rest | 61% | 35% | +28.6 % | -9.4 % | 100 % | 230 | 16 | 52 % | -2 % |
| LIVE +Neustart mit Rest (ohne Halten) | 61% | 36% | +26.4 % | -9.4 % | 100 % | 233 | 15 | 48 % | -3 % |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | 39% | 22% | +15.5 % | -18.5 % | 100 % | 256 | 17 | 55 % | 21 % |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | 39% | 25% | +16.9 % | -19.0 % | 100 % | 231 | 17 | 61 % | 22 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | 56% | 32% | +24.3 % | -9.4 % | 100 % | 233 | 0 | 41 % | -5 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | 56% | 32% | +15.4 % | -9.4 % | 100 % | 213 | 0 | 31 % | 0 % |
| LIVE-heute +Neustart mit Rest | 56% | 32% | +24.4 % | -9.4 % | 100 % | 232 | 0 | 41 % | -5 % |
| LIVE-heute +Zonen nachziehen | 56% | 32% | +23.5 % | -9.4 % | 100 % | 238 | 0 | 42 % | -3 % |
| LIVE-heute +Trendfilter EMA200 | 11% | 20% | -5.7 % | -9.0 % | 100 % | 36 | 0 | -1 % | 10 % |
| LIVE-heute +Trendfilter EMA50 | 17% | 38% | +5.3 % | -10.6 % | 100 % | 110 | 0 | 5 % | -5 % |
| LIVE-heute +1D-Ebene grob (n=8) | 56% | 31% | -0.5 % | -22.9 % | 100 % | 236 | 0 | 49 % | 40 % |
| LIVE-heute +1D-Ebene fein (n=5, Gegenprobe zu E23) | 39% | 24% | +17.8 % | -18.6 % | 100 % | 261 | 0 | 59 % | 20 % |
| LIVE-heute +1D-Ebene sehr grob (n=12) | 61% | 31% | -0.0 % | -22.0 % | 100 % | 253 | 0 | 42 % | 34 % |
| LIVE-heute +Ampel klein bei unguenstig | 56% | 32% | +18.8 % | -7.6 % | 100 % | 238 | 0 | 38 % | 0 % |
| LIVE-heute +Ampel UMGEKEHRT (Gegenprobe) | 56% | 32% | +24.2 % | -9.3 % | 100 % | 238 | 0 | 43 % | -3 % |
| LIVE-heute +immer halbe Tranche (Nullhypothese) | 56% | 32% | +14.6 % | -5.3 % | 100 % | 238 | 0 | 28 % | -1 % |
| LIVE-heute +Rest halten +Neustart mit Rest | 56% | 31% | +23.5 % | -9.4 % | 100 % | 225 | 0 | 41 % | -3 % |
| Long+Short (Ref) | 33% | 38% | -3.9 % | -21.2 % | 100 % | 101 | 0 | -26 % | -18 % |

## Beste Kombination (nach Rendite): NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 %

- Kauf-Trigger getroffen: 2/7 (im Fenster) — 23.03.26, 27.03.26
- Kauf verpasst: 20.01.26, 29.01.26, 30.01.26, 31.01.26, 28.02.26
- Verkauf-Trigger getroffen: 5/11 (im Fenster) — 14.01.26, 17.03.26, 08.04.26, 17.04.26, 22.04.26
- Verkauf verpasst: 25.01.26, 02.02.26, 23.02.26, 28.02.26, 02.03.26, 14.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,231 €** (+32.3 %) · Buy&Hold im Fenster: -12.0 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,047 € · 87 Abschluesse, 59 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*LIVE-heute +Zonen nachziehen*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2026-01 | -156 € | -1.6 % | -156 € | -1.6 % |
| 2026-02 | -83 € | -0.8 % | -83 € | -0.8 % |
| 2026-03 | +580 € | +5.9 % | +524 € | +5.4 % |
| 2026-04 | +1,034 € | +10.0 % | +715 € | +7.0 % |
| 2026-05 | +495 € | +4.3 % | +310 € | +2.8 % |
| 2026-06 | -62 € | -0.5 % | -59 € | -0.5 % |
| 2026-07 | +345 € | +2.9 % | +328 € | +2.9 % |
| 2026-08 | +295 € | +2.4 % | +136 € | +1.2 % |
| 2026-09 | -100 € | -0.8 % | -94 € | -0.8 % |

Monate im Plus: **5 von 9** (live) gegen **5 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Was faengt die Engine von der Marktbewegung ein?

Dieselben Monate, jetzt neben der Bitcoin-Bewegung. **Aufwaerts-Beteiligung** = wie viel des Anstiegs die Engine in steigenden Monaten mitnimmt (hoch ist gut). **Abwaerts-Beteiligung** = wie viel des Rueckgangs sie in fallenden Monaten mitmacht (niedrig oder negativ ist gut).

| Monat | Bitcoin | Engine | davon eingefangen |
|---|---|---|---|
| 2026-01 | -13.8 % | -1.6 % | — |
| 2026-02 | -14.9 % | -0.8 % | — |
| 2026-03 | +2.0 % | +5.9 % | 303 % |
| 2026-04 | +11.8 % | +10.0 % | 85 % |
| 2026-05 | -3.5 % | +4.3 % | — |
| 2026-06 | -20.4 % | -0.5 % | — |
| 2026-07 | +7.3 % | +2.9 % | 40 % |
| 2026-08 | +24.9 % | +2.4 % | 10 % |
| 2026-09 | +2.3 % | -0.8 % | -35 % |

**Aufwaerts-Beteiligung: 42 %** — in den 5 steigenden Monaten legte Bitcoin zusammen +48.3 % zu, die Engine +20.5 %.

**Abwaerts-Beteiligung: -3 %** — in den 4 fallenden Monaten verlor Bitcoin zusammen -52.6 %, die Engine +1.4 %.

**So ist das zu lesen:** Die Gesamtrendite verrraet nicht, WO sie herkommt. Eine Strategie kann glaenzend aussehen, weil sie in fallenden Maerkten gewinnt, und trotzdem in einer Rally kaum mitkommen. Die Spalte 'davon eingefangen' zeigt das je Monat: Faellt sie mit steigender Bitcoin-Bewegung systematisch ab, nimmt die gestaffelte Gewinnmitnahme der Engine genau in den grossen Bewegungen die Position weg. Das ist Bauart, kein Fehler — aber es entscheidet, wofuer dieses Werkzeug taugt und wofuer nicht.

Naeherung: Monatsrenditen addiert statt verkettet (fuer diese Kennzahl ueblich). Wenige Monate — die Richtung ist belastbarer als die Prozentzahl.

## Was ist die Vorab-Information wert?

Die meisten Kauf- und Teilgewinn-Signale nennen ein **Fib-Level**, das die Kerze nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben. Wer erst auf die Telegram-Nachricht reagiert, findet diesen Preis oft nicht mehr am Markt. Beide Zeilen sind DIESELBEN Signale, nur anders abgerechnet.

| Abrechnung | Rendite | max. Rueckgang |
|---|---|---|
| **Limit-Order lag vorher dort** (zum genannten Level) | **+23.5 %** | -9.4 % |
| **erst nach der Nachricht reagiert** (zum Kerzenschluss) | **+23.4 %** | -9.2 % |
| Unterschied | **+0.1 Punkte** | |

Betroffen sind 66 von 238 Signalen — bei den uebrigen ist der genannte Preis ohnehin der Kerzenschluss (Stop, Restverkauf, Flush-Einstieg, Kaufleiter). Bei den betroffenen liegt der Kerzenschluss im Median **0.41 %** vom genannten Level entfernt.

**So ist das zu lesen:** Der Unterschied ist der Wert der Vorbereitung — also dessen, was die Vorschau-Nachricht und die Zonen-Linien im Chart ermoeglichen. Ist er klein, kann man entspannt auf die Signale reagieren. Ist er gross, entscheidet die vorab platzierte Order ueber einen erheblichen Teil des Ergebnisses.

**Die Zahl ist eine UNTERGRENZE.** Die Zeile 'erst nach der Nachricht' unterstellt, dass man genau zum Kerzenschluss handelt. Tatsaechlich laeuft die Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026), der reale Preis liegt also noch weiter weg. Ausserdem rechnet auch die obere Zeile ohne Schlupf und ohne Teilausfuehrungen.

## Echte Futures-Daten: was bringen sie?

Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes (2003 Punkte) — damit hat die Engine erstmals ein echtes Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.

Beide Zeilen: Variante *LIVE-heute +Zonen nachziehen*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied sind die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD (Stand bisher) | 56% | 33% | +23.8 % | -9.4 % | 243 |
| **mit echtem Futures-CVD** | 56% | 32% | **+23.5 %** | -9.4 % | 238 |

**5 Signale Unterschied** — die echten Daten erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das hilft, sagt die Rendite-Spalte.

## Aggregiertes Spot-CVD: was bringt es?

Bis E37 kam JEDE Zahl der Engine von einer einzigen Boerse. Das Kuerzel `.A` in den Coinalyze-Symbolen heisst Binance, nicht 'aggregiert' — der Code behauptete das Gegenteil, von E9.1 bis zum 19.09.2026. Furkan aggregiert dagegen ausdruecklich ueber mehrere Boersen.

Hier nur der Spot-Teil: 3 Maerkte (Binance, Bybit, Coinbase — OKX hat bei Coinalyze keinen Spot), 2002 vollstaendige Punkte, 2 ausgelassen (ein Zeitpunkt zaehlt nur, wenn ihn alle Boersen haben — sonst saehe eine Teilsumme aus wie ein Einbruch des Spot-Flows).

Alle Zeilen: Variante *LIVE-heute +Zonen nachziehen*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied ist die Herkunft des Spot-CVD.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| heute (nur Binance) | 56% | 32% | +23.5 % | -9.4 % | 238 |
| **aggregiert, groesster Markt je Boerse** | 56% | 31% | **+20.9 %** | -8.2 % | 233 |
| **aggregiert, alle Dollar-Maerkte** | 56% | 30% | **+21.3 %** | -8.2 % | 218 |

**Die Signalzahl aendert sich** — die Muster feuern an anderen Stellen, sobald mehr als eine Boerse zaehlt. Ob das hilft, sagt die Rendite-Spalte; ob es Zufall war, die Fensterhalbierung weiter unten.

**Einheiten, damit es niemand spaeter vermischt:** Die heutige Zeile rechnet in Dollar (Quote-Volumen der Binance-Kerzen), die aggregierten in BTC (Basiswert, wie das Futures-CVD). In `classify_pattern` geht beides nur als relative Aenderung ein, die Einheit kuerzt sich also heraus — summiert werden duerfen die Reihen trotzdem nie.

## Aggregierte Derivate-Daten: was bringen sie?

Open Interest, Liquidationen und Futures-CVD stehen **direkt** in den Bedingungen aller fuenf Muster — ein OI-Wipeout von 5 %, eine Liquidations-Kaskade, Futures-CVD gegen Spot. Das Spot-CVD (Abschnitt darueber) geht dagegen nur ueber zwei Steigungsvergleiche ein. Wenn Aggregation irgendwo wirkt, dann hier.

Perp-Maerkte: Binance (BTCUSD_PERP.A), Bybit (BTCUSD.6), OKX (BTCUSD_PERP.3), Hyperliquid (BTC.H). OI 1502 Punkte, Liquidationen 1469, Futures-CVD 2001.

**Einheiten:** OI und Liquidationen kommen in USD zurueck (`convert_to_usd`) und sind ueber Boersen hinweg summierbar. Das Futures-CVD dagegen kommt in der Denominierung des jeweiligen Marktes — deshalb werden dafuer nur Maerkte derselben Einheit zusammengerechnet. Ausgeschlossen: BTC.H.

Alle Zeilen: Variante *LIVE-heute +Zonen nachziehen*, dieselben Kerzen, derselbe Zeitraum. Der Unterschied sind allein die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| heute (nur Binance) | 56% | 32% | +23.5 % | -9.4 % | 238 |
| **+OI aggregiert** | 56% | 32% | **+24.6 %** | -9.4 % | 230 |
| **+OI +Liquidationen aggregiert** | 61% | 33% | **+23.3 %** | -9.4 % | 228 |
| **+alle drei aggregiert** | 61% | 35% | **+23.2 %** | -9.4 % | 217 |

**Die Signalzahl aendert sich** — mehrere Boersen fuehren zu anderen Entscheidungen. Ob das hilft, sagt die Rendite-Spalte.

## Furkans eigene Termine gegen die Engine

Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche Kurse, gleiche Gebuehr (0.1 %/Order), 10.000 € Start, offene Position am Ende zum Schlusskurs bewertet.

**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide Fenster zusammen ergeben ein faires Bild.**

Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein Teil seiner Verkaufstage Stops waren, also volle Ausstiege.

| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |
|---|---|---|---|---|---|---|
| **kurz** (Engine hat alle Daten)<br><sub>12.01.2026–22.04.2026</sub> | **-8.8 % bis -1.8 %** | -6.8 % | -15.6 % | **+14.3 %** | -9.4 % | -14.4 % |
| **lang** (Furkans volle Abfolge)<br><sub>25.09.2025–22.04.2026</sub> | **-23.7 % bis -6.1 %** | -19.7 % | -30.1 % | **+18.1 %** | -9.4 % | -30.5 % |

Im langen Fenster handelte Furkan an 20 Kauf- und 23 Verkaufstagen.

**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in beiden darueber, ist die Richtung „mehr wie Furkan werden" die falsche und der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, entscheidet keines von beiden.

**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag erlebt hat.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 60 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 60 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 12.01.2026–18.05.2026 · Haelfte 2: 18.05.2026–20.09.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +4.3 % | 57. | +4.9 % | 19. |
| +Kaufleiter | +9.1 % | 54. | +5.2 % | 18. |
| +Flush core | +22.0 % | 14. | -2.2 % | 45. |
| LIVE: nur Long +Kaufleiter +Flush core | +26.3 % | 1. | -1.9 % | 43. |
| +Kaufleiter +Bed.Stop | +5.9 % | 56. | +6.6 % | 9. |
| LIVE +Rest-Freigabe | +21.4 % | 16. | -4.1 % | 55. |
| LIVE +Stop nachziehen | +25.0 % | 3. | -2.2 % | 46. |
| LIVE +Stop nachziehen +Rest-Freigabe | +21.4 % | 17. | -3.6 % | 54. |
| LIVE +Stop +Liq-Kaskade | +19.8 % | 21. | -3.1 % | 52. |
| LIVE +Stop +Liq-Zonen | +18.3 % | 30. | -3.0 % | 51. |
| LIVE +Stop +Liq beides | +18.4 % | 27. | -3.0 % | 50. |
| MEINE Einstellung ohne Flush | +13.1 % | 49. | +2.8 % | 29. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +24.7 % | 4. | -0.9 % | 37. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +22.2 % | 11. | -1.1 % | 40. |
| LIVE +Stop +Verkauf am letzten Hoch | +22.5 % | 8. | -2.4 % | 49. |
| LIVE +Stop +Verkauf am schwachen Hoch | +22.3 % | 10. | -2.0 % | 44. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +16.0 % | 39. | -1.4 % | 42. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +13.2 % | 48. | -1.2 % | 41. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +23.6 % | 5. | -2.2 % | 47. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +25.5 % | 2. | -0.6 % | 36. |
| LIVE +Stop +Sperre 48 h nach Stop | +22.1 % | 12. | +3.1 % | 27. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +20.9 % | 18. | +4.7 % | 21. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +14.7 % | 45. | +4.7 % | 22. |
| LIVE +Stop +alle vier neuen Hebel | +17.3 % | 33. | -1.0 % | 38. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +19.9 % | 20. | +7.9 % | 4. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +23.2 % | 6. | +4.4 % | 24. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +22.1 % | 13. | +7.0 % | 7. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +18.3 % | 29. | +4.6 % | 23. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +16.6 % | 35. | +4.2 % | 25. |
| NEU-LIVE +kein Gegengeschaeft je Kerze | +19.1 % | 25. | +6.3 % | 12. |
| NEU-LIVE +Ziele festhalten | +22.5 % | 9. | +5.5 % | 17. |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | +20.2 % | 19. | +4.8 % | 20. |
| NEU-LIVE +Mindest-Bein 5 % | +19.6 % | 22. | +5.6 % | 16. |
| NEU-LIVE +groesstes Bein | +15.5 % | 41. | -6.1 % | 57. |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | +15.5 % | 42. | -6.1 % | 58. |
| NEU-LIVE +Bein in Handelsrichtung | +19.2 % | 24. | +7.0 % | 6. |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | +22.6 % | 7. | +7.9 % | 5. |
| NEU-LIVE +Break-even im Plus | +12.3 % | 52. | +2.5 % | 30. |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | +14.1 % | 46. | -4.8 % | 56. |
| LIVE +Widerstand des Gegen-Beins | +15.4 % | 43. | +6.3 % | 11. |
| LIVE +Widerstand statt Verkauf am letzten Hoch | +16.2 % | 38. | +6.4 % | 10. |
| LIVE +Rest halten | +3.3 % | 58. | +10.7 % | 1. |
| LIVE +Rest halten +Neustart mit Rest | +16.2 % | 37. | +10.6 % | 2. |
| LIVE +Neustart mit Rest (ohne Halten) | +19.6 % | 23. | +5.7 % | 14. |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | +18.4 % | 28. | -2.3 % | 48. |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | +17.1 % | 34. | -0.0 % | 34. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | +17.7 % | 31. | +5.6 % | 15. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | +12.7 % | 51. | +2.5 % | 31. |
| LIVE-heute +Neustart mit Rest | +17.7 % | 32. | +5.7 % | 13. |
| LIVE-heute +Zonen nachziehen | +18.7 % | 26. | +4.0 % | 26. |
| LIVE-heute +Trendfilter EMA200 | -5.1 % | 60. | -0.6 % | 35. |
| LIVE-heute +Trendfilter EMA50 | +6.3 % | 55. | -1.0 % | 39. |
| LIVE-heute +1D-Ebene grob (n=8) | +12.7 % | 50. | -11.7 % | 59. |
| LIVE-heute +1D-Ebene fein (n=5, Gegenprobe zu E23) | +21.8 % | 15. | -3.2 % | 53. |
| LIVE-heute +1D-Ebene sehr grob (n=12) | +15.0 % | 44. | -12.7 % | 60. |
| LIVE-heute +Ampel klein bei unguenstig | +16.3 % | 36. | +2.2 % | 32. |
| LIVE-heute +Ampel UMGEKEHRT (Gegenprobe) | +15.9 % | 40. | +6.7 % | 8. |
| LIVE-heute +immer halbe Tranche (Nullhypothese) | +11.3 % | 53. | +2.9 % | 28. |
| LIVE-heute +Rest halten +Neustart mit Rest | +13.8 % | 47. | +8.5 % | 3. |
| Long+Short (Ref) | -4.3 % | 59. | +0.5 % | 33. |

**In BEIDEN Haelften unter den besten 5:** keine einzige Variante

**Wie viel davon waere blosser Zufall?** Bei 60 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.4** Varianten. Gemessen: **0**. Das ist nicht mehr als der Zufall ohnehin liefert — die Rangfolge oben ist damit KEIN Beleg. Dann nur den groben Hebeln trauen (Richtung, Kaufleiter, Flush) und die Feinheiten weglassen.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1504 OI-Punkte, 1505 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 %' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.