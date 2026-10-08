"""Synthetic P3 run-binding, deadline, interruption and read-only counterexamples."""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import urllib.error
from unittest.mock import patch

import durable_delivery as durable
import freshness
import github_delivery as github
import github_freshness
import run_health
from production_contract import CANDLE_MS, canonical, digest
from test_github_delivery import FakeAPI, REPO, BRANCH, STORE_ID, fails, stage_message
from test_production_runtime import seeded
import p3_store_probe as probe
import p3_backup_rehearsal as backup_tool
import produktion_health
import produktion_freshness
import produktion_github_backup
import p3_run_binding


def run_env(kind, slot, run='101', attempt='1'):
    return {'BTC_DELIVERY_RUN_REPOSITORY':'synthetic/code',
        'BTC_DELIVERY_WORKFLOW':'.github/workflows/'+kind+'.yml',
        'BTC_DELIVERY_RUN_ID':run, 'BTC_DELIVERY_RUN_ATTEMPT':attempt,
        'BTC_DELIVERY_EXPECTED_START_MS':str(slot)}


def finish(store, kind, slot):
    if kind == 'watch':
        store.snapshot['control']['health']['current_run'].update(
            watch_candle_open_ms=slot//CANDLE_MS*CANDLE_MS, watch_observed_ms=slot+1500)
    run_health.record_event(store,kind,'finish',slot+2000,None)


@contextmanager
def healthy_fixture(adapter='github'):
    with tempfile.TemporaryDirectory() as td:
        path, data, _ = seeded(td)
        with durable.read_only_volume(path,STORE_ID) as source:
            snapshot = deepcopy(source.snapshot)
        base = snapshot['control']['migration']['W']+2*CANDLE_MS
        snapshot['engine']['last_signal_ts'] = base-CANDLE_MS
        snapshot['control']['owner'] = None
        c = snapshot['control']
        policy = {'identity':{k:c[k] for k in ('store_id','stream_id','code_sha','config_sha256')},
            'store':{'adapter':adapter}, 'schedules':{}}
        for kind, period, phase in (('signal',CANDLE_MS,2*freshness.MINUTE),
                                    ('watch',15*freshness.MINUTE,8*freshness.MINUTE)):
            policy['schedules'][kind] = {'period_ms':period,'phase_ms':phase,
                'first_start_ms':base+phase, 'repository':'synthetic/code',
                'workflow':'.github/workflows/'+kind+'.yml','branch':'synthetic-runtime'}
        policy['schedules']['signal']['close_offset_ms'] = 2*freshness.MINUTE
        day = 24*60*freshness.MINUTE
        policy['schedules']['backup'] = {'period_ms':day,'phase_ms':base%day,'first_start_ms':base}
        if adapter == 'github':
            policy['store'].update(repo=REPO,branch=BRANCH,path=github.STORE_PATH)
            seed = github.initial_envelope(snapshot,REPO,BRANCH,STORE_ID)
            api = FakeAPI(seed); api._set(probe.synthetic_active(seed))
        else:
            with durable.VolumeStore(path,STORE_ID) as s:
                s.snapshot = snapshot; s.snapshot['control']['mode'] = 'active'; s.commit()
            api = None
        runs = {}
        for kind, slot, run_id in (('signal',base+2*freshness.MINUTE,'101'),
                                  ('watch',base+8*freshness.MINUTE,'201'),
                                  ('watch',base+23*freshness.MINUTE,'202'),
                                  ('watch',base+38*freshness.MINUTE,'203'),
                                  ('watch',base+53*freshness.MINUTE,'204')):
            store = (github.GitHubStore(api,REPO,BRANCH,STORE_ID,run_id,'1')
                     if adapter == 'github' else durable.VolumeStore(path,STORE_ID))
            with store, patch.dict(os.environ,run_env(kind,slot,run_id)):
                run_health.record_event(store,kind,'start',slot+1000,None)
                finish(store,kind,slot)
            runs.setdefault(kind,[]).append({'repository':'synthetic/code','workflow':'.github/workflows/'+kind+'.yml',
                'branch':'synthetic-runtime','head_sha':c['code_sha'], 'run_id':run_id,
                'run_attempt':'1','expected_start_ms':slot,'created_ms':slot+500,
                'started_ms':slot+750,'completed_ms':slot+3000,'status':'completed','conclusion':'success'})
        backup = {'status':'confirmed','store_id':STORE_ID,'code_sha':c['code_sha'],
            'config_sha256':c['config_sha256'],'expected_start_ms':base,'verified_ms':base+100,
            'manifest_sha256':'a'*64,'store_commit_sha':'b'*40,'source_revision':0,
            'history_verified':True,'restore_blocked_verified':True}
        if api:
            backup['store_commit_sha']=min(api.records)
            backup['snapshot_digest']=json.loads(api.records[backup['store_commit_sha']]['body'])['body_digest']
        yield {'api':api,'path':path,'policy':policy,'runs':runs,'backup':backup,
               'now':base+60*freshness.MINUTE,'base':base}


def check(f):
    return freshness.check_github(f['api'],lambda:deepcopy(f['runs']),
        lambda:deepcopy(f['backup']),f['policy'],f['now'])


def test_probe_controller_is_fixed_fake_only_and_budgeted():
    result = probe.probe()
    assert result['passed'] and result['source_unchanged']
    assert result['fake_put_count'] == 7 and result['real_requests'] == 0
    assert result['max_observed_bytes'] < github.MAX_BYTES
    fails(ValueError,lambda:probe.synthetic_active(canonical({'repo':'foreign/repo'}).encode()))


def test_read_only_github_monitor_and_pinned_completions_are_healthy():
    with healthy_fixture() as f:
        before = deepcopy(f['api'].record); puts = f['api'].put_count
        with patch.object(github.GitHubStore,'__enter__',side_effect=AssertionError('owner write')):
            assert check(f) == freshness.response()
        assert f['api'].record == before and f['api'].put_count == puts
        s = github.read_only(f['api'],REPO,BRANCH,STORE_ID)
        for kind in ('signal','watch'):
            bound = s.snapshot['control']['health']['successful_runs'][kind]
            assert bound['completion']['revision'] < s.revision
            assert 'commit_sha' not in bound['run']
            assert s.read_revision(bound['completion'])['control']['health']['completion_candidate'] == bound['run']


def test_missing_signal_and_watch_starts_return_503_even_after_204():
    for kind in ('signal','watch'):
        with healthy_fixture() as f:
            f['runs'][kind] = []
            assert check(f) == freshness.response(kind+'_missing_start')


def test_foreign_new_runs_attempts_and_failed_runs_cannot_use_old_health():
    for field, value, error in (
        ('run_id','999','completion_run_mismatch'),('run_attempt','2','completion_run_mismatch'),
        ('repository','foreign/code','run_identity_mismatch'),('workflow','other.yml','run_identity_mismatch'),
        ('head_sha','f'*40,'run_identity_mismatch'),('branch','foreign','run_identity_mismatch'),
        ('conclusion','failure','run_failed'),('conclusion','cancelled','run_failed')):
        with healthy_fixture() as f:
            f['runs']['watch'][-1][field] = value
            assert check(f) == freshness.response(error),field


def test_running_and_overlong_runs_are_unhealthy():
    for status, started, error in (('queued',0,'run_overdue'),('in_progress',0,'run_overdue'),
                                 ('in_progress',59,'run_unfinished')):
        with healthy_fixture() as f:
            r=f['runs']['watch'][-1];r.update(status=status,conclusion=None,
                started_ms=f['base']+started*freshness.MINUTE)
            assert check(f) == freshness.response(error)
    with healthy_fixture() as f:
        r=f['runs']['signal'][0];r['completed_ms']=r['started_ms']+freshness.MAX_RUN_MS+1
        assert check(f) == freshness.response('run_overdue')


def test_signal_45_minutes_is_anchored_to_close_not_open_or_dispatch():
    with healthy_fixture() as f:
        f['runs']['signal']=[]
        f['now']=f['base']+45*freshness.MINUTE
        assert check(f) == freshness.response('signal_missing_start')
    with healthy_fixture() as f:
        f['now']=f['base']+CANDLE_MS+45*freshness.MINUTE
        assert check(f) == freshness.response('signal_missing_start')


def test_watch_due_occurrences_and_stale_success_cannot_hide_missing_start():
    with healthy_fixture() as f:
        f['now']=f['base']+114*freshness.MINUTE
        assert check(f) == freshness.response('watch_missing_start')
    with healthy_fixture() as f:
        f['runs']['watch'][-1]['expected_start_ms']+=1
        assert check(f) == freshness.response('run_schedule_mismatch')
    with healthy_fixture() as f:
        f['runs']['watch'].pop(0)  # due 08 missing, later 23/38/53 succeeded
        assert check(f) == freshness.response('watch_missing_start')


def test_backup_26h_counts_expected_slot_not_late_verification():
    with healthy_fixture() as f:
        # Exactly 26h is still at the boundary; one millisecond more is stale.
        day=24*60*freshness.MINUTE
        slot=f['base']-25*60*freshness.MINUTE
        f['policy']['schedules']['backup'].update(first_start_ms=slot,phase_ms=slot%day)
        f['backup']['expected_start_ms']=slot
        f['backup']['verified_ms']=f['now']
        assert check(f) == freshness.response()
        f['now']+=1
        assert check(f) == freshness.response('backup_overdue')
    for key in ('history_verified','restore_blocked_verified'):
        with healthy_fixture() as f:
            f['backup'][key]=False
            assert check(f) == freshness.response('backup_overdue')


def mutate(api, fn):
    env=api.envelope();fn(env['snapshot']);env['body_digest']=digest(env['snapshot'])
    api._set(canonical(env).encode())


def test_blocked_uncertain_missing_finish_and_missing_binding_are_unhealthy():
    for change, error in (
        (lambda s:s['control'].update(mode='blocked'),'stream_blocked'),
        (lambda s:s['control'].update(owner={'repository':REPO,'run_id':'dead','run_attempt':'1','nonce':'n'}),'store_owned'),
        (lambda s:s['control']['health']['current_run'].update(status='failed'),'run_unfinished'),
        (lambda s:s['control']['health'].update(consecutive_mutex_conflicts=2),'mutex_conflicts'),
        (lambda s:s['control']['health']['successful_runs'].pop('signal'),'completion_missing'),
        (lambda s:s['control']['health']['successful_runs']['watch']['completion'].update(revision=999),'completion_revision_mismatch')):
        with healthy_fixture() as f:
            mutate(f['api'],change)
            assert check(f) == freshness.response(error)
    with healthy_fixture() as f:
        with github.GitHubStore(f['api'],REPO,BRANCH,STORE_ID,'303','1') as s:
            m=stage_message(s);m.update(status='sending',attempts=1,target='a'*64);s.commit()
        assert check(f) == freshness.response('uncertain_delivery')


def test_corrupt_pinned_completion_and_rewritten_history_do_not_certify_health():
    with healthy_fixture() as f:
        s=github.read_only(f['api'],REPO,BRANCH,STORE_ID)
        pin=s.snapshot['control']['health']['successful_runs']['signal']['completion']['commit_sha']
        f['api'].records[pin]['body']+=b' '
        assert check(f)['http_status']==503
    with healthy_fixture() as f:
        f['api'].rewrite_history()
        assert check(f)['http_status']==503


def test_api_errors_head_movement_and_run_movement_return_secret_free_503():
    with healthy_fixture() as f:
        f['api'].missing=True
        assert check(f) == freshness.response('api_or_store_unavailable')
    with healthy_fixture() as f:
        calls=[]
        def moving():
            calls.append(1)
            if len(calls)==2:f['runs']['watch'][-1]['run_attempt']='2'
            return deepcopy(f['runs'])
        r=freshness.check_github(f['api'],moving,lambda:f['backup'],f['policy'],f['now'])
        assert r == freshness.response('runs_moved_during_check')
    with healthy_fixture() as f:
        def reader():
            f['api'].rewrite_history();return deepcopy(f['runs'])
        assert freshness.check_github(f['api'],reader,lambda:f['backup'],f['policy'],f['now'])['http_status']==503
    encoded=canonical(freshness.response('api_or_store_unavailable'))
    assert 'token' not in encoded and 'body_base64' not in encoded


def test_sqlite_same_binding_and_read_only_files_remain_identical():
    with healthy_fixture('sqlite') as f:
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f['path'].iterdir()}
        r=produktion_health.evaluate_bound(f['path'],STORE_ID,f['policy'],f['runs'],f['backup'],f['now'])
        assert r == freshness.response()
        after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in f['path'].iterdir()}
        assert before==after
        f['runs']['watch'][-1]['run_attempt']='2'
        assert produktion_health.evaluate_bound(f['path'],STORE_ID,f['policy'],f['runs'],f['backup'],f['now'])['http_status']==503
        assert produktion_health.evaluate(f['path'],STORE_ID,f['now'])['healthy'] is False


def test_unconfirmed_completion_write_and_attestation_halt_run():
    for failure_step in ('candidate','attestation'):
        for failure in ('timeout_before','403','429'):
            with healthy_fixture() as f:
                slot=f['base']+68*freshness.MINUTE
                s=github.GitHubStore(f['api'],REPO,BRANCH,STORE_ID,'303','1').__enter__()
                with patch.dict(os.environ,run_env('watch',slot,'303')):
                    run_health.record_event(s,'watch','start',slot+1000,None)
                    original=f['api'].update;calls=[]
                    def update(*args):
                        calls.append(1)
                        if len(calls)==(1 if failure_step=='candidate' else 2):f['api'].fail_next=failure
                        return original(*args)
                    with patch.object(f['api'],'update',side_effect=update):
                        fails(github.StoreError,lambda:finish(s,'watch',slot))
                assert s._halted
                assert f['api'].envelope()['snapshot']['control']['owner'] is not None
                assert check(f)['http_status']==503


def test_lost_completion_reply_after_write_requires_exact_readback():
    with healthy_fixture() as f:
        slot=f['base']+68*freshness.MINUTE
        with github.GitHubStore(f['api'],REPO,BRANCH,STORE_ID,'303','2') as s, patch.dict(os.environ,run_env('watch',slot,'303','2')):
            run_health.record_event(s,'watch','start',slot+1000,None)
            original=f['api'].update
            def lost(*args):f['api'].fail_next='timeout_after';return original(*args)
            with patch.object(f['api'],'update',side_effect=lost):
                finish(s,'watch',slot)
            assert s.snapshot['control']['health']['successful_runs']['watch']['run']['run_attempt']=='2'


def test_health_identity_missing_foreign_owner_or_finish_without_start_fails():
    with healthy_fixture() as f:
        with github.GitHubStore(f['api'],REPO,BRANCH,STORE_ID,'303','1') as s:
            with patch.dict(os.environ,{},clear=True):
                fails(ValueError,lambda:run_health.record_event(s,'watch','start',f['now'],None))
            with patch.dict(os.environ,run_env('watch',f['now'],'999')):
                fails(ValueError,lambda:run_health.record_event(s,'watch','start',f['now'],None))
            with patch.dict(os.environ,run_env('watch',f['now'],'303')):
                fails(ValueError,lambda:run_health.record_event(s,'watch','finish',f['now'],None))


def test_two_stale_claims_use_cas_one_owner_and_no_age_stealing():
    with healthy_fixture() as f:
        old=deepcopy(f['api'].record)
        first=github.GitHubStore(f['api'],REPO,BRANCH,STORE_ID,'303','1').__enter__()
        f['api'].stale_record=old
        other=github.GitHubStore(f['api'],REPO,BRANCH,STORE_ID,'404','2')
        fails(github.StoreConflict,other.__enter__)
        assert f['api'].envelope()['snapshot']['control']['owner']==first.owner
        fails(github.StoreConflict,lambda:github.GitHubStore(f['api'],REPO,BRANCH,STORE_ID,'505','1').__enter__())
        first.__exit__(None,None,None)


def test_fake_backup_full_history_hashes_latest_pin_and_blocked_restore():
    with healthy_fixture() as f:
        pin=f['api'].record['commit_sha'];rev=f['api'].envelope()['revision']
        p=backup_tool.package_fake(f['api'],REPO,BRANCH,STORE_ID,pin,'d'*64)
        assert p['manifest']['commit_count']==len(f['api'].records)
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'restored'
            r=backup_tool.restore_fake(p,target,pin,rev)
            assert r['mode']=='blocked'
            with durable.read_only_volume(target,STORE_ID) as s:
                assert s.snapshot['control']['health']['successful_runs']=={}
                assert s.snapshot['control']['health']['restore_requires_reconciliation']
        for bad in ('hash','latest','history'):
            changed=deepcopy(p)
            if bad=='hash':changed['history'][0]['body_base64']='eA=='
            if bad=='latest':changed['manifest']['pin']='f'*40
            if bad=='history':
                changed['history'].pop();changed['manifest']['history_sha256']=digest(changed['history'])
                changed['manifest']['commit_count']=len(changed['history'])
            fails(ValueError,lambda:backup_tool.verify_fake(changed,pin,rev))
        fails(ValueError,lambda:backup_tool.package_fake(object(),REPO,BRANCH,STORE_ID,pin,'d'*64))


def test_offline_freshness_cli_fixture_has_no_listener_or_transport():
    with healthy_fixture() as f:
        s=github.read_only(f['api'],REPO,BRANCH,STORE_ID)
        completions={str(b['completion']['revision']):s.read_revision(b['completion'])
                     for index in s.snapshot['control']['health']['completed_runs'].values()
                     for b in index.values()}
        fixture={'synthetic':True,'snapshot':s.snapshot,'revision':s.revision,
            'completion_snapshots':completions,'runs':f['runs'],'policy':f['policy'],
            'backup':f['backup'],'now_ms':f['now']}
        path=f['path'].parent/'fixture.json';path.write_text(canonical(fixture),encoding='utf-8')
        with patch('urllib.request.urlopen',side_effect=AssertionError('network')):
            assert produktion_freshness.simulate(path) == freshness.response()
        fixture['runs']['watch']=[];path.write_text(canonical(fixture),encoding='utf-8')
        assert produktion_freshness.simulate(path)['http_status']==503


def test_get_only_reader_limits_errors_response_size_and_elapsed_budget():
    client=github_freshness.ReadOnlyClient('synthetic-secret')
    with patch('urllib.request.urlopen',side_effect=AssertionError('mutation/network')):
        fails(github.StoreUnavailable,lambda:client._request('PUT','/synthetic'))
        client.requests=github_freshness.MAX_READS
        fails(github.StoreUnavailable,lambda:client._request('GET','/synthetic'))
        client.requests=0;client.started-=github_freshness.MAX_TOTAL_SECONDS+1
        fails(github.StoreUnavailable,lambda:client._request('GET','/synthetic'))
    for code in (403,429):
        client=github_freshness.ReadOnlyClient('synthetic-secret')
        error=urllib.error.HTTPError('https://api.github.com/synthetic',code,'secret-body',{},None)
        with patch('urllib.request.urlopen',side_effect=error):
            try:client._request('GET','/synthetic')
            except github.StoreUnavailable as exc:
                assert 'secret' not in str(exc) and str(code) in str(exc)
            else:raise AssertionError('HTTP failure accepted')
    client=github_freshness.ReadOnlyClient('synthetic-secret')
    with patch('urllib.request.urlopen',return_value=io.BytesIO(b'x'*(github.MAX_RESPONSE_BYTES+1))):
        fails(github.StoreUnavailable,lambda:client._request('GET','/synthetic'))


def test_github_run_reader_uses_actual_attempt_jobs_and_complete_get_pages():
    with healthy_fixture() as f:
        routes=[]
        def request(method,route,payload=None):
            assert method=='GET' and payload is None
            routes.append(route)
            if '/workflows/' in route:
                kind='signal' if 'signal.yml' in route else 'watch'
                items=[]
                for r in f['runs'][kind]:
                    items.append({'id':int(r['run_id']),'run_attempt':int(r['run_attempt']),
                        'repository':{'full_name':r['repository']},'path':r['workflow'],
                        'head_branch':r['branch'],'head_sha':r['head_sha'],
                        'display_title':'p3:'+kind+':'+str(r['expected_start_ms']//1000),
                        'event':'workflow_dispatch','created_at':github_freshness.iso(r['created_ms']),
                        'run_started_at':github_freshness.iso(r['started_ms']),
                        'status':r['status'],'conclusion':r['conclusion']})
                return {'total_count':len(items),'workflow_runs':items}
            run_id=route.split('/actions/runs/')[1].split('/')[0]
            r=next(r for rs in f['runs'].values() for r in rs if r['run_id']==run_id)
            assert '/attempts/1/jobs?' in route
            job={'run_id':int(run_id),'run_attempt':1,'head_sha':r['head_sha'],
                'status':'completed','conclusion':'success','completed_at':github_freshness.iso(r['completed_ms'])}
            return {'total_count':1,'jobs':[job]}
        client=github_freshness.ReadOnlyClient('synthetic-secret')
        with patch.object(client,'_request',side_effect=request):
            actual=github_freshness.read_runs(client,f['policy'],f['now'])
        s=github.read_only(f['api'],REPO,BRANCH,STORE_ID)
        assert freshness.evaluate(s.snapshot,s.revision,s.read_revision,actual,f['policy'],f['now'],f['backup'])==freshness.response()
        assert len(routes)==5 # two lists, signal latest, watch due and latest jobs
        def incomplete(method,route,payload=None):
            result=request(method,route,payload);result['total_count']+=1;return result
        with patch.object(client,'_request',side_effect=incomplete):
            fails(github.StoreUnavailable,lambda:github_freshness.read_runs(client,f['policy'],f['now']))
        def wrong_attempt(method,route,payload=None):
            result=request(method,route,payload)
            if 'jobs' in result:result['jobs'][0]['run_attempt']=2
            return result
        with patch.object(client,'_request',side_effect=wrong_attempt):
            fails(ValueError,lambda:github_freshness.read_runs(client,f['policy'],f['now']))


def test_watch_without_current_data_cannot_record_success():
    import main
    from test_production_runtime import active
    with tempfile.TemporaryDirectory() as td:
        path,data,_=seeded(td)
        with active(td,path,data):
            fails(ValueError,lambda:main.watch_flush(data_dir=data,kerzen_roh=[]))
        with durable.read_only_volume(path,STORE_ID) as s:
            assert 'watch' not in s.snapshot['control']['health'].get('successful_runs',{})


def test_successful_run_health_needs_both_confirmed_sqlite_writes():
    with healthy_fixture('sqlite') as f:
        slot=f['base']+68*freshness.MINUTE
        with durable.VolumeStore(f['path'],STORE_ID) as s, patch.dict(os.environ,run_env('watch',slot,'303')):
            run_health.record_event(s,'watch','start',slot+1000,None)
            original=s.commit;calls=[]
            def fail_attestation():
                calls.append(1)
                if len(calls)==2:raise OSError('synthetic disk failure')
                original()
            with patch.object(s,'commit',side_effect=fail_attestation):
                fails(OSError,lambda:finish(s,'watch',slot))
        with durable.read_only_volume(f['path'],STORE_ID) as s:
            assert s.snapshot['control']['health']['successful_runs']['watch']['run']['run_id']=='204'
            assert s.snapshot['control']['health']['completion_candidate']['run_id']=='303'


def test_real_local_git_bundle_synthetic_store_history_and_blocked_restore():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);path,_,paths=seeded(root)
        with durable.read_only_volume(path,STORE_ID) as s:
            seed=github.initial_envelope(s.snapshot,REPO,BRANCH,STORE_ID)
        repo=root/'synthetic-git';repo.mkdir()
        subprocess.run(['git','init','-b',BRANCH,str(repo)],check=True,capture_output=True)
        folder=repo/'delivery';folder.mkdir()
        env={**os.environ,'GIT_AUTHOR_NAME':'Synthetic P3','GIT_COMMITTER_NAME':'Synthetic P3',
            'GIT_AUTHOR_EMAIL':'synthetic@example.invalid','GIT_COMMITTER_EMAIL':'synthetic@example.invalid'}
        for body in (seed,probe.synthetic_active(seed)):
            (folder/'stream.json').write_bytes(body)
            subprocess.run(['git','-c','safe.directory='+repo.as_posix(),'-C',str(repo),'add','delivery/stream.json'],check=True,capture_output=True)
            subprocess.run(['git','-c','safe.directory='+repo.as_posix(),'-C',str(repo),'commit','-m','Synthetic fixture only'],env=env,check=True,capture_output=True)
        pin=produktion_github_backup.git(repo,'rev-parse','HEAD').decode().strip()
        identity={'repo':REPO,'branch':BRANCH,'store_id':STORE_ID,
                  'stream_id':json.loads(seed)['snapshot']['control']['stream_id']}
        out=root/'backup';target=root/'restore'
        m=produktion_github_backup.package_local(repo,BRANCH,pin,identity,paths[-1],out)
        assert m['history_count']==2 and m['revision']==1 and m['second_private_repository'] is None
        r=produktion_github_backup.restore_local(out,target,pin,1)
        assert r['git_fsck'] and r['mode']=='blocked' and not r['real_backup_write']
        with durable.read_only_volume(target/'blocked-store',STORE_ID) as s:
            assert s.snapshot['control']['mode']=='blocked'
            assert s.snapshot['control']['health']['restore_requires_reconciliation']
        fails(ValueError,lambda:produktion_github_backup.restore_local(out,root/'wrong-pin','f'*40,1))
        fails(ValueError,lambda:produktion_github_backup.restore_local(out,root/'missing-latest',pin,2))
        (out/'stream.json').write_bytes((out/'stream.json').read_bytes()+b' ')
        fails(ValueError,lambda:produktion_github_backup.restore_local(out,root/'bad-hash',pin,1))


def test_checked_runner_rejects_foreign_actual_github_identity_before_fetch():
    import produktion_runner
    with tempfile.TemporaryDirectory() as td:
        _,data,_=seeded(td)
        env={**run_env('signal',1791100800000,'303'),
            'BTC_DELIVERY_ADAPTER':'github','BTC_DELIVERY_STORE_ID':STORE_ID,
            'BTC_DELIVERY_RUNNER_ROOT':str(data.parent),'BTC_DELIVERY_CODE_SHA':'a'*40,
            'BTC_DELIVERY_BOT_IDENTITY':'synthetic-bot','TELEGRAM_BOT_TOKEN':'fake',
            'TELEGRAM_CHAT_ID':'synthetic-target','GITHUB_REPOSITORY':'synthetic/code',
            'GITHUB_RUN_ID':'303','GITHUB_RUN_ATTEMPT':'2','GITHUB_SHA':'a'*40}
        with patch.dict(os.environ,env,clear=True),patch('urllib.request.urlopen',side_effect=AssertionError('network')):
            fails(ValueError,lambda:produktion_runner.run_checked('signal',data,fetch=lambda _:(_ for _ in ()).throw(AssertionError('fetch'))))


def test_warning_at_80_percent_and_hard_write_budget_before_put():
    with healthy_fixture() as f:
        s=github.GitHubStore(f['api'],REPO,BRANCH,STORE_ID,'303','1').__enter__()
        s.writes=39;s.commit();assert s.writes==40 and s.warning
        s.writes=github.MAX_WRITES;before=f['api'].put_count
        fails(github.StoreUnavailable,s.commit)
        assert f['api'].put_count==before


def test_dispatch_timestamp_pins_slot_before_github_runner_delay():
    with healthy_fixture() as f:
        s=f['policy']['schedules']['watch'];slot=f['base']+53*freshness.MINUTE
        assert freshness.dispatch_slot(s,str(slot//1000))==slot
        assert freshness.dispatch_slot(s,str((slot+119000)//1000))==slot
        fails(ValueError,lambda:freshness.dispatch_slot(s,str((slot+120000)//1000)))
        fails(ValueError,lambda:freshness.dispatch_slot(s,'%cjo:unixtime%'))
        fails(ValueError,lambda:freshness.dispatch_slot(s,'-1'))
        actual={'GITHUB_REPOSITORY':'synthetic/code', 'GITHUB_RUN_ID':'303','GITHUB_RUN_ATTEMPT':'2',
            'GITHUB_SHA':f['policy']['identity']['code_sha'], 'GITHUB_REF':'refs/heads/synthetic-runtime',
            'GITHUB_WORKFLOW_REF':'synthetic/code/.github/workflows/watch.yml@refs/heads/synthetic-runtime'}
        binding=p3_run_binding.prepare(f['policy'],'watch',str(slot//1000),actual)
        assert binding['BTC_DELIVERY_EXPECTED_START_MS']==str(slot)
        assert binding['BTC_DELIVERY_RUN_ATTEMPT']=='2'
        actual['GITHUB_WORKFLOW_REF']='foreign/.github/workflows/watch.yml@refs/heads/main'
        fails(ValueError,lambda:p3_run_binding.prepare(f['policy'],'watch',str(slot//1000),actual))


def test_backup_receipt_manifest_is_bound_and_reader_clients_share_budget():
    with healthy_fixture() as f:
        source=json.loads(f['api'].records[f['backup']['store_commit_sha']]['body'])
        manifest={'schema':'p3-backup-set-v2',
            'stream_id':f['policy']['identity']['stream_id'],'store_path':github.STORE_PATH,
            'identity':{'repo':REPO,'branch':BRANCH,'store_id':STORE_ID,'stream_id':f['policy']['identity']['stream_id']},
            'pin':f['backup']['store_commit_sha'],'snapshot_digest':source['body_digest'],
            'revision':source['revision'],'code_sha':source['snapshot']['control']['code_sha'],
            'config_sha256':source['snapshot']['control']['config_sha256']}
        manifest.update(package_manifest_sha256=['d'*64],package_count=1,
            chain_sha256=digest(['d'*64]),history_count=source['revision']+1)
        receipt={'schema':'p3-verified-backup-receipt-v2','status':'confirmed',
            'verified_chain_sha256':manifest['chain_sha256'],'verified_source_pin':manifest['pin'],
            'verified_source_revision':manifest['revision'],'upload_readback_verified':True,
            'manifest':manifest,'manifest_sha256':digest(manifest),
            'expected_start_ms':f['backup']['expected_start_ms'],'verified_ms':f['backup']['verified_ms'],
            'history_verified':True,'restore_blocked_verified':True}
        record={'body':canonical(receipt).encode(),'commit_sha':'b'*40}
        f['policy']['backup_store']={'repo':'synthetic/second-backup','branch':'backup-only','receipt_path':'backup/latest-receipt.json'}
        budget=github_freshness.ReadBudget()
        a=github_freshness.ReadOnlyClient('synthetic-a',budget)
        b=github_freshness.ReadOnlyClient('synthetic-b',budget)
        with patch.object(b,'read',return_value=record):
            observed=github_freshness.read_backup(b,f['policy'])
            assert observed['snapshot_digest']==source['body_digest']
        a.requests=github_freshness.MAX_READS
        assert b.requests==a.requests
        with patch('urllib.request.urlopen',side_effect=AssertionError('network')):
            fails(github.StoreUnavailable,lambda:b._request('GET','/synthetic'))
        receipt['manifest']['identity']['store_id']='foreign'
        record['body']=canonical(receipt).encode()
        with patch.object(b,'read',return_value=record):
            fails(ValueError,lambda:github_freshness.read_backup(b,f['policy']))


def _health_crash_worker(path, slot, phase):
    slot=int(slot)
    with durable.VolumeStore(path,STORE_ID) as s, patch.dict(os.environ,run_env('watch',slot,'303')):
        original=s.commit
        def commit():
            original()
            h=s.snapshot['control']['health']
            current=h.get('current_run',{})
            successful=h.get('successful_runs',{}).get('watch',{}).get('run',{})
            candidate=h.get('completion_candidate',{})
            if ((phase=='start' and current.get('status')=='running')
                    or (phase=='candidate' and candidate.get('run_id')=='303' and successful.get('run_id')!='303')
                    or (phase=='attestation' and successful.get('run_id')=='303')):
                os._exit(71)
        with patch.object(s,'commit',side_effect=commit):
            run_health.record_event(s,'watch','start',slot+1000,None)
            finish(s,'watch',slot)


def test_process_loss_at_each_health_boundary_survives_restart_read_only():
    for phase in ('start','candidate','attestation'):
        with healthy_fixture('sqlite') as f:
            slot=f['base']+68*freshness.MINUTE
            proc=subprocess.run([sys.executable,__file__,'--p3-health-crash',str(f['path']),str(slot),phase],capture_output=True)
            assert proc.returncode==71,(phase,proc.stderr)
            # New process rereads only durable files after the child and its mutex died.
            with durable.read_only_volume(f['path'],STORE_ID) as s:
                h=s.snapshot['control']['health']
                assert h['current_run']['run_id']=='303'
                if phase=='start':assert h['current_run']['status']=='running'
                if phase=='candidate':assert h['successful_runs']['watch']['run']['run_id']=='204'
                if phase=='attestation':assert h['successful_runs']['watch']['run']['run_id']=='303'
            newer={'repository':'synthetic/code','workflow':'.github/workflows/watch.yml',
                'branch':'synthetic-runtime','head_sha':f['policy']['identity']['code_sha'],
                'run_id':'303','run_attempt':'1','expected_start_ms':slot,'created_ms':slot+500,
                'started_ms':slot+750,'completed_ms':slot+3000,'status':'completed','conclusion':'failure'}
            f['runs']['watch'].append(newer);f['now']=slot+4000
            assert produktion_health.evaluate_bound(f['path'],STORE_ID,f['policy'],f['runs'],f['backup'],f['now'])['http_status']==503


if __name__=='__main__' and '--p3-health-crash' in sys.argv:
    _health_crash_worker(*sys.argv[2:])
