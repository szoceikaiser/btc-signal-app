"""Build a versioned A2 model-flow from frozen R1 and archived source timestamps.

No network. Availability is explicitly modeled by the A2 contract, not claimed
as historical API publication. Original R0/R1 files are read-only.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from flow_contract import AsOfSeries, FOUR_HOURS_MS, MAX_FUNDING_AGE_MS, MAX_OI_AGE_MS, asof, direct

DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
N6 = ROOT / "docs" / "nach-6"
R1 = N6 / "r1-inputs.json"
ARCHIVE = N6 / "sources" / "archive-8651bc8c056c.json"
RAW = N6 / "r1-raw"
OUT = DOC / "A7-flow-modeled-v2.json.gz"
MANIFEST = DOC / "A7-flow-modeled-manifest-v2.json"
EXTENSION_START = 1790496000000
FIELDS = ("spot_cvd", "fut_cvd", "oi", "oi_btc", "funding", "long_liq", "short_liq", "long_pct")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_map(archive, name, raw_name, fields):
    points = {int(t): v for t, v in archive[name].items() if int(t) < EXTENSION_START}
    raw = read(RAW / f"{raw_name}.json")
    assert len(raw) == 1 and raw[0]["symbol"] == "BTCUSDT_PERP.A"
    extension = {int(p["t"]) * 1000: [float(p[k]) for k in fields]
                 for p in raw[0]["history"] if int(p["t"]) * 1000 >= EXTENSION_START}
    assert len(extension) == len(raw[0]["history"]) - sum(
        int(p["t"]) * 1000 < EXTENSION_START for p in raw[0]["history"])
    for t, vals in extension.items():
        points[t] = vals[0] if len(vals) == 1 else vals
    return dict(sorted(points.items()))


def saved(path, raw):
    if path.exists():
        assert path.read_bytes() == raw, f"Frozen output changed: {path}"
    else:
        path.write_bytes(raw)


def main():
    contract = DOC / "A7-ABLEITUNGSVERTRAG-v2.md"
    assert contract.exists()
    prior = read(DOC / "A7-analysemanifest-v1.json")
    assert sha(R1) == prior["frozen_data"]["R1_sha256"]
    r1, archive = read(R1), read(ARCHIVE)
    assert r1["ende"] == 1790683200000
    cs, old_fs = r1["candles"], r1["flow"]
    assert len(cs) == len(old_fs) == 2493
    assert all(c["ts"] == f["ts"] and c["ts"] + FOUR_HOURS_MS <= r1["ende"]
               for c, f in zip(cs, old_fs))
    assert all(b["ts"] - a["ts"] == FOUR_HOURS_MS for a, b in zip(cs, cs[1:]))
    closes = {c["ts"]: c["close"] for c in cs}
    oi_map = source_map(archive, "oi", "open-interest-history", ["c"])
    liq_map = source_map(archive, "liq", "liquidation-history", ["l", "s"])
    fut_components = source_map(archive, "fut", "ohlcv-history", ["bv", "v"])
    assert all(0 <= v[0] <= v[1] for t, v in fut_components.items() if t >= EXTENSION_START)
    fut_map = {t: (2 * v[0] - v[1] if isinstance(v, list) else v)
               for t, v in fut_components.items()}
    ls_map = source_map(archive, "ls", "long-short-ratio-history", ["l"])
    for name, mapping in [("oi", oi_map), ("liq", liq_map), ("fut", fut_map), ("ls", ls_map)]:
        assert len(mapping) == len(set(mapping)) and all(t % FOUR_HOURS_MS == 0 for t in mapping), name
    funding_raw = read(RAW / "funding.json")["rates"]
    funding_map = {
        int(datetime.fromisoformat(p["timestamp"].replace("Z", "+00:00")).timestamp() * 1000):
        float(p["relativeFundingRate"]) * 8 for p in funding_raw
    }
    assert len(funding_map) == len(funding_raw) == 8880
    assert all(math.isfinite(v) for v in funding_map.values())
    oi_series = AsOfSeries(oi_map.items(), FOUR_HOURS_MS)
    btc_series = AsOfSeries(((t, val / closes[t]) for t, val in oi_map.items() if t in closes),
                            FOUR_HOURS_MS)
    funding_series = AsOfSeries(funding_map.items())
    flow = []
    fut_cvd = 0.0
    old_mismatch = Counter()
    active_coverage = {field: Counter() for field in FIELDS}
    missing_active = {field: [] for field in FIELDS}
    for c, old in zip(cs, old_fs):
        ts, decision = c["ts"], c["ts"] + FOUR_HOURS_MS
        fut_delta = fut_map.get(ts)
        if fut_delta is not None:
            fut_cvd += fut_delta
        oi, oi_meta = asof(oi_series, decision, "coinalyze_archive_oi_usd", MAX_OI_AGE_MS)
        btc, btc_meta = asof(btc_series, decision, "coinalyze_archive_oi_btc", MAX_OI_AGE_MS)
        funding, funding_meta = asof(funding_series, decision, "kraken_hourly_funding_indicator_x8",
                                      MAX_FUNDING_AGE_MS)
        liq = liq_map.get(ts)
        long_pct = ls_map.get(ts)
        metadata = {
            "spot_cvd": direct(ts, decision, "r1_frozen_binance_taker_quote_cvd"),
            "fut_cvd": direct(ts, decision, "coinalyze_archive_fut_delta_btc", fut_delta is not None),
            "oi": oi_meta, "oi_btc": btc_meta, "funding": funding_meta,
            "long_liq": direct(ts, decision, "coinalyze_archive_long_liq_usd", liq is not None),
            "short_liq": direct(ts, decision, "coinalyze_archive_short_liq_usd", liq is not None),
            "long_pct": direct(ts, decision, "coinalyze_archive_long_pct", long_pct is not None),
        }
        for item in metadata.values():
            item["historical_api_as_of_proven"] = False
        row = {
            "ts": ts, "spot_cvd": old["spot_cvd"], "fut_cvd": fut_cvd,
            "oi": oi, "oi_btc": btc, "funding": funding,
            "long_liq": liq[0] if liq is not None else 0.0,
            "short_liq": liq[1] if liq is not None else 0.0,
            "long_pct": long_pct if long_pct is not None else 0.0,
            "provenance": metadata,
        }
        for field in FIELDS:
            coverage = metadata[field]["coverage"]
            if ts >= r1["start"]:
                active_coverage[field][coverage] += 1
                if coverage == "missing":
                    missing_active[field].append(ts)
            if ts >= r1["start"] and not math.isclose(row[field], old[field], rel_tol=1e-10, abs_tol=1e-7):
                old_mismatch[field] += 1
        flow.append(row)
    assert len(flow) == len(cs)
    assert all(len(missing_active[name]) == 0 for name in ("spot_cvd", "fut_cvd", "oi", "oi_btc", "funding", "long_pct"))
    assert len(missing_active["long_liq"]) == len(missing_active["short_liq"]) == 4
    print("Source numeric differences:", dict(old_mismatch), flush=True)
    assert all(old_mismatch[name] == 0 for name in ("spot_cvd", "oi", "funding", "long_liq", "short_liq", "long_pct"))
    output = {"package": "A7-flow-modeled-v2", "start": r1["start"], "ende": r1["ende"],
              "candles": cs, "flow": flow}
    encoded = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    compressed = gzip.compress(encoded, compresslevel=6, mtime=0)
    saved(OUT, compressed)
    manifest = {
        "schema": "a7-flow-modeled-v2", "contract_sha256": sha(contract),
        "code_sha256": sha(Path(__file__)), "base_commit": prior["base_commit"],
        "R1_input_sha256": sha(R1), "archive_sha256": sha(ARCHIVE),
        "raw_sha256": {p.name: sha(p) for p in sorted(RAW.glob("*.json"))},
        "data_sha256": hashlib.sha256(encoded).hexdigest(), "compressed_sha256": sha(OUT),
        "first_open_ms": cs[0]["ts"], "end_exclusive_ms": r1["ende"],
        "all_bars": len(cs), "active_bars": sum(c["ts"] >= r1["start"] for c in cs),
        "source_ranges": {name: {"first": min(mapping), "last": max(mapping), "count": len(mapping)}
                          for name, mapping in [("oi", oi_map), ("liq", liq_map),
                                                ("fut", fut_map), ("ls", ls_map),
                                                ("funding", funding_map)]},
        "active_coverage": {name: dict(counts) for name, counts in active_coverage.items()},
        "missing_active_times": missing_active,
        "numeric_differences_against_R1": dict(old_mismatch),
        "historical_api_as_of_proven": False,
        "availability": "A2 modeled bar close for Coinalyze/Binance; source timestamp for Kraken hourly funding",
        "no_new_market_data": True,
        "not_a_derivative_payment_book": True,
    }
    saved(MANIFEST, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print("A7 derived modeled flow:", len(cs), "bars;", manifest["active_bars"],
          "active; missing active", {k: len(v) for k, v in missing_active.items()},
          "mismatch", dict(old_mismatch), "sha256", sha(OUT), flush=True)


if __name__ == "__main__":
    main()
