"""Public data monitor; automatic codejob token only for code metadata."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import actions_freshness as monitor
import public_access as public
from github_freshness import ReadBudget
from production_contract import canonical
from freshness import response


def run(path):
    with Path(path).open('rb') as f: raw=f.read(128*1024+1)
    if len(raw)>128*1024: return response('monitor_configuration_invalid')
    policy=json.loads(raw)
    if policy.get('enabled') is not True: return response('monitor_disabled')
    if policy.get('python_version') and tuple(policy['python_version'])!=sys.version_info[:3]:
        return response('monitor_configuration_invalid')
    d=policy['deployment'];v=policy['independent_verifier'];budget=ReadBudget()
    try:
        public.deployment(policy['public_access'],d)
        if policy.get('monitor_entry'):
            from reviewed_actions_entry import EntryReader,actual
            from produktion_actions_runner import check_code_pin
            t=policy['monitor_entry'];check_code_pin(t['code_sha'])
            actual(EntryReader(os.environ.get('GITHUB_TOKEN'),t['repository']),
                   t['repository'],'refs/heads/'+t['branch'],t['code_sha'],t['workflow'],t['workflow_sha256'])
        source=monitor.Reader(None,[d['private_store_repository']],budget)
        code=monitor.Reader(os.environ.get('GITHUB_TOKEN'),
            [d['code_repository'],v['binding']['repository']],budget,metadata=True)
        public.check(code,policy['public_access'],[(d['code_repository'],d['code_ref'].removeprefix('refs/heads/'))])
        backup=monitor.Reader(None,
            [v['repository'],policy['backup_target']['repository']],budget)
        branches=[(d['private_store_repository'],b) for b in (d['store_branch'],d['fence_branch'])]
        public.check(source,policy['public_access'],branches,branches)
        branches=[(v['repository'],v['receipt_branch']),
                  (policy['backup_target']['repository'],policy['backup_target']['branch'])]
        public.check(backup,policy['public_access'],branches,branches)
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
