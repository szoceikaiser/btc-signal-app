"""Pure dispatch/run binding preparation; no network, workflow or transport."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
from freshness import dispatch_slot
from production_contract import canonical


def prepare(policy, kind, epoch_seconds, actual):
    if kind not in ('signal','watch'):raise ValueError('Only regular signal/watch schedules')
    schedule=policy['schedules'][kind]
    slot=dispatch_slot(schedule,epoch_seconds)
    expected_ref=schedule['repository']+'/'+schedule['workflow']+'@refs/heads/'+schedule['branch']
    if (actual['GITHUB_REPOSITORY']!=schedule['repository']
            or actual['GITHUB_WORKFLOW_REF']!=expected_ref
            or actual['GITHUB_REF']!='refs/heads/'+schedule['branch']
            or actual['GITHUB_SHA']!=policy['identity']['code_sha']
            or not actual['GITHUB_RUN_ID'].isdigit()
            or not actual['GITHUB_RUN_ATTEMPT'].isdigit()
            or int(actual['GITHUB_RUN_ATTEMPT'])<1):
        raise ValueError('Actual run differs from approved policy')
    return {'BTC_DELIVERY_RUN_REPOSITORY':schedule['repository'],
        'BTC_DELIVERY_WORKFLOW':schedule['workflow'],'BTC_DELIVERY_RUN_ID':actual['GITHUB_RUN_ID'],
        'BTC_DELIVERY_RUN_ATTEMPT':actual['GITHUB_RUN_ATTEMPT'],
        'BTC_DELIVERY_CODE_SHA':actual['GITHUB_SHA'],
        'BTC_DELIVERY_EXPECTED_START_MS':str(slot)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true',required=True)
    p.add_argument('--fixture',required=True);a=p.parse_args()
    f=json.loads(Path(a.fixture).read_text(encoding='utf-8'))
    if f.get('synthetic') is not True:raise ValueError('Synthetic fixture only')
    print(canonical(prepare(f['policy'],f['kind'],f['dispatch_epoch_seconds'],f['actual'])))
