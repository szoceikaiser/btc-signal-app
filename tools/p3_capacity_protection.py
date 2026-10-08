"""Additive local evidence inventory; no Git mutation or external access."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NAMES = ('a1-work', 'rendite-pruefung-work', 'produktion-work', 'engine-integration-work')

def inventory(exclude):
    paths = []
    for name in (*NAMES, 'audit-backups'):
        for parent, dirs, files in os.walk(ROOT/name):
            dirs[:] = [d for d in dirs if d != '.git' and Path(parent)/d != exclude]
            paths.extend(Path(parent)/f for f in files if f != '.git')
    def item(p):
        h = hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
        return p.relative_to(ROOT).as_posix(), h.hexdigest()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        hashes = dict(pool.map(item, paths))
    states = {}
    for name in (*NAMES, 'p3-betrieb-work'):
        def git(*args):
            return subprocess.check_output(['git', '-c', 'safe.directory='+(ROOT/name).as_posix(),
                '-C', str(ROOT/name), *args], text=True).strip()
        states[name] = dict(head=git('rev-parse','HEAD'), tree=git('rev-parse','HEAD^{tree}'),
                           status=git('status','--porcelain=v1','--untracked-files=all'))
    workflow = {p.relative_to(ROOT/'p3-betrieb-work').as_posix(): item(p)[1]
                for p in (ROOT/'p3-betrieb-work/.github/workflows').glob('*') if p.is_file()}
    return dict(files=hashes, states=states, workflows=workflow)

if __name__ == '__main__':
    out = Path(sys.argv[2]).resolve()
    data = inventory(out)
    if sys.argv[1] == 'before':
        out.mkdir(exist_ok=False)
        name = 'PROTECTED-BEFORE.json'
    else:
        old = json.loads((out/'PROTECTED-BEFORE.json').read_text())
        changed = [p for p,h in old['files'].items() if data['files'].get(p) != h]
        new = [p for p in data['files'] if p not in old['files']]
        data = dict(passed=not changed and not new and old['workflows']==data['workflows']
            and all(old['states'][n]==data['states'][n] for n in NAMES),
            checked_files=len(old['files']), changed=changed, new=new, states=data['states'],
            workflows=data['workflows'])
        assert data['passed'], data
        name = 'PROTECTED-AFTER.json'
    (out/name).write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    print(name, len(data.get('files',{})), data.get('passed'))
