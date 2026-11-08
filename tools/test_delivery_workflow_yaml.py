"""Actual YAML regression, including exact parsed-shell preservation.

Development dependency: PyYAML==6.0.3. No network or workflow execution.
"""
import argparse
import json
from pathlib import Path
import subprocess
import yaml

ROOT=Path(__file__).resolve().parents[1]
PUBLISHED='8caee66b2231a765d15f1991eaf9039ee1e8cfb9'
NAMES=('signal','watch','lage','backup','backup-verify','pages','freshness')
AFFECTED=set(NAMES[:5])

def published(name):
    return subprocess.check_output(['git','-C',str(ROOT),'show',PUBLISHED+':.github/workflows/'+name+'.yml']).decode()
def runs(document):
    return [s['run'] for job in document['jobs'].values() for s in job['steps'] if 'run' in s]
def check(source=False):
    result={}
    for name in NAMES:
        text=published(name) if source else (ROOT/'.github/workflows'/f'{name}.yml').read_text()
        try: document=yaml.safe_load(text)
        except yaml.YAMLError as exc:
            if not source or name not in AFFECTED:raise
            result[name]=dict(ok=False,reason=exc.problem,line=exc.problem_mark.line+1)
            continue
        if source and name in AFFECTED:raise AssertionError('Published bug no longer reproduced: '+name)
        assert isinstance(document,dict) and isinstance(document['jobs'],dict)
        if name in AFFECTED:
            old=published(name)
            expected=[line[len('        run: '):] for line in old.splitlines() if line.startswith('        run: python3 -c ')]
            actual=[command for command in runs(document) if command.startswith('python3 -c ')]
            assert len(expected)==len(actual)==1 and actual==expected,(name,'Shell bytes changed')
            assert '        run: |-\n          python3 -c ' in text
        if name=='pages':
            assert runs(document)==runs(yaml.safe_load(published(name))), 'Pages commands changed'
        result[name]=dict(ok=True,exact_command=True if name in AFFECTED else None)
    if source:assert sum(not item['ok'] for item in result.values())==5
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--published-baseline',action='store_true')
    args=parser.parse_args()
    print(json.dumps(dict(parser='PyYAML '+yaml.__version__,published_baseline=args.published_baseline,
        workflows=check(args.published_baseline)),indent=2))
