"""Sabotage-Probe fuer E38.1 (Muster-Nachlauf).

Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Jede Zeile hier
ist ein Fehler, den man beim Bauen wirklich machen koennte — und der die Zahlen im
Bericht still verfaelschen wuerde, statt zu krachen.
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    # --- Die Grundrate: ohne sie ist jede Musterzeile wertlos -------------------------
    ("Grundrate enthaelt nur einen Teil der Kerzen", "backtest.py",
     '        e["kerzen"] += 1\n        alle["kerzen"] += 1',
     '        e["kerzen"] += 1'),

    ("Grundrate bekommt die Werte nicht", "backtest.py",
     '            e[h].append(aend)\n            alle[h].append(aend)',
     '            e[h].append(aend)'),

    ("Abstand zur Grundrate wird nicht ausgewiesen", "backtest.py",
     '        return f"{roh} ({ab:+.2f} gg. Grundrate), {quote}"',
     '        return f"{roh}, {quote}"'),

    ("Abstand wird falsch herum gerechnet", "backtest.py",
     '        ab = (d["median"] - basis[h]["median"]) * 100',
     '        ab = (basis[h]["median"] - d["median"]) * 100'),

    # --- Der Nachlauf ------------------------------------------------------------------
    ("Kerzen ohne vollen Nachlauf werden mitgezaehlt", "backtest.py",
     '        if i + hmax >= len(candles):\n            break',
     '        if False:\n            break'),

    ("Jeder Horizont schneidet anders ab (Spalten unvergleichbar)", "backtest.py",
     '    hmax = max(horizonte)',
     '    hmax = min(horizonte)'),

    ("Kerzen vor dem Fensterstart werden gewertet", "backtest.py",
     '        if c.ts < start_ms:\n            continue',
     '        if False:\n            continue'),

    ("Nachlauf zeigt nach hinten statt nach vorn", "backtest.py",
     '            aend = (candles[i + h].close - c.close) / c.close',
     '            aend = (c.close - candles[i + h].close) / c.close'),

    # --- Episoden gegen Kerzen ---------------------------------------------------------
    ("Episoden zaehlen jede Kerze einzeln (Fallzahl erfunden)", "backtest.py",
     '        neu_begonnen = name != vorher   # neue Episode nur beim Wechsel',
     '        neu_begonnen = True'),

    ("Der Muster-Merker wird nie fortgeschrieben", "backtest.py",
     '        vorher = name\n        for h in horizonte:',
     '        for h in horizonte:'),

    # --- Median gegen Mittelwert -------------------------------------------------------
    ("Kernzahl ist der Mittelwert (ein Flush-Tag kippt die Zeile)", "backtest.py",
     '        return {"median": _med(werte),',
     '        return {"median": (sum(werte) / len(werte)) if werte else 0.0,'),

    ("Median nimmt bei gerader Anzahl den falschen Wert", "backtest.py",
     '    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0',
     '    return s[n // 2]'),

    # --- Die Warnungen, die vor einer Fehlentscheidung schuetzen -----------------------
    ("Warnung bei zu duenner Datenlage faellt weg", "backtest.py",
     '    if m5["episoden"] < MUSTER_MIN_EPISODEN:',
     '    if False:'),

    ("Mindestzahl auf 1 gesenkt (drei Ereignisse gelten als Beleg)", "backtest.py",
     'MUSTER_MIN_EPISODEN = 20',
     'MUSTER_MIN_EPISODEN = 1'),

    ("Fehlendes Muster 5 wird verschwiegen", "backtest.py",
     '    if not m5:\n        zeilen.append("Muster 5 kam im Fenster **kein einziges Mal**',
     '    if False:\n        zeilen.append("Muster 5 kam im Fenster **kein einziges Mal**'),

    ("Der Hinweis 'das ist keine Ertragsaussage' verschwindet", "backtest.py",
     '               "**Was diese Messung NICHT zeigt.** Sie misst den Kurs nach dem Muster, "\n'
     '               "nicht den Ertrag einer Regel.',
     '               "Sie misst den Kurs nach dem Muster, "\n'
     '               "und zwar den Ertrag einer Regel.'),

    # --- Der Abschnitt darf nicht lautlos verschwinden (Lehre aus E37.3) ---------------
    ("Leere Statistik liefert trotzdem eine Tabelle", "backtest.py",
     '    if not stat or "ALLE" not in stat:\n        return []',
     '    if False:\n        return []'),
]


def lauf():
    # __pycache__ leeren und Bytecode abschalten: sonst laedt Python bei
    # groessengleichen Aenderungen die ALTE .pyc und die Sabotage wirkt nicht.
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
