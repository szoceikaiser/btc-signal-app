"""Bundle/ZIP/full-tree restoration, offline suites and saved V1 process replays."""
import gzip
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
from verify_4_backup import git, sha

ROOT = Path(__file__).resolve().parents[1]
BASE = 'ebc01a48057994629c021bd84ab7f9a236678b70'
BRANCH = 'codex/etappe-5a-telegram-outbox'
TAG = 'sicherung/vor-audit-korrekturen-2026-09-28'

def main():
    commit = git(ROOT,'rev-parse','HEAD').decode().strip()
    assert git(ROOT,'branch','--show-current').decode().strip() == BRANCH
    assert not git(ROOT,'status','--porcelain').strip()
    backup = ROOT.parent/'audit-backups'/('5a-abschluss-'+commit[:7]); backup.mkdir(exist_ok=True)
    ci = json.loads((backup/'github-ci.json').read_text(encoding='utf-8-sig'))
    assert ci['commit'] == commit and ci['tests_success']
    assert ci['tag_object'] == '7d78094c17624b90b8f7ebc387b96570ff2c8ef7'
    assert ci['tag_target'] == '469be65f65327a3b6abf2794ceba09c1fe0de9e2'
    assert ci['runs'] and all(r['head_sha']==commit and r['name']=='Tests' and r['conclusion']=='success' for r in ci['runs'])
    bundle, archive = backup/'abschluss.bundle', backup/'abschluss.zip'
    if not bundle.exists(): git(ROOT,'bundle','create',str(bundle),'refs/heads/'+BRANCH,'refs/tags/'+TAG)
    checked = subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}','bundle','verify',str(bundle)],cwd=ROOT,capture_output=True,check=True)
    (backup/'bundle-verify.log').write_bytes(checked.stdout+checked.stderr)
    refs = git(ROOT,'bundle','list-heads',str(bundle)).decode().splitlines()
    assert len(refs)==2 and commit+' refs/heads/'+BRANCH in refs
    if not archive.exists(): git(ROOT,'archive','--format=zip','--output='+str(archive),commit)
    files = git(ROOT,'ls-tree','-r','--name-only',commit).decode().splitlines()
    manifest = {}
    with zipfile.ZipFile(archive) as z:
        assert {n for n in z.namelist() if not n.endswith('/')} == set(files)
        for path in files:
            blob = git(ROOT,'show',commit+':'+path)
            assert z.read(path)==blob, path
            import hashlib
            manifest[path]=hashlib.sha256(blob).hexdigest()
    (backup/'git-tree-sha256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('ZIP and complete Git tree verified',flush=True)
    restored = backup/'wiederherstellung'
    if not restored.exists(): git(backup,'clone','--branch',BRANCH,str(bundle),str(restored))
    assert git(restored,'rev-parse','HEAD').decode().strip()==commit
    git(restored,'remote','set-url','origin','https://github.com/szoceikaiser/btc-signal-app.git')
    git(restored,'fsck','--full')
    assert git(restored,'rev-parse',TAG+'^{}').decode().strip()==ci['tag_target']
    for path in files:
        assert git(restored,'hash-object','--path='+path,path).strip()==git(ROOT,'rev-parse',commit+':'+path).strip(),path
    print('Bundle restore complete tree verified',flush=True)
    def proof(script,name,*args):
        proc = subprocess.run([sys.executable,str(restored/script),*map(str,args)],cwd=restored,
            env={**os.environ,'PYTHONUTF8':'1','TELEGRAM_BOT_TOKEN':'','TELEGRAM_CHAT_ID':''},capture_output=True)
        (backup/name).write_bytes(proc.stdout); (backup/(name+'.stderr')).write_bytes(proc.stderr)
        assert proc.returncode==0,(script,proc.stderr.decode(errors='replace'))
        return proc.stdout
    assert b'712 passed, 0 failed' in proof(Path('engine/run_tests.py'),'wiederherstellung-tests.log')
    for script,saved in [('engine/sabotage_5a.py','5a-sabotage.json'),
                         ('engine/sabotage_4.py','5a-4-sabotage.json'),
                         ('engine/sabotage_3b.py','5a-3b-sabotage.json')]:
        assert json.loads(proof(Path(script),'wiederherstellung-'+saved)) == json.loads((ROOT/'docs/nacharbeit-2026-09-28'/saved).read_text())
    for script,saved in [('engine/sabotage_d01.py','5a-d01-sabotage.log'),('engine/sabotage_f09.py','5a-f09-sabotage.log')]:
        proof(Path(script),'wiederherstellung-'+saved)
    scope=json.loads(proof(Path('tools/verify_5a_scope.py'),'wiederherstellung-scope.json'))
    assert scope['head']==commit
    print('Restored 712 tests and all targeted sabotages passed',flush=True)
    # Restore frozen external inputs from the verified stage-4 backup, not newer branches.
    prior=ROOT.parent/'audit-backups/4-abschluss-ebc01a4'
    prior_result=json.loads((prior/'ABSCHLUSS.json').read_text())
    assert prior_result['commit']==BASE and prior_result['bundle_restore_verified']
    frozen=backup/'eingefrorene-inputs'; frozen.mkdir(exist_ok=True)
    for source in (prior/'eingefrorene-inputs').iterdir():
        if source.is_file():
            assert sha(source)==prior_result['frozen_hashes'][source.name]
            (frozen/source.name).write_bytes(source.read_bytes())
    report=json.loads((restored/'docs/nacharbeit-2026-09-28/4-ergebnis.json').read_text())
    assert sha(frozen/'eingaben.json')==report['frozen_hashes']['docs/e445/eingaben.json']
    spec=importlib.util.spec_from_file_location('restored_cost_check',restored/'tools/verify_4.py')
    checker=importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
    with gzip.open(restored/'docs/nacharbeit-2026-09-28/4-ledger.json.gz','rt',encoding='utf-8') as stream: rows=json.load(stream)
    costs=[checker.independent_costs(s['result']) for row in rows for s in row['scenarios']]
    assert costs==[s['costs_verified'] for s in report['summaries']]
    replays=[]
    for i,summary in enumerate(report['summaries']):
        with gzip.open(restored/f'docs/nacharbeit-2026-09-28/4-restart-{i}.json.gz','rt',encoding='utf-8') as stream: payload=json.load(stream)
        payload['input_path']=str(frozen/'eingaben.json')
        cp=backup/f'wiederherstellung-checkpoint-{i}.json.gz'
        with gzip.open(cp,'wt',encoding='utf-8') as stream: json.dump(payload,stream,allow_nan=False)
        replay=json.loads(proof(Path('tools/verify_4_resume.py'),f'wiederherstellung-replay-{i}.json',cp))
        assert replay['sha256']==summary['restart_sha256']
        replays.append(dict(name=summary['name'],slippage_pct=summary['slippage_pct'],**replay))
        print(f'Preserved V1 replay {i+1}/6 identical',flush=True)
    (backup/'wiederherstellung-losabgleich.json').write_text(json.dumps(costs,indent=2))
    assert not git(restored,'status','--porcelain').strip()
    assert not git(ROOT,'status','--porcelain').strip()
    changed=git(ROOT,'diff','--name-only',BASE,commit).decode().splitlines()
    result=dict(stage='5a abgeschlossen',commit=commit,branch=BRANCH,base=BASE,
        local_tests=712,baseline_tests=676,new_tests=36,old_test_changes='none',
        sabotages_5a=16,sabotages_4=23,sabotages_3b=19,d01_sabotages=6,f09_sabotages=3,
        github=ci,bundle_restore_verified=True,full_tree_verified=True,zip_verified=True,
        restored_tests=712,restore_probes_identical=True,restored_independent_comparisons=6,
        process_replays=replays,backup_sha256={'abschluss.bundle':sha(bundle),'abschluss.zip':sha(archive)},
        frozen_hashes={p.name:sha(p) for p in frozen.iterdir() if p.is_file()},
        changed_files_sha256={p:manifest[p] for p in changed},
        report='docs/nacharbeit-2026-09-28/ETAPPE-5A-ABSCHLUSS.md',
        boundaries=['No exactly-once claim; uncertain delivery blocks ordered queue',
                    'Telegram receipt is API acceptance, not reading/manual fill',
                    'Local disk durability; ephemeral runner loss before Git commit remains open',
                    'Ancillary watch/lage/test/resend commands remain one-shot',
                    'No main/live/dispatch/site/strategy changes; F17 remains 5b'],
        next_stage='Separate 5b only: GPT-6 Sol / mittel; no automatic start')
    (backup/'ABSCHLUSS.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    (backup/'START-5B.md').write_text(f'Gesicherter Abschlusscommit: `{commit}`\n\n'+(restored/'docs/nacharbeit-2026-09-28/START-5B.md').read_text(encoding='utf-8'),encoding='utf-8')
    (backup/'README.md').write_text(f'# Etappe 5a gesichert\n\nCommit `{commit}`; Zweig `{BRANCH}`.\n\nABSCHLUSS.json enthält Remote-/CI-/Restore-Belege. Bundle/ZIP geprüft. Kein Live-Go. Folgeauftrag separat START-5B.md.\n',encoding='utf-8')
    print(json.dumps(dict(commit=commit,backup=str(backup),verified=True,tests=712,hashes=result['backup_sha256']),indent=2))

if __name__=='__main__': main()
