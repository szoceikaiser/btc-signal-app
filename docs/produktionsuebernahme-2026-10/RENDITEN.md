# Renditeaufstellung der Prüfungen

Aus vorhandenen eingefrorenen Belegen erstellt; keine neue Strategie gerechnet oder optimiert.
Alle Werte sind Prozent, keine Jahresrenditen und keine Ergebnisse deines echten Kontos.
**H1 und H2 starten getrennt mit neuem Kapital und leerem Bestand.** Deshalb sind sie weder
zu addieren noch zu einer Gesamtrendite zu verketten. Ein Strich bedeutet fehlender bzw.
nicht durchgeführter Halbzeitnachweis, niemals 0 %. V035 bleibt ausdrücklich gesperrt.

## Etappen: Basis und E42

| Etappe / Daten / Modell | Konfiguration | Gesamt % | H1 % | H2 % |
|---|---|---:|---:|---:|
| Originalaudit / Level-Diagnose | Basis | +36,13 | +23,61 | +10,13 |
| Originalaudit / Level-Diagnose | E42 | +35,42 | +25,37 | +8,01 |
| 1 / F09 / alte Level-Simulation; ursprüngliche laufende Schlusskerze enthalten | Basis | +36,14 | — | — |
| 1 / F09 / alte Level-Simulation; ursprüngliche laufende Schlusskerze enthalten | E42 | +35,42 | — | — |
| 2 / D01 / Level-Simulation; nur geschlossene Kerzen | Basis | +36,13 | — | — |
| 2 / D01 / Level-Simulation; nur geschlossene Kerzen | E42 | +35,42 | — | — |
| 3b / Ausführung / kausal V1 | Basis | +34,31 | — | — |
| 3b / Ausführung / kausal V1 | E42 | +32,51 | — | — |
| 4 / kausal V1 | Basis | +34,19 | — | — |
| 4 / kausal V1 | E42 | +33,00 | — | — |
| 6 / kausal V1 | Basis | +34,19 | — | — |
| 6 / kausal V1 | E42 | +33,00 | — | — |
| Nach-6 R0 / V1_close_to_next_open_zero_latency | Basis | +34,19 | — | — |
| Nach-6 R0 / V1_close_to_next_open_zero_latency | E42 | +33,00 | — | — |
| Nach-6 R1 / V1_close_to_next_open_zero_latency | Basis | +33,82 | — | — |
| Nach-6 R1 / V1_close_to_next_open_zero_latency | E42 | +32,63 | — | — |
| A7/A8 R0 / kausal S0 | Basis | +34,19 | +23,84 | +8,36 |
| A7/A8 R1 / kausal S0 | Basis | +33,82 | +23,84 | +8,06 |
| A7/A8 R0 / kausal S0 | E42 | +33,00 | +23,96 | +7,29 |
| A7/A8 R1 / kausal S0 | E42 | +32,63 | +23,96 | +7,00 |

Die frühen Schritte 1/2 verwendeten noch die alte Simulation; Originalaudit und A7-Level-
Diagnose sind ebenfalls keine belegten historischen Orders. Die kausalen V1-Rechnungen ab 3b
verwenden einen anderen Ausführungs-/Rückkopplungsvertrag. Unterschiede sind daher nicht
pauschal zusätzliche oder verlorene Handelsgewinne durch eine einzelne Korrektur.

Etappe 3a legte den Vertrag fest; 5a/5b betrafen Versand und Chart. A1–A6 prüften Korrekturen
und Handfälle, ohne jeweils neue vollständige historische H1/H2-Reihen zu erzeugen.
A7 berechnete die bedingten Reihen; A8 bestätigte die Spotreihen unverändert und erneuerte
nur die betroffenen V035-Diagnosen. Die Short-Handprobe ist keine Gesamtrendite.

R0 reicht bis zum festgehaltenen Beobachtungsschluss am 27.09.2026; R1 ergänzt 13 geschlossene
4h-Kerzen bis 29.09.2026 12:00 UTC. Beide Fenster beginnen am 18.01.2026 20:00 UTC.
Die exakten halboffenen Zeitgrenzen je Lauf stehen in der Varianten-CSV. Die Grenzen der
ursprünglichen Hälften und der auf 4h ausgerichteten späteren Hälften sind nicht identisch.

## Alle ursprünglichen Konfigurationen: aktuelles kausales S0-Modell

S0: 0,1 % Gebühr je Fill, kein zusätzlicher Slippage-Aufschlag, simulierte Ausführung am
nächsten 4h-Open. Historische API-Verfügbarkeit und tatsächliche Fills bleiben unbewiesen.
86 eindeutige Konfigurationen einschließlich V035; S004 ist der Alias von V000.
Die alten Parameterbezeichnungen bleiben zur Zuordnung erhalten; A2 übersetzt `muster_cvd=alt`
im korrigierten Modell zu `usd`. Die ausgeschriebene Änderung steht relativ zum Original-V000.

| ID | Änderung | R0 Gesamt % | R0 H1 % | R0 H2 % | R1 Gesamt % | R1 H1 % | R1 H2 % |
|---|---|---:|---:|---:|---:|---:|---:|
| V000 | Basis | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V001 | rest_halten=true | +28,29 | +15,26 | +11,31 | +27,93 | +15,26 | +11,00 |
| V002 | verkauf_faktor=0.67 | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V003 | rest_halten=true, verkauf_faktor=0.67 | +28,29 | +15,26 | +11,31 | +27,93 | +15,26 | +11,00 |
| V004 | ausbruch_ruecktest=true | +33,00 | +23,96 | +7,29 | +32,63 | +23,96 | +7,00 |
| V005 | rest_halten=true, ausbruch_ruecktest=true | +25,50 | +14,80 | +9,32 | +25,15 | +14,80 | +9,02 |
| V006 | ausbruch_ruecktest=true, verkauf_faktor=0.67 | +33,00 | +23,96 | +7,29 | +32,63 | +23,96 | +7,00 |
| V007 | rest_halten=true, ausbruch_ruecktest=true, verkauf_faktor=0.67 | +25,50 | +14,80 | +9,32 | +25,15 | +14,80 | +9,02 |
| V008 | trail_stop=false, high_exit=off | +34,92 | +21,82 | +10,75 | +34,47 | +21,82 | +10,38 |
| V009 | high_exit=off | +35,27 | +21,82 | +11,04 | +34,82 | +21,82 | +10,67 |
| V010 | trail_stop=false | +34,31 | +23,84 | +8,46 | +33,94 | +23,84 | +8,16 |
| V011 | trail_stop=false, high_exit=off, ausbruch_ruecktest=true | +36,90 | +22,62 | +11,65 | +36,45 | +22,62 | +11,28 |
| V012 | high_exit=off, ausbruch_ruecktest=true | +37,96 | +22,62 | +12,51 | +37,50 | +22,62 | +12,13 |
| V013 | trail_stop=false, ausbruch_ruecktest=true | +32,51 | +23,96 | +6,90 | +32,14 | +23,96 | +6,60 |
| V014 | stop_rueckeroberung=0, bein_richtung=auto, zonen_nachziehen=false | +23,99 | +19,03 | +4,17 | +23,65 | +19,03 | +3,88 |
| V015 | stop_rueckeroberung=0, bein_richtung=auto | +21,37 | +18,12 | +2,75 | +21,03 | +18,12 | +2,47 |
| V016 | stop_rueckeroberung=0, zonen_nachziehen=false | +31,36 | +19,79 | +9,66 | +31,00 | +19,79 | +9,35 |
| V017 | stop_rueckeroberung=0 | +32,07 | +22,11 | +8,16 | +31,71 | +22,11 | +7,86 |
| V018 | bein_richtung=auto, zonen_nachziehen=false | +24,71 | +19,50 | +4,36 | +24,36 | +19,50 | +4,07 |
| V019 | bein_richtung=auto | +22,07 | +18,58 | +2,94 | +21,73 | +18,58 | +2,65 |
| V020 | zonen_nachziehen=false | +29,27 | +17,67 | +9,86 | +28,91 | +17,67 | +9,55 |
| V021 | flush_entry=off, buy_ladder=false, liq_entry=off | +13,81 | +13,93 | -0,11 | +13,68 | +13,93 | -0,22 |
| V022 | flush_entry=off, buy_ladder=false | +15,00 | +15,18 | -0,16 | +14,68 | +15,18 | -0,43 |
| V023 | buy_ladder=false, liq_entry=off | +28,78 | +18,89 | +8,32 | +28,64 | +18,89 | +8,21 |
| V024 | buy_ladder=false | +34,02 | +23,17 | +8,81 | +33,64 | +23,17 | +8,51 |
| V025 | flush_entry=off, liq_entry=off | +19,11 | +19,92 | -0,67 | +18,99 | +19,92 | -0,77 |
| V026 | flush_entry=off | +17,63 | +17,53 | +0,08 | +17,30 | +17,53 | -0,19 |
| V027 | liq_entry=off | +34,80 | +25,49 | +7,42 | +34,65 | +25,49 | +7,31 |
| V028 | muster_oi=btc | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V029 | muster_cvd=usd | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V030 | muster_cvd=usd, muster_oi=btc | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V031 | muster_oi=btc, ausbruch_ruecktest=true | +33,18 | +23,96 | +7,44 | +32,81 | +23,96 | +7,14 |
| V032 | muster_cvd=usd, ausbruch_ruecktest=true | +33,00 | +23,96 | +7,29 | +32,63 | +23,96 | +7,00 |
| V033 | muster_cvd=usd, muster_oi=btc, ausbruch_ruecktest=true | +33,18 | +23,96 | +7,44 | +32,81 | +23,96 | +7,14 |
| V034 | bias_long=false | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 | +0,00 |
| V035 | bias_short=true — GESPERRT F02 | — | — | — | — | — | — |
| V036 | flush_entry=t1 | +25,82 | +22,48 | +2,72 | +25,47 | +22,48 | +2,44 |
| V037 | tp_ladder=false | +34,56 | +24,91 | +7,73 | +34,19 | +24,91 | +7,43 |
| V038 | trend_filter=true | +11,27 | +7,15 | +3,85 | +10,97 | +7,15 | +3,56 |
| V039 | trend_ema=50 | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V040 | strict_confirm=true | +27,20 | +23,70 | +2,83 | +27,06 | +23,70 | +2,72 |
| V041 | confluence=true | +15,08 | +8,25 | +6,31 | +15,08 | +8,25 | +6,31 |
| V042 | conditional_stop=true | +35,49 | +21,55 | +11,47 | +35,11 | +21,55 | +11,16 |
| V043 | release_stale_rest=true | +32,96 | +22,71 | +8,36 | +32,59 | +22,71 | +8,06 |
| V044 | liq_exit=spike | +30,75 | +19,60 | +9,32 | +30,30 | +19,60 | +8,95 |
| V045 | liq_exit=zone | +33,53 | +26,60 | +5,47 | +33,22 | +26,60 | +5,23 |
| V046 | liq_exit=both | +33,25 | +26,58 | +5,27 | +32,94 | +26,58 | +5,03 |
| V047 | high_exit=weak | +33,45 | +22,03 | +9,36 | +33,06 | +22,03 | +9,04 |
| V048 | liq_entry=filter | +28,73 | +19,04 | +8,14 | +28,59 | +19,04 | +8,03 |
| V049 | block_unhealthy=true | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V050 | muster5_entry=true | +35,87 | +23,79 | +9,76 | +35,49 | +23,79 | +9,45 |
| V051 | muster5_halten=leiter | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V052 | muster5_halten=alle | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V053 | stop_puffer_pct=0.005 | +36,67 | +22,61 | +11,47 | +36,29 | +22,61 | +11,16 |
| V054 | stop_rueckeroberung=3 | +34,49 | +23,91 | +8,54 | +34,12 | +23,91 | +8,24 |
| V055 | stop_auf_docht=true | +31,92 | +23,37 | +6,93 | +31,55 | +23,37 | +6,64 |
| V056 | confirm_t1=true | +38,27 | +23,57 | +11,89 | +37,79 | +23,57 | +11,51 |
| V057 | cooldown_h=48 | +30,66 | +20,57 | +8,36 | +30,29 | +20,57 | +8,06 |
| V058 | cooldown_h=48.0 | +30,66 | +20,57 | +8,36 | +30,29 | +20,57 | +8,06 |
| V059 | min_stop_pct=0.0 | +18,26 | +17,59 | +0,57 | +17,94 | +17,59 | +0,29 |
| V060 | no_flip=false | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V061 | freeze_targets=true | +29,61 | +20,71 | +7,37 | +29,25 | +20,71 | +7,07 |
| V062 | min_bein_pct=0.0 | +27,81 | +20,31 | +6,23 | +27,45 | +20,31 | +5,94 |
| V063 | bein_wahl=groesstes | +13,61 | +14,93 | -1,15 | +13,30 | +14,93 | -1,42 |
| V064 | be_im_plus=true | +4,84 | +1,94 | +2,84 | +4,80 | +1,94 | +2,80 |
| V065 | widerstand_exit=on | +30,92 | +21,28 | +7,94 | +30,68 | +21,28 | +7,75 |
| V066 | neustart_mit_rest=false | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V067 | zonen_1d=true | +28,35 | +28,13 | +0,24 | +27,99 | +28,76 | -0,17 |
| V068 | pivot_n_1d=8 | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V069 | pivot_n_1d=12 | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V070 | ampel_filter=klein | +29,90 | +22,84 | +5,75 | +29,54 | +22,84 | +5,45 |
| V071 | ampel_filter=gross | +34,25 | +24,95 | +7,44 | +33,99 | +24,95 | +7,23 |
| V072 | ampel_filter=immer | +24,21 | +18,86 | +4,50 | +24,04 | +18,86 | +4,36 |
| V073 | high_exit_hist=live | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V074 | ruecktest_fenster=6 | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| V075 | zonen_1d=true, pivot_n_1d=8 | +16,98 | +20,85 | -3,20 | +16,66 | +20,85 | -3,47 |
| V076 | zonen_1d=true, pivot_n_1d=12 | +14,92 | +22,58 | -6,25 | +14,60 | +22,58 | -6,51 |
| V077 | trend_filter=true, trend_ema=50 | +9,27 | +4,61 | +4,45 | +8,97 | +4,61 | +4,16 |
| V078 | ausbruch_ruecktest=true, ruecktest_fenster=6 | +33,56 | +24,48 | +7,29 | +33,19 | +24,48 | +7,00 |
| S000 | pivot_n=3 | +18,66 | +8,13 | +9,74 | +18,31 | +8,13 | +9,42 |
| S001 | pivot_n=3, k_atr=3.0 | +18,66 | +8,13 | +9,74 | +18,31 | +8,13 | +9,42 |
| S002 | pivot_n=4 | +34,67 | +25,31 | +7,47 | +34,32 | +25,31 | +7,19 |
| S003 | pivot_n=4, k_atr=3.0 | +34,67 | +25,31 | +7,47 | +34,32 | +25,31 | +7,19 |
| S005 | k_atr=3.0 | +34,19 | +23,84 | +8,36 | +33,82 | +23,84 | +8,06 |
| S006 | pivot_n=6 | +38,19 | +20,87 | +14,33 | +37,81 | +20,87 | +14,01 |
| S007 | pivot_n=6, k_atr=3.0 | +38,19 | +20,87 | +14,33 | +37,81 | +20,87 | +14,01 |

## Ausführung und Kosten: feste Basis/E42-Paare

Für S1–S4 wurden Gesamtfenster und Drittel gerechnet, keine zusätzlichen H1/H2-Reihen.
Die Halbzeitergebnisse aus S0 werden nicht auf diese Szenarien übertragen.

| Daten | Szenario | Basis gesamt % | E42 gesamt % | E42 minus Basis pp |
|---|---|---:|---:|---:|
| R0 | S0 | +34,19 | +33,00 | -1,19 |
| R0 | S1 | +28,52 | +26,78 | -1,74 |
| R0 | S2 | +8,15 | +4,67 | -3,48 |
| R0 | S3 | +27,20 | +28,37 | +1,18 |
| R0 | S4 | +8,38 | +7,82 | -0,56 |
| R1 | S0 | +33,82 | +32,63 | -1,19 |
| R1 | S1 | +28,14 | +26,40 | -1,74 |
| R1 | S2 | +7,75 | +4,28 | -3,47 |
| R1 | S3 | +26,76 | +27,93 | +1,17 |
| R1 | S4 | +7,92 | +7,36 | -0,56 |

Die genauen Kosten-/Latenzverträge stehen in [Nach-6 plan.json](../nach-6/plan.json).
Keine Gitterzeile erreicht im korrigierten Modell die alte Schwelle von +1 Prozentpunkt
gegen die Basis in beiden getrennten Hälften. Einzelne höhere Gesamtwerte sind keine
Freigabe. Beide Hälften wurden zuvor zur Entwicklung verwendet; es gibt keinen
unabhängigen Zukunftsnachweis oder eine vollständige Korrektur für alle früheren Suchen.

## Weitere Aufstellungen und Quellen

- [Alle Modellfamilien und Szenarien als CSV](RENDITEN-VARIANTEN.csv): ursprüngliche Level-Diagnose, korrigierte Level-Diagnose und kausale S0–S4-Reihen getrennt.
- [Alle gemessenen Etappenzeilen als CSV](RENDITEN-ETAPPEN.csv): einschließlich weiterer F09/D01-Zeilen und Kostenfälle.
- [Frühere Entwicklungsentscheidungen E1–E44.6](../audit-nacharbeit-2026-10/A7-M01-M02-BEWERTUNG.md): 76 Entscheidungen mit damaliger Basis und damaligen Ergebnissen. Nicht archivierte frühere Hälften werden nicht erfunden.
- [Maschinenlesbare Aufstellung und Quellhashes](RENDITEN.json).
- [A8-Endregister](../audit-nacharbeit-2026-10/REGISTER.md).

Diese Aufstellung dient der Nachvollziehbarkeit; sie entscheidet keine neue Einstellung und aktiviert nichts.
