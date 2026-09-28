# Vorfestlegung der ergänzenden Strukturprüfung

28.09.2026, nach Kenntnis des 79-Zeilen-Gitters, **vor Berechnung dieses Zusatzes**.
Anlass ist die vollständige Abdeckung der frühen E4-Entscheidung: Der automatische
Vergleich aus dem heutigen Backtest-Gitter enthält keine abweichenden Werte für
`pivot_n` und `k_atr`. Die ursprüngliche Kalibrierung ist in
`docs/ETAPPENPLAN.md:103` dokumentiert: **n=3/4/5/6 × k=2/3**, acht Kombinationen.
Sie optimierte damals Datumsnähe zu Handelsnotizen, nicht unabhängige Nettorendite.

Diese exakt acht Kombinationen werden als vollständiges 4×2-Gitter **S000–S007**
erneut untersucht; n=5/k=2 ist die bereits gemessene heutige Basis V000. Es kommen
somit sieben eindeutige Konfigurationen hinzu. Alle übrigen 43 Handelsparameter
bleiben auf dem festgehaltenen Live-Stand. Keine Kopplung an die beobachtete
E42/Hochverkauf-Wechselwirkung, keine Zwischenwerte oder zusätzliche Pivotweiten.

Hypothese: Die frühe Wahl könnte auf dem heutigen Parameterverbund eine andere
Wirkung haben; ein günstiger Vergleich beim Erkennen bekannter Handelsdaten ist
keine Renditevalidierung. Die OR-Verknüpfung des ATR-Kriteriums mit absoluten
Bein-Schwellen kann einen Teil der k-Änderungen wirkungslos machen. Das wird als
Ergebnis ausgewiesen, nicht durch Nachjustieren weiterer Schwellen umgangen.

Daten: unveränderte E44.5-Eingaben mit SHA-256
`ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a`;
D01 entfernen, F09 im unabhängigen Losbuch korrigieren. Dieselben vier
Ausführungs-/Kostenmodelle und zwei Hälften wie im Hauptgitter. Kennzahlen:
Rendite, Schluss-Drawdown, Kosten, Orders, Kapitalbindung, Hälften,
verzinster Vorteil ohne jeweils einen Monat, Kostenempfindlichkeit.

Ein neuer explorativer Kandidat benötigt mindestens **+2 Prozentpunkte in beiden
Hälften**, höchstens einen Punkt tieferen vergleichbar definierten Drawdown und
positiven Vorteil ohne jeden einzelnen Monat. Bestätigte technische Fehler und
fehlende unabhängige Daten verhindern weiterhin eine Aktivierungsfreigabe.
Alle Zeilen werden berichtet. Die Ergänzung ist keine Reproduktion des frühen E4-
Laufs und wird nicht rückwirkend dem ersten 79-Zeilen-Plan zugerechnet.
