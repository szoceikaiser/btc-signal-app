# Deaktiviertes Free-Quotenpaket

ÃƒÆ’Ã¢â‚¬â€œffentliche Variante ist gewÃƒÆ’Ã‚Â¤hlt. Dieses Paket ersetzt die frÃƒÆ’Ã‚Â¼here anonyme
Lesevorgabe durch den vorhandenen automatischen `GITHUB_TOKEN`. Es erzeugt
keine Repositories, Rechte, Secrets, Providerstarts oder Nachrichten.

## Kleine Einrichtungsliste fÃƒÆ’Ã‚Â¼r die spÃƒÆ’Ã‚Â¤tere manuelle Freigabe

1. Vorgesehene ÃƒÆ’Ã‚Â¶ffentliche Ziele: `szoceikaiser/btc-delivery-store`
   (`delivery-stream-v2`, `delivery-fence-v2`, immutable `reviewed-migration`),
   `szoceikaiser/btc-delivery-backup` (`verified-pair-packages`) und
   `szoceikaiser/btc-delivery-backup-verification` (`verified-receipts`).
   Sie sind noch nicht erstellt. IDs bleiben `null`, bis tatsÃƒÆ’Ã‚Â¤chlich belegt.
2. Die vorhandenen deaktivierten Runtime-/Public-Access-Vorlagen mit echten
   IDs, Code-/Config-/Migrationspins, tatsÃƒÆ’Ã‚Â¤chlichen Schutz-/Bypassreviews und
   getrennten Writerreviews vervollstÃƒÆ’Ã‚Â¤ndigen und neu versiegeln. Ein fehlendes
   `bypass_actors` bleibt UNKNOWN. GET `permissions` ist keine Tokenintrospektion.
3. `tools/p4_install_hosted_templates.py --out NEUES_VERZEICHNIS` materialisiert
   sieben weiterhin deaktivierte Workflows und einen prÃƒÆ’Ã‚Â¼fbaren Installationsdiff.
   Der Diff wird hier weder angewendet noch verÃƒÆ’Ã‚Â¶ffentlicht. In allen Jobs
   bleiben Queue/Attempt-/Entry-/SHA-PrÃƒÆ’Ã‚Â¼fungen erhalten.
4. Nur automatisch injizierter `GITHUB_TOKEN` fÃƒÆ’Ã‚Â¼r ÃƒÆ’Ã‚Â¶ffentliche GETs. Keine
   manuellen Reader-Secrets anlegen. Sender erhÃƒÆ’Ã‚Â¤lt allein seinen bisherigen
   Storewriter und seine Versandrolle, Producer allein Backupwriter, Verifier
   allein Quittungswriter. Pages und Monitor erhalten keinen Writerkey. Die
   bestehenden Pages-/OIDC-Rechte gehÃƒÆ’Ã‚Â¶ren zur Pages-VerÃƒÆ’Ã‚Â¶ffentlichung und werden
   hier nicht erweitert. Writersecrets kommen nicht in Gitargumente/-dateien.
5. Optionale Datei `provider-read-probe.disabled.yml` separat manuell prÃƒÆ’Ã‚Â¼fen.
   Sie ist nicht Bestandteil des normalen Installationsdiffs. Erst nach eigener
   Freigabe dÃƒÆ’Ã‚Â¼rfen ihr `if: false` und ihre VerÃƒÆ’Ã‚Â¶ffentlichung geÃƒÆ’Ã‚Â¤ndert werden.
   Variable `BTC_PROBE_PUBLIC_IDS_JSON` enthÃƒÆ’Ã‚Â¤lt exakt die vier ÃƒÆ’Ã‚Â¶ffentlichen
   Repositorynamen (drei Ziele plus `szoceikaiser/btc-signal-app`) und echte
   positive IDs. Kein Secretwert gehÃƒÆ’Ã‚Â¶rt in diese Variable.

## Protokoll und Quoten

Der offizielle Checkout ist auf Commit
`11bd71901bbe5b1630ceea73d27597364c9af683` gepinnt, mit festem Code-SHA,
`persist-credentials: false`, ohne Submodule/LFS und mit vorausgesetztem Git.
Der frÃƒÆ’Ã‚Â¼here eingebettete Codebootstrap entfÃƒÆ’Ã‚Â¤llt aus allen sieben Vorlagen.
Der alte Bootstrapquelltext bleibt als unbenutzte historische Quelle erhalten.
Actionpin-/Linux-/Providerabnahme ist damit nicht behauptet.

Mutable Heads werden mit eng begrenzten authentifizierten Git-Advertisements
gelesen. Immutable Raw-Dateien mÃƒÆ’Ã‚Â¼ssen einen bereits unabhÃƒÆ’Ã‚Â¤ngig bekannten
Blob-SHA bzw. Workflow-SHA256 erfÃƒÆ’Ã‚Â¼llen; bei Backupdateien kommt dieser SHA
aus dem vollstÃƒÆ’Ã‚Â¤ndig rekonstruierten und geprÃƒÆ’Ã‚Â¼ften Gitbaum. Writerreadback
prÃƒÆ’Ã‚Â¼ft die zuvor vorgeschlagenen exakten Bytes und weiterhin den Parentcommit.
Keine Fehlerroute wechselt auf REST/anonym/einen anderen Token. Nur immutable
Daten werden innerhalb einer Beobachtung dedupliziert; Caches sind auf 8 MiB
je Client begrenzt. Keine alte Store- oder Frischequittung ersetzt aktuelle Reads.

Monitor: vollstÃƒÆ’Ã‚Â¤ndiger CLI einschlieÃƒÆ’Ã…Â¸lich eigener EntryprÃƒÆ’Ã‚Â¼fung, fÃƒÆ’Ã‚Â¤lliger Runs,
exakter Completionrevisionen, Fence, unabhÃƒÆ’Ã‚Â¤ngiger vollstÃƒÆ’Ã‚Â¤ndiger Backupquittung,
aktueller Regeln/Bypassreviews und finaler Bewegungskontrolle. Run-/Jobmetadaten
werden abschlieÃƒÆ’Ã…Â¸end erneut gelesen. Ein Initial- und ein finaler Headread
begrenzen dieselbe gesamte Beobachtung. Grenze bleibt 64 GET / 20 Sekunden;
Signal 45 Minuten ab Candle-Close, Wache 15 Minuten, Backup 26 Stunden bleiben.

Pages exportiert ein Paket und prÃƒÆ’Ã‚Â¼ft Paket/geschlossenen Store/Fence sowie
aktuelle Schutzregeln nach dem Artefaktupload unmittelbar vor dem Deploy.
Ein identischer zusÃƒÆ’Ã‚Â¤tzlicher Mittelcheck entfÃƒÆ’Ã‚Â¤llt. Deploypolling ist mit
20 Sekunden, 10-Sekunden-Intervall und einem Fehler begrenzt. Das ist kein
Versprechen erfolgreicher oder pÃƒÆ’Ã‚Â¼nktlicher Pagesbereitstellung.

Das kleine Stundenmodell wiederholt vollstÃƒÆ’Ã‚Â¤ndige lokale CLI-Requesttraces fÃƒÆ’Ã‚Â¼r
4 Wachen, 2 Signaltermine, 1 Lage, 7 Pagesjobs mit je 2 Beobachtungen,
12 unabhÃƒÆ’Ã‚Â¤ngige Monitorchecks und 1 Producer-/Verifierpaar in einer Zeitachse.
Es ist ein Volumen-Replay und kein gemeinsamer Markt-/Livezustandslauf.
779 gemessene automatische REST-GETs plus 56 Checkout-/Metadaten- und
56 Pages-Service-Reserve ergeben 891/1000, Reserve 109. 85 Writeroperationen
werden separat ausgewiesen; selbst alles REST gemeinsam plus Reserven wÃƒÆ’Ã‚Â¤re
976. Writerquoten hÃƒÆ’Ã‚Â¤ngen von den tatsÃƒÆ’Ã‚Â¤chlichen separat reviewten Credentials
und deren gemeinsam genutztem Providerkonto ab. Sie sind noch nicht belegt.
Git-/Raw-Reads und eine zusÃƒÆ’Ã‚Â¤tzliche Git-Checkout-Allowance werden separat
gezÃƒÆ’Ã‚Â¤hlt. Keine neue Quote je Job oder Tokenstring. GrÃƒÆ’Ã‚Â¶ÃƒÆ’Ã…Â¸ere Datenhistorien,
weitere manuelle AuftrÃƒÆ’Ã‚Â¤ge oder weitere Workflows brauchen eine neue ZÃƒÆ’Ã‚Â¤hlung.

Restquote 0 stoppt weitere Requests auch bei vergangenem Resetwert. Reset ist
Beobachtungsdatum, keine lokale QuotenauffÃƒÆ’Ã‚Â¼llung. 403/429/Retry-After stoppen
ohne Retry, Tokenwechsel, bestÃƒÆ’Ã‚Â¤tigte Erfolgsquittung oder Fristverschiebung.
SekundÃƒÆ’Ã‚Â¤re Limits sind keine garantierte VerfÃƒÆ’Ã‚Â¼gbarkeit. Die erlaubte offizielle
Referenz ist der bereits gelesene GitHub-Artikel
https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api .

## Noch ausstehende Providerbeweise

Die optionale Probe hat maximal 10 GET, 0 Write, 0 Versand, 5 Jobminuten,
keinen Checkout und keine Wiederholung. Sie prÃƒÆ’Ã‚Â¼ft die drei ÃƒÆ’Ã‚Â¶ffentlichen IDs
und Branchpins, einen gepinnten Storeblob ÃƒÆ’Ã‚Â¼ber REST/Raw, dessen exakte Bytes
und den gleichen Branch ÃƒÆ’Ã‚Â¼ber Git. Ein abschlieÃƒÆ’Ã…Â¸endes Coderepo-GET zeigt
Rate-Limit-Header nach den Transporten. Ausgabe nur Status, IDs/Pins und
Quotaheader; keine Token oder Payloadtexte. Hier wurde sie nicht gestartet.
Konkurrierende Jobs kÃƒÆ’Ã‚Â¶nnen die Headerdifferenz verÃƒÆ’Ã‚Â¤ndern; diese kleine Probe
belegt allein keine allgemeine Quoten-/Zeit-/Protection-/Bypassabnahme.

Cross-Repo-GET-UnterstÃƒÆ’Ã‚Â¼tzung des echten automatischen Jobtokens, tatsÃƒÆ’Ã‚Â¤chliche
Git-/Raw-Quotenzuordnung, tatsÃƒÆ’Ã‚Â¤chliche Actionaufrufe und die eingeplanten
Plattformreserven mÃƒÆ’Ã‚Â¼ssen spÃƒÆ’Ã‚Â¤ter belegt werden. Der synthetische Provider
bestÃƒÆ’Ã‚Â¤tigt diese Eigenschaften ausdrÃƒÆ’Ã‚Â¼cklich nicht. Alle Vorlagen bleiben aus.

Alte Liveengine und Belege bleiben erhalten; C05 inaktiv, S006 Vergleich.
Externer Alarm, frischer Stillstandsschnitt, vollstÃƒÆ’Ã‚Â¤ndige C05-Zielconfig und
P4/Cutover bleiben eigene offene Schritte. Keine Actionsbereinigung: Vor jeder
spÃƒÆ’Ã‚Â¤teren LÃƒÆ’Ã‚Â¶schung/Stilllegung Zweck, AbhÃƒÆ’Ã‚Â¤ngigkeiten und Folgen erklÃƒÆ’Ã‚Â¤ren und
Nutzer fragen, auch bei Runs, Logs, Artefakten und Branches.
