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
