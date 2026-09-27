"""Run every pre-existing sabotage runner to completion; logs stay on audit branch."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27/sabotage'
OUT.mkdir(parents=True,exist_ok=True)
results=[]
for p in sorted((ROOT/'engine').glob('sabotage_*.py')):
    start=time.monotonic()
    with (OUT/(p.stem+'.log')).open('w',encoding='utf-8') as f:
        r=subprocess.run([sys.executable,'-u',str(p)],cwd=ROOT/'engine',
                         env={**os.environ,'PYTHONUTF8':'1'},stdout=f,stderr=subprocess.STDOUT)
    results.append(dict(script=p.name,exit_code=r.returncode,seconds=time.monotonic()-start))
    (OUT/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(results[-1],flush=True)
sys.exit(int(any(x['exit_code'] for x in results)))
