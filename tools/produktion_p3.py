"""Read-only P3 evidence for the selected, still offline GitHub path."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
P2B = 'e8d6a8ba79505f0bfbd23cd7e6cc9ca57f09bcc3'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def inspect():
    sys.path.insert(0, str(ROOT/'tools'))
    import produktion_p2
    p2 = produktion_p2.inspect()
    head = p2['head']
    subprocess.check_call(['git', 'merge-base', '--is-ancestor', P2B, head], cwd=ROOT)
    changed = set(git('diff', '--name-only', P2B, head, '--', '.github/workflows').splitlines())
    assert changed <= {'.github/workflows/produktion-offline.yml'}, changed
    workflow = (ROOT/'.github/workflows/produktion-offline.yml').read_text(encoding='utf-8')
    assert 'branches: [codex/produktion-audit-uebernahme]' in workflow
    assert 'tools/produktion_p3.py' in workflow
    template = (ROOT/'ops/produktion/github-workflow.disabled.yml').read_text(encoding='utf-8')
    runtime = json.loads((ROOT/'ops/produktion/github-runtime.disabled.json').read_text(encoding='utf-8'))
    assert 'if: ${{ false }}' in template
    assert runtime['enabled'] is False and runtime['live_activation'] == 'P4 only'
    assert (ROOT/'engine/test_github_delivery.py').is_file()
    assert (ROOT/'docs/produktionsuebernahme-2026-10/P3-GITHUB-BERICHT.md').is_file()
    return {'schema': 'produktion-p3-github-offline-proof-v1', 'head': head,
            'p2b_baseline': P2B, 'selected_adapter': 'github',
            'real_store_api_writes': False, 'live_activation': False,
            'disabled_template': True, 'ci_workflow_changes': sorted(changed)}


if __name__ == '__main__':
    print(json.dumps(inspect(), ensure_ascii=False, sort_keys=True))
