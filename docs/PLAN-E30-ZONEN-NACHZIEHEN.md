# E30 — Zonen einer laufenden Position nachziehen

Status: ABGESCHLOSSEN (05.09.2026) — Schalter ist LIVE

## Problem aus Kaisers Sicht

> "Ich finde es nicht logisch. Die Kauf und verkaufsbereiche richten sich nach
> Indikatoren, fib level etc. Wenn sich eine neue Struktur ergibt, dann dürften
> diese nicht festgefahren bleiben sondern sich ändern. Bei Furkan ändern sie
> sich doch auch, oder?"

Kaiser hat recht. Belege:

**1. Der Code friert die Zonen hart ein — ohne Schalter.**
`strategy_core.py` Zeile 974/975:
```python
elif pos.state != PosState.FLAT and pos.zones is not None:
    z = pos.zones
```
Alles danach — Kaufleiter, 0.786-Nachkauf, Teilgewinn-Level, Invalidierung —
liest aus `z`, also aus den Zonen des Einstiegsmoments. Der aktuelle Impuls
`imp` wird zwar jede Kerze neu berechnet (Zeile 789), bei offener Position aber
nur noch von `release_stale_rest` angesehen (und der Schalter ist aus und greift
ohnehin nur in TP1/TP2).

**2. Das widerspricht der eigenen Projektregel.**
Der Kommentar zu `release_stale_rest` sagt wörtlich:
"Deckt Grundregel 1 ab: Zonen sind dynamisch, nie starr."
Genau das gilt bei offener Position nicht.

**3. Es ist in sich asymmetrisch.**
Die *Ziele* wandern schon mit (`pos.retrace_extreme` läuft weiter, `ext_target`
rechnet daraus). Der *Stop* wandert schon mit (`trail_stop`). Nur die
*Kaufbereiche* stehen fest. Für diese Asymmetrie gibt es keine Begründung —
die dokumentierte Begründung (E18.3) richtete sich gegen Ziele, die mit jedem
neuen Tief nach unten rutschen, nicht gegen Zonen, die nach oben nachziehen.

**4. Furkan zieht nach.** Transkript 17:21 ff.: er zeichnet Retracement über die
jeweils aktuelle Konsolidierung ("wenn man hier eine Konsolidierung hat, man
zieht das hier von unten bis nach oben"). 17:52 ff.: "hier zwei Käufe und dann
zuletzt bei 82.000, wo ich danach dann die Position hochskaliert habe" — er
skaliert auf höherem Niveau nach, nicht nur in der Ursprungszone.

**Konkreter Schaden im Live-Fall vom 05.09.2026:**
Der Plan nennt eine Kaufleiter-Zone 75.546–78.409 $. Der nachgezogene Stop steht
bei 77.941 $. Der Teil der Zone unterhalb 77.941 ist tot — würde der Kurs
dorthin laufen, wäre die Position vorher gestoppt. Gleichzeitig hat sich eine
neue, höhere Struktur gebildet (76.264 → 82.300) mit Golden Pocket
78.377–78.570 $ — die die Engine nicht ansieht, weil sie noch auf die alte
schaut.

## Soll-Zustand

Neuer Schalter `zonen_nachziehen` (bool, Default **False**, wie jeder neue
Mechanismus im Projekt).

Ist er an, gilt bei offener Position vor jeder weiteren Auswertung:

- Liegt ein neuer bestätigter Impuls vor (andere start/end-Zeitstempel als
  `pos.zones.impulse`), **und**
- zeigt er in dieselbe Richtung wie das alte Bein, **und**
- setzt er den Trend intakt fort — bei Long: höheres Tief **und** höheres Hoch;
  bei Short: tieferes Hoch **und** tieferes Tief —

dann wird `pos.zones = fib_zones(neuer Impuls)` gesetzt.

Andernfalls bleibt alles wie bisher. Insbesondere: bricht die Struktur nach
unten, wird **nicht** nachgezogen. Die Engine kauft also keiner kaputten
Struktur hinterher, und der Stop kann durch das Nachziehen nur steigen, nie
lockerer werden (folgt aus "höheres Tief", da `invalidation = impuls.start`).

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `engine/strategy_core.py` | Helfer `trend_intakt(alt, neu)`; Parameter `zonen_nachziehen` in `evaluate()`; Nachzieh-Block direkt vor `z = pos.zones` (Zeile ~974) |
| `engine/test_strategy.py` | Test: zieht bei intaktem Trend nach; Gegenprobe: zieht bei gebrochener Struktur NICHT nach; Gegenprobe: erzeugt kein Kauf-/Verkauf-Karussell |
| `engine/main.py` | `EVAL_DEFAULTS` um `"zonen_nachziehen": False` |
| `engine/backtest.py` | Gittereintrag mit genau EINEM Unterschied zur Live-Zeile |
| `site/data/config.json` | erst nach Messung, falls die Zahlen dafür sprechen |

## Etappen

- **E30.1 — Kernlogik + Tests.** Schalter, Helfer, Nachzieh-Block, drei Tests
  inkl. Sabotage-Probe. Default aus, Live-Verhalten unverändert. Status: OFFEN
- **E30.2 — Messung.** Gitterzeile `LIVE-heute +Zonen nachziehen` mit genau einem
  Unterschied. Kennzahlen wie üblich: Rendite, max. Rückgang, Aufwärts-/
  Abwärts-Beteiligung, Gegengeschäfte, Signale. Dazu Robustheitsprüfung
  (Fensterhalbierung). **Status: FERTIG (05.09.2026, Bericht-Stand 15:40 UTC).**

  | | Rendite | max. Rückgang | Signale | Gegen&shy;geschäfte | Aufwärts | Abwärts |
  |---|---|---|---|---|---|---|
  | LIVE-heute +Neustart mit Rest (live) | +36,2 % | −9,7 % | 243 | **0** | 49 % | −17 % |
  | LIVE-heute +Zonen nachziehen | +37,2 % | −9,7 % | 251 | **1** | 54 % | −14 % |

  Robustheit (Fensterhalbierung): Live 1. Hälfte +22,5 % (Platz 35), 2. Hälfte
  +7,7 % (Platz 6). Nachziehen: +24,9 % (Platz 31) / +6,5 % (Platz 12). Uneindeutig
  — und der Bericht hält ohnehin fest, dass die Rangfolge bei 52 Varianten nicht
  über dem Zufallserwartungswert liegt und deshalb kein Beleg ist.

  **Belastbar** sind: der max. Rückgang (identisch, −9,7 %) und die
  Beteiligungspaare. Aufwärts steigt 49 → 54 %, während Abwärts sich von −17 auf
  −14 % VERBESSERT. Das ist die Kombination, die der Bericht selbst als "wirklich
  etwas gewonnen" definiert (steigt Aufwärts ohne dass Abwärts mitsteigt). Sie
  passt genau zur E26-Diagnose: die Engine war zu selten und zu klein investiert.

  **Mangel gefunden und behoben — siehe E30.2b.**

- **E30.2b — no_flip-Lücke beim Neustart mit Rest. FERTIG (05.09.2026).**

  Das 1 Gegengeschäft kam NICHT vom Nachziehen. Ursache: der `neustart_mit_rest`-
  Block (E21) läuft NACH dem Positions-Management im selben `evaluate()`-Aufruf
  und ruft `_versuche_einstieg()` auf, ohne `_darf_aufstocken()` zu fragen. In
  derselben Kerze konnten dadurch Teilgewinne (Leiter + Extension 1.0) und ein
  neuer KAUF 1 zusammenfallen. `no_flip` sicherte bis dahin nur die Nachkauf-Pfade.

  **Reproduziert, bevor etwas geändert wurde:** Suchlauf über konstruierte
  Kerzenfolgen; Kerze 9 liefert `{KAUF_1, TEILVERKAUF_LADDER, TEILVERKAUF_1}` —
  **mit UND ohne** `zonen_nachziehen`. Die Lücke betrifft also die heutige
  Live-Einstellung; dass die Live-Zeile im gemessenen Fenster 0 Gegengeschäfte
  zeigte, war Zufall, nicht Schutz.

  **Behebung:** `and _darf_aufstocken()` in die Bedingung des Neustart-Blocks.
  Der Neustart wird dadurch um eine Kerze verschoben, nicht verhindert.

  **Beleg:** Test `test_no_flip_deckt_auch_den_neustart_mit_rest_ab` schlug vor
  der Korrektur fehl (Gegengeschäft bei ts=9), danach grün. 165 Tests gesamt.
- **Nachmessung nach E30.2b — FERTIG (Bericht-Stand 05.09.2026, 21:50 UTC).**

  | | Rendite | max. Rückgang | Signale | Gegen&shy;geschäfte | Aufwärts | Abwärts |
  |---|---|---|---|---|---|---|
  | LIVE-heute +Neustart mit Rest (live) | +36,3 % | −9,7 % | 243 | 0 | 49 % | −17 % |
  | LIVE-heute +Zonen nachziehen | +36,4 % | −9,7 % | 249 | 0 | 52 % | −14 % |

  Der Fix wirkt: **0 Gegengeschäfte in beiden Zeilen.** Kaisers Vorgabe ist erfüllt.

  Der Rendite-Vorteil ist damit verschwunden (+0,1 statt vorher +1,0 Punkte) — das
  eine Gegengeschäft war also leicht renditewirksam. Was bleibt: Aufwärts 49 → 52 %
  bei gleichzeitig Abwärts −17 → −14 %. Beide Seiten besser, max. Rückgang und
  Rendite unverändert. Preis: 6 Signale mehr (249 statt 243).

  Robustheit weiterhin uneindeutig: 1. Hälfte +24,0 % (Platz 32) gegen +22,9 %
  (Platz 35), 2. Hälfte +6,5 % (Platz 12) gegen +7,8 % (Platz 6). Keine Variante
  liegt in beiden Hälften unter den besten 5 — die Rangfolge bleibt kein Beleg.

  Nebenwirkung des Fixes auf andere Zeilen: *LIVE-heute +Rest halten +Neustart mit
  Rest* fiel von +35,7 auf +33,9 % (Gegengeschäft 1 → 0). Die Live-Zeile selbst
  blieb praktisch unberührt (+36,2 → +36,3 %), was zu ihren 0 Gegengeschäften passt.

- **E30.3 — Entscheidung: LIVE. FERTIG (05.09.2026).** Kaiser hat den Schalter
  freigegeben. Umgesetzt: `zonen_nachziehen: true` in `site/data/config.json`
  (mit ausführlichem Hinweistext), `panel=True` von *LIVE-heute +Neustart mit Rest*
  auf *LIVE-heute +Zonen nachziehen* verschoben, damit der Chart die Rendite der
  tatsächlich gefahrenen Einstellung zeigt.

  Begründung fürs Protokoll: nicht die Rendite (+0,1 Punkte = nichts), sondern die
  Konstruktion. Ohne den Schalter rechnet die Engine mit Zonen, die der Markt
  hinter sich gelassen hat, und weist im Telegram-Plan Kaufmarken aus, die
  unterhalb des eigenen Stops liegen und damit unerreichbar sind. Der Backtest
  belegt, dass diese Korrektur nichts kostet.

  Gegenprobe bestanden: Setzt man den Schalter in `config.json` zurück auf false,
  während die Panel-Zeile stehen bleibt, schlägt
  `test_panel_variante_entspricht_der_live_einstellung` an. 165 Tests grün.
