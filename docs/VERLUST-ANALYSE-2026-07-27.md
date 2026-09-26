# Verlust-Analyse: Warum macht Furkan wenig Verluste — und wie schaffen wir das auch?

Stand: 2026-07-27 · Grundlage: kompletter Ordner gelesen (alle Docs, alle 3.382 Zeilen
Python, alle Datendateien, Transkript, beide Update-Auswertungen), 73/73 Tests grün,
eigene Nachrechnung der 208 Backtest-Signale auf Positions-Ebene.

---

## 1. Kurzurteil zur Strategie

**Die Strategie ist gut. Die Umsetzung handelt sie zu oft.**

Was belastbar ist:

- Der Kern (Golden Pocket + Order-Flow-Bestätigung + Tranchen) funktioniert: +29,8 %
  gegen Buy&Hold −30,3 % im selben Fenster. Das ist ein Unterschied von 60 Punkten in
  einem Bärenmarkt.
- Die Richtungs-Entscheidung (nur Long) ist der größte einzelne Hebel und ist sauber
  gemessen: +30 % gegen +2 % bei Long+Short.
- Die Halbierungs-Prüfung aus E11 war die richtige Entscheidung und hat gehalten.
- Der Code ist sauber, testbar, ehrlich dokumentiert. Die Selbstkritik in den Docs
  („Recall ≠ Gewinn", „Verkaufsseite ist auserzählt") ist ungewöhnlich diszipliniert.

Was nicht stimmt:

- **Die Trefferquote im Bericht ist geschönt** — nicht absichtlich, sondern durch einen
  Zählfehler. Dazu Abschnitt 3.
- **70 % aller Positionen enden im Stop.** 26 von 37.
- **Ein echter Bug** hat die Break-even-Absicherung und drei gemessene Mechanismen still
  ausgehebelt. Gefunden, behoben, Regressionstest dazu (Abschnitt 5).

---

## 2. Warum Furkan wenig Verluste macht

Fünf Gründe, alle aus dem Material belegbar — und in genau dieser Reihenfolge wichtig.

### 2.1 Er handelt 2,4-mal seltener

Aus deinen Notizen: 20 Kauf-Tage, die sich zu **11 Einstiegs-Clustern** in 6 Monaten
zusammenfassen (27.–30.10. ist EINE Position, nicht vier) = **1,8 Positionen pro Monat**.

Unsere Engine: **37 Positionen in 8,3 Monaten = 4,5 pro Monat**.

Jede Position ist eine neue Gelegenheit zu verlieren. Wer 2,4-mal so oft einsteigt, macht
bei gleicher Qualität 2,4-mal so viele Verlust-Trades. Das ist keine Meinung, das ist
Arithmetik. **Das ist der Hauptgrund.**

### 2.2 Sein Stop ist weiter weg, weil sein Bein größer ist

Sein eigenes Video-Beispiel (Frame 17:55, der Kauf am 08.01.2026):

| | Furkans Beispiel | unsere Engine (Median) |
|---|---|---|
| Größe des Impuls-Beins | **9,7 %** | ca. 6,5 % |
| Abstand Einstieg → Invalidierung | **3,59 %** | **2,28 %** |

Bei 15 von 37 Positionen liegt der Stop **unter 2 %** vom Einstieg. Bei vier Positionen
unter 0,6 %. Der Extremfall: **0,02 %** (29.04.) — dieser Stop war praktisch garantiert.

Ein 2-%-Stop liegt bei BTC innerhalb des normalen Tagesrauschens. Man wird nicht
ausgestoppt, weil man falsch lag, sondern weil der Markt atmet.

Ursache im Code: `pivot_n=5` / `k_atr=2.0` / `min_pct=3 %` lässt Beine ab ~3 % als
„signifikanten Impuls" durchgehen. Furkan zeichnet sein Fib auf Bewegungen von ~10 %.
`k_atr` steht seit E4b unverändert auf 2.0, `min_pct=0.03` wurde **nie** variiert.

### 2.3 Er steigt nach einem Stop nicht sofort wieder ein

Aus der Signalliste, Positionen der Reihe nach (S = Stop, V = Ziel/Rest):

```
S V V S S S S S S S V S V V S S S S S V V V V S S V S S S S S S S S S S V
```

**Die längste Serie: 10 Stops hintereinander** (Mai–Juli). Weitere Serien mit 7 und 5.
Der Median-Abstand zwischen einem Stop und dem nächsten Einstieg: **68 Stunden** — in
sieben Fällen unter 24 Stunden, in einem Fall 4 Stunden.

Das ist das klassische Sägeblatt: Die Zonen ändern sich nach einem Stop kaum, also steigt
die Engine fast an derselben Stelle wieder ein und wird fast an derselben Stelle wieder
gestoppt. Furkan wartet auf eine neue Struktur.

### 2.4 Er zieht den Stop hoch, sobald die Position im Plus ist

Zitat Update-Video B, 18:42: *„Ich werde bei Aufstockung immer wieder meinen Stop in
Profit oder auf Break even setzen, dass ich aus dieser Position keinen Verlust mehr
machen kann."*

Unser `trail_stop` zieht erst nach, wenn **Teilgewinne realisiert** sind. Genau die
Positionen, die über 4–5 Tranchen aufgebaut und dann ohne einen einzigen Teilgewinn
gestoppt wurden, sind unsere teuersten:

| Position | Tranchen | Ergebnis |
|---|---|---|
| 16.02. | 4 | −407 € |
| 06.03. | 5 | −423 € |
| 26.05. | 5 | −481 € |
| 16.06. | 4 | −418 € |
| 31.05. | 4 | −185 € |
| **Summe** | | **−1.914 € = 44 % aller Verluste** |

Dieser Punkt steht seit dem Update-Video als **OFFEN** im Etappenplan. Er ist billig zu
bauen und zielt genau auf das Problem.

### 2.5 Er entscheidet zuerst die Richtung, dann das Timing

Transkript 16:20: *„damit ich überhaupt erstmal meinen Bias habe: gehe ich eher long,
gehe ich eher short."* Sein Makrobild war im ganzen Zeitraum vorsichtig — er war
trotzdem long. Der Bias steuert bei ihm **Größe und Aggressivität**, nicht nur an/aus.

Das habt ihr für die Richtung gelöst (nur Long). Für die **Größe** noch nicht: Jede
Position geht mit bis zu 100 % des Kapitals rein, egal ob der Stop 0,5 % oder 5 % entfernt
liegt. Ein Setup mit doppelt so engem Stop bekommt dieselbe Größe — und verliert im
Zweifel doppelt so oft.

### 2.6 Ehrlichkeitshinweis

Es gibt keinen geprüften Track Record von Furkan. Was wir haben, sind deine Notizen zu
dem, was er in Videos zeigt. Menschen zeigen ihre guten Trades vollständiger als ihre
schlechten. Die fünf Punkte oben stimmen als **Methode** — ob seine Verlustquote
tatsächlich so niedrig ist wie es aussieht, kann niemand von außen prüfen.

---

## 3. Wo unsere Verluste wirklich herkommen (nachgerechnet)

Ich habe die 208 Signale der Live-Einstellung neu abgerechnet — nicht pro Verkauf,
sondern **pro Position** (Einstieg bis vollständiger Ausstieg). Kontrolle: mein Endstand
12.955 € gegen offizielle 12.976 € (0,2 % Abweichung durch die Bewertung der offenen
Position) — die Rechnung stimmt.

| | Bericht sagt | tatsächlich (pro Position) |
|---|---|---|
| Trades | 79 | **37** |
| davon im Gewinn | 61 = **77 %** | 21 = **57 %** |

**Der Bericht zählt jeden Teilverkauf als eigenen Trade.** Eine Position, die dreimal
Teilgewinn nimmt und dann im Minus gestoppt wird, erscheint als „3 Gewinne, 1 Verlust" —
tatsächlich ist sie ein Verlust. Im Code: `backtest.py`, `trades_closed += 1` in jedem
Verkaufszweig. Die 77 % sind nicht falsch gerechnet, sie messen nur etwas anderes als das,
wonach es klingt.

Die echten Zahlen:

- **37 Positionen · 21 Gewinner (+7.317 €) · 16 Verlierer (−4.362 €) · netto +2.955 €**
- Durchschnittsgewinn +348 €, Durchschnittsverlust −273 € → **Payoff 1,28 bei 57 % Trefferquote**
- **Gebühren 724 €** bei 167 Orders = **24 % des Nettogewinns**
- Mediane Haltedauer **32 Stunden**; 13 von 37 Positionen unter 24 Stunden

Payoff 1,28 bei 57 % ist ein dünner Vorsprung. Die Simulation rechnet mit exakten
Signalpreisen ohne Schlupf — bei 167 Orders kostet schon 0,05 % Slippage je Order weitere
~350 €, also gut 12 % des Gewinns.

---

## 4. Was messbar hilft (drei Hebel, nachgerechnet)

Nachträgliche Was-wäre-wenn-Rechnung auf **denselben** Signalen. Kein neuer Backtest —
Zahlen sind Richtungsangaben, keine Endergebnisse (siehe Abschnitt 6).

| Variante | Rendite | max. Rückgang | Rendite je Rückgangspunkt | Positionen | Verlust-Positionen | Verlustsumme | Treffer |
|---|---|---|---|---|---|---|---|
| **IST (Live)** | +29,5 % | −11,0 % | 2,7 | 37 | 16 | −4.362 € | 57 % |
| **A** Sperre 48 h nach einem Stop | +29,5 % | **−4,7 %** | 6,2 | 27 | 10 | −2.433 € | 63 % |
| **B** nur Setups mit Stop-Abstand ≥ 2 % | +20,6 % | −6,3 % | 3,3 | 22 | 9 | −2.649 € | 59 % |
| **A + B zusammen** | **+27,0 %** | **−3,7 %** | **7,3** | **18** | **6** | **−1.608 €** | **67 %** |

**A + B kostet 2,5 Punkte Rendite und liefert dafür:**

- ein Drittel des Rückgangs (−3,7 % statt −11,0 %)
- **62 % weniger Verlust-Positionen** (6 statt 16)
- **63 % weniger Verlustgeld** (−1.608 € statt −4.362 €)
- halb so viele Trades (18 statt 37), Gebühren 294 € statt 724 €
- risikobereinigt **2,7× besser** (7,3 gegen 2,7)

Halbierungs-Prüfung (dieselbe Logik wie E11) — beide Filter senken Rückgang **und**
Verlustzahl in **beiden** Hälften:

| | H1 Rückgang / Verlierer | H2 Rückgang / Verlierer |
|---|---|---|
| IST | −6,4 % / 9 von 18 | −11,0 % / 7 von 19 |
| A + B | **−3,7 % / 5 von 10** | **−2,2 % / 1 von 8** |

### Der Hebel, der NICHT hilft

**Risiko-normierte Positionsgröße** (Größe = Zielrisiko ÷ Stop-Abstand, also kleine
Position bei engem Stop) habe ich mitgemessen: 1 % Risiko → +8,5 %, 2 % → +16,5 %,
3 % → +20,7 %, 4 % → +25,8 %. Der Rückgang sinkt kaum mit. Die Idee ist theoretisch
richtig, aber sie behandelt nur das Symptom — sie macht die schlechten Setups klein,
statt sie wegzulassen. **Wegzulassen ist besser.**

Wichtig zur Abgrenzung: Das ist NICHT dasselbe wie die in E10.1 widerlegte Kapital-Reserve.
Die war ein gleichmäßiger Größenregler (Rendite fällt proportional). Hier wird
ungleichmäßig gewichtet. Ergebnis trotzdem: kein Gewinn gegenüber A + B.

### Reihenfolge

1. **A — Sperre nach einem Stop** (`cooldown_h`, Vorschlag 48 h). Größte Wirkung, kostet
   im Test null Rendite, wenige Zeilen Code.
2. **Break-even-Stop, sobald die Position im Plus ist** (Abschnitt 2.4). Steht schon als
   OFFEN im Plan, zielt auf 44 % der Verlustsumme. `entry_ref` existiert bereits — und
   funktioniert nach dem Bugfix aus Abschnitt 5 überhaupt erst richtig.
3. **B — Mindest-Stop-Abstand** (`min_stop_pct`, Vorschlag 2 % oder 1,5 × ATR).
4. Falls das nicht reicht: `k_atr` und `min_pct` hochsetzen (3,0 / 5 %), damit die Engine
   überhaupt nur noch Beine in Furkans Größenordnung zeichnet. Das ist der Eingriff an
   der Wurzel — er würde 1. bis 3. teilweise überflüssig machen, ist aber der größte
   Umbau und der einzige, der die Signalmenge grundlegend verändert.

Alle vier als schaltbare Parameter, Default aus, dann **einmal** den echten
Backtest-Workflow laufen lassen.

### Zum Einwand „E11 hat die Optimierung beendet"

Der Beschluss war richtig und gilt weiter für **Einstiegs-Mechanismen**, die um Rendite
konkurrieren. A und B sind etwas anderes: keine neuen Signalquellen, sondern
**Begrenzungen**, die die Zahl der Trades halbieren. Ihre Wirkung ist auch kein
2-Punkte-Rauschen, sondern eine Drittelung des Rückgangs, stabil über beide Hälften. Und
gemessen wurde beides bisher nie. Zwei Gitterzeilen sind dafür vertretbar.

---

## 5. Gefundener Fehler (behoben)

`strategy_core.py`, STOPLOSS-Zweig: Dort stand eine **handgeschriebene Teil-Rücksetzung**
der Position statt des zentralen `_reset_position()`. Fünf Felder wurden vergessen:
`entry_ref`, `entry_pct`, `liq_exits`, `high_exits`, `liq_entries`.

Zwei konkrete Folgen:

1. **Der Break-even-Stop rechnete mit einem falschen Einstand.** `entry_pct` summierte
   sich über *alle* gestoppten Positionen hinweg (im Test nach der ersten Position bereits
   145 %). Da neue Tranchen den Durchschnitt nur noch anteilig verschieben können, blieb
   `entry_ref` am Preis einer längst geschlossenen Position kleben. `trail_stop` nimmt für
   Long das **Maximum** der Kandidaten — ein zu hoch hängengebliebener „Einstand" setzt
   den Stop also zu hoch und stoppt zu früh.
2. **Drei gemessene Mechanismen waren teilweise abgeschaltet.** `liq_exits` (max 3),
   `high_exits` (max 2) und `liq_entries` (max 2) liefen gegen ihr Maximum und blieben
   dort, bis zufällig einmal über `VERKAUF_REST` geschlossen wurde — das passiert nur bei
   10 von 37 Positionen, dazwischen liegen Stop-Serien von bis zu 10. **Die Messungen aus
   E9.11, E10.2 und E10.3 („Liquidationsdaten bringen nichts") sind damit an einem
   gebremsten Mechanismus entstanden.** Ihr Ergebnis ist nicht zwingend falsch, aber es ist
   nicht sauber gemessen.

Behoben: Der Zweig ruft jetzt `_reset_position(pos)` wie überall sonst. Dazu ein
Regressionstest `test_stoploss_setzt_alle_zaehler_zurueck`. Gegenprobe gemacht — mit dem
alten Code ist der Test rot, mit dem Fix grün. **73/73 Tests grün.**

Zu tun: Kaiser pusht (`git pull --no-rebase && git add -A && git commit && git push`) und
lässt den Backtest-Workflow einmal laufen. Die Live-Einstellung nutzt `trail_stop=true`,
also wirkt Punkt 1 sofort.

---

## 6. Grenzen dieser Analyse

- Abschnitt 4 rechnet **nachträglich auf einer fertigen Signalliste**. Wird eine Position
  übersprungen, bliebe die echte Engine FLAT und könnte auf einer *anderen* Kerze
  einsteigen. Die Richtung stimmt, die genauen Prozente werden sich verschieben. Nur der
  echte Backtest-Lauf zählt.
- 37 Positionen sind wenig. Nach den Filtern bleiben 18. Bei so kleinen Zahlen entscheiden
  einzelne Trades mit.
- Das Fenster (18.11.2025–27.07.2026) ist ein Bärenmarkt: BTC −30 %. Eine Strategie, die
  Dips kauft und schnell aussteigt, hat es dort strukturell leichter als in einem
  Aufwärtstrend, wo dasselbe Verhalten Runner abschneidet.
- Die Simulation kennt keinen Schlupf. Bei 167 Orders ist das relevant (~350 € bei
  0,05 %/Order) und spricht zusätzlich für weniger Trades.
- Das Video-Transkript ist eine automatische Untertitel-Abschrift mit Fehlern
  („FIP Retracement", „ein Z ein Level"). Die Regeln in `STRATEGIE.md` stammen aus
  geprüften Video-Frames, das ist die verlässlichere Quelle.

---

## 6b. NACHTRAG: Messlauf nach dem Bugfix (2026-07-27, 19:56 UTC)

Backtest gelaufen, Ergebnisse aus dem Repo gelesen und positionsweise nachgerechnet
(meine Rechnung trifft die offiziellen +32,2 % auf die Nachkommastelle — die Zerlegung
stimmt).

### Der Fix wirkt genau dort, wo er wirken sollte

Alle Varianten **ohne** `trail_stop` und ohne Liquidations-Mechanismen haben exakt
dieselbe Signalzahl wie vorher (115 / 137 / 181 / 207 / 146). Der Eingriff war also
chirurgisch. Verändert haben sich nur die Varianten, die `entry_ref` oder die Zähler
benutzen — genau die Vorhersage aus Abschnitt 5.

Live-Einstellung (`LIVE +Stop nachziehen`), vorher → nachher:

| | vorher | nachher |
|---|---|---|
| Rendite | +29,8 % | **+32,2 %** |
| STOPLOSS-Signale | 26 | **19** |
| Positionen, die im Stop enden | 70 % | **56 %** |
| längste Stop-Serie | **10** in Folge | **5** |
| mediane Haltedauer | 32 h | **50 h** |
| Teilgewinne (TV1 / TV2) | 14 / 0 | **18 / 2** |

Der korrekt gerechnete Break-even-Stop hält Positionen länger am Leben und lässt sie
öfter am Ziel statt am Stop enden. Das war Punkt 1 der Fehlerbeschreibung.

### E10.3 kippt: Liquidations-Konfluenz war nie neutral, sie war abgeschaltet

Punkt 2 der Fehlerbeschreibung ist ebenfalls bestätigt — und deutlicher als gedacht:

| `LIVE +Stop +Liq-Konfluenz aufstocken` | vorher (Bug) | nachher (Fix) |
|---|---|---|
| Rendite | +29,7 % (= „exakt neutral") | **+37,0 %** |
| gegen Referenz | ±0,0 Punkte | **+4,8 Punkte** |
| Signale | 227 | 255 |
| Platz Hälfte 1 / Hälfte 2 | 1. / **15.** | 1. / **5.** |

Das Urteil aus E10.3 („boost ist exakt neutral, 19 Zusatz-Nachkäufe ohne jeden Effekt")
ist damit **hinfällig** — die Zähler waren nach wenigen Stops am Anschlag, der
Mechanismus lief die meiste Zeit gar nicht. `liq_exit` und `high_exit` wurden ebenfalls
neu gemessen und bleiben schlechter als die Referenz (Liq-Zonen +23,3 % gegen +32,2 %) —
**die Befunde von E9.11 und E10.2 halten, nur E10.3 dreht sich.**

### Die drei Hebel aus Abschnitt 4, neu gerechnet

| Variante | Rendite | max. Rückgang | Rend. je Rückgangspunkt | Positionen | Verlust-Positionen | Verlustsumme | Gebühren |
|---|---|---|---|---|---|---|---|
| IST (nach Fix) | +32,2 % | −11,8 % | 2,7 | 34 | 16 | −4.013 € | 686 € |
| A Sperre 48 h nach Stop | +30,0 % | −8,6 % | 3,5 | 27 | 12 | −2.804 € | 506 € |
| B Mindest-Stop-Abstand 2 % | +24,7 % | −6,4 % | 3,9 | 19 | 8 | −2.297 € | 329 € |
| **A + B zusammen** | **+31,6 %** | **−3,7 %** | **8,5** | **17** | **6** | **−1.677 €** | **298 €** |

**A + B ist nach dem Fix praktisch gratis geworden:** 0,6 Punkte Rendite (vorher 2,5)
gegen ein Drittel des Rückgangs, halb so viele Positionen, 10 Verlust-Trades weniger.
Risikobereinigt 3,1-mal besser. In beiden Hälften weniger Verlierer und weniger Rückgang,
in Hälfte 2 sogar mehr Rendite als die Live-Einstellung (+13,4 % gegen +10,7 %).

### Was ich davon empfehle — und was nicht

**Bauen: A + B.** Die Begründung ist nach dem Fix stärker, nicht schwächer.

**Vorsichtig bei `liq_entry="boost"`.** Es ist jetzt die beste gemessene Variante, es ist
Furkans ausdrücklich beschriebene Methode (Golden Pocket + Liquidationszone fallen
zusammen), und es kann strukturell wenig kaputtmachen — es fügt nur eine Nachkauf-Tranche
hinzu, höchstens 2× je Position, und blockiert nie einen Einstieg. Aber: Der Bericht sagt
selbst „nur 1 von 5 Varianten in beiden Hälften oben → die Rangfolge ist im Wesentlichen
Zufall", die Spanne in Hälfte 2 beträgt über 19 Varianten nur 5,5 bis 10,8 Prozentpunkte,
und die Schätzung für genau diese Variante ist durch **einen einzigen Bugfix um 7,3 Punkte
gesprungen**. Die Messgenauigkeit liegt also bei mehreren Punkten, nicht bei Nachkommastellen.

Mein Vorschlag: `liq_entry` ist deine Entscheidung, nicht meine. Wenn du umstellst, dann
in `site/data/config.json` auf `"boost"` — und `panel=True` in `backtest.py` muss auf
dieselbe Zeile wandern, sonst zeigt das Chart-Panel eine Rendite, die die Engine nicht
erzielt.

---

## 6c. NACHTRAG 2: Warum steigt die Engine bei ungesundem Order-Flow ein?

Kaisers Beobachtung (2026-07-27): *„Furkan steigt nur bei gesunden Indikatoren ein. Warum
wurde am 23.06., 16.06., 31.05. trotzdem gekauft, wenn es danach abwärts ging?"*

Nachgesehen in den Signal-Begründungen des Messlaufs — die Antwort steht dort wörtlich drin.

### Befund: 32 von 34 Ersteinstiegen ohne ein einziges gesundes Muster

| Muster beim Ersteinstieg | Anzahl |
|---|---|
| **keine Prüfung** (0.5-Level, KAUF 1) | **16** |
| **NEUTRAL** | **16** |
| GESUNDER_TREND | 1 |
| CAPITULATION_RESET | 1 |

Kaisers drei Beispiele: 31.05. und 16.06. waren KAUF-1-Einstiege am 0.5-Level, 23.06. ein
KAUF 2 „+ Bestätigung (NEUTRAL)". Alle drei hatten zusätzlich sehr enge Stops
(1,36 % / 2,0 % / **0,38 %**) — die beiden Probleme addieren sich.

### Drei Ursachen im Code

**(a) Der 0.5-Level-Einstieg prüft den Order-Flow überhaupt nicht.** In `evaluate` steht
im KAUF-1-Zweig keine einzige Flow-Bedingung — nur `_trend_ok` / `_confluence_ok` /
`_liq_entry_ok`, und die geben bei den Live-Defaults alle bedingungslos `True` zurück.
Der Einstieg feuert allein, weil der Preis das Level berührt. Betrifft 16 von 34
Ersteinstiegen und 41 von 88 Kauf-Signalen.

**(b) `_confirm_long()` ist eine ODER-Kette, keine Konfluenz.**
`Kapitulation ODER funding ≤ 0 ODER Spot-CVD in zwei Kerzen gestiegen` — eines von drei
genügt. `funding ≤ 0` ist ein Alltagszustand. Damit ist „+ Bestätigung" im Signaltext
praktisch immer erfüllt und trägt keine Information. Furkan verlangt das Gegenteil
(Transkript 15:50: *„Konfluenz aus Daten, aus Werkzeugen, aus Indikatoren"*).

**(c) DER EIGENTLICHE KONSTRUKTIONSFEHLER: Der Kompass kennt keinen ungesunden Abverkauf.**
Von den vier Mustern setzen drei (Gesunder Trend, Derivate-Pump, Short-Covering) im Code
`price_chg > 0` voraus; das vierte (Kapitulation) beschreibt einen *gesunden* Absturz.
Ein fallender Markt, der die Kapitulations-Prüfung nicht besteht, fällt auf `NEUTRAL` —
ununterscheidbar von einem ruhigen Seitwärtsmarkt. **`NEUTRAL` blockiert nichts.**
Die Engine kann „guter Dip" sagen und „weiß nicht", aber nicht „schlechter Dip" — und
behandelt „weiß nicht" als Erlaubnis.

Verschärfend: Die einzige Einstiegs-Sperre ist `pattern != DERIVATE_PUMP`. Muster 2
verlangt steigenden Preis — **beim Dip-Kauf kann die Sperre also nie greifen.** Die 34
Warnungen im Zeitraum feuern ausnahmslos erst bei bereits offener Position (der
Warn-Zweig liegt im Positions-Management, nicht im Einstiegs-Block).

### Was gebaut werden müsste (NICHT gebaut, Kaisers Entscheidung 2026-07-27)

**Muster 5 „ungesunder Abverkauf"** als Spiegelbild der Kapitulation, aus vorhandenen
Daten (Coinalyze OI + Liquidationen, Binance Spot-CVD):

- Preis fällt **und** Spot-CVD fällt mit → der Dip wird nicht wirklich gekauft
- **OI steigt** statt zu fallen → Longs laden nach, der Treibstoff für den Flush wächst
- **Funding noch positiv** → Long-Überhang nicht abgebaut
- **keine Long-Liquidations-Kaskade** → die Kapitulation steht noch aus

Verwendung als Einstiegs-Sperre (wirkt auf alle Einstiegsarten inkl. Kaufleiter), plus
`confirm_t1` = echte Flow-Prüfung für den 0.5-Level-Einstieg.

**Warnung aus der Messung:** „nur bei gesundem Muster einsteigen" (GESUNDER_TREND oder
CAPITULATION_RESET erforderlich) lässt **2 von 34 Positionen** übrig, Rendite +1,8 %. So
streng darf es nicht werden. Ziel ist, die schlechten zu sperren — nicht nur die zwei
perfekten zuzulassen. Auch „ohne 0.5-Level-Einstiege" kostet viel: +15,7 % statt +32,2 %.
Die 0.5-Einstiege müssen also **gefiltert**, nicht **gestrichen** werden.

**Warum es diesmal anders laufen könnte als bei den bisherigen Filtern:** `strict_confirm`
wurde in E8.5 als „wirkungslos" abgehakt — mit der ausdrücklichen Notiz *„im Backtest
fehlen OI+Futures-CVD → nichts Strengeres zu prüfen"* und *„für E8.3-Retest mit echter
Live-OI aufheben"*. Der Retest fand nie statt. Die echten OI-/Liquidationsdaten kamen erst
mit E9.1. Und `strict_confirm` betrifft ohnehin nur KAUF 2, nicht die 16 ungeprüften
0.5-Einstiege. Die früheren Filter (trend_filter, confluence) waren dagegen
Preis-Struktur-Filter — hier geht es um Order-Flow, also um die Ebene, für die überhaupt
erst seit E9.1 Daten vorliegen.

**Vorgabe von Kaiser für den späteren Bau:** alles in EINEN Backtest-Lauf — Muster-5-Sperre,
`confirm_t1`, Sperre 48 h nach Stop und Mindest-Stop-Abstand 2 % als Gitterzeilen einzeln
und kombiniert gegen die Live-Einstellung.

---

## 6d. ENDSTAND 28.07.2026 — was aus den Empfehlungen geworden ist

Alle drei Hebel aus Abschnitt 4 wurden gebaut und im echten Backtest gemessen. Ergebnis:

| Empfehlung | gemessen | Entscheidung |
|---|---|---|
| **Mindest-Stopabstand 2 %** | gleiche Rendite, Rückgang −12,3 → −7,0 %, ein Viertel weniger Signale | **LIVE** |
| Sperre 48 h nach Stop | wirkt (Rückgang −8,5 %), kippt aber zwischen den Hälften (Platz 22 / 2) | verworfen — `min_stop_pct` erreicht dasselbe stabiler |
| Break-even-Stop schon im Plus | im Bugfix aufgegangen: `trail_stop` rechnete mit falschem Einstand | **erledigt durch den Fix** |

**Der Stand der Live-Einstellung heute: +41,5 % bei −7,5 % Rückgang** (vorher +32,2 % bei
−12,3 %). Der Rückgang ist fast halbiert, die Rendite gestiegen, die Signalzahl gesunken.

### Kaisers Ausgangsfrage, konkret beantwortet

Von seinen drei Beispielen hätte die 2-%-Regel zwei verhindert: 31.05. (1,36 % Abstand)
und 23.06. (**0,38 %**). Der 16.06. (2,76 %) wäre durchgegangen. Nicht jeder Verlust ist
vermeidbar.

**Und die Regel, die gewirkt hat, schaut den Markt gar nicht an.** Das gezielt gebaute
Warnlicht — „ist der Markt gerade gesund?" — hat in neun Monaten dreimal ausgelöst und
2,2 Punkte gekostet. Später bestätigt: Auch mit echten Futures-Daten (E16) ändert sich
daran nichts, es lag also nicht am Material. Eine Zustands-Schwelle lässt sich an ein
Fenster anpassen, eine Mindest-Toleranz nicht — sie stimmt aus Konstruktion.

### Was von Abschnitt 3 zu korrigieren ist

Die dortige Zahl „37 Positionen, 57 % Trefferquote" stammt aus dem Signalstand **vor** dem
Bugfix. Nach dem Fix waren es 34 Positionen; seit der Umstellung auf Mindestabstand und
Liq-Konfluenz sind es deutlich weniger. Die **Aussage** bleibt gültig: Der Bericht zählt
Teilverkäufe als eigene Trades, die dort ausgewiesene Trefferquote ist deshalb höher als
die auf Positions-Ebene.

---

## 7. Antwort in drei Sätzen

Furkan macht wenig Verluste, weil er **selten** handelt, mit **weit entferntem Stop** auf
**großen Strukturen**, nach einem Stop **wartet**, und den Stop **auf Break-even zieht,
sobald die Position im Plus ist**.

Unsere Engine macht das Gegenteil: 2,4-mal so viele Positionen, halb so weite Stops,
Wiedereinstieg nach vier Stunden, Break-even-Schutz erst nach einem Teilgewinn — und der
war durch einen Bug ohnehin fehlerhaft.

Die drei Gegenmittel sind klein, sie kosten im Test 2,5 Punkte Rendite und bringen dafür
**62 % weniger Verlust-Trades und ein Drittel des Rückgangs**.
