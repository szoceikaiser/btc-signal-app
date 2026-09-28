"""In-memory mutations against reached 3b assertions, no source file writes."""
from pathlib import Path
import json
from unittest.mock import patch
import execution_v1 as v
import strategy_core as sc
import test_execution_v1 as t


def main():
    cases=[]
    source=Path(v.__file__).read_text(encoding='utf-8')
    mutations=[
        ('old_signal_price_instead_of_next_open','price=candle.open*(1+self.slip if buy else 1-self.slip)',
         "price=o['price']*(1+self.slip if buy else 1-self.slip)",t.test_h04_causal_buy_gap_and_separate_reference),
        ('omit_buy_fee','quantity=amount*(1-self.fee)/price','quantity=amount/price',t.test_h10_fee_once_each_fill),
        ('overspend_cash','min(self.cash-self.reserved_cash, self.alloc * o[\'tranche_pct\']/100)',
         "self.alloc * o['tranche_pct']/100",t.test_h16_sequential_cash_reservations_partial_funding),
        ('omit_reservation', 'self.reserved_cash += amount','self.reserved_cash += 0',t.test_h16_sequential_cash_reservations_partial_funding),
        ('no_full_exit_priority','if full:\n', 'if False:\n',t.test_h09_full_exit_suppresses_buy_and_partial_sale),
        ('allow_buy_with_sell',"chosen = sorted(sellable,key=lambda o:(o['type']!='RUECKKAUF_STOP',o['sequence']))",
         "chosen = orders",t.test_h09_partial_exit_suppresses_buy),
        ('wrong_partstop_quantity', 'min(self.units-self.reserved_units, self.rk_units)',
         'self.units-self.reserved_units',t.test_real_e42_partial_stop_precedes_tp_and_preserves_other_lots),
        ('gap_silent_next_existing', "if any(b.ts-a.ts!=STEP for a,b in zip(candles,candles[1:])):",
         'if False:',t.test_gaps_and_duplicates_and_order_rejected),
        ('recover_unclosed_next_open','if c.ts+STEP<=end_ms','if c.ts<=end_ms',t.test_d01_cutoff_cannot_recover_unclosed_next_open),
        ('wrong_risk_pre_fill','risk.bar(book,c)','risk.bar(Book(start_capital,fee,slippage,deploy,initial_units),c)',t.test_h13_open_partial_sale_inventory_during_low),
        ('omit_gap_before_sell','risk.observe(book.value(c.open))', 'pass # gap risk removed',t.test_upward_gap_peak_before_sale_cost_is_preserved),
        ('upper_uses_low_first','(2,(c.high,c.low,c.close))','(2,(c.low,c.high,c.close))',t.test_h03_extremes_and_close_bounds),
        ('reset_peak_every_bar','def bar(self, book, c):','def bar(self, book, c):\n        self.peaks=[book.value(c.open)]*3',t.test_multiple_bars_carry_peaks_not_reset),
        ('no_execution_feedback','decision.confirm(pos,executed,book)','pass # no feedback',t.test_feedback_before_next_decision_f09_reinvestment),
        ('partial_cash_not_reported','if fraction<1:\n','if False:\n',t.test_h16_sequential_cash_reservations_partial_funding),
        ('invent_last_close_fill','book.expire(o,cs[-1].close)',
         "book.fill(o,sc.Candle(o['ts']+STEP,cs[-1].close,cs[-1].close,cs[-1].close,cs[-1].close))",t.test_h11_last_signal_expires_no_phantom_fill),
        ('confirm_rejected_actions','_execution_gate=lambda a: a in accepted',
         '_execution_gate=lambda a: True',t.test_real_rejected_ladder_buy_does_not_consume_rung),
    ]
    for name,old,new,test in mutations:
        test() # reached, green original assertion before mutation
        assert old in source,name
        ns=dict(__name__='execution_v1_mutant',__file__=v.__file__)
        # Register for dataclass module lookup, then patch production globals only
        # during this mutant. Test expectations remain independently fixed.
        import sys,types
        mod=types.ModuleType(ns['__name__']);sys.modules[mod.__name__]=mod
        mod.__dict__.update(ns)
        exec(compile(source.replace(old,new),'<'+name+'>','exec'),mod.__dict__)
        original={k:getattr(v,k) for k in ('Book','Risk','validate','run_v1','decide','Decision')}
        mutated={k:getattr(mod,k) for k in original}
        caught=None
        with patch.multiple(v,**mutated):
            try: test()
            except (AssertionError,ValueError) as e: caught=type(e).__name__
        assert caught,name+' SURVIVED'
        cases.append(dict(name=name,baseline='PASS',detected=caught))

    # Two strategy mutations must reach actual candidates, not a scripted band.
    strategy=Path(sc.__file__).read_text(encoding='utf-8')
    for name,old,new,test in [
        ('consume_rejected_buy_rung','and _allow("buy_ladder")','',t.test_real_rejected_ladder_buy_does_not_consume_rung),
        ('suppress_sell_after_buy_no_flip', 'params = dict(params, bias_short=False, no_flip=False)',
         'params = dict(params, bias_short=False, no_flip=True)',t.test_real_conflict_buy_ladder_and_tp1_before_priority),
    ]:
        test()
        caught=None
        if name.startswith('consume'):
            # A fresh Enum would invalidate comparisons; reuse all sc identities
            # and compile just the modified function into the production globals.
            import inspect
            fn=inspect.getsource(sc._evaluate).replace(old,new)
            ns=dict(sc.__dict__);exec(compile(fn,'<'+name+'>','exec'),ns)
            with patch.object(sc,'_evaluate',ns['_evaluate']):
                try:test()
                except AssertionError as e:caught=type(e).__name__
        else:
            # Explicitly contaminate side-isolated generation with its buy probe:
            # the old no_flip filter then hides an actual simultaneous sell.
            def contaminated(cs,fs,p,params):
                from copy import deepcopy
                probe=deepcopy(p)
                sig=sc.evaluate(cs,fs,probe,**dict(params,no_flip=True,bias_short=False))
                d=original['decide'](cs,fs,p,params)
                allowed={s.type.name for s in sig}
                d.candidates=[o for o in d.candidates if o['type'] in allowed]
                return d
            with patch.object(v,'decide',contaminated):
                try:test()
                except AssertionError as e:caught=type(e).__name__
        assert caught,name+' SURVIVED'
        cases.append(dict(name=name,baseline='PASS',detected=caught))
    print(json.dumps(dict(result='PASS',mutations=len(cases),cases=cases),indent=2))


if __name__=='__main__': main()
