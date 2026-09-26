# Bauplan E43 — Korrekturen aus der Gesamtprüfung vom 26.09.2026

> Grundlage: `docs/PRUEFUNG-2026-09-26-GESAMT.md` (Teil A: Befunde, Teil E: Vorschlag).
> Auftrag Kaiser, 26.09.2026: *„es wurden bisher sehr viele test gemacht und zum teil
> verworfen … ich möchte, das du alle test nochmals eingehend prüft, ob die vorherige ki
> das ganze richtig verstanden und gebaut hat."* Nach dem Bericht: „Go“.
>
> Arbeitsweise (seit 26.09.2026): gebaut wird auf dem Arbeitszweig `claude/...`. In `main`
> (live) kommt jede Etappe erst nach Kaisers ausdrücklichem „Go“.

## Etappen (Reihenfolge = Nutzwert)

| Etappe | Inhalt | Art | Aufwand | Status |
|---|---|---|---|---|
| E43.1 | Futures-CVD im Lage-Abruf in Dollar (Befund A1) | reine Anzeige | mittel | **LIVE** seit 26.09.2026 (Kaisers Go, in `main` gemerged) |
| E43.2 | Gitterzeile „LIVE-heute +Bein in Handelsrichtung“, genau ein Unterschied | Messung, kein neuer Schalter | Auswertung: **niedrig** | **LIVE** seit 26.09.2026 (`bein_richtung: "bias"`, Entscheidungsregel erfüllt, Kaisers Go) |
| E43.3 | Muster 2 vergleicht Dollar-Beträge statt Anteile an einer willkürlichen Summe (A2) | Schalter, Default aus | **hoch** | **BAUPLAN FERTIG** 26.09.2026, Bau OFFEN |
| E43.4 | Open Interest in Kontrakten statt Dollar (A3) | Schalter, Default aus | **mittel bis hoch** | OFFEN |
| E43.5 | Test „mehr Historie“ summiert neu und erreicht den Muster-2-Zweig (A4) | Test | mittel | OFFEN |
| E43.6 | Nachmessung mit genau einem Unterschied: `rest_halten`, `strict_confirm`, `confirm_t1`, `cooldown_h`; danach Muster 5 wiederholen | Messung | **niedrig** | OFFEN |
| E43.7 | Wissens-Layer berichtigen (`be_im_plus`, E37-Satz, Funding-Einheit) | Text | **niedrig** | OFFEN |

### Aufwand je Etappe (Kaisers Wunsch 26.09.2026: Tokens sparen, wo es geht)

| Stufe | Modell / Denkaufwand | Wann |
|---|---|---|
| **niedrig** | kleines oder mittleres Modell, niedriger Denkaufwand | Backtest anstoßen und eine Tabelle nach einer **vorab festgelegten** Regel auswerten; Gitterzeilen nach Vorlage; Texte berichtigen. Lesen: nur `00_STAND.md`, jüngster Abschnitt `UEBERGABE.md`, dieser Plan |
| **mittel** | mittleres Modell, normaler Denkaufwand | kleine Code-Änderung mit Test und Sabotage, die kein Signal ändert (Anzeige, Test-Reparatur) |
| **hoch** | stärkstes Modell, hoher Denkaufwand | Änderung an der Handelslogik oder Mustererkennung: Live und Backtest müssen gleich rechnen, Tests brauchen Vorprobe und Sabotage |
| **maximal** | stärkstes Modell, maximaler Denkaufwand | Gesamtprüfungen, neue Mechanismen aus Furkans Videos (E42), Entscheidungsregeln für Live-Schaltungen, E41.6 |

**Sparregeln:** Eine Etappe je Chat — lange Chats werden mit jeder Nachricht teurer.
`BACKTEST.md` nie ganz lesen, nur die betroffenen Zeilen (Suche nach dem Zeilennamen).
`GEMESSEN-UND-ENTSCHIEDEN.md` (42 KB) nur lesen, wenn etwas Neues vorgeschlagen wird.

## E43.1 — Futures-CVD in Dollar (Anzeige)

**Problem:** `fut_cvd` kommt von Coinalyze `ohlcv-history` in **BTC** (die Schnittstelle
ignoriert `convert_to_usd`). `orderflow_detail()` gab den Wert trotzdem mit „$“ aus und
rechnete den Anteil am Spot-Flow als BTC geteilt durch Dollar. Beides war um den Faktor
Kurs zu klein.

**Regel:** Jedes Kerzen-Delta wird mit dem Schlusskurs **derselben** Kerze in Dollar
umgerechnet, dann wird summiert. Fehlt zu einem Flow-Punkt die Kerze, entfällt die Zeile
(lieber keine Zeile als eine falsche).

**Betroffen:** `engine/strategy_core.py` (`orderflow_detail`, neue Hilfsfunktion
`_fut_cvd_usd`), `engine/test_main.py` (der alte Test hielt den Fehler fest und wird
berichtigt), neue Sabotage-Probe `engine/sabotage_e43.py`.

**Bewusst NICHT:** `FlowPoint.fut_cvd` bleibt in BTC. `classify_pattern` liest die Reihe
weiter wie bisher, das ändert erst E43.3, und zwar als Schalter. E43.1 ändert kein Signal.

## E43.2 — „Bein in Handelsrichtung“ gegen die heutige Live-Zeile

**Problem:** `bein_richtung: "bias"` entspricht Furkans zwei Fib-Rastern (Standbild
02.08.2026 16:12: Kaufzonen aus dem großen Aufwärts-Bein 57.802 → 66.940, Widerstand aus
dem kleinen Abwärts-Bein). Gemessen wurde er nur gegen die Live-Zeile vom 27.08.2026. Im
Lauf vom 23.09.2026 war die alte Zeile die beste des Gitters (+32,2 % gegen +25,4 %),
in den Hälften aber H1 nur +0,5 (Rauschen) und H2 +5,2.

**Regel:** eine Zeile `LIVE-heute +Bein in Handelsrichtung`, die sich von der
`panel=True`-Zeile in **genau einem** Punkt unterscheidet (`bein_richtung="bias"`). Ein
Test hält das fest.

**Entscheidungsregel, festgelegt VOR der Messung (26.09.2026):** `bein_richtung: "bias"`
geht nur live, wenn die Zeile gegen die Live-Zeile
1. in **beiden** Fensterhälften um **mindestens 1 Punkt** besser ist, **und**
2. der maximale Rückgang **nicht mehr als 1 Punkt** tiefer liegt.

Sonst bleibt `auto`. Geht der Schalter live, gilt die **Ausschalt-Regel**: aus, wenn die
alte Einstellung (`auto`) in beiden Hälften um mindestens 1 Punkt besser ist oder der
Rückgang live mehr als 1 Punkt tiefer liegt. Der Bericht prüft das dann selbst (wie bei E41).

**Einschränkung, vorab benannt:** Der Rückgangsvergleich zwischen zwei Varianten ist
pfadabhängig (Lehre vom 23.09.2026). Er bleibt trotzdem Teil der Regel, bis E41.6 ein
besseres Maß liefert — die Regel wird nicht nachträglich gelockert.

**Bewusst NICHT:** keine Kombination mit anderen Schaltern in derselben Zeile; kein
Nachjustieren von `min_bein_pct`.

**Messung gegen die Entscheidungsregel (26.09.2026, Fenster 18.01.–26.09.2026):**

| Bedingung | H1 (bis 24.05.) | H2 (danach) | Rückgang (Vollfenster) |
|---|---:|---:|---:|
| `bein_richtung="bias"` | +23,6 % | +9,5 % | −9,9 % |
| Live-Zeile (`auto`) | +20,0 % | +4,3 % | −10,9 % |
| Unterschied | **+3,6 Punkte** | **+5,2 Punkte** | **1,0 Punkt flacher** |

Bedingung 1 (beide Hälften ≥ 1 Punkt besser) erfüllt, Bedingung 2 (Rückgang nicht mehr als
1 Punkt tiefer) erfüllt — der Rückgang ist sogar flacher, nicht tiefer. **Kaisers Go
26.09.2026: `bein_richtung: "bias"` LIVE seit 26.09.2026** (`site/data/config.json`,
Panel-Zeile in `backtest.py` mitgewandert auf `LIVE-heute +Bein in Handelsrichtung`, alte
Panel-Zeile ohne Namensänderung stehen gelassen, neue Ausschalt-Probe-Zeile
`LIVE bis 26.09.2026 (ohne Bein-Richtung)` ergänzt). Ausschalt-Regel wie oben beschrieben,
der Bericht prüft sie künftig selbst (wie bei E41).

## Umsetzung E43.1 und E43.2 (26.09.2026)

- `strategy_core._fut_cvd_usd()` rechnet jedes Kerzen-Delta mit dem Schlusskurs derselben
  Kerze in Dollar um; `orderflow_detail()` nutzt sie für die Futures-Zeile. Kein Signal
  ändert sich (`evaluate()` ruft `orderflow_detail()` nicht auf).
- Der alte Test `test_futures_cvd_zeigt_das_verhaeltnis_zum_spot` hielt den Fehler fest
  (600 BTC galten neben 15 Mio $ als „verschwindend“). Berichtigt: 600 BTC × 80.000 $ =
  48 Mio $ je Kerze → „320 % des Spot-Flows“, Wert „+576,0 Mio $“.
- Neu: `test_futures_cvd_rechnet_jede_kerze_mit_ihrem_eigenen_kurs` (Kurs verdoppelt sich
  im Fenster), `test_futures_cvd_ohne_passende_kerze_entfaellt`,
  `test_e43_bein_richtung_zeile_hat_genau_einen_unterschied_zur_live_zeile` (mit Vorprobe:
  der Schalter wirkt nur, wenn genau eine Richtung erlaubt ist).
- Gitterzeile `LIVE-heute +Bein in Handelsrichtung` in `backtest.py`.
- **447 Tests grün.** `sabotage_e43.py`: 7 Sabotagen, alle gefangen.

## Go 26.09.2026: E43.1 und E43.2 in main, E43.2 live geschaltet

- Arbeitszweig `claude/dazzling-noether-1w087b` per Fast-Forward nach `main` gemerged.
- E43.1 ist reine Anzeige und lief sofort mit (kein Signal ändert sich).
- E43.2: Entscheidungsregel erfüllt (Tabelle oben) → `bein_richtung: "bias"` in
  `site/data/config.json` gesetzt (war `"auto"`), `panel=True` in `backtest.py` von der
  Rückeroberungs-Zeile auf `LIVE-heute +Bein in Handelsrichtung` verschoben, neue
  Ausschalt-Probe-Zeile `LIVE bis 26.09.2026 (ohne Bein-Richtung)` ergänzt.
- Der vorab-Test `test_e43_bein_richtung_zeile_hat_genau_einen_unterschied_zur_live_zeile`
  ist durch zwei Nach-Go-Tests ersetzt (Vorbild E41):
  `test_e43_bein_richtung_ist_live_und_das_panel_ist_mitgewandert`,
  `test_e43_alte_bein_richtung_unterscheidet_sich_in_genau_einem_punkt`.
- Da `bein_richtung` jetzt Teil der Live-Basis ist, mussten alle bestehenden
  „unterscheidet sich in genau einem Punkt von der Live-Zeile"-Gitterzeilen um
  `bein_richtung="bias"` ergänzt werden (Ampel ×3, Muster 5 ×5, E41-Ausschalt-Probe,
  E41-Robustheit, „MEINE Einstellung ohne Flush") — sonst hätten sie neu zwei
  Unterschiede statt einem gemessen.
- **448 Tests grün** (444 in `main` vor dem Merge, 447 auf dem Arbeitszweig, +1 durch die
  Aufspaltung des E43.2-Tests). `sabotage_e43.py`: weiterhin 7 von 7 gefangen.

## E43.3 — Muster 2 vergleicht Dollar-Beträge im Fenster statt Anteile an einer
willkürlichen Summe (Befund A2)

**Noch nicht gebaut.** Dieser Abschnitt ist der Bauplan (Regel, Schalter, betroffene
Dateien, Entscheidungsregel) — Kaisers Zustimmung dazu ist eingeholt (26.09.2026: „Ja,
bereite den Bauplan vor"), der Bau selbst noch nicht.

**Problem, genau lokalisiert** (`strategy_core.classify_pattern`, Muster 2):

```python
spot = _slope([p.spot_cvd for p in f])   # f = flow[-window:], window = 12 Kerzen
fut  = _slope([p.fut_cvd  for p in f])
...
if price_chg > 0 and fut > 0 and spot <= fut / 3 and oi_chg >= 0.03 and (...):
    return Pattern.DERIVATE_PUMP
```

`_slope(vals) = (vals[-1] - vals[0]) / abs(vals[0])`. `spot_cvd`/`fut_cvd` sind
**kumulierte** Reihen, die irgendwo weit vor dem 12-Kerzen-Fenster zu laufen begonnen
haben (bei welchem Kerzenindex, hängt davon ab, wie weit `flow` zurückreicht — live seit
Engine-Start, im Backtest seit Fensteranfang: **verschieden**). Der Zähler
`vals[-1] - vals[0]` ist unabhängig von diesem Startpunkt (ein konstanter Offset kürzt
sich heraus), die Division durch `abs(vals[0])` **zerstört genau diese Unabhängigkeit**:
derselbe reale Geldfluss im Fenster ergibt, je nachdem wo die kumulierte Summe zu laufen
begann, einen kleinen oder einen riesigen `_slope()`-Wert. Beleg (`demo_slope.py`,
Anhang `docs/PRUEFUNG-2026-09-26-GESAMT.md`): identischer Verlauf von Kurs, OI und
Funding, nur der Startwert der beiden kumulierten Reihen geändert →
`GESUNDER_TREND, GESUNDER_TREND, DERIVATE_PUMP, DERIVATE_PUMP`. Zusatzfehler: `fut_cvd`
kommt weiterhin in BTC (Coinalyze, Befund A1) — `classify_pattern` vergleicht also BTC
mit Dollar, wenn auch nur über den ohnehin kaputten Umweg der relativen Slopes.

**Regel:** neuer Schalter `muster_cvd`, Werte `"alt"` (Default, heutiges Verhalten
unverändert) | `"usd"` (Korrektur, betrifft **nur Muster 2**):

- `fut_delta_usd` = Summe der pro Kerze in Dollar umgerechneten Futures-Deltas
  **innerhalb des Fensters** — dieselbe Umrechnung wie `_fut_cvd_usd()` (E43.1: jedes
  Kerzen-Delta mit dem Schlusskurs derselben Kerze multiplizieren, dann erst
  aufsummieren), aber fensterlokal statt über die ganze Historie.
- `spot_delta_usd` = `f[-1].spot_cvd - f[0].spot_cvd` — `spot_cvd` ist laut
  `FlowPoint`-Vertrag bereits in Dollar; statt der relativen `_slope()` zählt die
  **absolute** Fenster-Differenz (offset-unabhängig, siehe oben).
- Vergleich in Muster 2 bei `"usd"`: `spot_delta_usd <= fut_delta_usd / 3` — dieselbe
  Verhältnis-Logik wie bisher, jetzt mit zwei tatsächlich vergleichbaren
  Dollar-Größen statt zweier unabhängig-willkürlich skalierter Prozentwerte.
- **Nur Muster 2 ändert sich.** Muster 1 (`spot > 0`) und Muster 5 (`spot < 0`) bleiben
  unangetastet: Das Vorzeichen von `_slope()` stimmt immer mit dem Vorzeichen der
  Fenster-Differenz überein (Division durch `abs(vals[0])` kann das Vorzeichen nicht
  drehen) — betroffen ist ausschließlich der Magnituden-Vergleich `spot <= fut/3`.
- Ohne Futures-Quelle (`has_fut == False`, US-Geo-Block-Zweig): unverändert: dort gibt
  es keine Futures-Reihe umzurechnen, `muster_cvd` wirkt dort nicht.

**Entscheidungsregel, festgelegt VOR der Messung (wie E41/E43.2):** `muster_cvd: "usd"`
geht nur live (Default wechselt von `"alt"` auf `"usd"`), wenn die Zeile gegen die
heutige Live-Zeile (`bein_richtung="bias"`, seit 26.09.2026 live)
1. in **beiden** Fensterhälften um **mindestens 1 Punkt** besser ist, **und**
2. der maximale Rückgang **nicht mehr als 1 Punkt** tiefer liegt.

**Sonderregel für A2/A3 (Teil E des Prüfberichts, gilt auch hier):** Liefert `"usd"`
**keine** bessere Rendite, wird die Korrektur trotzdem als **Anzeige-Korrektur**
übernommen — die Musterzeile im Lage-Abruf soll dieselbe Definition benutzen wie
`evaluate()`, unabhängig vom Handels-Ergebnis. Der Handels-Schalter (`muster_cvd`
selbst) bleibt dann auf `"alt"`.

**Vorprobe, vor der eigentlichen Gitter-Messung:** nachweisen, dass der Schalter im
Datensatz überhaupt greift — `demo_slope.py` aus dem Prüfbericht-Anhang als echten,
bleibenden Test verdrahten (zwei Szenarien mit identischem Kurs/OI/Funding-Verlauf,
nur verschiedenem Startwert der kumulierten Reihen, müssen bei `"alt"` verschieden und
bei `"usd"` gleich klassifizieren). Ohne diese Vorprobe wäre die Gitterzeile eine Kopie
der Live-Zeile und die Messung bedeutungslos (dieselbe Lehre wie bei E43.2s
`bias_long != bias_short`-Vorprobe).

**Abhängigkeit zu E43.5 (A4):** `test_mehr_historie_aendert_die_signale_nicht` erreicht
den Muster-2-Zweig laut Prüfbericht nie — das sollte vor oder zusammen mit E43.3
repariert werden, sonst bleibt unklar, ob der Zweig im bestehenden Testfenster überhaupt
je ausgelöst wird.

**Betroffene Dateien (geplant):**

- `engine/strategy_core.py` — `classify_pattern()` bekommt den Parameter
  `muster_cvd: str = "alt"`; bei `"usd"` die neue fensterlokale Dollar-Rechnung für
  Muster 2 (neue Hilfsfunktion, z. B. `_muster2_dollar(candles, flow, window)`, analog
  zu `_fut_cvd_usd`, aber fensterlokal für beide Reihen). `evaluate()` muss den
  Parameter zu jedem `classify_pattern()`-Aufruf durchreichen.
- `engine/main.py` — `EVAL_DEFAULTS`: neuer Schlüssel `"muster_cvd": "alt"`.
- `engine/backtest.py` — `EVAL_KEYS` ergänzen; neue Gitterzeile
  `LIVE-heute +Muster 2 in Dollar (E43.3)`, geklont von der **aktuellen** Panel-Zeile
  (also inklusive `bein_richtung="bias"`, `stop_rueckeroberung=1` usw.) plus **genau**
  `muster_cvd="usd"` als einzigem Unterschied.
- `engine/test_strategy_core.py` — Vorprobe-Test (siehe oben) und ein Test, der beweist,
  dass `muster_cvd` bei `evaluate()` ankommt (Vorbild
  `test_ampel_filter_kommt_im_backtest_ueberhaupt_an`).
- `engine/test_backtest.py` — Gitterzeilen-Test „genau ein Unterschied zur Live-Zeile"
  (Vorbild `test_e43_bein_richtung_ist_live_und_das_panel_ist_mitgewandert`).
- Neue Sabotage-Datei `engine/sabotage_e433.py` (Vorbild `sabotage_e381.py`), mindestens:
  Schalter fehlt in `EVAL_KEYS`/kommt nicht an; die `"usd"`-Rechnung rechnet doch nicht
  mit dem Kerzenpreis (bleibt BTC); Vorzeichen-/Verhältnis-Fehler in der neuen
  Vergleichslogik; Gitterzeile hat zwei Unterschiede statt einem; die Entscheidungsregel
  selbst ist falsch herum oder eine Bedingung fehlt (Vorbild der acht
  „Ausschalten:…"-Sabotagen in `sabotage_e41.py`).
- `site/data/config.json` — neuer Schlüssel `"muster_cvd": "alt"` +
  `_hinweis_muster_cvd` (Default AUS, „Erst nach Backtest-Messung einschalten").

**Bewusst NICHT:**

- keine Anpassung der bestehenden Schwellen (`oi_chg >= 0.03`, `funding_hot`,
  `sharp_move_pct` …) über die Korrektur hinaus — das wäre Nachjustieren an der
  Vergangenheit.
- Muster 1, 3, 4, 5 bleiben unverändert.
- der US-Geo-Block-Zweig (ohne Futures-Quelle) bleibt unverändert.
- kein gleichzeitiges Anfassen von A3/OI (das ist E43.4) — ein Unterschied je Zeile,
  sonst weiß man hinterher nicht, was gewirkt hat.

## E43.4 bis E43.7

Werden vor dem Bau hier ergänzt (Regel, Schwellen, betroffene Dateien, Entscheidungsregel).
Stichpunkte stehen in `docs/PRUEFUNG-2026-09-26-GESAMT.md`, Teil E.
