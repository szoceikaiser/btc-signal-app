"""Offline-Tests fuer die Coinalyze-Anbindung (E9.1). Kein Netz, kein Key noetig."""

import io
import json

import coinalyze


def test_build_url_enthaelt_endpoint_und_params():
    url = coinalyze.build_url("open-interest-history",
                              {"symbols": "BTCUSDT_PERP.A", "interval": "4hour"})
    assert url.startswith("https://api.coinalyze.net/v1/open-interest-history?")
    assert "symbols=BTCUSDT_PERP.A" in url or "symbols=BTCUSDT_PERP.A".replace(".", "%2E") in url
    assert "interval=4hour" in url


class _FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
        return False


def test_get_json_nutzt_injizierten_opener_und_key():
    captured = {}

    def fake_opener(req, timeout=0):
        captured["url"] = req.full_url
        captured["key"] = req.headers.get("Api_key") or req.headers.get("api_key")
        return _FakeResp(json.dumps([{"symbol": "X", "history": [1, 2, 3]}]).encode())

    data = coinalyze.get_json("liquidation-history",
                              {"symbols": "BTCUSDT_PERP.A", "interval": "4hour"},
                              api_key="KEY123", opener=fake_opener)
    assert data == [{"symbol": "X", "history": [1, 2, 3]}]
    assert captured["key"] == "KEY123"
    assert "liquidation-history" in captured["url"]


def test_sample_kuerzt_history_auf_letzte_drei():
    data = [{"symbol": "X", "history": [1, 2, 3, 4, 5]}]
    assert coinalyze._sample(data) == [{"symbol": "X", "history": [3, 4, 5]}]
    # Robust gegen unerwartete Formen
    assert coinalyze._sample({"foo": "bar"}) == {"foo": "bar"}


def _fake(resp):
    def opener(req, timeout=0):
        return _FakeResp(json.dumps(resp).encode())
    return opener


# Format am 2026-07-24 per Test-Lauf bestaetigt
def test_oi_by_ts_nimmt_close_und_wandelt_in_ms():
    resp = [{"symbol": "BTCUSDT_PERP.A", "history": [
        {"t": 1784865600, "o": 1, "h": 2, "l": 0.5, "c": 6762600631.87},
        {"t": 1784880000, "o": 1, "h": 2, "l": 0.5, "c": 6787210608.47}]}]
    d = coinalyze.oi_by_ts("KEY", opener=_fake(resp))
    assert d == {1784865600000: 6762600631.87, 1784880000000: 6787210608.47}


def test_liquidations_by_ts_long_und_short():
    resp = [{"symbol": "BTCUSDT_PERP.A", "history": [
        {"t": 1784865600, "l": 281390.06, "s": 1587451.09}]}]
    d = coinalyze.liquidations_by_ts("KEY", opener=_fake(resp))
    assert d == {1784865600000: (281390.06, 1587451.09)}


def test_history_points_findet_symbol():
    resp = [{"symbol": "BTCUSDT_PERP.A", "history": [{"t": 1, "c": 9}]}]
    assert coinalyze._history_points(resp) == [{"t": 1, "c": 9}]
    assert coinalyze._history_points([]) == []
