# Etappe 5a: Telegram-Versandliste und Wiederanlauf (F13)

29.09.2026. Eigener Zweig `codex/etappe-5a-telegram-outbox`, Arbeitsbaum
`C:/Users/oeztu/BTC-Trading/etappe-5a-work`, direkt aus der gesicherten Basis
`ebc01a48057994629c021bd84ab7f9a236678b70`. Exakte Abschluss-SHA und
GitHub-/CI-/Bundle-/ZIP-/Restore-Belege stehen nach Abnahme lokal in
`audit-backups/5a-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.

## Ergebnis und Vertrag

F13 ist im Hauptlauf korrigiert: neue Nachrichten werden mit dem verarbeiteten
Positionsstand dauerhaft vorgemerkt, sicher abgelehnte Sendungen beim nächsten
Lauf wieder versucht und bestätigte Nachrichten übersprungen. Wiederanlauf
benötigt weder eine neue Kerze noch einen neuen Handelsentscheid. Bereits
verarbeitete Kerzen werden nicht wieder ausgewertet. Unklare Zustellung stoppt
die Versandfolge, statt einen möglicherweise angenommenen Text zu duplizieren.

Vor Implementierung festgelegt: [F13-VERTRAG.md](F13-VERTRAG.md).
Die lokale ID ist SHA256 über Art, Ereigniszeit, Sequenz und fachlichen Inhalt;
gespeicherter Text samt zusätzlichem SHA256 bleibt stabil. Sie ist ausdrücklich
kein Telegram-Idempotenzschlüssel und verändert keine Signal-/Chart-ID (F17).

`state.json` ist der maßgebliche atomare Commit. `_delivery` Version 1 enthält
Versandabsichten, unveränderliche Texte, Status, Anzahl der Versuche, Zielhash,
Telegram-message_id und Projektionen von Signalhistorie/OI sowie gegebenenfalls
Flush-Auflösung. Neue Position/Dedupe und zugehörige Absichten werden gemeinsam
gespeichert. `signals.json`, `oi_history.json` und passende Flush-Auflösung sind
reparierbare Projektionen; ein Schreibfehler dort löscht keine Versandabsicht.
Der Positionscodec bleibt Schema 2, der Offline-V1-Checkpoint bleibt Schema 1.
Die Versandliste wird nicht auf die 500 Chart-Signale gekürzt; bestätigte IDs
bleiben erhalten. Das bedeutet wachsenden Speicher und vollständige lokale
Snapshot-Schreibvorgänge; keine unbewiesene unbegrenzte Skalierbarkeit.

Temporäre Datei, flush/fsync, atomarer Ersatz und auf POSIX Verzeichnissynchronisation
begrenzen die Prozessabsturzfenster. Ein OS-Dateilock serialisiert Hauptläufe
auf demselben lokalen Datenpfad; Prozessende gibt ihn frei. Ungültige/künftige
Versandschemata, doppelte IDs, Textveränderung oder Bestätigung ohne message_id
werden vor Versand und Datenüberschreibung abgewiesen. Token und rohe
Transport-Exceptions werden weder gespeichert noch ausgegeben. Das gebundene
Chat-Ziel wird ausschließlich als Hash gespeichert; Zielwechsel blockiert.

| Status | Bedeutung / Wiederanlauf |
|---|---|
| pending | dauerhaft vorgemerkt; fehlende Zugangsdaten sind keine Bestätigung |
| sending | vor API-Versuch gespeichert; nach Prozessabbruch uncertain |
| rejected | explizite Telegram-Clientablehnung; nächster Lauf versucht einmal erneut |
| confirmed | ok=true und positive integer message_id dauerhaft gespeichert; nie erneut senden |
| uncertain | Timeout, ungültige Antwort, Serverfehler oder unterbrochener Versuch; Folge blockiert |
| preview | expliziter Dry-run; terminal, auch bei später gesetzten Zugangsdaten kein Versand |

`deliver_telegram` unterscheidet diese Transportergebnisse. HTTP-4xx gilt nur mit
explizitem strukturiertem Fehler als sicher abgelehnt; HTTP-5xx und verlorene/
unvollständige Antworten sind konservativ unklar. Hauptlauf sendet strikt nach
gespeicherter Reihenfolge: bisheriger Plan/Vorschau/Flush, dann je Kerze E41,
E42 und einzelne Signale. Eine Lücke stoppt Nachfolger. Pro Hauptlauf wird jede
sicher abgelehnte Nachricht höchstens einmal versucht; keine Endlosschleife.

Die Bot-API liefert bei Erfolg ein Message-Objekt, bei Fehler ok=false und
Fehlerangaben. Dies ist API-Annahme, kein Beweis, dass der Empfänger gelesen
oder eine manuelle Order ausgeführt hat. Die dokumentierten sendMessage-Parameter
enthalten keinen allgemeinen Idempotenzschlüssel. Unsere Entscheidung, unklare
Fälle anzuhalten, folgt aus dieser fehlenden sicher belegbaren Wiederholbarkeit.
Quelle, 29.09.2026: [Telegram Bot API – Requests](https://core.telegram.org/bots/api#making-requests),
[sendMessage](https://core.telegram.org/bots/api#sendmessage).

## Netzfreie Belege

Gezielt gelesen wurde nur F13 im unabhängigen Audit `ccf2b01` samt
`audit/additional_probes.py`, `audit/telegram_order.py` und zugehörigen Ergebnissen.
Kein Gesamtaudit. Original-F13 auf unverändertem Etappe-4-Code erneut erreicht,
diesmal mit echter Strategieauswertung KAUF_1: erster Lauf ein Signal/ein
fehlgeschlagener Versuch, gleicher zweiter Lauf null Signale/null Versuche.
[Ausgangsbeleg](5a-baseline-f13.json), [Skript](../../tools/verify_5a_baseline.py).

- **712/712 Tests**, davon **alle 676 bisherigen unverändert** und **36 neue**.
  Kein alter Test gestrichen oder angepasst. [Testprotokoll](5a-tests.log).
- Hauptlauf erreicht realen KAUF_1, tatsächlichen Positionsstand T1 und Dedupe.
  Ablehnung → gleicher Text/gleiche ID → Bestätigung nach Neustart; keine neue
  Position, kein zusätzlicher Kauf, keine Signalhistorien-Doppelung.
- Echter HTTP-Parser im Hauptlauf mit ausschließlich Fake-Responses:
  429-Ablehnung, erfolgreicher Neustart mit message_id 77; ok ohne ID wird unklar.
  Timeout nach simulierter Annahme, HTTP-500, HTTP-4xx ohne Beleg, malformed JSON,
  URLError, legacy boolean, fehlende Zugangsdaten, Dry-run und Zielwechsel geprüft.
- Erreichter realer E41-Wartezweig vor zwei realen Teilverkäufen: FIFO bleibt
  erhalten; Ablehnung in der Mitte wiederholt nur den Rest, Unsicherheit stoppt ihn.
  Plan/Vorschau werden vor Transport gespeichert; Flush-Auflösung überlebt einen
  beschädigten Projektionsstand, ohne eine neuere Warnung zurückzusetzen.
- Schreibfehler vor Commit: kein Versand/keine Positionsfortschreibung. Fehler
  nach Commit bei Signalprojektion: Neustart repariert und sendet ohne Signalreplay.
  Fehler vor saving sending: kein Versuch; Fehler nach Antwort beim Quittieren:
  gespeichertes sending wird beim Neustart uncertain, keine automatische Doppelung.
- **Fünf echte Prozessabbrüche** mit os._exit in separaten Python-Prozessen:
  vor Commit, nach Commit, nach sending/vor API, nach simulierter Annahme,
  nach dauerhafter Quittung. Festgelegte Wiederanlaufzustände geprüft. Ein sechster
  Prozess prüft konkurrierenden Zugriff; Sperre und anschließende Freigabe passen.
- Aktiver Altbestand/Historie bleiben erhalten; keine alten Sendungen rekonstruiert.
  Fehlende Kerzen/Fetchfehler hindern Wiederholung der vorhandenen Liste nicht.
  Beschädigte Signal-/OI-Projektionen werden aus der Transaktion repariert.
- **16/16 F13-Sabotagen** erst nach jeweils erreichtem grünem Ausgangsfall erkannt.
  Dazu vergessene Absicht, unstabile ID, erneut gesendete Bestätigung/Unsicherheit,
  übersprungener Versuchsspeicher, verlorene Quittung, überholte Ablehnung,
  falsche Serverfehlerklassifikation und ignorierter Ziel-/Schema-/Textkonflikt.
  [Sabotagen](5a-sabotage.json), [Skript](../../engine/sabotage_5a.py).
- Bestehende Schutzproben: **4 23/23**, **3b 19/19**, **D01 6/6**, **F09 3/3**.
  [4](5a-4-sabotage.json), [3b](5a-3b-sabotage.json),
  [D01](5a-d01-sabotage.log), [F09](5a-f09-sabotage.log).

## Erhaltener Umfang, Abschluss und Grenzen

F09/D01, kompletter V1-Vertrag, Gebühren/Slippage, Schluss-DD/obere Intrabar-Grenze,
Restlose/Kosten, Stopmaxima und Positionsschema werden unverändert erhalten.
`strategy_core.py`, `execution_v1.py`, `inventory.py`, `position_state.py`,
`backtest.py`, sämtliche bisherigen Tests, `site/`, Workflows und bestätigte
Verträge sind gegenüber ebc01a4 identisch. Keine neue Strategiemessung oder Schwelle.
Sechs gespeicherte V1-Fortsetzungen und unabhängige Kostenrechnungen werden im
frisch restaurierten Abschlussbundle erneut geprüft; keine neuen Eingaben/Zeilen.

Vor Push geprüft: nur Tests reagiert auf diesen Zweig; Pages nur auf main/site
oder Signal-Engine/Backtest, niemals Tests. Alle anderen Workflows bleiben
Schedule/Handstart. Kein Dispatch. [Scope-Prüfer](../../tools/verify_5a_scope.py).
GitHub-Prüfer liest ausschließlich eigenen Remote-HEAD, Tests zur exakten SHA,
main zur Beobachtung und unverändertes Sicherungstagobjekt/-ziel. Danach Bundle,
ZIP, vollständiger Baumvergleich, frischer Restore, 712 Tests und sämtliche
Schutzproben sowie sechs identische V1-Prozessfortsetzungen.
[Abschlussprüfer](../../tools/verify_5a_backup.py).

**Keine Exactly-once-Garantie.** Ein Absturz nach gespeichertem sending, aber vor
dem API-Aufruf bleibt konservativ unklar; das kann ohne tatsächlichen Versand
die Liste anhalten. Unklarheit benötigt separate manuelle Klärung mit Zustellbeleg;
in 5a kein automatischer Freigabemechanismus, kein historisches resend-all.
Ein dauerhaft falsch konfiguriertes Ziel bleibt rejected; kein unbelegter Erfolg.

**Dauerhaftigkeit gilt auf dem überlebenden lokalen Datenpfad.** Der bestehende
GitHub-Workflow übernimmt site/data erst nach dem Python-Lauf in Git. Geht ein
ephemerer Runner davor vollständig verloren oder scheitert dessen anschließender
Git-Push, kann dessen jüngste lokale Transaktion fehlen. Damit ist eine vollständige
hostübergreifende Betriebsgarantie ausdrücklich nicht bewiesen. Vor einem eigenen
Live-Go braucht dieser Betriebspfad eine dauerhafte externe Transaktionsablage
oder eine entsprechend geprüfte Workflow-Aufteilung. In dieser Etappe wird kein
Workflow/Deployment verändert. Lock schützt keine voneinander getrennten Hosts,
fsync schützt nicht gegen verlorene Datenträger oder zerstörtes Dateisystem.

Der korrigierte Bereich ist `run_engine` einschließlich seiner Flush-Auflösung,
E41/E42, Plan, Vorschau und Signaltexte. Eigenständige `--watch`, `--lage`,
`--test-telegram` und ausdrücklich manuelles `--resend-all` bleiben bestehende
Einmalbefehle; deren eigener dauerhafter Versand ist kein Abnahmebeleg dieser Etappe.
Keine manuelle Live-Ausführung wird aus Telegram rekonstruiert.

Privates Backup-Repo und fremde Arbeitsbäume nicht committet; keine neueren
main-/E44.4-/E44.5-Commits übernommen. Originale, private Volltranskripte und
Sicherungstag unverändert. Keine echten Nachrichten, Orders, Live-Schalter,
Deployments oder main-Push/Merges. F17 bleibt **5b**; V2, Shorts/Margin/Funding,
E41.6 und weitere Befunde bleiben getrennt.

Nächster ausschließlich separater Auftrag: [START-5B.md](START-5B.md),
**GPT-6 Sol / Aufwand mittel**, bei unklaren Herkunftskollisionen hoch.
Empfehlung nach Aufgabenrisiko, keine automatische Modellumstellung.
5a nach geprüfter GitHub-/Bundle-/Restore-Abnahme beenden, 5b nicht starten.
