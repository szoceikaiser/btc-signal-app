# Nacharbeit nach dem unabhaengigen Audit

Stand 28.09.2026. Kleine, einzeln pruefbare Etappen; nach jeder Etappe Ergebnis,
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

## Start fuer die naechste Etappe

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
