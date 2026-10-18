"""Independent Fraction ledger from submitted orders and frozen market inputs.

No imports of production accounting, quantity, fee, funding or lot helpers.
Production event amounts are assertions, never inputs to the reference balance.
"""
from fractions import Fraction as F

OPEN = {'entry_t1','entry_gp','entry_flush','dip','buy_ladder','liq_buy',
        'upgrade_gp','upgrade_full','e42_buy'}
FULL = {'STOPLOSS','VERKAUF_REST','SHORT_STOPLOSS','SHORT_COVER_REST'}
PART = {'TEILVERKAUF_1','TEILVERKAUF_2','SHORT_TP_1','SHORT_TP_2'}
SPECIAL = {'RUECKKAUF_STOP','SHORT_RUECKTEST_STOP'}
HOUR = 3_600_000


def fraction(x):
    return F(str(x))


def verify(result, *, start, marks, trade_opens, rates, assumed, fee='0.001', capital='10000', deploy='1'):
    wallet, charge, deployment = map(fraction, (capital, fee, deploy))
    lots, peak, allocation = [], F(0), F(0)
    fees = payments = realized = F(0)
    max_error = F(0)
    events = result['book'].events
    consumed = 0
    first_risk = None

    def qty():
        return sum((x['q'] for x in lots), F(0))

    def state(mark):
        margin = sum((x['q']*x['p'] for x in lots), F(0))
        pnl = sum((x['d']*x['q']*(mark-x['p']) for x in lots), F(0))
        return dict(wallet=wallet, equity=wallet+pnl, margin=margin,
                    available=wallet-margin, gross=qty()*mark, unrealized=pnl, qty=qty())

    def equal(actual, expected):
        nonlocal max_error
        error = abs(fraction(actual)-expected)
        max_error = max(max_error, error)
        assert error <= F(1,10**18), (actual, str(expected), float(error))

    def compare(raw, mark):
        for key,value in state(mark).items():
            equal(raw[key],value)

    def risk(mark, at):
        nonlocal first_risk
        s = state(mark)
        breached = s['equity'] <= 0 or s['available'] < 0 or s['gross'] > s['equity']
        if breached and first_risk is None:
            first_risk = at

    def floor_lot(q):
        return F(q*10000//1,10000)

    by_time = {}
    for e in events:
        by_time.setdefault(e['at'],[]).append(e)
    for at in range(start, result['end_at']+1, HOUR):
        mark = fraction(marks[at])
        risk(mark,at)
        current = list(by_time.get(at,[]))
        if at > start and lots:
            assert current and current[0]['kind']=='funding', ('missing payment',at)
            e = current.pop(0)
            compare(e['before'],mark)
            source_rate = rates.get(at-HOUR)
            if source_rate is None:
                assert at-HOUR in assumed, ('missing original rate',at-HOUR)
                source_rate = assumed[at-HOUR]
            amount = -lots[0]['d']*qty()*fraction(source_rate)
            assert e['rate_at']==at-HOUR
            equal(e['qty'],qty())
            equal(e['absolute_rate'],fraction(source_rate))
            equal(e['amount'],amount)
            wallet += amount
            payments += amount
            compare(e['after'],mark)
            risk(mark,at)
            consumed += 1
        for e in current:
            assert e['kind']=='fill'
            o = e['audit_order']
            assert e['at']==o['ts']+4*HOUR, 'non-causal fill'
            compare(e['before'],mark)
            price, pct = fraction(trade_opens[at]),fraction(o['tranche_pct'])
            equal(e['price'],price)
            direction = -1 if o['type'].startswith('SHORT_') else 1
            cost = pnl = F(0)
            if o['action'] in OPEN:
                if not lots:
                    allocation,peak = wallet*deployment,F(0)
                assert not lots or lots[0]['d']==direction
                q = floor_lot(allocation*pct/100/(price*(1+charge)))
                cost = q*price*charge
                old = wallet
                lot = dict(q=q,p=price,d=direction,special=o['action']=='e42_buy')
                lots.append(lot)
                wallet -= cost
                s = state(mark)
                accepted = q>0 and s['equity']>0 and s['available']>=0 and s['gross']<=s['equity']
                if not accepted:
                    lots.pop()
                    wallet = old
                    cost = F(0)
                else:
                    peak = max(peak,qty())
            else:
                if not lots or lots[0]['d']!=direction:
                    q = F(0)
                elif o['type'] in FULL:
                    q = qty()
                elif o['type'] in SPECIAL:
                    q = sum((x['q'] for x in lots if x['special']),F(0))
                else:
                    q = min(qty(),floor_lot(peak*(F(2,5) if o['type'] in PART else pct/100)))
                accepted = q>0
                remaining = q
                for lot in lots:
                    if o['type'] in SPECIAL and not lot['special']:
                        continue
                    take = min(lot['q'],remaining)
                    pnl += direction*take*(price-lot['p'])
                    lot['q'] -= take
                    remaining -= take
                assert remaining==0
                lots = [x for x in lots if x['q']]
                cost = q*price*charge
                wallet += pnl-cost
            assert accepted == (e['status']=='filled'), (at,e['type'])
            equal(e['qty'],q)
            equal(e['fee'],cost)
            equal(e['realized'],pnl)
            fees += cost
            realized += pnl
            compare(e['after'],mark)
            risk(mark,at)
            consumed += 1
    assert consumed == len(events)
    book = result['book']
    equal(book.wallet,wallet)
    equal(book.fees,fees)
    equal(book.funding,payments)
    equal(book.realized,realized)
    equal(book.qty,qty())
    assert first_risk == (book.risk_breaches[0]['at'] if book.risk_breaches else None)
    return dict(method='independent Fraction orders/FIFO/fees/hourly funding/marks',
                events_checked=consumed, all_hourly_marks_checked=True,
                first_risk_at=first_risk, max_error_usd=float(max_error),
                tolerance_usd=1e-18, passed=True)
