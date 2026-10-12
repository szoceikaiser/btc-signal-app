"""Explicit synthetic GitHub rehearsal. Import/default CLI are offline.

Real execution needs a complete plan, its independently approved digest and a
phase-specific human grant. Nothing in this module issues a grant.
"""
import argparse
import base64
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sqlite3
import time
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
import github_delivery as gh
import run_health
import telegram_outbox as box
from production_contract import canonical, digest, validate_v2, CANDLE_MS
from position_state import pos_to_state
from strategy_core import Position

SOURCE = '0ddd28b4db1679e4e5b89dc255ae500baa4c969c'
STORE = 'synthetic-p3-storeprobe-v1'
STREAM = 'synthetic-p3-stream-v1'
TARGET = hashlib.sha256(b'synthetic-p3-no-transport').hexdigest()
LIMITS = {'PUT': 48, 'GET': 384, 'GIT_PUSH': 1, 'mutations': 49,
          'run_puts': 12, 'case_puts': 12, 'case_gets': 128,
          'store_bytes': 768000, 'response_bytes': 2097152, 'timeout': 15}
READER401_PHASE = 'bootstrap-reader401-once'
RULES_DIAG = 'bootstrap-rules403-diagnose-once'
RULES_UPLOAD = 'bootstrap-rules403-upload-once'
RULES_RESUME = 'bootstrap-rules403-preget-once'
RULES_PHASES = (RULES_DIAG, RULES_UPLOAD, RULES_RESUME)
PUBLIC_ROOT = 'bootstrap-public-root-once'
PUBLIC_CONTINUE = 'bootstrap-public-missing-branch-once'
PUBLIC_ROOT_PHASES = (PUBLIC_ROOT, PUBLIC_CONTINUE)
BOOTSTRAP_PHASES = ('bootstrap', READER401_PHASE, *RULES_PHASES, *PUBLIC_ROOT_PHASES)
GIT_PHASES = ('bootstrap', READER401_PHASE, RULES_UPLOAD, *PUBLIC_ROOT_PHASES)
PHASES = ('bootstrap', 'activate', 'happy', 'lost-after', 'lost-before',
          'stale', 'process-loss', 'takeover', 'inspect')


def utc():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def template():
    return {'schema': 'p3-synthetic-probe-plan-v2', 'repo': None, 'repository_id': None,
        'branch': None, 'path': gh.STORE_PATH, 'store_id': STORE, 'stream_id': STREAM,
        'source_head': SOURCE, 'code_head': None, 'code_tree': None,
        'code_pins': None, 'seed_sha256': None, 'seed_commit': None,
        'credential_evidence_sha256': None, 'credential_repository_ids': None,
        'writer_permissions': {'contents': 'write', 'metadata': 'read'},
        'reader_permissions': {'contents': 'read', 'metadata': 'read',
                               'administration': 'read', 'pages': 'read'},
        'git_bootstrap_permissions': {'contents': 'write', 'metadata': 'read'},
        'limits': deepcopy(LIMITS), 'expected_rules': [],
        'bootstrap': 'single-root-git-push-blocked-seed',
        'phases': ['bootstrap', 'activate', 'happy', 'lost-after', 'process-loss', 'takeover', 'inspect'],
        'runs': [{'name': 'writer-'+str(i), 'run_id': 'synthetic-p3-'+str(i),
                  'run_attempt': str(1 if i % 2 else 2), 'nonce': None}
                 for i in range(1, 9)],
        'case_runs': {'activate': [0], 'happy': [1, 2], 'lost-after': [3, 4],
                      'lost-before': [5, 6], 'stale': [5, 6],
                      'process-loss': [5, 6], 'takeover': [7]},
        'takeover': None,
        'acknowledge_repo_credential_is_not_path_scope': True,
        'settings_and_other_writers_frozen': None,
        'journal_directory': None, 'expires_utc': None,
        'session_contract': 'sqlite-frontier-v2', 'expiry_policy': 'stop-all-outbound-no-grace'}


def validate_plan_structure(p):
    """Original immutable contract, including a well-formed historical deadline.

    This alone grants no current execution. Normal authorization also requires
    validate_plan; the exact Reader amendment proves its own current validity.
    """
    t = template()
    require(set(p) == set(t), 'Plan fields incomplete or unknown')
    require(p['schema'] == t['schema'] and p['source_head'] == SOURCE, 'Wrong source')
    require(isinstance(p['repo'], str) and re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+', p['repo'])
            and p['repo'].split('/')[1] not in ('.', '..'), 'Explicit repository required')
    require(type(p['repository_id']) is int and p['repository_id'] > 0, 'Repository ID required')
    b = p['branch']
    require(isinstance(b, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9/_-]*', b)
            and not b.endswith('/') and '//' not in b, 'Explicit valid branch required')
    for k in ('path', 'store_id', 'stream_id', 'limits', 'expected_rules', 'bootstrap',
              'writer_permissions', 'reader_permissions', 'git_bootstrap_permissions', 'case_runs',
              'session_contract', 'expiry_policy'):
        require(p[k] == t[k], 'Unsupported '+k)
    require(p['credential_repository_ids'] == [p['repository_id']], 'Credential must bind one repo')
    require(p['takeover'] is None, 'Takeover review is a separate later grant artifact')
    require(isinstance(p['journal_directory'], str) and Path(p['journal_directory']).is_absolute(),
            'Absolute dedicated local journal directory required')
    require(p['acknowledge_repo_credential_is_not_path_scope'] is True
            and p['settings_and_other_writers_frozen'] is True, 'Frozen settings and exclusive writers required')
    for k in ('code_head', 'code_tree', 'seed_commit'):
        require(isinstance(p[k], str) and re.fullmatch('[0-9a-f]{40}', p[k]), 'Missing pin '+k)
    for k in ('seed_sha256', 'credential_evidence_sha256'):
        require(isinstance(p[k], str) and re.fullmatch('[0-9a-f]{64}', p[k]), 'Missing digest '+k)
    require(isinstance(p['code_pins'], dict) and p['code_pins'], 'Code file pins required')
    require(isinstance(p['phases'], list) and len(p['phases']) == len(set(p['phases']))
            and all(x in PHASES for x in p['phases']), 'Invalid phase list')
    require(isinstance(p['runs'], list) and len(p['runs']) == 8, 'Exactly eight named run identities')
    for i, r in enumerate(p['runs']):
        require(set(r) == set(t['runs'][i]) and r['name'] == t['runs'][i]['name']
            and r['run_id'] == t['runs'][i]['run_id'] and r['run_attempt'] == t['runs'][i]['run_attempt']
            and isinstance(r['nonce'], str) and re.fullmatch('[0-9a-f]{32}', r['nonce']), 'Fixed synthetic run required')
    require(len({r['nonce'] for r in p['runs']}) == 8, 'Unique nonces required')
    require(isinstance(p['expires_utc'], str) and p['expires_utc'].endswith('Z')
            and datetime.fromisoformat(p['expires_utc'].replace('Z', '+00:00')).tzinfo == timezone.utc,
            'Plan expiry missing or invalid')
    return p


def validate_plan(p):
    validate_plan_structure(p)
    require(datetime.fromisoformat(p['expires_utc'].replace('Z', '+00:00')) > datetime.now(timezone.utc),
            'Plan expired or expiry missing')
    return p


def authorize(p, grant, phase, approved_digest):
    validate_plan(p)
    require(phase in p['phases'] and approved_digest == digest(p), 'Phase/independent plan pin mismatch')
    require(set(grant) == {'schema', 'plan_sha256', 'phase', 'approved_by', 'human_authorization',
                          'expires_utc', 'approval_evidence_sha256', 'review_sha256'}, 'Grant incomplete')
    require(grant['schema'] == 'p3-human-grant-v2' and grant['plan_sha256'] == approved_digest
            and grant['phase'] == phase and grant['human_authorization'] is True
            and isinstance(grant['approved_by'], str) and grant['approved_by']
            and re.fullmatch('[0-9a-f]{64}', grant['approval_evidence_sha256'] or '')
            and grant['expires_utc'].endswith('Z')
            and datetime.fromisoformat(grant['expires_utc'].replace('Z', '+00:00')) > datetime.now(timezone.utc),
            'Explicit human phase grant required')
    require((phase == 'takeover' and re.fullmatch('[0-9a-f]{64}', grant['review_sha256'] or ''))
            or (phase == 'inspect' and re.fullmatch('[0-9a-f]{64}', grant['review_sha256'] or ''))
            or (phase != 'takeover' and grant['review_sha256'] is None), 'Separate review grant required')
    guard = GrantGuard(p, grant, phase)
    verify_code_pin(p)
    return guard


def verify_code_pin(p):
    # Code identity is checked before any credential prompt or network operation.
    def git(*args):
        return subprocess.check_output(['git', '-c', 'safe.directory='+ROOT.as_posix(), '-C', str(ROOT), *args],
                                       stderr=subprocess.DEVNULL).decode().strip()
    require(git('rev-parse', 'HEAD') == p['code_head'] and git('rev-parse', 'HEAD^{tree}') == p['code_tree']
            and not git('status', '--porcelain', '--untracked-files=no'), 'Code pin or tracked worktree changed')
    for name, expected in p['code_pins'].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT) and path.is_file()
                and hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'Code file pin mismatch')


def synthetic_seed(p):
    """Fresh FLAT fixture, no production source, market input or migrated position."""
    config = {'muster_cvd': 'usd', 'bias_short': False, 'ausbruch_ruecktest': False}
    engine = pos_to_state(Position())
    engine.update(last_signal_ts=0, config=config,
                  _delivery={'version': 1, 'messages': [], 'signals': {'signals': []}, 'oi_history': []})
    control = {'store_id': STORE, 'stream_id': STREAM, 'mode': 'blocked', 'owner': None,
        'code_sha': p['code_head'], 'config_sha256': digest(config), 'target_binding': TARGET,
        'bot_identity': 'synthetic-no-bot', 'health': {}, 'reconciliations': [],
        'synthetic_probe': True,
        'migration': {'migration_id': 'synthetic-empty-no-import', 'B': 0, 'W': CANDLE_MS,
            'legacy_delivery': 'unknown_no_replay', 'history_sha256': digest({'signals': []}),
            'history_count': 0, 'source_hashes': {}, 'unknowns': [], 'gates': {}}}
    snapshot = {'version': 2, 'engine': engine, 'watch': {}, 'commands': {}, 'control': control}
    validate_v2(snapshot)
    env = json.loads(gh.initial_envelope(snapshot, p['repo'], p['branch'], STORE))
    env['write_id'] = 'synthetic-explicit-blocked-seed-v1'
    return canonical(env).encode()


def check_identity(p, body):
    probe = gh.GitHubStore(None, p['repo'], p['branch'], STORE, 'validation', '1')
    env = probe._parse({'body': body})
    c = env['snapshot']['control']
    require(c.get('synthetic_probe') is True and c['stream_id'] == STREAM
            and c['target_binding'] == TARGET and c['bot_identity'] == 'synthetic-no-bot'
            and c['code_sha'] == p['code_head'] and c['config_sha256'] == digest(
                {'muster_cvd': 'usd', 'bias_short': False, 'ausbruch_ruecktest': False}),
            'Only exact synthetic stream allowed')
    require(env['snapshot']['engine']['pos_state'] == 'FLAT'
            and not env['snapshot']['engine']['lots'], 'Synthetic empty position only')
    return env


class GrantGuard:
    """Bound approval, strict deadline, no network grace or clock rollback promise."""
    def __init__(self, p, grant, phase):
        self.plan_hash, self.grant_hash = digest(p), digest(grant)
        self.p, self.grant, self.phase = deepcopy(p), deepcopy(grant), phase
        require(grant['plan_sha256'] == self.plan_hash and grant['phase'] == phase
                and grant['schema'] == 'p3-human-grant-v2' and grant['human_authorization'] is True,
                'Grant not bound to actual plan/phase')
        self.started = self.last_wall = datetime.now(timezone.utc)
        self.started_mono = time.monotonic()
        self.expired = False
        self.check()

    def check(self, ledger=None):
        wall = datetime.now(timezone.utc)
        effective = max(wall, self.started + timedelta(seconds=time.monotonic()-self.started_mono))
        deadlines = self.deadlines()
        valid = (not self.expired and wall >= self.last_wall and all(effective < d for d in deadlines)
                 and digest(self.p) == self.plan_hash and digest(self.grant) == self.grant_hash)
        self.expired = not valid
        require(valid, 'Plan/grant expired, changed or clock moved backwards; no outbound grace')
        self.last_wall = wall
        if ledger:
            require(digest(ledger.p) == self.plan_hash and ledger.phase == self.phase,
                    'Live plan/phase differs from bound grant')
            ledger.check_time(wall)

    def deadlines(self):
        return [datetime.fromisoformat(x['expires_utc'].replace('Z', '+00:00'))
                for x in (self.p, self.grant)]


class Ledger:
    """One authoritative SQLite frontier + fsynced JSONL mirror + kernel lock.

    A request is reserved in SQLite FULL, mirrored with fsync, then acknowledged
    in SQLite FULL before outbound. Any uncertainty poisons this process and
    blocks every later opener. No automatic repair, resume or lock bypass.
    """
    def __init__(self, p, path, phase, previous=None, reviewed_termination=None, reader401_amendment=None,
                 rules403_amendment=None, public_root_amendment=None):
        self.p, self.path, self.phase = deepcopy(p), Path(path), phase
        self.counts = {'GET': 0, 'PUT': 0, 'GIT_PUSH': 0}
        self.cases, self.runs, self.run, self.phase_counts = {}, {}, None, {}
        self.previous_hash = '0'*64
        self.handle = self.db = self.lock_handle = None
        self.poisoned, self.guard = False, None
        require(self.path.parent.resolve() == Path(p['journal_directory']).resolve(), 'Journal directory pin mismatch')
        self.reader401_hash = digest(reader401_amendment) if reader401_amendment is not None else None
        self.rules403_hash = digest(rules403_amendment) if rules403_amendment is not None else None
        self.reader_validity_hash = (digest(rules403_amendment['reader_validity'])
            if isinstance(rules403_amendment, dict) and 'reader_validity' in rules403_amendment else None)
        self.public_root_hash = digest(public_root_amendment) if public_root_amendment is not None else None
        require((phase in p['phases'] and reader401_amendment is None and rules403_amendment is None)
                or (phase == READER401_PHASE and isinstance(reader401_amendment, dict) and rules403_amendment is None)
                or (phase in RULES_PHASES and isinstance(rules403_amendment, dict) and reader401_amendment is None)
                or (phase in PUBLIC_ROOT_PHASES and isinstance(public_root_amendment, dict)
                    and reader401_amendment is None and rules403_amendment is None),
                'Phase outside plan/review')
        require(public_root_amendment is None or phase in PUBLIC_ROOT_PHASES, 'Public review cannot authorize another phase')
        if phase in (READER401_PHASE, *RULES_PHASES, *PUBLIC_ROOT_PHASES):
            require(all((self.path.parent/name).is_file() for name in ('probe-session.sqlite3',
                'probe-session.lock', 'attempt-bootstrap.json', 'bootstrap.jsonl')), 'Existing session files required')
            require((self.path.parent/'probe-session.lock').stat().st_size > 0, 'Original lock bytes required')
            require(not any((self.path.parent/name).exists() for name in ('probe-session.sqlite3-wal',
                'probe-session.sqlite3-journal')), 'Unresolved session transaction')
            if phase in (*RULES_PHASES, *PUBLIC_ROOT_PHASES):
                require(all((self.path.parent/name).is_file() for name in
                    ('attempt-'+READER401_PHASE+'.json', READER401_PHASE+'.jsonl')), 'Original continuation files required')
        self.lock = self.path.parent/'probe-session.lock'
        self.database = self.path.parent/'probe-session.sqlite3'
        existed = self.lock.exists()
        self.lock_handle = self.lock.open('a+b')
        try:
            if self.lock.stat().st_size == 0:
                self.lock_handle.write(b'0'); self.lock_handle.flush(); os.fsync(self.lock_handle.fileno())
            self.lock_handle.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            new = not self.database.exists()
            if new:
                require(not existed and phase == 'bootstrap' and previous is None
                        and not list(self.path.parent.glob('*.jsonl'))
                        and not list(self.path.parent.glob('attempt-*')),
                        'Missing frontier/legacy session: no reset or automatic migration')
            self.db = sqlite3.connect(str(self.database), timeout=0, isolation_level=None)
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute('PRAGMA journal_mode=DELETE')
            if new:
                self.db.executescript('BEGIN IMMEDIATE; CREATE TABLE events (seq INTEGER PRIMARY KEY, body TEXT NOT NULL); '
                    'CREATE TABLE frontier (id INTEGER PRIMARY KEY CHECK(id=1), plan TEXT NOT NULL, '
                    'journal TEXT NOT NULL, published TEXT NOT NULL, highwater TEXT NOT NULL); COMMIT;')
                with self.transaction():
                    self.db.execute('INSERT INTO frontier VALUES (1,?,?,?,?)', (digest(p), '', '0'*64, utc()))
            state = self.db.execute('SELECT plan,journal,published,highwater FROM frontier WHERE id=1').fetchone()
            require(state and state[0] == digest(p), 'Foreign or incomplete session frontier')
            self.highwater = state[3]
            self.check_time(datetime.now(timezone.utc))
            rows = [json.loads(r[0]) for r in self.db.execute('SELECT body FROM events ORDER BY seq')]
            if rows:
                require(previous and Path(previous).resolve() == (self.path.parent/state[1]).resolve(),
                        'Predecessor is not authoritative latest session journal')
                require(self.verify(previous, digest(p)) == rows and state[2] == rows[-1]['hash'],
                        'Incomplete publication or journal/frontier mismatch; local review required')
                require(not any(r['event'] == 'phase_start' and r['phase'] == phase for r in rows),
                        'Phase already attempted; no replay with another filename')
                ended = {r['phase'] for r in rows if r['event'] == 'phase_end' and r.get('result') == 'confirmed'}
                halted = (any(r['event'] == 'phase_halt' for r in rows)
                          or any(r['event'] == 'phase_start' and r['phase'] not in ended for r in rows))
                terminal = rows[-1]['event'] in ('phase_end', 'phase_halt')
                if not terminal:
                    require(phase in ('takeover', 'inspect') and isinstance(reviewed_termination, dict),
                            'Interrupted frontier requires positive process-end review')
                if reviewed_termination is not None:
                    require(phase in ('takeover', 'inspect') and isinstance(reviewed_termination, dict),
                            'No boolean lock exception')
                    validate_termination(p, reviewed_termination, previous)
                if phase == 'takeover':
                    require(isinstance(reviewed_termination, dict), 'Separate exact termination review required')
                if phase not in ('takeover', 'inspect', READER401_PHASE, *RULES_PHASES, *PUBLIC_ROOT_PHASES):
                    require(not halted and rows[-1]['event'] == 'phase_end' and rows[-1].get('result') == 'confirmed',
                            'Incomplete predecessor; inspection/review only')
                if phase == 'activate':
                    require(rows[-1]['phase'] == 'bootstrap', 'Activation requires confirmed bootstrap')
                if phase in ('happy', 'lost-after', 'lost-before', 'stale', 'process-loss'):
                    require(any(r['event'] == 'activation' and r['result'] == 'confirmed-synthetic-only' for r in rows),
                            'Separately confirmed activation required')
                for row in rows:
                    if row['event'] == 'request': self._increment(row['method'], row['phase'], row.get('run'))
                self.previous_hash = rows[-1]['hash']
            else:
                require(new and previous is None, 'Incomplete initial frontier; no automatic retry')
            starts = [row for row in rows if row['event'] == 'phase_start']
            markers = list(self.path.parent.glob('attempt-*.json'))
            require({marker.name for marker in markers} == {'attempt-'+row['phase']+'.json' for row in starts},
                    'Unpublished phase attempt; no automatic restart')
            for row in starts:
                marker = json.loads((self.path.parent/('attempt-'+row['phase']+'.json')).read_text(encoding='utf-8'))
                require(marker == {key: row[key] for key in ('plan_sha256', 'phase', 'journal', 'pid', 'predecessor')},
                        'Phase attempt/frontier mismatch')
            if phase == READER401_PHASE:
                from p3_reader401_continue import validate_locked
                validate_locked(self, rows, state, reader401_amendment)
            if phase in RULES_PHASES:
                from p3_rules403 import validate_locked
                validate_locked(self, rows, state, rules403_amendment)
            if phase in PUBLIC_ROOT_PHASES:
                from p3_public_root import validate_locked
                validate_locked(self, rows, state, public_root_amendment)
                # The two historical Inspector reads also belong to this
                # reviewed bootstrap allowance; global counting already has all7.
                self.cases['bootstrap']['GET'] += self.cases.get('inspect', {}).get('GET', 0)
            self.prior_rows = rows
            # An interrupted phase start must not disappear behind a previously
            # confirmed frontier. A partial/extra intent permanently fails closed.
            require(not self.path.exists(), 'New journal filename required')
            with (self.path.parent/('attempt-'+phase+'.json')).open('x', encoding='utf-8') as marker:
                marker.write(canonical({'plan_sha256': digest(p), 'phase': phase, 'journal': self.path.name,
                                        'pid': os.getpid(), 'predecessor': self.previous_hash}))
                marker.flush(); os.fsync(marker.fileno())
            self.checkpoint('after_intent', 'phase_start')
            self.handle = self.path.open('x', encoding='utf-8', newline='\n')
            for row in rows: self.handle.write(canonical(row)+'\n')
            self.handle.flush(); os.fsync(self.handle.fileno())
            self.emit('phase_start', predecessor=self.previous_hash, pid=os.getpid(), journal=self.path.name)
        except BaseException:
            self.close()
            raise

    def transaction(self):
        # sqlite connection context manager does not BEGIN in autocommit mode.
        from contextlib import contextmanager
        @contextmanager
        def commit():
            self.db.execute('BEGIN IMMEDIATE')
            try: yield
            except BaseException:
                self.db.execute('ROLLBACK'); raise
            else: self.db.execute('COMMIT')
        return commit()

    def check_time(self, now):
        require(now >= datetime.fromisoformat(self.highwater.replace('Z', '+00:00')),
                'Clock behind durable session highwater')

    def checkpoint(self, point, event):
        """No-op fault seam used only by offline hard-process-loss tests."""

    def assert_published(self):
        require(not self.poisoned, 'Uncertain durable write; no outbound')
        state = self.db.execute('SELECT plan,journal,published FROM frontier WHERE id=1').fetchone()
        row = json.loads(self.db.execute('SELECT body FROM events ORDER BY seq DESC LIMIT 1').fetchone()[0])
        require(state == (digest(self.p), self.path.name, self.previous_hash)
                and row['hash'] == self.previous_hash and row['counts'] == self.counts,
                'Unpublished or changed frontier; no outbound')

    @staticmethod
    def verify(path, plan_digest):
        rows = []
        counts = {'GET': 0, 'PUT': 0, 'GIT_PUSH': 0}
        for line in Path(path).read_text(encoding='utf-8').splitlines():
            row = json.loads(line); h = row.pop('hash')
            require(digest(row) == h and row['plan_sha256'] == plan_digest, 'Journal corruption or foreign plan')
            if rows: require(row['previous_hash'] == rows[-1]['hash'], 'Journal hash chain broken')
            else: require(row['previous_hash'] == '0'*64, 'Complete cumulative journal root required')
            if row['event'] == 'request':
                require(row['method'] in counts, 'Unknown journal request')
                counts[row['method']] += 1
            require(row['counts'] == counts, 'Journal counters do not match attempted requests')
            row['hash'] = h; rows.append(row)
        require(bool(rows), 'Empty predecessor journal')
        return rows

    def _increment(self, method, phase, run):
        self.counts[method] += 1
        by_phase = self.phase_counts.setdefault(phase, {'GET': 0, 'PUT': 0, 'GIT_PUSH': 0})
        by_phase[method] += 1
        phase = 'bootstrap' if phase in BOOTSTRAP_PHASES else phase
        case = self.cases.setdefault(phase, {'GET': 0, 'PUT': 0, 'GIT_PUSH': 0})
        case[method] += 1
        if method == 'PUT' and run:
            key = canonical(run); self.runs[key] = self.runs.get(key, 0)+1

    def charge(self, method, **fields):
        if self.reader_validity_hash is not None or self.public_root_hash is not None:
            self.checkpoint('before_reservation', method)
            require(self.guard is not None, 'Reader validity needs bound guard before reservation')
            self.guard.check(self)
        self.assert_published()
        require(method in self.counts and self.counts[method] < LIMITS[method], 'Global request budget exhausted')
        require(self.phase not in BOOTSTRAP_PHASES or method != 'PUT', 'Bootstrap forbids PUT')
        if self.phase in PUBLIC_ROOT_PHASES:
            require(method in ('GET', 'GIT_PUSH') and self.phase_counts.get(self.phase, {}).get('GET', 0) < 23
                    and sum(self.phase_counts.get(x, {}).get('GET', 0) for x in PUBLIC_ROOT_PHASES) < 30,
                    'Public root request scope/budget exhausted')
        if self.phase in (RULES_DIAG, RULES_RESUME):
            attempted = sum(self.phase_counts.get(phase, {}).get('GET', 0) for phase in (RULES_DIAG, RULES_RESUME))
            require(method == 'GET' and attempted < 8,
                    'Diagnosis GET-only budget exhausted')
        budget_phase = 'bootstrap' if self.phase in BOOTSTRAP_PHASES else self.phase
        case = self.cases.get(budget_phase, {})
        if self.phase in (READER401_PHASE, *RULES_PHASES, *PUBLIC_ROOT_PHASES): fields['budget_phase'] = budget_phase
        if method in ('GET', 'PUT'):
            require(case.get(method, 0) < LIMITS['case_'+method.lower()+'s'], 'Case budget exhausted')
        if method != 'GET':
            require(self.counts['PUT']+self.counts['GIT_PUSH'] < LIMITS['mutations'], 'Mutation budget exhausted')
        if method == 'PUT':
            require(self.run is not None and self.runs.get(canonical(self.run), 0) < LIMITS['run_puts'], 'Run budget exhausted')
        self._increment(method, self.phase, self.run)
        self.emit('request', method=method, **fields)  # fsync BEFORE outbound request

    def emit(self, event, **fields):
        require(not self.poisoned, 'Uncertain journal/frontier write; local review required')
        if event == 'phase_end':
            require(self.guard is not None, 'Completion requires bound phase grant')
            self.guard.check(self)
        row = {'utc': utc(), 'repository_id': self.p['repository_id'], 'branch': self.p['branch'],
            'path': self.p['path'], 'phase': self.phase, 'run': self.run,
            'plan_sha256': digest(self.p), 'previous_hash': self.previous_hash,
            'counts': deepcopy(self.counts), 'event': event, **fields}
        row['hash'] = digest(row)
        try:
            self.checkpoint('before_commit', event)
            with self.transaction():
                if event == 'phase_end' and (self.reader_validity_hash is not None or self.public_root_hash is not None):
                    self.guard.check(self)
                self.db.execute('INSERT INTO events(body) VALUES (?)', (canonical(row),))
                self.highwater = max((self.highwater, row['utc']),
                    key=lambda value: datetime.fromisoformat(value.replace('Z', '+00:00')))
                self.db.execute('UPDATE frontier SET journal=?,highwater=? WHERE id=1', (self.path.name, self.highwater))
            self.checkpoint('after_commit', event)
            self.handle.write(canonical(row)+'\n'); self.handle.flush(); os.fsync(self.handle.fileno())
            self.checkpoint('after_mirror', event)
            with self.transaction():
                self.db.execute('UPDATE frontier SET published=? WHERE id=1', (row['hash'],))
            self.checkpoint('after_publish', event)
            self.previous_hash = row['hash']
            self.assert_published()
        except BaseException:
            self.poisoned = True
            raise

    def close(self):
        for name in ('handle', 'db', 'lock_handle'):
            handle = getattr(self, name, None)
            if handle is not None:
                handle.close(); setattr(self, name, None)
        # Kernel exclusivity ends on close/death; the durable open phase remains
        # blocked until positive process-end review. Never delete the lock file.


class HTTPStatus(gh.StoreUnavailable):
    def __init__(self, status, diagnostic=None):
        self.status = status
        self.diagnostic = diagnostic
        super().__init__('GitHub HTTP '+str(status))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Boundary:
    def __init__(self, p, ledger, reader, writer, opener=None, *, guard):
        self.p, self.ledger, self.reader, self.writer = p, ledger, reader, writer
        require(isinstance(guard, GrantGuard), 'Bound phase authorization required')
        self.guard = ledger.guard = guard
        self.guard.check(ledger)
        self.opener = opener or urllib.request.build_opener(NoRedirect()).open
        self.base = gh.GitHubContentsClient._route(p['repo'], '')
        self.allowed = False
        self.fault = None
        ledger.emit('authorization', grant_sha256=guard.grant_hash,
                    grant_expires_utc=guard.grant['expires_utc'], review_sha256=guard.grant['review_sha256'],
                    expiry_policy=p['expiry_policy'])

    def request(self, method, route, payload=None):
        self.guard.check(self.ledger)
        require(digest(self.p) == self.guard.plan_hash, 'Boundary plan changed')
        if self.ledger.phase in RULES_PHASES:
            from p3_rules403 import RulesGuard
            require(isinstance(self.guard, RulesGuard), 'Bound rules review required')
            self.guard.validate_route(method, route)
        if self.ledger.phase in PUBLIC_ROOT_PHASES:
            from p3_public_root import PublicGuard
            require(isinstance(self.guard, PublicGuard), 'Bound public root guard required')
            self.guard.validate_route(method, route)
        require(method != 'PUT' or self.ledger.phase not in ('inspect', *BOOTSTRAP_PHASES), 'Phase cannot PUT')
        require(route.startswith(self.base+'/') or route == self.base, 'Foreign repository route')
        require(method == 'GET' or (method == 'PUT' and self.allowed
                and route == self.base+'/contents/'+gh.STORE_PATH), 'Unapproved request')
        fields = {'bytes': 0, 'write_id': None, 'old_blob': None, 'revision': None,
                  'parent_digest': None}
        if self.ledger.phase in (*RULES_PHASES, *PUBLIC_ROOT_PHASES): fields['route'] = route
        if method == 'PUT':
            require(set(payload) == {'message', 'content', 'sha', 'branch'}
                    and payload['branch'] == self.p['branch'] and payload['sha'], 'No runtime bootstrap')
            body = base64.b64decode(payload['content'], validate=True)
            env = check_identity(self.p, body)
            require(len(body) <= LIMITS['store_bytes'], 'Store body limit')
            fields.update(bytes=len(body), write_id=env['write_id'], old_blob=payload['sha'],
                          revision=env['revision'], parent_digest=env['parent_digest'])
        self.ledger.charge(method, **fields)
        req = urllib.request.Request('https://api.github.com'+route,
            data=None if payload is None else canonical(payload).encode(), method=method,
            headers={'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json',
                'Authorization': 'Bearer '+(self.writer if method == 'PUT' else self.reader),
                'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'p3-synthetic-probe'})
        fault = self.fault if method == 'PUT' else None
        if method == 'PUT': self.fault = None
        self.before_outbound(method)
        try:
            if fault == 'before': raise TimeoutError()
            with self.opener(req, timeout=LIMITS['timeout']) as resp:
                raw = resp.read(LIMITS['response_bytes']+1)
                require(len(raw) <= LIMITS['response_bytes'], 'Response limit')
                status = resp.status
                require(status in (200, 201), 'Unexpected HTTP status')
                require(self.ledger.phase not in PUBLIC_ROOT_PHASES or status == 200, 'Public root GET needs positive200')
                value = json.loads(raw)
            if fault == 'after': raise TimeoutError()
        except urllib.error.HTTPError as exc:
            diagnostic = None
            if self.ledger.phase in (*RULES_PHASES, *PUBLIC_ROOT_PHASES):
                from p3_http_diagnostics import classify
                diagnostic = classify(exc, protection_context=(self.ledger.phase in PUBLIC_ROOT_PHASES
                    and getattr(self, 'public_protection_checked', False)
                    and route == self.base+'/branches/'+urllib.parse.quote(self.p['branch'],safe='')+'/protection'))
            self.ledger.emit('response', result='http-'+str(exc.code),
                             **({'diagnostic': diagnostic} if diagnostic is not None else {}), **fields)
            self.guard.check(self.ledger)
            if exc.code == 409: raise gh.StoreConflict('CAS conflict') from None
            raise HTTPStatus(exc.code, diagnostic) from None
        except (TimeoutError, OSError, urllib.error.URLError):
            self.ledger.emit('response', result='unknown', **fields)
            self.guard.check(self.ledger)
            raise gh.StoreUnavailable('Request outcome unknown') from None
        except Exception:
            self.ledger.emit('response', result='invalid-or-overbudget', **fields)
            self.guard.check(self.ledger)
            raise gh.StoreUnavailable('Invalid bounded response') from None
        self.ledger.emit('response', result='http-'+str(status), response_bytes=len(raw), **fields)
        self.guard.check(self.ledger)
        return value

    def before_outbound(self, method):
        self.ledger.checkpoint('before_outbound', method)
        self.ledger.assert_published()
        require(digest(self.p) == self.guard.plan_hash, 'Boundary plan changed')
        require(method != 'GIT_PUSH' or self.ledger.phase in GIT_PHASES, 'Bootstrap phase required')
        if self.ledger.phase in PUBLIC_ROOT_PHASES:
            from p3_public_root import PublicGuard
            require(isinstance(self.guard, PublicGuard), 'Bound public root guard required')
            require(method != 'GIT_PUSH' or self.guard.writer_authenticated, 'Writer authentication required before push')
            if method == 'GIT_PUSH': verify_code_pin(self.guard.a['execution_code'])
        self.guard.check(self.ledger)  # final check, after durable accounting/local prep

    def preflight(self, empty=False):
        r = self.request('GET', self.base)
        require(r.get('id') == self.p['repository_id'] and r.get('full_name') == self.p['repo']
                and r.get('private') is True and r.get('has_pages') is False
                and r.get('archived') is False and r.get('permissions', {}).get('admin') is True,
                'Repository/private/Pages/admin identity mismatch')
        require(self.request('GET', self.base+'/actions/permissions').get('enabled') is False,
                'Actions must be disabled')
        try: self.request('GET', self.base+'/pages')
        except HTTPStatus as exc: require(exc.status == 404, 'Pages inspection unavailable')
        else: raise ValueError('Pages site exists')
        branch = urllib.parse.quote(self.p['branch'], safe='')
        require(self.request('GET', self.base+'/rules/branches/'+branch+'?per_page=100&page=1') == [],
                'Unsupported effective branch rules')
        require(self.request('GET', self.base+'/rulesets?includes_parents=true&per_page=100&page=1') == [],
                'Unsupported repository/inherited rulesets')
        branches = self.request('GET', self.base+'/branches?per_page=100&page=1')
        require(branches == [] if empty else isinstance(branches, list) and len(branches) == 1
                and branches[0]['name'] == self.p['branch'] and branches[0]['protected'] is False,
                'Empty repo / sole unprotected branch required')
        if not empty:
            try: self.request('GET', self.base+'/branches/'+branch+'/protection')
            except HTTPStatus as exc: require(exc.status == 404, 'Branch protection inspection unavailable')
            else: raise ValueError('Unsupported classic branch protection')
        self.allowed = True
        self.ledger.emit('preflight', result='confirmed-private-frozen-settings')


class Client(gh.GitHubContentsClient):
    def __init__(self, boundary):
        self.boundary = boundary
        self.stale = None

    def _request(self, method, route, payload=None):
        return self.boundary.request(method, route, payload)

    def read(self, repo, branch, path=gh.STORE_PATH):
        require((repo, branch, path) == (self.boundary.p['repo'], self.boundary.p['branch'], gh.STORE_PATH),
                'Read identity mismatch')
        if self.stale is not None:
            value, self.stale = self.stale, None
            self.boundary.ledger.emit('fault', result='one-stale-local-read', commit=value['commit_sha'])
            return value
        record = super().read(repo, branch, path)
        check_identity(self.boundary.p, record['body'])
        self.boundary.ledger.emit('readback', result='observed-only', commit=record['commit_sha'],
            old_blob=record['blob_sha'], revision=json.loads(record['body'])['revision'], bytes=len(record['body']))
        return record

    def update(self, *args, **kwargs):
        p = self.boundary.p
        require(args[0:2] == (p['repo'], p['branch']), 'Write identity mismatch')
        return super().update(*args, **kwargs)

    def parents(self, repo, commit_sha):
        parents = super().parents(repo, commit_sha)
        self.boundary.ledger.emit('parent', result='observed-only', commit=commit_sha, parents=parents)
        return parents


def verify_history(client, full=False):
    p = client.boundary.p
    head = client.read(p['repo'], p['branch'])
    cursor = head['commit_sha']; rows = []
    prior = [r for r in client.boundary.ledger.prior_rows if r['event'] == 'history'
             and r['result'] == 'complete-blocked-root-confirmed']
    anchor = prior[-1] if prior and not full else None
    for _ in range(LIMITS['mutations']+1):
        record = client.read_at(p['repo'], cursor)
        env = check_identity(p, record['body'])
        commit = client._request('GET', client.boundary.base+'/git/commits/'+cursor)
        tree = client._request('GET', client.boundary.base+'/git/trees/'+commit['tree']['sha']+'?recursive=1')
        files = [(x['path'], x['type'], x.get('mode'), x['sha']) for x in tree['tree'] if x['type'] != 'tree']
        require(tree.get('truncated') is False and files == [(p['path'], 'blob', '100644', record['blob_sha'])],
                'Full store tree must contain only authoritative regular file')
        rows.append((cursor, env, record['body']))
        parents = [x['sha'] for x in commit['parents']]
        if anchor and cursor == anchor['commit']:
            require(hashlib.sha256(record['body']).hexdigest() == anchor['body_sha256']
                    and env['revision'] == anchor['revision'], 'Previously verified anchor changed')
            break
        if not parents:
            require(cursor == p['seed_commit'] and hashlib.sha256(record['body']).hexdigest() == p['seed_sha256']
                    and record['body'] == synthetic_seed(p) and env['revision'] == 0
                    and env['snapshot']['control']['mode'] == 'blocked', 'Exact blocked root required')
            break
        require(len(parents) == 1, 'Linear complete history required')
        cursor = parents[0]
    else: raise ValueError('History budget exhausted')
    for newer, older in zip(rows, rows[1:]):
        require(newer[1]['revision'] == older[1]['revision']+1
                and newer[1]['parent_digest'] == older[1]['body_digest'], 'Revision/digest chain mismatch')
    require(client.read(p['repo'], p['branch']) == head, 'History head moved')
    client.boundary.ledger.emit('history', result='complete-blocked-root-confirmed',
        commit=head['commit_sha'], revisions=rows[0][1]['revision']+1,
        revision=rows[0][1]['revision'], body_sha256=hashlib.sha256(head['body']).hexdigest(),
        independently_read_commits=len(rows), verified_anchor=anchor['commit'] if anchor else None)
    return head


def owner(p, index):
    r = p['runs'][index]
    return {'repository': p['repo'], **{k: r[k] for k in ('run_id', 'run_attempt', 'nonce')}}


def store_for(client, index):
    p = client.boundary.p; who = owner(p, index)
    client.boundary.ledger.run = who
    store = gh.GitHubStore(client, p['repo'], p['branch'], STORE, who['run_id'], who['run_attempt'])
    store.owner = who
    return store


def activation(client):
    p = client.boundary.p
    s = store_for(client, p['case_runs']['activate'][0])
    record, env = s._read()
    require(record['commit_sha'] == p['seed_commit'] and record['body'] == synthetic_seed(p),
            'Activation only from approved blocked seed')
    before = client.boundary.ledger.counts['PUT']
    try: s.__enter__()
    except ValueError: pass
    else: raise ValueError('Blocked claim unexpectedly succeeded')
    require(client.boundary.ledger.counts['PUT'] == before, 'Blocked gate wrote')
    client.boundary.ledger.emit('blocked_gate', result='denied-before-PUT')
    s._record, s._envelope, s.revision = record, env, env['revision']
    s.snapshot = deepcopy(env['snapshot']); s.snapshot['control']['mode'] = 'active'
    s._write()  # existing CAS/parent/readback contract, separate phase grant
    client.boundary.ledger.emit('activation', result='confirmed-synthetic-only', **s.confirmed_record())


def sequence(client, phase):
    p = client.boundary.p; ledger = client.boundary.ledger
    a, b = p['case_runs'][phase]
    first, second = store_for(client, a), store_for(client, b)
    # Both read before winner claims. Replay only the loser's observed read.
    ledger.run = first.owner
    start = client.read(p['repo'], p['branch'])
    ledger.run = second.owner
    require(client.read(p['repo'], p['branch']) == start, 'Contender start reads differ')
    ledger.run = first.owner
    if phase in ('lost-before', 'lost-after'):
        client.boundary.fault = 'before' if phase == 'lost-before' else 'after'
    first.__enter__()
    client.stale = deepcopy(start); ledger.run = second.owner
    before = ledger.counts['PUT']
    try: second.__enter__()
    except gh.StoreConflict: pass
    else: raise ValueError('Two owners accepted')
    require(ledger.counts['PUT'] == before+1, 'Stale loser must attempt exactly one CAS')
    ledger.emit('contender', result='stale-CAS-denied', owner=first.owner)
    ledger.run = first.owner
    slot = 2*CANDLE_MS + p['case_runs'][phase][0]*CANDLE_MS
    # Explicit environment bindings for existing run-health contract, no runner.
    keys = {'BTC_DELIVERY_RUN_REPOSITORY': p['repo'], 'BTC_DELIVERY_WORKFLOW': 'synthetic-local-signal',
        'BTC_DELIVERY_RUN_ID': first.owner['run_id'], 'BTC_DELIVERY_RUN_ATTEMPT': first.owner['run_attempt'],
        'BTC_DELIVERY_EXPECTED_START_MS': str(slot)}
    previous = {k: os.environ.get(k) for k in keys}
    os.environ.update(keys)
    try:
        run_health.record_event(first, 'signal', 'start', slot+1000, None)
        delivery = {'version': 1, 'messages': [], 'signals': {'signals': []}, 'oi_history': []}
        box.enqueue(delivery, 'probe', first.owner['run_id'], 0, {'text': 'synthetic-fixture-only'}, 'synthetic')
        first.snapshot['commands'][first.owner['run_id']] = {'_delivery': delivery, 'result': 'synthetic'}
        first.commit()
        m = delivery['messages'][0]
        m.update(status='sending', attempts=1, target=TARGET)
        if phase == 'stale': client.stale = deepcopy(first._record)
        first.commit()
        ledger.emit('sending', result='confirmed-no-transport', **first.confirmed_record())
        if phase == 'process-loss':
            ledger.emit('loss_boundary', result='sending-retained-no-completion')
            raise SystemExit(23)  # no __exit__, release or automatic restart
        m.update(status='confirmed', receipt=73)
        first.commit()
        first.snapshot['engine']['last_signal_ts'] = slot-CANDLE_MS
        run_health.record_event(first, 'signal', 'finish', slot+2000, None)
        bound = first.snapshot['control']['health']['successful_runs']['signal']
        require(first.read_revision(bound['completion'])['control']['health']['completion_candidate'] == bound['run']
                and bound['run']['nonce'] == first.owner['nonce'], 'Run completion binding mismatch')
        first.__exit__(None, None, None)
        require(client.read(p['repo'], p['branch'])['body'] == first._record['body']
                and first.snapshot['control']['owner'] is None, 'Release not confirmed')
        ledger.emit('run_completion', result='confirmed-synthetic-local-signal', binding=bound)
        ledger.run = second.owner
        with store_for(client, b): pass
        ledger.emit('sequence', result='confirmed-single-owner-fixture-release')
    finally:
        for k, v in previous.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def validate_termination(p, t, previous):
    require(isinstance(t, dict) and set(t) == {'expected_owner', 'expected_revision', 'expected_commit',
                                              'evidence', 'termination'}, 'Complete takeover review required')
    rows = Ledger.verify(previous, digest(p))
    term = t['termination']
    require(term['schema'] == 'p3-parent-wait-exit-v2' and term['plan_sha256'] == digest(p)
            and term['observed_wait'] is True and type(term['exit_code']) is int
            and type(term['pid']) is int and term['pid'] > 0
            and term['journal_name'] == Path(term['journal_name']).name
            and term['journal_sha256'] == hashlib.sha256((Path(previous).parent/term['journal_name']).read_bytes()).hexdigest(),
            'Positive parent wait receipt bound to exact journal required')
    original = Ledger.verify(Path(previous).parent/term['journal_name'], digest(p))
    require(rows[:len(original)] == original and term['frontier_hash'] == original[-1]['hash']
            and term['frontier_rows'] == len(original)
            and [r for r in original if r['event'] == 'phase_start'][-1]['pid'] == term['pid'],
            'Termination must bind exact phase PID and frontier prefix')
    sending = [r for r in rows if r['event'] == 'sending']
    require(sending and term['owner'] == t['expected_owner'] == sending[-1]['run']
            and term['revision'] == t['expected_revision'] == sending[-1]['revision']
            and term['commit'] == t['expected_commit'] == sending[-1]['commit_sha'],
            'Termination owner/revision/commit mismatch')
    e = t['evidence']
    require(e.get('old_owner') == t['expected_owner'] and e.get('reviewer')
            and re.fullmatch('[0-9a-f]{64}', e.get('evidence_sha256', ''))
            and all(e.get(k) is True for k in ('run_completed', 'workers_terminated', 'triggers_paused')),
            'Human worker/trigger review required')


def takeover(client, t):
    p = client.boundary.p
    evidence = t['evidence']
    require(re.fullmatch('[0-9a-f]{64}', evidence.get('evidence_sha256', ''))
            and evidence.get('old_owner') in [owner(p, i) for i in range(8)], 'Termination evidence binding')
    current = client.read(p['repo'], p['branch'])
    require(current['commit_sha'] == t['expected_commit'], 'Takeover commit changed')
    client.boundary.ledger.run = owner(p, 7)
    result = gh.review_takeover(client, p['repo'], p['branch'], STORE, t['expected_owner'],
                               t['expected_revision'], evidence)
    # Existing contract retains uncertain sending and forbids new claims.
    client.boundary.ledger.emit('takeover', result='confirmed-review-only', review=result)


def build_bootstrap(p, directory):
    """Local root preparation only. No remote; no default branch inference."""
    d = Path(directory); require(not d.exists(), 'Bootstrap directory must be new')
    d.mkdir(parents=True); hooks = d/'empty-hooks'; hooks.mkdir()
    env = git_environment()
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
        GIT_AUTHOR_NAME='Synthetic P3', GIT_AUTHOR_EMAIL='synthetic@invalid.example',
        GIT_COMMITTER_NAME='Synthetic P3', GIT_COMMITTER_EMAIL='synthetic@invalid.example',
        GIT_AUTHOR_DATE='2026-10-10T00:00:00Z', GIT_COMMITTER_DATE='2026-10-10T00:00:00Z')
    def git(*args, data=None):
        return subprocess.check_output(['git', '-c', 'safe.directory='+d.as_posix(),
            '-c', 'core.hooksPath='+hooks.as_posix(), '-C', str(d), *args], input=data, env=env,
            stderr=subprocess.DEVNULL, timeout=15).decode().strip()
    git('init', '--bare', '--initial-branch='+p['branch'])
    body = synthetic_seed(p)
    blob = git('hash-object', '-w', '--stdin', data=body)
    subtree = git('mktree', data=('100644 blob '+blob+'\tstream.json\n').encode())
    tree = git('mktree', data=('040000 tree '+subtree+'\tdelivery\n').encode())
    commit = git('commit-tree', tree, data=b'Explicit synthetic blocked seed\n')
    git('update-ref', 'refs/heads/'+p['branch'], commit)
    git('bundle', 'create', str(d/'blocked-seed.bundle'), 'refs/heads/'+p['branch'])
    require((d/'blocked-seed.bundle').stat().st_size <= LIMITS['response_bytes'], 'Bootstrap pack bound')
    return {'seed_commit': commit, 'seed_sha256': hashlib.sha256(body).hexdigest(), 'seed_bytes': len(body)}


def git_environment():
    # Names only: remove ambient Git overrides/credentials; never inspect values.
    return {k: v for k, v in os.environ.items()
            if not k.startswith(('GIT_', 'GH_', 'GITHUB_', 'BTC_DELIVERY_', 'TELEGRAM_'))}


def bootstrap(client, directory, *, reuse_reviewed_root=False, writer_prompt=None):
    p = client.boundary.p; ledger = client.boundary.ledger
    if reuse_reviewed_root:
        require((ledger.phase == READER401_PHASE and ledger.reader401_hash)
                or (ledger.phase == RULES_UPLOAD and ledger.rules403_hash), 'Reviewed root reuse only')
        from p3_reader401_continue import verify_root
        result = verify_root(p, directory)
    else:
        result = build_bootstrap(p, directory)
    require(result['seed_commit'] == p['seed_commit'] and result['seed_sha256'] == p['seed_sha256'],
            'Prepared root pin mismatch')
    client.boundary.preflight(empty=True)
    if writer_prompt is not None:
        require(ledger.phase == RULES_UPLOAD, 'Deferred Writer entry only for reviewed upload')
        client.boundary.writer = writer_prompt()
    require(client.boundary.writer, 'Dedicated bootstrap Contents credential required')
    askpass_py = Path(directory)/'synthetic-askpass.py'
    askpass_py.write_text("import os,sys\nprint('x-access-token' if 'username' in sys.argv[1].lower() else os.environ['P3_EXPLICIT_BOOTSTRAP_TOKEN'])\n", encoding='utf-8')
    askpass = Path(directory)/'synthetic-askpass.cmd'
    askpass.write_text('@echo off\r\n"'+sys.executable+'" "'+str(askpass_py)+'" %*\r\n', encoding='utf-8')
    env = git_environment()
    env.update(GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_ASKPASS=str(askpass), P3_EXPLICIT_BOOTSTRAP_TOKEN=client.boundary.writer)
    client.boundary.guard.check(ledger)
    ledger.charge('GIT_PUSH', write_id='synthetic-explicit-blocked-seed-v1', revision=0,
                  old_blob=None, parents=[], commit=result['seed_commit'], bytes=result['seed_bytes'])
    client.boundary.before_outbound('GIT_PUSH')
    try:
        # Exact new branch only; no force, tags, remote config, hooks or implicit credential search.
        subprocess.run(['git', '-c', 'safe.directory='+Path(directory).as_posix(),
            '-c', 'core.hooksPath='+str(Path(directory)/'empty-hooks'), '-C', str(directory),
            '-c', 'credential.helper=',
            '-c', 'http.followRedirects=false',
            'push', '--no-verify', '--porcelain', 'https://github.com/'+p['repo']+'.git',
            p['seed_commit']+':refs/heads/'+p['branch']], env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=True)
    except (subprocess.SubprocessError, OSError):
        ledger.emit('bootstrap_response', result='unknown-readback-only-if-grant-live')
    client.boundary.guard.check(ledger)
    verify_history(client)
    ledger.emit('bootstrap', result='confirmed-exact-blocked-root', **result)


def validate_token(value):
    # Shape only, no credential lookup/authentication, logging, trimming or repair.
    require(isinstance(value, str) and value.count('github_pat_') == 1
            and re.fullmatch(r'github_pat_[A-Za-z0-9_]{40,255}', value, flags=re.ASCII),
            'Ungueltiges Eingabeformat oder mehrfach eingefuegt. Kein Request gestartet; Wert nicht ausgeben.')
    return value


def read_token(role):
    print(role+': Genau EINMAL den vollstaendigen Fine-grained Token einfuegen, dann Enter. '
          'Keine Zeichen und keine Sternchen erscheinen; das ist normal.')
    return validate_token(getpass.getpass(role+' (unsichtbare Eingabe): '))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', metavar='NEW_FILE')
    parser.add_argument('--prepare-root', metavar='NEW_DIR')
    parser.add_argument('--plan'); parser.add_argument('--real', action='store_true')
    parser.add_argument('--grant'); parser.add_argument('--approved-plan-sha256')
    parser.add_argument('--phase', choices=PHASES); parser.add_argument('--journal')
    parser.add_argument('--previous-journal'); parser.add_argument('--bootstrap-dir')
    parser.add_argument('--termination-review')
    args = parser.parse_args()
    if args.template:
        require(not args.real and not args.plan, 'Template is offline only')
        with Path(args.template).open('x', encoding='utf-8') as f: f.write(json.dumps(template(), indent=2)+'\n')
        return
    if args.prepare_root:
        require(args.plan and not args.real, 'Offline preparation needs draft plan')
        p = json.loads(Path(args.plan).read_text(encoding='utf-8'))
        require(p['store_id'] == STORE and p['stream_id'] == STREAM
                and re.fullmatch('[0-9a-f]{40}', p['code_head'] or '')
                and isinstance(p['branch'], str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9/_-]*', p['branch'])
                and re.fullmatch('[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+', p['repo'] or ''), 'Draft target pins required')
        print(canonical(build_bootstrap(p, args.prepare_root))); return
    require(args.real and all((args.plan, args.grant, args.approved_plan_sha256, args.phase, args.journal)),
            'Default is offline; complete real execution plan and human phase grant required')
    p = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    grant = json.loads(Path(args.grant).read_text(encoding='utf-8'))
    guard = authorize(p, grant, args.phase, args.approved_plan_sha256)
    require(args.phase == 'bootstrap' or args.previous_journal, 'Cumulative predecessor ledger required')
    review = None
    if args.phase == 'takeover' or grant['review_sha256'] is not None:
        require(args.termination_review, 'Positive process end and exact owner/revision review required')
        review = json.loads(Path(args.termination_review).read_text(encoding='utf-8'))
        require(digest(review) == grant['review_sha256'], 'Unapproved termination review')
        validate_termination(p, review, args.previous_journal)
    ledger = Ledger(p, args.journal, args.phase, args.previous_journal, reviewed_termination=review)
    try:
        guard.check(ledger)
        reader = read_token('Reader')
        writer = '' if args.phase == 'inspect' else read_token('Writer')
        require(reader and (writer or args.phase == 'inspect'), 'Missing dedicated credentials')
        client = Client(Boundary(p, ledger, reader, writer, guard=guard))
        if args.phase == 'bootstrap':
            require(args.bootstrap_dir, 'New bootstrap directory required')
            bootstrap(client, args.bootstrap_dir)
        else:
            client.boundary.preflight(); verify_history(client)
            if args.phase == 'activate': activation(client)
            elif args.phase == 'takeover': takeover(client, review)
            elif args.phase != 'inspect': sequence(client, args.phase)
        ledger.emit('phase_end', result='confirmed')
    except BaseException:
        if not ledger.poisoned: ledger.emit('phase_halt', result='incomplete-no-retry-no-release')
        raise
    finally: ledger.close()


if __name__ == '__main__':
    try: main()
    except Exception:
        # No exception text/response bodies/credentials reach CLI output.
        print('HALT: incomplete or unapproved; inspect the bounded journal. No automatic retry.', file=sys.stderr)
        sys.exit(2)
