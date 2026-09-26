# Bauplan E24 — Chart zeigt, was Telegram sagt · Beteiligung auf der Webseite

**Auftrag Kaiser, 28.08.2026:** *„zu vorschlag 1: baue es ein, möchte es mir aber anschauen
und wenn es mir nicht gefällt (da vielleicht zu viele linien, bringt mich durcheinander)
dann soll es ausgeschaltet und der ursprung wiederhergestellt werden. zu vorschlag 2:
umsetzen"*

Ausgelöst durch zwei Beobachtungen von ihm: Die Beteiligungs-Kennzahl aus E22 fehlt auf der
Webseite, und der Telegram-Plan nennt Marken, die im Chart nicht zu sehen sind.

## Diagnose (28.08.2026, aus dem laufenden Zustand)

Position LONG, 65 % investiert, Einstand 78.807 $.

**Kein Fehler:** K1 im Chart (78.409 $) ist der *erste* Kauf am 0.5-Level, der Einstand im
Plan (78.807 $) der *Durchschnitt* aus drei Käufen — 25 % bei 78.409, 20 % bei 79.089,
20 % bei 79.024. Zwei verschiedene Größen, beide richtig.

**Fehler:** Fünf Marken aus dem Plan fehlen im Chart, weil er sie aus einer zweiten,
eigenen Rechnung zieht:

| Plan-Marke | Preis | im Chart |
|---|---|---|
| Nachkauf Liquidationszone | 79.369 $ | nein |
| Nachkauf Liquidationszone | 78.469 $ | nein |
| Teilgewinn kurz unter dem letzten Hoch | 80.866 $ | nein |
| Teilgewinn Zwischenziel Ext. 0.8 | 82.214 $ | nein |
| Teilgewinn Zwischenziel Ext. 0.9 | 82.787 $ | nein |

Der Einstand hat ebenfalls keine Linie.

## Soll-Zustand

**Grundsatz: eine Quelle.** Was der Chart als Handlungsmarke zeigt, kommt aus `state.plan` —
demselben Objekt, aus dem die Telegram-Nachricht gebaut wird. Keine zweite Rechnung, die
auseinanderlaufen kann. Dasselbe für die Beteiligung: sie wird einmal im Backend gerechnet
und steht in `backtest.json`; Bericht und Webseite lesen nur ab.

Die Fib-Linien bleiben, sie zeigen die *Struktur* (wo die Zonen liegen). Die Plan-Linien
zeigen die *Handlung* (was die Engine dort tut). Verschiedene Farben, verschiedene Strichart.

## Etappen

- **E24.1** `beteiligung` in `simulate()` ins pnl-Dict; Bericht liest daraus statt selbst
  zu rechnen · Status: FERTIG (28.08.2026)
- **E24.2** Monatstabelle auf der Webseite: Spalten „Bitcoin" und „davon eingefangen",
  darunter die beiden Kennzahlen · Status: FERTIG (28.08.2026)
- **E24.3** Chart zeichnet die Plan-Marken, mit Umschalter · Status: FERTIG (28.08.2026)

## Kaisers Rückfahrkarte (E24.3)

Er will es sehen und notfalls zurück. Deshalb **ein Umschalter direkt im Chart**, nicht in
`config.json`: ein Klick, sofort sichtbar, kein Commit, kein Warten auf den nächsten
Engine-Lauf. Der Zustand bleibt im Browser gemerkt (`localStorage`), gilt also nur für sein
Gerät und stört niemanden sonst.

Default **an** — er will es ja zuerst anschauen.

**Vollständiger Rückbau**, falls der Umschalter ihm nicht reicht: `site/index.html` auf den
Stand vor dem E24.3-Commit zurücksetzen. Der Commit fasst genau diese Änderung und nichts
anderes, damit ein `git revert` sauber durchgeht. Die Commit-Nummer steht nach dem Bau im
Etappenplan unter E24.

## Was bewusst NICHT gemacht wird

- **Keine Änderung an der Engine-Logik.** E24 ist reine Anzeige — kein Signal ändert sich,
  keine Regel, kein Backtest nötig.
- **Keine Plan-Linien ohne Position.** Ohne offene Position gibt es keinen Plan; dann bleibt
  es bei der Zonen-Vorschau wie bisher.
- **Die Fib-Linien werden nicht entfernt**, auch wo sie sich mit Plan-Marken überschneiden
  (0.786, Ziel 1.0, Ziel 1.618). Sie sagen etwas anderes aus. Falls Kaiser die Linienflut
  stört, ist der Umschalter die Antwort — nicht das stille Weglassen von Struktur.
