"""Sabotage-Probe fuer E44.2 (Wechselwirkungs-Tabelle und Monats-Probe), 26.09.2026.

Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Nie mitten im Lauf
abbrechen - die verfaelschte Datei wird erst am Ende jeder Sabotage wiederhergestellt.
Aufruf: python3 sabotage_e442.py
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    ("Wechselwirkung mit falschem Vorzeichen der Basis", "backtest.py",
     "    return round(ab - a - b + basis, 2)", "    return round(ab - a - b - basis, 2)"),
    ("Auch Zeilen mit zwei Unterschieden zaehlen als A", "backtest.py",
     "            if len(da) != 1:\n                continue", "            if not da:\n                continue"),
    ("Keine Ausrichtung auf die Aus-Ecke", "backtest.py",
     "                basis = grund[0] if grund else bl", "                basis = bl"),
    ("Gruppen werden mehrfach geliefert", "backtest.py",
     "                if gruppe in gesehen:\n                    continue", "                if False:\n                    continue"),
    ("Monats-Probe laesst den unguenstigsten statt den guenstigsten Monat weg", "backtest.py",
     "    krit = max(diffs, key=lambda m: diffs[m])", "    krit = min(diffs, key=lambda m: diffs[m])"),
    ("Monats-Probe prueft nur die Summe", "backtest.py",
     '            "haelt": ohne > 0}', '            "haelt": summe > 0}'),
    ("H1/H2-Spalten aus der falschen Haelfte", "backtest.py",
     "                h2 = e442_wechselwirkung(*[halb[l][1] for l in (bl, al, cl, abl)])",
     "                h2 = e442_wechselwirkung(*[halb[l][0] for l in (bl, al, cl, abl)])"),
    ("Abschnitt nicht im Bericht", "backtest.py",
     '        lambda: e442_abschnitt(results, halves, GRID, panel_cfg["label"]),',
     '        lambda: [],'),
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
