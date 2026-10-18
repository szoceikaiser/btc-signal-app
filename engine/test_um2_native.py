"""Native regression migrated from accepted UM2/M5 synthetic hand cases.

Source: um2-kombinationssuche-20261007/test_um2_gates.py and
um2-m5-gegenpruefung-20261007/verify_m5.py (R2). All fixture measurements
are synthetic; aligned()/measured() explicitly supply A2 evidence and UTC grid.
No historical strategy executions and no process strategy substitution.
"""
import unittest
from copy import deepcopy
from dataclasses import replace
import strategy_core as sc
import flow_contract as fc
import test_strategy_core as fixtures
from flow_contract import liquidation_usable
from liquidation_evidence import collect_events
from contextlib import contextmanager
STEP=fc.FOUR_HOURS_MS
def liquidations_usable(p):
    return all(liquidation_usable(p,k) for k in ('long_liq','short_liq'))
def long_usable(p): return liquidation_usable(p,'long_liq')

class NativeProbe:
    # Test harness only: observe native calls, never replace engine functions.
    def __init__(self): self.events=[]
    @contextmanager
    def installed(self):
        with collect_events() as events:
            yield self
        self.events.extend(events)
    def levels(self,*args,**kw):
        with self.installed(): return sc.liq_levels(*args,**kw)
    def cascade(self,*args,**kw):
        with self.installed(): return sc.liq_cascade(*args,**kw)
UM2Adapter=UM2M5Adapter=NativeProbe


def measured(fs, cs=None):
    """Explicit A2 synthetic observations; fixture timestamps become real UTC grid IDs."""
    new = []
    for i,p in enumerate(fs):
        ts = i*STEP if cs is None else cs[i].ts
        fields = ('long_liq','short_liq','oi','oi_btc','spot_cvd','fut_cvd','funding','long_pct')
        meta = {k:fc.direct(ts,ts+STEP,'synthetic_hand_measurement') for k in fields}
        new.append(replace(p,ts=ts,provenance=meta))
    return new

def aligned(cs,fs):
    cs = [replace(c,ts=i*STEP) for i,c in enumerate(cs)]
    return cs,measured(fs,cs)

def unknown(fs,index,coverage='missing',field='long_liq'):
    fs = deepcopy(fs)
    if coverage == 'missing':
        fs[index].provenance[field] = fc.direct(fs[index].ts,fs[index].ts+STEP,'synthetic_unknown',False)
    else:
        fs[index].provenance[field]['coverage'] = coverage
    return fs

def incremental(cs,fs,pos,**params):
    out=[]
    for i in range(len(cs)):
        out += sc.evaluate(cs[:i+1],fs[:i+1],pos,**params)
    return out

def level_fixture(n=181):
    cs=[sc.Candle(i*STEP,100,101,99,100) for i in range(n)]
    fs=measured([sc.FlowPoint(c.ts,1,0,1000,0,long_liq=100000 if i==n-2 else 1000,
                              short_liq=100000 if i==n-2 else 1000) for i,c in enumerate(cs)],cs)
    return cs,fs

class Gates(unittest.TestCase):
    def test_observed_zero_is_known_and_not_missing(self):
            cs,fs=level_fixture(20)
            fs=[replace(f,long_liq=0,short_liq=0) for f in fs]
            self.assertTrue(all(map(liquidations_usable,fs)))
            a=UM2Adapter()
            self.assertEqual(a.levels(cs,fs,'long'),[])
            self.assertFalse(a.cascade(fs,'short'))
            self.assertEqual(a.events,[])

    def test_levels_include_both_sides_and_unknown_warmup(self):
            cs,fs=level_fixture()
            a=UM2Adapter()
            for side in ('long','short'):
                self.assertTrue(a.levels(cs,fs,side))
                for field in ('long_liq','short_liq'):
                    for state in ('missing','stale'):
                        self.assertEqual(a.levels(cs,unknown(fs,2,state,field),side),[])
            self.assertTrue(a.events)

    def test_levels_exact_180_boundary(self):
            cs,fs=level_fixture()
            a=UM2Adapter()
            # With 181 inputs, index 0 is outside, index 1 is the oldest used measurement.
            self.assertTrue(a.levels(cs,unknown(fs,0),'long'))
            self.assertEqual(a.levels(cs,unknown(fs,1),'long'),[])
            self.assertEqual(a.levels(cs,unknown(fs,-1),'long'),[])

    def test_cascade_exact_12_boundary_both_sides(self):
            cs,fs=level_fixture(13)
            fs[-1]=replace(fs[-1],short_liq=1000000)
            a=UM2Adapter()
            self.assertTrue(a.cascade(fs,'short'))
            self.assertTrue(a.cascade(unknown(fs,0),'short'))
            for field in ('long_liq','short_liq'):
                self.assertFalse(a.cascade(unknown(fs,1,field=field),'short'))
                self.assertFalse(a.cascade(unknown(fs,-1,'stale',field),'short'))

    def test_provenance_absent_future_age_and_alignment(self):
            cs,fs=level_fixture(20)
            a=UM2Adapter()
            for key,value in [('available_ts',99*STEP),('sample_ts',99*STEP),('decision_ts',99*STEP),('age_ms',1)]:
                bad=deepcopy(fs)
                bad[5].provenance['long_liq'][key]=value
                self.assertEqual(a.levels(cs,bad,'long'),[])
            bad=deepcopy(fs)
            del bad[5].provenance['long_liq']
            self.assertEqual(a.levels(cs,bad,'long'),[])
            self.assertEqual(a.levels(cs,fs[1:]+[fs[0]],'long'),[])

    def test_consistent_carried_time_is_usable_no_silent_carry_created(self):
            cs,fs=level_fixture(20)
            bad=deepcopy(fs)
            for k in ('long_liq','short_liq'):
                bad[5].provenance[k].update(coverage='carried',sample_ts=4*STEP,available_ts=5*STEP,age_ms=STEP)
            self.assertTrue(liquidations_usable(bad[5]))
            bad[5].provenance['long_liq']['age_ms']=0
            self.assertFalse(liquidations_usable(bad[5]))

    def test_boost_loses_only_additional_entry(self):
            cs,fs=aligned(fixtures._liq_entry_pfad(),fixtures._liq_flow_long(13,2))
            a=UM2Adapter()
            params=dict(pivot_n=2,bias_short=False,tp_ladder=False,buy_ladder=False,liq_entry='boost')
            with a.installed():
                good=incremental(cs,fs,sc.Position(),**params)
                p=sc.Position()
                bad=incremental(cs,unknown(fs,2),p,**params)
            self.assertTrue(any('Konfluenz' in s.reason for s in good))
            self.assertFalse(any('Konfluenz' in s.reason for s in bad))
            self.assertTrue(any(s.type==sc.SignalType.KAUF_1 for s in bad))
            self.assertNotEqual(p.state,sc.PosState.FLAT)
            off_pos=sc.Position()
            with a.installed():
                off=incremental(cs,unknown(fs,2),off_pos,**dict(params,liq_entry='off'))
            self.assertEqual([(s.ts,s.type,s.tranche_pct) for s in bad],[(s.ts,s.type,s.tranche_pct) for s in off])
            self.assertEqual(p.state,off_pos.state)
            self.assertGreater(p.bestand_pct,0)

    def test_filter_missing_confirmation_does_not_become_off(self):
            cs,fs=aligned(fixtures._liq_entry_pfad(),fixtures._liq_flow_long(13,2))
            # Prior level 105 lies within 0.5% of entry low 104.5, while preserving the impulse.
            cs=cs[:-1]
            fs=fs[:-1]
            cs[10]=replace(cs[10],low=105)
            fs=[replace(f,long_liq=9000000 if i==10 else 1000) for i,f in enumerate(fs)]
            params=dict(pivot_n=2,bias_short=False,tp_ladder=False,buy_ladder=False)
            a=UM2Adapter()
            with a.installed():
                good=incremental(cs,fs,sc.Position(),liq_entry='filter',**params)
                bad=incremental(cs,unknown(fs,10),sc.Position(),liq_entry='filter',**params)
                off=incremental(cs,unknown(fs,10),sc.Position(),liq_entry='off',**params)
            self.assertTrue(good)
            self.assertFalse(bad)
            self.assertTrue(off)

    def test_spike_exit_missing_suppressed_protection_stop_kept(self):
            cs=fixtures.zigzag_candles()+[fixtures.c(8,106,106.5,104.5,105.5),fixtures.c(9,105.5,108,105,107.5)]
            cs,fs=aligned(cs,fixtures._liq_flow(len(cs),short_liq_last=5000000))
            params=dict(pivot_n=2,bias_short=False,tp_ladder=False,buy_ladder=False,liq_exit='spike')
            a=UM2Adapter()
            with a.installed():
                good=incremental(cs,fs,sc.Position(),**params)
                bad=incremental(cs,unknown(fs,-1),sc.Position(),**params)
                stop_cs=cs+[sc.Candle(10*STEP,99,100,97,98)]
                stop_fs=measured(fs+[replace(fs[-1],ts=10*STEP)],stop_cs)
                p=sc.Position()
                stopped=incremental(stop_cs,unknown(stop_fs,-1),p,**params)
            self.assertTrue(any('Teilgewinn an Liquidationen' in s.reason for s in good))
            self.assertFalse(any('Teilgewinn an Liquidationen' in s.reason for s in bad))
            self.assertTrue(any(s.type==sc.SignalType.STOPLOSS for s in stopped))
            self.assertEqual(p.state,sc.PosState.FLAT)

    def test_unknown_cascade_does_not_disable_independent_zone(self):
            cs,fs=level_fixture(181)
            # Current unknown is excluded from previous-bar zone history, included in cascade.
            now_c=sc.Candle(181*STEP,100,101,99,100)
            now_f=replace(fs[-1],ts=now_c.ts,provenance={k:fc.direct(now_c.ts,now_c.ts+STEP,'unknown',False) for k in ('long_liq','short_liq')})
            a=UM2Adapter()
            self.assertFalse(a.cascade(fs+[now_f],'short'))
            self.assertTrue(a.levels((cs+[now_c])[:-1],(fs+[now_f])[:-1],'short'))

    def test_no_position_reset_and_fresh_adapter_state(self):
            cs,fs=level_fixture()
            p=sc.Position(state=sc.PosState.T1,direction='LONG',bestand_pct=25,entry_ref=100,last_signal_ts=5*STEP)
            prior=deepcopy(p.__dict__)
            a=UM2Adapter()
            with a.installed():
                a.levels(cs,unknown(fs,1),'long')
            self.assertEqual(p.__dict__,prior)
            # A new process/adapter gives the same suppression, without reinitializing any book.
            b=UM2Adapter()
            self.assertEqual(b.levels(cs,unknown(fs,1),'long'),[])
            self.assertEqual(a.events,b.events)

    def test_independent_oi_or_price_rules_not_blanket_neutralized(self):
            cs,fs=aligned(*fixtures.e13_szenario(spot_faellt=False,oi_steigt=False))
            missing=unknown(fs,-1)
            a=UM2Adapter()
            with a.installed():
                self.assertEqual(sc.classify_pattern(cs,missing),sc.classify_pattern(cs,fs))

class M5Tests(unittest.TestCase):
    def setUp(self):
            self.cs, self.fs = aligned(*fixtures.e13_szenario())
            self.a = UM2M5Adapter()

    def pattern(self, fs, **kw):
            with self.a.installed():
                return sc.classify_pattern(self.cs, fs, **kw)

    def test_zero_and_small_measured_liquidations_still_m5(self):
            for value in (0, 1000):
                fs = [replace(f, long_liq=value) for f in self.fs]
                self.assertEqual(self.pattern(fs), sc.Pattern.UNGESUNDER_ABVERKAUF)
            self.assertEqual(self.a.events, [])

    def test_missing_stale_at_each_used_position_cannot_confirm_or_hold(self):
            for index in range(len(self.fs)-12, len(self.fs)):
                for coverage in ('missing', 'stale'):
                    fs = unknown(self.fs, index, coverage)
                    p = self.pattern(fs)
                    self.assertEqual(p, sc.Pattern.NEUTRAL)
                    self.assertFalse(sc.confirm_ok(p, fs, True, muster5_entry=True))
                    self.assertFalse(sc.muster5_haelt_zurueck('alle', p, 'LONG', True))

    def test_short_unknown_does_not_invalidate_long_evidence(self):
            for state in ('missing', 'stale'):
                fs = unknown(self.fs, -1, state, 'short_liq')
                self.assertEqual(self.pattern(fs), sc.Pattern.UNGESUNDER_ABVERKAUF)

    def test_unknown_outside_window_ignored_and_custom_window_respected(self):
            self.assertEqual(self.pattern(unknown(self.fs, -13)), sc.Pattern.UNGESUNDER_ABVERKAUF)
            self.assertEqual(self.pattern(unknown(self.fs, -12)), sc.Pattern.NEUTRAL)
            self.assertEqual(self.pattern(unknown(self.fs, -13), window=13), sc.Pattern.NEUTRAL)
            with self.a.installed():
                self.assertEqual(sc.classify_pattern(self.cs[:11], self.fs[:11]), sc.Pattern.NEUTRAL)

    def test_spike_exact_threshold_unchanged(self):
            fs = [replace(f, long_liq=1000) for f in self.fs]
            for last, expected in ((2999, sc.Pattern.UNGESUNDER_ABVERKAUF), (3000, sc.Pattern.NEUTRAL), (3001, sc.Pattern.NEUTRAL)):
                self.assertEqual(self.pattern(fs[:-1] + [replace(fs[-1], long_liq=last)]), expected)
            self.assertEqual(self.pattern(fs[:-1]+[replace(fs[-1], long_liq=3000)], liq_spike_mult=4), sc.Pattern.UNGESUNDER_ABVERKAUF)

    def test_no_metadata_or_bad_time_or_values_rejected(self):
            for value in (float('nan'), float('inf'), -1):
                self.assertEqual(self.pattern(self.fs[:-1]+[replace(self.fs[-1], long_liq=value)]), sc.Pattern.NEUTRAL)
            for key, value in [('available_ts', 999*STEP), ('sample_ts', 999*STEP), ('decision_ts', 0), ('age_ms', 1)]:
                fs = deepcopy(self.fs)
                fs[-1].provenance['long_liq'][key] = value
                self.assertEqual(self.pattern(fs), sc.Pattern.NEUTRAL)
            fs = deepcopy(self.fs)
            del fs[-1].provenance['long_liq']
            self.assertEqual(self.pattern(fs), sc.Pattern.NEUTRAL)

    def test_consistent_carried_long_is_usable(self):
            fs = deepcopy(self.fs)
            t = fs[-1].ts
            fs[-1].provenance['long_liq'].update(coverage='carried', sample_ts=t-STEP, available_ts=t, age_ms=STEP)
            self.assertTrue(long_usable(fs[-1]))
            self.assertEqual(self.pattern(fs), sc.Pattern.UNGESUNDER_ABVERKAUF)

    def test_independent_patterns_not_blanket_neutralized(self):
            for kind in ('m4', 'm3', 'm1'):
                cs = [replace(c, close=100 + (-7 if kind=='m4' else 3)*i/11) for i,c in enumerate(self.cs[-12:])]
                fs = [replace(f, spot_cvd=([100]*9+[95,100,106])[i] if kind=='m4' else 100+i*10,
                              oi=1000+i*(-8 if kind=='m4' else -5 if kind=='m3' else 2), funding=0)
                      for i,f in enumerate(self.fs[-12:])]
                fs = unknown(unknown(fs, -1), -1, field='short_liq')
                expected = {'m4':sc.Pattern.CAPITULATION_RESET, 'm3':sc.Pattern.SHORT_COVERING, 'm1':sc.Pattern.GESUNDER_TREND}[kind]
                with self.a.installed():
                    self.assertEqual(sc.classify_pattern(cs, fs), expected)

    def test_evaluate_uses_patched_classifier_for_actual_entry(self):
            params = dict(pivot_n=2, bias_short=False, confirm_t1=True, muster5_entry=True)
            bad = unknown(self.fs, -1)
            with self.a.installed():
                good = incremental(self.cs, self.fs, sc.Position(), **params)
                blocked = incremental(self.cs, bad, sc.Position(), **params)
            self.assertTrue(any(s.type==sc.SignalType.KAUF_1 for s in good))
            self.assertFalse(any(s.type==sc.SignalType.KAUF_1 for s in blocked))

def test_native_accepted_gate_countercases():
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Gates),
                             unittest.defaultTestLoader.loadTestsFromTestCase(M5Tests)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
if __name__=='__main__': test_native_accepted_gate_countercases()

