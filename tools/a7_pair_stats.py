"""Prespecified paired daily statistics for V000 versus V004 only."""

import gzip
import hashlib
import json
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


def main():
    socket.socket.connect = socket.create_connection = blocked
    plan = read(N6 / "plan.json")
    output = {"schema": "a7-paired-statistics-v1", "rows": ["V000", "V004"],
              "selection_adjusted": False,
              "interpretation": "conditional descriptive uncertainty on reused data; not independent validation",
              "plan_sha256": sha(N6 / "plan.json"), "results": []}
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
            output["results"].append({"package": package, "scenario": scenario,
                "summary_sha256": sha(summary_path), "results_sha256": sha(result_path),
                "daily_span": span, "paired": intervals, "comparison": comparison,
                "basis_end_usd": basis["ende"], "e42_end_usd": e42["ende"],
                "previous_N6_end_delta_usd_each": [x["delta_end_usd"] for x in summary["rows"]],
                "previous_N6_U1_identical": intervals == previous["U1"]})
            print(package, scenario, "paired days", span["n"],
                  "N6-U1 identical", intervals == previous["U1"], flush=True)
    dest = DOC / "A7-paired-statistics-v1.json"
    raw = (json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if dest.exists():
        assert dest.read_bytes() == raw
    else:
        dest.write_bytes(raw)


if __name__ == "__main__":
    main()
