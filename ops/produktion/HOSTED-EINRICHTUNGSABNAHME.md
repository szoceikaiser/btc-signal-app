# Spätere Einrichtung und begrenzte Abnahme — keine Ausführung jetzt

Alle echten Werte bleiben unbekannt und deaktiviert. Dieser Ablauf ist ein
Einrichtungsplan, kein Start-/Fortsetzungsprompt und keine Providerfreigabe.
Keine Wiederverwendung abgeschlossener Grants, Starter oder Tokenkampagnen.
Der konkrete öffentliche Einrichtungs- und Rollenvertrag steht verbindlich in
[FREE-EINRICHTUNG.md](FREE-EINRICHTUNG.md); nachfolgende Ablaufgrenzen bleiben.

1. Einmaliges Einrichtungsreview, höchstens60min: echte öffentliche Ziele
   `szoceikaiser/btc-delivery-store`, `btc-delivery-backup`,
   `btc-delivery-backup-verification` und deren numerische IDs/Sichtbarkeit,
   explizit public unter gewähltem GitHub Free, tatsächliche getrennte Rollen
   und aktive exakte Branchrules. Noch keine Ressource ist hier erstellt.
   Datenklassen/Dateiinventar und Secret-Ausschluss vor Veröffentlichung prüfen;
   keine Buchung/Planänderung. Ohne vollständige Schutz-/Bypassreviews stoppen.
   Offizielle bereits im Hauptchat gelesene Referenz:
   https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
2. Vor irgendeinem Schreib-/Versandbetrieb: Rollenreichweite und separate
   Workflowenvironments prüfen. Producer darf weder Stream/Fence noch
   Quittungen schreiben; Sender nur Stream/Fence; Verifier liest Backup und
   darf ausschließlich Quittungen schreiben. Alle Rollen dürfen fremde
   Repository-IDs nicht umleiten. Protection muss unveränderte Historie,
   keine Forcepushes/Branchlöschung und keine ungereviewten Bypässe sichern.
   Anonyme Rules-GETs und separater tatsächlicher Bypassreview; keine zusätzlichen
   Administration:write-Rechte. GETrepo.permissions ist keine Tokenintrospektion.
   Tatsächliche Ressourcen-/Writerbelege nötig; das lokale Fake ersetzt sie nicht.
3. Einmaliger expliziter Bootstrap: vorgeschlagene dedicated Storebranches
   `delivery-stream-v2`, `delivery-fence-v2`, Backupbranch
   `verified-pair-packages` und Quittungsbranch `verified-receipts` einrichten.
   Backup-/Quittungsbranches beginnen mit einem gültigen leeren Gitbaum auf
   einem vorhandenen Commit, nicht mit README/anderen Dateien. Das kann als
   separat reviewter initialer Gitcommit eingerichtet werden; der Hostedjob
   selbst legt keinen Branch an. Streamseed/Migration/Fencecursors nur aus
   frisch gestopptem, vollständig geprüftem Schnitt. Echte erste Startslots,
   Cursors, vollständige C05-Zielconfig und Alarmempfänger bleiben gesondert
   offen. C05a99be30a bleibt bis dieser fachlichen Abnahme inaktiv; S006 Vergleich.
4. Codepinreview: gesicherten neuen Codecommit in `btc-signal-app` erst als
   konkreten Diff beurteilen. Die in diesem Paket enthaltene deaktivierte
   Overlayausgabe umfasst genau sieben Workflowpfade. Actionreferenzen
   einschließlich deploy-pages v4.0.5 bei offiziellen Quellen bestätigen
   und dessen finalen Commitpin einsetzen; SHA256 der finalen YAMLbytes neu
   erzeugen. Exakten Code-/Python-/Runtime-/Config-/Aktivierungsreviewpin
   schriftlich binden. Nicht auf wechselnde Backtest-/Legacycommits entpinnen;
   die neue Entryprüfung erlaubt nur reviewed unveränderte Workflowbytes
   und überprüfte Abstammung. Coinalyze, Tests und Backtest erhalten.
5. Nicht geheime Runtimevariablen ausfüllen: `BTC_PRODUCTION_CODE_SHA`,
   `BTC_HOSTED_CODE_SHA`, `BTC_HOSTED_RUNTIME_JSON/SHA256`, die bestehenden
   reviewed Engine-/Pages-/Monitorruntimevariablen und die erzeugten
   `entry_workflows`-SHA256. `migration.target`, immutable Commit/Tree und
   vollständiges Blob-/Byteinventar ausdrücklich prüfen. `pins=null` nimmt
   pro Producertermin einen frischen Sourcecut; ein explizites erstes Pins-
   Objekt erzwingt genau die erste Abnahmesicherung. Secretwerte bleiben
   ausschließlich in den getrennten geschützten Secrets und werden nicht
   in Konfigurationen, Argumente, URLs, Dateien, Artefakte oder Logs kopiert.
6. Nach eigener ausdrücklicher Einrichtungs-/Testfreigabe ein begrenztes
   echtes, stilles Backupfenster: genau ein Producer und ein unabhängiger
   Verifier. Höchstens35min pro Job, intern gemeinsam1800s; keine automatische
   Dispatchkette und kein Telegram/Markt-/Sendetest. Insgesamt höchstens70
   Jobminuten und1GiB reservierter Transfer. Echte GitDB-/Branch-/Blob-/Byte-
   Readbacks und blocked Restore vollständig sichern. Bei Fehler stoppen,
   keine blinden Retries, keine neue Kampagne aus dieser Abnahme ableiten.
   Die tatsächliche Rollen-/Providerabnahme ist erst damit möglich.
7. Nur falls der erste Durchgang vollständig abgenommen ist, genau ein
   gesondert genehmigtes Folgepaar zur Inkrementerhaltung: dieselben Grenzen,
   maximal weitere70Jobminuten/1GiB Transfer. Vorherige Paket-/Manifest-
   und Commitidentitäten unverändert nachweisen, unabhängige Quittung
   zurücklesen. Gesamtrahmen maximal4Runs,140Jobminuten,2GiB reservierter
   Transfer; reale Kosten/Quota vorher bestimmen, kein Preisversprechen.
   Konkurrenz-/Lostresponsefehler bleiben primär synthetische lokale Belege;
   keine absichtliche Token-/Providerstörkampagne ist hier vorgesehen.
8. Separates Cutoverreview erst danach: aktuell alte Liveengine
   main69e676d85837567272e2935ed00ceb45c2516430 und Sicherung erhalten.
   Neuer frischer Stillstandsschnitt, vollständige C05-Config/P4, alte/neue
   Fortschritts-/Quittungsabstimmung und blocked Rückkehrregel erforderlich.
   Lokaler Erfolg begründet weder Livebereitschaft noch Gesundheit. Keine
   neuen Rendite-/Kombinationsläufe, Aprilfüllung oder Brokeranalyse.
9. Externen Alarm-/Deadmananbieter separat einrichten und prüfen, Vorschlag
   Check alle5min/Deadman10min. Empfänger, Zuständiger, Eskalation, echte
   Startcursors und erste Slots explizit binden. Optionaler Actionsmonitor
   ersetzt keinen anbieterunabhängigen Gesamtausfallalarm; bleibt disabled
   bis zum eigenen Review. Monitor200 benötigt vollständige echte Belege,
   keinen grünen Producer allein.

Vorlagen und Runtime bleiben bis zur jeweiligen Abnahme `if:false` /
`enabled=false`. Hier kein Merge, Push, PR, Dispatch, Providerrequest,
Settingswechsel, Nachricht oder Livewechsel.

Actionsbereinigung erst am Ende: vor JEDER Löschung oder Stilllegung
konkreten Namen, damalige Aufgabe, heutige Abhängigkeiten, Folgen und
gesicherte Belege erklären und Nutzer fragen. Gilt auch für Runs, Logs,
Artefakte und Branches. Dieser Auftrag enthält keine Löschfreigabe.

Keine weiteren Chats/Subagenten/automatischen Nachrichten. Nutzer übermittelt
das Ergebnis selbst im Hauptchat. Falls später ein neuer Start- oder
Fortsetzungsprompt erzeugt wird, als Markdown speichern und vollständig
wortgleich final ausgeben, Modell/Aufwand nennen und diese Pflicht vererben.
