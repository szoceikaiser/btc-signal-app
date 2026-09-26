# Bauplan E23 — die 1D-Ebene als zweiter Zonensatz

**Auftrag Kaiser, 28.08.2026:** *„ok, baue den schalter."*
Vorgeschichte: `docs/PRUEFUNG-1D-EBENE.md` (Vorab-Rechnung), `docs/FURKAN-UPDATE-2026-08-02.md`
Abschnitt 5 Vorschlag 1b, `docs/STRATEGIE.md` §4.1 Punkt 4.

## Ziel aus Nutzersicht

Die Engine überwacht heute EINE Ebene (4h) und wählt dort EIN Bein. Furkan führt zwei Raster
gleichzeitig. Ende Juli 2026 kostete uns das einen ganzen Monat: die 4h-Ebene sah nur Zappler
unter 5 % (überwiegend SHORT, bei `bias_short=false` nicht handelbar), während die 1D-Ebene
das Bein 57.800 → 66.956 gezeichnet hätte — dasselbe, das Furkan im Chart hatte.

Nach dem Bau soll die Engine bei aktivem Schalter zusätzlich die 1D-Zone prüfen, wenn die
4h-Ebene keinen Einstieg hergibt.

## Soll-Zustand

**Neuer Schalter `zonen_1d`** (bool, Default `False`, wie jeder ungemessene Mechanismus).

**Ablauf in `evaluate()`, wenn `zonen_1d=True`:**

1. Der 4h-Einstiegsversuch läuft unverändert zuerst.
2. Bleibt die Position danach FLAT, wird derselbe Einstiegsblock ein zweites Mal mit dem
   **1D-Impuls** durchlaufen.
3. Ist das 1D-Bein identisch mit dem 4h-Bein (gleiche Start-/Endpreise), entfällt der zweite
   Durchlauf — kein doppelter Aufwand, keine Doppelsignale.
4. Alle bestehenden Bedingungen gelten unverändert: Order-Flow-Bestätigung, `min_stop_pct`,
   `cooldown_h`, `block_unhealthy`, `trend_filter`, `liq_entry`, `flush_entry`.
5. Die Position übernimmt die 1D-Zonen — Stop, Ziele und Kaufleiter richten sich danach.

**Signal-Kennzeichnung:** Der Grund-Text bekommt den Zusatz `[1D]`, damit im Bericht und in
Telegram sichtbar ist, welche Ebene den Einstieg gestellt hat.

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `engine/strategy_core.py` | Parameter `zonen_1d`; `_versuche_einstieg(imp_arg=None)`; zweiter Durchlauf nach dem FLAT-Block und im E21-Neustart-Block |
| `engine/main.py` | `zonen_1d` in `EVAL_DEFAULTS` |
| `site/data/config.json` | `zonen_1d: false` + `_hinweis_zonen_1d` |
| `engine/backtest.py` | Parameter durchreichen, zwei Varianten im Grid |
| `engine/test_strategy_core.py` | Kern-Test + zwei Gegenproben |
| `engine/test_main.py` | Durchreich-Test (läuft über die bestehende Tabelle) |

## Parameterwahl

`daily_fib_zone()` bekommt `pivot_n` und `k_atr` **aus den Live-Werten** durchgereicht
(n=5, k_atr=2.0), dazu `min_bein_pct` und `bein_wahl` wie bisher. Der bestehende
`confluence`-Aufruf bleibt **unverändert** (k_atr=3.0, Default) — sonst würde sich das
Verhalten eines bereits gemessenen Schalters ändern.

**Geprüft vor dem Bau:** Live lädt `main.py` 400 4h-Kerzen = 66 Tage. Nachgerechnet über
394 Tage: das 1D-Bein aus 66 Tagen Historie ist in **100 %** der Fälle identisch mit dem aus
der vollen Historie. Das Fenster reicht, kein Nachladen nötig.

## Was bewusst NICHT gemacht wird

- **Keine 1D-Ebene für das Positions-Management.** Läuft eine Position, bleiben ihre
  eingefrorenen Zonen maßgeblich — egal welche Ebene sie gestellt hat. Sonst müssten Stop
  und Ziele mitten im Trade wechseln.
- **1D bekommt keinen Vorrang vor 4h.** 4h zuerst, 1D nur als Ergänzung. So ist bei
  `zonen_1d=false` das Verhalten bitgleich zu heute und der Schalter sauber messbar.
- **Kein eigener `min_bein_pct` für 1D.** Ein Parameter weniger im Spiel; falls der Backtest
  zeigt, dass 1D eine andere Mindest-Beinlänge braucht, ist das eine eigene Etappe.
- **Keine Konfluenz-Bevorzugung** („4h+1D = stärkste Zone", §4.1 Punkt 4 zweiter Halbsatz).
  Das wäre eine größere Tranche bei Überlappung — erst messen, ob die Ebene überhaupt trägt.

## Erwartung (damit sie hinterher überprüfbar ist)

Die Vorab-Rechnung fiel durch die Robustheitsprüfung: erste Fensterhälfte −18,1 %, zweite
+44,5 %. **Ich erwarte, dass der Schalter aus bleibt.** Er wird gebaut, damit die Frage
beantwortet ist statt offen — nicht weil ich mit einem Gewinn rechne.

## Etappen

- **E23.1** Kern in `strategy_core.py` + Tests · Status: FERTIG (28.08.2026)
- **E23.2** Schalter durchreichen (`main.py`, `config.json`) · Status: FERTIG (28.08.2026)
- **E23.3** Backtest-Varianten · Status: FERTIG (28.08.2026)
