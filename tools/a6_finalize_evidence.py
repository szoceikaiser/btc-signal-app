"""Adjudicate A6's reached failures and map all 316 audit mutations."""
from collections import Counter
import json
from pathlib import Path

from a6_inventory import ROOT, cases as static_cases
from a6_mutations import dynamic_cases
from a6_contract_cases import cases as new_cases

HERE = ROOT / 'docs/audit-nacharbeit-2026-10'
raw = json.loads((HERE / 'A6-mutations.json').read_text(encoding='utf-8'))
by_id = {r['id']: r for r in raw}
assert len(by_id) == len(raw), 'Duplicate case result'
old = static_cases + dynamic_cases()
assert len(old) == 316 and {c['id'] for c in old} <= set(by_id)
for row in raw:
    if row['status'] == 'caught_assertion':
        assert row['matches'] >= 1 and row['baseline']['exit_code'] == 0
        # The isolated driver reserves exit code 1 for AssertionError only.
        assert row['mutant']['exit_code'] == 1

# These 13 damaged branches ran and raised exactly the expected failure. The
# unmutated control for each returned zero. No import, syntax or timeout failure
# is accepted here. The original full traces remain in A6-mutations.json.
REACHED_EXCEPTIONS = {
    'sabotage_e381:005': 'IndexError',
    'sabotage_e381:006': 'IndexError',
    'sabotage_e381:015': 'TypeError',
    'sabotage_e381:017': 'KeyError',
    'sabotage_e39:018': 'IndexError',
    'sabotage_e40:013': 'IndexError',
    'sabotage_e40:017': 'ValueError',
    'sabotage_e40:020': 'RuntimeError',
    'sabotage_e40:021': 'RuntimeError',
    'sabotage_e40:027': 'ZeroDivisionError',
    'sabotage_e441:005': 'JSONDecodeError',
    'sabotage_e442:002': 'StopIteration',
    'sabotage_e443:035': 'KeyError',
    'current:sabotage_e443:033': 'StopIteration',
}
for key, exc in REACHED_EXCEPTIONS.items():
    row = by_id[key]
    assert row['status'] == 'survived_or_error' and row['matches'] >= 1
    assert row['baseline']['exit_code'] == 0 and row['mutant']['exit_code'] == 2
    assert exc in row['mutant']['tail'] and 'Traceback' in row['mutant']['tail']
    assert 'SyntaxError' not in row['mutant']['tail'] and 'ImportError' not in row['mutant']['tail']

SEVEN = {
    'sabotage_e41:012': 'refresh:E41-buy-wait',
    'sabotage_e41:043': 'refresh:E41-message-missing',
    'sabotage_e41:044': 'contract:T01-E41-order',
    'sabotage_e433:016': 'refresh:E433-cvd-key',
    'sabotage_e434:020': 'refresh:E434-oi-default',
    'sabotage_e434:024': 'refresh:E434-oi-key',
    'sabotage_e443:032': 'refresh:E443-legacy-inventory',
}
assert len(SEVEN) == 7

def line_of(path, snippet):
    if not path.exists():
        return None
    content = path.read_text(encoding='utf-8')
    return content[:content.find(snippet)].count('\n') + 1 if snippet in content else None


mapping = []
for case in old:
    result = by_id[case['id']]
    status = result['status']
    row = dict(id=case['id'], name=case['name'], original_script=case['script'],
               source_file=case['file'], original_template=case['old'],
               current_matches=result['matches'], current_result=status,
               test=result.get('test'),
               current_source_line=line_of(ROOT / 'engine' / case['file'], case['old']))
    if status == 'caught_assertion':
        row['adjudication'] = 'current_mutation_reached_assertion'
    elif case['id'] in REACHED_EXCEPTIONS:
        row['adjudication'] = 'current_mutation_reached_expected_failure'
        row['failure_type'] = REACHED_EXCEPTIONS[case['id']]
    else:
        replacement = SEVEN.get(case['id'], 'current:' + case['id'])
        if replacement in by_id:
            evidence = by_id[replacement]
            assert evidence['status'] == 'caught_assertion' or replacement in REACHED_EXCEPTIONS
            row['adjudication'] = 'text_template_replaced_current_equivalent_reached'
            row['current_equivalent'] = replacement
            row['equivalent_test'] = evidence.get('test')
        elif case['script'] in ('sabotage_e444.py', 'sabotage_e445.py'):
            row['adjudication'] = 'historical_only_absent_at_A5_base'
            row['reason'] = 'Original E44.4/E44.5 program remains at original audit commit; its target/test is absent in the A5 checkout.'
        elif case['id'] in ('sabotage_e433:019', 'sabotage_e433:021'):
            row['adjudication'] = 'retired_by_A2_default_contract'
            row['reason'] = 'A2 deliberately made usd the default; switching from alt to usd is no longer a defect mutation.'
            row['replacement_contract_test'] = 'test_a2_flow::test_a2_f06_constant_offsets_do_not_change_default_pattern'
        elif case['id'] in ('sabotage_e434:014', 'sabotage_e434:016', 'sabotage_e434:017'):
            row['adjudication'] = 'retired_by_A2_asof_contract'
            row['reason'] = 'A2 replaced separate old backfill paths with a shared as-of series and provenance.'
            row['replacement_contract_test'] = 'test_a2_flow::test_a2_f07_prefix_first_oi_and_stale_age_live_backtest'
        else:
            row['adjudication'] = 'unmapped_not_passed'
    mapping.append(row)

counts = Counter(x['adjudication'] for x in mapping)
summary = dict(original_case_count=len(mapping), original_adjudication=dict(counts),
               current_new_cases=len(new_cases()),
               new_cases=Counter(by_id[c['id']]['status'] for c in new_cases()),
               seven_original_obsolete_templates=dict(SEVEN),
               valid_runtime_reached=dict(REACHED_EXCEPTIONS),
               unmapped=[x['id'] for x in mapping if x['adjudication']=='unmapped_not_passed'])
(HERE / 'A6-mapping.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
(HERE / 'A6-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
