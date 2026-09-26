"""Sabotage-Probe fuer E43.4b (OI-Zeile im Lage-Abruf in Kontrakten, reine Anzeige),
26.09.2026.

Befund A3 in der Anzeige: Die OI-Zeile sagte "neues Geld kommt herein" bzw.
"Positionen werden geschlossen", wenn sich nur der Kurs bewegt hatte. Jede Zeile hier ist
ein Fehler, der diesen Satz still zurueckbringen oder eine Zahl falsch zeigen wuerde.

Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Nie mitten im Lauf
abbrechen - die verfaelschte Datei wird erst am Ende jeder Sabotage wiederhergestellt.
Aufruf: python3 sabotage_e434b.py
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    ("Richtung und Hinweis folgen doch dem Dollar", "strategy_core.py",
     '            richtung = kt["richtung"]\n', '            pass\n'),
    ("Pfeil folgt dem Dollar, Hinweis den Kontrakten", "strategy_core.py",
     '        zeilen.append({"name": "Open Interest", "wert": wert,\n'
     '                       "richtung": richtung, "hinweis": hin})',
     '        zeilen.append({"name": "Open Interest", "wert": wert,\n'
     '                       "richtung": oi["richtung"], "hinweis": hin})'),
    ("Kontrakt-Reihe liest doch das Dollar-OI", "strategy_core.py",
     "        kt = _of_reihe([p.oi_btc for p in flow], fenster)",
     "        kt = _of_reihe([p.oi for p in flow], fenster)"),
    ("Kontrakt-Prozent mit dem Stand am Fensterende als Nenner", "strategy_core.py",
     '            kt_pct = kt["aenderung"] / kt_davor * 100',
     '            kt_pct = kt["aenderung"] / flow[-1].oi_btc * 100'),
    ("Kurs-Bemerkung fehlt", "strategy_core.py",
     '        if richtung != oi["richtung"]:', '        if False:'),
    ("Kurs-Bemerkung vertauscht (Anstieg statt Rueckgang)", "strategy_core.py",
     '"steigt": " - der Dollar-Anstieg kommt nur vom Kurs"',
     '"steigt": " - der Dollar-Rueckgang kommt nur vom Kurs"'),
    ("Fall 'in Dollar verdeckt' fehlt", "strategy_core.py",
     '.get(\n                        oi["richtung"], " - in Dollar vom Kurs verdeckt")',
     '.get(\n                        oi["richtung"], "")'),
    ("Ohne Kontrakt-Reihe steht 'Kontrakte +0,0 %' (Stillstand behauptet)",
     "strategy_core.py",
     '        if kt and kt_davor:\n'
     '            kt_pct = kt["aenderung"] / kt_davor * 100\n'
     '            wert += f", Kontrakte {kt_pct:+.1f} %".replace(".", ",")\n'
     '            richtung = kt["richtung"]\n',
     '        if True:\n'
     '            kt_pct = (flow[-1].oi_btc - kt_davor) / kt_davor * 100 if kt_davor else 0.0\n'
     '            wert += f", Kontrakte {kt_pct:+.1f} %".replace(".", ",")\n'
     '            richtung = kt["richtung"] if kt else "flach"\n'),
    ("Hinweis-Texte vertauscht (steigt -> Positionen werden geschlossen)", "strategy_core.py",
     '        if richtung == "steigt":\n            hin = "neues Geld kommt herein"',
     '        if richtung == "steigt":\n            hin = "Positionen werden geschlossen"'),
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
