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
| E43.1 | Futures-CVD im Lage-Abruf in Dollar (Befund A1) | reine Anzeige | mittel | **FERTIG** 26.09.2026 (Arbeitszweig), wartet auf „Go“ |
| E43.2 | Gitterzeile „LIVE-heute +Bein in Handelsrichtung“, genau ein Unterschied | Messung, kein neuer Schalter | Auswertung: **niedrig** | **GEBAUT** 26.09.2026, Backtest auf dem Arbeitszweig läuft |
| E43.3 | Muster 2 vergleicht Dollar-Beträge statt Anteile an einer willkürlichen Summe (A2) | Schalter, Default aus | **hoch** | OFFEN |
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

## E43.3 bis E43.7

Werden vor dem Bau hier ergänzt (Regel, Schwellen, betroffene Dateien, Entscheidungsregel).
Stichpunkte stehen in `docs/PRUEFUNG-2026-09-26-GESAMT.md`, Teil E.
