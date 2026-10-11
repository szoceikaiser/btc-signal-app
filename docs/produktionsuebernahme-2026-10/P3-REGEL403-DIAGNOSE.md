# Regeln-403: einmalige Reader-Diagnose und getrennte Uploadprüfung

Stand 11.10.2026. Lokale Vorbereitung, keine neue reale Freigabe. Dieser Zusatz
erweitert ausschließlich die exakt belegte Folge Bootstrap-401/HALT → einmalige
Reader401-Fortsetzung → Regeln403/HALT. Originalplan, alte Code-/Seedidentität,
beide HALTs und die ursprüngliche Session bleiben maßgeblich. Keine Aktivierung.

## Gesicherter Eingang und getrennte Identitäten

Ausgangscode `0128237e4ed72fc3b11fad5249b20770e9eef725`, Tree
`69de229f4c1954ec5255e068d5252d8a8bdd534c`; ursprünglicher Bootstrapcode
`b0b0386e51c62a35b7c18053edf284862479da54`. Neue Ausführung erhält eigene
HEAD-/Tree-/Dateipins, einschließlich dieses Vertrags und der Vorlagen.
Git-Bytes und ursprüngliche LF→CRLF-Materialisierung werden ausdrücklich geprüft.
Die neuen Pins ersetzen weder den Originalplan noch die Seedidentität.

Maßgebliche reale Frontier: 17 vollständig veröffentlichte Zeilen,
GET5/PUT0/GIT_PUSH0, Hash
`bc8398ce91e92440f16399ce212520bc352232b8018d8a0b3fc65c3f26530a5a`.
Der ursprüngliche Plan läuft am 12.10.2026 um 09:30 UTC ab. Keine Verlängerung
durch diesen Vertrag. Historische 403-Header/-Bodies fehlen dauerhaft.

Die Amendierung bindet Originalplanhash, vollständige alte Amendierung/Grant,
Originalmaterialisierung, exakte aktuelle DB-/Lock-/Marker-/Journalbytes,
Frontier/Zeilenzahl/Zähler/UTC-Highwater, alte Rootbytes, neue Codepins,
feste Routen und unabhängigen Prozessende-Review. Unter exklusivem Kernel-Lock
müssen alle Journalpräfixe und die neueste SQLite-FULL-Frontier übereinstimmen.
Der Original-PID muss aktuell beendet/abwesend sein; ein tatsächlicher
Terminal-Endbericht und Prüfung des synchronen Codepfads sind erforderlich.
Eine heutige OS-Beobachtung wird niemals als historische Parent-Wait-Quittung
ausgegeben. Ein lebender PID sperrt auch bei behauptetem Review.

## Diagnose: genau ein Versuch, Reader allein

Phase `bootstrap-rules403-diagnose-once`, festes gleichnamiges JSONL im
ursprünglichen Sessionordner. Sie ist nur nach genau den bekannten 17 Zeilen
zulässig. Kein neuer Ordner, Seed, Markerreset, automatischer Neustart oder
allgemeiner HALT-Bypass. Auch ein vollständig diagnostizierter Featurefehler
verbraucht diesen Versuch. Der alte Reader401-Versuch bleibt verbraucht.

Es werden höchstens diese sieben GETs in dieser Reihenfolge ausgeführt, im
selben expliziten Repository; Branch und Repo werden korrekt URL-kodiert:

| Route relativ zu `/repos/{owner}/{repo}` | Prüfung / benötigte Fine-grained Leseberechtigung |
|---|---|
| leer | konkrete ID/Name, privat, nicht archiviert, Pages aus, Admin-Rolle; Metadata/read |
| `/actions/permissions` | enabled=false; Administration/read |
| `/pages` | streng geprüfte 404 Not Found; Pages/read |
| `/rules/branches/{branch}?per_page=100&page=1` | 200 und leere effektive Regeln; Metadata/read |
| `/rulesets?includes_parents=true&per_page=100&page=1` | 200 und leere eigene/geerbte Rulesets; Metadata/read |
| `/branches?per_page=100&page=1` | 200 und leeres Repository; Contents/read |
| `/branches/{branch}/protection` | streng geprüfte 404 auf noch abwesendem Branch; Administration/read |

Ein erkannter Feature-Hinweis ausschließlich an den drei Regelrouten erlaubt
noch die jeweils anderen festgelegten GETs zur Diagnose; kein Request wird
wiederholt. Andere Fehler beenden sofort. `phase_end confirmed` besitzt hier
ausschließlich `scope=read-only-diagnosis`; `upload_eligible=false` ist weiterhin
HALT mit Exitcode2. Ein erfolgreicher positiver Normalpfad liefert Exitcode0,
aber noch keinerlei Uploadberechtigung. Vorhandene Tokenrechte bleiben gleich.

## Fehlantworten: sichere Hinweise, keine erfundene Ursache

HTTP-Fehler werden mit maximal 4097 gelesenen Bytes auf das 4096-Byte-Limit
geprüft. Nur eindeutiges UTF-8-JSON mit message, documentation_url und optional
status ist zulässig. Message: 1–512 druckbare ASCII-Zeichen, Dokumentations-URL
aus fester offizieller Allowlist, Status muss passen. Zusätzliche/duplizierte
Felder, unerkannte URLs, überlange oder widersprüchliche Angaben sperren.

Nur ausgewählte Responseheader werden geprüft: JSON-Content-Type, numerische
Rate-Limitwerte/Retry-After und streng begrenzte akzeptierte Permission-Sets.
Headerduplikate, mehr als 256 Zeichen oder unbekannte Permissionnamen sperren.
Permission-Sets verwenden Komma für gemeinsam benötigte Rechte, Semikolon für
Alternativen. Die Angaben bestätigen keine tatsächlich erteilten Tokenrechte.
Nicht ausgewählte Header werden weder gespeichert noch ausgegeben.

Das Journal enthält Route, HTTP-Status und ausschließlich geprüfte Kategorien,
Zahlen und Permission-Enums: `permission-denied-hint`, `rate-limit-hint`,
`feature-unavailable-hint`, `unknown-403`, `invalid-error-response` oder
`ambiguous-error-response`; 401/404 haben eigene eng geprüfte Kategorien.
Keine Rohmessage, URL, Credentials, Requestheader oder Responsebodies im Log.
Fehlende Rateangaben sind kein Beweis ausreichenden Budgets. Nie automatische
Wiederholung, Wartefrist oder absichtliche Provokation von Anbieterlimits.

Die lexikalisch bekannten Upgrade-Meldungen sind **nur Feature-Hinweise**.
Offizielle Dokumentation beschreibt Verfügbarkeit, liefert aber keinen hier
verifizierten strukturierten 403-Nachweis, dass im konkreten Repository keine
wirksamen Regeln existieren. Daher `feature_absence_proved=false` in jedem Fall.
Browseranzeige, allgemeiner Tarif und Caller-Behauptung ersetzen keinen
positiven Nachweis. Es gibt keinen alternativen 403-Vorprüfungspfad, auch nicht
für Rulesetliste oder klassische Branchprotection.

Ein 404 auf abwesendem Branch belegt isoliert keine allgemeine Abwesenheit
klassischer Branchmuster oder korrekte Tokenrechte. Deshalb bleiben die
vorgeschriebenen Leserechte, beide positiven Regelnantworten und das leere
Repository zwingend; nach einem späteren Upload werden effektive Regeln,
Rulesets, der einzige `protected=false`-Branch und klassische Protection erneut
geprüft. Jeder fehlende Prüfnachweis blockiert den Abschluss. Der Hauptchat
muss die unveränderten Rechte/Einstellungen vor einer echten Freigabe prüfen.

## Ein späterer Upload ist eine eigene Entscheidung

Phase `bootstrap-rules403-upload-once` ist ausschließlich nach genau der ersten
vollständigen, rechtzeitig positiven Diagnose zulässig (36 Zeilen/GET12/PUT0/
Git0). Neuer Review und neuer Phasengrant binden deren vollständige neueste
Frontier, Prozessende, Amendierung/Grant und denselben neuen Ausführungscode.
Ein Feature-Hinweis, verlorene Antwort oder fehlender Abschluss genügt niemals.
Kein zweiter Grant wird vom Werkzeug erzeugt.

Uploadablauf: ursprünglichen parentlosen Root lokal prüfen → sieben frische
Vorprüfungs-GETs → erst jetzt Writer einmal verdeckt abfragen → exakt ein
vorher dauerhaft gezählter Git-Push des alten Commits auf den expliziten Branch
→ neun GETs zur vollständigen Root-/Historyprüfung → sieben GETs zur erneuten
Einstellungsprüfung → ausschließlich blocked-Root-Abschluss. Keine PUTs,
Aktivierung, neuen Rootcommits, Force-Pushes oder Branch-/Repoanlage per API.
Die zwei alten HALTs bleiben erhalten und sperren allgemeine Folgephasen.

| Budget | Grenze / erwarteter positiver Verbrauch |
|---|---|
| Diagnose neu | harte Grenze 8 GET, feste Folge 7; PUT0/Git0 |
| Gemeinsamer Bootstrap inkl. 401,403,Diagnose,Upload | GET128; positiv GET35/PUT0/Git1 |
| Upload neu | positiv 23 GET, PUT0, höchstens ein Git-Push |
| Ganze ursprüngliche Probe | GET384, PUT48, Git1, insgesamt49 Mutationen |
| Weitere Originalgrenzen | acht Runidentitäten, PUT12/Run, 768000 Storebytes, 2MiB Antwort |

Jeder Versuch zählt vor Outbound durch SQLite FULL → fsync-JSONL → bestätigte
FULL-Publikation. Unklarer Write oder Prozessverlust hinterlässt Reservierung
oder unveröffentlichten Sperrzustand. Kein automatischer Reparatur-/Resumeweg.
Probe/inspect/takeover teilen Sperre, Historie, Zähler und UTC-Highwater.

Plan, Grant und Amendierung müssen unmittelbar vor jedem HTTP-/Gitstart noch
gültig sein; exakte Deadline ist ungültig. Eingabe-/Vorprüfungszeit zählt mit.
Rechtzeitig gestartete, erst nach Ablauf beantwortete Requests bleiben gezählt;
kein weiterer Request, kein Nachlaufrecht, kein Readback und kein bestätigter
Gesamtabschluss nach Ablauf. Lokale Belege/HALT dürfen geschrieben werden.
Monotone Laufzeit, erkannter Uhrenrücksprung und dauerhafte UTC-Highwater sperren;
keine allgemeine Absicherung gegen extern manipulierte Systemuhren behauptet.

## Konkreter Freigabevorschlag und Bedienung

1. Hauptchat prüft neue Lieferung und alte Originalbytes unabhängig; ergänzt
   den echten Prozessende-/Evidenzreview und enges Ablaufdatum **vor** Original-
   Planablauf in `DIAGNOSE-AMENDMENT-NOT-APPROVED.json`. Unabhängigen Hash und
   ausdrücklichen Reader-Diagnosegrant ausstellen. Die mitgelieferten Vorlagen
   besitzen `human_authorization=false` und sind nicht ausführbar freigegeben.
2. Nur danach im sichtbaren Terminal den Starter `tools/p3_rules403_start.ps1`
   mit `-Phase Diagnose`, expliziten Amendierungs-/Grantpfaden und separat
   geprüftem SHA256 aufrufen. Reader genau einmal verdeckt einfügen, Enter.
   Kein Writer. Kategorie und Ergebnisort melden, keine Schlüsselwerte.
3. Keine Wiederholung bei HALT. Hauptchat prüft die neue vollständige Frontier.
   Bei Feature-/Rechte-/Rate-/unbekanntem Fehler bleibt Upload gesperrt.
   Ohne positiven Regelnnachweis gibt es innerhalb dieses Auftrags keine
   weitere technische Fortsetzung: kein Tarifwechsel, öffentliches Repo,
   breiterer Token oder neue Storeidentität als Umgehung.
4. Nur nach positivem Normalpfad eigenständigen Uploadreview/Grant erstellen,
   exakten neuen PID-/Frontiernachweis ergänzen; `-Phase Upload` getrennt starten.
   Reader einmal, Writer erst nach positiver frischer Vorprüfung. Danach nur
   blocked-Root abnehmen; keine Freigabe für Aktivierung oder P4 ableiten.

Kein neuer Chatprompt wird für diese Bedienung benötigt. Lokale Fixtures sind
klein und keine Produktionsgrößenmessung. Kein echter Diagnose-/Uploadlauf,
keine Online-CI oder Gesamtbetriebsabnahme durch diese Lieferung.

## Öffentliche offizielle Grundlagen (11.10.2026)

- [Effektive Branchregeln und Rulesetliste](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch): Metadata/read, Branch muss noch nicht existieren, effektive anwendbare Regeln.
- [Ruleset-Verfügbarkeit](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets): private Repositories abhängig vom Tarif; keine konkrete 403-Abwesenheitsattestation.
- [REST-Fehler, Rate-Limits und Permissionhinweise](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api): 403/429 können Rategründe haben; Permissionheader ist ein Anforderungshinweis.
- [Klassische Branchprotection](https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection): Administration/read; 404 bleibt nur im gesamten beschriebenen Normalpfad verwendbar.
