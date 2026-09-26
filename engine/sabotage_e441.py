"""Sabotage-Probe fuer E44.1 (Coinalyze-Archiv), 26.09.2026.

Jede Zeile ist ein Fehler, der das Archiv still wirkungslos oder falsch machen wuerde.
Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Nie mitten im Lauf
abbrechen - die verfaelschte Datei wird erst am Ende jeder Sabotage wiederhergestellt.
Aufruf: python3 sabotage_e441.py
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    ("Alt gewinnt statt neu", "archiv.py",
     "    out = dict(alt or {})\n    out.update(neu or {})\n",
     "    out = dict(neu or {})\n    out.update(alt or {})\n"),
    ("Alte Zeitpunkte gehen verloren", "archiv.py",
     "    out = dict(alt or {})\n", "    out = {}\n"),
    ("Laufende Kerze wird mitgespeichert", "archiv.py",
     "if ts + KERZE_MS <= jetzt_ms}", "if ts <= jetzt_ms}"),
    ("Liquidationen kommen als Liste statt Tupel zurueck", "archiv.py",
     "(tuple(v) if isinstance(v, list) else v)", "v"),
    ("Kaputte Datei bricht ab", "archiv.py",
     "    except (FileNotFoundError, json.JSONDecodeError):",
     "    except FileNotFoundError:"),
    ("Backtest mischt das Archiv nicht", "backtest.py",
     '    m = archiv.mit_archiv(frisch, archiv_daten)\n',
     '    m = frisch\n'),
    ("Backtest ruft das Mischen im Hauptlauf nicht auf", "backtest.py",
     "        oi_map, liq_map, fut_map, ls_map, archiv.laden())",
     "        oi_map, liq_map, fut_map, ls_map, {})"),
    ("Zaehlung 'nur im Archiv' falsch", "backtest.py",
     'info = {"oi_nur_archiv": len(set(m["oi"]) - set(oi_map or {}))}',
     'info = {"oi_nur_archiv": len(m["oi"])}'),
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
