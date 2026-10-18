# Historische Auswertung nach Etappe 6

Basis `05208cecce8d5a0e856a1ea56984b209f403ccd6`. Nur das festgelegte Paar Basis/E42-12; keine Optimierung. Live unverändert.

**Ergebnis bis 29.09., 12:00 UTC:** Im Hauptfall S1 endet die Basis mit 12.813,81 USD, E42 mit 12.639,84 USD: E42 liegt 173,96 USD beziehungsweise 1,3576 % darunter und hat höheren Schluss-DD sowie eine höhere obere Intrabar-Grenze. Das bedingte 95-%-Intervall des relativen Tagesbereichsvorteils reicht von −4,1660 bis +1,4369 % (p_cond 0,839658). Keine belegte Überlegenheit.

Die Basis dominiert historisch S0/S1/S2/S4. S3 (zusätzliche Wartekerze, 0,1 % Slippage) zeigt +117,27 USD für E42, aber höheren Schluss-DD: ein Zielkonflikt. Alle drei S3-Unsicherheitsintervalle umfassen null. Sein positiver Unterschied konzentriert sich auf August (+204,21 USD), mehr als der gesamte Vorteil. S1 bleibt auch bei beiden festgelegten Frischstarts negativ. Keine Auswahl des günstigsten Szenarios als neues Hauptresultat.

R0 endet am 27.09.2026 um 08:29:08.840 UTC (letzter Close 08:00). R1 endet fest am 29.09.2026 um 12:00 UTC. 
R1 ergänzt 13 abgeschlossene Kerzen; die 2.480 abgeschlossenen R0-Kerzen einschließlich Warmup sind feldgenau gleich. Die damalige laufende R0-Kerze bleibt im Original erhalten, war dort ausgeschlossen und wird nur in R1 als später abgeschlossene neue Kerze verwendet.

Daten, Parameter, Statistik und Ausführung wurden vor der Auswertung fixiert (erster Plan Commit `6462e08`, erhalten als `plan-v1.json`). Ein i+2-Frischstart traf einen numerischen Überverkauf um 1,7347e-18 BTC. Planversion 2 dokumentiert die isolierte Rundungskorrektur (höchstens 8 ULP des Spitzenbestands); materielle Überverkäufe bleiben gesperrt. Alle 60 Fälle wurden danach neu gerechnet. Analyse nach Datenkenntnis, keine historische Präregistrierung. 
30 kausale Läufe je Paket: zwei Zeilen × fünf Szenarien × ursprünglicher Start und zwei feste Frischstarts. Alle 60 mit unabhängiger Kandidaten-/Losbuchführung und Decimal-Restkosten geprüft.

| Fall | Fill | Slippage je Seite | Gebühr je Seite |
|---|---|---:|---:|
| S0 | nächstes Open | 0 % | 0,1 % |
| S1 (Hauptfall) | nächstes Open | 0,1 % | 0,1 % |
| S2 | nächstes Open | 0,5 % | 0,1 % |
| S3 | Open i+2 | 0,1 % | 0,1 % |
| S4 | Open i+2 | 0,5 % | 0,1 % |

## R0: vollständiger Pfad

| Fall | Basis USD | E42 USD | E42 − Basis USD | relativer Vorteil % | historische Dominanz |
|---|---:|---:|---:|---:|---|
| S0 | 13418.88 | 13299.89 | -118.99 | -0.8867 | Basis |
| S1 | 12852.01 | 12677.52 | -174.48 | -1.3576 | Basis |
| S2 | 10815.30 | 10467.26 | -348.03 | -3.2180 | Basis |
| S3 | 12719.69 | 12837.36 | +117.67 | +0.9251 | Zielkonflikt / Gleichstand |
| S4 | 10838.14 | 10781.67 | -56.47 | -0.5210 | Basis |

Dominanz gilt ausschließlich für Endwert, Schluss-DD und obere Intrabar-Grenze in diesem historischen Modell. Toleranzen: 0,01 USD / 1e-8 Prozentpunkte.

| Fall / Zeile | Gebühren USD | Cash USD | BTC | Restkosten USD | Exposition Ende % | Mittel % | DD Schluss % | DD untere % | DD obere % | Fills |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S0 Basis | 514.07 | 4676.48 | 0.10310534 | 8684.88 | 65.15 | 33.49 | 7.9166 | 9.9428 | 9.9428 | 171 |
| S0 E42 | 570.41 | 4635.01 | 0.10219110 | 8607.87 | 65.15 | 34.46 | 8.4177 | 9.9428 | 9.9428 | 196 |
| S1 Basis | 502.63 | 4481.84 | 0.09871530 | 8323.41 | 65.13 | 33.49 | 8.4989 | 9.9428 | 9.9428 | 171 |
| S1 E42 | 556.34 | 4420.99 | 0.09737512 | 8210.41 | 65.13 | 34.47 | 9.0636 | 10.2437 | 10.2437 | 196 |
| S2 Basis | 460.06 | 3781.38 | 0.08295588 | 7022.57 | 65.04 | 33.48 | 12.0534 | 12.6548 | 12.6548 | 171 |
| S2 E42 | 504.41 | 3659.70 | 0.08028640 | 6796.59 | 65.04 | 34.47 | 13.1053 | 13.6995 | 13.6995 | 196 |
| S3 Basis | 477.56 | 4442.17 | 0.09762258 | 8249.75 | 65.08 | 32.11 | 8.1439 | 9.9428 | 9.9428 | 162 |
| S3 E42 | 521.04 | 4483.27 | 0.09852571 | 8326.07 | 65.08 | 33.15 | 8.2843 | 9.9428 | 9.9428 | 183 |
| S4 Basis | 439.98 | 3794.90 | 0.08306594 | 7047.67 | 64.99 | 32.10 | 12.7905 | 13.1803 | 13.1803 | 162 |
| S4 E42 | 476.42 | 3775.13 | 0.08263314 | 7010.95 | 64.99 | 33.14 | 12.8109 | 13.2317 | 13.2317 | 183 |

Startwert 10.000 USD, keine Schlussliquidation. Exposition: BTC-Marktwert / Vermögen; Mittel über 4h-Closes. Risikopeaks der Hauptausgabe laufen durchgehend weiter. Intrabar sind Grenzen, keine gemessenen Preisreihenfolgen.

### R0: bedingte Unsicherheit

| Fall | Block Tage | n | A_days % | Basic 95-%-Intervall % | einseitige 95-%-Untergrenze % | p_cond |
|---|---:|---:|---:|---|---:|---:|
| S0 | 14 | 251 | -0.8867 | [-3.6978, +1.8598] | -3.2283 | 0.734913 |
| S0 | 7 | 251 | -0.8867 | [-4.2164, +2.2995] | -3.6167 | 0.702215 |
| S0 | 28 | 251 | -0.8867 | [-3.2885, +1.4753] | -2.9103 | 0.765762 |
| S1 | 14 | 251 | -1.3576 | [-4.1408, +1.4135] | -3.6757 | 0.835908 |
| S1 | 7 | 251 | -1.3576 | [-4.6329, +1.8789] | -4.0631 | 0.792160 |
| S1 | 28 | 251 | -1.3576 | [-3.7259, +1.0184] | -3.3549 | 0.868757 |
| S2 | 14 | 251 | -3.2180 | [-6.0424, -0.1651] | -5.5942 | 0.980401 |
| S2 | 7 | 251 | -3.2180 | [-6.4825, +0.3920] | -5.9714 | 0.960502 |
| S2 | 28 | 251 | -3.2180 | [-5.6429, -0.6166] | -5.2651 | 0.991500 |
| S3 | 14 | 251 | +0.9251 | [-3.8306, +4.3895] | -2.9828 | 0.302635 |
| S3 | 7 | 251 | +0.9251 | [-4.3055, +4.6687] | -3.2846 | 0.310134 |
| S3 | 28 | 251 | +0.9251 | [-3.3139, +4.1341] | -2.4905 | 0.288686 |
| S4 | 14 | 251 | -0.5210 | [-4.5840, +2.8104] | -3.8326 | 0.587771 |
| S4 | 7 | 251 | -0.5210 | [-5.0645, +3.1582] | -4.1868 | 0.567472 |
| S4 | 28 | 251 | -0.5210 | [-4.0745, +2.5320] | -3.4108 | 0.603770 |

UTC-Tagesbereich: 2026-01-19T00:00:00+00:00 bis 2026-09-27T00:00:00+00:00; 251 volle Tage. Ausgeschlossen: 4 Stunden am Anfang, 8 am Ende. Diese Randintervalle bleiben vollständig im Portfoliobericht. Tagesgrenzen sind Close vor neuem Open-Fill.

Stationärer gepaarter Bootstrap: 20.000 Replikate, PCG64/20260929, NumPy 2.3.5, lineare Quantile. 14 Tage Hauptfall; 7/28 vollständig sensitiv. Alle Szenarien verwenden bei gleicher Tageszahl dieselben Zufallsindizes. 
Intervalle und p-Werte sind nur bedingt auf das feste Paar. Frühere Auswahl nicht bereinigt; Power unbekannt. Schwache Abhängigkeit/Stationarität sind Annahmen, durch Regimewechsel und lange Haltephasen begrenzt. Renditeresampling erzeugt keine neuen OHLC-/Strategiepfade und keine DD-Verteilung.

### R0: alle Monate und Drittel, fortlaufendes Portfolio

Beiträge sind USD-Veränderungen im fortlaufenden Konto. Abschnitts-DD beginnt hier ausdrücklich am Abschnittsanfang und ist nur Zusatzdiagnostik; die Haupt-DD oben bleibt unverändert. Vollständige Gebühren/Bestände/Exposition und alle drei Abschnitts-DD je Zeile in `periods.csv` und `results.json`.

| Fall | Abschnitt UTC | Basis Beitrag USD | E42 Beitrag USD | Differenz USD | Basis Rendite % | E42 Rendite % | Basis Abschnitts-DD % | E42 Abschnitts-DD % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| S0 | 2026-01 (Teilmonat) | -296.35 | -296.35 | +0.00 | -2.963 | -2.963 | 2.963 | 2.963 |
| S0 | 2026-02 | +244.50 | +191.11 | -53.40 | +2.520 | +1.969 | 7.550 | 7.550 |
| S0 | 2026-03 | +1045.31 | +1100.11 | +54.80 | +10.508 | +11.118 | 5.464 | 5.670 |
| S0 | 2026-04 | +900.99 | +911.31 | +10.32 | +8.196 | +8.288 | 2.912 | 2.912 |
| S0 | 2026-05 | +489.08 | +489.56 | +0.48 | +4.112 | +4.112 | 4.113 | 4.113 |
| S0 | 2026-06 | +13.72 | +19.34 | +5.62 | +0.111 | +0.156 | 3.425 | 3.425 |
| S0 | 2026-07 | +151.43 | +85.18 | -66.25 | +1.221 | +0.686 | 3.395 | 3.413 |
| S0 | 2026-08 | +386.33 | +369.12 | -17.21 | +3.079 | +2.953 | 4.381 | 4.551 |
| S0 | 2026-09 (Teilmonat) | +483.88 | +430.52 | -53.36 | +3.741 | +3.345 | 5.597 | 5.597 |
| S0 | Drittel 1 | +1469.84 | +1481.15 | +11.31 | +14.698 | +14.811 | 7.917 | 8.418 |
| S0 | Drittel 2 | +927.41 | +933.93 | +6.52 | +8.086 | +8.134 | 4.721 | 4.721 |
| S0 | Drittel 3 | +1021.63 | +884.82 | -136.82 | +8.241 | +7.127 | 6.375 | 6.529 |
| S1 | 2026-01 (Teilmonat) | -309.74 | -309.74 | +0.00 | -3.097 | -3.097 | 3.097 | 3.097 |
| S1 | 2026-02 | +232.67 | +174.56 | -58.11 | +2.401 | +1.801 | 7.550 | 7.550 |
| S1 | 2026-03 | +953.87 | +997.13 | +43.26 | +9.613 | +10.108 | 5.681 | 6.060 |
| S1 | 2026-04 | +777.02 | +778.34 | +1.31 | +7.144 | +7.166 | 3.198 | 3.198 |
| S1 | 2026-05 | +435.26 | +434.75 | -0.51 | +3.735 | +3.735 | 4.241 | 4.241 |
| S1 | 2026-06 | -30.23 | -30.61 | -0.38 | -0.250 | -0.253 | 3.530 | 3.546 |
| S1 | 2026-07 | +97.27 | +26.76 | -70.51 | +0.807 | +0.222 | 3.395 | 3.414 |
| S1 | 2026-08 | +298.66 | +267.38 | -31.27 | +2.457 | +2.215 | 4.623 | 4.798 |
| S1 | 2026-09 (Teilmonat) | +397.23 | +338.95 | -58.28 | +3.189 | +2.747 | 5.880 | 5.880 |
| S1 | Drittel 1 | +1282.42 | +1269.31 | -13.11 | +12.824 | +12.693 | 8.499 | 9.064 |
| S1 | Drittel 2 | +776.43 | +775.12 | -1.31 | +6.882 | +6.878 | 4.962 | 4.966 |
| S1 | Drittel 3 | +793.16 | +633.10 | -160.06 | +6.577 | +5.256 | 6.816 | 6.985 |
| S2 | 2026-01 (Teilmonat) | -363.05 | -363.05 | +0.00 | -3.630 | -3.630 | 3.630 | 3.630 |
| S2 | 2026-02 | +185.95 | +109.30 | -76.65 | +1.930 | +1.134 | 7.550 | 7.550 |
| S2 | 2026-03 | +599.84 | +600.07 | +0.23 | +6.107 | +6.157 | 6.752 | 7.601 |
| S2 | 2026-04 | +316.91 | +289.14 | -27.77 | +3.041 | +2.795 | 4.385 | 4.385 |
| S2 | 2026-05 | +240.64 | +238.30 | -2.33 | +2.241 | +2.241 | 4.858 | 4.858 |
| S2 | 2026-06 | -184.47 | -203.89 | -19.42 | -1.680 | -1.875 | 4.157 | 4.339 |
| S2 | 2026-07 | -90.06 | -171.97 | -81.91 | -0.834 | -1.612 | 3.549 | 3.884 |
| S2 | 2026-08 | +1.03 | -71.17 | -72.20 | +0.010 | -0.678 | 5.581 | 5.779 |
| S2 | 2026-09 (Teilmonat) | +108.52 | +40.54 | -67.98 | +1.014 | +0.389 | 7.005 | 7.005 |
| S2 | Drittel 1 | +563.21 | +460.73 | -102.48 | +5.632 | +4.607 | 10.841 | 11.653 |
| S2 | Drittel 2 | +232.60 | +209.13 | -23.47 | +2.202 | +1.999 | 6.668 | 6.853 |
| S2 | Drittel 3 | +19.48 | -202.60 | -222.09 | +0.180 | -1.899 | 8.558 | 9.073 |
| S3 | 2026-01 (Teilmonat) | -126.30 | -126.30 | +0.00 | -1.263 | -1.263 | 1.728 | 1.728 |
| S3 | 2026-02 | +288.05 | +237.99 | -50.06 | +2.917 | +2.410 | 7.550 | 7.550 |
| S3 | 2026-03 | +1121.91 | +1116.38 | -5.53 | +11.041 | +11.041 | 5.656 | 5.656 |
| S3 | 2026-04 | +777.96 | +770.58 | -7.38 | +6.895 | +6.863 | 2.482 | 2.482 |
| S3 | 2026-05 | +381.59 | +406.97 | +25.39 | +3.164 | +3.392 | 4.605 | 4.605 |
| S3 | 2026-06 | -217.01 | -216.35 | +0.66 | -1.744 | -1.744 | 4.150 | 4.150 |
| S3 | 2026-07 | +167.29 | +166.79 | -0.51 | +1.368 | +1.368 | 3.393 | 3.393 |
| S3 | 2026-08 | +83.17 | +287.37 | +204.21 | +0.671 | +2.326 | 3.629 | 3.791 |
| S3 | 2026-09 (Teilmonat) | +243.02 | +193.93 | -49.10 | +1.948 | +1.534 | 5.574 | 5.924 |
| S3 | Drittel 1 | +1602.30 | +1532.37 | -69.93 | +16.023 | +15.324 | 7.550 | 7.550 |
| S3 | Drittel 2 | +623.90 | +656.90 | +33.00 | +5.377 | +5.696 | 6.532 | 6.532 |
| S3 | Drittel 3 | +493.49 | +648.09 | +154.60 | +4.036 | +5.317 | 6.394 | 6.537 |
| S4 | 2026-01 (Teilmonat) | -165.13 | -165.13 | +0.00 | -1.651 | -1.651 | 1.867 | 1.867 |
| S4 | 2026-02 | +240.48 | +171.40 | -69.08 | +2.445 | +1.743 | 7.550 | 7.550 |
| S4 | 2026-03 | +793.48 | +788.04 | -5.44 | +7.875 | +7.875 | 6.576 | 6.576 |
| S4 | 2026-04 | +347.29 | +317.24 | -30.05 | +3.195 | +2.939 | 2.810 | 2.810 |
| S4 | 2026-05 | +188.88 | +190.49 | +1.61 | +1.684 | +1.714 | 5.218 | 5.218 |
| S4 | 2026-06 | -346.41 | -343.29 | +3.13 | -3.037 | -3.037 | 4.770 | 4.770 |
| S4 | 2026-07 | +4.84 | +4.79 | -0.04 | +0.044 | +0.044 | 3.393 | 3.393 |
| S4 | 2026-08 | -203.85 | -95.39 | +108.46 | -1.843 | -0.870 | 4.866 | 5.171 |
| S4 | 2026-09 (Teilmonat) | -21.42 | -86.48 | -65.06 | -0.197 | -0.796 | 7.120 | 7.585 |
| S4 | Drittel 1 | +947.98 | +839.33 | -108.65 | +9.480 | +8.393 | 7.550 | 7.550 |
| S4 | Drittel 2 | +110.60 | +119.42 | +8.82 | +1.010 | +1.102 | 8.097 | 8.097 |
| S4 | Drittel 3 | -220.44 | -177.08 | +43.36 | -1.993 | -1.616 | 8.161 | 8.183 |

### R0: Frischstarts an beiden Drittelgrenzen

Jeweils bis zum Paketende, vorheriger Marktdatenpräfix als Warmup, 10.000 USD, null BTC, keine geerbten Absichten/Peaks. Bekannte Daten, keine unabhängigen Bestätigungsfenster.

| Start UTC | Fall | Basis USD | E42 USD | Differenz USD | Dominanz | Basis DD Schluss / obere % | E42 DD Schluss / obere % |
|---|---|---:|---:|---:|---|---|---|
| 2026-04-12T16:00:00+00:00 | S0 | 11699.27 | 11584.11 | -115.16 | Basis | 6.375 / 7.230 | 6.661 / 7.524 |
| 2026-04-12T16:00:00+00:00 | S1 | 11391.18 | 11249.60 | -141.58 | Basis | 7.277 / 8.110 | 7.968 / 8.794 |
| 2026-04-12T16:00:00+00:00 | S2 | 10238.65 | 10006.24 | -232.40 | Basis | 12.053 / 12.655 | 13.105 / 13.699 |
| 2026-04-12T16:00:00+00:00 | S3 | 10963.07 | 11131.59 | +168.52 | Zielkonflikt / Gleichstand | 8.144 / 8.802 | 8.284 / 8.942 |
| 2026-04-12T16:00:00+00:00 | S4 | 9899.68 | 9946.81 | +47.14 | Zielkonflikt / Gleichstand | 12.791 / 13.180 | 12.811 / 13.232 |
| 2026-07-05T12:00:00+00:00 | S0 | 10824.08 | 10712.70 | -111.39 | Basis | 6.375 / 7.230 | 6.529 / 7.230 |
| 2026-07-05T12:00:00+00:00 | S1 | 10657.74 | 10525.63 | -132.11 | Basis | 6.816 / 7.408 | 6.985 / 7.578 |
| 2026-07-05T12:00:00+00:00 | S2 | 10018.05 | 9810.12 | -207.93 | Basis | 8.558 / 9.139 | 9.073 / 9.436 |
| 2026-07-05T12:00:00+00:00 | S3 | 10403.63 | 10531.69 | +128.06 | Zielkonflikt / Gleichstand | 6.394 / 7.165 | 6.537 / 7.307 |
| 2026-07-05T12:00:00+00:00 | S4 | 9800.66 | 9838.42 | +37.75 | Zielkonflikt / Gleichstand | 8.161 / 8.670 | 8.183 / 8.724 |

Vollständige Cash/BTC/Restkosten/Gebühren/Exposition, Monats-/Drittelstände und größte Risikoepisoden auch für jeden Frischstart: Paket-`results.json` und `periods.csv`.

### R0: größte Rückgangsphasen des vollständigen Pfads

High/Low-Zeiten bezeichnen die Kerze mit diesem Schlusszeitpunkt, keinen beobachteten Intrabar-Zeitpunkt. Zusätzlich sind die drei größten Peak-bis-Erholung-Episoden je Maß im Ergebnis-JSON gespeichert.

| Fall / Zeile | Maß | DD % | Peak UTC / Bewertung | Tief UTC / Bewertung |
|---|---|---:|---|---|
| S0 Basis | Schluss | 7.9166 | 2026-03-17T00:00:00+00:00 / close | 2026-04-02T04:00:00+00:00 / close |
| S0 Basis | untere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S0 Basis | obere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S0 E42 | Schluss | 8.4177 | 2026-03-17T00:00:00+00:00 / close | 2026-04-02T04:00:00+00:00 / close |
| S0 E42 | untere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S0 E42 | obere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S1 Basis | Schluss | 8.4989 | 2026-03-17T00:00:00+00:00 / close | 2026-04-03T04:00:00+00:00 / close |
| S1 Basis | untere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S1 Basis | obere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S1 E42 | Schluss | 9.0636 | 2026-03-17T00:00:00+00:00 / close | 2026-04-03T04:00:00+00:00 / close |
| S1 E42 | untere Grenze | 10.2437 | 2026-03-17T04:00:00+00:00 / high | 2026-04-03T16:00:00+00:00 / low |
| S1 E42 | obere Grenze | 10.2437 | 2026-03-17T04:00:00+00:00 / high | 2026-04-03T16:00:00+00:00 / low |
| S2 Basis | Schluss | 12.0534 | 2026-05-11T00:00:00+00:00 / close | 2026-08-19T08:00:00+00:00 / close |
| S2 Basis | untere Grenze | 12.6548 | 2026-05-14T20:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |
| S2 Basis | obere Grenze | 12.6548 | 2026-05-14T20:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |
| S2 E42 | Schluss | 13.1053 | 2026-05-11T00:00:00+00:00 / close | 2026-08-19T08:00:00+00:00 / close |
| S2 E42 | untere Grenze | 13.6995 | 2026-05-14T20:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |
| S2 E42 | obere Grenze | 13.6995 | 2026-05-14T20:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |
| S3 Basis | Schluss | 8.1439 | 2026-05-11T00:00:00+00:00 / close | 2026-08-18T08:00:00+00:00 / close |
| S3 Basis | untere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S3 Basis | obere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S3 E42 | Schluss | 8.2843 | 2026-05-11T00:00:00+00:00 / close | 2026-08-18T08:00:00+00:00 / close |
| S3 E42 | untere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S3 E42 | obere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S4 Basis | Schluss | 12.7905 | 2026-05-11T00:00:00+00:00 / close | 2026-09-20T08:00:00+00:00 / close |
| S4 Basis | untere Grenze | 13.1803 | 2026-05-11T00:00:00+00:00 / high | 2026-09-20T04:00:00+00:00 / low |
| S4 Basis | obere Grenze | 13.1803 | 2026-05-11T00:00:00+00:00 / high | 2026-09-20T04:00:00+00:00 / low |
| S4 E42 | Schluss | 12.8109 | 2026-05-11T00:00:00+00:00 / close | 2026-08-19T08:00:00+00:00 / close |
| S4 E42 | untere Grenze | 13.2317 | 2026-05-11T00:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |
| S4 E42 | obere Grenze | 13.2317 | 2026-05-11T00:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |

### R0: Zeitstabilität und Konzentration

- S0: 4 positive, 4 negative, 1 unveränderte Monatsbeiträge; größte Monatsdifferenz -66.25 bis +54.80 USD.
- S1: 2 positive, 6 negative, 1 unveränderte Monatsbeiträge; größte Monatsdifferenz -70.51 bis +43.26 USD.
- S2: 1 positive, 7 negative, 1 unveränderte Monatsbeiträge; größte Monatsdifferenz -81.91 bis +0.23 USD.
- S3: 3 positive, 5 negative, 1 unveränderte Monatsbeiträge; größte Monatsdifferenz -50.06 bis +204.21 USD.
- S4: 3 positive, 5 negative, 1 unveränderte Monatsbeiträge; größte Monatsdifferenz -69.08 bis +108.46 USD.

Alle Positionszyklen mit Gewinn/Verlust, Gebühren, Zeitraum und Schlussstatus stehen in `cycles.json`; unterschiedliche Zyklen sind nicht automatisch paarbar.

## R1: vollständiger Pfad

| Fall | Basis USD | E42 USD | E42 − Basis USD | relativer Vorteil % | historische Dominanz |
|---|---:|---:|---:|---:|---|
| S0 | 13381.60 | 13262.94 | -118.66 | -0.8867 | Basis |
| S1 | 12813.81 | 12639.84 | -173.96 | -1.3576 | Basis |
| S2 | 10774.77 | 10428.05 | -346.73 | -3.2180 | Basis |
| S3 | 12675.69 | 12792.95 | +117.27 | +0.9251 | Zielkonflikt / Gleichstand |
| S4 | 10792.29 | 10736.06 | -56.23 | -0.5210 | Basis |

Dominanz gilt ausschließlich für Endwert, Schluss-DD und obere Intrabar-Grenze in diesem historischen Modell. Toleranzen: 0,01 USD / 1e-8 Prozentpunkte.

| Fall / Zeile | Gebühren USD | Cash USD | BTC | Restkosten USD | Exposition Ende % | Mittel % | DD Schluss % | DD untere % | DD obere % | Fills |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S0 Basis | 516.69 | 7293.17 | 0.07217374 | 6079.42 | 45.50 | 33.61 | 7.9166 | 9.9428 | 9.9428 | 173 |
| S0 E42 | 573.01 | 7228.50 | 0.07153377 | 6025.51 | 45.50 | 34.58 | 8.4177 | 9.9428 | 9.9428 | 198 |
| S1 Basis | 505.13 | 6984.61 | 0.06910071 | 5826.39 | 45.49 | 33.61 | 8.4989 | 9.9428 | 9.9428 | 173 |
| S1 E42 | 558.81 | 6889.78 | 0.06816259 | 5747.29 | 45.49 | 34.58 | 9.0636 | 10.2437 | 10.2437 | 198 |
| S2 Basis | 462.16 | 5876.18 | 0.05806912 | 4915.80 | 45.46 | 33.60 | 12.0534 | 12.6548 | 12.6548 | 173 |
| S2 E42 | 506.44 | 5687.09 | 0.05620048 | 4757.61 | 45.46 | 34.58 | 13.1053 | 13.6995 | 13.6995 | 198 |
| S3 Basis | 480.03 | 6911.01 | 0.06833580 | 5774.83 | 45.48 | 32.26 | 8.1439 | 9.9428 | 9.9428 | 164 |
| S3 E42 | 523.54 | 6974.95 | 0.06896799 | 5828.25 | 45.48 | 33.29 | 8.2843 | 9.9428 | 9.9428 | 185 |
| S4 Basis | 442.08 | 5887.20 | 0.05814616 | 4933.37 | 45.45 | 32.25 | 12.7905 | 13.1803 | 13.1803 | 164 |
| S4 E42 | 478.51 | 5856.52 | 0.05784319 | 4907.66 | 45.45 | 33.29 | 12.8109 | 13.2317 | 13.2317 | 185 |

Startwert 10.000 USD, keine Schlussliquidation. Exposition: BTC-Marktwert / Vermögen; Mittel über 4h-Closes. Risikopeaks der Hauptausgabe laufen durchgehend weiter. Intrabar sind Grenzen, keine gemessenen Preisreihenfolgen.

### R1: bedingte Unsicherheit

| Fall | Block Tage | n | A_days % | Basic 95-%-Intervall % | einseitige 95-%-Untergrenze % | p_cond |
|---|---:|---:|---:|---|---:|---:|
| S0 | 14 | 253 | -0.8867 | [-3.7408, +1.8687] | -3.2426 | 0.735263 |
| S0 | 7 | 253 | -0.8867 | [-4.1900, +2.2884] | -3.6057 | 0.701565 |
| S0 | 28 | 253 | -0.8867 | [-3.2879, +1.4791] | -2.8888 | 0.767412 |
| S1 | 14 | 253 | -1.3576 | [-4.1660, +1.4369] | -3.6919 | 0.839658 |
| S1 | 7 | 253 | -1.3576 | [-4.6045, +1.8642] | -4.0450 | 0.795010 |
| S1 | 28 | 253 | -1.3576 | [-3.7285, +1.0225] | -3.3381 | 0.869307 |
| S2 | 14 | 253 | -3.2180 | [-6.0248, -0.1732] | -5.6147 | 0.980851 |
| S2 | 7 | 253 | -3.2180 | [-6.4864, +0.3499] | -5.9809 | 0.962252 |
| S2 | 28 | 253 | -3.2180 | [-5.6345, -0.5919] | -5.2526 | 0.991300 |
| S3 | 14 | 253 | +0.9251 | [-3.9240, +4.3681] | -2.9795 | 0.302185 |
| S3 | 7 | 253 | +0.9251 | [-4.2458, +4.6217] | -3.3023 | 0.310184 |
| S3 | 28 | 253 | +0.9251 | [-3.2437, +4.1193] | -2.4459 | 0.286586 |
| S4 | 14 | 253 | -0.5210 | [-4.6200, +2.7814] | -3.8625 | 0.589071 |
| S4 | 7 | 253 | -0.5210 | [-4.9939, +3.1245] | -4.1772 | 0.573421 |
| S4 | 28 | 253 | -0.5210 | [-4.0034, +2.4805] | -3.3707 | 0.601620 |

UTC-Tagesbereich: 2026-01-19T00:00:00+00:00 bis 2026-09-29T00:00:00+00:00; 253 volle Tage. Ausgeschlossen: 4 Stunden am Anfang, 12 am Ende. Diese Randintervalle bleiben vollständig im Portfoliobericht. Tagesgrenzen sind Close vor neuem Open-Fill.

Stationärer gepaarter Bootstrap: 20.000 Replikate, PCG64/20260929, NumPy 2.3.5, lineare Quantile. 14 Tage Hauptfall; 7/28 vollständig sensitiv. Alle Szenarien verwenden bei gleicher Tageszahl dieselben Zufallsindizes. 
Intervalle und p-Werte sind nur bedingt auf das feste Paar. Frühere Auswahl nicht bereinigt; Power unbekannt. Schwache Abhängigkeit/Stationarität sind Annahmen, durch Regimewechsel und lange Haltephasen begrenzt. Renditeresampling erzeugt keine neuen OHLC-/Strategiepfade und keine DD-Verteilung.

### R1: alle Monate und Drittel, fortlaufendes Portfolio

Beiträge sind USD-Veränderungen im fortlaufenden Konto. Abschnitts-DD beginnt hier ausdrücklich am Abschnittsanfang und ist nur Zusatzdiagnostik; die Haupt-DD oben bleibt unverändert. Vollständige Gebühren/Bestände/Exposition und alle drei Abschnitts-DD je Zeile in `periods.csv` und `results.json`.

| Fall | Abschnitt UTC | Basis Beitrag USD | E42 Beitrag USD | Differenz USD | Basis Rendite % | E42 Rendite % | Basis Abschnitts-DD % | E42 Abschnitts-DD % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| S0 | 2026-01 (Teilmonat) | -296.35 | -296.35 | +0.00 | -2.963 | -2.963 | 2.963 | 2.963 |
| S0 | 2026-02 | +244.50 | +191.11 | -53.40 | +2.520 | +1.969 | 7.550 | 7.550 |
| S0 | 2026-03 | +1045.31 | +1100.11 | +54.80 | +10.508 | +11.118 | 5.464 | 5.670 |
| S0 | 2026-04 | +900.99 | +911.31 | +10.32 | +8.196 | +8.288 | 2.912 | 2.912 |
| S0 | 2026-05 | +489.08 | +489.56 | +0.48 | +4.112 | +4.112 | 4.113 | 4.113 |
| S0 | 2026-06 | +13.72 | +19.34 | +5.62 | +0.111 | +0.156 | 3.425 | 3.425 |
| S0 | 2026-07 | +151.43 | +85.18 | -66.25 | +1.221 | +0.686 | 3.395 | 3.413 |
| S0 | 2026-08 | +386.33 | +369.12 | -17.21 | +3.079 | +2.953 | 4.381 | 4.551 |
| S0 | 2026-09 (Teilmonat) | +446.60 | +393.57 | -53.02 | +3.453 | +3.058 | 5.597 | 5.597 |
| S0 | Drittel 1 | +1469.84 | +1481.15 | +11.31 | +14.698 | +14.811 | 7.917 | 8.418 |
| S0 | Drittel 2 | +927.41 | +933.93 | +6.52 | +8.086 | +8.134 | 4.721 | 4.721 |
| S0 | Drittel 3 | +984.35 | +847.87 | -136.49 | +7.940 | +6.829 | 6.375 | 6.529 |
| S1 | 2026-01 (Teilmonat) | -309.74 | -309.74 | +0.00 | -3.097 | -3.097 | 3.097 | 3.097 |
| S1 | 2026-02 | +232.67 | +174.56 | -58.11 | +2.401 | +1.801 | 7.550 | 7.550 |
| S1 | 2026-03 | +953.87 | +997.13 | +43.26 | +9.613 | +10.108 | 5.681 | 6.060 |
| S1 | 2026-04 | +777.02 | +778.34 | +1.31 | +7.144 | +7.166 | 3.198 | 3.198 |
| S1 | 2026-05 | +435.26 | +434.75 | -0.51 | +3.735 | +3.735 | 4.241 | 4.241 |
| S1 | 2026-06 | -30.23 | -30.61 | -0.38 | -0.250 | -0.253 | 3.530 | 3.546 |
| S1 | 2026-07 | +97.27 | +26.76 | -70.51 | +0.807 | +0.222 | 3.395 | 3.414 |
| S1 | 2026-08 | +298.66 | +267.38 | -31.27 | +2.457 | +2.215 | 4.623 | 4.798 |
| S1 | 2026-09 (Teilmonat) | +359.03 | +301.27 | -57.76 | +2.883 | +2.442 | 5.880 | 5.880 |
| S1 | Drittel 1 | +1282.42 | +1269.31 | -13.11 | +12.824 | +12.693 | 8.499 | 9.064 |
| S1 | Drittel 2 | +776.43 | +775.12 | -1.31 | +6.882 | +6.878 | 4.962 | 4.966 |
| S1 | Drittel 3 | +754.96 | +595.42 | -159.54 | +6.261 | +4.943 | 6.816 | 6.985 |
| S2 | 2026-01 (Teilmonat) | -363.05 | -363.05 | +0.00 | -3.630 | -3.630 | 3.630 | 3.630 |
| S2 | 2026-02 | +185.95 | +109.30 | -76.65 | +1.930 | +1.134 | 7.550 | 7.550 |
| S2 | 2026-03 | +599.84 | +600.07 | +0.23 | +6.107 | +6.157 | 6.752 | 7.601 |
| S2 | 2026-04 | +316.91 | +289.14 | -27.77 | +3.041 | +2.795 | 4.385 | 4.385 |
| S2 | 2026-05 | +240.64 | +238.30 | -2.33 | +2.241 | +2.241 | 4.858 | 4.858 |
| S2 | 2026-06 | -184.47 | -203.89 | -19.42 | -1.680 | -1.875 | 4.157 | 4.339 |
| S2 | 2026-07 | -90.06 | -171.97 | -81.91 | -0.834 | -1.612 | 3.549 | 3.884 |
| S2 | 2026-08 | +1.03 | -71.17 | -72.20 | +0.010 | -0.678 | 5.581 | 5.779 |
| S2 | 2026-09 (Teilmonat) | +68.00 | +1.32 | -66.67 | +0.635 | +0.013 | 7.005 | 7.005 |
| S2 | Drittel 1 | +563.21 | +460.73 | -102.48 | +5.632 | +4.607 | 10.841 | 11.653 |
| S2 | Drittel 2 | +232.60 | +209.13 | -23.47 | +2.202 | +1.999 | 6.668 | 6.853 |
| S2 | Drittel 3 | -21.04 | -241.82 | -220.78 | -0.195 | -2.266 | 8.558 | 9.073 |
| S3 | 2026-01 (Teilmonat) | -126.30 | -126.30 | +0.00 | -1.263 | -1.263 | 1.728 | 1.728 |
| S3 | 2026-02 | +288.05 | +237.99 | -50.06 | +2.917 | +2.410 | 7.550 | 7.550 |
| S3 | 2026-03 | +1121.91 | +1116.38 | -5.53 | +11.041 | +11.041 | 5.656 | 5.656 |
| S3 | 2026-04 | +777.96 | +770.58 | -7.38 | +6.895 | +6.863 | 2.482 | 2.482 |
| S3 | 2026-05 | +381.59 | +406.97 | +25.39 | +3.164 | +3.392 | 4.605 | 4.605 |
| S3 | 2026-06 | -217.01 | -216.35 | +0.66 | -1.744 | -1.744 | 4.150 | 4.150 |
| S3 | 2026-07 | +167.29 | +166.79 | -0.51 | +1.368 | +1.368 | 3.393 | 3.393 |
| S3 | 2026-08 | +83.17 | +287.37 | +204.21 | +0.671 | +2.326 | 3.629 | 3.791 |
| S3 | 2026-09 (Teilmonat) | +199.02 | +149.52 | -49.50 | +1.595 | +1.183 | 5.574 | 5.924 |
| S3 | Drittel 1 | +1602.30 | +1532.37 | -69.93 | +16.023 | +15.324 | 7.550 | 7.550 |
| S3 | Drittel 2 | +623.90 | +656.90 | +33.00 | +5.377 | +5.696 | 6.532 | 6.532 |
| S3 | Drittel 3 | +449.48 | +603.68 | +154.20 | +3.676 | +4.953 | 6.394 | 6.537 |
| S4 | 2026-01 (Teilmonat) | -165.13 | -165.13 | +0.00 | -1.651 | -1.651 | 1.867 | 1.867 |
| S4 | 2026-02 | +240.48 | +171.40 | -69.08 | +2.445 | +1.743 | 7.550 | 7.550 |
| S4 | 2026-03 | +793.48 | +788.04 | -5.44 | +7.875 | +7.875 | 6.576 | 6.576 |
| S4 | 2026-04 | +347.29 | +317.24 | -30.05 | +3.195 | +2.939 | 2.810 | 2.810 |
| S4 | 2026-05 | +188.88 | +190.49 | +1.61 | +1.684 | +1.714 | 5.218 | 5.218 |
| S4 | 2026-06 | -346.41 | -343.29 | +3.13 | -3.037 | -3.037 | 4.770 | 4.770 |
| S4 | 2026-07 | +4.84 | +4.79 | -0.04 | +0.044 | +0.044 | 3.393 | 3.393 |
| S4 | 2026-08 | -203.85 | -95.39 | +108.46 | -1.843 | -0.870 | 4.866 | 5.171 |
| S4 | 2026-09 (Teilmonat) | -67.28 | -132.09 | -64.82 | -0.620 | -1.215 | 7.120 | 7.585 |
| S4 | Drittel 1 | +947.98 | +839.33 | -108.65 | +9.480 | +8.393 | 7.550 | 7.550 |
| S4 | Drittel 2 | +110.60 | +119.42 | +8.82 | +1.010 | +1.102 | 8.097 | 8.097 |
| S4 | Drittel 3 | -266.29 | -222.69 | +43.60 | -2.408 | -2.032 | 8.161 | 8.183 |

### R1: Frischstarts an beiden Drittelgrenzen

Jeweils bis zum Paketende, vorheriger Marktdatenpräfix als Warmup, 10.000 USD, null BTC, keine geerbten Absichten/Peaks. Bekannte Daten, keine unabhängigen Bestätigungsfenster.

| Start UTC | Fall | Basis USD | E42 USD | Differenz USD | Dominanz | Basis DD Schluss / obere % | E42 DD Schluss / obere % |
|---|---|---:|---:|---:|---|---|---|
| 2026-04-13T08:00:00+00:00 | S0 | 11666.77 | 11551.93 | -114.84 | Basis | 6.375 / 7.230 | 6.661 / 7.524 |
| 2026-04-13T08:00:00+00:00 | S1 | 11357.32 | 11216.16 | -141.16 | Basis | 7.277 / 8.110 | 7.968 / 8.794 |
| 2026-04-13T08:00:00+00:00 | S2 | 10200.28 | 9968.75 | -231.53 | Basis | 12.053 / 12.655 | 13.105 / 13.699 |
| 2026-04-13T08:00:00+00:00 | S3 | 10925.15 | 11093.08 | +167.93 | Zielkonflikt / Gleichstand | 8.144 / 8.802 | 8.284 / 8.942 |
| 2026-04-13T08:00:00+00:00 | S4 | 9857.79 | 9904.73 | +46.94 | Zielkonflikt / Gleichstand | 12.791 / 13.180 | 12.811 / 13.232 |
| 2026-07-06T20:00:00+00:00 | S0 | 10794.01 | 10682.93 | -111.08 | Basis | 6.375 / 7.230 | 6.529 / 7.230 |
| 2026-07-06T20:00:00+00:00 | S1 | 10626.06 | 10494.35 | -131.71 | Basis | 6.816 / 7.408 | 6.985 / 7.578 |
| 2026-07-06T20:00:00+00:00 | S2 | 9980.51 | 9773.36 | -207.15 | Basis | 8.558 / 9.139 | 9.073 / 9.436 |
| 2026-07-06T20:00:00+00:00 | S3 | 10367.64 | 10495.25 | +127.61 | Zielkonflikt / Gleichstand | 6.394 / 7.165 | 6.537 / 7.307 |
| 2026-07-06T20:00:00+00:00 | S4 | 9759.20 | 9796.79 | +37.59 | Zielkonflikt / Gleichstand | 8.161 / 8.670 | 8.183 / 8.724 |

Vollständige Cash/BTC/Restkosten/Gebühren/Exposition, Monats-/Drittelstände und größte Risikoepisoden auch für jeden Frischstart: Paket-`results.json` und `periods.csv`.

### R1: größte Rückgangsphasen des vollständigen Pfads

High/Low-Zeiten bezeichnen die Kerze mit diesem Schlusszeitpunkt, keinen beobachteten Intrabar-Zeitpunkt. Zusätzlich sind die drei größten Peak-bis-Erholung-Episoden je Maß im Ergebnis-JSON gespeichert.

| Fall / Zeile | Maß | DD % | Peak UTC / Bewertung | Tief UTC / Bewertung |
|---|---|---:|---|---|
| S0 Basis | Schluss | 7.9166 | 2026-03-17T00:00:00+00:00 / close | 2026-04-02T04:00:00+00:00 / close |
| S0 Basis | untere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S0 Basis | obere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S0 E42 | Schluss | 8.4177 | 2026-03-17T00:00:00+00:00 / close | 2026-04-02T04:00:00+00:00 / close |
| S0 E42 | untere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S0 E42 | obere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S1 Basis | Schluss | 8.4989 | 2026-03-17T00:00:00+00:00 / close | 2026-04-03T04:00:00+00:00 / close |
| S1 Basis | untere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S1 Basis | obere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S1 E42 | Schluss | 9.0636 | 2026-03-17T00:00:00+00:00 / close | 2026-04-03T04:00:00+00:00 / close |
| S1 E42 | untere Grenze | 10.2437 | 2026-03-17T04:00:00+00:00 / high | 2026-04-03T16:00:00+00:00 / low |
| S1 E42 | obere Grenze | 10.2437 | 2026-03-17T04:00:00+00:00 / high | 2026-04-03T16:00:00+00:00 / low |
| S2 Basis | Schluss | 12.0534 | 2026-05-11T00:00:00+00:00 / close | 2026-08-19T08:00:00+00:00 / close |
| S2 Basis | untere Grenze | 12.6548 | 2026-05-14T20:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |
| S2 Basis | obere Grenze | 12.6548 | 2026-05-14T20:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |
| S2 E42 | Schluss | 13.1053 | 2026-05-11T00:00:00+00:00 / close | 2026-08-19T08:00:00+00:00 / close |
| S2 E42 | untere Grenze | 13.6995 | 2026-05-14T20:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |
| S2 E42 | obere Grenze | 13.6995 | 2026-05-14T20:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |
| S3 Basis | Schluss | 8.1439 | 2026-05-11T00:00:00+00:00 / close | 2026-08-18T08:00:00+00:00 / close |
| S3 Basis | untere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S3 Basis | obere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S3 E42 | Schluss | 8.2843 | 2026-05-11T00:00:00+00:00 / close | 2026-08-18T08:00:00+00:00 / close |
| S3 E42 | untere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S3 E42 | obere Grenze | 9.9428 | 2026-02-26T00:00:00+00:00 / high | 2026-02-28T08:00:00+00:00 / low |
| S4 Basis | Schluss | 12.7905 | 2026-05-11T00:00:00+00:00 / close | 2026-09-20T08:00:00+00:00 / close |
| S4 Basis | untere Grenze | 13.1803 | 2026-05-11T00:00:00+00:00 / high | 2026-09-20T04:00:00+00:00 / low |
| S4 Basis | obere Grenze | 13.1803 | 2026-05-11T00:00:00+00:00 / high | 2026-09-20T04:00:00+00:00 / low |
| S4 E42 | Schluss | 12.8109 | 2026-05-11T00:00:00+00:00 / close | 2026-08-19T08:00:00+00:00 / close |
| S4 E42 | untere Grenze | 13.2317 | 2026-05-11T00:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |
| S4 E42 | obere Grenze | 13.2317 | 2026-05-11T00:00:00+00:00 / high | 2026-08-19T08:00:00+00:00 / low |

### R1: Zeitstabilität und Konzentration

- S0: 4 positive, 4 negative, 1 unveränderte Monatsbeiträge; größte Monatsdifferenz -66.25 bis +54.80 USD.
- S1: 2 positive, 6 negative, 1 unveränderte Monatsbeiträge; größte Monatsdifferenz -70.51 bis +43.26 USD.
- S2: 1 positive, 7 negative, 1 unveränderte Monatsbeiträge; größte Monatsdifferenz -81.91 bis +0.23 USD.
- S3: 3 positive, 5 negative, 1 unveränderte Monatsbeiträge; größte Monatsdifferenz -50.06 bis +204.21 USD.
- S4: 3 positive, 5 negative, 1 unveränderte Monatsbeiträge; größte Monatsdifferenz -69.08 bis +108.46 USD.

Alle Positionszyklen mit Gewinn/Verlust, Gebühren, Zeitraum und Schlussstatus stehen in `cycles.json`; unterschiedliche Zyklen sind nicht automatisch paarbar.

## Belege, Datenqualität und Grenzen

Rohdaten/Verfügbarkeit: `data-manifest.json` hält die erste Archivprüfung fest (damals R1 unvollständig). Nach ausdrücklicher Freigabe von GitHub-Läufen wurde der getrennte Einmallauf mit dem vorhandenen Coinalyze-Secret ausgeführt; `r1-manifest.json` ist der ergänzte maßgebliche Paketbeleg. 
[GitHub-Datenlauf 36592684701](https://github.com/szoceikaiser/btc-signal-app/actions/runs/36592684701) enthält ausschließlich historische Marktdaten-GETs; alle Rohantworten und Hashes sind gesichert. Der abweichende Workflowname löst Pages nicht aus, Tokenrechte nur lesend, keine Telegram-Zugangsdaten.

OHLC/Spot-CVD: Binance Vision BTCUSDT; Futures-CVD/OI/Liquidationen/Long-Anteil: Coinalyze BTCUSDT_PERP.A (Binance, kein Börsenaggregat); Funding: Kraken PF_XBTUSD, stündlicher relativer Satz ×8 gemäß unverändertem Altmodell. Funding ist Eingabe der Strategie, kein Spot-Funding-Cashflow. Rohwerte nach Stichtag werden nicht als frühere Werte verwendet. 
R0-Warmup bleibt exakt, einschließlich vorhandener Defaults/fortgeschriebener Werte vor dem Handelsstart. Keine neue Interpolation. Der Überlappungscheck bestätigt die letzte abgeschlossene R0-Kerze; er beweist nicht Revisionsfreiheit der gesamten älteren Historie.

Erste hier belegbare R1-Version stammt vom späteren GET im GitHub-Lauf; rechtzeitige damalige Veröffentlichung bleibt unbekannt. R0 fehlt die vollständige ursprüngliche API-Rohantwort/Vintage-Kette. Das erlaubt einen bedingten historischen Modellvergleich, keinen Beleg erreichbarer Live-Fills; auch i+2 beweist keine ausreichende reale Liefer-/Menschen-/Brokerlatenz.

`search-inventory.json`: E43-Kontrollauswahl, E44-Kombinationen, Audit und Korrekturen lesend inventarisiert; versionierte Konfigurationen mit Code-/Datenhash dedupliziert. Frühere Gesamtfamilie unvollständig. **U2/Auswahlbereinigung nicht belegt.** Kein Reality-Check/SPA berechnet, keine zusätzlichen Suchalternativen neu gemessen und keine Mischung alter Signalbänder mit V1-Renditen.

Statistikgrundlage: [Politis & Romano, The Stationary Bootstrap](https://doi.org/10.1080/01621459.1994.10476870). Die schwache Stationaritäts-/Abhängigkeitsannahme ist hier keine bewiesene Eigenschaft. Keine persönliche Nutzenhürde oder absolute Risikotoleranz angenommen.

741 reguläre Tests (728 alte unverändert +13 neu), sechs synthetische Statistik-Testgruppen und 15 neue gezielte Schutzproben. Erhalten: F17 16, F13 16, Etappe 4 23, 3b 19, D01 6, F09 3. Protokolle in `checks/`. Unabhängige Rechnung übernimmt ausgewählte Kandidaten bzw. ausgeführte Mengen; sie bestätigt Buchführung, nicht Strategieauswahl oder historische Verfügbarkeit.

Live-Engine, Konfiguration, site, Versandliste, alte Ausführungs-/Positions-/Checkpointformate und Verträge unverändert. Nur eigener Zweig; kein main-Merge/Push, keine Orders oder Nachrichten. V1-Fills simuliert, historische Signalbänder Diagnostik, manueller Bestand unbekannt. F13-ID bleibt lokale Identität; uncertain blockiert, kein Reset/erneuter Versand bestätigter oder unklarer Nachrichten, keine Exactly-once-Zusage. Ephemerer Runnerverlust vor Git-Persistenz bleibt offen. V2/Shorts/E41.6 getrennt. **Kein Live-Go.**

Exakter Remote-HEAD, CI, Bundle/ZIP-Hashes, vollständiger Restore, Test-/Schutzproben und identische unabhängige Neuberechnung stehen nach Abschluss in `audit-backups/nach-6-abschluss-<SHA>/ABSCHLUSS.json`. Weitere Arbeit nur separat.
