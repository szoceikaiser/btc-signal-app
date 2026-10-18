"""Locked SQLite backup and blocked isolated restore."""
import argparse
from contextlib import closing
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import durable_delivery as durable
from production_contract import canonical, validate_v2
from produktion_store import verify_package


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def backup(store_path,store_id,migration_package,out):
    out=Path(out)
    if out.exists(): raise FileExistsError(out)
    verified=verify_package(migration_package)
    stage=Path(tempfile.mkdtemp(prefix='.produktion-backup-',dir=out.parent))
    try:
        with durable.VolumeStore(store_path,store_id) as store:
            if store.snapshot['version']!=2 or store.snapshot['control']['migration']['migration_id']!=verified['control']['migration']['migration_id']:
                raise ValueError('Migration package differs from store')
            with closing(sqlite3.connect(stage/'snapshot.sqlite')) as dest:
                store.db.backup(dest)
                if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                    raise ValueError('Backup integrity failure')
            (stage/'migration-source').mkdir()
            for p in (Path(migration_package)/'source').iterdir():
                if p.is_file(): shutil.copyfile(p,stage/'migration-source'/p.name)
            manifest={'schema':'produktion-backup-v1','store_id':store_id,'revision':store.revision,
                      'mode':store.snapshot['control']['mode'],
                      'code_sha':store.snapshot['control']['code_sha'],
                      'config_sha256':store.snapshot['control']['config_sha256'],
                      'migration_id':store.snapshot['control']['migration']['migration_id'],
                      'created_at_ms':int(time.time()*1000)}
            (stage/'snapshot.v2.json').write_text(canonical(store.snapshot)+'\n',encoding='utf-8')
            (stage/'backup-manifest.json').write_text(canonical(manifest)+'\n',encoding='utf-8')
            paths=sorted(p for p in stage.rglob('*') if p.is_file())
            (stage/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(stage).as_posix()}\n' for p in paths),encoding='utf-8')
            # Read the backup row, not just the file hash.
            with closing(sqlite3.connect(stage/'snapshot.sqlite')) as db:
                row=db.execute('SELECT store_id,revision,body,digest FROM snapshot WHERE id=1').fetchone()
                if row[:2]!=(store_id,store.revision) or hashlib.sha256(row[2].encode()).hexdigest()!=row[3] or json.loads(row[2])!=store.snapshot:
                    raise ValueError('Inconsistent backup row')
            stage.rename(out)
            store.snapshot['control']['health']['last_verified_backup_ms']=manifest['created_at_ms']
            store.snapshot['control']['health']['last_verified_backup_revision']=manifest['revision']
            store.commit()
    finally:
        if stage.exists(): shutil.rmtree(stage)
    return manifest


def verify_backup(package):
    package=Path(package)
    names=set()
    for line in (package/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest,sep,name=line.partition('  ')
        if (not sep or name in names or Path(name).is_absolute() or
                '..' in Path(name).parts or sha(package/name)!=digest):
            raise ValueError('Backup hash mismatch')
        names.add(name)
    required={'snapshot.sqlite','snapshot.v2.json','backup-manifest.json',
              'migration-source/state.json','migration-source/signals.json',
              'migration-source/oi_history.json','migration-source/config-source.json',
              'migration-source/source-manifest.json','migration-source/cutover.json',
              'migration-source/config-target.json'}
    if not required<=names:
        raise ValueError('Backup package lacks migration source')
    manifest=json.loads((package/'backup-manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema')!='produktion-backup-v1': raise ValueError('Unknown backup format')
    snapshot=json.loads((package/'snapshot.v2.json').read_text(encoding='utf-8'))
    validate_v2(snapshot)
    with closing(sqlite3.connect(f'file:{(package/"snapshot.sqlite").as_posix()}?mode=ro',uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('SQLite integrity failure')
        row=db.execute('SELECT store_id,revision,body,digest FROM snapshot WHERE id=1').fetchone()
        if row is None or row[:2]!=(manifest['store_id'],manifest['revision']) or json.loads(row[2])!=snapshot or hashlib.sha256(row[2].encode()).hexdigest()!=row[3]:
            raise ValueError('Backup snapshot mismatch')
    return manifest,snapshot


def restore(package,target):
    manifest,snapshot=verify_backup(package)
    target=Path(target)
    if target.exists(): raise FileExistsError(target)
    snapshot=deepcopy(snapshot)
    snapshot['control']['mode']='blocked'
    snapshot['control']['health']['restore_requires_reconciliation']=True
    snapshot['control']['health']['restored_from_revision']=manifest['revision']
    stage=Path(tempfile.mkdtemp(prefix='.produktion-restore-',dir=target.parent))
    try:
        durable.provision(stage/'store',manifest['store_id'],snapshot)
        with durable.VolumeStore(stage/'store',manifest['store_id']) as check:
            if check.snapshot!=snapshot: raise ValueError('Restore verification failed')
        (stage/'store').rename(target)
    finally:
        if stage.exists(): shutil.rmtree(stage)
    return {'store_id':manifest['store_id'],'source_revision':manifest['revision'],
            'mode':'blocked','restore_requires_reconciliation':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('backup'); b.add_argument('--store',required=True); b.add_argument('--store-id',required=True)
    b.add_argument('--migration-package',required=True); b.add_argument('--out',required=True)
    r=sub.add_parser('restore'); r.add_argument('--package',required=True); r.add_argument('--target',required=True)
    a=p.parse_args()
    print(canonical(backup(a.store,a.store_id,a.migration_package,a.out) if a.command=='backup' else restore(a.package,a.target)))
