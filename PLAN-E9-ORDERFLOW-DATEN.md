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

### E9.5 — Mehrtages-Kaufleiter (Furkans Tranchen-Nachkauf) · Status: MESSBEREIT
- Kaiser-Wunsch: Furkan kauft in Tranchen ueber mehrere Tage in die Schwaeche nach
  (nie all in; verpasste Cluster 27.-30.10., 29.-31.01. = 7 der 12 Kauf-Fehlstellen).
- ERLEDIGT: schaltbarer `buy_ladder`. In einer offenen Position feuert jede NEUE Tiefkerze
  (long) IN der Retracement-Zone (ueber Invalidierung, unter 0.5) mit Flow-Bestaetigung
  eine kleine Nachkauf-Tranche (BUY_LADDER_TRANCHE=15 %), hoechstens MAX_BUY_RUNGS=3.
  Position.buy_rungs zaehlt + wird persistiert. Rueckwaertskompatibel (Default aus).
  49/49 Tests. Grid testet Kaufleiter allein + mit Flush + mit bedingtem Stop.
- MESSLAUF-ERGEBNIS (Voll-Daten-Fenster 15.11.-01.05.): Kaufleiter HILFT — verdoppelt fast
  den Long-Gewinn (nur Long +9,8 %->+18,0 %, +977->+1.802 €) bei GLEICHER Treffer-/Praezision.
  Erster "mehr kaufen"-Hebel mit echtem Nutzen (Furkans Methode). KONSEQUENZ: buy_ladder=True
  als DEFAULT gesetzt.
- ZUSATZ (Kaiser 2026-07-24): flush_entry='core' ebenfalls als DEFAULT — ABER Flush-Einstiege
  tragen tag='FLUSH' und werden in Telegram als "AGGRESSIVER FLUSH-EINSTIEG — DEINE Entscheidung"
  markiert (Kaiser entscheidet individuell, App sendet nur Signale). Panel/Chart-Variante auf
  "Live: L+S +Kaufleiter +Flush" umgestellt (behebt Kaisers Verwirrung: Panel zeigte vorher die
  +2,8 % der Long+Short-Analyse statt der echten Live-Einstellung). 50/50 Tests.
  Long/Short-Split (Fenster): Short +762 € > Long +315 € — in diesem Zeitraum waren Shorts
  sogar profitabel (haengt vom Zeitraum ab).

### E9.6 — Ehrliche Messung + Web-Auswertung (Kaisers Vorgaben) · Status: MESSBEREIT
- ERLEDIGT: Backtest laeuft nur ueber das **Voll-Daten-Fenster** (ab der ersten OI-Kerze;
  eff_start = max(START_MS, min(oi_map))). Vorher (OI fehlt) keine Trigger. score() zaehlt
  nur Furkans Trigger IM Fenster (n_kauf/n_verkauf). Behebt Kaisers Sorge: frueher Teil war
  mit schlechten Daten kontaminiert.
- ERLEDIGT: P&L **getrennt nach Richtung** (long_profit/short_profit + Trades/Wins) in
  simulate(), im Bericht (Long €/Short € Spalten) und im Chart-Panel.
- ERLEDIGT: Panel/Chart-Variante = **Long+Short (Analyse)** (Kaiser: alle Longs UND Shorts
  zeigen). Backtest schreibt `site/data/backtest_signals.json` mit allen Signalen des
  Fensters; index.html laedt sie und zeichnet alle Marker (Long-Einstieg K1/K2 gruen,
  Long-Ausstieg TV/V/SL orange/rot, Short-Einstieg S1/S2 rot, Short-Ausstieg STP/SC lila) —
  plus Long/Short-P&L im Panel. 49/49 Tests.
- OFFEN (Punkt 5, Zukunfts-Investition): OI/Liq bei jedem Lauf in eine committete Historie
  mergen (Coinalyze loescht altes 4h-OI) -> kuenftige Backtests bekommen volle Abdeckung.
- NAECHSTER SCHRITT: Kaiser laesst Backtest laufen -> saubere Messung nur auf Voll-Daten +
  Long/Short getrennt sichtbar auf der Seite.

### E9.7 — Long+Short-Befund + Telegram-Neusendung · Status: TEILWEISE
- BEFUND (Backtest Voll-Daten-Fenster): Long+Short VERLIERT. "Live: L+S +Kaufleiter +Flush"
  = -3,9 % (Long +570 €/Short +120 €); "Long+Short (Analyse)" plain = +2,8 %. Long-only
  +Kaufleiter = +18 %. Grund: mechanische Shorts sind mistimed (kein Makro-Bias, der die
  Richtung waehlt). KONSEQUENZ: Panel/Chart = "+Kaufleiter" (nur Long, +18 %, robust).
  Empfehlung an Kaiser: live nur Long (state.json bias_short=false). Shorts erst sinnvoll
  mit Makro-/Richtungs-Bias (KI-Makro, pausiert) -> dann wieder aufnehmen.
- ERLEDIGT (Kaiser-Wunsch): Telegram-Neusendung aller Trigger auf Knopfdruck.
  main.py --resend-all (liest signals.json, sendet alle erneut, mit Kopf-Nachricht);
  signal.yml workflow_dispatch-Input "resend_all". 50/50 Tests.

### E9.8 — Konsistenz-Korrekturen (Cowork-Durchsicht 2026-07-26) · Status: MESSBEREIT
Drei Widersprueche zwischen Doku, Code und Live-Verhalten gefunden und behoben:
1. `.github/workflows/backtest.yml` committete `site/data/backtest_signals.json` NICHT
   (`git add` unvollstaendig). Die Chart-Seite laedt genau diese Datei fuer die volle
   Long/Short-Marker-Historie -> sie kam nie im Repo an. Pfad ergaenzt.
2. Das Chart-Panel (`panel=True` im backtest.py-GRID) stand auf "+Kaufleiter"
   (flush off). Live laeuft aber nur Long + Kaufleiter + **Flush core** (config.json +
   evaluate-Defaults). Das Panel zeigte damit eine Rendite, die die Engine nie erzielt hat.
   Panel-Flag auf die Variante "LIVE: nur Long +Kaufleiter +Flush core" gesetzt; darueber
   steht jetzt eine Panel-Regel als Kommentar (Flag muss bei jeder Aenderung an
   config.json oder an den evaluate-Defaults mitwandern).
3. Der Kommentarblock in `strategy_core.evaluate` behauptete weiterhin flush='off' sei
   Default und beste Kombination (Stand vor E9.1, ohne echtes OI). Auf den aktuellen,
   gemessenen Stand gebracht; die alte Aussage steht als HISTORIE dabei, mit dem Grund
   fuers Umkippen (Muster 4 war ohne Liquidationsdaten blind).
50/50 Tests gruen.
MESSLAUF-ERGEBNIS (2026-07-26 20:49 UTC, Fenster 17.11.2025-01.05.2026, 986 echte
OI-Punkte): Alle drei Korrekturen greifen. `backtest_signals.json` ist jetzt im Repo
(143 Signale) -> Chart zeigt erstmals die volle Historie. Panel zeigt
"LIVE: nur Long +Kaufleiter +Flush core": **+39,5 %** (10.000 -> 13.949 EUR),
Buy&Hold -16,4 %, realisierter Long-Gewinn +3.811 EUR aus 60 Abschluessen (47 im Gewinn).
Damit ist die Live-Einstellung im Grid auch die renditestaerkste (vorher zeigte das Panel
faelschlich -3,9 % aus der Long+Short-Variante). Vergleich: nur Long 10,2 % / +Kaufleiter
18,5 % / +Flush core 31,1 % / Long+Short-Referenz 3,2 %.
ZWEI OFFENE BEFUNDE aus dem Lauf (nicht behoben, bewusst dokumentiert):
(a) FENSTER WANDERT: eff_start war am 24.07. der 15.11., jetzt der 17.11. — Coinalyze
    loescht altes 4h-OI laufend. Damit ist JEDER Backtest ein anderer Zeitraum und
    Ergebnisse sind ueber die Zeit nicht vergleichbar (+38,9 % vom 24.07. vs. +39,5 %
    heute sind KEIN Fortschritt, nur ein anderes Fenster). -> E9.6 Punkt 5 (OI/Liq bei
    jedem Lauf in eine committete Historie mergen) wird damit vom "nice to have" zur
    Voraussetzung fuer belastbare Messungen. Naechste Etappe.
(b) FLUSH-CHURN + SIGNAL-MENGE: 143 Signale in 5,5 Monaten, Praezision nur 29 %
    (nur Long ohne Flush: 43 %). In den Signalen stehen mehrfach Ketten aus
    FLUSH-Einstieg -> Stop 4h spaeter -> naechster FLUSH-Einstieg (z. B. 28.-30.04.,
    drei Zyklen um 76-77k). Unterm Strich rentabel, aber whipsaw-anfaellig und viele
    Telegram-Nachrichten. Dazu Serien von WARNUNG-Nachrichten (Derivate-Pump), die
    weder Kauf noch Verkauf sind. Vor einer Verschaerfung erst messen, nicht raten.

### E9.9 — TP2-Blockade + Backtest-Zeitraum · Status: MESSBEREIT (2026-07-26)
BEFUND (Kaisers Frage „warum kommen nach dem 03.07. keine Signale?"): Die Engine lief
korrekt (letzte verarbeitete Kerze 26.07.2026 16:00), war aber **blockiert**. Am
03.07.2026 20:00 kam TEILVERKAUF 2; danach steht die Position in Zustand TP2 mit 20 %
Rest. In TP2 kann nur noch (a) der Stop bei Kerzenschluss unter der Invalidierung
(58.900 USD — Kurs 64.700, weit weg) oder (b) „Rest schliessen" bei Gegen-Muster
feuern. Beides trat 3 Wochen nicht ein. Und weil der Einstiegs-Block in `evaluate` nur
bei `state == FLAT` laeuft, wurde damit JEDER neue Einstieg verhindert — nicht nur
Stille, sondern Taubheit. Der Backtest konnte das nie zeigen, weil er am 01.05. endete.
- ERLEDIGT: schaltbarer `release_stale_rest` in evaluate. In TP1/TP2 wird der Rest
  freigegeben (VERKAUF_REST / SHORT_COVER_REST, 20 %), sobald der letzte signifikante
  Impuls NICHT mehr der ist, auf dem die Position sitzt (Vergleich ueber die
  Pivot-Zeitstempel, in state.json persistiert). Beim Positionsaufbau (T1/CORE/FULL)
  greift es absichtlich NICHT — dort ist der Stop zustaendig. Begruendung deckt
  Grundregel 1: Fib-Zonen sind dynamisch, nie starr; eine Position auf eingefrorenen
  Zonen ist irgendwann gegenstandslos.
- ERLEDIGT: live per `site/data/config.json` -> `release_stale_rest` umschaltbar (kein
  Push noetig, Browser-Edit reicht). Default AUS, bis gemessen. main.py gibt den Wert
  an evaluate weiter.
- ERLEDIGT: `END_MS` im Backtest ist jetzt **jetzt** statt hart 2026-05-01. Damit werden
  Mai/Juni/Juli 2026 mitsimuliert — genau der Zeitraum der Blockade.
- ERLEDIGT (Ehrlichkeit, Regel 3): `score()` bewertet Recall/Praezision nur bis zum
  letzten notierten Trigger + Toleranz (22.04.2026 + 1 Tag). Ohne das wuerde jedes
  Signal aus Mai-Juli automatisch als Fehltreffer zaehlen und die Praezision faelschlich
  einbrechen. Die P&L laeuft ueber das ganze Fenster. Der Bericht nennt beide Zeitraeume
  getrennt.
- Grid um `LIVE +Rest-Freigabe` erweitert (dieselbe Live-Kombination + Freigabe).
  Messfrage: schneidet die Freigabe Runner ab (kostet Rendite) oder bringt sie welche,
  weil die Engine nicht mehr blockiert ist? 54/54 Tests gruen.
- NAECHSTER SCHRITT: Kaiser pusht + laesst Backtest laufen. Wenn `LIVE +Rest-Freigabe`
  nicht schlechter ist: `release_stale_rest` in config.json auf true, Default in
  strategy_core und das panel-Flag mitziehen. Ergebnis hier nachtragen.

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
