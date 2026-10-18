"""Offline GitHub REST wire model. No HTTP server or external sockets."""
import base64
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import urllib.error
import urllib.parse

import p3_github_probe as probe

FIXTURE_TOKEN = 'github_pat_'+'FixtureOnly0'*7


class Response(io.BytesIO):
    def __init__(self, value, status=200):
        super().__init__(probe.canonical(value).encode()); self.status = status


class API:
    def __init__(self, plan, persisted=None):
        self.p = plan; self.records = {}; self.head = None; self.trace = []
        self.fail = None; self.override = {}; self.persisted = persisted
        self.root = True
        self.put(probe.synthetic_seed(plan), None, plan['seed_commit'])

    def put(self, body, parent, commit=None):
        blob = hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
        commit = commit or hashlib.sha1(body+(parent or '').encode()).hexdigest()
        tree = hashlib.sha1(b'tree'+body).hexdigest()
        self.records[commit] = {'body': base64.b64encode(body).decode(), 'blob': blob,
                                'parents': [] if parent is None else [parent], 'tree': tree}
        self.head = commit
        if self.persisted:
            Path(self.persisted).write_text(probe.canonical({'head': self.head, 'records': self.records}), encoding='utf-8')
        return commit

    def error(self, req, status):
        raise urllib.error.HTTPError(req.full_url, status, 'synthetic', {}, io.BytesIO(b'NEVER LOG RESPONSE'))

    def open(self, req, timeout):
        assert timeout == 15 and req.full_url.startswith('https://api.github.com'+probe.gh.GitHubContentsClient._route(self.p['repo'], ''))
        assert req.get_header('X-github-api-version') == '2022-11-28'
        parsed = urllib.parse.urlsplit(req.full_url)
        base = probe.gh.GitHubContentsClient._route(self.p['repo'], '')
        tail = parsed.path[len(base):]; query = urllib.parse.parse_qs(parsed.query)
        method = req.get_method(); self.trace.append((method, tail))
        if tail in self.override: return Response(self.override[tail])
        if method == 'GET':
            assert req.data is None
            if tail == '': return Response({'id': self.p['repository_id'], 'full_name': self.p['repo'],
                'private': True, 'has_pages': False, 'archived': False, 'permissions': {'admin': True}})
            if tail == '/actions/permissions': return Response({'enabled': False})
            if tail == '/pages' or tail.endswith('/protection'): self.error(req, 404)
            if tail.startswith('/rules/branches/') or tail == '/rulesets': return Response([])
            if tail == '/branches': return Response([] if self.head is None else [
                {'name': self.p['branch'], 'protected': False, 'commit': {'sha': self.head}}])
            if tail.startswith('/git/ref/heads/'):
                assert urllib.parse.unquote(tail[len('/git/ref/heads/'):]) == self.p['branch']
                return Response({'ref': 'refs/heads/'+self.p['branch'], 'object': {'sha': self.head, 'type': 'commit'}})
            if tail == '/contents/'+self.p['path']:
                assert set(query) == {'ref'}
                record = self.records[query['ref'][0]]
                return Response({'type': 'file', 'encoding': 'base64', 'sha': record['blob'], 'content': record['body']})
            if tail.startswith('/git/commits/'):
                commit = tail.split('/')[-1]; r = self.records[commit]
                return Response({'sha': commit, 'tree': {'sha': r['tree']}, 'parents': [{'sha': s} for s in r['parents']]})
            if tail.startswith('/git/trees/'):
                assert query == {'recursive': ['1']}
                r = next(r for r in self.records.values() if r['tree'] == tail.split('/')[-1])
                return Response({'truncated': False, 'tree': [{'type': 'tree', 'path': 'delivery', 'mode': '040000', 'sha': 'a'*40},
                    {'type': 'blob', 'path': self.p['path'], 'mode': '100644', 'sha': r['blob']}]})
            if tail.startswith('/compare/'):
                base_sha, head = tail.split('/')[-1].split('...'); current = head
                while current != base_sha:
                    parents = self.records[current]['parents']
                    if not parents: break
                    current = parents[0]
                return Response({'base_commit': {'sha': base_sha}, 'merge_base_commit': {'sha': current},
                    'status': 'identical' if head == base_sha else ('ahead' if current == base_sha else 'diverged')})
        if method == 'PUT':
            assert tail == '/contents/'+self.p['path'] and not query
            payload = json.loads(req.data)
            assert set(payload) == {'message', 'sha', 'branch', 'content'} and payload['branch'] == self.p['branch']
            mode, self.fail = self.fail, None
            if mode in (403, 429): self.error(req, mode)
            if mode == 'before': raise TimeoutError('synthetic')
            if payload['sha'] != self.records[self.head]['blob']: self.error(req, 409)
            body = base64.b64decode(payload['content'], validate=True)
            env = probe.check_identity(self.p, body)
            assert payload['message'] == 'delivery revision '+env['write_id']
            old = self.head; commit = self.put(body, old)
            if mode == 'after': raise TimeoutError('synthetic')
            return Response({'content': {'sha': self.records[commit]['blob']},
                             'commit': {'sha': commit, 'parents': [{'sha': old}]}}, 200)
        raise AssertionError('Unknown simulated request')


def plan(journal_directory=None):
    p = probe.template()
    p.update(repo='synthetic/offline-p3-probe', repository_id=900001, branch='p3-synthetic-only',
        code_head='a'*40, code_tree='b'*40, code_pins={'tools/p3_github_probe.py': 'c'*64},
        seed_commit='d'*40, credential_evidence_sha256='e'*64, credential_repository_ids=[900001],
        settings_and_other_writers_frozen=True, expires_utc='2099-01-01T00:00:00Z')
    p['phases'] = list(probe.PHASES)
    p['journal_directory'] = str(Path(journal_directory or '.').resolve())
    for i, r in enumerate(p['runs']): r['nonce'] = f'{i+1:032x}'
    p['seed_sha256'] = hashlib.sha256(probe.synthetic_seed(p)).hexdigest()
    probe.validate_plan(p)
    return p


def fixture_grant(p, phase, expires='2099-01-01T00:00:00Z'):
    """Offline fixture only; never imported or called by the real CLI."""
    return {'schema': 'p3-human-grant-v2', 'plan_sha256': probe.digest(p), 'phase': phase,
        'approved_by': 'offline-fixture-no-real-authorization', 'human_authorization': True,
        'expires_utc': expires, 'approval_evidence_sha256': 'a'*64, 'review_sha256': None}


def boundary(p, ledger, reader, writer, opener):
    return probe.Boundary(p, ledger, reader, writer, opener,
        guard=probe.GrantGuard(p, fixture_grant(p, ledger.phase), ledger.phase))


def execute(p, api, root, phase, previous=None, history=True):
    ledger = probe.Ledger(p, Path(root)/(phase+'.jsonl'), phase, previous)
    client = probe.Client(boundary(p, ledger, 'synthetic-reader', 'synthetic-writer', api.open))
    try:
        client.boundary.preflight()
        if history: probe.verify_history(client)
        if phase == 'bootstrap': pass  # root initialized locally by API, no external Git call
        elif phase == 'activate': probe.activation(client)
        elif phase != 'inspect': probe.sequence(client, phase)
        ledger.emit('phase_end', result='confirmed')
    except BaseException:
        ledger.emit('phase_halt', result='incomplete-no-retry-no-release')
        raise
    finally: ledger.close()
    return ledger.path


def rehearsal(directory):
    root = Path(directory); root.mkdir(parents=True, exist_ok=False)
    p = plan(root); api = API(p); previous = None
    for phase in ('bootstrap', 'activate', 'happy', 'lost-after'):
        previous = execute(p, api, root, phase, previous)
    try: execute(p, api, root, 'process-loss', previous)
    except SystemExit as exc: assert exc.code == 23
    else: raise AssertionError('Expected loss')
    rows = probe.Ledger.verify(root/'process-loss.jsonl', probe.digest(p))
    env = json.loads(base64.b64decode(api.records[api.head]['body']))
    assert env['snapshot']['control']['owner'] == probe.owner(p, 5)
    assert env['snapshot']['commands'][probe.owner(p, 5)['run_id']]['_delivery']['messages'][0]['status'] == 'sending'
    return {'schema': 'p3-offline-wire-rehearsal-v1', 'passed': True,
        'plan': p, 'counts': rows[-1]['counts'], 'trace_requests': len(api.trace),
        'sending_retained': True, 'real_requests': 0, 'production_size_measured': False,
        'last_revision': env['revision'], 'last_commit': api.head}


if __name__ == '__main__':
    import argparse
    import socket
    from unittest.mock import patch
    parser = argparse.ArgumentParser(); parser.add_argument('--out', required=True)
    a = parser.parse_args()
    def forbidden(*a, **k): raise AssertionError('External network forbidden')
    with patch('urllib.request.urlopen', side_effect=forbidden), patch.object(socket.socket, 'connect', forbidden):
        result = rehearsal(a.out)
    with (Path(a.out)/'RESULT.json').open('x', encoding='utf-8') as f:
        f.write(json.dumps(result, indent=2)+'\n')
    print(probe.canonical({k: v for k, v in result.items() if k != 'plan'}))
