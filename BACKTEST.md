# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 18.11.2025-27.07.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2111 4h-Kerzen geladen · Stand: 2026-07-27 19:21 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 27.07.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation. **max. Rueckgang** = groesster Einbruch vom jeweiligen Hoch (Drawdown) — je naeher an 0, desto ruhiger der Verlauf. **Einsatz** = wie viel des Kapitals je Position hoechstens investiert wird (100 % = keine Reserve, 60 % = 40 % Pulver bleibt trocken; Furkan-Update Juli 2026). Recall = Aehnlichkeit zu Furkans Terminen IM Fenster, KEIN Gewinn.

**Lesehilfe zu den Namen:** `LIVE` ist die Abkuerzung fuer *nur Long + Kaufleiter + Flush core* — der Flush steckt also drin. Jede Zeile, die mit `LIVE +…` beginnt, baut darauf auf. Die Zeile *+Kaufleiter* ist dagegen OHNE Flush.

| Variante | Recall | Praez. | Rendite | max. Rueckgang | Einsatz | Signale |
|---|---|---|---|---|---|---|
| nur Long (Basis) | 50% | 43% | +11.4 % | -5.5 % | 100 % | 115 |
| +Kaufleiter | 50% | 41% | +19.9 % | -6.3 % | 100 % | 137 |
| +Flush core | 54% | 32% | +24.8 % | -12.1 % | 100 % | 181 |
| LIVE: nur Long +Kaufleiter +Flush core | 54% | 32% | +33.1 % | -12.7 % | 100 % | 207 **<-- beste** |
| +Kaufleiter +Bed.Stop | 50% | 40% | +17.9 % | -7.0 % | 100 % | 146 |
| LIVE +Rest-Freigabe | 57% | 35% | +28.6 % | -13.0 % | 100 % | 217 |
| LIVE +Stop nachziehen | 57% | 34% | +30.0 % | -11.5 % | 100 % | 208 |
| LIVE +Stop nachziehen +Rest-Freigabe | 57% | 35% | +27.7 % | -11.8 % | 100 % | 208 |
| LIVE +Stop +Liq-Kaskade | 57% | 30% | +22.7 % | -11.1 % | 100 % | 237 |
| LIVE +Stop +Liq-Zonen | 61% | 34% | +27.9 % | -10.8 % | 100 % | 238 |
| LIVE +Stop +Liq beides | 61% | 34% | +27.9 % | -10.8 % | 100 % | 239 |
| MEINE Einstellung ohne Flush | 50% | 39% | +19.4 % | -6.2 % | 100 % | 132 |
| LIVE +Stop +Liq-Konfluenz aufstocken | 57% | 32% | +29.9 % | -11.8 % | 100 % | 227 |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 50% | 36% | +22.8 % | -12.2 % | 100 % | 178 |
| LIVE +Stop +Verkauf am letzten Hoch | 61% | 34% | +27.2 % | -12.0 % | 100 % | 229 |
| LIVE +Stop +Verkauf am schwachen Hoch | 61% | 33% | +27.4 % | -11.9 % | 100 % | 227 |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 57% | 34% | +17.9 % | -7.7 % | 60 % | 208 |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 57% | 34% | +14.8 % | -6.4 % | 50 % | 208 |
| Long+Short (Ref) | 43% | 58% | +1.7 % | -11.9 % | 100 % | 90 |

## Beste Kombination (nach Rendite): LIVE: nur Long +Kaufleiter +Flush core

- Kauf-Trigger getroffen: 6/11 (im Fenster) — 20.11.25, 21.11.25, 06.01.26, 08.01.26, 28.02.26, 23.03.26
- Kauf verpasst: 20.01.26, 29.01.26, 30.01.26, 31.01.26, 27.03.26
- Verkauf-Trigger getroffen: 9/17 (im Fenster) — 06.01.26, 14.01.26, 25.01.26, 23.02.26, 02.03.26, 17.03.26, 08.04.26, 14.04.26, 22.04.26
- Verkauf verpasst: 23.11.25, 28.11.25, 02.12.25, 03.12.25, 17.12.25, 02.02.26, 28.02.26, 17.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,311 €** (+33.1 %) · Buy&Hold im Fenster: -30.1 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,311 € · 87 Abschluesse, 68 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*LIVE +Stop nachziehen*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2025-11 | -228 € | -2.3 % | -228 € | -2.3 % |
| 2025-12 | +39 € | +0.4 % | +39 € | +0.4 % |
| 2026-01 | +1,213 € | +12.4 % | +979 € | +10.0 % |
| 2026-02 | -276 € | -2.5 % | -141 € | -1.3 % |
| 2026-03 | +1,021 € | +9.5 % | +216 € | +2.0 % |
| 2026-04 | +1,687 € | +14.3 % | +1,060 € | +9.8 % |
| 2026-05 | -414 € | -3.1 % | -421 € | -3.5 % |
| 2026-06 | -871 € | -6.7 % | -322 € | -2.8 % |
| 2026-07 | +824 € | +6.8 % | +757 € | +6.8 % |

Monate im Plus: **5 von 9** (live) gegen **5 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 19 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 19 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 18.11.2025–24.03.2026 · Haelfte 2: 24.03.2026–27.07.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +3.6 % | 19. | +7.5 % | 15. |
| +Kaufleiter | +8.7 % | 16. | +10.3 % | 2. |
| +Flush core | +15.3 % | 10. | +7.8 % | 13. |
| LIVE: nur Long +Kaufleiter +Flush core | +21.1 % | 2. | +9.5 % | 5. |
| +Kaufleiter +Bed.Stop | +6.4 % | 18. | +10.8 % | 1. |
| LIVE +Rest-Freigabe | +17.4 % | 7. | +9.6 % | 3. |
| LIVE +Stop nachziehen | +19.0 % | 3. | +9.6 % | 4. |
| LIVE +Stop nachziehen +Rest-Freigabe | +17.4 % | 8. | +9.2 % | 7. |
| LIVE +Stop +Liq-Kaskade | +14.1 % | 12. | +8.0 % | 12. |
| LIVE +Stop +Liq-Zonen | +18.8 % | 4. | +8.9 % | 10. |
| LIVE +Stop +Liq beides | +18.8 % | 5. | +8.9 % | 11. |
| MEINE Einstellung ohne Flush | +9.9 % | 15. | +9.0 % | 8. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +21.2 % | 1. | +7.2 % | 16. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +15.1 % | 11. | +7.6 % | 14. |
| LIVE +Stop +Verkauf am letzten Hoch | +17.6 % | 6. | +8.9 % | 9. |
| LIVE +Stop +Verkauf am schwachen Hoch | +17.4 % | 9. | +9.3 % | 6. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +10.3 % | 14. | +7.1 % | 17. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +8.6 % | 17. | +5.9 % | 19. |
| Long+Short (Ref) | +12.2 % | 13. | +6.2 % | 18. |

**In BEIDEN Haelften unter den besten 5:** LIVE +Stop nachziehen, LIVE: nur Long +Kaufleiter +Flush core

Bewertung: 2 von 5 Varianten halten sich in beiden Haelften oben. Die Varianten, die in beiden Haelften oben stehen, sind die einzigen, auf die man sich stuetzen sollte. Alles, was nur in einer Haelfte glaenzt, ist Zufall.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1506 OI-Punkte, 1507 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'LIVE: nur Long +Kaufleiter +Flush core' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.