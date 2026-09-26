# 00 STAND — Kurzstand in einer halben Minute

> **Diese Datei wird zuerst gelesen, auch von jeder KI.** Sie ist bewusst kurz und wird
> nach jeder abgeschlossenen Arbeit fortgeschrieben (Datum, was fertig, was als
> Nächstes). Ausführlich: `START-HIER.md`, dann `02_status/UEBERGABE.md`.
>
> Stand: **26.09.2026**

## Lage

- **Seit 26.09.2026 liegen Code UND Unterlagen im Repo `btc-signal-app`** (öffentlich).
  Die KI committet selbst auf einen Arbeitszweig; in `main` (live) erst nach Kaisers
  „Go“. Das private Repo `260729-btc-trading-backup` ist nur noch ein Backup. Alte Pfade
  `signal-app\...` meinen jetzt die Repo-Wurzel. Einzelheiten: `START-HIER.md`.
- Die Engine **läuft live** und handelt nicht selbst: sie sendet Telegram-Signale,
  Kaiser platziert die Orders. Webseite: `szoceikaiser.github.io/btc-signal-app`.
- **Tests:** in `main` **444**, auf dem Arbeitszweig mit E43.1/E43.2 **447**, alle grün
  (`cd engine && python3 run_tests.py`). Sabotage-Proben: in `main` fünf (151
  Sabotagen), auf dem Zweig zusätzlich `sabotage_e43.py` (7), alle gefangen.
- Letzte Live-Änderung am Handelsverhalten: **E41, Kaisers Rückeroberungs-Regel**
  (`stop_rueckeroberung: 1`), live seit 21.09.2026.
- **Offener Streitpunkt dazu:** Die vorab festgelegte Ausschalt-Regel für E41 hat am
  23.09.2026 angeschlagen (Rückgang 1,5 Punkte tiefer als erlaubt 1,0). Kaiser hat sie
  **bewusst überstimmt**; der Bericht meldet weiter „AUSSCHALTEN". Beim nächsten
  Backtest neu ansehen. Begründung: `docs\PLAN-E41-STOP.md`, Abschnitt „Nachmessung
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

## Was als Nächstes offen liegt (Reihenfolge = Nutzwert)

0. **E43 — Korrekturen aus der Gesamtprüfung** (`docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`).
   E43.1 (Futures-CVD in $) und E43.2 (Gitterzeile „Bein in Handelsrichtung“) sind auf
   dem Arbeitszweig gebaut, der Backtest dort läuft. Live erst nach Kaisers „Go“.
   Danach E43.3/E43.4 (Muster 2 und OI als Schalter).
1. **E41.6** — ein pfadunabhängiges Risikomaß je Position, damit die Ausschalt-Regel auf
   belastbarem Grund steht (Bauplan-Abschnitt in `docs\PLAN-E41-STOP.md`, nicht gebaut).
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
