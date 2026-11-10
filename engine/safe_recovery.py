"""Close-only recovery after completed business work. Never own, send or replay.

The only supported mutation closes an open fence against an independently
confirmed successful stream after all workers have ended. Historical aborted
maintenance remains a separate, unchanged validator.
"""
from copy import deepcopy
import hashlib
import re
from types import SimpleNamespace
from production_contract import canonical,digest,validate_v2

SCHEMA='btc-close-only-recovery-v1'

def require(ok):
    if not ok:raise ValueError('Recovery evidence refused')

def receipts(snapshot):
    validate_v2(snapshot)
    messages=[message for state in [snapshot['engine'],*snapshot['commands'].values()]
              for message in state.get('_delivery',{}).get('messages',[])]
    require(all(message['status']=='confirmed' and type(message.get('receipt')) is int
        and message['receipt']>0 and message.get('attempts')==1
        and message.get('target')==snapshot['control']['target_binding'] for message in messages))
    return digest(messages)

def completed(envelope,deployment,run):
    snapshot=envelope['snapshot'];control=snapshot['control'];validate_v2(snapshot)
    require(control['owner'] is None and control['mode']=='active'
        and not control['health'].get('restore_requires_reconciliation')
        and all(control[key]==deployment[key] for key in ('code_sha','config_sha256','store_id','bot_identity'))
        and run['kind'] in ('signal','watch') and run['attempt']=='1')
    from produktion_actions_runner import verify_health
    verify_health(SimpleNamespace(snapshot=snapshot),deployment,run)
    finished=control['health']['successful_runs'][run['kind']]['run']
    require(control['health'].get('completion_candidate')==finished)
    if run['kind']=='signal':
        require(snapshot['engine']['last_signal_ts']==int(run['expected_start_ms'])//14400000*14400000-14400000)
    else:
        require(finished['started_ms']<=finished['watch_observed_ms']<=finished['finished_ms']
            and finished['watch_candle_open_ms']==finished['watch_observed_ms']//14400000*14400000)
    return receipts(snapshot)

def validate(value,envelope,locator):
    proof=value['completion']['recovery'];run=value['run']
    require(proof['schema']==SCHEMA and value['phase']=='closed'
        and 'outcome' not in value['completion'] and proof['failed_run']==run['id']
        and type(proof['confirmed_at_ms']) is int and proof['confirmed_at_ms']>0
        and all(re.fullmatch('[0-9a-f]{64}',proof[key]) for key in
                ('old_fence_sha256','run_sha256','jobs_sha256','policy_sha256','receipts_sha256'))
        and re.fullmatch('[0-9a-f]{40}',proof['old_fence_commit'])
        and value['completion']['stream']==locator
        and envelope['revision']==locator['revision']
        and envelope['body_digest']==digest(envelope['snapshot'])==locator['snapshot_digest']
        and all(locator[key]==expected for key,expected in {
            'adapter':'github','repo':value['deployment']['private_store_repository'],
            'branch':value['deployment']['store_branch'],'path':'delivery/stream.json',
            'store_id':value['deployment']['store_id']}.items())
        and re.fullmatch('[0-9a-f]{40}',locator['commit_sha'])
        and hashlib.sha1(b'blob '+str(len(canonical(envelope).encode())).encode()+b'\0'
                         +canonical(envelope).encode()).hexdigest()==locator['blob_sha'])
    require(completed(envelope,value['deployment'],run)==proof['receipts_sha256'])
    old=deepcopy(value);old.update(phase='open',completion=None,write_id=proof['old_write_id'])
    require(hashlib.sha256(canonical(old).encode()).hexdigest()==proof['old_fence_sha256'])

def candidate(old,envelope,locator,review,write_id):
    require(old['phase']=='open' and old['completion'] is None)
    require(review['workers_terminated'] is True and review['run_completed'] is True)
    proof={key:review[key] for key in ('old_fence_commit','old_fence_sha256','run_sha256',
        'jobs_sha256','policy_sha256','confirmed_at_ms')}
    proof.update(schema=SCHEMA,old_write_id=old['write_id'],failed_run=old['run']['id'],
                 receipts_sha256=completed(envelope,old['deployment'],old['run']))
    value={**deepcopy(old),'phase':'closed','write_id':write_id,
           'completion':{'stream':deepcopy(locator),'recovery':proof}}
    validate(value,envelope,locator)
    return value
