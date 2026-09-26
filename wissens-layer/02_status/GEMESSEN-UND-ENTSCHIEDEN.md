# Gemessen und entschieden

> Die Landkarte über allem, was in diesem Projekt ausprobiert wurde. Zweck: Man soll
> auf einen Blick sehen, was schon durchgefallen ist, statt 1.800 Zeilen Chronik zu
> lesen — und nichts wieder vorschlagen, was bereits gemessen und verworfen wurde.
>
> Stand: 26.09.2026. Maßgeblich bleiben `site\data\config.json` (Hinweistexte zu jedem
> Schalter) und `docs\ETAPPENPLAN.md` (die vollständige Chronik).

> **VORBEHALT seit 26.09.2026 (Gesamtprüfung, `docs\PRUEFUNG-2026-09-26-GESAMT.md`):**
> Die Order-Flow-Muster wurden mit zwei Messfehlern erkannt (Muster 2 hängt vom
> Startpunkt der CVD-Summe ab; Open Interest in $ bewegt sich mit dem Kurs). Urteile, die
> an Muster 2 bis 5 hängen, gelten bis zur Nachmessung als **vorläufig**. Außerdem:
> `be_im_plus` ist **nicht** Furkans Regel (Vorbedingung fehlt), und der Satz zu E37
> „keine einzige Variante in beiden Hälften besser“ stimmt für den Lauf vom 23.09. nicht
> mehr (OI aggregiert H1 +0,6 / H2 +1,0, nach der Rauschgrenze trotzdem kein Befund).
> **Nachtrag 26.09.2026 (E43.3 gemessen):** Der erste der beiden Messfehler (A2, Startpunkt
> der CVD-Summe) ändert im Datensatz nur 2 von 1.504 Kerzen und kein Ergebnis. Der
> Vorbehalt hängt damit im Wesentlichen noch an A3 (OI in Dollar, E43.4).

## Wie diese Tabelle zu lesen ist

**Wichtige Warnung zu den Zahlen:** Die Backtest-Zeilen stammen aus verschiedenen
Zeitpunkten und bauen auf verschiedenen Basisvarianten auf. Eine Zeile von Juli
gegen eine von September zu stellen, ist kein fairer Vergleich — genau dieser Fehler
ist in diesem Projekt schon zweimal passiert. Fair vergleichbar sind nur Zeilen, die
sich in **genau einem** benannten Punkt unterscheiden. Wo unten Zahlen stehen, gehören
sie zu dem Vergleich, der in der Fundstelle benannt ist.

**Recall ist kein Gewinn.** Er misst nur die Ähnlichkeit zu Kaisers notierten
Furkan-Terminen, nicht den Ertrag.

**Die Rangfolge im Gitter ist kein Beleg.** Bei 67 Varianten und je 5 Plätzen in zwei
Fensterhälften liegt der Zufallserwartungswert bei 0,4 Varianten in beiden Hälften
unter den besten 5. Gemessen am 23.09.2026: 0. Nur groben Hebeln trauen (Richtung, Kaufleiter,
Flush), Feinheiten nicht.

## Live geschaltet

| Mechanismus | Seit | Warum an |
|---|---|---|
| `bias_long` (nur Long, `bias_short` aus) | Beginn | Mechanische Shorts ohne Makro-Bias verlieren |
| `buy_ladder` — Mehrtages-Kaufleiter | E8 | Deutlichster Renditehebel im Gitter, robust |
| `flush_entry: core` — Einstieg in die Kapitulation | E9.1 | Erst mit echten Liquidationsdaten positiv; vorher war `off` besser |
| `tp_ladder` — gestaffelte Teilgewinne an 0.8/0.9 | E8.2 | Bildet Furkans Vorgehen ab, Rendite leicht besser |
| `trail_stop` — Stop nachziehen nach Teilgewinnen | E9.10 | Furkan-Zitat „Stop über den Kauf gezogen"; Stop kann nur steigen |
| `high_exit: on` — Teilverkauf unter dem letzten Hoch | E10.2 | Dort sitzt das Angebot |
| `liq_entry: boost` — Nachkauf bei Fib-/Liquidations-Konfluenz | E10.3 | Furkans Konfluenz-Gedanke |
| `min_stop_pct: 0.02` — Mindestabstand Einstieg/Stop | E13 | 15 von 34 Positionen lagen darunter, eine bei 0,02 % |
| `min_bein_pct: 0.05` — Mindestlänge eines Beins | E19 | Der geforderte Stopabstand verlangt implizit ~5,5 % Beinlänge |
| `no_flip` — kein Kauf und Verkauf in derselben Kerze | E25, 28.08. | Beseitigt alle 16 Gegengeschäfte; kostet 3,1 Punkte Rendite und ist **nicht robust** — trotzdem an, weil 14 der 16 Paare denselben Preis hatten und in der Praxis gar nicht ausführbar wären |
| `neustart_mit_rest` — neu einsteigen, während ein Rest läuft | E26, 28.08. | Greift in 8 Monaten nur dreimal, **kein belegter Renditehebel** — an, weil es nichts kostet und einen Konstruktionsfehler behebt |
| `zonen_nachziehen` — Zonen der laufenden Position mitziehen | E30, 05.09. | **Die Rendite kippt zwischen zwei Tagen:** 05.09. +0,1 Punkte vorn, 06.09. 1,0 Punkte hinten. Rückgang beide Male gleich (−9,7 %), Beteiligung beide Male besser (Aufwärts 52 statt 51, Abwärts −14 statt −17). An wegen der Konstruktion, nicht wegen der Rendite |
| `stop_rueckeroberung: 1` — Stop erst, wenn die Marke nicht zurückerobert wird (Kaisers Regel) | E41, 21.09. | +26,4 gegen +23,5 %, Hälfte 1 +2,6 Punkte, **Hälfte 2 nur +0,2 (Rauschen)**, Rückgang 0,9 Punkte tiefer (Grenze 1,0), 9 statt 10 Stops; besteht mit 1 **und** 3 Kerzen. **Ausschalt-Regel vorab festgelegt:** aus, wenn der alte Stop in beiden Hälften ≥ 1 Punkt besser ist oder der Rückgang live > 1 Punkt tiefer liegt — der Bericht prüft das selbst. Telegram meldet Warten und Rückeroberung. **NACHMESSUNG 23.09.2026: die Ausschalt-Regel hat angeschlagen** (Rückgang 1,5 statt höchstens 1,0 Punkte tiefer) — Kaiser hat sie **bewusst überstimmt**: Rendite +2,6 Punkte, in beiden Hälften besser, und der Rückgangsvergleich zwischen zwei Varianten ist pfadabhängig. Der Bericht meldet weiter AUSSCHALTEN, der Hinweis steht daneben. **NACHMESSUNG 26.09.2026 auf der neuen Live-Basis (`bein_richtung: bias`): die Regel schlägt nicht mehr an** — Rückgang gleich (−9,9 %), H1 +4,0, H2 +0,2 Punkte für live, der Bericht meldet „Bleibt an“ (`docs\PLAN-E41-STOP.md`) |
| `pivot_n: 5`, `k_atr: 2.0`, `bein_wahl: juengstes`, `bein_richtung: auto` | Beginn / E19 | Struktur-Parameter, keine Ein-/Aus-Schalter. Sie bestimmen, welches Bein die Zonen zeichnet. Nur ändern, wenn ein Backtest-Lauf es stützt |
| `vorschau_telegram`, `plan_telegram`, `flush_wache` | E17, E22 | Marken vorher hinterlegbar machen — Signale nennen oft Preise, die es nicht mehr gibt |

### Ein Lehrstück zum Thema „Rauschen" (06.09.2026)

`zonen_nachziehen` wurde an zwei aufeinanderfolgenden Tagen gemessen. Zwischen den
Läufen liegt **ein Tag mehr Kursdaten**, sonst nichts:

| | 05.09. | 06.09. |
|---|---|---|
| LIVE +Neustart mit Rest | +36,3 % | +37,1 % |
| LIVE +Zonen nachziehen | +36,4 % | +36,1 % |
| **Vorsprung** | **+0,1 für Nachziehen** | **−1,0 gegen Nachziehen** |

Ein einziger Tag dreht das Vorzeichen. Wer aus einem Unterschied von einem Punkt eine
Entscheidung ableitet, entscheidet über Rauschen. Stabil blieben dagegen der maximale
Rückgang (beide Male −9,7 %) und die Beteiligungspaare (Aufwärts 52 gegen 51, Abwärts
−14 gegen −17). Genau deshalb sind das die Kennzahlen, denen man trauen darf.

## Gemessen und verworfen

| Mechanismus | Ergebnis | Fundstelle |
|---|---|---|
| `trend_filter` — Einstiege nur in Richtung des Tages-Trends | **Durchgefallen, deutlich** (13.09.2026). EMA200: Rendite **−0,4 %** gegen +30,9 % live, Signale von **251 auf 49**, Aufwärts-Beteiligung von 47 auf **1 %**, Platz **59 von 60**. EMA50 als Gegenprobe: +4,7 %, 111 Signale, Platz 58 — es liegt also **nicht an der Länge**. Der Filter schaltet die Engine nicht schärfer, sondern ab: Ein Fib-Retracement wird definitionsgemäß in einem Rückgang erreicht — genau die Momente, die der Filter ausschließt | `docs\PLAN-E33-UEBERGEORDNETER-TREND.md` |
| `ampel_filter` — kleinere Tranchen bei ungünstiger Lage | **Misst nichts** (13.09.2026). `klein` +26,6 % gegen `gross` (umgekehrte Ampel) +26,4 % — **0,2 Punkte**. In der zweiten Fensterhälfte schlägt die **umgekehrte** Ampel die richtige (+2,5 gegen +0,9 %) und die Live-Zeile gleich mit. Das Vorzeichen dreht zwischen den Hälften | `docs\PLAN-E34-AMPEL.md` |
| `zonen_1d` — 1D-Ebene als zweiter Zonensatz | **Zweimal verworfen.** E23: Robustheitsprüfung durchgefallen. E32.3 (13.09.2026) mit eigener Swing-Weite erneut gemessen — Rendite +5,5 % gegen +31,4 % live, Rückgang −22,9 % gegen −9,7 %, Abwärts-Beteiligung dreht von −11 auf **+29 %**. Platz 54 von 55 in der zweiten Hälfte | `docs\PRUEFUNG-1D-EBENE.md`, `docs\PLAN-E32-LAGEZEILE.md` |
| `pivot_n_1d` — eigene Swing-Weite für die 1D-Ebene | Gebaut, gemessen, verworfen (siehe Zeile darüber). Bleibt als Parameter im Code, Default 0 = altes Verhalten | `docs\PLAN-E32-LAGEZEILE.md` |
| `rest_halten` — Restposition nie verkaufen | Eins-zu-eins-Tausch: Aufwärts +4, Abwärts +4. Kein Gewinn, nur mehr Risiko | E26 |
| `freeze_targets` — Ziele nach dem ersten Teilgewinn festhalten | Rendite schlechter | E18.3 |
| `conditional_stop` — bei Verlust nachkaufen statt stoppen | Schlechter als der normale Stop | E7 |
| `liq_exit` (spike / zone / both) | Rendite schlechter, dazu 8 bis 26 Gegengeschäfte | E9.11 |
| `bein_wahl: groesstes` | Aufwärts-Beteiligung bricht auf 11 % ein | E19 |
| `block_unhealthy` — kein Kauf im ungesunden Abverkauf | Rendite schlechter | E13 |
| `widerstand_exit` — Teilverkauf an der Widerstandszone | Kostete Rendite | E20 |
| **Muster 5 als Treibstoff** (E38, 21.09.2026) — `muster5_entry`, `muster5_halten` (leiter/alle), Gegenprobe `block_unhealthy` | **Durchgefallen — aber weil die Schalter kaum greifen, nicht weil das Signal falsch ist.** `muster5_halten` griff in acht Monaten **nie** (238 Signale wie die Basis). `muster5_entry` griff fünfmal, +1,4 Punkte, nur in Hälfte 2. Die Bremse: ein Signal weniger. Das Signal selbst hält der Episoden-Gegenprobe stand (+1,2 Punkte über Grundrate, 77 % höher) — die Engine entscheidet nur fast nie, während es gilt | `docs\PLAN-E38-MUSTER5.md` |
| **STH-Kostenbasis als Regel** (E40.2/E40.3, 21.09.2026) — Filter „nur über STH" und Verstärker „unter STH" | **Nicht gebaut, weil die Vorfrage es ausschließt.** Jan–Sep 2026 lag der Kurs zu 84 % unter der STH-Kostenbasis, 90 von 108 Einstiegen darunter, nur 7 Wechsel im ganzen Fenster. Der Filter strich 83 % der Einstiege (wie EMA200), der Verstärker wäre eine allgemeine Positionsvergrößerung. Urteil über das Fenster, nicht über den Indikator. Quellen: bitview.space und bitcoin-data.com, beide frei, Abweichung 0,6 % | `docs\PLAN-E39-E40.md` |
| **Stop-Puffer 0,5 % und Stop beim Docht** (E41, 21.09.2026) — `stop_puffer_pct`, `stop_auf_docht` | **Docht (die strengere Richtung): durchgefallen** (+23,9 %, Hälfte 2 schlechter, 12 statt 10 Stops). **Puffer: formal bestanden, trotzdem nicht genommen** — der Wert 0,5 % lag nahe an den zehn Stops, die vorher angesehen wurden; das Risiko „auf genau diese Stops hin eingestellt" war im Plan benannt. Beide seit der Live-Schaltung der Rückeroberung aus dem Gitter | `docs\PLAN-E41-STOP.md` |
| **Aggregation über mehrere Börsen** (E37, 20.09.2026) — Spot-CVD, Open Interest, Liquidationen, Futures-CVD, Funding, Long-Short | **Durchgefallen, und zwar in der Robustheitsprüfung.** Im Vollfenster sah manches gut aus (OI +1,1 Punkte, Trefferquote 56→61 % Recall und 32→35 % Präzision bei 21 Signalen weniger). In der Halbierung war „OI aggregiert“ im Lauf vom 23.09. tatsächlich in BEIDEN Hälften besser (H1 +0,6, H2 +1,0) — H1 lag aber unter der 1-Punkt-Rauschgrenze, das Urteil hält also trotzdem (**berichtigt 26.09.2026**, Gesamtprüfung Teil E Punkt 7 — der ursprüngliche Satz „keine einzige Variante in beiden Hälften besser“ war für diesen Lauf falsch). Die Rangfolge kippt sonst lehrbuchmäßig: heutiger Stand Platz 1 in H1 und Platz 7 in H2; aggregiertes Spot-CVD genau umgekehrt. Funding aggregiert ist ein klares Nein (−6,1 Punkte auch nach Skalen-Normierung) | `docs\PLAN-E37-AGGREGATION.md` |
| `muster_cvd: usd` — Muster 2 vergleicht Dollar-Beträge im Fenster (E43.3, Befund A2, 26.09.2026) | **Misst fast nichts.** Nur **2 von 1.504** Kerzen anders erkannt; Rendite, Rückgang, beide Hälften und 244 Signale identisch. Entscheidungsregel nicht erfüllt → bleibt `alt`. Live gegen Backtest wich mit `alt` an 1 von 1.175 Kerzen ab, mit `usd` an 0: A2 ist echt, aber im Datensatz klein | `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md` |

## Gemessen, aber nie entschieden — offene Baustelle

Diese vier Schalter wurden im Gitter gemessen und stehen seither auf „erst nach
Backtest-Messung einschalten". Sie sind **nicht verworfen** — es wurde nur nie
entschieden. Zwei davon sahen auf ihrer damaligen Basis sogar besser aus:

| Schalter | Gemessen (alte Basis: *LIVE +Stop nachziehen*, +33,3 %) | Stand |
|---|---|---|
| `confirm_t1` — Order-Flow-Prüfung auch am 0.5-Level | heute im Gitter **+36,1 %** gegen Basis +33,3 % — aber 07/2026 mit **−4,6 Punkten** verworfen | aus |
| `cooldown_h: 48` — Sperrfrist nach einem Stop | heute **+36,5 %** gegen Basis +33,3 % — 07/2026 als „wirkt, kippt aber zwischen den Hälften" verworfen | aus |
| `be_im_plus` — Stop auf Einstand, sobald einmal im Plus | in der Fensterhalbierung auf Platz 48 und 52 von 52 — deutlich schlechter | aus |
| `release_stale_rest` — Rest freigeben bei veralteter Struktur | durch `trail_stop` und `neustart_mit_rest` praktisch ersetzt | aus |

**Wichtig und ehrlich — hier widersprachen sich zwei Quellen.** Zu `confirm_t1` und
`cooldown_h` gab es je zwei Zahlen: eine aus dem damaligen Gitter (beide besser als
ihre Basis) und eine aus `ANLEITUNG-EINSTELLUNGEN.md` vom 28.07.2026 (beide verworfen).
Beide konnten stimmen — sie waren gegen verschiedene Basisvarianten gemessen. Auf der
heutigen Live-Zeile mit genau einem Unterschied war keiner der beiden je gemessen.

**Erledigt 26.09.2026 (E43.6):** Genau diese Lücke ist jetzt geschlossen. Gegen die
heutige Live-Zeile mit genau einem Unterschied gemessen: `confirm_t1` (+35,0 % gegen
Live +35,4 %, H1 −0,8/H2 +0,9 Punkte) und `cooldown_h: 48` (+33,5 % gegen +35,4 %,
H1 −1,8/H2 +0,0 Punkte) erfüllen beide die vorab festgelegte Regel nicht (keiner in
beiden Fensterhälften mindestens 1 Punkt besser) — beide bleiben aus. Einzelheiten:
`docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt E43.6.

Damit gilt hier dieselbe Lehre, die im Projekt schon einmal teuer war: **Ein
Messergebnis gilt nur gegen die Basis, gegen die gemessen wurde. Nach jeder
Live-Umstellung sind verworfene Mechanismen wieder offen.** `high_exit` war fünfmal als
„kostet Rendite" verworfen — und ist heute eingeschaltet.

### Warum ein größeres Bein die Engine schlechter macht (13.09.2026)

Furkan rechnet mit einem 32-%-Bein, die Engine mit einem 8-%-Bein — sein Golden Pocket
lag am 12.09. bei 69.000–70.000, ihres bei 78.377–78.570. Das sah nach dem größten
offenen Hebel aus. Gemessen ist es das Gegenteil: Rendite bricht von +31,4 auf +5,5 %
ein, der Rückgang verdoppelt sich.

Der Grund ist kein Rechenfehler, sondern ein Unterschied in der Handhabung:

> **Furkans Zonen sind Wartepositionen, keine Auslöser.** Er sagt im selben Video
> „Ich würde die Position jetzt erstmal noch nicht hochskalieren" und „wenn ich hier
> nicht aufstocke, weil mir die Orderflow Daten nicht gefallen in dem Moment". Er hat
> die Zone und kauft trotzdem nicht. Die Engine kauft bei Berührung.

Ein größeres Bein heißt für sie: tiefer kaufen, häufiger kaufen, Stop 18 % entfernt.
Das verstärkt den Unterschied zu ihm, statt ihn zu schließen.

**Übertragbar auf jede künftige Idee dieser Art:** Bevor eine Beobachtung aus einem
Video in eine Regel wandert, muss geklärt sein, ob Furkan sie als Regel anwendet oder
als Ermessensspielraum. Zonen, Zielmarken und Aufstockungsniveaus sind bei ihm
Letzteres.

## Gebaut als Anzeige, nicht als Regel

Ein eigener Weg, der 2026 dreimal gegangen wurde, weil **neun Order-Flow-Filter
gemessen wurden und alle schlechter waren.** Die Beobachtung wird nicht verworfen —
sie wird angezeigt, statt gehandelt. Das kostet nichts und lässt die Entscheidung bei
Kaiser, so wie Furkan sie bei sich lässt.

| Was | Seit | Inhalt |
|---|---|---|
| **Lagezeile** (E32.1) | 12.09. | Struktur (Preis) und Spot-Nachfrage (Order-Flow) getrennt, dazu das Muster. Anlass: *„ich bekomme die info zur struktur nur, wenn ich eine nachricht für ein nachkauf erhalte. doch das ist zu spät, weil ich doch die limits vorher setze"* |
| **Übergeordneter Trend** (E33-B) | 13.09. | Kurs gegen Tages-EMA200, an erster Stelle der Lage. Dafür lädt der Hauptlauf 1.300 statt 400 Kerzen (nachgewiesen signalneutral) |
| **Ampel** (E34) | 13.09. | Fasst alle vier Angaben zu **einer** Aussage zusammen: günstig / gemischt / ungünstig, nach einfacher Mehrheit. Anlass: *„Ich brauche einen genauen Plan, wonach ich handele, ohne selbst entscheiden zu müssen"* |
| **STH-Kostenbasis im Lage-Abruf** (E40) | 21.09. | Wert, Abstand des Kurses in Prozent, Datum. Als Regel im Fenster nicht prüfbar (84 % der Kerzen darunter, 7 Wechsel) — als Marke, die Furkan nennt, trotzdem sichtbar. Quelle bitview.space, Ersatz bitcoin-data.com |

**Die Ampel sagt in jeder Nachricht selbst, dass sie nichts tut:** *„Der Plan oben
bleibt unverändert. Die Engine handelt die Lage NICHT — die Ampel ist eine
Beobachtung, keine Anweisung."* Dieser Satz ist Absicht und steht auch bei GÜNSTIG da.

Parallel wurde `ampel_filter` gebaut (Default `off`) und am 13.09.2026 gemessen —
**durchgefallen**, siehe die Tabelle „Gemessen und verworfen" und den Abschnitt
darunter. Die Anzeige bleibt, die Regel kommt nicht.

### Die Gegenprobe, die eine Fehlentscheidung verhindert hat (13.09.2026)

Das wichtigste Ergebnis dieses Tages ist keine Zahl, sondern eine Methode.

`ampel_filter="klein"` sah im Gesamtfenster **gut aus**: besserer maximaler Rückgang
(−7,6 statt −9,7 %), bessere Abwärts-Beteiligung (−6 statt −11 %), praktisch dieselbe
Aufwärts-Beteiligung (46 statt 47 %). Nach genau den Kennzahlen, denen dieses Projekt
sonst traut, liest sich das als „weniger Risiko bei gleicher Teilhabe" — ein Kandidat
fürs Live-Schalten.

Gemessen wurde aber gleichzeitig `"gross"`: **dieselbe Kürzung nach der
entgegengesetzten Regel.** Ergebnis +26,4 % gegen +26,6 % — 0,2 Punkte. Und in der
zweiten Fensterhälfte ist die *umgekehrte* Ampel besser als die richtige.

> **Regel ab jetzt: Jede Messung eines Filters bekommt eine umgekehrte Zeile.** Eine
> Variante, die besser aussieht als die Live-Zeile, ist so lange kein Befund, wie ihr
> Spiegelbild nicht mitgemessen ist. Eine dritte Zeile ohne den Filter (hier: `immer`,
> halbe Tranche ohne Ampel) trennt zusätzlich den Mechanismus von seiner Nebenwirkung.

Das ist die Verallgemeinerung der schon bekannten Warnung „eine Rangfolge ist kein
Beleg" — nur mit einem Werkzeug, das *vor* der Entscheidung greift statt danach.

### Der Maßstab fürs Rauschen, konkret (13.09.2026)

Dieselbe Live-Zeile, zwei Läufe am selben Tag:

| | 08:23 UTC | 12:57 UTC |
|---|---|---|
| LIVE-heute +Zonen nachziehen | +31,4 % | +30,9 % |

**Ein halber Tag mehr Kursdaten = 0,5 Punkte.** Wer einen Unterschied von unter einem
Punkt für einen Befund hält, entscheidet über Rauschen. (Das Gegenstück vom 06.09.:
ein ganzer Tag drehte dort ein Vorzeichen.)

## Zurückgenommen oder zu den Akten gelegt

| Thema | Was passiert ist |
|---|---|
| Break-even-Stop nach Aufstockung (E28) | Gebaut, dann auf Kaisers Wunsch zurückgenommen: *„das mit dem stop nachziehen möchte ich doch nicht haben. Das werde ich im laufe der trades ggf. Selber tun."* Ermessensfrage, bleibt bei ihm. Bauplan liegt als Vorlage in `docs\PLAN-E28-BREAKEVEN-NACH-AUFSTOCKUNG.md` |
| MVRV-Z als Richtungs-Bias (E29) | Datenquelle vorhanden, aber im Messfenster durchgehend 0,24–0,42 — kein einziger Schwellenwechsel, also nicht messbar |
| Warnungen entrümpeln | Kaiser: so lassen. Wiederholungen sind keine Doppelung, sondern eine Dauerangabe |

## Nicht Schalter, sondern behobene Fehler

| Fund | Datum | Kern |
|---|---|---|
| Rückgangsmessung war zu freundlich | 28.08. (E27) | Gemessen wurde nur an Signalzeitpunkten. Seither lückenlos an jeder Kerze und ihrem ungünstigsten Punkt. **Alle Rückgangszahlen aus Berichten davor sind nicht vergleichbar** |
| `no_flip` deckte den Neustart nicht ab | 05.09. (E30.2b) | Der Neustart-Block lief nach dem Positions-Management und stieg ein, ohne `no_flip` zu fragen. Betraf auch die Live-Einstellung — dass sie 0 Gegengeschäfte zeigte, war Zufall |
| Chart-Webseite war 8 Tage veraltet | 05.09. | GitHub löst bei Pushes, die ein Workflow selbst macht, keine weiteren Workflows aus. Die Seite baute nach Engine- und Backtest-Läufen nie neu. Behoben per `workflow_run` in `signal-app\.github\workflows\pages.yml` |
| `flush_entry` und `tp_ladder` wurden nicht gelesen | 27.08. (E18.1) | Standen in `config.json`, wurden von der Engine aber ignoriert |
| `EVAL_DEFAULTS` nannte zwei Schalter **doppelt** | 13.09. (E34) | `trend_filter` und `trend_ema` standen zweimal darin (einmal 50, einmal 200). Python nimmt still den letzten — das Verhalten war zufällig richtig, aber eine Änderung an der oberen Zeile hätte keine Wirkung und keine Fehlermeldung gehabt. Der Test, der alle Parameter prüft, kann das nicht finden: er sieht das fertige `dict`. Der neue Test liest den **Quelltext** |

### Zwei Lehren aus der Sabotage-Probe zu E34 (13.09.2026)

**1. Ein Test, der zwei leere Listen vergleicht, ist grün, egal was der Code tut.**
Der Test „die Ampel lässt Ausstiege unberührt" lief in einem Szenario, das gar keinen
Ausstieg erzeugt. Die Sabotage-Probe hat ihn entlarvt — ohne sie wäre der
gefährlichste denkbare Fehler dieses Ausbaus (ein halbierter Stop lässt die halbe
Position im fallenden Markt liegen) ungeprüft geblieben.

Beim Reparieren zeigte sich: Der Fall ist durch `evaluate()` gar nicht erreichbar —
die Ausstiegs-Zweige kehren zurück, bevor ein Einstieg feuern kann (nachgesehen über
9.000 Kerzen). Der Schutz war also **tote Absicherung, die kein Test erreicht**.
Deshalb steht er jetzt in einer eigenen Funktion (`kuerze_einstiege`), die sich mit
einer von Hand gemischten Signalliste direkt prüfen lässt.
**Übertragbar:** Lässt sich eine Schutzregel im laufenden System nicht auslösen, gehört
sie in eine eigene Funktion — sonst prüft man sie nie.

**2. Eine Zusammenfassung darf sich nicht selbst bestätigen.** Die erste Fassung der
Ampel verglich bei einem frischen Einstieg das gerade gesetzte Bein **mit sich selbst**
(`pos.zones` wird im selben Durchlauf gesetzt) und bekam ein Argument *dafür*
geschenkt, das keine Information enthält. Behoben durch einen Merker ganz oben in
`evaluate()`: bewertet wird die Lage, **in der die Entscheidung fällt**, nicht die
danach.

## Der Befund hinter E37: die Engine misst eine Börse, nicht den Markt

**Das Kürzel `.A` in den Coinalyze-Symbolen heißt Binance, nicht „aggregiert".** Der
Code behauptete das Gegenteil, von E9.1 (Juli 2026) bis zum 19.09.2026. Nachgewiesen:
`/exchanges` listet 28 Börsen mit `{'name': 'Binance', 'code': 'A'}`, und von 5436
Futures-Märkten benutzt keiner einen Code, der nicht in dieser Liste steht — es gibt
also nirgends ein Kürzel für ein Aggregat.

| Wert | tatsächliche Quelle | Börse |
|---|---|---|
| Spot-CVD | `data-api.binance.vision` | Binance |
| Futures-CVD, Open Interest, Liquidationen, Long-Short | Coinalyze `BTCUSDT_PERP.A` | Binance |
| **Funding** | **`futures.kraken.com`, stündlich ×8** | **Kraken** |

**Das Funding ist der unangenehmste Teil:** Es kommt von einer *anderen* Börse als
alles übrige, und das stand nirgends. `classify_pattern` vergleicht Binance-OI und
Binance-CVD gegen eine Kraken-Funding-Rate. `coinalyze.funding_by_ts()` existiert,
wird nirgends aufgerufen und hat keinen Test.

**Ableitung für künftige Arbeit:** Eine Annahme über fremde Daten gilt erst, wenn die
Quelle sie bestätigt hat. Ein Kommentar ist kein Nachweis — und eine Tabelle, die aus
dem Code-Aufbau geschlossen wurde, auch nicht. (Die erste Fassung dieses Befunds
führte das Funding selbst falsch unter Coinalyze.)

### Offen, ausdrücklich nicht entschieden

- **71 % Vorzeichen-Übereinstimmung** zwischen Kraken- und Coinalyze-Funding. In fast
  jedem dritten Zeitpunkt widersprechen sich die beiden Reihen. Solange das nicht
  erklärt ist, wäre ein Quellentausch ein Austausch der Bedeutung, nicht der
  Genauigkeit. **Berichtigt 26.09.2026** (Gesamtprüfung Teil E Punkt 7): Der „Faktor
  ~69“ zwischen den Skalen ist im Kern keine echte Diskrepanz, sondern eine **Einheit**
  — Coinalyze liefert Funding in Prozent (0,01 = 0,01 %), Kraken als Bruch. Rechnet man
  das um, ist der verbleibende Niveauunterschied klein (Median 3,8e-5 gegen 2,6e-5 als
  Bruch). Die Vorzeichen-Frage (71 % Übereinstimmung) bleibt davon unberührt und offen.
- Ob die Schwelle `funding_hot = 0.0001` zur Kraken-Reihe überhaupt passt. Sie wurde
  nie gegen diese Skala geprüft.
- **OKX hat bei Coinalyze keinen Spotmarkt** (belegt: Binance 49 abgelehnte
  BTC-Märkte, Coinbase 22, Bybit 16 — OKX null Einträge). Futures dagegen schon.

### Was von E37 bleibt, obwohl nichts live ging

Der Werkzeugkasten ist gebaut und geprüft: `spot_delta_aggregiert`, `oi_aggregiert`,
`liq_aggregiert`, `fut_delta_aggregiert`, `gewichtetes_mittel`, `skalen_vergleich`,
`perp_auswahl`. Falls später ein Grund auftaucht, ist Aggregation ein Schalter, kein
Neubau. Dazu drei Regeln, die jetzt an EINER Stelle stehen und für alle Werte gelten:

1. **Ein Zeitpunkt zählt nur, wenn ALLE Börsen ihn haben.** Sonst sähe eine Teilsumme
   beim Open Interest aus wie ein Einbruch um ein Drittel — also wie genau das Signal,
   auf das Muster 4 wartet. Ein Datenloch würde zum Kaufsignal.
2. **Summieren nur bei gleicher Denominierung.** OI und Liquidationen kommen in USD
   (`convert_to_usd`) und sind summierbar; `ohlcv-history` ignoriert das Flag und
   liefert in der Einheit des Marktes.
3. **Funding und Long-Short werden gewichtet, nicht summiert.** Ein Preis ist keine
   Menge. Ein *einfacher* Durchschnitt gäbe einer Zwergbörse dasselbe Gewicht wie
   Binance — und die Zahl sähe dabei völlig normal aus.

### Coinalyze: harte Grenzen, gemessen

- Intraday-Historie **1500–2000 Punkte**, ältere werden täglich gelöscht. Deshalb
  wandert das Backtest-Fenster mit; Zahlen aus zwei Läufen sind nur vergleichbar, wenn
  die Fensterangabe im Berichtskopf übereinstimmt.
- Das Rate-Limit zählt offenbar **je Symbol, nicht je Anfrage**. 429 kam bei rund 39
  abgefragten Symbolen, obwohl die Doku 40 Abrufe je Minute nennt. Der Code hält sich
  jetzt an den `Retry-After`-Kopf und fragt nach einem gescheiterten Sammelabruf
  einzeln nach.

## Die Kern-Diagnose (E26, weiterhin gültig)

Die Engine ist im Mittel nur mit **29 % des Kapitals** investiert und an **58 % der
Tage gar nicht**. Die niedrige Aufwärts-Beteiligung ist deshalb Arithmetik, kein
Defekt — und die Kehrseite (Abwärts) kommt aus derselben Quelle. Wer die
Aufwärts-Beteiligung heben will, muss die Engine länger investiert halten, nicht
ihre Trigger verschärfen.

Daraus folgt eine wiederkehrende Beobachtung: **Alle „schneller-raus"-Schalter haben
Rendite gekostet.** Sie reagieren auf kurzfristigen Order-Flow, ohne den
übergeordneten Rahmen zu kennen — und der ist in der Engine bislang fast leer.

### Nachtrag 13.09.2026: der übergeordnete Rahmen ist gemessen

Die Erklärung oben legte nahe, der fehlende Rahmen sei der Grund — also müsse ein
Rahmen die Sache retten. **Er tut es nicht.** Der Tages-Trend als Filter fällt mit
−0,4 % gegen +30,9 % durch, die Ampel misst gar nichts.

Damit steht der Zwischenstand ehrlich so da: **Zwölf Filter wurden gemessen, zwölf
waren schlechter.** Neun aus dem Order-Flow, zwei aus dem Trend, einer aus der Ampel.
Die Engine wird nicht besser, indem man ihr Bedingungen hinzufügt — in keiner der
bisher versuchten Formen. Was gewirkt hat, waren immer Mechanismen, die die Engine
**länger und größer investiert** halten (Kaufleiter, Flush-Einstieg), nie solche, die
sie zurückhalten.

Das deckt sich mit der Kern-Diagnose: Wer die Aufwärts-Beteiligung heben will, muss
die Engine länger investiert halten, nicht ihre Trigger verschärfen. Die Filter-Idee
ist damit nicht „noch nicht gut genug umgesetzt", sondern **gegen die Diagnose
gerichtet**.

## Was Furkan am 13.09.2026 tatsächlich tut — belegt, nicht geraten

Quelle: `Videos\260913\260913.txt`, Transkript des Sonntags-Updates vom 13.09.2026.
Zeitmarken in Klammern; alles in Anführungszeichen ist wörtlich.

**Seine Position (15:20):** „meine Position bei 59 000 geöffnet, mehrere Gewinne schon
realisiert, das letzte Mal über 80.000 US-Dollar. Ich suche natürlich jetzt nach
Einstiegen, um diese Position wieder hochzuskalieren."

**Sein Risikomanagement (17:34–17:57)** — und das ist der eigentliche Unterschied zur
Engine:

- „Gewinne sind schon realisiert und ich werde da jetzt kein großes Risiko eingehen."
- „Auch wenn ich die Position … unter dem Range Low wieder hochskalieren würde, würde
  ich es nicht so stark machen, dass ich … meine gesamten Gewinne … wieder auf den
  Tisch werfe."
- „egal, wie weit ich ihn nach oben ziehe, **mein Stop wird auf jeden Fall wieder
  drüber kommen, sodass die Gesamtposition hier nicht mehr in Verlust gehen kann**."

Sein Nachkauf ist damit **kein Einstieg mit Kapitalrisiko**. Er stockt eine Position
auf, deren Stop *über* dem Durchschnittseinstand liegt; im schlechtesten Fall verliert
er einen Teil bereits realisierter Gewinne. Die Engine bewertet jeden Einstieg so, als
wäre es der erste. Sie kennt keinen Zustand „Einstand 59 000, Stop im Plus, Nachlegen
kostet kein Kapital".

**Die frühere „zwei Bücher"-Erklärung (Spot gegen Futures) ist damit gegenstandslos.**
Kaisers Einwand war richtig: Es ist derselbe Markt. Der Unterschied ist nicht das Buch,
sondern **der Zustand der Position**.

### Drei Dinge, die er anschaut und die Engine nicht hat

1. **Eine Liquiditätskarte aus *offenen* Clustern** (15:04, 16:00–16:37). Er nennt:
   unter 76 000 (Longs), darüber 77 800 und 78 500, im Wochenchart 80 000 (Shorts).
   Daraus baut er einen Pfad: „erst … diese Liquidierung unter dem Range Low rausnehmen
   und dann vielleicht noch mal über die 80.000 kommen und die Shortpo[sitionen] dann
   liquidieren."

   *Korrektur an der ersten Fassung dieses Absatzes (20.09.2026): Dort stand, die
   Engine kenne Liquidationen nur rückblickend als Auslöser. **Das ist falsch.**
   `liq_entry: boost` ist seit E10.3 live geschaltet und benutzt Liquidations-Niveaus
   als Einstiegszone (`liq_levels`, `in_liq_zone`).*

   Der echte Unterschied ist ein anderer und schmaler: `liq_levels()` baut die Niveaus
   aus **bereits gelaufenen** Kaskaden — „Preisniveaus, an denen historisch
   außergewöhnlich viel liquidiert wurde". Furkan schaut auf **noch nicht ausgelöste**
   Cluster, also auf die geschätzten Liquidationspreise *aktuell offener* Positionen
   (Hyblock-Heatmap). Vergangenes Ereignis gegen ruhende Liquidität. Beides kann am
   selben Preis liegen, aber es ist nicht dieselbe Größe.
2. **Eine Bewertungsebene** (17:22): „die Kostbasis der kurzfristigen Investoren lag
   zuletzt ja bei ungefähr 71 000 US-Dollar" — neben Golden Pocket (69–70 k) und der
   50er-Marke (72 k). Das ist die STH-Kostenbasis aus der On-Chain-Ebene; in der Engine
   gibt es sie nicht. (Die Notiz „keine freie Datenquelle gefunden" in
   `OFFENE-PUNKTE.md` war falsch — checkonchain.com ist kostenlos.)
3. **Eine Ursachenfrage statt einer Schwelle** (16:59–17:15). Er setzt ausdrücklich
   **keine** Limit-Order: „Ich würde da auch in Echtzeit schauen wollen, warum fallen
   wir hier runter? Ist es wirklich, weil Spot verkauft wird, oder … einfach um kurz
   Liquidität zu fischen[?] Sehen wir dann direkt eine Reaktion[?]" Seine
   Entscheidungsregel ist keine Schwelle, sondern eine Frage mit zwei Antworten —
   echter Spot-Verkauf oder Abholen von Liquidität — und die Probe darauf ist die
   **Reaktion danach**. Die Engine hat keinen Begriff von „was passierte in den
   Minuten danach".

### Dieselbe Beobachtung, entgegengesetzte Lesart

(15:44) „Gerade werden sehr viele Short Positionen auch aufgemacht. Es wurden zwar Long
Position[en] jetzt liquidiert in der Bewegung, aber wie wir hier am CVD sehen,
aggressive Short Position[en]."

Das ist genau die Konstellation, die `classify_pattern` als **Muster 5 (ungesunder
Abverkauf)** führt. Furkan liest dieselbe Lage zusätzlich als **Treibstoff**: die neuen
Shorts sind die Liquidität, die den Kurs später nach oben zieht (Ziel 80 000). Beide
Lesarten widersprechen sich nicht — er ist an diesem Tag selbst „ein bisschen
vorsichtiger" und kauft nicht.

**Nachgesehen, was Muster 5 heute wirklich bewirkt: nichts.** Der einzige Schalter, der
daran hängt, ist `block_unhealthy` — und der steht Default aus, weil er in E13 Rendite
gekostet hat. Muster 5 erscheint nur noch in der Lagezeile (`MUSTER_KLARTEXT`) und in
`_AMPEL_DAGEGEN`, und die Ampel ist seit E34 ebenfalls reine Anzeige. **Die Bremse
zieht also gar nicht.** Was in der Telegram-Nachricht „ungesunder Abverkauf" heißt,
klingt nach Warnung, ändert aber am Verhalten der Engine keine einzige Entscheidung.
Das ist eine Lücke zwischen Anzeige und Verhalten, unabhängig von allem Weiteren.

**Die Treibstoff-Lesart ist nie gemessen worden — und es gibt eine exakte Vorlage
dafür, dass so ein Umbau wirken kann.** Bei Muster 4 wurde genau dieser Schritt schon
gemacht: Der Codekommentar sagt „Kapitulation ist in Furkans Methode kein Warnzeichen,
sondern die Einstiegslage - deshalb steht live `flush_entry='core'`". Vor E9.1 (ohne
echte Liquidationsdaten) war `off` besser; mit ihnen drehte das Ergebnis. Muster 5 ist
heute in derselben Lage, in der Muster 4 vor E9.1 war: benannt, angezeigt, ohne Wirkung.

### Ausdrücklich nicht belegt

- **In diesem Video ist der Nachkauf noch nicht passiert.** Er sucht ihn: „Ich habe
  aber tatsächlich keine Limit Order jetzt hier reingesetzt." Ob und wo er ihn
  ausgeführt hat, steht in diesem Transkript nicht.
- **Nichts davon ist gemessen.** Das sind Beobachtungen aus einer Quelle, keine
  Backtest-Ergebnisse. Punkt 1 und 2 wären grundsätzlich messbar; Punkt 3 ist im
  4-Stunden-Takt der Engine strukturell nicht abbildbar.

## E38.1 gemessen (20.09.2026): Muster 5 stützt die Treibstoff-Lesart — kurzfristig

Fenster 12.01.–20.09.2026, 2441 Kerzen, 1506 OI-Punkte. Gemessen wurde für jedes
Kompass-Muster der Kursnachlauf nach 1, 2 und 4 Tagen, jeweils mit dem Abstand zur
Grundrate über alle 1482 bewerteten Kerzen.

| Muster | Episoden | 1 Tag | 2 Tage | 4 Tage |
|---|---:|---|---|---|
| **ALLE (Grundrate)** | — | +0,01 %, 50 % höher | −0,06 %, 49 % | −0,26 %, 47 % |
| **UNGESUNDER_ABVERKAUF (5)** | 26 | **+1,04 % (+1,03), 76 %** | **+0,96 % (+1,02), 71 %** | −0,50 % (−0,24), 42 % |
| CAPITULATION_RESET (4) | 15 | **−1,61 % (−1,61), 33 %** | −1,45 % (−1,39), 33 % | −0,40 % (−0,14), 43 % |
| SHORT_COVERING (3) | 46 | −0,40 % (−0,41), 36 % | −0,15 % (−0,09), 47 % | −0,28 % (−0,02), 48 % |
| DERIVATE_PUMP (2) | 45 | +0,07 % (+0,07), 51 % | −0,12 % (−0,06), 47 % | +0,33 % (+0,59), 54 % |
| GESUNDER_TREND (1) | 97 | −0,06 % (−0,07), 49 % | −0,15 % (−0,09), 49 % | −0,16 % (+0,10), 47 % |

**Muster 5 ist die stärkste Zeile im Feld** — auf 1 bis 2 Tage, und nur dort. Bei 26
unabhängigen Episoden liegt die Zufallswahrscheinlichkeit für 76 % bei etwa 0,5 %. Der
Befund wurde vorab benannt (der Bauplan stand, bevor die Zahlen da waren), leidet also
nicht unter dem Mehrfachvergleich über 18 Tabellenzellen — bei nachträglicher Auswahl
wären es rund 8 %. Nach 4 Tagen dreht der Wert unter die Grundrate: **ein
kurzfristiges Signal, kein Regime.**

### Die wichtigste Zeile ist eine andere — und sie ist eine Warnung

**`CAPITULATION_RESET` hat den schlechtesten Nachlauf im ganzen Feld** (−1,61 Punkte
gegen die Grundrate, nur 33 % der Fälle höher). Und genau auf dieses Muster kauft die
Engine **live**: `flush_entry: core` ist seit E9.1 an und war der Hebel, der die
Rendite getragen hat.

**Wer nach dieser Tabelle handeln würde, müsste `flush_entry` abschalten — und das
wäre nachweislich falsch.**

Der Grund ist strukturell: Die Engine kauft nicht *zum Musterzeitpunkt*, sondern an der
Fib-Zone, mit Stop. Der Nachlauf ab Mustererkennung und der Ertrag ab Einstiegspreis
sind zwei verschiedene Größen. Bei Muster 4 fällt der Kurs nach der Erkennung weiter —
genau deshalb wird die Zone überhaupt erreicht, und die Erholung danach ist der Gewinn.

**Übertragbar, und teuer, wenn man es vergisst:** Ein Nachlauf-Median ist ein Hinweis,
wo man suchen soll, und niemals ein Beleg, dass ein Schalter verdient. Die Engine hat
denselben Beweis bereits im Bestand — man muss ihn nur lesen. *(Das steht auch im
Bericht selbst, damit es beim nächsten Lesen nicht wieder auffällt wie neu.)*

### Was daraus für den Bau folgt

Der kurze Horizont spricht **gegen** E38.2 (Muster 5 als Einstieg, analog `flush_entry`)
und **für** E38.3 (bei Muster 5 Teilverkäufe kurz aussetzen). Ein Signal, dessen Wirkung
nach zwei Tagen verschwunden ist, passt nicht zu einer Kaufleiter über Tage — wohl aber
zu der Frage, ob man *heute* verkaufen muss. Gemessen wird trotzdem beides: Die
Vermutung ist eine Vermutung.

### Nachgeholt am 21.09.2026: die Auswertung je Episode

Jede der 26 Episoden nur einmal gezählt (erste Kerze): 1 Tag **+1,20** über der
Grundrate, 77 % höher · 2 Tage +1,17, 69 % · 4 Tage **+1,24**, 58 %. Die Überlappung
hat nichts aufgeblasen — der Befund wird stärker, und auf 4 Tage dreht er ins Positive.
**Die erste Kerze einer Muster-5-Phase ist der beste Zeitpunkt**, spätere sind
schlechter.

## E38 entschieden (21.09.2026): Das Signal ist echt, die Engine kann es nicht benutzen

Alle drei Schalter und die Gegenprobe wurden gegen die Live-Zeile gemessen (je genau
ein Unterschied). **Alle bleiben aus.** `muster5_halten` griff nie, `muster5_entry`
fünfmal (+1,4 Punkte, nur in Hälfte 2), die Bremse einmal. Zahlen:
`docs\PLAN-E38-MUSTER5.md`.

**Der Grund ist strukturell:** Die Engine entscheidet ausschließlich an Fib-Zonen.
Diese fielen in acht Monaten fünfmal mit Muster 5 zusammen (Einstiege) und nie
(Teilverkäufe). Ein gutes Signal, das fast nie auf einen Entscheidungszeitpunkt trifft,
kann den Ertrag nicht bewegen — in keine Richtung.

**Damit ist die Ausgangsfrage zum ersten Mal gemessen beantwortet.** *„Was sieht
Furkan, was wir nicht sehen?"* — **Er handelt auf dem Order-Flow selbst, als
Zeitsignal. Die Engine benutzt den Order-Flow nur als Bestätigung an Preisniveaus.**

**Übertragbar, und es erklärt rückblickend einiges:** Ein Order-Flow-Schalter kann in
dieser Engine nur so viel bewirken, wie oft der Order-Flow-Zustand auf eine Fib-Zone
trifft. Bevor der nächste Order-Flow-Schalter gebaut wird, lohnt die billige Vorfrage:
*Wie oft fällt der Zustand überhaupt mit einem Entscheidungszeitpunkt zusammen?* Bei
`muster5_halten` hätte sie den Bau erspart.

**Ausdrücklich nicht entschieden:** ob ein zonenfreier Muster-5-Einstieg als eigenes,
kurzfristiges System (1–4 Tage, eigener Stop) gebaut werden soll. Die Einwände stehen
im Plan: Nachlauf ist nicht Ertrag, ~1 % Median nach Gebühren ohne Stop-Logik, 26
Ereignisse in acht Monaten.

## E39 gemessen (21.09.2026): Was passiert nach einem Stop?

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

Plan und Einzelheiten: `docs\PLAN-E39-E40.md`.

## E41 gemessen und live (21.09.2026): Stop mit Rückeroberung

Alle drei lockeren Stop-Varianten bestehen die vorab festgelegte Regel (Puffer 0,5 %,
Rückeroberung 1 und 3 Kerzen), die strengere Gegenprobe (Stop beim Docht) fällt durch.
Kaisers Rückeroberungs-Regel (B1): +26,4 % gegen +23,5 %, Rückgang −10,3 % gegen −9,4 %,
9 statt 10 Stops. **Einschränkungen:** In Hälfte 2 ist B1 nur 0,2 Punkte besser — im
Rauschen, und die Regel hatte keine Rauschgrenze (Mangel der Regel, nicht des
Ergebnisses). Der Rückgang liegt 0,9 Punkte schlechter, knapp an der Toleranz von 1,0.
**Entschieden (Kaiser, 21.09.2026): B1 live.** Die Ausschalt-Regel stand vor der ersten Messung danach fest und hat — anders als die Einschalt-Regel — eine Rauschgrenze: aus, wenn der alte Stop in **beiden** Hälften um mindestens 1 Punkt besser ist oder der Rückgang live um mehr als 1 Punkt tiefer liegt. Der Rückgang lag beim Einschalten 0,1 Punkte unter dieser Grenze — ein Anschlagen bald wäre kein Fehler, sondern die Regel.
Einzelheiten: `docs\PLAN-E41-STOP.md`.

### Nachmessung 23.09.2026: die Regel schlägt an — und überstimmt wird sie ausdrücklich

Zwei Tage mehr Daten (Fenster 15.01.–23.09.), ein Stop mehr: live +25,2 % gegen +22,6 %,
Hälfte 1 +20,0 gegen +17,8, Hälfte 2 +4,3 gegen +4,1 — aber **Rückgang −10,9 gegen
−9,4 %**, also 1,5 Punkte tiefer bei einer Toleranz von 1,0. Der Bericht meldet
AUSSCHALTEN; Kaiser lässt an und prüft beim nächsten Lauf neu. Die Begründung, die
Gegenargumente und die Kosten dieser Entscheidung stehen im Plan.

**Die neue Lehre — und sie betrifft nicht nur E41:** Der Satz „belastbar ist der maximale
Rückgang" gilt für **eine** Variante über die Zeit, **nicht** für den Vergleich zweier
Varianten. Beleg aus demselben Lauf: B3 wartet **länger** als B1 (bis zu drei Kerzen
statt einer) und zeigt trotzdem einen **flacheren** Rückgang (−10,4 gegen −10,9 %). Mehr
Warten kann in der Wartephase nur tiefer werden — der Unterschied entsteht also erst
danach, weil eine anders beendete Position alle folgenden Einstiege verschiebt. Wer zwei
Varianten am Fenster-Rückgang misst, misst Risiko **und** Pfadzufall. Ein
pfadunabhängiges Maß je Position ist als E41.6 vorgeschlagen, aber nicht gebaut.

**Warum nicht B3 mit drei Kerzen?** Weil es vorab als Robustheitsprüfung festgelegt war;
weil der Vorsprung die eigene Rauschgrenze nicht hält (Hälfte 2 nur +0,2 Punkte, in
beiden Läufen); weil B3 **keine Position mehr rettet** als B1 (9 Stops wie B1, der alte
Stop hat 10 — derselbe eine ausgelassene Stop); und weil drei Kerzen sich auf den nie
eigens gemessenen harten Boden aus E9.3 stützen würden. Für einen späteren Wechsel steht
jetzt eine vorab festgelegte Regel im Plan.

**Lehre für künftige Entscheidungsregeln:** „besser in beiden Hälften" braucht eine
Mindestspanne. Das Projekt kennt die Größenordnung des Rauschens (06.09.: ein Tag mehr
Daten dreht 1,0 Punkte) — sie gehört in jede Regel, die vor einer Messung festgelegt
wird. Ebenso ein Abgleich zweier Datenquellen: „bester Versatz ≠ 0" ohne Mindestabstand
schlägt bei einer träge laufenden Reihe schon bei 0,01 Punkten an (E40.1).
