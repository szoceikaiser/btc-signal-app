"""Independent long cash/lot accounting; no production accounting helper imported.

Matches the documented historical sizing convention (initial cycle cash, peak BTC
for partial sales). It does NOT make that convention a valid live execution model.
"""
from collections import defaultdict

BUY = {'KAUF_1', 'KAUF_2', 'NACHKAUF', 'RUECKKAUF'}
SELL = {'TEILVERKAUF_LADDER', 'TEILVERKAUF_1', 'TEILVERKAUF_2',
        'VERKAUF_REST', 'STOPLOSS', 'RUECKKAUF_STOP'}
FULL = {'VERKAUF_REST', 'STOPLOSS'}

def account(signals, candles, start, fee=.001, slip=0., mode='level', capital=10000., deploy=1.):
    groups=defaultdict(list)
    idx={c.ts:i for i,c in enumerate(candles)}
    unexecuted=[]
    for num,s in enumerate(signals):
        if s['type'].startswith('SHORT'):
            raise ValueError('Independent book is explicitly long-only')
        if s['type'] not in BUY | SELL:
            continue
        i=idx[s['ts']]
        delay={'level':0,'close':0,'next_open':1,'delay_4h':2}[mode]
        if i+delay>=len(candles):
            unexecuted.append(num)
            continue
        p=s['price'] if mode=='level' else candles[i].close if mode=='close' else candles[i+delay].open
        groups[candles[i+delay].ts].append((num,s,p))
    cash=float(capital)
    peak_units=allocation=fees=turnover=0.
    lots=[]
    fills=[]
    path=[]
    high_water=float(capital)
    dd=0.
    bar_peaks=[float(capital),float(capital)]
    bar_dd=[0.,0.]
    def observe(values,case):
        for value in values:
            bar_peaks[case]=max(bar_peaks[case],value)
            bar_dd[case]=min(bar_dd[case],value/bar_peaks[case]-1)
    cycles=0
    months={}
    for c in candles:
        if c.ts<start:
            continue
        before_units=sum(l['remaining_units'] for l in lots)
        if mode=='close':
            observe([cash+before_units*p for p in (c.open,c.low,c.high,c.close)],0)
            observe([cash+before_units*p for p in (c.open,c.high,c.low,c.close)],1)
        elif mode in ('next_open','delay_4h'):
            for case in (0,1): observe([cash+before_units*c.open],case)
        for num,s,quote in groups[c.ts]:
            buy=s['type'] in BUY
            price=quote*(1+slip if buy else 1-slip)
            units=sum(l['remaining_units'] for l in lots)
            before=cash
            sold=0.
            if buy:
                if units<1e-12:
                    allocation=cash*deploy
                    peak_units=0.
                    cycles+=1
                spent=min(cash,allocation*s['tranche_pct']/100)
                charge=spent*fee
                acquired=(spent-charge)/price
                cash-=spent
                lots.append(dict(id=num,ts=s['ts'],execution_ts=c.ts,type=s['type'],
                                 mark=s.get('stop_ref'),price=price,spent=spent,units=acquired,
                                 remaining_units=acquired,remaining_cost=spent,received=0.,
                                 fees=charge,exits=[]))
                peak_units=max(peak_units,units+acquired)
                quantity=acquired
                nominal=spent
            else:
                eligible=[l for l in lots if l['remaining_units']>1e-15 and
                          (s['type']!='RUECKKAUF_STOP' or l['type']=='RUECKKAUF')]
                available=sum(l['remaining_units'] for l in eligible)
                if s['type'] in FULL or s['type']=='RUECKKAUF_STOP':
                    sold=available
                else:
                    sold=min(available,peak_units*s['tranche_pct']/100)
                nominal=sold*price
                charge=nominal*fee
                cash+=nominal-charge
                fraction=sold/available if available else 0.
                for l in eligible:
                    q=l['remaining_units']*fraction
                    received=q*price*(1-fee)
                    basis=l['remaining_cost']*fraction
                    l['remaining_units']-=q
                    l['remaining_cost']-=basis
                    l['received']+=received
                    l['fees']+=q*price*fee
                    if q>1e-15:
                        l['exits'].append(dict(signal=num,ts=c.ts,type=s['type'],units=q,
                                               price=price,received=received,cost=basis,pnl=received-basis))
                quantity=sold
            fees+=charge
            turnover+=nominal
            assert cash>=-1e-7
            fills.append(dict(signal=num,ts=s['ts'],execution_ts=c.ts,type=s['type'],price=price,
                              units=quantity,cash_before=before,cash_after=cash,fee=charge,nominal=nominal))
        units=sum(l['remaining_units'] for l in lots)
        eq=cash+units*c.close
        if mode=='close':
            for case in (0,1): observe([eq],case)
        elif mode in ('next_open','delay_4h'):
            observe([cash+units*p for p in (c.open,c.low,c.high,c.close)],0)
            observe([cash+units*p for p in (c.open,c.high,c.low,c.close)],1)
        high_water=max(high_water,eq)
        dd=min(dd,eq/high_water-1)
        path.append(dict(ts=c.ts,equity=eq,cash=cash,units=units,exposure=units*c.close/eq if eq else 0))
        from datetime import datetime,timezone
        months[datetime.fromtimestamp((c.ts+14400000-1)/1000,timezone.utc).strftime('%Y-%m')]=eq
    end=path[-1]['equity'] if path else capital
    for l in lots:
        l['marked_value']=l['remaining_units']*candles[-1].close
        l['pnl']=l['received']+l['marked_value']-l['spent']
        l['liquidation_pnl']=l['received']+l['marked_value']*(1-fee)-l['spent']
        l['return_pct']=100*l['pnl']/l['spent'] if l['spent'] else None
    return dict(end=end,return_pct=100*(end/capital-1),dd_close_pct=100*dd,fees=fees,
                dd_intrabar_range_pct=sorted(100*x for x in bar_dd) if mode!='level' else None,
                turnover=turnover,orders=sum(x['units']>1e-15 for x in fills),
                zero_orders=sum(x['units']<=1e-15 for x in fills),cycles=cycles,
                avg_exposure_pct=100*sum(x['exposure'] for x in path)/len(path) if path else 0,
                fills=fills,lots=lots,path=path,month_ends=months,unexecuted=unexecuted)

def selfcheck(sabotage=False):
    from types import SimpleNamespace
    candles=[SimpleNamespace(ts=i,open=100.,close=p,low=p,high=p) for i,p in enumerate([100.,120.,90.])]
    signals=[dict(ts=0,type='KAUF_1',price=100.,tranche_pct=100),
             dict(ts=1,type='TEILVERKAUF_1',price=120.,tranche_pct=50),
             dict(ts=2,type='STOPLOSS',price=90.,tranche_pct=100)]
    r=account(signals,candles,0,fee=.01 if not sabotage else 0)
    # Hand calculation: buy 99 BTC, sell 49.5 at 120 and 49.5 at 90, each less 1%.
    assert abs(r['end']-(49.5*120*.99+49.5*90*.99))<1e-8
    assert abs(r['fees']-(100+49.5*120*.01+49.5*90*.01))<1e-8
    assert abs(sum(l['pnl'] for l in r['lots'])-(r['end']-10000))<1e-8
    assert r['orders']==3

if __name__=='__main__':
    selfcheck()
    try:
        selfcheck(sabotage=True)
    except AssertionError:
        print('Independent book: hand example PASS; fee sabotage CAUGHT')
    else:
        raise AssertionError('Sabotage survived')
