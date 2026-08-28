# Backtest-Bericht: Engine vs. Kaisers notierte Furkan-Trigger

**Voll-Daten-Fenster: 20.12.2025-28.08.2026** (nur wo alle Order-Flow-Daten inkl. echtem OI vorliegen — E9.6, Kaisers Vorgabe) · 2301 4h-Kerzen geladen · Stand: 2026-08-28 11:56 UTC

Toleranz ±1 Tag. Kauf-Handlung = Long kaufen/nachkaufen oder Short decken; Verkauf-Handlung = Long verkaufen/Stop oder Short eroeffnen.

**Zwei verschiedene Zeitraeume, nicht verwechseln:** Recall/Praezision werden nur bis 23.04.2026 bewertet (danach endet Kaisers Trigger-Liste, es gibt keinen Maszstab mehr). Die Rendite laeuft ueber das komplette Fenster bis 28.08.2026.

## Parameter-Vergleich

Alle n=5. Rendite = Gesamt-Simulation. **max. Rueckgang** = groesster Einbruch vom jeweiligen Hoch (Drawdown) — je naeher an 0, desto ruhiger der Verlauf. **Einsatz** = wie viel des Kapitals je Position hoechstens investiert wird (100 % = keine Reserve, 60 % = 40 % Pulver bleibt trocken; Furkan-Update Juli 2026). Recall = Aehnlichkeit zu Furkans Terminen IM Fenster, KEIN Gewinn.

**Lesehilfe zu den Namen:** `LIVE` ist die Abkuerzung fuer *nur Long + Kaufleiter + Flush core* — der Flush steckt also drin. Jede Zeile, die mit `LIVE +…` beginnt, baut darauf auf. Die Zeile *+Kaufleiter* ist dagegen OHNE Flush.

**Gegengeschaefte** (E25, Kaiser 28.08.2026) = Anzahl der 4h-Kerzen, in denen gleichzeitig aufgestockt UND teilverkauft wurde, meist zum selben Preis. An der Rendite ist das kaum abzulesen — der Backtest handelt beide Seiten zum exakten Signalpreis, netto bleibt die Tranchen-Differenz minus zwei Gebuehren. In der Praxis ist so ein Paar aber nicht ausfuehrbar: zwei Limit-Orders zum selben Preis heben sich auf, und die Telegram-Nachrichten widersprechen sich. Die Spalte misst also Umsetzbarkeit, nicht Gewinn. Der Schalter dagegen heisst `no_flip`.

**Aufwaerts** (E26) = Aufwaerts-Beteiligung: wie viel des Anstiegs die Variante in steigenden Monaten mitnimmt (Einzelheiten im Abschnitt weiter unten). Hoch ist gut. Die Rendite allein verraet das nicht — eine Variante kann glaenzend aussehen, weil sie in fallenden Monaten gewinnt, und in einer Rally trotzdem kaum mitkommen. Wer wissen will, ob ein Schalter grosse Anstiege besser einfaengt, schaut hier hin und nicht auf die Rendite. **Abwaerts** ist das Gegenstueck fuer fallende Monate — niedrig oder negativ ist gut. Die beiden gehoeren zusammen gelesen: Wer mehr vom Anstieg mitnimmt, ist laenger und groesser investiert und macht deshalb in aller Regel auch mehr vom Rueckgang mit. Steigt Aufwaerts, ohne dass Abwaerts mitsteigt, ist wirklich etwas gewonnen; steigen beide, wurde nur das Risiko erhoeht.

| Variante | Recall | Praez. | Rendite | max. Rueckgang | Einsatz | Signale | Gegen-
geschaefte | Auf-
waerts | Ab-
waerts |
|---|---|---|---|---|---|---|---|---|---|
| nur Long (Basis) | 52% | 41% | +10.9 % | -5.5 % | 100 % | 101 | 2 | 31 % | 7 % |
| +Kaufleiter | 52% | 40% | +17.8 % | -6.3 % | 100 % | 123 | 2 | 41 % | 4 % |
| +Flush core | 57% | 31% | +22.1 % | -12.1 % | 100 % | 179 | 2 | 53 % | 7 % |
| LIVE: nur Long +Kaufleiter +Flush core | 57% | 31% | +28.5 % | -12.7 % | 100 % | 205 | 2 | 61 % | 3 % |
| +Kaufleiter +Bed.Stop | 52% | 39% | +16.0 % | -7.0 % | 100 % | 134 | 2 | 37 % | 4 % |
| LIVE +Rest-Freigabe | 62% | 34% | +22.0 % | -13.0 % | 100 % | 211 | 2 | 56 % | 9 % |
| LIVE +Stop nachziehen | 62% | 33% | +28.3 % | -12.3 % | 100 % | 210 | 2 | 59 % | 2 % |
| LIVE +Stop nachziehen +Rest-Freigabe | 62% | 34% | +22.6 % | -12.6 % | 100 % | 213 | 2 | 56 % | 8 % |
| LIVE +Stop +Liq-Kaskade | 67% | 32% | +19.1 % | -11.5 % | 100 % | 258 | 8 | 44 % | 4 % |
| LIVE +Stop +Liq-Zonen | 76% | 33% | +19.1 % | -11.3 % | 100 % | 293 | 24 | 41 % | 1 % |
| LIVE +Stop +Liq beides | 76% | 33% | +18.8 % | -11.2 % | 100 % | 295 | 26 | 41 % | 1 % |
| MEINE Einstellung ohne Flush | 71% | 43% | +27.8 % | -7.5 % | 100 % | 220 | 14 | 36 % | -17 % |
| LIVE +Stop +Liq-Konfluenz aufstocken | 62% | 33% | +31.1 % | -12.3 % | 100 % | 259 | 4 | 64 % | 2 % |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 57% | 38% | +27.4 % | -13.0 % | 100 % | 187 | 1 | 64 % | 8 % |
| LIVE +Stop +Verkauf am letzten Hoch | 71% | 33% | +24.7 % | -11.9 % | 100 % | 270 | 18 | 47 % | -3 % |
| LIVE +Stop +Verkauf am schwachen Hoch | 67% | 32% | +24.5 % | -11.7 % | 100 % | 257 | 8 | 48 % | -2 % |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 62% | 33% | +17.5 % | -8.2 % | 60 % | 210 | 2 | 38 % | 2 % |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 62% | 33% | +14.5 % | -6.8 % | 50 % | 210 | 2 | 32 % | 2 % |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 62% | 33% | +26.2 % | -12.3 % | 100 % | 207 | 2 | 59 % | 6 % |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 57% | 33% | +31.0 % | -12.1 % | 100 % | 199 | 1 | 65 % | 3 % |
| LIVE +Stop +Sperre 48 h nach Stop | 57% | 34% | +31.4 % | -8.5 % | 100 % | 181 | 2 | 59 % | -3 % |
| LIVE +Stop +Mindest-Stopabstand 2 % | 52% | 40% | +30.9 % | -7.0 % | 100 % | 134 | 0 | 54 % | -6 % |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 52% | 43% | +24.2 % | -7.0 % | 100 % | 125 | 0 | 42 % | -6 % |
| LIVE +Stop +alle vier neuen Hebel | 43% | 39% | +18.0 % | -6.9 % | 100 % | 113 | 0 | 32 % | -5 % |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 52% | 41% | +34.7 % | -6.9 % | 100 % | 165 | 1 | 60 % | -6 % |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 57% | 33% | +35.8 % | -9.3 % | 100 % | 222 | 4 | 66 % | -3 % |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 62% | 41% | +35.6 % | -7.5 % | 100 % | 203 | 17 | 57 % | -10 % |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 67% | 40% | +28.4 % | -7.8 % | 100 % | 215 | 18 | 51 % | -4 % |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 67% | 41% | +25.5 % | -7.9 % | 100 % | 253 | 25 | 42 % | -7 % |
| NEU-LIVE +kein Gegengeschaeft je Kerze | 57% | 37% | +31.5 % | -7.5 % | 100 % | 201 | 0 | 49 % | -10 % |
| NEU-LIVE +Ziele festhalten | 62% | 41% | +29.9 % | -7.5 % | 100 % | 210 | 17 | 49 % | -8 % |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | 57% | 37% | +34.0 % | -7.5 % | 100 % | 209 | 0 | 46 % | -17 % |
| NEU-LIVE +Mindest-Bein 5 % | 71% | 38% | +37.5 % | -6.9 % | 100 % | 242 | 16 | 49 % | -20 % |
| NEU-LIVE +groesstes Bein | 43% | 61% | +17.6 % | -7.3 % | 100 % | 103 | 3 | 11 % | -23 % |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | 43% | 61% | +17.6 % | -7.3 % | 100 % | 103 | 3 | 11 % | -23 % |
| NEU-LIVE +Bein in Handelsrichtung | 62% | 35% | +32.7 % | -8.9 % | 100 % | 239 | 17 | 50 % | -12 % |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | 52% | 33% | +38.1 % | -8.2 % | 100 % | 228 | 14 | 39 % | -29 % |
| NEU-LIVE +Break-even im Plus | 52% | 31% | +15.9 % | -5.3 % | 100 % | 215 | 26 | 30 % | -2 % |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | 33% | 57% | +7.0 % | -8.1 % | 100 % | 144 | 15 | 9 % | -6 % |
| LIVE +Widerstand des Gegen-Beins | 71% | 37% | +30.1 % | -6.2 % | 100 % | 272 | 16 | 42 % | -14 % |
| LIVE +Widerstand statt Verkauf am letzten Hoch | 67% | 37% | +32.6 % | -6.8 % | 100 % | 228 | 3 | 47 % | -14 % |
| LIVE +Rest halten | 33% | 45% | +18.8 % | -6.9 % | 100 % | 84 | 4 | 25 % | -11 % |
| LIVE +Rest halten +Neustart mit Rest | 71% | 38% | +39.0 % | -8.2 % | 100 % | 236 | 17 | 55 % | -16 % **<-- beste** |
| LIVE +Neustart mit Rest (ohne Halten) | 71% | 38% | +38.6 % | -6.9 % | 100 % | 240 | 16 | 50 % | -20 % |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | 52% | 28% | +23.1 % | -17.6 % | 100 % | 256 | 15 | 52 % | 5 % |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | 52% | 31% | +26.2 % | -17.0 % | 100 % | 232 | 15 | 58 % | 4 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | 67% | 34% | +34.4 % | -7.1 % | 100 % | 241 | 0 | 41 % | -22 % |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | 67% | 34% | +27.8 % | -7.1 % | 100 % | 222 | 0 | 35 % | -17 % |
| LIVE-heute +Neustart mit Rest | 67% | 34% | +36.5 % | -7.1 % | 100 % | 239 | 0 | 44 % | -22 % |
| LIVE-heute +Rest halten +Neustart mit Rest | 67% | 34% | +35.5 % | -8.2 % | 100 % | 235 | 1 | 47 % | -18 % |
| Long+Short (Ref) | 38% | 39% | -2.3 % | -11.9 % | 100 % | 97 | 0 | -29 % | -25 % |

## Beste Kombination (nach Rendite): LIVE +Rest halten +Neustart mit Rest

- Kauf-Trigger getroffen: 6/9 (im Fenster) — 06.01.26, 08.01.26, 20.01.26, 28.02.26, 23.03.26, 27.03.26
- Kauf verpasst: 29.01.26, 30.01.26, 31.01.26
- Verkauf-Trigger getroffen: 9/12 (im Fenster) — 06.01.26, 14.01.26, 23.02.26, 28.02.26, 02.03.26, 17.03.26, 08.04.26, 17.04.26, 22.04.26
- Verkauf verpasst: 25.01.26, 02.02.26, 14.04.26

## P&L-Simulation (beste Kombination) — getrennt nach Richtung

Start 10.000 € -> **13,896 €** (+39.0 %) · Buy&Hold im Fenster: -9.9 % · Gebuehr 0.1 %/Order, kein Hebel.

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
| 2026-08 | +346 € | +2.6 % | +186 € | +1.5 % |

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
| 2026-08 | +26.5 % | +2.6 % | 10 % |

**Aufwaerts-Beteiligung: 44 %** — in den 4 steigenden Monaten legte Bitcoin zusammen +47.6 % zu, die Engine +21.0 %.

**Abwaerts-Beteiligung: -22 %** — in den 5 fallenden Monaten verlor Bitcoin zusammen -49.8 %, die Engine +11.1 %.

**So ist das zu lesen:** Die Gesamtrendite verrraet nicht, WO sie herkommt. Eine Strategie kann glaenzend aussehen, weil sie in fallenden Maerkten gewinnt, und trotzdem in einer Rally kaum mitkommen. Die Spalte 'davon eingefangen' zeigt das je Monat: Faellt sie mit steigender Bitcoin-Bewegung systematisch ab, nimmt die gestaffelte Gewinnmitnahme der Engine genau in den grossen Bewegungen die Position weg. Das ist Bauart, kein Fehler — aber es entscheidet, wofuer dieses Werkzeug taugt und wofuer nicht.

Naeherung: Monatsrenditen addiert statt verkettet (fuer diese Kennzahl ueblich). Wenige Monate — die Richtung ist belastbarer als die Prozentzahl.

## Was ist die Vorab-Information wert?

Die meisten Kauf- und Teilgewinn-Signale nennen ein **Fib-Level**, das die Kerze nur BERUEHRT hat — das Tief kann in Stunde 2 einer 4h-Kerze gelegen haben. Wer erst auf die Telegram-Nachricht reagiert, findet diesen Preis oft nicht mehr am Markt. Beide Zeilen sind DIESELBEN Signale, nur anders abgerechnet.

| Abrechnung | Rendite | max. Rueckgang |
|---|---|---|
| **Limit-Order lag vorher dort** (zum genannten Level) | **+36.5 %** | -7.1 % |
| **erst nach der Nachricht reagiert** (zum Kerzenschluss) | **+36.5 %** | -7.1 % |
| Unterschied | **-0.1 Punkte** | |

Betroffen sind 64 von 239 Signalen — bei den uebrigen ist der genannte Preis ohnehin der Kerzenschluss (Stop, Restverkauf, Flush-Einstieg, Kaufleiter). Bei den betroffenen liegt der Kerzenschluss im Median **0.41 %** vom genannten Level entfernt.

**So ist das zu lesen:** Der Unterschied ist der Wert der Vorbereitung — also dessen, was die Vorschau-Nachricht und die Zonen-Linien im Chart ermoeglichen. Ist er klein, kann man entspannt auf die Signale reagieren. Ist er gross, entscheidet die vorab platzierte Order ueber einen erheblichen Teil des Ergebnisses.

**Die Zahl ist eine UNTERGRENZE.** Die Zeile 'erst nach der Nachricht' unterstellt, dass man genau zum Kerzenschluss handelt. Tatsaechlich laeuft die Engine 1 bis 3 Stunden spaeter (GitHub-Verzoegerung, gemessen 29.07.2026), der reale Preis liegt also noch weiter weg. Ausserdem rechnet auch die obere Zeile ohne Schlupf und ohne Teilausfuehrungen.

## Echte Futures-Daten: was bringen sie?

Coinalyze liefert seit E16 auch das Taker-Kaufvolumen des Futures-Marktes (2003 Punkte) — damit hat die Engine erstmals ein echtes Futures-CVD. Vorher war der entsprechende Zweig in `classify_pattern` toter Code und Muster 2 (Derivate-Pump) lief ueber Ersatzmerkmale.

Beide Zeilen: Variante *LIVE-heute +Neustart mit Rest*, dieselben Kerzen, derselbe Zeitraum. Der einzige Unterschied sind die Daten.

| Datenlage | Recall | Praez. | Rendite | max. Rueckgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD (Stand bisher) | 62% | 34% | +35.8 % | -7.1 % | 245 |
| **mit echtem Futures-CVD** | 67% | 34% | **+36.5 %** | -7.1 % | 239 |

**6 Signale Unterschied** — die echten Daten erkennen den Derivate-Pump an anderen Stellen als die Naeherung. Ob das hilft, sagt die Rendite-Spalte.

## Furkans eigene Termine gegen die Engine

Kaisers Trigger-Listen dienten bisher nur als Aehnlichkeits-Massstab (Recall). Hier laufen sie erstmals durch dieselbe P&L-Rechnung wie die Engine — gleiche Kurse, gleiche Gebuehr (0.1 %/Order), 10.000 € Start, offene Position am Ende zum Schlusskurs bewertet.

**Zwei Fenster, und der Unterschied ist wichtig.** Das kurze beginnt dort, wo die Engine alle Daten hat (echtes Open Interest). Furkan hatte zu diesem Zeitpunkt aber schon eine Position aus September/Oktober, die wir nicht kennen — er verkauft im Fenster also etwas, das er vorher aufgebaut hat. Das lange Fenster beginnt an seinem ERSTEN notierten Termin und bildet seine Abfolge vollstaendig ab; dort fehlt dafuer der Engine vor Mitte November das Open Interest (Muster 4 inaktiv, Nachteil fuer die Engine). **Erst beide Fenster zusammen ergeben ein faires Bild.**

Tranchengroessen sind unbekannt (die Listen enthalten Tage, keine Betraege) — daher eine Spanne ueber 12 Annahmen: Kauf 25/33/50 % des freien Geldes, Verkauf 25/33/50/100 % der Position. Die 100 %-Annahme bildet ab, dass ein Teil seiner Verkaufstage Stops waren, also volle Ausstiege.

| Fenster | Furkan (Spanne) | Furkan 33/33 | dessen Rueckgang | Engine | dessen Rueckgang | Buy & Hold |
|---|---|---|---|---|---|---|
| **kurz** (Engine hat alle Daten)<br><sub>20.12.2025–22.04.2026</sub> | **-12.1 % bis +0.2 %** | -9.3 % | -19.8 % | **+23.1 %** | -7.1 % | -11.5 % |
| **lang** (Furkans volle Abfolge)<br><sub>25.09.2025–22.04.2026</sub> | **-23.7 % bis -6.1 %** | -19.7 % | -30.1 % | **+24.8 %** | -7.1 % | -30.5 % |

Im langen Fenster handelte Furkan an 20 Kauf- und 23 Verkaufstagen.

**So ist das zu lesen:** Liegt die Engine in BEIDEN Fenstern deutlich unter Furkans Spanne, gibt es echten Spielraum und es lohnt sich, seine Methode genauer nachzubauen. Liegt sie darin, sind beide auf verschiedenen Wegen am selben Ziel — weiteres Angleichen waere verschwendete Arbeit. Liegt sie in beiden darueber, ist die Richtung „mehr wie Furkan werden" die falsche und der Recall als Zielgroesse irrefuehrend. Widersprechen sich die Fenster, entscheidet keines von beiden.

**Grenzen, ehrlich — die Zahl ist ein Anhaltspunkt, kein Beweis:** Die Liste ist Kaisers Mitschrift dessen, was Furkan in Videos gezeigt hat, kein geprueftes Konto; Menschen zeigen gute Trades vollstaendiger als schlechte. Die Tranchengroessen sind geraten. Gerechnet wird mit Tagesschlusskursen, er handelte innertaegig. Welche Verkaufstage Teilgewinne und welche Stops waren, steht in den Listen nicht — deshalb die breite Spanne. Und die Engine kennt beim Nachrechnen den ganzen Zeitraum, waehrend Furkan ihn Tag fuer Tag erlebt hat.

## Robustheitspruefung: Fenster halbiert

Warum: Oben werden 51 Varianten gegen EIN Zeitfenster verglichen. Die beste von vielen sieht immer besser aus als sie ist — wie der Beste von 51 Muenzwerfern. Deshalb laeuft hier jede Variante noch einmal getrennt in zwei Haelften. **Liegt dieselbe Variante in beiden Haelften vorne, ist der Vorteil vermutlich echt. Kippt die Rangfolge, war es Zufall.**

Haelfte 1: 20.12.2025–25.04.2026 · Haelfte 2: 25.04.2026–28.08.2026. Jede Haelfte ist nur halb so lang und damit fuer sich zappeliger — auf die Rangfolge schauen, nicht auf die einzelne Zahl.

| Variante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| nur Long (Basis) | +9.4 % | 49. | +1.4 % | 22. |
| +Kaufleiter | +16.0 % | 45. | +1.6 % | 21. |
| +Flush core | +32.9 % | 12. | -8.2 % | 49. |
| LIVE: nur Long +Kaufleiter +Flush core | +39.5 % | 1. | -7.9 % | 46. |
| +Kaufleiter +Bed.Stop | +12.6 % | 47. | +3.0 % | 18. |
| LIVE +Rest-Freigabe | +34.7 % | 7. | -9.4 % | 51. |
| LIVE +Stop nachziehen | +38.1 % | 4. | -7.1 % | 43. |
| LIVE +Stop nachziehen +Rest-Freigabe | +34.7 % | 8. | -9.0 % | 50. |
| LIVE +Stop +Liq-Kaskade | +28.3 % | 22. | -7.2 % | 45. |
| LIVE +Stop +Liq-Zonen | +29.6 % | 18. | -8.1 % | 48. |
| LIVE +Stop +Liq beides | +29.2 % | 19. | -8.1 % | 47. |
| MEINE Einstellung ohne Flush | +20.7 % | 41. | +5.9 % | 12. |
| LIVE +Stop +Liq-Konfluenz aufstocken | +38.4 % | 3. | -5.2 % | 37. |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | +36.2 % | 5. | -6.5 % | 40. |
| LIVE +Stop +Verkauf am letzten Hoch | +33.8 % | 10. | -6.8 % | 42. |
| LIVE +Stop +Verkauf am schwachen Hoch | +33.5 % | 11. | -6.7 % | 41. |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | +23.6 % | 32. | -4.9 % | 35. |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | +19.4 % | 44. | -4.1 % | 34. |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | +35.9 % | 6. | -7.1 % | 44. |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | +38.6 % | 2. | -5.5 % | 38. |
| LIVE +Stop +Sperre 48 h nach Stop | +32.5 % | 14. | -0.9 % | 29. |
| LIVE +Stop +Mindest-Stopabstand 2 % | +31.5 % | 15. | -0.5 % | 26. |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | +24.8 % | 31. | -0.5 % | 27. |
| LIVE +Stop +alle vier neuen Hebel | +25.4 % | 30. | -5.9 % | 39. |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | +30.4 % | 17. | +3.2 % | 15. |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | +34.4 % | 9. | +1.1 % | 23. |
| NEU-LIVE +Verkauf unter dem letzten Hoch | +31.5 % | 16. | +3.1 % | 17. |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | +28.9 % | 20. | -0.3 % | 25. |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | +25.9 % | 29. | -0.3 % | 24. |
| NEU-LIVE +kein Gegengeschaeft je Kerze | +28.4 % | 21. | +2.4 % | 19. |
| NEU-LIVE +Ziele festhalten | +21.2 % | 40. | +3.8 % | 14. |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | +27.5 % | 23. | +3.2 % | 16. |
| NEU-LIVE +Mindest-Bein 5 % | +26.4 % | 27. | +8.8 % | 9. |
| NEU-LIVE +groesstes Bein | +21.4 % | 38. | -3.2 % | 31. |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | +21.4 % | 39. | -3.2 % | 32. |
| NEU-LIVE +Bein in Handelsrichtung | +26.6 % | 26. | +4.8 % | 13. |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | +26.9 % | 25. | +8.8 % | 10. |
| NEU-LIVE +Break-even im Plus | +13.3 % | 46. | +2.4 % | 20. |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | +11.4 % | 48. | -3.9 % | 33. |
| LIVE +Widerstand des Gegen-Beins | +19.5 % | 43. | +8.9 % | 8. |
| LIVE +Widerstand statt Verkauf am letzten Hoch | +21.5 % | 37. | +9.1 % | 7. |
| LIVE +Rest halten | +7.4 % | 50. | +14.1 % | 2. |
| LIVE +Rest halten +Neustart mit Rest | +22.2 % | 36. | +14.3 % | 1. |
| LIVE +Neustart mit Rest (ohne Halten) | +26.4 % | 28. | +9.7 % | 5. |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | +27.0 % | 24. | -3.1 % | 30. |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | +32.8 % | 13. | -4.9 % | 36. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | +23.1 % | 33. | +9.2 % | 6. |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | +22.3 % | 35. | +8.1 % | 11. |
| LIVE-heute +Neustart mit Rest | +23.1 % | 34. | +10.8 % | 4. |
| LIVE-heute +Rest halten +Neustart mit Rest | +19.7 % | 42. | +13.8 % | 3. |
| Long+Short (Ref) | +1.8 % | 51. | -0.7 % | 28. |

**In BEIDEN Haelften unter den besten 5:** keine einzige Variante

**Wie viel davon waere blosser Zufall?** Bei 51 Varianten und je 5 Plaetzen liegt der Erwartungswert bei reinem Zufall bei **0.5** Varianten. Gemessen: **0**. Das ist nicht mehr als der Zufall ohnehin liefert — die Rangfolge oben ist damit KEIN Beleg. Dann nur den groben Hebeln trauen (Richtung, Kaufleiter, Flush) und die Feinheiten weglassen.

Unabhaengig davon belastbar ist der **maximale Rueckgang**: Er haengt an der Zahl und der Qualitaet der Positionen, nicht daran, welche einzelnen Trades gut liefen. Wo zwei Varianten aehnliche Rendite haben, ist die mit dem kleineren Rueckgang die verlaesslichere Wahl — auch wenn ihre Platzierung schwankt.

## Einschraenkungen

- Open Interest + Liquidationen: **echt von Coinalyze** — 1504 OI-Punkte, 1505 Liq-Punkte im Zeitraum. Muster 4 (Kapitulation) aktiv.
  (4h-Reichweite von Coinalyze deckt evtl. nicht bis Sep'25 zurueck; aeltere Kerzen dann OI neutral.)
- Spot-CVD real (Binance Vision), Funding real (Kraken, sofern Historie reicht).
- Kaisers Liste enthielt Duplikate (laut Kaiser evtl. Versehen) -> dedupliziert.

Empfehlung: Variante 'LIVE +Rest halten +Neustart mit Rest' schneidet nach Rendite am besten ab. ABER Vorsicht: eine Variante, die nur durch WENIGE Signale (niedriger Recall) hoch rentiert, ist fragil (Glueck, nicht Koennen) — auf Rendite MIT anstaendiger Treffer-Quote achten. Filter (trend_filter/strict_confirm/confluence) sind in strategy_core.evaluate schaltbar; Default erst nach Bestaetigung setzen.