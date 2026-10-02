# A5 – Kapitalbindung, Funding und V2-Vertragsgrenze

02.10.2026. Ausschließlich F02/F12, A1–A4 erhalten. Basis
`291588946206333ca58d771f1cc96f261da1a981`, Implementierung
`2554a582d4b1c8dd1b3bca73ca3b5ad67c67964a`, Zweig
`codex/a1-audit-nacharbeit`, Arbeitsbaum `C:/Users/oeztu/BTC-Trading/a1-work`.
Der [A5-Vertrag](A5-VERTRAG.md) wurde vor der Implementierung gespeichert.

## Ergebnis und Reichweite

F02 ist im vereinbarten Offline-Umfang durch korrekte synthetische Buchrechnung
und explizite Ablehnung unbelegter historischer Derivatfälle behandelt.
**V035 bleibt nicht auswertbar.** Es gibt keinen neu implementierten kausalen
Short-Strategiepfad und keinen Nachweis historischer Derivatfills. Das ist die
beauftragte Ablehnung nicht unterstützter Fälle, kein behaupteter Derivatebacktest.
F12/V2 ist ausdrücklich abgegrenzt; V1/i+2 bleiben gültige Spot-Vergleichsverträge.

| Priorität / ID | Datei und Zeile im Implementierungscommit | Auswirkung / Änderung | Beleg |
|---|---|---|---|
| P2 F02 | `engine/backtest.py:950` | Alte Shortrechnung ohne Margin/Funding wird standardmäßig abgewiesen. Nur ausdrücklich `legacy_derivatives=True` erlaubt die unveränderte historische Reproduktion, mit maschinenlesbarer Ungültigkeitskennzeichnung. | `A5-vorher.log`; `test_a5_accounting.py:195` |
| P2 F02 | `engine/derivative_accounting.py:42`, `:104`, `:141` | Getrennte Spot-/Perpetual-Bücher, Losmengen, 1x-Margin, freie Mittel, Kosten, Gross Exposure ohne Netting. Zweite Vollbelegung abgewiesen; keine Nutzung unrealisierter Gewinne als Wallet. | Handfälle `:36`, `:69`, `:209`; unabhängiges Fraction-Buch `:136` |
| P2 F02 | `engine/derivative_accounting.py:82`, `:129` | Expliziter Zahlungskalender, Rate/Quelle und exakt zeitgleicher Markpreis. Positive Rate belastet Long und begünstigt Short; Altbestand zahlt vor gleichzeitigen Fills. Fehlende Zahlung wird nie Null. | Tests `:47`, `:88`, `:102` |
| P2 F02 | `engine/derivative_accounting.py:111`, `:125` | Konservative Risikodomäne; bei Grenzverletzung keine gültige Gesamtrechnung und keine erfundene Liquidation. | Test `:113` |
| P2 F02 | `engine/execution_v1.py:352`, `engine/execution_delayed.py:33` | Explizite Perpetual-Longs, Shortkonfigurationen, fremde Produkte und Hebel ungleich 1 werden abgewiesen. Fehlendes Instrumentfeld behält ausschließlich den bereits geltenden Spot-Modellvertrag. | Test `:185`; alle vorhandenen V1/i+2-Tests |
| P2 F02 / Daten | `tools/a5_inventory.py:12`; `A5-historical-eligibility-v1.json` | 79 ursprüngliche Gitterzeilen plus acht Strukturzeilen mit einer identischen Konfiguration ergeben 86 eindeutige Zeilen. V035 gesperrt; übrige Zeilen erhalten nur eine F02-Einstufung unter Spot-Annahme, keine allgemeine Daten-/Ergebnisfreigabe. | Test `:220`; Originaldateihashes und unveränderte Parameter im neuen Inventar |
| P1 F12 / Vertragsgrenze | `engine/backtest.py:1154`; `A5-VERTRAG.md`, Abschnitt F12/V2 | Level-/Close-Diagnostik ist keine vorherige Order und kein erreichbarer Fill. Keine neue V2-Strategie. | Original-Gegenfall; bestehender `test_execution_v1.py:253` mit echtem Kandidaten 170 und späterem Fill 130 |

## Vorher und unabhängige Rechnungen

`tools/a5_baseline.py` liest temporär die Python-Dateiblobs des Originalaudits
`ccf2b01c0578346f325261e72445b7375a9ac706` und des A4-Ausgangscommits.
Beide reproduzieren zwei 100-%-Shorts: 200 % nominale Belegung und 20 % Gewinn bei
10 % Kursrückgang. Ein einzelner unverschuldeter 100-%-Short hätte 10 % erzielt.
Beide erreichen außerdem das F12-Ziel, das sich mit dem neuen Kerzentief von 200
auf 170 ändert und rückwirkend derselben Kerze zugeordnet wird. Die reine
Signalerzeugung ist keine vorab aktivierte Order. Protokoll: [A5-vorher.log](A5-vorher.log).

Die 14 neuen Testfunktionen enthalten unter anderem folgende ausgeschriebenen Fälle:

| Fall | Rechnung / Ergebnis |
|---|---|
| Zwei 100-%-Shorts, Start 10.000, Preis 100, keine Kosten, Ende 90 | Erster bindet 10.000; zweiter abgelehnt; End-Equity 11.000 |
| 40 BTC, Mark 100, Funding +1 % | Long −40 USD, Short +40 USD; bei −1 % Vorzeichen umgekehrt; gemessene Null = 0 |
| Spot-Long gegen Perpetual-Long, gleiche Menge/Preise | Spot 10.000 Equity, Perpetual 9.960 nach obiger Zahlung; kein Funding aus bloßer Long-Richtung weggelassen |
| Long 40@100, Abbau 10@110 und 30@120, Gebühr 1 %, Funding +2 %/−1 % | 10.000+700−87−88+36 = 10.561; Margin 4.000→3.000→0 |
| Short 40@100, Abbau 10@90 und 30@80, gleiche Kosten/Raten | 10.000+700−73+72−24 = 10.675 |
| Eröffnung genau an 8h, Teilabbau an 16h, Restabbau an 24h | Zahlungen nur an 16h auf 40 BTC und 24h auf 30 BTC; keine an 8h/32h |
| Unabhängiges gemischtes Buch | Fraction-Rechnung mit separat verwahrten Sicherheiten und freiem Cash; jeder Ereignisstand abgeglichen; 10.000+475−10,175+18 = 10.482,825 |

Das unabhängige Buch benutzt keine Produktionsfunktion für Bewertung, Gebühren,
Funding oder Margin. Es erhält dieselben ausdrücklich vorgegebenen Fills und
Raten. Die Rechnung belegt Kapitalerhaltung und Kosten, keine reale Ausführung.

Die vorhandenen Fundingpfade liefern Indikatoren: `engine/main.py:227` skaliert
stündliche relative Werte mit acht; `tools/prepare_n6.py:28` übernimmt dieselbe
Skalierung für den Flow. `docs/nach-6/r1-manifest.json` belegt Rohquellen und
Zeitstempel, aber weder einen vollständigen damaligen Vertrags-/Zahlungsnachweis
für V035 noch passende Perpetual-Markpreise. Spot-OHLC ist kein stiller Ersatz.
Diese Dateien und R0/R1 wurden nicht verändert; keine neue Datensammlung.

## Regression und Erhalt

- **784 Tests bestanden, 0 fehlgeschlagen:** 770 bestehende und 14 neue Funktionen.
  Darunter sämtliche A1–A4-, V1-, i+2- und F12-Handproben.
- **Sechs** synthetische Statistikprüfungen und **15** erreichte Nach-6-Schutzproben
  bestanden. Keine T01-Gesamtabnahme und keine neue historische Messung.
- Drei alte Short-Testfunktionen behalten sämtliche numerischen Assertions,
  verwenden aber ausdrücklich den ungültigen Legacy-Reproduktionsmodus. Der erste
  Gesamtlauf fand noch zwei fehlende Opt-ins (780/2); nach deren Ergänzung 784/0.
  Originaltests bleiben am A4-Commit ausführbar; keine Erwartung gelöscht.
- Alle 22 Register-IDs fortgeführt; nur F02 und F12 fachlich geändert. A4-Volume,
  Strategie-/Flow-/Aggregationscode, R0/R1, Workflows und historische Berichte
  unverändert. A3-Datensperren und A4-Bereitstellungsgrenzen gelten weiter.
- Logs liegen in der additiven A5-Sicherung; keine privaten Transkripte oder
  Backupverzeichnisse werden in den öffentlichen Zweig aufgenommen.

## Abschluss und Grenzen

Vor dem Push sind alle lokalen sowie aktuellen Defaultbranch-Workflows einschließlich
`workflow_run` gelesen und als Beleg gespeichert. Nur Tests dürfen ausgelöst werden.
Exakte Abschluss-SHA, CI-Ergebnis, vollständiges Bundle, Hashmanifest und geprüfte
Wiederherstellung stehen in `UEBERGABE.md`/`UEBERGABE.json` der neuen A5-Sicherung.
Dieser Bericht nimmt deren Ergebnis nicht vorweg.

Das synthetische Perpetualbuch unterstützt ausschließlich USD-Sicherheiten, lineare
BTC/USD-Kontrakte, explizite Fills und einen periodischen Zahlungskalender. Es ist
keine Börsenintegration. Grenzverletzungen führen zu nicht auswertbar, nicht zu
einem erfundenen Margin-Call/Stop/Fill. Markpunkte belegen keine Intrabar-Solvenz.
V035 bleibt ohne weitere Evidenz gesperrt; V2, E41.6 und unbekannte manuelle Bestände
bleiben Grenzen. A4-Speicherbereitstellung/Migration/Runner-Anbindung bleibt offen.
Kein Live-Go, main-Merge, Deployment, Pages, echter Versand, Broker oder Secretabruf.
