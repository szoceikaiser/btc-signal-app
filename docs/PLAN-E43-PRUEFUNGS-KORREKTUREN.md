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
| E43.3 | Muster 2 vergleicht Dollar-Beträge statt Anteile an einer willkürlichen Summe (A2) | Schalter, Default aus | **hoch** | **GEMESSEN** 26.09.2026: 2 von 1.504 Kerzen anders, Rendite identisch, Regel nicht erfüllt → bleibt `"alt"` (Arbeitszweig) |
| E43.4 | Open Interest in Kontrakten statt Dollar (A3) | Schalter, Default aus | **hoch** | **GEMESSEN** 26.09.2026: 210 von 1.504 Kerzen anders, Rendite identisch, Regel nicht erfüllt → bleibt `"usd"`. Seit 26.09.2026 in `main` (Kaisers Go), 488 Tests, `sabotage_e434.py` 37/37 |
| E43.4b | OI-Zeile im Lage-Abruf zeigt die Kontrakte neben den Dollar (A3 in der Anzeige) | reine Anzeige | mittel | **LIVE** seit 26.09.2026 (Kaisers Go, in `main`), 493 Tests, `sabotage_e434b.py` 9/9 |
| E43.5 | Test „mehr Historie“ summiert neu und erreicht den Muster-2-Zweig (A4) | Test | mittel | **FERTIG** 26.09.2026 (Arbeitszweig, noch nicht in `main`), 450 Tests, `sabotage_e433.py` 5/5 |
| E43.6 | Nachmessung mit genau einem Unterschied: `rest_halten`, `strict_confirm`, `confirm_t1`, `cooldown_h` | Messung | **niedrig** | **GEMESSEN** 26.09.2026 (GitHub-Actions-Backtest, Arbeitszweig `claude/e43-6-gitterzeilen-eo6mzb`), 501 Tests grün. Alle vier Schalter erfüllen die Entscheidungsregel nicht → bleiben aus (siehe Abschnitt E43.6, „Messung 26.09.2026“) |
| E43.7 | Wissens-Layer berichtigen (`be_im_plus`, E37-Satz, Funding-Einheit) | Text | **niedrig** | **FERTIG** 26.09.2026 (`wissens-layer/02_status/GEMESSEN-UND-ENTSCHIEDEN.md`), reine Textkorrektur, 501 Tests unverändert grün |

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

### Ergänzungen zum E43.3-Bauplan (26.09.2026, beim Bau, vor jeder Messung)

Beim Lesen des Codes vor dem Bau gefunden. Die Regel oben ändert sich dadurch nicht, sie
wird nur genauer:

- **„Futures steigt“ bei `"usd"`:** Die Bedingung `fut > 0` prüft bei `"usd"` die
  Dollar-Summe `fut_delta_usd > 0`, damit beide Seiten des Vergleichs in derselben
  Einheit stehen. Das Vorzeichen stimmt fast immer mit dem der BTC-Differenz überein.
  Nur bei stark wechselnden Kerzen-Deltas und großer Kursbewegung im Fenster kann es
  abweichen.
- **Fehlt zu einem Flow-Punkt im Fenster die Kerze** (gleiche `ts`), gibt es keine
  Dollar-Summe. Dann wird kein Derivate-Pump erkannt: lieber keine Warnung als eine
  mit falschem Kurs (dieselbe Haltung wie `_fut_cvd_usd`). Live und im Backtest werden
  Kerze und Flow-Punkt in derselben Schleife gebaut, der Fall tritt dort nicht auf.
- **Anzeige = Handel:** Die drei `classify_pattern`-Aufrufe für Lage-Abruf, Vorschau und
  Plan in `main.py` bekommen denselben `muster_cvd`-Wert wie `evaluate()`. Solange der
  Schalter auf `"alt"` steht, ändert sich dort nichts. **Offen für Kaiser nach der
  Messung:** Die Sonderregel (Anzeige-Korrektur auch ohne Rendite-Gewinn) hieße, dass
  die Anzeige `"usd"` rechnet, der Handel aber `"alt"`. Dann stünde im Lage-Abruf
  gelegentlich ein anderes Muster als das, nach dem die Engine gehandelt hat. Dafür
  bräuchte es einen eigenen Anzeige-Schlüssel. Er wird erst gebaut, wenn Kaiser das
  nach der Messung so will.
- **Grenze, bewusst nicht behoben:** Die E37-Datenvarianten „Spot-CVD aggregiert“ und
  „ALLES aggregiert“ führen das Spot-CVD in **BTC** (`coinalyze.spot_delta_aggregiert`),
  nicht in Dollar. Mit `"usd"` würden dort BTC und Dollar verglichen. Sie laufen mit
  der Panel-Einstellung, also mit `"alt"`, solange der Schalter aus ist. Geht `"usd"`
  live, müssen diese Varianten ihr Spot-Delta vorher in Dollar umrechnen (eigene
  Folgeetappe, hier vermerkt, damit es nicht vergessen wird).
- **Vorprobe im echten Datensatz:** Der Backtest-Bericht bekommt einen Abschnitt
  „E43.3“, der (1) zählt, an wie vielen Kerzen im Fenster `"alt"` und `"usd"`
  verschiedene Muster ergeben, und (2) die Entscheidungsregel oben selbst prüft
  (Vorbild `e41_abschnitt`). Ist die Zahl der umklassifizierten Kerzen 0, misst die
  Gitterzeile nichts, und der Bericht sagt das.

### Umsetzung E43.3 (26.09.2026, Arbeitszweig, noch nicht gemessen)

- `strategy_core.py`: `_muster2_dollar()` (Spot- und Futures-Delta im Fenster in Dollar,
  Futures je Kerze mit deren Schlusskurs), `classify_pattern(..., muster_cvd="alt")`,
  `evaluate(..., muster_cvd="alt")` reicht den Wert weiter. Bei `"alt"` rechnet alles
  wie bisher.
- `main.py`: `EVAL_DEFAULTS["muster_cvd"] = "alt"`; Lage-Abruf, Vorschau und Plan rechnen
  das Muster mit demselben Wert wie der Handel.
- `backtest.py`: `muster_cvd` in `EVAL_KEYS` und `_BASE`; Gitterzeile
  „LIVE-heute +Muster 2 in Dollar (E43.3)“ mit genau einem Unterschied; Berichtsabschnitt
  „E43.3“ mit Vorprobe im Datensatz (`e433_umklassifiziert`) und Urteil nach der
  Entscheidungsregel (`e433_einschalten`).
- `site/data/config.json`: `"muster_cvd": "alt"` plus `_hinweis_muster_cvd`.
- **Tests:** 17 neue, zusammen mit E43.5 jetzt **467 grün**. Darunter die verdrahtete
  Vorprobe `demo_slope` (bei `"alt"` GESUNDER_TREND, GESUNDER_TREND, DERIVATE_PUMP,
  DERIVATE_PUMP wie im Prüfbericht; bei `"usd"` viermal GESUNDER_TREND) und der Kern:
  Mit `"usd"` erkennt die Engine bei 400 und 1.200 geladenen Kerzen dieselben Muster
  (im Pump-Szenario 16 gegen 16 Derivate-Pumps; bei `"alt"` 8 gegen 3).
- **Die Vorprobe im Bericht rechnet richtig**, bewiesen im Szenario: Mit einem alten
  Spot-Abfluss vor dem Live-Ladefenster hätte die Live-Engine mit `"alt"` an 47 von 500
  Kerzen ein anderes Muster gesehen als der Backtest, mit `"usd"` an 0.
- **Sabotage:** `sabotage_e433.py`, 29 Sabotagen. Beim ersten Lauf blieb eine
  ungefangen („Futures steigt“ fehlt bei `"usd"`). Dafür kam der Test
  `test_e433_fallende_futures_sind_kein_pump` dazu, danach war auch sie gefangen.

### Messung E43.3 (26.09.2026, GitHub-Lauf 36233723729, Fenster 18.01.–26.09.2026)

| Variante | Rendite | Rückgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live (`alt`)** | +35,3 % | −9,9 % | +23,6 % | +9,5 % | 244 |
| Muster 2 in Dollar (`usd`) | +35,3 % | −9,9 % | +23,6 % | +9,5 % | 244 |

- **Vorprobe im Datensatz:** 1.504 Kerzen im Fenster. Derivate-Pump mit `alt` an 96,
  mit `usd` an 94 Kerzen. **Verschieden erkannt: 2 Kerzen.** Die Zeile misst also etwas,
  nur fast nichts.
- **Live gegen Backtest** (1.175 nachstellbare Kerzen): Mit `alt` hätte die Live-Engine
  an **1** Kerze ein anderes Muster gesehen als der Backtest, mit `usd` an **0**.
  Befund A2 ist im echten Datensatz also bestätigt, aber klein.
- **Urteil nach der vorab festgelegten Regel:** in beiden Hälften ≥ 1 Punkt besser:
  **nein** (H1 ±0,0, H2 ±0,0). Rückgang: gleich. **Regel nicht erfüllt, `muster_cvd`
  bleibt auf `"alt"`.**
- **Einordnung:** Kein Renditebefund, weder dafür noch dagegen. Die Sorge aus dem
  Prüfbericht („Dieselbe Lage ergibt Furkans bestes Muster oder sein Warnmuster“) stimmt
  im Prinzip, betrifft in acht Monaten aber nur zwei Kerzen und kein einziges Signal
  im Ergebnis. Die bisherigen Urteile, die an Muster 2 hängen, verlieren durch A2 also
  praktisch nichts. **A3 (OI in Dollar, E43.4) ist damit der größere offene Hebel** der
  Mustererkennung.
- **Offen für Kaiser — Sonderregel (Prüfbericht Teil E):** die Korrektur nur in der
  Anzeige übernehmen. Das bräuchte einen eigenen Anzeige-Schlüssel. Anzeige und Handel
  würden dann an wenigen Kerzen (hier 2 von 1.504) verschieden erkennen.

## E43.5 — Der Test „mehr Historie“ summiert je Ladefenster neu und erreicht Muster 2 (Befund A4)

**Kaisers Auftrag 26.09.2026:** *„Ja, bau E43.5 und E43.3“*. E43.5 kommt zuerst, weil
E43.3 ohne ein Szenario, das Muster 2 erreicht, nichts beweisen kann.

**Problem (Prüfbericht A4):** `test_mehr_historie_aendert_die_signale_nicht` schneidet
**eine** vorgerechnete CVD-Liste verschieden weit aus. Live beginnt die Summe bei jedem
Lauf neu bei null, und zwar ab der ersten geladenen Kerze. Außerdem erreicht das Szenario
Muster 2 nie (OI +0,6 % je zwei Tage, Funding konstant). Zusätzlich beim Lesen gefunden:
Die im Test hartcodierte „Live-Einstellung“ ist veraltet. Es fehlen
`stop_rueckeroberung: 1` (live seit 21.09.) und `bein_richtung: "bias"` (live seit 26.09.).

**Regel für den Test:**

1. Der bestehende Test summiert das CVD je Ladefenster ab null (wie `main.fetch_data`).
   Die Live-Einstellung kommt aus der Panel-Zeile des Gitters, die ein anderer Test
   gegen `config.json` prüft, statt aus einer eigenen, veraltenden Liste. Sein Zweck
   bleibt E33-A (Pivots, EMA, Zonen), Muster 2 ist dort ausdrücklich nicht gedeckt.
2. Neues Szenario mit Pump-Phasen: Kurs, Futures-Delta, OI (+0,6 % je Kerze) und
   Funding steigen gemeinsam, Spot kaum. Dazwischen schwanken Spot- und Futures-Delta
   langsam, damit die kumulierten Summen je nach Startpunkt verschieden groß sind.
3. **Vorprobe (Regel 2):** In den letzten 60 Kerzen erfüllt das Szenario mehrfach alle
   Muster-2-Voraussetzungen außer dem strittigen Größenvergleich, und `classify_pattern`
   erkennt in **beiden** Ladefenstern mindestens einmal DERIVATE_PUMP.
4. **Befund A2 als Test:** Mit der heutigen Rechnung ergeben Ladefenster 400 und 1200
   verschiedene Muster, und **jede** abweichende Kerze hat auf einer Seite
   DERIVATE_PUMP. Damit ist bewiesen, dass die Abweichung genau aus Muster 2 kommt.
   E43.3 muss diesen Unterschied bei `"usd"` zum Verschwinden bringen, bei `"alt"` muss
   er bleiben.

**Neuer Nebenbefund beim Bau (26.09.2026, noch nicht behoben):** Mit dem Pump-Szenario
unterscheiden sich die Signale zwischen Ladefenster 400 und 1200 auch an einer Stelle,
die mit Muster 2 nichts zu tun hat: „Teilgewinn am letzten Hoch“. `next_pivot_beyond()`
nimmt das nächste Pivot-Hoch über dem Kurs aus der **ganzen** geladenen Historie. Ein
längeres Fenster kann also ein älteres, näher liegendes Hoch dazuholen. Beispiel im
Szenario: Mit 1200 Kerzen verkauft die Engine an „131.281“, mit 400 Kerzen erst an
„135.282“. Live lädt 1.300 Kerzen, der Backtest rechnet ab 10.08.2025. Ob das im echten
Datensatz einen Unterschied macht, ist **nicht gemessen**. Eingetragen in
`02_status/OFFENE-PUNKTE.md` als **A5**. Der E43.5-Test vergleicht deshalb die
Muster-Folge und die Muster-2-Signale, nicht alle Signale. Die Lücke steht im Test
ausdrücklich dabei, statt still weggelassen zu werden.

**Betroffene Dateien:** `engine/test_strategy_core.py` (Test umgebaut, Szenario, Vorprobe,
Befund-Test), `engine/sabotage_e433.py` (Sabotagen für E43.5 und E43.3 zusammen).

**Bewusst NICHT:** kein Eingriff in `strategy_core.py` in dieser Etappe; A5 nicht
nebenbei beheben (eigene Etappe, eigener Schalter, eigene Messung).

**Umgesetzt 26.09.2026 (Arbeitszweig):** `_flow_ab()` summiert je Ladefenster ab null,
`_live_einstellung()` liest die Panel-Zeile, `_pump_szenario()` liefert die Pump-Phasen.
Neu: `test_e435_szenario_erreicht_den_muster2_zweig` (Vorprobe) und
`test_e435_befund_a2_mehr_historie_dreht_muster2` (Befund A2 als Test). Der umgebaute
`test_mehr_historie_aendert_die_signale_nicht` bleibt mit Neu-Summierung und heutiger
Live-Einstellung grün. **450 Tests grün.** `sabotage_e433.py`: 5 von 5 gefangen
(Summe wieder ausgeschnitten, Szenario ohne Pump, OI zu schwach, `_slope` ohne Division,
Muster 2 unerreichbar).

## E43.4 — Open Interest in Kontrakten statt Dollar (Befund A3)

**Gebaut und gemessen 26.09.2026 auf dem Arbeitszweig: Regel nicht erfüllt, bleibt
`"usd"`** (siehe „Messung E43.4“). Der Bauplan unten ist unverändert, so wie Kaiser ihm
zugestimmt hat. Was beim Bau dazukam, steht in „Umsetzung E43.4“.

**Problem, genau lokalisiert** (`strategy_core.classify_pattern`):

```python
oi_chg = (f[-1].oi - f[0].oi) / f[0].oi if f[0].oi else 0.0   # f = flow[-12:], 2 Tage
```

`FlowPoint.oi` ist das Open Interest in **Dollar**. Es kommt von Coinalyze
`open-interest-history` mit `convert_to_usd=true` für `BTCUSDT_PERP.A`. Das ist ein
linearer USDT-Kontrakt, sein OI zählt BTC. Dollar-OI = BTC-OI × Kurs. In `oi_chg`
steckt deshalb immer die Kursänderung im Fenster:
(1 + Änderung der Kontrakte) × (1 + Änderung des Kurses) − 1. Die Schwellen sind so
groß wie die Kursbewegungen, die die Muster selbst verlangen:

| Muster | Bedingung heute (Dollar) | was sie in Kontrakten verlangt | live handelswirksam? |
|---|---|---|---|
| 4 Kapitulation | Kurs ≤ −4 %, OI ≤ −5 % | bei −5 % Kurs **keine** geschlossene Position | ja: starke Bestätigung beim Einstieg (`_confirm_long`) |
| 5 Abverkauf mit neuen Shorts | Kurs ≤ −2 %, OI ≥ −1 % | bei −2 % Kurs müssen die Kontrakte um rund 1 % **steigen** | nein (`block_unhealthy`, `muster5_*` aus), nur Anzeige und Ampel |
| 3 Short-Covering | Kurs ≥ +2 %, OI ≤ −2 % | bei +2 % Kurs müssen die Kontrakte um rund 4 % fallen | ja: Restverkauf nach dem ersten Ziel |
| 2 Derivate-Pump | Kurs > 0, OI ≥ +3 % | bei +3 % Kurs **kein** neuer Kontrakt | ja: Einstiegssperre, Restverkauf, Telegram-Warnung |
| 1 Gesunder Trend | Kurs > 0, OI 0 bis +10 % | bei +3 % Kurs dürfen die Kontrakte um rund 3 % fallen | nein (Short-Seite, `block_unhealthy`), nur Anzeige und Ampel |

Muster 1 fehlt in der Tabelle des Prüfberichts. Es liest dasselbe `oi_chg` und ist
genauso betroffen.

**Nachgeprüft 26.09.2026** mit `demo_oi_usd.py` (Prüfbericht-Anhang) gegen den heutigen
Code. Die Kontrakte bleiben die ganze Zeit gleich. Die Kontrakt-Rechnung ist von Hand
nachgestellt (OI-Reihe = Kontrakte statt Kontrakte × Kurs):

| Lage | heute (Dollar) | in Kontrakten |
|---|---|---|
| Kurs −5 %, Spot dreht am Ende, Kontrakte gleich | CAPITULATION_RESET | UNGESUNDER_ABVERKAUF |
| Kurs +3,5 %, Futures steigt, Funding zieht an, Kontrakte gleich | DERIVATE_PUMP | GESUNDER_TREND |
| wie oben, aber Kontrakte −6 % | – | CAPITULATION_RESET |
| wie oben, aber Kontrakte +4 % | – | DERIVATE_PUMP |

Die letzten beiden Zeilen sind die Gegenprobe: In Kontrakten werden beide Muster weiter
erkannt, wenn wirklich Positionen geschlossen oder eröffnet werden. Der Schalter schaltet
die Muster also nicht ab, er berichtigt sie.

**Regel:** neuer Schalter `muster_oi`, Werte `"usd"` (Default, heutiges Verhalten
unverändert) | `"btc"` (Kontrakte, gemessen in BTC).

1. **Umrechnen am Datenpunkt, nicht an der Kerze.** Jeder echte Coinalyze-OI-Punkt wird
   mit dem Schlusskurs **derselben** 4h-Kerze (gleiche `ts`) in BTC umgerechnet:
   `oi_btc = oi_usd / close`. Beide Werte gelten zum Kerzenschluss (Coinalyze-Feld „c“).
   Erst danach wird aufgefüllt, genau wie heute beim Dollar-OI: vor dem ersten Punkt gilt
   der erste Wert, bei einem fehlenden Punkt der letzte. Aufgefüllt werden also
   **Kontrakte**, nicht Dollar.
   *Warum nicht einfach in `classify_pattern` durch den Kurs teilen, wie Teil E des
   Prüfberichts vorschlägt?* Ein aufgefüllter Dollar-Wert, geteilt durch den Kurs einer
   **anderen** Kerze, erfindet eine OI-Bewegung in Höhe der Kursbewegung. Das wäre genau
   der Fehler, der behoben werden soll. Das passiert im echten Datensatz: Das Messfenster
   beginnt dort, wo das Coinalyze-OI einsetzt (`eff_start = max(START_MS, min(oi_map))`,
   zuletzt 18.01.2026). Die ersten 11 Kerzen des Fensters lesen also aufgefüllte Werte.
   Live kann der OI-Punkt der gerade geschlossenen Kerze fehlen. Dann würde der
   Dollar-Wert der Vorkerze durch den neuen Kurs geteilt.
2. **Eine Hilfsfunktion für Live und Backtest:** `strategy_core.oi_in_btc(oi_usd, candles)`
   liefert `{ts: BTC}`. OI-Punkte ohne Kerze mit gleicher `ts` entfallen (lieber kein Wert
   als einer mit falschem Kurs, wie bei `_fut_cvd_usd`). `main.fetch_market_data` und
   `backtest.build_series` rufen beide diese Funktion auf und füllen das Ergebnis so auf,
   wie sie heute das Dollar-OI auffüllen. Neues Feld am Ende von `FlowPoint`:
   `oi_btc: float = 0.0` (0.0 = keine Kontrakt-Reihe). `FlowPoint.oi` bleibt in Dollar.
3. **`classify_pattern(..., muster_oi="usd")`:** Bei `"btc"` kommt `oi_chg` aus `oi_btc`
   statt aus `oi`. Die Formel bleibt gleich, **nur die Einheit ändert sich**. Ist `oi_btc`
   am Fensteranfang 0 (keine Reihe), gilt `oi_chg = 0`. Das ist dieselbe neutrale Antwort,
   die `"usd"` heute ohne OI-Daten gibt.
4. **Alle fünf Muster wechseln gemeinsam.** Es gibt nur ein `oi_chg`. Nur Muster 2 und 4
   umzustellen hieße, in derselben Einordnung zwei Einheiten zu mischen. Die Schwellen
   (+3 %, −5 %, −2 %, −1 %, 0 bis +10 %) bleiben, wie sie sind.
5. **Ohne Coinalyze:** Im Backtest ohne `oi_map` (OI konstant 1.0) und live im
   Kraken-Rückfall gilt `oi_btc = 0.0`, also OI-neutral. Die Kraken-Historie wird heute nur
   geschrieben, wenn Coinalyze ausfällt. Sie ist lückenhaft und im Backtest gar nicht
   nachstellbar.
6. **Anzeige = Handel** (wie E43.3): `evaluate()` reicht `muster_oi` an `classify_pattern`
   durch. Die drei Aufrufe für Lage-Abruf, Vorschau und Plan in `main.py` bekommen
   denselben Wert. Solange der Schalter auf `"usd"` steht, ändert sich nirgends etwas.
7. **Kurs-Quelle:** Geteilt wird durch den Binance-**Spot**-Schlusskurs, live und im
   Backtest derselbe. Coinalyze rechnet mit dem Perp-Kurs. Der Unterschied (Basis) liegt
   meist unter 0,1 % und ändert sich in zwei Tagen kaum. Gegen Schwellen von 1 bis 5 % ist
   das vernachlässigbar. Vermerkt, nicht korrigiert.

**Entscheidungsregel, festgelegt VOR der Messung** (wie E41, E43.2, E43.3; wird nicht
nachträglich gelockert): `muster_oi: "btc"` geht nur live, wenn die Zeile gegen die
heutige Live-Zeile (Panel: `bein_richtung="bias"`, `muster_cvd="alt"`)

1. in **beiden** Fensterhälften um **mindestens 1 Punkt** besser ist, **und**
2. der maximale Rückgang **nicht mehr als 1 Punkt** tiefer liegt.

Sonst bleibt `"usd"`. **Vorbedingung für ein Urteil:** Der Bericht findet OI-Daten im
Fenster, und die Vorprobe zählt mehr als 0 umklassifizierte Kerzen. Sonst meldet er „misst
nichts“ und fällt kein Urteil.

Geht der Schalter live, gilt die **Ausschalt-Regel**: zurück auf `"usd"`, wenn `"usd"` in
beiden Hälften um mindestens 1 Punkt besser ist oder der Rückgang mit `"btc"` mehr als
1 Punkt tiefer liegt. Der Bericht prüft das dann selbst (Vorbild E41, E43.2).

**Anzeige-Frage (Sonderregel aus Teil E), vorab festgelegt:** Die Musterzeile im
Lage-Abruf rechnet immer wie der Handel (Regel 6). Eine eigene Anzeige-Einstellung
(„Anzeige berichtigt, Handel alt“) wird erst gebaut, wenn Kaiser das nach der Messung
ausdrücklich will. Dann wird für A2 und A3 gemeinsam entschieden, wie in der Übergabe vom
26.09.2026 empfohlen.

**Vorab gesagt, damit das Ergebnis nicht falsch gelesen wird:** Anders als E43.3 (2 von
1.504 Kerzen) wird E43.4 voraussichtlich viele Kerzen umklassifizieren, weil ±3 % Kurs in
zwei Tagen häufig sind. Viele umklassifizierte Kerzen sind **kein** Urteil, es zählt nur
die Regel oben. In welche Richtung sich der Handel verschiebt, ist offen: Muster 2 und 4
werden seltener (weniger Einstiegssperren und Restverkäufe durch Muster 2, weniger starke
Bestätigungen durch Muster 4), Muster 3 und 5 häufiger (mehr Restverkäufe durch Muster 3).

**Vorprobe im Datensatz** (Berichtsabschnitt „E43.4“, Vorbild `e433_umklassifiziert`):

1. An wie vielen Kerzen im Fenster gibt es einen echten OI-Punkt? Bei 0 misst die Zeile
   nichts.
2. An wie vielen Kerzen ergeben `"usd"` und `"btc"` verschiedene Muster? Dazu je Muster
   die Anzahl unter beiden Einstellungen.
3. **A3 als Zahl:** Wie oft war die OI-Bedingung von Muster 2 (≥ +3 %), 3 (≤ −2 %),
   4 (≤ −5 %) und 5 (≥ −1 %) in Dollar erfüllt, und wie oft davon auch in Kontrakten?
   Damit wird die Aussage des Prüfberichts („die Engine erkennt Muster 2 und 4 zu einem
   großen Teil am Kurs“) am echten Datensatz geprüft statt an Kunstdaten.
4. Urteil nach der Entscheidungsregel (`e434_einschalten`, Vorbild `e433_einschalten`).

**Vorprobe in den Tests** (Regel 2: erst beweisen, dass der Zweig erreicht wird):

- `demo_oi_usd.py` als bleibender Test, alle vier Zeilen der Tabelle oben: gleiche
  Kontrakte → `"usd"` erkennt CAPITULATION_RESET und DERIVATE_PUMP, `"btc"` nicht. Echte
  Kontrakt-Änderung → `"btc"` erkennt beide.
- Ohne OI-Daten (konstant 1.0, `oi_btc = 0`) ergeben `"usd"` und `"btc"` dasselbe Muster.
- Aufgefüllte Werte erfinden keine Bewegung: Fehlt der letzte OI-Punkt, bleibt `oi_btc`
  beim Wert der Vorkerze, auch wenn der Kurs springt.
- Live = Backtest: Dieselben Rohdaten durch `main.fetch_market_data` (mit
  Coinalyze-Attrappe) und durch `backtest.build_series` ergeben je Kerze dasselbe
  `oi_btc`.

**Betroffene Dateien (geplant):**

- `engine/strategy_core.py`: `FlowPoint.oi_btc`, `oi_in_btc()`,
  `classify_pattern(..., muster_oi="usd")`, `evaluate(..., muster_oi="usd")` reicht durch.
- `engine/main.py`: `fetch_market_data` füllt `oi_btc` (Coinalyze-Weg; Kraken-Rückfall
  0.0); `EVAL_DEFAULTS["muster_oi"] = "usd"`; die drei Anzeige-Aufrufe von
  `classify_pattern` bekommen `muster_oi`.
- `engine/backtest.py`: `build_series` füllt `oi_btc` über dieselbe Hilfsfunktion;
  `muster_oi` in `EVAL_KEYS` und `_BASE`; Gitterzeile `LIVE-heute +OI in Kontrakten
  (E43.4)`, geklont von der Panel-Zeile plus **genau** `muster_oi="btc"`;
  `e434_umklassifiziert`, `e434_einschalten`, `e434_abschnitt`, im Bericht verdrahtet.
- `engine/test_strategy_core.py`, `engine/test_main.py`, `engine/test_backtest.py`: die
  Tests oben, dazu: Schalter kommt in `evaluate` an (Vorbild
  `test_e433_muster_cvd_kommt_in_evaluate_an`), Gitterzeile hat genau einen Unterschied,
  Live-Konfiguration steht auf `"usd"`, Entscheidungsregel in beide Richtungen, Bericht
  verdrahtet, Anzeige rechnet wie der Handel.
- Neue Sabotage-Datei `engine/sabotage_e434.py` (Vorbild `sabotage_e433.py`), mindestens:
  Schalter fehlt in `EVAL_KEYS` oder kommt nicht an; Umrechnung mit dem Kurs der falschen
  Kerze (Vor- oder Folgekerze); erst Dollar auffüllen, dann teilen (der naive Weg);
  Leer-Wächter fehlt (`oi_btc = 0` erzeugt eine Bewegung oder eine Division durch null);
  `"btc"` wirkt nur in Muster 2 statt in allen; `main` und `backtest` rechnen verschieden;
  Kraken-Rückfall teilt doch durch den Kurs; Gitterzeile mit zwei Unterschieden;
  Entscheidungsregel falsch herum oder mit fehlender Bedingung.
- `site/data/config.json`: `"muster_oi": "usd"` plus `_hinweis_muster_oi` (Default aus,
  „erst nach Backtest-Messung und Kaisers Go umschalten“).

**Bewusst NICHT:**

- keine Änderung der Schwellen (+3 %, −5 %, −2 %, −1 %, +10 %, `oi_wipeout_pct`) über die
  Einheit hinaus. Das wäre Nachjustieren an der Vergangenheit.
- keine Kombination mit `muster_cvd="usd"` in derselben Zeile (ein Unterschied je Zeile).
  Die E43.4-Zeile läuft mit `muster_cvd="alt"`, wie live.
- kein zweiter Coinalyze-Abruf mit `convert_to_usd=false`. Er hätte die Kontrakte direkt
  geliefert, kostet aber live und im Backtest einen weiteren Abruf (die 429-Grenzen sind
  bekannt). Für die aggregierten E37-Reihen hilft er auch nicht: Dort rechnen inverse
  Kontrakte in Dollar, lineare in BTC, summierbar ist nur Dollar.
- die **OI-Zeile im Lage-Abruf** (`orderflow_detail`) bleibt in Dollar, mit ihrem Hinweis
  („neues Geld kommt herein“ / „Positionen werden geschlossen“). Der Hinweis folgt der
  Dollar-Richtung. Bei fallendem Kurs und gleichen Kontrakten sagt er also „Positionen
  werden geschlossen“, obwohl niemand geschlossen hat. Das ist A3 in der Anzeige.
  **Empfehlung:** ein eigener kleiner Anzeige-Schritt (Kontrakt-Änderung daneben, Hinweis
  nach Kontrakten), unabhängig vom Handels-Urteil, Aufwand mittel. Nicht in dieser Etappe,
  damit sie genau eine Sache ändert.
- im Kraken-Rückfall keine Kontrakte in `state.json` speichern (das wäre eine Änderung am
  Zustand, siehe Regel 5).
- Liquidationen bleiben in Dollar: `_liq_spike` vergleicht die letzte Kerze mit dem
  Mittel desselben Fensters. Der Kurseffekt ist dort klein und nicht Teil von A3.
- die Auswertungen im Bericht, die `classify_pattern` ohne Schalter aufrufen
  (`muster_nachlauf`, E38-Statistik), bleiben bei `"usd"`, solange der Schalter live aus
  ist.
- A5 (`next_pivot_beyond`) nicht nebenbei beheben.

**Grenze, bewusst nicht behoben (vermerkt wie bei E43.3):** Die E37-Datenvarianten „OI
aggregiert“ und folgende summieren das Dollar-OI mehrerer Perp-Märkte. `oi_in_btc` teilt
diese Summe durch den Binance-Spot-Kurs. Das stimmt für lineare Kontrakte (USDT, USDC),
für inverse (USD-Kontrakte) nicht, denn deren Dollar-OI bewegt sich nicht mit dem Kurs.
Die Varianten laufen mit der Panel-Einstellung (`"usd"`) und sind deshalb erst betroffen,
wenn `"btc"` live geht. Dann vorher prüfen, welche gewählten Märkte invers sind
(`perp_auswahl` meldet die Denominierung je Markt).

**Abhängigkeit:** E43.6 (Nachmessung `rest_halten`, `strict_confirm`, danach Muster 5)
wartet auf das E43.4-Urteil. Der Restverkauf hängt an Muster 2 und 3, Muster 5 an der
OI-Bedingung.

**Aufwand:** hoch (Mustererkennung; Live und Backtest müssen gleich rechnen; Vorprobe und
Sabotage). Stand vor dem Bau: **467 Tests grün**. Geschätzt rund 20 neue Tests.

### Umsetzung E43.4 (26.09.2026, Arbeitszweig, noch nicht gemessen)

Kaisers Zustimmung zum Bauplan: *„Ja“*. Gebaut wie oben, ohne Abweichung von der Regel.

- `strategy_core.py`: `FlowPoint.oi_btc` (letztes Feld, Default 0.0), `oi_in_btc(oi_usd,
  kurs)`, `oi_aenderung(f, muster_oi)`. `classify_pattern(..., muster_oi="usd")` holt
  `oi_chg` aus `oi_aenderung`, alle fünf Muster lesen denselben Wert.
  `evaluate(..., muster_oi="usd")` reicht ihn durch. `"usd"` rechnet Zeichen für Zeichen
  wie vorher (auch der Randfall „OI am Fensterende 0“ ergibt weiter −100 %). `"btc"` gibt
  ohne Kontrakt-Reihe 0 zurück.
- `main.py`: `fetch_market_data` rechnet die Coinalyze-Punkte mit dem Schlusskurs ihrer
  Kerze um und füllt danach auf. Der Kraken-Rückfall bekommt `oi_btc = 0.0`.
  `EVAL_DEFAULTS["muster_oi"] = "usd"`. Lage-Abruf, Vorschau und Plan rechnen das Muster
  mit demselben Wert wie der Handel.
- `backtest.py`: `build_series` genauso (dieselbe Hilfsfunktion), `muster_oi` in
  `EVAL_KEYS` und `_BASE`, Gitterzeile „LIVE-heute +OI in Kontrakten (E43.4)“ mit genau
  einem Unterschied, Berichtsabschnitt „E43.4“ mit `e434_umklassifiziert` (Vorprobe),
  `e434_einschalten` (Regel) und `e434_abschnitt`.
- **Genauer als im Plan:** „A3 als Zahl“ zählt je Muster nur Kerzen, an denen die
  **Kursbedingung** des Musters erfüllt ist. Gezählt wird, ob die OI-Bedingung dort in
  Dollar, in Kontrakten oder in beiden erfüllt ist. Ohne diese Einschränkung wäre z. B.
  „OI ≥ −1 %“ (Muster 5) fast immer erfüllt und die Zahl sagte nichts. Muster 1 steht
  mit in der Tabelle.
- `site/data/config.json`: `"muster_oi": "usd"` plus `_hinweis_muster_oi`.
- **Tests:** 21 neue, **488 grün**. Darunter die verdrahtete Vorprobe `demo_oi_usd`
  (`usd`: CAPITULATION_RESET und DERIVATE_PUMP, `btc`: UNGESUNDER_ABVERKAUF und
  GESUNDER_TREND) mit Gegenprobe, je Muster eine Lage für Muster 1, 3 und 5, der Weg
  durch `evaluate()` und „Live = Backtest“: Dieselben Rohdaten ergeben in
  `fetch_market_data` (mit Attrappen statt Netz) und in `build_series` dieselben
  Kontrakte, auch vor dem ersten OI-Punkt, in einer Lücke und an der jüngsten Kerze ohne
  Punkt.
- **Sabotage:** `sabotage_e434.py`, 37 Sabotagen, alle beim ersten Lauf gefangen.
  Drei Vorlagen in `sabotage_e433.py` suchten Zeilen, die E43.4 geändert hat
  (`evaluate`-Aufruf, `EVAL_KEYS`, Anzeige-Aufruf). Sie sind auf den neuen Wortlaut
  nachgezogen, mit unveränderter Absicht.

### Messung E43.4 (26.09.2026, GitHub-Lauf 36236645038, Fenster 18.01.–26.09.2026)

| Variante | Rendite | Rückgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live (`usd`)** | +35,4 % | −9,9 % | +23,6 % | +9,6 % | 244 |
| OI in Kontrakten (`btc`) | +35,4 % | −9,9 % | +23,6 % | +9,6 % | 227 |

- **Vorprobe im Datensatz:** 1.504 Kerzen im Fenster, alle mit echtem OI-Punkt.
  **Verschieden erkannt: 210 Kerzen (14 %).** Die Zeile misst also etwas, und zwar
  viel mehr als E43.3 (2 Kerzen).

  | Muster | Kerzen mit `usd` | Kerzen mit `btc` |
  |---|---:|---:|
  | Kapitulation (4) | 21 | 11 |
  | Derivate-Pump (2) | 96 | 48 |
  | Gesunder Trend (1) | 184 | 149 |
  | Short-Covering (3) | 56 | 103 |
  | Abverkauf mit neuen Shorts (5) | 47 | 97 |
  | Neutral | 1.100 | 1.096 |

- **A3 als Zahl** (unter der Kursbedingung des Musters: OI-Bedingung erfüllt in Dollar,
  in Kontrakten, in beiden):

  | Muster | Kerzen | in Dollar | in Kontrakten | in beiden |
  |---|---:|---:|---:|---:|
  | 4 Kapitulation (Kurs ≤ −4 %, OI ≤ −5 %) | 127 | 74 | 30 | 30 |
  | 5 Abverkauf (Kurs ≤ −2 %, OI ≥ −1 %) | 334 | 95 | 209 | 95 |
  | 3 Short-Covering (Kurs ≥ +2 %, OI ≤ −2 %) | 332 | 12 | 65 | 12 |
  | 2 Derivate-Pump (Kurs > 0, OI ≥ +3 %) | 758 | 296 | 144 | 144 |
  | 1 Gesunder Trend (Kurs > 0, OI 0 bis +10 %) | 758 | 474 | 359 | 322 |

  **Befund A3 ist im echten Datensatz bestätigt, und er ist groß:** Die Pump-Bedingung
  „OI ≥ +3 %“ war in Dollar 296-mal erfüllt, in Kontrakten nur 144-mal. Rund die Hälfte
  kam also allein vom Kurs. Bei der Kapitulation waren es 44 von 74 (60 %). Umgekehrt
  waren Short-Covering und Muster 5 in Dollar viel zu selten: 12 statt 65 bzw. 95 statt
  209.
- **Urteil nach der vorab festgelegten Regel:** in beiden Hälften ≥ 1 Punkt besser:
  **nein** (H1 ±0,0, H2 ±0,0). Rückgang: gleich. **Regel nicht erfüllt, `muster_oi`
  bleibt auf `"usd"`.**
- **Die 17 Signale weniger** ändern weder Rendite noch Hälften noch Rückgang, auch nicht
  in der ersten Nachkommastelle. Das passt nur zu Signalen ohne Tranche, also zu den
  Warnungen „Derivate-Pump: anfällig für Long-Flush“ während einer offenen Position
  (Derivate-Pump halbiert: 96 → 48 Kerzen). **Das ist ein Schluss, nicht gezählt:** Der
  Bericht schlüsselt die Signalarten je Zeile nicht auf, und ohne Coinalyze-Key lässt
  sich der Lauf nicht außerhalb von GitHub nachstellen.
- **Einordnung:** Die Mustererkennung ändert sich an 14 % der Kerzen, der Handel in acht
  Monaten praktisch nicht. Die Einstiege hängen an den Fib-Zonen, die Muster wirken nur
  an wenigen Stellen (Sperre, Bestätigung, Restverkauf), und dort lagen beide Rechnungen
  offenbar gleich. Die bisherigen Urteile, die an Mustern hängen, verlieren durch A3
  deshalb für die Rendite nichts. Für die **Anzeige** gilt das nicht: Der Lage-Abruf nennt
  an rund jeder siebten Kerze ein Muster, das zum Teil nur aus dem Kurs stammt.
- **Offen für Kaiser — Anzeige-Frage für A2 und A3 gemeinsam** (vorab so festgelegt):
  beide Handels-Schalter bleiben aus. Eine eigene Anzeige-Einstellung hieße, dass der
  Lage-Abruf an rund 14 % der Kerzen ein anderes Muster nennt als das, nach dem die
  Engine handelt. **Empfehlung der KI:** keine getrennte Muster-Anzeige, stattdessen der
  kleine Anzeige-Schritt aus „Bewusst NICHT“: In der OI-Zeile steht die Kontrakt-Änderung
  neben der Dollar-Änderung, und der Hinweis („neues Geld“ / „Positionen werden
  geschlossen“) folgt den Kontrakten. Dann sieht Kaiser selbst, ob das OI wegen neuer
  Positionen oder nur wegen des Kurses steigt, und Anzeige und Handel bleiben bei
  derselben Mustererkennung.

## E43.4b — OI-Zeile im Lage-Abruf in Kontrakten (reine Anzeige)

**Kaisers Auftrag 26.09.2026:** *„Bau zuerst die OI-Zeile in Kontrakten“* (seine Antwort
auf die Anzeige-Frage A2/A3 nach der Messung E43.4).

**Problem:** Die Zeile „Open Interest“ im Lage-Abruf (`orderflow_detail`) zeigt die
Änderung in Dollar. Richtung, Pfeil und Hinweis („neues Geld kommt herein“ /
„Positionen werden geschlossen“) folgen dem Dollar-Wert. Fällt der Kurs um 5 % und
niemand schließt eine Position, steht dort „Positionen werden geschlossen“. Das ist
falsch (Befund A3 in der Anzeige; E43.4 hat gezählt, wie oft das passiert).

**Regel:**

1. Der Dollar-Wert bleibt stehen, **dahinter** steht die Änderung der Kontrakte in
   Prozent (`FlowPoint.oi_btc`, dieselbe Reihe wie E43.4): „+120,0 Mio $ (+3,0 %),
   Kontrakte +0,0 %“.
2. Richtung (Pfeil) und Hinweis folgen den **Kontrakten**: steigt → „neues Geld kommt
   herein“, fällt → „Positionen werden geschlossen“, flach → „unveraendert“. Die
   Richtung wird wie bisher am Maßstab der früheren Fensteränderungen derselben Reihe
   bestimmt (`_of_reihe`).
3. Zeigen Dollar und Kontrakte in verschiedene Richtungen, sagt der Hinweis das dazu:
   „der Dollar-Anstieg kommt nur vom Kurs“, „der Dollar-Rueckgang kommt nur vom Kurs“,
   bzw. bei flachem Dollar-Wert „in Dollar vom Kurs verdeckt“.
4. Ohne Kontrakt-Reihe (Kraken-Rückfall, kein Coinalyze) bleibt die Zeile genau wie
   bisher: nur Dollar, Hinweis nach Dollar. Keine Zeile „Kontrakte 0 %“, die Stillstand
   behauptet, wo nichts bekannt ist.

**Bewusst NICHT:** keine Änderung an `classify_pattern`, `evaluate` oder am Muster im
Lage-Abruf (die Musterzeile rechnet weiter wie der Handel, `muster_oi: "usd"`); kein
Schalter (reine Anzeige, wie E43.1); keine anderen Zeilen des Order-Flow-Blocks.

**Betroffene Dateien:** `engine/strategy_core.py` (`orderflow_detail`),
`engine/test_strategy_core.py`, `engine/test_main.py` (Nachricht bleibt handytauglich),
neue Sabotage-Probe `engine/sabotage_e434b.py`.

**Umgesetzt 26.09.2026, ohne Abweichung von der Regel. Live seit 26.09.2026 (Kaisers Go).** So steht es im
Lage-Abruf (Kurs +3 %, Kontrakte gleich):

```
Open Interest: +225,5 Mio $ (+3,0 %),
Kontrakte +0,0 % →
  unveraendert - der Dollar-Anstieg
  kommt nur vom Kurs
```

Der Dollar-Teil ist immer zu lang, um „Kontrakte“ noch in dieselbe Handyzeile (38
Zeichen) zu nehmen. „Kontrakte +x,x %“ steht deshalb samt Pfeil geschlossen in der
zweiten Zeile, und der Pfeil gehört sichtbar zu den Kontrakten.

- **Tests:** 5 neue, **493 grün**. Je ein Test für „Kurs allein ist kein neues Geld“,
  „Kursrutsch ist kein Schließen“ (beide mit Vorprobe: ohne Kontrakt-Reihe zeigt
  dieselbe Lage den alten Fehler), für echte Kontrakt-Änderungen samt „in Dollar vom
  Kurs verdeckt“, für „ohne Kontrakt-Reihe wie bisher“, und dafür, dass die Zeile im
  Lage-Abruf ankommt und handytauglich bleibt.
- **Sabotage:** `sabotage_e434b.py`, 9 Sabotagen, alle beim ersten Lauf gefangen.
  `sabotage_e43.py` (7/7) und `sabotage_e434.py` (37/37) erneut gelaufen, alle
  Vorlagen der übrigen Proben passen weiter.

## E43.6 — Nachmessung mit genau einem Unterschied: `rest_halten`, `strict_confirm`,
`confirm_t1`, `cooldown_h`

**GEBAUT 26.09.2026** (Arbeitszweig `claude/e43-6-gitterzeilen-eo6mzb`): die vier
Gitterzeilen, die vier Vorproben und der Berichtsabschnitt `e436_abschnitt` stehen in
`engine/backtest.py`, verdrahtet wie `e433_abschnitt`/`e434_abschnitt`. **501 Tests
grün** (Ausgangsbasis 493, 8 neue: je ein Test „genau ein Unterschied zur Panel-Zeile"
für alle vier Zeilen, die Entscheidungsregel, zwei Zähl-Funktionen mit synthetischen
Signal-Listen, der Berichtsabschnitt und die Verdrahtung in `main()`). Keine eigene
Sabotage-Datei, wie geplant.

**NOCH NICHT GEMESSEN:** Die bauende Sitzung hatte keinen Netzzugriff auf
Binance/Coinalyze (`fetch_candles_range` scheitert am Tunnel), ein echter
`python3 backtest.py`-Lauf gegen den realen Datensatz war deshalb nicht möglich. Die vier
Schalter bleiben bis zur echten Messung **aus**. Nächster Schritt: in einer Sitzung mit
Netzzugriff `python3 backtest.py` laufen lassen, Abschnitt „E43.6" im Bericht lesen, hier
je Schalter „Messung E43.6" mit Ergebnis nachtragen (Vorbild „Messung E43.3“/„Messung
E43.4“ oben in der Tabelle).

**Warum diese vier:** Teil C des Prüfberichts (`docs/PRUEFUNG-2026-09-26-GESAMT.md`)
listet sie als „gebaut, aber nie mit genau einem Unterschied gegen die heutige Live-Zeile
gemessen" — `strict_confirm` zusätzlich ohne echte OI-Daten (07/2026). Nach Projektregel
ist ein Mechanismus, der gegen eine ältere Live-Einstellung verworfen wurde, wieder offen.
Alle vier existieren im Code bereits und wirken, es fehlt nur die faire Messzeile.

**Live-Basis, gegen die gemessen wird** (Panel-Zeile in `backtest.py`, seit 26.09.2026):
`bias_short=False, flush_entry="core", buy_ladder=True, trail_stop=True,
min_stop_pct=0.02, liq_entry="boost", high_exit="on", min_bein_pct=0.05, no_flip=True,
neustart_mit_rest=True, zonen_nachziehen=True, stop_rueckeroberung=1,
bein_richtung="bias"` (dazu die Defaults `muster_cvd="alt"`, `muster_oi="usd"`).

**Geklärt vor dem Bau — lohnt sich die Muster-5-Wiederholung jetzt?** Teil C sagt zu
`block_unhealthy`/`muster5_*`: „Urteil hält vorerst, Muster 5 hängt aber an A3: nach der
Korrektur einmal wiederholen." Die Korrektur ist inzwischen gemessen: **A2 (`muster_cvd`)
und A3 (`muster_oi`) blieben beide auf ihrem alten Wert** (`"alt"` bzw. `"usd"`, siehe
„Messung E43.3" und „Messung E43.4" oben) — die Mustererkennung, an der Muster 5 hängt,
hat sich also nirgends geändert. Eine Wiederholung jetzt würde exakt dieselben Kerzen und
Zahlen liefern wie die letzte Messung. **Bewusst NICHT jetzt wiederholen.** Sinnvoll wird
die Wiederholung erst, wenn `muster_cvd` oder `muster_oi` tatsächlich auf den korrigierten
Wert wechselt — dann ändert sich die Mustererkennung real, und erst dann sagt eine neue
Zahl etwas Neues. Bis dahin bleibt das Urteil aus Teil C stehen. E43.6 misst deshalb nur
die vier Schalter im Titel; die Muster-5-Wiederholung ist zurückgestellt, nicht vergessen
(Eintrag bleibt in `02_status/OFFENE-PUNKTE.md`).

**Entscheidungsregel, festgelegt VOR der Messung (wie E41, E43.2, E43.3, E43.4; wird nicht
nachträglich gelockert), für alle vier Zeilen gleich:** Ein Schalter geht nur live, wenn
die Zeile gegen die heutige Live-Zeile
1. in **beiden** Fensterhälften um **mindestens 1 Punkt** besser ist, **und**
2. der maximale Rückgang **nicht mehr als 1 Punkt** tiefer liegt.

Sonst bleibt der Schalter aus (`False` bzw. `0`). Geht einer live, gilt die
**Ausschalt-Regel** wie bei E41/E43.2/E43.4: zurück auf aus, wenn „aus" in beiden
Hälften mindestens 1 Punkt besser ist oder der Rückgang mit dem Schalter mehr als 1 Punkt
tiefer liegt. Der Bericht prüft das dann selbst. **Vorbedingung für ein Urteil:** die
Vorprobe (unten, je Schalter) zählt mehr als 0 Kerzen/Ereignisse, an denen der Schalter im
Fenster überhaupt etwas ändert — sonst meldet der Bericht „misst nichts" und fällt kein
Urteil (Vorbild `e433_umklassifiziert`).

### `rest_halten`

**Gitterzeile** `LIVE-heute +Rest halten (E43.6)`: Panel-Zeile plus **genau**
`rest_halten=True`. Die im Wissens-Layer genannte Vorbedingung „nur zusammen mit
`neustart_mit_rest` sinnvoll" ist bereits erfüllt — `neustart_mit_rest=True` ist seit
E43.2 Teil der Live-Basis selbst.

**Vorprobe im Datensatz:** zählen, an wie vielen abgeschlossenen Positionen im Fenster die
Regel „Rest schliessen bei Gegen-Muster" (`strategy_core.py`, `exit_pat and not
rest_halten`) überhaupt ausgelöst hat — das sind genau die Ereignisse, die `rest_halten`
verändert (der Rest läuft dann bis zum Stop statt sofort verkauft zu werden). 0 Treffer →
die Zeile misst nichts.

**Bewusst NICHT:** keine gleichzeitige Änderung von `neustart_mit_rest` (bereits an, s.
o.); keine Anpassung der Muster-Bedingung für `exit_pat` (das wäre eine zweite Änderung in
derselben Zeile).

### `strict_confirm`

**Gitterzeile** `LIVE-heute +Strenge Bestaetigung (E43.6)`: Panel-Zeile plus **genau**
`strict_confirm=True`.

**Vorprobe im Datensatz:** zählen, an wie vielen Kerzen im Fenster `_confirm_long()` bzw.
`_confirm_short()` beim heutigen (lockeren) Maßstab wahr wären, aber beim strengen
Maßstab (`cvd_up UND fund_ok` statt `cvd_up ODER fund_ok`, jeweils ohne „starke"
Bestätigung durch Muster 4/DERIVATE_PUMP/Muster-5) falsch — das sind die Einstiege, die
`strict_confirm` verhindern würde. 0 Treffer → die Zeile misst nichts. **Wichtig:** Anders
als die Messung 07/2026 (Wissens-Layer-Hinweis: „ohne echte OI-Daten") laufen im heutigen
Fenster echte Coinalyze-Funding- und CVD-Daten mit — die alte Zahl von damals gilt hier
nicht, es wird neu gezählt.

**Bewusst NICHT:** keine Kombination mit `confirm_t1` in derselben Zeile — beide zusammen
wären zwei Unterschiede, und ob sie sich gegenseitig verstärken, ist eine eigene, spätere
Frage, falls beide einzeln etwas zeigen.

### `confirm_t1`

**Gitterzeile** `LIVE-heute +Bestaetigung am 0.5-Level (E43.6)`: Panel-Zeile plus
**genau** `confirm_t1=True` (`strict_confirm` bleibt in dieser Zeile aus).

**Vorprobe im Datensatz:** zählen, wie viele der Ersteinstiege am 0,5-Level im Fenster
heute **ganz ohne** Order-Flow-Bestätigung ausgelöst hätten (`_confirm_long`/
`_confirm_short` mit dem heutigen, nicht-strengen Maßstab wäre `False`) — das ist genau
die Zahl, die `confirm_t1` blockieren würde. 0 Treffer → die Zeile misst nichts. Die alte
Zahl aus dem Wissens-Layer-Hinweis (16 von 34, gemessen 07/2026) gilt nur für das damalige
Fenster und wird hier neu gezählt.

**Bewusst NICHT:** keine gleichzeitige Änderung von `strict_confirm` (s. o., eigene
Zeile).

### `cooldown_h`

**Gitterzeile** `LIVE-heute +Sperrfrist nach Stop 48h (E43.6)`: Panel-Zeile plus
**genau** `cooldown_h=48.0` — der im Wissens-Layer-Hinweis vorgeschlagene Wert, keine neu
erfundene Zahl.

**Vorprobe im Datensatz:** zählen, an wie vielen Stellen im Fenster ein neuer Einstieg
innerhalb von 48 Stunden nach einem Stop erfolgt wäre — nur diese Fälle verändert der
Schalter. 0 Treffer → die Zeile misst nichts.

**Bewusst NICHT:** kein anderer Wert als 48 (das wäre Nachjustieren an der Vergangenheit);
keine Kombination mit `min_stop_pct`, das laut Wissens-Layer-Hinweis dieselbe
Stop-Serien-Frage schon stabiler adressiert.

### Bewusst NICHT (für ganz E43.6)

- Keine Kombination der vier Schalter untereinander in einer Zeile — jede Zeile hat
  **genau einen** Unterschied zur heutigen Panel-Zeile, wie bei E43.2/E43.3/E43.4.
- Keine Muster-5-Wiederholung in dieser Etappe (Begründung oben).
- Kein Eingriff in `strategy_core.py` — alle vier Schalter existieren und rechnen schon
  richtig, es fehlt nur die faire Messzeile im Gitter.
- Keine Anpassung der Schwellen selbst (48h, die Bedingungen in `_confirm_long`/
  `_confirm_short`) über die genannten Werte hinaus.

**Betroffene Dateien (geplant):**

- `engine/backtest.py`: vier neue `V(...)`-Zeilen (siehe oben), Berichtsabschnitt „E43.6"
  mit den vier Vorproben und je einem Urteil nach der Entscheidungsregel (Vorbild
  `e433_umklassifiziert`/`e433_einschalten`, `e434_umklassifiziert`/`e434_einschalten`).
- `engine/test_backtest.py`: ein Test je Zeile „genau ein Unterschied zur Panel-Zeile"
  (Vorbild `test_e43_bein_richtung_ist_live_und_das_panel_ist_mitgewandert`).
- Voraussichtlich **keine eigene Sabotage-Datei** — anders als E43.3/E43.4 entsteht kein
  neuer Rechenweg, nur neue Gitterzeilen und Zähl-Auswertungen (Vorbild E43.2, das ebenfalls
  ohne eigene Sabotage auskam; `sabotage_e43.py` deckte dort nur E43.1s neue Rechnung ab).

**Aufwand:** niedrig (reine Auswertung nach vorab festgelegter Regel, kein neuer
Mechanismus) — wie in der Etappen-Tabelle oben vermerkt. Ausgangsbasis **493 Tests grün**;
geschätzt **4 bis 8 neue Tests** (vier Zeilen-Tests plus ggf. je ein Vorprobe-Test).

### Messung 26.09.2026 (GitHub-Actions-Backtest, Arbeitszweig)

Gebaut wie oben beschrieben, 8 neue Tests, **501 grün**. Beim ersten Backtest-Lauf
krachten alle vier Vorproben (`'dict' object has no attribute 'reason'`) — `run_backtest()`
liefert Signale als `dict` (`Signal.to_dict()`), die Zählfunktionen griffen per Attribut
statt per Schlüssel zu; die Testfixtures bauten fälschlich `Signal`-Objekte statt `dict`
und fingen den Fehler deshalb nicht. Behoben, erneut gemessen, weiter 501 Tests grün.

Live-Basis in diesem Lauf: +35,4 % Rendite, −9,9 % Rückgang, H1 +23,6 %, H2 +9,5 %,
244 Signale. Alle vier Vorproben zählen mehr als 0 Treffer (misst also etwas), aber
**keine der vier Zeilen erfüllt die Entscheidungsregel** — jede scheitert an
Bedingung 1 (nicht in beiden Fensterhälften ≥ 1 Punkt besser):

| Schalter | Vorprobe (Treffer) | H1 gegen live | H2 gegen live | Rückgang gegen live | Urteil |
|---|---:|---:|---:|---:|---|
| `rest_halten` | 11 Positionen | −4,3 | +3,2 | +0,0 | Regel nicht erfüllt → bleibt aus |
| `strict_confirm` | 1.354 von 1.505 Kerzen | +2,4 | −7,6 | +0,0 | Regel nicht erfüllt → bleibt aus |
| `confirm_t1` | 9 von 14 Ersteinstiegen | −0,8 | +0,9 | +0,0 | Regel nicht erfüllt → bleibt aus |
| `cooldown_h` (48h) | 1 Einstieg | −1,8 | +0,0 | +0,0 | Regel nicht erfüllt → bleibt aus |

**Ergebnis: alle vier Schalter bleiben aus** (`rest_halten=False`, `strict_confirm=False`,
`confirm_t1=False`, `cooldown_h=0.0`). Keine Ausschalt-Frage, da keiner live gegangen ist.
Am Code (`strategy_core.py`, `config.json`) wurde nichts geändert — reine Messung.
Vollständiger Bericht: `BACKTEST.md`, Abschnitt „E43.6“, Commit `7433652` auf
`claude/e43-6-gitterzeilen-eo6mzb`.

## E43.7

Noch nicht als Bauplan ausgeschrieben (Text-Etappe: `be_im_plus`-Urteil im Wissens-Layer
berichtigen, E37-Satz korrigieren, Funding-Einheit richtigstellen — Prüfbericht Teil E,
Punkt 7). Wird ergänzt, wenn E43.6 gebaut und entschieden ist.
