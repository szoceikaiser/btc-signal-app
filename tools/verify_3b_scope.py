"""Local scope and protected-tree check, read-only; run before branch push."""
from pathlib import Path
import json
import subprocess
ROOT=Path(__file__).resolve().parents[1]
BASE='67c8e624de3cc1b854a78dced755a5702b1a9c9a'
TAG='sicherung/vor-audit-korrekturen-2026-09-28'
def git(*args):
    return subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}',*args],cwd=ROOT,
                          capture_output=True,text=True,check=True).stdout.strip()
def main():
    assert git('remote','get-url','origin')=='https://github.com/szoceikaiser/btc-signal-app.git'
    assert git('branch','--show-current')=='codex/etappe-3b-f01-f12'
    git('merge-base','--is-ancestor',BASE,'HEAD')
    assert git('rev-parse',TAG)=='7d78094c17624b90b8f7ebc387b96570ff2c8ef7'
    assert git('rev-parse',TAG+'^{}')=='469be65f65327a3b6abf2794ceba09c1fe0de9e2'
    protected=['site','.github','BACKTEST.md','docs/e445',
        'docs/nacharbeit-2026-09-28/F01-F12-VERTRAG.md',
        'docs/nacharbeit-2026-09-28/D01.md','docs/nacharbeit-2026-09-28/F09.md',
        'docs/nacharbeit-2026-09-28/3a-pruefung.json','docs/nacharbeit-2026-09-28/d01-ergebnis.json']
    git('diff','--exit-code',BASE,'--',*protected)
    changes=git('diff','--name-only',BASE).splitlines()
    allowed={'engine/backtest.py','engine/strategy_core.py','engine/test_strategy_core.py',
             'wissens-layer/00_STAND.md','wissens-layer/02_status/UEBERGABE.md',
             'docs/nacharbeit-2026-09-28/ETAPPEN.md'}
    assert all(p in allowed or p.startswith('docs/nacharbeit-2026-09-28/3b-') or
               p in {'docs/nacharbeit-2026-09-28/F01-F12-UMSETZUNG.md','engine/execution_v1.py',
                     'engine/sabotage_3b.py','engine/test_execution_v1.py'} or
               p.startswith('tools/verify_3b') for p in changes),changes
    tests=(ROOT/'.github/workflows/tests.yml').read_text(encoding='utf-8')
    assert '  push:' in tests and 'python3 run_tests.py' in tests
    print(json.dumps(dict(result='PASS',base=BASE,head=git('rev-parse','HEAD'),
        protected=protected,tag=git('rev-parse',TAG+'^{}'),allowed_push_workflow='Tests'),indent=2))
if __name__=='__main__':main()
