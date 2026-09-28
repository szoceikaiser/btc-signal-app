# Ergänzende Strukturprüfung: ursprüngliche E4-Werte

Vorfestlegung: [STRUKTURPLAN.md](STRUKTURPLAN.md), vor diesem Lauf committed. Acht Zeilen, davon eine identisch mit V000; sieben zusätzliche eindeutige Konfigurationen, zusammen mit dem Hauptgitter 86. Alle sonstigen Parameter auf heutiger eingefrorener Live-Basis. Keine Wiederholung des ursprünglichen E4-Triggerabgleichs und kein unberührter Test.

Gleiche abgeschlossene Daten, unabhängige F09-Buchführung und Kostenmodelle wie [KOMBINATIONEN.md](KOMBINATIONEN.md). Level-Rendite bleibt wegen der bekannten Ausführungs-/Engine-Grenzen eine hypothetische Vergleichszahl. Schluss-DD ist nicht der maximale Intraday-Rückgang.

| ID | n | k | Level % | H1/H2 % | Δ H1/H2 Punkte | Schluss-DD % | Gebühren USD | Orders / Null | Ø investiert % | nächste Eröffnung % | +4h, teuer % | Minimum ohne Monat, Punkte | beide ≥2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| S000 | 3 | 2 | 18.19 | 6.54/10.94 | -17.07/+0.81 | -15.27 | 565.66 | 227/18 | 36.00 | 13.98 | -3.21 | -18.89 | False |
| S001 | 3 | 3 | 18.19 | 6.54/10.94 | -17.07/+0.81 | -15.27 | 565.66 | 227/18 | 36.00 | 13.98 | -3.21 | -18.89 | False |
| S002 | 4 | 2 | 35.44 | 24.08/9.16 | +0.47/-0.97 | -8.30 | 565.56 | 193/14 | 35.43 | 31.56 | 14.02 | -1.41 | False |
| S003 | 4 | 3 | 35.44 | 24.08/9.16 | +0.47/-0.97 | -8.30 | 565.56 | 193/14 | 35.43 | 31.56 | 14.02 | -1.41 | False |
| S004 | 5 | 2 | 36.13 | 23.61/10.13 | +0.00/+0.00 | -8.29 | 545.01 | 191/14 | 35.42 | 31.09 | 17.97 | +0.00 | False |
| S005 | 5 | 3 | 36.13 | 23.61/10.13 | +0.00/+0.00 | -8.29 | 545.01 | 191/14 | 35.42 | 31.09 | 17.97 | +0.00 | False |
| S006 | 6 | 2 | 39.27 | 20.22/15.85 | -3.39/+5.72 | -8.29 | 438.52 | 161/16 | 39.83 | 35.59 | 25.87 | -4.34 | False |
| S007 | 6 | 3 | 39.27 | 20.22/15.85 | -3.39/+5.72 | -8.29 | 438.52 | 161/16 | 39.83 | 35.59 | 25.87 | -4.34 | False |

## Einordnung

Keine Variante erreicht +2 Punkte in beiden Hälften; auch der +1-Filter würde keine neue Alternative qualifizieren. n=6 erhöht die Gesamtrendite auf 39,27 %, verliert jedoch 3,39 Punkte in H1 und gewinnt 5,72 in H2. Ohne den günstigsten einzelnen Monat kippt der Vorteil bis auf −4,34 Punkte. n=3 fällt deutlich zurück. Die ursprüngliche Nähe zu bekannten Handelsdaten rechtfertigt somit keine allgemeine Wahl eines profitableren Nachbarwerts.

**k=2 und k=3 sind hier redundant:** `last_significant_impulse` verlangt zunächst mindestens 5 % Beinlänge, danach mindestens k×ATR **oder** 3 % Beinlänge (`strategy_core.py:236–243`). Wer die harte 5-%-Grenze erfüllt, erfüllt bereits die 3-%-Alternative. Deshalb verändert k in diesem Live-Verbund die Impulsauswahl nicht. Das ist ein logischer Zusammenhang der Regeln, keine zusätzliche empirische Bestätigung durch doppelte Renditezeilen.

Alle acht Detaildateien liegen unter `struktur/Sxxx.json`. Die Auswahl aus den alten Werten erweitert die Zahl der untersuchten Konfigurationen; sie liefert keine neue unabhängige Stichprobe. Ein besserer Nachbarwert wäre eine Sensitivitätswarnung, keine automatische Neu-Kalibrierung.
