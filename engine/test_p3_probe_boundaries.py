"""Offline regression for N-P3-02/03, including real process death and CLI wiring."""
import base64
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
from test_p3_github_probe import rejects


class Clock(datetime):
    current = datetime(2030, 1, 1, tzinfo=timezone.utc)

    @classmethod
    def now(cls, tz=None):
        return cls.current if tz else cls.current.replace(tzinfo=None)


def reset_clock():
    Clock.current = datetime(2030, 1, 1, tzinfo=timezone.utc)


def started(td, phase='activate', expiry=None):
    plan = sim.plan(td); api = sim.API(plan)
    previous = sim.execute(plan, api, td, 'bootstrap')
    ledger = p.Ledger(plan, Path(td, phase+'.jsonl'), phase, previous)
    grant = sim.fixture_grant(plan, phase, expiry or '2099-01-01T00:00:00Z')
    client = p.Client(p.Boundary(plan, ledger, 'fixture', 'fixture', api.open,
                               guard=p.GrantGuard(plan, grant, phase)))
    return plan, api, previous, ledger, client


def cli(plan, api, directory, phase, previous, prompt=None, grant=None):
    """Actual argparse/main/authorize; tests patch only code-pin gate where dirty."""
    root = Path(directory)
    grant = grant or sim.fixture_grant(plan, phase)
    planfile, grantfile = root/(phase+'-plan.json'), root/(phase+'-grant.json')
    planfile.write_text(p.canonical(plan), encoding='utf-8')
    grantfile.write_text(p.canonical(grant), encoding='utf-8')
    argv = ['probe', '--real', '--plan', str(planfile), '--grant', str(grantfile),
            '--approved-plan-sha256', p.digest(plan), '--phase', phase,
            '--journal', str(root/(phase+'-cli.jsonl'))]
    if previous: argv += ['--previous-journal', str(previous)]
    with patch.object(sys, 'argv', argv), patch.object(p.getpass, 'getpass', prompt or (lambda *_: sim.FIXTURE_TOKEN)), \
         patch.object(p.urllib.request, 'build_opener', return_value=types.SimpleNamespace(open=api.open)):
        p.main()


def test_authoritative_frontier_rejects_old_omitted_alternative_and_foreign_journals():
    for failed in (False, True):
        with tempfile.TemporaryDirectory() as td:
            plan = sim.plan(td); api = sim.API(plan)
            boot = sim.execute(plan, api, td, 'bootstrap')
            activate = sim.execute(plan, api, td, 'activate', boot)
            if failed:
                ledger = p.Ledger(plan, Path(td,'happy.jsonl'), 'happy', activate)
                ledger.charge('GET'); ledger.emit('phase_halt', result='fixture-failure'); ledger.close()
                happy = Path(td,'happy.jsonl')
            else: happy = sim.execute(plan, api, td, 'happy', activate)
            latest = p.Ledger.verify(happy, p.digest(plan))[-1]['counts']
            copied = Path(td,'alternative.jsonl'); copied.write_bytes(happy.read_bytes())
            for previous in (boot, activate, copied, None):
                for phase in ('lost-after', 'inspect', 'takeover'):
                    rejects(ValueError, lambda: p.Ledger(plan, Path(td,'new.jsonl'), phase, previous))
            # Actual CLI must reject before credential entry and before API.
            calls = len(api.trace)
            with patch.object(p, 'verify_code_pin', lambda _: None):
                rejects(ValueError, lambda: cli(plan, api, td, 'lost-after', activate,
                    prompt=lambda *_: (_ for _ in ()).throw(AssertionError('credential'))))
            assert len(api.trace) == calls
            ledger = p.Ledger(plan, Path(td,'inspect.jsonl'), 'inspect', happy)
            assert ledger.counts == latest
            ledger.emit('phase_halt', result='fixture-stop'); ledger.close()
            rejects(ValueError, lambda: p.Ledger(plan, Path(td,'takeover.jsonl'), 'takeover', happy))
            changed = deepcopy(plan); changed['repo'] = 'fixture/foreign'
            rejects(ValueError, lambda: p.Ledger(changed, Path(td,'foreign.jsonl'), 'inspect', Path(td,'inspect.jsonl')))


def test_cli_grant_expires_during_credentials_before_any_outbound():
    reset_clock()
    with tempfile.TemporaryDirectory() as td, patch.object(p, 'datetime', Clock):
        plan = sim.plan(td); api = sim.API(plan)
        boot = sim.execute(plan, api, td, 'bootstrap')
        grant = sim.fixture_grant(plan, 'activate', '2030-01-01T00:01:00Z')
        before = len(api.trace)
        def prompt(*_): Clock.current += timedelta(minutes=2); return sim.FIXTURE_TOKEN
        with patch.object(p, 'verify_code_pin', lambda _: None):
            rejects(ValueError, lambda: cli(plan, api, td, 'activate', boot, prompt, grant))
        rows = p.Ledger.verify(Path(td,'activate-cli.jsonl'), p.digest(plan))
        assert rows[-1]['event'] == 'phase_halt' and len(api.trace) == before
        assert not any(r['event'] == 'request' and r['phase'] == 'activate' for r in rows)


def test_preflight_expiry_exact_deadline_and_mutation_reservation_boundary():
    for place in ('preflight', 'before-put', 'after-reservation'):
        reset_clock()
        with tempfile.TemporaryDirectory() as td, patch.object(p, 'datetime', Clock):
            plan, api, _, ledger, client = started(td, expiry='2030-01-01T00:01:00Z')
            if place == 'preflight':
                original = api.open
                def expire_response(*a, **kw):
                    response = original(*a, **kw); Clock.current += timedelta(minutes=1); return response
                client.boundary.opener = expire_response
                rejects(ValueError, client.boundary.preflight)
                assert ledger.counts['PUT'] == 0
            else:
                client.boundary.preflight()
                original = ledger.checkpoint
                def checkpoint(point, event):
                    if point == 'after_publish' and event == 'request' and ledger.counts['PUT']:
                        Clock.current += timedelta(minutes=1)
                    original(point, event)
                if place == 'before-put': Clock.current += timedelta(minutes=1)
                else: ledger.checkpoint = checkpoint
                n = len(api.trace)
                rejects(ValueError, lambda: p.activation(client))
                assert not any(r[0] == 'PUT' for r in api.trace[n:])
                assert ledger.counts['PUT'] == (place == 'after-reservation')
            rejects(ValueError, lambda: ledger.emit('phase_end', result='confirmed'))
            ledger.close()


def test_timely_put_late_or_lost_response_has_no_readback_retry_or_completion():
    for lost in (False, True):
        reset_clock()
        with tempfile.TemporaryDirectory() as td, patch.object(p, 'datetime', Clock):
            plan, api, _, ledger, client = started(td, expiry='2030-01-01T00:01:00Z')
            client.boundary.preflight(); old = api.head; original = api.open
            def late(req, **kw):
                response = original(req, **kw)
                if req.method == 'PUT':
                    Clock.current += timedelta(minutes=1)
                    if lost: raise TimeoutError()
                return response
            client.boundary.opener = late
            rejects(ValueError, lambda: p.activation(client))
            assert api.head != old and ledger.counts['PUT'] == 1 and api.trace[-1][0] == 'PUT'
            calls = len(api.trace)
            rejects(ValueError, lambda: client.read(plan['repo'], plan['branch']))
            rejects(ValueError, lambda: ledger.emit('phase_end', result='confirmed'))
            assert len(api.trace) == calls
            ledger.emit('phase_halt', result='expired-without-completion'); ledger.close()
            rows = p.Ledger.verify(Path(td,'activate.jsonl'), p.digest(plan))
            assert rows[-2]['event'] == 'response' and rows[-1]['event'] == 'phase_halt'


def test_git_push_deadline_after_local_preparation_and_after_reply():
    for late in (False, True):
        reset_clock()
        with tempfile.TemporaryDirectory() as td, patch.object(p, 'datetime', Clock):
            plan = sim.plan(td); pins = p.build_bootstrap(plan, Path(td,'prepared'))
            plan.update(seed_commit=pins['seed_commit'], seed_sha256=pins['seed_sha256'])
            api = sim.API(plan); api.head = None
            ledger = p.Ledger(plan, Path(td,'bootstrap.jsonl'), 'bootstrap')
            guard = p.GrantGuard(plan, sim.fixture_grant(plan, 'bootstrap', '2030-01-01T00:01:00Z'), 'bootstrap')
            client = p.Client(p.Boundary(plan, ledger, 'fixture', 'fixture', api.open, guard=guard))
            pushes = []; original = subprocess.run
            def run(args, **kw):
                if 'push' not in args: return original(args, **kw)
                pushes.append(args); api.head = plan['seed_commit']; Clock.current += timedelta(minutes=1)
                raise subprocess.CalledProcessError(1, args)
            def checkpoint(point, event):
                if not late and point == 'before_outbound' and event == 'GIT_PUSH':
                    Clock.current += timedelta(minutes=1)
            ledger.checkpoint = checkpoint
            with patch.object(subprocess, 'run', run):
                rejects(ValueError, lambda: p.bootstrap(client, Path(td,'execution')))
            assert len(pushes) == int(late) and ledger.counts['GIT_PUSH'] == 1
            assert ledger.counts['GET'] == 6  # settings before root; no post-expiry history
            ledger.close()


def test_grant_plan_phase_review_binding_clock_rollback_and_restart_highwater():
    reset_clock()
    with tempfile.TemporaryDirectory() as td, patch.object(p, 'datetime', Clock):
        plan, api, boot, ledger, client = started(td)
        original = deepcopy(client.boundary.guard.grant)
        client.boundary.guard.grant['review_sha256'] = 'e'*64
        rejects(ValueError, lambda: client.boundary.request('GET', client.boundary.base))
        client.boundary.guard.grant = original
        rejects(ValueError, lambda: client.boundary.request('GET', client.boundary.base)) # sticky
        ledger.emit('phase_halt', result='fixture-stop'); ledger.close()
        Clock.current -= timedelta(seconds=1)
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'inspect.jsonl'), 'inspect', Path(td,'activate.jsonl')))
    reset_clock()
    with tempfile.TemporaryDirectory() as td, patch.object(p, 'datetime', Clock):
        plan, api, _, ledger, client = started(td, expiry='2030-01-01T00:01:00Z')
        with patch.object(p.time, 'monotonic', return_value=client.boundary.guard.started_mono+60):
            rejects(ValueError, lambda: client.boundary.request('GET', client.boundary.base))
        assert ledger.counts['GET'] == 16
        ledger.close()


def test_uncertain_fsync_or_frontier_publication_never_reaches_transport():
    for point in ('before_commit', 'after_commit', 'after_mirror', 'after_publish', 'fsync'):
        with tempfile.TemporaryDirectory() as td:
            plan, api, _, ledger, client = started(td)
            before = len(api.trace)
            def checkpoint(here, event):
                if here == point and event == 'request': raise OSError('fixture-durable-uncertainty')
            ledger.checkpoint = checkpoint
            if point == 'fsync':
                with patch.object(p.os, 'fsync', side_effect=OSError('fixture-fsync')):
                    rejects(OSError, lambda: client.boundary.request('GET', client.boundary.base))
            else: rejects(OSError, lambda: client.boundary.request('GET', client.boundary.base))
            rejects(ValueError, lambda: client.boundary.request('GET', client.boundary.base))
            assert len(api.trace) == before and ledger.poisoned
            ledger.close()
            rejects(ValueError, lambda: p.Ledger(plan, Path(td,'inspect.jsonl'), 'inspect', Path(td,'activate.jsonl')))


def kill_worker(td, point, event):
    def deny(*a, **kw): raise AssertionError('network denied in child')
    socket.socket.connect = socket.create_connection = p.urllib.request.urlopen = deny
    plan = sim.plan(td); api = sim.API(plan)
    Path(td,'plan.json').write_text(p.canonical(plan), encoding='utf-8')
    previous = sim.execute(plan, api, td, 'bootstrap') if event == 'next_phase_start' else None
    def checkpoint(self, here, what):
        if here == point and what == ('phase_start' if event == 'next_phase_start' else event): os._exit(71)
    def transport(*a, **kw):
        Path(td,'OUTBOUND').write_text('unexpected', encoding='utf-8'); return api.open(*a, **kw)
    with patch.object(p.Ledger, 'checkpoint', checkpoint):
        phase = 'activate' if previous else 'bootstrap'
        ledger = p.Ledger(plan, Path(td,phase+'.jsonl'), phase, previous)
        boundary = sim.boundary(plan, ledger, 'fixture', 'fixture', transport)
        boundary.request('GET', boundary.base)
    raise AssertionError('kill point not hit')


def test_hard_process_loss_at_frontier_and_request_boundaries_preserves_reservations():
    for event in ('phase_start', 'request'):
        for point in ('before_commit', 'after_commit', 'after_mirror', 'after_publish', 'before_outbound'):
            if point == 'before_outbound' and event == 'phase_start': continue
            target = 'GET' if point == 'before_outbound' else event
            with tempfile.TemporaryDirectory() as td:
                process = subprocess.Popen([sys.executable, str(Path(__file__)), '--kill', td, point, target],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                assert process.wait(timeout=60) == 71, process.stderr.read().decode()
                assert not Path(td,'OUTBOUND').exists()
                db = sqlite3.connect(str(Path(td,'probe-session.sqlite3')))
                rows = [json.loads(r[0]) for r in db.execute('SELECT body FROM events ORDER BY seq')]; db.close()
                count = sum(r['event'] == 'request' for r in rows)
                assert count == int(event == 'request' and point != 'before_commit')
                plan = json.loads(Path(td,'plan.json').read_text())
                for phase in ('bootstrap', 'inspect', 'takeover'):
                    rejects(ValueError, lambda: p.Ledger(plan, Path(td,'new.jsonl'), phase,
                            Path(td,'bootstrap.jsonl') if phase != 'bootstrap' else None))


def test_kernel_exclusivity_is_shared_by_probe_inspect_and_takeover():
    with tempfile.TemporaryDirectory() as td:
        plan, api, boot, ledger, client = started(td)
        planfile = Path(td,'plan.json'); planfile.write_text(p.canonical(plan), encoding='utf-8')
        script = """import json,sys;from pathlib import Path
sys.path.insert(0,sys.argv[1]);import p3_github_probe as p
plan=json.loads(Path(sys.argv[2]).read_text())
try:p.Ledger(plan,Path(sys.argv[2]).parent/'competing.jsonl',sys.argv[3],sys.argv[4])
except (OSError,ValueError):sys.exit(0)
sys.exit(9)
"""
        for phase in ('lost-after', 'inspect', 'takeover'):
            result = subprocess.run([sys.executable, '-c', script, str(ROOT/'tools'), str(planfile), phase,
                                     str(ledger.path)], capture_output=True, timeout=60)
            assert result.returncode == 0, result.stderr.decode()
            assert not Path(td,'competing.jsonl').exists()
        ledger.close()


def test_hard_loss_before_next_phase_frontier_cannot_reuse_old_confirmed_frontier():
    with tempfile.TemporaryDirectory() as td:
        process = subprocess.Popen([sys.executable, str(Path(__file__)), '--kill', td,
                                    'before_commit', 'next_phase_start'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        assert process.wait(timeout=60) == 71, process.stderr.read().decode()
        plan = json.loads(Path(td,'plan.json').read_text()); boot = Path(td,'bootstrap.jsonl')
        assert p.Ledger.verify(boot, p.digest(plan))[-1]['event'] == 'phase_end'
        assert Path(td,'attempt-activate.json').exists() and not Path(td,'OUTBOUND').exists()
        for phase in ('activate', 'inspect', 'takeover'):
            rejects(ValueError, lambda: p.Ledger(plan, Path(td,'alternative.jsonl'), phase, boot))


def test_reviewed_inspection_cannot_hide_interrupted_phase_or_reset_takeover_budget():
    import p3_probe_launcher as launcher
    with tempfile.TemporaryDirectory() as td:
        process = subprocess.Popen([sys.executable, str(ROOT/'engine/test_p3_github_probe.py'), '--worker', td],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        assert process.wait(timeout=60) == 23, process.stderr.read().decode()
        plan = json.loads(Path(td,'plan.json').read_text()); journal = Path(td,'process-loss.jsonl')
        term = launcher.observe_exit(process, plan, journal)
        review = {'expected_owner': term['owner'], 'expected_revision': term['revision'],
                  'expected_commit': term['commit'], 'termination': term,
                  'evidence': {'old_owner': term['owner'], 'reviewer': 'fixture', 'evidence_sha256': 'e'*64,
                               'run_completed': True, 'workers_terminated': True, 'triggers_paused': True}}
        saved = json.loads(Path(td,'api.json').read_text()); api = sim.API(plan)
        api.head, api.records = saved['head'], saved['records']
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'inspect.jsonl'), 'inspect', journal))
        ledger = p.Ledger(plan, Path(td,'inspect.jsonl'), 'inspect', journal, reviewed_termination=review)
        client = p.Client(sim.boundary(plan, ledger, 'fixture', '', api.open))
        client.boundary.preflight(); p.verify_history(client)
        ledger.emit('phase_end', result='confirmed'); total = dict(ledger.counts); ledger.close()
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'lost-after.jsonl'), 'lost-after', Path(td,'inspect.jsonl')))
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'takeover.jsonl'), 'takeover', journal,
                                          reviewed_termination=review))
        ledger = p.Ledger(plan, Path(td,'takeover.jsonl'), 'takeover', Path(td,'inspect.jsonl'),
                          reviewed_termination=review)
        assert ledger.counts == total
        client = p.Client(sim.boundary(plan, ledger, 'fixture', 'fixture', api.open))
        client.boundary.preflight(); p.verify_history(client); p.takeover(client, review)
        assert ledger.counts['PUT'] == total['PUT']+1
        ledger.emit('phase_end', result='confirmed'); ledger.close()


def test_missing_central_frontier_and_legacy_files_never_create_fresh_budget():
    with tempfile.TemporaryDirectory() as td:
        plan = sim.plan(td)
        Path(td,'old.jsonl').write_text('old sealed journal', encoding='utf-8')
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'bootstrap.jsonl'), 'bootstrap'))
        assert not Path(td,'probe-session.sqlite3').exists()
    with tempfile.TemporaryDirectory() as td:
        plan = sim.plan(td); api = sim.API(plan)
        boot = sim.execute(plan, api, td, 'bootstrap')
        # Test-only disappearance, retaining the original DB under another name.
        Path(td,'probe-session.sqlite3').rename(Path(td,'preserved.sqlite3'))
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'new.jsonl'), 'bootstrap'))
        rejects(ValueError, lambda: p.Ledger(plan, Path(td,'activate.jsonl'), 'activate', boot))
        assert not Path(td,'probe-session.sqlite3').exists()


if __name__ == '__main__' and sys.argv[1:2] == ['--kill']:
    kill_worker(*sys.argv[2:])
