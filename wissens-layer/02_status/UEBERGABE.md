# Laufende Übergabe

## Historischer Folgeauftrag nach Etappe 6 — 29.09.2026

- Direkt aus 05208cecce8d5a0e856a1ea56984b209f403ccd6, eigener Zweig
  codex/nach-6-historische-auswertung; kein neuer main-/E44.4-/E44.5-Code.
- R0 unverändert; R1 bis fest 29.09.2026 12:00 UTC vollständig ergänzt:
  13 neue abgeschlossene Kerzen, 2.480 alte abgeschlossene Präfixkerzen feldgleich.
  Nutzer erlaubte im laufenden Auftrag GitHub-Läufe. Isolierter Rohdatenlauf
  36592684701 nutzte Coinalyze-Secret, ohne Repo-Schreibrechte/Telegram/Pages.
- 60 feste kausale Läufe: R0/R1 × Basis/E42 × S0–S4 × drei Startpunkte.
  7.338 Fills / 60.630 Closes unabhängig geprüft; keine neuen Suchalternativen.
- R1 Hauptfall S1: Basis 12.813,81 USD, E42 12.639,84 USD (−173,96 USD,
  −1,3576 % relativ), Schluss-DD 8,4989 / 9,0636 %, obere Grenze 9,9428 / 10,2437 %.
  Basis dominiert S0/S1/S2/S4; S3 +117,27 USD für E42 bei höherem Schluss-DD.
- 20.000 stationäre gepaarte Tages-Bootstraps, Seed 20260929, Block 14/7/28,
  alle Ergebnisse/Monate/Drittel/Frischstarts berichtet. S1-Hauptintervall R1
  −4,1660 bis +1,4369 %, p_cond 0,839658; nur bedingt, Auswahlbereinigung nicht belegt.
  Historische Vintages/erreichbare Live-Fills bleiben unbelegt, keine Power-Zusage.
- 741 Tests (728 alte unverändert), 6 synthetische Testgruppen, 15 neue Schutzproben;
  alle alten F17/F13/4/3b/D01/F09-Proben erhalten. Isolierte i+2-Rundungskorrektur
  samt Gegenfall/Planrevision dokumentiert; bisheriger V1-/Checkpointcode unverändert.
- Bericht docs/nach-6/BERICHT.md, vollständige Ergebnisse/CSV/Ledger/Manifeste daneben.
  Exakte Abschluss-SHA/CI/Bundle/ZIP/Restore: lokale
  audit-backups/nach-6-abschluss-<Kurz-SHA>/ABSCHLUSS.json.
- Live-Konfiguration, site, Versandliste und Produktions-Engine unverändert;
  kein main-Merge, keine Nachrichten/Orders/Deployments, kein Live-Go.
  F13-uncertain blockiert; kein Reset/Exactly-once, manueller Bestand unbekannt.
  Runnerverlust vor Git-Persistenz sowie V2/Shorts/E41.6 bleiben separat offen.
- Auftrag danach beenden. Weitere Kandidaten, Auswahlbereinigung und Live-Entscheidungen
  ausschließlich separat; kein automatischer Folgeauftrag.

## Übergabe 29.09.2026: Etappe 6, retrospektives Design v2

Eigener Zweig codex/etappe-6-reproduktion-design direkt aus gesichertem 5b
bb862204c97c6bb4c0da49cb6f1de90dd58af663. R0-Reproduktion unverändert:
sechs vollständige V1-Läufe exakt identisch, 1.101 Fills / 9.054 Closes unabhängig
geprüft, 728 Tests unverändert. Engine/site/Daten/Versand/Verträge/Workflows erhalten.

Nutzer lehnt Jahreswartezeit ab und verlangt sachliche historische Prüfung bis
jetzt. Design v2 in 6-BESTAETIGUNGSDESIGN.md / 6-design-register.json:
R0 bis 27.09. bleibt erhalten; R1 mit gleicher Basis/Warmup bis festem Stichtag
29.09.2026 12:00 UTC geplant. R1 noch nicht beschafft/gemessen. Keine neuen
Kandidaten oder Auswertungen durch diese Designänderung. Unbestätigte Nutzen-
und DD-Budgets zurückgezogen, keine persönliche Risikotoleranz unterstellt.
Wirkung/Risiko/Dominanz und Zielkonflikte berichten statt willkürlicher Hürden.

Historische Kalendermonate/mechanische Drittel/Startzustandssensitivität und alle
Kosten-/Latenzfälle festgelegt. Paar-Bootstrap nur bedingte Unsicherheit,
keine Bereinigung der früheren Auswahl. Suchhistorie E43/E44/Audit/Korrekturen
lesend inventarisieren. Reality-Check/SPA und E42-spezifische simultane Aussagen
nur bei vollständiger relevanter Familie/geprüfter Implementierung. Familie noch
nicht nachgewiesen; trotzdem beschreibende historische Evidenz möglich.
Keine KI-Objektivität als Ersatz für statistische Auswahlkontrolle behaupten.

D6-A retrospektiv durch Nutzer festgelegt, D6-B/C zurückgezogen; alte Fragen
nicht erneut stellen. Offene Technik: R1-Paket/Quellen-/Verfügbarkeitsmanifest,
Statistik/synthetische Tests, separate i+2-Umsetzung und Suchinventar. Bekannte
R0-Dominanz der Basis nur historischer Modellbefund, kein Zukunfts-/Live-Go.
Version-1-Sicherung efc3b1a unverändert. Bericht ETAPPE-6-ABSCHLUSS.md;
neue exakte SHA/CI/Bundle/ZIP/Restore lokal 6-abschluss-<Kurz-SHA>/ABSCHLUSS.json.

Keine Nachrichten/Orders/Deployments/Live-Schalter/Dispatches/main-Push/Merges.
F13-ID lokale Versandidentität; uncertain blockiert, kein Reset/Exactly-once.
Ephemerer Runnerverlust vor Git-Persistenz offen, manuelle Fills unbekannt.
V2/Shorts/E41.6/weitere Befunde getrennt. Nächster separater Auftrag
START-NACH-6.md: retrospektive Umsetzung/Auswertung; nichts automatisch starten.

---

## Übergabe 29.09.2026: Etappe 5b F17 abgeschlossen

- Chart erhält alle Quellen/Kollisionen: L Live-Referenz, H historische Diagnostik,
  optional V1 Modell-Fills. Deterministische Chartidentitäten, vollständige
  Ereignisliste, reine Altbestandsprojektion ohne Versand-/Zustandsänderung.
- **728 Tests**, alle **712 alten unverändert**, 16 neue; **16/16 F17-Sabotagen**.
  5a 16/16, 4 23/23, 3b 19/19, D01 6/6, F09 3/3 erhalten. 1.101 gespeicherte
  V1-Fills auf Zeit/Preis/Identität projiziert, keine historische Neuberechnung.
- Engine, Versandliste, Strategie, Konfiguration, historische Daten und Workflows
  identisch zur gesicherten Basis 6c0c6fdd56db9bb27febaf42c56f6e33bcab0685.
  Keine echte Zustellung/Orders/Deployments/main-Push/Merges/Dispatches, kein Live-Go.
- Grenzen aus 5a bleiben: uncertain sperrt Folge, keine Exactly-once-Garantie,
  ephemerer Runnerverlust vor Git-Persistenz offen. Chart-ID ist kein Zustellbeleg;
  identische Altduplikate erlauben keine nachträgliche Einzelzuordnung.
- Zweig `codex/etappe-5b-chart-identitaet`, Arbeitsbaum `etappe-5b-work`, Bericht
  `docs/nacharbeit-2026-09-28/ETAPPE-5B-ABSCHLUSS.md`. Exakte SHA/CI/Restore lokal
  `audit-backups/5b-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.
- Nächster **separater** Auftrag: Etappe 6, `START-6.md`; Sol/mittel für begrenzte
  Reproduktion, Astra/hoch für Bestätigungsdesign. Nichts automatisch starten.

F17-Vertrag vor Umsetzung festgelegt. Originalmerge auf exakter 5a-Basis und
zwei unabhängige Audit-Snapshot-Konflikte reproduziert. Tatsächliches JavaScript
inklusive HTML-load/Marker-/Listenpfad netzfrei geprüft; kein Screenshot-/Live-
Seitenbeleg behauptet. Explizite IDs nur quellenintern bei identischem Inhalt
zusammengefasst; widersprüchliche Inhalte markiert, Altduplikate erhalten.
Optionale V1-Ergebnisdatei wird nicht erzeugt oder automatisch ausgewählt.
728 Restore-Tests, alle Schutzproben, sechs identische bereits festgelegte V1-
Prozessfortsetzungen und unabhängiger Kostenabgleich gehören zur lokalen Abnahme.
V2/Shorts/E41.6/weitere Befunde getrennt. Privates Repo/Originale/Tag unverändert.

---

## 29.09.2026 — Etappe 5a F13 abgeschlossen auf eigenem Zweig

Direkt aus gesichertem Etappe-4-Abschluss ebc01a48057994629c021bd84ab7f9a236678b70,
Zweig `codex/etappe-5a-telegram-outbox`, Arbeitsbaum `etappe-5a-work`.
ABSCHLUSS.json von Etappe 4, Remotes/Zweige/Änderungen und Arbeitsbäume geprüft;
fremde ungetrackte E44-Dateien und private Änderungen erhalten. Keine neueren
main-/E44.4-/E44.5-Commits übernommen, privates Backup-Repo nicht committet.

Vor Umsetzung Vertrag F13-VERTRAG.md festgelegt. Hauptlauf speichert atomar
Position, Dedupe, unveränderliche Nachrichtenabsichten und reparierbare Historien-
Projektionen in state.json. Nachrichten-ID aus Art/Zeit/Sequenz/Inhalt; Text-SHA,
Versandstatus, Versuche, Zielhash und message_id dauerhaft gespeichert.
Sending vor API-Aufruf, confirmed nur nach positivem Telegram-Beleg.
Ablehnung/pending wird beim Neustart in Reihenfolge erneut versucht, auch ohne
neue Kerzen/bei Fetchfehler. Confirmed nie erneut. Timeout/unterbrochenes sending
wird uncertain und stoppt Folgeeinträge. Ein OS-Dateilock schützt den lokalen Pfad.

712/712 Tests: sämtliche 676 bisherigen unverändert, 36 neue F13-Fälle.
Original-F13 mit echter KAUF_1-Auswertung auf ebc01a4 reproduziert. Echte E41-
Wartemeldung vor zwei Teilverkäufen, Hauptlauf plus echter Fake-HTTP-Parser,
Schreibfehler/Projektreparatur, Altbestand/kein Historienreplay, Zielwechsel,
fehlende Zugangsdaten, Dry-run und Schema-/Textfehler geprüft. Fünf separate
Python-Prozesse abrupt beendet: vor/nach Commit, vor API, nach simulierter
Annahme und nach Quittung. Konkurrenzprozess/Sperrfreigabe geprüft.
16/16 F13-Sabotagen erst nach grüner erreichter Vorprobe erkannt;
4 23/23, 3b 19/19, D01 6/6 und F09 3/3 erhalten.

Keine Änderung an Strategie, site, Workflows, V1/Positionscodec oder alten Tests.
F09/D01, Restlose/Kosten, monotoner Stop, Next-Open, Exitpriorität, Reservierungen,
Gebühren/Slippage, Schluss-DD/obere Intrabar-Grenze und bestätigte Verträge bleiben.
GitHub-Zweig/Remote-HEAD/Tests zur exakten SHA lesend geprüft. Bundle/ZIP,
vollständiger Baumvergleich, frischer Restore, 712 Tests/Schutzproben und sechs
identische gespeicherte V1-Prozessfortsetzungen lokal gesichert unter
`audit-backups/5a-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.
Bericht: `docs/nacharbeit-2026-09-28/ETAPPE-5A-ABSCHLUSS.md`.

Grenzen: API-Annahme ist kein Lesebeleg/manueller Fill. Keine Exactly-once-Zusage;
unklare Fälle benötigen separate manuelle Klärung. Lokale Transaktion überlebt
Prozessende, nicht verlorene Datenträger/getrennte Hostkopien. Der unveränderte
GitHub-Workflow persistiert erst nach dem Lauf: Verlust des ephemeren Runners
davor bleibt offen und muss vor Live-Go separat gelöst werden. Eigenständige
watch/lage/test/resend-Befehle bleiben Einmalbefehle. Keine echten Nachrichten,
Orders, Deployments, Live-Schalter, Dispatches oder main-Push/Merges.
Sicherungstag/Originale/private Volltranskripte unverändert. F17 bleibt 5b;
V2/Shorts/E41.6/andere Befunde nicht bearbeitet. Nächster separater Auftrag:
`START-5B.md`, GPT-6 Sol / Aufwand mittel, bei Herkunftsmehrdeutigkeit hoch.
5a beenden; keine Folgeetappe automatisch starten.

---

## 29.09.2026 — Etappe 4 F03/F04/F05/F10 abgeschlossen auf eigenem Zweig

Arbeitsbaum `etappe-4-work`, Zweig `codex/etappe-4-bestand-stop`, direkt aus dem
gesicherten 3b-Abschluss `9606a6f555f9cdaee86f9c33a5175c5c5306b365`.
Remotes, Zweige, Arbeitsbäume und Änderungen geprüft; private/fremde Änderungen
erhalten. Keine neueren main-/E44.4-/E44.5-Commits übernommen. Privates Repo nicht
committet; Sicherungstag unverändert, main nur lesend beobachtet.

Vertrag: `docs/nacharbeit-2026-09-28/F03-F04-F05-F10-VERTRAG.md`.
Bericht: `docs/nacharbeit-2026-09-28/ETAPPE-4-ABSCHLUSS.md`.
V1 führt gebührenhaltige Restkosten je tatsächlich gefülltem Los, proportionalen
gewöhnlichen Verkauf und gezielten E42-Losverkauf. Gesamteinstand enthält E42;
Basis-Einstand für den Hauptstop bleibt davon getrennt. Ein Long-Stop bleibt nach
Aktivierung monoton bis FLAT, auch nach Kursbruch, Nachkauf, Zonen-/Fensterwechsel
und Neustart. Beim bestätigten TP-Fill wird er aus dem bekannten Präfix aktiviert,
erst nach Kostenrückkopplung; abgelehnte/verfallene TP-Absichten aktivieren ihn nicht.
Engine und Plan verwenden denselben gespeicherten Stop samt Grund und E41-Regel.

Positionsschema 2 speichert sämtliche entscheidungsrelevanten Felder einschließlich
widerstand_exits und Pivot-Indizes. V1-Checkpoint 1 umfasst zusätzlich Reservierungen,
Absichten, bekannte Entscheidungsbasis, Cash/Restlose, Risiko und bisherige Ergebnisse.
JSON-Weg plus neue Prozesse liefern identische Fortsetzung. Altzustände behalten
Position/Dedupe/Signalanker; unbekannte frühere Stopmaxima und fehlende Zähler sind
markiert. Keine manuelle Live-Ausführung wird aus Telegram-Signalen rekonstruiert.
Der Live-Observer bleibt Signalreferenz, kein Kostennachweis. Anzeige kennzeichnet
diese Grenze ausdrücklich. Versandmechanik/F13 und Chart/F17 bleiben unberührt.

**676/676 Tests**, 38 neue; **23/23 neue Sabotagen** nach erreichtem Ausgangsfall.
Bestehende 3b 19/19, D01 6/6, F09 3/3 erneut bestanden. Zwei alte Erwartungen zu
Strukturstop/Plan korrigiert, zwei E42-Fixtures um echte Testlose ergänzt. Ein
Muster-2-Test isoliert nun den Struktur-Nachzug; seine bisherigen Muster-/Signal-
Assertions bleiben, die zusätzliche Strukturhistorie hat einen eigenen Gegenfall.
Alle Anpassungen mit konkreten Werten im Bericht. Kein Test gestrichen.

Vorab genau dieselben zwei Zeilen und drei Slippages wie 3b festgelegt. Ausschließlich
lokales `backtest.run_execution`, Inputs unverändert. 1.101 Fills und 9.054 Closes
gegen unabhängiges Audit-Buch und Decimal-Kostenrechnung geprüft; sechs echte
Prozessneustarts mit identischem Gesamtergebnis. Ohne Slippage Endwerte
13.418,88 / 13.299,89 USD; gegenüber 3b −12,57 / +49,02. Schluss-DD 7,9166 / 8,4177 %,
**obere Intrabar-Grenze jeweils 9,9428 %**. Kein Gitter, keine Renditezielsetzung,
keine neuen DD-Schwellen. Originale und frühere Ergebnisdateien unverändert.

Eigener GitHub-Zweig, exakte Abschluss-SHA/CI, Bundle/ZIP und geprüfter frischer
Restore unter `audit-backups/4-abschluss-<Kurz-SHA>/ABSCHLUSS.json`.
Keine privaten Volltranskripte, main-Push/Merge, Live-Schalter, Nachrichten, Orders,
Deployments oder Dispatches. Nächster getrennter Auftrag **Etappe 5a, GPT-6 Sol / hoch**:
`docs/nacharbeit-2026-09-28/START-5A.md`. Etappe 4 beenden, nichts automatisch starten.

---

## 28.09.2026 — Etappe 3b F01/F12 abgeschlossen auf eigenem Zweig

Arbeitsbaum `etappe-3b-work`, Zweig `codex/etappe-3b-f01-f12`, direkt vom exakten
3a-Abschluss `67c8e624de3cc1b854a78dced755a5702b1a9c9a`. Remotes, Zweige und alle
Arbeitsbäume geprüft; fremde ungetrackte E44-Artefakte erhalten. Privates Backup-Repo
nicht committet. Keine neueren main-/E44.4-/E44.5-Commits übernommen.

Neuer V1-Zugang `backtest.run_execution`/`run_execution_half`: getrennte Kauf-/
Verkaufskandidaten auf gleichem gebuchtem Vorzustand; Reservierung und Fill am nächsten
zulässigen Open; echte Fills/Ablehnungen vor neuer Entscheidung zurückgekoppelt.
Teilfinanzierung skaliert nur bestehende Tranche; kein Phantomverbrauch von Leiter-
stufen. Haupt-/Gesamtausstieg vor Teilstop vor Teilverkauf; Verkauf sperrt Paketkäufe.
F09-Zyklusreset/Wiederanlage, bestehende Tranchen und D01-Stichtag erhalten.

**638/638 Tests** (600 alt, 38 neu), **19/19 Sabotagen**, 16 unabhängige Handfälle
(zwölf V1, drei ausgeschlossene V2-Fälle, H14 ausgeschlossene E41.6-Arithmetik).
Echte Konflikte, Rückkopplung, Cash/Reservierungen, Datenende/Lücken, Präfixe und
Risikozeitpunkte erreicht. D01 6/6 und F09 3/3 bestehende Mutationen ebenfalls erkannt.
Zwei Quelltext-Assertions zeigen wegen Auslagerung auf `_evaluate`, sonst alte
Erwartungen unverändert. Bericht `docs/nacharbeit-2026-09-28/F01-F12-UMSETZUNG.md`.

Genau Live-Basis und bestehendes E42 (zwölf Kerzen), pro Zeile 0/0,1/0,5 % Slippage
je Seite, nur lokal auf unveränderten Audit-Inputs. Gebühren 0,1 % je Fill.
Jeder Fill und Cash/BTC-Close-Pfad, Monatsstände, Los-PnL, Kosten und Risikofelder
gegen unverändertes unabhängiges Losbuch abgeglichen. Endwerte ohne Slippage:
13.431,45 / 13.250,88 USD gegenüber 3a-Level 13.613,09 / 13.541,56 USD.
Schluss-DD 7,9166 / 8,4177 %, **obere Intrabar-Grenze jeweils 9,9428 %**.
Alle neuen Kandidatenbänder unterscheiden sich vom alten Signalband; Buchführung
ist Erfolg, keine gewünschte Rendite. Ergebnisse ausschließlich separate `3b-*`.

F03/F04-Einstand/Stop-Nachzug und Persistenz bleiben offen; ursprüngliche Referenz-
Einstandsformel erhalten und kann Strategie weiter beeinflussen. Keine untrennbare
Etappe-4-Korrektur benötigt. Live-Observer und bisherige Signalband-/Workflow-Zugänge
bleiben historische Diagnostik ohne V1-Zertifizierung. Neue Messungen ausdrücklich
mit `run_execution`, keine still umgedeuteten alten Drawdown-Werte/Schwellen.

Originaldaten/Ergebnisse, site/Workflows, Live-Schalter, privates Backup und Sicherungstag
unverändert; kein Merge/main-Push, Dispatch, Telegram, Order oder Deployment.
Eigener GitHub-Zweig plus CI zur exakten Abschluss-SHA und frischer Bundle-Clone lokal
unter `audit-backups/3b-abschluss-<Kurz-SHA>/ABSCHLUSS.json` nachgewiesen.

Nächster separater Auftrag **Etappe 4: GPT-6 Astra / hoch** für Einstands-/Stop-/
Persistenzvertrag und kritische Prüfung; Sol / hoch für danach klar begrenzte Umsetzung.
Neue DD-Schwellen vor späterer Strategiebewertung; V2/Short-Margin/Funding/E41.6 getrennt.
Etappe 3b beenden; keine Folgeetappe automatisch starten.

---

## 28.09.2026 — Etappe 3a F01/F12 abgeschlossen, Umsetzung 3b noch nicht begonnen

Eigener Arbeitsbaum `vertrag-3a-work`, Zweig `codex/etappe-3a-ausfuehrungsvertrag`,
direkt aus D01 `5fabe2bae1506546fc31708ceecef2034365300f` (enthält F09).
Remotes, saubere Ausgangsarbeitsbäume und unveränderten Sicherungstag geprüft.
Privates Backup-Repo nicht committet; main nur lesend aktualisiert/beobachtet.

Vertrag: `docs/nacharbeit-2026-09-28/F01-F12-VERTRAG.md`. Nutzer hat alle drei
fachlichen Fragen ausdrücklich beantwortet: D1-A nächstes Open, D2-A Ausstiege
vor Käufen (bei Verkauf kein Kauf im selben Paket), D3 Risikopaket Long/Spot,
Schluss-DD und Intrabar-Grenzen, 0,1 % Gebühr, 0/0,1/0,5 % Slippage je Seite.
Next-Open bleibt idealisierte Null-Latenz-Ausführung. Keine Vorab-Limit-Orders
unterstellen. Signalzeit, Fill und Zustand müssen in 3b kausal getrennt werden.
Kein bloßes Umrechnen des alten Signalbands als vollständige Korrektur ausgeben.

16 Handfälle mit 27 rationalen Identitäten, acht negative Kontrollwerte erkannt,
drei erreichte Ist-Proben. F01 Verkauf nach Tief: bisher 0 statt 50 % DD; Kauf nach
Tief: bisher 50 statt 0 %; F12 neues Ziel derselben Kerze reproduziert. Diese Proben
bestätigen offene Fehler, sie reparieren nichts. Unveränderte Suite: **600/600**.
Prüfartefakte `3a-pruefung.json`, `3a-tests.log`, Skript `tools/verify_3a_contract.py`.

Keine Änderungen an Engine, site, Workflows, Live-Schaltern, Originaldaten oder
früheren Ergebnissen. Kein Gesamtaudit, E44.4/E44.5, Merge, main-Push, Telegram,
Order, Deployment oder Backtest-Workflow. Eigener Zweig wird gesichert; GitHub-CI
und Remote-HEAD zur exakten SHA sowie Bundle-Wiederherstellung werden lokal unter
`audit-backups/3a-abschluss-<Kurz-SHA>` nachgewiesen (ABSCHLUSS.json).

Für V1/3b keine offene fachliche Auswahl mehr. Neue quantitative DD-Schwellen und
Abschaltregeln vor späterer Strategiebewertung, E41.6-Budget, V2 und Shorts bleiben
eigene Entscheidungen. F03/F04/Persistenz bleiben Etappe 4; Abhängigkeiten bei
Fill-Rückkopplung konkret melden, nicht still in 3b mitreparieren.

Neuer Chat sinnvoll: **GPT-6 Sol / hoch**, Aufwand hoch beibehalten, von der
3a-Empfehlung Astra auf Sol wechseln. Auftrag `docs/nacharbeit-2026-09-28/START-3B.md`.
Vor neuem Schreibzugriff gesicherten 3a-Commit prüfen, eigenen Folgearbeitsbaum
anlegen. Etappe 3a danach beendet; dieser Abschluss startet 3b nicht.

---

## 28.09.2026 — Audit-Nacharbeit, Etappe 2 (D01), nur eigener Arbeitszweig

`codex/fix-d01-kerzenschluss` in `fix-d01-work` basiert auf abgeschlossenem F09
`6edb941b10e4220f4634e4570de8de25261d58b2`. Abruf/Aufbau verwenden Kerzenabschluss
<= festen Messstichtag. Gespeicherte Reihen werden am damaligen `ende` gemeinsam
abgegrenzt; Teilfenster haben denselben Vertrag. Keine Signalregel geaendert.

**600 Tests bestanden**, sechs konkrete alte Messpfade durch Gegenfaelle erreicht,
**6/6 Sabotagen erkannt**. Originalfall selbst bestaetigt: 2.481 Kerzen, letzte
27.09.2026 08:00 UTC bei Stichtag 08:29:08.840 offen; jetzt 2.480 abgeschlossene,
1.509 im Handelsfenster. Fuenf eingefrorene Varianten gegen F09 allein neu gerechnet:
je ein Teilverkauf weniger, Endwerte 0,36 bis 0,66 USD niedriger, mit unabhaengigem
Losbuch abgeglichen; H1-Endwerte gleich. Keine Mindestrendite als Erfolgskriterium.

Bericht und Wiederholung: `docs/nacharbeit-2026-09-28/D01.md`; Zahlen separat
`d01-ergebnis.json`. Audit/F09/Originalinputs bleiben unveraendert. Eigener Zweig
wird auf GitHub gesichert und ausschliesslich `Tests` fuer exakte HEAD-SHA geprueft.
Lokaler CI-Beleg und Abschlussbundle liegen getrennt unter `audit-backups`.

Keine E44.4/E44.5-Uebernahme, main-/Live-Schalter, Nachrichten, Orders oder Deployments.
Sicherungstag unveraendert auf `469be65`. F01/F12 und weitere Auditfehler bleiben offen.
Naechster Auftrag: **3a, GPT-6 Astra / hoch**, Vertrag fuer Ausfuehrung/Risiko und
Handfaelle; danach **3b, GPT-6 Sol / hoch**, klare Umsetzung. Die Empfehlung ist
aufgabenbezogen und stellt das Modell nicht automatisch um. D01 danach beenden.

---

## 28.09.2026 — Audit-Nacharbeit, Etappe 1 (F09), nur Arbeitszweig

Aus gesichertem aktuellem main `469be65` wurde `codex/fix-f09-wiederanlage`
angelegt. Der Long-Abrechner verkauft numerische Rundungsreste bei einem eigentlich
vollstaendigen Teilverkauf mit. Dadurch verwenden Folgekaeufe neues Cash und neue
Hoechstbestaende. Keine Strategie-Schalter und keine Signalregeln veraendert.

585 alte plus vier neue Tests bestehen. Drei der neuen Tests scheiterten zuvor;
alle drei gezielten Sabotagen werden erkannt. Fuenf historische Zeilen stimmen
nach der Korrektur mit dem unabhaengigen Audit-Losbuch ueberein. F09 kann die
Rendite je nach Variante erhoehen oder senken. D01/F01/F12 bleiben offen.

Bericht: `docs/nacharbeit-2026-09-28/F09.md`. Etappen, Modellempfehlungen und
Startauftrag: `docs/nacharbeit-2026-09-28/ETAPPEN.md`.
Naechste Etappe D01: **GPT-6 Sol, Aufwand mittel**. Die Modelleinstellung wurde
durch die Arbeit nicht automatisch umgestellt. Jede Etappe getrennt abschliessen.

Kein Merge-Go, kein main-Push, keine Telegram-Nachricht, kein Messworkflow und
kein Deployment. E44.4/E44.5 sind nicht Teil dieses Korrekturzweigs. Rueckkehrpunkt:
`sicherung/vor-audit-korrekturen-2026-09-28`, lokal als Bundle/ZIP erfolgreich geprueft.

---

> Was zuletzt passiert ist, was offen liegt, was eine neue Session als Erstes wissen
> muss. **Jüngster Abschnitt oben.** Nach jeder abgeschlossenen Arbeit einen datierten
> Abschnitt hier ergänzen — nicht erst am Ende eines Vorhabens.
>
> Kurzfassung: `00_STAND.md`. Fertiger Prompt für einen neuen Chat: `STARTPROMPT.md`.

---

## 27.09.2026 (24) — E44.3 gebaut: E42 „Ausbruch mit Rücktest“ (Zweig, wartet auf Go)

- **Zweig `claude/e44-3-ausbruch-ruecktest-k7m2qx`** (von `main` 2643f13). **585 Tests grün**
  (545 + 40 neu in `engine/test_e443.py`). **Sabotage `engine/sabotage_e443.py`: 42 Sabotagen.**
  Erster Lauf 39 gefangen; die drei Lücken (Verkaufskerze als Fenster ohne `no_flip`,
  gescheiterter Ausbruch ohne neuen Ausbruch, Hauptstop nimmt den Teil nicht mit) mit drei
  Tests geschlossen, zweiter Lauf: **42 von 42 gefangen**, danach wieder 585 grün.
- **Schalter** `ausbruch_ruecktest` (Default `false`) und `ruecktest_fenster` (12) in
  `site/data/config.json`, mit Hinweistext samt Entscheidungs- und Ausschalt-Regel aus Plan
  Abschnitt 8. Solange aus: exakt dieselben Signale (Test). **Nicht live, nicht gemessen.**
- **Kaiser 27.09.2026 (neue Frage 4): „Nur die 25 %“** — der Stop an der Marke gilt nur für den
  Rückkauf-Teil, der Rest behält Stop und Einstand. Alles, was die Regel sonst offen ließ, steht
  als **Bau-Auslegung** im Plan, Abschnitt 6 K1 (u. a. neue Signaltypen `RUECKKAUF`/
  `RUECKKAUF_STOP`, Feld `bestand_pct` für „voll investiert“, Rückkauf aus FLAT eröffnet eine
  Position auf dem aktuellen Bein, spiegelbildlich für Short).
- **Zustand in `state.json`:** 10 neue Felder (`e42_*`, `bestand_pct`). Prüfweg am Stück gegen
  Kerze für Kerze in getrennten Läufen: Signale **und alle Telegram-Texte** gleich, in zwei
  Szenarien (nach Teilverkauf am Hoch mit Warten, Rückeroberung und Stop des Teils; aus FLAT
  nach Rest-Verkauf).
- **Versand geändert (auch ohne E42 wirksam, nur bei Nachhol-Läufen):** Meldungen und Signale
  gehen jetzt **je Kerze** raus (E41-Meldung, E42-Meldungen, Signale dieser Kerze). Vorher kamen
  erst alle E41-Meldungen, dann alle Signale. Im Normalbetrieb (eine Kerze je Lauf) gleich.
- **Nebenbei erledigt:** `_hinweis_be_im_plus` in `config.json` berichtigt (Rest aus E43).
- **Backtest:** `simulate()` bucht den Rückkauf und verkauft beim Stop genau diese Einheiten;
  `gegengeschaefte()` und Recall-Typen kennen die neuen Signale; Chart-Marker `RK`/`RKS`. **Keine
  Gitterzeile** — die kommt mit E44.5.
- **Hochladen:** Aus dieser Sitzung war GitHub gesperrt (Repo nicht für die Sitzung freigegeben,
  Kaisers Rechner ohne GitHub-Zugang aus der Sandbox). Der Stand liegt als git-Bundle in
  `BTC-Trading\Claude outputs\e44-3.bundle`, dazu `E44-3-HOCHLADEN.cmd` im Ordner `BTC-Trading`
  (Doppelklick: Zweig hoch, Unterlagen nach `main`). Steht der Zweig auf GitHub, ist das erledigt.
- **Nächster Schritt:** Kaisers Go für `main` (Schalter bleibt aus, ändert live nichts außer der
  Versand-Reihenfolge bei Nachhol-Läufen). Danach **E44.4** (`verkauf_faktor`, Aufwand mittel),
  dann E44.5 (Gitter messen). Offen für E44.5: zählen, wie oft ein Rückkauf auf eine alte Marke
  kam (die Beobachtung hat bis zum Ausbruch keine Frist).

---

## 26.09.2026 (23) — Kaisers Go: E44.1 und E44.2 in main, Antworten auf die Fragen

- **Go für `main`:** Zweig `claude/blissful-maxwell-9uwt6x` nach `main` gemerged (Commit
  `db9b468`), **545 Tests grün**. Archiv und Wechselwirkungs-Abschnitt sind damit live
  (Handelsverhalten unverändert).
- **cron-job.org:** Kaiser will das Archiv nicht von Hand starten, und die Flush-Wache hatte
  noch keinen externen Anstoß. Anleitung für beide Aufträge:
  `ANLEITUNG-PUENKTLICHER-START.md`, **Schritt 5**. Einrichten muss Kaiser selbst (sein Konto,
  sein Schlüssel). Offen, bis er „eingerichtet“ meldet.
- **Frage 1 (E42):** nicht verstanden, im Plan (Abschnitt 10) mit Beispiel neu gestellt. Neuer
  Furkan-Beleg für Ausbruch und Rücktest: 02.08. 14:17.
- **Frage 2 (Shorts):** **Ja.** E44.6 wird gebaut, zuerst ein eigener Bauplan-Abschnitt. Zwei
  Punkte dafür stehen im Plan (Bein-Wahl hängt heute an genau einer erlaubten Richtung; Furkans
  Warnung vor späten Shorts 10.09. 19:40).
- **Frage 3 (Transkripte):** liegen jetzt in `wissens-layer/05_quellen/`. **Hinweis an Kaiser:**
  Das Repo ist öffentlich, vollständige Transkripte gehören laut Arbeitsregeln nicht hinein.
  Nicht gelöscht, Entscheidung bei ihm.

**Nachtrag:** Kaiser hat die drei E42-Werte bestätigt („1=ja, 2=ja, 3=ja“). **Nächster Schritt:
E44.3 bauen** (Aufwand hoch), danach der Bauplan-Abschnitt E44.6 (Shorts). Startprompts: Plan, Abschnitt 9a.

---

## 26.09.2026 (22) — E44.2 gebaut: Wechselwirkungen und Monats-Probe (Zweig, wartet auf Go)

Auf Zweig `claude/blissful-maxwell-9uwt6x`, zusammen mit E44.1. In `backtest.py`:
`e442_vierergruppen` (findet alle sauberen 2×2-Gruppen im Gitter, Basis = Ecke mit beiden
Schaltern aus), `e442_wechselwirkung`, `monats_probe` (hält der Vorsprung ohne den
günstigsten Monat?) und der neue Berichtsabschnitt „E44: Wechselwirkungen und
Monats-Probe“. Gegen das echte Gitter geprüft: **dieselben 16 Gruppen** wie in der Analyse.
Kein Schalter, keine Gitterzeile, kein Urteil geändert. 10 neue Tests, **545 grün**,
`sabotage_e442.py` **8/8 gefangen**. Die Probe fand beim ersten Lauf eine echte Testlücke
(beide Hälften hatten im Test dieselben Zahlen, eine vertauschte Hälfte fiel nicht auf),
behoben.

**Offen für Kaiser: ein Go für `main` deckt E44.1 und E44.2 ab.** Danach: Actions →
Coinalyze-Archiv → Run workflow (einmal von Hand), und beim nächsten Backtest erscheint
der Abschnitt „E44“ im Bericht.

**Nächster Schritt danach:** E44.3 (E42 Ausbruch mit Rücktest), braucht Kaisers Antwort
auf Frage 1 im Plan, Abschnitt 10. Aufwand hoch. Startprompt: Plan, Abschnitt 9a.

---

## 26.09.2026 (21) — E44.1 gebaut: Coinalyze-Archiv (Zweig, wartet auf Go)

Kaiser: *„Leg mir 44.1 und 44.2 los und bereite jede Etappe so vor, dass ich im neuen Chat
damit beginnen kann.“* Startpunkte je Etappe stehen jetzt im Plan, Abschnitt 9a,
Einzelheiten zu E44.1/E44.2 in 9b/9c, Platz für Kaisers Antworten in Abschnitt 10.

**E44.1 gebaut** auf Zweig `claude/blissful-maxwell-9uwt6x`: `engine/archiv.py` (mischt
OI, Liquidationen, Futures-Delta, Long-Short in `site/data/archiv/coinalyze_4h.json`, nur
abgeschlossene Kerzen, neu gewinnt, alt bleibt), `backtest.py` mischt das Archiv vor dem
Aufbau der Reihen dazu und nennt im Bericht, wie viele OI-Punkte nur aus dem Archiv stammen.
Neuer Workflow `.github/workflows/archiv.yml` (täglich 03:47 UTC plus Knopf). `main.py`
unberührt. 8 neue Tests, **535 grün**, `sabotage_e441.py` **8/8 gefangen**.

**Solange das Archiv leer ist oder nicht älter als Coinalyze, ändert sich keine Zahl.**
Der Nutzen beginnt erst, wenn der Workflow in `main` läuft; jeder Tag ohne ihn kostet rund
6 alte 4h-Punkte. **Offen für Kaiser: Go für `main`.** Danach einmal anstoßen: Actions →
Coinalyze-Archiv → Run workflow.

**Als Nächstes:** E44.2 (läuft in diesem Chat weiter).

---

## 26.09.2026 (20) — E44: Kombinations-Analyse, Bauplan geschrieben, nichts gebaut

**Auftrag Kaiser:** *„welche dieser Tests und Indikatoren miteinander kombiniert und getestet
werden können. Um am Ende mehr Rendite rauszuholen […] Insbesondere beachte Furkans
Strategien.“* Ergebnis: `docs/PLAN-E44-KOMBINATIONEN.md`.

**Grundlage:** keine neue Messung. Nachgerechnet aus `BACKTEST.md` (Lauf 26.09. 15:18) und
`site/data/backtest_signals.json` (Nachbau endet bei 13.509 € gegen 13.532 € im Bericht).
Befunde:
- 16 saubere 2×2-Gruppen im Gitter: Filter × Filter bis −10,2 Punkte über die Summe hinaus,
  Verstärker × Verstärker additiv, Ergänzungen bis +13,7. Eingetragen in
  `GEMESSEN-UND-ENTSCHIEDEN.md`, Abschnitt „Wechselwirkungen“.
- Live-Einstellung: 50 % der Zeit in einer Position, zeitgewichtet 35 % investiert, in einer
  Position fast immer 100 %, Haltedauer Median 4 Tage. Rest-Verkauf bei Gegen-Muster zu
  7 von 9 richtig, die 2 falschen sind die Rallys (07.04. +5,4 %, 19.08. +14,4 %). Die Stops
  hielten die Engine aus beiden großen Abwärtsphasen heraus.
- Furkan-Abgleich über die ausgewerteten Auszüge in `docs/`. **Die Rohabschriften im
  Backup-Repo waren nicht lesbar** (Rechte-Prüfung der Arbeitsumgebung hat das Auflisten
  blockiert), das steht als offene Frage im Plan.

**Vorschlag:** E42 (Ausbruch mit Rücktest) als Partner von `high_exit`, `verkauf_faktor`
0,67 und `rest_halten` im 2³-Gitter. Hauptzeile „LIVE-heute +E42“ entscheidet nach der
bekannten Regel plus Monats-Probe, die übrigen Zeilen brauchen 2 Punkte in beiden Hälften.
K4 (Shorts im Abwärts-Regime) nur nach Kaisers Grundsatz-Ja.

**Offen für Kaiser:** die drei Fragen in Abschnitt 10 des Plans. **Sofort machbar ohne
Antwort:** E44.1 (Coinalyze-Archiv) und E44.2 (Wechselwirkungs-Tabelle und Monats-Probe
im Bericht), beide Aufwand mittel. Code unberührt, 527 Tests grün.

---

## 26.09.2026 (19) — E43.7 in main nachgetragen, E43 abgeschlossen

**Kaiser:** *„43.7 und 43.8 müssten schon erledigt sein.“* Stimmt: E43.8 war in `main`.
E43.7 war um 13:44 Uhr in einem **parallelen Chat** erledigt worden (Zweig
`claude/e43-6-gitterzeilen-eo6mzb`, Commit `5bc1030`), der E43.6 ein zweites Mal gebaut
hatte. Nach `main` kam die E43.6-Fassung des anderen Zweigs, E43.7 blieb liegen.

**Getan (reine Unterlagen, direkt in `main`, Kaisers „Ja, leg los“):** die drei
Korrekturen neu eingetragen, nicht kopiert (der Doppel-Zweig hatte leicht andere Zahlen):
E37-Satz, `be_im_plus`-Urteil (Lesefehler, mit E43.8-Zahlen; Randvermerk auch in
`docs/ETAPPENPLAN.md` E19 und `docs/FURKAN-UPDATE-2026-08-03.md` §3), Funding-„Faktor 69“
(= Einheit). Abschnitt „nie entschieden“ in `GEMESSEN-UND-ENTSCHIEDEN.md` mit allen sechs
Messungen geschlossen, Vorbehalt oben um E43.4 ergänzt. Zwei Lehren in
`BEKANNTE-PROBLEME.md`: Fixtures im echten Datenformat bauen; nicht zwei Chats parallel.
`STARTPROMPT.md` auf 527 Tests und E43-abgeschlossen gebracht. **Code unberührt, 527
Tests grün.**

**Offen, klein:** `_hinweis_be_im_plus` in `site/data/config.json` zitiert Furkan ohne die
Vorbedingung — mit der nächsten Code-Änderung auf einem Arbeitszweig berichtigen. Der
Doppel-Zweig `claude/e43-6-gitterzeilen-eo6mzb` ist überholt; löschen macht Kaiser.

**Nächster Schritt (Kaisers Auftrag):** Kombinations-Analyse — welche einzeln gemessenen
Mechanismen und Indikatoren sich sinnvoll kombinieren lassen, mit Furkans Transkripten.

---

## 26.09.2026 (18) — E43.8 gemessen: be_im_plus und release_stale_rest bleiben aus

**Auftrag Kaiser:** „be_im_plus und release_stale_rest jetzt auch messen" — die
letzten zwei aus der Liste der seit Monaten unentschiedenen Schalter
(`02_status/OFFENE-PUNKTE.md`). Auf neuem Zweig
`claude/e43-8-nachmessung-be-im-plus-release-stale-rest` (von `main`) gebaut: zwei
Gitterzeilen mit genau einem Unterschied zur Panel-Zeile, Vorbild E43.6.

**Besonderheit:** beide Schalter sind zustandsabhängig (Break-even-Zeitpunkt bzw.
Rest-Freigabe hängen vom laufenden Positions-Status ab) — anders als
`strict_confirm`/`confirm_t1` (reine Kerzen-Logik) gibt es keine Vorprobe ohne
Simulation. Die Vorprobe zählt deshalb generischer: an wie vielen (Zeitpunkt,
Signaltyp)-Paaren die Gitterzeile überhaupt vom Live-Lauf abweicht
(`e438_signale_verschieden`, verallgemeinert aus dem „Verschieden erkannt" von
E43.3/E43.4). 7 neue Tests, **527 Tests grün**, keine Änderung an `strategy_core.py`
(beide Schalter existieren und rechnen schon richtig), keine eigene Sabotage-Datei.

**Gemessen (GitHub-Actions-Lauf 36250880529, Fenster 18.01.–26.09.2026):**

| Schalter | Vorprobe (Treffer) | Rendite | H1 | H2 | Signale | Urteil |
|---|---:|---:|---:|---:|---:|---|
| **Live (Basis)** | — | +35,3 % | +23,6 % | +9,5 % | 244 | — |
| `be_im_plus` | 205 Paare | +18,0 % | +8,1 % | +10,0 % | 348 | H1 −15,5, H2 +0,5 → nicht erfüllt |
| `release_stale_rest` | 2 Paare | +34,6 % | +22,5 % | +9,5 % | 244 | H1 −1,1, H2 +0,0 → nicht erfüllt |

**Beide Schalter bleiben aus.** `be_im_plus` ist dabei — anders als A2/A3/A5/E43.6 —
ein echter, großer Befund: 205 von 244 Signal-Paaren ändern sich, die Signalzahl
steigt um 104 (244→348), die Rendite bricht um 17,3 Punkte ein, fast ausschließlich in
Hälfte 1. Der frühere Break-even-Stop wirft die Engine öfter aus Positionen, die
später weitergelaufen wären. Reiht sich bei den zwölf zuvor gemessenen Filtern ein
(„Zwölf gemessene Filter, zwölf schlechter", `00_STAND.md`). `release_stale_rest`
ändert dagegen kaum etwas (2 von 244 Paaren) und verfehlt die Regel nur knapp.
Am Handelsverhalten ändert sich nichts. Einzelheiten:
`docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „Messung E43.8".

**Damit ist Punkt 6 aus `02_status/OFFENE-PUNKTE.md` (seit Monaten unentschiedene
Schalter) vollständig abgeschlossen:** alle sechs (`rest_halten`, `strict_confirm`,
`confirm_t1`, `cooldown_h`, `be_im_plus`, `release_stale_rest`) sind jetzt mit genau
einem Unterschied gemessen. Alle bleiben aus.

**Nächster Schritt, offen:** E43.7 (Wissens-Layer-Texte berichtigen — u. a. das
`be_im_plus`-Lesefehler-Urteil aus der Gesamtprüfung, jetzt mit den echten Zahlen von
E43.8 unterlegbar), oder E41.6/E42 (Kaisers Entscheidung).

---

## 26.09.2026 (17) — E43.6 gemessen: alle vier Schalter bleiben aus

**Auftrag Kaiser:** „Merge nach main und E43.6 bauen" — A5 (siehe unten) nach `main`
gemergt, dann E43.6 auf neuem Zweig `claude/e43-6-nachmessung-vier-schalter` (von
`main`) gebaut: vier Gitterzeilen mit genau einem Unterschied zur Panel-Zeile
(`rest_halten`, `strict_confirm`, `confirm_t1`, `cooldown_h=48`), je eine Vorprobe im
Datensatz, Entscheidungsregel wie E41/E43.2–E43.5/A5.

**Vorbereitung:** `_confirm_long()`/`_confirm_short()` in `strategy_core.py` auf eine
neue, öffentliche `confirm_ok()` zurückgeführt (einzige Rechenstelle) — `evaluate()`
UND die `strict_confirm`/`confirm_t1`-Vorproben lesen jetzt von derselben Funktion.
Reiner Refactor, kein Verhaltensunterschied. 13 neue Tests, **520 Tests grün.** Keine
eigene Sabotage-Datei (kein neuer Rechenweg außerhalb des bekannten
`confirm_ok`/`exit_pat`/`_cooldown_ok`, wie E43.2).

**Gemessen (GitHub-Actions-Lauf 36249824852, Fenster 18.01.–26.09.2026):**

| Schalter | Vorprobe (Treffer) | Rendite | H1 | H2 | Signale | Urteil |
|---|---:|---:|---:|---:|---:|---|
| **Live (Basis)** | — | +35,3 % | +23,6 % | +9,5 % | 244 | — |
| `rest_halten` | 11 Positionen | +34,5 % | +19,4 % | +12,7 % | 236 | H1 −4,3, H2 +3,2 → nicht erfüllt |
| `strict_confirm` | 1.356 von 1.505 Kerzen | +28,5 % | +26,0 % | +1,9 % | 206 | H1 +2,4, H2 −7,6 → nicht erfüllt |
| `confirm_t1` | 9 von 14 Ersteinstiegen | +34,9 % | +22,8 % | +10,3 % | 240 | H1 −0,8, H2 +0,9 → nicht erfüllt |
| `cooldown_h` (48h) | 1 Einstieg | +33,4 % | +21,8 % | +9,5 % | 244 | H1 −1,8, H2 +0,0 → nicht erfüllt |

**Alle vier Schalter bleiben aus.** Rückgang bei allen vieren identisch zur Live-Zeile
(+0,0 Punkte) — die Regel scheitert überall am ersten Kriterium (beide Hälften ≥ 1
Punkt besser). Auffällig: `strict_confirm` sah in H1 sogar besser aus (+2,4 Punkte),
drehte in H2 aber um 7,6 Punkte — genau die Art von Einzelhälften-Vorsprung, vor der
die Regel schützen soll (dieselbe Lehre wie B3/E41.6). Am Handelsverhalten ändert sich
nichts. Einzelheiten: `docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „Messung
E43.6".

**Damit sind `confirm_t1` und `cooldown_h` aus der Liste der seit Monaten
unentschiedenen Schalter raus** (`02_status/OFFENE-PUNKTE.md`). Offen bleiben
`be_im_plus` und `release_stale_rest` — dieselbe Messlücke, noch nicht angegangen.

**Nächster Schritt, offen:** E43.7 (Wissens-Layer-Texte berichtigen), `be_im_plus`/
`release_stale_rest` messen, oder E41.6/E42 (Kaisers Entscheidung).

---

## 26.09.2026 (16) — A5 gemessen und entschieden: bleibt aus

**Auftrag Kaiser:** A5 messen wie in `OFFENE-PUNKTE.md` Punkt 8 beschrieben. Erst
zählen, an wie vielen Kerzen im Fenster `next_pivot_beyond()` mit der Live-Historie
(1.300 Kerzen) ein anderes nächstes Pivot-Hoch fände als mit der Backtest-Historie (ab
10.08.2025). Bei 0 Treffern nur dokumentieren, sonst eine Gitterzeile mit genau einem
Unterschied bauen.

**Zählung (GitHub-Actions-Lauf 36247317191):** 53 von 1.177 nachstellbaren Kerzen im
Fenster hätten ein anderes nächstes Pivot gesehen (long oder short) — Treffer > 0, also
weiter wie im Auftrag beschrieben.

**Gebaut:** neuer Parameter `evaluate(high_exit_hist="voll"|"live")` in
`strategy_core.py`. `"live"` beschränkt die Pivotsuche NUR für den `high_exit`-
Teilverkauf (Teilgewinn am letzten Hoch) auf die letzten `HIGH_EXIT_LIVE_KERZEN`
(= `main.LIMIT_HAUPT`, 1.300) Kerzen — kein Eingriff in die übrigen Pivot-Verwender
(Impuls, Gegenzonen, 1D-Ebene). Default `"voll"` = bisheriges Verhalten; `main.py` lädt
ohnehin nur 1.300 Kerzen, dort also folgenlos. Gitterzeile „LIVE-heute +Pivot-Hoch nur
letzte 1.300 Kerzen (A5)“ mit genau einem Unterschied zur Panel-Zeile. `a5_next_pivot_
beyond`, `a5_einschalten`, `a5_abschnitt` im Bericht (Vorbild E43.3/E43.4). 8 neue
Tests (Mechanismus in `evaluate()`, Berichtsabschnitt, Konfig-Default) — **507 Tests
grün.** Keine eigene Sabotage-Datei (kein neuer Rechenweg außerhalb des bekannten
`next_pivot_beyond`, wie E43.2).

**Gemessen (GitHub-Actions-Lauf 36248384303, Fenster 18.01.–26.09.2026):**

| Variante | Rendite | Rückgang | H1 | H2 | Signale |
|---|---:|---:|---:|---:|---:|
| **Live (voll)** | +35,3 % | −9,9 % | +23,6 % | +9,4 % | 244 |
| Pivot-Hoch nur letzte 1.300 Kerzen (live) | +35,3 % | −9,9 % | +23,6 % | +9,4 % | 244 |

**Urteil nach der vorab festgelegten Entscheidungsregel** (wie E41/E43.2/E43.3/E43.4):
in beiden Hälften ≥ 1 Punkt besser: **nein** (H1 ±0,0, H2 ±0,0). Rückgang: gleich.
**Regel nicht erfüllt — `high_exit_hist` bleibt auf `"voll"`.**

**Einordnung:** dieselbe Lehre wie bei A2/E43.3 — der Fehler ist im Prinzip echt (53
von 1.177 Kerzen sehen ein anderes Pivot), wirkt sich im gemessenen Fenster aber auf
kein einziges Signal aus. Kein Renditebefund, weder dafür noch dagegen. Am Code sonst
nichts geändert. Einzelheiten: `docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „A5“.

**Nächster Schritt, offen:** E43.6 bauen (wartet auf Kaisers Go, siehe unten) oder
E41.6/E42 (Kaisers Entscheidung).

---

## 26.09.2026 (15) — E43.6-Bauplan geschrieben, wartet auf Kaisers Go zum Bauen

Auftrag Kaiser: erst den Bauplan-Abschnitt E43.6 schreiben und zeigen, noch nicht bauen.
Erledigt in `docs/PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „E43.6": je Schalter
(`rest_halten`, `strict_confirm`, `confirm_t1`, `cooldown_h`) eine Gitterzeile mit genau
einem Unterschied zur heutigen Panel-Zeile, eine Vorprobe im Datensatz und die
Entscheidungsregel wie bei E43.2/E43.3/E43.4 (beide Hälften ≥ 1 Punkt besser, Rückgang
nicht mehr als 1 Punkt tiefer).

**Geklärt: Muster-5-Wiederholung lohnt sich jetzt nicht.** Teil C des Prüfberichts wollte
sie „nach der Korrektur" von A2/A3. Beide Korrekturen (`muster_cvd`, `muster_oi`) sind
inzwischen gemessen und **beide auf dem alten Wert geblieben** (`"alt"`, `"usd"`) — an der
Mustererkennung, an der Muster 5 hängt, hat sich also nichts geändert. Eine Wiederholung
jetzt würde exakt dieselben Zahlen liefern wie zuletzt. Zurückgestellt, nicht vergessen:
erst sinnvoll, wenn einer der beiden Schalter tatsächlich live geht.

**Keine Code-Änderung, kein Test lief.** 493 Tests bleiben Referenz. Noch nicht gebaut:
vier neue `V(...)`-Zeilen und ein Berichtsabschnitt „E43.6" in `engine/backtest.py`,
geschätzt 4–8 neue Tests, aller Wahrscheinlichkeit nach ohne eigene Sabotage-Datei
(kein neuer Rechenweg, nur neue Messzeilen).

**Nächster Schritt:** Kaisers „Ja" zum Bauplan, dann Bau auf einem `claude/...`-Zweig,
Vorprobe je Zeile, Messung, Urteil nach der Entscheidungsregel — wie bei E43.3/E43.4.

---

## 26.09.2026 (14) — Kaisers Go: E43.4b in main, weiter im neuen Chat

Kaiser: *„Ja“* (Go für `main`). Arbeitszweig `claude/e43-4-open-interest-9mmh0l` per
Fast-Forward nach `main`. Die OI-Zeile im Lage-Abruf zeigt ab dem nächsten Abruf die
Kontrakte (reine Anzeige). **493 Tests grün in `main`.** `STARTPROMPT.md` nachgezogen.

**Nächster Schritt: E43.6**, im neuen Chat. Zuerst den Bauplan-Abschnitt „E43.6“ im
Plan schreiben und Kaiser zeigen: vier Gitterzeilen mit genau einem Unterschied zur
heutigen Live-Zeile (`rest_halten`, `strict_confirm`, `confirm_t1`, `cooldown_h`), je
eine Vorprobe, dass der Schalter im Datensatz überhaupt etwas ändert, und die
Entscheidungsregel vorab (wie E43.2). **Dabei klären:** Die Muster-5-Wiederholung war
„nach der Korrektur von A3“ gedacht. `muster_oi` blieb aber `"usd"`. Ob sie noch etwas
misst, gehört in den Bauplan. Aufwand: mittel.

---

## 26.09.2026 (13) — E43.4b: OI-Zeile im Lage-Abruf in Kontrakten (Arbeitszweig)

**Kaisers Auftrag:** *„Bau zuerst die OI-Zeile in Kontrakten“* (seine Antwort auf die
Anzeige-Frage A2/A3). Zweig: `claude/e43-4-open-interest-9mmh0l`. **`main` ist
unverändert.** Reine Anzeige, kein Schalter, kein Signal ändert sich.

- Die OI-Zeile zeigt hinter dem Dollar-Wert die Änderung der Kontrakte. Pfeil und Hinweis
  folgen den Kontrakten. Zeigen Dollar und Kontrakte in verschiedene Richtungen, steht
  dabei „der Dollar-Anstieg/-Rueckgang kommt nur vom Kurs“ bzw. „in Dollar vom Kurs
  verdeckt“. Ohne Kontrakt-Reihe (Kraken-Rückfall) bleibt die Zeile wie bisher.
- Die Musterzeile ändert sich nicht, sie rechnet weiter wie der Handel.
- **493 Tests grün** (+5). `sabotage_e434b.py` 9/9 beim ersten Lauf.
- Regel und Beispiel: `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „E43.4b“.

**Offen für Kaiser:** „Go“ für `main`. **Danach:** E43.6, zuerst der Bauplan-Abschnitt.

---

## 26.09.2026 (12) — Kaisers Go: E43.4 in main

Kaiser: *„Go für main“*. Arbeitszweig `claude/e43-4-open-interest-9mmh0l` per
Fast-Forward nach `main` (`main` hatte sich seit dem Abzweigen nicht bewegt).
`muster_oi` bleibt `"usd"`, das Handelsverhalten ändert sich nicht. **488 Tests grün in
`main`.** `STARTPROMPT.md` auf den Stand nach dem Go gebracht.

Kaisers Frage vor dem Go: Vor heute lag die Rendite bei rund 25 %, jetzt bei 35 %. Der
Sprung kommt von E43.2 (`bein_richtung: "bias"`, Go am Vormittag), nicht von E43.3 oder
E43.4. Belegt aus der Berichtsgeschichte: Lauf 08:23 Live-Zeile +25,2 %, die Zeile „Bein
in Handelsrichtung“ im selben Lauf schon +35,4 %. Die alte Einstellung steht im
heutigen Bericht als „LIVE bis 26.09.2026 (ohne Bein-Richtung)“ unverändert bei +25,2 %.
Nebenbei: Die neue Einstellung trifft Furkans Kauftage seltener (Treffer-Quote 59 → 35 %,
Präzision 35 → 23 %).

**Offen für Kaiser:** die Anzeige-Frage zu A2/A3 (Empfehlung siehe Abschnitt 11).
**Danach:** E43.6, zuerst der Bauplan-Abschnitt.

---

## 26.09.2026 (11) — E43.4 gemessen: bleibt `"usd"`, A3 ist echt und groß

Backtest-Lauf 36236645038 (Arbeitszweig `claude/e43-4-open-interest-9mmh0l`, Fenster
18.01.–26.09.2026). **`main` ist unverändert.**

- **Rendite, beide Hälften und Rückgang identisch** (+35,4 %, H1 +23,6, H2 +9,6,
  −9,9 %). **Regel nicht erfüllt, `muster_oi` bleibt `"usd"`.**
- **Vorprobe:** 210 von 1.504 Kerzen anders erkannt (14 %). Derivate-Pump 96 → 48,
  Kapitulation 21 → 11, Short-Covering 56 → 103, Muster 5 47 → 97.
- **A3 als Zahl:** Die Pump-Bedingung „OI ≥ +3 %“ war in Dollar 296-mal erfüllt, in
  Kontrakten 144-mal. Die Hälfte kam also allein vom Kurs. Bei der Kapitulation: 74
  gegen 30.
- **227 statt 244 Signale**, ohne jede Wirkung auf die Rendite. Das passt nur zu Signalen
  ohne Tranche (Pump-Warnungen). **Schluss, nicht gezählt:** Der Bericht schlüsselt
  Signalarten je Zeile nicht auf.
- Nachgetragen: Plan „Messung E43.4“, `_hinweis_muster_oi`, Gitter-Kommentar. Die
  E43.3-Sabotage „Rückgang zählt nicht“ hat eine eindeutige Vorlage bekommen (ihre Zeile
  gibt es seit E43.4 zweimal), weiter 29/29 gefangen. **488 Tests grün.**

**Offen für Kaiser:**
1. „Go“, den Arbeitszweig nach `main` zu übernehmen? Am Handelsverhalten ändert sich
   **nichts** (`muster_oi` bleibt `"usd"`).
2. Anzeige-Frage für A2 und A3 gemeinsam. **Empfehlung der KI:** keine getrennte
   Muster-Anzeige (Lage-Abruf und Handel würden an rund 14 % der Kerzen verschiedene
   Muster nennen). Stattdessen ein kleiner Anzeige-Schritt: In der OI-Zeile steht die
   Kontrakt-Änderung neben der Dollar-Änderung, und der Hinweis folgt den Kontrakten.

**Danach:** E43.6 (Nachmessungen `rest_halten`, `strict_confirm`, `confirm_t1`,
`cooldown_h`; danach Muster 5). Die Voraussetzung „nach A2/A3“ ist jetzt erfüllt.

---

## 26.09.2026 (10) — E43.4 gebaut (Arbeitszweig), Messung läuft

**Kaisers Auftrag:** *„Ja“* (zum Bauplan E43.4). Zweig:
`claude/e43-4-open-interest-9mmh0l`. **`main` ist unverändert**, live ändert sich nichts:
`muster_oi` steht auf `"usd"`.

- Gebaut wie im Bauplan: `FlowPoint.oi_btc`, `oi_in_btc()` (Umrechnung am OI-Datenpunkt,
  dann auffüllen, live und im Backtest dieselbe Funktion), `oi_aenderung()`, Schalter
  `muster_oi` in `classify_pattern`/`evaluate`/`EVAL_DEFAULTS`/`EVAL_KEYS`/`_BASE`/
  `config.json`, Anzeige rechnet wie der Handel, Gitterzeile „LIVE-heute +OI in
  Kontrakten (E43.4)“, Berichtsabschnitt „E43.4“ (Vorprobe, A3 als Zahl, Urteil).
- **488 Tests grün** (467 + 21). `sabotage_e434.py`: 37 von 37 gefangen, beim ersten
  Lauf. Drei Vorlagen in `sabotage_e433.py` auf den neuen Wortlaut nachgezogen (E43.4
  hat dieselben Zeilen geändert). Alle älteren Proben erneut gelaufen, alle Sabotagen
  gefangen: E43.3 29, E43 7, E38 24, E38.1 17, E39 25, E40 27, E41 58.
- Einzelheiten: `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, „Umsetzung E43.4“.

**Offen:** Backtest auf GitHub (Workflow „Backtest“ auf dem Arbeitszweig), dann Urteil
nach der vorab festgelegten Regel, dann Kaisers Go.

---

## 26.09.2026 (9) — Bauplan E43.4 (Open Interest in Kontrakten)

**Kaisers Auftrag:** zuerst den Bauplan-Abschnitt E43.4 schreiben und zeigen, dann bauen.
Zweig: `claude/e43-4-open-interest-9mmh0l`. Reine Planung, **am Code wurde nichts
geändert**, 467 Tests weiter grün. `main` ist unverändert.

**Ergänzt in `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „E43.4“:**
- Schalter `muster_oi` (`"usd"` Default | `"btc"`). Bei `"btc"` rechnet `oi_chg` in
  Kontrakten, für **alle fünf** Muster (Muster 1 fehlte in der Tabelle des Prüfberichts),
  Schwellen unverändert.
- **Abweichung vom Vorschlag im Prüfbericht:** nicht in `classify_pattern` durch den Kurs
  teilen, sondern jeden echten OI-Punkt mit dem Kurs seiner eigenen Kerze umrechnen und
  erst dann auffüllen. Sonst erfinden aufgefüllte Werte eine OI-Bewegung in Höhe der
  Kursbewegung. Das träfe die ersten 11 Kerzen des Messfensters, das dort beginnt, wo das
  OI einsetzt, und live eine fehlende letzte OI-Kerze.
- Entscheidungsregel vor der Messung wie E43.3, dazu Ausschalt-Regel, Vorbedingung
  „misst nichts“, Vorprobe im Datensatz (A3 als Zahl) und in den Tests (`demo_oi_usd`
  mit Gegenprobe; heute nachgeprüft).
- Die OI-Zeile im Lage-Abruf („Positionen werden geschlossen“) ist A3 in der Anzeige.
  Empfohlen als eigener kleiner Anzeige-Schritt, nicht in E43.4.

**Offen:** Kaisers Zustimmung zum Bauplan, dann der Bau (Aufwand **hoch**).

---

## 26.09.2026 (8) — Kaisers Go: E43.5 und E43.3 in main

Kaiser: *„Go“*. Arbeitszweig `claude/btc-signal-engine-start-hyiqny` per Fast-Forward
nach `main`. `muster_cvd` bleibt `"alt"`, das Handelsverhalten ändert sich nicht.
**467 Tests grün in `main`.** Nächster Schritt: E43.4 (Bauplan zuerst), Aufwand hoch.

---

## 26.09.2026 (7) — E43.5 und E43.3 gebaut und gemessen (Arbeitszweig)

**Kaisers Auftrag:** *„Ja, bau E43.5 und E43.3"*. Zweig:
`claude/btc-signal-engine-start-hyiqny`. **`main` ist unverändert.**

**E43.5 fertig** (Befund A4, Bauplan im Plan-Abschnitt „E43.5"):
- `test_mehr_historie_aendert_die_signale_nicht` summiert das CVD jetzt je Ladefenster
  ab null (wie live) und nimmt die Live-Einstellung aus der Panel-Zeile. Die alte,
  hartcodierte Liste war veraltet (ohne `stop_rueckeroberung`, ohne `bein_richtung`).
- Neues Pump-Szenario. Die Vorprobe beweist, dass Muster 2 erreicht wird. Ein
  Befund-Test beweist A2: 400 und 1.200 geladene Kerzen ergeben verschiedene Muster, und
  jede Abweichung ist ein Derivate-Pump.
- **450 Tests grün.** `sabotage_e433.py` 5 von 5 gefangen.

**Neuer Nebenbefund A5 (nicht gemessen, nicht behoben):** „Teilgewinn am letzten Hoch“
hängt von der Länge der geladenen Historie ab (`next_pivot_beyond` sucht in allen
Kerzen). Eingetragen in `OFFENE-PUNKTE.md` Punkt 8.

**E43.3 gebaut** (Befund A2, Plan-Abschnitte „E43.3“, „Ergänzungen“ und „Umsetzung
E43.3“):
- Neuer Schalter `muster_cvd` (`"alt"` | `"usd"`), Default `"alt"` in `config.json`,
  `EVAL_DEFAULTS` und `_BASE`. Bei `"usd"` vergleicht Muster 2 Spot- und Futures-Delta
  als Dollar-Beträge im 12-Kerzen-Fenster. Anzeige und Handel rechnen mit demselben Wert.
- Gitterzeile „LIVE-heute +Muster 2 in Dollar (E43.3)“, genau ein Unterschied zur
  Panel-Zeile. Neuer Berichtsabschnitt „E43.3“: zählt die umklassifizierten Kerzen,
  zählt, wie oft live und Backtest verschieden erkannt hätten, und prüft die
  Entscheidungsregel selbst.
- **467 Tests grün.** `sabotage_e433.py`: 29 Sabotagen, alle gefangen (eine brauchte
  einen zusätzlichen Test, siehe Plan).
- **Offene Entscheidung für Kaiser nach der Messung:** Sonderregel aus dem Prüfbericht
  (Korrektur nur in der Anzeige, Handel bleibt `"alt"`) hieße, dass Anzeige und Handel
  auseinanderlaufen. Nicht gebaut, bis Kaiser das will.

**Backtest gemessen** (GitHub-Lauf 36233723729, Fenster 18.01.–26.09.2026):
- **E43.3:** Nur **2 von 1.504** Kerzen anders erkannt. Rendite (+35,3 %), beide Hälften,
  Rückgang und 244 Signale identisch. **Regel nicht erfüllt, `muster_cvd` bleibt
  `"alt"`.** Live gegen Backtest wich mit `"alt"` an 1 von 1.175 Kerzen ab, mit `"usd"`
  an 0: A2 ist echt, aber klein. Der größere offene Hebel der Mustererkennung ist A3
  (E43.4).
- **E41 auf der neuen Live-Basis:** Die Ausschalt-Regel **schlägt nicht mehr an**
  (Rückgang gleich −9,9 %, H1 +4,0, H2 +0,2 Punkte für live). Der Bericht meldet
  „Bleibt an“. Der Streitpunkt vom 23.09. ist damit erledigt, ohne dass die Regel
  geändert wurde (`docs\PLAN-E41-STOP.md`, „Nachmessung 26.09.2026“).
- **E43.2-Ausschalt-Probe hält:** `auto` H1 +20,0 / H2 +4,3 gegen `bias` +23,6 / +9,5.

**Offen für Kaiser:**
1. „Go“, den Arbeitszweig nach `main` zu übernehmen? Am Handelsverhalten ändert sich
   **nichts** (`muster_cvd` bleibt `"alt"`). Es kämen: die besseren Tests (E43.5), der
   Schalter samt Gitterzeile und Berichtsabschnitt, die Unterlagen.
2. Sonderregel (Anzeige-Korrektur nur im Lage-Abruf): nicht bauen, bis E43.4 gemessen
   ist. Empfehlung der KI: danach Anzeige und Handel gemeinsam entscheiden.

**Nächster Schritt nach dem Go:** E43.4 (OI in Kontrakten statt Dollar, Befund A3):
zuerst den Bauplan-Abschnitt schreiben, dann bauen. Aufwand **hoch**.

---

## 26.09.2026 (6) — Bauplan E43.3 (Muster 2 in Dollar)

**Kaisers Auftrag:** *„Ja, bereite den Bauplan für E43.3 vor."* — reine Planung, **am
Code wurde nichts geändert**, 448 Tests weiter grün.

**Ergänzt in `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Abschnitt „E43.3“:**

- Genaue Fehlerdiagnose: `_slope()` dividiert die (offset-unabhängige) Fenster-Differenz
  der kumulierten CVD-Reihen durch ihren willkürlichen Startwert — dieselbe reale Lage
  klassifiziert je nach Startwert der Summe verschieden (Beleg: `demo_slope.py`,
  Prüfbericht-Anhang). Zusatzfehler: `fut_cvd` ist weiterhin BTC (A1), `classify_pattern`
  vergleicht also nebenbei BTC mit Dollar.
- Vorgeschlagene Regel: neuer Schalter `muster_cvd` (`"alt"`/`"usd"`, Default aus).
  Bei `"usd"` ersetzt eine fensterlokale, in Dollar umgerechnete Differenz (wie E43.1s
  `_fut_cvd_usd`, nur fensterlokal statt über die ganze Historie) den relativen
  `_slope()`-Vergleich — **nur in Muster 2**, Muster 1/3/4/5 bleiben unangetastet
  (ihr Vorzeichen-Vergleich ist von dem Fehler nicht betroffen).
- Entscheidungsregel vor der Messung (wie E41/E43.2) plus die Sonderregel aus Teil E:
  bringt „usd“ keine bessere Rendite, wird es trotzdem als Anzeige-Korrektur übernommen,
  der Handels-Schalter bleibt dann aus.
- Vorprobe vorgeschrieben (Vorbild E43.2s `bias_long != bias_short`): `demo_slope.py`
  muss als echter, bleibender Test verdrahtet werden, sonst ist unbewiesen, dass der
  Schalter im Datensatz überhaupt etwas ändert.
- Abhängigkeit notiert: E43.5 (A4, „mehr Historie“-Test erreicht den Muster-2-Zweig nie)
  sollte vor oder mit E43.3 repariert werden.
- Betroffene Dateien, neue Sabotage-Datei (`sabotage_e433.py`, Vorbild `sabotage_e381.py`)
  und „Bewusst NICHT“ vollständig aufgelistet — Einzelheiten im Plan, nicht hier
  wiederholt.

**Offen:** der eigentliche Bau (Aufwand **hoch** — stärkstes Modell, eigene Etappe),
danach Gitter-Messung gegen die Entscheidungsregel, dann erst Kaisers Go für `main`.

---

## 26.09.2026 (5) — Kaisers Go: E43.1 und E43.2 live in main

**Kaisers Auftrag:** *„Ich gebe das Go für main: E43.1 und E43.2, falls Go. Führe den
Merge/Cherry-Pick aus dem Arbeitszweig nach main aus, aktualisiere die
Live-Konfiguration falls nötig, prüfe die 444 main-Tests, aktualisiere UEBERGABE.md und
00_STAND.md, committe und pushe nach main."*

**Gemacht:**

- Arbeitszweig `claude/dazzling-noether-1w087b` per Fast-Forward nach `main` gemerged
  (er enthielt bereits den ganzen main-Stand als Vorfahren, kein Cherry-Pick nötig).
- **E43.1** ist reine Anzeige und lief damit sofort mit — kein Signal ändert sich.
- **E43.2 — Entscheidungsregel geprüft** (Tabelle in
  `docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`, Fenster 18.01.–26.09.2026):
  - H1: `bias` +23,6 % gegen `auto` +20,0 % → **+3,6 Punkte besser**
  - H2: `bias` +9,5 % gegen `auto` +4,3 % → **+5,2 Punkte besser**
  - Rückgang: `bias` −9,9 % gegen `auto` −10,9 % → **1,0 Punkt flacher**, nicht tiefer

  Beide Bedingungen der vorab festgelegten Regel erfüllt → **`bein_richtung: "bias"`
  seit 26.09.2026 LIVE.**
- **Live-Konfiguration aktualisiert:** `site/data/config.json`, `bein_richtung`
  `"auto"` → `"bias"` (Hinweistext mit der Messung ergänzt).
- **Panel-Zeile in `backtest.py` mitgewandert:** `panel=True` von
  „LIVE-heute +Rueckeroberung vor dem Stop (1 Kerze)" auf
  „LIVE-heute +Bein in Handelsrichtung" verschoben. Neue Ausschalt-Probe-Zeile
  „LIVE bis 26.09.2026 (ohne Bein-Richtung)" ergänzt (Ausschalt-Regel im Kommentar).
- **Folgekorrektur, weil `bein_richtung` jetzt Teil der Live-Basis ist:** alle
  bestehenden „unterscheidet sich in genau einem Punkt von der Live-Zeile"-Zeilen
  brauchten `bein_richtung="bias"` dazu, sonst hätten sie ab jetzt zwei Unterschiede
  statt einem gemessen — betroffen: die drei Ampel-Zeilen (E34), vier Muster-5-Zeilen
  (E38), „MEINE Einstellung ohne Flush" und die beiden E41-Zeilen (Ausschalt-Probe,
  Robustheit 3-Kerzen). Die Trendfilter- und 1D-Ebene-Zeilen sind NICHT betroffen (kein
  Test hält für sie die Basis fest, absichtlich unverändert gelassen).
- **Tests entsprechend angepasst** (Vorbild E41): der Vor-Go-Test
  `test_e43_bein_richtung_zeile_hat_genau_einen_unterschied_zur_live_zeile` ist ersetzt
  durch `test_e43_bein_richtung_ist_live_und_das_panel_ist_mitgewandert` und
  `test_e43_alte_bein_richtung_unterscheidet_sich_in_genau_einem_punkt`.
- **Sabotage-Proben nachgezogen:** `sabotage_e41.py` (5 Muster) und `sabotage_e38.py`
  (1 Muster) suchten exakte Textstellen in `backtest.py`, die durch das Einfügen von
  `bein_richtung="bias"` verschoben waren („Vorlage fehlt" — die Sabotage konnte nicht
  greifen, ein stiller Ausfall). Muster an den neuen Text angepasst, dieselbe
  Sabotage-Absicht beibehalten.
- **448 Tests grün**, alle sechs Sabotage-Dateien (`sabotage_e38/e381/e39/e40/e41/e43`)
  laufen wieder vollständig und fangen alles.

**Offen:** E43.3 bis E43.7 (siehe Plan), sonst wie gehabt E41.6/E42.

---

## 26.09.2026 (4) — E43.1 und E43.2 gebaut (Arbeitszweig)

Nach Kaisers „Go“ zum Umzug (in `main` zusammengeführt) weiter nach Plan
`docs\PLAN-E43-PRUEFUNGS-KORREKTUREN.md`:

- **E43.1 fertig:** Futures-CVD im Lage-Abruf jetzt in Dollar (je Kerze mit deren
  Schlusskurs umgerechnet). Reine Anzeige, kein Signal ändert sich.
- **E43.2 gebaut:** Gitterzeile „LIVE-heute +Bein in Handelsrichtung“ mit genau einem
  Unterschied zur Live-Zeile. Entscheidungsregel vorab im Plan. Backtest auf dem
  Arbeitszweig angestoßen.
- **447 Tests grün**, `sabotage_e43.py` 7 von 7 gefangen.

**Offen:** Ergebnis des Backtests auswerten; Kaisers „Go“ für `main`.

**ZWISCHENSTAND 26.09.2026, 08:20 UTC** (für den Fall eines Abbruchs):
- Zweig: `claude/dazzling-noether-1w087b`. `main` enthält den Umzug der Unterlagen,
  **nicht** E43.1/E43.2.
- Läuft: Backtest auf dem Zweig, GitHub-Lauf **36229181185** (angestoßen 08:14 UTC). Er
  committet `BACKTEST.md` auf den Zweig.
- Nächster Schritt (Aufwand **niedrig**): `git pull` auf dem Zweig, in `BACKTEST.md` die
  Zeile „LIVE-heute +Bein in Handelsrichtung“ gegen „LIVE-heute +Rueckeroberung vor dem
  Stop (1 Kerze)“ nach der Regel im Plan E43.2 prüfen (Hälftentabelle „Robustheitspruefung:
  Fenster halbiert“ und Spalte max. Rückgang). Ergebnis in Plan und hier eintragen,
  Kaiser berichten, um „Go“ bitten.
- Neu seit 26.09.: Regel „Zwischenstände sichern und Aufwand vorschlagen“
  (`ARBEITSREGELN.md`, Abschnitt Budget).
- Neu seit 26.09.: Reine Unterlagen dürfen direkt in `main`; am Ende jedes Schritts
  bekommt Kaiser den fertigen Prompt für den neuen Chat, den Aufwand und den Hinweis,
  ob er den Aufwand ändern soll. Die automatische Rückmeldung zum Backtest im alten Chat
  ist abgesagt: Die Auswertung macht ein neuer Chat (Aufwand niedrig).

---

## 26.09.2026 (3) — Umzug: Unterlagen ins Code-Repo, KI committet selbst

**Kaisers Wunsch:** *„Kannst du nicht alles so umbauen, dass du auf github commitest?“* —
und auf die Frage nach dem privaten Repo: *„das ist nur ein backup und nicht aktuell.
nehme https://github.com/szoceikaiser/btc-signal-app“*.

**Gemacht:** `docs\`, `wissens-layer\`, `STARTPROMPT.md` und `PRUEFPROMPT.md` aus dem
Backup (Stand 26.09.2026, 8:44, plus die Gesamtprüfung) ins Repo `btc-signal-app`
übernommen. Startprompt, Prüfprompt, Arbeitsregeln (Abschnitt Git), Bekannte Probleme,
Start-hier und die wichtigsten Pfade angepasst. Neue Regel: KI pusht auf einen
Arbeitszweig, `main` nur nach Kaisers „Go“.

**Bewusst NICHT übernommen** (öffentliches Repo): `Transkript.md`, `Videos\`,
`Kauftrigger.md`/`Verkaufstrigger.md` (die Daten stehen ohnehin in `backtest.py`),
`heatmap-test\`, `Claude outputs\`, `signal-app-lokal\`, die Windows-Skripte. Die
Transkripte liegen weiter auf Kaisers Rechner und im privaten Backup.

**Am Code nichts geändert.** 444 Tests grün.

---

## 26.09.2026 (2) — Gesamtprüfung aller Messungen gegen Furkans Videos

**Auftrag Kaiser:** alle Tests nochmals eingehend prüfen, ob die vorherige KI das Ganze
richtig verstanden und gebaut hat; Grundlage Transkript und Videos.

**Ergebnis:** `docs\PRUEFUNG-2026-09-26-GESAMT.md`. Kurz:

- Grundgerüst richtig (Fib-Levels, Dreipunkt-Extension, Tranchen, dynamische Zonen, keine
  Zukunftskenntnis im Backtest). Standbild 02.08. bestätigt die zwei Fib-Raster.
- **A1** Lage-Abruf: Futures-CVD kommt in BTC, steht als $ da (Faktor Kurs zu klein).
- **A2** `classify_pattern`: `spot <= fut / 3` vergleicht Anteile an einer willkürlich
  begonnenen Summe. Gleiche Lage ergibt je nach Startwert GESUNDER_TREND oder
  DERIVATE_PUMP; live wird anders summiert als im Backtest. Muster 2 wirkt live (Kaufsperre,
  5 von 10 Restverkäufen, 30 Warnungen im Lauf vom 23.09.).
- **A3** OI in $ = Kontrakte × Kurs: bei −5 % Kurs ohne eine geschlossene Position erkennt
  die Engine Kapitulation, bei +3,5 % ohne neuen Kontrakt Derivate-Pump.
- **A4** `test_mehr_historie_aendert_die_signale_nicht` erreicht den Muster-2-Zweig nie.
- **Lesefehler:** `be_im_plus` ist nicht Furkans Regel (Vorbedingung „Gewinne schon
  realisiert“ fehlt); Furkans Regel entspricht `trail_stop`.
- **Messbasis:** 16 von 25 ausgeschalteten Schaltern/Datenvarianten nie mit genau einem
  Unterschied gegen die heutige Live-Zeile gemessen. Vorneweg `bein_richtung: bias`.

**Am Code wurde nichts geändert.** 444 Tests grün. Nachstell-Skripte stehen im Anhang des
Berichts. Börsendaten waren aus der Arbeitsumgebung gesperrt: bewiesen ist der
Mechanismus, nicht die Häufigkeit im echten Fenster.

**Nächster Schritt, offen:** Kaiser entscheidet über Teil E des Berichts (Reihenfolge nach
Nutzwert, Entscheidungsregel vorab festgelegt).

---

## 26.09.2026 — Wissens-Layer aufgefrischt, Übergabe vorbereitet

**Fertig:** Alle Dateien des Wissens-Layers auf den Stand nach E41 gebracht. Neu
hinzugekommen:

- `00_STAND.md` — Kurzstand, wird künftig nach jeder Arbeit fortgeschrieben.
- `04_konventionen/BEKANNTE-PROBLEME.md` — Umgebungs- und Werkzeugfallen, getrennt von
  den inhaltlichen Befunden.
- diese Datei (`02_status/UEBERGABE.md`).
- `STARTPROMPT.md` und `PRUEFPROMPT.md` in der Repo-Wurzel.

Der Übergabeprompt stand vorher **doppelt** (in `ETAPPENPLAN.md` und in
`START-HIER.md`) und war in beiden Fassungen veraltet (174 Tests, letzte Etappe E30).
Maßgeblich ist jetzt allein `STARTPROMPT.md`; `START-HIER.md` verweist nur dorthin.

**Am Code wurde nichts geändert.** 444 Tests grün.

**Nächster Schritt, offen:** E41.6 oder E42 (siehe unten) — Kaisers Entscheidung.

---

## 23.09.2026 — Ausschalt-Regel für E41 hat angeschlagen, Kaiser hat überstimmt

**Messung** (Backtest 23.09.2026, 18:40 UTC, Fenster 15.01.–23.09.2026):

| Variante | Rendite | Rückgang | H1 | H2 | Stops |
|---|---:|---:|---:|---:|---:|
| Live: Rückeroberung 1 Kerze | +25,2 % | **−10,9 %** | +20,0 % | +4,3 % | 9 |
| Alter Stop (bis 21.09.) | +22,6 % | −9,4 % | +17,8 % | +4,1 % | 10 |
| B3 · 3 statt 1 Kerze | +26,8 % | −10,4 % | +21,4 % | +4,5 % | 9 |

Bedingung 2 der vorab festgelegten Ausschalt-Regel ist verletzt (Rückgang 1,5 statt
höchstens 1,0 Punkte tiefer). Der Bericht meldet **AUSSCHALTEN**.

**Kaisers Entscheidung:** anlassen, beim nächsten Backtest neu prüfen. Begründung,
Gegenargumente und die Kosten stehen in `docs\PLAN-E41-STOP.md`, Abschnitt „Nachmessung
23.09.2026". Im Bericht steht die Überstimmung jetzt **neben** der Ausschalt-Meldung —
die Regel wurde nicht abgeschwächt (zwei Sabotagen sichern das ab).

**Kaisers Frage „warum nicht B3 mit 3 Kerzen?" ist beantwortet** (fünf Gründe im Plan);
der stärkste: B3 hat **gleich viele Stops** wie B1 (9 gegen 9, alter Stop 10) — es ist
derselbe eine ausgelassene Stop, der Unterschied entsteht nur aus späteren Stop-Preisen.
Für einen späteren Wechsel liegt eine **vorab festgelegte Regel** im Plan (zwei Läufe,
vier Wochen Abstand, in beiden Hälften ≥ 1 Punkt besser, Rückgang nicht tiefer).

**Neue Projektlehre:** Der Fenster-Rückgang ist **zwischen zwei Varianten**
pfadabhängig — B3 wartet länger und zeigt trotzdem einen flacheren Rückgang. Daraus der
Vorschlag **E41.6**: ein Risikomaß je Position (tiefster Punkt zwischen dem alten Stop
und dem Live-Ausstieg), Schwelle vorab festgelegt. Nicht gebaut.

**Stand Code:** 444 Tests, `sabotage_e41.py` 58 Sabotagen, alle gefangen.

---

## 21.09.2026 — E41 live, STH-Kostenbasis als Anzeige

**Live geschaltet** (Kaisers Entscheidung): `stop_rueckeroberung: 1`. Der erste
4h-Schluss unter der Invalidierung stoppt nicht mehr; die Engine wartet eine Kerze auf
die Rückeroberung. Danach gilt die Marke als **geprüft** — der nächste Schluss darunter
stoppt sofort. Notbremse: mehr als 5 % unter der Marke stoppt ohne Warten. Während des
Wartens und in der Kerze der Rückeroberung wird nicht nachgekauft.

**Telegram** meldet „⏳ STOP WARTET" und „✅ MARKE ZURÜCKEROBERT"; die Plan-Nachricht
nennt die Regel in der Stop-Zeile und warnt, wenn die Engine gerade wartet.

**Drei Dinge, die erst beim Bauen auffielen** (alle behoben, im Plan dokumentiert):
die Merker mussten in `state.json` (sonst käme der Stop live nie), der 0,786-Nachkauf
hätte nach einer Rückeroberung zu einem nie existierenden Preis gebucht, und die
Nachkaufsperre muss auch die Kerze der Rückeroberung umfassen.

**Ebenfalls fertig:** die **STH-Kostenbasis** steht als Zeile im Lage-Abruf (Wert,
Abstand in Prozent, Datum, „Nur Anzeige, keine Regel"). Quelle bitview.space, Ersatz
bitcoin-data.com. Als *Regel* ist sie nicht prüfbar: 84 % der Kerzen lagen darunter, nur
7 Wechsel im Fenster — E40.2/E40.3 wurden deshalb nicht gebaut.

**Ebenfalls fertig:** E38 (Muster 5) ist entschieden — das Signal ist echt, die Engine
kann es nicht benutzen, weil sie nur an Fib-Zonen entscheidet. Alle Schalter aus, nur
der Text in den Nachrichten wurde ersetzt und die Ampel zählt Muster 5 neutral.

**Gitter umgebaut:** Panel-Zeile ist jetzt „LIVE-heute +Rückeroberung vor dem Stop
(1 Kerze)". Neu: „LIVE bis 21.09.2026 (Stop ohne Rückeroberung)" als Ausschalt-Probe und
„Rückeroberung 3 statt 1 Kerze" als Robustheitsprüfung. A (Puffer 0,5 %) und C (Docht)
sind nach der Messung aus dem Gitter genommen.

---

## Was als Nächstes offen liegt

Vollständig und nach Nutzwert sortiert: `02_status/OFFENE-PUNKTE.md`. Die beiden
naheliegenden Vorhaben:

1. **E41.6 — pfadunabhängiges Risikomaß.** Für jeden Stop des alten Stops den tiefsten
   Punkt messen, den die Position live danach noch sah. Damit ließe sich die
   Ausschalt-Bedingung als „zusätzlicher Buchverlust je Position" fassen statt als
   Fenster-Rückgang. Schwelle **vor** der Messung festlegen. Grundlage:
   `docs\PLAN-E41-STOP.md`, Abschnitt E41.6.
2. **E42 — Ausbruch mit Rücktest** (Kaisers zweite Regel, wörtlich im Plan E41
   zitiert): Die Engine verkauft heute kurz unter dem letzten Hoch (`high_exit: on`).
   Bricht der Kurs durch und hält beim Rücktest (Schluss nicht mehr darunter, höchstens
   der Docht), sind weitere Gewinne zu erwarten — zurückkaufen oder den Rest halten?
   Eigene Etappe, weil es in E41 einen zweiten Unterschied pro Gitterzeile erzeugt
   hätte. Noch kein Bauplan.

**Vier Schalter hängen seit Monaten unentschieden** (`confirm_t1`, `cooldown_h`,
`be_im_plus`, `release_stale_rest`) — sie wurden nie mit **genau einem** Unterschied
gegen die heutige Basis gemessen. Zwei saubere Gitterzeilen würden das klären.


## 07.10.2026: isolierte lokale UM2-Engineintegration (keine Aktivierung)

Nur Branch `codex/um2-engine-integration` ab P3 `a7cf45d` ist korrigiert.
Native Liquidations-/M5-Gates: 20/20 eingefrorene Vollfensterläufe exakt zu den
gespeicherten Tapes. Danach 20 gleiche Läufe mit Ablehnung eines Kaufs ohne
darstellbaren BTC-Zuwachs; insgesamt 40 historische Strategieläufe. N-UM2-01
verbraucht dort keine Nachkaufstufe mehr. C05/S006/V000 unverändert, C02 S0/S2/S3
je ein Kleinstfill weniger; Signalfolgen identisch, größte Endwertabweichung
3,64e-12 USD. Isoliert 90/125 alte diagnostische Kleinstoperationen abgelehnt;
35 bleiben darstellbar. Keine allgemeine Mindestorder oder neue Gesamtrangfolge.

C05 und S006 liegen vollständig und inaktiv unter
`docs/um2-engine-integration/candidates/`. Lokale Tests: 834/0 Testfunktionen,
34 neue einzelne Gegenfälle mit gefangener Sabotage. Details und Grenzen:
`docs/um2-engine-integration/ERGEBNIS.md`; additive Nachweise im übergeordneten
Projekt `audit-backups/um2-engine-integration-20261007/`. Wissenspräfix- und
Diagnostiktests wurden nach den historischen Läufen verstärkt; Strategie-/
Ausführungsdateien blieben dabei identisch. Es erfolgte keine weitere Historienrechnung.

Hauptchat-Abnahme, sichere aktuelle Workflowprüfung/separat autorisierter Push
und Online-CI, echte Fills, P3/D3 und P4 bleiben offen. Keine Umstellung von
Site, Runtime, Store oder bestehenden Positionen. Hauptplan nicht endgültig
abgenommen. Vier Aprillücken, unbekannter Warmup, modellierte Verfügbarkeit,
mindestens 94 frühere Suchen und fehlende Zukunftsprobe bleiben Grenzen.

## UM2-Budgetnacharbeit 08.10.2026
Branch codex/um2-engine-integration. Geldvertrag: docs/um2-engine-integration/GELDVERTRAG-v2.md. Additive Belege: audit-backups/um2-budget-korrektur-20261008 im Projektstamm. Synthetische Pruefung bestanden; 0/20 neue Vollfensterstarts vor dem Codepin. Danach ausschliesslich C05/S006/V000/C02 je S0-S4. Kein Push, keine Online-CI, keine Nachrichten oder Aktivierung.


UM2-Budgetabschluss 08.10.2026: 20/20 neue Vollfensterstarts, insgesamt 60 inklusive früherer 40; alle Signale exakt unverändert, maximale Endwert-/Equitydifferenz 2.1827872842550278e-11 USD. 842 Tests und gezielte Sabotagen bestanden. Bericht docs/um2-engine-integration/BUDGET-v2-ERGEBNIS.md. Lokale Sicherung/Restore wird separat belegt; Hauptchat-Abnahme, Online-CI und Live-Gates offen.
