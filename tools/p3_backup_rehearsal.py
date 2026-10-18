"""Full fake-store history package and blocked local restore. No real backup API."""
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import durable_delivery as durable
import github_delivery as github
from production_contract import canonical, digest
from test_github_delivery import FakeAPI

MAX_PACKAGE_BYTES = 16 * 1024 * 1024
MAX_COMMITS = 1000


def package_fake(api, repo, branch, store_id, pin, migration_sha256):
    if not isinstance(api, FakeAPI):
        raise ValueError('FakeAPI only; real backup needs separate authorization')
    chain = []; head = pin
    while head:
        if len(chain) >= MAX_COMMITS: raise ValueError('History budget exhausted')
        record = api.read_at(repo, head, github.STORE_PATH)
        parents = api.parents(repo, head)
        if len(parents) > 1: raise ValueError('Unexpected merge')
        chain.append({'commit_sha':head, 'parents':parents, 'blob_sha':record['blob_sha'],
                      'body_base64':base64.b64encode(record['body']).decode()})
        head = parents[0] if parents else None
    snapshot = json.loads(api.read_at(repo,pin,github.STORE_PATH)['body'])
    manifest = {'schema':'p3-synthetic-github-backup-v1', 'synthetic':True,
        'repo':repo, 'branch':branch, 'path':github.STORE_PATH, 'store_id':store_id,
        'pin':pin, 'revision':snapshot['revision'], 'snapshot_digest':snapshot['body_digest'],
        'code_sha':snapshot['snapshot']['control']['code_sha'],
        'config_sha256':snapshot['snapshot']['control']['config_sha256'],
        'migration_sha256':migration_sha256, 'history_sha256':digest(chain),
        'commit_count':len(chain), 'real_git_history_verified':False}
    package = {'manifest':manifest, 'history':chain}
    if len(canonical(package).encode()) > MAX_PACKAGE_BYTES: raise ValueError('Package budget exhausted')
    verify_fake(package, pin, snapshot['revision'])
    return package


def verify_fake(package, required_pin, required_revision):
    m, chain = package['manifest'], package['history']
    if (m['schema'] != 'p3-synthetic-github-backup-v1' or m['synthetic'] is not True
            or m['pin'] != required_pin or m['revision'] != required_revision
            or m['history_sha256'] != digest(chain) or m['commit_count'] != len(chain)
            or not 1 <= len(chain) <= MAX_COMMITS
            or len(canonical(package).encode()) > MAX_PACKAGE_BYTES
            or not m['migration_sha256']):
        raise ValueError('Backup identity/history/hash mismatch')
    parser = github.GitHubStore(None,m['repo'],m['branch'],m['store_id'],'verify','1',m['path'])
    envelopes = []
    for index, record in enumerate(chain):
        body = base64.b64decode(record['body_base64'],validate=True)
        actual = hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
        if actual != record['blob_sha']: raise ValueError('Backup blob mismatch')
        envelopes.append(parser._parse({'body':body}))
        expected_parent = [chain[index+1]['commit_sha']] if index+1 < len(chain) else []
        if record['parents'] != expected_parent: raise ValueError('Incomplete pinned history')
    if chain[0]['commit_sha'] != m['pin'] or envelopes[0]['revision'] != m['revision']:
        raise ValueError('Latest backup revision missing')
    if (envelopes[0]['body_digest'] != m['snapshot_digest']
            or envelopes[0]['snapshot']['control']['code_sha'] != m['code_sha']
            or envelopes[0]['snapshot']['control']['config_sha256'] != m['config_sha256']):
        raise ValueError('Backup pins mismatch')
    for newer, older in zip(envelopes,envelopes[1:]):
        if newer['revision'] != older['revision']+1 or newer['parent_digest'] != older['body_digest']:
            raise ValueError('Backup revision lineage mismatch')
    if envelopes[-1]['revision'] != 0 or envelopes[-1]['snapshot']['control']['mode'] != 'blocked':
        raise ValueError('Full blocked-seed history required')
    return deepcopy(envelopes[0]['snapshot'])


def restore_fake(package, target, required_pin, required_revision):
    snapshot = verify_fake(package, required_pin, required_revision)
    snapshot['control']['mode'] = 'blocked'
    snapshot['control']['owner'] = None
    snapshot['control']['health']['restore_requires_reconciliation'] = True
    snapshot['control']['health']['successful_runs'] = {}
    snapshot['control']['health']['completed_runs'] = {}
    for s in [snapshot['engine'], *snapshot['commands'].values()]:
        for message in s.get('_delivery',{}).get('messages',[]):
            if message['status'] == 'sending':
                message.update(status='uncertain',reason='blocked_restore')
    durable.provision(target, package['manifest']['store_id'], snapshot)
    with durable.read_only_volume(target,package['manifest']['store_id']) as restored:
        assert restored.snapshot == snapshot
    return {'mode':'blocked', 'source_pin':required_pin, 'source_revision':required_revision,
            'restore_requires_reconciliation':True, 'real_backup_repository':None}
