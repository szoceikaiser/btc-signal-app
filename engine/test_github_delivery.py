"""Local fake-API counterexamples for the unprovisioned GitHub store adapter."""
from contextlib import contextmanager
from copy import deepcopy
import base64
import hashlib
import io
import json
import os
import tempfile
from unittest.mock import patch

import durable_delivery as durable
import github_delivery as github
import telegram_outbox as box
from production_contract import canonical
from test_production_runtime import seeded


REPO = 'synthetic/private-store'
BRANCH = 'delivery-only'
STORE_ID = 'synthetic-store'


def fails(error, fn):
    try:
        fn()
    except error:
        return
    raise AssertionError('Expected '+str(error))


class FakeAPI:
    """A serial one-file branch with Contents SHA conflicts and Git parents."""

    def __init__(self, body):
        self.sequence = 0
        self.parents_by_commit = {}
        self.record = None
        self.put_count = 0
        self.fail_next = None
        self.stale_after_update = False
        self.stale_record = None
        self.missing = False
        self._set(body)

    def _set(self, body):
        self.sequence += 1
        prior = self.record['commit_sha'] if self.record else None
        commit = f'{self.sequence:040x}'
        blob = hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
        self.parents_by_commit[commit] = [] if prior is None else [prior]
        self.record = {'commit_sha': commit, 'blob_sha': blob, 'body': body}
        return commit

    def read(self, repo, branch, path):
        if self.missing:
            raise github.StoreUnavailable('404')
        if self.stale_record is not None:
            result, self.stale_record = self.stale_record, None
            return deepcopy(result)
        return deepcopy(self.record)

    def update(self, repo, branch, expected_blob_sha, body, write_id, path):
        self.put_count += 1
        mode, self.fail_next = self.fail_next, None
        if mode in ('403', '429', 'timeout_before'):
            raise github.StoreUnavailable(mode)
        if mode == '409' or expected_blob_sha != self.record['blob_sha']:
            raise github.StoreConflict('stale blob')
        old = deepcopy(self.record)
        commit = self._set(body)
        if self.stale_after_update:
            self.stale_record, self.stale_after_update = old, False
        if mode == 'timeout_after':
            raise github.StoreUnavailable('lost response')
        return commit

    def parents(self, repo, commit_sha):
        return self.parents_by_commit[commit_sha]

    def rewrite_history(self):
        # Administrator rewrite with identical bytes/blob, but a new parent.
        self.sequence += 1
        commit = f'{self.sequence:040x}'
        self.parents_by_commit[commit] = []
        self.record['commit_sha'] = commit

    def envelope(self):
        return json.loads(self.record['body'])


@contextmanager
def fake_store():
    with tempfile.TemporaryDirectory() as td:
        store_path, _, _ = seeded(td)
        with durable.VolumeStore(store_path, STORE_ID) as volume:
            snapshot = deepcopy(volume.snapshot)
        seed = json.loads(github.initial_envelope(snapshot, REPO, BRANCH, STORE_ID))
        seed['snapshot']['control']['mode'] = 'active'  # synthetic P4 transition
        seed['parent_digest'] = seed['body_digest']
        seed['body_digest'] = github._digest(seed['snapshot'])
        seed['revision'] += 1
        yield FakeAPI(canonical(seed).encode('utf-8'))


def new_store(api, attempt='1'):
    return github.GitHubStore(api, REPO, BRANCH, STORE_ID, 'run-100', attempt)


def stage_message(store):
    delivery = {'version': 1, 'messages': [], 'signals': {'signals': []}, 'oi_history': []}
    box.enqueue(delivery, 'test', 'synthetic-event', 0, {'text': 'synthetic'}, 'synthetic')
    store.snapshot['commands']['synthetic'] = {'_delivery': delivery, 'result': 'synthetic'}
    store.commit()  # Intent committed before transport.
    return store.snapshot['commands']['synthetic']['_delivery']['messages'][0]


def test_two_claims_use_one_remote_owner_and_checked_release():
    with fake_store() as api:
        first = new_store(api)
        first.__enter__()
        assert first.snapshot['control']['owner'] == first.owner
        fails(github.StoreConflict, lambda: new_store(api, '2').__enter__())
        first.__exit__(None, None, None)
        assert api.envelope()['snapshot']['control']['owner'] is None
        with new_store(api, '2') as second:
            assert second.owner != first.owner
        assert api.put_count == 4


def test_lost_put_response_resolved_only_by_exact_commit_and_parent():
    with fake_store() as api:
        api.fail_next = 'timeout_after'
        with new_store(api) as store:
            api.fail_next = 'timeout_after'
            message = stage_message(store)
            api.fail_next = 'timeout_after'
            message.update(status='sending', attempts=1, target=hashlib.sha256(b'target').hexdigest())
            store.commit()
            api.fail_next = 'timeout_after'
            message.update(status='confirmed', receipt=73)
            store.commit()
            assert store.revision == api.envelope()['revision']
            api.fail_next = 'timeout_after'  # release
        assert api.envelope()['snapshot']['commands']['synthetic']['_delivery']['messages'][0]['status'] == 'confirmed'
        assert api.envelope()['snapshot']['control']['owner'] is None


def test_timeout_before_put_and_stale_read_halt_without_retry():
    with fake_store() as api:
        api.fail_next = 'timeout_before'
        fails(github.StoreConflict, lambda: new_store(api).__enter__())
        assert api.put_count == 1 and api.envelope()['snapshot']['control'].get('owner') is None
    with fake_store() as api:
        api.stale_after_update = True
        fails(github.StoreConflict, lambda: new_store(api).__enter__())
        assert api.put_count == 1
        assert api.envelope()['snapshot']['control']['owner'] is not None


def test_stale_sha_owner_rewrite_and_old_history_stop_writer():
    with fake_store() as api:
        store = new_store(api).__enter__()
        old = api.envelope()
        old['snapshot']['control']['health']['external_change'] = 'synthetic'
        old['body_digest'] = github._digest(old['snapshot'])
        api._set(canonical(old).encode('utf-8'))
        store.snapshot['control']['health']['local_change'] = 'synthetic'
        fails(github.StoreConflict, store.commit)
        fails(github.StoreConflict, store.commit)  # poisoned after conflict
    with fake_store() as api:
        store = new_store(api).__enter__()
        api.rewrite_history()
        fails(github.StoreConflict, store.commit)


def test_terminated_owner_requires_evidence_and_sending_becomes_uncertain():
    with fake_store() as api:
        store = new_store(api).__enter__()
        message = stage_message(store)
        message.update(status='sending', attempts=1, target=hashlib.sha256(b'target').hexdigest())
        store.commit()
        owner, revision = deepcopy(store.owner), store.revision
        fails(github.StoreConflict, lambda: new_store(api, '2').__enter__())
        evidence = {'reviewer': 'synthetic-operator', 'evidence_sha256': 'a' * 64,
                    'old_owner': owner,
                    'run_completed': True, 'workers_terminated': True, 'triggers_paused': True}
        for key in ('run_completed', 'workers_terminated', 'triggers_paused'):
            bad = dict(evidence, **{key: False})
            fails(ValueError, lambda: github.review_takeover(api, REPO, BRANCH, STORE_ID,
                owner, revision, bad))
        fails(github.StoreConflict, lambda: github.review_takeover(api, REPO, BRANCH, STORE_ID,
            owner, revision-1, evidence))
        result = github.review_takeover(api, REPO, BRANCH, STORE_ID, owner, revision, evidence)
        assert result['converted_sending'] == 1
        envelope = api.envelope()
        assert envelope['snapshot']['control']['owner'] is None
        assert envelope['snapshot']['commands']['synthetic']['_delivery']['messages'][0]['status'] == 'uncertain'
        fails(github.StoreConflict, lambda: new_store(api, '2').__enter__())


def test_private_identity_404_403_429_and_no_local_fallback():
    with fake_store() as api:
        fails(ValueError, lambda: github.GitHubStore(api, 'wrong/repo', BRANCH, STORE_ID, 'run', '1').__enter__())
        fails(ValueError, lambda: github.GitHubStore(api, REPO, 'wrong', STORE_ID, 'run', '1').__enter__())
        fails(ValueError, lambda: github.GitHubStore(api, REPO, BRANCH, 'wrong', 'run', '1').__enter__())
        api.missing = True
        fails(github.StoreUnavailable, lambda: new_store(api).__enter__())
    for status in ('403', '429', '409'):
        with fake_store() as api:
            api.fail_next = status
            fails(github.StoreError, lambda: new_store(api).__enter__())
            assert api.envelope()['snapshot']['control'].get('owner') is None
    with tempfile.TemporaryDirectory() as td:
        env = {'BTC_DELIVERY_ADAPTER': 'github', 'BTC_DELIVERY_STORE': td,
               'BTC_DELIVERY_STORE_ID': STORE_ID, 'BTC_DELIVERY_RUNNER_ROOT': td}
        with patch.dict(os.environ, env):
            fails(ValueError, lambda: durable.configured_store(td))


def test_size_and_write_budget_keep_full_history_and_never_send():
    with fake_store() as api:
        store = new_store(api).__enter__()
        before = api.put_count
        store.snapshot['control']['health']['large'] = 'x' * github.MAX_BYTES
        fails(github.StoreUnavailable, store.commit)
        assert api.put_count == before
        store.snapshot['control']['health'].pop('large')
        store.writes = github.MAX_WRITES
        fails(github.StoreUnavailable, store.commit)
        assert api.put_count == before


def test_confirmed_remote_revision_survives_lost_runner_mirror():
    with fake_store() as api:
        with new_store(api) as store:
            message = stage_message(store)
            message.update(status='sending', attempts=1, target=hashlib.sha256(b'target').hexdigest())
            store.commit()
            message.update(status='confirmed', receipt=73)
            store.commit()
            revision = store.revision
            try:
                raise OSError('synthetic mirror lost')
            except OSError:
                pass
        assert api.envelope()['revision'] == revision + 1  # checked unlock
        with new_store(api, '2') as reopened:
            saved = reopened.snapshot['commands']['synthetic']['_delivery']['messages'][0]
            assert saved['status'] == 'confirmed' and saved['receipt'] == 73


def test_initial_envelope_is_blocked_and_cannot_bootstrap_runtime():
    with tempfile.TemporaryDirectory() as td:
        store_path, _, _ = seeded(td)
        with durable.VolumeStore(store_path, STORE_ID) as volume:
            body = github.initial_envelope(volume.snapshot, REPO, BRANCH, STORE_ID)
        api = FakeAPI(body)
        fails(ValueError, lambda: new_store(api).__enter__())
        assert api.put_count == 0


def test_rest_client_uses_pinned_commit_branch_and_previous_blob_sha_without_network():
    with fake_store() as api:
        seen = []
        def urlopen(request, timeout):
            seen.append(request)
            path = request.full_url
            if request.get_method() == 'PUT':
                payload = json.loads(request.data)
                assert payload['branch'] == BRANCH and payload['sha'] == api.record['blob_sha']
                assert base64.b64decode(payload['content']) == api.record['body']
                return io.BytesIO(json.dumps({'commit': {'sha': 'f' * 40}}).encode())
            if '/git/ref/heads/' in path:
                return io.BytesIO(json.dumps({'object': {'sha': api.record['commit_sha']}}).encode())
            if '/contents/' in path:
                assert 'ref=' + api.record['commit_sha'] in path
                return io.BytesIO(json.dumps({'type': 'file', 'encoding': 'base64',
                    'sha': api.record['blob_sha'],
                    'content': base64.b64encode(api.record['body']).decode()}).encode())
            if '/git/commits/' in path:
                return io.BytesIO(json.dumps({'parents': [{'sha': 'a' * 40}]}).encode())
            raise AssertionError('Unrecognized fake REST route')
        client = github.GitHubContentsClient('synthetic-secret')
        with patch('urllib.request.urlopen', side_effect=urlopen):
            record = client.read(REPO, BRANCH)
            assert record == api.record
            assert client.update(REPO, BRANCH, record['blob_sha'], record['body'], 'synthetic-write') == 'f' * 40
            assert client.parents(REPO, 'f' * 40) == ['a' * 40]
        assert len(seen) == 5
        assert all('synthetic-secret' not in request.full_url for request in seen)
