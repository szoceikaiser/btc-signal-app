"""Offline HTTP-decision fixture CLI. Does not open a port or read secrets."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'engine'))
from freshness import evaluate
from production_contract import canonical, digest


def simulate(path):
    f = json.loads(Path(path).read_text(encoding='utf-8'))
    if f.get('synthetic') is not True:
        raise ValueError('Synthetic inputs required')
    def read_revision(locator):
        snapshot = f['completion_snapshots'][str(locator['revision'])]
        if digest(snapshot) != locator['snapshot_digest']:
            raise ValueError('Completion digest mismatch')
        return snapshot
    return evaluate(f['snapshot'], f['revision'], read_revision,
                    f['runs'], f['policy'], f['now_ms'], f['backup'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--offline', required=True, action='store_true')
    p.add_argument('--fixture', required=True); a = p.parse_args()
    result = simulate(a.fixture)
    print(canonical(result)); sys.exit(0 if result['http_status'] == 200 else 20)
