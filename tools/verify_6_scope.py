"""Restrict stage 6 to reproduction evidence/design; preserve all baseline code."""
import json
import re
from pathlib import Path
from verify_4_backup import git

ROOT = Path(__file__).resolve().parents[1]
BASE = 'bb862204c97c6bb4c0da49cb6f1de90dd58af663'
BRANCH = 'codex/etappe-6-reproduktion-design'
TAG = 'sicherung/vor-audit-korrekturen-2026-09-28'

def verify():
    def g(*args): return git(ROOT, *args).decode().strip()
    assert g('remote', 'get-url', 'origin') == 'https://github.com/szoceikaiser/btc-signal-app.git'
    assert g('branch', '--show-current') == BRANCH
    assert g('rev-parse', TAG) == '7d78094c17624b90b8f7ebc387b96570ff2c8ef7'
    assert g('rev-parse', TAG+'^{}') == '469be65f65327a3b6abf2794ceba09c1fe0de9e2'
    tip = g('rev-parse', 'HEAD')
    while tip != BASE:
        parents = g('rev-list', '--parents', '-n', '1', tip).split()
        assert len(parents) == 2, 'No merge or alternate ancestry allowed'
        tip = parents[1]
    allowed = {'wissens-layer/00_STAND.md', 'wissens-layer/02_status/UEBERGABE.md',
        'docs/nacharbeit-2026-09-28/ETAPPEN.md',
        'docs/nacharbeit-2026-09-28/ETAPPE-6-ABSCHLUSS.md',
        'docs/nacharbeit-2026-09-28/START-NACH-6.md'}
    def permitted(p):
        return p in allowed or p.startswith('tools/verify_6') or p.startswith('docs/nacharbeit-2026-09-28/6-')
    changes = sorted(set(g('diff', '--name-only', BASE).splitlines()) |
        set(g('ls-files', '--others', '--exclude-standard').splitlines()))
    assert all(permitted(p) for p in changes), changes
    original = g('ls-tree', '-r', '--name-only', BASE).splitlines()
    protected = [p for p in original if not permitted(p)]
    # Compare actual working-tree normalized blobs, not just index/diff claims.
    for path in protected:
        assert g('hash-object', '--path='+path, path) == g('rev-parse', BASE+':'+path), path
    workflows = list((ROOT/'.github/workflows').glob('*.yml'))
    assert sorted(p.name for p in workflows if re.search(r'^  push:', p.read_text(), re.M)) == ['pages.yml', 'tests.yml']
    pages = (ROOT/'.github/workflows/pages.yml').read_text()
    assert 'branches: [main]' in pages and 'workflows: ["Signal-Engine", "Backtest"]' in pages
    return dict(result='PASS', base=BASE, head=g('rev-parse', 'HEAD'), branch=BRANCH,
        changes=changes, protected_files_identical=len(protected), old_test_changes='none',
        engine_site_workflows_contracts_inputs_identical=True, only_branch_push_workflow='Tests',
        no_new_main_or_e444_e445_commits=True, private_repo_not_committed=True)

if __name__ == '__main__': print(json.dumps(verify(), indent=2))
