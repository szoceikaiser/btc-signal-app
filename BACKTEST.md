# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 18.11.2025-27.07.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2111 4h-Kerzen geladen · Stand: 2026-07-27 17:29 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 27.07.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation; Long €/Short € = realisierter Gewinn/Verlust getrennt nach Richtung. Recall = Aehnlichkeit zu Furkans Terminen IM Fenster.

| Variante | Recall | Praez. | Rendite | Long € | Short € | Signale |
|---|---|---|---|---|---|---|
| nur Long (Basis) | 50% | 43% | +11.4 % | +1,138 | +0 | 115 |
| +Kaufleiter | 50% | 41% | +19.9 % | +1,994 | +0 | 137 |
| +Flush core | 54% | 32% | +24.8 % | +2,479 | +0 | 181 |
| LIVE: nur Long +Kaufleiter +Flush core | 54% | 32% | +33.1 % | +3,311 | +0 | 207 **<-- beste** |
| +Kaufleiter +Bed.Stop | 50% | 40% | +17.9 % | +1,794 | +0 | 146 |
| LIVE +Rest-Freigabe | 57% | 35% | +28.6 % | +2,818 | +0 | 217 |
| LIVE +Stop nachziehen | 57% | 34% | +30.0 % | +2,953 | +0 | 208 |
| LIVE +Stop nachziehen +Rest-Freigabe | 57% | 35% | +27.7 % | +2,725 | +0 | 208 |
| LIVE +Stop +Liq-Kaskade | 57% | 30% | +22.8 % | +2,230 | +0 | 237 |
| LIVE +Stop +Liq-Zonen | 61% | 34% | +28.0 % | +2,750 | +0 | 238 |
| LIVE +Stop +Liq beides | 61% | 34% | +28.0 % | +2,750 | +0 | 239 |
| Long+Short (Ref) | 43% | 58% | +1.7 % | +374 | -203 | 90 |

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

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1506 OI-Punkte, 1507 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'LIVE: nur Long +Kaufleiter +Flush core' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.