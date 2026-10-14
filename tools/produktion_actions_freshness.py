"""Executable read-only monitor. Credentials must be explicitly injected."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import actions_freshness as monitor
from github_freshness import ReadBudget
from production_contract import canonical
from freshness import response


def run(path):
    with Path(path).open('rb') as f: raw=f.read(128*1024+1)
    if len(raw)>128*1024: return response('monitor_configuration_invalid')
    policy=json.loads(raw)
    if policy.get('enabled') is not True: return response('monitor_disabled')
    d=policy['deployment'];v=policy['independent_verifier'];budget=ReadBudget()
    try:
        source=monitor.Reader(os.environ.get('BTC_MONITOR_STORE_READ_TOKEN'),[d['private_store_repository']],budget)
        code=monitor.Reader(os.environ.get('BTC_MONITOR_ACTIONS_READ_TOKEN'),
            [d['code_repository'],v['binding']['repository']],budget)
        backup=monitor.Reader(os.environ.get('BTC_MONITOR_BACKUP_READ_TOKEN'),
            [v['repository'],policy['backup_target']['repository']],budget)
        result=monitor.check(source,code,backup,policy,int(time.time()*1000))
    except Exception: result=response('candidate_evidence_unavailable')
    result['budget']={'get':budget.requests,'put':0,'transport':0,
        'reserved_response_bytes':budget.requests*2*1024*1024}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--policy',required=True);a=p.parse_args()
    try: result=run(a.policy)
    except Exception: result=response('monitor_configuration_invalid')
    print(canonical(result));sys.exit(0 if result['http_status']==200 else 20)
