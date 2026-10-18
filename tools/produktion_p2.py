"""Read-only P2 evidence: new HEAD contract, frozen P1 evidence, offline scope."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
P1='7df2e20e8b68c1c7db8a5b4715fd6c1253e9165b'
P2A='d6297f84578147ca09e408c6a83a86716d586d1d'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()


def inspect():
    head=git('rev-parse','HEAD')
    branch=git('rev-parse','--abbrev-ref','HEAD')
    assert branch=='codex/produktion-audit-uebernahme'
    subprocess.check_call(['git','merge-base','--is-ancestor',P2A,head],cwd=ROOT)
    frozen=('P2A-BETRIEBSVERTRAG.md','P2A-MIGRATIONSVERTRAG.md',
            'P2A-GITHUB-ADAPTER.md','P2B-IMPLEMENTIERUNGSPLAN.md',
            'P1-INTEGRATION.json','RENDITEN.md','RENDITEN.json',
            'RENDITEN-VARIANTEN.csv','RENDITEN-ETAPPEN.csv')
    for name in frozen:
        assert not git('diff',P2A,'--',f'docs/produktionsuebernahme-2026-10/{name}'),name
    sys.path.insert(0,str(ROOT/'engine'))
    import durable_delivery as durable
    old=json.loads(subprocess.check_output(['git','show',
        'ca8ad2fb730174ca1887791d425ae01aa6a715e6:site/data/state.json'],cwd=ROOT))
    try:
        durable.validate({'version':1,'engine':old,'watch':{},'commands':{}})
    except ValueError as exc:
        assert 'Migration requires' in str(exc)
    else:
        raise AssertionError('Legacy P1 direct import became possible')
    workflow=(ROOT/'.github/workflows/produktion-offline.yml').read_text(encoding='utf-8')
    assert 'branches: [codex/produktion-audit-uebernahme]' in workflow
    assert "github.ref == 'refs/heads/codex/produktion-audit-uebernahme'" in workflow
    assert 'contents: read' in workflow and 'secrets.' not in workflow
    assert 'tools/produktion_p2.py' in workflow and 'cd engine && python run_tests.py' in workflow
    return {'schema':'produktion-p2-offline-proof-v1','head':head,'branch':branch,
            'p1_evidence_frozen_at':P1,'p2a_contract_frozen_at':P2A,
            'old_direct_import_refused':True,'production_activated':False,
            'real_host_api_alarm_backup_acceptance':'open'}


if __name__=='__main__':
    print(json.dumps(inspect(),ensure_ascii=False,sort_keys=True))
