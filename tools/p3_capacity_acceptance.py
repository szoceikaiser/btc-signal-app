"""Reproduce old ceiling, measure v2 consecutive backups and fresh local restore."""
import json
import os
from pathlib import Path
import shutil
import sys
import time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'engine')]
import p3_backup_chain as b
import produktion_github_backup as legacy


def size(root):return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file())


def objects(repo):
    values={};budget=b.Budget()
    for line in b.git(repo,budget,'cat-file','--batch-all-objects','--batch-check=%(objecttype) %(objectsize)').splitlines():
        kind,n=line.decode().split();part=values.setdefault(kind,dict(count=0,bytes=0))
        part['count']+=1;part['bytes']+=int(n)
    return values


def run(out):
    out=Path(out).resolve();budget=b.Budget()
    f=json.loads((out/'capacity-30-days/fixture.json').read_text())
    old=ROOT.parent/'audit-backups/p3-hauptchat-abnahme-20261008/synthetic-history-1001.bundle'
    assert b.sha(old)=='407ec3fe4704b5f83546b2d53beff44706ac1b816b8ebe5938c411578170c689'
    source=out/'old-fixture-source'
    b.git(out,budget,'clone','--bare',str(old),str(source))
    oldpin='53392592cc77e47eb62a66c0d4a573d5f531972a'
    try:legacy.history(source,oldpin,f['identity'])
    except ValueError as exc:
        assert str(exc)=='History size limit';error=str(exc)
    else:raise AssertionError('Old ceiling not reproduced')
    a=b.append_local(source,f['identity']['branch'],oldpin,1000,f['identity'],f['migration'],out/'old-fixture-v2')
    r=b.restore_verified(out/'old-fixture-v2',a['manifest'],out/'old-fixture-restored',oldpin,1000,f['identity'])
    b.write_json(out/'N-P3-01-REPRODUCTION.json',dict(old_error=error,old_bundle_bytes=old.stat().st_size,
        old_bundle_sha256=b.sha(old),source_pin=oldpin,source_revision=1000,v2=a,restore=r,passed=True))
    print('old 1001 fixture restored fully',flush=True)
    root=out/'capacity-chain';backups=[];oldhashes={};repo=Path(f['source'])
    for day in (1,2,3,10,20,30):
        pin=f['pins'][day-1]
        b.git(repo,b.Budget(),'update-ref','refs/heads/'+f['identity']['branch'],pin['pin'])
        a=b.append_local(repo,f['identity']['branch'],pin['pin'],pin['revision'],f['identity'],f['migration'],root)
        assert all(b.sha(root/n)==h for n,h in oldhashes.items())
        current={p.relative_to(root).as_posix():b.sha(p) for p in (root/'packages').rglob('*') if p.is_file()}
        additional={n:h for n,h in current.items() if n not in oldhashes}
        entry=dict(day=day,states=pin['revision']+1,added_package_files=len(additional),
            added_package_bytes=sum((root/n).stat().st_size for n in additional),old_files_unchanged=True,**a)
        backups.append(entry);oldhashes=current
        b.write_json(out/f'BACKUP-DAY-{day:02d}.json',entry)
        print('backup day',day,'packages',a['manifest']['package_count'],'seconds',a['metrics']['seconds'],flush=True)
    # Copy only actual backup artifacts, then restore without source alternates.
    copied=out/'capacity-local-readback';shutil.copytree(root/'packages',copied/'packages')
    assert all(b.sha(copied/n)==h for n,h in oldhashes.items())
    end=f['pins'][-1];m=backups[-1]['manifest']
    restored=out/'capacity-fresh-restore'
    result=b.restore_verified(copied,m,restored,end['pin'],end['revision'],f['identity'])
    budget=b.Budget()
    original=b.git(repo,budget,'rev-list','--reverse',end['pin'])
    actual=b.git(restored/'verification-repository',budget,'rev-list','--reverse',end['pin'])
    assert original==actual and len(actual.splitlines())==f['states']>=15302
    assert not (restored/'verification-repository/objects/info/alternates').exists()
    manifests,total=b.load_segments(root,f['identity'])
    result=dict(passed=True,synthetic_only=True,fixture=f,backups=backups,restore=result,
        all_original_commits_exact=True,source_git_bytes=size(repo),package_bytes=total,
        source_unpacked_objects=objects(repo),restored_unpacked_objects=objects(restored/'verification-repository'),
        restored_git_bytes=size(restored/'verification-repository'),restored_store_bytes=size(restored/'blocked-store'),
        unpacked_store_body_bytes=sum(m['unpacked_bytes'] for m in manifests),
        max_package_bytes=max(size(root/'packages'/f'{i:06d}') for i in range(len(manifests))),
        max_package_commits=max(m['count'] for m in manifests),
        max_package_unpacked_bytes=max(m['unpacked_bytes'] for m in manifests),
        real_requests=0,real_transport=0,production_size_measured=False)
    assert result['unpacked_store_body_bytes']==f['body_bytes']
    assert result['source_unpacked_objects']==result['restored_unpacked_objects']
    b.write_json(out/'CAPACITY-ACCEPTANCE.json',result)
    print('CAPACITY PASSED',f['states'],total,flush=True)


if __name__=='__main__':
    for k in list(os.environ):
        if k.startswith(('BTC_DELIVERY_','GITHUB_','GH_','TELEGRAM_')):del os.environ[k]
    with patch('urllib.request.urlopen',side_effect=AssertionError('Network forbidden')),\
         patch('socket.create_connection',side_effect=AssertionError('Network forbidden')):
        run(sys.argv[1])
