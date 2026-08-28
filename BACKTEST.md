# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 20.12.2025-28.08.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2300 4h-Kerzen geladen · Stand: 2026-08-28 07:03 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 28.08.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation. **max. Rueckgang** = groesster Einbruch vom jeweiligen Hoch (Drawdown) — je naeher an 0, desto ruhiger der Verlauf. **Einsatz** = wie viel des Kapitals je Position hoechstens investiert wird (100 % = keine Reserve, 60 % = 40 % Pulver bleibt trocken; Furkan-Update Juli 2026). Recall = Aehnlichkeit zu Furkans Terminen IM Fenster, KEIN Gewinn.

**Lesehilfe zu den Namen:** `LIVE` ist die Abkuerzung fuer *nur Long + Kaufleiter + Flush core* — der Flush steckt also drin. Jede Zeile, die mit `LIVE +…` beginnt, baut darauf auf. Die Zeile *+Kaufleiter* ist dagegen OHNE Flush.

| Variante | Recall | Praez. | Rendite | max. Rueckgang | Einsatz | Signale |
|---|---|---|---|---|---|---|
| nur Long (Basis) | 52% | 41% | +11.0 % | -5.5 % | 100 % | 100 |
| +Kaufleiter | 52% | 40% | +18.0 % | -6.3 % | 100 % | 122 |
| +Flush core | 57% | 31% | +22.2 % | -12.1 % | 100 % | 178 |
| LIVE: nur Long +Kaufleiter +Flush core | 57% | 31% | +28.7 % | -12.7 % | 100 % | 204 |
| +Kaufleiter +Bed.Stop | 52% | 39% | +16.1 % | -7.0 % | 100 % | 133 |
| LIVE +Rest-Freigabe | 62% | 34% | +22.2 % | -13.0 % | 100 % | 210 |
| LIVE +Stop nachziehen | 62% | 33% | +28.5 % | -12.3 % | 100 % | 209 |
| LIVE +Stop nachziehen +Rest-Freigabe | 62% | 34% | +22.7 % | -12.6 % | 100 % | 212 |
| LIVE +Stop +Liq-Kaskade | 67% | 32% | +19.2 % | -11.5 % | 100 % | 257 |
| LIVE +Stop +Liq-Zonen | 76% | 33% | +19.2 % | -11.3 % | 100 % | 292 |
| LIVE +Stop +Liq beides | 76% | 33% | +18.9 % | -11.2 % | 100 % | 294 |
| MEINE Einstellung ohne Flush | 71% | 43% | +28.1 % | -7.5 % | 100 % | 219 |
| LIVE +Stop +Liq-Konfluenz aufstocken | 62% | 33% | +31.5 % | -12.3 % | 100 % | 258 |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 57% | 38% | +27.6 % | -13.0 % | 100 % | 186 |
| LIVE +Stop +Verkauf am letzten Hoch | 71% | 33% | +24.8 % | -11.9 % | 100 % | 269 |
| LIVE +Stop +Verkauf am schwachen Hoch | 67% | 32% | +24.6 % | -11.7 % | 100 % | 256 |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 62% | 33% | +17.6 % | -8.2 % | 60 % | 209 |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 62% | 33% | +14.6 % | -6.8 % | 50 % | 209 |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 62% | 33% | +26.4 % | -12.3 % | 100 % | 206 |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 57% | 33% | +31.1 % | -12.1 % | 100 % | 198 |
| LIVE +Stop +Sperre 48 h nach Stop | 57% | 34% | +31.5 % | -8.5 % | 100 % | 180 |
| LIVE +Stop +Mindest-Stopabstand 2 % | 52% | 40% | +31.1 % | -7.0 % | 100 % | 133 |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 52% | 43% | +24.3 % | -7.0 % | 100 % | 124 |
| LIVE +Stop +alle vier neuen Hebel | 43% | 39% | +18.2 % | -6.9 % | 100 % | 112 |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 52% | 41% | +35.1 % | -6.9 % | 100 % | 164 |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 57% | 33% | +36.2 % | -9.3 % | 100 % | 221 |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 62% | 41% | +35.9 % | -7.5 % | 100 % | 202 |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 67% | 40% | +28.7 % | -7.8 % | 100 % | 214 |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 67% | 41% | +25.7 % | -7.9 % | 100 % | 252 |
| NEU-LIVE +kein Gegengeschaeft je Kerze | 57% | 37% | +31.8 % | -7.5 % | 100 % | 200 |
| NEU-LIVE +Ziele festhalten | 62% | 41% | +30.2 % | -7.5 % | 100 % | 209 |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | 57% | 37% | +34.4 % | -7.5 % | 100 % | 208 |
| NEU-LIVE +Mindest-Bein 5 % | 71% | 38% | +37.9 % | -6.9 % | 100 % | 241 |
| NEU-LIVE +groesstes Bein | 43% | 61% | +17.6 % | -7.3 % | 100 % | 103 |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | 43% | 61% | +17.6 % | -7.3 % | 100 % | 103 |
| NEU-LIVE +Bein in Handelsrichtung | 62% | 35% | +33.0 % | -8.9 % | 100 % | 238 |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | 52% | 33% | +38.4 % | -8.2 % | 100 % | 227 |
| NEU-LIVE +Break-even im Plus | 52% | 31% | +16.1 % | -5.3 % | 100 % | 214 |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | 33% | 57% | +7.0 % | -8.1 % | 100 % | 144 |
| LIVE +Widerstand des Gegen-Beins | 71% | 37% | +30.3 % | -6.2 % | 100 % | 271 |
| LIVE +Widerstand statt Verkauf am letzten Hoch | 67% | 37% | +32.9 % | -6.8 % | 100 % | 227 |
| LIVE +Rest halten | 33% | 45% | +18.9 % | -6.9 % | 100 % | 84 |
| LIVE +Rest halten +Neustart mit Rest | 71% | 38% | +39.3 % | -8.2 % | 100 % | 235 **<-- beste** |
| LIVE +Neustart mit Rest (ohne Halten) | 71% | 38% | +38.9 % | -6.9 % | 100 % | 239 |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | 52% | 28% | +23.4 % | -17.6 % | 100 % | 255 |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | 52% | 31% | +26.5 % | -17.0 % | 100 % | 231 |
| Long+Short (Ref) | 38% | 39% | -2.2 % | -11.9 % | 100 % | 96 |

## Beste Kombination (nach Rendite): LIVE +Rest halten +Neustart mit Rest

- Kauf-Trigger getroffen: 6/9 (im Fenster) — 06.01.26, 08.01.26, 20.01.26, 28.02.26, 23.03.26, 27.03.26
- Kauf verpasst: 29.01.26, 30.01.26, 31.01.26
- Verkauf-Trigger getroffen: 9/12 (im Fenster) — 06.01.26, 14.01.26, 23.02.26, 28.02.26, 02.03.26, 17.03.26, 08.04.26, 17.04.26, 22.04.26
- Verkauf verpasst: 25.01.26, 02.02.26, 14.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,929 €** (+39.3 %) · Buy&Hold im Fenster: -9.5 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,836 € · 92 Abschluesse, 70 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*NEU-LIVE +Mindest-Bein 5 %*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2025-12 | +92 € | +0.9 % | +92 € | +0.9 % |
| 2026-01 | +595 € | +5.9 % | +595 € | +5.9 % |
| 2026-02 | -88 € | -0.8 % | -88 € | -0.8 % |
| 2026-03 | +659 € | +6.2 % | +472 € | +4.5 % |
| 2026-04 | +1,332 € | +11.8 % | +950 € | +8.6 % |
| 2026-05 | +400 € | +3.2 % | +200 € | +1.7 % |
| 2026-06 | +88 € | +0.7 % | +83 € | +0.7 % |
| 2026-07 | +311 € | +2.4 % | +292 € | +2.4 % |
| 2026-08 | +397 € | +3.0 % | +216 € | +1.7 % |

Monate im Plus: **8 von 9** (live) gegen **8 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Was faengt die Engine von der Marktbewegung ein?

Dieselben Monate, jetzt neben der Bitcoin-Bewegung. **Aufwaerts-Beteiligung** = wie viel des Anstiegs die Engine in steigenden Monaten mitnimmt (hoch ist gut). **Abwaerts-Beteiligung** = wie viel des Rueckgangs sie in fallenden Monaten mitmacht (niedrig oder negativ ist gut).

| Monat | Bitcoin | Engine | davon eingefangen |
|---|---|---|---|
| 2025-12 | -0.8 % | +0.9 % | — |
| 2026-01 | -10.2 % | +5.9 % | — |
| 2026-02 | -14.9 % | -0.8 % | — |
| 2026-03 | +2.0 % | +6.2 % | 317 % |
| 2026-04 | +11.8 % | +11.8 % | 100 % |
| 2026-05 | -3.5 % | +3.2 % | — |
| 2026-06 | -20.4 % | +0.7 % | — |
| 2026-07 | +7.3 % | +2.4 % | 33 % |
| 2026-08 | +27.1 % | +3.0 % | 11 % |

**Aufwaerts-Beteiligung: 49 %** — in den 4 steigenden Monaten legte Bitcoin zusammen +48.1 % zu, die Engine +23.4 %.

**Abwaerts-Beteiligung: -20 %** — in den 5 fallenden Monaten verlor Bitcoin zusammen -49.8 %, die Engine +9.9 %.

**So ist das zu lesen:** Die Gesamtrendite verrraet nicht, WO sie herkommt. Eine Strategie kann glaenzend aussehen, weil sie in fallenden Maerkten gewinnt, und trotzdem in einer Rally kaum mitkommen. Die Spalte 'davon eingefangen' zeigt das je Monat: Faellt sie mit steigender Bitcoin-Bewegung systematisch ab, nimmt die gestaffelte Gewinnmitnahme der Engine genau in den grossen Bewegungen die Position weg. Das ist Bauart, kein Fehler — aber es entscheidet, wofuer dieses Werkzeug taugt und wofuer nicht.

Naeherung: Monatsrenditen addiert statt verkettet (fuer diese Kennzahl ueblich). Wenige Monate — die Richtung ist belastbarer als die Prozentzahl.

## Was ist die Vorab-Information wert?

Die meisten Kauf- und Teilgewinn-Signale nennen ein **Fib-Level**, das die Kerze nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben. Wer erst auf die Telegram-Nachricht reagiert, findet diesen Preis oft nicht mehr am Markt. Beide Zeilen sind DIESELBEN Signale, nur anders abgerechnet.

| Abrechnung | Rendite | max. Rueckgang |
|---|---|---|
| **Limit-Order lag vorher dort** (zum genannten Level) | **+37.9 %** | -6.9 % |
| **erst nach der Nachricht reagiert** (zum Kerzenschluss) | **+36.3 %** | -6.9 % |
| Unterschied | **+1.5 Punkte** | |

Betroffen sind 66 von 241 Signalen — bei den uebrigen ist der genannte Preis ohnehin der Kerzenschluss (Stop, Restverkauf, Flush-Einstieg, Kaufleiter). Bei den betroffenen liegt der Kerzenschluss im Median **0.42 %** vom genannten Level entfernt.

**So ist das zu lesen:** Der Unterschied ist der Wert der Vorbereitung — also dessen, was die Vorschau-Nachricht und die Zonen-Linien im Chart ermoeglichen. Ist er klein, kann man entspannt auf die Signale reagieren. Ist er gross, entscheidet die vorab platzierte Order ueber einen erheblichen Teil des Ergebnisses.

**Die Zahl ist eine UNTERGRENZE.** Die Zeile 'erst nach der Nachricht' unterstellt, dass man genau zum Kerzenschluss handelt. Tatsaechlich laeuft die Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026), der reale Preis liegt also noch weiter weg. Ausserdem rechnet auch die obere Zeile ohne Schlupf und ohne Teilausfuehrungen.

## Echte Futures-Daten: was bringen sie?

Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes (2002 Punkte) — damit hat die Engine erstmals ein echtes Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.

Beide Zeilen: Variante *NEU-LIVE +Mindest-Bein 5 %*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied sind die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD (Stand bisher) | 67% | 38% | +37.5 % | -6.9 % | 247 |
| **mit echtem Futures-CVD** | 71% | 38% | **+37.9 %** | -6.9 % | 241 |

**6 Signale Unterschied** — die echten Daten erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das hilft, sagt die Rendite-Spalte.

## Furkans eigene Termine gegen die Engine

Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche Kurse, gleiche Gebuehr (0.1 %/Order), 10.000 € Start, offene Position am Ende zum Schlusskurs bewertet.

**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide Fenster zusammen ergeben ein faires Bild.**

Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein Teil seiner Verkaufstage Stops waren, also volle Ausstiege.

| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |
|---|---|---|---|---|---|---|
| **kurz** (Engine hat alle Daten)<br><sub>20.12.2025–22.04.2026</sub> | **-12.1 % bis +0.2 %** | -9.3 % | -19.8 % | **+26.4 %** | -6.9 % | -11.5 % |
| **lang** (Furkans volle Abfolge)<br><sub>25.09.2025–22.04.2026</sub> | **-23.7 % bis -6.1 %** | -19.7 % | -30.1 % | **+32.2 %** | -6.9 % | -30.5 % |

Im langen Fenster handelte Furkan an 20 Kauf- und 23 Verkaufstagen.

**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in beiden darueber, ist die Richtung „mehr wie Furkan werden" die falsche und der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, entscheidet keines von beiden.

**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag erlebt hat.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 47 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 47 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 20.12.2025–25.04.2026 · Haelfte 2: 25.04.2026–28.08.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +9.4 % | 45. | +1.5 % | 18. |
| +Kaufleiter | +16.0 % | 41. | +1.7 % | 17. |
| +Flush core | +32.9 % | 12. | -8.0 % | 45. |
| LIVE: nur Long +Kaufleiter +Flush core | +39.5 % | 1. | -7.8 % | 42. |
| +Kaufleiter +Bed.Stop | +12.6 % | 43. | +3.1 % | 14. |
| LIVE +Rest-Freigabe | +34.7 % | 7. | -9.3 % | 47. |
| LIVE +Stop nachziehen | +38.1 % | 4. | -7.0 % | 39. |
| LIVE +Stop nachziehen +Rest-Freigabe | +34.7 % | 8. | -8.9 % | 46. |
| LIVE +Stop +Liq-Kaskade | +28.3 % | 22. | -7.1 % | 41. |
| LIVE +Stop +Liq-Zonen | +29.6 % | 18. | -8.0 % | 44. |
| LIVE +Stop +Liq beides | +29.2 % | 19. | -8.0 % | 43. |
| MEINE Einstellung ohne Flush | +20.7 % | 38. | +6.2 % | 8. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +38.4 % | 3. | -5.0 % | 33. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +36.2 % | 5. | -6.3 % | 36. |
| LIVE +Stop +Verkauf am letzten Hoch | +33.8 % | 10. | -6.7 % | 38. |
| LIVE +Stop +Verkauf am schwachen Hoch | +33.5 % | 11. | -6.7 % | 37. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +23.6 % | 32. | -4.8 % | 32. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +19.4 % | 40. | -4.0 % | 30. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +35.9 % | 6. | -7.0 % | 40. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +38.6 % | 2. | -5.4 % | 34. |
| LIVE +Stop +Sperre 48 h nach Stop | +32.5 % | 14. | -0.8 % | 25. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +31.5 % | 15. | -0.3 % | 22. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +24.8 % | 31. | -0.3 % | 23. |
| LIVE +Stop +alle vier neuen Hebel | +25.4 % | 30. | -5.8 % | 35. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +30.4 % | 17. | +3.5 % | 11. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +34.4 % | 9. | +1.4 % | 19. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +31.5 % | 16. | +3.4 % | 13. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +28.9 % | 20. | -0.1 % | 20. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +25.9 % | 29. | -0.1 % | 21. |
| NEU-LIVE +kein Gegengeschaeft je Kerze | +28.4 % | 21. | +2.7 % | 15. |
| NEU-LIVE +Ziele festhalten | +21.2 % | 37. | +4.1 % | 10. |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | +27.5 % | 23. | +3.4 % | 12. |
| NEU-LIVE +Mindest-Bein 5 % | +26.4 % | 27. | +9.1 % | 5. |
| NEU-LIVE +groesstes Bein | +21.4 % | 35. | -3.2 % | 27. |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | +21.4 % | 36. | -3.2 % | 28. |
| NEU-LIVE +Bein in Handelsrichtung | +26.6 % | 26. | +5.1 % | 9. |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | +26.9 % | 25. | +9.1 % | 6. |
| NEU-LIVE +Break-even im Plus | +13.3 % | 42. | +2.5 % | 16. |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | +11.4 % | 44. | -3.9 % | 29. |
| LIVE +Widerstand des Gegen-Beins | +19.5 % | 39. | +9.0 % | 7. |
| LIVE +Widerstand statt Verkauf am letzten Hoch | +21.5 % | 34. | +9.3 % | 4. |
| LIVE +Rest halten | +7.4 % | 46. | +14.1 % | 2. |
| LIVE +Rest halten +Neustart mit Rest | +22.2 % | 33. | +14.6 % | 1. |
| LIVE +Neustart mit Rest (ohne Halten) | +26.4 % | 28. | +9.9 % | 3. |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | +27.0 % | 24. | -2.9 % | 26. |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | +32.8 % | 13. | -4.7 % | 31. |
| Long+Short (Ref) | +1.8 % | 47. | -0.6 % | 24. |

**In BEIDEN Haelften unter den besten 5:** keine einzige Variante

**Wie viel davon waere blosser Zufall?** Bei 47 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.5** Varianten. Gemessen: **0**. Das ist nicht mehr als der Zufall ohnehin liefert — die Rangfolge oben ist damit KEIN Beleg. Dann nur den groben Hebeln trauen (Richtung, Kaufleiter, Flush) und die Feinheiten weglassen.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1503 OI-Punkte, 1504 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'LIVE +Rest halten +Neustart mit Rest' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.