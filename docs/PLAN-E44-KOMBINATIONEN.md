# Bauplan E44 — Welche Schalter und Indikatoren gehören zusammen?

> **Status: E44.1 und E44.2 in `main`** (26.09.2026, siehe 9a). Handelsverhalten unverändert.
> Grundlage: Backtest-Lauf vom 26.09.2026 15:18 UTC (`BACKTEST.md`, Fenster 18.01.–26.09.2026,
> 78 Gitterzeilen) und die Signalliste der Live-Einstellung (`site/data/backtest_signals.json`).
> Keine neue Messung, alle Zahlen unten sind aus diesen beiden Dateien nachgezählt.

## Auftrag

Kaiser, 26.09.2026: *„all diese Dutzenden Tests [wurden] alle nacheinander gemacht und man
hat die Testergebnisse dann immer mit den vorherigen Ergebnissen verglichen. Ich möchte,
dass du tiefgründig analysierst, welche dieser Tests und Indikatoren miteinander kombiniert
und getestet werden können. Um am Ende mehr Rendite rauszuholen […] Insbesondere beachte
Furkans Strategien.“*

## Kurzfassung

1. **Die Beobachtung stimmt.** Das Projekt hat Schalter fast immer einzeln gegen die
   jeweilige Live-Zeile gemessen („genau ein Unterschied“). Das schützt vor Selbsttäuschung,
   übersieht aber Paare, die nur **zusammen** wirken.
2. **Es gibt trotzdem schon Kombinationsdaten.** 16 Vierergruppen im heutigen Gitter sind
   zufällig saubere 2×2-Versuche (Basis, A, B, A+B im selben Lauf). Sie zeigen vier klare Regeln:
   **zwei Filter zusammen schaden sich stark** (bis −10 Punkte über die Summe hinaus),
   **zwei Verkaufsregeln zusammen schaden**, **zwei Einstiegs-Verstärker addieren sich**
   und **eine Ergänzung (der eine Schalter schafft den Zustand, den der andere braucht)
   bringt bis +14 Punkte**.
3. **Indikatoren als Einstiegs-Filter zu kombinieren, ist die am häufigsten gemessene
   Sackgasse des Projekts.** Die Ampel, `strict_confirm` (CVD UND Funding), Muster 5 als
   Sperre und die Aggregation sind alle schon Indikator-Kombinationen, und alle waren
   schlechter. Vier Filter, die einzeln teils besser aussahen, kosteten zusammen 6 Punkte,
   statt die erwarteten knapp 10 zu bringen.
4. **Die Rendite geht heute an einer anderen Stelle verloren**: in den großen Anstiegen.
   Nach 7 von 9 Rest-Verkäufen kam der nächste Kauf tiefer, der Verkauf war also richtig.
   Die zwei Ausnahmen (April +5,4 %, August +14,4 %) sind genau die verpassten Rallys.
   Die Engine hat keinen Weg, in einen laufenden Anstieg zurückzukehren.
5. **Der beste Kandidat ist deshalb eine Ergänzung, kein Filter:** Kaisers Regel
   „Ausbruch mit Rücktest“ (E42) als Partner des live geschalteten `high_exit`. Dazu zwei
   Begleiter, die zu Furkans Aussagen passen, und eine vorab festgelegte Messung mit
   8 Zeilen statt 2³⁰ Möglichkeiten.

---

## 1. Warum „einer nach dem anderen“ etwas übersehen kann

Das Vorgehen bisher war: Schalter X gegen die Live-Zeile messen, ist er in beiden
Fensterhälften besser, wird er live, und die nächste Messung läuft gegen die neue Basis.
Fachlich ist das eine **Koordinatensuche**: Man ändert immer nur eine Stellschraube.
Sie findet zuverlässig Einzelverbesserungen, übersieht aber zwei Fälle:

- **A allein schadet, B allein schadet, A+B zusammen hilft.** Beispiel aus diesem Projekt:
  `rest_halten` allein kostete 11,6 Punkte, weil der liegende Rest jeden neuen Einstieg
  blockierte. Erst mit `neustart_mit_rest` wurde er brauchbar (Abschnitt 2, Zeile 5).
- **A allein hilft, B allein hilft, A+B zusammen schadet.** Beispiel: Sperrfrist 48 h und
  Mindest-Stopabstand, einzeln +3,7 und +4,6 Punkte, zusammen −1,9 (Zeile 2).

Die Gegenseite gilt genauso und ist der Grund für die Regel „genau ein Unterschied“:
**Wer viele Kombinationen misst, findet immer eine, die zufällig gut aussieht.** 30
Ein/Aus-Schalter ergeben über eine Milliarde Kombinationen. Bei 8 Monaten Daten, 21
abgeschlossenen Positionen und 9 Stops wäre die beste davon fast sicher Zufall. Die Antwort
ist deshalb nicht „alles mit allem“, sondern **wenige Kombinationen mit einer Begründung,
vorab festgelegt**.

## 2. Was die vorhandenen Kombinationen zeigen

Alle Zeilen stammen aus **demselben** Backtest-Lauf (26.09.2026), gleiches Fenster, gleiche
Daten. Jede Vierergruppe unterscheidet sich in genau zwei benannten Schaltern. Die meisten
stehen auf einer **älteren** Basis als heute live; die absoluten Zahlen entscheiden also
nichts, das Muster schon.

**Wechselwirkung** = (A+B) − (A) − (B) + (Basis). Null heißt: Die Wirkungen addieren sich
einfach. Positiv heißt: Zusammen besser als die Summe. Negativ heißt: Zusammen schlechter.

| # | Paar | Art | Basis | +A | +B | +A+B | Wechselwirkung gesamt | H1 | H2 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | Kaufleiter × Flush-Einstieg | zwei Einstiegs-Verstärker | +9,4 | +14,6 | +19,3 | +23,8 | **−0,7** | −0,4 | 0,0 |
| 2 | Sperrfrist 48 h × Mindest-Stopabstand 2 % | zwei Filter | +22,1 | +25,8 | +26,7 | +20,2 | **−10,2** | −3,3 | −1,7 |
| 3 | Ziele festhalten × Mindest-Bein 5 % | zwei Einschränkungen | +26,6 | +26,0 | +23,4 | +14,6 | **−8,2** | −6,0 | −1,8 |
| 4 | Verkauf am Hoch × Verkauf an Liq-Niveaus | zwei Verkaufsregeln | +29,4 | +30,7 | +24,0 | +21,7 | **−3,6** | −3,9 | +0,6 |
| 5 | Rest halten × Neustart mit Rest | Ergänzung | +25,4 | +13,8 | +25,5 | +27,6 | **+13,7** | +12,9 | −0,4 |
| 6 | Mindest-Bein 5 % × Bein in Handelsrichtung | Ergänzung | +30,7 | +25,4 | +27,7 | +32,1 | **+9,7** | +3,4 | +5,2 |
| 7 | Liq-Konfluenz × Mindest-Stopabstand | Verstärker × Filter | +22,1 | +23,4 | +26,7 | +29,4 | +1,4 | −0,6 | +1,8 |
| 8 | Rest-Freigabe × Stop nachziehen | zwei Lösungen desselben Problems | +23,8 | +16,4 | +22,1 | +16,9 | +2,2 | +1,3 | +0,8 |

Dazu die Viererzeile „alle vier neuen Hebel“ (Warnlicht, Flow-Prüfung am 0.5-Level,
Sperrfrist 48 h, Mindest-Stopabstand) auf der Basis +22,1 %: einzeln −1,3 / +2,6 / +3,7 /
+4,6 Punkte. Addiert wären das **+31,7 %**, gemessen sind es **+16,1 %**.

**Die vier Regeln, die daraus folgen:**

1. **Filter plus Filter schadet, und zwar mehr als die Summe** (Zeilen 2, 3 und die Viererzeile).
   Jeder Filter streicht Einstiege, zwei Filter streichen oft *verschiedene*, und die
   Engine bleibt noch länger draußen. Das ist die Kern-Diagnose in
   verschärfter Form: Die Engine ist ohnehin zu wenig investiert.
2. **Zwei Verkaufsregeln zusammen schaden** (Zeile 4). Die zweite verkauft, was die erste
   hätte laufen lassen.
3. **Zwei Einstiegs-Verstärker addieren sich** (Zeile 1). Kaufleiter und Flush sind die
   beiden größten Renditebringer des Projekts. Zusammen bringen sie fast exakt die Summe.
4. **Echte Gewinne aus Kombinationen kommen nur aus Ergänzungen** (Zeilen 5 und 6): Der eine
   Schalter schafft einen Zustand, ohne den der andere nicht funktioniert. `rest_halten`
   braucht `neustart_mit_rest`, sonst blockiert der Rest. `bein_richtung: bias` braucht
   `min_bein_pct`, sonst wählt es zu kleine Beine. **Zeile 6 trägt als einzige Ergänzung in
   beiden Hälften**, und genau diese Kombination ist seit heute live (E43.2).

Zeile 8 ist kein Gewinn, obwohl die Zahl positiv ist: Beide Schalter lösen dasselbe
Problem, jeder kostet allein. Zusammen kosten sie weniger als die Summe, weil der zweite
nichts mehr zu tun hat. Eine **Doppelung** erkennt man daran, dass A+B kaum anders ist als
der schwächere Einzelwert.

**Folgerung für die Suche:** Nicht Filter kombinieren, sondern zu jedem Mechanismus fragen:
*Welchen Zustand braucht er, den heute niemand herstellt?* Oder umgekehrt: *Welcher
live geschaltete Mechanismus hinterlässt einen Zustand, den niemand auflöst?*

## 3. Wo die Rendite heute verloren geht

Nachgerechnet aus den 244 Signalen der Live-Einstellung (`backtest_signals.json`), mit
derselben Tranchen-Rechnung wie `simulate()`. Kontrolle: Der Nachbau endet bei 13.509 €,
der Bericht bei 13.532 €. Die Differenz kommt davon, dass der Nachbau zum letzten
Signalpreis bewertet, nicht zum letzten Schlusskurs. Die Zeitanteile sind zu Signalpreisen
gerechnet, also eine Näherung.

| Kennzahl | Wert |
|---|---:|
| Rendite / max. Rückgang / Buy & Hold im Fenster | +35,3 % / −9,9 % / −10,3 % |
| Positionen | 22 (21 abgeschlossen, 1 offen seit 23.09.) |
| Zeit mit offener Position | **50 %** |
| Zeitgewichteter investierter Anteil | **35 %** |
| Höchster investierter Anteil je Position (Median) | 100 % |
| Haltedauer je Position (Median / längste) | 4 Tage / 22 Tage |
| Positionsende durch Stop / Rest-Verkauf bei Gegen-Muster / letzten Teilgewinn | 9 / 9 / 3 |

**Die Engine ist nicht zu vorsichtig beim Einstieg.** In einer Position geht sie fast immer
auf 100 %. Sie ist aber nur die Hälfte der Zeit in einer Position, und die dauert im Median
vier Tage.

**Was nach einem vollständigen Ausstieg passiert** (nächster Kauf, Preis gegen den
Ausstiegspreis):

| Ausstieg durch | Fälle | nächster Kauf tiefer | nächster Kauf höher |
|---|---:|---|---|
| Rest-Verkauf bei Gegen-Muster (Muster 2 oder 3) | 9 | **7** (−1,3 bis −4,4 %) | **2: 07.04. +5,4 % (10,7 Tage flach), 19.08. +14,4 % (6,3 Tage flach)** |
| letzter Teilgewinn | 3 | 2 | 1 (+1,7 %) |
| Stop | 9 | 4, davon **2 große Abwärtsphasen**: 20.01. −25,2 % (21,7 Tage flach), 17.05. −20,9 % (23,8 Tage flach) | 5 (+0,1 bis +4,2 %) |

Drei Schlüsse:

1. **Die Stops arbeiten.** Sie haben die Engine aus beiden großen Abwärtsphasen des Fensters
   herausgehalten. Bei nur 9 Stops hat jede Stop-Änderung zudem kaum Messkraft (E39).
   Hier liegt kein Hebel.
2. **Der Rest-Verkauf bei Gegen-Muster ist meistens richtig** (7 von 9). Ihn abzuschalten
   (`rest_halten`) gibt diese 7 guten Ausstiege mit her. Deshalb kostet `rest_halten` in
   Hälfte 1 4,3 Punkte und bringt in Hälfte 2 3,2 (E43.6).
3. **Die zwei Fehlgriffe sind die zwei Rallys.** Im August stieg Bitcoin um 24,9 %, die
   Engine um 2,4 %: Rest-Verkauf am 19.08. bei 68.554, nächster Kauf erst am 25.08. bei
   78.409. Die Engine kauft nur in Rücksetzern an Fib-Zonen. Läuft der Kurs ohne tiefen
   Rücksetzer weiter, kommt sie nicht mehr hinein.

**Genau das, und nur das, soll eine Kombination reparieren:** die 7 guten Rest-Verkäufe
behalten und nur in den Rallys wieder einsteigen.

## 4. Was Furkan dazu sagt

Belegt aus den bereits ausgewerteten Videos, mit Zeitmarken aus `docs/STRATEGIE.md`, den
`docs/FURKAN-UPDATE-*.md` und der Gesamtprüfung Teil B. Die Rohabschriften unter `Videos\`
im Backup-Repo waren in dieser Sitzung nicht lesbar (Rechte-Prüfung der Arbeitsumgebung).
Siehe „Offene Fragen“.

| Furkan | Quelle | Was es für Kombinationen heißt |
|---|---|---|
| „Nie all out“, er hält seit Juli **eine** Position | Tutorial 18:00; Prüfung B12 | Die Engine steigt bei jedem Rest-Verkauf ganz aus. Widerspruch bekannt (E21) |
| Das Hoch ist keine Wand, sondern **der Anfang einer Zone**: Er verkauft dort UND noch einmal darüber, „ein bisschen weniger“ | Juli-B 19:14–19:21 | Zwei Dinge: Nach dem Verkauf unter dem Hoch geht es für ihn weiter, und **die Verkaufs-Tranchen werden nach oben kleiner**. Die Engine macht es umgekehrt (40 / 40 / Leiter 15) |
| Kaisers Regel vom 21.09.: Durchbricht der Kurs den Widerstand und hält beim Rücktest (Schluss nicht darunter, höchstens der Docht), „sind weitere Kursgewinne zu erwarten“ | `docs/PLAN-E41-STOP.md` | Das ist der fehlende Rückweg in die Rally. Vorgemerkt als E42 |
| Zuerst Makro-Bias, **dann long ODER short**; alle Muster gelten spiegelbildlich | Tutorial 16:03, 13:28 | Die Engine ist nur long und in Abwärtsphasen flach. Ein Short-Zweig nur im Abwärts-Regime wäre eine Einsatz-Erweiterung, kein Filter |
| Aufstocken mit Gewinnpolster: „mein Stop wird auf jeden Fall wieder drüber kommen“ | 13.09. 17:34–17:57 | Passt zu `neustart_mit_rest` + `trail_stop`. **Kaiser hat den Stop-Teil (E28) am 28.08. bewusst abgelehnt**, deshalb hier nicht vorgeschlagen |
| Zonen sind Wartepositionen, er schaut in Echtzeit, warum der Kurs fällt | 13.09. 16:59 | Mit 4h-Kerzen nicht abbildbar (E32.3). Kein Kombinationsthema |

## 5. Allgemeines Wissen über den Bitcoin-Markt, abgeglichen mit der Engine

Nicht in diesem Projekt gemessen. Es dient nur dazu, Lücken zu finden, nicht als Beleg.

| Bekannte Eigenschaft von BTC | In der Engine? |
|---|---|
| **Kapitulation und Liquidationskaskaden kehren oft kurzfristig um** | Ja: `flush_entry: core` (live), größter Renditehebel |
| **Überhitzte Derivate (Funding hoch, OI steigt ohne Spot) kippen oft** | Ja: Muster 2/3 als Rest-Verkauf, zu 7 von 9 richtig |
| **Kurze Dochte unter Marken (Stop-Jagd), besonders in dünnen Stunden** | Ja: E41 Rückeroberung (live) |
| **Trends halten an (Momentum)**. In der Fachliteratur für Kryptowährungen gut belegt, z. B. Liu & Tsyvinski (2021). In starken Trends bleiben tiefe Rücksetzer aus | **Nein.** Die Engine kauft nur Rücksetzer an Fib-Zonen. Das ist die eine strukturelle Lücke, und sie passt zu Abschnitt 3 |
| Nach sehr ruhigen Phasen folgt oft ein großer Ausschlag (Volatilitäts-Squeeze), Furkan Juli-B 15:00 | Nein. Die Handlung ist aber ungeklärt (Juli-B §4: „erst eine Handlung definieren“) |
| Makro-Lage (US-Aktien, Zinsen) bestimmt die Richtung | Nein, bewusst (Prüfbarkeit, E8.5). Nur als Tages-EMA gemessen, als Filter durchgefallen |

**Ergebnis:** Drei der vier bekannten, handelbaren BTC-Eigenschaften hat die Engine schon,
und sie tragen die Rendite. Die vierte (Momentum, also Trendfortsetzung) fehlt, und genau
dort liegen die zwei verpassten Rallys.

## 6. Die Kandidaten, nach Nutzwert

### K1: E42 „Ausbruch mit Rücktest“, als Partner von `high_exit` (höchster Nutzwert)

**Ergänzung im Sinne von Regel 4:** `high_exit: on` (live) verkauft unter dem letzten
Hoch und hinterlässt einen Zustand, den niemand auflöst: die Engine ist draußen, das Hoch
ist durchbrochen. E42 löst genau diesen Zustand auf.

Regel (aus Kaisers Worten, Werte **vorab** festgelegt, keine Nachjustierung):

- **Wann beobachtet wird:** nach einem Teilverkauf am letzten Hoch (`high_exit`) oder nach
  einem vollständigen Ausstieg durch Teilgewinn oder Rest-Verkauf, nicht nach einem Stop.
- **Marke:** das nächste bestätigte Pivot-Hoch über dem Kurs im Moment dieses Verkaufs,
  also dieselbe Marke, die `high_exit` benutzt (`next_pivot_beyond`).
- **Ausbruch:** eine 4h-Kerze **schließt** über der Marke. Ein Docht allein zählt nicht.
- **Rücktest:** innerhalb der nächsten **12 Kerzen (2 Tage)** berührt das Tief einer Kerze
  die Zone Marke +0,5 % (derselbe Abstand wie `high_exit`), und die Kerze **schließt nicht
  darunter** („höchstens mit dem Docht“).
- **Handlung:** Rückkauf mit **25 %** (Größe von KAUF 1) zum Schluss dieser Kerze. Stop:
  Schluss unter der Marke, mit der live geschalteten Rückeroberung (1 Kerze). Ziele über
  die vorhandene Extension-Logik.
- **Nur, wenn die Engine nicht schon voll investiert ist.** Kein zweiter Rückkauf auf
  dieselbe Marke.
- **Robustheitszeile** (wie B3 bei E41): Rücktest-Fenster 6 statt 12 Kerzen. Sie entscheidet
  nichts, sie zeigt nur, ob das Ergebnis an der Zahl hängt.

**Zustand über Kerzen hinweg:** Marke, Ausbruchszeitpunkt und „schon zurückgekauft“ müssen in
`state.json`, sonst tut der Backtest etwas, das live nie passiert. Prüfweg wie immer:
dieselbe Kursfolge am Stück und Kerze für Kerze, Signale und Telegram-Meldungen gleich.

### K2: Verkaufs-Tranchen nach oben kleiner (Furkan, Juli-B 19:14)

Ein Parameter `verkauf_faktor` (live 1,0; Messwert **0,67**, also ein Drittel weniger je
Teilverkauf). Der Rest wird größer und läuft länger. Das passt zur Kern-Diagnose („was
gewirkt hat, hielt die Engine länger investiert“) und ist **nicht** die sechste Variante
„mehr verkaufen“, die der Wissens-Layer als auserzählt führt, sondern die Gegenrichtung.
Nie gemessen.

### K3: `rest_halten` noch einmal, aber nur als Partner von K1

Einzeln ist `rest_halten` gemessen und aus (E43.6). Mit E42 ändert sich die Frage: Ist ein
gehaltener Rest besser als ein Rückkauf nach Rücktest? Die Daten aus Abschnitt 3 lassen
erwarten, dass K1 allein besser ist, weil er die 7 guten Rest-Verkäufe behält. Die Zeile
wird **zum Verstehen** mitgemessen, nicht zum Entscheiden.

### K4: Shorts nur im Abwärts-Regime (Furkans Makro-Stufe), Kaisers Entscheidung zuerst

`bias_short: "regime"`: Shorts nur, wenn der Tagesschluss unter dem Tages-EMA200 liegt,
Longs unverändert. Das ist **kein dreizehnter Filter**, denn es streicht keinen einzigen
heutigen Einstieg. Es gibt der Engine etwas zu tun in der Hälfte der Zeit, in der sie
flach ist. Gründe dagegen, ehrlich: Mechanische Shorts haben in jeder bisherigen Messung
verloren („Long+Short“ heute −4,0 %). E33 hat gezeigt, dass ein Tages-EMA kein
Makro-Bias ist. Das Fenster ist überwiegend fallend, was einen Short-Zweig schönrechnen
kann. **Nur bauen, wenn Kaiser überhaupt Short-Signale per Telegram bekommen will.**

### K5: Infrastruktur, damit Kombinationen überhaupt belastbar messbar werden

- **Coinalyze-Daten archivieren** (E9.6 Punkt 5, seit Juli offen). Coinalyze hält nur rund
  1.500 bis 2.000 4h-Werte vor, deshalb **wandert** das Fenster: im Juli begann es am
  18.11.2025, heute am 18.01.2026. Werden die Daten täglich ins Repo geschrieben, **wächst**
  es stattdessen um einen Monat pro Monat. Jede Kombinationsmessung wird dadurch mit der
  Zeit belastbarer, ohne dass jemand etwas tun muss. Billig und rein technisch.
- **Wechselwirkungs-Tabelle automatisch im Bericht** (Abschnitt 2 als Code), damit jede
  künftige 2×2-Messung ihre Wechselwirkung selbst ausweist.
- **Monats-Probe** für die Entscheidungsregel: Der Vorsprung muss positiv bleiben, wenn
  man einen einzelnen Monat weglässt, egal welchen. Die Monatswerte liefert `simulate()`
  schon. Das fängt den Fall `neustart_mit_rest` ab, dessen 2,1 Punkte aus zwei Ereignissen
  stammten.

## 7. Bewusst NICHT

- **Keine Filter-Kombinationen.** Regel 1 aus Abschnitt 2 ist gemessen: zwei Filter schaden
  mehr als die Summe. Kein dreizehnter Filter, auch nicht aus mehreren Indikatoren.
- **Kein Gitter „alles mit allem“.** 2³⁰ Kombinationen bei 21 Positionen sind Zufallssuche.
- **Keine „Rendite über Einsatz“ als Strategie.** Mehr Einsatz bringt mehr Rendite und im
  selben Verhältnis mehr Rückgang (gemessen 27.07.2026: 100 / 60 / 50 % Einsatz gegen
  +30,0 / +17,9 / +14,8 %). Das ist eine Risikofrage für Kaiser, keine Verbesserung der
  Engine. Dasselbe gilt für Hebel.
- **Nichts an den Stops.** 9 Stops im Fenster, die großen Abwärtsphasen wurden vermieden.
- **Nicht wieder:** `be_im_plus`, Trendfilter, Ampel, 1D-Ebene, Aggregation, Muster 5 als
  Filter, Einsatz unter 100 %.
- **Kein Break-even-Stop nach Aufstockung** (E28). Furkan-belegt, von Kaiser abgelehnt.

## 8. Messdesign und Entscheidungsregel (vor jeder Messung festgelegt)

**Gitter:** alle Kombinationen aus K1, K2 und K3 auf der heutigen Live-Zeile, also 2³ = 8
Zeilen (die Live-Zeile ist eine davon), dazu die Robustheitszeile von K1. K4 läuft
getrennt und nur nach Kaisers Ja.

**Eine Hauptzeile entscheidet, die anderen erklären.** Vorab benannt: **„LIVE-heute +E42“**.
Nur sie kann nach der normalen Regel live gehen. So bleibt die Zahl der Zufallstreffer so
niedrig wie bei jeder Einzelmessung. Zur Einordnung: Im heutigen Gitter besteht **keine**
der 77 übrigen Zeilen die Regel gegen die Live-Zeile.

**Regel für die Hauptzeile** (wie E41, E43.2 bis E43.8, plus Monats-Probe):
1. in **beiden** Fensterhälften mindestens **1 Punkt** besser als live, **und**
2. max. Rückgang nicht mehr als **1 Punkt** tiefer, **und**
3. der Vorsprung bleibt positiv, wenn **ein beliebiger einzelner Monat** weggelassen wird.

**Regel für die übrigen Kombinationszeilen** (strenger, weil sie mehrere sind): beide
Hälften mindestens **2 Punkte** besser, Rückgang wie oben, Monats-Probe wie oben. Und dazu
eine inhaltliche Erklärung aus den Wechselwirkungen, bevor sie Kaiser vorgeschlagen werden.

**Ausschalt-Regel, falls etwas live geht:** wie bei E41. Die alte Einstellung läuft als
Gegenprobe im Bericht weiter. Ausschalten, wenn sie in beiden Hälften mindestens 1 Punkt
besser ist oder der Rückgang live mehr als 1 Punkt tiefer liegt. Der Bericht prüft das
selbst.

## 9. Etappen

| Etappe | Inhalt | Art | Aufwand | Hängt ab von |
|---|---|---|---|---|
| E44.1 | Coinalyze-Archiv: 4h-Werte täglich ins Repo, Backtest liest Archiv + frische Daten | Infrastruktur, kein Handelsverhalten | mittel | — |
| E44.2 | Bericht: Wechselwirkungs-Tabelle und Monats-Probe als Code, mit Tests und Sabotage | Messwerkzeug | mittel | — |
| E44.3 | E42 als Schalter (Default aus), Zustand in `state.json`, Telegram-Text, Tests, Sabotage, Prüfweg am Stück gegen Kerze für Kerze | neuer Mechanismus | **hoch** | Kaisers Ja zu den Werten in K1 |
| E44.4 | `verkauf_faktor` als Parameter (Default 1,0) | kleiner Mechanismus | mittel | — |
| E44.5 | 2³-Gitter + Robustheitszeile, Backtest auf dem Arbeitszweig, Urteil nach Abschnitt 8 | Messung | niedrig | E44.2 bis E44.4 |
| E44.6 | K4 Shorts im Abwärts-Regime | neuer Zweig | hoch | Kaisers Grundsatz-Ja |

E44.1 und E44.2 sind unabhängig und sofort machbar. E44.3 ist der Kern.

## 9a. Status je Etappe und Startpunkt für einen neuen Chat

**Status (wird nach jeder Etappe fortgeschrieben):**

| Etappe | Status |
|---|---|
| E44.1 Coinalyze-Archiv | **GEBAUT** 26.09.2026 auf Zweig `claude/blissful-maxwell-9uwt6x`, 535 Tests, `sabotage_e441.py` 8/8. **IN `main` seit 26.09.2026** (Kaisers Go). Täglicher Anstoß über cron-job.org, Anleitung `ANLEITUNG-PUENKTLICHER-START.md` Schritt 5 (Kaiser richtet ein) |
| E44.2 Wechselwirkungen + Monats-Probe im Bericht | **GEBAUT** 26.09.2026 auf demselben Zweig, 545 Tests, `sabotage_e442.py` 8/8 gefangen. Findet im echten Gitter dieselben 16 Gruppen wie Abschnitt 2. Wirkt erst im nächsten Backtest-Lauf (neuer Berichtsabschnitt „E44“). **IN `main` seit 26.09.2026** (Kaisers Go). Erscheint im nächsten Backtest |
| E44.3 E42 Ausbruch mit Rücktest | **BEREIT ZUM BAU**: Kaiser hat die drei Werte am 26.09.2026 bestätigt (Abschnitt 10) |
| E44.4 `verkauf_faktor` | OFFEN |
| E44.5 2³-Gitter messen | OFFEN, braucht E44.2 bis E44.4 |
| E44.6 Shorts im Abwärts-Regime | OFFEN, **Kaisers Ja am 26.09.2026**. Zuerst eigener Bauplan-Abschnitt (Punkte a und b in Abschnitt 10) |

**So beginnt ein neuer Chat mit einer Etappe (spart Tokens):** Den Kurzprompt aus
`STARTPROMPT.md` nehmen und als `AUFGABE` eine dieser Zeilen einsetzen. Die KI liest dann nur
`00_STAND.md`, den jüngsten Abschnitt von `UEBERGABE.md` und diesen Plan.

- **E44.1:** `E44.1 aus docs\PLAN-E44-KOMBINATIONEN.md fertigstellen (Abschnitt 9b). Zuerst den
  Status in 9a und den juengsten UEBERGABE-Abschnitt lesen, dort steht, was schon gebaut ist.` Aufwand: mittel.
- **E44.2:** `E44.2 aus docs\PLAN-E44-KOMBINATIONEN.md bauen (Abschnitt 9c).` Aufwand: mittel.
- **E44.3:** `E44.3 (E42 Ausbruch mit Ruecktest) aus docs\PLAN-E44-KOMBINATIONEN.md bauen,
  Abschnitt 6 K1, mit meinen Antworten aus Abschnitt 10.` Aufwand: **hoch**.
- **E44.4:** `E44.4 (verkauf_faktor) aus docs\PLAN-E44-KOMBINATIONEN.md bauen, Abschnitt 6 K2.` Aufwand: mittel.
- **E44.5:** `E44.5 aus docs\PLAN-E44-KOMBINATIONEN.md: 2^3-Gitter nach Abschnitt 8 bauen,
  Backtest auf dem Zweig anstossen, Urteil nach der vorab festgelegten Regel.` Aufwand: niedrig bis mittel.
- **E44.6:** nur nach Kaisers Ja, eigener Bauplan-Abschnitt zuerst. Aufwand: hoch.

### 9b. E44.1 im Detail: Coinalyze-Archiv

- **Problem:** Coinalyze liefert nur rund 1.500 bis 2.000 4h-Werte. Das Messfenster wandert
  deshalb nach vorn (Juli: ab 18.11.2025, heute: ab 18.01.2026), ältere Daten gehen verloren.
- **Lösung:** neues Modul `engine/archiv.py`. Es lädt OI, Liquidationen, Futures-Delta und
  Long-Short von Coinalyze, übernimmt **nur abgeschlossene** 4h-Kerzen und mischt sie in
  `site/data/archiv/coinalyze_4h.json`. Neue Werte überschreiben alte zum selben Zeitpunkt,
  alte Zeitpunkte bleiben erhalten. Leeres oder fehlendes Archiv ist kein Fehler.
- **Backtest:** mischt nach dem Coinalyze-Abruf das Archiv dazu (`archiv.zusammen`).
  Solange das Archiv nicht älter ist als Coinalyze, ändert sich **keine Zahl**. Erst wenn
  Coinalyze ältere Werte löscht, die das Archiv noch hat, wird das Fenster länger (bis
  höchstens `START_MS` = 01.09.2025). Der Berichtskopf nennt das Fenster ohnehin.
- **Täglich schreiben:** neuer Workflow `.github/workflows/archiv.yml` (einmal täglich
  plus Knopf), ruft `python3 archiv.py` auf und committet nur die Archivdatei. Die
  Live-Engine (`main.py`) wird **nicht** angefasst.
- **Bewusst NICHT:** kein Eingriff in `main.py` oder `strategy_core.py`, kein neues
  Handelsverhalten, keine Aggregation (nur die Reihen, die der Backtest heute nutzt).
- **Tests:** Mischen (neu gewinnt, alt bleibt), nur abgeschlossene Kerzen, Speichern und
  Laden mit Liquidations-Paaren, fehlende Datei, Backtest ruft das Mischen wirklich auf.
  Sabotage-Probe `sabotage_e441.py`.
- **Falls der Workflow nicht gepusht werden kann** (Workflow-Dateien sind in manchen
  Umgebungen geschützt): Datei steht im Plan, Kaiser legt sie über GitHub von Hand an.

### 9c. E44.2 im Detail: Wechselwirkungen und Monats-Probe im Bericht

- **Wechselwirkungs-Tabelle:** Funktion `e442_vierergruppen(GRID)` findet alle Gruppen
  Basis/A/B/A+B, in denen A und B sich von der Basis in je genau einem, verschiedenen Schalter
  unterscheiden und A+B genau beide Änderungen trägt. `e442_wechselwirkung` rechnet
  (A+B) − A − B + Basis für Gesamt, H1 und H2. Neuer Berichtsabschnitt „E44: Wechselwirkungen“.
  Das ist Abschnitt 2 dieses Plans, als Code.
- **Monats-Probe:** Funktion `monats_probe(monate_live, monate_var)`: Summe der monatlichen
  Renditedifferenzen, und ob sie positiv bleibt, wenn ein beliebiger einzelner Monat
  weggelassen wird. Im Bericht für jede Zeile „LIVE-heute +…“ gegen die Panel-Zeile.
  Sie wird Teil der Entscheidungsregel ab E44.5 (Abschnitt 8).
- **Bewusst NICHT:** keine neue Gitterzeile, kein Schalter, keine Änderung an bestehenden
  Urteilen.
- **Tests:** konstruierte Gitter mit bekannter Wechselwirkung, Gruppen mit zwei Unterschieden
  werden nicht mitgezählt, Monats-Probe kippt bei einem einzelnen Ausreißermonat.
  Sabotage-Probe `sabotage_e442.py`.

## 10. Offene Fragen an Kaiser

**Antworten hier eintragen, sobald Kaiser sie gibt** (Datum und Wortlaut):

- **Frage 1 (E42-Werte), 26.09.2026:** Kaiser: *„E42 verstehe nicht was du von mir willst.“*
  Nach der Erklärung mit Beispiel: **Kaiser 26.09.2026: „1=ja, 2=ja, 3=ja“.** Damit gelten die
  Werte aus K1 unverändert: Rücktest-Fenster 12 Kerzen (2 Tage), Rückkauf 25 %, Stop bei
  Schluss unter der Marke (mit Rückeroberung, 1 Kerze). **E44.3 kann gebaut werden.** Neuer Beleg für die Regel selbst: Furkan 02.08.2026 14:17
  (`wissens-layer/05_quellen/260802_Transkript.txt`): *„die Bestätigung für den Bullenmarkt
  kam dann immer, wenn der Breakout über die Costbasis kam, der Retest und dann ging es halt
  eben halt hoch.“*
- **Frage 2 (Shorts), 26.09.2026:** Kaiser: *„ja ich möchte short signale wenn der markt fällt.
  Ich gehe davon aus, dass alle signale für long dafür genutzt werden, nur in die
  entgegengesetzte richtung.“* **Ja → E44.6 wird gebaut.** Die gespiegelte Short-Logik gibt es
  in der Engine schon (`bias_short`, Signale SHORT_1/SHORT_2/…, Telegram-Texte vorhanden).
  Neu ist nur, **wann** Shorts erlaubt sind: im fallenden Markt (Vorschlag K4: Tagesschluss
  unter Tages-EMA200). Zwei Punkte für den Bauplan-Abschnitt E44.6:
  (a) `bein_richtung: "bias"` (live) wählt das Bein nach der EINEN erlaubten Richtung
  (`main.py`: nur wenn `bias_long != bias_short`). Mit Regime-Shorts muss die Richtung je
  Kerze aus dem Regime kommen, sonst fällt die Bein-Wahl still auf `auto` zurück.
  (b) Furkan warnt 10.09.2026 19:40 davor, nach einem großen Fall noch Shorts aufzubauen
  („ein bisschen spät“). Das ist ein Argument, die Regel nicht nachzuschärfen, bis sie
  gemessen ist, und die Ausschalt-Regel ernst zu nehmen.
- **Frage 3 (Transkripte), 26.09.2026:** Kaiser hat sie in `wissens-layer/05_quellen/`
  abgelegt, Haupttranskript `ORderFLow-Transkript.md`, dazu 260727, 260802, 260803, 260910,
  260913. **Achtung:** Das Repo ist öffentlich, die Arbeitsregeln verbieten vollständige
  Transkripte darin (Hinweis an Kaiser gegeben, Entscheidung bei ihm).

**Frage 1 einfach erklärt (für Kaiser):** Die Engine verkauft heute einen Teil kurz unter
dem letzten Hoch. Beispiel: letztes Hoch 70.000, Verkauf bei 69.650. Steigt der Kurs danach
trotzdem, schließt eine 4h-Kerze bei 70.800 (Ausbruch), fällt zurück bis 70.100 und schließt
wieder darüber (Rücktest gehalten), dann kauft die Engine wieder ein. Dafür braucht sie drei
Zahlen, die vorher festgelegt werden müssen: (1) wie lange sie nach dem Ausbruch auf den
Rücktest wartet (Vorschlag 2 Tage), (2) wie viel sie zurückkauft (Vorschlag 25 % wie der
erste Kauf), (3) wo der Stop liegt (Vorschlag: Schluss wieder unter 70.000). Antwort
„ja“ genügt, oder andere Zahlen.


1. **E42-Werte:** Rücktest-Fenster 2 Tage, Rückkauf 25 %, Stop bei Schluss unter der Marke.
   Passt das zu dem, was du mit „Ausbruch mit Rücktest“ meinst?
2. **Shorts:** Willst du grundsätzlich Short-Signale bekommen, wenn der Markt im
   Abwärts-Regime ist? Ohne dein Ja wird K4 nicht gebaut.
3. **Transkripte:** Die Rohabschriften im Backup-Repo (`Videos\`, `Transkript.md`) konnte
   ich in dieser Sitzung nicht lesen, die Arbeitsumgebung hat den Zugriff blockiert. Die
   Analyse stützt sich auf die ausgewerteten Auszüge in `docs\`. Das Makro-Video vom
   02.08.2026 ist laut Wissens-Layer noch nicht vollständig ausgewertet. Soll ich das
   nachholen, wenn du den Zugriff freigibst?
