# P2b – begrenzte Umsetzung nach P2a

Modell `gpt-6-sol`, Denkaufwand `high`, im neuen Chat tatsächlich auswählen.
Der Betriebs-/Migrationsvertrag ist vorgegeben; Sol soll die begrenzte Umsetzung
und Gegenfälle übernehmen. Kein max/ultra, keine parallelen Agenten, keine erneute
allgemeine Auditrunde. Keine laufende Sammlung und keine Renditeoptimierung.

## Arbeitsreihenfolge und Dateigrenzen

Zuerst externe P2a-Übergabe, `P2A-BETRIEBSVERTRAG.md`, `P2A-MIGRATIONSVERTRAG.md`
und dieses Dokument lesen. Adapterentwurf nur für Paket G. Danach ausschließlich
unten genannte betroffene Dateien. P2a-Originale bleiben als Vertrag erhalten;
notwendige Abweichung begründen und in eigenem P2b-Bericht festhalten.

| Paket | Dateien (neu, sofern angegeben) | Abgegrenztes Ergebnis |
|---|---|---|
| M – Offline-Migration | neu `tools/produktion_migrate.py`, `engine/production_contract.py`, `engine/test_production_migration.py`; gezielt `engine/position_state.py` | Reiner Konverter nach Eingabe-/Ausgabetabelle; vollständiger Feld-/Historienabgleich, B/W, Config-Pin, Unknowns, gates, kein Netzwerk. Kein echter Store. |
| S – Store und Runner | `engine/durable_delivery.py`, `engine/main.py`, `engine/telegram_outbox.py`; neu `tools/produktion_runner.py`, `tools/produktion_store.py`, `engine/test_production_runtime.py` | Snapshot v2, Control-Erhalt auch wenn main.py engine ersetzt, fail-closed Eingang für alle Pfade, historische Unterdrückung, gepinnte Config, Position/History erhalten. Vorhandenen SQLite-Adapter wiederverwenden; keine unnötige neue Datenbankbibliothek. |
| O – Betrieb offline | neu `tools/produktion_health.py`, `tools/produktion_backup.py`, `tools/produktion_reconcile.py`, `tools/produktion_export.py`, `engine/test_production_operations.py`; neu `ops/produktion/README.md`, `ops/produktion/runtime.example.json` | Health, konsistentes Backup/Restore in neue Ziele, gesperrter Restore, zweistufige positive Belegklärung mit erwarteter Revision, geheimnisfreier Projektionsexport. Kein Reset und kein automatischer Versand. |
| H – vorhandener Host, nur nach D1 | in `ops/produktion/` genau ein zum benannten Host passendes deaktiviertes Scheduler-/Servicebeispiel | Absolute Pfade, Konto/Rechte, UTC-Schedule, Prozess-/Timeoutregeln. Kein Installieren/Starten/Registrieren eines Dienstes. Ohne Host nur plattformneutrale Runneranbindung. |
| G – GitHub-Adapter, separat und nur nach D1 | neu `engine/github_delivery.py`, `engine/test_github_delivery.py`, lokale Fake-API-Fixtures; minimale Store-Fabrik in `durable_delivery.py`, deaktivierte Workflowvorlage in `ops/produktion/` | Exakt separater P2a-Adapterentwurf, bedingte Updates/Owner/Commitnachweis; Tests ausschließlich lokal. Keine privaten Repos/Tokens erstellen, keine echten Store-API-Schreibvorgänge. G nicht zusätzlich zu H bauen. |
| C – Nachweise | `.github/workflows/produktion-offline.yml`, ggf. `tests.yml`; neu `tools/produktion_p2.py`, `docs/produktionsuebernahme-2026-10/P2B-BERICHT.md` und maschinenlesbare Nachweise | Sichere branchgebundene CI, gezielte neue Fälle plus vollständige Engine-Regression; P1-Nachweis als eingefrorener Befund erhalten. Eigener Commit, exakte CI, additive geprüfte Sicherung und Folgeprompt. |

Keine Änderungen an Strategieparametern, Backtestmodellen, Rohdaten, alten
Arbeitsbäumen oder Sicherungen. `strategy_core.py` nur dann gezielt ändern, wenn
ein konkreter neuer Test einen Vertragsverstoß beim Erhalt der Altposition belegt;
keine neue Strategieentscheidung. Bei Änderung deren Auswirkung benennen und nur
betroffene Nachweise erneuern. Die Renditeaufstellung bleibt unverändert.

## Ein-/Ausgaben und sichere Bedienung

M-Eingaben und Dateischema sind vollständig im Migrationsvertrag festgelegt.
P1-Fixture aus exakt `ca8ad2f...`/P1-Blobs auslesen, nicht aus weiterlaufendem main.
Rehearsal-Grenze offen als synthetisch kennzeichnen. Alle Testbelege und Ziele
synthetisch; Transport injiziert/mocked, unerwarteten Netzwerkzugriff im Test
hart fehlschlagen lassen. Quellen vor/nach dem Test hashen.

CLI-Abgrenzung: `migrate` erzeugt Paket, `store provision` erzeugt neuen gesperrten
Teststore, `runner --offline` simuliert Fortsetzung ohne Credentials, `health`
liest, `backup` erzeugt neues Paket, `restore` neues gesperrtes Ziel,
`reconcile --review` erzeugt Änderungsplan und `--apply-review` verlangt dessen
Hash plus erwartete Revision. Positive Zustellklärung ändert weder Position noch
Nachrichtentext. Kein generisches Freigabe-/Reset-Flag, kein Live-Aktivierungsbefehl
in P2b. Reale Aktivierung bleibt P4 nach P3 und ausdrücklich freigegebenem Paket.

Der öffentliche Export ist eine Feld-Allowlist, kein nachträgliches Entfernen
einiger bekannter Secretfelder. Kein privater Snapshot im Repository/Pages/CI-Log.
P2b darf aktive `.github/workflows/signal.yml`, `watch.yml`, `lage.yml` nicht auf
einen neuen Versender umschalten. Zukünftige Runnerworkflows nur als deaktivierte
Vorlagen außerhalb `.github/workflows`; unter `.github/workflows` ausschließlich
Offline-Tests ändern. P3 prüft die spätere Aktivierungsdiff separat.

## Verbindliche Gegenfälle / Abnahme

| ID | Fall | Erwartung |
|---|---|---|
| M01 | Direkter Import originaler P1-T1 ohne `_delivery` | Weiterhin abgewiesen. Nur expliziter geprüfter Legacy-Konverter erzeugt Kandidaten. |
| M02 | T1-Konvertierung und Serializer-Rundlauf | Alle bekannten Positionswerte gleich; signal_reference, keine Lose/Fills; unbekannter Höchststop und fehlende Werte gekennzeichnet. |
| M03 | Vollständige Alt-Historie einschließlich >500 Einträgen | Unverändert importiert und beim ersten neuen Lauf nicht still abgeschnitten. Keine alten Outboxnachrichten. |
| M04 | Fehlende/alte Watchdatei, offene Grenzwarnung, gleiche Kerze neu gestartet | Keine alte Warnung oder Auflösung, keine fiktive Quittung. Erst Kerze >W darf neu warnen. |
| M05 | B/History-Zeitkonflikt, Lücke, Zukunft, unklare letzte Runs, fehlende Pflichtdatei, gemischte Revisionen, fremdes `_delivery`, NaN, falsches Schema | Fehlerbericht, kein aktivierbarer Zustand; Quellen bytegleich. |
| M06 | Wiederholter Konverter, vorhandenes Ausgabe-/Storeziel, teilweiser Schreibfehler | Deterministische Ergebnisse nur in neuen Zielen; vorhandene Daten unangetastet; kein halb aktiver Store. |
| K01 | alte state.config alt, Ziel usd; gleiche B und geänderter Plan/Vorschau | Kein Versand bei bloßer Neuprojektion; neue Kerze verwendet usd. E42/Short aus. |
| K02 | fehlende/defekte Config, Pinabweichung, andere Parameterdifferenz, abgelaufener Cutover | Fail-closed vor Fetch/Send; kein Altconfig-/Default-Fallback. |
| S01 | Abbruch nach Intent, vor/nach sending, nach Annahme, nach Quittung; gesamten temporären Runner verwerfen | Intent überlebt, sending wird uncertain, bestätigtes/unklares nie nochmals senden. Echte Kindprozesse, künstlicher Transport. |
| S02 | Zwei Runner und alle manuellen Pfade konkurrieren | Genau ein Mutex-Owner; Gegner sendet/entscheidet nicht und verändert Recovery nicht. |
| S03 | Store fehlt/falsch/defekt, Disk-full/Commitfehler, falsches Ziel/Bot, Mirrorverlust | Keine Neuanlage/keine Git-Rückfallquelle; keine Nachrichten nach unbestätigter Schreibgrenze. |
| S04 | uncertain plus neue Operation-ID, Watch, Lage, Test, Hauptlauf, resend-all | Global blockiert **vor** neuer produktiver Auswertung; keine Historiennachsendung durch Umgehung. |
| S05 | Explizite Ablehnung und Retry | Gespeicherter Text/ID bleibt gleich; keine Rekalkulation, keine enge Wiederholung. |
| O01 | gültige und unpassende/fehlende positive Klärungsbelege, stale Revision, Plan nachträglich geändert | Nur passender positiver Beleg bestätigt; Unklarheit nie pending; nachvollziehbarer Klärungseintrag. |
| O02 | Backup während konkurrierendem Schreiber; Restore alte Revision | Konsistente Sicherung oder Abbruch; Restore immer blocked; kein behaupteter Verlustnachweis allein aus SHA. |
| O03 | kompletter Runner-/Store-Neustart, negative Healthfälle, fehlender Watch-Heartbeat | Richtige Status-/Exitklassen; Stillstand sichtbar, keine automatische Freigabe. |
| O04 | Public Export enthält `_delivery`, Control, Text/Belege oder unbekannte Felder | Negativtest muss Export verweigern/Allowlist anwenden; sichere Anzeige bleibt nutzbar. |
| G01 | Falls gewählt: alle Konflikt-/Timeout-/Owner-/Kapazitätsfälle aus Adapterentwurf | Lokale Fake-Protokolltests grün; reale API-Probe ausdrücklich noch offen. |

Zusätzlich vollständige Engine-Suite; P1 hatte 796 Tests. Neue Zahl tatsächlich
messen, alte Zahl nicht als neues Ergebnis ausgeben. Keine Wiederholung historischer
Renditeläufe. P1-Quellgleichheit kann nach Engineänderungen nicht mehr auf HEAD
angewendet werden: P1 an seiner gepinnten SHA verifizieren/als vorhandenen Beleg
erhalten, P2 eigenständig auf Kandidaten prüfen. Nie einfach den Gleichheitscheck
abschalten und dieselbe P1-Aussage weiter ausgeben.

## Fertigstellungs- und Rückfallgrenzen

P2b liefert fertige M/S/O/C-Pakete und, falls D1 beantwortet, genau H oder G offline.
Ohne D1 weiter unabhängig arbeiten und Umfang am Ende ausdrücklich als
„gemeinsamer Offline-Kern fertig, Betriebsanbindung offen“ ausweisen; keinen
vollständig betriebsfertigen P2b behaupten. G ist neue Adapterarbeit, nicht durch
alte SQLite-Tests gedeckt. Fehlende reale Host-/GitHub-/Alarm-/Backupbelege sind
P3-Gates. D2 wird erst am frischen Kandidaten entschieden. Kostenfreiheit nicht
aus einem unbestätigten Tarif ableiten.

Vor Push alle lokalen und aktuellen Default-Workflowtrigger inklusive
`workflow_run` vollständig lesen. Nur Tests und branchgebundene Offline-CI dürfen
starten; keine alten Dispatchs. Eigener Etappencommit, Ergebnisse exakt zu dessen
SHA, additive Sicherung mit Hashmanifest und frischem Restore. Bei realem oder
simuliertem Versand nach einer Testgrenze nie auf älteres Journal zurückfallen.
Bei benötigter größerer Scopeänderung aktuellen Stand gesichert übergeben statt
eine neue Auditrunde oder neue Strategieentwicklung zu eröffnen.

Jeder Start-/Fortsetzungsprompt muss vollständig kopierfertig in einem Codeblock
der abschließenden Chatantwort stehen UND als Markdown-Datei gespeichert werden.
Link/Zusammenfassung genügt nicht. Jeder Prompt nennt konkrete Modell-ID und
Denkaufwand, begründet die budgetbewusste Wahl und vererbt diese gesamte Pflicht
ausdrücklich an alle Folgechats. Nach endgültigem Abschluss kein Folgeprompt.
