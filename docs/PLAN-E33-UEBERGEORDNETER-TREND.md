# E33 — Übergeordneter Trend: Historie, Messung, Anzeige

Status: GEBAUT 13.09.2026 — Messung steht aus

## Anlass

Kaiser: *„wir brauchen den übergeordneten bias. ist dafür dann eine längerfristige
beobachtung der preisentwicklung, der anderen indikatoren nicht sinnvoll. … Arbeitet
Furkan nicht auch mit Langzeitindikatoren wie EMA?"*

## Was das Transkript sagt — und was nicht

**Furkan nutzt KEINE technischen Langzeitindikatoren.** Wörtlich (15:58–16:27):

> *„Ich versuche das Ganze so simpel wie möglich zu halten. **Ich benutze keine 17
> verschiedenen Indikatoren.** … Natürlich gibt es ganz wichtige Faktoren wie
> **Makrokorrelation**. Was ist wahrscheinlich, was am **US-Aktienmarkt** passiert? Was
> ist wahrscheinlich mit den **US-Staatsanleihen, deren Zinsen, Renditen** — das spielt
> immer übergeordnet erstmal eine Rolle, **damit ich überhaupt erstmal meinen Bias habe.
> Gehe ich eher long, gehe ich eher short, übergeordnet.**"*

Sein Bias kommt von **außerhalb des Charts**. Kein EMA, kein gleitender Durchschnitt.

Die EMA-Idee stammt aus `docs/STRATEGIE.md` §5 und ist dort ehrlich als **Behelf**
gekennzeichnet: *„App-Umsetzung: einfacher Trendfilter, z. B. Preis vs. EMA200 auf 1D …
kein Makro-Feed verfügbar."*

`signal-app/PLAN-E8.5-KI-MAKRO-BIAS.md` (24.07.2026, nie gebaut) nennt den Grund, warum
Furkans echte Methode schwierig ist: **Ein KI-Makro-Bias ließe sich nicht rückwirkend
prüfen.** Man kann nicht fragen, was eine KI im März 2026 gesagt hätte, ohne dass sie
den weiteren Verlauf kennt.

Deshalb dieser Zwischenschritt: der **mechanische**, backtestbare Trend. Er ist nicht
Furkans Methode, aber er ist messbar — und wenn er nichts bringt, weiß man das, bevor
man die teure, unmessbare Lösung baut.

## Zwei Befunde aus dem Code

**1. Der Trendfilter ist längst gebaut — und wurde nie gemessen.**
`trend_filter` + `daily_trend()` (Preis gegen Tages-EMA) existieren seit E8.5. Aber:
Der Schalter steht **nicht in `config.json`** (live gar nicht erreichbar), und im
Backtest-Gitter gibt es **keine einzige Zeile**, die ihn misst.

**2. Ein stiller Fehler: `EMA200` ist in Wahrheit ein `EMA67`.**
`daily_trend()` rechnet `ema(closes, min(period, len(closes)))`. Die Live-Engine lädt
`LIMIT = 400` 4h-Kerzen = **67 Tage**. Wer `trend_ema=200` einstellt, bekommt also
klaglos einen EMA über 67 Tage.

Nachgemessen (13.09.2026, konstruierte Serie über 1300 Kerzen):

| Ladefenster | Tage | „EMA200" ergibt |
|---|---|---|
| 400 Kerzen | 67 | 124.108 |
| 1200 Kerzen | 201 | **102.438** |

**21 % Unterschied, ohne jede Warnung.** Und schlimmer: Der Backtest sieht das volle
Fenster und rechnet den echten EMA200 — Live und Messung würden verschiedene Dinge tun.

## Soll-Zustand

### A — Historie und ehrliche Messung

1. **`fetch_spot(limit)` mit Paginierung.** Binance liefert höchstens 1000 Kerzen je
   Abruf (der Backtest paginiert deshalb bereits in 1000er-Blöcken). Die Live-Engine
   holt künftig 1300 Kerzen ≈ 217 Tage in zwei Abrufen.
2. **`LIMIT = 1300` nur für den Hauptlauf.** Die Flush-Wache (alle 15 Minuten) bleibt
   bei 400 — sie braucht keinen Trend, und ihre Last soll nicht verdoppelt werden.
3. **`daily_trend(..., streng=True)` gibt `None`, wenn weniger Tage als `period`
   vorliegen.** Lieber keine Aussage als eine falsche. `_trend_ok()` blockiert bei
   `None` nichts — unbekannt heißt nicht „verboten".
4. **`trend_filter` und `trend_ema` in `config.json`**, Default aus / 200.
5. **Zwei Gitterzeilen:** Trendfilter mit EMA50 und mit EMA200.

### B — Anzeige statt Regel

Der übergeordnete Trend kommt in die **Lage-Zeile** von Plan und Vorschau, unabhängig
davon, ob `trend_filter` an ist:

```
Lage:  Uebergeordnet: Kurs 77.279 $ unter EMA200 (79.140 $)
       Struktur intakt - hoeheres Tief 76.264 $, hoeheres Hoch 82.300 $
       Spot-Nachfrage nachgelassen (die Nachfrage hat gedreht)
       Muster: ungesunder Abverkauf (der Dip wird nicht gekauft)
```

Begründung: Dieses Projekt hat neun Order-Flow-**Filter** gemessen, alle waren
schlechter. Die **Anzeige** dagegen (E32.1) kostet nichts und lässt Kaiser entscheiden —
so, wie Furkan es auch tut. Erst wenn die Messung zeigt, dass der Filter etwas bringt,
wird daraus eine Regel.

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `engine/main.py` | `fetch_spot()` mit Paginierung; `LIMIT` 400 → 1300; Flush-Wache bleibt bei 400; `EVAL_DEFAULTS` um `trend_filter`/`trend_ema` |
| `engine/strategy_core.py` | `daily_trend(..., streng)`; `trend_lage()`; Trend in `lage_bericht()` |
| `engine/telegram_notify.py` | Trend-Zeile in der Lage-Ausgabe |
| `engine/backtest.py` | zwei Gitterzeilen |
| `site/data/config.json` | `trend_filter: false`, `trend_ema: 200` + Hinweistexte |

## Geprüft, bevor gebaut wurde

**Ändert mehr Historie die Signale?** Nachgemessen mit einer 1300-Kerzen-Serie, Live-
Einstellung, letzte 60 Kerzen: **7 Signale bei 400, 7 Signale bei 1200 — identisch**,
gleicher Endzustand. Das war die Voraussetzung dafür, `LIMIT` überhaupt anfassen zu
dürfen. Ein Test hält es fest.

Der Grund ist nachvollziehbar: `atr` sieht 14 Kerzen, `classify_pattern` 12,
`last_significant_impulse` läuft rückwärts und nimmt das jüngste taugliche Bein. Nur
`daily_trend` und `daily_fib_zone` resampeln die **gesamte** Historie — und beide hängen
an Schaltern, die aus sind.

## Bewusst NICHT gemacht

- **Kein KI-Makro-Bias.** Furkans echte Methode, aber nicht backtestbar. Erst messen,
  ob die billige Lösung reicht.
- **Der Trendfilter wird nicht live geschaltet.** Default aus, bis gemessen.
- **Die Flush-Wache lädt weiterhin 400 Kerzen.** Sie prüft nur die laufende Kerze.
- **Kein EMA auf 4h.** Der übergeordnete Trend ist per Definition die Tagesebene.

## Umsetzung — fertig (13.09.2026)

196 Tests grün. **Sechs Sabotagen, alle gefangen** — zwei davon erst im zweiten Anlauf,
und beide Male deckten sie echte Mängel auf:

| Eingriff | gefangen von |
|---|---|
| `streng` wird ignoriert (stiller Kurz-EMA kehrt zurück) | 4 Tests |
| Trend-Richtung vertauscht | `test_trend_lage_liefert_klartext_oder_nichts` |
| Trend fällt aus der Nachricht | `test_uebergeordneter_trend_steht_in_den_nachrichten` |
| `trend_period` wird ignoriert | `test_lage_bericht_nimmt_den_trend_auf` |
| Paginierung lädt nur den ersten Block | `test_fetch_spot_paginiert_ueber_1000_kerzen` |
| Notbremse entfernt | `test_fetch_spot_bricht_ab_wenn_die_api_nicht_vorankommt` |

### Zwei Fehler, die erst die Sabotage-Probe gezeigt hat

**1. Endlosschleife in `fetch_spot`.** Die erste Fassung prüfte nur `fehlt > 0`. Hätte
die API wiederholt Daten geliefert, ohne dass die Liste wächst, wäre die Schleife ewig
gelaufen — im 15-Minuten-Takt ein hängender Workflow, der niemandem auffällt. Behoben
durch eine Obergrenze (`MAX_ABRUFE`) **und** eine Fortschrittsprüfung.

**2. Die Fortschrittsprüfung war toter Code.** Sie verglich die *Listenlänge* — die
wächst aber auch, wenn die API zweimal denselben Block liefert (dann mit Duplikaten).
Die Sabotage bewirkte deshalb nichts, was den Mangel entlarvte. Jetzt wird geprüft, ob
die Historie tatsächlich **weiter zurückreicht**: `int(out[0][0]) >= aeltester → break`.

### Was live geschaltet ist — und was nicht

- **Live: nichts am Handelsverhalten.** `trend_filter` steht auf `false`.
- **Live: die Anzeige.** Der übergeordnete Trend steht ab dem nächsten Engine-Lauf in
  Plan und Vorschau — an erster Stelle der Lage, weil er den Rahmen setzt.
- **Live: mehr Historie.** Der Hauptlauf lädt 1300 statt 400 Kerzen. Nachgewiesen
  signalneutral.

## Gemessen — 13.09.2026, 12:57 UTC (60 Varianten)

**Der Trendfilter ist durchgefallen, und zwar deutlich.** `trend_filter` bleibt aus.

| Variante | Rendite | max. Rückgang | Signale | Aufwärts | Abwärts |
|---|---|---|---|---|---|
| **LIVE-heute +Zonen nachziehen** | **+30,9 %** | −9,7 % | **251** | 47 % | −11 % |
| +Trendfilter EMA200 | **−0,4 %** | −9,2 % | **49** | **1 %** | 1 % |
| +Trendfilter EMA50 | +4,7 % | −10,6 % | 111 | 7 % | −3 % |

Die Signalzahl sagt alles: **von 251 auf 49.** Der Filter schaltet die Engine nicht
schärfer, er schaltet sie **ab** — 80 % aller Einstiege fallen weg, und die
Aufwärts-Beteiligung bricht von 47 auf **1 %** ein. Die Variante steht in der ersten
Fensterhälfte auf **Platz 59 von 60**, die EMA50-Zeile auf Platz 58.

Die Gegenprobe beantwortet auch ihre Frage: Es liegt **nicht an der Länge**. EMA50 ist
zwar weniger schlimm (111 statt 49 Signale), aber ebenfalls weit unter der Live-Zeile.
Beide Weiten scheitern an derselben Sache.

### Warum das plausibel ist — und was es NICHT heißt

Die Engine handelt Rücksetzer in einem Aufwärtsbein. Ein Rücksetzer ist definitionsgemäß
ein Kursrückgang; ein Filter „nur kaufen, wenn der Kurs über der Tages-EMA200 liegt"
schließt genau die Momente aus, in denen ein Fib-Retracement überhaupt erreicht wird.
Der Filter widerspricht der Strategie, statt sie einzuschränken.

**Das heißt nicht, dass Furkans Bias-Ebene wertlos ist.** Es heißt, dass ein Tages-EMA
nicht ihr Ersatz ist. Furkan sagt es selbst (15:58): *„Ich benutze keine 17 verschiedenen
Indikatoren"* — sein Bias kommt aus Makro, nicht aus dem Chart. Der EMA war der
backtestbare Behelf; er ist jetzt gemessen und erledigt. Damit ist der Weg frei, die
Frage offen zu lassen, statt sie mit einem Indikator zu besetzen, der sie nicht
beantwortet.

### Was bleibt

- **`trend_filter` bleibt aus** — gemessen und durchgefallen, nicht „noch offen".
- **Die Trend-Anzeige bleibt.** Der Kurs gegen die Tages-EMA200 steht weiter an
  erster Stelle der Lage. Als *Information* kostet sie nichts.
- **Die 1.300 Kerzen Historie bleiben.** Sie waren die Voraussetzung dafür, dass der
  EMA200 überhaupt ein EMA200 ist — und ohne sie wäre die Messung eine Messung des
  falschen Dings gewesen (siehe „Ein stiller Fehler" oben).
