# BTC-Signal-App nach Furkan Yildirims Strategie — Etappenplan

Stand: 2026-07-22 · Projektordner: `BTC-Trading`

## Ziel (aus Nutzersicht)

Kaiser möchte Furkans Order-Flow-Strategie (Video, ~25 Min, 1080p) als Anwendung:
- Serverseitig laufend, **dauerhaft kostenlos gehostet**.
- **Push-Trigger per Telegram**: Kauf, Verkauf, Teilgewinnmitnahme, Stoploss, Nachkauf — für **Long und Short**.
- **Web-Chart** (Handy + PC): Kerzen auf 1h / 4h / 1D / 3D / 1W / 1M, mit eingezeichneten Triggern.
- Golden Pockets **dynamisch** (aus letzten Hochs/Tiefs in intelligent gewähltem Zeitabschnitt), NICHT starr — das war der Fehler früherer Versuche.
- Nutzer-Zitat: „Teilgewinnmitnahme wie bei Furkan, weil nie all in oder all out."

## Getroffene Entscheidungen

| Thema | Entscheidung |
|---|---|
| Push-Kanal | Telegram (eigener Bot) |
| Hosting | GitHub (Konto vorhanden); Actions = Signal-Engine, Pages = Chart-Webseite. Wird in E3 verifiziert. |
| Datenquelle | Dieselbe Börse/Plattform wie im Video (wird in E1 identifiziert) |

## Benötigte Inputs (vom Nutzer)

- [x] Video: `Order Flow Trading Indikatoren der Bitcoin Krypto Profis erklärt.mp4`
- [x] Transkript mit Zeitstempeln (`Transkript.md`)
- [x] Kaisers notierte Kauf-/Verkaufstrigger (`Kauftrigger.md`, `Verkaufstrigger.md`)

## Etappen

### E1 — Videoanalyse → Strategie-Spezifikation · Status: FERTIG (2026-07-22, Fable)
Ergebnis: `docs/STRATEGIE.md`. 20+ Video-Frames extrahiert und geprüft; der YouTuber blendet
sein eigenes Regel-Dokument ein — alle Regeln wörtlich übernommen. Plattformen verifiziert:
Velo (CVD/OI/Funding/Liquidations, aggregiert), TradingView (Fib), Pionex (Ausführung).
Transkript lesen; an allen entscheidenden Zeitstempeln Frames aus dem Video extrahieren und ansehen (Pflicht — Transkript allein reicht nicht). Ergebnis: `docs/STRATEGIE.md` mit: allen Indikatoren, wie Furkan sie kombiniert, exakten Regeln/Schwellen, Golden-Pocket-Logik (dynamische Bezugspunkte + Wahl des Zeitabschnitts), Long- und Short-Regeln, verwendete Plattform/Börse.

### E2 — Gegencheck mit Kaisers Trigger-Notizen · Status: FERTIG (2026-07-22, Fable)
Ergebnis: `docs/GEGENCHECK.md`. Alle 46 Trigger-Daten gegen Binance-Tageskerzen geprüft:
kein Widerspruch zur Spezifikation; mehrere punktgenaue Treffer (08.01. GP, 14.01.
Extension 1.0). Eine offene, nicht blockierende Frage an Kaiser (Doppel-Einträge).
Abweichung/Notiz: Börsen-APIs sind aus der Cowork-Sandbox per curl blockiert, per
Web-Fetch erreichbar — für E3/E4 einplanen (auf GitHub Actions kein Problem).

### E3 — Hosting-Recherche + Architektur · Status: FERTIG (2026-07-22, Fable)
Ergebnis: `docs/ARCHITEKTUR.md`. Entscheidung: public GitHub-Repo — Actions (Engine, Cron
15 Min, idempotent gegen Cron-Verzögerungen) + Pages (Chart-Frontend) + Telegram-Bot.
Alle Datenquellen ohne API-Key; Liquidations in V1 als Proxy (OI-Abfall + Range-Spike).

### E4a — Kern-Engine offline · Status: FERTIG (2026-07-22, Fable)
Ergebnis: `signal-app/engine/strategy_core.py` + `test_strategy_core.py` + `run_tests.py`.
12/12 Tests gruen (`python3 run_tests.py`), darunter die Video-Zahlen als Testvektoren
(GP 89.563,6/89.294,3 aus Frame 17:55; Extension-1.0-Ziel vs. reales Hoch 14.01. < 0,3 %
Abweichung). Abdeckung: Pivots, dynamische Fib-Zonen (Long+Short), 4 Kompass-Muster,
Zustandsmaschine (KAUF 1/2, NACHKAUF, TEILVERKAUF 1/2, STOPLOSS, Dedupe).
Hinweis Sandbox: PyPI/Boersen-APIs dort blockiert — Tests laufen ohne pytest via run_tests.py;
E4b (Fetcher/Backtest) auf GitHub Actions entwickeln/ausfuehren.
### E4b — Daten-Layer + Backtest/Kalibrierung gegen Kaisers Trigger · Status: TEILWEISE (2026-07-22, Fable)
FERTIG: `engine/main.py` — Fetcher (Binance Spot/Futures/OI/Funding, ohne Key), CVD-
Berechnung, State-Persistenz, Kerzen-Nachholschleife; 4 Offline-Tests (Fake-Fetch).
Dokumentierte Abweichung: V1 nutzt Binance statt Multi-Boersen-Aggregation.
OFFEN: Live-Verifikation auf Actions + Backtest-Kalibrierung (N, k, Schwellen) gegen
Kaisers Trigger-Liste (Ziel ≥70 % ±1 Tag).

(E4 wurde in E4a/E4b geteilt, siehe oben. Kaisers Rückmeldung 2026-07-22: Doppel-Einträge
in den Trigger-Listen evtl. Versehen → im Backtest tolerant werten.)

### E5 — Telegram-Benachrichtigungen · Status: FERTIG offline (2026-07-22, Fable)
Ergebnis: `signal-app/engine/telegram_notify.py` (nur Standardbibliothek, Dry-Run-Modus)
+ Tests. Nachrichtenformate je Trigger-Typ (Emoji, Preis, Tranche, Stop-Referenz, Grund,
Zeit, Sicherheits-Fusszeile). Duplikat-Schutz liegt in der Engine (Kerzen-Dedupe).
VERBLEIBT fuer E7: BotFather-Anleitung + Live-Sendetest mit echtem Token.

### E6 — Web-Chart · Status: FERTIG offline (2026-07-22, Fable)
Ergebnis: `signal-app/site/index.html` (lightweight-charts via CDN, dunkles Theme,
Handy-tauglich) + Demo-`data/signals.json`/`state.json` mit echten Zahlen aus
Video/Gegencheck. Timeframes 1h/4h/1D/3D/1W/1M; Trigger-Marker (K1/K2/NK/TV1/TV2/V/SL,
Short-Seite, Warnung); Fib-Zonen als gestrichelte Linien. Kerzen client-seitig von
Binance-Public-API, Fallback auf committete `data/candles_*.json` (liefert E4b).
Verifiziert offline: JS-Syntax (node --check) + JSON valide. VERBLEIBT fuer E7:
Live-Test im Browser (CORS), Pages-Deploy.

### E7 — Deployment + Anleitung + Testlauf · Status: IN ARBEIT (2026-07-22)
FERTIG: 3 Workflows (`tests.yml`, `signal.yml` Cron 15 Min + Testnachricht-Option,
`pages.yml`), `README.md` = komplette Schritt-für-Schritt-Anleitung (Repo, Pages,
BotFather, Secrets, Testlauf), `.gitignore`. YAML validiert, 20/20 Tests gruen.
Stand Deployment: Repo live (github.com/szoceikaiser/btc-signal-app), 3 Workflows
registriert, Tests auf Actions gruen, Telegram-Testnachricht ANGEKOMMEN.
Praxis-Befund Erstlauf: fapi.binance.com liefert HTTP 451 (US-Geo-Block der
GitHub-Runner) → Engine umgestellt auf Binance-Vision (Kerzen/Spot-CVD) + Kraken
Futures (OI-Snapshots mit eigener Historie, Funding stundenweise ×8); Kompass-Muster 2
ohne Fut-CVD ueber OI+Funding+Spot. 21/21 Tests gruen.
ABGESCHLOSSEN (2026-07-22): Ende-zu-Ende verifiziert — Engine-Lauf gruen (400 Kerzen,
Nachholung erzeugte 15 historische Signale inkl. kompletter Long-/Short-Zyklen mit
Stops), state.json/signals.json live im Repo, Webseite online
(szoceikaiser.github.io/btc-signal-app), Telegram funktioniert, Cron aktiv (15 Min).
Lokaler Ordner signal-app ist jetzt git-Clone (Updates via git push).
Hinweis: Erstlauf-Nachholung kann einen einmaligen Telegram-Nachrichten-Schwall
ausgeloest haben — ab jetzt nur noch Echtzeit-Signale.
E7 damit FERTIG.
Nachtraege 2026-07-22: (a) Chart laedt Signaldaten jetzt direkt aus dem Repo (raw),
weil Bot-Commits kein Pages-Redeploy ausloesen — Demo-Badge-Problem behoben.
(b) OHLC-Overlay (Crosshair, de-DE, Δ%) + Doppelklick-Reset im Chart.
(c) E4b-Backtest gebaut: engine/backtest.py + Workflow "Backtest" (workflow_dispatch);
Grid pivot_n 3-6 × k_atr 2/3, Vergleich gegen Kaisers Trigger (±1 Tag, Kauf=Long
kaufen/Short decken, Verkauf=Long verkaufen/Short eroeffnen), Bericht BACKTEST.md.
24/24 Tests gruen.
E4b-ERGEBNIS (2026-07-22, BACKTEST.md im App-Repo): beste Kombination n=5, k_atr=2.0 —
Kaufseite 13/20 (65 %), Verkaufsseite 7/24 (29 %), gesamt 45 % Recall / 54 % Praezision.
Kalibrierte Defaults in strategy_core.evaluate uebernommen. Ziel 70 % verfehlt; Ursachen
identifiziert: (1) OI-Historie fehlte im Backtest (live vorhanden -> Muster 4 aktiv),
(2) Furkans gestaffelte Verkaeufe ueber mehrere Tage nicht modelliert, (3) kein
FLAT-Einstieg bei GP-Durchschlag (Crash-Kerzen). E4b damit FERTIG.

### E8 — Verbesserungen aus Backtest-Erkenntnissen · Status: OFFEN
1. ERLEDIGT (2026-07-22): Capitulation-Einstieg aus FLAT (Long: Kerze durchschlaegt
   GP, Schluss ueber Invalidierung; Short spiegelbildlich) -> KAUF_2/SHORT_2 75 %.
   29/29 Tests gruen. Chart-Kerzen-Historie erweitert (1h: 3 Seiten, 4h: 2).
   Erkenntnis aus Analyse: schwache Verkaufsquote war groesstenteils Folgefehler
   verpasster Einstiege -> dieser Fix hebt beide Seiten. Kaisers Hinweis: Trigger
   nach 27.03. nicht mehr notiert -> Praezision nach April unterschaetzt.
   Wirkung per Backtest-Lauf messen (Workflow "Backtest").
2. FERTIG (2026-07-24, E8.2): Gestaffelte Teilgewinne. Parameter tp_ladder in
   strategy_core.evaluate: Zwischen-Teilgewinne an Extension 0.8 und 0.9 (je 15 %,
   hoechstens eine Stufe je Kerze) VOR dem 1.0-Ziel — bildet Furkans mehrtaegige
   Verkaufs-Ladders nach (02.-03.10., 08.-22.04.). Long UND Short (TEILVERKAUF_LADDER /
   SHORT_TP_LADDER) inkl. Telegram-Style (gelb) + Chart-Marker (TVL/STPL) + Legende;
   tp_rungs wird im state.json persistiert. Backtest-Grid um Dimension Leiter (an/aus)
   erweitert, P&L-Sim verkauft je Stufe 15 % der Spitzenposition. 32/32 Tests gruen.
   MESSLAUF-ERGEBNIS (BACKTEST.md, 2026-07-24) bei n=5: Leiter aus vs. an je Recall 45 %
   und Praezision 54 % (UNVERAENDERT), Rendite -5,3 % (an) statt -6,0 % (aus). Die Leiter
   trifft KEINE neuen Verkaufstage (Recall gleich, Regel 3), verbessert aber die Rendite
   durch gestaffelte Gewinnmitnahme und hat keinen gemessenen Nachteil. KONSEQUENZ:
   Default tp_ladder=True gesetzt (strategy_core). Backtest-"beste"-Marker steht weiter
   auf "aus", weil sein Ranking nur Recall+Praezision vergleicht (Rendite beim Gleichstand
   ignoriert) — kein Widerspruch. Erfordert einen weiteren Push durch Kaiser.
3. Nach ~2 Wochen Live-OI-Historie: Backtest auf juengstem Zeitraum wiederholen und
   Muster-Schwellen (oi_wipeout, sharp_move) kalibrieren.
4. ERLEDIGT (2026-07-22): P&L-Simulation in backtest.py (tranchen-genau, 0,1 %
   Gebuehr, Buy&Hold-Vergleich) + Panel auf der Chart-Webseite (site/data/
   backtest.json) + Anleitungen ANLEITUNG-EINSTELLUNGEN.md / ANLEITUNG-TELEGRAM.md
   im App-Repo (mit Kontrollpunkten und Fehlerdiagnose aus Kaisers Einrichtung).
   27/27 Tests gruen. Backtest-Workflow muss neu laufen, damit Panel Daten hat.
5. Richtungs-Bias (Furkans Schritt 1). ERKENNTNIS 2026-07-24 (Kaiser + erneute
   Transkript-Lesung 16:03-19:41): Furkan entscheidet die RICHTUNG (long/short) zuerst
   aus MAKRO ("damit ich ueberhaupt meinen Bias habe: gehe ich eher long oder short"),
   erst danach Orderflow+Fib nur zum TIMING des Einstiegs auf der gewaehlten Seite. In
   Kaisers Order-Zeitraum war der Bias praktisch immer LONG — seine "Verkaeufe" waren
   Long-Schliessungen/Teilgewinne, KEINE Shorts. Unsere Engine hat diese erste Stufe
   NICHT: sie leitet die Richtung nur aus dem letzten Swing-Impuls ab und erzeugt so
   Shorts, die Furkan nie gehandelt hat. ZWISCHENSCHRITT (implementiert 2026-07-24):
   Backtest-Grid um Dimension Richtung erweitert (ls=Long+Short vs. long=bias_short=false),
   Auswahl jetzt primaer nach Rendite. MESSLAUF-ERGEBNIS (BACKTEST.md, 2026-07-24):
   long-only schlaegt long+short bei jedem pivot_n; bei n=4/5/6 kippt es von Verlust in
   Gewinn (n=5: -5,3 %->+2,5 %, n=4: +3,6 %; n=6 +16,3 % aber fragil, nur 16 % Recall).
   Buy&Hold -28,4 %. Bestaetigt: die von Furkan nie gehandelten Shorts kosteten Rendite.
   Live-Engine bewusst NICHT fest auf long gestellt (Bias soll dynamisch sein).
   GEWAEHLT (Kaiser 2026-07-24): automatischer Bias per KI-Makro (Stufe 2 — taegliche
   KI liest Makro/News -> long/short/neutral), NICHT der mechanische EMA-Filter (Stufe 1).
   Vollstaendiger Design-/Erkundungsstand + Bausteine + Ehrlichkeitshinweis:
   siehe signal-app/PLAN-E8.5-KI-MAKRO-BIAS.md (repo-getrackt, damit auch in Cowork
   verfuegbar). NOCH NICHT GEBAUT — pausiert, Kaiser macht zuerst mit etwas anderem weiter.
   Manueller Schalter bias_long/bias_short in state.json bleibt (geplant: config bias_mode
   "auto"/"manual").
6. ERLEDIGT (2026-07-23, E8.1): Capitulation-/Squeeze-Einstieg bei GP-Durchschlag
   + Chart-Historie erweitert. MESSLAUF-ERGEBNIS: Variante "core" (75 %) verschlechterte
   Recall 45->36 % (kannibalisiert Ladder-Kaeufe 27./28.10., 29.-31.01.). P&L erstmals
   gemessen: -9,8 % vs. Buy&Hold -28,4 % (Baerenmarkt-Zeitraum; Strategie verliert
   deutlich weniger als der Markt). DARAUF E8.1b (2026-07-23): flush_entry-Parameter
   (off/t1/core, Default t1 = kleine Tranche), Backtest-Grid 12 Kombis (n 3-6 x Modus)
   mit Rendite-Spalte. MESSLAUF 23.07. 19:37: flush='off' gewinnt klar (n=5:
   Recall 45 %/Praez. 54 %/Rendite -6,0 % vs. t1/core je 36 %/-8,7/-9,8 %).
   KONSEQUENZ: Default flush_entry='off' gesetzt (strategy_core), Parameter bleibt
   fuer E8.3-Retest mit echter Live-OI-Historie erhalten. 31/31 Tests gruen.
   E8.1/E8.1b damit ABGESCHLOSSEN — Kalibrierungsschleife geschlossen; die
   Kombination (5, 2.0, off) = alter Stand vor E8.1 ist bestaetigt der beste.
   OFFEN bleiben E8-Punkte 3 (OI-Retest nach ~2 Wochen), 5 (Trendfilter),
   7 (Backtest-Marker im Chart), 8 (adaptiver Lookback). Punkt 2 (gestaffelte
   Verkaeufe) seit 2026-07-24 FERTIG (E8.2, Default tp_ladder=True).
7. Backtest-Signale optional als eigene Marker im Chart (Historie vor Mai sichtbar
   machen; Live-Signale existieren erst ab Erstlauf-Fenster ~17.05.2026).
8. Adaptiver Pivot-Lookback (volatilitaetsabhaengiges n) — Anregung aus Opus-Review.
9. IMPLEMENTIERT (2026-07-24, Messung ausstehend): Drei Furkan-Filter fuer BESSERE
   LONG-EINSTIEGE (Kaiser: "bessere Long-Trades / mehr Gewinn"). Alle aus Furkans
   Methode, in strategy_core.evaluate einzeln schaltbar, Default AUS bis per Backtest
   gemessen: (a) trend_filter — nur Setups in Richtung des 1D-Trends (Furkans Schritt 1,
   Preis vs. Tages-EMA aus resample_daily; EMA50 als Naeherung, EMA200/1D braeuchte mehr
   Live-Historie); (b) strict_confirm — KAUF 2 nur wenn Spot-CVD dreht UND Funding stimmt
   (statt eines von beiden = Furkans Konfluenz-Prinzip); (c) confluence — Einstieg nur,
   wenn die 4h-Zone in der 1D-Retracement-Zone liegt (daily_fib_zone). Neue Helfer:
   ema/resample_daily/daily_trend/daily_fib_zone. Backtest-Grid (backtest.py) auf
   Dict-Configs umgestellt, testet die drei Hebel einzeln + kombiniert gegen nur-Long-Basis
   + Long+Short-Referenz; Auswahl nach Rendite. 37/37 Tests gruen.
   MESSLAUF-ERGEBNIS (BACKTEST.md, 2026-07-24, alle nur-Long n=5): KEINER der drei Filter
   verbessert die Long-Trades. Basis "nur Long" 27 % Recall/+2,5 %. (a) Trendfilter SCHAEDLICH:
   Recall 27->5 %, Rendite +2,5->-3,1 % — Grund: Furkan KAUFT Dips (Preis unter EMA), ein
   "nur Long ueber EMA"-Filter blockt genau diese Einstiege; das Falling-Knife-Risiko fangen
   die Stops ab. (b) Konfluenz 4h/1D FRAGIL: Recall 27->7 %, nur 16 Signale, 0/20 Kauftage
   getroffen — +2,9 % ist Glueckstreffer, kein Fortschritt. (c) Strenge Bestaetigung
   WIRKUNGSLOS (identisch zur Basis; im Backtest fehlen OI+Futures-CVD -> nichts Strengeres
   zu pruefen). KONSEQUENZ: KEIN Filter als Default (alle bleiben schaltbar AUS). strict_confirm
   fuer E8.3-Retest mit echter Live-OI aufheben. ERKENNTNIS: mehr Filter = weniger Trades =
   mehr Gluecksabhaengigkeit, nicht mehr Gewinn. Robust bleibt nur die RICHTUNG (nur Long).
   Bessere Long-Trades kommen aus besseren DATEN (E8.3 Live-OI ~Anfang Aug) + intelligentem
   Richtungs-Bias (KI-Makro), nicht aus mechanischen Gattern. Kaiser notiert spaeter
   Furkan-Long-Trades nach 27.03. als erweiterten Maszstab.

### E9 — Echte Order-Flow-Daten (Coinalyze) + intelligentes Dip-/Stop-Management · Status: OFFEN (Start 2026-07-24)
Durchbruch aus der Diskussion mit Kaiser: Es GIBT kostenlose historische OI-/Liquidations-
Daten (Coinalyze). Die bisherigen E8.5-Filter brachten nichts, weil die Engine ohne echtes
OI/Liquidationen/Futures-CVD blind war. E9 schliesst diese Daten an und macht damit alles
moeglich, was Furkan tut: welcher Dip haelt (Muster 4), wann warten statt stoppen, Liquidations-
Heatmap. E8.3 (auf 2 Wochen Eigen-OI warten) entfaellt — Coinalyze liefert die Historie mit.
Vollstaendiger Etappenplan (E9.1 Daten-Layer, E9.2 Muster mit echten Daten + Retest,
E9.3 bedingter Stop/Nachkauf-Leiter statt pauschalem Stop, E9.4 Liquidationen sichtbar):
siehe **signal-app/PLAN-E9-ORDERFLOW-DATEN.md** (repo-getrackt). Alles schaltbar, Default aus,
per Backtest gemessen. Braucht kostenlosen Coinalyze-Key von Kaiser (COINALYZE_API_KEY,
Anleitung folgt). Reachability von US-Actions-Runnern verifizieren.

### E10 — Erkenntnisse aus Furkans Update-Videos (Juli 2026) · Status: IN ARBEIT (2026-07-27)
Kaiser hat zwei Transkripte geliefert. Auswertungen mit Zitaten:
**docs/FURKAN-UPDATE-2026-07.md** (Video A) und **docs/FURKAN-UPDATE-2026-07-B.md** (Video B).

- **E10.1 Kapital-Reserve** („Pulver behalten") · FERTIG, Hypothese WIDERLEGT: Rendite
  fällt fast exakt proportional zum Einsatz (100 % → +30,0 %, 60 % → +17,9 %,
  50 % → +14,8 %), risikobereinigt sogar leicht schlechter. Bleibt bei 100 %. Grund:
  falsche Ebene — Furkan meint die Reserve fürs Spot-Portfolio, nicht fürs 4h-Trading.
  Nebenbefund aus der neu eingeführten Drawdown-Spalte: `flush_entry` verdoppelt Rendite
  UND maximalen Rückgang (+33,1 %/−12,7 % gegen +19,9 %/−6,3 % ohne Flush).
- **E10.2 Teilverkauf unter dem letzten Hoch** · FERTIG, gemessen: Recall 57 → 61 %,
  Rendite −2,8 Punkte. Der Spot-Filter („weak") macht keinen Unterschied (+27,1 gegen
  +27,3 %) — Punkt 4 des Videos damit erledigt, ohne eigene Warn-Nachricht.
  **ÜBERGREIFENDER BEFUND: Fünf Mechanismen auf der Verkaufsseite gemessen, alle heben
  die Ähnlichkeit zu Furkan, alle kosten Rendite. Die Verkaufsseite ist auserzählt.**
- **E10.3 Liquidationszonen für EINSTIEGE** (`liq_entry`, boost/filter) · FERTIG,
  gemessen 2026-07-27: `boost` exakt neutral (+29,8 % gegen +29,8 %, 19 zusätzliche
  Nachkäufe ohne jeden Effekt), `filter` schädlich (+22,5 %, Recall 57→50 %). Damit sind
  Liquidationsdaten auf beiden Seiten gemessen — kein Renditevorteil. Bleibt `off`.

### E11 — Robustheit statt neuer Mechanismen · Status: FERTIG (gemessen 2026-07-27)

**ERGEBNIS DER HALBIERUNG** (H1 18.11.25–24.03.26, H2 24.03.26–27.07.26):

In BEIDEN Hälften unter den besten 5 — und zwar genau zwei Varianten:
`LIVE: nur Long +Kaufleiter +Flush core` (Platz 2 / 3) und `LIVE +Stop nachziehen`
(Platz 3 / 5). Das ist die Live-Einstellung. Sie hält.

**Der Beleg, dass die Prüfung nötig war:** `LIVE +Stop +Liq-Konfluenz aufstocken` war in
Hälfte 1 auf **Platz 1** (+21,2 %) und in Hälfte 2 auf **Platz 15** (+7,0 %). Genau die
Variante, die im Volljahr „exakt neutral" aussah, wäre bei einem kürzeren Testfenster als
Gewinner durchgegangen. Ebenso gekippt: `+Kaufleiter +Bed.Stop` (Platz 17 → 1),
`+Kaufleiter` allein (15 → 2), `Liq-Zonen` (4 → 9).

**Stabil über beide Hälften** (und damit belastbar):
- Kapital-Reserve ist konstant schlechter (Plätze 14/16 und 16/18) → E10.1 bestätigt.
- Long+Short ist konstant schlechter (13 / 17) → nur Long bestätigt.
- Die Live-Kombination liegt in beiden Hälften in der oberen Gruppe.

**Einschränkungen der Prüfung, ehrlich:**
- Hälfte 2 ist stark gestaucht: alle 18 Varianten liegen zwischen +5,8 % und +10,8 %.
  Bei 1–2 Punkten Abstand ist die Rangfolge dort fast bedeutungslos. Aussagekräftig ist
  vor allem, dass die Live-Variante in KEINER Hälfte unten liegt.
- Jede Hälfte umfasst nur gut vier Monate.
- Plausibilitätsprüfung bestanden: H1 und H2 verzinst ergeben ungefähr das Vollfenster
  (LIVE 1,211 × 1,095 = +32,6 % gegen gemessene +33,1 %) — die Aufteilung rechnet sauber.
- Alle 18 Varianten sind in beiden Hälften positiv, während BTC 30 % verlor. Ermutigend,
  aber die Simulation kauft und verkauft zu exakten Signalpreisen ohne Schlupf.

**BESCHLUSS: Die Optimierungsphase ist beendet.** Live-Einstellung eingefroren
(nur Long, Kaufleiter, Flush core, trail_stop). Weitere Mechanismen werden nicht mehr
gegen dieses Fenster gemessen — jede weitere Variante erhöht nur die Überanpassung.
Neue Erkenntnisse kommen ab jetzt aus dem LIVE-Betrieb und aus dem Heatmap-Test
(ANLEITUNG-HEATMAP-TEST.md), nicht aus dem Backtest.

**NACHTRAG 2026-07-27 (Kaisers Frage „was hätte ich pro Monat verdient?"):** Der Bericht
hat jetzt einen Abschnitt **„Monat für Monat"** — Kontostand am Ende jedes Kalendermonats,
offene Positionen zum Schlusskurs bewertet, live gegen „ohne Flush" nebeneinander. Dafür
liefert `simulate()` zusätzlich `monate`. Neue Grid-Zeile *MEINE Einstellung ohne Flush*
(nur Long + Kaufleiter + Stop, `flush_entry="off"`), damit der Vergleich die echte
Alternative zeigt und nicht die alte Zeile ohne nachgezogenen Stop.
Beim Bauen aufgefallen und behoben: Der angeschnittene LETZTE Monat fehlte zunächst, die
Monatssumme stimmte dann nicht mit dem Gesamtergebnis überein (im Testfall −139 € statt
−651 €). Der Test prüft die Summengleichheit jetzt mit einer bis zum Schluss offenen
Position, sonst fällt genau dieser Fehler nicht auf. 72/72 Tests grün.

**ERGEBNIS Monatsübersicht (2026-07-27):** Monate im Plus **5 von 9 bei beiden
Varianten** — der Flush verbessert also nicht die Trefferquote der Monate, er verstärkt
nur die Ausschläge in beide Richtungen (live/ohne Flush: Jan +12,4/+10,0 · Feb −2,5/−1,3 ·
Mär +9,5/+2,0 · Apr +14,3/+9,8 · Mai −3,1/−3,5 · Jun −6,7/−2,8 · Jul +6,8/+6,8).

Beantwortet nebenbei Kaisers Frage nach den Verlust-Einstiegen Ende Mai/Juni: Der
schlechteste Monat (Juni −871 € live gegen −322 € ohne Flush) geht zu rund zwei Dritteln
auf die **Flush-Einstiege** zurück — NICHT auf einen fehlenden Makro-Bias. Dieselben
Flush-Einstiege brachten in Januar, März und April zusammen rund 1.400 € mehr. Unterm
Strich +30,0 % gegen +19,4 %, Rückgang aber −11,5 % gegen −6,2 %; risikobereinigt liegt
"ohne Flush" vorn (3,13 gegen 2,61 Rendite je Rückgangspunkt).
"MEINE Einstellung ohne Flush" liegt im Halbtest auf Platz 15 (H1) und 8 (H2), also in
KEINER Hälfte oben — kein Argument, live umzustellen. Da Flush-Signale in Telegram
markiert sind und Kaiser einzeln entscheidet, liegt sein tatsächliches Ergebnis ohnehin
zwischen beiden Spalten.

#### Vorherige Begründung (Beschluss 2026-07-27)
**Gesamtbild nach allen Messungen dieser Session:** Es wirken genau vier Dinge — Richtung
(nur Long), Kaufleiter, Flush-Einstieg (verdoppelt Rendite UND Rückgang) und der
nachgezogene Stop (kostet etwas Rendite, kauft Entblockung und weniger Rückgang). Alles
andere ist gemessen und wirkungslos oder schädlich: vier Einstiegsfilter (trend_filter,
confluence, strict_confirm, liq_entry=filter), fünf Verkaufsmechanismen, die
Kapital-Reserve, Liquidationsdaten auf beiden Seiten.

**Das eigentliche Risiko ist jetzt nicht ein fehlender Mechanismus, sondern
Überanpassung.** Inzwischen sind 18 Varianten gegen EIN Zeitfenster (18.11.25–27.07.26)
verglichen worden. Unterschiede von 2–3 Prozentpunkten sind bei dieser Zahl von Vergleichen
nicht mehr von Zufall zu unterscheiden. Belastbar sind nur die großen Effekte:
nur Long (+30 %) gegen Long+Short (+2 %), Kaufleiter (+20 % gegen +11 %), Flush
(Verdopplung von Rendite und Rückgang).

GEBAUT 2026-07-27: `run_half()` in backtest.py lässt jede Variante zusätzlich getrennt in
zwei Hälften laufen (Trennpunkt = Mitte des Voll-Daten-Fensters). Hälfte 1 wird hinten
abgeschnitten, Hälfte 2 nutzt die früheren Kerzen als Warmup — genau wie die Engine live
die Vergangenheit kennt. Neuer Berichtsabschnitt **„Robustheitsprüfung: Fenster halbiert"**
mit Rendite und Platz je Hälfte, dazu die Liste der Varianten, die in BEIDEN Hälften unter
den besten 5 liegen. 71/71 Tests grün. Laufzeit des Backtests steigt auf etwa das
1,7-Fache (Workflow-Timeout 30 Min bleibt ausreichend).

SO IST DAS ERGEBNIS ZU LESEN:
- Viele Varianten in beiden Hälften oben → die Rangfolge im Hauptteil ist belastbar.
- 0 bis 1 Variante → die Feinunterschiede sind Rauschen. Dann NUR den groben Hebeln
  trauen (Richtung, Kaufleiter) und alles Feine weglassen. Das wäre kein Rückschlag,
  sondern die wichtigste Erkenntnis des Projekts: weniger Mechanik, mehr Verlässlichkeit.

Ergänzend: E9.6 Punkt 5 (OI/Liq in eine committete Historie mergen) würde künftig längere
und damit belastbarere Fenster ermöglichen.
- **OFFEN:** Stop auch bei jeder Aufstockung auf Break-even (Video B, 18:50, kleine
  Ergänzung zu E9.10) · Volatilitäts-Regime aus eigener ATR (erst Handlung definieren).
- **ABGELEHNT von Kaiser:** MVRV-„Valuezone" als Spot-Nachkaufebene — er kauft kein Spot.
  Quelle trotzdem notiert (Bitcoin Magazine Pro bzw. checkonchain, STH-MVRV-Bänder).
  Offene Alternative: derselbe MVRV-Z als backtestbarer Richtungs-Bias statt des
  pausierten KI-Makro-Bias (E8.5).

### E12 — Verlust-Analyse (Kaisers Frage: „Furkan macht wenig Verluste, warum?") · Status: ANALYSE FERTIG, Umsetzung OFFEN (2026-07-27)

Vollständiger Bericht: **docs/VERLUST-ANALYSE-2026-07-27.md**. Kurzfassung:

**BUGFIX (erledigt, muss gepusht werden):** Der STOPLOSS-Zweig in `strategy_core.evaluate`
hatte eine handgeschriebene Teil-Rücksetzung statt `_reset_position()` und vergaß
`entry_ref`, `entry_pct`, `liq_exits`, `high_exits`, `liq_entries`. Folgen: (a) der
Break-even-Stop (`trail_stop`, live aktiv) rechnete mit dem Einstand einer längst
geschlossenen Position, weil `entry_pct` über alle Stops hinweg weiterwuchs; (b) die
Zähler von `liq_exit`/`high_exit`/`liq_entry` liefen gegen ihr Maximum und schalteten die
Mechanismen still ab — **die Messergebnisse aus E9.11, E10.2 und E10.3 sind daher an einem
gebremsten Mechanismus entstanden und nicht sauber.** Behoben + Regressionstest
`test_stoploss_setzt_alle_zaehler_zurueck` (Gegenprobe gemacht: ohne Fix rot). 73/73 grün.

**MESSUNG auf Positions-Ebene (nicht pro Teilverkauf):** 37 Positionen, 21 Gewinner,
16 Verlierer = **57 % Trefferquote, nicht 77 %**. Der Bericht zählt jeden Teilverkauf als
Trade (`trades_closed` in backtest.py) — eine Position mit 3 Teilgewinnen und Stop im Minus
erscheint als „3 Gewinne, 1 Verlust". 70 % aller Positionen enden im Stop; Gebühren
724 € = 24 % des Nettogewinns; mediane Haltedauer 32 h.

**DIAGNOSE:** Furkan handelt 1,8 Positionen/Monat (11 Einstiegs-Cluster in Kaisers Liste),
die Engine 4,5. Sein Stop liegt 3,59 % vom Einstieg (Video-Beispiel 08.01., Bein 9,7 %),
unserer im Median 2,28 % (Bein ~6,5 %); 15 von 37 unter 2 %, einer bei 0,02 %. Längste
Stop-Serie: 10 in Folge, Wiedereinstieg im Median nach 68 h, kürzester Fall 4 h.

**GEMESSEN (nachträglich auf denselben Signalen, kein Neu-Backtest — Richtungsangabe):**
Sperre 48 h nach einem Stop + Mindest-Stop-Abstand 2 % ⇒ Rendite +27,0 % statt +29,5 %,
Rückgang **−3,7 % statt −11,0 %**, Verlust-Positionen **6 statt 16**, Verlustsumme
−1.608 € statt −4.362 €, 18 statt 37 Positionen. Beide Filter senken Rückgang UND
Verlustzahl in BEIDEN Hälften. Risiko-normierte Positionsgröße wurde mitgemessen und
bringt nichts (behandelt das Symptom statt der Ursache).

**OFFEN, in dieser Reihenfolge:** (1) `cooldown_h` = Sperre nach Stop; (2) Break-even-Stop
sobald die Position im Plus ist — nicht erst nach Teilgewinn (das ist der schon notierte
Video-B-Punkt, trifft 44 % der Verlustsumme); (3) `min_stop_pct`; (4) falls nötig `k_atr`
3.0 / `min_pct` 5 %, damit die Engine nur noch Beine in Furkans Größenordnung zeichnet.
Alle schaltbar, Default aus, dann EIN Backtest-Lauf.

**Abgrenzung zu E11:** Der Beschluss „Optimierungsphase beendet" gilt für Einstiegs-
Mechanismen, die um Rendite konkurrieren. (1)–(4) sind Begrenzungen, die die Trade-Zahl
halbieren; ihre Wirkung ist kein 2-Punkte-Rauschen und wurde nie gemessen.

**MESSLAUF NACH DEM FIX (2026-07-27, 19:56 UTC) — Bugfix bestätigt:**
Alle Varianten ohne `trail_stop`/Liq-Mechanismen haben unveränderte Signalzahlen
(115/137/181/207/146) — der Eingriff war chirurgisch. Live-Einstellung
`LIVE +Stop nachziehen`: **+29,8 % → +32,2 %**, STOPLOSS-Signale **26 → 19**, Anteil
gestoppter Positionen **70 % → 56 %**, längste Stop-Serie **10 → 5**, mediane Haltedauer
**32 h → 50 h**, Teilgewinne TV1/TV2 **14/0 → 18/2**.

**E10.3 IST DAMIT HINFÄLLIG:** `LIVE +Stop +Liq-Konfluenz aufstocken` springt von
+29,7 % („exakt neutral") auf **+37,0 %** (+4,8 gegen Referenz) und von Platz 15 auf
Platz 5 in Hälfte 2 — es ist die einzige Variante in beiden Hälften unter den besten 5.
Die Zähler waren nach wenigen Stops am Anschlag, der Mechanismus lief die meiste Zeit
nicht. **E9.11 und E10.2 halten dagegen** (Liq-Zonen +23,3 %, Verkauf am Hoch +28,3 %,
beide unter der Referenz) — deren Befunde sind jetzt sauber gemessen.

**Drei Hebel neu gerechnet (positionsweise, Rendite trifft die offiziellen +32,2 % exakt):**
A (Sperre 48 h) +30,0 %/−8,6 %/12 Verlierer · B (Mindestabstand 2 %) +24,7 %/−6,4 %/8 ·
**A+B +31,6 % / Rückgang −3,7 % / 6 Verlierer von 17 Positionen / Gebühren 298 € statt
686 €.** A+B kostet nach dem Fix nur noch **0,6** Punkte Rendite statt 2,5 und ist
risikobereinigt 3,1× besser; in Hälfte 2 sogar renditestärker als die Live-Einstellung.
→ Empfehlung unverändert: A+B bauen.

**OFFEN zur Entscheidung durch Kaiser:** `liq_entry="boost"` live schalten
(`site/data/config.json`). Dafür: beste gemessene Variante, Furkans ausdrückliche Methode,
strukturell risikoarm (fügt nur eine Nachkauf-Tranche hinzu, max. 2× je Position,
blockiert nie). Dagegen: Robustheitsprüfung meldet „1 von 5 → Rangfolge im Wesentlichen
Zufall", Spanne in Hälfte 2 nur 5,5–10,8 % über 19 Varianten, und die Schätzung für genau
diese Variante ist durch EINEN Bugfix um 7,3 Punkte gesprungen — Messgenauigkeit also
mehrere Punkte. Bei Umstellung muss `panel=True` in `backtest.py` mitwandern.

### E13 — Einstieg nur bei gesundem Order-Flow · Status: GEBAUT 2026-07-28, MESSUNG AUSSTEHEND

**GEBAUT (alle Default AUS, Live-Verhalten unveraendert):**
- `Pattern.UNGESUNDER_ABVERKAUF` (Muster 5) in `classify_pattern` — Preis faellt UND
  Spot-CVD faellt mit UND OI haelt/steigt (≥ −1 %) UND Funding > 0 UND keine
  Long-Liquidations-Kaskade. Halbe Preis-Schwelle (−2 %), damit es WARNT statt hinterher
  festzustellen. Weicht Muster 4: ist der Markt ausgeraeumt, gewinnt die Kapitulation.
- `block_unhealthy` — sperrt Einstiege UND Kaufleiter-Nachkaeufe bei Muster 5 (Long) bzw.
  Muster 1 (Short: nicht in echte Spot-Nachfrage shorten). Nachkauf-Sperre, weil Kaisers
  Beispiel 16.06. genau daran scheiterte (Ersteinstieg + 3 Nachkaeufe in den fallenden Markt).
- `confirm_t1` — Order-Flow-Bestaetigung auch fuer den 0.5-Level-Einstieg.
- `cooldown_h` — Sperrfrist nach einem Stop. Neues Feld `Position.last_stop_ts`, das
  BEWUSST nicht in `_reset_position` steht (Erinnerung ZWISCHEN Positionen) und in
  state.json persistiert wird.
- `min_stop_pct` — Mindestabstand Einstieg→Invalidierung, geprueft an allen sechs
  Einstiegspfaden (0.5-Level, Golden Pocket, Flush; Long und Short).
- Alle vier in `config.json` mit Klartext-Hinweisen, in `main.py` durchgereicht.
- Backtest-Gitter: 6 neue Zeilen (jeder Hebel einzeln, Sperre+Mindestabstand, alle vier).
  19 → 25 Varianten; Workflow-Timeout 30 → 50 min (Trockenlauf: ~5 min, viel Reserve).
- 82/82 Tests gruen. **Gegenprobe gemacht:** jeder der fuenf Mechanismen einzeln im Code
  ausgehebelt → jedes Mal wird genau der zugehoerige Test rot. Dazu ein Test, der prueft,
  dass das Warnlicht einen bloss NEUTRALEN Markt NICHT sperrt (sonst waere es nur ein
  Handelsverbot), und einer, der belegt, dass ohne Einschalten nichts anders laeuft.

**MESSERGEBNIS (BACKTEST.md, 2026-07-28 12:54 UTC, 25 Varianten).** Referenz
`LIVE +Stop nachziehen` = +32,2 % / Rueckgang −12,3 % / 212 Signale.

| Hebel | Rendite | Rueckgang | Signale | Platz H1 / H2 |
|---|---|---|---|---|
| Warnlicht (`block_unhealthy`) | +30,0 % | −12,3 % | **209** | 5. / 8. |
| Flow-Pruefung 0.5-Level (`confirm_t1`) | +27,6 % | −12,1 % | 202 | 16. / 2. |
| Sperre 48 h nach Stop (`cooldown_h`) | **+33,9 %** | **−8,5 %** | 185 | 17. / **1.** |
| Mindest-Stopabstand 2 % (`min_stop_pct`) | **+33,0 %** | **−7,0 %** | 156 | **2.** / 10. |
| Sperre + Mindestabstand | +26,4 % | −7,0 % | 146 | 13. / 11. |
| alle vier zusammen | +14,7 % | −6,9 % | 117 | 19. / 25. |

1. **Warnlicht praktisch wirkungslos: es hat 3 von 212 Signalen verhindert.** Muster 5
   feuert im echten Datensatz fast nie. Wahrscheinliche Ursache: die Bedingung
   `funding_now > 0` — im Baerenmarkt ist das Funding beim Abverkauf meist schon gedreht.
   Die drei verhinderten Kaeufe waren profitabel (−2,2 Punkte Rendite). **BEWUSST NICHT
   nachjustiert** (Kaiser 2026-07-28): Die Schwelle so lange lockern, bis das Ergebnis
   passt, waere Ueberanpassung an genau dieses Fenster. Bleibt ausgeschaltet im Code
   liegen; sinnvoll erst mit laengerer Historie (E9.6 Punkt 5) neu zu pruefen.
   → Damit ist Kaisers Ausgangsfrage beantwortet: Den Indikator GIBT es, aber er haette
   an den fraglichen Tagen nicht geholfen.
2. **`confirm_t1` kostet Rendite** (−4,6 Punkte). Reiht sich in alle bisherigen
   Einstiegsfilter ein. Bleibt aus.
3. **`cooldown_h` und `min_stop_pct` erreichen die Referenz-Rendite bei fast halbem
   Rueckgang** — Rendite je Rueckgangspunkt 4,0 bzw. **4,7** gegen 2,6 der Referenz
   (bester Wert im ganzen Feld). Dazu 27 bzw. 56 Signale weniger.
4. **Zusammen sind sie schlechter als einzeln** (+26,4 %), alle vier deutlich schlechter
   (+14,7 %, Recall 39 %). Bestaetigt die Projektregel „mehr Filter = weniger Trades =
   mehr Gluecksabhaengigkeit". Es kommt hoechstens EINER in Frage.
5. **`min_stop_pct` ist der stabilere der beiden.** `cooldown_h` kippt von Platz 17 auf
   Platz 1 zwischen den Haelften (Zufallsverdacht); `min_stop_pct` liegt in beiden
   Haelften auf Augenhoehe mit der Live-Einstellung (H1 +22,6 gegen +20,7 %, H2 +10,9
   gegen +11,9 %). Die Rendite ist also NICHT der Punkt — der Punkt ist der Rueckgang.
   Dazu hat er eine mechanische Begruendung unabhaengig von der Tabelle: unter 2 %
   Abstand loest schon das normale Rauschen den Stop aus (Furkans Video-Beispiel: 3,59 %).
6. `liq_entry="boost"` hat sich zum ZWEITEN Mal als einzige Variante in beiden Haelften
   unter den besten 5 gehalten (H1 1., H2 4., +37,0 %).

**GEBAUT 2026-07-28 (zweiter Messlauf, ausstehend):** zwei Gitterzeilen
`+Mindestabstand 2 % +Liq-Konfluenz` und `+Sperre 48 h +Liq-Konfluenz` (27 Varianten).
Frage: Vertragen sich die beiden Kandidaten, oder fressen sie sich gegenseitig auf wie
„Sperre + Mindestabstand"? Beide greifen an derselben Stelle an (Einstiegs-Auswahl).

**ZWEITER MESSLAUF (2026-07-28 13:14 UTC, 27 Varianten) — die Hebel ERGAENZEN sich:**

| Variante | Rendite | Rueckgang | Rend./Rueckg. | Signale | H1 / H2 |
|---|---|---|---|---|---|
| bisher live (`LIVE +Stop`) | +32,2 % | −12,3 % | 2,6 | 212 | 5. / 9. |
| Mindestabstand allein | +33,0 % | −7,0 % | 4,7 | 156 | 3. / 12. |
| Liq-Konfluenz allein | +37,0 % | −12,3 % | 3,0 | 255 | 2. / 6. |
| **Mindestabstand + Liq-Konfluenz** | **+39,1 %** | **−6,9 %** | **5,7** | 187 | **1. / 3.** |
| Sperre 48 h + Liq-Konfluenz | +40,3 % | −9,3 % | 4,3 | 220 | 13. / 1. |

`Mindestabstand + Liq-Konfluenz` ist die **einzige Variante, die in BEIDEN Haelften unter
den besten 5 liegt** — beim vorherigen Lauf schaffte das keine der interessanten. Sie hat
zugleich die beste Rendite je Rueckgangspunkt im gesamten Feld. `Sperre + Liq-Konfluenz`
hat zwar 1,2 Punkte mehr Rendite, kippt aber wieder (H1 13. / H2 1.) und hat ein Drittel
mehr Rueckgang.

**LIVE GESCHALTET 2026-07-28 (Kaiser):** `min_stop_pct: 0.02` + `liq_entry: "boost"` in
`site/data/config.json`. `panel=True` in backtest.py auf dieselbe Zeile verschoben; die
Vergleichszeile „MEINE Einstellung ohne Flush" hat die neuen Schalter ebenfalls bekommen,
damit die zweite Spalte der Monatsuebersicht sich weiterhin NUR im Flush unterscheidet.
Ein Abgleich-Skript prueft Panel gegen config.json — beides stimmt ueberein.

**Antwort auf Kaisers Ausgangsfrage (Einstiege 31.05./16.06./23.06.):** Der Abstand
Einstieg→Invalidierung betrug 1,36 % / 2,76 % / **0,38 %**. Die 2-%-Regel haette ZWEI der
drei Positionen gar nicht erst eroeffnet — nicht wegen eines Marktzustands-Indikators,
sondern aus Geometrie. Insgesamt lagen 15 von 34 Positionen unter 2 %.
Bemerkenswert: Der intuitive Weg („pruefe, ob der Markt gesund ist") wurde gebaut und hat
in neun Monaten dreimal ausgeloest. Gewirkt hat die Regel, die den Markt gar nicht
anschaut. Eine Zustands-Schwelle laesst sich an ein Fenster anpassen, eine Mindest-Toleranz
nicht — sie stimmt aus Konstruktion.

**MONATSUEBERSICHT (2026-07-28):** `backtest.json` traegt jetzt zusaetzlich
`pnl_ohne_flush`; die Webseite zeigt beide Spalten nebeneinander (ohne Flush hervorgehoben
= sicherer Boden, mit Flush blasser = Obergrenze). Flush-Signale im Chart mit ⚡ und
eigener Farbe markiert, Legende ergaenzt. Die Signal-Erzeugung ist unveraendert — der
Flush wird weiter erzeugt, gesendet und gezeichnet.

#### Analyse, die dazu gefuehrt hat (2026-07-27)

Auslöser (Kaiser): *„Furkan steigt nur bei gesunden Indikatoren ein. Warum wurde am 23.06.,
16.06., 31.05. trotzdem gekauft?"* Vollständig in **docs/VERLUST-ANALYSE-2026-07-27.md**
Abschnitt 6c. Kurzfassung:

**BEFUND aus den Signal-Begründungen des Messlaufs:** Von 34 Ersteinstiegen hatten **16
gar keine Flow-Prüfung** (0.5-Level) und **16 das Muster NEUTRAL**; nur je 1× GESUNDER_TREND
und CAPITULATION_RESET. **32 von 34 Einstiegen ohne ein einziges gesundes Signal.**
Kaisers drei Beispiele: 31.05./16.06. = KAUF 1 (ungeprüft), 23.06. = KAUF 2 bei NEUTRAL;
alle drei zusätzlich mit sehr engem Stop (0,38–2,0 %).

**DREI URSACHEN IM CODE:**
1. Der KAUF-1-Zweig in `evaluate` enthält **keine einzige Flow-Bedingung** — bei den
   Live-Defaults geben `_trend_ok`/`_confluence_ok`/`_liq_entry_ok` bedingungslos True
   zurück. Betrifft 41 von 88 Kauf-Signalen.
2. `_confirm_long()` ist eine ODER-Kette (`Kapitulation ODER funding≤0 ODER cvd_up`);
   `funding ≤ 0` ist ein Alltagszustand → „+ Bestätigung" im Signaltext ist praktisch
   immer erfüllt und trägt keine Information. Furkan verlangt Konfluenz (Transkript 15:50).
3. **KONSTRUKTIONSFEHLER: `classify_pattern` kennt keinen ungesunden Abverkauf.** Drei der
   vier Muster verlangen `price_chg > 0`, das vierte beschreibt einen *gesunden* Absturz.
   Alles andere Fallende → `NEUTRAL`, und NEUTRAL blockiert nichts. Die einzige
   Einstiegssperre (`pattern != DERIVATE_PUMP`) verlangt steigenden Preis und kann beim
   Dip-Kauf **nie** greifen; die 34 Warnungen feuern ausnahmslos erst bei offener Position.

**ZU BAUEN (noch nicht gebaut):** `Muster 5 = ungesunder Abverkauf` als Einstiegssperre
(Preis fällt UND Spot-CVD fällt mit UND OI steigt UND Funding positiv UND keine
Long-Liquidations-Kaskade — das Spiegelbild von Muster 4, alle Daten liegen seit E9.1 vor)
+ `confirm_t1` = echte Flow-Prüfung für den 0.5-Level-Einstieg.

**GRENZEN, vorab gemessen:** „nur bei GESUNDER_TREND/CAPITULATION_RESET einsteigen" lässt
2 von 34 Positionen übrig (+1,8 %) — zu streng. „ohne 0.5-Level-Einstiege" kostet
+32,2 % → +15,7 %. Die 0.5-Einstiege müssen **gefiltert**, nicht **gestrichen** werden.

**WARUM NICHT WIE DIE ALTEN FILTER:** `strict_confirm` wurde in E8.5 als wirkungslos
abgehakt — mit der eigenen Notiz *„im Backtest fehlen OI+Futures-CVD"* und *„für Retest
mit echter Live-OI aufheben"*. Der Retest fand nie statt; echte OI-/Liq-Daten kamen erst
mit E9.1, der Zähler-Bug (E12) verzerrte zusätzlich. trend_filter/confluence waren
Preis-Struktur-Filter, hier geht es um Order-Flow.

**KAISERS VORGABE FÜR DEN BAU:** alles in EINEN Backtest-Lauf — Muster-5-Sperre,
`confirm_t1`, Sperre 48 h nach Stop und Mindest-Stop-Abstand 2 % (E12) einzeln und
kombiniert gegen die Live-Einstellung. Alle schaltbar, Default aus.

### E14 — Verkaufsseite gegen die NEUE Basis neu gemessen · Status: FERTIG, live geschaltet 2026-07-28

Auslöser (Kaiser): *„auf dem Weg nach oben sind Teilgewinne in den Bereichen vor den
Liquidationen sinnvoll — so beschreibt es Furkan, oder?"* Berechtigter Einwand: E9.11 und
E10.2 hatten genau das gemessen, aber gegen die **damalige** Basis — vor Mindest-Stopabstand
und Liq-Konfluenz.

| Variante | Rendite | Rückgang | Recall | H1 / H2 |
|---|---|---|---|---|
| Basis (Umstellung vom Vormittag) | +39,1 % | **−6,9 %** | 50 % | 2. / 5. |
| **+Verkauf unter dem letzten Hoch** | **+40,3 %** | −7,5 % | **57 %** | **1. / 4.** |
| +Verkauf an den Liquidations-Niveaus | +33,8 % | −7,8 % | 57 % | 3. / 22. |
| beides zusammen | +30,7 % | −7,9 % | 57 % | 5. / 24. |

**BEFUND: Der Satz „die Verkaufsseite ist auserzählt" (E10.2) galt nur für die damalige
Basis.** `high_exit="on"` kostete dort 3,9 Punkte (+28,3 gegen +32,2), bringt jetzt 1,2
(+40,3 gegen +39,1) und hebt den Recall von 50 auf 57 %. Erklärungs-HYPOTHESE (nicht
belegt): Früher wurden viele Positionen mit fast keinem Stop-Abstand ohnehin ausgestoppt —
früher Teilgewinn beschnitt dann nur die wenigen Gewinner. Seit die aussichtslosen
Einstiege unterbleiben, erreichen mehr Positionen den Widerstand tatsächlich.
**Lehre für künftige Messungen: Ein Mechanismus-Befund gilt immer nur gegen die Basis, gegen
die er gemessen wurde. Nach jeder Basis-Änderung sind verworfene Mechanismen erneut offen.**

Erstmals liegen **ZWEI** Varianten in beiden Hälften unter den besten 5 (Zufallserwartung
bei 30 Varianten: 0,8) — der Bericht meldet selbst, dass die Rangfolge trägt.

**Ehrlich zur Größe:** Knapper Fall. Risikobereinigt minimal schlechter (5,4 gegen 5,7
Rendite je Rückgangspunkt), 38 Signale mehr. Die tragenden Argumente sind die Platzierung
in beiden Hälften und dass es Furkans tatsächliches Verhalten abbildet.

**LIVE GESCHALTET:** `high_exit: "on"` in config.json; `panel=True` und die Vergleichszeile
„MEINE Einstellung ohne Flush" mitgezogen (Abgleich-Skript bestätigt Übereinstimmung).

**BERICHT VERBESSERT:** Die Robustheitsprüfung rechnet jetzt den Zufalls-Erwartungswert
(25 / Anzahl Varianten) neben das gemessene Ergebnis — ohne diesen Maßstab wurde „1 von 5
in beiden Hälften oben" regelmäßig überschätzt. Dazu der Hinweis, dass der maximale
Rückgang die belastbarere Kennzahl ist als die Platzierung.

**Heatmap-Test: 1 von 4–5 Beobachtungen da (27.08.2026).** Auswertung in
`heatmap-test/AUSWERTUNG.md`. Erste Beobachtung: Beim Teilverkauf „am letzten Hoch" am
26.08. (79.089 / 78.926) lag das große Cluster bei rund 81.400–81.800, also **über** dem
Verkaufspreis — spricht dafür, dass der Verkauf zu früh kam. Noch nicht entschieden, weil
der Kurs die Zone bis zum Screenshot nicht erreicht hatte. **Wichtiger Nebenbefund:** Die
Niveaus, die die Engine aus Coinalyze rechnet (78.121 und 77.851 in den Nachkauf-Signalen
desselben Tages), liegen dort, wo die Heatmap ebenfalls ein Band zeigt — erste unabhängige
Bestätigung, dass `liq_entry="boost"` echte Zonen trifft und keine Fantasiezahlen.
Screenshots von coinank.com bei Teilverkaufs-Nachrichten weiter in `heatmap-test/`. Ablauf:
`signal-app/ANLEITUNG-HEATMAP-TEST.md`. Frage: Lag das große Liquidations-Cluster ÜBER
unserem Verkaufspreis (dann hätte Warten mehr gebracht und eine echte, vorausschauende
Heatmap wäre ihr Geld wert) oder auf/unter ihm (dann trägt unser Rückwärts-Behelf)?
Das ist NICHT rückwirkend messbar — historische Heatmaps existieren nicht. Deshalb
Vorwärts-Sammlung, 4–5 Beobachtungen. `high_exit="on"` erzeugt mehr Teilverkäufe und damit
schneller genug Beobachtungen.

### E15 — Furkans Termine als P&L statt nur als Ähnlichkeits-Maßstab · Status: FERTIG (2026-07-28)

Kaisers Frage: *„Wie können wir testen, ob seine Methode noch besser ist?"* Die Trigger-Listen
dienten seit E2 nur als Recall-Maßstab; was sie an **Geld** gebracht hätten, war nie gerechnet.
`furkan_pnl()` in backtest.py schließt das (6 Tests + Gegenprobe an drei Stellen).

| Fenster | Furkan (Spanne über 12 Annahmen) | Furkan 33/33 | dessen Rückgang | Engine | Buy & Hold |
|---|---|---|---|---|---|
| kurz 19.11.–22.04. | −9,2 % bis +0,5 % | −7,3 % | −19,9 % | **+37,5 %** | −14,6 % |
| lang 25.09.–22.04. | −23,7 % bis −6,1 % | −19,7 % | −30,1 % | **+38,1 %** | −30,5 % |

**BEFUND: Die Ähnlichkeit zu Furkans Terminen trägt kein Geld.** Damit ist erklärt, warum
über Wochen JEDER Mechanismus, der den Recall hob, Rendite kostete (fünf auf der Verkaufs-,
vier auf der Einstiegsseite). **KONSEQUENZ: Recall bleibt als Beschreibung, taugt aber nicht
als Zielgröße.** Neue Ideen aus seinen Videos bleiben wertvoll (E14 war eine), müssen sich
aber an Rendite und Rückgang messen.

**GEGEN DIE ÜBERINTERPRETATION — drei Gründe, warum das NICHT „wir sind besser" heißt:**
(1) Die Engine-Zahl ist die beste von 30 Varianten, ausgewählt gegen genau dieses Fenster;
Furkan hat nicht gegen unsere Daten optimiert. Das ist strukturell unfair.
(2) Tranchengrößen und die Unterscheidung Teilgewinn/Stop fehlen in den Listen — 18 Punkte
Ergebnisunterschied allein durch geratene Größen.
(3) Furkan hat Buy & Hold um 11 Punkte geschlagen (−19,7 % gegen −30,5 %) — seine Methode
hat genau das geleistet, wofür sie gedacht ist: weniger verlieren.
Zwei Fenster, weil jedes eine Seite benachteiligt: das kurze schneidet Furkans
Positionsaufbau aus September/Oktober ab, das lange lässt die Engine vor Mitte November
ohne Open Interest laufen.

### E16 — Futures-CVD + Long-Short-Verhältnis (Coinalyze) · Status: GEBAUT 2026-07-28, MESSUNG AUSSTEHEND

**DURCHBRUCH bei der Datenlage.** Der Coinalyze-Endpunkt `ohlcv-history` liefert für
`BTCUSDT_PERP.A` pro 4h-Kerze `v` (Volumen) und `bv` (davon Taker-Käufe) — daraus folgt
**Futures-Taker-Delta = 2·bv − v**, dieselbe Formel wie für Spot. Damit ist die größte
Datenlücke des Projekts geschlossen: Futures-CVD fehlte seit E7 komplett (fapi.binance.com
sperrt US-Runner, HTTP 451), der Zweig `if has_fut:` in `classify_pattern` war seit dem
ersten Tag **toter Code**, Muster 2 lief nur über Ersatzmerkmale. Dazu neu:
`long-short-ratio-history` (28.07.: 65,1 % long / 34,9 % short) → neues FlowPoint-Feld
`long_pct`. Der Endpunkt `buy-sell-volume-history` existiert NICHT (404) — die Daten
stecken in der Kerzen-Historie.

**GEBAUT:** `fut_delta_by_ts` / `long_short_by_ts` in coinalyze.py (Parser gegen das echte
Antwortformat aus der Probe getestet); Verdrahtung in `main.py` (live) und
`backtest.py::build_series` (rückwirkend) — beide in EIGENEN try-Blöcken, ein Ausfall
lässt alles wie vor E16 laufen. Neuer Berichtsabschnitt **„Echte Futures-Daten: was bringen
sie?"**: dieselbe Variante, dieselben Kerzen, einmal mit und einmal ohne Futures-CVD —
der Unterschied ist damit allein den Daten zuzuschreiben. 96/96 Tests grün, Gegenprobe an
vier Stellen (jede Sabotage macht genau den zugehörigen Test rot).

**EINHEIT:** Die Volumina sind Basiswert-Mengen (BTC), nicht USD wie das Spot-Delta. Für
`classify_pattern` unerheblich, weil dort nur `_slope()` (relative Änderung) eingeht und
`spot <= fut / 3` zwei relative Werte vergleicht — die Einheit kürzt sich. Für absolute
Auswertungen müsste mit dem Preis multipliziert werden. Im Code dokumentiert.

**MESSERGEBNIS (2026-07-28 15:01 UTC, 2004 Futures-Punkte):**

| Datenlage | Recall | Präz. | Rendite | max. Rückgang | Signale |
|---|---|---|---|---|---|
| ohne Futures-CVD | 57 % | 39 % | +40,3 % | −7,5 % | 225 |
| mit echtem Futures-CVD | 57 % | 38 % | **+41,5 %** | −7,5 % | 215 |

Der Effekt ist **breit, aber klein** — und zwar über das ganze Gitter hinweg, nicht nur bei
der Live-Variante: durchgehend rund 8–10 % weniger Signale und +0,4 bis +1,2 Punkte Rendite
(nur Long 115→103 Signale/+11,4→+11,8 %; LIVE 207→198/+33,1→+33,6 %; Liq-Konfluenz
255→246/+37,0→+38,1 %). Dass es konsistent in dieselbe Richtung geht, macht es glaubwürdiger
als einen Einzelausschlag — aber die Größenordnung bleibt marginal. Ursache: Muster 2
(Derivate-Pump) feuert mit echten Daten häufiger und sperrt entsprechend mehr Einstiege.
Rückgang und Recall sind unverändert.

**DAMIT IST DIE OFFENE FRAGE ENTSCHIEDEN — und zwar negativ:** Neun gescheiterte
Order-Flow-Filter hatten zwei mögliche Erklärungen (Order Flow lässt sich nicht in feste
Regeln fassen, ODER unsere Daten waren zu grob). **Die zweite ist widerlegt.** Die
Ersatzmerkmale waren nah genug an den echten Daten; wo sich beide unterscheiden, geht es um
1 Punkt, nicht um den Unterschied zwischen „wirkungslos" und „wirksam". Die gescheiterten
Filter bleiben gescheitert, und es lohnt nicht, sie mit besseren Daten erneut aufzurollen.

**KONSEQUENZ:** Keine Umstellung nötig — die Daten fließen automatisch ein, es gibt keinen
Schalter. `long_pct` bleibt erfasst, aber von keiner Regel benutzt; nach diesem Befund
besteht kein Anlass, daraus eine weitere Regel zu bauen.

### BESCHLUSS 2026-07-28: Optimierungsphase erneut beendet

Nach E11 war die Optimierung schon einmal eingefroren; E12–E16 waren durch den Bugfix und
die neue Datenquelle berechtigt. Jetzt sind **drei große Fragen beantwortet** — warum die
Verluste entstanden (E12: zu enge Stops, nicht fehlende Indikatoren), ob Furkans Termine
mehr Geld bringen (E15: nein), ob es an den Daten lag (E16: nein).

**Inzwischen sind 30 Varianten gegen EIN Fenster verglichen.** Ab hier ist Überanpassung das
dominierende Risiko, nicht ein fehlender Mechanismus. Neue Erkenntnisse kommen aus dem
Live-Betrieb und aus dem Heatmap-Test, nicht aus weiteren Gitterzeilen.

Live eingefroren: nur Long · Kaufleiter · Flush core · Stop nachziehen · Mindest-Stopabstand
2 % · Liq-Konfluenz · Teilverkauf unter dem letzten Hoch. Backtest: +41,5 % / Rückgang
−7,5 % im Fenster 19.11.2025–28.07.2026 (Buy & Hold −30,7 %).

### E18 — Drei Mechanik-Fehler aus der Code-Durchsicht · Status: FERTIG (gemessen 2026-08-27)

Auslöser: Kaisers Bitte um eine vollständige Durchsicht („jede Datei, jede Zeile") und
seine Freigabe „ja, leg los". Vollständiger Bauplan: **docs/PLAN-E18-MECHANIK-FIXES.md**.
Vorab geprüft: Alle Code-Dateien im lokalen Ordner waren byte-identisch mit origin/main
(md5), nur `site/data/` war veraltet — deshalb konnte direkt lokal gearbeitet werden.

**E18.1 — Alle Schalter kommen jetzt an (Verhalten unverändert, sofort gültig).**
`run_engine()` reichte nur 11 von 20 `evaluate`-Parametern durch. `flush_entry`,
`tp_ladder`, `buy_ladder`, `conditional_stop`, `pivot_n`, `k_atr` und die drei
E8.5-Filter standen fest im Code — wer sie in `config.json` änderte, bewirkte nichts
und bekam keine Meldung. Gleichzeitig lasen `watch_flush()` und `zonen_vorschau()`
dieselben Werte sehr wohl aus der Datei: Die Flush-Wache hätte geschwiegen, während die
Engine weiter Flush-Signale erzeugt; die Vorschau hätte Zonen angekündigt, die die
Engine nicht handelt. Neu: Tabelle `EVAL_DEFAULTS` + `eval_params()` in main.py (ein
unbrauchbarer Wert fällt auf den Vorgabewert zurück und wird protokolliert, statt den
Lauf abzubrechen). **Nachgerechnet mit der echten config.json: kein einziger Parameter
ändert sich** — die Vorgabewerte sind mit den bisherigen Code-Defaults identisch.
Der neue Test `test_alle_evaluate_parameter_werden_durchgereicht` vergleicht die
Signatur von `evaluate` mit der Tabelle und schlägt fehl, sobald ein Parameter fehlt
oder ein Vorgabewert abweicht — der Fehler kann so nicht zurückkommen.

**E18.2 — `no_flip` (Default aus).** In 16 von 214 Signalen der Live-Variante wurde in
derselben Kerze aufgestockt UND teilverkauft, meist zum selben Preis (Quellen: 10×
Liquidations-Konfluenz, 9× Kaufleiter, 5× 0.786-Nachkauf, 1× GP-Aufstockung). Ursache:
Der Nachkauf prüft das Tief der Kerze, der Teilgewinn am letzten Hoch ihr Hoch; beide
Blöcke wissen nichts voneinander. Kosten: doppelte Gebühr auf ein Geschäft, das sich
selbst aufhebt, plus zwei widersprüchliche Telegram-Nachrichten. Mit `no_flip` entscheidet
in einer Kerze das erste Signal die Richtung. **Vollständige Ausstiege (Stop, Rest
schließen) sind nie betroffen**, Ersteinstiege aus FLAT ebenfalls nicht.

**E18.3 — `freeze_targets` (Default aus).** `pos.retrace_extreme` wurde auch nach dem
ersten Teilgewinn fortgeschrieben; ein späteres Tief senkte damit ext1/ext2. Nachgestellt:
Ziel 1.618 von 301,8 auf 257,8 — unter das ursprüngliche 1.0-Ziel. Auch mit `trail_stop`
bleibt der milde Fall (301,8 → 286,8 ohne Stop-Signal). Passt zum Befund, dass
`TEILVERKAUF_2` im ganzen Messfenster genau **einmal** vorkam. Neu: Feld
`Position.ziel_extrem`, gesetzt beim ersten realisierten Teilgewinn, persistiert in
state.json, zurückgesetzt in `_reset_position`. Das laufende `retrace_extreme` bleibt
unverändert, damit die Mehrtages-Kaufleiter sich nicht ändert; `pos_to_state` zeichnet
die Ziele aus der eingefrorenen Referenz, sonst zeigte der Chart andere Linien als die
Engine handelt.

**Tests: 128/128 grün** (vorher 115). **Gegenprobe gemacht:** jeder der drei Mechanismen
einzeln im Code ausgehebelt → jedes Mal wird genau der zugehörige Test rot
(E18.1: nennt die fehlenden Parameter beim Namen; E18.2: beide Richtungs-Tests;
E18.3: der Einfrier-Test). Dazu je ein Test, der den ALTEN Zustand dokumentiert — ohne
Schalter läuft alles wie bisher.

**Backtest-Gitter: 30 → 33 Varianten** (`+kein Gegengeschaeft je Kerze`,
`+Ziele festhalten`, `+beides`), jeweils auf der aktuellen Live-Einstellung aufgesetzt.

**MESSERGEBNIS (BACKTEST.md, 2026-08-27 10:52 UTC, 33 Varianten).** Fenster
19.12.2025–27.08.2026 (2295 Kerzen), Referenz = Live-Einstellung
`NEU-LIVE +Verkauf unter dem letzten Hoch` +35,5 % / Rückgang −7,5 % / 202 Signale.

| Variante | Rendite | Rückgang | Signale | Platz H1 / H2 |
|---|---|---|---|---|
| Referenz (live) | **+35,5 %** | −7,5 % | 202 | 15. / 5. |
| +kein Gegengeschäft je Kerze (`no_flip`) | +31,4 % | −7,5 % | 200 | 20. / 7. |
| +Ziele festhalten (`freeze_targets`) | +29,9 % | −7,5 % | 209 | 27. / 2. |
| +beides | +34,0 % | −7,5 % | 208 | 22. / 4. |

**BEIDE BLEIBEN AUS.** Keiner der zwei Schalter erreicht die Referenz, und keiner senkt den
Rückgang (überall −7,5 %). Bemerkenswert an `no_flip`: Er entfernt nur **2** der 202 Signale,
kostet aber 4 Punkte — die 16 Gegengeschäfte waren also nicht die Kostenstelle, für die ich
sie gehalten habe; was sich ändert, sind die Folgepfade der Zustandsmaschine. Die
Gebührenersparnis von 16 halben Tranchen ist gegen Pfadänderungen dieser Größe bedeutungslos.
`freeze_targets` erzeugt sogar mehr Signale (209 statt 202), weil Positionen ohne den zweiten
Teilgewinn länger offen bleiben.

**Die Robustheitsprüfung sagt in diesem Lauf gar nichts — und zwar für alle 33 Varianten:**
„In BEIDEN Hälften unter den besten 5: keine einzige" (Zufallserwartung 0,8). Hälfte 2
(24.04.–27.08.) liegt komplett zwischen −0,4 % und +3,8 %; dort ist die Rangfolge Rauschen.
Der Bericht zieht selbst die richtige Konsequenz: nur den groben Hebeln trauen.

**Nicht vergleichbar mit dem Lauf vom 29.07.:** Das Fenster hat sich an BEIDEN Enden
verschoben (19.12. statt 20.11. vorn, 27.08. statt 29.07. hinten) und Buy & Hold steht jetzt
bei −9,8 % statt −26,2 %. Das ist Befund 4 der Durchsicht in Reinform.

**NEUE FRAGE AUS DIESEM LAUF (wichtiger als beide Schalter):** Im August hat die Engine
**+0,4 %** gemacht, während Bitcoin von 64.500 auf 78.800 gestiegen ist (+22 %). Auch in der
gesamten zweiten Hälfte kommt keine einzige Variante über +3,8 %. Die Strategie ist in
Bärenmärkten geprüft und hat dort geliefert; wie sie sich in einer Rally verhält, hat bisher
nie jemand gemessen. Mögliche Ursachen (ungeprüft): Die Engine steht die meiste Zeit in
Teilpositionen (aktuell T1 = 25 %), die Teilgewinne greifen früh, und Dip-Einstiege bekommen
in einem Markt ohne tiefe Rücksetzer selten eine Gelegenheit. **Das wäre die nächste
lohnende Untersuchung** — nicht ein weiterer Schalter.

**OFFEN:** (1) Die Aufwärts-Frage oben untersuchen. (2) Befund 4 aus der Durchsicht
(Rückgang zwischen den Signalen mitmessen). (3) Variante „Verkaufsseite hat Vorrang"
für `no_flip` — nach diesem Ergebnis nur noch, wenn die Telegram-Widersprüche stören;
als Rendite-Hebel ist die Idee gemessen und erledigt.

**NICHT in diesem Paket:** Der maximale Rückgang wird in `simulate()` nur an
Signalzeitpunkten gemessen — Buchverluste zwischen zwei Signalen fehlen. Das ändert keine
Signale, aber alle bisherigen Rückgangs-Zahlen, und gehört deshalb in eine eigene Etappe.
Ebenso offen: kein `.gitattributes` (CRLF erzeugt Schein-Änderungen an ganzen Dateien),
`heatmap-test/` weiter leer, das Makro-Video vom 02.08.2026 unausgewertet.

### E19 — Das Referenz-Bein (aus Furkans Video vom 02.08.2026) · Status: GEBAUT 2026-08-27, MESSUNG AUSSTEHEND

Vollständige Auswertung: **docs/FURKAN-UPDATE-2026-08-02.md**. Kern in drei Sätzen:

**Unsere Fib-Mechanik stimmt exakt mit seiner überein.** Aus seinen zwei genannten Zahlen
(Nachkaufzone „61.300 bis 61.000") ließ sich sein Bein zurückrechnen: Tief 57.800,19
(01.07.2026) → Hoch 66.956,15 (21.07.2026). Unsere Formel ergibt darauf 0.618 = 61.298 und
0.65 = 61.005. Kein Zahlenunterschied.

**Was auseinandergeht, ist die Wahl des Beins.** Am selben Tag zeichnete unsere Engine
(Repo-Historie, Commit d023500) das Bein 65.409 → 62.275 — zwei Tage, 4,8 %, Richtung
SHORT, also bei `bias_short=false` unhandelbar. Furkan zeichnete drei Wochen und 15,8 %
nach oben.

**Folge, messbar:** Vom 27.07. bis 25.08.2026 war die Engine **durchgehend FLAT** —
genau der Monat, in dem Bitcoin von 63.000 auf 78.800 stieg. Median-Beinlänge der Vorschau
in diesem Monat: 4,0 %. Ursache ist eine Verkettung von drei je für sich richtigen Regeln:
`last_significant_impulse` nimmt das jüngste statt des größten Beins → kleines Bein heißt
kleiner Abstand Golden Pocket → Invalidierung (bei 1,9 % Bein rund 1,2 %) → `min_stop_pct`
(2 %) verwirft den Einstieg. Die Engine zeichnet Beine, die für ihre eigene
Mindestanforderung zu klein sind.

Das ist zugleich die Antwort auf die offene Frage aus E18 („warum nur +0,4 % im August?").
Nicht die Gewinnmitnahme war das Problem, sondern der fehlende Einstieg.

**Unsere eigene Spezifikation fordert die Lösung bereits** (STRATEGIE.md §4.1): Punkt 3
verlangt den jüngsten signifikanten Impuls *in Trendrichtung* (Trendrichtung wird nirgends
geprüft), Punkt 4 *beide Ebenen überwachen, 4h und 1D*. Der Schalter `confluence` (E8.5,
gemessen und verworfen) ist NICHT diese Umsetzung — er nutzt die 1D-Zone als Filter für
4h-Setups, nicht als eigene Einstiegszone.

**AUS DEN VIDEO-FRAMES (nachgereicht, `Videos/260802/frames/`):** Sein Raster ist direkt
ablesbar und deckt sich bis auf 5–15 $ mit unserer Rechnung (0.618 = 61.292,8 gegen
61.298; 0.65 = 61.000,4 gegen 61.005 — die Differenz ist BingX-Perp gegen Binance-Spot).
Entscheidend ist ein Detail, das im Transkript nicht steht: **Er führt zwei Fib-Raster
gleichzeitig** — das große Aufwärts-Bein für die Kaufzone darunter und ein zweites vom
selben Hoch abwärts als Widerstand. Er muss also gar nicht wählen; unsere Engine muss, und
sie wählte das kleine, abwärtsgerichtete. Er arbeitet dabei auf 2h (TradingView) bzw. 1h
(OKX), nicht auf 4h — der Zeitrahmen ist aber nicht die Ursache, die Auswahl ist es.

**GEBAUT 2026-08-27 (alle vier Default aus, Live-Verhalten unverändert):**
- `bein_richtung="bias"` — sucht nur Beine in der handelbaren Richtung. Wirkt nur, wenn
  genau eine Richtung erlaubt ist (live: nur Long). Trifft die 17 Stillstands-Tage direkt.
- `min_bein_pct` — harte Untergrenze für die Beinlänge (Vorschlag 0.05, hergeleitet aus
  der 35–38-%-Regel gegen `min_stop_pct` = 2 %).
- `bein_wahl="groesstes"` — unter den letzten 12 Pivots das Bein mit der größten Spanne.
- `be_im_plus` — Break-even-Stop, sobald die Position einmal im Plus stand (neues Feld
  `Position.be_aktiv`, in state.json persistiert). Deckt Furkans Aufstockungs-Regel und
  Punkt 2 der Verlust-Analyse ab (44 % der Verlustsumme, nie gebaut).

Dazu: `zonen_vorschau()` benutzt jetzt dieselbe Parameter-Aufbereitung wie die Engine
(`eval_params`), damit die Telegram-Vorschau nie wieder andere Zonen ankündigt als die
Engine handelt. **135/135 Tests grün** (vorher 128), Gegenprobe für jeden der vier
Mechanismen gemacht — jede Sabotage macht genau die zugehörigen Tests rot.
Backtest-Gitter: 33 → **40 Varianten** (jeder Hebel einzeln, dazu Bein-Richtung +
Mindest-Bein und die Kombination mit Break-even).

**NICHT gebaut:** 1D-Zonen als eigener zweiter Zonensatz (§4.1 Punkt 4 wörtlich). Das ist
der größere Eingriff — die Zustandsmaschine kennt heute genau eine Zonenreihe je Position.
Erst messen, ob `bein_richtung` und `min_bein_pct` die Blockade schon lösen.

**MESSERGEBNIS (BACKTEST.md, 2026-08-27 11:45 UTC, 40 Varianten).** Referenz =
Live-Einstellung `NEU-LIVE +Verkauf unter dem letzten Hoch`.

| Variante | Rendite | Rückgang | Rend./Rückg. | Recall | Signale | H1 / H2 |
|---|---|---|---|---|---|---|
| Referenz (live) | +35,4 % | −7,5 % | 4,7 | 62 % | 202 | 15. / 8. |
| **+Mindest-Bein 5 %** | **+37,4 %** | **−6,9 %** | **5,4** | **71 %** | 241 | 25. / **1.** |
| +Bein in Handelsrichtung | +32,6 % | −8,9 % | 3,7 | 62 % | 238 | 24. / 3. |
| +beides zusammen | +38,6 % | −8,2 % | 4,7 | 52 % | 227 | 22. / 2. |
| +größtes Bein | +17,6 % | −7,3 % | 2,4 | 43 % | 103 | 30. / 21. |
| +Break-even im Plus | +15,9 % | **−5,3 %** | 3,0 | 52 % | 214 | 36. / 11. |

**1. Die Erwartung ist eingetroffen, und zwar genau dort, wo sie hingehörte.** In Hälfte 2
(24.04.–27.08., die Aufwärtsphase) belegen die E19-Hebel die Plätze **1, 2 und 3**; die
Live-Einstellung liegt dort auf 8. In Hälfte 1 (Bärenmarkt) ist es umgekehrt: Referenz
Platz 15, die Hebel auf 22–25. **Sie tauschen Bärenmarkt-Rendite gegen
Aufwärtsmarkt-Rendite** — kein universelles „besser". Das bestätigt die Diagnose
(Stillstand in der Rally), macht die Hebel aber regime-abhängig.

**2. `min_bein_pct = 0.05` ist die einzige Variante im ganzen Feld, die die
Live-Einstellung in ALLEN drei Kennzahlen gleichzeitig schlägt:** mehr Rendite (+2,0),
weniger Rückgang (−0,6), höherer Recall (62 → 71 %, der beste Wert im Feld). Dazu 39
Signale mehr — der Stillstand löst sich also tatsächlich auf. Rendite je Rückgangspunkt
5,4, ebenfalls Bestwert.

**3. `bein_wahl="groesstes"` ist klar schlechter** (+17,6 %, nur 103 statt 202 Signale) —
trotz der höchsten Präzision im Feld (61 %). Die bekannte Falle: wenige Signale, hohe
Trefferquote, wenig Geld. In Hälfte 2 sogar negativ. Bleibt aus, Schalter bleibt im Code.

**4. `be_im_plus` ist der teuerste Hebel im ganzen Projekt: −19,5 Punkte Rendite**
(+15,9 % gegen +35,4 %) für 2,2 Punkte weniger Rückgang. Risikobereinigt 3,0 gegen 4,7.
Das ist bemerkenswert, weil es Furkans ausdrückliche Regel ist und die Verlust-Analyse vom
27.07. sie mit „44 % der Verlustsumme" veranschlagt hatte. Die Rechnung stimmt trotzdem
nicht: Positionen, die im Plus standen und zurückfallen, werden sofort geschlossen — die
Runner sterben, bevor sie laufen. **Erwartung widerlegt, Schalter bleibt aus.**

> **Berichtigt 26.09.2026 (E43.7, Gesamtprüfung Teil B Punkt 7):** Lesefehler. `be_im_plus` ist **nicht** Furkans Regel — ihm fehlt die Vorbedingung „Gewinne schon realisiert“. Furkans Regel entspricht `trail_stop` (live). Auf der heutigen Live-Basis gemessen (E43.8): `be_im_plus` +18,0 % gegen +35,3 %. Siehe `wissens-layer\02_status\GEMESSEN-UND-ENTSCHIEDEN.md`.

**5. Robustheit: 0 von 40 Varianten in beiden Hälften unter den besten 5**
(Zufallserwartung 0,6). Die Rangfolge trägt in diesem Lauf wieder nichts. Wer
`min_bein_pct` einschaltet, tut das NICHT wegen der Tabelle, sondern wegen der Mechanik:
Der Abstand Golden Pocket → Stop ist konstruktiv 35–38 % der Beinlänge, `min_stop_pct`
verlangt 2 %, also braucht es ein Bein von ~5,5 %. Diese Rechnung gilt unabhängig von
jedem Zeitfenster — wie damals bei `min_stop_pct` selbst.

**LIVE GESCHALTET 2026-08-27 (Kaiser): `min_bein_pct: 0.05`** in `site/data/config.json`.
`panel=True` in backtest.py ist auf die Zeile *NEU-LIVE +Mindest-Bein 5 %* gewandert, die
Vergleichszeile „MEINE Einstellung ohne Flush" hat den Schalter ebenfalls bekommen — die
Monatsübersicht unterscheidet sich damit weiterhin NUR im Flush. Neu ist ein Test, der
diese Regel dauerhaft absichert: `test_panel_variante_entspricht_der_live_einstellung`
vergleicht die Panel-Zeile mit `config.json` und wird rot, sobald beide auseinanderlaufen
(Gegenprobe gemacht). Bisher stand diese Regel nur als Kommentar im Code — und genau
solche Merk-Regeln waren der Grund für E18.1. `bein_richtung`, `bein_wahl` und
`be_im_plus` bleiben ausgeschaltet. **137/137 Tests grün.**

Live-Einstellung ab jetzt: nur Long · Kaufleiter · Flush core · Stop nachziehen ·
Mindest-Stopabstand 2 % · Liq-Konfluenz · Teilverkauf unter dem letzten Hoch ·
**Mindest-Beinlänge 5 %**.

*Die Abwägung, die dahinterstand:* Dafür:
einzige Variante, die in allen drei Kennzahlen vorn liegt; behebt einen echten
Regelkonflikt; löst den gemessenen Stillstand (Platz 1 in der Aufwärtshälfte). Dagegen:
kostet im Bärenmarkt rund 5 Punkte (H1 +26,4 % gegen +31,5 %), und die Robustheitsprüfung
stützt in diesem Lauf gar nichts. Bei Umstellung muss `panel=True` in backtest.py auf
dieselbe Zeile wandern, und die Vergleichszeile „MEINE Einstellung ohne Flush" bekommt den
Schalter ebenfalls.

**Gegenrechnung, ein Datenpunkt:** Mit seinem Bein hätte das 0.5-Level bei 62.378 gelegen;
das Tagestief am 01.08. war 62.275, der Stop-Abstand 7,3 %. Der Einstieg wäre gekommen.

### E20 — Widerstandsmarken + Plan zur laufenden Position · Status: GEBAUT 2026-08-27, MESSUNG AUSSTEHEND

Auslöser: Kaisers Frage *„ich kann doch nach Kerzenschluss ggf. nicht mehr zu dem genannten
Preis kaufen bzw. verkaufen … kann man nicht, wie auch Furkan das tut, sagen: ich werde an
diesem Kurs Teilgewinne realisieren?"* — plus die Auswertung des Videos vom 03.08.2026
(`docs/FURKAN-UPDATE-2026-08-03.md`), die genau das belegt.

**E20.1 — Das zweite Fib-Raster (`gegen_zonen`).** Furkan führt zwei Raster gleichzeitig:
eines in Handelsrichtung für die Kaufzonen darunter, eines GEGEN die Richtung für die
Widerstände darüber. Am 03.08. nennt er *„Golden Pocket 64.200 bis 64.300, da könnte
Widerstand vorherrschen"* — unsere Engine hatte am Vorabend für dasselbe Bein
**64.212–64.312** in der Vorschau stehen. **Zwölf Dollar daneben: Sie sah die Zone, benutzte
sie nur nicht.** Neu: `gegen_zonen()` liefert die Levels des jüngsten signifikanten Beins
entgegen der Handelsrichtung; `widerstand_marken()` schreibt sie in `state.json`; der Chart
zeichnet sie in eigener Farbe. Dazu der Schalter `widerstand_exit` (Default aus): Teilgewinn
am Golden Pocket der Gegenbewegung — diese Marke liegt unter dem letzten Hoch und wird
deshalb früher erreicht als `high_exit`.

**E20.2 — Plan-Nachricht (`positions_plan` + `format_plan`).** Bei offener Position schickt
Telegram jetzt ALLE Marken auf einmal — Nachkaufzonen, Teilgewinn-Stufen, Widerstand, Stop,
je mit Tranchengröße. Gesendet wird nur, wenn sich eine Marke um mehr als 0,25 % verschiebt
oder eine hinzukommt (`plan_geaendert`), nicht bei jedem Lauf. Das ist das Gegenstück zur
Vorschau, die dasselbe für den Einstieg tut: **Beide Seiten lassen sich damit als
Limit-Order vorlegen, statt einer Nachricht hinterherzulaufen.** Abschaltbar über
`plan_telegram`.

**Der Test, der das Ganze zusammenhält:** `test_plan_marken_stimmen_mit_der_engine_ueberein`
prüft, dass die im Plan genannte Marke „Ziel 1.0" die Engine dort auch wirklich auslöst —
und zwar zu genau diesem Preis. Ein Plan, der andere Zahlen nennt als die Engine handelt,
wäre schlimmer als gar keiner. Gegenprobe gemacht (Marke 5 % verschoben → Test rot).

**145/145 Tests grün** (vorher 141). Gegenproben für alle vier Mechanismen; zwei Tests
mussten dafür nachgeschärft werden, weil die erste Fassung die Sabotage nicht bemerkte.
Backtest-Gitter: 40 → **42 Varianten** (`widerstand_exit` allein und statt `high_exit`).

**MESSERGEBNIS (BACKTEST.md, 2026-08-27 14:39 UTC, 42 Varianten):**

| Variante | Rendite | Rückgang | Rend./Rückg. | Recall | Signale | H1 / H2 |
|---|---|---|---|---|---|---|
| Referenz (live, Mindest-Bein 5 %) | **+37,9 %** | −6,9 % | **5,5** | 71 % | 241 | 25. / 2. |
| +Widerstand zusätzlich | +30,4 % | **−6,2 %** | 4,9 | 71 % | 271 | 35. / 4. |
| +Widerstand statt Verkauf am letzten Hoch | +33,0 % | −6,8 % | 4,9 | 67 % | 227 | 30. / **1.** |

**`widerstand_exit` bleibt AUS.** Beide Varianten kosten Rendite (−7,5 bzw. −4,9 Punkte)
und sind auch risikobereinigt schlechter. Der Mechanismus erzeugt 30 zusätzliche Signale —
er verkauft früher und schneidet damit Positionen ab, die noch weiterliefen. Dasselbe
Muster wie bei `be_im_plus` und `no_flip`: früher aussteigen kostet.

**Wieder regime-abhängig:** In Hälfte 2 (Aufwärtsphase) landen die beiden auf Platz 4 und
**Platz 1** — besser als die Live-Einstellung auf Platz 2. In Hälfte 1 (Bärenmarkt) auf 35.
und 30. Robustheitsprüfung: 0 von 42 Varianten in beiden Hälften unter den besten 5
(Zufallserwartung 0,6) — die Rangfolge trägt wieder nichts.

**Der eigentliche Gewinn dieser Etappe steckt nicht im Schalter, sondern in der Anzeige.**
Die Widerstandszone steht seit heute **immer** im Plan und im Chart, unabhängig vom
Schalter (Kaisers Einwand: sonst wäre ausgerechnet die neue Marke im Normalbetrieb
unsichtbar geblieben). Sie kostet dort nichts und liefert genau die Information, die
Furkan zuerst nennt, wenn er über Teilgewinne spricht. Ob im Einzelfall dort verkauft
wird, entscheidet Kaiser — die Messung sagt nur, dass es sich nicht lohnt, es MECHANISCH
bei jedem Mal zu tun. Derselbe Unterschied wie bei `be_im_plus`: Furkan wählt aus, die
Engine würde stur handeln.

**OFFEN:** Kaisers ursprüngliche Frage ist nur halb beantwortet — die Einzelsignale kommen
weiterhin zusätzlich zum Plan (~40 Nachrichten im Monat statt 27). Ob sie für Marken
entfallen sollen, die schon im Plan standen (dann nur noch Stop, neue Struktur,
Flush-Warnung: ~20 im Monat), entscheidet er, sobald er die Plan-Nachricht ein paar Tage
im Einsatz hatte.

### E21 — Nie ganz aussteigen (Kaisers Beobachtung) · Status: GEBAUT 2026-08-27, MESSUNG AUSSTEHEND

Auslöser (Kaiser): *„Furkan hat durchschnittlichen Einstieg bei rund 59.000, ist aber noch
immer investiert und tätigt nur Teilverkäufe. So konnte er auch den Anstieg im August voll
mitnehmen. Wir hingegen steigen ein, steigen aus, immer wieder."*

**Die Zahlen dazu** (aus `backtest_signals.json` rekonstruiert):

| | Furkan | Engine |
|---|---|---|
| Positionen | eine, seit ~01.07. | **22 in 8 Monaten** |
| Zeit im Markt | durchgehend | **45 % — 55 % der Zeit ganz draußen** |
| Haltedauer | 8 Wochen und läuft | Median 5 Tage, längste 12,5 |
| Positionsende | keins | 12× Gegen-Muster, 9× Stop |

Rückkauf nach vollständigem Ausstieg: 14× tiefer, 7× höher, Median −0,9 %. Im
Bärenmarkt-Fenster hat sich das Aussteigen also gelohnt — der schlechteste Einzelfall
kostete aber **+14,4 %** Rückkaufpreis.

**Der Denkfehler, den das aufdeckt:** Alle bisher gemessenen Verkaufs-Mechanismen
(`be_im_plus`, `widerstand_exit`, `freeze_targets`, `no_flip`, `liq_exit`, `high_exit`)
machen die Engine **schneller draußen** — und jeder einzelne kostete Rendite. Die
Gegenrichtung wurde nie geprüft. Dabei ist sie der eigentliche Unterschied zu Furkan: Er
sagt den Anstieg nicht voraus, er bleibt drin, weil sein Stop über dem Einstand liegt und
er nichts mehr verlieren kann. **Das ist keine Prognose, sondern Positionsführung.**

Zur Indikatoren-Frage, die Kaiser dabei stellt: Nein, vorhersehen lässt es sich nicht — neun
Order-Flow-Filter sind gemessen und gescheitert, und E16 hat ausgeschlossen, dass es an zu
groben Daten lag.

**GEBAUT (beide Default aus):**
- `rest_halten` — der Rest wird bei Gegen-Muster nicht mehr verkauft, er läuft bis zum Stop.
- `neustart_mit_rest` — neuer Einstieg, während der Rest noch läuft. Ohne das wäre
  `rest_halten` eine Blockade: Die Engine steigt sonst nur aus FLAT ein (Befund E9.9). Der
  alte Bestand bleibt im Durchschnitts-Einstand, die Zähler des neuen Zyklus starten bei null.

Dafür wurde der Einstiegs-Block in `evaluate` als Funktion `_versuche_einstieg()`
ausgelagert — er wird jetzt an zwei Stellen gebraucht. Der Neustart läuft **nach** dem
Positions-Management (ein Stop in derselben Kerze hat Vorrang) und **vor** der
Einstands-Fortschreibung.

**151/151 Tests grün.** Gegenproben für beide Schalter plus eine dritte für den Bestand
beim Neustart — diese schlug zuerst NICHT an, weil der Test nur `entry_pct > 75` prüfte;
jetzt prüft er den exakten Wert 100 (75 alter Bestand + 25 neue Tranche). Ohne die
Verschärfung wäre nicht aufgefallen, wenn der alte Bestand beim Neustart verlorengeht.

**Backtest-Gitter: 42 → 45 Varianten** (Rest halten, Rest halten + Neustart, Neustart allein).

**MESSERGEBNIS (BACKTEST.md, 2026-08-27 19:52 UTC, 45 Varianten):**

| Variante | Rendite | Rückgang | Rend./Rückg. | Recall | Signale | H1 / H2 |
|---|---|---|---|---|---|---|
| Referenz (live) | +37,9 % | −6,9 % | 5,49 | 71 % | 242 | 25. / 5. |
| **+Neustart mit Rest allein** | **+39,0 %** | **−6,9 %** | **5,65** | 71 % | 240 | 26. / 3. |
| +Rest halten +Neustart | +39,4 % | −8,2 % | 4,80 | 71 % | 236 | 31. / 1. |
| +Rest halten allein | +18,9 % | −6,9 % | 2,74 | 33 % | **84** | 44. / 2. |
| *(alt)* Rest-Freigabe (E9.9) | +22,2 % | −13,0 % | 1,71 | 62 % | 211 | 7. / 45. |

**Meine Erwartung war falsch — und das ist der Erkenntnisgewinn.** Ich hatte auf
`rest_halten` gesetzt (länger drin bleiben). Der wirksame Hebel ist der andere:
**`neustart_mit_rest`**, also nicht „länger drin bleiben", sondern **„schneller wieder rein
dürfen"**. `rest_halten` allein ist sogar schädlich: 84 statt 242 Signale — der liegende
Rest blockiert die Engine genau so, wie E9.9 es beschrieben hatte.

**`neustart_mit_rest` ist die einzige Variante im ganzen Feld, die die Live-Einstellung in
der Rendite schlägt, ohne Rückgang, Recall oder Signalzahl zu verschlechtern** (+1,1
Punkte, identischer Rückgang −6,9 %, gleicher Recall 71 %). Rendite je Rückgangspunkt
**5,65** — bester Wert im Feld. Und sie liegt in BEIDEN Hälften auf Referenz-Niveau oder
knapp darüber (H1 26. gegen 25., H2 3. gegen 5.); das war bei keinem der vorherigen Hebel so,
die immer in einer Hälfte gewannen und in der anderen verloren.

**Das tragende Argument steht wieder außerhalb der Tabelle:** Für genau dieses Problem — der
Rest blockiert neue Einstiege — gab es seit E9.9 schon eine Lösung, `release_stale_rest`,
die den Rest zum Marktpreis wegwirft. Sie steht im selben Lauf bei **+22,2 % / −13,0 %**.
`neustart_mit_rest` löst dasselbe Problem, ohne etwas zu verkaufen, und ist dabei 17 Punkte
besser. Es ist keine neue Wette, sondern der bessere Weg für eine bekannte Schwäche.

Die Kombination mit `rest_halten` hat 0,4 Punkte mehr Rendite — das ist Rauschen —, aber
1,3 Punkte mehr Rückgang. Das ist keins.

**Robustheit:** 0 von 45 Varianten in beiden Hälften unter den besten 5 (Erwartung 0,6).
Zum vierten Mal in Folge trägt die Rangfolge nichts; die Entscheidung stützt sich auf den
Vergleich mit `release_stale_rest` und darauf, dass keine Kennzahl schlechter wird.

**OFFEN zur Entscheidung durch Kaiser:** `neustart_mit_rest: true` live schalten,
`rest_halten` aus lassen. Bei Umstellung wandert `panel=True` auf die Zeile
*LIVE +Neustart mit Rest (ohne Halten)*; der Test
`test_panel_variante_entspricht_der_live_einstellung` erzwingt das ohnehin.

### E22 — Beteiligung an der Marktbewegung · Status: FERTIG (2026-08-27)

Auslöser (Kaiser): *„Im August ist der Preis von BTC über 20 % gestiegen. Das hätte nur ein
Wachstum von 1,1 % bei uns bewirkt?"* — die Verwechslung zweier Zahlen führte zur richtigen
Frage. Die Gesamtrendite verrät nicht, WO sie herkommt.

**Gemessen (Monatsrenditen der Live-Variante gegen Bitcoin, Dez 25 – Aug 26):**

| | Bitcoin | Engine | Beteiligung |
|---|---|---|---|
| 4 steigende Monate | +48,3 % | +23,4 % | **48 %** |
| 5 fallende Monate | −52,0 % | **+9,9 %** | **−19 %** |

Die Engine nimmt also knapp die Hälfte der Anstiege mit und macht Rückgänge nicht nur nicht
mit, sondern verdient in ihnen. **Für einen fallenden Markt ist das ein sehr gutes Profil.**

**Das Muster dahinter ist wichtiger als der Durchschnitt:**

| Monat | Anstieg BTC | davon eingefangen |
|---|---|---|
| März | +2,0 % | 310 % |
| April | +11,8 % | 100 % |
| Juli | +7,3 % | 33 % |
| August | **+27,2 %** | **11 %** |

**Je größer der Anstieg, desto weniger fängt die Engine ein.** Bei kleinen Bewegungen
schlägt sie den Markt (sie handelt die Schwankungen), bei einer echten Rally nimmt ihr die
gestaffelte Gewinnmitnahme genau die Position weg, die sie bräuchte. Das ist Bauart, kein
Fehler — ein Dip-Kauf-System mit Teilverkaufsleiter ist auf Seitwärts- und Abwärtsphasen
ausgelegt. Es entscheidet aber, wofür das Werkzeug taugt: als Schutz in fallenden Märkten
sehr gut, als Hauptmotor in einem Bullenmarkt nicht.

**Einordnung zum Vergleich mit Furkan:** Er hat ZWEI Töpfe — ein Spot-Portfolio, das er in
der MVRV-Valuezone nachkauft und liegen lässt (das hat den August voll mitgenommen), und
daneben die Futures-Position. Unsere Engine ist nur das Gegenstück zum zweiten Topf. Wir
haben also einen Teil mit einem Ganzen verglichen.

**GEBAUT:** `simulate()` schreibt je Monat zusätzlich `btc_pct` mit (aus denselben Kursen
und Zeitpunkten wie die Equity, damit der angeschnittene erste und letzte Monat nicht
verzerren); `beteiligung()` wertet aus; der Bericht hat einen neuen Abschnitt
**„Was fängt die Engine von der Marktbewegung ein?"** mit Monatstabelle, beiden Kennzahlen
und der Spalte *davon eingefangen*. 154/154 Tests grün, zwei Gegenproben. Näherung
dokumentiert: Monatsrenditen addiert statt verkettet (für diese Kennzahl üblich).

**Keine Regel geändert** — die Kennzahl misst nur. Ab jetzt zeigt jeder Backtest-Lauf, ob
eine Änderung die Aufwärts-Beteiligung verbessert oder bloß den Rückgang schönt.

## Bewusst NICHT gemacht (mit Begründung)

- **Warnungen NICHT entrümpelt oder abgeschaltet** (Kaiser 2026-07-28). Befund: 34 der
  212 Signale sind Warnungen (16 %), alle mit Tranche 0 % und identischem Text, verteilt
  auf nur 15 Episoden — 19 sind also Wiederholungen (12.03.: vier Nachrichten in 16 h).
  Kaisers Frage „was bringt mir das, da steht keine Anweisung drin?" ist berechtigt: Es
  gibt keine, weil die Engine das Sinnvolle schon selbst tut — während eines Derivate-Pumps
  sind neue Einstiege fest gesperrt, und Verkaufen wurde fünfmal gemessen und kostete jedes
  Mal Rendite. Die Warnung ist reine Innensicht: sie sagt, WARUM die Engine gerade nicht
  kauft. **Entscheidung Kaiser: so lassen.** Begründung: Die Wiederholungen sind keine
  Doppelung, sondern eine Dauerangabe — vier Nachrichten in Folge heißen „läuft immer noch",
  das könnte eine einzelne Meldung nicht ausdrücken. Angebotene Alternativen (einmal je
  Episode = 34→15, oder Schalter zum Abschalten) wurden geprüft und verworfen.

- **Kein automatisches Trading** — die App sendet nur Signale; Orders platziert Kaiser selbst. (Sicherheit, API-Keys mit Handelsrechten wären auf kostenlosem Hosting ein Risiko.)
- **Keine starren Golden-Pocket-Levels** — explizite Anforderung: dynamisch aus Hochs/Tiefs.

## Übergabeprompt (für spätere Session / anderes Modell) — Stand 2026-07-23

```
Lies zuerst BTC-Trading/docs/ETAPPENPLAN.md (Statusquelle!), dann docs/STRATEGIE.md,
docs/ARCHITEKTUR.md, docs/GEGENCHECK.md.
STAND: Die App ist LIVE. Repo: github.com/szoceikaiser/btc-signal-app (public).
Webseite: szoceikaiser.github.io/btc-signal-app. Telegram laeuft (Secrets im Repo:
TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID). Engine-Cron alle 15 Min (Workflow Signal-Engine),
Backtest per Workflow "Backtest" auf Knopfdruck. Lokaler Arbeitsordner = git-Clone:
C:\Users\oeztu\BTC-Trading\signal-app — Aenderungen dort machen, Kaiser pusht selbst:
git pull --no-rebase && git add -A && git commit && git push.
AUFGABE: Etappen mit Status OFFEN abarbeiten (E8.x), nach jeder Etappe Status FERTIG
mit Datum setzen, Tests gruen halten (cd engine && python3 run_tests.py — 128 Tests;
lokal auf Windows: PYTHONIOENCODING=utf-8 setzen, sonst scheitern 5 Tests nur am
Emoji-Druck in der Konsole, nicht am Code).
REGELN: (1) Golden Pockets dynamisch aus Swing-Struktur, nie starr. (2) Long und Short
gleichwertig. (3) Nur Signale, kein Auto-Trading, keine Gewinnversprechen — und
Recall-% immer klar von Gewinn trennen. (4) Binance-FUTURES-API ist von GitHub-Runnern
geo-blockiert (HTTP 451) — Datenquellen-Mix aus ARCHITEKTUR.md beibehalten (Binance
Vision Spot + Kraken Futures). (5) Kaiser ist kein Entwickler: Anleitungen mit
Kontrollpunkten schreiben (Muster: signal-app/ANLEITUNG-*.md), Befehle als fertige
Bloecke, nach jedem Schritt Rueckmeldung abwarten. (6) Sandbox-Hinweise: Boersen-APIs
per curl blockiert, Web-Fetch geht; PyPI blockiert (Tests via run_tests.py, ohne
pytest); keine git-Schreibbefehle im Mount ausfuehren (index.lock bleibt haengen —
Kaiser loescht per del).
```


### E23 — Die 1D-Ebene als zweiter Zonensatz · Status: GEMESSEN 2026-08-28, SCHALTER BLEIBT AUS

Kaiser: *„Im Transkript von Furkan hattest du gesehen, dass er mit 4h und 1d charts
arbeitet. du wolltest etwas prüfen. hast du das?"* — hatte ich nicht. Von den drei
Vorschlägen aus `FURKAN-UPDATE-2026-08-02.md` Abschnitt 5 waren (a) größtes Bein und
(c) Mindest-Beinlänge gemessen; (b) die 1D-Zone als **eigene** Einstiegszone war offen.
`confluence` (E8.5) benutzt sie nur als Filter auf 4h-Setups — das ist etwas anderes.
Bauplan: `docs/PLAN-E23-1D-ZONENSATZ.md`, Vorab-Rechnung: `docs/PRUEFUNG-1D-EBENE.md`.

**Was gebaut ist.** Schalter `zonen_1d` (Default aus). Bei `true` läuft der 4h-Versuch
unverändert zuerst; bleibt die Position danach FLAT, wird derselbe Einstiegsblock ein
zweites Mal mit dem 1D-Impuls durchlaufen. Zeichnen beide Ebenen dasselbe Bein
(`gleiches_bein()`, Preisvergleich statt Zeitstempel), entfällt der zweite Durchlauf.
Signale aus der 1D-Ebene tragen `[1D]` im Grund. Alle bestehenden Sicherungen gelten
unverändert — `min_stop_pct`, `cooldown_h`, Order-Flow-Bestätigung, `block_unhealthy`.
Bei `zonen_1d=false` ist `_imp_1d` immer None und die Bedingung Wort für Wort die alte:
das Verhalten ist bitgleich zu vorher.

**Vorab geprüft, damit der Bau nicht ins Leere läuft.** Live lädt `main.py` 400 4h-Kerzen
= 66 Tage. Über 394 Tage nachgerechnet: das 1D-Bein aus 66 Tagen Historie ist in **100 %**
der Fälle identisch mit dem aus voller Historie. Kein Nachladen nötig.

**Der Befund, der die Etappe ausgelöst hat.** Am 26.07.2026 hätte die 1D-Ebene das Bein
57.800 → 66.956 gezeichnet — dasselbe, das in Furkans Chart steht (0.5 bei 62.378 gegen
seine 62.371). Nachgerechnet mit echten 4h-Kerzen sah die 4h-Ebene mit den Live-Parametern
zur selben Zeit das Bein 63.100 → 66.956: handelbar, aber am jüngsten Tief verankert. Sein
0.5-Level lag bei 65.028, weit über dem Tagestief von 62.275, und sein Stop bei 63.100 —
den riss der Tagesschluss von 62.824 noch am selben Tag. Die 1D-Ebene hätte bei 62.378
gekauft, mit Stop bei 57.800 und intakter Struktur.

**Eine eigene Fehlkorrektur.** In der ersten Fassung von `PRUEFUNG-1D-EBENE.md` stand, mit
`min_bein_pct: 0.05` hätte die 4h-Ebene gar kein Bein gezeichnet. Das war vermutet, nicht
gemessen, und falsch: `last_significant_impulse` überspringt ein zu kleines Bein und greift
eines höher. Der Backtest sagt dasselbe — die Variante mit Mindest-Bein hat mehr Signale
(242 statt 203), nicht weniger. Korrigiert; der Befund wurde dadurch schärfer, nicht
schwächer.

**Was NICHT gebaut ist** (Begründung im Bauplan): keine 1D-Zonen im Positions-Management,
kein Vorrang für 1D, kein eigener `min_bein_pct` für 1D, keine Konfluenz-Bevorzugung
(§4.1 Punkt 4 zweiter Halbsatz).

**Erwartung, damit sie überprüfbar ist.** Die Vorab-Rechnung über 15 Monate fällt durch die
Robustheitsprüfung: erste Fensterhälfte −18,1 %, zweite +44,5 % — der Vorteil steckt in
einer Marktphase. **Ich rechne damit, dass der Schalter aus bleibt.** Gebaut wird er, damit
die Frage beantwortet ist statt offen.

**MESSERGEBNIS (Backtest 28.08.2026, 07:03 UTC, Fenster 20.12.2025–28.08.2026).**
Der Schalter bleibt aus — deutlicher als erwartet.

| | Rendite | max. Rückgang | Signale | Recall | Präz. |
|---|---|---|---|---|---|
| **NEU-LIVE +Mindest-Bein 5 %** (live) | **+37,9 %** | **−6,9 %** | 241 | 71 % | 38 % |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | +23,4 % | **−17,6 %** | 255 | 52 % | 28 % |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | +26,5 % | −17,0 % | 231 | 52 % | 31 % |

Schlechter in **jeder** Spalte. Der Rückgang von −17,6 % ist der schlechteste im gesamten
Gitter aus 47 Varianten — die nächstschlechtere liegt bei −13,0 %.

**Robustheitsprüfung**, und hier kippt es endgültig:

| Variante | H1 (bis 25.04.) | Platz | H2 (ab 25.04.) | Platz |
|---|---|---|---|---|
| NEU-LIVE +Mindest-Bein 5 % | +26,4 % | 27. | **+9,1 %** | 5. |
| NEU-LIVE +1D-Ebene | +27,0 % | 24. | **−2,9 %** | 26. |

In der zweiten Hälfte verliert die 1D-Variante Geld, während die Live-Einstellung dort auf
Platz 5 liegt. Die Gegenprobe ohne Mindest-Bein zeigt dasselbe (−4,7 %, Platz 31): der
Effekt kommt von der 1D-Ebene selbst, nicht vom Zusammenspiel mit dem 5-%-Sieb.

**Warum der Rückgang so viel schlimmer wird.** Die 1D-Zonen verankern am echten
Strukturtief — genau das war ihr Vorteil am 01.08. Damit liegt die Invalidierung aber 7 bis
17 % entfernt statt 2 bis 5 %. Jeder Verlust-Trade kostet entsprechend mehr. Furkan
kompensiert das über die Positionsgröße („Tranchen, dynamisch, nie alles auf einmal");
unsere Engine setzt in jeder Variante 100 %. Der weitere Stop ohne die kleinere Position
ist der Fehler — nicht die Ebene an sich. Falls das je wieder aufgegriffen wird, gehört
`einsatz_pct` in Abhängigkeit vom Stop-Abstand dazu, sonst wiederholt sich das Ergebnis.

**Was meine Vorab-Rechnung falsch gemacht hat** (wichtiger als das Ergebnis selbst):
Sie sagte erste Hälfte schlecht, zweite gut. Gemessen ist es umgekehrt. Die Zeiträume sind
nicht deckungsgleich (Handrechnung 06/2025–08/2026, Backtest 12/2025–08/2026), aber das
erklärt nur einen Teil. Der eigentliche blinde Fleck: Die Handrechnung hat den **maximalen
Rückgang gar nicht gemessen** — und der ist hier das Ausschlusskriterium, nicht die Rendite.
Merksatz für die nächste Vorab-Rechnung: ohne Rückgangs-Messung ist eine Renditezahl
wertlos.

**Backtest.** Zwei neue Gitterzeilen (jetzt 47): `NEU-LIVE +1D-Ebene als zweiter Zonensatz`
und als Gegenprobe dieselbe Einstellung ohne Mindest-Bein — damit sichtbar wird, ob ein
Effekt von der 1D-Ebene kommt oder nur davon, wie das 5-%-Sieb die 4h-Beine verschiebt.

**Tests.** 5 neue (159 gesamt, alle grün), jeder mit Gegenprobe: Sabotage des 1D-Durchlaufs
→ 2 rot, Sabotage von `gleiches_bein` → 2 rot, Sabotage der `[1D]`-Kennzeichnung → 1 rot.
Ein eigener Test sichert das Szenario selbst ab (dass die beiden Ebenen darin wirklich
verschiedene Beine zeichnen) — sonst könnte der Haupttest grün bleiben, ohne zu messen,
was er zu messen vorgibt.


### E24 — Chart zeigt, was Telegram sagt · Beteiligung auf der Webseite · Status: GEBAUT 2026-08-28

Zwei Beobachtungen von Kaiser am 28.08.2026: die Beteiligungs-Kennzahl aus E22 fehlt auf der
Webseite, und *„der einstand bei 78807\$ war, auf [der Seite] steht aber bei K1: 78409\$.
Warum deckt sich das nicht? Auch der Nachkauf auf Telegramm und Teilverkauf deckt sich nicht
mit dem chart."* Bauplan: `docs/PLAN-E24-CHART-UND-PLAN.md`.

**Was kein Fehler war.** K1 im Chart (78.409 \$) ist der erste Kauf am 0.5-Level, der
Einstand im Plan (78.807 \$) der Durchschnitt aus drei Käufen — 25 % bei 78.409, 20 % bei
79.089, 20 % bei 79.024. Zwei verschiedene Größen. Auffällig dabei: beide Nachkäufe lagen
ÜBER dem Ersteinstieg. Das ist `liq_entry="boost"` — Aufstocken an der Liquidationszone,
unabhängig davon, ob der Kurs über oder unter dem Einstand steht. Gemessen ist der Schalter
gut, aber „Nachkauf" ist dafür der falsche Name; es ist Aufstocken in die Stärke.

**Was ein Fehler war.** Fünf Marken aus dem Plan fehlten im Chart, weil er sie aus einer
zweiten, eigenen Rechnung zog: zwei Liquidations-Nachkäufe (79.369 / 78.469), der Teilgewinn
kurz unter dem letzten Hoch (80.866) und die beiden Zwischenziele (82.214 / 82.787). Die
Einstandslinie fehlte ganz.

**E24.1 — eine Quelle für die Beteiligung.** `beteiligung()` wird jetzt in `simulate()`
gerechnet und steht damit im pnl-Dict und in `site/data/backtest.json`. Der Bericht liest
daraus statt selbst zu rechnen (mit Rückfall für ältere Läufe). Bericht und Webseite können
nicht mehr auseinanderlaufen.

**E24.2 — Monatstabelle auf der Seite.** Neue Spalten „Bitcoin" und „davon eingefangen"
(letztere nur in steigenden Monaten — ein Anteil am Rückgang wäre keine sinnvolle Größe, auf
Mobil ausgeblendet), darunter beide Kennzahlen. Sie zeigen *beide* Rechnungen: „Aufwärts
36 % (mit Flush 49 %)" — sonst stünde auf der Seite eine andere Zahl als im Bericht, der mit
der Live-Variante rechnet.

**E24.3 — Chart zeichnet aus `state.plan`.** Genau das Objekt, aus dem auch die
Telegram-Nachricht gebaut wird. Fib-Linien an Preisen, die der Plan ohnehin nennt, entfallen
dann; nie zwei Linien auf demselben Preis. Stop und Einstand werden zuerst gezeichnet, weil
der Stop sich seinen Preis mit der Untergrenze der Kaufleiter teilt und die wichtigere
Auskunft ist. Ergebnis: **15 Linien statt 10**, jede mit Handlung und Tranche im Text.

**Kaisers Rückfahrkarte** (*„wenn es mir nicht gefällt … dann soll es ausgeschaltet und der
ursprung wiederhergestellt werden"*): Umschalter „Plan-Marken" oben neben den
Zeitrahmen-Knöpfen. Ein Klick, sofort sichtbar, kein Commit; der Zustand liegt in
`localStorage`, gilt also nur für sein Gerät. Default an. Für den vollständigen Rückbau
genügt es, `site/index.html` auf den Stand vor dem E24-Commit zu setzen.

**Keine Engine-Änderung.** E24 ist reine Anzeige — kein Signal, keine Regel, kein Backtest
nötig. 159 Tests unverändert grün.


### E25 — Gegengeschäfte messbar machen · Status: GEMESSEN 2026-08-28, `no_flip` EMPFOHLEN

Kaiser, zum dritten Mal: *„ich sehe im chart schon wieder kauf und verkauf am 26.08 bei
0:00 = 79089\$"* — und diesmal deutlich: *„ich möchte kein gegengeschäft sehen"*.

**Meine falsche Entwarnung, und woher sie kam.** Beim ersten Mal (E18.2) habe ich gesagt,
`no_flip` betreffe „nur 2 von 202 Signalen". Nachgezählt im Lauf vom 28.08.:

- **16 Kerzen** mit Aufstockung UND Teilverkauf, **14 davon zum identischen Preis**
- **41 von 241 Einzelsignalen** daran beteiligt — jedes sechste

Meine „2 von 202" war die *Differenz der Gesamt-Signalzahl* zwischen zwei Gitterzeilen.
Die sagt nichts über die Häufigkeit: no_flip unterdrückt ein Signal, wodurch sich die
Position ändert und später andere Signale entstehen — unterm Strich fast dieselbe Zahl,
bei ganz anderem Verlauf. Ich habe die falsche Kennzahl für die Frage genommen. Im
`_hinweis_no_flip` in `config.json` stand die richtige Zahl (16 von 214) die ganze Zeit da.

**Der Vergleich war zusätzlich unbrauchbar.** Die Gitterzeile *NEU-LIVE +kein
Gegengeschaeft je Kerze* läuft ohne `min_bein_pct`, das seit 27.08. live ist. Sie gegen die
Live-Zeile zu halten misst zwei Unterschiede gleichzeitig. Neu im Gitter (jetzt 49):

- `NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft` — unterscheidet sich von der Live-Zeile
  in **genau einem** Punkt; ein Test hält das fest, sonst schleicht sich der Fehler zurück
- `NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten` — die beiden
  Schalter waren früher zusammen besser als einzeln

**Neue Spalte „Gegengeschaefte"** in der Haupttabelle des Berichts (`gegengeschaefte()`),
gezählt auf Kerzenebene: drei Signale in einer Kerze sind EIN Widerspruch, nicht drei.
Vollständige Ausstiege (Stop, Rest schließen) zählen nicht mit — die dürfen immer feuern.

**Warum die Kennzahl nötig ist und die Rendite nicht reicht.** Der Backtest handelt beide
Seiten zum exakten Signalpreis; netto bleibt die Tranchen-Differenz minus zwei Gebühren,
das verschwindet im Rauschen. In der Praxis ist so ein Paar aber **gar nicht ausführbar** —
zwei Limit-Orders zum selben Preis heben sich auf. An diesen 14 Stellen rechnet der
Backtest also eine Handlung mit, die Kaiser nie ausführen könnte. Die Spalte misst
Umsetzbarkeit, nicht Gewinn. Sollte `no_flip` im Backtest etwas kosten, ist das gegen
diesen Punkt abzuwägen — nicht automatisch ein Ausschlusskriterium.

**Tests.** 3 neue (162 gesamt, grün), alle mit Gegenprobe: Zählung auf Signal- statt
Kerzenebene → 2 rot; Stop als Gegengeschäft mitgezählt → 1 rot; ein zweiter Unterschied in
der neuen Gitterzeile → 1 rot.

**MESSERGEBNIS (Backtest 28.08.2026, 10:46 UTC, Fenster 20.12.2025–28.08.2026).**

| | Recall | Präz. | Rendite | max. Rückgang | Signale | Gegengeschäfte |
|---|---|---|---|---|---|---|
| NEU-LIVE +Mindest-Bein 5 % (live) | 71 % | 38 % | +37,3 % | −6,9 % | 241 | **16** |
| **+kein Gegengeschäft** | 67 % | 34 % | +34,2 % | −7,1 % | 240 | **0** |
| +kein Gegengeschäft +Ziele festhalten | 67 % | 34 % | +27,7 % | −7,1 % | 221 | 0 |

Der Schalter wirkt vollständig: 16 → 0. Er kostet im Gesamtfenster 3,1 Punkte Rendite, der
Rückgang bleibt praktisch gleich (−6,9 → −7,1). **Die Signalzahl fällt von 241 auf 240** —
genau ein Signal. Damit ist mein alter Denkfehler noch einmal schwarz auf weiß belegt: die
Netto-Signalzahl taugt nicht als Maß für die Häufigkeit.

**Robustheitsprüfung, und die dreht das Bild:**

| Variante | H1 (bis 25.04.) | Platz | H2 (ab 25.04.) | Platz |
|---|---|---|---|---|
| NEU-LIVE +Mindest-Bein 5 % | +26,4 % | 27. | +8,7 % | 7. |
| +kein Gegengeschäft | +23,1 % | 33. | **+9,0 %** | **4.** |

Der Nachteil steckt vollständig in der ERSTEN Hälfte. In der jüngeren ist der Schalter
leicht besser und liegt drei Plätze weiter vorn. Dazu die Zufallsrechnung des Berichts
selbst: bei 49 Varianten und je 5 Plätzen liegt der Erwartungswert bei 0,5 — gemessen 0.
Keine Variante ist in beiden Hälften vorne. **Die Rangfolge ist kein Beleg, und damit sind
auch die 3,1 Punkte keiner.**

**Empfehlung: einschalten.** Nicht weil es Rendite bringt, sondern weil es nichts
Belegbares kostet und ein reales Problem löst:

1. Die 16 Gegengeschäfte verschwinden restlos, 14 davon waren zum identischen Preis.
2. Der Renditeunterschied ist nicht robust — H1 schlechter, H2 besser.
3. Der maximale Rückgang bleibt gleich.
4. An den 14 gleichpreisigen Stellen rechnet der Backtest ohnehin eine Handlung mit, die
   Kaiser nie hätte ausführen können. Ein Teil der 3,1 Punkte ist damit fiktiv.
5. Kaisers Vorgabe: *„ich möchte kein gegengeschäft sehen."* Bei einem Preis, der sich
   nicht belegen lässt, entscheidet die Umsetzbarkeit.

`freeze_targets` bleibt aus — die Kombination ist mit +27,7 % deutlich schlechter.

**Live geschaltet 28.08.2026:** `no_flip: true` in `config.json`. Der Test
`test_panel_variante_entspricht_der_live_einstellung` schlug beim Umschalten sofort an —
richtig so: `panel=True` musste von `NEU-LIVE +Mindest-Bein 5 %` auf
`NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft` wandern, sonst zeigte die Chart-Webseite
weiter die Rendite einer Einstellung, die die Engine nicht mehr fährt. Genau der Fehler,
gegen den der Test 2026-08 gebaut wurde.


### E26 — Warum grosse Anstiege kaum ankommen · Status: GEMESSEN 2026-08-28, `neustart_mit_rest` LIVE

Kaiser: *„wie gehen wir das offene an?"* — gemeint war die Aufwärts-Beteiligung von 36 %
(August nur 11 %). Vor jedem Vorschlag erst gemessen, und die Ursache ist eine andere als
vermutet.

**Diagnose: die Engine ist schlicht klein positioniert.** Positionsanteil über die Zeit
rekonstruiert (Backtest-Signale + Tageskurse, 20.12.2025–28.08.2026):

| Monat | BTC | Tage investiert | ⌀ Anteil | ⌀ Anteil an Auf-Tagen |
|---|---|---|---|---|
| 2026-03 | +2,9 % | 48 % | 36 % | 46 % |
| 2026-04 | +11,7 % | 40 % | 30 % | 31 % |
| 2026-07 | +7,4 % | 52 % | 32 % | 31 % |
| 2026-08 | +24,6 % | 50 % | 39 % | 32 % |
| **gesamt** | | **42 %** | **29 %** | |

Im Mittel **29 % des Kapitals**, an 58 % der Tage gar nichts. An Aufwärts-Tagen ist der
Anteil nicht höher als sonst — im August sogar niedriger. Damit sind die 36 %
Aufwärts-Beteiligung keine Fehlfunktion, sondern **Arithmetik**: Wer im Mittel mit einem
knappen Drittel dabei ist, fängt auch etwa ein Drittel ein.

**Und die Kehrseite gehört dazu.** Dieselbe Zurückhaltung erzeugt die Abwärts-Beteiligung
von −17 %. Beides kommt aus derselben Quelle. Mehr vom Anstieg heisst zwangsläufig auch
mehr vom Rückgang — das ist keine Stellschraube, die man einseitig drehen kann.

**Nebenbefund aus der Diagnose (August im Detail):** Am 14.08. Stop bei 62.921, nachdem die
Position über die Mehrtages-Leiter, die 0.786-Zone und die Liquidations-Konfluenz auf
rechnerisch 155 % aufgebaut worden war. Am 19.08. dann kompletter Ausstieg bei 68.554
("Gegen-Muster am Ziel"). Der Anstieg lief bis 81.478 weiter — die Engine kam erst am 25.08.
bei 78.409 zurück, nach 87 % der Bewegung.

**Der Hebel lag bereits gemessen im Gitter**, nur nicht vergleichbar: Die drei besten Zeilen
der zweiten Fensterhälfte sind *Rest halten* und *Neustart mit Rest* (Plätze 1 und 3) — alle
drei laufen aber ohne `no_flip`, das seit 28.08. live ist. Derselbe Vergleichsfehler wie bei
E25. Neu im Gitter (jetzt 51), jede mit genau den benannten Unterschieden zur Live-Zeile:

- `LIVE-heute +Neustart mit Rest`
- `LIVE-heute +Rest halten +Neustart mit Rest`

**Neue Spalte „Aufwaerts"** in der Haupttabelle: die Aufwärts-Beteiligung je Variante. Ohne
sie sieht man nur die Rendite — und die verrät nicht, ob ein Schalter grosse Anstiege
wirklich besser einfängt oder bloss in fallenden Monaten gewinnt. Genau die Zahl, um die es
Kaiser geht.

**Ein zu schwacher Test, aufgedeckt durch die eigene Sabotage-Probe.** Der erste Anlauf von
`test_beteiligung_steht_im_pnl_dict_fuer_die_tabellenspalte` prüfte nur `beteiligung()`
selbst. Als ich das Feld versuchsweise aus dem pnl-Dict entfernte, blieb alles grün — die
Tabellenspalte hätte stumm überall „—" gezeigt. Jetzt läuft der Test durch `simulate()`.
Das ist derselbe Fehlertyp, den Kaiser schon zweimal an meinen Gegenproben gefunden hat:
geprüft wird die Funktion, nicht der Weg.

**Tests.** 2 neue (164 gesamt, grün), Sabotage-Probe: dritter Unterschied in einer neuen
Zeile → 1 rot; `beteiligung` aus dem pnl-Dict → 1 rot; auf/ab-Trennung aufgehoben → 3 rot.

**MESSERGEBNIS (Backtest 28.08.2026, 11:32 UTC).** Alle drei Zeilen mit `no_flip`, damit
sich jeweils nur das Gemeinte unterscheidet:

| | Rendite | Rückgang | Gegengesch. | **Aufwärts** | 2. Hälfte |
|---|---|---|---|---|---|
| Basis (bisher live) | +34,5 % | −7,1 % | 0 | 41 % | Platz 6 |
| **+Neustart mit Rest** | **+36,6 %** | −7,1 % | 0 | **44 %** | **Platz 4** |
| +Rest halten +Neustart | +35,7 % | −8,2 % | 1 | 47 % | Platz 3 |

`neustart_mit_rest` ist in jedem Punkt besser und in keinem schlechter — 2,1 Punkte mehr
Rendite, 3 Punkte mehr Aufwärts-Beteiligung, identischer Rückgang, weiterhin null
Gegengeschäfte. **Live geschaltet 28.08.2026**, Panel-Zeile mitgezogen (der Panel-Test
schlug beim Umschalten wieder sofort an — er tut zuverlässig, was er soll).

**KORREKTUR nach Kaisers Rückfrage (*„misst der backtest die vergangenheit auch mit
neustart mit rest?"*).** Ja — und daraus folgt ein Vorbehalt, den ich beim Empfehlen nicht
hatte. Nachgezählt, wie oft der Schalter überhaupt greift, also wie oft die Engine neu
einsteigt, während noch ein Rest läuft:

| Fensterhälfte | Fälle |
|---|---|
| bis 25.04.2026 | **1** (09.01., 90.130 $) |
| ab 25.04.2026 | **2** (30.04., 75.920 $ · 23.07., 65.028 $) |
| gesamt in 8 Monaten | **3** |

Passend dazu ist die Rendite in der ERSTEN Fensterhälfte bei beiden Varianten identisch
(+23,1 %). Die gesamten 2,1 Punkte Vorsprung entstehen aus **zwei Ereignissen** in der
zweiten Hälfte. Zwei Datenpunkte sind keine Statistik.

Meine Formulierung „besser in allem, schlechter in nichts" bleibt sachlich richtig, taugt
aber nicht als Begründung. Die tragfähige lautet:

1. Der Schalter **kostet nichts** — Rückgang unverändert −7,1 %, Abwärts-Beteiligung
   unverändert −22 %, Gegengeschäfte weiter null.
2. Er greift **selten**, im Schnitt alle drei Monate. Das begrenzt Nutzen wie Schaden.
3. Die Konstruktion trägt unabhängig von der Messung: Ohne ihn muss die Engine warten, bis
   der letzte Rest weg ist, bevor sie eine neue Struktur handeln darf. Genau dafür gab es
   die alte Rest-Freigabe (E9.9), die den Rest zum Marktpreis wegwarf — ein
   Konstruktionsfehler, den dieser Schalter sauberer behebt.

Also: gemessen harmlos, konstruktiv sinnvoll, dreimal von Vorteil — **kein belegter
Renditehebel**. Wer die Zahl später wiederfindet, soll wissen, worauf sie beruht.

**Und was die +36,5 % NICHT sind.** Der Backtest rechnet jede Variante von null durch, mit
dem Schalter von Anfang an. Kaisers Konto startet dagegen mit der Position, die es gerade
hat, und hatte den Schalter bis heute aus. Die Zahl ist ein Variantenvergleich, keine
Vorhersage für das reale Ergebnis.

`rest_halten` bleibt aus: 3 Punkte mehr Aufwärts-Beteiligung, aber 1,1 Punkte mehr Rückgang
und ein Gegengeschäft zurück. Das ist eine Abwägung, keine Verbesserung — und die Regel
lautet, einen Schalter nach dem anderen zu bewegen.

> **Diese Begründung ist mit E27 hinfällig geworden** (Lauf 28.08.2026, 18:17 UTC). Mit der
> lückenlosen Rückgangs-Messung schrumpft der Abstand von 1,1 auf **0,4 Punkte**
> (−9,4 % gegen −9,8 %). Das Rückgangs-Argument trägt nicht mehr. Die Entscheidung bleibt
> trotzdem — mit der besseren Begründung aus der Abwärts-Spalte:
>
> | | Rendite | Rückgang | Aufwärts | Abwärts |
> |---|---|---|---|---|
> | live | +34,9 % | −9,4 % | 44 % | −22 % |
> | +Rest halten | +34,0 % | −9,8 % | **48 %** | **−18 %** |
>
> Aufwärts +4 Punkte, Abwärts +4 Punkte — ein Eins-zu-eins-Tausch bei leicht sinkender
> Rendite. Die Engine fängt mehr vom Anstieg ein und macht im selben Maß mehr vom Rückgang
> mit. Das ist keine Verbesserung, sondern nur mehr Marktexposition. Dazu wieder das
> bekannte Muster: erste Fensterhälfte schlechter (Platz 42 gegen 34), zweite besser.
>
> Genau dafür war die Abwärts-Spalte gebaut (E26.2). Ohne sie stünde hier jetzt „0,4 Punkte,
> vielleicht doch?" — mit ihr ist die Sache klar.

**Der Preis von `no_flip`, jetzt exakt beziffert.** Zwei Zeilen unterscheiden sich nur in
diesem Punkt:

| | Rendite | **Aufwärts** | Gegengeschäfte |
|---|---|---|---|
| ohne `no_flip` | +38,7 % | **50 %** | 16 |
| mit `no_flip` | +36,6 % | **44 %** | 0 |

2,1 Punkte Rendite **und 6 Punkte Aufwärts-Beteiligung**. Das ist mehr, als ich Kaiser am
Vortag gesagt hatte — damals stand nur die Rendite zur Verfügung, und die war nicht robust.
Die Aufwärts-Beteiligung ist der ehrlichere Maßstab. An der Entscheidung ändert es nichts
(14 der 16 Paare waren zum identischen Preis und damit nicht ausführbar), aber die Zahl
gehört auf den Tisch.

**E26.2 — Spalte „Abwaerts"** dazu, weil „Aufwärts" allein irreführt: Wer mehr vom Anstieg
mitnimmt, macht in aller Regel auch mehr vom Rückgang mit. Steigt nur Aufwärts, ist etwas
gewonnen; steigen beide, wurde bloß das Risiko erhöht.

**E26.3 — Test auf Tabellenkopf und Trennlinie.** Beim Ergänzen der Spalte wäre ein
vergessener Strich in der Markdown-Trennlinie niemandem aufgefallen: GitHub verschiebt dann
alle Werte um eine Spalte, und man liest wochenlang Zahlen unter falschen Überschriften.
Der Test vergleicht beide Zeilen; Gegenprobe (Spalte ohne Trennlinie) schlägt an.
174 Tests grün (die Zahl 165 in früheren Notizen dieser
  Sitzung war zu niedrig — test_coinalyze.py war beim Zählen übersehen worden).


### E27 — Der maximale Rückgang war zu freundlich gemessen · Status: GEBAUT 2026-08-28

Kaiser fragte nach den offenen Punkten; dies war der wichtigste. Notiert stand er seit E18
(„NICHT in diesem Paket"), liegen geblieben ist er, weil er keine Signale ändert — aber er
ändert **jede Rückgangszahl, die wir je gelesen haben**.

**Der Fehler.** `simulate()` wertete die Kontostände nur an Signalzeitpunkten aus:

```python
for e in [x["equity"] for x in equity] + [end_equity]:
    peak_eq = max(peak_eq, e); max_dd = min(max_dd, e / peak_eq - 1.0)
```

Zwischen zwei Signalen können Wochen liegen. Was das Konto in dieser Zeit an Buchverlust
erlebte, tauchte nirgends auf. Im Extremfall: gekauft, der Kurs fällt 40 %, erholt sich,
kein Signal dazwischen — gemeldeter Rückgang **0 %**, tatsächlicher 30 %.

**Die Korrektur.** Der Positionsstand wird nach jedem Signal mitgeschrieben; anschließend
läuft die Messung über **jede Kerze** und wertet sie an ihrem ungünstigsten Punkt aus —
Tief bei Long, Hoch bei Short. Das ist der Stand, den man auf dem Konto gesehen hätte, nicht
der geschönte Schlusskurs.

**Folge, die man kennen muss:** Alle Rückgangszahlen werden ab dem nächsten Lauf grösser.
Sie sind nicht mit älteren Berichten vergleichbar. Die Lesehilfe im Bericht sagt das jetzt.
Und mehrere heutige Entscheidungen stützten sich auf die alte Zahl — allen voran die gegen
`rest_halten` (−8,2 % gegen −7,1 %). Diese Abwägung ist mit der korrigierten Messung neu zu
führen.

**Tests.** 3 neue (168 gesamt, grün): Rückgang zwischen den Signalen, Kerzentief statt
Schluss bei Long, Kerzenhoch bei Short. Sabotage-Probe: zurück auf die alte Messung → 3 rot;
nur Schlusskurs statt Tief/Hoch → 3 rot.

**MESSERGEBNIS (Lauf 28.08.2026, 18:17 UTC).** Der Fehler war grösser als vermutet:

| | vorher | lückenlos | Aufschlag |
|---|---|---|---|
| Live-Einstellung | −7,1 % | **−9,4 %** | +32 % |
| +Rest halten | −8,2 % | **−9,8 %** | +20 % |
| alle 52 Varianten, Median | — | **−9,9 %** | — |
| schlechteste Variante | — | −20,1 % | — |

Rund ein Drittel des tatsächlichen Rückgangs fehlte in jeder bisherigen Zahl. Direkte
Folge: die Ablehnung von `rest_halten` unter E26 musste neu begründet werden (dort als
Zitatblock nachgetragen) — das Rückgangs-Argument war nach der Korrektur zu dünn, die
Abwärts-Beteiligung trägt die Entscheidung dagegen sauber.

**Merksatz für später:** Eine Kennzahl, die nur an Ereigniszeitpunkten gemessen wird,
beschreibt nicht den Zustand dazwischen. Das galt hier für den Rückgang; es lohnt sich zu
prüfen, wo im Projekt sonst noch so gerechnet wird.

### E27.2 — `.gitattributes` (nebenbei, aber täglich spürbar)

Der Grund für das `git checkout --` in jeder Push-Anleitung: Der Workflow schreibt LF,
Windows machte CRLF daraus, Git hielt ganze Dateien für geändert — der Diff einer
Ein-Zeilen-Änderung umfasste 446 Zeilen. `* text=auto eol=lf` beendet das. Einmalig muss
nach dem Einchecken `git add --renormalize .` laufen.

Ebenfalls aufgefallen: `engine/__pycache__/*.pyc` sind versioniert, obwohl `.gitignore` sie
ausschliesst — `.gitignore` greift nicht bei bereits verfolgten Dateien. Sie gehören mit
`git rm --cached -r engine/__pycache__` aus der Versionierung genommen.


### E28 — Break-even-Stop nach jeder Aufstockung (Furkan) · Status: ZURUECKGENOMMEN 2026-08-28 (Kaisers Entscheidung)

Kaiser: *„Break even stop nach furkan umsetzen."* Bauplan:
`docs/PLAN-E28-BREAKEVEN-NACH-AUFSTOCKUNG.md`.

> **ZURUECKGENOMMEN noch am selben Tag, vor dem Push.** Kaiser: *„das mit dem stop
> nachziehen möchte ich doch nicht haben. Das werde ich im laufe der trades ggf. selber
> tun."* Der gesamte Code wurde entfernt (`strategy_core.py`, `main.py`, `backtest.py`,
> `config.json`, Tests), die Arbeitskopie steht wieder exakt auf dem E27-Commit, 168 Tests
> grün. Nichts davon war je auf GitHub.
>
> **Die Begründung ist gut und gehört festgehalten:** Wann der Stop nachgezogen wird, hängt
> davon ab, wie sich der Markt gerade anfühlt — ob eine Bewegung noch Luft hat oder kippt.
> Das ist eine Ermessensentscheidung, die Furkan von Hand trifft und die Kaiser ebenfalls
> von Hand treffen will. Eine mechanische Regel dafür trifft sie immer gleich, egal wie die
> Lage ist. Die Engine soll die Marken liefern; der Ausstieg bleibt Kaisers Sache.
>
> **Was daraus bleibt** (die Arbeit war nicht umsonst): Der Bauplan liegt vollständig vor,
> samt des Konstruktionsfehlers, den erst das Ausprobieren zeigte (Karussell im fallenden
> Markt, Lösung über den `be_auf_aktiv`-Merker). Sollte der Punkt je wieder aufkommen, ist
> er in einer Stunde nachgebaut statt in einem halben Tag.
>
> **`trail_stop` bleibt drin** (live seit E9.10). Auf Nachfrage entschieden: *„Nein, nicht
> rausnehmen."* Er zieht den Stop nach, sobald ein Teilgewinn realisiert ist — also erst,
> wenn schon etwas gesichert wurde.
>
> **Daraus die Trennlinie für alles, was künftig in diese Richtung kommt:** Den Stop
> nachzuziehen NACH einem realisierten Gewinn ist Mechanik und darf automatisch laufen. Ihn
> nachzuziehen, WÄHREND sich eine Position noch aufbaut, ist eine Ermessensfrage — dabei
> zählt, ob eine Bewegung noch Luft hat oder kippt, und das entscheidet Kaiser von Hand.
> Eine mechanische Regel träfe diese Entscheidung immer gleich, egal wie die Lage ist.

**Die Quelle, zweimal wörtlich:** *„wenn ich die Order gefüllt bekomme, würde ich meinen
Stop … hochsetzen auf das neue Entry. Mit der Position möchte ich nicht mehr in Verlust
gehen."* (Video 02.08.2026, 16:07–16:25; identisch in Video B, 18:50.) Notiert seit E10,
in E12 als Punkt 2 der Verlust-Analyse (44 % der Verlustsumme), nie gebaut.

**Warum es nichts Bestehendes ist.** Drei verschiedene Auslöser:

| Mechanismus | löst aus bei | Status |
|---|---|---|
| `trail_stop` | realisiertem Teilgewinn | live |
| `be_im_plus` | Position stand im Plus | gemessen, aus |
| **`be_nach_aufstockung`** | **gefüllter Nachkauf** | neu, Default aus |

**Gebaut:** Feld `Position.aufstockungen`, hochgezählt an der zentralen Stelle, an der auch
der Durchschnitts-Einstand fortgeschrieben wird — dort laufen alle sechs Einstiegspfade
zusammen (0.786-Zone, Kaufleiter, Liquidations-Konfluenz, bedingter Nachkauf). Sechs
Einzelstellen zu patchen wäre die Variante, bei der man eine vergisst. Als Aufstockung zählt
ein Einstiegssignal nur, wenn `entry_pct` davor schon > 0 war.

**Der Konstruktionsfehler, den erst das Ausprobieren zeigte.** Wörtlich umgesetzt entsteht
ein Karussell: Die Kaufleiter kauft mit 15-%-Tranchen in einen fallenden Kurs, der Einstand
sinkt kaum mit und liegt über dem Kurs — der Stop lag damit über dem Markt und feuerte
sofort. Vier Stop-und-Wiedereinstieg-Zyklen in acht Kerzen. Ergänzt wurde deshalb die
Bedingung, dass der Kurs den Einstand einmal überschritten haben muss (Merker
`be_auf_aktiv`). Das ist die einzige Lesart, die trägt: Die Regel schützt einen Gewinn, den
man hat. Derselbe Merker-Grund wie bei `be_im_plus` (E19.3) — die Bedingung ist in der
Kerze, in der der Stop greifen soll, nicht mehr erfüllt.

**Erwartung, damit sie überprüfbar ist.** Mehr Stops, kürzere Haltedauer, **niedrigere
Aufwärts-Beteiligung** — die Position wird künftig öfter beendet, bevor eine Bewegung
ausläuft. Ob der vermiedene Verlust das aufwiegt, muss die Rendite zeigen. Besonders im
Blick zu behalten: `liq_entry="boost"` stockt auch ÜBER dem Einstand auf (26.08.2026:
Einstieg 78.409, Nachkäufe 79.089/79.024 → Einstand steigt auf 78.807). Der Stop rückt
dadurch näher an den Kurs. Deshalb läuft eine zweite Gitterzeile OHNE die
Liquidations-Konfluenz, damit sich beide Effekte trennen lassen.

**Tests.** 5 neue (173 gesamt, grün). Sabotage-Probe, alle vier greifen: Merker weggelassen
→ 2 rot; Ersteinstieg als Aufstockung gezählt → 1 rot; Stop stumpf gesetzt statt maximiert
→ 1 rot; Reset vergisst die Zähler → 1 rot.

**Zwei zu schwache Tests, die erst die Sabotage-Probe aufgedeckt hat** — beide beim ersten
Anlauf grün geblieben, obwohl der Mechanismus kaputt war:
1. Der Zähler-Test prüfte `pos.aufstockungen` am ENDE. Nach einem Stop setzt
   `_reset_position()` alles auf null — der Test war grün, egal was unterwegs gezählt wurde.
   Jetzt wird der höchste Stand während des Laufs geprüft.
2. Der Lockerungs-Test hatte ein Szenario, in dem gar kein Stop möglich war. Jetzt liegt der
   Einstand unter der Invalidierung (so wie nach einem bedingten Nachkauf), und der Test
   verlangt, dass die Invalidierung trotzdem greift.


### E29 — MVRV-Z als Richtungs-Bias · Status: GEPRUEFT UND ZU DEN AKTEN (28.08.2026)

Kaiser: *„auch mvrv-z als richtungsbias prüfen, ob umgesetzt werden kann."* Offen seit E10
(Furkans MVRV-Valuezone) und E12 als Alternative zum pausierten KI-Makro-Bias (E8.5).

**Datenquelle gäbe es.** BGeometrics / bitcoin-data.com bietet eine kostenlose API mit MVRV,
Registrierung für einen Schlüssel (wie Coinalyze als GitHub-Secret). Grenze: **8 Anfragen
pro Stunde, 15 pro Tag** — für die Engine (6 Läufe täglich) knapp ausreichend, die
Flush-Wache (alle 15 Min) dürfte den Wert nie abrufen. Bitbo hat ebenfalls einen
MVRV-Z-Endpunkt, aber ohne erkennbaren kostenlosen Zugang. Erreichbarkeit war von hier aus
nicht prüfbar (Netzsperre in beiden Umgebungen); auf GitHub Actions vermutlich kein Problem.

**Woran es scheitert: nicht messbar.** Der MVRV-Z bewegt sich über Zyklen von Jahren, unser
Backtest-Fenster umfasst acht Monate. Belegte Werte darin:

| Zeitpunkt | BTC | MVRV-Z |
|---|---|---|
| 08.06.2026 | ~62.000 $ | 0,24 |
| bei ~76.000 $ | | „unter 1, über 0" |
| 08.08.2026 | ~72.000 $ | 0,42 |

Die klassischen Schwellen sind **0** (Zyklustief) und **7** (Zyklushoch). Keine wurde
berührt, nicht annähernd. Ein Bias auf dieser Basis wäre über das gesamte Fenster konstant
„Long erlaubt" — also identisch mit `bias_long=true, bias_short=false`, das ohnehin live
ist. Der Backtest lieferte Zeile für Zeile dieselben Signale. **Bauen ginge, messen nicht.**

Dasselbe gilt für die naheliegende Alternative (MVRV-Z als Faktor für die Positionsgröße
statt als Ein/Aus-Schalter): Bei einer Spanne von 0,24 bis 0,42 müssten die Schwellen frei
erfunden werden.

**Offener Vorschlag, nicht gebaut:** den Wert einmal täglich abrufen und nur ANZEIGEN
(state.json, Chart, Vorschau-Nachricht). Kostet eine Anfrage am Tag, ändert keine Regel und
baut die Historie auf, die heute fehlt. In einem Jahr wäre eine echte Messung möglich.

## Review-Antworten (Fragen von Opus 4.8, beantwortet 2026-07-23)

1. Swings: fester Pivot-Lookback n=5 (beidseitige Bestaetigung) + Mindest-Beinlaenge
   (Spanne >= k_atr x ATR(14), k=2.0 kalibriert, ODER >= 3 %) in
   last_significant_impulse — Zappler werden gefiltert. Lookback selbst nicht
   adaptiv -> E8-Idee (volatilitaetsabhaengiges n).
2. Invalidierung = Ursprung des ankernden Beins (Fib 1.0); Stop bei KERZENSCHLUSS
   jenseits davon (konservative Variante aus dem Video).
3. CVD = Binance-Taker-Proxy (Spot, kumuliertes Taker-Delta), KEIN Multi-Boersen-CVD;
   Futures-CVD fehlt (451-Block), Muster 2 ersatzweise via OI+Funding+Spot-flach.
   OI/Funding nur Kraken PF_XBTUSD (OI-Snapshot-Historie selbst aufgebaut).
   Alles dokumentiert in ARCHITEKTUR.md.
4. Backtest existiert (engine/backtest.py + Workflow "Backtest"), 8 Kombis gegen
   Kaisers 44 notierte Trigger (±1 Tag): 13/20 Kauf, 7/24 Verkauf VOR dem
   Capitulation-Fix (E8.1). Messlauf NACH E8.1 steht aus.

## E30 — Zonen einer laufenden Position nachziehen (05.09.2026)

Anlass: Kaiser — "Wenn sich eine neue Struktur ergibt, dann dürften diese nicht
festgefahren bleiben sondern sich ändern. Bei Furkan ändern sie sich doch auch,
oder?" Er hat recht: `strategy_core.py` Zeile 974 setzte `z = pos.zones` hart,
ohne Schalter. Ziele und Stop wanderten längst mit, nur die Kaufbereiche nicht —
im Widerspruch zur eigenen Grundregel 1 ("Zonen sind dynamisch, nie starr").

- **E30.1 Kernlogik + Tests — FERTIG (05.09.2026).** Schalter `zonen_nachziehen`
  (Default aus). Zieht die Zonen auf ein neues Bein, aber nur bei intaktem Trend:
  höheres Tief UND höheres Hoch (Short spiegelbildlich). Bei Trendbruch bleiben
  die alten Zonen stehen. 4 neue Tests, Sabotage-Probe bestanden.
- **E30.2 Messung — FERTIG (05.09.2026).** Rendite +37,2 % gegen +36,2 % live,
  Rückgang identisch −9,7 %. Aufwärts-Beteiligung 49 → 54 %, Abwärts −17 → −14 %
  (beides besser — der seltene Fall eines echten Gewinns statt eines Tauschs).
  Aber: 1 Gegengeschäft statt 0, entgegen Kaisers Vorgabe. Ursache offen.
- **E30.2b no_flip-Lücke — FERTIG (05.09.2026).** Das eine Gegengeschäft kam nicht
  vom Nachziehen: der Neustart-mit-Rest-Block (E21) fragte `_darf_aufstocken()`
  nicht ab und konnte deshalb in dieselbe Kerze fallen wie ein Teilverkauf. Vor der
  Änderung reproduziert (mit UND ohne `zonen_nachziehen`), danach behoben. Betrifft
  auch die Live-Einstellung.
- **Nachmessung nach E30.2b — FERTIG (05.09.2026, 21:50 UTC).** 0 Gegengeschäfte in
  beiden Zeilen. Rendite +36,4 % gegen +36,3 % live, Rückgang beide −9,7 %.
  Aufwärts 49 → 52 %, Abwärts −17 → −14 %. Der Schalter kostet nichts und verbessert
  die Beteiligung leicht.
- **E30.3 Entscheidung — LIVE seit 05.09.2026.** `zonen_nachziehen: true`,
  Panel-Zeile mitgewandert auf *LIVE-heute +Zonen nachziehen*. Grund: der Schalter
  kostet nichts und behebt einen Konstruktionsfehler — nicht die Rendite.

## Nebenbefund (05.09.2026): Chart-Webseite war 8 Tage veraltet

GitHub löst bei einem Push, den ein Workflow mit dem Standard-GITHUB_TOKEN macht,
keine weiteren Workflows aus. Signal-Engine und Backtest schrieben deshalb zwar nach
`site/data`, konnten aber den Pages-Workflow nie auslösen — die veröffentlichte Seite
stand seit dem letzten Push von Hand (28.08.) still und zeigte veraltete
Backtest-Zahlen. Behoben durch einen `workflow_run`-Auslöser in `pages.yml`, der nur
bei erfolgreichen Läufen greift.

Details: `docs/PLAN-E30-ZONEN-NACHZIEHEN.md`

## Arbeitsweise: HOCHLADEN.cmd (05.09.2026)

Kaiser: "muss das übrigens mit backup.cmd sein? können wir das nicht anders lösen?"

Hintergrund: Es gibt zwei getrennte Repositories, und das ist beabsichtigt.
`signal-app` ist öffentlich (unbegrenzte Actions-Minuten für Backtest und Engine),
`260729-btc-trading-backup` ist privat und enthält das Furkan-Transkript, Kaisers
notierte Trigger, die Analysen in `docs/` und die Heatmap-Screenshots. Diese
Unterlagen gehören nicht in ein öffentliches Repo — eine Zusammenlegung wäre
deshalb keine Vereinfachung, sondern eine Veröffentlichung.

Gelöst wurde stattdessen der Doppelaufwand: `HOCHLADEN.cmd` im Ordner BTC-Trading
erledigt beides per Doppelklick — erst Code committen und pushen (mit Rückfrage
nach einer kurzen Beschreibung, Enter setzt das Datum ein), dann `BACKUP.cmd` für
die Unterlagen. Räumt die hängende `index.lock` selbst weg und bricht bei einem
misslungenen Rebase sauber ab (`git rebase --abort`), statt den Ordner in einem
halbfertigen Zustand zu hinterlassen. Reines ASCII und CRLF, aus demselben Grund
wie bei BACKUP.cmd.

## E31 — Wissens-Layer (05.09.2026)

Kaiser: *"Ist all unser Wissen über die Fehlschläge und wie die engine nun alles
analysiert im Wissens Layer enthalten?"* — Antwort war: das meiste ja, aber verstreut
über 29 Dateien und 7.324 Zeilen an drei Orten, und der Übergabeprompt war sechs
Wochen alt. Umgesetzt nach Teil A und Teil B2 aus Kaisers Prompt-Bibliothek
(bestehendes Projekt strukturieren).

**Entscheidung Kaiser (05.09.2026):** Der Layer legt sich als Landkarte DARÜBER,
es wird nichts verschoben. Grund: rund 20 Code-Stellen verweisen auf `docs/...`;
ein Verschieben würde sie alle brechen. Bei der Doppelung bleibt `config.json`
maßgeblich für das Warum, `ANLEITUNG-EINSTELLUNGEN.md` wird auf das Wie reduziert.

- **E31.1 — START-HIER.md + 02_status/ — FERTIG (05.09.2026).**
  `wissens-layer/START-HIER.md` (Projekt in einer Minute, die beiden Repos, die
  maßgeblichen Quellen, **aktueller Übergabeprompt** — ersetzt den vom 23.07.),
  `02_status/GEMESSEN-UND-ENTSCHIEDEN.md` (jeder Mechanismus mit Ergebnis,
  Entscheidung und Fundstelle) und `02_status/OFFENE-PUNKTE.md`.

  **Kongruenz-Check maschinell durchgeführt** (Abgleich der Tabelle gegen
  `config.json`, Prüfung aller Datei-Verweise). Er fand vier Lücken, die behoben
  wurden — und dabei einen neuen Befund:

  **`confirm_t1`, `cooldown_h`, `be_im_plus` und `release_stale_rest` hängen
  unentschieden in der Luft.** Sie stehen seit Monaten auf "erst nach
  Backtest-Messung einschalten", sind also weder live noch verworfen. `confirm_t1`
  (+36,1 %) und `cooldown_h` (+36,5 %) sahen auf ihrer damaligen Basis
  (*LIVE +Stop nachziehen*, +33,3 %) sogar deutlich besser aus. Diese Basis gibt es
  nicht mehr, und auf der heutigen wurden sie nie mit genau einem Unterschied
  gemessen. Zwei saubere Gitterzeilen würden das klären.

- **E31.2 — übrige Ordner (01_produkt, 03_architektur, 04_konventionen,
  05_quellen, 06_entwicklung) — OFFEN, Freigabe steht aus.**
- **E31.3 — Doppelung auflösen — OFFEN, Freigabe steht aus.**

- **E31.2 — die übrigen fünf Ordner — FERTIG (05.09.2026).**
  `01_produkt/ZIEL-UND-NICHT-ZIELE.md`, `03_architektur/UEBERBLICK.md`,
  `04_konventionen/ARBEITSREGELN.md`, `05_quellen/MASSGEBLICHE-QUELLEN.md`,
  `06_entwicklung/BEFEHLE.md`. Nichts verschoben, nichts an bestehenden Dateien
  geändert.

  Der Kongruenz-Check über alle acht Layer-Dateien (Datei-Verweise, Testzahl,
  Schalterzahl, Workflow-Zahl gegen die echten Quellen) fand **einen sachlichen
  Fehler: die Testzahl.** In dieser Sitzung war durchgehend von 165 Tests die Rede —
  tatsächlich sind es **174**. Beim manuellen Zählen war `test_coinalyze.py`
  übersehen worden; `run_tests.py` findet alle `test_*.py` selbst. Überall im
  Wissens-Layer korrigiert. Lehre: die Zahl aus dem Läufer nehmen, nicht selbst zählen.

- **E31.3 — Doppelung auflösen — FERTIG (05.09.2026).**

  Vorgehen nach Teil A Punkt 7 der Prompt-Bibliothek: erst absorbieren, dann kürzen.
  Neun Hinweistexte in `config.json` wurden um das ergänzt, was **nur** in
  `ANLEITUNG-EINSTELLUNGEN.md` stand (Messwerte zu `confirm_t1`, `cooldown_h`,
  `block_unhealthy`, `bias_short`, `min_stop_pct`, `liq_entry`, `release_stale_rest`,
  die `high_exit`-Lehre und der E30.2b-Nachtrag zu `no_flip`); `bias_long` bekam
  erstmals einen. Alle 31 Schalter haben jetzt einen Hinweistext. Erst danach wurde die
  Schalter-Tabelle in der Anleitung durch einen Verweis ersetzt.

  Zusätzlich in der Anleitung berichtigt: Abschnitt 4 behauptete, `pivot_n`, `k_atr`,
  `flush_entry` und `buy_ladder` stünden im Quelltext — sie stehen seit E18.1 in
  `config.json`. Abschnitt 7 beschrieb das Hochladen von Hand mit `git pull --no-rebase`
  und verweist jetzt auf `HOCHLADEN.cmd`. `signal-app/README.md` nennt den Wissens-Layer.

  **Dabei zwei Fehler gefunden, die nichts mit der Etappe zu tun hatten:**

  1. **Die Gitterzeile *MEINE Einstellung ohne Flush* war nie mitgewandert.** Sie soll
     sich von der Panel-Zeile in genau einem Punkt unterscheiden (`flush_entry`) — die
     Monatsübersicht auf der Webseite stellt beide gegenüber. Tatsächlich fehlten dort
     `no_flip` und `neustart_mit_rest` (beide live seit 28.08.) und `zonen_nachziehen`
     (seit 05.09.): **vier Unterschiede statt einem.** Die Webseite verglich also seit
     dem 28.08. nicht „mit gegen ohne Flush", sondern ein Sammelsurium. Behoben; der
     neue Test `test_ohne_flush_zeile_unterscheidet_sich_nur_im_flush` hält es fest
     (Sabotage-Probe bestanden). 175 Tests grün.

  2. **Der Eintrag zu `confirm_t1`/`cooldown_h` im Wissens-Layer war unvollständig.**
     Er stützte sich nur auf das heutige Gitter (beide besser als ihre Basis) und kannte
     die gegenteilige Messung vom 28.07.2026 aus der Anleitung nicht (−4,6 Punkte bzw.
     „kippt zwischen den Hälften"). Beide Quellen stimmen — sie messen gegen
     verschiedene Basisvarianten. Der Layer nennt jetzt beide und die Lehre daraus, die
     im Projekt schon einmal teuer war: **ein Messergebnis gilt nur gegen die Basis,
     gegen die gemessen wurde.** Diese Regel stand bisher nur in der Anleitung und ist
     jetzt in `04_konventionen/ARBEITSREGELN.md` verankert.

## E32 — Lage-Information in Plan und Vorschau (13.09.2026)

Anlass: Kaiser nach dem Furkan-Video vom 10.09.2026 — *"ich bekomme die info zur
struktur nur, wenn ich eine nachricht für ein nachkauf erhalte. doch das ist zu spät,
weil ich doch die limits vorher setze."* Nachgeprüft: `format_vorschau()` und
`format_plan()` enthielten **keine einzige Zeile** über Order-Flow. Die Engine wertet
alles aus und behielt das Ergebnis für sich.

Belege aus dem Video (Standbilder gezogen, Videodatei unter `Videos/260910/`):

- **Furkan führt DREI Fib-Raster gleichzeitig** in einem Chart. Das größte:
  62.200 → 82.000, Golden Pocket bei **69.000–70.000**. Die Engine rechnete im selben
  Moment mit 76.264 → 82.300, Golden Pocket **78.377–78.570** — rund **9.000 $**
  daneben. Daher sein Satz bei 18:16: *"Ich würde die Position jetzt erstmal noch nicht
  hochskalieren."* Bei 76.954 $ ist er weit über jeder seiner Kaufzonen.
- **Sein Order-Flow-Chart (Velo) zeigt genau die fünf Größen, die die Engine schon
  erfasst**: Spot-Volumen (`spot_cvd`), Futures-Volumen (`fut_cvd`), Open Interest
  (`oi`), Funding, Liquidationen.
- Die Zahlen "57.700 / 57.500" aus dem Transkript sind **kein** Abschreibfehler —
  im Chart stehen Fib-Marken bei 57.802,4 und 57.837,4.

- **E32.1 Lage in Plan und Vorschau — FERTIG (13.09.2026).**
  Neue Funktionen `spot_nachfrage()` und `lage_bericht()` in `strategy_core.py`,
  Klartext-Tabelle `MUSTER_KLARTEXT`. Zwei getrennte Aussagen, wie Furkan sie trennt:
  Struktur am **Preis** (dieselbe Regel wie `trend_intakt` aus E30), Gesundheit am
  **Order-Flow**. Spot-Nachfrage in vier Zuständen (stabil / zurückgekehrt /
  nachgelassen / schwach) aus der Netto-Nachfrage zweier 3-Kerzen-Fenster.
  **Kein Backtest nötig und keiner gemacht:** E32.1 ändert kein einziges Signal.
  Ein eigener Test hält genau das fest (`test_lage_aendert_keine_signale`).
  182 Tests grün. Sabotage-Probe mit fünf Eingriffen bestanden — jeder wurde von
  mindestens einem Test gefangen.
- **E32.2 Meldung bei Wechsel der Spot-Lage — OFFEN.** Schaltbar, Default aus, weil
  sie zusätzliche Nachrichten erzeugt.
- **E32.3 Zweiter Zonensatz aus einem großen Bein — OFFEN.** Der eigentliche Hebel
  (9.000 $ Unterschied) und die teuerste Etappe. Muss gemessen werden.

Details: `docs/PLAN-E32-LAGEZEILE.md`

### E32.3 — GEMESSEN 13.09.2026: verworfen

Die 1D-Ebene mit eigener Swing-Weite ist in **jeder** geprüften Weite deutlich
schlechter als die Live-Einstellung:

| | Rendite | max. Rückgang | Aufwärts | Abwärts |
|---|---|---|---|---|
| live (Zonen nachziehen) | +31,4 % | −9,7 % | 47 % | −11 % |
| n=8 (die Hypothese) | +5,5 % | −22,9 % | 53 % | +29 % |
| n=5 (was E23 tat) | +21,6 % | −18,6 % | 58 % | +10 % |
| n=12 | +6,4 % | −22,0 % | 47 % | +23 % |

In der zweiten Fensterhälfte belegen sie Platz 50, 54 und 55 von 55.

Der Befund selbst (E23 rief die 1D-Ebene mit der 4h-Swing-Weite auf und maß deshalb
Feinstruktur statt Furkans Ebene) war **richtig** — die Schlussfolgerung daraus war
falsch. Mit der richtigen Weite wird es schlechter, weil die Engine dann tiefer und
häufiger kauft, mit einem Stop 18 % entfernt.

**Die Lehre, die bleibt:** Furkans Zonen sind Wartepositionen, keine Auslöser. Er hat
die Zone im Chart und kauft trotzdem nicht, solange der Order-Flow nicht passt
(„wenn ich hier nicht aufstocke, weil mir die Orderflow Daten nicht gefallen"). Die
Engine kauft bei Berührung. Dieselbe Linie, zwei verschiedene Dinge — ein größeres Bein
verstärkt diesen Unterschied, statt ihn zu schließen.

`zonen_1d` bleibt aus, `pivot_n_1d` bleibt 0. Der Parameter bleibt im Code (Default 0 =
altes Verhalten, getestet), damit die Messung dauerhaft nachvollziehbar ist.
