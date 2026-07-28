# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 19.11.2025-28.07.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2116 4h-Kerzen geladen · Stand: 2026-07-28 14:11 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 28.07.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation. **max. Rueckgang** = groesster Einbruch vom jeweiligen Hoch (Drawdown) — je naeher an 0, desto ruhiger der Verlauf. **Einsatz** = wie viel des Kapitals je Position hoechstens investiert wird (100 % = keine Reserve, 60 % = 40 % Pulver bleibt trocken; Furkan-Update Juli 2026). Recall = Aehnlichkeit zu Furkans Terminen IM Fenster, KEIN Gewinn.

**Lesehilfe zu den Namen:** `LIVE` ist die Abkuerzung fuer *nur Long + Kaufleiter + Flush core* — der Flush steckt also drin. Jede Zeile, die mit `LIVE +…` beginnt, baut darauf auf. Die Zeile *+Kaufleiter* ist dagegen OHNE Flush.

| Variante | Recall | Praez. | Rendite | max. Rueckgang | Einsatz | Signale |
|---|---|---|---|---|---|---|
| nur Long (Basis) | 50% | 43% | +11.4 % | -5.5 % | 100 % | 115 |
| +Kaufleiter | 50% | 41% | +19.9 % | -6.3 % | 100 % | 137 |
| +Flush core | 54% | 32% | +24.8 % | -12.1 % | 100 % | 181 |
| LIVE: nur Long +Kaufleiter +Flush core | 54% | 32% | +33.1 % | -12.7 % | 100 % | 207 |
| +Kaufleiter +Bed.Stop | 50% | 40% | +17.9 % | -7.0 % | 100 % | 146 |
| LIVE +Rest-Freigabe | 57% | 35% | +26.9 % | -13.0 % | 100 % | 217 |
| LIVE +Stop nachziehen | 57% | 34% | +32.2 % | -12.3 % | 100 % | 212 |
| LIVE +Stop nachziehen +Rest-Freigabe | 57% | 35% | +27.5 % | -12.6 % | 100 % | 219 |
| LIVE +Stop +Liq-Kaskade | 61% | 32% | +22.4 % | -11.5 % | 100 % | 259 |
| LIVE +Stop +Liq-Zonen | 64% | 33% | +23.3 % | -11.3 % | 100 % | 288 |
| LIVE +Stop +Liq beides | 64% | 33% | +23.0 % | -11.2 % | 100 % | 290 |
| MEINE Einstellung ohne Flush | 61% | 45% | +23.9 % | -6.9 % | 100 % | 177 |
| LIVE +Stop +Liq-Konfluenz aufstocken | 57% | 33% | +37.0 % | -12.3 % | 100 % | 255 |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 50% | 37% | +28.8 % | -13.0 % | 100 % | 188 |
| LIVE +Stop +Verkauf am letzten Hoch | 64% | 34% | +28.3 % | -11.9 % | 100 % | 264 |
| LIVE +Stop +Verkauf am schwachen Hoch | 61% | 33% | +28.0 % | -11.7 % | 100 % | 256 |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 57% | 34% | +19.7 % | -8.2 % | 60 % | 212 |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 57% | 34% | +16.3 % | -6.8 % | 50 % | 212 |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 57% | 34% | +30.0 % | -12.3 % | 100 % | 209 |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 54% | 31% | +27.6 % | -12.1 % | 100 % | 202 |
| LIVE +Stop +Sperre 48 h nach Stop | 54% | 35% | +33.9 % | -8.5 % | 100 % | 185 |
| LIVE +Stop +Mindest-Stopabstand 2 % | 50% | 40% | +33.0 % | -7.0 % | 100 % | 156 |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 50% | 41% | +26.4 % | -7.0 % | 100 % | 146 |
| LIVE +Stop +alle vier neuen Hebel | 39% | 35% | +14.3 % | -6.9 % | 100 % | 117 |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 50% | 40% | +39.1 % | -6.9 % | 100 % | 187 |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 54% | 33% | +40.3 % | -9.3 % | 100 % | 220 |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 57% | 39% | +40.3 % | -7.5 % | 100 % | 225 **<-- beste** |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 57% | 38% | +33.8 % | -7.8 % | 100 % | 240 |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 57% | 38% | +30.7 % | -7.9 % | 100 % | 278 |
| Long+Short (Ref) | 43% | 57% | -0.7 % | -11.9 % | 100 % | 89 |

## Beste Kombination (nach Rendite): NEU-LIVE +Verkauf unter dem letzten Hoch

- Kauf-Trigger getroffen: 7/11 (im Fenster) — 20.11.25, 21.11.25, 06.01.26, 08.01.26, 28.02.26, 23.03.26, 27.03.26
- Kauf verpasst: 20.01.26, 29.01.26, 30.01.26, 31.01.26
- Verkauf-Trigger getroffen: 9/17 (im Fenster) — 06.01.26, 14.01.26, 25.01.26, 28.02.26, 02.03.26, 17.03.26, 08.04.26, 17.04.26, 22.04.26
- Verkauf verpasst: 23.11.25, 28.11.25, 02.12.25, 03.12.25, 17.12.25, 02.02.26, 23.02.26, 14.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **14,034 €** (+40.3 %) · Buy&Hold im Fenster: -31.0 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +4,034 € · 94 Abschluesse, 67 im Gewinn
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
| 2026-03 | +674 € | +5.8 % | +56 € | +0.5 % |
| 2026-04 | +1,503 € | +12.3 % | +987 € | +9.0 % |
| 2026-05 | -668 € | -4.9 % | -406 € | -3.4 % |
| 2026-06 | -30 € | -0.2 % | -27 € | -0.2 % |
| 2026-07 | +979 € | +7.5 % | +864 € | +7.5 % |

Monate im Plus: **6 von 9** (live) gegen **5 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 30 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 30 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 19.11.2025–25.03.2026 · Haelfte 2: 25.03.2026–28.07.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +4.1 % | 30. | +9.4 % | 21. |
| +Kaufleiter | +9.2 % | 27. | +12.3 % | 9. |
| +Flush core | +15.1 % | 19. | +9.7 % | 20. |
| LIVE: nur Long +Kaufleiter +Flush core | +20.9 % | 7. | +11.4 % | 12. |
| +Kaufleiter +Bed.Stop | +6.9 % | 29. | +13.7 % | 6. |
| LIVE +Rest-Freigabe | +17.9 % | 13. | +10.0 % | 19. |
| LIVE +Stop nachziehen | +20.7 % | 8. | +11.9 % | 10. |
| LIVE +Stop nachziehen +Rest-Freigabe | +17.9 % | 14. | +10.5 % | 16. |
| LIVE +Stop +Liq-Kaskade | +14.8 % | 20. | +8.9 % | 23. |
| LIVE +Stop +Liq-Zonen | +17.4 % | 15. | +6.6 % | 29. |
| LIVE +Stop +Liq beides | +17.1 % | 17. | +6.6 % | 28. |
| MEINE Einstellung ohne Flush | +13.0 % | 23. | +12.9 % | 8. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +25.0 % | 4. | +13.4 % | 7. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +18.6 % | 10. | +8.5 % | 25. |
| LIVE +Stop +Verkauf am letzten Hoch | +18.1 % | 12. | +10.5 % | 15. |
| LIVE +Stop +Verkauf am schwachen Hoch | +18.4 % | 11. | +10.0 % | 18. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +11.8 % | 24. | +8.5 % | 26. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +9.8 % | 26. | +7.1 % | 27. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +18.8 % | 9. | +11.9 % | 11. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +14.5 % | 21. | +13.9 % | 5. |
| LIVE +Stop +Sperre 48 h nach Stop | +13.3 % | 22. | +18.1 % | 2. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +22.6 % | 6. | +10.9 % | 13. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +16.5 % | 18. | +10.9 % | 14. |
| LIVE +Stop +alle vier neuen Hebel | +10.8 % | 25. | +5.4 % | 30. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +26.3 % | 2. | +14.0 % | 4. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +17.3 % | 16. | +19.6 % | 1. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +26.4 % | 1. | +14.4 % | 3. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +26.1 % | 3. | +9.0 % | 22. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +22.9 % | 5. | +8.8 % | 24. |
| Long+Short (Ref) | +7.9 % | 28. | +10.3 % | 17. |

**In BEIDEN Haelften unter den besten 5:** LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz, NEU-LIVE +Verkauf unter dem letzten Hoch

**Wie viel davon waere blosser Zufall?** Bei 30 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.8** Varianten. Gemessen: **2**. Das ist deutlich mehr als der Zufall liefert — die Rangfolge oben traegt.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1505 OI-Punkte, 1506 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'NEU-LIVE +Verkauf unter dem letzten Hoch' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.