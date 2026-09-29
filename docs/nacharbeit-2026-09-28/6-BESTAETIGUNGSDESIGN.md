# Bestätigungsdesign nach Etappe 6

Entwurf v1, 29.09.2026. **Noch nicht fachlich freigegeben und noch nicht gemessen.**
Dieses Dokument legt einen künftigen Modellvergleich fest; es erteilt kein Live-Go.
Die Nutzerentscheidungen D6-A bis D6-C unten sind vor einer Registrierung nötig.
Ein fachlich bestätigter Entwurf ist ebenfalls kein Auftrag zur Messung.

## 1. Auswahl, bekannte Vorinformation und Geltungsbereich

Kontrolle B ist ausschließlich die bereits eingefrorene Live-Basis
`LIVE-heute +Bein in Handelsrichtung`; einziger Kandidat K ist die ebenfalls
eingefrorene Zeile `LIVE-heute +E42`, E42 mit 12 Kerzen und eigenem Teilstop.
Die vollständigen Parameter stehen in `6-ledger.json.gz` unter `rows[].params`;
deren kanonische SHA256 stehen in `6-design-register.json`. Nur dieser Unterschied
wird untersucht. Keine weitere Zeile, keine Parameteroptimierung, kein Gitter,
kein Wechsel der Kontrolle auf einen späteren main-Stand. Die Kontrolle ist eine
historisch benannte Modellkonfiguration, kein Beleg des heutigen Live-Bestands.

Diese Auswahl ist nach Kenntnis früherer Messungen erfolgt und somit **keine
historisch blinde Auswahl**. E43/E44, Audit und Etappen 3b/4/6 haben Entwicklungs-
wissen erzeugt. Der alte Datenbereich einschließlich seiner Hälften ist Entwicklung,
auch wenn Kosten oder Buchführung später korrigiert wurden. Die jetzige Reproduktion
ist ein Korrektheitsbeleg und erhöht die statistische Stichprobe nicht.
Bereits gesehene Archive werden niemals rückwirkend als unabhängige Bestätigung
bezeichnet. Der generelle Zusammenhang zwischen wiederholter Backtest-Auswahl und
Überanpassung ist untersucht: [Bailey et al., The probability of backtest overfitting](https://escholarship.org/uc/item/4w1110bb).

Long/Spot, unverschuldet, V1-Fills simuliert. Keine Aussagen über V2, Shorts,
E41.6, Brokerhandel oder manuelle Orderausführung. F13/F17 bleiben unverändert.

## 2. Registrierung und unabhängiges Fenster

Vorgeschlagenes Fenster: **01.10.2026 00:00 UTC bis 01.10.2027 00:00 UTC**,
links geschlossen, rechts offen, 365 Tage / 2.190 geschlossene 4h-Kerzen.
Am rechten Rand bewertet der Schluss der letzten zulässigen Kerze den Bestand;
kein Fill am Open außerhalb des Fensters. Nicht ausgeführte Endabsichten bleiben
ausgewiesen. 10.000 USD Startcash, null BTC, frischer FLAT-Zustand je Zeile und
Szenario. Kein echter Live-Bestand und kein Entwicklungsergebnis werden übernommen.

Warmup: exakt die 365 Tage unmittelbar vor dem Fenster, nur Marktdatenpräfix,
keine geerbten Orders/Positionen/Risikopeaks. Es muss vollständig und quellenidentisch
vorliegen; andernfalls ist dieses Design nicht ausführbar. Das ist eine vorab
festgelegte Historienlänge, keine Zusicherung identischer Signale zum Live-Observer.
V1 sieht pro Entscheidung nur bis zum betreffenden Schluss abgeschlossene Daten.

Vor dem ersten Fensterbalken müssen Entscheidungen, exakte Code-SHA, Parameter-
Hashes, Datenquellen und Datencodec, Kosten, Statistik-Implementierung und Seed in
einem unveränderlich referenzierten Registrierungscommit gesichert werden.
Dieser Commit darf erst nach separat beauftragter Umsetzung und netzfreien
Handfall-/Kausalitätsprüfungen entstehen. Ein Entwurfscommit allein genügt nicht.
Verspätete Registrierung: das Oktoberfenster ist verloren; **kein stilles Verschieben**.
Ein neuer getrennter Auftrag muss ein vollständig künftiges Fenster registrieren.

Keine Rendite-, Signal- oder Ranglisteninspektion während des Fensters, keine
Zwischenentscheidung und keine Verlängerung bei schlechtem oder unsicherem Ergebnis.
Erlaubt ist technische Datenqualität ohne Strategieauswertung; Eingriffe werden
mit Zeitpunkt/Grund protokolliert. Eine Person, die die Kandidatenergebnisse vorher
sieht, kann dieses Fenster danach nicht als blind beurteilen. Nachträgliche
Strategieänderungen brauchen einen neuen Commit und neues unberührtes Fenster.

## 3. Primäre Hypothese und wirtschaftlicher Mindestunterschied

Primäres Szenario: 0,1 % Gebühr je Fill und **0,1 % Slippage je Seite**, V1
Schluss → direkt folgendes zulässiges Open, idealisierte Null-Latenz.
Alle Entscheidungen werden je Kostenfall neu erzeugt und rückgekoppelt.

E_B(d), E_K(d) sind UTC-Tagesendwerte am 00:00-Schluss, vor dortigen neuen Open-Fills.
E(0)=10.000. Für die 365 gepaarten Tage gilt
`x_d = log(E_K(d)/E_K(d-1)) - log(E_B(d)/E_B(d-1))`.
Zielgröße ist `A = exp(365 * mean(x)) - 1`, der relative Vorsprung im Endvermögen
für einen Jahrespfad. Bei genau 365 Tagen entspricht der Punktwert
`E_K(365)/E_B(365)-1`. Dies sind **keine Rendite-Prozentpunkte** und keine
versprochene Rendite. Beispiel für die Einheit: 12.240 statt 12.000 USD = 2 %
relativer Vorsprung, unabhängig vom ursprünglichen Startwert.

Vorschlag D6-B: ökonomischer Mindestvorsprung **2 % relatives Endvermögen pro Jahr**.
`H0: mu <= log(1.02)/365`; `H1: mu > log(1.02)/365`.
Ein Punktwert über 2 % reicht nicht: die einseitige Unsicherheitsuntergrenze muss
ebenfalls strikt über 2 % liegen. Diese Hürde ist eine zu entscheidende
Nutzenanforderung, nicht aus den alten Ergebnissen geschätzt.

Keine alternative primäre Sharpe-, Trefferquote-, Trade-PnL-, Monats- oder
Halbfensterhypothese. Diese Kennzahlen, wenn berichtet, bleiben beschreibend.
Trades sind wegen überlappender Positionen keine unabhängigen Stichproben.

## 4. Mehrfachprüfung und vorab feste Unsicherheitsrechnung

Die Familie enthält **m=1** Kandidatenvergleich. Kosten- und Latenzszenarien
sind Pflichtbelastungen, keine neuen Chancen auf einen positiven Test. Familien-
alpha ist 0,05 einseitig; bei m=1 entspricht Holm dem Einzeltest. Werden vor Beginn
weitere Kandidaten verlangt, ist das ein neuer Entwurf: Familie vollständig nennen,
m einfrieren und Holm mit sortierten p-Werten `p_(j) <= .05/(m-j+1)` bis zum ersten
Nichtbestehen anwenden; keine ungenutzten Kandidatenplätze oder nachträgliche
Entfernung schlechter Zeilen. Holm schützt nur bei gültigen Einzel-p-Werten;
es repariert weder kontaminierte Daten noch ungültige Bootstrap-Annahmen.
Quelle: [Holm (1979), A Simple Sequentially Rejective Multiple Test Procedure](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf).

Gepaarter stationärer Blockbootstrap der täglichen Vektoren `(r_B, r_K)`:
20.000 Replikate, NumPy PCG64, Seed 20260929, mittlere Blocklänge **14 Tage**.
Erster Index gleichverteilt aus 0..364; für jeden folgenden Tag mit Wahrscheinlichkeit
1/14 neuer gleichverteilter Start, sonst nächster zyklischer Index. Beide Zeilen
verwenden dieselben Indizes. Kein IID-Shuffle, kein Resampling einzelner Fills,
keine Suche nach der besten Blocklänge. Die genaue NumPy-Version und Quantilregel
(`method="linear"`) werden vor Beginn im Implementierungscommit gesichert.

Für jede Replikation `z_b = mean(x_b*) - mean(x)`.
`L_mu = mean(x) - quantile(z, .95)`; `L_A=exp(365*L_mu)-1`.
Berichten: Punktwert A, einseitige 95-%-Untergrenze L_A und zweiseitiges
95-%-Basic-Intervall mit Grenzen `mean(x)-q_.975(z)` und
`mean(x)-q_.025(z)`, jeweils nach A transformiert.
Nullverteilung an der H0-Grenze: `p = (1 + count[z_b >= mean(x)-log(1.02)/365]) / 20001`.
Abnahme erfordert `p <= .05` **und** `L_A > .02`; numerische Randfälle bestehen
nicht. Sensitivitäten sind vorab 7 und 28 Tage mit gleichem Seed/Replikationsumfang;
beide müssen `L_A > 0` zeigen. Sie ersetzen den 14-Tage-Haupttest niemals.

Blockbootstrap ist für schwach abhängige stationäre Reihen entwickelt:
[Politis & Romano (1994), The Stationary Bootstrap](https://users.ssc.wisc.edu/~behansen/718/Politis%20Romano.pdf).
Seine Anwendung hier ist eine **Modellannahme**, keine endliche Fehlergarantie.
365 Tage liefern bei 14-Tage-Blöcken grob 26 Blocklängen, keine 365 unabhängigen
Beobachtungen; lange Positionszyklen und Regimewechsel können das unzureichend machen.
Dieser Bootstrap schätzt Unsicherheit der realisierten Renditepaare; er erzeugt
keine konsistent neu ausgespielten Strategiepfade auf erfundenen OHLC/Flow-Daten.
DD wird deshalb nicht aus diesen resampleten Tagespaaren als Intrabar-DD behauptet.

Vor Registrierung: Statistikcode an synthetischen Null-/Alternativreihen,
Abhängigkeit, konstanten Reihen, Quantilgrenzen und Paarung prüfen. Keine echten
Kandidatenmessungen für diese Codeprüfung. Eine zugesicherte 80-%-Power ist ohne
belastbare Langfristvarianz unbekannt. Planungsrelation im Normalmodell:
`MDE_annual_log ~= (1.645+0.842)*sigma_LRV*365/sqrt(365)` über der H0-Grenze.
Sie ist keine berechnete Power dieser Strategie. Ohne ausreichende Präzision lautet
das Ergebnis **unentschieden**, nicht Gleichwertigkeit oder Kandidatenschaden.
Keine Verlängerung, neue Blocklänge oder Lockerung nach Sichtung des Ergebnisses.

## 5. Neue Risikoanforderungen, getrennt von Signifikanz

Vorschlag D6-C, ausdrücklich **neu und vorab zu entscheiden**:
in jedem festgelegten Szenario K-Schluss-DD höchstens **15 %**, obere
Intrabar-DD-Grenze höchstens **20 %**; zusätzlich beide K-DD-Werte höchstens
**2 Prozentpunkte** über B im selben Szenario. Gleichheit besteht, Überschreitung
scheitert. Diese Zahlen sind Risikobudgets des Nutzers, keine aus dem bisherigen
DD-Band abgeleitete Sicherheitsgrenze. Alte 1-Punkt-Regeln gelten nicht automatisch.

Schluss-DD und obere Intrabar-Grenze werden nach F01/F12 mit vollständigem Peakpfad
und Gebühren bewertet; Altbestand trägt Open-Lücken, Fills werden am selben Open
vor/nach Kosten bewertet. Die obere Grenze ist keine beobachtete Intrabar-Reihenfolge,
kein VaR und kein statistisches Quantil. Die untere Grenze bleibt sichtbar.
Bei verzögerten Szenarien müssen diese Grenzen erneut aus dem tatsächlich simulierten
Bestandsverlauf bewiesen werden; keine Übernahme alter DD-Werte.

Die Risiken sind deterministische Abnahmekriterien für das eine Modellfenster;
kein inferenzieller Nachweis, dass die künftige Verlustwahrscheinlichkeit begrenzt
ist. Zusätzlich berichten: Endcash/BTC, Kostenbasis, Gebühren, Exposition,
Fill-/Ablehnungsanzahl, Endabsichten und größter Positionszyklus. Keine Rangliste
aus einer nachträglich gewichteten Mischung dieser Kennzahlen.

## 6. Kosten- und Latenzbelastungen ohne Szenarioauswahl

Genau folgende fünf Szenarien pro Zeile, insgesamt zehn künftige Läufe:

| ID | Ausführung | Gebühr je Seite | Slippage je Seite | Rolle |
|---|---|---:|---:|---|
| S0 | direktes Folge-Open | 0,1 % | 0 % | idealisierte Referenz |
| S1 | direktes Folge-Open | 0,1 % | 0,1 % | einziges primäres Testszenario |
| S2 | direktes Folge-Open | 0,1 % | 0,5 % | Kostenstress |
| S3 | Open i+2 | 0,1 % | 0,1 % | zusätzlich eine volle 4h-Wartekerze |
| S4 | Open i+2 | 0,1 % | 0,5 % | kombinierter Stress |

S3/S4 benötigen separat geprüfte Offline-Umsetzung; V1 kann sie derzeit nicht
einfach durch einen Parameter einschalten. Absichten/Mengen bleiben reserviert,
bis zum Fill keine weitere Handelsentscheidung, nur Marktdaten sammeln.
Keine stille Stornierung/Revalidierung. Kein Ersatzfill außerhalb des Fensters
oder bei einer Datenlücke. Intrabar-Bestand bleibt zwischen Opens konstant.

Zusatzhürde: K-Endvermögen mindestens B-Endvermögen in **jedem** Belastungsfall
S0/S2/S3/S4; die neuen DD-Hürden gelten auch dort. Stress kann günstiger oder
ungünstiger sein; daraus keine obere/untere Performancegarantie. Stresshürden
sind keine zusätzlichen Signifikanzbehauptungen und dürfen S1 nicht ersetzen.
Historische Signalbänder bloß auf spätere Preise umzubuchen ist unzulässig.
Keine Gebühren-/Latenzschätzung aus Telegram, keine behauptete Liquidität/Queue.

## 7. Datenverfügbarkeit als zwingende Vorbedingung

Die bisher eingefrorenen Inputs belegen keine historische Publikationszeit oder
Revision. Vor Registrierung eine einzige konkrete Quelle je Feld und UTC-Codec
festlegen: OHLC samt Börse/Paar, Spot-/Futures-Flow, OI/Funding sowie alle weiteren
tatsächlich verwendeten Felder. Die Zeilen müssen dieselben Quellen und Zeitgrenzen
benutzen. Noch kein Quellenmanifest oder zukünftiges Vintage-Archiv vorhanden:
**Umsetzbarkeit ist offen**, kein Versprechen einer Messung im Oktoberfenster.

Neue Datensicherung muss pro Rohantwort Beobachtungszeit, Quellzeit, UTC-Empfangszeit,
erste Verfügbarkeit, Versions-/Revisionsstatus und SHA256 führen. Vorregistrierte
Transformationen schließen spätere Versionen von einer früheren Entscheidung aus.
Ein Feedwert darf nicht deshalb am alten Close verfügbar heißen, weil er später
für diese Kerze geliefert wurde. Fehlende/ungültige Pflichtdaten, unerwartete
Revision ohne Vintage oder Lücke in Warmup/Fenster machen den Gesamtvergleich
**nicht abnahmefähig**; keine Interpolation, rückwirkende Füllung oder günstige
Teilfensterwahl. Fehleranalyse bleibt erlaubt und beschreibend dokumentiert.

V1-S1 ist ausdrücklich ein Benchmark unter idealisierter Schlussverfügbarkeit.
As-of-Belege müssen diese Annahme pro genutztem Feld prüfbar machen. Bei Belegen
erst nach dem Schluss ist S1 kein zeitlich erreichbarer Fall; statistischer Erfolg
darin allein wird nicht als Bestätigung unter realer Datenverfügbarkeit gewertet.
Für S3/S4 muss die gesamte Liefer-/Entscheidungslatenz vor deren Fillgrenze liegen;
sonst sind auch diese Fälle nicht abnahmefähig. Ein zusätzliches reales
Latenzmodell wäre ein neuer vorab registrierter Vertrag, kein nachträglicher Filter.

Diese Etappe richtet keine laufende Sammlung/Automation ein, ruft keine neuen
Marktdaten ab und misst keinen der künftigen Kandidatenfälle.

## 8. Entscheidung, Ergebnisformen und nachträgliches Wissen

Reihenfolge der Abnahme: (1) rechtzeitige Registrierung und intaktes as-of-Manifest,
(2) Buchführung/Kausalität/Restore korrekt, (3) S1-Punktwert, p und Untergrenze
erfüllen Mindestunterschied, (4) Sensitivitäten positiv, (5) sämtliche Kosten-/
Latenz- und Risikoanforderungen erfüllt. Keine Reihenfolge als Nachtest-Auswahl.

- **Modellvergleich bestätigt:** alle Voraussetzungen/Hürden erfüllt, nur unter
  den registrierten Modell-/Datenannahmen und für dieses Fenster.
- **Nicht bestätigt:** belastbare Daten, aber mindestens eine fachliche Hürde
  verfehlt; daraus folgt weder sicherer Schaden noch Gleichwertigkeit.
- **Unentschieden:** Unsicherheit zu groß oder Inferenzannahmen nicht ausreichend
  tragfähig; vollständige Resultate und Grenzen zeigen.
- **Nicht abnahmefähig:** Registrierung/Daten/Kausalität/Implementierung mangelhaft;
  keine statistische Kandidatenentscheidung aus dem beschädigten Vergleich.

Technischer Fehler nach Fensterbeginn: betroffene Registrierung sperren,
ungeänderte Rohdaten erhalten, Fehler und alle betrachteten Ergebnisse offenlegen.
Korrigierte Auswertung ist Nachanalyse; neue Bestätigung braucht neues zukünftiges
Fenster. Kein selektives Löschen misslungener Resultate, kein Wechsel von p-Wert
auf Punktwert, kein Retuning der DD-Grenze. Alle vorgesehenen Szenarien gemeinsam
veröffentlichen, auch negative und ungültige. Andere Archive nur als neue Exploration.

**Selbst ein bestätigter Modellvergleich ist kein Live-Go.** Unbekannter manueller
Bestand, tatsächliche Fills/Verfügbarkeit/Latenz sowie F13-Runnerdauerhaftigkeit
bleiben gesondert. F13-ID ist lokale Versandidentität, kein Telegram-
Idempotenzschlüssel; unklare Zustellung blockiert, keine Exactly-once-Garantie.
Keine Wiederholung bestätigter/unklarer Sendungen und kein Versandlistenreset.

## 9. Konkrete fachliche Entscheidungen

| ID | Vorschlag zur Entscheidung | Status |
|---|---|---|
| D6-A | Nur E42/12 gegen eingefrorene Basis; zukünftiges Fenster 01.10.2026–01.10.2027 UTC, rechtzeitige Registrierung und as-of-Daten zwingend | offen |
| D6-B | Mindestens 2 % relatives Jahres-Endvermögen, einseitige 95-%-Untergrenze ebenfalls darüber | offen |
| D6-C | In allen fünf Szenarien höchstens 15 % Schluss-DD / 20 % obere Intrabar-Grenze; beide höchstens +2 Prozentpunkte gegenüber Basis | offen |

Diese Zahlen/Termine sind konkrete Entwurfsvorschläge. Schweigen bestätigt nichts.
Abweichende Antworten werden vor Registrierung eingearbeitet; Antworten erteilen
keine automatische Mess-/Implementierungs-/Live-Freigabe. Weitere offene technische
Voraussetzungen: Quellen-/Vintage-Manifest, vollständiger Warmup, S3/S4-Umsetzung,
Statistikcode samt synthetischen Prüfungen und registrierte Abhängigkeiten.

Quellen am 29.09.2026 geprüft. Methodenwahl, Zeitfenster und Hürden sind der
vorliegende Entwurf; die Quellen empfehlen diese konkreten Risikobudgets nicht.
