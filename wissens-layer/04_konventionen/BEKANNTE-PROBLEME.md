# Bekannte Probleme und Umgebungsfallen

> Was in der Praxis Zeit gekostet hat — Werkzeug-, Umgebungs- und Ablauffallen. Wer hier
> zuerst nachsieht, verliert die Stunde nicht zweimal. Für inhaltliche Befunde ist
> `02_status/GEMESSEN-UND-ENTSCHIEDEN.md` zuständig. Stand: 26.09.2026.

## Umgebung einer KI-Sitzung

| Was | Zustand | Folge für die Arbeit |
|---|---|---|
| Börsen-APIs (Binance, Coinalyze) | Aus einer Cloud-Sandbox meist **nicht** erreichbar (Proxy) | Kursdaten nicht selbst holen. Messen lässt nur der Backtest auf GitHub |
| GitHub | In der Claude-Code-Cloud-Umgebung **erreichbar** (Stand 26.09.2026), in anderen Sandboxen oft nicht | Wenn erreichbar: Stand selbst holen, auf dem Arbeitszweig committen und pushen, Actions prüfen. Wenn nicht: Kaiser `stand-holen.bat` ausführen lassen |
| PyPI | Blockiert | Keine Fremdpakete, deshalb `run_tests.py` statt `pytest` |
| Windows-Konsole | Bricht bei Emoji ab | Vor dem Testlauf `PYTHONIOENCODING=utf-8` setzen, sonst scheitern Tests am Druck, nicht am Code |
| Workflow-Dateien (`.github\workflows\`) | Aus manchen Sandboxen **nicht schreibbar** („protected file") | Kaiser kopiert sie von Hand |
| Dateien löschen im gemounteten Ordner | Meist nicht möglich | Überschreiben oder verschieben; Löschen macht Kaiser |
| git-Schreibbefehle im gemounteten Ordner | Verboten | `index.lock` bleibt hängen. Kaiser löscht sie mit `del "C:\Users\oeztu\BTC-Trading\signal-app\.git\index.lock"` |

**Wenn die KI selbst GitHub erreichen kann**, öffnet das drei Dinge, die vorher nicht
gingen: den Lauf-Verlauf prüfen (`…/actions` — ein roter Lauf fiel einmal **sechs Tage**
niemandem auf), den Backtest selbst anstoßen statt Kaiser zu bitten, und den echten
Stand im Repo lesen statt den auf Kaisers Rechner. **Seit 26.09.2026 pusht die KI
selbst** — auf einen Arbeitszweig, nie direkt auf `main` (Regeln: `ARBEITSREGELN.md`,
Abschnitt Git). Kaisers Rechner ist nur noch eine Kopie; er holt den Stand mit
`stand-holen.bat`, wenn er dort lesen will.

## Fallen beim Arbeiten mit Dateien

- **Eine einmal hochgeladene Kopie ist ein Schnappschuss, kein Spiegel.** Wer eine Datei
  vor einer Stunde aus dem Ordner geholt hat und sie jetzt vergleicht, vergleicht mit
  einem alten Stand. Vor jedem Vergleich frisch holen. Zweimal passiert, beide Male
  entstand daraus der Verdacht, eine Änderung sei verlorengegangen.
- **Vor dem Zurückschreiben die Änderungszeit prüfen** und beim Schreiben mitgeben, damit
  eine fremde Änderung nicht überschrieben wird. Läuft der Schreibversuch auf einen
  Konflikt, erst neu holen und die eigene Änderung erneut anwenden — nicht erzwingen.
- **Dateien nie aus abgeschnittener Werkzeug-Ausgabe neu tippen.** Immer mit einem
  kleinen Skript ändern, das die Datei selbst liest, und mit einem Anker arbeiten, der
  genau einmal vorkommt (`assert s.count(alt) == 1`).

## Fallen bei den Tests

- **Ein Test, der sich still überspringt, ist schlimmer als keiner.**
  `test_panel_variante_entspricht_der_live_einstellung` braucht `site\data\config.json`
  **neben** dem `engine`-Ordner. Fehlt die Repo-Struktur in der Arbeitskopie, übersprang
  er sich früher stumm: Am 13.09.2026 war jeder GitHub-Lauf sechs Tage rot, während die
  Arbeitskopie „alles grün" meldete. Seit E36.1 gibt er beim Überspringen eine Zeile aus
  — **taucht sie auf, ist die Testzahl nicht vollständig.**
- **Die Testzahl immer mitnennen.** „0 failed" bei weniger Tests heißt: eine Datei wurde
  nicht geladen.
- **Sabotage-Proben nie von außen abbrechen.** Sie verfälschen eine Datei, testen und
  stellen sie danach wieder her. Ein Abbruch mittendrin (21.09.2026: Zeitlimit der
  Shell nach zwei Minuten) lässt die Datei **sabotiert** zurück — die Tests waren danach
  rot, und die Ursache stand nicht im Code, sondern im abgebrochenen Werkzeug. Im
  Hintergrund mit Protokoll laufen lassen und danach prüfen, dass jede Vorlage wieder
  im Code steht.
- **Testfixtures, die ein anderes Datenformat bauen als der echte Code, decken den
  Fehler nicht auf** (gefunden 26.09.2026 in einem parallelen E43.6-Bau). `run_backtest()`
  liefert Signale als `dict` (`Signal.to_dict()`), nicht als `Signal`-Objekte. Drei neue
  Zählfunktionen griffen per Attribut zu (`s.reason`) statt per Schlüssel (`s["reason"]`);
  die Tests bauten von Hand `Signal`-Objekte und liefen grün, der echte Backtest-Lauf
  krachte. Lehre: Fixtures aus der echten Erzeugerfunktion bauen, nicht daneben.
- **Doppelte Dateien laufen mit.** Eine Kopie `coinalyze-1.py` samt Testdatei lag
  einmal im `engine`-Ordner und wurde vom Läufer mitgenommen — ein Test schlug an, der
  gar nicht zum Code gehörte.

## Fallen bei der Zusammenarbeit mehrerer Chats

- **Zwei Chats gleichzeitig am selben Repo bauen doppelt.** Am 26.09.2026 bauten zwei
  Sitzungen E43.6 unabhängig voneinander auf zwei Zweigen. Nach `main` kam nur eine
  Fassung; E43.7, das die andere Sitzung danach erledigt hatte, blieb auf dem nicht
  übernommenen Zweig liegen und galt in `main` weiter als „offen“. **Vor Beginn:**
  `git fetch` und `git branch -r --sort=-committerdate` — liegt ein Zweig vorn, der nicht
  in `main` ist (`git log origin/main..origin/<zweig>`), zuerst klären, was darauf steht.
  Und möglichst nur einen Chat zur Zeit arbeiten lassen.

## Fallen bei den Daten

- **bitview.space liefert eine Werteliste ohne Datum.** Das Datum wird aus `start` und
  dem Index gerechnet (Index 0 = 01.01.2009). Wer den Seriennamen nicht exakt trifft,
  bekommt schweigend eine **andere** Reihe — in E40.0 war es `sth_awake_price`.
- **bitcoin-data.com liefert Zahlen als Text** und erlaubt nur 15 Abrufe pro Tag und IP
  (GitHub teilt IPs). Die Werte hängen 7 Tage nach.
- **Binance-Futures-API sperrt GitHub-Runner** (HTTP 451) — deshalb der
  Public-Data-Spiegel.
- **Der Coinalyze-Endpunkt `buy-sell-volume-history` existiert nicht**; diese Daten
  stecken in der Kerzen-Historie.

## Bekannt und bewusst nicht behoben

- ~~**Code verweist über die Repo-Grenze.**~~ **Erledigt 26.09.2026:** `docs\` liegt jetzt
  im selben Repo wie der Code.
- **`widerstand_exits` (E20) wird nicht in `state.json` gespeichert.** Folgenlos, solange
  `widerstand_exit` aus ist — vor einem Einschalten zu beheben.
- **Tote Nachkaufstufen im Telegram-Plan:** Marken unterhalb des nachgezogenen Stops
  werden weiter angezeigt, obwohl sie unerreichbar sind. Reines Anzeigeproblem.
- **`ANLEITUNG-EINSTELLUNGEN.md` driftet** gegenüber `config.json`. Maßgeblich ist
  `config.json`; die Anleitung soll auf das „Wie" reduziert werden. Noch offen.
- **Die Flush-Wache hängt am GitHub-Zeitplan** und hat damit dasselbe Verzugsproblem,
  das für den Haupttakt seit 17.09.2026 behoben ist. Kaiser wollte die
  Telegram-Nachrichtenzahl „erst mal belassen".
- **`signal-app-lokal\`** ist der Stand vom 22.07.2026 — historisch, nicht verwenden.
