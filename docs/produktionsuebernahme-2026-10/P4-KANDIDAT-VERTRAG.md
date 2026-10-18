# Deaktivierter Produktions-Teilkandidat, 13.10.2026

Basis 4bf3ad1996d8077cb9ea933da5e4cfc243f5d9a7 enthält UM2/M5, Geld-/Budget-/
Prüfer-, Store- und Backupkorrekturen. Keine erneute Übernahme dieser Commits.
Dieser lokale Branch ist ein Code-/Betriebsvorschlag, keine aktuelle Mainmigration.
Die geerbten Dateien in site/data sind alte P1-Projektionen und **keine erlaubte
Quelle für den Cutover**. Aktuelle öffentliche Byte-/Blobidentitäten und der
Workflowgraph liegen im separaten Abnahmepaket. Kein aktiver Workflow verändert.

## Explizite Bestätigungsrichtlinie

Nur BTC_DELIVERY_CONFIRMATION_POLICY=github-confirmation-v1 wählt den neuen
Produktionsclient in durable_delivery.configured_store. Ohne Auswahl bleibt der
bisherige GitHubContentsClient mit einem Zyklus erhalten. Unbekannte Auswahl,
unvollständige Richtlinie, fehlende Budgets/Journaldatei oder falsche Bindung sperren.
Config und Journal müssen absolute Pfade haben; Journal liegt außerhalb des
gesamten Runners auf dauerhaftem, einzeln schreibbarem SQLite-fähigem Datenträger.
mode=rw, BEGIN IMMEDIATE und synchronous=FULL; keine automatische Dateianlage,
Storeanlage, Migration oder lokale Versandfallbacks im Produktivpfad.

provision_journal ist ausschließlich eine explizite lokale Vorbereitungsfunktion.
Sie erstellt eine neue Datei exklusiv und bindet Repo/Branch/Store/Run/Attempt/
Code-SHA, vollständige Richtlinie und Erfassungszeit. Ein späterer echter Host
muss die gesondert geprüfte Vorbereitung und das Überleben dieser Datei belegen.
Es gibt hier keinen Scheduler, Installationsdienst oder echten Journalbootstrap.

| Grenze | Deaktivierter Vorschlag / Begründung |
|---|---|
| Bestätigungszyklen | höchstens 3, ausschließlich GET; kein weiterer PUT im Fall |
| GET je Write-Fall | 11 = 3 × (Ref + gepinnter Blob + Ref) + Parent + abschließender Ref |
| PUT je Fall | 1; zufällige Write-ID, persistenter Fallstatus, kein Response-Retry |
| GET je gebundenem Run | 640; Initialread 3 + höchstens 50 × 11 = 553, Reserve 87 für weitere reine Laufzeitreads; keine Aussage über Anbieterquoten |
| PUT je Run | 50 inklusive Claim, Nutzdaten, sending/receipt und Release; geerbtes 80%-Warnlimit bleibt |
| Requestbody je HTTP | 1.100 KiB; deckt Base64 und JSON für den geerbten 750-KiB-Storebody ab |
| Responsebody je HTTP | 2 MiB; tatsächliche Wirebytes einschließlich Whitespace, Allocation bis Limit+1; Überschreitung sperrt |
| Requestbody je Run | 60 MiB; vor PUT gesamtes Bodybudget prüfen |
| Responsebody je Run | 1.380 MiB; konservativ 690 × 2 MiB reserviert; nicht als gleichzeitiger RAM-Bedarf verstehen |
| Deadline | frisch eingegebener UTC-ms-Pin, spätestens 15 Minuten nach Journalerstellung; jede Anfrage und Antwort vor Ablauf, Uhr rückwärts sperrt |
| HTTP-Timeout | höchstens 15 s und höchstens verbleibende Deadline; kein Erfolg bei verspäteter Antwort; tatsächliche Host-Zeitbegrenzung zusätzlich offen |

Vor PUT müssen alle elf möglichen Bestätigungs-GETs und zwölf Responsebudgets
noch verfügbar sein. Jede HTTP-Anfrage wird vor dem Aufruf transaktional und
dauerhaft reserviert. Fehlgeschlagene Requests zählen mit. Die konservative
Response-Reservierung wird nicht zurückgegeben. Request-/Responsebytes bezeichnen
HTTP-Bodies, nicht Header/TLS-Overhead. Journal enthält Hash der Route, Zählung,
Bytes und Status; keine Token, Chattexte oder HTTP-Antwortbodies.

Nur die bereits geprüften Übergangsfälle vom eigenen alten zum eigenen neuen
Head dürfen reine Reads wiederholen. Erfolg verlangt eigenes kanonisches Byte-
Ergebnis, Write-ID, exakte Revision und Digestlinie, Blob-SHA, genau den eigenen
Vorgängercommit als Parent und abschließend denselben stabilen Head. Bei verlorenem
PUT-Reply gilt dieselbe Prüfung ohne erfundene Commitantwort. Alte Antworten nach
drei Zyklen, fremde Bytes/Heads, CAS-Fehler, unbekannte oder verspätete Antworten
sperren. Kein zweiter PUT und kein automatischer Takeover.

Ein reservierter Request oder offener Write-Fall nach Prozessverlust sperrt die
Factory beim Wiederöffnen. Auch ein vollständig empfangener PUT ohne abgeschlossene
Bestätigung bleibt offen. HALT ist persistent. Neuer Run/Attempt oder neue Datei
darf keine ausstehende Zustellung übergehen; der Remoteowner und sending/uncertain
bleiben zusätzliche Sperren. Klärung benötigt separat geprüfte Stilllegung und
Belegabgleich, keine Änderung dieses Journals oder Wiederholung des alten Auftrags.

## Runner, Strategie und Freigabe

tools/produktion_candidate_runner.py prüft zuerst enabled=true und anschließend
Schema, Aktivierungsreview-Pin, operation=signal/watch, alle Runtime-/Umgebungs-
Bindungen, Budgets und Configdigest. Danach geht es über produktion_runner.run_checked
und die tatsächliche Engine in configured_store. Die vorhandenen tatsächlichen
GitHub-Run-/Attempt-/SHA-/Workflowchecks bleiben wirksam. Disabled wird vor Factory,
Store, Eingabefetch oder Transport abgewiesen. Der Offlinebeweis benutzt synthetische
HTTP-/Transportfixtures und das vorhandene Engine-/Migrationsverfahren.

github-runtime.disabled.json bleibt enabled=false, mit null für echte Bindungen.
github-workflow.disabled.yml liegt außerhalb .github/workflows, Job und produktiver
Schritt sind literal false. Die vorgeschlagene spätere Workflowidentität lautet
.github/workflows/production-delivery.yml; ihr Einbau und alle Triggeränderungen
gehören in einen separat freigegebenen Aktivierungsdiff. Vorgeschlagen wird ein
geeigneter vorhandener Host mit persistentem Journal; actualHost nicht abgenommen.

C05 bleibt der inaktive Vorschlag mit Config-SHA
a99be30ae26a753f9734fbe2d67ac49f33e090a691904336421742f92420f787,
pivot_n=6, muster5_entry=true und muster_cvd=usd. S006 bleibt inaktiv als Vergleich.
Der fachliche Beleg bleibt der bedingte 785er-Vergleich. Keine neue Rangfolge,
Zukunftsrendite oder historischen Rechnungen. Vier April-Liquidationslücken bleiben
offen, ohne Nullschätzung oder andere Quelle. Keine manuelle Vorschau-/Limit-/
Fill-/Brokeranalyse. Die öffentliche Altconfig hat noch CVD alt und fehlende neuere
Parameter; diese Unterschiede sind beim konkreten Configentscheid zu prüfen.

## P4-/Rückfallentwurf – ausschließlich Review

1. Vor Entscheidung öffentlichen Main erneut pinnen und Code-/Workflowdiff zu
   diesem Kandidaten reviewen. Sämtliche alten Versender/Schreiber erfassen:
   Signal schedule/dispatch mit test/resend, Watch schedule/dispatch, Lage manuell,
   externe cron-job.org-Dispatchs, wartende/manuelle Runs, Archiv/Backtest-Schreiber
   und Pages workflow_run-/Pushfolgen. Stilllegung/Runende positiv belegen.
2. Erst nach Stillstand neuen konsistenten Snapshot aller Pflichtdateien/Journale
   aufnehmen; aktuelle state/watch/config/signals/OI bytegleich sichern. HEAD,
   vollständiger Tree und Dateiidentitäten vor/nach Aufnahme vergleichen. Dieses
   laufende Publicsnapshot und geerbte site/data ersetzen keinen frischen Snapshot.
3. B=last_signal_ts, T=belegter Stilllegungszeitpunkt, W=floor(T/4h)*4h; B muss
   W-4h sein. Unbekannte Runs, verpasste geschlossene Kerze, bestehendes neues
   _delivery oder fehlende Konsistenzbelege sperren Legacykonverter. Wenn eine
   weitere Kerze vor Start schließt, Kandidat verwerfen und Grenze frisch herstellen.
4. C05 oder eine andere ausdrücklich geprüfte vollständige Zielconfig entscheiden;
   tatsächliche Zusatzfelder/defaults und Digest binden. Alte state.config unverändert
   archivieren. Position als Signalreferenz erhalten, keine echten Lose/Kosten oder
   Stopmaxima rekonstruieren. D2: konkrete menschliche Entscheidung zu aktiver
   Altposition und Unknowns mit Belegreferenz erforderlich.
5. Offlinekonverter schreibt neues blocked-Paket; vollständige Historie erhalten,
   Legacyquittungen unknown_no_replay, keine Legacy-Outbox, kein resend-all. Watch
   bis W unterdrücken. Paket/sicheres Zweitziel/frischen blocked-Restore reviewen.
6. Erst eigene Übernahmefreigabe darf Code und blocked-Store übernehmen. Owner,
   Runbindung, persistenten Journalpfad und neue Deadline/Budgets frisch prüfen.
   Aktivierung plus Versand benötigt **separate ausdrückliche Versandfreigabe**
   mit Ziel-/Botbindung und genauem Auftragsumfang. Kein impliziter Starttest.
7. Bei HALT alle Auslöser wieder stilllegen, Runende und neuesten maßgeblichen
   Store/Journal/Backup sichern. sending bleibt uncertain; keine automatische
   Wiederholung oder Ownerexpiry. Rückfall bedeutet kompatiblen alten Code nur
   gegen den neuesten erhaltenen Versand-/Positionszustand, weiterhin blocked.
   Niemals alte state-Datei oder alten Backupstand aktivieren. Ein Restore löscht
   Erfolgsindizes und fordert Nachfolgeabgleich; frühere Sends dürfen nicht erneut
   entstehen. Ist Kompatibilität nicht bewiesen, Stillstand bleibt der Rückfall.

N-P3-01 ist lokal geschlossen (15.482 Stände); keine Wiederöffnung. Knappe
Git-Speicherreserve, Windows-Veröffentlichungsgrenze, tatsächlicher Hostbetrieb,
externer Frischealarm und geschütztes zweites Backup bleiben getrennte Gates.
