"""Offline i+2 contract only. No imports from live routing, no persistence format.

Reuse the verified V1 book/decision/risk primitives; a pending package freezes
decisions for one full additional bar. Market prefixes still grow during waiting.
"""
from copy import deepcopy
from datetime import datetime, timezone
import math
import execution_v1 as v
import strategy_core as sc
import inventory
from position_state import pos_to_state


def run_delayed(candles, flow, cfg, *, start_ms, end_ms, fee=.001,
                slippage=.001, decision_fn=v.decide):
    if cfg.get('bias_short', False):
        raise ValueError('Long/Spot only')
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
    pos, book, risk = sc.Position(), v.Book(10000., fee, slippage, deploy), v.Risk(10000.)
    book.sync_position(pos)
    pending, decision = [], None
    equity, signals, feedback, waiting, months = [], [], [], [], {}
    for i, c in enumerate(cs):
        if c.ts < start_ms:
            pos.last_signal_ts = c.ts
            continue
        risk.observe(book.value(c.open))
        if pending and c.ts == pending[0]['ts'] + 2*v.STEP:
            executed = []
            for order in pending:
                risk.observe(book.value(c.open))
                executed.append(book.fill(order, c))
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
    for order in pending:
        book.expire(order, active[-1].close)
        book.ledger[-1]['event_at'] = active[-1].ts+v.STEP
    for event in book.ledger:
        event['eligible_fill_at'] = event['candle_id']+2*v.STEP
        if event['reason'] == 'next_open':
            event['reason'] = 'delayed_i_plus_2_open'
    return dict(model='V1_offline_close_to_i_plus_2_open', next_open_offset=2,
        risk_unit='positive_loss_percent', start=10000., ende=book.value(active[-1].close),
        rendite_pct=(book.value(active[-1].close)/10000-1)*100,
        dd_close_pct=risk.dd[0]*100, dd_intrabar_lower_pct=risk.dd[1]*100,
        dd_intrabar_upper_pct=risk.dd[2]*100, cash=book.cash, btc=book.units,
        reserved_cash=book.reserved_cash, reserved_btc=book.reserved_units,
        fees=sum(e['fee'] for e in book.ledger), fee_pct=fee*100, slippage_pct=slippage*100,
        unfilled_end_of_data=sum(e['status']=='unfilled_end_of_data' for e in book.ledger),
        signals=signals, ledger=book.ledger, equity=equity, month_ends=months,
        feedback=feedback, waiting=waiting, lots=deepcopy(book.lots),
        cost_basis=inventory.summary(book.lots)['cost'],
        cost_entry=inventory.summary(book.lots)['entry'], position_state=pos_to_state(pos))
