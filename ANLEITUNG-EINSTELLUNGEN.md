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

| Schalter | Werte | Bedeutung |
|---|---|---|
| `bias_long` | `true` / `false` | Long-Signale erlauben. Steht auf `true`. |
| `bias_short` | `true` / `false` | Short-Signale erlauben. Steht auf **`false`** — Shorts haben in jeder Messung Geld verloren, weil der Engine der Richtungs-Bias fehlt. |
| `trail_stop` | `true` / `false` | Stop nachziehen, sobald Teilgewinne realisiert sind: auf den Durchschnitts-Einstand (Break-even) bzw. hinter das letzte Struktur-Tief. Furkans „Kapital schützen". Steht auf **`true`**. |
| `release_stale_rest` | `true` / `false` | Restposition freigeben, wenn ein neuer Impuls bestätigt ist. Löst dasselbe Problem wie `trail_stop`, aber schlechter (verkauft zum Marktpreis). Steht auf `false` — nur eines von beiden einschalten. |
| `liq_exit` | `off` / `spike` / `zone` / `both` | Teilverkauf an Liquidationen. Gemessen: kostet Rendite. Steht auf `off`. |
| `high_exit` | `off` / `on` / `weak` | Teilverkauf kurz unter dem letzten Hoch. Gemessen: kostet Rendite. Steht auf `off`. |
| `liq_entry` | `off` / `boost` / `filter` | Liquidationszonen beim **Einstieg**: `boost` stockt zusätzlich auf, wenn Fib-Zone und Liquidationszone zusammenfallen (Furkans Konfluenz), `filter` lässt nur noch solche Einstiege zu. Noch nicht gemessen. |

**Goldene Regel:** Immer nur EINEN Schalter auf einmal ändern und danach einen Backtest
laufen lassen (Abschnitt 3). Sonst weißt du hinterher nicht, welche Änderung was bewirkt
hat. Und: Was der Backtest nicht bestätigt hat, bleibt aus.

## 2. Prüf-Takt der Engine ändern

Datei: [`.github/workflows/signal.yml`](https://github.com/szoceikaiser/btc-signal-app/edit/main/.github/workflows/signal.yml)

Zeile `- cron: "7,22,37,52 * * * *"` = Minuten 7, 22, 37, 52 jeder Stunde.
Seltener prüfen (z. B. stündlich): `- cron: "7 * * * *"`. Öfter als alle 15 Min
bringt nichts (die Strategie arbeitet auf 4h-Kerzen) und GitHub verzögert ohnehin.

## 3. Backtest starten

1. [Actions → Backtest](https://github.com/szoceikaiser/btc-signal-app/actions/workflows/backtest.yml)
2. **Run workflow** → grüner Knopf. Dauert 5–15 Minuten.
3. Ergebnis: Datei `BACKTEST.md` im Repo **und** das Backtest-Panel auf der
   [Chart-Webseite](https://szoceikaiser.github.io/btc-signal-app/) (Seite neu laden).

Wichtig beim Lesen: „Ähnlichkeit" (Recall) sagt, wie oft die Engine an Furkans
Terminen gehandelt hätte. **Gewinn/Verlust steht NUR in der Simulations-Zeile**
(10.000 € → …). Das sind zwei verschiedene Dinge.

## 4. Strategie-Parameter (für Fortgeschrittene)

Datei: `engine/strategy_core.py`. Relevante Stellschrauben:

| Was | Wo | Bedeutung |
|---|---|---|
| `pivot_n=5` | `def evaluate(...)` | Kerzen zur Swing-Bestätigung. Kleiner = mehr, frühere Signale (mehr Rauschen) |
| `k_atr=2.0` | `def evaluate(...)` | Mindestgröße eines Impulses in ATR. Kleiner = mehr Impulse zählen |
| `flush_entry="core"` | `def evaluate(...)` | Einstieg in die Kapitulations-Kerze. Verdoppelt Rendite UND maximalen Rückgang. Die Signale sind in Telegram als „AGGRESSIVER FLUSH-EINSTIEG — DEINE Entscheidung" markiert, du entscheidest also ohnehin je Fall |
| `buy_ladder=True` | `def evaluate(...)` | Mehrtages-Kaufleiter (Nachkauf in die Schwäche). Bester gemessener Renditehebel |
| `TRANCHEN` | oberhalb von `evaluate` | Positionsgrößen je Signal (25/50/25 rein, 40/40/Rest raus) |
| `oi_wipeout_pct`, `sharp_move_pct`, `funding_hot` | `def classify_pattern(...)` | Schwellen der 4 Kompass-Muster |

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
