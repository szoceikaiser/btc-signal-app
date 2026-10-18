"""A5 synthetic offline fill accounting; no strategy, exchange or live routing.

See A5-VERTRAG.md. Decimal money, explicit marks and settlement calendar.
Missing evidence or a breached risk domain invalidates the whole replay.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation

SPOT = 'spot_btc_usd'
PERP = 'linear_btc_usd_perpetual'


class NotEvaluable(ValueError):
    pass


def number(value):
    if isinstance(value, bool):
        raise NotEvaluable('Boolean is not an amount')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise NotEvaluable('Invalid amount') from None
    if not result.is_finite():
        raise NotEvaluable('Non-finite amount')
    return result


def timestamp(value):
    if type(value) is not int or value < 0:
        raise NotEvaluable('Expected nonnegative UTC milliseconds')
    return value


def require_spot_config(cfg):
    """Existing V1/i+2 defaults mean model Spot, never verified real holdings."""
    if (cfg.get('instrument', SPOT) != SPOT or cfg.get('bias_short', False)
            or number(cfg.get('leverage', 1)) != 1):
        raise NotEvaluable('F02: V1/i+2 is Long/Spot only, leverage=1; derivatives unsupported')


def replay(fills, marks, *, instrument, start_ms, end_ms, capital=10000,
           fee='0.001', leverage=1, funding=None, calendar=None):
    """Replay supplied hypothetical fills, not a causal strategy backtest.

    fills: {id, ts, action: open|close, lot, side: long|short, qty, price}.
    marks: {UTC milliseconds: price}, including every fill and the end.
    funding: [{ts, rate, source}], calendar: {interval_ms, offset_ms}.
    Returns Decimal-valued ledger. Never fills gaps with zero/carried funding.
    """
    start_ms, end_ms = timestamp(start_ms), timestamp(end_ms)
    cash, fee = number(capital), number(fee)
    if (instrument not in (SPOT, PERP) or number(leverage) != 1
            or end_ms < start_ms or cash <= 0 or not 0 <= fee < 1):
        raise NotEvaluable('Unsupported instrument, leverage, window or capital/cost')
    perp = instrument == PERP
    prices = {}
    for ts, price in marks.items():
        timestamp(ts)
        p = number(price)
        if not start_ms <= ts <= end_ms or p <= 0:
            raise NotEvaluable('Invalid mark/window')
        prices[ts] = p
    if end_ms not in prices:
        raise NotEvaluable('Missing end mark')
    by_time, identities, used_lots = {}, set(), set()
    previous = start_ms
    for raw in fills:
        f = deepcopy(raw)
        if set(f) != {'id', 'ts', 'action', 'lot', 'side', 'qty', 'price'}:
            raise NotEvaluable('Incomplete/unknown fill fields')
        ts = timestamp(f['ts'])
        if (not previous <= ts <= end_ms or ts not in prices
                or not isinstance(f['id'], str) or not f['id'] or f['id'] in identities
                or not isinstance(f['lot'], str) or not f['lot']
                or f['action'] not in ('open', 'close') or f['side'] not in ('long', 'short')):
            raise NotEvaluable('Invalid, duplicate or unordered fill')
        f['qty'], f['price'] = number(f['qty']), number(f['price'])
        if f['qty'] <= 0 or f['price'] <= 0 or (not perp and f['side'] == 'short'):
            raise NotEvaluable('Invalid quantity/price or Spot short')
        identities.add(f['id']); previous = ts
        by_time.setdefault(ts, []).append(f)
    settlements, due = {}, set()
    if perp:
        if not isinstance(calendar, dict) or set(calendar) != {'interval_ms', 'offset_ms'} or funding is None:
            raise NotEvaluable('Missing explicit funding calendar/data')
        interval, offset = timestamp(calendar['interval_ms']), timestamp(calendar['offset_ms'])
        if interval <= 0 or offset >= interval:
            raise NotEvaluable('Invalid funding calendar')
        first = start_ms + (offset-start_ms) % interval
        due = set(range(first, end_ms+1, interval))
        for row in funding:
            if set(row) != {'ts', 'rate', 'source'}:
                raise NotEvaluable('Funding needs exact timestamp, rate and source')
            ts = timestamp(row['ts'])
            if ts not in due or ts in settlements or not isinstance(row['source'], str) or not row['source'].strip():
                raise NotEvaluable('Off-calendar, duplicate or unsourced funding')
            settlements[ts] = (number(row['rate']), row['source'])
    elif funding or calendar is not None:
        raise NotEvaluable('Spot has no funding calendar/payments')
    lots, ledger = {}, []
    realized = charges = payments = Decimal(0)

    def state(mark):
        margin = sum((v['qty']*v['entry'] for v in lots.values()), Decimal(0)) if perp else Decimal(0)
        gross = sum((v['qty']*mark for v in lots.values()), Decimal(0))
        pnl = sum((v['direction']*v['qty']*(mark-v['entry']) for v in lots.values()), Decimal(0)) if perp else gross
        return dict(wallet=cash, margin=margin, available=cash-margin,
                    gross=gross, equity=cash+pnl, lots=deepcopy(lots))

    def valid(s):
        return s['equity'] > 0 and s['available'] >= 0 and s['gross'] <= s['equity']

    def record(ts, kind, before, mark, **extra):
        after = state(mark)
        if not valid(after):
            raise NotEvaluable(f'Risk domain breached at {ts} after {kind}; no liquidation assumed')
        ledger.append(dict(ts=ts, kind=kind, mark=mark, before=before, after=after, **extra))

    for ts in sorted(set(prices) | set(by_time) | due):
        if ts not in prices:
            if lots:
                raise NotEvaluable(f'Missing exact funding mark at {ts}')
            continue
        mark = prices[ts]
        before = state(mark)
        if not valid(before):
            raise NotEvaluable(f'Risk domain breached at {ts} before events')
        if ts in due and lots:
            if ts not in settlements:
                raise NotEvaluable(f'Missing funding payment rate at {ts}')
            rate, source = settlements[ts]
            legs = {k: -v['direction']*v['qty']*mark*rate for k,v in lots.items()}
            payment = sum(legs.values(), Decimal(0))
            cash += payment; payments += payment
            record(ts, 'funding', before, mark, rate=rate, source=source, legs=legs, payment=payment)
        for f in by_time.get(ts, []):
            before = state(mark)
            q, p, key = f['qty'], f['price'], f['lot']
            cost = q*p*fee
            if f['action'] == 'open':
                if key in used_lots:
                    raise NotEvaluable('Reused opening lot ID')
                used_lots.add(key)
                old_cash = cash
                cash -= cost if perp else q*p+cost
                lots[key] = dict(qty=q, entry=p, direction=1 if f['side']=='long' else -1)
                if not valid(state(mark)):
                    cash = old_cash; del lots[key]
                    record(ts, 'rejected_capital', before, mark, fill=f, fee=Decimal(0))
                    continue
            else:
                if key not in lots or lots[key]['direction'] != (1 if f['side']=='long' else -1) or q > lots[key]['qty']:
                    raise NotEvaluable('Close exceeds matching actual lot')
                lot = lots[key]
                pnl = lot['direction']*q*(p-lot['entry'])
                cash += pnl-cost if perp else q*p-cost
                realized += pnl
                lot['qty'] -= q
                if not lot['qty']:
                    del lots[key]
            charges += cost
            record(ts, f['action'], before, mark, fill=f, fee=cost)
        record(ts, 'mark', state(mark), mark)
    return dict(contract='A5-offline-book-v1', instrument=instrument,
                scope='hypothetical explicit fills; no strategy/execution or intrabar proof',
                end=state(prices[end_ms]), fees=charges, funding=payments,
                realized_pnl=realized, ledger=ledger)
