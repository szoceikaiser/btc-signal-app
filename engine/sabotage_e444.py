"""E44.4: jede neue Testfunktion hat eine gezielte Sabotage.

Alle Mutationen laufen in Wegwerf-Kopien, nie im Arbeitscode. Kein Netz, keine
Markt-Messung. Im Hintergrund mit Protokoll ausfuehren, bis zum Ende laufen lassen.
Aufruf: python3 -u sabotage_e444.py > sabotage_e444.log 2>&1
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ENG = Path(__file__).resolve().parent
# Name, Datei, Original, Sabotage, zugehoeriger Test (kein Test darf fehlen).
FAELLE = [
    ("Default aktiviert", "main.py", '"verkauf_faktor": 1.0,', '"verkauf_faktor": 0.67,',
     "test_defaults_und_neutraler_pfad"),
    ("Ungueltiger Faktor erlaubt", "strategy_core.py",
     'return faktor if 0 < faktor <= 1 else 1.0', 'return faktor',
     "test_faktor_validierung"),
    ("Long unskaliert", "strategy_core.py",
     's.tranche_pct = verkauf_tranche(s.tranche_pct, verkauf_faktor)',
     's.tranche_pct = verkauf_tranche(s.tranche_pct, 1.0 if not s.type.name.startswith("SHORT") else verkauf_faktor)',
     "test_long_alle_teilgewinn_typen"),
    ("Short unskaliert", "strategy_core.py",
     's.tranche_pct = verkauf_tranche(s.tranche_pct, verkauf_faktor)',
     's.tranche_pct = verkauf_tranche(s.tranche_pct, 1.0 if s.type.name.startswith("SHORT") else verkauf_faktor)',
     "test_short_alle_teilgewinn_typen"),
    ("Kaeufe und Stops auch gekuerzt", "strategy_core.py",
     'if s.type in _TEILVERKAUF_TYPES:\n            s.tranche_pct = verkauf_tranche',
     'if True:\n            s.tranche_pct = verkauf_tranche',
     "test_kauf_rueckkauf_und_stops_bleiben_unskaliert"),
    ("Plan behaelt alte Mengen", "main.py",
     'ziel["tranche"] = verkauf_tranche(ziel["tranche"], par["verkauf_faktor"])',
     'ziel["tranche"] = ziel["tranche"]',
     "test_plan_und_telegram_nennen_die_reduzierten_mengen"),
    ("Backtest verwirft Parameter", "backtest.py",
     'params = {k: cfg[k] for k in EVAL_KEYS if k in cfg}',
     'params = {k: cfg[k] for k in EVAL_KEYS if k in cfg and k != "verkauf_faktor"}',
     "test_backtest_reicht_faktor_an_engine_weiter"),
    ("Long Leiter verkauft weiter 15", "backtest.py",
     's.get("tranche_pct", LADDER_TRANCHE) / 100.0 * peak_units',
     'LADDER_TRANCHE / 100.0 * peak_units',
     "test_simulate_long_bucht_signalmenge_und_ganzen_rest"),
    ("Long TP verkauft weiter 40", "backtest.py",
     's.get("tranche_pct", 40) / 100.0 * peak_units', '0.4 * peak_units',
     "test_simulate_long_bucht_signalmenge_und_ganzen_rest"),
    ("Short Leiter deckt weiter 15", "backtest.py",
     's.get("tranche_pct", LADDER_TRANCHE) / 100.0 * s_peak',
     'LADDER_TRANCHE / 100.0 * s_peak',
     "test_simulate_short_bucht_signalmenge_und_ganzen_rest"),
    ("Short TP deckt weiter 40", "backtest.py",
     's.get("tranche_pct", 40) / 100.0 * s_peak', '0.4 * s_peak',
     "test_simulate_short_bucht_signalmenge_und_ganzen_rest"),
    ("State verliert Bruchteile", "main.py",
     'pos.bestand_pct = float(d.get("bestand_pct", min(100, pos.entry_pct or 0)) or 0)',
     'pos.bestand_pct = int(d.get("bestand_pct", min(100, pos.entry_pct or 0)) or 0)',
     "test_bruchteile_ueberleben_state_json"),
    ("Neustart verliert Bruchteile", "main.py",
     'pos.bestand_pct = float(d.get("bestand_pct", min(100, pos.entry_pct or 0)) or 0)',
     'pos.bestand_pct = int(d.get("bestand_pct", min(100, pos.entry_pct or 0)) or 0)',
     "test_getrennte_prozesse_gleiche_signale_telegram_und_state"),
    ("Restmeldung behauptet 20 Prozent", "telegram_notify.py",
     'if sig["type"] in ("VERKAUF_REST", "SHORT_COVER_REST"):', 'if False:',
     "test_rest_meldung_verspricht_keine_feste_20_prozent"),
]

DRIVER = '''import sys, traceback
import test_e444 as t
try:
    for name in sys.argv[1:]:
        getattr(t, name)()
except AssertionError:
    traceback.print_exc()
    sys.exit(1)
except Exception:
    traceback.print_exc()
    sys.exit(2)
'''


def main():
    import test_e444
    tests = sorted(n for n in vars(test_e444) if n.startswith("test_"))
    assert set(tests) == {x[4] for x in FAELLE}, "Test ohne Gegenprobe!"
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    gefangen = 0
    with tempfile.TemporaryDirectory(prefix="e444-sabotage-") as tmp:
        root = Path(tmp)
        eng = root / "engine"
        eng.mkdir()
        for p in ENG.glob("*.py"):
            shutil.copy2(p, eng / p.name)
        cfg = root / "site/data"
        cfg.mkdir(parents=True)
        shutil.copy2(ENG.parent / "site/data/config.json", cfg / "config.json")
        basis = subprocess.run([sys.executable, "-c", DRIVER, *tests], cwd=eng,
                               env=env, capture_output=True, text=True, encoding="utf-8")
        if basis.returncode:
            print("BASIS NICHT GRUEN", basis.stdout, basis.stderr, flush=True)
            return 2
        print(f"BASIS: {len(tests)} Tests gruen", flush=True)
        for nr, (name, datei, alt, neu, test) in enumerate(FAELLE, 1):
            p = eng / datei
            original = p.read_text(encoding="utf-8")
            assert original.count(alt) == 1, (name, "Sabotage-Stelle nicht eindeutig")
            try:
                p.write_text(original.replace(alt, neu), encoding="utf-8")
                ergebnis = subprocess.run([sys.executable, "-c", DRIVER, test], cwd=eng,
                                          env=env, capture_output=True, text=True, encoding="utf-8")
                ok = ergebnis.returncode == 1
                gefangen += ok
                print(f"{nr:02d} {'GEFANGEN' if ok else 'LUECKE/FEHLER'}: {name} -> {test}", flush=True)
                print(ergebnis.stdout + ergebnis.stderr, flush=True)
            finally:
                p.write_text(original, encoding="utf-8")
    print(f"ERGEBNIS: {gefangen}/{len(FAELLE)} gefangen; {len(tests)} Tests abgedeckt", flush=True)
    return 0 if gefangen == len(FAELLE) else 1


if __name__ == "__main__":
    sys.exit(main())
