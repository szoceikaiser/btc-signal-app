# E39 und E40 — Was passiert nach einem Stop? · STH-Kostenbasis

> Angelegt 21.09.2026. Anlass: Kaisers Frage, ob die Muster-5-Erkenntnis zu der Funktion
> wird, die er für den Fall haben wollte, dass die Engine ausgestoppt hat, er aber
> weitermacht — und ob die STH-Kostenbasis in einen Testlauf kommt.

## Vorab: E38-Anzeige (erledigt 21.09.2026)

Die Funktion für „Engine ausgestoppt, ich mache weiter" gibt es seit E35: **Lage
abrufen**. Ein zonenfreier Muster-5-Einstieg wäre dagegen ein zweites, selbst
kaufendes System — nicht gewollt. Muster 5 kommt stattdessen **als Information** in
den Abruf.

- **Text (Kaisers Wahl, Option 3, ohne Namen):** „Abverkauf mit neuen Short-Wetten -
  Kurs faellt, Spot wird verkauft, Open Interest haelt oder steigt, noch keine
  Liquidationswelle", darunter „Jan-Sep 2026 folgte darauf meist eine Gegenbewegung
  nach oben (1-4 Tage) - nicht immer." Gilt in Lage-Abruf, Plan und Vorschau.
  Zwei Abweichungen von der Vorlage: fester Zeitraum statt „seit Januar" (die Messung
  ist eine Momentaufnahme) und „hält oder steigt" (so verlangt es `classify_pattern`).
- **Ampel:** Muster 5 zählt **neutral** — weder dafür noch dagegen, auch nicht für
  einen Short. Vorher zählte es gegen den Long; die Messung widerspricht dem.
- **Folge für die Ampel-Filter-Tests:** Ihr Szenario bekam die ungünstige Ampel bisher
  aus Spot + Muster 5. Mit Muster 5 neutral sagte nur noch ein Kriterium etwas, die
  Ampel schwieg, und die Tests prüften nichts mehr. Die Vorprobe in
  `test_ampel_filter_gegenprobe_und_nullhypothese` hat das als einzige sofort gemeldet.
  Behoben mit einer kurzen EMA im Szenario (Trend + Spot statt Spot + Muster 5).
  **Die E34-Gitterzeilen (`ampel_filter`) messen ab jetzt eine leicht andere Ampel** —
  folgenlos, weil der Schalter seit E34 verworfen ist, aber ihre Zahlen sind nicht mehr
  mit denen vom 13.09. vergleichbar.
- Nebenbei: `_umbruch` trennt keine Wörter mehr am Bindestrich (aus „Short-Wetten"
  wurde sonst „Short-" / „Wetten").

## E39 — Was passiert nach einem Stop? · **FERTIG, GEMESSEN 21.09.2026**

Reine Messung auf den Stops der **Live-Einstellung** (nicht der rendite-besten Zeile —
ein Test prüft die Verdrahtung). Gemessen ab dem **Stop-Preis**, getrennt nach:

- **Art:** Stop an der Invalidierung (Kaisers Fall) gegen nachgezogenen Stop nach
  Teilgewinnen (da ist schon Gewinn gesichert — eine andere Lage)
- **Muster in der Stop-Kerze** (was die Engine in diesem Moment sah)

Je Zelle: Median, Anteil „wieder über dem Stop-Preis", und — der eigentliche Grund für
diese Messung — der **tiefste Punkt** bis dahin (Median und schlimmster Fall). Wer
weitermacht, sitzt ihn aus. Der Bericht sagt ausdrücklich, dass „wieder drüber" nicht
„Weitermachen hat sich gelohnt" heißt: gemessen wird ab Stop-Preis, nicht ab Einstand.

Geprüft: `sabotage_e39.py`, 25 Sabotagen, alle gefangen (zwei erst im zweiten
Durchgang: „schlimmster Fall ist der Median" und „Gleichstand zählt als wieder drüber").

### Ergebnis

Lauf vom 21.09.2026 (Fenster 13.01.–21.09., Live-Einstellung). **Zehn Stops in acht
Monaten, alle an der Invalidierung** — kein einziger nachgezogener Stop; Positionen
nach Teilgewinnen endeten stattdessen über `VERKAUF_REST` („Gegen-Muster am Ziel").

| Horizont | Median ab Stop-Preis | wieder drüber | tiefster Punkt bis dahin (Median / schlimmster) |
|---|---|---|---|
| 1 Tag | +0,45 % | 7 von 10 | −1,0 % / −2,7 % |
| 2 Tage | +0,58 % | **9 von 10** | −1,6 % / −3,7 % |
| 4 Tage | +2,14 % | 6 von 10 | −2,0 % / −4,0 % |

Grundrate zum Vergleich: +0,01 % nach 1 Tag, 50 % höher. Zufallswahrscheinlichkeit
bei 50 %: 9 von 10 → 1,1 %, 7 von 10 → 17 %, 6 von 10 → 38 %. Nur die 2-Tage-Zahl
sticht heraus — bei zehn Fällen.

**Muster in der Stop-Kerze: 9× NEUTRAL, 1× Kapitulation, 0× Muster 5.** Die neue
Muster-5-Zeile im Lage-Abruf wäre im Moment des Stops kein einziges Mal erschienen.
Sie kann in den Stunden danach auftauchen — aber das Muster unterscheidet
Stop-Situationen nicht.

### Der eigentliche Befund steht nicht in der Tabelle, sondern in der Stopliste

**Die Stops schließen fast alle nur knapp unter der Invalidierung.** Abstand des
Kerzenschlusses zur Invalidierung: Median **−0,28 %**, sieben von zehn innerhalb von
0,5 %, einer bei −0,003 % (78.082 gegen 78.084). Zweimal wurde dieselbe Marke
getroffen (63.100 am 31.07. und 14.08.).

Das ist genau Furkans Frage aus dem Video vom 13.09.: *„Ist es wirklich, weil Spot
verkauft wird, oder einfach um kurz Liquidität zu fischen?"* Ein einzelner
4-Stunden-Schluss knapp unter einem Tief kann beides sein, und die Engine kann es
nicht unterscheiden. Der letzte Stop der Liste (15.09.2026, 76.186 gegen 76.264)
liegt in der Zone, die das Video zwei Tage vorher als offenen Liquidierungscluster
„knapp unter dem Tief von Freitag" benannt hatte.

**Ausdrücklich nicht entschieden:** ob ein Stop, der auf einen einzelnen knappen
Schluss nicht reagiert (Puffer unter der Invalidierung oder zweite Bestätigungskerze),
besser wäre. Dagegen stehen: zehn Fälle; `conditional_stop` (E7, ähnlicher Gedanke)
war schlechter als der normale Stop; und im einen Fall, in dem der Bruch echt ist,
kostet jeder Puffer mehr. In Code und Wissens-Layer findet sich kein gemessener
Stop-Puffer — die Chronik (`docs\ETAPPENPLAN.md`) ist vor jedem Bau zu prüfen.

## E40 — STH-Kostenbasis

### E40.0 — Gibt es eine freie Quelle? · **JA — ZWEI, GEPRÜFT 21.09.2026**

Recherche 21.09.2026 (vollständig: siehe unten). **Zwei kostenlose Kandidaten**, beide
laut Doku mit täglicher Reihe, **beide aus der Arbeitsumgebung nicht prüfbar** (Proxy
blockiert). Geprüft wird deshalb im GitHub-Lauf — dort, wo die Daten später auch
geholt werden müssten. Die Probe steht als eigener Abschnitt im Backtest-Bericht, weil
der Backtest-Workflow nur den Bericht zurückschreibt (keine Workflow-Änderung nötig).

| Quelle | Laut Doku | Haken |
|---|---|---|
| **bitcoin-data.com** (BGeometrics) | `/v1/sth-realized-price`, JSON, ohne Schlüssel, ~4 Jahre | Gratis: 10/Stunde, **15/Tag je IP** — GitHub-Runner teilen IPs. Seit 09/2026 letzte 7 Tage nur im Abo |
| **bitview.space** (Bitcoin Research Kit, Open Source) | JSON/CSV, ohne Konto, ohne Limit, ab Genesis | Serienname unbekannt (Probe sucht ihn); zählt STH als < **150** Tage statt 155 |

Die Probe fragt BGeometrics **höchstens zweimal** (zweite Pfadform nur bei Bedarf) und
bitview höchstens zweimal (Suche, dann die gefundene Reihe). Sie rät keinen Seriennamen.

Ausgeschieden: checkonchain (nur Chart), Bitbo (nur Chart), Newhedge / LookIntoBitcoin
/ Glassnode / CryptoQuant / bitcoinisdata (nur bezahlt), Coin Metrics Community (nur
gesamte Realized Cap, Altersbänder bezahlt). Selbst berechnen: braucht einen Full Node
plus ~350 GB — in GitHub Actions nicht machbar.

#### Ergebnis der Probe (Backtest-Lauf 21.09.2026, 07:41 UTC)

**Beide Quellen antworten aus GitHub Actions.**

| | bitcoin-data.com (BGeometrics) | bitview.space (BRK) |
|---|---|---|
| Antwort | 200, JSON | 200, JSON |
| Reihe | `sth-realized-price` | `sth_realized_price` (in der Suche gefunden) |
| Historie | **1.446 Tage**, ab 21.09.2022 | ab 2009 (Tagesreihe, 6.473 Punkte) |
| Letzter Punkt | **14.09.2026** — genau 7 Tage Verzug, wie im Changelog angekündigt | **heute** (Zeitstempel 21.09.2026 07:41) |
| Format | `{"d", "unixTs", "sthRealizedPrice"}`, Zahlen als **Text** | reine Werteliste **ohne Datum**; Index 0 = 01.01.2009 |
| Grenzen | 15 Abrufe/Tag je IP | keine bekannt |
| STH-Definition | < 155 Tage | < 150 Tage |

**Der Wert passt zu Furkan.** BGeometrics nennt für den 14.09.2026 **71.262 $**. Im
Video vom 13.09. sagt er: *„Kostbasis der kurzfristigen Investoren lag zuletzt ja bei
ungefähr 71 000 US-Dollar."* Unabhängige Bestätigung, dass es dieselbe Größe ist.

**Datumszuordnung bei bitview — hergeleitet, nicht geraten:** Die Reihe beginnt
`[null, null, 0.0, null, null, null, null, null, 0.0, …]`. Mit Index 0 = 01.01.2009
fällt die erste 0.0 auf den **03.01.2009** (Genesis-Block) und die nächste auf den
**09.01.2009** (erster Block danach); dazwischen gab es keine Blöcke. Und der letzte
Index 6.472 fällt auf den 21.09.2026 — heute. Drei unabhängige Ankerpunkte, alle
stimmig. In E40.1 wird die Zuordnung trotzdem gegen BGeometrics geprüft.

**Ein Fehler in meiner Probe:** Sie hat bei bitview die **falsche Reihe** geholt —
`sth_awake_price` statt `sth_realized_price`. Mein Namensfilter nahm den ersten
Treffer, der „sth" und „price" enthielt. Die richtige Reihe steht in der Trefferliste,
wurde aber nicht abgerufen. Behebung in E40.1: exakter Name statt Suche.

**Folgerung für die Rollen:**

- **Backtest:** bitview als Hauptquelle (keine Tagesgrenze, volle Historie),
  BGeometrics als **Gegenprüfung** — zwei unabhängig berechnete Reihen, die sich auf
  den gemeinsamen Tagen fast decken müssen (Unterschied 150 gegen 155 Tage). Weichen sie
  deutlich ab, ist die Datumszuordnung falsch — dieselbe Vorsicht wie beim Funding in
  E37, wo zwei Quellen nur zu 71 % übereinstimmten.
- **Lage-Abruf:** bitview, weil aktuell. BGeometrics wäre sieben Tage alt.

### E40.1 — Gegenprüfung und Vorfrage · **GEMESSEN 21.09.2026**

Ersetzt die Probe aus E40.0. Holt beide Reihen mit **exaktem Namen** (der Fehler aus der
Probe — falsche bitview-Reihe — ist damit behoben) und fragt bitcoin-data.com **genau
einmal** ab.

- **Gegenprüfung:** Beide Reihen auf gemeinsamen Tagen, für Versätze von −3 bis +3 Tagen.
  Liegt der beste Versatz nicht bei 0 oder weichen sie im Median um mehr als 2 % ab, gilt
  die hergeleitete bitview-Zuordnung als zweifelhaft — dann wird mit bitcoin-data.com
  gemessen. **Die Regel stand vor dem ersten Lauf fest.**
- **Kein Blick in die Zukunft:** Jede Kerze bekommt den STH-Wert des **Vortags**. Der
  Tageswert steht erst am Tagesende fest.
- **Vorfrage:** Anteil der Kerzen, Einstiege und Stops der Live-Einstellung unter der
  STH-Kostenbasis; Nachlauf aller Kerzen und ab Einstiegspreis, getrennt nach unter /
  über; und wie oft der Zustand **wechselt** — wenige Wechsel heißen wenige lange
  Phasen, dann sind die Kerzenzahlen kein unabhängiger Beleg.

Geprüft: `sabotage_e40.py` (neu gefasst für E40.1), **17 Sabotagen, alle gefangen**.

#### Ergebnis E40.1 (Backtest-Lauf 21.09.2026, 13:56 UTC)

**Quellen:** bitview.space 5.866 Tage (ab 31.08.2010, bis heute), bitcoin-data.com
1.446 Tage (bis 14.09.). Gegenprüfung auf 1.446 gemeinsamen Tagen: **0,63 %**
Abweichung bei Versatz 0, **0,62 %** bei Versatz +1 Tag.

Die vorab festgelegte Regel („bester Versatz ≠ 0 → zweifelhaft") hat damit angeschlagen
— wegen eines Unterschieds von **0,01 Prozentpunkten**. Die STH-Kostenbasis bewegt sich
von Tag zu Tag kaum, benachbarte Versätze liegen deshalb immer fast gleichauf. **Die
Regel war zu streng gefasst** (ohne Mindestabstand). Die Folge ist harmlos: gemessen
wurde mit bitcoin-data.com, dessen Punkte ein Datum tragen und das Fenster abdecken. Die
0,6 % Grundabweichung erklären sich aus der Definition (150 gegen 155 Tage).

**Vorfrage — die eigentliche Antwort:**

| | unter STH | über STH |
|---|---:|---:|
| Kerzen | **84 %** (1.235 von 1.471) | 16 % |
| Einstiege der Live-Einstellung | **90 von 108** | 18 |
| Stops der Live-Einstellung | 9 von 10 | 1 |

Der Zustand wechselte im ganzen Fenster nur **7-mal**. Januar bis September 2026 war
im Kern **eine lange Phase unter der STH-Kostenbasis**.

Nachlauf ab Einstiegspreis: unter STH nach 4 Tagen +2,51 % (67 % höher), über STH
−0,71 % (44 % höher, nur 18 Fälle in wenigen Phasen).

**Folgerung — so wie die Vorfrage es vorsah:**

- **E40.2 (STH statt EMA200 im Trendfilter, nur über STH kaufen) wird nicht gebaut.** Er
  würde 90 von 108 Einstiegen streichen — dasselbe Schicksal wie der EMA200-Filter
  (251 → 49 Signale, −0,4 %).
- **E40.3 (größere Tranche unter STH) wird nicht gebaut.** Er träfe 83 % aller
  Einstiege und wäre damit keine Verstärkung besonderer Lagen, sondern eine allgemeine
  Vergrößerung der Positionen. Was er misst, ließe sich nicht von „einfach mehr
  investiert" trennen.
- **In diesem Fenster kann die STH-Kostenbasis keine Entscheidung der Engine
  unterscheiden.** Das ist kein Urteil über den Indikator, sondern über das Fenster:
  Mit sieben Wechseln gibt es zu wenige Phasen über der Marke.
- **Entschieden und gebaut (Kaiser, 21.09.2026): die STH-Kostenbasis als Anzeige im
  Lage-Abruf** (Abstand des Kurses zur Marke). Furkan nennt sie als Marke; als
  Information braucht sie keine Backtest-Rechtfertigung, so wie die Ampel.

#### Die STH-Zeile im Lage-Abruf (gebaut 21.09.2026)

Im Abruf steht jetzt, direkt unter den Zonen:

```
STH-Kostenbasis: 71.262 $
Kurs 6,6 % darueber
(Einstand der kurzfristigen Halter,
Stand 14.09.2026. Nur Anzeige, keine
Regel.)
```

- **Quelle:** erst bitview.space (tagesaktuell), fällt die aus, bitcoin-data.com (bis zu
  sieben Tage Verzug — deshalb steht das Datum immer dabei).
- **Fällt beides aus, fehlt nur diese Zeile.** Der Abruf selbst kommt trotzdem.
- Nur im Abruf, nicht in Plan oder Vorschau — dort entscheidet sie nichts, und jede
  Zeile mehr macht die Nachrichten länger.
- Die Abruf-Funktionen stehen seit diesem Bau in `main.py`, weil Backtest **und** Abruf
  sie nutzen. Geprüft: 9 Tests, `sabotage_e40.py` um 10 Sabotagen erweitert (27, alle
  gefangen).

### Kaisers Frage: STH zusammen mit den durchgefallenen Regeln testen?

**Nicht alle Kombinationen — aber drei, und die stehen hier, bevor es Zahlen gibt.**

Alle zwölf durchgefallenen Filter mit STH zu kombinieren hieße: dutzende Gitterzeilen,
und bei so vielen findet sich zwangsläufig eine, die gut aussieht. Das Projekt hat das
schon gemessen — bei 52 Varianten lag die Zufallserwartung für „in beiden Hälften unter
den besten fünf" bei 0,5, gemessen wurde 0. Eine Kombination, die man erst *nach* den
Zahlen auswählt, ist Rauschen mit Begründung.

Sinnvoll sind Kombinationen mit einem **Grund vorab**. Festgelegt am 21.09.2026:

1. **Vorfrage (E40.1):** Wie oft liegt der Kurs an einem Entscheidungszeitpunkt der
   Engine unter / über der STH-Kostenbasis? Die Lehre aus E38: Ein Signal, das fast nie
   auf eine Fib-Zone trifft, kann keinen Schalter tragen. Dazu der Nachlauf getrennt
   nach „Kurs unter / über STH".
2. **STH statt EMA200 im `trend_filter` (E40.2).** Der Filter fiel durch (−0,4 % gegen
   +30,9 %), weil ein Fib-Retracement definitionsgemäß im Rückgang erreicht wird. Die
   EMA200 war aber nur ein Behelf — Furkans tatsächlicher Rahmen ist u. a. die
   STH-Kostenbasis. Das ist keine beliebige Kombination, sondern **der durchgefallene
   Filter mit der Referenz, die er eigentlich hätte haben sollen.** Gegenprobe: die
   EMA200-Zeile, die schon im Gitter steht.
3. **STH als Verstärker (E40.3):** größere Tranche, wenn der Einstieg unter der
   STH-Kostenbasis liegt. Das ist die Richtung, in die bisher als einzige etwas gewirkt
   hat (länger und größer investiert, nicht vorsichtiger).

Und getrennt davon, wie bei der Ampel: **als Zeile im Lage-Abruf** — eigene
Entscheidung, auch wenn die Regeln durchfallen. Dort zählt, wie aktuell der letzte
Wert ist (BGeometrics: 7 Tage Verzug im Gratis-Plan).

Alles Weitere erst, wenn die Probe eine Reihe bestätigt hat.
