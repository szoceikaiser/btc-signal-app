# Lokale Vorbereitung der echten synthetischen Storeprobe

Stand 10.10.2026. **Keine echte Probe und keine Repositoryanlage genehmigt oder
ausgeführt.** Hauptchat entscheidet über Ziel, Zugang, Freigaben und Abnahme.
Quelle: `0ddd28b4db1679e4e5b89dc255ae500baa4c969c`, Baum
`b50464d192b81b4dcd888ae02113b56672bc4485`. Die neue Codeidentität steht im
additiven Lieferbeleg; sie hat hier keine Online-CI.

## Werkzeug und offline prüfbare Vorbereitung

`tools/p3_github_probe.py` ist von Fake-only `p3_store_probe.py` und dem unveränderten
Laufzeitadapter getrennt. Import und Aufruf ohne vollständige Realargumente machen
keine Requests und fragen keine Credentials ab. Es gibt keine selbst erzeugte
Freigabe. `tools/p3_probe_simulation.py` ersetzt ausschließlich die HTTP-Grenze;
dieselben Contents-, Ref-, Commit-, Tree- und Compare-Requestformen durchlaufen
den vorhandenen CAS-/Parent-/Readbackvertrag.

Planvorlage lokal in eine neue Datei schreiben:

```powershell
python tools/p3_github_probe.py --template <NEUE-PLANVORLAGE.json>
```

Die mitgelieferte `P3-STOREPROBE-PLAN.template.json` enthält ausdrücklich offene
Werte. Hauptchat muss **ein** dediziertes privates synthetisches Repo mit tatsächlicher
ID auswählen, die ausdrückliche Branch festlegen, acht feste Nonces, den neuen
Code-HEAD/Baum/Dateihashes, Ablaufdatum, den absoluten Journalordner und einen
geprüften Berechtigungsbeleg eintragen. Kein Kontoscan, kein Secretabruf.
Store/Stream, FLAT-Fixture, Pfad und bedeutungslose Transportidentität sind fest.
Produktionsidentitäten können weder aktiviert noch durch einen Plan eingesetzt werden.

Vorliegende Repositoryanlage und Settings sind Voraussetzung eines gesonderten
Auftrags. Das Werkzeug legt kein Repo an, deaktiviert keine Settings und startet
keine Actions. Die Probe braucht eingefrorene Einstellungen und ausgeschlossene
andere Schreiber. Der aktuelle Adapter kann Änderungen von GitHub-Settings nicht
atomar mit Contents-CAS verbinden; deshalb gehört diese organisatorische Bindung
in den späteren konkreten Freigabetext.

## Rechte und Vorprüfung

Getrennte, kurzlebige Credentials, ausschließlich für die bestätigte Repository-ID:

| Zugang | Rechte | Verwendung |
| --- | --- | --- |
| Schreiber | Contents:write, Metadata:read | Contents-CAS; keine Actions-/Workflows-/PR-/Admin-Schreibrechte |
| Prüfer | Contents:read, Metadata:read, Administration:read, Pages:read | Privatheit, Actions, Pages, Branchregeln und vollständige Historie |
| Bootstrap | Contents:write, Metadata:read | Ein exakter Nicht-Force-Git-Push; kann dasselbe geprüfte Writercredential sein |

Der Prüfer muss im Repo Administrationszugang besitzen, dessen Token auf die
genannten Leserechte eingeschränkt ist. GitHub nennt Administration:read für
Actions-Settings und klassische Branchprotection; Pages:read für die Pages-Abfrage.
Das Contents-Credential begrenzt **nicht** auf Datei/Branch. Seine verbleibende
Schreibmacht im gesamten Testrepo muss vom Nutzer ausdrücklich akzeptiert werden.
Die API beweist nicht selbst die Auswahl aller Repos oder alle Tokenrechte: der
separat geprüfte Credentialbeleg, Hash und genau eine Repository-ID sind zusätzlich
Pflicht. Das Werkzeug erzeugt diesen Beleg nicht.

Vor jeder Phase liest der Prüfer Repo-ID/full_name/private/has_pages/archived und
effektives `permissions.admin`, Actions `enabled=false`, Pages (404 **zusammen mit**
`has_pages=false`, belegtem Pages:read und Adminprüfung), aktive Regeln für die exakt
genannte Branch, Regeln einschließlich übergeordneter Regeln sowie Branchliste.
Für diesen engen Plan sind Regelnlisten leer, die einzige vorhandene Branch ist
unprotected, klassische Protection ergibt mit belegtem Administration:read 404.
Nichtleere Regeln werden ohne Ausnahmekonstruktion abgewiesen. Der Regelnendpoint
funktioniert auch für noch nicht vorhandene Branches. Fehlende Prüfrechte,
403/429, andere Repos/Branches, Pages oder Actions halten vor dem Write an.
404 allein ist kein ausreichender Rechtebeleg.

Öffentliche offizielle Dokumentation, gelesen am 10.10.2026:

- [References: leere Repositories](https://docs.github.com/en/rest/git/refs#create-a-reference)
- [Contents/CAS](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents)
- [Actions-Settings und Leserechte](https://docs.github.com/en/rest/actions/permissions#get-github-actions-permissions-for-a-repository)
- [Pages und Leserechte](https://docs.github.com/en/rest/pages/pages#get-a-github-pages-site)
- [Regeln für vorhandene und fehlende Branches](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch)
- [Klassische Branchprotection](https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection)

## Expliziter blocked-Root-Bootstrap

GitHub kann in einem Repository ohne Branches keine References über die
References-API anlegen. Die Contents-API kann ein leeres Repo initialisieren;
die vollständige Bindung einer neuen, frei benannten Branch wird hier bewusst
durch einen **gesondert benannten Git-Initialisierungsschritt** gelöst.

1. Mit ausgefülltem Ziel/Codepin den Root ausschließlich lokal vorbereiten:

   ```powershell
   python tools/p3_github_probe.py --prepare-root <NEUER-LOKALER-BARE-ORDNER> --plan <PLAN-ENTWURF.json>
   ```

   Dies schreibt lokale Git-Objekte, keine API. Root enthält ausschließlich
   `delivery/stream.json`; keine README, Vorgänger, Workflow, Tag oder Position.
   Snapshot ist synthetisch FLAT, blocked, Owner leer; Revision0, Null-Parentdigest.
   Deterministische Commitmetadaten und Seed-write_id ermöglichen Vorabpinning.
   Rootcommit, Seed-SHA256 und Bytes in den Plan übernehmen. Bundle/fsck/Tree lokal
   prüfen. Neuer ausführender Bare-Ordner erzeugt später exakt dieselben Objekte.
2. Hauptchat prüft den vollständigen Plan einschließlich Rootbytes/-commit,
   Quelle, Codepins, Zugang, Budgets und Restschreibmacht. Canonical-JSON-SHA256 des
   Plans unabhängig berechnen und ausdrücklich autorisieren. Eine Grantdatei
   muss diesen Hash, **eine** Phase, tatsächlichen menschlichen Freigeber,
   Freigabebeleg-SHA256 und kurze UTC-Gültigkeit binden. Kein generischer Freibrief.
3. Genehmigte Bootstrapphase bestätigt zunächst **keine vorhandene Branch**,
   keine Regeln, Privatheit und Settings. Dann genau ein Versuch:
   `git push --no-verify --porcelain https://github.com/<OWNER>/<REPO>.git <ROOTSHA>:refs/heads/<BRANCH>`.
   Nie `--force`, DELETE, Default-/main-Fallback oder README-Initialisierung.
   Hooks sind auf einen neuen leeren Ordner gesetzt; System-/Global-Gitconfig
   und ambient Gitüberschreibungen sind deaktiviert. Die Credentialhilfe benutzt
   nur das ausdrücklich verdeckt eingegebene Testcredential über einen privaten
   Askpass-Pipe; kein Token in URL, Kommandoargumenten, Datei oder Output.
4. Auch bei verlorener Gitantwort nur Readback, solange Plan UND Grant noch gelten: Ref → Contents am Commit → Ref,
   vollständiger Tree, Root ohne Parent und exakt freigegebene Bytes. Keine
   unbestätigte Bootstrapfortsetzung und kein zweiter Push. Unbekannter Zustand
   bleibt erhalten. Kein Cleanup/Reset des Ziels.

Dieser Bootstrap ist eine neue eigene Mutation. Repositoryanlage/Settingsänderung
sind **nicht** in seinem Budget oder seiner Freigabe enthalten. Die externe
Transportausführung erfolgt ausschließlich später mit gesonderter Zustimmung.

## Phasen und Freigabebindung

Ausgefüllter Plan und echte Grants liegen außerhalb des Codes. Eine Grantvorlage
ist kein Auftrag und hat `human_authorization=false`. Das Werkzeug hat keinen
Grantgenerator. Die menschliche Freigabe und deren Beleg müssen tatsächlich aus
dem Hauptchat stammen; ein boolesches JSON-Feld allein stellt diese Erlaubnis
nicht her. Vor dem Credentialprompt prüft das Werkzeug HEAD/Baum/Dateihashes und
sauberen tracked Code. Kein Push dieses neuen Codebranches durch Storefreigabe.

Späterer Aufruf **erst nach Hauptchat-Freigabe**:

```powershell
python tools/p3_github_probe.py --real --plan <PLAN.json> --grant <PHASENFREIGABE.json> --approved-plan-sha256 <UNABHAENGIG-FREIGEGEBENER-HASH> --phase <PHASE> --journal <PLAN-JOURNALORDNER/NEUE-PHASE.jsonl> --previous-journal <UNMITTELBARER-VOLLSTAENDIGER-VORGAENGER.jsonl>
```

Bootstrap lässt `--previous-journal` weg und benötigt zusätzlich
`--bootstrap-dir <NEUER-BARE-ORDNER>`. Normale Starts aktivieren nichts. Phase
`activate` muss unmittelbar auf bestätigten Bootstrap folgen: blocked-Claim
scheitert ohne PUT, dann separat genehmigter synthetischer Aktiv-CAS. Runtime
bootstrapped nie.

| Phase | Benannte Runs | Verhalten / geplante Obergrenze |
| --- | --- | --- |
| bootstrap | separate Rootinitialisierung | 1 Git-Pushversuch, 0 PUTs |
| activate | writer-1 | blocked verweigert; 1 bestätigter Aktiv-PUT |
| happy | writer-2 / writer-3 | zwei gleiche Startreads, ein Gewinner, ein veralteter CAS-Verlierer; Claim, Start, Intent, sending, Fixturequittung73, Kandidat, Attestation, bestätigte Freigabe, zweite bestätigte Claim/Freigabe; 11 PUT-Versuche |
| lost-after | writer-4 / writer-5 | dieselbe synthetische Folge; Writerantwort nach Mutation lokal verworfen, nur exakter Write-/Parentreadback bestätigt; 11 PUT-Versuche |
| process-loss | writer-6 / writer-7 | nach bestätigtem sending Prozess beenden, kein Transport/Unlock/Runabschluss; 5 PUT-Versuche |
| takeover | writer-8 / Maintenance | eigene Freigabe, positive Parent-Wait-Quittung und exakter Owner/Revisions-/Commitbeleg; 1 PUT, sending → uncertain; keine Zustellfreigabe |
| inspect | Read-only | nur begrenzte Settings-/Historienprüfung; 0 PUTs |

Summe dieser gewählten Folge: **29 PUT-Versuche plus1 Git-Push**, davon ein
veralteter, nicht mutierender CAS je Zweischreiberphase. Ohne takeover28 PUTs.
Die alternativen terminalen `lost-before`/`stale`-Phasen sind vorbereitet und
offline getestet, aber **nicht** Bestandteil der gelieferten Standard-Realfreigabe.
Eine Wahl im späteren Plan muss vor Beginn erfolgen. Nach einem solchen unklaren
Zustand kein weiteres Experiment, neue Run-ID/Store-ID oder älterer gesunder Stand
zur Umgehung. 403/429/Responsebudgetproben ausschließlich lokal; keine absichtlichen
realen Rechtefehler, Limits oder Rate-Limit-Flut.

Das ist ein synthetischer **lokaler** Runabschluss im echten Teststore, kein
GitHub-Actions-Lauf: Actions bleiben aus. Der bestehende run_health-Vertrag bindet
Start/Kandidat/bestätigten Locator/Attestation an Repo, Run/Attempt/Nonce,
Code/Config/Store/Stream. Die gespeicherte Kandidatenrevision wird separat mit
Compare-Vorfahrprüfung gelesen. Eine echte Signal-/Watch-/Monitor-/Actionsabnahme
ist damit nicht erfolgt. Telegram, E-Mail, Broker, Marktabfrage: null.

## Request-, Byte- und Unterbrechungsgrenzen

- Global höchstens48 PUT-Versuche,384 GET-Versuche,1 Git-Pushversuch,
  **49 versuchte Mutationen insgesamt**. Kein POST/PATCH/DELETE/Forceweg.
- Genau acht vorab benannte synthetische Runidentitäten, je12 PUTs; je Phase12
  PUTs und128 GETs, zusätzlich immer das gemeinsame globale Budget. Die
  Bootstrapphase erhält genau einen Git-Pushversuch. Keine ungezählten Retries.
- 768.000 unkodierte Storebytes je Body,2 MiB je API-Antwort,15s je Request und
  Bootstrap-Gitprozess. Rootbundle höchstens2 MiB; Root enthält nur den kleinen
  synthetischen Seed. Dies ist keine Produktionsgrößen- oder Hostkapazitätsmessung.
- Jeder Versuch wird **vor** dem Request durable gezählt, auch lokal verworfene
  oder 403/429/409/Timeoutversuche. Ref/Contents/Ref, Parent, Compare, Settings und
  Tree zählen ebenfalls. Grantablauf autorisiert keine Fortsetzung.
- Bootstrap prüft vollständig ab Root. Spätere Phasen prüfen alle neuen Commits
  bis zum exakt im vollständigen Vorgängerjournal bestätigten Historienanker,
  einschließlich Blob/Tree, Parentdigest und Revision. Der Anker wird erneut
  unabhängig gelesen und gegen den bestätigten Bodyhash gebunden. Kein
  ausgelassener Vorfahr und keine abgeschnittene Storehistorie.

UTC-Journal mit Repo-ID/Branch/Pfad, Phase, Run/Attempt/Nonce, Write-ID, altem
Blob, Revision, Digestparent, beobachtetem und bestätigtem Commit/Parent, Bytes,
Requestzählern und Ergebnis. Keine Credentials, Nachrichtentexte oder API-Bodies.
`observed-only` ist keine Writebestätigung. Erst nach CAS-/Readbackvertrag erscheint
`confirmed`; bei Fehler niemals phase_end/Runerfolg erfinden.

Seit N-P3-02 gilt ausschließlich `p3-synthetic-probe-plan-v2` mit
`session_contract=sqlite-frontier-v2` und `expiry_policy=stop-all-outbound-no-grace`.
Die neue Grantvorlage verlangt `p3-human-grant-v2`. Alte Pläne/Journale werden
nicht automatisch migriert; alte Belege bleiben unverändert.

Der im Plan festgelegte **eine** Journalordner enthält `probe-session.sqlite3`,
`probe-session.lock`, feste `attempt-<PHASE>.json`-Startbelege und sämtliche
kumulativen Phasenjournale. Die Startbelege werden vor dem ersten Phasenjournal
geflusht und fsync-bestätigt; jeder muss exakt zum zentralen phase_start passen.
Ein zusätzlicher/partieller Startbeleg sperrt die Fortsetzung auch dann, wenn
die frühere zentrale Frontier noch confirmed war. SQLite ist die
maßgebliche unverzweigte Sessionhistorie. Vor Credentials prüft der nächste Start
den Planhash, den exakten zuletzt gebundenen Dateinamen, alle Journalzeilen gegen
die zentralen Zeilen, den bestätigten Publikationshash und die daraus vollständig
rekonstruierten Gesamt-/Phasen-/Runzähler. Ein älterer gültiger Hash, ausgelassene
Zwischenphasen, eine anders benannte Kopie oder ein fremder Plan reichen nicht.
Auch eine fehlgeschlagene Phase gehört dauerhaft zur Frontier. `inspect` kann
vorherigen Verlust/Fehler nicht zu einem gesunden Mutationsvorgänger machen.
Jede Phase ist im Plan höchstens einmal ausführbar, auch mit anderem Dateinamen.

Eine gemeinsame Betriebssystemsperre gilt für Probe, Inspektion und Übernahme.
Die Lockdatei wird nie entfernt. Der Kernel gibt die Sperre nach Prozessende
frei; das ist **keine** Freigabe der offenen dauerhaften Phase. Ohne positiven
Prozessende-/Owner-/Revisionsbeleg bleiben deren Folgestarts gesperrt. Es gibt
keinen Review-Nebenlock, Boolean-Bypass, Fristablauf oder automatische Entsperrung.

Jede Reservierung erfolgt in dieser Reihenfolge: SQLite-Transaktion mit
`synchronous=FULL` committen → Journalzeile schreiben/flush/fsync → Publikationshash
in zweiter FULL-Transaktion committen → Frontier/Zähler und Freigabe erneut prüfen
→ Outbound. Dies gilt für sämtliche GETs, PUT-Versuche und den einen Git-Push,
auch bei HTTP-Fehlern, verlorenen Antworten und Inspektion. Ein Abbruch nach
Reservierung kann konservativ einen Versuch zählen, obwohl nichts hinausging;
dieser Versuch wird nicht zurückerstattet. Die Budgets steigen dadurch nicht.

Unklarer Commit/fsync/Publikationsschritt sperrt den laufenden Prozess. Nach
hartem Verlust mit unvollständiger Publikation bleiben zentrale Historie und
abweichendes Journal für lokale Prüfung erhalten; das Werkzeug repariert,
exportiert oder wiederholt sie **nicht automatisch**. Eine solche Session ist
mit diesem Werkzeug nicht fortsetzbar. Das ist eine bewusste Restgrenze, keine
Erlaubnis für einen neuen Ordner/Planhash oder einen älteren gesunden Storestand.
Ein fehlendes zentrales DB-File bei vorhandenen Sessionartefakten hält ebenfalls
an. Geprüft ist harter Prozessverlust; Stromausfall-/Datenträgergarantien über die
Zusagen des lokalen Dateisystems und SQLite hinaus werden nicht behauptet.

### Grantgültigkeit unmittelbar an der Grenze (N-P3-03)

Der tatsächlich autorisierte Grant samt Plan-/Phasen-/Reviewhash wird an die
laufende Boundary gebunden und sein Hash/Ablauf im Journal vermerkt. Vor jedem
Request und erneut **nach** dauerhafter Zählung, direkt vor HTTP oder Git-Push,
müssen Plan **und** Grant gelten. Es gilt strikt `jetzt < Deadline`; genau an
der Deadline ist kein Start erlaubt. Credentialeingabe, Vorprüfung, Seed-/Askpass-
Vorbereitung oder langsames fsync verlängern die Freigabe nicht. Zusätzlich
prüft die Abschlussmeldung die noch gültige Freigabe.

**Kein Nachlaufrecht:** Auch neue GETs/Readbacks sind nach Ablauf verboten.
Ein rechtzeitig gestarteter Request darf seine Antwort liefern; kommt diese
nach Ablauf, wird nur das beobachtete Ergebnis lokal protokolliert. Danach
keine neue Mutation, kein Retry, kein Readback und kein pauschales `confirmed`.
Eine unklare Mutation oder ein überlebendes sending bleibt erhalten und gesperrt.
Eine eigene spätere `inspect`-Freigabe kann nur bei weiterhin gültigem Gesamtplan,
maßgeblicher vollständiger Frontier und freier gemeinsamer Sperre lesen; bei
offener unterbrochener Phase benötigt sie zusätzlich den separat gebundenen
positiven Prozessende-Review. Nach Ablauf des Gesamtplans endet dieser Ablauf;
ein neuer Plan ist keine automatische Budgetrücksetzung.

Innerhalb eines Prozesses begrenzt zusätzlich monotone verstrichene Zeit die
Laufzeit. Rückläufige UTC sperrt den Guard dauerhaft. Die zentral gespeicherte
höchste beobachtete UTC verhindert bei Neustart eine Fortsetzung hinter dieser
Zeitmarke, auch bei Übergabe alter Journale. Das ist kein allgemeiner Schutz gegen
gezielt verstellte Systemuhren, zurückgerollte Datenträger, gefälschte menschliche
Freigaben oder einen absichtlich veränderten Client. Der lokale Sessionordner
muss vollständig und unverändert erhalten und gesichert werden.

Die Prozessverlustphase später durch `p3_probe_launcher.py` starten. Der Elternprozess
beobachtet `wait()` und speichert eine neue `p3-parent-wait-exit-v2`-Quittung mit
PID/Exitcode/UTC, exakt zur Phase gehörender PID, Journalname, Frontierhash/-zeilenzahl, vollständigem Journalhash und dem zuletzt bestätigten
sending-Owner/Revision/Commit. Timeout ist kein Runende und erzeugt keine Quittung:

```powershell
python tools/p3_probe_launcher.py --plan <PLAN.json> --journal <JOURNAL/process-loss.jsonl> --receipt <NEUE-ENDEQUITTUNG.json> -- --real --plan <PLAN.json> --grant <VERLUSTFREIGABE.json> --approved-plan-sha256 <PLANHASH> --phase process-loss --journal <JOURNAL/process-loss.jsonl> --previous-journal <JOURNAL/lost-after.jsonl>
```

Für takeover prüft der Hauptchat positiv diese Parent-Wait-Quittung, keine
anderen Worker und pausierte Trigger. Neue Reviewdatei enthält `expected_owner`,
`expected_revision`, `expected_commit`, `termination` (Originalquittung) und
`evidence` (reviewer, evidence_sha256, old_owner, run_completed,
workers_terminated, triggers_paused). Eigene Takeovergrant bindet den canonical
Reviewhash als `review_sha256`. Aufruf zusätzlich mit
`--termination-review <REVIEW.json>`. Das Werkzeug prüft positive Waitquittung,
Journalhash/Frontierpräfix und exakten aktuellen Commit/Owner/Revision unter der
gemeinsamen Sessionsperre. Ein inzwischen bestätigtes inspect darf nur das
unveränderte Originalpräfix ergänzen; als Vorgänger ist weiterhin die neueste
Frontier nötig. Für inspect nach offenem Prozessverlust bindet dessen Grant
ebenfalls den Reviewhash und der Aufruf erhält `--termination-review`.
Alte Locks werden nicht entfernt. Kein Fristablauf.
Überlebendes sending bleibt uncertain und sperrt neue Claims, auch unter anderen
vorbenannten Runs. Nur inspect ist danach vorgesehen; keine Zustellklärung,
Produktionsfreigabe, neue Stream-ID oder automatische Reaktivierung.

## Konkreter Freigabevorschlag für den Hauptchat

Zunächst Code und neue lokale Gegenfallbelege für N-P3-02/03 abnehmen. Danach tatsächliches Testrepo, ID,
Branch, lokale Journalpfade, Zugang und Settings über einen gesonderten Auftrag
konkret auswählen und bestätigen. Den vollständig ausgefüllten Plan mit Code- und
Seedpins sowie festen Sessionordner unabhängig prüfen. Der Ablauf darf
keine alte v1-Session fortsetzen. Vor jeder späteren Phasenfreigabe den neuesten
Frontierhash, Dateinamen, kumulative Zähler und Restbudget prüfen; genügend
Zeit für Vorprüfung, Mutation und vollständigen Readback einplanen. Keine
Verlängerung eines Grants durch das Werkzeug. Erst dann darf der Nutzer genau diesen Planhash
mit obigen49/48/384-Grenzen und repoweiter Restschreibmacht genehmigen.

Bootstrap und Aktivierung sind ausdrücklich getrennte benannte Freigaben.
Danach happy und lost-after; Prozessverlust am Ende. **Takeover erst nach dem
tatsächlichen positiv belegten Prozessende und einer neuen konkreten Reviewfreigabe.**
Kein Auftrag dieses Arbeitschats erteilt eine dieser Freigaben. Testrepo und
ungeklärte Historie erhalten; Aufbewahrung/Aufräumen separat entscheiden.

Kein Hauptplanupdate, Online-CI, Push des Codebranches, Merge/PR/Dispatch, aktive
Workflowänderung, Host/cron/Deployment, tatsächliches Backup, Positionmigration,
Livewechsel oder P4. C05/S006 bleiben inaktiv. Der manuelle Vorschau-Limitablauf
wird nicht analysiert. Der Nutzer meldet diese Abgabe selbst im Hauptchat.
