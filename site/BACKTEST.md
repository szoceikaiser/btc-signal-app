# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 29.12.2025-06.09.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2356 4h-Kerzen geladen · Stand: 2026-09-06 13:11 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 06.09.2026.

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
| nur Long (Basis) | 52% | 41% | +15.2 % | -7.8 % | 100 % | 106 | 2 | 38 % | 7 % |
| +Kaufleiter | 52% | 40% | +22.4 % | -8.7 % | 100 % | 129 | 2 | 49 % | 4 % |
| +Flush core | 57% | 31% | +26.9 % | -14.7 % | 100 % | 184 | 2 | 60 % | 7 % |
| LIVE: nur Long +Kaufleiter +Flush core | 57% | 31% | +33.5 % | -15.5 % | 100 % | 211 | 2 | 68 % | 3 % |
| +Kaufleiter +Bed.Stop | 52% | 39% | +20.5 % | -9.6 % | 100 % | 140 | 2 | 45 % | 4 % |
| LIVE +Rest-Freigabe | 62% | 34% | +27.4 % | -15.5 % | 100 % | 218 | 2 | 64 % | 9 % |
| LIVE +Stop nachziehen | 62% | 33% | +33.4 % | -15.1 % | 100 % | 216 | 2 | 67 % | 2 % |
| LIVE +Stop nachziehen +Rest-Freigabe | 62% | 34% | +28.0 % | -15.1 % | 100 % | 220 | 2 | 64 % | 8 % |
| LIVE +Stop +Liq-Kaskade | 67% | 32% | +24.2 % | -13.2 % | 100 % | 266 | 8 | 52 % | 3 % |
| LIVE +Stop +Liq-Zonen | 76% | 33% | +24.3 % | -12.6 % | 100 % | 299 | 24 | 49 % | 1 % |
| LIVE +Stop +Liq beides | 76% | 33% | +23.9 % | -12.6 % | 100 % | 301 | 26 | 49 % | 1 % |
| MEINE Einstellung ohne Flush | 71% | 46% | +28.0 % | -9.8 % | 100 % | 224 | 15 | 42 % | -11 % |
| LIVE +Stop +Liq-Konfluenz aufstocken | 62% | 33% | +34.6 % | -15.7 % | 100 % | 265 | 4 | 68 % | 2 % |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 57% | 38% | +32.4 % | -15.4 % | 100 % | 193 | 1 | 71 % | 8 % |
| LIVE +Stop +Verkauf am letzten Hoch | 71% | 33% | +29.9 % | -13.3 % | 100 % | 276 | 18 | 55 % | -3 % |
| LIVE +Stop +Verkauf am schwachen Hoch | 67% | 32% | +29.7 % | -13.3 % | 100 % | 263 | 8 | 56 % | -2 % |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 62% | 33% | +20.9 % | -9.9 % | 60 % | 216 | 2 | 44 % | 2 % |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 62% | 33% | +17.2 % | -8.3 % | 50 % | 216 | 2 | 36 % | 2 % |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 62% | 33% | +31.2 % | -15.1 % | 100 % | 213 | 2 | 67 % | 6 % |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 57% | 33% | +36.1 % | -14.9 % | 100 % | 205 | 1 | 72 % | 3 % |
| LIVE +Stop +Sperre 48 h nach Stop | 57% | 34% | +36.5 % | -11.9 % | 100 % | 187 | 2 | 66 % | -3 % |
| LIVE +Stop +Mindest-Stopabstand 2 % | 52% | 40% | +36.0 % | -10.5 % | 100 % | 140 | 0 | 61 % | -6 % |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 52% | 43% | +29.0 % | -10.5 % | 100 % | 131 | 0 | 50 % | -6 % |
| LIVE +Stop +alle vier neuen Hebel | 43% | 39% | +22.7 % | -10.5 % | 100 % | 119 | 0 | 39 % | -5 % |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 52% | 41% | +38.3 % | -10.9 % | 100 % | 171 | 1 | 65 % | -6 % |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 57% | 33% | +39.4 % | -12.6 % | 100 % | 228 | 4 | 71 % | -3 % |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 62% | 41% | +39.6 % | -9.2 % | 100 % | 209 | 17 | 62 % | -10 % **<-- beste** |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 67% | 40% | +32.6 % | -11.1 % | 100 % | 221 | 18 | 57 % | -4 % |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 67% | 41% | +30.2 % | -9.4 % | 100 % | 259 | 25 | 50 % | -7 % |
| NEU-LIVE +kein Gegengeschaeft je Kerze | 57% | 37% | +35.4 % | -9.5 % | 100 % | 207 | 0 | 55 % | -11 % |
| NEU-LIVE +Ziele festhalten | 62% | 41% | +32.5 % | -9.2 % | 100 % | 214 | 17 | 52 % | -8 % |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | 57% | 37% | +36.7 % | -9.5 % | 100 % | 214 | 0 | 50 % | -17 % |
| NEU-LIVE +Mindest-Bein 5 % | 71% | 41% | +37.8 % | -9.8 % | 100 % | 246 | 17 | 55 % | -14 % |
| NEU-LIVE +groesstes Bein | 43% | 62% | +15.9 % | -8.3 % | 100 % | 105 | 4 | 11 % | -21 % |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | 43% | 62% | +15.9 % | -8.3 % | 100 % | 105 | 4 | 11 % | -21 % |
| NEU-LIVE +Bein in Handelsrichtung | 62% | 35% | +36.7 % | -9.9 % | 100 % | 245 | 17 | 52 % | -15 % |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | 52% | 36% | +38.3 % | -9.9 % | 100 % | 232 | 15 | 46 % | -23 % |
| NEU-LIVE +Break-even im Plus | 52% | 31% | +14.8 % | -8.0 % | 100 % | 220 | 26 | 28 % | -2 % |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | 33% | 57% | +7.0 % | -9.1 % | 100 % | 143 | 15 | 9 % | -6 % |
| LIVE +Widerstand des Gegen-Beins | 71% | 40% | +31.0 % | -9.1 % | 100 % | 276 | 17 | 49 % | -8 % |
| LIVE +Widerstand statt Verkauf am letzten Hoch | 67% | 40% | +32.3 % | -9.7 % | 100 % | 232 | 3 | 53 % | -6 % |
| LIVE +Rest halten | 33% | 50% | +17.3 % | -9.4 % | 100 % | 80 | 4 | 26 % | -8 % |
| LIVE +Rest halten +Neustart mit Rest | 67% | 39% | +39.2 % | -11.1 % | 100 % | 239 | 18 | 61 % | -10 % |
| LIVE +Neustart mit Rest (ohne Halten) | 71% | 41% | +38.8 % | -9.8 % | 100 % | 244 | 17 | 56 % | -14 % |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | 52% | 30% | +25.6 % | -18.5 % | 100 % | 262 | 16 | 57 % | 7 % |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | 52% | 31% | +28.0 % | -19.0 % | 100 % | 236 | 16 | 63 % | 8 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | 67% | 37% | +34.8 % | -9.7 % | 100 % | 245 | 0 | 47 % | -17 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | 67% | 37% | +27.0 % | -9.7 % | 100 % | 225 | 0 | 39 % | -11 % |
| LIVE-heute +Neustart mit Rest | 67% | 37% | +36.9 % | -9.7 % | 100 % | 243 | 0 | 50 % | -17 % |
| LIVE-heute +Zonen nachziehen | 67% | 37% | +35.9 % | -9.7 % | 100 % | 249 | 0 | 51 % | -14 % |
| LIVE-heute +Rest halten +Neustart mit Rest | 62% | 35% | +34.0 % | -11.0 % | 100 % | 234 | 0 | 50 % | -12 % |
| Long+Short (Ref) | 38% | 43% | +0.9 % | -21.2 % | 100 % | 101 | 0 | -18 % | -22 % |

## Beste Kombination (nach Rendite): NEU-LIVE +Verkauf unter dem letzten Hoch

- Kauf-Trigger getroffen: 5/9 (im Fenster) — 06.01.26, 08.01.26, 28.02.26, 23.03.26, 27.03.26
- Kauf verpasst: 20.01.26, 29.01.26, 30.01.26, 31.01.26
- Verkauf-Trigger getroffen: 8/12 (im Fenster) — 14.01.26, 25.01.26, 28.02.26, 02.03.26, 17.03.26, 08.04.26, 17.04.26, 22.04.26
- Verkauf verpasst: 06.01.26, 02.02.26, 23.02.26, 14.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,962 €** (+39.6 %) · Buy&Hold im Fenster: -8.4 % · Gebuehr 0.1 %/Order, kein Hebel.

- **LONG-Trades:** +3,882 € · 92 Abschluesse, 66 im Gewinn
- **SHORT-Trades:** +0 € · 0 Abschluesse, 0 im Gewinn

WICHTIG: Die Recall-Prozente oben sind Aehnlichkeit zu Furkans Terminen, KEIN Gewinn. Der Gewinn steht nur in den P&L-Zeilen.

## Monat fuer Monat

Kontostand am Monatsende, Start 10.000 €, offene Positionen zum jeweiligen Schlusskurs bewertet. Der erste und der letzte Monat sind angeschnitten (das Fenster beginnt Mitte November und endet heute).

Links die Live-Einstellung (*LIVE-heute +Zonen nachziehen*), rechts dieselbe Einstellung **ohne** den aggressiven Flush-Einstieg.

| Monat | live € | live % | ohne Flush € | ohne Flush % |
|---|---|---|---|---|
| 2025-12 | +26 € | +0.3 % | +26 € | +0.3 % |
| 2026-01 | +391 € | +3.9 % | +370 € | +3.7 % |
| 2026-02 | -87 € | -0.8 % | -86 € | -0.8 % |
| 2026-03 | +614 € | +5.9 % | +459 € | +4.5 % |
| 2026-04 | +1,095 € | +10.0 % | +924 € | +8.6 % |
| 2026-05 | +523 € | +4.3 % | +195 € | +1.7 % |
| 2026-06 | -66 € | -0.5 % | +81 € | +0.7 % |
| 2026-07 | +365 € | +2.9 % | +284 € | +2.4 % |
| 2026-08 | +313 € | +2.4 % | +160 € | +1.3 % |
| 2026-09 | +415 € | +3.1 % | +391 € | +3.1 % |

Monate im Plus: **8 von 10** (live) gegen **9 von 10** (ohne Flush).

Die Euro-Betraege wachsen mit dem Konto — Gewinne werden reinvestiert, ein spaeterer Monat arbeitet also mit mehr Kapital als ein frueher. Zwei Monate sind deshalb nur ueber die Prozentspalte fair vergleichbar.

## Was faengt die Engine von der Marktbewegung ein?

Dieselben Monate, jetzt neben der Bitcoin-Bewegung. **Aufwaerts-Beteiligung** = wie viel des Anstiegs die Engine in steigenden Monaten mitnimmt (hoch ist gut). **Abwaerts-Beteiligung** = wie viel des Rueckgangs sie in fallenden Monaten mitmacht (niedrig oder negativ ist gut).

| Monat | Bitcoin | Engine | davon eingefangen |
|---|---|---|---|
| 2025-12 | +0.5 % | +0.3 % | 55 % |
| 2026-01 | -10.2 % | +3.9 % | — |
| 2026-02 | -14.9 % | -0.8 % | — |
| 2026-03 | +2.0 % | +5.9 % | 303 % |
| 2026-04 | +11.8 % | +10.0 % | 85 % |
| 2026-05 | -3.5 % | +4.3 % | — |
| 2026-06 | -20.4 % | -0.5 % | — |
| 2026-07 | +7.3 % | +2.9 % | 40 % |
| 2026-08 | +24.9 % | +2.4 % | 10 % |
| 2026-09 | +1.7 % | +3.1 % | 183 % |

**Aufwaerts-Beteiligung: 51 %** — in den 6 steigenden Monaten legte Bitcoin zusammen +48.2 % zu, die Engine +24.7 %.

**Abwaerts-Beteiligung: -14 %** — in den 4 fallenden Monaten verlor Bitcoin zusammen -49.0 %, die Engine +6.9 %.

**So ist das zu lesen:** Die Gesamtrendite verrraet nicht, WO sie herkommt. Eine Strategie kann glaenzend aussehen, weil sie in fallenden Maerkten gewinnt, und trotzdem in einer Rally kaum mitkommen. Die Spalte 'davon eingefangen' zeigt das je Monat: Faellt sie mit steigender Bitcoin-Bewegung systematisch ab, nimmt die gestaffelte Gewinnmitnahme der Engine genau in den grossen Bewegungen die Position weg. Das ist Bauart, kein Fehler — aber es entscheidet, wofuer dieses Werkzeug taugt und wofuer nicht.

Naeherung: Monatsrenditen addiert statt verkettet (fuer diese Kennzahl ueblich). Wenige Monate — die Richtung ist belastbarer als die Prozentzahl.

## Was ist die Vorab-Information wert?

Die meisten Kauf- und Teilgewinn-Signale nennen ein **Fib-Level**, das die Kerze nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben. Wer erst auf die Telegram-Nachricht reagiert, findet diesen Preis oft nicht mehr am Markt. Beide Zeilen sind DIESELBEN Signale, nur anders abgerechnet.

| Abrechnung | Rendite | max. Rueckgang |
|---|---|---|
| **Limit-Order lag vorher dort** (zum genannten Level) | **+35.9 %** | -9.7 % |
| **erst nach der Nachricht reagiert** (zum Kerzenschluss) | **+35.0 %** | -9.6 % |
| Unterschied | **+0.9 Punkte** | |

Betroffen sind 73 von 249 Signalen — bei den uebrigen ist der genannte Preis ohnehin der Kerzenschluss (Stop, Restverkauf, Flush-Einstieg, Kaufleiter). Bei den betroffenen liegt der Kerzenschluss im Median **0.41 %** vom genannten Level entfernt.

**So ist das zu lesen:** Der Unterschied ist der Wert der Vorbereitung — also dessen, was die Vorschau-Nachricht und die Zonen-Linien im Chart ermoeglichen. Ist er klein, kann man entspannt auf die Signale reagieren. Ist er gross, entscheidet die vorab platzierte Order ueber einen erheblichen Teil des Ergebnisses.

**Die Zahl ist eine UNTERGRENZE.** Die Zeile 'erst nach der Nachricht' unterstellt, dass man genau zum Kerzenschluss handelt. Tatsaechlich laeuft die Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026), der reale Preis liegt also noch weiter weg. Ausserdem rechnet auch die obere Zeile ohne Schlupf und ohne Teilausfuehrungen.

## Echte Futures-Daten: was bringen sie?

Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes (2004 Punkte) — damit hat die Engine erstmals ein echtes Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.

Beide Zeilen: Variante *LIVE-heute +Zonen nachziehen*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied sind die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD (Stand bisher) | 62% | 37% | +36.3 % | -9.7 % | 254 |
| **mit echtem Futures-CVD** | 67% | 37% | **+35.9 %** | -9.7 % | 249 |

**5 Signale Unterschied** — die echten Daten erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das hilft, sagt die Rendite-Spalte.

## Furkans eigene Termine gegen die Engine

Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche Kurse, gleiche Gebuehr (0.1 %/Order), 10.000 € Start, offene Position am Ende zum Schlusskurs bewertet.

**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide Fenster zusammen ergeben ein faires Bild.**

Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein Teil seiner Verkaufstage Stops waren, also volle Ausstiege.

| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |
|---|---|---|---|---|---|---|
| **kurz** (Engine hat alle Daten)<br><sub>29.12.2025–22.04.2026</sub> | **-12.1 % bis +0.2 %** | -9.3 % | -19.8 % | **+21.0 %** | -9.7 % | -10.4 % |
| **lang** (Furkans volle Abfolge)<br><sub>25.09.2025–22.04.2026</sub> | **-23.7 % bis -6.1 %** | -19.7 % | -30.1 % | **+16.9 %** | -9.7 % | -30.5 % |

Im langen Fenster handelte Furkan an 20 Kauf- und 23 Verkaufstagen.

**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in beiden darueber, ist die Richtung „mehr wie Furkan werden" die falsche und der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, entscheidet keines von beiden.

**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag erlebt hat.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 52 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 52 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 29.12.2025–04.05.2026 · Haelfte 2: 04.05.2026–06.09.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +9.4 % | 50. | +5.3 % | 18. |
| +Kaufleiter | +16.0 % | 46. | +5.6 % | 16. |
| +Flush core | +32.1 % | 13. | -4.0 % | 46. |
| LIVE: nur Long +Kaufleiter +Flush core | +38.7 % | 1. | -3.7 % | 45. |
| +Kaufleiter +Bed.Stop | +12.6 % | 49. | +7.0 % | 10. |
| LIVE +Rest-Freigabe | +33.4 % | 9. | -4.5 % | 49. |
| LIVE +Stop nachziehen | +37.2 % | 4. | -2.8 % | 41. |
| LIVE +Stop nachziehen +Rest-Freigabe | +33.4 % | 10. | -4.0 % | 47. |
| LIVE +Stop +Liq-Kaskade | +27.8 % | 25. | -2.8 % | 40. |
| LIVE +Stop +Liq-Zonen | +28.2 % | 23. | -3.1 % | 44. |
| LIVE +Stop +Liq beides | +27.8 % | 24. | -3.0 % | 43. |
| MEINE Einstellung ohne Flush | +21.3 % | 42. | +4.5 % | 21. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +37.6 % | 3. | -2.1 % | 37. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +35.4 % | 6. | -2.2 % | 38. |
| LIVE +Stop +Verkauf am letzten Hoch | +32.7 % | 11. | -2.1 % | 35. |
| LIVE +Stop +Verkauf am schwachen Hoch | +32.4 % | 12. | -2.0 % | 34. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +23.2 % | 38. | -1.9 % | 33. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +19.1 % | 45. | -1.5 % | 32. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +35.0 % | 7. | -2.8 % | 42. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +37.8 % | 2. | -1.2 % | 31. |
| LIVE +Stop +Sperre 48 h nach Stop | +34.1 % | 8. | +1.8 % | 29. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +31.5 % | 14. | +3.4 % | 24. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +24.8 % | 32. | +3.4 % | 25. |
| LIVE +Stop +alle vier neuen Hebel | +25.4 % | 31. | -2.2 % | 39. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +30.4 % | 18. | +6.0 % | 14. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +35.9 % | 5. | +2.6 % | 28. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +31.5 % | 15. | +6.2 % | 13. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +28.9 % | 21. | +2.9 % | 27. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +25.9 % | 29. | +3.4 % | 26. |
| NEU-LIVE +kein Gegengeschaeft je Kerze | +28.4 % | 22. | +5.5 % | 17. |
| NEU-LIVE +Ziele festhalten | +23.9 % | 35. | +5.9 % | 15. |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | +29.9 % | 20. | +5.2 % | 19. |
| NEU-LIVE +Mindest-Bein 5 % | +27.1 % | 27. | +7.4 % | 8. |
| NEU-LIVE +groesstes Bein | +23.7 % | 36. | -7.2 % | 50. |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | +23.7 % | 37. | -7.2 % | 51. |
| NEU-LIVE +Bein in Handelsrichtung | +30.8 % | 16. | +3.5 % | 23. |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | +27.6 % | 26. | +7.4 % | 9. |
| NEU-LIVE +Break-even im Plus | +13.3 % | 48. | +1.4 % | 30. |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | +15.0 % | 47. | -8.0 % | 52. |
| LIVE +Widerstand des Gegen-Beins | +19.5 % | 44. | +9.2 % | 3. |
| LIVE +Widerstand statt Verkauf am letzten Hoch | +21.5 % | 40. | +7.8 % | 7. |
| LIVE +Rest halten | +6.0 % | 51. | +9.0 % | 4. |
| LIVE +Rest halten +Neustart mit Rest | +22.2 % | 39. | +13.3 % | 1. |
| LIVE +Neustart mit Rest (ohne Halten) | +27.1 % | 28. | +8.2 % | 5. |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | +30.1 % | 19. | -4.4 % | 48. |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | +30.8 % | 17. | -2.1 % | 36. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | +24.6 % | 33. | +6.6 % | 11. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | +21.4 % | 41. | +4.6 % | 20. |
| LIVE-heute +Neustart mit Rest | +24.6 % | 34. | +7.8 % | 6. |
| LIVE-heute +Zonen nachziehen | +25.7 % | 30. | +6.5 % | 12. |
| LIVE-heute +Rest halten +Neustart mit Rest | +20.4 % | 43. | +10.5 % | 2. |
| Long+Short (Ref) | -3.0 % | 52. | +4.0 % | 22. |

**In BEIDEN Haelften unter den besten 5:** keine einzige Variante

**Wie viel davon waere blosser Zufall?** Bei 52 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.5** Varianten. Gemessen: **0**. Das ist nicht mehr als der Zufall ohnehin liefert — die Rangfolge oben ist damit KEIN Beleg. Dann nur den groben Hebeln trauen (Richtung, Kaufleiter, Flush) und die Feinheiten weglassen.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1505 OI-Punkte, 1506 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'NEU-LIVE +Verkauf unter dem letzten Hoch' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.