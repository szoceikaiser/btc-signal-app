# Anleitung: Heatmap-Test (kostenlos, deine Augen als Messinstrument)

**Die Frage, die wir beantworten:** Wenn die App einen Teilverkauf meldet — lag zu diesem
Zeitpunkt die große Liquiditäts-Ansammlung (Liquidations-Cluster) **über** unserem
Verkaufspreis? Dann hätte Warten mehr gebracht, und eine echte Heatmap wäre ihr Geld wert.
Lag sie **auf oder unter** unserem Preis, war der Verkauf richtig und wir brauchen sie nicht.

Das lässt sich nicht rückwirkend messen — historische Heatmaps gibt es nicht zu kaufen.
Deshalb sammeln wir 4 bis 5 Beobachtungen im Vorwärtsgang. Dein Aufwand pro Beobachtung:
etwa 30 Sekunden. Die Auswertung mache ich.

**Kosten: 0 €.** Kein Abo, keine Anmeldung nötig (Coinank geht ohne Konto).

---

## Einmal vorbereiten

Der Ordner ist schon angelegt:

```
C:\Users\oeztu\BTC-Trading\heatmap-test\
```

Der liegt **außerhalb** von `signal-app`, also wird dort nichts auf GitHub hochgeladen.
Die Screenshots bleiben auf deinem Rechner.

Leg dir diesen Link als Favorit an — Heatmap, ohne Login:
**https://coinank.com/chart/derivatives/liq-heat-map/btcusdt/1w**

(Alternative, falls du ein Velo-Konto hast: velo.xyz → Chart → Liquidations. Furkan nutzt
im Video Velo. Für den Test reicht Coinank.)

---

## Der Ablauf (wenn eine Telegram-Nachricht kommt)

Ausgelöst wird der Test durch eine **Teilverkaufs-Nachricht**. Das sind die mit:

- 🟡 `TEILVERKAUF Leiter` (Zwischenziel)
- 🟠 `TEILVERKAUF 1 (Extension 1.0)`
- 🟠 `TEILVERKAUF 2 (Extension 1.618)`

Kauf-Signale und Stops sind für diesen Test **nicht** interessant — die kannst du ignorieren.

1. **Möglichst zeitnah** (am besten innerhalb einer Stunde) den Heatmap-Link öffnen.
   Wichtig: Die Heatmap verändert sich laufend. Ein Screenshot von morgen früh ist für
   eine Nachricht von heute Abend wertlos.
2. Ansicht **1 Woche** (`1w`) wählen — dann sieht man die Cluster über und unter dem Kurs.
3. **Screenshot machen** (Windows: `Windows-Taste + Umschalt + S`, Bereich ziehen).
   Auf dem Bild müssen zu sehen sein:
   - die **Preisachse** (die Zahlen rechts oder links)
   - die **aktuelle Kurslinie**
   - die farbigen Cluster **oberhalb** des Kurses
4. Screenshot in den Ordner `heatmap-test` speichern. **Der Dateiname ist egal** — Windows
   schreibt Datum und Uhrzeit hinein, und ich kann das Änderungsdatum der Datei lesen.
5. Fertig. Nichts eintragen, nichts rechnen.

**Kontrollpunkt:** Im Ordner liegt eine `.png`-Datei, auf der du die Preiszahlen lesen kannst.
Wenn du sie nicht lesen kannst, kann ich es auch nicht — dann noch einmal größer abziehen.

---

## Nach 4 bis 5 Screenshots

Sag mir einfach **„Heatmap-Screenshots sind drin"**. Dann mache ich Folgendes:

1. Ich lese die Bilder und notiere, wo die Cluster lagen.
2. Ich hole die passenden Signale aus dem Repo (`site/data/signals.json`) — dort steht,
   zu welchem Preis und an welchem Fib-Ziel verkauft wurde. Das musst du nicht abtippen.
3. Ich hole die Kerzen danach und schaue, **wie weit der Kurs wirklich noch gelaufen ist**.
4. Ergebnis: Bei wie vielen der Beobachtungen hätte Warten auf das Cluster mehr gebracht?

**Danach die Entscheidung:**
- Cluster lag meistens höher **und** der Kurs ist auch dorthin gelaufen → die Idee hat
  Substanz. Dann bauen wir die manuellen Zonen (du trägst die Niveaus in `config.json` ein,
  die Engine nutzt sie) — immer noch ohne Abo.
- Cluster lag auf oder unter unserem Verkaufspreis → Thema erledigt, du hast dir
  199–699 $ im Monat gespart. Auch das ist ein Ergebnis.

---

## Wenn gerade keine Signale kommen

Möglich — die Engine hing bis zuletzt im Zustand TP2 fest (siehe E9.9/E9.10). Sobald
`trail_stop` in `site/data/config.json` auf `true` steht, löst sich das beim nächsten
Rücksetzer und es kommen wieder Signale. Erfahrungswert aus dem Backtest: Teilverkäufe
etwa alle 3 bis 4 Tage. Für 4 bis 5 Beobachtungen also grob zwei Wochen.

Kein Stress: Wenn du eine Nachricht verpasst hast, überspring sie einfach. Lieber vier
saubere, zeitnahe Screenshots als zehn alte.
