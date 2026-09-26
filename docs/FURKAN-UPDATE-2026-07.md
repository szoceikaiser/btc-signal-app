# Auswertung: Furkan-Update-Video Juli 2026 (Transkript von Kaiser)

Stand: 2026-07-27 · Quelle: Transkript mit Zeitstempeln, von Kaiser eingefügt.
Zweck: Was ist NEU gegenüber `docs/STRATEGIE.md` (Order-Flow-Tutorial) und was davon
lässt sich in die Engine bauen? Nur umsetzbare Punkte — Marktmeinung und Nachrichtenlage
(Vierjahreszyklus, Saylor/Strategy, Iran, Fed) sind bewusst nicht Teil dieser Liste.

## 1. Kapital-Reserve („Pulver behalten") — GEBAUT 2026-07-27, Messung ausstehend

Zitat 21:12–21:22: *"Wenn es runtergeht, muss man Pulver haben zum Nachschießen, klaren
Plan haben, **ab welchem Niveau man wie viel Prozent seines Kapitals reinschießt**. Wenn
es aber nicht runterläuft, muss man so positioniert sein, dass man zufrieden ist."*

Das ist eine explizite Kapitalregel und sie steht im Widerspruch dazu, wie unsere
P&L-Simulation rechnet: Dort werden über die Tranchen bis zu **100 % des verfügbaren
Geldes** investiert, ein Puffer wird nirgends zurückgehalten (`simulate()` in
backtest.py: `alloc = cash` beim Positionsstart, danach `min(cash, alloc * tranche%)`).
Furkan hält bewusst Reserve für tiefere Niveaus.

**Baubar:** Obergrenze für den eingesetzten Anteil je Position (`deploy_pct`), Rest bleibt
liegen. Betrifft nur die Simulation, nicht die Signallogik. Dazu neu im Bericht: Spalte
**max. Rückgang (Drawdown)** — ohne die sähe eine Reserve zwangsläufig schlecht aus.

### MESSERGEBNIS 2026-07-27 (Fenster 18.11.2025–27.07.2026): Hypothese widerlegt

| Einsatz | Rendite | max. Rückgang | Rendite je Rückgangs-Punkt |
|---|---|---|---|
| 100 % (keine Reserve) | +30,0 % | −11,5 % | 2,61 |
| 60 % | +17,9 % | −7,7 % | 2,32 |
| 50 % | +14,8 % | −6,4 % | 2,31 |

Die Rendite fällt **fast exakt proportional** zum Einsatz (30,0 × 0,6 = 18,0 gegen
gemessene 17,9; × 0,5 = 15,0 gegen 14,8). Meine Vermutung, die Reserve würde den tieferen
Tranchen zu Kapital verhelfen und sich dadurch selbst bezahlen, ist damit **falsch** —
der Effekt ist nicht messbar. Der Rückgang sinkt sogar etwas WENIGER als proportional,
d. h. risikobereinigt ist die Reserve leicht schlechter, nicht besser.

**Konsequenz:** `deploy_pct` bleibt bei 100 %. Wer weniger Risiko will, legt schlicht
weniger Geld auf das Konto — derselbe Effekt, ohne Extra-Mechanik.

**Wichtige Einordnung (nicht als Widerlegung von Furkan lesen):** Er spricht über die
Reserve im Zusammenhang mit dem **Spot-Portfolio** und einem möglichen finalen Crash —
also über Niveaus weit unter jeder laufenden Trading-Position (seine Valuezone
55.500–47.100 bei einem Kurs von 65.000). Wir haben die Reserve in der falschen Ebene
eingebaut: Innerhalb des kurzfristigen 4h-Systems ist sie nur ein Größenregler, weil die
Kaufleiter die Dips innerhalb einer Position ohnehin schon abfängt. Ihren eigentlichen
Zweck erfüllt sie erst mit Punkt 3 (Valuezone) — das hebt Punkt 3 in der Priorität.

### NEBENBEFUND aus der neuen Drawdown-Spalte (wichtiger als die Reserve selbst)

Die Spalte war für die Reserve gedacht, zeigt aber etwas anderes — was `flush_entry`
wirklich kostet:

| Variante | Rendite | max. Rückgang | Rendite je Rückgangs-Punkt |
|---|---|---|---|
| nur Long + Kaufleiter (ohne Flush) | +19,9 % | **−6,3 %** | **3,16** |
| LIVE: + Flush core | +33,1 % | −12,7 % | 2,61 |
| LIVE + Stop nachziehen | +30,0 % | −11,5 % | 2,61 |

Der Flush-Einstieg **verdoppelt Rendite und Rückgang zugleich**. Risikobereinigt ist
„nur Long + Kaufleiter" mit Abstand die ruhigste gute Variante (3,16 gegen 2,61) — und
sie hat mit 137 statt 207 Signalen ein Drittel weniger Telegram-Nachrichten.
Das ist keine Rechenfrage, sondern eine Temperamentsfrage: mehr Rendite mit doppelt so
tiefen Einbrüchen, oder ruhiger schlafen. Kaisers Entscheidung, nicht meine.
Bestätigt nebenbei den nachgezogenen Stop (E9.10): −11,5 % statt −12,7 % Rückgang bei
gleichem Verhältnis, dazu besserer Recall — er kostet Rendite, aber er kauft dafür
messbar etwas.

## 2. Teilverkauf UNTER dem vorherigen Hoch — NEU, könnte die schwache Verkaufsseite heben

Zitat 19:52–19:57: *"Die weiteren Gewinne werde ich dann hier bei über 66.600 **hier unter
diesem Hoch** rausnehmen, wenn wir da hochlaufen."* Dazu 19:24: *"Dieses Hoch vom 22. Juni
ist immer noch nicht raus."*

Er nimmt Teilgewinne also an einem **Struktur-Niveau** (letztes Swing-Hoch, knapp
darunter), nicht an einer rechnerischen Fib-Extension. Unsere Engine kennt nur
Extension 1.0 / 1.618. Genau die Verkaufsseite ist unser schwächster Wert
(9/17 im letzten Backtest).

**Baubar:** Teilverkauf, wenn der Kurs sich dem letzten bestätigten Pivot-Hoch nähert
(z. B. 0,5 % darunter) — die Pivot-Erkennung ist bereits da (`find_pivots`). Schaltbar,
gegen die Live-Variante messen. Hängt inhaltlich mit E9.11 zusammen: über alten Hochs
liegt typischerweise die Liquidität.

## 3. MVRV-„Valuezone" — VON KAISER ABGELEHNT (2026-07-27): er kauft kein Spot

Entscheidung Kaiser: *„da ich keine Spots kaufen will, ist die Valuezone für mich nicht
relevant."* Damit ist die Spot-Ebene vom Tisch — sie wird NICHT gebaut.

Quelle trotzdem festgehalten (per Screenshot aus dem Video identifiziert, Zeitmarke 14:02):
**Bitcoin Magazine Pro**, `bitcoinmagazinepro.com/charts/mvrv-zscore/`. Rote Überhitzungs-
zone ab ca. Z = 7, grüne Kaufzone bei Z ≤ 0. Ob es dafür eine kostenlose API gibt, wurde
NICHT recherchiert (nicht mehr nötig).

OFFEN GEBLIEBENE ALTERNATIVE (Kaiser vorgelegt, noch nicht entschieden): Derselbe
MVRV-Z-Score könnte statt für Spot-Käufe für den **Richtungs-Bias** dienen — also die
Frage long/short, die nach allen Messungen der größte offene Hebel ist. Vorteil gegenüber
dem pausierten KI-Makro-Bias (E8.5): MVRV-Z hat eine lange Historie und wäre damit
**backtestbar**, während die KI-Variante nur vorwärts validierbar ist.

### Ursprüngliche Analyse (für den Fall, dass es doch mal relevant wird)

Zitat 17:07–17:19: *"Ich schaue mir diese dynamischen Modelle an, abgeleitet vom MVRV, wo
diese Valuezone entsteht. **Immer wenn der Kurs hier reinfällt, kaufe ich Spot nach.**"*
Konkret 20:34–20:40: *"Die Valuezone liegt aktuell bei 55.500 bis 47.100."*

Wichtig: Das ist **nicht** sein 4h-Trading. Er trennt sauber zwischen
- **Spot-Portfolio**: langfristig, Nachkauf in der Valuezone, kein Stop, kein Timing
- **Futures-Position**: kurzfristig, Golden Pocket + Order-Flow, mit Stop

Unsere Engine bildet ausschließlich die zweite Ebene ab. Die erste fehlt komplett.

**Baubar, aber Datenfrage offen:** Braucht MVRV bzw. MVRV-Z-Score aus On-Chain-Daten.
Ob es dafür eine kostenlose API gibt, ist NICHT recherchiert. CoinAnk hat auf API-Level 1
mehrere Indikator-Endpunkte (Puell, ahr999, Pi-Cycle, 200-Wochen-Heatmap, Rainbow) —
ob MVRV dabei ist, muss geprüft werden. Erst Quelle klären, dann bauen.

### MESSERGEBNIS 2026-07-27 (E10.2)

| Variante | Recall | Praez. | Rendite | max. Rückgang |
|---|---|---|---|---|
| LIVE +Stop (Referenz) | 57 % | 34 % | +29,9 % | −11,5 % |
| LIVE +Stop +Verkauf am letzten Hoch | 61 % | 34 % | +27,1 % | −12,0 % |
| LIVE +Stop +Verkauf am schwachen Hoch | 61 % | 33 % | +27,3 % | −11,9 % |

Zwei Befunde:
1. **Der Spot-Filter bringt nichts.** „on" und „weak" liegen mit +27,1 % und +27,3 % im
   Rauschen auseinander, bei 229 gegen 227 Signalen. Kaisers Frage „was bringt uns die
   Warnung?" ist damit sauber beantwortet: nichts Messbares. Die Beobachtung stimmt
   vermutlich, sie ist nur kein handelbarer Vorteil. Erledigt, nicht weiter verfolgen.
2. Der Verkauf am Hoch hebt den Recall auf 61 % — denselben Wert wie die Liquidationszonen
   — und kostet 2,8 Punkte Rendite. Beide erreichen exakt dieselbe Decke, treffen also
   vermutlich dieselben verpassten Verkaufstage.

### ÜBERGREIFENDER BEFUND (nach fünf Messungen auf der Verkaufsseite)

Getestet wurden: Leiter-Teilgewinne (E8.2), Rest-Freigabe (E9.9), Liquidations-Kaskaden,
Liquidationszonen (E9.11), Verkauf am Struktur-Hoch (E10.2). **Alle heben die Ähnlichkeit
zu Furkans Verkaufstagen. Alle kosten Rendite.** Von +33,1 % (nur Fib-Ziele) auf
+27 bis +30 %, je nach Mechanismus.

Die Erklärung ist konsistent: Jeder dieser Mechanismen verkauft ZUSÄTZLICH und FRÜHER.
Die Fib-Ausstiege der Engine sind für den Gewinn offenbar besser getimt als Furkans
Struktur- und Liquiditäts-Ausstiege — jedenfalls in diesem Fenster und mit unseren
Näherungen.

**KONSEQUENZ: Die Verkaufsseite ist auserzählt.** Die Lücke im Recall (9/17) kostet kein
Geld, sie ist nur eine Unähnlichkeit. Weitere Arbeit dort ist verschwendet. Die offenen
Hebel liegen bei der RICHTUNG (Bias) und den EINSTIEGEN.

### ÜBERHOLT — KORREKTUR 28.07.2026: `high_exit="on"` ist LIVE

Der Satz „die Verkaufsseite ist auserzählt" galt **nur für die damalige Basis**. Kaisers
Einwand vom 28.07. („auf dem Weg nach oben sind Teilgewinne vor den Liquidationen sinnvoll,
so beschreibt es Furkan, oder?") führte zur Neumessung gegen die inzwischen geänderte Basis
(Mindest-Stopabstand 2 % + Liq-Konfluenz):

| Basis | Rendite ohne `high_exit` | mit `high_exit="on"` | Recall |
|---|---|---|---|
| alt (07/2026) | +32,2 % | +28,3 % → **−3,9 Punkte** | 57 → 64 % |
| neu (28.07.) | +39,1 % | **+41,5 %** → **+1,2 Punkte** | 50 → 57 % |

Erklärungs-HYPOTHESE: Früher wurden viele Positionen mit fast keinem Stop-Abstand ohnehin
ausgestoppt — früher Teilgewinn beschnitt dann nur die wenigen Gewinner. Seit die
aussichtslosen Einstiege unterbleiben, erreichen mehr Positionen den Widerstand tatsächlich.

**DIE ALLGEMEINE LEHRE, wichtiger als dieser Einzelfall:** Ein Mechanismus-Befund gilt
immer nur gegen die Basis, gegen die er gemessen wurde. Nach jeder Basis-Änderung sind
verworfene Mechanismen wieder offen. „Auserzählt" ist ein Zustand, kein Urteil.
`liq_exit` (Verkauf an den Liquidations-Niveaus) wurde gegen dieselbe neue Basis
mitgemessen und bleibt schlechter (+34,7 % gegen +41,5 %) — der Befund gilt dort weiter.

**GEBAUT 2026-07-27 (E10.2):** `high_exit` in evaluate —
"off" | "on" | "weak". Teilverkauf (15 %), sobald der Kurs bis auf 0,5 % an das nächste
bestätigte Pivot-Hoch heranläuft, höchstens 2× je Position. Short spiegelbildlich am
Pivot-Tief. Neuer Helfer `next_pivot_beyond`. Live über `config.json` schaltbar.
Punkt 4 ist darin aufgegangen (siehe unten).

## 4. Ausbruch ohne Spot-Nachfrage — NICHT als Warnung gebaut, in Punkt 2 aufgegangen

Kaisers Einwand (2026-07-27): *"Was bringt uns die Warnung, was sollen wir daraus
schlussfolgern?"* — berechtigt. Eine Warnung, aus der keine Handlung folgt, ist nur eine
weitere Telegram-Nachricht; von denen haben wir mit den Derivate-Pump-Warnungen schon zu
viele. Als eigenständiges Signal daher VERWORFEN.

Stattdessen als Modus `high_exit="weak"` in Punkt 2 eingebaut: Der Teilverkauf am letzten
Hoch feuert dann NUR, wenn der Anlauf ohne steigendes Spot-CVD passiert. Damit wird aus
der Beobachtung eine Handlung, die der Backtest bewerten kann — und die Messung
beantwortet Kaisers Frage direkt: Bringt der Spot-Filter etwas gegenüber "immer am Hoch
verkaufen"? Beide Varianten stehen im Grid nebeneinander.

### Ursprüngliche Einordnung

Zitat 20:01–20:26: *"Short-Positionen werden liquidiert, Open Interest geht hoch und Spot
kann nicht mitziehen… Spot-Nachfrage Fehlanzeige, obwohl wir höhere Hochs hinlegen. **Bei
Breakouts müsste man spätestens da Spot-Nachfrage sehen.** Deswegen bin ich vorsichtig."*

Neu ist die Zuspitzung auf den **Breakout-Moment**: Ein neues höheres Hoch OHNE steigendes
Spot-CVD ist ein Warnsignal. Unsere `classify_pattern` prüft Spot-CVD über ein festes
Fenster, aber nicht gezielt beim Ausbruch über das letzte Pivot-Hoch.

**Baubar:** Warnung (oder Einstiegssperre) bei Bruch über das letzte Pivot-Hoch ohne
Spot-CVD-Anstieg. Alle Bausteine vorhanden.

## 5. Bestätigt, nicht neu: Makro zuerst

Die erste Videohälfte ist reine Makroanalyse (US-Firmenpleiten auf 16-Jahres-Hoch,
Hedgefonds-Verkäufe, Margin Debt zum BIP auf Hochpunkt, Staatsstützung in China,
Ölpreis/Iran, Zinsentscheidung). Das bestätigt die Hierarchie aus STRATEGIE.md §5 und
damit den pausierten Plan **E8.5 (KI-Makro-Bias)** — Richtung zuerst, Timing danach.
Bemerkenswert: Sein Makrobild ist vorsichtig, er ist aber trotzdem long positioniert.
Der Bias steuert bei ihm die GRÖSSE und die Aggressivität, nicht nur an/aus.

## Reihenfolge-Vorschlag

1. **Kapital-Reserve (1)** — billig, betrifft die Simulation, und beantwortet Kaisers
   offene Frage, ob wir realistisch rechnen. Zuerst.
2. **Verkauf unter dem letzten Hoch (2)** — billig, zielt genau auf unsere schwächste
   Kennzahl, hängt mit den Liquidationszonen zusammen.
3. **Breakout ohne Spot (4)** — billig, kleine Ergänzung.
4. **MVRV-Valuezone (3)** — erst Datenquelle recherchieren, dann entscheiden. Eigene
   Ebene, größerer Umbau.
