# P3 – getrennte reale GitHub-Store-Abnahme (Vorbereitung)

Stand 04.10.2026. Basis: P3 `85428fe015f99df70321681b3775af10c44e3d51`.
**Plan, keine Freigabe und keine ausgeführte reale API-Schreibprobe.** Der lokale
Adapter und seine Fake-API-Tests sind abgenommen; GitHub selbst als privater
Store ist es nicht. Diese Probe benötigt einen gesonderten Auftrag. Sie benutzt
ausschließlich synthetische, bedeutungslose Daten und niemals Telegram, Broker,
main-Zustand, bestehende Secrets oder aktive Produktionsworkflows.

## Vorbedingungen und Grenzen

1. Ein ausdrücklich für die Probe freigegebenes **privates** Store-Repository
   benennen. Nur eine eigene Storebranch und `delivery/stream.json` verwenden;
   Actions im Store-Repository deaktivieren. Repository-ID, Branch, Store-ID,
   Prüfer, Zeitpunkt und Test-Run-IDs protokollieren. Keine Probe im öffentlichen
   Code-Repository oder im späteren Sicherungsrepository.
2. Ein kurzlebiges, auf genau dieses Repository begrenztes Test-Credential mit
   `Contents: write` und getrennte Leseberechtigung verwenden. Tokenwert nicht
   in Bericht, Logs, Git oder CI ausgeben. Ein Repository-Credential allein ist
   **keine Pfadbegrenzung**. Vorher tatsächliche Branchregeln, wirksame
   Schreibrechte und die Möglichkeit unerwünschter Pfad-/Branchschreibungen
   prüfen. Falls diese Grenzen nicht erzwingbar sind, als Restrisiko melden und
   keine produktive Freigabe daraus ableiten.
3. Prüfhülle mit synthetischer v2-Struktur, fester Repo-/Branch-/Store-Identität,
   monotoner Revision, parent-Digest, write_id und Body-Digest vorbereiten.
   Testbranch beginnt gesperrt. Den Test-Client nur manuell und isoliert ausführen;
   `run_checked` ist keine freigegebene produktive CLI. Vor jeder Mutation
   750 KiB und 50 schreibende Requests pro Run als Adaptergrenzen prüfen.
4. Vor dem ersten schreibenden Request genau den erlaubten Testumfang, den
   Credentialinhaber und den Aufräum-/Aufbewahrungsentscheid protokollieren.
   Kein Reset, Force-Push, Löschen oder History-Rewrite als Testschritt.

## Nachweisfolge

| Schritt | Erwarteter Beleg und Abbruchbedingung |
| --- | --- |
| Identität und Read | Privates Repo, explizite Branch und Storepfad stimmen; 404, fremde Store-ID, falsche Branch oder fehlender Inhalt führen zum Halt ohne Bootstrap. |
| Zwei Schreiber | Zwei getrennte Run-ID/Attempt/Nonce lesen dieselbe Revision und versuchen Claim. Genau ein bestätigter Owner; der Verlierer stoppt vor Intent und Transport. Kein stiller Retry mit alter Blob-SHA. |
| Mutation und Lesebestätigung | Gewinner schreibt Claim, Intent, `sending`, synthetische Quittung und Unlock nacheinander. Für jeden Schritt: vorherige Blob-SHA im PUT, neue Revision/write_id/Digest, Commit-Parent und aktueller Branchkopf nachlesen. Ohne exakte Bestätigung kein nächster Schritt. Kein realer Transport. |
| Unklare Antwort | Kontrolliert verlorene PUT-Antwort/Timeout an Claim, Intent, `sending`, Quittung und Unlock. Nur exakt nachgelesener eigener Commit darf dem noch laufenden Prozess Erfolg geben. Unerreichbarer oder abweichender Stand hält an. Ein neuer Lauf behandelt überlebendes `sending` als `uncertain`. |
| Rechte und Störungen | Gezielt 403/429, ungültiges Credential, schreibgeschützte Branch, fremde Branch/Datei und veraltete Blob-SHA prüfen. Fehler blockieren; keine lokale/Git-Ersatzquelle, kein automatischer Replay. Negative Rechteproben nur im freigegebenen Test-Repo. |
| Owner nach Runende | Beendeten Altlauf und stillgelegte Test-Worker getrennt belegen. Kein zeitbasiertes Stehlen. `review_takeover` nur mit exakter Owner-/Revisionsbindung und belegtem Runende; `sending` bleibt `uncertain`, bis ein positiver externer Zustellbeleg zugeordnet ist. Ohne Beleg bleibt gesperrt. |
| Grenzen und Historie | Gemessene unkodierte Bytes und schreibende Requests je Testlauf dokumentieren; 80%-Warnung und harte Grenzen prüfen, ohne Historie zu kürzen. Die P1-Fixture mit 16 600 Byte ist keine Messung des frischen main-Snapshots. |

Die Probe ist bestanden, wenn jede positive Mutation samt Parent und Branch
nachgelesen wurde, jeder Gegenfall vor Transport anhält und Repository-/Rechte-
grenzen belegt sind. Ein einzelnes HTTP 200/201 oder eine grüne Fake-API-Suite
ist dafür kein Ersatz. Für jeden Fall Requesttyp, Zeitpunkt, Statusklasse,
erwartete/gelesene Revision, Commit-SHA, Run-ID und Ergebnis ohne Token/privaten
Body im **geschützten** Prüfprotokoll festhalten. Ungeklärte Antwort,
abweichender Parent, fremder Owner oder nicht belegtes Runende bedeutet
`blockiert`; niemals durch Reset bereinigen.

Der frische vollständige main-Snapshot, seine tatsächliche Größe/Requestzahl
und D2 gehören erst zur späteren stillgelegten P4-Grenze. Diese synthetische
P3-Probe aktiviert keine Workflows und begründet keine Live-Freigabe.

Quellen: [GitHub Contents API](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents),
[Tokenbegrenzung auf ausgewählte Repositorys](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens),
[GitHub-Actions-Einstellungen](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).
