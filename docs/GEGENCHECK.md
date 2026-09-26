# Gegencheck (E2): Kaisers notierte Trigger vs. Strategie-Spezifikation

> **WICHTIGER NACHTRAG 28.07.2026 — Punkt 4 der Konsequenzen unten ist WIDERLEGT.**
> Das Ziel „≥70 % dieser Trigger reproduzieren" hat das Projekt monatelang in die falsche
> Richtung gelenkt. In E15 wurden dieselben Trigger-Listen erstmals durch die
> P&L-Simulation geschickt: Sie hätten im Messzeitraum **Geld verloren**
> (−7,3 % im kurzen, −19,7 % im langen Fenster, Spanne je nach Tranchen-Annahme
> −23,7 % bis +0,5 %). Damit ist erklärt, warum über Wochen **jeder** Mechanismus, der
> die Trefferquote hob, Rendite kostete — fünf auf der Verkaufs-, vier auf der
> Einstiegsseite.
>
> **Die Analyse unten bleibt richtig und wertvoll:** Furkans Termine liegen tatsächlich an
> Golden Pockets, Extensions und Strukturbrüchen — die Strategie-Spezifikation erklärt sie
> gut. Nur als *Optimierungsziel* taugen die Termine nicht. Recall beschreibt Ähnlichkeit,
> er misst keinen Erfolg.
>
> Fairnesshalber: Furkan hat Buy & Hold um 11 Punkte geschlagen (−19,7 % gegen −30,5 %).
> Seine Methode hat geleistet, wofür sie gedacht ist — weniger verlieren als der Markt.

Datenbasis: Binance BTCUSDT Tageskerzen 01.09.2025–02.05.2026 (öffentliche API).
Methode: Jeder notierte Kauf-/Verkaufstag wurde gegen lokale Hochs/Tiefs, Fib-Retracements
(0.5 / 0.618–0.65 / 0.786) und Extension-Ziele (1.0 / 1.618) des jeweils letzten
signifikanten Impulses geprüft. Stand: 2026-07-22.

## Ergebnis: Die Strategie-Spezifikation erklärt die Trigger-Daten sehr gut

### Exakte Treffer (stärkste Belege)

| Datum | Notiert als | Befund |
|---|---|---|
| **08.01.2026** | Kauf | Tagestief 89.311 — Golden Pocket 89.563–89.294 des Impulses 86.650→94.765. **Im Video selbst gezeichnet (Frame 17:55).** Perfekter GP-Kauf. |
| **06.01.2026** | Kauf | Tief 91.263 ≈ 0.5-Level (~90.7k) desselben Impulses → „erste Order am 0.5" — exakt Regel 6.1/KAUF 1. |
| **14.01.2026** | Verkauf | Extension 1.0: 89.3 + (94.79−86.65) ≈ 97.4k. Tageshoch 14.01: **97.924**. Teilgewinn fast punktgenau am 1:1-Ziel. |
| **29.–30.10.2025** | Nachkäufe | GP des Impulses 102.0k→116.4k = 107.0–107.5k. Tagestiefs 109.2k/106.3k — Kern-+Nachkauf in/unter der Zone. |
| **02.–03.10.2025** | Verkäufe | Extension 1.0 des Sep-Impulses (107.3→117.9→108.6) = 119.2k. Hochs 121.0k/122.2k — Teilgewinne am 1:1-Ziel. |
| **10.10.2025** | Kauf (+Verkauf) | Flash-Crash-Tag (Tief 102.000 nach 122.5k): Muster 4 „Capitulation/Flush + Reset" wie im Lehrbuch. Kauf in den Flush. |
| **21.11.2025** | Nachkauf | Tief 80.600 = DAS lokale Bottom der Nov-Korrektur; Ladder 17.11 (92.2k) → 20.11 (86.6k) → 21.11 (80.6k), danach +12 % in 7 Tagen. |
| **08.–22.04.2026** | 4 Verkäufe | Gestaffelte Teilgewinne 71.1k → 74.1k → 77.1k → 78.2k in die April-Rally (Top 79.5k am 22.04.) — „nie all out" in Reinform. |

### Verkäufe an Abwärtstagen = Stoplosses (bestätigt die Stop-Regel)

25.01. (86.1k), 02.02. (74.6k), 16.10. (107.4k), 12.11. (100.8k), 17.12. (85.3k), 23.02.
(63.9k, 2 Tranchen): Alles Tage, an denen die Struktur brach (Schluss unter 0.786 bzw.
Swing-Tief). Beispiel: Käufe 29.–31.01. (84.6/84.3/78.7k) wurden am 02.02. gestoppt —
BTC fiel danach auf 60.000. Der Stop hat das Muster „sauber ausgestoppt statt
durchgehalten" — exakt Regel 6.1/STOPLOSS.

### Tage mit Kauf UND Verkauf (25.09., 10.10., 04.11., 06.01., 28.02.)
Konsistente Lesart: Rotationstage — Teilgewinn/Stop der Altposition + Neueinstieg in den
Flush (Muster 4) bzw. an der neuen Fib-Zone. Passt zur Tranchen-Logik (nie all in/all out).

## Quantitative Zusammenfassung

- 20 Kauf-Tage: 13 lagen ≤3 % über dem Tiefsten Kurs der Folgewoche bzw. direkt an
  lokalen Böden/Fib-Zonen; die übrigen 7 waren frühe Ladder-Tranchen, deren Serie durch
  notierte Stops (Verkaufsliste) beendet wurde — d. h. auch die „Fehlkäufe" folgen dem System.
- 26 Verkaufs-Tage: 17 an lokalen Hochs/Extension-Zielen (Teilgewinne), 9 an
  Strukturbrüchen (Stops). Kein einziger Trigger widerspricht der Spezifikation.

## Konsequenzen für E4 (Backtest-Kalibrierung)

1. Tranchen-Ladder bestätigt: Einstiege oft über 2–4 Tage verteilt (27.–30.10., 29.–31.01.,
   17.–21.11.) → Signal-Engine muss NACHKAUF-Stufen unterhalb der Erstzone aktiv anbieten.
2. Stops sind Tagesschluss-basiert plausibel; 4h-Schluss als Default beibehalten, 1D als
   konservative Variante testen.
3. Extension 1.0 ist das primäre Teilgewinn-Ziel (mehrfach fast punktgenau), 1.618 selten
   erreicht → Gewichtung 40/40/Rest bestätigt.
4. Kaisers Datenreihe dient als Referenz-Set: Der Backtest in E4 soll ≥70 % dieser Trigger
   (±1 Tag) reproduzieren, ohne übermäßig viele Zusatzsignale zu erzeugen.

## Offene Frage an Kaiser (nicht blockierend)

Die doppelten Einträge (23.02., 28.02. je 2×) und die Kauf+Verkauf-Tage: Waren das
tatsächlich mehrere Tranchen bzw. Rotationen am selben Tag? Falls du es anders notiert
hattest (z. B. Short-Eröffnungen), bitte kurz sagen — ändert nur die Backtest-Bewertung,
nicht die Strategie.
