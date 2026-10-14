# Deaktivierter GitHub-Actions-Kandidat

Modellauftrag: gpt-6.1-sol, high. Basis: abgenommener Kandidat 6b600c71.
Keine neue Strategieentscheidung. Alle Runtimepins bleiben null/disabled.
Der Workflow liegt außerhalb aktiver Workflows, mit literal false. Kein Server.

Die bestehende Factory benutzt bei explizitem `github-actions-fence-v1` nur
den Client des gerade zugelassenen Runtimeprozesses. Kein direkter Aufruf,
kein SQLite-/Cache-/Artifact-Fallback. Die bisherige Richtlinie bleibt für
frühere Belege verfügbar; eine fehlerhafte Actionsauswahl fällt niemals darauf zurück.

## Dauerhafte Autorität

Geschütztes bestehendes GitHub-Repository, zwei dedizierte Branches:

- Storebranch: unverändert ausschließlich `delivery/stream.json`. Bestehende
  CAS-/Owner-/sending-/uncertain-/Revisions-/Runhealthmechanismen bleiben maßgeblich.
- Sperrbranch: ausschließlich `delivery/actions-fence.json`, höchstens 8192 Bytes.
  Ein fest gebundenes Deployment und der letzte Run, offen oder abgeschlossen.
  Keine TTL, kein automatisch zurückgesetzter Zähler, keine Wiederaufnahme.

Die Runtime prüft tatsächliche Code-Repo/Ref/Workflow/Run-ID/Attempt/Runnummer,
sauberen Checkout-HEAD, effektive Config, Bot und Store-/Sperrbranch gegen Pins.
Deployment und Budgets liegen in der Sperre; das Runobjekt bindet zusätzlich
Operation, erwarteten Startslot und Deadline. Attempt muss 1 sein. Die Runnummer
muss größer als die letzte dieses fest gebundenen Workflows sein. Umbenennung,
Reset oder Code-/Configwechsel benötigt gestoppte Schreiber und explizite
Maintenance; kein Lauf verändert die Deploymentbindung automatisch.

Vor jeder Engine-/Fetch-/Transportoperation: konsistenter Sperrread, genau ein
CAS-PUT auf open, eigene exakte Bytes plus Write-ID, eigener Commitparent und
abschließender stabiler Head. Erst danach ist die Factory zugelassen. Alle ihre
Aufrufe teilen denselben Request-/Byte-/Zeitbudgetzähler. Ein Prozessverlust
verliert Zähler, aber die offene Sperre verbietet jedem Ersatzprozess weitere
fachliche Requests. Vor einem erfolgreichen Claim gibt es keinen fachlichen
Write oder Versand. Concurrent claim kann höchstens einen CAS-Gewinner haben.

Nach bestätigtem Engineabschluss, freigegebenem Storeowner und passendem
erfolgreichem Runhealthbeleg: frischer Storepin und Sperrread, genau ein CAS-PUT
auf closed. Es folgen ausschließlich dessen Bestätigungsreads. Keine fachliche
Operation nach dieser Abschlussmutation. Gleiche/ältere Runs werden auch nach
closed abgelehnt. Ein neuer Run verarbeitet den neuesten Storezustand.

Offene Sperre, fehlende Datei/Branch, ungewisse Mutation, ungewisser Versand,
Deadline/Budgetbruch oder falsche Pins: Halt und Operatorreview. Kein Recreate,
Age-Takeover, PUT-Retry oder Resend. Maintenance benötigt stillgelegte Trigger,
positiv beendete alte Worker und neuesten Store-/Sperrpin; unbekannte Quittungen
bleiben unbekannt. Es wird hier kein Maintenance-Livewerkzeug freigegeben.

## Drei ausgewählte Bestätigungszyklen und Kosten

`confirmation_cycles=3` bleibt ausdrücklich gewählt. Pro fachlichem Fall genau
ein PUT, höchstens 3 reine konsistente Readzyklen (je 3 GET), danach Parent-GET
und Schlusshead-GET: maximal 11 GET pro Write. Dieselbe Grenze gilt für beide
Sperrmutationen; dort bleibt bewegter Head konservativ ein Fehler. Kein
automatischer Wechsel zu einem Zyklus. Alte/unbestätigte Writes sind kein Erfolg.

Zusatz pro vollständig abgeschlossenem Run: zwei Sperr-PUT, zweimal initiale
Sperrreads (6 GET), zwei Bestätigungen (10 bis 22 GET) und der abschließende
Storepin (3 GET): **19 bis 31 GET + 2 PUT**. Kein Gitrequest im Runtimepfad.
Sperrpayload je PUT konservativ unter 24 KiB (Base64 des 8-KiB-Files plus
Branchname und JSON; dessen tatsächliche Bytes zählen vollständig).
Bestätigungsresponses werden
innerhalb derselben 2-MiB-Reservierung wie Storeantworten gezählt.

Gesamtrun einschließlich Zusatz: GET <=640, PUT <=50 (also höchstens 48
fachliche PUT), HTTP-JSON-Requestbody <=1,126,400 Bytes pro Request / 60 MiB pro
Run, Responsebody <=2 MiB pro Request / 1380 MiB reserviert pro Run. Pro Fall
1 PUT/11 GET; vor PUT vollständige Worst-case-Readreserve. Fehlerrequests zählen
mit. Oversize liest höchstens ein zusätzliches Sentinelbyte, dann Halt.
Headers/TLS sind keine behaupteten Bodybytes. Timeout <=15s und <=Restdeadline;
Run <=15min ab Start, GitHub-Job zusätzlich timeout-minutes15. Markt-/Transport-
Grenzen bleiben die geerbten Grenzen; die neue Zählung umfasst Store und Sperre.

Das kleine Sperrfile wächst nicht mit Requests/Runs. Git erzeugt zwei zusätzliche
Commits pro fertigem Run auf dessen getrenntem Branch; Historienwachstum ist
eine echte Kapazitätsfrage, kein kostenloses unbegrenztes Hilfsjournal. Unter
48 fachlichen PUT/640 GET darf ein Lauf früher stoppen, wenn seine volle
Reserve fehlt. Verlust vor Abschluss hält die Sperre offen und kostet Betriebspause.

## Vorbereitung und spätere praktische Gates

`produktion_actions_prepare.py --runtime VOLLSTAENDIGE_DATEI --out NEUE_DATEI`
erzeugt ausschließlich lokale Sperrseedbytes, exklusiv und ohne HTTP. Die
gelieferte Nullpin-Runtime wird abgelehnt. Kein bestehender Sperrbranch darf aus
alten Seed-/Backupbytes neu eröffnet werden. Spätere Bootstrap-/Berechtigungs-
entscheidung separat mit frischem stopped-Snapshot, gebundenem Code/Config und
geschützten Branches. Workflowvariablen enthalten reviewed Runtime und Config;
Projektionen liegen unter `.runtime/data`, nie geerbtes `site/data` als Input.

Vor P4: Checkoutaction auf geprüften Commit pinnen, tatsächliches hosted Image /
Python prüfen, Workflowref/Runnummer/Concurrency sowie Rechte und reale
CAS-/Visibility-/Crashfälle auf GitHub gezielt abnehmen. Die literal false und
der explizite Disabled-Abweisungsschritt sind bewusste Aktivierungssperren; das
fertige P4-Paket muss deren Änderungen ausdrücklich reviewen. Keine neue
Testkampagne oder echte Probe in diesem Auftrag.

Bestehende v2-Backups bleiben für den unveränderten Storebranch nutzbar. Sie
prüfen exakt einen Stream pro Commit und sind **nicht** der Sperrbranchbackup.
Die zweite geschützte Sicherung braucht zusätzlich dessen vollständiges Bundle,
aktuellen Sperrpin und eine Quittung zum im closed-Beleg referenzierten Storepin.
Ein Restore bleibt blocked; ungewisse/offene Sperren werden nicht cleared.
Die bereits abgenommene Kapazität wird dadurch nicht rückwirkend erweitert.
