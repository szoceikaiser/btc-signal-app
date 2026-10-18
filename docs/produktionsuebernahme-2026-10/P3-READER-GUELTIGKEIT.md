# Begrenzte aktuelle Gültigkeit für die unveränderte Reader-Historie

12.10.2026. Offlinevertrag, kein menschlicher Grant und kein reales Startdatum.
Ergänzt P3-SKRIPTSTART-FORTSETZUNG.md ausschließlich an der aktuellen Zeitgrenze.
Die dortige Originaldeadline bleibt historisch unverändert und für alle normalen
Phasen sowie Upload weiterhin wirksam. Die frühere940-Testhistorie samt Windows-,
Pfadlängen- und Timeoutbefunden bleibt erhalten; kein neuer uneingeschränkt grüner
Gesamtlauf wird aus diesem Nachtrag abgeleitet.

## Originalvertrag und aktuelle Gültigkeit

`validate_plan_structure` prüft den vollständigen Originalvertrag einschließlich
der syntaktisch vollständigen UTC-Deadline. Das gewährt allein keine Ausführung.
`validate_plan` prüft zusätzlich deren heutige Gültigkeit und bleibt der Einstieg
aller normalen Phasen. Deren GrantGuard prüft weiterhin Plan UND Grant.

Nur `bootstrap-rules403-preget-once` mit exakt geprüftem v2-Nachtrag darf statt des
verstrichenen Originalendes ein eigenes aktuelles Reader-Fenster verwenden. Kein
CLI-Schalter zum Ignorieren von Ablauf, kein Ändern des Plans oder SQLite-Digests.
Die Klassenprüfung bleibt dieselbe kanonische RulesGuard mit striktem isinstance.

Die v2-Amendierung enthält `reader_validity` mit Originalplanhash, unverändertem
Originalende, exakter21-Zeilen-Frontier und GET5/PUT0/Git0, unabhängigem Reviewhash,
UTC-Start und UTC-Ende. Der Start liegt nach dem alten Planende; Ende muss später
als Start und höchstens60Minuten danach liegen. Amendierungsende entspricht genau
diesem Ende. Der menschliche Phasengrant bindet den Hash der ganzen Amendierung
und darf deren Ende nicht überschreiten. Review und Autorisierung bleiben getrennte
Belege. Echte Kalenderdaten werden erst später im Hauptchat gebunden.

Alle alten Grants/Amendierungen und Ereignisse behalten ihre damaligen Grenzen.
Die vollständigen17altenZeilen plus die vier belegten Vor-GET-Diagnosezeilen werden
weiter exakt geprüft. Schon eine frühere Diagnose-Requestreservierung, unbekannte
Antwort, andere Frontier oder Pushvorbereitung schließt den Fall aus. Root, drei
alte Journale/Marker, Lock und DB-Bytes bleiben gebunden; positives Prozessende,
echter Terminal-Endbericht und pausierte Trigger sind erforderlich. Keine erfundene
Parent-Wait-Quittung. Der neue Executor benötigt vollständige aktuelle Dateipins
und einen Nachfolger des abgenommenen cd082c2 samt historischem Materialisierungsbezug.

## Dauerhafte Grenzen und Ablauf

Die vorhandene Kernel-Sperre, SQLite-FULL, fsync und bestätigte Publikation bleiben
unverändert. Nach der dauerhaft publizierten phase_start-Zeile entsteht vor jeder
Reader-Eingabe die neue `reader_validity`-Zeile: vollständiger Nachtrag, dessen Hash,
Amendierungs-/Granthash und aktueller Code. Jede Unklarheit sperrt den Prozess;
kein Request vor bestätigter Zählung. Keine automatische Wiederholung oder Reparatur.

Gültigkeit wird vor Ledgerbeginn/Eingabe, unmittelbar vor jeder Reservierung und
jedem Outbound sowie direkt vor confirmed geprüft. Der tatsächliche Zeitraum
einschließlich Eingabe/Prüfung zählt. Start inklusive, Ende exklusiv; das genaue Ende
sperrt. Die effektive Uhr ist mindestens die verstrichene monotone Prozesszeit;
Wallclock-Rücksprung sperrt dauerhaft im Prozess, persistente Highwater bleibt
maßegeblich. Kein unbelegtes Versprechen gegen beliebige Systemuhrmanipulation.

Eine rechtzeitig gestartete Antwort nach Ablauf bleibt gezählt/protokolliert, darf
keinen Folgerequest oder confirmed auslösen. Keine Nachlaufzeit und kein Readback-
Sonderrecht. Verlorene Antwort bleibt unknown und gesperrt. Ablauf unmittelbar vor
Abschluss kann einen offenen, nicht bestätigten Frontierzustand hinterlassen;
dieser wird nicht automatisch erneut ausgeführt.

Sieben feste Routen und sichere403-Klassifikation bleiben. Beide Diagnosephasen
zusammen maximal8zusätzlicheGETs, AltGET5 bleibt gezählt. Gemeinsamer Bootstrap128,
globalGET384/PUT48/Git1/49Mutationen unverändert. Reader-Nachtrag PUT0/Git0 und kein
Writer. Positiv:41Zeilen (eine neue dauerhafte Gültigkeitszeile), GET12/PUT0/Git0.
Auch dann `upload_eligible=false`: dieser Zeitvertrag eröffnet keinen Upload.
Bestehender Upload kann ihn weder übernehmen noch aus ihm ein eigenes Recht
ableiten. Ein späterer Upload benötigt einen separat entwickelten/abgenommenen
aktuellen Vertrag; in diesem Auftrag kein solcher Zeitnachtrag. Aktivierung/P4 offen.

## Vorlage und Starter

`P3-READER-GUELTIGKEIT.template.json` ist der v2-Amendierungsentwurf.
`P3-READER-GRANT.template.json` enthält keine menschliche Autorisierung. Die additive
Lieferung enthält zusätzlich einen auf die echten21Zeilen bezogenen Entwurf mit
offenen Start-/End-/Review-/Grantdaten. Keine neue Session und kein neues Root.

Nach unabhängiger Hauptchat-Abnahme und späterem tatsächlichem Review/Grant:
sichtbaren `tools/p3_rules403_start.ps1` mit `-Phase DiagnoseFortsetzen`, konkreten
Plan-/Amendierungs-/Grantpfaden und unabhängig geprüftem Amendierungshash verwenden.
Der Starter verlangt v2 und ruft den tatsächlichen `python -B tools/p3_rules403.py`
auf. Er prüft alle Laufzeitbindungen zusätzlich im Pythonvertrag. Reader bleibt
beim Nutzer; kein Grant wird durch dieses Werkzeug erzeugt. Nach HALT nicht erneut
starten; Ergebnisort und sichere Kategorie im Hauptchat prüfen lassen.

Der Nutzer meldet Fertigstellung selbst. Keine Nachricht an andere Chats. Kein neuer
Start-/Fortsetzungsprompt erforderlich; kein Prompt durch diesen Vertrag erstellt.
