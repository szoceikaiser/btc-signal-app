# Retrospektives Prüfdesign nach Etappe 6

Version 2, 29.09.2026. Der Nutzer verlangt ausdrücklich eine Prüfung **von der
Vergangenheit bis zum aktuellen Stichtag ohne Jahreswartezeit**. Dies ersetzt das
Zukunftsfenster von Version 1. Keine neuen Kandidatenmessungen oder Live-Freigabe
in dieser Designänderung.

## 1. Sachliche Aussage und bekannte Daten

Historische Daten dürfen trotz Vorkenntnis ausgewertet werden. Verbindlich sind
feste Regeln, kausale Simulation, erhaltene Rohdaten, unabhängige Buchführung und
vollständige Resultate. Fehlende Emotion beseitigt statistische Auswahlwirkungen
nicht: Unter vielen ausprobierten Regeln kann zufällig eine gute ausgewählt werden,
auch durch KI. Die Kenntnis früherer Ergebnisse wird offengelegt.

Drei Ebenen unterscheiden: (1) reproduzierbarer historischer Modellbefund,
(2) Stabilität über feste Zeitabschnitte/Kosten/Latenz mit ausgewiesener Unsicherheit,
(3) auswahlbereinigte statistische Evidenz nur bei hinreichend erfasster früherer
Suche und tragfähigen Inferenzannahmen. Ein zukünftiges Jahr ist dafür keine
Voraussetzung. Bekanntes Material bleibt allerdings **kein unabhängiges
Bestätigungsfenster**. Spätere historische Teilfenster werden durch Präfixsimulation
nicht rückwirkend unabhängig von der Strategieentwicklung. Reproduktion zählt
nicht als neue Stichprobe.

[White (2000), A Reality Check for Data Snooping](https://doi.org/10.1111/1468-0262.00152)
behandelt die Überlegenheit des besten Modells einer Spezifikationssuche.
[Hansen (2005), A Test for Superior Predictive Ability](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=264569)
ergänzt einen studentisierten Test. Beide benötigen Voraussetzungen; ein
Methodenname repariert keine fehlende Suchhistorie.

## 2. Varianten, historische Pakete und Stichtag

Kontrolle B: `LIVE-heute +Bein in Handelsrichtung` aus gesichertem 5b
`bb862204c97c6bb4c0da49cb6f1de90dd58af663`. Einziger Bewertungskandidat K:
`LIVE-heute +E42`, E42/12 mit eigenem Teilstop. Vollständige Parameter und
kanonische Hashes in `6-design-register.json` und `6-ledger.json.gz`.
Keine weitere Variante/Optimierung und kein Wechsel auf neueren main.
Die Kontrolle ist eine historische Modellkonfiguration, kein belegter Live-Bestand.

| Paket | Beginn Handel | Stichtag | Stand |
|---|---|---|---|
| R0 | 18.01.2026 20:00 UTC | 27.09.2026 08:29:08.840 UTC | sechs Läufe vollständig reproduziert |
| R1 | gleicher Beginn/Warmup | **29.09.2026 12:00 UTC** | historische Aktualisierung geplant, weder beschafft noch gemessen |

R1-Zielstichtag ist die letzte abgeschlossene 4h-Grenze der gelesenen UTC-Uhr
29.09.2026 12:01:31. D01 lässt nur Kerzen mit Schluss spätestens am Stichtag zu.
R0 bleibt unverändert: 2.480 zulässige Kerzen einschließlich vorhandenen Warmups,
1.509 Handels-Closes je Fall, ursprüngliche Inputs und Ergebnis-Hashes.
R0 nicht als Ergebnis „bis heute“ ausgeben.

R1 vor Auswertung separat mit Rohdaten-, Transformations-, Code- und Parameter-
Hashes sichern. R0-Präfix byte-/feldgenau erhalten. Revisionen separat benennen,
niemals still überschreiben. Fehlende neue Pflichtdaten als Lücke ausweisen;
keine Interpolation oder automatische Verschiebung des Stichtags beim späteren
Abruf. Frühere Archive/Handelsstarts nur mit getrennt festgelegtem kompatiblem
Paket, nicht durch Zusammenkleben günstiger Fenster.

Vorhandener Warmup bleibt exakt erhalten. 10.000 USD Startcash, null BTC,
frischer FLAT-Zustand, keine geerbten Orders/Risikopeaks. Schlussbewertung am
letzten zulässigen Close; keine fingierte Liquidation oder Fill außerhalb des
Fensters. Long/Spot, unverschuldet, V1-Fills simuliert.

## 3. Fixierter Analyseplan und Suchhistorie

Version 2 wird **vor der nächsten Auswertung** gesichert. Dies ist eine
Analysefestlegung nach Datenkenntnis, keine rückwirkende Präregistrierung vor
Datenentstehung. Paket-/Code-SHA, Zeilen, Zeitabschnitte, Kosten, Seed und
Statistikversion vor R1/statistischer Analyse fixieren; danach kein Retuning.
Korrekturen mit neuer Version/Grund und Vergleich zum alten Ergebnis dokumentieren.

Frühere Auswahl zunächst nur lesend rekonstruieren: E43/E44, Audit, Etappen
3b/4/6, betrachtete Schalter/Parameter/Kombinationen, verwendete Daten und Gründe
für Auswahl/Verwerfung. Deduplizieren nach vollständiger Konfiguration plus
Code-/Datenversion, nicht nur Name. Auch die Auswahl der Kontrolle erfassen.
Eine rohe Anzahl Versuche beweist keine vollständige Familie.

## 4. Wirkung und Risiko ohne erfundene persönliche Budgets

Hauptfall S1: 0,1 % Gebühr und 0,1 % Slippage je Fill.
Primäre Wirkung `A_window=E_K(end)/E_B(end)-1`, zusätzlich USD-Unterschied,
beide Nettorenditen, Gebühren, Cash/BTC, Restkosten und Exposition.
Wissenschaftliche Richtungsfrage `H0: mu<=0` gegen `H1: mu>0` für den mittleren
gepaarten täglichen Logrenditeunterschied. Positiver Punktwert allein genügt
nicht für eine statistische Überlegenheitsaussage.

**2 % wirtschaftlicher Mindestvorsprung aus Version 1 zurückgezogen.**
Kein bestätigtes Nutzenbudget vorhanden. Effektgröße, Unsicherheit und Kosten
berichten; kein persönliches Mindestmaß als wissenschaftlich hergeleitet ausgeben.
Hauptausgabe für echte Fensterlänge. Annualisierung, falls gezeigt, lediglich
Rechenskalierung, keine neue Stichprobe oder erwartete zukünftige Rendite.

**15 % Schluss-DD / 20 % obere Intrabar-Grenze / +2 Prozentpunkte zurückgezogen.**
Risikotoleranz lässt sich ohne Nutzervorgabe nicht objektiv herleiten. Beide DD-Maße,
untere Grenze, Differenzen zur Basis und größte Rückgangsphasen vollständig zeigen.
Keine alten DD-Schwellen übertragen und keine neuen absoluten Verlustbudgets erfinden.

Gewichtungsfreie Vergleichsaussage **historische Dominanz**: mindestens gleiches
Endvermögen, höchstens gleicher Schluss-DD und höchstens gleiche obere Intrabar-
Grenze, mindestens eine strikte Verbesserung, im selben Fenster/Kostenfall.
Vorab numerische Toleranzen: 0,01 USD Endvermögen, 1e-8 Prozentpunkte DD.
Gilt nur für diese drei historischen Modellkennzahlen, nicht für sämtliche Pfade
oder Zukunft. Mehr Rendite bei mehr Risiko bedeutet Zielkonflikt; ohne Nutzervorgabe
kein willkürlich gewichteter Gesamtscore/Live-Go.

## 5. Vorab feste Stabilitätsprüfungen

Alle UTC-Kalendermonate gemeinsam zeigen, Randmonate als Teilmonate markieren,
kontinuierlicher Portfoliopfad ohne Monatsreset.

Drei chronologische Abschnitte aus N zulässigen Handelskerzen, Grenzen
`floor(N/3)` und `floor(2N/3)` ohne Renditekenntnis der neuen Auswertung bestimmen.
Beiträge und Abschnitts-DD getrennt von vollständiger Pfad-DD zeigen; vollständige
Risikopeaks für Hauptkennzahlen nicht zurücksetzen.

Separat geplante Frischstarts an diesen Grenzen: nur vorheriger Marktdatenpräfix,
10.000 USD Cash, null BTC, keine geerbten Fills/Absichten. Prüft
Startzustandssensitivität; **keine unabhängigen Bestätigungen**.

Alle Monate/Drittel ausgeben, keine besten Perioden auswählen. Vorzeichenwechsel
und Konzentration auf wenige Monate/Positionszyklen kennzeichnen. Kein neues
Regimeraster nach Ergebnissichtung. Trade-Anzahl ist keine unabhängige Stichprobe.
Walk-forward kann Kausalität/Stabilität prüfen, nicht die globale Vorkenntnis
der Entwicklung rückgängig machen.

## 6. Unsicherheit und Auswahlbereinigung

**U1: bedingte Unsicherheit des festen Paars.** Nur vollständig enthaltene
UTC-Tage, erste/letzte Teilintervalle bleiben im Gesamtbericht, zählen nicht als
ganze Inferenztage. Tagesendwerte an 00:00-Schlüssen vor dortigen neuen Open-Fills:
`x_d=log(E_K(d)/E_K(d-1))-log(E_B(d)/E_B(d-1))`.
n, genaue Tagesgrenzen und ausgeschlossene Randstunden berichten.
`A_days=exp(n*mean(x))-1` bezeichnet diesen Tagesbereich, nicht A_window.

Stationärer gepaarter Blockbootstrap: 20.000 Replikate, PCG64, Seed 20260929,
14 Tage Hauptblocklänge, 7/28 Tage feste Sensitivitäten, alle drei berichten.
Erster Index gleichverteilt 0..n-1, dann mit Wahrscheinlichkeit 1/L neuer Start,
sonst zyklisch nächster Index. Gleiche Indizes für gemeinsam betrachtete Zeilen.
Quantilregel linear, NumPy-Version vor Implementierung sichern. Kein IID-Shuffle
von Fills und keine nachträgliche Blocklängenwahl.

`z_b=mean(x_b*)-mean(x)`; Basic-Intervall für mu:
`[mean(x)-q_.975(z),mean(x)-q_.025(z)]`, einseitige Untergrenze
`L_mu=mean(x)-q_.95(z)`; Transformation über `exp(n*mu)-1`.
`p_cond=(1+count[z_b>=mean(x)])/20001` an H0-Grenze 0.
**Diese Intervalle/p-Werte sind bedingt auf das aktuelle Paar und nicht um dessen
frühere Auswahl bereinigt.** Ein kleiner p_cond ist keine unabhängige Bestätigung
und kein allgemeines 5-%-Fehlerkontrollversprechen.

[Politis & Romano (1994), The Stationary Bootstrap](https://doi.org/10.1080/01621459.1994.10476870)
setzt tragfähige schwache Abhängigkeit/Stationarität voraus. Regimewechsel und lange
Haltezyklen begrenzen die Anwendung. n/L ist nur eine grobe Blocklängeneinordnung,
keine bewiesene effektive Stichprobe. Power unbekannt. Renditeresampling erzeugt
keine neuen konsistenten OHLC/Flow-Strategiepfade oder Intrabar-DD-Verteilung.
Statistikcode vor Auswertung synthetisch auf Null/Alternative/Abhängigkeit,
Konstanz/Paarung/Quantilgrenzen prüfen.

**U2: auswahlbereinigte historische Evidenz**, sofern relevante Suchfamilie
vollständig rekonstruierbar: White-Reality-Check als vorab festgelegtes
Hauptverfahren, gemeinsam resamplete tägliche Logrenditedifferenzen aller
relevanten Alternativen gegen Kontrolle, Maximum mittlerer Vorteile und
zentrierter stationärer Bootstrap nach Originalverfahren. Hansen-SPA als
studentisierte Ergänzung, kein Wechsel auf günstigeren p-Wert. 14 Tage Hauptfall,
7/28 sensitiv; vollständig geprüfte Methodenimplementierung erforderlich.

Ein signifikanter Familien-Maximumtest identifiziert zunächst mindestens eine
überlegene Alternative, **nicht automatisch E42**. Für E42-spezifische Aussagen
zusätzlich simultane E42-Grenzen oder individuelle familienweise Fehlerkontrolle
über die vollständige Familie verlangen. Kontrollauswahl, Code-/Datenänderungen
und nicht rekonstruierbare Entscheidungen ausdrücklich berücksichtigen.

Die vollständige alte Familie ist derzeit **nicht nachgewiesen**. Zwei aktuelle
Zeilen bedeuten nicht m=1 für frühere Auswahl. Holm über das heutige Paar oder
Bonferroni mit geratener Versuchszahl repariert keine fehlenden Alternativen.
Bei Lücken bleibt U2 „Auswahlbereinigung nicht belegt“. U1 und korrekte historische
Stabilitätsbefunde werden trotzdem geliefert: Ergebnisse ohne Jahreswartezeit,
mit einer Stärke der Aussage, die zu den Belegen passt.

U2 kann kausale Neuberechnungen früherer Suchalternativen benötigen. Diese sind
zusätzliche Messungen, **nicht Teil dieser Etappe-6-Designänderung**; separate
Beauftragung/Scope nötig. Alte Signalband-Renditen nicht mit korrigiertem V1
in einer Testmatrix mischen. Keine automatische neue Strategieauswahl oder
Übernahme neuerer E44.4/E44.5-Implementierungen.

## 7. Kosten, Latenz und Risikobuchführung

Gebühr immer 0,1 % je Fill. Alle Fälle gleichzeitig berichten:

| ID | Ausführung | Slippage je Seite | Rolle |
|---|---|---:|---|
| S0 | direktes Folge-Open | 0 % | idealisierte Referenz |
| S1 | direktes Folge-Open | 0,1 % | Hauptvergleich |
| S2 | direktes Folge-Open | 0,5 % | Kostenstress |
| S3 | Open i+2 | 0,1 % | eine zusätzliche volle 4h-Wartekerze |
| S4 | Open i+2 | 0,5 % | kombinierter Stress |

S0/S1/S2 auf R0 bereits reproduziert. S3/S4 und R1 geplant, nicht gemessen.
i+2 benötigt separat geprüfte Offline-Umsetzung: Absichten unverändert reserviert
bis Fill, davor keine weitere Handelsentscheidung, nur Daten sammeln; keine
stille Stornierung/Revalidierung. Je Szenario kausal neu rechnen, keine Umbuchung
fertiger Signalbänder. Kostenspielraum nur als vorab feste Diagnose, kein Retuning.

Schluss-DD plus obere/untere Intrabar-Grenze gemäß F01/F12 auf vollständigem
Bestands-/Peakpfad, einschließlich Open-Lücken und Vor-/Nachfillbewertungen zum
selben Kurs. Die obere Grenze ist kein beobachteter Verlust/VaR/künftiges Maximum.
Für verzögerte Ausführung Grenzen erneut prüfen. Stress ist kein Beleg realer
Brokerlatenz und keine Performancegarantie.

## 8. Historische Verfügbarkeit und Revision

Reproduzierbare später heruntergeladene Werte beweisen keine Verfügbarkeit am
alten Kerzenschluss. Manifest je verwendetes Feld: Quelle/Börse/Paar,
UTC-Zuordnung, Transformation, Hash, erste belegbare Verfügbarkeit, Revision,
fehlende Vintages.

„As-of belegt“ nur bei rechtzeitig verfügbarer verwendeter Version.
„Verfügbarkeit idealisiert/unbekannt“ erlaubt bedingten Modellvergleich, keine
Behauptung erreichbarer Live-Fills. Daten-/Kausalitätsfehler wie Lücken,
Zukunftswerte, falsche Zuordnung oder stiller Quellenwechsel sperren das Paket.

Fehlende Vintages nicht erfinden. Null-Latenz-Folge-Open bleibt Benchmark unter
Schlussverfügbarkeit; auch vier Stunden extra beweisen ohne Zeitbelege keine
ausreichende reale Liefer-/Menschen-/Brokerlatenz. In dieser Designänderung keine
laufende Sammlung/Automation, neue Marktdatenabfrage oder Live-Änderung.
R1-Beschaffung ist separat geplant.

## 9. Ergebnisformen und vorhandener Befund

Ausgeben: Wirkung, Dominanz/Zielkonflikt, Zeitstabilität, Kosten/Latenz,
bedingte Unsicherheit, Auswahlbereinigungsstatus, Verfügbarkeitsstatus.
Unpräzise/widersprüchliche Evidenz bleibt unentschieden. Fehlende Inferenzannahmen
löschen keine korrekte historische Buchführung, begrenzen deren Verallgemeinerung.

Bereits bekannt aus gesicherten R0-Läufen, **keine neue Messung**:

| Slippage | E42 minus Basis Endwert USD | Schluss-DD-Differenz pp | obere Intrabar-Differenz pp |
|---|---:|---:|---:|
| 0 % | -118,99 | +0,5010 | 0,0000 |
| 0,1 % | -174,48 | +0,5646 | +0,3009 |
| 0,5 % | -348,03 | +1,0519 | +1,0447 |

Die Basis dominiert E42 für diese drei vollständigen R0-Szenarien in den drei
genannten Kennzahlen. Das ist ein historischer Modellbefund, kein Zukunftsbeweis
und kein Ergebnis bis 29.09. Quelle: unabhängig geprüftes `6-ergebnis.json`.
Kein Herbeiführen eines positiven Vorteils durch Änderung der Kriterien.

## 10. Aufgelöste alte Fragen und getrennte Umsetzung

D6-A: Jahresfenster ausdrücklich verworfen; rückblickende Prüfung bis festem
aktuellen Stichtag gemäß Nutzerauftrag. D6-B: unbegründete 2-%-Nutzenhürde
zurückgezogen. D6-C: unbegründete 15/20/+2-DD-Budgets zurückgezogen.
Keine erneute Zustimmung zu diesen alten Vorschlägen erforderlich.

Version 1 bleibt im Commit `efc3b1a7160801df2642f7f222eebd399face8b8`
nachvollziehbar; seine Sicherung unverändert. Offen: R1-Paket/Quellenmanifest,
Statistikcode/synthetische Prüfung, separate i+2-Umsetzung und Suchhistorieninventar.
Fehlende volle Auswahlbereinigung verhindert keine sachliche beschreibende Prüfung.
Keine neuen Kandidatenmessungen oder automatische Folgeetappe durch diesen Entwurf.

F13/F17 unverändert. V1-Fills simuliert, historische Signalbänder Diagnostik,
manueller Bestand unbekannt. F13-ID lokale Versandidentität, kein Telegram-
Idempotenzschlüssel; uncertain blockiert, bestätigte/unklare Sendungen nicht
wiederholen, kein Reset/Exactly-once. Ephemerer Runnerverlust vor Git-Persistenz
separat offen. Keine Telegram-/Broker-Aufrufe, Orders, Deployments, Live-Schalter,
Backtest-Dispatches oder main-Push/Merges. V2/Shorts/E41.6/andere Befunde getrennt.
**Kein Live-Go.** Primärquellen geprüft 29.09.2026.
