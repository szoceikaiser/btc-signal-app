"""Parent wait receipt for a separately authorized probe process. No own API."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import p3_github_probe as probe


def observe_exit(process, plan, journal, timeout=300, *, expected_phase='process-loss'):
    code = process.wait(timeout=timeout)  # timeout is never evidence of termination
    rows = probe.Ledger.verify(journal, probe.digest(plan))
    boundaries = [r for r in rows if r['event'] == 'loss_boundary']
    sending = [r for r in rows if r['event'] == 'sending']
    probe.require(boundaries and sending and boundaries[-1]['run'] == sending[-1]['run']
                  and expected_phase in ('process-loss','public-store-process-loss')
                  and not any(r['event'] == 'phase_end' and r['phase'] == expected_phase for r in rows),
                  'No confirmed interrupted sending boundary')
    probe.require([r for r in rows if r['event'] == 'phase_start'][-1]['pid'] == process.pid
                  and [r for r in rows if r['event'] == 'phase_start'][-1]['phase']==expected_phase,
                  'Observed process must own interrupted phase')
    row = sending[-1]
    return {'schema': 'p3-parent-wait-exit-v2', 'plan_sha256': probe.digest(plan),
        'pid': process.pid, 'observed_wait': True, 'exit_code': code, 'ended_utc': probe.utc(),
        'journal_name': Path(journal).name, 'frontier_hash': rows[-1]['hash'], 'frontier_rows': len(rows),
        'journal_sha256': hashlib.sha256(Path(journal).read_bytes()).hexdigest(),
        'owner': row['run'], 'revision': row['revision'], 'commit': row['commit_sha']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', required=True); p.add_argument('--journal', required=True)
    p.add_argument('--receipt', required=True); p.add_argument('probe_args', nargs=argparse.REMAINDER)
    a = p.parse_args(); args = a.probe_args[1:] if a.probe_args[:1] == ['--'] else a.probe_args
    probe.require('--real' in args and '--phase' in args
                  and args[args.index('--phase')+1] == 'process-loss'
                  and '--journal' in args and args[args.index('--journal')+1] == a.journal
                  and '--plan' in args and args[args.index('--plan')+1] == a.plan,
                  'Only the bound separately authorized process-loss phase')
    plan = json.loads(Path(a.plan).read_text(encoding='utf-8')); probe.validate_plan(plan)
    probe.require(not Path(a.receipt).exists(), 'Receipt must be new')
    process = subprocess.Popen([sys.executable, str(probe.ROOT/'tools/p3_github_probe.py'), *args])
    receipt = observe_exit(process, plan, a.journal)
    with Path(a.receipt).open('x', encoding='utf-8') as f: f.write(probe.canonical(receipt)+'\n')
    print('Parent observed process exit. Receipt is evidence for separate review; no takeover was performed.')
