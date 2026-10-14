"""Run only the new operational completion cases, with network disabled."""
import os
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import test_betriebsabschluss as tests

if __name__=='__main__':
    for key in list(os.environ):
        if key.startswith(('BTC_DELIVERY_','BTC_PAGES_','BTC_MONITOR_','TELEGRAM_','GITHUB_','GH_','COINALYZE_')):
            del os.environ[key]
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--evidence',required=True);p.add_argument('--only',default='');args=p.parse_args()
    evidence=Path(args.evidence).resolve();evidence.mkdir(parents=True,exist_ok=True)
    tests.ARTIFACT_ROOT=evidence/'two-history-example'
    temp=evidence/'scratch';temp.mkdir(exist_ok=True);tempfile.tempdir=str(temp)
    failed=0;count=0
    with patch.object(socket,'create_connection',side_effect=AssertionError('Real network forbidden')):
        for name,fn in sorted(vars(tests).items()):
            if name.startswith('test_') and callable(fn) and (not args.only or args.only in name):
                count+=1
                try: fn();print('PASS',name,flush=True)
                except Exception:
                    failed+=1;print('FAIL',name,flush=True);traceback.print_exc()
    print(f'{count-failed}/{count} new focused tests passed; real network forbidden',flush=True)
    sys.exit(bool(failed))
