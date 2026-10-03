"""A8 structural acceptance; frozen files only, no network or strategy search."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT/'docs/audit-nacharbeit-2026-10'
sys.path.insert(0,str(ROOT/'engine'))


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    design = read(DOC/'A7-analysemanifest-v1.json')
    index = read(DOC/'A7-resultindex-v1.json')
    ids = {r['id'] for r in design['rows']}
    assert len(ids)==86 and set(index['rows'])==ids
    assert index['identical_alias']=={'S004':'V000'}
    assert index['rows']['V035']['returns'] is None
    assert not index['selection_adjusted'] and not index['historical_api_as_of_proven']
    assert not index['legacy_and_causal_ranked_together']
    for row in design['rows']:
        canonical = json.dumps(row['params'],sort_keys=True,separators=(',',':'),ensure_ascii=False)
        assert hashlib.sha256(canonical.encode()).hexdigest()==row['params_sha256_canonical']
    references = {}
    def visit(x):
        if isinstance(x,dict):
            if 'file' in x and 'sha256' in x:
                assert references.setdefault(x['file'],x['sha256'])==x['sha256']
            for v in x.values(): visit(v)
        elif isinstance(x,list):
            for v in x: visit(v)
    visit(index)
    for path,digest in references.items():
        assert sha(ROOT/path)==digest, path
    run_refs = {p for p in references if '/A7-runs/' in p}
    assert len(run_refs)==1250
    actual_runs = {p.relative_to(ROOT).as_posix() for p in (DOC/'A7-runs').glob('*.json')}
    assert run_refs==actual_runs
    modes = Counter()
    for p in sorted(run_refs):
        r = read(ROOT/p)
        mode=r.get('mode','grid')  # First 15 R0/S0 grid files precede this field.
        if 'mode' not in r:
            assert Path(p).stem==f"{r['package']}-{r['scenario']}-{r['id']}"
        modes[mode]+=1
        assert r['id']!='V035' and r['independent_account_verified']
        assert not r['historical_api_as_of_proven']
        assert r['flow_sha256']==index['flow_sha256']
        assert r['design_sha256']==sha(DOC/'A7-analysemanifest-v1.json')
        assert r['cutoff_ms']<=1790683200000
        assert r['detail']['cash']>=0 and r['detail']['btc']>=0
        ev = json.dumps(r['signal_events']).encode()
        assert hashlib.sha256(ev).hexdigest()==r['signal_event_sha256']
        assert len([p for p in r['detail']['periods'] if p['kind']=='third'])==3
    assert sorted(modes.values())==[10,10,20,20,170,170,850], modes
    for rid in ids-{'V035'}:
        for package in ('R0','R1'):
            r=index['rows'][rid]['packages'][package]
            assert set(r['causal'])=={'S0','S1','S2','S3','S4'}
            assert set(r['halves_S0'])=={'half1','half2'}
            assert len(r['legacy_diagnostic']['cases'])==4
    flow=json.loads(gzip.decompress((DOC/'A7-flow-modeled-v2.json.gz').read_bytes()))
    candles=flow['candles']
    # F08's corrected rejection branch is unreachable on the frozen A7 inputs.
    assert len({c['ts'] for c in candles})==len(candles)
    assert all(c['ts']%14_400_000==0 for c in candles)
    assert all(b['ts']-a['ts']==14_400_000 for a,b in zip(candles,candles[1:]))
    mapping=read(DOC/'A6-mapping.json')
    mutations={x['id']:x for x in read(DOC/'A6-mutations.json')}
    assert len(mapping)==len({x['id'] for x in mapping})==316
    categories=Counter(x['adjudication'] for x in mapping)
    assert sorted(categories.values())==[2,3,13,25,30,243]
    summary=read(DOC/'A6-summary.json')
    for mid,row in mutations.items():
        if row['status']=='caught_assertion':
            assert row['matches']>0 and row['baseline']['exit_code']==0
            # A6 DRIVER reserves 1 for AssertionError, 2 for other exceptions.
            # Three long FlowPoint assertions have truncated 1800-character tails.
            assert row['mutant']['exit_code']==1
            if 'AssertionError' not in row['mutant']['tail']:
                assert mid in {'sabotage_e434:005','sabotage_e434:007','sabotage_e434:015'}
    for mid,kind in summary['valid_runtime_reached'].items():
        row=mutations[mid]
        assert row['matches']>0 and row['baseline']['exit_code']==0
        assert row['mutant']['exit_code']!=0 and kind in row['mutant']['tail']
        assert not any(k in row['mutant']['tail'] for k in ('SyntaxError','ImportError','ModuleNotFoundError'))
    decisions=read(DOC/'A7-M01-M02-zuordnung-v1.json')
    assert decisions['decision_count']==len(decisions['decisions'])==76
    assert decisions['old_code_rows_count']==len(decisions['old_code_rows'])==85
    paired=read(DOC/'A7-paired-statistics-v1.json')
    assert paired['rows']==['V000','V004'] and not paired['selection_adjusted']
    assert len(paired['results'])==10
    assert all(x['previous_N6_U1_identical'] for x in paired['results'])
    assert {x['daily_span']['n'] for x in paired['results']}=={251,253}
    registry=read(DOC/'REGISTER.json')
    expected={f'F{i:02}' for i in range(1,18)}|{'D01','D02','M01','M02','T01'}
    assert len(registry['findings'])==22 and {x['id'] for x in registry['findings']}==expected
    # Restored pending orders and open inventory must resume identically.
    import test_stage4 as cp
    cp.test_pending_buy_checkpoint_json_restart_exact_parity()
    cp.test_open_position_checkpoint_json_restart_exact_parity()
    cp.test_checkpoint_rejects_changed_prefix_config_and_incomplete_reservations()
    causal=read(DOC/'A8-V035-causal-v2.json')
    assert not causal['historical_v035_return_valid']
    assert all(x['passed'] and x['max_error_usd']==0 for x in causal['independent_reference_checks'])
    result=dict(schema='a8-independent-acceptance-v1',register_ids=22,
        original_configurations=86,conditional_spot_rows=85,blocked_rows=['V035'],
        indexed_file_hashes_verified=len(references),causal_files=1250,run_modes=dict(modes),
        frozen_candles_aligned_unique_contiguous=len(candles),
        f08_change_cannot_change_frozen_spot_results=True,
        a6_original_cases_verified=316,a6_categories=dict(categories),
        a6_runtime_failures_checked=len(summary['valid_runtime_reached']),
        m01_decisions=76,m01_code_rows=85,paired_statistics=10,
        checkpoint_checks=3,checkpoint_exact_parity=True,
        a7_index_sha256=sha(DOC/'A7-resultindex-v1.json'),
        a8_v035_sha256=sha(DOC/'A8-V035-causal-v2.json'),
        historical_api_as_of_proven=False,live_approval=False)
    path=DOC/'A8-acceptance-v1.json'
    raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
    if path.exists(): assert path.read_bytes()==raw, 'A8 acceptance changed'
    else: path.write_bytes(raw)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
