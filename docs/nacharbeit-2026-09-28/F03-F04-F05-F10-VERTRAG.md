# Etappe 4: Bestand, Einstand, Stop und Zustand

28.09.2026. Basis exakt `9606a6f555f9cdaee86f9c33a5175c5c5306b365`.
Nur F03/F04/F05/F10; eigener Zweig `codex/etappe-4-bestand-stop`.
V1 aus F01-F12-VERTRAG.md bleibt verbindlich. Kein main-/Live-Go.

## 1. Drei getrennte Wahrheiten

- Signalreferenz: `evaluate` beobachtet Signale, keine manuellen Ausführungen.
  Die bisherige tranchengewichtete `entry_ref` bleibt in diesem ausdrücklich
  historischen Signalmodell ein Referenzanker, kein belegter Kosteneinstand.
- Simulierte Fills: V1 führt tatsächliche **im Modell** gefüllte BTC-Lose mit
  Bruttokosten einschließlich Kaufgebühr. Nur gebuchte Fills verändern diese Lose.
  Signalpreise, Ablehnungen und Reservierungen tun das nicht.
- Live-Bestand: unbekannt, solange kein unabhängiger Ausführungsbeleg existiert.
  Telegram-Signale und alte state.json werden niemals zu Broker-Fills umgedeutet.
  Es wird in dieser Etappe kein Broker-/manueller Import gebaut.

Positionsplan und gespeicherter Zustand kennzeichnen ihre Herkunft. Ein Signalanker
darf dort nicht als bestätigter Live-Einstand erscheinen. Historische Signalbänder
bleiben Diagnostik. Neue Messungen ausschließlich `backtest.run_execution`.

## 2. Lose und Kosten

Je Kauf: Los-ID = Order-ID, Fillzeit/-preis, BTC, Bruttokosten, Kaufgebühr,
Herkunft `base` oder `e42`. Bruttobudget B ergibt bei Gebühr f und Fillpreis p
`q=B*(1-f)/p`, Kosten B. Teilfinanzierung verwendet nur tatsächlich bezahltes B.
Slippage steckt ausschließlich im Fillpreis, nicht nochmals in den Kosten.
Gesamteinstand = Summe verbleibender Bruttokosten / Summe verbleibender BTC.
Ohne Gebühren: `75/(25/220+50/172.8)=186.1096605744…`.

Gewöhnliche Verkäufe reduzieren **jedes** verbleibende Los und dessen Kosten um
denselben Mengenanteil. E42-Teilstop reduziert ausschließlich E42-Lose; die
Basislose bleiben identisch. Verkaufskosten mindern Erlös/realisierten Gewinn,
nicht die Anschaffungskosten des Restbestands. Kein steuerliches FIFO-Modell.
Vollausstieg leert Lose/Kosten/Höchstbestand und setzt den Positionszyklus zurück;
F09-Restbereinigung und Wiederanlage aus neuer Kasse bleiben erhalten.

Gesamteinstand und Basis-Einstand sind getrennte Größen: Der Hauptstop verwendet
weiterhin den Basisteil, E42 seinen eigenen Teilstop (bestätigte E42-Regel).
E42 in den Haupt-Break-even einzurechnen würde auch alte Basislose wegen eines
neuen Rückkaufs stoppen; das wäre eine zusätzliche, hier nicht vorgenommene
Strategieänderung. Der Plan nennt Gesamteinstand und die Basis des Hauptstops.
`entry_pct` bleibt historischer Strategie-/Tranchenmerker, kein BTC-Bestand und
kein Marktwert. Tatsächliche Restlose sind die Kostenquelle in V1.

## 3. Gültiger Long-Hauptstop

Vorhandene Aktivierung von trail_stop/be_im_plus bleibt. Neue Strukturkandidaten
müssen bei ihrer erstmaligen Auswahl bestätigt und unter dem aktuellen Close sein.
Ein bereits gewählter Stop bleibt gültig, auch wenn der Kurs ihn unterschreitet,
der Pivot aus dem Fenster fällt, Einstand sinkt oder Zonen wechseln.
Innerhalb derselben offenen Long-Position gilt `S_neu=max(S_alt,S_Kandidaten)`.
Nur FLAT beendet die Grenze. Ein Nachkauf/Neustart mit Rest senkt sie nicht.
Der gespeicherte Grund entscheidet weiterhin, ob E41-Rückeroberung gilt:
ursprüngliche Invalidierung mit bestehender E41-Logik, nachgezogener Stop direkt
am Schlussbruch. Keine Umstellung auf Intrabar-/Broker-Stoporders.
Ein gemeinsamer Resolver liefert Preis und Grund an Engine und Positionsplan;
Planlesen mutiert weder Zustand noch Handelsentscheidung.

Ein Teilverkauf kann die Nachzugsbedingung neu aktivieren. Deshalb wird der
prospektive Stop nach dem Signalzustandsübergang, in V1 aber erst nach tatsächlichem
Fill und Kostenrückkopplung, aus dem bekannten Entscheidungspräfix gespeichert.
Kein rückwirkender Stop-Fill in derselben Kerze; keine Aktivierung durch abgelehnte
oder verfallene Verkäufe. Der nächste reguläre Schluss prüft diese gültige Grenze.

115 bei Close120 bleibt beim folgenden Close110 bestehen: Stopkandidat zum
Folge-Open gemäß V1, kein Rückfall auf Einstand100. Das korrigiert das Verhalten,
nicht nur dessen Anzeige. Shorts bleiben historische, unveränderte Diagnostik.

## 4. Persistenz und Altzustände

Versioniertes Positionsschema mit vollständigen Dataclass-Feldern einschließlich
widerstand_exits, Pivot-Indizes, E41/E42, Stoppreis/-grund, Losen und Herkunft.
Nur e42_meldungen ist flüchtige Ausgabe der aktuellen Kerze, keine Entscheidung.
Versionierte V1-Checkpoints enthalten zusätzlich Kasse, Reservierungen, ausstehende
Absichten samt bekannter Entscheidungsbasis, Losbuch, Risikopeaks, Historie und
Konfiguration. JSON-Hin-/Rückweg und Fortsetzung müssen identisch sein.
Unbekannte künftige Versionen und unvollständige neue Zustände werden abgelehnt.

Unversionierte Live-Altzustände werden ohne Reset übernommen. Fehlende Felder
erhalten dokumentierte Defaults und eine Migrationskennzeichnung; fehlende
widerstand_exits/alte Stopmaxima sind nicht rekonstruierbar. Der alte entry_ref
bleibt als Signalreferenz erhalten. Es werden weder historische Lose erfunden
noch bereits gesendete Signale neu ausgewertet. Bei der ersten regulären neuen
Kerze beginnt die speicherbare Stopgrenze aus dem vorhandenen Wissen. Historische
Stopmaxima sind damit ausdrücklich nicht rückwirkend garantiert.
Alte V1-Ergebnisdateien sind keine fortsetzbaren Checkpoints; ohne vollständige
Fill-/Reservierungsbasis kein stiller Neustart aus einem Ergebnisaggregat.

## 5. Vorab begrenzte Abnahme

Alle 638 bisherigen Tests bleiben; fachlich nötige Änderungen einzeln begründen.
Audit-Gegenfälle zuerst auf unverändertem 3b-Code reproduzieren, danach echte
Produktionszweige erreichen und gezielte Mutationen erkennen. Unabhängige
Los-/Kostenrechnung, Gebühren/Teilfinanzierung, proportionale Verkäufe, gezielter
E42-Verkauf, FLAT/Wiederanlage, Altzustände und Mehrkerzen-Neustartparität.

Historischer Umfang **vor Messung festgelegt**: ausschließlich dieselben zwei
Zeilen wie 3b (Live-Basis und vorhandenes E42/12), jeweils Slippage 0/0,1/0,5 %,
Gebühr 0,1 %, dieselben eingefrorenen Audit-Inputs und Stichtag. Vergleich gegen
gespeicherte 3b-Ergebnisse; keine neue Zeile, kein Gitter, keine Schwellenwahl.
Input-SHA256 `ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a`.
Ergebnisse separat `4-*`; Originale unverändert. Erfolg ist korrekte Buchführung
und identische Fortsetzung, unabhängig von Rendite. F13/F17 und weitere Befunde
bleiben getrennten Etappen vorbehalten.
