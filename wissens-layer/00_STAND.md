# 00 STAND — Kurzstand in einer halben Minute

## Aktueller Arbeitsstand 28.09.2026: Audit-Nacharbeit, Etappe 2

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
