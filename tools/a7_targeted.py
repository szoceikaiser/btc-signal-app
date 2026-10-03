"""Fixed A7 V000/V004 pair on the separately derived, modeled A2 flow."""

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "tools"))
from backtest import run_execution
from execution_delayed import run_delayed
from historical_analysis import describe, verify_account
from strategy_core import Candle, FlowPoint

DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
N6 = ROOT / "docs" / "nach-6"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def frozen(path, data):
    if path.exists():
        existing = path.read_bytes()
        if path.name.endswith("-summary.json"):
            # Wall-clock duration is observational, not part of the model result.
            def without_duration(raw):
                value = json.loads(raw)
                for row in value["rows"]:
                    row.pop("elapsed_seconds", None)
                return value
            assert without_duration(existing) == without_duration(data), path
        elif path.name.endswith(".json.gz"):
            assert json.loads(gzip.decompress(existing)) == json.loads(gzip.decompress(data)), path
        else:
            assert existing == data, path
    else:
        path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", choices=["R0", "R1"], default="R1")
    parser.add_argument("--scenario", choices=["S0", "S1", "S2", "S3", "S4"], default="S0")
    args = parser.parse_args()
    def network_blocked(*_args, **_kwargs):
        raise AssertionError("A7 targeted run is offline")
    socket.socket.connect = socket.create_connection = network_blocked
    design = read(DOC / "A7-analysemanifest-v1.json")
    gate = read(DOC / "A7-auswertbarkeit-v2.json")
    flow_manifest = read(DOC / "A7-flow-modeled-manifest-v2.json")
    path = DOC / "A7-flow-modeled-v2.json.gz"
    assert gate["flow_data_sha256"] == flow_manifest["compressed_sha256"] == sha(path)
    data = json.loads(gzip.decompress(path.read_bytes()))
    n6_plan = read(N6 / "plan.json")
    scenario = next(s for s in n6_plan["scenarios"] if s["id"] == args.scenario)
    cutoff = data["ende"] if args.package == "R1" else read(N6 / "R0" / "results.json")["cutoff"]
    cs = [Candle(**c) for c in data["candles"] if c["ts"] + 14_400_000 <= cutoff]
    fs = [FlowPoint(**f) for f in data["flow"][:len(cs)]]
    assert len(cs) == len(fs)
    rows = [next(r for r in design["rows"] if r["id"] == id) for id in ("V000", "V004")]
    book_path = ROOT / "tools" / "a7_independent_book.py"
    assert sha(book_path) == n6_plan["book_sha256"]
    spec = importlib.util.spec_from_file_location("a7_independent_audit_book", book_path)
    book = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(book)
    book.selfcheck()
    old = read(N6 / args.package / "results.json")
    old_pair = next(item for item in old["results"] if item["start_index"] == 0 and
                    item["scenario"] == args.scenario)
    results = []
    summaries = []
    for i, row in enumerate(rows):
        params = dict(row["params"])
        params["muster_cvd"] = "usd"
        assert gate["rows"][int(row["id"][1:])]["status"] == "eligible_conditional_spot_model"
        start = time.monotonic()
        fn = run_execution if scenario["next_open_offset"] == 1 else run_delayed
        result = fn(cs, fs, params, start_ms=data["start"], end_ms=cutoff,
                    fee=scenario["fee_pct"] / 100, slippage=scenario["slippage_pct"] / 100)
        check = verify_account(result, book, cs, data["start"], scenario["next_open_offset"])
        detail = describe(result, cs, check)
        before = old_pair["rows"][i]
        summaries.append({"id": row["id"], "modelled": detail,
                          "previous_N6_end": before["ende"],
                          "delta_end_usd": detail["ende"] - before["ende"],
                          "elapsed_seconds": time.monotonic() - start,
                          "independent_account_verified": True})
        results.append({"id": row["id"], "result": result})
        print(args.package, args.scenario, row["id"], "end", round(result["ende"], 4),
              "delta_N6", round(detail["ende"] - before["ende"], 4),
              "book PASS", flush=True)
    summary = {"schema": "a7-targeted-v1", "package": args.package,
               "scenario": args.scenario, "flow_sha256": sha(path),
               "design_sha256": sha(DOC / "A7-analysemanifest-v1.json"),
               "source_N6_summary_sha256": sha(N6 / args.package / "results.json"),
               "historical_api_as_of_proven": False, "rows": summaries,
               "delta_pair_usd": summaries[1]["modelled"]["ende"] - summaries[0]["modelled"]["ende"],
               "returns_calculated": True}
    stem = f"A7-targeted-{args.package}-{args.scenario}"
    frozen(DOC / f"{stem}-summary.json", (json.dumps(summary, indent=2, ensure_ascii=False,
        allow_nan=False) + "\n").encode("utf-8"))
    raw = json.dumps(results, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode("utf-8")
    frozen(DOC / f"{stem}-results.json.gz", gzip.compress(raw, compresslevel=6, mtime=0))


if __name__ == "__main__":
    main()
