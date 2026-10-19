"""Separately pinned presentation; the clean Core20D owns every live check.

No execution simulation, provider expansion, store write or alternate upload tree.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

RENDERER = Path(__file__).resolve().parents[1]
CORE_SHA = '20d755a4332fb32aeab08b1973b650eeae10f31e'
CONFIG_SHA = '3efe8a17330c228a75fe879d4e7c7ed0cade766e4a07ca0c05832b88aa3d282b'
STRATEGY_SHA = 'a99be30ae26a753f9734fbe2d67ac49f33e090a691904336421742f92420f787'
REPORT_SHA = '6d64486e83917a01976296c4688fb019f6c56d6d66a0f9862df36041cafb6f19'
STATIC = ('index.html', 'chart_signals.js', 'c05_report.js')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(RENDERER), *args], timeout=15).decode().strip()


def renderer_binding(runtime):
    pin = runtime.get('renderer', {})
    code = pin.get('code_sha', '')
    expected = {'schema':'btc-c05-renderer-v1', 'code_sha':code,
                'core_code_sha':CORE_SHA, 'runtime_config_sha256':CONFIG_SHA,
                'strategy_sha256':STRATEGY_SHA, 'report_sha256':REPORT_SHA}
    if (pin != expected or not re.fullmatch('[0-9a-f]{40}', code) or code == CORE_SHA
            or git('rev-parse', 'HEAD') != code
            or git('status', '--porcelain', '--untracked-files=all')):
        raise ValueError('Exact clean independently reviewed renderer required')
    if runtime['deployment']['code_sha'] != CORE_SHA or runtime['deployment']['config_sha256'] != CONFIG_SHA:
        raise ValueError('Renderer cannot change strategy/store deployment')
    report = (RENDERER/'site/c05-report.json').read_bytes()
    if sha(report) != REPORT_SHA:
        raise ValueError('Missing, changed or foreign C05 report')
    validate_report(json.loads(report))
    return expected


def validate_report(r):
    if (r['schema'] != 'btc-c05-historical-report-v1' or r['currency'] != 'USD'
            or r['strategy_sha256'] != STRATEGY_SHA or r['runtime_config_sha256'] != CONFIG_SHA
            or r['source_start_utc'] != '2026-01-18T20:00:00+00:00'
            or r['source_end_utc'] != '2026-10-04T08:00:00+00:00'
            or r['initial_cash_usd'] != 10000 or r['initial_btc'] != 0
            or r['new_strategy_runs'] != 0 or r['is_live_account'] is not False
            or r['base_scenario'] != 'S0' or len(r['months']) != 10
            or [s['id'] for s in r['scenarios']] != ['S0','S1','S2','S3','S4']):
        raise ValueError('Historical C05 identity differs')
    prior = r['initial_cash_usd']
    factor = 1
    for i, m in enumerate(r['months']):
        if (m['month'] != '2026-%02d' % (i+1) or m['start_usd'] != prior
                or m['partial_month'] != (i in (0,9))
                or not math.isclose((m['end_usd']/prior-1)*100, m['return_pct'], abs_tol=1e-10)
                or not math.isclose(m['end_usd']-prior, m['change_usd'], abs_tol=1e-9)):
            raise ValueError('Monthly chain differs')
        prior = m['end_usd']; factor *= 1+m['return_pct']/100
    if (prior != r['base_end_usd'] or not math.isclose(10000*factor, prior, abs_tol=1e-8)
            or r['scenarios'][0]['end_usd'] != prior
            or r['base_end_usd'] != r['base_final_cash_usd']+r['base_final_btc_value_usd']):
        raise ValueError('Final accounting differs')


def bind_core(path):
    core = Path(path).resolve()
    if core == RENDERER:
        raise ValueError('Separate Core20D checkout required')
    sys.path[:0] = [str(core/'tools'), str(core/'engine')]
    import produktion_pages_export as base
    if base.ROOT != core:
        raise ValueError('Core import location differs')
    base.check_code_pin(CORE_SHA)
    return base


def source_files(base):
    result = {name:base.bounded_file(RENDERER/'site'/name, 1024*1024) for name in STATIC}
    result['live_projection.js'] = base.bounded_file(base.ROOT/'site/live_projection.js', 1024*1024)
    result['c05-report.json'] = base.bounded_file(RENDERER/'site/c05-report.json', 128*1024)
    for name in base.HISTORY:
        result['history/'+name] = base.bounded_file(base.ROOT/'site/data'/name, 16*1024*1024)
    return result


def manifest_for(base, body, d, private_pins, renderer):
    pins = {'code_sha':d['code_sha'], 'config_sha256':d['config_sha256'],
            'projection_binding':base.digest({'deployment':d, 'pins':private_pins})}
    return {'schema':'btc-pages-manifest-v1', 'projection':'projection-'+sha(body)+'.json',
            'sha256':sha(body), 'pins':pins, 'renderer':renderer,
            'report':{'path':'c05-report.json', 'sha256':REPORT_SHA},
            'history':{name:{'path':'history/'+name, 'sha256':sha(raw), 'source_code_sha':CORE_SHA}
                       for name in base.HISTORY
                       for raw in [base.bounded_file(base.ROOT/'site/data'/name,16*1024*1024)]},
            'historical_notice':'C05/S0 bis 04.10.2026 08:00 UTC; H/V1 separater alter Core20D-Stand, keine C05-Marken'}


def verify_package(base, out, d, private_pins, renderer):
    manifest = json.loads(base.bounded_file(out/'projection-manifest.json',16384))
    filename = manifest['projection']
    if not re.fullmatch(r'projection-[0-9a-f]{64}\.json', filename):
        raise ValueError('Projection path differs')
    body = base.bounded_file(out/filename,750*1024)
    expected_manifest = manifest_for(base, body, d, private_pins, renderer)
    value = json.loads(body); now = int(time.time()*1000)
    if (manifest != expected_manifest or value['pins'] != manifest['pins']
            or value['schema'] != 'btc-public-projection-v1'
            or not 0 <= now-value['observed_ms'] < 120000
            or not 0 <= now-(value['signal_asof_ms']+14400000) <= 8*3600000):
        raise ValueError('Package mixed, changed or expired')
    files = source_files(base)
    files[filename] = body
    files['projection-manifest.json'] = base.canonical(manifest).encode()
    entries = list(out.rglob('*'))
    if (any(p.is_symlink() for p in entries)
            or {p.relative_to(out).as_posix() for p in entries if p.is_file()} != set(files)):
        raise ValueError('Additional or missing upload file')
    for name, raw in files.items():
        if base.bounded_file(out/name,16*1024*1024) != raw:
            raise ValueError('Upload differs from clean bound source: '+name)


def export(base, runtime_path, config_path, out, verify=None, identities_only=False):
    from job_quota import read_only_environment, Headers
    read_only_environment(); quota = Headers()
    runtime = json.loads(Path(runtime_path).read_text(encoding='utf-8'))
    renderer = renderer_binding(runtime)
    d = base.validate(runtime, quota)
    branches = [(d['private_store_repository'],b) for b in (d['store_branch'],d['fence_branch'])]
    preflight = base.public.preflight(runtime['public_access'], branches, () if identities_only else branches, quota)
    config = json.loads(Path(config_path).read_text(encoding='utf-8'))
    from production_contract import effective_config
    if base.digest(effective_config(config)) != d['config_sha256']:
        raise ValueError('Configuration differs from reviewed pin')
    client = base.ReadClient(os.environ.get('GITHUB_TOKEN'),d['private_store_repository'],
                            {d['store_branch']:base.github.STORE_PATH,d['fence_branch']:base.actions.FENCE_PATH},quota=quota)
    snapshot, private_pins = base.observe(client,d,config)
    out = Path(out)
    receipt = {'schema':'btc-c05-pages-local-receipt-v1','deployment':d,'pins':private_pins,'renderer':renderer}
    if verify:
        if json.loads(base.bounded_file(verify,16384)) != receipt:
            raise ValueError('Pair/renderer moved since package preparation')
        verify_package(base,out,d,private_pins,renderer)
    else:
        now = int(time.time()*1000)
        if not 0 <= now-(snapshot['engine']['last_signal_ts']+14400000) <= 8*3600000:
            raise ValueError('Signal slice too old or in future')
        pins = {'code_sha':d['code_sha'],'config_sha256':d['config_sha256'],
                'projection_binding':base.digest({'deployment':d,'pins':private_pins})}
        body = base.project(snapshot,now,pins)
        manifest = manifest_for(base,body,d,private_pins,renderer)
        if out.with_suffix('.receipt.json').exists():
            raise FileExistsError('Preserve previous receipt')
        out.mkdir(parents=True,exist_ok=False)
        for name,raw in source_files(base).items():
            target=out/name; target.parent.mkdir(exist_ok=True)
            with target.open('xb') as f: f.write(raw)
        (out/manifest['projection']).write_bytes(body)
        (out/'projection-manifest.json').write_text(base.canonical(manifest),encoding='utf-8')
        with out.with_suffix('.receipt.json').open('x',encoding='utf-8') as f: f.write(base.canonical(receipt))
        verify_package(base,out,d,private_pins,renderer)
    client.guard()
    return {'get':client.gets,'preflight_get':preflight,'put':0,'transport':0}


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for key in ('core','runtime','config','out'): p.add_argument('--'+key,required=True)
    p.add_argument('--verify');p.add_argument('--identities-only',action='store_true')
    a=p.parse_args()
    try:
        export(bind_core(a.core),a.runtime,a.config,a.out,a.verify,a.identities_only)
    except Exception:
        print('Bound C05 Pages export refused; no publication.',file=sys.stderr)
        sys.exit(20)
