# BTC Signal-App — Order-Flow-Strategie (nach Furkan Yildirim)

Sendet Kauf-/Verkaufs-Trigger (Long + Short, Tranchen, Stops) per Telegram und zeigt
Charts mit Trigger-Markern als Webseite. Läuft komplett kostenlos auf GitHub
(Actions = Engine alle 15 Min, Pages = Chart-Webseite).

**Kein Auto-Trading:** Die App signalisiert nur — Orders platzierst du selbst.
Keine Gewinngarantie; Krypto ist hochriskant.

## Einrichtung (einmalig, ~10 Minuten)

### 1. Repository anlegen und Code hochladen
1. github.com → oben rechts **+** → **New repository** → Name z. B. `btc-signal-app`,
   Sichtbarkeit **Public** (wichtig: unbegrenzte Actions-Minuten) → **Create repository**.
2. Auf der leeren Repo-Seite: Link **uploading an existing file** anklicken.
3. Den kompletten **Inhalt** des Ordners `signal-app` (Ordner `engine`, `site`, `.github`,
   Datei `README.md`, `.gitignore`) ins Browserfenster ziehen → **Commit changes**.
   Falls der Ordner `.github` beim Ziehen nicht mitkommt (versteckte Ordner):
   im Explorer „Ausgeblendete Elemente" einblenden und erneut ziehen.

### 2. Chart-Webseite aktivieren
1. Repo → **Settings** → **Pages** → Source: **GitHub Actions**.
2. Repo → **Actions** → ggf. „I understand my workflows, enable them".
3. Workflow **Chart-Webseite (Pages)** → **Run workflow**.
4. Danach ist die Seite erreichbar unter `https://DEIN-NAME.github.io/btc-signal-app/`
   (Link steht auch in Settings → Pages). Auf dem Handy: Link öffnen → „Zum
   Startbildschirm hinzufügen".

### 3. Telegram-Bot anlegen
1. In Telegram **@BotFather** öffnen → `/newbot` → Namen vergeben →
   den **Token** kopieren (Format `123456:ABC-…`).
2. Deinem neuen Bot eine beliebige Nachricht schreiben (z. B. „Start").
3. Im Browser öffnen: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   (`<TOKEN>` ersetzen) → im Text steht `"chat":{"id":123456789` → diese Zahl ist
   deine **Chat-ID**.
4. Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository
   secret**: einmal `TELEGRAM_BOT_TOKEN` (der Token), einmal `TELEGRAM_CHAT_ID` (die Zahl).

### 4. Testen
1. **Actions** → **Tests** → sollte grün sein (läuft bei jedem Upload automatisch).
2. **Actions** → **Signal-Engine** → **Run workflow** → Haken bei
   „Nur Telegram-Testnachricht senden" → du bekommst eine Testnachricht aufs Handy.
3. **Run workflow** noch einmal **ohne** Haken → echter Engine-Lauf; danach zeigt die
   Webseite unten „Engine-Stand" mit aktueller Zeit.

Ab jetzt läuft alles automatisch (alle 15 Min). Fertig.

## Signale

| Code | Bedeutung | Tranche |
|---|---|---|
| K1 / S1 | Einstieg am 0.5-Retracement | 25 % |
| K2 / S2 | Kernposition im Golden Pocket (0.618–0.65) | 50 % |
| NK / SNK | Nachkauf an der 0.786-Zone | 25 % |
| TV1 / STP1 | Teilgewinn am Extension-1.0-Ziel | 40 % |
| TV2 / STP2 | Teilgewinn am Extension-1.618-Ziel | 40 % |
| V / SC | Rest schließen (Gegen-Muster am Ziel) | Rest |
| SL / SSL | Stoploss (Kerzenschluss hinter Invalidierung) | 100 % |
| W | Warnung: Derivate-Pump aktiv | — |

## Weiterführende Anleitungen

- [ANLEITUNG-EINSTELLUNGEN.md](ANLEITUNG-EINSTELLUNGEN.md) — Long/Short schalten,
  Takt ändern, Backtest starten, Parameter, git-Updates (inkl. bekannter Fehler)
- [ANLEITUNG-TELEGRAM.md](ANLEITUNG-TELEGRAM.md) — Telegram von Null einrichten,
  mit Kontrollpunkten und Fehlerdiagnose-Tabelle

## Technik

- `engine/strategy_core.py` — Strategie-Regeln (Swings, dynamische Fib-Zonen,
  Order-Flow-Kompass, Zustandsmaschine). `engine/run_tests.py` führt alle Tests aus.
- `engine/main.py` — Datenabruf (Binance, ohne API-Key), Auswertung, Telegram.
- `site/` — Chart-Webseite (GitHub Pages).
- Long/Short lassen sich in `site/data/state.json` unter `config` abschalten
  (`bias_long` / `bias_short` auf `false`).
