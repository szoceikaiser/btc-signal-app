"""Fuehrt nur D01-Gegenfaelle gegen den unveraenderten F09-Commit aus."""
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'engine'))
import test_d01_kerzenschluss as tests


def main():
    source = subprocess.run(['git', '-c', f'safe.directory={ROOT.as_posix()}', 'show',
                             '6edb941b10e4220f4634e4570de8de25261d58b2:engine/backtest.py'],
                            capture_output=True, check=True).stdout
    old = types.ModuleType('_F09_before_D01')
    old.__file__ = str(ROOT/'engine/backtest.py')
    exec(compile(source, '<F09-before-D01>', 'exec'), old.__dict__)
    current = tests.bt
    result = {}
    try:
        tests.bt = old
        for name, fn in vars(tests).items():
            if name.startswith('test_') and callable(fn):
                try:
                    fn()
                    result[name] = 'bestanden'
                except Exception as exc:
                    result[name] = type(exc).__name__
    finally:
        tests.bt = current
    assert result['test_before_close_excludes_unfinished_and_all_associated_values'] == 'AssertionError'
    assert result['test_fetch_filters_api_inclusive_close_timestamp'] == 'AssertionError'
    assert result['test_half_uses_close_not_open_and_empty_is_explicit'] == 'AssertionError'
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
