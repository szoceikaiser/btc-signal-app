"""Sabotage-Probe fuer E40.1 (STH-Kostenbasis: Gegenpruefung und Vorfrage, 21.09.2026).

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
    ("bitview um einen Tag verschoben", "backtest.py",
     'STH_BITVIEW_TAG0 = date(2009, 1, 1)',
     'STH_BITVIEW_TAG0 = date(2009, 1, 2)'),
    ("bitview ignoriert den Startindex", "backtest.py",
     '            out[STH_BITVIEW_TAG0 + timedelta(days=start + i)] = float(v)',
     '            out[STH_BITVIEW_TAG0 + timedelta(days=i)] = float(v)'),
    ("bitview behaelt Nullwerte", "backtest.py",
     '        if isinstance(v, (int, float)) and v > 0:',
     '        if isinstance(v, (int, float)):'),
    ("bitcoin-data: Text wird nicht in Zahlen gewandelt", "backtest.py",
     '        out = {date.fromisoformat(p["d"]): float(p["sthRealizedPrice"])',
     '        out = {date.fromisoformat(p["d"]): p["sthRealizedPrice"]'),
    ("bitcoin-data wird zweimal gefragt (Tageslimit)", "backtest.py",
     '    status, text, fehler = holen(STH_BGEOMETRICS)',
     '    holen(STH_BGEOMETRICS)\n    status, text, fehler = holen(STH_BGEOMETRICS)'),
    ("STH des selben Tages (kennt die Zukunft)", "backtest.py",
     '        v = sth.get(to_date(c.ts) - timedelta(days=1))',
     '        v = sth.get(to_date(c.ts))'),
    ("Abgleich waehlt den schlechtesten Versatz", "backtest.py",
     '    bester = min(je, key=lambda k: je[k]["median"])',
     '    bester = max(je, key=lambda k: je[k]["median"])'),
    ("Abgleich verschiebt in die falsche Richtung", "backtest.py",
     '        abw = [abs(a[t] - b[t + timedelta(days=k)]) / b[t + timedelta(days=k)]\n'
     '               for t in a if (t + timedelta(days=k)) in b]',
     '        abw = [abs(a[t] - b[t - timedelta(days=k)]) / b[t - timedelta(days=k)]\n'
     '               for t in a if (t - timedelta(days=k)) in b]'),
    ("Vorfrage: unter und ueber vertauscht", "backtest.py",
     '        g = "unter" if c.close < s else "ueber"',
     '        g = "ueber" if c.close < s else "unter"'),
    ("Vorfrage: Einstiegs-Nachlauf zeigt nach hinten", "backtest.py",
     '                einstiege[g][h].append((candles[i + h].close - preis) / preis)',
     '                einstiege[g][h].append((candles[i - h].close - preis) / preis)'),
    ("Vorfrage: Teilverkaeufe zaehlen als Einstieg", "backtest.py",
     '_STH_EINSTIEGE = ("KAUF_1", "KAUF_2", "NACHKAUF")',
     '_STH_EINSTIEGE = ("KAUF_1", "KAUF_2", "NACHKAUF", "TEILVERKAUF_1")'),
    ("Vorfrage: Wechsel werden nicht gezaehlt", "backtest.py",
     '        if vorher is not None and g != vorher:\n            wechsel += 1',
     '        if False:\n            wechsel += 1'),
    ("Vorfrage: Einstiege ohne Nachlauf zaehlen mit", "backtest.py",
     '            if i + hmax >= len(candles):\n                ohne_nachlauf += 1\n                continue\n            einstiege[g]["n"] += 1',
     '            if False:\n                ohne_nachlauf += 1\n                continue\n            einstiege[g]["n"] += 1'),
    ("Zweifelhafte Zuordnung wird nicht gemeldet", "backtest.py",
     '        if abgleich["bester_versatz"] != 0 or med0 > STH_ABGLEICH_MAX:',
     '        if False:'),
    ("Duenne Gruppen werden nicht gemeldet", "backtest.py",
     '    duenn = [g for g in ("unter", "ueber") if e[g]["n"] < STOP_MIN_FAELLE]',
     '    duenn = []'),
    ("Hinweis 'Nachlauf ist nicht Ertrag' verschwindet", "backtest.py",
     '    z += ["", "**Was diese Messung NICHT zeigt:** ob ein Schalter verdient. Nachlauf ist "',
     '    z += ["", "**Was diese Messung zeigt:** ob ein Schalter verdient. Nachlauf ist "'),
    ("Vorfrage misst die beste Variante statt live", "backtest.py",
     '            _sthvor = sth_vorfrage(candles, sth_je_kerze(candles, _sth), _psigs, eff_start)',
     '            _sthvor = sth_vorfrage(candles, sth_je_kerze(candles, _sth), sigs, eff_start)'),
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
