"""Run historical mutations against reached tests in a disposable checkout copy.

Every case gets a passing unmodified control immediately before the mutation.
Only an assertion in that same test counts as detection; missing templates,
other exceptions, timeouts and skipped cases remain explicit failures.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from a6_inventory import ROOT, cases as static_cases
from a6_contract_cases import cases as contract_cases

OVERRIDES = {
    'sabotage_e41:011': ('test_a6_regression', 'test_a6_e41_never_applies_waiting_rule_to_trailed_stop'),
    'sabotage_e434:003': ('test_a6_regression', 'test_a6_missing_btc_oi_does_not_create_movement'),
}

AUDIT = ROOT.parent / 'audit-work'
OUT = ROOT / 'docs/audit-nacharbeit-2026-10/A6-mutations.json'
PYTHON = sys.executable
ENV = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
DRIVER = '''import importlib,sys,traceback
try:
    importlib.import_module(sys.argv[1]).__dict__[sys.argv[2]]()
except AssertionError:
    traceback.print_exc()
    sys.exit(1)
except BaseException:
    traceback.print_exc()
    sys.exit(2)
'''


def dynamic_cases():
    answer = []
    for script in ('sabotage_e444.py', 'sabotage_e445.py'):
        tree = ast.parse((AUDIT / 'engine' / script).read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'FAELLE'
                            for t in n.targets))
        for index, (name, file, old, new, test) in enumerate(ast.literal_eval(node.value), 1):
            answer.append(dict(id=f'{script[:-3]}:{index:03d}', script=script,
                               name=name, file=file, old=old, new=new,
                               preferred_test=test))
    return answer


def original_names():
    found = {}
    logs = list((AUDIT / 'docs/audit-2026-09-27/sabotage-portabel').glob('*.log'))
    logs += list((AUDIT / 'docs/audit-2026-09-27/sabotage').glob('*.log'))
    for log in logs:
        content = log.read_text(encoding='utf-8', errors='replace')
        for name, tests in re.findall(r'OK  ([^\r\n]+)\s*\n\s*->[^\r\n]*?\| ([^\r\n]+)', content):
            found[(log.stem + '.py', name)] = [x.strip() for x in tests.split(', ')]
    additions = json.loads((AUDIT / 'docs/audit-2026-09-27/sabotage-ergaenzung.json')
                           .read_text(encoding='utf-8'))
    for row in additions:
        if row.get('failing_tests'):
            found[('sabotage_e443.py', row['name'])] = [
                x.split('::')[-1] for x in row['failing_tests']]
    return found


def tests_index():
    by_name = {}
    for path in (ROOT / 'engine').glob('test_*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                by_name.setdefault(node.name, []).append(path.stem)
    return by_name


def run_test(engine, module, name):
    try:
        result = subprocess.run([PYTHON, '-c', DRIVER, module, name], cwd=engine,
                                env=ENV, text=True, capture_output=True,
                                encoding='utf-8', timeout=120)
        return dict(exit_code=result.returncode,
                    tail=(result.stdout + result.stderr)[-1800:])
    except subprocess.TimeoutExpired as exc:
        return dict(exit_code=124, tail=str(exc))


def main():
    selected = sys.argv[1] if len(sys.argv) > 1 else None
    originals = original_names()
    index = tests_index()
    all_cases = static_cases + dynamic_cases() + contract_cases()
    rows = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else []
    done = {x['id'] for x in rows}
    with tempfile.TemporaryDirectory(prefix='btc-a6-mutations-') as tmp:
        root = Path(tmp)
        for sub in ('engine', 'site', 'docs', 'wissens-layer'):
            shutil.copytree(ROOT / sub, root / sub,
                            ignore=shutil.ignore_patterns('__pycache__', '.git'))
        for file in ROOT.glob('*.md'):
            shutil.copy2(file, root / file.name)
        engine = root / 'engine'
        for case in all_cases:
            if case['id'] in done or (selected and not case['id'].startswith(selected)):
                continue
            entry = {k: case[k] for k in ('id', 'script', 'name', 'file')}
            path = engine / case['file']
            if not path.exists():
                entry.update(matches=0, status='missing_file')
                rows.append(entry)
                OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
                print(entry['id'], entry['status'], flush=True)
                continue
            source = path.read_text(encoding='utf-8')
            old = case['old']
            entry['matches'] = source.count(old)
            if not entry['matches']:
                entry['status'] = 'missing_template'
            else:
                names = ([OVERRIDES[case['id']][1]] if case['id'] in OVERRIDES else
                         [case['preferred_test']] if 'preferred_test' in case else
                         originals.get((case['script'], case['name']), []))
                candidates = [(module, name) for name in names
                              for module in index.get(name, [])
                              if ('preferred_module' not in case or module == case['preferred_module'])
                              and (case['id'] not in OVERRIDES or module == OVERRIDES[case['id']][0])]
                entry['candidates'] = candidates
                if not candidates:
                    entry['status'] = 'no_mapped_test'
                else:
                    for module, name in candidates:
                        baseline = run_test(engine, module, name)
                        if baseline['exit_code'] != 0:
                            entry['status'] = 'baseline_failed'
                            entry['test'] = f'{module}::{name}'
                            entry['baseline'] = baseline
                            break
                        try:
                            path.write_text(source.replace(old, case['new'], 1), encoding='utf-8')
                            mutant = run_test(engine, module, name)
                        finally:
                            path.write_text(source, encoding='utf-8')
                        entry['test'] = f'{module}::{name}'
                        entry['baseline'] = baseline
                        entry['mutant'] = mutant
                        if mutant['exit_code'] == 1:
                            entry['status'] = 'caught_assertion'
                            break
                    else:
                        entry['status'] = 'survived_or_error'
            rows.append(entry)
            OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
            print(entry['id'], entry['status'], entry.get('test', ''), flush=True)
    from collections import Counter
    print('TOTAL', Counter(x['status'] for x in rows), flush=True)


if __name__ == '__main__':
    main()
