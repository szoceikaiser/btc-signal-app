# Architektur-Entscheidung (E3)

Stand: 2026-07-22 · Recherche-Basis: GitHub-Doku/Community (Juli 2026), Binance-API-Doku.

## Entscheidung

**Ein öffentliches GitHub-Repository mit drei Bausteinen — komplett kostenlos:**

1. **Signal-Engine** (Python) — läuft per **GitHub Actions Cron alle 15 Minuten**.
   Holt Kurse/OI/Funding von öffentlichen Börsen-APIs (ohne API-Key), berechnet Swings,
   dynamische Fib-Zonen und den Order-Flow-Kompass, führt die Positions-Zustandsmaschine
   und sendet neue Trigger per **Telegram-Bot** (Token als GitHub Secret).
   Zustand (`state.json`, `signals.json`) wird ins Repo committet.
2. **Chart-Webseite** — **GitHub Pages** (statisch, kostenlos, per Handy/PC aufrufbar).
   Kerzencharts 1h/4h/1D/3D/1W/1M (lightweight-charts via CDN), Kerzen client-seitig von
   der Binance-Public-API (Fallback: JSON aus dem Repo), Trigger-Marker + Fib-Zonen +
   CVD/OI/Funding-Panels aus `signals.json`/`state.json`.
3. **Telegram-Bot** — einmalige Einrichtung durch Kaiser (BotFather, 2 Minuten, Anleitung
   folgt in E7). Nachrichtenformate je Trigger-Typ gemäß STRATEGIE.md §6.

## Warum GitHub (und nicht …)?

| Option | Bewertung |
|---|---|
| **GitHub Actions + Pages** ✅ | Kaiser hat Konto; public Repo = unbegrenzte Actions-Minuten; Pages kostenlos; alles an einem Ort; kein Server zu pflegen. |
| GitHub Pages allein | Kann keinen Server-Code ausführen — nur als Frontend nutzbar (so machen wir es). |
| Cloudflare Workers (free) | Zuverlässiger Cron, aber zusätzliches Konto, JS-only, CPU-Limits — unnötige Komplexität. |
| Render/Railway/Fly free | Free-Tiers wurden mehrfach eingeschränkt (Spin-down, Kreditmodelle) — nicht verlässlich dauerhaft kostenlos. |
| Oracle Cloud Free | Dauerhaft kostenlose VM, aber Konto-/Wartungsaufwand; Overkill für 1 Cron-Job. Fallback-Option, falls GitHub je nicht reicht. |
| Lokaler Rechner | Ausgeschlossen: müsste 24/7 laufen; Anforderung war Server-Betrieb. |

## Recherche-Fakten, auf denen die Entscheidung beruht

- Actions-Cron: Minimum 5 Min; **Verzögerungen von 5–30 Min sind normal**, zu Stoßzeiten
  auch länger. Konsequenz: Engine wertet **abgeschlossene** 4h-/1D-Kerzen aus und ist
  idempotent (Deduplizierung über Kerzen-Timestamp) — Verzögerungen sind dann harmlos.
- Public Repos: Actions-Minuten unbegrenzt (Standard-Runner). Private Repos: 2.000 Min/Monat
  — bei 15-Min-Takt zu knapp → **Repo public** (enthält keine Geheimnisse; Telegram-Token
  liegt in GitHub Secrets, nie im Code).
- Scheduled Workflows werden nach **60 Tagen ohne Commits** deaktiviert. Unsere Engine
  committet bei jeder Zustandsänderung ohnehin; zusätzlich Keepalive-Workflow (monatlicher
  Auto-Commit) als Sicherheitsnetz.
- Binance bietet Public-Market-Data-Endpoints ohne Key (`data-api.binance.vision`, u. a.
  `/api/v3/klines`); Futures-Klines enthalten Taker-Buy-Volumen → **CVD selbst berechenbar**
  (Spot und Futures getrennt, über Binance/Bybit/OKX aggregierbar).
- Chart-Seite: primär client-seitiger Kerzen-Abruf; falls CORS einer Börse klemmt, liefert
  das Repo committete Kerzen-JSONs als Fallback (in E6 wird der primäre Weg getestet).

## Datenquellen-Matrix (alle ohne API-Key)

### Datenquellen-Matrix — STAND 28.07.2026 (gültig)

| Datum | Quelle | Hinweis |
|---|---|---|
| Kerzen + Spot-CVD | Binance Public-Data-Spiegel (data-api.binance.vision) | inkl. Taker-Buy-Volumen → CVD; **nicht** geo-blockiert; ohne Key |
| Open Interest | **Coinalyze** `open-interest-history` | aggregiert über Börsen, mit Historie. Kraken-Snapshot nur noch als Rückfall, wenn Coinalyze ausfällt |
| Funding | Kraken Futures, stündliche Historie ×8 (8h-Äquivalent) | Coinalyze hätte es auch (`funding-rate-history`), Kraken funktioniert und bleibt |
| Liquidationen | **Coinalyze** `liquidation-history` | echte Beträge je 4h-Kerze (long/short getrennt), kein Proxy mehr |
| **Futures-CVD** | **Coinalyze** `ohlcv-history` (E16, 28.07.2026) | Felder `v` (Volumen) und `bv` (davon Käufe) → Delta = 2·bv − v. **Schließt die letzte offene Datenlücke.** Einheit: Basiswert (BTC), nicht USD — für `classify_pattern` unerheblich, weil dort nur relative Änderungen eingehen |
| **Long-Short-Verhältnis** | **Coinalyze** `long-short-ratio-history` (E16) | Anteile in Prozent; wird erfasst, aber von keiner Regel benutzt |

Zugang: **ein kostenloser Coinalyze-Key** als GitHub-Secret `COINALYZE_API_KEY`,
40 Abrufe/Minute. Jeder Abruf steckt in einem eigenen Fehler-Block — fällt eine Quelle
aus, läuft die Engine mit dem bisherigen Ersatzweg weiter statt abzubrechen.
Der Endpunkt `buy-sell-volume-history` existiert NICHT (404); die Daten stecken in der
Kerzen-Historie. Der Workflow „Coinalyze-Test" klopft die Endpunkte jederzeit neu ab.

### Frühere Fassung (überholt, nur zur Einordnung)

| Datum | Quelle(n) | Hinweis |
|---|---|---|
| Open Interest | Kraken Futures (PF_XBTUSD), Snapshot je Lauf | Engine baute eigene Historie auf; erste ~2 Tage OI-Muster neutral |
| Liquidations | V1: Proxy (scharfer OI-Abfall + Range-Spike) | ersetzt durch echte Coinalyze-Daten |
| Futures-CVD | **gab es nicht** | fapi.binance.com sperrt US-Runner (HTTP 451); der Zweig `if has_fut:` in `classify_pattern` war bis E16 toter Code, Muster 2 lief über Ersatzmerkmale |

**KORREKTUR (2026-07-24, Kaiser hatte recht):** Die frühere Aussage „Open Interest hat für
den Zeitraum keine kostenlose Historie" ist FALSCH. **Coinalyze** (coinalyze.net, api.coinalyze.net)
liefert per kostenloser API (kostenloser Key, 40 Abrufe/Min) **historisches OI + Funding +
echte Liquidationen**, aggregiert über Börsen — 4h reicht mehrere Monate zurück, Tageswerte
unbegrenzt. Furkan bestätigt im Video zudem kostenlose Liquidations-Tools (Velo komplett
kostenlos; Coinank als Heatmap-Alternative; Hyblock zahlt er nur, weil „besser"). GEPLANT
(E8.3 vorgezogen): Coinalyze als OI-/Liquidations-Quelle anbinden (ersetzt Kraken-OI-Snapshot
+ Liquidations-Proxy), dann Muster 2/3/4 mit echten Daten + bedingter Stop/Nachkauf.
Erreichbarkeit von GitHub-US-Runnern auf Actions verifizieren (Coinalyze ist kein
US-geoblockter Boersen-Endpoint, aber testen).

**Praxis-Befund (2026-07-22, Erstlauf):** `fapi.binance.com` (Binance Futures) blockiert
GitHub-Runner-IPs (USA) mit **HTTP 451** — daher der Quellen-Mix oben. Preisbasis ist
Spot statt Perp (Differenz minimal, dokumentierte Abweichung). Futures-CVD hat ohne
Binance-Futures keine kostenlose Quelle → Kompass-Muster 2 (Derivate-Pump) wird über
OI ↑ + Funding zieht an + Spot-CVD flach erkannt (deckt Furkans Merkmale ab).
Die Chart-Webseite ist nicht betroffen (Browser-Abruf läuft über Kaisers IP).

## Risiken & Gegenmaßnahmen

- Actions-Ausfall/Verzögerung → 4h-Takt der Strategie verträgt Stunden Verspätung;
  Engine holt verpasste Kerzen nach (idempotent).
- Börsen-API-Änderung → Aggregation über 3 Börsen; fällt eine aus, rechnen die anderen.
- GitHub-Policy-Änderung → Architektur ist portabel (ein Python-Skript + statisches
  Frontend); Umzug auf Oracle Free/Cloudflare jederzeit möglich.

## Konsequenz für den Etappenplan

E4 wird geteilt (jede Etappe einzeln grün lieferbar):
- **E4a — Kern-Engine offline**: Swing-Erkennung, dynamische Fib-Zonen, Kompass-Muster,
  Zustandsmaschine + Unit-Tests mit synthetischen Daten (läuft ohne Netz).
- **E4b — Daten-Layer + Backtest**: Fetcher/Aggregation, Backtest Sep'25–Apr'26,
  Kalibrierung gegen Kaisers Trigger (Ziel ≥70 % Reproduktion ±1 Tag; Doppel-Einträge
  laut Kaiser evtl. Versehen → tolerant werten).
