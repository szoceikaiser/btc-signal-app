# Backtest-Bericht (E4b): Engine vs. Kaisers notierte Furkan-Trigger

Zeitraum: 01.09.2025-30.04.2026 (4h-Kerzen, 1585 Stueck) · Stand: 2026-07-24 13:59 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

## Parameter-Vergleich (E8.5: bessere Long-Einstiege, alle n=5 nur-Long)

Drei Furkan-Filter, einzeln und kombiniert (Furkans Schritt 1 = Richtung aus Makro, dann Konfluenz-Bestaetigung): **Trendfilter** = keine Longs gegen den 1D-Trend (Preis vs. Tages-EMA). **Strenge Bestaetigung** = KAUF 2 nur wenn Spot-CVD dreht UND Funding stimmt (statt eines von beiden). **Konfluenz 4h/1D** = Einstieg nur, wenn die 4h-Zone in der 1D-Retracement-Zone liegt. Sortiert nach Rendite.

| Variante | Recall | Praezision | Rendite | Signale |
|---|---|---|---|---|
| nur Long (Basis) | 43% | 42% | +12.3 % | 92 |
| +Flush t1 | 45% | 30% | +24.2 % | 146 |
| +Flush core | 45% | 31% | +33.5 % | 145 **<-- beste** |
| +Strenge Bestaetigung | 43% | 40% | +4.6 % | 90 |
| +Flush t1 +Streng | 45% | 34% | +11.6 % | 134 |
| Long+Short (Ref) | 45% | 49% | -2.6 % | 59 |

## Beste Kombination (nach Rendite): +Flush core (pivot_n=5, nur Long=True, Trendfilter=False, strenge Best.=False, Konfluenz=False)

- Kauf-Trigger getroffen: 8/20 — 21.10.25, 17.11.25, 20.11.25, 21.11.25, 06.01.26, 08.01.26, 28.02.26, 23.03.26
- Kauf verpasst: 25.09.25, 10.10.25, 27.10.25, 28.10.25, 29.10.25, 30.10.25, 04.11.25, 20.01.26, 29.01.26, 30.01.26, 31.01.26, 27.03.26
- Verkauf-Trigger getroffen: 12/24 — 16.10.25, 04.11.25, 12.11.25, 06.01.26, 14.01.26, 25.01.26, 23.02.26, 02.03.26, 17.03.26, 08.04.26, 14.04.26, 22.04.26
- Verkauf verpasst: 25.09.25, 02.10.25, 03.10.25, 10.10.25, 23.11.25, 28.11.25, 02.12.25, 03.12.25, 17.12.25, 02.02.26, 28.02.26, 17.04.26
- Engine-Signal-Tage gesamt: 31 Kauf / 41 Verkauf

## P&L-Simulation (beste Kombination)

Start 10.000 € -> **13,348 €** (+33.5 %) · Buy&Hold im Zeitraum: -28.4 % · 73 Verkaufs-Vorgaenge, davon 58 im Gewinn · Gebuehr 0.1 % je Order, kein Hebel.

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in dieser P&L-Zeile.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 998 OI-Punkte, 999 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante '+Flush core' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.