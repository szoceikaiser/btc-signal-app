# E41 — Ein Stop, der nicht auf jeden knappen Schluss reagiert

> Angelegt 21.09.2026, ergänzt um Kaisers Regel am selben Tag. Status: **LIVE seit 21.09.2026 — B1 (Rückeroberung, 1 Kerze), Kaisers Entscheidung.** Die Ausschalt-Regel hat am **23.09.2026 angeschlagen** und wurde von Kaiser **bewusst überstimmt** — siehe „Nachmessung 23.09.2026". **Auf der neuen Live-Basis (26.09.2026) schlägt sie nicht mehr an** — siehe „Nachmessung 26.09.2026" am Ende.
> Anlass: der Befund aus E39 (`docs\PLAN-E39-E40.md`).

## Worum es geht, in einem Absatz

Die Engine steigt heute aus, sobald **eine einzige 4-Stunden-Kerze** unter der
Invalidierung schließt, egal wie knapp. E39 hat die zehn Stops der Live-Einstellung aus
acht Monaten angesehen: Im Median schloss die Kerze **0,28 %** unter der Invalidierung,
sieben von zehn weniger als 0,5 %, einer 2 $ darunter. Zwei Tage später stand der Kurs
in **neun von zehn** Fällen wieder über dem Stop-Preis. Das sieht aus wie das, was Furkan
„Liquidität fischen" nennt: ein kurzer Stich unter das Tief, der die Stops abholt und
dann dreht. E41 misst, ob ein Stop, der auf solche knappen Schlüsse nicht reagiert,
**unterm Strich** besser ist — denn im einen Fall, in dem der Bruch echt ist, kostet
jede Verzögerung mehr.

## Kaisers Regel (21.09.2026) — sie ersetzt meine ursprüngliche Variante B

> *„Wenn der Stop-Bereich einen Widerstand darstellt, der Kurs darunter fällt und
> diesen wieder nach oben durchbricht und sich oberhalb hält, dann hält sich der Kurs
> oberhalb des Widerstandes. Dann könnte man den Stop setzen. Denn wenn er wieder
> darunter fällt, dann hat der Widerstand nicht gehalten und es muss mit weiterem
> Kursrückgang gerechnet werden."*

Die Invalidierung ist der Ursprung des Beins, also ein Tief — unter dem Kurs heißt
das **Unterstützung**, über dem Kurs **Widerstand**; die Logik ist dieselbe. Kaisers
Regel ist die mechanische Fassung von Furkans Satz aus dem Video vom 13.09.: *„Sehen
wir dann direkt eine Reaktion?"* Die Reaktion ist die **Rückeroberung**.

Sie ist besser als meine erste Fassung von B, und zwar in einem entscheidenden Punkt:
Dort hätte jeder neue Schluss unter der Marke wieder eine Wartekerze bekommen. Bei
Kaiser gilt die Schonfrist **genau einmal**: Ist die Marke einmal unterschritten und
zurückerobert, ist sie **geprüft** — der nächste Schluss darunter ist ein echter Bruch.

## Klarstellung: E41 hat mit E38 nichts zu tun

Von E38 ist in der Engine **nichts aktiv** — alle drei Schalter stehen auf aus.
Geändert haben sich nur der Muster-Text und die Ampel in den Nachrichten, und beide
entscheiden nichts. E39 hat die **heutige** Engine vermessen, und der Stop-Befund
gehört zu ihr, nicht zu Muster 5. (Muster 5 war bei keinem der zehn Stops aktiv.)

## Was die Chronik dazu sagt (geprüft 21.09.2026)

- **Stop bei Kerzenschluss** war von Beginn an eine bewusste Wahl: „konservative Variante
  aus dem Video" (Review-Antworten, 23.07.2026). Ein Stop schon beim Docht wäre also die
  *strengere* Variante — die kommt als Gegenprobe ins Gitter.
- **`min_stop_pct: 0.02`** (live seit 28.07.) regelt etwas anderes: den Abstand vom
  *Einstieg* zur Invalidierung, nicht wie empfindlich der Stop *an* der Invalidierung
  auslöst. Begründung damals: „unter 2 % Abstand löst schon das normale Rauschen den
  Stop aus." E41 ist dieselbe Frage, eine Ebene tiefer.
- **`conditional_stop`** (E9.3) ist am nächsten verwandt: bei Verlust nachkaufen statt
  stoppen, solange der Order-Flow bestätigt, mit hartem Boden 5 %. **Schlechter als der
  normale Stop.** Wichtiger Unterschied: E41 kauft nichts nach, es wartet nur.
- **Ein Stop-Puffer oder eine Bestätigungskerze wurde nie gemessen.** Weder in der
  Chronik noch im Code noch im Wissens-Layer.

## Die Varianten — festgelegt, bevor es Zahlen gibt

Jede Gitterzeile unterscheidet sich von der Live-Zeile in **genau einem** Punkt.

| Zeile | Regel | Warum diese |
|---|---|---|
| **A · Puffer 0,5 %** | Stop erst, wenn der Schluss mehr als 0,5 % unter der Invalidierung liegt | Einfachste Form. **Vorsicht:** Der Wert ist rund und nicht aus den zehn Stops abgeleitet — aber er liegt nahe an ihnen, und das Risiko, auf genau diese Stops hin zu optimieren, ist real. Deshalb nur *ein* Pufferwert, nicht mehrere zur Auswahl |
| **B1 · Rückeroberung, 1 Kerze** (Kaisers Regel) | Erster Schluss unter der Invalidierung → noch kein Stop. Schließt die **nächste** Kerze wieder darüber → Marke zurückerobert, gilt ab jetzt als **geprüft**. Schließt sie darunter → Stop. Nach einer Rückeroberung: der nächste Schluss darunter → **sofort** Stop, keine zweite Schonfrist | Bildet Furkans „direkt eine Reaktion" ab. Kein frei wählbarer Prozentwert |
| **B3 · Rückeroberung, 3 Kerzen** | Wie B1, aber bis zu drei Kerzen (12 Stunden) Zeit für die Rückeroberung | **Robustheitsprüfung für B1**, keine eigene Wahl. Kaiser: „keine Ahnung, wie viele Kerzen" — ehrlich, und genau deshalb zwei Werte, vorab festgelegt. **B zählt nur, wenn B1 und B3 in dieselbe Richtung zeigen.** Hängt das Ergebnis an der Kerzenzahl, war es Zufall |
| **C · Gegenprobe: Stop schon beim Docht** | Stop, sobald das Kerzen-*Tief* unter der Invalidierung liegt | Die strengere Richtung. Gewinnt sie, war die Idee falsch herum. Verlieren A und B gegen die Live-Zeile *und* C auch, ist der heutige Stop gut gewählt |

**Während der Wartezeit kauft die Engine nichts nach.** Ein Nachkauf unter der
Invalidierung wäre der durchgefallene `conditional_stop` (E9.3) durch die Hintertür.

**Wie gewartet wird, legt die Messung fest — nicht wie viel:** Ich habe die zehn Stops
aus E39 bewusst **nicht** daraufhin angesehen, ob sie in einer oder drei Kerzen
zurückerobert wurden. Wer das vorher nachsieht und danach die Kerzenzahl wählt, misst
hinterher nur seine eigene Auswahl.

**Notbremse für B:** Schließt die erste Kerze schon **mehr als 5 %** unter der
Invalidierung, wird sofort gestoppt, ohne zu warten. Die 5 % sind nicht neu erfunden,
sondern der vorhandene harte Boden `DIP_FLOOR_PCT` aus E9.3 — ein Wert, der nicht an
diesen Daten eingestellt wurde.

**Gilt nur für den ursprünglichen Stop an der Invalidierung.** Ein nach Teilgewinnen
nachgezogener Stop bleibt, wie er ist — dort ist Gewinn gesichert, und genau den soll
kein Puffer aufs Spiel setzen. (In den acht Monaten gab es davon ohnehin keinen.)

## Die Entscheidungsregel — ebenfalls vorab festgelegt

Ein Schalter geht nur live, wenn **alle drei** Bedingungen erfüllt sind:

1. **Besser in beiden Fensterhälften** als die Live-Zeile (die Projektregel).
2. **Maximaler Rückgang nicht mehr als 1 Punkt schlechter** als live. Ein späterer Stop
   heißt bei einem echten Bruch einen tieferen Verlust. Die Renditespalte zeigt das
   nicht, der Rückgang schon.
3. **Die Zahl der Stops sinkt tatsächlich.** Sonst hat der Schalter nicht gegriffen, und
   eine bessere Zahl wäre Zufall (Lehre aus E38: `muster5_halten` griff nie).

Fällt eine davon, bleibt der Schalter aus — auch wenn die Rendite besser aussieht.

## Etappen

### E41.1 — Schalter `stop_puffer_pct` (Default 0,0)
Ein Zahlenwert. 0,0 = heutiges Verhalten. Nur am ursprünglichen Invalidierungs-Stop.

### E41.2 — Schalter `stop_rueckeroberung` (Default 0 = aus; 1 oder 3 Kerzen)
Braucht zwei Merker in der Position: „wartet seit Kerze X" und „Marke ist geprüft".
Beide werden bei jedem Positionswechsel zurückgesetzt — die Lehre aus E18 (Zähler,
die einen Stop überlebten). Der Merker „geprüft" gehört zu **dieser** Invalidierung:
Zieht die Engine die Zonen nach (`zonen_nachziehen`) und entsteht eine neue
Invalidierung, gilt die neue Marke wieder als ungeprüft.

### E41.3 — Gegenprobe `stop_auf_docht` (Default aus)
Stop auf das Kerzentief statt auf den Schluss.

### E41.4 — Tests und Sabotage-Probe
Die gefährlichen Fälle zuerst, jeder mit Vorprobe (das Szenario muss wirklich einen
Stop erzeugen, sonst prüft der Test nichts — der Fehler aus E38):

- Alle drei Schalter aus → **exakt** dieselben Signale wie heute
- **Eine Position darf nie hängen bleiben:** Bei einem langsamen Abverkauf, bei dem jede
  Kerze nur ein wenig tiefer schließt, muss der Stop trotzdem kommen
- Die Notbremse feuert bei einem tiefen Schluss sofort
- Nach einer Rückeroberung stoppt der nächste Schluss darunter **sofort** — keine
  zweite Schonfrist
- Während der Wartezeit entsteht kein Nachkauf
- Eine neue Invalidierung (nach Zonen-Nachziehen) ist wieder ungeprüft
- Nachgezogene Stops bleiben unverändert
- Die Schalter kommen im Backtest und in der Live-Engine an (`EVAL_KEYS`, `EVAL_DEFAULTS`)

### E41.5 — Gitterlauf, Halbierung, Entscheidung
Vier Zeilen (A, B1, B3, C) gegen die Live-Zeile. Im Bericht zusätzlich je Zeile die **Zahl
der Stops** und die **Liste der Stops mit Datum** — damit man sieht, welche Stops
ausgeblieben sind und was stattdessen aus der Position wurde. Entscheidung nach der
Regel oben, festgehalten auch wenn sie Nein lautet.

### Nur falls ein Schalter live geht — nicht Teil dieses Plans *(gebaut 21.09.2026, siehe „Entscheidung“ unten)*
Für B1/B3 bräuchte die Live-Engine eine Nachricht in der Wartekerze („Schluss unter der
Invalidierung — Stop, wenn auch die nächste Kerze darunter schließt"). Ohne sie
wüsstest du nicht, warum der Stop ausbleibt. Wird erst gebaut, wenn B die Messung
besteht.

## Was dieser Plan ausdrücklich NICHT tut

- Keine Empfehlung, einen laufenden Trade nach einem Stop zu halten. E41 misst eine
  Regel für die Engine, über acht Monate und zehn Stops.
- Keine Suche nach dem „besten" Pufferwert. Ein Wert, vorab gewählt.
- Keine Kombination mit anderen Schaltern.

## Kaisers zweite Hälfte der Regel — bewusst NICHT in E41

> *„Das gleiche gilt bei einer Aufwärtsbewegung. Prallt der Kurs an einem Widerstand ab
> und geht wieder runter, dann hält der Widerstand. Durchbricht er ihn und hält sich
> oberhalb (z. B. Kurs fällt wieder bis zum Widerstand, unterschreitet ihn aber nicht
> mehr oder nur mit dem Docht und kehrt nach Norden), dann ist der Widerstand gefallen
> und weitere Kursgewinne sind zu erwarten."*

Das ist der **Ausbruch mit Rücktest**. Er betrifft nicht den Stop, sondern die
Teilverkäufe: Die Engine verkauft heute live kurz **unter** dem letzten Hoch
(`high_exit: on`). Kaisers Regel sagt, was danach passieren sollte — prallt der Kurs
ab, war der Verkauf richtig; bricht er durch und hält beim Rücktest, sind weitere
Gewinne zu erwarten, also zurückkaufen oder den Rest nicht verkaufen.

Das ist eine eigene Frage mit eigenem Schalter. In E41 mitgemessen, hätte jede Zeile
zwei Unterschiede zur Live-Zeile, und man wüsste nicht, welcher gewirkt hat. Vorgemerkt
als **E42** in `wissens-layer\02_status\OFFENE-PUNKTE.md`.

---

## Umsetzung (21.09.2026)

Alle drei Schalter stehen **aus**; die Live-Engine verhält sich unverändert (Test:
exakt dieselben Signale).

| Schalter | Werte | Gitterzeile |
|---|---|---|
| `stop_puffer_pct` | 0,0 = aus | A: 0,005 |
| `stop_rueckeroberung` | 0 = aus | B1: 1, B3: 3 |
| `stop_auf_docht` | aus | C: an |

Die Entscheidung steht in **einer** Funktion auf Modulebene (`stop_entscheidung`), damit
jeder Fall einzeln prüfbar ist: knapper Schluss, Rückeroberung, zweiter Bruch nach der
Rückeroberung, harter Boden, neue Marke nach Zonen-Nachziehen, Short spiegelbildlich.

### Drei Dinge, die erst beim Bauen auffielen

1. **Die Live-Engine hätte das Warten jedes Mal vergessen.** Sie läuft bei jedem
   4-Stunden-Takt als neuer Prozess und liest die Position aus `state.json`. Ohne die
   drei neuen Merker in der Datei finge das Warten bei jedem Lauf neu an — der Stop käme
   **nie**. Der Backtest hätte das nicht gezeigt, weil er am Stück rechnet. Die Merker
   werden jetzt gespeichert; ein Test prüft das Hin und Zurück.
   *Nebenbefund, nicht behoben:* `widerstand_exits` (E20) wird ebenfalls nicht
   gespeichert. Folgenlos, weil `widerstand_exit` aus ist — aber derselbe Fehlertyp.
2. **Der Nachkauf in der Rückeroberungskerze hätte zu einem Preis gebucht, den es nie
   gab.** Die 0,786-Regel bucht zum Levelpreis — richtig, solange der Kurs von oben
   kommt. Nach einer Rückeroberung kommt er von unten; eine Limit-Order wäre zum
   Eröffnungskurs gefüllt worden. Behoben: Gebucht wird der günstigere der beiden, aber
   **nur**, wenn E41 eine Marke als geprüft führt. Ein Test sichert, dass die Live-Zahlen
   davon unberührt bleiben.
3. **Die Nachkaufsperre gilt auch für die Kerze der Rückeroberung**, nicht nur fürs
   Warten. Die Bestätigung steht erst mit deren Schluss fest.

### Geprüft

**406 Tests grün. `sabotage_e41.py`: 28 Sabotagen, alle gefangen** — eine erst im
zweiten Durchgang („Preiskorrektur gilt auch ohne E41"; es fehlte der Test, dass die
Live-Buchung unverändert bleibt).

### Was der Bericht zeigt

Abschnitt „E41: Stop mit Puffer, Rückeroberung oder Docht": je Variante Rendite,
Rückgang, beide Hälften, Zahl der Stops und das **Urteil nach der vorab festgelegten
Regel** — maschinell, nicht von Hand. Darunter für jeden Live-Stop: gleich gestoppt,
oder wie die Position stattdessen endete und zu welchem Preis.

## Ergebnis (Backtest-Lauf 21.09.2026, 13:56 UTC, Fenster 13.01.–21.09.)

| Variante | Rendite | Rückgang | H1 | H2 | Stops | Regel |
|---|---:|---:|---:|---:|---:|---|
| **Live** | +23,5 % | −9,4 % | +18,7 % | +4,0 % | 10 | — |
| A · Puffer 0,5 % | +27,8 % | −10,3 % | +21,3 % | +5,4 % | 8 | besteht |
| **B1 · Rückeroberung 1 Kerze** | +26,4 % | −10,3 % | +21,3 % | **+4,2 %** | 9 | besteht |
| B3 · Rückeroberung 3 Kerzen | +27,8 % | −10,3 % | +22,5 % | **+4,4 %** | 9 | besteht |
| C · Docht (Gegenprobe) | +23,9 % | −9,1 % | +20,7 % | +3,0 % | 12 | fällt durch |

**Formal bestehen alle drei lockeren Varianten, die strengere Gegenprobe fällt durch.**
Die Richtung ist stimmig: lockerer ist besser, strenger schlechter. Kaisers Regel
besteht mit 1 **und** mit 3 Kerzen.

### Was die Tabelle NICHT so deutlich sagt, wie sie aussieht

1. **In Hälfte 2 liegt B im Rauschen.** B1 ist dort um **0,2** Punkte besser, B3 um 0,4.
   Das Projekt hat am 06.09. gemessen, dass **ein einziger Tag mehr Daten** einen
   Unterschied von 1,0 Punkten umdreht. Die Regel „besser in beiden Hälften" hatte
   keine Rauschgrenze — **das ist ein Mangel meiner Regel**, obwohl die Lehre dazu im
   Wissens-Layer stand. Belastbar besser ist B nur in Hälfte 1 (+2,6 bzw. +3,8).
2. **Der Rückgang liegt knapp an der Grenze:** 0,9 Punkte schlechter bei einer Toleranz
   von 1,0.
3. **Meine Liste „Was wurde aus der Position" übertreibt den einen großen Fall.** Sie
   vergleicht mit dem Live-Stop-Preis — übersieht aber, dass die Live-Engine danach
   **wieder einsteigt**. Beim Stop vom 08.03. (65.971 $) kaufte sie acht Stunden später
   per Flush-Einstieg bei 67.555 $ wieder ein. Der Schaden des Live-Stops war also
   nicht die „+8,9 %" aus der Liste, sondern der **Wiedereinstieg 2,4 % höher** plus
   Gebühren. Die übrigen verzögerten Stops endeten 0,1–1,4 % schlechter oder bis zu
   0,9 % besser als live. Der Renditeunterschied insgesamt ist das Netto aus vielen
   verschobenen Positionen und lässt sich nicht sauber einem Fall zuschreiben.
   Behebung im nächsten Bau: die Liste nennt den Wiedereinstieg der Live-Engine mit.

### Welche Variante überhaupt in Frage käme

**B1.** Laut Plan ist B3 die *Robustheitsprüfung* für B1, „keine eigene Wahl" — B3
deshalb zu nehmen, weil seine Zahlen besser sind, wäre genau die nachträgliche Auswahl,
vor der der Plan warnt. A scheidet aus demselben Grund aus: Der Wert 0,5 % lag nahe an
den zehn Stops, die ich vorher gesehen hatte; das Plan-Risiko „auf genau diese Stops hin
optimiert" war benannt.

### Entscheidung: B1 live (Kaiser, 21.09.2026)

Kaiser hat nach dem Bericht entschieden: **„B1 live schalten"**. Seit 21.09.2026 steht
in `config.json` `"stop_rueckeroberung": 1`. Wirksam ab dem ersten Engine-Lauf nach dem
Hochladen.

**Was sich damit für dich ändert:**

- Schließt eine 4-Stunden-Kerze knapp unter der Invalidierung, kommt **kein Stop**,
  sondern die Nachricht **„⏳ STOP WARTET"**. Sie sagt, wie weit der Schluss unter der
  Marke liegt, und was als Nächstes passiert: Schließt die nächste Kerze wieder darüber,
  hat die Marke gehalten — sonst kommt der Stop.
- Wird die Marke zurückerobert: Nachricht **„✅ MARKE ZURÜCKEROBERT"**. Ab dann gilt sie
  als geprüft; der nächste Schluss darunter stoppt **sofort**.
- Liegt schon der erste Schluss mehr als 5 % unter der Marke: Stop ohne Warten.
- Während des Wartens und in der Kerze der Rückeroberung sendet die Engine **keinen
  Nachkauf**.
- Die **Plan-Nachricht** nennt die Regel in der Stop-Zeile, statt weiter „Stop bei
  Kerzenschluss darunter" zu versprechen. Wartet die Engine gerade, steht dort eine
  Achtung-Zeile.
- Eine **Stop-Order bei der Börse** wartet nicht: Sie löst schon aus, wenn der Kurs die
  Marke berührt — also beim Docht, noch strenger als der alte Engine-Stop (Variante C).
  Die Rückeroberungs-Regel gibt es nur in den Engine-Nachrichten.

**Warum 1 Kerze und nicht 3:** B3 war laut Plan die Robustheitsprüfung für B1, keine
eigene Wahl. Die bessere Zahl von B3 als Grund zu nehmen, wäre die nachträgliche
Auswahl, vor der der Plan warnt.

### Die Ausschalt-Regel — festgelegt VOR der ersten Messung nach dem Umschalten

Die Einschalt-Regel hatte keine Rauschgrenze; diese hat eine. Der Schalter geht wieder
**aus** (`"stop_rueckeroberung": 0`), wenn der Backtest **eines** von beiden zeigt:

1. **Der alte Stop ist in beiden Fensterhälften um mindestens 1 Punkt besser** als
   live. Nur „besser" genügt nicht — beim Einschalten lag B1 in Hälfte 2 nur 0,2 Punkte
   vorn, ein gleich kleiner Rückstand wäre genauso Rauschen.
2. **Der Rückgang live ist um mehr als 1 Punkt tiefer** als beim alten Stop. Das war
   beim Einschalten eine der drei Bedingungen, und sie muss auch danach halten.

„Stoppt live nicht seltener als der alte Stop" ist **kein** Ausschaltgrund, wird aber
gemeldet: Dann hat die Regel im Fenster nichts bewirkt.

**Ehrlich zum Abstand:** Beim Einschalten lag der Rückgang 0,9 Punkte tiefer — 0,1
unter der Grenze. Es ist also gut möglich, dass die zweite Bedingung bald anschlägt.
Dann gilt die Regel, auch wenn die Rendite besser aussieht.

### Was der Backtest-Bericht seitdem zeigt

Abschnitt „E41: Stop mit Rückeroberung — live seit 21.09.2026": Live gegen den alten
Stop (und B3 zur Information), das Urteil nach der Ausschalt-Regel **maschinell**
(„Bleibt an." oder „AUSSCHALTEN."), darunter jeder Stop des alten Stops: gleich
gestoppt, oder wie die Position live stattdessen endete — **und ob der alte Stop danach
wieder einkaufte, zu welchem Preis**. Damit ist Punkt 3 aus „Was die Tabelle NICHT so
deutlich sagt" behoben: Der Fall 08.03. zeigt jetzt den Wiedereinstieg 2,4 % höher.

**Im Gitter:** Die Panel-Zeile heißt jetzt „LIVE-heute +Rückeroberung vor dem Stop
(1 Kerze)". Alle Zeilen „LIVE-heute + X" (Trendfilter, 1D-Ebene, Ampel, Muster 5) und
„MEINE Einstellung ohne Flush" tragen die Rückeroberung mit — sonst mäßen sie zwei
Unterschiede. Neu: „LIVE bis 21.09.2026 (Stop ohne Rückeroberung)" als Ausschalt-Probe
und „Rückeroberung 3 statt 1 Kerze" als weiterlaufende Robustheitsprüfung. **A (Puffer)
und C (Docht) sind aus dem Gitter genommen:** gemessen, Ergebnis oben, keine
Entscheidung hängt mehr an ihnen.

### Geprüft (Live-Schaltung)

- Die Live-Engine liefert **dieselben Signale und Meldungen**, ob sie alle Kerzen in
  einem Lauf nachholt oder jede Kerze in einem eigenen Lauf sieht (so wie sie auf GitHub
  läuft). Ohne gespeicherten Wartezähler käme der Stop nie — ein Test hält das fest.
- Holt ein Lauf mehrere Kerzen nach, kommt „STOP WARTET" **vor** dem Stop, dem es
  vorausging.
- Ein nach Teilgewinnen nachgezogener Stop bekommt im Plan **keine** Schonfrist
  versprochen.
- **443 Tests grün.** Sabotage-Proben: `sabotage_e41.py` neu gefasst, **56 Sabotagen,
  alle gefangen**; `sabotage_e40.py` 27, alle gefangen; E38, E38.1 und E39 weiterhin
  ohne Lücke.

---

## Nachmessung 23.09.2026 — die Ausschalt-Regel schlägt an

Backtest-Lauf 23.09.2026, 18:40 UTC, Fenster **15.01.–23.09.2026** (zwei Tage mehr als
am 21.09., ein Stop mehr am 15.09., Fensteranfang zwei Tage später).

| Variante | Rendite | Rückgang | H1 | H2 | Stops | Platz H1 | Platz H2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Live: Rückeroberung, 1 Kerze** | +25,2 % | **−10,9 %** | +20,0 % | +4,3 % | 9 | 20. | 29. |
| Alter Stop (bis 21.09.) | +22,6 % | −9,4 % | +17,8 % | +4,1 % | 10 | 38. | 33. |
| B3 · 3 statt 1 Kerze | +26,8 % | −10,4 % | +21,4 % | +4,5 % | 9 | 15. | 27. |

- Bedingung 1 (alter Stop in **beiden** Hälften mindestens 1 Punkt besser): **nein** —
  live ist in beiden Hälften besser.
- Bedingung 2 (Rückgang live mehr als 1 Punkt tiefer als beim alten Stop): **ja** —
  **1,5** Punkte. Am 21.09. waren es 0,9 bei einer Grenze von 1,0.

Der Bericht meldet deshalb **AUSSCHALTEN**.

### Kaisers Entscheidung (23.09.2026): anlassen, beim nächsten Backtest neu prüfen

Kaiser hat die Meldung bewusst überstimmt. Der Schalter bleibt auf 1.
**Festgehalten, damit es nachvollziehbar bleibt:**

**Was dafür spricht**

- Die Rendite liegt 2,6 Punkte höher (+25,2 gegen +22,6 %), und live ist in **beiden**
  Fensterhälften besser — die erste, wichtigere Bedingung ist klar erfüllt.
- **Der Rückgangsvergleich zwischen zwei Varianten ist pfadabhängig.** Mehr Warten kann
  *in der Wartephase* nur tiefer werden, nie flacher. Trotzdem zeigt B3 — das **länger**
  wartet — einen **flacheren** Rückgang (−10,4 gegen −10,9 %). Der Unterschied entsteht
  also nicht im Warten, sondern danach: Eine anders beendete Position verschiebt alle
  folgenden Einstiege. Damit misst die Spalte *Rückgang* zwischen zwei Varianten nicht
  nur Risiko, sondern auch Zufall.
- 0,5 Punkte trennen B1 und B3 im Rückgang, und B3 liegt mit −10,4 % **genau** auf der
  Grenze. Eine Bedingung, die an 0,1 Punkten kippt, ist keine belastbare Aussage.

**Was dagegen spricht — und was das Überstimmen kostet**

- Bedingung 2 war die **Risiko**-Bedingung, nicht die Rendite-Bedingung. Sie zu
  übergehen heißt: der tiefere Buchverlust wird in Kauf genommen. In diesem Fenster sind
  das −10,9 statt −9,4 %.
- **Eine vorab festgelegte Regel zu überstimmen, ist genau der Vorgang, gegen den dieses
  Projekt seine Regeln schreibt.** Wer sie einmal beugt, hat beim nächsten Mal kein
  Argument mehr gegen das Beugen. Deshalb steht es hier, statt still zu passieren, und
  deshalb **meldet der Bericht weiter AUSSCHALTEN** — der Hinweis auf die Überstimmung
  steht daneben, er ersetzt sie nicht (ein Test hält das fest).
- Die Mehrrendite hängt an **einem** Fall: Am 08.03.2026 hielt live bis zum 13.03. und
  verkaufte den Rest bei 71.831 $, statt bei 65.971 $ zu stoppen (+8,9 %). Sieben der
  zehn Fälle endeten mit der Regel leicht **schlechter** (−0,1 bis −1,4 %), zwei besser.
  Ein Fall ist kein Beleg.

**Nächste Prüfung:** beim nächsten Backtest-Lauf. Schlägt Bedingung 2 wieder an, ist die
Frage nicht mehr „ausschalten oder nicht", sondern: **Ist der Rückgangsvergleich
zwischen Varianten überhaupt das richtige Maß?** Dazu der Vorschlag E41.6 unten.

### Kaisers Frage: Warum haben wir nicht B3 mit drei Kerzen genommen?

Fünf Antworten, von der formalen zur inhaltlichen:

1. **Weil es vorher so festgelegt war.** Im Plan oben steht zu B3: *„Robustheitsprüfung
   für B1, keine eigene Wahl."* Kaiser selbst hatte gesagt, er habe „keine Ahnung, wie
   viele Kerzen" — genau deshalb wurden **zwei** Werte vorab gemessen, statt einen zu
   suchen. Wer danach den besseren nimmt, hat nicht gemessen, sondern ausgewählt: Der
   bessere von zwei Würfen sieht immer besser aus, als er ist.
2. **Der Unterschied hält die eigene Rauschgrenze nicht.** B3 gegen B1: Hälfte 1
   **+1,4**, Hälfte 2 **+0,2** Punkte. Die Projektgrenze für Rauschen liegt bei 1,0
   Punkt (06.09.2026: ein Tag mehr Daten drehte 1,0 Punkte um). Nur Hälfte 1 liegt
   darüber. Am 21.09. war es dasselbe Bild (+1,2 / +0,2). Zwei Läufe, zweimal dieselbe
   Aussage: **In der zweiten Hälfte ist zwischen 1 und 3 Kerzen kein Unterschied
   messbar.**
3. **B3 rettet keine einzige Position mehr als B1.** Beide haben **9 Stops**, der alte
   Stop hat 10. Es ist derselbe eine Stop, der in beiden Varianten ausbleibt (08.03.).
   Der Renditeunterschied entsteht also nicht daraus, dass drei Kerzen eine Position
   zusätzlich durch die Delle tragen, sondern aus **ein paar späteren Stop-Preisen** —
   und die sind, wie die Liste im Bericht zeigt, mal 0,4 % besser, mal 1,4 % schlechter.
4. **Mehr Wartezeit ist mechanisch riskanter, nicht weniger.** Wer drei Kerzen wartet,
   sitzt bis zu acht Stunden länger in einer Position, deren Marke gebrochen ist. Dass
   B3 hier trotzdem besser aussieht, ist ein Fensterbefund, kein Mechanismus. Die
   Richtung „lockerer ist besser" ist in beiden Läufen stabil; **die Feinstufe innerhalb
   dieser Richtung ist es nicht.**
5. **Der harte Boden bekäme bei 3 Kerzen erst Gewicht.** Die Notbremse (erster Schluss
   mehr als 5 % unter der Marke → sofort Stop) wirkt bei 1 Kerze nur in dieser ersten
   Kerze; danach stoppt die nächste Kerze unter der Marke ohnehin. Bei 3 Kerzen ist sie
   über zwei zusätzliche Kerzen hinweg die **einzige** Grenze nach unten — und sie wurde
   nie eigens gemessen, sie ist der übernommene Wert `DIP_FLOOR_PCT` aus E9.3. Ein
   Wechsel auf 3 Kerzen ändert also nicht nur eine Zahl, er lehnt sich an eine
   ungemessene zweite an.

**Damit ein Wechsel auf 3 Kerzen keine nachträgliche Auswahl wäre, braucht er eine
vorab festgelegte Regel. Hiermit festgelegt (23.09.2026):**

> B3 wird nur live, wenn in **zwei aufeinanderfolgenden** Backtest-Läufen, die
> mindestens **vier Wochen** auseinanderliegen, gilt: B3 ist in **beiden**
> Fensterhälften um mindestens **1 Punkt** besser als B1 **und** B3s Rückgang ist
> **nicht tiefer** als B1s. Sonst bleibt es bei einer Kerze — auch wenn B3s Rendite
> höher aussieht. Beim Lauf vom 23.09.2026 ist die Regel **nicht** erfüllt (Hälfte 2
> nur +0,2).

### E41.6 — Vorschlag: ein Risikomaß ohne Pfadabhängigkeit (nicht gebaut)

Die Ausschalt-Regel hängt heute am **Fenster-Rückgang**, und der vergleicht zwei
Kapitalkurven, deren Positionen zu verschiedenen Zeitpunkten laufen. Sauberer wäre ein
Maß **je Position**, wie E39 es schon kennt: Für jeden Stop des alten Stops den
**tiefsten Punkt**, den die Position live danach noch gesehen hat, bevor sie endete.
Das ist reines Kursrechnen, unabhängig davon, was die Engine danach macht.

Dann hieße die Bedingung nicht mehr „Rückgang 1 Punkt tiefer", sondern: *„Im Median
kostet das Warten mehr als X % zusätzlichen Buchverlust je betroffener Position."* Der
Wert X wäre **vor** der Messung festzulegen. Erst dann ist entscheidbar, ob das Warten
teuer ist — oder ob nur die Kapitalkurve anders verläuft.

### Geprüft (Nachtrag 23.09.2026)

**444 Tests grün.** Der Bericht nennt die Überstimmung nur, wenn die Regel anschlägt,
und die Ausschalt-Meldung bleibt daneben stehen — zwei Sabotagen sichern beides ab
(`sabotage_e41.py`, jetzt 58 Sabotagen, alle gefangen).

## Nachmessung 26.09.2026 — auf der neuen Live-Basis schlägt die Regel nicht mehr an

Erster Backtest nach dem Wechsel auf `bein_richtung: "bias"` (E43.2, live seit
26.09.2026), GitHub-Lauf 36233723729 auf dem Arbeitszweig, Fenster 18.01.–26.09.2026.
Beide Vergleichszeilen tragen `bein_richtung: "bias"`, unterscheiden sich also weiter in
genau einem Punkt.

| Variante | Rendite | Rückgang | H1 | H2 | Stops |
|---|---:|---:|---:|---:|---:|
| **Live: Rückeroberung, 1 Kerze** | +35,3 % | −9,9 % | +23,6 % | +9,5 % | 9 |
| Alter Stop (bis 21.09.) | +30,8 % | −9,9 % | +19,6 % | +9,3 % | 10 |
| B3 · 3 statt 1 Kerze | +34,2 % | −9,9 % | +21,9 % | +9,7 % | 9 |

**Urteil nach der unveränderten Ausschalt-Regel:** alter Stop in beiden Hälften ≥ 1 Punkt
besser: nein (H1 −4,0, H2 −0,2). Rückgang live mehr als 1 Punkt tiefer: nein (gleich,
−9,9 % gegen −9,9 %). **Der Bericht meldet „Bleibt an.“** Der offene Streitpunkt vom
23.09.2026 hat sich damit auf der heutigen Basis erledigt, **ohne** dass die Regel
geändert wurde.

Zur Einordnung: Der Rückgang, an dem die Regel am 23.09. anschlug (1,5 Punkte), ist hier
in beiden Zeilen gleich. Die Regel reagiert auf den Pfad, das war das Argument für die
Überstimmung. Es bleibt richtig, dass ein Rückgangsvergleich zwischen zwei Varianten
pfadabhängig ist; E41.6 (ein pfadunabhängiges Risikomaß) bleibt deshalb sinnvoll, ist
aber nicht mehr dringend. Die Regel läuft bei jedem Backtest weiter mit.

