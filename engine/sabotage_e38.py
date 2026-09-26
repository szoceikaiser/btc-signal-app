"""Sabotage-Probe fuer E38.2 und E38.3 (Muster 5 als Treibstoff).

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
    # --- Der gefaehrlichste Fehler ueberhaupt: ein Stop wird zurueckgehalten ----------
    ("STOPLOSS zaehlt als Teilverkauf (Position bleibt im Fall liegen)",
     "strategy_core.py",
     '_TEILVERKAUF_TYPES = {SignalType.TEILVERKAUF_LADDER, SignalType.TEILVERKAUF_1,',
     '_TEILVERKAUF_TYPES = {SignalType.STOPLOSS, SignalType.VERKAUF_REST,\n'
     '                      SignalType.SHORT_STOPLOSS, SignalType.SHORT_COVER_REST,\n'
     '                      SignalType.TEILVERKAUF_LADDER, SignalType.TEILVERKAUF_1,'),

    # --- muster5_halten: der Schalter selbst -------------------------------------------
    ("Schalter wirkt auch im Default 'off'", "strategy_core.py",
     '    if modus == "off" or pattern != Pattern.UNGESUNDER_ABVERKAUF:\n        return False',
     '    if pattern != Pattern.UNGESUNDER_ABVERKAUF:\n        return False'),

    ("Schalter greift bei JEDEM Muster", "strategy_core.py",
     '    if modus == "off" or pattern != Pattern.UNGESUNDER_ABVERKAUF:',
     '    if modus == "off" or False:'),

    ("Schalter greift auf dem falschen Muster (4 statt 5)", "strategy_core.py",
     '    if modus == "off" or pattern != Pattern.UNGESUNDER_ABVERKAUF:',
     '    if modus == "off" or pattern != Pattern.CAPITULATION_RESET:'),

    ("Schalter greift auch beim Short", "strategy_core.py",
     '    if richtung != "LONG":\n        # Bei einem Short ist Liquiditaet oberhalb ein Grund, EHER zu decken, nicht',
     '    if False:\n        # Bei einem Short ist Liquiditaet oberhalb ein Grund, EHER zu decken, nicht'),

    ("'leiter' haelt auch die geplanten Ziele zurueck", "strategy_core.py",
     '    return modus == "alle" or not ziel',
     '    return True'),

    ("'alle' laesst die Ziele durch (wie 'leiter')", "strategy_core.py",
     '    return modus == "alle" or not ziel',
     '    return not ziel'),

    ("Waechter ruft die Regel gar nicht auf", "strategy_core.py",
     '        return not muster5_haelt_zurueck(muster5_halten, pattern, pos.direction, ziel)',
     '        return True'),

    ("no_flip-Pruefung faellt beim Umbau heraus", "strategy_core.py",
     '        if no_flip and any(x.type in _AUFBAU_TYPES for x in signals):\n            return False\n        return not muster5_haelt_zurueck(',
     '        if False:\n            return False\n        return not muster5_haelt_zurueck('),

    # --- Ziel-Markierung: leiter und alle muessen unterscheidbar bleiben ---------------
    ("Das 1.0-Ziel gilt nicht mehr als Ziel", "strategy_core.py",
     '                    and _darf_teilverkaufen(ziel=True):\n                hit1 = (cur.high >= ext1)',
     '                    and _darf_teilverkaufen():\n                hit1 = (cur.high >= ext1)'),

    ("Das 1.618-Ziel gilt nicht mehr als Ziel", "strategy_core.py",
     '            if pos.state == PosState.TP1 and _darf_teilverkaufen(ziel=True):',
     '            if pos.state == PosState.TP1 and _darf_teilverkaufen():'),

    ("Die Leiter wird faelschlich als Ziel gefuehrt", "strategy_core.py",
     '                    and pos.tp_rungs < len(LADDER_FACTORS) and _darf_teilverkaufen():',
     '                    and pos.tp_rungs < len(LADDER_FACTORS) and _darf_teilverkaufen(ziel=True):'),

    ("Der Teilverkauf am letzten Hoch gilt als Ziel", "strategy_core.py",
     '                    and pos.state in (PosState.T1, PosState.CORE, PosState.FULL) \\\n'
     '                    and _darf_teilverkaufen():\n                ref = candles[-2].close',
     '                    and pos.state in (PosState.T1, PosState.CORE, PosState.FULL) \\\n'
     '                    and _darf_teilverkaufen(ziel=True):\n                ref = candles[-2].close'),

    # --- muster5_entry ------------------------------------------------------------------
    ("Muster 5 bestaetigt Kaeufe auch im Default 'aus'", "strategy_core.py",
     '        strong = pattern == Pattern.CAPITULATION_RESET or (\n'
     '            muster5_entry and pattern == Pattern.UNGESUNDER_ABVERKAUF)',
     '        strong = pattern == Pattern.CAPITULATION_RESET or (\n'
     '            pattern == Pattern.UNGESUNDER_ABVERKAUF)'),

    ("Muster 4 faellt aus der starken Bestaetigung heraus", "strategy_core.py",
     '        strong = pattern == Pattern.CAPITULATION_RESET or (\n'
     '            muster5_entry and pattern == Pattern.UNGESUNDER_ABVERKAUF)',
     '        strong = (muster5_entry and pattern == Pattern.UNGESUNDER_ABVERKAUF)'),

    # --- Durchreichen: ein Schalter, der nirgends ankommt ------------------------------
    ("muster5_entry steht nicht in EVAL_KEYS (Gitterzeile = Kopie der Basis)",
     "backtest.py",
     '             "block_unhealthy", "muster5_entry", "muster5_halten",',
     '             "block_unhealthy", "muster5_halten",'),

    ("muster5_halten steht nicht in EVAL_KEYS", "backtest.py",
     '             "block_unhealthy", "muster5_entry", "muster5_halten",',
     '             "block_unhealthy", "muster5_entry",'),

    ("Live-Engine reicht die Schalter nicht durch", "main.py",
     '    "muster5_entry": False, "muster5_halten": "off",',
     '    "muster5_halten": "off",'),

    ("Live-Engine bekommt einen anderen Vorgabewert", "main.py",
     '    "muster5_entry": False, "muster5_halten": "off",',
     '    "muster5_entry": True, "muster5_halten": "off",'),

    # --- Die Gitterzeilen ---------------------------------------------------------------
    ("Eine E38-Zeile weicht in einem zweiten Punkt ab", "backtest.py",
     '    V("LIVE-heute +Muster 5 als Kauf-Bestaetigung",\n'
     '      bias_short=False, flush_entry="core",',
     '    V("LIVE-heute +Muster 5 als Kauf-Bestaetigung",\n'
     '      bias_short=False, flush_entry="off",'),

    ("Beide Halten-Zeilen messen dasselbe", "backtest.py",
     '      bein_richtung="bias", muster5_halten="alle"),',
     '      bein_richtung="bias", muster5_halten="leiter"),'),

    ("Die Gegenprobe (Bremse) verschwindet aus dem Gitter", "backtest.py",
     'V("LIVE-heute +Muster 5 sperrt Kaeufe (Bremse, Gegenprobe)"',
     'V("LIVE-heute +Muster 5 sperrt Kaeufe (UMBENANNT)"'),

    # --- E38.1: die Episoden-Gegenprobe --------------------------------------------------
    ("Episoden-Gegenprobe nimmt doch alle Kerzen", "backtest.py",
     '            if neu_begonnen:\n                e["ep"][h].append(aend)',
     '            if True:\n                e["ep"][h].append(aend)'),

    ("Gegenprobe zeigt die Kerzen- statt der Episodenzahl", "backtest.py",
     '        zeilen.append(f"| {name} | {e[horizonte[0]][\'n\']} | {zellen} |")',
     '        zeilen.append(f"| {name} | {stat[name][\'kerzen\']} | {zellen} |")'),
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
