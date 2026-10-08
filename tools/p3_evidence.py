"""Local additive evidence helpers; never invokes historical entry points."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROTECTED = ('a1-work', 'rendite-pruefung-work', 'produktion-work', 'engine-integration-work')


def inventory():
    files, states = {}, {}
    for name in (*PROTECTED, 'audit-backups'):
        base = ROOT / name
        for p in sorted(base.rglob('*')):
            if p.is_file() and '.git' not in p.relative_to(base).parts:
                files[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
        if name in PROTECTED:
            def git(*args):
                return subprocess.check_output(['git', '-c', 'safe.directory='+base.as_posix(),
                    '-C', str(base), *args], text=True)
            states[name] = {'head': git('rev-parse', 'HEAD').strip(),
                'tree': git('rev-parse', 'HEAD^{tree}').strip(),
                'status': git('status', '--porcelain=v1', '--untracked-files=all')}
    return {'files': files, 'states': states}


if __name__ == '__main__':
    out = Path(sys.argv[2])
    if sys.argv[1] == 'before':
        result = inventory()
        out.parent.mkdir(parents=True, exist_ok=False)
    else:
        before = json.loads(Path(sys.argv[3]).read_text())
        after = inventory()
        changed = [p for p, h in before['files'].items() if after['files'].get(p) != h]
        new_protected = [p for p in after['files'] if p not in before['files']
            and p.split('/')[0] in PROTECTED]
        result = {'passed': not changed and not new_protected and before['states'] == after['states'],
            'checked_files': len(before['files']), 'changed': changed,
            'new_protected': new_protected, 'states': after['states']}
        assert result['passed'], result
    out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print({'files': len(result.get('files', {})), 'passed': result.get('passed')})
