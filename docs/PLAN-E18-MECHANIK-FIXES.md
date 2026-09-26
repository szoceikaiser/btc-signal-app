# Bauplan E18: Drei Mechanik-Fehler beheben (Durchsicht 27.08.2026)

Stand: 2026-08-27 · Auslöser: vollständige Code-Durchsicht auf Kaisers Bitte
(„analysiere dieses Projekt, jede Datei, jede Zeile").
Kaisers Freigabe: *„ja, leg los"* — die ersten drei Befunde beheben, schaltbar,
mit Gegenprobe im Test, wie im Projekt üblich.

## Ausgangslage (geprüft, nicht vermutet)

Alle Code-Dateien im lokalen Ordner `signal-app` waren am 27.08.2026 **byte-identisch**
mit dem Live-Repo (md5-Vergleich) — nur die Daten unter `site/data/` sind lokal veraltet.
Deshalb konnte direkt im lokalen Ordner gearbeitet werden. Beim Pushen ist das wichtig:
**erst `git pull`, dann committen**, sonst überschreiben die alten Datenstände den
Live-Zustand.

## Die drei Befunde

### B1 — Sechs Einstellungen kommen live nicht an
`run_engine()` reicht 11 von 20 möglichen Werten an `evaluate()` durch. Nicht dabei:
`flush_entry`, `tp_ladder`, `buy_ladder`, `conditional_stop`, `pivot_n`, `k_atr`,
dazu die drei nie benutzten E8.5-Filter (`trend_filter`, `strict_confirm`, `confluence`).
Live gelten deshalb die Vorgabewerte aus dem Code. Wer einen dieser Werte in
`config.json` ändert, bewirkt **nichts** — und bekommt keine Fehlermeldung.
Besonders heikel: `watch_flush()` und `zonen_vorschau()` lesen dieselben Werte
sehr wohl aus der Datei. Zwei Teile derselben App mit zwei Wahrheiten.

### B2 — Kauf und Verkauf in derselben Kerze
16 von 214 Signalen der Live-Variante fallen auf Kerzen, in denen gleichzeitig
nachgekauft und teilverkauft wird — meist zum selben Preis. Quellen (Mehrfachnennung):
10× Liquidations-Konfluenz-Nachkauf, 9× Mehrtages-Kaufleiter, 5× 0.786-Nachkauf,
1× Golden-Pocket-Aufstockung. Ursache: Der Nachkauf prüft das **Tief** der Kerze,
der Teilgewinn am letzten Hoch das **Hoch** derselben Kerze; beide Blöcke wissen
nichts voneinander. Kosten: doppelte Gebühr auf ein Geschäft, das sich selbst
aufhebt, plus zwei widersprüchliche Telegram-Nachrichten.

### B3 — Die Extension-Ziele wandern nach unten
`pos.retrace_extreme` wird auch nach dem ersten Teilgewinn fortgeschrieben. Fällt der
Kurs danach noch einmal tiefer, ohne dass der Stop auslöst, sinken ext1/ext2 mit.
Nachgestellt: Ziel 1.618 von 301,8 auf 257,8 — unter das ursprüngliche 1.0-Ziel (240).
Auch mit `trail_stop` (live an) bleibt der milde Fall: 301,8 → 286,8 ohne Stop-Signal.
Passt zum Befund, dass `TEILVERKAUF_2` im ganzen Messfenster genau **einmal** vorkommt.

## Soll-Zustand

| Etappe | Änderung | Live-Wirkung sofort? |
|---|---|---|
| E18.1 | Alle `evaluate`-Parameter werden aus `config.json` durchgereicht; ein Test verhindert den Rückfall | **nein** — die neuen Vorgabewerte entsprechen exakt den bisherigen Code-Defaults |
| E18.2 | `no_flip`: in einer Kerze wird nur eine Richtung gehandelt | nein — Default `false` |
| E18.3 | `freeze_targets`: Zielreferenz wird beim ersten Teilgewinn eingefroren | nein — Default `false` |

Grundsatz wie im ganzen Projekt: **schaltbar bauen, Default aus, per Backtest messen,
erst danach live schalten.** E18.1 ist die Ausnahme — dort ändert sich nichts am
Verhalten, es wird nur die Anzeige ehrlich.

### E18.1 im Detail
- `run_engine()` reicht zusätzlich durch: `pivot_n` (5), `k_atr` (2.0), `flush_entry`
  ("core"), `tp_ladder` (true), `buy_ladder` (true), `conditional_stop` (false),
  `trend_filter` (false), `strict_confirm` (false), `confluence` (false), `trend_ema` (50).
  Die Klammerwerte sind die bisherigen Code-Defaults — **darum ändert sich nichts**.
- `config.json` bekommt die neuen Schalter mit Klartext-Hinweis.
- Neuer Test `test_alle_evaluate_parameter_werden_durchgereicht`: vergleicht die
  Signatur von `evaluate` mit den Schlüsseln, die `run_engine` weitergibt. Kommt später
  ein Parameter dazu und wird nicht durchgereicht, wird der Test rot.

### E18.2 im Detail (`no_flip`, Default false)
Regel: **Sobald in einer Kerze ein Teilverkauf erzeugt wurde, wird in derselben Kerze
nicht mehr aufgestockt — und umgekehrt.** Betroffen sind nur Aufbau- und
Teilverkaufs-Signale:
- gesperrt werden können: `NACHKAUF`, `SHORT_NACHLEGEN`, das Upgrade `KAUF_2`/`SHORT_2`,
  `TEILVERKAUF_LADDER`, `TEILVERKAUF_1/2`, `SHORT_TP_*`
- **nie** gesperrt: `STOPLOSS`, `SHORT_STOPLOSS`, `VERKAUF_REST`, `SHORT_COVER_REST`
  (vollständige Ausstiege dürfen nie unterdrückt werden) sowie Ersteinstiege aus FLAT
- Es entscheidet, was zuerst kommt. Ob stattdessen die Verkaufsseite Vorrang haben
  sollte, ist eine eigene Frage — erst messen, dann entscheiden (siehe Offen).

### E18.3 im Detail (`freeze_targets`, Default false)
- Neues Feld `Position.ziel_extrem` (persistiert in `state.json`), gesetzt beim ersten
  realisierten Teilgewinn (Leiter-Stufe oder TP1).
- `ext1`/`ext2` rechnen ab dann mit `ziel_extrem` statt mit dem laufenden
  `retrace_extreme`. Das laufende Extrem bleibt unverändert erhalten, damit die
  Mehrtages-Kaufleiter (`made_new_extreme`) sich nicht ändert.
- `_reset_position` setzt das Feld zurück.

## Bewusst NICHT gemacht

- **Kein Live-Umschalten.** Alle drei Schalter bleiben aus, bis ein Backtest-Lauf sie
  gemessen hat. Das Projekt hat sich diese Regel teuer erarbeitet (E11, E13).
- **Befund 4 (maximaler Rückgang nur an Signalzeitpunkten gemessen) bleibt offen.** Er
  gehört nicht in dasselbe Paket: Er ändert keine Signale, sondern die Bewertung —
  und würde alle bisherigen Rückgangs-Zahlen neu setzen. Eigene Etappe.
- **Kein `.gitattributes`.** Die CRLF-Umstellung würde jede Datei im Repo als geändert
  markieren und diesen Diff unlesbar machen. Getrennt erledigen.

## Offen nach E18

1. Messlauf (Workflow „Backtest") mit den neuen Gitterzeilen; erst danach entscheiden,
   ob `no_flip`/`freeze_targets` live gehen.
2. Falls `no_flip` Rendite kostet: Variante „Verkaufsseite hat Vorrang" bauen und messen.
3. Befund 4: Rückgang zwischen den Signalen mitmessen (`simulate()`).
4. Auswertung des Makro-Videos vom 02.08.2026 (`Videos/260802/`) — passt zum pausierten
   KI-Makro-Bias (E8.5).
