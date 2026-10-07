"""Explicit synthetic liquidation observations for numerical hand-built tests.

No producer/runtime imports this module. Values including default zeros in these
chosen fixtures are stipulated synthetic observations, never archive substitutes.
Unknown-data tests construct raw FlowPoint or set missing/stale evidence explicitly.
"""
from strategy_core import FlowPoint
from flow_contract import direct, FOUR_HOURS_MS


def synthetic_liquidation_point(*args, **kwargs):
    point = FlowPoint(*args, **kwargs)
    if point.provenance:
        raise ValueError('Use explicit original provenance; do not relabel a point')
    point.provenance.update({field: direct(point.ts, point.ts + FOUR_HOURS_MS,
        'synthetic_liquidation_fixture') for field in ('long_liq', 'short_liq')})
    return point
