# F17: Chartidentität und Herkunft (29.09.2026, vor Umsetzung)

Basis exakt 6c0c6fdd56db9bb27febaf42c56f6e33bcab0685. Nur lesende
Chartprojektion; Engine, Versandliste, Position und historische Dateien unverändert.

1. Dateiquellen bestimmen die Herkunft: signals.json = Live-Signalreferenz (L),
   backtest_signals.json = historische Signalband-Diagnostik (H). Optionales
   execution_v1.json enthält genau ein explizites Ergebnis mit model
   V1_close_to_next_open_zero_latency; nur ledger/status=filled = Modell-Fill (V1).
   Keine automatische Erstellung, Neuberechnung oder Auswahl eines Szenarios.
   Live-Referenz ist kein Broker-Fill; V1 ist simuliert; H ist kein V1-Beleg.
2. Identität ist ein versionierter, nach Quelle getrennter Chartschlüssel.
   Vorhandene signal_id/id wird als Quellen-ID benutzt, niemals als Zustellbeleg.
   Gleiche Quellen-ID mit identischem vollständigem JSON-Inhalt wird dedupliziert.
   Widersprüchliche Inhalte bei derselben ID bleiben als markierte Kollision erhalten.
   Keine Herkunft gewinnt durch Zeit/Typ oder Eingangsreihenfolge.
3. Altbestand ohne ID: deterministischer Schlüssel aus Quelle, kanonischem
   vollständigem JSON-Inhalt (sortierte Objektschlüssel) und Vorkommensnummer
   identischer Inhalte. Kein verlustbehafteter Hash. Identische Altzeilen bleiben
   getrennt, weil ihre tatsächliche Identität nicht rekonstruierbar ist.
   Schlüssel bleiben bei Reload/JSON-Neustart, Umsortieren und Hinzufügen anderer
   Datensätze stabil. Für ununterscheidbare Kopien ist nur die Schlüsselmenge stabil;
   Änderung/Löschung solcher Kopien erlaubt keine historische Einzelzuordnung.
   Migration ausschließlich im Speicher, ohne Zustandsschreiben oder Versand.
4. Sortierung: Ereigniszeit, feste Quellenfolge L/H/V1, numerische Sequenz sofern
   vorhanden, danach vollständiger Chartschlüssel; unabhängig von Ladefolge.
   Referenzen verwenden unverändertes ts (Kerzenanfang), Modell-Fills fill_at und
   fill_price. Mehrere Marker nach Snap auf derselben Anzeige-Kerze bleiben erhalten.
5. Marker tragen Quellenkürzel; eine lesbare Ereignisliste nennt Quelle, Zeit,
   Referenz-/Fillpreis, Tranche/Menge, Grund, Identität und Kollision/Altbestand.
   Externe Texte werden als Textknoten gerendert. Ungültige Zeilen werden sichtbar
   gezählt; unbekannte V1-Modelle abgewiesen, nicht als historische Fills umgedeutet.
6. Netzfreie Abnahme am tatsächlichen Merge/Marker-/Listenpfad: Originalfehler,
   beide Snapshot-Kollisionen, gegensätzliche Quellen, mehrere gleichartige
   Kerzensignale, explizite ID-Kollision, Altduplikate, Reload/Reorder, V1-Zeit/Preis,
   ungültige Daten und Textinjektion; grüne Vorproben vor gezielten Sabotagen.
   712 bestehende Tests unverändert. F13-ID ist lokale Versandidentität, kein
   Telegram-Idempotenzschlüssel; Versandliste bleibt vollständig unangetastet.

Kein Live-Go. Unklare Zustellung blockiert weiterhin, keine Exactly-once-Zusage;
ephemerer Runnerverlust vor Git-Persistenz bleibt offen. V2/Shorts/E41.6 und
weitere Befunde bleiben getrennt.
