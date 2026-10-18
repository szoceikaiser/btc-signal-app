"""One explicitly reviewed bootstrap continuation; no network without --real.

The original plan/seed code identity and session remain authoritative. A separate
amendment pins this executor and the exact fully published first Reader-401.
No artifact in this module grants human authorization.
"""
import argparse
from copy import deepcopy
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import p3_github_probe as p

PHASE = p.READER401_PHASE
ORIGINAL_HEAD = 'b0b0386e51c62a35b7c18053edf284862479da54'
ORIGINAL_TREE = '81ef0047f94ea8fe99783e5b269254e6c7c8fd9a'
END_BASIS = 'terminal-reader401-plus-fresh-os-end-and-exclusive-lock'
EXTRA_PINS = {'tools/p3_reader401_continue.py', 'tools/p3_reader401_start.ps1',
              'tools/p3_github_probe.py', 'engine/github_delivery.py', 'engine/production_contract.py'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def template():
    return {'schema': 'p3-reader401-amendment-v1', 'phase': PHASE,
        'original_plan_sha256': None, 'original_grant': None,
        'original_code_head': ORIGINAL_HEAD, 'original_code_tree': ORIGINAL_TREE,
        'original_code_materialization': None,
        'execution_code': {'code_head': None, 'code_tree': None, 'code_pins': None},
        'predecessor': {'journal': 'bootstrap.jsonl', 'journal_sha256': None,
            'frontier_hash': None, 'frontier_rows': 5, 'highwater': None,
            'counts': {'GET': 1, 'PUT': 0, 'GIT_PUSH': 0},
            'database_sha256': None, 'marker_sha256': None, 'lock_sha256': None},
        'root': {'directory': None, 'files_sha256': None},
        'review': {'reviewer': None, 'evidence_sha256': None, 'original_pid': None,
            'observed_utc': None, 'end_basis': END_BASIS, 'terminal_code_path_checked': False,
            'all_workers_ended': False, 'triggers_paused': False, 'human_review': False},
        'scope': 'same-plan-same-root-one-continuation-no-PUT-no-later-phase',
        'expires_utc': None}


def parse_utc(value):
    p.require(isinstance(value, str) and value.endswith('Z'), 'Explicit UTC required')
    return p.datetime.fromisoformat(value.replace('Z', '+00:00'))


def git(directory, *args):
    env = p.git_environment()
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_OPTIONAL_LOCKS='0')
    return subprocess.check_output(['git', '-c', 'safe.directory='+Path(directory).as_posix(),
        '-C', str(directory), *args], env=env, stderr=subprocess.DEVNULL, timeout=15)


def original_materialization(plan):
    """Describe exact historical Git-to-working bytes; this is not an approval."""
    result = {}
    for name, expected in plan['code_pins'].items():
        p.require('\\' not in name and '..' not in Path(name).parts
                  and not Path(name).is_absolute(), 'Invalid original code path')
        raw = git(p.ROOT, 'show', ORIGINAL_HEAD+':'+name)
        canonical = hashlib.sha256(raw).hexdigest()
        transform = 'identity'
        if canonical != expected:
            p.require(b'\r' not in raw and hashlib.sha256(raw.replace(b'\n', b'\r\n')).hexdigest() == expected,
                      'Historical working bytes cannot be proved')
            transform = 'lf-to-crlf'
        result[name] = {'git_blob_sha256': canonical, 'working_sha256': expected, 'transform': transform}
    return result


def verify_original_code(plan, materialization):
    p.require(plan['code_head'] == ORIGINAL_HEAD and plan['code_tree'] == ORIGINAL_TREE,
              'Only the reviewed original executor is eligible')
    p.require(git(p.ROOT, 'rev-parse', ORIGINAL_HEAD+'^{tree}').decode().strip() == ORIGINAL_TREE,
              'Original Git tree unavailable')
    p.require('tools/p3_github_probe.py' in plan['code_pins'], 'Original probe file pin missing')
    p.require(materialization == original_materialization(plan),
              'Explicit historical Git/working-byte materialization binding differs')


def root_files(directory):
    root = Path(directory)
    p.require(root.is_absolute() and root.is_dir() and root.resolve() == root.absolute(),
              'Existing exact local root directory required')
    entries = list(root.rglob('*'))
    p.require(not any(entry.is_symlink() for entry in entries), 'Root symlink forbidden')
    return {f.relative_to(root).as_posix(): sha(f) for f in entries if f.is_file()}


def verify_root(plan, directory):
    """Read local objects only; never init, repair, update-ref or fetch."""
    root = Path(directory); files = root_files(root)
    p.require('objects/info/alternates' not in files, 'External object alternates forbidden')
    seed = plan['seed_commit']
    p.require(git(root, 'rev-list', '--parents', seed).decode().strip() == seed,
              'Exact parentless root required')
    p.require(git(root, 'for-each-ref', '--format=%(objectname) %(refname)').decode().strip()
              == seed+' refs/heads/'+plan['branch'], 'Exact sole root branch required')
    p.require(git(root, 'ls-tree', '-r', '--name-only', seed).decode().strip() == plan['path'],
              'Root must contain sole authoritative path')
    body = git(root, 'show', seed+':'+plan['path'])
    p.require(body == p.synthetic_seed(plan) and hashlib.sha256(body).hexdigest() == plan['seed_sha256'],
              'Original seed bytes/code identity changed')
    settings = git(root, 'config', '--local', '--name-only', '--list').decode().splitlines()
    p.require(set(settings) <= {'core.repositoryformatversion', 'core.filemode', 'core.bare',
                               'core.symlinks', 'core.ignorecase'}, 'Unexpected local Git settings')
    p.require((root/'empty-hooks').is_dir() and not list((root/'empty-hooks').iterdir()), 'Empty hook directory required')
    return {'seed_commit': seed, 'seed_sha256': plan['seed_sha256'], 'seed_bytes': len(body)}


def root_matches(amendment):
    root = Path(amendment['root']['directory'])
    expected = amendment['root']['files_sha256']; actual = root_files(root)
    # The existing, reviewed ephemeral askpass path is the sole allowed addition.
    helpers = {
        'synthetic-askpass.py': "import os,sys\nprint('x-access-token' if 'username' in sys.argv[1].lower() else os.environ['P3_EXPLICIT_BOOTSTRAP_TOKEN'])\n",
        'synthetic-askpass.cmd': '@echo off\r\n"'+sys.executable+'" "'+str(root/'synthetic-askpass.py')+'" %*\r\n'}
    p.require(isinstance(expected, dict) and expected and not set(expected).intersection(helpers),
              'Original root manifest must precede askpass preparation')
    p.require(set(actual) <= set(expected) | set(helpers)
              and all(actual.get(name) == value for name, value in expected.items()), 'Reviewed root files changed')
    for name, body in helpers.items():
        if name in actual:
            # write_text uses native newline conversion, like the existing bootstrap.
            encoded = body.replace('\n', os.linesep).encode('utf-8')
            p.require(actual[name] == hashlib.sha256(encoded).hexdigest(), 'Askpass helper changed')


def process_ended(pid):
    """Fresh OS observation; errors and PID reuse fail closed, never a fake wait."""
    p.require(type(pid) is int and pid > 0 and pid != os.getpid(), 'Original process still present')
    if os.name == 'nt':
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = kernel.OpenProcess(0x100000, False, pid)  # SYNCHRONIZE only
        if not handle:
            p.require(ctypes.get_last_error() == 87, 'Process status unavailable')
            return 'currently-absent'
        try:
            p.require(kernel.WaitForSingleObject(handle, 0) == 0, 'Original PID alive or status unknown')
            return 'currently-signaled'
        finally: kernel.CloseHandle(handle)
    try: os.kill(pid, 0)
    except ProcessLookupError: return 'currently-absent'
    except OSError: raise ValueError('Process status unavailable') from None
    raise ValueError('Original PID still present')


def validate_chain(plan, rows, state, amendment):
    """Pure validation; may also examine preserved real snapshots without opening Ledger."""
    pred = amendment['predecessor']
    p.require(len(rows) == 5 and [r['event'] for r in rows]
              == ['phase_start', 'authorization', 'request', 'response', 'phase_halt'],
              'Only the complete first Reader-401 chain is eligible')
    p.require(all(r['phase'] == 'bootstrap' and r['run'] is None and r['plan_sha256'] == p.digest(plan)
                  and r['repository_id'] == plan['repository_id'] and r['branch'] == plan['branch']
                  and r['path'] == plan['path'] for r in rows), 'Foreign chain identity')
    p.require(rows[0]['journal'] == pred['journal'] == 'bootstrap.jsonl'
              and rows[0]['predecessor'] == '0'*64 and rows[2]['method'] == 'GET'
              and rows[3]['result'] == 'http-401' and rows[4]['result'] == 'incomplete-no-retry-no-release',
              'Not a known synchronous first Reader-401 halt')
    for i, row in enumerate(rows):
        p.require(row['counts'] == {'GET': int(i >= 2), 'PUT': 0, 'GIT_PUSH': 0}, 'Historical counters changed')
    p.require(all(rows[2].get(k) is None for k in ('old_blob', 'write_id', 'revision', 'parent_digest'))
              and rows[2]['bytes'] == 0, 'Unexpected mutation metadata')
    original_grant = amendment['original_grant']
    p.require(original_grant['plan_sha256'] == p.digest(plan) and original_grant['phase'] == 'bootstrap'
              and original_grant['human_authorization'] is True and original_grant['review_sha256'] is None
              and p.digest(original_grant) == rows[1]['grant_sha256']
              and rows[1]['grant_expires_utc'] == original_grant['expires_utc']
              and rows[1]['review_sha256'] is None and rows[1]['expiry_policy'] == plan['expiry_policy']
              and all(parse_utc(r['utc']) < parse_utc(original_grant['expires_utc']) for r in rows),
              'Original grant or outcome binding changed')
    p.require(pred['frontier_rows'] == 5 and pred['frontier_hash'] == rows[-1]['hash']
              and pred['counts'] == rows[-1]['counts'] and pred['highwater'] == rows[-1]['utc']
              and tuple(state) == (p.digest(plan), pred['journal'], pred['frontier_hash'], pred['highwater']),
              'Amendment does not bind authoritative frontier')
    review = amendment['review']
    p.require(review['original_pid'] == rows[0]['pid'] and review['end_basis'] == END_BASIS
              and all(review[k] is True for k in ('human_review', 'terminal_code_path_checked',
                                                  'all_workers_ended', 'triggers_paused'))
              and isinstance(review['reviewer'], str) and review['reviewer']
              and re.fullmatch('[0-9a-f]{64}', review['evidence_sha256'] or '')
              and parse_utc(rows[-1]['utc']) <= parse_utc(review['observed_utc']) <= p.datetime.now(p.timezone.utc),
              'Positive separately reviewed terminal process end required')


def validate_locked(ledger, rows, state, amendment):
    """Called under the common kernel lock, before any new durable phase intent."""
    pred = amendment['predecessor']; root = ledger.path.parent
    p.require(ledger.path.name == PHASE+'.jsonl', 'Fixed continuation journal required')
    validate_chain(ledger.p, rows, state, amendment)
    p.require((root/pred['journal']).read_bytes() == ''.join(p.canonical(r)+'\n' for r in rows).encode(),
              'Historical journal bytes must remain exact')
    for name, key in [(pred['journal'], 'journal_sha256'), ('probe-session.sqlite3', 'database_sha256'),
                      ('attempt-bootstrap.json', 'marker_sha256'), ('probe-session.lock', 'lock_sha256')]:
        if name == 'probe-session.lock':
            # Windows byte-range locks reject another handle, including our own.
            # Read through the handle that owns the lock; never unlock to hash.
            ledger.lock_handle.seek(0)
            actual = hashlib.sha256(ledger.lock_handle.read()).hexdigest()
            ledger.lock_handle.seek(0)
        else: actual = sha(root/name)
        p.require(actual == pred[key], 'Pinned predecessor file changed')
    p.require(not any((root/name).exists() for name in ('probe-session.sqlite3-wal', 'probe-session.sqlite3-journal')),
              'Unresolved database transaction')
    ledger.reader401_end_observation = process_ended(amendment['review']['original_pid'])
    root_matches(amendment)
    p.require(not (Path(amendment['root']['directory'])/'synthetic-askpass.py').exists()
              and not (Path(amendment['root']['directory'])/'synthetic-askpass.cmd').exists(), 'Prior push preparation exists')
    verify_root(ledger.p, amendment['root']['directory'])


class AmendmentGuard(p.GrantGuard):
    def __init__(self, plan, grant, amendment):
        self.amendment = deepcopy(amendment)
        self.amendment_hash = p.digest(amendment)
        super().__init__(plan, grant, PHASE)

    def check(self, ledger=None):
        super().check(ledger)
        p.require(p.digest(self.amendment) == self.amendment_hash == self.grant['review_sha256']
                  and self.amendment['original_plan_sha256'] == self.plan_hash
                  and p.datetime.now(p.timezone.utc) < parse_utc(self.amendment['expires_utc']),
                  'Amendment changed or expired')
        if ledger:
            p.require(ledger.reader401_hash == self.amendment_hash, 'Ledger amendment differs from live grant')
            root_matches(self.amendment)


def authorize(plan, amendment, grant, approved_amendment):
    p.validate_plan(plan)
    t = template()
    p.require(set(amendment) == set(t) and amendment['schema'] == t['schema']
              and amendment['scope'] == t['scope'] and amendment['phase'] == PHASE
              and amendment['original_plan_sha256'] == p.digest(plan)
              and amendment['original_code_head'] == ORIGINAL_HEAD and amendment['original_code_tree'] == ORIGINAL_TREE
              and approved_amendment == p.digest(amendment), 'Complete independently approved amendment required')
    for key in ('execution_code', 'predecessor', 'root', 'review'):
        p.require(set(amendment[key]) == set(t[key]), 'Incomplete amendment binding')
    p.require(set(grant) == {'schema', 'plan_sha256', 'phase', 'approved_by', 'human_authorization',
                          'expires_utc', 'approval_evidence_sha256', 'review_sha256'}
              and grant['schema'] == 'p3-human-grant-v2' and grant['phase'] == PHASE
              and grant['plan_sha256'] == p.digest(plan) and grant['review_sha256'] == approved_amendment
              and grant['human_authorization'] is True and isinstance(grant['approved_by'], str) and grant['approved_by']
              and re.fullmatch('[0-9a-f]{64}', grant['approval_evidence_sha256'] or ''), 'Separate human continuation grant required')
    p.require(parse_utc(grant['expires_utc']) <= parse_utc(amendment['expires_utc']),
              'Grant must end no later than amendment')
    guard = AmendmentGuard(plan, grant, amendment)
    verify_original_code(plan, amendment['original_code_materialization'])
    execution = amendment['execution_code']
    p.require(execution['code_head'] != ORIGINAL_HEAD
              and set(execution['code_pins']) >= set(plan['code_pins']) | EXTRA_PINS, 'New complete execution pins required')
    verify_execution_code(execution)
    return guard


def verify_execution_code(execution):
    p.verify_code_pin(execution)
    git(p.ROOT, 'merge-base', '--is-ancestor', ORIGINAL_HEAD, execution['code_head'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template'); parser.add_argument('--real', action='store_true')
    parser.add_argument('--plan'); parser.add_argument('--amendment'); parser.add_argument('--grant')
    parser.add_argument('--approved-amendment-sha256')
    args = parser.parse_args()
    if args.template:
        p.require(not args.real, 'Offline template only')
        with Path(args.template).open('x', encoding='utf-8') as f: f.write(json.dumps(template(), indent=2)+'\n')
        return
    p.require(args.real and all((args.plan, args.amendment, args.grant, args.approved_amendment_sha256)),
              'Default is offline; separately approved amendment and grant required')
    plan, amendment, grant = [json.loads(Path(name).read_text(encoding='utf-8-sig'))
                             for name in (args.plan, args.amendment, args.grant)]
    guard = authorize(plan, amendment, grant, args.approved_amendment_sha256)
    root = Path(plan['journal_directory'])
    # No mkdir, alternate journal directory, new plan or reset path.
    ledger = p.Ledger(plan, root/(PHASE+'.jsonl'), PHASE, root/amendment['predecessor']['journal'],
                      reader401_amendment=amendment)
    try:
        guard.check(ledger)
        reader = p.read_token('Reader'); writer = p.read_token('Writer')
        client = p.Client(p.Boundary(plan, ledger, reader, writer, guard=guard))
        ledger.emit('reader401_amendment', amendment_sha256=guard.amendment_hash,
                    execution_head=amendment['execution_code']['code_head'],
                    execution_tree=amendment['execution_code']['code_tree'],
                    original_code_head=plan['code_head'], original_pid=amendment['review']['original_pid'],
                    process_end_observation=ledger.reader401_end_observation,
                    predecessor_frontier=amendment['predecessor']['frontier_hash'],
                    result='reviewed-single-continuation')
        p.bootstrap(client, amendment['root']['directory'], reuse_reviewed_root=True)
        ledger.emit('phase_end', result='confirmed')
        print('Blocked-Root bestaetigt. Keine Aktivierung starten; Belege im Hauptchat pruefen lassen.')
    except BaseException:
        if not ledger.poisoned: ledger.emit('phase_halt', result='incomplete-no-retry-no-release')
        raise
    finally: ledger.close()


if __name__ == '__main__':
    try: main()
    except Exception:
        print('HALT: Fortsetzung nicht bestaetigt. Nicht erneut starten. Nur Status, keine Schluesselwerte melden.', file=sys.stderr)
        sys.exit(2)
