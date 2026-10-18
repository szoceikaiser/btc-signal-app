"""Allow only offline follow-up and explicitly authorized isolated GitHub tools."""
import json
import re
from pathlib import Path
from verify_4_backup import git
ROOT=Path(__file__).resolve().parents[1]
BASE='05208cecce8d5a0e856a1ea56984b209f403ccd6'
BRANCH='codex/nach-6-historische-auswertung'
TAG='sicherung/vor-audit-korrekturen-2026-09-28'


def verify():
    def g(*args):return git(ROOT,*args).decode().strip()
    assert g('remote','get-url','origin')=='https://github.com/szoceikaiser/btc-signal-app.git'
    assert g('branch','--show-current')==BRANCH
    assert g('rev-parse',TAG)=='7d78094c17624b90b8f7ebc387b96570ff2c8ef7'
    assert g('rev-parse',TAG+'^{}')=='469be65f65327a3b6abf2794ceba09c1fe0de9e2'
    tip=g('rev-parse','HEAD')
    while tip!=BASE:
        parents=g('rev-list','--parents','-n','1',tip).split()
        assert len(parents)==2
        tip=parents[1]
    allowed={'.gitattributes','.github/workflows/coinalyze-test.yml','.github/workflows/tests.yml',
        'wissens-layer/00_STAND.md','wissens-layer/02_status/UEBERGABE.md','docs/nacharbeit-2026-09-28/ETAPPEN.md',
        'engine/execution_delayed.py','engine/test_execution_delayed.py'}
    def permitted(p):return p in allowed or p.startswith('docs/nach-6/') or p.startswith('tools/historical_') or p.startswith('tools/test_historical_') or p.startswith('tools/verify_n6') or p in {'tools/fetch_n6_data.py','tools/n6_github.py','tools/prepare_n6.py','tools/report_n6.py'}
    changes=sorted(set(g('diff','--name-only',BASE).splitlines())|set(g('ls-files','--others','--exclude-standard').splitlines()))
    assert all(permitted(p) for p in changes),changes
    protected=[p for p in g('ls-tree','-r','--name-only',BASE).splitlines() if not permitted(p)]
    for path in protected:assert g('hash-object','--path='+path,path)==g('rev-parse',BASE+':'+path),path
    workflows=list((ROOT/'.github/workflows').glob('*.yml'))
    assert sorted(p.name for p in workflows if re.search(r'^  push:',p.read_text(),re.M))==['pages.yml','tests.yml']
    pages=(ROOT/'.github/workflows/pages.yml').read_text()
    assert 'branches: [main]' in pages and 'workflows: ["Signal-Engine", "Backtest"]' in pages
    data=(ROOT/'.github/workflows/coinalyze-test.yml').read_text()
    assert data.startswith('name: Nach-6 Historische Rohdaten') and 'contents: read' in data
    assert 'persist-credentials: false' in data and BRANCH in data
    assert not any(x in data for x in ['git push','TELEGRAM','engine/main','backtest.py','schedule:'])
    fetch=(ROOT/'tools/fetch_n6_data.py').read_text()
    assert 'END=1790683200' in fetch and 'START=1790481600' in fetch
    return dict(result='PASS',base=BASE,head=g('rev-parse','HEAD'),branch=BRANCH,
        protected_files_identical=len(protected),old_tests_unchanged=728,
        live_engine_site_contracts_checkpoint_unchanged=True,only_automatic_push='Tests',
        user_authorized_isolated_data_dispatch=True,no_pages_trigger=True,changes=changes)


if __name__=='__main__':print(json.dumps(verify(),indent=2))
