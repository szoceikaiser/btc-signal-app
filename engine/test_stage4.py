"""Stage 4: independent cost arithmetic, reached stop branches and JSON restart."""
from copy import deepcopy
from dataclasses import asdict, fields
from fractions import Fraction as F
import json
import math
from unittest.mock import patch

import execution_v1 as v
import inventory
import main
import strategy_core as sc
from position_state import pos_from_state, pos_to_state
from test_execution_v1 import bars, entry_fixture, position


def near(a, b):
    assert a is not None and math.isclose(a, float(b), rel_tol=2e-12, abs_tol=1e-12), (a, b)


def json_copy(d):
    return json.loads(json.dumps(d, allow_nan=False))


def trade(book, action, typ, price, pct, step):
    orders = book.schedule([dict(ts=step*v.STEP, action=action, type=typ,
        price=999., tranche_pct=pct, reason='independent cost case')], price)
    assert len(orders) == 1, 'Must reach a funded production fill'
    done = book.fill(orders[0], sc.Candle((step+1)*v.STEP, price, price, price, price))
    assert book.ledger[-1]['status'] in ('filled', 'rejected')
    return done


def test_audit_cost_25_at220_50_at17280_real_gp_feedback():
    book = v.Book(100, 0, 0, 1)
    trade(book, 'entry_t1', 'KAUF_1', 220, 25, 0)
    z = sc.fib_zones(sc.Impulse(sc.Pivot(0, 0, 20, 'L'), sc.Pivot(1, v.STEP, 420, 'H')))
    pos = sc.Position(direction='LONG', state=sc.PosState.T1, zones=z,
                      retrace_extreme=220, entry_ref=220, entry_pct=25, bestand_pct=25)
    book.sync_position(pos)
    cs = [sc.Candle(2*v.STEP, 185, 190, z.gp_upper-1, 185)]
    fs = [sc.FlowPoint(2*v.STEP, 0, 0, 1, 0)]
    d = v.decide(cs, fs, pos, dict(buy_ladder=False, tp_ladder=False, high_exit='off'))
    assert [o['action'] for o in d.candidates] == ['upgrade_gp']
    orders = book.schedule(d.candidates, 185)
    done = [book.fill(o, sc.Candle(3*v.STEP, 172.8, 180, 170, 175)) for o in orders]
    d.confirm(pos, done, book)
    expected = F(75)/(F(25, 220)+F(50)/F('172.8'))
    near(pos.entry_ref, expected)
    near(book.snapshot(175)['cost_entry'], expected)
    near(sum(l['cost'] for l in pos.lots), 75)
    assert pos.inventory_source == 'simulated_fills' and pos.state == sc.PosState.CORE
    assert abs(pos.entry_ref-(220*25+172.8*50)/75) > 2


def test_fee_slippage_and_reference_price_are_separate():
    book = v.Book(100, .001, .005, 1)
    trade(book, 'entry_t1', 'KAUF_1', 220, 25, 0)
    trade(book, 'upgrade_gp', 'KAUF_2', 172.8, 50, 1)
    expected_q = F(25)*F('0.999')/(F(220)*F('1.005')) + F(50)*F('0.999')/(F('172.8')*F('1.005'))
    near(book.units, expected_q)
    near(book.snapshot(200)['cost_entry'], F(75)/expected_q)
    near(sum(l['buy_fee'] for l in book.lots), F('0.075'))
    assert all(l['fill_price'] != 999 for l in book.lots)
    near(book.cash, 25)


def test_partial_funding_records_only_paid_cost_and_units():
    book = v.Book(100, .001, 0, 1)
    trade(book, 'entry_t1', 'KAUF_1', 200, 75, 0)
    done = trade(book, 'upgrade_gp', 'KAUF_2', 100, 50, 1)
    assert done['fraction'] == .5
    assert book.ledger[-1]['reason'] == 'cash_shortfall'
    near(book.ledger[-1]['rejected_budget'], 25)
    near(book.cash, 0)
    near(sum(l['cost'] for l in book.lots), 100)
    near(book.units, F(75)*F('0.999')/200+F(25)*F('0.999')/100)


def mixed_book(fee=0):
    book = v.Book(200, fee, 0, 1)
    trade(book, 'entry_t1', 'KAUF_1', 100, 50, 0)  # B100, 1 BTC before fees
    trade(book, 'e42_buy', 'RUECKKAUF', 200, 25, 1)  # B50, .25 BTC
    return book


def test_proportional_sale_preserves_each_lot_cost_per_coin():
    book = mixed_book()
    before = deepcopy(book.lots)
    trade(book, 'tp1', 'TEILVERKAUF_1', 180, 40, 2)
    for old, new in zip(before, book.lots):
        near(new['units'], F(str(old['units']))*F('0.6'))
        near(new['cost'], F(str(old['cost']))*F('0.6'))
    near(book.units, F('0.75'))
    near(book.rk_units, F('0.15'))
    near(book.snapshot(180)['cost_entry'], 120)
    near(book.ledger[-1]['disposed_cost'], 60)
    near(book.ledger[-1]['realized_pnl'], 30)


def test_targeted_e42_sale_preserves_base_lot_after_proportional_sale():
    book = mixed_book()
    trade(book, 'tp1', 'TEILVERKAUF_1', 180, 40, 2)
    base = deepcopy(book.lots[0])
    trade(book, 'part_stop', 'RUECKKAUF_STOP', 150, 25, 3)
    assert book.lots == [base]
    near(book.units, F('0.6'))
    near(book.snapshot(150)['cost_entry'], 100)
    near(book.ledger[-1]['disposed_cost'], 30)
    near(book.ledger[-1]['realized_pnl'], F('-7.5'))
    assert book.rk_units == 0


def test_e42_does_not_replace_main_stop_basis_with_total_entry():
    book = mixed_book()
    p = position(sc.PosState.TP1)
    book.sync_position(p)
    near(p.entry_ref, 100)
    near(inventory.summary(p.lots)['entry'], 120)
    level, reason = sc.resolve_stop(p, sc.Candle(3*v.STEP, 140, 140, 140, 140), [], trail_stop=True, commit=True)
    assert level == 100 and reason == 'Einstand (nachgezogen)'
    plan = main.positions_plan([sc.Candle(3*v.STEP, 140, 140, 140, 140)], [], {'trail_stop': True}, p)
    near(plan['einstand'], 120)
    near(plan['basis_einstand'], 100)
    assert plan['stop']['preis'] == 100 and plan['live_bestand_belegt'] is False


def test_sale_fee_does_not_change_remaining_acquisition_cost():
    book = mixed_book(.001)
    before = deepcopy(book.lots)
    trade(book, 'tp1', 'TEILVERKAUF_1', 180, 40, 2)
    for old, new in zip(before, book.lots):
        near(new['cost'], old['cost']*.6)
        near(new['buy_fee'], old['buy_fee']*.6)
    e = book.ledger[-1]
    near(e['disposed_cost'], 60)
    near(e['fee'], F('0.4995')*180*F('0.001'))
    near(e['realized_pnl'], F('0.4995')*180*F('0.999')-60)


def test_flat_clears_lots_cost_and_next_cycle_uses_new_cash():
    book = mixed_book()
    trade(book, 'stop', 'STOPLOSS', 150, 100, 2)
    assert book.units == 0 and book.lots == [] and book.rk_units == 0
    assert book.snapshot(150)['cost_entry'] is None and book.snapshot(150)['cost_basis'] == 0
    cash = book.cash
    trade(book, 'entry_t1', 'KAUF_1', 200, 25, 3)
    near(book.lots[0]['cost'], cash*.25)
    near(book.peak_units, cash*.25/200)
    assert len(book.lots) == 1


def test_tiny_real_lot_is_not_dust_and_full_sale_closes_exactly():
    book = v.Book(1e-16, .001, 0, 1)
    trade(book, 'entry_t1', 'KAUF_1', 1e5, 100, 0)
    assert 0 < book.units < 1e-20 and book.lots[0]['cost'] == 1e-16
    trade(book, 'stop', 'STOPLOSS', 1e5, 100, 1)
    assert book.units == 0 and book.lots == []


def test_unknown_initial_cost_is_never_invented_from_signal_reference():
    book = v.Book(100, 0, 0, 1, 2)
    p = position()
    book.sync_position(p)
    assert p.entry_ref == 100 and not p.cost_basis_complete
    assert inventory.summary(p.lots)['entry'] is None
    trade(book, 'entry_t1', 'KAUF_1', 200, 25, 0)
    assert book.snapshot(200)['cost_basis'] is None


def stop_fixture():
    p = position(sc.PosState.TP1)
    p.retrace_extreme, p.bestand_pct = 100, 50
    cs = [sc.Candle(2*v.STEP, 120, 121, 119, 120)]
    kw = dict(trail_stop=True, tp_ladder=False, buy_ladder=False, rest_halten=True,
              bias_short=False, high_exit='off')
    return p, cs, kw


def test_audit_stop115_survives_close110_and_json_restart():
    p, cs, kw = stop_fixture()
    with patch.object(sc, 'find_pivots', return_value=[sc.Pivot(0, 0, 115, 'L')]):
        first = sc.evaluate(cs, [], p, **kw)
    assert first == [] and p.valid_stop == 115 and p.valid_stop_reason == 'Struktur-Tief'
    p = pos_from_state(json_copy(pos_to_state(p)))
    cs.append(sc.Candle(3*v.STEP, 120, 121, 109, 110))
    # The pivot vanished from the rolling input; stop must still trigger.
    with patch.object(sc, 'find_pivots', return_value=[]):
        second = sc.evaluate(cs, [], p, **kw)
    assert [s.type for s in second] == [sc.SignalType.STOPLOSS]
    assert '115' in second[0].reason and p.state == sc.PosState.FLAT
    assert p.valid_stop is None


def test_plan_uses_stored_engine_stop_and_is_read_only():
    p, cs, kw = stop_fixture()
    with patch.object(sc, 'find_pivots', return_value=[sc.Pivot(0, 0, 115, 'L')]):
        sc.evaluate(cs, [], p, **kw)
    assert p.valid_stop == 115
    before = deepcopy(p)
    with patch.object(main, 'find_pivots', return_value=[]):
        plan = main.positions_plan(cs, [], kw, p)
    assert plan['stop'] == {'preis': 115, 'grund': 'Struktur-Tief'}
    assert p == before


def test_stop_does_not_fall_after_lower_entry_zone_or_switch():
    p, cs, kw = stop_fixture()
    sc.resolve_stop(p, cs[-1], [sc.Pivot(0, 0, 115, 'L')], trail_stop=True, commit=True)
    p.entry_ref = 90
    p.zones = sc.fib_zones(sc.Impulse(sc.Pivot(0, 0, 60, 'L'), sc.Pivot(1, 1, 140, 'H')))
    p.state = sc.PosState.CORE  # restart with a remaining position
    assert sc.resolve_stop(p, cs[-1], [], trail_stop=False, commit=True) == (115, 'Struktur-Tief')
    sc._reset_position(p)
    assert p.valid_stop is None and p.valid_stop_reason == ''


def test_new_structure_must_be_under_close_but_old_boundary_needs_not():
    p, cs, kw = stop_fixture()
    assert sc.resolve_stop(p, cs[-1], [sc.Pivot(0, 0, 125, 'L')], trail_stop=True, commit=True)[0] == 100
    p.valid_stop, p.valid_stop_reason = 125, 'Struktur-Tief'
    assert sc.resolve_stop(p, cs[-1], [], trail_stop=True, commit=True)[0] == 125


def test_trailing_stop_does_not_get_e41_grace():
    p, cs, kw = stop_fixture()
    p.valid_stop, p.valid_stop_reason = 115, 'Struktur-Tief'
    cs.append(sc.Candle(3*v.STEP, 116, 116, 109, 110))
    with patch.object(sc, 'find_pivots', return_value=[]):
        sigs = sc.evaluate(cs, [], p, **dict(kw, stop_rueckeroberung=3))
    assert [s.type for s in sigs] == [sc.SignalType.STOPLOSS]


def test_original_stop_e41_counter_survives_restart_and_uses_stored_boundary():
    p = position()
    p.valid_stop, p.valid_stop_reason = 85, 'Invalidierung'
    cs = [sc.Candle(2*v.STEP, 86, 86, 84, 84)]
    kw = dict(trail_stop=False, stop_rueckeroberung=1, buy_ladder=False, tp_ladder=False)
    with patch.object(sc, 'find_pivots', return_value=[]):
        assert sc.evaluate(cs, [], p, **kw) == []
    assert p.stop_wartet == 1 and p.stop_wartet_inv == 85
    p = pos_from_state(json_copy(pos_to_state(p)))
    cs.append(sc.Candle(3*v.STEP, 84, 85, 84, 84))
    with patch.object(sc, 'find_pivots', return_value=[]):
        sigs = sc.evaluate(cs, [], p, **kw)
    assert [s.type for s in sigs] == [sc.SignalType.STOPLOSS]


def test_all_position_fields_roundtrip_including_fraction_and_pivot_indices():
    p = position(sc.PosState.TP1, widerstand_exits=1, stop_wartet=1, stop_wartet_inv=80,
        stop_geprueft=82, e42_marke=130, e42_richtung='LONG', e42_start_ts=1,
        e42_ausbruch_ts=2, e42_gekauft=125, e42_teil_marke=130, e42_teil_wartet=1,
        e42_teil_wartet_inv=130, e42_teil_geprueft=128, valid_stop=115,
        valid_stop_reason='Struktur-Tief', last_stop_ts=99, liq_exits=2, high_exits=3,
        liq_entries=4, buy_rungs=5, tp_rungs=6, dip_buys=7, ziel_extrem=108, be_aktiv=True)
    p.bestand_pct = 12.3456789
    mixed_book().sync_position(p)
    p.e42_meldungen = [{'art': 'transient'}]
    saved = pos_to_state(p)
    required = {f.name for f in fields(sc.Position)} - {'e42_meldungen', 'state'} | {'pos_state', 'state_version'}
    assert set(saved) == required
    restored = pos_from_state(json_copy(saved))
    expected = deepcopy(p)
    expected.e42_meldungen = []
    assert restored == expected
    assert restored.widerstand_exits == 1 and restored.bestand_pct == 12.3456789
    assert restored.zones.impulse.end.idx == 1


def test_legacy_active_state_preserves_reference_history_and_dedupe():
    old = dict(pos_state='TP1', direction='LONG', entry_ref=188.53333, entry_pct=130,
               last_signal_ts=1234, widerstand_exits=1, stop_wartet=1, stop_wartet_inv=80)
    p = pos_from_state(old)
    assert p.state == sc.PosState.TP1 and p.entry_ref == 188.53333
    assert p.entry_pct == 130 and p.last_signal_ts == 1234 and p.widerstand_exits == 1
    assert p.lots == [] and p.inventory_source == 'signal_reference' and not p.cost_basis_complete
    assert 'prior_stop_maximum_unknown' in p.migration_notes and p.valid_stop is None
    assert pos_from_state(json_copy(pos_to_state(p))) == p


def test_missing_legacy_widerstand_is_marked_not_reconstructed():
    p = pos_from_state({'pos_state': 'CORE', 'entry_ref': 100})
    assert p.widerstand_exits == 0
    assert 'widerstand_exits_missing_default_0' in p.migration_notes
    assert p.state == sc.PosState.CORE and p.entry_ref == 100


def rejects(fn):
    try:
        fn()
    except (ValueError, KeyError):
        return
    raise AssertionError('Incomplete/unsupported state accepted')


def test_unknown_version_or_missing_decision_field_rejected():
    d = pos_to_state(position())
    rejects(lambda: pos_from_state(dict(d, state_version=99)))
    d.pop('widerstand_exits')
    rejects(lambda: pos_from_state(d))
    d = pos_to_state(position())
    d.pop('state_version')
    rejects(lambda: pos_from_state(d))
    d = pos_to_state(position())
    d['zones'].pop('impuls_ende_ts')
    rejects(lambda: pos_from_state(d))
    d = pos_to_state(position())
    d.update(valid_stop=float('nan'), valid_stop_reason='Struktur-Tief')
    rejects(lambda: pos_from_state(d))


def test_live_reference_plan_cannot_claim_manual_fills():
    from telegram_notify import format_plan
    p, cs, kw = stop_fixture()
    plan = main.positions_plan(cs, [], kw, p)
    assert plan['bestand_quelle'] == 'signal_reference' and not plan['live_bestand_belegt']
    assert 'Signalreferenz' in plan['einstand_art']
    text = format_plan(plan)
    assert 'Signalreferenz' in text and 'nicht belegt' in text


def checkpoint_fixture():
    cs, fs = entry_fixture()
    cfg = dict(bias_short=False, pivot_n=2, tp_ladder=False, buy_ladder=False)
    full = v.run_v1(cs, fs, cfg, start_ms=0, end_ms=cs[-1].ts+v.STEP)
    fill = next(e for e in full['ledger'] if e['status'] == 'filled')
    return cs, fs, cfg, full, fill


def test_pending_buy_checkpoint_json_restart_exact_parity():
    import backtest
    cs, fs, cfg, full, fill = checkpoint_fixture()
    r = backtest.run_execution(cs, fs, cfg, start_ms=0, end_ms=cs[-1].ts+v.STEP,
                 checkpoint_at=fill['candle_id'])
    checkpoint = json_copy(r.pop('checkpoint'))
    assert checkpoint['pending'] and checkpoint['book']['reserved_cash'] > 0
    assert checkpoint['book']['units'] == 0
    assert r == full
    assert v.resume_v1(cs, fs, checkpoint) == full


def test_open_position_checkpoint_json_restart_exact_parity():
    cs, fs, cfg, full, fill = checkpoint_fixture()
    r = v.run_v1(cs, fs, cfg, start_ms=0, end_ms=cs[-1].ts+v.STEP,
                 checkpoint_at=fill['fill_at'])
    checkpoint = json_copy(r.pop('checkpoint'))
    assert checkpoint['book']['units'] > 0 and checkpoint['position']['lots']
    assert v.resume_v1(cs, fs, checkpoint) == full


def test_checkpoint_rejects_changed_prefix_config_and_incomplete_reservations():
    cs, fs, cfg, full, fill = checkpoint_fixture()
    cp = v.run_v1(cs, fs, cfg, start_ms=0, end_ms=cs[-1].ts+v.STEP,
                  checkpoint_at=fill['candle_id'])['checkpoint']
    changed = list(cs)
    c = changed[0]
    changed[0] = sc.Candle(c.ts, c.open, c.high+1, c.low, c.close)
    rejects(lambda: v.resume_v1(changed, fs, json_copy(cp)))
    bad = json_copy(cp)
    bad['book']['reserved_cash'] = 0
    rejects(lambda: v.resume_v1(cs, fs, bad))
    bad = json_copy(cp)
    bad['decision']['params']['trail_stop'] = True
    rejects(lambda: v.resume_v1(cs, fs, bad))
    bad = json_copy(cp)
    bad['version'] = 2
    rejects(lambda: v.resume_v1(cs, fs, bad))


def test_book_pending_reservations_lots_and_ledger_roundtrip():
    book = mixed_book(.001)
    book.schedule([dict(ts=3*v.STEP, action='part_stop', type='RUECKKAUF_STOP',
        price=150, tranche_pct=25, reason='pending')], 150)
    restored = v.Book.from_state(json_copy(book.to_state()))
    assert restored.__dict__ == book.__dict__
    assert restored.reserved_units > 0 and restored.lots


def test_flat_reset_preserves_cross_cycle_memories_only():
    p = position(valid_stop=115, valid_stop_reason='Struktur-Tief', last_stop_ts=42,
                 e42_marke=130, e42_richtung='LONG', e42_gekauft=125, widerstand_exits=2)
    mixed_book().sync_position(p)
    sc._reset_position(p)
    assert p.lots == [] and p.valid_stop is None and p.widerstand_exits == 0
    assert p.last_stop_ts == 42 and p.e42_marke == 130 and p.e42_gekauft == 125
    assert pos_from_state(json_copy(pos_to_state(p))) == p


def test_resistance_limit_reached_then_identical_after_restart():
    import test_strategy_core as t
    cs = t._e20_pfad() + [t.c(16, 124, 127, 123, 126.5)]
    p = t._e20_position(cs)
    kw = dict(pivot_n=2, k_atr=2., bias_short=False, tp_ladder=False,
              buy_ladder=False, high_exit='off', widerstand_exit='on')
    first = sc.evaluate(cs, t.neg_funding_flow(), p, **kw)
    assert len([s for s in first if 'Widerstandszone' in s.reason]) == 1
    assert p.widerstand_exits == 1
    resumed = pos_from_state(json_copy(pos_to_state(p)))
    for i in (17, 18):
        cs.append(t.c(i, 124, 127, 123, 126.5))
        a = sc.evaluate(cs, t.neg_funding_flow(), p, **kw)
        b = sc.evaluate(cs, t.neg_funding_flow(), resumed, **kw)
        assert a == b and p == resumed
        hits = [s for s in a if 'Widerstandszone' in s.reason]
        assert len(hits) == (1 if i == 17 else 0)
    assert p.widerstand_exits == sc.MAX_WIDERSTAND_EXITS == 2


def test_live_reference_multibar_restart_no_duplicate_historical_signals():
    p, cs, kw = stop_fixture()
    pivots = [sc.Pivot(0, 0, 115, 'L')]
    with patch.object(sc, 'find_pivots', return_value=pivots):
        sc.evaluate(cs, [], p, **kw)
    resumed = pos_from_state(json_copy(pos_to_state(p)))
    assert sc.evaluate(cs, [], resumed, **kw) == []  # Dedupe survives restart.
    for i, price in ((3, 119), (4, 118), (5, 110)):
        cs.append(sc.Candle(i*v.STEP, price, price+1, price-1, price))
        with patch.object(sc, 'find_pivots', return_value=[]):
            a = sc.evaluate(cs, [], p, **kw)
            b = sc.evaluate(cs, [], resumed, **kw)
        assert a == b and p == resumed
        resumed = pos_from_state(json_copy(pos_to_state(resumed)))
    assert p.state == sc.PosState.FLAT and len(a) == 1 and a[0].type == sc.SignalType.STOPLOSS


def test_pending_stop_checkpoint_keeps_inventory_until_next_open():
    p = position(sc.PosState.TP1, valid_stop=115, valid_stop_reason='Struktur-Tief')
    lots = [dict(id='explicit_initial', at=0, fill_price=100., units=1.,
                 cost=100., buy_fee=0., kind='base')]
    cs, fs = bars([(120, 120, 119, 120), (120, 120, 109, 110), (90, 95, 85, 90)])
    cfg = dict(trail_stop=True, buy_ladder=False, tp_ladder=False, rest_halten=True)
    with patch.object(sc, 'find_pivots', return_value=[]):
        r = v.run_v1(cs, fs, cfg, start_ms=0, end_ms=3*v.STEP,
                     start_capital=0, initial_units=1, initial_position=p,
                     initial_lots=lots, checkpoint_at=v.STEP)
    cp = json_copy(r.pop('checkpoint'))
    assert cp['book']['units'] == 1 and cp['book']['reserved_units'] == 1
    assert cp['pending'][0]['type'] == 'STOPLOSS'
    assert cp['position']['valid_stop'] == 115
    with patch.object(sc, 'find_pivots', return_value=[]):
        resumed = v.resume_v1(cs, fs, cp)
    assert resumed == r
    near(r['cash'], 89.91)
    assert r['lots'] == [] and r['position_state']['pos_state'] == 'FLAT'


def test_missing_book_cost_field_and_forged_live_source_are_rejected():
    d = mixed_book().to_state()
    d['lots'][0].pop('cost')
    rejects(lambda: v.Book.from_state(d))
    d = pos_to_state(position())
    d['inventory_source'] = 'live_fills'
    rejects(lambda: pos_from_state(d))


def test_selling_all_base_leaves_e42_without_phantom_base_entry():
    book = v.Book(100, 0, 0, 1)
    trade(book, 'e42_buy', 'RUECKKAUF', 125, 25, 0)
    p = position()
    book.sync_position(p)
    assert p.entry_ref is None and p.entry_pct == 0
    near(inventory.summary(p.lots)['entry'], 125)


def test_tiny_partial_sale_retains_nonzero_cost():
    book = v.Book(1e-16, 0, 0, 1)
    trade(book, 'entry_t1', 'KAUF_1', 1e5, 100, 0)
    trade(book, 'tp1', 'TEILVERKAUF_1', 1e5, 40, 1)
    assert len(book.lots) == 1
    assert math.isclose(book.lots[0]['cost'], 6e-17, rel_tol=1e-12)
    assert math.isclose(book.lots[0]['units'], 6e-22, rel_tol=1e-12)


def test_checkpoint_preserves_earlier_peak_and_drawdown():
    p = position(sc.PosState.TP2)
    lots = [dict(id='initial', at=0, fill_price=100., units=1., cost=100., buy_fee=0., kind='base')]
    cs, fs = bars([(120, 200, 120, 180), (180, 185, 165, 170), (160, 160, 150, 150)])
    cfg = dict(trail_stop=True, buy_ladder=False, tp_ladder=False, rest_halten=True)
    with patch.object(sc, 'find_pivots', return_value=[]):
        r = v.run_v1(cs, fs, cfg, start_ms=0, end_ms=3*v.STEP, start_capital=0,
                     initial_units=1, initial_position=p, initial_lots=lots, checkpoint_at=v.STEP)
    cp = json_copy(r.pop('checkpoint'))
    assert cp['risk']['peaks'][2] == 200 and cp['risk']['dd'][2] > 0
    near(r['dd_intrabar_upper_pct'], 40)  # H200 before L120 in the first candle.
    with patch.object(sc, 'find_pivots', return_value=[]):
        assert v.resume_v1(cs, fs, cp) == r


def test_mixed_position_proportional_sale_then_e42_stop_across_restart():
    p = position(e42_teil_marke=110)
    lots = [dict(id=k, at=0, fill_price=price, units=q, cost=cost, buy_fee=0., kind=k)
            for k, price, q, cost in [('base', 100., 1., 100.), ('e42', 200., .25, 50.)]]
    cs, fs = bars([(140, 140, 120, 130), (130, 200, 120, 180),
                   (180, 180, 100, 105), (100, 110, 95, 105)])
    cfg = dict(trail_stop=False, buy_ladder=False, tp_ladder=False, rest_halten=True)
    with patch.object(sc, 'find_pivots', return_value=[]):
        r = v.run_v1(cs, fs, cfg, start_ms=0, end_ms=4*v.STEP, fee=0,
                     start_capital=50, initial_units=1.25, initial_position=p,
                     initial_lots=lots, checkpoint_at=2*v.STEP)
    cp = json_copy(r.pop('checkpoint'))
    assert cp['pending'][0]['type'] == 'RUECKKAUF_STOP'
    near(cp['book']['reserved_units'], .15)
    near(cp['book']['lots'][0]['cost'], 60)
    near(cp['book']['lots'][1]['cost'], 30)
    with patch.object(sc, 'find_pivots', return_value=[]):
        assert v.resume_v1(cs, fs, cp) == r
    assert [e['type'] for e in r['ledger'] if e['status'] == 'filled'] == ['TEILVERKAUF_1', 'RUECKKAUF_STOP']
    near(r['btc'], .6)
    near(r['cost_basis'], 60)
    near(r['cost_entry'], 100)
    assert r['position_state']['e42_teil_marke'] is None


def test_confirmed_tp_arms_stop_before_next_close_using_only_known_prefix():
    p = position()
    cs, fs = bars([(140, 200, 120, 140)])
    pivot = sc.Pivot(0, 0, 115, 'L')
    kw = dict(trail_stop=True, tp_ladder=False, buy_ladder=False, rest_halten=True)
    with patch.object(sc, 'find_pivots', return_value=[pivot]):
        d = v.decide(cs, fs, p, kw)
    assert [o['action'] for o in d.candidates] == ['tp1']
    assert p.state == sc.PosState.FULL and p.valid_stop == 80
    lots = [dict(id='base', at=0, fill_price=100., units=1., cost=100., buy_fee=0., kind='base')]
    book = v.Book(0, 0, 0, 1, 1, lots)
    pending = book.schedule(d.candidates, 140)
    done = [book.fill(o, sc.Candle(v.STEP, 110, 112, 108, 110)) for o in pending]
    with patch.object(sc, 'find_pivots', return_value=[pivot]) as find:
        d.confirm(p, done, book)
    assert find.call_args.args[0] == cs  # No next-bar information used to arm stop.
    assert p.state == sc.PosState.TP1 and p.valid_stop == 115
    p = pos_from_state(json_copy(pos_to_state(p)))
    cs.append(sc.Candle(v.STEP, 110, 112, 108, 110))
    fs.append(sc.FlowPoint(v.STEP, 0, 0, 1, 0))
    with patch.object(sc, 'find_pivots', return_value=[]):
        nxt = v.decide(cs, fs, p, kw)
    assert [o['action'] for o in nxt.candidates] == ['stop']


def test_unfilled_tp_does_not_arm_fill_dependent_trailing():
    p = position()
    cs, fs = bars([(140, 200, 120, 140)])
    with patch.object(sc, 'find_pivots', return_value=[sc.Pivot(0, 0, 115, 'L')]):
        d = v.decide(cs, fs, p, dict(trail_stop=True, tp_ladder=False, buy_ladder=False, rest_halten=True))
    assert [o['action'] for o in d.candidates] == ['tp1']
    assert p.valid_stop == 80 and p.state == sc.PosState.FULL
    book = v.Book(0, 0, 0, 1, 1)
    for o in book.schedule(d.candidates, 140):
        book.expire(o, 140)
    assert p.valid_stop == 80 and p.state == sc.PosState.FULL


def test_signal_tp_plan_arms_same_stop_for_next_observation():
    p = position()
    cs = [sc.Candle(0, 140, 200, 120, 140)]
    with patch.object(sc, 'find_pivots', return_value=[sc.Pivot(0, 0, 115, 'L')]):
        sigs = sc.evaluate(cs, [], p, trail_stop=True, tp_ladder=False, buy_ladder=False, rest_halten=True)
    assert [s.type for s in sigs] == [sc.SignalType.TEILVERKAUF_1]
    assert p.valid_stop == 115 and p.state == sc.PosState.TP1
    plan = main.positions_plan(cs, [], {'trail_stop': True}, p)
    assert plan['stop']['preis'] == 115


def test_structure_history_can_change_armed_stop_without_changing_usd_pattern():
    import test_strategy_core as t
    cs, raw = t._pump_szenario()
    target = 18403200000
    results = []
    for window in (400, 1200):
        p = sc.Position()
        for i in range(len(cs)-60, len(cs)+1):
            start = max(0, i-window)
            prefix = cs[start:i]
            flow = t._flow_ab(cs, raw, start, i)
            sigs = sc.evaluate(prefix, flow, p, **dict(t._live_einstellung(), muster_cvd='usd'))
            if prefix[-1].ts == target:
                assert [s.type for s in sigs] == [sc.SignalType.TEILVERKAUF_LADDER]
                results.append((sc.classify_pattern(prefix, flow, muster_cvd='usd'), p.valid_stop))
                break
    assert results[0][0] == results[1][0]
    near(results[0][1], 135679.20473905507)
    near(results[1][1], 138026.3881866903)
