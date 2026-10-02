"""A7 full-exit rounding case found in frozen V015/R0/S0."""

import inventory
import execution_v1 as execution
from strategy_core import Candle


def test_v015_full_exit_clears_real_lots_and_rejects_true_oversell():
    quantities = [0.0010355359558259032, 0.0006283033457108166,
                  0.000837737794281089, 0.0006437209274360484,
                  0.0010728682123934139, 0.0007623844720688509,
                  0.007929369117568677]
    lots = [dict(id=str(i), at=0, fill_price=1., units=q, cost=q,
                 buy_fee=0., kind="base") for i, q in enumerate(quantities)]
    requested = 0.012909919825284829
    try:
        inventory.sell([dict(l) for l in lots], requested + 1e-9,
                       close_cohort=True)
    except ValueError as exc:
        assert str(exc) == "Lot oversell"
    else:
        raise AssertionError("A real oversell must fail")
    disposed, _ = inventory.sell(lots, requested, close_cohort=True)
    assert not lots
    assert abs(disposed - sum(quantities)) < 1e-15


def test_final_partial_sale_uses_exact_flat_inventory():
    aggregate = 0.012909919825284829
    lots = [dict(id="real", at=0, fill_price=100., units=aggregate, cost=aggregate*100,
                 buy_fee=0., kind="base")]
    book = execution.Book(1000., 0., 0., 1., initial_units=aggregate,
                          initial_lots=lots)
    order = dict(id="test", ts=0, sequence=0, action="tp1",
                 type="TEILVERKAUF_1", price=100., amount=aggregate+1.7e-18,
                 requested=aggregate, tranche_pct=40)
    book.fill(order, Candle(execution.STEP, 100., 100., 100., 100.))
    assert book.units == 0 and not book.lots


def test_v005_delayed_exit_respects_prior_peak_rounding():
    total = 0.0019242404444868055
    lots = [dict(id=str(i), at=0, fill_price=100., units=q, cost=q*100,
                 buy_fee=0., kind="base")
            for i, q in enumerate((0.001, total-0.001))]
    disposed, _ = inventory.sell(lots, 0.00192424044448683,
                                 close_cohort=True, rounding_scale=.15)
    assert not lots and abs(disposed-total*100) < 1e-12
