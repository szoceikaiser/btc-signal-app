"""Prespecified paired daily statistics for V000 versus V004 only."""

import gzip
import hashlib
import json
import argparse
import math
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from historical_analysis import compare
from historical_stats import daily_pair, paired_bootstrap

DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
N6 = ROOT / "docs" / "nach-6"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(*_args, **_kwargs):
    raise AssertionError("A7 paired statistics are offline")


def numerically_equal(a, b):
    """Compare platform math results without weakening identities or source hashes."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, int) or isinstance(b, int):
        return type(a) is type(b) and a == b
    if isinstance(a, float) and isinstance(b, float):
        return math.isfinite(a) and math.isfinite(b) and math.isclose(
            a, b, rel_tol=1e-10, abs_tol=1e-12)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(numerically_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(numerically_equal(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-cross-platform", action="store_true")
    args = parser.parse_args()
    socket.socket.connect = socket.create_connection = blocked
    plan = read(N6 / "plan.json")
    dest = DOC / "A7-paired-statistics-v1.json"
    frozen = read(dest) if args.verify_cross_platform else None
    output = {"schema": "a7-paired-statistics-v1", "rows": ["V000", "V004"],
              "selection_adjusted": False,
              "interpretation": "conditional descriptive uncertainty on reused data; not independent validation",
              "plan_sha256": sha(N6 / "plan.json"), "results": []}
    if args.verify_cross_platform:
        assert {k: v for k, v in output.items() if k != "results"} == {
            k: v for k, v in frozen.items() if k != "results"}
    for package in ("R0", "R1"):
        old = read(N6 / package / "results.json")
        for scenario in ("S0", "S1", "S2", "S3", "S4"):
            stem = f"A7-targeted-{package}-{scenario}"
            summary_path = DOC / f"{stem}-summary.json"
            result_path = DOC / f"{stem}-results.json.gz"
            summary = read(summary_path)
            full = json.loads(gzip.decompress(result_path.read_bytes()))
            assert [x["id"] for x in full] == ["V000", "V004"]
            assert summary["flow_sha256"] == read(DOC / "A7-auswertbarkeit-v2.json")["flow_data_sha256"]
            assert all(x["independent_account_verified"] for x in summary["rows"])
            basis, e42 = (x["result"] for x in full)
            returns, span = daily_pair(basis, e42)
            intervals = [paired_bootstrap(returns, length) for length in (14, 7, 28)]
            previous = next(x for x in old["results"] if x["start_index"] == 0 and
                            x["scenario"] == scenario)
            assert [x["modelled"]["ende"] for x in summary["rows"]] == [
                x["ende"] for x in previous["rows"]]
            comparison = compare(*(x["modelled"] for x in summary["rows"]))
            row = {"package": package, "scenario": scenario,
                "summary_sha256": sha(summary_path), "results_sha256": sha(result_path),
                "daily_span": span, "paired": intervals, "comparison": comparison,
                "basis_end_usd": basis["ende"], "e42_end_usd": e42["ende"],
                "previous_N6_end_delta_usd_each": [x["delta_end_usd"] for x in summary["rows"]],
                "previous_N6_U1_identical": intervals == previous["U1"]}
            output["results"].append(row)
            if args.verify_cross_platform:
                saved = frozen["results"][len(output["results"])-1]
                assert saved["previous_N6_U1_identical"] is True
                assert numerically_equal(intervals, previous["U1"])
                assert numerically_equal({k: v for k, v in row.items()
                                          if k != "previous_N6_U1_identical"},
                                         {k: v for k, v in saved.items()
                                          if k != "previous_N6_U1_identical"})
            print(package, scenario, "paired days", span["n"],
                  "N6-U1 exact", intervals == previous["U1"], flush=True)
    if args.verify_cross_platform:
        assert len(frozen["results"]) == len(output["results"]) == 10
        print("Cross-platform numeric verification: 10/10, max tolerance 1e-12 absolute")
        return
    raw = (json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if dest.exists():
        assert dest.read_bytes() == raw
    else:
        dest.write_bytes(raw)


if __name__ == "__main__":
    main()
