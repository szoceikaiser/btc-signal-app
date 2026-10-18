"""Only the affected hosted Actions tests; raw network forbidden."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import produktion_candidate_offline as proof

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--temp-root',type=Path,required=True)
    a=p.parse_args()
    if not a.temp_root.is_absolute() or not a.temp_root.is_dir(): p.error('Existing absolute temp-root required')
    tempfile.tempdir=str(a.temp_root)
    proof.MODULES=('test_actions_delivery',)
    result=proof.run()
    print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
