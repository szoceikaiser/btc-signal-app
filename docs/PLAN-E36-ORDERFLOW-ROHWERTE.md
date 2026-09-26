# E36 — Furkans sieben Rohwerte im Lage-Abruf

Status: BAUPLAN 19.09.2026

## Anlass

Kaiser, 19.09.2026:

> *„Furkan Yildirim hatte in dem YouTube-Video über Orderflow seine Herangehensweise
> geschildert, wie er die Indikatoren liest und zu welcher Strategie er dadurch
> entwickelt. Wir haben sehr viele Indikatoren getestet und viele davon für unsere
> Engine verworfen. An der Engine darf auch nichts verändert werden. Jedoch: Können wir
> die Indikatoren aus seinem Video für diesen manuellen Button freischalten?"*

Der Gedanke ist richtig und folgt der Linie, die sich in diesem Projekt bewährt hat:
**Was als Regel schadet, kann als Anzeige nützen.** Zwölf Filter wurden gemessen, zwölf
waren schlechter — aber der Lage-Abruf handelt nicht. Dort kostet ein Indikator nichts.

## Der Befund: alle sieben Werte liegen längst vor

Die Engine holt bei jedem Lauf genau die Größen, die Furkan im Video abliest. Sie
fließen in `classify_pattern` ein — angezeigt wird aber nur das **Ergebnis**
(„gesunder Trend", „Derivate-Pump"). Die Zahlen dahinter hat nie jemand gesehen.

| Furkans Größe | Feld | Quelle |
|---|---|---|
| Spot-CVD | `spot_cvd` | Binance Vision |
| Futures-CVD | `fut_cvd` | Coinalyze (`fut_delta_by_ts`, E16) |
| Open Interest | `oi` | Coinalyze (`oi_by_ts`) |
| Funding | `funding` | Kraken Futures |
| Long-Liquidationen | `long_liq` | Coinalyze (`liquidations_by_ts`) |
| Short-Liquidationen | `short_liq` | dito |
| Long/Short-Positionierung | `long_pct` | Coinalyze (`long_short_by_ts`, E16) |

Es muss also **nichts beschafft werden, nur ausgegeben.**

## Wie Furkan sie liest (Transkript, wörtlich)

**CVD** (8:05–9:38):

> *„Spotmarkt-CVD grau, **echte Nachfrage**, Angebot ohne Hebel, das ist qualitativer
> Flow. Future-CVD ist orange … der **gehebelte Flow**, oft taktisch, oft kurzfristig.
> … Spot-CVD steigt und Future-CVD ist flach — das ist ein Indiz dafür, dass dieser
> Anstieg über die Spot-Nachfrage kommt und **das ist gesund**. … Futures-CVD hoch,
> Spot-CVD flach oder geht sogar runter: Derivate treiben die Bewegung, und diese
> Bewegung ist dann **anfällig für einen Long Flush**."*

**Open Interest** (10:06–10:52):

> *„Geht der Preis hoch und Open Interest [steigt], dann kommt **neues Geld** rein,
> Trend kann tragen. … Steigt der Preis und Open Interest fällt, bedeutet das, dass der
> Preis steigt, weil vor allem Short-Positionen zwangsgeschlossen werden, also ein
> **Short Squeeze** … ohne neues Geld. Wenn der Preis runtergeht, während Open Interest
> ebenfalls runtergeht, ist das ein klassischer **Long Flush, ein Wipeout** — und das
> ist oft auch etwas Positives."*

**Funding** (11:10–11:26):

> *„Funding ist … die Differenz zwischen den Futuremärkten und den Spotmärkten. Daraus
> kann man ableiten, woher der Move kommt, ob wir **überhebelt** sind."*

Die vier Muster (13:08–15:03) sind dann Kombinationen dieser Größen — genau das, was
`classify_pattern` schon rechnet.

## Soll-Zustand

Eine neue Funktion `orderflow_detail(candles, flow, fenster)` liefert je Größe:
Wert, Richtung (`steigt` / `faellt` / `flach`) und Klartext. Der Lage-Abruf zeigt sie
als Block, gefolgt vom Muster — damit sichtbar wird, **woraus** das Muster entsteht.

### Das Fenster: 12 Kerzen (2 Tage)

Bewusst dasselbe Fenster wie `classify_pattern` (dort `window=12`). Nur so erklären die
Rohwerte das Muster, das darunter steht. Ein abweichendes Fenster würde Zahlen zeigen,
die zur Schlussfolgerung nicht passen — und das wäre schlimmer als gar keine Zahlen.

### Die Schwelle für „flach" ist eine Setzung

Furkan sagt „flach" und meint es im Augenmaß. Mechanisch braucht es eine Grenze.
Gewählt: **ein Drittel der typischen Fensterbewegung** (Median der absoluten
Fensteränderungen über die verfügbare Historie). Das kalibriert sich selbst und kommt
ohne willkürliche USD-Zahl aus, die bei anderem Kursniveau falsch wäre.

Das ist **keine Messung**, sondern eine Setzung — wie die Gleichgewichtung der Ampel
in E34. Sie wird hier offen als solche benannt, weil der Abruf nichts handelt und die
Schwelle damit nur die Lesbarkeit betrifft, nicht das Ergebnis.

### Fehlende Daten werden als fehlend gezeigt

Ohne Coinalyze-Schlüssel bleiben `fut_cvd` und `long_pct` bei 0. Eine Zeile
„Futures-CVD 0 $ — flach" wäre dann **falsch**: Sie behauptet Stillstand, wo in
Wahrheit nichts bekannt ist. Solche Größen werden als *keine Daten* ausgewiesen
und aus dem Block genommen.

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `engine/strategy_core.py` | `orderflow_detail()` |
| `engine/telegram_notify.py` | Block im Lage-Abruf |
| `engine/main.py` | Rohwerte in `lage_abruf()` mitgeben |

## Bewusst NICHT gemacht

- **Kein Eingriff in die Engine.** `evaluate()` wird nicht angefasst, kein neuer
  Schalter, keine neue Gitterzeile. Kaisers Vorgabe — und die Messlage stützt sie.
- **Keine neue Datenquelle.** Alles liegt vor; Heatmaps und Orderbuch-Tiefe, die Furkan
  ebenfalls zeigt, bleiben außen vor (keine freie Historie, nicht prüfbar).
- **Keine Bewertung der Rohwerte.** Der Block zeigt Zahlen und Richtungen. Die
  Zusammenfassung bleibt bei Muster und Ampel, die es schon gibt.
- **Nur im Lage-Abruf.** Plan und Vorschau bleiben unverändert — sie sollen kurz
  bleiben, und Kaiser hatte die Nachrichtenzahl schon als grenzwertig bezeichnet.

## Umsetzung — fertig (19.09.2026)

**228 Tests grün. Dreizehn Sabotagen, alle gefangen** — eine erst nach einer Korrektur.

| Eingriff | gefangen von |
|---|---|
| Fehlende Daten werden als 0 gezeigt | 2 Tests |
| „flach" verschwindet | `test_orderflow_richtung_kennt_flach` |
| Richtung vertauscht | `test_orderflow_richtung_kennt_flach` |
| Anderes Fenster als das Muster | `test_orderflow_richtung_kennt_flach` |
| Spot-CVD fällt aus dem Block | 3 Tests |
| Futures-CVD fällt aus dem Block | 2 Tests |
| Positionierung ohne Daten gezeigt | `test_orderflow_detail_zeigt_fehlende_daten_nicht_als_null` |
| Liquidationen ohne Daten gezeigt | dito |
| Furkans Wortwahl fällt weg | `test_lage_abruf_enthaelt_furkans_rohwerte` |
| Block fällt aus der Nachricht | dito |
| Fenster steht nicht mehr in der Nachricht | dito |
| Abruf reicht die Rohwerte nicht durch | dito |
| `evaluate()` ruft die Anzeige doch auf | `test_orderflow_detail_ist_reine_anzeige` |

### Derselbe Testfehler zum dritten Mal — und was daraus folgt

Der „flach"-Test benutzte eine Reihe mit einer Fensteränderung von **exakt 0**. Dort
greift aber der triviale Zweig am Ende der Funktion (`return "flach"`), nicht die
Schwellenregel. Die Sabotage „’flach‘ verschwindet" überlebte deshalb unbemerkt: Der
Test sah richtig aus und berührte die geprüfte Regel nie.

Das ist nach E34 („zwei leere Listen verglichen") und E35 („Zusicherung unter einem
`if`, das nie zutraf") der **dritte Fall desselben Musters** in drei Ausbaustufen.

Korrigiert mit einem Szenario, dessen Änderung **klein, aber nicht null** ist (+120 bei
einer Schwelle von 400) — plus zwei Zusicherungen davor, die festhalten, dass das
Szenario die Regel überhaupt trifft:

```python
assert r["aenderung"] > 0, "Szenario passt nicht - die Aenderung muss > 0 sein"
assert 0 < r["aenderung"] < massstab * OF_FLACH_ANTEIL, "Szenario trifft die Regel nicht"
```

**Übertragbar, und inzwischen die wichtigste Testregel dieses Projekts:** Ein Test muss
nachweisen, dass sein Szenario den geprüften Zweig **erreicht**. Ein grüner Test ohne
diesen Nachweis ist kein Beleg — und die Sabotage-Probe ist bisher jedes Mal das
einzige gewesen, was den Unterschied gezeigt hat.

### So sieht der Abruf jetzt aus

```
Order-Flow im Detail (letzte 48 Stunden):
  Preis                              -4,9 %  faellt
  Spot-CVD                      +52,4 Mio $  steigt   (echte Nachfrage, ohne Hebel)
  Futures-CVD                   +10,4 Mio $  steigt   (gehebelter Flow, oft kurzfristig)
  Open Interest         -2,0 Mio $ (-0,2 %)  flach    (unveraendert)
  Funding                         -0,0071 %  faellt   (Shortueberhang)
  Long-Liquidationen             26,0 Mio $           (Longs wurden geschlossen)
  Short-Liquidationen             8,9 Mio $           (Shorts wurden geschlossen)
  Positionierung                  54 % long           (mehrheitlich long)
```

Darunter stehen unverändert die Lage-Zeile (mit dem Muster) und die Ampel. Die Rohwerte
erklären also, **woraus** das Muster entsteht — ohne selbst etwas zu behaupten.

## E36.1 — Die Tests waren sechs Tage rot, und niemand hat es gesehen

Nachtrag 19.09.2026. Kaiser meldete eine Fehlermeldung des `Tests`-Workflows. Der Blick
in die Lauf-Historie zeigte: **Lauf #80 am 13.09. war der letzte grüne.** Seither jeder
Lauf rot — #81, #82, #83, #84, #85.

### Der Fehler

```
AssertionError: Panel-Zeile weicht von config.json ab: {'trend_ema': (50, 200)}
```

E33 (13.09.) hob `trend_ema` von 50 auf 200 — in `evaluate()`, in `EVAL_DEFAULTS` und
in `config.json`. In `_BASE` (backtest.py) blieb es bei 50. Folgenlos fürs Ergebnis,
weil `trend_filter` überall aus ist und `trend_ema` dann nie gelesen wird — aber die
Panel-Zeile bildete die Live-Einstellung nicht mehr ab.

**Der Test, der genau davor warnt, existierte längst** und hat auch angeschlagen. Sechs
Tage lang, bei jedem Push.

### Warum ich es nicht gesehen habe

```python
if not cfg_datei.exists():                     # ohne Repo-Daten nichts zu pruefen
    return
```

Meine Arbeitskopie enthält nur `engine/` — ohne `site/data/` daneben. Der Test kehrte
dort **stillschweigend** zurück und meldete „bestanden". Auf GitHub, wo das ganze Repo
liegt, lief er und fiel.

Ich habe also sechs Tage lang „228 Tests grün" gemeldet, während die Prüfung, die es
wissen musste, in meiner Umgebung gar nicht stattfand. Dass die Zahl stimmte, machte
es schlimmer, nicht besser: Sie sah nach Deckung aus, die es nicht gab.

### Zwei Korrekturen

1. **`_BASE` steht jetzt auf `trend_ema=200`.** Tests wieder grün.
2. **Die Arbeitsumgebung bildet das Repo ab.** `site/data/` liegt jetzt neben
   `engine/`, mit den echten Live-Dateien. Ein Testlauf, der die Repo-Struktur nicht
   hat, prüft nicht dasselbe wie GitHub.
3. **Der Test überspringt sich nicht mehr still.** Fehlt die Datei, steht jetzt
   `UEBERSPRUNGEN: site/data/config.json fehlt - Panel-Zeile ungeprueft!` im
   Protokoll. (Gegengeprüft: die Zeile erscheint tatsächlich, wenn `site/data` fehlt.)

### Der vierte Fall desselben Musters

Zum vierten Mal in drei Ausbaustufen: **eine Prüfung, die grün meldet, ohne
stattgefunden zu haben.**

| | Stufe | Form |
|---|---|---|
| 1 | E34 | Test verglich zwei leere Listen |
| 2 | E35 | Zusicherung stand unter einem `if`, das nie zutraf |
| 3 | E36 | Szenario erreichte den geprüften Zweig nicht (Änderung exakt 0) |
| 4 | **E36.1** | **Test übersprang sich still — in meiner Umgebung, nicht im Code** |

Die ersten drei fand die Sabotage-Probe. Den vierten fand sie **nicht**, weil er gar
nicht im Code saß, sondern in der Umgebung, in der ich sabotiere. Er wurde nur
sichtbar, weil Kaiser eine E-Mail bekam.

**Daraus folgt eine Regel, die über das Testschreiben hinausgeht:** Die Zahl „N Tests
grün" ist wertlos, solange nicht feststeht, dass N in der richtigen Umgebung erreicht
wurde. Künftig gehört zu jeder Meldung dieser Zahl, dass der Lauf die Repo-Struktur
hatte — und ein Blick auf die GitHub-Lauf-Historie, nicht nur auf die eigene.

## E36.2 — Kaisers zwei Funde am fertigen Ergebnis

Nachtrag 19.09.2026, nach der ersten echten Telegram-Nachricht.

### Fund 1: Die Spot-Nachfrage widersprach sich

```
Spot-CVD  +177,7 Mio $  steigt          <- Rohwert-Block, 48 h
Spot-Nachfrage nachgelassen              <- Lage-Zeile, 12 h
```

Zwei Zahlen unter fast demselben Namen, **über verschiedene Zeiträume**, ohne dass der
Zeitraum dabeistand. Beides war richtig: Über zwei Tage floss viel Spot-Geld herein,
in den letzten 12 Stunden kippte der Zufluss.

Besonders ärgerlich, weil im Bauplan oben wörtlich steht, ein abweichendes Fenster
wäre „schlimmer als gar keine Zahlen" — ich hatte dabei nur an `classify_pattern`
gedacht und `spot_nachfrage` übersehen, das mit `SPOT_FENSTER` (12 h) rechnet.

**Behoben:** Die kurze Ebene steht jetzt darunter, **wenn sie in die andere Richtung
zeigt**. Der Unterschied ist die eigentliche Information — ein Tempoverlust, und genau
darauf achtet Furkan.

Die Richtung dieser Zusatzzeile folgt dem **Vorzeichen**, nicht dem Maßstab: Nach
Maßstab gerechnet hieße −11 Mio nach typischen +48 Mio „flach" — richtig gerechnet,
aber am Punkt vorbei.

### Fund 2: Die Größenordnung beim Futures-CVD ging unter

`+7 Tsd $ steigt` neben `+177,7 Mio $` — rechnerisch richtig, aber es verdeckt die
Aussage. Dass der Hebel praktisch keine Rolle spielt, **ist** Furkans „gesunder Trend".
Jetzt steht das Verhältnis dabei; unter 0,5 % als Klartext („verschwindend gegen den
Spot"), weil „0,0 % des Spot-Flows" nach einem Rechenfehler aussieht.

### Fund 3 (der größte): Die Nachricht war auf dem Handy unlesbar

Kaisers Screenshot zeigte, was ich nie geprüft hatte: **Telegram rendert den Text
proportional und ohne `parse_mode`.** Eine Spaltenausrichtung mit Leerzeichen kann dort
gar nicht funktionieren — und jede zu lange Zeile bricht zwei- bis dreimal um.

Gemessen an der alten Fassung: **praktisch jede Zeile zu lang, bis zu 210 Zeichen.**

**Behoben:** Kurze Zeilen mit Doppelpunkt statt Tabellen, Pfeile (↑ ↓ →) statt Wörtern,
und jeder Fließtext wird selbst umgebrochen (`_umbruch`, `ZEILE_MAX = 38`). Plan und
Vorschau bleiben bewusst unverändert — deren Zeilen sind kürzer, und ein ungefragter
Umbau hätte Kaisers gewohnte Nachrichten verändert.

Die Zeilenlänge ist jetzt eine **geprüfte Regel**
(`test_lage_nachricht_bleibt_handy_tauglich`), für beide Zweige der Nachricht.

### Neun Sabotagen — drei entkamen zuerst

**233 Tests grün.** Beim ersten Durchlauf blieben drei ungefangen:

| Entkommen | Warum | Behoben durch |
|---|---|---|
| `ZEILE_MAX` auf 99 hochgesetzt | **Der Test prüfte gegen dieselbe Konstante, die er absichern soll** — die Messlatte wanderte mit | feste Zahl `HANDY = 38` im Test, plus `assert ZEILE_MAX <= HANDY` |
| Zusatzzeile nimmt Maßstab statt Vorzeichen | im Testszenario sagten beide dasselbe | Szenario, das beide trennt, mit Nachweis davor (`assert roh["richtung"] == "flach"`) |
| Fenster der Zusatzzeile weicht ab | gar kein Test dafür | eigener Test auf `SPOT_FENSTER` |

**Der erste ist eine neue Variante des bekannten Musters:** Ein Test, der seinen
Grenzwert aus dem geprüften Code importiert, prüft nichts — er stellt nur fest, dass
der Code mit sich selbst übereinstimmt. Das ist der fünfte Fall in vier Ausbaustufen
und gehört in dieselbe Reihe wie „leere Listen", „`if`, das nie zutrifft", „Zweig nicht
erreicht" und „Test übersprang sich still".

### So sieht die Nachricht jetzt aus

```
🔎 LAGE AUF ABRUF
Annahme: LONG-Position

Kurs 81.136 $

Aufwaerts-Bein
76.264 $ -> 82.300 $

0.5-Level: 79.282 $
Golden Pocket: 78.377 $
  bis 78.570 $
0.786-Zone: 77.556 $
Ungueltig ab: 76.264 $

ORDER-FLOW (48 h)

Preis: +6,1 % ↑
Spot-CVD: +177,7 Mio $ ↑
  echte Nachfrage, ohne Hebel
... letzte 12 h: -8,2 Mio $ ↓
  zuletzt gedreht
Futures-CVD: +7 Tsd $ ↑
  verschwindend gegen den Spot
Open Interest: +507,4 Mio $ (+6,1 %) ↑
  neues Geld kommt herein
Funding: +0,0038 % ↓
  Longueberhang
Long-Liquidationen: 9,2 Mio $
Short-Liquidationen: 90,8 Mio $
Positionierung: 47 % long
  mehrheitlich short
```
