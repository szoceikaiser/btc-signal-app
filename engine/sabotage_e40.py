"""Sabotage-Probe fuer E40.1 (STH-Kostenbasis: Gegenpruefung und Vorfrage, 21.09.2026)
und die STH-Zeile im Lage-Abruf (ebenfalls 21.09.2026).

Die Abruf-Funktionen stehen seit der Lage-Zeile in main.py (Backtest UND Abruf nutzen sie).

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
    ("bitview um einen Tag verschoben", "main.py",
     'STH_BITVIEW_TAG0 = date(2009, 1, 1)',
     'STH_BITVIEW_TAG0 = date(2009, 1, 2)'),
    ("bitview ignoriert den Startindex", "main.py",
     '            out[STH_BITVIEW_TAG0 + timedelta(days=start + i)] = float(v)',
     '            out[STH_BITVIEW_TAG0 + timedelta(days=i)] = float(v)'),
    ("bitview behaelt Nullwerte", "main.py",
     '        if isinstance(v, (int, float)) and v > 0:',
     '        if isinstance(v, (int, float)):'),
    ("bitcoin-data: Text wird nicht in Zahlen gewandelt", "main.py",
     '        out = {date.fromisoformat(p["d"]): float(p["sthRealizedPrice"])',
     '        out = {date.fromisoformat(p["d"]): p["sthRealizedPrice"]'),
    ("bitcoin-data wird zweimal gefragt (Tageslimit)", "main.py",
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
    # --- STH-Kostenbasis als Zeile im Lage-Abruf (Kaiser 21.09.2026) --------------------
    ("Abruf: nimmt den AELTESTEN statt den juengsten Wert", "main.py",
     '            tag = max(werte)',
     '            tag = min(werte)'),
    ("Abruf: keine zweite Quelle", "main.py",
     '    for quelle, abruf in (("bitview.space", sth_bitview),\n'
     '                          ("bitcoin-data.com", sth_bgeometrics)):',
     '    for quelle, abruf in (("bitview.space", sth_bitview),):'),
    ("Abruf: Ausfall der ersten Quelle reisst alles mit", "main.py",
     '        try:\n            werte, _fehler = abruf(holen)\n        except Exception:  # noqa: BLE001\n            werte = {}',
     '        if True:\n            werte, _fehler = abruf(holen)\n        if False:\n            werte = {}'),
    ("Lage-Abruf: STH-Fehler bricht den ganzen Abruf ab", "main.py",
     '    try:\n        out["sth"] = sth()\n',
     '    out["sth"] = sth()\n    try:\n        pass\n'),
    ("Lage-Abruf: STH wird nie eingetragen", "main.py",
     '        out["sth"] = sth()\n',
     '        out["sth"] = None\n'),
    ("Lage-Abruf: holt die STH im Normalfall nicht", "main.py",
     '               dry_run: bool = False, sth=sth_kostenbasis) -> dict | None:',
     '               dry_run: bool = False, sth=lambda: None) -> dict | None:'),
    ("Nachricht: STH-Zeile fehlt", "telegram_notify.py",
     '    zeilen += _sth_zeilen(l.get("sth"), l["kurs"])\n',
     ''),
    ("Nachricht: darueber und darunter vertauscht", "telegram_notify.py",
     '    seite = "darueber" if abstand >= 0 else "darunter"',
     '    seite = "darunter" if abstand >= 0 else "darueber"'),
    ("Nachricht: Abstand gegen den Kurs statt gegen die Marke", "telegram_notify.py",
     '    abstand = (kurs - w) / w * 100',
     '    abstand = (kurs - w) / kurs * 100'),
    ("Nachricht: leere STH zeigt eine Zeile", "telegram_notify.py",
     '    if not sth or not sth.get("wert"):\n        return []',
     '    if not sth:\n        return []'),
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
