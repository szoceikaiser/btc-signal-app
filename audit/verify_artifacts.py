"""Check audit consistency and preserve exact artifact hashes. No network or live actions."""
import argparse
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'
START='e2b0051199c2e0c38723cc3a23c00ea3bd320601'
EXPECTED='ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a'

def git(*args):
    return subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}',*args],cwd=ROOT).decode('utf-8')
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def text_sha_lf(path):
    try:
        data=path.read_bytes().decode('utf-8')
    except UnicodeDecodeError:
        return None
    return hashlib.sha256(data.replace('\r\n','\n').encode('utf-8')).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify-manifest',action='store_true')
    args=parser.parse_args()
    if args.verify_manifest:
        manifest=read('dateimanifest.json')
        for item in manifest['files']:
            path=ROOT/item['path']
            assert sha(path)==item['sha256'] or (item.get('sha256_lf') is not None and
                    text_sha_lf(path)==item['sha256_lf']),item['path']
        print('Manifest OK:',len(manifest['files']),'Dateien')
        return
    assert git('branch','--show-current').strip()=='codex/audit-2026-09-27'
    assert git('remote','get-url','origin').strip()=='https://github.com/szoceikaiser/btc-signal-app.git'
    changed=git('diff','--name-only',START).splitlines()
    untracked=git('ls-files','--others','--exclude-standard').splitlines()
    allowed=lambda p:p.startswith(('audit/','docs/audit-2026-09-27/'))
    assert all(allowed(p) for p in changed+untracked),[p for p in changed+untracked if not allowed(p)]
    assert git('diff','--name-only',START,'--','engine','site','.github').strip()==''
    assert sha(ROOT/'docs/e445/eingaben.json')==EXPECTED
    for entry in read('reproduktion.json')['files']:
        assert entry['text_equal']
        assert sha(ROOT/'docs/e445'/entry['file'])==entry['original_sha256']
    plan=read('gitter-plan.json')
    frozen=json.loads(git('show','e7e92d3:docs/audit-2026-09-27/gitter-plan.json'))
    assert plan==frozen,'Preregistered plan changed'
    rows=[read('grid/'+r['id']+'.json') for r in plan['rows']]
    assert len(rows)==79
    assert len({json.dumps(r['params'],sort_keys=True) for r in rows})==79
    raw=json.loads((ROOT/'docs/e445/eingaben.json').read_text())
    closed=[c for c in raw['candles'] if c['ts']+14400000<=raw['ende']]
    for p,row in zip(plan['rows'],rows):
        assert p['params']==row['params']
        assert row['input_sha256']==EXPECTED
        assert row['candles']==len(closed)==2480
        if row['long_only']:
            assert len(row['scenarios'])==4
            assert abs(row['scenarios'][0]['end']-row['tolerance']['ende'])<.011
            assert row['scenarios'][0]['fees']>=0
    assert sum(r['long_only'] for r in rows)==78
    for group in ('G1','G2','G3','G4','G5'):
        assert sum(group in r['groups'] for r in rows)==8,group
    assert len(read('parameter-verzeichnis.json')['parameters'])==45
    cases=read('e42-faelle.json')
    obs,episodes,lots=cases['observations'],cases['episodes'],cases['lots']
    assert (len(obs),len(episodes),len(lots))==(57,33,16)
    assert len({(o['start'],o['mark']) for o in obs})==57
    assert len({(e['observation'],e['breakout']) for e in episodes})==33
    assert sum(cases['counts']['terminal'].values())==33
    assert sum(e['replaced_same_bar'] for e in episodes)==1
    checked=read('e42-ablaufkontrolle.json')
    assert checked['signals_exact'] and checked['input_sha256']==EXPECTED
    profile_breakouts=sum((c['kind']=='begin' and c['breakout']>=0) or
                         (c['kind']=='step' and c['result']=='ausbruch')
                         for row in checked['timeline'] for c in row['calls'])
    assert profile_breakouts==33
    by_id={o['id']:o for o in obs}
    for e in episodes:
        end=by_id[e['observation']].get('end')
        assert end is None or e['end']<=end
    for lot in lots:
        assert abs(lot['remaining_units'])<1e-12
        assert abs(lot['units']-sum(e['units'] for e in lot['exits']))<1e-12
        assert abs(lot['pnl']-sum(e['pnl'] for e in lot['exits']))<1e-7
    p=cases['portfolio']
    assert abs(sum(l['pnl'] for l in lots)-p['direct_rk_pnl'])<1e-7
    assert abs(p['difference']-p['direct_rk_pnl']-p['other_lots_difference'])<1e-7
    for key,idx in (('baseline',0),('e42',4)):
        path=[v for v in cases['portfolio_paths'][key] if v['ts']+14400000<=raw['ende']]
        assert len(path)==1509
        assert abs(path[-1]['equity']-rows[idx]['scenarios'][0]['end'])<1e-7
    assert '--- 607 passed, 0 failed' in (OUT/'tests-abschluss.log').read_text(encoding='utf-8')
    jsons=list(OUT.rglob('*.json'))
    for path in jsons:json.loads(path.read_text(encoding='utf-8'))
    missing=[]
    for path in OUT.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            target=unquote(target.strip('<>').split('#')[0])
            if not target or re.match(r'^https?://',target):continue
            if not (path.parent/target).exists():missing.append((path.name,target))
    assert not missing,missing
    # Never print a suspected credential; report only its file if validation fails.
    token_pattern=re.compile(r'(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,}|\b\d{8,}:[A-Za-z0-9_-]{30,})')
    private_hashes={x['sha256'] for x in read('inventar.json')['private_transcripts']}
    for path in list((ROOT/'audit').glob('*'))+list(OUT.rglob('*')):
        if path.is_file() and path.suffix in ('.py','.cjs','.json','.md','.log'):
            assert not token_pattern.search(path.read_text(encoding='utf-8')),f'Potential credential in {path.name}'
            assert sha(path) not in private_hashes,'Private full transcript copied'
    result=dict(checked_at=datetime.now(timezone.utc).isoformat(),
                head_before_snapshot_commit=git('rev-parse','HEAD').strip(),
                production_base=START,production_unchanged=True,input_sha256=EXPECTED,
                preregistration_unchanged=True,configurations=79,long_ledgers_reconciled=78,
                complete_factorial_grids=5,json_files_parsed=len(jsons),markdown_links_valid=True,
                original_tests='607 passed, 0 failed',e42_observations=57,e42_breakouts=33,
                same_bar_replaced=1,e42_lots=16,independent_profile_matches=True,
                private_full_transcripts_added=False,credential_scan='No matching tokens')
    (OUT/'abschlusspruefung.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    files=[]
    for directory in (ROOT/'audit',OUT):
        for path in sorted(directory.rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts or path.name=='dateimanifest.json':continue
            files.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,
                              sha256=sha(path),sha256_lf=text_sha_lf(path)))
    manifest=dict(created_at=result['checked_at'],head_before_snapshot_commit=result['head_before_snapshot_commit'],
                  original_inputs=EXPECTED,
                  text_note='sha256 hashes original working bytes; sha256_lf permits only CRLF/LF normalization by the repository .gitattributes. Binary hashes remain exact.',files=files)
    (OUT/'dateimanifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('Manifest:',len(files),'files')

if __name__=='__main__':main()
