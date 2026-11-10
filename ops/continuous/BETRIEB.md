# Betriebspaket: Überwachung und begrenzter Wiederanlauf

Vorbereitung, keine Aktivierungsfreigabe. Die Strategie bleibt auf Core20D.
Die bestehende historische Abbruchwartung ist unabhängig und verbraucht;
ihre Journale, Marker, Quittungen und unveränderlichen Snapshots bleiben liegen.

## Automatisch zulässiger Fall

`continuous_operations.py` kann genau eine offene Fence schließen, wenn der
zugehörige Signal-/Watch-Lauf seine erfolgreiche fachliche Abschlussrevision
bereits gespeichert hat, der Owner null ist und jede Zustellung eine positive
Quittung mit passender Zielbindung und genau einem Versuch besitzt. Die
historische Abschlussrevision wird anhand ihres tatsächlichen Git-Commits und
der Abstammung gelesen. Run und alle Jobs müssen abgeschlossen und auf dem
bekannten GitHub-hosted Runner sein; sämtliche fünf Queuefilter bleiben leer.
Schutzregeln, Repositoryidentitäten und tatsächliche Workflowbytes werden vor
der Mutation erneut gegen den vorhandenen Review geprüft.

Das Werkzeug verändert keinen Stream, übernimmt keinen Owner und sendet nichts.
Es startet keinen Workflow und ersetzt keinen Slot. Die Closure enthält einen
expliziten Recoverybeleg. GitHubs failure bleibt failure. Monitor und Pages
verweigern diesen Übergang als Gesundnachweis. Nur ein späterer neuer regulärer
Signal-/Watch-Slot darf über den tatsächlichen Actions-Einstieg wieder eintreten.
Die vorhandenen Run-/Cursor-/Versuchprüfungen bleiben bestehen.

Lebender/fremder Owner, sending/uncertain, fehlende Quittung, fehlende fachliche
Abschlussrevision, Self-hosted Worker, wechselnde Heads oder unvollständige
Schutz-/Runbelege bedeuten STOP und Alarm. Kein TTL-Takeover, keine neue
historische Wartung, kein Nachsenden. Der sichere Betrieb bleibt verfügbar,
indem Diagnose und Alarm weiterlaufen; Sends bleiben gesperrt.

## Dauerhaftes Versuchbudget

Der Incident ist der exakte alte Fencecommit. Auf einem stabilen Betreiberhost
liegt genau eine Datei `<state-dir>/<incident>.sqlite`. SQLite synchronous FULL
reserviert die exakten Kandidatenbytes vor dem einzigen PUT. Nach Neustart oder
verlorener Antwort werden zuerst tatsächliche Bodies, Heads und direkte Eltern
gelesen. Gespeicherter Kandidat: bestätigen, kein weiterer PUT. Alter Zustand
nach unklarer Antwort: STOP, Versuch verbraucht. Fremder Zustand: STOP.

Maximal 160 GET, ein Fence-PUT, drei Sekunden pro HTTP-Anfrage, 2 MiB pro
Response und 15 Minuten unverlängerbare Incidentfrist. Reads und Deadline
bleiben im Journal. Ein neuer Prozess setzt sie nicht zurück. Kein ephemerer
GitHub-Runner als Journalhost, keine automatische Journalrotation oder
Neuanlage für denselben Incident nach Verlust. Ein erneutes CLI mit anderem
State-Verzeichnis ist kein zulässiger Restart. Nach Budgetende separat rein
lesend untersuchen, niemals neues Budget durch neues Verzeichnis erzeugen.

## Tatsächlicher Einstieg

Der unveränderte Strategie-Core wird durch den erweiterten, exakt gehashten
Loader geladen. Der neue Toolpfad ist ebenfalls Teil des Extension-Manifests:

```text
python tools/pinned_delivery_entry.py --core <clean-Core20D> --extension <release>
  --manifest-sha256 <reviewed-manifest> --tool continuous_operations.py --
  --policy <reviewed-recovery-policy.json> --state-dir <persistent-state>
  --incident-fence <actual-open-fence-commit> --result-file <new-evidence.json>
```

Ohne `--execute` ist dies eine lokale Vorschau ohne Journal oder Netzwerk.
Die Resultdatei muss neu sein. Der Loader unterdrückt ungeprüfte Toolausgabe;
die geprüfte Resultdatei enthält nur kontrollierte Zustände und Commitbelege.
Erst mit zusätzlichem `--execute` und ausdrücklich freigegebener Policy kann
der eine PUT erfolgen. Der Storezugang kommt dann aus dem vorhandenen
`BTC_DELIVERY_GITHUB_TOKEN` des freigegebenen Hosts. Kein Credential wird durch
dieses Paket erzeugt, aus GitHub gelesen oder in Journal/Result gespeichert.

Die automatische Auslösung und sichere Credentialbereitstellung auf einem
dauerhaften Betreiberhost sind noch separat zu integrieren und abzunehmen.
Das Paket stellt keinen bereits laufenden Recoverydienst dar.

## Aktivierungsfolge für den Hauptchat

1. Main, laufende Jobs, alle externen Aufträge, GitHub-Pausen und tatsächliche
   Store-/Fenceheads neu lesen. Historische Belege sind kein heutiger Zustand.
   Den erfolgreichen Signal-/Watch-/Pages-Abnahmestand vom 10.11. erhalten.
2. Pausenbuch mit belegten UTC-Anfangs-/Endgrenzen vervollständigen und als
   Betriebshistorie dauerhaft sichern. Die alte Ausfallzeit bleibt sichtbar.
   `first_start_ms` wird durch dieses Paket nicht geändert. Keine alten Slots
   nachholen und keine Überwachungsgrenze zum Verbergen von Fehlern versetzen.
3. Code und fünf neue Reviewstrings bei weiter pausierten Betriebsstartern
   veröffentlichen, Gitbytes und Variablen unabhängig zurücklesen. CI bleibt
   aktiv; grünes CI allein ersetzt die Betriebsprüfung nicht.
4. Unabhängigen Verifier und Sicherungshersteller freigeben, eine frische
   vollständige Sicherung/Quittung samt unabhängigem Download und blockierter
   Rücksicherung abnehmen. Aktuelle Quittung und beide Historien prüfen.
5. Pages vor den neuen Signal-/Watch-Quelläufen freigeben. Signal und Watch nur
   für kommende echte reguläre Slots freigeben; Archiv gemäß bestätigtem
   bestehendem Zeitplan. Lage ist manuell, Backtest getrennt. Keine historischen
   Runs erneut starten. Den ersten neuen Zyklus einschließlich Nutzerempfang
   und Pagesstand konkret prüfen.
6. Vollständigen Frischeprüfer alle zehn Minuten freigeben. Cloudflarequelle
   mit den neuen Workflow-/Policyhashes veröffentlichen, aktuelle Plattform
   unabhängig zurücklesen und echten positiven `/health`-Pfad abnehmen.
   Erst danach externen Alarmjob 8671736 auf Minute 3,13,23,33,43,53 aktivieren.
   Bestehenden E-Mail-Empfänger unverändert übernehmen und Zustellung testen.
7. Recoveryautomation bleibt aus, bis stabiler Journalhost, Rechtebindung,
   Secretinjektion, Trigger und Betriebshistorie separat abgenommen sind.

## Zeitpläne und Grenzen

Historische feste UTC-Verträge: Signal :02 und :32 alle vier Stunden; Watch
:08/:23/:38/:53. Keine native zusätzliche GitHub-Cronquelle hinzufügen. Producer
8671686 und Verifier 8671690 behalten den frisch zu bestätigenden bestehenden
Tagesplan; Quittung höchstens 26 Stunden gültig. Monitor 8671707 alle zehn
Minuten. Externer HTTP-Prüfer 8671736 jeweils drei Minuten danach. Die beiden
Healthaufträge 8664392/8671736 wurden zuletzt als inaktiv beschrieben;
8664392 nicht stillschweigend aktivieren. Die sechs regulären Aufträge sind
8462318, 8663295, 8663306, 8671686, 8671690, 8671707.

Nach Ablauf einer fachlichen Frist: höchstens circa zehn Minuten bis zum
nächsten vollständigen Check, plus bis zu drei Minuten zum externen Check,
plus tatsächliche GitHub-/Provider-/Mailverzögerung. Fehlender Monitor selbst
führt ebenfalls zu HTTP503. Watch-Frist 15 Minuten, Signal bis :45 nach
Kerzenschluss. Kein garantiertes SLA. Close-only-Recovery nach Auslösung
höchstens 15 Minuten; nächster neuer Watchslot höchstens 15 Minuten, nächste
Signalphase höchstens vier Stunden. Vollständige grüne Monitorhistorie kann
bis zur nächsten erforderlichen Signalphase dauern; nicht künstlich begrünen.

Monitor maximal 80 GET/30 Sekunden je Lauf, sechs Läufe/Stunde. Externer Worker
maximal drei GET, davon zwei öffentliche Core-API-Reads, je Probe. Recovery
nicht alle zehn Minuten voll gegen dasselbe Incident pollend starten, sondern
einmal bei belegtem Incident; eine Reservierung bleibt dauerhaft verbraucht.
Anonyme Corequote, geteilte Provider-IP und GitHub-Jobquoten vor Aktivierung
aktuell messen; keine zweite Tokenrolle als Quotenbypass.

## Konkrete Liveabnahme und wiederkehrende Probe

- Fehleralarm durch kontrolliert fehlende Monitorobligation und Ausfall des
  Cloudflare-Endpunkts getrennt prüfen; tatsächliche Mail an bestehenden
  Accountempfänger bestätigen. Cron-204 bedeutet nur angenommenen Dispatch.
- Sicheren Close-only-Fall zuerst in isolierter Testumgebung mit denselben
  Berechtigungen/Journalhost prüfen, inklusive Prozessende nach gespeichertem
  PUT und Neustart. Keine Produktionszustellung absichtlich unklar erzeugen.
- Nach jedem Release sowie mindestens monatlich frisches Backup unabhängig
  herunterladen und mit regulärem P4-Restore in ein neues lokales Git-Repo
  zurücksichern. Quittungen, Cursors, historische aborted-/recovery-Belege und
  RESTORE-BLOCKED prüfen; daraus niemals direkt einen Sender starten.
- Monatsprobe und Alarmbestätigung terminieren/zuweisen; das ist in diesem
  lokalen Paket noch keine aktivierte Scheduleraufgabe.
