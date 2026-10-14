# Deaktivierter Hostedabschluss, 14.10.2026

Code: `btc-signal-app`; keine lokale Dauerinstallation. Die sieben Vorlagen
bleiben außerhalb `.github/workflows`, jeder Job enthält `if: ${{ false }}`.
`hosted-backup-runtime.disabled.json` enthält ausschließlich Vorschlagsnamen,
`enabled=false`, keine erfundenen Repository-IDs, Rechte oder Secretwerte.

## Ausführbare Wege

`python3 tools/p4_hosted_backup.py producer` beziehungsweise `verifier` liest
die nicht geheime, kanonisch gehashte Runtime aus `BTC_HOSTED_RUNTIME_JSON`.
`BTC_HOSTED_RUNTIME_SHA256` muss deren Digest ohne das Feld `runtime_sha256`
sein. Beide Jobs prüfen sauberen Checkout, exakten Codepin, Python 3.12.14,
Linux-Runner, tatsächliche Actions-Metadaten, Repository-ID, Workflowpfad,
Main-Ref, Attempt 1, Run-ID/-Nummer und den ursprünglichen Backuptermin.
`RUNNER_TEMP` erhält ein exklusives neues Verzeichnis pro Ausführung.

Producerrollen: `BTC_HOSTED_SOURCE_READ_TOKEN`, `BTC_HOSTED_BACKUP_WRITE_TOKEN`,
`BTC_HOSTED_RECEIPT_READ_TOKEN`, `BTC_HOSTED_METADATA_READ_TOKEN`.
Verifierrollen: `BTC_HOSTED_SOURCE_READ_TOKEN`, `BTC_HOSTED_BACKUP_READ_TOKEN`,
`BTC_HOSTED_RECEIPT_WRITE_TOKEN`, `BTC_HOSTED_METADATA_READ_TOKEN`.
Vier unterschiedliche Werte sind zwingend. Gegenseitige Writerinjektionen
werden abgewiesen. Source-/Backupreader des Verifiers separat vom Producer
bereitstellen; Workflow-Environment/Secretzugriff später ebenfalls trennen.

Vor Facharbeit werden tatsächliche private Repository-IDs und effektive
`permissions.pull/push/admin/maintain` gelesen. Source/Migration ausschließlich
read; Backupwriter ausschließlich Backup; Receiptwriter ausschließlich
Quittung. Gegen alle drei Ziele werden zusätzliche Schreibrechte abgewiesen.
Nur ein explizites HTTP404 darf den negativen Zugriffstest erfüllen;
Timeout, 401/403 und andere Fehler sind kein Rechtebeweis. Unvollständige
Permissionantworten auf lesbaren Zielen führen zum Abbruch.

Der Producer liest beide aktuellen Source-Refs und pinnt sie vor dem Transfer.
`pins=null` bedeutet einen jeweils neu aufgenommenen Schnitt, keinen ungesteuerten
Checkout. Optional vollständige `pins` verlangen exakt diesen Schnitt.
Git Smart HTTP v0 fordert ausschließlich den betreffenden Pin ohne shallow,
haves, Filter, Tags oder weitere Refs. Gepinnte vollständige Packs werden mit
`index-pack --strict` importiert, dann fsck und die vorhandenen vollständigen
Stream-/Fence-/Migrations-/Paarprüfungen ausgeführt. Die Migration kommt als
vollständiger, explizit gepinnter GitDB-Baum mit Dateiblob-/Byteinventar vom
Quellenleser. Historische Nachrichten, Quittungen, Commands und Fencecursors
bleiben Paketbestandteil. Open/sending/uncertain dürfen gesichert werden;
Restore bleibt blocked, das ergibt keine Betriebsgesundheit.

Vorhandene vollständige Pakete werden frisch vom Backupziel geladen und
vollständig rückgeprüft. Neue Inkremente erweitern dieselben Paketpfade.
`pair-manifest.json` ist nur der aktuelle Zeiger. Zusätzlich wird jeder genaue
Manifeststand unter `manifests/<digest>.json` erhalten. Paketpfade sind
unveränderlich; eine abweichende vorhandene Datei wird abgewiesen.
Das endgültige Paarmanifest bindet die ursprüngliche Backupoccurrence und
den tatsächlichen Producerlauf. Alte Paketbytes können damit keinen neuen
täglichen Quittungstermin vortäuschen.

Veröffentlicht werden GitDB-Blobs, ein vollständiger Tree auf dem alten
`base_tree`, ein Commit mit genau diesem Parent und **ein** `force:false`
Refupdate. Kein Bootstrap, Reset, Forcepush oder Branchneuanlegen im Job.
Zunächst müssen eingerichtete Branches mit gültigem leerem Gitbaum existieren.
Parallelpublikationen erzeugen Geschwistercommits; der zweite Refupdate ist
nicht fast-forward und muss scheitern. Bei verlorener PATCH-Antwort darf ein
einmaliger Reconciliation-GET ausschließlich den vorgeschlagenen Commit
bestätigen; ein Nachfolger genügt nicht. Keine zweite Mutation. Verlorene
Blob-/Tree-/Commitantwort beendet den Lauf vor Refupdate. Lose Objekte sind
keine bestätigte Sicherung. Vor dem lokalen Uploadbeleg werden Commitparent,
Tree-ID, vollständige Dateiliste, alle Blob-IDs und alle Paketbytes vom Ziel
zurückgelesen; Source- und Zielbewegung verweigern den Beleg.

Der Verifier nimmt einen eigenen Backupzielpin, lädt alle benötigten Pakete
und Migration ausschließlich aus diesem Ziel und führt den vollständigen
Zwei-Historien-Restore in ein neues blocked-Verzeichnis aus. Zusätzlich prüft
er die Pins gegen authentifizierte Quellhistorie, unveränderte beobachtete
Source-Refs und den tatsächlich erfolgreichen gepinnten Producerlauf desselben
Termins. Ein zwischenzeitlicher regulärer Sourcefortschritt ist erlaubt, falls
der gesicherte Pin sein Vorfahr ist; Bewegung innerhalb des Verifierchecks
ist verboten. Er schreibt nur das geschützte Quittungsziel und liest die
veröffentlichte Quittung mit sämtlichen erhaltenen Zielblobs exakt zurück.
`receipt.json` zeigt auf den neuesten Termin; `receipts/<digest>.json` bleibt
unveränderlich. Gleicher/älterer Quittungstermin wird abgewiesen.

Der Frischechecker versteht `backup_target.manifest_prefix="manifests/"` und
prüft den dazu gehörenden digestgebundenen Manifestpfad aus der echten
veröffentlichten Quittung. Lokale Producerdateien und Actionsartefakte sind
kein Ersatz für diese beiden Zielreads.

## Fester Produktionscode bei wechselnden Legacycommits

Checkout verwendet `BTC_PRODUCTION_CODE_SHA` beziehungsweise
`BTC_HOSTED_CODE_SHA`, nicht den wechselnden Actionsentry-HEAD. Runtime,
Fence und Stream behalten den festen Codepin. `entry_workflows` bindet jeden
zugelassenen YAML-Pfad bytegenau per SHA256. Für einen neueren Main-Entry
werden dessen authentifizierte Workflowbytes und die Abstammung vom festen
Codepin geprüft. Andere Workflowbytes oder fremde Historie scheitern vor
Facharbeit. Monitor verifiziert diese Bindung ebenfalls und vergleicht Jobs
mit ihrem tatsächlichen Entry-HEAD; fachliche Completion bleibt an Produktionscode
gebunden. Alte Konfigurationen ohne Workflowhash akzeptieren weiterhin nur
exakt identischen Entry-/Code-HEAD. Kein stilles Entpinnen.

Die Vorlagen legen Python explizit mit setup-python auf 3.12.14 fest.
Checkout/setup-python/configure-pages/upload-pages sind mit konkreten
Commitreferenzen, deploy-pages mit der konkreten Releaseversion v4.0.5 gebunden.
**Diese Actionreferenzen wurden offline lokal gelesen, nicht beim Provider
verifiziert.** Vor echter Einrichtung alle Referenzen gegen offizielle
Actionquellen prüfen, deploy-pages zusätzlich auf den bestätigten Commit
festlegen, Workflowdigests danach neu erzeugen und abnehmen. Keine Freigabe
allein aus diesen Versionsangaben.

## Zahlenmäßige neue Grenzen

| Grenze pro Producer/Verifier | Wert |
|---|---:|
| Gesamtdauer gemeinsam mit allen Paar-/Gitprüfungen | 1800s und ursprüngliche 26h-Terminschranke |
| Einzelner HTTP-Request als tatsächliche Wall-Deadline | 15s |
| HTTPoperationen gesamt / davon Mutationen (inkl. read-only upload-pack POST) | 4096 / 2048 |
| Refupdates je Publication | 1; keine Wiederholung |
| Gemeinsame reservierte Request-/Responsebytes | 512MiB |
| RESTantwort / RESTrequest | 28MiB / 28MiB |
| Smart-HTTP-Advertisement / vollständige Packantwort pro Source | 2MiB / 64MiB |
| Git pkt-line / Anzahl | 65524 Bytes / 1048576 |
| Vollständiger aktueller Backup-/Quittungszielbaum | 128MiB, 4096 Dateien |
| Temporärer Gesamtbaum / je Sourceobjektverzeichnis | 1GiB / 128MiB |
| Gitprozesse insgesamt / Prozessbaum | 8192 / 64 Prozesse |
| Python / Gitprozessbaum RSS; einzelne Gitzeit | 256MiB / 192MiB; 120s |
| HTTPworker | einer normal; nach unklarer PATCH höchstens zwei; keine Workerwiederverwendung |

Disküberwachung zählt mit scandir spätestens bei der nächsten Budgetprüfung
nach100ms; Gitwatchdog prüft alle50ms. Das ist eine Abbruchgrenze mit möglichem
Messintervallüberschuss, keine garantierte Dateisystemquota. Auf POSIX hat der
Packimport zusätzlich RLIMIT_FSIZE64MiB je Datei und RLIMIT_AS192MiB je
Prozess, der CLI RLIMIT_AS256MiB. Diese Address-Spacegrenzen können früher
als die bestehenden RSSgrenzen abbrechen. Kein Prozess darf bei einem
Budgetbruch einen bestätigten Beleg erzeugen. Timed-out HTTPworker sind daemon,
führen höchstens den einen bereits gestarteten Request fort; der CLI wartet
nicht unbeschränkt auf DNS/Trickle. Deshalb bleibt jede unbestätigte Mutation
fail-closed; es gibt keinen parallelen zweiten Sendeversuch.

Die bestehenden Paargrenzen bleiben enger, wo zutreffend: Segment256 Commits,
64MiB unpacked,20MiB Paket; gemeinsam512 Segmente/8GiB theoretische Paketmenge,
128KiB Manifest,750KiB Stream,8KiB Fence. Der Hostedtransfer lässt ausdrücklich
nur128MiB Zielbaum/512MiB reservierten Transfer zu; er erweitert diese Grenzen
nicht auf8GiB. Eine neue größere Historie stoppt und erhält die letzte gültige
Sicherung, sie wird niemals abgeschnitten. Retention/Kapazitätswechsel benötigt
eigenes Review und keine automatische Löschung.

Actions640GET/50PUT,900s/ursprüngliche Terminfrist und Monitor64GET/20s bleiben
unverändert. Die zusätzliche Entrybindung von Pages/optionalem Monitor nutzt
einen separaten Code-only Reader mit3GET/0Writes,6MiB reservierten Antworten,
20s Gesamtzeit/3s Sockettimeout. Pages-Storeexport behält12GET/120s/24MiB.
Die Entrybindung im Enginejob belastet denselben bestehenden640GET-Zähler.

## Neue Protokollannahmen und offene Providerbeweise

1. GitHub Smart HTTP v0 liefert den gepinnten Ref und side-band-64k/ofs-delta;
   vollständiger unshallowed Packtransfer ohne haves und ohne Redirect/Proxy.
   GitLFS/Submodule/Sparse/Promisor werden nicht unterstützt und dedicated
   Stream-/Fencebäume erlauben nur die bekannte einzelne JSON-Datei.
2. Authentifizierte GitDB-GETs liefern SHA1-Objektidentitäten, unverfälschte
   Base64bytes und untruncated vollständige Trees. Tree- und Blob-IDs werden
   selbst berechnet. Commit-SHA und Parent/Tree werden unabhängig über den
   authentifizierten immutable GET bestätigt; alte Commitheader werden beim
   Source-Gittransfer vollständig als echte Gitobjekte geprüft.
3. GitDBRefupdate mit force=false ist tatsächlich atomarer Fastforward.
   Es ist keine API-CAS mit expected_sha. Der unveränderte Parent bildet den
   CAS-Ersatz; Geschwister werden abgewiesen. Eine Antwort auf Commitcreation
   ist allein kein Uploadbeleg.
4. Effektive permissions und vollständige Branchprotection sind für die
   injizierten Rollen sichtbar. Protection muss force/deletion=false,
   enforce_admins=true und linear_history=true liefern. Die Einrichtung muss
   zusätzliche Bypassrollen, Tokenreichweite, Writerrestrictions und
   Workflowenvironmenttrennung unabhängig bestätigen. APIpermissions sind
   kein vollständiger kryptographischer Tokenintrospektionsbeweis.
   Unverfügbare oder unvollständige Protectionantwort: Abbruch. Gegebenenfalls
   ausschließlich Administration:read für Protectioneinsicht prüfen, keine
   Administrations-Schreibrechte. Tarif/Rechte heute unbekannt.
5. Die echte Rollen-/Tarif-/APIabnahme und Referenz-/Runtimeversorgung bleiben
   offen. Die synthetischen Fakes belegen Codewege und Grenzen, keinen echten
   GitHubprovider, Branchschutz, Tarif oder Livebetrieb.

## Installierbarer deaktivierter Diff

`python3 tools/p4_install_hosted_templates.py --out <neues-Verzeichnis>`
erzeugt die sieben vorgesehenen `.github/workflows/*.yml`, eine vollständige
`INSTALL-DISABLED.diff` gegen die alten Dateien und `WORKFLOW-SHA256.json`.
Es verändert weder alte Workflows noch site/data. Signal/Wache/Lage/Pages,
Backup/Verifier und optionale Frischeprüfung sind abgebildet. Coinalyze-
Archiv/Test, Tests und Backtest bleiben unverändert. Overlay zuerst allein
reviewen; kein Merge/Push/Dispatch Bestandteil dieses Tools oder Auftrags.

Producer00:00UTC, Verifier00:15UTC sind deaktivierte Vorschlagscronzeiten.
Abhängigkeit wird durch denselben unveränderlichen Termin und realen
Producerabschluss geprüft, keine automatische workflow_dispatch-Nachricht.
Ein langsamer Producer lässt den Verifier scheitern; geplante Start-/Alarm-
Eskalation ist Teil der späteren begrenzten Abnahme, keine automatische
Retrykampagne. Tatsächliche GitHubcronstarts werden nicht als garantiert
behauptet. Externe Deadmanbindung bleibt separat enabled=false.
