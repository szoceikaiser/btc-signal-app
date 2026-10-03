"""Isolated causal 1x linear BTC/USD perpetual simulation.

The strategy sees closed 4h candles and confirmed simulated fills only.  This
module has no order transport and does not change the Spot V1 executor.
"""
from copy import deepcopy
from decimal import Decimal as D, ROUND_DOWN

import backtest as bt
import strategy_core as sc
from derivative_accounting import NotEvaluable, number
from execution_v1 import STEP, validate

HOUR = 3_600_000
OPEN_ACTIONS = {'entry_t1', 'entry_gp', 'entry_flush', 'dip', 'buy_ladder',
                'liq_buy', 'upgrade_gp', 'upgrade_full', 'e42_buy'}
FULL_TYPES = {'STOPLOSS', 'VERKAUF_REST', 'SHORT_STOPLOSS', 'SHORT_COVER_REST'}
PART_TYPES = {'TEILVERKAUF_1', 'TEILVERKAUF_2', 'SHORT_TP_1', 'SHORT_TP_2'}
E42_STOP = {'RUECKKAUF_STOP', 'SHORT_RUECKTEST_STOP'}
LOT_STEP = D('0.0001')


class MissingFunding(NotEvaluable):
    def __init__(self, rate_at, settle_at, side, quantity):
        super().__init__(f'Missing published funding rate at {rate_at} for payment {settle_at}')
        self.rate_at, self.settle_at = rate_at, settle_at
        self.side, self.quantity = side, quantity


def side_of(signal):
    return 'short' if signal['type'].startswith('SHORT_') else 'long'


class PerpBook:
    def __init__(self, capital='10000', fee='0.001', deploy='1', enforce_risk=True):
        self.wallet, self.fee, self.deploy = map(number, (capital, fee, deploy))
        if self.wallet <= 0 or not 0 <= self.fee < 1 or not 0 < self.deploy <= 1:
            raise NotEvaluable('Invalid perpetual capital, fee or deployment')
        self.initial = self.wallet
        self.alloc = self.wallet * self.deploy
        self.lots = []
        self.peak_qty = D(0)
        self.invested_pct = D(0)
        self.fees = self.funding = self.realized = D(0)
        self.events = []
        self.enforce_risk = enforce_risk
        self.risk_breaches = []

    @property
    def qty(self):
        return sum((x['qty'] for x in self.lots), D(0))

    @property
    def side(self):
        return self.lots[0]['side'] if self.lots else None

    def state(self, mark):
        mark = number(mark)
        margin = sum((x['qty'] * x['entry'] for x in self.lots), D(0))
        unrealized = sum(((1 if x['side'] == 'long' else -1) * x['qty'] *
                          (mark - x['entry']) for x in self.lots), D(0))
        equity = self.wallet + unrealized
        return dict(wallet=self.wallet, equity=equity, margin=margin,
                    available=self.wallet-margin, gross=self.qty*mark,
                    unrealized=unrealized, qty=self.qty, side=self.side)

    def check(self, mark, at):
        s = self.state(mark)
        if s['equity'] <= 0 or s['available'] < 0 or s['gross'] > s['equity']:
            if self.enforce_risk:
                raise NotEvaluable(f'1x margin/gross risk breached at {at}')
            if not self.risk_breaches or self.risk_breaches[-1]['at'] != at:
                self.risk_breaches.append(dict(at=at, side=self.side,
                    equity=str(s['equity']), margin=str(s['margin']),
                    available=str(s['available']), gross=str(s['gross'])))
        # Independent wallet conservation, including closed-lot P&L.
        if self.wallet != self.initial+self.realized-self.fees+self.funding:
            raise AssertionError('Wallet conservation failed')
        return s

    def payment(self, rate_at, settle_at, absolute_rate, mark):
        before = self.check(mark, settle_at)
        if not self.lots:
            return
        if absolute_rate is None:
            raise MissingFunding(rate_at, settle_at, self.side, self.qty)
        absolute_rate = number(absolute_rate)
        amount = (1 if self.side == 'short' else -1)*self.qty*absolute_rate
        self.wallet += amount
        self.funding += amount
        after = self.check(mark, settle_at)
        self.events.append(dict(kind='funding', at=settle_at, rate_at=rate_at,
                                side=self.side, qty=str(self.qty),
                                absolute_rate=str(absolute_rate), amount=str(amount),
                                before={k: str(v) for k,v in before.items() if isinstance(v,D)},
                                after={k: str(v) for k,v in after.items() if isinstance(v,D)}))

    def fill(self, order, at, price, mark):
        price, mark = number(price), number(mark)
        before = self.check(mark, at)
        opening = order['action'] in OPEN_ACTIONS
        side = side_of(order)
        cost = realized = D(0)
        if opening:
            if self.side not in (None, side):
                raise NotEvaluable('Opposite position cannot be opened before close')
            budget = self.alloc*number(order['tranche_pct'])/100
            qty = (budget/(price*(1+self.fee))).quantize(LOT_STEP, rounding=ROUND_DOWN)
            if qty <= 0:
                status, reason = 'rejected', 'minimum_quantity'
            else:
                cost = qty*price*self.fee
                self.wallet -= cost; self.fees += cost
                lot = dict(id=order['id'], side=side, qty=qty, entry=price,
                           kind='e42' if order['action']=='e42_buy' else 'base')
                self.lots.append(lot)
                try:
                    proposed = self.state(mark)
                    if (proposed['equity'] <= 0 or proposed['available'] < 0
                            or proposed['gross'] > proposed['equity']):
                        raise NotEvaluable('Opening exceeds 1x capacity')
                    self.check(mark, at)
                except NotEvaluable:
                    self.lots.pop(); self.wallet += cost; self.fees -= cost
                    status, reason = 'rejected', 'capital_or_risk'
                else:
                    self.peak_qty = max(self.peak_qty, self.qty)
                    self.invested_pct = min(D(100), self.invested_pct+number(order['tranche_pct']))
                    status, reason = 'filled', 'next_open'
        else:
            if self.side != side or not self.lots:
                status, reason, qty = 'rejected', 'no_matching_inventory', D(0)
            else:
                typ = order['type']
                if typ in FULL_TYPES:
                    qty = self.qty
                elif typ in E42_STOP:
                    qty = sum((x['qty'] for x in self.lots if x['kind']=='e42'), D(0))
                elif typ in PART_TYPES:
                    qty = min(self.qty, (self.peak_qty*D('.4')).quantize(LOT_STEP, rounding=ROUND_DOWN))
                else:
                    qty = min(self.qty, (self.peak_qty*number(order['tranche_pct'])/100).quantize(LOT_STEP, rounding=ROUND_DOWN))
                if qty <= 0:
                    status, reason = 'rejected', 'minimum_quantity'
                else:
                    old_qty, remain = self.qty, qty
                    realized = D(0)
                    for lot in list(self.lots):
                        if typ in E42_STOP and lot['kind'] != 'e42':
                            continue
                        take = min(remain, lot['qty'])
                        realized += (1 if side=='long' else -1)*take*(price-lot['entry'])
                        lot['qty'] -= take; remain -= take
                        if lot['qty'] == 0:
                            self.lots.remove(lot)
                        if remain == 0:
                            break
                    if remain:
                        raise AssertionError('Close allocation incomplete')
                    cost = qty*price*self.fee
                    self.wallet += realized-cost
                    self.realized += realized; self.fees += cost
                    self.invested_pct = D(0) if not self.lots else self.invested_pct*self.qty/old_qty
                    self.check(mark, at)
                    status, reason = 'filled', 'next_open'
        after = self.check(mark, at)
        event = dict(kind='fill', at=at, signal_at=order['ts'],
                     type=order['type'], action=order['action'], side=side,
                     status=status, reason=reason, price=str(price), qty=str(qty),
                     fee=str(cost if status=='filled' else D(0)),
                     realized=str(realized if status=='filled' else D(0)),
                     before={k: str(v) for k,v in before.items() if isinstance(v,D)},
                     after={k: str(v) for k,v in after.items() if isinstance(v,D)})
        self.events.append(event)
        return dict(order, fraction=1. if status=='filled' else 0., event=event)

    def sync(self, pos):
        if self.side is None:
            if pos.direction != 'NONE':
                sc._reset_position(pos)
            return
        pos.direction = self.side.upper()
        pos.bestand_pct = float(self.invested_pct)
        base = [x for x in self.lots if x['kind']=='base']
        if base:
            pos.entry_ref = float(sum((x['qty']*x['entry'] for x in base), D(0)) /
                                  sum((x['qty'] for x in base), D(0)))
        pos.inventory_source = 'simulated_fills'


def candidates(prefix, flow, position, params):
    before = deepcopy(position)
    observed = deepcopy(before)
    sc._evaluate(prefix, flow, observed, **params, _execution_gate=lambda a: False)
    found = []
    for want_open in (True, False):
        probe = deepcopy(before)
        signals = sc._evaluate(prefix, flow, probe, **params,
                               _execution_gate=lambda a: (a in OPEN_ACTIONS)==want_open)
        found.extend(s.to_dict() | {'action': s.execution_action}
                     for s in signals if s.type != sc.SignalType.WARNUNG)
    return before, observed, found


def run(candles, flow, cfg, *, start_ms, end_ms, trade_opens, marks,
        absolute_rates, fee='0.001', capital='10000', deploy='1',
        assumed_missing=None, enforce_risk=True):
    """Return a causal ledger; assumed_missing is diagnostic only and never history."""
    if not cfg.get('bias_short') or cfg.get('instrument', 'linear_btc_usd_perpetual') != 'linear_btc_usd_perpetual':
        raise NotEvaluable('Explicit V035 linear perpetual with short bias required')
    if number(cfg.get('leverage',1)) != 1:
        raise NotEvaluable('Only 1x supported')
    cs, fs = validate(candles, flow, end_ms)
    active = [c for c in cs if c.ts >= start_ms]
    if not active:
        raise NotEvaluable('No closed active candles')
    params = {k:cfg[k] for k in bt.EVAL_KEYS if k in cfg}
    params['no_flip'] = False  # Execution serializes exits before new entries.
    pos, book = sc.Position(), PerpBook(capital, fee, deploy, enforce_risk)
    pending = []
    pending_decision = None
    signals, gap_positions, missing_rate_observations = [], [], []
    assumptions = assumed_missing or {}
    for i,c in enumerate(cs):
        if c.ts < start_ms:
            pos.last_signal_ts = c.ts
            continue
        if c.ts not in trade_opens:
            raise NotEvaluable(f'Missing next-open trade candle at {c.ts}')
        if pending:
            filled = [book.fill(order, c.ts, trade_opens[c.ts], marks[c.ts])
                      for order in pending]
            before, observed, prefix, fprefix = pending_decision
            accepted = {x['action']: x for x in filled if x['fraction']}
            if accepted:
                updated = deepcopy(before)
                sc._evaluate(prefix, fprefix, updated, **params,
                             _execution_gate=lambda a: a in accepted,
                             _execution_sizes={a: x['tranche_pct'] for a,x in accepted.items()})
                pos = updated
            else:
                pos = observed
            book.sync(pos)
        for at in range(c.ts+HOUR, c.ts+STEP+1, HOUR):
            if at not in marks:
                raise NotEvaluable(f'Missing exact hourly mark at {at}')
            rate_at = at-HOUR
            rate = absolute_rates.get(rate_at)
            if rate is None:
                missing_rate_observations.append(dict(rate_at=rate_at, settle_at=at,
                                                      side=book.side, qty=str(book.qty)))
            if rate is None and book.qty and rate_at in assumptions:
                gap_positions.append(dict(rate_at=rate_at, settle_at=at,
                                          side=book.side, qty=str(book.qty),
                                          assumed_absolute_rate=str(assumptions[rate_at])))
                rate = assumptions[rate_at]
            book.payment(rate_at, at, rate, marks[at])
            book.check(marks[at], at)
        before, observed, found = candidates(cs[:i+1], fs[:i+1], pos, params)
        signals.extend(dict(s, decided_at=c.ts+STEP) for s in found)
        exits = [s for s in found if s['action'] not in OPEN_ACTIONS and book.qty]
        opens = [s for s in found if s['action'] in OPEN_ACTIONS and
                 (book.side in (None, side_of(s)))]
        full = [s for s in exits if s['type'] in FULL_TYPES]
        selected = [full[0]] if full else exits if exits else opens
        if selected:
            pending = [dict(s, id=f'perp:{c.ts}:{n}') for n,s in enumerate(selected)]
            pending_decision = (before, observed, cs[:i+1], fs[:i+1])
        else:
            pending = []
            pos = observed
            book.sync(pos)
    return dict(book=book, signals=signals, gap_positions=gap_positions,
                missing_rate_observations=missing_rate_observations,
                end_at=active[-1].ts+STEP, pending_at_end=pending,
                hypothetical=bool(assumptions))
