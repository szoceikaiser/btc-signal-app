"""Bounded untrusted GitHub error hints, never an authorization or rules bypass."""
import json
import re

MAX_ERROR_BYTES = 4096
FEATURE_MESSAGES = {
    'Upgrade to GitHub Pro or make this repository public to enable this feature.',
    'Upgrade to GitHub Team or make this repository public to enable this feature.',
}
RIGHTS_MESSAGES = {'Resource not accessible by personal access token',
                   'Resource not accessible by integration', 'Must have admin rights to Repository.'}
DOCS = {'https://docs.github.com/rest', 'https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting',
        'https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api',
        'https://docs.github.com/rest/repos/rules#get-rules-for-a-branch',
        'https://docs.github.com/rest/repos/rules#get-all-repository-rulesets',
        'https://docs.github.com/rest/branches/branch-protection#get-branch-protection',
        'https://docs.github.com/rest/pages/pages#get-a-apiname-pages-site',
        'https://docs.github.com/rest/pages/pages#get-a-github-pages-site'}


def unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj: raise ValueError('duplicate')
        obj[key] = value
    return obj


def classify(error):
    """Emit only allowlisted enums/numbers; no message, URL, header or raw body.

    Feature wording is merely a conservative lexical hint, NOT a documented
    attestation that effective rules/protection cannot exist for this repo.
    """
    invalid = {'category': 'invalid-error-response', 'feature_absence_proved': False}
    try:
        raw = error.read(MAX_ERROR_BYTES+1)
        if len(raw) > MAX_ERROR_BYTES: return invalid
        obj = json.loads(raw.decode('utf-8'), object_pairs_hook=unique)
        if not isinstance(obj, dict) or not set(obj) <= {'message', 'documentation_url', 'status'}: return invalid
        message = obj.get('message')
        if not isinstance(message, str) or not 1 <= len(message) <= 512 or any(ord(c) < 32 or ord(c) > 126 for c in message): return invalid
        if 'status' in obj and obj['status'] != str(error.code): return invalid
        if obj.get('documentation_url') not in DOCS: return invalid
        hints = {}
        for name in ('x-ratelimit-remaining', 'x-ratelimit-limit', 'x-ratelimit-reset', 'retry-after',
                     'x-accepted-github-permissions', 'content-type'):
            headers = error.headers
            values = headers.get_all(name) if hasattr(headers, 'get_all') else [v for k, v in headers.items() if k.lower() == name]
            if not values: continue
            if len(values) != 1 or not isinstance(values[0], str) or len(values[0]) > 256: return invalid
            value = values[0]
            if name == 'content-type':
                if value.lower() not in ('application/json', 'application/json; charset=utf-8'): return invalid
            elif name == 'x-accepted-github-permissions':
                alternatives = [x.strip() for x in value.split(';')]
                parsed = []
                for alternative in alternatives:
                    permissions = [x.strip() for x in alternative.split(',')]
                    if not 1 <= len(permissions) <= 4 or len(set(permissions)) != len(permissions): return invalid
                    if not all(re.fullmatch(r'(metadata|contents|administration|pages)=(read|write)', x) for x in permissions): return invalid
                    parsed.append(sorted(permissions))
                if not 1 <= len(parsed) <= 4: return invalid
                hints['accepted_permission_sets'] = parsed  # requirement hint, never token attestation
            else:
                if not re.fullmatch(r'0|[1-9][0-9]{0,9}', value): return invalid
                number = int(value)
                if name == 'retry-after' and number > 86400: return invalid
                hints[name.replace('-', '_')] = number
        if hints.get('x_ratelimit_remaining', 0) > hints.get('x_ratelimit_limit', 10**10): return invalid
        rate = error.code == 429 or hints.get('x_ratelimit_remaining') == 0 or 'retry_after' in hints
        rate = rate or message.startswith('API rate limit exceeded for ') or message in {
            'You have exceeded a secondary rate limit. Please wait a few minutes before you try again.'}
        rights = message in RIGHTS_MESSAGES
        feature = message in FEATURE_MESSAGES
        if sum((bool(rate), rights, feature)) > 1: category = 'ambiguous-error-response'
        elif rate: category = 'rate-limit-hint'
        elif error.code == 403 and rights: category = 'permission-denied-hint'
        elif error.code == 403 and feature: category = 'feature-unavailable-hint'
        elif error.code == 401 and message == 'Bad credentials': category = 'authentication-denied'
        elif error.code == 404 and message == 'Not Found': category = 'not-found'
        else: category = 'unknown-'+str(error.code)
        return {'category': category, 'feature_absence_proved': False, **hints}
    except Exception:
        return invalid
    finally:
        try: error.close()
        except Exception: pass  # closing an untrusted body must not expose its exception
