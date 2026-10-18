"""Lokaler F09/D01-Vergleich: unveraenderte Auditdaten, keine API oder Live-Aktion."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BASE = '6edb941b10e4220f4634e4570de8de25261d58b2'
AUDIT = 'ccf2b01c0578346f325261e72445b7375a9ac706'
INPUT_HASH = 'ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a'
sys.path.insert(0, str(ROOT / 'engine'))
import backtest as bt
from strategy_core import Candle, FlowPoint


def git(root, *args):
    return subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}', *args],
                          cwd=root, capture_output=True, check=True).stdout


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-root', type=Path, required=True)
    args = parser.parse_args()
    source = args.audit_root.resolve()
    assert git(source, 'rev-parse', 'HEAD').decode().strip() == AUDIT
    git(source, 'diff', '--exit-code', AUDIT, '--', 'audit/book.py', 'docs/e445/')
    files = [source / 'docs/e445' / name for name in
             ('eingaben.json', 'signale.json', 'ergebnis.json')]
    hashes = {p.name: sha(p) for p in files}
    assert hashes['eingaben.json'] == INPUT_HASH
    data, saved, result = [json.loads(p.read_text(encoding='utf-8')) for p in files]
    cs = [Candle(**c) for c in data['candles']]
    fl = [FlowPoint(**f) for f in data['flow']]
    closed, aligned = bt.closed_series(cs, fl, end_ms=data['ende'])
    # Unabhaengige Erwartung aus UTC-Kalenderdaten, nicht aus dem Filterhelfer.
    last_open = int(datetime(2026, 9, 27, 8, tzinfo=timezone.utc).timestamp() * 1000)
    assert len(cs) == len(fl) == 2481 and cs[-1].ts == last_open
    assert last_open < data['ende'] < last_open + 4 * 60 * 60 * 1000
    assert len(closed) == len(aligned) == 2480 and closed[-1].ts == last_open - 14400000
    assert sum(c.ts >= data['start'] for c in closed) == 1509
    spec = importlib.util.spec_from_file_location('d01_independent_book', source / 'audit/book.py')
    book = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = book
    spec.loader.exec_module(book)
    book.selfcheck()
    old_code = git(ROOT, 'show', BASE + ':engine/backtest.py')
    ns = {'__name__': '_f09_only', '__file__': str(ROOT / 'engine/backtest.py')}
    exec(compile(old_code, '<F09-only>', 'exec'), ns)
    rows = []
    for row in result['zeilen']:
        if row['params'].get('verkauf_faktor', 1) != 1:
            continue
        name, cfg = row['label'], row['params']
        assert 'verkauf_faktor' not in bt.EVAL_KEYS
        before_sig = ns['run_backtest'](cs, fl, cfg, start_ms=data['start'])
        # E44.5 speichert zusaetzlich eine Diagnose, ohne Einfluss auf Signale/Fills.
        saved_core = [{k: v for k, v in s.items() if k != 'beobachtung_kerzen'}
                      for s in saved[name]]
        assert before_sig == saved_core, name + ': F09-Replay weicht ab'
        after_sig = bt.run_backtest(closed, aligned, cfg, start_ms=data['start'])
        expected_sig = [s for s in before_sig if s['ts'] < last_open]
        assert after_sig == expected_sig, name + ': unerwartete Aenderung vor Schlusskerze'
        before = ns['simulate'](before_sig, cs, start_ms=data['start'])
        after = bt.simulate(after_sig, closed, start_ms=data['start'])
        independent = book.account(after_sig, closed, data['start'])
        assert abs(after['ende'] - independent['end']) <= .0051
        old_half = ns['run_half'](cs, fl, cfg, data['start'], end_ms=data['start'] + (data['ende'] - data['start']) // 2)[1]
        new_half = bt.run_half(closed, aligned, cfg, data['start'], end_ms=data['start'] + (data['ende'] - data['start']) // 2)[1]
        rows.append(dict(name=name, before=before, after=after,
                         independent_end=independent['end'],
                         delta_return_pp=(after['ende']-before['ende'])/100,
                         before_signals=len(before_sig),after_signals=len(after_sig),
                         removed_signals=[s for s in before_sig if s['ts'] == last_open],
                         h1_before=old_half, h1_after=new_half))
        print(f"{name}: {before['ende']:.2f} -> {after['ende']:.2f}; "
              f"Signale {len(before_sig)} -> {len(after_sig)}", flush=True)
    assert len(rows) == 5
    assert hashes == {p.name: sha(p) for p in files}
    out = dict(base_commit=BASE, audit_commit=AUDIT, hashes=hashes,
               original_candles=len(cs), closed_candles=len(closed),
               trading_candles=1509, measurement_cutoff_ms=data['ende'],
               saved_created_at=data['erzeugt'], excluded_open_ms=last_open,
               last_closed_open_ms=closed[-1].ts,
               backtest_sha256=sha(ROOT/'engine/backtest.py'),
               independent_book_sha256=sha(source/'audit/book.py'),
               fee=.001, fill='level', capital=10000, signals_recomputed=True, rows=rows)
    dest = ROOT/'docs/nacharbeit-2026-09-28/d01-ergebnis.json'
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('5/5 unabhaengig abgeglichen; Originaldaten unveraendert.', flush=True)


if __name__ == '__main__':
    main()
