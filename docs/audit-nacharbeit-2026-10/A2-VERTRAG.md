# A2-Vertrag: Flow v1

Stand: 01.10.2026. Version `a2-flow-v1`. Dieser Vertrag wurde ohne neue
Renditemessung festgelegt. Die alten R0/R1-Eingaben, Hashes, Ergebnisse und die
historischen 86 Gitterzeilen bleiben unverändert. Neue Ableitungen brauchen eigene
Dateien und Hashes. Eine API-Veröffentlichung zum damaligen Kerzenschluss ist aus
den heutigen Archiven nicht beweisbar.

## F06: CVD-Signal

Der aktuelle Muster-2-Vergleich nutzt `muster_cvd="usd"`: Im 12-Kerzen-Fenster
zählt Binance-Spot-CVD als Differenz von letztem und erstem kumulierten
USD-Wert. Aggregiertes Spot-CVD in BTC wird wie Futures-CVD Delta für Delta
mit dem Schlusskurs derselben Kerze in USD umgerechnet. Jedes
Futures-CVD-Delta in BTC wird ebenfalls mit dem Schlusskurs derselben Kerze in USD
umgerechnet und summiert. Ein Derivate-Pump verlangt positives Futures-Delta und
Spot-Delta höchstens ein Drittel davon. Die bestehende Schwelle ist ein fachlicher
Vergleich, keine nach Rendite gewählte Schwelle. Preis, OI und Funding bleiben
separate Bedingungen. Alle anderen Vorzeichenvergleiche benutzen ebenfalls
Fensterdifferenzen; der Ersatzweg ohne Futures-Daten verlangt Spot-Delta höchstens
null. Konstante Summenversätze beider CVD-Reihen ändern damit kein Muster.

`muster_cvd="alt"` bleibt für die Reproduktion älterer Ergebnisse aufrufbar.
`site/data/config.json`, `main.EVAL_DEFAULTS` und der direkte Engine-Default sind
jetzt `usd`. Die historische Backtest-Gitterbasis und ihre Panel-Zeile sind noch
`alt`; sie dürfen bis A7 nicht als Rendite der korrigierten Live-Einstellung
ausgegeben werden. A7 rechnet die festgelegten Vergleiche mit neuer Ableitung.

## F07/D02: Verfügbarkeit, Abdeckung und Entscheidungsfreigabe

Jeder von Live-/Backtest-Serienbauern erzeugte `FlowPoint` trägt für Spot-CVD,
Futures-CVD, OI in USD und BTC, Funding, Liquidationen und Long-Anteil je ein
`provenance`-Objekt: Quelle, Messzeit, angenommene Verfügbarkeitszeit,
Entscheidungszeit, Alter in Millisekunden und Abdeckung (`missing`, `observed`,
`carried`, `stale`). Die Zahl null allein belegt nie eine Messung. `missing`
bezeichnet keinen verfügbaren Wert, `stale` einen vorhandenen, aber für die
Entscheidung zu alten Wert. `observed` kann eine echte Null enthalten.

Eine Coinalyze-4h-Messung mit Kerzen-Open-Zeit `t` wird frühestens am modellierten
Kerzenschluss `t+4h` genutzt. Kraken-Snapshot und Funding tragen ihre eigene
Zeitmarke. Vor dem ersten verfügbaren OI gibt es keine Rückwärtsfüllung. Danach
ist höchstens 8h Fortschreibung erlaubt; Alter wird relativ zur angenommenen
Verfügbarkeit berechnet. Funding darf ebenfalls höchstens 8h alt sein. Ein
überschrittener Wert bleibt mit `stale` sichtbar, wird aber nicht als aktuelle
Bestätigung genutzt. Diese konservativen Fristen sind der A2-Vertrag und keine
Behauptung über die damalige API-Latenz.

Musterbedingungen, die OI, Funding oder CVD benötigen, verlangen nutzbare
Messungen. Der Long-Bestätigungszweig `funding <= 0` verlangt ausdrücklich
`observed` oder `carried`; fehlendes und veraltetes Funding liefern dort kein
positives Signal. Eine andere belegte Bestätigung (z. B. Spot-CVD) kann nach den
bestehenden ODER-Regeln weiter freigeben. Im strengen UND-Modus fehlt die
Funding-Bestätigung entsprechend. Vor erstem OI können OI-abhängige Muster nicht
freigegeben werden; bestehende reine Preis- oder anders belegte Signalwege sind
nicht pauschal gesperrt. Warmup-Kerzen werden nicht vorzeitig gehandelt, und der
Start beim ersten OI heilt nicht rückwirkend erfundene Vorlaufwerte.

Die Metadaten bleiben in `FlowPoint` und im V1-Checkpoint erhalten. Ein alter
Checkpoint ohne Metadaten wird beim Einlesen als `legacy_unverified/missing`
markiert; seine numerischen Nullen gelten nicht als nachgewiesene Messungen.
Direkt konstruierte `FlowPoint`-Testwerte behalten ihre bisherige Bedeutung als
explizit gelieferte synthetische Messungen. R0/R1-Originalzeilen ohne Metadaten
werden nicht durch neue Felder in ihren Originaldateien umgedeutet.

## Grenzen und Folgearbeit

Die Marktdatenadapter für vollständige Börsenkörbe, Einheiten und abgeschlossene
Tage sind A3. OI- und Funding-Quellzeitmarken in den eingefrorenen Daten belegen
keinen tatsächlichen damaligen Veröffentlichungszeitpunkt. Historische Renditen
werden erst A7 auf den festgelegten Konfigurationen neu gerechnet. A2 startet
keine Datensammlung und gibt keinen Live-Betrieb frei.
