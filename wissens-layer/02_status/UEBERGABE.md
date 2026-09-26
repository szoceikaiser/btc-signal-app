# Laufende Übergabe

> Was zuletzt passiert ist, was offen liegt, was eine neue Session als Erstes wissen
> muss. **Jüngster Abschnitt oben.** Nach jeder abgeschlossenen Arbeit einen datierten
> Abschnitt hier ergänzen — nicht erst am Ende eines Vorhabens.
>
> Kurzfassung: `00_STAND.md`. Fertiger Prompt für einen neuen Chat: `STARTPROMPT.md`.

---

## 26.09.2026 (7) — E43.5 und E43.3 gebaut (Arbeitszweig)

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

**Nächster Schritt:** Backtest auf dem Arbeitszweig auswerten: Abschnitt „E43.3“ in
`BACKTEST.md` lesen (Urteil steht dort), dazu den E41-Abschnitt auf der neuen
Live-Basis (`bein_richtung: "bias"`). Aufwand **niedrig**.

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
