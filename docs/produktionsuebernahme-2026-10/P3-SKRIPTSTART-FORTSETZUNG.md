# Direkter Skriptstart und einmalige Vor-GET-Fortsetzung

Stand 12.10.2026. Lokale Vorbereitung, keine tatsächliche Diagnose und kein
neuer Grant. Ergänzung zum Regeln-403-Vertrag; keine allgemeine HALT-Ausnahme.

## Korrigierte Abdeckung und Eintritt

Die frühere Lieferung prüfte importiertes `r.main`, auch in Childprozessen.
Das deckte den tatsächlichen `python -B tools/p3_rules403.py`-Start nicht ab.
Bei HEAD4c157a7 definierte der direkte Start `__main__.RulesGuard`, während
Boundary die Klasse aus `p3_rules403` prüfte. Die beiden Identitäten waren
verschieden; der strikte Check stoppte vor jeder Requestreservierung. Kein
Enginefehler, keine neue GitHub-Auth-/Tarifaussage. Diese Abnahmelücke wird
ausdrücklich korrigiert; alte versiegelte Berichte werden nicht umgeschrieben.

Der Skripteintritt delegiert jetzt vor jeder Klassendefinition an das kanonisch
importierte Modul. Beide Eintrittswege verwenden genau dieselbe RulesGuard.
Der isinstance-Check bleibt unverändert; keine Duck-Typing-Ausnahme, kein
Akzeptieren einer zweiten Klasse und kein Alias in sys.modules. Reader401 und
Probe-Launcher wurden auf dieselbe konkrete Ursache geprüft: deren Pfade
vergleichen keine dort unter __main__ definierte Klasse mit einem unabhängigen
Import. Sie werden nicht sachfremd geändert.

## Ausschließlich der belegte 21-Zeilen-Fall

Neue Phase `bootstrap-rules403-preget-once`, eigenes festes gleichnamiges
Journal im ursprünglichen Sessionordner. Die alte Diagnose bleibt verbraucht.
Ihr Originalexecutor HEAD `4c157a780d4db8482edcaab88d35d81dbcb17e54`, Tree
`0a2931ee742b5a4adae2bedaa7b81fef9e56ce60` und dessen vollständige 37Dateipins
einschließlich expliziter Git→Arbeitsbyte-Materialisierung werden zusätzlich
zu b0b0386/0128237 gebunden; neue Ausführung besitzt eigene HEAD/Tree/Dateipins.
Originalplan/Seed werden nicht ersetzt.

Erforderlich sind exakt die bekannten ersten17Zeilen und danach ausschließlich
phase_start → authorization → rules403_amendment → phase_halt. Alle vier
Zeilen besitzen GET5/PUT0/Git0 und den alten Diagnosenamen; gültiger damaliger
Grant/Amendierung/Originalplan, alte Codepins und Vorgängerbindung müssen
stimmen. Bereits eine Requestreservierung, unknown-Response, anderer Abschluss,
fehlender Marker, unsichere Publikation oder irgendeine Pushvorbereitung
schließt diese Fortsetzung aus. Keine Exceptionursache wird nachträglich als
damals aufgezeichnet behauptet: Grundlage sind gepinnter Code, genaue
Zeilenform, direkte Offline-Reproduktion und unabhängiger Review.

Die neue Amendierung enthält `interrupted_diagnosis` mit vollständiger alter
Diagnoseamendierung, altem Grant und alter Code-Materialisierung. Sie bindet
die gesamte jüngste DB-/Lock-/Dreijournal-/Dreimarkerfrontier und den Root.
Unter exklusivem Kernel-Lock werden alle alten Journalpräfixe bytegleich
geprüft, der zuletzt gestartete PID frisch auf Ende/Abwesenheit geprüft und
ein tatsächlicher Terminal-Endbericht samt synchronem Codepfad verlangt.
Keine erfundene Parent-Wait-Quittung. Dann neue dauerhafte Startabsicht.
SQLite FULL, fsync, bestätigte Publikation und UTC-Highwater bleiben maßgeblich.
Kein Reset, Cleanup, neuer Ordner, Frist-/Ownerablauf oder automatischer Retry.

Realer Eingang:21Zeilen, Frontier
`30a8b2ac6de72e1ad93c5f88da80c15e3194989544acafafa50521099c3156df`,
Highwater `2026-10-12T06:30:43.734391Z`, GET5/PUT0/Git0. PID19940 plus
tatsächlicher Terminal-Endbericht; frische Prüfung vor späterem Start nötig.

## Rechte, Budget und Gültigkeit

Nur Reader einmal verdeckt einfügen, Enter. Keine Writer-Abfrage, PUTs oder
Git-Pushes in beiden Diagnosephasen. Unverändert sieben fest gepinnte Routen
und die sichere begrenzte Fehlerklassifikation des Regeln-403-Vertrags.
**Beide Diagnosephasen teilen insgesamt höchstens acht zusätzliche GETs**;
alle alten fünf GETs bleiben im Bootstrap128/global384 erhalten. Der normale
positive Fortsetzungsabschluss liegt bei40Zeilen und GET12/PUT0/Git0. Kein
neuer Budgettopf durch Phase, Datei, Verzeichnis oder Planhash. Originalgrenzen
PUT48/Git1/49Mutationen, acht Runs und PUT12/Run bleiben unverändert.

Plan, aktueller Grant und Amendierung werden unmittelbar vor Outbound geprüft;
exakte Deadline sperrt. Nach spät/verloren eintreffender Antwort kein weiterer
Request und kein pauschales confirmed. Keine Verlängerung des Originalplans:
**12.10.2026 09:30UTC /11:30MESZ**. Ein abgelaufener Plan bleibt gesperrt; eine
spätere Planentscheidung gehört ausschließlich in den Hauptchat.

Feature-/Rechte-/Rate-/unknown403 bleiben Sperrgründe. Kein403→leereRegeln,
keine Tarif-/Token-/Repoänderung. Eine vollständige reine Lesediagnose mit
`upload_eligible=false` darf weiterhin `phase_end confirmed` mit eng begrenztem
`scope=read-only-diagnosis` und trotzdem Exit2/HALT liefern.

## Späterer Upload

Ein positiver Abschluss der Fortsetzungsphase öffnet keinen Upload. Der schon
vorhandene getrennte Uploadpfad kann ausschließlich mit eigenem aktuellem
Review/Grant an exakt diese40Zeilen, deren Prozessende, vollständige
Fortsetzungsamendierung/-grant und denselben neuen Executor gebunden werden.
Alle21altenZeilen bleiben enthalten. Ohne diese Belege keine Writer-Abfrage.
Sieben frische Vorprüfungs-GETs gehen der Writer-Eingabe voraus, danach
höchstens der eine unverbrauchte Git-Push des ursprünglichen Roots, neun
History-/Root-GETs und sieben nachträgliche Einstellungs-GETs. Positiver
Gesamtverbrauch weiterhin GET35/PUT0/Git1. Alle historischen HALTs bleiben;
normale Aktivierung und weitere Probephasen werden nicht freigeschaltet.

## Vorlagen, Bedienung und Abnahme

Die gelieferte `PREGET-AMENDMENT-NOT-APPROVED.json` bindet den echten Eingang,
enthält aber keinen neuen Prozessende-/Freigabereview oder erfundenen Grant.
Der Hauptchat prüft die Lieferung und aktuellen Originalbytes unabhängig,
ergänzt Ende-/Freeze-/Evidenzreview, enges Ablaufdatum innerhalb des
Originalplans und separat gebundenen Freigabehash/Phasengrant.

Erst danach den sichtbaren PowerShell-Starter `tools/p3_rules403_start.ps1`
mit `-Phase DiagnoseFortsetzen`, konkretem Amendierungs-/Grantpfad und
unabhängig geprüftem SHA256 verwenden. Der Starter ruft weiterhin direkt
`python -B tools/p3_rules403.py` auf. Keine Wiederholung nach HALT; Kategorie
und Ergebnisort im Hauptchat melden, keine Schlüsselwerte. Uploadvorlage
bleibt ohne künftige echte Frontier/Prozessende/Grant unvollständig.

Die neuen Tests starten einen **separaten Pythonprozess mit genau -B und dem
tatsächlichen Skriptpfad**. Test-sitecustomize ersetzt nur Eingabe und
HTTP/Git-Transport; für Fehlerprüfungen feste Uhr/benannte Crashpunkte und
Beobachtung unveränderter Prädikate. Neue Codepin-, Klassen-, Guard-, Routen-
und Frontierprüfungen bleiben aktiv. Alle Outbounds prüfen zuvor die
dauerhaft bestätigte Requestreservierung. Keine echte Zugangseingabe.
Nur historische Fixtureerzeugung überbrückt ausdrücklich alte Codegates
und für die alten4c-Skriptbytes deren damaliges Zweiphasentupel. Sie wird
niemals als ungepatchte historische Liveausführung bezeichnet.

Kein neuer Chatprompt, keine Online-CI, echte Probe oder P4-Abnahme durch
diese lokale Lieferung. Nutzer meldet Fertigstellung selbst im Hauptchat.
