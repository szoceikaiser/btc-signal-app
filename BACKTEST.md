# Backtest-Bericht (E4b): Engine vs. Kaisers notierte Furkan-Trigger

Zeitraum: 01.09.2025-30.04.2026 (4h-Kerzen, 1585 Stueck) · Stand: 2026-07-24 09:35 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

## Parameter-Vergleich

(Leiter = gestaffelte Zwischen-Teilgewinne Ext 0.8/0.9, E8.2. Richtung: ls = Long+Short wie bisher, long = nur Long/bias_short=false. Furkan handelte in diesem Zeitraum fast nur Long. Sortiert nach Rendite = das Geld-Maß.)

| pivot_n | Richtung | Leiter | Recall | Praezision | Rendite | Signale |
|---|---|---|---|---|---|---|
| 3 | ls | an | 32% | 27% | -4.7 % | 75 |
| 3 | long | an | 25% | 31% | -2.6 % | 54 |
| 4 | ls | an | 41% | 36% | -4.3 % | 59 |
| 4 | long | an | 34% | 42% | +3.6 % | 54 |
| 5 | ls | an | 45% | 54% | -5.3 % | 49 |
| 5 | long | an | 27% | 44% | +2.5 % | 38 |
| 6 | ls | an | 25% | 33% | -2.3 % | 41 |
| 6 | long | an | 16% | 30% | +16.3 % | 31 **<-- beste** |

## Beste Kombination (nach Rendite): pivot_n=6, Richtung=long, Leiter=an, flush=off, k_atr=2.0

- Kauf-Trigger getroffen: 2/20 — 04.11.25, 17.11.25
- Kauf verpasst: 25.09.25, 10.10.25, 21.10.25, 27.10.25, 28.10.25, 29.10.25, 30.10.25, 20.11.25, 21.11.25, 06.01.26, 08.01.26, 20.01.26, 29.01.26, 30.01.26, 31.01.26, 28.02.26, 23.03.26, 27.03.26
- Verkauf-Trigger getroffen: 5/24 — 16.10.25, 04.11.25, 12.11.25, 06.01.26, 17.03.26
- Verkauf verpasst: 25.09.25, 02.10.25, 03.10.25, 10.10.25, 23.11.25, 28.11.25, 02.12.25, 03.12.25, 17.12.25, 14.01.26, 25.01.26, 02.02.26, 23.02.26, 28.02.26, 02.03.26, 08.04.26, 14.04.26, 17.04.26, 22.04.26
- Engine-Signal-Tage gesamt: 10 Kauf / 13 Verkauf

## P&L-Simulation (beste Kombination)

Start 10.000 € -> **11,629 €** (+16.3 %) · Buy&Hold im Zeitraum: -28.4 % · 18 Verkaufs-Vorgaenge, davon 14 im Gewinn · Gebuehr 0.1 % je Order, kein Hebel.

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in dieser P&L-Zeile.

## Einschraenkungen

- Open Interest: keine kostenlose Historie fuer den Zeitraum -> OI-Muster neutral.
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: pivot_n=6, k_atr=2.0, flush_entry='off', tp_ladder=True. Richtung=long: 'long' heisst bias_short=false in site/data/state.json (kein Code-Default — der Richtungs-Bias soll dynamisch aus Makro kommen, E8.5). Schneidet 'long' hier klar besser ab, ist das die Bestaetigung von Furkans Long-Bias in diesem Zeitraum.