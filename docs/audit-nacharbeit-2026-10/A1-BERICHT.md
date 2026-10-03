# A1 – Konfigurationstypen und ATR bei kurzem Vorlauf

Stand: Implementierung auf Basis `dc5ddd6aaa8cde6a44c51892910c045ebd6f387a`; nur A1. Änderungen an Live-Zustand, Strategiekandidaten und historischen Gesamtläufen waren nicht Teil dieser Etappe.

## Fachliche Ergebnisse

| ID / Priorität | Fundstelle | Auswirkung | Vorher-/Nachherbeleg |
|---|---|---|---|
| F11 / P3 | `engine/main.py:370–400`; Regression `engine/test_main.py:358` | `bool("false")` ist in Python wahr. Damit konnte eine als Long-only gedachte Konfiguration unbeabsichtigt Shorts zulassen; zusätzlich verschleierte die Umwandlung einen Schemafehler. | Unveränderte Basis-SHA ausgeführt: `eval_params({"bias_short":"false"})` ergab `True`. Neu gilt ein enger Typvertrag: jeder boolesche Schalter muss als JSON-Bool (`true` oder `false`) vorliegen. Ein falscher Typ bricht mit `TypeError` samt Feldnamen und Wert ab; kein stiller Default kann den Modus umkehren. Echte `True`/`False` bleiben identisch. Die versionierte `site/data/config.json` verwendet native JSON-Booleans (u. a. `bias_short: false`) und bleibt gültig/unverändert. Gezielte Regression prüft `false`, `true`, Text, Integer und `null`. |
| F16 / P3 | `engine/strategy_core.py:148–164`; Regression `engine/test_strategy_core.py:28` | Bei kurzem Vorlauf waren die Slices der Vorgänger- und aktuellen Kerzen unterschiedlich lang und nicht ausgerichtet. Fester Originalvektor lieferte ATR `2` statt `26`; normaler Vorlauf war von dieser speziellen Slice-Verschiebung nicht betroffen. | Originalgegenprobe am Basisstand: drei Kerzen ergaben `2.0`. Unabhängig von `atr()` berechnete TRs des Prüfvektors sind `21` und `31`, Mittel `26`. Neue Implementierung bildet die letzten bis zu `period` aufeinanderfolgenden True Ranges aus `period+1` Schluss-/OHLC-Kerzen. Gezielte Regression deckt leeres Fenster, eine Kerze, zwei TRs bei `period=14`, genaues Fenster `period=2` und längeren Verlauf `period=3` mit unabhängiger Rechnung ab. |

## Typverträge und Grenzen

JSON-Bools sind ausschließlich die JSON-Literale `true` und `false`, die Python als `bool` lädt. Strings wie `"false"`, Zahlen wie `0`/`1`, `null` und andere Werte werden als ungültig abgewiesen. Diese Abweisung ist bewusst ein harter Fehler: auf den Default zurückzufallen wäre bei einem Schalter mit `True`-Default ebenfalls eine mögliche unbemerkte Richtungsumkehr. Der bisherige tolerante Default-Fallback für ungültige numerische Werte bleibt unverändert.

ATR berechnet den einfachen Mittelwert der letzten höchstens `period` True Ranges. Für jede True Range wird die Kerze mit ihrem unmittelbaren Vorgänger verglichen. Weniger als zwei Kerzen ergeben `0.0`; eine Periode kleiner als eins ist ungültig und ergibt `ValueError`. Bei normal langem Vorlauf bleibt die Auswahl der letzten `period` Paare dieselbe wie zuvor.

## Prüfungen und Abnahme

Gezielte Tests: `engine/test_main.py::test_eval_params_verlangt_json_booleans_statt_truthy_text` und `engine/test_strategy_core.py::test_atr_kurzer_vorlauf_und_volles_fenster_gegen_unabhaengige_true_ranges` bestanden. `git diff --check` bestanden. Diese zielgerichteten Belege sind keine Aussage zu Strategieperformance. Keine Renditeoptimierung, keine historischen Gesamtläufe, kein Telegram-/Broker-Aufruf, kein Deployment, kein Merge und kein Live-Umschalten.

Der vollständige Repository-Testlauf ergab 743 bestanden und 0 fehlgeschlagen (Windows mit `PYTHONUTF8=1`). Der sichere Tests-CI-Lauf zur exakten Abschluss-SHA sowie Bundle-Hash und geprüfte Wiederherstellung aller getrackten Git-Blobs sind im lokalen additiven A1-Übergabebeleg und Hashmanifest dokumentiert. Der vollständige fortgeschriebene 22-ID-Status steht in [`REGISTER.md`](REGISTER.md) und [`REGISTER.json`](REGISTER.json).
