"""Frozen pre-A4 probes; simulated transport only, no original files modified."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BASE = 'aaadbf6606ae1082e2eb59fd0ef1e1d4e1f23c1b'


def worker():
    import main
    import telegram_notify as tg
    from test_main import szenario, _wache_szenario
    sent = []
    with tempfile.TemporaryDirectory() as temp:
        # Each directory models a fresh checkout after TOTAL runner loss.
        for name in ('lost-runner', 'replacement-runner'):
            d = Path(temp)/name
            d.mkdir()
            (d/'config.json').write_text('{"plan_telegram":false,"vorschau_telegram":false}')
            with patch.dict(os.environ, TELEGRAM_BOT_TOKEN='FAKE', TELEGRAM_CHAT_ID='FAKE'), \
                 patch.object(tg.urllib.request, 'urlopen', side_effect=AssertionError('network forbidden')), \
                 patch.object(main, 'deliver_telegram', side_effect=lambda text,*a: sent.append(text) or dict(status='confirmed',message_id=1)), \
                 contextlib.redirect_stdout(io.StringIO()):
                main.run_engine(fetch=szenario, data_dir=d)
    assert len(sent) == 2 and sent[0] == sent[1]
    excluded = {}
    for kind in ('test', 'resend', 'lage', 'watch'):
        with tempfile.TemporaryDirectory() as temp:
            d = Path(temp)
            (d/'config.json').write_text('{"pivot_n":2}')
            (d/'signals.json').write_text(json.dumps({'signals': [dict(ts=14400000,type='KAUF_1',label='offline',price=100,tranche_pct=25,reason='offline')]}))
            def invoke():
                if kind == 'test': return main.send_testnachricht()
                if kind == 'resend': return main.resend_all_signals(data_dir=d)
                if kind == 'lage': return main.lage_abruf(fetch=szenario,data_dir=d,sth=lambda:None)
                raw, _, now = _wache_szenario(tief=100,schluss=106)
                return main.watch_flush(data_dir=d,kerzen_roh=raw,now_ms=now)
            with patch.dict(os.environ,TELEGRAM_BOT_TOKEN='FAKE',TELEGRAM_CHAT_ID='FAKE'), \
                 patch.object(tg.urllib.request,'urlopen',side_effect=AssertionError('network forbidden')), \
                 patch.object(tg,'send_telegram',return_value=False) as sender, \
                 contextlib.redirect_stdout(io.StringIO()):
                invoke(); first=sender.call_count
                invoke(); second=sender.call_count-first
            assert first==(2 if kind=='resend' else 1)
            assert second==(0 if kind=='watch' else first)
            excluded[kind]=dict(rejected_first_attempts=first,second_attempts=second,
                durable_receipt=False,watch_marked_despite_rejection=kind=='watch')
    print(json.dumps(dict(base=BASE, original_F13='see original-f13 below',
                         lost_runner_duplicate_acceptances=len(sent), identical_text=True,
                         excluded_commands=excluded),indent=2))


if __name__ == '__main__':
    if '--worker' in sys.argv:
        worker()
    else:
        with tempfile.TemporaryDirectory() as temp:
            d = Path(temp)
            files = subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'engine'], cwd=ROOT, text=True).splitlines()
            for name in files:
                if name.endswith('.py'):
                    dest=d/name; dest.parent.mkdir(exist_ok=True)
                    dest.write_bytes(subprocess.check_output(['git','show',f'{BASE}:{name}'],cwd=ROOT))
            env={**os.environ,'PYTHONPATH':str(d/'engine'),'PYTHONUTF8':'1'}
            subprocess.run([sys.executable,__file__,'--worker'],env=env,check=True)
        # Exact original F13 block, with its imports, no other audit cases.
        source=(ROOT.parent/'audit-work/audit/additional_probes.py').read_text(encoding='utf-8')
        block=source[source.index('    c=sc.Candle'):source.index('    # Independent causality')]
        imports=source[:source.index('def main():')].replace("ROOT=Path(__file__).resolve().parents[1]",f"ROOT=Path({str(ROOT.parent/'audit-work')!r})")
        code=imports+'\nif True:\n    result={}\n'+block+'    print(json.dumps(result,indent=2))\n'
        subprocess.run([sys.executable,'-c',code],check=True,env={**os.environ,'PYTHONUTF8':'1'})
