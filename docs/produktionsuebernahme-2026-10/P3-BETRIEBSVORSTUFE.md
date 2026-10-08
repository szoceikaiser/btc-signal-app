# Lokale P3-Betriebsvorstufe – 08.10.2026

Basis ist Engine-HEAD `4ea6bb377d71940fd50d789dff178fcf0719a3b9`, Baum
`79941674ee2129a091cbde1d3388744d260f0993`. Eigener Zweig
`codex/p3-betriebsvorbereitung`. Keine externe Probe, Betriebsabnahme oder P4-Freigabe.

## Abschlussvertrag

Signal und Watch benötigen Repository, Workflowpfad, tatsächliche Run-ID und
Attempt sowie einen ausdrücklich übergebenen erwarteten UTC-Starttermin. Bei
GitHub prüft `run_checked` außerdem die tatsächlichen `GITHUB_*`-Variablen gegen
diese Bindung. Runtimekonfiguration, Code-, Store- und Streamidentität bleiben
gepinnt. Fehlende Metadaten führen vor der fachlichen Verarbeitung zum Halt.

`run_health.record_event` speichert Start und Status. Für einen erfolgreichen
Abschluss müssen alle Nachrichten bestätigt und der Stream aktiv sein. Watch
braucht eine tatsächlich beobachtete aktuelle Kerze und genügend Eingabekerzen;
ein leerer Datenabruf darf keinen Erfolg erzeugen. Ein Watch ohne Warnung kann
erfolgreich sein. Signalfrische verlangt zusätzlich die richtige zuletzt
ausgewertete **geschlossene** Kerze.

Der Abschluss erfolgt in zwei Schritten unter derselben Sperre:

1. Abschlusskandidat mit Run/Attempt/Nonce, Code-/Config-/Store-/Streamidentität,
   Start-/Endzeit und bekannter numerischer nächster Revision. Schreiben und
   exaktes Readback bestätigen. Keine eigene noch unbekannte Commit-SHA im Body.
2. Eine weitere bestätigte Revision speichert den Locator des vorigen Abschlusses:
   Revision und Snapshotdigest, bei GitHub zusätzlich Repository/Branch/Pfad,
   Commit- und Blob-SHA. Erst nach Bestätigung dieses Schreibens ist die Bindung
   dauerhaft. Anschließend erfolgt beim GitHub-Schreiber die bestätigte Freigabe
   des Owners. Ein Monitor akzeptiert keinen noch gehaltenen Owner.

Der Monitor liest den Abschluss an seinem unveränderlichen Commit nach und prüft
auch, dass er Vorfahr des konsistent gelesenen aktuellen Storeheads ist. SQLite
speichert Abschlussrevisionen in `health_revisions` innerhalb derselben
Transaktion; jede Aktualisierung hat Readback. Die aktuelle Health enthält pro
Art einen begrenzten Index von acht Terminen plus den neuesten Abschluss. Dies
ist ausschließlich ein Lookupindex: Git-Historie, SQLite-Abschlussrevisionen,
Signalhistorie und Nachrichtenjournal werden nicht gekürzt.

Eine nicht bestätigte zweite Speicherung hinterlässt höchstens einen Kandidaten;
eine alte Bindung legitimiert den neuen Run nicht. Nach Prozessverlust können
GitHub-Metadaten selbst einen bereits gespeicherten Abschluss als fehlgeschlagenen
Run ausweisen: auch dann 503. Fehler oder Unklarheit erlauben keinen Replay.

## Fristen und read-only Prüfung

`freshness.evaluate` bewertet vollständige Metadaten, konsistente Storebytes und
geprüfte Sicherungsmetadaten; `check_github` bindet die GET-Leser ein. Zu Beginn
und Ende werden Storehead und Run-Metadaten verglichen. Änderungen während der
Prüfung sind unklar und ergeben 503. `GitHubStore.__enter__` wird dabei nie benutzt.
SQLite liest mit `mode=ro` in einer Snapshottransaktion, ohne Mutexmutation.

Es gelten explizite UTC-Perioden, Phasen und erste erwartete Termine:

| Art | Bisheriger Zeitplan als Vorschlag | Alarmgrenze |
| --- | --- | --- |
| Signal | 00/04/08/12/16/20 Uhr, jeweils Minute 02 | 45 Minuten nach **Schluss** der zugehörigen 4h-Kerze; Dispatchminute 02 verschiebt diese Grenze nicht |
| Watch | Minuten 08/23/38/53 | 45 Minuten nach dem jeweiligen erwarteten Prüftermin |
| Lauf | Tatsächlicher Laufstart | Mehr als 15 Minuten Laufdauer |
| Backup | Täglich, konkrete Phase offen | Mehr als 26 Stunden seit dem erwarteten Sicherungstermin, nicht seit verspätetem Readback |

Beispiel: Schluss 12:00, Signalstart 12:02, Signalgrenze 12:45 UTC.
`Candle.ts=08:00` bezeichnet die **Öffnung** dieser geschlossenen Kerze. Watch
12:08 hat die Grenze 12:53 UTC. Das sind tolerierte Ausfallgrenzen und keine
absichtlichen Wartezeiten. Fehler, unklare Zustellung und unvollständige oder
laufende neue Runs sind bereits vorher unhealthy. Konservatives 503 auch während
eines neuen, noch nicht bestätigten Laufs kann eine kurze Fehlermeldung erzeugen;
dieser Punkt ist in der späteren Alarmprobe ausdrücklich zu prüfen.

Der Prüfer verlangt den **konkret fälligen Termin** und den neuesten Run. Ein
späterer Watch-Erfolg verdeckt damit keinen ausgelassenen fälligen Termin. Bei
einem Monitor alle fünf Minuten und Watch alle 15 Minuten wird jeder solche
Fehler im offenen Fristfenster beobachtbar. Längere Monitorlücken garantieren
keinen rückwirkenden Alarm; cron-Ausfall ist eine gemeinsame Abhängigkeit.

GitHub-Metadaten werden ohne Erfolgs-/Branch-/Headfilter gelesen, damit neuere
Fehler und falsche Identitäten sichtbar bleiben. Spätere separate Workflows
müssen `run-name: p3:<kind>:<dispatch_epoch_seconds>` aus ihrem Dispatchinput verwenden.
cron-job.org ersetzt `%cjo:unixtime%` im Body durch den Zeitpunkt des Aufrufs
in Unixsekunden. Der gemeinsame reine Helfer `dispatch_slot` ordnet ihn dem
gepinnten UTC-Termin zu und lehnt Dispatchs außerhalb der ersten zwei Minuten
nach dem Starttermin ab. Der Workflow setzt daraus `BTC_DELIVERY_EXPECTED_START_MS`.
Der Monitor rechnet unabhängig denselben Termin aus dem Run-Titel nach.
Das verhindert das Erraten des Watch-Termins aus einem verspäteten Start. Dieses
Schema ist ein lokaler Vertrag; vorhandene aktive Workflows sind unverändert.
Der Attempt wird im Run und in der attemptgebundenen Jobliste geprüft. Die
Job-Abschlusszeit wird gelesen; `updated_at` gilt nicht als Abschlussbeweis.

Die Antwort enthält nur `schema`, `healthy` und eine feste Fehlerklasse, außen
HTTP 200 oder 503. Keine privaten Bodies, Zieltexte, Tokens oder Mailadressen.
Der alte SQLite-CLI ohne externe Metadaten bleibt ein Diagnosewerkzeug und meldet
jetzt ausdrücklich `external_run_binding_unverified`, niemals gesunden Betrieb.
`produktion_freshness.py --offline --fixture ...` erzeugt nur lokale Entscheidungen.
Kein Listener, Host, Alarmtransport oder Credentialabruf wird gestartet.

## Grenzen

Store: höchstens 768.000 unkodierte Bytes und 50 PUT-Versuche je Run; Warnung bei
80 Prozent. Fake-Probecontroller zusätzlich höchstens zwölf PUTs. Health erhöht
den Laufbedarf um drei bestätigte Writes (Start, Abschluss, Attestation), neben
Claim/Freigabe und fachlichen Writes. Vollständige Historien bleiben erhalten;
am Größenlimit wird angehalten. Fixturebytes sind keine Produktionsmessung.

Monitor: höchstens 32 GETs, 2 MiB Antwortbytes je Request, drei Sekunden
Requesttimeout, 20 Sekunden Gesamtbudget. Maximal 100 Runs je Art, bei gefüllter
100er-Seite oder unvollständiger Ergebnismenge Halt; höchstens 20 Jobs und keine
fehlende Seite. Typischer vollständig gesunder Durchlauf mit zwei benötigten
Terminen je Art: bis zwölf Metadaten-GETs, acht Abschluss-GETs (Compare/Contents),
sechs Store-GETs und fünf Backup-GETs (Quittung plus Quellpin) = 31. Die getrennt
berechtigten GET-Clients müssen **denselben `ReadBudget`** verwenden. Keine automatische Wiederholung,
Pagination oder Cachegesundheit. Ein langsamer oder großer Compare führt zu 503.

`ReadOnlyClient` hat keinen Schreibpfad und enthält keine Credentialsuche. Der
spätere Host muss `http_status` als echten Status setzen, `Cache-Control: no-store`
verwenden und Ausnahmen/Timeout ebenfalls auf 503 abbilden. Ein gespeichertes
200 darf keine spätere Prüfung ersetzen. Der Host ist in P3 weiterhin ungewählt.

Owner verfällt nicht. Kein zeitbasiertes Stehlen, kein Exactly-once-Versprechen,
kein Reset von Zustellung oder neue ID als Umgehung. Intent und sending liegen
vor Transport, Quittung danach. Überlebendes sending wird nach belegtem Runende
und kontrollierter Übernahme uncertain; nur positiver externer Zustellbeleg darf
klären. SQLite-Prozessverlust-/Runnerverlusttests und GitHub-Fakegegenfälle bleiben
Teil der Regressionen. C05/S006, native UM2-/M5-Gates und exakte Geldrechnung bleiben
erhalten. Kein neuer historischer Strategie- oder Renditelauf.

Separate externe Pläne stehen in `P3-EXTERNE-PROBENPLAENE.md`; offene Angaben und
Freigaben in `ops/produktion/p3-acceptance.disabled.json`. Alle sind Vorschläge.

Die [cron-job.org-Variablen](https://docs.cron-job.org/creating-cron-jobs.html)
liefern Ausführungszeit, nicht geplante Zeit. Geplante Zeit und Jitter sind
deshalb in der späteren cron-Probe getrennt zu prüfen. Keine stillschweigende
Behauptung über die aktuelle Kontokonfiguration.
