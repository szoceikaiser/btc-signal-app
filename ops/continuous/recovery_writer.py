"""Writer-only recovery entry, authenticated by recovery.yml."""
import hashlib
import json
import sys


def head(client, branch):
    return client._request('GET', client._route(client.repo, '/git/ref/heads/' + branch))['object']['sha']


def admit(client, fence, stream):
    """Reuse the writer's guards with one observation of each shared ruleset."""
    from types import SimpleNamespace
    import github_recovery as recovery

    cache = {}

    def request(method, route, payload=None):
        # Branch rule lists and all mutable worker observations remain distinct.
        prefix = client._route(client.repo, '')
        if method == 'GET' and payload is None and (route == prefix or route.startswith(prefix + '/rulesets/')):
            if route not in cache:
                cache[route] = client._request(method, route)
            return cache[route]
        return client._request(method, route, payload)

    def read(repo, branch, path=recovery.g.STORE_PATH):
        d = client.policy['deployment']
        recovery.safe.require((repo, branch, path) == (client.repo, d['store_branch'], recovery.g.STORE_PATH))
        return stream

    # verify_guards checks completion history against this exact snapshot.
    # The two live branch heads are independently read again before the CAS.
    class GuardView(SimpleNamespace):
        @property
        def _response_link(self):
            return getattr(client, '_response_link', '')

    guards = GuardView(policy=client.policy, repo=client.repo, code=client.code,
        clock=client.clock, self_run=client.self_run, _route=client._route, _request=request,
        read=read, is_ancestor=client.is_ancestor, read_at=client.read_at)
    return recovery.verify_guards(guards, fence, json.loads(stream['body']))


def read_incident(client, journal_head, path):
    import github_recovery as recovery

    try:
        record = client.read_at(client.repo, journal_head, path)
    except recovery.g.StoreHTTPFailure as exc:
        if str(exc) == 'GitHub store HTTP 404':
            return None
        raise
    return record['blob_sha'], json.loads(record['body'])


def run(client, identity):
    import github_recovery as recovery
    from production_contract import canonical, digest
    import secrets

    safe = recovery.safe
    policy = client.policy
    d = policy['deployment']
    j = policy['journal']
    safe.require(j['repository'] == client.repo and j['branch'] == 'recovery-journal-live'
        and j['reviewed'] is True and j['credential_reference'] == 'github-fine-grained-pat:21186996'
        and j['required_permissions'] == {'contents': 'write', 'metadata': 'read'})
    journal_head = head(client, j['branch'])
    safe.require(client.is_ancestor(client.repo, j['seed_commit'], journal_head))
    fence_record = client.read_at(client.repo, head(client, d['fence_branch']), recovery.actions.FENCE_PATH)
    fence = recovery.actions.parse_fence(fence_record, d)
    proof = (fence.get('completion') or {}).get('recovery')
    if fence['phase'] == 'closed' and proof is None:
        return {'phase': 'no-open-incident', 'writes': 0}
    stream = client.read_at(client.repo, head(client, d['store_branch']), recovery.g.STORE_PATH)
    envelope = recovery.g.GitHubStore(client, client.repo, d['store_branch'], d['store_id'], 'read-only', '1')._parse(stream)
    incident = proof['old_fence_commit'] if proof else fence_record['commit_sha']
    path = 'recovery/incidents/' + incident + '.json'
    previous = read_incident(client, journal_head, path)
    deadline = previous[1]['deadline_ms'] if previous else client.clock() + 900000
    policy_hash = digest(policy)
    safe.require(client.clock() < deadline)

    class AdmissionJournal(recovery.ContentsJournal):
        # The first CAS uses precisely the blob that was admitted. Its result
        # is still resolved by the original Journal.change transaction check.
        first_read = True
        acquisition = True

        def read(self, path):
            if self.first_read:
                self.first_read = False
                return previous
            if self.acquisition:
                return read_incident(client, head(client, j['branch']), path)
            return super().read(path)

        def cas(self, path, blob, value):
            if not self.acquisition:
                return super().cas(path, blob, value)
            safe.require(client.clock() < deadline)
            # The candidate already reserves 128 reads. Allow only the two
            # transaction readback GETs until that reservation is confirmed.
            try:
                return super().cas(path, blob, value)
            finally:
                journal.remaining = 2
                journal.lease = identity
                client.journal = journal

    transport = AdmissionJournal(client)
    journal = recovery.ledger.Journal(transport, incident, policy_hash, deadline, client.clock)
    initial = journal.read()
    transport.first_read = True
    state = initial[1] if initial else {}
    plan = state.get('plan')
    writes = state.get('writes', {})
    pin = lambda record: {key: value for key, value in record.items() if key != 'body'}
    original_fence, original_stream = fence, stream
    if plan is not None:
        original_fence = plan['fence_body']
        original_stream = {**plan['stream'], 'body': canonical(plan['stream_body']).encode()}
        # Verify the exact old bytes from Git before using them on a resumed run.
        if original_stream != stream:
            safe.require(client.read_at(client.repo, original_stream['commit_sha']) == original_stream)
        if proof:
            # safe.validate reconstructs this exact parent fence and verifies
            # its SHA-256, while the direct-parent read binds its Git commit.
            old_body = canonical(original_fence).encode()
            old_blob = hashlib.sha1(b'blob ' + str(len(old_body)).encode() + b'\0' + old_body).hexdigest()
            safe.require(plan['fence']['blob_sha'] == old_blob
                and proof['old_fence_sha256'] == hashlib.sha256(old_body).hexdigest())
        else:
            safe.require(pin(fence_record) == plan['fence'] and fence == original_fence)
        safe.require(plan['fence']['commit_sha'] == incident and original_fence['phase'] == 'open')
        if stream != original_stream:
            reserved = writes.get('stream', {})
            safe.require(plan['release'] is not None and reserved.get('old') == plan['stream']
                and reserved.get('body') == plan['release'] == envelope
                and reserved.get('status') in ('reserved', 'confirmed')
                and (reserved['status'] != 'confirmed' or reserved.get('commit_sha') == stream['commit_sha'])
                and client.parents(client.repo, stream['commit_sha']) == [plan['stream']['commit_sha']])
        else:
            safe.require('stream' not in writes)
    else:
        safe.require(not proof and not writes)

    if proof:
        reservation = writes.get('fence', {})
        safe.require(reservation.get('old') == plan['fence'] and reservation.get('body') == fence
            and reservation.get('status') in ('reserved', 'confirmed')
            and (plan['release'] is None or writes['stream']['status'] == 'confirmed')
            and client.parents(client.repo, fence_record['commit_sha']) == [incident])
        safe.validate(fence, envelope, recovery.locator(stream, envelope))
    else:
        # An open fence with an unresolved fence reservation cannot be retried.
        safe.require('fence' not in writes)

    meta, jobs = admit(client, original_fence, original_stream)
    if plan is None:
        review = dict(old_fence_commit=incident, old_fence_sha256=hashlib.sha256(fence_record['body']).hexdigest(),
            run_sha256=digest(meta), jobs_sha256=digest(jobs), policy_sha256=policy_hash,
            confirmed_at_ms=client.clock(), workers_terminated=True, run_completed=True)
        owner = envelope['snapshot']['control']['owner']
        release = event = None
        if owner is not None:
            review.update(old_owner=owner, old_revision=envelope['revision'],
                old_snapshot_digest=envelope['body_digest'], old_stream_commit=stream['commit_sha'])
            release, event = safe.release_owner(envelope, fence['run'], d, review, secrets.token_hex(16))
        plan = dict(fence=pin(fence_record), fence_body=fence, stream=pin(stream), stream_body=envelope,
            review=review, release=release, owner_event=event, close_write_id=secrets.token_hex(16))
    else:
        review = plan['review']
        safe.require(review['policy_sha256'] == policy_hash and review['old_fence_commit'] == incident
            and review['old_fence_sha256'] == hashlib.sha256(canonical(original_fence).encode()).hexdigest()
            and review['workers_terminated'] is True and review['run_completed'] is True)
        if plan['release'] is not None:
            original = json.loads(original_stream['body'])
            safe.require(all(review[key] == value for key, value in {
                'old_owner': original['snapshot']['control']['owner'], 'old_revision': original['revision'],
                'old_snapshot_digest': original['body_digest'], 'old_stream_commit': original_stream['commit_sha'],
            }.items()))
            release, event = safe.release_owner(original, original_fence['run'], d, review, plan['release']['write_id'])
            safe.require(release == plan['release'] and event == plan['owner_event'])

    if plan['release'] is None:
        close = safe.candidate(plan['fence_body'], envelope, recovery.locator(stream, envelope),
            plan['review'], plan['close_write_id'])
    elif proof:
        close = safe.owner_candidate(plan['fence_body'], envelope, recovery.locator(stream, envelope),
            plan['review'], plan['owner_event'], plan['close_write_id'])
    if proof:
        safe.require(close == fence)

    def check_heads():
        safe.require(head(client, d['fence_branch']) == fence_record['commit_sha']
            and head(client, d['store_branch']) == stream['commit_sha'])

    check_heads()
    # The incident blob read from journal_head is the CAS precondition.
    if proof and reservation['status'] == 'confirmed':
        safe.require(reservation['commit_sha'] == fence_record['commit_sha'])
        return dict(phase='already-confirmed-no-write', stream_commit=stream['commit_sha'],
                    fence_commit=fence_record['commit_sha'])
    journal.acquire(identity)
    journal.remaining -= 2
    transport.acquisition = False
    if proof:
        check_heads()
        journal.confirm('fence', pin(fence_record))
        return dict(phase='already-confirmed-no-write', stream_commit=stream['commit_sha'],
                    fence_commit=fence_record['commit_sha'])
    if state.get('plan') is None:
        check_heads()
        journal.plan(plan)
    current = recovery.inspect(client)
    safe.require(current[0] == fence_record and current[2] == stream)
    if plan['release'] is not None:
        released = recovery.confirmed_write(client, journal, 'stream', plan['stream'], plan['release'],
            recovery.g.STORE_PATH, d['store_branch'], plan['stream']['commit_sha'])
        env = plan['release']
        close = safe.owner_candidate(plan['fence_body'], env, recovery.locator(released, env),
            plan['review'], plan['owner_event'], plan['close_write_id'])
    else:
        released, env = stream, envelope
    closed = recovery.confirmed_write(client, journal, 'fence', plan['fence'], close,
        recovery.actions.FENCE_PATH, d['fence_branch'], released['commit_sha'])
    safe.validate(close, env, recovery.locator(released, env))
    return dict(phase='recovered-await-fresh-regular-run', outcome=close['completion'].get('outcome', 'reconciled'),
        incident=incident, stream_commit=released['commit_sha'], fence_commit=closed['commit_sha'])


def main(core, extension, loader_sha, manifest_sha):
    loader = extension / 'tools/pinned_delivery_entry.py'
    raw = loader.read_bytes()
    if hashlib.sha256(raw).hexdigest() != loader_sha:
        raise ValueError('Unreviewed recovery loader')
    namespace = {'__name__': 'reviewed_delivery_loader', '__file__': str(loader)}
    exec(compile(raw, str(loader), 'exec'), namespace)
    namespace['install'](core, extension, manifest_sha)
    import github_recovery
    github_recovery.run = run
    target = extension / 'tools/continuous_operations.py'
    sys.argv = [str(target), '--github', '--policy', 'recovery-policy.json',
                '--result-file', 'recovery-result.json']
    # Run exactly the bytes authenticated by the loader, not a second source read.
    sys.modules['continuous_operations'].main()
