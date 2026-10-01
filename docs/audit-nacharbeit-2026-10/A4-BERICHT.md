# A4 – Versandpersistenz über Runnerverlust hinaus

A4 ist im vereinbarten isolierten Umfang implementiert und geprüft. **Reale
Betriebsbereitstellung bleibt offen.** Ausschließlich Rest F13; kein Live-Go.
Basis `aaadbf6606ae1082e2eb59fd0ef1e1d4e1f23c1b`, Implementierungscommit
`0cd06d2a81114966e34238d9bcf1074fc25461bc`, Zweig
`codex/a1-audit-nacharbeit`, Arbeitsbaum `C:/Users/oeztu/BTC-Trading/a1-work`.

Der vor der Umsetzung gespeicherte [Vertrag](A4-VERTRAG.md) legt Identitäten,
Schreibgrenzen und uncertain fest. [A4-BETRIEB.md](A4-BETRIEB.md) beschreibt die
implementierte Schnittstelle und gesondert erforderliche Bereitstellung.

## Befund, Änderung und Beleg

| Priorität | Datei/Zeile im Implementierungscommit | Auswirkung und Korrektur | Beleg |
|---|---|---|---|
| P1, F13 | `engine/main.py:929`, `engine/durable_delivery.py:164`, `engine/telegram_outbox.py:30` | Nach Runnerverlust fehlen lokale Quittungen; nun wird der externe Snapshot vor jedem lokalen Zustandsmirror committed und vor Marktverarbeitung wiederhergestellt. Position, Fortschritt und Intent bleiben zusammen. | Original-F13 und A3-Runnerverlust in `A4-vorher.log`; sechs harte Hauptlauf-Abbruchgrenzen in `test_a4_delivery.py:146` |
| P1, F13 | `engine/durable_delivery.py:66`, `:91`, `:101` | Fester Store, Inhaltsprüfung, Revision, synchroner Commit und prozessübergreifender Mutex. Fehlender/defekter/falscher Store verweigert den Lauf; kein stiller Git-Rückfall. Nach Prozessende wird sending uncertain. | `test_a4_delivery.py:169`, `:187`, `:207`, `:240`; Konkurrenz und Schreibfehler vor/nach simulierter Annahme |
| P1, F13 | `engine/durable_delivery.py:198`, `engine/main.py:719`, `:820`, `:1100`, `:1108`, `engine/telegram_notify.py:519` | Testnachricht, Neusendung, Lage und Watch besitzen nun gespeicherte Batches/Quittungen. Manuelle Auftrags-ID bleibt bei Wiederanlauf gleich. Watch-Merker wird gemeinsam mit Intent gespeichert. Direkter alter Einmalversand außerhalb eines Auftrags wird abgewiesen. | Vier erreichte Originalpfade in `A4-vorher.log`; zwölf harte Abbrüche mit Runnerlöschung in `test_a4_delivery.py:153`; gefrorener Lage-Batch ohne Refetch `:295` |
| P1, F13 | `engine/durable_delivery.py:111`, `:185`, `engine/main.py:953`, `:1091` | Unklare Zustellung blockiert auch neue Auftrags-IDs und Hauptlaufversand. Keine Wiederholung aufgrund fehlender Quittung, kein Reset. | `test_a4_delivery.py:252`; gespeicherte sending-Fälle nach Runnerverlust bleiben uncertain, Transportzähler bleibt unverändert |
| P1, Betriebsgrenze | `engine/durable_delivery.py:117`, `.github/workflows/signal.yml:75`, `watch.yml:39`, `lage.yml:41` | Separates geeignetes Volume, Migration und Anbindung sind noch nicht bereitgestellt. Die Workflows wurden nicht umgeschaltet. Ohne Konfiguration würde der neue reale Versand scheitern. | `A4-BETRIEB.md`; keine echten Nachrichten, kein produktiver Workflowtest |

## Reproduktion und Abnahme

`tools/a4_baseline.py` liest ausschließlich den unveränderten A3-Gitstand in ein
temporäres Verzeichnis und den gezielt extrahierten Original-F13-Block aus
`audit-work/audit/additional_probes.py:35`. Kein Original wird geschrieben. Der
Originalfall erreicht einen fehlgeschlagenen Versand und danach **null** neue
Versandversuche. Am A3-Stand entstehen nach Runnerverlust **zwei** simulierte
Annahmen desselben Signaltexts. Die vier ausgeschlossenen Befehle besitzen dort
keine dauerhafte Quittung; Watch markiert sogar eine abgelehnte Warnung als erledigt.

Die A4-Proben verwenden echte SQLite-Dateien, `os._exit(71)` in Kindprozessen,
eine separate simulierte Transportannahmeliste und entfernen das **gesamte**
temporäre Runnerverzeichnis. Quellcode/Fixture werden wie bei einem neuen Checkout
erneut verwendet; nur das außerhalb liegende Volume enthält den Versandzustand.
Das ist ein Nachweis für Runnerverlust, kein simulierter Verlust des Volumes selbst.
Ergebnisse der sechs Hauptlaufgrenzen:

| Abbruch | Dauerhafter Stand vorher | Annahmen vorher | Neue Versuche nach Wiederherstellung |
|---|---|---:|---:|
| vor Intentcommit | kein Intent | 0 | 1 nach erneuter Entscheidung |
| nach Intentcommit | pending | 0 | 1 ohne Signalreplay |
| nach sending, vor Aufruf | sending | 0 | 0, danach uncertain |
| nach Annahme | sending | 1 | 0, danach uncertain |
| vor Quittungscommit | sending | 1 | 0, danach uncertain |
| nach Quittungscommit | confirmed | 1 | 0 |

Zwölf weitere Prozessabbrüche decken Intentcommit, Annahme und Quittungscommit
aller vier zusätzlichen Pfade ab. Bei Neusendung bleibt der noch nicht versandte
zweite Batch-Eintrag nach bestätigtem erstem Eintrag pending und wird einmal
fortgesetzt. Weitere Proben prüfen echten aktiven Positionsstand statt altem
Checkout, Zielbindung, explizite Ablehnungswiederholung vor einem scheiternden
Marktabruf, Quittung trotz lokalem Spiegeldefekt, Watch-Auflösung durch die Engine,
fehlende Identität, unvollständige Migration, unbekannten Store und Dry-run.

Alle Transporte sind ersetzt; der Netzwerkzugriff der Transportbibliothek ist
zusätzlich gesperrt. Kein Telegram-Token wurde abgerufen. GitHub-Prüfungen benutzen
ausschließlich öffentliche unauthentifizierte Lesezugriffe; Git-Push verwendet
die reguläre Git-Anmeldung ohne Auslesen von Zugangsdaten.

## Regression und Erhalt

- `engine/run_tests.py`: **770 bestanden, 0 fehlgeschlagen** (756 bestehende plus
  14 neue A4-Testfunktionen; darin 18 getrennte harte Abbruchfälle).
- Sechs synthetische Statistikprüfungen und 15 Nach-6-Schutzproben bestanden.
- Die 16 erreichten 5a-Versandsabotagen wurden weiterhin erkannt; additive Datei
  `A4-5a-sabotage.json`. Keine T01-Gesamtabnahme vorweggenommen.
- Bestehende 5a-Tests behalten sämtliche Erwartungen. Ihr `offline`-Testkontext
  ersetzt ausschließlich die neue externe Session durch einen lokalen Kontext,
  damit deren ursprünglicher lokaler Vertrag weiter gezielt geprüft wird. Die
  A4-Tests benutzen den echten Adapter ohne diese Ersetzung. Originaltests bleiben
  über A3-Commit und Sicherung verfügbar.
- A1–A3-Strategie-/Datenkorrekturen, historische Eingaben, R0/R1, Workflows und
  alte Dokumente wurden nicht geändert. Keine Handels-/Renditeneuberechnung.
- `git diff --check` bestanden. Register enthält alle 22 ursprünglichen IDs;
  ausschließlich F13 erhält neue fachliche Statusbelege.

## Abschlussverfahren und offene Punkte

Vor dem einzigen Push wurden alle acht lokalen und alle acht öffentlichen
Defaultbranch-Workflows gelesen (beobachtetes main:
`15144d240fe8420b3607a32e01fbe75153cc223c`). Branch-Push startet nur Tests.
Pages-Push verlangt main/site; seine `workflow_run`-Kette hört ausschließlich auf
Signal-Engine/Backtest, nicht auf Tests. Keine Dispatches oder Workflowänderungen.

Die tatsächliche Registerabschluss-SHA, Tests-CI zur exakt gleichen SHA und die
verifizierte additive Sicherung stehen nach Abschluss in `UEBERGABE.md` und
`UEBERGABE.json` der neuen A4-Sicherung. Eine eigene Dokumentations-Abschluss-SHA
vermeidet eine selbstreferenzielle Commit-ID in diesem Bericht.

F13 ist für den Adapter und sämtliche inventarisierten Pfade unter dem erklärten
Volume-Vertrag behoben und simuliert geprüft. Realer Speicherbetrieb bleibt offen:
Bereitstellung, geprüfte Migration, zuverlässige Locks/fsync, Zugriffsschutz,
Überwachung und echte Betriebsabnahme sind nicht erfolgt. Separate Storekopien,
NFS, Volume-Verlust und alte Speicherbackups sind keine sichere Wiederherstellung.
Uncertain benötigt beleggestützte manuelle Klärung; keine Exactly-once-Behauptung.
Diese Grenzen werden im Register erhalten. A5 wird nicht automatisch gestartet.
