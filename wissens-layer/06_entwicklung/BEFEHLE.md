# Befehle

> Alles, was man zum Arbeiten braucht. Stand: 26.09.2026.

## Für Kaiser: Änderungen hochladen

**Doppelklick auf `HOCHLADEN.cmd`** im Ordner `C:\Users\oeztu\BTC-Trading`.

Das Skript zeigt die geänderten Code-Dateien, fragt nach einer kurzen Beschreibung
(Enter setzt das Datum ein), lädt zu GitHub hoch und sichert danach die Unterlagen
ins private Repo. Die hängende `index.lock` räumt es selbst weg. Geht das
Zusammenführen mit GitHub schief, bricht es sauber ab (`git rebase --abort`) und gibt
eine Meldung aus.

`BACKUP.cmd` wird davon aufgerufen und muss nicht mehr einzeln angeklickt werden.

## Für Kaiser: Backtest anstoßen

GitHub → Repo `btc-signal-app` → Reiter **Actions** → links **Backtest** →
**Run workflow**. Dauert rund 6 Minuten (gemessen 21.09.2026, 67 Varianten).

Danach steht der Bericht in `BACKTEST.md` und — seit 05.09.2026 — auch unter
`site\BACKTEST.md`, also über die Webseite lesbar. Auf den Rechner kommt er mit
`stand-holen.bat`.

## Für Kaiser: Lage auf Knopfdruck

GitHub → **Actions** → **Lage-Abruf** → **Run workflow**. Schickt eine Telegram-Nachricht
mit Struktur, Zonen, Order-Flow-Rohwerten, Ampel und STH-Kostenbasis — unter der
**Annahme** einer Long-Position. Ändert nichts, erzeugt kein Signal, fasst `state.json`
nicht an.

## Für Kaiser: Stand von GitHub holen

Doppelklick auf **`stand-holen.bat`** — das ist immer der letzte Schritt nach einem
Backtest oder einem Engine-Lauf.

Nur nachsehen, ohne eigene Dateien anzufassen:

```
cd /d C:\Users\oeztu\BTC-Trading\signal-app
git fetch
git log --oneline HEAD..origin/main
```

## Tests

```
cd engine
python3 run_tests.py
```

**444 Tests** (Stand 26.09.2026), alle müssen grün sein. **Kein `pytest`** — die
Umgebung erreicht PyPI nicht zuverlässig, deshalb der eigene Läufer.

Die Zahl hier mitzupflegen lohnt sich: Läuft der Läufer plötzlich mit *weniger* Tests
durch und meldet trotzdem „0 failed", hat sich eine Datei still übersprungen — genau
der Fehlertyp, den dieses Projekt schon zweimal teuer bezahlt hat. Dasselbe gilt für die
Zeile `UEBERSPRUNGEN: site/data/config.json fehlt`: Dann fehlt der Arbeitskopie die
Repo-Struktur, und die Panel-Prüfung lief nicht.

Auf Windows vorher `PYTHONIOENCODING=utf-8` setzen, sonst scheitern einige Tests nur
am Emoji-Druck in der Konsole, nicht am Code.

**Sabotage-Proben** liegen als `engine\sabotage_e*.py` daneben (z. B. `python3
sabotage_e41.py`). Sie verfälschen den Code absichtlich Zeile für Zeile und prüfen,
ob die Tests rot werden. Ein Test, den keine Sabotage rot färbt, prüft nichts. Fünf
Proben, zusammen 151 Sabotagen, alle gefangen (Stand 26.09.2026).

**Eine Probe niemals von außen abbrechen** — sie stellt die verfälschte Datei erst am
Ende wieder her. Lange Läufe im Hintergrund mit Protokoll starten und danach prüfen,
dass der Code wieder unverändert ist.

## Umgebungsgrenzen (wichtig für jede KI-Session)

| Was | Zustand |
|---|---|
| Börsen-APIs (Binance, Coinalyze) | Aus einer Cloud-Arbeitsumgebung **nicht** erreichbar (Proxy). Messen lässt nur der Backtest auf GitHub |
| GitHub | Aus einer Cloud-Arbeitsumgebung meist **nicht** erreichbar. Dann: Kaiser `git fetch` ausführen lassen und über `origin/main` lesen. Hat die KI eigenen Zugriff, kann sie Lauf-Verlauf und Repo direkt prüfen — gepusht wird trotzdem nur von Kaiser |
| PyPI | Blockiert. Kein Nachinstallieren von Paketen |
| git-Schreibbefehle im gemounteten Ordner | **Nicht ausführen.** Die `index.lock` bleibt hängen. Lesen ist in Ordnung |
| Dateien löschen im gemounteten Ordner | Nicht möglich. Stattdessen überschreiben oder verschieben |
| Workflow-Dateien (`.github\workflows\`) | Aus manchen Umgebungen nicht schreibbar. Kaiser kopiert sie von Hand |

## Die Engine von Hand anstoßen

GitHub → Actions → **Signal-Engine** → **Run workflow**. Läuft sonst pünktlich über
cron-job.org (sechsmal täglich, 0/4/8/12/16/20 UTC + 2 Minuten), zusätzlich als Netz
über den GitHub-Zeitplan, plus die **Flush-Wache** alle 15 Minuten.

## Einstellungen ändern

`site\data\config.json` bearbeiten, hochladen, wirkt ab dem nächsten Lauf
(spätestens nach 15 Minuten). Die Datei wird von der Engine **nie** überschrieben,
kann also konfliktfrei bearbeitet werden.

Zu jedem Schalter steht im Feld `_hinweis_<name>`, was er tut, was gemessen wurde und
warum er an oder aus ist. Das ist die maßgebliche Quelle dafür — nicht
`ANLEITUNG-EINSTELLUNGEN.md`.

**Wird ein Schalter live geschaltet, muss `panel=True` in `backtest.py` mitwandern**,
sonst zeigt der Chart die Rendite einer Einstellung, die nicht mehr gefahren wird.
Ein Test hält das fest und schlägt an, wenn es vergessen wird. **Mitwandern müssen
auch** „MEINE Einstellung ohne Flush" und jede Zeile „LIVE-heute + X" — sonst misst
sie zwei Unterschiede statt einem (zuletzt geprüft bei E41, 21.09.2026; auch das
halten Tests fest).
