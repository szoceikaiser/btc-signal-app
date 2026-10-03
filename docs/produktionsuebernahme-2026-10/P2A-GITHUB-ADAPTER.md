# P2a – separater GitHub-Persistenzentwurf (Paket G)

**Neuer Entwurf, nicht implementiert, nicht durch A4 abgenommen.** Nur nach D1
in P2b aufnehmen; kein Repository, Token oder externer Dienst wird hier angelegt.
Ziel: die vorhandenen GitHub-hosted Runner weiterverwenden, ohne Serverkauf.

## Speicher und Sicherheitsgrenze

Ein separates **privates** Repository enthält auf einer ausschließlich dem Store
vorbehaltenen Branch genau eine maßgebliche `delivery/stream.json` samt Historie.
Keine Workflows/Pages in diesem Repository; Actions dort deaktiviert. Keine
Nachrichtentexte/Quittungen im öffentlichen `btc-signal-app`. Ob schon ein geeignetes
privates Repository vorhanden ist, ist unbekannt. Einrichtung und begrenzte
repositoryspezifische `Contents: write`-Berechtigung sind Nutzerentscheidungen;
kein Abrufen vorhandener Secrets in P2a/P2b. Kein pauschales repo-weites Token,
keine automatischen Konto-/Tarifänderungen und kein Kostenversprechen.

Code läuft weiterhin im bestehenden Actions-Repository; Storezugriff wird später
nur freigegebenen main-Workflows möglich gemacht, niemals PR-Code. P2b nutzt einen
lokalen Fake des GitHub-APIs. Reale Provisionierung, Rechte- und Persistenzprobe
mit synthetischen Daten bedürfen einer eigenen späteren Freigabe; Telegram bleibt
dabei aus. Ein mockbasierter Test beweist die Plattformsemantik nicht.

## Schreibprotokoll: vor Versand statt nachträglichem Push

GitHub dokumentiert beim Contents-Update die bisherige Blob-SHA, explizite Branch,
Schreibrechte und Konfliktantworten. Darauf beruht der **hier entworfene**, noch
abzunehmende bedingte Updatepfad. Referenz:
[Repository Contents API](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents).
Die Dokumentation ist kein formaler Nachweis unserer Gesamtgarantie. Eine reale
Zwei-Schreiber-Probe und Commit-Lesebestätigung gehören zur späteren Adapterabnahme.

Hülle: Snapshot v2 aus Betriebsvertrag plus monotone `revision`, `parent_digest`,
`write_id`, SHA256 des kanonischen Nutzinhalts, feste Store-/Repo-/Branch-Identität
und `control.owner`. Jede Revision ändert den Inhalt, auch beim Unlock (kein ABA
durch Wiederverwenden alter identischer Bytes). Kein Force-Push, Reset, Merge,
Löschen oder paralleler Browsereditor auf der Storebranch. Branchschutz und
Berechtigungen müssen das soweit verfügbar erzwingen; Administrator-Manipulation
oder Verlust des Dienstes bleiben außerhalb der Garantie und führen zum Halt.

1. Datei an expliziter Branch lesen, SHA/Schema/Hashes/Identität prüfen. 404 führt
   zum Abbruch, nie zum Laufzeit-Bootstrap. Nach Provisionierung nur Updates,
   jeder Request enthält die vorher gelesene Blob-SHA.
2. Freien Owner durch bedingtes Update auf eindeutige Instanz-ID setzen:
   Repository, Run-ID, Run-Attempt und zufällige Nonce. Bei Konflikt nicht senden.
   Aktuellen Zustand erneut lesen; ein fremder Owner bedeutet besetzt.
3. Erfolgreiches Update durch Lesen des zurückgegebenen Commitobjekts und des
   aktuellen Branchzustands bestätigen. Erwartete Revision, write_id, Owner und
   Digest müssen exakt passen. Nur dann ist diese Instanz schreibberechtigt.
4. Jede weitere Mutation muss denselben Owner und erwartete Revision/Blob-SHA
   prüfen. Intent, `sending`, Quittung und Freigabe werden einzeln remote committed
   und nachgelesen. Scheitert eine Grenze, kein folgender Transport.
5. Owner am Ende durch ein weiteres geprüftes Update freigeben. Jede Nachricht
   bleibt an denselben Ablauf gebunden; Git-Artefakte am Laufende sind nur Exporte.

Bei HTTP-Timeout nach PUT: Ausgang ist unklar. **Kein blindes Wiederholen oder
Transportieren.** Mit unveränderlicher write_id den tatsächlichen Zustand lesen;
nur exakt identische bestätigte Mutation darf der noch laufende ursprüngliche
Prozess als erfolgreich werten. Unerreichbarer/abweichender Zustand stoppt ihn.
Ein neuer Prozess darf selbst eine wiedergefundene `sending`-Revision niemals als
Erlaubnis zur Zustellung interpretieren; das ist `uncertain`. Ein unklarer
Quittungs-Commit darf nur durch bereits dauerhaft exakt vorhandenes `confirmed`
aufgelöst werden. Inhalt zusammenkopieren oder Git-Rebase ist verboten.

## Konkurrenz und abgebrochene Runner

Actions-`concurrency` mit einem gemeinsamen Streamschlüssel und
`cancel-in-progress: false` ist zusätzliche Lastbegrenzung; es ersetzt den Owner
nicht. Alle Versandpfade teilen denselben Store. Keine GitHub-Lease, die nach
Zeitablauf automatisch gestohlen wird: Ein pausierter alter Runner könnte sonst
nach dem neuen Owner noch senden. Telegram versteht keine Fencing-Nummer.

Wenn der Owner nicht sauber freigegeben wurde, **bleibt er gesperrt**, auch nach
Stunden oder nach Erscheinen eines neuen Runs. Entsperren nur in einem gesonderten
Maintenance-Auftrag: alle Auslöser stilllegen, exakte alte Run-ID/Attempt endgültig
beendet und keine weiteren Worker nachweisen; erwartete Owner-ID/Revision prüfen;
`sending → uncertain` und Übernahmebeleg gemeinsam speichern. Keine Freigabe nur
aufgrund von Heartbeat-Alter oder „Cancel angefordert“. Fehlt ein belastbarer
Beleg der Prozessbeendigung, keine Übernahme. Diese konservative Betriebsgrenze
kostet Verfügbarkeit, vermeidet aber einen unbelegten Exactly-once-Anspruch.

Der normale neue Lauf darf bestätigte/pending-Zustände erst nach dieser Übergabe
bearbeiten. `uncertain` bleibt unabhängig vom nun freien Owner gesperrt. Positiven
Zustellbeleg nur nach dem gemeinsamen Reconciliation-Vertrag übernehmen.

## Kapazität, Ausfälle, Backup und Abnahme

P2b-Paket G setzt vorläufig eine harte Grenze von 750 KiB unkodiertem Snapshot und
50 schreibenden API-Anfragen pro Run. Das sind eigene konservative Schutzgrenzen,
keine GitHub-Quotenzusage. Repräsentative gemessene Größe/Requests in P2b berichten;
falls der vollständige Snapshot schon darüber liegt, G-Abnahme blockieren und
separate Segmentierungsentscheidung verlangen. Nie Historie/Quittungen still
abschneiden. Wachstum vor jeder Mutation prüfen, 80%-Warnschwelle. Auf 403/429,
Timeout, Rate-Limit oder erschöpftes Budget anhalten; keine Replay-/Fallbackstrecke.
Explizite Ablehnung erlaubt einen späteren neuen Run, `sending` nicht.

Konsistente Sicherung an **einer** unveränderlichen Commit-SHA: State-Datei,
Store-ID/Revision/Digest, zugehörige Code-/Config-/Migrationsbelege, Git-Historie als
Bundle und Hashmanifest in ein neues geschütztes Ziel exportieren. Restore ohne
Transport testen. Öffentliches CI-Artefakt ist kein zulässiges Ziel privater Belege.
Eine alte Branch/Dateikopie startet niemals aktiv. Verlust der neuesten Revision
oder Zurücksetzen der Branch sperrt den Stream bis zum vollständigen Zustellabgleich.

Zusätzlich zu den gemeinsamen P2b-Fällen: zwei gleichzeitige Claims, veraltete SHA,
Ownerwechsel nach Pause, beendeter und nicht nachweislich beendeter Alt-Runner,
angenommener PUT mit verlorener Antwort an jeder Grenze, verzögertes Lesen,
falsche Branch/Store-ID, 404/403/429, Commit bestätigt aber Mirror verloren,
Budget-/Größenüberschreitung, unerwartete Historienumschreibung. Fake-Tests müssen
alle Fälle abdecken; externe GitHub-Probe bleibt ein ausdrücklich offenes P3-Gate.

Gesamtbewertung: umsetzbare Alternative in vorhandener Plattform, aber deutlich
mehr eigener Adaptercode und Bedienaufwand als ein vorhandenes lokales Volume.
Ohne benannten Host ist sie der bevorzugte **Entwurf**, keine implizite Zustimmung
zur Einrichtung eines privaten Repositories oder zum Gebrauch neuer Credentials.
