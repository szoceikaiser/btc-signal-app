"""Materialize a reviewable disabled workflow overlay and diff; never install live.

Output must be a new directory. Legacy workflow files are read for the diff,
never edited. No network, activation, push, branch changes or cleanup.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
MAPPING={'signal':'signal','watch':'watch','lage':'lage','pages':'pages',
         'backup':'backup','backup-verify':'backup-verify','monitor':'freshness'}


def materialize(out):
    out=Path(out).resolve();out.mkdir(exist_ok=False)
    target=out/'.github/workflows';target.mkdir(parents=True)
    diff=[];pins={}
    for kind,name in MAPPING.items():
        source=ROOT/'ops/produktion'/f'{kind}-workflow.disabled.yml'
        raw=source.read_bytes();text=raw.decode()
        if 'if: ${{ false }}' not in text or 'self-hosted' in text: raise ValueError('Disabled hosted template required')
        path='.github/workflows/'+name+'.yml';(target/(name+'.yml')).write_bytes(raw)
        old=ROOT/path
        # Canonical tracked bytes, including legacy committed CRLF/BOM. Windows
        # read_text newline translation would produce an unapplyable base diff.
        before=subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT,timeout=15).decode().splitlines(True) if old.exists() else []
        diff.extend(difflib.unified_diff(before,text.splitlines(True),fromfile='a/'+path if old.exists() else '/dev/null',tofile='b/'+path))
        pins[path]=hashlib.sha256(raw).hexdigest()
    (out/'INSTALL-DISABLED.diff').write_text(''.join(diff),encoding='utf-8',newline='\n')
    (out/'WORKFLOW-SHA256.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    return pins


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();materialize(a.out)
