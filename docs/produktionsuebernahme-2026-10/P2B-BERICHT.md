# P2b – gemeinsamer Offline-Kern

Stand: 04.10.2026. Zweig `codex/produktion-audit-uebernahme`.
P2a-Basis `d6297f84578147ca09e408c6a83a86716d586d1d`.
**Keine Live-Freigabe, kein Umschalten der aktiven Produktionsworkflows.**

## Umgesetzt

- **M:** Lokaler Konverter mit explizitem Quellenmanifest, Byte-Hashes,
  identischem B/W-Cutover, vollständigem T1- und Historienerhalt, gepinnter
  `alt → usd`-Konfiguration, Unknown-Liste und gesperrtem v2-Snapshot. P1 ist
  ausschließlich Rehearsal; dessen synthetische Schnittgrenze ist kein frischer
  main-Snapshot. Fehlende letzte Läufe, gemischte Quelle, Historie nach B,
  fremdes Journal und unzulässige Konfiguration werden abgewiesen.
- **S:** v2-Kontrollhülle auf dem vorhandenen SQLite-Adapter. Eine gemeinsame
  Sperre und Store-ID für Signal, Watch und manuelle Pfade; Identität,
  Zielbindung, Bot-Identität und Config-Pin werden vor dem produktiven Fetch
  geprüft. `sending` wird bei Wiederanlauf dauerhaft `uncertain`; jede
  Unklarheit stoppt auch neue Operation-IDs und Auswertung. Der historische
  `resend-all`-Pfad ist gesperrt. P1-main ohne Journal bleibt direkt nicht
  provisionierbar. V1 bleibt nur für seine bisherigen Tests lesbar und kann v2
  nicht öffnen. Der Offline-Runner arbeitet auf einer temporären Kopie mit
  synthetischem, netzfreiem Transport.
- **Schnittgrenzen:** Initiale Plan-/Vorschau-Neuprojektion bei unverändertem B
  versendet nichts. Watch bis W und alte Flush-Auflösungen bis W bleiben
  unterdrückt. Importierte Signale werden auch bei mehr als 500 Einträgen beim
  ersten Weiterlauf nicht abgeschnitten. Historische Nachrichten bekommen
  weder Outbox-Eintrag noch erfundene Quittung.
- **O:** Maschinenlesbare Health-Prüfung, Watch-Heartbeat auch ohne Warnung,
  gesperrte SQLite-Backup-API-Sicherung und Restore in ein neues Ziel,
  zweistufige positive Klärung mit erwarteter Revision und unveränderlichem
  Prüfplan sowie expliziter öffentlicher Feld-Allowlist-Export. Backup auf
  derselben Platte ist kein zweites Sicherungsziel. Eine externe Quittung muss
  weiterhin durch einen Menschen eindeutig zugeordnet werden.
- **C:** Eigener P2-Nachweis und branchgebundene Offline-CI mit kompletter
  Engine-Regression. Die P1-Codegleichheitsprüfung wird nicht auf den
  geänderten HEAD übertragen. P1-Renditedateien bleiben unverändert.

## Geprüfte Gegenfälle und Grenzen

Die lokalen Tests benutzen P1-Blobs von
`ca8ad2fb730174ca1887791d425ae01aa6a715e6` und synthetische
Transport-/Belegdaten. Sie prüfen T1-Rundlauf, 600 zusätzliche historische
Einträge, fehlende Watchdatei, alte Grenzwarnung, harte Prozessabbrüche nach
Intent/sending/Annahme/Quittung, vollständigen Runnerverlust, globale
Unklarheitssperre, falsche Zielquittung, Config-Abweichung, stale
Klärungsrevision, Backup-Konkurrenz, gesperrten Restore und private Felder
im öffentlichen Export. Die vollständige lokale Engine-Suite nach der letzten
Codeänderung: **810 bestanden, 0 Fehler** (UTF-8). Die exakte Abschluss-SHA
und CI-Läufe stehen im additiven externen Abschlussnachweis. Kein alter
Backtest oder Renditelauf.

**D1 offen:** GitHub startet derzeit alte Workflows, besitzt aber noch keinen
abgenommenen privaten Zustandsadapter. Paket G oder ein konkret vorhandener
Dauerläufer H wurde nicht ausgewählt. Deshalb ist der gemeinsame Offline-Kern
fertig, die Betriebsanbindung offen. Das öffentliche Code-Repository darf kein
privates Versandjournal aufnehmen.

**D3 offen:** Verantwortlicher, unabhängiger Alarmweg und zweites geschütztes
Sicherungsziel sind nicht benannt. D2 wird erst am konkreten frischen Snapshot
entschieden. Realer Host, API-Schreibpfad, Stromausfallverhalten, externe
Alarmierung und Wiederherstellung nach tatsächlichem Storeverlust sind hier
nicht abgenommen. Ein SHA oder lokaler Restore beweist nicht, dass seit der
Sicherung nichts versandt wurde.

P3 muss D1/D3 klären und dann genau einen Betriebsweg getrennt abnehmen; bei
GitHub zuerst Paket G mit eigener Fake-API-Prüfung und späterer echter
API-Abnahme. P4 braucht einen neuen stillgelegten Snapshot, D2 für genau
diesen Zustand, externe Storeprüfung und eine ausdrückliche Live-Freigabe.
