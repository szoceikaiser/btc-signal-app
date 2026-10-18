"""Manual synthetic store-write / existing hosted backup entries. No sender.

No ref creation, retries, recovery, market or Telegram calls. A partial store
publication remains evidence and prohibits another run against the seed pins.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time
import urllib.parse

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'engine')]
import p4_backup_probe_prepare as prep
import p4_hosted_backup as h
import p3_backup_chain as b
import p4_backup_pair as pair
import actions_delivery as actions
import actions_schedule as slots
import github_delivery as github
import public_access as public
import telegram_outbox as box
from production_contract import canonical,digest


class ProbeBudget(h.Budget):
    """Smaller request counts, unchanged deadlines/transfer/resource ceilings."""
    def reserve(self,method,request_bytes,response_limit):
        if self.http>=256 or (method!='GET' and self.mutations>=64):
            raise ValueError('Synthetic probe request cap')
        super().reserve(method,request_bytes,response_limit)


def validate(runtime):
    if runtime.get('probe_name')!=prep.NAME or runtime.get('enabled') is not True:
        raise ValueError('Synthetic runtime disabled')
    prep.validate_access(runtime['public_access'])
    d=runtime['deployment'];public.deployment(runtime['public_access'],d)
    if (d['store_branch']!=prep.BRANCHES['stream'] or d['fence_branch']!=prep.BRANCHES['fence']
            or runtime['identity']['store_id']!=prep.NAME+'-store' or runtime['identity']['stream_id']!=prep.NAME+'-stream'
            or d['bot_identity']!=prep.NAME+'-NO-BOT'
            or runtime['runtime_sha256']!=digest({k:v for k,v in runtime.items() if k!='runtime_sha256'})
            or platform.system()!='Linux' or sys.version_info[:3]!=(3,12,14)):
        raise ValueError('Synthetic identity/runtime differs')
    for key,repo,branch in (('source',prep.STORE,'stream'),('backup',prep.BACKUP,'backup'),('receipts',prep.RECEIPTS,'receipts')):
        if runtime[key]!={'repository':repo,'id':prep.REPOS[repo]['id'],'branch':prep.BRANCHES[branch]}:
            raise ValueError('Synthetic destination differs')


def store(runtime,root):
    validate(runtime);binding=runtime['store_writer'];budget=ProbeBudget(root)
    expected={'GITHUB_REPOSITORY':prep.CODE,'GITHUB_REF':'refs/heads/main',
        'GITHUB_WORKFLOW_REF':prep.CODE+'/.github/workflows/backup-store-probe.yml@refs/heads/main',
        'GITHUB_RUN_ATTEMPT':'1','GITHUB_EVENT_NAME':'workflow_dispatch','RUNNER_OS':'Linux',
        'BTC_HOSTED_RUNTIME_SHA256':runtime['runtime_sha256']}
    if any(os.environ.get(k)!=v for k,v in expected.items()): raise ValueError('Manual store entry differs')
    if binding['repository']!=prep.CODE or binding['repository_id']!=1309164619 or binding['branch']!='main' or binding['workflow']!='.github/workflows/backup-store-probe.yml':
        raise ValueError('Pinned store workflow differs')
    if any(not (os.environ.get(k,'').isdigit() and int(os.environ[k])>0) for k in ('GITHUB_RUN_ID','GITHUB_RUN_NUMBER')):
        raise ValueError('Actual run identity missing')
    h.check_code_pin(binding['code_sha'],budget)
    # Only this step receives this writer. Backup/verifier never receive it.
    writer=os.environ.get('BTC_REVIEWED_STORE_TOKEN');token=os.environ.get('GITHUB_TOKEN')
    forbidden=('BTC_HOSTED_BACKUP_WRITE_TOKEN','BTC_HOSTED_RECEIPT_WRITE_TOKEN','BTC_DELIVERY_GITHUB_TOKEN',
        'TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID','COINALYZE_API_KEY')
    if not writer or not token or writer==token or any(os.environ.get(k) for k in forbidden):
        raise ValueError('Distinct synthetic store writer required')
    public.credential(runtime['public_access'],'sender_write',prep.STORE,[prep.BRANCHES[k] for k in ('stream','fence')])
    client=h.Client(writer,{prep.STORE},{prep.STORE},budget);client.access=runtime['public_access']
    meta=h.Client(token,{prep.CODE},set(),budget,metadata=True);meta.access=runtime['public_access']
    meta.repository({'repository':prep.CODE,'id':1309164619,'branch':'main'},False)
    slot=h.metadata(meta,runtime,binding)
    s=runtime['source'];f={**s,'branch':prep.BRANCHES['fence']}
    public.check(client,runtime['public_access'],[(prep.STORE,t['branch']) for t in (s,f)],
                 [(prep.STORE,t['branch']) for t in (s,f)])
    # Both seeds must still be exact before the first mutation. No resume path.
    seed=runtime['probe_seed']
    if client.ref(s)!=seed['stream'] or client.ref(f)!=seed['fence']: raise ValueError('Seed moved; no repeat/resume')
    _,sf=client.tree(s,seed['stream']);_,ff=client.tree(f,seed['fence'])
    if set(sf)!={github.STORE_PATH} or set(ff)!={actions.FENCE_PATH}: raise ValueError('Foreign seed files')
    raw=client.blob(s,sf[github.STORE_PATH]);env=b.parser(runtime['identity'])._parse({'body':raw})
    fence=actions.parse_fence({'body':client.blob(f,ff[actions.FENCE_PATH])},runtime['deployment'])
    if env['revision']!=0 or env['snapshot']['control']['mode']!='blocked' or fence['run'] is not None:
        raise ValueError('Fresh blocked synthetic seed required')
    # Fence uses a fictional signal cursor solely to exercise the existing fence
    # history contract. No Signal workflow, engine or completion is executed.
    run={'number':1,'id':'910151','attempt':'1','workflow':'.github/workflows/signal.yml','kind':'signal',
         'expected_start_ms':str(slot+2*slots.MINUTE),'deadline_utc_ms':slot+45*slots.MINUTE}
    opened=deepcopy(fence);opened.update(phase='open',run=run,completion=None,write_id=prep.NAME+'-open')
    opened['cursors'][run['workflow']]={'number':run['number'],'id':run['id']}
    pair.transition(fence,opened)
    actions.parse_fence({'body':canonical(opened).encode()},runtime['deployment'])
    op=h.publish(client,f,seed['fence'],{actions.FENCE_PATH:canonical(opened).encode()},{actions.FENCE_PATH})
    snapshot=deepcopy(env['snapshot'])
    command={'result':prep.NAME,'_delivery':{'version':1,'messages':[],
        'signals':{'signals':[]},'oi_history':[]}}
    box.enqueue(command['_delivery'],'synthetic',prep.NAME,0,{'synthetic':True},'SYNTHETIC BACKUP ONLY - NEVER SEND')
    command['_delivery']['messages'][0].update(status='confirmed',attempts=1,
        target=snapshot['control']['target_binding'],receipt=910151)
    snapshot['commands'][prep.NAME]=command
    snapshot['control']['health']['synthetic_backup_probe']=prep.NAME
    successor={**env,'snapshot':snapshot,'revision':1,'parent_digest':env['body_digest'],
               'body_digest':digest(snapshot),'write_id':prep.NAME+'-progress'}
    stream_raw=canonical(successor).encode();b.parser(runtime['identity'])._parse({'body':stream_raw})
    if client.ref(s)!=seed['stream'] or client.ref(f)!=op['commit_sha']: raise ValueError('Pair moved before stream')
    sp=h.publish(client,s,seed['stream'],{github.STORE_PATH:stream_raw},{github.STORE_PATH})
    loc={'adapter':'github','repo':prep.STORE,'branch':s['branch'],'path':github.STORE_PATH,
         'store_id':runtime['identity']['store_id'],'commit_sha':sp['commit_sha'],'revision':1,
         'blob_sha':h.oid('blob',stream_raw),'snapshot_digest':successor['body_digest']}
    closed=deepcopy(opened);closed.update(phase='closed',completion={'stream':loc},write_id=prep.NAME+'-closed')
    pair.transition(opened,closed)
    if client.ref(s)!=sp['commit_sha'] or client.ref(f)!=op['commit_sha']: raise ValueError('Pair moved before close')
    cp=h.publish(client,f,op['commit_sha'],{actions.FENCE_PATH:canonical(closed).encode()},{actions.FENCE_PATH})
    public.check(client,runtime['public_access'],[(prep.STORE,t['branch']) for t in (s,f)],
                 [(prep.STORE,t['branch']) for t in (s,f)])
    if client.ref(s)!=sp['commit_sha'] or client.ref(f)!=cp['commit_sha']: raise ValueError('Final source cut moved')
    result={'schema':'btc-synthetic-store-confirmed-v1','synthetic_only':True,'engine_executed':False,
        'runtime_sha256':runtime['runtime_sha256'],
        'real_send':False,'expected_start_ms':slot,'store_run_id':os.environ['GITHUB_RUN_ID'],
        'pins':{'stream':{'commit_sha':sp['commit_sha'],'revision':1,'blob_sha':loc['blob_sha'],
                          'snapshot_digest':loc['snapshot_digest']},
                'fence':{'commit_sha':cp['commit_sha'],'revision':2,
                    'blob_sha':h.oid('blob',canonical(closed).encode()),'body_sha256':digest(closed)}},
        'metrics':{**budget.metrics(),'http':budget.http,'mutations':budget.mutations,
                   'reserved_transfer_bytes':budget.transfer}}
    b.write_json(Path(root)/'confirmed.json',result)
    return result


def cli(argv=None):
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('store','producer','verifier'));a=p.parse_args(argv)
    try:
        raw=os.environ['BTC_HOSTED_RUNTIME_JSON'].encode()
        if len(raw)>b.MAX_MANIFEST: raise ValueError('Runtime limit')
        runtime=json.loads(raw);validate(runtime)
        explicit=os.environ.get('BTC_ACTIONS_EXPLICIT_START_MS','')
        if not explicit.isdigit() or not slots.valid_slot('backup',int(explicit)):
            raise ValueError('Explicit original UTC occurrence required')
        if any(os.environ.get(k) for k in ('TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID','COINALYZE_API_KEY')):
            raise ValueError('Live credential injection forbidden')
        if a.mode!='store' and (runtime.get('pins') is None or not runtime.get('probe_store_run_id')):
            raise ValueError('Store cut must be separately reviewed and pinned first')
        original_open=h.Client.open_request
        sequence=[0]
        def audited(request,timeout):
            sequence[0]+=1;u=urllib.parse.urlsplit(request.full_url)
            row={'http_operation':sequence[0],'method':request.get_method(),'host':u.netloc,'path':u.path,'query':u.query}
            # Never log headers, request payloads, response bodies or exceptions.
            print(canonical({**row,'outcome':'started'}),flush=True)
            try:
                response=original_open(request,timeout=timeout)
                print(canonical({**row,'outcome':'response_headers','status':getattr(response,'status',None)}),flush=True)
                return response
            except Exception:
                print(canonical({**row,'outcome':'unconfirmed_stop'}),flush=True)
                raise
        h.Client.open_request=staticmethod(audited)
        if os.name=='posix':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(b.MAX_PYTHON_RSS,b.MAX_PYTHON_RSS))
        parent=Path(os.environ['RUNNER_TEMP']).resolve()
        if not parent.is_dir() or parent.is_symlink(): raise ValueError('Runner temp missing')
        root=Path(tempfile.mkdtemp(prefix='btc-probe-'+a.mode+'-',dir=parent))
        if a.mode=='store': result=store(runtime,root)
        else:
            # Existing protocol, same validation and all safety deadlines.
            # Limits change only for this explicitly bounded synthetic entry.
            h.Budget=ProbeBudget
            result=h.run(runtime,a.mode,root)
            if result['expected_start_ms']!=runtime['probe_expected_start_ms']:
                raise ValueError('Probe occurrence differs from reviewed store cut')
        print(canonical(result))  # Public synthetic evidence only; no credentials.
        return 0
    except Exception:
        print('Synthetic backup refused; preserve evidence, no retry/resume.',file=sys.stderr)
        return 20


if __name__=='__main__': sys.exit(cli())
