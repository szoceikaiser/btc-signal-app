# Vollständiges Befundregister – Auditnacharbeit ab 01.10.2026

Stand: A1, Basis `dc5ddd6aaa8cde6a44c51892910c045ebd6f387a`. Dieses Register ergänzt das Originalaudit vom 27.09.2026; es ersetzt keine Originaldatei und kennzeichnet keinen Befund pauschal als erledigt. Die Fundstellen beziehen sich auf `audit-work/docs/audit-2026-09-27/BERICHT.md` im Originalzweig `codex/audit-2026-09-27` (`ccf2b01c0578346f325261e72445b7375a9ac706`).

| ID | Originalfundstelle und Befund | Vorhandene Erledigungsbelege | A1-Status und Reichweite | Folgeetappe | Verbleibende Grenze |
|---|---|---|---|---|---|
| F01 | P1, „Die Drawdown-Rechnung…“ (ca. Z. 79); Bestand innerhalb der Kerze falsch | Offline-V1-Korrektur und Prüfung laut Erhaltregister; Basis/E42-Abnahme nach dc5ddd6 | Erhalten, durch A1 nicht geändert | A6 Regression, A7 Ergebnisfolgen, A8 Abschluss | Intrabar-Reihenfolge ohne feinere Daten begrenzt; kein Live-Go |
| F02 | P2-Tabelle (ca. Z. 170); Short-Margin/Kapital/Funding | Keine; separat offen im Erhaltregister | Offen | A5 | Derivatefälle, Kapitalbindung und Funding nicht nachgewiesen |
| F03 | P1, „Struktur-Stop kann wieder sinken“ (ca. Z. 112) | Etappe 4 monotone Grenze geprüft | Erhalten, durch A1 nicht geändert | A6/A8 | Keine pauschale Aussage außerhalb geprüften Vertrags |
| F04 | P1, „Engine-Einstand…“ (ca. Z. 125); Einstand nach Kapitalprozenten gemittelt | Etappe 4 Lose/Kosten geprüft | Erhalten, durch A1 nicht geändert | A6/A7/A8 | Manueller Live-Einstand unbekannt |
| F05 | P3-Tabelle (ca. Z. 177); Widerstandszähler geht im State verloren | Etappe 4 Zustandsfortsetzung geprüft | Erhalten, durch A1 nicht geändert | A6/A8 | Widerstandsverkauf derzeit aus; Aktivierung nicht belegt |
| F06 | P2-Tabelle (ca. Z. 167); CVD-Muster abhängig vom Summenstart | Keine; offen im Erhaltregister | Offen | A2 | Offset-Invarianz und historische Ableitungen ausstehend |
| F07 | P2-Tabelle (ca. Z. 168); OI-Erstwert rückwärts gefüllt | Keine; unverändertes R0 ist keine Reparatur | Offen | A2 | Kausalität und Alter/Abdeckung ausstehend |
| F08 | P2-Tabelle (ca. Z. 171); Tagesresampling nutzt unvollständigen Tag | Keine; offen | Offen | A3 | UTC-Abschluss und Lückensemantik ausstehend |
| F09 | P1, „Rest verhindert neuen Kapitalzyklus“ (ca. Z. 93) | Etappe 1 und Folgeprüfungen; zusätzlicher i+2-Fall gesondert | Erhalten, durch A1 nicht geändert | A6 Regression, A7 Ergebnisfolgen, A8 | A1 ändert keine Buchführung; alter Gegenfall/Artefakt bleibt erhalten |
| F10 | P1, „Engine-Einstand…“ (ca. Z. 125); Planstop weicht ab | Etappe 4 gemeinsamer Stop-Resolver geprüft | Erhalten, durch A1 nicht geändert | A6/A8 | Keine neue Reichweite durch A1 |
| F11 | P3-Tabelle (ca. Z. 181); `eval_params` macht Text `false` wahr | Vorher am Basiscommit reproduziert: `True`; A1 gezielt korrigiert und regressionsgeprüft | **Korrigiert und gezielt geprüft:** nur echte JSON-Booleans zulässig; Falschtyp löst TypeError aus. Bestehende `config.json` unverändert gültig. | A6 Regression, A8 Abschluss | Andere Konfigurationsgrenzen nicht Gegenstand dieser Korrektur; keine Live-Aktivierung |
| F12 | P1, „Signal am Kerzenschluss…“ (ca. Z. 61) | Offline-V1/i+2-Pfad geprüft; V2 separat begrenzt | Erhalten, durch A1 nicht geändert | A5 V2-Abgrenzung, A7 Semantik, A8 | Vorab liegende bedingte Orders bleiben eigener Vertrag |
| F13 | P1, „Fehlgeschlagene Telegram-Nachrichten…“ (ca. Z. 138) | Etappe 5a lokaler Hauptlauf/Outbox; Teilfälle | Erhalten, durch A1 nicht geändert | A4 Restfälle, A6/A8 | Vollständiger Runnerverlust und ausgeschlossene Einmalbefehle offen |
| F14 | P3-Tabelle (ca. Z. 182); fehlender Börsenmarkt dennoch als vollständige Summe | Keine; Aggregation außerhalb Einzelmarktpaket offen | Offen | A3 | Vollständigkeit des gesamten angeforderten Korbs offen |
| F15 | P3-Tabelle (ca. Z. 183); Volumen verschiedener Einheiten verglichen | Keine; offen | Offen | A3 | Einheiten-/Denominierungsnachweis ausstehend |
| F16 | P3-Tabelle (ca. Z. 184); ATR bei kurzem Vorlauf falsch ausgerichtet | Vorher am Basiscommit reproduziert: `2.0`, unabhängig errechnete TRs `[21,31]`, Mittel `26`; A1 korrigiert und zielgerichtet geprüft | **Korrigiert und gezielt geprüft:** letzte bis Periode verfügbare True Ranges; leer/eine Kerze ergeben 0, voller Vorlauf geprüft | A6 Regression, A8 Abschluss | A1 prüft den Grenzvertrag, nicht Strategierenditen oder Live-Auswirkung |
| F17 | P1, „Chart lässt bei Kollision…“ (ca. Z. 152) | Etappe 5b Herkunft/Ereignisidentität geprüft | Erhalten, durch A1 nicht geändert | A6/A8 | Keine neue Chart-Abnahme durch A1 |
| D01 | P2-Tabelle (ca. Z. 166); laufende Kerze im historischen Input | Etappe 2 geschlossene Reihen/Cutoff geprüft; nach-6 erhält D01 | Erhalten, durch A1 nicht geändert | A3 Regression, A8 | Historischer Beschaffungszeitpunkt nicht bewiesen |
| D02 | P2-Tabelle (ca. Z. 169); fehlend und neutral beide als Null | Keine; offen | Offen | A2 | Herkunft, fehlend/neutral/veraltet und Bestätigungswirkung ausstehend |
| M01 | P2-Tabelle (ca. Z. 172); alte LIVE-Zeilen gegen verschiedene Basis | Historische Einordnung erhalten; festes aktuelles Paar dokumentiert | Erhalten, durch A1 nicht geändert | A7/A8 | Alte Entscheidungen nicht pauschal auf heutige Basis übertragbar |
| M02 | P2-Tabelle (ca. Z. 173); wiederverwendete Daten/Mehrfachauswahl | Auswahlgrenze im Nach-6-Prüfbericht ausdrücklich offengelegt | Erhalten, durch A1 nicht geändert | A7/A8 | Vollständige frühere Suchfamilie unbekannt; keine Auswahlkorrektur behauptet |
| T01 | P3-Tabelle (ca. Z. 185); veraltete Sabotagen und fehlende E41-Reihenfolgeprobe | Etappe 5a erreichte E41-Wartekerze mit Teilverkäufen | Erhalten, durch A1 nicht geändert | A6 | Keine pauschale Schließung der übrigen alten Vorlagenlücken |

Maschinenlesbare identische Datenstruktur: [`REGISTER.json`](REGISTER.json). A1 berührt nur F11/F16; alle anderen 20 Einträge behalten ihren belegten Status und ihre zugewiesene Folgeetappe.
