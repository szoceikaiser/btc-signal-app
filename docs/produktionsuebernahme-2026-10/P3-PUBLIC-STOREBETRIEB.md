# Begrenzter öffentlicher synthetischer Storebetrieb

Vorbereitung, kein echterWrite/Grant/Aktivierung. OriginalPlanhash/Deadline bleiben
historisch unverändert. Ein eigener Betriebsvertrag bindet die vollständige bestätigte
112-Zeilen-Historie, deren Quellen/Grants/Materialisierung, OriginalRoot, aktuelle
Ausführungspins und frischen Prozessende-/Freeze-Review. Eigenes max20h-Fenster und
ausdrücklicher Abschnittsgrant; echteDaten bisHauptchat-Abnahme offen.

## Drei getrennte Abschnitte

Initial:activate→happy→lost-after→process-loss. Eigener menschlicherGrant darf diese
vier benanntenPhasen zusammen autorisieren, maximal28PUTversuche. Reader/Writer werden
einmalverdeckt imChildprozess eingegeben, vor jedemdurablenPhasenstart. ReinerAbbruch
vorStart:Exit3, keinMarker/Request. KeineCredential-Dateien/-Argumente/-Clipboardlogs;
derParent erhält nie dieZugangswerte. Parent startet tatsächlichen Python-B-Worker
und wartet auf dessenExit. Jede Phase verwendet dieselbe zentraleFrontier/Kernel-
sperre/SQLiteFULL/fsync/Highwater und die vorhandenenCAS-/Owner-/Runabschlussfunktionen.

Nach bestätigtensending erzeugt process-loss keinenRunabschluss oderUnlock und endet
mitExit23. Der tatsächlicheParent bindet PID/Exitcode/UTC/Journalbytes/Frontier/Owner/
Revision/Commit in eine neueQuittung. Timeout/anderesEnde erzeugt keineLossquittung.
Dann **STOPP** fürHauptchat-Abnahme der wirklichen Daten. KeinTakeovergrant wird
vorweg erzeugt. Keine automatischeFortsetzung, Frist oderOwnerlease.

Takeover:neuer eigenständigerGrant bindet wirkliche neuesteFrontier und separat
reviewte Originalquittung/Owner/Commit/Revision, alleWorker beendet/Triggerpausiert.
Der bestehende Übernahmevertrag macht sending ohneZustellbeleg uncertain, blockiert
neueClaims und erlaubt keine erneuteNachricht. mode bleibt dabei active; die
Zustellsperre folgt aus uncertain, keine Engineänderung. Das Reviewfeld run_completed bezeichnet
hier positivesProzessende, keinen erfolgreichenSignal-/Run-health-Abschluss.

Inspect:nochmals eigener lesenderGrant, aktuelleFrontier;0PUT. Kein erneuterGit-Push,
keinRootbootstrap, keinStore-/Stream-/Runidentitätswechsel. Namespacepublic-store-*
trennt Phasenmarker vom früher verbrauchtenInspector; es schafft keinenBudgettopf.

## Unveränderte Standardlogik und Geltungsgrenzen

activate entsperrt ausschließlich den feste synthetischenRoot (1PUT), blocked-Claim
vorher verweigert. happy: zwei benannteWriter/alteSHA, einOwner, Intent/sending/
Fixturequittung73/gebundenerRunabschluss/Freigabe (11PUTversuche). lost-after dieselbe
Folge, eine erfolgreicheMutationantwort lokal verworfen, nur exakterWrite-/Parent-
Readback bestätigt (11). process-loss bispersistiertemsending (5). Takeover1.
Summe29PUTversuche einschließlichCAS-Verlierern; kein echterTransport, Telegram,
E-Mail/Broker/Marktabruf. lost-before, weitereVerluststellen undRechte-/Ratefehler
bleiben offline. Keine vollständigeProduktions-/Host-/Alarm-/Backup-/P4-Abnahme.

Vor jederPhase frischePublic-ID/Admin/Actionsaus/Pagesaus, positive200/leere effektive
Regeln/Rulesets, alleiniger ungeschützterZielbranch und eng gebundeneSchutzantworten.
Nach ersterMutation darf derBranchkopf voranschreiten: sein40stelligerCommit muss
nichtRoot-SHA sein. Vollständige neue lineareCommit-/Parent-/Digest-/Bytekette wird
über verifizierteHistorienanker auf den bestätigtenRoot zurückgeführt. KeinREADME-
Vorfahr/fremderRoot/Pfad. Die ersteAktivierung verlangt exaktRootbytes/Revision0.

GlobalAltGET37/PUT0/Git1 bleibt. VerbindlicheOriginalgrenzen384GET/48PUT/Git1/
49Mutationen,12PUT und128GET jeRun/Fall,768000Storebytes/2MiBAntworten. Runidentitäten/
Attempts/Nonces unverändert. Tatsächliche vollständigeFolge undGET-Restbudget werden
imLieferbericht aus dem simuliertenWire ausgewiesen. Jede versuchteMutation/Read vor
Outbound durable gezählt, keineRefunds/Blind-Retries; Datumguard vorOutbound und
confirmed, keinNachlauf. UngeklärterWrite/abgelaufenerGrant sperrtFolgephasen.

## Bedienung erst nach späterer Freigabe

Hauptchat prüft Paket/112Bytes/Root/Code/Budgets, füllt aktuellesWindow/Review und
autorisiert konkretenInitial-Schreibumfang. Sichtbarer p3_public_operations_start.ps1
mit Section initial und neuemReceiptPath. UserZugänge einmalverdeckt, keinKEY imChat.
Nach STOPP Quittung/Frontier imHauptchat prüfen lassen. Erst mitneuemTakeoverreview/
Grant Section takeover; danach eigenerSectioninspect-Grant. JederGrant bindet seine
neuesteEntry-Datei/Frontier/Hashes; keine altenDateien/Marker zurücksetzen.

Keine tatsächlicheFreigabe durch Vorlagen, keinGrantgenerator. Keine Engine-/Strategie-
oderBackupentwicklung, C05/S006inaktiv, manuelleVorschau-Limits nicht analysiert.
Nutzer meldet Fertigstellung selbst, kein neuerChat oderFortsetzungsprompt nötig.
