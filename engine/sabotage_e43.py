"""Sabotage-Probe fuer E43.1 (Futures-CVD im Lage-Abruf in Dollar) und E43.2
(Gitterzeile "Bein in Handelsrichtung"), 26.09.2026.

Befund A1 der Gesamtpruefung (docs/PRUEFUNG-2026-09-26-GESAMT.md): fut_cvd kommt in BTC,
wurde aber als Dollar angezeigt. Jede Zeile hier ist ein Fehler, den man beim Bauen
wirklich machen koennte - und der die Anzeige still wieder falsch machen wuerde.

Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Nie mitten im Lauf
abbrechen - die verfaelschte Datei wird erst am Ende jeder Sabotage wiederhergestellt.
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    ("Anzeige nimmt wieder die BTC-Reihe", "strategy_core.py",
     '    fu = _of_reihe(_fut_cvd_usd(candles, flow), fenster)',
     '    fu = _of_reihe([p.fut_cvd for p in flow], fenster)'),
    ("Delta wird nicht mit dem Kurs multipliziert", "strategy_core.py",
     '        summe += (p.fut_cvd - vorher) * k',
     '        summe += (p.fut_cvd - vorher)'),
    ("ein einziger Kurs fuer die ganze Reihe", "strategy_core.py",
     '        summe += (p.fut_cvd - vorher) * k',
     '        summe += (p.fut_cvd - vorher) * candles[-1].close'),
    ("kumulierter Wert statt Delta", "strategy_core.py",
     '        vorher = p.fut_cvd\n        out.append(summe)',
     '        out.append(summe)'),
    ("fehlende Kerze wird mit Ersatzkurs gerechnet", "strategy_core.py",
     '        k = kurs.get(p.ts)\n        if k is None:',
     '        k = kurs.get(p.ts, 80000.0)\n        if k is None:'),
    # --- E43.2: die Gitterzeile "LIVE-heute +Bein in Handelsrichtung" -----------------
    ("Gitterzeile misst nichts (auto statt bias)", "backtest.py",
     'stop_rueckeroberung=1,\n      bein_richtung="bias"),',
     'stop_rueckeroberung=1,\n      bein_richtung="auto"),'),
    ("Gitterzeile mit zweitem Unterschied (alter Stop)", "backtest.py",
     'stop_rueckeroberung=1,\n      bein_richtung="bias"),',
     'stop_rueckeroberung=0,\n      bein_richtung="bias"),'),
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
