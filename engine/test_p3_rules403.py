"""Rules403 CLI fixtures: local child processes, simulated wire, no real keys."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from email.message import Message
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import types
import urllib.error
import urllib.parse
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'engine')]
import p3_github_probe as p
import p3_reader401_continue as c
import p3_rules403 as r
import p3_http_diagnostics as errors
import p3_probe_simulation as sim
import test_p3_reader401 as previous
from test_p3_github_probe import rejects


def save(path, value): previous.save(path, value)
def read(path): return previous.read(path)
def deny(*a, **kw): raise AssertionError('External network forbidden')


def http_error(url, status, message='Not Found', headers=None, raw=None):
    h = Message(); h['Content-Type'] = 'application/json'
    for k, v in (headers or {}).items(): h[k] = v
    raw = raw if raw is not None else p.canonical({'message': message, 'documentation_url': 'https://docs.github.com/rest', 'status': str(status)}).encode()
    return urllib.error.HTTPError(url, status, 'fixture', h, io.BytesIO(raw))


class RulesAPI(sim.API):
    def __init__(self, plan, mode='positive'):
        super().__init__(plan); self.head = None; self.mode = mode

    def open(self, req, **kw):
        path = urllib.parse.urlsplit(req.full_url).path
        if path.endswith('/pages') or path.endswith('/protection'):
            self.trace.append((req.method, path)); raise http_error(req.full_url, 404)
        if '/rules/branches/' in path and self.mode != 'positive':
            self.trace.append((req.method, path))
            if self.mode == 'feature': raise http_error(req.full_url, 403, sorted(errors.FEATURE_MESSAGES)[0])
            if self.mode == 'rights': raise http_error(req.full_url, 403, 'Resource not accessible by personal access token', {'X-Accepted-GitHub-Permissions': 'metadata=read'})
            if self.mode == 'rate': raise http_error(req.full_url, 403, 'API rate limit exceeded for fixture.', {'X-RateLimit-Remaining': '0'})
            if self.mode == 'unknown': raise http_error(req.full_url, 403, 'Unspecified denial')
            if self.mode == 'long': raise http_error(req.full_url, 403, raw=b'x'*5000)
            if self.mode == 'ambiguous': raise http_error(req.full_url, 403, sorted(errors.FEATURE_MESSAGES)[0], {'X-RateLimit-Remaining': '0'})
            if self.mode == 'timeout': raise TimeoutError('fixture')
            raise AssertionError('bad fixture mode')
        return super().open(req, **kw)


def historical_fixture(td):
    plan, a = previous.fixture(td); root = Path(td)
    a['execution_code'] = {'code_head': r.BASE_HEAD, 'code_tree': r.BASE_TREE,
        'code_pins': {name: hashlib.sha256(c.git(ROOT, 'show', r.BASE_HEAD+':'+name)).hexdigest()
                      for name in set(plan['code_pins']) | c.EXTRA_PINS}}
    save(root/'reader-amendment.json', a)
    proc = subprocess.Popen([sys.executable, str(Path(__file__)), '--reader-worker', td],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.wait(timeout=90) == 0, proc.stderr.read().decode()
    rows = p.Ledger.verify(root/(c.PHASE+'.jsonl'), p.digest(plan))
    assert len(rows) == 17 and rows[5]['pid'] == proc.pid
    save(root/'reader-parent-wait-fixture.json', {'pid': proc.pid, 'exit_code': proc.returncode})
    return plan, amendment(root, r.DIAG)


def amendment(root, phase):
    root = Path(root); plan = read(root/'plan.json'); a = r.template(phase)
    olda = read(root/'reader-amendment.json'); oldg = read(root/'reader-grant.json')
    journal = c.PHASE+'.jsonl' if phase == r.DIAG else r.DIAG+'.jsonl'
    rows = p.Ledger.verify(root/journal, p.digest(plan))
    a.update(original_plan_sha256=p.digest(plan), reader401_amendment=olda, reader401_grant=oldg,
             reader401_code_materialization=r.materialization(olda['execution_code']), root=olda['root'],
             routes=r.routes(plan), expires_utc='2099-01-01T00:00:00Z')
    a['execution_code'] = {'code_head': 'f'*40, 'code_tree': 'e'*40,
        'code_pins': {name: 'e'*64 for name in set(olda['execution_code']['code_pins']) | r.EXTRA_PINS}}
    a['predecessor'].update(journal=journal, frontier_hash=rows[-1]['hash'], frontier_rows=len(rows),
        highwater=rows[-1]['utc'], counts=rows[-1]['counts'],
        files_sha256={name: c.sha(root/name) for name in r.session_files(rows)})
    latest = [x for x in rows if x['event'] == 'phase_start'][-1]
    a['review'].update(reviewer='offline-fixture-only', evidence_sha256='a'*64, original_pid=latest['pid'],
        observed_utc=p.utc(), terminal_code_path_checked=True, human_terminal_end_report=True,
        all_workers_ended=True, triggers_paused=True, human_review=True)
    if phase == r.UPLOAD:
        a['diagnosis'] = {'amendment': read(root/(r.DIAG+'-amendment.json')), 'grant': read(root/(r.DIAG+'-grant.json'))}
        a['execution_code'] = a['diagnosis']['amendment']['execution_code']
    return a


def fixture_grant(plan, a):
    g = sim.fixture_grant(plan, a['phase']); g['review_sha256'] = p.digest(a); return g


def cli(td, a, grant=None, mode='positive', prompt=None, checkpoint=None, patch_code=True, api=None, push_hook=None):
    root = Path(td); plan = read(root/'plan.json'); phase = a['phase']; grant = grant or fixture_grant(plan, a)
    save(root/(phase+'-amendment.json'), a); save(root/(phase+'-grant.json'), grant)
    api = api or RulesAPI(plan, mode); prompts = []; pushes = []; original_run = subprocess.run
    attempts = root/'fixture-attempts'; attempts.mkdir(exist_ok=True)
    attempt = attempts/('%03d'%len(list(attempts.iterdir()))); attempt.mkdir()
    save(attempt/'amendment.json', a); save(attempt/'grant.json', grant)
    def wire(method):
        db = sqlite3.connect((root/'probe-session.sqlite3').as_uri()+'?mode=ro', uri=True)
        last = previous.read_latest(db); state = db.execute('SELECT published FROM frontier').fetchone()[0]; db.close()
        assert last['hash'] == state and last['event'] == 'request' and last['method'] == method
        assert last['counts']['GET'] >= 6
        with (root/(phase+'-fixture-wire.jsonl')).open('a', encoding='utf-8') as f:
            f.write(p.canonical({'method': method, 'published': state})+'\n'); f.flush(); os.fsync(f.fileno())
    original_open = api.open
    def opened(req, **kw): wire(req.method); return original_open(req, **kw)
    def run(args, **kw):
        if 'push' not in args: return original_run(args, **kw)
        assert phase == r.UPLOAD and args[-1] == plan['seed_commit']+':refs/heads/'+plan['branch']
        assert kw['env']['P3_EXPLICIT_BOOTSTRAP_TOKEN'] == sim.FIXTURE_TOKEN
        wire('GIT_PUSH'); pushes.append('fixture'); api.head = plan['seed_commit']
        if push_hook: push_hook()
        return types.SimpleNamespace(returncode=0)
    def ask(label):
        prompts.append(label)
        assert phase != r.DIAG or label.startswith('Reader')
        return prompt(label) if prompt else sim.FIXTURE_TOKEN
    argv = ['rules', '--real', '--phase', phase, '--plan', str(root/'plan.json'), '--amendment', str(root/(phase+'-amendment.json')),
            '--grant', str(root/(phase+'-grant.json')), '--approved-amendment-sha256', p.digest(a)]
    outcome = 'raised'
    with ExitStack() as stack:
        for obj, name, val in [(sys, 'argv', argv), (p.getpass, 'getpass', ask), (subprocess, 'run', run),
            (socket.socket, 'connect', deny), (socket.socket, 'connect_ex', deny), (socket, 'create_connection', deny),
            (p.urllib.request, 'urlopen', deny)]: stack.enter_context(patch.object(obj, name, val))
        stack.enter_context(patch.object(p.urllib.request, 'build_opener', return_value=types.SimpleNamespace(open=opened)))
        if patch_code: stack.enter_context(patch.object(r, 'verify_execution_code', lambda _: None))
        if checkpoint: stack.enter_context(patch.object(p.Ledger, 'checkpoint', checkpoint))
        try: result = r.main(); outcome = 'returned-'+str(result); return result
        finally:
            value = {'phase': phase, 'http': api.trace, 'pushes': len(pushes), 'prompts': prompts, 'outcome': outcome}
            save(root/'fixture-latest.json', value); save(attempt/'outcome.json', value)


def completed_diagnosis(td, a, mode='positive'):
    root = Path(td); save(root/'pending-amendment.json', a)
    proc = subprocess.Popen([sys.executable, str(Path(__file__)), '--phase-worker', td, mode],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    expected = 0 if mode == 'positive' else 2
    assert proc.wait(timeout=90) == expected, proc.stderr.read().decode()
    save(root/'diagnosis-parent-wait-fixture.json', {'pid': proc.pid, 'exit_code': proc.returncode})
    return amendment(root, r.UPLOAD)


def test_rules403_positive_reader_only_diagnosis_then_separate_upload_and_replays():
    with tempfile.TemporaryDirectory() as td:
        plan, a = historical_fixture(td); root = Path(td); oldbytes = (root/(c.PHASE+'.jsonl')).read_bytes()
        upload = completed_diagnosis(td, a)
        wire = read(root/'fixture-latest.json'); assert len(wire['prompts']) == 1 and wire['pushes'] == 0 and len(wire['http']) == 7
        rows = p.Ledger.verify(root/(r.DIAG+'.jsonl'), p.digest(plan)); assert len(rows) == 36 and rows[-1]['counts']['GET'] == 12
        rejects(ValueError, lambda: cli(td, a))
        assert not read(root/'fixture-latest.json')['prompts']
        assert cli(td, upload) == 0
        rows = p.Ledger.verify(root/(r.UPLOAD+'.jsonl'), p.digest(plan))
        assert rows[-1]['counts'] == {'GET': 35, 'PUT': 0, 'GIT_PUSH': 1}, rows[-1]['counts']
        assert rows[-1]['scope'] == 'blocked-root-only-no-activation'
        assert (root/(r.UPLOAD+'.jsonl')).read_bytes().startswith(oldbytes)
        assert (root/(c.PHASE+'.jsonl')).read_bytes() == oldbytes
        rejects(ValueError, lambda: cli(td, upload))
        rejects(ValueError, lambda: p.Ledger(plan, root/'activate.jsonl', 'activate', root/(r.UPLOAD+'.jsonl')))


def test_rules403_feature_hint_is_diagnosed_but_never_empty_rules_or_upload_authority():
    with tempfile.TemporaryDirectory() as td:
        plan, a = historical_fixture(td); upload = completed_diagnosis(td, a, 'feature')
        rows = p.Ledger.verify(Path(td,r.DIAG+'.jsonl'), p.digest(plan))
        assert rows[-1]['result'] == 'confirmed' and rows[-1]['scope'] == 'read-only-diagnosis'
        assert rows[-2]['upload_eligible'] is False and rows[-2]['feature_absence_proved'] is False
        rejects(ValueError, lambda: cli(td, upload))
        assert read(Path(td,'fixture-latest.json'))['prompts'] == []


def test_rules403_permission_rate_unknown_ambiguous_long_and_lost_answers_stop():
    for mode, category in [('rights','permission-denied-hint'), ('rate','rate-limit-hint'), ('unknown','unknown-403'),
                          ('ambiguous','ambiguous-error-response'), ('long','invalid-error-response'), ('timeout','incomplete-or-expired')]:
        with tempfile.TemporaryDirectory() as td:
            plan, a = historical_fixture(td)
            rejects((r.Halt, p.gh.StoreUnavailable), lambda: cli(td, a, mode=mode))
            rows = p.Ledger.verify(Path(td,r.DIAG+'.jsonl'), p.digest(plan))
            assert rows[-1]['event'] == 'phase_halt' and rows[-1]['category'] == category
            assert rows[-1]['counts'] == {'GET': 9, 'PUT': 0, 'GIT_PUSH': 0}
            assert len(read(Path(td,'fixture-latest.json'))['prompts']) == 1
            rejects(ValueError, lambda: cli(td, a))


def test_rules403_error_parser_is_bounded_redacted_and_rejects_ambiguous_fields():
    url = 'https://api.github.com/repos/synthetic/fixture/rules/branches/test'
    marker = 'PRIVATE_FIXTURE_DO_NOT_LOG'
    cases = [b'x'*5000, b'{"message":"Not Found","message":"oops","documentation_url":"https://docs.github.com/rest"}',
        p.canonical({'message':'Not Found','documentation_url':'https://evil.invalid/'+marker}).encode(),
        p.canonical({'message':'Not Found','documentation_url':'https://docs.github.com/rest','extra':marker}).encode(),
        p.canonical({'message':'x'*513,'documentation_url':'https://docs.github.com/rest'}).encode()]
    for raw in cases:
        result = errors.classify(http_error(url,403,raw=raw)); assert result['category'] == 'invalid-error-response'
        assert marker not in p.canonical(result)
    for headers in [{'X-RateLimit-Remaining':'-1'}, {'Retry-After':'1000000'},
                    {'X-Accepted-GitHub-Permissions':marker}, {'Content-Type':'text/html'}]:
        assert errors.classify(http_error(url,403,'deny',headers))['category'] == 'invalid-error-response'
    e = http_error(url,403,'deny'); e.headers['X-RateLimit-Remaining']='0'; e.headers['X-RateLimit-Remaining']='10'
    assert errors.classify(e)['category'] == 'invalid-error-response'
    result = errors.classify(http_error(url,403,'Resource not accessible by personal access token', {'X-Accepted-GitHub-Permissions':'metadata=read; contents=read,metadata=read'}))
    assert result['category']=='permission-denied-hint' and len(result['accepted_permission_sets'])==2
    result = errors.classify(http_error(url,403,marker)); assert marker not in p.canonical(result) and result['category']=='unknown-403'


def test_rules403_wrong_grant_plan_code_routes_end_review_and_seed_deny_before_input():
    with tempfile.TemporaryDirectory() as td:
        plan, a = historical_fixture(td); root = Path(td)
        for mode in ('grant','expiry','review','route','plan','code','history','end'):
            changed = deepcopy(a); g = fixture_grant(plan, changed)
            if mode == 'grant': g['human_authorization'] = False
            if mode == 'expiry': g['expires_utc'] = '2020-01-01T00:00:00Z'
            if mode == 'review': g['review_sha256'] = '0'*64
            if mode == 'route': changed['routes'][0] = '/user'
            if mode == 'plan': changed['original_plan_sha256'] = '0'*64
            if mode == 'code': changed['reader401_amendment']['execution_code']['code_head'] = '0'*40
            if mode == 'history': changed['reader401_code_materialization'] = {}
            if mode == 'end': changed['review']['human_terminal_end_report'] = False
            if changed != a: g['review_sha256'] = p.digest(changed)
            rejects(ValueError, lambda: cli(td, changed, g))
            assert read(root/'fixture-latest.json')['prompts'] == []
        ref = root/'execution/refs/heads'/plan['branch']; raw = ref.read_bytes(); ref.write_text('0'*40+'\n')
        try: rejects(ValueError, lambda: cli(td,a))
        finally: ref.write_bytes(raw)
        assert read(root/'fixture-latest.json')['prompts'] == []


def test_rules403_missing_files_altered_frontier_and_prior_write_or_unknown_deny():
    with tempfile.TemporaryDirectory() as td:
        plan, a = historical_fixture(td); root = Path(td)
        for name in ('probe-session.sqlite3','attempt-'+c.PHASE+'.json','bootstrap.jsonl'):
            path=root/name; held=root/(name+'.held'); path.rename(held)
            try: rejects((ValueError,FileNotFoundError),lambda:cli(td,a)); assert read(root/'fixture-latest.json')['prompts']==[]
            finally: held.rename(path)
        for field in ('frontier_hash','frontier_rows','counts'):
            changed=deepcopy(a); changed['predecessor'][field]={'frontier_hash':'0'*64,'frontier_rows':5,'counts':{'GET':1,'PUT':0,'GIT_PUSH':0}}[field]
            rejects(ValueError,lambda:cli(td,changed));assert read(root/'fixture-latest.json')['prompts']==[]
        rows=p.Ledger.verify(root/(c.PHASE+'.jsonl'),p.digest(plan))
        for mode in ('PUT','GIT_PUSH','unknown'):
            changed=deepcopy(rows)
            if mode=='unknown':changed[15]['result']='unknown'
            else:changed[14]['method']=mode
            rejects(ValueError,lambda:r.validate_history(plan,changed,a))
        ledger=p.Ledger(plan,root/(r.DIAG+'.jsonl'),r.DIAG,root/(c.PHASE+'.jsonl'),rules403_amendment=a)
        try:
            rejects((ValueError,OSError),lambda:cli(td,a))
            for phase in ('inspect','takeover'):
                rejects((ValueError,OSError),lambda:p.Ledger(plan,root/'other.jsonl',phase,ledger.path))
            for method in ('PUT','GIT_PUSH'):rejects(ValueError,lambda:ledger.charge(method))
            for _ in range(8):ledger.charge('GET')
            rejects(ValueError,lambda:ledger.charge('GET'))
            assert ledger.counts['GET']==ledger.cases['bootstrap']['GET']==13
        finally:ledger.close()


def test_rules403_upload_needs_new_grant_latest_frontier_and_fresh_rules_before_writer():
    with tempfile.TemporaryDirectory() as td:
        plan,a=historical_fixture(td); upload=completed_diagnosis(td,a); root=Path(td)
        rejects(ValueError,lambda:cli(td,upload,grant=fixture_grant(plan,a)))
        changed=deepcopy(upload);changed['predecessor']=deepcopy(a['predecessor'])
        rejects(ValueError,lambda:cli(td,changed));assert read(root/'fixture-latest.json')['prompts']==[]
        rejects(p.HTTPStatus,lambda:cli(td,upload,mode='feature'))
        wire=read(root/'fixture-latest.json');assert wire['pushes']==0 and len(wire['prompts'])==1
        rows=p.Ledger.verify(root/(r.UPLOAD+'.jsonl'),p.digest(plan))
        assert rows[-1]['counts']['GIT_PUSH']==0 and rows[-1]['event']=='phase_halt'


class Clock(datetime):
    current=None
    @classmethod
    def now(cls,tz=None):return cls.current if tz else cls.current.replace(tzinfo=None)


def test_rules403_credential_preflight_and_late_push_expiry_never_confirm_or_retry():
    for where in ('reader', 'preflight', 'writer', 'late-push'):
        with tempfile.TemporaryDirectory() as td:
            plan,a=historical_fixture(td)
            if where in ('writer','late-push'):a=completed_diagnosis(td,a)
            Clock.current=datetime.now(timezone.utc)+timedelta(seconds=1);deadline=Clock.current+timedelta(seconds=60)
            g=fixture_grant(plan,a);g['expires_utc']=deadline.isoformat().replace('+00:00','Z')
            def prompt(label):
                if where=='reader' or (where=='writer' and label.startswith('Writer')):Clock.current=deadline
                return sim.FIXTURE_TOKEN
            api=RulesAPI(plan);opened=api.open
            def response(req,**kw):
                result=opened(req,**kw)
                if where=='preflight':Clock.current=deadline
                return result
            api.open=response
            def late():
                Clock.current=deadline
                raise subprocess.TimeoutExpired('fixture-push',15)
            with patch.object(p,'datetime',Clock):
                rejects(ValueError,lambda:cli(td,a,g,prompt=prompt,api=api,push_hook=late if where=='late-push' else None))
            rows=p.Ledger.verify(Path(td,a['phase']+'.jsonl'),p.digest(plan));wire=read(Path(td,'fixture-latest.json'))
            assert rows[-1]['event']=='phase_halt' and wire['pushes']==int(where=='late-push')
            assert len(wire['http'])=={'reader':0,'preflight':1,'writer':7,'late-push':7}[where]
            assert rows[-1]['counts']=={'GET':{'reader':5,'preflight':6,'writer':19,'late-push':19}[where],
                                        'PUT':0,'GIT_PUSH':int(where=='late-push')}
            rejects(ValueError,lambda:cli(td,a));assert not read(Path(td,'fixture-latest.json'))['prompts']


def test_rules403_rehashed_prior_write_unknown_and_live_pid_actual_cli():
    for mode in ('PUT','GIT_PUSH','unknown','live-pid'):
        with tempfile.TemporaryDirectory() as td:
            plan,a=historical_fixture(td);root=Path(td)
            rows=p.Ledger.verify(root/(c.PHASE+'.jsonl'),p.digest(plan))
            if mode=='unknown':rows[15]['result']='unknown'
            elif mode=='live-pid':rows[5]['pid']=os.getpid()
            else:rows[14]['method']=mode
            counts={'GET':0,'PUT':0,'GIT_PUSH':0};prev='0'*64
            for row in rows:
                row.pop('hash');row['previous_hash']=prev
                if row['event']=='request':counts[row['method']]+=1
                row['counts']=dict(counts);row['hash']=p.digest(row);prev=row['hash']
            db=sqlite3.connect(root/'probe-session.sqlite3')
            for i,row in enumerate(rows,1):db.execute('UPDATE events SET body=? WHERE seq=?',(p.canonical(row),i))
            db.execute('UPDATE frontier SET published=?',(rows[-1]['hash'],));db.commit();db.close()
            (root/(c.PHASE+'.jsonl')).write_text(''.join(p.canonical(row)+'\n' for row in rows),encoding='utf-8',newline='\n')
            save(root/('attempt-'+c.PHASE+'.json'),{key:rows[5][key] for key in ('plan_sha256','phase','journal','pid','predecessor')})
            a=amendment(root,r.DIAG)
            save(root/'semantic-countercase.json',{'mode':mode,'fixture_history_rehashed':True,'live_pid':os.getpid() if mode=='live-pid' else None})
            rejects(ValueError,lambda:cli(td,a));wire=read(root/'fixture-latest.json')
            assert not wire['prompts'] and not wire['http'] and not wire['pushes']


def test_rules403_foreign_route_rejected_before_request_reservation():
    with tempfile.TemporaryDirectory() as td:
        plan,a=historical_fixture(td);root=Path(td);g=fixture_grant(plan,a)
        ledger=p.Ledger(plan,root/(r.DIAG+'.jsonl'),r.DIAG,root/(c.PHASE+'.jsonl'),rules403_amendment=a)
        try:
            boundary=r.RulesBoundary(plan,ledger,sim.FIXTURE_TOKEN,'',guard=r.RulesGuard(plan,g,a))
            for route in ('/user',r.routes(plan)[0]+'/contents/foreign',r.routes(plan)[3]+'&unexpected=1'):
                rejects(ValueError,lambda:boundary.request('GET',route))
            assert ledger.counts=={'GET':5,'PUT':0,'GIT_PUSH':0}
        finally:ledger.close()


def test_rules403_exact_grant_deadline_before_http_and_git():
    for phase in (r.DIAG,r.UPLOAD):
        with tempfile.TemporaryDirectory() as td:
            plan,a=historical_fixture(td)
            if phase==r.UPLOAD:a=completed_diagnosis(td,a)
            Clock.current=datetime.now(timezone.utc)+timedelta(seconds=1); deadline=Clock.current+timedelta(seconds=60)
            g=fixture_grant(plan,a);g['expires_utc']=deadline.isoformat().replace('+00:00','Z')
            def checkpoint(self,point,event):
                if point=='before_outbound' and event==('GET' if phase==r.DIAG else 'GIT_PUSH'):Clock.current=deadline
            with patch.object(p,'datetime',Clock):rejects(ValueError,lambda:cli(td,a,g,checkpoint=checkpoint))
            wire=read(Path(td,'fixture-latest.json'));assert wire['pushes']==0
            assert len(wire['http'])==(0 if phase==r.DIAG else 7)
            rows=p.Ledger.verify(Path(td,phase+'.jsonl'),p.digest(plan));assert rows[-1]['event']=='phase_halt'
            assert rows[-1]['counts']=={'GET':6 if phase==r.DIAG else 19,'PUT':0,'GIT_PUSH':int(phase==r.UPLOAD)}


def test_rules403_hard_loss_keeps_exact_reservations_and_never_replays():
    points=[('after_intent','phase_start'),('before_commit','rules403_amendment'),('after_commit','rules403_amendment'),
            ('after_mirror','rules403_amendment'),('after_publish','rules403_amendment'),
            ('before_commit','request'),('after_commit','request'),('after_mirror','request'),('after_publish','request'),
            ('before_outbound','GET'),('before_outbound','GIT_PUSH')]
    for point,event in points:
        with tempfile.TemporaryDirectory() as td:
            plan,a=historical_fixture(td)
            if event=='GIT_PUSH':a=completed_diagnosis(td,a)
            save(Path(td,'pending-amendment.json'),a)
            proc=subprocess.Popen([sys.executable,str(Path(__file__)),'--kill',td,point,event],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            assert proc.wait(timeout=90)==71,proc.stderr.read().decode()
            save(Path(td,'hard-loss-parent-wait-fixture.json'),{'point':point,'event':event,'pid':proc.pid,'exit_code':proc.returncode})
            db=sqlite3.connect(Path(td,'probe-session.sqlite3'));last=previous.read_latest(db);db.close()
            expected=19 if event=='GIT_PUSH' else 5+int(event in ('request','GET') and point!='before_commit')
            assert last['counts']=={'GET':expected,'PUT':0,'GIT_PUSH':int(event=='GIT_PUSH')}
            wire=Path(td,a['phase']+'-fixture-wire.jsonl')
            assert (len(wire.read_text().splitlines()) if wire.exists() else 0)==(7 if event=='GIT_PUSH' else 0)
            rejects(ValueError,lambda:cli(td,a));assert not read(Path(td,'fixture-latest.json'))['prompts']


def worker():
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=p.urllib.request.urlopen=deny
    kind,td=sys.argv[1:3];root=Path(td)
    if kind=='--reader-worker':
        plan=read(root/'plan.json');a=read(root/'reader-amendment.json');api=RulesAPI(plan,'unknown')
        try:previous.cli(td,plan,a,api=api)
        except p.HTTPStatus as exc:assert exc.status==403
        else:raise AssertionError('Expected original403')
        save(root/'reader-grant.json',read(root/'grant.json'));return 0
    a=read(root/'pending-amendment.json')
    if kind=='--phase-worker':return cli(td,a,mode=sys.argv[3])
    point,event=sys.argv[3:5]
    def checkpoint(self,here,what):
        if here==point and what==event:
            save(root/'fixture-killpoint.json',{'point':point,'event':event,'pid':os.getpid()})
            os._exit(71)
    cli(td,a,checkpoint=checkpoint);raise AssertionError('Kill point missed')


if __name__=='__main__':sys.exit(worker())
