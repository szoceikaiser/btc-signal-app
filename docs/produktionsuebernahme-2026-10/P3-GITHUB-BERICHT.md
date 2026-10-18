# P3 – GitHub-Weg, Offline-Adapter und offene Betriebsabnahme

Stand 04.10.2026. **Keine Live-Freigabe.** D1 wurde vom Nutzer ausdrücklich als
GitHub beantwortet. Paket G ist daher die einzige P3-Anbindung; H wird nicht
gebaut. Es wurden kein privates Repository, Token, Dienst oder reale Store-API-
Schreibvorgänge eingerichtet. Die aktiven Versandworkflows bleiben unverändert.

## Gelieferter lokaler Adapter

`engine/github_delivery.py` enthält einen Contents-API-Client und einen v2-Store
mit einem einzigen Owner für alle Pfade. Die Storedatei wird nur an einer
expliziten Branch/Repo-Identität gelesen und mit der vorigen Blob-SHA bedingt
aktualisiert. Der Inhalt enthält Revision, parent-Digest, eigene write_id,
Body-Digest und den vollständigen Snapshot. Jeder Schreibschritt wird anhand
des aktuellen Branchkopfs und des Commit-Parents nachgelesen. Ein Timeout nach
PUT darf nur bei exakt bestätigtem eigenem Inhalt als Erfolg gelten. Eine
abweichende Antwort, fremder Owner, veraltete SHA, nicht erreichbarer Store
oder überschrittenes Budget stoppt den Lauf; kein lokaler/Git-Rückfall.

Die gemeinsame Store-Fabrik in `durable_delivery.py` verlangt für G explizite
Repo-/Branch-/Run-/Token-Identität und verbietet ein gleichzeitig gesetztes
lokales Store-Volume. Die produktive `produktion_runner.py`-CLI bleibt weiterhin
unzugänglich; `run_checked` ist nur ein späterer Eingang. Die Vorlage unter
`ops/produktion/` liegt außerhalb `.github/workflows` und hat `if: false`.
Eine spätere Aktivierungsdiff muss alle alten und neuen Auslöser gemeinsam
prüfen. GitHub-`concurrency` ist nur eine zweite Begrenzung: standardmäßig kann
ein neuer wartender Lauf einen alten wartenden ersetzen, daher bleibt der
Store-Owner maßgeblich.

`review_takeover` ist nur eine explizite Wartungsoperation mit erwarteter
Revision/Owner und belegtem beendetem Altlauf, gestoppten Workern und
stillgelegten Auslösern. Sie stellt überlebendes `sending` im selben Commit
auf `uncertain`, gibt aber keine Zustellung ohne positiven externen Beleg frei.
Diese Angaben sind derzeit Operatorbelege; eine echte Run-/Workerprüfung ist
noch nicht implementiert oder abgenommen.

Lokale Fake-API-Gegenfälle prüfen zwei Claims, sauberes Unlock, Timeout vor und
nach PUT an Claim/Intent/sending/Quittung/Unlock, verzögertes Lesen, veraltete
Blob-SHA, Parent-Abweichung nach Historienumschreibung, 404/403/429,
Identitätsfehler, nicht belegten und belegten Ownerwechsel, globale
`uncertain`-Sperre, Mirrorverlust sowie 750-KiB-/50-Schreibgrenzen. Ein
synthetischer P1-Fixture-Snapshot maß 16 600 Byte im Store-Envelop; Claim und
Unlock benötigten zwei schreibende Requests. Das ist **keine** Größen- oder
Requestmessung eines frischen main-Snapshots. Historie wird bei Grenzfehlern
nicht gekürzt.

Die vollständige lokale Engine-Suite nach der Adapteränderung lief mit UTF-8:
**820 bestanden, 0 Fehler**. Die Tests nutzen ausschließlich lokale Fakes und
synthetische Belege. Exakte Commit-/CI-/Restore-Nachweise werden additiv
außerhalb dieses Berichts abgelegt.

## D3: Entwurf mit vorhandener Infrastruktur

Der Nutzer übernimmt persönlich die Reaktion auf Alarme und unklare
Zustellungen. Der konkrete E-Mail-Empfänger, Vertretung und überprüfte
Reaktionszeiten sind noch offen. `cron-job.org` ist bereits als Dispatch-
Auslöser dokumentiert; seine aktuelle Konfiguration wurde nicht ausgelesen.
Empfehlung: dessen Fehler-/Deaktivierungs-E-Mails aktivieren und ergänzend einen
**getrennten Frischemonitor** benutzen, der den erfolgreichen Abschluss eines
Signal-/Watch-Laufs samt Health/Store-Revision innerhalb der Frist prüft. Ein
HTTP 204 des Dispatchs allein belegt nur dessen Annahme. Ein bloßer GitHub-
Workflow kann seinen eigenen ausgebliebenen Start nicht melden. Der Monitor
benötigt einen externen Prüfpunkt, der bei veraltetem Status einen Fehler
liefert; ein statisches Pages-Dokument oder ein stets mit 200 antwortender
GitHub-API-Aufruf genügt nicht. Ein solcher Prüfpunkt wurde nicht eingerichtet.

Der Nutzer nennt ein weiteres privates GitHub-Repository als mögliches zweites
geschütztes Sicherungsziel. Entwurf: konsistente Sicherung der Store-Commit-SHA
mit vollständiger Historie, Code-/Config-/Migrationsbelegen und Hashmanifest in
ein separates privates Repository mit getrennt begrenztem Schreibrecht;
regelmäßiger isolierter Restore ohne Transport. Dieses Ziel teilt GitHub als
Plattform und bei gleichem Konto auch dessen Zugriffsrisiko. Es bietet daher
keinen Nachweis gegen GitHub-weiten Ausfall oder Kontoübernahme. Repository,
Rechte, Schutz und Probe sind noch offen; kein echtes Backup wurde geschrieben.

GitHub dokumentiert [E-Mail-Benachrichtigungen für gestartete Läufe](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs)
und [Verzögerung/Verlust geplanter Läufe](https://docs.github.com/en/actions/tutorials/manage-your-work/close-inactive-issues).
`cron-job.org` dokumentiert [Fehler-E-Mails](https://cron-job.org/en/faq/)
und [Benachrichtigungseinstellungen](https://docs.cron-job.org/rest-api.html).
Die Folgerung zum fehlenden Abschluss ist eine Betriebsableitung aus diesen
Grenzen, kein zugesagter Dienstumfang.

## Für weitere P3-/P4-Abnahme offen

- Echtes privates Store-Repository, begrenzte Rechte und getrennte API-Probe
  mit ausschließlich synthetischen Daten; insbesondere zwei Schreiber,
  bedingte Updates, Commit-Lesebestätigung und Branch-/Rechtefehler.
- Frischer vollständiger main-Snapshot zur Größen-/Requestmessung erst nach
  späterer Stilllegung; D2 gilt nur für genau diesen konkreten Zustand.
- Konkreter unabhängiger Frischemonitor, E-Mail-Ziel, Test eines ausgebliebenen
  Laufs und eine benannte Reaktionsfrist. Die Nutzerrolle allein beweist noch
  keinen funktionierenden Alarmweg.
- Zweites privates Sicherungsrepository mit begrenzten Rechten, geschützter
  Geschichte, Hashmanifest und echter isolierter Restoreprobe. Gemeinsames
  GitHub-Ausfallrisiko bleibt ausdrücklich benannt.
- P4: alle alten Trigger und wartenden Läufe stilllegen, frischen Cutover,
  aktuelle Store-Revision, externe Zustellbelege und ausdrückliche Live-Freigabe.

Unverändert: ein Store/ein Owner, Intent und `sending` vor Transport, Quittung
danach, `uncertain` blockiert neue IDs und Auswertung. Kein Reset, keine
Exactly-once-Zusage, keine historische Nachsendung. T1, volle Historie, B/W,
`alt → usd`, E42/Short aus und Public Export nur per Allowlist. P1 und
RENDITEN-Dateien bleiben eingefroren.
