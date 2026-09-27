"""Replay E44.5 into a separate directory; compare original artifacts."""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/audit-2026-09-27'
sys.path.insert(0, str(ROOT/'engine'))
import e445

def main():
    start=time.monotonic()
    original=ROOT/'docs/e445'
    target=OUT/'replay'
    (target/'docs/e445').mkdir(parents=True, exist_ok=True)
    e445.bt.ROOT=target
    sys.argv=['e445.py','--replay',str(original/'eingaben.json')]
    e445.main()
    rows=[]
    for p in sorted(original.iterdir()):
        a,b=p.read_bytes(),(target/'docs/e445'/p.name).read_bytes()
        rows.append(dict(file=p.name,original_sha256=hashlib.sha256(a).hexdigest(),
                         replay_sha256=hashlib.sha256(b).hexdigest(),byte_equal=a==b,
                         text_equal=a.decode().replace('\r\n','\n')==b.decode().replace('\r\n','\n')))
    result=dict(seconds=time.monotonic()-start,files=rows)
    (OUT/'reproduktion.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    assert all(r['text_equal'] for r in rows), 'Replay differs beyond line endings'

if __name__=='__main__':
    main()
