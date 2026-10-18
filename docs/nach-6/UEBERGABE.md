# Abschluss und getrennte Folgearbeit

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

Reproduktion: Python 3.12, NumPy 2.3.5. Zuerst engine/run_tests.py, dann tools/test_historical_stats.py und tools/verify_n6_probes.py.

`tools/historical_analysis.py --package R0 --inputs <Sicherung>/eingefrorene-inputs --out <Ausgabe>/R0`

Analog `--package R1 --out <Ausgabe>/R1`. Der Plan prüft sämtliche fixierten Code-/Datenhashes; niemals automatisch neu registrieren oder Daten erneut abrufen. `tools/verify_n6_backup.py` erstellt/verifiziert den vollständigen Abschluss einschließlich 60 identischer Neuläufe und sechs alter Prozess-Checkpoints.
