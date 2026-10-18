"""Independent hand cases for the isolated perpetual executor."""
import unittest
import gzip
import json
from decimal import Decimal as D
from pathlib import Path

from derivative_accounting import NotEvaluable
from execution_perp_offline import MissingFunding, PerpBook
import strategy_core as sc


def order(typ, action, pct, at=0):
    return dict(id=f'{typ}:{at}', ts=at, type=typ, action=action,
                tranche_pct=pct, price=100, reason='hand case')


class PerpOfflineCases(unittest.TestCase):
    def test_short_funding_and_close_independent_formula(self):
        b = PerpBook('1000', '0.001')
        opened = b.fill(order('SHORT_1','entry_t1',25), 4, 100, 100)
        self.assertEqual(opened['fraction'],1)
        q = b.qty
        b.payment(4, 5, D('0.2'), 98)
        b.fill(order('SHORT_COVER_REST','stop',100,8), 12, 90, 90)
        self.assertEqual(b.qty,0)
        expected = D(1000)+q*(D(100)-D(90))+q*D('.2')-q*(D(100)+D(90))*D('.001')
        self.assertEqual(b.wallet,expected)
        self.assertEqual(b.state(90)['margin'],0)

    def test_long_pays_positive_funding_and_receives_negative(self):
        b = PerpBook('1000','0')
        b.fill(order('KAUF_1','entry_t1',25),4,100,100)
        q = b.qty
        b.payment(4,5,D('.5'),100)
        b.payment(5,6,D('-.25'),100)
        self.assertEqual(b.wallet,D(1000)-q*D('.25'))
        self.assertEqual(b.funding,-q*D('.25'))

    def test_two_full_shorts_cannot_bind_same_capital(self):
        b = PerpBook('1000','0')
        first = b.fill(order('SHORT_1','entry_t1',100),4,100,100)
        second = b.fill(order('SHORT_2','upgrade_gp',100,4),4,100,100)
        self.assertEqual(first['fraction'],1)
        self.assertEqual(second['fraction'],0)
        self.assertEqual(b.qty,D(10))
        self.assertEqual(b.state(100)['available'],0)

    def test_missing_held_funding_is_not_zero(self):
        b = PerpBook('1000','0')
        b.fill(order('SHORT_1','entry_t1',25),4,100,100)
        with self.assertRaises(MissingFunding) as cm:
            b.payment(4,5,None,100)
        self.assertEqual((cm.exception.rate_at,cm.exception.settle_at),(4,5))

    def test_risk_breach_invalidates_replay(self):
        b = PerpBook('1000','0')
        b.fill(order('SHORT_1','entry_t1',100),4,100,100)
        with self.assertRaises(NotEvaluable):
            b.check(101,5)

    def test_short_gate_declines_before_state_write(self):
        # Use the actual frozen prefix that emitted V035's first short.
        root = Path(__file__).resolve().parents[1]
        doc = root/'docs/audit-nacharbeit-2026-10'
        data = json.loads(gzip.decompress((doc/'A7-flow-modeled-v2.json.gz').read_bytes()))
        design = json.loads((doc/'A7-analysemanifest-v1.json').read_text())
        cfg = next(x['params'] for x in design['rows'] if x['id']=='V035')
        c = [sc.Candle(**x) for x in data['candles'] if x['ts']<=1769457600000]
        f = [sc.FlowPoint(**x) for x in data['flow'] if x['ts']<=1769457600000]
        import backtest as bt
        params = {k:cfg[k] for k in bt.EVAL_KEYS if k in cfg}
        params['muster_cvd'] = 'usd'
        p = sc.Position()
        p.last_signal_ts = c[-2].ts
        sc._evaluate(c,f,p,**params,_execution_gate=lambda _:False)
        self.assertEqual(p.direction,'NONE')


if __name__ == '__main__':
    unittest.main()
