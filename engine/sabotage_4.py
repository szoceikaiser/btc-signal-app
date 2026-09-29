"""Targeted in-memory faults. Every unchanged case must pass before mutation."""
import inspect
import json
from unittest.mock import patch
import execution_v1 as v
import inventory as inv
import main
import position_state as state
import strategy_core as sc
import test_stage4 as t


def main_test():
    cases = [
        ('reference_instead_of_filled_entry', v, 'Book',
         "pos.entry_ref = base['entry']", 'pass # keep signal anchor',
         t.test_audit_cost_25_at220_50_at17280_real_gp_feedback),
        ('omit_buy_fee_from_cost', v, 'Book', 'units=quantity, cost=amount, fee=charge,',
         'units=quantity, cost=amount-charge, fee=charge,', t.test_fee_slippage_and_reference_price_are_separate),
        ('requested_instead_of_funded_cost', v, 'Book', 'units=quantity, cost=amount, fee=charge,',
         "units=quantity, cost=o['requested'], fee=charge,", t.test_partial_funding_records_only_paid_cost_and_units),
        ('arithmetic_mean_instead_of_cost_per_btc', inv, 'summary',
         'cost/units if units and complete else None',
         "sum(l['fill_price']*l['cost'] for l in selected)/cost if units and complete else None",
         t.test_audit_cost_25_at220_50_at17280_real_gp_feedback),
        ('keep_sold_cost', inv, 'sell', "lot['cost'] *= 1-fraction", 'pass # sold cost remains',
         t.test_proportional_sale_preserves_each_lot_cost_per_coin),
        ('partstop_sells_base_lots', inv, 'sell',
         "if not e42_only or l['kind'] == 'e42'", 'if True',
         t.test_targeted_e42_sale_preserves_base_lot_after_proportional_sale),
        ('e42_changes_main_entry', v, 'Book', "base = inventory.summary(self.lots, 'base')",
         'base = inventory.summary(self.lots)', t.test_e42_does_not_replace_main_stop_basis_with_total_entry),
        ('full_exit_keeps_lot', inv, 'sell', '1. if close_cohort else min(1., units/total)',
         '.99 if close_cohort else min(1., units/total)', t.test_flat_clears_lots_cost_and_next_cycle_uses_new_cash),
        ('drop_tiny_real_lot', inv, 'sell', "l['units'] > 0", "l['units'] > 1e-12",
         t.test_tiny_partial_sale_retains_nonzero_cost),
        ('stop_maximum_forgotten', sc, 'resolve_stop',
         'if long_side and pos.valid_stop is not None and pos.valid_stop >= level:',
         'if False:', t.test_audit_stop115_survives_close110_and_json_restart),
        ('do_not_store_stop', sc, 'resolve_stop', 'if commit and long_side:',
         'if False:', t.test_audit_stop115_survives_close110_and_json_restart),
        ('new_structure_above_close_allowed', sc, 'resolve_stop',
         'p.kind == "L" and p.price < cur.close', 'p.kind == "L"',
         t.test_new_structure_must_be_under_close_but_old_boundary_needs_not),
        ('plan_uses_entry_instead_of_stop', main, 'positions_plan',
         'plan["stop"] = {"preis": stop, "grund": grund}',
         'plan["stop"] = {"preis": pos.entry_ref, "grund": grund}',
         t.test_plan_uses_stored_engine_stop_and_is_read_only),
        ('e41_uses_old_zone_not_valid_stop', sc, '_evaluate',
         'pos, cur, stop_level, long_side, puffer_pct=stop_puffer_pct,',
         'pos, cur, z.invalidation, long_side, puffer_pct=stop_puffer_pct,',
         t.test_original_stop_e41_counter_survives_restart_and_uses_stored_boundary),
        ('forget_widerstand_exits', state, 'pos_to_state',
         "if f.name not in TRANSIENT | {'state', 'zones'}",
         "if f.name not in TRANSIENT | {'state', 'zones', 'widerstand_exits'}",
         t.test_resistance_limit_reached_then_identical_after_restart),
        ('truncate_remaining_fraction', state, 'pos_from_state', 'inventory.validate(pos.lots)',
         'pos.bestand_pct = int(pos.bestand_pct)\n    inventory.validate(pos.lots)',
         t.test_all_position_fields_roundtrip_including_fraction_and_pivot_indices),
        ('forget_pivot_index', state, 'pos_to_state', 'impuls_ende_idx=z.impulse.end.idx',
         'impuls_ende_idx=0', t.test_all_position_fields_roundtrip_including_fraction_and_pivot_indices),
        ('reset_legacy_position', state, 'pos_from_state', "pos.inventory_source = 'signal_reference'",
         "pos.state = PosState.FLAT\n        pos.inventory_source = 'signal_reference'",
         t.test_legacy_active_state_preserves_reference_history_and_dedupe),
        ('restore_without_pending_orders', v, 'run_v1', "pending = deepcopy(resume_state['pending'])",
         'pending = []', t.test_pending_buy_checkpoint_json_restart_exact_parity),
        ('forget_prior_risk_peak', v, 'run_v1',
         "risk.peaks, risk.dd = deepcopy(resume_state['risk']['peaks']), deepcopy(resume_state['risk']['dd'])",
         'pass # forget checkpoint risk', t.test_checkpoint_preserves_earlier_peak_and_drawdown),
        ('forge_live_inventory_label', main, 'positions_plan', '"live_bestand_belegt": False',
         '"live_bestand_belegt": True', t.test_live_reference_plan_cannot_claim_manual_fills),
        ('do_not_arm_after_confirmed_tp', v, 'Decision',
         "if executed and result.direction == 'LONG' and result.zones is not None:",
         'if False:', t.test_confirmed_tp_arms_stop_before_next_close_using_only_known_prefix),
        ('do_not_arm_signal_tp_plan', sc, '_evaluate',
         'if _execution_gate is None and pos.direction == "LONG" and pos.zones is not None:',
         'if False:', t.test_signal_tp_plan_arms_same_stop_for_next_observation),
    ]
    report = []
    for name, module, attr, old, new, test in cases:
        test()  # Reached green production case, before touching the function.
        source = inspect.getsource(getattr(module, attr))
        assert old in source, name+' mutation anchor missing'
        ns = dict(module.__dict__)
        exec(compile(source.replace(old, new), '<'+name+'>', 'exec'), ns)
        mutant = ns[attr]
        from contextlib import ExitStack
        caught = None
        with ExitStack() as stack:
            stack.enter_context(patch.object(module, attr, mutant))
            # Shared imports must see the same mutated codec/resolver.
            if module is state:
                for alias in (t, main, v):
                    stack.enter_context(patch.object(alias, attr, mutant))
            if module is sc and attr == 'resolve_stop':
                stack.enter_context(patch.object(main, attr, mutant))
            try:
                test()
            except (AssertionError, ValueError) as error:
                caught = type(error).__name__
        assert caught, name+' SURVIVED'
        report.append(dict(name=name, reached_baseline='PASS', detected=caught,
                           production=f'{module.__name__}.{attr}', test=test.__name__))
    print(json.dumps(dict(result='PASS', mutations=len(report), cases=report), indent=2))


if __name__ == '__main__':
    main_test()
