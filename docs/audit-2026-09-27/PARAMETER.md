# Vollständiges Parameter- und Vergleichsverzeichnis

Die Tabelle enthält alle 45 aktuellen `evaluate`-Parameter. **Code-Default ist nicht Live-Einstellung.** Maßgeblich für die konfigurierte Live-Engine ist `main` 89885adc. Am 28.09. wurde remote bis 97e375b geprüft: seit der eingefrorenen Basis änderten sich nur `state.json` und `signals.json`, nicht der Code oder die Konfiguration. Eine tatsächlich manuell ausgeführte Order folgt daraus nicht.

Implementierung: [strategy_core.evaluate](../../engine/strategy_core.py#L1655), Durchreichung [main.EVAL_DEFAULTS/eval_params](../../engine/main.py#L331), historische Definitionen und Datenstände in [ENTSCHEIDUNGEN.md](ENTSCHEIDUNGEN.md). Die Test-Suite umfasst alle vorhandenen `test_*.py`; spezifische zusätzliche Gegenproben sind im Abschlussbericht genannt. Einzelgegenprobe = nur dieser Parameter gegen die gemeinsame heutige Basis. Abhängige Einstellungen werden zusätzlich gemeinsam mit ihrem Hauptschalter geprüft.

| Parameter | Zweck / Herkunft | Code-Default | effektiv live | neue Einzelprobe(n) |
|---|---|---|---|---|
| `bias_long` | Long-Einstiege erlauben; E8.5 | `true` | true | V034 |
| `bias_short` | Short-Einstiege erlauben; E8.5/E10; F02 | `true` | false | V035 |
| `pivot_n` | Bestätigungsweite links/rechts für Hochs und Tiefs; E4 | `5` | 5 | keine abweichende Einzelzeile |
| `k_atr` | Mindestgröße eines Impulses relativ zur Schwankung; E4 | `2.0` | 2.0 | keine abweichende Einzelzeile |
| `flush_entry` | Einstieg bei Durchstich des GP und bestätigter Kapitulation; E8/E9 | `"core"` | "core" | V026, V036 |
| `tp_ladder` | Zwischenverkäufe vor den Hauptzielen; E8 | `true` | true | V037 |
| `strict_confirm` | Strengere Kombination von Flow-Bestätigungen; E8.5/E43.6 | `false` | false | V040 |
| `confluence` | Zusätzliche Tageszonen-Bestätigung; E8.5 | `false` | false | V041 |
| `conditional_stop` | Bedingtes Halten/Aufstocken unter Invalidierung; E9 | `false` | false | V042 |
| `buy_ladder` | Mehrere kleinere Käufe innerhalb der Zone; E9.8 | `true` | true | V024 |
| `release_stale_rest` | Rest bei veralteter Impulsstruktur verkaufen; E9.9/E43.8 | `false` | false | V043 |
| `trail_stop` | Stop nach Teilverkauf auf Einstand/Pivot nachziehen; E9.10; F03/F04 | `false` | true | V010 |
| `liq_exit` | An Liquidationsspitze oder historischer Zone teilverkaufen; E9.11/E14 | `"off"` | "off" | V044, V045, V046 |
| `high_exit` | Vor dem nächsten bestätigten Hoch teilverkaufen; E10/E14 | `"off"` | "on" | V009, V047 |
| `liq_entry` | An historischer Liquidationszone aufstocken oder Einstieg filtern; E10/E13 | `"off"` | "boost" | V027, V048 |
| `block_unhealthy` | Ungesunden Abverkauf beim Einstieg sperren; E13 | `false` | false | V049 |
| `muster5_entry` | Muster 5 als zusätzliche Long-Bestätigung; E38 | `false` | false | V050 |
| `muster5_halten` | Muster 5 beim Halten des Rests berücksichtigen; E38 | `"off"` | "off" | V051, V052 |
| `stop_puffer_pct` | Puffer unter Invalidierung vor Stop; E41 | `0.0` | 0.0 | V053 |
| `stop_rueckeroberung` | Eine oder drei Kerzen Rückeroberungsfrist; E41 | `0` | 1 | V017, V054 |
| `stop_auf_docht` | Stop schon bei Intrabar-Berührung statt Schluss; E41 | `false` | false | V055 |
| `confirm_t1` | Auch den ersten 0,5-Einstieg bestätigen lassen; E13/E43.6 | `false` | false | V056 |
| `cooldown_h` | Wartezeit nach Stop; E13/E43.6 | `0.0` | 0.0 | V057, V058 |
| `min_stop_pct` | Zu nahe anfängliche Stops verhindern; E13 | `0.0` | 0.02 | V059 |
| `no_flip` | Nach erstem Teilkauf/-verkauf Gegenrichtung derselben Kerze sperren; E18/E25 | `false` | true | V060 |
| `freeze_targets` | Zielreferenz nach erstem Teilverkauf einfrieren; E18 | `false` | false | V061 |
| `min_bein_pct` | Zu kleine Referenzimpulse überspringen; E19 | `0.0` | 0.05 | V062 |
| `bein_wahl` | Jüngstes oder größtes geeignetes Bein wählen; E19 | `"juengstes"` | "juengstes" | V063 |
| `be_im_plus` | Stop auf Einstand, sobald Position zuvor im Plus; E19/E43.8 | `false` | false | V064 |
| `bein_richtung` | Impuls nur in erlaubter Handelsrichtung wählen; E19/E43.2 | `"auto"` | "bias" | V019 |
| `widerstand_exit` | Teilverkäufe am GP eines Gegenbeins; E20; F05 | `"off"` | "off" | V065 |
| `rest_halten` | Rest bei Gegenmuster nicht verkaufen; E21/E26/E43.6/E44.5 | `false` | false | V001 |
| `neustart_mit_rest` | Neuer Einstieg bei noch laufendem Rest; E21/E26 | `false` | true | V066 |
| `zonen_1d` | Zusätzlicher Einstiegsversuch mit Tagesimpuls; E23/E32.3; F08 | `false` | false | V067 |
| `zonen_nachziehen` | Offene Kaufzonen bei intakter neuer Struktur aktualisieren; E30 | `false` | true | V020 |
| `pivot_n_1d` | Eigene Pivotweite für Tageszonen; 0 übernimmt 4h-Wert; E32.3 | `0` | 0 | V068, V069 |
| `trend_filter` | Einstieg auf erlaubter Seite der Tages-EMA; E8.5/E33; F08 | `false` | false | V038 |
| `trend_ema` | Länge der Tages-EMA; E33 | `200` | 200 | V039 |
| `ampel_filter` | Einstiegstranche nach Ampel halbieren; Gegenproben; E34 | `"off"` | "off" | V070, V071, V072 |
| `muster_cvd` | Relative Summenstände oder vergleichbare lokale USD-Deltas; E43.3; F06 | `"alt"` | "alt" | V029 |
| `muster_oi` | OI-Veränderung in USD oder BTC-Kontrakten; E43.4 | `"usd"` | "usd" | V028 |
| `high_exit_hist` | Pivot-Historie für Verkauf am Hoch begrenzen; E43.5/A5 | `"voll"` | "voll" | V073 |
| `ausbruch_ruecktest` | E42: nach verkauftem Hoch Ausbruch/Rücktest zurückkaufen; E42/E44.3/E44.5 | `false` | false | V004 |
| `ruecktest_fenster` | Frist des E42-Rücktests in 4h-Kerzen; E44.3/E44.5 | `12` | 12 | V074 |
| `verkauf_faktor` | Alle Teilverkaufstranchen verkleinern; E44.4/E44.5; nur Zweig | `1.0` | nicht implementiert auf main; Faktor effektiv 1 | V002 |

`verkauf_faktor` existiert auf E44.4/E44.5, nicht auf main. Der neutrale Faktor 1 wurde unabhängig gegen den eingefrorenen main-Code geprüft: identische Signale. `muster5_*`, `stop_puffer_pct`, `stop_auf_docht`, `strict_confirm`, `confluence` und `pivot_n_1d` können auch über ihren Code-Default wirksam ausgeschaltet sein, wenn kein eigener Schlüssel in `config.json` steht.

## Weitere Schalter und feste Größen

| Einstellung | tatsächlich / Default | Zweck und Beleg | Auditstatus |
|---|---|---|---|
| `vorschau_telegram` | true / true | Vorschau-Versand, E17; main.run_engine | Format-/Persistenztests; kein realer Versand im Audit |
| `plan_telegram` | true / true | Versand geänderter Positionspläne, E20 | F10/F13: Planstop und Zustellung fehlerhaft |
| `flush_wache` | true / true | Laufende Kerze beobachten, nur Warnung | Nicht mit abgeschlossenem Einstiegssignal verwechseln; kein Renditeschalter |
| Chart `planMarken` | pro Browser, standardmäßig an | E24: localStorage; zeichnet state.plan | Code geprüft; keine echte Benutzer-Browsersitzung geprüft |
| `deploy_pct` | nur Backtest, 1,0; historische Werte 0,6/0,5 | Anteil des verfügbaren Kapitals je Positionsbeginn, E10 | Kein Live-Ausführungsbuch. Ergänzende Kapitalprobe separat dokumentiert; keine Optimierung |
| Mehrbörsen-Spot, Futures-CVD, OI, Funding, Liquidationen | nicht live umgeschaltet | E37-Abruf-/Vergleichswege in coinalyze.py/backtest.py; keine gleichnamigen live EVAL-Schalter | Alte Rohantworten fehlen; F14/F15 und Datenverfügbarkeit begrenzen Schlussfolgerungen |
| Coinalyze versus Kraken-OI | hängt von verfügbarem API-Key/Antwort ab | main.fetch_market_data; mit erfolgreichem Coinalyze-OI dessen Zeitreihe, sonst Kraken-Snapshots | Konfigurationsdatei allein beweist die tatsächliche Datenquelle eines vergangenen Laufs nicht |
| Futures-CVD vorhanden / Ersatzweg | Laufzeitentscheidung bei fehlenden Daten | E16; kein gewöhnlicher Konfigurationsschalter | Haupttranskript verlangt Trennung; heutige CVD-Gegenproben ersetzen keinen ursprünglichen Datenvergleich |
| STH-Kostenbasis | Anzeige; zwei Anbieter, unterschiedlich definiert/verzögert | E40; main.sth_kostenbasis | Kein Einstiegsfilter; historische Veröffentlichung nicht rekonstruiert |
| Makro-KI, MVRV-Z, Regime-Shorts E44.6 | nicht gebaut | E8.5/E29/E44-Plan | Keine nachträglich behauptete Wirksamkeitsmessung; E44.6 hier nicht umgesetzt |
| `be_nach_aufstockung` | auf ausdrücklichen Nutzerwunsch zurückgenommen | E28; nie öffentlich live | Kein bestehender Schalter; kein Anlass zur eigenmächtigen Wiedereinführung |

Feste Strategiegrößen (zusätzlich zu den Schaltern, nicht alle empirisch kalibriert):

| Konstante | Wert |
|---|---|
| `BEIN_PIVOTS` | `12` |
| `SPOT_FENSTER` | `3` |
| `OF_FENSTER` | `12` |
| `OF_FLACH_ANTEIL` | `0.3333333333333333` |
| `AMPEL_TRANCHE` | `0.5` |
| `TRANCHEN` | `{"T1": 25, "CORE": 50, "FULL": 25, "TP1": 40, "TP2": 40}` |
| `MAX_DIP_BUYS` | `2` |
| `DIP_FLOOR_PCT` | `0.05` |
| `DIP_TRANCHE` | `20` |
| `MAX_BUY_RUNGS` | `3` |
| `BUY_LADDER_TRANCHE` | `15` |
| `LADDER_FACTORS` | `[0.8, 0.9]` |
| `LADDER_TRANCHE` | `15` |
| `MAX_LIQ_EXITS` | `3` |
| `LIQ_SPIKE_MULT` | `3.0` |
| `LIQ_LOOKBACK` | `180` |
| `LIQ_ZONE_TOL` | `0.005` |
| `LIQ_ZONE_MIN_MULT` | `3.0` |
| `MAX_WIDERSTAND_EXITS` | `2` |
| `MAX_HIGH_EXITS` | `2` |
| `HIGH_EXIT_TOL` | `0.005` |
| `HIGH_EXIT_LIVE_KERZEN` | `1300` |
| `MAX_LIQ_ENTRIES` | `2` |
| `LIQ_ENTRY_TRANCHE` | `20` |
| `RUECKTEST_FENSTER` | `12` |
| `RUECKTEST_TOL` | `0.005` |
| `RUECKKAUF_TRANCHE` | `25` |

Weitere fest kodierte Mustergrenzen stehen in `classify_pattern` (u. a. Preis ±1/2 %, OI +3/−5 %, Funding 0,0001), ATR als einfacher 14-Kerzen-Mittelwert, grundlegende Impuls-Untergrenze 3 % alternativ zum ATR-Kriterium. Diese Zahlen sind keine vollständig aus dem Transkript belegten Regeln. Die neuen Messungen variieren sie nicht nachträglich.

## Jede bestehende Gitterzeile: Entfernung zur heutigen Basis

Diese Tabelle rekonstruiert **alle 85 bestehenden Code-Konfigurationen**, unabhängig davon, ob ihr Name noch „LIVE“ enthält. Änderungen werden aus den effektiven Parametern berechnet. Mehrere Unterschiede sind keine Einzelgegenprobe. Der heutige 79-Zeilen-Audit übernimmt die alten Parameterwerte, setzt sie aber auf dieselbe Basis; er ist deshalb ausdrücklich keine Reproduktion des alten Laufs.

| alte Gitterzeile | Anzahl Unterschiede | wirkliche Unterschiede zu heute |
|---|---:|---|
| nur Long (Basis) | 12 | flush_entry="off", buy_ladder=false, trail_stop=false, high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| +Kaufleiter | 11 | flush_entry="off", trail_stop=false, high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| +Flush core | 11 | buy_ladder=false, trail_stop=false, high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE: nur Long +Kaufleiter +Flush core | 10 | trail_stop=false, high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| +Kaufleiter +Bed.Stop | 12 | flush_entry="off", conditional_stop=true, trail_stop=false, high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Rest-Freigabe | 11 | release_stale_rest=true, trail_stop=false, high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop nachziehen | 9 | high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop nachziehen +Rest-Freigabe | 10 | release_stale_rest=true, high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Liq-Kaskade | 10 | liq_exit="spike", high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Liq-Zonen | 10 | liq_exit="zone", high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Liq beides | 10 | liq_exit="both", high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| MEINE Einstellung ohne Flush | 1 | flush_entry="off" |
| LIVE +Stop +Liq-Konfluenz aufstocken | 8 | high_exit="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +nur bei Liq-Konfluenz einsteigen | 9 | high_exit="off", liq_entry="filter", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Verkauf am letzten Hoch | 8 | liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Verkauf am schwachen Hoch | 9 | high_exit="weak", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop, 60 % Einsatz (40 % Reserve) | 10 | high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false, deploy_pct=0.6 |
| LIVE +Stop, 50 % Einsatz (50 % Reserve) | 10 | high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false, deploy_pct=0.5 |
| LIVE +Stop +Warnlicht (kein Kauf in ungesunden Abverkauf) | 10 | high_exit="off", liq_entry="off", block_unhealthy=true, stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Flow-Pruefung am 0.5-Level | 10 | high_exit="off", liq_entry="off", stop_rueckeroberung=0, confirm_t1=true, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Sperre 48 h nach Stop | 10 | high_exit="off", liq_entry="off", stop_rueckeroberung=0, cooldown_h=48, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Mindest-Stopabstand 2 % | 8 | high_exit="off", liq_entry="off", stop_rueckeroberung=0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Sperre 48 h +Mindestabstand 2 % | 9 | high_exit="off", liq_entry="off", stop_rueckeroberung=0, cooldown_h=48, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +alle vier neuen Hebel | 11 | high_exit="off", liq_entry="off", block_unhealthy=true, stop_rueckeroberung=0, confirm_t1=true, cooldown_h=48, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Mindestabstand 2 % +Liq-Konfluenz | 7 | high_exit="off", stop_rueckeroberung=0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Stop +Sperre 48 h +Liq-Konfluenz | 9 | high_exit="off", stop_rueckeroberung=0, cooldown_h=48, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Verkauf unter dem letzten Hoch | 6 | stop_rueckeroberung=0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Verkauf an den Liquidations-Niveaus | 8 | liq_exit="zone", high_exit="off", stop_rueckeroberung=0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Verkauf unter dem Hoch +an den Liq-Niveaus | 7 | liq_exit="zone", stop_rueckeroberung=0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +kein Gegengeschaeft je Kerze | 5 | stop_rueckeroberung=0, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Ziele festhalten | 7 | stop_rueckeroberung=0, no_flip=false, freeze_targets=true, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +kein Gegengeschaeft +Ziele festhalten | 6 | stop_rueckeroberung=0, freeze_targets=true, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Mindest-Bein 5 % | 5 | stop_rueckeroberung=0, no_flip=false, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +groesstes Bein | 7 | stop_rueckeroberung=0, no_flip=false, min_bein_pct=0.0, bein_wahl="groesstes", bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Mindest-Bein 5 % +groesstes Bein | 6 | stop_rueckeroberung=0, no_flip=false, bein_wahl="groesstes", bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Bein in Handelsrichtung | 5 | stop_rueckeroberung=0, no_flip=false, min_bein_pct=0.0, neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Bein in Handelsrichtung +Mindest-Bein 5 % | 4 | stop_rueckeroberung=0, no_flip=false, neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Break-even im Plus | 7 | stop_rueckeroberung=0, no_flip=false, min_bein_pct=0.0, be_im_plus=true, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Bein-Wahl +Break-even im Plus | 7 | stop_rueckeroberung=0, no_flip=false, bein_wahl="groesstes", be_im_plus=true, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Widerstand des Gegen-Beins | 6 | stop_rueckeroberung=0, no_flip=false, bein_richtung="auto", widerstand_exit="on", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Widerstand statt Verkauf am letzten Hoch | 7 | high_exit="off", stop_rueckeroberung=0, no_flip=false, bein_richtung="auto", widerstand_exit="on", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Rest halten | 6 | stop_rueckeroberung=0, no_flip=false, bein_richtung="auto", rest_halten=true, neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE +Rest halten +Neustart mit Rest | 5 | stop_rueckeroberung=0, no_flip=false, bein_richtung="auto", rest_halten=true, zonen_nachziehen=false |
| LIVE +Neustart mit Rest (ohne Halten) | 4 | stop_rueckeroberung=0, no_flip=false, bein_richtung="auto", zonen_nachziehen=false |
| NEU-LIVE +1D-Ebene als zweiter Zonensatz | 6 | stop_rueckeroberung=0, no_flip=false, bein_richtung="auto", neustart_mit_rest=false, zonen_1d=true, zonen_nachziehen=false |
| NEU-LIVE +1D-Ebene, ohne Mindest-Bein (Gegenprobe) | 7 | stop_rueckeroberung=0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_1d=true, zonen_nachziehen=false |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft | 4 | stop_rueckeroberung=0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| NEU-LIVE +Mindest-Bein 5 % +kein Gegengeschaeft +Ziele festhalten | 5 | stop_rueckeroberung=0, freeze_targets=true, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE-heute +Neustart mit Rest | 3 | stop_rueckeroberung=0, bein_richtung="auto", zonen_nachziehen=false |
| LIVE-heute +Rueckeroberung vor dem Stop (1 Kerze) | 1 | bein_richtung="auto" |
| LIVE-heute +Trendfilter EMA200 | 2 | trend_filter=true, bein_richtung="auto" |
| LIVE-heute +Trendfilter EMA50 | 3 | trend_filter=true, trend_ema=50, bein_richtung="auto" |
| LIVE-heute +1D-Ebene grob (n=8) | 3 | bein_richtung="auto", zonen_1d=true, pivot_n_1d=8 |
| LIVE-heute +1D-Ebene fein (n=5, Gegenprobe zu E23) | 2 | bein_richtung="auto", zonen_1d=true |
| LIVE-heute +1D-Ebene sehr grob (n=12) | 3 | bein_richtung="auto", zonen_1d=true, pivot_n_1d=12 |
| LIVE-heute +Ampel klein bei unguenstig | 1 | ampel_filter="klein" |
| LIVE-heute +Ampel UMGEKEHRT (Gegenprobe) | 1 | ampel_filter="gross" |
| LIVE-heute +immer halbe Tranche (Nullhypothese) | 1 | ampel_filter="immer" |
| LIVE-heute +Rest halten +Neustart mit Rest | 4 | stop_rueckeroberung=0, bein_richtung="auto", rest_halten=true, zonen_nachziehen=false |
| LIVE-heute +Muster 5 als Kauf-Bestaetigung | 1 | muster5_entry=true |
| LIVE-heute +Muster 5 haelt Zwischenverkaeufe | 1 | muster5_halten="leiter" |
| LIVE-heute +Muster 5 haelt ALLE Teilverkaeufe | 1 | muster5_halten="alle" |
| LIVE-heute +Muster 5 sperrt Kaeufe (Bremse, Gegenprobe) | 1 | block_unhealthy=true |
| LIVE-heute +Muster 5 Kauf UND Halten (zwei Unterschiede) | 2 | muster5_entry=true, muster5_halten="leiter" |
| LIVE bis 21.09.2026 (Stop ohne Rueckeroberung) | 1 | stop_rueckeroberung=0 |
| LIVE-heute +Rueckeroberung 3 statt 1 Kerze (Robustheit) | 1 | stop_rueckeroberung=3 |
| LIVE-heute +Bein in Handelsrichtung | 0 | identisch |
| LIVE bis 26.09.2026 (ohne Bein-Richtung) | 1 | bein_richtung="auto" |
| LIVE-heute +Muster 2 in Dollar (E43.3) | 1 | muster_cvd="usd" |
| LIVE-heute +OI in Kontrakten (E43.4) | 1 | muster_oi="btc" |
| LIVE-heute +Pivot-Hoch nur letzte 1.300 Kerzen (A5) | 1 | high_exit_hist="live" |
| LIVE-heute +Rest halten (E43.6) | 1 | rest_halten=true |
| LIVE-heute +Strenge Bestaetigung (E43.6) | 1 | strict_confirm=true |
| LIVE-heute +Bestaetigung am 0.5-Level (E43.6) | 1 | confirm_t1=true |
| LIVE-heute +Sperrfrist nach Stop 48h (E43.6) | 1 | cooldown_h=48.0 |
| LIVE-heute +Break-even im Plus (E43.8) | 1 | be_im_plus=true |
| LIVE-heute +Rest-Freigabe bei neuer Struktur (E43.8) | 1 | release_stale_rest=true |
| Long+Short (Ref) | 13 | bias_short=true, flush_entry="off", buy_ladder=false, trail_stop=false, high_exit="off", liq_entry="off", stop_rueckeroberung=0, min_stop_pct=0.0, no_flip=false, min_bein_pct=0.0, bein_richtung="auto", neustart_mit_rest=false, zonen_nachziehen=false |
| LIVE-heute +kleinere Verkaeufe | 1 | verkauf_faktor=0.67 |
| LIVE-heute +kleinere Verkaeufe +Rest halten | 2 | rest_halten=true, verkauf_faktor=0.67 |
| LIVE-heute +E42 | 1 | ausbruch_ruecktest=true |
| LIVE-heute +E42 +Rest halten | 2 | rest_halten=true, ausbruch_ruecktest=true |
| LIVE-heute +E42 +kleinere Verkaeufe | 2 | ausbruch_ruecktest=true, verkauf_faktor=0.67 |
| LIVE-heute +E42 +kleinere Verkaeufe +Rest halten | 3 | rest_halten=true, ausbruch_ruecktest=true, verkauf_faktor=0.67 |
| LIVE-heute +E42 (6 Kerzen, Robustheit) | 2 | ausbruch_ruecktest=true, ruecktest_fenster=6 |
