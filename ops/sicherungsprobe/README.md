# Ausschließlich synthetische Sicherungsprobe — lokal vorbereitet

Modellvorgabe gpt-6.1-sol, Aufwand high. Keine externe Einrichtung oder Ausführung
aus diesem Verzeichnis ableiten. Keine Engine-/C05-Aktivierung und kein Versand.

Die drei YAML-Dateien liegen außerhalb `.github/workflows`, enthalten einen
deaktivierten Job und ausschließlich `workflow_dispatch`. Die Materialisierung
liefert einen separaten Vorschlagsdiff mit drei neuen Main-Workflowdateien;
es werden keine alten Workflowdateien ersetzt. `backup.yml` und
`backup-verify.yml` sind durch den vorhandenen Hostedvertrag vorgegeben.

`tools/p4_backup_probe_prepare.py --code-pin <geprüfter-Commit> --out <neu>`
erzeugt ohne Netzwerk eine vollständig künstliche Legacyquelle, ein mit dem
vorhandenen Konverter erzeugtes blocked-Migrationspaket, fünf einzelne
Branchseeds, drei Gitbundles, konkrete YAMLbytes und eine **deaktivierte**
Runtime. Sie enthält echte Repository-IDs, aber keine erfundenen neuen
Ruleset-IDs, Bypassabnahmen oder Main-Einstiegscommits.

Die drei neuen Rulesetvorschläge in diesem Verzeichnis schützen ausschließlich
die fünf `probe-20261015-*`-Branches. Alte Regeln/Branches bleiben unverändert.
Store umfasst Stream, Fence und Migration in einem neuen Ruleset mit drei
exakten Refs; Backup und Quittung je einen. Alle active, ohne Bypass,
deletion/non_fast_forward/required_linear_history. Erst separat tatsächlich
eingerichtete und geprüfte IDs/Antworten/UI-Belege dürfen ein neues
`btc-public-access-v1`-Dokument bilden. Alte Regeln gelten für andere Refs und
werden dafür nicht umetikettiert. PAT-Rechte gelten repositoryweit; neue
Branchlisten im Writerreview sind zusätzliche logische Aufnahmebindungen.
Der Verifier-Metadatenbeleg muss die erfolgte Erneuerung berücksichtigen.

`--access <neuer-geprüfter-Review> --entry-pin <tatsächlicher-Main-Commit>`
erzeugt nach erneutem lokalen Review den tatsächlichen Einrichtungsdatensatz.
Dieser Schritt hat keine kurzen Eingabefristen und führt keine Requests aus.
Eine aktivierbare Ausgabe ist kein Nachweis des Providerzustands: vor Dispatch
muss der Hauptchat alle tatsächlich gelesenen Regeln, IDs und Bypassbelege
gegenprüfen. Die Runtime und ihre Seeds hängen von diesem Review ab; die
deaktivierten Beispieldateien dürfen nicht vorab gepusht werden.

Code wird später auf einem eigenen Branch publiziert und auf seinem genauen
Commit ausgecheckt. Nur die drei YAMLs werden als eigener Datei-Commit auf
Main vorgeschlagen, ohne Kandidatenmerge. Für diese Probe bindet
`probe_entry_sha` jeden Einstieg exakt an diesen separat geprüften Maincommit
und dessen authentifiziert rückgelesene YAMLbytes. Ein neuer Main-HEAD ist
kein stillschweigend erlaubter Nachfolger. Normale Hostedruntimes ohne das Feld
behalten die bisherige Code-Abstammungsprüfung. Alte Livejobs und Cronauslöser
werden weder angehalten noch geändert; verschieben sie den Einstieg vor einem
Dispatch, muss der Hauptchat neu prüfen und die Probe bleibt angehalten.

Geplante Einmalfolge: Main/Code/Schutz/Seed-Abnahme → Storewriter im Environment
`btc-delivery-v2` → Hauptchat prüft tatsächliche Run-/Ref-/Blobbelege →
`--seal-runtime <initiale-runtime.json> --store-result <geprüftes-confirmed.json>
--out <neue-cut-runtime.json>` → Producer im Environment `btc-backup-producer`
→ tatsächlichen erfolgreichen Producer prüfen → Verifier auf frischem Runner
im Environment `btc-backup-verifier` → Quittung unabhängig rücklesen.
Alle drei Dispatches verwenden denselben expliziten UTC-Mitternachtstermin
als `expected_start_ms` und `probe_name=btc-synthetic-backup-20261015`.
Die vorhandene 26h-Frist, 1800s pro CLI, 15s je Request, Ressourcenlimits und
35min Jobtimeout bleiben erhalten. Zusätzlich 256 Requests/64 Nicht-GET je
Probelauf; read-only upload-pack-POSTs zählen als Nicht-GET. Keine Wiederholung
und keine automatische Fortsetzung nach unklarer Mutation. Der abgeschlossene
P3-Lauf wird nicht aufgerufen.

`tools/check_backup_probe_offline.py <neuer-Ausgabepfad>` prüft nur diesen neuen
Ablauf mit lokalen Gitobjekten und künstlichem HTTP; echte Socketverbindungen
sind gesperrt. Linux und der saubere Codecheckout werden dort ausdrücklich
simuliert. Es ist keine reale Smart-HTTP-, Secretwert-, Writer- oder
Linuxabnahme. Keine alten Gesamttestreihen werden ausgeführt.

Der spätere Storewriter erzeugt einen fiktiven Fencecursor unter dem
vorhandenen Signalpfad sowie einen ausdrücklich erfundenen Nachrichtenbeleg.
Das ist ausschließlich Protokollprüfstoff, kein echter Signalworkflowabschluss
und kein Telegrambeleg. Stream bleibt blocked. Producer sichert beide vollen
Historien und die Migration, Verifier restauriert nur aus dem Backupdownload
in ein neues blocked-Verzeichnis und schreibt/rückliest die Prüfquittung.
Kein Bootstrap ist hier bereits erfolgt. Pages ist nicht Teil der Probe; nur
die weiterhin deaktivierte Pagesvorlage bindet jetzt deploy-pages auf den
offiziell bestätigten Commit von v4.0.5. Die externe Composite-Action
upload-pages-artifact enthält intern weiterhin upload-artifact@v4; daraus
keine vollständige transitive Pagespinabnahme ableiten.
