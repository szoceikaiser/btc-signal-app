"""Read-only source inventory. Never copies private transcript contents."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/audit-2026-09-27'

def git(*args):
    return subprocess.check_output(['git', '-c', f'safe.directory={ROOT.as_posix()}', *args], cwd=ROOT).decode('utf-8')

def stamp(p, name):
    data = p.read_bytes()
    return dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                lines=len(data.splitlines()))

def main():
    tracked = git('ls-files').splitlines()
    files = [stamp(ROOT / p, p) for p in tracked if (ROOT / p).is_file()]
    private = [stamp(p, p.relative_to(ROOT.parent).as_posix())
               for p in sorted((ROOT.parent / 'Videos').rglob('*'))
               if p.is_file() and p.suffix.lower() in ('.txt', '.md', '.srt', '.vtt')]
    functions = []
    for p in sorted((ROOT / 'engine').glob('*.py')):
        tree = ast.parse(p.read_text(encoding='utf-8-sig'))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                functions.append(dict(file=p.relative_to(ROOT).as_posix(), name=node.name,
                                      line=node.lineno, end=node.end_lineno))
    result = dict(created=datetime.now(timezone.utc).isoformat(), head=git('rev-parse','HEAD').strip(),
                  refs=git('show-ref'), files=files, private_transcripts=private, functions=functions,
                  backtest_history=git('log','--all','--format=%H %aI %s','--','BACKTEST.md'))
    (OUT/'inventar.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Tracked files:',len(files),'private transcripts:',len(private),'functions/classes:',len(functions))

if __name__ == '__main__':
    main()
