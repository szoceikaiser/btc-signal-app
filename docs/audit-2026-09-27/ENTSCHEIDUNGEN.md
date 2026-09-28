# Rekonstruktion sämtlicher dokumentierter Strategieentscheidungen

Stand 28.09.2026. **Historische Zahlen in dieser Datei sind rekonstruierte damalige Aussagen**, soweit nicht ausdrücklich „Audit“ davor steht. Für E44.5 gelang das originale Replay. Für ältere Renditeläufe fehlen vollständige ursprüngliche Eingaben; ihre Ergebnisse dürfen deshalb nicht als unabhängig reproduziert gelten. Softwareprüfungen und heutige Neuberechnungen sind davon getrennt.

Das Verzeichnis besteht aus drei zusammengehörigen Teilen:

- Nachstehende Chronik sämtlicher dokumentierter Etappen und Entscheidungen einschließlich verworfener/nicht gebauter Ideen.
- [PARAMETER.md](PARAMETER.md): alle 45 aktuellen Handelsparameter mit Zweck, Herkunft, Code-Default, wirklichem Live-Wert, neuer Gegenprobe, weiteren Daten-/Anzeigeschaltern, festen Größen und **allen 85 alten Gitterzeilen mit ihren tatsächlichen Unterschieden zur heutigen Basis**.
- [HISTORISCHE-BELEGE.md](HISTORISCHE-BELEGE.md) und [historie.json](historie.json): 80 verschiedene Berichtstände, deren vollständige Tabellen, Beleg-Commits und 38 Konfigurationsrevisionen. Letztere umfassen auch Kommentaränderungen und sind nicht 38 Aktivierungen.

`H` = historische Rendite-/Nachlaufmessung, `S` = Software-/Funktionsprüfung,
`L` = dokumentierte echte Betriebsbeobachtung. Ein `L` belegt beispielsweise eine
zugestellte Nachricht oder veraltete Webseite, **keine geprüfte Kontorendite**.
Für tatsächliche Trades wurden keine vollständigen Brokerabrechnungen gefunden.

## Fenster und ursprüngliche Vergleichsbasen

| Kürzel | Fenster laut damaligen Berichten | Wesentliche Grenze |
|---|---|---|
| W0 | 01.09.2025–30.04.2026, Berichte 22.–24.07. | OI/Futures-Flow teilweise Ersatzdaten; Triggerabgleich, nicht vollständige Furkan-Handelsakte |
| W1 | 17.11.2025–01.05.2026, 26.07.; ab 27.07. 18.11.2025–27.07.2026 | „Voll-Daten“ startet mit vorhandenem OI; wechselnde Anfangsdaten, Rohantworten fehlen |
| W2 | 19.11.2025–28.07.2026 | spätere Juliläufe rollen Anfang und Ende weiter |
| W3 | 19.12.2025–27.08.2026 | ältere Codebasis vor no_flip/Neustart/Zonennachzug/Rückeroberung/Beinrichtung |
| W4 | 20.12.2025–28.08.2026 | innerhalb des Tages mehrere Code-/DD-Änderungen; nicht eine unveränderte Messung |
| W5 | 28.12.2025–05.09.2026; am Folgetag 29.12.–06.09. | Beim Tagesvergleich ändern sich **beide** Fensterränder |
| W6 | 05.01.–13.09.2026 | Tageszonen/EMA/Ampel vor E41/E43.2 |
| W7 | 11.01.–19.09.; 12.01.–20.09.; 13.01.–21.09.2026 | Aggregation/Muster 5/Stop/STH; verschiedene Messläufe |
| W8 | 15.01.–23.09.2026 | E41 aktiv, Beinrichtung noch auto |
| W9 | 18.01.–26.09.2026 | mehrere Läufe vor/nach Beinrichtung bias; exakten Basisnamen beachten |
| W10 | 18.01.–27.09.2026 | Original-E44.5 einschließlich unfertiger letzter Kerze; vollständige abgeleitete Eingaben vorhanden |
| Audit | 18.01.–27.09.2026 bis zum Schluss 08:00 UTC | nur abgeschlossene Kerzen; 10.08.2025–18.01.2026 zusätzlich als Indikator-Vorlauf; F09 separat korrigiert |

Die präzisen Tagesstände und Tabellen jedes archivierten Berichts sind im Belegindex
verlinkt. Vor E27 beziehen sich Drawdowns teilweise nur auf Signalzeitpunkte. Auch
nach E27 verbleibt F01. Ein alter Risikoabstand ist somit nicht unbesehen verwendbar.

## Chronik E1–E22

Hauptquelle dieser Etappen: [ETAPPENPLAN.md](../ETAPPENPLAN.md), ergänzt durch die
dort verlinkten Pläne, `config.json`-Hinweise und die jeweiligen Git-Berichte.

| Etappe / Zweck | Art, ursprüngliche Basis und Fenster | Damaliger Befund / Entscheidungsregel | Entscheidung und unabhängige Einordnung |
|---|---|---|---|
| E1 Regeln aus Furkan ableiten | S/Quellen; keine Renditebasis | Fibonacci, Bestätigung, Stop, Stufenkäufe formalisiert | Grundformeln nachvollziehbar. Feste 4h, n=5, Prozenttranchen und numerische Musterschwellen sind zusätzliche Entwicklerregeln. Kein vollständiges Abbild der Originalstrategie. |
| E2 notierte Kauf-/Verkaufstage gegen Markt prüfen | H, manuelle Datenlisten; keine Größen/Ausführungen | Datumsnähe und Marktverlauf; teilweise Tief der Folgewoche | Nur rückblickende Plausibilität. Echte Furkan-Rendite und damals erreichbare Preise nicht belegt. Doppelte Tage und Kauf/Short-Deckung dürfen nicht als unabhängige Trades zählen. |
| E3–E7 Engine, Webseite, Automatisierung, Telegram | S, teilweise L; Demo-/Funktionsfälle | Ausgabe, Persistenz, Verbindung; dokumentierte API-451-Ausfälle und Kraken-Ersatz | Betrieb nachgewiesen, kein Renditenachweis. Der Audit versendet nichts. Aktuell F05/F10/F13 und Datenqualitätsgrenzen. |
| E4 Pivot-/ATR-Kalibrierung | H, 8 Kombinationen n=3…6 und k=2/3, W0 | n=5/k=2: etwa 45 % Recall, 54 % Präzision; Ziel ≥70 % nicht erreicht | Gewählt als Datumsnäherung. Die Ziele waren nicht Nettorendite oder unabhängige Vorhersagekraft; ±1 Tag erlaubt viel Zufall. Audit S000–S007: vollständiges altes 4×2-Gitter auf heutiger Basis, keine Reproduktion der alten Kalibrierung; kein robuster Vorteil beider Hälften. |
| E8.1 Kapitulation/Flush | H, frühere Long+Short-Basis, W0, teilweise ohne echtes OI | Ohne Flush ca. −6 %, T1 ca. −8,7 %, Core ca. −9,8 % | Damals zunächst aus. Gilt nicht gegen heutige Basis; E9 führte auf neuer Datenbasis zum gegenteiligen Ergebnis. |
| E8.2/3/4 Zwischenverkäufe und Bestätigung | H/S, W0 | Leiter 0,8/0,9 mit 15-%-Tranchen etwa −5,3 % statt −6 %; Recall kaum verändert | Leiter aktiv, gewählte Größen sind Setzungen. Softwaretests prüfen die gewählte Mechanik, keinen statistisch gesicherten Mehrertrag. |
| E8.5 nur Long | H, bisher Long+Short, W0 | ungefähr +2,5 % statt −5,3 % | Long-only aktiv. Heutiger Short-Vergleich durch F02 nicht als unverschuldete Anlagebilanz interpretierbar. „Shorts generell ungeeignet“ folgt daraus nicht. |
| E8.5 Trend/strenge Bestätigung/Konfluenz | H, Long-only +2,5 %, W0 | EMA etwa −3,1 %, Konfluenz +2,9 % mit weniger Signalen, strenge Variante teils ohne Wirkung bei Ersatzdaten | Filter aus. Diese frühe Basis ist überholt; aktuelle gemeinsame Proben erfassen die vorhandenen Regeln. |
| E8.5 KI-Makro-Bias | Plan, keine Messung; [PLAN-E8.5](../../PLAN-E8.5-KI-MAKRO-BIAS.md) | Rückwirkende LLM-Beurteilung wegen möglichem Ausgangswissen nicht belastbar | Pausiert/nicht gebaut. Kein Beleg gegen zeitpunktgerecht protokollierte Makrosignale generell. |
| E9.1/2 OI und tatsächliche Liquidationen | S/H, Ersatz-OI → Coinalyze-Binance, W1 | Muster wurden erstmals mit echter OI-Zeitreihe bewertbar | Datenpfad aktiv bei verfügbarem API-Zugriff. Quellen-/Ausfallabhängigkeit ist kein Konfigurationsschalter und muss je Lauf archiviert werden. |
| E9.3 bedingter Stop mit Nachkauf | H, damalige Basis +12,3 %, W1 | etwa +9,2 %; zusammen mit Flush ca. +33,1 statt +33,5 % | Aus. Größeres Risiko durch spätere Invalidierung. Aktuelle Einzelprobe eingeschlossen; nicht identisch mit E41-Warten ohne Nachkauf. |
| E9.4–7 vollständiger Datenbereich/Portfoliomessung/Flush-Core | H/S, W1 | Voll-Daten-Fenster statt künstlich neutralem OI; Flush-Core wurde vorteilhaft | Core aktiv. Neue Datenbasis erklärt, warum E8-Ablehnung nicht übertragbar war. „Voll-Daten“ garantiert weder damalige Publikationszeit noch unveränderte Daten. |
| E9.8 Kaufleiter | H, damalige Long/Flush-Basis, W1 | ca. +18,0 statt +9,8 % | Aktiv. Im Audit einzeln und mit Flush/Liquidationsaufstockung aus-/eingeschaltet (G4). Keine einheitliche Stoprisiko-Skalierung. |
| E9.9 alten Rest freigeben | H, Buy-ladder/Trail-Basis; spätere alte Zeile +22,2 %, DD −13,0 % | Verkauf bei neuer Struktur, um neue Einstiege zu ermöglichen | Aus; E21/E26 adressieren das Problem anders. E43.8 prüfte später erneut gegen aktuelle Basis. |
| E9.10 Stop nach Teilgewinn nachziehen | H/S, W1 | Einstands-/Pivotstop nach realisiertem Teilverkauf | Aktiv. F03 beweist, dass die berechnete Stoplinie wieder sinken kann; F04, dass der Einstand falsch gewichtet ist. Im aktuellen Datensatz wirkt das Abschalten nicht auf die Rendite. Das beweist keine korrekte Implementierung. |
| E9.11 Liquidationsverkäufe spike/zone/both | H, Buy-ladder/Trail-Basis, W1 | Keiner der geprüften Ausstiege überzeugte | Alle aus; alte Ablehnungen nur für damalige Basis. Heutige Einzelproben enthalten alle drei Werte. Bereits ausgelöste Liquidationen sind keine Karte offener Liquidität. |
| E10 Cashreserve 100/60/50 % | H, damalige Basis, W1 | +30,0 / +17,9 / +14,8 % | 100 % Modellkapital gewählt. Niedrigere Roh-Rendite widerlegt keine vernünftige Risikoreduktion. Auf heutiger Basis neu: [KAPITAL.md](KAPITAL.md), +36,13 / +31,19 / +26,14 %. |
| E10 Verkauf am alten Hoch | H, alte Basis, W1 | zunächst etwa −2,8 Punkte gegenüber Basis | Zunächst aus; **durch E14 überholt**. Das ist ein belegtes Beispiel, warum einzelne frühere Ablehnungen nicht endgültig sind. |
| E10 Liquidations-Einstieg boost/filter | H, alte Basis, W1 | Boost zunächst ohne Renditewirkung trotz 19 Signalen wegen fehlendem Cash; Filter +22,5 statt +29,8 % | Zunächst nicht gewählt; Boost später mit Mindeststop sinnvoller. Die Signalzahl misst keine ausgeführten Käufe. |
| E11 halbes Fenster / Rangvergleich | H, W1: ungefähr 18.11.–24.03. und 24.03.–27.07. | Schnittmenge der Top-5, Interpretation anhand 25/N | Keine unabhängige Validierung: Parameter wurden schon mit beiden Hälften entwickelt. 25/N unterstellt unabhängige, gleichverteilte Ranglisten; die Varianten sind stark korreliert. |
| E12 Verlust- und Reset-Prüfung | S/H, [Verlustanalyse](../VERLUST-ANALYSE-2026-07-27.md) | Nicht zurückgesetzte Zähler verfälschten wiederholte Positionen; pro Teilverkauf gezählte „Gewinntrades“ überhöhten Positions-Trefferquote | Reset repariert, frühere Hebel neu gemessen. Behauptung „Strategie gut“ war stärker als die Belege. 77 % profitable Teilverkäufe waren nicht 77 % profitable Gesamtpositionen. |
| E13 Filter/Bestätigung/Wartezeit | H, LIVE+Trail etwa +32,2 %, W2 | Abverkaufssperre ~30 %, confirm_t1 ~27,6 %, 48h-Wartezeit ~33,9 %, DD teils geringer; Rangfolge H1/H2 wechselte | Nicht gewählt. Spätere alte Gitterzeilen zeigten andere Vorzeichen; deshalb E43.6-Nachmessung. Ein Rangwechsel beweist für sich weder Zufall noch das Gegenteil. |
| E13 Mindeststop 2 % | H, +32,2 %-Basis, W2 | +33,0 %, DD etwa −7 statt −12,3 % nach damaliger DD-Formel; H1 +0,9, H2 −2,4 Punkte | Aktiv wegen Risikoabwägung, nicht weil beide Hälften gewinnen. Alte DD-Zahlen vor E27 und heutiger F01 begrenzen das Argument. |
| E13 Mindeststop × Liquidations-Boost | H, gleiche vier Ecken, W2 | Boost allein ~37 %, Mindeststop+Boost ~39,1 %, Basis ~32,2 % | Kombination aktiv. Tatsächlich untersuchte Wechselwirkung, keine bloße Einzelannahme. Heutige G4-/Einzelproben enthalten die Mechanismen. |
| E14 Hochverkauf auf neuer Basis | H, Mindeststop+Boost +39,1 %, W2 | high_exit +40,3 %, DD −7,5 statt −6,9; Liquidationsverkauf ~33,8, beide ~30,7 % | high_exit aktiv, Liquidationsausstiege aus. Frühe high_exit-Ablehnung E10 ausdrücklich überholt. Neue G2 zeigt bisher nicht gemessene Interaktion mit E42. |
| E15 hypothetische Furkan-Bilanz | H, unvollständige Notizen, Größenannahmen | 12 Szenarien; kurzes Fenster 19.11.–22.04. −9,2 bis +0,5 %, langes 09/2025–22.04. −23,7 bis −6,1 % | Keine tatsächliche Furkan-Rendite. Größen, Instrument, Finanzierung und Ausführungen fehlen. Ein Vergleich „Engine schlägt Furkan“ ist nicht zulässig. |
| E16 Futures-CVD/Long-Anteil | H/S, +40,3 %-Basis, W2 | echte Futures-Deltas statt Ersatz, etwa +41,5 %; Long-Anteil zusätzlich gesammelt | Futures-Datenweg übernommen, Long-Anteil ohne eigene Handelsregel. Ein kleiner Effekt widerlegt den Nutzen besserer Daten nicht allgemein. |
| E17 Vorschau, Planbarkeit, Flush-Wache | S/L/H, folgende Juliläufe | 61 von 214 Signalpreisen verschieden vom Schluss; Warnung für laufende Kerze | Anzeigen aktiv. Frühere Level lassen sich nur dann als Limit handeln, wenn alle Voraussetzungen schon vorher bekannt waren. F12 widerlegt pauschale Gleichsetzung mit realer Ausführung. |
| E18.1 Konfiguration durchreichen | S, [Plan E18](../PLAN-E18-MECHANIK-FIXES.md) | Mehrere Schlüssel kamen live nicht an; zentraler Durchreich-Test | Reparatur übernommen. Heutige normale Werte stimmen; Zeichenkette false wird trotzdem zu true (F11). |
| E18.2 no_flip und E18.3 Ziele einfrieren | H/S, W3, damalige Basis ca. +35,5 % | no_flip ~31,4 %, freeze ~29,9 %, gemeinsam ~34 % | Zunächst aus. Gleichkerzen-Reihenfolge bleibt eine Modellentscheidung; später E25 no_flip aus Bedienungsgründen aktiv. freeze bleibt aus. |
| E19 Mindestbein, Auswahl, Richtung, Break-even | H, W3, Basis +35,4 % | Mindestbein +37,4 %, Richtung bias +32,6 %, Kombination +38,6 %, größtes Bein +17,6 %, be_im_plus +15,9 % | min_bein 5 % aktiv, übrige damals aus. **Beinrichtung-Ablehnung durch E43.2 überholt.** be_im_plus bildet Furkans „bereits Gewinne realisiert“ nicht ab. |
| E20 Gegenbein-Widerstand / Positionsplan | H/S, W3, Basis +37,9 % | Widerstand zusätzlich +30,4 %, statt high_exit +33,0 %; DD −6,2/−6,8 statt −6,9 % | widerstand_exit aus, Plan/Anzeige an. Fehlendes Persistenzfeld F05 verhindert verlässlichen Live-Vergleich bei Aktivierung; Planstop weicht ab (F10). |
| E21 Rest halten × Neustart | H/S, W3, Basis +37,9 % | Rest allein +18,9 %, Neustart +39,0 %, beide +39,4 %; noch ohne no_flip | Vollständiges kleines Zusammenspiel bereits gemessen. Rest blockiert ohne Neustart weitere Einstiege. Nicht einfach gegen heutige +36,13 % halten. |
| E22 Markt-Beteiligung | H/S, W3, Monatsvergleich | Aufwärtsmonate summiert +48,3 % BTC/+23,4 % Engine; Abwärts −52,0/+9,9 % | Anzeige, kein Handelsschalter. Summierte Monatsrenditen sind keine Vermögensentwicklung. Verhältnis wird nahe null instabil; Kapitalbindung und Kosten getrennt betrachten. |

## Chronik E23–E44.6

| Etappe / Zweck | Art, ursprüngliche Basis und Fenster | Damaliger Befund / Entscheidungsregel | Entscheidung und unabhängige Einordnung |
|---|---|---|---|
| E23 zusätzliche Tageszonen | H/S, W4, Basis +37,9 %, DD −6,9 | +23,4 %, DD −17,6; H1 +27,0 vs +26,4, H2 −2,9 vs +9,1; Gegenprobe ohne Mindestbein +26,5 % | Aus. Andere Stops bei gleicher Kapitaltranche vermischen Signalqualität und Risiko. Vorabrechnung auf anderem Fenster ist keine Reproduktion. |
| E24 Chart/Plan und Einstand | S/L, [Plan E24](../PLAN-E24-CHART-UND-PLAN.md) | Fehlende Planmarken im Chart, Einstand versus einzelner K1 verwechselt | Chart liest state.plan; lokaler Anzeigeumschalter. F04 betrifft auch den dargestellten Einstand, F10 den gemeinsamen Planstop. Geteilte Datenquelle kann einen gemeinsamen Fehler verbreiten. |
| E25 no_flip | H/S/Nutzerpräferenz, W4, Basis +37,3 %, 16 Gegengeschäftskerzen | +34,2 %, 0 Gegengeschäfte, DD −7,1 statt −6,9; H1 −3,3, H2 +0,3 Punkte | Aktiv auf Wunsch. Praktische Konsistenzentscheidung, kein belegter Renditegewinn. Dass Kauf/Verkauf netto zusammenfallen, macht sie nicht physikalisch unmöglich; Reihenfolge und reale Auftragsausführung sind die offene Frage. |
| E26 Neustart mit Rest auf no_flip-Basis | H/S, W4, Basis +34,5 % | +36,6 %, gleiche alte DD-Zahl; nur drei Neustarts, Vorteil aus zwei Fällen | Aktiv als Konstruktionsentscheidung. Drei Ereignisse tragen keinen allgemeinen Renditenachweis; „kostet nichts“ gilt nur für gemessenen Pfad. |
| E26 Rest halten × Neustart auf neuer Basis | H, W4 | +35,7 %, zunächst DD −8,2 statt −7,1; nach E27 DD −9,8 statt −9,4, Return +34,0 statt +34,9 | Rest aus. Ursprüngliches Risikoargument wurde bereits im Projekt korrigiert. Audit F09 ändert die Buchung erneut. |
| E27 DD zwischen Signalen und an Kerzentiefs | S/H, W4 | Live DD −7,1 → −9,4 %, Median 52 Varianten −9,9 % | Richtige grundsätzliche Korrektur. F01: Positionsstand nach den Trades wird noch immer für die ganze aktuelle Kerze verwendet; Reihenfolge von Hoch/Tief ungesichert. |
| E28 Break-even nach Aufstockung | S/Plan, [Plan E28](../PLAN-E28-BREAKEVEN-NACH-AUFSTOCKUNG.md) | gebaut und vor Push vollständig zurückgenommen; keine tragende Renditemessung | Expliziter Nutzerwunsch, manuell entscheiden. Nicht live. Keine Wiederaufnahme im Audit; trail_stop ist ein anderer Mechanismus. |
| E29 MVRV-Z | Recherche/Plan, W4; wenige bekannte Werte | ~0,24–0,42; klassische 0/7-Schwellen nicht berührt | Nicht gebaut. Kein aussagekräftiger Test einer zyklischen On-Chain-Regel. Kostenbasis/Valuezone sind zudem nicht dasselbe wie MVRV-Z. |
| E30 Zonen nachziehen | H/S, W5 | zunächst +37,2 vs +36,2, nach zusätzlicher no_flip-Reparatur +36,4 vs +36,3, DD gleich −9,7; Folgetag +36,1 vs +37,1 | Aktiv als strukturelle Entscheidung, nicht Renditebeweis. Zwei bewegte Fensterränder und Pfadänderung: kein wissenschaftlicher Nachweis einer universellen 1-Punkt-Rauschgrenze. |
| E30 Pages-Aktualisierung | L/S, 05.09. | Webseite acht Tage alt, weil Workflow-Push keinen Push-Folgeworkflow auslöste | workflow_run ergänzt. Heute unbeschränkter Folgeauslöser auch nach Backtest auf fremdem Zweig: im Audit deshalb kein gewöhnlicher Backtest-Workflow gestartet. |
| E31 Wissens-Layer und falsch benannte Vergleichsbasis | S/Dokumentation | „ohne Flush“ hatte zwischenzeitlich vier Unterschiede zu live; korrigiert | Positiver Regressionstest. Alte Namen bleiben trotzdem gefährlich: heute sind nur 23 von 85 Gitterzeilen echte Einzelabweichungen und eine identisch; 61 unterscheiden sich mehrfach. |
| E32.1 Lageanzeige und E32.2 Wechselmeldung | S, [Plan E32](../PLAN-E32-LAGEZEILE.md) | Struktur/Spot/Muster in Plan; Wechselmeldung offen | Anzeige aktiv, keine zusätzliche Handelshandlung. Nachträgliche Begriffe wie „Short-Wetten“ sind Interpretation, keine eindeutig identifizierten Kontopositionen. |
| E32.3 Tages-Pivotweiten 5/8/12 | H, W6, Basis +31,4 %, DD −9,7 | n8 +5,5 %, DD −22,9; n5 +21,6, n12 +6,4 | Aus. Heutige abhängige Gegenproben V075/V076 prüfen n8/12 mit aktivierter Tagesebene. Nur n ändern, während zonen_1d aus ist, wäre keine echte Probe. |
| E33 Tagestrend EMA200/50 | H/S, W6, Basis +30,9 % | EMA200 −0,4 %, EMA50 +4,7 %, starke Signalreduktion; zu kurze EMA-Historie repariert | Filter aus, Anzeige an. Ein misslungener Eintrittsfilter widerlegt keinen übergeordneten Trendansatz generell; F08 betrifft unfertigen Tag. |
| E34 Ampel klein/gross/immer | H/S, W6, Basis +30,9 % | +26,6 / +26,4 / +19,0 %; H2 umgekehrte Ampel besser | Filter aus, Anzeige an. Gute Gegenprobe; ähnliche Gesamtrenditen beweisen nicht, dass sämtliche Eingaben informationslos sind. Seit E38 zählt Muster 5 neutral, deshalb unterscheiden sich Regelversionen. |
| E35 Lage auf Abruf | S/L, [Plan E35](../PLAN-E35-LAGE-ABRUF.md) | Kontext unabhängig vom Engine-Positionsstand, Ampelrichtung korrigiert | Anzeige an/auf Abruf. Kein Replay menschlicher Handlungen. Keine Nachricht im Audit ausgelöst. |
| E36 Order-Flow-Rohwerte | S/L, [Plan E36](../PLAN-E36-ORDERFLOW-ROHWERTE.md) | Zahlen/Umbruch/Quellenausfälle geprüft; zwischenzeitlich Tests nicht zuverlässig sichtbar | Anzeige aktiv. E43.1 korrigiert Futures-Einheit. Ein Zahlenblock ist nicht automatisch unabhängig bestätigte Information. |
| E37 Spot größter Markt/alle Dollar-Märkte | H/S, W7, 19.09., Basis +23,5 %, DD −9,4 | +20,9 / +21,3 %, DD beide −8,2; Coinbase-Auswahl von kleinem USDT zu großem USD korrigiert | Nicht live übernommen. Einheiten/Börsenauswahl wichtig; heutige F14/F15 zeigen zusätzliche Lücken. Kein Beweis gegen Mehrbörsendaten generell. |
| E37 Futures-CVD/OI/Funding/Liquidationen einzeln und zusammen | H/S, W7, neun Datenvarianten | Keine erfüllt ≥1 Punkt je Hälfte; OI etwa +0,6/+1,0, Funding deutlich schwächer | Alte Aussage „keine in beiden besser“ war zu stark und wurde im Projekt korrigiert. Basis vor E41/E43.2; Originalreihen fehlen. Neue Performance-Reproduktion daher nicht möglich. |
| E38 Muster 5: Kerzen und Episoden | H, W7, 20.09. | 45 Kerzen/26 Episoden; anfängliche Trefferquote und p≈0,5 % vermischten Zählebenen; spätere Episodenrechnung ergänzt | Nachlauf ist kein Handelsertrag. Auch getrennte Episoden haben überlappende 1/2/4-Tage-Zukunftsfenster; Unabhängigkeit nicht bewiesen. |
| E38 muster5_entry, Halten leiter/alle, Sperre | H/S, W7 | Haltevarianten berühren keine relevanten Verkäufe; Einstiegsvariante fünf zusätzliche Bestätigungen, ca. +1,4 Punkte nur H2 | Handelsschalter aus, erklärende Anzeige aktiv. Null effektive Ereignisse widerlegen einen Mechanismus nicht. Audit Einzelproben erneuert; keine Optimierung der Musterschwellen. |
| E39 Verlauf nach Stop | H, W7, 21.09., zehn Stops der Live-Basis | Median Schluss 0,28 % unter Marke; 9/10 nach zwei Tagen wieder darüber; behauptete 1,1-%-Zufallszahl | Kleine abhängige Stichprobe, ausgewählter Horizont, Stops bereits nach Kursfall selektiert. Kein zulässiger Beweis, Stops abzuschalten oder Verluste auszusitzen. |
| E40 STH-Kostenbasis | H/S, W7 | Preis 84 % der Zeit darunter; 90/108 Käufe darunter, sieben Kreuzungen; zwei Anbieter | Anzeige an, kein Filter gebaut. Historische Veröffentlichung/Revision und 150/155-Tage-Definition offen. 84 % Dominanz allein beweist keine Nutzlosigkeit. |
| E41 Puffer 0,5 %, Rückeroberung 1/3, Dochtstop | H/S, W7, Basis +23,5 %, DD −9,4 | 1 Kerze +26,4 %, H1 +2,6/H2 +0,2 Punkte, DD −10,3; 1/3/Puffer bestanden damalige Regel >0 je Hälfte, DD höchstens 1 Punkt schlechter | 1 Kerze auf Wunsch aktiv, Puffer/3 nur Gegenproben, Docht aus. Die damalige Einschaltregel hatte **keine** 1-Punkt-Rauschgrenze je Hälfte. |
| E41 Ausschaltregel überschrieben | H/Nutzerentscheidung, W8 | +25,2 vs +22,6 %, aber DD −10,9 vs −9,4: Grenze 1 Punkt verletzt | Nutzer ließ aktiv; kein automatischer Regelvollzug. W9 nach Beinrichtung bias DD gleich, Hälften +4,0/+0,2. Alter Abschaltbefund ist basenabhängig; F01 begrenzt sämtliche DD-Abwägungen. |
| E41.6 pfadunabhängiger Stopvergleich | Plan | vorgeschlagen, nicht gebaut | Gesamtpfad bleibt relevant; zusätzlich identische Startposition je Stopereignis vergleichen. Audit erklärt direkte/indirekte Effekte bei E42, liefert keine historische E41.6-Reproduktion. |
| E42 Vorschlag des Nutzers | Regel/Plan, [E41](../PLAN-E41-STOP.md), [E44](../PLAN-E44-KOMBINATIONEN.md) | Ausbruch und gehaltener Rücktest als Rückkauf; kein eigener damaliger Messlauf | In E44.3 gebaut. Keine automatische Ableitung aus der rückblickenden STH-Aussage im Furkan-Video. |
| E43.1 Futures-CVD-Anzeige in USD | S, W9 | BTC fälschlich als Dollar angezeigt; historische Delta-Umrechnung je Kerze | Anzeige korrigiert. Richtige Einheiten sind keine neue Alpha-Hypothese und brauchen keinen Renditesieg. |
| E43.2 Bein in Handelsrichtung | H/S, W9, alte live-Basis auto +25,2 % | bias ~35,4 %; Hälften +3,6/+5,2 Punkte, DD 1 Punkt flacher; Regel ≥1 je Hälfte und DD-Toleranz | Seit 26.09. live bias. Ein starkes Ergebnis im Entwicklungsfenster, kein unabhängiger Zukunftstest. Genau dieselbe Idee war E19 auf anderer Basis verworfen. |
| E43.3 Muster 2 in lokalen USD-Deltas | H/S, W9, Basis +35,3 % | nur 2/1504 Musterkerzen anders; Rendite/Hälften/Signale gleich, ≥1-Regel verfehlt | Handel bleibt alt. F06 bestätigt den Nullpunktfehler unabhängig. Kein Renditeunterschied rechtfertigt nicht den fehlerhaften Messbegriff. |
| E43.4 OI in Kontrakten | H/S, W9, Basis +35,4 % | 210/1504 Musterkerzen anders, 227 statt 244 Signale, Rendite gleich | Handel bleibt USD. Neue G5: gleiche Portfoliorendite trotz Klassifikationsunterschieden. USD-OI und Preis sind keine unabhängigen Informationen über neue Kontrakte. |
| E43.4b OI-Anzeige | S | Kontraktveränderung zusätzlich zum Dollarstand | Anzeige übernommen, Handelsmuster unverändert. Quellenkonvention muss für jeden Anbieter erhalten bleiben. |
| E43.5 Test auf Historienlänge / A5 | S/H, W9 | früherer Test erreichte Muster 2 nicht; nachgebessert. 53/1177 andere mögliche Pivots; high_exit_hist=live ohne Signal-/Renditeeffekt | high_exit_hist bleibt voll. Audit: volles Präfix, rollende 1300 Kerzen und persistierter Neustart erzeugen gleiche tatsächliche Signale in diesem Fenster. Prinzipielle Fensterabhängigkeit bleibt. |
| E43.6 Rest/strict/T1/cooldown erneut | H, W9, Basis +35,3 % | Rest +34,5, Hälften −4,3/+3,2; strict +28,5 (+2,4/−7,6); T1 +34,9 (−0,8/+0,9); cooldown +33,4 (−1,8/0) | Alle aus nach ≥1 je Hälfte. Diese Ablehnungen sind relativ aktuell; heutige gemeinsame Wiederholung und F09-Korrektur getrennt in KOMBINATIONEN. |
| E43.7 Wissens-Korrekturen | Dokumentation | sechs zu starke/überholte Aussagen eingegrenzt | Positiv; kein neuer Handels- oder Renditetest. Weitere Überdehnungen nennt dieser Audit. |
| E43.8 be_im_plus und release_stale_rest erneut | H, W9, Basis +35,3 % | be +18,0 %, Hälften −15,5/+0,5; Freigabe +34,6 (−1,1/0) | Beide aus; neue Einzelproben auf gemeinsamer Basis vorhanden. be_im_plus bleibt eine andere Regel als E28/trail_stop. |
| E44.1 Archiv | S, seit 26.09. in main | alte Coinalyze-Zeitpunkte behalten, frische Werte gewinnen | Hilfreich, aber kein unveränderliches Archiv des damaligen Wissens. Empfangs-/Publikationszeiten und frühere Versionen fehlen. |
| E44.2 Wechselwirkungen/Monatsprobe | S/H, W9 | 16 frühere 2×2-Gruppen aus altem Gitter extrahiert | Tatsächlich untersuchte Kombinationen dokumentiert. Aussagen „zwei Filter schaden immer“ oder „Stops sind kein Hebel“ sind daraus nicht ableitbar. |
| E44.3 E42 implementieren | S, main 5a50fd8 | 25 % Rückkauf; 0,5-%-Zone, 12 Kerzen; eigener Teilstop, Persistenz/Telegram; Default false | Code in main, **Schalter aus**. Audit rekonstruiert 57 Beobachtungen, 33 Ausbrüche, 16 Rückkäufe, alle Abgänge und den Gesamtpfad. |
| E44.4 kleinere Teilverkäufe | S, Zweig eeb4eea | Faktor 1/0,67, zwölf neue Tests; 14 Mutationen | Nur Zweig, Default 1; damals noch keine Renditemessung. Keine Live-Aktivierung durch Vorhandensein von Code. |
| E44.5 acht Kombinationen plus Frist 6 | H/S, W10, ursprüngliche Live-Basis +36,14 % | E42 +35,93 %, H1 +1,76/H2 −1,71 Punkte, DD gleich, Monatsprobe −0,83. E42 ≥1, erklärende Kombinationen ≥2 je Hälfte, DD höchstens 1 schlechter, Monatsvorteil stets positiv | Originales Replay gelingt. **Keine Zeile besteht**. F09 verändert einzelne korrigierte Renditen um bis zu 1,30 Punkte; D01 entfernt laufende Kerze. Urteil „keine Aktivierung belegt“ bleibt, Zahlen sind nicht unverändert belastbar. |
| E44.6 Shorts im Abwärts-Regime | Plan, kein implementierter/gesicherter Lauf | EMA-bedingte Shorts zusätzlich zu Long | Kein Audit-Auftrag zur Umsetzung/Live-Schaltung. Erst F02, Finanzierung, Daten und Kausalität klären; kein Merge-Go. |

## Was bereits kombiniert wurde – und was neu ist

Bereits belegt sind Pivotweite × ATR, Flush × Stopbehandlung, Mindeststop ×
Liquidationsaufstockung, Hochverkauf × Liquidationsverkauf, no_flip × feste Ziele,
Mindestbein × Beinrichtung, Widerstandsverkauf zusätzlich/statt Hochverkauf,
Resthalten × Neustart auf mehreren damaligen Basen, Tageszonen mit/ohne Mindestbein,
Muster-5-Einstieg/Halten und verschiedene Mehrbörsen-Datenpakete. E44.2 enthält
16 aus dem vorhandenen Gitter rekonstruierbare vier-Ecken-Gruppen; das ist kein
vollständiges faktorielles Experiment aller aktuellen Schalter.

E44.5 hat **nur** E42 × kleinere Teilverkäufe × Resthalten vollständig untersucht.
Insbesondere **E42 × high_exit aus** war dadurch nicht geprüft. Der Audit legt
zusätzlich G2–G5 vorher fest, darunter genau dieses Zusammenspiel sowie aktive
Bestandteile, die beim bisherigen Weiterbauen häufig als feste Basis behandelt wurden.

Heute: 79 eindeutige Konfigurationen, davon eine wegen des mangelhaften Short-Buchs
nicht als vergleichbare Rendite bewertet. Die 78 Long-Zeilen enthalten 45
Parameter sowie wirkungsabhängige Gegenproben. **Keine neue Einzelvariante erfüllt
beide Hälften ≥1 Punkt.** Nur die identischen Signalpfade V011/V012 (E42 an,
high_exit aus, trail_stop wahlweise aus/an) erreichen +1,29/+1,28 Punkte; sie
verfehlen die vorab strengere Kombinationsregel ≥2. Das ist eine begründete offene
Hypothese, keine Freigabe.

Der Vollständigkeitsabgleich ergänzte anschließend nach eigener Vorfestlegung das
frühe E4-Gitter: acht Zeilen, sieben weitere eindeutige Konfigurationen, insgesamt
**86 Handelskonfigurationen**. n=6 erhöht die Gesamtrendite auf 39,27 %, hat aber
−3,39/+5,72 Punkte Hälftendifferenz. Keine neue Zeile besteht. k=2/3 ist durch die
harte 5-%-Beinuntergrenze und die alternative 3-%-Schwelle logisch redundant.
Siehe [STRUKTUR.md](STRUKTUR.md); Werte und Prüfung waren vor dem Lauf in 098a65d
festgehalten. Dieser Zusatz ist keine nachträgliche Erweiterung des ursprünglichen
79-Zeilen-Plans.

Alle aktuellen Renditen, Risiken, Kosten, Orderzahlen, Kapitalbindungen, Hälften,
Monatsproben und Ausführungsstress stehen ohne Auswahl in
[KOMBINATIONEN.md](KOMBINATIONEN.md). Für genaue alte → neue Schalterzuordnung
enthält [PARAMETER.md](PARAMETER.md) jede einzelne Gegenprobe-ID.

## Belegstärke der Entscheidungen

**Belastbar als Software-/Quellenbefund:** Fib-Formeln, bestätigte Pivots im
Präfixverfahren, nachweisbare Persistenzwege, Reproduktion der E44.5-Ausgaben,
explizite Nutzerentscheidungen und die hier reproduzierten Fehlerbeispiele.

**Belastbar als bedingte historische Beschreibung:** Ein bestimmter Satz Signale
liefert unter ausdrücklich genannten Buchungs-/Kostenannahmen einen bestimmten
Portfoliopfad. Die unabhängige Kontrollrechnung stimmt nach F09-Korrektur für alle
78 Long-Konfigurationen des Hauptgitters und sieben zusätzlichen Strukturvarianten
überein. Das bestätigt die Rechnung, nicht die damalige
Ausführbarkeit oder die Zukunftsrendite.

**Nicht belegt:** Ein durch viele Entwicklungsrunden ausgewählter Schalter hat
einen stabilen Vorteil in neuen Marktphasen; Furkans tatsächliche Kontorendite;
Telegram-Zustellung aller alten Signale; historische Veröffentlichungszeiten der
abgeleiteten/aggregierten Daten. Fehlende Belege werden nicht durch eine große
Anzahl grüner Tests ersetzt.
