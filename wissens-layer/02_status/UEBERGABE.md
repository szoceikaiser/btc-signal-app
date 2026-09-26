# Laufende Übergabe

> Was zuletzt passiert ist, was offen liegt, was eine neue Session als Erstes wissen
> muss. **Jüngster Abschnitt oben.** Nach jeder abgeschlossenen Arbeit einen datierten
> Abschnitt hier ergänzen — nicht erst am Ende eines Vorhabens.
>
> Kurzfassung: `00_STAND.md`. Fertiger Prompt für einen neuen Chat: `STARTPROMPT.md`.

---

## 26.09.2026 (22) — E44.2 gebaut: Wechselwirkungen und Monats-Probe (Zweig, wartet auf Go)

Auf Zweig `claude/blissful-maxwell-9uwt6x`, zusammen mit E44.1. In `backtest.py`:
`e442_vierergruppen` (findet alle sauberen 2×2-Gruppen im Gitter, Basis = Ecke mit beiden
Schaltern aus), `e442_wechselwirkung`, `monats_probe` (hält der Vorsprung ohne den
günstigsten Monat?) und der neue Berichtsabschnitt „E44: Wechselwirkungen und
Monats-Probe“. Gegen das echte Gitter geprüft: **dieselben 16 Gruppen** wie in der Analyse.
Kein Schalter, keine Gitterzeile, kein Urteil geändert. 10 neue Tests, **545 grün**,
`sabotage_e442.py` **8/8 gefangen**. Die Probe fand beim ersten Lauf eine echte Testlücke
(beide Hälften hatten im Test dieselben Zahlen, eine vertauschte Hälfte fiel nicht auf),
behoben.

**Offen für Kaiser: ein Go für `main` deckt E44.1 und E44.2 ab.** Danach: Actions →
Coinalyze-Archiv → Run workflow (einmal von Hand), und beim nächsten Backtest erscheint
der Abschnitt „E44“ im Bericht.

**Nächster Schritt danach:** E44.3 (E42 Ausbruch mit Rücktest), braucht Kaisers Antwort
auf Frage 1 im Plan, Abschnitt 10. Aufwand hoch. Startprompt: Plan, Abschnitt 9a.

---

## 26.09.2026 (21) — E44.1 gebaut: Coinalyze-Archiv (Zweig, wartet auf Go)

Kaiser: *„Leg mir 44.1 und 44.2 los und bereite jede Etappe so vor, dass ich im neuen Chat
damit beginnen kann.“* Startpunkte je Etappe stehen jetzt im Plan, Abschnitt 9a,
Einzelheiten zu E44.1/E44.2 in 9b/9c, Platz für Kaisers Antworten in Abschnitt 10.

**E44.1 gebaut** auf Zweig `claude/blissful-maxwell-9uwt6x`: `engine/archiv.py` (mischt
OI, Liquidationen, Futures-Delta, Long-Short in `site/data/archiv/coinalyze_4h.json`, nur
abgeschlossene Kerzen, neu gewinnt, alt bleibt), `backtest.py` mischt das Archiv vor dem
Aufbau der Reihen dazu und nennt im Bericht, wie viele OI-Punkte nur aus dem Archiv stammen.
Neuer Workflow `.github/workflows/archiv.yml` (täglich 03:47 UTC plus Knopf). `main.py`
unberührt. 8 neue Tests, **535 grün**, `sabotage_e441.py` **8/8 gefangen**.

**Solange das Archiv leer ist oder nicht älter als Coinalyze, ändert sich keine Zahl.**
Der Nutzen beginnt erst, wenn der Workflow in `main` läuft; jeder Tag ohne ihn kostet rund
6 alte 4h-Punkte. **Offen für Kaiser: Go für `main`.** Danach einmal anstoßen: Actions →
Coinalyze-Archiv → Run workflow.

**Als Nächstes:** E44.2 (läuft in diesem Chat weiter).

---

## 26.09.2026 (20) — E44: Kombinations-Analyse, Bauplan geschrieben, nichts gebaut

**Auftrag Kaiser:** *„welche dieser Tests und Indikatoren miteinander kombiniert und getestet
werden können. Um am Ende mehr Rendite rauszuholen […] Insbesondere beachte Furkans
Strategien.“* Ergebnis: `docs/PLAN-E44-KOMBINATIONEN.md`.

**Grundlage:** keine neue Messung. Nachgerechnet aus `BACKTEST.md` (Lauf 26.09. 15:18) und
`site/data/backtest_signals.json` (Nachbau endet bei 13.509 € gegen 13.532 € im Bericht).
Befunde:
- 16 saubere 2×2-Gruppen im Gitter: Filter × Filter bis −10,2 Punkte über die Summe hinaus,
  Verstärker × Verstärker additiv, Ergänzungen bis +13,7. Eingetragen in
  `GEMESSEN-UND-ENTSCHIEDEN.md`, Abschnitt „Wechselwirkungen“.
- Live-Einstellung: 50 % der Zeit in einer Position, zeitgewichtet 35 % investiert, in einer
  Position fast immer 100 %, Haltedauer Median 4 Tage. Rest-Verkauf bei Gegen-Muster zu
  7 von 9 richtig, die 2 falschen sind die Rallys (07.04. +5,4 %, 19.08. +14,4 %). Die Stops
  hielten die Engine aus beiden großen Abwärtsphasen heraus.
- Furkan-Abgleich über die ausgewerteten Auszüge in `docs/`. **Die Rohabschriften im
  Backup-Repo waren nicht lesbar** (Rechte-Prüfung der Arbeitsumgebung hat das Auflisten
  blockiert), das steht als offene Frage im Plan.

**Vorschlag:** E42 (Ausbruch mit Rücktest) als Partner von `high_exit`, `verkauf_faktor`
0,67 und `rest_halten` im 2³-Gitter. Hauptzeile „LIVE-heute +E42“ entscheidet nach der
bekannten Regel plus Monats-Probe, die übrigen Zeilen brauchen 2 Punkte in beiden Hälften.
K4 (Shorts im Abwärts-Regime) nur nach Kaisers Grundsatz-Ja.

**Offen für Kaiser:** die drei Fragen in Abschnitt 10 des Plans. **Sofort machbar ohne
Antwort:** E44.1 (Coinalyze-Archiv) und E44.2 (Wechselwirkungs-Tabelle und Monats-Probe
im Bericht), beide Aufwand mittel. Code unberührt, 527 Tests grün.

---

## 26.09.2026 (19) — E43.7 in main nachgetragen, E43 abgeschlossen

**Kaiser:** *„43.7 und 43.8 müssten schon erledigt sein.“* Stimmt: E43.8 war in `main`.
E43.7 war um 13:44 Uhr in einem **parallelen Chat** erledigt worden (Zweig
`claude/e43-6-gitterzeilen-eo6mzb`, Commit `5bc1030`), der E43.6 ein zweites Mal gebaut
hatte. Nach `main` kam die E43.6-Fassung des anderen Zweigs, E43.7 blieb liegen.

**Getan (reine Unterlagen, direkt in `main`, Kaisers „Ja, leg los“):** die drei
Korrekturen neu eingetragen, nicht kopiert (der Doppel-Zweig hatte leicht andere Zahlen):
E37-Satz, `be_im_plus`-Urteil (Lesefehler, mit E43.8-Zahlen; Randvermerk auch in
`docs/ETAPPENPLAN.md` E19 und `docs/FURKAN-UPDATE-2026-08-03.md` §3), Funding-„Faktor 69“
(= Einheit). Abschnitt „nie entschieden“ in `GEMESSEN-UND-ENTSCHIEDEN.md` mit allen sechs
Messungen geschlossen, Vorbehalt oben um E43.4 ergänzt. Zwei Lehren in
`BEKANNTE-PROBLEME.md`: Fixtures im echten Datenformat bauen; nicht zwei Chats parallel.
`STARTPROMPT.md` auf 527 Tests und E43-abgeschlossen gebracht. **Code unberührt, 527
Tests grün.**

**Offen, klein:** `_hinweis_be_im_plus` in `site/data/config.json` zitiert Furkan ohne die
Vorbedingung — mit der nächsten Code-Änderung auf einem Arbeitszweig berichtigen. Der
Doppel-Zweig `claude/e43-6-gitterzeilen-eo6mzb` ist überholt; löschen macht Kaiser.

**Nächster Schritt (Kaisers Auftrag):** Kombinations-Analyse — welche einzeln gemessenen
Mechanismen und Indikatoren sich sinnvoll kombinieren lassen, mit Furkans Transkripten.

---

## 26.09.2026 (18) — E43.8 gemessen: be_im_plus und release_stale_rest bleiben aus

**Auftrag Kaiser:** „be_im_plus und release_stale_rest jetzt auch messen" — die
letzten zwei aus der Liste der seit Monaten unentschiedenen Schalter
(`02_status/OFFENE-PUNKTE.md`). Auf neuem Zweig
`claude/e43-8-nachmessung-be-im-plus-release-stale-rest` (von `main`) gebaut: zwei
Gitterzeilen mit genau einem Unterschied zur Panel-Zeile, Vorbild E43.6.

**Besonderheit:** beide Schalter sind zustandsabhängig (Break-even-Zeitpunkt bzw.
Rest-Freigabe hängen vom laufenden Positions-Status ab) — anders als
`strict_confirm`/`confirm_t1` (reine Kerzen-Logik) gibt es keine Vorprobe ohne
Simulation. Die Vorprobe zählt deshalb generischer: an wie vielen (Zeitpunkt,
Signaltyp)-Paaren die Gitterzeile überhaupt vom Live-Lauf abweicht
(`e438_signale_verschieden`, verallgemeinert aus dem „Verschieden erkannt" von
E43.3/E43.4). 7 neue Tests, **527 Tests grün**, keine Änderung an `strategy_core.py`
(beide Schalter existieren und rechnen schon richtig), keine eigene Sabotage-Datei.

**Gemessen (GitHub-Actions-Lauf 36250880529, Fenster 18.01.–26.09.2026):**

| Schalter | Vorprobe (Treffer) | Rendite | H1 | H2 | Signale | Urteil |
|---|---:|---:|---:|---:|---:|---|
| **Live (Basis)** | — | +35,3 % | +23,6 % | +9,5 % | 244 | — |
| `be_im_plus` | 205 Paare | +18,0 % | +8,1 % | +10,0 % | 348 | H1 −15,5, H2 +0,5 → nicht erfüllt |
| `release_stale_rest` | 2 Paare | +34,6 % | +22,5 % | +9,5 % | 244 | H1 −1,1, H2 +0,0 → nicht erfüllt |

**Beide Schalter bleiben aus.** `be_im_plus` ist dabei — anders als A2/A3/A5/E43.6 —
ein echter, großer Befund: 205 von 244 Signal-Paaren ändern sich, die Signalzahl
steigt um 104 (244→348), die Rendite bricht um 17,3 Punkte ein, fast ausschließlich in
Hälfte 1. Der frühere Break-even-Stop wirft die Engine öfter aus Positionen, die
später weitergelaufen wären. Reiht sich bei den zwölf zuvor gemessenen Filtern ein
(„Zwölf gemessene Filter, zwölf schlechter", `00_STAND.md`). `release_stale_rest`
ändert dagegen kaum etwas (2 von 244 Paaren) und verfehlt die Regel nur knapp.
Am Handelsverhalten ändert sich nichts. Einzelheiten:
`docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „Messung E43.8".

**Damit ist Punkt 6 aus `02_status/OFFENE-PUNKTE.md` (seit Monaten unentschiedene
Schalter) vollständig abgeschlossen:** alle sechs (`rest_halten`, `strict_confirm`,
`confirm_t1`, `cooldown_h`, `be_im_plus`, `release_stale_rest`) sind jetzt mit genau
einem Unterschied gemessen. Alle bleiben aus.

**Nächster Schritt, offen:** E43.7 (Wissens-Layer-Texte berichtigen — u. a. das
`be_im_plus`-Lesefehler-Urteil aus der Gesamtprüfung, jetzt mit den echten Zahlen von
E43.8 unterlegbar), oder E41.6/E42 (Kaisers Entscheidung).

---

## 26.09.2026 (17) — E43.6 gemessen: alle vier Schalter bleiben aus

**Auftrag Kaiser:** „Merge nach main und E43.6 bauen" — A5 (siehe unten) nach `main`
gemergt, dann E43.6 auf neuem Zweig `claude/e43-6-nachmessung-vier-schalter` (von
`main`) gebaut: vier Gitterzeilen mit genau einem Unterschied zur Panel-Zeile
(`rest_halten`, `strict_confirm`, `confirm_t1`, `cooldown_h=48`), je eine Vorprobe im
Datensatz, Entscheidungsregel wie E41/E43.2–E43.5/A5.

**Vorbereitung:** `_confirm_long()`/`_confirm_short()` in `strategy_core.py` auf eine
neue, öffentliche `confirm_ok()` zurückgeführt (einzige Rechenstelle) — `evaluate()`
UND die `strict_confirm`/`confirm_t1`-Vorproben lesen jetzt von derselben Funktion.
Reiner Refactor, kein Verhaltensunterschied. 13 neue Tests, **520 Tests grün.** Keine
eigene Sabotage-Datei (kein neuer Rechenweg außerhalb des bekannten
`confirm_ok`/`exit_pat`/`_cooldown_ok`, wie E43.2).

**Gemessen (GitHub-Actions-Lauf 36249824852, Fenster 18.01.–26.09.2026):**

| Schalter | Vorprobe (Treffer) | Rendite | H1 | H2 | Signale | Urteil |
|---|---:|---:|---:|---:|---:|---|
| **Live (Basis)** | — | +35,3 % | +23,6 % | +9,5 % | 244 | — |
| `rest_halten` | 11 Positionen | +34,5 % | +19,4 % | +12,7 % | 236 | H1 −4,3, H2 +3,2 → nicht erfüllt |
| `strict_confirm` | 1.356 von 1.505 Kerzen | +28,5 % | +26,0 % | +1,9 % | 206 | H1 +2,4, H2 −7,6 → nicht erfüllt |
| `confirm_t1` | 9 von 14 Ersteinstiegen | +34,9 % | +22,8 % | +10,3 % | 240 | H1 −0,8, H2 +0,9 → nicht erfüllt |
| `cooldown_h` (48h) | 1 Einstieg | +33,4 % | +21,8 % | +9,5 % | 244 | H1 −1,8, H2 +0,0 → nicht erfüllt |

**Alle vier Schalter bleiben aus.** Rückgang bei allen vieren identisch zur Live-Zeile
(+0,0 Punkte) — die Regel scheitert überall am ersten Kriterium (beide Hälften ≥ 1
Punkt besser). Auffällig: `strict_confirm` sah in H1 sogar besser aus (+2,4 Punkte),
drehte in H2 aber um 7,6 Punkte — genau die Art von Einzelhälften-Vorsprung, vor der
die Regel schützen soll (dieselbe Lehre wie B3/E41.6). Am Handelsverhalten ändert sich
nichts. Einzelheiten: `docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „Messung
E43.6".

**Damit sind `confirm_t1` und `cooldown_h` aus der Liste der seit Monaten
unentschiedenen Schalter raus** (`02_status/OFFENE-PUNKTE.md`). Offen bleiben
`be_im_plus` und `release_stale_rest` — dieselbe Messlücke, noch nicht angegangen.

**Nächster Schritt, offen:** E43.7 (Wissens-Layer-Texte berichtigen), `be_im_plus`/
`release_stale_rest` messen, oder E41.6/E42 (Kaisers Entscheidung).

---

## 26.09.2026 (16) — A5 gemessen und entschieden: bleibt aus

**Auftrag Kaiser:** A5 messen wie in `OFFENE-PUNKTE.md` Punkt 8 beschrieben. Erst
zählen, an wie vielen Kerzen im Fenster `next_pivot_beyond()` mit der Live-Historie
(1.300 Kerzen) ein anderes nächstes Pivot-Hoch fände als mit der Backtest-Historie (ab
10.08.2025). Bei 0 Treffern nur dokumentieren, sonst eine Gitterzeile mit genau einem
Unterschied bauen.

**Zählung (GitHub-Actions-Lauf 36247317191):** 53 von 1.177 nachstellbaren Kerzen im
Fenster hätten ein anderes nächstes Pivot gesehen (long oder short) — Treffer > 0, also
weiter wie im Auftrag beschrieben.

**Gebaut:** neuer Parameter `evaluate(high_exit_hist="voll"|"live")` in
`strategy_core.py`. `"live"` beschränkt die Pivotsuche NUR für den `high_exit`-
Teilverkauf (Teilgewinn am letzten Hoch) auf die letzten `HIGH_EXIT_LIVE_KERZEN`
(= `main.LIMIT_HAUPT`, 1.300) Kerzen — kein Eingriff in die übrigen Pivot-Verwender
(Impuls, Gegenzonen, 1D-Ebene). Default `"voll"` = bisheriges Verhalten; `main.py` lädt
ohnehin nur 1.300 Kerzen, dort also folgenlos. Gitterzeile „LIVE-heute +Pivot-Hoch nur
letzte 1.300 Kerzen (A5)“ mit genau einem Unterschied zur Panel-Zeile. `a5_next_pivot_
beyond`, `a5_einschalten`, `a5_abschnitt` im Bericht (Vorbild E43.3/E43.4). 8 neue
Tests (Mechanismus in `evaluate()`, Berichtsabschnitt, Konfig-Default) — **507 Tests
grün.** Keine eigene Sabotage-Datei (kein neuer Rechenweg außerhalb des bekannten
`next_pivot_beyond`, wie E43.2).

**Gemessen (GitHub-Actions-Lauf 36248384303, Fenster 18.01.–26.09.2026):**

| Variante | Rendite | Rückgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live (voll)** | +35,3 % | −9,9 % | +23,6 % | +9,4 % | 244 |
| Pivot-Hoch nur letzte 1.300 Kerzen (live) | +35,3 % | −9,9 % | +23,6 % | +9,4 % | 244 |

**Urteil nach der vorab festgelegten Entscheidungsregel** (wie E41/E43.2/E43.3/E43.4):
in beiden Hälften ≥ 1 Punkt besser: **nein** (H1 ±0,0, H2 ±0,0). Rückgang: gleich.
**Regel nicht erfüllt — `high_exit_hist` bleibt auf `"voll"`.**

**Einordnung:** dieselbe Lehre wie bei A2/E43.3 — der Fehler ist im Prinzip echt (53
von 1.177 Kerzen sehen ein anderes Pivot), wirkt sich im gemessenen Fenster aber auf
kein einziges Signal aus. Kein Renditebefund, weder dafür noch dagegen. Am Code sonst
nichts geändert. Einzelheiten: `docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „A5“.

**Nächster Schritt, offen:** E43.6 bauen (wartet auf Kaisers Go, siehe unten) oder
E41.6/E42 (Kaisers Entscheidung).

---

## 26.09.2026 (15) — E43.6-Bauplan geschrieben, wartet auf Kaisers Go zum Bauen

Auftrag Kaiser: erst den Bauplan-Abschnitt E43.6 schreiben und zeigen, noch nicht bauen.
Erledigt in `docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „E43.6": je Schalter
(`rest_halten`, `strict_confirm`, `confirm_t1`, `cooldown_h`) eine Gitterzeile mit genau
einem Unterschied zur heutigen Panel-Zeile, eine Vorprobe im Datensatz und die
Entscheidungsregel wie bei E43.2/E43.3/E43.4 (beide Hälften ≥ 1 Punkt besser, Rückgang
nicht mehr als 1 Punkt tiefer).

**Geklärt: Muster-5-Wiederholung lohnt sich jetzt nicht.** Teil C des Prüfberichts wollte
sie „nach der Korrektur" von A2/A3. Beide Korrekturen (`muster_cvd`, `muster_oi`) sind
inzwischen gemessen und **beide auf dem alten Wert geblieben** (`"alt"`, `"usd"`) — an der
Mustererkennung, an der Muster 5 hängt, hat sich also nichts geändert. Eine Wiederholung
jetzt würde exakt dieselben Zahlen liefern wie zuletzt. Zurückgestellt, nicht vergessen:
erst sinnvoll, wenn einer der beiden Schalter tatsächlich live geht.

**Keine Code-Änderung, kein Test lief.** 493 Tests bleiben Referenz. Noch nicht gebaut:
vier neue `V(...)`-Zeilen und ein Berichtsabschnitt „E43.6" in `engine/backtest.py`,
geschätzt 4–8 neue Tests, aller Wahrscheinlichkeit nach ohne eigene Sabotage-Datei
(kein neuer Rechenweg, nur neue Messzeilen).

**Nächster Schritt:** Kaisers „Ja" zum Bauplan, dann Bau auf einem `claude/...`-Zweig,
Vorprobe je Zeile, Messung, Urteil nach der Entscheidungsregel — wie bei E43.3/E43.4.

---

## 26.09.2026 (14) — Kaisers Go: E43.4b in main, weiter im neuen Chat

Kaiser: *„Ja“* (Go für `main`). Arbeitszweig `claude/e43-4-open-interest-9mmh0l` per
Fast-Forward nach `main`. Die OI-Zeile im Lage-Abruf zeigt ab dem nächsten Abruf die
Kontrakte (reine Anzeige). **493 Tests grün in `main`.** `STARTPROMPT.md` nachgezogen.

**Nächster Schritt: E43.6**, im neuen Chat. Zuerst den Bauplan-Abschnitt „E43.6“ im
Plan schreiben und Kaiser zeigen: vier Gitterzeilen mit genau einem Unterschied zur
heutigen Live-Zeile (`rest_halten`, `strict_confirm`, `confirm_t1`, `cooldown_h`), je
eine Vorprobe, dass der Schalter im Datensatz überhaupt etwas ändert, und die
Entscheidungsregel vorab (wie E43.2). **Dabei klären:** Die Muster-5-Wiederholung war
„nach der Korrektur von A3“ gedacht. `muster_oi` blieb aber `"usd"`. Ob sie noch etwas
misst, gehört in den Bauplan. Aufwand: mittel.

---

## 26.09.2026 (13) — E43.4b: OI-Zeile im Lage-Abruf in Kontrakten (Arbeitszweig)

**Kaisers Auftrag:** *„Bau zuerst die OI-Zeile in Kontrakten“* (seine Antwort auf die
Anzeige-Frage A2/A3). Zweig: `claude/e43-4-open-interest-9mmh0l`. **`main` ist
unverändert.** Reine Anzeige, kein Schalter, kein Signal ändert sich.

- Die OI-Zeile zeigt hinter dem Dollar-Wert die Änderung der Kontrakte. Pfeil und Hinweis
  folgen den Kontrakten. Zeigen Dollar und Kontrakte in verschiedene Richtungen, steht
  dabei „der Dollar-Anstieg/-Rueckgang kommt nur vom Kurs“ bzw. „in Dollar vom Kurs
  verdeckt“. Ohne Kontrakt-Reihe (Kraken-Rückfall) bleibt die Zeile wie bisher.
- Die Musterzeile ändert sich nicht, sie rechnet weiter wie der Handel.
- **493 Tests grün** (+5). `sabotage_e434b.py` 9/9 beim ersten Lauf.
- Regel und Beispiel: `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „E43.4b“.

**Offen für Kaiser:** „Go“ für `main`. **Danach:** E43.6, zuerst der Bauplan-Abschnitt.

---

## 26.09.2026 (12) — Kaisers Go: E43.4 in main

Kaiser: *„Go für main“*. Arbeitszweig `claude/e43-4-open-interest-9mmh0l` per
Fast-Forward nach `main` (`main` hatte sich seit dem Abzweigen nicht bewegt).
`muster_oi` bleibt `"usd"`, das Handelsverhalten ändert sich nicht. **488 Tests grün in
`main`.** `STARTPROMPT.md` auf den Stand nach dem Go gebracht.

Kaisers Frage vor dem Go: Vor heute lag die Rendite bei rund 25 %, jetzt bei 35 %. Der
Sprung kommt von E43.2 (`bein_richtung: "bias"`, Go am Vormittag), nicht von E43.3 oder
E43.4. Belegt aus der Berichtsgeschichte: Lauf 08:23 Live-Zeile +25,2 %, die Zeile „Bein
in Handelsrichtung“ im selben Lauf schon +35,4 %. Die alte Einstellung steht im
heutigen Bericht als „LIVE bis 26.09.2026 (ohne Bein-Richtung)“ unverändert bei +25,2 %.
Nebenbei: Die neue Einstellung trifft Furkans Kauftage seltener (Treffer-Quote 59 → 35 %,
Präzision 35 → 23 %).

**Offen für Kaiser:** die Anzeige-Frage zu A2/A3 (Empfehlung siehe Abschnitt 11).
**Danach:** E43.6, zuerst der Bauplan-Abschnitt.

---

## 26.09.2026 (11) — E43.4 gemessen: bleibt `"usd"`, A3 ist echt und groß

Backtest-Lauf 36236645038 (Arbeitszweig `claude/e43-4-open-interest-9mmh0l`, Fenster
18.01.–26.09.2026). **`main` ist unverändert.**

- **Rendite, beide Hälften und Rückgang identisch** (+35,4 %, H1 +23,6, H2 +9,6,
  −9,9 %). **Regel nicht erfüllt, `muster_oi` bleibt `"usd"`.**
- **Vorprobe:** 210 von 1.504 Kerzen anders erkannt (14 %). Derivate-Pump 96 → 48,
  Kapitulation 21 → 11, Short-Covering 56 → 103, Muster 5 47 → 97.
- **A3 als Zahl:** Die Pump-Bedingung „OI ≥ +3 %“ war in Dollar 296-mal erfüllt, in
  Kontrakten 144-mal. Die Hälfte kam also allein vom Kurs. Bei der Kapitulation: 74
  gegen 30.
- **227 statt 244 Signale**, ohne jede Wirkung auf die Rendite. Das passt nur zu Signalen
  ohne Tranche (Pump-Warnungen). **Schluss, nicht gezählt:** Der Bericht schlüsselt
  Signalarten je Zeile nicht auf.
- Nachgetragen: Plan „Messung E43.4“, `_hinweis_muster_oi`, Gitter-Kommentar. Die
  E43.3-Sabotage „Rückgang zählt nicht“ hat eine eindeutige Vorlage bekommen (ihre Zeile
  gibt es seit E43.4 zweimal), weiter 29/29 gefangen. **488 Tests grün.**

**Offen für Kaiser:**
1. „Go“, den Arbeitszweig nach `main` zu übernehmen? Am Handelsverhalten ändert sich
   **nichts** (`muster_oi` bleibt `"usd"`).
2. Anzeige-Frage für A2 und A3 gemeinsam. **Empfehlung der KI:** keine getrennte
   Muster-Anzeige (Lage-Abruf und Handel würden an rund 14 % der Kerzen verschiedene
   Muster nennen). Stattdessen ein kleiner Anzeige-Schritt: In der OI-Zeile steht die
   Kontrakt-Änderung neben der Dollar-Änderung, und der Hinweis folgt den Kontrakten.

**Danach:** E43.6 (Nachmessungen `rest_halten`, `strict_confirm`, `confirm_t1`,
`cooldown_h`; danach Muster 5). Die Voraussetzung „nach A2/A3“ ist jetzt erfüllt.

---

## 26.09.2026 (10) — E43.4 gebaut (Arbeitszweig), Messung läuft

**Kaisers Auftrag:** *„Ja“* (zum Bauplan E43.4). Zweig:
`claude/e43-4-open-interest-9mmh0l`. **`main` ist unverändert**, live ändert sich nichts:
`muster_oi` steht auf `"usd"`.

- Gebaut wie im Bauplan: `FlowPoint.oi_btc`, `oi_in_btc()` (Umrechnung am OI-Datenpunkt,
  dann auffüllen, live und im Backtest dieselbe Funktion), `oi_aenderung()`, Schalter
  `muster_oi` in `classify_pattern`/`evaluate`/`EVAL_DEFAULTS`/`EVAL_KEYS`/`_BASE`/
  `config.json`, Anzeige rechnet wie der Handel, Gitterzeile „LIVE-heute +OI in
  Kontrakten (E43.4)“, Berichtsabschnitt „E43.4“ (Vorprobe, A3 als Zahl, Urteil).
- **488 Tests grün** (467 + 21). `sabotage_e434.py`: 37 von 37 gefangen, beim ersten
  Lauf. Drei Vorlagen in `sabotage_e433.py` auf den neuen Wortlaut nachgezogen (E43.4
  hat dieselben Zeilen geändert). Alle älteren Proben erneut gelaufen, alle Sabotagen
  gefangen: E43.3 29, E43 7, E38 24, E38.1 17, E39 25, E40 27, E41 58.
- Einzelheiten: `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, „Umsetzung E43.4“.

**Offen:** Backtest auf GitHub (Workflow „Backtest“ auf dem Arbeitszweig), dann Urteil
nach der vorab festgelegten Regel, dann Kaisers Go.

---

## 26.09.2026 (9) — Bauplan E43.4 (Open Interest in Kontrakten)

**Kaisers Auftrag:** zuerst den Bauplan-Abschnitt E43.4 schreiben und zeigen, dann bauen.
Zweig: `claude/e43-4-open-interest-9mmh0l`. Reine Planung, **am Code wurde nichts
geändert**, 467 Tests weiter grün. `main` ist unverändert.

**Ergänzt in `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „E43.4“:**
- Schalter `muster_oi` (`"usd"` Default | `"btc"`). Bei `"btc"` rechnet `oi_chg` in
  Kontrakten, für **alle fünf** Muster (Muster 1 fehlte in der Tabelle des Prüfberichts),
  Schwellen unverändert.
- **Abweichung vom Vorschlag im Prüfbericht:** nicht in `classify_pattern` durch den Kurs
  teilen, sondern jeden echten OI-Punkt mit dem Kurs seiner eigenen Kerze umrechnen und
  erst dann auffüllen. Sonst erfinden aufgefüllte Werte eine OI-Bewegung in Höhe der
  Kursbewegung. Das träfe die ersten 11 Kerzen des Messfensters, das dort beginnt, wo das
  OI einsetzt, und live eine fehlende letzte OI-Kerze.
- Entscheidungsregel vor der Messung wie E43.3, dazu Ausschalt-Regel, Vorbedingung
  „misst nichts“, Vorprobe im Datensatz (A3 als Zahl) und in den Tests (`demo_oi_usd`
  mit Gegenprobe; heute nachgeprüft).
- Die OI-Zeile im Lage-Abruf („Positionen werden geschlossen“) ist A3 in der Anzeige.
  Empfohlen als eigener kleiner Anzeige-Schritt, nicht in E43.4.

**Offen:** Kaisers Zustimmung zum Bauplan, dann der Bau (Aufwand **hoch**).

---

## 26.09.2026 (8) — Kaisers Go: E43.5 und E43.3 in main

Kaiser: *„Go“*. Arbeitszweig `claude/btc-signal-engine-start-hyiqny` per Fast-Forward
nach `main`. `muster_cvd` bleibt `"alt"`, das Handelsverhalten ändert sich nicht.
**467 Tests grün in `main`.** Nächster Schritt: E43.4 (Bauplan zuerst), Aufwand hoch.

---

## 26.09.2026 (7) — E43.5 und E43.3 gebaut und gemessen (Arbeitszweig)

**Kaisers Auftrag:** *„Ja, bau E43.5 und E43.3"*. Zweig:
`claude/btc-signal-engine-start-hyiqny`. **`main` ist unverändert.**

**E43.5 fertig** (Befund A4, Bauplan im Plan-Abschnitt „E43.5"):
- `test_mehr_historie_aendert_die_signale_nicht` summiert das CVD jetzt je Ladefenster
  ab null (wie live) und nimmt die Live-Einstellung aus der Panel-Zeile. Die alte,
  hartcodierte Liste war veraltet (ohne `stop_rueckeroberung`, ohne `bein_richtung`).
- Neues Pump-Szenario. Die Vorprobe beweist, dass Muster 2 erreicht wird. Ein
  Befund-Test beweist A2: 400 und 1.200 geladene Kerzen ergeben verschiedene Muster, und
  jede Abweichung ist ein Derivate-Pump.
- **450 Tests grün.** `sabotage_e433.py` 5 von 5 gefangen.

**Neuer Nebenbefund A5 (nicht gemessen, nicht behoben):** „Teilgewinn am letzten Hoch“
hängt von der Länge der geladenen Historie ab (`next_pivot_beyond` sucht in allen
Kerzen). Eingetragen in `OFFENE-PUNKTE.md` Punkt 8.

**E43.3 gebaut** (Befund A2, Plan-Abschnitte „E43.3“, „Ergänzungen“ und „Umsetzung
E43.3“):
- Neuer Schalter `muster_cvd` (`"alt"` | `"usd"`), Default `"alt"` in `config.json`,
  `EVAL_DEFAULTS` und `_BASE`. Bei `"usd"` vergleicht Muster 2 Spot- und Futures-Delta
  als Dollar-Beträge im 12-Kerzen-Fenster. Anzeige und Handel rechnen mit demselben Wert.
- Gitterzeile „LIVE-heute +Muster 2 in Dollar (E43.3)“, genau ein Unterschied zur
  Panel-Zeile. Neuer Berichtsabschnitt „E43.3“: zählt die umklassifizierten Kerzen,
  zählt, wie oft live und Backtest verschieden erkannt hätten, und prüft die
  Entscheidungsregel selbst.
- **467 Tests grün.** `sabotage_e433.py`: 29 Sabotagen, alle gefangen (eine brauchte
  einen zusätzlichen Test, siehe Plan).
- **Offene Entscheidung für Kaiser nach der Messung:** Sonderregel aus dem Prüfbericht
  (Korrektur nur in der Anzeige, Handel bleibt `"alt"`) hieße, dass Anzeige und Handel
  auseinanderlaufen. Nicht gebaut, bis Kaiser das will.

**Backtest gemessen** (GitHub-Lauf 36233723729, Fenster 18.01.–26.09.2026):
- **E43.3:** Nur **2 von 1.504** Kerzen anders erkannt. Rendite (+35,3 %), beide Hälften,
  Rückgang und 244 Signale identisch. **Regel nicht erfüllt, `muster_cvd` bleibt
  `"alt"`.** Live gegen Backtest wich mit `"alt"` an 1 von 1.175 Kerzen ab, mit `"usd"`
  an 0: A2 ist echt, aber klein. Der größere offene Hebel der Mustererkennung ist A3
  (E43.4).
- **E41 auf der neuen Live-Basis:** Die Ausschalt-Regel **schlägt nicht mehr an**
  (Rückgang gleich −9,9 %, H1 +4,0, H2 +0,2 Punkte für live). Der Bericht meldet
  „Bleibt an“. Der Streitpunkt vom 23.09. ist damit erledigt, ohne dass die Regel
  geändert wurde (`docs\PLAN-E41-STOP.md`, „Nachmessung 26.09.2026“).
- **E43.2-Ausschalt-Probe hält:** `auto` H1 +20,0 / H2 +4,3 gegen `bias` +23,6 / +9,5.

**Offen für Kaiser:**
1. „Go“, den Arbeitszweig nach `main` zu übernehmen? Am Handelsverhalten ändert sich
   **nichts** (`muster_cvd` bleibt `"alt"`). Es kämen: die besseren Tests (E43.5), der
   Schalter samt Gitterzeile und Berichtsabschnitt, die Unterlagen.
2. Sonderregel (Anzeige-Korrektur nur im Lage-Abruf): nicht bauen, bis E43.4 gemessen
   ist. Empfehlung der KI: danach Anzeige und Handel gemeinsam entscheiden.

**Nächster Schritt nach dem Go:** E43.4 (OI in Kontrakten statt Dollar, Befund A3):
zuerst den Bauplan-Abschnitt schreiben, dann bauen. Aufwand **hoch**.

---

## 26.09.2026 (6) — Bauplan E43.3 (Muster 2 in Dollar)

**Kaisers Auftrag:** *„Ja, bereite den Bauplan für E43.3 vor."* — reine Planung, **am
Code wurde nichts geändert**, 448 Tests weiter grün.

**Ergänzt in `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „E43.3“:**

- Genaue Fehlerdiagnose: `_slope()` dividiert die (offset-unabhängige) Fenster-Differenz
  der kumulierten CVD-Reihen durch ihren willkürlichen Startwert — dieselbe reale Lage
  klassifiziert je nach Startwert der Summe verschieden (Beleg: `demo_slope.py`,
  Prüfbericht-Anhang). Zusatzfehler: `fut_cvd` ist weiterhin BTC (A1), `classify_pattern`
  vergleicht also nebenbei BTC mit Dollar.
- Vorgeschlagene Regel: neuer Schalter `muster_cvd` (`"alt"`/`"usd"`, Default aus).
  Bei `"usd"` ersetzt eine fensterlokale, in Dollar umgerechnete Differenz (wie E43.1s
  `_fut_cvd_usd`, nur fensterlokal statt über die ganze Historie) den relativen
  `_slope()`-Vergleich — **nur in Muster 2**, Muster 1/3/4/5 bleiben unangetastet
  (ihr Vorzeichen-Vergleich ist von dem Fehler nicht betroffen).
- Entscheidungsregel vor der Messung (wie E41/E43.2) plus die Sonderregel aus Teil E:
  bringt „usd“ keine bessere Rendite, wird es trotzdem als Anzeige-Korrektur übernommen,
  der Handels-Schalter bleibt dann aus.
- Vorprobe vorgeschrieben (Vorbild E43.2s `bias_long != bias_short`): `demo_slope.py`
  muss als echter, bleibender Test verdrahtet werden, sonst ist unbewiesen, dass der
  Schalter im Datensatz überhaupt etwas ändert.
- Abhängigkeit notiert: E43.5 (A4, „mehr Historie“-Test erreicht den Muster-2-Zweig nie)
  sollte vor oder mit E43.3 repariert werden.
- Betroffene Dateien, neue Sabotage-Datei (`sabotage_e433.py`, Vorbild `sabotage_e381.py`)
  und „Bewusst NICHT“ vollständig aufgelistet — Einzelheiten im Plan, nicht hier
  wiederholt.

**Offen:** der eigentliche Bau (Aufwand **hoch** — stärkstes Modell, eigene Etappe),
danach Gitter-Messung gegen die Entscheidungsregel, dann erst Kaisers Go für `main`.

---

## 26.09.2026 (5) — Kaisers Go: E43.1 und E43.2 live in main

**Kaisers Auftrag:** *„Ich gebe das Go für main: E43.1 und E43.2, falls Go. Führe den
Merge/Cherry-Pick aus dem Arbeitszweig nach main aus, aktualisiere die
Live-Konfiguration falls nötig, prüfe die 444 main-Tests, aktualisiere UEBERGABE.md und
00_STAND.md, committe und pushe nach main."*

**Gemacht:**

- Arbeitszweig `claude/dazzling-noether-1w087b` per Fast-Forward nach `main` gemerged
  (er enthielt bereits den ganzen main-Stand als Vorfahren, kein Cherry-Pick nötig).
- **E43.1** ist reine Anzeige und lief damit sofort mit — kein Signal ändert sich.
- **E43.2 — Entscheidungsregel geprüft** (Tabelle in
  `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Fenster 18.01.–26.09.2026):
  - H1: `bias` +23,6 % gegen `auto` +20,0 % → **+3,6 Punkte besser**
  - H2: `bias` +9,5 % gegen `auto` +4,3 % → **+5,2 Punkte besser**
  - Rückgang: `bias` −9,9 % gegen `auto` −10,9 % → **1,0 Punkt flacher**, nicht tiefer

  Beide Bedingungen der vorab festgelegten Regel erfüllt → **`bein_richtung: "bias"`
  seit 26.09.2026 LIVE.**
- **Live-Konfiguration aktualisiert:** `site/data/config.json`, `bein_richtung`
  `"auto"` → `"bias"` (Hinweistext mit der Messung ergänzt).
- **Panel-Zeile in `backtest.py` mitgewandert:** `panel=True` von
  „LIVE-heute +Rueckeroberung vor dem Stop (1 Kerze)" auf
  „LIVE-heute +Bein in Handelsrichtung" verschoben. Neue Ausschalt-Probe-Zeile
  „LIVE bis 26.09.2026 (ohne Bein-Richtung)" ergänzt (Ausschalt-Regel im Kommentar).
- **Folgekorrektur, weil `bein_richtung` jetzt Teil der Live-Basis ist:** alle
  bestehenden „unterscheidet sich in genau einem Punkt von der Live-Zeile"-Zeilen
  brauchten `bein_richtung="bias"` dazu, sonst hätten sie ab jetzt zwei Unterschiede
  statt einem gemessen — betroffen: die drei Ampel-Zeilen (E34), vier Muster-5-Zeilen
  (E38), „MEINE Einstellung ohne Flush" und die beiden E41-Zeilen (Ausschalt-Probe,
  Robustheit 3-Kerzen). Die Trendfilter- und 1D-Ebene-Zeilen sind NICHT betroffen (kein
  Test hält für sie die Basis fest, absichtlich unverändert gelassen).
- **Tests entsprechend angepasst** (Vorbild E41): der Vor-Go-Test
  `test_e43_bein_richtung_zeile_hat_genau_einen_unterschied_zur_live_zeile` ist ersetzt
  durch `test_e43_bein_richtung_ist_live_und_das_panel_ist_mitgewandert` und
  `test_e43_alte_bein_richtung_unterscheidet_sich_in_genau_einem_punkt`.
- **Sabotage-Proben nachgezogen:** `sabotage_e41.py` (5 Muster) und `sabotage_e38.py`
  (1 Muster) suchten exakte Textstellen in `backtest.py`, die durch das Einfügen von
  `bein_richtung="bias"` verschoben waren („Vorlage fehlt" — die Sabotage konnte nicht
  greifen, ein stiller Ausfall). Muster an den neuen Text angepasst, dieselbe
  Sabotage-Absicht beibehalten.
- **448 Tests grün**, alle sechs Sabotage-Dateien (`sabotage_e38/e381/e39/e40/e41/e43`)
  laufen wieder vollständig und fangen alles.

**Offen:** E43.3 bis E43.7 (siehe Plan), sonst wie gehabt E41.6/E42.

---

## 26.09.2026 (4) — E43.1 und E43.2 gebaut (Arbeitszweig)

Nach Kaisers „Go“ zum Umzug (in `main` zusammengeführt) weiter nach Plan
`docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`:

- **E43.1 fertig:** Futures-CVD im Lage-Abruf jetzt in Dollar (je Kerze mit deren
  Schlusskurs umgerechnet). Reine Anzeige, kein Signal ändert sich.
- **E43.2 gebaut:** Gitterzeile „LIVE-heute +Bein in Handelsrichtung“ mit genau einem
  Unterschied zur Live-Zeile. Entscheidungsregel vorab im Plan. Backtest auf dem
  Arbeitszweig angestoßen.
- **447 Tests grün**, `sabotage_e43.py` 7 von 7 gefangen.

**Offen:** Ergebnis des Backtests auswerten; Kaisers „Go“ für `main`.

**ZWISCHENSTAND 26.09.2026, 08:20 UTC** (für den Fall eines Abbruchs):
- Zweig: `claude/dazzling-noether-1w087b`. `main` enthält den Umzug der Unterlagen,
  **nicht** E43.1/E43.2.
- Läuft: Backtest auf dem Zweig, GitHub-Lauf **36229181185** (angestoßen 08:14 UTC). Er
  committet `BACKTEST.md` auf den Zweig.
- Nächster Schritt (Aufwand **niedrig**): `git pull` auf dem Zweig, in `BACKTEST.md` die
  Zeile „LIVE-heute +Bein in Handelsrichtung“ gegen „LIVE-heute +Rueckeroberung vor dem
  Stop (1 Kerze)“ nach der Regel im Plan E43.2 prüfen (Hälftentabelle „Robustheitspruefung:
  Fenster halbiert“ und Spalte max. Rückgang). Ergebnis in Plan und hier eintragen,
  Kaiser berichten, um „Go“ bitten.
- Neu seit 26.09.: Regel „Zwischenstände sichern und Aufwand vorschlagen“
  (`ARBEITSREGELN.md`, Abschnitt Budget).
- Neu seit 26.09.: Reine Unterlagen dürfen direkt in `main`; am Ende jedes Schritts
  bekommt Kaiser den fertigen Prompt für den neuen Chat, den Aufwand und den Hinweis,
  ob er den Aufwand ändern soll. Die automatische Rückmeldung zum Backtest im alten Chat
  ist abgesagt: Die Auswertung macht ein neuer Chat (Aufwand niedrig).

---

## 26.09.2026 (3) — Umzug: Unterlagen ins Code-Repo, KI committet selbst

**Kaisers Wunsch:** *„Kannst du nicht alles so umbauen, dass du auf github commitest?“* —
und auf die Frage nach dem privaten Repo: *„das ist nur ein backup und nicht aktuell.
nehme https://github.com/szoceikaiser/btc-signal-app“*.

**Gemacht:** `docs\`, `wissens-layer\`, `STARTPROMPT.md` und `PRUEFPROMPT.md` aus dem
Backup (Stand 26.09.2026, 8:44, plus die Gesamtprüfung) ins Repo `btc-signal-app`
übernommen. Startprompt, Prüfprompt, Arbeitsregeln (Abschnitt Git), Bekannte Probleme,
Start-hier und die wichtigsten Pfade angepasst. Neue Regel: KI pusht auf einen
Arbeitszweig, `main` nur nach Kaisers „Go“.

**Bewusst NICHT übernommen** (öffentliches Repo): `Transkript.md`, `Videos\`,
`Kauftrigger.md`/`Verkaufstrigger.md` (die Daten stehen ohnehin in `backtest.py`),
`heatmap-test\`, `Claude outputs\`, `signal-app-lokal\`, die Windows-Skripte. Die
Transkripte liegen weiter auf Kaisers Rechner und im privaten Backup.

**Am Code nichts geändert.** 444 Tests grün.

---

## 26.09.2026 (2) — Gesamtprüfung aller Messungen gegen Furkans Videos

**Auftrag Kaiser:** alle Tests nochmals eingehend prüfen, ob die vorherige KI das Ganze
richtig verstanden und gebaut hat; Grundlage Transkript und Videos.

**Ergebnis:** `docs\PRUEFUNG-2026-09-26-GESAMT.md`. Kurz:

- Grundgerüst richtig (Fib-Levels, Dreipunkt-Extension, Tranchen, dynamische Zonen, keine
  Zukunftskenntnis im Backtest). Standbild 02.08. bestätigt die zwei Fib-Raster.
- **A1** Lage-Abruf: Futures-CVD kommt in BTC, steht als $ da (Faktor Kurs zu klein).
- **A2** `classify_pattern`: `spot <= fut / 3` vergleicht Anteile an einer willkürlich
  begonnenen Summe. Gleiche Lage ergibt je nach Startwert GESUNDER_TREND oder
  DERIVATE_PUMP; live wird anders summiert als im Backtest. Muster 2 wirkt live (Kaufsperre,
  5 von 10 Restverkäufen, 30 Warnungen im Lauf vom 23.09.).
- **A3** OI in $ = Kontrakte × Kurs: bei −5 % Kurs ohne eine geschlossene Position erkennt
  die Engine Kapitulation, bei +3,5 % ohne neuen Kontrakt Derivate-Pump.
- **A4** `test_mehr_historie_aendert_die_signale_nicht` erreicht den Muster-2-Zweig nie.
- **Lesefehler:** `be_im_plus` ist nicht Furkans Regel (Vorbedingung „Gewinne schon
  realisiert“ fehlt); Furkans Regel entspricht `trail_stop`.
- **Messbasis:** 16 von 25 ausgeschalteten Schaltern/Datenvarianten nie mit genau einem
  Unterschied gegen die heutige Live-Zeile gemessen. Vorneweg `bein_richtung: bias`.

**Am Code wurde nichts geändert.** 444 Tests grün. Nachstell-Skripte stehen im Anhang des
Berichts. Börsendaten waren aus der Arbeitsumgebung gesperrt: bewiesen ist der
Mechanismus, nicht die Häufigkeit im echten Fenster.

**Nächster Schritt, offen:** Kaiser entscheidet über Teil E des Berichts (Reihenfolge nach
Nutzwert, Entscheidungsregel vorab festgelegt).

---

## 26.09.2026 — Wissens-Layer aufgefrischt, Übergabe vorbereitet

**Fertig:** Alle Dateien des Wissens-Layers auf den Stand nach E41 gebracht. Neu
hinzugekommen:

- `00_STAND.md` — Kurzstand, wird künftig nach jeder Arbeit fortgeschrieben.
- `04_konventionen/BEKANNTE-PROBLEME.md` — Umgebungs- und Werkzeugfallen, getrennt von
  den inhaltlichen Befunden.
- diese Datei (`02_status/UEBERGABE.md`).
- `STARTPROMPT.md` und `PRUEFPROMPT.md` in der Repo-Wurzel.

Der Übergabeprompt stand vorher **doppelt** (in `ETAPPENPLAN.md` und in
`START-HIER.md`) und war in beiden Fassungen veraltet (174 Tests, letzte Etappe E30).
Maßgeblich ist jetzt allein `STARTPROMPT.md`; `START-HIER.md` verweist nur dorthin.

**Am Code wurde nichts geändert.** 444 Tests grün.

**Nächster Schritt, offen:** E41.6 oder E42 (siehe unten) — Kaisers Entscheidung.

---

## 23.09.2026 — Ausschalt-Regel für E41 hat angeschlagen, Kaiser hat überstimmt

**Messung** (Backtest 23.09.2026, 18:40 UTC, Fenster 15.01.–23.09.2026):

| Variante | Rendite | Rückgang | H1 | H2 | Stops |
|---|---:|---:|---:|---:|---:|
| Live: Rückeroberung 1 Kerze | +25,2 % | **−10,9 %** | +20,0 % | +4,3 % | 9 |
| Alter Stop (bis 21.09.) | +22,6 % | −9,4 % | +17,8 % | +4,1 % | 10 |
| B3 · 3 statt 1 Kerze | +26,8 % | −10,4 % | +21,4 % | +4,5 % | 9 |

Bedingung 2 der vorab festgelegten Ausschalt-Regel ist verletzt (Rückgang 1,5 statt
höchstens 1,0 Punkte tiefer). Der Bericht meldet **AUSSCHALTEN**.

**Kaisers Entscheidung:** anlassen, beim nächsten Backtest neu prüfen. Begründung,
Gegenargumente und die Kosten stehen in `docs\PLAN-E41-STOP.md`, Abschnitt „Nachmessung
23.09.2026". Im Bericht steht die Überstimmung jetzt **neben** der Ausschalt-Meldung —
die Regel wurde nicht abgeschwächt (zwei Sabotagen sichern das ab).

**Kaisers Frage „warum nicht B3 mit 3 Kerzen?" ist beantwortet** (fünf Gründe im Plan);
der stärkste: B3 hat **gleich viele Stops** wie B1 (9 gegen 9, alter Stop 10) — es ist
derselbe eine ausgelassene Stop, der Unterschied entsteht nur aus späteren Stop-Preisen.
Für einen späteren Wechsel liegt eine **vorab festgelegte Regel** im Plan (zwei Läufe,
vier Wochen Abstand, in beiden Hälften ≥ 1 Punkt besser, Rückgang nicht tiefer).

**Neue Projektlehre:** Der Fenster-Rückgang ist **zwischen zwei Varianten**
pfadabhängig — B3 wartet länger und zeigt trotzdem einen flacheren Rückgang. Daraus der
Vorschlag **E41.6**: ein Risikomaß je Position (tiefster Punkt zwischen dem alten Stop
und dem Live-Ausstieg), Schwelle vorab festgelegt. Nicht gebaut.

**Stand Code:** 444 Tests, `sabotage_e41.py` 58 Sabotagen, alle gefangen.

---

## 21.09.2026 — E41 live, STH-Kostenbasis als Anzeige

**Live geschaltet** (Kaisers Entscheidung): `stop_rueckeroberung: 1`. Der erste
4h-Schluss unter der Invalidierung stoppt nicht mehr; die Engine wartet eine Kerze auf
die Rückeroberung. Danach gilt die Marke als **geprüft** — der nächste Schluss darunter
stoppt sofort. Notbremse: mehr als 5 % unter der Marke stoppt ohne Warten. Während des
Wartens und in der Kerze der Rückeroberung wird nicht nachgekauft.

**Telegram** meldet „⏳ STOP WARTET" und „✅ MARKE ZURÜCKEROBERT"; die Plan-Nachricht
nennt die Regel in der Stop-Zeile und warnt, wenn die Engine gerade wartet.

**Drei Dinge, die erst beim Bauen auffielen** (alle behoben, im Plan dokumentiert):
die Merker mussten in `state.json` (sonst käme der Stop live nie), der 0,786-Nachkauf
hätte nach einer Rückeroberung zu einem nie existierenden Preis gebucht, und die
Nachkaufsperre muss auch die Kerze der Rückeroberung umfassen.

**Ebenfalls fertig:** die **STH-Kostenbasis** steht als Zeile im Lage-Abruf (Wert,
Abstand in Prozent, Datum, „Nur Anzeige, keine Regel"). Quelle bitview.space, Ersatz
bitcoin-data.com. Als *Regel* ist sie nicht prüfbar: 84 % der Kerzen lagen darunter, nur
7 Wechsel im Fenster — E40.2/E40.3 wurden deshalb nicht gebaut.

**Ebenfalls fertig:** E38 (Muster 5) ist entschieden — das Signal ist echt, die Engine
kann es nicht benutzen, weil sie nur an Fib-Zonen entscheidet. Alle Schalter aus, nur
der Text in den Nachrichten wurde ersetzt und die Ampel zählt Muster 5 neutral.

**Gitter umgebaut:** Panel-Zeile ist jetzt „LIVE-heute +Rückeroberung vor dem Stop
(1 Kerze)". Neu: „LIVE bis 21.09.2026 (Stop ohne Rückeroberung)" als Ausschalt-Probe und
„Rückeroberung 3 statt 1 Kerze" als Robustheitsprüfung. A (Puffer 0,5 %) und C (Docht)
sind nach der Messung aus dem Gitter genommen.

---

## Was als Nächstes offen liegt

Vollständig und nach Nutzwert sortiert: `02_status/OFFENE-PUNKTE.md`. Die beiden
naheliegenden Vorhaben:

1. **E41.6 — pfadunabhängiges Risikomaß.** Für jeden Stop des alten Stops den tiefsten
   Punkt messen, den die Position live danach noch sah. Damit ließe sich die
   Ausschalt-Bedingung als „zusätzlicher Buchverlust je Position" fassen statt als
   Fenster-Rückgang. Schwelle **vor** der Messung festlegen. Grundlage:
   `docs\PLAN-E41-STOP.md`, Abschnitt E41.6.
2. **E42 — Ausbruch mit Rücktest** (Kaisers zweite Regel, wörtlich im Plan E41
   zitiert): Die Engine verkauft heute kurz unter dem letzten Hoch (`high_exit: on`).
   Bricht der Kurs durch und hält beim Rücktest (Schluss nicht mehr darunter, höchstens
   der Docht), sind weitere Gewinne zu erwarten — zurückkaufen oder den Rest halten?
   Eigene Etappe, weil es in E41 einen zweiten Unterschied pro Gitterzeile erzeugt
   hätte. Noch kein Bauplan.

**Vier Schalter hängen seit Monaten unentschieden** (`confirm_t1`, `cooldown_h`,
`be_im_plus`, `release_stale_rest`) — sie wurden nie mit **genau einem** Unterschied
gegen die heutige Basis gemessen. Zwei saubere Gitterzeilen würden das klären.
