"""Write exclusive ephemeral config/runtime only; no store, transport or bootstrap."""
import argparse
import json
import os
from pathlib import Path
import sys
from produktion_actions_runner import deployment
from production_contract import canonical, digest, effective_config
from actions_delivery import WORKFLOWS, POLICY


def prepare(kind, out):
    if kind not in ('signal','watch','lage','pages'):
        raise ValueError('Unknown runtime preparation')
    runtime=json.loads(os.environ['REVIEWED_RUNTIME_JSON'])
    config=json.loads(os.environ['REVIEWED_CONFIG_JSON'])
    d=runtime.get('deployment',{}) if kind=='pages' else deployment(runtime)
    if (runtime.get('enabled') is not True or d.get('workflows') != WORKFLOWS
            or d.get('confirmation_policy') != POLICY
            or digest(effective_config(config)) != d.get('config_sha256')):
        raise ValueError('Disabled or inconsistent reviewed runtime/configuration')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    (out/'data').mkdir()
    (out/'runtime.json').write_text(canonical(runtime),encoding='utf-8')
    (out/'data/config.json').write_text(canonical(config),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--kind',required=True);p.add_argument('--out',required=True)
    a=p.parse_args()
    try: prepare(a.kind,a.out)
    except Exception:
        print('Reviewed runtime preparation refused.',file=sys.stderr);sys.exit(20)
