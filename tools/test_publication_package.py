"""Package-only checks: seven real entries, exact hashes, observer namespace.

No workflow, remote request, market access or message is executed.
"""
from pathlib import Path
import argparse,hashlib,json,shlex,subprocess,sys,tempfile,runpy
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'delivery-extension.json').read_bytes())
mh=hashlib.sha256((ROOT/'delivery-extension.json').read_bytes()).hexdigest()
for path,expected in manifest['files'].items():
    body=(ROOT/path).read_bytes()
    assert b'\r' not in body, path
    assert hashlib.sha256(body).hexdigest()==expected,path
lh=manifest['files']['tools/pinned_delivery_entry.py']
names=('signal','watch','lage','freshness','backup','backup-verify','pages')
for name in names:
    body=(ROOT/'.github/workflows'/f'{name}.yml').read_bytes();text=body.decode()
    assert b'\r' not in body,name
    commands=[line.strip().removeprefix('run: ') for line in text.splitlines() if 'python3 -c ' in line]
    assert len(commands)==(3 if name=='pages' else 1),(name,len(commands))
    for command in commands:
        tokens=shlex.split(command);assert tokens[:2]==['python3','-c']
        compile(tokens[2],'<workflow bootstrap>','exec')
        assert lh in tokens[2] and tokens[tokens.index('--manifest-sha256')+1]==mh
    assert 'path: extension' in text and 'persist-credentials: false' in text
    if name in ('signal','watch','lage'):
        assert 'working-directory: core' in text and '--runtime core/.runtime/runtime.json' in text
    if name=='freshness':
        assert 'path: observer' in text and 'path: core' in text
        assert 'working-directory: observer' in text and '--core ../core' in text and '--observer-root .' in text
    if name in ('backup','backup-verify','pages'): assert 'working-directory: core' in text
print('PASS all seven actual workflow paths, bootstrap syntax and manifest/module hashes')

def checkout(path,pin):
    path.mkdir();subprocess.check_output(['git','init',str(path)],stderr=subprocess.PIPE)
    objects=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--path-format=absolute','--git-path','objects'],text=True).strip()
    (path/'.git/objects/info/alternates').write_bytes(Path(objects).as_posix().encode()+b'\n')
    subprocess.check_output(['git','-C',str(path),'checkout','--detach',pin],stderr=subprocess.PIPE)

if __name__=='__main__':
    sys.path.insert(0,str(ROOT/'tools'))
    import pinned_delivery_entry as loader
    with tempfile.TemporaryDirectory() as tmp:
        core=Path(tmp)/'core';observer=Path(tmp)/'observer'
        checkout(core,loader.CORE);checkout(observer,'f3f054851f500af1926b149f13a2ee8890a8c2bc')
        (observer/'monitor-policy.json').write_text('{}')
        original=loader.install(core,ROOT,mh)
        seen=[]
        def inspect_reader(path,run_name):
            assert Path(path).resolve()==observer/'tools/produktion_actions_freshness.py'
            entry=sys.modules['produktion_actions_runner']
            assert entry.ROOT==observer
            entry.check_code_pin('f3f054851f500af1926b149f13a2ee8890a8c2bc')
            seen.append(True)
        args=['entry','--core',str(core),'--extension',str(ROOT),'--manifest-sha256',mh,
              '--tool','produktion_actions_freshness.py','--observer-root',str(observer),'--','--policy','monitor-policy.json']
        with patch.object(sys,'argv',args),patch.object(runpy,'run_path',side_effect=inspect_reader):
            assert loader.main()==0
        assert seen and sys.modules['produktion_actions_runner'] is original
        original.check_code_pin(loader.CORE)
        print('PASS real clean observer pin remains independent from real clean strategy pin; namespace restored')
