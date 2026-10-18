# P2a – frischer Zustandsimport ohne historische Nachsendung

Vertrag für spätere Offline-Implementierung und P3/P4. **Keine Migration in P2a.**
Der Snapshot `ca8ad2fb730174ca1887791d425ae01aa6a715e6` bleibt nur P1-Testfixture.
Das während P2a fortlaufende main wird weder zurückgesetzt noch als live migriert
bezeichnet. Ein Git-Commit allein ist bei alten Versandpfaden kein Zustellbeleg.

## 1. Eingabepaket und Schnittgrenze

Das Werkzeug `tools/produktion_migrate.py` soll ausschließlich explizite lokale
Dateien lesen, ohne Netzwerk, Engine-Liveaufruf, Secrets oder Schreibzugriff auf
Quellen. Parameter: `--source-dir`, `--manifest`, `--cutover`, `--config`, `--out`.
Ausgabeziel muss neu sein; keine In-place-Migration und keine Store-Provisionierung
im Konverter. Gleiche Eingabebytes ergeben identische fachliche Ausgabe/Hashes;
Zeitstempel werden eingegeben und nicht aus der laufenden Uhr erfunden.

| Eingabe | Prüfung / Bedeutung |
|---|---|
| `source-manifest.json` | Schema, `mode: rehearsal/live_candidate`, Repository, volle Code-/Quell-SHA, Git-Tree, Erfassungszeit UTC, je Pfad Byte-SHA256 und Größe; `watch.json` ausdrücklich vorhanden oder fehlend. |
| `state.json`, `signals.json`, `oi_history.json` | Alle aus derselben stillgelegten Aufnahme; Pflichtdateien, endliche Zahlen, gültige Typen/Zeiten, Position und Historie konsistent; keine Demo. Gesamte erhaltene Historie, keine Neusortierung/Entdoppelung durch Annahmen. |
| `config-source.json` und eingebettetes `state.config` | Beide separat erhalten und vergleichen; letzteres ist die frühere Projektion, nicht stillschweigend die neue Betriebswahl. |
| freigegebene `config-target.json` | Im P1-Fixture nur `muster_cvd: alt → usd` plus Hinweistext; E42/Short aus. Bei späterem main jede zusätzliche Differenz gesondert prüfen, keine Anpassung an aktuelle Rendite. |
| `watch.json` optional; bestehende Journale/Quittungen, falls vorhanden | Fehlend heißt unbekannt, nicht „nie gesendet“. Wenn ein neuerer Snapshot bereits `_delivery` enthält, in diesem Legacy-Konverter abbrechen; kein Leeren fremder Journale. Eigener geprüfter Import nötig. |
| `cutover.json` | Eingetragene UTC-Grenze, Kerzenidentitäten, Stilllegungsbelege, Run-IDs/Endzustände aller alten Versender und Schreiber, bekannte letzte persistierte Auswertung, neue Store-ID, Ziel-/Botbindung, Config-Hash; konkrete D2-Entscheidungen als Belegreferenzen oder `null`. |
| Belege / Einschränkungen | Bekannte Altzustellungen und Stopbelege nur unverändert referenzieren. Fehlende Quittungen/Fills/Stopmaxima als unbekannt aufführen. Private Belege bleiben außerhalb des öffentlichen Repos. |

Stilllegung ist P4-Arbeit: GitHub-Schedules, externe Dispatchs, manuelle Wege und
wartende Läufe sperren; laufende Läufe vollständig auslaufen lassen oder deren
Abbruch gesondert klären. Danach Schreiberstillstand belegen, Dateien aufnehmen
und vor/nach Aufnahme HEAD und Hashes vergleichen. Alter Versand kann schon vor
seinem Git-Push erfolgt sein. Ein fehlgeschlagener/abgebrochener letzter Lauf oder
unbekannte laufende Instanz blockiert die Einstufung als konsistent. Das bloße
Vorliegen von state/signals im selben Commit reicht nicht.

Zeitbegriffe (Millisekunden UTC; Candle.ts bezeichnet Kerzenanfang):

- `B = source.state.last_signal_ts`, unverändert übernehmen. Kein Hochsetzen,
  damit vermeintlich alte Kerzen übersprungen werden.
- `T = freeze_at_ms`, belegter Zeitpunkt nach Stilllegung; `W = floor(T/4h)*4h`,
  die bei Stilllegung laufende Kerze. Engine-Schnittgrenze `B`, Watch-Sperrgrenze `W`.
- Für einen **aktivierbaren Legacy-Import** muss B genau die letzte zum Zeitpunkt
  T vollständig geschlossene 4h-Kerze sein (`W - 4h`). B in Zukunft, unpassendes
  Raster, Historie neuer als B oder eine verpasste geschlossene Kerze: Abbruch.
  Keine stille Nachrechnung einer Lücke mit verändertem CVD und laufender Position.
- Ein vorhandener Watch-Merker darf höchstens W betreffen. Alle alten Watch-
  Hinweise/Auflösungen bis W bleiben erhalten bzw. unbekannt, aber unterdrückt.
  Der erste neue Watch-Hinweis muss eine Kerze **nach W** betreffen. Das bewusste
  Auslassen des Restes der Grenzkerze ist Teil des Freigabeberichts.

P1 darf als `rehearsal` mit ausdrücklich synthetischer passender T-Grenze getestet
werden. Das beweist nur die Mechanik. Ein Live-Kandidat darf keine synthetischen
Stilllegungs-/Quittungsbelege verwenden. Falls zwischen Snapshot und Aktivierung
eine weitere Kerze schließt, gilt der Kandidat als abgelaufen: P4-Grenze erneut
herstellen und frisch prüfen, keinen alten Kandidaten automatisch nachholen.
Kann main nicht rechtzeitig einen konsistenten Stand liefern, bleibt die Migration
gesperrt; ein gesonderter Nachführungsplan wäre eine neue begrenzte Aufgabe.

## 2. Position, Historie und fehlende Altwerte

Unverändert erhalten: Richtung und T1/sonstiger Zustand, `last_signal_ts`,
`entry_ref`, `entry_pct`, `bestand_pct`, `tp_rungs`, `dip_buys`, `buy_rungs`,
`liq_exits`, `high_exits`, `liq_entries`, `retrace_extreme`, `ziel_extrem`,
`be_aktiv`, `last_stop_ts`, sämtliche vorhandenen Stop-Wartemarken und E42-Merker,
Pivotzeit/Art/Preis und Zonen. Keine Position auf FLAT zurücksetzen.
`pos_from_state → pos_to_state` ergänzt ausschließlich versionierte Struktur;
Abgleich jedes ursprünglichen fachlichen Felds und Bericht jeder Ergänzung.
Unbekannte Zusatzfelder bleiben im Rohzustand erhalten und werden zur Prüfung
gemeldet, niemals kommentarlos als operative Defaults gedeutet.

Legacy-Provenienz bleibt explizit: `inventory_source=signal_reference`, `lots=[]`,
bei aktiver Position `cost_basis_complete=false`; keine Börsenfills, Stückzahlen,
Kosten oder realen Einstandskosten aus Prozent-/Signaleinträgen ableiten.
`entry_ref` bleibt Signalreferenz. Fehlender `widerstand_exits` bleibt dokumentierter
technischer Default 0; E42 bleibt aus. Fehlende Pivotindizes werden als technische
Altparser-Defaults gemeldet, nicht als bekannte historische Indizes bezeichnet.

Fehlender `valid_stop` bleibt `null` mit `prior_stop_maximum_unknown`.
Der neue Stop kann nach Aktivierung nur **ab seinem ersten tatsächlich gesicherten
Wert** monoton sein; es gibt keine rückwirkende Höchststopgarantie. Neue Werte
entfernen die historische Lückenmarkierung der laufenden Altposition nicht.
Ein alter Planstop ist höchstens ein belegter damaliger Projektionswert, kein
Beweis für ein früheres Maximum. Ein externer Stopbeleg muss Zeitpunkt/Bedeutung
und Quelle nennen. Keine automatische Umdeutung eines heutigen Brokerstops zum
höchsten historischen Signalstop. Ohne D2 bleibt aktive Altposition live gesperrt;
die Offline-Konvertierung darf ihre unbekannten Werte vollständig erhalten.

Alle vorhandenen Signale und OI-Punkte werden unverändert in `_delivery.signals`
bzw. `_delivery.oi_history` übernommen. Die vollständige importierte Historie wird
zusätzlich im unveränderlichen Migrationsarchiv gesichert. Die bestehende Grenze
von 500 Signalen im regulären Hauptlauf darf die importierte Historie beim ersten
Weiterlauf nicht abschneiden; P2b muss das bewahren bzw. einen expliziten, verlustfreien
Archivverweis samt Export implementieren. Kein neues Rendite-/Historienrechnen.

## 3. Historische Zustellungen nicht erfinden

Legacy-Signale sind Anzeige-/Entscheidungshistorie, **keine neue Outbox**.
Der Konverter setzt für den Legacy-Import `_delivery.version=1`, `messages=[]`,
`signals=<vollständige Quelle>`, `oi_history=<vollständige Quelle>`.
Das ist nur zusammen mit der validierten Migration in `control.migration` zulässig;
ein handgeschriebenes leeres Journal ohne Schnittgrenze darf keinen Live-Import
freischalten. Diese Regel ergänzt A4, sie schwächt dessen direkte Importverweigerung
nicht ab. `commands={}` bedeutet ausschließlich „keine neuen journalisierten
Aufträge“, nicht „früher wurden keine manuellen Nachrichten versandt“.

`control.migration` enthält: `migration_id` als Hash aus kanonischem Inputmanifest,
Cutover und Zielkonfiguration; Quellenhashes; B und W; Hash der gesamten Alt-Historie;
`legacy_delivery=unknown_no_replay`; Watch-Provenienz; Config-Differenz; unveränderliche
Unknown-Liste; Freigabebelege oder offene Gates. Historische Quittungen werden weder
`confirmed` noch `pending`; es werden keine Telegram-IDs erfunden. Ein fehlendes
Watchfile wird als `source_presence=missing` geführt und `watch={}` kann nur mit
der separaten Sperrgrenze W verwendet werden, niemals mit fiktivem `gewarnt_ts`.

Die Laufzeit muss die Grenze an **allen** Nachrichtenarten durchsetzen:

| Pfad | Import-/Restartregel |
|---|---|
| Signal und E41/E42-Ereignis | B oder älter: nicht auswerten/nicht senden. Historische ID bleibt in der Historie. E42 bleibt zusätzlich deaktiviert. |
| Plan und Zonen-Vorschau | Bei unverändertem B nur Anzeigeprojektion erneuern, ohne Versand. Änderung durch CVD/Parser allein darf keine Startnachricht erzeugen. Vergleichsbasis dauerhaft speichern; erst echte neue Kerze > B darf neue projektionale Nachricht erzeugen. |
| Watch | Grenzkerze W und ältere Kerzen unterdrücken, auch wenn watch.json fehlt. Fehlende alte Warnung wird nicht nachgebaut. |
| Flush-Auflösung | Auflösung eines alten Watch-Vorgangs <= W nicht senden; historische Warn-/Auflösungswerte nicht als bestätigt überschreiben. Künftige Vorgänge normal journalisieren. |
| Lage/Test | Nur ausdrücklich neuer freigegebener Auftrag mit stabiler Operation-ID und demselben Store; keine implizite Startmeldung. |
| `resend-all` | Für importierte Historie gesperrt; neue Operation-ID überstimmt weder Schnittgrenze noch Unklarheit. Kein Replay-Schalter in P2b. |

Die Unterdrückung ist dauerhaft prüfbare Migrationspolitik, keine gefälschte
Transportquittung. Gleicher Import/Restart darf keinen Beleg und keine Nachricht
verdoppeln. Import in existierenden Store ist immer Fehler, auch bei gleicher ID.

## 4. Konfiguration alt → usd

Rohes `state.config` im Archiv bytegleich behalten. Die effektive neue Konfiguration
wird einmal aus geprüftem `config-target.json` berechnet, vollständig gespeichert
und gepinnt; im Ziel-state wird sie als aktuelle Projektion geführt. Bericht zeigt
Originalprojektion, externe Alt-Konfiguration, Ziel und tatsächlich aufgelöste
Parameter. `muster_cvd=usd`, `bias_short=false`, `ausbruch_ruecktest=false` zwingend.
Keine alte Historie mit usd umschreiben, keine Parameteroptimierung.

Neuer produktiver Runner muss vor jedem Lauf fehlende, unlesbare, ungültige oder
vom Pin abweichende Konfiguration **ablehnen**, statt main.py-Fallback auf alte
eingebettete Werte/Defaults zuzulassen. Signal/Watch/Lage verwenden denselben
aufgelösten Stand. Konfigurationswechsel benötigt später neuen geprüften Pin.

Offline-Abnahme: identische abgeschlossene Eingaben einmal mit alter Projektion
und einmal mit Zielkonfiguration für die gezielte Schnittstellenprüfung, ohne
Backtestgitter oder Renditebewertung. Bis B bleibt importierter Zustand/Historie
erhalten; erster neuer Schritt muss usd verwenden. Planstop und Signalstop beziehen
sich auf denselben fortgesetzten Positionszustand, Unknown-Felder bleiben sichtbar.
Keine rekursive historische Neuentscheidung ab dem ursprünglichen Einstieg.

## 5. Ausgaben und Freigabestufen

Neues Ausgabeverzeichnis enthält `source/` mit unveränderten Eingaben,
`migration-manifest.json`, `snapshot.v2.json`, `migration-report.json`,
`MIGRATIONSBERICHT.md`, `SHA256SUMS` und `projection/` mit vorbereiteten Spiegeln.
Das Maschinenmanifest enthält Feld-Diffs, Ergänzungen, B/W, unterdrückte Altarten,
Historienanzahl/Hash, unbekannte Werte und jeden Gate-Status. Private Daten bleiben
im lokalen Paket. Bericht/CI im öffentlichen Repo nur mit sicheren Fixturewerten
oder freigegebenen Aggregaten, keine privaten Nachrichten oder Belege.

`conversion_valid` bedeutet strukturell korrekt und verlustfrei;
`activation_ready` erfordert zusätzlich belegten Stillstand, Frische, Zielbindung,
D1–D3, überprüfte Config und extern abgenommenen Store. Standard ist false.
Ein P1-Rehearsal hat unabhängig von simulierten Entscheidungen immer false.
`tools/produktion_store.py provision` soll nur explizit geprüfte Pakete akzeptieren,
einen neuen Pfad verwenden und den Store **blocked** anlegen. Aktivierung ist eine
spätere P4-Aktion, kein Parameter für P2b-Tests gegen reale Ziele.

Bei Fehlern kein aktivierbarer Snapshot und kein teilweise provisionierter Store;
Diagnosebericht darf in einem getrennten neuen Fehlerverzeichnis entstehen.
Ausgaben werden vor Erfolg noch einmal eingelesen und vollständig geprüft.
Zusammengehörige Eingaben aus unterschiedlichen Revisionen, fehlende Pflichtdatei,
NaN/Infinity, ungültige Zustände, neue unbekannte Schema-Version, fremdes Journal,
ungeklärter letzter Lauf oder Historie nach B sind klare Gegenfälle.

Rückfall: vor erstem neuen Versand Kandidat verwerfen, Quelle weiter unverändert
aufbewahren; ein späterer Altbetrieb wäre ausdrücklich zu entscheiden. Nach neuem
Versand nur aktuellen Store mit kompatiblem Code weiterführen oder anhalten.
Kein Restore von P1/P2-Testdaten in Produktion, kein Journalverlust durch main-Merge.
