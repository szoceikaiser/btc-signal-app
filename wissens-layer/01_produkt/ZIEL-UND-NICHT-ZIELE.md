# Ziel und Nicht-Ziele

> Stand: 26.09.2026. Maßgeblich für die Strategie selbst bleibt `docs\STRATEGIE.md`.

## Wofür es dieses Projekt gibt

Kaiser handelt Bitcoin nach der Order-Flow-Strategie von Furkan Yildirim. Die
Strategie funktioniert, aber sie verlangt, im richtigen Moment am Chart zu sitzen:
Die entscheidenden Kaufzonen werden oft nur für Stunden berührt, häufig mitten in
der Nacht. Die Engine übernimmt das Beobachten und meldet sich, wenn eine Marke
erreicht wird — und, seit E17/E22, schon vorher, damit die Order als Limit
hinterlegt werden kann.

## Der Nutzer

Ein einziger: Kaiser. Er ist **nicht IT-affin**. Daraus folgt für alles, was gebaut
wird: Anleitungen als fertige Befehlsblöcke, ein Schritt nach dem anderen, nach jedem
Schritt Rückmeldung abwarten. Fehlermeldungen sollen erklären, was zu tun ist, nicht
was intern schiefging.

## Produktprinzipien

1. **Signale, keine Ausführung.** Die Engine handelt nicht selbst.
2. **Alles ist ein Schalter, Default aus.** Jeder neue Mechanismus wird zuschaltbar
   gebaut und per Backtest gemessen, bevor er live geht.
3. **Nachvollziehbar statt clever.** Zu jedem Signal gehört ein Grund im Klartext.
   Zu jedem Schalter steht in `config.json`, was gemessen wurde und warum er an ist.
4. **Marken vorher, nicht hinterher.** Furkan legt Zonen im Voraus fest und arbeitet
   sie ab. Deshalb Vorschau und Plan — nicht nur Signale nach Kerzenschluss.
5. **Nichts kostet Geld.** Alle Datenquellen sind kostenlos, das Hosting ebenfalls.
6. **Anzeigen statt handeln, wenn die Messung nichts hergibt.** Der dritte Weg dieses
   Projekts, dreimal gegangen (Lagezeile, Ampel, STH-Kostenbasis): Eine Beobachtung,
   die als Regel Rendite kostet oder nicht prüfbar ist, wird nicht verworfen — sie
   wird **angezeigt**. Das kostet nichts und lässt die Entscheidung bei Kaiser, so wie
   Furkan sie bei sich lässt. Jede Anzeige sagt in der Nachricht selbst, dass sie
   nichts auslöst.
7. **Entscheidungsregeln stehen vor der Messung fest — samt Ausschalt-Regel.** Wer
   einen Schalter live schaltet, legt vorher schriftlich fest, was ihn wieder
   ausschalten würde, mit einer Rauschgrenze (siehe `04_konventionen/ARBEITSREGELN.md`).
   Der Backtest-Bericht prüft diese Regel selbst und schreibt sein Urteil hin.

## Bewusste Nicht-Ziele

| Nicht-Ziel | Warum |
|---|---|
| **Kein automatisches Trading** | Sicherheit. API-Schlüssel mit Handelsrechten auf kostenlosem Hosting wären ein Risiko. Kaiser platziert die Orders selbst |
| **Keine Gewinnversprechen** | Der Backtest ist eine Simulation, kein Versprechen. Recall misst Ähnlichkeit zu Furkans Terminen, nicht Ertrag |
| **Keine Anlageberatung** | Die Engine und die Unterlagen sagen nie, ob eine laufende Position zu halten oder zu schließen ist. Sie beschreiben Marken und Messungen |
| **Keine starren Golden-Pocket-Levels** | Die Zonen entstehen dynamisch aus der Swing-Struktur — ausdrückliche Anforderung |
| **Keine Fremdpakete** | Die Engine läuft mit der Python-Standardbibliothek. Kein `pandas`, kein `numpy`, kein `pytest`. Grund: die Umgebung erreicht PyPI nicht zuverlässig |
| **Keine Überanpassung** | Schwellen so lange verstellen, bis die Vergangenheit passt, ist verboten. Deshalb Fensterhalbierung, Zufallserwartungswert, Rauschgrenze und vorab festgelegte Regeln |
| **Kein zweiter Nutzer** | Keine Anmeldung, keine Mandantentrennung, keine Rechteverwaltung |
| **Kein zweites, eigenständig kaufendes System** | Ein zonenfreier Einstieg (z. B. auf Muster 5) wäre genau das. Vorgeschlagen, nicht gewollt — die Engine entscheidet an Fib-Zonen, sonst nirgends |
