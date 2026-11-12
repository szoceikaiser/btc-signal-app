"""Monitor-only entry. Reuse the reviewed delivery install and observer pin."""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types

OBSERVER = 'f3f054851f500af1926b149f13a2ee8890a8c2bc'
PHASES = ('configuration','admission','fence','latest_run','schedule','completions',
          'independent_backup','backup_ancestry','final_admission','final_reobservation','complete')
REASONS = ('time_limit','get_limit','provider_error','provider_quota','scope_refused',
           'evidence_changed','evidence_invalid','evidence_unavailable')


def public_result(result, budget):
    detail=result.get('diagnostic',{})
    phase=detail.get('phase')
    ok=result.get('http_status')==200
    value={'phase':phase if phase in PHASES else 'configuration',
           'status':'ok' if ok else 'refused_or_halted',
           'get':budget.requests,'elapsed_ms':int((time.monotonic()-budget.started)*1000)}
    if not ok:
        reason=detail.get('reason')
        value['reason']=reason if reason in REASONS else 'evidence_unavailable'
    return value


def verified(path, expected):
    body=path.read_bytes()
    if hashlib.sha256(body).hexdigest()!=expected:
        raise ValueError('Unreviewed monitor input')
    return compile(body,str(path),'exec')


def install(a):
    extension=Path(a.extension).resolve()
    loader=extension/'tools/pinned_delivery_entry.py'
    source=extension/'ops/continuous/freshness/actions_freshness.py'
    monitor_code=verified(source,a.monitor_sha256)
    base={'__name__':'reviewed_delivery_entry','__file__':str(loader)}
    exec(verified(loader,a.loader_sha256),base)
    base['install'](a.core,extension,a.manifest_sha256)
    monitor=types.ModuleType('reviewed_freshness_runtime')
    exec(monitor_code,monitor.__dict__)

    observer=Path(a.observer_root).resolve()
    def git(*args):
        return subprocess.check_output(['git','-C',str(observer),*args],
                                       text=True,stderr=subprocess.DEVNULL).strip()
    if (git('rev-parse','HEAD')!=OBSERVER
            or git('status','--porcelain','--','engine','tools','ops','site','.github')):
        raise ValueError('Exact clean observer required')
    spec=importlib.util.spec_from_file_location('produktion_actions_runner',observer/'tools/produktion_actions_runner.py')
    observer_entry=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer_entry)
    sys.modules['produktion_actions_runner']=observer_entry
    return monitor


def observe(path, monitor, budget):
    # Same admission and bound read sequence as the pinned observer CLI.
    import public_access as public
    phase='configuration'
    try:
        with Path(path).open('rb') as f: raw=f.read(128*1024+1)
        if len(raw)>128*1024: raise ValueError()
        policy=json.loads(raw)
        if policy.get('enabled') is not True: raise ValueError()
        if policy.get('python_version') and tuple(policy['python_version'])!=sys.version_info[:3]:
            raise ValueError()
        d=policy['deployment'];v=policy['independent_verifier']
        from job_quota import read_only_environment
        read_only_environment()
        public.deployment(policy['public_access'],d)
        if (v['binding']['repository']!=d['code_repository']
                or v['binding']['branch']!=d['code_ref'].removeprefix('refs/heads/')
                or v['binding']['workflow']!='.github/workflows/backup-verify.yml'):
            raise ValueError()
        t=policy['monitor_entry']
        from reviewed_actions_entry import actual
        from produktion_actions_runner import check_code_pin
        check_code_pin(t['code_sha'])
        token=os.environ.get('GITHUB_TOKEN')
        entry_reader=monitor.Reader(token,[t['repository']],budget,metadata=True)
        actual(entry_reader,t['repository'],'refs/heads/'+t['branch'],t['code_sha'],t['workflow'],t['workflow_sha256'])
        phase='admission'
        source=monitor.Reader(token,[d['private_store_repository']],budget)
        code=monitor.Reader(token,[d['code_repository'],v['binding']['repository']],budget,metadata=True)
        code_branches=[(d['code_repository'],d['code_ref'].removeprefix('refs/heads/'))]
        public.check(code,policy['public_access'],code_branches)
        backup=monitor.Reader(token,[v['repository'],policy['backup_target']['repository']],budget)
        source_branches=[(d['private_store_repository'],b) for b in (d['store_branch'],d['fence_branch'])]
        public.check(source,policy['public_access'],source_branches)
        branches=[(v['repository'],v['receipt_branch']),
                  (policy['backup_target']['repository'],policy['backup_target']['branch'])]
        public.check(backup,policy['public_access'],branches)
        def admission():
            public.check(source,policy['public_access'],source_branches,source_branches)
            public.check(backup,policy['public_access'],branches,branches)
            public.check(code,policy['public_access'],code_branches)
        return monitor.check(source,code,backup,policy,int(time.time()*1000),admission)
    except Exception as exc:
        return monitor.failure(phase,exc)


def main():
    try:
        with open(os.devnull,'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            parser=argparse.ArgumentParser()
            for name in ('core','extension','observer-root','loader-sha256','manifest-sha256','monitor-sha256','policy'):
                parser.add_argument('--'+name,required=True)
            args=parser.parse_args()
            monitor=install(args)
            from github_freshness import ReadBudget
            budget=ReadBudget()
            value=public_result(observe(args.policy,monitor,budget),budget)
    except BaseException:
        value={'phase':'bootstrap','status':'refused_or_halted','reason':'binding_refused'}
    print(json.dumps(value,sort_keys=True))
    return 0 if value['status']=='ok' else 20


if __name__=='__main__': raise SystemExit(main())
