"""Local pinned Git-store packaging and blocked restore; no fetch, push or tokens.

CLI accepts only an explicit synthetic source marker. Actual private source
acquisition and second-repository upload require a later bounded authorization.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import durable_delivery as durable
import github_delivery as github
from production_contract import canonical, digest
from produktion_store import verify_package

MAX_PACKAGE_BYTES = 20 * 1024 * 1024
MAX_HISTORY_COMMITS = 1000


def git(repo, *args):
    return subprocess.check_output(['git','-c','safe.directory='+Path(repo).resolve().as_posix(),
        '-C',str(repo),*args],stderr=subprocess.PIPE)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def history(repo, pin, identity):
    rows = git(repo,'rev-list','--parents',pin).decode().splitlines()
    if not 1 <= len(rows) <= MAX_HISTORY_COMMITS: raise ValueError('History size limit')
    parser = github.GitHubStore(None,identity['repo'],identity['branch'],identity['store_id'],
                               'offline-verify','1',github.STORE_PATH)
    prior = None; total = 0; first = None
    for i, row in enumerate(rows):
        parts = row.split(); commit = parts[0]
        expected_parent = [rows[i+1].split()[0]] if i+1 < len(rows) else []
        if parts[1:] != expected_parent: raise ValueError('Complete linear history required')
        body = git(repo,'show',commit+':'+github.STORE_PATH)
        total += len(body)
        if total > MAX_PACKAGE_BYTES: raise ValueError('Unpacked history size limit')
        env = parser._parse({'body':body})
        if first is None: first = env
        if prior and (prior['revision'] != env['revision']+1 or prior['parent_digest'] != env['body_digest']):
            raise ValueError('Pinned store history lineage mismatch')
        prior = env
    if prior['revision'] != 0 or prior['snapshot']['control']['mode'] != 'blocked':
        raise ValueError('Blocked seed history missing')
    return first, rows


def package_local(repo, branch, pin, identity, migration, out):
    out = Path(out).resolve()
    if out.exists(): raise FileExistsError(out)
    if branch != identity['branch'] or git(repo,'rev-parse','refs/heads/'+branch).decode().strip() != pin:
        raise ValueError('Source head differs from approved pin')
    if git(repo,'status','--porcelain').strip(): raise ValueError('Source checkout not clean')
    source, rows = history(repo,pin,identity)
    if source['snapshot']['control']['stream_id'] != identity['stream_id']:
        raise ValueError('Pinned stream identity mismatch')
    migrated = verify_package(migration)
    if migrated['control']['migration']['migration_id'] != source['snapshot']['control']['migration']['migration_id']:
        raise ValueError('Migration identity mismatch')
    stage=Path(tempfile.mkdtemp(prefix='.p3-git-backup-',dir=out.parent))
    try:
        (stage/'stream.json').write_bytes(git(repo,'show',pin+':'+github.STORE_PATH))
        shutil.copytree(migration,stage/'migration')
        git(repo,'bundle','create',str(stage/'history.bundle'),'refs/heads/'+branch)
        git(repo,'bundle','verify',str(stage/'history.bundle'))
        c=source['snapshot']['control']
        manifest={'schema':'p3-local-github-backup-v1','identity':identity,'pin':pin,
            'store_path':github.STORE_PATH,'stream_id':c['stream_id'],
            'target_binding':c['target_binding'],'bot_identity':c['bot_identity'],
            'revision':source['revision'],'snapshot_digest':source['body_digest'],
            'code_sha':c['code_sha'],'config_sha256':c['config_sha256'],
            'migration_id':c['migration']['migration_id'],'history_count':len(rows),
            'history_sha256':digest(rows),'second_private_repository':None}
        (stage/'backup-manifest.json').write_text(canonical(manifest)+'\n',encoding='utf-8')
        files=sorted(p for p in stage.rglob('*') if p.is_file())
        if sum(p.stat().st_size for p in files)>MAX_PACKAGE_BYTES: raise ValueError('Backup package size limit')
        (stage/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(stage).as_posix()+'\n' for p in files),encoding='utf-8')
        if git(repo,'rev-parse','refs/heads/'+branch).decode().strip()!=pin:
            raise ValueError('Source changed during package creation')
        stage.rename(out)
        return manifest
    finally:
        if stage.exists():
            if stage.resolve().parent!=out.parent or not stage.name.startswith('.p3-git-backup-'):
                raise ValueError('Unsafe staging cleanup')
            shutil.rmtree(stage)


def restore_local(package, target, required_pin, required_revision):
    package=Path(package).resolve(); target=Path(target).resolve()
    if target.exists(): raise FileExistsError(target)
    names=set()
    for line in (package/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        h,sep,name=line.partition('  ')
        if (not sep or name in names or Path(name).is_absolute() or '..' in Path(name).parts
                or sha(package/name)!=h): raise ValueError('Backup hash mismatch')
        names.add(name)
    actual={p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()
            and p.relative_to(package).as_posix()!='SHA256SUMS'}
    if names != actual or not {'history.bundle','stream.json','backup-manifest.json'} <= names:
        raise ValueError('Backup inventory mismatch')
    if sum(p.stat().st_size for p in package.rglob('*') if p.is_file())>MAX_PACKAGE_BYTES:
        raise ValueError('Backup size limit')
    m=json.loads((package/'backup-manifest.json').read_text(encoding='utf-8'))
    if m['schema']!='p3-local-github-backup-v1' or m['pin']!=required_pin or m['revision']!=required_revision:
        raise ValueError('Required latest revision missing')
    stage=Path(tempfile.mkdtemp(prefix='.p3-git-restore-',dir=target.parent))
    try:
        restored=stage/'verification-repository'
        subprocess.run(['git','clone','--no-hardlinks',str(package/'history.bundle'),str(restored)],
                       check=True,capture_output=True)
        git(restored,'fsck','--full')
        env, rows=history(restored,required_pin,m['identity'])
        if (len(rows)!=m['history_count'] or digest(rows)!=m['history_sha256']
                or env['revision']!=required_revision or env['body_digest']!=m['snapshot_digest']
                or git(restored,'show',required_pin+':'+github.STORE_PATH)!=(package/'stream.json').read_bytes()
                or env['snapshot']['control']['code_sha']!=m['code_sha']
                or env['snapshot']['control']['config_sha256']!=m['config_sha256']
                or env['snapshot']['control']['stream_id']!=m['stream_id']
                or env['snapshot']['control']['stream_id']!=m['identity']['stream_id']
                or m['store_path']!=github.STORE_PATH
                or env['snapshot']['control']['target_binding']!=m['target_binding']
                or env['snapshot']['control']['bot_identity']!=m['bot_identity']
                or env['snapshot']['control']['migration']['migration_id']!=m['migration_id']):
            raise ValueError('Restored history/identity mismatch')
        migrated=verify_package(package/'migration')
        if migrated['control']['migration']['migration_id']!=m['migration_id']:
            raise ValueError('Restored migration mismatch')
        snapshot=deepcopy(env['snapshot']);snapshot['control'].update(mode='blocked',owner=None)
        h=snapshot['control']['health'];h.update(restore_requires_reconciliation=True,
            restored_from_commit=required_pin,restored_from_revision=required_revision,
            successful_runs={},completed_runs={})
        for s in [snapshot['engine'],*snapshot['commands'].values()]:
            for msg in s.get('_delivery',{}).get('messages',[]):
                if msg['status']=='sending':msg.update(status='uncertain',reason='blocked_restore')
        durable.provision(stage/'blocked-store',m['identity']['store_id'],snapshot)
        with durable.read_only_volume(stage/'blocked-store',m['identity']['store_id']) as check:
            if check.snapshot!=snapshot:raise ValueError('Blocked restore mismatch')
        # Verification checkout contains original pinned bytes, never an active writer.
        # Disable its push URL locally, independent of the unreachable bundle origin.
        git(restored,'remote','set-url','--push','origin','DISABLED-OFFLINE-RESTORE')
        stage.rename(target)
        return {'mode':'blocked','pin':required_pin,'revision':required_revision,
            'history_count':len(rows),'git_fsck':True,'real_backup_write':False}
    finally:
        if stage.exists():
            if stage.resolve().parent!=target.parent or not stage.name.startswith('.p3-git-restore-'):
                raise ValueError('Unsafe staging cleanup')
            shutil.rmtree(stage)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true',required=True)
    p.add_argument('--synthetic-plan',required=True);a=p.parse_args()
    plan=json.loads(Path(a.synthetic_plan).read_text(encoding='utf-8'))
    if plan.get('synthetic') is not True:raise ValueError('Synthetic source only in this CLI')
    # v1 functions above are explicit legacy readers/writers for old evidence.
    # New CLI runs always use v2 and require an independently supplied revision.
    from p3_backup_chain import append_local, restore_verified
    result=append_local(plan['source'],plan['branch'],plan['pin'],plan['revision'],
        plan['identity'],plan['migration'],plan['out'])
    print(canonical(restore_verified(plan['out'],result['manifest'],plan['restore'],
        plan['pin'],plan['revision'],plan['identity'])))
