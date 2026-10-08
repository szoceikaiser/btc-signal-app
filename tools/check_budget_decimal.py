"""Second budget-policy proof, independent Decimal transactions, no engine helpers.

10,000 digits with Inexact trapped: exhaustion fails instead of silently rounding.
Stored rational values must terminate exactly when converted; all money products
originate from finite decimals. No absolute/relative/ULP money-policy tolerance.
"""
from decimal import Decimal as D, localcontext, Inexact
import math, struct
BUY={'entry_t1','entry_gp','entry_flush','dip','buy_ladder','liq_buy','upgrade_gp','upgrade_full','e42_buy'}
def d(x):return D(str(x))
def rational(s):
    a,sep,b=s.partition('/')
    return D(a)/D(b) if sep else D(a)
def check(ok,rule,e):
    if not ok:raise AssertionError((rule,e.get('order_id')))

def quantity_float(net, price):
    with localcontext() as ctx:
        ctx.prec=200;ctx.traps[Inexact]=False
        q=float(net/price)
    # Prove the candidate's IEEE nearest-even interval using integer products;
    # the 200-digit quotient is not itself the correctness assumption.
    a,b=net.as_integer_ratio();c,dn=price.as_integer_ratio();n,den=a*dn,b*c
    qn,qd=q.as_integer_ratio();un,ud=math.nextafter(q,math.inf).as_integer_ratio()
    even=struct.unpack('>Q',struct.pack('>d',q))[0]%2==0
    upper=2*n*qd*ud-den*(qn*ud+un*qd)
    assert upper<0 or (upper==0 and even),'BTC upper rounding midpoint'
    if q>0:
        ln,ld=math.nextafter(q,0.).as_integer_ratio()
        lower=2*n*qd*ld-den*(qn*ld+ln*qd)
        assert lower>0 or (lower==0 and even),'BTC lower rounding midpoint'
    return q

def verify(r,s,cfg):
    with localcontext() as context:
        context.prec=10000;context.traps[Inexact]=True
        return replay(r,s,cfg)

def replay(r,s,cfg):
    for e in r['ledger']:
        if e['status']=='filled' and e['action'] in BUY:
            check(e['quantity']>0 and float(e['before']['btc']+e['quantity'])!=e['before']['btc'],'accepted_invisible_buy',e)
    bank=d(r['start']);origin=bank;budget=D(0);outgoing=incoming=charges=rounding=D(0)
    holds={};partial={};btc=0.;planned=None;old=False
    fee=d(s['fee_pct'])/100
    signals={(x['candle_id'],x['sequence']):x for x in r['signals']}
    def inspect(st,e):
        nonlocal old
        if 'money' not in st:old=True;return
        expected=dict(initial=origin,cash=bank,alloc=budget,spent=outgoing,proceeds=incoming,fees=charges,quantity_rounding=rounding)
        check(set(st['money'])==set(expected)|{'pending'},'money_schema',e)
        check(all(rational(st['money'][k])==a for k,a in expected.items()),'transaction_balance',e)
        check({k:rational(a) for k,a in st['money']['pending'].items()}==holds,'reservation_balance',e)
        check(st['cash']==float(bank) and st['reserved_cash']==float(sum(holds.values(),D(0))) and st['available_cash']==float(bank-sum(holds.values(),D(0))),'money_float_views',e)
        check(bank==origin+incoming-outgoing and bank>=sum(holds.values(),D(0)),'money_conservation',e)
    for e in r['ledger']:
        action=e['action'];key=e['order_id'];buy=action in BUY
        signal=signals[e['candle_id'],e['sequence']]
        if e['status']=='scheduled' or e['reason'] in ('no_cash','no_inventory','exit_priority','sell_excludes_buy'):
            if planned!=e['candle_id']:
                if btc==0 and not holds:budget=bank*d(cfg.get('deploy_pct',1))
                planned=e['candle_id']
        inspect(e['before'],e)
        demand=budget*d(signal['tranche_pct'])/100
        usable=bank-sum(holds.values(),D(0))
        if buy and e['status']=='scheduled':
            allocation=min(usable,demand)
            check(allocation>0,'scheduled_without_budget',e)
            check(key not in holds,'duplicate_reservation',e)
            if 'money' in e['before']:
                check(rational(e['amount_exact'])==allocation and rational(e['requested_exact'])==demand and e['reserved_amount']==float(allocation) and e['requested_amount']==float(demand),'exact_allocation',e)
            holds[key]=allocation
        elif e['status']=='filled':
            quantity=d(e['quantity']);quote=d(e['fill_price'])
            if buy:
                check(key in holds,'fill_without_reservation',e);allocation=holds.pop(key)
                # Division for BTC generally repeats. It is the sole rounded
                # boundary; 200 significant digits plus a float midpoint proof.
                rounded=quantity_float(allocation*(1-fee),quote)
                check(rounded>0 and btc+rounded!=btc,'accepted_without_representable_quantity',e)
                if 'money' in e['before']:
                    check(e['quantity']==rounded and e['gross_budget']==float(allocation) and rational(e['amount_exact'])==allocation,'buy_conversion',e)
                charge=allocation*fee;bank-=allocation;outgoing+=allocation
                delta=allocation-charge-quantity*quote;rounding+=delta
                btc+=e['quantity'];partial[key]=(allocation,demand)
                if 'money' in e['before']:check(rational(e['quantity_rounding_usd'])==delta,'quantity_rounding_account',e)
            else:
                charge=quantity*quote*fee;net=quantity*quote-charge
                bank+=net;incoming+=net;btc-=e['quantity']
                if not e['after']['lots']:btc=0.
                if 'money' in e['before']:check(rational(e['proceeds_exact'])==net,'sale_proceeds',e)
            charges+=charge
            if 'money' in e['before']:check(e['fee']==float(charge) and rational(e['fee_exact'])==charge,'exact_fee',e)
        elif buy and e['status']=='unfilled_end_of_data':
            check(key in holds,'expiry_without_reservation',e);del holds[key]
        elif buy and e['status']=='rejected':
            why=e['reason']
            if why=='no_cash':check(min(usable,demand)<=0,'rejected_available_budget',e)
            elif why=='unrepresentable_btc_increment':
                check(key in holds,'rejection_without_reservation',e)
                px=d(e['valuation_price']*(1+float(d(s['slippage_pct'])/100)))
                q=quantity_float(holds[key]*(1-fee),px)
                check(q<=0 or btc+q==btc,'rejected_representable_buy',e)
                check(e['computed_quantity']==q,'rejected_quantity',e)
                check(all(e['before'][k]==e['after'][k] for k in ('cash','btc','lots')),'rejection_preserves_assets',e)
                del holds[key]
            elif why=='cash_shortfall':
                check(key in partial and partial[key][0]<partial[key][1],'false_partial_rejection',e)
                a,w=partial[key];check(e['rejected_budget']==float(w-a),'partial_rejection_amount',e)
            elif why in ('exit_priority','sell_excludes_buy'):
                check(any(x['candle_id']==e['candle_id'] and x['status']=='scheduled' and x['action'] not in BUY for x in r['ledger']),'false_sale_priority',e)
            else:check(False,'unjustified_buy_rejection',e)
        inspect(e['after'],e)
    check(not holds,'unreleased_cash',{})
    if btc==0:budget=bank*d(cfg.get('deploy_pct',1))
    check(not old,'missing_precise_history',{})
    check(r['cash']==float(bank) and r['fees']==float(charges),'final_money_views',{})
    expected=dict(initial=origin,cash=bank,alloc=budget,spent=outgoing,proceeds=incoming,fees=charges,quantity_rounding=rounding)
    check(set(r.get('money',{}))==set(expected)|{'pending'} and not r['money']['pending'] and all(rational(r['money'][k])==n for k,n in expected.items()),'final_exact_money',{})
    return dict(passed=True,method='Independent Decimal transaction proof with Inexact trap, bidirectional policy',cash=str(bank),fees=str(charges),quantity_rounding_usd=str(rounding))
