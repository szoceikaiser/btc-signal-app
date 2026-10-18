"""Run the isolated causal V035 diagnostic on frozen public inputs only."""
import gzip
import hashlib
import json
import socket
import sys
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
from execution_perp_offline import HOUR, MissingFunding, run as production_run, PerpBook
from a8_perp_reference import verify
from unittest.mock import patch
from copy import deepcopy
from derivative_accounting import NotEvaluable
from strategy_core import Candle, FlowPoint

DOC = ROOT / 'docs/audit-nacharbeit-2026-10'
SRC = DOC / 'A7-V035-sources'
GAPS = [1770206400000, 1771005600000, 1778306400000]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gzip(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def ms(text):
    return int(datetime.fromisoformat(text.replace('Z', '+00:00')).timestamp()*1000)


REFERENCE_CHECKS = []

def run(*args, **kwargs):
    original = PerpBook.fill
    def record(self, order, *a):
        result = original(self, order, *a)
        result['event']['audit_order'] = deepcopy(order)
        return result
    with patch.object(PerpBook, 'fill', record):
        result = production_run(*args, **kwargs)
    checked = verify(result, start=kwargs['start_ms'], marks=kwargs['marks'],
                     trade_opens=kwargs['trade_opens'],
                     rates=kwargs['absolute_rates'], assumed=kwargs.get('assumed_missing', {}))
    REFERENCE_CHECKS.append(checked)
    return result


def main():
    def offline(*args, **kwargs):
        raise AssertionError('A8 causal acceptance is offline')
    socket.socket.connect = socket.create_connection = offline
    previous = json.loads((SRC/'causal-position-discovery-v1.json').read_text(encoding='utf-8'))
    manifest_path = SRC/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    series = {}
    for key, spec in manifest['series'].items():
        path = SRC/spec['file']
        assert digest(path) == spec['sha256']
        rows = load_gzip(path)
        assert len(rows)==spec['count']
        series[key] = {int(x['time']):x for x in rows}
    start, cutoff = manifest['active_start_ms'], manifest['r1_cutoff_ms']
    assert list(series['trade-4h']) == list(range(start,cutoff+1,4*HOUR))
    assert list(series['mark-1h']) == list(range(start-HOUR,cutoff+1,HOUR))
    trade = {t:D(str(x['open'])) for t,x in series['trade-4h'].items()}
    marks = {t+HOUR:D(str(x['close'])) for t,x in series['mark-1h'].items()}
    assert all(t in marks for t in range(start, cutoff+1, HOUR))
    funding_path = ROOT/'docs/nach-6/r1-raw/funding.json'
    assert digest(funding_path) == previous['funding_sha256']
    raw = json.loads(funding_path.read_text(encoding='utf-8'), parse_float=D)
    rates = {ms(x['timestamp']):x['fundingRate'] for x in raw['rates']}
    assert [t for t in range(start,cutoff,HOUR) if t not in rates] == GAPS
    design = json.loads((DOC/'A7-analysemanifest-v1.json').read_text(encoding='utf-8'))
    row = next(x for x in design['rows'] if x['id']=='V035')
    assert row['params_sha256_canonical'] == previous['parameter_sha256']
    cfg = dict(row['params'], muster_cvd='usd', instrument='linear_btc_usd_perpetual')
    flow_path = DOC/'A7-flow-modeled-v2.json.gz'
    assert digest(flow_path) == previous['flow_sha256']
    data = load_gzip(flow_path)
    candles = [Candle(**x) for x in data['candles']]
    flow = [FlowPoint(**x) for x in data['flow']]
    # First pass identifies payment relevance.  Missing-rate assumptions in
    # this pass are labelled and are never accepted as historical returns.
    scenario = run(candles, flow, cfg, start_ms=start, end_ms=cutoff,
                   trade_opens=trade, marks=marks, absolute_rates=rates,
                   assumed_missing={t:D(0) for t in GAPS}, enforce_risk=False)
    prefix_end = ms('2026-02-01T00:00:00Z')
    prefix = run(candles, flow, cfg, start_ms=start, end_ms=prefix_end,
                 trade_opens=trade, marks=marks, absolute_rates=rates)
    assert prefix['book'].events == [x for x in scenario['book'].events
                                    if x['at']<prefix_end or
                                    (x['at']==prefix_end and x['kind']=='funding')]
    relevant = {x['rate_at'] for x in scenario['gap_positions']}
    sensitivity = []
    for illustrative_rate in (D('-1'), D('1')):
        alt = run(candles, flow, cfg, start_ms=start, end_ms=cutoff,
                  trade_opens=trade, marks=marks, absolute_rates=rates,
                  assumed_missing={t:illustrative_rate for t in GAPS},
                  enforce_risk=False)
        sensitivity.append(dict(illustrative_absolute_usd_per_btc=str(illustrative_rate),
                                open_gaps=[x['rate_at'] for x in alt['gap_positions']],
                                first_risk_breach_at=alt['book'].risk_breaches[0]['at']
                                if alt['book'].risk_breaches else None))
    strict = None
    try:
        strict = run(candles, flow, cfg, start_ms=start, end_ms=cutoff,
                     trade_opens=trade, marks=marks, absolute_rates=rates)
    except MissingFunding as exc:
        strict = dict(blocked=True, rate_at=exc.rate_at, settle_at=exc.settle_at,
                      side=exc.side, quantity=str(exc.quantity))
    risk_strict_with_placeholders = None
    try:
        run(candles, flow, cfg, start_ms=start, end_ms=cutoff,
            trade_opens=trade, marks=marks, absolute_rates=rates,
            assumed_missing={t:D(0) for t in GAPS})
    except NotEvaluable as exc:
        risk_strict_with_placeholders = str(exc)
    assert risk_strict_with_placeholders and 'risk breached' in risk_strict_with_placeholders
    book = scenario['book']
    fills = [x for x in book.events if x['kind']=='fill']
    payments = [x for x in book.events if x['kind']=='funding']
    independent_wallet = (D(10000) + sum((D(x['realized'])-D(x['fee']) for x in fills), D(0))
                          + sum((D(x['amount']) for x in payments), D(0)))
    independent_unrealized = sum(((1 if x['side']=='long' else -1)*x['qty']*
                                  (marks[scenario['end_at']]-x['entry']) for x in book.lots), D(0))
    independent_equity = independent_wallet+independent_unrealized
    assert independent_wallet == book.wallet
    assert independent_equity == book.state(marks[scenario['end_at']])['equity']
    result = dict(independent_reference_checks=REFERENCE_CHECKS, schema='a8-v035-causal-position-discovery-v2',
                  contract='closed 4h decision; next contiguous 4h open; 1x PF_XBTUSD linear USD book; current-cycle peak and realized-wallet budget; hourly absolute Kraken funding at period end',
                  model_fee='0.001 S0 assumption, not historical Kraken tariff',
                  parameter_sha256=row['params_sha256_canonical'],
                  manifest_sha256=digest(manifest_path), flow_sha256=digest(flow_path),
                  funding_sha256=digest(funding_path),
                  scenario='zero placeholders ONLY to discover position sensitivity; scenario P&L is not a historical return',
                  gap_positions=scenario['gap_positions'],
                  illustrative_sensitivity=sensitivity,
                  gap_relevance=[dict(rate_at=t,
                                      position_open_in_zero_scenario=t in relevant,
                                      observation=next(x for x in scenario['missing_rate_observations']
                                                       if x['rate_at']==t)) for t in GAPS],
                  strict=strict if isinstance(strict,dict) else dict(blocked=False),
                  strict_risk_with_zero_placeholders=risk_strict_with_placeholders,
                  signal_count=len(scenario['signals']), fill_count=len(fills),
                  accepted_fill_count=sum(x['status']=='filled' for x in fills),
                  funding_payment_count=len(payments),
                  prefix_invariance=dict(through_ms=prefix_end, passed=True),
                  hypothetical_risk_breach_count=len(book.risk_breaches),
                  hypothetical_first_risk_breach=book.risk_breaches[0] if book.risk_breaches else None,
                  end_position=dict(side=book.side, qty=str(book.qty)),
                  independent_wallet_difference_usd=str(book.wallet-independent_wallet),
                  independent_equity_difference_usd=str(book.state(marks[scenario['end_at']])['equity']-independent_equity),
                  historical_v035_return_valid=False,
                  return_blockers=['missing original funding at held 2026-02-13 hour',
                                   '1x risk breach in explicit zero-placeholder diagnostic',
                                   'historical fees, fills and liquidation terms not proven'],
                  historical_api_as_of_proven=False, real_fills_proven=False)
    out = DOC/'A8-V035-causal-v2.json'
    encoded = (json.dumps(result, indent=2, ensure_ascii=False)+'\n').encode('utf-8')
    if out.exists():
        assert out.read_bytes() == encoded, 'Frozen A8 causal V035 result changed'
    else:
        out.write_bytes(encoded)
    print(json.dumps({k:result[k] for k in ('gap_positions','strict','signal_count',
                                           'fill_count','accepted_fill_count',
                                           'funding_payment_count','hypothetical_first_risk_breach',
                                           'historical_v035_return_valid')},
                     indent=2))


if __name__ == '__main__':
    main()
