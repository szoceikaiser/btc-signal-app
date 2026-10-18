"""Snapshot and verify workflow triggers before any A6 branch push."""
import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
git = ['git', '-c', 'safe.directory=' + root.as_posix()]
remote_sha = subprocess.check_output(git + ['rev-parse', 'origin/main'], cwd=root,
                                     text=True).strip()


def trigger_block(body):
    lines = body.splitlines()
    start = next(i for i, line in enumerate(lines) if line == 'on:')
    end = next((i for i in range(start + 1, len(lines))
                if lines[i] and not lines[i].startswith((' ', '#'))), len(lines))
    return '\n'.join(lines[start:end])


paths = sorted((root / '.github/workflows').glob('*.yml'))
assert len(paths) == 8
rows = {'local': {}, 'default_branch': {}}
for path in paths:
    relative = path.relative_to(root).as_posix()
    local = path.read_text(encoding='utf-8')
    remote = subprocess.check_output(git + ['show', 'origin/main:' + relative],
                                     cwd=root).decode('utf-8')
    for label, body in (('local', local), ('default_branch', remote)):
        rows[label][path.name] = dict(sha256=hashlib.sha256(body.encode()).hexdigest(),
                                      triggers=trigger_block(body))
for label, files in rows.items():
    assert len(files) == 8
    assert 'workflow_run:' not in files['tests.yml']['triggers']
    for name, row in files.items():
        trigger = row['triggers']
        if name != 'tests.yml':
            assert 'push:' not in trigger or (name == 'pages.yml' and
                                              'branches: [main]' in trigger)
        if 'workflow_run:' in trigger:
            assert name == 'pages.yml'
            assert 'workflows: ["Signal-Engine", "Backtest"]' in trigger
    assert all('workflows: ["Tests"]' not in row['triggers'] for row in files.values())
assert 'push:' in rows['local']['tests.yml']['triggers']
out = dict(default_branch_sha=remote_sha, branch='codex/a1-audit-nacharbeit',
           workflow_count=8, local_equals_current_default=(rows['local'] == rows['default_branch']),
           only_branch_push_workflow='tests.yml',
           tests_has_no_workflow_run_successor=True, workflows=rows)
target = root / 'docs/audit-nacharbeit-2026-10/A6-prepush-workflows.json'
target.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in out.items() if k != 'workflows'}, indent=2))
