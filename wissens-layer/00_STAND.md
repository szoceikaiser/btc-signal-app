# 00 STAND — Kurzstand in einer halben Minute

## Historischer Folgeauftrag nach Etappe 6 — 29.09.2026

- Direkt aus 05208cecce8d5a0e856a1ea56984b209f403ccd6, eigener Zweig
  codex/nach-6-historische-auswertung; kein neuer main-/E44.4-/E44.5-Code.
- R0 unverändert; R1 bis fest 29.09.2026 12:00 UTC vollständig ergänzt:
  13 neue abgeschlossene Kerzen, 2.480 alte abgeschlossene Präfixkerzen feldgleich.
  Nutzer erlaubte im laufenden Auftrag GitHub-Läufe. Isolierter Rohdatenlauf
  36592684701 nutzte Coinalyze-Secret, ohne Repo-Schreibrechte/Telegram/Pages.
- 60 feste kausale Läufe: R0/R1 × Basis/E42 × S0–S4 × drei Startpunkte.
  7.338 Fills / 60.630 Closes unabhängig geprüft; keine neuen Suchalternativen.
- R1 Hauptfall S1: Basis 12.813,81 USD, E42 12.639,84 USD (−173,96 USD,
  −1,3576 % relativ), Schluss-DD 8,4989 / 9,0636 %, obere Grenze 9,9428 / 10,2437 %.
  Basis dominiert S0/S1/S2/S4; S3 +117,27 USD für E42 bei höherem Schluss-DD.
- 20.000 stationäre gepaarte Tages-Bootstraps, Seed 20260929, Block 14/7/28,
  alle Ergebnisse/Monate/Drittel/Frischstarts berichtet. S1-Hauptintervall R1
  −4,1660 bis +1,4369 %, p_cond 0,839658; nur bedingt, Auswahlbereinigung nicht belegt.
  Historische Vintages/erreichbare Live-Fills bleiben unbelegt, keine Power-Zusage.
- 741 Tests (728 alte unverändert), 6 synthetische Testgruppen, 15 neue Schutzproben;
  alle alten F17/F13/4/3b/D01/F09-Proben erhalten. Isolierte i+2-Rundungskorrektur
  samt Gegenfall/Planrevision dokumentiert; bisheriger V1-/Checkpointcode unverändert.
- Bericht docs/nach-6/BERICHT.md, vollständige Ergebnisse/CSV/Ledger/Manifeste daneben.
  Exakte Abschluss-SHA/CI/Bundle/ZIP/Restore: lokale
  audit-backups/nach-6-abschluss-<Kurz-SHA>/ABSCHLUSS.json.
- Live-Konfiguration, site, Versandliste und Produktions-Engine unverändert;
  kein main-Merge, keine Nachrichten/Orders/Deployments, kein Live-Go.
  F13-uncertain blockiert; kein Reset/Exactly-once, manueller Bestand unbekannt.
  Runnerverlust vor Git-Persistenz sowie V2/Shorts/E41.6 bleiben separat offen.
- Auftrag danach beenden. Weitere Kandidaten, Auswahlbereinigung und Live-Entscheidungen
  ausschließlich separat; kein automatischer Folgeauftrag.

## Aktueller Arbeitsstand 29.09.2026: Etappe 6, retrospektives Design v2

- Sechs eingefrorene V1-Läufe exakt reproduziert: 1.101 Fills / 9.054 Closes
  unabhängig geprüft, 728 Tests unverändert. Basis exakt bb862204c97c6bb4c0da49cb6f1de90dd58af663.
- Nutzer verlangt historische Prüfung bis jetzt ohne Jahreswartezeit. Zukunfts-
  fenster aufgehoben; unbestätigte 2-%-Nutzen-/15/20/+2-DD-Budgets zurückgezogen.
  Feste Wirkung/Risiko/Dominanz, Zeitabschnitte, Kosten/Latenz und Unsicherheit;
  frühere Auswahl gesondert berücksichtigen, kein erfundenes unabhängiges Fenster.
- R0-Befund endet 27.09.; R1 bis 29.09.2026 12:00 UTC geplant, noch keine neuen
  Inputs beschafft/Messungen. Statistik/i+2/Quellenmanifest/Suchinventar offen.
  Keine erneute Zustimmung zu den alten Vorschlägen nötig. Kein Live-Go.
- Zweig codex/etappe-6-reproduktion-design, Arbeitsbaum etappe-6-work;
  Bericht/Design/Register in docs/nacharbeit-2026-09-28. Exakte SHA/CI/Bundle/ZIP/
  vollständiger Restore in audit-backups/6-abschluss-<Kurz-SHA>/ABSCHLUSS.json.
  Alte v1-Sicherung efc3b1a bleibt erhalten.
- Nächster separater Auftrag: START-NACH-6.md, retrospektive Umsetzung/Auswertung;
  keine automatische Folgearbeit. Engine/site/Workflows/Daten/Verträge unverändert.
  F13-Betriebsgrenzen, unbekannter Live-Bestand, V2/Shorts/E41.6 bleiben offen.

## Aktueller Arbeitsstand 29.09.2026: Etappe 5b F17 abgeschlossen

- Chart erhält alle Quellen/Kollisionen: L Live-Referenz, H historische Diagnostik,
  optional V1 Modell-Fills. Deterministische Chartidentitäten, vollständige
  Ereignisliste, reine Altbestandsprojektion ohne Versand-/Zustandsänderung.
- **728 Tests**, alle **712 alten unverändert**, 16 neue; **16/16 F17-Sabotagen**.
  5a 16/16, 4 23/23, 3b 19/19, D01 6/6, F09 3/3 erhalten. 1.101 gespeicherte
  V1-Fills auf Zeit/Preis/Identität projiziert, keine historische Neuberechnung.
- Engine, Versandliste, Strategie, Konfiguration, historische Daten und Workflows
  identisch zur gesicherten Basis 6c0c6fdd56db9bb27febaf42c56f6e33bcab0685.
  Keine echte Zustellung/Orders/Deployments/main-Push/Merges/Dispatches, kein Live-Go.
- Grenzen aus 5a bleiben: uncertain sperrt Folge, keine Exactly-once-Garantie,
  ephemerer Runnerverlust vor Git-Persistenz offen. Chart-ID ist kein Zustellbeleg;
  identische Altduplikate erlauben keine nachträgliche Einzelzuordnung.
- Zweig `codex/etappe-5b-chart-identitaet`, Arbeitsbaum `etappe-5b-work`, Bericht
  `docs/nacharbeit-2026-09-28/ETAPPE-5B-ABSCHLUSS.md`. Exakte SHA/CI/Restore lokal
  `audit-backups/5b-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.
- Nächster **separater** Auftrag: Etappe 6, `START-6.md`; Sol/mittel für begrenzte
  Reproduktion, Astra/hoch für Bestätigungsdesign. Nichts automatisch starten.

## Aktueller Arbeitsstand 29.09.2026: Etappe 5a abgeschlossen

- F13 im Hauptlauf: atomare Position/Dedupe/Versandabsicht in state.json,
  stabile lokale Nachrichten-ID und Text, dauerhafte Versandliste Version 1.
  Signal-/OI-/Flush-Projektionen werden beim Neustart repariert.
- Sicher abgelehnte/pending Sendungen werden geordnet wieder versucht,
  bestätigte nie wiederholt. Timeout/unterbrochener Versuch ist uncertain und
  blockiert Nachfolger. Keine Exactly-once-Zusage oder erfundene manuelle Fills.
- **712 Tests**, alle **676 alten unverändert**, 36 neue; **16/16 F13-Sabotagen**.
  4 23/23, 3b 19/19, D01 6/6, F09 3/3 erhalten. Fünf reale Prozessabbrüche
  netzfrei geprüft; kompletter Restore mit sechs identischen V1-Fortsetzungen.
- Strategie, site, Workflows, Live-Konfiguration und bestätigte Verträge identisch
  zu ebc01a4. Keine Nachrichten/Orders/Deployments/main-Push/Merges oder Dispatches.
- Lokale Dauerhaftigkeit gilt bei überlebendem Datenpfad. Der bestehende ephemere
  GitHub-Runner committet erst nach dem Lauf; Verlust davor bleibt Betriebsgrenze.
  Unklarheit benötigt separate Klärung. Eigenständige watch/lage/test/resend-
  Befehle bleiben Einmalbefehle. Kein Live-Go.
- Zweig `codex/etappe-5a-telegram-outbox`, Arbeitsbaum `etappe-5a-work`, Basis
  `ebc01a48057994629c021bd84ab7f9a236678b70`. Bericht
  `docs/nacharbeit-2026-09-28/ETAPPE-5A-ABSCHLUSS.md`; exakte SHA/CI/Restore in
  `audit-backups/5a-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.
- Nächster **separater** Auftrag: 5b/F17, **GPT-6 Sol / mittel**, bei unklaren
  Herkunftskollisionen hoch. `START-5B.md`. 5a beenden, nichts automatisch starten.

## Aktueller Arbeitsstand 29.09.2026: Etappe 4 abgeschlossen

- F03/F04/F05/F10: V1-Restlose und gebührenhaltige Kosten, proportionaler Verkauf,
  gezielter E42-Teilstop, monoton gespeicherter Long-Stop und gemeinsamer Positionsplan.
- Signalreferenz, simulierte Fills und unbekannter manueller Live-Bestand bleiben
  ausdrücklich getrennt. Kein erfundener Live-Einstand, kein Altpositionsreset.
- Positionsschema 2; vollständige V1-Checkpoints Version 1 einschließlich Absichten,
  Reservierungen, Kosten, E41/E42 und Risiko. `widerstand_exits` bleibt erhalten.
- **676 Tests**, **23/23 neue Sabotagen**, 3b 19/19, D01 6/6, F09 3/3.
  Vier Auditfehler auf 3b reproduziert. Sechs festgelegte lokale Vergleiche:
  1.101 Fills / 9.054 Closes unabhängig geprüft, sechs Prozessneustarts exakt gleich.
- Ohne Slippage: Live-Basis 13.418,88 USD (−12,57 gegenüber 3b), E42 13.299,89 USD
  (+49,02); obere Intrabar-DD-Grenze jeweils **9,9428 %**. Keine Strategieauswahl.
- Zweig `codex/etappe-4-bestand-stop`, Arbeitsbaum `etappe-4-work`, Basis `9606a6f`.
  Bericht `docs/nacharbeit-2026-09-28/ETAPPE-4-ABSCHLUSS.md` nennt jede Testanpassung
  und die Grenzen. Exakte Abschluss-SHA/CI/Restore lokal in
  `audit-backups/4-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.
- Kein main-/Live-Go; Originale/Tag/Workflows unverändert. Nächster **getrennter**
  Auftrag: Etappe 5a (F13), **GPT-6 Sol / hoch**, siehe `START-5A.md` im Berichtsordner.
  F17 bleibt 5b; keine Folgeetappe automatisch starten.

## Aktueller Arbeitsstand 28.09.2026: Etappe 3b abgeschlossen

- F01/F12-Vertrag V1 umgesetzt im neuen Offline-Pfad `backtest.run_execution`:
  Schlusswissen → direkt folgendes zulässiges Open, Cash/BTC-Reservierungen,
  echte Fills/Ablehnungen vor der nächsten Entscheidung, D2-Ausgangspriorität.
- **638 Tests**, **19/19 neue Sabotagen**, 16 Handfälle; D01 6/6, F09 3/3 erhalten.
  Zwei vorab begrenzte eingefrorene Zeilen × drei Slippage-Szenarien lokal gemessen;
  jeder Fill, Close-Bestand, Monatsstand, Gebühren und DD gegen unabhängige Lose geprüft.
- Schluss-DD und **obere Intrabar-Grenze** als neue positive Verlustfelder.
  Alte Schwellen nicht übertragen. Live-Basis ohne Slippage: 13.431,45 USD,
  Close-DD 7,9166 %, obere Grenze 9,9428 %; kein Strategie-/Live-Go.
- Zweig `codex/etappe-3b-f01-f12`, Arbeitsbaum `etappe-3b-work`, Basis exakt `67c8e62`.
  Bericht `docs/nacharbeit-2026-09-28/F01-F12-UMSETZUNG.md`; exakte Abschluss-SHA/CI
  und Bundle-Wiederherstellung lokal `audit-backups/3b-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.
- Bisheriger Signalband-/Backtest-Workflow bleibt historische Diagnostik, kein V1-Beleg.
  Main/site/Live-Schalter/Workflows/Originale/Sicherungstag unverändert durch 3b.
  F03/F04/Persistenz offen; nächster getrennter Auftrag **Etappe 4, GPT-6 Astra / hoch**
  für Entwurf/Prüfung, danach Sol / hoch für klare Umsetzung. 3b beenden.

## Aktueller Arbeitsstand 28.09.2026: Etappe 3a abgeschlossen

- Ausführungs-/Risikovertrag F01/F12 festgelegt, **keine 3b-Umsetzung**.
  Basis D01 `5fabe2b`, eigener Zweig `codex/etappe-3a-ausfuehrungsvertrag`
  in `vertrag-3a-work`.
- Nutzer bestätigt: Schluss-Signale zum nächsten Open; Gesamtausstieg vor
  Teilstop vor Teilverkauf, bei Verkauf kein Kauf im selben Paket; Long/Spot,
  Schluss-DD plus Intrabar-Grenzen, Gebühr 0,1 %, Slippage 0/0,1/0,5 % je Seite.
- 16 Handfälle, 27 rationale Rechenprüfungen, acht falsche Kontrollwerte erkannt;
  drei gezielte Ist-Proben bestätigen weiterhin F01/F12. **600 Tests bestanden**.
  Produktionscode, Live-Konfiguration und historische Ergebnisse unverändert.
- Bericht: `docs/nacharbeit-2026-09-28/F01-F12-VERTRAG.md`.
  Neue DD-Schwellen, E41.6 und bedingte Vorab-Orders bleiben getrennte Entscheidungen.
- Nächster eigener Chat: **3b, GPT-6 Sol / hoch**, Aufwand hoch beibehalten.
  Vollständiger Auftrag: `docs/nacharbeit-2026-09-28/START-3B.md`.
  Kein main-/Live-Go. Abschluss auf eigenem GitHub-Zweig, lokale Sicherung unter
  `audit-backups/3a-abschluss-<Kurz-SHA>`. Etappe 3a hier beenden.

## Abgeschlossener Arbeitsstand 28.09.2026: Audit-Nacharbeit, Etappe 2

- D01 abgeschlossen auf `codex/fix-d01-kerzenschluss`, aus F09 `6edb941`:
  nur am Messstichtag abgeschlossene 4h-Kerzen; gespeicherte Daten verwenden ihr
  damaliges `ende`. OHLC/Flow und Teilfenster gemeinsam abgegrenzt.
- **600 Tests**, sechs von sechs D01-Sabotagen erkannt. Eingefrorene Daten:
  2.481 -> 2.480 Kerzen; fuenf Varianten jeweils ein Signal weniger; Endwert
  gegen F09 allein um 0,36 bis 0,66 USD niedriger. Unabhaengiges Losbuch passt.
- Bericht: `docs/nacharbeit-2026-09-28/D01.md`. Originale/F09-Ergebnisse unveraendert.
- Main/Live und Sicherungstag unveraendert durch diese Arbeit; kein Merge-Go.
  Naechste getrennte Etappe 3a F01/F12: **GPT-6 Astra / hoch** fuer den Vertrag,
  danach Umsetzung 3b **GPT-6 Sol / hoch**. D01 hier beenden.

## Abgeschlossene Etappe 1 (historische Referenz)

- Arbeitszweig `codex/fix-f09-wiederanlage`, aus main `469be65`.
- F09 (Rundungsrest verhindert Wiederanlage) ist isoliert korrigiert: 589 Tests,
  drei von drei gezielten Sabotagen erkannt, fuenf eingefrorene Vergleiche mit
  unabhaengiger Buchfuehrung abgeglichen. Hauptbericht: `docs/nacharbeit-2026-09-28/F09.md`.
- Main/Live bleiben unveraendert; E44.4/E44.5 nicht uebernommen. Sicherungstag:
  `sicherung/vor-audit-korrekturen-2026-09-28`. Main-Basissuite hier: 585 Tests.
- Naechste getrennte Etappe: D01, nur abgeschlossene Kerzen. Empfehlung:
  **GPT-6 Sol, Aufwand mittel**. Etappen und Startauftrag: `docs/nacharbeit-2026-09-28/ETAPPEN.md`.
- Originalaudit liegt separat auf `codex/audit-2026-09-27`, Abschluss `ccf2b01`.

## Aelterer Kurzstand (historische Referenz, nicht der aktuelle Arbeitsstand)

> **Diese Datei wird zuerst gelesen, auch von jeder KI.** Sie ist bewusst kurz und wird
> nach jeder abgeschlossenen Arbeit fortgeschrieben (Datum, was fertig, was als
> Nächstes). Ausführlich: `START-HIER.md`, dann `02_status/UEBERGABE.md`.
>
> Stand: **27.09.2026 (18)**

## Lage

- **Seit 26.09.2026 liegen Code UND Unterlagen im Repo `btc-signal-app`** (öffentlich).
  Die KI committet selbst auf einen Arbeitszweig; in `main` (live) erst nach Kaisers
  „Go“. Das private Repo `260729-btc-trading-backup` ist nur noch ein Backup. Alte Pfade
  `signal-app\...` meinen jetzt die Repo-Wurzel. Einzelheiten: `START-HIER.md`.
- Die Engine **läuft live** und handelt nicht selbst: sie sendet Telegram-Signale,
  Kaiser platziert die Orders. Webseite: `szoceikaiser.github.io/btc-signal-app`.
- **Tests:** in `main` **545**, alle grün (`cd engine && python3 run_tests.py`); auf dem
  Zweig `claude/e44-3-ausbruch-ruecktest-k7m2qx` (E44.3) **585**.
  Sabotage-Proben: fünf ältere (151 Sabotagen) plus `sabotage_e43.py` (7), alle gefangen;
  neu `sabotage_e443.py` (42 Sabotagen, alle gefangen).
- **NEU 27.09.2026: E44.3 gebaut (Zweig, wartet auf Kaisers Go).** E42 „Ausbruch mit
  Rücktest“ als Schalter `ausbruch_ruecktest` (Default **aus**), Kaisers Werte (12 Kerzen,
  25 %, Stop bei Schluss unter der Marke). **Kaiser 27.09.: der Stop gilt nur für die 25 %.**
  Handelsverhalten unverändert, solange aus. Noch nicht gemessen (E44.5). Einzelheiten:
  `docs\PLAN-E44-KOMBINATIONEN.md`, Abschnitt 6 K1 „Bau-Auslegung“, und `UEBERGABE.md` (24).
- **Kaisers Go 26.09.2026: E43.1 und E43.2 live.** Arbeitszweig nach `main` gemerged.
  E43.1 (Futures-CVD im Lage-Abruf jetzt in Dollar) ist reine Anzeige. E43.2
  (`bein_richtung: "bias"`) hat die vorab festgelegte Entscheidungsregel erfüllt (beide
  Fensterhälften ≥ 1 Punkt besser, Rückgang 1,0 Punkt flacher statt tiefer) und ist seit
  26.09.2026 live (`site/data/config.json`, Panel-Zeile in `backtest.py` mitgewandert).
  Einzelheiten und Messwerte: `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`.
- Letzte Live-Änderung am Handelsverhalten davor: **E41, Kaisers Rückeroberungs-Regel**
  (`stop_rueckeroberung: 1`), live seit 21.09.2026.
- **Streitpunkt dazu (erledigt 26.09.2026, siehe oben):** Die Ausschalt-Regel für E41
  hatte am 23.09.2026 angeschlagen (Rückgang 1,5 Punkte tiefer als erlaubt 1,0); Kaiser
  hatte sie bewusst überstimmt. Begründung: `docs\PLAN-E41-STOP.md`, Abschnitt „Nachmessung
  23.09.2026".
- Letzte Anzeige-Änderung: **STH-Kostenbasis im Lage-Abruf** (E40, 21.09.2026).
- **Gesamtprüfung 26.09.2026** (`docs\PRUEFUNG-2026-09-26-GESAMT.md`): Grundgerüst
  (Fib, Tranchen, Ziele, Zonen) richtig verstanden und gebaut. **Vier Fehler bewiesen,
  noch nicht behoben:** (A1) Futures-CVD im Lage-Abruf ist BTC, wird als $ angezeigt;
  (A2) Muster 2 „Derivate-Pump“ hängt vom Startpunkt der CVD-Summe ab, live anders als
  im Backtest; (A3) Open Interest in $ bewegt sich schon mit dem Kurs und erfüllt so die
  Schwellen von Muster 2 und 4; (A4) der zugehörige Test erreicht den Zweig nie. Dazu:
  16 von 25 ausgeschalteten Schaltern nie gegen die heutige Live-Zeile gemessen, vorneweg
  `bein_richtung: bias` (Furkans zwei Raster).

- **Kaisers Go 26.09.2026: E43.5 und E43.3 in `main`** (Handelsverhalten unverändert):
  E43.5 fertig (Test „mehr Historie“ erreicht jetzt Muster 2), **E43.3 gebaut und
  gemessen**: nur 2 von 1.504 Kerzen anders, Rendite identisch, Regel nicht erfüllt,
  `muster_cvd` bleibt `"alt"`. **467 Tests grün in `main`.**
- **E41-Streitpunkt erledigt (26.09.2026):** Auf der neuen Live-Basis
  (`bein_richtung: "bias"`) schlägt die Ausschalt-Regel nicht mehr an, der Bericht
  meldet „Bleibt an“ (`docs\PLAN-E41-STOP.md`, „Nachmessung 26.09.2026“).
- **A5 gemessen und entschieden (26.09.2026), seit 26.09.2026 in `main`:** „Teilgewinn
  am letzten Hoch“ hing von der Länge der geladenen Historie ab (53 von 1.177 Kerzen
  anders erkannt) — Gitterzeile `high_exit_hist="live"` gebaut, Rendite/Hälften/
  Rückgang identisch, Regel nicht erfüllt, bleibt `"voll"`. Einzelheiten:
  `OFFENE-PUNKTE.md` Punkt 8, `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md` Abschnitt „A5“.
- **E43.6 gemessen (26.09.2026), seit 26.09.2026 in `main`:** vier seit Monaten
  unentschiedene Schalter (`rest_halten`, `strict_confirm`, `confirm_t1`,
  `cooldown_h=48`) mit genau einem Unterschied gegen die Live-Zeile gemessen — **alle
  vier Regeln nicht erfüllt, alle vier bleiben aus.** `strict_confirm` sah in H1 sogar
  besser aus, drehte in H2 aber um 7,6 Punkte. Einzelheiten: `docs\PLAN-E43-
  PRUEFUNGS-KORREKTUREN.md`, Abschnitt „Messung E43.6“.
- **E43.8 gemessen (26.09.2026, Arbeitszweig):** die letzten zwei unentschiedenen
  Schalter (`be_im_plus`, `release_stale_rest`) gemessen — **beide Regeln nicht
  erfüllt, beide bleiben aus.** `be_im_plus` ist dabei ein echter, großer Befund
  (Rendite +35,3 % → +18,0 %, +104 Signale) — reiht sich bei den zwölf zuvor
  gemessenen Filtern ein. `release_stale_rest` ändert kaum etwas. **527 Tests grün.**
  Damit sind alle sechs seit Monaten unentschiedenen Schalter gemessen. Einzelheiten:
  `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „Messung E43.8“. **In `main`.**
- **E43.7 fertig und in `main` (26.09.2026, reine Unterlagen):** E37-Satz,
  `be_im_plus`-Urteil (Lesefehler: nicht Furkans Regel) und Funding-„Faktor 69“
  (= Einheit) berichtigt; Abschnitt „nie entschieden“ in `GEMESSEN-UND-ENTSCHIEDEN.md`
  mit allen sechs Messungen geschlossen. E43.7 war schon einmal auf dem Zweig
  `claude/e43-6-gitterzeilen-eo6mzb` erledigt, aber nie nach `main` gekommen (zwei Chats
  parallel, siehe `04_konventionen\BEKANNTE-PROBLEME.md`). **Damit ist E43 abgeschlossen.**

## Was als Nächstes offen liegt (Reihenfolge = Nutzwert)

**NEU: E44 — Kombinationen** (`docs\PLAN-E44-KOMBINATIONEN.md`, 26.09.2026, Analyse,
nichts gebaut). Befund: Filter-Kombinationen schaden gemessen mehr als die Summe, Gewinne
kommen nur aus Ergänzungen. Die Rendite geht in den Rallys verloren, nicht beim Einstieg
und nicht bei den Stops. Vorschlag: E42 (Ausbruch mit Rücktest) als Partner von
`high_exit`, gemessen in einem 2³-Gitter mit einer vorab benannten Hauptzeile. **Wartet
auf Kaisers Antworten** (Abschnitt 10 im Plan). **E44.1 (Coinalyze-Archiv) und E44.2
(Wechselwirkungen, Monats-Probe) sind seit 26.09.2026 in `main`** (Kaisers Go), 545 Tests
grün. cron-job.org-Aufträge für Archiv und Flush-Wache: Anleitung Schritt 5, Kaiser richtet
ein. Kaiser will Shorts im fallenden Markt (E44.6). **E44.3 (E42) ist gebaut** (Zweig
`claude/e44-3-ausbruch-ruecktest-k7m2qx`, 585 Tests, wartet auf Go). **Nächster Schritt: E44.4**
(`verkauf_faktor`), danach E44.5 (Gitter messen). Startprompt je Etappe: Plan, Abschnitt 9a.

0. **E43 — Korrekturen aus der Gesamtprüfung** (`docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`).
   E43.1 und E43.2 live seit 26.09.2026. E43.5 und E43.3 gebaut, gemessen und seit
   26.09.2026 in `main` (E43.3 bleibt `"alt"`). **Als Nächstes
   E43.4** (Open Interest in Kontrakten statt Dollar, Befund A3): **gebaut, gemessen,
   seit 26.09.2026 in `main`** (Kaisers Go). 210 von 1.504 Kerzen anders erkannt,
   Rendite identisch, Regel nicht erfüllt, `muster_oi` bleibt `"usd"`. A3 ist echt: Die
   Hälfte der Pump-Treffer beim OI kam nur vom Kurs. **E43.4b** (Kaisers Antwort auf
   die Anzeige-Frage): Die OI-Zeile im Lage-Abruf zeigt die Kontrakte neben den Dollar,
   Pfeil und Hinweis folgen den Kontrakten. **Live seit 26.09.2026** (Kaisers Go,
   reine Anzeige). **E43.6 und E43.8 gemessen** 26.09.2026 (`rest_halten`,
   `strict_confirm`, `confirm_t1`, `cooldown_h`, `be_im_plus`, `release_stale_rest` —
   alle sechs Regeln nicht erfüllt, alle bleiben aus; Muster-5-Wiederholung weiterhin
   zurückgestellt, da `muster_cvd`/`muster_oi` beide auf dem alten Wert blieben).
   **E43.7 fertig** (siehe oben). A5 ist gemessen und entschieden. **E43 ist damit
   abgeschlossen.** Rest: `_hinweis_be_im_plus` in `config.json` mit der nächsten
   Code-Änderung berichtigen.
1. **E41.6** — ein pfadunabhängiges Risikomaß je Position (Bauplan-Abschnitt in
   `docs\PLAN-E41-STOP.md`, nicht gebaut). Seit 26.09.2026 weniger dringend: Die
   Ausschalt-Regel schlägt auf der neuen Live-Basis nicht mehr an.
2. **E42** — Kaisers zweite Regel: Ausbruch über das letzte Hoch mit Rücktest. **Als E44.3
   gebaut (27.09.2026, Zweig, Schalter aus)**, gemessen wird in E44.5.
3. Alles weitere: `02_status/OFFENE-PUNKTE.md`, nach Nutzwert sortiert.

## Die drei Sätze, die man nie vergessen darf

1. **Zwölf gemessene Filter, zwölf schlechter.** Was gewirkt hat, hielt die Engine
   länger und größer investiert, nie das, was sie zurückhielt.
2. **Ein Renditeunterschied unter 1 Punkt ist Rauschen** — er kippt an einem einzigen
   Tag mehr Daten (gemessen 06.09.2026).
3. **Die Engine ist bei jedem Lauf ein neuer Prozess.** Alles, was über eine Kerze
   hinaus gilt, muss in `state.json` — sonst tut der Backtest etwas, das live nie
   passiert.


## 07.10.2026: isolierte lokale UM2-Engineintegration (keine Aktivierung)

Nur Branch `codex/um2-engine-integration` ab P3 `a7cf45d` ist korrigiert.
Native Liquidations-/M5-Gates: 20/20 eingefrorene Vollfensterläufe exakt zu den
gespeicherten Tapes. Danach 20 gleiche Läufe mit Ablehnung eines Kaufs ohne
darstellbaren BTC-Zuwachs; insgesamt 40 historische Strategieläufe. N-UM2-01
verbraucht dort keine Nachkaufstufe mehr. C05/S006/V000 unverändert, C02 S0/S2/S3
je ein Kleinstfill weniger; Signalfolgen identisch, größte Endwertabweichung
3,64e-12 USD. Isoliert 90/125 alte diagnostische Kleinstoperationen abgelehnt;
35 bleiben darstellbar. Keine allgemeine Mindestorder oder neue Gesamtrangfolge.

C05 und S006 liegen vollständig und inaktiv unter
`docs/um2-engine-integration/candidates/`. Lokale Tests: 834/0 Testfunktionen,
34 neue einzelne Gegenfälle mit gefangener Sabotage. Details und Grenzen:
`docs/um2-engine-integration/ERGEBNIS.md`; additive Nachweise im übergeordneten
Projekt `audit-backups/um2-engine-integration-20261007/`. Wissenspräfix- und
Diagnostiktests wurden nach den historischen Läufen verstärkt; Strategie-/
Ausführungsdateien blieben dabei identisch. Es erfolgte keine weitere Historienrechnung.

Hauptchat-Abnahme, sichere aktuelle Workflowprüfung/separat autorisierter Push
und Online-CI, echte Fills, P3/D3 und P4 bleiben offen. Keine Umstellung von
Site, Runtime, Store oder bestehenden Positionen. Hauptplan nicht endgültig
abgenommen. Vier Aprillücken, unbekannter Warmup, modellierte Verfügbarkeit,
mindestens 94 frühere Suchen und fehlende Zukunftsprobe bleiben Grenzen.
