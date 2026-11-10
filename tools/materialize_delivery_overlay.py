"""Reproducibly build local workflow integration from the unchanged main base."""
from pathlib import Path
import hashlib
import json
import subprocess
import re

ROOT=Path(__file__).resolve().parents[1]
BASE='8b4862745afdf7e4733a7ec7648eb0cc16d65935'
PUBLISHED='514641b64445091d17a59c5a5347e50840c566b4'
m=json.loads((ROOT/'delivery-extension.json').read_bytes())
m['files']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in m['files']}
(ROOT/'delivery-extension.json').write_bytes(json.dumps(m,sort_keys=True,separators=(',',':')).encode())
mh=hashlib.sha256((ROOT/'delivery-extension.json').read_bytes()).hexdigest()
lh=m['files']['tools/pinned_delivery_entry.py']
checkout='''      - name: Checkout independently hash-reviewed delivery extension
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
        with:
          path: extension
          ref: ${{ github.sha }}
          persist-credentials: false
          fetch-depth: 1
'''
def command(relative,core):
    path=relative+'/tools/pinned_delivery_entry.py'
    body=('try:\n p='+json.dumps(path)+'\n if hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()!='
          +json.dumps(lh)+': raise ValueError()\n runpy.run_path(p,run_name="__main__")\n'
          'except SystemExit: raise\nexcept BaseException: sys.exit("delivery phase=bootstrap reason=binding_refused")')
    bootstrap='import hashlib,runpy,sys,pathlib; exec('+json.dumps(body)+')'
    return "python3 -c '"+bootstrap+"' --core "+core+' --extension '+relative+' --manifest-sha256 '+mh
for name in ('signal','watch','lage','freshness','backup','backup-verify','pages'):
    path='.github/workflows/'+name+'.yml'
    text=subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':'+path]).decode().replace('\r\n','\n')
    if name=='freshness':
        text=text.replace('        with:\n          ref: f3f054','        with:\n          path: observer\n          ref: f3f054',1)
        text=text.replace('$(git rev-parse HEAD)','$(git -C observer rev-parse HEAD)')
        strategy='''      - name: Checkout unchanged strategy core for delivery readers
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
        with:
          path: core
          ref: 20d755a4332fb32aeab08b1973b650eeae10f31e
          persist-credentials: false
          fetch-depth: 1
'''
        text=text.replace('      - name: Verify checkout pin before loading code',strategy+'      - name: Verify checkout pin before loading code',1)
    elif name!='pages':
        text=text.replace('        with:\n          ref: 20d755','        with:\n          path: core\n          ref: 20d755',1)
        text=text.replace('$(git rev-parse HEAD)','$(git -C core rev-parse HEAD)')
    text=text.replace('      - name: Verify checkout pin before loading code',checkout+'      - name: Verify checkout pin before loading code',1)
    if name in ('signal','watch','lage'):
        text=text.replace('      - name: Prepare exact reviewed runtime (no store or transport)\n',
            '      - name: Prepare exact reviewed runtime (no store or transport)\n        working-directory: core\n')
        old='python3 tools/produktion_actions_runner.py --runtime .runtime/runtime.json --kind '+name+' --data-dir .runtime/data'
        text=text.replace(old,command('extension','core')+' --runtime core/.runtime/runtime.json --kind '+name+' --data-dir core/.runtime/data')
    elif name=='pages':
        text=text.replace('python3 ../renderer/tools/c05_pages_export.py',command('../extension','.')+' --tool renderer --renderer-root ../renderer --')
    else:
        marker={'freshness':'Read bounded candidate evidence','backup':'Checked exclusive temporary producer entry',
                'backup-verify':'Checked exclusive temporary verifier entry'}[name]
        cwd='observer' if name=='freshness' else 'core'
        text=text.replace('      - name: '+marker+'\n','      - name: '+marker+'\n        working-directory: '+cwd+'\n')
        for tool in ('p4_hosted_backup.py','produktion_actions_freshness.py'):
            core='../core' if name=='freshness' else '.'
            extra=' --observer-root .' if name=='freshness' else ''
            text=text.replace('python3 tools/'+tool,command('../extension',core)+extra+' --tool '+tool+' --')
    if name in ('signal','watch','lage','backup','backup-verify'):
        # A colon-space inside the Python bootstrap is not a YAML plain scalar.
        # Strip chomping preserves the intended command without a final LF.
        text,count=re.subn(r'(?m)^(        )run: (python3 -c .*)$',
            lambda match:match[1]+'run: |-\n'+match[1]+'  '+match[2],text)
        if count!=1: raise ValueError('Exactly one bootstrap run block required: '+name)
    (ROOT/path).write_bytes(text.encode())
print('manifest',mh,'loader',lh)

# Effective policy must be supplied by an authorized reader; never infer it from stale evidence.
import os
review_path=os.environ.get("BTC_MONITOR_REVIEW_FILE")
if review_path:
    policy=json.loads(Path(review_path).read_bytes())
    normalized=json.loads(json.dumps(policy))
    normalized["monitor_entry"]["workflow_sha256"]="SELF_WORKFLOW_SHA256"
    canonical=lambda v:json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
    published=subprocess.check_output(['git','-C',str(ROOT),'show',PUBLISHED+':.github/workflows/freshness.yml']).decode()
    old=re.search(r'expected = "([0-9a-f]{64})"',published).group(1)
    if hashlib.sha256(canonical(normalized)).hexdigest()!=old: raise ValueError("Effective reviewed monitor policy differs; stop publication")
    for name in ("signal","watch","lage","backup","backup-verify","pages"):
        path=".github/workflows/"+name+".yml"
        normalized["entry_workflows"][path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    new=hashlib.sha256(canonical(normalized)).hexdigest()
    target=ROOT/".github/workflows/freshness.yml"
    template_guard=re.search(rb'expected = "([0-9a-f]{64})"',target.read_bytes()).group(1)
    target.write_bytes(target.read_bytes().replace(template_guard,new.encode()))
    print("effective monitor normalized target",new)
else:
    print("BLOCKED: effective monitor policy absent; freshness policy guard is provisional")
