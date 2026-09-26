# Offene Punkte

> Stand: 26.09.2026. Nach Nutzwert sortiert, nicht nach Alter.
> Erledigtes wandert hier raus und in die Chronik (`docs\ETAPPENPLAN.md`).
> Kurzstand: `00_STAND.md` · was zuletzt lief: `UEBERGABE.md`.

## NEU 26.09.2026 — aus der Gesamtprüfung (höchster Nutzwert zuerst)

Bericht: `docs\PRUEFUNG-2026-09-26-GESAMT.md` (Teil E). Nichts davon ist gebaut.

1. **A1 Anzeige:** Futures-CVD im Lage-Abruf in $ umrechnen. **Erledigt, live seit 26.09.2026 (E43.1).**
2. **Gitterzeile „LIVE-heute +Bein in Handelsrichtung“** (`bein_richtung: bias`), genau ein
   Unterschied. Kein neuer Code. **Erledigt: gemessen, live seit 26.09.2026 (E43.2).**
3. **A2 als Schalter:** Muster 2 vergleicht Dollar-Beträge statt Anteile an einer
   willkürlichen Summe. Behebt zugleich live ≠ Backtest. **Gebaut und gemessen 26.09.2026
   als E43.3:** nur 2 von 1.504 Kerzen anders, Rendite identisch, bleibt `"alt"`.
4. **A3 als Schalter:** OI durch den Kurs teilen (Kontrakte statt Dollar).
5. **A4:** Test summiert ab Fensteranfang neu, Vorprobe auf den Muster-2-Zweig. **Erledigt
   26.09.2026 als E43.5** (Arbeitszweig).
6. **Nachmessung mit genau einem Unterschied — GEMESSEN 26.09.2026 als E43.6:**
   `rest_halten`, `strict_confirm`, `confirm_t1`, `cooldown_h` — alle vier Regeln
   nicht erfüllt (keine Zeile in beiden Fensterhälften ≥ 1 Punkt besser), alle vier
   bleiben aus. `strict_confirm` sah in H1 sogar besser aus, drehte in H2 aber um
   7,6 Punkte. Einzelheiten: `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt
   „Messung E43.6". Als Nächstes: `block_unhealthy`/Muster 5 einmal wiederholen,
   sobald `muster_cvd`/`muster_oi` tatsächlich wechseln (siehe Abschnitt E43.6).
7. **Wissens-Layer berichtigen:** `be_im_plus`-Urteil, E37-Satz („keine einzige
   Variante“), „Faktor 69“ beim Funding = Prozent-Einheit.
8. **A5 — GEMESSEN und ENTSCHIEDEN 26.09.2026.** „Teilgewinn am letzten Hoch“
   (`high_exit`, live) hing von der geladenen Historie ab: `next_pivot_beyond()` nahm
   das nächste Pivot-Hoch über dem Kurs aus **allen** geladenen Kerzen, live sind das
   nur `main.LIMIT_HAUPT` (1.300) Kerzen (gleitendes Fenster), der Backtest rechnete ab
   10.08.2025 (wachsendes Fenster) — dieselbe Fehlerklasse wie A2/A3 (live ≠ Backtest).
   **Zählung:** 53 von 1.177 nachstellbaren Kerzen hätten ein anderes nächstes Pivot
   gesehen — Treffer > 0. **Gitterzeile gebaut** (`evaluate(high_exit_hist="live")`,
   genau ein Unterschied zur Panel-Zeile, „LIVE-heute +Pivot-Hoch nur letzte 1.300
   Kerzen (A5)“) und über GitHub Actions gemessen: Rendite/Hälften/Rückgang/Signale
   identisch zur Live-Zeile (+35,3 %, −9,9 %, 244 Signale, beide Varianten gleich).
   **Regel nicht erfüllt** (beide Hälften ≥ 1 Punkt besser: nein) — `high_exit_hist`
   bleibt auf `"voll"`. Wie bei A2: der Fehler ist real, aber folgenlos fürs Ergebnis.
   Einzelheiten: `docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „A5“.

## Am Wissens-Layer selbst

*(Etappe 2 und 3 sind am 05.09.2026 abgeschlossen worden.)*

## Erledigt am 13.09.2026 — die fünf offenen Gitterzeilen sind gemessen

Alle fünf sind **durchgefallen**. `trend_filter` und `ampel_filter` bleiben aus; die
dazugehörigen **Anzeigen** (Trend in der Lage, Ampel darunter) bleiben live. Zahlen und
Begründung: `docs\PLAN-E33-UEBERGEORDNETER-TREND.md`, `docs\PLAN-E34-AMPEL.md` und
`wissens-layer\02_status\GEMESSEN-UND-ENTSCHIEDEN.md`.

**Damit ist die Filter-Frage vorerst zu.** Zwölf gemessene Filter, zwölf schlechter.
Wer den dreizehnten vorschlägt, sollte zuerst erklären, warum er nicht unter dieselbe
Diagnose fällt: Die Engine ist im Mittel nur mit 29 % des Kapitals investiert — ihr
Problem ist zu wenig Teilhabe, nicht zu wenig Vorsicht.

## Erledigt am 17.09.2026 — pünktlicher Anstoß über cron-job.org

**Die größte Lücke zwischen Backtest und Wirklichkeit ist geschlossen.** Der Befund vom
29.07.2026 (`signal-app\ANLEITUNG-PUENKTLICHER-START.md`) galt unverändert weiter:
Nachgemessen am 17.09.2026 lief der letzte GitHub-Zeitplan-Lauf erst um 09:08 UTC, eine
Stunde nach dem 08:00-Kerzenschluss — die 12:00-Kerze war zu diesem Zeitpunkt schon über
eine Stunde geschlossen und noch nicht ausgewertet.

**Warum das mehr war als Komfort:** Der Backtest handelt zum exakten Signalpreis im
Moment der Kerzenschluss-Auswertung. Die gemessenen +30,9 % (Stand 13.09.) setzen also
eine Pünktlichkeit voraus, die es in der Praxis nicht gab — die größte Lücke zwischen
Messung und Wirklichkeit, die dieses Projekt hatte, und im Gegensatz zu jedem gemessenen
Filter mit 15 Minuten Arbeit zu schließen.

**Umsetzung:** Kaiser hat einen Fine-grained Personal Access Token (`engine-anstoss`,
nur `btc-signal-app`, `Actions: Read and write`, 1 Jahr) sowie ein Konto bei
cron-job.org angelegt. Auftrag „BTC Signal-Engine" ruft
`.../actions/workflows/signal.yml/dispatches` per POST auf, sechsmal täglich
(0/4/8/12/16/20 Uhr UTC + 2 Minuten), mit den Headern `Accept`, `Authorization: Bearer …`,
`X-GitHub-Api-Version` und `Content-Type: application/json`, Body `{"ref":"main"}`.
Benachrichtigung bei Fehlschlag steht an. Testlauf: `204 No Content`, GitHub Actions
zeigte den Lauf sofort als „Manually run" (#416).

Der GitHub-Zeitplan bleibt zusätzlich als Netz bestehen — doppelte Telegram-Nachrichten
kann es nicht geben, die Engine merkt sich die zuletzt ausgewertete Kerze.

**Noch offen:** die Flush-Wache (`watch.yml`, alle 15 Minuten) hat dasselbe
Zuverlässigkeitsproblem. Bewusst noch nicht angefasst — erst beobachten, wie sich die
Telegram-Nachrichtenzahl mit dem pünktlichen Haupttakt entwickelt (Kaiser wollte die
Zahl „erst mal belassen").

## Am Projekt

- **Der übergeordnete Rahmen: als mechanischer Filter erledigt, als Idee offen.**
  Furkans Prozess ist zweistufig: erst der Makro-Bias, dann Order-Flow zum Timing
  (`docs\STRATEGIE.md` §5). Horizont 3 ist seit E33/E34 **sichtbar** (Tages-EMA200,
  Ampel) und gemessen — als Regel kostet er Rendite, und zwar dramatisch (−0,4 %
  gegen +30,9 %, Signale von 251 auf 49). Der Grund ist strukturell: Ein
  Fib-Retracement wird definitionsgemäß in einem Rückgang erreicht — genau die
  Momente, die ein „Kurs über EMA"-Filter ausschließt. **Ein Tages-EMA ist kein
  Ersatz für einen Makro-Bias.**
- **KI-Makro-Bias** (`signal-app\PLAN-E8.5-KI-MAKRO-BIAS.md`, 24.07.2026, nie gebaut).
  Furkans echte Methode: US-Aktienmarkt, Staatsanleihen, Renditen — *kein* EMA
  (Transkript 15:58). Das Hindernis ist nicht der Aufwand, sondern die Prüfbarkeit:
  **man kann nicht fragen, was eine KI im März 2026 gesagt hätte, ohne dass sie den
  weiteren Verlauf kennt.** Der billige Behelf ist jetzt gemessen und durchgefallen —
  das ist ein Argument dafür, die teure Lösung zu prüfen, aber **kein** Argument dafür,
  sie ungemessen live zu schalten. Wer sie angeht, braucht zuerst eine Antwort auf die
  Prüfbarkeitsfrage, nicht auf die Bau-Frage.
- **`confirm_t1` und `cooldown_h` — GEMESSEN 26.09.2026 (siehe Punkt 6 oben).** Auf
  ihrer damaligen Basis (+33,3 %) sahen sie deutlich besser aus (+36,1 % bzw. +36,5 %)
  — diese Basis gibt es nicht mehr. Auf der heutigen Live-Zeile mit genau einem
  Unterschied gemessen: beide Regeln nicht erfüllt, beide bleiben aus.
- **`be_im_plus` und `release_stale_rest` — GEMESSEN 26.09.2026 als E43.8** (Details:
  `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „Messung E43.8"). Beide Regeln
  nicht erfüllt, beide bleiben aus. **`be_im_plus` ist dabei ein echter, großer
  Befund** (anders als A2/A3/A5/E43.6): 205 von 244 Signal-Paaren ändern sich, die
  Rendite bricht von +35,3 % auf +18,0 % ein (−17,3 Punkte, fast nur in Hälfte 1) —
  reiht sich bei den zwölf zuvor gemessenen Filtern ein, die alle Rendite kosteten.
  `release_stale_rest` ändert kaum etwas (2 von 244 Paaren) und verfehlt die Regel nur
  knapp.
- **E32.2 — Meldung, wenn die Spot-Nachfrage kippt**, während eine Position offen ist.
  Schaltbar, Default aus. Seit E32.1 steht die Lage in Plan und Vorschau, seit E34 auch
  die Ampel; was fehlt, ist die aktive Meldung bei einem **Wechsel** — heute muss Kaiser
  auf die nächste Plan-Nachricht warten, und die kommt nur, wenn sich eine Marke ändert.
  Naheliegende Erweiterung: melden, wenn die **Ampelstufe** wechselt.
*(E32.3 wurde am 13.09.2026 gemessen und verworfen — die 1D-Ebene ist in jeder
Swing-Weite deutlich schlechter. Siehe `wissens-layer/02_status/GEMESSEN-UND-ENTSCHIEDEN.md`.)*

- **Struktur-Bruch-Benachrichtigung.** Angeboten, nicht entschieden: eine reine
  Info-Nachricht, wenn die Struktur bricht, breiter als die heutige schmale
  Derivate-Pump-Warnung. Keine neue Handelsregel, nur Information.
- **Tote Nachkaufstufen im Telegram-Plan.** Marken unterhalb des nachgezogenen Stops
  werden weiterhin angezeigt, obwohl sie unerreichbar sind. Reines Anzeigeproblem,
  bewusst nicht Teil von E30.
- **Telegram-Nachrichtenzahl** (~40 im Fenster, Ziel ~20). Kaiser: „erst mal belassen."
- **Heatmap-Test:** bisher nur 1 von 4–5 geplanten Beobachtungen; Kursverlauf ab
  ca. 30.08. nachzutragen.
*(**Cron-job.org als zweiter Auslöser** wurde am 17.09.2026 eingerichtet — siehe unten.)*
- **Makro-Video vom 02.08.2026** ist noch nicht ausgewertet.
- **STH-Kostenbasis (E40) — erledigt 21.09.2026.** Als Regel im Fenster nicht
  prüfbar (84 % der Kerzen darunter, 7 Wechsel) — E40.2/E40.3 nicht gebaut. **Als Zeile
  im Lage-Abruf gebaut** (Kaiser: „Ja, als Zeile im Abruf"): Wert, Abstand in Prozent,
  Datum. Quelle bitview.space, Ersatz bitcoin-data.com. Plan: `docs\PLAN-E39-E40.md`.
  Neu prüfen erst, wenn das Messfenster eine längere Phase **über** der Marke enthält.
- **E41 — Stop mit Rückeroberung: LIVE seit 21.09.2026** (Kaisers Regel, 1 Kerze).
  **Die Ausschalt-Regel hat am 23.09.2026 angeschlagen** (Rückgang 1,5 statt höchstens
  1,0 Punkte tiefer als der alte Stop) und wurde von Kaiser **bewusst überstimmt** —
  Rendite +2,6 Punkte, und der Rückgangsvergleich zwischen Varianten ist pfadabhängig.
  **Beim nächsten Backtest wieder ansehen:** Abschnitt „E41" im Bericht prüft die Regel
  selbst und schreibt „Bleibt an." oder „AUSSCHALTEN.". Schlägt sie erneut an, ist die
  Frage nicht „ausschalten oder nicht", sondern ob der Fenster-Rückgang das richtige Maß
  ist (siehe E41.6). Telegram meldet „STOP WARTET" und „MARKE ZURÜCKEROBERT".
  `docs\PLAN-E41-STOP.md`.
- **E41.6 — ein Risikomaß ohne Pfadabhängigkeit (vorgeschlagen, nicht gebaut).** Für
  jeden Stop des alten Stops den **tiefsten Punkt**, den die Position live danach noch
  sah, bevor sie endete — reines Kursrechnen, unabhängig davon, was die Engine danach
  tat. Damit ließe sich die Ausschalt-Bedingung als „zusätzlicher Buchverlust je
  betroffener Position" fassen statt als Fenster-Rückgang. Schwelle **vor** der Messung
  festlegen. Begründung: `docs\PLAN-E41-STOP.md`, Abschnitt E41.6.
- **Drei statt einer Kerze (B3) — vorab festgelegte Regel liegt vor, Stand offen.** B3
  sieht in beiden Läufen besser aus (Rendite, Rückgang), hält aber die Rauschgrenze in
  Hälfte 2 nicht (+0,2 Punkte) und rettet keine Position mehr als B1. Ein Wechsel ist nur
  nach der im Plan festgelegten Regel zulässig (zwei Läufe, vier Wochen Abstand, in
  beiden Hälften ≥ 1 Punkt besser, Rückgang nicht tiefer).
- **E42 — Ausbruch mit Rücktest (Kaisers Regel, 21.09.2026), vorgemerkt.** Die Engine
  verkauft live unter dem letzten Hoch (`high_exit: on`). Bricht der Kurs dort durch
  und hält beim Rücktest (Schluss nicht mehr darunter, höchstens der Docht), sind
  weitere Gewinne zu erwarten — zurückkaufen oder den Rest halten? Eigene Etappe, weil
  sie in E41 einen zweiten Unterschied pro Gitterzeile erzeugen würde.
- **Offene statt gelaufene Liquidationscluster** (neu, 20.09.2026). Die Engine hat
  bereits eine Liquiditätskarte — `liq_entry: boost` ist seit E10.3 live. Aber
  `liq_levels()` baut die Niveaus aus **bereits gelaufenen** Kaskaden. Furkan schaut
  auf die geschätzten Liquidationspreise **noch offener** Positionen (Hyblock,
  Video 13.09., 16:00–16:37). **Das Hindernis ist die Prüfbarkeit, nicht der Bau:**
  für einen Backtest bräuchte man die historischen Heatmaps, und eine freie Quelle
  dafür ist nicht bekannt. Damit fällt der Punkt in dieselbe Kategorie wie der
  KI-Makro-Bias. Der laufende `heatmap-test` (bisher 1 von 4–5 Beobachtungen) ist der
  billige Weg, überhaupt erst ein Gefühl dafür zu bekommen.
- **Muster 5 — gemessen und entschieden (E38, 21.09.2026).** Das Signal ist echt
  (erste Kerze einer Episode: +1,2 Punkte über Grundrate, 77 % höher), die Engine kann
  es aber nicht benutzen, weil sie nur an Fib-Zonen entscheidet. Alle Schalter aus.
  **Zwei Reste bleiben offen:**
  (a) ~~Die Lagezeile stimmt nicht mehr mit der Messung überein.~~ **Erledigt
  21.09.2026:** neuer Text in allen Nachrichten, Ampel zählt Muster 5 neutral.
  (b) **Ein zonenfreier Muster-5-Einstieg** wäre ein zweites, kurzfristiges System mit
  eigenem Stop — kein Schalter. Nicht entschieden; Einwände im Plan.
  Beleg: `docs\PLAN-E38-MUSTER5.md`.
- **Sicherung `signal-app-lokal\`** ist der Stand vom 22.07.2026, also überholt.
  Entweder auffrischen oder als historisch kennzeichnen.

## Bekannt und bewusst nicht behoben

- ~~**Code verweist über die Repo-Grenze.**~~ **Erledigt 26.09.2026:** `docs\` und der
  Wissens-Layer liegen jetzt im Repo `btc-signal-app`.
- **Kein Auto-Trading.** Bewusste Entscheidung, kein offener Punkt.
- **`widerstand_exits` (E20) wird nicht in `state.json` gespeichert** (gefunden beim
  E41-Bau, 21.09.2026). Folgenlos, solange `widerstand_exit` aus ist — wird der
  Schalter je eingeschaltet, muss das vorher behoben werden: Die Live-Engine vergäße
  sonst bei jedem Lauf, welche Widerstands-Teilverkäufe schon gemeldet wurden.
