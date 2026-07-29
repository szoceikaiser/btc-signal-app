# Anleitung: Einstellungen der Signal-App ändern

Alle Einstellungen werden direkt auf GitHub geändert — du brauchst dafür nur den
Browser. Grundprinzip immer gleich: Datei öffnen → **Stift-Symbol** (oben rechts,
„Edit this file") → ändern → grüner Knopf **Commit changes**.

**Goldene Regeln (aus Erfahrung):**
- Namen und Werte **kopieren statt tippen** — ein Tippfehler und nichts funktioniert.
- Nach JEDER Änderung den Kontrollpunkt prüfen, der beim jeweiligen Abschnitt steht.
- In JSON-Dateien nur die Werte ändern (z. B. `true` → `false`), niemals
  Anführungszeichen, Kommas oder Klammern löschen.

---

## 1. Alle Schalter der Engine (`config.json`)

Datei: [`site/data/config.json`](https://github.com/szoceikaiser/btc-signal-app/edit/main/site/data/config.json)
(diese Datei wird von der Engine NIE überschrieben — hier gibt es keine Konflikte)

**So geht jede Änderung:** Link öffnen (führt direkt in den Bearbeiten-Modus) → **nur den
Wert** ändern, also z. B. `false` durch `true` ersetzen → Anführungszeichen, Doppelpunkt
und Komma stehen lassen → oben rechts **Commit changes…** → im Dialog nochmal **Commit
changes**. Wirkung ab dem nächsten Engine-Lauf.

**Kontrollpunkt:** Datei neu laden — steht dein Wert noch drin? Und in
[`site/data/state.json`](https://github.com/szoceikaiser/btc-signal-app/blob/main/site/data/state.json)
zeigt der Abschnitt `config` nach dem nächsten Lauf denselben Wert. Erst dann hat die
Engine ihn wirklich gelesen.

**Stand 28.07.2026.** Die Spalte „jetzt" zeigt, was live eingestellt ist.

| Schalter | Werte | jetzt | Bedeutung und Messstand |
|---|---|---|---|
| `bias_long` | `true` / `false` | **`true`** | Long-Signale erlauben. |
| `bias_short` | `true` / `false` | **`false`** | Short-Signale erlauben. Aus: Shorts haben in jeder Messung Geld verloren (+41 % nur Long gegen −1 % mit Shorts), weil der Engine der Richtungs-Bias fehlt. |
| `trail_stop` | `true` / `false` | **`true`** | Stop nachziehen, sobald Teilgewinne realisiert sind: auf den Durchschnitts-Einstand (Break-even) bzw. hinter das letzte Struktur-Tief. Furkans „Kapital schützen". |
| `min_stop_pct` | Zahl, `0` = aus | **`0.02`** | **Mindestabstand zwischen Einstieg und Stop (2 %).** Ist der Stop näher, wird gar nicht erst gekauft — solche Stops löst schon das normale Rauschen aus. Verschiebt den Stop NICHT und blockiert KEINE Nachkäufe; er gilt nur beim Eröffnen. Gemessen: gleiche Rendite bei fast halbem Rückgang, ein Viertel weniger Nachrichten. |
| `liq_entry` | `off` / `boost` / `filter` | **`boost`** | Liquidationszonen beim **Einstieg**. `boost` = zusätzliche Nachkauf-Tranche, wenn Fib-Zone und Liquidationszone zusammenfallen (Furkans Konfluenz), höchstens 2× je Position; verbietet nie etwas. `filter` = nur noch bei Konfluenz einsteigen — gemessen, schlechter. |
| `high_exit` | `off` / `on` / `weak` | **`on`** | Teilverkauf, sobald der Kurs bis auf 0,5 % an das letzte bestätigte Hoch heranläuft (Furkan: „hier unter diesem Hoch rausnehmen"). `weak` = nur ohne Spot-Nachfrage. **Achtung:** Gegen die alte Basis kostete das 3,9 Punkte, gegen die heutige bringt es 1,2 — ein Befund gilt immer nur für die Basis, gegen die er gemessen wurde. |
| `release_stale_rest` | `true` / `false` | `false` | Restposition freigeben, wenn ein neuer Impuls bestätigt ist. Löst dasselbe Problem wie `trail_stop`, aber schlechter (verkauft zum Marktpreis). Nur eines von beiden einschalten. |
| `liq_exit` | `off` / `spike` / `zone` / `both` | `off` | Teilverkauf an Liquidationen. Zweimal gemessen, kostet beide Male Rendite. |
| `block_unhealthy` | `true` / `false` | `false` | „Warnlicht": kein Kauf und kein Nachkauf, solange Muster 5 aktiv ist (Kurs fällt, Spot-CVD fällt mit, OI hält, Funding positiv, noch keine Zwangsverkaufs-Welle = der Absturz ist noch nicht durch). Gemessen 07/2026: hat 3 von 212 Signalen verhindert, −2,2 Punkte. Bleibt aus. |
| `confirm_t1` | `true` / `false` | `false` | Order-Flow-Prüfung auch für den 0.5-Level-Einstieg — der einzige Einstieg ohne jede Prüfung. Gemessen: −4,6 Punkte. Bleibt aus. |
| `cooldown_h` | Stunden, `0` = aus | `0` | Sperrfrist nach einem Stop. Gemessen: wirkt (Rückgang −12,3 → −8,5 %), kippt aber zwischen den Zeit-Hälften stark (Platz 22 / Platz 2) — deshalb nicht gewählt. `min_stop_pct` erreicht dasselbe stabiler. |

**Goldene Regel:** Immer nur EINEN Schalter auf einmal ändern und danach einen Backtest
laufen lassen (Abschnitt 3). Sonst weißt du hinterher nicht, welche Änderung was bewirkt
hat. Und: Was der Backtest nicht bestätigt hat, bleibt aus.

**Zweite Regel, teuer gelernt:** Ein Messergebnis gilt nur gegen die Basis, gegen die
gemessen wurde. Nach jeder Umstellung sind verworfene Mechanismen wieder offen —
`high_exit` war fünfmal „kostet Rendite" und ist heute eingeschaltet.

**Wenn du einen Schalter änderst:** In `engine/backtest.py` muss `panel=True` auf der
Gitterzeile stehen, die deiner neuen Einstellung entspricht — sonst zeigt das Panel auf
der Webseite eine Rendite, die die Engine nie erzielt hat. Ebenso muss die Zeile
„MEINE Einstellung ohne Flush" mitwandern, damit die zweite Spalte der Monatsübersicht
sich weiterhin nur im Flush unterscheidet.

## 2. Prüf-Takt der Engine ändern

Datei: [`.github/workflows/signal.yml`](https://github.com/szoceikaiser/btc-signal-app/edit/main/.github/workflows/signal.yml)

**Pünktlich gestartet wird die Engine seit 29.07.2026 von außen** — siehe
[ANLEITUNG-PUENKTLICHER-START.md](ANLEITUNG-PUENKTLICHER-START.md). Der GitHub-Zeitplan
ist nur noch das Netz für den Fall, dass der externe Dienst ausfällt.

Zeile im Workflow: `- cron: "2,32 0,4,8,12,16,20 * * *"` — zwei Rückfall-Versuche je
4h-Kerzenschluss (00/04/08/12/16/20 UTC), 12 Läufe am Tag.

**Warum nicht öfter?** Zwei Gründe. Erstens wertet die Strategie nur *abgeschlossene*
4h-Kerzen aus — dazwischen gibt es nichts zu entscheiden. Zweitens hilft „öfter" bei
GitHub nachweislich nicht:

| gemessen am 29.07.2026 | Versuche je Kerzenschluss | tatsächliche Läufe | Verzug |
|---|---|---|---|
| vorher | 4 | 1 | 1–2 h |
| Versuch, es zu verbessern | 7 | **weiterhin 1** | 2,5–3 h |

In sechs beobachteten Zeitfenstern gab es **nie zwei Läufe**. Bei zufälligem Verwerfen
hätte man bei sieben Versuchen fast zwei erwartet. GitHub drosselt offenbar pro
Repository — dagegen helfen mehr Einträge nicht, nur ein anderer Startweg.

## 2a. Warum Limit-Orders im Voraus wichtiger sind als der Takt

Deine Signale zerfallen in zwei Gruppen, und sie verhalten sich völlig verschieden:

| Signal | genannter Preis | hilft Pünktlichkeit? |
|---|---|---|
| Kauf am 0.5-Level, Golden Pocket, 0.786-Zone, Teilgewinn-Ziele | ein **Level** | **kaum** |
| Stop, Restverkauf, Flush-Einstieg, Kaufleiter, Liq-Konfluenz | **Kerzenschluss** | **sehr** |

Der Grund für die erste Zeile: Ein Kaufsignal am 0.5-Level entsteht, weil das **Tief** der
Kerze das Level berührt hat. Dieses Tief kann in Stunde 2 einer 4-Stunden-Kerze gelegen
haben. Zum Kerzenschluss steht der Kurs womöglich längst wieder darüber — der Preis aus
der Nachricht ist dann nicht mehr am Markt, egal wie schnell du liest.

**Die Lösung ist, die Order vorher hinzulegen.** Genau so beschreibt Furkan es im Video:
„da könnte man dann schon erste Order platzieren." Er wartet nicht auf ein Signal, er
lässt sich abholen.

**Damit das geht, zeigt die Chart-Webseite die Zonen jetzt auch ohne offene Position**
(ergänzt 29.07.2026). Vorher standen dort nur Linien, während eine Position lief — also
genau dann nicht, wenn man den Einstieg vorbereitet. Erkennbar an der Beschriftung:

- **gestrichelt**, ohne Zusatz = Zonen einer laufenden Position
- **gepunktet**, mit „(Vorschau)" = aktuelle Struktur, noch keine Position offen

Unter dem Chart steht dann zusätzlich, welche Richtung die Struktur hat und aus welchem
Impuls sie stammt. Ist gar nichts eingezeichnet, hat die Engine gerade keinen
signifikanten Impuls gefunden — dann gibt es auch nichts vorzubereiten.

## 3. Backtest starten

1. [Actions → Backtest](https://github.com/szoceikaiser/btc-signal-app/actions/workflows/backtest.yml)
2. **Run workflow** → grüner Knopf. Dauert 5–15 Minuten.
3. Ergebnis: Datei `BACKTEST.md` im Repo **und** das Backtest-Panel auf der
   [Chart-Webseite](https://szoceikaiser.github.io/btc-signal-app/) (Seite neu laden).

Wichtig beim Lesen: „Ähnlichkeit" (Recall) sagt, wie oft die Engine an Furkans
Terminen gehandelt hätte. **Gewinn/Verlust steht NUR in der Simulations-Zeile**
(10.000 € → …). Das sind zwei verschiedene Dinge.

**Und seit 28.07.2026 wissen wir mehr:** Die Ähnlichkeit ist auch kein *Ziel*. Der
Berichtsabschnitt „Furkans eigene Termine gegen die Engine" rechnet seine Trigger-Listen
durch dieselbe Simulation — sie hätten im Messzeitraum Geld verloren. Das erklärt, warum
über Wochen jeder Mechanismus, der den Recall hob, Rendite kostete. **Recall beschreibt,
er steuert nicht.** Bewerte Änderungen an Rendite und maximalem Rückgang.

Diese Abschnitte stehen im Bericht:

| Abschnitt | Was er beantwortet |
|---|---|
| Parameter-Vergleich | alle Varianten nebeneinander |
| Monat für Monat | was das Konto in jedem Kalendermonat gemacht hätte, mit und ohne Flush |
| Was ist die Vorab-Information wert? | wie viel Rendite davon abhängt, dass die Limit-Order vorher dort liegt |
| Echte Futures-Daten | ob bessere Daten etwas bringen (Antwort 07/2026: kaum) |
| Furkans eigene Termine | ob seine Methode mehr Geld gebracht hätte |
| Robustheitsprüfung | ob die Rangfolge trägt oder Zufall ist — **inklusive der Zahl, die der Zufall allein liefern würde** |

## 4. Strategie-Parameter (für Fortgeschrittene)

Datei: `engine/strategy_core.py`. Relevante Stellschrauben:

| Was | Wo | Bedeutung |
|---|---|---|
| `pivot_n=5` | `def evaluate(...)` | Kerzen zur Swing-Bestätigung. Kleiner = mehr, frühere Signale (mehr Rauschen) |
| `k_atr=2.0` | `def evaluate(...)` | Mindestgröße eines Impulses in ATR. Kleiner = mehr Impulse zählen |
| `flush_entry="core"` | `def evaluate(...)` | Einstieg in die Kapitulations-Kerze. Verdoppelt Rendite UND maximalen Rückgang. Die Signale sind in Telegram als „AGGRESSIVER FLUSH-EINSTIEG — DEINE Entscheidung" markiert, du entscheidest also ohnehin je Fall |
| `buy_ladder=True` | `def evaluate(...)` | Mehrtages-Kaufleiter (Nachkauf in die Schwäche). Bester gemessener Renditehebel |
| `TRANCHEN` | oberhalb von `evaluate` | Positionsgrößen je Signal (25/50/25 rein, 40/40/Rest raus) |
| `oi_wipeout_pct`, `sharp_move_pct`, `funding_hot` | `def classify_pattern(...)` | Schwellen der **5** Kompass-Muster (Furkans vier plus „ungesunder Abverkauf", ergänzt 07/2026) |

Nach jeder Änderung laufen die Tests automatisch (Actions → Tests). **Wird der Lauf
rot: Änderung rückgängig machen** (im Commit-Verlauf „Revert") oder Claude fragen.
Empfehlung: Parameter-Änderungen zuerst per Backtest (Abschnitt 3) bewerten.

## 5. Telegram-Nachrichtentexte ändern

Datei: `engine/telegram_notify.py`, Funktion `format_signal` (Textzeilen) und
`STYLE` (Emojis). Gleiche Regel: Tests müssen grün bleiben.

## 6. Chart-Bedienung (keine Einstellung nötig)

Mausrad bzw. zwei Finger = Zoom · Ziehen = Verschieben · **Doppelklick = Ansicht
zurücksetzen** · Überfahren einer Kerze = OHLC-Overlay oben links (Open, High, Low,
Close, Veränderung) · Knöpfe oben rechts = Zeitebene (1h–1M).

## 7. Änderungen vom lokalen Ordner hochschieben (mit Claude erarbeitet)

Wenn Claude Dateien in `C:\Users\oeztu\BTC-Trading\signal-app` geändert hat:

```
cd C:\Users\oeztu\BTC-Trading\signal-app
git pull --no-rebase
git add -A
git commit -m "Kurze Beschreibung der Aenderung"
git push
```

Bekannte Fehler und Lösungen:

| Fehlermeldung | Ursache | Lösung |
|---|---|---|
| `rejected … non-fast-forward` | Engine hat inzwischen selbst committet | erst `git pull --no-rebase`, dann `git push` |
| `index.lock: File exists` | abgebrochener git-Prozess | `del C:\Users\oeztu\BTC-Trading\signal-app\.git\index.lock`, dann Befehle wiederholen |
| Editor-Fenster mit „Merge branch…" | normaler Merge-Hinweis | Fenster einfach schließen |
