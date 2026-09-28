# Unabhängiger Audit des Bitcoin-Signalprojekts

Abschlussstand: 28.09.2026. Repository `szoceikaiser/btc-signal-app`, eigener Zweig
`codex/audit-2026-09-27`. **Kein Merge-Go für E44.4 oder E44.5.**

## Kurzurteil

**Das Projekt besitzt eine umfangreiche, tatsächlich ausgeführte Testsuite und eine
weitgehend nachvollziehbare Entwicklungsgeschichte. Seine historische Rendite ist
jedoch noch keine belastbare Aussage über eine ausführbare Live-Strategie.** Mehrere
Fehler betreffen genau die Grundlagen früherer Entscheidungen: Ausführungszeitpunkt,
Drawdown, Einstand, Stop-Nachzug und Wiederanlage. Daneben bestehen konkrete Risiken
für die Übereinstimmung zwischen Engine, Telegram und Chart.

| Einordnung | Ergebnis |
|---|---|
| Belastbar innerhalb der geprüften Bedingungen | 607 bestehende Tests laufen durch. E44.5 lässt sich mit den gespeicherten Eingaben und unverändertem Engine-Code inhaltlich exakt reproduzieren. Pivot-Erkennung wartet im geprüften Präfix auf die rechten Bestätigungskerzen. Main und E44.5 erzeugen mit den Live-Defaults dieselben Signale auf den eingefrorenen Daten. |
| Bestätigt fehlerhaft | Drawdown verwendet den falschen Bestand innerhalb einer Kerze; winzige BTC-Reste verändern Folgekäufe; der Einstand wird für Kapitaltranchen falsch gemittelt; ein nachgezogener Struktur-Stop kann wieder fallen; eine fehlgeschlagene Telegram-Zustellung wird nicht zuverlässig wiederholt; der Chart bevorzugt bei Kollisionen den Backtest-Eintrag. |
| Nicht ausreichend belegt | Reale erzielbare Rendite, Vorteil von E42, Überlegenheit der gewählten Live-Schalter und Gleichsetzung der App mit Furkans tatsächlicher Strategie. Ein grüner Funktionstest beweist keines dieser Dinge. |
| Mit vorhandenen Belegen nicht vollständig prüfbar | Ältere historische Renditeläufe ohne ihre damaligen Rohdaten, frühere tatsächliche API-Verfügbarkeit, echte Broker-Ausführungen, vollständige Telegram-Zustellhistorie und damalige Liquiditätskarten. |

**E42 ist weder durch die Idee eines gehaltenen Rücktests gerechtfertigt noch durch
die kleine negative historische Differenz allgemein widerlegt.** Im gespeicherten
Fenster wurden 16 Rückkauf-Lose eröffnet: sechs mit Gewinn, zehn mit Verlust. Nach
unabhängiger Buchführung verdienen diese Lose zusammen 13,45 USD; das Gesamtportfolio
liegt trotzdem 71,53 USD hinter E42 aus. Das ist kein Widerspruch: Rückkäufe verändern
Cash, weitere Kaufgrößen, Teilverkäufe und den späteren Strategiepfad.

Die gemeinsame Neuberechnung umfasst **79 vorab festgelegte Konfigurationen**, darunter
fünf vollständige kleine Kombinationsgitter, sowie separat vorab dokumentierte
Kapitalquoten. Keine neue Kombination erfüllt die strengere Regel von mindestens
zwei Prozentpunkten Vorteil in beiden Hälften. E42 zusammen mit abgeschaltetem
Hoch-Verkauf ist eine interessante Wechselwirkung mit rund 1,29/1,28 Punkten Vorteil
in den Hälften. Das ist ein Anlass für einen späteren sauberen Vorwärtstest, kein Go.

## Berichte und Belege

| Frage | Vollständiger Bericht |
|---|---|
| Welche Entscheidungen wurden wann, womit und gegen welche Basis getroffen? | [ENTSCHEIDUNGEN.md](ENTSCHEIDUNGEN.md), [PARAMETER.md](PARAMETER.md), [HISTORISCHE-BELEGE.md](HISTORISCHE-BELEGE.md) |
| Was sagt Furkan tatsächlich, und was ist Entwicklerinterpretation? | [FURKAN-QUELLEN.md](FURKAN-QUELLEN.md) |
| Was geschah in jedem E42-Fall? | [E42.md](E42.md), [vollständiger Ereignis- und Losdatensatz](e42-faelle.json) |
| Welche Kombinationen wurden wie gemessen? | [KOMBINATIONEN.md](KOMBINATIONEN.md), [KAPITAL.md](KAPITAL.md), [Vorfestlegung](PLAN.md) |
| Was ist reproduziert, was korrigiert, wie wiederholen? | [REPRODUKTION.md](REPRODUKTION.md) |
| Welche Daten sind tatsächlich belegt? | [DATEN.md](DATEN.md) |
| Welche externe Evidenz passt zum Projekt? | [FORSCHUNG.md](FORSCHUNG.md) |
| Welche Auftragsbestandteile wurden geprüft, welche bleiben begrenzt? | [ABDECKUNG.md](ABDECKUNG.md) |

Die folgenden Codezeilen beziehen sich auf Engine-Stand `e2b0051`. Die Auditdateien
verändern keine Produktionsdatei. Reproduzierbare Gegenbeispiele stehen in
[`audit/probes.py`](../../audit/probes.py),
[`audit/additional_probes.py`](../../audit/additional_probes.py),
[`audit/chart_probe.cjs`](../../audit/chart_probe.cjs) und
[`audit/telegram_order.py`](../../audit/telegram_order.py).

## Priorisierte Befunde

### P1: Vor weiteren Strategieentscheidungen korrigieren und erneut messen

**F12 – Ein Signal am Kerzenschluss erhält teilweise einen früheren Preis derselben
Kerze.** `strategy_core.evaluate` entscheidet mit der abgeschlossenen 4h-Kerze;
`backtest.simulate`, Zeilen 881–929, rechnet dennoch standardmäßig den angegebenen
Fib-Preis ab. Eine zuvor berührte Marke ist keine nachträglich verfügbare Ausführung.
Insbesondere wird das Korrekturtief und damit das Extension-Ziel teilweise aus der
gerade abgeschlossenen Kerze bestimmt. Ob das Tief vor oder nach dem Hoch lag, ist
aus OHLC nicht bekannt. Eine vorher platzierte Order wäre ein anderer, explizit zu
simulierender Handelsprozess mit damals bekannten Marken und Stornierungen.

Zwei konkrete Verkäufe liegen sogar außerhalb der eigenen Kerzenspanne: am
05.03.2026, 12:00 UTC, TV1 zu 70.402,28 bei Tief 71.168,65; am 13.06., 08:00 UTC,
Leiter-Verkauf zu 63.666,55 bei Tief 63.726,57. Beide Preise liegen **unter** dem Tief:
das ist in diesen Fällen ungünstiger für den Verkäufer und beweist keine pauschale
Gewinnübertreibung. Es beweist die fehlende Abbildung einer tatsächlichen Ausführung.
Die Bezeichnung „Wert der Vorab-Order“ für die Differenz Level/Schluss ist deshalb
zu stark. Auch eine spätere Ausführung kann günstiger werden; Verzögerung ist kein
immer gleichgerichteter Preisnachteil.

**F01 – Die Drawdown-Rechnung kann einen realen Rückgang vollständig übersehen.**
[`backtest.py`](../../engine/backtest.py), Zeilen 1091–1111, wendet den Bestand
**nach allen Signalen der Kerze** auf deren Tief und Hoch an. Einfacher Kontrollfall:
10.000 USD vollständig zu 100 investiert; nächste Kerze Tief 50, Schluss 100;
Verkauf zu Schluss 100. Der Kontowert fällt zwischenzeitlich um 50 %. Die bestehende
Rechnung meldet 0 %. Zusätzlich unterstellt die feste Reihenfolge Tief → Hoch eine
nicht belegte Kursabfolge. Das betrifft die Aussagekraft aller Entscheidungen mit
„höchstens ein Punkt mehr Drawdown“, auch nach dem früheren E27-Fix.

Das Audit berechnet den Schluss-Drawdown separat und prüft für kausale
Schluss-/Folgekerzen-Ausführung beide OHLC-Reihenfolgen. Ein exakter maximaler
Intraday-Rückgang für bedingte Level-Orders bleibt ohne feinere Daten offen. Die
Tatsache, dass ein Basiswert numerisch ähnlich bleibt, widerlegt den Gegenfall nicht.

**F09 – Ein Rest von ungefähr 0,000000000000000028 BTC verhindert einen neuen
Kapitalzyklus.** `backtest.py:997` verlangt exakt `units == 0.0`. Nach vollständigen
prozentualen Teilverkäufen verbleibt ein Rundungsrest. Beim nächsten Kauf bleiben der
alte Bezugsbetrag und Höchstbestand bestehen. Reproduzierbarer Übergang: 06./07.04.,
Zeitstempel 1775462400000 → 1775563200000. Die unabhängige Rechnung gleicht nicht nur
eine Kennzahl ab, sondern führt Käufe, Losmengen, anteilige Abgänge und Gebühren selbst.

Auf den unveränderten Originaleingaben verändert **nur diese Buchungskorrektur**:

| Variante | Ursprünglicher Endwert bei 10.000 USD | Unabhängiger Endwert | Änderung der Rendite |
|---|---:|---:|---:|
| Rest halten | 13.541,49 | 13.671,88 | +1,304 Prozentpunkte |
| E42 | 13.593,32 | 13.542,22 | −0,511 Prozentpunkte |
| E42, sechs Kerzen | 13.650,87 | 13.599,55 | −0,513 Prozentpunkte |

Die übrigen sechs Originalzeilen stimmen auf Rundung überein. Der Fehler kann also
je nach Pfad **in beide Richtungen** wirken. Die Originalartefakte sind unverändert
erhalten; ihre Rangfolge wurde nicht still überschrieben.

**F03 – Der nachgezogene Struktur-Stop kann wieder sinken.**
`strategy_core.py:2186–2202` nimmt für Long nur bestätigte Tiefs **unter dem jetzigen
Schlusskurs**. Ein zuvor gültiger Stop bei 115 entfällt, sobald der Schluss auf 110
fällt; übrig bleibt im Gegenbeispiel der Einstand 100. Es erfolgt kein Stop. Der
vorherige maximale Stop wird nicht als monotone Grenze gespeichert.

Der vorhandene Test `test_trail_stop_lockert_den_stop_nie` in
`test_strategy_core.py:571` prüft lediglich, dass ein Kurs unter der ursprünglichen
Invalidierung einen Stop auslöst. Er erreicht den oben beschriebenen Rückfall vom
Struktur-Stop nicht. Live ist `trail_stop=true`; im gemeinsamen historischen Gitter
ändert sein Ausschalten bei den hier geprüften Basis-/G2-Pfaden allerdings nichts.
Das belegt geringe Wirksamkeit in diesen Pfaden, nicht die Fehlerfreiheit des Stops.

**F04/F10 – Engine-Einstand und angezeigter Stop können vom tatsächlichen Bestand
abweichen.** In `strategy_core.py:2637–2640` wird der Preis mit Kapitalprozenten
arithmetisch gemittelt. Für 25 Geldeinheiten zu 220 und 50 zu 172,80 ist der korrekte
Einstand ohne Gebühren `75 / (25/220 + 50/172,8) = 186,10966`. Der Code liefert
188,53333. Bei Kapitaltranchen muss nach gekauften BTC gewichtet werden. Dazu zählt
`entry_pct` historische Käufe, sinkt bei Verkäufen nicht und kann über 100 steigen.
Die Portfoliosimulation führt tatsächliche BTC anders als die Signal-Engine.

`main.positions_plan`, ab Zeile 591, bildet außerdem nicht alle Stop-Kandidaten der
Engine ab: Gegenfall F10 zeigt Engine-Stop 115, Plan-Stop 100. Ein gespeicherter und
zwischen Oberflächen geteilter Plan beseitigt eine falsche Berechnung nicht. Die
Korrektur muss Bestand, Loskosten, Signal-Stop und Darstellung gemeinsam definieren.

**F13 – Fehlgeschlagene Telegram-Nachrichten können dauerhaft verschwinden.**
`main.py:1079–1081` persistiert den verarbeiteten Stand vor dem Signalversand;
`telegram_notify.py:490–503` wertet `send_telegram=False` nicht aus. Die netzfreie
Gegenprobe erzeugt ein Signal, lässt die Zustellung scheitern und wiederholt dieselbe
Kerze: zweiter Lauf null Signale, null Versandversuche. Eine neu berechnete Vorschau
wird an anderer Stelle vor der Speicherung gesendet, wodurch umgekehrt Doppelungen
bei einem anschließenden Schreibfehler möglich sind. Drei einzeln geschriebene
JSON-Dateien bilden auch keine gemeinsame atomare Transaktion.

Es ist **kein tatsächlicher historischer Nachrichtenverlust nachgewiesen**; dafür
fehlen Zustellbelege. Der bestätigte Fehler ist die fehlende Zuverlässigkeit im
Fehlerfall. Abhilfe: dauerhafte Versandliste mit eindeutiger Signal-ID, quittierte
Zustellung, Wiederholungsregeln und konsistente Speicherung.

**F17 – Der Chart lässt bei einer Kollision den Backtest gewinnen.**
[`site/index.html`](../../site/index.html), um Zeile 389, verarbeitet
`[...btsig, ...sig]` und behält beim Schlüssel Zeitstempel + Typ den ersten Eintrag.
Die ausgeführte JavaScript-Gegenprobe zeigt daher 100 aus dem Backtest anstelle von
105 aus dem Live-Eintrag. Im tatsächlich gespeicherten Snapshot sind zwei Kollisionen
mit unterschiedlichen Gründen beziehungsweise 15 statt 20 % Tranche vorhanden;
die Preise dieser beiden realen Kollisionen sind gleich. Ein real beobachteter
Preiswiderspruch wird hier **nicht** behauptet. Mehrere berechtigte Signale desselben
Typs in derselben Kerze können durch denselben Schlüssel ebenfalls zusammenfallen.

### P2: Datenbegriff, Zeitverfügbarkeit und bisherige Statistik

| ID | Befund, Beleg und Reichweite | Konsequenz |
|---|---|---|
| D01 | In 2.481 gespeicherten E44.5-Kerzen liegt eine laufende Kerze: 27.09., 08:00 UTC, gespeichertes Ende 08:29, Kerzenschluss erst 12:00. `main.fetch_market_data` filtert unfertige Kerzen, der ursprüngliche Backtest nicht durchgängig. | Original-Replay unverändert lassen; gemeinsame Messung nur mit 2.480 geschlossenen Kerzen. Davon 1.509 im Auswertungszeitraum, Rest Vorlauf. |
| F06 | `_slope`/`classify_pattern`, `strategy_core.py:467/1047`: relativer Anstieg kumulativer CVD hängt vom willkürlichen Summenstart ab. Dieselben Änderungen plus konstanter Versatz ändern DERIVATE_PUMP in GESUNDER_TREND. | Technische Bedeutung korrigieren unabhängig davon, ob die Korrektur auf einem kurzen Fenster Rendite kostet. G5 liefert hier unveränderte Renditen; 90-Tage-Neustart verändert ein Muster, kein Signal. |
| F07 | `main.py:285/308`, `backtest.py:761/782`: das erste später vorhandene OI wird in frühere fehlende Zeitpunkte zurückgetragen. Gegenfall: erster Messpunkt bei 8h steht schon bei 0h. | Fehlend vor erstem Wert muss fehlend bleiben. Der Backtest-Start beim ersten OI begrenzt direkte Trades, heilt aber erfundene Vorlaufdaten nicht. Keine pauschale Behauptung, alle 2026-Trades sähen Zukunft. |
| D02 | Fehlende Werte teilen sich teilweise die Zahl null mit echten neutralen Messungen. `confirm_ok` akzeptiert unter anderem Funding ≤0 als Long-Bestätigung. | „Keine Information“ darf keine positive Bestätigung liefern. Herkunft, Abdeckung und Alter pro Wert mitführen. Im eingefrorenen Input wurden keine Funding-Nullen gefunden; die Fehlerbedingung ist separat erreicht. |
| F02 | Short-Eröffnungen in `backtest.py:1033–1042` binden kein Kapital/Margin, nur Gebühren. Zwei nominale 100-%-Shorts erzeugen bei 10 % Kursfall 20 % Rendite trotz behauptetem Handel ohne Hebel. Funding fehlt. | Frühere Long/Short-Vergleiche und V035 sind nicht als unverschuldete Alternativen vergleichbar. Aktuelles Live ist Long-only; reale Perpetual-Longs hätten ebenfalls Funding. |
| F08 | `resample_daily`, Zeile 302, erzeugt aus zwei 4h-Kerzen bereits eine Tageskerze; Tagesindikatoren können damit den laufenden Tag verwenden. | Kein Zugriff auf den noch unbekannten späteren Tagesschluss im Präfix-Test, aber andere Semantik als „abgeschlossene Tageskerzen“. Optionale Tagesregeln erst nach eindeutiger Definition beurteilen. |
| M01 | Viele alte Zeilen heißen „LIVE“, unterscheiden sich aber in mehreren Parametern von heutigem Live. Von 85 Codezeilen: eine identisch, 23 mit einer Änderung, 61 mit mehreren. | Alte Ablehnung gilt für die damalige konkrete Basis. Nicht ohne Weiteres auf die heutige Kombination übertragen. |
| M02 | Daten wiederholt zur Entwicklung verwendet, zahlreiche Filter und Regeln getestet, teilweise Grenzwerte/Regeln später angepasst; unabhängige Versuchsanzahl unbekannt. | Hälften und Monatsproben sind nützliche Diagnosen, keine unberührte externe Validierung und kein statistischer Signifikanznachweis. |

### P3: Weitere bestätigte Fehler und Prüfgrenzen

| ID | Reproduzierbarer Befund | Derzeitiger Umfang |
|---|---|---|
| F05 | `pos_to_state`/`pos_from_state`, `main.py:399/445`, verlieren `widerstand_exits`: 1 → 0. | Widerstandsverkauf aktuell aus. Bei Aktivierung würde der Neustart anders handeln als ein durchlaufender Backtest. |
| F11 | `eval_params({"bias_short":"false"})` ergibt boolesch wahr. | Aktuelles JSON nutzt richtige boolesche Werte; latenter Konfigurationsfehler. Schema/Typen statt pauschalem `bool(text)`. |
| F14 | `_summiere_vollstaendig`, `coinalyze.py:512`, summiert nur zurückgekehrte Märkte. Fehlt B vollständig, gelten Punkte von A als vollständig. Der Bericht nennt zwar `ohne_antwort=[B]`, die Rechenreihe wird trotzdem geliefert. | Aggregation live aus. Widerspruch zur behaupteten Regel „alle gefragten Reihen“; keine gemessene Auswirkung auf Live-Rendite behauptet. |
| F15 | `_nach_denominierung`, `coinalyze.py:660`, vergleicht Rohvolumen unterschiedlicher Einheiten: 2.000 USD schlägt 1.000 BTC, obwohl diese bei 60.000 USD/BTC 60 Mio USD entsprechen. | Aggregation aus. Marktauswahl außerdem anhand heutiger Verfügbarkeit und über ganze Historie gemessenem Volumen, kein sauberer damaliger Börsenkorb. |
| F16 | `atr`, `strategy_core.py:148`, richtet bei Historie ≤ Periode Vorgängerschlüsse falsch aus. Drei Kerzen ergeben 2 statt unabhängiger True-Range-Mittelwert 26. | Normaler langer Vorlauf nicht betroffen. Grenzfall relevant für kurze Datenfenster/Tests. |
| T01 | Sieben alte Sabotagevorlagen treffen den heutigen Code nicht mehr. Nach Anpassung werden sechs erkannt; eine vertauschte E41-Nachrichtenreihenfolge bleibt mit 607 grünen Tests unentdeckt. | Eigene Gegenprobe erreicht eine Wartekerze **mit** Teilverkäufen und erkennt die Mutation. Die Produktionsreihenfolge ist dabei korrekt; dies ist eine Testlücke. |

## Was die Prüfungen auch positiv zeigen

Die 607 Tests wurden in der vollständigen Repository-Struktur ausgeführt, einschließlich
der echten Konfiguration. Die vorhandenen Sabotageläufe wurden ebenfalls geprüft;
Windows-Probleme mit `SIGALRM` wurden in einer isolierten Laufumgebung behandelt,
nicht als bestandene Tests gezählt. Die Bilanz und sämtliche Protokolle stehen im
Reproduktionsbericht. Vorlagen ohne Treffer zählen als nicht ausgeführte Eingriffe.

Die Pivot-Gegenprobe fordert n rechte Kerzen und erkennt einen absichtlich zu früh
zugelassenen Pivot. Der Audit-Präfixlauf fügt keine späteren Kerzen hinzu. Für den
aktuellen Long-Standard liefern Neustart nach jeder Kerze und rollierende 1.300
Kerzen dieselben 244 Signale wie der volle eingefrorene Backtest. Das belegt die
geprüfte Code-Parität, aber nicht die tatsächliche historische API-/Live-Parität.

Ein eigenes Losbuch wurde mit einer von Hand berechenbaren Kauf-/Verkaufsfolge
geprüft. Eine absichtlich ausgelassene Gebühr wird erkannt. Bei allen 78 auswertbaren
Long-Zeilen stimmt es nach F09-Korrektur mit der isoliert korrigierten Originalrechnung
bis auf deren Cent-Rundung überein. V035 mit Short-Anteilen bleibt ausdrücklich
außerhalb dieses Nachweises.

## Gemeinsame Renditemessung und Entscheidungsregeln

Basis: unveränderte aktuelle Live-Parameter, Rohdaten-Hash
`ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a`,
Handelszeitraum 18.01.–27.09.2026 bis Schluss 08:00 UTC. Nur geschlossene Kerzen,
F09 im Audit-Losbuch korrigiert. **Sonstige Engine-Fehler sind nicht still repariert.**
Alle Werte sind Modellrechnungen, keine Kontoergebnisse.

| Modell / Variante | Rendite % | H1 % | H2 % | Einordnung |
|---|---:|---:|---:|---|
| Live-Basis, Level-Preise | 36,13 | 23,61 | 10,13 | Gemeinsame Vergleichszahl, Ausführbarkeit nicht gesichert |
| Nur E42 zusätzlich | 35,42 | 25,37 | 8,01 | Vorteil in H1, Nachteil in H2 |
| Nur Rest halten | 36,72 | 20,50 | 13,46 | Unterschiedliche Wirkung der Hälften |
| Kleinere Verkäufe + Rest halten | 37,90 | 18,16 | 16,71 | Hohe zeitliche Konzentration und höheres Risiko |
| E42 + Hoch-Verkauf aus | 39,14 | 24,90 | 11,40 | +1,29/+1,28 Punkte; strengere Kombinationsregel +2/+2 verfehlt |

Die Basis fällt bei Ausführung am Schluss auf 34,10 %, bei nächster Eröffnung mit
0,05 % Preisnachteil pro Seite auf 31,09 %, bei einer weiteren 4h-Kerze Verzögerung
und höheren Kosten auf 17,97 %. Diese Stressmodelle verschieben dieselben
Signalabsichten. Sie berechnen die Signal-Engine **nicht** erneut aus tatsächlich
verspäteten Ausführungen und Beständen. Damit beschreiben sie die Empfindlichkeit,
nicht die vollständige Live-Simulation eines anderen Ausführungsprozesses.

Die Basis enthält 191 positive Orders, 14 Orders ohne verfügbares Kauf-/Verkaufsvolumen,
22 Kapitalzyklen, 545,01 USD Gebühren und im Mittel 35,42 % investiertes Vermögen.
244 Signale sind nicht 244 ausführbare Trades; auch Teilverkäufe sind keine
unabhängigen Positionen. Der Schluss-Drawdown beträgt −8,29 %. Bei Schlussausführung
ergibt die OHLC-Risikoprüfung ungefähr −9,94 %. Die Risikodefinitionen dürfen in einer
Entscheidungsregel nicht vermischt werden.

Die Kapitalquote zeigt den üblichen Zielkonflikt konkret: 60 % Bereitstellung liefert
31,19 % Modellrendite bei −7,55 % Schluss-Drawdown, 50 % liefert 26,14 % bei −6,74 %.
Eine geringere Roh-Rendite macht eine Reserve deshalb nicht automatisch schlechter.
Buy-and-Hold im gleichen angeschnittenen Fenster liegt nach Einstiegsgebühr bei
−9,57 %, mit wesentlich größerem Schluss-Drawdown. Dieser Vergleich validiert die
Signalstrategie wegen ihrer Ausführungs- und Datengrenzen noch nicht.

Die ursprüngliche E44.5-Regel ergibt im originalen Replay weiterhin „keine Variante
bestanden“. Nach der gemeinsamen Korrektur ergibt sich weiterhin kein qualifizierter
neuer Kandidat. Die zwei formal ähnlichen G2-Zeilen V011/V012 unterscheiden sich nur
im hier wirkungslosen Trailing-Schalter; sie sind **keine zwei unabhängigen Bestätigungen**.

Sieben- und 28-Tage-Blockproben für E42 minus Basis liefern sehr breite beschreibende
95-%-Intervalle von ungefähr −6,08 bis +6,15 beziehungsweise −5,53 bis +5,88
Prozentpunkten. Es gibt nur ungefähr neun 28-Tage-Blöcke. Das Vorzeichen eines kleinen
historischen Unterschieds ist daher nicht stabil genug für eine allgemeine Aussage.
Diese Intervalle berücksichtigen zeitliche Abhängigkeit teilweise, aber weder die
gesamte frühere Parametersuche noch neue Marktregime. Sie sind keine zugesicherte
zukünftige Gewinnspanne und kein nachträglich korrigierter Signifikanztest.

Die rollierende Auswertung Mai–September hält Parameter fest und trägt offene
Positionen weiter. Sie ist eine rückblickende zeitliche Konsistenzprüfung. Ein
Walk-forward-Verfahren mit unberührten Prüfphasen und unabhängiger Auswahl lässt
sich auf bereits oft benutzten Monaten nicht nachträglich herstellen.

## Furkan und externe Forschung

Alle sechs gefundenen Transkripte wurden vollständig gelesen und nach Datum,
Zeitmarke und Art der Aussage zugeordnet. Furkan trennt langfristige Spotkäufe,
bestehende Futures-Positionen, mehrere Strukturen und bedingte neue Ideen. Ein
Original-Standbild vom 02.08. zeigt ausdrücklich einen 2h-Chart. Eine universelle
Regel „immer genau unser 4h-Pivot plus Tagesfilter“ ist daraus nicht ableitbar.

0,5/Golden Pocket und gestaffelte Gewinne sind in den Quellen enthalten. Dagegen
sind die konkreten 25/50/25-Käufe, 40/40-Verkäufe, Schwellen der Order-Flow-Muster,
E42-Frist und automatischer Pivot-Bezug Projektentscheidungen. Der zitierte Rücktest
vom 02.08. bezieht sich rückblickend auf eine übergeordnete On-Chain-Kostenbasis,
nicht auf den exakten E42-Mechanismus. Bereits erfolgte Liquidationen sind außerdem
keine Karte noch offener Liquiditätsansammlungen.

Die Primärliteratur stützt die Relevanz von Marktsegmentierung, Order Flow,
Momentum und zeitabhängigen Volatilitätsmustern. Sie belegt **nicht** diese konkrete
Fib-/Rücktest-Regel. Ein Effekt auf Millisekundenebene ist kein Nachweis für einen
4h-Einstieg; gleichzeitig beobachteter Flow erklärt einen Kurszug teilweise, ohne
den nächsten vorherzusagen. Forschung zu vielen technischen Regeln unterstreicht
Kosten und Mehrfachtests. Details, Originalquellen, passende Zeitebenen und fünf
vorab formulierbare Anschlussfragen: [FORSCHUNG.md](FORSCHUNG.md).

## Maßnahmen in sinnvoller Reihenfolge

| Priorität | Konkrete Maßnahme | Abnahme / notwendiger Beleg |
|---|---|---|
| 1 | Ausführungsvertrag definieren: Kerzenschluss-Signal oder vorher liegende bedingte Order; Signalzeit, Bekanntgabezeit und Fillzeit getrennt führen. | Keine Order nutzt später bekannt gewordene Kerzenwerte. Reihenfolgefälle Kauf/Stop/Verkauf mit feineren Daten oder ausgewiesenen Grenzen. |
| 1 | Portfolio- und Risikorechnung reparieren: F09, tatsächliche BTC-Lose/Einstand, Kapitalbindung, Margin/Funding bei Derivaten, Bestand vor/nach jedem Ereignis. | Handrechenbare Gegenfälle F01/F02/F04/F09 bestehen; unabhängiges Losbuch stimmt bei allen Varianten. Alte und korrigierte Berichte getrennt archivieren. |
| 1 | Stop monoton speichern und denselben tatsächlichen Stop in Engine, state und Plan verwenden. | F03/F10 über zwei aufeinanderfolgende Kerzen einschließlich Neustart testen. Keine stille Strategieänderung als angeblicher Anzeige-Fix. |
| 1 | Versand dauerhaft quittieren; Chart nach Herkunft und eindeutiger Signal-ID zusammenführen. | F13 mit fehlgeschlagener Zustellung, Wiederanlauf und Schreibfehler; F17 mit widersprechenden und gleichzeitigen Signalen. Keine echten Testnachrichten ohne Auftrag. |
| 2 | Rohdaten mit Abrufzeit, Endpunkt, Instrument, Einheit, Vollständigkeit und damaligem Veröffentlichungsstand unveränderlich archivieren. | Fehlend bleibt fehlend; nur abgeschlossene Kerzen; F06/F07/D01/D02; Aggregation zusätzlich F14/F15. |
| 2 | Bestehende entscheidungsrelevante Tests um erreichbare Gegenfälle und unabhängige Zahlen ergänzen; veraltete Sabotagen als Fehler melden. | Testname, tatsächlich erreichter Zweig und nachgewiesen gefangene Mutation; kein „grün“ bei übersprungenem Fall. |
| 3 | Dieselben vorab festgelegten Gitter nach den grundlegenden Korrekturen erneut rechnen. | Keine nachträgliche Schwellenoptimierung; jede Ergebnisänderung einer Korrektur zuordnen; Hälften/Kosten/Risiko konsistent. |
| 3 | Anschließend einen zeitlich neuen, protokollierten Schattenbetrieb planen. | Parameter vorher einfrieren, Eingänge/Signal/Simulationsfüllung speichern; unabhängige E42-Episoden zählen. Mindestumfang anhand gewünschter Messgenauigkeit planen, nicht „ein grüner Monat“. |
| 4 | Nur begründete neue Mechanismen untersuchen, zuerst einfache Trend-/Volatilitätsreferenzen und sauber messbaren Flow. | Hypothese, damalige Datenverfügbarkeit, Kosten und Erfolgskriterium vorher festlegen. On-Chain nur mit belegter Veröffentlichungszeit. |

Diese Maßnahmen sind Empfehlungen des Audits. Es wurden keine Produktionskorrekturen
aktiviert. Unvermeidbar offen bleiben echte vergangene Ausführungen, nicht archivierte
Datenstände und eine noch nicht existierende unabhängige Zukunftsstichprobe. Fehlende
Belege lassen sich durch zusätzliche Varianten auf denselben Monaten nicht ersetzen.

## Sicherung und Eingriffsgrenzen

Eingefrorenes main: `89885adc9fb6d2eae60f7a64f9452760a4e33cd9`.
E44.4: `eeb4eea72e3ac2baa5b713c57337801b1b8bc291`.
E44.5: `e2b0051199c2e0c38723cc3a23c00ea3bd320601`.
Originaler Messcode `68e15ae` hat gegenüber diesem E44.5-Stand keine Engine-Differenz.
Die später geprüften main-Änderungen bis `ce8e713fc75291b57154138a71aad319c01ad2d4`
betreffen nur automatisch aktualisierte `state.json` und `signals.json`.
Die Abschlussabfrage steht getrennt in [github-abschluss.json](github-abschluss.json).

GitHub-Schreibrechte wurden geprüft; Audit-Zwischenstände liegen auf einem eigenen
Zweig. Ein Branch-Push startet ausschließlich den vorhandenen Tests-Workflow.
Der gewöhnliche Backtest-Workflow wurde nicht gestartet, weil sein erfolgreicher
Abschluss über `pages.yml` auch ohne passende Zweigbegrenzung eine Veröffentlichung
auslösen kann. Keine Messung per GitHub-Dispatch, kein Merge, keine Live-Umstellung,
keine Telegram-Nachricht, kein Deployment durch den Audit. Die private Backup-Wurzel
und private Volltranskripte wurden nicht in den öffentlichen Zweig übernommen.
