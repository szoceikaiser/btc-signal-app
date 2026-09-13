# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 05.01.2026-13.09.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2397 4h-Kerzen geladen · Stand: 2026-09-13 08:23 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 13.09.2026.

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
| nur Long (Basis) | 52% | 43% | +13.4 % | -7.8 % | 100 % | 101 | 2 | 32 % | 3 % |
| +Kaufleiter | 52% | 42% | +20.5 % | -8.7 % | 100 % | 124 | 2 | 43 % | 0 % |
| +Flush core | 57% | 32% | +23.7 % | -14.7 % | 100 % | 180 | 2 | 55 % | 4 % |
| LIVE: nur Long +Kaufleiter +Flush core | 57% | 33% | +30.2 % | -15.5 % | 100 % | 207 | 2 | 63 % | 1 % |
| +Kaufleiter +Bed.Stop | 52% | 42% | +18.6 % | -9.6 % | 100 % | 135 | 2 | 39 % | 0 % |
| LIVE +Rest-Freigabe | 62% | 35% | +23.2 % | -15.5 % | 100 % | 219 | 2 | 59 % | 7 % |
| LIVE +Stop nachziehen | 62% | 34% | +29.3 % | -15.1 % | 100 % | 215 | 2 | 62 % | 1 % |
| LIVE +Stop nachziehen +Rest-Freigabe | 62% | 35% | +23.8 % | -15.1 % | 100 % | 221 | 2 | 59 % | 6 % |
| LIVE +Stop +Liq-Kaskade | 67% | 33% | +20.4 % | -13.2 % | 100 % | 264 | 8 | 46 % | 2 % |
| LIVE +Stop +Liq-Zonen | 76% | 33% | +21.4 % | -12.6 % | 100 % | 294 | 24 | 43 % | -2 % |
| LIVE +Stop +Liq beides | 76% | 34% | +21.1 % | -12.6 % | 100 % | 296 | 26 | 43 % | -1 % |
| MEINE Einstellung ohne Flush | 62% | 46% | +23.2 % | -9.7 % | 100 % | 230 | 0 | 36 % | -9 % |
| LIVE +Stop +Liq-Konfluenz aufstocken | 62% | 34% | +30.2 % | -15.7 % | 100 % | 262 | 4 | 65 % | 2 % |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 57% | 38% | +27.9 % | -15.4 % | 100 % | 194 | 1 | 67 % | 7 % |
| LIVE +Stop +Verkauf am letzten Hoch | 71% | 34% | +26.2 % | -13.3 % | 100 % | 273 | 18 | 49 % | -4 % |
| LIVE +Stop +Verkauf am schwachen Hoch | 67% | 33% | +25.7 % | -13.3 % | 100 % | 261 | 8 | 50 % | -3 % |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 62% | 34% | +18.5 % | -9.9 % | 60 % | 215 | 2 | 40 % | 1 % |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 62% | 34% | +15.3 % | -8.3 % | 50 % | 215 | 2 | 33 % | 1 % |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 62% | 34% | +27.2 % | -15.1 % | 100 % | 212 | 2 | 62 % | 4 % |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 57% | 34% | +32.0 % | -14.9 % | 100 % | 204 | 1 | 68 % | 2 % |
| LIVE +Stop +Sperre 48 h nach Stop | 57% | 36% | +33.1 % | -11.9 % | 100 % | 184 | 2 | 62 % | -4 % |
| LIVE +Stop +Mindest-Stopabstand 2 % | 52% | 40% | +34.7 % | -10.5 % | 100 % | 141 | 0 | 56 % | -10 % |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 52% | 43% | +27.7 % | -10.5 % | 100 % | 132 | 0 | 44 % | -10 % |
| LIVE +Stop +alle vier neuen Hebel | 43% | 39% | +21.4 % | -10.5 % | 100 % | 120 | 0 | 33 % | -9 % |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 52% | 41% | +37.2 % | -10.9 % | 100 % | 172 | 1 | 61 % | -9 % |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 57% | 35% | +35.6 % | -12.6 % | 100 % | 223 | 4 | 67 % | -3 % |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 62% | 41% | +38.5 % | -9.2 % | 100 % | 210 | 17 | 58 % | -13 % **<-- beste** |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 67% | 40% | +31.4 % | -11.1 % | 100 % | 221 | 18 | 53 % | -8 % |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 67% | 41% | +29.0 % | -9.4 % | 100 % | 259 | 25 | 44 % | -11 % |
| NEU-LIVE +kein Gegengeschaeft je Kerze | 57% | 37% | +34.3 % | -9.5 % | 100 % | 208 | 0 | 51 % | -13 % |
| NEU-LIVE +Ziele festhalten | 62% | 41% | +30.0 % | -9.2 % | 100 % | 217 | 17 | 50 % | -7 % |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | 57% | 37% | +34.1 % | -9.5 % | 100 % | 215 | 0 | 47 % | -15 % |
| NEU-LIVE +Mindest-Bein 5 % | 67% | 43% | +35.3 % | -9.8 % | 100 % | 240 | 17 | 50 % | -15 % |
| NEU-LIVE +groesstes Bein | 38% | 74% | +10.0 % | -11.7 % | 100 % | 105 | 4 | 12 % | -9 % |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | 38% | 74% | +10.0 % | -11.7 % | 100 % | 105 | 4 | 12 % | -9 % |
| NEU-LIVE +Bein in Handelsrichtung | 57% | 40% | +31.8 % | -9.9 % | 100 % | 234 | 16 | 51 % | -9 % |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | 48% | 38% | +35.8 % | -9.9 % | 100 % | 226 | 15 | 40 % | -22 % |
| NEU-LIVE +Break-even im Plus | 52% | 31% | +14.8 % | -8.0 % | 100 % | 220 | 26 | 30 % | -1 % |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | 33% | 65% | +5.6 % | -10.8 % | 100 % | 158 | 16 | 10 % | -3 % |
| LIVE +Widerstand des Gegen-Beins | 67% | 42% | +29.0 % | -9.1 % | 100 % | 268 | 17 | 43 % | -11 % |
| LIVE +Widerstand statt Verkauf am letzten Hoch | 62% | 42% | +29.9 % | -9.7 % | 100 % | 226 | 3 | 48 % | -9 % |
| LIVE +Rest halten | 38% | 63% | +20.2 % | -9.4 % | 100 % | 84 | 5 | 26 % | -12 % |
| LIVE +Rest halten +Neustart mit Rest | 67% | 42% | +34.1 % | -11.1 % | 100 % | 242 | 18 | 56 % | -8 % |
| LIVE +Neustart mit Rest (ohne Halten) | 67% | 43% | +33.8 % | -9.8 % | 100 % | 246 | 17 | 52 % | -11 % |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | 48% | 32% | +21.1 % | -18.5 % | 100 % | 254 | 16 | 53 % | 7 % |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | 48% | 33% | +23.4 % | -19.0 % | 100 % | 228 | 16 | 59 % | 8 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | 62% | 38% | +32.4 % | -9.7 % | 100 % | 239 | 0 | 42 % | -17 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | 62% | 38% | +23.3 % | -9.7 % | 100 % | 219 | 0 | 36 % | -9 % |
| LIVE-heute +Neustart mit Rest | 62% | 38% | +31.9 % | -9.7 % | 100 % | 245 | 0 | 45 % | -14 % |
| LIVE-heute +Zonen nachziehen | 62% | 38% | +31.4 % | -9.7 % | 100 % | 251 | 0 | 47 % | -11 % |
| LIVE-heute +1D-Ebene grob (n=8) | 62% | 37% | +5.5 % | -22.9 % | 100 % | 249 | 0 | 53 % | 29 % |
| LIVE-heute +1D-Ebene fein (n=5, Gegenprobe zu E23) | 48% | 33% | +21.6 % | -18.6 % | 100 % | 266 | 0 | 58 % | 10 % |
| LIVE-heute +1D-Ebene sehr grob (n=12) | 67% | 37% | +6.4 % | -22.0 % | 100 % | 266 | 0 | 47 % | 23 % |
| LIVE-heute +Rest halten +Neustart mit Rest | 62% | 38% | +28.9 % | -11.1 % | 100 % | 237 | 0 | 43 % | -11 % |
| Long+Short (Ref) | 38% | 50% | +1.8 % | -21.2 % | 100 % | 97 | 0 | -29 % | -29 % |

## Beste Kombination (nach Rendite): NEU-LIVE +Verkauf unter dem letzten Hoch

- Kauf-Trigger getroffen: 5/9 (im Fenster) — 06.01.26, 08.01.26, 28.02.26, 23.03.26, 27.03.26
- Kauf verpasst: 20.01.26, 29.01.26, 30.01.26, 31.01.26
- Verkauf-Trigger getroffen: 8/12 (im Fenster) — 14.01.26, 25.01.26, 28.02.26, 02.03.26, 17.03.26, 08.04.26, 17.04.26, 22.04.26
- Verkauf verpasst: 06.01.26, 02.02.26, 23.02.26, 14.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,850 €** (+38.5 %) · Buy&Hold im Fenster: -17.9 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,850 € · 93 Abschluesse, 66 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*LIVE-heute +Zonen nachziehen*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2026-01 | +313 € | +3.1 % | +313 € | +3.1 % |
| 2026-02 | -87 € | -0.8 % | -87 € | -0.8 % |
| 2026-03 | +608 € | +5.9 % | +548 € | +5.4 % |
| 2026-04 | +1,084 € | +10.0 % | +750 € | +7.0 % |
| 2026-05 | +518 € | +4.3 % | +325 € | +2.8 % |
| 2026-06 | -65 € | -0.5 % | -62 € | -0.5 % |
| 2026-07 | +414 € | +3.4 % | +344 € | +2.9 % |
| 2026-08 | +311 € | +2.4 % | +142 € | +1.2 % |
| 2026-09 | +49 € | +0.4 % | +46 € | +0.4 % |

Monate im Plus: **7 von 9** (live) gegen **7 von 9** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Was faengt die Engine von der Marktbewegung ein?

Dieselben Monate, jetzt neben der Bitcoin-Bewegung. **Aufwaerts-Beteiligung** = wie viel des Anstiegs die Engine in steigenden Monaten mitnimmt (hoch ist gut). **Abwaerts-Beteiligung** = wie viel des Rueckgangs sie in fallenden Monaten mitmacht (niedrig oder negativ ist gut).

| Monat | Bitcoin | Engine | davon eingefangen |
|---|---|---|---|
| 2026-01 | -16.1 % | +3.1 % | — |
| 2026-02 | -14.9 % | -0.8 % | — |
| 2026-03 | +2.0 % | +5.9 % | 303 % |
| 2026-04 | +11.8 % | +10.0 % | 85 % |
| 2026-05 | -3.5 % | +4.3 % | — |
| 2026-06 | -20.4 % | -0.5 % | — |
| 2026-07 | +7.3 % | +3.4 % | 46 % |
| 2026-08 | +24.9 % | +2.4 % | 10 % |
| 2026-09 | -2.0 % | +0.4 % | — |

**Aufwaerts-Beteiligung: 47 %** — in den 4 steigenden Monaten legte Bitcoin zusammen +46.0 % zu, die Engine +21.7 %.

**Abwaerts-Beteiligung: -11 %** — in den 5 fallenden Monaten verlor Bitcoin zusammen -57.0 %, die Engine +6.5 %.

**So ist das zu lesen:** Die Gesamtrendite verrraet nicht, WO sie herkommt. Eine Strategie kann glaenzend aussehen, weil sie in fallenden Maerkten gewinnt, und trotzdem in einer Rally kaum mitkommen. Die Spalte 'davon eingefangen' zeigt das je Monat: Faellt sie mit steigender Bitcoin-Bewegung systematisch ab, nimmt die gestaffelte Gewinnmitnahme der Engine genau in den grossen Bewegungen die Position weg. Das ist Bauart, kein Fehler — aber es entscheidet, wofuer dieses Werkzeug taugt und wofuer nicht.

Naeherung: Monatsrenditen addiert statt verkettet (fuer diese Kennzahl ueblich). Wenige Monate — die Richtung ist belastbarer als die Prozentzahl.

## Was ist die Vorab-Information wert?

Die meisten Kauf- und Teilgewinn-Signale nennen ein **Fib-Level**, das die Kerze nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben. Wer erst auf die Telegram-Nachricht reagiert, findet diesen Preis oft nicht mehr am Markt. Beide Zeilen sind DIESELBEN Signale, nur anders abgerechnet.

| Abrechnung | Rendite | max. Rueckgang |
|---|---|---|
| **Limit-Order lag vorher dort** (zum genannten Level) | **+31.4 %** | -9.7 % |
| **erst nach der Nachricht reagiert** (zum Kerzenschluss) | **+30.1 %** | -9.6 % |
| Unterschied | **+1.3 Punkte** | |

Betroffen sind 71 von 251 Signalen — bei den uebrigen ist der genannte Preis ohnehin der Kerzenschluss (Stop, Restverkauf, Flush-Einstieg, Kaufleiter). Bei den betroffenen liegt der Kerzenschluss im Median **0.41 %** vom genannten Level entfernt.

**So ist das zu lesen:** Der Unterschied ist der Wert der Vorbereitung — also dessen, was die Vorschau-Nachricht und die Zonen-Linien im Chart ermoeglichen. Ist er klein, kann man entspannt auf die Signale reagieren. Ist er gross, entscheidet die vorab platzierte Order ueber einen erheblichen Teil des Ergebnisses.

**Die Zahl ist eine UNTERGRENZE.** Die Zeile 'erst nach der Nachricht' unterstellt, dass man genau zum Kerzenschluss handelt. Tatsaechlich laeuft die Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026), der reale Preis liegt also noch weiter weg. Ausserdem rechnet auch die obere Zeile ohne Schlupf und ohne Teilausfuehrungen.

## Echte Futures-Daten: was bringen sie?

Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes (2003 Punkte) — damit hat die Engine erstmals ein echtes Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.

Beide Zeilen: Variante *LIVE-heute +Zonen nachziehen*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied sind die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD (Stand bisher) | 62% | 39% | +30.7 % | -9.7 % | 254 |
| **mit echtem Futures-CVD** | 62% | 38% | **+31.4 %** | -9.7 % | 251 |

**3 Signale Unterschied** — die echten Daten erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das hilft, sagt die Rendite-Spalte.

## Furkans eigene Termine gegen die Engine

Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche Kurse, gleiche Gebuehr (0.1 %/Order), 10.000 € Start, offene Position am Ende zum Schlusskurs bewertet.

**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide Fenster zusammen ergeben ein faires Bild.**

Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein Teil seiner Verkaufstage Stops waren, also volle Ausstiege.

| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |
|---|---|---|---|---|---|---|
| **kurz** (Engine hat alle Daten)<br><sub>05.01.2026–22.04.2026</sub> | **-12.1 % bis +0.2 %** | -9.3 % | -19.8 % | **+19.8 %** | -9.7 % | -16.7 % |
| **lang** (Furkans volle Abfolge)<br><sub>25.09.2025–22.04.2026</sub> | **-23.7 % bis -6.1 %** | -19.7 % | -30.1 % | **+16.9 %** | -9.7 % | -30.5 % |

Im langen Fenster handelte Furkan an 20 Kauf- und 23 Verkaufstagen.

**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in beiden darueber, ist die Richtung „mehr wie Furkan werden" die falsche und der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, entscheidet keines von beiden.

**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag erlebt hat.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 55 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 55 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 05.01.2026–11.05.2026 · Haelfte 2: 11.05.2026–13.09.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +8.8 % | 54. | +4.2 % | 19. |
| +Kaufleiter | +15.4 % | 50. | +4.4 % | 17. |
| +Flush core | +31.1 % | 18. | -4.1 % | 45. |
| LIVE: nur Long +Kaufleiter +Flush core | +37.6 % | 1. | -3.8 % | 42. |
| +Kaufleiter +Bed.Stop | +12.1 % | 52. | +5.8 % | 7. |
| LIVE +Rest-Freigabe | +32.3 % | 12. | -5.3 % | 48. |
| LIVE +Stop nachziehen | +36.2 % | 3. | -3.5 % | 40. |
| LIVE +Stop nachziehen +Rest-Freigabe | +32.3 % | 13. | -4.8 % | 47. |
| LIVE +Stop +Liq-Kaskade | +26.8 % | 30. | -4.4 % | 46. |
| LIVE +Stop +Liq-Zonen | +27.7 % | 27. | -3.9 % | 44. |
| LIVE +Stop +Liq beides | +27.3 % | 29. | -3.9 % | 43. |
| MEINE Einstellung ohne Flush | +22.3 % | 41. | +1.2 % | 28. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +36.1 % | 4. | -2.2 % | 35. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +33.5 % | 7. | -2.3 % | 37. |
| LIVE +Stop +Verkauf am letzten Hoch | +32.1 % | 14. | -3.4 % | 39. |
| LIVE +Stop +Verkauf am schwachen Hoch | +31.4 % | 16. | -3.0 % | 38. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +22.6 % | 40. | -2.2 % | 36. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +18.6 % | 48. | -1.8 % | 32. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +34.0 % | 6. | -3.5 % | 41. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +36.7 % | 2. | -1.9 % | 33. |
| LIVE +Stop +Sperre 48 h nach Stop | +33.0 % | 8. | +1.8 % | 27. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +32.5 % | 11. | +4.7 % | 14. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +25.6 % | 36. | +4.7 % | 15. |
| LIVE +Stop +alle vier neuen Hebel | +26.3 % | 35. | -1.0 % | 31. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +31.6 % | 15. | +7.9 % | 2. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +34.5 % | 5. | +3.1 % | 24. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +33.0 % | 9. | +7.0 % | 4. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +29.5 % | 21. | +4.6 % | 16. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +26.8 % | 31. | +4.2 % | 18. |
| NEU-LIVE +kein Gegengeschaeft je Kerze | +29.8 % | 20. | +6.3 % | 6. |
| NEU-LIVE +Ziele festhalten | +26.5 % | 34. | +5.5 % | 10. |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | +31.4 % | 17. | +4.8 % | 13. |
| NEU-LIVE +Mindest-Bein 5 % | +28.4 % | 25. | +4.8 % | 11. |
| NEU-LIVE +groesstes Bein | +21.7 % | 42. | -9.6 % | 52. |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | +21.7 % | 43. | -9.6 % | 53. |
| NEU-LIVE +Bein in Handelsrichtung | +29.9 % | 19. | +1.0 % | 29. |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | +29.0 % | 23. | +4.8 % | 12. |
| NEU-LIVE +Break-even im Plus | +13.7 % | 51. | +2.5 % | 25. |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | +16.5 % | 49. | -9.3 % | 51. |
| LIVE +Widerstand des Gegen-Beins | +20.7 % | 46. | +5.7 % | 8. |
| LIVE +Widerstand statt Verkauf am letzten Hoch | +22.8 % | 39. | +5.6 % | 9. |
| LIVE +Rest halten | +8.8 % | 53. | +7.1 % | 3. |
| LIVE +Rest halten +Neustart mit Rest | +23.0 % | 38. | +8.5 % | 1. |
| LIVE +Neustart mit Rest (ohne Halten) | +28.4 % | 26. | +3.6 % | 21. |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | +29.0 % | 22. | -6.6 % | 49. |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | +28.5 % | 24. | -2.2 % | 34. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | +26.6 % | 32. | +4.1 % | 20. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | +21.5 % | 44. | +1.0 % | 30. |
| LIVE-heute +Neustart mit Rest | +26.6 % | 33. | +3.3 % | 23. |
| LIVE-heute +Zonen nachziehen | +27.7 % | 28. | +2.5 % | 26. |
| LIVE-heute +1D-Ebene grob (n=8) | +21.2 % | 45. | -13.4 % | 54. |
| LIVE-heute +1D-Ebene fein (n=5, Gegenprobe zu E23) | +32.5 % | 10. | -8.3 % | 50. |
| LIVE-heute +1D-Ebene sehr grob (n=12) | +23.7 % | 37. | -14.7 % | 55. |
| LIVE-heute +Rest halten +Neustart mit Rest | +20.6 % | 47. | +6.4 % | 5. |
| Long+Short (Ref) | -0.6 % | 55. | +3.3 % | 22. |

**In BEIDEN Haelften unter den besten 5:** keine einzige Variante

**Wie viel davon waere blosser Zufall?** Bei 55 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.5** Varianten. Gemessen: **0**. Das ist nicht mehr als der Zufall ohnehin liefert — die Rangfolge oben ist damit KEIN Beleg. Dann nur den groben Hebeln trauen (Richtung, Kaufleiter, Flush) und die Feinheiten weglassen.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1504 OI-Punkte, 1505 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'NEU-LIVE +Verkauf unter dem letzten Hoch' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.