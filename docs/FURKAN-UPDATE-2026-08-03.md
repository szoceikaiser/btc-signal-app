# Auswertung: Furkan-Update vom 03.08.2026

Quelle: `Videos/260803/260803_Transkript.txt` (13 Min) · ausgewertet 2026-08-27.
Das Video ist überwiegend Nachrichtenlage (Strategy-Verkauf, Trump Media, Clarity Act,
Wallet-Hack). Handelsrelevant ist ein einziger Abschnitt — der hat es aber in sich.

## 1. Er arbeitet mit einem PLAN, nicht mit Einzelsignalen (2:28–3:24)

Wörtlich, in einer Minute nennt er **vier Preismarken im Voraus**:

> „Meine kurzfristige Future-Position hat Average Entry bei 59.700. Ich habe zweimal schon
> Gewinne realisiert. **Plan ist es**, falls wir runterfallen sollten **zwischen 61.300 und
> 61.000**, da werde ich die Position noch mal aufstocken. Wenn wir weiter nach oben gehen
> sollten, werde ich **weitere Gewinne realisieren, vor allem unter der 67.000-Dollar-Marke**."

> „Die ersten wichtigen Bereiche in dieser Gegenbewegung wird natürlich das **Golden Pocket**
> sein. **64.200 bis 64.300** US-Dollar. Da könnte Widerstand vorherrschen. Idealerweise
> kommen wir hier drüber […] sodass wir dieses **Hoch vom Juni** wieder angreifen können.
> Also dieses Hoch von **67.200**."

Das ist genau das Format, das Kaiser vorgeschlagen hat: **wo kaufe ich nach, wo nehme ich
Gewinne mit, wo liegt der Widerstand, wo der Stop** — alles vorab, an festen Kursen, als
Limit-Order platzierbar. Er verschickt keine Einzelmeldungen an sich selbst, er hat einen
Plan und arbeitet ihn ab. Erst wenn sich die Struktur ändert, ändert sich der Plan.

**Konsequenz für unsere App:** Unsere Signale kommen nach Kerzenschluss und nennen einen
Preis, den es zu dem Zeitpunkt oft nicht mehr gibt (gemessen in E17: 61 von 214 Signalen
betroffen, Median 0,35 % Abstand). Die Vorschau-Nachricht (2026-07-29) löst das für die
EINSTIEGE. Für die AUSSTIEGE gibt es bisher nichts Vergleichbares.

## 2. Unsere Engine hat exakt dieselbe Zone gerechnet wie er — und sie nur anders benutzt

Er nennt am 03.08. das Golden Pocket der Gegenbewegung mit **64.200 bis 64.300**.
Unsere Engine hatte am Vorabend (Repo-Stand `d023500`, 02.08.2026 20:50 UTC) in der
Vorschau stehen:

```
"richtung": "SHORT", "impuls_start": 65409.56, "impuls_ende": 62275.0,
"gp_upper": 64212.16, "gp_lower": 64312.46
```

**64.212 bis 64.312 gegen seine 64.200 bis 64.300 — zwölf Dollar Unterschied.**
Die Engine hat also nicht falsch gerechnet. Sie hat dieselbe Struktur gesehen wie er.

Der Unterschied liegt allein in der **Verwendung**: Für ihn ist diese Zone eine
**Widerstandsmarke**, die seinem laufenden Long im Weg steht („da könnte Widerstand
vorherrschen"). Unsere Engine wollte daraus ein **Short-Setup** machen — und durfte es bei
`bias_short=false` nicht handeln, also stand sie still.

**Das ist der dritte Beleg für E19 und er verschiebt die Lösung:** `bein_richtung="bias"`
(nur Beine in Handelsrichtung suchen) wirft das Gegen-Bein weg. Furkan wirft es nicht weg,
er benutzt es anders. Die vollständige Umsetzung ist der **zweite Zonensatz**
(STRATEGIE.md §4.1 Punkt 4): das Bein in Handelsrichtung für Einstiege, das Gegen-Bein für
Widerstand und Teilgewinne.

## 3. Break-even-Stop bei Aufstockung — dritter Beleg (3:33)

> „Wenn ich wirklich noch mal die Position aufstocken sollte in diesem Bereich von 61.000,
> dann werde ich meinen **Stop natürlich auch wieder auf den neuen Entry rüberziehen**,
> sodass ich da keine Verluste mehr mit dieser Position machen kann."

Damit ist die Regel dreimal belegt (Video B 18:50, 02.08. 16:07, jetzt 03.08. 3:33).
**Gemessen ist sie trotzdem der teuerste Hebel des Projekts** (`be_im_plus`: +15,9 % gegen
+35,4 %, siehe E19). Kein Widerspruch, sondern ein Unterschied im Kontext: Er zieht den
Stop auf den Einstand einer Position, die er **diskretionär und selten** führt (1,8
Positionen im Monat). Unsere Engine handelt das Vierfache; bei ihr schneidet dieselbe Regel
die Gewinner ab, bevor sie laufen. **Bleibt aus — aber der Grund gehört notiert, damit die
Regel nicht ein viertes Mal als „neue Idee" auftaucht.**

> **Berichtigt 26.09.2026 (E43.7, Gesamtprüfung Teil B Punkt 7):** Lesefehler. `be_im_plus` ist **nicht** Furkans Regel — ihm fehlt die Vorbedingung „Gewinne schon realisiert“. Furkans Regel entspricht `trail_stop` (live). Auf der heutigen Live-Basis gemessen (E43.8): `be_im_plus` +18,0 % gegen +35,3 %. Siehe `wissens-layer\02_status\GEMESSEN-UND-ENTSCHIEDEN.md`.

## 4. Nichts Neues, aber bestätigt

- Nachkaufzone weiterhin 61.300–61.000 (unverändert gegenüber dem 02.08.) — das Golden
  Pocket des Beins 57.802 → 66.940, siehe `FURKAN-UPDATE-2026-08-02.md`.
- Spot-Nachfrage kam am 03.08. kurz zurück (2:02–2:19, „die Steigung deutlich steiler")
  — für ihn Bestätigung, keine Handlungsregel.
- Trendbeschreibung „tiefer werdende Tiefs und tiefer werdende Hochs" (2:56): genau das,
  was unsere Swing-Erkennung ohnehin misst.

## 5. Was daraus zu bauen wäre

1. **Ausstiegs-Plan per Telegram** (Kaisers Vorschlag, von diesem Video gestützt): eine
   Nachricht, die bei offener Position ALLE geplanten Marken nennt — Teilgewinn-Stufen,
   Extension-Ziele, Widerstand am letzten Hoch, Nachkaufzonen, Stop. Neu gesendet nur, wenn
   sich eine Marke ändert. Damit lassen sich auch die Ausstiege als Limit-Order vorlegen,
   statt einer Nachricht hinterherzulaufen.
2. **Zweiter Zonensatz** (§4.1 Punkt 4, jetzt dreifach belegt): Gegen-Bein als
   Widerstandsmarke führen, statt es wegzuwerfen oder daraus einen unhandelbaren Trade zu
   machen.
