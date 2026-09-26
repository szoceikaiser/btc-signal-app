"""Sabotage-Probe fuer E43.5 (Test "mehr Historie" erreicht Muster 2) und E43.3
(Muster 2 in Dollar, Schalter muster_cvd), 26.09.2026.

Befunde A2 und A4 der Gesamtpruefung (docs/PRUEFUNG-2026-09-26-GESAMT.md). Jede Zeile
hier ist ein Fehler, den man beim Bauen wirklich machen koennte - und der entweder den
Befund still wieder verdecken oder die neue Rechnung still falsch machen wuerde.

Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Nie mitten im Lauf
abbrechen - die verfaelschte Datei wird erst am Ende jeder Sabotage wiederhergestellt.
Aufruf: python3 sabotage_e433.py
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    # --- E43.5: der Test selbst -------------------------------------------------------
    ("Test schneidet wieder EINE vorgerechnete Summe aus", "test_strategy_core.py",
     "    for i in range(aus, bis):\n        sd, fd, oi, fu = roh[i]\n"
     "        spot += sd\n        fut += fd\n"
     "        out.append(FlowPoint(kerzen[i].ts, spot, fut, oi, fu))",
     "    for i in range(0, bis):\n        sd, fd, oi, fu = roh[i]\n"
     "        spot += sd\n        fut += fd\n        if i >= aus:\n"
     "            out.append(FlowPoint(kerzen[i].ts, spot, fut, oi, fu))"),
    ("Szenario ohne Pump-Phase", "test_strategy_core.py",
     "PUMP_ZYKLUS, PUMP_AB, PUMP_BIS = 36, 20, 32",
     "PUMP_ZYKLUS, PUMP_AB, PUMP_BIS = 36, 20, 20"),
    ("Szenario mit zu schwachem OI-Anstieg (wie der alte Test)", "test_strategy_core.py",
     "        oi = 1e9 * (1 + 0.006 * (min(ph, PUMP_BIS - 1)",
     "        oi = 1e9 * (1 + 0.0006 * (min(ph, PUMP_BIS - 1)"),
    # --- E43.5: der Code, den der Befund-Test festhaelt -------------------------------
    ("_slope ohne Division (alt rechnet nicht mehr wie bisher)", "strategy_core.py",
     "    return (vals[-1] - vals[0]) / abs(vals[0])",
     "    return (vals[-1] - vals[0])"),
    ("Muster 2 unerreichbar (OI-Schwelle zehnfach)", "strategy_core.py",
     "        if (price_chg > 0 and fut > 0 and spot <= fut / 3 and oi_chg >= 0.03",
     "        if (price_chg > 0 and fut > 0 and spot <= fut / 3 and oi_chg >= 0.3"),
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
