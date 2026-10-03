"""Reconcile public Kraken chart funding with the frozen A7 hourly archive.

This is a source check, not a derivative strategy or return calculation.
"""
import hashlib
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/audit-nacharbeit-2026-10"
SRC = DOC / "A7-V035-sources"
RAW = ROOT / "docs/nach-6/r1-raw/funding.json"
HOUR = 3_600_000
SOURCES = {
    "2026-02-04T12:00:00Z": (
        "funding-chart-feb04-empty.json", 1770199200, 1770217200,
        "5b83239da90473ffbccebca3c85be133404d553b87d1d2190e3d8bad33eef915"),
    "2026-02-13T18:00:00Z": (
        "funding-chart-feb13.json", 1771002000, 1771012800,
        "676b770917e1eb3d06741b11fb5e09bd01eac03376f1d85d084736fba1300d1f"),
    "2026-05-09T06:00:00Z": (
        "funding-chart-may09.json", 1778302800, 1778313600,
        "74ade414997ab783e98d0129da27f63df7f2f10507b16678d64179964fa7683d"),
}


def stamp(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen = json.loads(RAW.read_text(encoding="utf-8"), parse_float=Decimal)
    rates = {stamp(r["timestamp"]): r["fundingRate"] for r in frozen["rates"]}
    observations = []
    for iso, (name, since, to, expected_hash) in SOURCES.items():
        path = SRC / name
        assert digest(path) == expected_hash
        data = json.loads(path.read_text(encoding="utf-8"))["result"]
        ts = stamp(iso)
        url = ("https://futures.kraken.com/api/charts/v1/analytics/"
               f"PF_XBTUSD/funding?since={since}&interval=3600&to={to}")
        chart = {int(t): tuple(Decimal(v) for v in ohlc)
                 for t, ohlc in zip(data["timestamp"], data["data"]["rate"])}
        assert ts not in rates
        assert len(chart) == len(data["timestamp"])
        neighbors = []
        for adjacent in (ts-HOUR, ts+HOUR):
            if adjacent in chart and adjacent in rates:
                delta = chart[adjacent][3] - rates[adjacent]
                assert abs(delta) < Decimal("0.000000000001"), (iso, adjacent, delta)
                neighbors.append({"timestamp_ms": adjacent,
                                  "chart_close": str(chart[adjacent][3]),
                                  "archive_rate": str(rates[adjacent]),
                                  "absolute_difference": str(abs(delta))})
        if ts in chart:
            assert len(neighbors) == 2
            ohlc = chart[ts]
            # A flat candle identifies the displayed value, but could be a
            # chart carry-forward rather than a settled hourly payment.
            assert len(set(ohlc)) == 1
            assert ohlc[3] == chart[ts-HOUR][3]
            status = "chart_displays_previous_value_settlement_unproven"
            value = str(ohlc[3])
        else:
            assert not chart and not neighbors
            status = "missing_in_archive_and_public_chart"
            value = None
        observations.append({"timestamp": iso, "status": status,
                             "chart_absolute_usd_per_btc": value,
                             "chart_file": name, "chart_sha256": expected_hash,
                             "chart_url": url, "adjacent_checks": neighbors})
    output = {
        "schema": "a7-v035-funding-gap-reconciliation-v1",
        "frozen_funding_sha256": digest(RAW),
        "contract": "Exact UTC hour; chart close checked against both neighboring frozen endpoint rates. At both gaps the chart repeats the prior close, so payment remains unproven. No zero, carry, or interpolation is inserted into accounting.",
        "historical_api_as_of_proven": False,
        "full_window_complete": False,
        "observations": observations,
    }
    path = SRC / "gap-reconciliation-v1.json"
    content = json.dumps(output, indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        assert path.read_text(encoding="utf-8") == content
    else:
        path.write_text(content, encoding="utf-8")
    print("V035 funding reconciliation PASS: 2 chart values (settlement unproven), 1 chart absent")


if __name__ == "__main__":
    main()
