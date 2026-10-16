"""Complete portable offline acceptance; uses installed dependencies only."""
import argparse,ast,json,platform,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import run_tests

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--jobs',type=int,default=4);a=p.parse_args()
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    versions={'python':sys.version,'platform':platform.platform()}
    import numpy
    versions['numpy']=numpy.__version__
    for binary in ('node','git'):
        exe=shutil.which(binary)
        if not exe:raise RuntimeError(binary+' is required')
        proc=subprocess.run([exe,'--version'],env=run_tests.environment(),capture_output=True,check=True)
        versions[binary]={'executable':exe,'version':proc.stdout.decode().strip()}
    (out/'VERSIONS.json').write_text(json.dumps(versions,indent=2)+'\n')
    print('ACTUAL_VERSIONS '+json.dumps(versions),flush=True)
    inventory=[m+'::'+n for m,n in run_tests.discover()]
    print('FUNCTION_INVENTORY '+json.dumps(inventory),flush=True)
    runs=[]
    stages=[('engine',[sys.executable,'-B',str(ROOT/'engine/run_tests.py'),'--out',str(out/'functions'),'--jobs',str(a.jobs)]),('statistics',[sys.executable,'-B',str(ROOT/'tools/test_historical_stats.py')]),('offline-mutations',[sys.executable,'-B',str(ROOT/'tools/verify_n6_probes.py')])]
    for label,command in stages:
        print('START',label,flush=True)
        with (out/(label+'.stdout.txt')).open('wb') as stdout,(out/(label+'.stderr.txt')).open('wb') as stderr:
            proc=subprocess.run(command,cwd=ROOT,env=run_tests.environment(),stdout=stdout,stderr=stderr)
        runs.append(dict(stage=label,returncode=proc.returncode,passed=proc.returncode==0))
        print(('PASS' if proc.returncode==0 else 'FAIL'),label,flush=True)
        if label=='engine':
            report=json.loads((out/'functions/RESULTS.json').read_text())
            print('FUNCTION_RESULT '+json.dumps({k:v for k,v in report.items() if k!='results'}),flush=True)
            for row in report['results']:
                print(('PASS ' if row['passed'] else 'FAIL ')+row['test'],flush=True)
                # Always show the seven safe P3 submodes and the real CLI AS
                # measurements, including when they pass. All workers are synthetic.
                diagnostic=('test_public_unknown_prior_mutation' in row['test'] or
                            'test_repeated_real_cli_memory_probe' in row['test'])
                if not row['passed'] or diagnostic:
                    print('DETAIL '+json.dumps(row),flush=True)
                    folder=out/'functions'/row['artifacts']
                    for stream in ('stdout','stderr'):
                        path=folder/(stream+'.txt')
                        if path.exists():
                            raw=path.read_bytes();print('::group::'+row['test']+' '+stream,flush=True)
                            print(raw[:65536].decode('utf-8',errors='replace'),flush=True)
                            if len(raw)>65536:print('TRUNCATED '+str(len(raw)-65536)+' bytes',flush=True)
                            print('::endgroup::',flush=True)
                    if diagnostic:
                        for path in folder.rglob('probe/RESULT.json'):
                            print('MEMORY_PROBE '+path.read_text()[:65536],flush=True)
        else:
            for stream in ('stdout','stderr'):
                raw=(out/(label+'.'+stream+'.txt')).read_bytes()
                print(label+' '+stream+' '+raw[:65536].decode('utf-8',errors='replace'),flush=True)
                if len(raw)>65536:print('TRUNCATED '+str(len(raw)-65536)+' bytes',flush=True)
    summary=dict(python=sys.version,platform=platform.platform(),offline=True,stages=runs,passed=all(r['passed'] for r in runs),provider_proof=False)
    summary['engine']=json.loads((out/'functions/RESULTS.json').read_text())
    tree=ast.parse((ROOT/'tools/test_historical_stats.py').read_text());summary['statistics_functions']=sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_') for n in tree.body)
    if runs[2]['passed']:summary['mutation_probes']=len(json.loads((out/'offline-mutations.stdout.txt').read_text())['probes'])
    (out/'ACCEPTANCE.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return int(not summary['passed'])

if __name__=='__main__':sys.exit(main())
