# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 20.12.2025-28.08.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2303 4h-Kerzen geladen · Stand: 2026-08-28 18:17 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 28.08.2026.

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
| nur Long (Basis) | 52% | 41% | +10.3 % | -7.8 % | 100 % | 101 | 2 | 31 % | 7 % |
| +Kaufleiter | 52% | 40% | +17.2 % | -8.7 % | 100 % | 123 | 2 | 42 % | 4 % |
| +Flush core | 57% | 31% | +21.4 % | -14.7 % | 100 % | 179 | 2 | 55 % | 7 % |
| LIVE: nur Long +Kaufleiter +Flush core | 57% | 31% | +27.8 % | -15.5 % | 100 % | 205 | 2 | 64 % | 3 % |
| +Kaufleiter +Bed.Stop | 52% | 39% | +15.3 % | -9.6 % | 100 % | 134 | 2 | 38 % | 4 % |
| LIVE +Rest-Freigabe | 62% | 34% | +21.3 % | -15.5 % | 100 % | 211 | 2 | 59 % | 9 % |
| LIVE +Stop nachziehen | 62% | 33% | +27.6 % | -15.1 % | 100 % | 210 | 2 | 62 % | 2 % |
| LIVE +Stop nachziehen +Rest-Freigabe | 62% | 34% | +21.9 % | -15.1 % | 100 % | 213 | 2 | 59 % | 8 % |
| LIVE +Stop +Liq-Kaskade | 67% | 32% | +18.5 % | -13.2 % | 100 % | 258 | 8 | 45 % | 4 % |
| LIVE +Stop +Liq-Zonen | 76% | 33% | +18.8 % | -12.6 % | 100 % | 293 | 24 | 42 % | 1 % |
| LIVE +Stop +Liq beides | 76% | 33% | +18.4 % | -12.6 % | 100 % | 295 | 26 | 42 % | 1 % |
| MEINE Einstellung ohne Flush | 71% | 43% | +26.3 % | -9.4 % | 100 % | 220 | 14 | 35 % | -17 % |
| LIVE +Stop +Liq-Konfluenz aufstocken | 62% | 33% | +29.2 % | -15.7 % | 100 % | 259 | 4 | 64 % | 2 % |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 57% | 38% | +26.7 % | -15.4 % | 100 % | 187 | 1 | 67 % | 8 % |
| LIVE +Stop +Verkauf am letzten Hoch | 71% | 33% | +24.2 % | -13.3 % | 100 % | 270 | 18 | 49 % | -3 % |
| LIVE +Stop +Verkauf am schwachen Hoch | 67% | 32% | +24.0 % | -13.3 % | 100 % | 257 | 8 | 50 % | -2 % |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 62% | 33% | +17.1 % | -9.9 % | 60 % | 210 | 2 | 40 % | 2 % |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 62% | 33% | +14.2 % | -8.3 % | 50 % | 210 | 2 | 33 % | 2 % |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 62% | 33% | +25.5 % | -15.1 % | 100 % | 207 | 2 | 62 % | 6 % |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 57% | 33% | +30.2 % | -14.9 % | 100 % | 199 | 1 | 68 % | 3 % |
| LIVE +Stop +Sperre 48 h nach Stop | 57% | 34% | +30.6 % | -11.9 % | 100 % | 181 | 2 | 62 % | -3 % |
| LIVE +Stop +Mindest-Stopabstand 2 % | 52% | 40% | +30.2 % | -10.5 % | 100 % | 134 | 0 | 56 % | -6 % |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 52% | 43% | +23.5 % | -10.5 % | 100 % | 125 | 0 | 44 % | -6 % |
| LIVE +Stop +alle vier neuen Hebel | 43% | 39% | +17.4 % | -10.4 % | 100 % | 113 | 0 | 32 % | -5 % |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 52% | 41% | +32.7 % | -10.9 % | 100 % | 165 | 1 | 60 % | -6 % |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 57% | 33% | +33.8 % | -12.6 % | 100 % | 222 | 4 | 67 % | -3 % |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 62% | 41% | +34.0 % | -9.2 % | 100 % | 203 | 17 | 58 % | -10 % |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 67% | 40% | +27.1 % | -11.1 % | 100 % | 215 | 18 | 52 % | -4 % |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 67% | 41% | +24.6 % | -9.4 % | 100 % | 253 | 25 | 44 % | -7 % |
| NEU-LIVE +kein Gegengeschaeft je Kerze | 57% | 37% | +29.9 % | -9.5 % | 100 % | 201 | 0 | 50 % | -10 % |
| NEU-LIVE +Ziele festhalten | 62% | 41% | +28.4 % | -9.2 % | 100 % | 210 | 17 | 49 % | -8 % |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | 57% | 37% | +32.5 % | -9.5 % | 100 % | 209 | 0 | 46 % | -17 % |
| NEU-LIVE +Mindest-Bein 5 % | 71% | 38% | +35.9 % | -9.4 % | 100 % | 242 | 16 | 49 % | -20 % |
| NEU-LIVE +groesstes Bein | 43% | 61% | +17.6 % | -8.3 % | 100 % | 103 | 3 | 12 % | -23 % |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | 43% | 61% | +17.6 % | -8.3 % | 100 % | 103 | 3 | 12 % | -23 % |
| NEU-LIVE +Bein in Handelsrichtung | 62% | 35% | +31.1 % | -9.9 % | 100 % | 239 | 17 | 50 % | -12 % |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | 52% | 33% | +36.5 % | -9.9 % | 100 % | 228 | 14 | 39 % | -29 % |
| NEU-LIVE +Break-even im Plus | 52% | 31% | +15.3 % | -8.0 % | 100 % | 216 | 26 | 31 % | -2 % |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | 33% | 57% | +7.0 % | -9.1 % | 100 % | 144 | 15 | 10 % | -6 % |
| LIVE +Widerstand des Gegen-Beins | 71% | 37% | +29.0 % | -8.7 % | 100 % | 272 | 16 | 43 % | -14 % |
| LIVE +Widerstand statt Verkauf am letzten Hoch | 67% | 37% | +31.2 % | -9.0 % | 100 % | 228 | 3 | 47 % | -14 % |
| LIVE +Rest halten | 33% | 45% | +18.7 % | -9.4 % | 100 % | 84 | 4 | 27 % | -11 % |
| LIVE +Rest halten +Neustart mit Rest | 71% | 38% | +37.3 % | -9.8 % | 100 % | 236 | 17 | 56 % | -16 % **<-- beste** |
| LIVE +Neustart mit Rest (ohne Halten) | 71% | 38% | +37.0 % | -9.4 % | 100 % | 240 | 16 | 51 % | -20 % |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | 52% | 28% | +21.6 % | -18.5 % | 100 % | 256 | 15 | 52 % | 5 % |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | 52% | 31% | +24.7 % | -19.0 % | 100 % | 232 | 15 | 59 % | 4 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | 67% | 34% | +32.8 % | -9.4 % | 100 % | 241 | 0 | 41 % | -22 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | 67% | 34% | +26.4 % | -9.4 % | 100 % | 222 | 0 | 35 % | -17 % |
| LIVE-heute +Neustart mit Rest | 67% | 34% | +34.9 % | -9.4 % | 100 % | 239 | 0 | 44 % | -22 % |
| LIVE-heute +Rest halten +Neustart mit Rest | 67% | 34% | +34.0 % | -9.8 % | 100 % | 235 | 1 | 48 % | -18 % |
| Long+Short (Ref) | 38% | 39% | -2.9 % | -20.1 % | 100 % | 97 | 0 | -32 % | -25 % |

## Beste Kombination (nach Rendite): LIVE +Rest halten +Neustart mit Rest

- Kauf-Trigger getroffen: 6/9 (im Fenster) — 06.01.26, 08.01.26, 20.01.26, 28.02.26, 23.03.26, 27.03.26
- Kauf verpasst: 29.01.26, 30.01.26, 31.01.26
- Verkauf-Trigger getroffen: 9/12 (im Fenster) — 06.01.26, 14.01.26, 23.02.26, 28.02.26, 02.03.26, 17.03.26, 08.04.26, 17.04.26, 22.04.26
- Verkauf verpasst: 25.01.26, 02.02.26, 14.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,733 €** (+37.3 %) · Buy&Hold im Fenster: -12.0 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,836 € · 92 Abschluesse, 70 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*LIVE-heute +Neustart mit Rest*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2025-12 | +92 € | +0.9 % | +92 € | +0.9 % |
| 2026-01 | +604 € | +6.0 % | +595 € | +5.9 % |
| 2026-02 | -90 € | -0.8 % | -88 € | -0.8 % |
| 2026-03 | +533 € | +5.0 % | +472 € | +4.5 % |
| 2026-04 | +1,114 € | +10.0 % | +950 € | +8.6 % |
| 2026-05 | +533 € | +4.3 % | +200 € | +1.7 % |
| 2026-06 | +87 € | +0.7 % | +83 € | +0.7 % |
| 2026-07 | +431 € | +3.4 % | +292 € | +2.4 % |
| 2026-08 | +186 € | +1.4 % | +36 € | +0.3 % |

Monate im Plus: **8 von 9** (live) gegen **8 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Was faengt die Engine von der Marktbewegung ein?

Dieselben Monate, jetzt neben der Bitcoin-Bewegung. **Aufwaerts-Beteiligung** = wie viel des Anstiegs die Engine in steigenden Monaten mitnimmt (hoch ist gut). **Abwaerts-Beteiligung** = wie viel des Rueckgangs sie in fallenden Monaten mitmacht (niedrig oder negativ ist gut).

| Monat | Bitcoin | Engine | davon eingefangen |
|---|---|---|---|
| 2025-12 | -0.8 % | +0.9 % | — |
| 2026-01 | -10.2 % | +6.0 % | — |
| 2026-02 | -14.9 % | -0.8 % | — |
| 2026-03 | +2.0 % | +5.0 % | 257 % |
| 2026-04 | +11.8 % | +10.0 % | 85 % |
| 2026-05 | -3.5 % | +4.3 % | — |
| 2026-06 | -20.4 % | +0.7 % | — |
| 2026-07 | +7.3 % | +3.4 % | 46 % |
| 2026-08 | +23.7 % | +1.4 % | 6 % |

**Aufwaerts-Beteiligung: 44 %** — in den 4 steigenden Monaten legte Bitcoin zusammen +44.7 % zu, die Engine +19.8 %.

**Abwaerts-Beteiligung: -22 %** — in den 5 fallenden Monaten verlor Bitcoin zusammen -49.8 %, die Engine +11.1 %.

**So ist das zu lesen:** Die Gesamtrendite verrraet nicht, WO sie herkommt. Eine Strategie kann glaenzend aussehen, weil sie in fallenden Maerkten gewinnt, und trotzdem in einer Rally kaum mitkommen. Die Spalte 'davon eingefangen' zeigt das je Monat: Faellt sie mit steigender Bitcoin-Bewegung systematisch ab, nimmt die gestaffelte Gewinnmitnahme der Engine genau in den grossen Bewegungen die Position weg. Das ist Bauart, kein Fehler — aber es entscheidet, wofuer dieses Werkzeug taugt und wofuer nicht.

Naeherung: Monatsrenditen addiert statt verkettet (fuer diese Kennzahl ueblich). Wenige Monate — die Richtung ist belastbarer als die Prozentzahl.

## Was ist die Vorab-Information wert?

Die meisten Kauf- und Teilgewinn-Signale nennen ein **Fib-Level**, das die Kerze nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben. Wer erst auf die Telegram-Nachricht reagiert, findet diesen Preis oft nicht mehr am Markt. Beide Zeilen sind DIESELBEN Signale, nur anders abgerechnet.

| Abrechnung | Rendite | max. Rueckgang |
|---|---|---|
| **Limit-Order lag vorher dort** (zum genannten Level) | **+34.9 %** | -9.4 % |
| **erst nach der Nachricht reagiert** (zum Kerzenschluss) | **+35.0 %** | -9.2 % |
| Unterschied | **-0.1 Punkte** | |

Betroffen sind 64 von 239 Signalen — bei den uebrigen ist der genannte Preis ohnehin der Kerzenschluss (Stop, Restverkauf, Flush-Einstieg, Kaufleiter). Bei den betroffenen liegt der Kerzenschluss im Median **0.41 %** vom genannten Level entfernt.

**So ist das zu lesen:** Der Unterschied ist der Wert der Vorbereitung — also dessen, was die Vorschau-Nachricht und die Zonen-Linien im Chart ermoeglichen. Ist er klein, kann man entspannt auf die Signale reagieren. Ist er gross, entscheidet die vorab platzierte Order ueber einen erheblichen Teil des Ergebnisses.

**Die Zahl ist eine UNTERGRENZE.** Die Zeile 'erst nach der Nachricht' unterstellt, dass man genau zum Kerzenschluss handelt. Tatsaechlich laeuft die Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026), der reale Preis liegt also noch weiter weg. Ausserdem rechnet auch die obere Zeile ohne Schlupf und ohne Teilausfuehrungen.

## Echte Futures-Daten: was bringen sie?

Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes (2005 Punkte) — damit hat die Engine erstmals ein echtes Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.

Beide Zeilen: Variante *LIVE-heute +Neustart mit Rest*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied sind die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD (Stand bisher) | 62% | 34% | +34.1 % | -9.4 % | 245 |
| **mit echtem Futures-CVD** | 67% | 34% | **+34.9 %** | -9.4 % | 239 |

**6 Signale Unterschied** — die echten Daten erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das hilft, sagt die Rendite-Spalte.

## Furkans eigene Termine gegen die Engine

Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche Kurse, gleiche Gebuehr (0.1 %/Order), 10.000 € Start, offene Position am Ende zum Schlusskurs bewertet.

**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide Fenster zusammen ergeben ein faires Bild.**

Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein Teil seiner Verkaufstage Stops waren, also volle Ausstiege.

| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |
|---|---|---|---|---|---|---|
| **kurz** (Engine hat alle Daten)<br><sub>20.12.2025–22.04.2026</sub> | **-12.1 % bis +0.2 %** | -9.3 % | -19.8 % | **+23.1 %** | -9.4 % | -11.5 % |
| **lang** (Furkans volle Abfolge)<br><sub>25.09.2025–22.04.2026</sub> | **-23.7 % bis -6.1 %** | -19.7 % | -30.1 % | **+24.8 %** | -9.4 % | -30.5 % |

Im langen Fenster handelte Furkan an 20 Kauf- und 23 Verkaufstagen.

**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in beiden darueber, ist die Richtung „mehr wie Furkan werden" die falsche und der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, entscheidet keines von beiden.

**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag erlebt hat.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 51 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 51 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 20.12.2025–25.04.2026 · Haelfte 2: 25.04.2026–28.08.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +9.4 % | 49. | +0.8 % | 22. |
| +Kaufleiter | +16.0 % | 45. | +1.0 % | 21. |
| +Flush core | +32.9 % | 12. | -8.7 % | 49. |
| LIVE: nur Long +Kaufleiter +Flush core | +39.5 % | 1. | -8.4 % | 48. |
| +Kaufleiter +Bed.Stop | +12.6 % | 47. | +2.4 % | 15. |
| LIVE +Rest-Freigabe | +34.7 % | 7. | -9.9 % | 51. |
| LIVE +Stop nachziehen | +38.1 % | 4. | -7.6 % | 43. |
| LIVE +Stop nachziehen +Rest-Freigabe | +34.7 % | 8. | -9.5 % | 50. |
| LIVE +Stop +Liq-Kaskade | +28.3 % | 22. | -7.6 % | 45. |
| LIVE +Stop +Liq-Zonen | +29.6 % | 18. | -8.4 % | 47. |
| LIVE +Stop +Liq beides | +29.2 % | 19. | -8.3 % | 46. |
| MEINE Einstellung ohne Flush | +20.7 % | 41. | +4.7 % | 12. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +38.4 % | 3. | -6.6 % | 39. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +36.2 % | 5. | -7.0 % | 40. |
| LIVE +Stop +Verkauf am letzten Hoch | +33.8 % | 10. | -7.2 % | 42. |
| LIVE +Stop +Verkauf am schwachen Hoch | +33.5 % | 11. | -7.1 % | 41. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +23.6 % | 32. | -5.2 % | 35. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +19.4 % | 44. | -4.4 % | 34. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +35.9 % | 6. | -7.6 % | 44. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +38.6 % | 2. | -6.0 % | 36. |
| LIVE +Stop +Sperre 48 h nach Stop | +32.5 % | 14. | -1.4 % | 29. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +31.5 % | 15. | -1.0 % | 25. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +24.8 % | 31. | -1.0 % | 26. |
| LIVE +Stop +alle vier neuen Hebel | +25.4 % | 30. | -6.4 % | 38. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +30.4 % | 17. | +1.7 % | 19. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +34.4 % | 9. | -0.4 % | 23. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +31.5 % | 16. | +1.9 % | 17. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +28.9 % | 20. | -1.4 % | 28. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +25.9 % | 29. | -1.0 % | 24. |
| NEU-LIVE +kein Gegengeschaeft je Kerze | +28.4 % | 21. | +1.2 % | 20. |
| NEU-LIVE +Ziele festhalten | +21.0 % | 40. | +2.6 % | 14. |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | +27.3 % | 23. | +2.0 % | 16. |
| NEU-LIVE +Mindest-Bein 5 % | +26.4 % | 27. | +7.5 % | 9. |
| NEU-LIVE +groesstes Bein | +21.4 % | 38. | -3.2 % | 30. |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | +21.4 % | 39. | -3.2 % | 31. |
| NEU-LIVE +Bein in Handelsrichtung | +26.6 % | 26. | +3.6 % | 13. |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | +26.9 % | 25. | +7.5 % | 10. |
| NEU-LIVE +Break-even im Plus | +13.3 % | 46. | +1.8 % | 18. |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | +11.4 % | 48. | -3.9 % | 32. |
| LIVE +Widerstand des Gegen-Beins | +19.5 % | 43. | +8.0 % | 7. |
| LIVE +Widerstand statt Verkauf am letzten Hoch | +21.5 % | 37. | +8.0 % | 6. |
| LIVE +Rest halten | +7.4 % | 50. | +13.9 % | 1. |
| LIVE +Rest halten +Neustart mit Rest | +22.1 % | 36. | +13.0 % | 2. |
| LIVE +Neustart mit Rest (ohne Halten) | +26.4 % | 28. | +8.4 % | 5. |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | +27.0 % | 24. | -4.2 % | 33. |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | +32.8 % | 13. | -6.1 % | 37. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | +23.1 % | 33. | +7.9 % | 8. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | +22.1 % | 35. | +6.8 % | 11. |
| LIVE-heute +Neustart mit Rest | +23.1 % | 34. | +9.5 % | 4. |
| LIVE-heute +Rest halten +Neustart mit Rest | +19.6 % | 42. | +12.4 % | 3. |
| Long+Short (Ref) | +2.0 % | 51. | -1.3 % | 27. |

**In BEIDEN Haelften unter den besten 5:** keine einzige Variante

**Wie viel davon waere blosser Zufall?** Bei 51 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.5** Varianten. Gemessen: **0**. Das ist nicht mehr als der Zufall ohnehin liefert — die Rangfolge oben ist damit KEIN Beleg. Dann nur den groben Hebeln trauen (Richtung, Kaufleiter, Flush) und die Feinheiten weglassen.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1506 OI-Punkte, 1507 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'LIVE +Rest halten +Neustart mit Rest' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.