"""Test-Runner ohne Abhaengigkeiten. Ausfuehren: python3 run_tests.py

Findet automatisch alle test_*.py im Ordner und fuehrt deren test_-Funktionen aus.
"""
import importlib
import pathlib
import sys
import traceback

ok = fail = 0
for path in sorted(pathlib.Path(__file__).parent.glob("test_*.py")):
    mod = importlib.import_module(path.stem)
    for name, fn in sorted(vars(mod).items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                ok += 1
                print(f"PASS {path.stem}::{name}")
            except Exception:
                fail += 1
                print(f"FAIL {path.stem}::{name}")
                traceback.print_exc(limit=3)
print(f"--- {ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
