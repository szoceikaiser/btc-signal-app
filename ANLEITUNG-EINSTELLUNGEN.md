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

### Welcher Schalter macht was?

**Die Erklärungen stehen in der `config.json` selbst.** Zu jedem Schalter gehört dort
ein Feld `_hinweis_<name>` — es sagt, was er tut, was gemessen wurde und warum er an
oder aus ist. Wenn du die Datei zum Ändern öffnest, hast du die Begründung also direkt
vor Augen.

Das ist bewusst so: Eine zweite Liste hier in der Anleitung ist irgendwann veraltet,
ohne dass es jemand merkt. Genau das war bis zum 05.09.2026 der Fall — hier standen 14
Schalter beschrieben, während die `config.json` 29 kannte. Alles, was hier stand und
dort fehlte, ist inzwischen dorthin übertragen worden.

**Welche Schalter es gibt und wie sie jetzt stehen,** zeigt dir die `config.json`
selbst — oder, als Übersicht mit Messergebnis und Entscheidung, die Tabelle in
`BTC-Trading\wissens-layer\02_status\GEMESSEN-UND-ENTSCHIEDEN.md`.

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

## 2b. Die Flush-Wache (seit 29.07.2026)

Flush-Einstiege sind das Gegenteil der Level-Käufe: schnelle Bewegungen, oft innerhalb
einer Kerze vorbei, **nicht als Limit-Order vorbereitbar**. Dafür gibt es einen eigenen,
leichten Zwischenlauf — Workflow **Flush-Wache**, alle 15 Minuten.

Er schaut nur nach, ob der Kurs in der **laufenden** Kerze gerade durch das Golden Pocket
fällt, und schickt dann:

```
⚡ FLUSH ENTWICKELT SICH — noch NICHT bestaetigt
BTC gerade 63.400 $
Golden Pocket 63.200 $ nach unten durchstossen
Ungueltig ab  62.000 $ — noch 2.2 % Luft
Die Kerze schliesst um 16:00 UTC.
```

**Warum kein Signal?** Die Flush-Bedingung verlangt, dass die Kerze **über** der
Ungültig-Marke *schließt*. Bei einer laufenden Kerze steht das nicht fest — der Kurs kann
noch weiter fallen. Ein Signal, das jetzt gilt und in zwei Stunden nicht mehr, wäre
schlimmer als ein spätes. Deshalb ein Hinweis zum Hinschauen, keine Aufforderung.

**Nach Kerzenschluss kommt automatisch die Auflösung** — bestätigt oder nicht. Damit
bleibt keine Warnung offen.

Höchstens eine Warnung je Kerze. Der Zwischenlauf fasst die Engine nicht an, erzeugt keine
Signale und taucht im Backtest nicht auf. Fällt er aus, ändert sich an den Signalen nichts.
Abschalten über `flush_wache` in der `config.json`.

**Damit er wirklich alle 15 Minuten läuft, braucht er den externen Anstoß** (siehe
[ANLEITUNG-PUENKTLICHER-START.md](ANLEITUNG-PUENKTLICHER-START.md)) — GitHub-Zeitpläne
werden verworfen, das ist ja der Grund für die ganze Übung. Ein zweiter Auftrag bei
cron-job.org, alle 15 Minuten, URL endet auf `watch.yml/dispatches`.

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

**Achtung, das war lange falsch beschrieben:** `pivot_n`, `k_atr`, `flush_entry` und
`buy_ladder` stehen **nicht mehr** im Quelltext, sondern in der `config.json` wie jeder
andere Schalter auch. Sie werden dort geändert, nicht in `engine/strategy_core.py`.

Wirklich nur im Quelltext stehen noch:

| Was | Wo | Bedeutung |
|---|---|---|
| `TRANCHEN` | `engine/strategy_core.py`, oberhalb von `evaluate` | Positionsgrößen je Signal (25/50/25 rein, 40/40/Rest raus) |
| `oi_wipeout_pct`, `sharp_move_pct`, `funding_hot` | `engine/strategy_core.py`, in `classify_pattern(...)` | Schwellen der **5** Kompass-Muster (Furkans vier plus „ungesunder Abverkauf", ergänzt 07/2026) |

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

## 7. Änderungen vom lokalen Ordner hochladen

**Seit 05.09.2026 genügt ein Doppelklick auf `HOCHLADEN.cmd`** im Ordner
`C:\Users\oeztu\BTC-Trading`. Das Skript zeigt die geänderten Dateien, fragt nach
einer kurzen Beschreibung (Enter setzt das Datum ein), lädt den Code zu GitHub hoch und
sichert danach die Unterlagen ins private Backup-Repo. Die hängende `index.lock` räumt
es selbst weg.

Falls du es doch von Hand machen willst:

```
cd /d C:\Users\oeztu\BTC-Trading\signal-app
del .git\index.lock
git add -A
git commit -m "Kurze Beschreibung der Aenderung"
git pull --rebase
git push
```

Bekannte Fehler und Lösungen:

| Fehlermeldung | Ursache | Lösung |
|---|---|---|
| `rejected … non-fast-forward` | Die Automatik hat inzwischen selbst committet | `git pull --rebase`, dann `git push` |
| `index.lock: File exists` | abgebrochener git-Prozess | `del .git\index.lock`, dann Befehle wiederholen |
| `CONFLICT` beim Rebase | dieselbe Datei an beiden Orten geändert | `git rebase --abort`, dann Claude fragen |

**Warum `--rebase` und nicht nur `git pull`:** Ohne das öffnet git mitunter einen
Texteditor in der Konsole und will eine Zusammenführungs-Nachricht — daraus kommt man
ohne vim-Kenntnisse schlecht wieder heraus.
