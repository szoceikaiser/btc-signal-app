"""Hash-pinned delivery overlay; pristine strategy Core20D stays authoritative.

The calling reviewed workflow must authenticate this file before executing it.
No module search path from the extension is used for strategy imports.
"""
import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types
import contextlib
import os
import re

CORE = '20d755a4332fb32aeab08b1973b650eeae10f31e'

def public_monitor_result(value):
    known={'configuration','fence','latest_run','schedule','completions','independent_backup',
           'backup_ancestry','final_reobservation','complete'}
    detail=value.get('diagnostic',{})
    result={'phase':detail.get('phase') if detail.get('phase') in known else 'monitor',
            'status':'ok' if value.get('http_status')==200 else 'refused_or_halted'}
    for key in ('stream_commit','fence_commit'):
        if re.fullmatch('[0-9a-f]{40}',str(detail.get(key,''))):result[key]=detail[key]
    return result
MODULES = {'aborted_maintenance':'engine/aborted_maintenance.py',
           'safe_recovery':'engine/safe_recovery.py',
           'github_recovery_journal':'engine/github_recovery_journal.py',
           'github_recovery':'tools/github_recovery.py',
           'continuous_operations':'tools/continuous_operations.py',
           'actions_delivery':'engine/actions_delivery.py',
           'actions_freshness':'engine/actions_freshness.py',
           'produktion_pages_export':'tools/produktion_pages_export.py',
           'p4_backup_pair':'tools/p4_backup_pair.py'}

def install(core, extension, manifest_sha256):
    core=Path(core).resolve(); extension=Path(extension).resolve()
    raw=(extension/'delivery-extension.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest_sha256:
        raise ValueError('Unreviewed extension manifest')
    manifest=json.loads(raw)
    expected=set(MODULES.values())|{'tools/pinned_delivery_entry.py'}
    if manifest['core']!=CORE or set(manifest['files'])!=expected:
        raise ValueError('Extension scope differs')
    sources={}
    for path,sha in manifest['files'].items():
        source=extension/path
        if source.is_symlink() or not source.resolve().is_relative_to(extension):
            raise ValueError('Extension path escape')
        body=source.read_bytes()
        if hashlib.sha256(body).hexdigest()!=sha: raise ValueError('Extension bytes changed')
        sources[path]=body
    if (subprocess.check_output(['git','-C',str(core),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()!=CORE
            or subprocess.check_output(['git','-C',str(core),'status','--porcelain',
                '--untracked-files=all','--','.',':(exclude).runtime'],text=True,stderr=subprocess.DEVNULL)):
        raise ValueError('Clean exact strategy core required')
    # Load original imports first. Existing objects/ROOT/check_code_pin retain core paths.
    sys.path[:0]=[str(core/'engine'),str(core/'tools')]
    entry=importlib.import_module('produktion_actions_runner')
    new=('aborted_maintenance','safe_recovery','github_recovery_journal','github_recovery','continuous_operations')
    modules={name:importlib.import_module(name) for name in MODULES if name not in new}
    for name in new:
        modules[name]=types.ModuleType(name);sys.modules[name]=modules[name]
    for name in ('aborted_maintenance','safe_recovery','github_recovery_journal','actions_delivery','actions_freshness',
                 'produktion_pages_export','p4_backup_pair','continuous_operations','github_recovery'):
        module=modules[name]; path=MODULES[name]
        module.__file__=str(core/path)
        exec(compile(sources[path],str(extension/path),'exec'),module.__dict__)
    return entry

def _run(phase):
    p=argparse.ArgumentParser()
    p.add_argument('--core',required=True); p.add_argument('--extension',required=True)
    p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--kind',choices=('signal','watch','lage'))
    p.add_argument('--runtime'); p.add_argument('--data-dir')
    p.add_argument('--tool',choices=('p4_hosted_backup.py','produktion_actions_freshness.py','renderer','continuous_operations.py'))
    p.add_argument('--renderer-root')
    p.add_argument('--observer-root')
    p.add_argument('tool_args',nargs=argparse.REMAINDER)
    a=p.parse_args()
    phase[0]='extension'
    entry=install(a.core,a.extension,a.manifest_sha256)
    phase[0]='runtime'
    if a.tool:
        import runpy
        target=Path(a.core)/'tools'/a.tool
        if a.tool=='continuous_operations.py':
            target=Path(a.extension)/'tools'/a.tool
        if a.tool=='produktion_actions_freshness.py':
            observer=Path(a.observer_root).resolve()
            pin='f3f054851f500af1926b149f13a2ee8890a8c2bc'
            if (subprocess.check_output(['git','-C',str(observer),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()!=pin
                    or subprocess.check_output(['git','-C',str(observer),'status','--porcelain','--',
                        'engine','tools','ops','site','.github'],text=True,stderr=subprocess.DEVNULL)):
                raise ValueError('Exact clean observer required')
            # The observer's original code-pin check must inspect its own ROOT,
            # not the strategy checkout. Isolate its entry module namespace.
            old_entry=sys.modules['produktion_actions_runner']
            spec=importlib.util.spec_from_file_location('produktion_actions_runner',observer/'tools/produktion_actions_runner.py')
            observer_entry=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(observer_entry)
            sys.modules['produktion_actions_runner']=observer_entry
            target=observer/'tools'/a.tool
        if a.tool=='renderer':
            renderer=Path(a.renderer_root).resolve()
            if (subprocess.check_output(['git','-C',str(renderer),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
                    !='769240621314677e13da5afbf32821d6a350c9df'
                    or subprocess.check_output(['git','-C',str(renderer),'status','--porcelain'],text=True,stderr=subprocess.DEVNULL)):
                raise ValueError('Exact clean renderer required')
            target=renderer/'tools/c05_pages_export.py'
        sys.argv=[str(target)]+(a.tool_args[1:] if a.tool_args[:1]==['--'] else a.tool_args)
        try:
            if a.tool=='produktion_actions_freshness.py':
                parser=argparse.ArgumentParser();parser.add_argument('--policy',required=True)
                args=parser.parse_args(sys.argv[1:])
                namespace=runpy.run_path(str(target),run_name='reviewed_monitor_module')
                result=namespace['run'](args.policy)
                phase[1]=public_monitor_result(result)
                if result.get('http_status')!=200:raise SystemExit(20)
            else:runpy.run_path(str(target),run_name='__main__')
        finally:
            if a.tool=='produktion_actions_freshness.py':
                sys.modules['produktion_actions_runner']=old_entry
    else:
        if not a.kind or not a.runtime or not a.data_dir: p.error('Signal/watch runtime required')
        entry.run_runtime(a.runtime,a.kind,a.data_dir)

def main():
    phase=['arguments',None]
    code=0
    try:
        # Provider/exception text is never public, including successful fetch logs.
        with open(os.devnull,'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            _run(phase)
    except SystemExit as exc:
        code=0 if exc.code in (None,0) else 20
    except BaseException:
        code=20
    if phase[1] is not None:print(json.dumps(phase[1],sort_keys=True))
    if code:
        print('delivery phase='+phase[0]+' reason=refused_or_halted',file=sys.stderr)
    return code

if __name__=='__main__': raise SystemExit(main())
