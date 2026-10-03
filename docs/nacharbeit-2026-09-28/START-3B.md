# Startprompt für einen neuen Chat: ausschließlich Etappe 3b

Modell vor Start auf **GPT-6 Sol, Aufwand hoch** stellen. Bei einer neu auftretenden
Grundsatzfrage gezielt Astra/hoch empfehlen; nicht automatisch Modelle wechseln.
3a ist abgeschlossen; dieser Prompt startet in der jetzigen Sitzung keine Umsetzung.

```text
Bearbeite ausschließlich Etappe 3b (F01/F12) am Repository
szoceikaiser/btc-signal-app. Antworte auf Deutsch, Zwischenmeldungen kurz.
Arbeite bis zum geprüften und auf eigenem GitHub-Zweig gesicherten Abschluss.

C:\Users\oeztu\BTC-Trading ist das private Backup-Repo: dort nichts committen.
Abgeschlossene Etappe 3a:
- Arbeitsbaum C:\Users\oeztu\BTC-Trading\vertrag-3a-work
- Zweig codex/etappe-3a-ausfuehrungsvertrag
- Den exakten Abschlusscommit aus der lokalen Abschlussicherung
  audit-backups\3a-abschluss-<Kurz-SHA>\ABSCHLUSS.json bzw. dem gesicherten
  Remote-Zweig ermitteln und mit lokalem HEAD abgleichen, bevor du schreibst.
- Basis 5fabe2bae1506546fc31708ceecef2034365300f (F09 + D01), 600 Tests.
- Unabhängiger Audit: audit-work, codex/audit-2026-09-27,
  ccf2b01c0578346f325261e72445b7375a9ac706, nur gezielt lesen.
- Unveränderlicher Tag sicherung/vor-audit-korrekturen-2026-09-28 zeigt auf
  469be65f65327a3b6abf2794ceba09c1fe0de9e2. Tag weder ändern noch neu setzen.
  main kann durch unabhängige Live-Läufe weitergerückt sein.

Lies zuerst wissens-layer/00_STAND.md und den jüngsten Abschnitt von
wissens-layer/02_status/UEBERGABE.md, dann
docs/nacharbeit-2026-09-28/F01-F12-VERTRAG.md vollständig,
ETAPPEN.md, D01.md und tools/verify_3a_contract.py samt 3a-pruefung.json.
Prüfe Remotes, Zweige, Arbeitsbäume und bestehende Änderungen. Lege einen eigenen
Arbeitsbaum und Zweig vom gesicherten 3a-Abschlusscommit an; nichts von main,
E44.4 oder E44.5 übernehmen. Bestehende Änderungen erhalten.

Der Nutzer hat ausdrücklich entschieden; nicht erneut zur Auswahl stellen:
D1-A: Schluss-Signale zum Open der direkt folgenden zulässigen 4h-Kerze.
Das ist ein idealisiertes Null-Latenz-Modell, kein belegter Telegram-/Broker-Fill.
D2-A: Gesamtausstieg vor Teilstop vor Teilverkauf; bei einem ausführbaren
Verkauf im Entscheidungspaket entfällt jeder Kauf desselben Pakets.
D3: Long/Spot ohne Hebel; Schluss-Drawdown plus obere Intrabar-Risikogrenze
(untere Grenze mit ausweisen); Gebühr 0,1 % je Fill, Slippage-Szenarien
0/0,1/0,5 % je Seite. Alte DD-Schwellen nicht automatisch übertragen.

Implementiere den Vertrag V1 mit getrenntem Signalwissen, Kerzen-ID,
Entscheidungszeit, Referenzpreis, Order-/Fillzeit und Fillpreis. Kein vergangenes
Tief/Hoch darf nachträglich einen Fill liefern. Lücken zum Folge-Open buchen,
fehlendes Folge-Open ohne Fill ausweisen, Datenlücken ablehnen. Ereignis-Ledger
mit Cash, Reservierung und tatsächlichen BTC vor/nach jedem Ereignis.
Bestätigte Fills/Ablehnungen müssen vor der nächsten Entscheidung in den
simulierten Handelszustand zurückfließen. Kein bloßes Neuabrechnen alter Signale.
Keine Leiterstufe für abgelehnte Käufe/Verkäufe verbrauchen. F09-Wiederanlage,
BTC-Höchstbestände, bestehende Tranchen und D01-Zeitgrenzen erhalten.

Prüfe die 16 Handfälle unabhängig, ergänze aussagekräftige Tests für Scheduling,
Rückkopplung, echte Konfliktkandidaten, Kapitalgrenzen und Risikozeitpunkte.
Vorprobe: Der relevante Codezweig wird erreicht; Gegenprobe: gezielte Sabotage
schlägt an. Bestehende 600 Tests erhalten oder jede vertragsbedingte Änderung
begründen. Abgleich gegen unabhängige Losrechnung; Messungen nur lokal auf
unveränderten eingefrorenen Inputs und in separaten neuen Ergebnisdateien.
Richtige Buchführung ist Erfolg, keine gewünschte Rendite. Kein Gesamtaudit und
kein neues Strategie-/Kombinationsgitter. Umfang etwaiger historischer lokaler
Vergleiche vorab eng festlegen.

F03/F04/Einstand/Stop-Nachzug/Persistenz bleiben Etappe 4. Braucht die technische
Fill-Rückkopplung eine untrennbare Korrektur daraus, den konkreten Konflikt erst
offenlegen statt diese weitere Etappe still vorzuziehen. Vorher liegende bedingte
Orders (V2), Short-Margin/Funding und E41.6-Risikobudget sind nicht Teil von 3b.

Kein Merge oder Push nach main, keine Live-Schalter, Telegram-Nachrichten,
Orders, Deployments, gewöhnlichen GitHub-Backtest-Workflows oder E44.4/E44.5-
Übernahmen. Keine privaten Volltranskripte hochladen. Originaldaten, frühere
Ergebnisse und Sicherungstag unverändert lassen. Automatische Unit-Tests auf
dem eigenen Zweig sind erlaubt; vor Push Workflow-Auslöser prüfen.

Dokumentiere Änderungen, unabhängige Prüfungen, Ergebnisdifferenzen und Grenzen;
aktualisiere Kurzstand, Etappen und Übergabe. Sichere den eigenen Zweig auf GitHub,
prüfe Remote-HEAD/CI exakt zum Abschlusscommit und erstelle ein geprüftes lokales
Abschlussbundle samt Wiederherstellungsprobe. Liefere Bericht, Tests/Gegenproben,
Grenzen, Zweig/Commit, Sicherungspfad und Empfehlung für die nächste getrennte
Etappe. Beende danach 3b. Kein automatischer Start der folgenden Etappe.
```
