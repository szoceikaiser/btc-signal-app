"""Existing synthetic regression suite with network denial and credential removal."""
import os
from pathlib import Path
import runpy
import socket
import sys
from unittest.mock import patch
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
sys.path.insert(0,str(ROOT/'tools'))


def forbidden(*args,**kwargs):
    raise AssertionError('External network forbidden during P3 local regression')


if __name__=='__main__':
    # Inspect only key names, never retrieve or print ambient credential values.
    for key in list(os.environ):
        if key.startswith(('BTC_DELIVERY_', 'TELEGRAM_', 'GITHUB_', 'GH_')):
            del os.environ[key]
    with patch.object(urllib.request,'urlopen',side_effect=forbidden),\
         patch.object(socket,'create_connection',side_effect=forbidden):
        runpy.run_path(str(ROOT/'engine/run_tests.py'),run_name='__main__')
