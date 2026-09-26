# E32 — Lage-Information in Plan und Vorschau

Status: E32.1 FERTIG (live) · E32.3 GEMESSEN und VERWORFEN (13.09.2026)

## Problem aus Kaisers Sicht

> „Es schaut sich immer die orderflow daten an und auch die spot nachfrage. insofern
> wäre es wichtig in den telegramm nachrichten beim auswerten der indikatoren: info zu
> erhalten ob short spot nachfrage stabil ist oder nicht, ob sie wiedergekehrt sind,
> oder nachgelassen hat. … **ich bekomme die info zur struktur nur, wenn ich eine
> nachricht für ein nachkauf erhalte. doch das ist zu spät, weil ich doch die limits
> vorher setze.**"

Der letzte Satz ist der Kern. Die Engine erfasst den kompletten Order-Flow, wertet ihn
aus — und behält das Ergebnis für sich, außer es steht zufällig im Grund eines Signals.

**Nachgeprüft am Code (12.09.2026):** `format_vorschau()` und `format_plan()` in
`telegram_notify.py` enthalten **keine einzige Zeile** über Order-Flow. Die Vorschau
nennt Zonen und Stop, der Plan nennt Marken und Stop. Nichts über Spot-Nachfrage,
nichts über das erkannte Muster, nichts über die Struktur.

## Beleg aus dem Video vom 10.09.2026

Furkan liest bei Velo fünf Panels, die alle ihre Entsprechung in der Engine haben:

| Sein Panel | Feld in der Engine |
|---|---|
| Aggregated Spot Volume | `FlowPoint.spot_cvd` |
| Aggregated Volume (Futures) | `FlowPoint.fut_cvd` |
| Aggregated Open Interest | `FlowPoint.oi` |
| Aggregated Funding | `FlowPoint.funding` |
| Aggregated Liquidations | `FlowPoint.long_liq` / `short_liq` |

Wörtlich bei 17:22: *„Was wir aber auch sehen ist, dass auch Spot natürlich verkauft
worden ist in dieser Bewegung rein. Was wir jetzt sehen wollen, ist bei einer
Gegenbewegung nach oben hin, dass wieder die Spot Nachfrage kommt und nicht nur ein
Short Liquidierungsevent stattfindet. Das ist ganz wichtig."*

**Wichtige Unterscheidung, die Furkan sauber trennt und die den Bau bestimmt:**

- *„Ist die Struktur intakt?"* beantwortet er am **Preis** — 21:10: „höhere Hochs,
  höhere Tiefs, also die Struktur ist nicht gebrochen". Das ist unsere `trend_intakt`-
  Regel aus E30.
- *„Ist die Bewegung gesund?"* beantwortet er am **Order-Flow** — die Spot-Nachfrage
  prüft nicht die Struktur, sondern die Qualität der Bewegung.

Beides gehört in die Nachricht, aber als zwei getrennte Angaben.

## Soll-Zustand (E32.1)

Eine Lage-Angabe in **PLAN** und **VORSCHAU** — also in Nachrichten, die Kaiser
ohnehin bekommt, bevor er die Limit-Orders setzt.

```
Lage:  Struktur intakt — höheres Tief 76.264, höheres Hoch 82.300
       Spot-Nachfrage nachgelassen (Netto-Verkäufe in den letzten 3 Kerzen)
       Muster: ungesunder Abverkauf (der Dip wird nicht gekauft)
```

### Spot-Nachfrage — vier Zustände

`spot_cvd` ist ein kumuliertes Delta. Die Differenz über ein Fenster ist damit die
Netto-Nachfrage in diesem Fenster. Verglichen werden das jüngste Fenster und das
davor (je 3 Kerzen = 12 Stunden):

| jetzt | davor | Text |
|---|---|---|
| > 0 | > 0 | **stabil** — Nachfrage trägt |
| > 0 | ≤ 0 | **zurückgekehrt** — Käufer sind zurück |
| ≤ 0 | > 0 | **nachgelassen** — die Nachfrage hat gedreht |
| ≤ 0 | ≤ 0 | **schwach** — Verkaufsdruck hält an |

Kaisers drei Zustände plus der vierte Fall, den er nicht genannt hat, der aber
vorkommt und unterschieden werden muss.

### Struktur

| Lage | Text |
|---|---|
| dasselbe Bein wie beim Einstieg | **unverändert** |
| neues Bein, Trend fortgesetzt | **intakt** — höheres Tief X, höheres Hoch Y |
| neues Bein, Trend gebrochen | **gebrochen** — das neue Bein liegt tiefer |
| kein Bein / zu wenig Daten | nichts ausgeben |

### Muster in Klartext

`Pattern.UNGESUNDER_ABVERKAUF` sagt Kaiser nichts. Übersetzt:

| Muster | Text |
|---|---|
| GESUNDER_TREND | gesunder Trend (Spot trägt die Bewegung) |
| DERIVATE_PUMP | Derivate-Pump (Hebel treibt, Spot fehlt) |
| SHORT_COVERING | Short-Covering (Shorts decken sich ein) |
| CAPITULATION_RESET | Kapitulation (der Markt ist ausgeräumt) |
| UNGESUNDER_ABVERKAUF | ungesunder Abverkauf (der Dip wird nicht gekauft) |
| NEUTRAL | neutral |

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `engine/strategy_core.py` | neue Funktion `lage_bericht()` + Dataclass `Lage`; Klartext-Tabelle der Muster |
| `engine/main.py` | Lage berechnen und in die Dicts für Plan und Vorschau legen |
| `engine/telegram_notify.py` | Lage in `format_plan()` und `format_vorschau()` ausgeben |
| `engine/test_strategy_core.py` | Tests der vier Spot-Zustände und der Struktur-Fälle |
| `engine/test_telegram_notify.py` | Test, dass die Zeile in beiden Nachrichten erscheint |

## Warum hier KEIN Backtest nötig ist

Die Projektregel „alles schaltbar, Default aus, per Backtest messen" zielt auf
Mechanismen, die **Signale verändern**. E32.1 ändert kein einziges Signal — es ist
reine Anzeige in Nachrichten, die ohnehin verschickt werden. Ein Backtest könnte
dazu nichts messen, weil sich an Ein- und Ausstiegen nichts ändert.

Was trotzdem gilt: Tests **und** Gegenproben. Ein Test, der auch bei absichtlich
kaputter Logik grün bleibt, ist wertlos.

## Bewusst NICHT gemacht

- **Keine neue Telegram-Nachricht.** Die Lage geht in bestehende Nachrichten. Kaisers
  Restliste nennt „Nachrichtenzahl senken" als offenen Punkt — eine eigene Lage-Meldung
  wäre das Gegenteil. Sie kommt als E32.2 mit Schalter und Default aus.
- **Keine Handelsregel.** Die Lage sperrt nichts und löst nichts aus. Wer aus der
  Spot-Nachfrage eine Kaufsperre machen will, baut `block_unhealthy` aus — der ist
  gemessen und schlechter.
- **Nicht das große Bein.** Der eigentliche Hebel (Furkan führt drei Fib-Raster
  gleichzeitig, das größte 62.200 → 82.000) ist E32.3 und braucht einen Backtest.

## Etappen

- **E32.1 — Lage in Plan und Vorschau.** Status: in Arbeit
- **E32.2 — Meldung bei Wechsel der Spot-Lage.** Schaltbar, Default aus. Status: OFFEN
- **E32.3 — Zweiter Zonensatz aus einem großen Bein.** Muss gemessen werden. Status: OFFEN

---

# E32.3 — Eigene Swing-Weite für die 1D-Ebene

Status: gemessen 13.09.2026 — **verworfen, Schalter bleibt aus**

## Der Befund, der alles ändert: E23 hat nie Furkans Ebene gemessen

`daily_fib_zone()` wurde von E23 mit `pivot_n` aufgerufen — der Swing-Weite, die für
**4h-Kerzen** eingestellt ist (5). Auf Tageskerzen ist das sehr fein: Schon ein kleines
Zwischentief zählt als Swing, und `bein_wahl="juengstes"` nimmt danach das kleine, junge
Bein. Die „1D-Ebene" war damit **nicht** Furkans übergeordnete Ebene, sondern dieselbe
Feinstruktur auf gröberen Kerzen.

**Nachgerechnet mit echten Tageskerzen (Binance, Stand 12.09.2026):**

| Swing-Weite auf 1D | gefundenes Bein | Spanne | Golden Pocket |
|---|---|---|---|
| n=5 (was E23 tat) | 76.264 → 82.300 | 8 % | 78.377 – 78.570 |
| **n=8** | **62.535 → 82.300** | **32 %** | **69.453 – 70.085** |
| n=12 | kein Bein | — | — |

Furkan im Video vom 10.09.2026 (20:41): *„das Golden Pocket aus dieser Bewegung von
62.000 auf 82.000"* — im Chart abgelesen **69.000–70.000**. Das trifft **n=8**, nicht n=5.

Damit ist auch klar, warum E23 durch die Robustheitsprüfung fiel: Es maß gar nicht, was
es messen sollte.

## Der Preis — ehrlich gehalten

Ein Pivot bei n=8 braucht **acht Tageskerzen rechts** zur Bestätigung. Über die letzten
21 Tage geprüft:

- n=5 lieferte **durchgehend** ein Bein.
- n=8 lieferte an **8 von 21 Tagen gar keines** — die Zone erscheint später und
  verschwindet zwischenzeitlich.

Die gröbere Ebene ist träger. Ob sich das lohnt, **kann diese Analyse nicht beantworten** —
sie steht auf 45 Tageskerzen und einem einzigen Zeitpunkt. Das entscheidet der Backtest.

## Umsetzung

Neuer Parameter `pivot_n_1d` (Default **0** = wie `pivot_n`, also exakt das bisherige
Verhalten). Kein neuer Mechanismus, keine neue Zonenlogik — nur die Trennung zweier
Weiten, die bisher dieselbe waren.

| Datei | Änderung |
|---|---|
| `engine/strategy_core.py` | `daily_fib_zone()` und `evaluate()` bekommen `pivot_n_1d` |
| `engine/main.py` | `EVAL_DEFAULTS` um `"pivot_n_1d": 0` |
| `engine/backtest.py` | `EVAL_KEYS`, `_BASE` und **drei Gitterzeilen** |

## Die drei Gitterzeilen

| Zeile | Zweck |
|---|---|
| `LIVE-heute +1D-Ebene grob (n=8)` | die Hypothese: Furkans Ebene |
| `LIVE-heute +1D-Ebene fein (n=5, Gegenprobe zu E23)` | trennt „1D-Ebene" von „gröbere Weite" |
| `LIVE-heute +1D-Ebene sehr grob (n=12)` | prüft, ob noch gröber noch besser wäre |

Die mittlere Zeile ist die wichtigste: Ohne sie wüsste man hinterher nicht, ob ein
Unterschied von der zweiten Ebene kommt oder von der Weite.

## Tests und Gegenproben

186 Tests grün. Vier Sabotagen, alle gefangen:

| Eingriff | gefangen von |
|---|---|
| `pivot_n_1d` wird ignoriert | 2 Tests |
| `0` nimmt fälschlich 8 statt `pivot_n` | 7 Tests |
| Parameter wird von `evaluate()` nicht durchgereicht | `test_pivot_n_1d_kommt_durch_evaluate_an` |
| Panel-Zeile wandert fälschlich mit | `test_ohne_flush_zeile_unterscheidet_sich_nur_im_flush` |

Der dritte Punkt war beim ersten Anlauf **nicht** gefangen: Der Test prüfte nur
`daily_fib_zone()` direkt, nicht den Weg durch `evaluate()`. Dieselbe Lehre wie dreimal
zuvor in diesem Projekt — deshalb der eigene Verdrahtungstest.

## Bewusst NICHT gemacht

- **Nichts live geschaltet.** `pivot_n_1d` steht auf 0, `zonen_1d` bleibt aus. Die
  Live-Einstellung ist unverändert; ein Test hält fest, dass der Parameter ohne
  `zonen_1d` gar nichts tut.
- **Kein neues Auswahlverfahren.** `bein_wahl="groesstes"` wäre die naheliegende
  Alternative — sie ist gemessen und schlecht (Aufwärts-Beteiligung 11 %).
- **Die 4h-Ebene bleibt unberührt.** `pivot_n` ändert sich nicht.

## Ergebnis der Messung (13.09.2026, Bericht-Stand 08:23 UTC)

**Die Hypothese ist widerlegt. Deutlich.**

| Variante | Rendite | max. Rückgang | Signale | Aufwärts | Abwärts |
|---|---|---|---|---|---|
| LIVE-heute +Zonen nachziehen (live) | **+31,4 %** | **−9,7 %** | 251 | 47 % | **−11 %** |
| +1D-Ebene grob (n=8) — die Hypothese | +5,5 % | −22,9 % | 249 | 53 % | **+29 %** |
| +1D-Ebene fein (n=5, was E23 tat) | +21,6 % | −18,6 % | 266 | 58 % | +10 % |
| +1D-Ebene sehr grob (n=12) | +6,4 % | −22,0 % | 266 | 47 % | +23 % |

Robustheit (Fensterhalbierung), zweite Hälfte: die drei 1D-Varianten landen auf
**Platz 50, 54 und 55 von 55** — die schlechtesten Plätze des gesamten Gitters.

### Was schiefgeht — und warum es lehrreich ist

Die Aufwärts-Beteiligung steigt tatsächlich (47 → 53 %). Aber die **Abwärts-Beteiligung
dreht von −11 % auf +29 %**: Statt vom Rückgang verschont zu bleiben, macht die Engine
29 % davon mit. Der maximale Rückgang verdoppelt sich von −9,7 auf −22,9 %.

Das ist genau der Fall, den der Backtest-Bericht selbst beschreibt: *„steigen beide,
wurde nur das Risiko erhöht."*

Der Mechanismus dahinter: Ein zweiter Zonensatz aus einem 32-%-Bein heißt, dass die
Engine **tiefer und häufiger** kauft — mit einer Invalidierung bei 62.535, also einem
Stop, der 18 % entfernt liegt. Sie kauft in fallende Märkte hinein und hat keinen nahen
Ausstieg. Furkan tut oberflächlich dasselbe, aber mit einem entscheidenden Unterschied:

> **Seine Zonen sind Wartepositionen, keine Auslöser.**
> 18:16: *„Ich würde die Position jetzt erstmal noch nicht hochskalieren."*
> 20:54: *„wenn ich hier nicht aufstocke, weil mir die Orderflow Daten nicht gefallen
> in dem Moment …"*
> 22:24: *„Ich habe genug Cashreserven, um noch mal nachzuschießen."*

Er hat die Zone im Chart und kauft **trotzdem nicht**, solange der Order-Flow nicht
passt. Die Engine kauft, sobald der Preis die Zone berührt. Dieselbe Linie, zwei völlig
verschiedene Dinge.

### Was daraus folgt

- **`zonen_1d` bleibt aus, `pivot_n_1d` bleibt 0.** Nichts wird live geschaltet.
- **E23 war im Ergebnis richtig, in der Begründung unvollständig.** Die Weite war
  tatsächlich falsch gekoppelt (das war ein echter Fund) — aber mit der richtigen Weite
  wird es *schlechter*, nicht besser. Die alte Schlussfolgerung steht.
- **Der Parameter bleibt im Code.** Er kostet nichts (Default 0 = altes Verhalten), ist
  getestet, und die drei Gitterzeilen dokumentieren die Messung dauerhaft. Wer die Idee
  in einem Jahr wieder hat, sieht sofort, dass sie gemessen wurde.
- **Die eigentliche Lehre ist kein Parameter.** Furkans Vorsprung liegt nicht in der
  Zone, sondern darin, dass er sie nicht mechanisch handelt. Eine Engine, die ein
  32-%-Bein bekommt, aber weiter bei jeder Berührung kauft, wird dadurch nur riskanter.
  Das spricht für die *Anzeige* (E32.1, fertig) und gegen die *Regel*.
