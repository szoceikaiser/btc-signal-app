# Auswertung: Furkans zweites Update-Video (Juli 2026, „Playbook vor der Zinsentscheidung")

Stand: 2026-07-27 · Quelle: Transkript mit Zeitstempeln, von Kaiser eingefügt.
Zeitlich NACH dem ersten Update: Position inzwischen im Schnitt bei 59.700 eröffnet,
zweimal Teilgewinne realisiert (zuletzt ~66.100), Kurs ~65.000.

Wie beim ersten Video: nur umsetzbare Punkte. Marktmeinung (Strategy, BlackRock-ETF-
Kritik, Börsenpleiten, Zinsentscheidung, Netto-Verschuldung der US-Privatanleger) ist
interessant, aber nichts, was in Code geht.

## 1. Stop bei JEDER Aufstockung auf Break-even — Präzisierung zu E9.10

Zitat 18:42–18:57: *"Dementsprechend würde ich dann auch mein Stop wieder über den Entry
setzen, weil ich mit der Position kein Risiko eingehen möchte. Also ich werde **bei
Aufstockung immer wieder** meinen Stop in Profit oder auf Break even setzen, dass ich aus
dieser Position keinen Verlust mehr machen kann."*

Unser `trail_stop` (E9.10) zieht den Stop nach, sobald **Teilgewinne** realisiert sind
(TP1/TP2 oder eine Leiter-Stufe). Furkan zieht ihn zusätzlich bei **jeder Aufstockung**
nach — also auch beim Nachkauf im Golden Pocket, ohne dass vorher verkauft wurde.

**Baubar, klein:** Auslöser des Nachziehens um „Position wurde aufgestockt" erweitern
(`buy_rungs > 0` oder Zustand ≥ CORE). `entry_ref` existiert bereits.

## 2. Liquidationszonen für den EINSTIEG — neu und ungetestet

Zitat 18:27–18:42: *"Wenn man die Liquidierungszonen anschaut, unter uns liegt deutlich
mehr. Es sind viele Long-Positionen dazugekommen, vor allem **ab 61.700 runter bis
60.500**. **Hier liegt dann auch aktuell das Golden Pocket**, wo ich persönlich die
Position wieder aufstocken würde."*

Das ist der wichtigste Punkt des Videos. Er nutzt die Liquidationszone **unter** dem Kurs
als KAUF-Zone — dort werden Longs liquidiert, das erzeugt den Flush, und genau da will er
rein. Und er sucht die **Konfluenz mit dem Golden Pocket**: beide Zonen fallen zusammen,
das macht sie stark.

Wir haben Liquidationsdaten bisher **ausschließlich für Ausstiege** getestet (E9.11) —
und dort haben sie Rendite gekostet. Für **Einstiege** ist es nie gemessen worden. Das
passt exakt zum übergreifenden Befund aus E10.2: Die Verkaufsseite ist auserzählt, die
offenen Hebel liegen bei Richtung und Einstiegen.

**GEBAUT 2026-07-27 (E10.3), Messung ausstehend:** `liq_entry` in evaluate —
`"off"` | `"boost"` | `"filter"`.
- **boost**: zusätzliche Nachkauf-Tranche (20 %), wenn der Kurs in der Fib-Zone UND an
  einem historischen Long-Liquidations-Cluster steht, Struktur intakt und Order-Flow
  bestätigt. Höchstens 2× je Position (`Position.liq_entries`, persistiert).
- **filter**: Einstiege (0.5-Level, Golden Pocket, Flush) NUR noch bei dieser Konfluenz —
  die restriktive Gegenprobe. Erwartung eher schlecht, weil alle bisherigen Filter
  (trend_filter, confluence, strict_confirm) die Rendite gesenkt haben.
- Short spiegelbildlich über Short-Liquidationen am Kerzen-HOCH.
- Helfer `liq_levels` / `in_liq_zone` aus E9.11 wiederverwendet, Niveaus je Seite einmal
  pro Kerze zwischengespeichert.
- **Kausalität** wie bei E9.11 abgesichert: Zonen nur aus `candles[:-1]`/`flow[:-1]`, ein
  eigener Test prüft, dass die Kaskade der aktuellen Kerze den Einstieg nicht selbst
  rechtfertigt. Dabei fiel auf, dass der Test-Helfer `run_incremental` den Flow NICHT
  mitschnitt — für positionsabhängige Flows falsch. Neuer Helfer `run_incremental_flow`
  schneidet beides parallel, genau wie die Produktion es aufruft.
- Live über `config.json` schaltbar. 70/70 Tests grün.

Einschränkung unverändert: unsere Zonen sind rückwärtsgerichtet (wo wurde liquidiert)
und 4h-grob (eine Kerze spannt 1–2 %), nicht Furkans Vorausschau.

### MESSERGEBNIS 2026-07-27 (E10.3)

| Variante | Recall | Präz. | Rendite | max. Rückgang | Signale |
|---|---|---|---|---|---|
| LIVE +Stop (Referenz) | 57 % | 34 % | +29,8 % | −11,5 % | 208 |
| +Liq-Konfluenz aufstocken (`boost`) | 57 % | 32 % | **+29,8 %** | −11,8 % | 227 |
| nur bei Liq-Konfluenz einsteigen (`filter`) | 50 % | 36 % | +22,5 % | −12,2 % | 178 |

1. **`boost` ist exakt neutral.** 19 zusätzliche Konfluenz-Nachkäufe, und die Rendite
   bleibt auf die Nachkommastelle gleich. Die Zonen wurden also gefunden, sie hatten nur
   keinen Vorteil — die Tranchen dort liefen wie der Durchschnitt.
2. **`filter` schadet**, wie bei jedem Filter zuvor: −7,3 Punkte Rendite, Recall 57→50 %.
   Die Präzision steigt auf 36 % (weniger, gezieltere Signale) — und genau das ist die
   Falle, vor der wir uns die ganze Zeit hüten: bessere Trefferquote, weniger Geld.
3. Damit sind Liquidationsdaten auf BEIDEN Seiten gemessen (Ausstieg E9.11, Einstieg
   E10.3). Ergebnis beide Male: kein Renditevorteil. Der freie Rückwärts-Proxy für
   Furkans Heatmap trägt nicht.

**KONSEQUENZ:** `liq_entry` bleibt `off`. Live-Einstellung unverändert.

### ÜBERHOLT — KORREKTUR 28.07.2026: `liq_entry="boost"` ist LIVE

Das Ergebnis oben („exakt neutral") war an einem **gebremsten Mechanismus** gemessen. Der
STOPLOSS-Zweig in `strategy_core.evaluate` setzte die Position nur teilweise zurück und
vergaß unter anderem den Zähler `liq_entries`. Nach wenigen Stops stand er am Maximum, und
der Mechanismus schaltete sich still ab (Details: ETAPPENPLAN E12). Nach dem Fix:

| | vorher (mit Bug) | nachher |
|---|---|---|
| Rendite | +29,7 % („neutral") | **+37,0 %** |
| Platz Hälfte 1 / Hälfte 2 | 1. / **15.** | 1. / **4.** |

Zusammen mit dem Mindest-Stopabstand: **+40,5 % bei −6,9 % Rückgang**, und als eine von
nur zwei Varianten in beiden Zeit-Hälften unter den besten fünf. Furkans Beobachtung aus
18:27 — Golden Pocket und Liquidationszone fallen zusammen, dort aufstocken — trägt also.
**Live seit 28.07.2026.**

**Lehre daraus:** Ein negatives Messergebnis kann am Messaufbau liegen. Bevor eine Idee
verworfen wird, lohnt die Frage, ob der Mechanismus überhaupt gelaufen ist.

## 3. Teilgewinn ÜBER dem alten Hoch, mit kleinerer Tranche

Zitat 19:14–19:21: *"Wichtig wäre, dass wir das Hoch von 67.300 rausnehmen. Das ist
ungefähr der Bereich knapp drüber, wo noch mal eine **Short-Liquidierungszone** ist. Also
hier drüber würde ich noch mal Gewinne realisieren, **ein bisschen weniger** als ich es
bei 66.100 getan habe."*

Zwei Korrekturen an unserem E10.2:
- Wir verkaufen 0,5 % **unter** dem letzten Hoch. Er verkauft dort UND noch einmal
  **darüber**, wo die Short-Liquidationen sitzen. Das Hoch ist für ihn keine Wand,
  sondern der Anfang einer Zone.
- **Die Tranchen werden nach oben kleiner.** Unsere Engine macht es umgekehrt (TV1 40 %,
  TV2 40 %, Leiter je 15 %).

Angesichts des Befunds „Verkaufsseite kostet Rendite" ist beides trotzdem **niedrige
Priorität** — es wäre die sechste Variante desselben Themas.

## 4. Volatilität an historischen Tiefs — kostenlos berechenbar

Zitat 15:00–15:15: *"Schaut euch die implizierte Volatilität an, liegt an historischen
Tiefs. Immer wenn die Volatilität so tief gefallen ist, gab es im Anschluss einen großen
Volatilitäts-Squeeze."*

Implizite Volatilität (aus Optionen) haben wir nicht. Die **realisierte** Volatilität
lässt sich aber aus unseren eigenen Kerzen rechnen (ATR im Verhältnis zum Preis) — ohne
jede neue Datenquelle. Ein Mehrmonats-Tief darin wäre ein Regime-Signal: „gleich wird es
wild".

Was man damit täte, ist offen — kleinere Position? weitere Stops? gar nichts? Ohne klare
Handlung ist es dieselbe Falle wie die Breakout-Warnung. **Erst eine Handlung definieren,
dann bauen.**

## 5. Bestätigt, nicht neu

- 17:45–17:53: *"Spot wird stärker verkauft als über die Future-Märkte, die meisten
  Anstiege kommen über den Futuremarkt"* — genau unser Muster 2 (Derivate-Pump).
- 18:03: *"Long-Positionen werden gerade liquidiert, davor wurden Shorts liquidiert"* —
  Muster 3/4, haben wir.
- 17:36: *"höher werdende Tiefs, höher werdende Hochs, saubere Struktur"* — unsere
  Pivot-Logik.

## Reihenfolge-Vorschlag

1. **Punkt 2 (Liquidationszonen für Einstiege)** — der einzige wirklich neue Hebel, und er
   zielt auf die richtige Seite (Einstiege statt Ausstiege).
2. **Punkt 1 (Stop auch bei Aufstockung)** — klein, ergänzt E9.10 sauber.
3. Punkt 4 nur, wenn vorher eine konkrete Handlung feststeht.
4. Punkt 3 vorerst nicht — die Verkaufsseite ist gemessen und auserzählt.
