"""Descriptive capital benchmark fixed by the original supplementary plan."""

import gzip
import hashlib
import json
from pathlib import Path
import socket

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
STEP = 14_400_000


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(*_args, **_kwargs):
    raise AssertionError("A7 benchmark has no network access")


def case(candles, fraction):
    capital, fee = 10000., .001
    entry, final = candles[0]["close"], candles[-1]["close"]
    budget = capital*fraction
    btc = budget*(1-fee)/entry
    cash = capital-budget
    end = cash+btc*final
    exit_fee = btc*final*fee
    peak, max_dd = capital, 0.
    for c in candles:
        equity = cash+btc*c["close"]
        peak = max(peak, equity)
        max_dd = max(max_dd, 100*(1-equity/peak))
    return {"fraction": fraction, "entry_close_usd": entry,
            "final_close_usd": final, "entry_fee_usd": budget*fee,
            "btc": btc, "cash_usd": cash, "end_marked_usd": end,
            "return_marked_pct": (end/capital-1)*100,
            "exit_fee_if_sold_usd": exit_fee,
            "end_if_sold_usd": end-exit_fee,
            "return_if_sold_pct": ((end-exit_fee)/capital-1)*100,
            "dd_close_pct": max_dd}


def main():
    socket.socket.connect = socket.create_connection = blocked
    flow_path = DOC / "A7-flow-modeled-v2.json.gz"
    data = json.loads(gzip.decompress(flow_path.read_bytes()))
    output = {"schema": "a7-buyhold-description-v1", "flow_sha256": sha(flow_path),
              "historical_execution_claim": False,
              "mean_exposure_benchmark_selected_after_seeing_V000_exposure": True,
              "results": []}
    for package in ("R0", "R1"):
        cutoff = (read(ROOT / "docs" / "nach-6" / "R0" / "results.json")["cutoff"]
                  if package == "R0" else data["ende"])
        cs = [c for c in data["candles"] if data["start"] <= c["ts"] and
              c["ts"]+STEP <= cutoff]
        assert cs and cs[0]["ts"] == data["start"]
        base = read(DOC / "A7-runs" / f"{package}-S0-V000.json")
        exposure = base["detail"]["verification"]["avg_exposure_pct"]/100
        output["results"].append({"package": package, "start_ms": cs[0]["ts"],
               "cutoff_ms": cutoff, "bars": len(cs),
               "full": case(cs, 1.), "V000_mean_exposure_fraction": exposure,
               "exposure_matched_posthoc": case(cs, exposure)})
    dest = DOC / "A7-buyhold-v1.json"
    raw = (json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False)+"\n").encode()
    if dest.exists():
        assert dest.read_bytes() == raw
    else:
        dest.write_bytes(raw)
    print("A7 buy and hold description R0/R1, no trading comparison claim")


if __name__ == "__main__":
    main()
