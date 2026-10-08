"""Additive synthetic acceptance artifacts; never starts a service or transport."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'));sys.path.insert(0,str(ROOT/'tools'))
from production_contract import canonical
import durable_delivery as durable
import github_delivery as github
import freshness
from test_p3_operations import healthy_fixture, check
from test_production_runtime import seeded
from test_github_delivery import REPO, BRANCH, STORE_ID
import p3_store_probe
import p3_backup_rehearsal
import produktion_github_backup


def write(path,value):
    with Path(path).open('x',encoding='utf-8') as f:f.write(json.dumps(value,indent=2)+'\n')


def build(out):
    out=Path(out).resolve()
    write(out/'STORE-PROBE.json',p3_store_probe.probe())
    with healthy_fixture() as f:
        s=github.read_only(f['api'],REPO,BRANCH,STORE_ID)
        completions={str(b['completion']['revision']):s.read_revision(b['completion'])
            for index in s.snapshot['control']['health']['completed_runs'].values() for b in index.values()}
        fixture={'synthetic':True,'snapshot':s.snapshot,'revision':s.revision,
            'completion_snapshots':completions,'runs':f['runs'],'policy':f['policy'],
            'backup':f['backup'],'now_ms':f['now']}
        write(out/'HEALTHY-FIXTURE.json',fixture)
        before=f['api'].put_count
        result=check(f);assert result==freshness.response()
        write(out/'READONLY-CHECK.json',{'passed':True,'decision':result,
            'fake_puts_before':before,'fake_puts_after':f['api'].put_count,
            'new_puts':f['api'].put_count-before,'real_requests':0,
            'store_bytes':len(f['api'].record['body']),'completion_revision':s.revision})
        scenarios=[]
        for name, alter in (
            ('signal_missing',lambda g:g['runs'].update(signal=[])),
            ('watch_missing',lambda g:g['runs']['watch'].pop(0)),
            ('wrong_attempt',lambda g:g['runs']['watch'][-1].update(run_attempt='2')),
            ('failed_run',lambda g:g['runs']['watch'][-1].update(conclusion='failure')),
            ('backup_unverified',lambda g:g['backup'].update(history_verified=False)),
            ('run_too_long',lambda g:g['runs']['signal'][0].update(
                completed_ms=g['runs']['signal'][0]['started_ms']+freshness.MAX_RUN_MS+1))):
            g={**f,'runs':deepcopy(f['runs']),'backup':deepcopy(f['backup'])};alter(g)
            decision=check(g);assert decision['http_status']==503
            scenarios.append({'case':name,**decision})
        write(out/'FRESHNESS-COUNTERCASES.json',{'synthetic':True,'passed':True,'cases':scenarios})
        pin=f['api'].record['commit_sha'];rev=f['api'].envelope()['revision']
        package=p3_backup_rehearsal.package_fake(f['api'],REPO,BRANCH,STORE_ID,pin,'d'*64)
        write(out/'FAKE-BACKUP-PACKAGE.json',package)
        write(out/'FAKE-BLOCKED-RESTORE.json',p3_backup_rehearsal.restore_fake(
            package,out/'fake-blocked-restore',pin,rev))
    # A separate real local Git fixture proves bundle and object integrity;
    # its content and provenance remain explicitly synthetic.
    root=out/'synthetic-git-fixture';root.mkdir(exist_ok=False)
    path,_,paths=seeded(root)
    with durable.read_only_volume(path,STORE_ID) as s:
        seed=github.initial_envelope(s.snapshot,REPO,BRANCH,STORE_ID)
    repo=root/'repository';repo.mkdir()
    subprocess.run(['git','init','-b',BRANCH,str(repo)],check=True,capture_output=True)
    (repo/'delivery').mkdir()
    env={**os.environ,'GIT_AUTHOR_NAME':'Synthetic P3','GIT_COMMITTER_NAME':'Synthetic P3',
        'GIT_AUTHOR_EMAIL':'synthetic@example.invalid','GIT_COMMITTER_EMAIL':'synthetic@example.invalid'}
    for body in (seed,p3_store_probe.synthetic_active(seed)):
        (repo/'delivery/stream.json').write_bytes(body)
        subprocess.run(['git','-c','safe.directory='+repo.as_posix(),'-C',str(repo),'add','delivery/stream.json'],check=True,capture_output=True)
        subprocess.run(['git','-c','safe.directory='+repo.as_posix(),'-C',str(repo),'commit','-m','Synthetic P3 fixture'],env=env,check=True,capture_output=True)
    pin=produktion_github_backup.git(repo,'rev-parse','HEAD').decode().strip()
    identity={'repo':REPO,'branch':BRANCH,'store_id':STORE_ID,
              'stream_id':json.loads(seed)['snapshot']['control']['stream_id']}
    m=produktion_github_backup.package_local(repo,BRANCH,pin,identity,paths[-1],out/'synthetic-local-git-backup')
    r=produktion_github_backup.restore_local(out/'synthetic-local-git-backup',out/'synthetic-local-git-restore',pin,m['revision'])
    write(out/'LOCAL-GIT-BACKUP-RESTORE.json',{'synthetic':True,'passed':True,'manifest':m,
        'restore':r,'real_private_backup_write':False})
    write(out/'SCOPE.json',{'real_external_store_requests':0,'real_backup_writes':0,
        'real_transport_calls':0,'historical_strategy_executions':0,'active_workflow_changes':0,
        'pushes':0,'private_test_repo_provisioned':False,'host_provisioned':False,
        'cron_job_configured':False,'alarm_sent':False,'p4_authorized':False,
        'fixtures_are_not_production_size_measurement':True})


if __name__=='__main__':
    for key in list(os.environ):
        if key.startswith(('BTC_DELIVERY_','TELEGRAM_','GITHUB_','GH_')):del os.environ[key]
    with patch('urllib.request.urlopen',side_effect=AssertionError('Network forbidden')):
        build(sys.argv[1])
