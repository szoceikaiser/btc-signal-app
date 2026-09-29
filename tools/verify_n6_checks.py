"""Full regression and inherited protection suite, no network or measurements."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'docs/nach-6/checks')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    entries=[]
    for script in ['engine/run_tests.py','tools/test_historical_stats.py','tools/verify_n6_probes.py',
        'tools/verify_5b_probes.py','tools/verify_5b_v1.py','engine/sabotage_5a.py',
        'engine/sabotage_4.py','engine/sabotage_3b.py','engine/sabotage_d01.py','engine/sabotage_f09.py']:
        proc=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,
            env={**os.environ,'PYTHONUTF8':'1','TELEGRAM_BOT_TOKEN':'','TELEGRAM_CHAT_ID':''},capture_output=True)
        (args.out/(Path(script).stem+'.log')).write_bytes(proc.stdout)
        (args.out/(Path(script).stem+'.stderr')).write_bytes(proc.stderr)
        assert proc.returncode==0,(script,proc.stderr.decode(errors='replace'))
        if script=='engine/run_tests.py':assert b'741 passed, 0 failed' in proc.stdout
        entries.append(dict(script=script,result='PASS'))
        print(script,'PASS',flush=True)
    (args.out/'summary.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')


if __name__=='__main__':main()
