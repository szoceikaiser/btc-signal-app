# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 19.11.2025-28.07.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2116 4h-Kerzen geladen · Stand: 2026-07-28 15:01 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 28.07.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation. **max. Rueckgang** = groesster Einbruch vom jeweiligen Hoch (Drawdown) — je naeher an 0, desto ruhiger der Verlauf. **Einsatz** = wie viel des Kapitals je Position hoechstens investiert wird (100 % = keine Reserve, 60 % = 40 % Pulver bleibt trocken; Furkan-Update Juli 2026). Recall = Aehnlichkeit zu Furkans Terminen IM Fenster, KEIN Gewinn.

**Lesehilfe zu den Namen:** `LIVE` ist die Abkuerzung fuer *nur Long + Kaufleiter + Flush core* — der Flush steckt also drin. Jede Zeile, die mit `LIVE +…` beginnt, baut darauf auf. Die Zeile *+Kaufleiter* ist dagegen OHNE Flush.

| Variante | Recall | Praez. | Rendite | max. Rueckgang | Einsatz | Signale |
|---|---|---|---|---|---|---|
| nur Long (Basis) | 50% | 43% | +11.8 % | -5.5 % | 100 % | 103 |
| +Kaufleiter | 50% | 41% | +20.5 % | -6.3 % | 100 % | 125 |
| +Flush core | 54% | 33% | +25.1 % | -12.1 % | 100 % | 172 |
| LIVE: nur Long +Kaufleiter +Flush core | 54% | 33% | +33.6 % | -12.7 % | 100 % | 198 |
| +Kaufleiter +Bed.Stop | 50% | 40% | +18.5 % | -7.0 % | 100 % | 134 |
| LIVE +Rest-Freigabe | 57% | 35% | +27.1 % | -13.0 % | 100 % | 207 |
| LIVE +Stop nachziehen | 57% | 34% | +32.9 % | -12.3 % | 100 % | 203 |
| LIVE +Stop nachziehen +Rest-Freigabe | 57% | 35% | +27.7 % | -12.6 % | 100 % | 209 |
| LIVE +Stop +Liq-Kaskade | 61% | 32% | +22.8 % | -11.5 % | 100 % | 250 |
| LIVE +Stop +Liq-Zonen | 64% | 33% | +23.8 % | -11.3 % | 100 % | 279 |
| LIVE +Stop +Liq beides | 64% | 33% | +23.4 % | -11.2 % | 100 % | 281 |
| MEINE Einstellung ohne Flush | 61% | 45% | +24.6 % | -6.9 % | 100 % | 165 |
| LIVE +Stop +Liq-Konfluenz aufstocken | 57% | 33% | +38.1 % | -12.3 % | 100 % | 246 |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 50% | 36% | +29.7 % | -13.0 % | 100 % | 177 |
| LIVE +Stop +Verkauf am letzten Hoch | 64% | 34% | +28.8 % | -11.9 % | 100 % | 255 |
| LIVE +Stop +Verkauf am schwachen Hoch | 61% | 33% | +28.6 % | -11.7 % | 100 % | 247 |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 57% | 34% | +20.1 % | -8.2 % | 60 % | 203 |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 57% | 34% | +16.6 % | -6.8 % | 50 % | 203 |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 57% | 34% | +30.7 % | -12.3 % | 100 % | 200 |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 54% | 31% | +28.3 % | -12.1 % | 100 % | 199 |
| LIVE +Stop +Sperre 48 h nach Stop | 54% | 35% | +34.6 % | -8.5 % | 100 % | 176 |
| LIVE +Stop +Mindest-Stopabstand 2 % | 50% | 39% | +34.0 % | -7.0 % | 100 % | 146 |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 50% | 41% | +27.1 % | -7.0 % | 100 % | 137 |
| LIVE +Stop +alle vier neuen Hebel | 39% | 35% | +15.2 % | -6.9 % | 100 % | 116 |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 50% | 38% | +40.5 % | -6.9 % | 100 % | 177 |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 54% | 33% | +41.4 % | -9.3 % | 100 % | 211 |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 57% | 38% | +41.5 % | -7.5 % | 100 % | 215 **<-- beste** |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 57% | 37% | +34.7 % | -7.8 % | 100 % | 230 |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 57% | 37% | +31.2 % | -7.9 % | 100 % | 268 |
| Long+Short (Ref) | 43% | 57% | -0.9 % | -11.9 % | 100 % | 85 |

## Beste Kombination (nach Rendite): NEU-LIVE +Verkauf unter dem letzten Hoch

- Kauf-Trigger getroffen: 7/11 (im Fenster) — 20.11.25, 21.11.25, 06.01.26, 08.01.26, 28.02.26, 23.03.26, 27.03.26
- Kauf verpasst: 20.01.26, 29.01.26, 30.01.26, 31.01.26
- Verkauf-Trigger getroffen: 9/17 (im Fenster) — 06.01.26, 14.01.26, 25.01.26, 28.02.26, 02.03.26, 17.03.26, 08.04.26, 17.04.26, 22.04.26
- Verkauf verpasst: 23.11.25, 28.11.25, 02.12.25, 03.12.25, 17.12.25, 02.02.26, 23.02.26, 14.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **14,153 €** (+41.5 %) · Buy&Hold im Fenster: -30.7 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +4,153 € · 94 Abschluesse, 67 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*NEU-LIVE +Verkauf unter dem letzten Hoch*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2025-11 | -228 € | -2.3 % | -228 € | -2.3 % |
| 2025-12 | +78 € | +0.8 % | +78 € | +0.8 % |
| 2026-01 | +1,154 € | +11.7 % | +1,154 € | +11.7 % |
| 2026-02 | +573 € | +5.2 % | -91 € | -0.8 % |
| 2026-03 | +706 € | +6.1 % | +56 € | +0.5 % |
| 2026-04 | +1,506 € | +12.3 % | +987 € | +9.0 % |
| 2026-05 | -670 € | -4.9 % | -406 € | -3.4 % |
| 2026-06 | -30 € | -0.2 % | -27 € | -0.2 % |
| 2026-07 | +1,064 € | +8.1 % | +937 € | +8.1 % |

Monate im Plus: **6 von 9** (live) gegen **5 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Echte Futures-Daten: was bringen sie?

Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes (2004 Punkte) — damit hat die Engine erstmals ein echtes Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.

Beide Zeilen: Variante *NEU-LIVE +Verkauf unter dem letzten Hoch*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied sind die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD (Stand bisher) | 57% | 39% | +40.3 % | -7.5 % | 225 |
| **mit echtem Futures-CVD** | 57% | 38% | **+41.5 %** | -7.5 % | 215 |

**10 Signale Unterschied** — die echten Daten erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das hilft, sagt die Rendite-Spalte.

## Furkans eigene Termine gegen die Engine

Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche Kurse, gleiche Gebuehr (0.1 %/Order), 10.000 € Start, offene Position am Ende zum Schlusskurs bewertet.

**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide Fenster zusammen ergeben ein faires Bild.**

Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein Teil seiner Verkaufstage Stops waren, also volle Ausstiege.

| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |
|---|---|---|---|---|---|---|
| **kurz** (Engine hat alle Daten)<br><sub>19.11.2025–22.04.2026</sub> | **-9.2 % bis +0.5 %** | -7.3 % | -19.9 % | **+37.9 %** | -5.1 % | -14.6 % |
| **lang** (Furkans volle Abfolge)<br><sub>25.09.2025–22.04.2026</sub> | **-23.7 % bis -6.1 %** | -19.7 % | -30.1 % | **+38.5 %** | -5.2 % | -30.5 % |

Im langen Fenster handelte Furkan an 20 Kauf- und 23 Verkaufstagen.

**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in beiden darueber, ist die Richtung „mehr wie Furkan werden" die falsche und der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, entscheidet keines von beiden.

**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag erlebt hat.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 30 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 30 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 19.11.2025–25.03.2026 · Haelfte 2: 25.03.2026–28.07.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +4.1 % | 30. | +9.8 % | 21. |
| +Kaufleiter | +9.2 % | 27. | +12.8 % | 9. |
| +Flush core | +15.0 % | 19. | +10.1 % | 19. |
| LIVE: nur Long +Kaufleiter +Flush core | +20.8 % | 7. | +11.9 % | 12. |
| +Kaufleiter +Bed.Stop | +6.9 % | 29. | +14.2 % | 6. |
| LIVE +Rest-Freigabe | +17.9 % | 13. | +10.2 % | 18. |
| LIVE +Stop nachziehen | +20.8 % | 8. | +12.4 % | 10. |
| LIVE +Stop nachziehen +Rest-Freigabe | +17.9 % | 14. | +10.7 % | 16. |
| LIVE +Stop +Liq-Kaskade | +14.8 % | 20. | +9.3 % | 23. |
| LIVE +Stop +Liq-Zonen | +17.4 % | 15. | +6.9 % | 29. |
| LIVE +Stop +Liq beides | +17.1 % | 17. | +7.0 % | 28. |
| MEINE Einstellung ohne Flush | +13.0 % | 23. | +13.6 % | 8. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +25.1 % | 4. | +14.2 % | 7. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +18.9 % | 9. | +9.1 % | 25. |
| LIVE +Stop +Verkauf am letzten Hoch | +18.1 % | 12. | +11.0 % | 15. |
| LIVE +Stop +Verkauf am schwachen Hoch | +18.4 % | 11. | +10.6 % | 17. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +11.8 % | 24. | +8.8 % | 26. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +9.8 % | 26. | +7.3 % | 27. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +18.8 % | 10. | +12.4 % | 11. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +14.6 % | 21. | +14.5 % | 5. |
| LIVE +Stop +Sperre 48 h nach Stop | +13.4 % | 22. | +18.7 % | 2. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +22.9 % | 5. | +11.4 % | 13. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +16.6 % | 18. | +11.4 % | 14. |
| LIVE +Stop +alle vier neuen Hebel | +10.9 % | 25. | +6.2 % | 30. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +26.7 % | 2. | +14.8 % | 4. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +17.4 % | 16. | +20.5 % | 1. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +26.7 % | 1. | +15.1 % | 3. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +26.2 % | 3. | +9.7 % | 22. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +22.9 % | 6. | +9.2 % | 24. |
| Long+Short (Ref) | +7.9 % | 28. | +10.1 % | 20. |

**In BEIDEN Haelften unter den besten 5:** LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz, NEU-LIVE +Verkauf unter dem letzten Hoch

**Wie viel davon waere blosser Zufall?** Bei 30 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.8** Varianten. Gemessen: **2**. Das ist deutlich mehr als der Zufall liefert — die Rangfolge oben traegt.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1505 OI-Punkte, 1506 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'NEU-LIVE +Verkauf unter dem letzten Hoch' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.