"""Offline preparation only. No network, credentials, engine entry or dispatch.

New protection IDs cannot be known before setup. Default output is explicitly
disabled. --access accepts a separately reviewed NEW-branch admission document;
it never relabels historical production-branch evidence as new-branch proof.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'engine'), str(ROOT/'tools')]
import actions_delivery as actions
import github_delivery as github
import public_access as public
import produktion_migrate as migrate
import produktion_store
import produktion_actions_runner as entry
import p3_backup_chain as b
import p4_hosted_backup as h
from production_contract import canonical, digest, effective_config

NAME = 'btc-synthetic-backup-20261015'
CODE = 'szoceikaiser/btc-signal-app'
STORE = 'szoceikaiser/btc-delivery-store'
BACKUP = 'szoceikaiser/btc-delivery-backup'
RECEIPTS = 'szoceikaiser/btc-delivery-backup-verification'
BRANCHES = {'stream':'probe-20261015-stream', 'fence':'probe-20261015-fence',
            'migration':'probe-20261015-migration', 'backup':'probe-20261015-packages',
            'receipts':'probe-20261015-receipts'}
REPOS = {STORE:{'id':1420314517,'visibility':'public','branches':[BRANCHES[k] for k in ('stream','fence','migration')]},
         BACKUP:{'id':1420315667,'visibility':'public','branches':[BRANCHES['backup']]},
         RECEIPTS:{'id':1420316189,'visibility':'public','branches':[BRANCHES['receipts']]},
         CODE:{'id':1309164619,'visibility':'public','branches':['main']}}
WORKFLOWS = {'store_writer':'backup-store-probe', 'producer':'backup', 'verifier':'backup-verify'}


def put(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((canonical(value)+'\n').encode())


def git(repo, *args, data=None):
    p=subprocess.run(['git','-c','core.hooksPath=NUL',*args],cwd=repo,input=data,
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    return p.stdout.strip().decode()


def object_write(repo, kind, raw):
    pin=git(repo,'hash-object','-w','-t',kind,'--stdin',data=raw)
    if pin!=h.oid(kind,raw): raise ValueError('Local Git object differs')
    return pin


def tree_write(repo, files):
    node={}
    for name,raw in files.items():
        h.safe_path(name);cur=node;parts=name.split('/')
        for part in parts[:-1]: cur=cur.setdefault(part,{})
        cur[parts[-1]]=object_write(repo,'blob',raw)
    def build(cur):
        rows=[]
        for name,value in cur.items():
            folder=isinstance(value,dict)
            rows.append((name+('/' if folder else ''),('40000' if folder else '100644').encode()+b' '+name.encode()+b'\0'+
                         bytes.fromhex(build(value) if folder else value)))
        return object_write(repo,'tree',b''.join(raw for _,raw in sorted(rows)))
    return build(node)


def commit(repo, branch, files, parent=None):
    tree=tree_write(repo,files)
    raw=('tree '+tree+'\n'+('parent '+parent+'\n' if parent else '')+
         'author Synthetic backup <fixture@example.invalid> 1792022400 +0000\n'
         'committer Synthetic backup <fixture@example.invalid> 1792022400 +0000\n\n'+NAME+'\n').encode()
    pin=object_write(repo,'commit',raw)
    git(repo,'update-ref','refs/heads/'+branch,pin)
    return pin,tree


def validate_access(access):
    if access['repositories']!=REPOS: raise ValueError('Exact synthetic targets and real IDs required')
    # This is structural validation of supplied review bytes, not a provider read.
    class Reviewed:
        def request(self,method,repo,tail):
            raise ValueError('Provider response required; preparation never performs HTTP')
    for repo,t in REPOS.items():
        for branch in t['branches']: public.target(access,repo,branch)
    for repo,keys in ((STORE,('stream','fence','migration')),(BACKUP,('backup',)),(RECEIPTS,('receipts',))):
        for key in keys:
            branch=BRANCHES[key];p=access['protections'][repo+'@'+branch]
            if p['repository_id']!=REPOS[repo]['id'] or p['repository']!=repo or p['branch']!=branch:
                raise ValueError('New protection review missing')
            if not p['rulesets'] or not re.fullmatch('[0-9a-f]{64}',p['active_rules_sha256']):
                raise ValueError('Actual rule IDs/hash required')
            for rid,rs in p['rulesets'].items():
                v=rs['bypass_review']
                if (not rid.isdigit() or int(rid)<=0 or v['status']!='actually-reviewed' or v['bypass_actors']!=[]
                        or v['repository']!=repo or v['repository_id']!=REPOS[repo]['id'] or v['branch']!=branch
                        or v['ruleset_id']!=int(rid) or v['public_sha256']!=rs['public_sha256']
                        or v['sha256']!=public.review_hash(v)):
                    raise ValueError('Actual separate bypass review required')
    for role,repo,keys in (('sender_write',STORE,('stream','fence')),('backup_write',BACKUP,('backup',)),
                           ('receipt_write',RECEIPTS,('receipts',))):
        public.credential(access,role,repo,[BRANCHES[k] for k in keys])


def prepare(out, code_pin, access=None, entry_pin=None):
    if not re.fullmatch('[0-9a-f]{40}',code_pin): raise ValueError('Exact code commit required')
    git(ROOT,'cat-file','-e',code_pin+'^{commit}')
    if access is not None:
        validate_access(access)
        if not re.fullmatch('[0-9a-f]{40}',entry_pin or ''): raise ValueError('Actual installed main entry pin required')
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    enabled=access is not None
    access=deepcopy(access) if enabled else {'schema':'btc-public-access-v1','enabled':False,
        'repositories':deepcopy(REPOS),'protections':{},'credential_reviews':{}}
    put(out/'public-access.json',access)
    # No historical state/config/market data is read. This miniature legacy
    # input is constructed entirely from literals and converted by the real tool.
    cfg={'muster_cvd':'usd','bias_short':False,'ausbruch_ruecktest':False}
    old={**cfg,'muster_cvd':'alt'};B=1785542400000;W=B+14400000
    source=out/'source';source.mkdir()
    values={'state.json':{'pos_state':'FLAT','last_signal_ts':B,'config':old},
            'signals.json':{'signals':[{'ts':B,'type':'SYNTHETIC_BACKUP_ONLY','price':100}]},
            'oi_history.json':[{'ts':B,'value':1,'synthetic':True}],'config-source.json':old}
    for name,value in values.items(): put(source/name,value)
    files={n:{'sha256':hashlib.sha256((source/n).read_bytes()).hexdigest(),'size':(source/n).stat().st_size} for n in values}
    files['watch.json']={'presence':'missing'}
    manifest={'schema':'produktion-source-v1','mode':'rehearsal','repository':NAME,'code_sha':code_pin,
        'source_sha':code_pin,'git_tree':git(ROOT,'rev-parse',code_pin+'^{tree}'),
        'captured_at_utc':'2026-10-15T00:00:00Z','files':files}
    cutover={'freeze_at_ms':W+1000,'last_persisted_B':B,'source_sha':code_pin,
        'last_runs':[{'id':NAME,'status':'complete'}],'synthetic':True,
        'writers_stopped':False,'snapshot_consistent':False,'stream_id':NAME+'-stream',
        'store_id':NAME+'-store','target_binding':digest(NAME+'-NO-TELEGRAM'),
        'bot_identity':NAME+'-NO-BOT','code_sha':code_pin}
    for name,value in (('source-manifest.json',manifest),('cutover.json',cutover),('config-target.json',cfg)):
        put(out/name,value)
    migration=out/'migration'
    migrate.convert(source,out/'source-manifest.json',out/'cutover.json',out/'config-target.json',migration)
    snapshot=produktion_store.verify_package(migration)
    runtime=json.loads((ROOT/'ops/produktion/hosted-backup-runtime.disabled.json').read_text())
    d=runtime['deployment'];d.update(code_sha=code_pin,store_id=cutover['store_id'],config_sha256=digest(effective_config(cfg)),
        bot_identity=cutover['bot_identity'],activation_review_sha256=digest({'synthetic_only':NAME}),
        store_branch=BRANCHES['stream'],fence_branch=BRANCHES['fence'],public_access_sha256=digest(access))
    runtime.update(enabled=enabled,public_access=access,deployment=entry.deployment(d),
        identity={'repo':STORE,'branch':BRANCHES['stream'],'store_id':cutover['store_id'],'stream_id':cutover['stream_id']},
        activation_review_sha256=digest({'synthetic_only':NAME}),pins=None,probe_name=NAME)
    for key,repo in (('source',STORE),('backup',BACKUP),('receipts',RECEIPTS)):
        runtime[key]={'repository':repo,'id':REPOS[repo]['id'],'branch':BRANCHES['stream' if key=='source' else key]}
    for key,name in WORKFLOWS.items():
        raw=(ROOT/'ops/sicherungsprobe'/f'{name}.disabled.yml').read_bytes()
        # Default files are inactive; approval materialization changes exactly one gate.
        active=raw.replace(b'if: ${{ false }} # REVIEW-GATE',
            b"if: ${{ github.ref == 'refs/heads/main' && github.run_attempt == 1 && inputs.probe_name == '"+NAME.encode()+b"' }}")
        if active==raw: raise ValueError('Missing disabled review gate')
        dest=out/'workflow-overlay/.github/workflows'/f'{name}.yml';dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(active)
        runtime[key]={'repository':CODE,'repository_id':REPOS[CODE]['id'],'branch':'main',
            'workflow':'.github/workflows/'+name+'.yml','code_sha':code_pin,'probe_entry_sha':entry_pin,
            'workflow_sha256':hashlib.sha256(active).hexdigest()}
    repos={}
    for key,repo_name in (('store',STORE),('backup',BACKUP),('receipts',RECEIPTS)):
        repo=out/(key+'.git');repo.mkdir();git(repo,'init','--bare');repos[key]=repo
    migration_files={p.relative_to(migration).as_posix():p.read_bytes() for p in sorted(migration.rglob('*')) if p.is_file()}
    mp,mt=commit(repos['store'],BRANCHES['migration'],migration_files)
    runtime['migration']={'target':{'repository':STORE,'id':REPOS[STORE]['id'],'branch':BRANCHES['migration']},
        'commit_sha':mp,'tree_sha':mt,'files':{n:{'sha':h.oid('blob',v),'bytes':len(v)} for n,v in migration_files.items()}}
    seed=json.loads(github.initial_envelope(snapshot,STORE,BRANCHES['stream'],cutover['store_id']))
    seed['write_id']=NAME+'-seed'
    stream_raw=canonical(seed).encode();fence_raw=actions.seed_fence(runtime['deployment'])
    sp,st=commit(repos['store'],BRANCHES['stream'],{github.STORE_PATH:stream_raw})
    fp,ft=commit(repos['store'],BRANCHES['fence'],{actions.FENCE_PATH:fence_raw})
    bp,bt=commit(repos['backup'],BRANCHES['backup'],{})
    rp,rt=commit(repos['receipts'],BRANCHES['receipts'],{})
    runtime['probe_seed']={'stream':sp,'fence':fp,'backup':bp,'receipts':rp}
    runtime['runtime_sha256']=digest({k:v for k,v in runtime.items() if k!='runtime_sha256'})
    put(out/'runtime.json',runtime)
    # Bundles contain ONLY the five named synthetic refs; never --all/mirror.
    for key,ks in (('store',('stream','fence','migration')),('backup',('backup',)),('receipts',('receipts',))):
        git(repos[key],'bundle','create',str(out/(key+'.bundle')),*['refs/heads/'+BRANCHES[k] for k in ks])
        git(repos[key],'fsck','--full','--no-reflogs')
    put(out/'SEEDS.json',{'synthetic_only':True,'bootstrap_executed':False,'code_sha':code_pin,
        'heads':runtime['probe_seed'],'migration':runtime['migration'],'stream_tree':st,'fence_tree':ft,
        'backup_tree':bt,'receipts_tree':rt,'pending_new_protection_review':not enabled})
    inventory={p.relative_to(out).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in sorted(out.rglob('*')) if p.is_file() and not any(x.endswith('.git') for x in p.relative_to(out).parts)}
    put(out/'FILES.json',inventory)
    return runtime


def seal_cut(runtime, store_result):
    if (runtime.get('probe_name')!=NAME or runtime.get('enabled') is not True
            or runtime['runtime_sha256']!=digest({k:v for k,v in runtime.items() if k!='runtime_sha256'})
            or store_result.get('schema')!='btc-synthetic-store-confirmed-v1'
            or store_result.get('runtime_sha256')!=runtime['runtime_sha256']
            or store_result.get('synthetic_only') is not True or store_result.get('engine_executed') is not False
            or store_result.get('real_send') is not False
            or store_result['pins']['stream']['revision']!=1 or store_result['pins']['fence']['revision']!=2):
        raise ValueError('Exact reviewed store result required')
    value=deepcopy(runtime);value['pins']=store_result['pins']
    value['probe_store_run_id']=store_result['store_run_id']
    value['probe_expected_start_ms']=store_result['expected_start_ms']
    value['runtime_sha256']=digest({k:v for k,v in value.items() if k!='runtime_sha256'})
    return value


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--code-pin')
    p.add_argument('--access',help='Separately reviewed NEW-branch access JSON; never secret values')
    p.add_argument('--entry-pin',help='Exact installed main workflow commit; separate from code checkout pin')
    p.add_argument('--seal-runtime',help='Instead of preparing: original admitted runtime file')
    p.add_argument('--store-result',help='Separately reviewed public confirmed store result')
    a=p.parse_args()
    if a.seal_runtime:
        value=seal_cut(json.loads(Path(a.seal_runtime).read_text()),json.loads(Path(a.store_result).read_text()))
        with Path(a.out).open('x',encoding='utf-8',newline='\n') as f: f.write(canonical(value)+'\n')
    else:
        prepare(a.out,a.code_pin,json.loads(Path(a.access).read_text()) if a.access else None,a.entry_pin)
    print('Offline synthetic fixture prepared; no provider operations performed.')
