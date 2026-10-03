"""Historical capital fractions in the separate four-case legacy diagnostic."""

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from backtest import run_backtest
from strategy_core import Candle, FlowPoint

DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
STEP = 14_400_000


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(*_args, **_kwargs):
    raise AssertionError("A7 legacy capital analysis is offline")


def main():
    socket.socket.connect = socket.create_connection = blocked
    design_path = DOC / "A7-analysemanifest-v1.json"
    flow_path = DOC / "A7-flow-modeled-v2.json.gz"
    design = read(design_path)
    data = json.loads(gzip.decompress(flow_path.read_bytes()))
    row = next(r for r in design["rows"] if r["id"] == "V000")
    cases = design["comparison_lanes"]["legacy_diagnostic"]["costs"]
    book_path = ROOT / "tools" / "a7_independent_book.py"
    assert sha(book_path) == read(ROOT / "docs" / "nach-6" / "plan.json")["book_sha256"]
    spec = importlib.util.spec_from_file_location("a7_legacy_capital_book", book_path)
    book = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(book)
    book.selfcheck()
    output = {"schema": "a7-legacy-capital-v1", "row": "V000",
              "flow_sha256": sha(flow_path), "design_sha256": sha(design_path),
              "historical_execution_claim": False, "results": []}
    for package in ("R0", "R1"):
        cutoff = (read(ROOT / "docs" / "nach-6" / "R0" / "results.json")["cutoff"]
                  if package == "R0" else data["ende"])
        cs = [Candle(**c) for c in data["candles"] if c["ts"]+STEP <= cutoff]
        fs = [FlowPoint(**f) for f in data["flow"][:len(cs)]]
        params = dict(row["params"])
        params["muster_cvd"] = "usd"
        signals = run_backtest(cs, fs, params, start_ms=data["start"])
        for fraction in (1., .6, .5):
            results = []
            for case in cases:
                account = book.account(signals, cs, data["start"], fee=case["fee"],
                                       slip=case["slip"], mode=case["fill"],
                                       deploy=fraction)
                results.append({"case": case, "account": {k: v for k, v in account.items()
                                if k not in ("fills", "lots", "path")}})
            output["results"].append({"package": package, "fraction": fraction,
                                      "cases": results})
            print(package, fraction, [round(x["account"]["end"], 2) for x in results],
                  flush=True)
    dest = DOC / "A7-legacy-capital-v1.json"
    raw = (json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False)+"\n").encode()
    if dest.exists():
        assert dest.read_bytes() == raw
    else:
        dest.write_bytes(raw)


if __name__ == "__main__":
    main()
