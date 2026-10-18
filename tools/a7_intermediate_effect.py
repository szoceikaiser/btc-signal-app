"""Attribute the two remaining A2 signal changes to conditional S0 balances."""

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "engine"), str(ROOT / "tools")]
from backtest import run_execution
from historical_analysis import describe, verify_account
from strategy_core import Candle, FlowPoint

DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
STEP = 14_400_000


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(*_args, **_kwargs):
    raise AssertionError("A7 intermediate comparison is offline")


def main():
    socket.socket.connect = socket.create_connection = blocked
    design_path = DOC / "A7-analysemanifest-v1.json"
    flow_path = DOC / "A7-flow-modeled-v2.json.gz"
    numeric_path = ROOT / "docs" / "nach-6" / "r1-inputs.json"
    design = read(design_path)
    gate = read(DOC / "A7-auswertbarkeit-v2.json")
    assert gate["manifest_sha256"] == sha(design_path)
    assert gate["flow_data_sha256"] == sha(flow_path)
    modeled = json.loads(gzip.decompress(flow_path.read_bytes()))
    numeric = read(numeric_path)
    assert read(DOC / "A7-flow-modeled-manifest-v2.json")["numeric_differences_against_R1"] == {}
    plan = read(ROOT / "docs" / "nach-6" / "plan.json")
    scenario = next(s for s in plan["scenarios"] if s["id"] == "S0")
    assert scenario["next_open_offset"] == 1
    book_path = ROOT / "tools" / "a7_independent_book.py"
    assert sha(book_path) == plan["book_sha256"]
    spec = importlib.util.spec_from_file_location("a7_independent_audit_book", book_path)
    book = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(book)
    book.selfcheck()
    output = {"schema": "a7-intermediate-A2-S0-v1", "historical_api_as_of_proven": False,
              "scope": "conditional spot model; no historical as-of or execution claim",
              "scenario": "S0", "design_sha256": sha(design_path),
              "modeled_flow_sha256": sha(flow_path), "numeric_R1_sha256": sha(numeric_path),
              "book_sha256": sha(book_path), "results": []}
    for package in ("R0", "R1"):
        cutoff = (modeled["ende"] if package == "R1" else
                  read(ROOT / "docs" / "nach-6" / "R0" / "results.json")["cutoff"])
        cs = [Candle(**c) for c in modeled["candles"] if c["ts"] + STEP <= cutoff]
        inputs = {"numeric_alt": numeric["flow"][:len(cs)],
                  "modeled_alt": modeled["flow"][:len(cs)]}
        for rid in ("V050", "V075"):
            row = next(r for r in design["rows"] if r["id"] == rid)
            outcomes = {}
            for name, records in inputs.items():
                params = dict(row["params"])
                fs = [FlowPoint(**f) for f in records]
                assert all(c.ts == f.ts for c, f in zip(cs, fs))
                result = run_execution(cs, fs, params, start_ms=modeled["start"],
                                       end_ms=cutoff, fee=scenario["fee_pct"] / 100,
                                       slippage=scenario["slippage_pct"] / 100)
                check = verify_account(result, book, cs, modeled["start"], 1)
                detail = describe(result, cs, check)
                outcomes[name] = {"end_usd": detail["ende"],
                                  "return_pct": detail["rendite_pct"],
                                  "fees_usd": detail["fees"],
                                  "fills": check["fills"],
                                  "signal_count": len(result["signals"]),
                                  "result_sha256": detail["result_sha256"],
                                  "independent_book_verified": True}
            corrected = read(DOC / "A7-runs" / f"{package}-S0-{rid}.json")
            assert corrected["independent_account_verified"]
            outcomes["modeled_corrected_cvd"] = {
                "end_usd": corrected["detail"]["ende"],
                "return_pct": corrected["detail"]["rendite_pct"],
                "fees_usd": corrected["detail"]["fees"],
                "fills": corrected["detail"]["verification"]["fills"],
                "signal_count": len(corrected["signal_events"]),
                "result_sha256": corrected["detail"]["result_sha256"],
                "independent_book_verified": True}
            output["results"].append({"package": package, "id": rid,
                 "cutoff_ms": cutoff, "outcomes": outcomes,
                 "numeric_to_modeled_delta_usd": outcomes["modeled_alt"]["end_usd"]-
                                                 outcomes["numeric_alt"]["end_usd"],
                 "cvd_delta_usd": outcomes["modeled_corrected_cvd"]["end_usd"]-
                                  outcomes["modeled_alt"]["end_usd"]})
    dest = DOC / "A7-intermediate-A2-S0-v1.json"
    raw = (json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if dest.exists():
        assert dest.read_bytes() == raw
    else:
        dest.write_bytes(raw)
    print([(x["package"], x["id"], round(x["numeric_to_modeled_delta_usd"], 6),
            round(x["cvd_delta_usd"], 6)) for x in output["results"]])


if __name__ == "__main__":
    main()
