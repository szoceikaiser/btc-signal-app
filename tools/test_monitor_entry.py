"""Reuse the existing independent full-provider fixture through the real CLI."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import test_free_quota as fixture
import actions_freshness

def main():
    fixture.OUT=ROOT/'.local-tests/github-recovery-monitor-entry'
    fixture.OUT.mkdir(parents=True,exist_ok=False)
    http=fixture.monitor_fixture();now=http.f['base']+60*fixture.operating.slots.MINUTE
    code,result,requests=fixture.monitor_cli(http,now)
    assert code==0 and result['http_status']==200,(code,result)
    assert result['diagnostic']['phase']=='complete'
    assert result['budget']['get']==len(requests.rows)<=actions_freshness.MAX_GET
    http.jobs['105']['jobs'][0]['conclusion']='skipped'
    code,bad,_=fixture.monitor_cli(http,now)
    assert code==20 and bad['http_status']==503
    (fixture.OUT/'RESULT.json').write_text(json.dumps({'normal':result,'skipped_job':bad},indent=2),encoding='utf-8')
    print('PASS actual monitor CLI: all real validators + simulated provider, independent backup, 200/complete')
    print('PASS actual monitor CLI: skipped worker is 503; no healthy claim, no production request')

if __name__=='__main__':main()
