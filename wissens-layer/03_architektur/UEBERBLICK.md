# Architektur-Überblick

> Zusammenfassung. Maßgeblich für die Grundsatzentscheidungen und die vollständige
> Datenquellen-Matrix bleibt `docs\ARCHITEKTUR.md`. Stand: 26.09.2026.

## Die Grundentscheidung

Ein öffentliches GitHub-Repository mit drei Bausteinen, komplett kostenlos:
die Signal-Engine (Python, per GitHub Actions), die Chart-Webseite (GitHub Pages)
und der Telegram-Bot. Kein Server, kein Hosting-Vertrag, keine laufenden Kosten.

## Ordnerkarte

```
(Stand vor dem 26.09.2026 - seit dem Umzug liegen docs\, wissens-layer\, STARTPROMPT.md
 und PRUEFPROMPT.md IM Repo btc-signal-app; die Kopien unter BTC-Trading\ sind veraltet.
 Siehe START-HIER.md, Abschnitt "Wo alles liegt".)
BTC-Trading\                      Repo "260729-btc-trading-backup" (privat)
  00_STAND.md                     -> liegt in wissens-layer\, nicht hier
  STARTPROMPT.md                  fertiger Übergabe-Prompt für einen neuen Chat
  PRUEFPROMPT.md                  Prompt für einen reinen Prüfdurchlauf
  wissens-layer\                  dieser Ordner
  docs\                           Strategie, Chronik, Analysen, Baupläne (PLAN-E*.md)
  Transkript.md                   Abschrift des Furkan-Videos
  Kauftrigger.md / Verkaufstrigger.md   Kaisers notierte Termine (Rohdaten)
  heatmap-test\                   gesammelte Screenshots
  Videos\                         weitere Transkripte (u. a. 260913)
  HOCHLADEN.cmd                   Doppelklick: Code hochladen + sichern
  BACKUP.cmd                      wird von HOCHLADEN.cmd aufgerufen
  stand-holen.bat                 holt den GitHub-Stand zurück auf den Rechner
  signal-app\                     Repo "btc-signal-app" (OEFFENTLICH)
    engine\                       der gesamte Python-Code
    site\                         die Webseite (index.html + data\)
    .github\workflows\            die sieben Automatik-Läufe
    BACKTEST.md                   erzeugter Bericht - NIE von Hand ändern
    ANLEITUNG-*.md                Einrichtungsanleitungen
```

## Der Code (Stand 26.09.2026)

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `engine\strategy_core.py` | 2.112 | Das Herz: Pivots, Impulse, Fib-Zonen, Order-Flow-Kompass, Muster, Ampel, Zustandsmaschine, alle Schalter. Enthält `evaluate()` und die Stop-Entscheidung `stop_entscheidung()` (E41) |
| `engine\backtest.py` | 2.866 | Das Gitter aus 67 Varianten, Kennzahlen, Fensterhalbierung, Bericht `BACKTEST.md`, die Sonderabschnitte E38.1/E39/E40.1/E41 |
| `engine\main.py` | 1.059 | Der Live-Lauf: Daten holen, `evaluate()` aufrufen, Zustand fortschreiben, Telegram. Dazu Flush-Wache, Lage-Abruf und die STH-Abrufe (die auch der Backtest benutzt) |
| `engine\telegram_notify.py` | 557 | Nachrichtenformate (Signal, Vorschau, Plan, Flush-Warnung, Lage-Abruf, Stop wartet / Marke zurückerobert) |
| `engine\coinalyze.py` | 1.047 | Order-Flow-Daten (Open Interest, Liquidationen, Futures-CVD, Long-Short) |
| Tests | 7.078 in fünf Dateien | **447 Tests**, alle müssen grün sein |
| `engine\sabotage_e*.py` | 924 in sechs Dateien | Sabotage-Proben: verfälschen den Code Zeile für Zeile und prüfen, dass Tests rot werden. Zusammen 158 Sabotagen |

**Eine Abhängigkeit, die man kennen muss:** `backtest.py` importiert aus `main.py`
(`_get_json`, `fetch_funding_8h`, die STH-Abrufe). Der Grund ist Absicht — zwei
Abschriften derselben Abruf-Funktion wären irgendwann auseinandergelaufen. `main.py`
importiert **nicht** aus `backtest.py`, und der Live-Teil von `main.py` steht hinter
`if __name__ == "__main__"`, damit der Import nichts auslöst.

## Die sieben Automatik-Läufe

| Workflow | Auslöser | Was er tut |
|---|---|---|
| **Signal-Engine** (`signal.yml`) | cron-job.org sechsmal täglich (0/4/8/12/16/20 UTC + 2 Min) **und** GitHub-Cron als Netz **und** von Hand | Der Live-Lauf. Schreibt `state.json`/`signals.json` ins Repo, sendet Telegram |
| **Flush-Wache** (`watch.yml`) | GitHub-Cron alle 15 Min | Meldet, wenn sich in der laufenden 4h-Kerze ein Flush entwickelt. Fasst `state.json` nicht an |
| **Lage-Abruf** (`lage.yml`) | nur von Hand | Die Lage auf Knopfdruck unter der Annahme einer Long-Position (E35/E36), inkl. Order-Flow-Rohwerten und STH-Kostenbasis. Ändert nichts |
| **Backtest** (`backtest.yml`) | nur von Hand | Rechnet das Gitter (rund 6 Minuten), schreibt `BACKTEST.md`, `site\BACKTEST.md` und die JSON-Dateien |
| **Chart-Webseite** (`pages.yml`) | Push nach `site\**`, **oder** nach erfolgreichem Signal-/Backtest-Lauf | Veröffentlicht den Ordner `site\` |
| **Tests** (`tests.yml`) | Push | Hält die 447 Tests grün |
| **Coinalyze-Test** (`coinalyze-test.yml`) | nur von Hand | Klopft die Datenendpunkte ab |

**Wichtig zu Pages:** GitHub löst bei einem Push, den ein Workflow selbst macht,
keine weiteren Workflows aus. Deshalb hat die Webseite acht Tage lang veraltete
Zahlen gezeigt, obwohl der Backtest lief. Der `workflow_run`-Auslöser in `pages.yml`
schließt diese Lücke seit 05.09.2026.

**Wichtig zum Anstoß:** Der GitHub-Zeitplan lief in der Praxis 1–3 Stunden zu spät —
gemessen am 17.09.2026. Seither stößt cron-job.org `signal.yml` per API pünktlich an
(Fine-grained Token `engine-anstoss`, nur dieses Repo, `Actions: Read and write`, ein
Jahr gültig). Doppelte Nachrichten kann es nicht geben: die Engine merkt sich die
zuletzt ausgewertete Kerze. Die Flush-Wache hat dasselbe Verzugsproblem und ist
bewusst noch nicht umgestellt.

## Datenquellen (alle kostenlos)

| Daten | Quelle |
|---|---|
| Kerzen + Spot-CVD | Binance Public-Data-Spiegel (`data-api.binance.vision`) — nicht geo-blockiert, ohne Schlüssel |
| Open Interest, Liquidationen, Futures-CVD, Long-Short-Verhältnis | **Coinalyze** (kostenloser Schlüssel als Secret `COINALYZE_API_KEY`, 40 Abrufe/Minute) |
| Funding | Kraken Futures |
| STH-Kostenbasis (Anzeige + E40-Messung) | **bitview.space** (`sth_realized_price/day1`, ab 2009, tagesaktuell, ohne Abrufgrenze) — Ersatz: **bitcoin-data.com** (`/v1/sth-realized-price`, 15 Abrufe/Tag je IP, 7 Tage Verzug) |

Zwei Fallen, die schon Zeit gekostet haben: Die Binance-**Futures**-API sperrt
GitHub-Runner (HTTP 451) — deshalb der Public-Data-Spiegel. Und der Coinalyze-Endpunkt
`buy-sell-volume-history` existiert nicht; diese Daten stecken in der Kerzen-Historie.
Bei bitview.space kommt eine reine Werteliste **ohne Datum** zurück; das Datum wird aus
dem Feld `start` und dem Index gerechnet (Index 0 = 01.01.2009). Wer den Serienname
nicht exakt trifft, bekommt schweigend eine andere Reihe — genau das ist in E40.0
passiert.

Jeder Abruf steckt in einem eigenen Fehler-Block: Fällt eine Quelle aus, läuft die
Engine mit dem Ersatzweg weiter, statt abzubrechen. Die STH-Zeile im Lage-Abruf
entfällt dann einfach.

## Zustand und Datenfluss

`site\data\state.json` ist das Gedächtnis der Engine: offene Position, eingefrorene
Zonen, Zähler, der aktuelle Plan und die Vorschau — und seit E41 die drei Merker der
Rückeroberungs-Regel (`stop_wartet`, `stop_wartet_inv`, `stop_geprueft`). Es wird bei
jedem Lauf neu ins Repo committet.

**Warum das wichtig ist:** Die Engine läuft bei jedem Takt als **neuer Prozess**. Was
nicht in `state.json` steht, existiert im nächsten Lauf nicht mehr. Bei E41 hätte das
bedeutet, dass das Warten jedes Mal neu beginnt und der Stop **nie** kommt — im
Backtest unsichtbar, weil der am Stück rechnet. *Nebenbefund, nicht behoben:*
`widerstand_exits` (E20) wird ebenfalls nicht gespeichert; folgenlos, solange
`widerstand_exit` aus ist.

`signals.json` ist die Signal-Historie — sie wird **fortgeschrieben, nie neu
berechnet**; ein späterer Lauf ändert also keine vergangenen Signale mehr.

`config.json` wird dagegen **nie** von der Engine überschrieben. Deshalb kann Kaiser
sie jederzeit konfliktfrei bearbeiten: 35 Schalter, zu jedem ein Feld `_hinweis_*` mit
Messwerten und Begründung.

## Wo die Live-Einstellung im Backtest steht

Genau **eine** Gitterzeile trägt `panel=True` — sie muss der echten Live-Einstellung
aus `config.json` entsprechen, sonst zeigt die Webseite eine Rendite, die nie erzielt
wurde. Ein Test vergleicht beides bei jedem Lauf. Daneben gehören mitgezogen: die
Zeile „MEINE Einstellung ohne Flush" (Monatsübersicht) und jede Zeile „LIVE-heute + X"
— sonst messen die genau zwei Unterschiede statt einem. Auch das halten Tests fest.
