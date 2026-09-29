"""Freeze analysis after synthetic checks and before historical measurement."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from historical_analysis import digest,canonical,dump,ROOT,DOC


def main():
    assert not (DOC/'plan.json').exists(), 'Never overwrite a frozen plan'
    for script,out in [('tools/test_historical_stats.py','synthetic-tests.log'),
                       ('tools/verify_n6_probes.py','new-probes.json')]:
        p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,capture_output=True)
        (DOC/out).write_bytes(p.stdout)
        assert p.returncode==0,p.stderr.decode(errors='replace')
    assert '739 passed, 0 failed' in (DOC/'tests.log').read_text(encoding='utf-8-sig')
    reg=json.loads((ROOT/'docs/nacharbeit-2026-09-28/6-design-register.json').read_text(encoding='utf-8'))
    for row in reg['rows']:assert digest(canonical(row['params']))==row['params_sha256']
    names=[p.relative_to(ROOT).as_posix() for p in (ROOT/'engine').glob('*.py')]
    names+=['tools/'+n for n in ['historical_analysis.py','historical_stats.py','test_historical_stats.py','verify_4.py','verify_n6_probes.py']]
    names+=['docs/nacharbeit-2026-09-28/6-design-register.json','docs/nach-6/data-manifest.json','docs/nach-6/r1-manifest.json',
            'docs/nach-6/synthetic-tests.log','docs/nach-6/new-probes.json']
    plan=dict(version=1,frozen_at=datetime.now(timezone.utc).isoformat(),
        base='05208cecce8d5a0e856a1ea56984b209f403ccd6',
        declaration='Analysis after data knowledge, not historical preregistration',
        input_sha256='ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a',
        book_sha256='f919af6641400fd91d2f231ed02c5bf68e69242b8267065f8220a6160589f1b8',
        packages=dict(R0=dict(input_sha256='ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a',third_indices=[503,1006]),
            R1=dict(input_sha256=digest((DOC/'r1-inputs.json').read_bytes()),third_indices=[507,1014])),
        r1_measured=False,numpy_version=np.__version__,python=sys.version,
        rows=reg['rows'],scenarios=reg['scenarios'],bootstrap=reg['bootstrap'],
        third_indices=[503,1006],fresh_start_policy='at each third boundary, through R0 end; full prior market prefix, FLAT/cash10000',
        days='complete UTC days only; close before new open fills; excluded margins disclosed',
        period_policy='all months and thirds on continuous path; local DD secondary, global peaks never reset',
        dominance_tolerance=dict(usd=.01,dd_pp=1e-8),selection_adjusted=False,
        hash_convention='SHA256 UTF8 bytes with CRLF normalized to LF',
        files={n:digest((ROOT/n).read_bytes().replace(b'\r\n',b'\n')) for n in sorted(names)})
    plan['bootstrap']['numpy_version']=np.__version__
    dump(DOC/'plan.json',plan)
    print('Analysis plan frozen; no historical results calculated')


if __name__=='__main__':main()
