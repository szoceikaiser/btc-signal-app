"""Six predeclared V1 comparisons; independent Decimal costs and audit book.

Only reads frozen inputs and 3b results. No network, configuration selection or
new grid. Every filled lot and every close cost basis are checked independently.
"""
import argparse
from copy import deepcopy
from decimal import Decimal as D, localcontext
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'engine'))
import backtest as bt
import strategy_core as sc
import execution_v1 as v


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def near(a, b):
    assert a is not None and abs(float(a)-float(b)) <= max(1e-7, abs(float(b))*2e-10), (a, b)


def independent_costs(result):
    """Decimal lots derived from gross budgets and market open, not book helpers.

    Sales follow reported executed quantity; the second independent audit book
    separately checks sizing from candidates. Check each residual lot after fill.
    """
    lots = {}
    by_time = {}
    realized = D(0)
    bought = disposed = D(0)
    with localcontext() as context:
        context.prec = 45
        fee = D(str(result['fee_pct']))/100
        slip = D(str(result['slippage_pct']))/100
        fills = [e for e in result['ledger'] if e['status'] == 'filled']
        for e in fills:
            buy = e['type'] in {'KAUF_1', 'KAUF_2', 'NACHKAUF', 'RUECKKAUF'}
            quote = D(str(e['valuation_price']))
            price = quote*(1+slip if buy else 1-slip)
            near(e['fill_price'], price)
            if buy:
                cost = D(str(e['gross_budget']))
                quantity = cost*(1-fee)/price
                lots[e['order_id']] = dict(q=quantity, cost=cost, fee=cost*fee,
                    kind='e42' if e['type'] == 'RUECKKAUF' else 'base')
                near(e['quantity'], quantity)
                bought += cost
            else:
                eligible = {k: l for k, l in lots.items()
                            if e['type'] != 'RUECKKAUF_STOP' or l['kind'] == 'e42'}
                total = sum((l['q'] for l in eligible.values()), D(0))
                quantity = D(str(e['quantity']))
                full = e['type'] in {'STOPLOSS', 'VERKAUF_REST', 'RUECKKAUF_STOP'} or e['after']['btc'] == 0
                fraction = D(1) if full else quantity/total
                released = sum((l['cost']*fraction for l in eligible.values()), D(0))
                near(e['disposed_cost'], released)
                pnl = quantity*price*(1-fee)-released
                near(e['realized_pnl'], pnl)
                disposed += released
                realized += pnl
                for key, lot in eligible.items():
                    if full:
                        del lots[key]
                    else:
                        for field in ('q', 'cost', 'fee'):
                            lot[field] *= 1-fraction
            actual = {l['id']: l for l in e['after']['lots']}
            assert set(actual) == set(lots), (e['id'], set(actual), set(lots))
            for key, lot in lots.items():
                for field, expected in (('units', 'q'), ('cost', 'cost'), ('buy_fee', 'fee')):
                    near(actual[key][field], lot[expected])
                assert actual[key]['kind'] == lot['kind']
            q = sum((l['q'] for l in lots.values()), D(0))
            cost = sum((l['cost'] for l in lots.values()), D(0))
            near(e['after']['cost_basis'], cost)
            if q:
                near(e['after']['cost_entry'], cost/q)
            else:
                assert e['after']['cost_entry'] is None
            by_time[e['fill_at']] = (q, cost)
        q = cost = D(0)
        for row in result['equity']:
            q, cost = by_time.get(row['candle_id'], (q, cost))
            near(row['btc'], q)
            near(row['cost_basis'], cost)
            if q:
                near(row['cost_entry'], cost/q)
            else:
                assert row['cost_entry'] is None
        near(bought-disposed, cost)
        # Realized profit plus marked residual profit = change in portfolio.
        unrealized = D(str(result['ende']))-D(str(result['cash']))-cost
        near(result['ende']-10000, realized+unrealized)
    return dict(fills=len(fills), closes=len(result['equity']),
                remaining_cost=float(cost), acquired_cost=float(bought),
                disposed_cost=float(disposed), realized_pnl=float(realized))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-root', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, default=ROOT/'docs/nacharbeit-2026-09-28')
    args = parser.parse_args()
    audit = args.audit_root.resolve()
    files = [audit/'docs/e445'/n for n in ('eingaben.json', 'signale.json', 'ergebnis.json')]
    files += [audit/'audit/book.py', ROOT/'docs/nacharbeit-2026-09-28/3b-ergebnis.json']
    hashes = {(p.relative_to(audit) if p.is_relative_to(audit) else p.relative_to(ROOT)).as_posix(): sha(p) for p in files}
    assert sha(files[0]) == 'ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a'
    assert sha(files[3]) == 'f919af6641400fd91d2f231ed02c5bf68e69242b8267065f8220a6160589f1b8'
    data = json.loads(files[0].read_text(encoding='utf-8'))
    baseline = json.loads(files[4].read_text(encoding='utf-8'))
    cs = [sc.Candle(**c) for c in data['candles']]
    fs = [sc.FlowPoint(**f) for f in data['flow']]
    closed, _ = bt.closed_series(cs, fs, end_ms=data['ende'])
    spec = importlib.util.spec_from_file_location('independent_stage4_audit', files[3])
    book = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(book)
    book.selfcheck()
    assert len(baseline['rows']) == 2
    rows, summaries = [], []
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for row in baseline['rows']:
        scenarios = []
        assert [s['result']['slippage_pct'] for s in row['scenarios']] == [0., .1, .5]
        for old in row['scenarios']:
            prior = old['result']
            slip = prior['slippage_pct']/100
            result = bt.run_execution(cs, fs, row['params'], start_ms=data['start'],
                                      end_ms=data['ende'], slippage=slip)
            costcheck = independent_costs(result)
            orders = {f"v1:{o['ts']}:{o['sequence']}": o for o in result['signals']}
            chosen = [orders[e['order_id']] for e in result['ledger'] if e['status'] == 'scheduled']
            other = book.account(chosen, closed, data['start'], fee=.001, slip=slip, mode='next_open')
            near(result['ende'], other['end'])
            near(result['fees'], other['fees'])
            near(result['dd_close_pct'], -other['dd_close_pct'])
            near(result['dd_intrabar_upper_pct'], -other['dd_intrabar_range_pct'][0])
            near(result['dd_intrabar_lower_pct'], -other['dd_intrabar_range_pct'][1])
            fills = [e for e in result['ledger'] if e['status'] == 'filled']
            otherfills = [f for f in other['fills'] if f['units'] > 1e-15]
            assert len(fills) == len(otherfills)
            for a, b in zip(fills, otherfills):
                assert a['fill_at'] == b['execution_ts'] and a['type'] == b['type']
                near(a['quantity'], b['units'])
                near(a['fee'], b['fee'])
                near(a['before']['cash'], b['cash_before'])
                near(a['after']['cash'], b['cash_after'])
            for a, b in zip(result['equity'], other['path']):
                near(a['cash'], b['cash'])
                near(a['btc'], b['units'])
                near(a['equity'], b['equity'])
            assert len(result['equity']) == len(other['path'])
            for month, point in result['month_ends'].items():
                near(point['equity'], other['month_ends'][month])
            # One predeclared restart per scenario: immediately after first buy fill.
            first = next(e for e in fills if e['type'] in {'KAUF_1', 'KAUF_2', 'NACHKAUF', 'RUECKKAUF'})
            with_checkpoint = bt.run_execution(cs, fs, row['params'], start_ms=data['start'],
                end_ms=data['ende'], slippage=slip, checkpoint_at=first['fill_at'])
            checkpoint = with_checkpoint.pop('checkpoint')
            assert with_checkpoint == result and checkpoint['position']['lots']
            # Independent process reads an actual JSON file after the producer exits.
            # The same frozen data are passed; child imports no parent in-memory state.
            stem = f"4-restart-{len(summaries)}"
            cpfile = args.out_dir/(stem+'.json.gz')
            payload = dict(checkpoint=checkpoint, input_path=str(files[0]))
            with gzip.GzipFile(filename=str(cpfile), mode='wb', mtime=0) as stream:
                stream.write(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode())
            child = subprocess.run([sys.executable, str(ROOT/'tools/verify_4_resume.py'), str(cpfile)],
                                   capture_output=True, text=True, check=True)
            digest = hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()
            assert json.loads(child.stdout)['sha256'] == digest
            oldband = [(s['ts'], s['type'], s['price']) for s in prior['signals']]
            newband = [(s['ts'], s['type'], s['price']) for s in result['signals']]
            summary = dict(name=row['name'], slippage_pct=prior['slippage_pct'],
                end=result['ende'], old_end=prior['ende'], delta_end=result['ende']-prior['ende'],
                dd_close=result['dd_close_pct'], dd_upper=result['dd_intrabar_upper_pct'],
                old_dd_close=prior['dd_close_pct'], old_dd_upper=prior['dd_intrabar_upper_pct'],
                fills=len(fills), old_fills=sum(e['status']=='filled' for e in prior['ledger']),
                signal_band_changed=oldband != newband, costs_verified=costcheck,
                restart_at=first['fill_at'], restart_sha256=digest, restart_identical=True)
            summaries.append(summary)
            scenarios.append(dict(summary=summary, result=result, independent=other))
            print(f"{row['name']} slip {slip:.3f}: {result['ende']:.2f}; delta {summary['delta_end']:+.2f}; "
                  f"DD {result['dd_close_pct']:.4f} / upper {result['dd_intrabar_upper_pct']:.4f}; "
                  f"{len(fills)} fills, costs and process restart PASS", flush=True)
        rows.append(dict(name=row['name'], params=row['params'], scenarios=scenarios))
    assert hashes == {(p.relative_to(audit) if p.is_relative_to(audit) else p.relative_to(ROOT)).as_posix(): sha(p) for p in files}
    report = dict(result='PASS', base='9606a6f555f9cdaee86f9c33a5175c5c5306b365',
                  frozen_hashes=hashes, scope='Same 2 rows x 3 slippages as 3b; no selection',
                  start=data['start'], cutoff=data['ende'], summaries=summaries)
    (args.out_dir/'4-ergebnis.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    with gzip.GzipFile(filename=str(args.out_dir/'4-ledger.json.gz'), mode='wb', mtime=0) as stream:
        stream.write(json.dumps(rows, ensure_ascii=False, allow_nan=False).encode())


if __name__ == '__main__':
    main()
