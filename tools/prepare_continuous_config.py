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
    manifest_raw=(ROOT/'delivery-extension.json').read_bytes();manifest=json.loads(manifest_raw)
    template=(ROOT/'ops/continuous/recovery-workflow.template.yml').read_text()
    workflow=template.replace('LOADER_SHA256',manifest['files']['tools/pinned_delivery_entry.py']).replace('MANIFEST_SHA256',hashlib.sha256(manifest_raw).hexdigest())
    signal=(ROOT/'.github/workflows/signal.yml').read_text()
    bootstrap=next(line.strip() for line in signal.splitlines() if line.strip().startswith('python3 -c ')).split(' --runtime ')[0]
    command=bootstrap+' --tool continuous_operations.py -- --github --policy recovery-policy.json --result-file recovery-result.json'
    workflow=re.sub(r'(?m)^          python3 -c .+$',lambda match:'          '+command,workflow)
    (ROOT/'.github/workflows/recovery.yml').write_bytes(workflow.encode())
    value['recovery_entry']=dict(repository=policy['deployment']['code_repository'],branch='main',
        workflow='.github/workflows/recovery.yml',code_sha=policy['deployment']['code_sha'],
        workflow_sha256=hashlib.sha256(workflow.encode()).hexdigest())
    value['journal']=dict(repository=policy['deployment']['private_store_repository'],branch='recovery-journal-live',
        reviewed=False,seed_commit=None,public_access=None,credential_reference='github-fine-grained-pat:21186996',
        required_permissions={'contents':'write','metadata':'read'})
    a.recovery_output.write_bytes(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
    print('Disabled external pins and recovery config prepared; no activation')

if __name__=='__main__':main()
