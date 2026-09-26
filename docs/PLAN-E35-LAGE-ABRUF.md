# E35 — Lage auf Abruf, und die Ampel zeigt in die richtige Richtung

Status: BAUPLAN 17.09.2026

## Anlass

Kaiser, 17.09.2026:

> *„Zuletzt wurde der Plan ausgestoppt, weil der Stoploss angeschlagen ist nach der
> Beendigung der 4-Stunden-Kerze. Ich habe aber den Stoploss nicht als Limit eingestellt
> und mein Trade läuft jetzt weiter. Jetzt würde ich gerne zwischendurch sehen, wie die
> Struktur aussieht. … Ich würde nämlich beobachten wollen, ob ich jetzt meinen Trade
> weiterlaufen lassen oder ob ich ihn schließen soll."*

Zwei Dinge treffen hier zusammen. Das zweite ist das wichtigere und wäre ohne den
ersten Anlass nicht aufgefallen.

## Der Fehler, der zuerst behoben gehört

**Die Ampel bewertet die Richtung des gefundenen Beins — nicht die, die gehandelt wird.**

`zonen_vorschau()` ruft `ampel(_lage, long_side=imp.up)` auf. Steht live `bias_short:
false`, ist die Engine also reine Long-Engine — aber sobald `last_significant_impulse`
ein **Abwärts**-Bein findet (bei `bein_richtung: "auto"` ist das der Normalfall),
rechnet die Ampel für einen **Short**, den die Engine nie eingehen würde.

Nachgerechnet am Live-Stand vom 17.09.2026, 13:41 UTC (`state.json`):

| Lage | Wert |
|---|---|
| Trend | Kurs 76.482 $ **über** EMA200 (70.184 $) |
| Spot-Nachfrage | stabil |
| Struktur | Bein 79.600 $ → 74.968 $ (abwärts) |

| Ampel gerechnet für | Ergebnis |
|---|---|
| **SHORT** (so stand es in der Nachricht) | `UNGUENSTIG — 0 von 2 sprechen dafuer` |
| **LONG** (was die Engine tatsächlich handelt) | `GUENSTIG — 2 von 2 sprechen dafuer` |

Dieselben Daten, das genaue Gegenteil. Wer die Nachricht liest und long ist — wie
Kaiser gerade —, liest sie falsch herum. **Das ist der gefährlichste Fehlertyp, den
dieses Projekt bisher hatte:** keine falsche Zahl, sondern eine richtige Zahl mit
verkehrtem Vorzeichen, ohne dass etwas auffällt.

Entstanden ist er in E34 (13.09.): Die Ampel wurde richtungsfähig gebaut und in
`zonen_vorschau` an `imp.up` gehängt — die einzige Richtung, die dort verfügbar schien.
Dass das Bein und die handelbare Richtung auseinanderlaufen können, wurde nicht bedacht.
Kein Test hat es gefangen, weil alle E34-Tests die Ampel direkt geprüft haben, nie die
Verdrahtung in der Vorschau.

## Soll-Zustand

### A — Richtung nach dem Bias, nicht nach dem Bein

1. **Ist genau eine Richtung erlaubt** (`bias_long != bias_short`), rechnet die Ampel in
   dieser Richtung — egal, welches Bein gefunden wurde.
2. **Sind beide erlaubt**, bleibt es beim Bein (`imp.up`): dann kann die Engine beides,
   und das Bein ist die beste verfügbare Auskunft.
3. **Die Nachricht nennt die Richtung immer**: `Ampel (fuer LONG): …`. Auch dann, wenn
   sie eindeutig scheint — genau diese Selbstverständlichkeit war der Fehler.

### B — Der Lage-Abruf

`python3 main.py --lage`, ausgelöst über einen Knopf in GitHub Actions.

- **Rechnet unter der Annahme einer Long-Position.** Gesucht wird gezielt das letzte
  signifikante **Aufwärts**-Bein (`nur_auf=True`), unabhängig davon, was
  `bein_richtung` sagt. Findet sich keins, sagt die Nachricht das — statt ersatzweise
  ein Abwärtsbein zu zeigen, das für einen Long nichts bedeutet.
- **Zeigt die vier Angaben und die Ampel**, dazu Kurs, Bein und die Fib-Zonen des
  Aufwärtsbeins (Nachkaufmarken und Invalidierung).
- **Sendet immer**, ohne Dedupe — der Abruf ist ja gerade der Wunsch, jetzt zu sehen,
  wie es steht.
- **Fasst `state.json` nicht an.** Kein Signal, keine Zustandsänderung, kein Einfluss
  auf den nächsten regulären Lauf. Dasselbe Prinzip wie `--watch`.
- **Sagt in der Fußzeile, was sie ist:** ein Abruf unter Long-Annahme, während die
  Engine selbst auf FLAT steht.

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `engine/main.py` | Richtungswahl in `zonen_vorschau`; `lage_abruf()`; `--lage` in der CLI |
| `engine/telegram_notify.py` | `format_lage()`; Richtung im Ampel-Kopf |
| `engine/strategy_core.py` | `ampel_richtung()` — eine Stelle, die die Richtung bestimmt |
| `.github/workflows/lage.yml` | **eigener Workflow** „Lage abrufen“ (nur Handstart, nur Leserechte) |

## Bewusst NICHT gemacht

- **Kaisers tatsächliche Position wird nicht eingetragen.** Die Engine bleibt auf FLAT.
  Ein Nebenzustand „Kaiser ist noch drin, die Engine nicht" wäre eine dauerhafte
  Fehlerquelle; der Abruf rechnet stattdessen ausdrücklich unter einer *Annahme* und
  sagt das auch.
- **Keine Empfehlung.** Die Nachricht sagt nicht, ob gehalten oder geschlossen werden
  soll. Der Schlusssatz der Ampel aus E34 bleibt unverändert stehen.
- **Kein Eingriff ins Handelsverhalten.** `--lage` erzeugt keine Signale und ändert
  keine Marke.
- **Die Backtest-Zeilen bleiben unberührt.** Die Richtungs-Reparatur betrifft nur die
  Anzeige; `evaluate()` hat die Ampel ohnehin nur hinter `ampel_filter` (aus).

## Umsetzung — fertig (17.09.2026)

**222 Tests grün. Zehn Sabotagen, alle gefangen.**

| Eingriff | gefangen von |
|---|---|
| Richtung folgt wieder dem Bein statt dem Bias | 2 Tests |
| Richtung vertauscht (Long/Short) | 4 Tests |
| Vorschau hängt die Ampel wieder ans Bein | `test_vorschau_ampel_folgt_dem_bias_nicht_dem_bein` |
| Richtung fällt aus der Nachricht | 2 Tests |
| Abruf nimmt auch Abwärts-Beine | `test_lage_abruf_erfindet_kein_bein_wenn_keins_da_ist` |
| Abruf rechnet die Ampel für Short | `test_lage_abruf_rechnet_die_ampel_fuer_long` |
| Abruf schreibt `state.json` | `test_lage_abruf_fasst_den_zustand_nicht_an` |
| Zonen werden auch ohne Bein gezeigt | `test_lage_abruf_erfindet_kein_bein_wenn_keins_da_ist` |
| Hinweis auf den echten Zustand fällt weg | `test_lage_abruf_rechnet_die_ampel_fuer_long` |
| Kopfzeile nennt die Annahme nicht mehr | `test_lage_abruf_rechnet_die_ampel_fuer_long` |

### Ein Fehler, den diesmal die Vorprüfung gefangen hat

Drei der neuen Tests prüften die Ampel unter `if out.get("ampel")` — und in allen
drei Szenarien war sie **`None`**. Sie liefen also vollständig ins Leere und wären grün
geblieben, egal was der Code tut. Genau derselbe Fehlertyp wie bei E34 („zwei leere
Listen verglichen"), diesmal aber **vor** der Sabotage-Probe aufgefallen, weil die
Zwischenwerte nachgesehen statt angenommen wurden.

Ursache: Die Ampel schweigt unter zwei Aussagen, und in einem kurzen Testszenario
reicht die Historie für `trend_ema: 200` nie — es sprach nur die Spot-Nachfrage.
Behoben durch `trend_ema: 3` in diesen Tests, mit einer Zusicherung davor
(`assert out["ampel"] is not None, "Szenario passt nicht mehr"`), damit ein späterer
Umbau des Szenarios den Test nicht stillschweigend wieder entwertet.

**Übertragbar:** Ein Test, dessen Kernaussage unter einem `if` steht, ist erst dann
ein Test, wenn nachgewiesen ist, dass die Bedingung im Szenario auch zutrifft.

## Nachtrag 19.09.2026 — eigener Workflow statt Haken

Der Abruf war zuerst als **Eingabe innerhalb von `signal.yml`** gebaut. Kaisers
Einwand: *„diese seite zeigt unser engine. nicht die, welche ich manuell starten
kann.“*

Er hat recht, und die erste Fassung war aus zwei Gründen schlechter:

1. **Unauffindbar.** In der Workflow-Liste erscheint kein eigener Eintrag — der Abruf
   versteckt sich als Option hinter der Signal-Engine.
2. **Gefährlich.** Wer den Haken vergisst und trotzdem auf „Run workflow“ klickt,
   startet einen **echten Engine-Lauf**. Ein Blick auf die Lage darf nie in einen
   Handelslauf umschlagen können.

Korrigiert: `lage.yml` ist ein **eigener Workflow** — kein Zeitplan (nur Handstart),
`permissions: contents: read` (kann am Repo nichts ändern), kein Commit-Schritt, eigene
`concurrency`-Gruppe. Die Eingabe `lage_jetzt` ist aus `signal.yml` wieder entfernt;
zwei Wege für dieselbe Sache wären eine Fehlerquelle.

**Übertragbar:** Ein Modus, der etwas grundsätzlich anderes tut als der Workflow, in
dem er steckt, gehört nicht als Schalter hinein, sondern daneben. Die Absicherung soll
in der Struktur liegen, nicht in der Aufmerksamkeit des Bedienenden.

## Anleitung für Kaiser

**Lage jetzt abrufen:**

1. Tab **Actions** öffnen
2. Links in der Seitenleiste **„Lage abrufen“** anklicken
3. Rechts **„Run workflow“** → grüner Knopf

Nach etwa einer halben Minute kommt die Nachricht per Telegram. Sie ändert nichts —
weder an der Engine noch an einer Marke, und auch nichts am Repo.
