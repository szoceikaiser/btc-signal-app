"""Frozen F02/F12 counterexamples. Read git blobs, never change originals."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = '291588946206333ca58d771f1cc96f261da1a981'
AUDIT = 'ccf2b01c0578346f325261e72445b7375a9ac706'


def worker():
    import backtest as bt
    import strategy_core as sc
    from unittest.mock import patch
    step = 14400000
    short = [dict(ts=0, type='SHORT_1', price=100, tranche_pct=100),
             dict(ts=step, type='SHORT_NACHLEGEN', price=100, tranche_pct=100)]
    cc = [sc.Candle(0,100,100,100,100), sc.Candle(step,100,100,100,100),
          sc.Candle(2*step,100,100,90,90)]
    r = bt.simulate(short, cc, fee=0, start_ms=0)
    assert r['rendite_pct'] == 20
    z = sc.fib_zones(sc.Impulse(sc.Pivot(0,0,80,'L'),sc.Pivot(1,step,160,'H')))
    pos = sc.Position(direction='LONG',state=sc.PosState.FULL,zones=z,
                      retrace_extreme=120,entry_ref=140,entry_pct=100,bestand_pct=100)
    c = sc.Candle(2*step,140,190,90,140)
    with patch.object(sc,'find_pivots',return_value=[]):
        sig = sc.evaluate([c],[],pos,tp_ladder=False,buy_ladder=False,
                          bias_short=False,rest_halten=True)
    assert [s.type.name for s in sig] == ['TEILVERKAUF_1']
    assert sig[0].price == 170 and sig[0].ts == c.ts
    print(json.dumps(dict(commit=sys.argv[2], F02=dict(return_pct=20,
        nominal_exposure_pct=200, unlevered_single_short_return_pct=10),
        F12=dict(old_target=200, same_bar_new_target=170, candle=[140,190,90,140],
                 prior_order_proven=False))))


if __name__ == '__main__':
    if '--worker' in sys.argv:
        worker()
    else:
        for repo, sha in ((ROOT.parent/'audit-work', AUDIT), (ROOT, BASE)):
            with tempfile.TemporaryDirectory() as temp:
                d = Path(temp)
                names = subprocess.check_output(['git','ls-tree','-r','--name-only',sha,'engine'],cwd=repo,text=True).splitlines()
                for name in names:
                    if name.endswith('.py'):
                        out=d/name; out.parent.mkdir(exist_ok=True)
                        out.write_bytes(subprocess.check_output(['git','show',sha+':'+name],cwd=repo))
                subprocess.run([sys.executable,__file__,'--worker',sha],check=True,
                    env={**os.environ,'PYTHONPATH':str(d/'engine'),'PYTHONUTF8':'1'})
