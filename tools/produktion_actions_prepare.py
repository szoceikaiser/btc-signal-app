"""Offline deployment fence preparation; never creates a remote store."""
import argparse
import json
from pathlib import Path
from produktion_actions_runner import deployment
from actions_delivery import seed_fence

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--runtime',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--cursors',required=True,help='Explicit reviewed per-workflow start floors; never infer zero for existing workflows')
    a = p.parse_args()
    runtime = json.loads(Path(a.runtime).read_text(encoding='utf-8'))
    pin = deployment(runtime)
    if any(v is None for v in pin.values()):
        p.error('Complete reviewed deployment required; disabled template is not a seed')
    baseline = json.loads(Path(a.cursors).read_text(encoding='utf-8'))
    if (baseline.get('schema') != 'actions-v2-start-cursors-v1'
            or baseline.get('review_sha256') != pin['activation_review_sha256']):
        p.error('Explicit per-workflow start floors bound to this activation review required')
    body = seed_fence(pin, baseline['cursors'])
    with Path(a.out).open('xb') as output:
        output.write(body)
