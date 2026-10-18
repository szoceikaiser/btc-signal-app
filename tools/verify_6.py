"""Only six frozen full V1 runs; secured 5b provenance and independent accounts.

No candidate search, network, main import, delivery or live writes. Accepts an
explicit backup path so the same verification can run in a fresh bundle clone.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import sys
from verify_4_backup import git, sha
from verify_4 import independent_costs, near, bt, sc

ROOT = Path(__file__).resolve().parents[1]
BASE = 'bb862204c97c6bb4c0da49cb6f1de90dd58af663'
DOC = ROOT/'docs/nacharbeit-2026-09-28'

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()

def secured(prior):
    manifest = json.loads((prior/'ABSCHLUSS.json').read_text(encoding='utf-8'))
    assert manifest['commit'] == BASE and manifest['local_tests'] == 728
    assert all(manifest[k] for k in ('bundle_restore_verified', 'full_tree_verified', 'zip_verified'))
    ci = manifest['github']
    assert ci['commit'] == BASE and ci['tests_success'] and ci['runs']
    assert all(r['head_sha'] == BASE and r['name'] == 'Tests' and r['conclusion'] == 'success' for r in ci['runs'])
    for name, expected in manifest['backup_sha256'].items():
        assert sha(prior/name) == expected, name
    tree = json.loads((prior/'git-tree-sha256.json').read_text())
    files = git(ROOT, 'ls-tree', '-r', '--name-only', BASE).decode().splitlines()
    assert set(files) == set(tree)
    for name in files:
        assert hashlib.sha256(git(ROOT, 'show', BASE+':'+name)).hexdigest() == tree[name], name
    for name, expected in manifest['changed_files_sha256'].items():
        assert tree[name] == expected, name
    frozen = prior/'eingefrorene-inputs'
    assert {p.name for p in frozen.iterdir() if p.is_file()} == set(manifest['frozen_hashes'])
    for name, expected in manifest['frozen_hashes'].items():
        assert sha(frozen/name) == expected, name
    return manifest, frozen, tree

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prior-backup', type=Path, default=ROOT.parent/'audit-backups/5b-abschluss-bb86220')
    parser.add_argument('--out-dir', type=Path, default=DOC)
    args = parser.parse_args()
    manifest, frozen, tree = secured(args.prior_backup)
    print('Secured exact 5b commit, full tree, bundle/ZIP and frozen inputs PASS', flush=True)
    def blocked(*a, **kw):
        raise AssertionError('Network forbidden during stage-6 reproduction')
    socket.create_connection = blocked
    socket.socket.connect = blocked
    data = json.loads((frozen/'eingaben.json').read_text(encoding='utf-8'))
    reference = json.loads((DOC/'4-ergebnis.json').read_text())
    assert data['start'] == reference['start'] and data['ende'] == reference['cutoff']
    assert sha(frozen/'eingaben.json') == reference['frozen_hashes']['docs/e445/eingaben.json']
    with gzip.open(DOC/'4-ledger.json.gz', 'rt', encoding='utf-8') as f:
        old_rows = json.load(f)
    assert [r['name'] for r in old_rows] == ['LIVE-heute +Bein in Handelsrichtung', 'LIVE-heute +E42']
    spec = importlib.util.spec_from_file_location('stage6_independent_book', frozen/'book.py')
    book = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(book)
    book.selfcheck()
    cs = [sc.Candle(**c) for c in data['candles']]
    fs = [sc.FlowPoint(**f) for f in data['flow']]
    closed, _ = bt.closed_series(cs, fs, end_ms=data['ende'])
    summaries, rows = [], []
    for row in old_rows:
        assert [s['result']['slippage_pct'] for s in row['scenarios']] == [0., .1, .5]
        scenarios = []
        for saved in row['scenarios']:
            old = saved['result']
            assert old['fee_pct'] == .1
            slip = old['slippage_pct']/100
            result = bt.run_execution(cs, fs, row['params'], start_ms=data['start'], end_ms=data['ende'], slippage=slip)
            assert result == old, (row['name'], slip, 'full result differs')
            index = len(summaries)
            assert digest(result) == manifest['process_replays'][index]['sha256'] == reference['summaries'][index]['restart_sha256']
            costs = independent_costs(result)
            assert costs == reference['summaries'][index]['costs_verified']
            orders = {f"v1:{o['ts']}:{o['sequence']}": o for o in result['signals']}
            chosen = [orders[e['order_id']] for e in result['ledger'] if e['status'] == 'scheduled']
            other = book.account(chosen, closed, data['start'], fee=.001, slip=slip, mode='next_open')
            assert other == saved['independent']
            for actual, expected in [(result['ende'], other['end']), (result['fees'], other['fees']),
                    (result['dd_close_pct'], -other['dd_close_pct']),
                    (result['dd_intrabar_upper_pct'], -other['dd_intrabar_range_pct'][0]),
                    (result['dd_intrabar_lower_pct'], -other['dd_intrabar_range_pct'][1])]:
                near(actual, expected)
            fills = [e for e in result['ledger'] if e['status'] == 'filled']
            otherfills = [f for f in other['fills'] if f['units'] > 1e-15]
            assert len(fills) == len(otherfills)
            for a, b in zip(fills, otherfills):
                assert a['fill_at'] == b['execution_ts'] and a['type'] == b['type']
                for actual, expected in [(a['quantity'], b['units']), (a['fee'], b['fee']),
                    (a['before']['cash'], b['cash_before']), (a['after']['cash'], b['cash_after'])]:
                    near(actual, expected)
            assert len(result['equity']) == len(other['path'])
            for a, b in zip(result['equity'], other['path']):
                for key, field in [('cash', 'cash'), ('btc', 'units'), ('equity', 'equity')]:
                    near(a[key], b[field])
            for month, point in result['month_ends'].items():
                near(point['equity'], other['month_ends'][month])
            summary = dict(name=row['name'], slippage_pct=old['slippage_pct'], fee_pct=.1,
                end=result['ende'], dd_close=result['dd_close_pct'], dd_upper=result['dd_intrabar_upper_pct'],
                delta_vs_secured=0., fills=len(fills), closes=len(result['equity']), costs_verified=costs,
                full_result_identical=True, sha256=digest(result), independent_book_identical=True)
            summaries.append(summary)
            scenarios.append(dict(result=result, independent=other))
            print(f"{row['name']} slip {old['slippage_pct']}%: {result['ende']:.2f}; complete ledger, costs, book PASS", flush=True)
        rows.append(dict(name=row['name'], params=row['params'], scenarios=scenarios))
    assert sum(s['fills'] for s in summaries) == 1101
    assert sum(s['closes'] for s in summaries) == 9054
    # Verify every external input stayed unchanged throughout the runs.
    for name, expected in manifest['frozen_hashes'].items():
        assert sha(frozen/name) == expected
    report = dict(result='PASS', base=BASE, scope='Only frozen 2 rows x 3 slippages; full causal V1 runs',
        secured_5b_tree_files=len(tree), backup_hashes_verified=manifest['backup_sha256'],
        frozen_hashes=manifest['frozen_hashes'], start=data['start'], cutoff=data['ende'],
        closed_candles=len(closed), summaries=summaries, network_blocked=True,
        independence_limit='Audit book checks executed sizing from selected candidates; Decimal checks lots from gross budgets. Neither validates economic merit or historical input availability.')
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir/'6-ergebnis.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    with gzip.GzipFile(filename=str(args.out_dir/'6-ledger.json.gz'), mode='wb', mtime=0) as stream:
        stream.write(json.dumps(rows, ensure_ascii=False, allow_nan=False).encode())

if __name__ == '__main__': main()
