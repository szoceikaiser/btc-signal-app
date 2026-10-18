# Einmalige Fortsetzung nach dem ersten Reader-401

Stand 11.10.2026. Lokal vorbereitete Vertragserweiterung, keine Freigabe.
Der Hauptchat muss Code, Belege und den konkreten Amendierungsvertrag unabhängig
abnehmen; danach entscheidet der Nutzer über genau einen gebundenen Versuch.
Der bisherige Halt ist bewusst strikt, kein belegter Handelsenginefehler.

## Enger Ausgangspunkt und Originalidentität

Nur die neue Phase `bootstrap-reader401-once` darf genau fünf vollständig
publizierte zentrale Ereignisse fortsetzen: phase_start → authorization → erster
GET → http-401 → phase_halt. Zähler GET1/PUT0/GIT_PUSH0. Keine frühere Mutation,
unklare Antwort, zweite Authstörung, sending oder sonstige phase_halt-Ausnahme.
Alle Zeilen tragen denselben Originalplanhash und Repo-/Branch-/Pfadbezug.

Der maßgebliche historische Fall bindet Planhash
`db2385a028c47beab1058931f4eff9eb4e5a00dc1105b9510385af003ea5d967`, Repo
`szoceikaiser/btc-p3-store-probe`, ID1414013858, Branch `p3-synthetic-only`, Pfad
`delivery/stream.json`. Frontier:
`54d6696fac6579f2e455b50c2cbf24278db482408d37b9f0a68cde22334b9553`.
Journaldateihash:
`bb1529caf47f72aa81d1894f2119995f3984625e1b6e30ed3d57b7ac593d60b1`.
Die echten Dateien werden in diesem Auftrag weder mit Ledger geöffnet noch
fortgesetzt. Entwicklung ausschließlich mit Kopien und Offline-Fixtures.

Der Originalplan bleibt unverändert, einschließlich HEAD
`b0b0386e51c62a35b7c18053edf284862479da54`, Tree
`81ef0047f94ea8fe99783e5b269254e6c7c8fd9a`, 22 Arbeitsdateipins und Ablauf
`2026-10-12T09:30:00Z`. Der Seed behält diese ursprüngliche Codeidentität.
Der neue Executor erhält eigene HEAD-/Tree-/Arbeitsdateipins, muss ein Nachfahre
des Originals sein und verlangt einen sauberen versionierten Arbeitsbaum.
Sein Pinset umfasst mindestens alle alten Pinpfade und die neuen Executorpfade.

`original_code_materialization` bindet pro Originaldatei den kanonischen
Git-Blob-SHA256, den unveränderten alten Arbeitsdateihash und entweder `identity`
oder die exakte Transformation `lf-to-crlf`. Im tatsächlichen Fall sind acht
Dateien identisch und 14 CRLF-materialisiert. Nur CR-freie Git-Bytes dürfen exakt
so umgewandelt werden; das Ergebnis muss den alten Hash ergeben. Diese explizite
Zuordnung gehört zum Amendierungshash. Keine stille Normalisierung alter Pins.

## Amendierung, positives Ende und dauerhafte Session

`p3-reader401-amendment-v1` bindet Originalplanhash, vollständigen ursprünglichen
Grant samt historisch protokolliertem Digest, fünf Zeilen über Frontier und
Dateihash, DB, alten Marker, Lockbytes, UTC-Highwater, Zähler, vorhandenen Root
mit Dateihashmanifest sowie neuen Ausführungscode. Der separate menschliche
Grant `p3-human-grant-v2` nennt weiterhin den Originalplanhash, die neue feste
Phase und den Amendierungshash als `review_sha256`. Der Starter fordert diesen
Hash zusätzlich als unabhängig geprüften Parameter. Fehlende Angaben halten
vor Credentials und Transport an.

Für PID14508 existiert keine Parent-Wait-Quittung; sie wird nicht nachträglich
behauptet. Der eigene Endenachweis kombiniert ausdrücklich:

1. Unabhängig geprüften ursprünglichen synchronen Codepfad: erster Reader-401
   und vollständig publizierter terminaler Halt vor jeder Mutation.
2. Menschlichen Review mit Prüfer, Evidenzhash, Original-PID, Beobachtungs-UTC,
   positiv bestätigtem Ende aller Worker und pausierten Triggern.
3. Frische OS-Prüfung der exakten PID durch den Executor: beendet/abwesend.
   Lebende wiederverwendete PID, Zugriffsfehler oder unbekannter Zustand stoppen.
4. Exklusiven Zugriff mit derselben Kernelsperre und exakt passender zentraler
   Frontier, Journal- und Markerhistorie.

Diese Kombination heißt
`terminal-reader401-plus-fresh-os-end-and-exclusive-lock`. PID-Abwesenheit allein
ist keine Freigabe. Sie gilt nur für den belegten mutationsfreien Reader-401;
die Parent-Wait-/Owner-/Revisionsbindung für sending-Übernahme bleibt bestehen.
Die frische OS-Beobachtung wird bei zulässigem Start im neuen Journal vermerkt.

Kein neuer Sessionordner oder Plandigest, kein Löschen. Das neue feste Journal
`bootstrap-reader401-once.jsonl` enthält das unveränderte Original als Präfix.
Die alte Journaldatei bleibt erhalten; DB und neuer Startmarker werden später
über das bestehende FULL-/fsync-/Publikationsprotokoll ergänzt. Unter Windows
wird der Lockhash durch den bereits sperrenden Handle gelesen, ohne Entsperren.

Der neue Startmarker ist vor der ersten neuen phase_start-Zeile dauerhaft.
Harter Verlust zwischen Marker, zentralem Commit, Journal-fsync, Publikations-
commit und Outbound bleibt gesperrt. Auch lokaler Eingabefehler nach Start
verbraucht diesen einen Versuch. Kein automatischer Cleanup, Reparatur, Replay,
Fristablauf oder Rückerstattung reservierter Versuche. Vollständige kumulative
Historie und zentrale Frontier bleiben Voraussetzung für inspect/takeover.

## Root, Budgets und Gültigkeit

Exakt der vorhandene parentlose blocked-FLAT-Root bleibt maßgeblich:
`c78a4d1283aabdf187a65f628bd2882277b168e7`, Seed-SHA256
`0bb72c1a5fb9d6e77cd5579a6083c5cf6033e502c9c2b001cc3719079c56f53a`,
1981 Bytes, nur die festgelegte Datei. Lokale Objekte, einzige Branchreferenz,
Seedbytes und Rootmanifest werden geprüft. Kein neues Git-init oder Schreiben
eines neuen Seeds. Der bestehende Askpassweg bleibt: Token nur im Prozess und
in der kurzlebigen Git-Kindprozessumgebung, nicht in Argumenten oder Dateien.
Die zwei bekannten tokenfreien Helperdateien dürfen bei der Vorbereitung
hinzukommen; alle ursprünglichen Rootdateien bleiben hashgleich.

Privatheit, Actions aus, Pages aus, Regeln und leeres Repo werden erneut mit
ausreichenden Leserechten geprüft. Dann höchstens ein exakt gebundener,
dauerhaft vor Outbound gezählter Pushversuch und vollständiger Rootreadback.
Keine Aktivierung oder spätere Phase automatisch.

| Budget | Unveränderte Grenze | Erfolgreiche Offline-Fixture |
|---|---:|---:|
| GET global | 384 | 16 inklusive des alten GET |
| PUT global | 48 | 0 |
| Git-Push | 1 | 1 |
| Mutationen insgesamt | 49 | 1 |
| Bootstrap einschließlich Fortsetzung GET | 128 | 16 |
| Bootstrap einschließlich Fortsetzung PUT | 0 | 0 |
| Store / Antwort | 768000 Bytes / 2 MiB | kleine Fixture, keine Größenmessung |

Die neue Phase zählt beim Fallbudget immer zu bootstrap. Andere Fälle behalten
zwölf PUTs je Fall/Run und acht feste Runidentitäten. Fehler, verlorene Antworten
und vor Outbound abgebrochene Reservierungen zählen dauerhaft mit.

Originalplan, neuer Grant und Amendierung müssen direkt vor jedem HTTP-/Gitstart
gelten. Grantende darf nicht nach Amendierungsende liegen. Strikt `jetzt < Ende`,
zusätzlich monotone Zeit und UTC-Highwater. Genau an der Deadline kein Start.
Kein Nachlaufrecht, auch kein neuer GET/Readback. Ein rechtzeitig gestarteter
Request darf sein späteres Ergebnis lokal protokollieren, erhält nach Ablauf
aber weder Retry noch Readback oder pauschales confirmed. Vollständige
Abschlussbelege und gültige Freigabe sind erforderlich. Kein allgemeines
Versprechen gegen absichtlich verstellte Uhren oder zurückgerollte Datenträger.

## Konkrete spätere Freigabe und interaktiver Start

Zuerst Code-/Belegabnahme im Hauptchat. Danach bekannte echte Session und Root
read-only erneut inventarisieren, offene Prozessendereviewfelder positiv belegen,
neue Ausführungspins und alte Materialisierung prüfen. Originalplan muss noch
gelten; nach seinem Ablauf ist dieser Weg gesperrt. Kein neuer Plan als Reset.
Erst nach Nutzerzustimmung zum vollständigen Amendierungshash den eigenen Grant
für `bootstrap-reader401-once` mit enger, ausreichender Deadline und tatsächlichem
Zustimmungsbeleg ausstellen. Vorlagen haben offene Angaben, false-Freigaben und
keine gültige Deadline. Hier wird kein echter Grant ausgestellt.

Später in einem sichtbaren interaktiven PowerShell-Fenster den geprüften Starter
aus dem gepinnten Arbeitsbaum aufrufen; Platzhalter erst durch die vom Hauptchat
geprüften Artefaktpfade und den bestätigten Hash ersetzen:

```powershell
& 'C:\Users\oeztu\BTC-Trading\p3-storeprobe-work\tools\p3_reader401_start.ps1' `
  -AmendmentPath '<GEPRUEFTE-AMENDIERUNG.json>' `
  -GrantPath '<EXPLIZITER-FORTSETZUNGSGRANT.json>' `
  -ApprovedAmendmentSha256 '<UNABHAENGIG-BESTAETIGTER-HASH>'
```

Der Starter verwendet den bestehenden Originalplan und dessen festen Journalordner.
Reader und Writer jeweils **genau einmal** vollständig einfügen, keine Zeichen
oder Sternchen erwarten, dann Enter. Nicht mehrfach einfügen. Werte/Teile nie
im Chat, Dateien oder Argumenten nennen; kein Clipboardzugriff. Die lokale
ASCII-/Präfix-/Längenprüfung verwirft offensichtliche Mehrfachkopien, Leerzeichen,
Zeilenumbrüche und unpassende Form ohne Reparatur. Sie beweist keine gültige
Authentifizierung; ein weiterer 401 bleibt möglich und stoppt endgültig.

Bei Halt nicht erneut starten, nichts löschen, nur Status/Belegpfade ohne
Schlüsselwerte im Hauptchat melden. Bei bestätigtem Root ebenfalls Belege dort
prüfen lassen. Die historische Haltzeile sperrt den normalen Aktivierungspfad
weiter; dieser Auftrag schafft keine Ausnahme für spätere Phasen.
Der Nutzer meldet das lokale Ergebnis selbst; kein zusätzlicher Chatprompt nötig.
