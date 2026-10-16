"""Complete portable offline acceptance; uses installed dependencies only."""
import argparse,ast,json,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import run_tests

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--jobs',type=int,default=4);a=p.parse_args()
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    runs=[]
    stages=[('engine',[sys.executable,'-B',str(ROOT/'engine/run_tests.py'),'--out',str(out/'functions'),'--jobs',str(a.jobs)]),('statistics',[sys.executable,'-B',str(ROOT/'tools/test_historical_stats.py')]),('offline-mutations',[sys.executable,'-B',str(ROOT/'tools/verify_n6_probes.py')])]
    for label,command in stages:
        print('START',label,flush=True)
        with (out/(label+'.stdout.txt')).open('wb') as stdout,(out/(label+'.stderr.txt')).open('wb') as stderr:
            proc=subprocess.run(command,cwd=ROOT,env=run_tests.environment(),stdout=stdout,stderr=stderr)
        runs.append(dict(stage=label,returncode=proc.returncode,passed=proc.returncode==0))
        print(('PASS' if proc.returncode==0 else 'FAIL'),label,flush=True)
    summary=dict(python=sys.version,platform=platform.platform(),offline=True,stages=runs,passed=all(r['passed'] for r in runs),provider_proof=False)
    summary['engine']=json.loads((out/'functions/RESULTS.json').read_text())
    tree=ast.parse((ROOT/'tools/test_historical_stats.py').read_text());summary['statistics_functions']=sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_') for n in tree.body)
    if runs[2]['passed']:summary['mutation_probes']=len(json.loads((out/'offline-mutations.stdout.txt').read_text())['probes'])
    (out/'ACCEPTANCE.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return int(not summary['passed'])

if __name__=='__main__':sys.exit(main())
