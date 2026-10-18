# P1 – integrierte Übernahmebasis, noch kein betriebsfertiger Versand

03.10.2026. Produktionsbasis `ca8ad2fb730174ca1887791d425ae01aa6a715e6`,
Auditbasis `881e36a6271a6e49400d47da59342755e33cf402`. Neuer Zweig
`codex/produktion-audit-uebernahme` im Arbeitsbaum `produktion-work`.

## Ergebnis und tatsächliche Grenze

Die beiden Historien sind im neuen Zweig konfliktfrei integriert. Sämtliche
Engine-Dateien, Chartänderungen und die Auditkonfiguration entsprechen exakt
A8. Die sieben von main übernommenen Datendateien sind unverändert; dazu gehören
state, signals, OI-Verlauf, Archiv und bisherige Backtestprojektionen. Diese
Projektionen werden damit nicht als neu validierte Live-Renditen ausgegeben.

Der Zweig ist eine überprüfbare Integrationsbasis, **noch nicht produktionsreif**.
P2 muss den fehlenden Host-/Storebetrieb, die Migrationsschnittgrenze und
ungeklärte Zustellungs-/Positionshistorie lösen. P1 hat keinen laufenden Dienst
eingerichtet oder umgestellt. main und sämtliche früheren Arbeitsbäume bleiben
unverändert. Die spätere Live-Freigabe gehört ausschließlich zu P4.

## Konkrete Integrationsnachweise

| Gegenstand | Nachweis / Folge |
|---|---|
| Produktionsdaten | `P1-INTEGRATION.json` listet die sieben unveränderten Git-Blob-SHA256. Kein Rückspielen der älteren A8-state/signals/Archiv-Dateien. |
| Laufende Position | P1-main enthält `T1`, Stand `2026-10-03T15:37:47Z`. Trockener Parser-/Serializer-Rundlauf erhält Richtung, Zeit, Einstiegssignal, Anteil, Leiterstände und Stop-Wartestatus. Es wird kein echter Börsenbestand behauptet. |
| Fehlende Altposition-Felder | `legacy_unversioned`, `live_fills_unknown`, `widerstand_exits_missing_default_0`, `prior_stop_maximum_unknown` bleiben ausdrücklich benannt. Keine erfundenen Lose oder früheren Stopmaxima. |
| Versand | Kein `_delivery` im alten state; keine watch.json in dieser main-Sicherung. Ein unmittelbarer Import in den neuen dauerhaften Store wird erwartungsgemäß abgewiesen. Fehlende Datei bedeutet keinen Nachweis, dass nie gewarnt/gesendet wurde. |
| Parameter | Einzige geänderte operative Einstellung ist `muster_cvd: alt → usd`, außerdem ihr Hinweistext. Technische Korrektur F06; keine Parameteroptimierung. E42/Short bleiben aus. Eingebettete Alt-Konfiguration im state bleibt als bisherige Projektion erhalten und muss beim späteren kontrollierten Weiterlauf berücksichtigt werden. |
| Workflows | Signal, Watch, Lage, alter Backtest und Archiv im Übernahmezweig auf main begrenzt. Pages verlangt auch beim vorgeschalteten Workflow main. Das neue `Produktionsuebernahme Offline` läuft ausschließlich auf dem Übernahmezweig mit Leserechten, ohne Secrets und ohne Marktabrufe. Bestehende sichere Tests laufen weiterhin. Diese Schutzänderungen sind noch nicht auf main aktiv. |
| Renditen | Generator liest vorhandene Git-/Dateibelege und prüft ihre Zuordnung; keine neue historische Rechnung. Ursprüngliche Level-Diagnose, korrigierte Level-Diagnose und kausale Modelle bleiben getrennt. Fehlende Halbzeitläufe bleiben leer. |

Prüfprogramme: `tools/produktion_p1.py` und `tools/produktion_renditen.py --verify`.
Der P1-Codegleichheitscheck ist bewusst auf den unveränderten A8-Import begrenzt.
Wenn P2 neue produktive Dateien ändert, muss die CI den eingefrorenen P1-Beleg
weiter erhalten und neue Änderungen gezielt prüfen; nicht unbemerkt die
P1-Aussage „Engine unverändert“ für einen späteren Codebaum übernehmen.

## Übernahmezuordnung aller 22 Audit-IDs

Die A8-Endstatus werden nicht neu bewertet. Diese Tabelle beschreibt, was ihre
Korrekturen bei der Produktionsübernahme bedeuten. „Übernommen“ heißt hier immer
im vorbereiteten Zweig, nicht live aktiviert.

| ID | Zugeordneter Bereich | Übernahme / noch erforderlicher Betriebsschritt |
|---|---|---|
| F01 | Offline-Risikoauswertung | Kausale Equity-/Drawdownrechnung erhalten; keine Intrabar-Ausführungsgarantie. |
| F02 | Offline-Derivate | Modellbuch erhalten; keine Aktivierung von Shorts, keine V035-Gesamtrendite. |
| F03 | Live-Stoplogik | Monotone Grenze übernommen; Migration darf unbekanntes früheres Maximum nicht erfinden. |
| F04 | Bestand / Auswertung | Simulierte Lose und Einstand korrekt; echte manuelle Fills weiterhin unbekannt. |
| F05 | Live-Neustart | Widerstandszähler wird künftig gespeichert; alter fehlender Zähler explizit markiert, Mechanismus bleibt aus. |
| F06 | Flow-Messung / Konfiguration | Korrekte USD-Fensterdeltas und Wechsel alt→usd; Auswirkung im Weiterlauf gezielt prüfen. |
| F07 | Flow-Verfügbarkeit | Verfügbarkeit, Alter und Herkunft künftig beachten; keine rückwirkend erfundenen API-Veröffentlichungen. |
| F08 | Tagesdaten | Nur vollständige geschlossene UTC-Tage; ungültige Zusatzpunkte werden ausgeschlossen. |
| F09 | Offline-Kapitalbuch | Rundungsrest und Kapitalzyklen korrekt; unbekannten echten Restbestand nicht zurücksetzen. |
| F10 | Live-Plan und Stop | Gemeinsame Stopgrenze übernommen; Planprojektion nach Migration gegen Signalzustand prüfen. |
| F11 | Live-Konfiguration | Strikte Booleans; bestehende gültige Einstellung erhalten. |
| F12 | Offline-Ausführung | Kausale Modellfills; keine Behauptung, dass deine manuellen Orders so ausgeführt wurden. |
| F13 | Live-Versand / Betrieb | Technischer Storepfad vorhanden, reale Bereitstellung/Migration fehlen; P2a/P2b zwingend. Kein ungesicherter Altversand-Fallback. |
| F14 | Datenadapter | Vollständige endliche Aggregatwerte und gültige Gewichte; Ausfallverhalten prüfen. |
| F15 | Datenadapter / Einheiten | USD-Normalisierung vor Auswahl; unbekannte historische Körbe bleiben unbekannt. |
| F16 | Indikatorberechnung | ATR-Vorlaufkorrektur übernommen; keine Renditezusage. |
| F17 | Chart / Anzeige | Quellengetrennte Signalidentitäten übernommen; alte Signale bei Migration erhalten. |
| D01 | Kerzenschluss | Nur abgeschlossene Eingaben für abgeschlossene 4h-Entscheidungen; Watch bleibt gesonderter Hinweisweg. |
| D02 | Datenqualität | Fehlend/alt/echte Null getrennt; fehlendes Funding bestätigt Long nicht. |
| M01 | Historische Entscheidungen | Chronik/wechselnde Basen erhalten; kein produktiver Schalter. |
| M02 | Aussagegrenzen | Mehrfachsuche und wiederverwendete Hälften kenntlich; keine künstliche Verbesserung. |
| T01 | Tests | Erreichte Gegenfälle und Mutationsnachweise erhalten; gezielte neue Migrationstests in P2b. |

## Etappenabschluss

Die lokale vollständige Regression bestand mit **796 Tests, 0 Fehlern**.
P1-Integrationsprüfung und Renditeaufbereitung bestanden; letztere umfasst
1.110 Modell-/Szenariozeilen, 54 Etappenzeilen und 1.625 Quelldateien.
Die endgültige Commit-SHA, genaue CI-Läufe,
Sicherungshashes und der frische Restore stehen nach ihrem tatsächlichen
Abschluss in der additiven externen `UEBERGABE.md/json`. Keine vorweggenommene
Behauptung einer grünen CI oder vollständig bereitgestellten Betriebsumgebung.

Nächster neuer Chat: **P2a**, `gpt-6-astra`, Denkaufwand `high`. Danach nach festem
Vertrag **P2b mit `gpt-6-sol` / `high`**. Der Etappenplan begrenzt unnötige
Wiederholungen. Die noch offene Hostentscheidung ist keine Zustimmung zu einem
kostenpflichtigen Angebot und wird nicht durch Zeitablauf ersetzt.
