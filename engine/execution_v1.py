"""Causal offline Long/Spot execution, contract V1 (stage 3b).

Closed-bar knowledge -> next contiguous eligible 4h open. No live routing,
conditional orders, funding or persisted broker position. Legacy backtest.py
signal-band accounting remains only a named historical diagnostic.
"""
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import math

import strategy_core as sc

STEP = 14_400_000
BUY_ACTIONS = {'entry_t1', 'entry_gp', 'entry_flush', 'dip', 'buy_ladder',
               'liq_buy', 'upgrade_gp', 'upgrade_full', 'e42_buy'}
# The documented generator order, not an assumed intrabar price path.
ACTION_ORDER = ['entry_t1', 'entry_gp', 'entry_flush', 'dip', 'stop', 'part_full',
                'part_stop', 'buy_ladder', 'liq_buy', 'liq_sell', 'resistance',
                'high', 'upgrade_gp', 'upgrade_full', 'tp_ladder', 'tp1', 'tp2',
                'rest_pattern', 'rest_stale', 'e42_buy']
FULL = {'STOPLOSS', 'VERKAUF_REST'}


@dataclass
class Decision:
    candidates: list
    observed: sc.Position
    sell_state: sc.Position
    before: sc.Position
    candles: list
    flow: list
    params: dict

    def confirm(self, position, executed, book):
        """Re-evaluate the SAME known prefix, allowing only executed blocks.

        The reference-price entry formula is intentionally unchanged (F04).
        Partial cash funding scales its existing tranche weighting. Actual BTC
        and available cash are carried separately by Book, never by that formula.
        """
        accepted = {o['action']: o for o in executed}
        full = any(o['type'] in FULL for o in executed)
        if full:
            result = deepcopy(self.sell_state)
        else:
            result = deepcopy(self.before)
            sizes = {a: o['tranche_pct'] * o['fraction'] for a, o in accepted.items()}
            sc._evaluate(self.candles, self.flow, result, **self.params,
                         _execution_gate=lambda a: a in accepted,
                         _execution_sizes=sizes)
        # F09: a fully sold book is FLAT even if percentage arithmetic says TP2.
        if book.units == 0 and executed:
            sc._reset_position(result)
        if book.units > 0:
            result.bestand_pct = book.invested_pct
            if book.rk_units == 0:
                result.e42_teil_marke = None
                result.e42_teil_wartet = 0
                result.e42_teil_wartet_inv = result.e42_teil_geprueft = None
        position.__dict__.update(deepcopy(result.__dict__))


def decide(candles, flow, position, params):
    """Both sides see the same booked pre-decision position and known prefix.

    Opposite-side trading blocks are disabled BEFORE any writes. Virtual same-
    side stage transitions retain TP1/TP2 and GP/FULL candidate dependencies.
    no_flip is superseded by D2 at scheduling, not allowed to hide conflicts.
    """
    params = dict(params, bias_short=False, no_flip=False)
    before = deepcopy(position)
    observed = deepcopy(before)
    sc._evaluate(candles, flow, observed, **params, _execution_gate=lambda a: False)
    candidates = []
    sell_state = None
    for buy in (True, False):
        probe = deepcopy(before)
        sigs = sc._evaluate(candles, flow, probe, **params,
                            _execution_gate=lambda a: (a in BUY_ACTIONS) == buy)
        if not buy:
            sell_state = probe
        for sig in sigs:
            if sig.type == sc.SignalType.WARNUNG:
                continue
            candidates.append(dict(sig.to_dict(), action=sig.execution_action))
    candidates.sort(key=lambda o: ACTION_ORDER.index(o['action']))
    position.__dict__.update(deepcopy(observed.__dict__))
    return Decision(candidates, observed, sell_state, before, candles, flow, params)


class Book:
    def __init__(self, capital, fee, slip, deploy, initial_units=0.):
        self.cash = float(capital)
        self.units = float(initial_units)
        self.peak_units = self.units
        self.rk_units = 0.
        self.alloc = self.cash * deploy if self.units else 0.
        self.invested_pct = 100. if self.units else 0.
        self.fee, self.slip, self.deploy = fee, slip, deploy
        self.reserved_cash = self.reserved_units = 0.
        self.ledger = []

    def value(self, price):
        return self.cash + self.units * price

    def snapshot(self, price):
        return dict(cash=self.cash, btc=self.units, reserved_cash=self.reserved_cash,
                    reserved_btc=self.reserved_units, available_cash=self.cash-self.reserved_cash,
                    available_btc=self.units-self.reserved_units, rk_btc=self.rk_units,
                    market_value=self.units*price, equity=self.value(price))

    def event(self, order, status, reason, at, price, before, **details):
        self.ledger.append(dict(id=f"{order['id']}:{len(self.ledger)}", order_id=order['id'],
            candle_id=order['ts'], knowledge_assumed_at=order['ts']+STEP,
            decision_at=order['ts']+STEP, order_at=order['ts']+STEP,
            scheduled_at=order['ts']+STEP, event_at=at, sequence=order['sequence'],
            action=order['action'], type=order['type'], signal_reason=order.get('reason',''),
            reference_price=order['price'], valuation_price=price, fill_at=None,
            fill_price=None, status=status, reason=reason, fee=0., quantity=0.,
            before=before, after=self.snapshot(price), **details))

    def quantities(self, o):
        if o['action'] in BUY_ACTIONS:
            return min(self.cash-self.reserved_cash, self.alloc * o['tranche_pct']/100)
        if o['type'] in FULL:
            return self.units-self.reserved_units
        if o['type'] == 'RUECKKAUF_STOP':
            return min(self.units-self.reserved_units, self.rk_units)
        # Existing TP1/TP2 each 40%; ladder uses its existing declared quote.
        share = o['tranche_pct']/100 if o['type']=='TEILVERKAUF_LADDER' else .4
        q = min(self.units-self.reserved_units, self.peak_units*share)
        if q > 0 and 0 < self.units-self.reserved_units-q <= 8*math.ulp(self.peak_units):
            q = self.units-self.reserved_units
        return q

    def schedule(self, candidates, close_price):
        if self.units == 0:
            self.alloc = self.cash*self.deploy
            self.peak_units = self.rk_units = 0.
            self.invested_pct = 0.
        orders = [dict(o, sequence=i, id=f"v1:{o['ts']}:{i}") for i,o in enumerate(candidates)]
        sellable = [o for o in orders if o['action'] not in BUY_ACTIONS and self.quantities(o)>0]
        full = [o for o in sellable if o['type'] in FULL]
        if full:
            # Main stop first; stable generation sequence for other full exits.
            chosen = [min(full,key=lambda o:(o['action']!='stop',o['sequence']))]
        elif sellable:
            chosen = sorted(sellable,key=lambda o:(o['type']!='RUECKKAUF_STOP',o['sequence']))
        else:
            chosen = [o for o in orders if o['action'] in BUY_ACTIONS]
        pending=[]
        for o in orders:
            if o not in chosen:
                reason = 'exit_priority' if full else 'sell_excludes_buy' if sellable and o['action'] in BUY_ACTIONS else 'no_inventory'
                self.event(o,'rejected',reason,o['ts']+STEP,close_price,self.snapshot(close_price))
        for o in chosen:
            buy=o['action'] in BUY_ACTIONS
            amount=self.quantities(o)
            requested=self.alloc*o['tranche_pct']/100 if buy else amount
            before=self.snapshot(close_price)
            if amount <= 0:
                self.event(o,'rejected','no_cash' if buy else 'no_inventory',o['ts']+STEP,close_price,before)
                continue
            o.update(amount=amount, requested=requested)
            if buy: self.reserved_cash += amount
            else: self.reserved_units += amount
            self.event(o,'scheduled','next_open',o['ts']+STEP,close_price,before,
                       reserved_amount=amount, requested_amount=requested)
            pending.append(o)
        return pending

    def fill(self, o, candle):
        before=self.snapshot(candle.open)
        buy=o['action'] in BUY_ACTIONS
        price=candle.open*(1+self.slip if buy else 1-self.slip)
        amount=o['amount']
        if buy:
            self.reserved_cash -= amount
            quantity=amount*(1-self.fee)/price
            charge=amount*self.fee
            self.cash -= amount
            self.units += quantity
            self.invested_pct = min(100., self.invested_pct + amount/self.alloc*100)
            if o['type']=='RUECKKAUF': self.rk_units += quantity
            self.peak_units=max(self.peak_units,self.units)
        else:
            self.reserved_units -= amount
            if 0 < self.units-amount <= 8*math.ulp(self.peak_units) and self.reserved_units <= 8*math.ulp(self.peak_units):
                amount=self.units  # F09, including the last fill of a multi-sale package.
            quantity=amount
            charge=quantity*price*self.fee
            old=self.units
            self.cash += quantity*price-charge
            self.units -= quantity
            self.invested_pct *= self.units/old
            if o['type']=='RUECKKAUF_STOP' or self.units==0:
                self.rk_units=0.
            else:
                self.rk_units *= self.units/old
        # Round only numerical reservation subtraction noise, never BTC minima.
        if abs(self.reserved_cash) <= 8*math.ulp(max(1.,self.cash)): self.reserved_cash=0.
        if abs(self.reserved_units) <= 8*math.ulp(max(self.peak_units,1e-300)): self.reserved_units=0.
        fraction=amount/o['requested'] if buy and o['requested'] else 1.
        event=dict(id=f"{o['id']}:{len(self.ledger)}",order_id=o['id'],candle_id=o['ts'],
            knowledge_assumed_at=o['ts']+STEP,decision_at=o['ts']+STEP,order_at=o['ts']+STEP,
            scheduled_at=o['ts']+STEP,event_at=candle.ts,fill_at=candle.ts,
            sequence=o['sequence'],action=o['action'],type=o['type'],reference_price=o['price'],
            signal_reason=o.get('reason',''),valuation_price=candle.open,fill_price=price,
            status='filled',reason='partial_cash' if fraction<1 else 'next_open',
            fee=charge,quantity=quantity,gross_budget=amount if buy else None,
            before=before,after=self.snapshot(candle.open))
        self.ledger.append(event)
        if fraction<1:
            self.event(o,'rejected','cash_shortfall',candle.ts,candle.open,self.snapshot(candle.open),
                       rejected_budget=o['requested']-amount)
        assert self.cash >= -1e-8 and self.units >= 0 and self.rk_units <= self.units+1e-10
        return dict(o, fraction=fraction)

    def expire(self, o, close):
        before=self.snapshot(close)
        if o['action'] in BUY_ACTIONS: self.reserved_cash-=o['amount']
        else: self.reserved_units-=o['amount']
        self.event(o,'unfilled_end_of_data','no_eligible_next_open',o['ts']+STEP,close,before)


class Risk:
    def __init__(self, start):
        self.peaks=[start]*3
        self.dd=[0.]*3

    def observe(self, value, cases=(1,2)):
        for i in cases:
            self.peaks[i]=max(self.peaks[i],value)
            self.dd[i]=max(self.dd[i],1-value/self.peaks[i])

    def bar(self, book, c):
        for i,prices in [(1,(c.low,c.high,c.close)),(2,(c.high,c.low,c.close))]:
            for p in prices: self.observe(book.value(p),(i,))
        self.observe(book.value(c.close),(0,))


def validate(candles, flow, end_ms):
    if len(flow)!=len(candles) or any(c.ts!=f.ts for c,f in zip(candles,flow)):
        raise ValueError('V1 requires aligned candles and flow')
    if any(b.ts-a.ts!=STEP for a,b in zip(candles,candles[1:])):
        raise ValueError('V1 data_gap: missing, duplicate or unordered 4h candle')
    for c in candles:
        if c.ts%STEP or not all(math.isfinite(p) and p>0 for p in (c.open,c.high,c.low,c.close)) or not c.low<=min(c.open,c.close)<=max(c.open,c.close)<=c.high:
            raise ValueError('Invalid UTC 4h OHLC candle')
    # Filter paired inputs together; never recover an open from a D01-rejected bar.
    keep=[i for i,c in enumerate(candles) if c.ts+STEP<=end_ms]
    return [candles[i] for i in keep], [flow[i] for i in keep]


def run_v1(candles, flow, cfg, *, start_ms, end_ms, fee=.001, slippage=0.,
           start_capital=10000., initial_units=0., initial_position=None,
           decision_fn=decide):
    """Closed-loop simulation. Every cost scenario regenerates its own decisions.

    end_ms MUST be the frozen input's historical cutoff, not the current clock.
    initial holdings are an explicit hand-case hook, never used in measurements.
    """
    if cfg.get('bias_short',False): raise ValueError('V1 is Long/Spot only')
    deploy=cfg.get('deploy_pct',1.)
    if not (0<=fee<1 and 0<=slippage<1 and 0<=deploy<=1 and start_capital>=0 and initial_units>=0 and start_capital+initial_units>0):
        raise ValueError('Invalid capital/cost parameters')
    cs,fs=validate(candles,flow,end_ms)
    active=[c for c in cs if c.ts>=start_ms]
    if not active: raise ValueError('No eligible closed trading candles')
    if bool(initial_units) != bool(initial_position and initial_position.state!=sc.PosState.FLAT):
        raise ValueError('Initial holdings and strategy position disagree')
    if initial_position and initial_units and initial_position.direction!='LONG':
        raise ValueError('V1 initial position must be LONG')
    import backtest as bt
    params={k:cfg[k] for k in bt.EVAL_KEYS if k in cfg}
    pos=deepcopy(initial_position) if initial_position else sc.Position()
    book=Book(start_capital,fee,slippage,deploy,initial_units)
    if initial_position: book.invested_pct=initial_position.bestand_pct
    risk=Risk(book.value(active[0].open))
    equity=[]; signals=[]; feedback=[]; pending=[]; decision=None; months={}
    for i,c in enumerate(cs):
        if c.ts<start_ms:
            pos.last_signal_ts=c.ts
            continue
        risk.observe(book.value(c.open))  # Old inventory bears the gap.
        executed=[]
        for o in pending:
            risk.observe(book.value(c.open))
            executed.append(book.fill(o,c))
            risk.observe(book.value(c.open))
        if decision is not None:
            decision.confirm(pos,executed,book)
            feedback.append(dict(at=c.ts,cash=book.cash,btc=book.units,
                actions=[o['action'] for o in executed],state=pos.state.name,
                buy_rungs=pos.buy_rungs,tp_rungs=pos.tp_rungs,bestand_pct=pos.bestand_pct,
                entry_ref=pos.entry_ref,entry_pct=pos.entry_pct,e42_teil_marke=pos.e42_teil_marke))
        pending=[]
        risk.bar(book,c)
        value=book.value(c.close)
        equity.append(dict(candle_id=c.ts,at=c.ts+STEP,cash=book.cash,btc=book.units,equity=value))
        month=datetime.fromtimestamp((c.ts+STEP-1)/1000,timezone.utc).strftime('%Y-%m')
        months[month]=dict(at=c.ts+STEP,equity=value,close=c.close)
        decision=decision_fn(cs[:i+1],fs[:i+1],pos,params)
        for seq,o in enumerate(decision.candidates):
            signals.append(dict(o,sequence=seq,candle_id=c.ts,knowledge_assumed_at=c.ts+STEP,
                                decision_at=c.ts+STEP,reference_price=o['price']))
        pending=book.schedule(decision.candidates,c.close)
    for o in pending: book.expire(o,cs[-1].close)
    # Rejections/expiry leave only observation state, already applied by decide.
    final=book.value(active[-1].close)
    return dict(model='V1_close_to_next_open_zero_latency',risk_unit='positive_loss_percent',
        start=start_capital,ende=final,rendite_pct=(final/(start_capital+initial_units*active[0].open)-1)*100,
        dd_close_pct=risk.dd[0]*100,dd_intrabar_lower_pct=risk.dd[1]*100,
        dd_intrabar_upper_pct=risk.dd[2]*100,cash=book.cash,btc=book.units,
        reserved_cash=book.reserved_cash,reserved_btc=book.reserved_units,
        fees=sum(e['fee'] for e in book.ledger),fee_pct=fee*100,slippage_pct=slippage*100,
        unfilled_end_of_data=sum(e['status']=='unfilled_end_of_data' for e in book.ledger),
        signals=signals,ledger=book.ledger,equity=equity,month_ends=months,feedback=feedback,
        final_strategy=dict(state=pos.state.name,buy_rungs=pos.buy_rungs,tp_rungs=pos.tp_rungs,
                            entry_ref=pos.entry_ref,entry_pct=pos.entry_pct,bestand_pct=pos.bestand_pct))
