# Externe Cronjobs beim spaeteren Wechsel erhalten

Nutzerentscheidung vom 15.10.2026: Die alte Engine wird bereits von externen
Cronjobs ueber workflow_dispatch gestartet. Native GitHub-Zeitplaene waren in
seinem Betrieb mehrere Stunden verspaetet. Der Anbieter und seine aktuelle
Konfiguration wurden bei dieser lokalen Korrektur nicht geoeffnet oder geaendert.

Die weiterhin deaktivierten Signal- und Wachen-Vorlagen besitzen deshalb nur
workflow_dispatch und keinen parallelen schedule-Ausloeser. Lage bleibt ein
eigener manueller Auftrag. Interne Backup-/Monitorzeitplaene werden mit dieser
kleinen Korrektur nicht veraendert; die unabhaengige externe Frischekontrolle
bleibt eine eigene Abnahmevoraussetzung.

Vor dem spaeteren Wechsel sind die tatsaechlichen alten Cronjobs, Workflow-IDs,
Zielbranch, Aktivierung, Zeitangaben/Zeitzone, Anfragemethode/-body und Alarmwege
lesend zu erfassen. Zugangswerte nicht ausgeben oder in Belegdateien speichern.
Den vorhandenen Ausloesekanal erhalten, seine Ziele/Termine aber bewusst mit
dem neuen festen UTC-Vertrag abgleichen. Alte Einstellungen sind bisher kein
Beleg dafuer, dass sie zu den neuen Slots passen. Erforderliche Aenderungen erst
als konkreten Diff vorlegen. Kein unkontrollierter Parallelbetrieb beider
Engine-Versionen mit echtem Versand.

Zieltermine laut unveraendertem engine/actions_schedule.py:
- Signal: UTC 00/04/08/12/16/20 Uhr jeweils Minute 02 und 32. Beide Termine
  haben dieselbe Deadline: Candle-Close plus 45 Minuten.
- Wache: jede UTC-Stunde Minute 08/23/38/53, Deadline jeweils plus 15 Minuten.
- Lage: bewusst separat manuell, Deadline ab Runerstellung plus 15 Minuten.

Der optionale Dispatchinput expected_start_ms ist der urspruengliche Termin
in UTC-Millisekunden. Er darf nur mit einer belegten Faehigkeit des Anbieters
korrekt erzeugt werden; keine dynamischen Platzhalter erfinden. Ohne Input
verwendet der vorhandene Code GitHub run.created_at zur Slotzuordnung. Das ist
keine unabhaengige Bestaetigung des urspruenglich geplanten Cronzeitpunkts.
Auch workflow_dispatch garantiert keinen puenktlichen Runnerstart.

Die Hauptchatprobe hat zwei getrennte tatsaechliche Wachenentries fuer denselben
Slot ausgefuehrt: auch der zweite verbraucht 17 automatische REST-GETs; seine
Pagesbeobachtungen weitere 12. Mit Plattformreserven kostet dies weitere 41
pro Doppelstart. Vier solche Doppelstarts erhoehen das bisherige Stundenmodell
von 891 auf 1055. Signalduplikate sind fuer diese Ueberschreitung nicht noetig.
Die festgelegte einzelne externe Ausloesung beseitigt diesen geplanten zweiten
Zeitplan; sie behauptet keine neue softwareseitige Nullkosten-Deduplizierung.
Manuelle Zusatzstarts, Wiederholungen und weitere Jobs sind nicht in der
891er Basis enthalten und muessen vor ihrer Freigabe beruecksichtigt werden.

Die Nutzeraufnahme zeigt eine GitHub-Runfailed-Mail. Bestehende Fehlermails
erhalten. Separat belegen, wie kein Start, zu spaeter Abschluss, veralteter
fachlicher Zustand und GitHub-Ausfall zu einer externen Meldung fuehren.
Zuerst bestehende Alarmmoeglichkeiten des Cronanbieters pruefen, keinen weiteren
Dienst allein aufgrund dieser Korrektur verlangen.

Hier wurde kein Cronjob, GitHub-Workflow, Zugang oder Benachrichtigungsweg live
geaendert und keine Nachricht verschickt. Die aktive alte Engine bleibt erhalten.
