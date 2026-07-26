# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 17.11.2025-26.07.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2106 4h-Kerzen geladen · Stand: 2026-07-26 21:09 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 26.07.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation; Long €/Short € = realisierter Gewinn/Verlust getrennt nach Richtung. Recall = Aehnlichkeit zu Furkans Terminen IM Fenster.

| Variante | Recall | Praez. | Rendite | Long € | Short € | Signale |
|---|---|---|---|---|---|---|
| nur Long (Basis) | 48% | 43% | +11.2 % | +1,084 | +0 | 114 |
| +Kaufleiter | 48% | 41% | +19.7 % | +1,920 | +0 | 136 |
| +Flush core | 52% | 32% | +24.6 % | +2,418 | +0 | 180 |
| LIVE: nur Long +Kaufleiter +Flush core | 52% | 32% | +32.8 % | +3,229 | +0 | 206 **<-- beste** |
| +Kaufleiter +Bed.Stop | 48% | 40% | +17.7 % | +1,721 | +0 | 145 |
| LIVE +Rest-Freigabe | 55% | 35% | +28.3 % | +2,818 | +0 | 217 |
| Long+Short (Ref) | 41% | 58% | +0.9 % | +325 | -203 | 87 |

## Beste Kombination (nach Rendite): LIVE: nur Long +Kaufleiter +Flush core

- Kauf-Trigger getroffen: 6/12 (im Fenster) — 20.11.25, 21.11.25, 06.01.26, 08.01.26, 28.02.26, 23.03.26
- Kauf verpasst: 17.11.25, 20.01.26, 29.01.26, 30.01.26, 31.01.26, 27.03.26
- Verkauf-Trigger getroffen: 9/17 (im Fenster) — 06.01.26, 14.01.26, 25.01.26, 23.02.26, 02.03.26, 17.03.26, 08.04.26, 14.04.26, 22.04.26
- Verkauf verpasst: 23.11.25, 28.11.25, 02.12.25, 03.12.25, 17.12.25, 02.02.26, 28.02.26, 17.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,284 €** (+32.8 %) · Buy&Hold im Fenster: -29.9 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,229 € · 86 Abschluesse, 67 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1507 OI-Punkte, 1508 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'LIVE: nur Long +Kaufleiter +Flush core' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.