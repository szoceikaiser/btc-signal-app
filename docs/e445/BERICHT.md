# E44.5 — Kombinationsgitter

**Nur Messung auf dem Arbeitszweig. Keine Aktivierung, kein Merge-Go.**

K1 = E42, K2 = Verkauf-Faktor 0.67, K3 = Rest halten. Acht Ecken plus K1 mit 6 statt 12 Kerzen.
Hauptzeile: beide Haelften mindestens +1 Punkt. Erklaerungszeilen: mindestens +2 Punkte.
Dazu hoechstens 1 Punkt tieferer Rueckgang und positiver Vorsprung ohne jeden einzelnen Monat.
Monatsprobe: Summe der Monatsdifferenzen (E44.2, nicht verkettet). Robustheit entscheidet nichts.

| Variante | Rolle | Rendite % | H1 % | H2 % | Rueckgang % | Delta H1 | Delta H2 | ohne besten Monat | Regel |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| LIVE-heute +Bein in Handelsrichtung | Basis | +36.14 | +23.61 | +10.13 | -9.94 | — | — | — | keine Entscheidung |
| LIVE-heute +Rest halten (E43.6) | Erklaerung | +35.41 | +19.35 | +13.46 | -9.94 | -4.26 | +3.33 | -2.47 | nicht erfuellt |
| LIVE-heute +kleinere Verkaeufe | Erklaerung | +36.15 | +24.66 | +9.22 | -9.94 | +1.05 | -0.91 | -1.16 | nicht erfuellt |
| LIVE-heute +kleinere Verkaeufe +Rest halten | Erklaerung | +37.91 | +18.16 | +16.72 | -12.55 | -5.45 | +6.59 | -4.96 | nicht erfuellt |
| LIVE-heute +E42 | Hauptzeile | +35.93 | +25.37 | +8.42 | -9.94 | +1.76 | -1.71 | -0.83 | nicht erfuellt |
| LIVE-heute +E42 +Rest halten | Erklaerung | +34.58 | +20.51 | +11.67 | -11.13 | -3.10 | +1.54 | -2.27 | nicht erfuellt |
| LIVE-heute +E42 +kleinere Verkaeufe | Erklaerung | +34.86 | +25.25 | +7.67 | -9.94 | +1.64 | -2.46 | -2.57 | nicht erfuellt |
| LIVE-heute +E42 +kleinere Verkaeufe +Rest halten | Erklaerung | +34.67 | +17.63 | +14.49 | -13.11 | -5.98 | +4.36 | -6.47 | nicht erfuellt |
| LIVE-heute +E42 (6 Kerzen, Robustheit) | Robustheit | +36.51 | +25.90 | +8.42 | -9.94 | — | — | — | keine Entscheidung |

## Wechselwirkungen

(A+B) - A - B + Basis; positiv = zusammen besser als die Summe.

| Basis | A | B | Vollfenster | H1 | H2 |
|---|---|---|---:|---:|---:|
| LIVE-heute +Bein in Handelsrichtung | rest_halten | verkauf_faktor | +2.49 | -2.24 | +4.17 |
| LIVE-heute +Bein in Handelsrichtung | rest_halten | ausbruch_ruecktest | -0.62 | -0.60 | -0.08 |
| LIVE-heute +Bein in Handelsrichtung | verkauf_faktor | ausbruch_ruecktest | -1.08 | -1.17 | +0.16 |
| LIVE-heute +Rest halten (E43.6) | verkauf_faktor | ausbruch_ruecktest | -2.41 | -1.69 | -0.44 |
| LIVE-heute +kleinere Verkaeufe | rest_halten | ausbruch_ruecktest | -1.95 | -1.12 | -0.68 |
| LIVE-heute +E42 | rest_halten | verkauf_faktor | +1.16 | -2.76 | +3.57 |

## Alter der beobachteten Marken

Alter seit Beginn der Beobachtung beim Verkauf, nicht seit Entstehung des Pivots. Alte Marke hier: mehr als 12 Vierstundenkerzen (2 Tage). Nur Diagnose, kein neuer Filter.

| Variante | Rueckkaeufe | Alter erfasst | davon alte Marken | Maximum Kerzen |
|---|---:|---:|---:|---:|
| LIVE-heute +E42 | 16 | 16 | 2 | 74 |
| LIVE-heute +E42 +Rest halten | 11 | 11 | 1 | 15 |
| LIVE-heute +E42 +kleinere Verkaeufe | 14 | 14 | 1 | 15 |
| LIVE-heute +E42 +kleinere Verkaeufe +Rest halten | 10 | 10 | 1 | 15 |
| LIVE-heute +E42 (6 Kerzen, Robustheit) | 15 | 15 | 2 | 74 |

Bei bestandener Erklaerungszeile bleibt die inhaltliche Einordnung erforderlich; keine automatische Auswahl des Gitter-Siegers.
Ausschalt-Regel bei spaeterem Go: alte Zeile in beiden Haelften mindestens +1 Punkt besser ODER neuer Rueckgang mehr als 1 Punkt tiefer. Alte Zeile bleibt Gegenprobe.
Datenbegrenzung: ein Markt, historisches Fenster; keine Aussage ueber kuenftige Rendite.
