# Gemeinsame Kombinationsmatrix

Vorfestlegung: `gitter-plan.json`, Commit e7e92d3, vor Beginn der Messung. 79 eindeutige Konfigurationen; fünf vollständige 2×2×2-Gitter, Einzelgegenproben und abhängige Einstellungen. Alle Zeilen gegen identische Live-Parameter von main 89885adc.

Eingaben: SHA-256 ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a. Zeitraum 18.01.–27.09.2026 (letzter abgeschlossener 4h-Balken beginnt 04:00 UTC). D01: laufende letzte Kerze entfernt. F09: unabhängige Buchführung entfernt winzige Bestandsreste. Unveränderte ursprüngliche Simulation steht zusätzlich in jedem `grid/Vxxx.json`.

**Die Level-Rendite bleibt eine hypothetische Vergleichszahl:** zahlreiche Entscheidungen stehen erst am Kerzenschluss fest. Historische Berührung eines Levels beweist keine damals ausführbare Order. Schluss-DD ist der Rückgang an 4h-Schlusskursen; kein maximaler Intraday-Verlust. Für kausale Ausführungsmodelle liegen zusätzlich OHLC-Risikointervalle in den JSON-Dateien.

Kosten: 0,1 % pro Order. Nächste Eröffnung: zusätzlich 0,05 % ungünstigerer Preis pro Seite, Verzögerung 0 Stunden nach Signal-Verfügbarkeit. Spalte „+4h, teuer“: eine weitere Kerze Verzögerung, 0,2 % Gebühr und 0,1 % Preisabschlag/-aufschlag. Dies sind vorab bestimmte Stressannahmen, keine gemessenen Live-Ausführungen. Kaufanzahl plus Verkaufsanzahl zählt nur Orders mit positivem Volumen; Nullorders und gesamte Signale getrennt im Datensatz. H1/H2 starten jeweils mit neuem Kapital und leerem Bestand.

| ID | Änderung gegenüber live | Gruppe | Level % | H1 / H2 % | Schluss-DD % | Gebühren USD | Orders / Null | Ø investiert % | nächste Eröffnung % | +4h, teuer % |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V000 | Live-Basis | G1, G2, G3, G4, G5, baseline | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V001 | rest_halten=True | G1, single | 36.72 | 20.50 / 13.46 | -8.56 | 516.63 | 183 / 14 | 37.05 | 32.67 | 20.71 |
| V002 | verkauf_faktor=0.67 | G1, single | 36.13 | 24.66 / 9.21 | -8.63 | 521.38 | 190 / 15 | 38.21 | 30.92 | 17.62 |
| V003 | rest_halten=True, verkauf_faktor=0.67 | G1 | 37.90 | 18.16 / 16.71 | -11.07 | 439.83 | 175 / 22 | 46.10 | 34.03 | 22.34 |
| V004 | ausbruch_ruecktest=True | G1, G2, G5, single | 35.42 | 25.37 / 8.01 | -8.68 | 631.01 | 227 / 14 | 36.77 | 29.73 | 15.22 |
| V005 | rest_halten=True, ausbruch_ruecktest=True | G1 | 34.57 | 20.51 / 11.67 | -9.89 | 563.14 | 202 / 13 | 38.48 | 30.64 | 18.08 |
| V006 | ausbruch_ruecktest=True, verkauf_faktor=0.67 | G1 | 34.85 | 25.25 / 7.66 | -9.06 | 592.55 | 222 / 16 | 39.27 | 29.12 | 15.50 |
| V007 | rest_halten=True, ausbruch_ruecktest=True, verkauf_faktor=0.67 | G1 | 34.66 | 17.63 / 14.47 | -11.60 | 470.81 | 188 / 25 | 47.09 | 30.71 | 19.77 |
| V008 | trail_stop=False, high_exit=off | G2 | 37.57 | 24.05 / 10.90 | -8.85 | 489.89 | 139 / 24 | 40.40 | 32.20 | 19.43 |
| V009 | high_exit=off | G2, single | 37.57 | 24.05 / 10.90 | -8.85 | 489.89 | 139 / 24 | 40.40 | 32.20 | 19.43 |
| V010 | trail_stop=False | G2, single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V011 | trail_stop=False, high_exit=off, ausbruch_ruecktest=True | G2 | 39.14 | 24.90 / 11.40 | -8.85 | 524.42 | 152 / 25 | 40.76 | 33.36 | 19.94 |
| V012 | high_exit=off, ausbruch_ruecktest=True | G2 | 39.14 | 24.90 / 11.40 | -8.85 | 524.42 | 152 / 25 | 40.76 | 33.36 | 19.94 |
| V013 | trail_stop=False, ausbruch_ruecktest=True | G2 | 35.42 | 25.37 / 8.01 | -8.68 | 631.01 | 227 / 14 | 36.77 | 29.73 | 15.22 |
| V014 | stop_rueckeroberung=0, bein_richtung=auto, zonen_nachziehen=False | G3 | 23.71 | 16.74 / 5.97 | -7.71 | 498.89 | 186 / 16 | 33.19 | 20.35 | 13.38 |
| V015 | stop_rueckeroberung=0, bein_richtung=auto | G3 | 23.30 | 17.76 / 4.71 | -7.71 | 508.57 | 191 / 18 | 32.85 | 19.69 | 10.83 |
| V016 | stop_rueckeroberung=0, zonen_nachziehen=False | G3 | 32.25 | 18.87 / 11.26 | -8.18 | 479.03 | 171 / 15 | 34.93 | 29.27 | 17.24 |
| V017 | stop_rueckeroberung=0 | G3, single | 31.54 | 19.65 / 9.93 | -8.18 | 531.02 | 189 / 17 | 34.77 | 28.47 | 17.65 |
| V018 | bein_richtung=auto, zonen_nachziehen=False | G3 | 26.29 | 18.95 / 6.17 | -9.44 | 504.78 | 187 / 16 | 34.16 | 21.13 | 13.28 |
| V019 | bein_richtung=auto | G3, single | 25.87 | 19.99 / 4.90 | -9.44 | 514.29 | 192 / 18 | 33.83 | 20.46 | 10.74 |
| V020 | zonen_nachziehen=False | G3, single | 30.55 | 17.13 / 11.46 | -8.29 | 473.97 | 172 / 12 | 35.50 | 27.61 | 15.90 |
| V021 | flush_entry=off, buy_ladder=False, liq_entry=off | G4 | 20.13 | 15.62 / 3.90 | -7.00 | 262.75 | 116 / 3 | 20.66 | 12.44 | 7.38 |
| V022 | flush_entry=off, buy_ladder=False | G4 | 20.19 | 15.87 / 3.72 | -7.55 | 381.09 | 145 / 7 | 29.26 | 13.01 | 8.11 |
| V023 | buy_ladder=False, liq_entry=off | G4 | 31.38 | 21.07 / 8.51 | -7.00 | 353.87 | 137 / 3 | 23.18 | 26.84 | 15.12 |
| V024 | buy_ladder=False | G4, single | 35.78 | 23.44 / 10.00 | -8.02 | 510.51 | 173 / 5 | 33.42 | 30.26 | 17.83 |
| V025 | flush_entry=off, liq_entry=off | G4 | 26.64 | 21.64 / 4.11 | -7.55 | 348.82 | 143 / 5 | 26.20 | 18.75 | 11.54 |
| V026 | flush_entry=off | G4, single | 21.88 | 17.64 / 3.61 | -7.55 | 421.33 | 166 / 15 | 32.13 | 16.11 | 10.17 |
| V027 | liq_entry=off | G4, single | 37.50 | 26.59 / 8.62 | -7.55 | 445.20 | 162 / 5 | 27.96 | 32.75 | 18.17 |
| V028 | muster_oi=btc | G5, single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V029 | muster_cvd=usd | G5, single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V030 | muster_cvd=usd, muster_oi=btc | G5 | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V031 | muster_oi=btc, ausbruch_ruecktest=True | G5 | 35.60 | 25.37 / 8.16 | -8.68 | 631.43 | 228 / 14 | 36.84 | 29.91 | 15.84 |
| V032 | muster_cvd=usd, ausbruch_ruecktest=True | G5 | 35.42 | 25.37 / 8.01 | -8.68 | 631.01 | 227 / 14 | 36.77 | 29.73 | 15.22 |
| V033 | muster_cvd=usd, muster_oi=btc, ausbruch_ruecktest=True | G5 | 35.60 | 25.37 / 8.16 | -8.68 | 631.43 | 228 / 14 | 36.84 | 29.91 | 15.84 |
| V034 | bias_long=False | single | 0.00 | 0.00 / 0.00 | 0.00 | 0.00 | 0 / 0 | 0.00 | 0.00 | 0.00 |
| V035 | bias_short=True | single | -7.14* | nicht belastbar | nicht belastbar | nicht erhoben | nicht erhoben | nicht erhoben | nicht erhoben | nicht erhoben |
| V036 | flush_entry=t1 | single | 31.56 | 23.25 / 6.74 | -7.55 | 506.76 | 197 / 13 | 33.77 | 21.81 | 14.42 |
| V037 | tp_ladder=False | single | 36.88 | 24.85 / 9.64 | -8.41 | 538.20 | 168 / 14 | 37.06 | 30.35 | 16.55 |
| V038 | trend_filter=True | single | 11.70 | 7.06 / 4.33 | -7.55 | 109.75 | 45 / 6 | 12.76 | 11.03 | 6.08 |
| V039 | trend_ema=50 | single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V040 | strict_confirm=True | single | 28.76 | 26.03 / 2.17 | -8.42 | 437.98 | 164 / 3 | 27.68 | 24.27 | 13.67 |
| V041 | confluence=True | single | 14.70 | 7.66 / 6.54 | -12.50 | 495.82 | 176 / 18 | 31.14 | 11.22 | -0.20 |
| V042 | conditional_stop=True | single | 31.24 | 19.39 / 9.92 | -8.83 | 534.63 | 190 / 22 | 36.47 | 26.96 | 16.17 |
| V043 | release_stale_rest=True | single | 34.89 | 22.48 / 10.13 | -8.29 | 542.14 | 191 / 14 | 35.23 | 29.90 | 17.17 |
| V044 | liq_exit=spike | single | 33.56 | 18.86 / 12.37 | -8.29 | 563.06 | 239 / 14 | 28.23 | 29.22 | 14.35 |
| V045 | liq_exit=zone | single | 28.51 | 19.93 / 7.15 | -7.55 | 583.65 | 255 / 12 | 27.65 | 23.13 | 8.84 |
| V046 | liq_exit=both | single | 27.63 | 19.76 / 6.57 | -7.55 | 583.19 | 255 / 13 | 28.09 | 22.35 | 8.21 |
| V047 | high_exit=weak | single | 33.05 | 20.98 / 9.98 | -8.27 | 532.86 | 190 / 14 | 35.42 | 28.04 | 16.32 |
| V048 | liq_entry=filter | single | 31.83 | 20.70 / 9.23 | -7.55 | 430.48 | 154 / 4 | 28.11 | 26.81 | 12.83 |
| V049 | block_unhealthy=True | single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V050 | muster5_entry=True | single | 35.49 | 22.11 / 10.96 | -8.29 | 553.75 | 197 / 15 | 35.89 | 30.51 | 18.53 |
| V051 | muster5_halten=leiter | single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V052 | muster5_halten=alle | single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V053 | stop_puffer_pct=0.005 | single | 37.01 | 22.25 / 12.07 | -8.63 | 514.44 | 185 / 14 | 37.79 | 33.54 | 20.11 |
| V054 | stop_rueckeroberung=3 | single | 34.48 | 21.91 / 10.31 | -7.86 | 524.19 | 186 / 16 | 36.38 | 30.21 | 18.17 |
| V055 | stop_auf_docht=True | single | 33.24 | 22.84 / 8.47 | -7.95 | 601.60 | 203 / 20 | 32.89 | 29.10 | 16.93 |
| V056 | confirm_t1=True | single | 35.91 | 22.81 / 10.66 | -8.20 | 565.29 | 187 / 14 | 35.57 | 30.80 | 15.10 |
| V057 | cooldown_h=48 | single | 34.16 | 21.82 / 10.13 | -8.11 | 525.03 | 188 / 14 | 35.26 | 30.43 | 17.65 |
| V058 | cooldown_h=48.0 | single | 34.16 | 21.82 / 10.13 | -8.11 | 525.03 | 188 / 14 | 35.26 | 30.43 | 17.65 |
| V059 | min_stop_pct=0.0 | single | 20.49 | 18.28 / 1.86 | -12.44 | 736.91 | 244 / 20 | 39.77 | 14.66 | 2.67 |
| V060 | no_flip=False | single | 36.62 | 23.61 / 10.53 | -7.99 | 550.07 | 192 / 15 | 36.47 | 30.70 | 17.29 |
| V061 | freeze_targets=True | single | 30.32 | 20.03 / 8.57 | -8.29 | 469.61 | 159 / 14 | 36.11 | 25.48 | 13.38 |
| V062 | min_bein_pct=0.0 | single | 27.94 | 20.54 / 6.14 | -8.30 | 509.53 | 187 / 14 | 25.73 | 25.14 | 14.26 |
| V063 | bein_wahl=groesstes | single | 15.43 | 17.24 / -1.54 | -11.61 | 346.19 | 120 / 16 | 28.89 | 11.46 | 2.52 |
| V064 | be_im_plus=True | single | 18.52 | 8.08 / 9.66 | -9.46 | 849.29 | 288 / 21 | 25.54 | 7.34 | -8.61 |
| V065 | widerstand_exit=on | single | 29.12 | 18.08 / 9.36 | -8.11 | 546.58 | 221 / 15 | 31.18 | 25.30 | 13.01 |
| V066 | neustart_mit_rest=False | single | 36.83 | 23.61 / 10.69 | -8.29 | 552.32 | 190 / 16 | 32.35 | 31.42 | 19.03 |
| V067 | zonen_1d=True | single | 31.51 | 28.31 / 1.94 | -17.91 | 532.28 | 194 / 13 | 48.00 | 25.80 | 13.28 |
| V068 | pivot_n_1d=8 | single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V069 | pivot_n_1d=12 | single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V070 | ampel_filter=klein | single | 31.54 | 21.95 / 7.87 | -7.55 | 448.63 | 195 / 10 | 30.55 | 26.89 | 14.71 |
| V071 | ampel_filter=gross | single | 36.19 | 24.17 / 9.68 | -7.55 | 483.30 | 198 / 7 | 30.51 | 31.05 | 20.92 |
| V072 | ampel_filter=immer | single | 25.54 | 18.61 / 5.84 | -6.57 | 307.38 | 203 / 2 | 20.99 | 22.26 | 14.04 |
| V073 | high_exit_hist=live | single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V074 | ruecktest_fenster=6 | single | 36.13 | 23.61 / 10.13 | -8.29 | 545.01 | 191 / 14 | 35.42 | 31.09 | 17.97 |
| V075 | zonen_1d=True, pivot_n_1d=8 | dependent | 11.62 | 18.70 / -5.96 | -20.77 | 434.70 | 174 / 13 | 49.97 | 12.09 | 0.69 |
| V076 | zonen_1d=True, pivot_n_1d=12 | dependent | 16.58 | 22.48 / -4.82 | -17.75 | 467.22 | 185 / 13 | 40.98 | 17.28 | 5.09 |
| V077 | trend_filter=True, trend_ema=50 | dependent | 8.78 | 4.49 / 4.11 | -9.57 | 242.76 | 97 / 6 | 21.68 | 7.74 | 1.92 |
| V078 | ausbruch_ruecktest=True, ruecktest_fenster=6 | robust | 35.99 | 25.90 / 8.01 | -8.29 | 627.35 | 225 / 14 | 36.73 | 30.31 | 15.72 |

* Eine Zeile mit Short-Handel ist wegen F02 (fehlende Kapitalbindung/Margin, kein Funding) ausdrücklich keine vergleichbare unverschuldete Rendite. Alle Details und Signale: `grid/Vxxx.json`.

## Hälften und Konzentration

| ID | Δ H1 Punkte | Δ H2 Punkte | Kleinster verzinster Vorteil ohne einen Monat, Punkte | beide ≥1 |
|---|---:|---:|---:|---|
| V000 | 0.00 | 0.00 | 0.00 | False |
| V001 | -3.11 | 3.33 | -1.74 | False |
| V002 | 1.05 | -0.92 | -1.41 | False |
| V003 | -5.45 | 6.58 | -6.01 | False |
| V004 | 1.76 | -2.12 | -1.64 | False |
| V005 | -3.10 | 1.54 | -2.59 | False |
| V006 | 1.64 | -2.47 | -3.20 | False |
| V007 | -5.98 | 4.34 | -7.88 | False |
| V008 | 0.44 | 0.77 | -0.88 | False |
| V009 | 0.44 | 0.77 | -0.88 | False |
| V010 | 0.00 | 0.00 | 0.00 | False |
| V011 | 1.29 | 1.28 | 0.74 | True |
| V012 | 1.29 | 1.28 | 0.74 | True |
| V013 | 1.76 | -2.12 | -1.64 | False |
| V014 | -6.87 | -4.16 | -15.47 | False |
| V015 | -5.85 | -5.42 | -15.84 | False |
| V016 | -4.74 | 1.13 | -5.23 | False |
| V017 | -3.95 | -0.20 | -5.96 | False |
| V018 | -4.66 | -3.96 | -13.13 | False |
| V019 | -3.62 | -5.23 | -13.51 | False |
| V020 | -6.48 | 1.33 | -7.13 | False |
| V021 | -7.99 | -6.23 | -17.88 | False |
| V022 | -7.74 | -6.41 | -16.48 | False |
| V023 | -2.54 | -1.62 | -7.45 | False |
| V024 | -0.17 | -0.13 | -1.47 | False |
| V025 | -1.97 | -6.02 | -11.22 | False |
| V026 | -5.97 | -6.52 | -14.72 | False |
| V027 | 2.98 | -1.51 | -0.76 | False |
| V028 | 0.00 | 0.00 | 0.00 | False |
| V029 | 0.00 | 0.00 | 0.00 | False |
| V030 | 0.00 | 0.00 | 0.00 | False |
| V031 | 1.76 | -1.97 | -1.46 | False |
| V032 | 1.76 | -2.12 | -1.64 | False |
| V033 | 1.76 | -1.97 | -1.46 | False |
| V034 | -23.61 | -10.13 | -40.65 | False |
| V036 | -0.36 | -3.39 | -5.78 | False |
| V037 | 1.24 | -0.49 | -0.58 | False |
| V038 | -16.55 | -5.80 | -25.25 | False |
| V039 | 0.00 | 0.00 | 0.00 | False |
| V040 | 2.42 | -7.96 | -9.48 | False |
| V041 | -15.95 | -3.59 | -22.14 | False |
| V042 | -4.22 | -0.21 | -5.06 | False |
| V043 | -1.13 | 0.00 | -1.28 | False |
| V044 | -4.75 | 2.24 | -4.68 | False |
| V045 | -3.68 | -2.98 | -8.98 | False |
| V046 | -3.85 | -3.56 | -9.69 | False |
| V047 | -2.63 | -0.15 | -3.37 | False |
| V048 | -2.91 | -0.90 | -5.66 | False |
| V049 | 0.00 | 0.00 | 0.00 | False |
| V050 | -1.50 | 0.83 | -1.75 | False |
| V051 | 0.00 | 0.00 | 0.00 | False |
| V052 | 0.00 | 0.00 | 0.00 | False |
| V053 | -1.36 | 1.94 | -1.18 | False |
| V054 | -1.70 | 0.18 | -2.46 | False |
| V055 | -0.77 | -1.66 | -4.59 | False |
| V056 | -0.80 | 0.53 | -0.70 | False |
| V057 | -1.79 | 0.00 | -2.03 | False |
| V058 | -1.79 | 0.00 | -2.03 | False |
| V059 | -5.33 | -8.27 | -16.89 | False |
| V060 | 0.00 | 0.40 | -0.89 | False |
| V061 | -3.58 | -1.56 | -6.01 | False |
| V062 | -3.07 | -3.99 | -11.98 | False |
| V063 | -6.37 | -11.67 | -22.72 | False |
| V064 | -15.53 | -0.47 | -18.22 | False |
| V065 | -5.53 | -0.77 | -7.78 | False |
| V066 | 0.00 | 0.56 | -1.35 | False |
| V067 | 4.70 | -8.19 | -11.90 | False |
| V068 | 0.00 | 0.00 | 0.00 | False |
| V069 | 0.00 | 0.00 | 0.00 | False |
| V070 | -1.66 | -2.26 | -4.74 | False |
| V071 | 0.56 | -0.45 | -0.93 | False |
| V072 | -5.00 | -4.29 | -13.12 | False |
| V073 | 0.00 | 0.00 | 0.00 | False |
| V074 | 0.00 | 0.00 | 0.00 | False |
| V075 | -4.91 | -16.09 | -25.05 | False |
| V076 | -1.13 | -14.95 | -19.54 | False |
| V077 | -19.12 | -6.02 | -28.26 | False |
| V078 | 2.30 | -2.12 | -1.48 | False |

Ein bestandener Hälftenfilter ist keine Erfolgswahrscheinlichkeit. Die 79 Zeilen sind korreliert; schon früher wurden viele Varianten auf diesen Daten gewählt. 5 % pro Zeile wären bei unabhängigen 79 Nullhypothesen etwa vier zufällige Treffer. Die unbekannte Gesamtzahl historischer Versuche verhindert eine seriöse exakte nachträgliche Korrektur.

Nicht untersucht: das vollständige kartesische Produkt aller Schalter, neue nach Ergebnis ausgewählte Schwellen, Kombinationen mit archivisch nicht verfügbaren Mehrbörsen-/On-Chain-Rohdaten, echte Tick-Ausführung, Short-Funding. Neue Kombinationen außerhalb der fünf begründeten Gitter bedürfen einer eigenen Vorfestlegung und möglichst neuer Daten.
