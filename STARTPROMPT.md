# Startprompt für einen neuen Chat (BTC-Trading)

> **Maßgebliche Fassung.** Ältere Übergabeprompts in `docs\ETAPPENPLAN.md` (23.07.2026)
> und in früheren Fassungen von `wissens-layer\START-HIER.md` sind Zeitdokumente.
> Wer diesen Prompt ändert, ändert ihn **hier** und nirgends sonst.
>
> Stand: 26.09.2026 · Für eine KI mit Zugriff auf das Repo `btc-signal-app` auf GitHub.
> **Seit 26.09.2026 liegen Code UND Unterlagen in diesem einen Repo** (`docs\`,
> `wissens-layer\`). Das private Repo `260729-btc-trading-backup` ist nur noch ein
> Backup von Kaisers Rechner und nicht maßgeblich.
> Prüfe vor dem Einfügen nur eines: Stimmt die Testzahl unten noch (447)?

---

## Der Text zum Einfügen

```
Du arbeitest an meiner BTC-Signal-Engine. Repo: github.com/szoceikaiser/btc-signal-app
- darin liegen Code UND Unterlagen (docs\, wissens-layer\). Das Repo ist OEFFENTLICH:
keine Zugangsdaten, keine privaten Notizen, keine kompletten Video-Transkripte hinein.
Webseite: szoceikaiser.github.io/btc-signal-app

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

STAND: Letzte Live-Aenderung am Handelsverhalten ist E41 (meine Rueckeroberungs-Regel,
"stop_rueckeroberung": 1, live seit 21.09.2026). OFFEN UND WICHTIG: Die vorab
festgelegte Ausschalt-Regel dazu hat am 23.09.2026 angeschlagen (Rueckgang 1,5 statt
erlaubter 1,0 Punkte tiefer); ich habe sie bewusst ueberstimmt. Der Bericht meldet
weiter "AUSSCHALTEN". Das ist beim naechsten Backtest neu zu bewerten - Einzelheiten
in docs\PLAN-E41-STOP.md, Abschnitt "Nachmessung 23.09.2026".
NEU 26.09.2026: Gesamtpruefung docs\PRUEFUNG-2026-09-26-GESAMT.md - vier Fehler in
Muster-Erkennung und Anzeige bewiesen (A1-A4), noch nicht behoben. Vor jeder Arbeit an
Order-Flow-Mustern zuerst diesen Bericht lesen.

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

TESTS: cd engine && python3 run_tests.py -> 447 Tests, alle gruen.
Nenne die Zahl in deiner Antwort. Meldet der Laeufer WENIGER Tests und trotzdem
"0 failed", hat sich eine Datei still uebersprungen. Auf Windows vorher
PYTHONIOENCODING=utf-8 setzen. Eine Sabotage-Probe niemals mitten im Lauf abbrechen -
sie stellt die verfaelschte Datei erst am Ende wieder her.

DIE LIVE-ENGINE IST BEI JEDEM LAUF EIN NEUER PROZESS. Alles, was ueber eine Kerze
hinaus gilt, muss in site\data\state.json gespeichert und beim Start gelesen werden -
sonst tut der Backtest etwas, das live nie passiert. Pruefweg: dieselbe Kursfolge
einmal am Stueck und einmal Kerze fuer Kerze in getrennten Laeufen; Signale UND
Telegram-Meldungen muessen gleich sein.

HOCHLADEN UND MESSEN (seit 26.09.2026): DU committest und pushst selbst - aber NUR
auf einen eigenen Arbeitszweig (claude/...), nie direkt auf main. main ist die
Live-Fassung: Die Engine laeuft von dort. Auf den Zweig kommt erst, was fertig und
getestet ist; die Tests laufen bei jedem Push automatisch (Actions -> Tests). Den
Backtest (Actions -> Backtest, rund 6 Minuten) darfst du AUF DEINEM ZWEIG selbst
anstossen und den Lauf pruefen. In main zusammengefuehrt wird erst nach meinem
ausdruecklichen "Go". Vor jedem Push den neuesten Stand von main holen: Die Engine
committet alle 4 Stunden selbst. Ich hole mir den Stand auf den PC mit
stand-holen.bat nur, wenn ich dort etwas lesen will. Boersen-APIs sind aus
Arbeitsumgebungen meist gesperrt - eigene Messungen gehen nur ueber den Backtest.

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
