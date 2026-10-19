# BTC-Engine: Betrieb und manueller Backtest

## Backtest starten

1. [Repository öffnen](https://github.com/szoceikaiser/btc-signal-app).
2. **Actions** → **Backtest** → **Run workflow** (Workflow ausführen).
3. Branch **main** belassen und den grünen Knopf **Run workflow** anklicken.
4. Den neuen Lauf **C05 aktuell – höchstens 365 Tage** öffnen.
5. Nach Erfolg steht der lesbare Bericht in der **Summary** (Zusammenfassung).
   Unter **Artifacts** (Artefakte) lässt sich **C05-Backtest-LAUFNUMMER** herunterladen.

Jeder Start bestimmt sein Zeitfenster neu: letzte vollständig abgeschlossene
4h-Kerze, höchstens 365 Tage zurück. Die laufende Kerze wird ausgeschlossen.
200 weitere Kerzen sind technischer Vorlauf; sie zählen nicht zur Rendite.
Die OI-Historie kann das tatsächliche Messfenster verkürzen. Der Bericht nennt
das angeforderte und das tatsächliche Fenster und weist fehlende Werte aus.
Die 365 Tage sind eine Obergrenze, keine Behauptung lückenlos vorhandener Daten.

Alle vorhandenen Coinalyze-Archivwerte der vier Reihen OI, Liquidationen,
Futures-Delta und Long/Short im Fenster werden mit frischen Abrufen verbunden.
Frische Werte gewinnen bei Überschneidungen. Alte archivierte Zeitpunkte bleiben
in der Rechnung erhalten, auch wenn die API sie nicht mehr liefert. Das Archiv
selbst wird vom Backtest nicht geändert oder gekürzt; der Workflow
**Coinalyze-Archiv** sammelt weiterhin separat.

Gerechnet wird genau C05 mit der unveränderten abgenommenen Engine, 10.000 USD
ohne Anfangsbestand, S0 (0,1 % Gebühr je Ausführung, nächstes 4h-Open, kein
Slippage-Aufschlag). Keine neue Parametersuche, keine Änderung der Live-Position,
kein Versand. Die Ergebnisse sind Modellrechnungen. Die feste historische
C05-Referenz auf der Webseite bis 04.10.2026 ist separat und bleibt erhalten.

Artefakte enthalten Bericht, eingefrorene Recheneingaben und vollständige
Ausführungsbuchungen. Aufbewahrung auf GitHub: 90 Tage; wichtige Berichte lokal
herunterladen. Die Definition und der Quelltext des Backtests bleiben im Repo.

## Verbleibende Workflows

| Workflow | Aufgabe |
|---|---|
| Signal-Engine | Plan und neue reguläre Signale |
| Flush-Wache | Zusätzliche zeitnahe Flush-Prüfung |
| Lage abrufen | Manuell angeforderte aktuelle Lage |
| Coinalyze-Archiv | Historische Messwerte fortlaufend sichern |
| Chart-Webseite (Pages) | Geprüfte Darstellung veröffentlichen |
| backup | Tägliche Sicherung des Betriebsfortschritts |
| backup-verify | Sicherung unabhängig prüfen |
| BTC candidate freshness | Interne Aktualitäts- und Betriebsprüfung |
| Tests | Abgenommene Engine unabhängig offline prüfen |
| Backtest | Manuelle aktuelle C05-Modellrechnung |

Alte einmalige Diagnose-Workflows stehen bytegleich in
`ops/workflow-archiv/20261019/`. Historische Laufeinträge können weiterhin in
GitHub sichtbar sein; sie werden nicht gelöscht. Eine Wiederherstellung einer
Diagnose bedeutet eine neue Änderung der betreffenden Datei zurück nach
`.github/workflows/` und erneute Aktivierung des Workfloweintrags.

## Alarm und Wiederherstellung

Der bestehende cron-job.org-Aufruf prüft über Cloudflare die Engine auch von
außerhalb GitHubs. Eine Fehlermail bedeutet zuerst: den gespeicherten
Antwortgrund und die letzten Signal-/Wache-/Monitorläufe prüfen. Nicht allein
aufgrund einer Mail einen alten Store oder ein altes ZIP zurückspielen.

`btc-signal-app-backup` bewahrt die gesicherte alte Engine; der alte Stand ist
mit `engine-sicherung-final-20261018` benannt. `btc-delivery-backup` und
`btc-delivery-backup-verification` sichern beziehungsweise quittieren den
fortlaufenden Betriebszustand. Bei einer Wiederherstellung immer den aktuellen
Store und die Versandbestätigungen berücksichtigen, damit bereits versandte
Signale nicht erneut abgesendet werden. Codekorrekturen als gezielte neue
Commits; Betriebsfortschritt nicht durch alte Sicherungen überschreiben.
