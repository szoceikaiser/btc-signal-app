# Auswertung: Furkan-Update vom 02.08.2026 (Makro-Video)

Quelle: `Videos/260802/260802_Transkript.txt` · ausgewertet 2026-08-27.
Aufbau wie bei den Juli-Auswertungen: nur das, was sich auf unsere Engine auswirkt.
Marktmeinung (Yen-Intervention, Russland, Wallet-Hack) bleibt draußen.

## 1. Seine Fib-Levels gegen unsere — GEPRÜFT, sie stimmen exakt überein

Er nennt bei 15:51 seine Nachkaufzone: *„das ist hier das [Fib-]Retracement zwischen
61.300 und 61.000 US-Dollar"*, dazu die Liquidationszone *„ab 61.700 runter bis 60.500"*.

Rückgerechnet aus diesen zwei Zahlen mit **unserer** Fib-Definition (0.618 / 0.65):

| | |
|---|---|
| aus 61.300 = 0.618 folgt ein Bein-Tief von | 57.804 |
| aus 61.000 = 0.65 folgt ein Bein-Tief von | 57.793 |

Beide Rechnungen zeigen auf dasselbe Tief. Nachgeschlagen in den Binance-Tageskerzen:

- **Tief 57.800,19 $ am 01.07.2026**
- **Hoch 66.956,15 $ am 21.07.2026** (sein *„hochgelaufen auf knapp 67.000"*)

Damit ergibt unsere eigene Formel auf sein Bein:

| Level | Wert | Furkan sagt |
|---|---|---|
| 0.5 | 62.378 | — |
| **0.618** | **61.298** | **„61.300"** |
| **0.65** | **61.005** | **„61.000"** |
| 0.786 | 59.760 | — |
| Invalidierung (1.0) | 57.800 | — |

**Befund: Unsere Fib-Mechanik ist identisch mit seiner. Kein einziger Zahlenunterschied.**
Was auseinandergeht, ist ausschließlich die Frage, **über welches Bein** gezeichnet wird.

## 2. Genau da liegt der blinde Fleck — das Referenz-Bein

Was unsere Engine am selben Tag sah (Engine-Stand aus der Repo-Historie,
Commit d023500 vom 02.08.2026 20:50 UTC):

```
"richtung": "SHORT", "impuls_start": 65409.56, "impuls_ende": 62275.0
gp_upper 64212 · gp_lower 64312 · invalidation 65409 · Position: FLAT
```

Das ist das Hoch vom 31.07. gegen das Tief vom 01.08. — ein **Zwei-Tage-Bein von 4,8 %**,
und es zeigt nach unten. Furkan zeichnet zur selben Stunde ein **Drei-Wochen-Bein von
15,8 %**, und es zeigt nach oben.

Folge an diesem Tag: Seine Zone lag bei 61.000–61.300 (unter dem Kurs, ein Nachkauf-Level
für seinen laufenden Long), unsere bei 64.212–64.312 (über dem Kurs, ein Short-Setup).
Da `bias_short=false` live steht, war unsere Engine damit **handlungsunfähig**: Die einzige
Struktur, die sie sah, durfte sie nicht handeln.

### Das war kein Einzeltag

Aus der Repo-Historie, ein Eintrag je Tag (letzter Engine-Lauf des Tages):

| Zeitraum | Zustand der Engine | Vorschau-Bein |
|---|---|---|
| 27.07.–25.08.2026 | **durchgehend FLAT**, kein einziger Einstieg | Median **4,0 %**, kleinstes 1,0 % |
| Richtungswechsel der Vorschau | LONG/SHORT wechseln fast täglich | an 15 von 31 Tagen SHORT = gesperrt |
| 26.08.2026 | erster Einstieg (T1, 25 %) | 7,6 % |

In genau diesem Monat stieg Bitcoin von 63.000 auf 78.800 (+25 %). **Die Engine war den
gesamten Anstieg über flach.** Damit ist die offene Frage aus dem letzten Backtest
(„warum nur +0,4 % im August?") beantwortet — und die Antwort ist nicht die
Gewinnmitnahme, sondern der fehlende Einstieg.

### Die Mechanik dahinter (und warum zwei richtige Regeln zusammen blockieren)

1. `last_significant_impulse` nimmt das **jüngste** Bein, das ≥ 3 % oder ≥ 2×ATR misst.
   Kleine Beine erfüllen das laufend — das große Bein darüber wird nie betrachtet.
2. Ein kleines Bein hat einen kleinen Abstand zwischen Golden Pocket und Invalidierung:
   bei 1,9 % Beinlänge sind es rund 1,2 %.
3. `min_stop_pct = 0.02` verwirft jeden Einstieg unter 2 % Stop-Abstand — die im Juli
   *beste gemessene Einzelregel*.

Jede Regel für sich ist richtig und gemessen. Zusammen ergeben sie: **Die Engine zeichnet
Beine, die für ihre eigene Mindestanforderung zu klein sind.** Sie schließt sich selbst aus.

### Was unsere eigene Spezifikation dazu sagt

`docs/STRATEGIE.md` §4.1 fordert beides, was hier fehlt:

- Punkt 3: *„Referenz-Impuls = der jüngste signifikante, abgeschlossene Impuls
  **in Trendrichtung**"* — die Trendrichtung wird nirgends geprüft.
- Punkt 4: *„Auf 1D zusätzlich das größere Bild für übergeordnete Pockets
  (**beide Ebenen überwachen**; Konfluenz 4h+1D = stärkste Zone)"* — wir überwachen eine.

Der Schalter `confluence` (E8.5) ist **nicht** diese Umsetzung: Er benutzt die 1D-Zone als
Filter für 4h-Setups („liegt die kleine Zone in der großen?"), nicht als **eigene**
Einstiegszone. Gemessen wurde also nie, was Furkan tut.

**Gegenrechnung für den 01.08.2026:** Mit seinem Bein hätte unsere Engine ein 0.5-Level bei
62.378 gehabt. Das Tagestief am 01.08. war 62.275 — der Kauf wäre ausgelöst worden, mit
7,3 % Stop-Abstand (also weit über der 2-%-Hürde). Das ist EIN Datenpunkt und ersetzt keinen
Backtest, zeigt aber, dass die Blockade am Bein hängt und nicht an der Vorsichtsregel.

## 2b. NACHTRAG: was die Video-Frames zeigen (27.08.2026)

Kaiser hat das Video nachgereicht. Frames in `Videos/260802/frames/`. Sie bestätigen die
Rückrechnung aus Abschnitt 1 und liefern drei Dinge, die im Transkript nicht stehen.

**Sein Fib-Raster, direkt abgelesen** (Frame 16:45, TradingView, BTCUSDT.P auf BingX):

| Level | im Chart | unsere Rechnung (Binance) |
|---|---|---|
| 1 (Bein-Tief) | 57.802,4 | 57.800,19 |
| 0.786 | 59.757,7 | 59.760 |
| **0.65** | **61.000,4** | 61.005 |
| **0.618** | **61.292,8** | 61.298 |
| 0.5 | 62.371,0 | 62.378 |
| 0 (Bein-Hoch) | 66.939,7 | 66.956,15 |

Die Abweichung von rund 5–15 $ ist der Unterschied zwischen BingX-Perp und Binance-Spot.
**Die Methode ist dieselbe, bis auf die zweite Nachkommastelle.** Das Golden Pocket ist im
Chart als graue Box markiert — das ist die Zone, in der seine Limit-Order liegt.

**1. Er führt ZWEI Fib-Raster gleichzeitig.** Neben dem großen Aufwärts-Bein liegt ein
zweites Raster vom selben Hoch nach unten (1 = 66.939,7 · 0.786 = 66.209,1 · 0.618 =
65.694,7 · 0.5 = 65.299,3 · 0.382 = 64.924,0 · 0 = 63.708,9). Das große liefert die
Kaufzone unter dem Kurs, das kleine die Widerstandszone darüber.

Damit ist der Befund aus Abschnitt 2 schärfer als gedacht: Unsere Engine wählt **eines von
beiden aus** — und nahm an jenem Tag genau das kleine, abwärtsgerichtete, das sie bei
`bias_short=false` nicht handeln durfte. Furkan muss nicht wählen, er hat beide.
Genau das meint STRATEGIE.md §4.1 Punkt 4 mit „beide Ebenen überwachen".

**2. Er arbeitet auf 2h (TradingView) und 1h (OKX).** Unsere Engine wertet 4h-Kerzen aus.
Auf 2h entstehen mehr und feinere Pivots — sein großes Bein bleibt trotzdem das
Bezugssystem. Der Zeitrahmen ist also nicht der Grund für den Unterschied; die Auswahl ist es.

**3. Seine Order-Marker im OKX-Chart** (Frame 15:55) liegen bei rund 59.400–59.700 (Kauf,
01./02.07.) und darüber zwei Verkäufe — deckt sich mit „Entry 59.696, zweimal Gewinne
realisiert". Sein Einstieg lag also am Tief des Beins, nicht im Golden Pocket; das Pocket
ist für ihn die **Nachkauf**-Zone. Das passt zu unserer Kaufleiter, nicht zum Ersteinstieg.

## 3. Neu und nicht in unserer Engine: zwei On-Chain-Niveaus

Beide sind **Preisniveaus, die nicht aus der Kursstruktur kommen** — davon kennt unsere
Engine bisher keins (sie kennt nur Pivots, Fib-Levels und Liquidations-Cluster).

- **Kostbasis der kurzfristigen Halter, 13:55:** *„was immer noch fehlt, ist, dass wir über
  die Kostbasis der kurzfristigen Investoren kommen. Die liegt aktuell bei über 67.000."*
  Sein Muster aus früheren Bärenmärkten: Breakout darüber → Retest → Aufwärtsbewegung.
  **Beobachtung im Nachhinein:** Bitcoin überschritt 67.000 am 18./19.08.2026 und lief
  danach auf 79.500. Das stützt seine These — es ist aber ein einzelner Fall, und ob die
  Kostbasis im August noch bei 67.000 lag, wissen wir nicht.
- **MVRV-Valuezone, 13:14:** aktuell 55.250 bis 46.700 $, dort kauft er **Spot** nach.
  Kaiser hat die Valuezone als Spot-Ebene bereits abgelehnt (kauft kein Spot, E11) — das
  bleibt richtig. Offen ist weiterhin die andere Verwendung: derselbe MVRV-Z als
  **backtestbarer Richtungs-Bias** anstelle des pausierten KI-Makro-Bias (E8.5).

## 4. Bestätigt, was wir schon haben

- **Break-even-Stop bei jeder Aufstockung** (16:07–16:25): *„wenn ich die Order gefüllt
  bekomme, würde ich meinen Stop … hochsetzen auf das neue Entry. Mit der Position möchte
  ich nicht mehr in Verlust gehen."* Das ist wörtlich der offene Punkt aus
  `FURKAN-UPDATE-2026-07-B.md` (Video B, 18:50) — jetzt ein zweites Mal belegt. Unser
  `trail_stop` zieht bisher **erst nach einem Teilgewinn** nach, nicht nach jeder Aufstockung.
- **Liquidationszone + Golden Pocket als Konfluenz** (15:39–15:59): genau unser
  `liq_entry="boost"`, seit 28.07. live.
- **Runter spiken, Stops auslösen, dann hoch** (16:41–16:58): unser `flush_entry="core"`.
- **Spot-CVD trägt nicht, Futures-CVD hält stärker** (15:07–15:32): unser Muster 2
  (Derivate-Pump). Er zieht daraus keine Verkaufsregel, sondern steuert die Positionsgröße.
- **Tranchen, dynamisch, nie alles auf einmal** (13:38): Grundprinzip, seit E1 abgebildet.

## 5. Vorschlag zur Reihenfolge

1. **Referenz-Bein (Abschnitt 2) angehen** — das ist der einzige Punkt in dieser Auswertung,
   der einen ganzen Monat Untätigkeit erklärt. Denkbare Umsetzungen, jede schaltbar und
   einzeln messbar:
   a) Beim Zeichnen das **größte** signifikante Bein der letzten N Kerzen bevorzugen statt
      des jüngsten;
   b) die **1D-Zone als eigenständige Einstiegszone** führen (nicht als Filter), also
      zwei Zonensätze gleichzeitig überwachen — das ist §4.1 Punkt 4 wörtlich;
   c) eine **Mindest-Beinlänge** (z. B. 8 %) für die Zonenwahl, damit Mikro-Strukturen gar
      nicht erst zur Referenz werden.
2. **Break-even-Stop auch nach Aufstockungen** (Abschnitt 4) — klein, zweimal belegt.
3. STH-Kostbasis als Niveau: erst beobachten, ob wir überhaupt eine verlässliche kostenlose
   Quelle dafür haben, bevor daraus eine Regel wird.

## 6. Was das Video NICHT liefert

Keine neue Order-Flow-Regel, keine Schwellenwerte, keine Änderung an den Fib-Levels.
Der Wert dieses Videos für uns liegt vollständig in Abschnitt 2 — und der war nur zu
finden, weil er zufällig zwei konkrete Zahlen genannt hat (61.300 / 61.000), an denen sich
sein Bein zurückrechnen ließ.
