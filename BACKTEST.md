# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 19.12.2025-27.08.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2295 4h-Kerzen geladen · Stand: 2026-08-27 10:52 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 27.08.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation. **max. Rueckgang** = groesster Einbruch vom jeweiligen Hoch (Drawdown) — je naeher an 0, desto ruhiger der Verlauf. **Einsatz** = wie viel des Kapitals je Position hoechstens investiert wird (100 % = keine Reserve, 60 % = 40 % Pulver bleibt trocken; Furkan-Update Juli 2026). Recall = Aehnlichkeit zu Furkans Terminen IM Fenster, KEIN Gewinn.

**Lesehilfe zu den Namen:** `LIVE` ist die Abkuerzung fuer *nur Long + Kaufleiter + Flush core* — der Flush steckt also drin. Jede Zeile, die mit `LIVE +…` beginnt, baut darauf auf. Die Zeile *+Kaufleiter* ist dagegen OHNE Flush.

| Variante | Recall | Praez. | Rendite | max. Rueckgang | Einsatz | Signale |
|---|---|---|---|---|---|---|
| nur Long (Basis) | 52% | 41% | +10.9 % | -5.5 % | 100 % | 100 |
| +Kaufleiter | 52% | 40% | +17.8 % | -6.3 % | 100 % | 122 |
| +Flush core | 57% | 31% | +22.1 % | -12.1 % | 100 % | 178 |
| LIVE: nur Long +Kaufleiter +Flush core | 57% | 31% | +28.5 % | -12.7 % | 100 % | 204 |
| +Kaufleiter +Bed.Stop | 52% | 39% | +16.0 % | -7.0 % | 100 % | 133 |
| LIVE +Rest-Freigabe | 62% | 34% | +22.0 % | -13.0 % | 100 % | 210 |
| LIVE +Stop nachziehen | 62% | 33% | +28.3 % | -12.3 % | 100 % | 209 |
| LIVE +Stop nachziehen +Rest-Freigabe | 62% | 34% | +22.6 % | -12.6 % | 100 % | 212 |
| LIVE +Stop +Liq-Kaskade | 67% | 32% | +19.1 % | -11.5 % | 100 % | 257 |
| LIVE +Stop +Liq-Zonen | 71% | 32% | +18.8 % | -11.3 % | 100 % | 292 |
| LIVE +Stop +Liq beides | 71% | 32% | +18.4 % | -11.2 % | 100 % | 294 |
| MEINE Einstellung ohne Flush | 67% | 50% | +19.3 % | -6.9 % | 100 % | 152 |
| LIVE +Stop +Liq-Konfluenz aufstocken | 62% | 33% | +31.1 % | -12.3 % | 100 % | 258 |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 57% | 38% | +27.4 % | -13.0 % | 100 % | 186 |
| LIVE +Stop +Verkauf am letzten Hoch | 71% | 33% | +24.7 % | -11.9 % | 100 % | 269 |
| LIVE +Stop +Verkauf am schwachen Hoch | 67% | 32% | +24.5 % | -11.7 % | 100 % | 256 |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 62% | 33% | +17.5 % | -8.2 % | 60 % | 209 |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 62% | 33% | +14.5 % | -6.8 % | 50 % | 209 |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 62% | 33% | +26.2 % | -12.3 % | 100 % | 206 |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 57% | 33% | +31.0 % | -12.1 % | 100 % | 198 |
| LIVE +Stop +Sperre 48 h nach Stop | 57% | 34% | +31.4 % | -8.5 % | 100 % | 180 |
| LIVE +Stop +Mindest-Stopabstand 2 % | 52% | 40% | +30.9 % | -7.0 % | 100 % | 133 |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 52% | 43% | +24.1 % | -7.0 % | 100 % | 124 |
| LIVE +Stop +alle vier neuen Hebel | 43% | 39% | +18.0 % | -6.9 % | 100 % | 112 |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 52% | 41% | +34.6 % | -6.9 % | 100 % | 164 |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 57% | 33% | +35.7 % | -9.3 % | 100 % | 221 **<-- beste** |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 62% | 41% | +35.5 % | -7.5 % | 100 % | 202 |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 62% | 39% | +28.4 % | -7.8 % | 100 % | 214 |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 62% | 40% | +25.4 % | -7.9 % | 100 % | 252 |
| NEU-LIVE +kein Gegengeschaeft je Kerze | 57% | 37% | +31.4 % | -7.5 % | 100 % | 200 |
| NEU-LIVE +Ziele festhalten | 62% | 41% | +29.9 % | -7.5 % | 100 % | 209 |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | 57% | 37% | +34.0 % | -7.5 % | 100 % | 208 |
| Long+Short (Ref) | 38% | 39% | -2.3 % | -11.9 % | 100 % | 96 |

## Beste Kombination (nach Rendite): LIVE +Stop +Sperre 48 h +Liq-Konfluenz

- Kauf-Trigger getroffen: 4/9 (im Fenster) — 06.01.26, 08.01.26, 28.02.26, 23.03.26
- Kauf verpasst: 20.01.26, 29.01.26, 30.01.26, 31.01.26, 27.03.26
- Verkauf-Trigger getroffen: 8/12 (im Fenster) — 14.01.26, 25.01.26, 23.02.26, 02.03.26, 17.03.26, 08.04.26, 14.04.26, 22.04.26
- Verkauf verpasst: 06.01.26, 02.02.26, 28.02.26, 17.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,572 €** (+35.7 %) · Buy&Hold im Fenster: -9.8 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,501 € · 83 Abschluesse, 65 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*NEU-LIVE +Verkauf unter dem letzten Hoch*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2025-12 | +0 € | +0.0 % | +0 € | +0.0 % |
| 2026-01 | +494 € | +4.9 % | +494 € | +4.9 % |
| 2026-02 | +546 € | +5.2 % | -87 € | -0.8 % |
| 2026-03 | +673 € | +6.1 % | +54 € | +0.5 % |
| 2026-04 | +1,436 € | +12.3 % | +941 € | +9.0 % |
| 2026-05 | -639 € | -4.9 % | -387 € | -3.4 % |
| 2026-06 | -29 € | -0.2 % | -26 € | -0.2 % |
| 2026-07 | +1,015 € | +8.1 % | +894 € | +8.1 % |
| 2026-08 | +57 € | +0.4 % | +50 € | +0.4 % |

Monate im Plus: **6 von 9** (live) gegen **5 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Was ist die Vorab-Information wert?

Die meisten Kauf- und Teilgewinn-Signale nennen ein **Fib-Level**, das die Kerze nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben. Wer erst auf die Telegram-Nachricht reagiert, findet diesen Preis oft nicht mehr am Markt. Beide Zeilen sind DIESELBEN Signale, nur anders abgerechnet.

| Abrechnung | Rendite | max. Rueckgang |
|---|---|---|
| **Limit-Order lag vorher dort** (zum genannten Level) | **+35.5 %** | -7.5 % |
| **erst nach der Nachricht reagiert** (zum Kerzenschluss) | **+35.5 %** | -7.5 % |
| Unterschied | **+0.1 Punkte** | |

Betroffen sind 57 von 202 Signalen — bei den uebrigen ist der genannte Preis ohnehin der Kerzenschluss (Stop, Restverkauf, Flush-Einstieg, Kaufleiter). Bei den betroffenen liegt der Kerzenschluss im Median **0.35 %** vom genannten Level entfernt.

**So ist das zu lesen:** Der Unterschied ist der Wert der Vorbereitung — also dessen, was die Vorschau-Nachricht und die Zonen-Linien im Chart ermoeglichen. Ist er klein, kann man entspannt auf die Signale reagieren. Ist er gross, entscheidet die vorab platzierte Order ueber einen erheblichen Teil des Ergebnisses.

**Die Zahl ist eine UNTERGRENZE.** Die Zeile 'erst nach der Nachricht' unterstellt, dass man genau zum Kerzenschluss handelt. Tatsaechlich laeuft die Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026), der reale Preis liegt also noch weiter weg. Ausserdem rechnet auch die obere Zeile ohne Schlupf und ohne Teilausfuehrungen.

## Echte Futures-Daten: was bringen sie?

Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes (2003 Punkte) — damit hat die Engine erstmals ein echtes Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.

Beide Zeilen: Variante *NEU-LIVE +Verkauf unter dem letzten Hoch*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied sind die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD (Stand bisher) | 62% | 42% | +34.4 % | -7.5 % | 206 |
| **mit echtem Futures-CVD** | 62% | 41% | **+35.5 %** | -7.5 % | 202 |

**4 Signale Unterschied** — die echten Daten erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das hilft, sagt die Rendite-Spalte.

## Furkans eigene Termine gegen die Engine

Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche Kurse, gleiche Gebuehr (0.1 %/Order), 10.000 € Start, offene Position am Ende zum Schlusskurs bewertet.

**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide Fenster zusammen ergeben ein faires Bild.**

Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein Teil seiner Verkaufstage Stops waren, also volle Ausstiege.

| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |
|---|---|---|---|---|---|---|
| **kurz** (Engine hat alle Daten)<br><sub>19.12.2025–22.04.2026</sub> | **-12.1 % bis +0.2 %** | -9.3 % | -19.8 % | **+31.5 %** | -5.1 % | -11.3 % |
| **lang** (Furkans volle Abfolge)<br><sub>25.09.2025–22.04.2026</sub> | **-23.7 % bis -6.1 %** | -19.7 % | -30.1 % | **+38.6 %** | -5.1 % | -30.5 % |

Im langen Fenster handelte Furkan an 20 Kauf- und 23 Verkaufstagen.

**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in beiden darueber, ist die Richtung „mehr wie Furkan werden" die falsche und der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, entscheidet keines von beiden.

**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag erlebt hat.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 33 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 33 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 19.12.2025–24.04.2026 · Haelfte 2: 24.04.2026–27.08.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +9.4 % | 32. | +1.4 % | 9. |
| +Kaufleiter | +16.0 % | 29. | +1.6 % | 8. |
| +Flush core | +32.9 % | 12. | -8.2 % | 31. |
| LIVE: nur Long +Kaufleiter +Flush core | +39.5 % | 1. | -7.9 % | 28. |
| +Kaufleiter +Bed.Stop | +12.6 % | 31. | +3.0 % | 6. |
| LIVE +Rest-Freigabe | +34.7 % | 7. | -9.4 % | 33. |
| LIVE +Stop nachziehen | +38.1 % | 4. | -7.1 % | 25. |
| LIVE +Stop nachziehen +Rest-Freigabe | +34.7 % | 8. | -9.0 % | 32. |
| LIVE +Stop +Liq-Kaskade | +28.3 % | 21. | -7.2 % | 27. |
| LIVE +Stop +Liq-Zonen | +29.2 % | 17. | -8.1 % | 30. |
| LIVE +Stop +Liq beides | +28.8 % | 18. | -8.1 % | 29. |
| MEINE Einstellung ohne Flush | +14.0 % | 30. | +4.7 % | 1. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +38.4 % | 3. | -5.3 % | 19. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +36.2 % | 5. | -6.5 % | 22. |
| LIVE +Stop +Verkauf am letzten Hoch | +33.8 % | 10. | -6.8 % | 24. |
| LIVE +Stop +Verkauf am schwachen Hoch | +33.5 % | 11. | -6.7 % | 23. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +23.6 % | 26. | -4.9 % | 18. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +19.4 % | 28. | -4.1 % | 17. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +35.9 % | 6. | -7.1 % | 26. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +38.6 % | 2. | -5.5 % | 20. |
| LIVE +Stop +Sperre 48 h nach Stop | +32.5 % | 13. | -0.9 % | 16. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +31.5 % | 14. | -0.5 % | 13. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +24.8 % | 25. | -0.5 % | 14. |
| LIVE +Stop +alle vier neuen Hebel | +25.4 % | 24. | -5.9 % | 21. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +30.4 % | 16. | +3.2 % | 3. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +34.4 % | 9. | +1.0 % | 10. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +31.5 % | 15. | +3.1 % | 5. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +28.8 % | 19. | -0.4 % | 12. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +25.8 % | 23. | -0.3 % | 11. |
| NEU-LIVE +kein Gegengeschaeft je Kerze | +28.4 % | 20. | +2.4 % | 7. |
| NEU-LIVE +Ziele festhalten | +21.3 % | 27. | +3.8 % | 2. |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | +27.5 % | 22. | +3.1 % | 4. |
| Long+Short (Ref) | +1.7 % | 33. | -0.7 % | 15. |

**In BEIDEN Haelften unter den besten 5:** keine einzige Variante

**Wie viel davon waere blosser Zufall?** Bei 33 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.8** Varianten. Gemessen: **0**. Das ist nicht mehr als der Zufall ohnehin liefert — die Rangfolge oben ist damit KEIN Beleg. Dann nur den groben Hebeln trauen (Richtung, Kaufleiter, Flush) und die Feinheiten weglassen.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1504 OI-Punkte, 1505 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'LIVE +Stop +Sperre 48 h +Liq-Konfluenz' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.