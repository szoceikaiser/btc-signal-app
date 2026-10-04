"""Two-step positive receipt reconciliation. No negative-proof reset exists."""
import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import durable_delivery as durable
from production_contract import canonical, digest


def _find(snapshot,mid):
    matches=[]
    for scope,state in [('engine',snapshot['engine']),*[(k,v) for k,v in snapshot['commands'].items()]]:
        for m in state.get('_delivery',{}).get('messages',[]):
            if m['id']==mid: matches.append((scope,m))
    if len(matches)!=1: raise ValueError('Message ID is absent or ambiguous')
    return matches[0]


def _check(store,evidence):
    needed=('message_id','target_binding','text_sha256','attempt','receipt_message_id',
            'attempt_started_ms','observed_at_utc','reviewer','proof_path','proof_sha256')
    if any(k not in evidence for k in needed) or evidence.get('status')!='confirmed':
        raise ValueError('Only explicit positive evidence is accepted')
    if type(evidence['receipt_message_id']) is not int or evidence['receipt_message_id']<=0:
        raise ValueError('Missing positive Telegram receipt')
    if not isinstance(evidence['reviewer'],str) or not evidence['reviewer'].strip():
        raise ValueError('Named reviewer required')
    if not evidence['observed_at_utc'].endswith('Z'):
        raise ValueError('UTC observation required')
    observed=int(datetime.fromisoformat(evidence['observed_at_utc'].replace('Z','+00:00')).timestamp()*1000)
    proof=Path(evidence['proof_path'])
    if not proof.is_file() or hashlib.sha256(proof.read_bytes()).hexdigest()!=evidence['proof_sha256']:
        raise ValueError('Protected proof missing or altered')
    scope,m=_find(store.snapshot,evidence['message_id'])
    if (m['status']!='uncertain' or m['attempts']!=evidence['attempt'] or
            m.get('attempt_started_ms')!=evidence['attempt_started_ms'] or
            m['target']!=evidence['target_binding'] or m['text_sha256']!=evidence['text_sha256'] or
            evidence['target_binding']!=store.snapshot['control']['target_binding']):
        raise ValueError('Evidence does not match uncertain attempt')
    if not m['attempt_started_ms']-5*60*1000 <= observed <= m['attempt_started_ms']+60*60*1000:
        raise ValueError('External message time does not match delivery attempt')
    return scope,m


def review(store_path,store_id,evidence_path,out):
    out=Path(out)
    if out.exists(): raise FileExistsError(out)
    evidence=json.loads(Path(evidence_path).read_text(encoding='utf-8'))
    with durable.VolumeStore(store_path,store_id) as store:
        if store.snapshot['version']!=2: raise ValueError('P2 store required')
        scope,m=_check(store,evidence)
        body={'schema':'produktion-reconciliation-review-v1','store_id':store_id,
              'expected_revision':store.revision,'scope':scope,'message_id':m['id'],
              'attempt':m['attempts'],'attempt_started_ms':m['attempt_started_ms'],
              'text_sha256':m['text_sha256'],
              'target_binding':m['target'],'receipt_message_id':evidence['receipt_message_id'],
              'reviewer':evidence['reviewer'],'observed_at_utc':evidence['observed_at_utc'],
              'proof_sha256':evidence['proof_sha256'],'proof_path':str(Path(evidence['proof_path']).resolve()),
              'evidence_sha256':digest(evidence)}
    plan={**body,'review_sha256':digest(body)}
    out.write_text(canonical(plan)+'\n',encoding='utf-8')
    return plan


def apply_review(store_path,store_id,review_path,evidence_path,review_sha256,expected_revision):
    plan=json.loads(Path(review_path).read_text(encoding='utf-8'))
    body={k:v for k,v in plan.items() if k!='review_sha256'}
    if (digest(body)!=plan.get('review_sha256') or plan['review_sha256']!=review_sha256 or
            plan['expected_revision']!=expected_revision or plan['store_id']!=store_id):
        raise ValueError('Review hash/revision mismatch')
    evidence=json.loads(Path(evidence_path).read_text(encoding='utf-8'))
    if digest(evidence)!=plan['evidence_sha256']:
        raise ValueError('Evidence changed since review')
    with durable.VolumeStore(store_path,store_id) as store:
        if store.revision!=expected_revision: raise ValueError('Stale review revision')
        scope,m=_check(store,evidence)
        if scope!=plan['scope'] or m['id']!=plan['message_id'] or m['text_sha256']!=plan['text_sha256']:
            raise ValueError('Review no longer describes uncertain message')
        m['status']='confirmed'; m['receipt']=evidence['receipt_message_id']; m['reason']=None
        store.snapshot['control']['reconciliations'].append({
            'review_sha256':review_sha256,'message_id':m['id'],'scope':scope,
            'from':'uncertain','to':'confirmed','attempt':m['attempts'],
            'receipt_message_id':m['receipt'],'reviewer':evidence['reviewer'],
            'observed_at_utc':evidence['observed_at_utc'],
            'proof_sha256':evidence['proof_sha256'],'previous_revision':expected_revision})
        store.commit()
        return {'store_id':store_id,'revision':store.revision,'message_id':m['id'],
                'status':'confirmed','mode':store.snapshot['control']['mode']}


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--store',required=True); p.add_argument('--store-id',required=True)
    mode=p.add_mutually_exclusive_group(required=True); mode.add_argument('--review'); mode.add_argument('--apply-review')
    p.add_argument('--evidence',required=True); p.add_argument('--review-sha256'); p.add_argument('--expected-revision',type=int)
    a=p.parse_args()
    if a.review:
        result=review(a.store,a.store_id,a.evidence,a.review)
    else:
        if not a.review_sha256 or a.expected_revision is None: p.error('Review hash and expected revision required')
        result=apply_review(a.store,a.store_id,a.apply_review,a.evidence,a.review_sha256,a.expected_revision)
    print(canonical(result))
