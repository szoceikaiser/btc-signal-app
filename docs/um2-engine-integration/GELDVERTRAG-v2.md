# Geldvertrag V1-exact-budget-v2

Offline Spot, V1 und i+2. Ersetzt die Budgetarithmetik von cash-observable-v1. UM2-/M5-Regeln und Parameter unverändert. Keine automatische Migration, keine Broker-Schrittweitenlösung.

## Maßgebliche Rechnung

Kapital, Gebühr, deploy_pct und deklarierte Tranche bedeuten die endliche Dezimalschreibweise der Eingabe (`str(value)`). Beispielsweise 75 und 25 sind exakt 75/100 und 25/100. `100-64.4` als bereits berechneter Float bezeichnet dagegen 35.599999999999994: ohne zusätzliche Eingabesemantik darf dieser Wert nicht zu 35.6 umgedeutet werden. Die Strategie selbst liefert dieselben Parameter und Tranchensignale wie zuvor.

Intern speichern rationale Zahlen sämtliche Geldoperationen ohne Präzisionskontext, Rundung oder Cash-Clamping. Cash = Anfangskapital + Nettoverkaufserlöse − Bruttokaufbudgets. Im neuen flachen Zyklus wird das Budget = Cash × deploy_pct. Verkäufe im bestehenden Zyklus erhöhen verfügbares Cash, ohne den Zyklusnenner zu ersetzen. Angefordert = Zyklusbudget × deklarierter Anteil / 100; reserviert = min(angefordert, Cash − Summe offener Reservierungen). Jede Reservierung gehört genau einer Order. Nullbudget endet bei der Planung ohne Fill. Freigabe und Ablauf entfernen nur diese Reservierung, nie Cash.

Die Gebühr beim Kauf ist exakt Bruttobudget × Gebührensatz; beim Verkauf exakt verkaufte BTC × ausgeführter Preis × Gebührensatz. Der Preis bleibt der bestehende Float-Ausführungspreis aus tatsächlichem Open und Slippage; seine Dezimalschreibweise ist die Geldschnittstelle. Der Verkaufserlös wird aus der tatsächlich verkauften BTC-Menge und diesem Preis exakt hergeleitet.

## Konvertierung zu BTC und Ausgabe

BTC-Inventar, Losverwaltung und Strategie bleiben im bestehenden IEEE-Float-Modell. Die exakte Kaufmenge (Budget − Gebühr) / Ausführungspreis wird einmal auf Float gerundet. Kein positiver Betrag wird pauschal gekappt. Wenn diese Menge null wird oder keinen darstellbaren BTC-Gesamtzuwachs erzeugt, bleibt die Order ohne Gebühr und ohne Fillzustand; Cash und Lose bleiben erhalten. Eine echte winzige Wallet kann weiterhin handeln.

Der signed `quantity_rounding_usd`-Beleg je Kauf ist exakt Budget − Gebühr − decimal(tatsächliche Float-BTC) × decimal(Ausführungspreis). Er wird kumuliert ausgewiesen, nicht als weiteres verfügbares Cash erfunden oder still abgebucht. Das dokumentiert die verbleibende BTC-Konvertierung des Simulationsmodells. Geldbetrag, Gebühr und Reservierung bleiben davon unabhängig exakt. Die bestehende A7/F09-Abwicklung numerischer BTC-Kohortenabschlüsse bleibt erhalten; sie ist keine neue USD-Toleranz.

Float-Cash, Budget, Gebühr und Reservierung in den bisherigen Ausgabefeldern sind lediglich gerundete Ansichten. `money` in Snapshots, Endergebnis und Checkpoint enthält kanonische rationale Strings einschließlich Anfangskapital, Ausgaben, Nettoerlösen, Gebühren, Konvertierungsdifferenzen, Zyklusbudget und offenen Reservierungen. Ausgegebenes Available-Cash wird aus der exakten Differenz konvertiert, nie durch Subtraktion gerundeter Ansichten bestimmt.

## Neustart und unabhängige Kontrolle

Buchversion 2 verlangt vollständige präzise Zusatzfelder, die neue Semantik und identische gerundete Ansichten. Checkpoints früherer Geldsemantik werden zurückgewiesen; ein gespeicherter Float-Vorzustand wird nicht in einen exakten historischen Zustand umetikettiert. Initialbestände bleiben ausschließlich explizite synthetische/offline Eingaben mit eigener Anfangskapitalannahme.

Unabhängige Prüfer müssen Geld aus Anfangskapital und Ereignisabsichten herleiten, akzeptierte und abgelehnte Orders kontrollieren und zusätzlich Gebühren, BTC/Lose, Zustände, Equity und Risiko prüfen. Geldvertragsentscheidungen verwenden keine numerische Toleranz. Numerische Toleranzen bei Float-Risiko-/Losansichten legitimieren keine Order.
