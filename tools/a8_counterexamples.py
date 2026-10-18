"""Reproduce new A8 failures from the exact A7 Git blobs in memory."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT=Path(__file__).resolve().parents[1]
BASE='419e3fda6494645b3c227350f1b5145bffd6271a'
sys.path.insert(0,str(ROOT/'engine'))
import test_a8_acceptance as tests


def main():
    saved={k:tests.__dict__[k] for k in ('resample_daily','PerpBook','cz')}
    old={}
    sources={}
    for name in ('strategy_core','execution_perp_offline','coinalyze'):
        path='engine/'+name+'.py'
        raw=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
        sources[path]=hashlib.sha256(raw).hexdigest()
        module=types.ModuleType('a8_baseline_'+name)
        module.__file__=str(ROOT/path)
        sys.modules[module.__name__]=module
        exec(compile(raw,path,'exec'),module.__dict__)
        old[name]=module
    tests.resample_daily=old['strategy_core'].resample_daily
    tests.PerpBook=old['execution_perp_offline'].PerpBook
    tests.cz=old['coinalyze']
    rows=[]
    try:
        for name,fn in vars(tests).items():
            if name.startswith('test_'):
                try: fn()
                except AssertionError: rows.append(dict(test=name,before='reached AssertionError'))
                else: raise AssertionError('Counterexample did not fail: '+name)
    finally:
        tests.__dict__.update(saved)
    for row in rows:
        vars(tests)[row['test']]()
        row['after']='passed'
    result=dict(base_sha=BASE,original_git_blob_sha256=sources,cases=rows,
                old_files_modified=False,network_used=False)
    dest=ROOT/'docs/audit-nacharbeit-2026-10/A8-counterexamples-v1.json'
    raw=(json.dumps(result,indent=2)+'\n').encode()
    if dest.exists(): assert dest.read_bytes()==raw
    else: dest.write_bytes(raw)
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
