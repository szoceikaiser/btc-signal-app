"""Offline i+2 contract only. No imports from live routing, no persistence format.

Reuse the verified V1 book/decision/risk primitives; a pending package freezes
decisions for one full additional bar. Market prefixes still grow during waiting.
"""
from copy import deepcopy
from datetime import datetime, timezone
from dataclasses import asdict
import math
import execution_v1 as v
import strategy_core as sc
import inventory
from position_state import pos_to_state, pos_from_state


class DelayedBook(v.Book):
    def fill(self, order, candle):
        # Multi-sale subtraction can leave aggregate BTC one ulp below the
        # last reserved amount. Preserve intent; cap only numerical overshoot.
        adjusted = dict(order)
        excess = order['amount']-self.units if order['action'] not in v.BUY_ACTIONS else 0.
        if excess > 0:
            if excess > 8*math.ulp(self.peak_units):
                raise ValueError('Sale exceeds actual inventory')
            adjusted['amount'] = self.units
        accepted = super().fill(adjusted, candle)
        if excess > 0:
            self.ledger[-1]['numerical_btc_cap'] = excess
        return accepted


def run_delayed(candles, flow, cfg, *, start_ms, end_ms, fee=.001,
                slippage=.001, decision_fn=v.decide, checkpoint_at=None, resume_state=None):
    v.require_spot_config(cfg)
    deploy = cfg.get('deploy_pct', 1.)
    if not all(math.isfinite(x) for x in (fee, slippage, deploy)) or not (
            0 <= fee < 1 and 0 <= slippage < 1 and 0 <= deploy <= 1):
        raise ValueError('Invalid costs/allocation')
    cs, fs = v.validate(candles, flow, end_ms)
    active = [c for c in cs if c.ts >= start_ms]
    if not active:
        raise ValueError('No eligible closed trading candles')
    import backtest as bt
    params = {k: cfg[k] for k in bt.EVAL_KEYS if k in cfg}
    pos, book, risk = sc.Position(), DelayedBook(10000., fee, slippage, deploy), v.Risk(10000.)
    book.sync_position(pos)
    pending, decision = [], None
    equity, signals, feedback, waiting, months = [], [], [], [], {}
    context = dict(cfg=deepcopy(cfg), start_ms=start_ms, end_ms=end_ms, fee=fee, slippage=slippage)
    checkpoint, last_done = None, None
    if resume_state is not None:
        required={'version','execution_semantics','context','last_done','prefix','flow_prefix',
                  'book','position','risk','pending','decision','equity','signals','feedback','waiting','months'}
        if (set(resume_state)!=required or resume_state['version']!=1
                or resume_state['execution_semantics']!=v.EXECUTION_SEMANTICS
                or resume_state['context']!=context or decision_fn is not v.decide):
            raise ValueError('Unsupported/inconsistent delayed checkpoint')
        last_done=resume_state['last_done']
        prefix=[asdict(c) for c in cs if c.ts<=last_done]
        if (not prefix or prefix[-1]['ts']!=last_done or prefix!=resume_state['prefix']
                or [asdict(f) for f in fs[:len(prefix)]]!=resume_state['flow_prefix']):
            raise ValueError('Delayed checkpoint input prefix changed')
        book=DelayedBook.from_state(resume_state['book']);pos=pos_from_state(resume_state['position'])
        pending=deepcopy(resume_state['pending'])
        decision=v.Decision.from_state(resume_state['decision']) if resume_state['decision'] else None
        if (bool(pending)!=bool(decision) or (book.fee,book.slip,book.deploy)!=(fee,slippage,deploy)
                or book.lots!=pos.lots):
            raise ValueError('Delayed checkpoint book/decision disagrees')
        if decision and (decision.params!=dict(params,bias_short=False,no_flip=False)
                or [asdict(c) for c in decision.candles]!=prefix[:len(decision.candles)]
                or [asdict(f) for f in decision.flow]!=resume_state['flow_prefix'][:len(decision.flow)]
                or any(o['ts']!=decision.candles[-1].ts for o in pending)
                or not decision.candles[-1].ts<=last_done<decision.candles[-1].ts+2*v.STEP):
            raise ValueError('Delayed pending knowledge changed')
        if {o['id']:book.money.amount(o) for o in pending if o['action'] in v.BUY_ACTIONS}!=book.money.pending:
            raise ValueError('Delayed exact reservations disagree')
        if not math.isclose(math.fsum(o['amount'] for o in pending if o['action'] not in v.BUY_ACTIONS),book.reserved_units,rel_tol=1e-12,abs_tol=0):
            raise ValueError('Delayed BTC reservations disagree')
        risk.peaks,risk.dd=deepcopy(resume_state['risk']['peaks']),deepcopy(resume_state['risk']['dd'])
        if len(risk.peaks)!=3 or len(risk.dd)!=3 or not all(math.isfinite(p) and p>0 and math.isfinite(d) and 0<=d<=1 for p,d in zip(risk.peaks,risk.dd)):
            raise ValueError('Delayed risk state invalid')
        equity,signals,feedback,waiting,months=[deepcopy(resume_state[k]) for k in ('equity','signals','feedback','waiting','months')]
    def capture(i,c):
        if decision_fn is not v.decide:
            raise ValueError('Only native delayed decisions can be checkpointed')
        return dict(version=1,execution_semantics=v.EXECUTION_SEMANTICS,context=context,last_done=c.ts,
            prefix=[asdict(x) for x in cs[:i+1]],flow_prefix=[asdict(x) for x in fs[:i+1]],
            book=book.to_state(),position=pos_to_state(pos),risk=dict(peaks=list(risk.peaks),dd=list(risk.dd)),
            pending=deepcopy(pending),decision=decision.to_state() if decision else None,
            equity=deepcopy(equity),signals=deepcopy(signals),feedback=deepcopy(feedback),waiting=deepcopy(waiting),months=deepcopy(months))
    for i, c in enumerate(cs):
        if last_done is not None and c.ts<=last_done:
            continue
        if c.ts < start_ms:
            pos.last_signal_ts = c.ts
            continue
        risk.observe(book.value(c.open))
        if pending and c.ts == pending[0]['ts'] + 2*v.STEP:
            executed = []
            for order in pending:
                risk.observe(book.value(c.open))
                accepted = book.fill(order, c)
                if accepted is not None:
                    executed.append(accepted)
                risk.observe(book.value(c.open))
            decision.confirm(pos, executed, book)
            feedback.append(dict(at=c.ts, actions=[o['action'] for o in executed],
                cash=book.cash, btc=book.units, position=pos_to_state(pos)))
            pending, decision = [], None
        risk.bar(book, c)
        equity.append(dict(candle_id=c.ts, at=c.ts+v.STEP, cash=book.cash,
            btc=book.units, equity=book.value(c.close),
            cost_basis=inventory.summary(book.lots)['cost'],
            cost_entry=inventory.summary(book.lots)['entry']))
        month = datetime.fromtimestamp((c.ts+v.STEP-1)/1000, timezone.utc).strftime('%Y-%m')
        months[month] = dict(at=c.ts+v.STEP, equity=book.value(c.close), close=c.close)
        if pending:
            # No evaluate/confirm/stop update here. Reserved intent is immutable.
            waiting.append(dict(at=c.ts+v.STEP, pending=deepcopy(pending),
                reserved_cash=book.reserved_cash, reserved_btc=book.reserved_units,
                position=pos_to_state(pos)))
            if checkpoint_at==c.ts:checkpoint=capture(i,c)
            continue
        decision = decision_fn(cs[:i+1], fs[:i+1], pos, params)
        for seq, order in enumerate(decision.candidates):
            signals.append(dict(order, sequence=seq, candle_id=c.ts,
                knowledge_assumed_at=c.ts+v.STEP, decision_at=c.ts+v.STEP,
                reference_price=order['price']))
        pending = book.schedule(decision.candidates, c.close)
        if not pending:
            # Rejections/observations are resolved without postponing another
            # decision. No fills, no phantom strategy transitions.
            decision.confirm(pos, [], book)
            decision = None
        if checkpoint_at==c.ts:checkpoint=capture(i,c)
    for order in pending:
        book.expire(order, active[-1].close)
        book.ledger[-1]['event_at'] = active[-1].ts+v.STEP
    for event in book.ledger:
        event['eligible_fill_at'] = event['candle_id']+2*v.STEP
        if event['reason'] == 'next_open':
            event['reason'] = 'delayed_i_plus_2_open'
    result=dict(model='V1_offline_close_to_i_plus_2_open', next_open_offset=2,
        risk_unit='positive_loss_percent', start=10000., ende=book.value(active[-1].close),
        rendite_pct=(book.value(active[-1].close)/10000-1)*100,
        dd_close_pct=risk.dd[0]*100, dd_intrabar_lower_pct=risk.dd[1]*100,
        dd_intrabar_upper_pct=risk.dd[2]*100, cash=book.cash, btc=book.units,
        reserved_cash=book.reserved_cash, reserved_btc=book.reserved_units,
        fees=float(book.money.fees), money=book.money.state(), execution_semantics=v.EXECUTION_SEMANTICS,
        fee_pct=fee*100, slippage_pct=slippage*100,
        unfilled_end_of_data=sum(e['status']=='unfilled_end_of_data' for e in book.ledger),
        signals=signals, ledger=book.ledger, equity=equity, month_ends=months,
        feedback=feedback, waiting=waiting, lots=deepcopy(book.lots),
        cost_basis=inventory.summary(book.lots)['cost'],
        cost_entry=inventory.summary(book.lots)['entry'], position_state=pos_to_state(pos))
    if checkpoint_at is not None:
        if checkpoint is None:raise ValueError('Delayed checkpoint candle not reached')
        result['checkpoint']=checkpoint
    return result


def resume_delayed(candles, flow, checkpoint):
    context=deepcopy(checkpoint['context']);cfg=context.pop('cfg')
    return run_delayed(candles,flow,cfg,**context,resume_state=checkpoint)
