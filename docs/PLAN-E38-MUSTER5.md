# E38 — Muster 5: Bremse oder Treibstoff?

> Angelegt 20.09.2026. Auslöser: das Transkript des Videos vom 13.09.2026
> (`Videos\260913\260913.txt`), ausgewertet in
> `wissens-layer\02_status\GEMESSEN-UND-ENTSCHIEDEN.md`.

## Worum es geht

Furkan beschreibt am 13.09.2026 (15:44) eine Lage: *„Gerade werden sehr viele Short
Position[en] auch aufgemacht. Es wurden zwar Long Position[en] jetzt liquidiert in der
Bewegung, aber wie wir hier am CVD sehen, aggressive Short Position[en]."*

Das ist genau die Konstellation, die `classify_pattern` als **Muster 5
(UNGESUNDER_ABVERKAUF)** führt: Preis fällt, Spot-CVD fällt mit, OI hält oder steigt,
Funding positiv, keine Long-Liquidations-Kaskade.

Die Engine nennt das eine Warnung. Furkan liest dieselbe Lage **zusätzlich** als
Hinweis auf Liquidität oberhalb — die neuen Shorts sind das Material, das den Kurs
später nach oben zieht (er nennt 80 000 als Ziel). Beide Lesarten widersprechen sich
nicht; er kauft an dem Tag selbst nicht. Aber der Engine fehlt die zweite Hälfte.

## Zwei Befunde, die den Anlass tragen

**1. Die Bremse zieht gar nicht.** Nachgesehen am 20.09.2026: Der einzige Schalter, der
an Muster 5 hängt, ist `block_unhealthy` — und der ist seit E13 aus, weil er Rendite
gekostet hat. Muster 5 erscheint nur noch in `MUSTER_KLARTEXT` (Lagezeile) und in
`_AMPEL_DAGEGEN`, und die Ampel ist seit E34 ebenfalls reine Anzeige. **Was in der
Telegram-Nachricht nach Warnung klingt, ändert keine einzige Entscheidung.**

**2. Für den Umbau gibt es eine Vorlage im eigenen Projekt.** Bei Muster 4 wurde genau
dieser Schritt schon gemacht. Codekommentar in `strategy_core.py`: *„Kapitulation ist
in Furkans Methode kein Warnzeichen, sondern die Einstiegslage - deshalb steht live
`flush_entry='core'`."* Vor E9.1 — ohne echte Liquidationsdaten — war `off` besser; mit
ihnen drehte das Ergebnis. **Muster 5 steht heute da, wo Muster 4 vor E9.1 stand:
benannt, angezeigt, ohne Wirkung.**

## Warum das nicht unter die Filter-Diagnose fällt

Zwölf gemessene Filter, zwölf schlechter. Die Kern-Diagnose sagt: Die Engine ist im
Mittel nur mit 29 % des Kapitals investiert — ihr Problem ist zu wenig Teilhabe, nicht
zu wenig Vorsicht. Wer einen dreizehnten Filter vorschlägt, muss erklären, warum er
nicht unter dieselbe Diagnose fällt.

**E38 schlägt keinen Filter vor.** Beide geprüften Varianten halten die Engine *länger
oder größer* investiert, nicht kürzer. Das ist die Richtung, in die bisher als einzige
etwas funktioniert hat (Kaufleiter, Flush-Einstieg). Das ist kein Beleg dafür, dass es
wirkt — nur der Grund, warum es überhaupt gemessen zu werden verdient.

---

## Etappen

### E38.1 — Was passiert NACH einem Muster? · **FERTIG, GEMESSEN 20.09.2026**

Reine Messung, kein Schalter, keine Handelsregel. Neu in `engine\backtest.py`:
`muster_nachlauf()` und `muster_abschnitt()`. Der Abschnitt erscheint in `BACKTEST.md`
vor „Einschränkungen", über `abschnitt_oder_grund()` — er kann also nicht lautlos
fehlen (Lehre aus E37.3).

Gemessen wird für jedes Kompass-Muster die Kursänderung nach 6, 12 und 24 Kerzen
(1, 2 und 4 Tage).

**Drei Fallen, die der Code abfängt — jede davon würde die Zahlen still verfälschen:**

1. **Ohne Grundrate ist jede Musterzeile wertlos.** Steigt der Kurs im Fenster ohnehin
   um 3 % je zwei Tage, dann ist „nach Muster 5 +3 %" eine Aussage über das Fenster,
   nicht über Muster 5. In jeder Zelle steht deshalb der **Abstand zur Grundrate** über
   alle bewerteten Kerzen. *(Im Probelauf mit erfundenen Daten stand Muster 5 bei +11,6 %
   — und lag damit 1,6 Punkte **unter** der Grundrate. Ohne die Spalte hätte man
   „Treibstoff" gelesen.)*
2. **Aufeinanderfolgende Kerzen sind kein unabhängiger Beleg.** Muster 5 hält mehrere
   Kerzen an; 80 Kerzen können 9 Ereignisse sein. Gezählt werden deshalb **Episoden**
   (zusammenhängende Läufe), und die Mindestzahl (`MUSTER_MIN_EPISODEN = 20`) gilt für
   die Episoden. Darunter schreibt der Bericht selbst, dass die Zahl Rauschen ist —
   dieselbe Lehre wie bei `neustart_mit_rest`, das in acht Monaten nur dreimal griff.
3. **Ein einzelner Flush-Tag kippt einen Mittelwert.** Kernzahl ist der Median; der
   Mittelwert steht daneben, damit ein Auseinanderlaufen sichtbar wird.

Außerdem: Die letzten 24 Kerzen werden nicht gewertet (ihr Nachlauf wäre unvollständig),
und alle drei Horizonte teilen dieselbe Stichprobe — sonst wären die Spalten nicht
vergleichbar.

**Geprüft:** 24 neue Tests, **308 passed / 0 failed**. Sabotage-Probe
(`engine\sabotage_e381.py`, 17 Sabotagen) — **alle gefangen**.

> **Die Sabotage-Probe hat zwei echte Lücken gefunden**, beide erst beim zweiten
> Durchgang geschlossen:
> - *„Nachlauf zeigt nach hinten statt nach vorn"* lief zunächst **ungefangen** durch.
>   Das ist die gefährlichste denkbare Verwechslung in E38: Bei gedrehtem Vorzeichen
>   liest sich jede Bremse als Treibstoff — und die Zahlen sähen dabei völlig normal
>   aus. Kein Test fing es, weil alle Testreihen flach oder symmetrisch waren.
> - *„Median nimmt bei gerader Anzahl den falschen Wert"* ebenso: `s[n//2]` statt zu
>   mitteln verschiebt jede Musterzeile systematisch nach oben.
>
> Zusätzlich war **ein Test selbst falsch gedacht** (`test_..._median_widersteht_...`):
> Ein Einbruch in der Mitte erzeugt ZWEI Ausreißer, nicht einen — die Kerze davor sieht
> −60 %, die Kerze selbst +150 %. Die Behauptung „der Mittelwert wird heruntergezogen"
> war nicht durchgerechnet. Korrigiert und im Docstring festgehalten.

**Was diese Etappe NICHT beantwortet:** ob ein Schalter Rendite bringt. „Steigt danach"
ist nicht „verdient" — das steht auch so im Bericht. Das beantwortet erst E38.5.

**Abbruchbedingung:** Kommt Muster 5 auf weniger als 20 Episoden, endet E38 hier. Ein
Schalter auf dieser Grundlage wäre nicht messbar, egal wie gut die Zahl aussieht.

#### Ergebnis (Lauf vom 20.09.2026, Fenster 12.01.–20.09., 2441 Kerzen)

**Die Abbruchbedingung ist nicht eingetreten: 26 Episoden, 45 Kerzen.**

Muster 5 ist die stärkste Zeile im Feld — auf 1 Tag +1,03 Punkte über der Grundrate bei
76 % höher geschlossenen Fällen (Grundrate 50 %), auf 2 Tage +1,02 bei 71 %. Nach 4
Tagen dreht es unter die Grundrate (42 %). Zufallswahrscheinlichkeit bei 26 unabhängigen
Episoden rund 0,5 %; der Befund war vorab benannt, leidet also nicht unter dem
Mehrfachvergleich über die 18 Tabellenzellen.

**Die wichtigere Zeile ist `CAPITULATION_RESET`** — schlechtester Nachlauf im ganzen
Feld (−1,61 gegen Grundrate, 33 % höher), und genau darauf kauft die Engine live. Wer
nach der Tabelle handelte, müsste `flush_entry` abschalten, was nachweislich falsch
wäre. Die Engine kauft nicht zum Musterzeitpunkt, sondern an der Fib-Zone mit Stop —
Nachlauf ab Erkennung und Ertrag ab Einstiegspreis sind zwei verschiedene Größen.

**Damit ist die Tabelle ein Hinweis, wo zu suchen ist, und kein Beleg.** Vollständige
Einordnung: `wissens-layer\02_status\GEMESSEN-UND-ENTSCHIEDEN.md`, Abschnitt „E38.1
gemessen".

**Nachzuholen im nächsten Lauf:** die Auswertung **je Episode** statt je Kerze. Die
Trefferquote von 76 % ist über 45 Kerzen gerechnet, die zu 26 Episoden gehören (mittlere
Länge 1,73); benachbarte Kerzen teilen fast den ganzen Nachlauf.

### E38.2 — `muster5_entry` (Default aus) · **GEBAUT UND GEPRÜFT 20.09.2026**

**Umgesetzt anders als ursprünglich geplant — und zwar wegen eines Befunds beim Lesen
des Codes.** Geplant war ein eigener Einstiegszweig analog `flush_entry`. Beim Nachsehen
zeigte sich: **Der Flush-Einstieg ist gar kein eigenständiger Trigger.** Er hängt an der
Fib-Zone (`z.gp_lower`, `z.invalidation`) und feuert nur, wenn der Kurs das Golden
Pocket nach unten durchschlägt, aber darüber schließt. Muster 4 wirkt dort nur als
*Bestätigung* über `_confirm_long()` (`strong = pattern == CAPITULATION_RESET`).

Das ist dieselbe Struktur, die E38.1 erklärt: Die Engine kauft nicht zum Musterzeitpunkt,
sondern an einer Preiszone. Ein Muster-5-Trigger ohne Zonenbindung hätte die Engine
**im Nichts kaufen lassen**.

Deshalb ist `muster5_entry` ein `bool` geworden und setzt an genau einer Stelle an:

```python
strong = pattern == Pattern.CAPITULATION_RESET or (
    muster5_entry and pattern == Pattern.UNGESUNDER_ABVERKAUF)
```

Ein Test hält fest, dass jeder so entstandene Einstieg einen Stop-Bezug hat — der
Nachweis, dass nichts ohne Zone gekauft wird.

*Vorbehalt, der in die Auswertung gehört:* Muster 5 heißt „die Zwangsverkäufe stehen
noch bevor". In diesen Zustand zu kaufen heißt, **vor** der Kaskade zu kaufen — und
Furkan tut das an dem Tag ausdrücklich nicht. Diese Variante ist die aggressivere
Auslegung seiner Aussage, nicht die wörtliche.

### E38.3 — `muster5_halten` (Default aus) · **GEBAUT UND GEPRÜFT 20.09.2026**

Näher an dem, was er tatsächlich tut: Bei Muster 5 werden Teilverkäufe ausgesetzt, die
Position also länger gehalten statt früher gekauft. Er kauft nicht — er verkauft nur
nicht, weil er das Ziel oben sieht.

*Nach E38.1 der aussichtsreichere der beiden Zweige:* Die Wirkung von Muster 5 ist nach
zwei Tagen verschwunden. Ein so kurzes Signal passt nicht zu einer Kaufleiter über Tage,
wohl aber zu der Frage, ob heute verkauft werden muss. Gemessen wird trotzdem beides —
eine Vermutung bleibt eine Vermutung.

**Umsetzung:** `"off" | "leiter" | "alle"`. `"leiter"` hält nur die Zwischenverkäufe
zurück (Leiter, letztes Hoch, Liquidations- und Widerstandszone), `"alle"` auch die
geplanten Ziele an 1.0 und 1.618.

Der Schalter sitzt im vorhandenen Wächter `_darf_teilverkaufen()`, also **vor** dem
Erzeugen des Signals. Das war eine bewusste Entscheidung gegen die naheliegende
Alternative: Wer ein fertiges Teilverkauf-Signal hinterher wieder entfernt, muss
`tp_rungs`, `high_exits`, `liq_exits`, `widerstand_exits` **und** `pos.state`
zurückdrehen. Jeder vergessene Zähler wäre ein stiller Fehler — eine Leiterstufe gälte
als verbraucht, ohne dass verkauft wurde. Ein Test prüft genau das.

Die Entscheidungslogik steht als `muster5_haelt_zurueck()` **auf Modulebene**, nicht in
`evaluate()` — die Lehre aus E34: Eine Regel, deren Fälle sich im laufenden System nur
mühsam herbeiführen lassen, wird sonst nie vollständig geprüft.

**Zwei Grenzen sind fest eingebaut:**

- **Nur bei Long.** Bei einem Short ist Liquidität oberhalb ein Grund, *eher* zu decken.
- **Nie der Stop.** `STOPLOSS` und `VERKAUF_REST` stehen nicht in `_TEILVERKAUF_TYPES`
  und laufen am Wächter vorbei. Das ist der gefährlichste denkbare Fehler dieses
  Ausbaus — die Position bliebe im fallenden Markt liegen, weil ein Muster gerade
  „halten" sagt. Eine Sabotage nimmt `STOPLOSS` in die Menge auf; zwei Tests werden rot.

#### Ein Risiko, das die Renditespalte nicht zeigt

**`"alle"` verhindert das Nachziehen des Stops.** Ohne realisierten Teilgewinn greift
`trail_stop` nicht — die Position läuft mit dem ursprünglichen, weiter entfernten Stop
weiter. Im Testszenario ist der Unterschied eindeutig: `"off"` liefert Teilgewinn *und*
Stop, `"alle"` liefert nur den Einstieg.

Das ist kein Fehler, sondern eine Folge. Aber sie steht als eigener Test im Code
(`..._BEKANNTE_FOLGE`), damit eine gute Rendite dieser Variante beim Auswerten nicht
als reiner Gewinn missverstanden wird: **`"alle"` trägt mehr Risiko, und zwar an einer
Stelle, die die Renditespalte allein nicht sichtbar macht.**

### E38.4 — Sabotage-Probe für beide Schalter · **FERTIG 20.09.2026**

`engine\sabotage_e38.py`, **24 Sabotagen, alle gefangen.** Dazu `sabotage_e381.py`
(17 Sabotagen, ebenfalls alle) — zwei ihrer Vorlagen waren durch den Umbau veraltet und
wurden nachgezogen. Stand: **333 Tests, 0 rot.**

> **Vier Sabotagen liefen zuerst ungefangen durch.** Drei davon deckten fehlende Tests
> auf; die vierte deckte einen Designfehler bei mir auf:
> - *„Gegenprobe vergleicht gegen die falsche Grundrate"* ließ sich gar nicht sabotieren,
>   weil ich die Episoden-Grundrate **doppelt geführt** hatte — einmal über alle Kerzen
>   in `ep`, einmal in der Haupttabelle. Beide waren identisch, die Sabotage also eine
>   Nulländerung. Behoben: Es gibt jetzt genau eine Grundrate, und ein Test hält die
>   Festlegung fest (der Fenster-Durchschnitt wird nicht dadurch ein anderer, dass man
>   die Musterzeilen ausdünnt).
> - *„Die Gegenprobe (Bremse) verschwindet aus dem Gitter"* traf die falsche Stelle: Es
>   gibt drei Zeilen mit `block_unhealthy=True` im Gitter, und die Sabotage erwischte
>   eine aus E13. Auf das Label umgestellt.
> - *„Das 1.618-Ziel gilt nicht mehr als Ziel"* und *„Episoden-Gegenprobe nimmt doch alle
>   Kerzen"* waren schlicht ungetestet.

**Und ein Fehler, den die Tests selbst hatten.** Das erste Muster-5-Szenario erzeugte
**null Signale** — drei Tests verglichen zwei leere Listen und waren grün, egal was der
Code tat. Exakt der Fehlertyp aus E34, ein Vierteljahr später erneut. Das neue Szenario
hat deshalb eine **Vorprobe** (`test_m5_szenario_handelt_ueberhaupt_und_zwar_bei_muster_5`),
die drei Dinge erzwingt: mindestens drei Signale, darunter ein Zwischenverkauf *und* ein
geplantes Ziel, und alle in der Muster-5-Phase.

Der Trick, der das Szenario überhaupt möglich macht: ein hoher **Docht** auf zwei Kerzen.
Das 12-Kerzen-Fenster sieht weiter einen Rückgang (Muster 5 bleibt stehen), aber
`cur.high` erreicht die Leiter-Extensions. Ohne ihn schließen sich fallender Preis und
fällige Gewinnmitnahme gegenseitig aus.

### E38.5 — Gitterlauf gegen die Live-Zeile · **FERTIG, GEMESSEN 21.09.2026**

Fünf neue Gitterzeilen, jede mit **genau einem** Unterschied zur Live-Zeile. Ein Test
prüft das mechanisch — Lehre aus `confirm_t1` / `cooldown_h`: Ein Messergebnis gilt nur
gegen die Basis, gegen die gemessen wurde.

| Zeile | Unterschied |
|---|---|
| `+Muster 5 als Kauf-Bestaetigung` | `muster5_entry=True` |
| `+Muster 5 haelt Zwischenverkaeufe` | `muster5_halten="leiter"` |
| `+Muster 5 haelt ALLE Teilverkaeufe` | `muster5_halten="alle"` |
| `+Muster 5 sperrt Kaeufe (Bremse, Gegenprobe)` | `block_unhealthy=True` |
| `+Muster 5 Kauf UND Halten` | zwei — nur als Zusatz, kein Beleg |

**Die Gegenprobe ist der Grund, warum E38 überhaupt eine Aussage zulässt.** Sie misst
die *umgekehrte* Deutung: Muster 5 als Bremse. Das wurde in E13 schon einmal verworfen —
aber gegen eine andere Basis. Gewinnt sie hier, war die Treibstoff-Idee von Anfang an
falsch herum. Verlieren beide, sagt Muster 5 über den Ertrag schlicht nichts.

**Greift ein Schalter überhaupt?** Das zeigt die Spalte *Signale*: dieselbe Zahl wie die
Live-Zeile heißt, er ist nie angesprungen und damit nicht messbar — die Lehre aus
`neustart_mit_rest`, das in acht Monaten dreimal ansprang.

#### Ergebnis (Lauf vom 21.09.2026, Fenster 13.01.–21.09., 2444 Kerzen)

| Zeile | Rendite | Signale | H1 | H2 |
|---|---|---|---|---|
| **Live (Basis)** | +23,5 % | 238 | +18,7 % | +4,0 % |
| +Muster 5 als Kauf-Bestätigung | +24,9 % | 243 (+5) | +18,7 % | +4,8 % |
| +Muster 5 hält Zwischenverkäufe | +23,5 % | 238 | +18,7 % | +4,0 % |
| +Muster 5 hält ALLE Teilverkäufe | +23,5 % | 238 | +18,7 % | +4,0 % |
| +Muster 5 sperrt Käufe (Bremse) | +23,5 % | 237 (−1) | +18,7 % | +4,0 % |
| +Kauf UND Halten (zwei Unterschiede) | +24,9 % | 243 | +18,7 % | +4,8 % |

Max. Rückgang überall −9,4 %.

### E38.6 — Fensterhalbierung und Entscheidung · **FERTIG 21.09.2026: ALLE SCHALTER BLEIBEN AUS**

- **`muster5_halten` („leiter" und „alle") hat nie gegriffen.** Gleiche Signalzahl,
  gleiche Rendite wie die Basis. Dass der Schalter technisch ankommt, ist belegt:
  `muster5_entry` nimmt denselben Weg durch `EVAL_KEYS` und `run_backtest` und hat
  sehr wohl gewirkt. In acht Monaten gab es also **keinen einzigen fälligen
  Teilverkauf, während Muster 5 galt.** Fallender Preis (Muster 5) und fällige
  Gewinnmitnahme schließen sich im echten Markt praktisch aus — das Testszenario
  brauchte dafür einen künstlichen Docht. Nicht messbar, gleiche Kategorie wie
  `neustart_mit_rest`.
- **`muster5_entry` hat fünfmal gegriffen**, +1,4 Punkte — komplett in Hälfte 2
  (+4,8 statt +4,0 %), Hälfte 1 identisch. Die Projektregel verlangt „in **beiden**
  Hälften besser". Durchgefallen. Fünf Fälle wären ohnehin zu wenig; die Schwankung
  zwischen zwei Tagen lag bei `zonen_nachziehen` schon bei 1,1 Punkten.
- **Die Gegenprobe (Bremse) wirkt ebenfalls nicht:** ein Signal weniger, sonst nichts.

Damit trat genau der Fall ein, den der Plan vorab benannt hatte: *„Verlieren beide,
sagt Muster 5 über den Ertrag schlicht nichts."* Genauer: **über den Ertrag dieser
Engine.**

#### Warum — und warum das die eigentliche Antwort auf die Ausgangsfrage ist

Die Episoden-Gegenprobe aus E38.1 bestätigt das Signal selbst, es wird sogar stärker.
Jede der 26 Episoden nur einmal gezählt:

| Horizont | Median | gegen Grundrate | höher |
|---|---|---|---|
| 1 Tag | +1,20 % | **+1,20** | **77 %** |
| 2 Tage | +1,10 % | +1,17 | 69 % |
| 4 Tage | +0,97 % | **+1,24** | 58 % |

Auf Kerzenebene drehte der 4-Tage-Wert noch unter die Grundrate; je Episode ist er
positiv. Die späteren Kerzen einer Episode sind also die schlechteren — **die erste
Kerze einer Muster-5-Phase ist der beste Zeitpunkt.**

**Das Signal ist echt. Die Engine kann es nur nicht benutzen**, weil sie ausschließlich
an Fib-Zonen entscheidet und diese Zonen in acht Monaten nur fünfmal mit Muster 5
zusammenfielen (Einstiege) und nie (Teilverkäufe).

Das ist die bisher klarste gemessene Antwort auf die Frage, mit der alles anfing —
*„Was sieht Furkan, was wir nicht sehen?"*: **Furkan handelt auf dem Order-Flow
selbst, als Zeitsignal. Die Engine benutzt den Order-Flow nur als Bestätigung an
Preisniveaus.** Solange das so ist, kann kein Order-Flow-Schalter viel bewirken — egal
wie gut das Signal ist. Das erklärt rückblickend auch einen Teil der zwölf
durchgefallenen Filter.

#### Was daraus folgen könnte — ausdrücklich NICHT entschieden

Ein Muster-5-Einstieg **ohne** Zonenbindung wäre kein Schalter mehr, sondern ein
zweites System: eigener Stop, eigener Ausstieg, eigener Horizont (1–4 Tage statt
Wochen). Genau das wurde in E38.2 bewusst *nicht* gebaut, weil die Engine dann „im
Nichts" kaufte. Drei Einwände, die vor jedem Bau stehen:

1. **Nachlauf ist nicht Ertrag** — der Beweis steht in derselben Tabelle
   (`CAPITULATION_RESET`: schlechtester Nachlauf, trotzdem profitabel).
2. **+1,2 % Median vor Gebühren.** Der Backtest rechnet 0,1 % je Seite; bleiben ~1 %.
   Ohne Stop-Logik ist offen, was die 23 % der Fälle kosten, die *nicht* steigen.
3. **26 Ereignisse in acht Monaten**, gut drei im Monat. Wenig für eine Regel.

---

## Nebenstrang: STH-Kostenbasis

Getrennt von E38, weil es eine Datenfrage ist und keine Codefrage. Stand 20.09.2026:
Die Recherche wurde durch ein Nutzungslimit abgebrochen, bevor ein Ergebnis vorlag.
**Offen und ausdrücklich unbeantwortet:** ob checkonchain.com (oder eine andere freie
Quelle) die STH-Kostenbasis als Zahlenreihe mit brauchbarer Historie liefert — oder nur
als Bild. Ohne Reihe kein Backtest.

Korrigiert ist bisher nur die frühere Notiz „keine freie Datenquelle gefunden" in
`OFFENE-PUNKTE.md`: checkonchain ist kostenlos **zugänglich**. Ob es auch
**abrufbar** ist, ist damit nicht gesagt.
