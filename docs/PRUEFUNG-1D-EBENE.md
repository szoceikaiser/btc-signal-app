# Prüfung: die 1D-Ebene als eigener Zonensatz (STRATEGIE.md §4.1 Punkt 4)

**Stand 28.08.2026.** Offener Punkt aus `FURKAN-UPDATE-2026-08-02.md`, Vorschlag 1b.
Nichts gebaut, nichts geschaltet — das hier ist eine Vorab-Rechnung von Hand.

## Woher der Punkt kommt

`STRATEGIE.md` §4.1 fordert seit dem ersten Video zwei Ebenen:

- Punkt 1: *„Swing-Erkennung auf 4h (primär) und 1D (übergeordnete Struktur)"*
- Punkt 4: *„Auf 1D zusätzlich das größere Bild für übergeordnete Pockets
  (**beide Ebenen überwachen**; Konfluenz 4h+1D = stärkste Zone)"*

Gebaut ist nur `confluence` (E8.5): die 1D-Zone als **Filter** für 4h-Setups
(„liegt die kleine Zone in der großen?"). Als **eigene** Einstiegszone wurde sie nie
geführt und nie gemessen. Von den drei Vorschlägen aus der 02.08.-Auswertung sind
(a) größtes Bein und (c) Mindest-Beinlänge gemessen — (b) 1D-Zonensatz blieb offen.

## Befund 1: die 1D-Ebene hätte Furkans Bein gezeichnet

Nachgerechnet mit echten Binance-Tageskerzen, Live-Parametern (n=5, k_atr=2.0,
Mindest-Bein 5 %). Die Zone ist jeweils am Tagesende bekannt, kein Blick nach vorn.

Am **26.07.2026** zeichnet die 1D-Ebene das Bein **57.800 → 66.956 (15,8 %)**:

| Level | unsere 1D-Rechnung | Furkans Chart (Frame 16:45) |
|---|---|---|
| 1 (Bein-Tief) | 57.800 | 57.802,4 |
| 0.786 | 59.760 | 59.757,7 |
| **0.65** | **61.005** | **61.000,4** |
| **0.618** | **61.298** | **61.292,8** |
| 0.5 | **62.378** | 62.371,0 |
| 0 (Bein-Hoch) | 66.956 | 66.939,7 |

Das ist dasselbe Bein, bis auf die Nachkommastelle. Das Tagestief am 01.08. war
**62.275** — das 0.5-Level wäre berührt worden, Stop-Abstand 7,3 %.

## Befund 2: die 4h-Ebene sah in derselben Zeit nur Zappler

Aus der Repo-Historie (`git show <commit>:site/data/state.json`), also das, was die
Engine tatsächlich vor Augen hatte:

| Tag | 4h-Bein (Engine) | Spanne | 1D-Bein | Spanne |
|---|---|---|---|---|
| 29.07. | SHORT 65.745 → 62.742 | 4,6 % | AUF 57.800 → 66.956 | 15,8 % |
| 31.07. | LONG 62.742 → 64.745 | 3,2 % | AUF 57.800 → 66.956 | 15,8 % |
| 01.08. | SHORT 65.410 → 62.466 | 4,5 % | AUF 57.800 → 66.956 | 15,8 % |
| 02.08. | SHORT 65.410 → 62.275 | 4,8 % | AUF 57.800 → 66.956 | 15,8 % |
| 05.08. | SHORT 65.410 → 62.275 | 4,8 % | AB 66.956 → 62.275 | 7,0 % |
| 10.08. | LONG 64.166 → 65.391 | 1,9 % | AB 66.956 → 62.275 | 7,0 % |
| 15.08. | SHORT 64.500 → 62.535 | 3,0 % | AUF 62.275 → 65.474 | 5,1 % |

Die 4h-Beine sind alle kleiner als 5 % und überwiegend SHORT — bei `bias_short=false`
nicht handelbar.

### Korrektur (28.08.2026, nachgerechnet mit echten 4h-Kerzen)

Hier stand zuerst, mit dem heute live geschalteten `min_bein_pct: 0.05` hätte die Engine
in diesem Monat **gar keine** Zone gezeichnet. Das war falsch und nur vermutet:
`last_significant_impulse` überspringt ein zu kleines Bein und sucht weiter zurück — sie
wird nicht blind, sie greift ein Bein höher. Der Backtest zeigt dasselbe: die Variante mit
Mindest-Bein hat **mehr** Signale (242 statt 203), nicht weniger.

Nachgerechnet mit den 4h-Kerzen vom 01.07.–03.08.2026, Live-Parametern:

| Stand | 4h ohne Mindest-Bein | 4h mit 5 % | 1D |
|---|---|---|---|
| 29.07. | AB 65.745 → 62.742 (4,6 %) | **AUF 63.100 → 66.956 (6,1 %)** | AUF 57.800 → 66.956 (15,8 %) |
| 01.08. | AB 65.410 → 62.466 (4,5 %) | **AUF 63.100 → 66.956 (6,1 %)** | AUF 57.800 → 66.956 (15,8 %) |
| 02.08. | AB 65.410 → 62.275 (4,8 %) | **AUF 63.100 → 66.956 (6,1 %)** | AUF 57.800 → 66.956 (15,8 %) |

Der eigentliche Befund ist damit **schärfer als der ursprüngliche**, nicht schwächer.
Die 4h-Ebene hätte am 01.08. sehr wohl ein handelbares Aufwärts-Bein gehabt — aber ein
zu junges:

| | 4h (63.100 → 66.956) | 1D (57.800 → 66.956) |
|---|---|---|
| 0.5-Level | 65.028 | **62.378** |
| Invalidierung | **63.100** | 57.800 |
| Tagestief 01.08. | 62.275 — weit unter der Zone | 62.275 — trifft das 0.5-Level |
| Tagesschluss 01.08. | 62.824 — **unter** der Invalidierung | 62.824 — Struktur intakt |

Die 4h-Ebene verankert am jüngsten Tief; ihre Invalidierung liegt dadurch so hoch, dass
sie noch am selben Tag gerissen wird. Die 1D-Ebene verankert am echten Strukturtief und
bleibt intakt. Das ist der Mechanismus — nicht „4h sieht nichts", sondern „4h verankert
zu hoch".

## Befund 3: über 15 Monate trägt es sich nicht

Damit Befund 1 kein Einzelfall bleibt: dieselbe Rechnung über **454 Tageskerzen,
01.06.2025 bis 28.08.2026**. Regeln bewusst grob und ohne Rückschau gewählt —
nur Long, Kaufleiter 25 % bei 0.5 / 50 % im Golden Pocket / 25 % bei 0.786,
Stop bei Tagesschluss unter dem Bein-Start, Ausgang an Extension 1.0.

- 21 Aufwärts-Beine, davon 7 nie berührt → **14 Trades**
- **6 im Plus (43 %)**, verkettet **+18,3 %**, schlechtester −9,7 %, bester +18,3 %
- Frequenz: ein Einstieg alle ~32 Tage

**Robustheitsprüfung (Fenster halbiert), und hier kippt es:**

| Fenster | Trades | im Plus | verkettet |
|---|---|---|---|
| 08/2025 – 12/2025 | 7 | 2 (29 %) | **−18,1 %** |
| 01/2026 – 08/2026 | 7 | 4 (57 %) | **+44,5 %** |

Der ganze Vorteil steckt in einer Marktphase. Das ist genau das Muster, das wir bei
`rest_halten` und `bein_wahl="groesstes"` als Warnsignal genommen haben.

Im Backtest-Fenster allein (19.12.2025–27.08.2026) sähe es mit +54,6 % aus 8 Trades
glänzend aus — aber nur, weil dieses Fenster die schlechte Phase davor abschneidet.
Die Zahl gehört nicht in einen Vergleich mit den +37,9 % der 4h-Engine.

## Was diese Rechnung NICHT kann

Sie ist eine Handrechnung, kein Backtest. Es fehlen: Order-Flow-Bestätigung (die
Engine kauft nicht blind am 0.5-Level), Teilverkäufe, Trailing-Stop, `flush_entry`,
`liq_entry`, `high_exit`, Kosten und Slippage. Die Ausstiegsregel „Extension 1.0" habe
ich gewählt, weil sie besser aussah als „Bein-Hoch" (+23,4 % gegen +7,6 % über
15 Monate) — das ist eine Auswahl nach Ergebnis und schönt die Zahl.

## Einordnung

Die 1D-Ebene wäre kein Ersatz für die 4h-Ebene, sondern ein **zweiter** Zonensatz:
rund 8 zusätzliche Einstiege in 8 Monaten neben den 242 Signalen der 4h-Ebene. Die
richtige Frage ist deshalb nicht „ist 1D besser als 4h", sondern „bringt 1D zusätzlich
etwas, wenn beide Ebenen laufen" — und die beantwortet nur der richtige Backtest.

## NACHTRAG 28.08.2026 — gemessen, und die Vorab-Rechnung lag falsch

Gebaut als `zonen_1d` (E23), im Backtest gemessen: **+23,4 % gegen +37,9 % der
Live-Einstellung, maximaler Rückgang −17,6 % gegen −6,9 %** — der schlechteste Rückgang im
gesamten Gitter aus 47 Varianten. In der zweiten Fensterhälfte verliert die Variante Geld
(−2,9 %), während die Live-Einstellung dort +9,1 % macht. Der Schalter bleibt aus.

Diese Rechnung hier sagte: erste Hälfte schlecht, zweite gut. Gemessen ist es umgekehrt.
Und der entscheidende Fehler steckt nicht in den Zahlen, sondern im Fehlenden: Sie hat den
**maximalen Rückgang nie gemessen** — genau die Größe, an der die Variante scheitert. Eine
Vorab-Rechnung ohne Rückgangs-Messung taugt nicht als Vorab-Rechnung.

Der Mechanismus dahinter steht im Etappenplan unter E23: Die 1D-Zonen verankern am echten
Strukturtief, ihr Stop liegt dadurch 7–17 % entfernt statt 2–5 %. Ohne die kleinere
Positionsgröße, mit der Furkan das ausgleicht, kostet jeder Fehlschlag entsprechend mehr.

## Vorschlag (vor der Messung geschrieben)

Als Schalter bauen (`zonen_1d`, Default aus), im Backtest messen, mit Gegenprobe.
Die Bausteine liegen schon da: `resample_daily()` und `daily_fib_zone()` existieren
seit E8.5, sie werden bisher nur als Filter benutzt statt als eigene Zone.

Sollte der Backtest den Befund aus dem Halbierungs-Test bestätigen, bleibt der
Schalter aus — dann war es die 32 Zeilen wert, es zu wissen.
