# Etappenplan E9: Echte Order-Flow-Daten (Coinalyze) + intelligentes Dip-/Stop-Management

Stand: 2026-07-24 · Status: **GEPLANT, Umsetzung beginnt** · Repo-getrackt (auch in Cowork verfügbar)

## Warum (die Erkenntnisse aus der Diskussion mit Kaiser)

Die bisherigen Einstiegs-Filter (E8.5) brachten nichts, weil die Engine **blind** war:
kein echtes Open Interest, keine Liquidationen, kein Futures-CVD. Kaiser hatte recht:
1. **Historisches OI gibt es kostenlos** — Coinalyze (frühere Doku-Aussage „keine kostenlose
   OI-Historie" war falsch, in ARCHITEKTUR.md korrigiert).
2. **Kostenlose Liquidations-Tools** bestätigt Furkan im Video (Velo kostenlos, Coinank als
   Heatmap-Alternative; Hyblock zahlt er nur, weil „besser").
3. **„Wann kippt der Dip?"** kann nur beantwortet werden, wenn die Werkzeuge echte Daten
   sehen (OI-Wipeout+Long-Liquidationen = guter Dip; OI↑+Funding heiß = Dip kippt).
4. **Stop-Loss nicht pauschal:** Furkan kauft bei Verlust NACH, wenn der Order-Flow weiter
   für Aufwärtstrend spricht; nur stoppen, wenn die Struktur bricht UND der Flow kippt.

Diese Punkte laufen alle auf **eine** Sache zu: echte Order-Flow-Daten anschließen. Das ist
der größte offene Hebel. E8.3 (auf 2 Wochen Eigen-OI-Historie warten) entfällt — Coinalyze
liefert die Historie mit.

## Datenquelle: Coinalyze (Fakten)

- Basis-URL: `https://api.coinalyze.net/v1`
- Endpoints: `/open-interest-history`, `/funding-rate-history`, `/liquidation-history`
  (+ `/ohlcv-history`, `/future-markets`, aktuelle Werte). Params: `symbols`, `interval`
  (z. B. `4hour`/`H4`), `from`, `to` (Unix-Sekunden), `convert_to_usd`.
- **Kostenlos**, Key nötig (Header `api_key` oder Query). Rate-Limit 40 Abrufe/Min.
- Reichweite: intraday (1min–12h) ~1500–2000 Datenpunkte (4h ≈ mehrere Monate zurück,
  deckt Backtest ab 4h teils / daily voll), **daily unbegrenzt**.
- Aggregiert über die großen Börsen (nicht nur eine) — passt zu Furkans Aggregations-Prinzip.
- Erreichbarkeit von GitHub-US-Runnern (Actions) noch auf Actions zu VERIFIZIEREN (Coinalyze
  ist kein US-geoblockter Boersen-Endpoint wie Binance-Futures, aber testen).
- Offen/Stretch: Futures-CVD (Taker-Buy/Sell je Börse) — ob Coinalyze das liefert, beim Bau
  prüfen; OI+Funding+Liquidationen ist der bestätigte Kern.

## Etappen (jede einzeln lieferbar, Tests grün, per Backtest gemessen)

### E9.1 — Coinalyze-Daten-Layer · Status: OFFEN
- Kaiser holt kostenlosen Coinalyze-API-Key → GitHub-Secret `COINALYZE_API_KEY`
  (Anleitung: signal-app/ANLEITUNG-COINALYZE.md, mit Kontrollpunkten).
- `engine/coinalyze.py` (stdlib/urllib): Fetcher für OI-History, Funding-History,
  Liquidation-History; Transport injizierbar (Fake für Offline-Tests).
- `main.py`: Coinalyze als OI-/Funding-/Liquidations-Quelle einbinden (ersetzt
  Kraken-OI-Snapshot + Liquidations-Proxy; Kraken als Fallback behalten). FlowPoint
  ggf. um echte Liquidationen erweitern (long_liq/short_liq) — abwärtskompatibel.
- `backtest.py`: echtes historisches OI/Liquidationen in `build_series` einspeisen
  (statt OI konstant) → Muster 4 wird im Backtest aktiv.
- Offline-Tests (Fake-Fetch). Reachability auf Actions verifizieren (Testlauf).

### E9.2 — Muster 2/3/4 mit echten Daten schärfen + Retest · Status: OFFEN
- `classify_pattern` mit echtem OI + Liquidationen (statt Proxy): oi_wipeout, Liq-Cluster.
- Backtest neu mit echtem OI: E8.1/E8.1b-Retest — greift `flush_entry` (Capitulation-
  Einstieg) jetzt, wo Muster 4 aktiv ist? (War „off", WEIL OI fehlte.)
- Ziel: bessere Dip-Auswahl (welcher Dip hält). Schaltbar, per Rendite+Recall gemessen.

### E9.3 — Bedingter Stop / Nachkauf-Leiter statt pauschalem Stop · Status: OFFEN
- Furkans Kern (Kaiser): bei Verlust nachkaufen, wenn Order-Flow weiter bullisch; nur
  stoppen, wenn Struktur bricht UND Flow kippt.
- Neue Stop-Logik (schaltbar `conditional_stop`, Default aus bis gemessen): Schluss unter
  Invalidierung → NICHT sofort raus, sondern prüfen, ob Aufwärts-Kriterien halten
  (Spot-CVD hält, OI-Reset/Muster 4, Funding neutral/negativ, keine Long-Liq-Kaskade).
  Wenn ja → tiefere Nachkauf-Tranche (Leiter in die Schwäche), Invalidierung ggf. nachziehen.
  Wenn nein → Stop. Deckt zugleich Furkans Mehrtages-Kaufleitern (27.-30.10., 17.-21.11.,
  29.-31.01.) ab → mehr seiner Einstiege getroffen.
- Backtest: Rendite + Recall (ehrlich getrennt; Gefahr: mehr Nachkäufe = mehr Risiko,
  daher zwingend an echte Order-Flow-Bestätigung gekoppelt, nicht blind).

### E9.4 — Liquidationen sichtbar für Kaiser · Status: OFFEN
- Chart-Seite: Liquidations-Daten/-Cluster anzeigen; Link/Einbindung einer kostenlosen
  Heatmap (Velo/Coinank/Coinglass). Optional Liquidations-Zonen als „Magnete" im Chart.

## Regeln / Ehrlichkeit (Regel 3)
- Kein Gewinnversprechen. Jede Etappe schaltbar, Default = altes Verhalten, bis per Backtest
  gemessen. Recall (Ähnlichkeit zu Furkan) immer klar vom Gewinn (Rendite) trennen.
- Mehr Nachkäufe/weniger Stops erhöhen das Risiko — nur zulassen, wenn echte Order-Flow-
  Daten den Aufwärtstrend bestätigen (das ist der ganze Sinn von E9.1 zuerst).
- Kaiser ist kein Entwickler: für jeden Key/jede Einstellung eine ANLEITUNG mit
  Kontrollpunkten; Befehle als fertige Blöcke; nach jedem Schritt Rückmeldung.

## Reihenfolge / Abhängigkeiten
E9.1 (Daten) ist die Basis für alles. E9.2 und E9.4 bauen auf E9.1. E9.3 braucht E9.2
(„ist der Aufwärtstrend noch intakt?"-Signal). Start: E9.1 — zuerst die Key-Anleitung für
Kaiser (kritischer Pfad), parallel der offline-testbare Fetcher.
