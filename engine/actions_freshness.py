"""Bounded GET-only candidate health check. No store owner/write/recovery."""
from copy import deepcopy
import json
import re
import time
import urllib.parse
import actions_delivery as actions
import actions_schedule as slots
import github_delivery as github
from github_freshness import ReadBudget, utc_ms, iso
from production_confirmation import ProductionContentsClient
from production_contract import digest, validate_v2

MAX_GET = 80
MAX_SECONDS = 30
MAX_RUNS = 100


class Reader(github.GitHubContentsClient):
    open_request=staticmethod(ProductionContentsClient.open_request)
    response_byte_limit=2*1024*1024

    def __init__(self,token,repositories,budget,metadata=False):
        from job_quota import bind,Headers
        super().__init__(token,timeout=3)
        if not hasattr(budget,'quota_headers'): budget.quota_headers=Headers()
        bind(self,token,budget.quota_headers)
        self.metadata_routes=metadata
        self.repositories=set(repositories);self.budget=budget
        self._response_bytes=0
        self.mutable_metadata={}
        self.current_pins={}

    def _request(self,method,route,payload=None):
        if (method!='GET' or payload is not None or self.budget.requests>=MAX_GET
                or not any(route==self._route(r,'') or route.startswith(self._route(r,'/')) for r in self.repositories)):
            raise github.StoreUnavailable('GET-only monitor scope/budget refused')
        remaining=MAX_SECONDS-(time.monotonic()-self.budget.started)
        if remaining<=0: raise github.StoreUnavailable('Monitor total deadline')
        self.timeout=min(3,remaining)
        from public_access import tail_allowed
        parts=route.split('/',4);tail='/'+parts[4] if len(parts)==5 else ''
        if not tail_allowed(tail,self.metadata_routes): raise github.StoreUnavailable('Monitor path scope refused')
        from job_quota import cached
        self.quota_headers.before()
        hit=cached(self,route)
        if hit is not None: return hit
        self.budget.requests+=1
        result=super()._request(method,route)
        if '/actions/runs/' in route:
            self.mutable_metadata.setdefault(route,deepcopy(result))
        if time.monotonic()-self.budget.started>MAX_SECONDS: raise github.StoreUnavailable('Monitor total deadline')
        return result

    def read(self,repo,branch,path=github.STORE_PATH):
        # One initial ref, one final ref after ALL checks in check(). Immutable
        # contents remain bound to the initial commit; no mid-check head cache.
        ref=self._request('GET',self._route(repo,'/git/ref/heads/'+urllib.parse.quote(branch,safe='')))
        pin=self.current_pins.get((repo,branch,path))
        if pin:
            if ref['object']['sha']!=pin['commit_sha']: raise ValueError('Fence/stream head differs')
            return self.read_pinned(repo,ref['object']['sha'],path,blob=pin['blob_sha'])
        return self.read_at(repo,ref['object']['sha'],path)

    def jobs(self,repo,run_id):
        route=self._route(repo,'/actions/runs/'+run_id+'/attempts/1/jobs?per_page=100&page=1')
        # Reuse an earlier completed-job observation. check() re-GETs every
        # unique run/job route at the end, including this route.
        if route in self.mutable_metadata: return deepcopy(self.mutable_metadata[route])
        return self._request('GET',route)

    def update(self,*args,**kwargs): raise github.StoreUnavailable('No monitor mutation')


def selected(runs,kind,now,first):
    due=slots.due_slots(kind,now,first)
    if not due or not runs: raise ValueError(kind+'_missing_start')
    result=[]
    for slot in due:
        matches=[r for r in runs if r['expected_start_ms']==slot]
        if not matches: raise ValueError(kind+'_missing_start')
        result.append(max(matches,key=lambda r:r['created_ms']))
    newest=max(runs,key=lambda r:r['created_ms'])
    if newest not in result: result.append(newest)
    return result


def reviewed_run(reader,policy,repo,head,code,workflow):
    from reviewed_actions_entry import verify
    signature=policy.get('entry_workflows',{}).get(workflow)
    key=(repo,head,code,workflow,signature)
    if not hasattr(reader,'entry_verified'): reader.entry_verified=set()
    if key not in reader.entry_verified:
        verify(reader,repo,head,code,workflow,signature)
        reader.entry_verified.add(key)


def read_runs(client,policy,now):
    d=policy['deployment'];raws={};runs={}
    for kind in ('signal','watch'):
        due=slots.due_slots(kind,now,policy['first_start_ms'][kind])
        if not due: raise ValueError('Schedule not established')
        workflow=next(w for w,k in actions.WORKFLOWS.items() if k==kind)
        query=urllib.parse.urlencode({'per_page':MAX_RUNS,'page':1,'created':iso(min(due))+'..'+iso(now)})
        route=client._route(d['code_repository'],'/actions/workflows/'+workflow.rsplit('/',1)[-1]+'/runs?'+query)
        raw=client._request('GET',route);items=raw['workflow_runs'];raws[route]=deepcopy(raw)
        if raw['total_count']!=len(items) or len(items)>=MAX_RUNS: raise ValueError('Incomplete run query')
        normalized=[]
        for item in items:
            slot=slots.run_slot(kind,item)
            if (item['repository']['full_name']!=d['code_repository'] or item['path']!=workflow
                    or item['head_branch']!=d['code_ref'].removeprefix('refs/heads/')
                    or item['run_attempt']!=1 or not re.fullmatch('[1-9][0-9]*',str(item['id']))):
                raise ValueError('Run identity mismatch')
            reviewed_run(client,policy,d['code_repository'],item['head_sha'],d['code_sha'],workflow)
            normalized.append(dict(repository=d['code_repository'],workflow=workflow,run_id=str(item['id']),
                run_attempt='1',expected_start_ms=slot,created_ms=utc_ms(item['created_at']),
                started_ms=utc_ms(item.get('run_started_at') or item['created_at']),
                status=item['status'],conclusion=item['conclusion']))
        for run in selected(normalized,kind,now,policy['first_start_ms'][kind]):
            if run['status']!='completed' or run['conclusion']!='success': raise ValueError('Run failed/queued/incomplete')
            jobs=client.jobs(d['code_repository'],run['run_id'])
            if not 1<=len(jobs['jobs'])<=20 or jobs['total_count']!=len(jobs['jobs']): raise ValueError('Jobs incomplete')
            for job in jobs['jobs']:
                actual=next(item['head_sha'] for item in items if str(item['id'])==run['run_id'])
                if (str(job['run_id'])!=run['run_id'] or job['run_attempt']!=1 or job['head_sha']!=actual
                        or job['status']!='completed' or job['conclusion']!='success'):
                    raise ValueError('Job skipped/failed/foreign')
            run['completed_ms']=max(utc_ms(j['completed_at']) for j in jobs['jobs'])
        runs[kind]=normalized
    return runs,raws


def verify_completions(store,runs,policy,now):
    snapshot=store.snapshot;validate_v2(snapshot);c=snapshot['control'];d=policy['deployment']
    if (c['mode']!='active' or c['owner'] is not None or c['store_id']!=d['store_id']
            or any(c[k]!=d[k] for k in ('code_sha','config_sha256','bot_identity'))
            or c['health'].get('restore_requires_reconciliation') or store.blocked()
            or c['health'].get('consecutive_mutex_conflicts',0)>=2
            or c['health'].get('current_run',{}).get('status')!='completed'):
        raise ValueError('Stream blocked/owned/unfinished/foreign')
    if any(m['status']!='confirmed' for s in [snapshot['engine'],*snapshot['commands'].values()]
           for m in s.get('_delivery',{}).get('messages',[])): raise ValueError('Delivery incomplete/uncertain')
    for kind in ('signal','watch'):
        for meta in selected(runs[kind],kind,now,policy['first_start_ms'][kind]):
            slot=meta['expected_start_ms']
            if not slot<=meta['created_ms']<=meta['started_ms']<=meta['completed_ms']<=now:
                raise ValueError('Run time mismatch')
            if (meta['completed_ms']>slots.deadline(kind,slot)
                    or meta['completed_ms']-meta['started_ms']>15*slots.MINUTE): raise ValueError('Run overdue')
            bound=c['health'].get('completed_runs',{}).get(kind,{}).get(str(slot))
            if not bound: raise ValueError('Confirmed completion missing')
            run=bound['run'];loc=bound['completion']
            if (any(run[k]!=meta[k] for k in ('repository','workflow','run_id','run_attempt','expected_start_ms'))
                    or run['kind']!=kind or run['status']!='completed' or not run['nonce']
                    or any(run[k]!=c[k] for k in ('store_id','stream_id','code_sha','config_sha256'))
                    or any(loc.get(k)!=v for k,v in {'adapter':'github','repo':d['private_store_repository'],
                        'branch':d['store_branch'],'path':github.STORE_PATH,'store_id':d['store_id']}.items())
                    or not 0<=loc['revision']<store.revision or loc['revision']!=run['revision']
                    or not meta['started_ms']<=run['started_ms']<=run['finished_ms']<=meta['completed_ms']):
                raise ValueError('Completion identity/time/locator mismatch')
            completed=store.read_revision(loc)
            if (completed['control']['health']['completion_candidate']!=run
                    or any(completed['control'][k]!=c[k] for k in ('store_id','stream_id','code_sha','config_sha256'))):
                raise ValueError('Completion revision differs')
            if kind=='signal':
                if run['last_signal_ts']!=slot//(4*slots.HOUR)*(4*slots.HOUR)-4*slots.HOUR:
                    raise ValueError('Signal candle close mismatch')
            elif (run['watch_candle_open_ms']!=run['watch_observed_ms']//(4*slots.HOUR)*(4*slots.HOUR)
                    or not run['started_ms']<=run['watch_observed_ms']<=run['finished_ms']):
                raise ValueError('Watch observation mismatch')


def verify_fence_run(reader,deployment,fence,now,policy=None):
    run=fence['run'];repo=deployment['code_repository']
    meta=reader._request('GET',reader._route(repo,'/actions/runs/'+run['id']))
    if (str(meta['id'])!=run['id'] or meta['run_attempt']!=1 or meta['run_number']!=run['number']
            or meta['repository']['full_name']!=repo or meta['path']!=run['workflow']
            or meta['head_branch']!=deployment['code_ref'].removeprefix('refs/heads/')
            or meta['status']!='completed' or meta['conclusion']!='success'):
        raise ValueError('Latest fence run metadata incomplete/foreign')
    reviewed_run(reader,policy or {},repo,meta['head_sha'],deployment['code_sha'],run['workflow'])
    kind=run['kind']
    if kind=='lage':
        if meta['event']!='workflow_dispatch': raise ValueError('Latest Lage not manual')
        slot=utc_ms(meta['created_at']);end=slot+15*slots.MINUTE
    else:
        slot=slots.run_slot(kind,meta);end=slots.deadline(kind,slot)
    if int(run['expected_start_ms'])!=slot: raise ValueError('Latest fence occurrence differs')
    jobs=reader._request('GET',reader._route(repo,'/actions/runs/'+run['id']+'/attempts/1/jobs?per_page=100&page=1'))
    if not 1<=len(jobs['jobs'])<=20 or jobs['total_count']!=len(jobs['jobs']): raise ValueError('Latest fence jobs incomplete')
    for j in jobs['jobs']:
        if (str(j['run_id'])!=run['id'] or j['run_attempt']!=1 or j['head_sha']!=meta['head_sha']
                or j['status']!='completed' or j['conclusion']!='success'
                or not utc_ms(meta['created_at'])<=utc_ms(j['completed_at'])<=min(now,end)):
            raise ValueError('Latest fence job failed/late/future')


def read_backup(reader,code_reader,policy,now):
    # Trust boundary: separately protected verifier receipt branch. The verifier
    # must have fully restored the uploaded bytes, not the producer's local copy.
    t=policy['independent_verifier'];d=policy['deployment']
    record=reader.read(t['repository'],t['receipt_branch'],t['receipt_path'])
    if len(record['body'])>128*1024: raise ValueError('Receipt size')
    receipt=json.loads(record['body']);m=receipt['manifest'];v=receipt['verification']
    from p4_backup_pair import validate_pair
    validate_pair(m,m['pins'])
    if (receipt['schema']!='p4-independent-backup-receipt-v1' or receipt['verifier']!=t['binding']
            or receipt['manifest_sha256']!=digest(m) or m['deployment']!=d
            or v['manifest_sha256']!=digest(m) or v['pins']!=m['pins']
            or v['history_verified'] is not True or v['restore_blocked_verified'] is not True
            or v['package_manifest_sha256']!=digest(m['files']) or v['enabled'] is not False
            or receipt['upload_readback_verified'] is not True): raise ValueError('Independent full pair verification missing')
    for key in ('stream','fence'):
        h=m[key];hashes=h['package_manifest_sha256']
        if (not 1<=len(hashes)<=512 or h['package_count']!=len(hashes)
                or any(not re.fullmatch('[0-9a-f]{64}',x) for x in hashes)
                or len(set(hashes))!=len(hashes) or h['chain_sha256']!=digest(hashes)
                or h['history_count']!=h['revision']+1): raise ValueError('Backup history incomplete')
    slot=receipt['expected_start_ms']
    if (not slots.valid_slot('backup',slot) or slot<policy['first_start_ms']['backup']
            or not slot<=v['verified_ms']<=now or now>slots.deadline('backup',slot)):
        raise ValueError('Backup overdue/future')
    dest=receipt['destination'];target=policy['backup_target']
    if any(dest[k]!=target[k] for k in ('repository','branch')): raise ValueError('Foreign backup target')
    if target.get('manifest_prefix')=='manifests/':
        if dest['manifest_path']!='manifests/'+digest(m)+'.json': raise ValueError('Foreign immutable manifest path')
        if m['hosted']['expected_start_ms']!=slot: raise ValueError('Old hosted publication occurrence')
    elif dest['manifest_path']!=target['manifest_path']: raise ValueError('Foreign backup manifest path')
    # Actual immutable uploaded manifest, and ancestry on the pinned protected branch.
    uploaded=reader.read_pinned(dest['repository'],dest['commit_sha'],dest['manifest_path'],blob=dest['blob_sha'])
    if (json.loads(uploaded['body'])!=m or uploaded['blob_sha']!=dest['blob_sha']):
        raise ValueError('Uploaded manifest mismatch')
    current=reader._request('GET',reader._route(dest['repository'],'/git/ref/heads/'+urllib.parse.quote(dest['branch'],safe='')))
    if not reader.is_ancestor(dest['repository'],dest['commit_sha'],current['object']['sha']): raise ValueError('Backup branch rewritten')
    # Verify the independent verifier really ran the reviewed code/workflow.
    binding=t['binding'];run=code_reader._request('GET',code_reader._route(binding['repository'],
        '/actions/runs/'+str(receipt['verifier_run_id'])))
    if (run['repository']['full_name']!=binding['repository'] or run['path']!=binding['workflow']
            or run['head_branch']!=binding['branch']
            or run['run_attempt']!=1 or run['status']!='completed' or run['conclusion']!='success'
            or not utc_ms(run['created_at'])<=v['verified_ms']<=utc_ms(run['updated_at'])<=now):
        raise ValueError('Independent verifier run missing/foreign/failed')
    reviewed_run(code_reader,policy,binding['repository'],run['head_sha'],binding['code_sha'],binding['workflow'])
    jobs=code_reader._request('GET',code_reader._route(binding['repository'],
        '/actions/runs/'+str(receipt['verifier_run_id'])+'/attempts/1/jobs?per_page=100&page=1'))
    if (not 1<=len(jobs['jobs'])<=20 or jobs['total_count']!=len(jobs['jobs'])
            or any(j['conclusion']!='success' or j['status']!='completed' or j['head_sha']!=run['head_sha']
                   or str(j['run_id'])!=str(receipt['verifier_run_id']) or j['run_attempt']!=1 for j in jobs['jobs'])):
        raise ValueError('Verifier jobs incomplete')
    return receipt,record,current


def check(store_reader,code_reader,backup_reader,policy,now,admission=None):
    from freshness import response
    try:
        if policy.get('enabled') is not True or policy.get('schema')!='p4-actions-monitor-v1': raise ValueError('Monitor disabled')
        d=policy['deployment']
        if d['schedule_contract']!=slots.CONTRACT: raise ValueError('Schedule contract mismatch')
        repo=d['private_store_repository']
        fence_record=store_reader.read(repo,d['fence_branch'],actions.FENCE_PATH)
        fence=actions.parse_fence(fence_record,d)
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
        verify_fence_run(code_reader,d,fence,now,policy)
        runs,raws=read_runs(code_reader,policy,now)
        verify_completions(store,runs,policy,now)
        receipt,backup_record,backup_ref=read_backup(backup_reader,code_reader,policy,now)
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
        if admission: admission()
        for route,raw in list(code_reader.mutable_metadata.items()):
            if code_reader._request('GET',route)!=raw: raise ValueError('Run/jobs moved during check')
        for route,raw in raws.items():
            if code_reader._request('GET',route)!=raw: raise ValueError('Runs moved during check')
        t=policy['independent_verifier'];dest=policy['backup_target']
        def same(reader,repo,branch,record):
            return reader._request('GET',reader._route(repo,'/git/ref/heads/'+urllib.parse.quote(branch,safe='')))['object']['sha']==record['commit_sha']
        if (not same(backup_reader,t['repository'],t['receipt_branch'],backup_record)
                or backup_reader._request('GET',backup_reader._route(dest['repository'],
                    '/git/ref/heads/'+urllib.parse.quote(dest['branch'],safe='')))!=backup_ref
                or not same(store_reader,repo,d['store_branch'],original)
                or not same(store_reader,repo,d['fence_branch'],fence_record)):
            raise ValueError('Store/fence/backup moved during check')
        return response()
    except ValueError as exc:
        # Only controlled local categories, never provider response/credential text.
        return response('candidate_evidence_invalid')
    except Exception:
        return response('candidate_evidence_unavailable')
