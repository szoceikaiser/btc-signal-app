# Ergänzung zum Betriebspaket: GitHub-Recovery

Diese Ergänzung ersetzt die Aussage, dass ein zusätzlicher Dauerhost nötig sei.
Automatischer Auslöser ist workflow_run/completed von Signal-Engine und
Flush-Wache. Discovery liest die tatsächliche Fence; Ereignisparameter werden
nicht als Zustand vertraut. Kein eigener Pollingcron und keine Selbstrekursion.
Fehlende reguläre Starts bleiben Aufgabe des bestehenden externen Monitors.
Runner-Neustart erfolgt separat per kontrolliertem Recoveryrerun/Dispatch.

Default: BTC_RECOVERY_ENABLED=false, Recoverypolicy enabled=false und
activation_reviewed=false. Alle Betriebsaktivierungen bleiben gesondert.

Neu erforderlich: Branch recovery-journal-live im bestehenden btc-delivery-store,
unveränderlicher Seedcommit, exakte Branchregeln gegen Force/Delete sowie eine
separat tatsächlich reviewte recovery_journal_write-Rolle mit Contents:write
und Metadata:read ausschließlich dort. Der bestehende Store-PAT wird nicht
ausgelesen; seine bisherige Branchabnahme deckt den neuen Branch nicht ab.
Policy.journal.public_access bleibt bis zu diesen Belegen null. Keine neue
PAT-Identität oder Erweiterung ist durch dieses Paket freigegeben.

Journale: recovery/incidents/<original-open-fence-commit>.json. Atomare Contents-
Creates/Blob-CAS reservieren Plan, alte Heads, exakte neue Bytes und jeden der
maximal zwei Businesswrites vor dem PUT. Drei Leases mit je 128 GET vorausbezahlt,
unverlängerbare Incidentfrist 15 Minuten. Je Runner maximal 120 Sekunden und
acht Journal-CAS. Bootstrap-/Kontrolllesungen maximal 32 je ausgelöstem Job;
diese sind ausdrücklich zusätzliche Kontrollplane zu den 384 reservierten GET.
Wiederholte manuelle Diagnoseauslösungen sind kein neues Businessbudget.
Verlorene CAS-Antwort nur durch Transaction-Readback bestätigen, nie blind
wiederholen. Derselbe Businesswrite wird bei unbekanntem Ergebnis nie neu
reserviert. Journale/alte Snapshots weder überschreiben noch rotieren.

Sicherer Fall A: fachlich erfolgreicher, ownerfreier Stream; historische
Abschlussrevision und alle Quittungen geprüft; ausschließlich Fence schließen.
Fall B: exakter alter Store-Ownerworker beendet, alle Quittungen bestätigt;
Ownerfreigabe als einzelne bestätigte Streamrevision, danach aborted-Fence an
den tatsächlichen neuen Streamcommit binden. Health/Strategie/Nachrichten und
historischer GitHub-failure bleiben unverändert. Fremder/lebender Owner,
uncertain/sending, fehlende Quittung, wechselnde Heads oder unvollständige
Schutz-/Workerbelege blockieren und lassen den externen Alarm bestehen.

Nur der exakt gebundene aktuelle Recoveryrun mit überprüftem Job recover,
Workflowhash, Codeabstammung, Run-ID, Attempt und Commit darf aus der aktiven
Queueliste herausgerechnet werden. Jeder andere Run bleibt blockierend.

Vor Aktivierung: neue Branch-/Seed-/Rechte-/Bypassbelege erheben, Policy
vervollständigen und Hauptchatreview; Code und fünf reguläre Reviewstrings
bei fortbestehenden Pausen veröffentlichen, neue Recoverypolicy und Selfhash
zurücklesen. Erst nach separat bestätigter positiver/negativer Liveabnahme
BTC_RECOVERY_ENABLED setzen. Keine neuen regulären Slots durch Recovery;
Wiederanlauf ausschließlich durch den vorhandenen Zeitplan. Der externe
Cloudflare-/E-Mail-Alarm und monatliche unabhängige Restoreprobe bleiben nötig.
