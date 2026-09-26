# Prüfprompt — reiner Prüfdurchlauf (BTC-Trading)

> Für den Fall, dass eine **andere** KI das Projekt gegenlesen soll: nachrechnen,
> widersprechen, Lücken finden — **nichts ändern, nichts committen, nichts live
> schalten.** Ein zweites Augenpaar ist in diesem Projekt schon dreimal wertvoller
> gewesen als eine weitere Etappe.
>
> Stand: 26.09.2026. Ändert sich der Projektstand, hier die Zahlen mitziehen.

---

## Der Text zum Einfügen

```
Du machst einen PRUEFDURCHLAUF an meiner BTC-Signal-Engine. Repo:
github.com/szoceikaiser/btc-signal-app. Aendere NICHTS, committe nichts, schalte nichts live.
Ergebnis ist ein Befund, kein Umbau.

LIES: wissens-layer\00_STAND.md, dann 02_status\UEBERGABE.md,
02_status\GEMESSEN-UND-ENTSCHIEDEN.md, 02_status\OFFENE-PUNKTE.md,
04_konventionen\ARBEITSREGELN.md, 03_architektur\UEBERBLICK.md und den Bauplan des
letzten Vorhabens (derzeit docs\PLAN-E41-STOP.md). Code: engine\.
Zahlen: BACKTEST.md und site\data\config.json.

PRUEFE GENAU DIESE SIEBEN PUNKTE UND WIDERSPRICH, WO ES ETWAS ZU WIDERSPRECHEN GIBT:

1. STIMMEN DIE ZAHLEN? Jede Zahl in den Unterlagen gegen BACKTEST.md und den Code
   nachrechnen. Wo eine Zahl nicht belegt ist, sag es. Besonders: die Werte in den
   _hinweis_*-Texten in config.json.

2. STIMMT DIE LIVE-EINSTELLUNG MIT DER GEMESSENEN UEBEREIN? Genau eine Gitterzeile in
   backtest.py traegt panel=True; sie muss config.json entsprechen. Ausserdem muessen
   "MEINE Einstellung ohne Flush" und jede Zeile "LIVE-heute + X" den Live-Stand
   mittragen, sonst messen sie zwei Unterschiede statt einem.

3. PRUEFEN DIE TESTS WIRKLICH ETWAS? Suche Tests, die gruen bleiben wuerden, wenn man
   die Logik kaputt macht: leere Listen vergleichen, ein if, das nie zutrifft, ein
   Szenario, das den geprueften Zweig nicht erreicht, ein still uebersprungener Test.
   Genau diese vier Formen sind hier schon passiert. Die Sabotage-Proben
   (engine\sabotage_e*.py) darfst du laufen lassen - aber nie mitten im Lauf abbrechen.

4. WAS UEBERLEBT DEN NEUSTART NICHT? Die Live-Engine ist bei jedem Lauf ein neuer
   Prozess und liest site\data\state.json. Suche Zaehler und Merker in
   strategy_core.Position, die NICHT gespeichert werden. (Bekannt und unbehoben:
   widerstand_exits. Gibt es weitere?)

5. HAELT DIE E41-ENTSCHEIDUNG STAND? Die Rueckeroberungs-Regel ist live, ihre vorab
   festgelegte Ausschalt-Regel hat am 23.09.2026 angeschlagen und wurde von mir
   ueberstimmt. Lies die Begruendung in docs\PLAN-E41-STOP.md und sag mir ehrlich, ob
   sie traegt - auch wenn die Antwort "nein, schalte aus" lautet. Pruefe dabei das
   Argument, der Fenster-Rueckgang sei zwischen zwei Varianten pfadabhaengig.

6. WIDERSPRECHEN SICH UNTERLAGEN UND CODE? Der Wissens-Layer fasst zusammen; bei
   Widerspruch gewinnt das Original. Nenne jede Stelle, an der die Zusammenfassung
   etwas behauptet, was der Code nicht tut - und umgekehrt jede Verhaltensaenderung,
   die in den Telegram-Texten nicht nachgezogen wurde.

7. WAS FEHLT, DAS NIEMAND VERMISST? Ungeprueftes Verhalten, ein Schalter ohne
   Hinweistext, eine Datenquelle ohne Ersatzweg, eine Annahme ohne Gegenprobe.

FORM DER ANTWORT: Befunde nach Schwere sortiert. Je Befund: was ist falsch, woran man
es sieht (Datei und Zeile oder Zahl), was es praktisch bedeutet, und der kleinste
Schritt, der es behebt. Keine Umbauvorschlaege ohne Befund. Wenn ein Punkt sauber ist,
sag das in einem Satz - eine leere Liste ist auch ein Ergebnis.

Ich bin nicht IT-affin: Deutsch, kurz, ohne Fachbegriffe ohne Erklaerung.
```

---

## Was ein Prüfdurchlauf hier schon gefunden hat

Damit klar ist, warum sich das lohnt — alles echte Funde aus diesem Projekt:

- ein Test, der zwei **leere** Listen verglich und deshalb nie anschlagen konnte;
- eine Zusicherung unter einem `if`, das nie zutraf;
- ein Szenario, das den geprüften Zweig nicht erreichte (Änderung exakt 0);
- ein Test, der sich still übersprang — und **sechs Tage** jeden GitHub-Lauf rot ließ,
  während die Arbeitskopie „alles grün" meldete;
- Zähler, die einen Stop überlebten und die Position falsch weiterführten;
- ein Nachkauf, der zu einem Preis gebucht wurde, den es im Markt nie gab;
- eine Statistik, die einen Einzelfall überzeichnete, weil sie den Wiedereinstieg
  acht Stunden später unterschlug.
