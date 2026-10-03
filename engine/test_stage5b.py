"""Execute the actual production ChartSignals JS, including the HTML load path.

Node is provided on Actions Ubuntu; no browser, API or live filesystem writes.
"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def check(case):
    result = subprocess.run(['node', str(ROOT/'tools/chart_5b_tests.cjs'), case],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

def test_origins(): check('origins')
def test_conflict(): check('conflict')
def test_same_bar(): check('same_bar')
def test_legacy_duplicates(): check('legacy_duplicates')
def test_explicit_repeat(): check('explicit_repeat')
def test_id_collision(): check('id_collision')
def test_reload(): check('reload')
def test_sort(): check('sort')
def test_sequence(): check('sequence')
def test_v1(): check('v1')
def test_unknown_model(): check('unknown_model')
def test_invalid(): check('invalid')
def test_markers(): check('markers')
def test_safe_list(): check('safe_list')
def test_snapshot(): check('snapshot')
def test_page(): check('page')
