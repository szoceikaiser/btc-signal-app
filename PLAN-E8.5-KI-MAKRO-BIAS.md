# Plan / Erkundungsstand: KI-Makro-Bias (E8.5, Stufe 2)

Stand: 2026-07-24 · Status: **NUR ERKUNDET, NOCH NICHT GEBAUT** (kein Code angelegt).
Kaiser hat die Umsetzung pausiert, um zuerst an etwas anderem weiterzuarbeiten.
Diese Datei hält den kompletten Denkstand fest, damit die Umsetzung später (auch in
einer anderen Umgebung wie Cowork) ohne Neu-Recherche fortgesetzt werden kann.

## Warum das (Motivation, belegt)

Erneute Transkript-Lesung (16:03–19:41) + Kaisers Order-Analyse zeigen: Furkan
entscheidet die **Richtung (long/short) zuerst aus MAKRO** (*"damit ich überhaupt meinen
Bias habe: gehe ich eher long oder short"*), erst danach Orderflow + Fib nur zum **Timing
des Einstiegs** auf der gewählten Seite. In Kaisers Zeitraum war der Bias praktisch immer
LONG (seine "Verkäufe" waren Long-Schließungen/Teilgewinne, KEINE Shorts).

Unsere Engine hat diese erste Stufe bisher nicht — sie leitet die Richtung nur aus dem
letzten Swing-Impuls ab und erzeugt so Shorts, die Furkan nie handelte.

**Backtest-Beleg (2026-07-24, BACKTEST.md, Auswahl nach Rendite):** long-only schlägt
long+short bei jeder pivot_n-Einstellung; bei n=4/5/6 kippt es von Verlust in Gewinn.
Bei n=5: Long+Short −5,3 % vs. nur Long +2,5 %. Bei n=4: −4,3 % vs. +3,6 %. (Der
n=6-Ausreißer +16,3 % ist fragil — nur 16 % Recall = wenige, glückliche Treffer; nicht
darauf verlassen.) Buy&Hold im Zeitraum: −28,4 %.

Fazit: Wenn der Richtungs-Bias stimmt, wird die Strategie profitabel. Genau diesen Bias
soll die KI-Stufe liefern — **dynamisch** (mal long, mal short, je nach Makro), NICHT fest
verdrahtet (fest long wäre in einem echten Abwärtsmarkt gefährlich).

## Gewählter Ansatz

Von Kaiser gewählt: **KI-Makro-Bias** (statt des einfacheren mechanischen EMA200-Filters).
Eine tägliche KI-Stufe, die Makro/News liest und long/short/neutral setzt — am nächsten
an Furkans echtem Vorgehen. Kaiser hat "API-Key/Kosten, nicht deterministisch, mehr
Testaufwand" akzeptiert.

## Designentscheidungen (mit claude-api-Skill geprüft)

- **Modell:** `claude-opus-4-8` (bestes Urteil; ~1 Aufruf/Tag ≈ wenige Cent/Monat,
  vernachlässigbar).
- **Kein SDK / kein pip:** Das Modul ruft die Claude-API per `urllib` (Raw-HTTP an
  `POST https://api.anthropic.com/v1/messages`) auf — genau wie der bestehende
  Telegram-/Börsen-Code. Grund: Die ganze Engine ist bewusst stdlib-only; die
  Sandbox-Tests laufen OHNE PyPI, ein `import anthropic` würde sie brechen. Bewusste
  Abweichung vom SDK-Default des Skills.
- **Datenbeschaffung über Claudes `web_search`-Servertool:** Claude liest die *aktuelle*
  Makro-Lage selbst (Zinsen, S&P 500, DXY, BTC-Trend/News) statt eigener fragiler
  Scraper. Robuster und näher an Furkan. `pause_turn` im Loop behandeln (Message +
  Antwort erneut senden, bis `end_turn`; kein "Continue"-Text anhängen).
- **Structured Output** (`output_config: {format: {type:"json_schema", schema:{…}}}`):
  `{ bias: "long"|"short"|"neutral", confidence: "low"|"medium"|"high",
     reasoning: string (≤500 Zeichen), key_factors: string[] }`.
  Beim Parsen den **Text-Block** suchen (`type=="text"`), NICHT `content[0]` —
  adaptive thinking legt evtl. thinking-Blöcke davor. Dann `json.loads`.
- **Request-Parameter:** `model="claude-opus-4-8"`, `thinking={"type":"adaptive"}`,
  `tools=[{"type":"web_search_20260209","name":"web_search"}]`, `max_tokens` großzügig
  (z. B. 4000), `output_config.format` wie oben. Header: `x-api-key`,
  `anthropic-version: 2023-06-01`. Server-Tools laufen serverseitig — nur deklarieren.
- **Bias → Schalter:** long = (bias_long=True, bias_short=False); short = (False, True);
  neutral = (True, True).

## Geplante Bausteine

**Increment 1 (Kern, offline testbar):**
1. `engine/macro_bias.py` — stdlib. Baut Request, ruft Claude (Transport injizierbar für
   Tests), parst Bias, schreibt `site/data/macro_bias.json`:
   `{ generated_at, bias, confidence, reasoning, key_factors, bias_long, bias_short }`.
   `main()` liest `ANTHROPIC_API_KEY` aus der Umgebung.
2. `main.py`-Integration: liest `site/data/macro_bias.json`. **Vorrang:** wenn state.json
   `config.bias_mode == "manual"` → manuelle Schalter aus state.json; sonst (Default
   `"auto"`) die Makro-Flags. Fällt macro_bias.json/Datei weg → Default beide True.
3. `.github/workflows/macro.yml` — Cron 1×/Tag (z. B. `0 6 * * *`), führt
   `python engine/macro_bias.py` aus, committet `site/data/macro_bias.json`.
   Braucht GitHub-Secret **`ANTHROPIC_API_KEY`**.
4. `engine/test_macro_bias.py` — offline, Fake-Transport (kein Netz, kein anthropic-Paket):
   bias→flags, extract_bias aus Fake-Message mit thinking+text-Blöcken, pause_turn-Loop,
   run() schreibt korrektes JSON, Vorrang-Logik.
5. `ANLEITUNG-KI-MAKRO.md` (Muster wie andere ANLEITUNG-*.md, mit Kontrollpunkten):
   Anthropic-API-Key holen → als GitHub-Secret `ANTHROPIC_API_KEY` hinterlegen →
   Workflow aktivieren/erst manuell testen → Kosten (~Cent/Tag) → Wirkung → Override
   (`bias_mode: "manual"` in state.json).

**Increment 2 (Sichtbarkeit, später):**
6. Website-Panel in `site/index.html`: aktuellen Bias + Begründung anzeigen (Furkan:
   "ich sage euch meinen Bias"). Liest `site/data/macro_bias.json`.
7. Telegram-Nachricht bei **Bias-Wechsel** (long↔short↔neutral).

## Ehrlichkeitshinweis (Regel 3 — Recall/Gewinn trennen, keine Versprechen)

Der KI-Makro-Bias ist **kaum backtestbar**: historische News/LLM-Aufrufe lassen sich nicht
sauber nachspielen. Er ist ein **Vorwärts-Feature**, das man live validiert — anders als
der mechanische EMA200-Filter, den man historisch durchrechnen könnte. Kein
Gewinnversprechen; Furkan selbst betont Wahrscheinlichkeiten und News-Risiko
(*"ein schlechter Tweet von Trump und der Markt stürzt ein"*).

## So geht's weiter (Wiedereinstieg)

Zuerst `docs/ETAPPENPLAN.md` (Statusquelle) und diese Datei lesen. Dann Increment 1 in der
Reihenfolge 1→5 bauen, Tests grün halten
(`cd engine && PYTHONIOENCODING=utf-8 python run_tests.py`). Danach Kaiser die Anleitung
für den API-Key geben; er pusht selbst und richtet das Secret ein.
