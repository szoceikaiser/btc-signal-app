"""Exact-SHA bundle/ZIP/full tree restore, all tests, probes and six frozen runs."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
from verify_4_backup import git, sha
from verify_6 import secured
from verify_6_scope import BASE, BRANCH, TAG

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT/'docs/nacharbeit-2026-09-28'

def main():
    commit = git(ROOT, 'rev-parse', 'HEAD').decode().strip()
    assert git(ROOT, 'branch', '--show-current').decode().strip() == BRANCH
    assert not git(ROOT, 'status', '--porcelain').strip()
    backup = ROOT.parent/'audit-backups'/('6-abschluss-'+commit[:7])
    backup.mkdir(parents=True, exist_ok=True)
    ci = json.loads((backup/'github-ci.json').read_text(encoding='utf-8-sig'))
    assert ci['commit'] == commit and ci['tests_success'] and ci['branch'] == BRANCH
    assert ci['tag_object'] == '7d78094c17624b90b8f7ebc387b96570ff2c8ef7'
    assert ci['tag_target'] == '469be65f65327a3b6abf2794ceba09c1fe0de9e2'
    assert ci['runs'] and all(r['head_sha'] == commit and r['name'] == 'Tests' and r['conclusion'] == 'success' and r['event'] == 'push' for r in ci['runs'])
    prior = ROOT.parent/'audit-backups/5b-abschluss-bb86220'
    previous, inputs, _ = secured(prior)
    frozen = backup/'eingefrorene-inputs'
    frozen.mkdir(exist_ok=True)
    for name, expected in previous['frozen_hashes'].items():
        (frozen/name).write_bytes((inputs/name).read_bytes())
        assert sha(frozen/name) == expected
    bundle, archive = backup/'abschluss.bundle', backup/'abschluss.zip'
    if not bundle.exists(): git(ROOT, 'bundle', 'create', str(bundle), 'refs/heads/'+BRANCH, 'refs/tags/'+TAG)
    check = subprocess.run(['git', '-c', f'safe.directory={ROOT.as_posix()}', 'bundle', 'verify', str(bundle)], cwd=ROOT, capture_output=True, check=True)
    (backup/'bundle-verify.log').write_bytes(check.stdout+check.stderr)
    refs = git(ROOT, 'bundle', 'list-heads', str(bundle)).decode().splitlines()
    assert len(refs) == 2 and commit+' refs/heads/'+BRANCH in refs
    if not archive.exists(): git(ROOT, 'archive', '--format=zip', '--output='+str(archive), commit)
    expected_zip = zipfile.ZipFile(io.BytesIO(git(ROOT, 'archive', '--format=zip', commit)))
    files = git(ROOT, 'ls-tree', '-r', '--name-only', commit).decode().splitlines()
    tree = {}
    with zipfile.ZipFile(archive) as z:
        assert {n for n in z.namelist() if not n.endswith('/')} == set(files)
        for path in files:
            blob = expected_zip.read(path)
            assert z.read(path) == blob, path
            tree[path] = hashlib.sha256(blob).hexdigest()
    (backup/'git-tree-sha256.json').write_text(json.dumps(tree, indent=2), encoding='utf-8')
    restored = backup/'wiederherstellung'
    if not restored.exists(): git(backup, 'clone', '--branch', BRANCH, str(bundle), str(restored))
    assert git(restored, 'rev-parse', 'HEAD').decode().strip() == commit
    git(restored, 'remote', 'set-url', 'origin', 'https://github.com/szoceikaiser/btc-signal-app.git')
    git(restored, 'fsck', '--full')
    assert git(restored, 'rev-parse', TAG+'^{}').decode().strip() == ci['tag_target']
    restored_zip = zipfile.ZipFile(io.BytesIO(git(restored, 'archive', '--format=zip', 'HEAD')))
    assert set(git(restored, 'ls-tree', '-r', '--name-only', 'HEAD').decode().splitlines()) == set(files)
    for path in files:
        assert hashlib.sha256(restored_zip.read(path)).hexdigest() == tree[path]
    assert not git(restored, 'status', '--porcelain').strip()
    print('Bundle/ZIP/full restored Git tree PASS', flush=True)
    def proof(script, name, *args):
        proc = subprocess.run([sys.executable, str(restored/script), *map(str, args)], cwd=restored,
            env={**os.environ, 'PYTHONUTF8':'1', 'TELEGRAM_BOT_TOKEN':'', 'TELEGRAM_CHAT_ID':''}, capture_output=True)
        (backup/name).write_bytes(proc.stdout)
        (backup/(name+'.stderr')).write_bytes(proc.stderr)
        assert proc.returncode == 0, (script, proc.stderr.decode(errors='replace'))
        return proc.stdout
    assert b'728 passed, 0 failed' in proof(Path('engine/run_tests.py'), 'wiederherstellung-tests.log')
    print('Restored 728 tests PASS', flush=True)
    for script, saved in [('tools/verify_5b_probes.py', '5b-sabotage.json'),
            ('tools/verify_5b_v1.py', '5b-v1-projection.json'),
            ('engine/sabotage_5a.py', '5b-5a-sabotage.json'),
            ('engine/sabotage_4.py', '5b-4-sabotage.json'),
            ('engine/sabotage_3b.py', '5b-3b-sabotage.json')]:
        assert json.loads(proof(Path(script), 'wiederherstellung-'+saved)) == json.loads((DOC/saved).read_text())
    for script in ['engine/sabotage_d01.py', 'engine/sabotage_f09.py']:
        proof(Path(script), 'wiederherstellung-'+Path(script).stem+'.log')
    scope = json.loads(proof(Path('tools/verify_6_scope.py'), 'wiederherstellung-scope.json'))
    assert scope['head'] == commit
    design = json.loads(proof(Path('tools/verify_6_design.py'), 'wiederherstellung-design.json'))
    print('All inherited protection probes and design/scope PASS', flush=True)
    output = backup/'wiederherstellung-reproduktion'
    proof(Path('tools/verify_6.py'), 'wiederherstellung-messung.log', '--prior-backup', prior, '--out-dir', output)
    assert json.loads((output/'6-ergebnis.json').read_text()) == json.loads((DOC/'6-ergebnis.json').read_text())
    assert (output/'6-ledger.json.gz').read_bytes() == (DOC/'6-ledger.json.gz').read_bytes()
    print('Six restored full causal runs identical; independent accounts PASS', flush=True)
    report = json.loads((DOC/'6-ergebnis.json').read_text())
    replays = []
    for i, summary in enumerate(report['summaries']):
        with gzip.open(restored/f'docs/nacharbeit-2026-09-28/4-restart-{i}.json.gz', 'rt', encoding='utf-8') as f:
            payload = json.load(f)
        payload['input_path'] = str(frozen/'eingaben.json')
        cp = backup/f'wiederherstellung-checkpoint-{i}.json.gz'
        with gzip.open(cp, 'wt', encoding='utf-8') as f: json.dump(payload, f, allow_nan=False)
        replay = json.loads(proof(Path('tools/verify_4_resume.py'), f'wiederherstellung-replay-{i}.json', cp))
        assert replay['sha256'] == summary['sha256']
        replays.append(dict(name=summary['name'], slippage_pct=summary['slippage_pct'], **replay))
        print(f'Restored checkpoint {i+1}/6 identical', flush=True)
    assert not git(ROOT, 'status', '--porcelain').strip()
    assert not git(restored, 'status', '--porcelain').strip()
    changed = git(ROOT, 'diff', '--name-only', BASE, commit).decode().splitlines()
    registry = json.loads((DOC/'6-design-register.json').read_text())
    result = dict(stage='6 Reproduktion und Bestätigungsdesign gesichert', commit=commit, branch=BRANCH, base=BASE,
        local_tests=728, baseline_tests=728, new_tests=0, old_test_changes='none', github=ci,
        bundle_restore_verified=True, full_tree_verified=True, zip_verified=True, restored_tests=728,
        restored_full_comparisons=6, restored_independent_comparisons=6, restored_fills=1101, restored_closes=9054,
        restored_protection_probes=dict(f17=16, f13=16, stage4=23, stage3b=19, d01=6, f09=3),
        process_replays=replays, design_status=registry['status'], decisions=registry['decisions'],
        confirmation_measurements=0, live_go=False, implementation_registration_complete=False,
        frozen_hashes=previous['frozen_hashes'], changed_files_sha256={p:tree[p] for p in changed},
        backup_sha256={'abschluss.bundle':sha(bundle), 'abschluss.zip':sha(archive)},
        report='docs/nacharbeit-2026-09-28/ETAPPE-6-ABSCHLUSS.md',
        boundaries=['Only model reproduction; no economic confirmation', 'Future design needs prior registration and as-of data',
            'No live-go; manual live holdings unknown', 'No exactly-once guarantee; uncertain delivery blocks',
            'Ephemeral runner loss before Git persistence remains open', 'V2/Shorts/E41.6/other findings separate'],
        next_assignment='Separate design registration/technical feasibility only; START-NACH-6.md; do not auto-start')
    (backup/'ABSCHLUSS.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    (backup/'START-NACH-6.md').write_text(f'Gesicherter Etappe-6-Commit: `{commit}`\n\n'+(DOC/'START-NACH-6.md').read_text(encoding='utf-8'), encoding='utf-8')
    (backup/'README.md').write_text(f'# Etappe 6 gesichert\n\nCommit `{commit}`, Zweig `{BRANCH}`.\n\nDesign: {registry["status"]}.\nABSCHLUSS.json: exakte Remote-/CI-/Restore-Belege. Bundle und ZIP geprüft.\nKeine Bestätigungsmessung und kein Live-Go. Folgeauftrag nur separat.\n', encoding='utf-8')
    print(json.dumps(dict(commit=commit, backup=str(backup), verified=True, tests=728, design_status=registry['status']), indent=2))

if __name__ == '__main__': main()
