"""Exact ancestry, preserved contracts/676 old tests and safe branch triggers."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = 'ebc01a48057994629c021bd84ab7f9a236678b70'
BRANCH = 'codex/etappe-5a-telegram-outbox'
TAG = 'sicherung/vor-audit-korrekturen-2026-09-28'

def git(*args):
    return subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}',*args],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()

def verify():
    assert git('remote','get-url','origin') == 'https://github.com/szoceikaiser/btc-signal-app.git'
    assert git('branch','--show-current') == BRANCH
    assert git('rev-parse',TAG) == '7d78094c17624b90b8f7ebc387b96570ff2c8ef7'
    assert git('rev-parse',TAG+'^{}') == '469be65f65327a3b6abf2794ceba09c1fe0de9e2'
    tip = git('rev-parse','HEAD')
    while tip != BASE:
        parents = git('rev-list','--parents','-n','1',tip).split()
        assert len(parents) == 2
        tip = parents[1]
    allowed = {'engine/main.py','engine/telegram_notify.py','engine/telegram_outbox.py',
        'engine/test_stage5a.py','engine/sabotage_5a.py','wissens-layer/00_STAND.md',
        'wissens-layer/02_status/UEBERGABE.md','docs/nacharbeit-2026-09-28/ETAPPEN.md',
        'docs/nacharbeit-2026-09-28/F13-VERTRAG.md','docs/nacharbeit-2026-09-28/ETAPPE-5A-ABSCHLUSS.md',
        'docs/nacharbeit-2026-09-28/START-5B.md'}
    changes = sorted(set(git('diff','--name-only',BASE).splitlines()) |
                     set(git('ls-files','--others','--exclude-standard').splitlines()))
    assert all(p in allowed or p.startswith('tools/verify_5a') or p.startswith('docs/nacharbeit-2026-09-28/5a-') for p in changes), changes
    old_tests = git('ls-tree','-r','--name-only',BASE,'engine').splitlines()
    old_tests = [p for p in old_tests if Path(p).name.startswith('test_')]
    git('diff','--exit-code',BASE,'--',*old_tests)
    protected = ['site','.github','engine/strategy_core.py','engine/execution_v1.py',
        'engine/inventory.py','engine/position_state.py','engine/backtest.py','BACKTEST.md','docs/e445',
        'docs/nacharbeit-2026-09-28/F01-F12-VERTRAG.md',
        'docs/nacharbeit-2026-09-28/F03-F04-F05-F10-VERTRAG.md',
        'docs/nacharbeit-2026-09-28/ETAPPE-4-ABSCHLUSS.md']
    git('diff','--exit-code',BASE,'--',*protected)
    push = sorted(p.name for p in (ROOT/'.github/workflows').glob('*.yml') if '  push:' in p.read_text())
    assert push == ['pages.yml','tests.yml']
    pages = (ROOT/'.github/workflows/pages.yml').read_text()
    assert 'branches: [main]' in pages and 'workflows: ["Signal-Engine", "Backtest"]' in pages
    assert 'python3 run_tests.py' in (ROOT/'.github/workflows/tests.yml').read_text()
    return dict(result='PASS',base=BASE,head=git('rev-parse','HEAD'),branch=BRANCH,
        changes=changes, old_test_files_identical=len(old_tests), preserved=protected,
        tag_object=git('rev-parse',TAG),tag_target=git('rev-parse',TAG+'^{}'),
        only_branch_push_workflow='Tests', no_private_transcripts_added=True,
        no_strategy_site_workflow_changes=True)

if __name__ == '__main__': print(json.dumps(verify(),indent=2))
