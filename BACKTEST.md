# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 20.11.2025-29.07.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2123 4h-Kerzen geladen · Stand: 2026-07-29 16:08 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 29.07.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation. **max. Rueckgang** = groesster Einbruch vom jeweiligen Hoch (Drawdown) — je naeher an 0, desto ruhiger der Verlauf. **Einsatz** = wie viel des Kapitals je Position hoechstens investiert wird (100 % = keine Reserve, 60 % = 40 % Pulver bleibt trocken; Furkan-Update Juli 2026). Recall = Aehnlichkeit zu Furkans Terminen IM Fenster, KEIN Gewinn.

**Lesehilfe zu den Namen:** `LIVE` ist die Abkuerzung fuer *nur Long + Kaufleiter + Flush core* — der Flush steckt also drin. Jede Zeile, die mit `LIVE +…` beginnt, baut darauf auf. Die Zeile *+Kaufleiter* ist dagegen OHNE Flush.

| Variante | Recall | Praez. | Rendite | max. Rueckgang | Einsatz | Signale |
|---|---|---|---|---|---|---|
| nur Long (Basis) | 43% | 42% | +14.4 % | -5.5 % | 100 % | 102 |
| +Kaufleiter | 43% | 41% | +23.3 % | -6.3 % | 100 % | 124 |
| +Flush core | 46% | 32% | +28.1 % | -12.1 % | 100 % | 175 |
| LIVE: nur Long +Kaufleiter +Flush core | 46% | 32% | +36.8 % | -12.7 % | 100 % | 201 |
| +Kaufleiter +Bed.Stop | 43% | 40% | +21.3 % | -7.0 % | 100 % | 133 |
| LIVE +Rest-Freigabe | 50% | 35% | +30.5 % | -13.0 % | 100 % | 206 |
| LIVE +Stop nachziehen | 50% | 33% | +36.0 % | -12.3 % | 100 % | 207 |
| LIVE +Stop nachziehen +Rest-Freigabe | 50% | 35% | +31.1 % | -12.6 % | 100 % | 208 |
| LIVE +Stop +Liq-Kaskade | 54% | 31% | +25.6 % | -11.5 % | 100 % | 254 |
| LIVE +Stop +Liq-Zonen | 57% | 33% | +25.8 % | -11.3 % | 100 % | 283 |
| LIVE +Stop +Liq beides | 57% | 33% | +25.4 % | -11.2 % | 100 % | 285 |
| MEINE Einstellung ohne Flush | 54% | 46% | +28.6 % | -6.9 % | 100 % | 164 |
| LIVE +Stop +Liq-Konfluenz aufstocken | 50% | 33% | +41.9 % | -12.3 % | 100 % | 251 |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 43% | 30% | +27.9 % | -13.0 % | 100 % | 187 |
| LIVE +Stop +Verkauf am letzten Hoch | 57% | 33% | +31.7 % | -11.9 % | 100 % | 261 |
| LIVE +Stop +Verkauf am schwachen Hoch | 54% | 32% | +31.6 % | -11.7 % | 100 % | 251 |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 50% | 33% | +21.7 % | -8.2 % | 60 % | 207 |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 50% | 33% | +17.9 % | -6.8 % | 50 % | 207 |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 50% | 33% | +33.8 % | -12.3 % | 100 % | 204 |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 46% | 30% | +31.3 % | -12.1 % | 100 % | 201 |
| LIVE +Stop +Sperre 48 h nach Stop | 46% | 35% | +37.7 % | -8.5 % | 100 % | 180 |
| LIVE +Stop +Mindest-Stopabstand 2 % | 43% | 38% | +37.1 % | -7.0 % | 100 % | 145 |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 43% | 41% | +30.1 % | -7.0 % | 100 % | 136 |
| LIVE +Stop +alle vier neuen Hebel | 32% | 34% | +18.5 % | -6.9 % | 100 % | 113 |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 43% | 39% | +44.6 % | -6.9 % | 100 % | 176 |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 46% | 33% | +45.3 % | -9.3 % | 100 % | 216 |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 50% | 38% | +46.0 % | -7.5 % | 100 % | 214 **<-- beste** |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 50% | 37% | +38.0 % | -7.8 % | 100 % | 226 |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 50% | 37% | +34.7 % | -7.9 % | 100 % | 264 |
| Long+Short (Ref) | 36% | 57% | +1.1 % | -11.9 % | 100 % | 82 |

## Beste Kombination (nach Rendite): NEU-LIVE +Verkauf unter dem letzten Hoch

- Kauf-Trigger getroffen: 5/11 (im Fenster) — 06.01.26, 08.01.26, 28.02.26, 23.03.26, 27.03.26
- Kauf verpasst: 20.11.25, 21.11.25, 20.01.26, 29.01.26, 30.01.26, 31.01.26
- Verkauf-Trigger getroffen: 9/17 (im Fenster) — 06.01.26, 14.01.26, 25.01.26, 28.02.26, 02.03.26, 17.03.26, 08.04.26, 17.04.26, 22.04.26
- Verkauf verpasst: 23.11.25, 28.11.25, 02.12.25, 03.12.25, 17.12.25, 02.02.26, 23.02.26, 14.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **14,601 €** (+46.0 %) · Buy&Hold im Fenster: -26.2 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +4,601 € · 93 Abschluesse, 67 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*NEU-LIVE +Verkauf unter dem letzten Hoch*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2025-11 | +0 € | +0.0 % | +0 € | +0.0 % |
| 2025-12 | +121 € | +1.2 % | +121 € | +1.2 % |
| 2026-01 | +1,231 € | +12.2 % | +1,231 € | +12.2 % |
| 2026-02 | +591 € | +5.2 % | -94 € | -0.8 % |
| 2026-03 | +728 € | +6.1 % | +58 € | +0.5 % |
| 2026-04 | +1,554 € | +12.3 % | +1,018 € | +9.0 % |
| 2026-05 | -691 € | -4.9 % | -418 € | -3.4 % |
| 2026-06 | -31 € | -0.2 % | -28 € | -0.2 % |
| 2026-07 | +1,098 € | +8.1 % | +967 € | +8.1 % |

Monate im Plus: **6 von 9** (live) gegen **5 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Was ist die Vorab-Information wert?

Die meisten Kauf- und Teilgewinn-Signale nennen ein **Fib-Level**, das die Kerze nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben. Wer erst auf die Telegram-Nachricht reagiert, findet diesen Preis oft nicht mehr am Markt. Beide Zeilen sind DIESELBEN Signale, nur anders abgerechnet.

| Abrechnung | Rendite | max. Rueckgang |
|---|---|---|
| **Limit-Order lag vorher dort** (zum genannten Level) | **+46.0 %** | -7.5 % |
| **erst nach der Nachricht reagiert** (zum Kerzenschluss) | **+45.3 %** | -7.5 % |
| Unterschied | **+0.7 Punkte** | |

Betroffen sind 61 von 214 Signalen — bei den uebrigen ist der genannte Preis ohnehin der Kerzenschluss (Stop, Restverkauf, Flush-Einstieg, Kaufleiter). Bei den betroffenen liegt der Kerzenschluss im Median **0.35 %** vom genannten Level entfernt.

**So ist das zu lesen:** Der Unterschied ist der Wert der Vorbereitung — also dessen, was die Vorschau-Nachricht und die Zonen-Linien im Chart ermoeglichen. Ist er klein, kann man entspannt auf die Signale reagieren. Ist er gross, entscheidet die vorab platzierte Order ueber einen erheblichen Teil des Ergebnisses.

**Die Zahl ist eine UNTERGRENZE.** Die Zeile 'erst nach der Nachricht' unterstellt, dass man genau zum Kerzenschluss handelt. Tatsaechlich laeuft die Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026), der reale Preis liegt also noch weiter weg. Ausserdem rechnet auch die obere Zeile ohne Schlupf und ohne Teilausfuehrungen.

## Echte Futures-Daten: was bringen sie?

Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes (2005 Punkte) — damit hat die Engine erstmals ein echtes Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.

Beide Zeilen: Variante *NEU-LIVE +Verkauf unter dem letzten Hoch*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied sind die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD (Stand bisher) | 50% | 39% | +44.8 % | -7.5 % | 222 |
| **mit echtem Futures-CVD** | 50% | 38% | **+46.0 %** | -7.5 % | 214 |

**8 Signale Unterschied** — die echten Daten erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das hilft, sagt die Rendite-Spalte.

## Furkans eigene Termine gegen die Engine

Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche Kurse, gleiche Gebuehr (0.1 %/Order), 10.000 € Start, offene Position am Ende zum Schlusskurs bewertet.

**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide Fenster zusammen ergeben ein faires Bild.**

Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein Teil seiner Verkaufstage Stops waren, also volle Ausstiege.

| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |
|---|---|---|---|---|---|---|
| **kurz** (Engine hat alle Daten)<br><sub>20.11.2025–22.04.2026</sub> | **-9.2 % bis +0.5 %** | -7.3 % | -19.9 % | **+42.2 %** | -5.1 % | -9.8 % |
| **lang** (Furkans volle Abfolge)<br><sub>25.09.2025–22.04.2026</sub> | **-23.7 % bis -6.1 %** | -19.7 % | -30.1 % | **+39.6 %** | -5.1 % | -30.5 % |

Im langen Fenster handelte Furkan an 20 Kauf- und 23 Verkaufstagen.

**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in beiden darueber, ist die Richtung „mehr wie Furkan werden" die falsche und der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, entscheidet keines von beiden.

**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag erlebt hat.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 30 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 30 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 20.11.2025–26.03.2026 · Haelfte 2: 26.03.2026–29.07.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +6.2 % | 30. | +9.8 % | 20. |
| +Kaufleiter | +11.4 % | 27. | +12.8 % | 9. |
| +Flush core | +17.2 % | 19. | +10.2 % | 19. |
| LIVE: nur Long +Kaufleiter +Flush core | +23.1 % | 8. | +11.9 % | 12. |
| +Kaufleiter +Bed.Stop | +9.1 % | 29. | +14.2 % | 6. |
| LIVE +Rest-Freigabe | +20.3 % | 13. | +10.6 % | 17. |
| LIVE +Stop nachziehen | +23.2 % | 7. | +12.4 % | 10. |
| LIVE +Stop nachziehen +Rest-Freigabe | +20.3 % | 14. | +11.1 % | 15. |
| LIVE +Stop +Liq-Kaskade | +17.1 % | 20. | +9.3 % | 23. |
| LIVE +Stop +Liq-Zonen | +19.3 % | 15. | +6.8 % | 29. |
| LIVE +Stop +Liq beides | +19.0 % | 17. | +6.8 % | 28. |
| MEINE Einstellung ohne Flush | +16.3 % | 22. | +13.6 % | 8. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +28.4 % | 4. | +14.0 % | 7. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +17.2 % | 18. | +9.0 % | 25. |
| LIVE +Stop +Verkauf am letzten Hoch | +20.6 % | 12. | +10.9 % | 16. |
| LIVE +Stop +Verkauf am schwachen Hoch | +20.9 % | 10. | +10.5 % | 18. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +13.2 % | 24. | +8.8 % | 26. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +10.9 % | 28. | +7.3 % | 27. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +21.2 % | 9. | +12.4 % | 11. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +16.9 % | 21. | +14.4 % | 5. |
| LIVE +Stop +Sperre 48 h nach Stop | +16.1 % | 23. | +18.6 % | 2. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +25.4 % | 6. | +11.4 % | 13. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +19.0 % | 16. | +11.4 % | 14. |
| LIVE +Stop +alle vier neuen Hebel | +13.2 % | 25. | +6.7 % | 30. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +30.0 % | 2. | +14.8 % | 4. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +20.8 % | 11. | +20.3 % | 1. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +30.4 % | 1. | +15.1 % | 3. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +29.1 % | 3. | +9.7 % | 21. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +26.0 % | 5. | +9.2 % | 24. |
| Long+Short (Ref) | +11.7 % | 26. | +9.7 % | 22. |

**In BEIDEN Haelften unter den besten 5:** LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz, NEU-LIVE +Verkauf unter dem letzten Hoch

**Wie viel davon waere blosser Zufall?** Bei 30 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.8** Varianten. Gemessen: **2**. Das ist deutlich mehr als der Zufall liefert — die Rangfolge oben traegt.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1506 OI-Punkte, 1507 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'NEU-LIVE +Verkauf unter dem letzten Hoch' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.