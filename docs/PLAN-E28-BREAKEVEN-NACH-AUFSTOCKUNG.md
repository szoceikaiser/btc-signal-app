# Bauplan E28 — Break-even-Stop nach jeder Aufstockung (Furkan)

> **NICHT UMGESETZT — zurueckgenommen am 28.08.2026 auf Kaisers Entscheidung**, noch am
> Tag des Baus und vor dem Push: *„das mit dem stop nachziehen möchte ich doch nicht haben.
> Das werde ich im laufe der trades ggf. selber tun."* Der Code ist vollstaendig entfernt.
>
> Dieser Plan bleibt als Vorlage stehen. Er enthaelt alles, was ein Nachbau braucht — samt
> des Konstruktionsfehlers, den erst das Ausprobieren zeigte (siehe NACHTRAG weiter unten).

**Auftrag Kaiser, 28.08.2026:** *„Break even stop nach furkan umsetzen."*

## Die Quelle

Zweimal wörtlich belegt, in zwei verschiedenen Videos:

> *„wenn ich die Order gefüllt bekomme, würde ich meinen Stop … hochsetzen auf das neue
> Entry. Mit der Position möchte ich nicht mehr in Verlust gehen."*
> — Video 02.08.2026, 16:07–16:25 (`FURKAN-UPDATE-2026-08-02.md` Abschnitt 4)

Dieselbe Aussage in Video B vom Juli 2026, 18:50. Notiert seit E10 als offener Punkt, in
E12 als Punkt 2 der Verlust-Analyse (betrifft 44 % der Verlustsumme), nie gebaut.

## Was wir schon haben und warum es NICHT dasselbe ist

| Mechanismus | löst aus | Bezug |
|---|---|---|
| `trail_stop` (E9.10, live) | erst wenn Teilgewinne realisiert sind | höchster aus Invalidierung / Einstand / Struktur |
| `be_im_plus` (E19.3, aus) | sobald die Position einmal im Plus stand | Einstand |
| **`be_nach_aufstockung` (neu)** | **nach jeder Aufstockung** | **Einstand** |

Furkans Auslöser ist die gefüllte Order — nicht ein Teilgewinn, nicht ein Kursstand. Das
ist ein dritter, eigener Zeitpunkt.

## Soll-Zustand

**Neuer Schalter `be_nach_aufstockung`** (bool, Default `False`).

**Neues Positions-Feld `aufstockungen: int`**, hochgezählt an der zentralen Stelle, an der
auch der Durchschnitts-Einstand fortgeschrieben wird (`strategy_core.py`, „Durchschnitts-
Einstand fortschreiben"). Dort laufen ALLE Einstiegspfade zusammen — 0.786-Zone,
Kaufleiter, Liquidations-Konfluenz, bedingter Nachkauf. Sechs Einzelstellen zu patchen wäre
die Variante, bei der man eine vergisst.

Als Aufstockung zählt ein Einstiegs-Signal, wenn `pos.entry_pct` davor schon > 0 war — die
Position also bereits offen war. Der Ersteinstieg zählt nicht, auch nicht ein KAUF_2, das
direkt aus FLAT ins Golden Pocket geht.

**Wirkung im Stop-Block:** als eigener Zweig NACH dem `trail_stop`-Block, damit beide
zusammenwirken und der Stop nur steigen kann:

```python
if be_nach_aufstockung and pos.aufstockungen > 0 and pos.entry_ref is not None:
    stop_level = max(stop_level, pos.entry_ref)   # bei Long; bei Short min()
```

Bewusst **unabhängig von `trail_stop`** — Furkans Regel steht für sich. Und bewusst nur der
Einstand, nicht zusätzlich das Struktur-Tief: Er sagt „auf das neue Entry", nichts weiter.

**Zeitpunkt:** Der Zähler wird am Ende von `evaluate()` hochgezählt, der Stop-Block läuft
davor. Eine Aufstockung wirkt damit erst ab der FOLGENDEN Kerze — was richtig ist, sonst
könnte ein Nachkauf in derselben Kerze den Stop auslösen, die ihn erzeugt hat.

## Das Risiko, das gemessen werden muss

Die Liquidations-Konfluenz (`liq_entry="boost"`, live) stockt auch ÜBER dem bisherigen
Einstand auf. Beispiel vom 26.08.2026: Ersteinstieg 78.409, Nachkäufe bei 79.089 und
79.024 → Einstand steigt auf 78.807. Mit dem neuen Schalter läge der Stop danach bei
78.807 statt bei 75.546 — ein Rückgang von 1,7 % beendet die Position.

Das ist genau Furkans Absicht („nicht mehr in Verlust gehen"), kann aber bei uns häufiger
auslösen als bei ihm, weil er seine Nachkäufe von Hand setzt und wir mechanisch. **Erwartung
daher: deutlich mehr Stops, kürzere Haltedauer, niedrigere Aufwärts-Beteiligung.** Ob der
vermiedene Verlust das aufwiegt, entscheidet der Backtest.

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `engine/strategy_core.py` | Feld `aufstockungen`, Reset, Zähler, Stop-Zweig, Parameter |
| `engine/main.py` | `be_nach_aufstockung` in `EVAL_DEFAULTS` |
| `site/data/config.json` | Schalter + `_hinweis_be_nach_aufstockung` |
| `engine/backtest.py` | EVAL_KEYS, _BASE, zwei Gitterzeilen |
| `engine/test_strategy_core.py` | Kern-Test + Gegenproben |

## Was bewusst NICHT gemacht wird

- **Kein Puffer über dem Einstand.** Furkan sagt „auf das neue Entry". Mit Gebühren ist man
  dort minimal im Minus; ein Aufschlag wäre unsere Erfindung, nicht seine Regel.
- **Kein Struktur-Tief im neuen Zweig.** Das kann `trail_stop`, wenn es an ist.
- **`be_im_plus` bleibt unangetastet** (gemessen, aus). Der neue Schalter ersetzt es nicht,
  er misst einen anderen Auslöser.
- **Keine Ausnahme für Aufstockungen über dem Einstand.** Erst messen, wie oft das
  schadet — eine Sonderregel vor der Messung wäre geraten.

## NACHTRAG beim Bauen — eine Bedingung, die im Plan fehlte

Der erste Entwurf setzte die Regel wörtlich um: aufgestockt → Stop auf den Einstand. In der
Probe entstand ein **Karussell**: Die Kaufleiter kauft mit kleinen Tranchen (15 %) in einen
fallenden Kurs, der Einstand sinkt kaum mit und liegt damit ÜBER dem Kurs. Der Stop lag
folglich über dem Markt und feuerte sofort — vier Stop-und-Wiedereinstieg-Zyklen in acht
Kerzen.

Bei Furkan kann das nicht passieren: Seine Tranchen sind groß genug, dass der Einstand
spürbar fällt, und er setzt seine Nachkäufe von Hand, wenn der Kurs bereits gedreht hat.

**Ergänzte Bedingung:** Die Regel wird erst scharf, wenn der Kurs den Einstand einmal
überschritten hat (Merker `be_auf_aktiv`, bei Short spiegelbildlich). Das ist keine
Abschwächung, sondern die einzige Lesart, die trägt: Er sagt *„mit der Position möchte ich
nicht mehr in Verlust gehen"* — die Regel schützt einen Gewinn, den man **hat**. Wer im
Minus steht, hat nichts zu schützen.

Der Merker ist aus demselben Grund nötig wie seinerzeit bei `be_im_plus` (E19.3): Genau in
der Kerze, in der der Stop greifen soll, steht der Kurs schon wieder unter dem Einstand —
eine Prüfung im Moment des Zugriffs käme immer zu spät.

## Etappen

- **E28.1** Kern in `strategy_core.py` + Tests · Status: FERTIG (28.08.2026)
- **E28.2** Durchreichung (`main.py`, `config.json`) · Status: FERTIG (28.08.2026)
- **E28.3** Backtest-Varianten · Status: FERTIG (28.08.2026)
