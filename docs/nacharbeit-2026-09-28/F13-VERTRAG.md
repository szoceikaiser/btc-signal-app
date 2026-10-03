# F13: Versandvertrag vor Umsetzung (29.09.2026)

Basis ebc01a48057994629c021bd84ab7f9a236678b70. Nur Hauptlauf in
main.run_engine und Telegram-Transport; F17 und Handelsverträge bleiben getrennt.

1. Eine Nachricht erhält eine deterministische SHA256-ID aus Nachrichtentyp,
   Ereigniszeit, Sequenz innerhalb des Ereignisses und fachlichem Inhalt.
   Formatierter Text bleibt unveränderlich gespeichert. Die ID ist lokale
   Identität, kein Telegram-Idempotenzschlüssel. Signal-/Chartschema unverändert.
2. state.json wird die atomar ersetzte maßgebliche Transaktion: Positionsstand,
   verarbeitete Zeit, Versandabsichten und reparierbare Projektionen von
   signals.json/oi_history.json sowie gegebenenfalls Flush-Auflösung. Vor diesem
   Commit keinerlei Hauptlauf-Versand. Altzustände übernehmen ihre Historie;
   keine Rekonstruktion alter Sendungen und kein Positionsreset.
3. Versandliste Version 1: pending, sending, rejected, confirmed, uncertain,
   preview. Vor jedem externen Versuch sending dauerhaft speichern. Nur
   ok=true mit gültiger message_id ist confirmed. Telegram-Ablehnung ist
   rejected und beim nächsten Hauptlauf erneut versuchbar. Fehlende Zugangsdaten
   lassen pending bestehen. Dry-run erzeugt ausschließlich terminale preview.
4. Timeout, Verbindungs-/Antwortfehler und Prozessende nach sending sind uncertain:
   Telegram könnte angenommen haben. Keine automatische Wiederholung solcher
   Einträge. Sie sperren nachfolgende Nachrichten, ebenso Ablehnung, damit die
   fachliche Reihenfolge erhalten bleibt. Manuelle Klärung ist separat nötig;
   in 5a keine echten Klärungs-/Wiederholungsnachrichten. Keine Exactly-once-Zusage.
5. Neustart repariert Projektionen aus state.json, verarbeitet keine alte Kerze
   erneut und versucht offene sicher abgelehnte/pending Nachrichten in Reihenfolge
   auch ohne neue Kerzen. Bestätigte Nachrichten werden nie erneut versandt.
   Nachrichtenziel wird vor erstem Versuch gebunden; Zielwechsel sperrt Versand.
   Token und rohe Exceptions werden niemals dauerhaft/loggend ausgegeben.
6. Ein Betriebssystem-Dateilock serialisiert Hauptläufe auf demselben lokalen
   Datenpfad; atomarer Ersatz plus fsync begrenzen Prozessabsturzfenster.
   Keine Garantie gegen Plattenverlust, Dateisystem-/Hardwarefehler oder mehrere
   Hosts mit getrennten Kopien. GitHub-Runner müssen den letzten lokalen Commit
   extern dauerhaft übernehmen: bestehender Workflow committet erst nach dem Lauf.
   Ein Runnerverlust davor bleibt eine explizite Betriebsgrenze, kein Live-Go.

Abnahme netzfrei: erreichte Original-F13-Probe; Transport-Ablehnung und Timeout
nach simulierter Annahme; Absturz vor/nach Transaktionscommit, vor Versuch/nach
Annahme/nach Bestätigung; Projektionen/Schreibfehler; mehrere Nachrichten und
E41/E42-Reihenfolge; Neustart in neuem Prozess; Altposition/Historie; Dry-run,
fehlende Zugangsdaten, Zielwechsel, ungültiges Schema und konkurrierender Lauf.
676 vorhandene Tests bleiben erhalten. Alle Sabotagen erst nach erreichtem
grünem Produktionsfall. Keine echte API-Nachricht, Order oder Workflow-Dispatch.
