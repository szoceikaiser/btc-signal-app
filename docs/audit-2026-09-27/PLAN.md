# Unabhängiger Audit – Plan und Vorfestlegung

Stand: 27.09.2026. Auftrag: vollständige unabhängige Prüfung, kein Merge-Go.
Gewünschte Modelleinstellung: GPT-6 Astra, maximaler Aufwand. Die Modellwahl ist eine
Einstellung des aufrufenden Clients; dieses Dokument behauptet keinen technischen
Modellwechsel durch ein Audit-Skript.

## Sicherung und Grenzen des Auftrags

- Signal-Repo: `https://github.com/szoceikaiser/btc-signal-app.git`.
- Backup-Wurzel bleibt unberührt. Eigener Arbeitsbaum: `../audit-work`.
- Audit-Zweig: `codex/audit-2026-09-27`, Ausgangspunkt
  `e2b0051199c2e0c38723cc3a23c00ea3bd320601` (E44.5).
- Remote-main bei Beginn: `89885adc9fb6d2eae60f7a64f9452760a4e33cd9`.
  E44.4: `eeb4eea72e3ac2baa5b713c57337801b1b8bc291`.
- GitHub-Lesezugriff und Push-Probelauf am 27.09.2026 erfolgreich. Noch keine
  Veröffentlichung, kein Telegram, kein Schreiben nach main.
- `pages.yml` reagiert auf erfolgreiche `Backtest`- und `Signal-Engine`-Läufe
  ohne Einschränkung auf deren Zweig. Diese Workflows werden NICHT gestartet.
  Ein Push auf den Audit-Zweig startet nach gegenwärtiger YAML nur `Tests`.
- Private Transkripte werden ausschließlich lokal gelesen. Öffentlich gespeichert
  werden Fundstellen, Prüfsummen, Regelzusammenfassungen und kurze Belegzitate.
- Produktionslogik und Live-Konfiguration bleiben unverändert. Korrigierte
  Messungen entstehen in isolierten Audit-Werkzeugen und werden getrennt benannt.

## Arbeitspakete und Abnahme

1. Herkunft: Remotes, Zweige, Workflows, Code-/Daten-Hashes, vollständiges Inventar.
2. Entscheidungen: Chronik E1–E44.5, alle Schalter und Datenvarianten; ursprüngliche
   Basis, Fenster, Kennzahlen, Regel und Entscheidung mit Beleg und Beleglücke.
3. Originalquellen: alle sechs gefundenen Transkripte vollständig lesen;
   Regel → Formulierung → Code → Test → Signal. Allgemeine Regel, Einzelsituation,
   Rückschau und Entwicklerinterpretation ausdrücklich unterscheiden.
4. Software: vollständige vorhandene Suite; gezielte unabhängige Gegenrechnungen,
   zeitliche Kausalität, Signal-Ausführung, Bestand/Kapital, Persistenz/Telegram.
5. Historische Reproduktion: nur mit damaligen Eingaben und Code so nennen.
   E44.5 bytegenau wiederholen; ältere Artefakte/Commits inventarisieren.
6. E42: Zustandsübergänge je beobachteter Marke, einmalige Ereignis-IDs, Rückkäufe
   als eigene Lose mit allen späteren Abgängen, Kosten und offenem Rest; zusätzlich
   gesamter Portfoliopfad mit/ohne E42, direkte und indirekte Effekte trennen.
7. Gemeinsame Messbasis: eingefrorene E44.5-Eingaben, heutige Live-Parameter,
   komplette zusammengehörige kleine Gitter, aktive Bestandteile ausschalten.
8. Forschung: Primärquellen, konkrete Übertragbarkeit und historische/live
   Verfügbarkeit; keine Aufnahme zusätzlicher Indikatoren ohne Messdesign.
9. Berichte: priorisierte Befunde, Entscheidungskatalog, Kombinationsmatrix,
   E42-Fälle, Datenlücken und Maßnahmen; Abdeckung ehrlich abschließen.

## Vorab festgelegtes Messdesign (vor neuen Renditeläufen)

Gemeinsame Datenbasis zunächst `docs/e445/eingaben.json`, deren SHA-256 vor dem
ersten Lauf gespeichert wird. Sie enthält abgeleitete Kerzen/Flow-Reihen, keine
vollständigen historischen HTTP-Rohantworten. Vollständigkeit und Kausalität sind
zuerst zu prüfen. Neue Daten dürfen ältere Messungen nicht als Reproduktion ersetzen.
Vergleichsbasis ist die Konfiguration von eingefrorenem Remote-main, nicht eine
nachträglich ausgewählte Gewinnerzeile. Abweichungen des E44.5-Codes bei Default
werden separat gegen main geprüft.

Hypothesen und Gitter, keine ergebnisgetriebene Parametersuche:

| ID | Faktoren | Hypothese / Zweck |
|---|---|---|
| G1 | E42 aus/an × Verkauf 1/0,67 × Rest aus/an | E44.5 reproduzieren; Beteiligung nach Verkäufen |
| G2 | E42 aus/an × high_exit off/on × trail_stop aus/an | Rückkauf hängt vom vorherigen Verkauf und späterem Stop ab |
| G3 | stop_rueckeroberung 0/1 × bein_richtung auto/bias × zonen_nachziehen aus/an | Stop-Entscheidung auf alter/neuer Struktur-Basis |
| G4 | buy_ladder aus/an × flush_entry off/core × liq_entry off/boost | Mehrfach-Aufstockung, Kapitalbindung und Überschneidungen |
| G5 | E42 aus/an × muster_cvd alt/dollar × muster_oi usd/btc | Korrekte Einheiten/CVD-Nullpunkt als technische Gegenprobe |

Für G5 werden die genauen im Code zulässigen Modusnamen vor dem Lauf geprüft;
eine Namensanpassung ist keine Parameteroptimierung. Doppelte Konfigurationen
werden einmal gerechnet und in allen zugehörigen Gittern referenziert.
Zusätzlich: jeder aktive Handelsmechanismus einzeln aus; jeder bereits vorhandene
ausgeschaltete Mechanismus mit seinen dokumentierten Gitterwerten einzeln gegen
dieselbe Basis. Keine neue Schwellenwahl anhand des Ergebnisses. Falls weitere
Kombinationen begründet nötig sind, werden sie vor deren Berechnung als explorative
Erweiterung separat festgehalten. Nicht untersuchte Kombinationen werden genannt.

Kennzahlen: Rendite, maximaler Rückgang, Kosten in Geldeinheiten, Kauf-/Verkaufszahl,
abgeschlossene Positionen, Kapitalbindung, Monate, zwei separat gestartete Hälften,
zeitliche Abschnitte und Sensitivität gegenüber Ausführung und Kosten.
Bestehende Regel für G1 exakt nachrechnen. Audit-Erfolgskriterium für einen
**weiter zu prüfenden Kandidaten**: beide Hälften mindestens +1 Prozentpunkt
(explorative Kombinationen +2), Rückgang höchstens 1 Punkt tiefer, Vorteil nicht
nur aus einem Monat, kein bestätigter Buchungs-/Kausalitätsfehler als Gewinnquelle.
Das ist ausdrücklich kein statistischer Beweis und keine Freigabe.

Alle vorhandenen Daten wurden bereits wiederholt zur Entwicklung benutzt. Kein
Abschnitt wird als unberührter Test bezeichnet. Zeitlich getrennte feste Prüfungen
und rollierende Auswertung werden soweit möglich verwendet; Parameter bleiben
fest, kein Sieger wird rückwirkend durch das Testfenster ausgewählt. Resampling
erfolgt in zusammenhängenden Zeitblöcken, nicht durch unabhängiges Mischen einzelner
4h-Kerzen. Mehrfachtests werden gezählt; Unsicherheitsintervalle und Ereigniszahlen
begrenzen Aussagen. Bei zu kurzer Historie bleibt ein echter Vorwärtstest offen.

## Laufprotokoll

| Lauf-ID | Zweck | Status |
|---|---|---|
| audit-20260927-00 | Zugang, Remote-Stand, Workflows, Plan | erledigt |
| audit-20260927-01 | Basissuite, Inventar, Datenvalidierung | erledigt, 607 Tests bestanden |
| audit-20260927-02 | E44.5-Reproduktion | erledigt, inhaltlich exakt |
| audit-20260927-03 | unabhängige Gegenproben und E42-Lose | erledigt, Befunde und Grenzen dokumentiert |
| audit-20260927-04 | vorab festgelegte gemeinsame Gitter | erledigt, 79 Konfigurationen |
| audit-20260928-05 | separat vorher festgelegte Kapitalquoten | erledigt, siehe ERGAENZUNGSPLAN.md |
| audit-20260928-06 | separat vorher festgelegtes frühes E4-Gitter | erledigt, acht Zeilen / sieben zusätzliche Konfigurationen |

Zwischenstände werden regelmäßig auf diesem Zweig gesichert. Kein alter Befund
wird durch Überschreiben seiner Ursprungsdatei scheinbar korrigiert.

## Abschlussvermerk 28.09.2026

Die obigen Hypothesen und Kriterien wurden nach Kenntnis der Ergebnisse nicht
gelockert. G1 übernimmt die ursprünglichen Rollen (+1 Hauptzeile, +2 erklärende
Kombinationen); neue G2–G5-Kombinationen werden nach der vorab strengeren +2-Regel
eingeordnet. Alle 79 Parameterzeilen waren vor dem Lauf in e7e92d3 festgeschrieben.
Die ergänzende Kapitalquotenrechnung wurde separat in 9b916f0 vor ihrer Berechnung
begründet. Das frühe E4-Strukturgitter wurde separat in 098a65d vor der Berechnung
festgeschrieben; es ergänzt sieben eindeutige Konfigurationen auf insgesamt 86.
Detailergebnisse: BERICHT.md, ABDECKUNG.md und REPRODUKTION.md.
