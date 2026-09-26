# Maßgebliche Quellen

> Bei Widerspruch gewinnt immer das Original, nie eine Zusammenfassung — auch nicht
> die in diesem Wissens-Layer. Stand: 26.09.2026.

## Wer ist wofür die Wahrheit

| Thema | Maßgebliche Datei | Anmerkung |
|---|---|---|
| Kurzstand des Projekts | `wissens-layer\00_STAND.md` | Wird nach jeder Arbeit fortgeschrieben |
| Furkans Strategie | `docs\STRATEGIE.md` | Aus dem Video abgeleitet, mit geprüften Frame-Zeitmarken |
| Furkans Worte selbst | `Transkript.md`, `Videos\` | Rohabschriften mit Zeitmarken. Die letzte Instanz, wenn eine Auslegung strittig ist |
| Kaisers notierte Handelstermine | `Kauftrigger.md`, `Verkaufstrigger.md` | Rohdaten, nicht rekonstruierbar. Grundlage für Recall und Präzision |
| Chronik: was wann warum entschieden wurde | `docs\ETAPPENPLAN.md` | 128 KB. Nachschlagen, nicht am Stück lesen |
| Landkarte aller Messungen und Entscheidungen | `wissens-layer\02_status\GEMESSEN-UND-ENTSCHIEDEN.md` | Die Datei, die verhindert, dass Durchgefallenes erneut vorgeschlagen wird |
| Was jeder Schalter tut und **warum** er an oder aus ist | `site\data\config.json`, Felder `_hinweis_*` | Steht direkt beim Schalter, wo man ihn umlegt. 35 Schalter |
| Backtest-Zahlen | `BACKTEST.md` | **Wird bei jedem Lauf neu erzeugt — nie von Hand ändern.** Die Lesehilfen darin stehen im Quelltext von `backtest.py` |
| Technische Grundsatzentscheidungen und Datenquellen | `docs\ARCHITEKTUR.md` | |
| Wie gut die Strategie Kaisers Trigger erklärt | `docs\GEGENCHECK.md` | |
| Warum frühere Positionen verloren haben | `docs\VERLUST-ANALYSE-2026-07-27.md` | |
| Der tatsächliche Zustand der laufenden Position | `site\data\state.json` | Wird von der Engine geschrieben. Zum Lesen, nicht zum Bearbeiten |
| Übergabe an eine neue Session / andere KI | `STARTPROMPT.md` (Repo-Wurzel) | Einziger maßgeblicher Ort. Wird bei jeder größeren Änderung mitgezogen |
| Reiner Prüfdurchlauf (nichts ändern) | `PRUEFPROMPT.md` (Repo-Wurzel) | |
| Was zuletzt passiert ist, was halb fertig liegt | `wissens-layer\02_status\UEBERGABE.md` | Jüngster Abschnitt oben |

## Baupläne einzelner Etappen

`docs\PLAN-E*.md` — je Vorhaben ein Dokument mit Problemstellung (mit Kaisers
wörtlichem Einwand), Soll-Zustand, betroffenen Dateien, Etappen, Messergebnis und einem
Abschnitt „Bewusst NICHT gemacht". Vorhanden für **E18, E23, E24, E28, E30, E32, E33,
E34, E35, E36, E37, E38, E39/E40, E41, E43 und E44**.

Besonders ergiebig für eine neue Session:

| Datei | Warum sie sich lohnt |
|---|---|
| `docs\PLAN-E41-STOP.md` | Die aktuelle Live-Änderung (Rückeroberungs-Regel), die vorab festgelegte Ausschalt-Regel, deren Anschlagen am 23.09.2026, Kaisers Überstimmung — und der Vorschlag E41.6 |
| `docs\PLAN-E39-E40.md` | Was nach einem Stop passiert; die STH-Kostenbasis samt Quellenvergleich und der Entscheidung „Anzeige, keine Regel" |
| `docs\PLAN-E38-MUSTER5.md` | Muster 5 als Treibstoff: echtes Signal, das die Engine nicht benutzen kann — samt Episoden-Gegenprobe |
| `docs\PLAN-E37-AGGREGATION.md` | Warum die Engine eine Börse misst und nicht den Markt, und warum Aggregation trotzdem durchfiel |
| `docs\PLAN-E33-UEBERGEORDNETER-TREND.md`, `docs\PLAN-E34-AMPEL.md` | Die beiden Filter-Messungen, aus denen „Anzeige statt Regel" entstand |

`docs\PLAN-E28-BREAKEVEN-NACH-AUFSTOCKUNG.md` ist ausdrücklich als **Vorlage, nicht
umgesetzt** gekennzeichnet — der Mechanismus wurde auf Kaisers Wunsch zurückgenommen.

## Video-Auswertungen

| Datei | Inhalt |
|---|---|
| `docs\FURKAN-UPDATE-2026-07.md`, `…-07-B.md` | Auswertungen der Juli-Videos |
| `docs\FURKAN-UPDATE-2026-08-02.md`, `…-08-03.md` | August-Videos. Quelle für E19/E20 (Bein-Wahl, Widerstandszone) |
| `Videos\260913\` (weitere: 060727, 260802, 260803, 260910) | Video vom 13.09.2026 — Grundlage von E38 bis E41 (Muster 5, Stop-Verhalten, STH-Kostenbasis, offene Liquidationscluster) |

Das Makro-Video vom 02.08.2026 ist **noch nicht vollständig ausgewertet** — siehe
`02_status\OFFENE-PUNKTE.md`.

## Externe Datenquellen

| Quelle | Wofür | Grenzen |
|---|---|---|
| `data-api.binance.vision` | Kerzen, Spot-CVD | Public-Data-Spiegel; die Futures-API sperrt GitHub-Runner (451) |
| Coinalyze | Open Interest, Liquidationen, Futures-CVD, Long-Short | Schlüssel als GitHub-Secret, 40 Abrufe/Minute; `buy-sell-volume-history` existiert nicht |
| Kraken Futures | Funding | |
| `bitview.space` | STH-Kostenbasis (Hauptquelle) | Werteliste **ohne** Datum, Index 0 = 01.01.2009; exakter Serienname nötig |
| `bitcoin-data.com` | STH-Kostenbasis (Ersatz) | Zahlen als Text, 15 Abrufe/Tag je IP, 7 Tage Verzug |

## Zwei Doppelungen, die man kennen muss

**1. `ANLEITUNG-EINSTELLUNGEN.md` gegen `config.json`.** Die Anleitung erklärt einen Teil
der Schalter ein zweites Mal, die neueren fehlen dort ganz. Sie driftet also.
**Beschlossen: `config.json` ist maßgeblich** für das Warum; die Anleitung soll auf das
Wie reduziert werden. Noch nicht umgesetzt.

**2. Der Übergabeprompt.** Im `ETAPPENPLAN.md` steht noch der alte vom 23.07.2026, in
`START-HIER.md` stand bis 26.09.2026 ein zweiter. **Maßgeblich ist jetzt allein
`STARTPROMPT.md`** in der Repo-Wurzel; `START-HIER.md` verweist nur noch dorthin. Die
alten Fassungen bleiben als Zeitdokument stehen.

## Was NICHT maßgeblich ist

- Dieser Wissens-Layer. Er fasst zusammen und verweist. Bei Widerspruch gewinnt das
  Original.
- Der Ordner `signal-app-lokal\` — Stand vom 22.07.2026, historisch.
- Der Abschnitt „Frühere Fassung (überholt)" in `docs\ARCHITEKTUR.md` — ausdrücklich
  nur zur Einordnung.
- Zahlen in älteren Baupläne-Abschnitten: Sie gelten gegen die Basis, gegen die damals
  gemessen wurde. Welche das war, steht im jeweiligen Dokument.
