# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 19.11.2025-28.07.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2115 4h-Kerzen geladen · Stand: 2026-07-28 08:08 UTC

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
| LIVE +Rest-Freigabe | 57% | 35% | +27.2 % | -13.0 % | 100 % | 217 |
| LIVE +Stop nachziehen | 57% | 34% | +32.2 % | -12.3 % | 100 % | 212 |
| LIVE +Stop nachziehen +Rest-Freigabe | 57% | 35% | +27.8 % | -12.6 % | 100 % | 219 |
| LIVE +Stop +Liq-Kaskade | 61% | 32% | +22.4 % | -11.5 % | 100 % | 259 |
| LIVE +Stop +Liq-Zonen | 64% | 33% | +23.3 % | -11.3 % | 100 % | 288 |
| LIVE +Stop +Liq beides | 64% | 33% | +23.0 % | -11.2 % | 100 % | 290 |
| MEINE Einstellung ohne Flush | 50% | 41% | +19.9 % | -6.3 % | 100 % | 137 |
| LIVE +Stop +Liq-Konfluenz aufstocken | 57% | 33% | +37.0 % | -12.3 % | 100 % | 255 **<-- beste** |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 50% | 37% | +28.8 % | -13.0 % | 100 % | 188 |
| LIVE +Stop +Verkauf am letzten Hoch | 64% | 34% | +28.3 % | -11.9 % | 100 % | 264 |
| LIVE +Stop +Verkauf am schwachen Hoch | 61% | 33% | +28.0 % | -11.7 % | 100 % | 256 |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 57% | 34% | +19.7 % | -8.2 % | 60 % | 212 |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 57% | 34% | +16.3 % | -6.8 % | 50 % | 212 |
| Long+Short (Ref) | 43% | 57% | -1.0 % | -11.9 % | 100 % | 88 |

## Beste Kombination (nach Rendite): LIVE +Stop +Liq-Konfluenz aufstocken

- Kauf-Trigger getroffen: 7/11 (im Fenster) — 20.11.25, 21.11.25, 06.01.26, 08.01.26, 28.02.26, 23.03.26, 27.03.26
- Kauf verpasst: 20.01.26, 29.01.26, 30.01.26, 31.01.26
- Verkauf-Trigger getroffen: 9/17 (im Fenster) — 06.01.26, 14.01.26, 25.01.26, 23.02.26, 02.03.26, 17.03.26, 08.04.26, 14.04.26, 22.04.26
- Verkauf verpasst: 23.11.25, 28.11.25, 02.12.25, 03.12.25, 17.12.25, 02.02.26, 28.02.26, 17.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,697 €** (+37.0 %) · Buy&Hold im Fenster: -30.6 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,697 € · 88 Abschluesse, 67 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*LIVE +Stop nachziehen*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2025-11 | -228 € | -2.3 % | -228 € | -2.3 % |
| 2025-12 | +39 € | +0.4 % | +39 € | +0.4 % |
| 2026-01 | +1,098 € | +11.2 % | +979 € | +10.0 % |
| 2026-02 | +186 € | +1.7 % | -141 € | -1.3 % |
| 2026-03 | +842 € | +7.6 % | +147 € | +1.4 % |
| 2026-04 | +1,710 € | +14.3 % | +1,053 € | +9.8 % |
| 2026-05 | -528 € | -3.9 % | -418 € | -3.5 % |
| 2026-06 | -885 € | -6.7 % | -328 € | -2.9 % |
| 2026-07 | +982 € | +8.0 % | +891 € | +8.0 % |

Monate im Plus: **6 von 9** (live) gegen **5 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 19 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 19 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 19.11.2025–25.03.2026 · Haelfte 2: 25.03.2026–28.07.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +4.0 % | 19. | +9.4 % | 13. |
| +Kaufleiter | +9.1 % | 15. | +12.3 % | 3. |
| +Flush core | +15.0 % | 11. | +9.7 % | 12. |
| LIVE: nur Long +Kaufleiter +Flush core | +20.8 % | 2. | +11.4 % | 6. |
| +Kaufleiter +Bed.Stop | +6.8 % | 18. | +13.7 % | 1. |
| LIVE +Rest-Freigabe | +17.8 % | 7. | +10.2 % | 9. |
| LIVE +Stop nachziehen | +20.6 % | 3. | +11.9 % | 5. |
| LIVE +Stop nachziehen +Rest-Freigabe | +17.8 % | 8. | +10.8 % | 7. |
| LIVE +Stop +Liq-Kaskade | +14.8 % | 12. | +8.9 % | 14. |
| LIVE +Stop +Liq-Zonen | +17.4 % | 9. | +6.6 % | 19. |
| LIVE +Stop +Liq beides | +17.0 % | 10. | +6.6 % | 18. |
| MEINE Einstellung ohne Flush | +9.1 % | 16. | +12.3 % | 4. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +24.9 % | 1. | +13.4 % | 2. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +18.6 % | 4. | +8.5 % | 15. |
| LIVE +Stop +Verkauf am letzten Hoch | +18.0 % | 6. | +10.5 % | 8. |
| LIVE +Stop +Verkauf am schwachen Hoch | +18.3 % | 5. | +10.0 % | 10. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +11.7 % | 13. | +8.5 % | 16. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +9.7 % | 14. | +7.1 % | 17. |
| Long+Short (Ref) | +8.2 % | 17. | +9.9 % | 11. |

**In BEIDEN Haelften unter den besten 5:** LIVE +Stop +Liq-Konfluenz aufstocken, LIVE +Stop nachziehen

Bewertung: 2 von 5 Varianten halten sich in beiden Haelften oben. Die Varianten, die in beiden Haelften oben stehen, sind die einzigen, auf die man sich stuetzen sollte. Alles, was nur in einer Haelfte glaenzt, ist Zufall.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1504 OI-Punkte, 1504 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'LIVE +Stop +Liq-Konfluenz aufstocken' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.