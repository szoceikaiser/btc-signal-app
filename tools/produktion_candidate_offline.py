"""Executable bounded offline proof; no credentials, external input or network."""
import importlib
import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import traceback
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
MODULES=('test_production_confirmation','test_github_delivery','test_production_runtime',
         'test_production_migration','test_production_operations')

def run(only=None):
    results=[]
    # HTTP and transport are supplied by tests, raw networking is always blocked.
    captured=io.StringIO()
    with redirect_stdout(captured),patch.object(socket,'create_connection',side_effect=AssertionError('Offline proof: network refused')):
        for name in MODULES:
            module=importlib.import_module(name)
            for key,fn in sorted(vars(module).items()):
                if key.startswith('test_') and callable(fn) and (only is None or only==name+'::'+key):
                    try:fn();results.append({'test':name+'::'+key,'passed':True})
                    except Exception:
                        results.append({'test':name+'::'+key,'passed':False,'error':traceback.format_exc()})
    return {'schema':'btc-production-candidate-offline-v1','passed':all(x['passed'] for x in results),
            'count':len(results),'tests':results,'external_requests':0,'live_activation':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--temp-root',type=Path,help='Existing writable absolute temporary directory')
    parser.add_argument('--only',help='One exact module::test name')
    args=parser.parse_args()
    if args.temp_root:
        if not args.temp_root.is_absolute() or not args.temp_root.is_dir():parser.error('Existing absolute temp-root required')
        tempfile.tempdir=str(args.temp_root)
    result=run(args.only)
    if result['count']==0:parser.error('No matching targeted test')
    print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
