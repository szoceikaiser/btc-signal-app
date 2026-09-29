# Nacharbeit nach dem unabhaengigen Audit

Stand 29.09.2026. Kleine, einzeln pruefbare Etappen; nach jeder Etappe Ergebnis,
offene Grenzen und Empfehlung fuer Modell/Aufwand neu bewerten. Keine automatische
Live-Uebernahme. Ein Go zur Bearbeitung ist kein Go fuer main.

Rueckkehrpunkt vor allen Korrekturen:
`sicherung/vor-audit-korrekturen-2026-09-28`, Commit
`469be65f65327a3b6abf2794ceba09c1fe0de9e2`.
Lokales Bundle, ZIP und gepruefte Wiederherstellung unter
`C:/Users/oeztu/BTC-Trading/audit-backups/vor-korrekturen-20260928T103130Z/`.
Vor einer spaeteren Uebernahme den dann aktuellen Zustand erneut sichern und die
Zustandskompatibilitaet pruefen. Kein blindes Zurueckspielen alter Signalhistorie.

## Etappen und vorlaeufige Modellempfehlung

| Etappe | Inhalt und klarer Abschluss | Modell / Aufwand |
|---|---|---|
| 1 | F09: Rundungsrest/Wiederanlage; Gegenfaelle, unabhaengige Kontrollrechnung, eigener Commit | GPT-6 Sol / hoch |
| 2 | D01: laufende Schlusskerze aus Backtest-Eingaben entfernen; Zeitgrenzen und gleiche Zuordnung aller Reihen pruefen | GPT-6 Sol / mittel; bei unklaren API-Zeitbegriffen hoch |
| 3a | F01/F12: Ausfuehrungszeit und Risikoberechnung eindeutig festlegen; Handfaelle fuer Reihenfolge, Luecken und Bestand | GPT-6 Astra / hoch |
| 3b | Den festgelegten Vertrag implementieren und unabhaengig abgleichen | GPT-6 Sol / hoch; nur bei ungelöster Grundsatzfrage Astra |
| 4 | Einstand, Stop-Nachzug und gespeicherter Zustand; Hin-/Rueckweg bei laufender Position | GPT-6 Astra / hoch fuer Entwurf und kritische Pruefung, Sol / hoch fuer klar abgegrenzte Umsetzung |
| 5a | Telegram-Zustellung mit dauerhafter Versandliste und Wiederanlauf; netzfreie Fehlersimulation | GPT-6 Sol / hoch |
| 5b | Chart-Zusammenfuehrung mit eindeutigen Signal-IDs und Herkunft | GPT-6 Sol / mittel |
| 6 | Eingefrorene Vergleiche erneut rechnen; vorab neues Bestaetigungsdesign fuer wenige Kandidaten festlegen | GPT-6 Sol / mittel fuer Laeufe; Astra / hoch fuer statistische Bewertung |

Das sind Empfehlungen nach Aufgabenrisiko, keine Behauptung, dass ein Modellwechsel
bereits stattgefunden hat. Die aktive Modelleinstellung dieser Sitzung wird durch
diese Dateien und Werkzeuge nicht veraendert. Der Nutzer stellt Modell und Aufwand
vor dem naechsten Auftrag ein. Maximaler Aufwand bleibt gezielten schwierigen
Grundsatzfragen vorbehalten. Bekannte gruene Pruefungen werden nur bei neuen
Aenderungen oder konkreten offenen Risiken wiederholt.

Offizielle Einordnung: Sol eignet sich fuer anspruchsvolle Codearbeit; Luna fuer
einfache eng begrenzte Aufgaben, Astra fuer komplexe/mehrdeutige Analysen. Die genaue
Stufenzuordnung oben ist unsere aufgabenbezogene Empfehlung, keine Preisaussage ueber
den individuellen Codex-Tarif.
[OpenAI Modellauswahl](https://developers.openai.com/api/docs/guides/model-selection),
[GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol).

## Aktueller Stand

**Etappe 5b/F17 abgeschlossen** direkt aus gesichertem 5a `6c0c6fd…`, eigener
Zweig `codex/etappe-5b-chart-identitaet`. Quellengetrennte Chartidentitäten,
Kollisionen erhalten, lesbare Herkunftsliste; keine Engine-/Versandänderung.
**728 Tests**, alle 712 alten unverändert, 16 neue; **16/16 F17-Sabotagen**,
alle bisherigen Schutzproben erhalten. 1.101 vorhandene V1-Fills projiziert,
keine neue historische Rechnung. [Vertrag](F17-VERTRAG.md),
[Abschlussbericht](ETAPPE-5B-ABSCHLUSS.md). Exakte SHA/CI/Bundle/ZIP/Restore lokal
`audit-backups/5b-abschluss-<Kurz-SHA>/ABSCHLUSS.json`. 5a-Betriebsgrenzen bleiben,
kein Live-Go. Nächster **separater** Auftrag: [Etappe 6](START-6.md),
Sol/mittel für begrenzte Wiederholung, Astra/hoch für Bestätigungsdesign.
5b beenden, nichts automatisch starten.

### Historischer Abschluss 5a

**Etappe 5a abgeschlossen** auf `codex/etappe-5a-telegram-outbox`, direkt aus
gesichertem 4-Abschluss `ebc01a48057994629c021bd84ab7f9a236678b70`.
F13 im Hauptlauf: stabile Identität, atomare dauerhafte Versandabsicht mit
Position/Dedupe, geordnete Wiederholung sicherer Ablehnungen, bestätigte Quittungen
und konservativer Halt bei unklarer Zustellung. **712 Tests**, alle 676 alten
unverändert, 36 neue, **16/16 F13-Sabotagen**; 4/3b/D01/F09 erhalten.
[Vertrag](F13-VERTRAG.md), [Abschlussbericht](ETAPPE-5A-ABSCHLUSS.md).
Keine Exactly-once-Zusage; Verlust eines ephemeren GitHub-Runners vor dessen
Git-Commit bleibt Betriebsgrenze. Keine Workflow-/Strategie-/site-Änderung,
kein Live-Go. Geprüfter Remote-/CI-/Bundle-/ZIP-/Restore-Abschluss lokal in
`audit-backups/5a-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.
Nächster **separater** Auftrag **5b/F17**, **GPT-6 Sol / mittel**, bei unklaren
Herkunftskollisionen hoch; [Startprompt](START-5B.md). 5a beenden, nichts starten.

### Historischer Abschluss 4

**Etappe 4 abgeschlossen** auf `codex/etappe-4-bestand-stop`, direkt aus gesichertem
3b `9606a6f`. Restlose/Kosten in V1, monotone Long-Stop-Grenze, gemeinsamer Plan,
vollständiges Positionsschema 2 und V1-Checkpoint 1. **676 Tests**, **23/23 neue
Sabotagen**; 3b/D01/F09 erhalten. Sechs eng festgelegte lokale Vergleiche mit
unabhängiger Losrechnung und identischen Fortsetzungen in neuen Prozessen.
[Abschlussbericht und Grenzen](ETAPPE-4-ABSCHLUSS.md). Signalreferenz ist kein
belegter Live-Bestand; unbekannte Altgeschichte bleibt gekennzeichnet.
Kein main-/Live-Go. Nächster eigener Auftrag **Etappe 5a (F13), GPT-6 Sol / hoch**,
vollständiger [Startprompt](START-5A.md). F17 bleibt 5b. Etappe 4 hier beenden.

### Historischer Abschluss 3b

**Etappe 3b abgeschlossen** auf `codex/etappe-3b-f01-f12`, direkt aus gesichertem
3a `67c8e62`. Neuer kausaler V1-Pfad `backtest.run_execution` mit Ereignis-Ledger,
Reservierungen, Fill-Rückkopplung und Schluss-/Intrabar-Risiko. **638 Tests**,
**19/19 Sabotagen**, 16 unabhängige Handfälle; D01/F09 erhalten. Sechs eng begrenzte
lokale Läufe (zwei vorhandene Zeilen × drei Slippages), jeder Fill und Bestand gegen
unabhängige Losrechnung geprüft. [Umsetzung/Abnahme](F01-F12-UMSETZUNG.md).
Alte Signalband-/Workflow-Zugänge sind historische Diagnostik, kein korrigierter V1-Beleg.
Kein main-/Live-Go; Originale/Sicherungstag unverändert. F03/F04/Persistenz offen.
Nächster getrennter Auftrag **Etappe 4, GPT-6 Astra / hoch** für Entwurf und Prüfung,
anschließend Sol / hoch für eindeutig begrenzte Umsetzung. Etappe 3b hier beenden.

### Historischer Abschluss 3a

**Etappe 3a abgeschlossen** auf `codex/etappe-3a-ausfuehrungsvertrag`, aus D01
`5fabe2b`, ohne Produktionsänderung. [F01/F12-Vertrag](F01-F12-VERTRAG.md):
Nutzer bestätigt D1-A (nächstes Open), D2-A (Ausstiege vor Käufen, kein Kauf bei
Verkauf im Paket) und D3 (Long/Spot, Schluss-DD + Intrabar-Grenzen, Kostenpaket).
16 Handfälle, 27 rationale Identitäten, acht negative Kontrollen und drei gezielte
Ist-Proben; 600 bestehende Tests bestanden. F01/F12 sind vertraglich geklärt,
**im Produktionscode noch nicht behoben**. Neuer Chat für 3b mit GPT-6 Sol / hoch;
vollständiger aktueller Auftrag: [START-3B.md](START-3B.md).
Neue DD-Schwellen, V2, E41.6 und Shorts bleiben getrennte Entscheidungen.

Etappe 2 ist auf `codex/fix-d01-kerzenschluss` aus dem abgeschlossenen F09-Commit
`6edb941` umgesetzt: 600 Tests, 6/6 D01-Sabotagen, fuenf eingefrorene Vergleiche
mit unabhaengigem Losbuch. Bericht: [D01.md](D01.md). Etappe 2 ist beendet.

Etappe 1 ist auf `codex/fix-f09-wiederanlage` umgesetzt und geprueft.
Ausgangspunkt ist der gesicherte aktuelle main-Commit; E44.4/E44.5 werden nicht
mitgenommen. Bericht und Grenzen: [F09.md](F09.md).

Die neue Erfolgskriterien-Empfehlung wurde nach Kenntnis des Audits formuliert.
Sie ersetzt keine historischen Kriterien rueckwirkend. Fuer eine reine
Buchungskorrektur gilt ein richtiges Ergebnis als Erfolg, keine Mindestrendite.
Kein neues Kombinationsgitter in dieser Etappe und keine Aktivierung eines Schalters.

## Historischer Startauftrag Etappe 3a (abgeschlossen, nicht erneut ausführen)

Empfohlen: **GPT-6 Astra, Aufwand hoch** fuer Etappe 3a. Nach klarem Vertrag
Etappe 3b mit **GPT-6 Sol, Aufwand hoch**. Grund: Ausfuehrungsreihenfolge und
Risikobegriff erfordern erst eine fachlich eindeutige Entscheidung. Auftrag:

> Bearbeite ausschliesslich Etappe 3a (F01/F12), noch keine Umsetzung 3b.
> Beginne beim abgeschlossenen D01-Zweig und lies D01.md, Kurzstand und Uebergabe.
> Lege den Ausfuehrungs- und Risikovertrag eindeutig fest: Zeitpunkt des Signals,
> verfuegbares Wissen, Fill-Zeit/Preis, Reihenfolge bei Kauf/Stop/Verkauf,
> Kursluecken und Bestand vor/nach Ereignissen. Leite unabhaengige Handfaelle ab.
> Fasse benoetigte Nutzerentscheidungen konkret zusammen. Kein main-Merge,
> keine Schalter, Nachrichten, Orders, Deployments oder Backtest-Workflows.
> Schliess diese Etappe mit gesicherten Unterlagen und aktualisierter Empfehlung ab.

### Historischer Startauftrag Etappe 2 (abgeschlossen, nicht erneut ausfuehren)

> Bearbeite Etappe 2 (D01) aus docs/nacharbeit-2026-09-28/ETAPPEN.md.
> Pruefe Remotes, Zweige und den unveraenderten Sicherungstag zuerst.
> Arbeite von der abgeschlossenen F09-Korrektur aus auf einem neuen Arbeitszweig.
> Entferne nur unfertige Kerzen aus der historischen Messung und pruefe, dass
> OHLC und zugeordnete Reihen denselben abgeschlossenen Zeitbereich verwenden.
> Verwende fuer Gegenfaelle eine feste Uhr; pruefe kurz vor, genau auf und nach
> Kerzenschluss. Original-E44.5-Daten bleiben unveraendert. Dokumentiere jede
> Ergebnisaenderung getrennt von F09. Kein main-Merge, keine Live-Schalter,
> keine Telegram-Nachrichten und keine Deployment-Ausloeser. Beende diese Etappe
> mit Tests, Bericht, gesichertem Zweig und Modellempfehlung fuer den Folgeschritt.
