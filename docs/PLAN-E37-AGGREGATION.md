# E37 — Mehrere Börsen statt einer

Status: BAUPLAN 19.09.2026

## Anlass

Kaiser, 19.09.2026:

> *„Furkan hat alle kostenlosen Tools in diesem einen Video dargestellt. Doch haben
> wir denn die Order flows so noch nie getestet."*

Die Recherche dazu führte zu einem Befund, der größer ist als die Frage war — und zu
Kaisers Vorgabe für das Vorgehen:

> *„Unterteile doch den Ausbau aller 6 Werte aggregiert und erst Auswahl reparieren in
> sinnvolle Etappen, damit sich eben kein stiller Fehler einschleicht."*

## Der Befund: die Engine misst eine Börse, nicht den Markt

Das Kürzel `.A` in den Coinalyze-Symbolen heißt **Binance**, nicht „aggregiert". Der
Kommentar an `SYMBOL` in `coinalyze.py` behauptete seit E9.1 (Juli 2026) das Gegenteil.

Nachgewiesen durch den Probe-Lauf vom 19.09.2026, 17:50 UTC:

- `/exchanges` listet 28 Börsen, darunter `{'name': 'Binance', 'code': 'A'}`.
- 5436 Futures-Märkte benutzen 16 Börsen-Codes. **Keiner davon fehlt in der
  Börsenliste** — es gibt nirgends ein Pseudo-Kürzel für ein Aggregat.
- Der Eintrag zum Symbol der Engine:
  `{"symbol": "BTCUSDT_PERP.A", "exchange": "A", "symbol_on_exchange": "BTCUSDT", ...}`

Damit stammen **alle sechs Werte** von einer einzigen Börse:

| Wert | Quelle heute (nachgeprüft 20.09.) | Börse | im Code behauptet |
|---|---|---|---|
| Spot-CVD | `data-api.binance.vision` | Binance | Binance (korrekt) |
| Futures-CVD | Coinalyze `BTCUSDT_PERP.A` | Binance | „aggregiert über Börsen" ❌ |
| Open Interest | Coinalyze `BTCUSDT_PERP.A` | Binance | „aggregiert über Börsen" ❌ |
| **Funding** | **`futures.kraken.com`, stündlich ×8** | **Kraken** | „aggregiert über Börsen" ❌ |
| Liquidationen | Coinalyze `BTCUSDT_PERP.A` | Binance | „aggregiert über Börsen" ❌ |
| Long-Short | Coinalyze `BTCUSDT_PERP.A` | Binance | „aggregiert über Börsen" ❌ |

**Korrektur 20.09.2026:** Die erste Fassung dieser Tabelle führte das Funding unter
Coinalyze/Binance. Falsch — es kommt von **Kraken** (`fetch_funding_8h()` in
`main.py`). `classify_pattern` vergleicht also Binance-OI und Binance-CVD gegen die
Funding-Rate einer anderen Börse. `coinalyze.funding_by_ts()` existiert, wird
**nirgends aufgerufen** und hat keinen Test: toter Code.

**Welche Werte stammen aus Furkans Orderflow-Seminar?** Fünf, nicht sechs. Das
Long-Short-Verhältnis kommt aus E16 und anderen Videos — im Seminar-Transkript
taucht es nicht auf. Umgekehrt fehlt uns eines, das er dort zeigt: die
**Liquiditäts-Heatmap** (Hyblock, kostenpflichtig — er zahlt selbst dafür und nennt
CoinAnk als freie Alternative). Und beim Funding gibt es einen **zweiten**
Unterschied neben der Börse: Furkan stellt bei Velo „Open Interest gewichtet,
8 Stunden, Durchschnitt" ein; unsere Kraken-Reihe ist weder gewichtet noch ein
Durchschnitt über Börsen.

Furkan aggregiert im Orderflow-Seminar ausdrücklich: *„Wir schauen nicht nur auf eine
Börse."* Spot über Binance, Coinbase, Bybit, OKX; Futures über acht Perp-Märkte.

**Ehrlich und wichtig:** Damit ist NICHT gesagt, dass aggregierte Daten die Engine
besser machen. Das ist zu messen wie alles andere. Gesagt ist nur: Bisher wurde etwas
anderes gemessen, als im Code stand.

## Was die zweite Probe (18:08 UTC) geklärt hat

| Frage | Antwort |
|---|---|
| Liefert Spot `v` (Gesamtvolumen) und `bv` (Taker-Käufe)? | **Ja** → Delta = `2*bv - v` |
| Reichweite der 4h-Historie | **334 Tage**, 2005 Punkte, ab 20.10.2025 |
| Bringt EIN Abruf mehrere Symbolreihen? | **Ja** — 3 angefragt, 3 zurück |
| Alle vier Börsen Furkans? | **Drei.** OKX hat keinen BTC/Dollar-Spotmarkt mit Kauf-/Verkaufsdaten |

**Einheiten (aus den Rohwerten des Laufs abgelesen, Kurs ≈ 81.420 $):**

| Symbol | Börse | `v` letzte 4h-Kerze | Einheit |
|---|---|---|---|
| `BTCUSD.A` | Binance | 1257,5 | BTC |
| `BTCUSDT.C` | Coinbase | **2,2** | BTC |
| `sBTCUSDT.6` | Bybit | 318,4 | BTC |
| `BTCUSDT_PERP.A` | Binance Perp | 8024,4 | BTC |

Alles in **BTC** — die Summe ist also einheitenrein. Aber die Coinbase-Zahl entlarvt
einen Auswahlfehler: **2,2 BTC in vier Stunden sind 0,17 % der Summe.** Coinbases
Hauptmarkt ist `BTC-USD`, nicht `BTC-USDT`. Die jetzige Regel nimmt global USDT vor
USD und greift damit auf Coinbase den falschen Markt ab. Das Aggregat wäre faktisch
„Binance + Bybit".

## Warum das in Etappen muss

Die sechs Werte werden **nicht gleich** zusammengefasst. Genau hier sitzt die Gefahr:

| Wert | Richtige Regel | Was ein stiller Fehler hier anrichtet |
|---|---|---|
| Spot-CVD | Summe der Deltas | Falscher Markt → Aggregat ist eine Börse mit Deko |
| Futures-CVD | Summe der Deltas | Märkte mit anderer Denominierung mitsummiert → Zahl sieht normal aus, ist Unsinn |
| Open Interest | Summe | wie oben |
| Liquidationen | Summe | wie oben |
| **Funding** | **Nach Open Interest gewichtetes Mittel** | Einfacher Durchschnitt gibt einer winzigen Börse dasselbe Gewicht wie Binance |
| **Long-Short** | **Nach Open Interest gewichtetes Mittel** | wie oben |

Zwei Regeln, zwei Fallen — und beide erzeugen Zahlen, die plausibel aussehen. Das ist
derselbe Fehlertyp, der dieses Projekt schon fünfmal beschäftigt hat: etwas meldet
sich grün, ohne stattzufinden. Deshalb bekommt jede Regel ihre eigene Etappe mit
eigener Sabotage-Probe.

## Die Etappen

Jede Etappe lässt das Projekt grün zurück: Tests laufen, Datei ist committbar, und
nach jeder Etappe steht hier der Status.

### E37.1 — Auswahl nach Volumen, Einheiten belegt · Status: FERTIG 19.09.2026

Dritte Probe, ein Lauf, zwei Fragen:

1. **Auswahl reparieren.** Alle BTC/Dollar-Kandidaten je Börse in EINEM Abruf holen
   (funktioniert nachweislich), das Gesamtvolumen über das Fenster summieren und je
   Börse den **größten** Markt nehmen. Erwartung: Coinbase wechselt von `BTCUSDT.C`
   auf `BTCUSD.C`. Das ist zu belegen, nicht zu glauben.
2. **OKX ein zweites Mal prüfen.** Ist dort wirklich kein BTC/Dollar-Spotmarkt mit
   Kauf-/Verkaufsdaten, oder scheitert es an der Filterregel? Die Probe soll alle
   OKX-BTC-Einträge roh mitschreiben, auch die abgelehnten, mit Ablehnungsgrund.
3. **Einheiten je Markt ausweisen**, damit die Summe in E37.2 nicht auf Vertrauen
   beruht.

Ergebnis: eine Symboltabelle in `coinalyze_probe.json`. **Engine und Backtest bleiben
unberührt.**

**Gebaut am 19.09.2026** in `coinalyze.py` (Engine und Backtest unberührt):

- `_ablehnungsgrund()` — sagt, **warum** ein Markt ausscheidet, statt nur Ja/Nein.
  Trägt die OKX-Diagnose.
- `_kandidaten_je_boerse()` — **alle** passenden Märkte je Börse, nicht mehr einer.
- `_abgelehnte_je_boerse()` — die verworfenen BTC-Märkte mit Grund.
- `_groesster_je_boerse()` — entscheidet nach gemessenem `summe_v`. Ein Markt ohne
  lesbare Reihe kann nicht gewinnen; hat eine Börse gar keine, fällt sie ganz weg.
- `_einheit_einschaetzen()` — weist BTC gegen Dollar aus, mit Rechnung.
- `_pruefe_symbole()` — holt in Blöcken zu 6 (die Symbolgrenze von Coinalyze ist nicht
  dokumentiert). Ein gescheiterter Block wird vermerkt, die übrigen laufen weiter.
- `volumenvergleich_je_boerse` in der Ausgabe: Anteil jedes Marktes in Prozent — damit
  der alte Fehlgriff belegt ist und nicht nur behauptet.

18 Sabotagen durchgespielt, 18 gefangen (eine erst nach Nachbesserung: das Szenario
trennte gewählte und verworfene Märkte nicht nach Historienlänge). 246 Tests grün.

#### Ergebnis des Laufs (19.09.2026, 18:42 UTC)

**Gewählt, nach gemessenem Volumen über 334 Tage:**

| Börse | Symbol | an der Börse | Paar | Volumen | Anteil an der Börse |
|---|---|---|---|---|---|
| Binance | `BTCUSD.A` | `BTCUSDT` | BTC/USDT | 6.311.570 BTC | 60,97 % |
| Bybit | `sBTCUSDT.6` | `BTCUSDT` | BTC/USDT | 3.189.878 BTC | 92,58 % |
| Coinbase | `BTCUSD.C` | `BTC-USD` | BTC/USD | 2.818.917 BTC | 98,81 % |

**Die Reparatur war nötig und ist belegt.** Auf Coinbase hätte die alte Regel
`BTCUSDT.C` genommen — der hat **1,19 %** des Coinbase-Volumens. Der richtige Markt
ist 83-mal größer.

**Einheiten bestätigt:** alle drei in BTC. Binance 1432,7 BTC in der letzten
4h-Kerze ≈ 116,8 Mio. $ Umsatz — plausibel. Die Summe ist einheitenrein.

**Historie:** 334 Tage auf allen dreien, ab 20.10.2025. Kein Markt ist der Flaschenhals.

**Mehrfachabruf:** 10 Symbole in zwei Blöcken (6 + 4), alle zehn Reihen kamen zurück.

**OKX: kein Spot bei Coinalyze.** Die Diagnose ist eindeutig, weil sie auch die
Abgelehnten ausweist: Binance 49 abgelehnte BTC-Märkte, Coinbase 22, Bybit 16 — OKX
**null**, weder als Kandidat noch als Ablehnung. In der Spotliste (5953 Einträge)
kommt die Börse nicht vor. In der Futures-Liste dagegen schon (`BTCUSDT_PERP.3`),
also steht OKX ab E37.3 wieder zur Verfügung. Spot bleibt bei drei von vier.

#### Neu aufgetaucht — Entscheidung für E37.2

Das Volumen einer Börse verteilt sich auf **mehrere** Dollar-Märkte:

| Börse | Verteilung |
|---|---|
| Binance | USDT 60,97 % · FDUSD 21,15 % · USDC 17,83 % · USD 0,04 % |
| Bybit | USDT 92,58 % · USDC 7,17 % · USD 0,21 % · USDE 0,03 % |
| Coinbase | USD 98,81 % · USDT 1,19 % |

Nur den größten zu nehmen lässt auf Binance **39 % des Dollar-Flusses** liegen. Ob
das besser oder schlechter ist, wird nicht diskutiert, sondern gemessen: E37.2 bekommt
den Schalter `spot_markt_wahl` mit `"groesster"` (Default) und `"alle_dollar"`, und
E37.5 entscheidet. Begründung für den Default: „größter je Börse" ist am nächsten an
dem, was Velo als Börsen-Aggregat zeigt.

### E37.2 — Aggregiertes Spot-CVD, nur im Backtest · Status: FERTIG 19.09.2026

- Neue Funktion `spot_cvd_aggregiert()` in `coinalyze.py`: Delta je Symbol, dann Summe
  je Zeitstempel. Zeitstempel, die nicht auf allen Börsen vorliegen, werden
  **übersprungen und gezählt** — nicht stillschweigend als 0 behandelt.
- Schalter `spot_quellen` in `backtest.py`, Default `"binance"` (= heutiger Zustand).
- Schalter `spot_markt_wahl`: `"groesster"` (Default) oder `"alle_dollar"` — siehe
  den Befund am Ende von E37.1.
- **Einheiten-Abgleich gegen heute:** Das jetzige Spot-CVD kommt aus Binance-Vision
  und rechnet `2*bv - v` auf das **Quote**-Volumen (USD), das Coinalyze-Delta auf das
  **Basis**-Volumen (BTC). Beide Reihen gehen nur über `_slope()` als relative
  Änderung ein, die Einheit kürzt sich also heraus — aber das muss ein Test festhalten,
  sonst mischt die nächste Änderung die Einheiten doch.
- Zwei Gitterzeilen nach dem Muster von E16: **dieselbe Variante, dieselben Kerzen,
  einziger Unterschied sind die Daten.**
- Tests + Sabotage-Probe. Pflichtsabotagen: eine Börse fällt still weg; Lücken werden
  als 0 gezählt; Summe nimmt `bv` statt `2*bv - v`.

**Gebaut am 19.09.2026** — in `coinalyze.py` und `backtest.py`; `strategy_core.py`
und `main.py` **unberührt**, die Engine handelt unverändert weiter:

- `_hole_reihen_roh()` — der Blockabruf wurde herausgelöst. Probe und Produktion teilen
  sich jetzt dieselbe Mechanik; wären es zwei Wege, könnte die Probe etwas bestätigen,
  was der Produktionsweg anders macht.
- `spot_delta_aggregiert()` — Delta `2*bv - v` je Markt, dann Summe. **Ein Zeitpunkt
  zählt nur, wenn ihn alle gefragten Märkte haben**; unvollständige werden ausgelassen
  und gezählt. Grund: An einem Tag mit einer Coinbase-Lücke sähe eine Teilsumme aus
  wie ein Einbruch des Spot-Flusses um ein Drittel, ohne dass am Markt etwas passiert
  wäre. Der Bericht nennt Gesamtpunkte, vollständige, ausgelassene und Märkte ohne
  Antwort.
- `spot_auswahl()` — liefert **beide** Wahlmöglichkeiten in einem Durchgang. Die
  Marktliste hat 5953 Einträge; sie zweimal zu holen wäre Verschwendung und könnte
  zwischen den Läufen sogar unterschiedlich ausfallen.
- `build_series(..., spot_map=...)` — **ersetzt** die Binance-Vision-Rechnung, statt
  sie zu ergänzen. Sonst zählte Binance doppelt und in zwei Einheiten. Eine übergebene,
  aber leere Karte heißt „keine Daten" und fällt **nicht** still auf Binance zurück —
  sonst bliebe ein Totalausfall der Aggregation unbemerkt, weil beide Vergleichszeilen
  dasselbe rechneten.
- Vergleichsabschnitt im Bericht nach dem Muster von E16: drei Zeilen, dieselbe
  Variante, dieselben Kerzen, derselbe Zeitraum — nur die Herkunft des Spot-CVD ist
  verschieden.

14 Sabotagen durchgespielt, 14 gefangen. 257 Tests grün.

**Einheiten stehen im Bericht**, damit sie niemand später vermischt: die heutige Zeile
rechnet in Dollar (Quote-Volumen der Binance-Kerzen), die aggregierten in BTC
(Basiswert, wie das Futures-CVD). Beide gehen nur über `_slope()` als relative
Änderung ein — summiert werden dürfen sie trotzdem nie.

#### Ergebnis des Messlaufs (19.09.2026, 19:16 UTC)

Fenster 11.01.–19.09.2026, Variante *LIVE-heute +Zonen nachziehen*, 3 Märkte,
2004 vollständige Punkte, 2 ausgelassen.

| Datenlage | Recall | Präz. | Rendite | max. Rückgang | Signale | Rendite/Rückgang |
|---|---|---|---|---|---|---|
| heute (nur Binance) | 56 % | 32 % | **+23,5 %** | −9,4 % | 238 | 2,50 |
| aggregiert, größter Markt je Börse | 56 % | 31 % | +20,9 % | **−8,2 %** | 233 | 2,55 |
| aggregiert, alle Dollar-Märkte | 56 % | 30 % | +21,3 % | **−8,2 %** | 218 | 2,60 |

**Die Daten ändern etwas** — anders als bei E16 (Futures-CVD, „ändert nichts") bewegt
sich die Signalzahl: 238 → 233 → 218. Mehrere Börsen lassen die Muster an anderen
Stellen feuern. Die Aussage „wir sehen nur eine Börse" ist also nicht folgenlos.

**Aber es kostet Rendite und kauft Ruhe:** rund 2,5 Punkte weniger Rendite, rund
1,2 Punkte weniger Rückgang. Das Verhältnis aus beidem bleibt praktisch gleich
(2,50 / 2,55 / 2,60). Kein Grund umzustellen, und kein Beleg, dass Binance allein
schadet. **Für den Spot-Teil ist das ein Unentschieden.**

**Wichtiger Vorbehalt — das Fenster hat sich verschoben.** Der Lauf misst
11.01.–19.09.2026, der vom 13.09. maß 05.01.–13.09.2026. Coinalyze löscht
Intraday-Punkte täglich, das Fenster wandert also mit. Dieselbe Variante steht heute
bei +23,5 %, am 13.09. bei +30,9 % — **das ist das Fenster, nicht die Engine.**
Wer Zahlen aus zwei Läufen vergleicht, muss zuerst die Fensterangabe im Kopf des
Berichts vergleichen.

**Was fehlt:** Die Fensterhalbierung deckt nur die Gitter-Varianten ab, nicht diese
drei Zeilen — sie sind Datenvarianten, keine Parametervarianten. Für sie gibt es
also keine Robustheitsprüfung. Das wiegt hier weniger schwer als sonst, weil die
aggregierten Zeilen *schlechter* abschneiden: Die Gefahr „Beste von 60 sieht besser
aus als sie ist" trifft Gewinner, nicht Verlierer. Trotzdem offen und vor E37.6
nachzuholen.

### E37.3 — Aggregierte Summen: OI, Liquidationen, Futures-CVD · Status: FERTIG 20.09.2026

Dieselbe Regel (Summe) für drei Werte, deshalb eine Etappe.

- Perp-Märkte auswählen wie in E37.1, aber zusätzlich nach
  `oi_lq_vol_denominated_in` gruppieren. **Märkte mit abweichender Denominierung
  werden nicht mitsummiert, sondern gemeldet.**
- Schalter `derivate_quellen`, Default `"binance"`.
- Pflichtsabotage: ein Markt mit anderer Denominierung wird mitsummiert — der Test
  muss das fangen.

**Gebaut am 20.09.2026** — in `coinalyze.py` und `backtest.py`; Engine unberührt.

- `_summiere_vollstaendig()` — die Lücken-Regel aus E37.2 ist **herausgelöst** und gilt
  jetzt für alle vier Werte. Wäre sie viermal geschrieben, könnte sie dreimal richtig
  und einmal falsch sein. Beim Open Interest wiegt sie besonders schwer: Eine
  Teilsumme wäre ein scheinbarer Einbruch um ein Drittel — also genau das Signal, auf
  das Muster 4 (Kapitulation) wartet. **Ein Datenloch würde zum Kaufsignal.**
- `PERP_BOERSEN` = Binance, Bybit, OKX, Hyperliquid. Furkan nennt im Seminar fünf;
  Bitget führt Coinalyze nicht.
- `perp_auswahl()` — größter Perp-Markt je Börse nach gemessenem Volumen, plus die
  Denominierung je Markt, plus die fertige Einheiten-Trennung. Wer die Märkte wählt,
  sagt auch, welche summiert werden dürfen — sonst müsste jeder Aufrufer die Regel
  selbst kennen, und einer macht es falsch.
- `oi_aggregiert()`, `liq_aggregiert()`, `fut_delta_aggregiert()`.
- **Die Einheiten-Falle, per Probe geklärt:** `open-interest-history` und
  `liquidation-history` laufen mit `convert_to_usd=true` und kommen in **USD** →
  über Börsen summierbar. `ohlcv-history` ignoriert das Flag: `v`/`bv` kommen in der
  Denominierung des Marktes. Deshalb wird das Futures-CVD **nur** über Märkte
  derselben Einheit gebildet; der Rest wird gemeldet, nicht stillschweigend
  weggelassen. Welche Gruppe gewinnt, entscheidet das **Volumen** — zwei Zwergbörsen
  dürfen Binance nicht überstimmen.
- Liquidationen: Long und Short laufen durch **dieselbe** Vollständigkeitsprüfung.
  Sonst stünde an einem Zeitpunkt eine volle Long-Summe neben einer halben
  Short-Summe, und die Kaskaden-Erkennung kippt.

16 Sabotagen, 16 gefangen. 266 Tests grün.

#### Ein Fehler im Prüfer selbst (20.09.2026)

Beim ersten Durchgang meldete die Sabotage-Probe **sechs** ungefangene Fälle. Zwei
davon waren echte Testlücken, vier hatten eine andere Ursache — und die ist
lehrreich genug für den Wissens-Layer:

1. **Stale `__pycache__`.** Sabotagen, die die Dateigröße nicht ändern (etwa
   `p.get("s")` → `p.get("l")`), wurden von Python **nicht wirksam**: Die
   Bytecode-Prüfung vergleicht Änderungszeit (sekundengenau) und Größe — bleiben
   beide gleich, lädt Python die alte `.pyc`. Die Sabotage fand nicht statt, der Test
   blieb grün, und die Probe meldete „ungefangen". Behoben: `__pycache__` vor jedem
   Lauf löschen und `PYTHONDONTWRITEBYTECODE=1` setzen.
2. **Zwei Sabotagen waren Selbstläufer** — semantisch identisch mit dem Original
   (`raus = [] or [...]` ist dasselbe wie `raus = [...]`). Eine Sabotage, die nichts
   ändert, kann nichts auslösen.

**Die Richtung des Fehlers ist die gute:** Beides erzeugt falschen ALARM, nicht
falsche Entwarnung. Frühere „OK"-Ergebnisse bleiben gültig. Aber es ist dieselbe
Familie wie alles andere in dieser Woche — diesmal im Werkzeug, das genau danach
suchen soll.

#### Erster Messlauf: der Abschnitt verschwand lautlos (20.09.2026, 09:25 UTC)

Der Backtest lief durch, der Bericht wurde geschrieben — **aber der Derivate-Abschnitt
war nicht darin.** Kein Fehler, keine Zeile, nichts. `oi_agg` war leer, und die
Bedingung `if oi_agg:` ließ den ganzen Abschnitt weg. Warum, stand nirgends: Der Grund
ging als `print()` ins Workflow-Protokoll und damit an niemanden.

**Das ist derselbe Fehlertyp wie alles andere diese Woche**, nur eine Ebene höher: Der
Test, der sich still übersprang, meldete nichts. Der Abschnitt, der still ausfiel,
meldet auch nichts. In beiden Fällen sieht das Ergebnis aus wie Ordnung.

Zwei Konsequenzen, beide gebaut:

1. **`abschnitt_oder_grund()` in `backtest.py`.** Fehlt ein Vergleich, steht er
   trotzdem im Bericht — mit dem Grund, oder mit „unbekannt — es wurde kein Grund
   festgehalten", falls niemand einen festhielt. Gilt jetzt für den Spot- **und** den
   Derivate-Abschnitt. Vier Tests, sechs Sabotagen, alle gefangen.
   Damit ist auch die Lücke geschlossen, die ich selbst benannt hatte: Der Weg durch
   `main()` war nicht prüfbar. Die Entscheidung „Abschnitt oder Grund" ist jetzt eine
   eigene Funktion und wird offline getestet.
2. **Auswahl-Fenster von 365 auf 30 Tage** (`AUSWAHL_TAGE`). Für die Rangfolge genügt
   ein Monat — welcher Markt einer Börse der größte ist, ändert sich nicht dadurch,
   dass man ein Jahr misst. Aber ein Jahr mal zehn Symbole ist zehnmal so viel Last
   auf einer Schnittstelle mit 40 Abrufen je Minute, und das ist der wahrscheinlichste
   Grund für den Ausfall. Ein Test prüft, dass der Parameter auch wirklich ankommt —
   die entsprechende Sabotage blieb beim ersten Versuch ungefangen.

271 Tests grün.

#### Zweiter Messlauf: jetzt sagt der Bericht, woran es lag (20.09.2026, 10:07 UTC)

> **Dieser Vergleich konnte nicht gerechnet werden.** Grund: Abruf lief durch,
> lieferte aber keine OI-Punkte. Gewählte Märkte: ['Binance', 'Bybit', 'OKX',
> 'Hyperliquid']. Bericht: keine einzige Reihe erhalten

Damit ist die Marktauswahl **nicht** das Problem — alle vier Börsen wurden gefunden.
Der Open-Interest-Abruf selbst lieferte nichts. Drei Ursachen gefunden, alle behoben:

1. **Die Diagnose hörte eine Ebene zu früh auf.** Der HTTP-Grund stand im
   Blockprotokoll (`bericht["bloecke"]`), und ich habe nur das Feld `fehler`
   ausgegeben. Eine Diagnose, die den eigentlichen Grund verschluckt, ist keine.
   Jetzt steht das Blockprotokoll mit im Bericht.
2. **Die Taktung war nie aktiv.** Die Pause zwischen den Blöcken hing an
   `if i and not kw` — gedacht als „im Test nicht warten". Im echten Lauf sind aber
   `frm`/`to` gesetzt, `kw` ist also **nicht** leer, und es wurde **nie** gewartet.
   Genau dort, wo das Rate-Limit von 40 Abrufen je Minute greift, lief alles ohne
   Pause. Jetzt explizit über `PAUSE_JE_BLOCK`; eine Pause entfällt nur, wenn ein
   Test-Opener injiziert ist (kein Netz = kein Limit).
3. **Der Mehrfachabruf war für diesen Endpunkt eine Annahme.** Belegt war er nur für
   `ohlcv-history`. Jetzt gibt es einen **Rückfall auf Einzelabrufe**: Was der
   Sammelabruf nicht liefert, wird einzeln nachgefragt und protokolliert.

Am Rückfall hing noch ein Randfall: Die erste Fassung prüfte `len(neu) < len(teil)`.
Kommt eine Reihe doppelt oder eine fremde mit, stimmt die **Anzahl**, das gesuchte
Symbol fehlt trotzdem — und der Rückfall bliebe aus. Maßgeblich ist jetzt, **welche**
Symbole da sind, nicht wie viele Reihen kamen.

275 Tests grün.

#### Dritter Messlauf: die Ursache steht fest (20.09.2026, 10:52 UTC)

> Bloecke: {'symbole': ['BTCUSD_PERP.A', 'BTCUSD.6', 'BTCUSD_PERP.3', 'BTC.H'],
> **'http_error': 429**, 'body': '{"message":"Too Many Requests. See the
> \\"Retry-After\\" header."}'}

**Rate-Limit.** Und die Antwort sagt seit dem ersten Fehlschlag, was zu tun wäre —
wir haben den Hinweis dreimal übersehen und stattdessen den ganzen Vergleich
fallengelassen.

Die Doku nennt 40 Abrufe je Minute, und so viele Anfragen waren es nicht. Offenbar
zählt Coinalyze **je Symbol, nicht je Anfrage**: Bis zu diesem Punkt hatte der Lauf
rund 39 Symbole abgefragt (Spot-Auswahl 10, Spot-Daten 3 + 10, Perp-Auswahl ~12,
dazu vier Einzelabrufe der Engine), und die nächsten vier kippten ihn. Das ist eine
Erklärung, die passt — kein Beweis.

Gebaut:

- **`_mit_wiederholung()`** — bei 429 wird gewartet und wiederholt, mit der Zeit aus
  dem `Retry-After`-Kopf. Ohne Kopf wird die Wartezeit verdoppelt (1,6 / 3,2 / 6,4 s),
  gedeckelt bei 30 s, höchstens vier Versuche. Andere Fehler fliegen sofort durch —
  bei einem 404 hilft Warten nichts.
- **Rückfall greift jetzt auch nach einem HTTP-Fehler.** Vorher sprang er nur an, wenn
  die Antwort unvollständig war; scheiterte der Block, fiel er ersatzlos aus. Ein
  einzelnes Symbol kostet weniger Kontingent und kommt oft durch, wo vier scheitern.

280 Tests grün.

**Zwei Lücken, die die Sabotage-Probe dabei aufdeckte** — beide von derselben Sorte
wie der `tage`-Parameter: Die Wiederholung war fehlerfrei gebaut und **nirgends
verdrahtet** geprüft. Ein Test kann eine Funktion absichern und trotzdem nicht merken,
dass sie nie aufgerufen wird. Dafür gibt es jetzt einen Test, der den **Weg** durch
`_hole_reihen_roh` geht statt die Funktion allein.

**Muster, das sich durch diese Etappe zieht:** Punkt 2 ist wieder eine Prüfung, die
grün meldet ohne stattzufinden — diesmal keine Testprüfung, sondern eine Wartezeit.
Sie stand im Code, war lesbar, sah richtig aus, und war unter den echten Bedingungen
immer abgeschaltet. Dieselbe Familie wie der Test, der sich still übersprang, und wie
das `__pycache__`-Problem im Sabotage-Prüfer.

#### Vierter Messlauf: die Zahlen (20.09.2026, 11:31 UTC)

Perp-Märkte: Binance `BTCUSD_PERP.A`, Bybit `BTCUSD.6`, OKX `BTCUSD_PERP.3`,
Hyperliquid `BTC.H`. OI 1502 Punkte, Liquidationen 1469, Futures-CVD 2001.
**Hyperliquid wurde beim Futures-CVD ausgeschlossen** — andere Denominierung. Die
Einheiten-Trennung hat also im Echtbetrieb gegriffen, nicht nur im Test.

| Datenlage | Recall | Präz. | Rendite | max. Rückgang | Signale |
|---|---|---|---|---|---|
| heute (nur Binance) | 56 % | 32 % | +23,5 % | −9,4 % | 238 |
| +OI aggregiert | 56 % | 32 % | **+24,6 %** | −9,4 % | 230 |
| +OI +Liquidationen | 61 % | 33 % | +23,3 % | −9,4 % | 228 |
| +alle drei | 61 % | **35 %** | +23,2 % | −9,4 % | 217 |

**Die Rendite ist flach.** +23,5 / +24,6 / +23,3 / +23,2 — das ist Rauschen, kein
Effekt. Der maximale Rückgang ändert sich überhaupt nicht (−9,4 % in allen vier
Zeilen).

**Recall und Präzision steigen dagegen deutlich:** 56 → 61 % Recall, 32 → 35 %
Präzision, bei **21 Signalen weniger**. Mit aggregierten Daten trifft die Engine
Furkans Termine besser und feuert seltener daneben.

**Und genau hier gilt die Projektregel: Recall ≠ Gewinn.** Näher an Furkan ist kein
Ergebnis. Die Engine wird ähnlicher, nicht profitabler. Was die bessere Treffer-Quote
in einem echten Konto wert wäre — weniger Orders, weniger Gebühren, weniger Schlupf —
ist nicht gemessen und bleibt Vermutung.

**Fehlende Absicherung, wie beim Spot-Teil:** Die Fensterhalbierung deckt nur die
Gitter-Varianten ab, nicht diese vier Zeilen. Die +1,1 Punkte der OI-Zeile sind damit
nicht robustheitsgeprüft und bei dieser Streuung ohnehin nicht belastbar.

#### Zwischenstand zur Ausgangsfrage

Kaisers Frage war: *„Was sieht Furkan, was wir nicht sehen?"* Auf die Datenseite
bezogen ist sie jetzt beantwortet:

| Teil | gemessen | Ergebnis |
|---|---|---|
| Spot-CVD (E37.2) | ja | Rendite −2,5 Punkte, Rückgang −1,2 Punkte → Unentschieden |
| OI, Liquidationen, Futures-CVD (E37.3) | ja | Rendite flach, Recall +5 / Präzision +3 Punkte |

**Aggregation ist nicht der Unterschied.** Der Befund „wir messen eine Börse, nicht
den Markt" war sachlich richtig und ist für die Rendite folgenlos — dieselbe Antwort
wie bei E16 (echtes Futures-CVD), nur diesmal mit sichtbarer Wirkung auf die
Trefferquote statt gar keiner.

### E37.4 — Gewichtete Mittel: Funding und Long-Short · Status: FERTIG 20.09.2026

- **Zuerst der Quellenwechsel, dann die Gewichtung.** Das Funding kommt heute von
  Kraken und geht damit als einziger Wert gegen eine andere Börse als alle übrigen.
  Der erste Schritt ist deshalb nicht Aggregation, sondern: dieselbe Größe einmal von
  Coinalyze holen (`funding_by_ts()` liegt ungenutzt bereit) und gegen die
  Kraken-Reihe halten. Erst wenn klar ist, wie weit die beiden auseinanderlaufen,
  lohnt der gewichtete Durchschnitt.
- Gewichtung nach Open Interest je Börse und Zeitpunkt (so stellt Furkan es bei Velo
  ein: „Open Interest gewichtet, 8 Stunden, Durchschnitt").
- Pflichtsabotagen: einfacher Durchschnitt statt gewichtet; Gewichte nicht normiert;
  Gewicht eines Marktes ohne OI-Daten stillschweigend 0 statt Ausschluss.
- Diese Etappe ist die heikelste. Sie kommt bewusst zuletzt vor der Messung.

**Gebaut am 20.09.2026** — in `coinalyze.py` und `backtest.py`; Engine unberührt.

- `gewichtetes_mittel()` — nach Open Interest je Zeitpunkt, **normiert**. Ohne
  Normierung käme statt eines Mittels eine mit dem Open Interest skalierte Zahl
  heraus, die je nach Marktphase um Größenordnungen schwankt.
- `funding_aggregiert()`, `long_short_aggregiert()` — beide über dasselbe Mittel.
- `oi_je_symbol()` — das Open Interest wird **einmal** geholt und doppelt genutzt:
  als Summe (E37.3) und als Gewicht (E37.4). Ein zweiter Abruf derselben Daten hat
  am selben Tag das Rate-Limit gesprengt.
- `skalen_vergleich()` — der erste Schritt laut Plan, vor jeder Gewichtung.

**Warum kein Summieren:** Eine Funding-Rate ist ein Preis, keine Menge. Zwei Börsen
mit 0,01 % und 0,03 % haben zusammen nicht 0,04 %. Dasselbe beim Long-Anteil —
summiert käme etwas über 100 % heraus.

**Die Falle, an der die Sabotage ansetzt:** Ein *einfacher* Durchschnitt gibt einer
Zwergbörse dasselbe Gewicht wie Binance. Im Test hält „GROSS" 90 % des Open Interest:
einfacher Durchschnitt 0,055, richtig gewichtet 0,019 — Faktor drei, und **beide
Zahlen sehen plausibel aus**.

**Die Skalenfrage steht vor dem Austausch**, nicht danach. Das Funding kommt von
Kraken (`relativeFundingRate * 8`), die aggregierte Reihe von Coinalyze. In
`classify_pattern` ist das Vorzeichen skalenunabhängig — die Schwelle
`funding_hot = 0.0001` aber nicht. Der Bericht weist deshalb Median-Beträge beider
Reihen, den Faktor und den Anteil gleicher Vorzeichen aus, und warnt ausdrücklich,
wenn der Faktor über 2 oder unter 0,5 liegt.

12 Sabotagen, 12 gefangen (eine erst nach Nachbesserung: kein Szenario hatte ein
Symbol, das *überhaupt keine* Gewichtsreihe liefert). 289 Tests grün.

#### Messlauf (20.09.2026, 13:54 UTC) — und warum er die Frage NICHT beantwortet

| Datenlage | Recall | Präz. | Rendite | max. Rückgang | Signale |
|---|---|---|---|---|---|
| heute (Kraken-Funding, Binance-Long-Short) | 56 % | 32 % | +23,5 % | −9,4 % | 238 |
| +Funding aggregiert (rohe Skala) | 56 % | 30 % | +19,0 % | −11,8 % | 260 |
| +Funding +Long-Short aggregiert | 56 % | 30 % | +19,0 % | −11,8 % | 260 |

Sieht nach einem klaren Nein aus: 4,5 Punkte weniger Rendite, 2,4 Punkte mehr
Rückgang, 22 Signale mehr. **Ist es aber nicht — die Zeile misst etwas anderes.**

Der Skalenvergleich, den der Plan vorgeschrieben hatte, liefert die Erklärung:

> Median-Betrag Kraken **3,805e-05**, Coinalyze **2,613e-03** — Faktor 0,0146.
> Gleiches Vorzeichen in **71 %** der Fälle.

Die Coinalyze-Reihe ist rund **69-mal so groß**. Die Schwelle `funding_hot = 0.0001`
ist damit bei Kraken das 2,6-Fache des Medians — eine hohe Hürde — und bei Coinalyze
ein Sechsundzwanzigstel davon, also **fast immer überschritten**. Muster 2
(Derivate-Pump) feuert dadurch viel häufiger; genau das zeigen die 22 zusätzlichen
Signale. **Gemessen wurde die verschobene Schwelle, nicht die Aggregation.**

Der Plan hat den Fall vorhergesehen („zuerst der Quellenwechsel, dann die
Gewichtung"), und die Warnung im Bericht ist auch erschienen — aber die Vergleichszeile
lief trotzdem ungewandelt. Nachgebessert:

- **Eine vierte Zeile**, die die aggregierte Reihe mit dem *gemessenen* Faktor auf die
  heutige Größenordnung normiert. Erst sie hält die Skala fest und zeigt die Wirkung
  der Aggregation allein.
- **Die Warnung war unlesbar:** `{_f:.1f}` machte aus Faktor 0,0146 die Anzeige
  „Faktor 0.0". Eine Warnung, die ihre eigene Zahl unkenntlich macht.

#### Der ernstere Punkt: 71 % Vorzeichen-Übereinstimmung

Zwei Funding-Reihen auf denselben Markt sollten fast immer in dieselbe Richtung
zeigen. 71 % heißt: **In fast jedem dritten Zeitpunkt widersprechen sie sich.**

Dann ist es nicht dieselbe Größe, sondern eine andere — und dagegen hilft kein
Umrechnungsfaktor. Mögliche Ursachen, keine davon geprüft: Kraken liefert stündlich
und wird mit 8 multipliziert, Coinalyze liefert je 4h-Intervall; Kraken ist ein
einzelner Markt, die Coinalyze-Reihe ein Mittel über vier; oder die Felder bedeuten
schlicht Verschiedenes.

**Konsequenz für E37.6:** Selbst wenn die normierte Zeile gut aussieht, darf das
Funding nicht umgestellt werden, solange diese 71 % nicht erklärt sind. Ein
Quellentausch wäre sonst ein Austausch der Bedeutung, nicht der Genauigkeit.

Nebenbei: **511 von 2009 Zeitpunkten (25 %) fielen weg**, weil nicht alle vier Börsen
dort sowohl einen Wert als auch ein Gewicht hatten. Beim Open Interest waren es
deutlich weniger. Auch das gehört vor eine Umstellung geklärt.

#### Nachgemessen mit normierter Skala (20.09.2026, 14:21 UTC)

| Datenlage | Recall | Präz. | Rendite | max. Rückgang | Signale |
|---|---|---|---|---|---|
| heute (Kraken-Funding, Binance-Long-Short) | 56 % | 32 % | **+23,5 %** | −9,4 % | 238 |
| +Funding aggregiert (rohe Skala) | 56 % | 30 % | +19,0 % | −11,8 % | 260 |
| +Funding aggregiert, auf heutige Skala normiert | 56 % | 30 % | **+17,4 %** | −11,8 % | 241 |
| +Funding normiert +Long-Short aggregiert | 56 % | 30 % | +17,4 % | −11,8 % | 241 |

**Die Normierung hat die Zeile nicht gerettet — sie hat sie verschlechtert.**
+17,4 % statt +23,5 %: **6,1 Punkte weniger Rendite, 2,4 Punkte mehr Rückgang**,
Präzision von 32 auf 30 %.

Dass die Signalzahl mit Normierung wieder nahe am heutigen Stand liegt (241 gegen
238), zeigt, dass die Normierung funktioniert hat: Die Schwelle `funding_hot` greift
wieder wie vorher. Was bleibt, ist die Wirkung der aggregierten Reihe selbst — und
die ist **deutlich negativ**.

**Damit ist E37.4 beantwortet: Nein.** Und die Erklärung liegt bei den 71 %
Vorzeichen-Übereinstimmung: Es ist nicht dieselbe Größe. Eine andere Größe in
`funding_now > 0` einzusetzen dreht die Musterbedingung in fast jedem dritten
Zeitpunkt — kein Wunder, dass das kostet.

Das ist zugleich das klarste Ergebnis der ganzen E37-Reihe. Alle anderen Zeilen waren
Unentschieden oder Rauschen; diese hier ist ein eindeutiges Nein.

### E37.5 — Messen · Status: FERTIG 20.09.2026

Volles Gitter, jede Stufe einzeln und alle zusammen, plus die Fensterhalbierung
(Robustheitsprüfung). Vergleichsbasis ist die heutige Live-Zeile mit genau einem
Unterschied — den Daten.

Zusätzlich die Frage, die sich nur hier beantworten lässt: **Verschiebt sich das
Messfenster?** Spot reicht 334 Tage zurück, das Open Interest bestimmt heute den
Start. Ob das Fenster wächst oder schrumpft, entscheidet über die Vergleichbarkeit
mit allen früheren Messungen.

**Gebaut am 20.09.2026:**

- **Eine Quelle der Wahrheit für alle Datenvarianten.** Bis hierher baute jeder
  Vergleichsabschnitt seine Reihen selbst. Für die Halbierung müssen es garantiert
  **dieselben** Reihen sein — sonst misst die Robustheitsprüfung etwas anderes als
  die Vollfenster-Tabelle, und niemand merkt es. Alle Reihen entstehen jetzt in
  `varianten`, alle drei Abschnitte bedienen sich daraus.
- **`besser_in_beiden_haelften()`** — die einzige Aussage, die aus einer Halbierung
  wirklich folgt. Aus `main()` herausgelöst und geprüft: Gleichstand zählt nicht als
  Vorsprung, eine Hälfte genügt nicht, und ohne Vergleichsbasis wird gar nichts
  behauptet.
- **Neuer Abschnitt „Robustheitsprüfung der Datenvarianten"** — die Datenzeilen aus
  E37.2/3/4 standen bisher **ohne jede** Robustheitsprüfung im Bericht, obwohl der
  Abschnitt direkt darunter genau davor warnt.
- Zusätzlich die Zeile **„ALLES aggregiert"**: Spot, OI, Liquidationen, Futures-CVD,
  normiertes Funding und Long-Short zusammen.

6 Sabotagen, 6 gefangen. 293 Tests grün.

#### Ergebnis (20.09.2026, 15:18 UTC) — Hälfte 1 bis 18.05., Hälfte 2 danach

| Datenvariante | Rendite H1 | Platz H1 | Rendite H2 | Platz H2 |
|---|---|---|---|---|
| **heute (Binance/Kraken)** | **+18,7 %** | **1.** | +4,0 % | 7. |
| Spot-CVD aggregiert | +14,3 % | 6. | **+5,8 %** | **1.** |
| Spot-CVD, alle Dollar-Märkte | +14,4 % | 5. | +5,6 % | 2. |
| OI aggregiert | +18,7 % | 2. | +5,0 % | 3. |
| OI +Liquidationen | +17,7 % | 3. | +4,7 % | 5. |
| OI +Liq +Futures-CVD | +17,6 % | 4. | +4,8 % | 4. |
| Funding normiert | +13,5 % | 7. | +3,4 % | 8. |
| Funding normiert +Long-Short | +13,5 % | 8. | +3,4 % | 9. |
| ALLES aggregiert | +12,0 % | 9. | +4,6 % | 6. |

**In BEIDEN Hälften besser als der heutige Stand: keine einzige Variante.**

Und die Rangfolge kippt lehrbuchmäßig: Der heutige Stand ist in Hälfte 1 **Erster**
und in Hälfte 2 **Siebter**. Das aggregierte Spot-CVD ist genau umgekehrt — Sechster,
dann Erster. Nach der Regel, die in diesem Bericht seit E11 steht („Kippt die
Rangfolge, war es Zufall"), ist damit **keiner** der Vollfenster-Vorsprünge belastbar,
in keine Richtung.

Die stabilste Zeile ist `OI aggregiert` (Platz 2 und 3) — aber auch sie schlägt den
heutigen Stand nicht in beiden Hälften.

### E37.6 — Entscheiden · Status: FERTIG 20.09.2026 — alle Schalter bleiben AUS

**Entscheidung: Die Engine wird nicht umgestellt.** Kein Schalter geht live, alles
bleibt auf dem heutigen Stand (Binance für die Order-Flow-Werte, Kraken fürs Funding).

Begründung, der Reihe nach gemessen:

| Etappe | Ergebnis | Rendite | Robustheit |
|---|---|---|---|
| E37.2 Spot-CVD | Unentschieden | −2,5 Punkte, Rückgang −1,2 | Rangfolge kippt |
| E37.3 OI/Liq/Futures-CVD | Rendite flach, Trefferquote besser | ±0 | Rangfolge kippt |
| E37.4 Funding/Long-Short | **Klares Nein** | −6,1 Punkte | in beiden Hälften letzte Plätze |
| E37.5 Halbierung | keine Variante in beiden Hälften besser | — | — |

**Was gewonnen wurde, obwohl nichts live geht:**

1. **Ein falscher Kommentar ist weg.** Der Code behauptete seit Juli eine Aggregation,
   die es nie gab. Jetzt steht dort, was stimmt — inklusive des Funding-Sonderwegs
   über Kraken, den niemand entschieden hatte.
2. **Eine Erklärung ist ausgeschlossen.** „Furkan sieht mehr, weil er über Börsen
   aggregiert" ist gemessen und widerlegt. Das war Kaisers Ausgangsfrage, und sie hat
   jetzt eine Antwort statt einer Vermutung.
3. **Die Datenzeilen haben endlich eine Robustheitsprüfung.** Sie stand seit E37.2 aus.
4. **Der Werkzeugkasten ist da.** `spot_delta_aggregiert`, `oi_aggregiert`,
   `liq_aggregiert`, `fut_delta_aggregiert`, `gewichtetes_mittel`, `skalen_vergleich`
   — alles getestet und sabotagegeprüft. Falls später ein Grund auftaucht, ist die
   Aggregation ein Schalter, kein Neubau.

**Ausdrücklich NICHT entschieden** und vor jeder späteren Umstellung zu klären:

- Die **71 % Vorzeichen-Übereinstimmung** beim Funding zwischen Kraken und Coinalyze.
  Solange das nicht erklärt ist, ist ein Quellentausch ein Austausch der Bedeutung.
- Die **25 % ausgelassenen Zeitpunkte** beim gewichteten Mittel.
- Ob `funding_hot = 0.0001` zur Kraken-Reihe überhaupt passt — die Schwelle wurde nie
  gegen diese Skala geprüft, sie stammt aus einer Zeit, in der niemand die Quelle kannte.

## Was E37 NICHT beantwortet hat

Kaisers eigentliche Frage war nicht „bringt Aggregation Rendite", sondern: **Warum hat
Furkan nachgekauft, wo die Engine ausgestoppt hat?**

Darauf gibt E37 eine Teilantwort — *nicht wegen besserer Order-Flow-Daten* — und
Kaiser hat am 20.09.2026 die bis dahin geltende Erklärung korrigiert:

> *„Du kennst die letzten Videos von Furkan nicht. Er hat nachgekauft und zwar auf dem
> Future Markt also ein Trade und keinen Spot Kauf."*

Damit fällt die „zwei Bücher"-Erklärung (Spot nach On-Chain-Bewertung, Trade nach
Chart) für diesen Fall aus. Die Frage ist offen.

**Was die Sichtung des Videos vom 10.09.2026 ergeben hat** (Bildauswertung, kein
Transkript vorhanden — fünf von 23 Minuten abgetastet):

- Makro: Financial Times zu Ölpreis und Anleiherenditen
- **Hyblock Capital** — Liquidations-Heatmap, BTC bei 77.055, Liquidität bei 76.749
- **checkonchain.com** — Short-Term-Holder MVRV und SOPR mit Standardabweichungsbändern

**Korrektur einer früheren Behauptung:** checkonchain.com ist **kostenlos**. Die
Einschätzung „MVRV und STH-Kostenbasis brauchen ein Bezahl-Abo (Glassnode/CryptoQuant)"
war falsch — wieder geschlossen statt nachgesehen.

**Zwei Ebenen, die die Engine überhaupt nicht hat:**

1. Eine **Bewertungsebene** — STH-MVRV, Kostenbasis, Standardabweichungsbänder.
2. Eine **Liquiditätskarte** — wo ruhende Liquidität und Stops liegen. Die Engine sieht
   Liquidations*ereignisse* nach dem Auslösen, nicht die Karte davor.

Das ist die bessere Spur als alles, was in E37 steckte — und es erklärt, warum E37
nichts gefunden hat: Gesucht wurde in der Ebene, die wir schon hatten.

### E37.6 — Entscheiden · Status: FERTIG 20.09.2026 — alle Schalter bleiben AUS

Nur wenn E37.5 es trägt, wird die Engine umgestellt. Sonst bleibt der Schalter aus und
der Befund steht dokumentiert im Wissens-Layer. **„Recall ≠ Gewinn" gilt hier
genauso: näher an Furkan ist kein Ergebnis.**

## Was bewusst NICHT gemacht wird

- **Keine neue Datenquelle.** Velo kostet 199 $/Monat; Coinbase, Bybit und OKX liefern
  in ihren eigenen Kerzen kein Taker-Kaufvolumen. Coinalyze bleibt die einzige Quelle.
- **Kein OKX-Ersatz über Umwege**, falls E37.1 bestätigt, dass dort nichts zu holen
  ist. Drei von vier Börsen werden dann als Drei-von-vier dokumentiert, nicht
  kaschiert.
- **Keine Änderung an der Handelslogik.** E37 tauscht Daten aus, keine Regeln. Ob
  Furkans positive Konfluenz als Einstiegsbedingung gebaut wird, ist eine eigene
  Frage (siehe unten) und wartet auf das Ergebnis von E37.5.
- **Keine Rückrechnung älterer Berichte.** Alle Zahlen in `BACKTEST.md` von vor E37
  beruhen auf Binance-Daten. Sie werden als solche gekennzeichnet, nicht neu gerechnet.

## Offen daneben, nicht Teil von E37

Aus derselben Recherche, bewusst getrennt gehalten: **Furkans positive Konfluenz.**
Muster 5 (ungesunder Abverkauf) ist sein Vier-fach-UND in der negativen Richtung und
ist als `block_unhealthy` gemessen. Die positive Seite prüft in `_confirm_long()` nur
zwei von sieben Werten und verknüpft sie mit ODER — eins von dreien genügt. Ein
Vier-fach-UND als Einstiegsbedingung wurde nie als Gitterzeile gemessen.

Das ist die nächste inhaltliche Etappe nach E37 — und sie profitiert davon, dann auf
aggregierten Daten zu laufen.

## Regeln für jede Etappe

1. Alles schaltbar, **Default aus** (= heutiger Zustand).
2. **Sabotage-Probe für jeden neuen Test**, mit den oben genannten Pflichtsabotagen.
   Ungefangene Sabotage heißt: Test nachziehen, nicht Sabotage streichen.
3. Erst messen, dann behaupten. Kein Schalter geht live ohne Backtest-Zeile.
4. Nach jeder Etappe: Status hier auf FERTIG mit Datum, Abweichungen dokumentieren,
   Testweg und Upload-Schritte an Kaiser.
5. Kaiser ist nicht IT-affin: jeder Schritt einzeln, anklickbar, ohne Entscheidung
   seinerseits.

## Übergabeprompt für eine spätere Session

```
Lies zuerst wissens-layer/02_status/GEMESSEN-UND-ENTSCHIEDEN.md, dann
docs/PLAN-E37-AGGREGATION.md.
Arbeite den Etappenplan ab: beginne bei der ersten Etappe mit Status OFFEN und setze
nach jeder fertigen Etappe den Status auf FERTIG mit Datum.
Regeln: alles schaltbar mit Default aus; Sabotage-Probe fuer jeden Test; erst messen,
dann behaupten; Recall ist kein Gewinn; Kaiser braucht anklickbare Einzelschritte.
Arbeitsumgebung: device_bash geht nicht (Windows-Update 08.09.2026) — Dateien per
device_stage_files -> Cloud -> SendUserFile -> device_commit_files MIT fileUuid.
Workflow-Dateien sind geschuetzt und muessen von Kaiser von Hand kopiert werden.
Nach jeder Etappe: Verifikation, Testweg, Upload-Schritte.
```
