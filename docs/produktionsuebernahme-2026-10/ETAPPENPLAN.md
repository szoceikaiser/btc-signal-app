# Kontrollierte Produktionsübernahme der Auditkorrekturen

Auftrag vom 03.10.2026: vorhandene Korrekturen kontrolliert betriebsfähig machen;
Renditeergebnisse der Prüfungs-/Entwicklungsetappen einschließlich beider Hälften
verständlich aufstellen. Auf Nutzerwunsch erfolgt die Übernahme in getrennten Chats.
Dies ist ein Umsetzungsauftrag nach A8, keine Wiederholung des Gesamtaudits.

## Verbindliche Ausgangspunkte

- Aktuelle Produktionsbasis bei P1: `ca8ad2fb730174ca1887791d425ae01aa6a715e6`.
- Abgenommene Korrekturen: `881e36a6271a6e49400d47da59342755e33cf402`.
- Neuer Arbeitsbaum: `C:/Users/oeztu/BTC-Trading/produktion-work`.
- Neuer Zweig: `codex/produktion-audit-uebernahme`.
- A8 und die bisherigen Arbeitsbäume/Sicherungen bleiben unverändert.
- Der Übernahmezweig integriert beide Historien. Die aktuellen Laufzeitdateien
  von main werden erhalten, nicht mit alten Auditständen ersetzt.
- Ein Branch-Commit oder grüne CI ist keine Live-Freigabe. Kein main-Merge,
  Deployment, Telegram, Broker, Secretabruf, Live-Umschalten, laufende Sammlung
  oder alter Backtest-Dispatch ohne einen dafür ausdrücklich freigegebenen Auftrag.
- Keine parallelen Agenten. Keine neue Parameteroptimierung.

## Etappen mit überprüfbarem Ende

| Etappe | Arbeit / Abnahme | Modell-ID / Denkaufwand |
|---|---|---|
| P1 – Übernahmebasis und Aufstellung | Aktuelles main und A8 isoliert integrieren; alle 22 IDs ihren Betriebsfolgen zuordnen; Laufzeitdaten, Konfigurationsänderung und Altzustandslücken nachweisen; branchgebundene Offline-CI; reproduzierbare Renditeübersicht aus vorhandenen Belegen. Eigener Commit, CI zur exakten SHA und additive Sicherung. | `gpt-6-astra` / `high` |
| P2a – Betriebsweg und Migrationsvertrag | Vorhandene/gewählte Betriebsumgebung mit dem Nutzer klären; einen konkreten umsetzbaren Betriebsweg, Datenträger-/Runnervertrag, Schnittgrenze, Umgang mit alten Quittungs-/Positionslücken und Abnahmekriterien festlegen. Keine erneute Strategieprüfung, keine kostenpflichtige Bereitstellung, keine echte Migration. | `gpt-6-astra` / `high` |
| P2b – Umsetzung nach festem Vertrag | Dauerhaften Store, Runneranbindung, Zustandsmigration, Sperren, Überwachung, Sicherung und beleggestützte Behandlung unklarer Zustellung implementieren. Trockene Migration des eingefrorenen Altzustands und Abbruch-/Neustart-/Parallelitätsfälle bestehen. Keine echten Nachrichten, keine Live-Migration. | `gpt-6-sol` / `high` |
| P3 – Freigabekandidat | Dann aktuelles main erneut lesen und sicher integrieren; Migration mit frischem Snapshot wiederholen; Signal-/Plan-/Chart-/Versandverhalten anhand eingefrorener Eingaben prüfen; unbekannte Positionsdaten ausdrücklich erhalten. Sichere CI, prüfbarer PR, genaue Aktivierungs- und Rückfallanleitung. Fehlende externe Betriebsnachweise klar benennen. | `gpt-6-sol` / `high` |
| P4 – Kontrollierte Aktivierung | Erst nach ausdrücklicher Freigabe des konkreten P3-Ergebnisses: laufende Auslöser geordnet anhalten, frischen konsistenten Zustand sichern, migrieren, freigegebenen Stand übernehmen und beobachtet starten. Kontrollierter Sendetest nur mit ausdrücklicher Versandfreigabe. Rückfall darf keinen alten Versandzustand wiederholen. | `gpt-6-sol` / `medium` |

Die Modellempfehlungen gelten für den jeweiligen neuen Chat. Ein Text stellt
Modell oder Aufwand nicht technisch um. Kein kostenpflichtiger Dienst wird
ohne Nutzerentscheidung eingerichtet. P2 darf keine erfundene Host-Verfügbarkeit
oder funktionierende Datenträgeranbindung behaupten.

Budgetentscheidung: Astra nur für die noch offene, folgenreiche Betriebs- und
Migrationsentscheidung; danach Sol mit festem Vertrag. P4/medium gilt nur bei
unverändertem, vollständig abgenommenem Ablauf; bei einer neuen Migration oder
einem ungeklärten Zwischenzustand nicht improvisieren. Die Empfehlungen sind
aufgabenspezifisch, kein Verbrauchsversprechen für den Tarif des Nutzers.
Keine pauschalen `max`/`ultra`, keine parallelen Agenten, keine Wiederholung der
1.250 historischen Rechnungen. Pro Folgechat nur Übergabe, Vertrag und betroffene
Dateien lesen. Offizielle Modellbeschreibungen:
[Sol](https://developers.openai.com/api/docs/models/gpt-6-sol),
[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra).

## Bewusste Entscheidungen und offene Voraussetzungen

1. A8 enthält eine tatsächliche Konfigurationskorrektur `muster_cvd: alt → usd`.
   Sie beseitigt die Abhängigkeit vom willkürlichen Summenstart. Dies ist eine
   fachliche Messkorrektur, keine auf Rendite ausgewählte neue Einstellung.
   Andere Parameterwerte bleiben gegenüber der P1-main-Basis gleich. Vor
   Aktivierung sind Signalwirkungen und die eingebettete alte state-Konfiguration
   sauber zu behandeln; state.json darf nicht einfach zurückgesetzt werden.
2. Aktuelles main hat kein neues Versandjournal. Fehlende alte Telegramquittungen
   werden weder als bestätigt noch als noch zu senden erfunden. Die Übernahme
   braucht eine belegte Schnittgrenze und darf historische Signale nicht neu senden.
3. Alte Positionen sind Signalreferenzen, keine bekannten Börsenbestände. Lose,
   tatsächliche Einstandskosten und das frühere Maximum des Stops sind nicht
   nachträglich aus Modellbuchungen zu erfinden. Fehlende Felder werden markiert.
4. Ein dauerhafter geeigneter Store samt Host ist noch nicht bereitgestellt.
   A4 verweigert realen Versand ohne ihn. Ein gewöhnlicher GitHub-Cache, ein
   nachträglicher Artefaktupload oder ein Git-Commit nach dem Senden lösen die
   Absturzlücke nicht. Den geprüften Schutz nicht mit einem Fallback umgehen.
   P2a darf einen geeigneten bereits vorhandenen dauerhaften Dienst als Alternative
   prüfen, auch einen ausdrücklich entworfenen GitHub-Persistenzadapter. Dieser
   wäre eine neue Umsetzung mit eigenem Vertrag/Nachweis, kein schon abgenommener
   A4-Betrieb. Vorhandene Infrastruktur bevorzugen; keinen Serverkauf voraussetzen.
5. E42 und Shorts bleiben aus; keine Renditeauswahl aus den historischen Gittern.
   V035 bleibt ohne freigegebene historische Gesamtrendite.
6. Alle Renditen sind Modell-/Diagnoseergebnisse; fehlende frühere Halbzeitläufe
   werden als fehlend gezeigt. Neuere Halbzeiten werden keiner alten Etappe
   zugeschrieben. Getrennt gestartete Hälften dürfen nicht zu einer Gesamtrendite
   addiert oder verkettet werden.

## Abschluss jedes Chats

P2a-Vertrag: `P2A-BETRIEBSVERTRAG.md`, `P2A-MIGRATIONSVERTRAG.md` und separat
`P2A-GITHUB-ADAPTER.md`; begrenzte Umsetzung in `P2B-IMPLEMENTIERUNGSPLAN.md`.
Hostentscheidung D1, konkrete spätere Migrationsfreigabe D2 und Betriebszuständigkeit
D3 bleiben ausdrücklich zu belegen. Ohne diese Entscheidungen kein Live-Go.
P2a ändert weder Engine noch Laufzeitdaten/Renditen. Seine Offline-CI vergleicht die
vorhandene Renditeaufstellung nur noch mit P1, ohne erneute Berechnung.

Jede Etappe erhält einen belegten Status, Commit, passende sichere CI und eine
additive Sicherung mit Hashmanifest und geprüfter Wiederherstellung. Vor Push
alle Workflowtrigger einschließlich `workflow_run` und die aktuellen
Default-Workflows lesen. Keine alten Auditnachweise überschreiben.

Jeden Start- oder Fortsetzungsprompt vollständig und kopierfertig direkt in der
abschließenden Chatantwort in einem Codeblock ausgeben UND zusätzlich als
Markdown-Datei speichern. Ein Link oder eine Zusammenfassung genügt nicht.
Jeder Prompt nennt die konkrete Modell-ID und den Denkaufwand und gibt diese
gesamte Ausgabe- und Speicherpflicht ausdrücklich an alle weiteren Chats weiter.
Nach endgültigem Abschluss dieses Produktionsauftrags ist kein Folgeprompt nötig.
