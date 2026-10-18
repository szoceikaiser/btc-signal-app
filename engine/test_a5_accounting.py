"""A5 hand cases plus an independent segregated-collateral Fraction book."""
from decimal import Decimal as D
from fractions import Fraction as F
import derivative_accounting as a

H = 3600000
CAL = dict(interval_ms=8*H, offset_ms=0)


def fill(ts=0, action='open', lot='a', side='short', qty=40, price=100, id=None):
    return dict(id=id or f'{ts}-{action}-{lot}', ts=ts, action=action,
                lot=lot, side=side, qty=qty, price=price)


def payment(ts=8*H, rate='.01'):
    return dict(ts=ts, rate=rate, source='synthetic exact settlement')


def run(fills=None, marks=None, **kw):
    args = dict(instrument=a.PERP, start_ms=0, end_ms=8*H, fee=0,
                calendar=CAL, funding=[payment()])
    args.update(kw)
    return a.replay(fills if fills is not None else [fill()],
                    marks if marks is not None else {0:100,8*H:100}, **args)


def reject(fn, text):
    try:
        fn()
    except a.NotEvaluable as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError('Expected not evaluable: '+text)


def test_a5_two_full_shorts_bind_capital():
    r = run([fill(qty=100), fill(ts=4*H,lot='b',qty=100)],
            {0:100,4*H:100,8*H:90}, funding=[payment(rate=0)])
    entries = [x for x in r['ledger'] if 'fill' in x]
    assert [x['kind'] for x in entries] == ['open','rejected_capital']
    assert entries[0]['after']['margin'] == 10000
    assert entries[0]['after']['available'] == 0
    assert r['end']['equity'] == 11000 and r['end']['gross'] == 9000
    assert r['end']['lots']['a']['qty'] == 100


def test_a5_long_short_funding_signs_and_measured_zero():
    for side, sign in [('long',-1),('short',1)]:
        for rate in ['.01','-.01','0']:
            r = run([fill(side=side)], funding=[payment(rate=rate)])
            expected = D(sign)*4000*D(rate)
            assert r['funding'] == expected
            assert r['end']['equity'] == 10000+expected
            assert r['end']['margin'] == 4000
            assert r['end']['available'] == 6000+expected


def test_a5_spot_is_not_perpetual_long():
    args = dict(instrument=a.SPOT, calendar=None, funding=None)
    r = run([fill(side='long')], **args)
    p = run([fill(side='long')])
    assert r['funding'] == 0 and r['end']['equity'] == 10000
    assert r['end']['wallet'] == 6000 and r['end']['margin'] == 0
    assert p['funding'] == -40 and p['end']['equity'] == 9960
    reject(lambda: run(**args), 'Spot short')
    reject(lambda: run([fill(side='long')], instrument=a.SPOT), 'Spot has no funding')


def test_a5_hand_roundtrips_fees_and_partial_margin():
    for side in ('long', 'short'):
        fs = [fill(side=side), fill(8*H,'close',side=side,qty=10,price=110),
              fill(16*H,'close',side=side,qty=30,price=120)]
        # long PnL=700; short=-700. Use mirrored exit prices for short.
        if side == 'short':
            fs[1]['price'],fs[2]['price'] = 90,80
        marks = {0:100,8*H:fs[1]['price'],16*H:fs[2]['price']}
        r = run(fs, marks, end_ms=16*H, fee='.01',
                funding=[payment(rate='.02'), payment(16*H,'-.01')])
        # Long: 10000+700 - (40+11+36) -88+36 = 10561.
        # Short: 10000+700 -(40+9+24) +72-24 = 10675.
        assert r['end']['equity'] == (10561 if side=='long' else 10675)
        closes = [e for e in r['ledger'] if e['kind']=='close']
        assert closes[0]['after']['margin'] == 3000
        assert closes[-1]['after']['margin'] == 0 and not r['end']['lots']
        assert r['end']['wallet'] == r['end']['equity']


def test_a5_funding_exact_boundaries_partial_close_and_no_postclose_payment():
    fs = [fill(ts=8*H), fill(16*H,'close',qty=10), fill(24*H,'close',qty=30)]
    r = run(fs, {8*H:100,16*H:100,24*H:100,32*H:100}, end_ms=32*H,
            funding=[payment(16*H), payment(24*H)])
    assert r['funding'] == 70  # 40 BTC then 30 BTC; entry boundary excluded.
    assert [(e['ts'],e['payment']) for e in r['ledger'] if e['kind']=='funding'] == [(16*H,40),(24*H,30)]
    assert r['end']['equity'] == 10070
    # A different explicitly supplied settlement schedule is honoured.
    r = run(end_ms=6*H, marks={0:100,2*H:100,6*H:100},
            calendar=dict(interval_ms=4*H,offset_ms=2*H),
            funding=[payment(2*H),payment(6*H)])
    assert r['funding'] == 80


def test_a5_missing_funding_and_mark_never_default_to_zero():
    reject(lambda: run(funding=None), 'Missing explicit')
    reject(lambda: run(funding=[]), 'Missing funding')
    reject(lambda: run(marks={0:100,16*H:100},end_ms=16*H), 'Missing exact funding mark')
    reject(lambda: run(funding=[dict(ts=8*H,rate=None,source='x')]), 'Invalid amount')
    reject(lambda: run(funding=[payment(rate='NaN')]), 'Non-finite')
    reject(lambda: run(funding=[dict(ts=8*H,rate=0,source='')]), 'unsourced')
    reject(lambda: run(funding=[payment(),payment()]), 'duplicate')
    reject(lambda: run(funding=[payment(7*H)]), 'Off-calendar')


def test_a5_risk_and_unsupported_products_do_not_invent_liquidations():
    reject(lambda: run([fill(qty=100)],{0:100,8*H:110}), 'Risk domain')
    reject(lambda: run([fill(qty=100)],funding=[payment(rate='-.01')]), 'Risk domain')
    reject(lambda: run(instrument='inverse_btc_perpetual'), 'Unsupported')
    reject(lambda: run(leverage=2), 'Unsupported')
    reject(lambda: run(capital='NaN'), 'Non-finite')
    # Fee reserve matters even before the first funding payment.
    r = run([fill(qty=100)],fee='.001',funding=[])
    assert r['ledger'][0]['kind'] == 'rejected_capital'
    assert r['end']['equity'] == 10000 and r['fees'] == 0


def test_a5_invalid_fills_and_inputs():
    reject(lambda: run([fill(),fill()]), 'duplicate')
    reject(lambda: run([fill(4*H),fill(0,lot='b')],{0:100,4*H:100,8*H:100}), 'unordered')
    reject(lambda: run([fill(),fill(8*H,'close',qty=41)]), 'Close exceeds')
    reject(lambda: run([fill(),fill(8*H,'close',side='long')]), 'Close exceeds')
    reject(lambda: run([fill(qty=-1)]), 'Invalid quantity')
    reject(lambda: run([fill(),fill(8*H,lot='a')]), 'Reused')
    reject(lambda: run(marks={0:100}), 'Missing end')
    reject(lambda: run(calendar=dict(interval_ms=0,offset_ms=0)), 'Invalid funding calendar')


def test_a5_independent_segregated_collateral_book_every_event():
    # Independently keep FREE cash and collateral separately (production stores wallet).
    # Fixed input tape, Fraction arithmetic, no production valuation/fee helpers.
    fs = [fill(qty=20,side='long'), fill(4*H,lot='b',qty=30,price=110),
          fill(8*H,'close',qty=5,price=105,side='long'),
          fill(12*H,'close',lot='b',qty=30,price=95),
          fill(16*H,'close',qty=15,price=100,side='long')]
    marks = {0:100,4*H:110,8*H:105,12*H:95,16*H:100}
    rates = {8*H:F(1,100),16*H:F(-1,200)}
    r = run(fs,marks,end_ms=16*H,fee='.001',funding=[payment(t,str(float(v))) for t,v in rates.items()])
    free, collateral, holdings = F(10000), {}, {}
    for event in r['ledger']:
        ts = event['ts']; mark = F(marks[ts])
        if event['kind']=='funding':
            for key, (q,entry,direction) in holdings.items():
                free -= direction*q*mark*rates[ts]
        elif event['kind'] in ('open','close'):
            f = next(f for f in fs if f['id']==event['fill']['id'])
            q,p = F(f['qty']),F(f['price']); charge=q*p/1000
            key=f['lot']
            if f['action']=='open':
                collateral[key]=q*p; free-=q*p+charge
                holdings[key]=(q,p,1 if f['side']=='long' else -1)
            else:
                old,entry,direction=holdings[key]
                released=collateral[key]*q/old
                collateral[key]-=released
                free+=released+direction*q*(p-entry)-charge
                holdings[key]=(old-q,entry,direction)
        locked=sum(collateral.values(),F(0))
        value=free+locked+sum((d*q*(mark-p) for q,p,d in holdings.values()),F(0))
        s=event['after']
        assert F(s['available'])==free and F(s['margin'])==locked
        assert F(s['equity'])==value and F(s['wallet'])==free+locked
    # 10000 + 475 realized - 10.175 fees + 18 funding.
    assert r['end']['equity'] == D('10482.825')


def test_a5_spot_roundtrip_capital_conservation_and_costs():
    fs=[fill(side='long'),fill(8*H,'close',side='long',price=110)]
    r=run(fs,{0:100,8*H:110},instrument=a.SPOT,calendar=None,funding=None,fee='.001')
    assert r['end']['equity']==D('10391.6') and r['fees']==D('8.4')
    for instrument in (a.SPOT,a.PERP):
        kw=dict(instrument=instrument,fee=0)
        if instrument==a.SPOT: kw.update(calendar=None,funding=None)
        r=run([fill(side='long')],**kw, **({} if instrument==a.SPOT else {'funding':[payment(rate=0)]}))
        assert all(e['before']['equity']==e['after']['equity'] for e in r['ledger'])


def test_a5_existing_execution_paths_reject_perpetual_long_and_short():
    from execution_v1 import run_v1
    from execution_delayed import run_delayed
    for fn in (run_v1,run_delayed):
        for cfg in [dict(instrument=a.PERP),dict(bias_short=True),dict(leverage=2),dict(instrument='unknown')]:
            reject(lambda: fn([],[],cfg,start_ms=0,end_ms=8*H), 'Long/Spot only')
    a.require_spot_config({})
    a.require_spot_config(dict(instrument=a.SPOT,leverage=1,bias_short=False))


def test_a5_legacy_shorts_rejected_except_labelled_original_reproduction():
    import backtest as bt
    from strategy_core import Candle
    sigs=[dict(ts=0,type='SHORT_1',price=100,tranche_pct=100),
          dict(ts=4*H,type='SHORT_NACHLEGEN',price=100,tranche_pct=100)]
    cs=[Candle(0,100,100,100,100),Candle(4*H,100,100,90,90)]
    reject(lambda:bt.simulate(sigs,cs,start_ms=0,fee=0),'F02')
    old=bt.simulate(sigs,cs,start_ms=0,fee=0,legacy_derivatives=True)
    assert old['rendite_pct']==20 and old['derivative_evaluable'] is False
    assert old['historically_executable'] is False
    assert old['execution_contract']=='legacy_retrospective_diagnostic'
    assert any('F12' in s for s in old['limitations'])


def test_a5_no_long_short_netting_or_unrealized_profit_reuse():
    # A hedge has near-zero net exposure, but each side binds gross collateral.
    r=run([fill(qty=60),fill(0,lot='b',side='long',qty=60)],funding=[payment(rate=0)])
    assert [e['kind'] for e in r['ledger'] if 'fill' in e]==['open','rejected_capital']
    # Profitable short has unrealized gains, but only 1000 free wallet remains.
    r=run([fill(qty=90),fill(4*H,lot='b',qty=20,price=90)],
          {0:100,4*H:90,8*H:90},funding=[payment(rate=0)])
    assert r['end']['margin']==9000 and r['end']['available']==1000
    assert r['end']['equity']==10900 and len(r['end']['lots'])==1


def test_a5_historical_inventory_v035_and_all_original_rows_preserved():
    import hashlib
    import json
    from pathlib import Path
    data=json.loads((Path(__file__).resolve().parents[1]/
        'docs/audit-nacharbeit-2026-10/A5-historical-eligibility-v1.json').read_text(encoding='utf-8'))
    assert len(data['rows'])==86 and len({r['id'] for r in data['rows']})==86
    blocked=[]
    for row in data['rows']:
        canonical=json.dumps(row['params'],sort_keys=True,separators=(',',':'))
        assert hashlib.sha256(canonical.encode()).hexdigest()==row['params_sha256']
        if row['f02_status']=='not_evaluable':
            blocked.append(row['id'])
            reject(lambda:a.require_spot_config(row['params']), 'F02')
        else:
            a.require_spot_config(row['params'])
        assert not row['historical_execution_proven']
    assert blocked==['V035']
