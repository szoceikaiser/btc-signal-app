"""Diagnose only ten observed offline failures; never grants full acceptance."""
import argparse,json,platform,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import run_tests
CASES=(
    'test_free_public::test_lost_response_exact_readback_without_retry',
    'test_free_public::test_preflight_cli_anonymous_and_monitor_receipt_readback',
    'test_free_public::test_public_cli_pair_and_confirmed_receipt',
    'test_free_quota::test_pair_counts_and_full_independent_restore',
    'test_free_quota::test_shared_hour_and_header_stops',
    'test_hosted_backup::test_complete_first_backup_fresh_independent_download_receipt_readback',
    'test_hosted_backup::test_missing_old_foreign_moving_parts_and_receipt_confirmation_fail_closed',
    'test_hosted_backup::test_open_sending_states_restore_blocked_without_health_claim',
    'test_offline_runner::test_descendant_python_and_node_cannot_open_sockets_even_with_clean_environment',
    'test_p3_public_root::test_public_unknown_prior_mutation_missing_marker_live_exact_pid_and_kernel_lock',
)
LOG_LIMIT=65536

def diagnose(out):
    expected={module+'::'+name for module,name in run_tests.discover()}
    assert len(CASES)==len(set(CASES))==10 and set(CASES)<=expected
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
    print(json.dumps({'schema':'btc-linux-offline-diagnosis-v1','python':sys.version,'platform':platform.platform(),'cases':list(CASES),'full_acceptance':False,'real_credentials_used':False}),flush=True)
    for index,case in enumerate(CASES):
        row=run_tests.run_one(index,*case.split('::'),out);rows.append(row)
        print(('PASS ' if row['passed'] else 'FAIL ')+case,flush=True)
        if not row['passed']:
            print('DIAGNOSTIC '+json.dumps(row),flush=True)
            for stream in ('stdout','stderr'):
                path=out/row['artifacts']/(stream+'.txt')
                if path.is_file():
                    raw=path.read_bytes();print('::group::'+case+' '+stream+' (first 65536 bytes)',flush=True)
                    print(raw[:LOG_LIMIT].decode('utf-8',errors='replace'),flush=True)
                    if len(raw)>LOG_LIMIT:print('TRUNCATED '+str(len(raw)-LOG_LIMIT)+' bytes',flush=True)
                    print('::endgroup::',flush=True)
    result={'schema':'btc-linux-offline-diagnosis-result-v1','python':sys.version,'platform':platform.platform(),'planned':10,'passed':sum(r['passed'] for r in rows),'failed':sum(not r['passed'] for r in rows),'complete':len(rows)==10,'full_acceptance':False,'results':rows}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result),flush=True);return int(bool(result['failed']) or not result['complete'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True)
    sys.exit(diagnose(parser.parse_args().out))
