"""Resume the frozen A7 conditional spot runs, with an independent book per run.

The grid mode covers every eligible original row in R0/R1 under S0. The pair
mode covers the prespecified V000/V004 across all five causal scenarios. Each
result is saved atomically and is immutable on rerun. No network is available.
"""

import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "engine"), str(ROOT / "tools")]
from backtest import run_execution
from execution_delayed import run_delayed
from historical_analysis import describe, verify_account
from strategy_core import Candle, FlowPoint

DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
OUT = DOC / "A7-runs"
STEP = 14_400_000


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(*_args, **_kwargs):
    raise AssertionError("A7 batch has no network access")


def atomic_frozen(path, obj):
    raw = (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False) + "\n").encode("utf-8")
    if path.exists():
        assert path.read_bytes() == raw, path
        return
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(raw)
    os.replace(temp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["grid", "pair", "half1", "half2",
                                           "fresh1", "fresh2", "capital06",
                                           "capital05"], required=True)
    parser.add_argument("--package", choices=["R0", "R1"], required=True)
    parser.add_argument("--scenario", choices=["S0", "S1", "S2", "S3", "S4"], required=True)
    parser.add_argument("--from-id", default="")
    parser.add_argument("--only-id", default="")
    args = parser.parse_args()
    socket.socket.connect = socket.create_connection = blocked

    design_path = DOC / "A7-analysemanifest-v1.json"
    gate_path = DOC / "A7-auswertbarkeit-v2.json"
    flow_path = DOC / "A7-flow-modeled-v2.json.gz"
    design, gate = read(design_path), read(gate_path)
    assert gate["manifest_sha256"] == sha(design_path)
    assert gate["flow_data_sha256"] == sha(flow_path)
    assert gate["eligible_conditional_spot"] == 85 and gate["blocked_F02"] == 1
    assert not gate["historical_api_as_of_proven"]
    assert gate["rows"][35]["id"] == "V035" and gate["rows"][35]["status"] == "blocked_F02"
    data = json.loads(gzip.decompress(flow_path.read_bytes()))
    n6_plan = read(ROOT / "docs" / "nach-6" / "plan.json")
    scenario = next(s for s in n6_plan["scenarios"] if s["id"] == args.scenario)
    assert scenario in design["comparison_lanes"]["causal_spot"]["scenarios"]
    cutoff = (data["ende"] if args.package == "R1" else
              read(ROOT / "docs" / "nach-6" / "R0" / "results.json")["cutoff"])
    full_cutoff = cutoff
    start_ms = data["start"]
    if args.mode in ("half1", "half2"):
        midpoint = data["start"] + (cutoff - data["start"]) // 2
        if args.mode == "half1":
            cutoff = midpoint
        else:
            start_ms = midpoint
    cs = [Candle(**c) for c in data["candles"] if c["ts"] + STEP <= cutoff]
    fs = [FlowPoint(**f) for f in data["flow"][:len(cs)]]
    assert len(cs) == len(fs) and all(c.ts == f.ts for c, f in zip(cs, fs))
    assert cutoff <= 1790683200000
    if args.mode in ("fresh1", "fresh2"):
        active = [c for c in cs if c.ts >= data["start"]]
        boundaries = n6_plan["packages"][args.package]["third_indices"]
        start_ms = active[boundaries[0 if args.mode == "fresh1" else 1]].ts

    book_path = ROOT / "tools" / "a7_independent_book.py"
    assert sha(book_path) == n6_plan["book_sha256"]
    spec = importlib.util.spec_from_file_location("a7_independent_audit_book", book_path)
    book = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(book)
    book.selfcheck()
    rows = ([r for r in design["rows"] if r["id"] != "V035"] if args.mode in
            ("grid", "half1", "half2")
            else [next(r for r in design["rows"] if r["id"] == name)
                  for name in ("V000", "V004")])
    if args.mode.startswith("capital"):
        rows = rows[:1]
    assert len(rows) == (85 if args.mode in ("grid", "half1", "half2") else
                         1 if args.mode.startswith("capital") else 2)
    OUT.mkdir(exist_ok=True)
    for row in rows:
        rid = row["id"]
        if (args.from_id and rid < args.from_id) or (args.only_id and rid != args.only_id):
            continue
        suffix = "" if args.mode in ("grid", "pair") else f"-{args.mode}"
        dest = OUT / f"{args.package}-{args.scenario}-{rid}{suffix}.json"
        if dest.exists():
            existing = read(dest)
            assert existing["flow_sha256"] == sha(flow_path)
            assert existing["design_sha256"] == sha(design_path)
            assert existing["independent_account_verified"]
            continue
        eligibility = next(r for r in gate["rows"] if r["id"] == rid)
        assert eligibility["status"] == "eligible_conditional_spot_model"
        assert eligibility["original_params_sha256"] == row["params_sha256_canonical"]
        params = dict(row["params"])
        params["muster_cvd"] = eligibility["effective_cvd"]
        if args.mode == "capital06":
            params["deploy_pct"] = .6
        elif args.mode == "capital05":
            params["deploy_pct"] = .5
        fn = run_execution if scenario["next_open_offset"] == 1 else run_delayed
        t0 = time.monotonic()
        result = fn(cs, fs, params, start_ms=start_ms, end_ms=cutoff,
                    fee=scenario["fee_pct"] / 100,
                    slippage=scenario["slippage_pct"] / 100)
        check = verify_account(result, book, cs, start_ms, scenario["next_open_offset"],
                               params.get("deploy_pct", 1.))
        detail = describe(result, cs, check)
        event_keys = [(s["ts"], s["type"], s.get("tranche_pct")) for s in result["signals"]]
        summary = {"schema": "a7-conditional-spot-run-v1", "id": rid,
                   "package": args.package, "scenario": args.scenario,
                   "flow_sha256": sha(flow_path), "design_sha256": sha(design_path),
                   "cutoff_ms": cutoff, "full_cutoff_ms": full_cutoff,
                   "start_ms": start_ms, "mode": args.mode,
                   "historical_api_as_of_proven": False,
                   "independent_account_verified": True,
                   "detail": detail, "signal_events": event_keys,
                   "daily_equity": [[e["at"], e["equity"]] for e in result["equity"]
                                    if e["at"] % 86_400_000 == 0],
                   "signal_event_sha256": hashlib.sha256(json.dumps(event_keys).encode()).hexdigest()}
        atomic_frozen(dest, summary)
        print(args.package, args.scenario, rid, round(result["ende"], 4),
              "book PASS", round(time.monotonic() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
