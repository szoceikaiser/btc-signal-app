# Pflichtfunktionen im deaktivierten Kandidaten

Diese Vorlagen bleiben außerhalb `.github/workflows`; jeder neue Job hat
`if: ${{ false }}`, beide Runtimevorlagen `enabled=false`. Kein Livewechsel,
kein Versand und kein Storebootstrap durch diesen lokalen Auftrag.

## Bedienung und bestehende Abhängigkeiten

| Gewünschte Aktion | Späterer unveränderter Zielpfad | Deaktivierte Vorlage | Art |
|---|---|---|---|
| Signal-Engine | `.github/workflows/signal.yml` | `signal-workflow.disabled.yml` | Signal, Zeitplan und Hand-/externer Start |
| Flush-Wache | `.github/workflows/watch.yml` | `watch-workflow.disabled.yml` | Wache, Zeitplan und Hand-/externer Start |
| Lage abrufen | `.github/workflows/lage.yml` | `lage-workflow.disabled.yml` | nur eigener Handstart; kein Kind-Wahlschalter |
| Chart-Webseite (Pages) | `.github/workflows/pages.yml` | `pages-workflow.disabled.yml` | Handstart, site-Push, erfolgreiche Signal/Wache/Lage/Backtest-Folge |

Der vorhandene cron-job.org-Aufruf kann weiterhin `signal.yml` bzw. `watch.yml`
mit `ref: main` und ohne Inputs verwenden; eine leere Eingabe bindet den festen
UTC-Slot aus dem tatsächlichen Run-created_at, niemals aus dem Stepbeginn.
Signal hat Phasen :02/:32 je4h, Wache :08/:23/:38/:53. Späte Aufrufe werden
abgewiesen; ein explizites ursprüngliches `expected_start_ms` ist optional.
Der neue verbindliche Termin-/Backup-/Monitorvertrag und verbleibende echte
Bindungen stehen in [BETRIEBSABSCHLUSS.md](BETRIEBSABSCHLUSS.md).
Die tatsächlichen externen Einstellungen wurden hier nicht gelesen oder geändert.
Alte Signal-Inputs `test_telegram`/`resend_all` gehören nicht zum neuen Sendepfad;
historischen Resend nicht übernehmen. Coinalyze-Test bleibt eigener Diagnoseknopf.
Tests, Backtest, Coinalyze-Archiv und Coinalyze-Test sowie sämtliche alten aktiven
Workflowdateien sind bytegleich zur Ausgangsbasis. Keine Actionsbereinigung.
Pages nutzt denselben Gruppennamen wie alle drei Sendeworkflows, mit `queue: max`
(höchstens100 wartend, keine FIFO-Garantie), und bricht keinen laufenden Auftrag ab.
Bei workflow_run muss der Auslöser erfolgreich, aus demselben
Repo/main und auf demselben Codepin sein. Backtest-/Archivschreibrechte bleiben
außerhalb des Versandstreams; neue Codecommits brauchen einen neuen geprüften Pin.

## Sperrschema v2 und Auftragsschutz

`github-actions-fence-v2` ist absichtlich inkompatibel zu v1. Dieselbe exakte
Deploymentbindung enthält genau drei feste Workflow/Kind-Paare. Drei dauerhafte
Cursors speichern jeweils letzte Laufnummer und Run-ID; die Laufnummer wird nur
innerhalb dieses Workflows verglichen. Run-ID dient Identität, nie Zeitordnung.
Ein gemeinsamer CAS-geschützter open/closed-Fence sperrt alle drei Workflows.
Der Cursor wird bereits bei bestätigter Aufnahme gespeichert. Attempt 2, derselbe
Prozessauftrag und alte Laufnummern bleiben gesperrt, auch nach anderem Workflow.
Kein TTL, keine automatische Übernahme, kein automatischer Neustart offener Aufträge.

Lage benötigt workflow_dispatch aus lage.yml. Die Auftrags-ID ist SHA256 der
kanonischen Repo/Workflow/Run-ID, ohne Attempt; sie wird vom Entry abgeleitet.
Die bestehende dauerhafte Lagefunktion speichert Nachrichten vor Transport und
eine eigene `actions-lage-completion-v1` am Auftrag. Sie bindet Run, Auftrags-ID,
Code/Config, Resultat, Outbox und unveränderten Engine-/Watchstand. Nur vollständige
bestätigte zielgebundene Quittungen mit einem Versuch erlauben den Abschluss.
Alte Signal-health genügt nie. Bei leerem Marktresultat, Ablehnung oder Ungewissheit
bleibt der Fence offen; ein Prozessverlust erlaubt keinen automatischen Resend.

Der Geschäftsstore bleibt `btc-github-store-v1` / Snapshot v2. Alte Commands,
Signale, Quittungen, Geld-/UM2-/M5-/Backupregeln werden nicht migriert oder gekürzt.
Nur das separate Fenceschema ändert sich. Ein realer v1-Fence wird ausdrücklich
abgewiesen. `produktion_actions_prepare.py` schreibt ausschließlich einen neuen
lokalen Seed mit exklusivem Ziel; nie über bestehende Sperren schreiben. Ein
synthetischer Nullcursor ist kein Rücksetzplan für bestehende reale Aufträge.
Vor realer Übernahme müssen alle alten offenen/abgeschlossenen Aufträge gesichert,
die Auslöser angehalten und bestehende Workflow-Laufnummern als geprüfte Startgrenzen
gebunden sein. Der Seed-CLI verlangt `--cursors`: Schema
`actions-v2-start-cursors-v1`, `review_sha256` passend zum Aktivierungsreview und
genau drei `cursors` mit `number`/`id`. Es gibt im CLI keinen Nullcursor-Default.
Alte Sperren bleiben erhalten, unklare Aufträge bleiben gesperrt.

## Öffentliche Projektion und Grenzen

`produktion_pages_export.py` hat ausschließlich GET und keine Store-Claim-/PUT-
oder Telegramfunktion. Ein Contents:read-Token für den privaten Store ist getrennt
vom Sendetoken. Exact deployment, tatsächlicher Pagesentry/Repo/Ref/Codepin und
sauberer Checkout einschließlich site werden geprüft. Der Store bleibt authentisch
auf seinen Repo/Branch/Store-/Config-/Code-/Botpins; alle Outboxes müssen bestätigt,
Owner leer und Fence geschlossen sein. Sein Abschluss muss exakt die aktuelle
Streamrevision/Commit/Blob/Digest belegen. Die letzte Lage wird am eigenen Auftrag,
Signal/Wache am exakt gebundenen erfolgreichen Run geprüft. Doppellesung von
Fence und Stream verweigert Veränderungen; ein Seed ohne Abschluss veröffentlicht nie.

Je Beobachtung genau 12 GET, null PUT/Transport; keine Retries. Maximal 2 MiB je
Antwort, 24 MiB reservierte Antwortbytes, 10s je Request, 120s Gesamtdauer, kein
Redirect/Proxy. Signalstand darf nicht zukünftig oder über 8h nach Kerzenschluss
liegen. Der Export erzeugt ein neues exklusives Uploadverzeichnis mit nur HTML,
zwei Scripts, einer gemeinsamen hashbenannten State-/Signalprojektion, Manifest
und expliziten bisherigen öffentlichen historischen Backtest/V1-Dateien. Kein
geerbtes `site/data`-Verzeichnis, keine Config, Commands, Chattexte, Outbox oder
internen Quittungen. Die Felder sind verschachtelt ausgewählt in public_projection.py.
Private Store-/Fence-Locators liegen außerhalb des Uploadbaums in einer Quittungsdatei.

Manifest, öffentlicher Payload und historische Dateien sind hashgebunden. Vor Upload
und unmittelbar vor Deploy werden Zustand UND Uploadbytes erneut geprüft, unbekannte
Dateien abgewiesen. Insgesamt höchstens 36 GET / 72 MiB / drei 120s-Phasen pro Pagesjob.
Ein offener oder bewegter Stand ergibt einen fehlgeschlagenen Build, keinen alten
Git-Liveersatz. Pages bleibt beim zuletzt veröffentlichten bestätigten Paket; im
Browser wird der Zeitstand und nach 45min fehlende Exportaktualität sichtbar, auch
bei länger offener Seite. Kurschart nutzt seine bestehende Börsenquelle; Ausfall
führt zu sichtbarem Fehler ohne alte Gitkerzen. Signalmarker/Plan-/Vorschau-Linien
und historische Monats-/Backtestanzeige bleiben erhalten. Historische Ergebnisse
tragen ihren bisherigen generated_at/Zeitraum und ausdrücklich keine neue C05-Rendite.

Ein letzter GET beweist den Stand bei Beobachtung, keine atomare Transaktion mit
dem externen Pagesdeploy. Spätere externe/adminseitige Storeänderungen können allein
durch lokale Quelltests nicht ausgeschlossen werden. Spätere Aktivierung benötigt
die echte Sperr-/Repository-/Branch-/Token-/Configbindung, frischen Stillstandsschnitt,
vollständige C05-Zielconfig (weiter inaktiv), zweite geschützte Sicherung und unabhängigen
Frischealarm. Bestehende action-Versionstags/Hostedimage sind noch keine hier neu
verifizierten unveränderlichen Providerpins. Keine erneute Hostedkampagne und kein
pauschales live-ready aus diesen Offlinebelegen.
