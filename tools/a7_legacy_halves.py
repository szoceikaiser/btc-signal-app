"""Recompute the old level diagnostic's independently started halves."""

import argparse
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
OUT = DOC / "A7-legacy-halves"
STEP = 14_400_000


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(*_args, **_kwargs):
    raise AssertionError("A7 legacy halves are offline")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", choices=["R0", "R1"], required=True)
    args = parser.parse_args()
    socket.socket.connect = socket.create_connection = blocked
    design_path = DOC / "A7-analysemanifest-v1.json"
    flow_path = DOC / "A7-flow-modeled-v2.json.gz"
    gate = read(DOC / "A7-auswertbarkeit-v2.json")
    design = read(design_path)
    assert gate["manifest_sha256"] == sha(design_path)
    assert gate["flow_data_sha256"] == sha(flow_path)
    data = json.loads(gzip.decompress(flow_path.read_bytes()))
    cutoff = (data["ende"] if args.package == "R1" else
              read(ROOT / "docs" / "nach-6" / "R0" / "results.json")["cutoff"])
    midpoint = data["start"] + (cutoff - data["start"]) // 2
    cs = [Candle(**c) for c in data["candles"] if c["ts"] + STEP <= cutoff]
    fs = [FlowPoint(**f) for f in data["flow"][:len(cs)]]
    assert len(cs) == len(fs) and all(c.ts == f.ts for c, f in zip(cs, fs))
    book_path = ROOT / "tools" / "a7_independent_book.py"
    assert sha(book_path) == read(ROOT / "docs" / "nach-6" / "plan.json")["book_sha256"]
    spec = importlib.util.spec_from_file_location("a7_independent_legacy_book", book_path)
    book = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(book)
    book.selfcheck()
    OUT.mkdir(exist_ok=True)
    for row in design["rows"]:
        rid = row["id"]
        if rid == "V035":
            continue
        dest = OUT / f"{args.package}-{rid}.json"
        if dest.exists():
            assert read(dest)["flow_sha256"] == sha(flow_path)
            continue
        eligibility = next(x for x in gate["rows"] if x["id"] == rid)
        assert eligibility["status"] == "eligible_conditional_spot_model"
        params = dict(row["params"])
        params["muster_cvd"] = eligibility["effective_cvd"]
        halves = []
        for start, end in ((data["start"], midpoint), (midpoint, cutoff)):
            count = sum(c.ts + STEP <= end for c in cs)
            sig = run_backtest(cs[:count], fs[:count], params, start_ms=start)
            account = book.account(sig, cs[:count], start, fee=.001, slip=0, mode="level")
            halves.append({"start_ms": start, "end_ms": end,
                           "signal_count": len(sig), "account":
                           {k: v for k, v in account.items() if k not in ("fills", "lots", "path")}})
        obj = {"schema": "a7-corrected-legacy-halves-v1", "id": rid,
               "package": args.package, "flow_sha256": sha(flow_path),
               "design_sha256": sha(design_path), "book_sha256": sha(book_path),
               "historical_api_as_of_proven": False, "execution_claim": False,
               "halves": halves}
        raw = (json.dumps(obj, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False)+"\n").encode()
        temp = dest.with_suffix(".tmp")
        temp.write_bytes(raw)
        os.replace(temp, dest)
        print(args.package, rid, [round(x["account"]["return_pct"], 3)
                                  for x in halves], flush=True)
    assert len(list(OUT.glob(f"{args.package}-*.json"))) == 85


if __name__ == "__main__":
    main()
