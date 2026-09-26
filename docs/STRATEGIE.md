# Strategie-Spezifikation: Furkan Yildirims Order-Flow-Strategie (BTC)

Quelle: Video „Order Flow Trading Indikatoren der Bitcoin Krypto Profis erklärt" (~25 Min)
+ Transkript mit Zeitstempeln + geprüfte Video-Frames.
Stand: 2026-07-22 · Etappe E1 · Alle Regeln aus Video-Notizen (blankslate-Dokument, im Video
eingeblendet) wörtlich übernommen und mit Chart-Frames abgeglichen.

---

## 1. Plattformen und Datenquellen (im Video verifiziert)

| Zweck | Plattform im Video | Frame-Beleg |
|---|---|---|
| Order-Flow-Daten (CVD, OI, Funding, Liquidations) | **Velo (velo.xyz/chart)**, kostenlos, BTCUSDT Binance-Futures | 20:45–23:59 |
| Fib-Retracement / Extensions | **TradingView**, BTCUSDT.P (Binance Perpetual), 4h | 16:40–18:55 |
| Ausführung seiner Trades | **Pionex**, BTC/USDT USDT-M Perp (B/S-Marker auf Tageschart) | 18:25 |
| Liquidation-Heatmap | Hyblock (bezahlt); kostenlose Alternativen: Velo, Coinank | 4:24–4:47 |

**Aggregation (wichtig, nicht nur eine Börse):**
- Spot-CVD: Binance, Coinbase, Bybit, OKX (22:02)
- Futures-CVD: Perps von Binance, Bybit, OKX, Deribit, Hyperliquid (+ USD(T)-Perps) (22:10)
- Funding: Binance USDT Perp, Bybit USDT Perp, OKX USDT Swap, Deribit USD Perp,
  Hyperliquid USD Perp — **skaliert auf 8 Stunden, View: Average**, Rate in %, OI-gewichtet (22:48–23:59, Frame 23:50)
- Alle Werte in **Dollar**, nicht Coins (20:56)
- CVD = kumuliertes Delta (Market-Käufe − Market-Verkäufe), als Linie (20:47)
- OI: aggregiert, Dollar, als Candles dargestellt (22:31)

## 2. Die 4 Kern-Indikatoren und ihre Regeln (wörtlich aus seinen Notizen)

### 2.1 CVD (Cumulative Volume Delta)
Kumulierte Market-Käufe minus Market-Verkäufe.
- Spot-CVD (grau): echte Nachfrage/Angebot ohne Hebel → „qualitativer" Flow
- Futures-CVD (orange): gehebelter Flow, oft taktisch/kurzfristig → Squeeze-Anfälligkeit

| Beobachtung | Bedeutung |
|---|---|
| Spot-CVD ↑ + Preis ↑ | gesund, Nachfrage trägt |
| Futures-CVD ↑ + Spot-CVD flach/↓ | Derivate treiben; anfällig für Long-Flush |
| Spot-/Preis-Divergenz | Vorsicht: Umkehr / Mean Reversion |

### 2.2 Open Interest (OI)
Offene Futures-Kontrakte (Long = Short).

| Beobachtung | Bedeutung |
|---|---|
| Preis ↑ + OI ↑ | neues Geld kommt rein; Trend kann tragen |
| Preis ↑ + OI ↓ | Short-Covering-Rally „ohne Neu-Geld" |
| Preis ↓ + OI ↓ | Long-Flush/Wipeout; nach Reset oft bessere Basis |

### 2.3 Funding
Long↔Short-Ausgleich im Perp-Markt (Differenz Futures-/Spotpreis).

| Beobachtung | Bedeutung |
|---|---|
| steigend/positiv und schnell | Long-Überhang, Squeeze-Risiko |
| neutral/leicht | „sauberer" Markt, Raum für nachhaltige Trends |
| negativ | Spot > Future; oft gut für Erholung (10:57: Funding negativ vor Gegenbewegung) |

### 2.4 Liquidations
Zwangsschließungen gehebelter Positionen.

| Beobachtung | Bedeutung |
|---|---|
| Cluster an Tiefs/Hochs | Bewegung von Zwang getrieben; danach oft Snapback |
| keine Liquidations trotz großer Bewegung | Flow eher „organisch" (Spot/Positionierung) |

## 3. Der „Order-Flow-Kompass": 4 Muster (wörtlich, Frame 14:50)

1. **Gesunder Trend-Anstieg**: Spot-CVD ↑, Futures-CVD ↑ (nicht überzogen), OI ↑ moderat,
   Funding neutral → nachhaltig.
2. **Derivate-getriebener Pump**: Futures-CVD ↑ stark, Spot-CVD flach/↓, OI ↑ deutlich,
   Funding zieht an → anfällig für Long-Flush.
3. **Short-Covering-Rally**: Preis ↑, OI ↓, Liquidations (Shorts) ↑, Funding bleibt gedämpft
   → Snapback möglich, Nachhaltigkeit fraglich.
4. **Capitulation/Flush + Reset**: Preis ↓ scharf, OI ↓ (Wipeout), Liquidations (Longs) ↑,
   danach Spot-CVD dreht ↑ → gute Basis für Erholung.

Alle Muster gelten spiegelbildlich für Short (13:28: „umgekehrt natürlich dann auch nach unten").

### 3.1 Muster 5 „Ungesunder Abverkauf" — EIGENE ERGÄNZUNG, nicht von Furkan (E13, 07/2026)

Furkans vier Muster beschreiben **drei steigende Märkte und genau einen fallenden** — die
Kapitulation, also den *gesunden* Absturz. Für einen ungesunden Absturz gab es keinen
Begriff; er landete auf NEUTRAL und war damit von einem ruhigen Seitwärtsmarkt nicht zu
unterscheiden. Genau in dieser Lage hat die Engine gekauft (16 von 34 Ersteinstiegen).

Muster 5 = Spiegelbild von Muster 4, alle vier Merkmale gleichzeitig:
Preis fällt · Spot-CVD fällt mit (der Dip wird nicht gekauft) · OI hält oder steigt (die
gehebelten Longs sind noch drin) · Funding weiter positiv · **keine** Long-Liquidations-
Kaskade (die Zwangsverkäufe stehen noch bevor).

**Gemessen und für schwach befunden:** Als Einstiegssperre (`block_unhealthy`) hat es in
neun Monaten 3 von 212 Signalen verhindert und 2,2 Punkte Rendite gekostet. Bleibt
ausgeschaltet im Code. Wahrscheinliche Ursache: Die Bedingung `Funding > 0` ist beim
Abverkauf im Bärenmarkt meist schon gedreht. **Bewusst NICHT nachjustiert** — eine
Schwelle so lange lockern, bis die Vergangenheit passt, ist Überanpassung.

## 4. Chart-Werkzeuge: Fib-Retracement + Extensions

**Verwendete Levels (Frame 17:55):** 0.382 · 0.5 · 0.618 · 0.65 · 0.786

- **Golden Pocket = 0.618–0.65** — wichtigster Trendwende-Bereich (17:28)
- **0.5-Level**: dort „erste Order platzieren" — erste Teilposition (17:39)
- 0.786: tiefere Auffangzone; darunter Invalidierung der Struktur
- **Extensions als Kursziele: 1.0 („eins-zu-eins", gleiche Bewegung noch einmal) und 1.618**
  (18:25–19:02; Frame 18:55: 1.0-Ziel bei 97.932 nach Impuls). Spikes bis 1.618 möglich.

**Konstruktion im Video:** Auf dem 4h-Chart von einem markanten Swing-Tief zum Swing-Hoch
gezogen (bzw. Hoch→Tief für Short). Beispiel Frame 17:55: Hoch 94.764,8 → Tief 86.348,7,
Golden Pocket 89.563,6–89.294,3 — Preis drehte exakt dort (08.01.2026).

### 4.1 Dynamische Golden Pockets (KRITISCH — Fehler früherer Umsetzungen)
Die Levels sind NIE starr. Sie beziehen sich auf das jeweils **letzte relevante Hoch/Tief**
und verschieben sich mit jeder neuen bestätigten Swing-Struktur. Algorithmische Umsetzung:

1. **Swing-Erkennung** auf 4h (primär) und 1D (übergeordnete Struktur):
   Pivot-Hoch/Tief = Extremum mit N Kerzen Bestätigung links/rechts (Start: N=5 auf 4h).
2. **Signifikanz-Filter**: Ein Impuls (Pivot→Pivot) zählt nur, wenn seine Spanne
   ≥ k · ATR(14) des Timeframes (Start: k=3) oder ≥ 3 % ist — sonst Rauschen.
3. **Referenz-Impuls** = der jüngste signifikante, abgeschlossene Impuls in Trendrichtung.
   Neues bestätigtes Swing-Hoch/Tief ⇒ Fib-Raster sofort neu berechnen (Pockets „wandern").
4. **Zeitabschnitt intelligent**: Kein fixes Lookback-Fenster. Das Fenster ergibt sich aus
   der Swing-Struktur selbst (letzter signifikanter Impuls). Auf 1D zusätzlich das größere
   Bild für übergeordnete Pockets (beide Ebenen überwachen; Konfluenz 4h+1D = stärkste Zone).
5. Parameter N und k werden in E4 per Backtest gegen Kaisers Trigger-Daten kalibriert.

## 5. Entscheidungsprozess (Hierarchie, 16:03–19:41)

1. **Übergeordneter Bias (Makro)**: Makrokorrelation, US-Aktienmarkt, Renditen → eher Long
   oder eher Short. (App-Umsetzung: einfacher Trendfilter, z. B. Preis vs. EMA200 auf 1D +
   optional manueller Bias-Schalter in der Web-UI; kein Makro-Feed verfügbar.)
2. **Liquidationszonen** = Magnete im Chart eintragen (wo liegt der „größte Schmerz").
3. **Order-Flow-Daten** (Kompass-Muster aus Abschnitt 3) zur Nachhaltigkeits-Beurteilung.
4. **Fib-Zonen** (Golden Pocket + Extensions) als konkrete Einstiegs-/Ausstiegszonen.

## 6. Abgeleitete Trigger-Logik für die App

### 6.1 LONG-Setup
Voraussetzung (Kontext): Bias nicht bärisch; kein aktives Muster 2 (Derivate-Pump).

| Trigger | Bedingung | Aktion / Telegram |
|---|---|---|
| **KAUF 1 (klein)** | Preis berührt 0.5-Retracement des Referenz-Impulses aufwärts | „Erste Teilposition" (~25 %) |
| **KAUF 2 (Kern)** | Preis im Golden Pocket 0.618–0.65 UND ≥1 Bestätigung: Spot-CVD dreht ↑ / Funding ≤ neutral / Muster 4 aktiv (Long-Liq-Cluster + OI-Reset) | Kernposition (~50 %) |
| **NACHKAUF** | Spike auf 0.786, Struktur intakt (kein 4h-Schluss darunter), Spot-CVD hält | Rest (~25 %) |
| **WARNUNG** | Muster 2 erkannt während Position offen | „Anfällig für Long-Flush" |
| **TEILVERKAUF 1** | Extension 1.0 erreicht | ~40 % Gewinnmitnahme |
| **TEILVERKAUF 2** | Extension 1.618 erreicht | weitere ~40 % |
| **VERKAUF (Rest)** | Muster 2/3 am Hoch oder Spot-/Preis-Divergenz | Rest schließen |
| **STOPLOSS** | 4h-Schluss unter 0.786 (aggressiv) bzw. unter Swing-Tief 1.0 (konservativ, Default) | Position schließen |

### 6.2 SHORT-Setup (spiegelbildlich)
Referenz-Impuls abwärts; Einstieg bei Retracement 0.5 → Golden Pocket 0.618–0.65 nach oben;
Bestätigung: Spot-CVD dreht ↓ / Funding hoch+schnell steigend (Long-Überhang) / Muster 2 am
Hoch. Ziele: Extension 1.0, dann 1.618 nach unten. Stop: 4h-Schluss über 0.786/Swing-Hoch.

### 6.3 Positionsführung
Nie all-in / all-out (17:45, 18:00): Aufbau in Tranchen (25/50/25), Abbau in Tranchen
(40/40/Rest). Jedes Signal nennt Tranchen-Größe, Zone, Stop-Referenz und Begründung
(welches Muster/Level).

## 7. Umsetzungshinweise für die App (Vorgriff auf E3/E4)

- Kerzen + Taker-Buy-Volumen (→ CVD selbst berechnen): öffentliche REST-APIs von Binance
  (Spot + Futures), Bybit, OKX, Coinbase — kostenlos, ohne Key.
  CVD pro Kerze = Taker-Buy − Taker-Sell, kumuliert; Spot und Futures getrennt aggregieren.
- OI: öffentliche Endpoints Binance/Bybit/OKX, in USD aggregieren.
- Funding: öffentliche Endpoints, auf 8h skalieren, Durchschnitt (OI-gewichtet wenn möglich).
- Liquidations: beste kostenlose Quelle in E3 recherchieren (Bybit REST, Binance WS,
  Coinank/Coinglass Free). Fallback-Proxy: scharfer OI-Abfall + Preis-Spike = Flush-Ereignis
  (deckt Muster 3/4 ab, ohne exakte Liquidationssummen).
- Auswertung auf 4h-Kerzenschluss (primärer Takt) + 1D-Kontext; Signal-Deduplizierung.

## 7a. NACHTRAG 28.07.2026 — was die Umsetzung inzwischen anders macht

Die Spezifikation oben beschreibt Furkans Methode und bleibt gültig. Die Engine weicht
inzwischen an drei Stellen bewusst ab, jeweils nach Messung:

| Punkt | Furkan | Engine | Grund |
|---|---|---|---|
| Richtung | long **und** short je nach Makro-Bias | **nur long** | Der Makro-Bias (§5 Punkt 1) fehlt uns. Mechanische Shorts ohne ihn: −1 % gegen +41 % |
| Einstiegsauswahl | diskretionär | zusätzlich **Mindestabstand 2 %** zwischen Einstieg und Invalidierung | 15 von 34 Positionen lagen darunter, eine bei 0,02 % — solche Stops löst das Rauschen aus. Sein eigenes Video-Beispiel: 3,59 % |
| Order-Flow beim Einstieg | vier Indikatoren, dann Urteil | nur eine schwache Oder-Prüfung | **Neun** Versuche, daraus feste Regeln zu machen, haben alle Rendite gekostet — auch mit echten Futures-Daten (E16). Order Flow trägt zum Verstehen bei, nicht als Schwellenwert |

**Der wichtigste Befund für die Bewertung dieser Spezifikation:** Furkans Termine, durch
dieselbe P&L-Rechnung geschickt, hätten im Messzeitraum Geld verloren (E15). Die Regeln
oben sind trotzdem die Grundlage von allem, was funktioniert — Golden Pocket, Tranchen,
Extensions, nie all in / nie all out. Was sich als untauglich erwiesen hat, ist die
Ähnlichkeit zu seinen **Terminen** als Zielgröße.

## 8. Offene Punkte / bewusste Annahmen

- Makro-Bias (Punkt 5.1) ist im Video diskretionär; App nutzt Trendfilter + optionalen
  manuellen Schalter. Abweichung dokumentiert.
- Liquidation-Heatmap (Hyblock) ist kostenpflichtig → wir nutzen Liquidations-Daten +
  Fib-/Swing-Zonen als Magnet-Näherung.
- Parameter (N, k, Bestätigungs-Schwellen) sind Startwerte → Kalibrierung in E4 per
  Backtest gegen Kaisers notierte Trigger-Daten (docs/GEGENCHECK.md).
