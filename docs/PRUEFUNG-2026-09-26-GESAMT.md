# Gesamtprüfung 26.09.2026: Hat die vorige KI Furkans Strategie richtig verstanden, gebaut und gemessen?

> **Auftrag Kaiser, 26.09.2026:** *„es wurden bisher sehr viele test gemacht und zum teil
> verworfen und der schalter auf aus gestellt. ich möchte, das du alle test nochmals
> eingehend prüft, ob die vorherige ki das ganze richtig verstanden und gebaut hat.
> grundlagen ist das transkript und das video im ordner Videos und anschließend alle
> weiteren in den unterordnern."*
>
> **Am Code wurde nichts geändert.** 444 Tests grün (nachgezählt 26.09.2026).
> Dieser Bericht beschreibt Befunde und schlägt Schritte vor. Gebaut wird erst nach
> Kaisers Zustimmung, nach den fünf Projektregeln (Schalter, Default aus, Gitterzeile,
> Sabotage, Entscheidungsregel vor der Messung).

## Grundlage und Grenzen dieser Prüfung

**Gelesen:** das Tutorial-Transkript (`Transkript.md`) und die vier Update-Transkripte
(`Videos\060727`, `260802`, `260803`, `260913`), das Standbild `Videos\260802\frames\16-12.jpg`,
`docs\STRATEGIE.md`, der Wissens-Layer, `ETAPPENPLAN.md` (auszugsweise), der komplette
Engine-Kern (`strategy_core.py`), die Datenbeschaffung (`main.py`, `coinalyze.py`), die
Backtest-Rechnung (`backtest.py`: Gitter, `build_series`, `simulate`), der letzte
Backtest-Bericht (`BACKTEST.md`, Lauf 23.09.2026) und die gespeicherten Rohdaten
(`site\data\coinalyze_probe.json`, `backtest_signals.json`).

**Nicht möglich:**
- Die Videodateien liegen nicht im Repo (216 MB, per `.gitignore` ausgeschlossen). Geprüft
  wurde gegen die Transkripte und das Standbild.
- Börsen-APIs sind aus der Arbeitsumgebung gesperrt (Binance, Kraken, Coinalyze: HTTP 403).
  Die Fehler in Teil A sind deshalb **mit Kunstdaten nachgestellt** und damit als
  Mechanismus bewiesen. **Wie oft** sie im echten Fenster zugeschlagen haben und was sie an
  Rendite bewegen, ist **nicht gezählt**. Das geht nur über den Backtest auf GitHub, nachdem
  die Korrektur als Schalter gebaut ist.

---

## Kurzfassung

1. **Das Grundgerüst ist richtig verstanden und richtig gebaut:** Fib-Retracement,
   Golden Pocket, 0,786-Zone, Extension-Ziele 1,0 und 1,618 (korrekt als Dreipunkt-Extension
   vom Korrekturtief aus), Tranchen, „nie all in“, dynamische Zonen, keine Kenntnis der
   Zukunft im Backtest. Die Zonen stimmen mit Furkans Chart bis auf 5 bis 15 $ überein.
2. **Die Order-Flow-Muster (Furkans „Kompass“) werden dagegen mit zwei Messfehlern
   erkannt.** Beide sind mit Kunstdaten bewiesen (A2, A3). Einer davon lässt Live-Engine
   und Backtest bei derselben Kerze verschieden entscheiden.
3. **Eine Anzeige im Lage-Abruf zeigt Kaiser falsche Zahlen** (A1): Das Futures-Volumen
   steht als Dollar da, ist aber in BTC. Es sah dadurch um den Faktor Kurs zu klein aus,
   also rund 77.000-mal. Die Aussage „der Hebel spielt praktisch keine Rolle“ war deshalb
   falsch.
4. **Viele Schalter wurden gegen eine Live-Einstellung gemessen, die es nicht mehr gibt.**
   Von 25 ausgeschalteten Schaltern und Datenvarianten sind nur 9 mit genau einem
   Unterschied gegen die heutige (7) oder die unmittelbar vorherige Live-Zeile (2)
   gemessen. Die übrigen 16 liefen gegen ältere Stände. Der auffälligste Fall:
   **„Bein in Handelsrichtung“** entspricht genau Furkans Vorgehen (zwei Fib-Raster,
   Standbild 02.08.). Im Lauf vom 23.09. ist es die beste Zeile des Gitters. Gegen die
   heutige Einstellung wurde es aber nie gemessen, und es steht auf keiner Offen-Liste.
   Die Zahl ist ein Hinweis, kein Beleg (Einzelheiten in Teil C).
5. **Ein Urteil beruht auf einem Lesefehler:** `be_im_plus` wurde als „Furkans ausdrückliche
   Regel, der teuerste Hebel des Projekts“ verbucht. Furkans Regel hat aber eine
   Vorbedingung, die der Schalter weglässt (B, Punkt 7).

---

## Teil A — Vier Fehler, die bewiesen sind

### A1 · Futures-CVD im Lage-Abruf: BTC wird als Dollar angezeigt (Anzeige)

*CVD = kumuliertes Kauf-minus-Verkaufs-Volumen. Spot = echte Käufe ohne Hebel,
Futures = Terminmarkt mit Hebel.*

- Das Spot-Delta kommt von Binance in **Dollar** (`main.py`, Quote-Volumen).
- Das Futures-Delta kommt von Coinalyze `ohlcv-history` in **BTC**. Der Code sagt das selbst
  (`coinalyze.py`, `fut_delta_by_ts`: „EINHEIT: … BTC, nicht USD“). Bestätigt an den
  gespeicherten Rohdaten: Eine 4h-Kerze hat dort `v = 11.190` bei Kurs 81.275. Das sind
  11.190 BTC (rund 909 Mio $), keine 11.190 $.
- `orderflow_detail()` (`strategy_core.py`) gibt den Futures-Wert trotzdem mit
  `_usd_kurz()` als „$“ aus. Außerdem rechnet sie den Anteil „% des Spot-Flows“ als BTC
  geteilt durch Dollar. Das ist rund um den Faktor Kurs (etwa 77.000) zu klein.
- **Folge:** Im Lage-Abruf stand z. B. „Futures-CVD +7 Tsd $ … verschwindend gegen den Spot“
  neben „Spot-CVD +177,7 Mio $“. Tatsächlich waren es rund +7.000 BTC, also bei einem Kurs um 77.000 $
  rund **540 Mio $**, etwa das Dreifache des Spot-Wertes. Nach Furkan (Transkript 9:00–9:31) ist das eher
  „Derivate treiben die Bewegung“, das Gegenteil von „gesunder Trend“. Die Begründung zu
  E36.2 im Code zieht genau diesen falschen Schluss.
- **Betrifft das Handeln der Engine?** Nein, die Funktion ist reine Anzeige. Aber Kaiser
  setzt nach diesen Zeilen seine Limits.

### A2 · „Derivate-Pump“ hängt davon ab, wo die Summierung begonnen hat

`classify_pattern()` erkennt Muster 2 (Derivate-Pump) unter anderem mit
`spot <= fut / 3`. Beide Werte kommen aus `_slope()`: **Veränderung im Fenster geteilt durch
den Stand der kumulierten Reihe am Fensteranfang.** Dieser Stand ist willkürlich. Er hängt
nur davon ab, ab welcher Kerze die Summe gebildet wurde:
- **live** ab der ersten der 1.300 geladenen Kerzen (Spot) bzw. ab 90 Tagen (Futures),
- **im Backtest** ab dem Anfang der Datenreihe.

Nachgestellt mit identischer Marktlage (Kurs +3 %, Spot +200 Mio $, Futures +2.000 BTC,
OI +4 %, Funding steigt leicht). Geändert wurde **nur** der Startwert der Summen:

| Spot-CVD-Summe am Start | Futures-CVD-Summe am Start | erkanntes Muster |
|---:|---:|---|
| −5 Mrd $ | −20.000 BTC | GESUNDER_TREND |
| −0,5 Mrd $ | −20.000 BTC | GESUNDER_TREND |
| **−50 Mrd $** | −20.000 BTC | **DERIVATE_PUMP** |
| −5 Mrd $ | **+1.000 BTC** | **DERIVATE_PUMP** |

Dieselbe Lage ergibt also Furkans bestes Muster oder sein Warnmuster. (Skript:
`demo_slope.py` im Anhang dieses Berichts.)

**Warum das live zählt:** Muster 2 ist heute schon ein **Filter** und ein **Ausstieg**:
- Kein neuer Einstieg bei Derivate-Pump (`evaluate`, Einstiegszweig).
- Restverkauf bei Derivate-Pump nach dem ersten Ziel. Im Lauf vom 23.09. waren das **5 von
  10 Restverkäufen**.
- **30 Telegram-Warnungen** „Derivate-Pump“ in acht Monaten.
- Die Ampel zählt Muster 2 als Gegenargument.

Und weil live anders summiert wird als im Backtest, kann die Live-Engine an einer Kerze
„Derivate-Pump“ sehen, an der der Backtest „gesunder Trend“ gesehen hat. Das ist genau die
Fehlerklasse, die das Projekt mit der Regel „jeder Lauf ist ein neuer Prozess“ ausschließen
will.

*Die Vorzeichen-Prüfungen (Spot steigt / fällt) in Muster 1, 4 und 5 sind davon
**nicht** betroffen. Nur der Größenvergleich in Muster 2 ist es.*

### A3 · Open Interest in Dollar: Schon die Kursbewegung erfüllt die OI-Schwellen

*Open Interest (OI) = Zahl der offenen Terminkontrakte. Furkan: „Geht der Preis hoch und
Open Interest steigt: neues Geld kommt rein“ (Transkript 9:31).*

Coinalyze liefert das OI mit `convert_to_usd=true`, also **Kontrakte × Kurs**.
Rohdaten: 8,79 Mrd $ ≈ 108.000 BTC × 81.275. Steigt der Kurs um 3 %, steigt das Dollar-OI
um 3 %, auch wenn **niemand** eine neue Position eröffnet hat. Die Schwellen der Muster
liegen genau in dieser Größe:

| Muster | OI-Bedingung (in Dollar) | was sie dadurch wirklich verlangt |
|---|---|---|
| 4 Kapitulation | Kurs ≤ −4 %, OI ≤ −5 % | bei −5 % Kurs **keine einzige** geschlossene Position |
| 2 Derivate-Pump | Kurs > 0, OI ≥ +3 % | bei +3 % Kurs **kein einziger** neuer Kontrakt |
| 3 Short-Covering | Kurs ≥ +2 %, OI ≤ −2 % | Kontrakte müssen um **rund 4 %** fallen (strenger als gedacht) |
| 5 Abverkauf mit neuen Shorts | Kurs ≤ −2 %, OI ≥ −1 % | Kontrakte müssen **steigen** (strenger als gedacht) |

Nachgestellt, die Zahl der Kontrakte bleibt die ganze Zeit **gleich**:
- Kurs −5 %, Spot dreht am Ende nach oben → **CAPITULATION_RESET** („OI-Wipeout“).
- Kurs +3,5 %, Spot kaum, Futures steigt, Funding steigt leicht → **DERIVATE_PUMP**
  („neues Geld“).

(Skript: `demo_oi_usd.py`.) Die Engine erkennt Muster 2 und 4 also zu einem großen Teil am
**Kurs** und Muster 3 und 5 seltener, als sie sollte.

*Einordnung:* Furkan stellt Velo auch auf Dollar ein (Transkript 22:31). Er beurteilt aber
mit dem Auge große Bewegungen („komplett ein Wipeout“). Die Engine legt feste 3-bis-5-%-
Schwellen über zwei Tage, und in dieser Spanne ist der Kurseffekt genauso groß wie die
Schwelle selbst.

### A4 · Der Test „mehr Historie ändert nichts“ prüft den betroffenen Zweig nicht

`test_mehr_historie_aendert_die_signale_nicht` (`test_strategy_core.py`) sollte absichern,
dass ein größeres Ladefenster kein Signal verändert. Er schneidet aber **dieselbe
vorgerechnete** CVD-Liste nur verschieden weit aus. Live beginnt die Summe bei jedem
Ladefenster neu bei null. Außerdem wächst das OI im Test nur um 0,6 % je zwei Tage und das
Funding ist konstant, **der Derivate-Pump-Zweig wird also nie erreicht.** Das verletzt
Regel 2 (Vorprobe: erst nachweisen, dass das Szenario den Zweig erreicht). A2 konnte er
deshalb nicht finden.

---

## Teil B — Richtig verstanden? Abgleich mit den Videos

| # | Furkan (Quelle) | Engine | Urteil |
|---|---|---|---|
| 1 | Erst Makro-Bias (US-Aktien, Anleihen, Renditen), dann long oder short (Tutorial 16:01) | nur Long, kein Makro-Bias | **richtig begründet.** Ein Tages-EMA ist kein Ersatz (E33 gemessen) |
| 2 | Golden Pocket 61,8–65 %, erste Order am 50-%-Level, nie all in (17:00–18:00) | 0,5 / 0,618–0,65 / 0,786, Tranchen 25/50/25 | **richtig** |
| 3 | Extension „vom Tief zum Hoch zum weiteren Tief“, Ziel 1:1, dann 1,618 (18:00–19:00) | `ext_target` vom Korrekturtief aus | **richtig** (Dreipunkt-Extension) |
| 4 | Liquidationszonen = wo **offene** Positionen liegen, „größter Schmerz“ (16:31, Hyblock) | `liq_levels`: wo **schon** liquidiert wurde | **Stellvertreter, nicht dasselbe.** An einer gelaufenen Kaskade ist die Liquidität schon weg. Bekannt seit 20.09., als Datenfrage offen |
| 5 | Vier Muster, Aggregat über Binance, Coinbase, Bybit, OKX | Muster-Logik sinngemäß übernommen, Daten von einer Börse | **Logik richtig, Messung fehlerhaft** (A2, A3). Aggregation: E37 gemessen |
| 6 | Zwei Fib-Raster gleichzeitig: großes Aufwärts-Bein für Käufe, kleines Abwärts-Bein als Widerstand (Standbild 02.08. 16:12: 57.802 → 66.940 und 66.940 → 63.709) | nimmt das **jüngste** Bein, auch wenn es abwärts zeigt und nicht handelbar ist | **richtig erkannt** (E19, `bein_richtung`), **nie gegen die heutige Live-Zeile gemessen** (siehe C) |
| 7 | Break-even: „Gewinne schon realisiert … Stop über dem AK“, dann bei Aufstockung „Stop auf das neue Entry“ (27.07. 17:01–18:27; 02.08. 16:11–16:25; 13.09. 17:34–17:57) | `be_im_plus`: Stop auf Einstand, sobald eine **frische** Position einmal im Plus war | **Lesefehler:** Die Vorbedingung „Teilgewinne schon realisiert“ fehlt. Furkans Regel entspricht `trail_stop` (live). Das Urteil „Furkans Regel kostet 19,5 Punkte“ ist damit gegenstandslos |
| 8 | Nach der Aufstockung einer Position mit Gewinnen: „mein Stop wird auf jeden Fall wieder drüber kommen“ (13.09.) | Nach einem Neustart aus dem Rest fällt der Engine-Stop auf die Invalidierung des **neuen** Beins zurück (`trail_stop` greift erst wieder nach dem nächsten Teilgewinn) | **Abweichung, bewusst so:** Kaiser hat E28 am 28.08. zurückgenommen („werde ich ggf. selber tun“). Nur zur Kenntnis |
| 9 | Stops auslösen lassen, „runter spiken … und dann wieder hochmarschieren“ (02.08. 16:50) | E41 Rückeroberung | **gestützt** durch dieses Zitat |
| 10 | Gewinne „unter diesem Hoch“, an der Short-Liquidationszone darüber (27.07. 19:01) | `high_exit: on` | **richtig.** Kleine Unschärfe: verkauft wird zum Kerzenschluss, nicht zum Limitpreis knapp unter dem Hoch |
| 11 | Zonen sind Wartepositionen, er kauft nicht automatisch, „in Echtzeit schauen, warum fallen wir“ (13.09. 16:59) | Engine kauft bei Berührung | **richtig erkannt** (E32.3), strukturell nicht abbildbar |
| 12 | „Nie all out“ (18:00), hält seit Juli **eine** Position | Restverkauf bei Gegen-Muster (Muster 2 oder 3) | **Widerspruch zu „nie all out“**, bekannt (E21). Der Auslöser hängt jetzt an A2/A3 |
| 13 | Funding: „neutral bis leicht“ = sauber, negativ oft gut (11:00–11:31) | Kraken-Funding × 8, Schwelle 0,0001 | **in Ordnung.** Die „Faktor 69“ im Bericht E37 sind im Kern eine **Einheit**: Coinalyze liefert Prozent (0,01 = 0,01 %), Kraken einen Bruch. Der echte Niveauunterschied ist klein (Median 3,8e-5 gegen 2,6e-5 als Bruch) |

---

## Teil C — Fair gemessen? Jeder ausgeschaltete Schalter

*„Genau ein Unterschied“ heißt: Die Messzeile unterscheidet sich von der **heutigen**
Live-Zeile (seit 21.09.2026) nur in diesem einen Schalter. Nach Projektregel ist ein
Mechanismus, der gegen eine ältere Live-Einstellung verworfen wurde, wieder offen.*

| Schalter | Furkan-Bezug richtig? | gebaut wie beschrieben? | genau 1 Unterschied zu heute? | Urteil |
|---|---|---|---|---|
| **`bein_richtung: bias`** | **ja** (Standbild 02.08.) | ja | **nein.** Basis vom 27.08. Dort +32,2 % gegen +25,4 % (+6,8 Punkte), beste Zeile im Gitter. **Aber:** in den Hälften H1 nur +0,5 (Rauschen), H2 +5,2. Im Lauf vom 27.08. waren es insgesamt nur +1,2, ohne Mindest-Bein sogar −2,9 | **neu messen, Priorität 1.** Hält die Engine länger investiert, passt also zur Kern-Diagnose. Ob es trägt, entscheidet erst die saubere Zeile |
| `rest_halten` | ja („nie all out“) | ja | nein (Basis ohne Zonen-Nachziehen und Rückeroberung) | neu messen, **nach** A2/A3 (der Restverkauf hängt an Muster 2/3) |
| `strict_confirm` | ja (Konfluenz-Prinzip) | ja | nein. Gemessen 07/2026 **ohne echte OI-Daten**, im Plan steht „für Retest aufheben“. Der Retest ist nie passiert | neu messen, nach A2/A3 |
| `confirm_t1` | indirekt | ja | nein (bekannt) | neu messen |
| `cooldown_h` | nein (eigene Idee) | ja | nein (bekannt) | neu messen |
| `be_im_plus` | **nein** (Vorbedingung fehlt, B7) | ja | nein | aus lassen, **Urteil im Wissens-Layer korrigieren** |
| `widerstand_exit` | ja (zweites Raster, 03.08. 3:00) | ja | nein (Basis 27.08.) | niedrige Priorität (macht die Engine schneller draußen) |
| `freeze_targets` | Mechanik | ja | nein | niedrige Priorität |
| `liq_exit` (spike/zone/both) | nur Stellvertreter (B4) | ja | nein (Basis 07/2026) | aus lassen, bis offene Cluster messbar sind |
| `liq_entry: filter` | Stellvertreter | ja | nein | aus lassen |
| `high_exit: weak` | ja | ja | nein | niedrige Priorität |
| `conditional_stop` | Kaisers Zitat | ja | nein (älteste Basis) | aus lassen, E41 deckt den Gedanken ab |
| `release_stale_rest` | – | ja | nein | aus lassen, durch `trail_stop` + Neustart ersetzt |
| `bein_wahl: groesstes` | ja (13.09.-Lehre) | ja | nein, aber −17 Punkte | aus lassen, der Abstand ist zu groß für Rauschen |
| Long+Short (`bias_short`) | ja (braucht Makro-Bias) | ja | nein (älteste Grundzeile) | niedrige Priorität, erst mit Makro-Bias sinnvoll |
| `confluence` (4h+1D) | ja (STRATEGIE 4.1) | ja | nein (07/2026) | niedrige Priorität, `zonen_1d` spricht dagegen |
| `tp_ladder` (live!) | **nicht** von Furkan (0,8/0,9 aus Kaisers Verkaufsdaten abgeleitet) | ja | nein (E8.2, alte Basis) | Gegenprobe „ohne Leiter“ wäre sauber |
| `block_unhealthy`, `muster5_*` | ja | ja | **ja** | Urteil hält vorerst, Muster 5 hängt aber an A3: nach der Korrektur einmal wiederholen |
| `trend_filter`, `zonen_1d`, `ampel_filter` | ja | ja | **ja** | **Urteil hält** (deutlich, nicht von A2/A3 betroffen) |
| `stop_puffer_pct`, `stop_auf_docht` | ja | ja | ja, gegen die Live-Zeile bis 21.09. (vor E41) | Urteil hält, es sind Alternativen zu derselben Stop-Regel |
| E37 Aggregation | ja | ja | ja | Urteil hält nach der Rauschgrenze. **Aber:** Der Satz im Wissens-Layer „keine einzige Variante in beiden Hälften besser“ ist für den Lauf vom 23.09. falsch. Dort ist „OI aggregiert“ in beiden Hälften besser (H1 +0,6, H2 +1,0), in H1 aber unter 1 Punkt, also Rauschen |

---

## Teil D — Was das für die tragenden Aussagen heißt

- **„Zwölf gemessene Filter, zwölf schlechter“** bleibt für Trend, 1D-Ebene und Ampel
  unberührt, die Abstände sind groß und hängen nicht an den Mustern. Die
  **Order-Flow**-Messungen (Warnlicht, Muster 5 als Bremse oder Treibstoff) liefen dagegen
  mit einer Mustererkennung, die zwei Messfehler hat. Dort ist das Urteil **vorläufig**,
  nicht widerlegt.
- **Die Live-Engine benutzt Muster 2 schon heute als Filter und als Ausstieg.** A2 und A3
  betreffen also nicht nur verworfene Schalter, sondern das laufende Handelsverhalten.
- **Die Rendite-Zahlen im Bericht sind nicht falsch gerechnet.** Sie beruhen aber auf einer
  Mustererkennung, die nach der Korrektur an manchen Kerzen anders entscheidet. In welche
  Richtung das die Rendite bewegt, ist offen. Das zeigt erst die Messung.
- **E41 (offener Streitpunkt) ist nicht direkt betroffen:** Die Stop-Regel hängt nicht an
  den Mustern, und beide Vergleichszeilen laufen mit derselben Mustererkennung.

---

## Teil E — Vorschlag, nach Nutzwert (nichts davon ist gebaut)

| # | Schritt | Art | Aufwand |
|---|---|---|---|
| 1 | **A1 beheben:** Futures-Delta je Kerze mit dem Schlusskurs in Dollar umrechnen, bevor es angezeigt wird. Test + Sabotage | reine Anzeige, ändert kein Signal | klein |
| 2 | **Gitterzeile „LIVE-heute +Bein in Handelsrichtung“**, genau ein Unterschied. Kein neuer Code, nur eine Zeile in `backtest.py` | Messung | sehr klein |
| 3 | **A2 als Schalter** (z. B. `muster_cvd: "alt"` / `"usd"`): Futures-Delta in Dollar, Muster 2 vergleicht Dollar-Beträge im Fenster statt Anteile an einer willkürlichen Summe. Gitterzeile | Schalter, Default alt | mittel |
| 4 | **A3 als Schalter** (z. B. `muster_oi: "usd"` / `"btc"`): OI durch den Kurs teilen, also Kontrakte statt Dollar. Gitterzeile | Schalter, Default usd | klein |
| 5 | **A4 reparieren:** Test summiert ab Fensteranfang neu und weist vorab nach, dass der Derivate-Pump-Zweig erreicht wird | Test | klein |
| 6 | **Nachmessung mit genau einem Unterschied:** `rest_halten`, `strict_confirm`, `confirm_t1`, `cooldown_h` (nach 3/4), danach `block_unhealthy`/Muster 5 einmal wiederholen | Messung | klein (Laufzeit) |
| 7 | **Wissens-Layer berichtigen:** `be_im_plus`-Urteil, E37-Satz, „Faktor 69“ = Prozent-Einheit | Text | klein |

**Entscheidungsregel, vorab festgelegt (Vorschlag, gilt für 2, 3, 4 und 6):** Ein Schalter
geht nur live, wenn er gegen die Live-Zeile in **beiden** Fensterhälften um **mindestens
1 Punkt** besser ist **und** der Rückgang **nicht mehr als 1 Punkt** tiefer liegt. Dazu eine
Ausschalt-Regel, die der Bericht selbst prüft (Vorbild E41). Liegt der Unterschied unter
1 Punkt, bleibt es beim alten Stand. Bei 3 und 4 zusätzlich: Liefern die Korrekturen **keine**
bessere Rendite, werden sie trotzdem als Anzeige-Korrektur übernommen (die Musterzeile im
Lage-Abruf soll stimmen). Der Handels-Schalter bleibt dann aus.

**Bewusst NICHT vorgeschlagen:** ein dreizehnter Filter; jede Nachjustierung der
Muster-Schwellen (3 %, 4 %, 5 %) über die Korrektur hinaus (das wäre Anpassen an die
Vergangenheit); ein Wechsel des Stop-Verhaltens nach dem Neustart (Kaisers Entscheidung
E28).

---

## Anhang: die beiden Nachstell-Skripte

Beide laufen mit der Standardbibliothek gegen das unveränderte `strategy_core.py`
(Aufruf aus `signal-app\engine`: `python3 demo_slope.py`).

**`demo_slope.py`**

```python
# Demonstration: DERIVATE_PUMP haengt vom (willkuerlichen) Startwert der kumulierten CVD-Reihen ab.
from strategy_core import Candle, FlowPoint, classify_pattern

def szenario(spot_start, fut_start):
    cs, fl = [], []
    for i in range(12):
        p = 60000 * (1 + 0.03 * i / 11)
        cs.append(Candle(i, p, p * 1.002, p * 0.998, p))
        fl.append(FlowPoint(i, spot_start + 200e6 * i / 11, fut_start + 2000 * i / 11,
                            10e9 * (1 + 0.04 * i / 11), 0.00002 + 0.000001 * i))
    return classify_pattern(cs, fl).name

for sp, fu in [(-5e9, -20000), (-0.5e9, -20000), (-50e9, -20000), (-5e9, 1000)]:
    print(sp, fu, szenario(sp, fu))
# Ergebnis 26.09.2026: GESUNDER_TREND, GESUNDER_TREND, DERIVATE_PUMP, DERIVATE_PUMP
```

**`demo_oi_usd.py`**

```python
# Demonstration: OI in USD = Kontrakte x Preis. Kontrakte bleiben konstant.
from strategy_core import Candle, FlowPoint, classify_pattern

KONTRAKTE = 100_000.0

def lauf(preis_aenderung, spot_delta, fut_delta, funding, spot_dreht=False):
    cs, fl, sp, fu = [], [], -5e9, -20000.0
    for i in range(12):
        p = 60000 * (1 + preis_aenderung * i / 11)
        cs.append(Candle(i, p, p * 1.002, p * 0.998, p))
        d = spot_delta / 11
        if spot_dreht and i >= 10:
            d = abs(d) * 3
        sp += d if i else 0
        fu += fut_delta / 11 if i else 0
        f = funding[i] if isinstance(funding, list) else funding
        fl.append(FlowPoint(i, sp, fu, KONTRAKTE * p, f))
    return classify_pattern(cs, fl).name

print(lauf(-0.05, -300e6, -3000, 0.00002, spot_dreht=True))            # CAPITULATION_RESET
print(lauf(0.035, 5e6, 3000, [0.00002 + 1e-6 * i for i in range(12)]))  # DERIVATE_PUMP
```
