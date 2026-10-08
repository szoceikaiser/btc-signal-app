# P2b/P3: deaktivierte Betriebsanbindung

Die Werkzeuge sind nur für lokale, isolierte Offline-Prüfungen vorbereitet.
`runtime.example.json` ist absichtlich deaktiviert und enthält keine Pfade,
Zugänge oder Scheduler-Registrierung. In P3 wurde D1 als GitHub gewählt.
D3 hat einen benannten Nutzer als Verantwortlichen und ein weiteres privates
GitHub-Repository als Sicherungsziel; Alarm- und Backupbetrieb sind nicht eingerichtet.
`github-runtime.disabled.json` und `github-workflow.disabled.yml` bleiben
ausdrücklich deaktiviert. `P3-GITHUB-BERICHT.md` beschreibt die lokale Fake-API-
Abnahme und die noch offenen realen Store-/Alarm-/Backup-Gates.

## Reihenfolge für eine Offline-Probe

1. Konsistente, stillgelegte Quellen als explizite lokale Dateien bereitstellen.
   `source-manifest.json` hat `schema: produktion-source-v1`, `mode`,
   `repository`, `code_sha`, `source_sha`, `git_tree`, `captured_at_utc` und
   `files` mit SHA256 und Größe je Datei; `watch.json` darf ausdrücklich
   `presence: missing` haben. `cutover.json` enthält die dokumentierten
   Schnitt- und Stilllegungsbelege. Die P1-Probe benutzt synthetische Grenzen.
2. `python tools/produktion_migrate.py --source-dir ... --manifest ... --cutover ... --config ... --out NEUES_PAKET`
3. `python tools/produktion_store.py provision --package NEUES_PAKET --target NEUER_TESTSTORE`
4. `python tools/produktion_runner.py --offline --store NEUER_TESTSTORE --store-id ... --config ... --fixture SYNTHETISCHE_EINGABEN.json --kind signal`
5. `python tools/produktion_health.py --store ... --store-id ...` liest den
   lokalen Diagnosestatus; ohne externe Runmetadaten bestätigt er keine gesunde
   Produktion (`external_run_binding_unverified`). Exitcode 20 bedeutet gesperrter/unvollständiger Betrieb, 30 unklare
   Zustellung, 40 defekter Store. Das Werkzeug versendet keinen Alarm.
6. `python tools/produktion_backup.py backup --store ... --store-id ... --migration-package ... --out NEUE_SICHERUNG`
   kopiert mit SQLite Backup API unter exklusiver Store-Sperre.
   `python tools/produktion_backup.py restore --package ... --target NEUES_RESTOREZIEL`
   legt ausschließlich einen gesperrten Store mit offenem Nachfolgeabgleich an.
7. `python tools/produktion_export.py --store ... --store-id ... --out NEUER_EXPORT`
   schreibt nur freigegebene Anzeigeattribute. Nicht den privaten Store oder das
   Migrationspaket in `site/data` oder das öffentliche Repository kopieren.

Positive Klärung: Ein geschützter externer Beleg mit `status: confirmed`,
Nachrichten-ID, Text-SHA256, Zielbindung, Versuch und dessen `attempt_started_ms`,
positiver `receipt_message_id`,
UTC-Beobachtungszeit, benanntem Prüfer, Belegpfad und Beleg-SHA256 wird mit
`produktion_reconcile.py --review NEUER_PLAN --evidence ... --store ... --store-id ...`
geprüft. `--apply-review PLAN --review-sha256 HASH --expected-revision REV`
wendet ausschließlich diesen unveränderten positiven Plan an. Die reine
Dateiformprüfung ersetzt nicht die menschliche Prüfung der tatsächlichen
Zuordnung. Es gibt keinen Reset zu `pending` und keine automatische Freigabe.

Der Offline-Runner nutzt nur einen temporären kopierten Store und einen
synthetischen Transport. Ein echter Host, API-Berechtigungen, Alarmweg,
zweites Sicherungsziel, frischer Migrationssnapshot und D2 gehören zu P3/P4.

## Lokale Betriebsvorstufe vom 08.10.2026

`tools/p3_store_probe.py --offline --out NEUE_DATEI` hat ausschließlich FakeAPI.
`tools/produktion_freshness.py --offline --fixture SYNTHETISCHE_FIXTURE` bildet
eine HTTP-Entscheidung ohne Listener. `tools/p3_run_binding.py --offline --fixture ...`
prüft Dispatchslot und tatsächliche synthetische Runmetadaten. Das lokale Git-
Backupwerkzeug hat weder fetch noch push und restoret ausschließlich blocked.

Vertrag: `docs/produktionsuebernahme-2026-10/P3-BETRIEBSVORSTUFE.md`.
Fünf getrennte externe Vorschlagspläne: `P3-EXTERNE-PROBENPLAENE.md` im selben
Verzeichnis. `p3-acceptance.disabled.json` enthält ausschließlich offene Angaben
und Vorschläge; `p3-run-binding.disabled.yml` liegt außerhalb aktiver Workflows.
Keine dieser Dateien gibt Einrichtung, Mailprobe oder P4 frei.
# Sicherungskapazität N-P3-01: v2

Neue lokale Backupaufrufe verwenden `tools/p3_backup_chain.py` über die
synthetische CLI `produktion_github_backup.py`; der Plan muss zusätzlich zur SHA
die unabhängig verlangte `revision` enthalten. Basis und unveränderliche
Inkremente erhalten die ganze Historie. Vertrag und Grenzen:
`docs/produktionsuebernahme-2026-10/P3-BACKUP-V2-VERTRAG.md`.
v1-Funktionen bleiben explizit für alte Belege erhalten. Betriebsquittungen
müssen v2 sein und den vollständigen privat gelesenen und restored Verbund
binden. Lokale Verifikationsdateien sind keine privaten Backupquittungen.
Keine reale Einrichtung, neue externe Berechtigung oder Aktivierung hierdurch.
