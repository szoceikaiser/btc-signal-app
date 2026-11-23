"""Focused offline checks with the reviewed loader and genuine local Git refs."""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import pickle
import runpy
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import urllib.parse
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT.parent
PINNED = AUDIT.parent/'signal-app-watch-43880114205-runtime'
WATCH = '.github/workflows/watch.yml'
CANARY = 'INJECTED-secret?token=test&provider=private'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loader():
    return runpy.run_path(str(ROOT/'tools/pinned_delivery_entry.py'))


def block_network():
    stack = ExitStack()
    for name in ('socket.create_connection', 'socket.socket.connect', 'socket.socket.connect_ex'):
        stack.enter_context(patch(name, side_effect=AssertionError('Unexpected real network')))
    stack.enter_context(patch.dict(os.environ, {'GIT_ALLOW_PROTOCOL': 'file',
        'TMP': str(AUDIT), 'TEMP': str(AUDIT), 'TMPDIR': str(AUDIT),
        'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_0': 'safe.directory',
        'GIT_CONFIG_VALUE_0': (PINNED/'core').as_posix(),
        'GIT_CONFIG_KEY_1': 'safe.directory', 'GIT_CONFIG_VALUE_1': (PINNED/'observer').as_posix()}))
    tempfile.tempdir = str(AUDIT)
    return stack


def install():
    loader()['install'](PINNED/'core', ROOT, sha(ROOT/'delivery-extension.json'))
    # Install places the pinned Core before the extension. Only fixtures absent
    # from the pinned strategy are sourced from the candidate.
    sys.path.extend([str(ROOT/'tools'), str(ROOT/'engine')])


def count(service):
    return {'GET': service.gets, 'business_attempts': service.business_attempts,
            'business_writes': service.business_writes, 'journal_puts': service.journal_puts,
            'sends': service.sends}


def mutation(mode, service, request):
    assert request.get_header('Authorization') == 'Bearer synthetic-store'
    data = json.loads(request.data)
    inp = data['variables']['input']
    assert 'createCommitOnBranch' in data['query']
    assert inp['branch'] == {'repositoryNameWithOwner': service.repo, 'branchName': service.d['fence_branch']}
    assert set(inp['fileChanges']) == {'additions'}
    addition, = inp['fileChanges']['additions']
    assert addition['path'] == actions.FENCE_PATH
    raw = base64.b64decode(addition['contents'], validate=True)
    assert json.loads(raw)['completion']['outcome'] == 'aborted'
    service.business_attempts += 1
    branch = service.d['fence_branch']
    current = service.head(branch)
    assert inp['expectedHeadOid'] == service.incident == current
    assert service.reservation()['writes']['fence']['status'] == 'reserved'
    if mode == 'crash_before':
        service.log()
        os._exit(71)
    if mode in ('commit_conflict', 'commit_conflict_sabotage'):
        old = record(service.fence_repo, current, actions.FENCE_PATH)
        current = commit_file(service.fence_repo, branch, actions.FENCE_PATH, old['body'], current)
        assert current != service.incident
        assert record(service.fence_repo, current, actions.FENCE_PATH)['blob_sha'] == old['blob_sha']
        if mode == 'commit_conflict':
            return service.response({'errors': [{'message': CANARY}]})
    assert current == inp['expectedHeadOid'] or mode == 'commit_conflict_sabotage'
    pin = commit_file(service.fence_repo, branch, actions.FENCE_PATH, raw, current)
    service.business_writes += 1
    if mode == 'crash_after':
        service.log()
        os._exit(72)
    if mode == 'lost_reply':
        raise TimeoutError(CANARY)
    return service.response({'data': {'createCommitOnBranch': {'commit': {'oid': pin}}}})


class EarlyService:
    def __init__(self, root):
        self.inner = Service(root)
        self.root = root
        self.mode = 'normal'
        self.gets = self.business_attempts = self.business_writes = self.journal_puts = self.sends = 0
        self.last_get = ''
        self.routes = []
        self.headers = {}
        self.bad_worker = False
        self.legacy_queue = False
        d = self.d
        previous_run = self.inner.fence['run']
        branch = d['fence_branch']
        before = self.head(branch)
        previous = {**self.inner.fence, 'phase': 'closed', 'write_id': 'prior-close',
            'completion': dict(stream=self.locate(self.env), get_before_close=17, put_before_close=3,
                request_bytes_before_close=5432, response_reserve_before_close=10000)}
        self.previous = commit_file(self.fence_repo, branch, actions.FENCE_PATH, canonical(previous).encode(), before)
        self.slot = schedule.slot_at('watch', int(previous_run['expected_start_ms']) + 900000)
        run = dict(number=1, id='11', attempt='1', workflow=WATCH, kind='watch',
                   expected_start_ms=str(self.slot), deadline_utc_ms=schedule.deadline('watch', self.slot))
        opened = {**previous, 'phase': 'open', 'run': run, 'write_id': 'open-new-watch',
                  'cursors': {**previous['cursors'], WATCH: {'number': 1, 'id': '11'}}, 'completion': None}
        self.incident = commit_file(self.fence_repo, branch, actions.FENCE_PATH, canonical(opened).encode(), self.previous)
        self.original = record(self.source, self.head(d['store_branch']), github.STORE_PATH)
        self.now = run['deadline_utc_ms'] + 1000
        self.raw_workflow = (ROOT/WATCH).read_bytes()
        self.policy['entry_workflows'][WATCH] = hashlib.sha256(self.raw_workflow).hexdigest()
        repo = {'full_name': d['code_repository']}
        self.meta = dict(id=11, run_number=1, run_attempt=1, path=WATCH, head_sha=d['code_sha'],
            repository=repo, head_repository=repo, head_branch='synthetic', status='completed',
            conclusion='failure', event='workflow_dispatch', display_title='btc-v2:watch:created',
            created_at=iso(self.slot+1000), updated_at=iso(self.slot+8000))
        self.jobs = {'total_count': 1, 'jobs': [dict(id=12, name='delivery', run_id=11, run_attempt=1,
            head_sha=d['code_sha'], status='completed', conclusion='failure',
            completed_at=iso(self.slot+5000), labels=['ubuntu-24.04'])]}
        self.worker_attempt('1')

    def __getattr__(self, key):
        inner = self.__dict__.get('inner')
        if inner is None:
            raise AttributeError(key)
        return getattr(inner, key)

    @property
    def incident_path(self):
        return 'recovery/incidents/' + self.incident + '.json'

    def reservation(self):
        head = git(self.jrepo, 'rev-parse', 'refs/heads/recovery-journal-live').decode().strip()
        return json.loads(record(self.jrepo, head, self.incident_path)['body'])

    def log(self):
        (self.root/'counts.json').write_text(json.dumps(count(self)), encoding='ascii')

    def open(self, request, timeout):
        u = urllib.parse.urlsplit(request.full_url)
        assert u.scheme == 'https' and u.netloc == 'api.github.com' and 0 < timeout <= 3
        method = request.get_method()
        if method == 'POST':
            assert u.path == '/graphql'
            return mutation(self.mode, self, request)
        if method == 'PUT':
            assert u.path.endswith('/contents/'+self.incident_path)
            self.journal_puts += 1
        else:
            assert method == 'GET'
            self.gets += 1
            self.last_get = u.path
            self.routes.append(u.path+'?'+u.query)
        if u.path.endswith('/actions/runs/900/attempts/'+self.environment['GITHUB_RUN_ATTEMPT']+'/jobs'):
            return self.response({'total_count': 1, 'jobs': [self.own_job]})
        if u.path.startswith('/repos/'+self.d['code_repository']+'/compare/'):
            base, entry = u.path.rsplit('/', 1)[1].split('...')
            assert base == self.d['code_sha'] and entry in (self.own['head_sha'], self.meta['head_sha'])
            return self.response({'base_commit': {'sha': base}, 'merge_base_commit': {'sha': base}, 'status': 'ahead'})
        if u.path.endswith('/actions/runs/11'):
            return self.response(self.meta)
        if u.path.endswith('/actions/runs/11/attempts/1/jobs'):
            response = self.response(self.jobs)
            response.headers.update(self.headers)
            return response
        if u.path.endswith('/contents/' + WATCH):
            raw = self.raw_workflow
            return self.response(dict(type='file', encoding='base64',
                content=base64.b64encode(raw).decode(), sha=blob(raw)))
        if u.path.endswith('/actions/runs') and (self.bad_worker or self.legacy_queue):
            status = urllib.parse.parse_qs(u.query)['status'][0]
            if status == 'queued':
                workflow = WATCH if self.bad_worker else '.github/workflows/freshness.yml'
                extra = dict(id=43799577702, path=workflow, status='queued', head_branch='synthetic',
                             run_attempt=1, repository={'full_name': self.d['code_repository']})
                return self.response({'total_count': 2, 'workflow_runs': [self.own, extra]})
        return self.inner.open(request, timeout)

    def descendants(self, distinct=False):
        assert self.head(self.d['fence_branch']) == self.incident
        self.inner.published_head = 'b'*40
        self.environment['GITHUB_SHA'] = self.own['head_sha'] = self.inner.published_head
        self.meta['head_sha'] = self.jobs['jobs'][0]['head_sha'] = 'c'*40 if distinct else self.inner.published_head

    def worker_attempt(self, attempt):
        self.environment['GITHUB_RUN_ATTEMPT'] = attempt
        self.own['run_attempt'] = int(attempt)
        self.own_job = dict(id=901, name='recover', run_id=900, run_attempt=int(attempt),
            head_sha=self.own['head_sha'], status='in_progress', labels=['ubuntu-24.04'])

    def client(self):
        diagnostic = writer['Diagnostic']()
        if getattr(self, 'through_entry', False):
            def probe(network, bind, run):
                client = network(self.policy, 'synthetic-store', 'synthetic-metadata')
                client.open_request = client.metadata.open_request = self.open
                client.clock = lambda: self.now
                return client, bind(client, self.environment)
            client, identity = writer['execute'](PINNED/'core', ROOT, sha(ROOT/'tools/pinned_delivery_entry.py'),
                sha(ROOT/'delivery-extension.json'), diagnostic, probe=probe)
        else:
            client = recovery.Network(self.policy, 'synthetic-store', 'synthetic-metadata', self.open, lambda: self.now)
            identity = recovery.bind_self(client, self.environment)
        self.identity = identity
        self.last_client = client
        client.diagnostic = diagnostic
        return client, identity

    def run(self, attempt='1'):
        self.worker_attempt(attempt)
        client, identity = self.client()
        def refuse_send(*args, **kwargs):
            self.sends += 1
            raise AssertionError('Recovery attempted delivery')
        try:
            with patch('telegram_notify.deliver_telegram', side_effect=refuse_send):
                return writer['run'](client, identity)
        finally:
            self.diagnostic = client.diagnostic.phase

    def rewrite_synthetic_input_fence(self, previous, opened):
        branch = self.d['fence_branch']
        parent = git(self.fence_repo, 'rev-parse', self.previous+'^').decode().strip()
        git(self.fence_repo, 'update-ref', 'refs/heads/'+branch, parent, self.incident)
        self.previous = commit_file(self.fence_repo, branch, actions.FENCE_PATH, canonical(previous).encode(), parent)
        self.incident = commit_file(self.fence_repo, branch, actions.FENCE_PATH, canonical(opened).encode(), self.previous)


def historical_fixture_bytes(name):
    # The pinned Core is shallow. Build an explicitly synthetic legacy source
    # for the existing migration fixture without addressing its absent P1 blob.
    from production_contract import effective_config
    from test_production_migration import ROOT as FIXTURE_ROOT
    target = json.loads((FIXTURE_ROOT/'site/data/config.json').read_bytes())
    config = {**effective_config(target), 'muster_cvd': 'alt'}
    state = {'pos_state': 'FLAT', 'config': config, 'last_signal_ts': 1791043200000}
    fixtures = {'state.json': state, 'config.json': config,
                'signals.json': {'signals': []}, 'oi_history.json': []}
    return canonical(fixtures[name]).encode()


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


class Offline(unittest.TestCase):
    def service(self, root=None):
        if root is None:
            root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=AUDIT)))
        return EarlyService(root)

    def measure(self, label, service, expected):
        measured = count(service)
        assert measured == {'GET': measured['GET'], 'business_attempts': expected[0],
                            'business_writes': expected[1], 'journal_puts': expected[2], 'sends': 0}, measured
        assert measured['GET'] > 0
        print(label, json.dumps(measured, sort_keys=True))

    def test_descendant_replay(self):
        for distinct in (False, True):
            with self.subTest(distinct=distinct):
                s = self.service()
                s.descendants(distinct)
                assert s.d['code_sha'] != s.own['head_sha']
                assert (s.meta['head_sha'] != s.own['head_sha']) == distinct
                assert s.run()['outcome'] == 'aborted'
                self.measure('descendant_first_'+str(distinct), s, (1, 1, 4))
                assert s.gets == 79 and s.last_client.bootstrap == 32
                assert s.reservation()['plan']['review']['previous_completion']['stream']['commit_sha'] == s.original['commit_sha']
                totals = count(s)
                s.routes = []
                assert s.run('2')['phase'] == 'already-confirmed-no-write'
                assert s.identity == dict(run_id='900', attempt='2', job_id='901', entry='b'*40)
                assert s.diagnostic == 'head_recheck' and s.last_client.bootstrap == 32
                assert s.gets-totals['GET'] == 32
                assert all(count(s)[k] == totals[k] for k in totals if k != 'GET')
                code = '/repos/'+s.d['code_repository']
                for entry, workflow in ((s.own['head_sha'], '.github/workflows/recovery.yml'), (s.meta['head_sha'], WATCH)):
                    assert code+'/contents/'+workflow+'?ref='+entry in s.routes
                    assert code+'/compare/'+s.d['code_sha']+'...'+entry+'?per_page=1' in s.routes
                assert s.routes[-2:] == ['/repos/'+s.repo+'/git/ref/heads/'+s.d['fence_branch']+'?',
                                        '/repos/'+s.repo+'/git/ref/heads/'+s.d['store_branch']+'?']
                print('descendant_replay', distinct, 'GET', s.gets-totals['GET'], 'bootstrap', s.last_client.bootstrap, 'identity', s.identity)
                # Sabotage the exact reuse decision, leaving every guard in place.
                source = (ROOT/'ops/continuous/recovery_writer.py').read_text()
                needle = "reusable = plan and plan['review'].get('previous_completion') == completion_evidence"
                assert source.count(needle) == 1
                namespace = {'__name__': 'sabotaged_offline_writer'}
                exec(compile(source.replace(needle, 'reusable = False'), '<offline-sabotage>', 'exec'), namespace)
                before = count(s)
                with patch.dict(writer, {'run': namespace['run']}):
                    with self.assertRaises(ValueError):
                        s.run('2')
                assert s.last_client.bootstrap == 33 and s.gets-before['GET'] == 32
                assert s.diagnostic == 'head_recheck'
                assert all(count(s)[k] == before[k] for k in before if k != 'GET')
                print('reuse_sabotage_caught', distinct, 'blocked before transport GET 33 in', s.diagnostic)
                original_read = writer['run'].__globals__['read_incident']
                def mismatched_completion(client, journal_head, path):
                    row = original_read(client, journal_head, path)
                    if row:
                        row = deepcopy(row)
                        row[1]['plan']['review']['previous_completion']['stream']['commit_sha'] = 'd'*40
                    return row
                before = count(s)
                with patch.dict(writer['run'].__globals__, {'read_incident': mismatched_completion}):
                    with self.assertRaises(ValueError):
                        s.run('2')
                assert s.last_client.bootstrap == 33 and s.diagnostic == 'head_recheck'
                assert all(count(s)[k] == before[k] for k in before if k != 'GET')
                print('different_completion_stream_refused', distinct)


    def test_resuming_worker_binding_entry(self):
        s = self.service()
        s.descendants(True)
        s.worker_attempt('1')
        # This is the authenticated writer entry's observed_bind, without replacing
        # bind_self or manufacturing the identity passed to run.
        def probe(network, bind, run):
            assert run is writer['run'] or run.__code__.co_filename.endswith('recovery_writer.py')
            client = network(s.policy, 'synthetic-store', 'synthetic-metadata')
            client.open_request = client.metadata.open_request = s.open
            client.clock = lambda: s.now
            return client, bind(client, s.environment)
        diagnostic = writer['Diagnostic']()
        client, identity = writer['execute'](PINNED/'core', ROOT, sha(ROOT/'tools/pinned_delivery_entry.py'),
            sha(ROOT/'delivery-extension.json'), diagnostic, probe=probe)
        assert identity == dict(run_id='900', attempt='1', job_id='901', entry='b'*40)
        assert client.bootstrap == 4 and diagnostic.phase == 'own_job'
        good = deepcopy(s.own_job)
        for key, value in (('run_id', 902), ('run_attempt', 2), ('head_sha', 'c'*40), ('name', 'foreign')):
            s.own_job = {**good, key: value}
            with self.assertRaises(ValueError):
                writer['execute'](PINNED/'core', ROOT, sha(ROOT/'tools/pinned_delivery_entry.py'),
                    sha(ROOT/'delivery-extension.json'), writer['Diagnostic'](), probe=probe)
        s.own_job = good
        assert s.business_attempts == s.journal_puts == 0
        print('real_entry_worker_binding exact identity accepted; four job identity counterprobes refused')

    def test_close_once_and_consumers(self):
        s = self.service()
        s.legacy_queue = True
        old = json.loads(record(s.fence_repo, s.incident, actions.FENCE_PATH)['body'])
        assert old['phase'] == 'open' and old['run']['id'] == '11'
        assert s.env['snapshot']['control']['owner'] is None
        result = s.run()
        assert result['outcome'] == 'aborted'
        self.measure('aborted', s, (1, 1, 4))
        fpin = s.head(s.d['fence_branch'])
        closed_record = record(s.fence_repo, fpin, actions.FENCE_PATH)
        closed = json.loads(closed_record['body'])
        assert closed['run'] == old['run'] and closed['cursors'] == old['cursors']
        assert record(s.source, s.head(s.d['store_branch']), github.STORE_PATH) == s.original
        assert s.reservation()['writes']['fence']['status'] == 'confirmed'
        totals = count(s)
        assert s.run('2')['phase'] == 'already-confirmed-no-write'
        assert all(count(s)[k] == totals[k] for k in totals if k != 'GET')
        print('confirmed replay added GET', s.gets - totals['GET'])
        c, _ = s.client()
        policy = dict(enabled=True, schema='p4-actions-monitor-v1', deployment=s.d)
        for m in (monitor, observer_monitor):
            observation = m.check(c, None, None, policy, s.now)
            assert observation['http_status'] == 503 and observation['diagnostic']['phase'] == 'fence'
        with self.assertRaisesRegex(ValueError, 'fresh successful regular run'):
            pages.observe(c, s.d, s.env['snapshot']['engine']['config'])

        # Real admission code. First prove that ancestry and prior bytes are consumed.
        successor = {**old['run'], 'id': '13', 'number': 2, 'expected_start_ms': str(s.slot+1800000)}
        operator = object.__new__(actions.ActionsClient)
        operator.journal = SimpleNamespace(binding={'repo': s.repo})
        operator.fence_branch = s.d['fence_branch']
        operator.admitted = False
        operator.read, operator.read_at, operator.parents = c.read, c.read_at, c.parents
        opened = []
        operator.fence_write = lambda _, value: opened.append(value)
        with self.assertRaises(github.StoreConflict):
            operator.acquire(s.d, {**successor, 'expected_start_ms': str(s.now)})
        assert not opened
        with patch.object(operator, 'parents', side_effect=lambda repo, pin:
                          ['a'*40] if pin == s.incident else c.parents(repo, pin)):
            with self.assertRaises(ValueError):
                operator.acquire(s.d, successor)
        assert not opened
        fresh_client, _ = s.client()
        operator.read, operator.read_at, operator.parents = fresh_client.read, fresh_client.read_at, fresh_client.parents
        operator.acquire(s.d, successor)
        assert len(opened) == 1 and opened[0]['completion'] is None and opened[0]['run'] == successor

        # The backup producer and an independent blocked restore must check the actual Git lineage.
        fcount = int(git(s.fence_repo, 'rev-list', '--count', fpin))
        sp = s.original
        pins = dict(stream=dict(commit_sha=sp['commit_sha'], revision=s.env['revision'],
                               blob_sha=sp['blob_sha'], snapshot_digest=s.env['body_digest']),
                    fence=dict(commit_sha=fpin, revision=fcount-1, blob_sha=closed_record['blob_sha'],
                               body_sha256=digest(closed)))
        plan = dict(stream_source=str(s.source), fence_source=str(s.fence_repo), deployment=s.d,
                    identity=s.provider.fixture['identity'], migration=s.provider.fixture['migration'],
                    pins=pins, out=str(s.root/'package'))
        output = pair.append(plan)
        restored = pair.restore(s.root/'package', output['manifest'], s.root/'restore', pins)
        assert restored['restore_blocked_verified'] and restored['enabled'] is False
        assert json.loads((s.root/'restore/actions-fence.original.json').read_bytes()) == closed
        proof = deepcopy(closed)
        proof['completion']['recovery']['previous_fence_sha256'] = '0' * 64
        with pair.b.batch(s.fence_repo, pair.b.Budget()) as read:
            previous = pair.watch_abort_history(read, [s.incident], proof, s.d)
        with self.assertRaises(ValueError):
            pair.crosscheck(proof, s.source, sp['commit_sha'], plan['identity'], s.d, pair.b.Budget(), previous)

    def test_full_followup_watch(self):
        from test_actions_delivery import BranchHTTP, fixture
        import offline_test_fixtures

        s = self.service()
        result = s.run()
        assert result['outcome'] == 'aborted'
        d = s.d
        fpin = result['fence_commit']
        sprior = s.original
        history = {pin: {actions.FENCE_PATH: record(s.fence_repo, pin, actions.FENCE_PATH)['body'].decode()}
                   for pin in (fpin, s.incident, s.previous)}
        history[sprior['commit_sha']] = {github.STORE_PATH: sprior['body'].decode()}
        parents = {fpin: [s.incident], s.incident: [s.previous]}
        http = BranchHTTP(state={'seq': 100, 'heads': {d['store_branch']: sprior['commit_sha'],
            d['fence_branch']: fpin}, 'parents': parents, 'history': history})
        http.access = s.policy['public_access']
        http.rules, http.rulesets = s.provider.rules, s.provider.rulesets
        slot = s.slot+1800000
        now = slot+1000
        candle = now//14400000*14400000
        candles = [[opened, '100', '101', '99', '100', '1', opened+14400000-1]
                   for opened in range(candle-40*14400000, candle+1, 14400000)]

        from test_betriebsabschluss import metadata
        base_reply = offline_test_fixtures.branch_reply
        def respond(provider, request, timeout):
            if '/actions/runs/13' not in request.full_url:
                return base_reply(provider, request, timeout)
            provider.seen.append(('GET', request.full_url, timeout))
            return io.BytesIO(canonical(metadata('watch', slot, '13', 2)).encode())

        with fixture() as (root, data, path, template, _), ExitStack() as stack:
            runtime = {**template, **d, 'public_access': http.access, 'entry_workflows': {}}
            path.write_bytes(canonical(runtime).encode())
            (data/'config.json').write_bytes(canonical(s.env['snapshot']['engine']['config']).encode())
            environment = dict(BTC_DELIVERY_GITHUB_REPO=s.repo, BTC_DELIVERY_GITHUB_BRANCH=d['store_branch'],
                BTC_DELIVERY_FENCE_BRANCH=d['fence_branch'], BTC_DELIVERY_STORE_ID=d['store_id'],
                BTC_DELIVERY_CODE_SHA=d['code_sha'], GITHUB_SHA=d['code_sha'],
                BTC_DELIVERY_BOT_IDENTITY=d['bot_identity'], BTC_DELIVERY_WORKFLOW=WATCH,
                GITHUB_WORKFLOW_REF=d['code_repository']+'/'+WATCH+'@'+d['code_ref'],
                GITHUB_RUN_ID='13', BTC_DELIVERY_RUN_ID='13', GITHUB_RUN_NUMBER='2')
            stack.enter_context(patch.dict(os.environ, environment))
            stack.enter_context(patch.object(offline_test_fixtures, 'branch_reply', respond))
            stack.enter_context(patch.object(actions.ActionsClient, 'open_request', side_effect=http.open))
            stack.enter_context(patch.object(entry.public, 'credential'))  # Synthetic credential review only.
            stack.enter_context(patch.object(entry.time, 'time', return_value=now/1000))
            send = stack.enter_context(patch.object(entry.runner.tg, 'deliver_telegram',
                                                   side_effect=AssertionError('Live send forbidden')))
            get_data = stack.enter_context(patch.object(entry.runner.main, '_get_json', return_value=candles))

            original_parents = deepcopy(http.state['parents'])
            http.state['parents'][s.incident] = ['e'*40]
            try:
                with self.assertRaisesRegex(ValueError, 'Recovery evidence refused'):
                    entry.run_runtime(path, 'watch', data)
                assert http.puts == 0 and get_data.call_count == 0 and send.call_count == 0
            finally:
                http.state['parents'] = original_parents
            http.seen.clear()
            outcome = entry.run_runtime(path, 'watch', data)
            current_pin = http.state['heads'][d['fence_branch']]
            final = json.loads(http.state['history'][current_pin][actions.FENCE_PATH])
            stream_pin = http.state['heads'][d['store_branch']]
            stream = json.loads(http.state['history'][stream_pin][github.STORE_PATH])
            assert final['phase'] == 'closed' and final['run']['id'] == '13'
            assert final['completion']['stream']['commit_sha'] == stream_pin
            assert 'recovery' not in final['completion']
            assert stream['snapshot']['control']['health']['successful_runs']['watch']['run']['run_id'] == '13'
            assert stream['snapshot']['engine'] == s.env['snapshot']['engine']
            assert get_data.call_count == 1 and send.call_count == 0
            print('regular_watch', 'GET', outcome['get'], 'PUT', outcome['put'], 'sends', send.call_count)

    def test_healthy_no_write(self):
        s = self.service()
        branch = s.d['fence_branch']
        git(s.fence_repo, 'update-ref', 'refs/heads/'+branch, s.previous, s.incident)
        assert actions.parse_fence(record(s.fence_repo, s.previous, actions.FENCE_PATH), s.d)['phase'] == 'closed'
        assert s.run()['phase'] == 'no-open-incident'
        self.measure('healthy', s, (0, 0, 0))
        assert git(s.jrepo, 'rev-parse', 'refs/heads/recovery-journal-live').decode().strip() == s.seed
        with patch.dict(writer['run'].__globals__, {'read_incident': lambda *_: self.fail('journal path reached')}):
            # Sabotage the healthy observation to an open fence and demonstrate that
            # this trips the checkpoint before touching the journal.
            with patch.object(actions, 'parse_fence', side_effect=lambda rec, d:
                    {**json.loads(rec['body']), 'phase': 'open'}):
                with self.assertRaisesRegex(AssertionError, 'journal path reached'):
                    s.run('2')

    def test_conflict_and_lost_reply(self):
        for mode in ('commit_conflict', 'commit_conflict_sabotage', 'lost_reply'):
            with self.subTest(mode=mode):
                s = self.service()
                s.mode = mode
                if mode == 'lost_reply':
                    assert s.run()['outcome'] == 'aborted'
                    self.measure(mode, s, (1, 1, 4))
                else:
                    with self.assertRaises(ValueError):
                        s.run()
                    self.measure(mode, s, (1, int(mode.endswith('sabotage')), 3))
                    assert s.reservation()['writes']['fence']['status'] == 'reserved'
                    if mode == 'commit_conflict':
                        with self.assertRaises(ValueError):
                            s.run('2')
                        assert s.business_attempts == 1

    def test_competing_recovery_reservation(self):
        s = self.service()
        original = recovery.ledger.Journal.reserve_write
        competing = []
        def contender(journal, key, old, body):
            reserved = original(journal, key, old, body)
            assert reserved['status'] == 'reserved'
            with self.assertRaisesRegex(ValueError, 'Persistent recovery reservation refused'):
                original(journal, key, old, body)
            competing.append(key)
            return reserved
        with patch.object(recovery.ledger.Journal, 'reserve_write', contender):
            assert s.run()['outcome'] == 'aborted'
        assert competing == ['fence']
        self.measure('competing_recovery', s, (1, 1, 4))
        assert list(s.reservation()['writes']) == ['fence']

    def test_rejections(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=AUDIT)))
        for case in ('owner','moved_stream','wrong_parent','sending','uncertain','page_link','job_count',
                     'running_job','wrong_branch','wrong_code','wrong_slot','deadline','active_writer','success','completion_index'):
            with self.subTest(case=case):
                folder = root/case
                folder.mkdir()
                s = self.service(folder)
                if case in ('owner','moved_stream','sending','uncertain','completion_index'):
                    env = deepcopy(s.env)
                    control = env['snapshot']['control']
                    if case == 'owner':
                        control['owner'] = dict(repository=s.repo, run_id='88', run_attempt='1', nonce='synthetic')
                    elif case == 'completion_index':
                        control['health']['completed_runs'] = {'watch': {str(s.slot): {
                            'run': {'run_id': '11'}, 'completion': s.locate(env)}}}
                    elif case != 'moved_stream':
                        env['snapshot']['engine']['_delivery']['messages'][-1]['status'] = case
                    env = s.inner.append_stream(env)
                    assert s.head(s.d['store_branch']) != s.original['commit_sha']
                    if case in ('sending', 'uncertain', 'completion_index'):
                        # Keep stream/fence binding correct so the receipt and
                        # completion checks can independently refuse the case.
                        previous = json.loads(record(s.fence_repo, s.previous, actions.FENCE_PATH)['body'])
                        opened = json.loads(record(s.fence_repo, s.incident, actions.FENCE_PATH)['body'])
                        previous['completion']['stream'] = s.locate(env)
                        s.rewrite_synthetic_input_fence(previous, opened)
                        if case == 'completion_index':
                            assert env['snapshot']['control']['health']['completed_runs']['watch'][str(s.slot)]['run']['run_id'] == '11'
                        else:
                            with self.assertRaises(ValueError):
                                recovery.safe.receipts(env['snapshot'])
                elif case == 'wrong_parent':
                    previous = json.loads(record(s.fence_repo, s.previous, actions.FENCE_PATH)['body'])
                    opened = json.loads(record(s.fence_repo, s.incident, actions.FENCE_PATH)['body'])
                    previous['write_id'] = opened['write_id']
                    s.rewrite_synthetic_input_fence(previous, opened)
                elif case == 'page_link':
                    s.headers['Link'] = '<https://api.github.com/synthetic?page=2>; rel="next"'
                elif case == 'job_count':
                    s.jobs['total_count'] = 2
                elif case == 'running_job':
                    s.jobs['jobs'][0]['status'] = 'in_progress'
                elif case == 'wrong_branch':
                    s.meta['head_branch'] = 'foreign'
                elif case == 'wrong_code':
                    s.raw_workflow += b'altered byte'
                elif case == 'wrong_slot':
                    s.meta['display_title'] = 'btc-v2:watch:'+str(s.slot-900000)
                elif case == 'deadline':
                    s.now = s.slot + 899999
                elif case == 'active_writer':
                    s.bad_worker = True
                elif case == 'success':
                    s.meta['conclusion'] = 'success'
                with self.assertRaises((ValueError, github.StoreError)):
                    s.run()
                assert s.diagnostic == ('early_watch_history' if case in
                    ('moved_stream','wrong_parent','sending','uncertain','deadline','completion_index') else 'admission')
                self.measure('refused_'+case, s, (0, 0, 0))
                if case == 'page_link':
                    # Sabotage only the metadata-link propagation. Same metadata
                    # would be incorrectly accepted if an unseen page were ignored.
                    original = recovery.Network._request
                    def omit_link(client, method, route, payload=None):
                        reply = original(client, method, route, payload)
                        client._response_link = ''
                        return reply
                    with patch.object(recovery.Network, '_request', omit_link):
                        assert s.run('2')['outcome'] == 'aborted'

    def test_process_restarts(self):
        for mode, first_code, saved in (('crash_before',71,False), ('crash_after',72,True)):
            with self.subTest(mode=mode):
                s = self.service()
                s.descendants(True)
                (s.root/'fixture.pkl').write_bytes(pickle.dumps(s))
                def child(operation):
                    return subprocess.run([sys.executable,'-I','-B',__file__,'--child',str(s.root),operation],
                                          capture_output=True, timeout=45)
                first = child(mode)
                assert first.returncode == first_code, (first.returncode, first.stdout, first.stderr)
                reserved = s.reservation()['writes']['fence']
                assert reserved['status'] == 'reserved'
                assert json.loads((s.root/'counts.json').read_bytes())['business_writes'] == int(saved)
                print(mode, (s.root/'counts.json').read_text())
                if saved:
                    same = child('same_worker')
                    assert same.returncode == 0, (same.stdout, same.stderr)
                    duplicate = json.loads(same.stdout)
                    assert duplicate['result'] == 'blocked' and duplicate['phase'] == 'journal_acquire'
                    assert duplicate['identity']['attempt'] == '1'
                    assert duplicate['counts']['business_attempts'] == duplicate['counts']['journal_puts'] == 0
                    assert s.reservation()['writes']['fence']['status'] == 'reserved'
                    print('same_worker_refused', json.dumps(duplicate, sort_keys=True))
                saved_pin = s.head(s.d['fence_branch'])
                replay = child('restart')
                assert s.head(s.d['fence_branch']) == saved_pin
                assert replay.returncode == 0, (replay.stdout, replay.stderr)
                second = json.loads(replay.stdout)
                assert second['identity'] == dict(run_id='900', attempt='2', job_id='901', entry='b'*40)
                assert second['counts']['business_attempts'] == 0
                assert second['counts']['journal_puts'] == (2 if saved else 0)
                assert second['result'] == ('already-confirmed-no-write' if saved else 'blocked')
                print(mode + '_restart', json.dumps(second, sort_keys=True))
                assert (s.reservation()['writes']['fence']['status'] == 'confirmed') == saved
                if not saved:
                    journal_pin = git(s.jrepo, 'rev-parse', 'refs/heads/recovery-journal-live').decode().strip()
                    assert journal_pin != s.seed
                    # Sabotage only the durable reference in the synthetic repo.
                    # With the reservation lost a new process would submit again.
                    git(s.jrepo, 'update-ref', 'refs/heads/recovery-journal-live', s.seed, journal_pin)
                    try:
                        retry = child('restart')
                        assert retry.returncode == 0, (retry.stdout, retry.stderr)
                        assert json.loads(retry.stdout)['counts']['business_attempts'] == 1
                    finally:
                        latest = git(s.jrepo, 'rev-parse', 'refs/heads/recovery-journal-live').decode().strip()
                        git(s.jrepo, 'update-ref', 'refs/heads/recovery-journal-live', journal_pin, latest)

    def test_diagnostics_real_loader(self):
        from test_actions_delivery import fixture
        for fault, phase, reason in (
            ('before_fence','watch_runtime_binding','invalid_json'),
            ('fence','watch_fence_acquire','state_conflict'),
            ('before_store','watch_before_store','runtime_failed'),
            ('store_read','watch_store_read','store_unavailable'),
            ('owner','watch_store_acquire','state_conflict'),
            ('owned','watch_store_owned','runtime_failed'),
        ):
            with self.subTest(fault=fault), fixture() as (_, data, path, _, http), ExitStack() as stack:
                reached = []
                def crash(exc):
                    reached.append(fault)
                    print(CANARY)
                    print(CANARY, file=sys.stderr)
                    raise exc(CANARY)
                workflow_ref = os.environ['GITHUB_WORKFLOW_REF'].replace('/signal.yml@','/watch.yml@')
                stack.enter_context(patch.dict(os.environ, {'BTC_DELIVERY_WORKFLOW': WATCH,
                                                            'GITHUB_WORKFLOW_REF': workflow_ref}))
                import offline_test_fixtures
                base_reply = offline_test_fixtures.branch_reply
                def watch_reply(service, request, timeout):
                    reply = base_reply(service, request, timeout)
                    if '/actions/runs/' in request.full_url:
                        metadata = json.load(reply)
                        metadata.update(created_at=iso(1791101280500), display_title='btc-v2:watch:created')
                        return io.BytesIO(canonical(metadata).encode())
                    return reply
                stack.enter_context(patch.object(offline_test_fixtures, 'branch_reply', watch_reply))
                stack.enter_context(patch.object(entry.time, 'time', return_value=1791101281))
                if fault == 'before_fence':
                    path.write_text(CANARY, encoding='ascii')
                    reached.append(fault)
                elif fault in ('fence','owner'):
                    http.mode = 'cas'
                    http.selected_path = actions.FENCE_PATH if fault == 'fence' else github.STORE_PATH
                elif fault == 'before_store':
                    stack.enter_context(patch.object(entry.runner, 'run_checked',
                                                    side_effect=lambda *_: crash(RuntimeError)))
                elif fault == 'store_read':
                    real_read = github.GitHubContentsClient.read
                    def read(client, repo, branch, file=github.STORE_PATH):
                        if file == github.STORE_PATH:
                            crash(github.StoreUnavailable)
                        return real_read(client, repo, branch, file)
                    stack.enter_context(patch.object(github.GitHubContentsClient, 'read', read))
                else:
                    stack.enter_context(patch.object(entry.runner.main, '_get_json',
                                                    side_effect=lambda *_: crash(RuntimeError)))
                namespace = loader()
                # Load real overlay once at program initialization. Retain the same
                # module objects for fixture seams on the second CLI invocation.
                stack.enter_context(patch.dict(namespace['main'].__globals__, {'install': lambda *_: entry}))
                argv = ['pinned_delivery_entry.py', '--core', str(PINNED/'core'), '--extension', str(ROOT),
                        '--manifest-sha256', sha(ROOT/'delivery-extension.json'), '--kind', 'watch',
                        '--runtime', str(path), '--data-dir', str(data)]
                stack.enter_context(patch.object(sys, 'argv', argv))
                send = stack.enter_context(patch.object(entry.runner.tg, 'deliver_telegram',
                                                      side_effect=AssertionError('Send forbidden')))
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    rc = namespace['main']()
                if fault in ('fence','owner'):
                    assert http.puts == (1 if fault == 'fence' else 2), http.seen
                else:
                    assert reached == [fault], (err.getvalue(), http.seen)
                expected = 'delivery phase='+phase+' reason='+reason+'\n'
                assert rc == 20 and out.getvalue() == '' and err.getvalue() == expected, (rc,out.getvalue(),err.getvalue())
                assert send.call_count == 0
                assert CANARY not in out.getvalue() + err.getvalue()
                good_gets = sum(request[0] == 'GET' for request in http.seen)
                good_puts = http.puts
                if fault == 'before_store':
                    # Targeted secret-filter sabotage on the same failure route.
                    with patch.dict(namespace['main'].__globals__, {'watch_error': lambda exc: str(exc)}):
                        # Reuse the seed fence snapshot so the same branch is reached.
                        http.state['heads']['actions-fence'] = '0'*39+'2'
                        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as exposed:
                            assert namespace['main']() == 20
                        assert CANARY in exposed.getvalue()
                print('diagnosis', fault, phase, reason, 'GET', good_gets,
                      'PUT', good_puts, 'sends', send.call_count)

    def test_historical_marker_consumers(self):
        import test_watch_abort as historical
        import watch_abort as marker
        import watch_abort_once
        historical.a, historical.w, historical.once = actions, marker, watch_abort_once
        historical.canonical, historical.digest = canonical, digest
        historical.b = pair.b
        old = historical.IncidentPaths()
        self.addCleanup(old.doCleanups)
        old.setUp()
        d = old.d
        provider = old.provider
        opened = provider.read_at(marker.REPOSITORY, marker.FENCE, actions.FENCE_PATH)
        prior = provider.read_at(marker.REPOSITORY, marker.PREVIOUS, actions.FENCE_PATH)
        stream = provider.read_at(marker.REPOSITORY, marker.STREAM)
        closed = marker.candidate(json.loads(opened['body']), json.loads(prior['body']), stream, historical.CONFIRMED)
        assert closed['completion']['watch_abort']['schema'] == marker.SCHEMA
        pin = historical.write(old.fence, watch_abort_once.REF, actions.FENCE_PATH, canonical(closed).encode())
        assert actions.parse_fence(provider.read_at(marker.REPOSITORY, pin, actions.FENCE_PATH), d) == closed
        c, run, writes = old.followup(historical.CONFIRMED + 1)
        c.admitted = False
        c.acquire(d, run)
        assert len(writes) == 1 and writes[0][0]['commit_sha'] == pin
        damaged = deepcopy(closed)
        damaged['completion']['watch_abort']['failed_run'] = '22'
        with self.assertRaises(github.StoreConflict):
            actions.parse_fence({'body': canonical(damaged).encode()}, d)
        print('historical_marker accepted and tampered marker rejected; historical operator was not invoked')

    def test_binding_rejects_tampered_overlay_bytes(self):
        target = ROOT/'engine/safe_recovery.py'
        original = target.read_bytes()
        manifest = sha(ROOT/'delivery-extension.json')
        assert hashlib.sha256(original).hexdigest() == json.loads((ROOT/'delivery-extension.json').read_bytes())['files']['engine/safe_recovery.py']
        try:
            target.write_bytes(original + b'\n# synthetic tampering\n')
            with self.assertRaisesRegex(ValueError, 'Extension bytes changed'):
                loader()['install'](PINNED/'core', ROOT, manifest)
        finally:
            target.write_bytes(original)


if __name__ == '__main__':
    with block_network():
        install()
        import actions_delivery as actions
        import actions_schedule as schedule
        import actions_freshness as monitor
        import github_delivery as github
        import github_recovery as recovery
        import p4_backup_pair as pair
        import produktion_actions_runner as entry
        import produktion_pages_export as pages
        from production_contract import canonical, digest
        from github_freshness import iso
        import test_continuous_operations
        import test_github_recovery
        from test_github_recovery import Service, commit_file, record
        def git(repo, *args):
            return pair.b.git(repo, pair.b.Budget(), *args)
        test_continuous_operations.git = test_github_recovery.git = git
        writer = runpy.run_path(str(ROOT/'ops/continuous/recovery_writer.py'))
        observer_monitor = SimpleNamespace(**runpy.run_path(str(ROOT/'ops/continuous/freshness/actions_freshness.py')))
        if sys.argv[1:2] == ['--child']:
            holder = Path(sys.argv[2])
            service = pickle.loads((holder/'fixture.pkl').read_bytes())
            mode = sys.argv[3]
            service.through_entry = True
            service.mode = 'normal' if mode in ('restart', 'same_worker') else mode
            try:
                result = service.run('2' if mode == 'restart' else '1')['phase']
            except (ValueError, github.StoreError):
                result = 'blocked'
            print(json.dumps({'result': result, 'counts': count(service), 'phase': service.diagnostic, 'identity': service.identity, 'bootstrap': service.last_client.bootstrap}))
        else:
            with patch('test_production_migration._blob', side_effect=historical_fixture_bytes):
                unittest.main(verbosity=2)

