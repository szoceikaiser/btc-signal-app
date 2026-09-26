# E34 — Die Ampel: aus vier Angaben eine Aussage

Status: BAUPLAN 13.09.2026

## Anlass

Kaiser, 13.09.2026:

> *„Jetzt ist hier meine Beobachtung gefragt, jedoch habe ich keine Erfahrung mit dem
> Trading. Ich brauche einen genauen Plan, wonach ich handele, ohne selbst entscheiden
> zu müssen, sondern die Engine soll anhand der Indikatoren für mich einen Plan
> aufstellen. Wie können wir diese Nachrichten jetzt sachlich bewerten, wie zum Beispiel
> Nachfrage hat gedreht, sodass sich daraus für mich einen Plan entwickeln lässt."*

Seit E32.1 und E33-B stehen vier Angaben in jeder Nachricht: übergeordneter Trend,
Struktur, Spot-Nachfrage, Muster. Sie sind **richtig**, aber sie verlangen eine
Abwägung — und genau die kann und will Kaiser nicht leisten.

Die Ampel nimmt ihm die Abwägung ab, **ohne** ihm eine Handlung vorzuschreiben.

## Die Grenze, die dieser Ausbau nicht überschreitet

Dieses Projekt hat **neun Order-Flow-Filter gemessen — alle waren schlechter.**
Zuletzt E32.3 (13.09.2026): die 1D-Ebene, die nach Theorie der größte Hebel sein
musste, lieferte +5,5 % gegen +31,4 % und drehte die Abwärts-Beteiligung von −11 %
auf +29 %. Platz 54 von 55.

Der Grund ist im Wissens-Layer festgehalten: **Furkans Zonen sind Wartepositionen,
keine Auslöser.** Er sagt *„Ich würde die Position jetzt erstmal noch nicht
hochskalieren"* und *„wenn mir die Orderflow Daten nicht gefallen in dem Moment"* —
das ist Ermessen, keine Regel. Jedes Mal, wenn dieses Ermessen mechanisiert wurde,
wurde das Ergebnis schlechter.

Deshalb gilt: **Die Ampel ist zuerst eine Anzeige.** Sie wird gleichzeitig als
Schalter gebaut, damit der Backtest die Frage beantworten kann — aber der Schalter
steht auf aus, bis gemessen ist.

## Die Bewertungsregel

Vier Kriterien, jedes sagt **dafür**, **dagegen** oder **nichts**. „Dafür" heißt:
spricht dafür, dass die Richtung der Position weiter trägt.

| Kriterium | spricht DAFÜR (Long) | spricht DAGEGEN (Long) | keine Aussage |
|---|---|---|---|
| Übergeordneter Trend | Kurs über EMA200 | Kurs unter EMA200 | Historie reicht nicht |
| Struktur | `intakt`, `unveraendert` | `gebrochen` | `neu` (kein Vergleichsbein) |
| Spot-Nachfrage | `stabil`, `zurueckgekehrt` | `nachgelassen`, `schwach` | zu wenig Flow-Daten |
| Muster | gesunder Trend, Kapitulation | Derivate-Pump, Short-Covering, ungesunder Abverkauf | neutral |

Für eine **Short**-Position kehren sich **drei** Zeilen um: Kurs unter EMA200 spricht
dafür, nachlassende Spot-Nachfrage spricht dafür, ungesunder Abverkauf spricht dafür.

**Die Struktur-Zeile kehrt sich NICHT um.** Sie kommt aus `trend_intakt()` und misst,
ob sich das Bein *der Position* fortsetzt — bei einem Short also tieferes Tief und
tieferes Hoch. Sie spricht damit immer schon in der Richtung der Position. Trend,
Spot-Nachfrage und Muster sind dagegen absolut (steigend / fallend) und müssen
gespiegelt werden.

> Dieser Unterschied war beim ersten Bauen falsch: die Ampel spiegelte alle vier
> Zeilen und behauptete für einen Short, eine intakte Abwärtsstruktur spreche gegen
> ihn. Korrigiert, ein Test hält es fest.

Live steht `bias_short: false` — die Short-Seite wird gebaut, damit die Ampel nicht
Unsinn sagt, falls sie je eingeschaltet wird.

### Warum die Kapitulation *dafür* spricht

Das ist die einzige Zeile, die überrascht. Ein ausgeräumter Markt ist in Furkans
Methode kein Warnzeichen, sondern die **Einstiegslage** — deshalb steht live
`flush_entry: "core"`, die Engine kauft bewusst in die Kapitulation hinein. Short-
Covering dagegen ist eine Aufwärtsbewegung ohne echte Nachfrage und spricht **nicht**
für einen Long.

### Die Stufe

Einfache Mehrheit unter den Kriterien, die überhaupt etwas sagen:

| | |
|---|---|
| mehr dafür als dagegen | **GUENSTIG** |
| mehr dagegen als dafür | **UNGUENSTIG** |
| gleich viele | **GEMISCHT** |
| weniger als zwei Aussagen | **KEINE AUSSAGE** (Block entfällt) |

Alle vier Kriterien zählen **gleich viel**. Das ist eine Setzung, keine Messung —
und sie wird hier offen als solche benannt. Jede andere Gewichtung wäre genauso
willkürlich, solange nicht gemessen ist. Der `ampel_filter`-Backtest ist der erste
Schritt, aus dem eine Messung zu machen.

## Was Kaiser sieht

```
Lage:  Uebergeordnet: Kurs 77.279 $ unter EMA200 (79.140 $)
       Struktur intakt - hoeheres Tief 76.264 $, hoeheres Hoch 82.300 $
       Spot-Nachfrage nachgelassen (die Nachfrage hat gedreht)
       Muster: ungesunder Abverkauf (der Dip wird nicht gekauft)

Ampel: UNGUENSTIG — 1 von 4 spricht dafuer
       dafuer:  Struktur
       dagegen: Trend, Spot-Nachfrage, Muster
       Der Plan oben bleibt unveraendert. Die Engine handelt die Lage NICHT —
       die Ampel ist eine Beobachtung, keine Anweisung.
```

Der Schlusssatz ist der wichtigste Teil dieses Ausbaus. Er steht **immer** dort,
auch bei GUENSTIG, und er ist so formuliert, dass er keine Handlungsfreiheit
suggeriert, die die Messung nicht deckt.

## Der Schalter — und seine Gegenprobe

`ampel_filter`, Default `"off"`. Wirkung bei `UNGUENSTIG`: **halbe Tranche** statt
der vollen. Eingriff an genau einer Stelle (Nachbearbeitung der Signalliste in
`evaluate()`), weil der Zustandsautomat nicht an der Tranchengröße hängt, sondern
am Signaltyp — so kann die Ampel die Positionsgröße ändern, ohne den Ablauf zu stören.

| Wert | Wirkung | wozu |
|---|---|---|
| `"off"` | nichts | Live-Zustand |
| `"klein"` | halbe Tranche bei **UNGUENSTIG** | Kaisers Frage |
| `"gross"` | halbe Tranche bei **GUENSTIG** | **Gegenprobe: umgekehrte Ampel** |
| `"immer"` | halbe Tranche **immer** | **Nullhypothese: liegt es an der Ampel?** |

Die beiden letzten Zeilen sind der Kern der Messung. Wenn `"klein"` besser abschneidet,
`"immer"` aber **genauso gut**, dann liegt es nicht an der Ampel, sondern daran, dass
kleinere Tranchen in diesem Fenster ohnehin besser waren. Und wenn `"gross"` — die
*umgekehrte* Ampel — ebenfalls gewinnt, misst die Ampel gar nichts.

Ohne diese beiden Zeilen wäre ein gutes Ergebnis von `"klein"` nicht interpretierbar.
Das ist dieselbe Lehre wie aus der Robustheitsprüfung: eine Rangfolge allein ist
kein Beleg.

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `engine/strategy_core.py` | `ampel()`; Aufruf + Tranchen-Halbierung in `evaluate()` |
| `engine/telegram_notify.py` | Ampel-Block unter der Lage, mit Schlusssatz |
| `engine/main.py` | `ampel` in Plan und Vorschau; `EVAL_DEFAULTS` |
| `engine/backtest.py` | `ampel_filter` in `EVAL_KEYS`, drei Gitterzeilen |
| `site/data/config.json` | `ampel_filter: "off"` + Hinweistext |

## Bewusst NICHT gemacht

- **Kein Einstiegsverbot.** Die Ampel unterdrückt kein Signal. Neun gemessene
  Sperren waren alle schlechter; eine zehnte ungemessen live zu schalten wäre
  genau der Fehler, den dieses Projekt sich abgewöhnt hat.
- **Keine Gewichtung der vier Kriterien.** Ungemessen wäre jede Gewichtung geraten.
- **Kein Einfluss auf Stop oder Teilgewinne.** Die Ampel darf nur die Größe eines
  *Einstiegs* ändern, nie einen Ausstieg. Ein Ausstieg muss immer durchkommen.
- **Kein Live-Schalten.** `ampel_filter: "off"`, bis die drei Gitterzeilen gelaufen
  sind — und auch dann nur, wenn `"gross"` und `"immer"` die Erklärung nicht
  wegnehmen.
- **Keine Empfehlung zur Positionsgröße.** Wie viel Kapital insgesamt im Markt
  steht, entscheidet die Ampel nicht und kann keine Engine entscheiden.

## Umsetzung — fertig (13.09.2026)

**214 Tests grün. Sechzehn Sabotagen, alle gefangen** — drei davon erst nach einer
Korrektur, und jede Korrektur deckte einen echten Mangel auf.

| Eingriff | gefangen von |
|---|---|
| Struktur wird beim Short doch gespiegelt | `test_ampel_spiegelt_fuer_short_aber_nicht_die_struktur` |
| Ampel spricht schon bei EINER Aussage | 3 Tests |
| Mehrheitsregel vertauscht | 4 Tests |
| Tranche wird gar nicht verkleinert | 2 Tests |
| Ampel greift auch nach Ausstiegen | `test_kuerzen_laesst_ausstiege_unberuehrt` |
| Richtung wird nicht je Signal gefragt | `test_kuerzen_fragt_je_signal_nach_der_richtung` |
| Kürzung wird gar nicht aufgerufen | 5 Tests |
| Bein wird mit sich selbst verglichen | 2 Tests |
| Gegenprobe `"gross"` wirkt wie `"klein"` | 2 Tests |
| Nullhypothese hängt doch an der Ampel | 2 Tests |
| Kapitulation gilt als Gegenargument | 2 Tests |
| Schlusssatz fällt aus der Nachricht | `test_ampel_steht_in_den_nachrichten_mit_dem_schlusssatz` |
| Ampel fällt aus Plan / aus Vorschau | `test_ampel_steht_in_plan_und_vorschau` |
| doppelter Schlüssel in `EVAL_DEFAULTS` | 3 Tests |
| `ampel_filter` fällt aus `EVAL_KEYS` | 2 Tests |

### Drei Fehler, die erst die Probe gezeigt hat

**1. Die Ampel verglich das Bein mit sich selbst.** In `evaluate()` wird `pos.zones`
beim Einstieg gesetzt, *bevor* die Ampel gerechnet hätte. Bei einem frischen Einstieg
hätte sie das gerade gesetzte Bein mit sich selbst verglichen — „Struktur unverändert",
ein geschenktes Argument *dafür*, das keine Information enthält. Behoben durch einen
Merker (`_pos_imp_vorher`) ganz oben in `evaluate()`: bewertet wird die Lage, **in der
die Entscheidung fällt**, nicht die danach. Aufgefallen, weil ein Gegenproben-Test
unerwartet ansprang.

**2. Der Test für den Ausstiegs-Schutz war leer.** Er verglich in einem Szenario, das
gar keinen Ausstieg erzeugt, zwei **leere Listen** — grün, egal was der Code tut.
Genau die Art Test, die dieses Projekt sich abgewöhnt hat. Beim Reparieren stellte
sich heraus, dass der Fall durch `evaluate()` überhaupt nicht erreichbar ist: die
Ausstiegs-Zweige kehren zurück, bevor ein Einstieg feuern kann (nachgesehen über
9.000 Kerzen der Live-Einstellung — nur `WARNUNG` mit Tranche 0 tritt zusammen mit
Einstiegen auf). Der Schutz war also vorhanden, aber **tote Absicherung, die kein
Test erreicht**. Deshalb steht die Kürzung jetzt in einer eigenen Funktion
`kuerze_einstiege()`, die sich mit einer von Hand gemischten Signalliste direkt
prüfen lässt — Stop, Teilgewinn und Rest-Verkauf bleiben nachweislich unangetastet.

**3. Ein doppelter Schlüssel in `EVAL_DEFAULTS`** (aus E33, gestern): `trend_filter`
und `trend_ema` standen **zweimal** darin, einmal mit 50 und einmal mit 200. Python
nimmt stillschweigend den letzten — das Verhalten war zufällig richtig, aber wer die
obere Zeile geändert hätte, hätte keine Wirkung gesehen und keine Fehlermeldung.
`test_alle_evaluate_parameter_werden_durchgereicht` kann das nicht finden, weil es
das fertige `dict` prüft. Der neue Test liest deshalb den **Quelltext**.

### Was live geschaltet ist — und was nicht

- **Live: nichts am Handelsverhalten.** `ampel_filter` steht auf `"off"`.
- **Live: die Anzeige.** Die Ampel steht ab dem nächsten Engine-Lauf unter der Lage
  in Plan und Vorschau — mit dem Schlusssatz, der sagt, dass sie nichts tut.

So sieht Kaisers Plan-Nachricht damit aus (echte Zahlen vom 13.09.2026):

```
Lage:  Uebergeordnet: Kurs 77.279 $ unter EMA200 (79.140 $)
       Struktur intakt - hoeheres Tief 76.264 $, hoeheres Hoch 82.300 $
       Spot-Nachfrage nachgelassen (die Nachfrage hat gedreht)
       Muster: ungesunder Abverkauf (der Dip wird nicht gekauft)

Ampel: UNGUENSTIG — 1 von 4 spricht dafuer
       dafuer:  Struktur
       dagegen: Trend, Spot-Nachfrage, Muster
       Der Plan oben bleibt unveraendert. Die Engine handelt die Lage NICHT —
       die Ampel ist eine Beobachtung, keine Anweisung.
```

## Nächster Schritt

Hochladen, dann Backtest. Fünf offene Gitterzeilen auf einmal: die drei Ampel-Zeilen
und die beiden aus E33 (`+Trendfilter EMA200`, `+Trendfilter EMA50`). Insgesamt
60 Varianten.

**Wie das Ergebnis zu lesen ist** — vorher festgelegt, damit es sich hinterher nicht
zurechtlegen lässt:

- `"klein"` besser, `"gross"` und `"immer"` schlechter → die Ampel misst etwas.
  Dann, und erst dann, lohnt das Gespräch über Live-Schalten.
- `"klein"` und `"immer"` etwa gleich → es lag an der Tranchengröße, nicht an der Ampel.
- `"gross"` ebenfalls besser → die Ampel misst nichts; beide Richtungen „funktionieren".
- Alle drei innerhalb weniger Punkte → Rauschen. Die Live-Rendite schwankte in einer
  Woche um 5 Punkte; Unterschiede dieser Größe sind kein Befund.

In allen Fällen außer dem ersten bleibt die Ampel, was sie heute ist: eine Anzeige.

## Gemessen — 13.09.2026, 12:57 UTC (60 Varianten)

**Eingetreten ist der dritte Fall: die Ampel misst nichts.** `ampel_filter` bleibt
auf `"off"`, dauerhaft.

| Variante | Rendite | max. Rückgang | Signale | Aufwärts | Abwärts |
|---|---|---|---|---|---|
| **LIVE-heute +Zonen nachziehen** | **+30,9 %** | −9,7 % | 251 | 47 % | −11 % |
| +Ampel klein bei ungünstig | +26,6 % | −7,6 % | 251 | 46 % | −6 % |
| +Ampel UMGEKEHRT (Gegenprobe) | +26,4 % | −9,3 % | 251 | 36 % | −13 % |
| +immer halbe Tranche (Nullhypothese) | +19,0 % | −5,3 % | 251 | 28 % | −8 % |

Die richtige und die **umgekehrte** Ampel liegen **0,2 Punkte** auseinander. Zum
Maßstab: dieselbe Live-Zeile stand um 08:23 UTC bei +31,4 % und um 12:57 UTC bei
+30,9 % — ein halber Tag mehr Kursdaten bewegt sie um 0,5 Punkte. 0,2 Punkte sind
kein Unterschied.

### Die Fensterhalbierung macht es endgültig

| Variante | 1. Hälfte | Platz | 2. Hälfte | Platz |
|---|---|---|---|---|
| LIVE-heute +Zonen nachziehen | +27,7 % | 28. | +2,1 % | 27. |
| +Ampel klein bei ungünstig | +24,9 % | 37. | +0,9 % | 32. |
| +Ampel UMGEKEHRT | +22,6 % | 41. | **+2,5 %** | **26.** |
| +immer halbe Tranche | +16,6 % | 51. | +1,3 % | 29. |

**In der zweiten Hälfte schlägt die umgekehrte Ampel die richtige** — und die
Live-Zeile gleich mit. Das Vorzeichen dreht zwischen den Hälften. Genau dieser Fall
stand oben als „die Ampel misst nichts".

### Was die Gegenprobe verhindert hat

Ohne die Zeile `"gross"` wäre dieses Ergebnis verführerisch gewesen: `"klein"` hat
im Gesamtfenster den **besseren Rückgang** (−7,6 statt −9,7 %), die **bessere
Abwärts-Beteiligung** (−6 statt −11 %) und praktisch **dieselbe Aufwärts-Beteiligung**
(46 statt 47 %). Nach den Kennzahlen, denen dieses Projekt sonst traut, sieht das aus
wie „weniger Risiko bei gleicher Teilhabe".

Die umgekehrte Ampel zeigt, dass das nicht an der Ampel liegt: Sie halbiert nach der
**entgegengesetzten** Regel und landet bei derselben Rendite. Was die Varianten trennt,
ist wie viel im Mittel investiert war — nicht *wann*.

**Übertragbar:** Jede künftige Messung eines Filters bekommt eine umgekehrte Zeile.
Eine Variante, die besser aussieht als die Live-Zeile, ist so lange kein Befund, wie
ihr Spiegelbild nicht gemessen ist.

### Was bleibt

- **`ampel_filter` bleibt `"off"`.** Nicht „bis zur nächsten Messung" — gemessen und
  durchgefallen.
- **Die Ampel als Anzeige bleibt.** Sie kostet nichts, sie ist nachweislich keine
  Handelsregel, und sie beantwortet Kaisers eigentliche Frage: die vier Angaben zu
  einer lesbaren Aussage zusammenzufassen.
- **Der Code bleibt**, wie `pivot_n_1d` nach E32.3 — Default `"off"`, damit eine
  spätere Messung auf einer anderen Basis nicht bei null anfängt.
