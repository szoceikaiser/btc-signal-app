# Laufende Übergabe

> Was zuletzt passiert ist, was offen liegt, was eine neue Session als Erstes wissen
> muss. **Jüngster Abschnitt oben.** Nach jeder abgeschlossenen Arbeit einen datierten
> Abschnitt hier ergänzen — nicht erst am Ende eines Vorhabens.
>
> Kurzfassung: `00_STAND.md`. Fertiger Prompt für einen neuen Chat: `STARTPROMPT.md`.

---

## 26.09.2026 (3) — Umzug: Unterlagen ins Code-Repo, KI committet selbst

**Kaisers Wunsch:** *„Kannst du nicht alles so umbauen, dass du auf github commitest?“* —
und auf die Frage nach dem privaten Repo: *„das ist nur ein backup und nicht aktuell.
nehme https://github.com/szoceikaiser/btc-signal-app“*.

**Gemacht:** `docs\`, `wissens-layer\`, `STARTPROMPT.md` und `PRUEFPROMPT.md` aus dem
Backup (Stand 26.09.2026, 8:44, plus die Gesamtprüfung) ins Repo `btc-signal-app`
übernommen. Startprompt, Prüfprompt, Arbeitsregeln (Abschnitt Git), Bekannte Probleme,
Start-hier und die wichtigsten Pfade angepasst. Neue Regel: KI pusht auf einen
Arbeitszweig, `main` nur nach Kaisers „Go“.

**Bewusst NICHT übernommen** (öffentliches Repo): `Transkript.md`, `Videos\`,
`Kauftrigger.md`/`Verkaufstrigger.md` (die Daten stehen ohnehin in `backtest.py`),
`heatmap-test\`, `Claude outputs\`, `signal-app-lokal\`, die Windows-Skripte. Die
Transkripte liegen weiter auf Kaisers Rechner und im privaten Backup.

**Am Code nichts geändert.** 444 Tests grün.

---

## 26.09.2026 (2) — Gesamtprüfung aller Messungen gegen Furkans Videos

**Auftrag Kaiser:** alle Tests nochmals eingehend prüfen, ob die vorherige KI das Ganze
richtig verstanden und gebaut hat; Grundlage Transkript und Videos.

**Ergebnis:** `docs\PRUEFUNG-2026-09-26-GESAMT.md`. Kurz:

- Grundgerüst richtig (Fib-Levels, Dreipunkt-Extension, Tranchen, dynamische Zonen, keine
  Zukunftskenntnis im Backtest). Standbild 02.08. bestätigt die zwei Fib-Raster.
- **A1** Lage-Abruf: Futures-CVD kommt in BTC, steht als $ da (Faktor Kurs zu klein).
- **A2** `classify_pattern`: `spot <= fut / 3` vergleicht Anteile an einer willkürlich
  begonnenen Summe. Gleiche Lage ergibt je nach Startwert GESUNDER_TREND oder
  DERIVATE_PUMP; live wird anders summiert als im Backtest. Muster 2 wirkt live (Kaufsperre,
  5 von 10 Restverkäufen, 30 Warnungen im Lauf vom 23.09.).
- **A3** OI in $ = Kontrakte × Kurs: bei −5 % Kurs ohne eine geschlossene Position erkennt
  die Engine Kapitulation, bei +3,5 % ohne neuen Kontrakt Derivate-Pump.
- **A4** `test_mehr_historie_aendert_die_signale_nicht` erreicht den Muster-2-Zweig nie.
- **Lesefehler:** `be_im_plus` ist nicht Furkans Regel (Vorbedingung „Gewinne schon
  realisiert“ fehlt); Furkans Regel entspricht `trail_stop`.
- **Messbasis:** 16 von 25 ausgeschalteten Schaltern/Datenvarianten nie mit genau einem
  Unterschied gegen die heutige Live-Zeile gemessen. Vorneweg `bein_richtung: bias`.

**Am Code wurde nichts geändert.** 444 Tests grün. Nachstell-Skripte stehen im Anhang des
Berichts. Börsendaten waren aus der Arbeitsumgebung gesperrt: bewiesen ist der
Mechanismus, nicht die Häufigkeit im echten Fenster.

**Nächster Schritt, offen:** Kaiser entscheidet über Teil E des Berichts (Reihenfolge nach
Nutzwert, Entscheidungsregel vorab festgelegt).

---

## 26.09.2026 — Wissens-Layer aufgefrischt, Übergabe vorbereitet

**Fertig:** Alle Dateien des Wissens-Layers auf den Stand nach E41 gebracht. Neu
hinzugekommen:

- `00_STAND.md` — Kurzstand, wird künftig nach jeder Arbeit fortgeschrieben.
- `04_konventionen/BEKANNTE-PROBLEME.md` — Umgebungs- und Werkzeugfallen, getrennt von
  den inhaltlichen Befunden.
- diese Datei (`02_status/UEBERGABE.md`).
- `STARTPROMPT.md` und `PRUEFPROMPT.md` in der Repo-Wurzel.

Der Übergabeprompt stand vorher **doppelt** (in `ETAPPENPLAN.md` und in
`START-HIER.md`) und war in beiden Fassungen veraltet (174 Tests, letzte Etappe E30).
Maßgeblich ist jetzt allein `STARTPROMPT.md`; `START-HIER.md` verweist nur dorthin.

**Am Code wurde nichts geändert.** 444 Tests grün.

**Nächster Schritt, offen:** E41.6 oder E42 (siehe unten) — Kaisers Entscheidung.

---

## 23.09.2026 — Ausschalt-Regel für E41 hat angeschlagen, Kaiser hat überstimmt

**Messung** (Backtest 23.09.2026, 18:40 UTC, Fenster 15.01.–23.09.2026):

| Variante | Rendite | Rückgang | H1 | H2 | Stops |
|---|---:|---:|---:|---:|---:|
| Live: Rückeroberung 1 Kerze | +25,2 % | **−10,9 %** | +20,0 % | +4,3 % | 9 |
| Alter Stop (bis 21.09.) | +22,6 % | −9,4 % | +17,8 % | +4,1 % | 10 |
| B3 · 3 statt 1 Kerze | +26,8 % | −10,4 % | +21,4 % | +4,5 % | 9 |

Bedingung 2 der vorab festgelegten Ausschalt-Regel ist verletzt (Rückgang 1,5 statt
höchstens 1,0 Punkte tiefer). Der Bericht meldet **AUSSCHALTEN**.

**Kaisers Entscheidung:** anlassen, beim nächsten Backtest neu prüfen. Begründung,
Gegenargumente und die Kosten stehen in `docs\PLAN-E41-STOP.md`, Abschnitt „Nachmessung
23.09.2026". Im Bericht steht die Überstimmung jetzt **neben** der Ausschalt-Meldung —
die Regel wurde nicht abgeschwächt (zwei Sabotagen sichern das ab).

**Kaisers Frage „warum nicht B3 mit 3 Kerzen?" ist beantwortet** (fünf Gründe im Plan);
der stärkste: B3 hat **gleich viele Stops** wie B1 (9 gegen 9, alter Stop 10) — es ist
derselbe eine ausgelassene Stop, der Unterschied entsteht nur aus späteren Stop-Preisen.
Für einen späteren Wechsel liegt eine **vorab festgelegte Regel** im Plan (zwei Läufe,
vier Wochen Abstand, in beiden Hälften ≥ 1 Punkt besser, Rückgang nicht tiefer).

**Neue Projektlehre:** Der Fenster-Rückgang ist **zwischen zwei Varianten**
pfadabhängig — B3 wartet länger und zeigt trotzdem einen flacheren Rückgang. Daraus der
Vorschlag **E41.6**: ein Risikomaß je Position (tiefster Punkt zwischen dem alten Stop
und dem Live-Ausstieg), Schwelle vorab festgelegt. Nicht gebaut.

**Stand Code:** 444 Tests, `sabotage_e41.py` 58 Sabotagen, alle gefangen.

---

## 21.09.2026 — E41 live, STH-Kostenbasis als Anzeige

**Live geschaltet** (Kaisers Entscheidung): `stop_rueckeroberung: 1`. Der erste
4h-Schluss unter der Invalidierung stoppt nicht mehr; die Engine wartet eine Kerze auf
die Rückeroberung. Danach gilt die Marke als **geprüft** — der nächste Schluss darunter
stoppt sofort. Notbremse: mehr als 5 % unter der Marke stoppt ohne Warten. Während des
Wartens und in der Kerze der Rückeroberung wird nicht nachgekauft.

**Telegram** meldet „⏳ STOP WARTET" und „✅ MARKE ZURÜCKEROBERT"; die Plan-Nachricht
nennt die Regel in der Stop-Zeile und warnt, wenn die Engine gerade wartet.

**Drei Dinge, die erst beim Bauen auffielen** (alle behoben, im Plan dokumentiert):
die Merker mussten in `state.json` (sonst käme der Stop live nie), der 0,786-Nachkauf
hätte nach einer Rückeroberung zu einem nie existierenden Preis gebucht, und die
Nachkaufsperre muss auch die Kerze der Rückeroberung umfassen.

**Ebenfalls fertig:** die **STH-Kostenbasis** steht als Zeile im Lage-Abruf (Wert,
Abstand in Prozent, Datum, „Nur Anzeige, keine Regel"). Quelle bitview.space, Ersatz
bitcoin-data.com. Als *Regel* ist sie nicht prüfbar: 84 % der Kerzen lagen darunter, nur
7 Wechsel im Fenster — E40.2/E40.3 wurden deshalb nicht gebaut.

**Ebenfalls fertig:** E38 (Muster 5) ist entschieden — das Signal ist echt, die Engine
kann es nicht benutzen, weil sie nur an Fib-Zonen entscheidet. Alle Schalter aus, nur
der Text in den Nachrichten wurde ersetzt und die Ampel zählt Muster 5 neutral.

**Gitter umgebaut:** Panel-Zeile ist jetzt „LIVE-heute +Rückeroberung vor dem Stop
(1 Kerze)". Neu: „LIVE bis 21.09.2026 (Stop ohne Rückeroberung)" als Ausschalt-Probe und
„Rückeroberung 3 statt 1 Kerze" als Robustheitsprüfung. A (Puffer 0,5 %) und C (Docht)
sind nach der Messung aus dem Gitter genommen.

---

## Was als Nächstes offen liegt

Vollständig und nach Nutzwert sortiert: `02_status/OFFENE-PUNKTE.md`. Die beiden
naheliegenden Vorhaben:

1. **E41.6 — pfadunabhängiges Risikomaß.** Für jeden Stop des alten Stops den tiefsten
   Punkt messen, den die Position live danach noch sah. Damit ließe sich die
   Ausschalt-Bedingung als „zusätzlicher Buchverlust je Position" fassen statt als
   Fenster-Rückgang. Schwelle **vor** der Messung festlegen. Grundlage:
   `docs\PLAN-E41-STOP.md`, Abschnitt E41.6.
2. **E42 — Ausbruch mit Rücktest** (Kaisers zweite Regel, wörtlich im Plan E41
   zitiert): Die Engine verkauft heute kurz unter dem letzten Hoch (`high_exit: on`).
   Bricht der Kurs durch und hält beim Rücktest (Schluss nicht mehr darunter, höchstens
   der Docht), sind weitere Gewinne zu erwarten — zurückkaufen oder den Rest halten?
   Eigene Etappe, weil es in E41 einen zweiten Unterschied pro Gitterzeile erzeugt
   hätte. Noch kein Bauplan.

**Vier Schalter hängen seit Monaten unentschieden** (`confirm_t1`, `cooldown_h`,
`be_im_plus`, `release_stale_rest`) — sie wurden nie mit **genau einem** Unterschied
gegen die heutige Basis gemessen. Zwei saubere Gitterzeilen würden das klären.
