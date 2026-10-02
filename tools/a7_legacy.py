"""Separate A7 diagnostic: corrected A2 signals under four old fill conventions.

Level and same-close values are retrospective diagnostics, not executable orders.
The result family is never ranked together with the closed-loop V1 runs.
"""

import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "engine"), str(ROOT / "tools")]
from backtest import run_backtest
from strategy_core import Candle, FlowPoint

DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
OUT = DOC / "A7-legacy"
STEP = 14_400_000


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(*_args, **_kwargs):
    raise AssertionError("A7 legacy diagnostic has no network access")


def events(signals):
    return [(s["ts"], s["type"], s.get("tranche_pct")) for s in signals]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", choices=["R0", "R1"], required=True)
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
    data = json.loads(gzip.decompress(flow_path.read_bytes()))
    cutoff = (data["ende"] if args.package == "R1" else
              read(ROOT / "docs" / "nach-6" / "R0" / "results.json")["cutoff"])
    cs = [Candle(**c) for c in data["candles"] if c["ts"] + STEP <= cutoff]
    fs = [FlowPoint(**f) for f in data["flow"][:len(cs)]]
    assert all(c.ts == f.ts for c, f in zip(cs, fs))
    book_path = ROOT / "tools" / "a7_independent_book.py"
    assert sha(book_path) == read(ROOT / "docs" / "nach-6" / "plan.json")["book_sha256"]
    spec = importlib.util.spec_from_file_location("a7_independent_legacy_book", book_path)
    book = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(book)
    book.selfcheck()
    costs = design["comparison_lanes"]["legacy_diagnostic"]["costs"]
    assert len(costs) == 4
    OUT.mkdir(exist_ok=True)
    for row in design["rows"]:
        rid = row["id"]
        if rid == "V035" or (args.from_id and rid < args.from_id) or (
                args.only_id and rid != args.only_id):
            continue
        dest = OUT / f"{args.package}-{rid}.json"
        if dest.exists():
            old_result = read(dest)
            assert old_result["flow_sha256"] == sha(flow_path)
            assert old_result["design_sha256"] == sha(design_path)
            continue
        eligibility = next(r for r in gate["rows"] if r["id"] == rid)
        assert eligibility["status"] == "eligible_conditional_spot_model"
        params = dict(row["params"])
        params["muster_cvd"] = eligibility["effective_cvd"]
        sig = run_backtest(cs, fs, params, start_ms=data["start"])
        new_events = events(sig)
        results = []
        for case in costs:
            result = book.account(sig, cs, data["start"], fee=case["fee"],
                                  slip=case["slip"], mode=case["fill"])
            results.append({"case": case, "account": {k: v for k, v in result.items()
                            if k not in ("fills", "lots", "path")}})
        previous = None
        if args.package == "R0":
            old_path = (ROOT.parent / "audit-work" / "docs" / "audit-2026-09-27" /
                        ("grid" if rid.startswith("V") else "struktur") / f"{rid}.json")
            old = read(old_path)
            previous = events(old["signals"])
            a, b = Counter(new_events), Counter(previous)
            differences = {"previous_source": str(old_path.relative_to(ROOT.parent)),
                           "previous_source_sha256": sha(old_path),
                           "previous_count": len(previous), "new_count": len(new_events),
                           "added": sorted([list(x) for x in (a - b).elements()]),
                           "removed": sorted([list(x) for x in (b - a).elements()])}
        obj = {"schema": "a7-corrected-legacy-diagnostic-v1", "id": rid,
               "package": args.package, "historical_api_as_of_proven": False,
               "execution_claim": False, "flow_sha256": sha(flow_path),
               "design_sha256": sha(design_path), "cutoff_ms": cutoff,
               "signal_events": new_events, "differences_to_original_R0": differences
               if args.package == "R0" else None, "cases": results}
        raw = (json.dumps(obj, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False) + "\n").encode()
        temp = dest.with_suffix(".tmp")
        temp.write_bytes(raw)
        os.replace(temp, dest)
        print(args.package, rid, len(sig), [round(r["account"]["end"], 2)
                                          for r in results], flush=True)


if __name__ == "__main__":
    main()
