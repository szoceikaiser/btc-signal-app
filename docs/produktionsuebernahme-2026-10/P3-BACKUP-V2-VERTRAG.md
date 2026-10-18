# N-P3-01: fortsetzbarer vollständiger Paketverbund v2

Vertrag vor Belastungsprüfung, 08.10.2026. Nur lokale synthetische Erprobung.
Keine Gesamtbetriebsfreigabe. v1 bleibt ausdrücklich ein begrenztes Altformat;
seine bisherigen Hashes und Belege werden nicht umgedeutet. Der v1-Restore bleibt
für alte Pakete verfügbar. Der Betriebsmonitor verlangt künftig v2. Überführung
erfordert einen neuen vollständigen v2-Verbund aus der unveränderten Quellhistorie.

## Unveränderliche Teile und Abschluss

Ein Verbund besteht aus einem Basispaket ab Revision 0 (blocked-Seed), danach
Git-Bundles mit genau dem vorigen Endcommit als Voraussetzung. Jedes Paket nennt
Index, Vorgängermanifest-SHA256, Identität, Anfang/Ende, Revisionsspanne, Anzahl,
Digest der geordneten Commit-/Parent-/Bodydigestzeilen und Datei-SHA256. Migration
liegt nur im Basispaket. Keine Kürzung, kein Squash, kein alternativer gesunder
Endstand. Alle alten Pakete bleiben unverändert und werden beim Fortsetzen nicht
kopiert. Die Ausgabe verwendet ausschließlich neue Paket- und Abschlussnamen.

Ein Abschlussmanifest bindet die geordnete Liste der Paketmanifestdigests, den
unabhängig verlangten neuesten Quellpin samt Revision und die gesamte Identität.
Vor Veröffentlichung wird aus ALLEN Paketen ein neuer isolierter Git-Store
aufgebaut, jede Revision einschließlich Parent und Digest stromweise geprüft,
Git-fsck ausgeführt und ein nachweislich blocked gesetzter Arbeitsstore erzeugt.
Erst danach ist das Abschlussmanifest mit lokaler Quittung atomar sichtbar.
Die lokale Quittung ist ausdrücklich kein privater Upload-/Readbackbeleg.

Pakete werden ebenfalls erst nach lokalem Readback und Prüfung ihrer Git-Objekte
atomar umbenannt. Unterbrechungen hinterlassen höchstens unreferenzierte gültige
Pakete oder versteckte Stagingreste, niemals einen neuen bestätigten Abschluss.
Wiederaufnahme prüft jedes vorhandene Paket erneut; widersprüchliche Fortsetzungen
halten an. Kein Überschreiben, keine automatische Löschung oder Replay.

## Getrennte Grenzen

Pro Paket: höchstens 256 Commits, 64 MiB aufsummierte unkomprimierte Storebodies,
20 MiB sämtliche Paketdateien; einzelner Body weiterhin höchstens 768.000 Bytes.
Die dedizierte Storebranch enthält ausschließlich `delivery/stream.json`;
Commitobjekt höchstens16 KiB, jeder der zwei festen Treeobjekte höchstens4 KiB.
So können zusätzliche Blobs keine ungemessene Entpacklast verstecken.
Höchstens64 Nutzdateien je Paket einschließlich der Migration, Manifest128 KiB.
Paketwechsel erfolgt vor Überschreiten von Commit-/Bodybudget. Zu große gepackte
Ausgabe hält sicher an und wird nicht als fertig veröffentlicht.
Pro Verbund: höchstens 512 Pakete, 8 GiB Paketdateien; höchstens 131.072 Commits
(bei kleineren Paketen weniger). Das entspricht theoretisch höchstens ca.257
Tagen bei 510 Writes/Tag, ausdrücklich keiner zugesicherten Laufzeit.
Vorwarnung bei 80% eines harten Größen-/Anzahllimits. Restore benötigt Platz für
vollständige Git-Objekte und blocked-Store zusätzlich zu Paketen; freier Platz
und reales Wachstum müssen vor externer Freigabe gemessen werden.

Ein Git-Prozessbaum: 120 Sekunden, 192 MiB RSS; Python-Verarbeitung: 256 MiB RSS,
gesamter Aufruf: 1.800 Sekunden. RSS wird laufend kontrolliert, Git-Packthreads=1,
Windowmemory=32 MiB und Deltacache=16 MiB. Unter Windows startet Git suspendiert,
wird vor Ausführung einem Jobobjekt zugeordnet und dann freigegeben. Der Job
begrenzt zusätzlich den gesamten committed Memory des Git-Prozessbaums auf
192 MiB und beendet bei Timeout/Schließen alle Kinder, auch Git-Launcher-Kinder.
Python-RSS und Git-Baum-RSS sind getrennte Grenzen, keine OS-Reservierung;
ein anderer späterer Host braucht eine gesonderte geprüfte Ressourcenbegrenzung.
Ein Blob/Commit wird einzeln gelesen; keine Liste aller Snapshotbodies im RAM.
Metadaten eines Pakets, höchstens 512 kleine Manifeste sowie höchstens 131.072
Commit-IDs (ohne Bodies; Git-Ausgabe zusätzlich auf 16 MiB begrenzt) sind begrenzt.
Daily-Writes kopieren nur neue Commits. Vollprüfung/Restore liest alte Pakete
erneut: CPU/Lesearbeit wächst linear, nicht konstant. Bei Zeit-/Platz-/Speicher-
grenze fehlt eine frische Quittung; 26h-Monitorfrist bleibt unverändert.

## Quittung und externer Vertrag

Die v2-Quittung bindet Abschlussmanifestdigest und Paketkettenroot, Gesamtrevision,
Quellcommit, Anzahl sowie vollständigen History- und blocked-Restorebeleg.
Der GET-only Monitor prüft die kompakte Quittung und weiterhin den Quellpin im
maßgeblichen Store. Er lädt nicht die gesamte Historie. Gemeinsames 32-GET-Budget,
Run-/Attemptbindung und 45min/15min/26h bleiben unverändert. Ein späterer realer
Backupwriter darf eine Betriebsquittung erst nach privatem Upload, Readback und
vollständigem frischem Restore exakt dieses Verbunds veröffentlichen.

Ein hart beendeter Backupwriter hinterlässt einen exklusiven lokalen Owner-Lock.
Er verfällt nicht. Erst positiv belegtes Prozessende und ausdrückliche lokale
Prüfung erlauben seine Entfernung; danach werden vorhandene Pakete erneut geprüft.

Aufbewahrung einzelner Tages-/Wochenabschlüsse darf KEINE ihrer abhängigen Basis-
oder Inkrementpakete entfernen. Keine automatische Löschung. Fehlende Teile,
falsche Reihenfolge/Vorgänger, fremde Identität, manipulierte Hashes, ausgelassene
Vorfahren oder veralteter Endpin stoppen. Blocked-Restore löscht Erfolgsindizes,
fordert Nachfolgeabgleich und wandelt sending in uncertain um; keine Aktivierung.
