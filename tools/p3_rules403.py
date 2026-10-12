"""One reviewed Reader-only rules diagnosis, then a separately reviewed root upload.

No 403 is accepted as empty rules. No feature-unavailable bypass is implemented.
Default/import are offline; no function issues a human authorization.
"""
import sys

if __name__ == '__main__':
    # Dispatch BEFORE defining classes: script and imports use precisely one
    # canonical security contract. Boundary's strict isinstance check stays.
    from p3_rules403 import main as _canonical_main
    try: sys.exit(_canonical_main())
    except Exception:
        print('HALT: Freigabe, Bindung oder Abschluss fehlt. Ergebnis liegt gegebenenfalls im Originalplan-Journalordner. Keine Schluesselwerte melden.', file=sys.stderr)
        sys.exit(2)

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import urllib.parse

import p3_github_probe as p
import p3_reader401_continue as old

BASE_HEAD = '0128237e4ed72fc3b11fad5249b20770e9eef725'
BASE_TREE = '69de229f4c1954ec5255e068d5252d8a8bdd534c'
DIAG, UPLOAD, RESUME = p.RULES_PHASES
SCRIPT_HEAD = '4c157a780d4db8482edcaab88d35d81dbcb17e54'
SCRIPT_TREE = '0a2931ee742b5a4adae2bedaa7b81fef9e56ce60'
EXTRA_PINS = {'tools/p3_rules403.py', 'tools/p3_http_diagnostics.py', 'tools/p3_rules403_start.ps1'}
SCOPES = {DIAG: 'reader-only-seven-fixed-routes-max-eight-GET-no-mutation',
          RESUME: 'reader-only-exact-21-row-pre-request-halt-shared-eight-GET-no-mutation',
          UPLOAD: 'one-original-root-push-positive-rules-only-no-activation'}
END_BASIS = 'terminal-synchronous-phase-plus-human-end-report-fresh-os-check-exclusive-lock'


class Halt(ValueError):
    """Only code-defined enum categories enter operator output."""
    def __init__(self, category):
        self.category = category
        super().__init__(category)


def routes(plan):
    base = p.gh.GitHubContentsClient._route(plan['repo'], '')
    branch = urllib.parse.quote(plan['branch'], safe='')
    return [base, base+'/actions/permissions', base+'/pages',
            base+'/rules/branches/'+branch+'?per_page=100&page=1',
            base+'/rulesets?includes_parents=true&per_page=100&page=1',
            base+'/branches?per_page=100&page=1', base+'/branches/'+branch+'/protection']


def template(phase=DIAG):
    p.require(phase in p.RULES_PHASES, 'Unknown recovery phase')
    value = {'schema': 'p3-rules403-amendment-v1', 'phase': phase, 'scope': SCOPES[phase],
        'original_plan_sha256': None, 'reader401_amendment': None, 'reader401_grant': None,
        'reader401_code_materialization': None,
        'execution_code': {'code_head': None, 'code_tree': None, 'code_pins': None},
        'predecessor': {'journal': old.PHASE+'.jsonl' if phase == DIAG else DIAG+'.jsonl',
            'frontier_hash': None, 'frontier_rows': None, 'highwater': None,
            'counts': None, 'files_sha256': None},
        'root': {'directory': None, 'files_sha256': None}, 'routes': None,
        'review': {'reviewer': None, 'evidence_sha256': None, 'original_pid': None, 'observed_utc': None,
            'end_basis': END_BASIS, 'terminal_code_path_checked': False, 'human_terminal_end_report': False,
            'all_workers_ended': False, 'triggers_paused': False, 'human_review': False},
        'diagnosis': None, 'expires_utc': None}
    if phase == RESUME:
        value['schema'] = 'p3-rules403-preget-amendment-v1'
        value['interrupted_diagnosis'] = {'amendment': None, 'grant': None, 'code_materialization': None}
    return value


def grant_template(phase=DIAG):
    return {'schema': 'p3-human-grant-v2', 'plan_sha256': None, 'phase': phase,
            'approved_by': None, 'human_authorization': False, 'expires_utc': None,
            'approval_evidence_sha256': None, 'review_sha256': None}


def materialization(execution):
    result = {}
    for name, expected in execution['code_pins'].items():
        p.require(not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name,
                  'Invalid historical code path')
        raw = old.git(p.ROOT, 'show', execution['code_head']+':'+name)
        canonical = hashlib.sha256(raw).hexdigest(); transform = 'identity'
        if expected != canonical:
            p.require(b'\r' not in raw and hashlib.sha256(raw.replace(b'\n', b'\r\n')).hexdigest() == expected,
                      'Historical working bytes not proved')
            transform = 'lf-to-crlf'
        result[name] = {'git_blob_sha256': canonical, 'working_sha256': expected, 'transform': transform}
    return result


def verify_historical_code(plan, a):
    reader = a['reader401_amendment']; code = reader['execution_code']
    old.verify_original_code(plan, reader['original_code_materialization'])
    p.require(reader['original_plan_sha256'] == p.digest(plan) and code['code_head'] == BASE_HEAD
              and code['code_tree'] == BASE_TREE and reader['original_code_head'] == old.ORIGINAL_HEAD
              and reader['original_code_tree'] == old.ORIGINAL_TREE, 'Wrong historical reader executor')
    p.require(old.git(p.ROOT, 'rev-parse', BASE_HEAD+'^{tree}').decode().strip() == BASE_TREE,
              'Original reader tree absent')
    p.require(set(code['code_pins']) >= set(plan['code_pins']) | old.EXTRA_PINS
              and a['reader401_code_materialization'] == materialization(code), 'Reader code pins differ')
    if a['phase'] == RESUME:
        prior = a['interrupted_diagnosis']; execution = prior['amendment']['execution_code']
        p.require(execution['code_head'] == SCRIPT_HEAD and execution['code_tree'] == SCRIPT_TREE
                  and old.git(p.ROOT, 'rev-parse', SCRIPT_HEAD+'^{tree}').decode().strip() == SCRIPT_TREE
                  and prior['code_materialization'] == materialization(execution), 'Wrong historical script executor')
        names = set(plan['code_pins']) | set(old.git(p.ROOT, 'diff', '--name-only', old.ORIGINAL_HEAD, SCRIPT_HEAD).decode().splitlines())
        p.require(set(execution['code_pins']) == names, 'Complete historical script pins required')
        old.git(p.ROOT, 'merge-base', '--is-ancestor', SCRIPT_HEAD, a['execution_code']['code_head'])
    elif a['phase'] == UPLOAD and a['diagnosis']['amendment']['phase'] == RESUME:
        verify_historical_code(plan, a['diagnosis']['amendment'])


def verify_execution_code(execution):
    p.verify_code_pin(execution)
    old.git(p.ROOT, 'merge-base', '--is-ancestor', BASE_HEAD, execution['code_head'])


def validate_grant(plan, grant, phase, review_hash):
    p.require(set(grant) == set(grant_template(phase)) and grant['schema'] == 'p3-human-grant-v2'
              and grant['plan_sha256'] == p.digest(plan) and grant['phase'] == phase
              and grant['review_sha256'] == review_hash and grant['human_authorization'] is True
              and isinstance(grant['approved_by'], str) and bool(grant['approved_by'])
              and re.fullmatch('[0-9a-f]{64}', grant['approval_evidence_sha256'] or ''), 'Bound human grant required')


def validate_shape(plan, a):
    phase = a['phase']; t = template(phase)
    p.require(set(a) == set(t) and a['schema'] == t['schema'] and a['scope'] == SCOPES[phase]
              and a['original_plan_sha256'] == p.digest(plan) and a['routes'] == routes(plan), 'Exact recovery scope required')
    for key in ('execution_code', 'predecessor', 'root', 'review'):
        p.require(set(a[key]) == set(t[key]), 'Incomplete review binding')
    p.require(a['root'] == a['reader401_amendment']['root'], 'Original root binding changed')
    p.require(a['execution_code']['code_head'] != BASE_HEAD
              and set(a['execution_code']['code_pins']) >= set(a['reader401_amendment']['execution_code']['code_pins']) | EXTRA_PINS,
              'New complete executor pins required')
    if phase in (DIAG, RESUME): p.require(a['diagnosis'] is None, 'Diagnosis cannot carry upload authority')
    else:
        d = a['diagnosis']
        p.require(isinstance(d, dict) and set(d) == {'amendment', 'grant'}, 'Exact completed diagnosis review required')
        prior = d['amendment']
        p.require(prior['phase'] in (DIAG, RESUME) and prior['execution_code'] == a['execution_code']
                  and prior['reader401_amendment'] == a['reader401_amendment']
                  and prior['reader401_grant'] == a['reader401_grant'] and prior['root'] == a['root'],
                  'Diagnosis/executor/history changed')
        validate_shape(plan, prior)
        validate_grant(plan, d['grant'], prior['phase'], p.digest(prior))
    if phase == RESUME:
        d = a['interrupted_diagnosis']
        p.require(isinstance(d, dict) and set(d) == {'amendment', 'grant', 'code_materialization'}, 'Exact interrupted diagnosis required')
        prior = d['amendment']
        p.require(prior['phase'] == DIAG and prior['reader401_amendment'] == a['reader401_amendment']
                  and prior['reader401_grant'] == a['reader401_grant'] and prior['root'] == a['root']
                  and a['execution_code']['code_head'] != SCRIPT_HEAD
                  and set(a['execution_code']['code_pins']) >= set(prior['execution_code']['code_pins']),
                  'Original diagnosis/history or new executor mismatch')
        validate_shape(plan, prior); validate_grant(plan, d['grant'], DIAG, p.digest(prior))


def authorize(plan, a, grant, approved_hash):
    p.validate_plan(plan); validate_shape(plan, a)
    p.require(p.digest(a) == approved_hash, 'Independent amendment hash required')
    validate_grant(plan, grant, a['phase'], approved_hash)
    p.require(old.parse_utc(grant['expires_utc']) <= old.parse_utc(a['expires_utc']), 'Grant outlives amendment')
    guard = RulesGuard(plan, grant, a)
    verify_historical_code(plan, a); verify_execution_code(a['execution_code'])
    return guard


class RulesGuard(p.GrantGuard):
    def __init__(self, plan, grant, a):
        self.amendment, self.amendment_hash = deepcopy(a), p.digest(a)
        super().__init__(plan, grant, a['phase'])

    def check(self, ledger=None):
        super().check(ledger)
        p.require(p.digest(self.amendment) == self.amendment_hash == self.grant['review_sha256']
                  and self.amendment['original_plan_sha256'] == self.plan_hash
                  and p.datetime.now(p.timezone.utc) < old.parse_utc(self.amendment['expires_utc']), 'Amendment changed/expired')
        if ledger:
            p.require(ledger.rules403_hash == self.amendment_hash, 'Live review differs from ledger')
            old.root_matches(self.amendment)

    def validate_route(self, method, route):
        p.require(method == 'GET', 'Recovery phases forbid mutating HTTP')
        fixed = routes(self.p)
        if route in fixed: return
        p.require(self.phase == UPLOAD, 'Diagnosis route not independently pinned')
        base = re.escape(p.gh.GitHubContentsClient._route(self.p['repo'], ''))
        branch = urllib.parse.quote(self.p['branch'], safe='')
        allowed = (route == p.gh.GitHubContentsClient._route(self.p['repo'], '/git/ref/heads/'+branch)
            or re.fullmatch(base+r'/contents/delivery/stream\.json\?ref=[0-9a-f]{40}', route)
            or re.fullmatch(base+r'/git/commits/[0-9a-f]{40}', route)
            or re.fullmatch(base+r'/git/trees/[0-9a-f]{40}\?recursive=1', route))
        p.require(allowed, 'Upload readback route outside exact repository contract')


def validate_history(plan, rows, a):
    """Validate old 17 lines without fabricating the absent old response body."""
    p.require(len(rows) >= 17, 'Missing complete original rules403 frontier')
    prior = a['reader401_amendment']; grant = a['reader401_grant']
    old.validate_chain(plan, rows[:5], (p.digest(plan), 'bootstrap.jsonl', rows[4]['hash'], rows[4]['utc']), prior)
    expected = ['phase_start', 'authorization', 'reader401_amendment']+['request', 'response']*4+['phase_halt']
    p.require([r['event'] for r in rows[5:17]] == expected
              and all(r['phase'] == old.PHASE and r['run'] is None for r in rows[5:17]), 'Not the precise original 403 path')
    p.require(all(r['repository_id'] == plan['repository_id'] and r['branch'] == plan['branch']
                  and r['path'] == plan['path'] and r['plan_sha256'] == p.digest(plan) for r in rows), 'Foreign history')
    validate_grant(plan, grant, old.PHASE, p.digest(prior))
    p.require(rows[5]['journal'] == old.PHASE+'.jsonl' and rows[5]['predecessor'] == rows[4]['hash']
              and rows[6]['grant_sha256'] == p.digest(grant) and rows[6]['review_sha256'] == p.digest(prior)
              and rows[6]['grant_expires_utc'] == grant['expires_utc']
              and rows[6]['expiry_policy'] == plan['expiry_policy'], 'Original reader grant differs')
    amendment = rows[7]
    p.require(amendment['amendment_sha256'] == p.digest(prior) and amendment['execution_head'] == BASE_HEAD
              and amendment['execution_tree'] == BASE_TREE and amendment['original_code_head'] == plan['code_head']
              and amendment['original_pid'] == rows[0]['pid'] and amendment['predecessor_frontier'] == rows[4]['hash']
              and amendment['process_end_observation'] in ('currently-absent', 'currently-signaled')
              and amendment['result'] == 'reviewed-single-continuation', 'Original amendment differs')
    for i in range(4):
        request, response = rows[8+2*i:10+2*i]
        expected_count = {'GET': i+2, 'PUT': 0, 'GIT_PUSH': 0}
        p.require(request['method'] == 'GET' and request['bytes'] == 0 and request['budget_phase'] == 'bootstrap'
                  and all(request.get(k) is None for k in ('old_blob', 'write_id', 'revision', 'parent_digest'))
                  and request['counts'] == response['counts'] == expected_count
                  and response['result'] == ('http-200', 'http-200', 'http-404', 'http-403')[i],
                  'Wrong original request/outcome; no generic HALT exception')
    p.require(rows[16]['result'] == 'incomplete-no-retry-no-release'
              and rows[16]['counts'] == {'GET': 5, 'PUT': 0, 'GIT_PUSH': 0}
              and all(old.parse_utc(r['utc']) < min(old.parse_utc(grant['expires_utc']), old.parse_utc(prior['expires_utc']))
                      for r in rows[5:17]), 'Expired or different historical outcome')


def positive_observations(plan):
    names = ('private-identity', 'actions-disabled', 'pages-not-found', 'empty-effective-rules',
             'empty-rulesets', 'empty-repository', 'protection-not-found-on-absent-branch')
    return [{'route': route, 'status': status, 'check': name} for route, status, name in
            zip(routes(plan), (200, 200, 404, 200, 200, 200, 404), names)]


def validate_diagnosis(plan, rows, a):
    d = a['diagnosis']; prior = d['amendment']; grant = d['grant']; phase = prior['phase']
    offset = 21 if phase == RESUME else 17
    if phase == RESUME: validate_interrupted(plan, rows[:21], prior)
    tail = rows[offset:]
    expected = ['phase_start', 'authorization', 'rules403_amendment']+['request', 'response']*7+['diagnosis', 'phase_end']
    p.require(len(rows) == offset+19 and [r['event'] for r in tail] == expected
              and all(r['phase'] == phase and r['run'] is None for r in tail), 'Complete first positive diagnosis required')
    p.require(tail[0]['journal'] == phase+'.jsonl' and tail[0]['predecessor'] == rows[offset-1]['hash']
              and tail[1]['grant_sha256'] == p.digest(grant) and tail[1]['review_sha256'] == p.digest(prior)
              and tail[1]['grant_expires_utc'] == grant['expires_utc']
              and tail[1]['expiry_policy'] == plan['expiry_policy']
              and tail[2]['amendment_sha256'] == p.digest(prior)
              and tail[2]['execution_code'] == a['execution_code']
              and tail[2]['predecessor_frontier'] == rows[offset-1]['hash']
              and tail[2]['process_end_observation'] in ('currently-absent', 'currently-signaled'),
              'Diagnosis code/grant/frontier differs')
    p.require(prior['predecessor']['frontier_hash'] == rows[offset-1]['hash']
              and prior['predecessor']['frontier_rows'] == offset and prior['predecessor']['counts'] == rows[offset-1]['counts'],
              'Diagnosis not attached to original latest frontier')
    for i, observation in enumerate(positive_observations(plan)):
        req, resp = tail[3+2*i:5+2*i]
        p.require(req['method'] == 'GET' and req['route'] == resp['route'] == observation['route']
                  and req['bytes'] == 0
                  and all(req.get(k) is None for k in ('old_blob', 'write_id', 'revision', 'parent_digest'))
                  and resp['result'] == 'http-'+str(observation['status']) and req['budget_phase'] == 'bootstrap'
                  and req['counts'] == resp['counts'] == {'GET': i+6, 'PUT': 0, 'GIT_PUSH': 0}, 'Diagnosis request/outcome differs')
        if observation['status'] == 404:
            p.require(resp['diagnostic']['category'] == 'not-found'
                      and resp['diagnostic']['feature_absence_proved'] is False, 'Ambiguous 404 cannot authorize upload')
    p.require(tail[-2]['observations'] == positive_observations(plan) and tail[-2]['upload_eligible'] is True
              and tail[-2]['result'] == 'positive-normal-rules-path'
              and tail[-1]['result'] == 'confirmed' and tail[-1]['scope'] == 'read-only-diagnosis'
              and rows[-1]['counts'] == {'GET': 12, 'PUT': 0, 'GIT_PUSH': 0}
              and all(old.parse_utc(r['utc']) < min(old.parse_utc(grant['expires_utc']), old.parse_utc(prior['expires_utc']))
                      for r in tail), 'No positive complete timely diagnosis; upload blocked')


def validate_interrupted(plan, rows, a):
    """Only the exact authorized pre-request script failure; never any HALT."""
    d = a['interrupted_diagnosis']; prior = d['amendment']; grant = d['grant']; tail = rows[17:]
    p.require(len(rows) == 21 and [x['event'] for x in tail] ==
              ['phase_start', 'authorization', 'rules403_amendment', 'phase_halt']
              and all(x['phase'] == DIAG and x['run'] is None
                      and x['counts'] == {'GET': 5, 'PUT': 0, 'GIT_PUSH': 0} for x in tail),
              'Only exact21 pre-request history can continue')
    p.require(tail[0]['journal'] == DIAG+'.jsonl' and tail[0]['predecessor'] == rows[16]['hash']
              and tail[1]['grant_sha256'] == p.digest(grant) and tail[1]['review_sha256'] == p.digest(prior)
              and tail[1]['grant_expires_utc'] == grant['expires_utc'] and tail[1]['expiry_policy'] == plan['expiry_policy']
              and tail[2]['amendment_sha256'] == p.digest(prior) and tail[2]['execution_code'] == prior['execution_code']
              and tail[2]['predecessor_frontier'] == rows[16]['hash']
              and tail[2]['process_end_observation'] in ('currently-absent', 'currently-signaled')
              and tail[2]['result'] == 'separately-reviewed-'+DIAG
              and tail[3]['result'] == 'incomplete-no-retry-no-release'
              and tail[3]['category'] == 'incomplete-or-expired', 'Not the reviewed script pre-request failure')
    pred = prior['predecessor']
    p.require(pred['frontier_rows'] == 17 and pred['frontier_hash'] == rows[16]['hash']
              and pred['highwater'] == rows[16]['utc'] and pred['counts'] == rows[16]['counts']
              and prior['review']['original_pid'] == rows[5]['pid']
              and all(old.parse_utc(x['utc']) < min(old.parse_utc(grant['expires_utc']),
                  old.parse_utc(prior['expires_utc']), old.parse_utc(plan['expires_utc'])) for x in tail),
              'Interrupted diagnosis frontier or original validity differs')


def session_files(rows):
    starts = [r for r in rows if r['event'] == 'phase_start']
    return {'probe-session.sqlite3', 'probe-session.lock'} | {r['journal'] for r in starts} | {
            'attempt-'+r['phase']+'.json' for r in starts}


def validate_locked(ledger, rows, state, a):
    phase = ledger.phase; pred = a['predecessor']; root = ledger.path.parent
    p.require(phase == a['phase'] and ledger.path.name == phase+'.jsonl', 'Fixed recovery journal required')
    validate_history(ledger.p, rows, a)
    if phase == DIAG: p.require(len(rows) == 17, 'Diagnosis only after the original 17-line frontier')
    elif phase == RESUME: validate_interrupted(ledger.p, rows, a)
    else: validate_diagnosis(ledger.p, rows, a)
    p.require(pred['frontier_rows'] == len(rows) and pred['frontier_hash'] == rows[-1]['hash']
              and pred['counts'] == rows[-1]['counts'] and pred['highwater'] == rows[-1]['utc']
              and tuple(state) == (p.digest(ledger.p), pred['journal'], pred['frontier_hash'], pred['highwater'])
              and set(pred['files_sha256']) == session_files(rows), 'Not the complete latest session frontier')
    for name, expected in pred['files_sha256'].items():
        if name == 'probe-session.lock':
            ledger.lock_handle.seek(0); actual = hashlib.sha256(ledger.lock_handle.read()).hexdigest(); ledger.lock_handle.seek(0)
        else: actual = old.sha(root/name)
        p.require(actual == expected, 'Original session file changed')
    starts = [i for i, r in enumerate(rows) if r['event'] == 'phase_start']
    for j, index in enumerate(starts):
        stop = starts[j+1] if j+1 < len(starts) else len(rows)
        p.require((root/rows[index]['journal']).read_bytes() == ''.join(p.canonical(r)+'\n' for r in rows[:stop]).encode(),
                  'Historical journal prefix changed')
    review = a['review']; latest = rows[starts[-1]]
    p.require(review['end_basis'] == END_BASIS and review['original_pid'] == latest['pid']
              and all(review[k] is True for k in ('terminal_code_path_checked', 'human_terminal_end_report',
                          'all_workers_ended', 'triggers_paused', 'human_review'))
              and isinstance(review['reviewer'], str) and review['reviewer']
              and re.fullmatch('[0-9a-f]{64}', review['evidence_sha256'] or '')
              and old.parse_utc(rows[-1]['utc']) <= old.parse_utc(review['observed_utc']) <= p.datetime.now(p.timezone.utc),
              'Positive independently reviewed exact process end required')
    ledger.rules403_end_observation = old.process_ended(review['original_pid'])
    old.root_matches(a); old.verify_root(ledger.p, a['root']['directory'])
    p.require(not any((Path(a['root']['directory'])/name).exists() for name in
                      ('synthetic-askpass.py', 'synthetic-askpass.cmd')), 'Previous push preparation forbidden')


class RulesBoundary(p.Boundary):
    def request(self, method, route, payload=None):
        try: return super().request(method, route, payload)
        except p.HTTPStatus as exc:
            # Existing preflight accepts a Pages/protection 404; here it must
            # also have a valid bounded Not Found envelope. No 403 exception.
            if exc.status == 404 and (exc.diagnostic or {}).get('category') != 'not-found':
                raise Halt('unverified-404') from None
            raise

    def preflight(self, empty=False):
        super().preflight(empty)
        if empty:
            try: self.request('GET', routes(self.p)[6])
            except p.HTTPStatus as exc:
                if exc.status != 404: raise
            else: raise Halt('classic-protection-present-or-unexpected')


def diagnose(client):
    ledger = client.boundary.ledger; plan = client.boundary.p; observations = []; blocked = []
    for i, route in enumerate(routes(plan)):
        status = 200
        try: value = client.boundary.request('GET', route)
        except p.HTTPStatus as exc:
            category = (exc.diagnostic or {}).get('category', 'unknown-response')
            if exc.status == 404 and i in (2, 6) and category == 'not-found': value = None; status = 404
            elif exc.status == 403 and i in (3, 4, 6) and category == 'feature-unavailable-hint':
                observations.append({'route': route, 'status': 403, 'check': category}); blocked.append(category); continue
            else: raise Halt(category) from None
        if i == 0:
            ok = isinstance(value, dict) and value.get('id') == plan['repository_id'] and value.get('full_name') == plan['repo']
            ok = ok and value.get('private') is True and value.get('has_pages') is False and value.get('archived') is False
            ok = ok and value.get('permissions', {}).get('admin') is True
        elif i == 1: ok = isinstance(value, dict) and value.get('enabled') is False
        elif i in (2, 6): ok = status == 404
        else: ok = value == []
        if not ok: raise Halt('settings-identity-or-rules-not-empty')
        observations.append(positive_observations(plan)[i])
    ready = not blocked and observations == positive_observations(plan)
    ledger.emit('diagnosis', result='positive-normal-rules-path' if ready else 'blocked-feature-unavailable-hint',
                observations=observations, upload_eligible=ready, feature_absence_proved=False)
    ledger.emit('phase_end', result='confirmed', scope='read-only-diagnosis', upload_eligible=ready)
    return ready


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template'); parser.add_argument('--phase', choices=p.RULES_PHASES, default=DIAG)
    parser.add_argument('--real', action='store_true'); parser.add_argument('--plan'); parser.add_argument('--amendment')
    parser.add_argument('--grant'); parser.add_argument('--approved-amendment-sha256')
    args = parser.parse_args()
    if args.template:
        p.require(not args.real, 'Template offline only')
        with Path(args.template).open('x', encoding='utf-8') as f: f.write(json.dumps(template(args.phase), indent=2)+'\n')
        return 0
    p.require(args.real and all((args.plan, args.amendment, args.grant, args.approved_amendment_sha256)),
              'Default offline; exact independently reviewed amendment/grant required')
    plan, a, grant = [json.loads(Path(name).read_text(encoding='utf-8-sig')) for name in (args.plan, args.amendment, args.grant)]
    p.require(a['phase'] == args.phase, 'Explicit phase differs from amendment')
    guard = authorize(plan, a, grant, args.approved_amendment_sha256)
    root = Path(plan['journal_directory']); result_path = root/(args.phase+'.jsonl')
    ledger = p.Ledger(plan, result_path, args.phase, root/a['predecessor']['journal'], rules403_amendment=a)
    try:
        guard.check(ledger)
        reader = p.read_token('Reader')  # Diagnosis never asks for Writer.
        client = p.Client(RulesBoundary(plan, ledger, reader, '', guard=guard))
        ledger.emit('rules403_amendment', amendment_sha256=p.digest(a), execution_code=a['execution_code'],
                    predecessor_frontier=a['predecessor']['frontier_hash'],
                    process_end_observation=ledger.rules403_end_observation,
                    result='separately-reviewed-'+args.phase)
        if args.phase in (DIAG, RESUME):
            ready = diagnose(client)
            print(('Diagnose abgeschlossen; eigener Uploadreview und Grant erforderlich.' if ready else
                   'HALT: feature-unavailable-hint; keine belegte Regelnabwesenheit, Upload gesperrt.')+' Ergebnis: '+str(result_path))
            return 0 if ready else 2
        p.bootstrap(client, a['root']['directory'], reuse_reviewed_root=True, writer_prompt=lambda: p.read_token('Writer'))
        client.boundary.preflight(empty=False)  # fresh effective/list/classic checks after creation
        ledger.emit('phase_end', result='confirmed', scope='blocked-root-only-no-activation')
        print('Blocked-Root bestaetigt; keine Aktivierung. Ergebnis: '+str(result_path))
        return 0
    except BaseException as exc:
        category = exc.category if isinstance(exc, Halt) else (exc.diagnostic or {}).get('category', 'http-'+str(exc.status)) if isinstance(exc, p.HTTPStatus) else 'incomplete-or-expired'
        if not ledger.poisoned: ledger.emit('phase_halt', result='incomplete-no-retry-no-release', category=category)
        print('HALT: '+category+'. Nicht erneut starten. Ergebnis: '+str(result_path))
        raise
    finally: ledger.close()
