# START HIER

> Einstiegsdatei des Wissens-Layers. Wer neu an diesem Projekt arbeitet — Mensch
> oder KI — liest zuerst `00_STAND.md` (halbe Minute) und dann diese Seite.
> Stand: 26.09.2026.

## Das Projekt in einer Minute

Eine Signal-Engine für Bitcoin, gebaut nach der Order-Flow-Strategie von Furkan
Yildirim. Sie wird sechsmal täglich nach jedem 4-Stunden-Kerzenschluss angestoßen,
liest Kursdaten und Order-Flow-Kennzahlen, zeichnet Fibonacci-Zonen aus der
Swing-Struktur und schickt Kauf-, Nachkauf-, Teilverkaufs- und Stop-Signale per
Telegram. Eine Flush-Wache schaut zusätzlich alle 15 Minuten in die laufende Kerze.
Dazu eine Webseite mit Chart und Backtest-Zahlen.

**Sie handelt nicht selbst.** Sie sendet Signale; die Orders platziert Kaiser von
Hand. Das ist eine bewusste Entscheidung, keine fehlende Funktion.

Betreiber und Auftraggeber: Kaiser. Er ist **nicht IT-affin** — Anleitungen gehören
als fertige Befehlsblöcke geschrieben, ein Schritt nach dem anderen, mit Rückmeldung
dazwischen.

## Wo alles liegt (umgestellt am 26.09.2026)

**Maßgeblich ist das Repo `btc-signal-app` auf GitHub (öffentlich).** Darin liegen seit
26.09.2026 Code **und** Unterlagen: `engine\`, `site\`, `docs\`, dieser Wissens-Layer,
`STARTPROMPT.md`, `PRUEFPROMPT.md`. Auf Kaisers Rechner ist das der Ordner
`BTC-Trading\signal-app\`.

| Ort | Rolle |
|---|---|
| `btc-signal-app` (GitHub, **öffentlich**) | **maßgeblich** — Code, Unterlagen, Backtest-Bericht |
| `BTC-Trading\` auf Kaisers Rechner, gesichert in `260729-btc-trading-backup` (**privat**) | nur noch Backup. Enthält außerdem, was nicht öffentlich gehört: Video-Transkripte, Kaisers Trigger-Notizen, Heatmap-Screenshots. Die Kopien von `docs\` und `wissens-layer\` dort sind **seit 26.09.2026 veraltet** |

**Arbeitsweise seit 26.09.2026:** Die KI committet selbst auf einen eigenen Arbeitszweig
(`claude/...`). In `main` (die Live-Fassung, von dort läuft die Engine) kommt eine
Änderung erst nach Kaisers ausdrücklichem „Go“.

**Alte Pfade:** Wo in älteren Texten `signal-app\...` steht, ist jetzt die Wurzel dieses
Repos gemeint (`signal-app\engine\` = `engine\`). Die rund 20 Code-Verweise auf
`docs\...` gehen seit dem Umzug nicht mehr ins Leere.

## Wie dieser Ordner zu benutzen ist

Der Wissens-Layer **verschiebt nichts**. Er fasst zusammen und verweist auf die
Originale, die an ihrem Platz bleiben. Bei Widerspruch gewinnt immer das Original.

| Datei / Ordner | Beantwortet die Frage |
|---|---|
| `00_STAND.md` | Wo steht das Projekt heute, was kommt als Nächstes? (**zuerst lesen**) |
| `01_produkt/` | Was soll die Engine leisten, was bewusst nicht? |
| `02_status/` | Was wurde gemessen, was ist entschieden, was ist offen, was lief zuletzt? |
| `03_architektur/` | Wie ist das technisch gebaut, welche Workflows laufen? |
| `04_konventionen/` | Nach welchen Regeln wird hier gearbeitet, welche Fallen sind bekannt? |
| `05_quellen/` | Welche Datei ist wofür die maßgebliche Wahrheit? |
| `06_entwicklung/` | Welche Befehle brauche ich? |

## Lesereihenfolge für eine neue KI-Session

1. `00_STAND.md` — Kurzstand.
2. `02_status/UEBERGABE.md` — die laufende Übergabe, **jüngster Abschnitt zuerst**.
3. `02_status/GEMESSEN-UND-ENTSCHIEDEN.md` — was schon gemessen und durchgefallen ist.
   **Diese Datei verhindert, dass zum dreizehnten Mal ein Filter vorgeschlagen wird.**
4. `02_status/OFFENE-PUNKTE.md` — was offen ist, nach Nutzwert sortiert.
5. `04_konventionen/ARBEITSREGELN.md` und `04_konventionen/BEKANNTE-PROBLEME.md`.
6. Bei Bedarf: `docs\STRATEGIE.md` (die Strategie), `03_architektur/UEBERBLICK.md`
   (der Bau), der jeweilige `docs\PLAN-E*.md`.

`docs\ETAPPENPLAN.md` ist die Chronik (128 KB) — **nachschlagen, nicht am Stück lesen.**

## Maßgebliche Quellen (Single Source of Truth)

| Thema | Maßgebliche Datei |
|---|---|
| Furkans Strategie | `docs\STRATEGIE.md` |
| Chronik aller Etappen, Begründungen, Kaisers Zitate | `docs\ETAPPENPLAN.md` |
| Was jeder Schalter tut und **warum** er an oder aus ist | `site\data\config.json` (Felder `_hinweis_*`) |
| Backtest-Zahlen | `BACKTEST.md` (wird bei jedem Lauf neu erzeugt — nie von Hand ändern) |
| Kaisers notierte Furkan-Termine (Rohdaten) | `Kauftrigger.md`, `Verkaufstrigger.md` |
| Technische Grundsatzentscheidungen | `docs\ARCHITEKTUR.md` |
| Der fertige Übergabe-Prompt für einen neuen Chat | `STARTPROMPT.md` (Repo-Wurzel) |

## Übergabe an eine neue Session oder eine andere KI

Der fertige Text zum Einfügen steht in **`STARTPROMPT.md`** im Ordner
`C:\Users\oeztu\BTC-Trading`. Er wird bei jeder größeren Änderung mitgezogen; wer ihn
ändert, ändert ihn dort und nirgends sonst. Ein reiner Prüfdurchlauf (nichts ändern,
nur nachrechnen und widersprechen) hat seinen eigenen Text in **`PRUEFPROMPT.md`**.

Die laufende Übergabe — was zuletzt passiert ist, was halb fertig ist, welche
Entscheidung offen liegt — steht in `02_status/UEBERGABE.md`.
