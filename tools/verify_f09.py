"""Offline-Nachmessung von F09 mit eingefrorenen Auditdaten und unabhaengigem Losbuch."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BASE = '469be65f65327a3b6abf2794ceba09c1fe0de9e2'
INPUT_HASH = 'ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a'
sys.path.insert(0, str(ROOT / 'engine'))
import backtest
from strategy_core import Candle


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-root', type=Path, required=True,
                        help='Arbeitsbaum mit Audit-Commit ccf2b01 und unveraenderten Eingaben')
    args = parser.parse_args()
    source = args.audit_root.resolve()
    audit_commit = subprocess.run(
        ['git', '-c', f'safe.directory={source.as_posix()}', 'rev-parse', 'HEAD'],
        cwd=source, capture_output=True, check=True, text=True).stdout.strip()
    assert audit_commit == 'ccf2b01c0578346f325261e72445b7375a9ac706'
    subprocess.run(['git', '-c', f'safe.directory={source.as_posix()}', 'diff',
                    '--exit-code', audit_commit, '--', 'audit/book.py', 'docs/e445/'],
                   cwd=source, capture_output=True, check=True)
    inputs = source / 'docs/e445/eingaben.json'
    signals_file = source / 'docs/e445/signale.json'
    assert sha(inputs) == INPUT_HASH, 'Andere Daten sind keine Reproduktion dieses Vergleichs'
    raw = json.loads(inputs.read_text(encoding='utf-8'))
    signals = json.loads(signals_file.read_text(encoding='utf-8'))
    candles = [Candle(**c) for c in raw['candles']]
    spec = importlib.util.spec_from_file_location('f09_independent_book', source / 'audit/book.py')
    book = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = book
    spec.loader.exec_module(book)
    book.selfcheck()
    before_code = subprocess.run(
        ['git', '-c', f'safe.directory={ROOT.as_posix()}', 'show', BASE + ':engine/backtest.py'],
        cwd=ROOT, capture_output=True, check=True).stdout
    namespace = {'__name__': '_f09_original', '__file__': str(ROOT / 'engine/backtest.py')}
    exec(compile(before_code, '<backtest-before-F09>', 'exec'), namespace)
    rows = []
    for name, stream in signals.items():
        if 'kleinere Verkaeufe' in name:
            continue  # E44.4 ist absichtlich nicht Teil dieses main-Korrekturzweigs.
        before = namespace['simulate'](stream, candles, start_ms=raw['start'])
        after = backtest.simulate(stream, candles, start_ms=raw['start'])
        independent = book.account(stream, candles, raw['start'])
        difference = after['ende'] - independent['end']
        assert abs(difference) <= .0051, (name, difference)
        row = dict(name=name,signals=len(stream),before_end=before['ende'],
                   after_end=after['ende'],independent_end=independent['end'],
                   delta_return_pp=(after['ende']-before['ende'])/100,
                   rounding_difference=difference,
                   before_closed_orders=before['trades'],after_closed_orders=after['trades'])
        rows.append(row)
        print(f"{name}: {before['ende']:.2f} -> {after['ende']:.2f}; "
              f"unabhaengig {independent['end']:.6f}")
    assert len(rows) == 5
    toy = [dict(ts=1767225600000, type='KAUF_1', price=120, tranche_pct=100),
           dict(ts=1767240000000, type='TEILVERKAUF_1', price=240, tranche_pct=40)]
    toy += [dict(ts=1767225600000+i*14400000, type='TEILVERKAUF_LADDER',
                 price=240, tranche_pct=15) for i in range(2,6)]
    toy += [dict(ts=1767312000000, type='KAUF_1', price=120, tranche_pct=25)]
    toy_cs = [Candle(1767225600000+i*14400000,p,p,p,p)
              for i,p in enumerate([120]+[240]*5+[120,240])]
    toy_before = namespace['simulate'](toy,toy_cs,start_ms=1767225600000)
    toy_after = backtest.simulate(toy,toy_cs,start_ms=1767225600000)
    assert toy_before['ende'] == 22455.02 and toy_after['ende'] == 24940.04
    result = dict(created_at=datetime.now(timezone.utc).isoformat(),base_commit=BASE,
                  audit_commit=audit_commit,
                  input_sha256=sha(inputs),signals_sha256=sha(signals_file),
                  old_backtest_sha256=hashlib.sha256(before_code).hexdigest(),
                  fixed_backtest_sha256=sha(ROOT/'engine/backtest.py'),
                  independent_book_sha256=sha(source/'audit/book.py'),
                  candles=len(candles),fee=.001,fill='level',start_capital=10000,
                  includes_original_unfinished_last_candle=True,
                  signals_recomputed=False,
                  hand_example=dict(before=toy_before['ende'],after=toy_after['ende']),
                  limitation='Nur F09 geaendert; F01/D01/F12 und weitere Auditbefunde bleiben offen.',
                  rows=rows)
    out = ROOT / 'docs/nacharbeit-2026-09-28/f09-ergebnis.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('5 Vergleiche stimmen mit unabhaengigem Losbuch innerhalb der Cent-Rundung ueberein.')


if __name__ == '__main__':
    main()
