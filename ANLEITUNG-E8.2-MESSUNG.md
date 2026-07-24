# Anleitung: E8.2 messen — gestaffelte Teilgewinne (Verkaufs-Leiter)

Was neu ist: Die Engine kann jetzt in **kleinen Stufen** in die Stärke verkaufen
(Zwischenziele bei Extension **0.8** und **0.9**, je 15 %, VOR dem 1.0-Ziel) —
statt nur einmal am 1.0-Ziel. Das bildet Furkans mehrtägige Verkaufs-Leitern nach
(z. B. 08.–22.04.). Ziel: mehr seiner Verkaufstage treffen (bisher der schwächste
Wert: nur 29 %).

**Wichtig:** Die Leiter ist vorerst **abgeschaltet** (Default). Erst der Backtest
entscheidet, ob sie eingeschaltet wird — genau wie beim letzten Mal (E8.1b). Diese
Anleitung führt die Messung durch. Bitte nach jedem Schritt kurz Rückmeldung geben.

---

## Schritt 1 — Code hochladen (dein üblicher Push)

In deinem Ordner `C:\Users\oeztu\BTC-Trading\signal-app` (Git Bash / Terminal):

```
git pull --no-rebase
git add -A
git commit -m "E8.2: gestaffelte Teilgewinne (tp_ladder) + Backtest-Grid"
git push
```

**Kontrollpunkt 1:** Der `git push` endet ohne rote Fehlermeldung (typisch:
`main -> main`). Falls „index.lock" klemmt: Datei
`signal-app\.git\index.lock` per `del` löschen und `git add`/`commit`/`push`
wiederholen.

---

## Schritt 2 — Backtest starten

1. Öffne [Actions → Backtest](https://github.com/szoceikaiser/btc-signal-app/actions/workflows/backtest.yml)
2. Rechts **Run workflow** → grüner Knopf **Run workflow**
3. Warten: 5–15 Minuten (Seite ab und zu neu laden, bis der Lauf grün ✓ ist)

**Kontrollpunkt 2:** Der Lauf hat einen grünen Haken. Falls rot: den Lauf öffnen,
mir den Text aus dem fehlgeschlagenen Schritt schicken.

---

## Schritt 3 — Ergebnis ablesen

Öffne [`BACKTEST.md`](https://github.com/szoceikaiser/btc-signal-app/blob/main/BACKTEST.md).
Die Tabelle hat jetzt eine neue Spalte **Leiter** (an/aus). Vergleiche die Zeilen
mit `pivot_n = 5` (unser Standard):

| worauf achten | Bedeutung |
|---|---|
| **Recall** | Ähnlichkeit zu Furkans Terminen — steigt die Verkaufsseite mit Leiter „an"? |
| **Präzision** | Anteil sinnvoller Signale — sollte NICHT stark fallen |
| **Rendite** | Gewinn/Verlust der Simulation (das echte Geld-Maß, NICHT Recall) |

**Merke:** Recall ist *Ähnlichkeit*, kein Gewinn. Der Gewinn steht allein in der
Rendite-Spalte bzw. der Simulations-Zeile (10.000 € → …).

---

## Schritt 4 — mir Bescheid geben (Rückmelde-Punkt)

Schick mir bitte einfach die **Zeile „beste Kombination"** aus `BACKTEST.md` und die
zwei `pivot_n = 5`-Zeilen (Leiter aus / Leiter an). Daraus entscheide ich:

- Leiter bringt mehr Verkaufs-Recall **ohne** Rendite/Präzision zu verschlechtern
  → ich setze `tp_ladder = True` als neuen Standard (kleiner Push von mir/dir).
- Leiter verschlechtert etwas → bleibt abgeschaltet, Parameter bleibt für später
  erhalten (wie damals `flush_entry`).

So oder so: Die Kalibrierungsschleife wird sauber geschlossen und dokumentiert.
