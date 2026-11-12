"""First production recovery observation through the reviewed read adapters."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import urlsplit

REPOSITORY = 'szoceikaiser/btc-signal-app'
WORKFLOW = '.github/workflows/recovery.yml'
LOADER_SHA256 = 'b2cf523146175d3f7216af9bab313d003f49e4405c1bb2682fd6bb93e2fdc95b'
MANIFEST_SHA256 = 'b9fb84e1357330f5829dfb1d3bcd8f5543abdcba875b7246e378de0b11f59a2f'
POLICY_SHA256 = '6ca17d60470fb93a6fa64f3e8e74e47f0ed36f3bff721bdaa154db567524fda8'
BASE_WORKFLOW_SHA256 = '9ab1073e973df9e07332b20aaf5a5dcbe9799972645023972a0760d6ee7c3f3f'


def require(condition):
    if not condition:
        raise ValueError('Recovery probe evidence refused')


def sha256(body):
    return hashlib.sha256(body).hexdigest()


class GetOnly:
    """Reject before opening a socket. Count actual attempts at this boundary."""

    def __init__(self, opener):
        self.opener = opener
        self.gets = 0

    def __call__(self, request, timeout):
        require(request.get_method() == 'GET' and request.data is None)
        target = urlsplit(request.full_url)
        require(target.scheme == 'https' and target.netloc in (
            'api.github.com', 'github.com', 'raw.githubusercontent.com'))
        self.gets += 1
        return self.opener(request, timeout)


def verify_invocation(environment):
    require(all(environment.get(key) == value for key, value in {
        'RECOVERY_ENABLED': 'false',
        'GITHUB_EVENT_NAME': 'workflow_dispatch',
        'GITHUB_REPOSITORY': REPOSITORY,
        'GITHUB_REF': 'refs/heads/main',
        'GITHUB_WORKFLOW_REF': f'{REPOSITORY}/{WORKFLOW}@refs/heads/main',
        'GITHUB_RUN_ATTEMPT': '1',
        'GITHUB_JOB': 'recover',
    }.items()))
    require(re.fullmatch('[0-9a-f]{40}', environment.get('GITHUB_SHA', '')))
    require(re.fullmatch('[0-9a-f]{64}', environment.get('PROBE_WORKFLOW_SHA256', '')))


def load_policy(environment, workflow_bytes):
    from production_contract import digest

    raw = environment['REVIEWED_RECOVERY_JSON']
    require(len(raw.encode()) <= 128 * 1024)
    policy = json.loads(raw)
    require(digest(policy) == POLICY_SHA256 and policy['enabled'] is False
            and policy['activation_reviewed'] is False and policy['journal']['reviewed'] is True)
    entry = policy['recovery_entry']
    require(entry['workflow_sha256'] == BASE_WORKFLOW_SHA256)
    workflow_sha = sha256(workflow_bytes)
    require(workflow_sha == environment['PROBE_WORKFLOW_SHA256'])
    # Only the in-memory entry binding is updated. No writer or journal uses it.
    entry['workflow_sha256'] = workflow_sha
    return policy


def install(extension, core, entry_sha):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(extension), *args], stderr=subprocess.DEVNULL)

    require(git('rev-parse', 'HEAD').decode().strip() == entry_sha)
    require(not git('status', '--porcelain', '--untracked-files=all', '--', WORKFLOW,
                    'ops/continuous/recovery_read_probe.py', 'tools/pinned_delivery_entry.py',
                    'delivery-extension.json'))
    loader = extension / 'tools/pinned_delivery_entry.py'
    body = loader.read_bytes()
    require(sha256(body) == LOADER_SHA256)
    namespace = {'__name__': 'reviewed_delivery_loader', '__file__': str(loader)}
    exec(compile(body, str(loader), 'exec'), namespace)
    namespace['install'](core, extension, MANIFEST_SHA256)


def ref_head(client, branch):
    ref = client._request('GET', client._route(client.repo, '/git/ref/heads/' + branch))
    head = ref['object']['sha']
    require(re.fullmatch('[0-9a-f]{40}', head))
    return head


def observe(client, environment):
    import actions_delivery as actions
    from aborted_maintenance import refuse_healthy
    import github_recovery
    from production_contract import digest
    from produktion_actions_runner import verify_health
    import public_access
    import safe_recovery

    identity = github_recovery.bind_self(client, environment)
    own_route = client._route(client.code, '/actions/runs/' + identity['run_id'])
    require(client.mutable_metadata[own_route]['event'] == 'workflow_dispatch')

    policy = client.policy
    deployment = policy['deployment']
    journal = policy['journal']
    require(journal['repository'] == client.repo and journal['branch'] == 'recovery-journal-live')
    public_access.deployment(policy['public_access'], deployment)
    public_access.check(client, policy['public_access'], [(client.code, 'main')])
    business = [(client.repo, deployment[key]) for key in ('store_branch', 'fence_branch')]
    journal_branch = [(client.repo, journal['branch'])]
    public_access.check(client, policy['public_access'], business, business)
    public_access.check(client, journal['public_access'], journal_branch, journal_branch)
    public_access.credential(journal['public_access'], 'recovery_journal_write',
                             client.repo, [journal['branch']])
    require(journal['public_access']['credential_reviews']['recovery_journal_write']
            ['credential_reference'] == journal['credential_reference'])
    journal_head = ref_head(client, journal['branch'])
    require(client.is_ancestor(client.repo, journal['seed_commit'], journal_head))

    fence_record, fence, stream_record, envelope = github_recovery.inspect(client)
    completion = fence['completion']
    require(fence['phase'] == 'closed' and fence['run'] and completion and 'recovery' not in completion)
    refuse_healthy(fence)
    snapshot = envelope['snapshot']
    control = snapshot['control']
    require(control['mode'] == 'active' and control['owner'] is None
            and not control['health'].get('restore_requires_reconciliation')
            and all(control[key] == deployment[key] for key in ('code_sha', 'config_sha256', 'store_id', 'bot_identity')))
    require(completion['stream'] == github_recovery.locator(stream_record, envelope))
    safe_recovery.receipts(snapshot)
    run = fence['run']
    if run['kind'] == 'lage':
        operation = digest({'repository': client.code, 'workflow': run['workflow'], 'run_id': run['id']})
        actions.verify_command(snapshot, SimpleNamespace(run=run, environment={
            'BTC_DELIVERY_RUN_REPOSITORY': client.code,
            'BTC_DELIVERY_CODE_SHA': deployment['code_sha'],
        }), operation)
    else:
        verify_health(SimpleNamespace(snapshot=snapshot), deployment, run)

    heads = {
        'journal_head': (journal['branch'], journal_head),
        'fence_head': (deployment['fence_branch'], fence_record['commit_sha']),
        'stream_head': (deployment['store_branch'], stream_record['commit_sha']),
    }
    for branch, expected in heads.values():
        require(ref_head(client, branch) == expected)
    return {**identity, **{key: head for key, (_, head) in heads.items()}}


def execute(environment, extension, core, transport):
    verify_invocation(environment)
    install(extension, core, environment['GITHUB_SHA'])
    from actions_freshness import Reader
    from github_freshness import ReadBudget
    from job_quota import read_only_environment

    read_only_environment()
    policy = load_policy(environment, (extension / WORKFLOW).read_bytes())
    repo = policy['deployment']['private_store_repository']
    client = Reader(environment.get('GITHUB_TOKEN'), [REPOSITORY, repo], ReadBudget(), metadata=True)
    client.open_request = transport
    client.policy, client.repo, client.code = policy, repo, REPOSITORY
    return observe(client, environment)


def main():
    def open_request(request, timeout):
        from production_confirmation import ProductionContentsClient
        return ProductionContentsClient.open_request(request, timeout)

    transport = GetOnly(open_request)
    try:
        with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            evidence = execute(os.environ, Path('extension'), Path('core'), transport)
        result = {'phase': 'no-open-incident', **evidence}
        code = 0
    except Exception:
        result = {'phase': 'blocked-or-unconfirmed'}
        code = 20
    print(json.dumps({**result, 'gets': transport.gets, 'writes': 0}, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
