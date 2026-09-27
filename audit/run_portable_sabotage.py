"""Old POSIX mutation runners in isolated copies. Windows lacks SIGALRM.

Only the outer alarm API is bypassed. The original 600-second subprocess timeout,
mutations and test assertions are unchanged. Original platform failures are retained.
"""
import json,os,runpy,shutil,signal,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27/sabotage-portabel'
if len(sys.argv)>1:
    signal.SIGALRM=987654
    original_signal=signal.signal
    signal.signal=lambda sig,handler: None if sig==987654 else original_signal(sig,handler)
    signal.alarm=lambda secs: 0
    runpy.run_path(sys.argv[1],run_name='__main__')
else:
    OUT.mkdir(exist_ok=True)
    results=[]
    for p in sorted((ROOT/'engine').glob('sabotage_*.py')):
        if 'SIGALRM' not in p.read_text(encoding='utf-8'): continue
        t=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='btc-audit-mutation-') as temp:
            copied=Path(temp)/'engine'
            shutil.copytree(ROOT/'engine',copied,ignore=shutil.ignore_patterns('__pycache__'))
            # Tests read config/site/docs relative to engine. Copy repository tracked
            # supporting directories, excluding audit artefacts and private sources.
            for sub in ('site','docs','wissens-layer'):
                shutil.copytree(ROOT/sub,Path(temp)/sub,ignore=shutil.ignore_patterns('audit-2026-09-27'))
            for file in ROOT.glob('*.md'): shutil.copy2(file,Path(temp)/file.name)
            log=OUT/(p.stem+'.log')
            with log.open('w',encoding='utf-8') as f:
                r=subprocess.run([sys.executable,'-u',str(Path(__file__).resolve()),str(copied/p.name)],
                    cwd=copied,env={**os.environ,'PYTHONUTF8':'1'},stdout=f,stderr=subprocess.STDOUT)
            text=log.read_text(encoding='utf-8')
            results.append(dict(script=p.name,exit_code=r.returncode,seconds=time.monotonic()-t,
                caught=text.count('OK  '),survived=text.count('!!! UNGEFANGEN:'),
                missing=text.count('!! VORLAGE NICHT GEFUNDEN:'),tail=text.splitlines()[-4:]))
            (OUT/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
            print(results[-1],flush=True)
