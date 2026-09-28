# Etappe 3a: Ausführungs- und Risikovertrag F01/F12

28.09.2026. **Geprüfter Vertrag; D1-A, D2-A und D3 vom Nutzer bestätigt.
Keine Produktionskorrektur und kein Live-Go.**
Ausgangspunkt: D01 `5fabe2bae1506546fc31708ceecef2034365300f`, einschließlich F09.
Zweig: `codex/etappe-3a-ausfuehrungsvertrag`; Arbeitsbaum:
`C:/Users/oeztu/BTC-Trading/vertrag-3a-work`.
Etappe 3a endet mit diesem Vertrag und belegten Handfällen. Die drei für V1/3b
notwendigen Entscheidungen sind getroffen. Künftige Risikoschwellen und V2 bleiben
gesonderte Entscheidungen, ohne die Umsetzung von V1 zu blockieren.

## 1. Herkunft und Grenzen dieses Auftrags

Vor Schreibzugriffen geprüft: D01-HEAD, sauberer D01- und Audit-Arbeitsbaum,
Worktree-Liste, Remotes, lokales Tagobjekt und Ziel. Öffentliches Arbeitsrepo:
`https://github.com/szoceikaiser/btc-signal-app.git`. Der übergeordnete Ordner gehört
zu `260729-btc-trading-backup`; dort wird nichts committet. Neuer Worktree direkt
aus D01, ohne neuere main-, E44.4- oder E44.5-Commits.
Sicherungstag `sicherung/vor-audit-korrekturen-2026-09-28` bleibt unverändert:
Objekt `7d78094c17624b90b8f7ebc387b96570ff2c8ef7`, Ziel
`469be65f65327a3b6abf2794ceba09c1fe0de9e2`.

Gezielte Auditquelle: `ccf2b01c0578346f325261e72445b7375a9ac706`,
`docs/audit-2026-09-27/BERICHT.md` F01/F12, `REPRODUKTION.md`,
`audit/probes.py` und `audit/book.py`. Auditdateien wurden nur gelesen.
Kein Gesamtaudit, kein neues historisches Gitter, keine Originaldatenänderung.

## 2. Selbst geprüfter Ist-Zustand auf D01

Alle Zeilen beziehen sich auf den unveränderten D01-Code, nicht auf Audit/E44.5.

| Stelle | Tatsächliche Annahme / Wirkung |
|---|---|
| `engine/backtest.py:795`, `run_backtest` | Wertet vollständige Präfixe einschließlich aktueller abgeschlossener Kerze aus. `Position` wird bereits während der Signalerzeugung verändert; das gesamte Signalband entsteht vor der Abrechnung. |
| `engine/strategy_core.py:90`, `Signal`; `:1834`, `evaluate` | `ts` ist Kerzenanfang, nicht Wissens- oder Ausführungszeit. Signal hat einen `price`, aber keine getrennte Fillzeit, Ordergültigkeit oder Ausführungsbestätigung. |
| `strategy_core.py:2034` ff. | Selbst T1 hängt u. a. vom endgültigen Kerzentief, Muster und gewähltem Impuls ab; GP zusätzlich von Bestätigung. Auch ohne `confirm_t1` ist daraus keine vorher bekannte Order bewiesen. |
| `strategy_core.py:2137–2151`, `:2433–2460` | Neues Tief/Hoch aktualisiert das Retracement-Extrem, daraus entstehen Ziele, die gegen Hoch/Tief derselben Kerze geprüft werden. F12-Handfall H08 erreicht diesen Zweig. |
| `strategy_core.py:2200–2284` | Hauptstop vor Teilstop; `conditional_stop` kann vorher den Hauptstop durch Nachkauf ersetzen. Hauptstop/Restfreigabe, danach Teilstop und weitere Käufe/Verkäufe. `no_flip` sperrt abhängig davon, welches Signal zuvor entstand. Das ist Programmreihenfolge, keine Intrabar-Beobachtung. |
| `engine/backtest.py:865–1059`, `simulate` | Default `fill="level"` nimmt `signal.price`; `close` nimmt Schlusskurs derselben Kerze. Signale werden in Eingangsreihenfolge sofort gebucht. Keine Orderwarteschlange, keine Fill-Rückkopplung in die Engine. |
| `backtest.py:982–1024` | Kaufbudget aus Cash bei Zyklusbeginn × deploy; Kaufgebühr vom Bruttobudget, Teilverkauf vom BTC-Höchstbestand; E42-Stop nur Rückkaufeinheiten. F09 bereinigt vollständige Verkäufe um Rundungsreste. |
| `backtest.py:1083–1102` | Bestand nach sämtlichen Signalen gilt rückwirkend für Low und High. Feste Reihenfolge Low → High, dazwischen kein Schluss jedes Balkens. Weder exakte Intrabar-Messung noch verlässliche Risikogrenze. |
| `engine/main.py:1016–1040` | Nachhol-Läufe erzeugen historische Signalpakete je Kerze; Telegram-Zeit und tatsächliche manuelle Ausführung sind damit nicht belegt. Kein Broker-Fill-Ledger. |

Der alte Kommentar „Differenz Level/Schluss = Wert der Vorab-Order“ und dessen
„Untergrenze“ sind nicht gedeckt. Verzögerung kann günstig oder ungünstig sein.
Die alten Felder werden in 3a nicht umgedeutet oder geändert. 3b muss Referenzpreis,
Signalzeit und Fill getrennt darstellen und alte Ergebnisse als Altmodell erhalten.
D01 stellt abgeschlossene historische Kerzen sicher, nicht historische Publikations-
oder Telegram-Latenz. Die live verwendete inklusive Schlusszeitprüfung ist nicht
Gegenstand dieser Etappe.

## 3. Vorschlag V1: Schluss-Signal, danach Ausführung

### Zeit und Wissen

Eine 4h-Kerze i ist `[t_i, t_i + 4h)` in UTC. `bar_open_ts=t_i`,
`bar_close_ts=t_i+4h`; der alte `ts` bleibt eine Kerzen-ID und darf nicht still
umdefiniert werden. Zur Entscheidung gehören nur bis zu diesem Schluss verfügbare
Eingaben. Historisch setzen wir deren Verfügbarkeit idealisiert am Schluss voraus;
`knowledge_assumed_at` kennzeichnet diese Annahme. Reale Datenverfügbarkeit,
`decision_at`, Versand, Empfang und tatsächliche Ausführung sind eigene Zeiten,
sofern überhaupt belegt. Eine Bestätigung der laufenden Kerze ist vorher unbekannt.

**Empfehlung D1-A:** Alle handelbaren Schluss-Signale, einschließlich Levelberührung,
E41-Schlussstop, Nachkauf und E42, werden als Absichten zum direkt folgenden Open
ausgeführt. Logische Reihenfolge an gleicher UTC-Grenze: Schluss i, Entscheidung i,
Open i+1, Fill. Keine weitere Information aus Kerze i+1 darf die Entscheidung i
ändern. `signal.price` bleibt Referenz und ist kein Fillpreis.
Diese Null-Latenz-Annahme ist ein idealisiertes Benchmark-Modell: Der erste Kurs
nach der Grenze kann real schon vor Datenlieferung/Telegram gehandelt worden sein.
Nicht als erreichbare Live-Rendite oder statistische Ober-/Untergrenze ausgeben.

Alternativ D1-B: ein zusätzliches vollständiges 4h-Intervall warten, Fill am Open
i+2. Das ist ein getrenntes Verzögerungsszenario, kein gemessener Mensch/Broker.
Eine ausstehende Absicht bleibt in diesem Modell unverändert reserviert; bis zu
ihrem Fill keine weitere Handelsentscheidung, nur neue Marktdaten sammeln. So
entstehen keine widersprüchlichen Zwischenabsichten. Wer zwischenzeitliche
Stornierung/Revalidierung will, muss deren Regeln gesondert festlegen.

### Fill, Kurslücke und Kosten

Im V1-Hauptmodell: `p_buy = next_open * (1+s)` und
`p_sell = next_open * (1-s)`. Empfehlung D3: `s=0` als idealisierte Referenz,
zusätzlich fest vorab `s=0,001` und `s=0,005` je Seite als Belastungsszenarien.
0,1 % Gebühr je Fill beibehalten; keine Behauptung über tatsächlichen Broker-Tarif.
Slippage verändert den Ausführungspreis, Gebühr wird genau einmal gebucht.
Spanne der Signalkerze ist kein zulässiger Preisdeckel für das nächste Open.
Schlussstop bei Marke 90, Schluss 85 und Folge-Open 70 verkauft zu 70 vor Kosten,
nicht rückwirkend zu 90 oder 85. Umgekehrt ist eine günstige Lücke möglich.

Kein Folge-Open in zulässigen Daten: `unfilled_end_of_data`, kein Ersatzfill am
letzten Close. Bestand bleibt bis zum letzten abgeschlossenen Close bewertet,
ausstehende Absichten werden gezählt. Warmup ohne Bestände oder Orders; an einer
Teilfenstergrenze zählt nur dessen vereinbarter Handelsbereich. Keine Ausführung
aus H1 nach H2 übernehmen, wenn H2 als frischer Lauf definiert ist. D01-Cutoff
gilt auch für verwendete Folgekerzen; kein Open aus einer verworfenen laufenden
Kerze heimlich zurückholen. Fehlende 4h-Kerzen nicht durch „nächste vorhandene“
ersetzen: betroffenen Lauf als Datenlücke ablehnen. Monatsstände nach UTC-Grenzen:
Schluss des alten Monats vor dem Fill am Open des neuen Monats.

### Reihenfolge und Rückkopplung

**Empfehlung D2-A (fachliche Änderung):** Auf derselben Wissensbasis zunächst
Kandidaten ohne vorzeitige Handelszustandsänderung ermitteln. Erst entscheiden:

1. Hauptstop oder anderer vollständiger Ausstieg: gesamter echter Bestand;
   Hauptstop hat bei mehreren Gründen Vorrang als Buchungsgrund. Andere Absichten
   des Pakets entfallen, kein Wiedereinstieg im selben Paket.
2. Sonst Teilstop: nur die ausdrücklich betroffenen, noch vorhandenen Lose.
3. Sonstige Teilverkäufe nach dem Teilstop. Mehrere unterschiedliche Stufen dürfen
   bleiben; bestehende Leiter-/TP-Mengen bleiben unverändert, insgesamt höchstens
   vorhandene BTC. Stabile Reihenfolge gleicher Priorität ist die dokumentierte
   bisherige Erzeugungsreihenfolge mit expliziter Sequenznummer.
4. Sobald ein ausführbarer Verkauf beschlossen ist, entfallen alle Käufe dieses
   Pakets. Andernfalls Käufe in bestehender Sequenz, begrenzt durch verfügbares Cash.

Die Regel ordnet **gleichzeitig beschlossene Absichten**; sie behauptet keine
chronologische Reihenfolge vergangener Hochs/Tiefs. Eine abgelehnte/stornierte
Absicht darf keine Leiterstufe, Positionsmenge oder Verbrauchsmarke fortschreiben.
Zeitliche Beobachtungen (z. B. E41-Warten) bleiben von Handelsbestätigungen getrennt.
`conditional_stop` ist, solange unverändert konfiguriert, bereits die Strategie-
entscheidung vor einem tatsächlichen Stop-Kandidaten; D2 aktiviert/deaktiviert sie
nicht. Stop-Warten wird nicht automatisch zu einer liegenden Stop-Market-Order.

Alternative D2-B: bestehende sequenzielle Prioritäten explizit beibehalten und als
Strategieregel dokumentieren. Dann können Kauf/Verkauf gemäß vorhandenen Schaltern
im selben Paket vorkommen, jedoch ausschließlich am späteren Fill und mit echtem
Bestand/Cash. Kein nachträgliches Sortieren eines schon mutierten `Position`-Objekts.

In 3b muss ein Fill oder eine dokumentierte Ablehnung **vor** der nächsten
Handelsentscheidung in den simulierten Handelszustand zurückfließen. Ein fertiges
altes Signalband nur auf spätere Preise umzubuchen ist lediglich eine Preissensitivität.
Bei Cashmangel kein Phantomkauf, bei leerem Bestand kein Phantomverkauf; bei nur
teilweise finanzierter Tranche tatsächlich gefüllte Menge und Restablehnung melden.
Signal-/Beobachtungszustand und gebuchter Bestand müssen unterscheidbar sein.
F04-Einstand, F03-Stop-Nachzug und Persistenzkorrekturen bleiben Etappe 4. Ein
offener F04/F03-Fehler darf deshalb weiterhin die Strategie beeinflussen; der
Bericht muss dies nennen. Benötigt die technische Fill-Rückkopplung eine gemeinsame
Änderung mit Etappe 4, muss 3b den Konflikt vor einer Scope-Erweiterung offenlegen.

## 4. Vorher liegende bedingte Orders sind ein anderer Vertrag V2

V2 ist **keine Rechtfertigung alter Level-Fills** und derzeit nicht Hauptempfehlung.
Eine Order braucht ID, Entscheidungs-/Aktivierungszeit, bekannte Datenbasis,
Richtung, Limit/Stop-Typ, Menge/Budget, Gültigkeit, Storno/Ersetzung und ggf. OCO-
Geschwister. Nur Preisbedingungen dürfen nach Aktivierung auslösen; unbekannter
späterer Flow oder Kerzenschluss darf eine frühere Ausführung weder erlauben noch
ungeschehen machen. Neue Marken aus Kerze i sind frühestens danach aktiv.

Vollständiger deterministischer V2-Vorschlag für eine spätere Entscheidung:
am Schluss i geplante Orders gelten ab Open i+1 für genau diese eine 4h-Kerze,
danach verfallen sie; erneute Platzierung nur mit neuer ID und reserviertem Kapital.
Am Open bereits vorher aktive Orders zuerst abarbeiten, danach dort wirksam
werdende Stornos/Ersetzungen und neue Orders. Bei gleicher Grenze ist dies eine
ausdrückliche konservative Modellregel, keine gemessene Brokerlatenz.
Stop-Ausgang vor Gewinn-Limit, dann übrige Verkäufe vor Käufen, wenn mehrere
bereits aktive Orders durch dieselbe Eröffnungslücke auslösbar sind. OCO-Geschwister
sofort löschen. Neue Schutzorders erst nach tatsächlichem Einstiegsfill aktiv.

Ohne Slippage: liegendes Kauf-Limit L bei Open <= L zum Open, sonst bei Berührung
zum L; liegendes Verkauf-Limit L bei Open >= L zum Open, sonst bei Berührung zum L.
Liegender Long-Stop-Market S bei Open <= S zum Open, sonst beim Abwärtsdurchgang
zum S. Stop-Limit garantiert keinen Fill; es müsste als eigener Typ modelliert
werden und gehört nicht in diesen vereinfachten V2-Vorschlag. Gebühren je Fill;
Limitpreise niemals durch pauschale Slippage verletzen. Berührung garantiert real
weder verfügbare Liquidität noch Queue-Priorität oder Vollausführung.

Intrabar-Konflikte: beide möglichen Extremreihenfolgen als Szenarien ausweisen,
ohne günstige Reihenfolge auszuwählen. Wiederholte Leveldurchgänge können zusätzliche
Ereignisse erzeugen: O-H-L-C und O-L-H-C sind bei dynamischen Orders **keine**
bewiesenen globalen Grenzen aller Pfade. Ohne feinere Daten solche Fälle markieren
und aus einer exakten Leistungsbehauptung ausschließen; keine stille Worst-Case-
Behauptung aus lediglich zwei Pfaden. Bei Wahl D1-C muss vor Umsetzung von V2
ein ergänzender Entwurf die tatsächlich gewünschten Ordertypen und Konfliktfälle
festlegen. Der gegenwärtige 3b-Vorschlag V1 ist dann nicht automatisch freigegeben.

## 5. Bestand, Kapital und Risiko V1

Empfehlung D3 beschränkt die Abnahme auf unverschuldetes Long/Spot. Short-Margin,
Funding, Liquidationen und F02 sind ausdrücklich nicht durch diesen Vertrag gelöst.

`C` = Cash, `Q` = tatsächlich gefüllte BTC, `R` = reserviertes Cash,
`C_available=C-R`, verkaufbar = Q minus reservierte Verkaufsmengen.
Reservierung ist keine Ausgabe und kein zusätzlicher Vermögenswert.
`E(p)=C+Q*p` ist Mark-to-Market nach bereits gezahlten Gebühren, ohne hypothetische
Schlussverkaufsgebühr. Keine fingierte Liquidation am Testende. Marktwert der Position
ist `Q*p`, historischer Einstand ist etwas anderes.

Kauf mit Bruttobudget B (einschließlich Gebühr f):
`C_after=C_before-B`, `Q_after=Q_before+B*(1-f)/p_fill`.
Verkauf q: `C_after=C_before+q*p_fill*(1-f)`, `Q_after=Q_before-q`.
Immer `0<=B<=C_available`, `0<=q<=Q_available`; jedes E42-Los <= Gesamtbestand.
Das bisherige Zyklusbudget und die Teilverkaufsquoten sind keine neue Strategie-
optimierung: `A=Cash_beim_neuen_Zyklus*deploy`, Kauf `min(C_available,A*tranche/100)`;
BTC-Höchstbestand nur nach echten Fills erhöhen, bei vollständig geschlossenem
Zyklus zurücksetzen. TP1/TP2 je 40 % und Leiter die bestehende Quote vom
BTC-Höchstbestand, gedeckelt auf verbleibende Menge; Teilstop nur betroffene Lose.
F09-Rundungserhalt und Wiederanlage bleiben Abnahmekriterien.

Jedes Ereignis protokolliert ID, Entscheidungsquelle, Order/Fillzeit, Referenz-/Fill-
preis, Status/Grund, Gebühr, C/Q/R davor und danach sowie Marktwert **am selben
Referenzkurs**. Eine reine Umbuchung ohne Kosten verändert E am Fillkurs nicht.
Slippage bewertet man gegen das unveränderte Open, nicht gegen den jeweils
günstigeren eigenen Fillpreis.

### Verbindliche zeitliche Bewertung (Vorschlag)

Am Open zunächst Altbestand zum Open bewerten: damit bleibt der Verlust durch die
Nacht-/Kerzenlücke vor einem Verkauf erhalten. Dann vor und nach jedem Fill zum
unveränderten Open bewerten. Während der Kerze verwendet V1 den Bestand **nach**
Open-Fills unverändert bis Close; Absichten am Close verändern ihn noch nicht.
Bei einem reinen Schluss-Fill-Vergleich gilt umgekehrt Altbestand bis unmittelbar
vor dem Schluss-Fill. H01 und H02 unterscheiden genau diese Zeitlagen.

Hauptkennzahl: `D_close=max_t(1-E_close(t)/max(E_start,E_close(<=t)))`, positive
Verlustgröße. Einschließlich Startwert und jedes abgeschlossenen Close, ohne
Zwischen-Fills als zusätzliche Close-Peaks. Das ist im Modell exakt, erfasst aber
keine vorübergehenden Intrabar-Verluste. Alte negative `max_drawdown_pct`-Werte nicht
unter demselben Namen ersetzen: neue benannte Felder mit Einheit/Definition.

Zusätzlich `D_intrabar_lower` und `D_intrabar_upper`, einschließlich Open und
Ereignisbewertungen. Für V1 mit konstantem Long-Bestand innerhalb jeder Kerze,
festen Open-Fills und OHLC-Extrema sind Low→High bzw. High→Low mit Open/Close
die untere bzw. obere mögliche maximale Drawdown-Grenze. Vorheriger Peak und
bisheriger maximaler Drawdown werden durchgehend fortgeführt, niemals je Kerze
zurückgesetzt. Begründung: Innerhalb einer Kerze ist E monoton in p; End-Peak
`max(alter Peak,E(Open),E(High),E(Close),E(Ereignisse))` hängt nicht von der
Extremreihenfolge ab. High vor Low maximiert den möglichen Rückgang; Low vor High
minimiert ihn, jedoch zählen der spätere Close und frühere Peaks weiter.
Wiederholte Besuche von High/Low können diese obere Grenze ohne Bestandsänderung
nicht überschreiten. H15 zeigt, warum die untere Grenze keine Prognose ist.

Empfehlung: Schluss-DD **und** obere Grenze prominent ausweisen; obere Grenze als
Risikovorsicht für künftige Vergleiche, nicht als beobachteter tatsächlicher Verlust.
Bei V2, wechselndem Intrabar-Bestand oder gemischten Short-/Long-Büchern gilt dieser
Beweis nicht. Kein VaR, keine Verlustwahrscheinlichkeit und keine Verlustgarantie.

Fenster-DD bleibt zwischen Strategien pfadabhängig. Für E41 später ein separater
Vergleich derselben eingefrorenen Startposition `(C0,Q0,E0)` am Referenzstop:
`L_extra=max_t max(0,E_ref_exit-E_wait(t))/E0`, Zeitraum vom Referenzausstieg bis
tatsächlichem Warteausstieg, ohne andere Folgegeschäfte/Wiederanlagen. Gleiche
Startlose, Kosten und Zeitbasis; Q für diesen Diagnosevergleich eingefroren.
Das isoliert eine Halteentscheidung, bildet aber nicht das komplette Portfolio ab.
Ist das Endereignis unbekannt, Fall als rechtszensiert ausweisen. Für Intrabar-Werte
weiterhin Grenzen. **E41.6 wird in 3b nicht nebenbei gebaut.**
Alte „höchstens 1 Punkt mehr DD“-Schwellen sind mit dem korrigierten Maß nicht
automatisch übertragbar. Neue Grenzen/Abschaltregeln vor späterer Strategiemessung
entscheiden; 3b-Erfolg ist korrekte Buchführung, keine Mindestrendite.

## 6. Unabhängige Handfälle

Alle Preise in USD/BTC, Default 10.000 USD, keine Gebühren/Slippage außer H10.
Die 16 Szenarien sind Akzeptanzbeispiele, kein gebauter neuer Simulator.

| Fall | Ereignis / Rechnung | Erwartung und Aussage |
|---|---|---|
| H01 Verkauf nach Tief | Bereits 100 BTC; O100 H100 L50 C100; Verkauf erst am Close oder nächsten Open100. Tiefwert 5.000. | Intrabar-DD 50 %, Close-DD 0 %. Ist-Abrechner meldet 0 %. |
| H02 Kauf nach Tief | Bis Close nur Cash; dieselbe Kerze; Kauf erst am Close100 bzw. danach. | Altes Tief erzeugt 0 % Positionsverlust. Ist-Abrechner mit Schluss-Signal meldet 50 %. |
| H03 Extremreihenfolge | 100 BTC, O100 H200 L50 C100. L→H→C: Werte 10.000/5.000/20.000/10.000; H→L→C umgekehrt. | DD-Band 50–75 %, Close-DD 0 %. Schluss nach Hoch mitwerten. |
| H04 Kausaler Kauf | Schluss-Signal Referenz100, Folge-Open125, Folge-Close100. | 80 BTC statt 100; Endwert 8.000. Signalpreis ist kein Fill. |
| H05 Stop-Lücke | 100 BTC, Schlussstop unter90 bei85, Folge-Open70. | 7.000 Cash; 30 % Verlust gegenüber 10.000, kein garantierter Stoppreis90. |
| H06 Vorherige Limits | Kauf-Limit100, Open90: 10.000/90 BTC. Separat 100 BTC, Verkauf-Limit120, Open130. | 111,111… BTC bzw. 13.000 Cash im idealisierten V2. Keine Ausführung zum ungünstigeren Limit erzwingen. |
| H07 OCO-Konflikt | 100 BTC, vorher Stop90 und Ziel110 aktiv, O100 H120 L80 C100. | Low zuerst: 9.000 Cash; High zuerst: 11.000. Nicht aus OHLC allein entscheidbar. |
| H08 Neues Ziel | Impuls80→160, altes Korrekturtief120: Ziel200. Neue Kerze O140 H190 L90 C140: neues Ziel170. | Engine erzeugt TV1 zu170. Auf Pfad 140→190→90→140 wird170 nach Kenntnis des Tiefs nie erreicht. V1 verkauft erst am Folge-Open. |
| H09 Konfliktpaket | Vorher C5.000/Q50, Preis100. Vollstop plus Kauf: Empfehlung nur Vollstop. Alternativ nur Teilverkauf20 plus Kauf: nur Teilverkauf. | C10.000/Q0 bzw. C7.000/Q30; Kauf entfällt. D2-B würde andere Folgeposition erlauben. |
| H10 Kosten | B10.000, Kauf100, f0,001: Q99,9; vollständiger Verkauf100: 99,9×100×0,999. | Cash9.980,01, Verlust19,99 = 0,1999 %. Keine doppelte/fehlende Gebühr. |
| H11 Datenende | Kaufsignal an letzter zulässiger Kerze, kein zulässiges Folge-Open. | Q0, Cash10.000, ein nicht ausgeführtes Signal. Rechnung bestätigt nur Nullbestand; Scheduling in 3b zu testen. |
| H12 Storno zu spät | Vorheriger Stop90 aktiv; Open80; Storno wird erst an dieser Grenze wirksam. | Nach V2-Vorschlag erst Fill80, C8.000; Storno kann Verlust nicht löschen. |
| H13 Teilverkauf am Open | Vorher Q100, Open100: 50 verkaufen, danach Low50. | C5.000/Q50, Tiefwert7.500. Bei Verkauf erst am Close läge Tiefwert noch5.000. |
| H14 Gleiche E41-Startlose | E0=10.000/Q100; Referenzausstieg90, Warten bis zwischenzeitlich60. | Zusatzverlust `(9.000−6.000)/10.000=30 %`; keine Beimischung späterer Wiedereinstiege. |
| H15 Wiederholte Extreme | Q100, Pfad100→50→200→50→100, gleiche OHLC wie H03. | 75 % DD trotz erstmaliger Reihenfolge Low→High; obere Grenze bleibt75 %. Bei bedingten Orders wären zusätzliche Durchgänge relevant. |
| H16 Cashgrenze | Zwei Kaufbudgets je7.500 aus C10.000. | Erst7.500, dann höchstens2.500; keine negative Kasse, tatsächliche Teilmenge rückmelden. |

## 7. Getroffene und verbleibende Entscheidungen

Die drei Auswahlfragen wurden im Gespräch einzeln ausdrücklich beantwortet.
Das frühere „Weiter“ wurde nicht als Zustimmung zu später gestellten Fragen benutzt.

| ID | Empfehlung / Begründung | Alternative / Konsequenz | Status |
|---|---|---|---|
| D1 | A: Schluss-Signale → direkt folgendes Open. Mit 4h-Daten klar prüfbar, kein rückwirkender Preis. | B: Open i+2 mit zusätzlicher Wartekerze; C: vorher liegende Orders, ergänzender V2-Entwurf nötig. | **A bestätigt**: „Schluss-Signale → nächstes Open (empfohlen)“ |
| D2 | A: Ausstiege vor Käufen, bei Verkauf kein Kauf im Paket. Verhindert künstliche Sofort-Wiederanlage und widersprüchliche Mengen. | B: bisherige Engine-Priorität bewusst erhalten; anderer Strategiepfad, gleiche kausale Fillregeln. | **A bestätigt**: „Verkäufe haben Vorrang; kein gleichzeitiger Kauf (empfohlen)“ |
| D3 | Schluss-DD plus obere Intrabar-Grenze; Long/Spot; f0,1 %, s0/0,1/0,5 %; neue DD-Schwellen später. | Nur Schluss-DD verbindlich (Intrabar weiterhin sichtbar), oder Paket offen lassen und Kosten/Geltungsbereich einzeln entscheiden. | **Paket bestätigt**: „Dieses Risikopaket übernehmen (empfohlen)“ |

Die Bestätigungen legen den fachlichen V1-Vertrag fest; sie starten in diesem Chat
keine Etappe 3b. Offen bleiben vor späteren Strategie-/Live-Entscheidungen konkrete
neue DD-Grenzen und Abschaltregeln. E41.6 erhält erst in eigener Etappe ein Budget.
V2-Ordertypen/Feindaten und Short-Margin/Funding benötigen eigene Entwürfe. Keine
dieser offenen Fragen wird durch stillschweigende Defaults entschieden.

## 8. Prüfung, Sicherung und Abnahmeplan für 3b

`python tools/verify_3a_contract.py` prüft **27 rationale Rechenidentitäten** zu
16 Handfällen sowie acht absichtlich falsche Kontrollwerte (alle abgewiesen).
Die Kontrollen sind **keine Produktionsmutationen und kein Beweis einer 3b-
Implementierung**. Drei gezielte Ist-Proben erreichen `simulate` bzw. `evaluate`:
F01-Verkauf, F01-Kauf und F12-neues Extension-Ziel. Sie bestätigen die noch offenen
Fehler. Protokoll: [3a-pruefung.json](3a-pruefung.json).
Die unveränderte vorhandene Suite wurde einmal lokal geprüft: **600 bestanden,
0 fehlgeschlagen**. Ergebnis separat
[3a-tests.log](3a-tests.log). Kein erneutes historisches Backtest-Gitter.

3b-Abnahme nach Entscheidungen: Ereignis-Ledger gegen unabhängige Handfälle und
Losrechnung; Präfix-/Kausalitätstest; Gebühren/Slippage und Datenende; volle und
teilweise Ausführung/Ablehnung mit Rückkopplung; Paketprioritäten mit echten
Engine-Kandidaten; F09-Wiederanlage; D01-Stichtag/Teilfenster; Risiko vor/nach Fill,
Lücke, Close und Extremreihenfolgen. Diese Assertions müssen den jeweiligen Zweig
erreichen und gezielte Sabotagen fangen. Keine bloße Umbuchung alter Signallisten
als „vollständig korrigierte Strategie“ verkaufen. Bestehende 600 Tests erhalten
oder eine durch den bestätigten Vertrag notwendige Änderung einzeln begründen.
Alte und neue Ergebnisse separat, Erfolg unabhängig von Renditevorzeichen.

In 3a verändert: nur dieser Bericht, Prüfartefakte/-skript, Etappen/Kurzstand/
Übergabe und Startprompt. `engine/`, `site/`, Workflows und alle historischen
Ergebnisse müssen gegenüber D01 identisch sein. Push nur auf eigenen Zweig.
Der vorhandene Push-Workflow `Tests` ist zulässig; `Backtest` wird nicht gestartet,
Pages reagiert nicht auf diesen Zweig oder Tests. Remote-HEAD, Tests zur exakten
SHA und unveränderten Sicherungstag lesend prüfen. Abschlussbundle, Archiv und
Wiederherstellungsprobe samt SHA/CI-Beleg lokal unter `audit-backups` sichern.

## 9. Verbleibende Grenzen und nächster Auftrag

4h-OHLC belegt keine Intrabar-Reihenfolge, wiederholten Durchgänge, Spreads,
Orderbuchliquidität, tatsächliche Fills, Queueposition, Teilausführungen oder
historische API-/Telegram-Reaktionszeit. Selbst Next-Open ist nur eine festgelegte
Ausführungsannahme. Flow-Verfügbarkeit/Revisionen und die anderen Auditfehler
bleiben offen. Kein Nachweis von Strategiegüte, Robustheit oder echter Rendite.

**Neuer Chat für 3b sinnvoll. Empfehlung GPT-6 Sol, Aufwand hoch**; D1–D3 sind
entschieden. Aufwand hoch beibehalten; von der für 3a empfohlenen Astra-Stufe
auf Sol wechseln. Begründung: begrenzte Codearbeit, aber Rückkopplung und
Risikobuchführung erfordern gründliche Prüfung. Bei Wahl V2 oder ungelöster
Grundsatzfrage zunächst Astra/hoch für den ergänzenden Vertrag. Dies ist unsere
Aufgabenempfehlung, keine automatische Umstellung. Offizielle Grundlage:
[GPT-6 Sol: komplexe Coding-Aufgaben, high unterstützt](https://developers.openai.com/api/docs/models/gpt-6-sol),
am 28.09.2026 abgerufen. Vollständiger Auftrag: [START-3B.md](START-3B.md).
