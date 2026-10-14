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
    a = p.parse_args()
    runtime = json.loads(Path(a.runtime).read_text(encoding='utf-8'))
    pin = deployment(runtime)
    if any(v is None for v in pin.values()):
        p.error('Complete reviewed deployment required; disabled template is not a seed')
    with Path(a.out).open('xb') as output:
        output.write(seed_fence(pin))
