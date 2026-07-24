# Backtest-Bericht (E4b): Engine vs. Kaisers notierte Furkan-Trigger

Zeitraum: 01.09.2025-30.04.2026 (4h-Kerzen, 1585 Stueck) · Stand: 2026-07-24 09:02 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

## Parameter-Vergleich

(Flush-Modus = Einstieg bei GP-Durchschlag; Leiter = gestaffelte Zwischen-Teilgewinne an Ext 0.8/0.9 je 15 % vor dem 1.0-Ziel, E8.2)

| pivot_n | k_atr | Flush | Leiter | Recall | Praezision | Rendite | Signale |
|---|---|---|---|---|---|---|---|
| 3 | 2.0 | off | aus | 32% | 28% | -4.6 % | 63 |
| 3 | 2.0 | off | an | 32% | 27% | -4.7 % | 75 |
| 4 | 2.0 | off | aus | 41% | 39% | -4.1 % | 49 |
| 4 | 2.0 | off | an | 41% | 36% | -4.3 % | 59 |
| 5 | 2.0 | off | aus | 45% | 54% | -6.0 % | 40 **<-- beste** |
| 5 | 2.0 | off | an | 45% | 54% | -5.3 % | 49 |
| 6 | 2.0 | off | aus | 20% | 31% | -4.2 % | 31 |
| 6 | 2.0 | off | an | 25% | 33% | -2.3 % | 41 |

## Beste Kombination: pivot_n=5, k_atr=2.0, flush=off, Leiter=aus

- Kauf-Trigger getroffen: 13/20 — 21.10.25, 27.10.25, 28.10.25, 29.10.25, 30.10.25, 17.11.25, 20.11.25, 21.11.25, 06.01.26, 08.01.26, 29.01.26, 30.01.26, 31.01.26
- Kauf verpasst: 25.09.25, 10.10.25, 04.11.25, 20.01.26, 28.02.26, 23.03.26, 27.03.26
- Verkauf-Trigger getroffen: 7/24 — 16.10.25, 12.11.25, 23.11.25, 28.11.25, 14.01.26, 25.01.26, 17.03.26
- Verkauf verpasst: 25.09.25, 02.10.25, 03.10.25, 10.10.25, 04.11.25, 02.12.25, 03.12.25, 17.12.25, 06.01.26, 02.02.26, 23.02.26, 28.02.26, 02.03.26, 08.04.26, 14.04.26, 17.04.26, 22.04.26
- Engine-Signal-Tage gesamt: 15 Kauf / 20 Verkauf

## P&L-Simulation (beste Kombination)

Start 10.000 € -> **9,399 €** (-6.0 %) · Buy&Hold im Zeitraum: -28.4 % · 18 Verkaufs-Vorgaenge, davon 10 im Gewinn · Gebuehr 0.1 % je Order, kein Hebel.

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in dieser P&L-Zeile.

## Einschraenkungen

- Open Interest: keine kostenlose Historie fuer den Zeitraum -> OI-Muster neutral.
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Engine-Standardwerte auf pivot_n=5, k_atr=2.0, flush_entry='off', tp_ladder=False setzen, falls abweichend (aktuelle Defaults in strategy_core.evaluate pruefen).