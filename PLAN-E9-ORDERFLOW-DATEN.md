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

### E9.1 — Coinalyze-Daten-Layer · Status: IN ARBEIT
- ERLEDIGT: Kaiser-Key als Secret `COINALYZE_API_KEY` gesetzt; Test-Workflow
  (.github/workflows/coinalyze-test.yml) am 2026-07-24 GRUEN — **Coinalyze von
  GitHub-US-Runnern erreichbar (kein Geo-Block)**.
- ERLEDIGT: `engine/coinalyze.py` (stdlib/urllib) mit build_url/get_json/fetch_history
  + Parsern oi_by_ts / funding_by_ts / liquidations_by_ts; Transport injizierbar.
  43/43 Tests gruen.
- **BESTAETIGTES ANTWORTFORMAT (2026-07-24):** Liste je Symbol
  `{"symbol","history":[...]}`. Symbol `BTCUSDT_PERP.A` (aggregiert), interval `4hour`,
  Key im Header `api_key`, `convert_to_usd=true`. `t` = Open-Time in Unix-SEKUNDEN.
  open-interest-history & funding-rate-history = OHLC (Close = Wert). liquidation-history
  = `{t, l, s}` mit l=Long-Liq (USD), s=Short-Liq (USD). OI real ~6,7-6,9 Mrd. USD.
  OFFEN: Funding-Skalierung pruefen (Coinalyze ~0,005-0,0076; Engine-Konvention
  Fraktion 0,0001=0,01 % — beim Wiring normalisieren; Vorzeichen stimmt).
- ERLEDIGT: `main.py` bindet Coinalyze OI + Liquidationen ein (Kraken-Snapshot nur noch
  Fallback ohne Key); FlowPoint um long_liq/short_liq erweitert (abwaertskompatibel).
- ERLEDIGT: `backtest.py` speist echtes historisches OI/Liq in `build_series` ein
  (statt OI konstant) -> Muster 4 im Backtest aktiv. Bericht zeigt OI-/Liq-Abdeckung.
- ERLEDIGT: `classify_pattern` nutzt echte Liquidationen (Long-Liq-Kaskade -> Muster 4
  auch ohne OI-Wipeout; Short-Liq -> Muster 3), rueckwaertskompatibel (ohne Liq = alte
  Logik). 45/45 Tests gruen + Smoke-Test: Muster 4 feuert mit echten Daten.
- E9.1 damit FERTIG (Live-Anbindung), Coinalyze-Reachability auf Actions bestaetigt.

### E9.2 — Muster 2/3/4 mit echten Daten schärfen + Retest · Status: MESSBEREIT
- ERLEDIGT: classify_pattern nutzt echtes OI + Liquidationen (in E9.1 gebaut).
- Backtest-Grid auf die Retest-Frage umgestellt: nur-Long-Basis vs. Flush t1/core vs.
  strenge Bestaetigung (alle mit echtem OI/Muster 4). Ziel: Greift `flush_entry`
  (Dip-in-die-Kapitulation kaufen) jetzt, wo Muster 4 aktiv ist? (War in E8.1b „off",
  WEIL OI fehlte.) NAECHSTER SCHRITT: Kaiser laesst Backtest laufen -> ich lese
  BACKTEST.md (inkl. OI-/Liq-Abdeckung) und werte aus: Rendite MIT anstaendigem Recall.

### E9.3 — Bedingter Stop / Nachkauf-Leiter statt pauschalem Stop · Status: MESSBEREIT
- ERLEDIGT: schaltbarer `conditional_stop` in evaluate. Schluss jenseits der Invalidierung
  -> NICHT sofort raus: wenn der Order-Flow den Trend weiter bestaetigt (_confirm_long/short,
  inkl. Muster 4 via Liquidationen) UND der harte Boden (DIP_FLOOR_PCT=5 %) nicht gebrochen
  ist UND hoechstens MAX_DIP_BUYS=2 mal -> Nachkauf-Tranche (DIP_TRANCHE=20 %) statt Stop.
  Sonst (Flow kippt / harter Boden / max erreicht) -> Stop. Position.dip_buys zaehlt +
  wird persistiert (main.py). Rueckwaertskompatibel (Default aus). 48/48 Tests gruen.
- ERLEDIGT (Panel-Fix, "alles was dazugehoert"): Backtest-Grid-Eintraege haben ein
  panel-Flag; das Chart-Panel (site/data/backtest.json) zeigt jetzt die LIVE-Einstellung
  ("nur Long (Basis)"), NICHT mehr die beste Fantasie-Variante (vorher irrefuehrend +33 %).
  index.html beschriftet es als "historische Simulation, keine Garantie, kein Live-Konto".
- MESSLAUF-ERGEBNIS (2026-07-24, echtes OI 998 Punkte): bedingter Stop hilft NICHT.
  Allein +9,2 % (schlechter als Basis +12,3 %); mit Flush +33,1 % vs. Flush allein +33,5 %
  (kein Unterschied -> sichert Flush nicht ab). Gruende: (1) Flush kauft ohnehin aggressiv
  Dips -> conditional_stop redundant; (2) OI deckt nur die juengere Haelfte ab (~166 Tage),
  Muster 4 im frueheren Teil blind -> Test handicapt. KONSEQUENZ: conditional_stop NICHT
  als Default (bleibt aus/schaltbar). Datengrenze: Coinalyze loescht altes 4h-OI (~250 Tage)
  -> Backtest bleibt fuer alte Zeit begrenzt; LIVE hat die Engine ab jetzt vollen Order-Flow.
  EMPFEHLUNG: konsolidieren statt ueberoptimieren. Robuster Gewinn = "nur Long" + echte
  Daten +12,3 % (schon live, Panel zeigt es). Flush/bedingter Stop bleiben aus.

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
