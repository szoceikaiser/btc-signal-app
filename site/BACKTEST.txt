# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 18.01.2026-26.09.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2476 4h-Kerzen geladen · Stand: 2026-09-26 15:18 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 26.09.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation. **max. Rueckgang** = groesster Einbruch vom jeweiligen Hoch (Drawdown) — je naeher an 0, desto ruhiger der Verlauf. **Seit 28.08.2026 (E27) lueckenlos gemessen:** an jeder Kerze und an ihrem unguenstigsten Punkt (Tief bei Long, Hoch bei Short). Vorher zaehlten nur die Signalzeitpunkte — was das Konto zwischen zwei Signalen an Buchverlust erlebte, fehlte. **Alle Rueckgangszahlen aus Berichten vor diesem Datum sind deshalb zu freundlich und nicht mit den heutigen vergleichbar.** **Einsatz** = wie viel des Kapitals je Position hoechstens investiert wird (100 % = keine Reserve, 60 % = 40 % Pulver bleibt trocken; Furkan-Update Juli 2026). Recall = Aehnlichkeit zu Furkans Terminen IM Fenster, KEIN Gewinn.

**Lesehilfe zu den Namen:** `LIVE` ist die Abkuerzung fuer *nur Long + Kaufleiter + Flush core* — der Flush steckt also drin. Jede Zeile, die mit `LIVE +…` beginnt, baut darauf auf. Die Zeile *+Kaufleiter* ist dagegen OHNE Flush.

**Gegengeschaefte** (E25, Kaiser 28.08.2026) = Anzahl der 4h-Kerzen, in denen gleichzeitig aufgestockt UND teilverkauft wurde, meist zum selben Preis. An der Rendite ist das kaum abzulesen — der Backtest handelt beide Seiten zum exakten Signalpreis, netto bleibt die Tranchen-Differenz minus zwei Gebuehren. In der Praxis ist so ein Paar aber nicht ausfuehrbar: zwei Limit-Orders zum selben Preis heben sich auf, und die Telegram-Nachrichten widersprechen sich. Die Spalte misst also Umsetzbarkeit, nicht Gewinn. Der Schalter dagegen heisst `no_flip`.

**Aufwaerts** (E26) = Aufwaerts-Beteiligung: wie viel des Anstiegs die Variante in steigenden Monaten mitnimmt (Einzelheiten im Abschnitt weiter unten). Hoch ist gut. Die Rendite allein verraet das nicht — eine Variante kann glaenzend aussehen, weil sie in fallenden Monaten gewinnt, und in einer Rally trotzdem kaum mitkommen. Wer wissen will, ob ein Schalter grosse Anstiege besser einfaengt, schaut hier hin und nicht auf die Rendite. **Abwaerts** ist das Gegenstueck fuer fallende Monate — niedrig oder negativ ist gut. Die beiden gehoeren zusammen gelesen: Wer mehr vom Anstieg mitnimmt, ist laenger und groesser investiert und macht deshalb in aller Regel auch mehr vom Rueckgang mit. Steigt Aufwaerts, ohne dass Abwaerts mitsteigt, ist wirklich etwas gewonnen; steigen beide, wurde nur das Risiko erhoeht.

| Variante | Recall | Praez. | Rendite | max. Rueckgang | Einsatz | Signale | Gegen-
geschaefte | Auf-
waerts | Ab-
waerts |
|---|---|---|---|---|---|---|---|---|---|
| nur Long (Basis) | 47% | 38% | +9.4 % | -7.8 % | 100 % | 95 | 2 | 34 % | 16 % |
| +Kaufleiter | 47% | 35% | +14.6 % | -8.7 % | 100 % | 116 | 2 | 44 % | 16 % |
| +Flush core | 53% | 27% | +19.3 % | -14.7 % | 100 % | 174 | 2 | 54 % | 17 % |
| LIVE: nur Long +Kaufleiter +Flush core | 53% | 26% | +23.8 % | -15.5 % | 100 % | 199 | 2 | 62 % | 17 % |
| +Kaufleiter +Bed.Stop | 47% | 34% | +12.8 % | -9.6 % | 100 % | 127 | 2 | 40 % | 15 % |
| LIVE +Rest-Freigabe | 59% | 30% | +16.4 % | -15.5 % | 100 % | 210 | 2 | 55 % | 22 % |
| LIVE +Stop nachziehen | 59% | 28% | +22.1 % | -15.1 % | 100 % | 206 | 2 | 58 % | 16 % |
| LIVE +Stop nachziehen +Rest-Freigabe | 59% | 30% | +16.9 % | -15.1 % | 100 % | 212 | 2 | 55 % | 21 % |
| LIVE +Stop +Liq-Kaskade | 65% | 29% | +16.0 % | -13.2 % | 100 % | 254 | 8 | 44 % | 13 % |
| LIVE +Stop +Liq-Zonen | 71% | 30% | +14.8 % | -12.6 % | 100 % | 286 | 24 | 42 % | 13 % |
| LIVE +Stop +Liq beides | 71% | 30% | +14.8 % | -12.6 % | 100 % | 288 | 25 | 42 % | 13 % |
| MEINE Einstellung ohne Flush | 35% | 26% | +21.2 % | -9.9 % | 100 % | 227 | 0 | 31 % | -6 % |
| LIVE +Stop +Liq-Konfluenz aufstocken | 59% | 29% | +23.4 % | -15.7 % | 100 % | 253 | 4 | 60 % | 16 % |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 53% | 30% | +20.8 % | -15.4 % | 100 % | 185 | 1 | 62 % | 22 % |
| LIVE +Stop +Verkauf am letzten Hoch | 71% | 31% | +19.6 % | -13.3 % | 100 % | 261 | 17 | 47 % | 10 % |
| LIVE +Stop +Verkauf am schwachen Hoch | 65% | 30% | +19.8 % | -13.3 % | 100 % | 250 | 8 | 48 % | 11 % |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 59% | 28% | +14.3 % | -9.9 % | 60 % | 206 | 2 | 38 % | 11 % |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 59% | 28% | +11.8 % | -8.3 % | 50 % | 206 | 2 | 32 % | 9 % |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 59% | 28% | +20.8 % | -15.1 % | 100 % | 204 | 2 | 58 % | 18 % |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 59% | 28% | +24.7 % | -14.9 % | 100 % | 198 | 1 | 63 % | 16 % |
| LIVE +Stop +Sperre 48 h nach Stop | 53% | 29% | +25.8 % | -11.9 % | 100 % | 175 | 2 | 59 % | 11 % |
| LIVE +Stop +Mindest-Stopabstand 2 % | 47% | 30% | +26.7 % | -10.5 % | 100 % | 134 | 0 | 54 % | 6 % |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 47% | 33% | +20.2 % | -10.5 % | 100 % | 125 | 0 | 43 % | 6 % |
| LIVE +Stop +alle vier neuen Hebel | 41% | 32% | +16.1 % | -10.5 % | 100 % | 115 | 0 | 34 % | 3 % |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 47% | 32% | +29.4 % | -10.9 % | 100 % | 165 | 1 | 57 % | 5 % |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 53% | 29% | +28.5 % | -12.6 % | 100 % | 214 | 4 | 63 % | 11 % |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 59% | 35% | +30.7 % | -9.2 % | 100 % | 201 | 16 | 55 % | 2 % |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 59% | 33% | +24.0 % | -11.1 % | 100 % | 215 | 17 | 51 % | 7 % |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 59% | 34% | +21.7 % | -9.4 % | 100 % | 251 | 24 | 44 % | 5 % |
| NEU-LIVE +kein Gegengeschaeft je Kerze | 53% | 32% | +26.6 % | -9.5 % | 100 % | 199 | 0 | 49 % | 2 % |
| NEU-LIVE +Ziele festhalten | 59% | 36% | +29.2 % | -9.2 % | 100 % | 205 | 16 | 44 % | -6 % |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | 53% | 32% | +26.0 % | -9.5 % | 100 % | 206 | 0 | 42 % | -4 % |
| NEU-LIVE +Mindest-Bein 5 % | 65% | 37% | +25.4 % | -9.4 % | 100 % | 238 | 17 | 43 % | -1 % |
| NEU-LIVE +groesstes Bein | 29% | 69% | +8.3 % | -12.2 % | 100 % | 107 | 3 | 12 % | -4 % |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | 29% | 69% | +8.3 % | -12.2 % | 100 % | 107 | 3 | 12 % | -4 % |
| NEU-LIVE +Bein in Handelsrichtung | 53% | 32% | +27.7 % | -9.9 % | 100 % | 232 | 16 | 54 % | 5 % |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | 41% | 30% | +32.1 % | -9.9 % | 100 % | 235 | 16 | 44 % | -9 % |
| NEU-LIVE +Break-even im Plus | 53% | 30% | +14.9 % | -8.0 % | 100 % | 218 | 26 | 25 % | -3 % |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | 29% | 67% | +8.0 % | -11.1 % | 100 % | 166 | 17 | 13 % | -2 % |
| LIVE +Widerstand des Gegen-Beins | 65% | 38% | +21.7 % | -8.7 % | 100 % | 265 | 17 | 38 % | 0 % |
| LIVE +Widerstand statt Verkauf am letzten Hoch | 59% | 36% | +22.7 % | -9.1 % | 100 % | 223 | 4 | 42 % | 2 % |
| LIVE +Rest halten | 35% | 53% | +13.8 % | -9.4 % | 100 % | 78 | 4 | 23 % | -2 % |
| LIVE +Rest halten +Neustart mit Rest | 65% | 36% | +27.6 % | -9.4 % | 100 % | 234 | 16 | 48 % | 0 % |
| LIVE +Neustart mit Rest (ohne Halten) | 65% | 37% | +25.5 % | -9.4 % | 100 % | 237 | 15 | 44 % | -1 % |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | 41% | 24% | +17.7 % | -18.5 % | 100 % | 263 | 17 | 56 % | 21 % |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | 41% | 25% | +19.2 % | -19.0 % | 100 % | 238 | 18 | 61 % | 23 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | 59% | 33% | +23.4 % | -9.4 % | 100 % | 237 | 0 | 38 % | -3 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | 59% | 33% | +14.6 % | -9.4 % | 100 % | 217 | 0 | 29 % | 2 % |
| LIVE-heute +Neustart mit Rest | 59% | 33% | +23.0 % | -9.4 % | 100 % | 236 | 0 | 37 % | -3 % |
| LIVE-heute +Rueckeroberung vor dem Stop (1 Kerze) | 59% | 35% | +25.1 % | -10.9 % | 100 % | 240 | 0 | 46 % | 1 % |
| LIVE-heute +Trendfilter EMA200 | 12% | 27% | -8.8 % | -10.5 % | 100 % | 40 | 0 | -2 % | 14 % |
| LIVE-heute +Trendfilter EMA50 | 18% | 43% | +3.0 % | -10.4 % | 100 % | 114 | 0 | 4 % | -2 % |
| LIVE-heute +1D-Ebene grob (n=8) | 59% | 35% | -0.8 % | -21.8 % | 100 % | 239 | 0 | 52 % | 45 % |
| LIVE-heute +1D-Ebene fein (n=5, Gegenprobe zu E23) | 41% | 29% | +27.1 % | -18.9 % | 100 % | 262 | 0 | 72 % | 22 % |
| LIVE-heute +1D-Ebene sehr grob (n=12) | 65% | 35% | +4.0 % | -18.9 % | 100 % | 247 | 0 | 46 % | 33 % |
| LIVE-heute +Ampel klein bei unguenstig | 35% | 23% | +31.0 % | -9.9 % | 100 % | 244 | 0 | 45 % | -7 % |
| LIVE-heute +Ampel UMGEKEHRT (Gegenprobe) | 35% | 23% | +35.6 % | -9.9 % | 100 % | 244 | 0 | 50 % | -10 % **<-- beste** |
| LIVE-heute +immer halbe Tranche (Nullhypothese) | 35% | 23% | +25.4 % | -8.7 % | 100 % | 244 | 0 | 35 % | -8 % |
| LIVE-heute +Rest halten +Neustart mit Rest | 59% | 33% | +22.6 % | -9.4 % | 100 % | 229 | 0 | 38 % | -2 % |
| LIVE-heute +Muster 5 als Kauf-Bestaetigung | 35% | 23% | +35.2 % | -9.9 % | 100 % | 251 | 0 | 51 % | -8 % |
| LIVE-heute +Muster 5 haelt Zwischenverkaeufe | 35% | 23% | +35.3 % | -9.9 % | 100 % | 244 | 0 | 50 % | -9 % |
| LIVE-heute +Muster 5 haelt ALLE Teilverkaeufe | 35% | 23% | +35.3 % | -9.9 % | 100 % | 244 | 0 | 50 % | -9 % |
| LIVE-heute +Muster 5 sperrt Kaeufe (Bremse, Gegenprobe) | 35% | 23% | +35.3 % | -9.9 % | 100 % | 244 | 0 | 50 % | -9 % |
| LIVE-heute +Muster 5 Kauf UND Halten (zwei Unterschiede) | 35% | 23% | +35.2 % | -9.9 % | 100 % | 251 | 0 | 51 % | -8 % |
| LIVE bis 21.09.2026 (Stop ohne Rueckeroberung) | 35% | 21% | +30.8 % | -9.9 % | 100 % | 248 | 0 | 42 % | -9 % |
| LIVE-heute +Rueckeroberung 3 statt 1 Kerze (Robustheit) | 35% | 23% | +34.2 % | -9.9 % | 100 % | 244 | 0 | 48 % | -9 % |
| LIVE-heute +Bein in Handelsrichtung | 35% | 23% | +35.3 % | -9.9 % | 100 % | 244 | 0 | 50 % | -9 % |
| LIVE bis 26.09.2026 (ohne Bein-Richtung) | 59% | 35% | +25.1 % | -10.9 % | 100 % | 240 | 0 | 46 % | 1 % |
| LIVE-heute +Muster 2 in Dollar (E43.3) | 35% | 23% | +35.3 % | -9.9 % | 100 % | 244 | 0 | 50 % | -9 % |
| LIVE-heute +OI in Kontrakten (E43.4) | 35% | 23% | +35.3 % | -9.9 % | 100 % | 227 | 0 | 50 % | -9 % |
| LIVE-heute +Pivot-Hoch nur letzte 1.300 Kerzen (A5) | 35% | 23% | +35.3 % | -9.9 % | 100 % | 244 | 0 | 50 % | -9 % |
| LIVE-heute +Rest halten (E43.6) | 41% | 25% | +34.5 % | -9.9 % | 100 % | 236 | 0 | 50 % | -7 % |
| LIVE-heute +Strenge Bestaetigung (E43.6) | 41% | 21% | +28.5 % | -9.9 % | 100 % | 206 | 0 | 43 % | -6 % |
| LIVE-heute +Bestaetigung am 0.5-Level (E43.6) | 35% | 24% | +34.9 % | -9.9 % | 100 % | 240 | 0 | 52 % | -7 % |
| LIVE-heute +Sperrfrist nach Stop 48h (E43.6) | 35% | 23% | +33.4 % | -9.9 % | 100 % | 244 | 0 | 47 % | -9 % |
| LIVE-heute +Break-even im Plus (E43.8) | 59% | 30% | +18.0 % | -10.2 % | 100 % | 348 | 0 | 33 % | 1 % |
| LIVE-heute +Rest-Freigabe bei neuer Struktur (E43.8) | 35% | 23% | +34.6 % | -9.9 % | 100 % | 244 | 0 | 51 % | -7 % |
| Long+Short (Ref) | 29% | 42% | -4.0 % | -21.2 % | 100 % | 95 | 0 | -23 % | -17 % |

## Beste Kombination (nach Rendite): LIVE-heute +Ampel UMGEKEHRT (Gegenprobe)

- Kauf-Trigger getroffen: 3/7 (im Fenster) — 20.01.26, 23.03.26, 27.03.26
- Kauf verpasst: 29.01.26, 30.01.26, 31.01.26, 28.02.26
- Verkauf-Trigger getroffen: 3/10 (im Fenster) — 17.03.26, 08.04.26, 22.04.26
- Verkauf verpasst: 25.01.26, 02.02.26, 23.02.26, 28.02.26, 02.03.26, 14.04.26, 17.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,563 €** (+35.6 %) · Buy&Hold im Fenster: -10.3 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,555 € · 99 Abschluesse, 66 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*LIVE-heute +Bein in Handelsrichtung*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2026-01 | -322 € | -3.2 % | -322 € | -3.2 % |
| 2026-02 | +355 € | +3.7 % | +355 € | +3.7 % |
| 2026-03 | +1,107 € | +11.0 % | +671 € | +6.7 % |
| 2026-04 | +714 € | +6.4 % | +745 € | +7.0 % |
| 2026-05 | +507 € | +4.3 % | +315 € | +2.8 % |
| 2026-06 | +15 € | +0.1 % | +14 € | +0.1 % |
| 2026-07 | +404 € | +3.3 % | +384 € | +3.3 % |
| 2026-08 | +300 € | +2.4 % | +132 € | +1.1 % |
| 2026-09 | +453 € | +3.5 % | -178 € | -1.4 % |

Monate im Plus: **8 von 9** (live) gegen **7 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Was faengt die Engine von der Marktbewegung ein?

Dieselben Monate, jetzt neben der Bitcoin-Bewegung. **Aufwaerts-Beteiligung** = wie viel des Anstiegs die Engine in steigenden Monaten mitnimmt (hoch ist gut). **Abwaerts-Beteiligung** = wie viel des Rueckgangs sie in fallenden Monaten mitmacht (niedrig oder negativ ist gut).

| Monat | Bitcoin | Engine | davon eingefangen |
|---|---|---|---|
| 2026-01 | -15.9 % | -3.2 % | — |
| 2026-02 | -14.9 % | +3.7 % | — |
| 2026-03 | +2.0 % | +11.0 % | 563 % |
| 2026-04 | +11.8 % | +6.4 % | 54 % |
| 2026-05 | -3.5 % | +4.3 % | — |
| 2026-06 | -20.4 % | +0.1 % | — |
| 2026-07 | +7.3 % | +3.3 % | 45 % |
| 2026-08 | +24.9 % | +2.4 % | 9 % |
| 2026-09 | +6.9 % | +3.5 % | 50 % |

**Aufwaerts-Beteiligung: 50 %** — in den 5 steigenden Monaten legte Bitcoin zusammen +52.9 % zu, die Engine +26.5 %.

**Abwaerts-Beteiligung: -9 %** — in den 4 fallenden Monaten verlor Bitcoin zusammen -54.8 %, die Engine +4.8 %.

**So ist das zu lesen:** Die Gesamtrendite verrraet nicht, WO sie herkommt. Eine Strategie kann glaenzend aussehen, weil sie in fallenden Maerkten gewinnt, und trotzdem in einer Rally kaum mitkommen. Die Spalte 'davon eingefangen' zeigt das je Monat: Faellt sie mit steigender Bitcoin-Bewegung systematisch ab, nimmt die gestaffelte Gewinnmitnahme der Engine genau in den grossen Bewegungen die Position weg. Das ist Bauart, kein Fehler — aber es entscheidet, wofuer dieses Werkzeug taugt und wofuer nicht.

Naeherung: Monatsrenditen addiert statt verkettet (fuer diese Kennzahl ueblich). Wenige Monate — die Richtung ist belastbarer als die Prozentzahl.

## Was ist die Vorab-Information wert?

Die meisten Kauf- und Teilgewinn-Signale nennen ein **Fib-Level**, das die Kerze nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben. Wer erst auf die Telegram-Nachricht reagiert, findet diesen Preis oft nicht mehr am Markt. Beide Zeilen sind DIESELBEN Signale, nur anders abgerechnet.

| Abrechnung | Rendite | max. Rueckgang |
|---|---|---|
| **Limit-Order lag vorher dort** (zum genannten Level) | **+35.3 %** | -9.9 % |
| **erst nach der Nachricht reagiert** (zum Kerzenschluss) | **+33.8 %** | -9.9 % |
| Unterschied | **+1.5 Punkte** | |

Betroffen sind 66 von 244 Signalen — bei den uebrigen ist der genannte Preis ohnehin der Kerzenschluss (Stop, Restverkauf, Flush-Einstieg, Kaufleiter). Bei den betroffenen liegt der Kerzenschluss im Median **0.48 %** vom genannten Level entfernt.

**So ist das zu lesen:** Der Unterschied ist der Wert der Vorbereitung — also dessen, was die Vorschau-Nachricht und die Zonen-Linien im Chart ermoeglichen. Ist er klein, kann man entspannt auf die Signale reagieren. Ist er gross, entscheidet die vorab platzierte Order ueber einen erheblichen Teil des Ergebnisses.

**Die Zahl ist eine UNTERGRENZE.** Die Zeile 'erst nach der Nachricht' unterstellt, dass man genau zum Kerzenschluss handelt. Tatsaechlich laeuft die Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026), der reale Preis liegt also noch weiter weg. Ausserdem rechnet auch die obere Zeile ohne Schlupf und ohne Teilausfuehrungen.

## Echte Futures-Daten: was bringen sie?

Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes (2004 Punkte) — damit hat die Engine erstmals ein echtes Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.

Beide Zeilen: Variante *LIVE-heute +Bein in Handelsrichtung*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied sind die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD (Stand bisher) | 35% | 23% | +35.2 % | -9.9 % | 247 |
| **mit echtem Futures-CVD** | 35% | 23% | **+35.3 %** | -9.9 % | 244 |

**3 Signale Unterschied** — die echten Daten erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das hilft, sagt die Rendite-Spalte.

## Aggregiertes Spot-CVD: was bringt es?

Bis E37 kam JEDE Zahl der Engine von einer einzigen Boerse. Das Kuerzel `.A` in den Coinalyze-Symbolen heisst Binance, nicht 'aggregiert' — der Code behauptete das Gegenteil, von E9.1 bis zum 19.09.2026. Furkan aggregiert dagegen ausdruecklich ueber mehrere Boersen.

Hier nur der Spot-Teil: 3 Maerkte (Binance, Bybit, Coinbase — OKX hat bei Coinalyze keinen Spot), 2004 vollstaendige Punkte, 0 ausgelassen (ein Zeitpunkt zaehlt nur, wenn ihn alle Boersen haben — sonst saehe eine Teilsumme aus wie ein Einbruch des Spot-Flows).

Alle Zeilen: Variante *LIVE-heute +Bein in Handelsrichtung*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied ist die Herkunft des Spot-CVD.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| heute (nur Binance) | 35% | 23% | +35.3 % | -9.9 % | 244 |
| **aggregiert, groesster Markt je Boerse** | 35% | 23% | **+35.2 %** | -9.9 % | 235 |
| **aggregiert, alle Dollar-Maerkte** | 35% | 20% | **+39.0 %** | -9.9 % | 222 |

**Die Signalzahl aendert sich** — die Muster feuern an anderen Stellen, sobald mehr als eine Boerse zaehlt. Ob das hilft, sagt die Rendite-Spalte; ob es Zufall war, die Fensterhalbierung weiter unten.

**Einheiten, damit es niemand spaeter vermischt:** Die heutige Zeile rechnet in Dollar (Quote-Volumen der Binance-Kerzen), die aggregierten in BTC (Basiswert, wie das Futures-CVD). In `classify_pattern` geht beides nur als relative Aenderung ein, die Einheit kuerzt sich also heraus — summiert werden duerfen die Reihen trotzdem nie.

## Aggregierte Derivate-Daten: was bringen sie?

Open Interest, Liquidationen und Futures-CVD stehen **direkt** in den Bedingungen aller fuenf Muster — ein OI-Wipeout von 5 %, eine Liquidations-Kaskade, Futures-CVD gegen Spot. Das Spot-CVD (Abschnitt darueber) geht dagegen nur ueber zwei Steigungsvergleiche ein. Wenn Aggregation irgendwo wirkt, dann hier.

Perp-Maerkte: Binance (BTCUSD_PERP.A), Bybit (BTCUSD.6), OKX (BTCUSD_PERP.3), Hyperliquid (BTC.H). OI 1504 Punkte, Liquidationen 1471, Futures-CVD 2002.

**Einheiten:** OI und Liquidationen kommen in USD zurueck (`convert_to_usd`) und sind ueber Boersen hinweg summierbar. Das Futures-CVD dagegen kommt in der Denominierung des jeweiligen Marktes — deshalb werden dafuer nur Maerkte derselben Einheit zusammengerechnet. Ausgeschlossen: BTC.H.

Alle Zeilen: Variante *LIVE-heute +Bein in Handelsrichtung*, dieselben Kerzen, derselbe Zeitraum. Der Unterschied sind allein die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| heute (nur Binance) | 35% | 23% | +35.3 % | -9.9 % | 244 |
| **+OI aggregiert** | 35% | 23% | **+37.3 %** | -9.9 % | 235 |
| **+OI +Liquidationen aggregiert** | 41% | 23% | **+39.6 %** | -9.9 % | 232 |
| **+alle drei aggregiert** | 41% | 23% | **+39.7 %** | -9.9 % | 216 |

**Die Signalzahl aendert sich** — mehrere Boersen fuehren zu anderen Entscheidungen. Ob das hilft, sagt die Rendite-Spalte.

## Gewichtete Mittel: Funding und Long-Short

Diese beiden Werte werden **nicht summiert**. Eine Funding-Rate ist ein Preis, keine Menge — zwei Boersen mit 0,01 % und 0,03 % haben zusammen nicht 0,04 %. Gewichtet wird nach Open Interest je Zeitpunkt, wie Furkan es bei Velo einstellt ('Open Interest gewichtet, 8 Stunden, Durchschnitt').

**Ein einfacher Durchschnitt waere hier die Falle:** Er gaebe einer Zwergboerse dasselbe Gewicht wie Binance — und die Zahl saehe dabei voellig normal aus.

1499 vollstaendige Punkte, 510 ausgelassen (ein Zeitpunkt zaehlt nur, wenn alle Boersen dort BEIDES haben: einen Wert und ein Gewicht).

### Zuerst die Skala — vor dem Austausch der Quelle

Das Funding der Engine kommt bis heute von **Kraken** (`relativeFundingRate * 8`), nicht von Coinalyze. Ob beide dieselbe Skala haben, stand nirgends. In `classify_pattern` ist das Vorzeichen skalenunabhaengig — die Schwelle `funding_hot = 0.0001` aber nicht. Wer die Quelle tauscht, ohne das zu pruefen, verschiebt stillschweigend eine Musterbedingung.

Gemessen an 1498 gemeinsamen Zeitpunkten: Median-Betrag Kraken 3.792e-05, Coinalyze 2.632e-03 — **Faktor 0.01**. Gleiches Vorzeichen in 72% der Faelle.

**Achtung, die Skalen weichen ab: Faktor 0.01441** — die Coinalyze-Reihe ist rund 69-mal so gross wie die von Kraken. Die Schwelle `funding_hot = 0.0001` meint damit etwas voellig anderes: gemessen am jeweiligen Median ist sie bei Kraken eine hohe Huerde und bei Coinalyze fast immer ueberschritten. Deshalb steht unten eine zusaetzliche Zeile, die die aggregierte Reihe auf die heutige Skala normiert — nur sie misst die AGGREGATION, die Zeile darueber misst vor allem die Skala.

**Und der ernstere Punkt: die Vorzeichen stimmen nur in 72% der Faelle ueberein.** Zwei Funding-Reihen auf denselben Markt sollten fast immer in dieselbe Richtung zeigen. Tun sie es nicht, ist es nicht dieselbe Groesse — dann hilft auch kein Umrechnungsfaktor, und der Quellentausch waere ein Austausch der Bedeutung, nicht der Genauigkeit.

Alle Zeilen: Variante *LIVE-heute +Bein in Handelsrichtung*, dieselben Kerzen, derselbe Zeitraum. Der Unterschied sind allein die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| heute (Kraken-Funding, Binance-Long-Short) | 35% | 23% | +35.3 % | -9.9 % | 244 |
| **+Funding aggregiert (rohe Skala)** | 35% | 23% | **+32.5 %** | -9.9 % | 273 |
| **+Funding aggregiert, auf heutige Skala normiert** | 35% | 23% | **+30.8 %** | -9.9 % | 244 |
| **+Funding normiert +Long-Short aggregiert** | 35% | 23% | **+30.8 %** | -9.9 % | 244 |

**So ist die Tabelle zu lesen:** Die Zeile *rohe Skala* vergleicht zwei Dinge auf einmal — andere Boersen UND eine andere Groessenordnung. Was sie misst, ist vor allem die verschobene Schwelle. Nur die Zeile *normiert* haelt die Skala fest und zeigt damit die Wirkung der Aggregation allein.

## Robustheitspruefung der Datenvarianten (E37.5)

Die Halbierung weiter unten prueft das Parameter-Gitter. Die Datenzeilen aus den Abschnitten darueber standen bisher **ohne jede Robustheitspruefung** im Bericht — obwohl fuer sie genau dasselbe gilt: Die beste von vielen sieht immer besser aus als sie ist.

Haelfte 1 bis 24.05.2026, Haelfte 2 danach. Variante *LIVE-heute +Bein in Handelsrichtung*, nur die Datenquelle unterscheidet sich.

| Datenvariante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| **heute (Binance/Kraken)** | +23.6 % | 5. | +9.5 % | 7. |
| Spot-CVD aggregiert | +21.4 % | 6. | +11.3 % | 2. |
| Spot-CVD, alle Dollar-Maerkte | +25.1 % | 3. | +11.5 % | 1. |
| OI aggregiert | +24.3 % | 4. | +10.5 % | 3. |
| OI +Liquidationen | +26.7 % | 1. | +10.2 % | 5. |
| OI +Liq +Futures-CVD | +26.7 % | 2. | +10.2 % | 4. |
| Funding normiert | +20.3 % | 7. | +8.7 % | 8. |
| Funding normiert +Long-Short | +20.3 % | 8. | +8.7 % | 9. |
| ALLES aggregiert | +19.7 % | 9. | +10.0 % | 6. |

**In BEIDEN Haelften besser als der heutige Stand: Spot-CVD, alle Dollar-Maerkte, OI aggregiert, OI +Liquidationen, OI +Liq +Futures-CVD.**

## Furkans eigene Termine gegen die Engine

Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche Kurse, gleiche Gebuehr (0.1 %/Order), 10.000 € Start, offene Position am Ende zum Schlusskurs bewertet.

**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide Fenster zusammen ergeben ein faires Bild.**

Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein Teil seiner Verkaufstage Stops waren, also volle Ausstiege.

| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |
|---|---|---|---|---|---|---|
| **kurz** (Engine hat alle Daten)<br><sub>18.01.2026–22.04.2026</sub> | **-8.8 % bis -1.8 %** | -6.8 % | -15.6 % | **+19.1 %** | -9.9 % | -16.5 % |
| **lang** (Furkans volle Abfolge)<br><sub>25.09.2025–22.04.2026</sub> | **-23.7 % bis -6.1 %** | -19.7 % | -30.1 % | **+25.4 %** | -10.0 % | -30.5 % |

Im langen Fenster handelte Furkan an 20 Kauf- und 23 Verkaufstagen.

**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in beiden darueber, ist die Richtung „mehr wie Furkan werden" die falsche und der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, entscheidet keines von beiden.

**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag erlebt hat.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 78 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 78 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 18.01.2026–24.05.2026 · Haelfte 2: 24.05.2026–26.09.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +4.2 % | 75. | +5.0 % | 38. |
| +Kaufleiter | +8.9 % | 71. | +5.2 % | 37. |
| +Flush core | +21.8 % | 29. | -1.8 % | 64. |
| LIVE: nur Long +Kaufleiter +Flush core | +26.1 % | 1. | -1.6 % | 63. |
| +Kaufleiter +Bed.Stop | +5.8 % | 73. | +6.7 % | 26. |
| LIVE +Rest-Freigabe | +21.2 % | 31. | -3.8 % | 75. |
| LIVE +Stop nachziehen | +24.8 % | 5. | -2.4 % | 65. |
| LIVE +Stop nachziehen +Rest-Freigabe | +21.2 % | 32. | -3.8 % | 76. |
| LIVE +Stop +Liq-Kaskade | +19.6 % | 39. | -3.2 % | 72. |
| LIVE +Stop +Liq-Zonen | +18.1 % | 48. | -3.0 % | 71. |
| LIVE +Stop +Liq beides | +18.1 % | 49. | -3.0 % | 70. |
| MEINE Einstellung ohne Flush | +17.6 % | 50. | +3.0 % | 47. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +24.4 % | 6. | -1.0 % | 56. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +22.0 % | 25. | -1.2 % | 58. |
| LIVE +Stop +Verkauf am letzten Hoch | +22.4 % | 20. | -2.7 % | 69. |
| LIVE +Stop +Verkauf am schwachen Hoch | +22.1 % | 24. | -2.4 % | 67. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +15.9 % | 55. | -1.5 % | 62. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +13.2 % | 62. | -1.3 % | 60. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +23.4 % | 15. | -2.4 % | 66. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +25.4 % | 3. | -0.8 % | 55. |
| LIVE +Stop +Sperre 48 h nach Stop | +21.9 % | 28. | -0.7 % | 54. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +20.9 % | 33. | +4.8 % | 40. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +14.7 % | 59. | +4.8 % | 41. |
| LIVE +Stop +alle vier neuen Hebel | +17.3 % | 51. | -1.0 % | 57. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +19.9 % | 37. | +8.0 % | 22. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +23.0 % | 16. | +0.7 % | 53. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +22.1 % | 23. | +7.0 % | 25. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +18.4 % | 47. | +4.7 % | 42. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +16.7 % | 54. | +4.3 % | 43. |
| NEU-LIVE +kein Gegengeschaeft je Kerze | +19.1 % | 43. | +6.3 % | 29. |
| NEU-LIVE +Ziele festhalten | +22.5 % | 18. | +5.5 % | 35. |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | +20.2 % | 34. | +4.9 % | 39. |
| NEU-LIVE +Mindest-Bein 5 % | +18.7 % | 44. | +5.6 % | 34. |
| NEU-LIVE +groesstes Bein | +12.2 % | 66. | -3.5 % | 73. |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | +12.2 % | 67. | -3.5 % | 74. |
| NEU-LIVE +Bein in Handelsrichtung | +19.2 % | 41. | +7.1 % | 24. |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | +19.2 % | 42. | +10.9 % | 3. |
| NEU-LIVE +Break-even im Plus | +12.3 % | 65. | +2.3 % | 49. |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | +10.9 % | 70. | -2.5 % | 68. |
| LIVE +Widerstand des Gegen-Beins | +14.4 % | 60. | +6.4 % | 28. |
| LIVE +Widerstand statt Verkauf am letzten Hoch | +15.3 % | 57. | +6.4 % | 27. |
| LIVE +Rest halten | +2.4 % | 76. | +11.0 % | 2. |
| LIVE +Rest halten +Neustart mit Rest | +15.3 % | 56. | +10.7 % | 4. |
| LIVE +Neustart mit Rest (ohne Halten) | +18.7 % | 45. | +5.7 % | 32. |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | +13.7 % | 61. | +3.4 % | 46. |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | +12.5 % | 64. | +5.8 % | 30. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | +16.7 % | 52. | +5.7 % | 33. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | +11.8 % | 68. | +2.5 % | 48. |
| LIVE-heute +Neustart mit Rest | +16.7 % | 53. | +5.8 % | 31. |
| LIVE-heute +Rueckeroberung vor dem Stop (1 Kerze) | +20.0 % | 35. | +4.3 % | 44. |
| LIVE-heute +Trendfilter EMA200 | -7.6 % | 78. | -1.2 % | 59. |
| LIVE-heute +Trendfilter EMA50 | +4.5 % | 74. | -1.4 % | 61. |
| LIVE-heute +1D-Ebene grob (n=8) | +11.4 % | 69. | -11.0 % | 78. |
| LIVE-heute +1D-Ebene fein (n=5, Gegenprobe zu E23) | +25.2 % | 4. | +1.6 % | 51. |
| LIVE-heute +1D-Ebene sehr grob (n=12) | +15.0 % | 58. | -9.9 % | 77. |
| LIVE-heute +Ampel klein bei unguenstig | +21.9 % | 26. | +7.2 % | 23. |
| LIVE-heute +Ampel UMGEKEHRT (Gegenprobe) | +24.2 % | 7. | +9.2 % | 20. |
| LIVE-heute +immer halbe Tranche (Nullhypothese) | +18.6 % | 46. | +5.5 % | 36. |
| LIVE-heute +Rest halten +Neustart mit Rest | +12.9 % | 63. | +8.6 % | 21. |
| LIVE-heute +Muster 5 als Kauf-Bestaetigung | +22.1 % | 21. | +10.3 % | 6. |
| LIVE-heute +Muster 5 haelt Zwischenverkaeufe | +23.6 % | 8. | +9.5 % | 10. |
| LIVE-heute +Muster 5 haelt ALLE Teilverkaeufe | +23.6 % | 9. | +9.5 % | 11. |
| LIVE-heute +Muster 5 sperrt Kaeufe (Bremse, Gegenprobe) | +23.6 % | 10. | +9.5 % | 12. |
| LIVE-heute +Muster 5 Kauf UND Halten (zwei Unterschiede) | +22.1 % | 22. | +10.3 % | 7. |
| LIVE bis 21.09.2026 (Stop ohne Rueckeroberung) | +19.6 % | 38. | +9.3 % | 19. |
| LIVE-heute +Rueckeroberung 3 statt 1 Kerze (Robustheit) | +21.9 % | 27. | +9.7 % | 9. |
| LIVE-heute +Bein in Handelsrichtung | +23.6 % | 11. | +9.5 % | 13. |
| LIVE bis 26.09.2026 (ohne Bein-Richtung) | +20.0 % | 36. | +4.3 % | 45. |
| LIVE-heute +Muster 2 in Dollar (E43.3) | +23.6 % | 12. | +9.5 % | 14. |
| LIVE-heute +OI in Kontrakten (E43.4) | +23.6 % | 13. | +9.5 % | 15. |
| LIVE-heute +Pivot-Hoch nur letzte 1.300 Kerzen (A5) | +23.6 % | 14. | +9.5 % | 16. |
| LIVE-heute +Rest halten (E43.6) | +19.4 % | 40. | +12.7 % | 1. |
| LIVE-heute +Strenge Bestaetigung (E43.6) | +26.0 % | 2. | +1.9 % | 50. |
| LIVE-heute +Bestaetigung am 0.5-Level (E43.6) | +22.8 % | 17. | +10.3 % | 5. |
| LIVE-heute +Sperrfrist nach Stop 48h (E43.6) | +21.8 % | 30. | +9.5 % | 17. |
| LIVE-heute +Break-even im Plus (E43.8) | +8.1 % | 72. | +10.0 % | 8. |
| LIVE-heute +Rest-Freigabe bei neuer Struktur (E43.8) | +22.5 % | 19. | +9.5 % | 18. |
| Long+Short (Ref) | -2.7 % | 77. | +1.1 % | 52. |

**In BEIDEN Haelften unter den besten 5:** keine einzige Variante

**Wie viel davon waere blosser Zufall?** Bei 78 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.3** Varianten. Gemessen: **0**. Das ist nicht mehr als der Zufall ohnehin liefert — die Rangfolge oben ist damit KEIN Beleg. Dann nur den groben Hebeln trauen (Richtung, Kaufleiter, Flush) und die Feinheiten weglassen.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## E38.1: Was passiert NACH einem Muster?

Kernzahl je Zelle: **Median der Kursaenderung** nach so vielen Kerzen, dahinter der Abstand zur Grundrate und der Anteil der Faelle, die hoeher schlossen. Die Grundrate ist der Median ueber ALLE bewerteten Kerzen — ohne sie misst man nur, ob der Kurs im Fenster ohnehin stieg.

| Muster | Kerzen | Episoden | +6 Kerzen (1 Tg.) | +12 Kerzen (2 Tg.) | +24 Kerzen (4 Tg.) |
|---|---:|---:|---|---|---|
| **ALLE (Grundrate)** | 1481 | — | +0.04 %, 51% hoeher | +0.02 %, 50% hoeher | -0.14 %, 48% hoeher |
| CAPITULATION_RESET | 21 | 15 | -1.61 % (-1.65 gg. Grundrate), 33% hoeher | -1.45 % (-1.47 gg. Grundrate), 33% hoeher | -0.40 % (-0.26 gg. Grundrate), 43% hoeher |
| DERIVATE_PUMP | 96 | 44 | +0.17 % (+0.12 gg. Grundrate), 52% hoeher | -0.08 % (-0.10 gg. Grundrate), 49% hoeher | +0.72 % (+0.87 gg. Grundrate), 56% hoeher |
| GESUNDER_TREND | 184 | 99 | -0.06 % (-0.10 gg. Grundrate), 49% hoeher | +0.02 % (-0.00 gg. Grundrate), 51% hoeher | -0.00 % (+0.14 gg. Grundrate), 50% hoeher |
| NEUTRAL | 1077 | 151 | +0.04 % (+0.00 gg. Grundrate), 51% hoeher | +0.04 % (+0.01 gg. Grundrate), 50% hoeher | -0.21 % (-0.06 gg. Grundrate), 48% hoeher |
| SHORT_COVERING | 56 | 46 | -0.40 % (-0.44 gg. Grundrate), 38% hoeher | -0.15 % (-0.17 gg. Grundrate), 46% hoeher | -0.32 % (-0.18 gg. Grundrate), 48% hoeher |
| UNGESUNDER_ABVERKAUF | 47 | 27 | +0.82 % (+0.77 gg. Grundrate), 72% hoeher | +0.73 % (+0.71 gg. Grundrate), 68% hoeher | -0.52 % (-0.38 gg. Grundrate), 40% hoeher |

**Wie diese Tabelle zu lesen ist.**
Muster 5 hat **27 Episoden** (47 Kerzen) — genug, um den Abstand zur Grundrate ernst zu nehmen. Entscheidend ist das VORZEICHEN dieses Abstands: negativ stuetzt die Bremse (der Kurs faellt nach Muster 5 staerker als sonst), positiv stuetzt die Treibstoff-Lesart.

### Gegenprobe je Episode (nur die erste Kerze)

Benachbarte Kerzen einer Episode teilen fast den ganzen Nachlauf — bei Horizont 6 sind 5 von 6 Kerzen dieselben. Ihre Trefferquote ist deshalb kein zweiter Beleg, sondern derselbe nochmal. Diese Tabelle zaehlt jede Episode genau einmal. **Bleibt der Abstand zur Grundrate hier stehen, war er echt; bricht er ein, hat die Ueberlappung ihn aufgeblasen.** Verglichen wird gegen dieselbe Grundrate wie oben — der Fenster-Durchschnitt aendert sich nicht dadurch, dass man die Musterzeilen ausduennt.

| Muster | Episoden | +6 Kerzen (1 Tg.) | +12 Kerzen (2 Tg.) | +24 Kerzen (4 Tg.) |
|---|---:|---|---|---|
| CAPITULATION_RESET | 15 | -1.85 % (-1.89 gg. Grundrate), 27% hoeher | -1.31 % (-1.33 gg. Grundrate), 33% hoeher | -4.75 % (-4.61 gg. Grundrate), 40% hoeher |
| DERIVATE_PUMP | 44 | -0.37 % (-0.41 gg. Grundrate), 43% hoeher | +0.05 % (+0.03 gg. Grundrate), 50% hoeher | -0.02 % (+0.13 gg. Grundrate), 50% hoeher |
| GESUNDER_TREND | 99 | +0.11 % (+0.07 gg. Grundrate), 52% hoeher | -0.03 % (-0.06 gg. Grundrate), 49% hoeher | +0.13 % (+0.27 gg. Grundrate), 51% hoeher |
| NEUTRAL | 151 | +0.01 % (-0.03 gg. Grundrate), 51% hoeher | -0.07 % (-0.10 gg. Grundrate), 49% hoeher | -0.44 % (-0.30 gg. Grundrate), 46% hoeher |
| SHORT_COVERING | 46 | -0.37 % (-0.41 gg. Grundrate), 39% hoeher | -0.15 % (-0.17 gg. Grundrate), 46% hoeher | +0.21 % (+0.35 gg. Grundrate), 52% hoeher |
| UNGESUNDER_ABVERKAUF | 27 | +1.19 % (+1.15 gg. Grundrate), 74% hoeher | +1.09 % (+1.07 gg. Grundrate), 67% hoeher | +0.90 % (+1.05 gg. Grundrate), 56% hoeher |

**Was diese Messung NICHT zeigt.** Sie misst den Kurs nach dem Muster, nicht den Ertrag einer Regel. Ein Muster kann im Schnitt steigen und als Schalter trotzdem Rendite kosten — das ist in diesem Projekt schon zwoelfmal passiert. Erst E38.5 beantwortet die Ertragsfrage.

**Der Gegenbeweis steht in dieser Tabelle selbst:** `CAPITULATION_RESET` ist das Muster, auf das die Engine live kauft (`flush_entry: core`, seit E9.1, der Hebel hinter der Rendite) — und sein Nachlauf gehoert zu den schlechtesten im Feld. Die Engine kauft eben nicht zum Musterzeitpunkt, sondern an der Fib-Zone mit Stop. Wer nach dieser Tabelle handelte, muesste `flush_entry` abschalten, und das waere nachweislich falsch.

## E39: Was passiert nach einem Stop?

Kaisers Frage: Die Engine ist ausgestoppt, der eigene Trade laeuft weiter. Was hat der Kurs nach den Stops der **Live-Einstellung** getan?

Gemessen ab dem **Stop-Preis** (dem Kerzenschluss, zu dem die Engine ausstieg). Je Zelle: Median der Kursaenderung · Anteil, in dem der Kurs danach wieder **ueber** dem Stop-Preis stand · **tiefster Punkt** bis dahin (Median, in Klammern der schlimmste Fall).

| Gruppe | Stops | +6 Kerzen (1 Tg.) | +12 Kerzen (2 Tg.) | +24 Kerzen (4 Tg.) |
|---|---:|---|---|---|
| **ALLE Stops** | 9 | +0.24 %, 78% drueber, tief -1.1 % (-1.8 %) | +0.77 %, 89% drueber, tief -1.1 % (-2.5 %) | +2.00 %, 100% drueber, tief -1.3 % (-3.7 %) |
| Art: Invalidierung *(zu wenige)* | 9 | +0.24 %, 78% drueber, tief -1.1 % (-1.8 %) | +0.77 %, 89% drueber, tief -1.1 % (-2.5 %) | +2.00 %, 100% drueber, tief -1.3 % (-3.7 %) |
| Muster: NEUTRAL *(zu wenige)* | 8 | +0.20 %, 75% drueber, tief -1.1 % (-1.8 %) | +0.69 %, 88% drueber, tief -1.1 % (-2.5 %) | +2.18 %, 100% drueber, tief -1.4 % (-3.7 %) |
| Muster: UNGESUNDER_ABVERKAUF *(zu wenige)* | 1 | +1.16 %, 100% drueber, tief -1.3 % (-1.3 %) | +1.28 %, 100% drueber, tief -1.3 % (-1.3 %) | +0.90 %, 100% drueber, tief -1.3 % (-1.3 %) |

**Zum Vergleich die Grundrate** (alle Kerzen, nicht nur Stops): +0.04 % nach 6 Kerzen, 51% hoeher. Liegen die Stops deutlich darueber, drehte der Kurs nach Stops oefter als sonst; liegen sie darunter, war der Stop im Schnitt der richtige Ausstieg.

**Achtung, zu duenn:** nur 9 Stops insgesamt. Unter 10 ist jede Zeile eine Anekdote.

**Wie diese Tabelle NICHT zu lesen ist.** *Wieder drueber* heisst nicht, dass Weitermachen sich gelohnt haette: Gemessen wird ab dem Stop-Preis, nicht ab dem eigenen Einstand - eine Position kann ueber dem Stop-Preis stehen und trotzdem im Minus sein. Und wer weitermacht, sitzt den **tiefsten Punkt** aus, bevor irgendetwas zurueckkommt. Die Spalte steht deshalb in jeder Zelle. Ruhig weitermachen kann nur, wessen Position schon im Plus abgesichert ist - dann ist der tiefste Punkt ein entgangener Gewinn und kein Verlust.

Gruppen mit *(zu wenige)* sind Einzelfaelle. Sie stehen da, damit man sieht, dass es sie gibt - nicht, damit man aus ihnen etwas ableitet.

## E40.1: STH-Kostenbasis - Gegenpruefung und Vorfrage

Reine Messung, kein Einfluss auf die Signale. Die STH-Kostenbasis ist der durchschnittliche Einstand der Coins, die juenger als ~5 Monate sind. Fuer jede Kerze gilt der Wert des **Vortags** - der Tageswert steht erst am Tagesende fest.

### Die beiden Quellen

| Quelle | Punkte | von | bis | Fehler |
|---|---:|---|---|---|
| bitview.space | 5871 | 31.08.2010 | 26.09.2026 | — |
| bitcoin-data.com | 1446 | 26.09.2022 | 19.09.2026 | — |

**Gegenpruefung** auf 1446 gemeinsamen Tagen: mittlere Abweichung 0.63 % bei Versatz 0; bester Versatz +1 Tag(e) (0.62 %).

**Achtung: Die Datumszuordnung ist zweifelhaft.** Gemessen wird deshalb mit bitcoin-data.com (dort steht das Datum in jedem Punkt).

### Vorfrage: Wie oft trifft der Zustand auf eine Entscheidung?

- **Kerzen:** 1205 von 1471 unter der STH-Kostenbasis (82%). Der Zustand wechselte **7-mal** - wenige lange Phasen: die Kerzenzahlen sind kein unabhaengiger Beleg.
- **Einstiege der Live-Einstellung:** 83 von 103 unter der STH-Kostenbasis.
- **Stops der Live-Einstellung:** 8 unter, 1 ueber.

**Nachlauf aller Kerzen**, getrennt nach Lage zur STH-Kostenbasis:

| Lage | Kerzen | +6 Kerzen (1 Tg.) | +12 Kerzen (2 Tg.) | +24 Kerzen (4 Tg.) |
|---|---:|---|---|---|
| unter STH | 1205 | -0.01 %, 50% hoeher | +0.06 %, 51% hoeher | -0.05 %, 49% hoeher |
| ueber STH | 266 | +0.16 %, 56% hoeher | +0.02 %, 50% hoeher | -0.31 %, 45% hoeher |

**Nachlauf ab Einstiegspreis** (die Frage hinter dem Verstaerker, E40.3):

| Einstieg | Anzahl | +6 Kerzen (1 Tg.) | +12 Kerzen (2 Tg.) | +24 Kerzen (4 Tg.) |
|---|---:|---|---|---|
| unter STH | 83 | +0.03 %, 51% hoeher | +0.60 %, 58% hoeher | +1.74 %, 61% hoeher |
| ueber STH | 20 | +0.40 %, 70% hoeher | +0.14 %, 55% hoeher | +0.01 %, 50% hoeher |

**Was diese Messung NICHT zeigt:** ob ein Schalter verdient. Nachlauf ist nicht Ertrag - `CAPITULATION_RESET` hatte in E38 den schlechtesten Nachlauf im Feld und traegt trotzdem die Rendite. Die Vorfrage entscheidet nur, ob E40.2 und E40.3 ueberhaupt genug Faelle haetten, um etwas zu messen.

## E41: Stop mit Rueckeroberung - live seit 21.09.2026

Seit dem Umschalten stoppt die Engine nicht mehr beim ersten Schluss unter der Invalidierung: Sie wartet **eine** Kerze, ob die Marke zurueckerobert wird (Kaisers Regel). Der alte Stop laeuft hier als Gegenprobe mit. Die Regel zum Ausschalten stand **vor** der ersten Messung fest (`docs/PLAN-E41-STOP.md`): ausschalten, wenn der alte Stop in **beiden** Haelften um mindestens 1 Punkt besser ist, **oder** wenn der Rueckgang live um mehr als 1 Punkt tiefer liegt als beim alten Stop.

| Variante | Rendite | Rueckgang | H1 | H2 | Stops |
|---|---:|---:|---:|---:|---:|
| **Live: Rueckeroberung, 1 Kerze** | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 9 |
| Alter Stop (bis 21.09.) | +30.8 % | -9.9 % | +19.6 % | +9.3 % | 10 |
| B3 · 3 statt 1 Kerze | +34.2 % | -9.9 % | +21.9 % | +9.7 % | 9 |

**Urteil nach der Ausschalt-Regel:**

- Alter Stop in beiden Haelften mindestens 1 Punkt besser: nein (H1 -4.0, H2 -0.2 Punkte gegen live)
- Rueckgang live mehr als 1 Punkt tiefer: nein (+0.0 Punkte gegen den alten Stop)
- **Bleibt an.**
- B3 zeigt nur, ob das Ergebnis an der Kerzenzahl haengt. Keine Entscheidung haengt daran: 3 Kerzen zu nehmen, weil die Zahl besser aussieht, waere die nachtraegliche Auswahl, vor der der Plan warnt.

### Die Stops, die live ausblieben

Fuer jeden Stop des alten Stops: Hat live an derselben Kerze gestoppt? Wenn nicht - wie endete die Position live, und **kaufte der alte Stop danach wieder ein**? Erst beide Zahlen zusammen zeigen, was der alte Stop gekostet oder gebracht hat (Lehre vom 21.09.: Beim Stop vom 08.03.2026 stieg die Engine acht Stunden spaeter 2,4 % hoeher wieder ein).

- 20.01.2026 89.726 $ — live stattdessen Stop am 20.01.2026 bei 88.428 $ (-1.4 % gegen den alten Stop)
- 08.03.2026 65.971 $ — live stattdessen Restverkauf am 13.03.2026 bei 71.831 $ (+8.9 % gegen den alten Stop); der alte Stop kaufte am 09.03.2026 bei 67.555 $ wieder ein (+2.4 % gegen seinen Stop)
- 19.03.2026 70.191 $ — live stattdessen Stop am 19.03.2026 bei 69.953 $ (-0.3 % gegen den alten Stop)
- 27.03.2026 66.703 $ — live stattdessen Stop am 27.03.2026 bei 66.113 $ (-0.9 % gegen den alten Stop)
- 02.04.2026 66.576 $ — live stattdessen Stop am 02.04.2026 bei 66.931 $ (+0.5 % gegen den alten Stop); der alte Stop kaufte am 02.04.2026 bei 66.931 $ wieder ein (+0.5 % gegen seinen Stop)
- 16.05.2026 78.082 $ — live stattdessen Stop am 17.05.2026 bei 78.029 $ (-0.1 % gegen den alten Stop)
- 18.06.2026 62.369 $ — live stattdessen Stop am 18.06.2026 bei 62.951 $ (+0.9 % gegen den alten Stop)
- 31.07.2026 62.717 $ — live stattdessen Stop am 31.07.2026 bei 62.972 $ (+0.4 % gegen den alten Stop)
- 14.08.2026 62.921 $ — live stattdessen Stop am 14.08.2026 bei 62.869 $ (-0.1 % gegen den alten Stop)
- 15.09.2026 76.186 $ — live stattdessen Stop am 15.09.2026 bei 75.644 $ (-0.7 % gegen den alten Stop)

Die Liste zeigt nur, wie die Positionen **endeten**. Zwischendurch gab es womoeglich Teilverkaeufe oder einen tieferen Buchverlust - dafuer steht die Spalte *Rueckgang* oben. Der Renditeunterschied insgesamt ist das Netto aus vielen verschobenen Positionen und laesst sich keinem einzelnen Fall zuschreiben.

## E43.3: Muster 2 in Dollar (Schalter `muster_cvd`, Default aus)

Befund A2 der Gesamtpruefung: Muster 2 (Derivate-Pump) teilte die Veraenderung im Fenster durch den Stand der kumulierten Summe am Fensteranfang - einen Stand, der nur davon abhaengt, wo die Summe zu laufen begann. `usd` vergleicht stattdessen Spot- und Futures-Delta als Dollar-Betraege im Fenster. Die Zeile unten unterscheidet sich von der Live-Zeile **nur** darin.

| Variante | Rendite | Rueckgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live (alt)** | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |
| Muster 2 in Dollar (usd) | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |

**Vorprobe im Datensatz:**

- Kerzen im Fenster: 1505. Derivate-Pump mit alt: 96, mit usd: 94. **Verschieden erkannt: 2 Kerzen.**
- Live gegen Backtest (1176 nachstellbare Kerzen, Summen live ab 1300 bzw. 540 Kerzen zurueck): Die Live-Engine haette mit alt an **1** Kerzen ein anderes Muster gesehen als der Backtest, mit usd an **0** (muss 0 sein).

**Urteil nach der Entscheidungsregel (vorab festgelegt):**

- In beiden Haelften mindestens 1 Punkt besser: nein (H1 +0.0, H2 +0.0 Punkte gegen live)
- Rueckgang nicht mehr als 1 Punkt tiefer: **ja** (+0.0 Punkte gegen live)
- **Regel nicht erfuellt - der Schalter bleibt auf `alt`.** Offen fuer Kaiser (Sonderregel aus dem Pruefbericht, Teil E): die Korrektur nur in der Anzeige uebernehmen. Dann stuende im Lage-Abruf gelegentlich ein anderes Muster als das, nach dem die Engine handelt.

## E43.4: Open Interest in Kontrakten (Schalter `muster_oi`, Default aus)

Befund A3 der Gesamtpruefung: Das Open Interest kommt in Dollar, also Kontrakte mal Kurs. Schon die Kursbewegung erfuellt so die OI-Schwellen der Muster. `btc` zaehlt Kontrakte: jeder OI-Punkt mit dem Kurs seiner eigenen Kerze umgerechnet, in allen Mustern, Schwellen unveraendert. Die Zeile unten unterscheidet sich von der Live-Zeile **nur** darin.

| Variante | Rendite | Rueckgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live (usd)** | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |
| OI in Kontrakten (btc) | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 227 |

**Vorprobe im Datensatz:**

- Kerzen im Fenster: 1505, davon mit echtem OI-Punkt: 1505. **Verschieden erkannt: 210 Kerzen.**

| Muster | Kerzen mit usd | Kerzen mit btc |
|---|---:|---:|
| CAPITULATION_RESET | 21 | 11 |
| DERIVATE_PUMP | 96 | 48 |
| GESUNDER_TREND | 184 | 149 |
| NEUTRAL | 1101 | 1097 |
| SHORT_COVERING | 56 | 103 |
| UNGESUNDER_ABVERKAUF | 47 | 97 |

**A3 als Zahl** - unter der Kursbedingung des Musters: Wie oft ist die OI-Bedingung in Dollar erfuellt, wie oft in Kontrakten?

| Muster | Kursbedingung | OI-Bedingung | Kerzen | in Dollar | in Kontrakten | in beiden |
|---|---|---|---:|---:|---:|---:|
| 4 Kapitulation | Kurs <= -4 % | OI <= -5 % | 127 | 74 | 30 | 30 |
| 5 Abverkauf mit neuen Shorts | Kurs <= -2 % | OI >= -1 % | 334 | 95 | 209 | 95 |
| 3 Short-Covering | Kurs >= +2 % | OI <= -2 % | 332 | 12 | 65 | 12 |
| 2 Derivate-Pump | Kurs > 0 | OI >= +3 % | 758 | 296 | 144 | 144 |
| 1 Gesunder Trend | Kurs > 0 | OI 0 bis +10 % | 758 | 474 | 359 | 322 |

**Urteil nach der Entscheidungsregel (vorab festgelegt):**

- In beiden Haelften mindestens 1 Punkt besser: nein (H1 +0.0, H2 +0.0 Punkte gegen live)
- Rueckgang nicht mehr als 1 Punkt tiefer: **ja** (+0.0 Punkte gegen live)
- **Regel nicht erfuellt - der Schalter bleibt auf `usd`.** Offen fuer Kaiser: die Anzeige-Frage (Sonderregel Teil E) fuer A2 und A3 gemeinsam.

## A5: next_pivot_beyond haengt von der Historie ab

Befund beim Bau von E43.5: `next_pivot_beyond()` (Teilgewinn am letzten Hoch, `high_exit`, live) sucht das naechste Pivot ueber ALLEN geladenen Kerzen. Live laedt main.py 1300 Spotkerzen (gleitendes Fenster), der Backtest rechnet ab Datenbeginn (wachsendes Fenster). Erst zaehlen, ob das im echten Datensatz ueberhaupt vorkommt.

- Kerzen im Fenster mit 1300 nachstellbaren Kerzen davor: 1177.
- Davon mit einem anderen naechsten Pivot (long ODER short): **53**.

**Gitterzeile mit genau einem Unterschied** (`high_exit_hist="live"` statt `"voll"`):

| Variante | Rendite | Rueckgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live (voll)** | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |
| Pivot-Hoch nur letzte 1.300 Kerzen (live) | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |

**Urteil nach der Entscheidungsregel (vorab festgelegt):**

- In beiden Haelften mindestens 1 Punkt besser: nein (H1 +0.0, H2 +0.0 Punkte gegen live)
- Rueckgang nicht mehr als 1 Punkt tiefer: **ja** (+0.0 Punkte gegen live)
- **Regel nicht erfuellt - bleibt auf `"voll"`.**

## E43.6: Nachmessung mit genau einem Unterschied (rest_halten, strict_confirm, confirm_t1, cooldown_h)

Vier seit Monaten unentschiedene Schalter (`02_status/OFFENE-PUNKTE.md`), jeder mit GENAU EINEM Unterschied zur heutigen Panel-Zeile. Alle vier existieren im Code bereits, es fehlte nur die faire Messzeile.

### `rest_halten`

**Vorprobe im Datensatz:** 11 Positionen im Live-Lauf hat die Regel "Rest schliessen bei Gegen-Muster" beendet - genau die Faelle, die `rest_halten` veraendert.

| Variante | Rendite | Rueckgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live** | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |
| LIVE-heute +Rest halten (E43.6) | +34.5 % | -9.9 % | +19.4 % | +12.7 % | 236 |

**Urteil nach der Entscheidungsregel (vorab festgelegt):**

- In beiden Haelften mindestens 1 Punkt besser: nein (H1 -4.3, H2 +3.2 Punkte gegen live)
- Rueckgang nicht mehr als 1 Punkt tiefer: **ja** (+0.0 Punkte gegen live)
- **Regel nicht erfuellt - bleibt aus.**

### `strict_confirm`

**Vorprobe im Datensatz:** Kerzen im Fenster: 1505. Davon mit lockerer Bestaetigung wahr, strenger falsch (long + short): **1356**.

| Variante | Rendite | Rueckgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live** | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |
| LIVE-heute +Strenge Bestaetigung (E43.6) | +28.5 % | -9.9 % | +26.0 % | +1.9 % | 206 |

**Urteil nach der Entscheidungsregel (vorab festgelegt):**

- In beiden Haelften mindestens 1 Punkt besser: nein (H1 +2.4, H2 -7.6 Punkte gegen live)
- Rueckgang nicht mehr als 1 Punkt tiefer: **ja** (+0.0 Punkte gegen live)
- **Regel nicht erfuellt - bleibt aus.**

### `confirm_t1`

**Vorprobe im Datensatz:** Ersteinstiege am 0.5-Level im Live-Lauf: 14. Davon ganz ohne Order-Flow-Bestaetigung: **9**.

| Variante | Rendite | Rueckgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live** | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |
| LIVE-heute +Bestaetigung am 0.5-Level (E43.6) | +34.9 % | -9.9 % | +22.8 % | +10.3 % | 240 |

**Urteil nach der Entscheidungsregel (vorab festgelegt):**

- In beiden Haelften mindestens 1 Punkt besser: nein (H1 -0.8, H2 +0.9 Punkte gegen live)
- Rueckgang nicht mehr als 1 Punkt tiefer: **ja** (+0.0 Punkte gegen live)
- **Regel nicht erfuellt - bleibt aus.**

### `cooldown_h` (48h)

**Vorprobe im Datensatz:** Neue Einstiege innerhalb von 48h nach einem Stop im Live-Lauf: **1**.

| Variante | Rendite | Rueckgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live** | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |
| LIVE-heute +Sperrfrist nach Stop 48h (E43.6) | +33.4 % | -9.9 % | +21.8 % | +9.5 % | 244 |

**Urteil nach der Entscheidungsregel (vorab festgelegt):**

- In beiden Haelften mindestens 1 Punkt besser: nein (H1 -1.8, H2 +0.0 Punkte gegen live)
- Rueckgang nicht mehr als 1 Punkt tiefer: **ja** (+0.0 Punkte gegen live)
- **Regel nicht erfuellt - bleibt aus.**

## E43.8: Nachmessung mit genau einem Unterschied (be_im_plus, release_stale_rest)

Die letzten zwei seit Monaten unentschiedenen Schalter (`02_status/OFFENE-PUNKTE.md`), jeder mit GENAU EINEM Unterschied zur heutigen Panel-Zeile.

### `be_im_plus`

**Vorprobe im Datensatz:** 205 (Zeitpunkt, Signaltyp)-Paare unterscheiden sich vom Live-Lauf.

| Variante | Rendite | Rueckgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live** | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |
| LIVE-heute +Break-even im Plus (E43.8) | +18.0 % | -10.2 % | +8.1 % | +10.0 % | 348 |

**Urteil nach der Entscheidungsregel (vorab festgelegt):**

- In beiden Haelften mindestens 1 Punkt besser: nein (H1 -15.5, H2 +0.5 Punkte gegen live)
- Rueckgang nicht mehr als 1 Punkt tiefer: **ja** (-0.3 Punkte gegen live)
- **Regel nicht erfuellt - bleibt aus.**

### `release_stale_rest`

**Vorprobe im Datensatz:** 2 (Zeitpunkt, Signaltyp)-Paare unterscheiden sich vom Live-Lauf.

| Variante | Rendite | Rueckgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live** | +35.3 % | -9.9 % | +23.6 % | +9.5 % | 244 |
| LIVE-heute +Rest-Freigabe bei neuer Struktur (E43.8) | +34.6 % | -9.9 % | +22.5 % | +9.5 % | 244 |

**Urteil nach der Entscheidungsregel (vorab festgelegt):**

- In beiden Haelften mindestens 1 Punkt besser: nein (H1 -1.1, H2 +0.0 Punkte gegen live)
- Rueckgang nicht mehr als 1 Punkt tiefer: **ja** (+0.0 Punkte gegen live)
- **Regel nicht erfuellt - bleibt aus.**

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1505 OI-Punkte, 1506 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'LIVE-heute +Ampel UMGEKEHRT (Gegenprobe)' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.