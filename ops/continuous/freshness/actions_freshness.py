"""Monitor-specific deadline and final readback over the reviewed validators."""
from copy import deepcopy
import json
import time
import urllib.parse
import actions_delivery as actions
import actions_schedule as slots
import github_delivery as github
from production_contract import digest
from actions_freshness import (Reader as ReviewedReader, MAX_GET, verify_fence_run,
                               read_runs, verify_completions, read_backup)

MAX_SECONDS = 40


class MonitorFailure(github.StoreUnavailable):
    pass


class EvidenceChanged(ValueError):
    pass


def time_left(budget):
    remaining=MAX_SECONDS-(time.monotonic()-budget.started)
    if remaining<=0:
        raise MonitorFailure('time_limit')
    return remaining


def failure(phase,exc):
    from freshness import response
    if isinstance(exc,MonitorFailure):
        reason=exc.args[0]
    elif isinstance(exc,EvidenceChanged):
        reason='evidence_changed'
    elif isinstance(exc,(ValueError,KeyError,TypeError)):
        reason='evidence_invalid'
    else:
        reason='evidence_unavailable'
    result=response('candidate_evidence_'+('invalid' if reason in ('evidence_invalid','evidence_changed') else 'unavailable'))
    result['diagnostic']={'phase':phase,'reason':reason}
    return result


class Reader(ReviewedReader):
    def _request(self,method,route,payload=None):
        if (method!='GET' or payload is not None
                or not any(route==self._route(r,'') or route.startswith(self._route(r,'/')) for r in self.repositories)):
            raise MonitorFailure('scope_refused')
        self.timeout=min(3,time_left(self.budget))
        if self.budget.requests>=MAX_GET: raise MonitorFailure('get_limit')
        from public_access import tail_allowed
        parts=route.split('/',4);tail='/'+parts[4] if len(parts)==5 else ''
        if not tail_allowed(tail,self.metadata_routes): raise MonitorFailure('scope_refused')
        from job_quota import cached,QuotaStopped
        if self.quota_headers.stopped: raise MonitorFailure('provider_quota')
        hit=cached(self,route)
        if hit is not None: return hit
        self.budget.requests+=1
        try:
            result=github.GitHubContentsClient._request(self,method,route)
        except (github.StoreError,QuotaStopped,OSError,json.JSONDecodeError):
            # A shortened I/O timeout can be wrapped by the core provider client.
            # The shared monotonic deadline distinguishes it from a provider fault.
            time_left(self.budget)
            raise MonitorFailure('provider_quota' if self.quota_headers.stopped else 'provider_error') from None
        if '/actions/runs/' in route:
            self.mutable_metadata.setdefault(route,deepcopy(result))
        time_left(self.budget)
        return result


def check(store_reader,code_reader,backup_reader,policy,now,admission=None):
    from freshness import response
    phase='configuration'
    try:
        if policy.get('enabled') is not True or policy.get('schema')!='p4-actions-monitor-v1': raise ValueError('Monitor disabled')
        d=policy['deployment']
        if d['schedule_contract']!=slots.CONTRACT: raise ValueError('Schedule contract mismatch')
        repo=d['private_store_repository']
        phase='fence'
        fence_record=store_reader.read(repo,d['fence_branch'],actions.FENCE_PATH)
        fence=actions.parse_fence(fence_record,d)
        if 'recovery' in (fence.get('completion') or {}):
            raise ValueError('Fresh successful regular run after recovery required')
        from aborted_maintenance import refuse_healthy
        refuse_healthy(fence)
        if fence['phase']!='closed' or not fence['completion']: raise ValueError('Fence open/uninitialized')
        store_reader.current_pins[(repo,d['store_branch'],github.STORE_PATH)]=fence['completion']['stream']
        store=github.read_only(store_reader,repo,d['store_branch'],d['store_id'])
        original=deepcopy(store._record)
        if fence['completion']['stream']!=store.confirmed_record(): raise ValueError('Fence/stream completion differs')
        if fence['run']['kind']=='lage':
            from types import SimpleNamespace
            op=digest({'repository':d['code_repository'],'workflow':fence['run']['workflow'],'run_id':fence['run']['id']})
            actions.verify_command(store.snapshot,SimpleNamespace(run=fence['run'],environment={
                'BTC_DELIVERY_RUN_REPOSITORY':d['code_repository'],'BTC_DELIVERY_CODE_SHA':d['code_sha']}),op)
        else:
            from produktion_actions_runner import verify_health
            verify_health(store,d,fence['run'])
        phase='latest_run'
        verify_fence_run(code_reader,d,fence,now,policy)
        phase='schedule'
        runs,raws=read_runs(code_reader,policy,now)
        phase='completions'
        verify_completions(store,runs,policy,now)
        phase='independent_backup'
        receipt,backup_record,backup_ref=read_backup(backup_reader,code_reader,policy,now)
        phase='backup_ancestry'
        for kind,branch,path in (('stream',d['store_branch'],github.STORE_PATH),('fence',d['fence_branch'],actions.FENCE_PATH)):
            pin=receipt['manifest']['pins'][kind]
            current=original if kind=='stream' else fence_record
            if not store_reader.is_ancestor(repo,pin['commit_sha'],current['commit_sha']): raise ValueError('Foreign backup history')
            observed=store_reader.read_pinned(repo,pin['commit_sha'],path,blob=pin['blob_sha'])
            if kind=='stream':
                env=store._parse(observed)
                if (env['revision']!=pin['revision'] or env['body_digest']!=pin['snapshot_digest']
                        or observed['blob_sha']!=pin['blob_sha']): raise ValueError('Backup stream pin mismatch')
            elif observed['blob_sha']!=pin['blob_sha'] or digest(json.loads(observed['body']))!=pin['body_sha256']:
                raise ValueError('Backup fence pin mismatch')
        # Reobserve every mutable input after ALL completion and backup checks.
        phase='final_admission'
        if admission: admission()
        phase='final_reobservation'
        for route,raw in list(code_reader.mutable_metadata.items()):
            if code_reader._request('GET',route)!=raw: raise EvidenceChanged()
        for route,raw in raws.items():
            if code_reader._request('GET',route)!=raw: raise EvidenceChanged()
        t=policy['independent_verifier'];dest=policy['backup_target']
        def same(reader,repo,branch,record):
            return reader._request('GET',reader._route(repo,'/git/ref/heads/'+urllib.parse.quote(branch,safe='')))['object']['sha']==record['commit_sha']
        if (not same(backup_reader,t['repository'],t['receipt_branch'],backup_record)
                or backup_reader._request('GET',backup_reader._route(dest['repository'],
                    '/git/ref/heads/'+urllib.parse.quote(dest['branch'],safe='')))!=backup_ref
                or not same(store_reader,repo,d['store_branch'],original)
                or not same(store_reader,repo,d['fence_branch'],fence_record)):
            raise EvidenceChanged()
        time_left(store_reader.budget)
        result=response();result['diagnostic']={'phase':'complete'};return result
    except Exception as exc:
        return failure(phase,exc)
