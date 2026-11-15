"""One read-only observation in the automatic Recovery context."""
import contextlib
import json
import hashlib
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from urllib.parse import urlencode, urlsplit

REPO = 'szoceikaiser/btc-signal-app'
REPO_ID = 1309164619
STORE = 'szoceikaiser/btc-delivery-store'
WORKFLOW = '.github/workflows/recovery.yml'
WATCH = '.github/workflows/watch.yml'
WATCH_ID = 323116288
DISABLED = '6ca17d60470fb93a6fa64f3e8e74e47f0ed36f3bff721bdaa154db567524fda8'
ACTIVE = 'de36ebc7b3c389c39daed79cb2a650acea18e395f5891e8af6a0c088a3d98ce5'
ACTIVE_WORKFLOW = 'e74a53e8bccf09d8ffbb1e5df69bf2b7d76bf2d10f5d2e9cecb3d3e8cae9da70'


def require(condition):
    if not condition:
        raise ValueError('Observation refused')


class GetOnly:
    def __init__(self, opener, diagnostic):
        self.opener = opener
        self.diagnostic = diagnostic
        self.gets = 0

    def __call__(self, request, timeout):
        target = urlsplit(request.full_url)
        if request.get_method() != 'GET' or request.data is not None:
            self.diagnostic.reason = 'mutation_refused'
            raise ValueError('Read-only transport')
        require(target.scheme == 'https' and target.netloc == 'api.github.com'
                and not target.fragment and any(
                    target.path == '/repos/' + repo or target.path.startswith('/repos/' + repo + '/')
                    for repo in (REPO, STORE)))
        self.gets += 1
        return self.opener(request, timeout)


def reviewed_inputs(env, extension, now):
    import actions_schedule as slots
    from production_contract import digest

    require(all(env.get(k) == v for k, v in {
        'RECOVERY_ENABLED': 'false', 'GITHUB_EVENT_NAME': 'workflow_run',
        'GITHUB_REPOSITORY': REPO, 'GITHUB_REPOSITORY_ID': str(REPO_ID),
        'GITHUB_REF': 'refs/heads/main', 'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_JOB': 'recover',
        'GITHUB_WORKFLOW_REF': f'{REPO}/{WORKFLOW}@refs/heads/main',
    }.items()))
    raw = env['RECOVERY_ONCE']
    require(len(raw) <= 512)
    gate = json.loads(raw)
    require(set(gate) == {'slot_ms','expires_ms','workflow_sha256'})
    slot, expires = gate['slot_ms'], gate['expires_ms']
    require(slots.valid_slot('watch', slot) and type(expires) is int
            and slot <= now < expires <= slots.deadline('watch', slot))
    require(gate['workflow_sha256'] == hashlib.sha256((extension / WORKFLOW).read_bytes()).hexdigest())
    raw = env['REVIEWED_RECOVERY_JSON']
    require(len(raw.encode()) <= 128 * 1024)
    policy = json.loads(raw)
    require(digest(policy) == DISABLED)
    policy.update(enabled=True, activation_reviewed=True)
    policy['recovery_entry']['workflow_sha256'] = ACTIVE_WORKFLOW
    require(digest(policy) == ACTIVE and policy['journal']['repository'] == STORE)
    policy['recovery_entry']['workflow_sha256'] = gate['workflow_sha256']
    with Path(env['GITHUB_EVENT_PATH']).open('rb') as f:
        raw = f.read(512 * 1024 + 1)
    require(len(raw) <= 512 * 1024)
    event = json.loads(raw)
    require(event['action'] == 'completed' and event['repository']['id'] == REPO_ID
            and event['repository']['full_name'] == REPO)
    return policy, gate, event['workflow_run']


def verify_occurrence(client, source, gate, identity, now, *, check_workflow=True):
    from actions_schedule import run_slot
    from github_freshness import iso, utc_ms
    from reviewed_actions_entry import verify

    slot, expires = gate['slot_ms'], gate['expires_ms']
    require(now < expires and type(source['id']) is int and source['id'] > 0 and source['workflow_id'] == WATCH_ID
            and source['path'] == WATCH and source['head_branch'] == 'main'
            and source['repository']['id'] == source['head_repository']['id'] == REPO_ID
            and source['repository']['full_name'] == source['head_repository']['full_name'] == REPO
            and source['status'] == 'completed' and source['conclusion'] == 'success'
            and source['event'] == 'workflow_dispatch'
            and run_slot('watch', source) == slot)
    finished = utc_ms(source['updated_at'])
    require(slot <= utc_ms(source['created_at']) <= finished <= now < expires)
    query = urlencode({'branch':'main', 'created':iso(slot)+'..'+iso(now), 'per_page':100, 'page':1})
    listing = client._request('GET', client._route(REPO, '/actions/runs?' + query))
    rows = listing['workflow_runs']
    require(listing['total_count'] == len(rows) < 100 and not client.metadata._response_link)
    watches = [r for r in rows if r['workflow_id'] == WATCH_ID or r['path'] == WATCH]
    if len(watches) != 1:
        client.diagnostic.reason = 'source_not_unique'
        raise ValueError('Watch occurrence is not unique')
    real = watches[0]
    for key in ('id','workflow_id','path','head_branch','head_sha','event','run_attempt',
                'status','conclusion','created_at','updated_at','display_title'):
        require(real[key] == source[key])
    require(real['repository']['id'] == real['head_repository']['id'] == REPO_ID)
    recoveries = [r for r in rows if r['path'] == WORKFLOW]
    if len(recoveries) != 1:
        client.diagnostic.reason = 'slot_consumed_or_ambiguous'
        raise ValueError('Recovery occurrence is not unique')
    own = recoveries[0]
    require(str(own['id']) == identity['run_id'] and own['run_attempt'] == 1
            and own['repository']['id'] == REPO_ID and own['head_branch'] == 'main'
            and own['head_sha'] == identity['entry'] and own['event'] == 'workflow_run'
            and finished <= utc_ms(own['created_at']) <= now)
    if check_workflow:
        policy = client.policy
        verify(client, REPO, source['head_sha'], policy['deployment']['code_sha'], WATCH,
               policy['entry_workflows'][WATCH])


def verify_closed(client, source):
    from actions_schedule import run_slot
    import github_recovery as recovery
    import public_access
    from produktion_actions_runner import verify_health

    policy = client.policy
    d = policy['deployment']
    j = policy['journal']
    public_access.deployment(policy['public_access'], d)
    business = [(STORE, d[key]) for key in ('store_branch', 'fence_branch')]
    journal = [(STORE, j['branch'])]
    public_access.check(client, policy['public_access'], business, business)
    public_access.check(client, j['public_access'], journal, journal)
    public_access.credential(j['public_access'], 'recovery_journal_write', STORE, [j['branch']])
    require(j['public_access']['credential_reviews']['recovery_journal_write']
            ['credential_reference'] == j['credential_reference'])
    head_route = lambda branch: client._route(STORE, '/git/ref/heads/' + branch)
    journal_head = client._request('GET', head_route(j['branch']))['object']['sha']
    require(client.is_ancestor(STORE, j['seed_commit'], journal_head))
    f, fence, s, envelope = recovery.inspect(client)
    run = fence['run']
    require(fence['phase'] == 'closed' and run and run['kind'] == 'watch'
            and run['id'] == str(source['id']) and fence['completion']
            and int(run['expected_start_ms']) == run_slot('watch', source)
            and not {'recovery', 'outcome'}.intersection(fence['completion'])
            and fence['completion']['stream'] == recovery.locator(s, envelope))
    control = envelope['snapshot']['control']
    require(control['mode'] == 'active' and control['owner'] is None
            and not control['health'].get('restore_requires_reconciliation')
            and all(control[k] == d[k] for k in ('code_sha','config_sha256','store_id','bot_identity')))
    recovery.safe.receipts(envelope['snapshot'])
    verify_health(SimpleNamespace(snapshot=envelope['snapshot']), d, run)
    for branch, expected in ((j['branch'],journal_head),(d['fence_branch'],f['commit_sha']),
                             (d['store_branch'],s['commit_sha'])):
        require(client._request('GET',head_route(branch))['object']['sha'] == expected)
    return {'journal_head':journal_head, 'fence_head':f['commit_sha'], 'stream_head':s['commit_sha']}


def main(writer, extension, core, loader_sha, manifest_sha):
    import time
    diagnostic = writer['Diagnostic']()
    transport = None
    result = {}

    def probe(network, bind, run):
        nonlocal transport
        env = os.environ
        now = int(time.time() * 1000)
        diagnostic.enter('slot_and_policy_binding')
        policy, gate, source = reviewed_inputs(env, extension, now)
        client = network(policy, env.get('BTC_DELIVERY_GITHUB_TOKEN'), env.get('GITHUB_TOKEN'))
        transport = GetOnly(client.open_request, diagnostic)
        client.open_request = client.metadata.open_request = transport
        identity = bind(client, env)
        diagnostic.enter('slot_uniqueness')
        verify_occurrence(client, source, gate, identity, int(time.time() * 1000))
        outcome = run(client, identity, read_only=True)
        require(outcome == {'phase':'no-open-incident','writes':0})
        diagnostic.enter('closed_state_check')
        heads = verify_closed(client, source)
        diagnostic.enter('slot_final_recheck')
        verify_occurrence(client, source, gate, identity, int(time.time() * 1000), check_workflow=False)
        diagnostic.enter('no-open-incident')
        diagnostic.reason = 'ok'
        result.update(heads, source_run_id=source['id'], recovery_run_id=identity['run_id'])

    try:
        with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            writer['execute'](core, extension, loader_sha, manifest_sha, diagnostic, probe=probe)
        status = 0
    except Exception:
        status = 1
    print(json.dumps({**json.loads(diagnostic.output()), **result,
                      'wire_gets':transport.gets if transport else 0, 'writes':0},sort_keys=True))
    return status
