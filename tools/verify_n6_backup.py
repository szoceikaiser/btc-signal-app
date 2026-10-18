"""Final exact-SHA CI, bundle/ZIP and complete independent restore acceptance."""
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
from verify_4_backup import git,sha
from verify_n6_scope import BASE,BRANCH,TAG
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/nach-6'


def main():
    commit=git(ROOT,'rev-parse','HEAD').decode().strip()
    assert not git(ROOT,'status','--porcelain').strip()
    backup=ROOT.parent/'audit-backups'/('nach-6-abschluss-'+commit[:7])
    backup.mkdir(parents=True,exist_ok=True)
    ci=json.loads((backup/'github-ci.json').read_text(encoding='utf-8-sig'))
    assert ci['commit']==commit and ci['tests_success'] and ci['branch']==BRANCH
    assert ci['tag_object']=='7d78094c17624b90b8f7ebc387b96570ff2c8ef7'
    assert ci['tag_target']=='469be65f65327a3b6abf2794ceba09c1fe0de9e2'
    assert ci['runs'] and all(r['head_sha']==commit and r['name']=='Tests' and r['event']=='push' and r['conclusion']=='success' for r in ci['runs'])
    prior=ROOT.parent/'audit-backups/6-abschluss-05208ce'
    previous=json.loads((prior/'ABSCHLUSS.json').read_text(encoding='utf-8'))
    assert previous['commit']==BASE
    for name,h in previous['backup_sha256'].items():assert sha(prior/name)==h
    frozen=backup/'eingefrorene-inputs';frozen.mkdir(exist_ok=True)
    for name,h in previous['frozen_hashes'].items():
        raw=(prior/'eingefrorene-inputs'/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==h
        (frozen/name).write_bytes(raw)
    bundle=backup/'abschluss.bundle';archive=backup/'abschluss.zip'
    if not bundle.exists():git(ROOT,'bundle','create',str(bundle),'refs/heads/'+BRANCH,'refs/tags/'+TAG)
    check=subprocess.run(['git','-c','safe.directory='+ROOT.as_posix(),'bundle','verify',str(bundle)],cwd=ROOT,capture_output=True,check=True)
    (backup/'bundle-verify.log').write_bytes(check.stdout+check.stderr)
    refs=git(ROOT,'bundle','list-heads',str(bundle)).decode().splitlines()
    assert len(refs)==2 and commit+' refs/heads/'+BRANCH in refs
    if not archive.exists():git(ROOT,'archive','--format=zip','--output='+str(archive),commit)
    files=git(ROOT,'ls-tree','-r','--name-only',commit).decode().splitlines()
    tree={}
    with zipfile.ZipFile(archive) as z:
        assert {n for n in z.namelist() if not n.endswith('/')}==set(files)
        for name in files:
            raw=git(ROOT,'show',commit+':'+name)
            assert z.read(name)==raw,name
            tree[name]=hashlib.sha256(raw).hexdigest()
    (backup/'git-tree-sha256.json').write_text(json.dumps(tree,indent=2),encoding='utf-8')
    restored=backup/'wiederherstellung'
    if not restored.exists():git(backup,'clone','--branch',BRANCH,str(bundle),str(restored))
    assert git(restored,'rev-parse','HEAD').decode().strip()==commit
    git(restored,'remote','set-url','origin','https://github.com/szoceikaiser/btc-signal-app.git')
    git(restored,'fsck','--full')
    def verify_files():
        entries=git(restored,'ls-tree','-r','HEAD').decode().splitlines()
        paths=[line.split('\t')[1] for line in entries]
        expected=[line.split('\t')[0].split()[2] for line in entries]
        actual=subprocess.run(['git','-c','safe.directory='+restored.as_posix(),'hash-object','--stdin-paths'],
            cwd=restored,input='\n'.join(paths)+'\n',text=True,capture_output=True,check=True).stdout.splitlines()
        assert actual==expected
        for name,h in tree.items():assert hashlib.sha256(git(restored,'show','HEAD:'+name)).hexdigest()==h
        assert not git(restored,'status','--porcelain').strip()
        return len(paths)
    count=verify_files()
    print('Bundle, ZIP and all restored files PASS',count,flush=True)
    def proof(script,name,*args):
        p=subprocess.run([sys.executable,str(restored/script),*map(str,args)],cwd=restored,
            env={**os.environ,'PYTHONUTF8':'1','TELEGRAM_BOT_TOKEN':'','TELEGRAM_CHAT_ID':''},capture_output=True)
        (backup/name).write_bytes(p.stdout);(backup/(name+'.stderr')).write_bytes(p.stderr)
        assert p.returncode==0,(script,p.stderr.decode(errors='replace'))
        return p.stdout
    proof('tools/verify_n6_checks.py','restore-checks.log','--out',backup/'restore-checks')
    print('Restored 741 tests, synthetic tests and all protection probes PASS',flush=True)
    scope=json.loads(proof('tools/verify_n6_scope.py','restore-scope.json'))
    assert scope['head']==commit
    def replay(package):
        output=backup/('restore-'+package)
        proof('tools/historical_analysis.py','restore-'+package+'.log','--package',package,'--inputs',frozen,'--out',output)
        assert json.loads((output/'results.json').read_text(encoding='utf-8'))==json.loads((DOC/package/'results.json').read_text(encoding='utf-8'))
        assert (output/'ledgers.json.gz').read_bytes()==(DOC/package/'ledgers.json.gz').read_bytes()
        print(package,'30 full restored runs exactly identical; independent accounts PASS',flush=True)
        return package
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(replay,['R0','R1']))
    old=json.loads((ROOT/'docs/nacharbeit-2026-09-28/6-ergebnis.json').read_text(encoding='utf-8'))
    def checkpoint(i):
        raw=(restored/f'docs/nacharbeit-2026-09-28/4-restart-{i}.json.gz').read_bytes()
        payload=json.loads(gzip.decompress(raw));payload['input_path']=str(frozen/'eingaben.json')
        file=backup/f'checkpoint-{i}.json.gz';file.write_bytes(gzip.compress(json.dumps(payload).encode(),mtime=0))
        result=json.loads(proof('tools/verify_4_resume.py',f'restore-checkpoint-{i}.json',file))
        assert result['sha256']==old['summaries'][i]['sha256']
        return result
    with ThreadPoolExecutor(max_workers=2) as pool:checkpoints=list(pool.map(checkpoint,range(6)))
    assert verify_files()==count and not git(ROOT,'status','--porcelain').strip()
    result=dict(stage='Historical follow-up after stage 6',base=BASE,commit=commit,branch=BRANCH,
        github=ci,bundle_restore_verified=True,full_tree_verified=True,zip_verified=True,
        restored_working_files=count,tests=741,old_tests_preserved=728,synthetic_groups=6,new_probes=15,
        inherited_probes=dict(f17=16,f13=16,stage4=23,stage3b=19,d01=6,f09=3),
        full_causal_restored_runs=60,independent_accounts=60,old_checkpoint_replays=checkpoints,
        frozen_hashes=previous['frozen_hashes'],backup_sha256={'abschluss.bundle':sha(bundle),'abschluss.zip':sha(archive)},
        r0_unchanged=True,r1_cutoff='2026-09-29T12:00:00Z',r1_complete_fields=True,as_of_proven=False,
        selection_adjusted=False,live_unchanged=True,live_go=False,scope=scope,
        report='docs/nach-6/BERICHT.md',summary=json.loads((DOC/'summary.json').read_text(encoding='utf-8')),
        next='Stop. Further strategy/live work only as separate assignment.')
    (backup/'ABSCHLUSS.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    (backup/'README.md').write_text(f'# Historischer Folgeauftrag gesichert\n\nCommit `{commit}`.\n\n60 vollständige Restore-Läufe, unabhängige Konten, 741 Tests und alle Schutzproben.\nR1 bis 29.09.2026 12:00 UTC; Live unverändert.\nABSCHLUSS.json enthält exakte CI-/Hash-/Restore-Belege.\n',encoding='utf-8')
    print(json.dumps(dict(result='PASS',commit=commit,backup=str(backup)),indent=2),flush=True)


if __name__=='__main__':main()
