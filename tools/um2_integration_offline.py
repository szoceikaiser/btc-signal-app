"""Read-only local integration proof; no dispatch, live store or data access."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='a7cf45d171500b3ef93bd5ca195071b419fe0dfb'
def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'-C',str(ROOT),*args],text=True).strip()
def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def inspect():
    assert git('branch','--show-current')=='codex/um2-engine-integration'
    head=git('rev-parse','HEAD')
    git('merge-base','--is-ancestor',BASE,head)
    frozen=('.github/workflows','ops','site','engine/config.json',
        'docs/audit-nacharbeit-2026-10','docs/produktionsuebernahme-2026-10',
        'tools/produktion_p1.py','tools/produktion_p2.py','tools/produktion_p3.py','tools/produktion_renditen.py')
    assert not git('diff',BASE,head,'--',*frozen),'Protected integration baseline changed'
    runtime=json.loads((ROOT/'ops/produktion/github-runtime.disabled.json').read_text())
    assert runtime['enabled'] is False and runtime['live_activation']=='P4 only'
    assert 'if: ${{ false }}' in (ROOT/'ops/produktion/github-workflow.disabled.yml').read_text()
    sys.path.insert(0,str(ROOT/'engine'))
    import execution_v1 as v,liquidation_evidence as evidence
    assert v.EXECUTION_SEMANTICS=='V1-exact-budget-v2'
    assert evidence.SEMANTICS_VERSION=='UM2-M5-v1-native'
    candidates=[]
    for label in ('C05-UM2','S006-UM2'):
        p=ROOT/'docs/um2-engine-integration/candidates'/(label+'.inactive.json')
        c=json.loads(p.read_text(encoding='utf-8'))
        assert c['active'] is False and c['runtime_binding'] is None and c['position_migration'] is False
        assert c['params']['muster_cvd']=='usd' and digest(c['params'])==c['config_sha256']
        candidates.append(dict(label=label,config_sha256=c['config_sha256'],active=False))
    return dict(passed=True,head=head,tree=git('rev-parse','HEAD^{tree}'),base=BASE,
        branch='codex/um2-engine-integration',frozen_paths_unchanged=list(frozen),
        candidates=candidates,live_activation=False,online_ci_completed=False,
        note='Old production_p2/p3 proofs retain their original P3-branch precondition. This separate integration proof and complete engine regression validate the new local branch without relabeling those old receipts.')
if __name__=='__main__':print(json.dumps(inspect(),indent=2,ensure_ascii=False))
