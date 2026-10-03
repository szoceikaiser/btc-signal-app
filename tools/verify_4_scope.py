"""Stage 4 scope, immutable inputs/tag, ancestry and branch push triggers."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '9606a6f555f9cdaee86f9c33a5175c5c5306b365'
TAG = 'sicherung/vor-audit-korrekturen-2026-09-28'


def git(*args):
    return subprocess.run(['git', '-c', f'safe.directory={ROOT.as_posix()}', *args],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main():
    assert git('remote', 'get-url', 'origin') == 'https://github.com/szoceikaiser/btc-signal-app.git'
    assert git('branch', '--show-current') == 'codex/etappe-4-bestand-stop'
    assert git('rev-parse', TAG) == '7d78094c17624b90b8f7ebc387b96570ff2c8ef7'
    assert git('rev-parse', TAG+'^{}') == '469be65f65327a3b6abf2794ceba09c1fe0de9e2'
    git('merge-base', '--is-ancestor', BASE, 'HEAD')
    # No merges/newer main ancestry: every post-base commit must be a single
    # parent chain belonging to this stage, ending directly at the specified base.
    tip = git('rev-parse', 'HEAD')
    while tip != BASE:
        parents = git('rev-list', '--parents', '-n', '1', tip).split()
        assert len(parents) == 2, parents
        tip = parents[1]
    protected = ['site', '.github', 'BACKTEST.md', 'docs/e445',
                 'docs/nacharbeit-2026-09-28/F01-F12-VERTRAG.md',
                 'docs/nacharbeit-2026-09-28/F01-F12-UMSETZUNG.md',
                 ':(glob)docs/nacharbeit-2026-09-28/3b-*',
                 ':(glob)docs/nacharbeit-2026-09-28/3a-*',
                 ':(glob)docs/nacharbeit-2026-09-28/d01-*',
                 ':(glob)docs/nacharbeit-2026-09-28/f09-*']
    git('diff', '--exit-code', BASE, '--', *protected)
    allowed = {'engine/backtest.py', 'engine/execution_v1.py', 'engine/main.py',
        'engine/strategy_core.py', 'engine/telegram_notify.py', 'engine/inventory.py',
        'engine/position_state.py', 'engine/test_stage4.py', 'engine/sabotage_4.py',
        'engine/test_execution_v1.py', 'engine/test_main.py', 'engine/test_strategy_core.py',
        'wissens-layer/00_STAND.md', 'wissens-layer/02_status/UEBERGABE.md',
        'docs/nacharbeit-2026-09-28/ETAPPEN.md',
        'docs/nacharbeit-2026-09-28/F03-F04-F05-F10-VERTRAG.md',
        'docs/nacharbeit-2026-09-28/ETAPPE-4-ABSCHLUSS.md',
        'docs/nacharbeit-2026-09-28/START-5A.md'}
    changes = sorted(set(git('diff', '--name-only', BASE).splitlines()) |
                     set(git('ls-files', '--others', '--exclude-standard').splitlines()))
    assert all(p in allowed or p.startswith('docs/nacharbeit-2026-09-28/4-') or
               p.startswith('tools/verify_4') for p in changes), changes
    tests = (ROOT/'.github/workflows/tests.yml').read_text(encoding='utf-8')
    pages = (ROOT/'.github/workflows/pages.yml').read_text(encoding='utf-8')
    assert '  push:' in tests and 'python3 run_tests.py' in tests
    assert 'branches: [main]' in pages and 'workflows: ["Signal-Engine", "Backtest"]' in pages
    pushes = []
    for p in (ROOT/'.github/workflows').glob('*.yml'):
        content = p.read_text(encoding='utf-8')
        if '  push:' in content:
            pushes.append(p.name)
    assert sorted(pushes) == ['pages.yml', 'tests.yml']
    print(json.dumps(dict(result='PASS', base=BASE, head=git('rev-parse', 'HEAD'),
        branch=git('branch', '--show-current'), changes=changes, protected=protected,
        tag_object=git('rev-parse', TAG), tag_target=git('rev-parse', TAG+'^{}'),
        allowed_push_workflow='Tests', live_and_originals_unchanged=True), indent=2))


if __name__ == '__main__':
    main()
