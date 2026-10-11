"""Offline CLI continuation fixtures. No real credentials, sockets or Git push."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import types
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import p3_github_probe as p
import p3_probe_simulation as sim
import p3_reader401_continue as c
from test_p3_github_probe import rejects


def deny(*a, **kw): raise AssertionError('External network forbidden')


def save(path, value): Path(path).write_text(p.canonical(value), encoding='utf-8')
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def fixture_worker(td):
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    p.urllib.request.urlopen = deny
    root = Path(td); plan = sim.plan(root)
    plan.update(code_head=c.ORIGINAL_HEAD, code_tree=c.ORIGINAL_TREE,
        code_pins={'tools/p3_github_probe.py': hashlib.sha256(c.git(ROOT, 'show',
                   c.ORIGINAL_HEAD+':tools/p3_github_probe.py')).hexdigest()})
    pins = p.build_bootstrap(plan, root/'prepared')
    plan.update(seed_commit=pins['seed_commit'], seed_sha256=pins['seed_sha256'])
    grant = sim.fixture_grant(plan, 'bootstrap')
    save(root/'plan.json', plan); save(root/'original-grant.json', grant)
    api = sim.API(plan)
    def rejected(req, **kw): api.error(req, 401)
    argv = ['probe', '--real', '--plan', str(root/'plan.json'), '--grant', str(root/'original-grant.json'),
        '--approved-plan-sha256', p.digest(plan), '--phase', 'bootstrap',
        '--journal', str(root/'bootstrap.jsonl'), '--bootstrap-dir', str(root/'execution')]
    with patch.object(sys, 'argv', argv), patch.object(p, 'verify_code_pin', lambda _: None), \
         patch.object(p.getpass, 'getpass', return_value=sim.FIXTURE_TOKEN), \
         patch.object(p.urllib.request, 'build_opener', return_value=types.SimpleNamespace(open=rejected)):
        try: p.main()
        except p.HTTPStatus as e: assert e.status == 401
        else: raise AssertionError('Expected Reader-401')


def fixture(td):
    proc = subprocess.Popen([sys.executable, str(Path(__file__)), '--fixture', str(td)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.wait(timeout=90) == 0, proc.stderr.read().decode()
    assert read(Path(td,'attempt-bootstrap.json'))['pid'] == proc.pid
    save(Path(td,'parent-wait-fixture.json'), {'pid': proc.pid, 'exit_code': proc.returncode, 'observed_wait': True})
    return amendment_for_existing(td)


def amendment_for_existing(td):
    root = Path(td); plan = read(root/'plan.json'); a = c.template()
    rows = p.Ledger.verify(root/'bootstrap.jsonl', p.digest(plan))
    assert [r['event'] for r in rows] == [
        'phase_start', 'authorization', 'request', 'response', 'phase_halt']
    a.update(original_plan_sha256=p.digest(plan), original_grant=read(root/'original-grant.json'),
             original_code_materialization=c.original_materialization(plan), expires_utc='2099-01-01T00:00:00Z')
    a['execution_code'] = {'code_head': 'f'*40, 'code_tree': 'e'*40,
                          'code_pins': {name: 'e'*64 for name in set(plan['code_pins']) | c.EXTRA_PINS}}
    a['predecessor'].update(journal_sha256=c.sha(root/'bootstrap.jsonl'), frontier_hash=rows[-1]['hash'],
        highwater=rows[-1]['utc'], database_sha256=c.sha(root/'probe-session.sqlite3'),
        marker_sha256=c.sha(root/'attempt-bootstrap.json'), lock_sha256=c.sha(root/'probe-session.lock'))
    a['root'] = {'directory': str(root/'execution'), 'files_sha256': c.root_files(root/'execution')}
    a['review'].update(reviewer='offline-fixture-only', evidence_sha256='e'*64, original_pid=rows[0]['pid'],
        observed_utc=p.utc(), terminal_code_path_checked=True, all_workers_ended=True,
        triggers_paused=True, human_review=True)
    return plan, a


def grant_for(plan, amendment):
    grant = sim.fixture_grant(plan, c.PHASE)
    grant['review_sha256'] = p.digest(amendment)
    return grant


def cli(td, plan, amendment, grant=None, prompt=None, checkpoint=None, api=None, patch_code=True):
    """Argparse, authorization, lock, accounting, preflight and root readback are real.

    Only the new code gate is patched in dirty-tree unit tests. Delivery rehearsal
    calls this with patch_code=False on the committed tree and genuine file pins.
    """
    root = Path(td); grant = grant or grant_for(plan, amendment)
    for name, value in [('plan.json', plan), ('amendment.json', amendment), ('grant.json', grant)]: save(root/name, value)
    api = api or sim.API(plan); api.head = None
    pushes = []; prompts = []; original_run = subprocess.run
    def wire_event(method):
        with (root/'fixture-wire-events.jsonl').open('a', encoding='utf-8') as f:
            f.write(p.canonical({'method': method, 'fixture_only': True})+'\n'); f.flush(); os.fsync(f.fileno())
    def fake_run(args, **kw):
        if 'push' not in args: return original_run(args, **kw)
        assert args[-2:] == ['https://github.com/'+plan['repo']+'.git', plan['seed_commit']+':refs/heads/'+plan['branch']]
        assert '--force' not in args and kw['env']['P3_EXPLICIT_BOOTSTRAP_TOKEN'] == sim.FIXTURE_TOKEN
        # Persisted reservation and publication MUST precede the simulated wire.
        db = sqlite3.connect(root/'probe-session.sqlite3')
        row = read_latest(db); state = db.execute('SELECT published FROM frontier').fetchone()[0]; db.close()
        assert row['event'] == 'request' and row['method'] == 'GIT_PUSH' and row['hash'] == state
        wire_event('GIT_PUSH'); pushes.append(args); api.head = plan['seed_commit']
        return types.SimpleNamespace(returncode=0)
    def ask(label):
        prompts.append(label)
        return prompt(label) if prompt else sim.FIXTURE_TOKEN
    original_open = api.open
    def checked_open(req, **kw):
        db = sqlite3.connect(root/'probe-session.sqlite3')
        row = read_latest(db); state = db.execute('SELECT published FROM frontier').fetchone()[0]; db.close()
        assert row['event'] == 'request' and row['method'] == req.method and row['hash'] == state
        assert row['counts']['GET'] >= 2  # first failed attempt retained
        wire_event(req.method)
        return original_open(req, **kw)
    argv = ['continue', '--real', '--plan', str(root/'plan.json'), '--amendment', str(root/'amendment.json'),
        '--grant', str(root/'grant.json'), '--approved-amendment-sha256', p.digest(amendment)]
    with ExitStack() as stack:
        for obj, name, value in [(sys, 'argv', argv), (p.getpass, 'getpass', ask),
                (socket.socket, 'connect', deny), (socket.socket, 'connect_ex', deny),
                (socket, 'create_connection', deny), (p.urllib.request, 'urlopen', deny),
                (subprocess, 'run', fake_run)]: stack.enter_context(patch.object(obj, name, value))
        stack.enter_context(patch.object(p.urllib.request, 'build_opener',
            return_value=types.SimpleNamespace(open=checked_open)))
        if patch_code: stack.enter_context(patch.object(c, 'verify_execution_code', lambda _: None))
        if checkpoint: stack.enter_context(patch.object(p.Ledger, 'checkpoint', checkpoint))
        try: c.main()
        finally: save(root/'fixture-wire.json', {'http': api.trace, 'pushes': len(pushes), 'prompts': len(prompts)})
    return api, pushes


def read_latest(db): return json.loads(db.execute('SELECT body FROM events ORDER BY seq DESC LIMIT 1').fetchone()[0])


def test_reader401_cli_continues_once_same_seed_history_and_cumulative_budget():
    with tempfile.TemporaryDirectory() as td:
        plan, a = fixture(td); root = Path(td); old = (root/'bootstrap.jsonl').read_bytes()
        oldroot = c.root_files(root/'execution')
        api, pushes = cli(td, plan, a)
        rows = p.Ledger.verify(root/(c.PHASE+'.jsonl'), p.digest(plan))
        assert rows[-1]['event'] == 'phase_end' and rows[-1]['result'] == 'confirmed'
        assert rows[-1]['counts'] == {'GET': 16, 'PUT': 0, 'GIT_PUSH': 1}
        assert len(api.trace) == 15 and len(pushes) == 1 and (root/'bootstrap.jsonl').read_bytes() == old
        current = c.root_files(root/'execution')
        assert all(current[name] == value for name, value in oldroot.items())
        c.root_matches(a)  # only the existing token-free askpass helpers may be added
        assert (root/(c.PHASE+'.jsonl')).read_bytes().startswith(old)
        assert all(r.get('budget_phase') == 'bootstrap' for r in rows if r['phase'] == c.PHASE and r['event'] == 'request')
        rejects(ValueError, lambda: cli(td, plan, a))
        assert read(root/'fixture-wire.json') == {'http': [], 'pushes': 0, 'prompts': 0}
        rejects(ValueError, lambda: p.Ledger(plan, root/'activate.jsonl', 'activate', root/(c.PHASE+'.jsonl')))


def test_reader401_missing_wrong_expired_or_unreviewed_grant_stops_before_credentials():
    with tempfile.TemporaryDirectory() as td:
        plan, original = fixture(td)
        for mode in ('missing', 'wrong-phase', 'wrong-review', 'expired', 'false-human', 'no-end-review',
                     'wrong-original-grant', 'wrong-materialization', 'wrong-plan', 'wrong-executor', 'long-grant'):
            a = deepcopy(original); changed = deepcopy(plan); g = grant_for(plan, a)
            if mode == 'missing': g.pop('approval_evidence_sha256')
            elif mode == 'wrong-phase': g['phase'] = 'bootstrap'
            elif mode == 'wrong-review': g['review_sha256'] = '0'*64
            elif mode == 'expired': g['expires_utc'] = '2020-01-01T00:00:00Z'
            elif mode == 'false-human': g['human_authorization'] = False
            elif mode == 'no-end-review': a['review']['all_workers_ended'] = False
            elif mode == 'wrong-original-grant': a['original_grant']['expires_utc'] = '2098-01-01T00:00:00Z'
            elif mode == 'wrong-materialization': a['original_code_materialization'] = {}
            elif mode == 'wrong-plan': changed['repo'] = 'synthetic/changed'
            elif mode == 'wrong-executor': a['execution_code']['code_head'] = c.ORIGINAL_HEAD
            elif mode == 'long-grant': a['expires_utc'] = '2098-01-01T00:00:00Z'
            if a != original: g['review_sha256'] = p.digest(a)
            rejects((ValueError, KeyError), lambda: cli(td, changed, a, g))
            assert read(Path(td,'fixture-wire.json')) == {'http': [], 'pushes': 0, 'prompts': 0}, mode
            assert not Path(td,'attempt-'+c.PHASE+'.json').exists()


def test_reader401_missing_or_changed_frontier_journal_marker_and_seed_stops():
    with tempfile.TemporaryDirectory() as td:
        plan, a = fixture(td); root = Path(td)
        for name in ('probe-session.sqlite3', 'bootstrap.jsonl', 'attempt-bootstrap.json', 'probe-session.lock'):
            path = root/name; saved = path.read_bytes(); held = root/(name+'.held')
            path.rename(held)
            try:
                rejects(ValueError, lambda: cli(td, plan, a))
                assert read(root/'fixture-wire.json')['prompts'] == 0 and not path.exists()
            finally: held.rename(path)
            path.write_bytes(saved+b'changed')
            try:
                rejects((ValueError, sqlite3.DatabaseError), lambda: cli(td, plan, a))
                assert read(root/'fixture-wire.json')['prompts'] == 0
            finally: path.write_bytes(saved)
        for key in ('frontier_hash', 'journal_sha256', 'marker_sha256', 'database_sha256', 'lock_sha256'):
            altered = deepcopy(a); altered['predecessor'][key] = 'f'*64
            rejects(ValueError, lambda: cli(td, plan, altered))
        altered = deepcopy(a); altered['predecessor']['journal'] = 'alternative.jsonl'
        (root/'alternative.jsonl').write_bytes((root/'bootstrap.jsonl').read_bytes())
        rejects(ValueError, lambda: cli(td, plan, altered))
        (root/'execution'/'unknown-file').write_text('unreviewed')
        rejects(ValueError, lambda: cli(td, plan, a))
        assert read(root/'fixture-wire.json')['prompts'] == 0


def test_reader401_semantic_prior_mutation_unknown_response_and_old_frontier_denied():
    with tempfile.TemporaryDirectory() as td:
        plan, a = fixture(td); root = Path(td)
        original_db = (root/'probe-session.sqlite3').read_bytes(); original_journal = (root/'bootstrap.jsonl').read_bytes()
        original = p.Ledger.verify(root/'bootstrap.jsonl', p.digest(plan))
        for mode in ('PUT', 'GIT_PUSH', 'unknown', '403', 'truncated', 'older-frontier'):
            rows = deepcopy(original); changed = deepcopy(a)
            if mode in ('PUT', 'GIT_PUSH'):
                rows[2]['method'] = mode
                for row in rows[2:]: row['counts'] = {'GET': 0, 'PUT': int(mode == 'PUT'), 'GIT_PUSH': int(mode == 'GIT_PUSH')}
            elif mode == 'unknown': rows[3]['result'] = 'unknown'
            elif mode == '403': rows[3]['result'] = 'http-403'
            elif mode == 'truncated': rows = rows[:-1]
            previous = '0'*64
            for row in rows:
                row.pop('hash'); row['previous_hash'] = previous; row['hash'] = previous = p.digest(row)
            with (root/'bootstrap.jsonl').open('w', encoding='utf-8', newline='\n') as f:
                f.write(''.join(p.canonical(r)+'\n' for r in rows))
            db = sqlite3.connect(root/'probe-session.sqlite3')
            db.execute('DELETE FROM events')
            db.executemany('INSERT INTO events(body) VALUES (?)', [(p.canonical(r),) for r in rows])
            frontier = rows[-2] if mode == 'older-frontier' else rows[-1]
            db.execute('UPDATE frontier SET published=?,highwater=?', (frontier['hash'], frontier['utc'])); db.commit(); db.close()
            changed['predecessor'].update(frontier_hash=frontier['hash'], highwater=frontier['utc'],
                frontier_rows=len(rows), counts=rows[-1]['counts'], journal_sha256=c.sha(root/'bootstrap.jsonl'),
                database_sha256=c.sha(root/'probe-session.sqlite3'))
            rejects(ValueError, lambda: cli(td, plan, changed))
            assert read(root/'fixture-wire.json') == {'http': [], 'pushes': 0, 'prompts': 0}
            (root/'probe-session.sqlite3').write_bytes(original_db); (root/'bootstrap.jsonl').write_bytes(original_journal)


def test_reader401_token_form_never_logs_or_repairs_input_and_blocks_wire():
    for token in (sim.FIXTURE_TOKEN*2, ' '+sim.FIXTURE_TOKEN, sim.FIXTURE_TOKEN+'\n', '', 'ghp_fixture'):
        rejects(ValueError, lambda: p.validate_token(token))
    assert p.validate_token(sim.FIXTURE_TOKEN) == sim.FIXTURE_TOKEN
    with tempfile.TemporaryDirectory() as td:
        plan, a = fixture(td)
        rejects(ValueError, lambda: cli(td, plan, a, prompt=lambda _: sim.FIXTURE_TOKEN*2))
        wire = read(Path(td,'fixture-wire.json')); assert wire == {'http': [], 'pushes': 0, 'prompts': 1}
        rows = p.Ledger.verify(Path(td,c.PHASE+'.jsonl'), p.digest(plan))
        assert rows[-1]['counts'] == {'GET': 1, 'PUT': 0, 'GIT_PUSH': 0} and rows[-1]['event'] == 'phase_halt'
        assert sim.FIXTURE_TOKEN not in Path(td,c.PHASE+'.jsonl').read_text()
        rejects(ValueError, lambda: cli(td, plan, a))


def test_reader401_second_auth_failure_stays_counted_and_has_no_retry():
    with tempfile.TemporaryDirectory() as td:
        plan, a = fixture(td); api = sim.API(plan)
        def bad(req, **kw): api.trace.append(('GET', '')); api.error(req, 401)
        api.open = bad
        rejects(p.HTTPStatus, lambda: cli(td, plan, a, api=api))
        rows = p.Ledger.verify(Path(td,c.PHASE+'.jsonl'), p.digest(plan))
        assert rows[-1]['counts'] == {'GET': 2, 'PUT': 0, 'GIT_PUSH': 0}
        rejects(ValueError, lambda: cli(td, plan, a))
        assert read(Path(td,'fixture-wire.json')) == {'http': [], 'pushes': 0, 'prompts': 0}


def test_reader401_alive_pid_and_shared_kernel_exclusivity():
    with tempfile.TemporaryDirectory() as td:
        plan, a = fixture(td)
        rejects(ValueError, lambda: c.process_ended(os.getpid()))
        # Known alive unrelated process/PID reuse must also fail closed.
        proc = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'])
        try: rejects(ValueError, lambda: c.process_ended(proc.pid))
        finally: proc.terminate(); proc.wait(timeout=15)
        ledger = p.Ledger(plan, Path(td,c.PHASE+'.jsonl'), c.PHASE, Path(td,'bootstrap.jsonl'), reader401_amendment=a)
        try:
            rejects((ValueError, OSError), lambda: cli(td, plan, a))
            assert read(Path(td,'fixture-wire.json')) == {'http': [], 'pushes': 0, 'prompts': 0}
            for phase in ('inspect', 'takeover'):
                rejects((ValueError, OSError), lambda: p.Ledger(plan, Path(td,'other.jsonl'), phase, ledger.path))
            assert ledger.counts == ledger.cases['bootstrap'] == {'GET': 1, 'PUT': 0, 'GIT_PUSH': 0}
            rejects(ValueError, lambda: ledger.charge('PUT'))
            # Existing attempt counts reduce the remaining shared case capacity.
            ledger.guard = p.GrantGuard(plan, grant_for(plan, a), c.PHASE)
            for _ in range(127): ledger.charge('GET')
            rejects(ValueError, lambda: ledger.charge('GET'))
            assert ledger.counts['GET'] == ledger.cases['bootstrap']['GET'] == 128
        finally: ledger.close()


def test_reader401_live_original_cli_process_and_manifest_bound_wrong_root_stop():
    with tempfile.TemporaryDirectory() as td:
        script = "import sys;sys.path.insert(0,sys.argv[1]);import test_p3_reader401 as t;t.fixture_worker(sys.argv[2]);print('READY',flush=True);sys.stdin.read(1)"
        proc = subprocess.Popen([sys.executable, '-c', script, str(ROOT/'engine'), td],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            while True:
                line = proc.stdout.readline()
                assert line, proc.stderr.read().decode()
                if line.strip() == b'READY': break
            plan, a = amendment_for_existing(td)
            rejects(ValueError, lambda: cli(td, plan, a))
            assert read(Path(td,'fixture-wire.json')) == {'http': [], 'pushes': 0, 'prompts': 0}
        finally:
            proc.communicate(b'x', timeout=30)
        assert proc.returncode == 0
        # The same review still must not accept a wrong root even when the
        # attacker/reviewer supplies a manifest matching the changed bytes.
        Path(td,'execution/refs/heads',plan['branch']).write_text('0'*40+'\n')
        a['root']['files_sha256'] = c.root_files(Path(td,'execution'))
        rejects((ValueError, subprocess.CalledProcessError), lambda: cli(td, plan, a))
        assert read(Path(td,'fixture-wire.json')) == {'http': [], 'pushes': 0, 'prompts': 0}


class Clock(datetime):
    current = None
    @classmethod
    def now(cls, tz=None): return cls.current if tz else cls.current.replace(tzinfo=None)


def test_reader401_exact_deadline_credentials_preflight_push_and_late_reply():
    for where in ('credentials', 'preflight', 'before-push', 'late-lost-reply'):
        with tempfile.TemporaryDirectory() as td:
            plan, a = fixture(td); Clock.current = datetime.now(timezone.utc)+timedelta(seconds=1)
            deadline = Clock.current+timedelta(minutes=1); grant = grant_for(plan, a)
            grant['expires_utc'] = deadline.isoformat().replace('+00:00', 'Z')
            api = sim.API(plan); original_open = api.open
            def opened(req, **kw):
                response = original_open(req, **kw)
                if where == 'preflight': Clock.current = deadline
                return response
            api.open = opened
            def prompt(_):
                if where == 'credentials': Clock.current = deadline
                return sim.FIXTURE_TOKEN
            def checkpoint(self, point, event):
                if where == 'before-push' and point == 'before_outbound' and event == 'GIT_PUSH': Clock.current = deadline
                if where == 'late-lost-reply' and point == 'before_outbound' and event == 'GIT_PUSH':
                    # Start is valid; fake Git returns lost response at exact expiry.
                    original_run = subprocess.run
                    def lost(args, **kw):
                        result = original_run(args, **kw)
                        if 'push' in args:
                            Clock.current = deadline
                            raise subprocess.CalledProcessError(1, args)
                        return result
                    subprocess.run = lost
            with patch.object(p, 'datetime', Clock):
                rejects(ValueError, lambda: cli(td, plan, a, grant, prompt, checkpoint, api))
            rows = p.Ledger.verify(Path(td,c.PHASE+'.jsonl'), p.digest(plan)); wire = read(Path(td,'fixture-wire.json'))
            assert rows[-1]['event'] == 'phase_halt' and not any(r['event'] == 'phase_end' for r in rows)
            assert wire['pushes'] == int(where == 'late-lost-reply')
            assert len(wire['http']) == {'credentials': 0, 'preflight': 1, 'before-push': 6, 'late-lost-reply': 6}[where]
            assert rows[-1]['counts']['GIT_PUSH'] == int(where in ('before-push', 'late-lost-reply'))


def kill_worker(td, point, event):
    plan = read(Path(td,'plan.json')); a = read(Path(td,'amendment.json'))
    def checkpoint(self, here, what):
        if here == point and what == event: os._exit(71)
    cli(td, plan, a, checkpoint=checkpoint)
    raise AssertionError('Kill point not reached')


def test_reader401_hard_loss_at_intent_amendment_frontier_and_request_boundaries():
    targets = [('after_intent', 'phase_start')]
    targets += [(point, event) for event in ('phase_start', 'reader401_amendment', 'request')
                for point in ('before_commit', 'after_commit', 'after_mirror', 'after_publish')]
    targets += [('before_outbound', 'GET'), ('before_outbound', 'GIT_PUSH')]
    for point, event in targets:
        with tempfile.TemporaryDirectory() as td:
            plan, a = fixture(td); save(Path(td,'amendment.json'), a)
            proc = subprocess.Popen([sys.executable, str(Path(__file__)), '--kill', td, point, event],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            assert proc.wait(timeout=90) == 71, (point, event, proc.stderr.read().decode())
            db = sqlite3.connect(Path(td,'probe-session.sqlite3')); last = read_latest(db); db.close()
            expected_get = 7 if event == 'GIT_PUSH' else 1+int(event in ('request', 'GET') and point != 'before_commit')
            assert last['counts'] == {'GET': expected_get, 'PUT': 0, 'GIT_PUSH': int(event == 'GIT_PUSH')}
            wire = Path(td,'fixture-wire-events.jsonl')
            assert (len(wire.read_text().splitlines()) if wire.exists() else 0) == (6 if event == 'GIT_PUSH' else 0)
            rejects(ValueError, lambda: cli(td, plan, a))
            assert read(Path(td,'fixture-wire.json')) == {'http': [], 'pushes': 0, 'prompts': 0}
            assert Path(td,'attempt-'+c.PHASE+'.json').exists()


if __name__ == '__main__':
    if sys.argv[1:2] == ['--fixture']: fixture_worker(sys.argv[2])
    elif sys.argv[1:2] == ['--kill']: kill_worker(*sys.argv[2:])
