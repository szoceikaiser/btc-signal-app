# A4 – Schnittstelle und offene Betriebsbereitstellung

Implementiert und simuliert geprüft; **nicht real bereitgestellt**. Die bestehenden
GitHub-Workflows sind unverändert. Ein GitHub-hosted Runner hat damit noch kein
persistentes Volume. Die neue Versandstrecke verweigert ohne dieses Volume den
Versand; ein Merge oder eine Aktivierung ist nicht Teil von A4.

## Adaptervertrag

`engine/durable_delivery.py` stellt `provision(path, store_id, snapshot)` sowie
`VolumeStore` bereit. Initialisierung erfolgt ausschließlich separat mit einem
geprüften Snapshot, niemals durch den Lauf. Der neue Pfad muss fehlen; vorhandene
Stores werden nicht überschrieben. Der Snapshot enthält `version: 1`, `engine`,
`watch` und `commands`. `engine` ist entweder ein ausdrücklich neuer leerer Stream
oder vollständiger Zustand mit `_delivery` Version 1 einschließlich `signals`
und `oi_history`. Bestehende aktive Positionen, verarbeitete Zeiten und sämtliche
Outbox-Einträge müssen übernommen werden. Altzustände ohne Outbox benötigen vor
Provisionierung eine geprüfte Migration in dieses Schema; die Funktion verweigert
deren stillen Import. Das gilt auch für Demo-Zustände. Frühere Zustellungen ohne
Quittung werden dadurch nicht nachträglich bewiesen. Unklare Vorgänge müssen vor
einer echten Migration anhand externer Belege geklärt werden.

Laufzeitparameter (keine Geheimnisse):

| Variable | Bedeutung |
|---|---|
| `BTC_DELIVERY_STORE` | Absoluter Pfad auf dem separat bereitgestellten Volume |
| `BTC_DELIVERY_STORE_ID` | Gepinnte Identität des zuvor provisionierten Stores |
| `BTC_DELIVERY_RUNNER_ROOT` | Absoluter Wurzelpfad des gesamten flüchtigen Runners; Datenpfad muss darin und Store außerhalb liegen |
| `BTC_DELIVERY_OPERATION_ID` | Stabile Auftrags-ID für `--lage`, `--test-telegram`, `--resend-all`; bei Wiederanlauf identisch, bei ausdrücklich neuem Auftrag neu |

Der Pfadvergleich prüft Konfigurationskonsistenz. Er kann nicht beweisen, dass ein
Volume tatsächlich runnerunabhängig gemountet wurde. Dies ist gesondert im Betrieb
nachzuweisen. `--watch` erhält seine Identität aus der Kerze und speichert seinen
Merker mit dem Nachrichtenbatch. Alle Pfade teilen einen Store und dessen Mutex.
Pro Stream/Telegram-Ziel ist genau ein Store zu betreiben; Kopien oder Wechsel der
Bot-Identität sind keine unterstützte Wiederherstellung. Der Telegram-Token bleibt
flüchtig; gespeichert wird nur die bestehende Chat-Zielbindung als Hash.

Der Mutex verwendet eine während des gesamten Laufs offene SQLite-Transaktion in
`mutex.sqlite`. Die unabhängige Snapshot-Datenbank `snapshot.sqlite` committet jede
Schreibgrenze mit `synchronous=FULL`, Revision und Inhalts-SHA256. Der Hash erkennt
versehentliche Beschädigung, ist keine Authentifizierung gegen einen Angreifer.
Dateisperren müssen für sämtliche beteiligten Prozesse auf demselben persistenten
Dateisystem wirksam sein. Ein konkurrierender Lauf scheitert sofort, statt die
Zustellung eines noch laufenden Prozesses als unterbrochen zu behandeln. Lange
Datenabrufe halten den Mutex; das ist eine bewusste Verfügbarkeitsgrenze.

Nach einem Prozessende wird gespeichertes `sending` zu `uncertain`. Das blockiert
auch einen Auftrag mit neuer Auftrags-ID. Es gibt keinen Reset-CLI und keinen
automatischen Retry dieser Einträge. Bestätigte Aufträge geben bei Wiederholung
ihren gespeicherten Ergebnisstand zurück. Explizit abgelehnte oder pending
Befehle verwenden gespeicherte Texte ohne erneuten Marktabruf. Beim Hauptlauf
erfolgt Wiederherstellung und offener Versand vor dem Marktabruf. Lokale
`state.json`/Projektionen und `command-delivery.json` sind ersetzbare Spiegel.

## Noch vor echtem Betrieb erforderlich

Ein geeigneter persistenter Host/Datenträger oder ein separat entworfener Dienst,
Zugriffsrechte, Überwachung, geprüfte Migration und eine passende Runner-Anbindung
sind **offen**. Die jetzigen Workflows setzen keine dieser Variablen und werden
durch A4 nicht eingerichtet. SQLite über beliebiges NFS, voneinander unabhängige
Runnerkopien oder geteilte Stores ohne zuverlässige Locks sind nicht unterstützt.
Eine Sicherung der Quelldateien ist kein laufender Versandstore. Verlust oder
Rückrollen des Volumes selbst bleibt außerhalb der geprüften Garantie. Backups
des Stores benötigen einen konsistenten SQLite-Snapshot bei quieszentem Betrieb;
ein altes Backup darf nicht ohne Zustellabgleich als aktueller Stream starten.

Die Abnahme entfernt nur vollständig isolierte temporäre Runner. Sie beweist die
Wiederherstellung bei überlebendem Volume mit simuliertem Transport; weder echte
Telegram-Zustellung noch physische Stromausfall-/Datenträgerresilienz. Für
`uncertain` ist separate beleggestützte Klärung erforderlich. Keine Exactly-once-
Zusage, keine Broker-Fills und kein Live-Go.
