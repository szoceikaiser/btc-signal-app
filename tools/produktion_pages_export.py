"""Bounded read-only export of one exact closed Actions/stream pair."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'engine'), str(ROOT/'tools')]
import actions_delivery as actions
import github_delivery as github
import public_access as public
from production_confirmation import ProductionContentsClient
from production_contract import canonical, digest, verify_runtime_config
from produktion_actions_runner import check_code_pin, deployment, verify_health
from public_projection import project

SCHEMA = 'btc-pages-export-v1'
WORKFLOW = '.github/workflows/pages.yml'
STATIC = ('index.html', 'chart_signals.js', 'live_projection.js')
HISTORY = ('backtest.json', 'backtest_signals.json', 'execution_v1.json')


def bounded_file(path, limit):
    with Path(path).open('rb') as f:
        raw = f.read(limit+1)
    if len(raw) > limit:
        raise ValueError('Local publication byte budget exceeded')
    return raw


class ReadClient(github.GitHubContentsClient):
    open_request = staticmethod(ProductionContentsClient.open_request)
    response_byte_limit = 2*1024*1024

    def __init__(self, token, repo, branches, clock=time.monotonic, quota=None):
        from job_quota import bind
        super().__init__(token, timeout=10)
        bind(self,token,quota)
        self.repo, self.branches, self.clock = repo, branches, clock
        self.started = self.highwater = clock()
        self.gets = self.bytes = self._response_bytes = 0
        self.allowed = set()

    def _request(self, method, route, payload=None):
        now = self.clock()
        if (method != 'GET' or payload is not None or route not in self.allowed
                or self.gets >= 12 or self.bytes+ self.response_byte_limit > 24*1024*1024
                or not self.highwater <= now < self.started+120):
            raise github.StoreUnavailable('Read-only export request/time/byte binding refused')
        self.highwater = now
        from job_quota import cached
        self.quota_headers.before()
        hit=cached(self,route)
        if hit is not None: return hit
        self.gets += 1
        # Reserve all response bytes, including failed responses.
        self.bytes += self.response_byte_limit
        self.timeout = min(10, self.started+120-now)
        result = super()._request(method, route, payload)
        now = self.clock()
        if not self.highwater <= now < self.started+120:
            raise github.StoreUnavailable('Export deadline exceeded')
        self.highwater = now
        return result

    def read(self, repo, branch, path=github.STORE_PATH):
        if repo != self.repo or self.branches.get(branch) != path:
            raise github.StoreConflict('Export branch/path differs from pin')
        route = self._route(repo, '/git/ref/heads/'+urllib.parse.quote(branch, safe=''))
        self.allowed = {route}
        # observe() checks both heads again after projection validation.
        ref=self._request('GET',route)
        return self.read_at(repo,ref['object']['sha'],path)

    def read_at(self, repo, commit_sha, path=github.STORE_PATH):
        if repo != self.repo or path not in self.branches.values():
            raise github.StoreConflict('Export immutable read differs')
        route = self._route(repo, '/contents/'+urllib.parse.quote(path, safe='/'))+'?'+urllib.parse.urlencode({'ref':commit_sha})
        self.allowed.add(route)
        return super().read_at(repo, commit_sha, path)

    def update(self, *args, **kwargs):
        raise github.StoreConflict('Export has no write path')

    def guard(self):
        now = self.clock()
        if not self.highwater <= now < self.started+120:
            raise github.StoreUnavailable('Export/package deadline exceeded')
        self.highwater = now


def validate(runtime,quota=None):
    if runtime.get('python_version') and tuple(runtime['python_version'])!=sys.version_info[:3]:
        raise ValueError('Reviewed Pages Python runtime differs')
    d = runtime.get('deployment', {})
    public.deployment(runtime['public_access'],d)
    if d != deployment(d):
        raise ValueError('Pages deployment fields must exactly match delivery deployment')
    if (runtime.get('enabled') is not True or runtime.get('schema') != SCHEMA
            or runtime.get('workflow') != WORKFLOW or runtime.get('deployment_schema') != actions.POLICY
            or d.get('workflows') != actions.WORKFLOWS or d.get('confirmation_policy') != actions.POLICY
            or d.get('fence_path') != actions.FENCE_PATH or d.get('store_path') != github.STORE_PATH
            or d.get('store_branch') == d.get('fence_branch')
            or any(not v for v in d.values())
            or not re.fullmatch('[0-9a-f]{40}', d.get('code_sha') or '')
            or any(not re.fullmatch('[0-9a-f]{64}', d.get(k) or '') for k in ('config_sha256','activation_review_sha256'))
            or os.environ.get('GITHUB_REPOSITORY') != d.get('code_repository')
            or os.environ.get('GITHUB_REF') != d.get('code_ref')
            or (os.environ.get('GITHUB_SHA') != d.get('code_sha') and not runtime.get('entry_workflows',{}).get(WORKFLOW))
            or os.environ.get('GITHUB_WORKFLOW_REF') != d['code_repository']+'/'+WORKFLOW+'@'+d['code_ref']
            or os.environ.get('GITHUB_RUN_ATTEMPT') != '1'):
        raise ValueError('Explicit reviewed Pages deployment and actual entry required')
    check_code_pin(d['code_sha'])
    if runtime.get('entry_workflows',{}).get(WORKFLOW):
        from reviewed_actions_entry import actual,EntryReader
        actual(EntryReader(os.environ.get('GITHUB_TOKEN'),d['code_repository'],quota),
               d['code_repository'],d['code_ref'],d['code_sha'],WORKFLOW,runtime['entry_workflows'][WORKFLOW])
    return d


def observe(client, d, config):
    repo = d['private_store_repository']
    first = client.read(repo, d['fence_branch'], actions.FENCE_PATH)
    fence = actions.parse_fence(first, d)
    if fence['phase'] != 'closed' or not fence['completion'] or fence['run'] is None:
        raise github.StoreConflict('No exact closed completion to publish')
    store = github.read_only(client, repo, d['store_branch'], d['store_id'])
    control = store.snapshot['control']
    verify_runtime_config(store.snapshot, config, code_sha=d['code_sha'], bot_identity=d['bot_identity'])
    if (control['mode'] != 'active' or control.get('owner') is not None or store.blocked()
            or any(m['status'] != 'confirmed' for s in [store.snapshot['engine'], *store.snapshot['commands'].values()]
                   for m in s.get('_delivery', {}).get('messages', []))
            or fence['completion']['stream'] != store.confirmed_record()):
        raise github.StoreConflict('Unclear/unconfirmed/foreign stream cannot publish')
    if fence['run']['kind'] == 'lage':
        from types import SimpleNamespace
        operation_id = digest({'repository':d['code_repository'], 'workflow':fence['run']['workflow'], 'run_id':fence['run']['id']})
        client_binding = SimpleNamespace(run=fence['run'], environment={
            'BTC_DELIVERY_RUN_REPOSITORY':d['code_repository'], 'BTC_DELIVERY_CODE_SHA':d['code_sha']})
        actions.verify_command(store.snapshot, client_binding, operation_id)
    else:
        verify_health(store, d, fence['run'])
    second_store = github.read_only(client, repo, d['store_branch'], d['store_id'])
    last = client.read(repo, d['fence_branch'], actions.FENCE_PATH)
    if first != last or store.confirmed_record() != second_store.confirmed_record():
        raise github.StoreConflict('Store/fence moved during public observation')
    return store.snapshot, {'stream':store.confirmed_record(), 'fence_commit':first['commit_sha'], 'fence_blob':first['blob_sha']}


def export(runtime_path, config_path, out, verify=None, identities_only=False):
    from job_quota import read_only_environment
    read_only_environment()
    from job_quota import Headers
    quota=Headers()
    runtime = json.loads(Path(runtime_path).read_text(encoding='utf-8'))
    d = validate(runtime,quota)
    branches=[(d['private_store_repository'],b) for b in (d['store_branch'],d['fence_branch'])]
    # The reviewed workflow performs the full mutable protection check at its
    # final pre-deploy gate. Earlier package steps still verify public identity.
    preflight_gets=public.preflight(runtime['public_access'],branches,() if identities_only else branches,quota)
    config = json.loads(Path(config_path).read_text(encoding='utf-8'))
    from production_contract import effective_config
    if digest(effective_config(config)) != d['config_sha256']:
        raise ValueError('Public export configuration differs from reviewed pin')
    client = ReadClient(os.environ.get('GITHUB_TOKEN'), d['private_store_repository'],
                        {d['store_branch']:github.STORE_PATH, d['fence_branch']:actions.FENCE_PATH},quota=quota)
    snapshot, private_pins = observe(client, d, config)
    if verify:
        saved = json.loads(bounded_file(verify, 16384))
        if saved != {'deployment': d, 'pins':private_pins}:
            raise github.StoreConflict('Publication snapshot moved after package preparation')
        verify_package(Path(out), d, private_pins)
        client.guard()
        return {'get':client.gets, 'preflight_get':preflight_gets, 'put':0, 'transport':0}
    now = int(time.time()*1000)
    # Observation time cannot make an old signal/data slice look fresh.
    if not 0 <= now-(snapshot['engine']['last_signal_ts']+14400000) <= 8*3600000:
        raise github.StoreConflict('Signal/data slice too old or from the future')
    pins = {'code_sha':d['code_sha'], 'config_sha256':d['config_sha256'],
            'projection_binding': digest({'deployment':d, 'pins':private_pins})}
    body = project(snapshot, now, pins)
    content_hash = hashlib.sha256(body).hexdigest()
    filename = 'projection-'+content_hash+'.json'
    # Construct only after all checks; never copy inherited live site/data.
    out = Path(out)
    if out.with_suffix('.receipt.json').exists():
        raise FileExistsError('Existing publication receipt must be preserved')
    out.mkdir(parents=True, exist_ok=False)
    for name in STATIC:
        (out/name).write_bytes(bounded_file(ROOT/'site'/name, 1024*1024))
    history = {}
    (out/'history').mkdir()
    for name in HISTORY:
        source = ROOT/'site/data'/name
        if source.is_file():
            raw = bounded_file(source, 16*1024*1024)
            json.loads(raw)  # reviewed, previously public frozen artifacts only
            sha = hashlib.sha256(raw).hexdigest()
            (out/'history'/name).write_bytes(raw)
            history[name] = {'path':'history/'+name, 'sha256':sha, 'source_code_sha':d['code_sha']}
    (out/filename).write_bytes(body)
    manifest = {'schema':'btc-pages-manifest-v1', 'projection':filename, 'sha256':content_hash,
                'pins':pins, 'history':history, 'historical_notice':'Historische Simulation; keine neue C05-Berechnung'}
    (out/'projection-manifest.json').write_text(canonical(manifest),encoding='utf-8')
    # Private locators stay alongside the package, never inside the upload tree.
    with out.with_suffix('.receipt.json').open('x',encoding='utf-8') as f:
        f.write(canonical({'deployment':d, 'pins':private_pins}))
    client.guard()
    return {'get':client.gets, 'preflight_get':preflight_gets, 'put':0, 'transport':0, 'public_bytes':len(body)}


def verify_package(out, d, private_pins):
    manifest = json.loads(bounded_file(out/'projection-manifest.json', 16384))
    sha = manifest['sha256']
    pins = {'code_sha':d['code_sha'], 'config_sha256':d['config_sha256'],
            'projection_binding':digest({'deployment':d, 'pins':private_pins})}
    if (not re.fullmatch('[0-9a-f]{64}', sha) or manifest['projection'] != 'projection-'+sha+'.json'
            or manifest['pins'] != pins):
        raise github.StoreConflict('Public package pins changed')
    body = bounded_file(out/manifest['projection'],750*1024)
    value = json.loads(body)
    now = int(time.time()*1000)
    if (hashlib.sha256(body).hexdigest() != sha or value['pins'] != pins
            or not 0 <= now-value['observed_ms'] < 120000
            or not 0 <= now-(value['signal_asof_ms']+14400000) <= 8*3600000):
        raise github.StoreConflict('Public package changed or expired')
    expected = set(STATIC) | {'projection-manifest.json',manifest['projection']}
    for name in STATIC:
        if bounded_file(out/name,1024*1024) != bounded_file(ROOT/'site'/name,1024*1024):
            raise github.StoreConflict('Public code differs from reviewed pin')
    for name, item in manifest['history'].items():
        if (name not in HISTORY or item['path'] != 'history/'+name or item['source_code_sha'] != d['code_sha']
                or hashlib.sha256(bounded_file(out/item['path'],16*1024*1024)).hexdigest() != item['sha256']
                or bounded_file(out/item['path'],16*1024*1024) != bounded_file(ROOT/'site/data'/name,16*1024*1024)):
            raise github.StoreConflict('Historical public artifact changed')
        expected.add(item['path'])
    if {p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()} != expected:
        raise github.StoreConflict('Unreviewed file in public upload tree')


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for k in ('runtime','config','out'): p.add_argument('--'+k,required=True)
    p.add_argument('--verify')
    p.add_argument('--identities-only',action='store_true')
    a=p.parse_args()
    try:
        export(a.runtime,a.config,a.out,a.verify,a.identities_only)
    except Exception:
        print('Pages export refused; no new publication.',file=sys.stderr)
        sys.exit(20)
