# Öffentliche Betriebsspeicher unter GitHub Free

Stand: lokaler deaktivierter Kandidat auf Basis 9a458483f56244882954f7d2bb40b6ab5cae2128.
Die öffentliche Variante einschließlich Zuständen, Historien, generierten
Telegramtexten und Zustellbelegen ist gewählt. Keine erneute Tarifentscheidung.
Diese Dateien sind noch keine Einrichtung oder Livefreigabe.

## Konkrete Ziele und Bindungen

| Repository | Branch | Zulässige Nutzdateien |
|---|---|---|
| szoceikaiser/btc-delivery-store | delivery-stream-v2 | delivery/stream.json; vollständige Vorgeschichte |
| szoceikaiser/btc-delivery-store | delivery-fence-v2 | delivery/actions-fence.json; vollständige Vorgeschichte |
| szoceikaiser/btc-delivery-store | reviewed-migration (neuer Vorschlag) | genau das separat geprüfte Migrationspaket mit vollständigem Dateimanifest |
| szoceikaiser/btc-delivery-backup | verified-pair-packages | pair-manifest.json, manifests/&lt;sha256&gt;.json, stream/packages/**, fence/packages/** |
| szoceikaiser/btc-delivery-backup-verification | verified-receipts | receipt.json, receipts/&lt;sha256&gt;.json |

Alle Zielrepositories sind vorgeschlagen, nicht angelegt; echte IDs, Schutzregeln,
Zugangsbelege und Payloadpins bleiben null/ausstehend. Codejob: bereits bestehendes
szoceikaiser/btc-signal-app, main; dessen echte ID wird ebenfalls vor Ort geprüft.
`private_store_repository` bleibt ausschließlich als kompatibler bestehender
Wire-Feldname in Fence/Backup/Completion erhalten. `public_access` bindet dieselbe
Adresse ausdrücklich an `visibility: public`, echte numerische ID und Branch.
Es gibt keine private Ausweichroute. Alte Legacyvorlagen außerhalb der sieben
neuen Hostedvorlagen und aktive Workflows werden hier nicht installiert/geändert.
Der kanonische Digest des vollständigen freigegebenen `public_access`-Dokuments
muss als `public_access_sha256` in jedes Deployment und damit jede Fence-/Backup-
Bindung. Die Runtime prüft diese Gleichheit vor Facharbeit. Reviewänderungen sind
eine neue konkrete Aktivierungsentscheidung; alte Fence-/Backuppins werden nicht
automatisch umgebunden oder freigeschaltet.

## Datenklassen und Dateiabschluss VOR Veröffentlichung

1. Den frischen, gestoppten Schnitt als blocked-Migration erzeugen; das ist eine
   eigene spätere Aufgabe. Vorhandenes Livebackup und main69e676d8 erhalten.
2. Für ALLE vorgesehenen Branches einschließlich sämtlicher erreichbarer Historie
   ein vollständiges Inventar erstellen: Repository/Branch, Commit/Tree, Pfad,
   Modus, Bytes, Gitblob-SHA und SHA256. Kein pauschales Upload eines Arbeitsordners.
   Store/Fence enthalten Zustände, Signalhistorie, Outboxtexte, Telegramreceipts,
   Zielhashes, Run-/Store-/Stream-IDs und Sperrzustände. Backup enthält dieselben
   Daten plus vollständige Historien; Quittungen enthalten Manifeste/Prüfpins.
3. Migration umfasst nur das inventarisierte Paket; Konfiguration auf fremde/private
   Zusatzdaten prüfen. Vorgeschlagenen reviewed-migration-Branch separat reviewen
   und dessen immutable Commit/Tree/Blobs pinnen. Runtime legt ihn niemals an.
4. Vor Publikation Dateien UND erreichbare Gitblobs auf Schlüssel, Zugangsdaten,
   credential-bearing URLs, Authorization/Cookie-Header, fremde private Daten und
   unerwartete Pfade prüfen. Nur später im Hauptchat darf ein dafür autorisierter
   Secretabgleich stattfinden; dieser Arbeitschat hat keine Secrets gelesen.
   Musterprüfung allein beweist keine Secretfreiheit. Konkrete Dateiliste und
   Prüferbeleg versiegeln. `.git`, lokale Environments, Logs, Testfixtures,
   Auditordner und Runtime-Secrets gehören nicht in die drei Datenspeicher.
5. Pages veröffentlicht ausschließlich die bestehende Whitelistprojektion und
   bereits öffentliche eingefrorene Historydateien; drei gesonderte Beobachtungen
   vor Paket/Upload/Deploy bleiben bestehen. Kein RAW-Fallback.

## Kleine Einrichtung im Hauptchat, in dieser Reihenfolge

1. Konkretes Inventar, Secret-Ausschluss, Setupdiff und Rollenbelege abnehmen.
   Keine alte Probe/Starter/Grant wiederverwenden. Repositories zunächst ohne
   automatische README/License/Gitignore anlegen; keine fremden Nutzdateien.
2. Echte öffentliche Repoantworten/IDs mit Namen abgleichen und in
   `public-access.disabled.json` sowie ALLEN Runtimekopien eintragen. Für die
   beiden Backupziele einen eigenen Parentcommit mit leerem Tree auf dem exakten
   Zielbranch erstellen, SHA/Tree pinnen. »Leer« bedeutet leere Nutzdaten, nicht
   ein zur Laufzeit zu erstellendes Ref. Unbekannte vorhandene Inhalte verweigern.
3. Store-Seed blocked und Fence-v2-Seed aus demselben Deployment separat erzeugen,
   prüfen und nur im genehmigten Bootstrap einspielen. Backup/Receipt noch ohne
   Pakete. Frische Migrationspins und Store-/Stream-IDs einsetzen. Keine Aktivierung.
4. Vier Repository-Rulesets für exakt die vier Betriebsbranches aktiv einrichten:
   deletion, non_fast_forward und required_linear_history, keine bypass actors,
   keine Ausnahmen oder inherited/organization-Regeln. Vorlage
   `public-ruleset.disabled.json` ist ausdrücklich disabled und kein POSTauftrag.
   Einrichtung ist separat; Runtime benötigt keinerlei Administration:write.
5. Anonymous GET rules/branches mit per_page=100 vollständig bis zum Ende lesen,
   maximal vier Seiten. Jede neue/fehlende/geänderte Regel, falsche Quelle oder
   unvollständige Pagination stoppt. Vollständige kanonische aktive Liste hashen.
   Jedes beteiligte Ruleset anonym GETten, nur bypass_actors aus dem öffentlichen
   Hash ausnehmen; exakte Repositoryquelle, Branchbedingung und active pinnen.
   Disabled/evaluate genügen nicht. Alle Ergebnisse in protection-Einträge binden.
6. Eigentümer prüft in der echten GitHub-Rulesetansicht separat und konkret für
   jeden Ruleset-ID/Repo-ID/Branch die vollständige Bypassliste einschließlich
   Integrationen/Repositoryrollen. Beleg ohne Schlüsselwerte archivieren, SHA256
   in `public-bypass-review.disabled.json` eintragen; erst nach tatsächlichem
   Review `bypass_actors: []`, status actually-reviewed, Prüfer/Zeit einsetzen und
   `public_access.review_hash` bilden. Vorlage niemals als Beweis deklarieren.
   Fehlendes bypass_actors in anonymen Antworten ist UNBEKANNT. Aktuelle versteckte
   Bypässe sind mit anonymen Reads allein nicht beweisbar. Jede administrative
   Änderung erfordert Stillstand und neuen tatsächlichen Review. Öffentliche
   Antwortänderungen werden erkannt; unverändert verdeckte Änderungen können
   ohne zusätzlichen Providerbeleg nicht erkannt werden. Diese Grenze bleibt offen.
7. Drei getrennte Writerzugänge mit separater nicht geheimer Referenz bereitstellen,
   wie unten beschrieben. Tatsächliche Auswahl und Reichweite einmalig reviewen;
   keine Schreibsondierung gegen fremde Repositories, keine Rechte aus Owner-
   permissions ableiten. Reviewrecords mit evidence_sha256 und review_hash binden.
8. Begrenzte lesende Vorprüfung erst nach ausdrücklicher Netzfreigabe im Hauptchat:
   `python tools/p4_public_preflight.py --review REVIEWED-public-access.json --out NEW-READ-EVIDENCE --public-read`.
   Neue Ausgabestelle erforderlich, GET-only, keine Schlüssel, 24GET/20s/48MiB,
   kein Setup, kein Writerbeweis. Alle vier Schutzbranches müssen vorhanden sein.
9. Konkreten disabled Overlaydiff prüfen; alle Runtime- und Workflowhashes, Codepin,
   `BTC_PUBLIC_CODE_REPOSITORY_ID` (echte Code-Repo-ID), Python-/Actionpins sowie
   Aktivierungsreview aufeinander beziehen. Keine
   Selbstreferenz erfinden: Runtime/Reviewdaten liegen außerhalb des Codepins in
   geprüften Variables. Der deploy-pages-Tag ist weiterhin erst durch einen real
   geprüften immutable Commit zu ersetzen. Linux-/Providerabnahme bleibt offen.
10. Nur nach eigenem Auftrag im Hauptchat ein kleines synthetisches Producer- und
    unabhängiges Verifierpaar unter tatsächlichen Rollen abnehmen: vollständiger
    Download, blocked Restore, exakte veröffentlichte Quittung, keine zweite
    Mutation bei verlorener Antwort. Höchstens ein weiteres Paar nach gesondertem
    konkreten Anlass/Freigabe, keine Kampagne. Nutzdaten-/Telegrambetrieb daraus
    nicht freigeben. Danach erst separater Cutoverauftrag mit frischem Schnitt,
    vollständiger C05-Zielconfig und externer Alarm-/Deadmanabnahme.

## Tatsächlich benötigte Zugänge

| Rolle | Ressourcenauswahl und Rechte | Injektion |
|---|---|---|
| Sender | nur btc-delivery-store; Contents:write + obligatorisches Metadata:read | BTC_REVIEWED_STORE_TOKEN → BTC_DELIVERY_GITHUB_TOKEN; getrennt von Telegram/Coinalyze |
| Producer | nur btc-delivery-backup; Contents:write + Metadata:read | BTC_HOSTED_BACKUP_WRITE_TOKEN, ausschließlich Producer |
| Verifier | nur btc-delivery-backup-verification; Contents:write + Metadata:read | BTC_HOSTED_RECEIPT_WRITE_TOKEN, ausschließlich Verifier |
| Codejob-Metadaten | automatisch für Codejobrepository; actions:read und contents:read | GITHUB_TOKEN: github.token; kein Fremdrepo-Writer |
| Datenreader | public anonymous; keinerlei Token | Source/Migration/Backup/Receipt/Pages/Monitor |

Fine-grained PATs mit Auswahl genau eines Repositories oder entsprechende GitHub
App-Installationen verwenden. Kein klassischer breit berechtigter PAT, kein
Administration:write und kein Workflow-Schreibrecht für Laufzeitrollen. Contents-
Rechte sind repositoryweit, keine erfundene branchfeine PAT-Berechtigung; die
Branchliste ist unsere Laufzeitschranke. Bei App-Nutzung ist kurzlebige Token-
Ausstellung separat konkret zu implementieren/reviewen; diese Vorlagen erwarten
fertig injizierte Role-Tokens und versprechen keine unbegrenzte Lebensdauer.

Einrichtungbeleg pro Writer: echte Credentialart und nicht geheime Referenz,
Resourceowner, ausgewählte Repo-ID und einzige Repoliste, Rechte, Ablaufstatus,
Appinstallation/Tokenausstellung soweit zutreffend, Prüfer und Zeitpunkt, SHA256
des geprüften Belegs. Kein Tokenwert im Record oder Screenshot. Gleiche Referenzen
werden verweigert. Ein Record ist ein menschlicher Reviewvertrag, keine technisch
vollständige Tokenintrospektion. GET repo.permissions darf fehlen; Ownerrechte
beweisen weder tatsächliche PAT-Schreibrechte noch Ausschluss fremder Schreibziele.
Unbelegte echte Schreibreichweite bleibt bis diesem Review offen. Ein späterer
erfolgreicher gebundener Write bestätigt nur das eine Ziel, keine globale Negation.

Schlüssel bleiben ausschließlich Secrets und Speicher im laufenden Prozess.
HTTP-Authorization nur für den jeweiligen Writerrequest bzw. Codejobmetadaten.
Kein Schlüssel bei Daten-GETs oder Gittransport; Gitkindprozesse erhalten die
bestehende saubere Env-Allowlist. Keine Tokens in URL/Argument/Datei/Log/Artefakt.
Kein neuer Secret-Reader-Zyklus. Verifier erhält keinen Backup-/Senderwriter;
Producer keinen Receipt-/Senderwriter. Runtime kann echte unbekannte Tokenreichweite
nicht selbst attestieren; die konkrete Einrichtungsabnahme ist zwingend.

## Budgets und Grenzen

Codebootstrap vor setup-python: sieben Vorlagen enthalten bytegleich
`tools/public_code_checkout.py`, ausgeführt mit dem vorhandenen Runner-python3.
Er akzeptiert nur das öffentliche Codejobrepository mit echter ID und festem
Codepin, nur leeres Workspace, keine Credentials und keine Checkoutaction.
Ein Metadaten-GET (2MiB), ein begrenztes Advertisement-GET (2MiB) und genau ein
read-only upload-pack POST (64MiB) für den angebotenen main-Head, maximal 69MiB
reservierter Transfer, je15s HTTPwallfrist, zusammen120s, Gitstep30s,
256MiB Workspace+Temporärdateien/32768 Dateien, Gitbaum192MiB/64 Prozesse.
Danach Gitobjektimport, echte Vorfahrenprüfung des festen Codepins und detached
Checkout. Git läuft ausschließlich lokal ohne Remote/Token/Helper/Hooks und mit
sauberer Env-Allowlist; keine Git-Secretdatei. Änderungen des main-Headers erlauben
keinen fremden Codepin. Fehlende Protokollunterstützung/zu große Codehistorie/
Symlinks/unerwartete vorhandene Dateien stoppen. Der Runner-python3-Bootstrap und
Linuxresourcegrenzen sind zusätzlich im Hauptchat tatsächlich abzunehmen.
Diese drei Code-HTTPoperationen kommen zu den nachfolgenden Jobbudgets hinzu.

Backup unverändert: 4096 HTTPoperationen (upload-pack POST darin gezählt), maximal
2048 Nicht-GETs, 512MiB reservierter Transfer, 15s je HTTPoperation, 1800s Gesamtzeit
und ursprüngliche Backupfrist, 64MiB Pack je vollständigem Ref, kein shallow/haves/
filter, 8192 Gitprozesse, 64 Prozesse im Baum. upload-pack ist die einzige anonyme
POST-Ausnahme, ausschließlich auf dem gebundenen GitHub-Repository und für den
bereits gepinnten, angebotenen Ref. Writer-REST bleibt authentifiziert. CAS/force:false,
vollständige Historien, immutable Manifeste, blocked Restore bleiben erhalten.

Sender: gemeinsame bestehende 640GET/50PUT, 11GET/1PUT je Bestätigungsfall, drei
Bestätigungszyklen, 2MiB Response, 15s Request und ursprüngliche Slotfristen. Die
öffentliche Repo-/Schutzprüfung verbraucht dasselbe Runbudget vor erster Mutation.
Kein TTL/Autotakeover/Resend; offener Fence blockiert unabhängig vom Alter.

Pages: unverändert 12 Daten-GET/120s/24MiB pro Beobachtung plus separat ausgewiesene
kleine Schutzvorprüfung maximal 24GET/20s/48MiB (gewöhnlich fünf GET für zwei
Branches mit je einem Ruleset). Bestehender Codeentryreader: 3GET/20s/6MiB.
Monitor: Schutzprüfungen im gemeinsamen unveränderten 64GET/20s/128MiB-Budget;
optionaler bestehender Codeentryreader 3GET/20s/6MiB separat. Keine Budgetausweitung
bei Fehlern oder Quotenmangel, kein Authfallback, kein Retry/Resend.

Diese lokalen Obergrenzen sind KEINE zugesicherte GitHub-Quote. Anonymous-API-
Limits können anders und bei gemeinsamem Runner-IP bereits erschöpft sein.
Gerade ein Fünfminutenmonitor und vollständige Backupreads können verfügbare
anonyme Quoten überschreiten. Echte Header/Restquote/Reset und kleine tatsächliche
GETzahlen vor Einrichtung messen; das ist hier nicht erfolgt. Keine zusätzlichen
Reader-Schlüssel oder unbeschränkten HTTPwege als Umgehung einführen. Reicht die
Quote bei erhaltenen Frischebedingungen nicht, bleibt Betrieb blockiert bis zu
einer separat geprüften konkreten Lösung. Gleicher Provider ersetzt keinen
externen Alarm/Deadman. Mockbelege belegen weder Linux noch Livebereitschaft/Rendite.

Keine Actionsbereinigung in diesem Paket. Jede spätere Löschung/Stilllegung auch
von Runs, Logs, Artefakten oder Branches erfordert vorher konkrete Aufgabe,
Abhängigkeiten, Folgen und Nutzerzustimmung. Keine automatischen Nachrichten.
