"""A4 persistent-volume adapter. No provisioning or network access on startup.

Requires one surviving volume with reliable SQLite locks/fsync (not NFS or
independent replicas). See A4-VERTRAG.md. Local files are only projections.
"""
from contextlib import contextmanager, closing
from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
import hashlib
import inspect
import json
import os
from pathlib import Path
import sqlite3

import telegram_outbox as box

active_store = ContextVar('active_delivery_store', default=None)
command_texts = ContextVar('delivery_command_texts', default=None)


def validate(snapshot):
    if not isinstance(snapshot, dict) or snapshot.get('version') != 1:
        raise ValueError('Invalid durable snapshot')
    for key in ('engine', 'watch', 'commands'):
        if not isinstance(snapshot.get(key), dict):
            raise ValueError('Incomplete durable snapshot')
    box.load_delivery(snapshot['engine'])
    if snapshot['engine'].get('demo'):
        raise ValueError('Demo state cannot seed a durable delivery stream')
    if snapshot['engine'] and '_delivery' not in snapshot['engine']:
        raise ValueError('Migration requires engine state with complete delivery projections')
    for entry in snapshot['commands'].values():
        if not isinstance(entry, dict) or '_delivery' not in entry or 'result' not in entry:
            raise ValueError('Incomplete durable command')
        box.load_delivery(entry)


def provision(path, store_id, snapshot):
    """Explicit offline bootstrap from a reviewed complete snapshot; never overwrite.

    Operator must seed existing engine state, projections and watch. An empty
    snapshot is appropriate ONLY for a genuinely new stream, not migration.
    """
    validate(snapshot)
    if not isinstance(store_id, str) or not store_id.strip():
        raise ValueError('Store identity required')
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    with closing(sqlite3.connect(path/'mutex.sqlite')) as lock, lock:
        lock.execute('CREATE TABLE mutex (id INTEGER PRIMARY KEY)')
    with closing(sqlite3.connect(path/'snapshot.sqlite')) as db, db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE snapshot (id INTEGER PRIMARY KEY CHECK(id=1), store_id TEXT, revision INTEGER, body TEXT, digest TEXT)')
        body = box.canonical(snapshot)
        db.execute('INSERT INTO snapshot VALUES (1, ?, 0, ?, ?)',
                   (store_id, body, hashlib.sha256(body.encode()).hexdigest()))


class VolumeStore:
    def __init__(self, path, store_id):
        self.path, self.store_id = Path(path), store_id
        self.db = self.lock = None

    def __enter__(self):
        # mode=rw is essential: a lost/unmounted database must NEVER become empty.
        try:
            self.lock = sqlite3.connect((self.path/'mutex.sqlite').as_uri()+'?mode=rw', uri=True, timeout=0)
            self.lock.execute('BEGIN IMMEDIATE')
            self.db = sqlite3.connect((self.path/'snapshot.sqlite').as_uri()+'?mode=rw', uri=True, timeout=0)
            self.db.execute('PRAGMA synchronous=FULL')
            row = self.db.execute('SELECT store_id,revision,body,digest FROM snapshot WHERE id=1').fetchone()
            if row is None or row[0] != self.store_id or hashlib.sha256(row[2].encode()).hexdigest() != row[3]:
                raise ValueError('Durable store identity/integrity mismatch')
            self.revision = row[1]
            self.snapshot = json.loads(row[2])
            validate(self.snapshot)
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *args):
        if self.db is not None:
            self.db.close()
        if self.lock is not None:
            self.lock.close()
        self.db = self.lock = None

    def commit(self):
        validate(self.snapshot)
        body = box.canonical(self.snapshot)
        with self.db:
            result = self.db.execute('UPDATE snapshot SET revision=revision+1,body=?,digest=? WHERE id=1 AND revision=? AND store_id=?',
                (body, hashlib.sha256(body.encode()).hexdigest(), self.revision, self.store_id))
            if result.rowcount != 1:
                raise RuntimeError('Durable revision conflict')
        self.revision += 1

    def recover(self):
        changed = False
        for state in [self.snapshot['engine'], *self.snapshot['commands'].values()]:
            for m in state.get('_delivery', {}).get('messages', []):
                if m['status'] == 'sending':
                    m['status'], m['reason'] = 'uncertain', 'process_interrupted'
                    changed = True
        if changed:
            self.commit()

    def blocked(self):
        return any(m['status'] in {'sending', 'uncertain'}
                   for state in [self.snapshot['engine'], *self.snapshot['commands'].values()]
                   for m in state.get('_delivery', {}).get('messages', []))


def configured_store(directory):
    raw, sid = os.environ.get('BTC_DELIVERY_STORE'), os.environ.get('BTC_DELIVERY_STORE_ID')
    if not raw or not sid:
        raise RuntimeError('Durable delivery store is not provisioned; send refused')
    path = Path(raw)
    runner_raw = os.environ.get('BTC_DELIVERY_RUNNER_ROOT')
    if not runner_raw or not Path(runner_raw).is_absolute():
        raise ValueError('Absolute BTC_DELIVERY_RUNNER_ROOT required')
    runner = Path(runner_raw).resolve()
    if not Path(directory).resolve().is_relative_to(runner):
        raise ValueError('Data directory outside declared runner')
    if not path.is_absolute() or path.resolve().is_relative_to(runner):
        raise ValueError('Delivery volume must be absolute and outside entire runner')
    return VolumeStore(path.resolve(), sid)


def has_credentials():
    return bool(os.environ.get('TELEGRAM_BOT_TOKEN') and os.environ.get('TELEGRAM_CHAT_ID'))


@contextmanager
def session(directory, dry_run=False):
    # Unconfigured offline runs preserve the established local preview workflow.
    if dry_run or (not has_credentials() and not os.environ.get('BTC_DELIVERY_STORE')):
        yield None
        return
    with configured_store(directory) as store:
        store.recover()
        token = active_store.set(store)
        try:
            yield store
        finally:
            active_store.reset(token)


def restore(store, directory):
    directory.mkdir(parents=True, exist_ok=True)
    box.atomic_json(directory/'state.json', store.snapshot['engine'])
    box.atomic_json(directory/'watch.json', store.snapshot['watch'])
    box.project(store.snapshot['engine'], directory)
    # Empty explicit bootstrap must also overwrite stale checkout projections.
    if '_delivery' not in store.snapshot['engine']:
        box.atomic_json(directory/'signals.json', {'signals': []})
        box.atomic_json(directory/'oi_history.json', [])


@contextmanager
def engine_session(directory, dry_run=False):
    with session(directory, dry_run) as store:
        if store is None:
            yield
            return
        restore(store, directory)
        state_path = (directory/'state.json').resolve()
        def persist(path, state):
            if path.resolve() == state_path:
                store.snapshot['engine'] = deepcopy(state)
                resolution = state.get('_delivery', {}).get('watch_resolution')
                if resolution and store.snapshot['watch'].get('gewarnt_ts') == resolution['gewarnt_ts']:
                    store.snapshot['watch'].update(resolution)
                store.commit()
        token = box.durable_writer.set(persist)
        try:
            yield
        finally:
            box.durable_writer.reset(token)


def can_dispatch():
    store = active_store.get()
    return store is None or not store.blocked()


def stage_text(text):
    batch = command_texts.get()
    if batch is None:
        raise RuntimeError('Direct one-shot send refused: durable command required')
    batch.append(text)
    return True


def durable_command(kind):
    """Freeze a complete one-shot batch before transport; stable request IDs retry it."""
    def decorate(fn):
        signature = inspect.signature(fn)
        @wraps(fn)
        def wrapped(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            directory = Path(bound.arguments['data_dir'])
            dry = bound.arguments.get('dry_run', False)
            if dry or not has_credentials():
                return fn(*args, **kwargs)
            request_id = os.environ.get('BTC_DELIVERY_OPERATION_ID')
            if kind != 'watch' and (not request_id or not request_id.strip()):
                raise ValueError('Stable BTC_DELIVERY_OPERATION_ID required')
            with box.engine_lock(directory), session(directory) as store:
                if store is None:
                    raise RuntimeError('Durable command requires storage')
                directory.mkdir(parents=True, exist_ok=True)
                # Only watch needs an engine projection; lage/test/resend do not
                # overwrite the local trading state as a side effect.
                if kind == 'watch':
                    restore(store, directory)
                key = kind if kind == 'watch' else box.identity('command', kind, 0, request_id)
                commands = store.snapshot['commands']
                entry = commands.get(key)
                def drain(entry):
                    if not can_dispatch():
                        return False
                    def persist(path, state):
                        commands[key] = deepcopy(state)
                        store.commit()
                    token = box.durable_writer.set(persist)
                    try:
                        import telegram_notify as tg
                        return box.drain(entry, directory/'command-delivery.json', tg.deliver_telegram,
                            os.environ['TELEGRAM_BOT_TOKEN'], os.environ['TELEGRAM_CHAT_ID'])
                    finally:
                        box.durable_writer.reset(token)
                if entry is not None:
                    done = drain(entry)
                    if kind != 'watch' or not done:
                        return deepcopy(entry['result'])
                if store.blocked():
                    raise RuntimeError('Uncertain delivery requires manual review')
                batch = []
                token = command_texts.set(batch)
                try:
                    if kind == 'resend':
                        # History must come from durable state, never stale Git.
                        directory.mkdir(parents=True, exist_ok=True)
                        hist = store.snapshot['engine'].get('_delivery', {}).get('signals', {'signals': []})
                        box.atomic_json(directory/'signals.json', hist)
                    result = fn(*args, **kwargs)
                finally:
                    command_texts.reset(token)
                if kind == 'watch' and not batch:
                    return result
                delivery = box.load_delivery(entry or {})
                delivery.update(signals={'signals': []}, oi_history=[])
                event = result['gewarnt_ts'] if kind == 'watch' else request_id
                for index, text in enumerate(batch):
                    box.enqueue(delivery, kind, event, index, {'text': text}, text)
                entry = {'_delivery': delivery, 'result': result}
                commands[key] = entry
                if kind == 'watch':
                    store.snapshot['watch'] = deepcopy(result)
                store.commit()
                drain(entry)
                return result
        return wrapped
    return decorate
