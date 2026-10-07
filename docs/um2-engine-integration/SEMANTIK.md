# Lokale UM2-Engineintegration

Basis ist P3 `a7cf45d171500b3ef93bd5ca195071b419fe0dfb`; keine Aktivierung.
Die native Version `UM2-M5-v1-native` validiert beide Liquidationsseiten
in den tatsächlich genutzten Niveau-/Kaskadenfenstern. M5 verlangt nur die
Long-Seite für seine Negation. Beobachtete Null ist gültig, unbekannte,
stale, zeitlich inkonsistente, negative und nicht endliche Werte sind es nicht.
Es entstehen keine Messwerte, kein Carry-forward und kein Buchreset.
M4, Folgezweige, Filter/Boost, unabhängige Zonen und Schutzstops bleiben erhalten.

Die optionale Diagnostik in `liquidation_evidence.py` sammelt Ereignisse über
einen ContextVar. Die Entscheidung hängt nicht von aktivierter Diagnostik ab.
Es gibt keine dynamische Quelltextersetzung oder produktive Prozessadapter.

Nachweise liegen additiv unter
`audit-backups/um2-engine-integration-20261007` im übergeordneten Projekt.
Vor numerischer Änderung sind 20/20 Vollfensterläufe (C05/S006/V000/C02,
je S0–S4) einschließlich Signalen, Fills, Zuständen, Equity und Gateereignissen
exakt gleich zu den versiegelten Tapes. Zwei unabhängige Decimalprüfer
verifizieren zusätzlich Buch, Gebühren und beide OHLC-Risikopfade.
Synthetische Fixtures werden ausdrücklich als solche bezeichnet und nur in
ausgewählten positiven Handfällen mit Messprovenienz konstruiert. Die Engine
akzeptiert fehlende Liquidationsprovenienz nicht zur Schonung alter Tests.

## Numerischer Ausführungsvertrag

`V1-cash-observable-v1` prüft jeden Kauf am tatsächlichen zulässigen Open.
Wenn seine berechnete BTC-Menge keinen darstellbaren Zuwachs des vorhandenen
Float-Gesamtbestands ergibt (einschließlich Mengenunterlauf auf null), wird die
reservierte Order als `unrepresentable_btc_increment` abgelehnt. Cash, BTC und
alle Lose bleiben exakt erhalten; die eigene Reservierung wird freigegeben.
Es entstehen keine Gebühr, kein Los und keine akzeptierte Fillrückmeldung,
also auch keine verbrauchte Nachkaufstufe oder E42-Fillmarke. Eine kleinere
berechenbare Teilfüllung wird weiterhin ausgeführt, wenn ihr Zuwachs darstellbar
ist. Die Entscheidung benutzt keine Schätzung eines künftigen Openpreises.

Diese Grenze stammt ausschließlich aus der aktuellen Gleitkommadarstellung,
nicht aus einer gewählten USD-Mindestorder. Echte kleine Cash-/BTC-Reste werden
nicht gelöscht; derselbe kleine Betrag kann bei kleinem/leerem Inventar oder
einem anderen tatsächlichen Preis ausführbar sein. Eine abgelehnte Reservierung
hat bis zur Auflösung im verzögerten Modell weiterhin die bisherige Wartewirkung.
Ein Floatbuch ist weiterhin kein beliebig präzises Geldsystem und dieser Patch
beweist nicht, dass sämtliche 125 alten diagnostischen Kleinstkäufe unter jeder
Konfiguration unterdrückt würden. Er beseitigt den konkret belegten Kauf ohne
darstellbaren Gesamtmengenzuwachs. Broker-Minima/Schrittweiten sind separat offen.

Offline-Buch- und Runnercheckpoints binden die Ausführungssemantik ausdrücklich.
Alte Checkpoints ohne diese Bindung werden abgelehnt; es gibt keine automatische
Migration bestehender Positionen. Serialisierter Neustart mit gebundener Semantik
und identischem Wissenspräfix bleibt exakt reproduzierbar.
