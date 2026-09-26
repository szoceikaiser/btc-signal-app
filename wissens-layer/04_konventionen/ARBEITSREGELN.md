# Arbeitsregeln

> Die Regeln, nach denen in diesem Projekt gearbeitet wird. Sie sind aus Fehlern
> entstanden, nicht aus Theorie — zu den meisten steht unten, welcher Fehler sie
> ausgelöst hat. Stand: 26.09.2026.

## Die fünf tragenden Regeln

### 1. Jeder neue Mechanismus wird ein Schalter, Default aus

Nichts geht ohne Messung live. Ein neuer Mechanismus bekommt einen Schalter in
`config.json` (Default `false` bzw. `0`), eine Gitterzeile im Backtest und einen
Hinweistext, der festhält, was gemessen wurde. Erst danach die Entscheidung.

### 2. Zu jedem Test gehört eine Gegenprobe

Ein Test, der auch dann grün bleibt, wenn man den Mechanismus absichtlich kaputt
macht, ist wertlos. Deshalb: nach jedem neuen Test die Logik gezielt sabotieren und
prüfen, dass der Test anschlägt. Die Proben liegen als `engine\sabotage_e*.py` dauerhaft
neben dem Code und sind jederzeit wiederholbar.

*Warum diese Regel existiert:* Mehrere Tests sind so schon durchgefallen — ein
Beteiligungs-Test prüfte nur die Hilfsfunktion statt den Weg durch `simulate()`, ein
Zähler-Test prüfte den Zustand **nach** dem Zurücksetzen der Position, und ein
Lockerungs-Test benutzte ein Szenario, in dem gar kein Stop möglich war. Alle sahen
grün aus und prüften nichts.

**Dazu gehört die Vorprobe:** Jeder Test muss zuerst nachweisen, dass sein Szenario den
geprüften Zweig überhaupt erreicht (ein `assert`, bevor die eigentliche Prüfung kommt).
Vier Mal in drei Ausbaustufen (E34, E35, E36, E36.1) war genau das der wunde Punkt.

### 3. Erst messen, dann behaupten

Keine Zahl nennen, die nicht nachgezählt ist. Keine Ursache benennen, die nicht
reproduziert wurde.

*Warum diese Regel existiert:* Sie ist mehrfach verletzt worden.
- Bei `no_flip` wurde behauptet, das Problem beträfe „2 von 202 Signalen". Tatsächlich
  waren es 16 Kerzen und 41 von 241 Signalen. Kaiser musste **dreimal** nachhaken.
- Bei `min_bein_pct` wurde behauptet, die 4h-Ebene hätte gar kein Bein gezeichnet.
  Nachgerechnet mit echten Kerzen: falsch.
- Beim Gegengeschäft in E30 lag der erste Verdacht daneben. Erst ein Suchlauf über
  konstruierte Kursverläufe fand die wirkliche Ursache.
- In E41 überzeichnete die erste Fassung der Stopliste einen Fall, weil sie den
  **Wiedereinstieg** der Engine acht Stunden später unterschlug.

### 4. Recall ist kein Gewinn — und die Rangfolge ist kein Beleg

Recall misst nur die Ähnlichkeit zu Kaisers notierten Furkan-Terminen. Und die
Platzierung im Gitter ist Zufall: Bei 67 Varianten und je 5 Plätzen in zwei
Fensterhälften liegt der Zufallserwartungswert bei 0,4 Varianten, die in **beiden**
Hälften unter den besten 5 landen. Gemessen (23.09.2026): 0. Also nur groben Hebeln
trauen (Richtung, Kaufleiter, Flush), Feinheiten nicht.

### 5. Jede vorab festgelegte Regel braucht eine Rauschgrenze — und eine Ausschalt-Regel

**Rauschgrenze:** „Besser in beiden Hälften" allein genügt nicht. Am 06.09.2026 hat
**ein einziger Tag mehr Daten** einen Unterschied von 1,0 Punkten umgedreht. Eine Regel
ohne Mindestspanne erklärt Rauschen zum Befund — genau das ist in E41 passiert
(Hälfte 2: +0,2 Punkte) und ist dort als Mangel der Regel dokumentiert. Dasselbe gilt
für Quellenvergleiche: „bester Versatz ≠ 0" ohne Mindestabstand schlägt bei einer träge
laufenden Reihe schon bei 0,01 Punkten an (E40.1).

**Ausschalt-Regel:** Wer einen Schalter live schaltet, legt **vorher** fest, was ihn
wieder ausschalten würde, und lässt den Bericht das selbst prüfen. Vorbild: der
Abschnitt „E41" in `BACKTEST.md` schreibt bei jedem Lauf „Bleibt an." oder
„AUSSCHALTEN.". Wird eine solche Meldung überstimmt, gehört das **als Überstimmung
dokumentiert** — mit Zahlen, Begründung und Kosten (so am 23.09.2026 geschehen). Die
Regel selbst wird dabei nicht abgeschwächt.

## Regeln für den Vergleich zweier Varianten

- **Genau ein Unterschied.** Zwei Zeilen, die sich in zwei Punkten unterscheiden,
  beweisen nichts. Dieser Fehler ist zweimal passiert: ältere `no_flip`- und
  `Neustart`-Zeilen liefen ohne `min_bein_pct` und wurden trotzdem verglichen.
- **Ein Messergebnis gilt nur gegen die Basis, gegen die gemessen wurde.** Nach jeder
  Live-Umstellung sind verworfene Mechanismen wieder offen. `high_exit` war fünfmal als
  „kostet Rendite" verworfen und ist heute eingeschaltet.
- **Beim Live-Schalten wandern drei Dinge mit:** `panel=True`, die Zeile „MEINE
  Einstellung ohne Flush" (darf sich nur in `flush_entry` unterscheiden) und **jede**
  Zeile „LIVE-heute + X". Tests halten alle drei fest. Am 05.09.2026 waren es vier
  Unterschiede statt einem; beim Umschalten auf E41 waren 18 Zeilen nachzuziehen.
- **Zahlen aus verschiedenen Zeitpunkten nicht mischen.** Die Rückgangsmessung wurde am
  28.08.2026 grundlegend geändert (vorher nur an Signalzeitpunkten, seither lückenlos).
  Alle Rückgangszahlen aus Berichten davor sind zu freundlich.
- **Der Fenster-Rückgang ist zwischen zwei Varianten pfadabhängig** (neu, 23.09.2026).
  Belastbar ist er für **eine** Variante über die Zeit. Beleg: B3 wartet länger als B1
  und zeigt trotzdem einen flacheren Rückgang — mehr Warten kann in der Wartephase nur
  tiefer werden, der Unterschied entsteht also erst danach, weil eine anders beendete
  Position alle folgenden Einstiege verschiebt. Wer Risiko zwischen Varianten messen
  will, braucht ein Maß **je Position** (Vorschlag E41.6).
- **Belastbar sind** der maximale Rückgang **einer** Variante über die Zeit und die
  **Beteiligungspaare** (Aufwärts/Abwärts). Steigt Aufwärts, ohne dass Abwärts
  mitsteigt, ist wirklich etwas gewonnen. Steigen beide, wurde nur das Risiko erhöht.

## Regeln für die Live-Engine

- **Jeder Lauf ist ein neuer Prozess.** Alles, was über eine Kerze hinaus gilt, muss in
  `state.json` gespeichert und beim Start gelesen werden. Der Backtest zeigt solche
  Fehler nicht, weil er am Stück rechnet.
- **Der Prüfweg dafür:** dieselbe Kursfolge einmal am Stück und einmal Kerze für Kerze
  in getrennten Läufen rechnen — Signale **und** Telegram-Meldungen müssen gleich sein.
  Genau dieser Test hat in E41 den Fehler gefunden, der den Stop nie hätte auslösen
  lassen.
- **Was die Engine nicht mehr tut, muss auch in den Nachrichten stehen.** Verspricht
  der Plan „Stop bei Kerzenschluss darunter", während die Engine eine Kerze wartet,
  widerspricht der Plan der Engine. Jede Verhaltensänderung zieht die Nachrichtentexte
  mit.
- **Anzeigen sagen, für welche Richtung sie gelten.** Die Ampel rechnete am 17.09.2026
  für einen Short, während Kaiser long war — dieselben Daten, umgekehrtes Vorzeichen.

## Zusammenarbeit mit Kaiser

- **Deutsch, kurz, mit konkretem nächsten Schritt.** Kaiser ist nicht IT-affin.
  Befehle als fertige Blöcke, einer nach dem anderen, Rückmeldung abwarten.
- **Erst planen, dann bauen.** Bei größeren Vorhaben zuerst einen Bauplan als
  Markdown-Datei ins Projekt schreiben (Muster: `docs\PLAN-E*.md`), dann in Etappen
  schneiden, die einzeln lieferbar sind. Nach jeder Etappe Status setzen — nicht am Ende.
- **Fragen, bevor etwas geändert wird**, was Kaiser gehört: bestehende Dateien,
  Ordnerstruktur, laufende Einstellungen. Dateien löschen tut Kaiser selbst.
- **Nicht überverkaufen.** Wenn eine Messung nichts hergibt, das sagen. „Kostet nichts
  und behebt einen Konstruktionsfehler" ist eine ehrliche Begründung — „bringt Rendite"
  wäre bei +0,1 Punkten gelogen.
- **Keine Anlageberatung.** Nie sagen, ob eine laufende Position zu halten oder zu
  schließen ist. Marken, Messungen und Mechanik beschreiben — die Entscheidung bleibt
  bei Kaiser.
- **Kaisers Einwände ernst nehmen.** Die größten Funde dieses Projekts kamen von ihm:
  die Gegengeschäfte, die eingefrorenen Zonen und die Rückeroberungs-Regel.
- **Der Zugangsschlüssel von Coinalyze wird Kaiser nie gezeigt** — auch nicht in Teilen.
  Er steckt als GitHub-Secret im Repo und wird dort von ihm selbst gepflegt.

## Git (umgestellt am 26.09.2026, Kaisers Wunsch)

- **Die KI committet und pusht selbst — aber nur auf einen eigenen Arbeitszweig**
  (`claude/...`), **nie direkt auf `main`**. `main` ist die Live-Fassung: Von dort laufen
  Engine, Flush-Wache und Webseite.
- **In `main` zusammengeführt wird erst nach Kaisers ausdrücklichem „Go“.** Vorher laufen
  auf dem Zweig die Tests (automatisch bei jedem Push) und, wo nötig, der Backtest
  (von Hand auf dem Zweig angestoßen).
- **Vor jedem Push den neuesten Stand von `main` holen.** Die Engine committet alle
  4 Stunden selbst (`Engine-Lauf: Zustand aktualisiert`), der Backtest ebenfalls.
- **Das Repo ist öffentlich:** keine Zugangsdaten, keine privaten Notizen, keine
  vollständigen Video-Transkripte hinein. Kurze Zitate mit Zeitmarke sind in Ordnung.
- Kaiser holt den Stand auf seinen Rechner mit `stand-holen.bat`, nur wenn er dort
  etwas lesen will. `HOCHLADEN.cmd` braucht er nur noch, wenn er selbst Dateien ändert.
- Aus einer Sandbox-Arbeitsumgebung mit gemountetem Ordner (nicht GitHub) heraus
  **keine** git-Schreibbefehle: die `index.lock` bleibt hängen. Lesen ist in Ordnung.
- Commit-Nachrichten: reines ASCII, kein Gedankenstrich — die Windows-Konsole
  zerhackt Sonderzeichen gelegentlich.
- Vor dem Push immer `git pull --rebase`, nie ein einfaches `git pull` — sonst öffnet
  sich in der Konsole ein Editor, aus dem ohne vim-Kenntnisse schwer herauszukommen ist.

## Definition of Done

Eine Aufgabe gilt erst dann als fertig, wenn:

1. Alle Tests grün sind (`cd engine && python3 run_tests.py`, aktuell **444**) — und
   die Zahl **genannt** wird. Läuft der Läufer mit weniger Tests durch und meldet
   trotzdem „0 failed", hat sich eine Datei still übersprungen.
2. Zu jedem neuen Test eine Sabotage gelaufen ist und gefangen wurde.
3. Der Bauplan (`docs\PLAN-E*.md`) und `docs\ETAPPENPLAN.md` den Status samt
   Abweichungen festhalten.
4. Bei einem neuen Schalter: Hinweistext in `config.json` mit den Messwerten **und**
   der Ausschalt-Regel.
5. Der Wissens-Layer nachgezogen ist: `00_STAND.md`, `02_status/UEBERGABE.md` und, wo
   betroffen, `GEMESSEN-UND-ENTSCHIEDEN.md` / `OFFENE-PUNKTE.md`.
6. Die Arbeit auf dem Arbeitszweig committet und gepusht ist, die Tests dort grün
   sind und Kaiser weiß, was er mit „Go“ live schaltet.
