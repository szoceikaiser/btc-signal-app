# Fünf getrennte externe P3-Probenpläne

08.10.2026. **Reviewbare Vorbereitung, null externe Ausführung.** Jede Aktion
braucht einen eigenen konkreten Auftrag des Hauptchats nach lokaler Prüfung.
Namen, Branches, Pfade, Hosts und Rechte unten sind Vorschläge/Platzhalter. Es
wurde kein privates Konto durchsucht, Credential gelesen oder Dienst eingerichtet.
Die alte Engine-CI an `4ea6bb3` gilt nicht für den neuen P3-Stand.

## 1. Privater synthetischer Teststore

Fehlende Angaben: `<OWNER>/<PRIVATE_TEST_REPO>`, Repository-ID, Testbranch
`<TEST_BRANCH>`, Credentialinhaber, Ablaufzeit und begrenzte Freigabe. Möglicher
Name: `btc-p3-store-probe`; **nicht ausgewählt**. Datei als Vorschlag
`delivery/stream.json`. Ausschließlich feste synthetische Store-/Stream-/Zielwerte.

Vor Schreiben: `GET /repos/{owner}/{repo}` (private=true, richtige ID),
`GET /repos/{owner}/{repo}/actions/permissions` (enabled=false), Branchregeln und
effektive Rechte prüfen. Pages aus. Ein getrenntes kurzlebiges Testcredential
erhält nur Contents:write für dieses Repo, Metadaten:read; keine Actions-/PR-/
Workflow-/Administrationsrechte für den Probeclient. Ein Repo-Credential ist
keine Pfadgrenze. Die verbleibende Möglichkeit, andere Dateien/Branches im
Testrepo zu schreiben, muss ausdrücklich im Freigabetext stehen. Settings werden
vom Nutzer oder einem gesondert erlaubten Administrationsweg gesetzt und belegt.
Keine Schreibprobe auf fremden Repositories als Berechtigungstest.

Der reale Client ist in diesem Auftrag nicht freigeschaltet. Die fertige lokale
Hülle `p3_store_probe.py --offline --out NEUE_DATEI` hat nur FakeAPI und keine
Token-/Repooption. Sie zeigt blocked-Seed, getrennten synthetischen Aktivübergang,
zwei Run-ID/Attempt/Nonce, Gewinner/Verlierer, Intent, sending, Fixturequittung,
bestätigtes Unlock, zweite Übernahme, Parent/Readback und Writebudget.

Nach separater Freigabe ist der konkrete Ablauf:

| Schritt | Exakte Aktion / Stop |
| --- | --- |
| Seed | Einmalige ausdrückliche Repositoryinitialisierung mit **blocked** synthetischem Seed auf der gewählten Testbranch. Contents-Create ohne SHA nur hier im Bootstrap; Laufzeitadapter kann nie bootstrappen. Fehlt die Branch, nicht stillschweigend default/main benutzen. |
| Blocked-Gate | Konsistentes Lesen via Ref → Contents an Commit → Ref. Runtimeclaim muss vor jedem PUT scheitern. Seedbytes und Quellhash erhalten. |
| Testaktivierung | Separater genehmigter ausschließlich synthetischer CAS-PUT: mode active, Revision+1, parent_digest, neuer write_id, Digest. Ein normaler Prozessstart aktiviert nichts. Readback, Blob-SHA, Commitparent und Branchkopf exakt prüfen. |
| Zwei Schreiber | Run A/Attempt1/NonceA und Run B/Attempt2/NonceB lesen denselben Start. Ein Owner gewinnt. B stoppt ohne Intent/Transport; bei tatsächlich veralteten Reads CAS-Konflikt, kein Retry. Beide Identitäten protokollieren. |
| Gewinner | Claim → Intent → sending → bedeutungslose Fixturequittung → Freigabe. Jeder PUT mit vorheriger Blob-SHA und expliziter Branch. Jeder Write wird über Ref/Contents/Ref und Commitparent bestätigt, bevor der nächste Schritt erfolgt. Null Transport. |
| Runbindung | Separater synthetischer Signal-/Watch-Abschluss mit Start, Kandidat, bestätigtem Abschlusslocator und bestätigter Attestation; Monitor prüft konkrete Run-ID/Attempt, Termin, Code/Config und Vorfahrbindung. Keine echte Marktabfrage. |
| Verlorene Antwort | Ein lokaler Wrapper verwirft gezielt die Antwort vor/nach einer realen **synthetischen Storemutation**, nie eine echte Nachricht. Nur exaktes Readback mit eigenem write_id und Parent bestätigt dem noch laufenden Prozess Erfolg. Andernfalls Halt/Owner erhalten, kein Blind-Retry. |
| Runende | Probeprozess beenden, keine anderen Worker und pausierte Trigger belegen. Kein Ownerablauf. Takeover nur bei exakter Owner-/Revision und positiv belegtem Runende. Überlebendes sending wird uncertain; neue IDs und Auswertung bleiben gesperrt. |
| Negative Rechte | Falsch gebundene lokale Eingaben müssen vor Write stoppen. 403/429/Timeout sind lokal vorhanden; eine reale 403-/Rate-Limit-Probe nur separat erlauben, nicht durch absichtliches Fluten. Nie Rate-Limits provozieren. |

Begrenzter Freigabevorschlag: maximal **48 PUT-Versuche insgesamt**, maximal acht
benannte Test-Run-Identitäten, je höchstens zwölf PUTs; zusätzlich **384 GETs**,
keine DELETE/PATCH/Force-/History-Rewrites. Zwei Bootstrap-/Aktivierungsmutationen
zählen mit. 768.000 unkodierte Bytes je Storebody, maximal 2 MiB API-Antwort,
maximal 15 Sekunden je Store-Request. Kein länger laufender Collector. Bei jeder
Abweichung sofort anhalten; ungeklärte Fälle erhalten ihre Branch/Owner/History.
Keine Aufräumaktion durch Reset. Aufbewahrung des Testrepos separat entscheiden.
Ein eventuelles neues Testsetup nach blockierendem Gegenfall braucht einen
anderen vorab benannten Teststream; dies ist kein Produktionsrecovery.

Protokoll: UTC, Requesttyp/Statusklasse, Ziel-ID/Branch/Pfad, alter Blob, Write-ID,
erwartete/gelesene Revision, Commitparent/-SHA, Bytes, kumulierte Requests,
Run-ID/Attempt/Nonce und Ergebnis. Keine Tokens, privaten Texte oder Mailbodies.
Kleine synthetische Fixtures sind **keine aktuelle Produktionsgrößenmessung**.

## 2. Spätere produktive Storeeinrichtung – weiterhin blocked

Fehlend: `<OWNER>/<PRIVATE_PRODUCTION_STORE_REPO>`, tatsächliche Branch,
Repository-ID, Store-/Stream-/Bot-/Zielidentität und begrenzte Rechte. Möglicher
Name `btc-delivery-state`, nicht gewählt. Actions und Pages dort aus; Repo privat.
Code bleibt im bestehenden Code-Repo. Betriebsschreiber Contents:write nur auf
diesem Store; Monitor Contents:read. Kein Token in URL, JSON, Git oder CI-Output.

Vor Produktionsbootstrap sind frischer stillgelegter Snapshot, Quellenmanifest,
volle Historie, exakter Code-/Konfigurationspin und konkrete D2-Entscheidungen
nötig. Das ist die spätere P4-Grenze und wird hier nicht durch alte Fixtures
ersetzt. Die aktuelle vollständige Zustandsgröße und Requestzahl müssen vor
Freigabe gemessen werden, einschließlich Migration, Outbox und Healthindex.
80%-Grenze erzeugt Warnung, harte Grenze Halt; keine Historienkürzung zur Passung.

Danach höchstens ein ausdrücklicher Bootstrap-Create des validierten **blocked**
Seeds auf der bestätigten Branch; vor/nach Ref/Parent/Digest/Bytes prüfen und
Manifest sichern. Keine Runtime-Provisionierung, Aktivierung oder Position-
migration aus dieser Zustimmung ableiten. Actions-Anbindung, alte Trigger,
Workflowinputs und alle `workflow_run`-Wege werden erst in einem eigenen P4-Diff
geprüft. C05/S006 bleiben inaktiv; Modellrenditen sind historische Modellwerte.

## 3. Dynamischer read-only Prüfpunkt

Fehlend: benannter vorhandener/gesondert erlaubter dynamischer Host, Betreiber,
TLS-URL `<MONITOR_URL>`, Zugriffsschutz und sichere Credentialbereitstellung.
Kein Host, Tarif oder Kauf ist gewählt. Der Windows-PC ist nicht als 24/7-Host
abgenommen. cron-job.org bleibt der einzige Alarm-/Schedulerdienst.

Der Endpoint ruft `freshness.check_github` mit folgenden getrennten GET-Lesern
auf: maßgeblicher Store (Contents:read), Code-Repo (Actions:read), Backuprepo
(Contents:read). **Alle drei ReadOnlyClients teilen einen ReadBudget**. Der
Monitor hat weder Actions:write noch Contents:write. Endpointauth liegt in einem
Header; keine Tokens in URL/Antwort. Keine privaten Storebytes im Hostlog.

Feste gepinnte Policy nennt tatsächlichen Codebranch/-SHA, Workflowpfade,
Store-/Stream-/Configidentität, Perioden/Phasen und erste erwartete UTC-Termine.
Null/fehlende Werte sind Fehler. Backup-Quittungspfad als Vorschlag
`backup/latest-receipt.json`; `read_backup` bindet Manifestdigest, Quellrepo/-pin,
Revision, volle-Historie-/blocked-Restorebeleg. Der Quellpin muss Vorfahr des
aktuellen maßgeblichen Stores sein und an dieser SHA den richtigen Digest und
die richtige Revision liefern. Volle Pakete werden beim Backup geprüft;
der Monitor lädt sie nicht alle fünf Minuten erneut herunter.

Healthy: echter HTTP200. Jeder semantische Fehler, APIausfall, Budget-/Timeout,
unlesbare Identität, alte/falsche Revision oder blocked/uncertain: **HTTP503**.
`Cache-Control: no-store`, keine statische Pages-/Cacheantwort, keine eigene
Sperrübernahme. Hostbudget: 32 GETs, 2 MiB je Antwort, drei Sekunden Requestlimit,
20 Sekunden Gesamtlimit; maximale HTTP-Antwort 1 KiB. Reverseproxy/Runtime müssen
auch vor Erreichen des Python-Codes bei Timeout einen Fehler zurückgeben.

Separater geschützter Testendpoint benutzt nur gespeicherte synthetische
Fixtures. Je eine 200-Probe, fehlender Signalstart, fehlender Watchstart trotz
späterem Erfolg, neuer fehlgeschlagener Run, falscher Attempt, alter Abschluss,
falscher Code/Config/Store, branchbewegter Read, API403/429, sending/uncertain,
fehlendes/überaltes Backup und >15-Minuten-Lauf ergeben503. Keine query-Parameter,
die den produktiven Endpoint auf eine Fakegesundheit umschalten könnten.

Die lokale Runbindung hat einen geprüften Dispatchvertrag: cron-job.org kann
`%cjo:unixtime%` in einem Body substituieren. Spätere Dispatchinputs als Vorschlag:
`{"ref":"<CODE_BRANCH>","inputs":{"kind":"signal","dispatch_epoch_seconds":"%cjo:unixtime%"}}`.
Der deaktivierte Workflowentwurf nutzt den Titel `p3:<kind>:<dispatch_epoch_seconds>`;
`p3_run_binding.prepare` prüft tatsächliche Runmetadaten und bestimmt denselben
Terminslot wie der Monitor. Kein Shellinterpolieren der Inputs. Dispatchs außerhalb
der ersten zwei Minuten nach dem gepinnten Starttermin scheitern ausdrücklich.
Bestehende cron-Aufträge und aktive Workflows werden in diesem Auftrag nicht geändert.

## 4. cron-job.org-End-to-End-Alarm und Wiederherstellung

Bereits entschieden: ausschließlich cron-job.org, persönliche Reaktion durch
den Nutzer, `szocei.kaiser@gmail.com`. Noch zu belegen: verifizierter E-Mail-Kanal,
Channel-ID, tatsächliche Signal-/Watch-Jobs und UTC-Pläne, Monitorjob, Timeout,
höchste akzeptierte Erkennungszeit und persönliche Reaktionsfrist. Die 45-/15-/
26h-Werte sind bisher Vertragsziele, keine bereits abgenommene SLA.

Nach eigenem Auftrag separaten Monitorjob mit `<MONITOR_URL>`, GET, Headerauth,
UTC alle fünf Minuten und höchstens30 Sekunden HTTP-Timeout einrichten.
Vorschlag: `onFailure=true`, `onFailureCount=1`, `onDisable=true`, `onSuccess=true`
für Wiederherstellung; ausgewählter verifizierter E-Mail-Kanal. `saveResponses=false`,
keine Header-/Tokenexporte. Bestehender Dispatchjob bleibt zunächst unverändert;
204 beweist nur Annahme. Seine eigene Fehler-/Deaktivierungsbenachrichtigung
später separat lesen und prüfen.

Probe ausschließlich am synthetischen Testendpoint, kein Produktionsdispatch:

1. 200-Ausgangsstand und cron-Run erfolgreich belegen.
2. Fehlenden Signalstart simulieren, 503, cron-Fehler und tatsächlichen Eingang
   an der gewählten Adresse mit UTC-Zeiten belegen.
3. Dasselbe für Watch, auch wenn ein späterer Watch erfolgreich ist.
4. Lauf-/API-/Store-/Backupfehler und nicht erreichbaren Endpoint jeweils prüfen.
5. Auf200 zurückkehren; Wiederherstellungs-E-Mail, Zeit und persönliche Kenntnisnahme
   protokollieren. Eine 200-Wiederherstellung entsperrt keine Zustellung.
6. Kontrollierte automatische Deaktivierungsprobe nur an einem getrennten
   Testauftrag; Alarm und anschließende kontrollierte Wiederherstellung belegen.

Je Probe maximal fünf Monitoraufrufe (bei fünf Minuten Takt höchstens25 Minuten),
höchstens zwei erwartete Statuswechsel-Mails (Fehler/Wiederherstellung); bei
unerwartetem Versand oder fehlendem Eingang abbrechen und Testjob deaktivieren,
keinen Versandsturm erzeugen. Geplante Zeit, tatsächlicher Dispatch, GitHub-
Erstellung, Abschluss/Storebestätigung, Erkennung, Eingang und Reaktion getrennt
erfassen. `%cjo:unixtime%` ist die Ausführungszeit; cron-`datePlanned` und Jitter
separat belegen. Das über cron-job.org gemeinsame Ausfallrisiko bleibt sichtbar;
eine nicht ausgeführte Monitorprüfung kann sich nicht selbst alarmieren.

## 5. Zweites privates GitHub-Backup und isolierter blocked-Restore

Fehlend: `<OWNER>/<PRIVATE_BACKUP_REPO>`, Repository-ID, Branch, Custodian und
getrennte repo-begrenzte Rechte, UTC-Backuptermin, Aufbewahrung und Restoreintervall.
Möglicher Name `btc-delivery-backup`, nicht ausgewählt. Privat, Actions und Pages
aus. Dieses Repo ist weder Teststore noch zweite aktive Zustandsautorität.
Vorschlag täglich und vor Änderungen; mindestens sieben Tages- und vier
Wochensätze, keine automatische Löschung; Restore vor Updates und monatlich.

Aus ausdrücklich erlaubtem nur lesendem lokalem Storeclone eine einzelne
bestätigte Branch-SHA pinnen. Vollständige Historie ab blocked-Seed und aktuelle
Datei an dieser SHA, Store-/Streamidentität, Revision/Digest, Code-/Configpin,
Migrationspaket und Datei-SHA256 erhalten. `p3_backup_chain.append_local` prüft
unabhängig verlangten Pin **und Revision**, Identität und gesamte lineare
Commit-/Digestfolge. Es macht **kein fetch/push**. Maßgeblich ist jetzt
[P3-BACKUP-V2-VERTRAG.md](P3-BACKUP-V2-VERTRAG.md): immutable Basis plus verkettete
Inkremente, je höchstens256 Commits,64 MiB unkomprimierte Storebodies und20 MiB
Paketdateien. Der Storebranch enthält ausschließlich `delivery/stream.json`;
README/Workflows/andere Blobs auf dieser Branch werden abgewiesen. Commit-/Tree-
Metadaten sind zusätzlich begrenzt. Bis512 Pakete/8 GiB, Vorwarnung80%, kein
unbegrenztes Kapazitätsversprechen. Aktuelle reale Größe und Änderungsrate vor
Auftrag messen. v1 bleibt Altformat mit seinen alten Grenzen; der Monitor nimmt
keine v1- oder rein lokale Quittung als aktuellen Betriebsbeleg an.

Nur neue Pakete in neue unveränderliche Verzeichnisse `packages/<INDEX>/` des
zweiten Repos übertragen; ein Paketcommit je Paket. Bereits bestätigte Pakete
werden weder geändert noch täglich erneut hochgeladen. Keine DELETE/Force-
Pushes/Historyrewrites. Nach jedem Commit Pin und alle Dateien/Hashes aus dem
zweiten Repo separat lesen. Bei unklarer Pushantwort nur Readback, kein
automatischer Zweitpush. Ein identisches bereits bestätigtes Paket darf nach
Readback wiederverwendet werden. Widerspruch oder fremder Parent: Halt.
Ausstehende Pakete sind noch kein vollständiger Backupabschluss.

**Aus dieser zweiten Kopie**, nicht aus dem Ursprungsclone, isoliert restoren:
Git-Bundleclone, `git fsck --full`, vollständige Commitfolge, Commit-/Blob-/Body-
Identität und alle Manifest-Vorgänger prüfen. `restore_verified` verlangt den
vorher unabhängig festgelegten neuesten Quellpin/-revision und die Quellidentität,
kopiert nie über ein bestehendes Ziel
und provisioniert ausschließlich `blocked-store` mit offenem Nachfolgeabgleich.
Sending wird uncertain. Alte Healthbindungen sind geleert; originale Archivbytes
bleiben im Verification-Clone unverändert. Der Clone hat einen gesperrten Pushweg,
keine Runtime, Credentials oder aktiven Transport.

Fehlproben: fehlendes/vertauschtes Zwischenpaket, falscher Vorgänger, auch nach
Neuberechnung äußerer Hashes, Hashmanipulation, fehlender neuester Commit,
ausgelassener Vorfahr, falsche Identität und abweichende Migration müssen vor einer
Restorefreigabe scheitern. Lokale Fakehistorie und zusätzlich echter lokaler
synthetischer Git-Bundle-/fsck-Restore sind getestet; das ist kein privater
GitHub-Backupnachweis. Source acquisition und Zweitrepo-Write sind noch offen.

Erst nach bestätigtem Zweitrepo-Readback **aller abhängigen Pakete** und isoliertem
vollständigem Restore ein neues Abschlussmanifest committen und lesen, danach
die getrennte Quittung an `backup/latest-receipt.json`: Schema
`p3-verified-backup-receipt-v2`, status confirmed, erwarteter Termin,
Bestätigungszeit, vollständiges `p3-backup-set-v2`-Manifest plus dessen SHA256,
`verified_chain_sha256`, `verified_source_pin`, `verified_source_revision`,
`upload_readback_verified`, `history_verified`, `restore_blocked_verified=true`.
Diese letzten beiden Commits haben jeweils CAS/Parent/Readback;
höchstens64 KiB Quittung. Nie eine noch unbekannte eigene Backupcommit-SHA in
sich einbetten. Monitor bindet die Quittung an den separat gelesenen Backuphead.
Freigabevorschlag nur für eine spätere synthetische Erstprobe plus Fortsetzung:
maximal6 neue Pakete,120 MiB Paketdateien,128 MiB übertragene Git-Packdaten je
Richtung insgesamt,128 KiB Abschlussmanifest und64 KiB Quittung; maximal8
Nicht-Force-Pushes (6 Paket-,1 Manifest-,1 Quittungscommit), nur der benannte
Backupbranch. Max200 lesende REST-Requests insgesamt, höchstens3 lokale
Git-Übernahmen vom benannten Zweitrepo, keine impliziten Submodule/LFS/anderen
Remotes. Transferzeit und tatsächliche Bytes müssen der spätere Ausführungsweg
hart begrenzen; kein realer Adapter ist hier freigeschaltet. Per Git-Schritt120s,
gesamter Verifikationsaufruf1800s, Python256 MiB RSS und Git-Baum192 MiB.
Freier Platz: vor Beginn mindestens zweimal gemessene Quell-Gitgröße plus
Paketverbund plus1 GiB Reserve; danach Abbruch bei gefährdeter Reserve.
Keine laufende Sammlung oder Löschung. Benötigt die konkrete Probe mehr,
kein stilles Weiterarbeiten: neue überprüfbare Freigabegrenze vorbereiten.

Unterbrechung nach Paketcommit, vor Abschluss sowie vor Quittung separat proben.
Keine neue frische Quittung ohne vollständigen Verbund; alte Quittung behält ihre
alte Terminbindung. Hart beendeter lokaler Writer hinterlässt nicht verfallenden
Owner-Lock; Prozessende und alle vorhandenen Pakete prüfen, bevor eine ausdrücklich
kontrollierte Wiederaufnahme erfolgt. Kein zeitgesteuertes Stehlen. Bei täglich
fortgeführten kleinen Paketen entstehen teilweise gefüllte letzte Pakete;
512-Paket-Limit kann daher vor der theoretischen Commitobergrenze greifen.
Tages-/Wochenaufbewahrung bewahrt immer sämtliche Basis-/Inkrementabhängigkeiten.
Ein v1-Paket wird nur explizit als v1 restored; Überführung benötigt einen neu
vollständig geprüften v2-Verbund, niemals eine umetikettierte alte Quittung.

Ein altes Restore bleibt trotz intakter Hashes blocked: fehlende Nachfolger und
Zustellungen erfordern positiven externen Abgleich. Keine automatische Rückkehr,
neue Store-ID oder ältere gesunde Revision als Umgehung. Das zweite Repository
teilt GitHub-Plattform- und gegebenenfalls Kontorisiko; die lokale Sicherung auf
derselben Platte ersetzt diese externe Probe nicht.

## Freigaben und Abschlusskriterien

Die fünf Probeaufträge sind getrennt. Keiner erlaubt main-Merge, PR, Push des
neuen Codezweigs, Workflow-Dispatch gegen Produktion, aktive Workflowänderung,
Deployment/Pages, Telegram, Broker, Secretabruf, Collector, Renditesuche,
Positionsmigration oder P4. Ein eigener begrenzter Code-Push/Online-CI-Auftrag
bleibt Sache des Hauptchats; die hier beschriebenen späteren Store-/Backupwrites
sind ausschließlich noch **nicht erteilte** Freigabevorschläge.

Abnahme verlangt tatsächliche private Sichtbarkeit/Rechte, gemessene Grenzen,
exakte Readbacks, reale Alarm-Eingangs-/Wiederherstellungszeiten und Restore aus
dem zweiten Ziel. Fake-Tests oder ein einzelnes HTTP200 ersetzen diese Belege
nicht. Hauptplan und P3/D3 werden hier nicht endgültig als abgenommen markiert.

Die Requestfelder beruhen auf [GitHub Contents/CAS](https://docs.github.com/en/rest/repos/contents),
[Run-Metadaten](https://docs.github.com/en/rest/actions/workflow-runs) und
[attemptgebundenen Joblisten](https://docs.github.com/en/rest/actions/workflow-jobs).
Die Alarmfelder und geplanten Zeiten folgen der [cron-job.org-REST-Dokumentation](https://docs.cron-job.org/rest-api.html);
die Dispatchvariable ist in [Cron job variables](https://docs.cron-job.org/creating-cron-jobs.html)
dokumentiert. Öffentlich lesende Dokumentationsprüfung08.10.2026, keine Kontoeinrichtung.
