"""Classify two authenticated reads of one reviewed Store ruleset."""

import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from continuous_operations import no_redirect_transport
from github_delivery import GitHubContentsClient, StoreConflict, StoreHTTPFailure, StoreUnavailable


REPO = 'szoceikaiser/btc-delivery-store'
RULE_ID = 25342277
ROUTE = GitHubContentsClient._route(REPO, f'/rulesets/{RULE_ID}')
ROLES = (
    ('job', 'GITHUB_TOKEN'),
    ('store', 'BTC_DELIVERY_GITHUB_TOKEN'),
)
HTTP_CLASSES = {
    'GitHub store HTTP 401': 'authentication_failed',
    'GitHub store HTTP 403': 'forbidden_or_limited',
    'GitHub store HTTP 404': 'not_found_or_hidden',
    'GitHub store HTTP 429': 'rate_limited',
}


class RuleReader(GitHubContentsClient):
    def __init__(self, token, opener):
        super().__init__(token, timeout=3)
        self.open_request = opener
        self.used = False

    def _request(self, method, route, payload=None):
        if self.used or method != 'GET' or route != ROUTE or payload is not None:
            raise StoreUnavailable('Ruleset probe request refused')
        self.used = True
        return super()._request(method, route)


def classify(token):
    if not token:
        return 'credential_missing'
    try:
        rule = RuleReader(token, no_redirect_transport())._request('GET', ROUTE)
    except StoreHTTPFailure as exc:
        return HTTP_CLASSES.get(str(exc), 'http_error')
    except StoreConflict:
        return 'http_error'
    except ValueError:
        return 'invalid_response'
    except Exception:
        return 'unconfirmed'

    if not isinstance(rule, dict):
        return 'invalid_response'
    if (type(rule.get('id')) is not int or rule['id'] != RULE_ID
            or rule.get('source') != REPO or rule.get('source_type') != 'Repository'
            or rule.get('target') != 'branch' or rule.get('enforcement') != 'active'):
        return 'unexpected_ruleset'
    if 'current_user_can_bypass' not in rule:
        return 'bypass_not_reported'
    bypass = rule['current_user_can_bypass']
    if bypass == 'never':
        return 'bypass_never'
    if bypass == 'always':
        return 'bypass_always'
    if bypass == 'pull_requests_only':
        return 'bypass_pull_requests_only'
    return 'bypass_unrecognized'


def main():
    result = {role: classify(os.environ.get(variable)) for role, variable in ROLES}
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
