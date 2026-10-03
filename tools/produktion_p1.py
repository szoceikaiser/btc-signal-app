"""Read-only integration proof; --write writes only the new P1 evidence file."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/produktionsuebernahme-2026-10'
MAIN = 'ca8ad2fb730174ca1887791d425ae01aa6a715e6'
AUDIT = '881e36a6271a6e49400d47da59342755e33cf402'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def original(path, ref=MAIN):
    return json.loads(git('show', f'{ref}:{path}'))


def inspect():
    # Git applies the repository's attributes here, avoiding CRLF false alarms.
    assert not git('diff', MAIN, '--', 'site/data', ':!site/data/config.json').strip()
    assert not git('diff', AUDIT, '--', 'engine', 'site/index.html',
                   'site/chart_signals.js', 'site/data/config.json').strip()
    before = original('site/data/config.json')
    after = json.loads((ROOT/'site/data/config.json').read_text(encoding='utf-8'))
    changes = {k: {'before': before.get(k), 'after': after.get(k)}
               for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
    assert set(changes) == {'muster_cvd', '_hinweis_muster_cvd'}
    assert changes['muster_cvd'] == {'before': 'alt', 'after': 'usd'}
    assert after['ausbruch_ruecktest'] is False and after['bias_short'] is False
    sys.path.insert(0, str(ROOT/'engine'))
    import position_state
    import durable_delivery
    state = original('site/data/state.json')
    pos = position_state.pos_from_state(state)
    converted = position_state.pos_to_state(pos)
    stable = ['pos_state', 'direction', 'last_signal_ts', 'entry_ref', 'entry_pct',
              'bestand_pct', 'tp_rungs', 'dip_buys', 'buy_rungs', 'last_stop_ts',
              'stop_wartet', 'stop_wartet_inv']
    assert all(converted[k] == state[k] for k in stable)
    assert converted['inventory_source'] == 'signal_reference' and not converted['lots']
    assert '_delivery' not in state
    # The old state must NOT be silently accepted for a durable live stream.
    refused = False
    try:
        durable_delivery.validate({'version': 1, 'engine': state, 'watch': {}, 'commands': {}})
    except ValueError as exc:
        refused = 'Migration requires' in str(exc)
    assert refused
    preserved = {}
    paths = git('ls-tree', '-r', '--name-only', MAIN, 'site/data').decode().splitlines()
    for path in paths:
        if path == 'site/data/config.json':
            continue
        blob = git('show', f'{MAIN}:{path}')
        preserved[path] = hashlib.sha256(blob).hexdigest()
    workflows = ROOT/'.github/workflows'
    for name, job in [('signal.yml', 'run'), ('watch.yml', 'wache'), ('lage.yml', 'lage'),
                      ('backtest.yml', 'backtest'), ('archiv.yml', 'archiv')]:
        text = (workflows/name).read_text(encoding='utf-8')
        assert f"  {job}:\n    if: github.ref == 'refs/heads/main'\n" in text
    pages = (workflows/'pages.yml').read_text(encoding='utf-8')
    assert "github.event.workflow_run.head_branch == 'main'" in pages
    assert "github.ref == 'refs/heads/main'" in pages
    offline = (workflows/'produktion-offline.yml').read_text(encoding='utf-8')
    assert "if: github.ref == 'refs/heads/codex/produktion-audit-uebernahme'" in offline
    assert 'branches: [codex/produktion-audit-uebernahme]' in offline
    assert 'secrets.' not in offline and 'contents: read' in offline
    register = original('docs/audit-nacharbeit-2026-10/REGISTER.json', AUDIT)
    return {
        'schema': 'production-p1-integration-v1', 'main': MAIN, 'audit': AUDIT,
        'production_activated': False, 'runtime_data_preserved_git_blob_sha256': preserved,
        'audit_engine_chart_and_config_preserved': True, 'config_changes': changes,
        'old_state': {'updated_at': state['updated_at'], 'pos_state': state['pos_state'],
                      'last_signal_ts': state['last_signal_ts'], 'preserved_position_fields': stable,
                      'migration_notes': converted['migration_notes'],
                      'has_delivery_journal': False, 'old_state_direct_provision_refused': refused,
                      'watch_file_at_main': 'site/data/watch.json' in paths},
        'audit_register_sha256': hashlib.sha256(git('show', f'{AUDIT}:docs/audit-nacharbeit-2026-10/REGISTER.json')).hexdigest(),
        'gates': {'production_jobs_main_only': True, 'pages_upstream_main_only': True,
                  'safe_offline_branch': True},
        'open': ['host_and_store', 'migration_cutover_and_unknown_delivery',
                 'new_main_snapshot_before_activation', 'live_operator_approval'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = inspect()
    path = DOC/'P1-INTEGRATION.json'
    if args.write:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8', newline='\n')
    else:
        assert result == json.loads(path.read_text(encoding='utf-8'))
    print('P1 PASS: main runtime preserved; audited code unchanged; old migration refused; workflows isolated.')
