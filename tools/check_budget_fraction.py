"""Independent exact policy replay. No engine imports, no tolerance for money decisions."""
from fractions import Fraction as F

BUY={'entry_t1','entry_gp','entry_flush','dip','buy_ladder','liq_buy','upgrade_gp','upgrade_full','e42_buy'}
def number(x):return F(str(x))
def require(ok,rule,event):
    if not ok:raise AssertionError((rule,event.get('order_id')))

def verify(r,scenario,cfg):
    # Run this first even on a consistent old tape: the policy must find the
    # forbidden accepted fill, not merely complain about missing v2 metadata.
    for e in r['ledger']:
        if e['status']=='filled' and e['action'] in BUY:
            require(e['quantity']>0 and e['before']['btc']+e['quantity']!=e['before']['btc'], 'accepted_invisible_buy',e)
    initial=number(r['start']);cash=initial;cycle=F(0);spent=proceeds=fees=residual=F(0)
    pending={};executed={};units=0.;last_plan=None
    fee=number(scenario['fee_pct'])/100
    sig={(s['candle_id'],s['sequence']):s for s in r['signals']}
    legacy=False;checked=0
    def state(s,e):
        nonlocal legacy,checked
        expected=dict(initial=initial,cash=cash,alloc=cycle,spent=spent,proceeds=proceeds,fees=fees,quantity_rounding=residual)
        if 'money' not in s:
            legacy=True;return
        actual=s['money']
        require(set(actual)==set(expected)|{'pending'},'money_schema',e)
        for k,n in expected.items():require(actual[k]==str(n),'money_'+k,e)
        require(actual['pending']=={k:str(n) for k,n in pending.items()},'money_reservations',e)
        require(s['cash']==float(cash) and s['reserved_cash']==float(sum(pending.values(),F(0)))
                and s['available_cash']==float(cash-sum(pending.values(),F(0))),'money_float_views',e)
        require(cash==initial+proceeds-spent and cash>=sum(pending.values(),F(0)),'money_conservation',e)
        checked+=1
    for e in r['ledger']:
        buy=e['action'] in BUY;ident=e['order_id'];s=sig[e['candle_id'],e['sequence']]
        planning=e['status']=='scheduled' or (e['status']=='rejected' and e['reason'] in ('no_cash','no_inventory','exit_priority','sell_excludes_buy'))
        if planning and last_plan!=e['candle_id']:
            if units==0 and not pending:cycle=cash*number(cfg.get('deploy_pct',1))
            last_plan=e['candle_id']
        state(e['before'],e)
        request=cycle*number(s['tranche_pct'])/100
        available=cash-sum(pending.values(),F(0))
        if e['status']=='scheduled' and buy:
            amount=min(available,request)
            require(amount>0,'scheduled_without_budget',e)
            require(ident not in pending,'duplicate_reservation',e)
            # Missing old exact fields do not hide the substantive zero-budget
            # counterexample; old tapes still cannot pass as complete v2 evidence.
            if 'money' in e['before']:
                require(e.get('amount_exact')==str(amount) and e.get('requested_exact')==str(request),'scheduled_exact_budget',e)
                require(e['reserved_amount']==float(amount) and e['requested_amount']==float(request),'scheduled_budget_views',e)
            pending[ident]=amount
        elif e['status']=='filled':
            q=e['quantity'];px=number(e['fill_price'])
            if buy:
                require(ident in pending,'fill_without_reservation',e)
                amount=pending.pop(ident);expected_q=float(amount*(1-fee)/px)
                require(expected_q>0 and units+expected_q!=units,'accepted_without_representable_quantity',e)
                if 'money' in e['before']:
                    require(q==expected_q and e['gross_budget']==float(amount) and e.get('amount_exact')==str(amount),'buy_conversion',e)
                charge=amount*fee;cash-=amount;spent+=amount;units+=q
                delta=amount-charge-number(q)*px;residual+=delta
                executed[ident]=(amount,request)
                if 'money' in e['before']:require(e.get('quantity_rounding_usd')==str(delta),'quantity_rounding_account',e)
            else:
                charge=number(q)*px*fee;net=number(q)*px-charge
                cash+=net;proceeds+=net;units-=q
                if not e['after']['lots']:units=0.
                if 'money' in e['before']:require(e.get('proceeds_exact')==str(net),'sale_proceeds',e)
            fees+=charge
            if 'money' in e['before']:require(e['fee']==float(charge) and e.get('fee_exact')==str(charge),'exact_fee',e)
        elif e['status']=='unfilled_end_of_data' and buy:
            require(ident in pending,'expiry_without_reservation',e);del pending[ident]
        elif e['status']=='rejected' and buy:
            reason=e['reason']
            if reason=='no_cash':require(min(available,request)<=0,'rejected_available_budget',e)
            elif reason=='unrepresentable_btc_increment':
                require(ident in pending,'rejection_without_reservation',e)
                amount=pending[ident]
                price=e['valuation_price']*(1+float(number(scenario['slippage_pct'])/100))
                q=float(amount*(1-fee)/number(price))
                require(q<=0 or units+q==units,'rejected_representable_buy',e)
                require(e['computed_quantity']==q,'rejected_quantity',e)
                require(e['before']['cash']==e['after']['cash'] and e['before']['btc']==e['after']['btc'] and e['before']['lots']==e['after']['lots'],'rejection_preserves_assets',e)
                del pending[ident]
            elif reason=='cash_shortfall':
                require(ident in executed and executed[ident][0]<executed[ident][1],'false_partial_rejection',e)
                a,w=executed[ident];require(e['rejected_budget']==float(w-a),'partial_rejection_amount',e)
            elif reason in ('exit_priority','sell_excludes_buy'):
                require(any(z['candle_id']==e['candle_id'] and z['status']=='scheduled' and z['action'] not in BUY for z in r['ledger']),'false_sale_priority',e)
            else:require(False,'unjustified_buy_rejection',e)
        state(e['after'],e)
    require(not pending,'unreleased_cash',{})
    if units==0:cycle=cash*number(cfg.get('deploy_pct',1))
    require(not legacy,'missing_precise_history',{})
    require(r['cash']==float(cash) and r['fees']==float(fees),'final_money_views',{})
    require(r.get('money')==dict(initial=str(initial),cash=str(cash),alloc=str(cycle),spent=str(spent),proceeds=str(proceeds),fees=str(fees),quantity_rounding=str(residual),pending={}), 'final_exact_money',{})
    return dict(passed=True,method='Independent rational reconstruction from initial capital and declared shares; both policy directions',snapshots=checked,cash=str(cash),fees=str(fees),quantity_rounding_usd=str(residual))
