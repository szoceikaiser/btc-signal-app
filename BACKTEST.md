# Backtest-Bericht (E4b): Engine vs. Kaisers notierte Furkan-Trigger

Zeitraum: 01.09.2025-30.04.2026 (4h-Kerzen, 1585 Stueck) · Stand: 2026-07-24 10:24 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

## Parameter-Vergleich (E8.5: bessere Long-Einstiege, alle n=5 nur-Long)

Drei Furkan-Filter, einzeln und kombiniert (Furkans Schritt 1 = Richtung aus Makro, dann Konfluenz-Bestaetigung): **Trendfilter** = keine Longs gegen den 1D-Trend (Preis vs. Tages-EMA). **Strenge Bestaetigung** = KAUF 2 nur wenn Spot-CVD dreht UND Funding stimmt (statt eines von beiden). **Konfluenz 4h/1D** = Einstieg nur, wenn die 4h-Zone in der 1D-Retracement-Zone liegt. Sortiert nach Rendite.

| Variante | Recall | Praezision | Rendite | Signale |
|---|---|---|---|---|
| Long+Short (alt) | 45% | 54% | -5.3 % | 49 |
| nur Long | 27% | 44% | +2.5 % | 38 |
| +Trendfilter | 5% | 14% | -3.1 % | 21 |
| +Strenge Bestaetigung | 27% | 44% | +2.5 % | 38 |
| +Konfluenz 4h/1D | 7% | 33% | +2.9 % | 16 **<-- beste** |
| +alle drei | 0% | 0% | -1.4 % | 3 |

## Beste Kombination (nach Rendite): +Konfluenz 4h/1D (pivot_n=5, nur Long=True, Trendfilter=False, strenge Best.=False, Konfluenz=True)

- Kauf-Trigger getroffen: 0/20 — 
- Kauf verpasst: 25.09.25, 10.10.25, 21.10.25, 27.10.25, 28.10.25, 29.10.25, 30.10.25, 04.11.25, 17.11.25, 20.11.25, 21.11.25, 06.01.26, 08.01.26, 20.01.26, 29.01.26, 30.01.26, 31.01.26, 28.02.26, 23.03.26, 27.03.26
- Verkauf-Trigger getroffen: 3/24 — 16.10.25, 17.12.25, 02.03.26
- Verkauf verpasst: 25.09.25, 02.10.25, 03.10.25, 10.10.25, 04.11.25, 12.11.25, 23.11.25, 28.11.25, 02.12.25, 03.12.25, 06.01.26, 14.01.26, 25.01.26, 02.02.26, 23.02.26, 28.02.26, 17.03.26, 08.04.26, 14.04.26, 17.04.26, 22.04.26
- Engine-Signal-Tage gesamt: 3 Kauf / 6 Verkauf

## P&L-Simulation (beste Kombination)

Start 10.000 € -> **10,287 €** (+2.9 %) · Buy&Hold im Zeitraum: -28.4 % · 11 Verkaufs-Vorgaenge, davon 10 im Gewinn · Gebuehr 0.1 % je Order, kein Hebel.

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in dieser P&L-Zeile.

## Einschraenkungen

- Open Interest: keine kostenlose Historie fuer den Zeitraum -> OI-Muster neutral.
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante '+Konfluenz 4h/1D' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.