"""Local full stream + fence incremental backup, fresh blocked restore.

No network, activation, credentials, sender, expiry or automatic takeover.
Uses p3's guarded Git processes and unchanged segment/RSS/time/byte limits.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'engine'), str(ROOT/'tools')]
import actions_delivery as actions
import github_delivery as github
from production_contract import canonical, digest
import p3_backup_chain as b

SCHEMA = 'p4-two-history-backup-v1'


def publish_new(source,target,budget):
    # Windows scanners can briefly hold a newly closed local payload directory.
    # Retry only this unchanged local rename, never a Git/HTTP mutation.
    for attempt in range(10):
        budget.check()
        if Path(target).exists(): raise FileExistsError(target)
        try:
            Path(source).rename(target)
            return
        except PermissionError:
            if os.name!='nt' or attempt==9: raise
            time.sleep(.1)


def head(repo, branch, budget):
    return b.git(repo,budget,'rev-parse','refs/heads/'+branch).decode().strip()


def inspect_fence(read, pin, deployment):
    raw=read(pin,'commit',16384)
    headers=raw.split(b'\n\n',1)[0].splitlines()
    parents=[line[7:].decode() for line in headers if line.startswith(b'parent ')]
    trees=[line[5:].decode() for line in headers if line.startswith(b'tree ')]
    if len(trees)!=1: raise ValueError('Fence tree missing')
    tree=read(trees[0],'tree',4096);prefix=b'40000 delivery\0'
    if not tree.startswith(prefix) or len(tree)!=len(prefix)+20: raise ValueError('Fence root tree')
    tree=read(tree[-20:].hex(),'tree',4096);prefix=b'100644 actions-fence.json\0'
    if not tree.startswith(prefix) or len(tree)!=len(prefix)+20: raise ValueError('Fence leaf tree')
    blob=tree[-20:].hex()
    body=read(blob,'blob',actions.MAX_FENCE_BYTES)
    value=actions.parse_fence({'body':body},deployment)
    return parents,body,value,blob


def transition(previous, current):
    if previous is None:
        if current['run'] is not None or current['phase']!='closed': raise ValueError('Full fence seed required')
        return
    if previous['phase']=='closed' and current['phase']=='open':
        run=current['run'];w=run['workflow']
        expected=deepcopy(previous['cursors']);expected[w]={'number':run['number'],'id':run['id']}
        if (run['number']<=previous['cursors'][w]['number'] or current['cursors']!=expected
                or any(c['id']==run['id'] for c in previous['cursors'].values())
                or current['completion'] is not None): raise ValueError('Fence cursor lineage')
    elif previous['phase']=='open' and current['phase']=='closed':
        if (current['run']!=previous['run'] or current['cursors']!=previous['cursors']
                or not current['completion']): raise ValueError('Fence close lineage')
    else: raise ValueError('Fence transition missing/reordered')


def crosscheck(value, stream_repo, stream_pin, identity, deployment, budget):
    if value['phase']=='open' or value['run'] is None: return
    loc=value['completion']['stream']
    expected={'adapter':'github','repo':identity['repo'],'branch':identity['branch'],
              'path':github.STORE_PATH,'store_id':identity['store_id']}
    if any(loc.get(k)!=v for k,v in expected.items()): raise ValueError('Foreign fence completion')
    b.git(stream_repo,budget,'merge-base','--is-ancestor',loc['commit_sha'],stream_pin)
    with b.batch(stream_repo,budget) as read:
        _,body,env=b.inspect(read,loc['commit_sha'],identity,b.parser(identity))
    blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
    if (loc['revision']!=env['revision'] or loc['blob_sha']!=blob or loc['snapshot_digest']!=env['body_digest']
            or any(env['snapshot']['control'][k]!=deployment[k] for k in ('code_sha','config_sha256','bot_identity'))):
        raise ValueError('Fence completion pin mismatch')


def fence_segments(root, deployment, budget):
    parts=Path(root)/'packages';manifests=[];prior=None;previous=b.ZERO;count=0;total=0
    files=sorted(parts.iterdir()) if parts.exists() else []
    if len(files)>b.MAX_SEGMENTS: raise ValueError('Fence segment limit')
    for i,p in enumerate(files):
        budget.check()
        if p.name!=f'{i:06d}' or p.is_symlink() or not p.is_dir(): raise ValueError('Missing fence increment')
        m=b.read_json(p/'segment.json')
        if (m['schema']!='p4-fence-segment-v1' or m['deployment']!=deployment or m['index']!=i
                or m['previous_manifest_sha256']!=previous or m['parent_pin']!=prior
                or m['first_revision']!=count or not 1<=m['count']<=b.MAX_COMMITS
                or m['revision']!=count+m['count']-1 or not b.HEX40.fullmatch(m['pin'])
                or not 0<m['unpacked_bytes']<=b.MAX_UNPACKED
                or m['files']!=b.inventory(p) or set(m['files'])!={'history.bundle','fence.json'}):
            raise ValueError('Fence package chain/hash mismatch')
        size=sum(x['bytes'] for x in m['files'].values())+(p/'segment.json').stat().st_size
        total+=size
        if size>b.MAX_PACKAGE or total>b.MAX_SET_BYTES: raise ValueError('Fence package byte limit')
        manifests.append(m);previous=digest(m);prior=m['pin'];count+=m['count']
    return manifests,total


def fence_manifest(ms,total):
    if not ms: raise ValueError('Empty fence history')
    last=ms[-1];hashes=[digest(m) for m in ms]
    return dict(schema='p4-fence-set-v1',deployment=last['deployment'],pin=last['pin'],
        revision=last['revision'],blob_sha=last['blob_sha'],body_sha256=last['body_sha256'],
        history_count=sum(m['count'] for m in ms),package_count=len(ms),package_bytes=total,
        package_manifest_sha256=hashes,chain_sha256=digest(hashes))


def append_fence(repo,branch,pin,revision,deployment,root,budget):
    root=Path(root);(root/'packages').mkdir(parents=True,exist_ok=True)
    if head(repo,branch,budget)!=pin: raise ValueError('Fence moved')
    ms,total=fence_segments(root,deployment,budget)
    prior=ms[-1]['pin'] if ms else None
    index=ms[-1]['revision']+1 if ms else 0
    previous=None
    if prior:
        b.git(repo,budget,'merge-base','--is-ancestor',prior,pin)
        with b.batch(repo,budget) as read: _,_,previous,_=inspect_fence(read,prior,deployment)
    ids=iter(b.commits(repo,pin,prior,budget))
    from itertools import islice
    while group:=list(islice(ids,b.MAX_COMMITS)):
        rows=[];unpacked=0;first=index;parent=prior;h=hashlib.sha256()
        with b.batch(repo,budget) as read:
            for commit in group:
                parents,body,value,blob=inspect_fence(read,commit,deployment)
                if parents!=([prior] if prior else []): raise ValueError('Incomplete fence ancestry')
                transition(previous,value)
                unpacked+=len(body)
                if unpacked>b.MAX_UNPACKED: raise ValueError('Fence unpacked limit')
                h.update((canonical([commit,prior,index,digest(value),blob])+'\n').encode())
                rows.append(commit);prior=commit;previous=value;index+=1
        i=len(ms)
        if i>=b.MAX_SEGMENTS: raise ValueError('Fence segment limit')
        stage=Path(tempfile.mkdtemp(prefix='.fence-stage-',dir=root))
        # Keep interrupted stages as evidence; never silently replace packages.
        scratch=stage/'scratch';scratch.mkdir();b.git(scratch,budget,'init','--bare')
        objects=b.git(repo,budget,'rev-parse','--path-format=absolute','--git-path','objects').decode().strip()
        (scratch/'objects/info/alternates').write_bytes((Path(objects).as_posix()+'\n').encode())
        b.git(scratch,budget,'update-ref','refs/heads/backup',prior)
        args=['bundle','create',str(stage/'history.bundle'),'refs/heads/backup']
        if parent: args.append('^'+parent)
        b.git(scratch,budget,*args)
        # scratch is outside the immutable published package, retained locally.
        package=stage/'payload';package.mkdir()
        (stage/'history.bundle').rename(package/'history.bundle')
        (package/'fence.json').write_bytes(body)
        m=dict(schema='p4-fence-segment-v1',index=i,deployment=deployment,
            previous_manifest_sha256=digest(ms[-1]) if ms else b.ZERO,parent_pin=parent,
            first_revision=first,revision=index-1,count=len(rows),pin=prior,blob_sha=blob,
            body_sha256=hashlib.sha256(body).hexdigest(),unpacked_bytes=unpacked,
            history_sha256=h.hexdigest(),files=b.inventory(package))
        b.write_json(package/'segment.json',m)
        size=sum(x['bytes'] for x in m['files'].values())+(package/'segment.json').stat().st_size
        if size>b.MAX_PACKAGE or total+size>b.MAX_SET_BYTES: raise ValueError('Fence package limit')
        publish_new(package,root/'packages'/f'{i:06d}',budget);ms.append(m);total+=size
    if index!=revision+1 or prior!=pin: raise ValueError('Independent fence revision/pin missing')
    return fence_manifest(ms,total)


def restore_fence(root,manifest,target,deployment,stream_repo,stream_pin,identity,budget):
    ms,total=fence_segments(root,deployment,budget)
    if fence_manifest(ms,total)!=manifest: raise ValueError('Required fence set differs')
    target=Path(target);target.mkdir(exist_ok=False);b.git(target,budget,'init','--bare')
    prior=None;previous=None;index=0
    for i,m in enumerate(ms):
        package=Path(root)/'packages'/f'{i:06d}';bundle=package/'history.bundle'
        with bundle.open('rb') as f:
            if f.readline()!=b'# v2 git bundle\n': raise ValueError('Fence bundle version')
            refs=[];dependencies=[]
            for _ in range(16):
                line=f.readline(8192)
                if line==b'\n': break
                if line.startswith(b'-'): dependencies.append(line[1:].split()[0].decode())
                else: refs.append(line.decode().strip())
            else: raise ValueError('Fence bundle header limit')
        if dependencies!=([prior] if prior else []) or refs!=[m['pin']+' refs/heads/backup']:
            raise ValueError('Fence dependency/ref mismatch')
        b.git(target,budget,'bundle','verify',str(bundle));b.git(target,budget,'bundle','unbundle',str(bundle))
        count=0;unpacked=0;h=hashlib.sha256()
        with b.batch(target,budget) as read:
            for commit in b.commits(target,m['pin'],prior,budget):
                parents,body,value,blob=inspect_fence(read,commit,deployment)
                if parents!=([prior] if prior else []): raise ValueError('Missing fence ancestry')
                transition(previous,value)
                crosscheck(value,stream_repo,stream_pin,identity,deployment,budget)
                h.update((canonical([commit,prior,index,digest(value),blob])+'\n').encode())
                count+=1;unpacked+=len(body)
                if count>b.MAX_COMMITS or unpacked>b.MAX_UNPACKED: raise ValueError('Fence restore step limit')
                prior=commit;previous=value;index+=1
        if (count!=m['count'] or unpacked!=m['unpacked_bytes'] or h.hexdigest()!=m['history_sha256']
                or body!=(package/'fence.json').read_bytes() or prior!=m['pin']
                or blob!=m['blob_sha'] or hashlib.sha256(body).hexdigest()!=m['body_sha256']):
            raise ValueError('Fence history bytes/hash mismatch')
        b.git(target,budget,'update-ref','refs/heads/backup',prior)
    b.git(target,budget,'fsck','--full','--no-reflogs')
    b.git(target,budget,'config','remote.origin.pushurl','DISABLED-OFFLINE-RESTORE')
    if index!=manifest['history_count'] or index!=manifest['revision']+1: raise ValueError('Fence history incomplete')
    return body,previous


def validate_pair(manifest,required):
    if manifest['schema']!=SCHEMA or manifest['pins']!=required:
        raise ValueError('Independent paired pins required')
    d=manifest['deployment'];s=manifest['stream'];f=manifest['fence']
    from produktion_actions_runner import deployment
    if (d!=deployment(d) or d['schedule_contract']!='btc-actions-slots-v1'
            or d['workflows']!=actions.WORKFLOWS or d['store_branch']==d['fence_branch']
            or any(not value for value in d.values())
            or not b.HEX40.fullmatch(d['code_sha'])
            or any(not b.HEX64.fullmatch(d[k]) for k in ('config_sha256','activation_review_sha256'))
            or s['schema']!='p3-backup-set-v2' or f['schema']!='p4-fence-set-v1'
            or s['store_path']!=github.STORE_PATH or s['stream_id']!=s['identity']['stream_id']
            or s['identity']['repo']!=d['private_store_repository'] or s['identity']['branch']!=d['store_branch']
            or s['identity']['store_id']!=d['store_id'] or f['deployment']!=d
            or any(s[k]!=d[k] for k in ('code_sha','config_sha256','bot_identity'))
            or not b.HEX40.fullmatch(required['stream'].get('blob_sha',''))
            or required!={'stream':{'commit_sha':s['pin'],'revision':s['revision'],'snapshot_digest':s['snapshot_digest'],
                                   'blob_sha':required['stream']['blob_sha']},
                         'fence':{'commit_sha':f['pin'],'revision':f['revision'],'blob_sha':f['blob_sha'],'body_sha256':f['body_sha256']}}
            or s['package_bytes']+f['package_bytes']>b.MAX_SET_BYTES
            or s['package_count']+f['package_count']>b.MAX_SEGMENTS):
        raise ValueError('Paired deployment/history pins differ')
    if len((canonical(manifest)+'\n').encode())>b.MAX_MANIFEST:
        raise ValueError('Paired manifest byte limit')


def inventory(root,budget):
    result={};total=0
    for kind in ('stream','fence'):
        for p in sorted((Path(root)/kind/'packages').rglob('*')):
            budget.check()
            if p.is_symlink(): raise ValueError('Backup symlink')
            if p.is_file():
                total+=p.stat().st_size
                if total>b.MAX_SET_BYTES or len(result)>=b.MAX_SEGMENTS*64: raise ValueError('Paired inventory limit')
                result[p.relative_to(root).as_posix()]={'bytes':p.stat().st_size,'sha256':b.sha(p)}
    return result


def restore(root,manifest,target,required,budget=None):
    budget=budget or b.Budget();validate_pair(manifest,required)
    root=Path(root).resolve();target=Path(target).resolve()
    if target.exists(): raise FileExistsError(target)
    if inventory(root,budget)!=manifest['files']: raise ValueError('Paired package inventory mismatch')
    # Partial failures remain explicitly blocked evidence, never a runnable store.
    target.mkdir();b.write_json(target/'RESTORE-BLOCKED.json',{'enabled':False,'reconciliation_required':True})
    s=manifest['stream'];d=manifest['deployment']
    latest=(root/'stream/packages'/f"{s['package_count']-1:06d}"/'stream.json').read_bytes()
    if hashlib.sha1(b'blob '+str(len(latest)).encode()+b'\0'+latest).hexdigest()!=required['stream']['blob_sha']:
        raise ValueError('Independent stream blob differs')
    sr=b.restore_verified(root/'stream',s,target/'stream',s['pin'],s['revision'],s['identity'],budget)
    body,value=restore_fence(root/'fence',manifest['fence'],target/'fence-verification-repository',d,
        target/'stream/verification-repository',s['pin'],s['identity'],budget)
    if value['phase']=='closed' and value['completion']:
        expected={'adapter':'github','repo':s['identity']['repo'],'branch':s['identity']['branch'],
            'path':github.STORE_PATH,'store_id':s['identity']['store_id'],'commit_sha':s['pin'],
            'revision':s['revision'],'blob_sha':required['stream']['blob_sha'],'snapshot_digest':s['snapshot_digest']}
        if value['completion']['stream']!=expected:
            raise ValueError('Closed terminal fence and stream are from different cuts')
    (target/'actions-fence.original.json').write_bytes(body)
    if inventory(root,budget)!=manifest['files']: raise ValueError('Backup moved during restore')
    receipt=dict(schema='p4-pair-local-verification-v1',status='local_verified',enabled=False,
        manifest_sha256=digest(manifest),pins=required,history_verified=True,restore_blocked_verified=True,
        fence_phase=value['phase'],cursors_sha256=digest(value['cursors']),stream_verification=sr,
        package_manifest_sha256=digest(manifest['files']),verified_ms=int(time.time()*1000),
        real_upload_verified=False,metrics=budget.metrics())
    b.write_json(target/'verification.json',receipt)
    return receipt


def append(plan,fault=None,budget=None):
    budget=budget or b.Budget();d=plan['deployment'];root=Path(plan['out']).resolve()
    root.mkdir(exist_ok=True)
    # A crash leaves the owner file. No TTL, overwrite or automatic retry.
    with (root/'.pair-owner').open('x') as f: f.write('Interrupted pair requires explicit operator review\n')
    def stable():
        for kind,branch in (('stream',d['store_branch']),('fence',d['fence_branch'])):
            if head(plan[kind+'_source'],branch,budget)!=plan['pins'][kind]['commit_sha']:
                raise ValueError('Source pair moved')
    try:
        stable()
        s=b.append_local(plan['stream_source'],d['store_branch'],plan['pins']['stream']['commit_sha'],
            plan['pins']['stream']['revision'],plan['identity'],plan['migration'],root/'stream',budget=budget)['manifest']
        f=append_fence(plan['fence_source'],d['fence_branch'],plan['pins']['fence']['commit_sha'],
            plan['pins']['fence']['revision'],d,root/'fence',budget)
        manifest=dict(schema=SCHEMA,deployment=d,stream=s,fence=f,pins=plan['pins'],files=inventory(root,budget))
        validate_pair(manifest,plan['pins'])
        if fault: fault('before_restore')
        stable()
        verification=root/('verify-'+digest(manifest)[:12])
        result=restore(root,manifest,verification,plan['pins'],budget)
        stable()
        if inventory(root,budget)!=manifest['files']: raise ValueError('Packages moved')
        # Immutable named completion; no 'latest' rewrite and no uploaded claim.
        b.write_json(root/('pair-'+digest(manifest)+'.json'),manifest)
        return {'manifest':manifest,'verification':result,'verification_path':str(verification)}
    finally:
        # Normal completion/failure releases only our own transient operation owner.
        (root/'.pair-owner').unlink()


def verify_readback(plan):
    """Independent verifier of an AUTHENTICATED, separately staged backup mirror.

    Caller must stage the exact protected destination commit. This function
    verifies every Git blob and package byte, then restores both histories.
    It emits local receipt bytes only; publication is an explicit later binding.
    """
    budget=b.Budget();d=plan['destination'];binding=plan['verifier']
    manifest=b.read_json(plan['manifest']);root=Path(plan['root']).resolve()
    validate_pair(manifest,plan['pins'])
    from actions_schedule import valid_slot, deadline
    now=int(time.time()*1000);slot=plan['expected_start_ms']
    if not valid_slot('backup',slot) or not slot<=now<=deadline('backup',slot): raise ValueError('Backup occurrence expired')
    if (os.environ.get('GITHUB_REPOSITORY')!=binding['repository']
            or os.environ.get('GITHUB_SHA')!=binding['code_sha']
            or os.environ.get('GITHUB_REF')!='refs/heads/'+binding['branch']
            or os.environ.get('GITHUB_WORKFLOW_REF')!=binding['repository']+'/'+binding['workflow']+'@refs/heads/'+binding['branch']
            or os.environ.get('GITHUB_RUN_ATTEMPT')!='1'
            or not (os.environ.get('GITHUB_RUN_ID') or '').isdigit()):
        raise ValueError('Independent verifier actual entry differs')
    from produktion_actions_runner import check_code_pin
    check_code_pin(binding['code_sha'])
    if head(plan['mirror'],d['branch'],budget)!=d['commit_sha']: raise ValueError('Readback destination moved')
    names=b.git(plan['mirror'],budget,'ls-tree','-r','--name-only',d['commit_sha']).decode().splitlines()
    # Dedicated backup branch contains exactly this immutable package set.
    if set(names)!=set(manifest['files'])|{d['manifest_path']}: raise ValueError('Readback package tree differs')
    with b.batch(plan['mirror'],budget) as read:
        raw=read(d['commit_sha']+':'+d['manifest_path'],'blob',b.MAX_MANIFEST)
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if json.loads(raw)!=manifest or blob!=d['blob_sha']: raise ValueError('Readback manifest differs')
        for name,item in manifest['files'].items():
            budget.check()
            if Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name: raise ValueError('Unsafe package path')
            raw=read(d['commit_sha']+':'+name,'blob',b.MAX_PACKAGE)
            if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
                raise ValueError('Uploaded package blob differs')
    verification=restore(root,manifest,plan['target'],plan['pins'],budget)
    if head(plan['mirror'],d['branch'],budget)!=d['commit_sha']: raise ValueError('Readback moved during verification')
    receipt=dict(schema='p4-independent-backup-receipt-v1',manifest=manifest,manifest_sha256=digest(manifest),
        verification=verification,expected_start_ms=slot,verifier=binding,
        verifier_run_id=os.environ['GITHUB_RUN_ID'],destination=d,upload_readback_verified=True)
    if len((canonical(receipt)+'\n').encode())>b.MAX_MANIFEST: raise ValueError('Independent receipt byte limit')
    b.write_json(plan['receipt_out'],receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('append');a.add_argument('--plan',required=True)
    a=sub.add_parser('verify-readback');a.add_argument('--plan',required=True)
    r=sub.add_parser('restore');r.add_argument('--root',required=True);r.add_argument('--manifest',required=True)
    r.add_argument('--required-pins',required=True);r.add_argument('--target',required=True)
    args=p.parse_args()
    try:
        if args.command=='append': result=append(b.read_json(args.plan))
        elif args.command=='verify-readback': result=verify_readback(b.read_json(args.plan))
        else: result=restore(args.root,b.read_json(args.manifest),args.target,b.read_json(args.required_pins))
        print(canonical(result))
    except Exception:
        print('Paired backup/restore refused; preserve evidence and review.',file=sys.stderr);sys.exit(20)
