"""Sabotage-Probe fuer E38 Anzeige/Ampel (21.09.2026) und E39 (Stop-Nachlauf).

Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Jede Zeile hier
ist ein Fehler, den man beim Bauen wirklich machen koennte — und der die Engine still
anders handeln liesse, statt zu krachen.
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    # --- Ampel: Muster 5 neutral ---------------------------------------------------------
    ("Muster 5 zaehlt wieder GEGEN den Long", "strategy_core.py",
     '    "muster":   {"DERIVATE_PUMP", "SHORT_COVERING"},\n}',
     '    "muster":   {"DERIVATE_PUMP", "SHORT_COVERING", "UNGESUNDER_ABVERKAUF"},\n}'),

    ("Muster 5 zaehlt FUER den Long", "strategy_core.py",
     '    "muster":   {"GESUNDER_TREND", "CAPITULATION_RESET"},',
     '    "muster":   {"GESUNDER_TREND", "CAPITULATION_RESET", "UNGESUNDER_ABVERKAUF"},'),

    # --- Texte ---------------------------------------------------------------------------
    ("Alter, wertender Text kommt zurueck", "strategy_core.py",
     '    "UNGESUNDER_ABVERKAUF": ("Abverkauf mit neuen Short-Wetten - Kurs faellt, Spot wird "',
     '    "UNGESUNDER_ABVERKAUF": ("ungesunder Abverkauf mit neuen Short-Wetten - Kurs faellt, Spot wird "'),

    ("Name im Hinweis", "strategy_core.py",
     '    "UNGESUNDER_ABVERKAUF": ("Jan-Sep 2026 folgte darauf meist eine Gegenbewegung nach "',
     '    "UNGESUNDER_ABVERKAUF": ("Laut Furkan folgte Jan-Sep 2026 darauf meist eine Gegenbewegung nach "'),

    ("Hinweis behauptet einen offenen Zeitraum", "strategy_core.py",
     '    "UNGESUNDER_ABVERKAUF": ("Jan-Sep 2026 folgte darauf meist eine Gegenbewegung nach "\n'
     '                             "oben (1-4 Tage) - nicht immer."),',
     '    "UNGESUNDER_ABVERKAUF": ("Seit Januar 2026 folgte darauf meist eine Gegenbewegung "\n'
     '                             "nach oben (1-4 Tage) - nicht immer."),'),

    ("Hinweis verschweigt das 'nicht immer'", "strategy_core.py",
     '                             "oben (1-4 Tage) - nicht immer."),',
     '                             "oben (1-4 Tage)."),'),

    ("Hinweis erscheint bei jedem Muster", "strategy_core.py",
     '        if pattern.name in MUSTER_HINWEIS:\n            lage["muster_hinweis"] = MUSTER_HINWEIS[pattern.name]',
     '        if True:\n            lage["muster_hinweis"] = MUSTER_HINWEIS["UNGESUNDER_ABVERKAUF"]'),

    ("Lage-Abruf zeigt den Hinweis nicht", "telegram_notify.py",
     '            if feld == "muster_text" and lage.get("muster_hinweis"):',
     '            if False:'),

    ("Plan/Vorschau zeigen den Hinweis nicht", "telegram_notify.py",
     '        if lage.get("muster_hinweis"):\n            zeilen += _umbruch(lage["muster_hinweis"], einzug="         ")',
     '        if False:\n            zeilen += _umbruch(lage["muster_hinweis"], einzug="         ")'),

    ("Plan-Umbruch vergisst den Vorsatz (Zeilen zu lang)", "telegram_notify.py",
     '        for t in _umbruch("Muster: " + wert, breite=ZEILE_MAX - 7):',
     '        for t in _umbruch("Muster: " + wert):'),

    ("Woerter werden wieder am Bindestrich getrennt", "telegram_notify.py",
     'subsequent_indent=einzug, break_on_hyphens=False) or [""]',
     'subsequent_indent=einzug) or [""]'),

    # --- E39: die Messung ------------------------------------------------------------------
    ("Zaehlt jeden Ausstieg, nicht nur Stops", "backtest.py",
     '        if s.get("type") != "STOPLOSS":\n            continue\n        i = idx.get(s.get("ts"))',
     '        if s.get("type") not in ("STOPLOSS", "VERKAUF_REST", "TEILVERKAUF_1"):\n            continue\n        i = idx.get(s.get("ts"))'),

    ("Nachlauf zeigt nach hinten", "backtest.py",
     '                g[h]["aend"].append((candles[i + h].close - preis) / preis)',
     '                g[h]["aend"].append((candles[i - h].close - preis) / preis)'),

    ("Tiefster Punkt schliesst die Stop-Kerze ein", "backtest.py",
     '                tief = min(c.low for c in candles[i + 1:i + h + 1])',
     '                tief = min(c.low for c in candles[i:i + h + 1])'),

    ("Tiefster Punkt ist in Wahrheit der hoechste", "backtest.py",
     '                tief = min(c.low for c in candles[i + 1:i + h + 1])',
     '                tief = max(c.low for c in candles[i + 1:i + h + 1])'),

    ("Schlimmster Fall ist der Median", "backtest.py",
     '                    "tief_schlimmst": min(t)}',
     '                    "tief_schlimmst": _med(t)}'),

    ("Nachgezogene Stops gelten als Invalidierung", "backtest.py",
     '        art = ("nachgezogen" if str(s.get("reason", "")).startswith("Nachgezogener")',
     '        art = ("nachgezogen" if False'),

    ("Stops ohne vollen Nachlauf zaehlen mit", "backtest.py",
     '        if i + hmax >= len(candles):\n            ohne_nachlauf += 1\n            continue\n        muster = (classify_pattern(',
     '        if i + hmax >= len(candles) + 999:\n            ohne_nachlauf += 1\n            continue\n        muster = (classify_pattern('),

    ("Stops ohne Nachlauf verschwinden still", "backtest.py",
     '            ohne_nachlauf += 1\n            continue\n        muster = (classify_pattern(',
     '            continue\n        muster = (classify_pattern('),

    ("'wieder drueber' zaehlt auch Gleichstand", "backtest.py",
     '                    "wieder_drueber": sum(1 for v in a if v > 0) / len(a),',
     '                    "wieder_drueber": sum(1 for v in a if v >= 0) / len(a),'),

    ("Duenne Gruppen werden nicht markiert", "backtest.py",
     '        if key != "ALLE" and e["n"] < STOP_MIN_FAELLE:',
     '        if False:'),

    ("Warnung bei zu wenigen Stops faellt weg", "backtest.py",
     '    if alle["n"] < STOP_MIN_FAELLE:\n        z += ["", f"**Achtung, zu duenn:**',
     '    if False:\n        z += ["", f"**Achtung, zu duenn:**'),

    ("Der Lesehinweis 'wieder drueber heisst nicht ...' verschwindet", "backtest.py",
     '          "**Wie diese Tabelle NICHT zu lesen ist.** *Wieder drueber* heisst nicht, dass "\n'
     '          "Weitermachen sich gelohnt haette:',
     '          "*Wieder drueber* heisst, dass "\n'
     '          "Weitermachen sich gelohnt haette:'),

    ("Tiefster Punkt fehlt in der Zelle", "backtest.py",
     '        return (f"{d[\'median\'] * 100:+.2f} %, {d[\'wieder_drueber\']:.0%} drueber, "\n'
     '                f"tief {d[\'tief_median\'] * 100:+.1f} % ({d[\'tief_schlimmst\'] * 100:+.1f} %)")',
     '        return (f"{d[\'median\'] * 100:+.2f} %, {d[\'wieder_drueber\']:.0%} drueber")'),

    ("E39 misst die beste Variante statt der Live-Einstellung", "backtest.py",
     '        _stopstat = stop_nachlauf(candles, flow, _psigs)',
     '        _stopstat = stop_nachlauf(candles, flow, sigs)'),
]

def lauf():
    shutil.rmtree(ENG / "__pycache__", ignore_errors=True)
    umg = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run([sys.executable, "run_tests.py"], cwd=ENG, env=umg,
                       capture_output=True, text=True, timeout=600)
    letzte = [z for z in r.stdout.splitlines() if "passed" in z]
    return (letzte[-1] if letzte else "?"), r.stdout


signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError()))
ungefangen = []
for name, datei, alt, neu in SABOTAGEN:
    pfad = ENG / datei
    orig = pfad.read_text(encoding="utf-8")
    if alt not in orig:
        print(f"!! VORLAGE NICHT GEFUNDEN: {name}")
        ungefangen.append(name + " [Vorlage fehlt]")
        continue
    signal.alarm(700)
    try:
        pfad.write_text(orig.replace(alt, neu, 1), encoding="utf-8")
        zeile, voll = lauf()
        rot = [z.split("::")[-1] for z in voll.splitlines() if z.startswith("FAIL")]
        if rot:
            print(f"OK  {name}\n    -> {zeile}  | {', '.join(rot[:3])}")
        else:
            print(f"!!! UNGEFANGEN: {name}\n    -> {zeile}")
            ungefangen.append(name)
    finally:
        pfad.write_text(orig, encoding="utf-8")
        signal.alarm(0)

print("\n" + "=" * 60)
zeile, _ = lauf()
print("nach Wiederherstellung:", zeile)
print("ungefangen:", ungefangen or "keine")
