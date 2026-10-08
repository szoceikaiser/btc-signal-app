# UM2-Budgetkorrektur v2 — lokale Rückgabe

N-UM2-01 ist in der Budgetursache korrigiert: endliche dezimale Eingabebeträge, Anteile, Gebühren, Erlöse und Reservierungen werden intern exakt rational gerechnet. 75 % plus 25 % desselben Budgets lassen exakt null Cash, ohne Mindestorder oder Cash-Clamping. Der dritte Kauf wird bereits bei der Planung abgelehnt, kein Nachkaufzähler verbraucht. Das Darstellbarkeitsgate bleibt Zusatzschutz. Echte kleine Guthaben und echte dezimal erklärte Teilreste bleiben erhalten. BTC-Konvertierungsdifferenzen sind explizit je Fill und kumuliert ausgewiesen.

P-UM2-02 ist geschlossen: zwei unabhängige Geldprüfungen (rational und Decimal mit Inexact-Trap, BTC-Rundung zusätzlich per ganzzahligem Mittelpunktbeweis) erzwingen zulässige Annahmen UND Ablehnungen. Sie benutzen keine Engine-Budget-/Inventarhelfer. Beide finden den verbotenen angenommenen Fill im vollständigen alten C02-S0-Tape unter neuer Semantik und den dritten Kauf im sauberen 75-/25-%-Fall. Kohorten-, Gebühren-, Equity-, beide Intrabar-Risiken und Monatsmarken werden zusätzlich mit den additiv kopierten unabhängigen Vorgängerprüfern rekonstruiert. Deren Float-Toleranzen erlauben keine Geldvertragsentscheidung; die vorgeschalteten Regeln prüfen Geld exakt.

## Nachweise und Reichweite

- `REPRODUCED-BEFORE.json`: beide Fehler vor der Engineänderung reproduziert.
- `CHECKER-COUNTEREXAMPLES-AFTER.json`: beide verbotenen Fälle werden nach der Korrektur aus dem richtigen fachlichen Grund erkannt, nicht bloß wegen fehlender Metadaten.
- `NATIVE-SAVED-PREFIX-WITNESSES.json`: K057-S1 und C02-S0 neu aus sauberem Anfangskapital anhand gespeicherter Buchabsichten aufgebaut; beanstandete Order hat exakt null Budget. Kein alter Float-Vorzustand wurde als neuer präziser Zustand etikettiert.
- `SAVED-125-BUDGET-HISTORIES.json`: 125 Operationen aus 107 gespeicherten Läufen, sämtliche nötigen Geldvorgeschichten ab Anfangskapital rekonstruiert. Alle 125 hatten unter den aufgezeichneten Absichten ein erschöpftes Budget. Nach früherer Abweichung bleiben spätere alte Absichten/Verkaufsquantitäten bedingte Eingaben. Das ist ausdrücklich keine korrigierte Strategie aller 107 Läufe oder K057.
- `FULL-CHECKERS-REAL-TINY.json`: echte winzige Verkaufserlöse und Wiederanlage bestehen beide vollständigen Prüfer. Synthetische Daten sind markiert.
- `EFFECTS-AND-STATES.json` und `POLICY-TRANSITIONS.json`: erster Zahlenunterschied je Lauf, jede geänderte Policy-Order, Folgewirkungen und unabhängige Fill-Rückmeldung/Nachkauf-/TP-Zähler. Vollständige alte/neue geänderte Fills stehen komprimiert neben jedem Run-Receipt.

## Begrenzter Wirkungsvergleich

Genau **20 neue historische Vollfensterstarts**, ausschließlich C05/S006/V000/C02 je S0–S4. Keine Halbläufe, keine K057-Strategie, keine Suche. Zusammen mit den 40 des ersten Integrationsauftrags sind es 60, getrennt gezählt. Code vor Start 1 fest gepinnt; alle 20 Rohresultate und Receipts einmalig erstellt. Sechs identische eingefrorene Eingaben, 1551 handelbare 4h-Bars, Start 1768766400000, Schluss 1791100800000, 10000 USD, 0,1 % Gebühr, unveränderte Konfigurationen/Slippage/Offsets. Kein Datenabruf.

Alle vollständigen Signalfolgen sind exakt gleich zu den ursprünglichen UM2-Tapes und der bisherigen Integrationsstufe. Gegenüber UM2 entfallen nur die drei bekannten C02-Kleinstfills (S0/S2/S3); gegenüber cash-observable-v1 keine weiteren ausgeführten Käufe/Verkäufe. Außerdem entfallen falsche winzige Cash-Shortfall-/Teilfüllungsmeldungen, auch bei einigen der anderen Kandidaten. C02/S3 reserviert die budgetlose Order gar nicht mehr: eine unnötige i+2-Wartekerze und deren leere Fillrückmeldung entfallen; die zusätzliche normale Close-Auswertung erzeugt kein anderes Signal. Das ist eine tatsächliche Ablaufänderung, keine durch Toleranz versteckte Gleichheit.

Die ersten sonstigen Unterschiede sind korrekt gerundete BTC-Konvertierungen oder exakte Gebühren/Verkaufserlöse an den dokumentierten ersten Ereignissen. Folgende Budgets, Loswerte, Gebühren und Equity propagieren diese Änderungen. Größte absolute Endwert-/Equitydifferenz **2,1827872842550278e-11 USD**. Keine materielle unerwartete Wirkung in diesen 20 Fenstern. Kein Beleg für unveränderte Pfade außerhalb dieser vier Kandidaten.

Endwerte in USD (bedingte vier Vergleiche, keine neue 137er-Rangfolge):

| Kandidat | S0 | S1 | S2 | S3 | S4 |
|---|---:|---:|---:|---:|---:|
| C05-UM2 | 14103.81223005 | 13612.00321170 | 11810.88478581 | 13834.91401096 | 12093.21884910 |
| S006-UM2 | 13964.66434938 | 13491.72923963 | 11755.50577723 | 13484.28677084 | 11850.13290385 |
| V000-UM2 | 13649.13942948 | 13082.27500934 | 11041.56989399 | 12693.00926315 | 10840.29498092 |
| C02-UM2 | 14195.78352478 | 13669.72857074 | 11754.56428542 | 12804.49836290 | 11036.16772555 |

## Regression und Zustand

842 Engine-Testfunktionen bestanden; darunter 21 einzelne native UM2-/M5-Gatefälle im bestehenden Wrapper. 8 neue gezielte Budgettests mit 8 gefangenen fachlichen Sabotagen; alle bisherigen 34 UM2-Einzelfälle mit gefangenen Sabotagen erhalten (11 Fehlervarianten). Drei Checker-Regressionsgruppen mit kohärenten illegalen Ausführungen/Ablehnungen, vier direkte Checker-Sabotagen sowie 6 Statistiktests und 15 N6-Sabotagen bestanden. Alte fachliche historische Erwartungen wurden nicht umgeschrieben.

Explizit geprüft: mehrere Reservierungen, Teilfüllung auch bei auf 1 gerundetem Quotienten, Ablauf, Verkäufe und Wiederkäufe im selben Zyklus, Zykluswechsel, E42, echte winzige Guthaben, kein zweifaches Ausgeben derselben Reservierung. V1 und i+2 verwenden dieselbe Geldsemantik. Vollständiger i+2-Neustart wurde ergänzt, inklusive gespeicherter Absicht, Wissenspräfix, Geld, Lose und Risiko. Beide Wege bestehen JSON-Neustartgleichheit. Buchversion 2 und V1-exact-budget-v2 weisen alte/invollständige Checkpoints zurück. Keine automatische Migration realer Positionen.

Die unabhängige Zustandsprüfung kontrolliert jede Fill-Aktionsrückmeldung, Cash/BTC und die diskreten Nachkauf-/TP-Zähler samt Neustart/Reset aus den Fillereignissen. Sie ist keine zweite Implementierung der Mustererkennung. Native Gates und deren akzeptierte Äquivalenz bleiben die unveränderte Grundlage; hier wurde die native Vorstufe nicht erneut historisch gerechnet.

Erstläufe bleiben als Logs erhalten: drei alte Tests betrafen direkte Cash-Injektion, alte Float-Restbehandlung und Wertgleichheit des neuen Geldobjekts. Diese wurden am dokumentierten Vertrag ausgerichtet und durch neue eigenständige Budget-/Gegenproben abgesichert. Die alte ergänzende Quote `100-64.4` ist als Float tatsächlich 35.599999999999994; explizites 35.6 erschöpft das Budget, die abweichende deklarierte Quote lässt dagegen nachweislich echtes 6e-13 USD stehen. Keine permissive Provenienzänderung.

## Unveränderte Grenzen und nächste Abnahme

C05 und S006 bleiben bytegleich inaktiv. C05-SHA a99be30ae26a753f9734fbe2d67ac49f33e090a691904336421742f92420f787; S006-SHA 231875a451857d9c553665f8c06f8a768349d353a23ed1912249f6d6e7d74096. C05: pivot_n=6 und muster5_entry=true, CVD usd. Der frühere Minimax-Abstand 55,38 USD zu S006 ist keine unabhängige Bestätigung.

Hauptchat soll Geldvertrag, Originalgegenbelege, 125 bedingte Budgethistorien, beide Richtungen der Prüfer, Policy-Übergänge und frischen Restore prüfen. Hauptplan wurde nicht als abgenommen markiert. Kein Push, main-Merge, PR, Dispatch, Deployment, Pages, Telegram, Broker, Secret-/Datenabruf, Collector, Kauf oder Livewechsel. T1/volle Historie, A8, P3-Zustell-/Storeschutz, aktive Site-/Runtime-/Store-Konfiguration bleiben erhalten. Alle zehn Workflows einschließlich workflow_run nur gelesen; branchgebundene Online-CI bleibt gesondert offen.

Vier Aprillücken, unbekannter Warmup, modellierte Datenverfügbarkeit, mindestens 94 frühere Suchen und fehlende unabhängige Zukunftsprobe bleiben Grenzen. Broker-Minima/Schrittweiten, echte Fills, P3/D3 und ausdrückliches P4 bleiben spätere Gates. Keine Livefreigabe und kein garantierter Mehrertrag. Kein Folgeprompt erstellt, kein Chat oder Nachricht erzeugt.
