"""Boundaries and archive orchestration; no provider calls or live state."""
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import rolling_backtest as r
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))
import backtest as bt


class RollingBacktestTests(unittest.TestCase):
    def test_365_days_closed_utc_including_exact_boundary(self):
        for now in (400 * r.DAY, 400 * r.DAY + 1234567, 401 * r.DAY - 1):
            load, start, end = r.window(now)
            self.assertLessEqual(end, now)
            self.assertLess(now - end, r.STEP)
            self.assertEqual(end - start, 365 * r.DAY)
            self.assertEqual(start - load, 200 * r.STEP)

    def test_archived_values_survive_fresh_retention_limit(self):
        old = {'oi': {0: 10, r.STEP: 20}, 'liq': {0: [0, 0]}, 'fut': {0: -2}, 'ls': {0: 55}}
        fresh = {'oi': {r.STEP: 21, 2*r.STEP: 30, 3*r.STEP: 40}}
        merged, coverage = r.merge(old, fresh, 0, 3*r.STEP)
        self.assertEqual(merged['oi'], {0: 10, r.STEP: 21, 2*r.STEP: 30})
        self.assertEqual(merged['liq'], {0: (0, 0)})
        self.assertEqual(coverage['oi']['archive_only'], 1)
        self.assertEqual(merged['fut'], {0: -2})
        self.assertEqual(merged['ls'], {0: 55})

    def test_no_old_or_open_or_future_archive_observations(self):
        self.assertEqual(r.series({0: 1, r.STEP: 2, 2*r.STEP: 3}, r.STEP, 2*r.STEP), {r.STEP: 2})

    def test_malformed_archive_fails_instead_of_silent_neutral(self):
        for bad in ({1: 4}, {0: float('nan')}, {0: True}):
            with self.assertRaises(ValueError):
                r.series(bad, 0, r.STEP)
        for value in ([-1, 0], [0], 0):
            archive = {field: {} for field in r.FIELDS}
            archive['liq'] = {0: value}
            with self.assertRaises(ValueError):
                r.merge(archive, {}, 0, r.STEP)

    def test_price_gap_duplicate_or_missing_latest_refuses_report(self):
        row = lambda t: [t, 10, 12, 9, 11, 0, 0, 100, 0, 0, 60]
        good = [row(i*r.STEP) for i in range(3)]
        self.assertEqual(r.validate_prices(good + [row(3*r.STEP)], 0, 0, 3*r.STEP), good)
        for bad in (good[:-1], good[1:], good[:1] + good[2:], good + good[:1]):
            with self.assertRaises(ValueError):
                r.validate_prices(bad, 0, 0, 3*r.STEP)

    def test_missing_liquidation_stays_missing_but_measured_zero_is_observed(self):
        raw = [[0, 10, 12, 9, 11, 0, 0, 100, 0, 0, 60],
               [r.STEP, 10, 12, 9, 11, 0, 0, 100, 0, 0, 60]]
        _, flow = bt.build_series(raw, [], {0: 100}, {0: (0, 0)}, {}, {}, end_ms=2*r.STEP)
        self.assertEqual(flow[0].provenance['long_liq']['coverage'], 'observed')
        self.assertEqual(flow[1].provenance['long_liq']['coverage'], 'missing')

    def test_execute_uses_archive_all_fields_and_writes_only_report(self):
        now = 400*r.DAY + 1234
        load, start, end = r.window(now)
        prices = [[t, 10, 12, 9, 11, 0, 0, 100, 0, 0, 60] for t in range(load, end, r.STEP)]
        params = json.loads((Path(__file__).resolve().parents[1] /
             'docs/um2-engine-integration/candidates/C05-UM2.inactive.json').read_bytes())['params']
        archive = {field: {} for field in r.FIELDS}
        for field, value in zip(r.FIELDS, (100, [0, 0], -1, 55)):
            archive[field] = {str(start): value}
        result = dict(ende=10000., cash=10000., btc=0., reserved_cash=0., reserved_btc=0.,
                      rendite_pct=0., fees=0.)
        fake = types.SimpleNamespace(fetch_candles_range=lambda a,b: prices,
            fetch_funding_8h=lambda: [], build_series=bt.build_series,
            run_execution=lambda cs,fs,cfg,**kw: result)
        contract = types.SimpleNamespace(effective_config=lambda v:v, digest=lambda v:r.CONFIG)
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            root = Path(tmp)
            self.assertEqual(root.resolve().parent, Path.cwd().resolve())
            candidate = root/'docs/um2-engine-integration/candidates/C05-UM2.inactive.json'
            candidate.parent.mkdir(parents=True)
            candidate.write_text(json.dumps({'params': params}))
            archive_path=root/'archive.json'; archive_path.write_text(json.dumps(archive))
            before=archive_path.read_bytes()
            with patch.object(r, 'bind_core', return_value=(fake,contract)), patch.dict(
                    'os.environ', {'REVIEWED_CONFIG_JSON':json.dumps(params),'COINALYZE_API_KEY':''}):
                r.execute(root, archive_path, root/'report', now_ms=now)
            report=json.loads((root/'report/report.json').read_bytes())
            self.assertEqual(report['end_ms'], end)
            self.assertLessEqual(end-report['start_ms'],365*r.DAY)
            self.assertEqual(archive_path.read_bytes(),before)
            self.assertEqual(set(report['archive_coverage']),set(r.FIELDS))
            self.assertTrue(all(c['archive_only']==1 for c in report['archive_coverage'].values()))
            inputs=json.loads((root/'report/inputs.json').read_bytes())
            self.assertEqual(inputs['coinalyze']['liq'][str(start)],[0,0])
            self.assertIn('mit Messlücken',(root/'report/BACKTEST.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
