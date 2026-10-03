# Nächster eigener Auftrag: Etappe 5a

Empfehlung **GPT-6 Sol, Aufwand hoch**. Keine automatische Modellumstellung und
kein Start dieser Etappe durch die Dokumentation. Exakte Abschluss-SHA von Etappe 4
steht in `audit-backups/4-abschluss-<Kurz-SHA>/ABSCHLUSS.json` und im Abschlusschat.

```text
Bearbeite ausschließlich Etappe 5a am Repository szoceikaiser/btc-signal-app:
Telegram-Zustellung mit dauerhafter Versandliste und Wiederanlauf (Audit F13).
Antworte auf Deutsch, kurze Zwischenmeldungen. Arbeite bis zum geprüften und
gesicherten Abschluss. Routineentscheidungen selbst lösen; fachliche Auswahlfragen
nur mit konkretem Gegenfall und Folgen stellen. Keine Folgeetappe vorziehen.

Ausgangspunkt ist der exakt gesicherte Etappe-4-Abschlusscommit auf
codex/etappe-4-bestand-stop, Arbeitsbaum
C:\Users\oeztu\BTC-Trading\etappe-4-work.
Übernimm die exakte SHA aus dem Abschlusschat bzw. der lokalen ABSCHLUSS.json;
nicht blind den neuesten Zweig-HEAD oder main verwenden.
C:\Users\oeztu\BTC-Trading ist das private Backup-Repo: dort nichts committen.

Lies zuerst wissens-layer/00_STAND.md, den jüngsten Abschnitt von
wissens-layer/02_status/UEBERGABE.md, docs/nacharbeit-2026-09-28/ETAPPEN.md,
F03-F04-F05-F10-VERTRAG.md, ETAPPE-4-ABSCHLUSS.md und F01-F12-VERTRAG.md
im selben Dokumentenordner sowie die lokale ABSCHLUSS.json. Prüfe Remotes,
Zweige, Arbeitsbäume und bestehende Änderungen vor Schreibzugriffen. Lege einen
eigenen Zweig und Arbeitsbaum direkt vom exakten Etappe-4-Abschluss an.
Keine neueren main-/E44.4-/E44.5-Commits übernehmen.

Lies im unabhängigen Audit audit-work, codex/audit-2026-09-27,
ccf2b01c0578346f325261e72445b7375a9ac706, gezielt F13 und die zugehörigen Proben.
Kein Gesamtaudit. Prüfe die Produktionspfade main.py und telegram_notify.py.
Definiere vor Umsetzung den Vertrag für stabile Nachrichtenidentität,
dauerhafte Versandabsicht, Zustellbestätigung, Wiederholung und Neustart.
Unterscheide sicher fehlgeschlagen von unklar zugestellt, etwa Timeout nach
Annahme durch Telegram. Keine unbelegte Exactly-once-Garantie behaupten.
Historische Signale nicht blind erneut senden oder Zustands-/Positionshistorie
zurücksetzen. Reale Nachrichten sind in dieser Etappe nicht freigegeben.

Erhalte F09/D01 und den bestätigten V1-Vertrag: Schlusswissen zum direkt nächsten
zulässigen 4h-Open, Exitpriorität, Cash/BTC/Reservierungen, echte Fill-Rückkopplung,
0,1 % Gebühr, Slippage-Szenarien 0/0,1/0,5 %, Schluss-DD plus obere Intrabar-Grenze.
Erhalte Etappe 4: Restlose/Kosten, monotone Long-Stop-Grenze, gemeinsamen Plan,
Positionsschema 2 und V1-Checkpointschema 1. Signalreferenz, simulierte Fills und
unbekannter manueller Live-Bestand bleiben getrennt. Bereits bestätigte Regeln
nicht erneut abfragen. Keine neuen DD-Schwellen oder Strategiegitter.

Reproduziere F13 netzfrei. Erreiche die betroffenen Produktionszweige vor
Sabotagen. Prüfe u.a. Ablehnung, Timeout, Prozessabbruch vor/nach Speicherung,
Neustart, mehrere Nachrichten und bereits bestätigte Zustellung. Alle bisherigen
676 Tests erhalten oder jede notwendige Änderung einzeln begründen. Kein echter
Telegram-/Broker-Aufruf; keine Orders, Live-Schalter, Deployments, gewöhnlichen
GitHub-Backtest-Workflows oder Push/Merge nach main. F17/Chart bleibt Etappe 5b;
V2, Shorts/Margin/Funding, E41.6 und andere Befunde bleiben getrennt.

Dokumentiere Vertrag, Umsetzung, Prüfungen und verbleibende Zustellgrenzen.
Aktualisiere Kurzstand, Etappen und Übergabe. Prüfe Workflow-Auslöser vor Push;
automatische Unit-Tests auf eigenem Zweig sind erlaubt. Sichere den eigenen
GitHub-Zweig, Remote-HEAD und CI zur exakten Abschluss-SHA, danach lokales
Abschlussbundle und ZIP samt geprüfter Wiederherstellung.
Sicherungstag sicherung/vor-audit-korrekturen-2026-09-28 auf
469be65f65327a3b6abf2794ceba09c1fe0de9e2, Originale und private Volltranskripte
unverändert lassen; keine privaten Volltranskripte hochladen.

Liefere Bericht, Tests/Gegenproben, Grenzen, Zweig/Commit, Sicherungspfad sowie
einen direkt kopierbaren Startprompt und Modell-/Aufwandsempfehlung für die
nächste getrennte Etappe. Beende dann 5a. Keine Folgeetappe automatisch starten.
```
