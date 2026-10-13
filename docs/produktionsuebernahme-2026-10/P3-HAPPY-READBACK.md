# Einmaliger lesender happy-Abgleich

Nur Offlinevorbereitung. Eigener Readervertrag und menschlicher Grant mit offenen
Datums-/Reviewfeldern; maximal20h. Originalplan, alte Deadline und Quellen/Grants
bleiben unverändert. Der neue Vertrag bindet allein den375-Zeilen-HALT nach dem
zweiten Claimversuch: GET134/PUT11/Git1, kein Readback/Parent für Revision10.
HTTP200 bestätigt den Claim nicht. Der ursprüngliche Ausnahmegrund bleibt unbekannt.

`p3_happy_readback_start.ps1` startet den tatsächlichen Python-B-Skripteintritt mit
kanonischer importierter HappyReadGuard-Klasse. Nur Reader einmal verdeckt eingeben.
Abbruch vor durablem Start: Exit3, kein Versuch. Keine Writerabfrage/PUT/Git/Takeover.
Neue feste Phasenmarke public-store-happy-readback-once in derselben zentralen Session.
Keine zweite Phase, kein neuer Ordner, kein HALT-Bypass für andere Abläufe.

Vor Input und nochmals unter Kernel-Lock: exakte375-Historie, SQLitefrontier,
Journalpräfixe/Marker/Hashes, historische und aktuelle Codepins, frisches positives
Prozessende/Freeze. SQLiteFULL/fsync/Publikation/Highwater und aktueller Zeitguard
vor Reservation, Outbound und Abschluss. Jeder versuchte Read einschließlich
Fehler/verlorener Antwort zählt dauerhaft. Kein Nachlauf/Refund/Blind-Retry.

## Dreizehn GETs, keine Mutation

1–7 öffentliche ID/Name/Admin, Actions, Pages, effektive Regeln, Rulesets,
alleiniger ungeschützter Zielbranch und eng kontextgebundene Schutzantwort.
8–10 Ref/Contents am exakten Refcommit/Ref. Wechsel bleibt erkennbar und sperrt;
kein erneutes Stabilisieren durch zusätzliche Reads.
11 unveränderlicher alter Contentskörper am Commit6ac4dfe9… (Revision9).
12 aktueller Commit samt exaktem Parent,13 vollständiger rekursiver Tree.

Alte bestätigte Readback-/Parentkette mit ursprünglichem vollständig verifiziertem
Rootanker wird exakt aus der375-Historie geprüft. Ein positiver PUT allein ist
kein Kettenglied. Neun erfolgreiche alte Mutationen müssen Readback/Revision/Bytes,
Blobübergang und genau einen passenden Parent besitzen; der409-Verlierer bleibt
gezählt. Keine Lücke bis zum bestätigten Stand9. Der alte Körper muss seinen
protokollierten Blob, Write-ID und Digest treffen und owner=None enthalten.

Aus diesem Körper wird ausschließlich snapshot.control.owner auf den alten zweiten
Run gesetzt; Revision10, Write-ID5e1320a386794f5ec92c3c9d3983e7f1,
parent_digest49955b2e… und neu berechneter body_digest. Kanonische Bytes müssen5758
sein. Eigener Claim: exakt diese Bytes und Parent=alterCommit, gültiger vollständiger
Tree, gleicher Kopf in beiden Refreads. Alter Stand: exakt alterCommit/Körper/Parent.
Abweichende/instabile/fremde/unerreichbare Stände bleiben gesperrt.

Ergebnis eigener Claim vorhanden oder ausschließlich alter Stand beobachtet ist
ein lesender Bericht. `phase_end=read-only-complete-recovery-forbidden`, niemals
pauschal confirmed. Alter Stand beweist keinen fehlgeschlagenen Write. Die
Kopfstabilität bezeichnet den beobachteten Ref/Contents/Ref-Zeitraum; spätere Reads
betreffen unveränderliche Commitobjekte, keine Garantie über künftige Köpfe.
Kein Entsperren, Wiederholen, neuer Run/Seed oder automatische Folgephase.

Bei kompletter Diagnose GesamtGET147/PUT11/Git1; GET237 bleiben. Die vier noch
geplanten Phasen allein benötigen231GET (103+71+38+19); nur6GET für einen zusätzlich
frisch geprüften happy-Abschluss reichen nicht einmal für dessen7 Settingsreads.
Deshalb keine Freigabe der bisherigen Gesamtfolge aus diesem Abgleich ableiten.
Konkreter späterer Budgetvorschlag steht im Lieferbericht; Grenzen unverändert.

Keine Engine-/Strategie-/Backupänderung, produktiver Transport oder P4. Vorlagen
stellen keine Freigabe aus. Nutzer legt Ergebnis im Hauptchat vor; kein Folgeprompt.
