# 00 STAND — Kurzstand in einer halben Minute

> **Diese Datei wird zuerst gelesen, auch von jeder KI.** Sie ist bewusst kurz und wird
> nach jeder abgeschlossenen Arbeit fortgeschrieben (Datum, was fertig, was als
> Nächstes). Ausführlich: `START-HIER.md`, dann `02_status/UEBERGABE.md`.
>
> Stand: **26.09.2026 (4)**

## Lage

- **Seit 26.09.2026 liegen Code UND Unterlagen im Repo `btc-signal-app`** (öffentlich).
  Die KI committet selbst auf einen Arbeitszweig; in `main` (live) erst nach Kaisers
  „Go“. Das private Repo `260729-btc-trading-backup` ist nur noch ein Backup. Alte Pfade
  `signal-app\...` meinen jetzt die Repo-Wurzel. Einzelheiten: `START-HIER.md`.
- Die Engine **läuft live** und handelt nicht selbst: sie sendet Telegram-Signale,
  Kaiser platziert die Orders. Webseite: `szoceikaiser.github.io/btc-signal-app`.
- **Tests:** in `main` **467**, alle grün (`cd engine && python3 run_tests.py`).
  Sabotage-Proben: fünf ältere (151 Sabotagen) plus `sabotage_e43.py` (7), alle gefangen.
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
  meldet „Bleibt an“ (`docs\PLAN-E41-STOP.md`, „Nachmessung 26.09.2026“). Neuer, ungemessener Nebenbefund **A5**: „Teilgewinn am letzten Hoch“
  hängt von der Länge der geladenen Historie ab (`OFFENE-PUNKTE.md`, Punkt 8).

## Was als Nächstes offen liegt (Reihenfolge = Nutzwert)

0. **E43 — Korrekturen aus der Gesamtprüfung** (`docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`).
   E43.1 und E43.2 live seit 26.09.2026. E43.5 und E43.3 gebaut, gemessen und seit
   26.09.2026 in `main` (E43.3 bleibt `"alt"`). **Als Nächstes
   E43.4** (Open Interest in Kontrakten statt Dollar, Befund A3): zuerst den
   Bauplan-Abschnitt schreiben. Danach E43.6 (Nachmessungen), E43.7 (Texte), A5
   (`OFFENE-PUNKTE.md`, Punkt 8: erst messen).
1. **E41.6** — ein pfadunabhängiges Risikomaß je Position (Bauplan-Abschnitt in
   `docs\PLAN-E41-STOP.md`, nicht gebaut). Seit 26.09.2026 weniger dringend: Die
   Ausschalt-Regel schlägt auf der neuen Live-Basis nicht mehr an.
2. **E42** — Kaisers zweite Regel: Ausbruch über das letzte Hoch mit Rücktest
   (zurückkaufen oder Rest halten). Vorgemerkt in `02_status/OFFENE-PUNKTE.md`.
3. Alles weitere: `02_status/OFFENE-PUNKTE.md`, nach Nutzwert sortiert.

## Die drei Sätze, die man nie vergessen darf

1. **Zwölf gemessene Filter, zwölf schlechter.** Was gewirkt hat, hielt die Engine
   länger und größer investiert, nie das, was sie zurückhielt.
2. **Ein Renditeunterschied unter 1 Punkt ist Rauschen** — er kippt an einem einzigen
   Tag mehr Daten (gemessen 06.09.2026).
3. **Die Engine ist bei jedem Lauf ein neuer Prozess.** Alles, was über eine Kerze
   hinaus gilt, muss in `state.json` — sonst tut der Backtest etwas, das live nie
   passiert.
