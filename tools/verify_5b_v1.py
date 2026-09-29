"""Project six existing frozen V1 ledgers; no new historical calculation."""
import gzip
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
def verify():
    with gzip.open(ROOT/'docs/nacharbeit-2026-09-28/4-ledger.json.gz','rt',encoding='utf-8') as f:
        rows=json.load(f)
    checks=[]
    js="""const fs=require('fs'),a=require('./site/chart_signals.js'),e=JSON.parse(fs.readFileSync(0,'utf8'));
    const expected=e.ledger.filter(x=>x.status==='filled');const r=a.merge({signals:[]},{signals:[]},e);
    if(r.issues.length||r.records.length!==expected.length)throw Error('fill count');
    for(const x of expected){const f=r.records.find(s=>s.source_id===x.id);
      if(!f||f.ts!==x.fill_at||f.price!==x.fill_price||f.source!=='simulated_v1_fill')throw Error('fill projection');}
    if(new Set(r.records.map(s=>s.chart_id)).size!==expected.length)throw Error('identity');
    console.log(JSON.stringify({fills:expected.length,result:'PASS'}));"""
    for row in rows:
        for scenario in row['scenarios']:
            check=json.loads(subprocess.check_output(['node','-e',js],
                input=json.dumps(scenario['result']).encode(),cwd=ROOT))
            checks.append(check)
    assert len(checks)==6 and sum(c['fills'] for c in checks)==1101
    return dict(result='PASS',existing_scenarios=6,projected_fills=1101,checks=checks,
                no_historical_recalculation=True)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
