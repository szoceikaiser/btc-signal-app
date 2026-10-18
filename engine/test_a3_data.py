"""A3: unabhaengige UTC-, Korb- und Einheiten-Gegenfaelle; kein Netz."""
import coinalyze as cz
from strategy_core import Candle, resample_daily, daily_trend

H4 = 14_400_000
DAY = 86_400_000


def _bar(ts, value):
    return Candle(ts, value, value + 1, value - 1, value)


def test_utc_tageswechsel_erfordert_alle_sechs_abgeschlossenen_slots():
    day0 = [_bar(i * H4, 100 + i) for i in range(6)]
    assert resample_daily(day0[:5]) == []
    assert resample_daily(day0) == [Candle(0, 100, 106, 99, 105)]
    assert resample_daily(day0 + [_bar(DAY, 999)]) == resample_daily(day0)
    # Erst nach dem sechsten Slot des Folgetags kommt dessen Tageskerze hinzu.
    day1 = [_bar(DAY + i * H4, 200 + i) for i in range(6)]
    assert [d.ts for d in resample_daily(day0 + day1)] == [0, DAY]


def test_teilluecke_und_doppelter_slot_sind_keine_tageskerze():
    bars = [_bar(i * H4, 100 + i) for i in range(6)]
    assert resample_daily(bars[:2] + bars[3:]) == []
    assert resample_daily(bars + [bars[3]]) == []
    assert resample_daily(bars + [_bar(7 * H4 + 1, 999)]) == [
        Candle(0, 100, 106, 99, 105)]
    assert daily_trend(bars[:5] + [_bar(DAY, 999)]) is None


def test_angeforderter_markt_ohne_antwort_sperrt_summe_und_mittel():
    summed, report = cz._summiere_vollstaendig({'A': {0: 10, 1: 11}},
                                                ['A', 'B'], [], 'USD')
    assert summed == {} and report['ohne_antwort'] == ['B']
    assert report['punkte_ausgelassen'] == 2 and report['punkte_vollstaendig'] == 0
    mean, report = cz.gewichtetes_mittel({'A': {0: 0.1}}, {'A': {0: 10}},
                                          ['A', 'B'], [], 'rate')
    assert mean == {} and report['ohne_antwort'] == ['B']


def test_teilluecke_laesst_nur_den_betroffenen_zeitpunkt_weg():
    summed, report = cz._summiere_vollstaendig(
        {'A': {0: 10, 1: 11}, 'B': {0: 20}}, ['A', 'B'], [], 'USD')
    assert summed == {0: 30} and report['punkte_ausgelassen'] == 1


def test_btc_usd_volumenvergleich_nach_belegter_umrechnung():
    btc = {'symbol': 'BTC', 'history': [{'t': 1, 'v': 1000, 'bv': 600, 'c': 60000}]}
    usd = {'symbol': 'USD', 'history': [{'t': 1, 'v': 2000, 'bv': 1200, 'c': 60000}]}
    b = cz._reihe_auswerten(btc, {'base_asset': 'BTC', 'quote_asset': 'USD',
                                   cz.DENOM_FELD: 'BASE_ASSET'})
    u = cz._reihe_auswerten(usd, {'base_asset': 'BTC', 'quote_asset': 'USD',
                                   cz.DENOM_FELD: 'QUOTE_ASSET'})
    assert b['summe_v_usd'] == 60_000_000 and u['summe_v_usd'] == 2000
    chosen, excluded = cz._nach_denominierung({
        'a': {'symbol': 'BTC', 'denominierung': 'BASE_ASSET', **b},
        'b': {'symbol': 'USD', 'denominierung': 'QUOTE_ASSET', **u}})
    assert chosen == ['BTC'] and [x['symbol'] for x in excluded] == ['USD']


def test_unbekannte_umrechnung_ist_nicht_auswertbar():
    row = {'symbol': 'X', 'history': [{'t': 1, 'v': 1000, 'bv': 600, 'c': 60000}]}
    missing = cz._reihe_auswerten(row, {'base_asset': 'BTC', 'quote_asset': 'USDT',
                                        cz.DENOM_FELD: 'BASE_ASSET'})
    assert missing['summe_v_usd'] is None and 'Umrechnung' in missing['nicht_auswertbar']
    unknown = cz._reihe_auswerten(row, {'base_asset': 'BTC', 'quote_asset': 'USD'})
    assert unknown['summe_v_usd'] is None
    with_fx = cz._reihe_auswerten(row, {'base_asset': 'BTC', 'quote_asset': 'USDT',
                                        cz.DENOM_FELD: 'BASE_ASSET'}, {'USDT': {1: 0.99}})
    assert with_fx['summe_v_usd'] == 59_400_000


def test_aggregierter_cvd_ohne_belegte_einheiten_wird_nicht_abgerufen():
    def forbidden(*_args, **_kw):
        raise AssertionError('ohne Einheitennachweis darf kein Abruf stattfinden')
    spot, sb = cz.spot_delta_aggregiert('offline', ['A'], opener=forbidden)
    fut, fb = cz.fut_delta_aggregiert('offline', ['A', 'B'],
                                      einheiten={'A': 'BTC', 'B': 'USD'}, opener=forbidden)
    assert spot == {} and 'fehler' in sb
    assert fut == {} and 'fehler' in fb
