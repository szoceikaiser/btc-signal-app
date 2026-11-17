"""Incident paths through the real hash-pinned overlay and local Git only."""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
RELEASE = 'a' * 40
CONFIRMED = 1794838081000


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(core, observer):
    entry = runpy.run_path(str(ROOT/'ops/continuous/freshness/entry.py'))
    return entry['install'](SimpleNamespace(
        core=core, observer_root=observer, extension=ROOT,
        loader_sha256=sha(ROOT/'tools/pinned_delivery_entry.py'),
        manifest_sha256=sha(ROOT/'delivery-extension.json'),
        monitor_sha256=sha(ROOT/'ops/continuous/freshness/actions_freshness.py')))


def write(git, ref, path, body):
    blob = git.git('hash-object', '-w', '--stdin', data=body).decode().strip()
    git.git('update-index', '--add', '--cacheinfo', '100644,' + blob + ',' + path)
    tree = git.git('write-tree').decode().strip()
    parent = git.git('for-each-ref', '--format=%(objectname)', ref).decode().strip()
    ancestry = ['-p', parent] if parent else []
    pin = git.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                  'commit-tree', tree, *ancestry, '-m', 'synthetic').decode().strip()
    git.git('update-ref', ref, pin)
    return pin


def record(git, pin, path):
    return dict(commit_sha=pin, blob_sha=git.git('rev-parse', pin+':'+path).decode().strip(),
                body=git.git('show', pin+':'+path))


class Provider:
    def __init__(self, fixture):
        self.f = fixture
        self.worker = 'disabled_manually'
        self.queue = dict(total_count=0, workflow_runs=[])
        self.main = RELEASE
        self.journal = w.JOURNAL
        self.stream = w.STREAM
        self.bad_readback = False
        self.job_status = 'completed'
        self.journal_tree = []

    def head(self, repo, branch):
        if repo == w.APP:
            assert branch == 'main'
            return self.main
        assert repo == w.REPOSITORY
        if branch == w.FENCE_BRANCH:
            return self.f.fence.git('rev-parse', once.REF).decode().strip()
        return {w.STREAM_BRANCH: self.stream, w.JOURNAL_BRANCH: self.journal}[branch]

    def get(self, repo, tail):
        if tail.startswith('/actions/workflows/'):
            return dict(path='.github/workflows/'+tail.rsplit('/',1)[1], state=self.worker)
        if tail == '/actions/runs/'+w.RUN:
            return dict(id=int(w.RUN), run_number=3730, run_attempt=1, status='completed',
                        conclusion='failure', event='workflow_dispatch', path=w.WATCH,
                        head_branch='main', head_sha=w.SOURCE, repository={'full_name':w.APP})
        if '/attempts/1/jobs?' in tail:
            return dict(total_count=1, jobs=[dict(id=int(w.JOB), run_id=int(w.RUN), run_attempt=1,
                        status=self.job_status, conclusion='failure', head_sha=w.SOURCE,
                        completed_at=w.JOB_END, labels=['ubuntu-24.04'])])
        if tail.startswith('/actions/runs?status='):
            return self.queue
        if tail.startswith('/git/commits/'):
            return dict(sha=w.JOURNAL, tree={'sha':'test-tree'})
        if tail == '/git/trees/test-tree?recursive=1':
            return dict(sha='test-tree', truncated=False, tree=self.journal_tree)
        raise AssertionError(tail)

    def parents(self, repo, pin):
        return self.f.fence.git('show','-s','--format=%P',pin).decode().split()

    def read_at(self, repo, pin, path='delivery/stream.json'):
        if self.bad_readback and path == a.FENCE_PATH and pin not in (w.FENCE,w.PREVIOUS):
            raise TimeoutError('synthetic unknown readback')
        return record(self.f.stream if path == 'delivery/stream.json' else self.f.fence, pin, path)

    def read(self, repo, branch, path='delivery/stream.json'):
        return self.read_at(repo,self.head(repo,branch),path)


class IncidentPaths(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.assertEqual(os.environ.get('GIT_ALLOW_PROTOCOL'),'file')
        stack.enter_context(patch('socket.create_connection',side_effect=AssertionError('network')))
        stack.enter_context(patch('socket.socket.connect',side_effect=AssertionError('network')))
        self.root = Path(stack.enter_context(tempfile.TemporaryDirectory(dir=ROOT/'..')))
        self.fence = self.repo('fence')
        self.stream = self.repo('stream')
        self.reservation = self.root/'attempt.json'
        self.stream_path = 'delivery/stream.json'
        config = dict(muster_cvd='usd',bias_short=False,ausbruch_ruecktest=False)
        d = dict(code_repository=w.APP,code_sha='1'*40,config_sha256=digest(config),
                 private_store_repository=w.REPOSITORY,store_id='test-store',
                 store_branch=w.STREAM_BRANCH,fence_branch=w.FENCE_BRANCH,bot_identity='test-bot',
                 schedule_contract='btc-actions-slots-v1',workflows=a.WORKFLOWS)
        self.d = d
        from position_state import Position, pos_to_state
        slot = 1794836280000
        done = dict(repository=w.APP,workflow=w.WATCH,run_id=w.PRIOR_RUN,run_attempt='1',kind='watch',
                    code_sha=d['code_sha'],config_sha256=d['config_sha256'],status='completed',
                    expected_start_ms=slot,started_ms=slot,finished_ms=slot+5000,
                    watch_observed_ms=slot+1000,watch_candle_open_ms=slot//14400000*14400000)
        engine = dict(pos_to_state(Position()),config=config,last_signal_ts=0,
                      _delivery=dict(version=1,signals={'signals':[]},oi_history=[],messages=[]))
        snap = dict(version=2,engine=engine,watch={},commands={},control=dict(
            stream_id='test-stream',store_id=d['store_id'],target_binding='2'*64,
            bot_identity=d['bot_identity'],mode='active',owner=None,code_sha=d['code_sha'],
            config_sha256=d['config_sha256'],reconciliations=[],health=dict(
                current_run=done,completion_candidate=done,successful_runs={'watch':{'run':done}}),
            migration=dict(migration_id='test',B=0,W=14400000,legacy_delivery='unknown_no_replay',
                           history_sha256=digest({'signals':[]}),history_count=0,
                           source_hashes={},unknowns={},gates={})))
        envelope = dict(schema='btc-github-store-v1',repo=w.REPOSITORY,branch=w.STREAM_BRANCH,
                        store_id=d['store_id'],revision=4928,parent_digest='0'*64,
                        write_id='test',snapshot=snap,body_digest=digest(snap))
        self.stream_pin = write(self.stream,'refs/heads/'+w.STREAM_BRANCH,self.stream_path,
                                canonical(envelope).encode())
        stream = record(self.stream,self.stream_pin,self.stream_path)
        self.locator = dict(adapter='github',repo=w.REPOSITORY,branch=w.STREAM_BRANCH,
                            path=self.stream_path,store_id=d['store_id'],revision=4928,
                            commit_sha=self.stream_pin,blob_sha=stream['blob_sha'],
                            snapshot_digest=envelope['body_digest'])
        self.seed = write(self.fence,once.REF,a.FENCE_PATH,a.seed_fence(d))
        self.old_run = dict(id=w.RUN,kind='watch',workflow=w.WATCH,number=3730,attempt='1',
                            deadline_utc_ms=w.DEADLINE,expected_start_ms='1794837180000')
        prev_run = dict(self.old_run,id=w.PRIOR_RUN,number=3729,expected_start_ms=str(slot))
        prev_open = self.opened(json.loads(a.seed_fence(d)),prev_run)
        write(self.fence,once.REF,a.FENCE_PATH,canonical(prev_open).encode())
        prev_fence = dict(prev_open,phase='closed',completion={'stream':self.locator})
        prev_pin = write(self.fence,once.REF,a.FENCE_PATH,canonical(prev_fence).encode())
        self.open = self.opened(prev_fence,self.old_run)
        old_pin = write(self.fence,once.REF,a.FENCE_PATH,canonical(self.open).encode())
        stack.enter_context(patch.multiple(w,FENCE=old_pin,FENCE_HASH=digest(self.open),
            PREVIOUS=prev_pin,PREVIOUS_HASH=digest(prev_fence),STREAM=self.stream_pin,
            STREAM_HASH=hashlib.sha256(stream['body']).hexdigest()))
        stack.enter_context(patch.object(once,'REMOTE',self.fence.directory.as_posix()))
        self.provider = Provider(self)
        self.writer = self.repo('operator')

    def repo(self,name):
        folder = self.root/name
        folder.mkdir()
        return once.FenceGit(folder)

    def opened(self,value,run):
        cursors = deepcopy(value['cursors'])
        cursors[run['workflow']] = dict(id=run['id'],number=run['number'])
        return dict(value,phase='open',completion=None,run=run,cursors=cursors,write_id='test-open')

    def execute(self):
        return once.close_once(self.provider,self.writer,RELEASE,self.reservation,CONFIRMED)

    def followup(self, slot):
        writes = []
        client = object.__new__(a.ActionsClient)
        client.journal = SimpleNamespace(binding={'repo':w.REPOSITORY})
        client.fence_branch = w.FENCE_BRANCH
        client.read = self.provider.read
        client.read_at = self.provider.read_at
        client.parents = self.provider.parents
        client.fence_write = lambda old, new: writes.append((old,new))
        run = dict(self.old_run,id='43890000000',number=3731,expected_start_ms=str(slot))
        return client,run,writes

    def test_close_and_real_acquire(self):
        pin = self.execute()
        closed = json.loads(self.provider.read_at(w.REPOSITORY,pin,a.FENCE_PATH)['body'])
        self.assertEqual(closed['cursors'],self.open['cursors'])
        self.assertEqual(closed['run'],self.open['run'])
        self.assertEqual(self.provider.parents(w.REPOSITORY,pin),[w.FENCE])
        self.assertEqual(self.provider.head(w.REPOSITORY,w.STREAM_BRANCH),w.STREAM)
        self.assertEqual(self.provider.head(w.REPOSITORY,w.JOURNAL_BRANCH),w.JOURNAL)
        client,run,writes = self.followup(CONFIRMED)
        with self.assertRaises(ValueError):
            client.acquire(self.d,run)
        self.assertEqual(writes,[])
        client,run,writes = self.followup(CONFIRMED+1)
        client.acquire(self.d,run)
        self.assertTrue(client.admitted)
        self.assertEqual(writes[0][1]['run'],run)
        self.assertEqual(writes[0][0]['commit_sha'],pin)
        client,run,writes = self.followup(CONFIRMED+1)
        self.provider.stream = '0'*40
        with self.assertRaises(ValueError):
            client.acquire(self.d,run)
        self.assertEqual(writes,[])
        with self.assertRaises(ValueError):
            self.execute()

    def test_real_freshness_rejects_abort(self):
        self.execute()
        result = monitor.check(self.provider,None,None,dict(
            schema='p4-actions-monitor-v1',enabled=True,deployment=self.d),CONFIRMED+1)
        self.assertEqual(result['http_status'],503)
        self.assertEqual(result['diagnostic']['phase'],'fence')
        self.assertFalse(result['body']['healthy'])

    def test_real_backup_and_restore(self):
        pin = self.execute()
        folder = self.root/'fence-package'
        manifest = pair.append_fence(self.fence.directory,w.FENCE_BRANCH,pin,4,self.d,folder,b.Budget())
        identity = dict(repo=w.REPOSITORY,branch=w.STREAM_BRANCH,store_id=self.d['store_id'],
                        stream_id='test-stream')
        raw, value = pair.restore_fence(folder,manifest,self.root/'restored',self.d,
                                        self.stream.directory,w.STREAM,identity,b.Budget())
        self.assertEqual(json.loads(raw),value)
        self.assertEqual(value['completion']['outcome'],'aborted')
        self.assertEqual(value['cursors'],self.open['cursors'])
        with patch.object(w,'STREAM_HASH','0'*64):
            with self.assertRaises(ValueError):
                pair.restore_fence(folder,manifest,self.root/'bad-restore',self.d,
                                   self.stream.directory,w.STREAM,identity,b.Budget())

    def test_drift_workers_and_job_stop_before_write(self):
        entry = {'path':'recovery/incidents/'+w.FENCE+'.json'}
        for key,value in (('journal','changed'),('stream','changed'),('worker','active'),
                          ('journal_tree',[entry]),
                          ('queue',{'total_count':1,'workflow_runs':[]}),('job_status','in_progress')):
            with self.subTest(key=key), patch.object(self.provider,key,value):
                with self.assertRaises(ValueError):
                    self.execute()
                self.assertFalse(self.reservation.exists())
                self.assertEqual(self.provider.head(w.REPOSITORY,w.FENCE_BRANCH),w.FENCE)

    def test_late_journal_drift_refuses_push(self):
        stage = self.writer.stage
        def race(body):
            commit = stage(body)
            self.provider.journal = 'b'*40
            return commit
        with patch.object(self.writer,'stage',side_effect=race), patch.object(
            self.writer,'close',side_effect=AssertionError('push after journal drift')
        ):
            with self.assertRaises(ValueError):
                self.execute()
        self.assertEqual(self.provider.head(w.REPOSITORY,w.FENCE_BRANCH),w.FENCE)

    def test_fence_lease_stops_identical_blob_at_different_commit(self):
        push = self.writer.close
        def race(commit):
            old_bytes = self.provider.read_at(w.REPOSITORY,w.FENCE,a.FENCE_PATH)['body']
            competitor = write(self.fence,once.REF,a.FENCE_PATH,old_bytes)
            self.assertNotEqual(competitor,w.FENCE)
            push(commit)
        with patch.object(self.writer,'close',side_effect=race):
            with self.assertRaisesRegex(ValueError,'update unconfirmed'):
                self.execute()
        self.assertEqual(self.provider.read(w.REPOSITORY,w.FENCE_BRANCH,a.FENCE_PATH)['body'],
                         canonical(self.open).encode())
        self.assertTrue(self.reservation.exists())

    def test_unclear_readback_consumes_attempt(self):
        self.provider.bad_readback = True
        with self.assertRaisesRegex(ValueError,'update unconfirmed'):
            self.execute()
        pin = json.loads(self.reservation.read_bytes())['close_commit']
        self.assertEqual(self.provider.head(w.REPOSITORY,w.FENCE_BRANCH),pin)
        with patch.object(self.writer,'close',side_effect=AssertionError('second push')):
            with self.assertRaises(ValueError):
                self.execute()


if __name__ == '__main__':
    monitor = install(sys.argv[1],sys.argv[2])
    del sys.argv[1:3]
    import actions_delivery as a
    import watch_abort as w
    import watch_abort_once as once
    import p4_backup_pair as pair
    import p3_backup_chain as b
    from production_contract import canonical, digest
    unittest.main(verbosity=2)
