"""Fixed intermediate signal bands for A7 V000/V004; no portfolio returns."""

from collections import Counter
import gzip
import hashlib
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
    raise AssertionError("A7 event attribution has no network access")


def events(signals):
    return [(s["ts"], s["type"], s.get("tranche_pct")) for s in signals]


def diff(a, b):
    # a -> b
    left, right = Counter(a), Counter(b)
    return {"before_count": len(a), "after_count": len(b),
            "removed": sorted([list(x) for x in (left - right).elements()]),
            "added": sorted([list(x) for x in (right - left).elements()])}


def main():
    socket.socket.connect = socket.create_connection = blocked
    design_path = DOC / "A7-analysemanifest-v1.json"
    flow_path = DOC / "A7-flow-modeled-v2.json.gz"
    old_path = ROOT / "docs" / "nach-6" / "r1-inputs.json"
    design, old = read(design_path), read(old_path)
    modeled = json.loads(gzip.decompress(flow_path.read_bytes()))
    assert len(old["candles"]) == len(modeled["candles"])
    assert all(a["ts"] == b["ts"] for a, b in zip(old["candles"], modeled["candles"]))
    output = {"schema": "a7-event-attribution-v1", "scope": "signal bands, no returns",
              "design_sha256": sha(design_path), "modeled_flow_sha256": sha(flow_path),
              "numeric_R1_sha256": sha(old_path), "historical_api_as_of_proven": False,
              "rows": []}
    for package in ("R0", "R1"):
        cutoff = (read(ROOT / "docs" / "nach-6" / "R0" / "results.json")["cutoff"]
                  if package == "R0" else modeled["ende"])
        cs = [Candle(**c) for c in modeled["candles"] if c["ts"] + STEP <= cutoff]
        numeric_fs = [FlowPoint(**f) for f in old["flow"][:len(cs)]]
        modeled_fs = [FlowPoint(**f) for f in modeled["flow"][:len(cs)]]
        for rid in ("V000", "V004"):
            row = next(r for r in design["rows"] if r["id"] == rid)
            old_params = dict(row["params"])
            alt_numeric = events(run_backtest(cs, numeric_fs, old_params,
                                              start_ms=modeled["start"]))
            alt_modeled = events(run_backtest(cs, modeled_fs, old_params,
                                              start_ms=modeled["start"]))
            new_params = dict(old_params)
            new_params["muster_cvd"] = "usd"
            usd_modeled = events(run_backtest(cs, modeled_fs, new_params,
                                              start_ms=modeled["start"]))
            original = None
            if package == "R0":
                old_result_path = (ROOT.parent / "audit-work" / "docs" /
                                   "audit-2026-09-27" / "grid" / f"{rid}.json")
                original = events(read(old_result_path)["signals"])
            obj = {"package": package, "id": rid,
                   "old_audit_to_current_numeric_alt": diff(original, alt_numeric)
                       if original is not None else None,
                   "numeric_alt_to_modeled_alt": diff(alt_numeric, alt_modeled),
                   "modeled_alt_to_modeled_usd": diff(alt_modeled, usd_modeled),
                   "signal_events": {"current_numeric_alt": alt_numeric,
                                     "modeled_alt": alt_modeled,
                                     "modeled_usd": usd_modeled}}
            output["rows"].append(obj)
            print(package, rid, [(k, len(v["added"]), len(v["removed"]))
                   for k, v in obj.items() if isinstance(v, dict) and "added" in v],
                  flush=True)
    dest = DOC / "A7-event-attribution-v1.json"
    raw = (json.dumps(output, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()
    if dest.exists():
        assert dest.read_bytes() == raw
    else:
        dest.write_bytes(raw)


if __name__ == "__main__":
    main()
