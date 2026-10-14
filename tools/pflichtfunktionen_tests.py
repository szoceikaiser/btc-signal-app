"""Focused test functions only; no pytest dependency or full-suite discovery."""
from pathlib import Path
import os
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'engine'),str(Path(__file__).resolve().parent)]
import test_actions_delivery
import test_pflichtfunktionen

if __name__ == '__main__':
    for key in list(os.environ):
        if key.startswith(('BTC_DELIVERY_', 'BTC_PAGES_', 'TELEGRAM_', 'GITHUB_', 'GH_', 'COINALYZE_')):
            del os.environ[key]
    temp_root = Path(os.environ['BTC_TEST_TMP']).resolve()
    workspace = Path(__file__).resolve().parents[2]
    if not temp_root.is_relative_to(workspace) or not temp_root.is_dir():
        raise ValueError('Existing workspace-contained synthetic temp root required')
    tempfile.tempdir = str(temp_root)
    failed=0;count=0
    with patch.object(socket,'create_connection',side_effect=AssertionError('Real network forbidden')):
        for module in (test_actions_delivery,test_pflichtfunktionen):
            for name,fn in sorted(vars(module).items()):
                if name.startswith('test_') and callable(fn):
                    count+=1
                    try:
                        fn();print('PASS',module.__name__+'.'+name,flush=True)
                    except Exception:
                        failed+=1;print('FAIL',module.__name__+'.'+name,flush=True);traceback.print_exc()
    print(f'{count-failed}/{count} focused tests passed; real network forbidden')
    sys.exit(bool(failed))
