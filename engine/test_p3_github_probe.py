"""Offline request/response, budget, grant and real process-loss counterexamples."""
import base64
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import p3_github_probe as p
import p3_probe_simulation as sim
import p3_probe_launcher as launcher


def rejects(error, fn):
    try: fn()
    except error: return
    raise AssertionError('Expected '+str(error))


def setup(td, phase='happy'):
    plan = sim.plan(td); api = sim.API(plan)
    previous = sim.execute(plan, api, td, 'bootstrap')
    previous = sim.execute(plan, api, td, 'activate', previous)
    ledger = p.Ledger(plan, Path(td)/(phase+'.jsonl'), phase, previous)
    client = p.Client(sim.boundary(plan, ledger, 'reader-secret-fixture', 'writer-secret-fixture', api.open))
    client.boundary.preflight()
    return plan, api, ledger, client


def test_full_wire_sequence_and_cumulative_budgets():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)/'rehearsal'; result = sim.rehearsal(out)
        assert result['passed'] and result['counts']['PUT'] == 28
        assert result['counts']['GET'] < 300 and result['real_requests'] == 0
        rows = p.Ledger.verify(out/'process-loss.jsonl', p.digest(result['plan']))
        for method in ('GET', 'PUT'):
            assert result['counts'][method] == sum(r['event'] == 'request' and r.get('method') == method for r in rows)
        for phase in ('happy', 'lost-after'):
            assert any(r['event'] == 'run_completion' and r['phase'] == phase for r in rows)
        assert rows[-1]['event'] == 'phase_halt'
        requests = [r for r in rows if r['event'] == 'request' and r['method'] == 'PUT']
        assert all(r['old_blob'] and r['write_id'] and r['revision'] and r['run']['nonce'] for r in requests)
        assert not any(r['event'] == 'phase_end' and r['phase'] == 'process-loss' for r in rows)


def test_default_import_missing_plan_and_no_credential_prompt_are_offline():
    script = "import sys, socket, urllib.request; sys.path.insert(0,'tools'); socket.socket.connect=lambda *a: (_ for _ in ()).throw(AssertionError('network')); urllib.request.urlopen=socket.socket.connect; import p3_github_probe as p; import getpass; getpass.getpass=lambda *a: (_ for _ in ()).throw(AssertionError('credential')); sys.argv=['probe']; p.main()"
    run = subprocess.run([sys.executable, '-c', script], cwd=ROOT, capture_output=True)
    assert run.returncode != 0 and b'Default is offline' in run.stderr
    assert b'AssertionError' not in run.stderr
    with tempfile.TemporaryDirectory() as td:
        draft = p.template(); Path(td, 'p.json').write_text(json.dumps(draft))
        with patch.object(p.getpass, 'getpass', side_effect=AssertionError('credential')):
            with patch.object(sys, 'argv', ['probe', '--real', '--plan', str(Path(td,'p.json'))]):
                rejects(ValueError, p.main)


def test_incomplete_foreign_production_or_unapproved_plans_fail():
    plan = sim.plan(); p.validate_plan(plan)
    for key, value in [('repository_id', None), ('repo', 'owner/../other'), ('branch', None),
                       ('path', '.github/workflows/run.yml'), ('store_id', 'production'),
                       ('stream_id', 'production'), ('credential_repository_ids', [900001, 99]),
                       ('reader_permissions', {'contents': 'read'}), ('source_head', 'f'*40),
                       ('expected_rules', [{'type': 'required_status_checks'}]), ('limits', {})]:
        bad = deepcopy(plan); bad[key] = value
        rejects(ValueError, lambda: p.validate_plan(bad))
    rejects(ValueError, lambda: p.authorize(plan, {}, 'activate', 'f'*64))
    rejects(ValueError, lambda: p.authorize(plan, {}, 'activate', p.digest(plan)))
    grant = {'schema': 'p3-human-grant-v2', 'plan_sha256': p.digest(plan), 'phase': 'activate',
        'approved_by': 'fixture-human', 'human_authorization': False, 'expires_utc': '2099-01-01T00:00:00Z',
        'approval_evidence_sha256': 'a'*64, 'review_sha256': None}
    rejects(ValueError, lambda: p.authorize(plan, grant, 'activate', p.digest(plan)))


def test_preflight_private_id_actions_pages_rules_and_insufficient_rights_stop_before_put():
    for tail, value in [('', {'id': 999, 'private': True}), ('/actions/permissions', {'enabled': True}),
                        ('/pages', {'status': 'built'}), ('/rules/branches/p3-synthetic-only', [{'type': 'update'}]),
                        ('/rulesets', [{'enforcement': 'active'}]), ('/branches', [{'name': 'main', 'protected': False}])]:
        with tempfile.TemporaryDirectory() as td:
            plan = sim.plan(td); api = sim.API(plan); api.override[tail] = value
            ledger = p.Ledger(plan, Path(td)/'bootstrap.jsonl', 'bootstrap')
            client = p.Client(sim.boundary(plan, ledger, 'fixture', 'fixture', api.open))
            rejects(ValueError, client.boundary.preflight)
            assert ledger.counts['PUT'] == 0 and not client.boundary.allowed
            ledger.close()
    with tempfile.TemporaryDirectory() as td:
        plan = sim.plan(td); api = sim.API(plan)
        def denied(req, timeout): api.error(req, 403)
        ledger = p.Ledger(plan, Path(td)/'bootstrap.jsonl', 'bootstrap')
        client = p.Client(sim.boundary(plan, ledger, 'fixture', 'fixture', denied))
        rejects(p.HTTPStatus, client.boundary.preflight)
        assert not client.boundary.allowed; ledger.close()


def test_blocked_claim_denies_and_activation_cannot_accept_production_stream():
    with tempfile.TemporaryDirectory() as td:
        plan = sim.plan(td); api = sim.API(plan)
        ledger = p.Ledger(plan, Path(td)/'bootstrap.jsonl', 'bootstrap')
        client = p.Client(sim.boundary(plan, ledger, 'fixture', 'fixture', api.open)); client.boundary.preflight()
        s = p.store_for(client, 0)
        rejects(ValueError, s.__enter__); assert ledger.counts['PUT'] == 0
        env = json.loads(p.synthetic_seed(plan)); env['snapshot']['control']['stream_id'] = 'production'
        env['body_digest'] = p.digest(env['snapshot'])
        rejects(ValueError, lambda: p.check_identity(plan, p.canonical(env).encode()))
        ledger.close()


def test_lost_before_403_429_attempt_once_and_halt_without_unlock():
    for mode in ('before', 403, 429):
        with tempfile.TemporaryDirectory() as td:
            plan, api, ledger, client = setup(td)
            s = p.store_for(client, 1); s.__enter__()
            old = api.head; before = ledger.counts['PUT']; api.fail = mode
            s.snapshot['control']['health']['synthetic'] = mode
            rejects(p.gh.StoreConflict, s.commit)
            assert api.head == old and ledger.counts['PUT'] == before+1
            rejects(p.gh.StoreConflict, s.commit)
            s.__exit__(None, None, None)
            assert api.head == old and ledger.counts['PUT'] == before+1
            assert json.loads(base64.b64decode(api.records[api.head]['body']))['snapshot']['control']['owner'] == s.owner
            ledger.close()


def test_lost_after_exact_readback_confirms_only_matching_parent():
    with tempfile.TemporaryDirectory() as td:
        plan, api, ledger, client = setup(td)
        api.fail = 'after'; s = p.store_for(client, 1); s.__enter__()
        assert s.revision == 2 and not s._halted
        api.fail = 'after'; s.__exit__(None, None, None)
        assert s.snapshot['control']['owner'] is None
        assert ledger.counts['PUT'] == 3; ledger.close()
    with tempfile.TemporaryDirectory() as td:
        plan, api, ledger, client = setup(td)
        original = api.put
        def wrong_parent(body, parent, commit=None):
            sha = original(body, parent, commit); api.records[sha]['parents'] = []; return sha
        api.put = wrong_parent; api.fail = 'after'
        s = p.store_for(client, 1); rejects(p.gh.StoreConflict, s.__enter__)
        assert s._halted and ledger.counts['PUT'] == 2; ledger.close()


def test_stale_concurrent_read_cas_and_stale_readback_preserve_owner():
    with tempfile.TemporaryDirectory() as td:
        plan, api, ledger, client = setup(td, 'stale')
        rejects(p.gh.StoreConflict, lambda: p.sequence(client, 'stale'))
        env = json.loads(base64.b64decode(api.records[api.head]['body']))
        assert env['snapshot']['control']['owner'] == p.owner(plan, 5)
        assert env['snapshot']['commands'][p.owner(plan,5)['run_id']]['_delivery']['messages'][0]['status'] == 'sending'
        ledger.close()


def test_global_case_run_and_byte_limits_stop_before_outbound():
    for counter, method, limit in [('global', 'GET', 384), ('global', 'PUT', 48),
                                    ('case', 'GET', 128), ('case', 'PUT', 12), ('run', 'PUT', 12)]:
        with tempfile.TemporaryDirectory() as td:
            plan, api, ledger, client = setup(td); p.store_for(client, 1)
            if counter == 'global': ledger.counts[method] = limit
            elif counter == 'case': ledger.cases[ledger.phase][method] = limit
            else: ledger.runs[p.canonical(ledger.run)] = limit
            n = len(api.trace); rejects(ValueError, lambda: ledger.charge(method)); assert len(api.trace) == n
            ledger.close()
    with tempfile.TemporaryDirectory() as td:
        plan, api, ledger, client = setup(td); s = p.store_for(client, 1); s.__enter__()
        n = ledger.counts['PUT']; s.snapshot['control']['health']['padding'] = 'x'*768000
        rejects(p.gh.StoreUnavailable, s.commit); assert ledger.counts['PUT'] == n; ledger.close()


def test_response_limit_malformed_blob_and_no_sensitive_log():
    with tempfile.TemporaryDirectory() as td:
        plan, api, ledger, client = setup(td)
        def oversized(req, timeout):
            response = sim.Response({}); response.write(b'x'*(p.LIMITS['response_bytes']+1)); response.seek(0); return response
        client.boundary.opener = oversized
        rejects(p.gh.StoreUnavailable, lambda: client.read(plan['repo'], plan['branch']))
        ledger.close()
        log = Path(td,'happy.jsonl').read_text()
        assert 'reader-secret-fixture' not in log and 'writer-secret-fixture' not in log and 'NEVER LOG RESPONSE' not in log
    with tempfile.TemporaryDirectory() as td:
        plan, api, ledger, client = setup(td)
        api.override['/contents/'+p.gh.STORE_PATH] = {'type': 'file', 'encoding': 'base64', 'sha': 'f'*40, 'content': 'e30='}
        rejects(p.gh.StoreUnavailable, lambda: client.read(plan['repo'], plan['branch'])); ledger.close()


def test_complete_history_rejects_readme_parent_digest_and_foreign_root():
    for kind in ('extra-file', 'digest', 'root'):
        with tempfile.TemporaryDirectory() as td:
            plan, api, ledger, client = setup(td)
            if kind == 'extra-file':
                api.override['/git/trees/'+api.records[api.head]['tree']] = {'truncated': False,
                    'tree': [{'path': 'README.md', 'type': 'blob', 'mode': '100644', 'sha': 'e'*40}]}
            elif kind == 'digest':
                env = json.loads(base64.b64decode(api.records[api.head]['body'])); env['parent_digest'] = 'f'*64
                api.put(p.canonical(env).encode(), api.head)
            else: api.records[plan['seed_commit']]['parents'] = ['f'*40]
            rejects((ValueError, KeyError, p.gh.StoreUnavailable), lambda: p.verify_history(client, full=True)); ledger.close()


def test_replay_fork_truncated_journal_and_incomplete_predecessor_denied():
    with tempfile.TemporaryDirectory() as td:
        plan, api, ledger, client = setup(td)
        ledger.emit('phase_halt', result='incomplete-no-retry-no-release'); ledger.close()
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'new.jsonl'), 'lost-after', Path(td,'happy.jsonl')))
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'again.jsonl'), 'happy', Path(td,'happy.jsonl')))
        bad = Path(td,'bad.jsonl'); bad.write_text(Path(td,'happy.jsonl').read_text()[:-9])
        rejects((ValueError, json.JSONDecodeError), lambda: p.Ledger.verify(bad, p.digest(plan)))


def test_local_git_bootstrap_is_root_only_blocked_deterministic_and_fsck():
    with tempfile.TemporaryDirectory() as td:
        plan = sim.plan(td); a = Path(td,'root-a'); b = Path(td,'root-b')
        one = p.build_bootstrap(plan, a); two = p.build_bootstrap(plan, b)
        assert one == two and one['seed_bytes'] < 768000
        def git(*args): return subprocess.check_output(['git', '-c', 'safe.directory='+a.as_posix(), '-C', str(a), *args]).decode().strip()
        assert git('rev-list', '--count', one['seed_commit']) == '1'
        assert git('rev-list', '--parents', one['seed_commit']) == one['seed_commit']
        assert git('ls-tree', '-r', '--name-only', one['seed_commit']) == p.gh.STORE_PATH
        assert git('show', one['seed_commit']+':'+p.gh.STORE_PATH).encode() == p.synthetic_seed(plan)
        git('fsck', '--full'); git('bundle', 'verify', str(a/'blocked-seed.bundle'))


def test_bootstrap_separate_git_mutation_lost_response_readback_and_no_retry():
    for loss in ('none', 'after', 'before'):
        with tempfile.TemporaryDirectory() as td:
            plan = sim.plan(td)
            pins = p.build_bootstrap(plan, Path(td,'prepared'))
            plan.update(seed_commit=pins['seed_commit'], seed_sha256=pins['seed_sha256'])
            api = sim.API(plan); api.head = None
            ledger = p.Ledger(plan, Path(td,'bootstrap.jsonl'), 'bootstrap')
            client = p.Client(sim.boundary(plan, ledger, 'fixture-reader', 'fixture-bootstrap', api.open))
            original_run = subprocess.run; pushes = []
            def run(args, **kwargs):
                if 'push' not in args: return original_run(args, **kwargs)
                pushes.append(args)
                assert args[-1] == plan['seed_commit']+':refs/heads/'+plan['branch']
                assert '--force' not in args and '--mirror' not in args and '--all' not in args
                assert 'http.followRedirects=false' in args
                assert kwargs['env']['P3_EXPLICIT_BOOTSTRAP_TOKEN'] == 'fixture-bootstrap'
                if loss != 'before': api.head = plan['seed_commit']
                if loss in ('before', 'after'): raise subprocess.CalledProcessError(1, args)
                return subprocess.CompletedProcess(args, 0)
            with patch.object(subprocess, 'run', run):
                if loss == 'before': rejects(p.gh.StoreUnavailable, lambda: p.bootstrap(client, Path(td,'execution-root')))
                else: p.bootstrap(client, Path(td,'execution-root'))
            assert len(pushes) == 1 and ledger.counts['GIT_PUSH'] == 1 and ledger.counts['PUT'] == 0
            ledger.close()
            rejects((ValueError, FileExistsError), lambda: p.Ledger(plan, Path(td,'again.jsonl'), 'bootstrap'))


def test_code_grant_pin_wrong_tree_missing_file_and_no_generated_grant():
    plan = sim.plan()
    grant = {'schema': 'p3-human-grant-v2', 'plan_sha256': p.digest(plan), 'phase': 'activate',
        'approved_by': 'fixture-human', 'human_authorization': True, 'expires_utc': '2099-01-01T00:00:00Z',
        'approval_evidence_sha256': 'a'*64, 'review_sha256': None}
    with patch.object(p.getpass, 'getpass', side_effect=AssertionError('prompt')):
        rejects(ValueError, lambda: p.authorize(plan, grant, 'activate', p.digest(plan)))
    assert not hasattr(p, 'create_grant')


def test_restart_after_loss_cannot_invent_completion_or_use_new_run_ids():
    with tempfile.TemporaryDirectory() as td:
        result = sim.rehearsal(Path(td,'run')); plan = result['plan']; journal = Path(td,'run/process-loss.jsonl')
        rows = p.Ledger.verify(journal, p.digest(plan))
        assert rows[-1]['event'] == 'phase_halt'
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'run/again.jsonl'), 'process-loss', journal))
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'run/another.jsonl'), 'lost-before', journal))
        corrupt = deepcopy(plan); corrupt['runs'][5]['run_id'] = 'replacement'
        rejects(ValueError, lambda: p.validate_plan(corrupt))


def hard_loss_worker(td):
    import socket
    def forbidden(*a, **k): raise AssertionError('External network forbidden')
    with patch('urllib.request.urlopen', side_effect=forbidden), patch.object(socket.socket, 'connect', forbidden):
        plan = sim.plan(td); api = sim.API(plan, persisted=Path(td,'api.json'))
        Path(td,'plan.json').write_text(p.canonical(plan), encoding='utf-8')
        previous = sim.execute(plan, api, td, 'bootstrap')
        previous = sim.execute(plan, api, td, 'activate', previous)
        original = p.Ledger.emit
        def emit(self, event, **fields):
            original(self, event, **fields)
            if event == 'loss_boundary': os._exit(23)
        with patch.object(p.Ledger, 'emit', emit): sim.execute(plan, api, td, 'process-loss', previous)


def test_hard_process_loss_parent_wait_explicit_takeover_and_uncertain_retention():
    with tempfile.TemporaryDirectory() as td:
        process = subprocess.Popen([sys.executable, str(Path(__file__)), '--worker', td], cwd=ROOT,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        assert process.wait(timeout=60) == 23, process.stderr.read().decode()
        plan = json.loads(Path(td,'plan.json').read_text()); journal = Path(td,'process-loss.jsonl')
        term = launcher.observe_exit(process, plan, journal)
        saved = json.loads(Path(td,'api.json').read_text()); api = sim.API(plan)
        api.records, api.head = saved['records'], saved['head']
        rows = p.Ledger.verify(journal, p.digest(plan))
        assert rows[-1]['event'] == 'loss_boundary' and list(Path(td).glob('probe-session.lock'))
        rejects((ValueError, FileExistsError), lambda: p.Ledger(plan, Path(td,'restart.jsonl'), 'takeover', journal))
        review = {'expected_owner': term['owner'], 'expected_revision': term['revision'],
            'expected_commit': term['commit'], 'termination': term,
            'evidence': {'old_owner': term['owner'], 'reviewer': 'synthetic-human-review', 'evidence_sha256': 'e'*64,
                         'run_completed': True, 'workers_terminated': True, 'triggers_paused': True}}
        p.validate_termination(plan, review, journal)
        for key, value in [('expected_revision', term['revision']+1), ('expected_commit','f'*40),
                           ('expected_owner',p.owner(plan,1))]:
            bad = deepcopy(review); bad[key] = value
            rejects(ValueError, lambda: p.validate_termination(plan, bad, journal))
        bad = deepcopy(review); bad['termination']['observed_wait'] = False
        rejects(ValueError, lambda: p.validate_termination(plan, bad, journal))
        ledger = p.Ledger(plan, Path(td,'takeover.jsonl'), 'takeover', journal, reviewed_termination=review)
        client = p.Client(sim.boundary(plan, ledger, 'fixture', 'fixture', api.open)); client.boundary.preflight()
        p.verify_history(client); p.takeover(client, review)
        env = json.loads(base64.b64decode(api.records[api.head]['body']))
        assert env['snapshot']['control']['owner'] is None
        assert env['snapshot']['commands'][term['owner']['run_id']]['_delivery']['messages'][0]['status'] == 'uncertain'
        n = ledger.counts['PUT']; rejects(p.gh.StoreConflict, p.store_for(client, 6).__enter__)
        assert ledger.counts['PUT'] == n and ledger.counts['GET'] < 384
        ledger.close()


if __name__ == '__main__' and sys.argv[1:2] == ['--worker']:
    hard_loss_worker(sys.argv[2])
