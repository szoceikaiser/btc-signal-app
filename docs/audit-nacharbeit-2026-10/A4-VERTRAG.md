# A4 – Versandvertrag v1 (vor Implementierung)

Basis: aaadbf6606ae1082e2eb59fd0ef1e1d4e1f23c1b. Ausschließlich Rest F13.
Keine Ergebnismessung von Handelsstrategien und keine echte Nachricht.

## Inventar und Grenze

Der Hauptlauf schreibt lokal Intent, sending und Quittung. signal.yml übernimmt
site/data erst danach in Git. Runnerverlust vor diesem Push verliert auch eine
lokale confirmed-Quittung; erneutes Checkout kann dasselbe Signal erneut senden.
Verlorenes pending verschwindet ebenfalls, falls die Eingabe nicht reproduzierbar
ist. Wiederherstellung muss deshalb vor Marktabruf und Entscheidung erfolgen.
Tatsächlich ausgeschlossene Pfade sind --test-telegram, --resend-all, --lage
und --watch (letzterer ist auch periodisch). Sie benutzen send_telegram ohne
dauerhafte Quittung; watch schreibt den Merker erst nach dem Senden.

## Identität, Zustände und Schreibgrenzen

Die bestehende SHA256-ID aus Typ, Ereignis, Sequenz und Inhalt bleibt gültig.
Gespeicherter Text und Zielbindung bleiben unveränderlich. Die ID ist kein
Telegram-Idempotenzschlüssel. Manuelle Befehle benötigen zusätzlich eine explizite
stabile Auftrags-ID: Wiederholung desselben Auftrags stellt denselben gespeicherten
Batch wieder her, ohne dessen Text neu zu berechnen. Eine absichtliche neue
Neusendung ist ein neuer Auftrag; kein Mittel zur Freigabe unklarer Zustellungen.
watch verwendet die Kerzenidentität und einen gemeinsam dauerhaft gespeicherten
Merker. Handelszustand und Befehlsjournal bleiben getrennt.

Vor dem ersten Versand werden vollständiger Intent und erforderlicher
Fortsetzungszustand außerhalb des Runners committed. Vor jedem Transportaufruf
wird sending dort committed. Erst eine strukturierte positive message_id erlaubt
confirmed und einen weiteren dauerhaften Commit. Bestätigte Einträge werden nicht
erneut gesendet. Explizite Ablehnung erlaubt Wiederholung, ungültige Antwort,
Timeout und überlebendes sending werden uncertain. Auch Abbruch zwischen sending
und dem ersten Netzwerkbyte bleibt vorsichtshalber uncertain. Kein automatischer
Reset; unklare Zustellung sperrt auch neue Befehle desselben Stores. Keine
Exactly-once-Garantie und keine Behauptung, uncertain sei zugestellt.

## Adapter und Bereitstellung

Implementiert wird ein SQLite-Snapshotadapter auf einem separat bereitgestellten,
persistenten Volume. Das Volume muss den gesamten Runner überleben, dieselbe
Store-ID behalten und zuverlässige SQLite-Dateisperren und fsync bieten.
Ein separater SQLite-Mutex bleibt während des ganzen Laufs gehalten; Snapshot-
Transaktionen committen unabhängig davon mit synchronous=FULL. Prozessende gibt
den Mutex frei. Konkurrierende Runner mit Zugriff auf denselben geeigneten
Datenträger werden serialisiert/abgewiesen. Getrennte Kopien, NFS, Split-Brain,
Volume-Verlust und Rückspielen veralteter Speicherbackups sind nicht abgesichert.
Das ist kein direkt auf GitHub-hosted Runnern bereitgestellter Speicherdienst.

Initialisierung ist ausdrücklich separat und erfordert geprüften Anfangszustand
(Migration vorhandener Position/Historie/Outbox/Watch). Kein automatisches Anlegen
oder Leeren beim Start, kein Rückfall auf Git bei fehlendem/defektem Store. Pinning
der Store-ID verhindert versehentlichen Wechsel. Ohne Bereitstellung wird realer
Versand vor Verarbeitung verweigert. Token werden weder gespeichert noch gelesen
durch diese Etappe; Tests verwenden ausschließlich künstliche Zugangswerte.
Lokale JSON-Dateien sind im dauerhaften Modus reparierbare Spiegel. Dry-run nutzt
nur lokale Vorschau und verändert die dauerhafte Ablage nicht.

## Abnahme

Original-F13 und Runnerverlust vor Korrektur netzfrei reproduzieren. Danach echte
Kindprozesse an Intent-, sending-, Annahme- und Quittungsgrenzen hart beenden;
vollständiges temporäres Runnerverzeichnis entfernen und aus separater Ablage
wiederherstellen. Prüfen: keine verlorenen gespeicherten Intents, kein erneuter
Versand bestätigter/unklarer Einträge, kein Signalreplay, Ablehnungsretry,
Schreibfehler, defekter/fehlender/falscher Store, Konkurrenz, ausgeschlossene
Befehle und A1–A3/5a-Regression. Betriebsbereitstellung bleibt ausdrücklich offen.
