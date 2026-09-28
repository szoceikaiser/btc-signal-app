# Datenherkunft, Zeitverfügbarkeit und Grenzen

Stand 28.09.2026. Dieser Bericht unterscheidet einen gespeicherten Zahlenstand von
dem damals tatsächlich verfügbaren Informationsstand. Beides ist für einen
reproduzierbaren Live-Vergleich erforderlich.

## Eingefrorene Messgrundlage

Datei: [docs/e445/eingaben.json](../e445/eingaben.json).
SHA-256: `ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a`.
Erzeugt laut Metadaten 27.09.2026, 08:29:16.179427 UTC; rechnerisches Ende
08:29:08.840 UTC. Handelsbeginn 18.01.2026, 20:00 UTC. Vorlauf ab 10.08.2025.

Die Datei enthält 2.481 Preis- und gleich viele zugeordnete Flow-Punkte. Unabhängig
geprüft: keine doppelten Zeitstempel, keine 4h-Lücke, korrekte zeitliche Paarung,
endliche Zahlen und gültige OHLC-Beziehungen. **Das beweist nur die Integrität der
abgeleiteten Reihe**, nicht die Vollständigkeit oder richtige ursprüngliche
Veröffentlichungszeit jedes Börsenfeeds.

Die letzte Kerze beginnt am 27.09. um 08:00 und war beim Abruf erst 29 Minuten alt.
Das Original-Replay enthält sie absichtlich weiter. Die gemeinsame Auditbasis
entfernt sie; es bleiben 2.480 abgeschlossene Kerzen, davon 1.509 im Handelsfenster.
Die letzte davon beginnt 04:00 und schließt 08:00 UTC. Die E42-Fallanalyse erklärt
zunächst das vollständige Original einschließlich der unfertigen Schlusskerze;
ihre Buchführung und der Vergleich auf geschlossener Basis sind getrennt benannt.

| Metadatum der ursprünglichen Beschaffung | Zahl |
|---|---:|
| Preis-Kerzen | 2.481 |
| Funding-Punkte vor Zuordnung | 8.825 |
| OI-Punkte vor Zuordnung | 1.510 |
| Liquidations-Punkte vor Zuordnung | 1.511 |
| Futures-Delta-Punkte vor Zuordnung | 2.009 |
| Long-/Short-Punkte vor Zuordnung | 2.009 |
| OI-Punkte ausschließlich aus lokalem Archiv | 6 |

Die vollständigen ursprünglichen HTTP-Antworten dieser Beschaffung sind in dem
E44.5-Paket nicht enthalten. Die Zahlen oben sind gespeicherte Beschaffungsmetadaten,
keine unabhängige erneute Messung der damaligen API-Antworten.

## Welche Reihe was misst

| Reihe | Tatsächlicher Codepfad und Einheit | Zeitpunkt / wichtige Grenze |
|---|---|---|
| Preis | Binance Vision BTCUSDT Spot, 4h-OHLC | Zeitstempel bezeichnet Kerzenanfang; Schlusswerte erst vier Stunden später bekannt. USDT wird im Modell wie USD behandelt; ein Perpetual- oder anderer Börsenpreis kann abweichen. |
| Spot-CVD | Summe von `2 × takerBuyQuoteVolume − quoteVolume` aus Binance-Kerzen | Signiertes aggressives Handelsvolumen, kein Nettozufluss in Bitcoin und keine Orderbuchtiefe. Summe in Quote-Währung, im Code USD genannt. |
| Futures-CVD | Coinalyze `BTCUSDT_PERP.A`, Delta `2*bv-v`, ursprünglich Basis-/Kontraktmenge BTC | `.A` bedeutet Binance, nicht Börsenaggregat. Umrechnung mit Kerzenpreis ist für absolute Anzeige nötig; ein Schlusskurs ist nur eine Näherung für den Dollarwert sämtlicher Trades. |
| Open Interest | Coinalyze OI-Schluss in USD; ergänzend USD geteilt durch damaligen Spot-Schluss | Wert gehört zur abgeschlossenen 4h-Kerze, wird aber unter deren Anfangszeit abgelegt. BTC-Umrechnung ist ein Näherungsmaß; kein direkt beobachteter Kontraktzähler für jeden möglichen Kontrakttyp. |
| Funding | Kraken PF_XBTUSD, stündliche relative Rate ×8 | Vergleichbares 8h-Ratenäquivalent, keine tatsächlich gezahlte achtstündige Summe. Im historischen und Live-Code jeweils letzter Punkt bis Kerzenschluss. Keine Funding-Abbuchung in der Portfoliorechnung. |
| Liquidationen | Coinalyze Binance, Long-/Short-Summe pro Kerze in USD | Bereits geschehene Zwangsschließungen. Keine offenen Liquidationsmarken, keine Aussage über ungetroffene Orders oder gesamte Weltmarkt-Abdeckung. |
| Long-/Short-Verhältnis | Coinalyze Binance, prozentuale Aufteilung laut Endpunkt | Keine vollständige weltweite Netto-Position und keine direkte Prognose, wer anschließend schließen muss. |
| Kraken-OI-Ersatz | Aktueller Snapshot × Markpreis, lokale Snapshot-Historie | Anderer Markt und andere Beobachtungsfrequenz. Der normale historische Backtest bildet diesen konkreten Live-Ausfallpfad nicht nach. |
| Mehrbörsenreihen | Optionale E37-Pfade, in Live nicht aktiviert | F14/F15: Vollständigkeit und Einheitenwahl fehlerhaft; heutige Marktauswahl ist nicht automatisch historisch verfügbar gewesen. |
| On-Chain/STH | E40-Anzeige, keine aktive Einstiegsregel | Neu berechnete historische Werte sind ohne damalige Veröffentlichungs-/Revisionszeit kein zulässiger damaliger Handelsinput. |

Quellen-/Parserbelege: [`main.py`](../../engine/main.py), Funktionen
`fetch_market_data`, `fetch_funding_8h`, `fetch_oi_snapshot`;
[`coinalyze.py`](../../engine/coinalyze.py), Funktionen `oi_by_ts`, `fut_delta_by_ts`,
`liquidations_by_ts`, `long_short_by_ts`;
[`backtest.py`](../../engine/backtest.py), `build_series`.
Die externen Endpunktdokumentationen und deren Grenzen sind mit Primärlinks in
[FORSCHUNG.md](FORSCHUNG.md) verzeichnet.

## Zeitliche Kausalität

Bei bestätigten Pivots werden die rechten n Kerzen im geprüften Präfix abgewartet.
Das aktuelle Codeverfahren zeigt in dieser Gegenprobe kein vorzeitig bestätigtes
Pivot. Eine absichtliche Mutation wird erkannt. Der rückwirkend am Pivotdatum
gezeichnete Punkt darf gleichwohl nicht mit seinem späteren Bestätigungszeitpunkt
verwechselt werden.

Ein OI-Schluss unter der Anfangszeit seiner Kerze ist für ein **Signal nach deren
Schluss** grundsätzlich zulässig. Für eine angeblich früher ausgeführte Intrabar-Order
wäre derselbe Wert noch nicht vollständig bekannt. Hinzu kommen reale
Veröffentlichungs- und Abrufverzögerungen, die nicht mitgespeichert sind. F07 ist ein
anderer, eindeutig bestätigter Fehler: vor der ersten vorhandenen Beobachtung wird
deren späterer Wert in die Vergangenheit zurückgefüllt.

Die Tagesaggregation nimmt bereits den laufenden Tag mit. Im Präfixlauf sind seine
späteren Stunden nicht enthalten; das ist daher kein nachgewiesenes Verwenden des
zukünftigen endgültigen Tagesschlusses. Es ist aber kein reiner Indikator aus
abgeschlossenen Tagen und benötigt eine eindeutige Regel, insbesondere beim
Vergleich von Tageszonen und EMA-Varianten.

Ein 12-Punkte-Vergleich zweier CVD-Endstände umfasst elf Änderungen, also 44 Stunden
bei 4h-Daten. Die Anzeige „48 Stunden“ beschreibt dann zwölf Kerzen, aber nicht exakt
die Differenz zwischen deren Endständen. Dieselbe Frage betrifft das kurze
3-Punkte-/„12h“-Fenster. Dies ist kleiner als die genannten Rechenfehler, sollte
aber als Messdefinition vereinheitlicht werden.

## Fehlende, ersetzte und revidierte Daten

Futures-Delta, Liquidationen und Positionierung werden bei fehlenden Werten teils
mit null ersetzt; OI wird fortgeschrieben oder vor dem ersten Punkt rückgefüllt.
Ohne Coinalyze kann der Live-Betrieb auf Kraken-Snapshots wechseln. Solche Reihen
sehen nach erfolgreicher Zuordnung vollständig aus, obwohl sich Quelle und
Informationsgehalt unterscheiden. Ein Nullwert muss mit einem Qualitätsmerkmal
unterscheidbar sein: „wirklich keine Liquidation“ versus „keine Antwort“.

Der archivierende Code ergänzt alte Zeitpunkte, lässt aber beim Zusammenführen
neu geholte Werte über ältere gewinnen. Das verhindert einen Teil des allmählichen
Historienverlusts, speichert jedoch keine vollständige Folge von Revisionen. Ein
revidierter Wert kann den heute nachgerechneten Verlauf ändern, ohne dass der
früher bekannte Zustand aus dem aktuellen Archiv rekonstruierbar wäre.

Die Coinalyze-Historie ist begrenzt; offizielle Dokumentation nennt für Intraday-Daten
etwa 1.500–2.000 Punkte und tägliches Entfernen älterer Punkte. Ein größeres `from`
fordert deshalb nicht automatisch eine längere verfügbare Historie an. Das Audit
hat keine frisch beschafften Daten an die Stelle fehlender alter Eingaben gesetzt.

## Parität: bewiesen und nicht bewiesen

Auf den eingefrorenen abgeleiteten Daten stimmen aktuelles main und E44.5 mit
Live-Defaults exakt überein. Ebenso Neustart nach jeder Kerze und rollierender
1.300-Kerzen-Verlauf: jeweils 244 Signale. Ein simulierter 90-Tage-CVD-Neustart ändert
ein Muster, aber keines dieser Signale. Datensatz:
[live-backtest-paritaet.json](live-backtest-paritaet.json).

Diese Tests reproduzieren keine damaligen API-Ausfälle, Veröffentlichungslatenzen,
Revisionen, wechselnden Live-Konfigurationen, ausstehenden Telegram-Sendungen oder
Broker-Fills. `state.json` ist ein Engine-Zustand; er ist kein Kontoauszug und kann
eine vom Nutzer manuell weitergehaltene Position nicht bestätigen. In der
Dokumentation ist eine solche Abweichung ausdrücklich beschrieben. Der Lage-Abruf
arbeitet deshalb mit einer Annahme, nicht mit einer verifizierten Nutzerposition.

## Konkrete verbleibende Datenlücken

1. Vollständige Originaleingaben vor E44.5: Rohantworten oder unveränderliche
   abgeleitete Reihen, damalige Konfiguration, tatsächlicher Checkout-SHA und Abrufzeit.
2. Für historische Live-Parität: pro Lauf angeforderte Instrumente, Erfolg/Ausfall,
   Veröffentlichung/Empfang und Revision jedes Datenpunkts.
3. Für echte Ausführung: vorgesehener Ordertyp, Erstellungs-/Änderungszeit, bestätigte
   Fillpreise und Mengen, Gebühren, Spread, Slippage und gegebenenfalls Funding/Margin.
4. Für Intrabar-Pfade: kleinere Kerzen oder Trades/Quotes, einschließlich der
   Reihenfolge von Markenberührung, Bestätigung, Stop und Teilverkauf.
5. Für Furkans reale Bilanz: vollständige Trades, Positionsgrößen und getrennte
   Spot-/Futures-Bücher. Datumsnotizen und nachträgliche Erklärungen reichen nicht.
6. Für Heatmaps/On-Chain: der damals veröffentlichte Stand einschließlich Revisionen.
   Ein späterer Screenshot beziehungsweise heutiger historischer Indikator genügt nicht.

Die verfügbaren privaten Transkripte wurden vollständig lokal geprüft. Gespeichert
sind nur Hashes, Fundstellen und verdichtete Regeln. Es wurden keine privaten
Volltranskripte oder Originalbilder in den öffentlichen Audit-Zweig kopiert.
