"""Sabotage-Probe fuer E40.0 (STH-Probe, 21.09.2026).

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
    ("BGeometrics wird immer zweimal gefragt (Tageslimit!)", "backtest.py",
     '        if _merke("bitcoin-data.com", url)["status"] == 200:\n            break',
     '        if _merke("bitcoin-data.com", url)["status"] == 999:\n            break'),

    ("Suche nimmt jede Preisreihe, nicht nur STH", "backtest.py",
     '        if "sth" in t and ("price" in t or "realized" in t):',
     '        if "price" in t or "realized" in t:'),

    ("Ohne Suchtreffer wird ein Name geraten", "backtest.py",
     '    if namen:\n        import urllib.parse',
     '    if True:\n        namen = namen or ["sth_realized_price"]\n        import urllib.parse'),

    ("Rohantwort ungekuerzt im Bericht", "backtest.py",
     '             "roh": (text or "")[:STH_ROH_MAX]}',
     '             "roh": (text or "")}'),

    ("Codeblock im Bericht kann aufbrechen", "backtest.py",
     '            z += ["", "```", e["roh"].replace("```", "\'\'\'"), "```"]',
     '            z += ["", "```", e["roh"], "```"]'),

    ("Letzter Punkt ist in Wahrheit der erste", "backtest.py",
     '        info["erster"], info["letzter"] = liste[0], liste[-1]',
     '        info["erster"], info["letzter"] = liste[0], liste[0]'),

    ("CSV wird nicht erkannt", "backtest.py",
     '        if len(zeilen) > 1 and "," in zeilen[0]:',
     '        if False:'),

    ("Fehler werden nicht in den Bericht geschrieben", "backtest.py",
     "            z.append(f\"- **keine brauchbare Antwort:** {e.get('fehler') or 'Status ' + str(e.get('status'))}\")",
     '            pass'),

    ("Probe ist nicht im Bericht verdrahtet", "backtest.py",
     '        lambda: sth_probe_abschnitt(_sthprobe),',
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
