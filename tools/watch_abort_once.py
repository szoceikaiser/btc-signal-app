"""Operator entry for the sole conditional update of the reviewed Watch fence."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

from actions_delivery import FENCE_PATH, parse_fence
from github_delivery import GitHubContentsClient
from production_contract import canonical
import watch_abort as incident


REMOTE = 'https://github.com/' + incident.REPOSITORY + '.git'
REF = 'refs/heads/' + incident.FENCE_BRANCH
WRITERS = ('watch.yml', 'signal.yml', 'lage.yml', 'recovery.yml')
ACTIVE = ('in_progress', 'waiting', 'requested', 'pending', 'queued')


def command(args, *, data=None, timeout=30):
    result = subprocess.run(args, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=timeout, check=False)
    if result.returncode:
        raise ValueError('Operator command failed: ' + args[0])
    return result.stdout


class GitHubReadback(GitHubContentsClient):
    def __init__(self):
        pass

    def _request(self, method, route, payload=None):
        incident.require(method == 'GET' and payload is None and route.startswith(
            ('/repos/' + incident.REPOSITORY + '/', '/repos/' + incident.APP + '/')))
        return json.loads(command(['gh', 'api', '--hostname', 'github.com', '--method', 'GET', route]))

    def get(self, repo, tail):
        return self._request('GET', self._route(repo, tail))

    def head(self, repo, branch):
        result = self.get(repo, '/git/ref/heads/' + branch)
        incident.require(result['ref'] == 'refs/heads/' + branch
                         and result['object']['type'] == 'commit')
        return result['object']['sha']


def check_heads(client, release, fence=None):
    for repo, branch, expected in (
        (incident.APP, 'main', release),
        (incident.REPOSITORY, incident.STREAM_BRANCH, incident.STREAM),
        (incident.REPOSITORY, incident.JOURNAL_BRANCH, incident.JOURNAL),
        (incident.REPOSITORY, incident.FENCE_BRANCH, fence or incident.FENCE),
    ):
        incident.require(client.head(repo, branch) == expected)


def check_workers(client):
    # Check server-side trigger state, then look for previously admitted jobs.
    for name in WRITERS:
        workflow = client.get(incident.APP, '/actions/workflows/' + name)
        incident.require(workflow['path'] == '.github/workflows/' + name
                         and workflow['state'] == 'disabled_manually')
    run = client.get(incident.APP, '/actions/runs/' + incident.RUN)
    incident.require(str(run['id']) == incident.RUN and run['run_number'] == 3730
                     and run['run_attempt'] == 1 and run['status'] == 'completed'
                     and run['conclusion'] == 'failure' and run['event'] == 'workflow_dispatch'
                     and run['path'] == incident.WATCH and run['head_branch'] == 'main'
                     and run['head_sha'] == incident.SOURCE
                     and run['repository']['full_name'] == incident.APP)
    jobs = client.get(incident.APP, '/actions/runs/' + incident.RUN + '/attempts/1/jobs?per_page=100&page=1')
    incident.require(jobs['total_count'] == len(jobs['jobs']) == 1)
    job = jobs['jobs'][0]
    incident.require(str(job['id']) == incident.JOB and str(job['run_id']) == incident.RUN
                     and job['run_attempt'] == 1 and job['status'] == 'completed'
                     and job['conclusion'] == 'failure' and job['head_sha'] == incident.SOURCE
                     and job['completed_at'] == incident.JOB_END and 'ubuntu-24.04' in job['labels']
                     and 'self-hosted' not in job['labels'])
    for status in ACTIVE:
        runs = client.get(incident.APP, '/actions/runs?status=' + status + '&per_page=100&page=1')
        incident.require(runs['total_count'] == 0 and runs['workflow_runs'] == [])


def prepare(client, release, now):
    check_heads(client, release)
    check_workers(client)
    repo = incident.REPOSITORY
    journal = client.get(repo, '/git/commits/' + incident.JOURNAL)
    tree = client.get(repo, '/git/trees/' + journal['tree']['sha'] + '?recursive=1')
    path = 'recovery/incidents/' + incident.FENCE + '.json'
    incident.require(journal['sha'] == incident.JOURNAL and tree['sha'] == journal['tree']['sha']
                     and tree['truncated'] is False and all(item['path'] != path for item in tree['tree']))
    incident.require(client.parents(repo, incident.FENCE) == [incident.PREVIOUS])
    old = client.read_at(repo, incident.FENCE, FENCE_PATH)
    previous = client.read_at(repo, incident.PREVIOUS, FENCE_PATH)
    opened = json.loads(old['body'])
    deployment = opened['deployment']
    closed = incident.candidate(parse_fence(old, deployment), parse_fence(previous, deployment),
                                client.read_at(repo, incident.STREAM), now)
    return canonical(closed).encode()


class FenceGit:
    def __init__(self, directory):
        self.directory = directory
        self.git('init', '--bare')

    def git(self, *args, data=None):
        return command(['git', '-C', str(self.directory), '-c', 'core.hooksPath=' + os.devnull,
                        '-c', 'commit.gpgSign=false', *args], data=data)

    def stage(self, body):
        self.git('fetch', '--no-tags', '--depth=2', REMOTE, REF)
        incident.require(self.git('rev-parse', 'FETCH_HEAD').decode().strip() == incident.FENCE)
        self.git('read-tree', incident.FENCE)
        blob = self.git('hash-object', '-w', '--stdin', data=body).decode().strip()
        self.git('update-index', '--cacheinfo', '100644,' + blob + ',' + FENCE_PATH)
        tree = self.git('write-tree').decode().strip()
        commit = self.git('-c', 'user.name=Signal-App Maintenance',
                          '-c', 'user.email=maintenance@users.noreply.github.com',
                          'commit-tree', tree, '-p', incident.FENCE,
                          '-m', 'Abort Watch 43880114205 after confirmed unchanged stream').decode().strip()
        incident.require(self.git('diff-tree', '--no-commit-id', '--name-only', '-r', commit).splitlines()
                         == [FENCE_PATH.encode()])
        return commit

    def close(self, commit):
        # The server checks the exact old commit, even if a competing commit has the same blob.
        result = self.git('push', '--porcelain', '--no-follow-tags', '--recurse-submodules=no',
                          '--force-with-lease=' + REF + ':' + incident.FENCE,
                          REMOTE, commit + ':' + REF)
        updates = [line for line in result.splitlines() if b'\t' in line]
        incident.require(len(updates) == 1 and updates[0].startswith(
            b' \t' + (commit + ':' + REF).encode() + b'\t'))


def close_once(client, writer, release, reservation, now):
    incident.require(not reservation.exists())
    body = prepare(client, release, now)
    commit = writer.stage(body)
    check_workers(client)
    # Consume the attempt before the push. An ambiguous result only permits readback.
    with reservation.open('x', encoding='utf-8') as file:
        file.write(canonical(dict(open_commit=incident.FENCE, close_commit=commit, release=release)))
        file.flush()
        os.fsync(file.fileno())
    check_heads(client, release)
    try:
        writer.close(commit)
        check_heads(client, release, fence=commit)
        incident.require(client.parents(incident.REPOSITORY, commit) == [incident.FENCE])
        incident.require(client.read_at(incident.REPOSITORY, commit, FENCE_PATH)['body'] == body)
        check_heads(client, release, fence=commit)
    except Exception:
        raise ValueError('Fence update unconfirmed; inspect the reservation and Store read-only') from None
    return commit


def main(extension, argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--reservation', type=Path)
    parser.add_argument('--exclusive-write-window', action='store_true')
    args = parser.parse_args(argv)
    incident.require(bool(re.fullmatch('[0-9a-f]{40}', args.release)) and args.release != incident.SOURCE)
    git = ['git', '-C', str(extension)]
    incident.require(command(git + ['rev-parse', 'HEAD']).decode().strip() == args.release
                     and not command(git + ['status', '--porcelain', '--untracked-files=no']))
    client = GitHubReadback()
    now = time.time_ns() // 1_000_000
    if args.check:
        prepare(client, args.release, now)
        check_heads(client, args.release)
        return {'status': 'watch_abort_preflight_passed'}
    incident.require(args.reservation is not None and args.exclusive_write_window)
    with tempfile.TemporaryDirectory(prefix='watch-abort-') as directory:
        commit = close_once(client, FenceGit(directory), args.release, args.reservation, now)
    return {'status': 'watch_abort_fence_confirmed', 'fence_commit': commit}
