# P2a – Betriebsvertrag und begrenzte Betriebsentscheidung

Stand 03.10.2026. Verbindliche Zielvorgaben für P2b; **keine Bereitstellung,
Migration oder Live-Freigabe**. P1 bleibt `7df2e20e8b68c1c7db8a5b4715fd6c1253e9165b`.
Die vorhandene Engine und ihre Laufzeitdaten werden in P2a nicht geändert.

## 1. Entscheidung aus der vorhandenen Infrastruktur

Gezielt geprüft: `.github/workflows/*.yml`, `ANLEITUNG-PUENKTLICHER-START.md`,
`engine/durable_delivery.py`, `telegram_outbox.py`, die betroffenen Stellen in
`main.py` und `position_state.py`. Öffentlich lesbare Repository-Metadaten weisen
`szoceikaiser/btc-signal-app` als **öffentlich** aus. main bei dieser Prüfung:
`1c6c51c216a5200c416fec0b5bc6fbcaf1d134c6`; kein neuer Migrationssnapshot.

Nachgewiesen sind GitHub-hosted Ubuntu-Runner und die Repositoryablage.
cron-job.org ist als Dispatch-Auslöser dokumentiert; seine aktuelle Einrichtung,
Zugänge und tatsächliche Verfügbarkeit wurden nicht geprüft. Keine Secrets gelesen.
Kein benannter eigener Dauerläufer, kein nachgewiesenes persistentes Runner-Volume.
Der vorhandene Windows-Arbeitsplatz ist kein Beleg für einen 24/7-Betrieb.

| Weg | Eignung und verbindliche Grenze |
|---|---|
| Vorhandener eigener Dauerläufer mit lokalem Datenträger | Technisch bevorzugt, **falls tatsächlich vorhanden und vom Nutzer benannt**: vorhandenen A4-SQLite-Adapter verwenden, kein neuer Persistenzdienst nötig. Noch nicht verfügbar nachgewiesen. |
| GitHub-hosted Runner mit neuem dauerhaften GitHub-Adapter | Empfohlene Alternative ohne eigenen Host. Separater Entwurf in `P2A-GITHUB-ADAPTER.md`; kein A4-Nachweis. Privates Zustandsrepository und Schreibberechtigung benötigen eine konkrete Nutzerentscheidung. Noch nicht implementiert oder provisioniert. |
| Laufender Windows-PC ohne Verfügbarkeitszusage | Als Offline-Testumgebung brauchbar, nicht als zugesagter Betrieb. Schlafen, Neustarts, Verbindung und unbeobachteter Ausfall sind offene Betriebsfragen. |
| Actions-Cache, Artefakt oder Git-Commit erst nach Versand | Ungeeignet als maßgeblicher Versandstore: Verlust zwischen Transport und späterer Sicherung bleibt möglich. |
| Neuer bezahlter Server | Keine Voraussetzung und nicht beauftragt. |

P2a legt damit keinen erfundenen Host fest. P2b setzt zunächst den gemeinsamen
Migrations-/Betriebskern mit dem vorhandenen SQLite-Testadapter um. Genau **ein**
realer Adapterweg wird nach D1 ausgewählt; ohne D1 bleibt die hostabhängige Anbindung
offen. Das ist ein benannter Lieferumfang mit Freigabegrenze, kein stiller Ersatz
für betriebsfertigen Versand. GitHub-Adapterarbeit ist das getrennte Paket G.

## 2. Ein Stream, ein maßgeblicher Zustand

Ein Stream bindet eine feste Store-ID, ein Versandziel und eine Bot-Identität.
Die Zielbindung ist bislang nur der Chat-Hash; Bot-Wechsel ist kein unterstützter
Restart. P2b muss den freigegebenen Bot als nichtgeheime Betriebsidentität pinnen
(kein Token speichern); deren reale Bestätigung erfolgt erst in P3/P4.
Es gibt genau einen schreibenden Betriebsweg. Signal, Watch, Lage, Test und
zulässige manuelle Aufträge teilen Store und Sperre. Alle alten Trigger werden
vor P4 kontrolliert stillgelegt, einschließlich externer Dispatch-Aufträge,
manueller Starts und noch wartender Läufe. Archiv ist kein Versender, muss aber
während der konsistenten Aufnahme ebenfalls ruhen.

Zielhülle für P2b: `version: 2`, `engine`, `watch`, `commands`, `control`.
Die getrennten Schemata `state_version: 2` und `_delivery.version: 1` bleiben
erhalten. `control` enthält mindestens `stream_id`, `store_id`, `target_binding`,
`bot_identity`, `mode`, `code_sha`, `config_sha256`, `migration`, `health`,
`reconciliations` und `owner` (nur für den GitHub-Adapter erforderlich).
`mode` ist `offline`, `blocked` oder `active`; Provisionierung startet gesperrt.
Fehlende Kontrollfelder und unbekannte Versionen werden abgewiesen. Ein alter
A4-Leser darf Version 2 nicht öffnen: bewusste Schutzgrenze gegen Rückfallcode.
Ein A4-v1-Import braucht einen eigenen geprüften Konverter, falls später benötigt;
der unmittelbare Import des unversionierten main-Zustands bleibt verboten.

Der Store enthält Position, vollständige übernommene Signalhistorie, OI-Projektion,
Watch, alle Nachrichten und Kontrollinformationen gemeinsam. Alte Rohdateien und
Konfigurationsprojektionen liegen zusätzlich unveränderlich im Migrationspaket.
`site/data` ist nach Aktivierung nur eine wiederherstellbare Anzeigeprojektion.
Kein blindes `git add site/data`: Versandjournal, Zielbindungen, Kontrollbelege und
Nachrichtentexte dürfen nicht aus dem privaten Store in das öffentliche Repository
oder in Pages gelangen. Ein expliziter Exporter schreibt nur freigegebene bestehende
Anzeigefelder; insbesondere ohne `_delivery` und `control`. Öffentliches Git ist
weder Restorequelle für Zustellungen noch eine zweite Zustandsautorität.

## 3. Verbindliche Schreib- und Versandfolge

1. Sperre erwerben, Schema/Identität/Integrität, Modus, Code- und Konfigurationspin
   prüfen. Keine Marktabfrage vor Wiederherstellung und Prüfung offener Zustellung.
2. Überlebendes `sending` dauerhaft nach `uncertain` überführen. Jede Unklarheit
   sperrt **alle** Versandpfade und den produktiven Entscheidungsfortschritt.
   Der bisherige Hauptlauf kann bei gesperrtem Versand trotzdem weiterrechnen;
   P2b muss am gemeinsamen Runner-Eingang vorher abbrechen. Offline-Diagnose ist
   nur auf einer separaten Kopie erlaubt und darf den Stream nicht fortschreiben.
3. Sichere offene `pending`/`rejected` zuerst mit gespeichertem Text fortsetzen.
   Erst danach neue Eingaben holen und zulässige neue Entscheidungen treffen.
4. Vollständigen Batch mit Position, Historie, Watch-Merker, IDs, unveränderlichen
   Texten und Fortsetzungszustand dauerhaft committen: **vor jedem ersten Versand**.
5. Vor jedem Transport `sending`, Zielbindung und Versuchsnummer committen.
   Nur nach bestätigtem Commit darf der Transport aufgerufen werden.
6. Strukturierte positive `message_id` plus passendes Ziel erlaubt `confirmed`.
   Quittung dauerhaft speichern, erst dann die nächste Nachricht behandeln.
7. Spiegel und Gesundheitsstatus ableiten, Sperre freigeben. Fehler beim Spiegel
   dürfen kein erneutes Senden bereits bestätigter Nachrichten bewirken.

| Gespeicherter Status / Ereignis | Aktion |
|---|---|
| `pending` | Nach Prüfung von Sperre, Ziel, Schnittgrenze und Modus zustellbar. |
| `rejected` | Nur echte strukturierte Ablehnung; gleicher gespeicherter Text, kein neuer Auftrag nötig. Höchstens ein Versuch je regulärem Lauf, keine enge Retry-Schleife. |
| `sending` nach Prozessende | Dauerhaft `uncertain`, kein Transport. Auch Abbruch vor erstem Netzwerkbyte zählt so. |
| Timeout, ungültige Antwort, unklare Annahme | `uncertain`, Alarm und Sperre. |
| `confirmed` | Nie automatisch erneut senden, Quittung erhalten. |
| Quittung empfangen, deren Speicherung scheitert | Lauf endet; gespeichertes `sending` ist beim Restart unklar. Kein Rückfall auf lokale Quittung oder neues Git-Checkout. |
| Store fehlt, ist beschädigt, falsch gebunden oder nicht erreichbar | Abbruch vor Datenverarbeitung/Versand. Keine automatische Provisionierung. |

Kein Exactly-once-Versprechen: Unterbrechung zwischen Transport und Quittung kann
eine tatsächlich gesendete Nachricht ohne gesicherten Beleg hinterlassen. Der
Vertrag bevorzugt dann Stillstand vor möglicher Doppelzustellung.

## 4. Konkreter SQLite-Betriebsweg bei vorhandenem Host

Ein dediziertes Betriebskonto startet einen lokalen Scheduler und einen kurzlebigen
Runnerprozess. Der Scheduler startet Signal nach 4h-Schluss ab Minute 2 UTC,
Watch wie bisher zu Minuten 8/23/38/53; konkurrierende Starts werden am gemeinsamen
Mutex abgewiesen. Kein nachholender Sturm identischer manueller Befehle.
Für Lage/Test/neue ausdrücklich erlaubte Aufträge bleibt eine Operation-ID beim
Retry gleich. `resend-all` bleibt für den migrierten historischen Bestand gesperrt.

Beispiel Linux: `/srv/btc/runtime/<run-id>` als Runnerwurzel,
`/var/lib/btc-delivery/<store-id>` als Store. Beispiel Windows:
`C:/BTC/runtime/<run-id>` und `C:/BTC/persist/<store-id>`; keine Einrichtung in P2a.
Variablen gemäß A4: `BTC_DELIVERY_STORE`, `BTC_DELIVERY_STORE_ID`,
`BTC_DELIVERY_RUNNER_ROOT`; Auftrags-ID nur für passende manuelle Befehle.
Hostprofil und absolute Pfade werden vor P3 konkret eingetragen und geprüft.

Datenträger: lokale zuverlässige SQLite-Locks/fsync, außerhalb des gesamten
Runnerverzeichnisses; keine Netzfreigabe, kein NFS/SMB, keine Cloud-Sync-Kopie.
Beide SQLite-Dateien bleiben zusammen am gleichen Ort. Ein Datenträgerwechsel oder
eine Kopie auf einen zweiten aktiven Host ist eine gesonderte Migration.
SQLite-Mutex bleibt über den vollständigen Lauf offen; `synchronous=FULL` für die
unabhängig committete Snapshot-DB. Es gibt keinen Ablaufzeitpunkt zum Stehlen der
Sperre. Vor Supervisor-Neustart muss der alte Prozess beendet sein. Betriebssystem-
Neustart darf den Dienst starten, jedoch keine offene Zustellung zurücksetzen.

Hostabnahme in P3: zwei echte Prozesse gegen denselben Datenträger; Abbruch an allen
Schreibgrenzen; Runnerverzeichnis verwerfen und neue Instanz starten; Hostneustart
mit überlebendem Store, Rechte-/Platzfehler und fehlender Mount. P2b simuliert dies
in isolierten lokalen Verzeichnissen. Ein Simulationspass beweist weder reale
Stromausfallsicherheit noch die Verfügbarkeit eines bislang unbenannten Hosts.

## 5. Überwachung, Stillstand und Verantwortlichkeit

Der Runner schreibt strukturierte, geheimnisfreie Statusdaten: Store-ID, Revision,
Code-/Config-Hash, Start/Ende UTC, letzte ausgewertete Kerze, letzter erfolgreicher
Watch-Check (auch ohne Warnung), offene/unklare Nachrichtenanzahl, feste Fehlerklasse
und letztes geprüftes Backup. Keine Nachrichtentexte, Token oder fremden HTTP-Bodies
in öffentlichen Logs. Exitcodes: 0 = erfolgreich, 10 = belegter Mutex-Konflikt,
20 = Migration/Config/Identität blockiert, 30 = unklare Zustellung,
40 = Store/Integrität, 50 = Daten/Transport ausdrücklich fehlgeschlagen.
Ein bloßes Prozessende 0 oder erfolgreicher Dispatch ist kein Gesundheitsnachweis.

Betriebsziele, keine zugesagte SLA: Alarm bei jedem `uncertain`/Integritätsfehler;
Signal fehlt 45 Minuten nach erwartetem 4h-Schluss; Watch-Check älter als 45 Minuten;
Lauf länger als 15 Minuten; kein geprüftes Backup seit 26 Stunden. Zwei aufeinander
folgende Mutex-Konflikte sind ebenfalls zu melden. Fehler halten weitere Sends
an; Zeitablauf entsperrt nichts. Ein toter Host kann sich nicht selbst melden.

P2b liefert einen lesenden `health`-Befehl und maschinenlesbares Ergebnis. Für P3
muss D3 einen tatsächlichen Verantwortlichen, Prüfzeiten und einen unabhängigen
Alarmkanal benennen. Bei GitHub können Workflow-Fehler Hinweise liefern, erkennen
aber allein keinen ausgebliebenen Start. Ein unabhängiger Prüfer oder ausdrücklich
übernommene manuelle Fristenkontrolle bleibt nötig. cron-job.org-Erfolg 204 beweist
nur die Dispatch-Annahme. Kein Alarmversand wird in P2a/P2b eingerichtet.

## 6. Unklare Zustellung: beleggestützte Klärung statt Reset

Unveränderte Originalnachricht, ID, Text-Hash, Zielbindung, Versuch und Revision
exportieren; alle Versender bleiben gesperrt. Ein Prüfer vergleicht einen konkreten
externen Zustellbeleg mit Ziel, Text, zeitlichem Zusammenhang und `message_id`.
Nur zweifelsfrei zuordenbarer positiver Beleg darf `uncertain → confirmed` bewirken.
Ein späteres Werkzeug benötigt erwartete Revision + ID + Prüfer + UTC-Zeit +
Beleg-Hash/geschützten Belegpfad; zuerst Prüfbericht, dann explizite Anwendung unter
derselben Store-Sperre. Originalzustand und Klärung bleiben nachvollziehbar.

Fehlender Chat-Eintrag, leere Suche, fehlende watch.json, Aussagen wie „wohl nicht
gesendet“ oder eine neue Operation-ID beweisen keine Nichtzustellung. Keine
Umwandlung nach `pending`/`rejected`, keine automatische Freigabe und kein
pauschales `--reset-uncertain`. Fehlt ein belastbarer Beleg, bleibt der Stream
gesperrt. Ein bewusster Verzicht oder eine absichtliche Neusendung trotz Unklarheit
wäre ein neuer gesondert zu entwerfender und freizugebender Vorgang, nicht P2b.
Alte Quittungslücken vor der Migration sind dagegen separat markierte unterdrückte
Historie gemäß Migrationsvertrag; sie werden nicht zu fiktiven Outbox-Versuchen.

## 7. Konsistente Sicherung und Rückfall

SQLite: Auslöser anhalten, laufenden Prozess geordnet beenden, Store-Mutex exklusiv
halten. Snapshot mit SQLite Backup API in ein neues Ziel kopieren, Integrität und
Body-Hash prüfen, Identität/Revision/Modus festhalten; Mutex-Schema konsistent
mitliefern oder offline neu erstellen, nie einen aktiven Lock kopieren. Rohkopie
von Dateien während Schreibbetrieb ist keine Sicherung.
Die [SQLite Backup API](https://sqlite.org/backup.html) dient der konsistenten
Datenbankkopie; der zusätzliche Betriebsstillstand bindet unsere mehreren Dateien
und Metadaten an denselben Stand.

Paket: DB/Snapshot, Control, Code-SHA, effektive Konfiguration, Migrationsquellen,
Quellen-/Datei-SHA256, Quittungs-/Klärungsjournal, Gesundheitsstatus. Neue eindeutige
Verzeichnisnamen, keine Überschreibung alter Sicherungen. Geschütztes zweites
Speicherziel vom Nutzer benennen; Kopie auf derselben Platte ist nur lokale
Wiederherstellung, keine Absicherung gegen Plattenverlust. Täglich und vor jedem
Update/Abgleich sichern; mindestens 7 Tages- und 4 Wochensätze als Betriebsziel,
in P2 keine automatische Löschung. Restoreprobe isoliert, ohne Transport/Zugang.

GitHub: vollständige Zustandsdatei an einer gepinnten Commit-SHA plus Historie und
Manifest exportieren; konkrete Regeln im separaten Adapterentwurf.

Nach Runnerverlust bei überlebendem aktuellem Store: aus Store wiederherstellen.
Nach Storeverlust oder altem Restore: **gesperrt** starten. SHA/Revision allein
beweisen nicht, dass danach nichts gesendet wurde. Den Zeitraum seit Sicherung
gegen erhaltene Nachfolgerevisionen und externe Zustellbelege abgleichen. Bei
fehlenden Belegen nicht starten; kein Wechsel zu neuem Store als Umgehung.
Nach erstem neuem Versand darf alter Code/Altzustand nie die Produktion übernehmen.
Code-Rollback nur mit lesekompatiblem aktuellen Store, ansonsten Versandhalt.

## 8. Konkrete noch notwendige Nutzerentscheidungen

| ID | Entscheidung in verständlichen Worten | Konsequenz ohne Antwort |
|---|---|---|
| D1 | Ist ein eigener Dauerläufer vorhanden (System/Datenträger/Verfügbarkeit), oder soll die separat entworfene GitHub-Variante umgesetzt werden? Bei GitHub: privates Zustandsrepository und begrenzte Schreibberechtigung dafür zulässig? | Gemeinsame Offline-Umsetzung fortsetzen; keine reale Runner-/Storefreigabe. Öffentliche Speicherung privater Journale ist kein Standard. |
| D2 | Beim späteren frischen Snapshot: unbekannte alte Zustellungen ohne Nachsendung akzeptieren? Falls aktive Position und alter Höchststop unbelegt bleiben: Betrieb mit ausdrücklich unbekannter Vorgeschichte und nur künftig monotonem Stop akzeptieren oder bis zum Beleg halten? | Migration als gesperrtes Prüfpaket möglich; Aktivierung verboten. Keine jetzt erfundene Pauschalzustimmung für zukünftigen Snapshot. |
| D3 | Wer reagiert auf Ausfälle/Unklarheit, welcher unabhängige Alarmweg und welches zweite geschützte Sicherungsziel stehen bereits zur Verfügung? | Health-/Backupwerkzeuge offline fertigstellen; Betriebsabnahme bleibt offen. |

Kein kostenpflichtiger Dienst ohne ausdrückliche Entscheidung. D1/D3 sind
Betriebsvoraussetzungen, D2 ist an die frische konkrete Migration gebunden.
Eine unbeantwortete optionale Frage und vergangene Zeit sind keine Zustimmung.

P2a-Schlussnachweise, exakte CI, Commit und Restore stehen in der additiven externen
`UEBERGABE.md/json`. Folgearbeit: `P2B-IMPLEMENTIERUNGSPLAN.md` und `START-P2B.md`.
