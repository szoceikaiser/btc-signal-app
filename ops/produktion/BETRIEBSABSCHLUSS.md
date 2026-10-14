# Lokaler Betriebsabschluss; weiterhin deaktiviert

Vertrag `btc-actions-slots-v1`, separate Sperre `github-actions-fence-v2`.
Keine Livefreigabe, kein neuer Storeseed und keine Änderung bestehender aktiver
Workflows. Alte Live-Sicherung 69e676d8… und abgeschlossene Testgrants bleiben
unberührt. C05 bleibt inaktiv; S006 Vergleich. Ein frischer Stillstandsschnitt
und die vollständige C05-Zielconfig fehlen weiterhin.

## Warteschlange und Terminbindung

Die vier Vorlagen Signal/Wache/Lage/Pages teilen weiterhin
`btc-delivery-single-stream`, jetzt mit `queue: max` und
`cancel-in-progress: false`. Das sind höchstens 100 wartende Jobs, keine
unbegrenzte Warteschlange und keine FIFO-Garantie nach Dispatchzeit. Dauerhafter
gemeinsamer CAS bleibt maßgeblich; kein TTL, Takeover oder Resend. Ein Auftrag,
der nie startet, kann keine Abschlussrevision erzeugen und wird im Frischecheck
als fehlend sichtbar. Abgebrochene/queued/unvollständige neueste oder fällige
Runs bleiben ungesund. Ein externer Monitor muss auch den fehlenden Monitorlauf
selbst überwachen; Actions-Warteschlangen versprechen keine Startfrist.

Der Entry liest genau einmal die tatsächlichen Runmetadaten über GET, mit
separatem Actions:read-Token. Run-ID/Nummer/Attempt/Repo/Pfad/Ref/Code/Event müssen
zur tatsächlichen Runnerumgebung passen. `run_started_at` oder Stepzeit werden
niemals zum neuen Solltermin. Es wird kein `scheduled_at` erfunden.

| Art | feste UTC-Termine | bindende Abschlussfrist |
|---|---|---|
| Signal | 00/04/08/12/16/20 Uhr jeweils :02 UND :32 | Kerzenschluss +45min, also :45 für beide Phasen |
| Wache | jede Stunde :08/:23/:38/:53 | jeweiliger Solltermin +15min |
| Backup | täglich 00:00 UTC, Vorschlag noch zu binden | Solltermin +26h; genau 26h noch gültig |
| Lage | eigener workflow_dispatch, tatsächliches created_at | created_at +15min; kein Signal-/Wache-Ersatz |

Signal behält ausdrücklich die bisherige close_offset-Regel: :02 hat 43min,
:32 hat 13min bis :45. Die bisherige allgemeine p3-Frischefixture ließ Wache
45min zu; der neue Kandidatenchecker setzt die geforderten 15min durch und
ändert die alte Fixture nicht. Sobald eine Frist erreicht ist, muss deren
Abschluss vorliegen. Beide Signalphasen sind eigenständige Verpflichtungen.
Wartezeit verbraucht das vorhandene Zeitfenster; die Runrequestdeadline wird
zusätzlich auf die ursprüngliche Abschlussfrist begrenzt, höchstens 15min Lauf.

`run-name: btc-v2:<kind>:<expected_start_ms oder created>` macht die Bindung im
belegten Run sichtbar. Optionales `expected_start_ms` ist ein ursprünglicher
UTC-Solltermin in **Millisekunden**. Ohne Input wird der letzte feste Slot aus
dem belegten `created_at` abgeleitet. Das ist bedienbar für einen Hand-/externen
Start im gültigen Fenster, beweist aber keinen ursprünglichen GitHub-Crontermin.
Außerhalb der Frist wird der Aufruf lesend abgewiesen; er eröffnet keinen Fence.
Für jederzeitige Auskunft dient Lage. Verlorene Ursprungsverpflichtungen werden
dadurch nicht erfüllt: z.B. ein erst :33 erzeugter Run kann niemals den fälligen
:02-Abschluss ersetzen. Der unabhängige Checker verlangt beide Phasen.

Konkreter externer Dispatchvorschlag (nur Text, keine echte Umstellung):

```json
{"ref":"main","inputs":{"expected_start_ms":"<ursprünglicher fester UTC-Solltermin als Dezimal-Millisekunden>"}}
```

Der externe Scheduler muss den Solltermin beim Erzeugen des Auftrags festhalten
und bei Verzögerung unverändert lassen. Ein pauschales `%cjo:unixtime%` liefert
Sekunden und möglicherweise die tatsächliche Auslösezeit; es ersetzt diese
Millisekunden-/Phasenbindung nicht ohne geprüfte Transformation. Die echte
cron-job.org-Konfiguration und ihr tatsächliches Verhalten sind weiterhin offen.

## Vollständige Zwei-Historien-Sicherung

`tools/p4_backup_pair.py append --plan plan.json` verarbeitet ausschließlich
bereitgestellte lokale Gitquellen. `plan.json` ist kanonisches JSON mit LF und
abschließendem Newline; ein vollständiges synthetisches Beispiel liegt im Beleg.
Erforderlich sind `stream_source`, `fence_source`, `identity`, `migration`,
`deployment`, `out` sowie unabhängige `pins` für beide Commitstände. Stream:
Commit/Blob/Revision/Snapshotdigest; Fence: Commit/Blob/Revision/Bodydigest.
Fence-Revision ist der nullbasierte Commitordinal seit dem vollständigen Seed,
keine erfundene Revision im Fenceschema. Repo/Branch/Store/Stream/Code/Config/
Bot/Review und Terminvertrag sind zusätzlich gemeinsam gebunden.

Die unveränderte Streambasis `p3_backup_chain` bleibt zuständig für ihre eigenen
Pakete. Ein optional geteilter Budgetzähler ist die einzige Erweiterung dort.
Separater Fencepfad und separate Gitfolge prüfen jeden Commit, genau einen
Elterncommit, erlaubte Zustandsübergänge und sämtliche Cursors. Closed-Verweise
müssen echte Commit-/Blob-/Revision-/Digeststände der gesicherten Streamfolge
belegen. Fremde/fehlende/umgeordnete Inkremente oder bewegte Quellbranches
erzeugen keine abgeschlossene Paarquittung. Vorhandene Pakete werden nie
überschrieben. Normale Aufrufe geben nur ihren eigenen vorübergehenden Owner
frei; ein harter Prozessverlust lässt den Owner für ausdrückliche Prüfung stehen.

Paarmanifest und vollständiges Dateiinventar binden beide Paketketten. Es wird
immer ausschließlich aus Paketen in einen frischen Zielpfad restored. Beide
Gitfolgen werden vollständig geprüft und fsck ausgeführt. Originale Versand-
quittungen, Commands und Fencebytes bleiben in den Gitfolgen erhalten.
Der zusätzliche lokale Betriebsstore bleibt blocked, verlangt Abstimmung und
hat leere Erfolgsindizes. `sending` wird dort zu `uncertain`; das originale
`sending` bleibt bytegleich in der gesicherten Historie. Originalfence wird
zusätzlich separat bytegleich abgelegt und niemals als aktive Sperre installiert.

```text
python3 tools/p4_backup_pair.py restore --root <Paarpakete> --manifest <Paarmanifest.json> --required-pins <unabhängig-geprüfte-Pins.json> --target <neuer-leerer-Zielpfad>
```

`verify-readback --plan <plan.json>` ist der getrennte Prüfpfad: eine zuvor
authentifiziert bereitgestellte lokale Spiegelung des privaten Backupziels
muss auf dem unabhängigen Commitpin stehen. Ihr dedizierter Branchbaum enthält
genau `pair-manifest.json` und alle Inventardateien. Jedes Gitblob wird gegen
Größe/Hash geprüft; anschließend werden die bereitgestellten Paketbytes erneut
vollständig frisch und blocked restored. Zielpin und Quellpakete werden danach
erneut geprüft. Der tatsächliche Verifier-Entry/Code/Attempt muss zur gebundenen
Runnerumgebung passen. Ausgabe ist eine neue lokale
`p4-independent-backup-receipt-v1`-Quittung. Nur der separat berechtigte Verifier
darf diese später auf dem geschützten Quittungsbranch veröffentlichen.

Die Authentizität der bereitgestellten Spiegelung benötigt einen später
eingerichteten, geprüften Provider-Lesepfad. Ein lokaler Repositoryname oder ein
boolesches Feld allein beweist keinen echten Upload. Hier sind alle Belege
synthetisch und auf demselben Rechner; keine externe Sicherung behauptet.

## Ausführbarer lesender Monitor

```text
python3 tools/produktion_actions_freshness.py --policy <geprüfte-monitor-policy.json>
```

Exit 0 mit HTTP-Entscheidung 200 nur bei vollständigem Befund; sonst Exit 20 und
503. Das CLI öffnet keinen HTTP-Port. Ein externer lesender Adapter muss später
Exit/JSON samt eigenem Deadman übernehmen. `monitor-runtime.disabled.json`
liefert ausschließlich eine deaktivierte Vorlage mit offenen echten Pins.

Der Monitor prüft Runlisten ohne Erfolgsfilter, fällige plus neueste Run-/Job-
Abschlüsse, exakte historische Completionrevisionen, aktuelle gemeinsame Sperre
und deren exakten Streamabschluss. GET-Doppellesung von Runs, Stream, Fence,
Prüfquittung und Backupbranch verweigert Bewegung. Backupquittung muss beide
vollständigen Ketten/Inventar/blocked-Restore, authentische Zielmanifestbytes und
einen erfolgreichen separat gebundenen Verifier-Run belegen. Beide Sourcepins
müssen echte Vorfahren der aktuellen autoritativen Historien sein.

Der Monitor führt absichtlich nicht bei jedem 5min-Check einen 8GiB-Restore aus.
Er vertraut dafür ausschließlich der getrennt geschützten Verifierquittung
und prüft deren echten Run sowie das immutable hochgeladene Manifest erneut.
Dieser Verifier darf weder der Producer noch der normale Sendetoken sein.
Fehlende Rechte, gefälschte lokale Fixtureflags oder reine Pages-HTTP200 ersetzen
diesen Vertrauensanker nicht. Ein kompromittierter geschützter Verifier bleibt
eine explizite Betriebsabhängigkeit; GET-Beobachtungen sind keine atomare
Transaktion über mehrere Repositories.

## Harte Budgets

| Pfad | GET / PUT | Zeit | Bytes und sonstige Grenzen |
|---|---|---|---|
| Actions incl. tatsächlichem Metadata-GET | 640 / 50 pro Run, unverändert | Request 15s, Run höchstens 900s UND ursprüngliche Terminfrist | Antwort 2MiB; Request 1.126.400; Run Request 62.914.560, reservierte Response 1.447.034.880 Bytes; CAS weiterhin max11GET/1PUT/3 Zyklen |
| Neuer Monitor, drei getrennte Tokens, ein Zähler | 64 / 0, keine Retries | Request max3s, zusammen20s; Redirect/Proxy abgewiesen | 2MiB pro Antwort, maximal134.217.728 reservierte Bytes; höchstens100 Runs pro Liste (100 oder unvollständige Pagination wird abgewiesen),20 Jobs pro ausgewähltem Run, Policy/Receipt128KiB |
| Paarappend/Restore/readback | 0 Netzrequests / 0 | gemeinsam1800s, je Git-Prozess120s | Python256MiB RSS, Gitprozessbaum192MiB,256 Commits/64MiB unpacked je Segment,20MiB Paket; beide Historien zusammen max512 Segmente/8GiB Paketbytes; Paarmanifest128KiB; Fence8KiB; Stream750KiB |

Der neue Monitor hat ausdrücklich 64 statt der früheren p3-32-GET-Obergrenze:
zusätzliche Fence-, Zweithistorien-, unabhängige Verifier-/Ziel- und abschließende
Bewegungsbelege benötigen zusätzliche Reads. Die 20s-Gesamtfrist bleibt gleich;
bei Ausschöpfung entsteht niemals gesund. Actions-, Pages- und sämtliche
p3_backup_chain-Grenzen wurden nicht erhöht. Fencepakete nutzen dieselben
Git-/RSS-/Bytegrenzen; ein geteilter Zähler verhindert doppelte 1800s-Budgets.

## Konkrete spätere Bindungen — keine Erstellung

Alle folgenden Namen sind **Vorschläge**, keine existierenden IDs oder Werte.
Code bleibt `szoceikaiser/btc-signal-app`, `refs/heads/main`, exakter neu geprüfter
Codepin. `btc-p3-store-probe` bleibt abgeschlossen und wird nicht verwendet.

| Zweck | vorgeschlagenes privates Ziel / Branches | engste Rollen und Variablen |
|---|---|---|
| Autoritativer Store | `szoceikaiser/btc-delivery-store`, `delivery-stream-v2` und `delivery-fence-v2` | Sendetoken nur dort Contents:write; keine PR-/Actions-/Adminrechte. `BTC_REVIEWED_STORE_REPOSITORY`, `BTC_REVIEWED_STORE_BRANCH`, `BTC_REVIEWED_FENCE_BRANCH`, `BTC_REVIEWED_STORE_ID`, `BTC_REVIEWED_BOT_IDENTITY`, `BTC_REVIEWED_RUNTIME_JSON`, `BTC_REVIEWED_CONFIG_JSON`, Secret `BTC_REVIEWED_STORE_TOKEN`. GitHub-Token des Codejobs nur Contents:read + Actions:read für Metadata. |
| Vollständige Zweitsicherung | `szoceikaiser/btc-delivery-backup`, `verified-pair-packages` | eigener Producer Contents:write nur dort; Source-Reader Contents:read nur Store, plus geprüfte immutable Migration. Keine Forcepush-/Löschrechte; geschützte Historie/Retention einzurichten. `BTC_BACKUP_SOURCE_PLAN_PATH`, `BTC_BACKUP_VERIFIER_CODE_SHA`; Upload-/Downloadadapter und dessen tatsächliche Commit-/Blobquittung offen. |
| Unabhängige Prüfung und Quittung | `szoceikaiser/btc-delivery-backup-verification`, `verified-receipts`; Codeworkflow `.github/workflows/backup-verify.yml` | separater Verifier liest Backup Contents:read, schreibt ausschließlich Quittungsziel Contents:write; Producer und Sendetoken dürfen hier nicht schreiben. Geschützter Schreibpfad/Review, exakter Verifier-Codepin und Workflow-/Runbindung einzurichten. `BTC_BACKUP_READBACK_PLAN_PATH`; authentifizierte Readbackbereitstellung und Quittungspublisher offen. |
| Frischemonitor | eigener externer Ausführungs-/Alarmanbieter, optional zusätzlich Actions | Secrets `BTC_MONITOR_STORE_READ_TOKEN` (Store Contents:read), `BTC_MONITOR_ACTIONS_READ_TOKEN` (Code/Verifier Actions:read), `BTC_MONITOR_BACKUP_READ_TOKEN` (Backup/Quittungsziel Contents:read); `BTC_MONITOR_POLICY_JSON`, `BTC_MONITOR_CODE_SHA`; niemals PUT/Telegram-/Recoveryberechtigung. |

Für die beiden lokalen Backupvorlagen werden getrennte self-hosted Labels
`btc-backup-staging` / `btc-independent-backup-verifier` vorgeschlagen. Sie
verarbeiten nur zuvor begrenzt und authentifiziert bereitgestellte Quellen;
sie enthalten absichtlich keinen ungeprüften `fetch --all` oder Publisher.
Quellenbereitstellung, geschützter Upload, unabhängiges Readback und Veröffentlichung
der Prüferquittung müssen als konkrete Providerbindungen vor Aktivierung ergänzt
und abgenommen werden. Ein grüner lokaler Producerjob reicht niemals für Monitor200.

Zusätzlich offen: tatsächliche Repository-/Branchschutzrechte und IDs, Bot-/
Zielbindung ohne Secretwerte, heutige Workflow-Startcursor, erste verpflichtende
UTC-Slots, Backup-00:00-Termin, Empfänger/Zuständiger/Eskalationszeiten und externer
Alarmtransport. Vorschlag: externer Check alle5min, Alarm bei503 oder fehlender
Checkausführung nach10min, Rückkehrmeldung nur nach vollständigem200; dieses
zusätzliche Beobachtungsintervall ist zu den fachlichen Fristen zu addieren,
keine Fristverlängerung im Checker. Tatsächlicher Alarmweg bleibt enabled=false.
Ein Monitor im selben GitHub-Anbieter erkennt dessen Gesamtausfall nicht unabhängig.

Keine Löschung/Stilllegung alter Workflows, Runs, Logs, Artefakte oder Branches.
Vor jeder späteren Actionsbereinigung: konkreten Namen, frühere Aufgabe,
Abhängigkeiten und Folgen erläutern und Nutzer fragen. Keine Freigabe hieraus.

## Fortschreibung Hostedbackup
Die früheren lokalen Staging-/Selfhostedannahmen sind durch die ausführbaren, weiterhin deaktivierten Hostedpfade ersetzt. Aktueller Vertrag: HOSTED-BACKUP.md; begrenzter Einrichtungsablauf: HOSTED-EINRICHTUNGSABNAHME.md. Alte Auditbelege bleiben unverändert erhalten. Keine Provider-/Liveabnahme hieraus.
