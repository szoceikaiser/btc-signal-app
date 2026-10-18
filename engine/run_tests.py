"""Portable offline acceptance, fresh process/output/environment per function.

All top-level test functions are inventoried; loops are not extra test functions.
Use --jobs 1 for serial diagnostics. No dependency installation or remote access.
"""
import argparse,ast,importlib,json,os,platform,shutil,subprocess,sys,tempfile,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
ENGINE=Path(__file__).resolve().parent

def environment():
    keep=('PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','HOME','USERPROFILE','TMP','TEMP','TMPDIR')
    env={k:os.environ[k] for k in keep if k in os.environ}
    node=shutil.which('node')
    if not node:raise RuntimeError('Node is required; no JavaScript case may be skipped')
    env.update(BTC_TEST_NODE=node,GITHUB_TOKEN='offline-automatic-jobtoken',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',BTC_OFFLINE_TEST='1',PYTHONPATH=str(ENGINE/'offline_guard'))
    return env

def discover(modules=None):
    paths=sorted(ENGINE.glob('test_*.py'));found=[]
    unknown=set(modules or ())-{p.stem for p in paths}
    if unknown:raise ValueError('Unknown modules: '+str(sorted(unknown)))
    for path in paths:
        if modules and path.stem not in modules:continue
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in sorted((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')),key=lambda n:n.name):found.append((path.stem,node.name))
    return found

def worker(module,name,folder):
    sys.path[:0]=[str(ENGINE),str(ENGINE.parent/'tools'),str(ENGINE/'offline_guard')]
    import sitecustomize
    sitecustomize.install()
    mod=importlib.import_module(module)
    # Match module --out entrypoints. Betriebsabschluss creates its own root.
    for index,item in enumerate(list(sys.modules.values())):
        if getattr(item,'__file__',None) and Path(item.__file__).resolve().parent==ENGINE:
            for key in ('ARTIFACT_ROOT','OUT'):
                if hasattr(item,key):
                    root=Path(folder)/('m'+str(index))/key.lower();root.parent.mkdir(exist_ok=True);setattr(item,key,root)
                    if key=='OUT' or item.__name__=='test_hosted_backup':root.mkdir(exist_ok=True)
    getattr(mod,name)()

def run_one(index,module,name,out):
    folder=out/f'{index:04d}';folder.mkdir();start=time.monotonic()
    row=dict(index=index,test=module+'::'+name,artifacts=folder.name)
    try:
        proc=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--worker',module,name,str(folder)],cwd=folder,env=environment(),capture_output=True,timeout=1800)
        (folder/'stdout.txt').write_bytes(proc.stdout);(folder/'stderr.txt').write_bytes(proc.stderr)
        row.update(returncode=proc.returncode,passed=proc.returncode==0)
    except subprocess.TimeoutExpired as exc:
        (folder/'stdout.txt').write_bytes(exc.stdout or b'');(folder/'stderr.txt').write_bytes(exc.stderr or b'');row.update(passed=False,error='timeout-1800s')
    except Exception as exc:
        row.update(passed=False,error=type(exc).__name__+': '+str(exc))
    row['seconds']=round(time.monotonic()-start,3)
    return row

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out');p.add_argument('--module',nargs='+');p.add_argument('--jobs',type=int,default=4);p.add_argument('--worker',nargs=3)
    a=p.parse_args()
    if a.worker:worker(*a.worker);return 0
    if not 1<=a.jobs<=8:p.error('--jobs must be 1..8')
    inventory=discover(a.module)
    out=Path(a.out).resolve() if a.out else Path(tempfile.mkdtemp(prefix='btc-tests-'))/'results';out.mkdir(parents=True,exist_ok=False)
    (out/'INVENTORY.json').write_text(json.dumps([m+'::'+n for m,n in inventory],indent=2)+'\n',encoding='utf-8')
    report=dict(python=sys.version,platform=platform.platform(),offline=True,jobs=a.jobs,counting='top-level functions; internal loops are not additional tests',planned=len(inventory),results=[],passed=0,failed=0,skipped=0,complete=False)
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        pending=[pool.submit(run_one,i,m,n,out) for i,(m,n) in enumerate(inventory)]
        for done in as_completed(pending):
            row=done.result();report['results'].append(row);report['results'].sort(key=lambda r:r['index']);report['passed']+=row['passed'];report['failed']+=not row['passed'];report['complete']=len(report['results'])==len(inventory)
            (out/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print(('PASS ' if row['passed'] else 'FAIL ')+row['test'],flush=True)
    print(f"--- {report['passed']} passed, {report['failed']} failed, 0 skipped; {out}")
    return int(bool(report['failed']) or not report['complete'])

if __name__=='__main__':sys.exit(main())
