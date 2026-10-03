"""Independent, narrowly copied scenarios F03/F04/F05/F10; no full audit."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

p = argparse.ArgumentParser()
p.add_argument('--baseline-root', type=Path, required=True)
a = p.parse_args()
sys.path.insert(0, str(a.baseline_root.resolve()/'engine'))
import strategy_core as sc
import main

step = 14400000
z = sc.fib_zones(sc.Impulse(sc.Pivot(0, 0, 80, 'L'), sc.Pivot(1, step, 160, 'H')))
pos = sc.Position(direction='LONG', state=sc.PosState.TP1, zones=z,
                  retrace_extreme=100, entry_ref=100, entry_pct=100, bestand_pct=50)
kw = dict(trail_stop=True, tp_ladder=False, buy_ladder=False, rest_halten=True,
          bias_short=False, high_exit='off')
cs = [sc.Candle(2*step, 120, 121, 119, 120)]
low = sc.Pivot(0, 0, 115, 'L')
with patch.object(sc, 'find_pivots', return_value=[low]):
    first = sc.evaluate(cs, [], pos, **kw)
    with patch.object(main, 'find_pivots', return_value=[low]):
        plan = main.positions_plan(cs, [], kw, pos)
    second = sc.evaluate(cs+[sc.Candle(3*step, 120, 121, 109, 110)], [], pos, **kw)
assert not first and not second and pos.state == sc.PosState.TP1
assert plan['stop']['preis'] == 100
z2 = sc.fib_zones(sc.Impulse(sc.Pivot(0, 0, 20, 'L'), sc.Pivot(1, step, 420, 'H')))
pos2 = sc.Position(direction='LONG', state=sc.PosState.T1, zones=z2,
                   retrace_extreme=220, entry_ref=220, entry_pct=25, bestand_pct=25)
sigs = sc.evaluate([sc.Candle(3*step, 185, 190, z2.gp_upper-1, 185)],
                   [sc.FlowPoint(3*step, 0, 0, 1, 0)], pos2,
                   buy_ladder=False, tp_ladder=False, high_exit='off', bias_short=False)
assert [s.type for s in sigs] == [sc.SignalType.KAUF_2]
expected = 75/(25/220+50/172.8)
assert abs(pos2.entry_ref-expected) > 1
restored = main.pos_from_state(main.pos_to_state(sc.Position(widerstand_exits=1)))
assert restored.widerstand_exits == 0
print(json.dumps(dict(result='Four baseline failures reproduced',
    source=str(a.baseline_root), F03=dict(prior_stop=115, close=110, stopped=False),
    F04=dict(signal_reference=pos2.entry_ref, independent_cost_entry=expected),
    F10=dict(engine_stop=115, plan_stop=plan['stop']['preis']),
    F05=dict(before=1, after=restored.widerstand_exits)), indent=2))
