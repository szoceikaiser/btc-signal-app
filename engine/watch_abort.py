"""One owner-free aborted Watch, bound to the reviewed immutable Store state."""
from copy import deepcopy
import hashlib
from types import SimpleNamespace

from production_contract import canonical
import safe_recovery


SCHEMA = 'btc-watch-43880114205-abort-v1'
REPOSITORY = 'szoceikaiser/btc-delivery-store'
APP = 'szoceikaiser/btc-signal-app'
SOURCE = '9317b6018a282cf39d051680dd4811dcb38a45a1'
FENCE = '88b993ee2d41b61abb5a6e62c0f223356b4c7c32'
FENCE_HASH = '719acc738232f2a06344a15301b505459bb6cb4b4239cb738f7142bc59651fb9'
PREVIOUS = '2dc27ae1282cb73c13eb405cc6df8951522d4f0a'
PREVIOUS_HASH = '3e543bc67dafdb69ec194abd93fd2ed812740b1f93bbbd004869aafd9022c867'
STREAM = '5545e1bc6d17f0789b801d86338f6901ca2cc1b2'
STREAM_HASH = '00749b8873aa7972a653613f4e15ced96e6cf11d1a150915dc35560828a985ec'
REVISION = 4928
JOURNAL = 'bd578797a1a47757762f9eac3c237dc91c325653'
FENCE_BRANCH = 'delivery-fence-live'
STREAM_BRANCH = 'delivery-stream-live'
JOURNAL_BRANCH = 'recovery-journal-live'
RUN = '43880114205'
PRIOR_RUN = '43877691651'
JOB = '133343453642'
JOB_END = '2026-11-16T13:53:50Z'
DEADLINE = 1794838080000
WATCH = '.github/workflows/watch.yml'
WRITE_ID = 'watch-abort-43880114205-v1'


def require(ok):
    if not ok:
        raise ValueError('Watch abort evidence differs from the reviewed incident')


def marker(value):
    return 'watch_abort' in (value.get('completion') or {})


def proof(confirmed_at_ms):
    return dict(schema=SCHEMA, open_commit=FENCE, previous_commit=PREVIOUS,
                journal_commit=JOURNAL, source_commit=SOURCE, failed_run=RUN,
                failed_job=JOB, job_completed_at=JOB_END, confirmed_at_ms=confirmed_at_ms)


def body_hash(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def validate_marker(value):
    completion = value['completion']
    evidence = completion['watch_abort']
    confirmed_at_ms = evidence['confirmed_at_ms']
    require(type(confirmed_at_ms) is int and confirmed_at_ms > DEADLINE
            and evidence == proof(confirmed_at_ms)
            and value['phase'] == 'closed' and value['write_id'] == WRITE_ID
            and set(completion) == {'outcome', 'stream', 'watch_abort', 'old_write_id'}
            and completion['outcome'] == 'aborted'
            and value['run'] == dict(attempt='1', id=RUN, kind='watch', number=3730,
                                     workflow=WATCH, deadline_utc_ms=DEADLINE,
                                     expected_start_ms='1794837180000')
            and completion['stream']['commit_sha'] == STREAM)
    opened = {**value, 'phase': 'open', 'completion': None, 'write_id': completion['old_write_id']}
    require(body_hash(opened) == FENCE_HASH)


def validate_history(value, opened, previous):
    validate_marker(value)
    require(body_hash(opened) == FENCE_HASH and body_hash(previous) == PREVIOUS_HASH
            and previous['phase'] == 'closed' and previous['run']['id'] == PRIOR_RUN
            and previous['completion']['stream'] == value['completion']['stream'])


def validate_stream(value, record):
    from github_delivery import read_only

    deployment = value['deployment']
    require(record['commit_sha'] == STREAM
            and hashlib.sha256(record['body']).hexdigest() == STREAM_HASH
            and deployment['private_store_repository'] == REPOSITORY
            and deployment['store_branch'] == STREAM_BRANCH
            and deployment['fence_branch'] == FENCE_BRANCH)
    reader = SimpleNamespace(read=lambda *_: record)
    store = read_only(reader, REPOSITORY, STREAM_BRANCH, deployment['store_id'])
    require(store.confirmed_record() == value['completion']['stream'])
    health = store.snapshot['control']['health']
    run = health['successful_runs']['watch']['run']
    require(store.revision == REVISION and run['run_id'] == PRIOR_RUN)
    previous_run = dict(id=PRIOR_RUN, kind='watch', workflow=WATCH, attempt='1',
                        expected_start_ms='1794836280000')
    safe_recovery.completed(store._envelope, deployment, previous_run)


def candidate(opened, previous, record, confirmed_at_ms):
    closed = {**deepcopy(opened), 'phase': 'closed', 'write_id': WRITE_ID, 'completion': {
        'outcome': 'aborted', 'stream': deepcopy(previous['completion']['stream']),
        'old_write_id': opened['write_id'], 'watch_abort': proof(confirmed_at_ms),
    }}
    validate_history(closed, opened, previous)
    validate_stream(closed, record)
    return closed
