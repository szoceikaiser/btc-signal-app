"""Read-only health evaluation; no alarm transport."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import durable_delivery as durable
from production_contract import CANDLE_MS, canonical


def evaluate(store_path, store_id, now_ms=None):
    now_ms=int(time.time()*1000) if now_ms is None else now_ms
    with durable.read_only_volume(store_path,store_id) as store:
        snapshot=store.snapshot
        if snapshot['version']!=2:
            raise ValueError('Health requires v2 store')
        control=snapshot['control']
        messages=[m for state in [snapshot['engine'],*snapshot['commands'].values()]
                  for m in state.get('_delivery',{}).get('messages',[])]
        uncertain=sum(m['status'] in ('sending','uncertain') for m in messages)
        pending=sum(m['status'] in ('pending','rejected') for m in messages)
        h=control['health']
        last_signal=snapshot['engine']['last_signal_ts']
        last_watch=h.get('last_watch_check_ms')
        last_backup=h.get('last_verified_backup_ms')
        started=h.get('run_started_ms')
        alarms=[]
        if uncertain: alarms.append('uncertain_delivery')
        if now_ms>last_signal+CANDLE_MS+45*60*1000: alarms.append('signal_overdue')
        if last_watch is None or now_ms-last_watch>45*60*1000: alarms.append('watch_overdue')
        if started is not None and h.get('run_finished_ms',-1)<started and now_ms-started>15*60*1000:
            alarms.append('run_overdue')
        if last_backup is None or now_ms-last_backup>26*60*60*1000: alarms.append('backup_overdue')
        if h.get('consecutive_mutex_conflicts',0)>=2: alarms.append('mutex_conflicts')
        if control['mode']!='active': alarms.append('stream_'+control['mode'])
        # Legacy local timestamps cannot certify a current external run.
        alarms.append('external_run_binding_unverified')
        return {'schema':'produktion-health-v1','store_id':store_id,'revision':store.revision,
                'mode':control['mode'],'code_sha':control['code_sha'],
                'config_sha256':control['config_sha256'],'last_signal_ts':last_signal,
                'last_watch_check_ms':last_watch,'last_verified_backup_ms':last_backup,
                'pending':pending,'uncertain':uncertain,'alarms':alarms,
                'healthy':not alarms, 'http_status':503}


def evaluate_bound(store_path, store_id, policy, runs, backup, now_ms):
    from freshness import evaluate as bound, response
    try:
        with durable.read_only_volume(store_path,store_id) as store:
            return bound(store.snapshot, store.revision, store.read_revision,
                         runs, policy, now_ms, backup)
    except Exception:
        return response('api_or_store_unavailable')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--store',required=True); p.add_argument('--store-id',required=True)
    a=p.parse_args()
    try:
        result=evaluate(a.store,a.store_id)
        print(canonical(result))
        sys.exit(0 if result['healthy'] else 30 if result['uncertain'] else 20)
    except sqlite3.OperationalError as exc:
        mutex='locked' in str(exc).lower()
        print(canonical({'schema':'produktion-health-v1',
                         'error_class':'mutex_conflict' if mutex else 'store_unavailable'}))
        sys.exit(10 if mutex else 40)
    except (ValueError,KeyError,OSError):
        print(canonical({'schema':'produktion-health-v1','error_class':'invalid_store'})); sys.exit(40)
