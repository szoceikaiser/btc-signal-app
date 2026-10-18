"""Only the original reached F13 case on the exact stage-4 worktree; no full audit."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent/'etappe-4-work'
sys.path.insert(0, str(BASE/'engine'))
import main
import telegram_notify as tg
from test_main import szenario

with tempfile.TemporaryDirectory() as temp:
    directory = Path(temp)
    (directory/'config.json').write_text(json.dumps(dict(plan_telegram=False, vorschau_telegram=False)))
    with patch.dict(os.environ, TELEGRAM_BOT_TOKEN='FAKE', TELEGRAM_CHAT_ID='FAKE'), \
         patch.object(tg, 'send_telegram', return_value=False) as sender, \
         patch.object(tg.urllib.request, 'urlopen', side_effect=AssertionError('network forbidden')), \
         contextlib.redirect_stdout(io.StringIO()):
        first = main.run_engine(fetch=szenario, data_dir=directory)
        attempts = sender.call_count
        second = main.run_engine(fetch=szenario, data_dir=directory)
        retries = sender.call_count-attempts
    state = json.loads((directory/'state.json').read_text())
    assert [s['type'] for s in first] == ['KAUF_1'] and attempts == 1
    assert second == [] and retries == 0
    result = dict(base='ebc01a48057994629c021bd84ab7f9a236678b70',
        reached='real evaluate KAUF_1', first_signals=len(first), first_attempts=attempts,
        restart_signals=len(second), restart_attempts=retries, last_signal_ts=state['last_signal_ts'],
        result='F13 reproduced offline; rejection lost on original')
    print(json.dumps(result, indent=2))
