# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 15.11.2025-01.05.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 1585 4h-Kerzen geladen · Stand: 2026-07-24 19:37 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation; Long €/Short € = realisierter Gewinn/Verlust getrennt nach Richtung. Recall = Aehnlichkeit zu Furkans Terminen IM Fenster.

| Variante | Recall | Praez. | Rendite | Long € | Short € | Signale |
|---|---|---|---|---|---|---|
| nur Long (Basis) | 52% | 43% | +9.8 % | +977 | +0 | 74 |
| +Kaufleiter | 52% | 41% | +18.0 % | +1,802 | +0 | 88 |
| +Flush core | 55% | 30% | +30.5 % | +2,924 | +0 | 127 |
| +Flush core +Kaufleiter | 55% | 30% | +38.9 % | +3,755 | +0 | 145 **<-- beste** |
| +Kaufleiter +Bed.Stop | 52% | 41% | +14.6 % | +1,462 | +0 | 93 |
| Long+Short (Analyse) | 45% | 58% | +2.8 % | +315 | +762 | 37 |

## Beste Kombination (nach Rendite): +Flush core +Kaufleiter

- Kauf-Trigger getroffen: 7/12 (im Fenster) — 17.11.25, 20.11.25, 21.11.25, 06.01.26, 08.01.26, 28.02.26, 23.03.26
- Kauf verpasst: 20.01.26, 29.01.26, 30.01.26, 31.01.26, 27.03.26
- Verkauf-Trigger getroffen: 9/17 (im Fenster) — 06.01.26, 14.01.26, 25.01.26, 23.02.26, 02.03.26, 17.03.26, 08.04.26, 14.04.26, 22.04.26
- Verkauf verpasst: 23.11.25, 28.11.25, 02.12.25, 03.12.25, 17.12.25, 02.02.26, 28.02.26, 17.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,892 €** (+38.9 %) · Buy&Hold im Fenster: -19.3 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,755 € · 61 Abschluesse, 47 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 998 OI-Punkte, 999 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante '+Flush core +Kaufleiter' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.