# P3 – D3 Alarm und zweite Sicherung (getrennte Vorbereitung)

Stand 04.10.2026. **Keine Einrichtung, keine Alarmprobe und kein echter
privater Backup-Write.** Der Nutzer übernimmt die Reaktion persönlich. Er nutzt
cron-job.org bereits für Dispatch, wünscht automatische Alarme und ein anderes
privates GitHub-Repository als zweites geschütztes Sicherungsziel. Die aktuelle
cron-Konfiguration, Empfänger und Fristen sind nicht nachgewiesen.

## Alarmweg: zwei verschiedene Aussagen prüfen

| Prüfer | Erfolgsbegriff | Fehlprobe |
| --- | --- | --- |
| Bestehender cron-job.org-Dispatch | HTTP-Ausführung und Aktivierung des Auftrags; Fehler-/Deaktivierungs-E-Mail an den festgelegten Empfänger. Ein 204 beweist nur Annahme des Dispatchs. | Test ohne echten Produktionsdispatch: kontrollierter Fehler/Deaktivierungs-Test an separatem Testauftrag oder dokumentiertem Wartungsfenster; Eingang, Zeit und Wiederherstellung der Benachrichtigung belegen. |
| Separater externer Frischemonitor | Dynamischer Prüfpunkt liefert nur dann Erfolg, wenn **Signal und Watch** innerhalb ihrer jeweils festgelegten Frist einen erfolgreich abgeschlossenen GitHub-Run **und** den zugehörigen dauerhaften Health-/Store-Revisionseintrag haben. Fehlender Run, nicht erfolgreicher Abschluss, veralteter Heartbeat, blockierter Store, `uncertain`, API-Fehler oder nicht lesbarer Prüfpunkt ergibt Fehler. | Für beide Arten jeweils erfolgreiche Probe und erzwungene Stale-/Failure-Probe ohne Telegram/Produktionsversand; Alarm-E-Mail, Zustellzeit und Wiederherstellung messen. |

Ein statisches Pages-Dokument und ein GitHub-API-Aufruf, der auch bei alten Runs
HTTP 200 liefert, sind kein Frischeprüfpunkt. Der Monitor muss die Antwort
**auswerten** und bei Veraltung nicht erfolgreich antworten. Ein Workflow kann
seinen eigenen ausgebliebenen Start nicht melden. Wenn cron-job.org auch den
separaten Monitor ausführt, müssen dessen Ausführungsausfall und
Deaktivierung ebenfalls alarmiert werden; die gemeinsame cron-Abhängigkeit
bleibt im Bericht sichtbar. Ein von GitHub unabhängiger Prüfer ist für
GitHub-Ausfall vorzuziehen. Der konkrete dynamische Prüfpunkt/Host ist noch
offen und wird hier nicht erfunden oder eingerichtet.

Vor Einrichtung festlegen: tatsächliche Signal-/Watch-Taktung und tolerierte
Laufzeit je Art; Frist ab erwartetem Abschluss; prüfbare Zuordnung von
Workflow-Run zu Health-/Store-Revision; E-Mail-Adresse/Verteiler,
Vertretung und maximale menschliche Reaktionszeit. Testprotokoll enthält
UTC-Zeit von erwartetem Abschluss, Erkennung, E-Mail-Eingang, Bestätigung und
Reaktion. Alarmtext nennt Stream, Art, letzte bestätigte Revision/Run-ID und
Grund, aber keinen privaten Body, Token oder Zieltext. **Keine automatische
Entsperrung** bei Alarm.

## Zweites geschütztes Sicherungsziel

Das vom Nutzer gewünschte weitere private GitHub-Repository ist noch nicht
benannt oder angelegt. Es erhält getrennte, begrenzte Schreibrechte und keine
Actions/Pages. Eine konsistente Sicherung wird an **einer unveränderlichen
Store-Commit-SHA** aufgenommen: vollständige Storedatei und Git-Historie,
Store-ID/Revision/Digest, zugehöriger Code-/Config-Pin, Migrationsbelege und
Hashmanifest. Private Inhalte dürfen weder in das öffentliche Code-Repository
noch in öffentliche CI-Artefakte geraten. Sicherungszeit, letzter erfolgreicher
Store-Commit und Sicherungsverzug werden protokolliert und überwacht.

Abnahme: Berechtigung/Privatsichtbarkeit und Historienerhalt prüfen; Manifest
gegen alle Bytes verifizieren; aus dem zweiten Repository **isoliert** in ein
neues Ziel restoren, Hashes, Commitfolge und Storeidentität nachlesen. Der
Restore bleibt `blocked` und versendet nichts. Ein verlorener neuester Commit
oder eine Diskrepanz zwischen Sicherung und maßgeblichem Store erfordert
vollständigen Zustellabgleich, keinen Rücksprung auf eine alte Kopie. Eine
Fehlprobe mit manipuliertem Hash und eine mit fehlender neuester Revision
müssen scheitern. Aufbewahrungsfrist, Takt und Restore-Intervall sind noch
festzulegen.

Ein anderes Repository beim selben Anbieter teilt GitHub-Plattformrisiko und
bei gleichem Konto auch Kontorisiko. Es erfüllt erst nach echter Schreib- und
Restoreprobe das gewählte zweite Ziel; es beweist keine Verfügbarkeit bei
GitHub-weitem Ausfall. Die vorhandene lokale P3-Bundle-Sicherung auf derselben
Platte ersetzt diese D3-Abnahme nicht.

## Offene Entscheidungen vor Ausführung

1. Konkreter externer Frischeprüfpunkt und Betreiber, tatsächliche Signal-/
   Watch-Fristen und Probe für ausgebliebene **erfolgreiche Abschlüsse**.
2. Alarm-E-Mail-Ziel, Vertretung, Reaktionsfrist und Freigabe einer gefahrlosen
   End-to-End-Alarmprobe.
3. Name/Eigentümer des zweiten privaten Repositorys, getrennte Rechte,
   Sicherungstakt, Aufbewahrung und Restore-Intervall; gesonderter Auftrag für
   Einrichtung und echte Sicherungsprobe.

Bis diese Belege vorliegen, bleibt D3 offen. P4 benötigt zusätzlich den
frischen stillgelegten Snapshot und eine ausdrückliche Live-Entscheidung.

Quellen: [cron-job.org REST-Benachrichtigungseinstellungen](https://docs.cron-job.org/rest-api.html),
[cron-job.org Statusbenachrichtigungen](https://cron-job.org/en/),
[GitHub Workflow-Runs API](https://docs.github.com/en/rest/actions/workflow-runs).
