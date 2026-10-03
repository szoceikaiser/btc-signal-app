"""Read-only secured 5a provenance and execution of the original F17 merge."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '6c0c6fdd56db9bb27febaf42c56f6e33bcab0685'

def verify():
    prior = ROOT.parent/'audit-backups/5a-abschluss-6c0c6fd'
    result = json.loads((prior/'ABSCHLUSS.json').read_text(encoding='utf-8'))
    assert result['commit'] == BASE and result['local_tests'] == 712
    assert result['bundle_restore_verified'] and result['github']['tests_success']
    for name, expected in result['backup_sha256'].items():
        assert hashlib.sha256((prior/name).read_bytes()).hexdigest() == expected
    old = ROOT.parent/'etappe-5a-work'
    for name, expected in result['changed_files_sha256'].items():
        blob = subprocess.check_output(['git','show',BASE+':'+name],cwd=old)
        assert hashlib.sha256(blob).hexdigest() == expected, name
        actual = subprocess.check_output(['git','hash-object','--path='+name,name],cwd=old)
        stored = subprocess.check_output(['git','rev-parse',BASE+':'+name],cwd=old)
        assert actual == stored, name
    html = subprocess.check_output(['git','show',BASE+':site/index.html'],cwd=ROOT).decode()
    start, end = html.index('    const seen = new Set();'), html.index('    const markers = ')
    block = html[start:end]+'\nreturn allSig;'
    js = '''const fs=require('fs');const merge=new Function('sig','btsig',BLOCK);
    const live={signals:[{ts:1000,type:'KAUF_1',price:105}]};
    const bt={signals:[{ts:1000,type:'KAUF_1',price:100}]};
    const shown=merge(live,bt);if(shown.length!==1||shown[0].price!==100)throw Error('not reached');
    const l=LIVE;
    const h=HISTORICAL;
    const byKey=new Map(h.signals.map(s=>[s.ts+'|'+s.type,s]));
    const conflicts=l.signals.flatMap(s=>{const b=byKey.get(s.ts+'|'+s.type);return b&&
      (s.price!==b.price||s.tranche_pct!==b.tranche_pct||s.reason!==b.reason)?[{live:s,historical:b}]:[];});
    console.log(JSON.stringify({shown_price:shown[0].price,expected_live_price:105,conflicts}));'''
    audit = ROOT.parent/'audit-work'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=audit).decode().strip() == 'ccf2b01c0578346f325261e72445b7375a9ac706'
    live = subprocess.check_output(['git','show','HEAD:site/data/signals.json'],cwd=audit).decode()
    historical = subprocess.check_output(['git','show','HEAD:site/data/backtest_signals.json'],cwd=audit).decode()
    js = js.replace('BLOCK',json.dumps(block)).replace('LIVE',live).replace('HISTORICAL',historical)
    probe = json.loads(subprocess.check_output(['node'],input=js.encode(),cwd=ROOT))
    assert len(probe['conflicts']) == 2
    return dict(base=BASE, secured_5a_hashes_verified=True, original_f17=probe,
                scope='Original production JavaScript, frozen snapshot; no remote page/session inspected')

if __name__ == '__main__': print(json.dumps(verify(),indent=2,ensure_ascii=False))
