"""Strictly synthetic isolated probe controller. No real-client option exists."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'engine'))
import durable_delivery as durable
import github_delivery as github
from production_contract import canonical
from test_github_delivery import FakeAPI, REPO, BRANCH, STORE_ID, stage_message
from test_production_runtime import seeded

MAX_PROBE_WRITES = 12


class ProbeAPI(FakeAPI):
    def __init__(self, body):
        self.trace = []; self.targets = set()
        super().__init__(body)

    def read(self, repo, branch, path):
        self.targets.add((repo, branch, path))
        self.trace.append({'method':'GET', 'step':'head_read'})
        return super().read(repo, branch, path)

    def update(self, repo, branch, sha, body, write_id, path):
        if (repo, branch, path) != (REPO, BRANCH, github.STORE_PATH):
            raise ValueError('Probe identity changed')
        if self.put_count >= MAX_PROBE_WRITES:
            raise github.StoreUnavailable('Probe write budget exhausted')
        prior = self.record['commit_sha']
        commit = super().update(repo, branch, sha, body, write_id, path)
        self.trace.append({'method':'PUT', 'prior_blob_sha':sha, 'commit_sha':commit,
            'parent':prior, 'revision':self.envelope()['revision'], 'bytes':len(body), 'write_id':write_id})
        return commit


def synthetic_active(seed):
    """Local bytes only; never writes a repository or changes the blocked source."""
    env = json.loads(seed)
    if env['repo'] != REPO or env['branch'] != BRANCH or env['store_id'] != STORE_ID:
        raise ValueError('Only fixed synthetic identity permitted')
    active = deepcopy(env)
    active['snapshot']['control']['mode'] = 'active'
    active.update(revision=env['revision']+1, parent_digest=env['body_digest'], write_id='synthetic-activation',
                  body_digest=github._digest(active['snapshot']))
    return canonical(active).encode('utf-8')


def probe():
    def forbidden(*a, **k): raise AssertionError('Network forbidden')
    with patch('urllib.request.urlopen', side_effect=forbidden), tempfile.TemporaryDirectory() as td:
        path, _, _ = seeded(td)
        with durable.read_only_volume(path, STORE_ID) as source:
            source_digest = github._digest(source.snapshot)
            seed = github.initial_envelope(source.snapshot, REPO, BRANCH, STORE_ID)
        blocked = ProbeAPI(seed)
        try: github.GitHubStore(blocked, REPO, BRANCH, STORE_ID, 'probe-101', '1').__enter__()
        except ValueError: pass
        else: raise AssertionError('Blocked seed accepted')
        assert blocked.put_count == 0
        api = ProbeAPI(seed)
        # Separate synthetic activation commit, retained in the full fake history.
        api._set(synthetic_active(seed))
        first = github.GitHubStore(api, REPO, BRANCH, STORE_ID, 'probe-101', '1')
        second = github.GitHubStore(api, REPO, BRANCH, STORE_ID, 'probe-202', '2')
        with first:
            before = api.put_count
            try: second.__enter__()
            except github.StoreConflict: pass
            else: raise AssertionError('Two owners')
            assert api.put_count == before
            m = stage_message(first)
            m.update(status='sending', attempts=1, target='a'*64)
            first.commit()
            # No transport call; meaningless fixture receipt after durable sending.
            m.update(status='confirmed', receipt=73)
            first.commit()
        with second: pass
        assert first.owner['nonce'] != second.owner['nonce']
        assert api.envelope()['snapshot']['control']['owner'] is None
        assert api.targets == {(REPO, BRANCH, github.STORE_PATH)}
        puts = [r for r in api.trace if r['method'] == 'PUT']
        for r in puts:
            assert api.parents(REPO, r['commit_sha']) == [r['parent']]
        with durable.read_only_volume(path, STORE_ID) as source:
            assert github._digest(source.snapshot) == source_digest and source.snapshot['control']['mode'] == 'blocked'
        return {'schema':'p3-fake-store-probe-v1', 'passed':True,
            'blocked_seed_denied_before_write':True, 'synthetic_transition_only':True,
            'source_unchanged':True, 'run_owners':[first.owner, second.owner],
            'repo':REPO, 'branch':BRANCH, 'path':github.STORE_PATH,
            'fake_put_count':api.put_count, 'max_probe_writes':MAX_PROBE_WRITES,
            'seed_bytes':len(seed), 'max_observed_bytes':max(r['bytes'] for r in puts),
            'trace':api.trace, 'real_requests':0, 'real_transport_calls':0,
            'production_size_measured':False, 'private_test_repository':None}


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--offline',action='store_true',required=True)
    p.add_argument('--out',required=True); a=p.parse_args(); out=Path(a.out)
    with out.open('x',encoding='utf-8') as f: f.write(json.dumps(probe(),indent=2)+'\n')
