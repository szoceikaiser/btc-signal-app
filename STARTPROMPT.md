# Startprompt für einen neuen Chat (BTC-Trading)

> **Maßgebliche Fassung.** Ältere Übergabeprompts in `docs\ETAPPENPLAN.md` (23.07.2026)
> und in früheren Fassungen von `wissens-layer\START-HIER.md` sind Zeitdokumente.
> Wer diesen Prompt ändert, ändert ihn **hier** und nirgends sonst.
>
> Stand: 26.09.2026 · Für eine KI mit Zugriff auf das Repo `btc-signal-app` auf GitHub.
> **Seit 26.09.2026 liegen Code UND Unterlagen in diesem einen Repo** (`docs\`,
> `wissens-layer\`). Das private Repo `260729-btc-trading-backup` ist nur noch ein
> Backup von Kaisers Rechner und nicht maßgeblich.
> Prüfe vor dem Einfügen nur eines: Stimmt die Testzahl unten noch? Stand 26.09.2026:
> `main` 493 (E43.4 und E43.4b nach Kaisers Go gemerged). Kein offener Arbeitszweig.

---

## Der Text zum Einfügen

```
Du arbeitest an meiner BTC-Signal-Engine. Repo: github.com/szoceikaiser/btc-signal-app
- darin liegen Code UND Unterlagen (docs\, wissens-layer\). Das Repo ist OEFFENTLICH:
keine Zugangsdaten, keine privaten Notizen, keine kompletten Video-Transkripte hinein.
Webseite: szoceikaiser.github.io/btc-signal-app

VOR ALLEM ANDEREN: Der letzte Arbeitsstand liegt oft NICHT in main, sondern auf dem
juengsten Zweig claude/... (git fetch; git branch -r --sort=-committerdate). Ist ein
claude-Zweig neuer als main, lies die Dateien unten VON DIESEM ZWEIG und arbeite dort
weiter. Dort steht in wissens-layer\02_status\UEBERGABE.md, was zuletzt lief.

LIES ZUERST, IN DIESER REIHENFOLGE:
1. wissens-layer\00_STAND.md                      (Kurzstand, halbe Minute)
2. wissens-layer\02_status\UEBERGABE.md           (jüngster Abschnitt zuerst)
3. wissens-layer\02_status\GEMESSEN-UND-ENTSCHIEDEN.md
   -> Diese Datei verhindert, dass du etwas vorschlaegst, das schon durchgefallen ist.
4. wissens-layer\02_status\OFFENE-PUNKTE.md       (nach Nutzwert sortiert)
5. wissens-layer\04_konventionen\ARBEITSREGELN.md und BEKANNTE-PROBLEME.md
Bei Bedarf: wissens-layer\START-HIER.md, 03_architektur\UEBERBLICK.md,
docs\STRATEGIE.md, der jeweilige docs\PLAN-E*.md.
docs\ETAPPENPLAN.md ist die Chronik (128 KB) - nachschlagen, nicht am Stueck lesen.

WAS DIE ENGINE IST: Signale nach Furkan Yildirims Order-Flow-Strategie, per Telegram.
Sie handelt NICHT selbst - ich platziere die Orders von Hand. Sechs Laeufe taeglich
nach jedem 4h-Kerzenschluss (pünktlich ueber cron-job.org), plus Flush-Wache alle
15 Minuten, plus Lage-Abruf auf Knopfdruck. Python-Standardbibliothek, kein pandas,
kein pytest.

STAND: Letzte Live-Aenderungen am Handelsverhalten: E41 (Rueckeroberungs-Regel,
"stop_rueckeroberung": 1, live seit 21.09.2026) und E43.2 ("bein_richtung": "bias",
live seit 26.09.2026, Entscheidungsregel erfuellt). Die Ausschalt-Regel zu E41, die am
23.09.2026 angeschlagen hatte, schlaegt auf der neuen Live-Basis NICHT mehr an
(Backtest 26.09.2026: "Bleibt an", docs\PLAN-E41-STOP.md, "Nachmessung 26.09.2026").
Gesamtpruefung docs\PRUEFUNG-2026-09-26-GESAMT.md (Befunde A1-A4): A1 live (E43.1),
A4 repariert (E43.5), A2 gebaut und gemessen (E43.3, Schalter muster_cvd): nur 2 von
1.504 Kerzen anders, Rendite identisch, bleibt "alt". A3 gebaut und gemessen (E43.4,
Schalter muster_oi, OI in Kontrakten): 210 von 1.504 Kerzen anders, Rendite identisch,
bleibt "usd" - A3 ist aber echt (die Haelfte der Pump-Treffer beim OI kam nur vom Kurs).
Neuer Nebenbefund A5 (Teilgewinn am letzten Hoch haengt von der Laenge der Historie ab),
nicht gemessen, OFFENE-PUNKTE Punkt 8. Anzeige-Frage A2/A3 entschieden: keine getrennte
Muster-Anzeige, stattdessen zeigt die OI-Zeile im Lage-Abruf die Kontrakte neben den
Dollar (E43.4b, live seit 26.09.2026, reine Anzeige). **Naechster Schritt: E43.6**
(Nachmessungen rest_halten, strict_confirm, confirm_t1, cooldown_h; danach Muster 5):
zuerst den Bauplan-Abschnitt in docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md schreiben. Vor jeder Arbeit
an Order-Flow-Mustern zuerst den Gesamtpruefungs-Bericht und den jeweiligen
Bauplan-Abschnitt lesen.

ICH: Kaiser, nicht IT-affin. Antworte auf Deutsch, kurz, mit einem konkreten naechsten
Schritt. Befehle als fertige Bloecke, einer nach dem anderen, und warte auf meine
Rueckmeldung. Keine Fachbegriffe ohne Erklaerung. Keine Anlageberatung: sag mir nie,
ob ich eine Position halten oder schliessen soll.

DIE FUENF REGELN, DIE HIER GELTEN:
(1) Jeder neue Mechanismus wird ein Schalter in site\data\config.json, Default aus,
    mit einer Gitterzeile im Backtest. Nichts geht ohne Messung live.
(2) Zu jedem neuen Test gehoert eine Sabotage: Code absichtlich kaputt machen und
    pruefen, dass der Test rot wird. Die Proben liegen als engine\sabotage_e*.py.
    Und jeder Test weist zuerst nach, dass sein Szenario den geprueften Zweig
    ueberhaupt erreicht.
(3) Erst messen, dann behaupten. Keine Zahl nennen, die nicht nachgezaehlt ist.
(4) Ein Unterschied unter 1 Punkt Rendite ist Rauschen (gemessen: ein Tag mehr Daten
    dreht 1,0 Punkte). Jede vorab festgelegte Regel braucht eine Rauschgrenze - und,
    wenn ein Schalter live geht, eine Ausschalt-Regel, die der Bericht selbst prueft.
    Vergleiche gelten nur bei GENAU EINEM Unterschied zur Live-Zeile.
(5) Zwoelf gemessene Filter, zwoelf schlechter. Was gewirkt hat, hielt die Engine
    laenger und groesser investiert. Wer einen dreizehnten Filter vorschlaegt, erklaert
    zuerst, warum er nicht unter diese Diagnose fällt. Eine Beobachtung, die als Regel
    nichts bringt, wird ANGEZEIGT statt gehandelt - das ist hier ein etablierter Weg.

TESTS: cd engine && python3 run_tests.py -> in main 493 Tests, alle gruen.
Nenne die Zahl in deiner Antwort. Meldet der Laeufer WENIGER Tests und trotzdem
"0 failed", hat sich eine Datei still uebersprungen. Auf Windows vorher
PYTHONIOENCODING=utf-8 setzen. Eine Sabotage-Probe niemals mitten im Lauf abbrechen -
sie stellt die verfaelschte Datei erst am Ende wieder her.

DIE LIVE-ENGINE IST BEI JEDEM LAUF EIN NEUER PROZESS. Alles, was ueber eine Kerze
hinaus gilt, muss in site\data\state.json gespeichert und beim Start gelesen werden -
sonst tut der Backtest etwas, das live nie passiert. Pruefweg: dieselbe Kursfolge
einmal am Stueck und einmal Kerze fuer Kerze in getrennten Laeufen; Signale UND
Telegram-Meldungen muessen gleich sein.

HOCHLADEN UND MESSEN (seit 26.09.2026): DU committest und pushst selbst. CODE nur auf
einen eigenen Arbeitszweig (claude/...), nie direkt auf main. REINE UNTERLAGEN
(wissens-layer\, docs\, STARTPROMPT.md, PRUEFPROMPT.md) darfst du direkt in main
schreiben (mein Einverstaendnis vom 26.09.2026), damit der letzte Stand immer dort liegt. main ist die
Live-Fassung: Die Engine laeuft von dort. Auf den Zweig kommt erst, was fertig und
getestet ist; die Tests laufen bei jedem Push automatisch (Actions -> Tests). Den
Backtest (Actions -> Backtest, rund 6 Minuten) darfst du AUF DEINEM ZWEIG selbst
anstossen und den Lauf pruefen. In main zusammengefuehrt wird erst nach meinem
ausdruecklichen "Go". Vor jedem Push den neuesten Stand von main holen: Die Engine
committet alle 4 Stunden selbst. Ich hole mir den Stand auf den PC mit
stand-holen.bat nur, wenn ich dort etwas lesen will. Boersen-APIs sind aus
Arbeitsumgebungen meist gesperrt - eigene Messungen gehen nur ueber den Backtest.

ZWISCHENSTAENDE UND AUFWAND: Mein Budget kann jederzeit enden. Halte deshalb nach jeder
Etappe, vor jedem langen Lauf und nach jedem groesseren Schritt den Stand fest
(UEBERGABE.md, Bauplan-Status) und pushe ihn auf deinen Arbeitszweig. Nenne zu jedem
vorgeschlagenen Schritt den noetigen Aufwand (niedrig/mittel/hoch/maximal, siehe
ARBEITSREGELN.md, Abschnitt Budget), damit ich Tokens sparen kann.

AM ENDE JEDES SCHRITTS gibst du mir IMMER: (1) den fertigen Prompt fuer den neuen Chat
mit dem naechsten Schritt, (2) den noetigen Aufwand (Modell und Denkaufwand), (3) einen
ausdruecklichen Hinweis, WENN ich den Aufwand gegenueber jetzt aendern soll.

ARBEITSWEISE BEI GROESSEREN VORHABEN: erst einen Bauplan als docs\PLAN-E<nr>-<name>.md
schreiben (Problem mit meinem Zitat, Regel, Schwellen, betroffene Dateien, "bewusst
NICHT gemacht", Entscheidungsregel VOR der Messung), dann in Etappen schneiden, die
einzeln lieferbar sind, und nach JEDER Etappe den Status setzen sowie
wissens-layer\00_STAND.md und 02_status\UEBERGABE.md fortschreiben. Wenn dein Budget
knapp wird: die laufende Etappe fertig machen oder sauber zurueckrollen - nichts
halbfertig stehen lassen.

Sag mir zuerst in drei Saetzen, wo das Projekt steht und was du als naechsten Schritt
vorschlaegst. Fang nicht an zu bauen, bevor ich zugestimmt habe.
```

---

## Kurzprompt für eine Fortsetzung (spart Tokens)

Für einen Folgeschritt mit Aufwand **niedrig** oder **mittel** reicht dieser kurze Prompt
statt des langen oben. Die KI füllt die Zeile `AUFGABE` am Ende jedes Schritts selbst aus
und gibt Kaiser den fertigen Text.

```
Du arbeitest an meiner BTC-Signal-Engine, Repo github.com/szoceikaiser/btc-signal-app
(oeffentlich). Antworte auf Deutsch, kurz, ich bin nicht IT-affin. Keine Anlageberatung.
Lies NUR: wissens-layer\00_STAND.md, den juengsten Abschnitt von
wissens-layer\02_status\UEBERGABE.md und den genannten Bauplan. Nicht mehr.
Arbeitszweig: <ZWEIG>. Code nur dort, main erst nach meinem Go; reine Unterlagen
darfst du direkt in main schreiben. Tests: cd engine && python3 run_tests.py (<ZAHL>).
Halte den Zwischenstand fest und pushe ihn (UEBERGABE.md, Bauplan-Status).
Am Ende: fertiger Prompt fuer den naechsten Chat + noetiger Aufwand + Hinweis, ob ich
den Aufwand aendern soll.
AUFGABE: <SCHRITT, mit Verweis auf den Bauplan>
```

## Wenn die neue KI **keinen** Zugriff auf das Repo hat

Dann diese Dateien in den Chat hochladen, in dieser Reihenfolge, und den Prompt oben
mit dem Satz beginnen: *„Die Dateien liegen als Anhang, nicht im Repo."*

1. `wissens-layer\00_STAND.md`
2. `wissens-layer\02_status\UEBERGABE.md`
3. `wissens-layer\02_status\GEMESSEN-UND-ENTSCHIEDEN.md`
4. `wissens-layer\02_status\OFFENE-PUNKTE.md`
5. `wissens-layer\04_konventionen\ARBEITSREGELN.md`
6. der Bauplan des laufenden Vorhabens (z. B. `docs\PLAN-E41-STOP.md`)
7. `site\data\config.json` (die Hinweistexte sind die Begründungen)
8. bei Code-Arbeit zusätzlich die betroffene Datei aus `engine\`

Ohne Repo-Zugriff kann die KI **nicht** testen und **nicht** messen. Dann gilt: Sie
darf Vorschläge und fertige Dateien liefern, aber keine Behauptung über Testzahlen oder
Backtest-Ergebnisse aufstellen.

## Pflege dieser Datei

Ändert sich eines der folgenden Dinge, gehört es hier hinein — sonst schickt der
nächste Chat eine veraltete Lage voraus:

- die Testzahl,
- die letzte Live-Änderung am Handelsverhalten,
- eine offene Entscheidung, die eine neue Session sofort wissen muss,
- eine neue tragende Arbeitsregel.
