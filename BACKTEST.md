# Backtest-Bericht (E4b): Engine vs. Kaisers notierte Furkan-Trigger

Zeitraum: 01.09.2025-30.04.2026 (4h-Kerzen, 1585 Stueck) · Stand: 2026-07-23 05:24 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

## Parameter-Vergleich

| pivot_n | k_atr | Recall (Kaisers Trigger getroffen) | Praezision (Engine-Signale nahe Kaisers Terminen) | Signale |
|---|---|---|---|---|
| 3 | 2.0 | 34% | 26% | 74 |
| 3 | 3.0 | 23% | 17% | 60 |
| 4 | 2.0 | 30% | 33% | 53 |
| 4 | 3.0 | 23% | 18% | 59 |
| 5 | 2.0 | 36% | 47% | 43 **<-- beste** |
| 5 | 3.0 | 20% | 28% | 46 |
| 6 | 2.0 | 23% | 32% | 33 |
| 6 | 3.0 | 11% | 17% | 33 |

## Beste Kombination: pivot_n=5, k_atr=2.0

- Kauf-Trigger getroffen: 8/20 — 21.10.25, 29.10.25, 30.10.25, 17.11.25, 20.11.25, 21.11.25, 06.01.26, 08.01.26
- Kauf verpasst: 25.09.25, 10.10.25, 27.10.25, 28.10.25, 04.11.25, 20.01.26, 29.01.26, 30.01.26, 31.01.26, 28.02.26, 23.03.26, 27.03.26
- Verkauf-Trigger getroffen: 8/24 — 16.10.25, 04.11.25, 12.11.25, 23.11.25, 28.11.25, 14.01.26, 25.01.26, 17.03.26
- Verkauf verpasst: 25.09.25, 02.10.25, 03.10.25, 10.10.25, 02.12.25, 03.12.25, 17.12.25, 06.01.26, 02.02.26, 23.02.26, 28.02.26, 02.03.26, 08.04.26, 14.04.26, 17.04.26, 22.04.26
- Engine-Signal-Tage gesamt: 15 Kauf / 21 Verkauf

## P&L-Simulation (beste Kombination)

Start 10.000 € -> **9,016 €** (-9.8 %) · Buy&Hold im Zeitraum: -28.4 % · 21 Verkaufs-Vorgaenge, davon 12 im Gewinn · Gebuehr 0.1 % je Order, kein Hebel.

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in dieser P&L-Zeile.

## Einschraenkungen

- Open Interest: keine kostenlose Historie fuer den Zeitraum -> OI-Muster neutral.
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Engine-Standardwerte auf pivot_n=5, k_atr=2.0 setzen, falls abweichend von (5, 3.0).