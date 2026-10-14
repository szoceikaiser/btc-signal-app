# P2b/P3: deaktivierte Betriebsanbindung

Aktueller begrenzter Vorschlag: `docs/produktionsuebernahme-2026-10/P4-KANDIDAT-VERTRAG.md`.
`tools/produktion_candidate_runner.py` ist an den tatsÃ¤chlichen Runner angebunden,
verweigert aber die mitgelieferte disabled-Runtime vor jeder Store-/Markt-/Transportarbeit.
Die neue opt-in BestÃ¤tigungsrichtlinie verlangt einen bereits vorbereiteten
persistenten Requestjournalpfad auÃŸerhalb des Runners. Keine automatische Anlage.
Reproduzierbarer Offlinebeweis: `python tools/produktion_candidate_offline.py`
(unter Windows optional `--temp-root ABSOLUTES_EXISTIERENDES_TESTVERZEICHNIS`).
Geerbtes `site/data` ist ausschlieÃŸlich alte P1-Basis, kein aktueller Migrationsinput.

Die Werkzeuge sind nur fÃ¼r lokale, isolierte Offline-PrÃ¼fungen vorbereitet.
`runtime.example.json` ist absichtlich deaktiviert und enthÃ¤lt keine Pfade,
ZugÃ¤nge oder Scheduler-Registrierung. In P3 wurde D1 als GitHub gewÃ¤hlt.
D3 hat einen benannten Nutzer als Verantwortlichen und ein weiteres privates
GitHub-Repository als Sicherungsziel; Alarm- und Backupbetrieb sind nicht eingerichtet.
`github-runtime.disabled.json` und `github-workflow.disabled.yml` bleiben
ausdrÃ¼cklich deaktiviert. `P3-GITHUB-BERICHT.md` beschreibt die lokale Fake-API-
Abnahme und die noch offenen realen Store-/Alarm-/Backup-Gates.

## Reihenfolge fÃ¼r eine Offline-Probe

1. Konsistente, stillgelegte Quellen als explizite lokale Dateien bereitstellen.
   `source-manifest.json` hat `schema: produktion-source-v1`, `mode`,
   `repository`, `code_sha`, `source_sha`, `git_tree`, `captured_at_utc` und
   `files` mit SHA256 und GrÃ¶ÃŸe je Datei; `watch.json` darf ausdrÃ¼cklich
   `presence: missing` haben. `cutover.json` enthÃ¤lt die dokumentierten
   Schnitt- und Stilllegungsbelege. Die P1-Probe benutzt synthetische Grenzen.
2. `python tools/produktion_migrate.py --source-dir ... --manifest ... --cutover ... --config ... --out NEUES_PAKET`
3. `python tools/produktion_store.py provision --package NEUES_PAKET --target NEUER_TESTSTORE`
4. `python tools/produktion_runner.py --offline --store NEUER_TESTSTORE --store-id ... --config ... --fixture SYNTHETISCHE_EINGABEN.json --kind signal`
5. `python tools/produktion_health.py --store ... --store-id ...` liest den
   lokalen Diagnosestatus; ohne externe Runmetadaten bestÃ¤tigt er keine gesunde
   Produktion (`external_run_binding_unverified`). Exitcode 20 bedeutet gesperrter/unvollstÃ¤ndiger Betrieb, 30 unklare
   Zustellung, 40 defekter Store. Das Werkzeug versendet keinen Alarm.
6. `python tools/produktion_backup.py backup --store ... --store-id ... --migration-package ... --out NEUE_SICHERUNG`
   kopiert mit SQLite Backup API unter exklusiver Store-Sperre.
   `python tools/produktion_backup.py restore --package ... --target NEUES_RESTOREZIEL`
   legt ausschlieÃŸlich einen gesperrten Store mit offenem Nachfolgeabgleich an.
7. `python tools/produktion_export.py --store ... --store-id ... --out NEUER_EXPORT`
   schreibt nur freigegebene Anzeigeattribute. Nicht den privaten Store oder das
   Migrationspaket in `site/data` oder das Ã¶ffentliche Repository kopieren.

Positive KlÃ¤rung: Ein geschÃ¼tzter externer Beleg mit `status: confirmed`,
Nachrichten-ID, Text-SHA256, Zielbindung, Versuch und dessen `attempt_started_ms`,
positiver `receipt_message_id`,
UTC-Beobachtungszeit, benanntem PrÃ¼fer, Belegpfad und Beleg-SHA256 wird mit
`produktion_reconcile.py --review NEUER_PLAN --evidence ... --store ... --store-id ...`
geprÃ¼ft. `--apply-review PLAN --review-sha256 HASH --expected-revision REV`
wendet ausschlieÃŸlich diesen unverÃ¤nderten positiven Plan an. Die reine
DateiformprÃ¼fung ersetzt nicht die menschliche PrÃ¼fung der tatsÃ¤chlichen
Zuordnung. Es gibt keinen Reset zu `pending` und keine automatische Freigabe.

Der Offline-Runner nutzt nur einen temporÃ¤ren kopierten Store und einen
synthetischen Transport. Ein echter Host, API-Berechtigungen, Alarmweg,
zweites Sicherungsziel, frischer Migrationssnapshot und D2 gehÃ¶ren zu P3/P4.

## Lokale Betriebsvorstufe vom 08.10.2026

`tools/p3_store_probe.py --offline --out NEUE_DATEI` hat ausschlieÃŸlich FakeAPI.
`tools/produktion_freshness.py --offline --fixture SYNTHETISCHE_FIXTURE` bildet
eine HTTP-Entscheidung ohne Listener. `tools/p3_run_binding.py --offline --fixture ...`
prÃ¼ft Dispatchslot und tatsÃ¤chliche synthetische Runmetadaten. Das lokale Git-
Backupwerkzeug hat weder fetch noch push und restoret ausschlieÃŸlich blocked.

Vertrag: `docs/produktionsuebernahme-2026-10/P3-BETRIEBSVORSTUFE.md`.
FÃ¼nf getrennte externe VorschlagsplÃ¤ne: `P3-EXTERNE-PROBENPLAENE.md` im selben
Verzeichnis. `p3-acceptance.disabled.json` enthÃ¤lt ausschlieÃŸlich offene Angaben
und VorschlÃ¤ge; `p3-run-binding.disabled.yml` liegt auÃŸerhalb aktiver Workflows.
Keine dieser Dateien gibt Einrichtung, Mailprobe oder P4 frei.
# SicherungskapazitÃ¤t N-P3-01: v2

Deaktivierte hosted-Actions-Anbindung: [GITHUB-ACTIONS-VERTRAG.md](GITHUB-ACTIONS-VERTRAG.md).
github-actions-runtime.disabled.json und github-actions-workflow.disabled.yml wÃ¤hlen drei BestÃ¤tigungszyklen mit
dauerhaftem CAS-Sperrbranch im Store-Repository. Kein self-hosted/SQLitejournal im neuen Actionspfad. Die alten deaktivierten
github-runtime/-workflow-Dateien bleiben fÃ¼r die abgenommenen Altbelege erhalten.

Neue lokale Backupaufrufe verwenden `tools/p3_backup_chain.py` Ã¼ber die
synthetische CLI `produktion_github_backup.py`; der Plan muss zusÃ¤tzlich zur SHA
die unabhÃ¤ngig verlangte `revision` enthalten. Basis und unverÃ¤nderliche
Inkremente erhalten die ganze Historie. Vertrag und Grenzen:
`docs/produktionsuebernahme-2026-10/P3-BACKUP-V2-VERTRAG.md`.
v1-Funktionen bleiben explizit fÃ¼r alte Belege erhalten. Betriebsquittungen
mÃ¼ssen v2 sein und den vollstÃ¤ndigen privat gelesenen und restored Verbund
binden. Lokale Verifikationsdateien sind keine privaten Backupquittungen.
Keine reale Einrichtung, neue externe Berechtigung oder Aktivierung hierdurch.

## Neuer deaktivierter Pflichtfunktionenstand

FÃ¼r getrennte Signal-/Wache-/Lageaktionen und die bestÃ¤tigte Pagesprojektion gilt
[PFLICHTFUNKTIONEN-V2.md](PFLICHTFUNKTIONEN-V2.md). Der frÃ¼here generische v1-Entry
bleibt historische deaktivierte Vorlage und wird nicht installiert. Keine aktive
Workflowdatei wurde fÃ¼r diese lokale Implementierung geÃ¤ndert.
