"""Reviewed runtime entry to the existing fail-closed production runner.

The delivered runtime is disabled. This entry never provisions a store or request
journal, creates credentials, registers a scheduler or selects a strategy.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'engine'), str(ROOT/'tools')]
import production_confirmation as confirmation
import produktion_runner


def run_runtime(runtime_path, kind, data_dir, **fixtures):
    runtime = json.loads(Path(runtime_path).read_text(encoding='utf-8'))
    if runtime.get('enabled') is not True:
        raise ValueError('Production candidate runtime is disabled')
    if (runtime.get('schema') != 'btc-production-candidate-runtime-v1'
            or runtime.get('store_adapter') != 'github'
            or not re.fullmatch('[0-9a-f]{64}', runtime.get('activation_review_sha256') or '')
            or kind not in ('signal', 'watch')):
        raise ValueError('Reviewed candidate activation/operation binding missing')
    expected = {
        'BTC_DELIVERY_ADAPTER': runtime['store_adapter'],
        'BTC_DELIVERY_GITHUB_REPO': runtime.get('private_store_repository'),
        'BTC_DELIVERY_GITHUB_BRANCH': runtime.get('store_branch'),
        'BTC_DELIVERY_STORE_ID': runtime.get('store_id'),
        'BTC_DELIVERY_CODE_SHA': runtime.get('code_sha'),
        'BTC_DELIVERY_BOT_IDENTITY': runtime.get('bot_identity'),
        'BTC_DELIVERY_RUN_REPOSITORY': runtime.get('code_repository'),
        'BTC_DELIVERY_WORKFLOW': runtime.get('workflow'),
        'BTC_DELIVERY_CONFIRMATION_POLICY': runtime.get('confirmation_policy'),
        'BTC_DELIVERY_CONFIRMATION_CONFIG': runtime.get('confirmation_config'),
        'BTC_DELIVERY_REQUEST_JOURNAL': runtime.get('request_journal')}
    if any(not v or os.environ.get(k) != v for k,v in expected.items()):
        raise ValueError('Runtime differs from explicit production environment')
    policy = confirmation.validate_policy(json.loads(Path(expected['BTC_DELIVERY_CONFIRMATION_CONFIG']).read_text(encoding='utf-8')))
    if {k:v for k,v in policy.items() if k!='deadline_utc_ms'} != runtime.get('confirmation_budgets'):
        raise ValueError('Runtime request budgets differ from pinned policy')
    from production_contract import effective_config, digest
    config = json.loads(Path(data_dir,'config.json').read_text(encoding='utf-8'))
    if digest(effective_config(config)) != runtime.get('config_sha256'):
        raise ValueError('Runtime effective strategy configuration pin mismatch')
    return produktion_runner.run_checked(kind, Path(data_dir), **fixtures)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--runtime',required=True)
    p.add_argument('--kind',choices=('signal','watch'),required=True)
    p.add_argument('--data-dir',required=True)
    a=p.parse_args()
    try: run_runtime(a.runtime,a.kind,a.data_dir)
    except Exception:
        print('Production candidate refused or halted; operator review required.',file=sys.stderr)
        sys.exit(20)
