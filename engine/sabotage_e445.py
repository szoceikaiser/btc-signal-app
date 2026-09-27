"""E44.5: gezielte Mutationen nur in temporaeren Kopien, jeder neue Test abgedeckt."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ENG = Path(__file__).resolve().parent
FAELLE = [
    ("K2 falsch", "backtest.py", "verkauf_faktor=0.67 if _k2 else 1.0", "verkauf_faktor=0.70 if _k2 else 1.0", "test_gitter_acht_ecken_genau_live_basis"),
    ("Robustheit falsch", "backtest.py", "ausbruch_ruecktest=True, ruecktest_fenster=6", "ausbruch_ruecktest=True, ruecktest_fenster=12", "test_robustheit_nur_sechs_statt_zwoelf"),
    ("H2 ignoriert", "e445.py", "h1 >= grenze and h2 >= grenze", "h1 >= grenze", "test_hauptzeile_beide_haelften_und_exakte_grenze"),
    ("Kombination zu leicht", "e445.py", "1.0 if haupt else 2.0", "1.0 if haupt else 1.0", "test_kombination_braucht_zwei_punkte"),
    ("Rueckgang ignoriert", "e445.py", "and dd >= -1.0", "and True", "test_rueckgang_verhindert_positive_renditeentscheidung"),
    ("Monatsprobe ignoriert", "e445.py", 'and mp["haelt"]', "and True", "test_monatsprobe_ausreisser_null_und_fehlende_monate"),
    ("Fehlende Monate erlaubt", "e445.py", "and vollstaendig and", "and True and", "test_monatsprobe_ausreisser_null_und_fehlende_monate"),
    ("Hauptrolle vertauscht", "e445.py", 'else "Hauptzeile" if label == bt.E445_HAUPT', 'else "Erklaerung" if label == bt.E445_HAUPT', "test_auswertung_rollen_wechselwirkungen_und_bericht"),
    ("Fehlende Haelfte ignoriert", "e445.py", 'raise ValueError("Kein Urteil: E44.5-Gitter oder Fensterhaelfte unvollstaendig")', 'return dict(zeilen=[], wechselwirkungen=[])', "test_fehlende_haelfte_keine_entscheidung"),
    ("Alter immer null", "backtest.py", '(s.ts - beobachtung_start) // CANDLE_MS', '0', "test_alter_aus_echter_engine_ohne_signalveraenderung"),
    ("Altersgrenze verschoben", "e445.py", "sum(a > 12 for a in alter)", "sum(a >= 12 for a in alter)", "test_alte_marken_grenze_im_bericht"),
]

DRIVER = '''import sys, traceback
import test_e445 as t
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
    import test_e445
    tests = sorted(n for n in vars(test_e445) if n.startswith("test_"))
    assert set(tests) == {x[4] for x in FAELLE}, "Test ohne Gegenprobe!"
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    gefangen = 0
    with tempfile.TemporaryDirectory(prefix="e445-sabotage-") as tmp:
        eng = Path(tmp) / "engine"
        eng.mkdir()
        for p in ENG.glob("*.py"):
            shutil.copy2(p, eng / p.name)
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
