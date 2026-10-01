# A2-Bericht: Flow-Kausalität und fehlende Information

Stand 01.10.2026. Basis `8ad1139793a2ec5724d418bc2fc3ab88801f8f9c`,
Implementierung `3d0a3af4c022a91d2ecb5528ac754ea793a5b766`, Zweig
`codex/a1-audit-nacharbeit`, Arbeitsbaum
`C:/Users/oeztu/BTC-Trading/a1-work`. Ausschließlich F06, F07 und D02 wurden
bearbeitet. Fachlicher Vertrag: [`A2-VERTRAG.md`](A2-VERTRAG.md).

| ID / Priorität | Vorher, Auswirkung | Änderung mit Datei/Zeile | Unabhängiger Beleg / Grenze |
|---|---|---|---|
| F06 / P2 | Originalgegenprobe `audit-work/audit/probes.py`: konstantes Futures-CVD-Offset ändert DERIVATE_PUMP in GESUNDER_TREND. Ein Summenstart ist keine Marktinformation. | `engine/strategy_core.py:1065,1144–1168` verwendet für den aktuellen Pfad Fensterdifferenzen und Dollarvergleich; `engine/main.py:372`, `site/data/config.json:25` setzen `usd`. | `engine/test_a2_flow.py:13` prüft unabhängige Spot- und Futures-Offsets. Ergebnis konstant DERIVATE_PUMP. Historische `alt`-Rechnung bleibt als Reproduktionsmodus; keine Renditesuche. |
| F07 / P2 | Originalgegenprobe `audit-work/audit/probes.py`: OI 12345 bei 8h erscheint bereits bei 0h. Das kann Vorlaufmuster verfälschen. | `engine/flow_contract.py:16–43` wählt nur vor Entscheidungszeit verfügbare Punkte; `engine/main.py:313`, `engine/backtest.py:782` nutzen denselben Vertrag. Vor erstem Wert `missing`, danach höchstens 8h nutzbare Fortschreibung. | `engine/test_a2_flow.py:27` prüft alle Präfixe, späten Erstwert, Alter/Status und Live-/Backtest-Parität. Keine Behauptung über damalige API-Publikation. |
| D02 / P2 | Originalgegenprobe `audit-work/audit/additional_probes.py`: fehlende Funding-Null kann Long bestätigen. Fehlend und neutral waren beide numerisch null. | `engine/strategy_core.py:28,1106,1440` nutzt Feldabdeckung für Muster/Bestätigung; `engine/main.py:318–333`, `engine/backtest.py:786–806` tragen Quelle, Zeit, Abdeckung und Alter mit; `engine/execution_v1.py:45` bewahrt es beim Wiederanlauf. | `engine/test_a2_flow.py:47,63,77` trennt gemessene Null, fehlend, veraltet, neuen und alten Checkpoint. Nur frische gemessene Null bestätigt aus Funding; andere belegte ODER-Zweige bleiben möglich. |

## Prüfungen und Entscheidungswirkung

- Lokaler Lauf `engine/run_tests.py` mit UTF-8: **748 bestanden, 0 fehlgeschlagen**;
  vollständiges Protokoll [`A2-tests-local.log`](A2-tests-local.log).
- `git diff --check` bestanden. Die ursprünglichen F06/F07/D02-Gegenfälle sind in
  `audit-work/docs/audit-2026-09-27/gegenproben.json` und
  `weitere-gegenproben.json` dokumentiert; diese Dateien blieben unverändert.
- Eine fehlende OI-Messung verlängert den fachlichen Warmup für OI-abhängige
  Muster bis zum ersten kausal verfügbaren Wert. Alte Rückwärtsfüllung kann keine
  Entscheidung mehr freigeben. Nach mehr als 8h ohne neuen Punkt ist das letzte
  OI veraltet; das Muster darf damit keine OI-Bedingung erfüllen.
- Funding `missing` oder `stale` erfüllt `funding <= 0` nicht. Ein echtes frisches
  Funding von null erfüllt diese bestehende Bedingung. Wenn eine andere vorhandene
  Bestätigung der ODER-Regel zutrifft, kann ein Einstieg dennoch zugelassen werden.
- Die historische 86-Zeilen-Gitterbasis und alte Panel-Zeile in `backtest.py`
  verwenden noch `alt`. Der aktuelle Konfigurationswert ist `usd`; die alte
  Panel-Rendite ist somit keine aktuelle A2-Rendite. Die gezielte Regression
  `test_panel_variante_entspricht_der_live_einstellung` weist genau diese eine
  Abweichung aus. Eine neue gepaarte Auswertung gehört ausschließlich zu A7.

## Datenstand und offene Grenzen

R0/R1-Rohdaten, Originalergebnisse und Hashregister wurden nicht geändert.
Die neue, additive Vertrags-/Gegenfallversion ist `a2-flow-v1` (Manifest
[`A2-ABLEITUNG-v1.json`](A2-ABLEITUNG-v1.json)); sie enthält keine neue
historische Rendite. R0/R1-Flow-Zeilen ohne alte Messmetadaten werden nicht
rückwirkend zu belegten Nullmessungen erklärt. Die damalige API-Verfügbarkeit,
unbekannte Veröffentlichungsverzögerung und echte Fills bleiben unbewiesen.
Tagesabschluss, vollständiger Börsenkorb und Einheiten sind A3; Ergebnisfolgen
sind A7. Kein Live-Go, Merge oder Deployment folgt aus A2.
