"""Exact 5a ancestry, all 712 old tests and all trading/delivery artifacts frozen."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '6c0c6fdd56db9bb27febaf42c56f6e33bcab0685'
BRANCH = 'codex/etappe-5b-chart-identitaet'
TAG = 'sicherung/vor-audit-korrekturen-2026-09-28'
def git(*args):
    return subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}',*args],cwd=ROOT).decode().strip()
def verify():
    assert git('remote','get-url','origin') == 'https://github.com/szoceikaiser/btc-signal-app.git'
    assert git('branch','--show-current') == BRANCH
    assert git('rev-parse',TAG) == '7d78094c17624b90b8f7ebc387b96570ff2c8ef7'
    assert git('rev-parse',TAG+'^{}') == '469be65f65327a3b6abf2794ceba09c1fe0de9e2'
    tip=git('rev-parse','HEAD')
    while tip != BASE:
        parents=git('rev-list','--parents','-n','1',tip).split(); assert len(parents)==2
        tip=parents[1]
    allowed={'site/index.html','site/chart_signals.js','engine/test_stage5b.py',
        'tools/chart_5b_tests.cjs','wissens-layer/00_STAND.md','wissens-layer/02_status/UEBERGABE.md',
        'docs/nacharbeit-2026-09-28/ETAPPEN.md','docs/nacharbeit-2026-09-28/F17-VERTRAG.md',
        'docs/nacharbeit-2026-09-28/ETAPPE-5B-ABSCHLUSS.md','docs/nacharbeit-2026-09-28/START-6.md'}
    changes=sorted(set(git('diff','--name-only',BASE).splitlines()) |
                   set(git('ls-files','--others','--exclude-standard').splitlines()))
    assert all(p in allowed or p.startswith('tools/verify_5b') or
               p.startswith('docs/nacharbeit-2026-09-28/5b-') for p in changes),changes
    tracked=git('ls-tree','-r','--name-only',BASE).splitlines()
    protected=[p for p in tracked if p.startswith(('engine/','site/data/','.github/', 'docs/e445/')) or
               p.endswith(('F01-F12-VERTRAG.md','F03-F04-F05-F10-VERTRAG.md','F13-VERTRAG.md')) or
               p.startswith('docs/nacharbeit-2026-09-28/4-')]
    git('diff','--exit-code',BASE,'--',*protected)
    push=sorted(p.name for p in (ROOT/'.github/workflows').glob('*.yml') if '  push:' in p.read_text())
    assert push==['pages.yml','tests.yml']
    pages=(ROOT/'.github/workflows/pages.yml').read_text()
    assert 'branches: [main]' in pages and 'workflows: ["Signal-Engine", "Backtest"]' in pages
    return dict(result='PASS',base=BASE,head=git('rev-parse','HEAD'),branch=BRANCH,
        changes=changes,protected_files_identical=len(protected),old_test_changes='none',
        only_branch_push_workflow='Tests',no_private_transcripts_added=True)
if __name__ == '__main__': print(json.dumps(verify(),indent=2))
