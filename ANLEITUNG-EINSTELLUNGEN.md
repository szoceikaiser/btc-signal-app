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

## 1. Long/Short an- oder abschalten

Datei: [`site/data/state.json`](https://github.com/szoceikaiser/btc-signal-app/edit/main/site/data/state.json)

1. Link öffnen (führt direkt in den Bearbeiten-Modus)
2. Den Block `"config"` suchen:
   ```json
   "config": { "bias_long": true, "bias_short": true }
   ```
3. Die Seite, die du NICHT handeln willst, auf `false` setzen.
   Beispiel „nur Long": `"bias_short": false`
4. **Commit changes**

Wirkung: ab dem nächsten Engine-Lauf (max. 15 Min). Kontrolle: Datei neu öffnen —
steht dein Wert noch drin? (Selten überschreibt ein zeitgleicher Engine-Lauf die
Änderung — dann einfach wiederholen.)

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
