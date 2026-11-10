"""Offline non-secret config derivation after workflow materialization."""
import argparse
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reviewed-monitor',type=Path,required=True)
    parser.add_argument('--recovery-output',type=Path,required=True);a=parser.parse_args()
    policy=json.loads(a.reviewed_monitor.read_bytes())
    workflow=ROOT/'.github/workflows/freshness.yml';raw=workflow.read_bytes()
    guard=re.search(rb'expected = "([0-9a-f]{64})"',raw).group(1).decode()
    worker=ROOT/'external/worker.mjs';source=worker.read_text()
    source=re.sub(r'workflowSha256: "[a-f0-9]{64}"','workflowSha256: "'+hashlib.sha256(raw).hexdigest()+'"',source)
    source=re.sub(r'policyBindingSha256: "[a-f0-9]{64}"','policyBindingSha256: "'+guard+'"',source)
    assert 'enabled: false,' in source
    worker.write_bytes(source.encode())
    value=dict(schema='btc-continuous-recovery-v1',enabled=False,activation_reviewed=False,
               deployment=policy['deployment'],public_access=policy['public_access'],entry_workflows=policy['entry_workflows'])
    a.recovery_output.write_bytes(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
    print('Disabled external pins and recovery config prepared; no activation')

if __name__=='__main__':main()
