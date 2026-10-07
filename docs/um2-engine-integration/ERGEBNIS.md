# Begrenzter lokaler Integrationsbefund

Die native UM2-/M5-Integration ist vor numerischer Änderung in 20 Vollfensterläufen
exakt zu den gespeicherten UM2-Tapes, einschließlich Gateereignissen. Danach wurden
genau dieselben 20 Läufe mit `V1-cash-observable-v1` gerechnet: insgesamt 40/40.
Rohdaten, Fenster, 10.000 USD, Parameter und S0–S4 blieben eingefroren.

C05, S006 und V000 sind in allen Szenarien exakt unverändert. C02 S1/S4 ebenfalls.
C02 S0/S2/S3 verlieren jeweils einen nicht darstellbaren Kleinstfill. Der jeweilige
Nachkaufzähler bleibt bei dessen Rückmeldung 0 statt 1. Die vollständigen
Signalfolgen bleiben auch dort identisch. Spätere Los-/Gebührenrundung und in S2
nachfolgende Budgets/Mengen ändern sich minimal: maximal 5,46e-12 USD Unterschied
in Equitymarken; Endwert S2 +3,64e-12 USD, S0/S3 unverändert. Beide unabhängigen
Decimalreplays prüfen Geld, Mengen, Gebühren, Lose und Risiken; vollständige
erste Ereignisse und Folgewirkungen sind im additiven Auditverzeichnis gesichert.

Eine zusätzliche isolierte Wiederholung der 125 diagnostischen Kleinstoperationen
aus 785 bereits gespeicherten Tapes zählt **keinen** historischen Strategielauf.
90 erfüllen das neue Ablehnungskriterium; 35 haben einen darstellbaren Zuwachs und
werden weiterhin gefüllt. Das ist ausdrücklich keine allgemeine Cashrestbereinigung
und kein Nachweis der korrigierten Rangfolge aller 137 Konfigurationen. Die numerische
Reichweite ist im Hauptchat zu beurteilen, bevor dieser Stand fachlich abgenommen wird.

C05 liegt vollständig und inaktiv in `candidates/C05-UM2.inactive.json`;
Config-SHA `a99be30ae26a753f9734fbe2d67ac49f33e090a691904336421742f92420f787`.
S006 bleibt der einfachere Vergleich. Der alte bedingte Minimaxvorsprung von
55,38 USD gegenüber S006 ist keine unabhängige Zukunftsbestätigung.

Lokale Suite: 834 Testfunktionen, darin ein Wrapper mit 21 portierten Gatefällen;
zusätzlich sechs synthetische Statistiktests, 15 N6-Mutationsproben und zwei
unabhängige Prüfer mit zehn abgewiesenen Manipulationen. Negative Erstläufe und
Präzisierungen der ausdrücklich synthetischen Fixtures sind erhalten.

Die folgenden Gates bleiben offen: aktuelle serverseitige Workflowprüfung und
separat autorisierter sicherer Push/branchgebundene Online-CI, echte Fills,
P3/D3 einschließlich echter Store-/Alarm-/Backup-Proben und ausdrückliches P4.
Keine Site-/Runtime-/Storekonfiguration oder bestehende Position wurde umgestellt.
Vier Aprillücken, unbekannter Warmup, modellierte Verfügbarkeit, mindestens 94
frühere Suchen und fehlende unabhängige Zukunftsprobe bleiben Grenzen. A8, T1,
volle Historie und P3-Zustell-/Store-Schutzregeln bleiben erhalten.
