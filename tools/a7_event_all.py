"""Intermediate R0 signal comparisons for every prespecified eligible row."""

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
OUT = DOC / "A7-events-R0"
STEP = 14_400_000


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(*_args, **_kwargs):
    raise AssertionError("A7 intermediate event run is offline")


def events(signals):
    return [(s["ts"], s["type"], s.get("tranche_pct")) for s in signals]


def difference(a, b):
    left, right = Counter(tuple(x) for x in a), Counter(tuple(x) for x in b)
    return {"before_count": len(a), "after_count": len(b),
            "removed": sorted([list(x) for x in (left-right).elements()]),
            "added": sorted([list(x) for x in (right-left).elements()])}


def main():
    socket.socket.connect = socket.create_connection = blocked
    design_path = DOC / "A7-analysemanifest-v1.json"
    modeled_path = DOC / "A7-flow-modeled-v2.json.gz"
    numeric_path = ROOT / "docs" / "nach-6" / "r1-inputs.json"
    design = read(design_path)
    numeric = read(numeric_path)
    modeled = json.loads(gzip.decompress(modeled_path.read_bytes()))
    assert read(DOC / "A7-flow-modeled-manifest-v2.json")["numeric_differences_against_R1"] == {}
    cutoff = read(ROOT / "docs" / "nach-6" / "R0" / "results.json")["cutoff"]
    cs = [Candle(**c) for c in modeled["candles"] if c["ts"]+STEP <= cutoff]
    numeric_fs = [FlowPoint(**f) for f in numeric["flow"][:len(cs)]]
    modeled_fs = [FlowPoint(**f) for f in modeled["flow"][:len(cs)]]
    assert [c.ts for c in cs] == [f.ts for f in numeric_fs] == [f.ts for f in modeled_fs]
    OUT.mkdir(exist_ok=True)
    for row in design["rows"]:
        rid = row["id"]
        if rid == "V035":
            continue
        dest = OUT / f"{rid}.json"
        if dest.exists():
            obj = read(dest)
            assert obj["design_sha256"] == sha(design_path)
            assert obj["modeled_flow_sha256"] == sha(modeled_path)
            continue
        params = dict(row["params"])
        alt_numeric = events(run_backtest(cs, numeric_fs, params,
                                          start_ms=modeled["start"]))
        alt_modeled = events(run_backtest(cs, modeled_fs, params,
                                          start_ms=modeled["start"]))
        corrected = read(DOC / "A7-legacy" / f"R0-{rid}.json")["signal_events"]
        source = (ROOT.parent / "audit-work" / "docs" / "audit-2026-09-27" /
                  ("grid" if rid.startswith("V") else "struktur") / f"{rid}.json")
        original = events(read(source)["signals"])
        obj = {"schema": "a7-R0-intermediate-events-v1", "id": rid,
               "design_sha256": sha(design_path), "modeled_flow_sha256": sha(modeled_path),
               "numeric_R1_sha256": sha(numeric_path), "original_result_sha256": sha(source),
               "old_audit_to_current_numeric_alt": difference(original, alt_numeric),
               "current_numeric_alt_to_modeled_alt": difference(alt_numeric, alt_modeled),
               "modeled_alt_to_corrected_cvd": difference(alt_modeled, corrected),
               "events_current_numeric_alt": alt_numeric,
               "events_modeled_alt": alt_modeled}
        dest.write_bytes((json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"))+"\n").encode("utf-8"))
        print(rid, [(len(obj[k]["added"]), len(obj[k]["removed"])) for k in (
            "old_audit_to_current_numeric_alt", "current_numeric_alt_to_modeled_alt",
            "modeled_alt_to_corrected_cvd")], flush=True)
    assert len(list(OUT.glob("*.json"))) == 85


if __name__ == "__main__":
    main()
