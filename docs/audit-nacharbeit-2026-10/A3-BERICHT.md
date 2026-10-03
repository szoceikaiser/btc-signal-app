# A3-Bericht – UTC-Tage, Börsenkorb und Einheiten

Basis: `c90fcd616f684b4b134f423fd86a2eaf6b95467c`, isolierter Zweig
`codex/a1-audit-nacharbeit`. Fachvertrag vor Korrektur:
[`A3-VERTRAG.md`](A3-VERTRAG.md). Synthetische Vorher-/Nachherwerte:
[`A3-ABLEITUNG-v1.json`](A3-ABLEITUNG-v1.json). Keine Rendite- oder
historische Gesamtauswertung in A3.

| ID / Priorität | Fundstelle, Auswirkung | Vorherbeleg | Korrektur und unabhängiger Nachherbeleg |
|---|---|---|---|
| F08 / P2 | `engine/strategy_core.py:310`: `resample_daily` aggregierte auch zwei von sechs 4h-Kerzen zu einem UTC-Tag. Tages-EMA und 1D-Fib konnten Teil- und Lückentage verwenden. | `audit-work/audit/probes.py:113–116`; am A2-Abschlussstand zwei Kerzen → eine Tageskerze. | `engine/strategy_core.py:310–344` verlangt sechs unterschiedliche, auf UTC-Mitternacht ausgerichtete abgeschlossene Slots. `engine/test_a3_data.py` prüft UTC-Wechsel, Teil- und Teillückentag getrennt. Vorhandene synthetische 1D-Fixtures wurden in `engine/test_strategy_core.py` und `engine/test_main.py` auf vollständige UTC-Tage gebracht; es wurde keine alte Testfunktion entfernt. |
| F14 / P3 | `engine/coinalyze.py:570` und `:821`: der Schnitt wurde nur über antwortende Märkte gebildet. A konnte bei fehlendem B als vollständige Summe oder vollständiges OI-Mittel erscheinen. | `audit-work/audit/additional_probes.py:14–19`; A=10/11, B ohne Antwort → `{0:10,1:11}`. | Summe und gewichtetes Mittel verlangen den ganzen angeforderten Korb. Ohne B: `{}`, zwei ausgelassene Punkte und expliziter Fehler; bei einer Teillücke bleibt nur der andere Punkt. `engine/test_a3_data.py`, `engine/test_coinalyze.py`. Liquidationen benötigen jetzt beide Felder `l`/`s` je Punkt, statt ein fehlendes Feld als null zu erfinden (`engine/coinalyze.py:930`). |
| F15 / P3 | `engine/coinalyze.py:262`, `:732`: rohe BTC- und USD-Volumina steuerten Rangfolge und Denominierungsgruppe. 2.000 USD schlugen 1.000 BTC trotz 60 Mio USD Gegenwert bei 60.000 USD/BTC. | `audit-work/audit/additional_probes.py:20–26`; Originalauswahl USD. | `engine/coinalyze.py:349–413` normalisiert je Punkt nur bei belegter Instrumenteinheit und Quote/USD-Kurs. `:262–295` und `:732–759` vergleichen USD-Umsatz. CVD-Adapter `:610`/`:762` verlangen belegte Einheiten; unbekannte Umrechnung liefert keine Reihe. Offline-Gegenfall: 60 Mio gegen 2.000 USD → BTC-Gruppe; fehlender FX-Kurs nicht auswertbar (`engine/test_a3_data.py`). |
| D01 / Regression | Eine laufende 4h-Kerze darf nicht in Tageswerte gelangen. Der Tageshelfer setzt abgeschlossene Eingänge voraus. | Vorheriger D01-Abschluss laut `engine/test_d01_kerzenschluss.py`. | Dieselbe D01-Testdatei ist im A3-Gesamtlauf grün; Backtest-Cutoff und Live-Filter wurden nicht verändert. |

Historische Aggregatvarianten sind in `engine/backtest.py:2865–2902`
ausdrücklich gesperrt: Eine heute gefundene Marktliste belegt den damaligen
Auswahlkorb nicht. A3 meldet diese Reihen als nicht auswertbar. Ein damaliger
Point-in-time-Markt-/Umrechnungsnachweis liegt nicht vor; A7 darf ohne ihn keine
historische Aggregatrendite behaupten. Die Hauptreihe auf vorhandenen
Binance/Kraken-Daten, R0/R1-Rohdaten, alte Berichte und Originalgegenproben bleiben
unverändert. Eine tatsächliche damalige API-Verfügbarkeit wird nicht behauptet.

Lokaler Offline-Lauf: `engine/run_tests.py` mit `PYTHONUTF8=1`: **756 bestanden,
0 fehlgeschlagen**; `tools/test_historical_stats.py`: sechs synthetische Prüfungen;
`tools/verify_n6_probes.py`: 15 Sabotagefälle gefangen. Testprotokoll:
[`A3-tests-local.log`](A3-tests-local.log). Die operative CI-/Sicherungsabnahme
wird in der A3-Übergabe mit exakter Abschluss-SHA belegt.
