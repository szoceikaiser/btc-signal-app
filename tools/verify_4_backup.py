"""Local full-tree bundle/ZIP restoration and isolated-process replay proof.

Run only after commit, remote exact-SHA CI proof saved as github-ci.json in the
computed backup directory. No network, push, private repository commit or delete.
"""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = '9606a6f555f9cdaee86f9c33a5175c5c5306b365'
BRANCH = 'codex/etappe-4-bestand-stop'
TAG = 'sicherung/vor-audit-korrekturen-2026-09-28'
AUDIT = ROOT.parent/'audit-work'


def git(root, *args):
    return subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}', *args],
                          cwd=root, capture_output=True, check=True).stdout


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    commit = git(ROOT, 'rev-parse', 'HEAD').decode().strip()
    assert git(ROOT, 'branch', '--show-current').decode().strip() == BRANCH
    assert not git(ROOT, 'status', '--porcelain').strip()
    backup = ROOT.parent/'audit-backups'/('4-abschluss-'+commit[:7])
    backup.mkdir(parents=True, exist_ok=True)
    ci = json.loads((backup/'github-ci.json').read_text(encoding='utf-8-sig'))
    assert ci['commit'] == commit and ci['tests_success']
    assert ci['tag_object'] == '7d78094c17624b90b8f7ebc387b96570ff2c8ef7'
    assert ci['tag_target'] == '469be65f65327a3b6abf2794ceba09c1fe0de9e2'
    assert ci['runs'] and all(r['head_sha'] == commit and r['conclusion'] == 'success'
                             and r['name'] == 'Tests' for r in ci['runs'])
    bundle, archive = backup/'abschluss.bundle', backup/'abschluss.zip'
    if not bundle.exists():
        git(ROOT, 'bundle', 'create', str(bundle), 'refs/heads/'+BRANCH, 'refs/tags/'+TAG)
    checked = subprocess.run(['git', '-c', f'safe.directory={ROOT.as_posix()}',
        'bundle', 'verify', str(bundle)], cwd=ROOT, capture_output=True, check=True)
    (backup/'bundle-verify.log').write_bytes(checked.stdout+checked.stderr)
    refs = git(ROOT, 'bundle', 'list-heads', str(bundle)).decode().splitlines()
    assert len(refs) == 2 and commit+' refs/heads/'+BRANCH in refs
    if not archive.exists():
        git(ROOT, 'archive', '--format=zip', '--output='+str(archive), commit)
    files = git(ROOT, 'ls-tree', '-r', '--name-only', commit).decode().splitlines()
    manifest = {}
    with zipfile.ZipFile(archive) as z:
        assert {n for n in z.namelist() if not n.endswith('/')} == set(files)
        for path in files:
            data = git(ROOT, 'show', commit+':'+path)
            assert z.read(path) == data, path
            manifest[path] = hashlib.sha256(data).hexdigest()
    (backup/'git-tree-sha256.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    restored = backup/'wiederherstellung'
    if not restored.exists():
        git(backup, 'clone', '--branch', BRANCH, str(bundle), str(restored))
    assert git(restored, 'rev-parse', 'HEAD').decode().strip() == commit
    git(restored, 'remote', 'set-url', 'origin', 'https://github.com/szoceikaiser/btc-signal-app.git')
    git(restored, 'fsck', '--full')
    assert git(restored, 'rev-parse', TAG+'^{}').decode().strip() == ci['tag_target']
    for path in files:
        actual = git(restored, 'hash-object', '--path='+path, path).decode().strip()
        expected = git(ROOT, 'rev-parse', commit+':'+path).decode().strip()
        assert actual == expected, path

    def proof(script, name, *args):
        proc = subprocess.run([sys.executable, str(restored/script), *map(str, args)],
            cwd=restored, env={**os.environ, 'PYTHONUTF8': '1'}, capture_output=True)
        (backup/name).write_bytes(proc.stdout)
        (backup/(name+'.stderr')).write_bytes(proc.stderr)
        assert proc.returncode == 0, (script, proc.stderr.decode('utf-8', errors='replace'))
        return proc.stdout

    assert b'676 passed, 0 failed' in proof(Path('engine/run_tests.py'), 'wiederherstellung-tests.log')
    for script, saved in [('engine/sabotage_4.py', '4-sabotage.json'),
                          ('engine/sabotage_3b.py', '4-3b-sabotage.json')]:
        actual = json.loads(proof(Path(script), 'wiederherstellung-'+saved))
        assert actual == json.loads((ROOT/'docs/nacharbeit-2026-09-28'/saved).read_text(encoding='utf-8'))
    scope = json.loads(proof(Path('tools/verify_4_scope.py'), 'wiederherstellung-scope.json'))
    assert scope['head'] == commit
    frozen = backup/'eingefrorene-inputs'
    frozen.mkdir(exist_ok=True)
    for path, name in [('docs/e445/eingaben.json', 'eingaben.json'),
                       ('docs/e445/signale.json', 'signale.json'),
                       ('docs/e445/ergebnis.json', 'ergebnis.json'), ('audit/book.py', 'book.py')]:
        data = (AUDIT/path).read_bytes()
        original = git(AUDIT, 'show', 'ccf2b01c0578346f325261e72445b7375a9ac706:'+path)
        assert data == original or data.replace(b'\r\n', b'\n') == original
        (frozen/name).write_bytes(data)
    report = json.loads((restored/'docs/nacharbeit-2026-09-28/4-ergebnis.json').read_text(encoding='utf-8'))
    assert sha(frozen/'eingaben.json') == report['frozen_hashes']['docs/e445/eingaben.json']
    # Independent Decimal costs again, using the restored verifier and saved fills.
    spec = importlib.util.spec_from_file_location('restored_cost_check', restored/'tools/verify_4.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    with gzip.open(restored/'docs/nacharbeit-2026-09-28/4-ledger.json.gz', 'rt', encoding='utf-8') as stream:
        rows = json.load(stream)
    costs = [checker.independent_costs(s['result']) for row in rows for s in row['scenarios']]
    assert costs == [s['costs_verified'] for s in report['summaries']]
    replays = []
    for i, summary in enumerate(report['summaries']):
        cp = restored/f'docs/nacharbeit-2026-09-28/4-restart-{i}.json.gz'
        with gzip.open(cp, 'rt', encoding='utf-8') as stream:
            payload = json.load(stream)
        payload['input_path'] = str(frozen/'eingaben.json')
        local_cp = backup/f'wiederherstellung-checkpoint-{i}.json.gz'
        with gzip.open(local_cp, 'wt', encoding='utf-8') as stream:
            json.dump(payload, stream, allow_nan=False)
        replay = json.loads(proof(Path('tools/verify_4_resume.py'), f'wiederherstellung-replay-{i}.json', local_cp))
        assert replay['sha256'] == summary['restart_sha256']
        replays.append(dict(name=summary['name'], slippage_pct=summary['slippage_pct'], **replay))
        print(f'Restored scenario {i+1}/6 identical', flush=True)
    (backup/'wiederherstellung-losabgleich.json').write_text(json.dumps(costs, indent=2), encoding='utf-8')
    git(restored, 'diff', '--exit-code', commit)
    assert not git(restored, 'status', '--porcelain').strip()
    assert not git(ROOT, 'status', '--porcelain').strip()
    changed = git(ROOT, 'diff', '--name-only', BASE, commit).decode().splitlines()
    result = dict(stage='4 abgeschlossen', commit=commit, branch=BRANCH, base=BASE,
        local_tests=676, baseline_tests=638, new_tests=38,
        old_test_changes='Two E42 fixtures, two F03/F10 expectations, one isolated E433 test configuration; see report',
        sabotages_4=23, sabotages_3b=19, d01_sabotages=6, f09_sabotages=3,
        frozen_comparisons=6, github=ci, bundle_restore_verified=True,
        full_tree_verified=True, zip_verified=True, restored_tests=676,
        restore_probes_identical=True, restored_independent_comparisons=6,
        process_replays=replays, backup_sha256={'abschluss.bundle': sha(bundle), 'abschluss.zip': sha(archive)},
        frozen_hashes={p.name: sha(p) for p in frozen.iterdir() if p.is_file()},
        changed_files_sha256={p: manifest[p] for p in changed},
        report='docs/nacharbeit-2026-09-28/ETAPPE-4-ABSCHLUSS.md',
        boundaries=['No main/live/dispatch changes', 'Manual live holdings remain unknown',
                    'Legacy signal reference is not actual acquisition cost',
                    'Pre-migration stop maxima cannot be reconstructed',
                    'F13 remains 5a; F17 remains 5b; V2/shorts/E41.6 excluded'],
        next_stage='Separate Etappe 5a: GPT-6 Sol / hoch; no automatic start')
    (backup/'ABSCHLUSS.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    prompt = (restored/'docs/nacharbeit-2026-09-28/START-5A.md').read_text(encoding='utf-8')
    (backup/'START-5A.md').write_text(f'Gesicherter Abschlusscommit: `{commit}`\n\n'+prompt, encoding='utf-8')
    (backup/'README.md').write_text(
        f'# Etappe 4 gesichert\n\nCommit `{commit}`; Zweig `{BRANCH}`.\n\n'
        'ABSCHLUSS.json enthält exakte Remote-/CI- und Wiederherstellungsbelege. '
        'abschluss.bundle und abschluss.zip sind vollständig geprüft. '
        'Keine automatische Live-Übernahme; nächster Auftrag separat START-5A.md.\n', encoding='utf-8')
    print(json.dumps(dict(commit=commit, backup=str(backup), verified=True, tests=676,
                         replays=6, hashes=result['backup_sha256']), indent=2))


if __name__ == '__main__':
    main()
