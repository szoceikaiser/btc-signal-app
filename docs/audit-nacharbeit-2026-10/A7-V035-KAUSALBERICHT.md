# A7/V035 – kausale Derivat-Nachprüfung

Stand 03.10.2026; Ausgang `969e69467149b2d8ab8c11cb5a7cb8aa47151343`.
Nur F02/V035 wurde fortgesetzt. A7s 85 Spotzeilen und M01/M02 wurden nicht
neu gewählt oder berechnet; A8 blieb ungestartet.

## Vertrag und Belege

`engine/execution_perp_offline.py:205-276` simuliert ausschließlich PF_XBTUSD
als linearen USD/BTC-Perpetual mit 1x-Kapitalgrenze. Die Strategie sieht nur
abgeschlossene 4h-Kerzen und zuvor bestätigte simulierte Fills. Eine Entscheidung
am Kerzenschluss wird am nächsten zusammenhängenden 4h-Open zum eingefrorenen
Handels-Open bepreist. Beim Schließen hat der volle Ausstieg Vorrang; sonst
werden Ausstiege vor Einstiegen ausgeführt. Gegenläufige Positionen werden
nicht gleichzeitig eröffnet. `no_flip` wird wie im V1-Ausführungsvertrag durch
die tatsächliche Reihenfolge ersetzt; dies ist ein neuer Ausführungsvertrag und
keine unveränderte Wiedergabe des alten Signalbandes.

`engine/strategy_core.py:2240-2270,2565` setzt die schon für Long vorhandenen
Ausführungsgates auch vor Short-Zustandsschreibungen. Mit fehlendem Gate wären
virtuelle Shorts trotz abgelehntem Fill entstanden. Der unveränderte Spot-Pfad
in `engine/execution_v1.py:93-100,357` erzwingt weiterhin `bias_short=False`
und weist Derivatkonfigurationen ab.

`engine/execution_perp_offline.py:34-189` führt BTC-Lose, Wallet, realisierte
und unrealisierte P&L, Gebühren und gebundene 1x-Margin in Decimal. Je Stunde
wird der veröffentlichte absolute USD/BTC-Satz vom Periodenbeginn mit dem
Bestand am Periodenende verbucht (`:81-96,244-257`). Ein fehlender Satz bei
offenem Bestand sperrt den strikten Lauf. Jede Bewertung prüft Equity > 0,
freie Wallet-Margin >= 0 und Bruttonotional <= Equity (`:59-79`). Kein
Liquidationskurs wird erfunden. Der modellierte Fillpreis ist keine Aussage
über echte Börsenfills, Spread, Orderbuch oder damalige API-Verfügbarkeit.

`tools/a7_v035_causal.py:27-125` verifiziert die Hashes der eingefrorenen
Kraken-Handels-/Markkerzen und des R1-Fundingarchivs, übernimmt exakt die
V035-Parameter (mit A2s `muster_cvd=usd`) und schreibt die knappe
[`causal-position-discovery-v1.json`](A7-V035-sources/causal-position-discovery-v1.json).
Die bisherige [Einzelfallprobe](A7-V035-NACHPRUEFUNG.md) bleibt ein eigener
retrospektiver Buchfall und wird nicht in diesen geschlossenen Strategielauf
eingemischt.

## Ergebnis der drei Fundinglücken

| Am Anfang gesetzte Rate UTC | Zahlung am Ende UTC | Modellierte Position | Aussage |
|---|---|---|---|
| 04.02. 12:00 | 04.02. 13:00 | 0 BTC | Im bis dahin strikten kausalen Pfad keine Zahlungspflicht. |
| 13.02. 18:00 | 13.02. 19:00 | Short 0,0798 BTC | Strikter Lauf stoppt mit `MissingFunding`; keine Rendite. |
| 09.05. 06:00 | 09.05. 07:00 | Long 0,0937 BTC nur im hypothetischen Weiterlauf | Bereits nach der fehlenden Februarrate und einer Risikogrenzverletzung; keine gültige historische Positionsfeststellung. |

Der hypothetische Weiterlauf setzt **nur zur Positionsdiagnose** für alle drei
fehlenden absoluten Sätze 0 USD/BTC ein und lässt spätere Risikoverletzungen
aufzeichnen, statt sie zu ignorieren. Die gleiche offene Lückenmenge tritt
bei illustrativen Sätzen von −1 und +1 USD/BTC auf. Diese drei Setzungen
sind keine beobachteten Zahlungen und keine belastbare obere oder untere
Grenze. Ihre Endkapitalwerte werden nicht als Ergebnis ausgewiesen.

Selbst mit Null-Platzhaltern sperrt die strikte 1x-Regel am **17.04.2026
15:00 UTC**: Bruttonotional 9.386,21159224223115 USD gegenüber Equity
9.339,4702375815354174420736 USD. Ohne vertraglich belegtes
Liquidations-/Marginverfahren kann danach keine gültige Position oder Rendite
fortgeschrieben werden. Der öffentliche Kraken-CSV-Export endet für PF_XBTUSD
am 01.02.; Grafik-Vorwerte und das interne Drittarchiv sind keine
Originalabrechnung. [Kraken beschreibt Derivat-Account-Logs mit dem Typ
„Funding Rate Change“](https://support.kraken.com/in/articles/360057072571-interpreting-the-logs-derivatives),
doch für die hier nur simulierte Position existiert kein reales Nutzerkonto
mit einem zugehörigen Zahlungslog. Ein solcher Log kann den fehlenden
öffentlichen Satz daher nicht belegen. Der öffentliche
[Funding-CSV-Export](https://support.kraken.com/articles/export-historical-funding-rates)
ist bereits in der vorigen Nachprüfung abgeglichen.

## Kontrollrechnung und Priorität

`tools/a7_v035_causal.py:83-89` rechnet Wallet aus Startkapital + realisierter
P&L − sämtlichen Fillgebühren + sämtlichen Fundingzahlungen und Equity aus
Wallet + offenem Los-P&L neu. Beide Abweichungen sind **0 USD**. Die sechs
gezielten Gegenfälle in `engine/test_execution_perp_offline.py:17-88` prüfen
Short-/Long-Vorzeichen, Stundenabgrenzung, zwei volle Shorts, fehlende Rate,
1x-Risikosperre und das Short-Gate. Ein identischer Zeitpräfix bis
01.02.2026 00:00 UTC liefert exakt dieselben Buchereignisse wie der spätere
Weiterlauf; zukünftige Kerzen beeinflussen diese Entscheidungen nicht. Die
52 vorhandenen A5- und V1-Gegenfälle
bestanden unverändert. Der kontrollierte hypothetische Lauf enthält 404
Kandidaten, 373 Fillversuche, davon 162 akzeptiert; diese Zähler sind keine
Handelskennzahlen einer gültigen historischen Rendite.

- **P1 F02 / 13.02.:** fehlender ursprünglich veröffentlichter Satz bei
  modelliertem Short. Auswirkung: strikter V035-Lauf stoppt am 13.02. 19:00 UTC.
  Beleg: JSON `strict`, `engine/execution_perp_offline.py:81-89`.
- **P1 F02 / Risiko:** 1x-Bruttogrenze wird selbst unter expliziten
  Null-Platzhaltern am 17.04. verletzt. Auswirkung: ohne belegtes
  Liquidationsmodell kein gültiger Weiterlauf bis Mai. Beleg: JSON
  `strict_risk_with_zero_placeholders` und `hypothetical_first_risk_breach`.
- **P2 F02 / historische Kosten und Ausführung:** 0,1 % ist der bestehende
  S0-Modellsatz, kein belegter Kraken-Tarif. Nächster 4h-Open, 0,0001 BTC
  Schritt und stündliche Marks sind Modellannahmen. Auswirkung: auch bei
  vollständigen Fundingdaten keine Behauptung realer Fills oder damaliger
  Handelsbedingungen. Beleg: `engine/execution_perp_offline.py:15-18,98-189`,
  Quellmanifest und A5-Vertrag.

**Urteil:** Die kausale F02-Nachprüfung ist als *nicht auswertbarer historischer
V035-Gesamtlauf* abgeschlossen. Es wird keine V035-Rendite und kein Vergleich
mit den alten retrospektiven V035-Diagnosezahlen freigegeben. Diese alte
Diagnose nutzt einen anderen Ausführungs- und Kostenvertrag. A8 kann den
belegten F02-Endstatus als offene Daten-/Risikogrenze prüfen; eine spätere
vollständige Zahl erfordert originale zahlungsfähige Funding- und
Liquidationsevidenz und einen erneut validierten Vertrag.
