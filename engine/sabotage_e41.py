"""Sabotage-Probe fuer E41 (Stop mit Puffer / Rueckeroberung / Docht, 21.09.2026).

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
    # --- Kaisers Regel ---------------------------------------------------------------
    ("Rueckeroberung: Stop kommt nie (Zaehler laeuft nicht)", "strategy_core.py",
     '    pos.stop_wartet += 1\n    pos.stop_wartet_inv = inv',
     '    pos.stop_wartet_inv = inv'),
    ("Rueckeroberung stoppt eine Kerze zu frueh", "strategy_core.py",
     '    if pos.stop_wartet > rueckeroberung:',
     '    if pos.stop_wartet >= rueckeroberung:'),
    ("Zurueckeroberte Marke wird nicht als geprueft gefuehrt", "strategy_core.py",
     '            pos.stop_geprueft = inv              # zurueckerobert -> Marke ist geprueft',
     '            pass'),
    ("Geprueft wird ignoriert (zweite Schonfrist)", "strategy_core.py",
     '    if pos.stop_geprueft == inv:\n        return True, cur.close, ("Kerzenschluss',
     '    if False:\n        return True, cur.close, ("Kerzenschluss'),
    ("Harter Boden faellt weg", "strategy_core.py",
     '    if jenseits(cur.close, DIP_FLOOR_PCT):',
     '    if False:'),
    ("Neue Marke erbt das Warten der alten", "strategy_core.py",
     '    if pos.stop_wartet and pos.stop_wartet_inv != inv:\n        pos.stop_wartet = 0',
     '    if False:\n        pos.stop_wartet = 0'),
    ("Rueckeroberung gilt nur fuer Long", "strategy_core.py",
     '        return preis > inv * (1 + abstand)',
     '        return False'),
    # --- Puffer und Docht --------------------------------------------------------------
    ("Puffer wird ignoriert", "strategy_core.py",
     '    unter = jenseits(cur.close, puffer_pct)',
     '    unter = jenseits(cur.close, 0.0)'),
    ("Docht-Stop zum Schlusskurs (geschoent)", "strategy_core.py",
     '            fill = min(cur.open, inv) if long_side else max(cur.open, inv)',
     '            fill = cur.close'),
    ("Docht-Stop bei Luecke zum Stopkurs statt zum Eroeffnungskurs", "strategy_core.py",
     '            fill = min(cur.open, inv) if long_side else max(cur.open, inv)',
     '            fill = inv'),
    # --- Einbindung in evaluate --------------------------------------------------------
    ("E41 greift auch beim nachgezogenen Stop", "strategy_core.py",
     '        if trail_note in ("", "Invalidierung") and (\n                stop_puffer_pct > 0',
     '        if True and (\n                stop_puffer_pct > 0'),
    ("Waehrend des Wartens wird nachgekauft", "strategy_core.py",
     '        if _e41_sperre:\n            return False\n        return not (no_flip',
     '        if False:\n            return False\n        return not (no_flip'),
    ("In der Kerze der Rueckeroberung wird nachgekauft", "strategy_core.py",
     '            _e41_sperre = _wartete or pos.stop_wartet > 0',
     '            _e41_sperre = pos.stop_wartet > 0'),
    ("Nachkauf nach Rueckeroberung zum teuren Levelpreis", "strategy_core.py",
     '                    if pos.stop_geprueft is not None:\n                        preis_nk = (min(',
     '                    if False:\n                        preis_nk = (min('),
    ("Preiskorrektur gilt auch ohne E41 (Live-Zahlen aendern sich)", "strategy_core.py",
     '                    if pos.stop_geprueft is not None:\n                        preis_nk = (min(',
     '                    if True:\n                        preis_nk = (min('),
    ("Stop-Grund aus E41 geht verloren", "strategy_core.py",
     '            elif stop_grund:\n                reason = stop_grund',
     '            elif False:\n                reason = stop_grund'),
    ("Stop-Preis aus E41 geht verloren", "strategy_core.py",
     '            signals.append(Signal(cur.ts, st, stop_preis, 100, reason))',
     '            signals.append(Signal(cur.ts, st, cur.close, 100, reason))'),
    ("Reset vergisst die Merker", "strategy_core.py",
     '    pos.stop_wartet = 0\n    pos.stop_wartet_inv = None\n    pos.stop_geprueft = None\n',
     ''),
    # --- Live-Engine -------------------------------------------------------------------
    ("Live-Engine speichert das Warten nicht", "main.py",
     '         "stop_wartet": pos.stop_wartet, "stop_wartet_inv": pos.stop_wartet_inv,',
     '         "stop_wartet_inv": pos.stop_wartet_inv,'),
    ("Live-Engine liest das Warten nicht", "main.py",
     '    pos.stop_geprueft = d.get("stop_geprueft")',
     '    pos.stop_geprueft = None'),
    ("Live-Engine reicht die Schalter nicht durch", "main.py",
     '    "stop_puffer_pct": 0.0, "stop_rueckeroberung": 0, "stop_auf_docht": False,',
     '    "stop_puffer_pct": 0.0, "stop_auf_docht": False,'),
    # --- Backtest ------------------------------------------------------------------------
    ("Schalter fehlt in EVAL_KEYS", "backtest.py",
     '             "stop_puffer_pct", "stop_rueckeroberung", "stop_auf_docht",',
     '             "stop_puffer_pct", "stop_auf_docht",'),
    ("B3 misst in Wahrheit B1", "backtest.py",
     '      stop_rueckeroberung=3),',
     '      stop_rueckeroberung=1),'),
    ("Urteil: Rueckgangsgrenze falsch herum", "backtest.py",
     '    dd_ok = v["dd"] >= basis["dd"] - E41_DD_TOLERANZ',
     '    dd_ok = v["dd"] <= basis["dd"] - E41_DD_TOLERANZ'),
    ("Urteil: ob der Schalter gegriffen hat, zaehlt nicht", "backtest.py",
     '            "besteht": beide and dd_ok and weniger}',
     '            "besteht": beide and dd_ok}'),
    ("Urteil: eine Kerzenzahl reicht", "backtest.py",
     '        if b1 and b3:',
     '        if b1 or b3:'),
    ("Gewinnende Gegenprobe wird verschwiegen", "backtest.py",
     '    if c:\n        z.append("- **Achtung: die Gegenprobe besteht.**',
     '    if False:\n        z.append("- **Achtung: die Gegenprobe besteht.**'),
    ("E41 misst gegen die beste Variante statt gegen live", "backtest.py",
     '        lambda: e41_abschnitt(results, halves, panel_cfg["label"]),',
     '        lambda: e41_abschnitt(results, halves, best_cfg["label"]),'),
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
