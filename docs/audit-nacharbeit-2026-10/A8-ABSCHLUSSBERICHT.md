# A8 – unabhängige fachliche Gesamtabnahme

Stand 03.10.2026. Geprüfte Ausgangs-SHA:
`419e3fda6494645b3c227350f1b5145bffd6271a`, Zweig
`codex/a1-audit-nacharbeit`, Arbeitsbaum `C:/Users/oeztu/BTC-Trading/a1-work`.
Vergleichsbasis der Nacharbeit ist `dc5ddd6aaa8cde6a44c51892910c045ebd6f387a`;
es wurde dort weder neu begonnen noch ein anderer Arbeitsbaum verändert.
Prüfung ohne parallele Agenten. Die nach dem Commit verifizierte Abschluss-SHA,
CI und additive Wiederherstellung stehen in der externen A8-Übergabe.

## Gesamturteil

**Die Auditnacharbeit ist im dokumentierten Offline-Umfang fachlich abgenommen.**
Alle 22 Original-IDs sind einzeln bewertet. A8 fand vier konkrete neue Codefehler
in drei IDs: zyklusübergreifende Teilverkaufsmenge und eingefrorenes Einstiegsbudget
in F02, einen ungültigen Tagesabschluss in F08 und ungültige Messwerte/Gewichte
in F14. Diese Fehler wurden korrigiert, nicht als Daten- oder Betriebsgrenze
umetikettiert. Die Nachweise der betroffenen V035-Rechnung wurden neu erstellt.

17 IDs sind innerhalb ihrer Verträge korrigiert/geprüft, F02/F12/F13 sind mit
ausdrücklich begrenzter Reichweite teilweise erledigt, M01/M02 sind fachlich
bewertete offene historische bzw. inferenzielle Grenzen. Keine allgemeine
Fehlerfreiheit außerhalb der geprüften Verträge und **keine Live-Freigabe**.
Reale Versandbereitstellung, damalige API-Verfügbarkeit, echte Fills und
historische Derivat-Ausführbarkeit bleiben unbewiesen.

## Neu gefundene Fehler und erneuerte Belege

Zeilen beziehen sich auf den A8-Abschlussbaum, soweit ausdrücklich anders angegeben.

| Priorität / ID | Datei / Zeile | Auswirkung, Korrektur und Gegenbeleg |
|---|---|---|
| P1 F02 | `engine/execution_perp_offline.py:107`; vorher an `419e3fd` `:106` | Nach Flat blieb `peak_qty` des vorigen Kapitalzyklus bestehen. Nach erst 5 BTC, vollständigem Ausstieg und neuer Position von 2,5 BTC verkaufte TP1 2 statt 1 BTC. Jetzt wird der Peak beim neuen Flat→Open-Zyklus zurückgesetzt; Long und Short sind geprüft. `engine/test_a8_acceptance.py:21`. |
| P1 F02 | `engine/execution_perp_offline.py:110`; vorher `:40,106` | `alloc` blieb lebenslang am ursprünglichen Startwallet hängen. Nach 1.000 USD Start und 100 USD realisiertem Gewinn kaufte eine neue 50-%-Tranche bei 100 USD nur 5 statt 5,5 BTC. Neues Zyklusbudget ist realisiertes Wallet × vorgegebene Kapitalquote; innerhalb desselben Zyklus bleibt es fest. Dies stellt die dokumentierte Kapitalzyklus-Semantik wieder her, ohne Parameter zu optimieren. `engine/test_a8_acceptance.py:33`. |
| P2 F08 | `engine/strategy_core.py:319,324,334` | Ein vollständiger Tag plus zusätzliche falsch ausgerichtete Kerze wurde entgegen A3-Vertrag akzeptiert. Jetzt wird der betroffene UTC-Tag verworfen, unabhängig von der Eingangsreihenfolge; ein anderer gültiger Tag bleibt erhalten. `engine/test_a8_acceptance.py:13`. |
| P2 F14 | `engine/coinalyze.py:595,611,853` | Vorhandener Schlüssel bedeutete bislang vollständige Messung, auch bei NaN oder unzulässigem OI-Gewicht. Summen verlangen endliche Zahlen; gewichtete Mittel zusätzlich nichtnegative Einzelgewichte und positives Gesamtgewicht. Ungültige Zeitpunkte werden ausgelassen und gezählt, echte gemessene Null bleibt gültig. `engine/test_a8_acceptance.py:45`. |
| P2 F02 / Kontrollbeleg | `tools/a7_v035_causal.py:100` (erhaltener A7-Code); neu `tools/a8_perp_reference.py:20` | Der A7-Ausdruck addierte die bereits vom Produktionsbuch berechneten Gebühren, realisierten Gewinne und Fundingbeträge. Das prüfte Konsistenz, aber nicht unabhängig deren Herleitung. A8 rekonstruiert Mengen, Annahme/Ablehnung, FIFO-Lose, Gebühren, Funding, Wallet, Margin, Equity und jede stündliche Risikoprüfung mit `Fraction` aus Aufträgen und eingefrorenen Marktquellen. Sämtliche Differenzen sind 0; drei gezielte Verfälschungen von Gebühren, Funding und Menge werden erkannt (`tools/test_a8_reference.py`). |
| P3 Registerklarheit | `REGISTER.md:1`, `REGISTER.json` | Alte primäre Status-/Reichweitenfelder konnten trotz neuer A7-Anhänge einen überholten Stand vermitteln. Alle 22 erhalten jetzt einen eindeutigen A8-Endstatus mit eigener Reichweite, Fundstelle, Beleg und Grenze. Vorherige Registeraussagen bleiben als gekennzeichnete Historie erhalten. |

Die vier neuen Testfunktionen scheitern am exakten A7-Ausgangscode und bestehen
nach der Korrektur. `tools/a8_counterexamples.py` lädt dafür die originalen
Git-Blobs nur in den Speicher; Originaldateien bleiben unverändert.
Ergebnis: [A8-counterexamples-v1.json](A8-counterexamples-v1.json).

## F02/V035: vier unterschiedliche Aussagearten

1. **A5-Modellbuch:** synthetische explizite Fills, 1x-Kapitalbindung und
   Fundingkalender. Keine Strategie- oder historische Renditevalidierung.
2. **Retrospektiver Einzelfall:** die alte 84-Stunden-Shortprobe mit
   10.144,86631483201195346419060 USD bleibt ein eigener Buchfall. Ihre
   Signalreferenzen und Kostenannahmen ergeben keinen geschlossenen kausalen
   Gesamtstrategielauf. A8 ändert diesen alten Beleg nicht.
3. **Kausaler Pfad:** abgeschlossene 4h-Entscheidungen, bestätigte simulierte
   Fills am nächsten zusammenhängenden 4h-Open, aktuelle Zykluskapitalbasis,
   Decimal-Gebühren, absolute stündliche USD/BTC-Fundingraten und Markrisiko.
   Keine Platzhalter sind in einem gültigen historischen Lauf zulässig.
4. **Hypothetischer Weiterlauf:** fehlende Sätze werden ausdrücklich mit 0 bzw.
   illustrativ −1/+1 USD/BTC ersetzt; verletzte Risiken werden protokolliert.
   Das dient allein der Diagnose. Es ergibt weder historische Positionen nach
   der ersten Sperre noch eine valide Rendite oder belastbare Renditeschranken.

Die korrigierten Werte stehen ausschließlich in
[A8-V035-causal-v2.json](A8-V035-causal-v2.json). Die A7-v1-Dateien und ihre
Berichte bleiben historische Belege am damaligen Code; ihre konkreten V035-
Mengen und Risikowerte sind durch A8 überholt.

| Frage | A7/v1 | A8/v2 nach Fehlerkorrektur | Gültige Aussage |
|---|---|---|---|
| 04.02.2026 12:00 UTC fehlende Rate | flat | flat | Bis dahin strikter Pfad ohne Zahlungspflicht in dieser Stunde. |
| 13.02.18:00 Rate, Zahlung 19:00 UTC | 0,0798 BTC Short | **0,0818 BTC Short** | Strikter Lauf stoppt weiterhin am **13.02.2026 19:00 UTC** mit `MissingFunding`. |
| Erste 1x-Verletzung mit Null-Platzhaltern | 17.04.15:00 UTC | **17.04.2026 14:00 UTC** | Bruttonotional **9.544,3676048208258 USD** > Equity **9.483,7993086568568546125155 USD**. Schon zuvor durch fehlende Februarrate ungültig. |
| 09.05.06:00 Rate, Zahlung 07:00 UTC | 0,0937 BTC Long hypothetisch | **0,1088 BTC Long hypothetisch** | Keine gültige historische Positionsfeststellung nach Funding- und Risikosperre. |

Der Null-Platzhalterlauf hat 363 Kandidaten, 341 Fillversuche, 144 angenommene
Fills und 4.216 Fundingbuchungen. Das sind **Diagnosezähler**, keine Kennzahlen
einer historisch gültigen Rendite. Die drei illustrativen Fundingansätze
lassen die relevante Lückenmenge unverändert; sie sind keine Zahlungsbelege.
Der separate gültige Präfix bis 01.02.2026 00:00 UTC ist ereignisgleich.
Die unabhängige Rechnung prüft je vollem Diagnoselauf 4.557 Ereignisse und
sämtliche stündlichen Marks, im Präfix 146 Ereignisse. Die explizite
Vergleichstoleranz beträgt 10⁻¹⁸ USD; die tatsächlich größte Abweichung ist 0.

**Keine V035-Gesamtrendite und kein Renditevergleich mit der alten Signalkonten-
Diagnose wird freigegeben.** Auch vollständige Raten würden allein keinen
Börsenliquidationsvertrag, historischen Tarif, Orderbuch oder tatsächliche
Ausführung belegen. Der S0-Gebührensatz 0,1 %, der 0,0001-BTC-Schritt und die
stündliche Markauflösung sind Modellannahmen. Kein Solvenznachweis zwischen Marks.

## Alle ursprünglichen Konfigurationen und Basis/E42

Die 79 Gitter- und acht Strukturzeilen ergeben nach dem belegten Alias S004=V000
genau **86 ursprüngliche Konfigurationen**. Das vor Ergebnismessung eingefrorene
Manifest bleibt unverändert. 85 Spotzeilen sind unter dem modellierten
Quellen-/Zeitvertrag auswertbar; V035 bleibt als eigene gesperrte Zeile erhalten.
Keine Kandidatenwahl, Schwellenoptimierung oder Nachoptimierung von M01/M02.

Die unabhängige Strukturprüfung bestätigt 1.681 referenzierte Dateihashes und
exakt 1.250 kausale Ergebnisdateien: 850 Gitterläufe (R0/R1 × S0–S4), 340
S0-Hälften, 40 Drittel-Frischstarts und 20 zusätzliche Kapitalquotenläufe.
Monate, fortlaufende Drittel, offene Endorders und unabhängige Buchnachweise
sind enthalten. 170 alte Diagnoseobjekte mit jeweils vier Fällen und 170
separate alte Halbzeitobjekte bleiben getrennt indexiert. Beleg:
[A8-acceptance-v1.json](A8-acceptance-v1.json), ursprünglicher
[A7-Ergebnisindex](A7-resultindex-v1.json).

Die 2.493 eingefrorenen Kerzen sind eindeutig, zusammenhängend und auf 4h UTC
ausgerichtet. Der neue F08-Fehlerzweig kann diese Daten nicht berühren. Der
F14-Aggregatadapter gehört nicht zu dieser eingefrorenen Einzelmarktreihe;
der F02-Pfad ist separat. Deshalb bleiben die 85 Spotreihen samt Artefakten
unverändert; eine Wiederholung aller 1.250 Rechnungen wäre nicht begründet.
Die sichere CI prüft zusätzlich das feste R0/R1-S0-Paar mit unabhängigem Buch,
die A2-Zwischenwirkungen, Statistik und den vollständigen Ergebnisindex.

Für **R1/S0** bleiben Basis/V000 **13.381,598027877413 USD** und E42/V004
**13.262,942895190434 USD**; E42 liegt **118,655132686979 USD** zurück.
Für S1/S2/S3/S4 sind die E42-Differenzen gerundet −173,96 / −346,73 /
+117,27 / −56,23 USD. Der Vorteil hängt vom Ausführungs-/Kostenszenario ab.
Das feste Paar stimmt in allen zehn gespeicherten Szenarien mit Nach-6 überein.
Keine Gitterzeile erfüllt die alte Hälftenschwelle von +1 Prozentpunkt in
beiden separat gestarteten Hälften. Das trägt keine Aktivierung von E42 oder
eines anderen Kandidaten. Es beweist ebenso wenig eine universelle Untauglichkeit
der betreffenden Regel.

Die A7-Ereigniszuordnung ist begrenzt und richtig getrennt: 79/85 Änderungen
zwischen Originalaudit und aktueller numerischer Alt-Reihe bündeln mehrere
Revisionen. Modellierte Verfügbarkeit entfernt bei V050 zwei Nachkäufe und
ändert S0 um +159,461596 USD (R0) bzw. +159,018561 USD (R1). Die anschließende
CVD-Korrektur entfernt bei V075 eine Warnung ohne Renditeänderung. Daraus wird
keine monokausale Erklärung aller alten Ergebnisdifferenzen abgeleitet.

## M01/M02 und Betriebsgrenzen

M01: Alle 76 dokumentierten Entscheidungen sind ihrer damaligen Basis und
ihrem Fenster zugeordnet. 85 alte Codezeilen verteilen sich in eine identische,
23 einfach und 61 mehrfach abweichende Basen. Fehlende frühere Rohreihen werden
nicht durch V000 ersetzt. Die Chronik ist keine unabhängige Replikation alter
Entscheidungen; Quellen-/Furkan-/Forschungsberichte bleiben erhalten.

M02: Mindestens 94 dokumentierte Suchen sind eine Untergrenze, nicht die bekannte
vollständige Suchfamilie. R0/R1 überlappen; Monate, Hälften und Drittel wurden
wiederverwendet. Zehn gepaarte Auswertungen des festgelegten V000/V004-Paars
verwenden 251 bzw. 253 vollständige UTC-Tage. Das R1/S0-14-Tage-Intervall von
etwa −3,74 bis +1,87 Prozentpunkten beschreibt bedingte Unsicherheit; es ist
keine auswahlbereinigte Signifikanz, keine unabhängige Stichprobe und keine
Prognose zukünftiger Überrendite. Der expositionsangepasste Buy-and-Hold-
Vergleich bleibt ausdrücklich post hoc.

F13: Code und simulierte harte Runnerabbrüche belegen Intent-/Quittungserhalt
auf einem separat überlebenden geeigneten Volume. Reale Bereitstellung,
Migration und Runneranbindung fehlen weiterhin. Ohne sie verweigert der neue
reale Versand den Betrieb. `uncertain` wird nicht automatisch zurückgesetzt;
keine Exactly-once-Zusage und kein Schutz bei Volume-Verlust, getrennten
Kopien, NFS oder veraltetem Backup. A8 sendete keine Nachricht.

Weitere Grenzen: heutige Marktlisten/Quote-Kurse beweisen keinen historischen
Börsenkorb; historische API-Publikation bleibt modelliert; V1/i+2 belegen keine
realen Fills. V2-Orders, E41.6 und unbekannte manuelle Bestände sind nicht
beauftragt. Die alte Pages-Kette hört auf Signal-Engine/Backtest; deshalb
wurde kein solcher Workflow aufgerufen. Alle neun lokalen und acht aktuellen
Default-Workflows einschließlich `workflow_run` wurden vor Push geprüft:
[A8-prepush-workflows.json](A8-prepush-workflows.json). Nur Tests und der
zusätzlich jobseitig auf den Audit-Zweig begrenzte Offline-Workflow dürfen
durch diesen Push starten. Keine Secrets, Sammlung, Pages, Broker oder Aktivierung.

## Prüfungen, Sicherung und Ende

- Lokale zusammengeführte Engineregression nach F02/F08: 795/0. Nach dem
  ergänzenden F14-Fix: sämtliche 68 betroffenen A3-/Coinalyze-/A8-Funktionen
  bestanden; keine unnötige zweite lokale Gesamtrunde. Sechs vorhandene
  Perpetual-Handfälle, unabhängige Referenz samt drei Verfälschungsproben,
  Quellpreflight und Ergebnisindex bestanden. Die finale vollständige
  Tests-CI muss zur tatsächlichen Abschluss-SHA grün sein.
- A6: sämtliche 316 Originalfälle geprüft und vollständig kategorisiert;
  243 Assertions, 13 beabsichtigte Fehlerzweige, 30 aktuelle Entsprechungen,
  fünf Vertragsablösungen und 25 nur historisch vorhandene Fälle. Die 14
  gespeicherten Laufzeitfehler einschließlich der neuen Entsprechung wurden
  anhand Typ/Traceback und grüner Gegenprobe geprüft. Drei abgeschnittene
  Assertion-Tails sind durch A6s getrennte Rückgabecodes (1 Assertion, 2
  sonstiger Fehler) belegt. Kein übersprungener Fall zählt als Treffer.
- Drei gezielte Checkpoint-Prüfungen: wartender Kauf, offener Bestand sowie
  Ablehnung veränderter/inkompletter Fortsetzung. JSON-Neustart ist exakt gleich.
- Alle 17 ursprünglichen Manifest-Quellhashes wurden separat abgeglichen.
  Die A7-Sicherung hat 13 geprüfte Manifest-Einträge; Bundle mit vollständiger
  Historie, Restore-SHA/-Baum und sauberer Restore-Zustand stimmen. Beleg:
  [A8-prior-backup-verification.json](A8-prior-backup-verification.json).
- Der A8-Abschluss erzeugt ein eigenes vollständiges Bundle, Inhalts-/
  Hashmanifest und einen frischen Restore. Dort werden Git-Integrität,
  Artefaktgleichheit, A8-Gegenfälle, kausale v2-Rechnung und gezielte
  Checkpointgleichheit geprüft. Ergebnisse, wahre SHA und exakte CI-URLs
  stehen ausschließlich in `restore-verification.json` und `UEBERGABE.md/json`
  der additiven A8-Sicherung; dieser Commit behauptet keine vorweggenommene CI.

Private Drittmaterialien wurden weder verwendet noch kopiert. Originalaudit,
R0/R1-Rohdaten, alte Berichte und Sicherungen bleiben unverändert. Nach der
verifizierten Commit-/CI-/Sicherungsabnahme endet A8 und damit dieser Auftrag.
Ein weiterer allgemeiner Prüfauftrag oder Folgeprompt ist nicht erforderlich.
