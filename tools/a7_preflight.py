"""Read-only A7 eligibility inventory. Never runs a return calculation."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
R0 = ROOT.parent / "audit-backups" / "6-abschluss-05208ce" / "eingefrorene-inputs" / "eingaben.json"
R1 = ROOT / "docs" / "nach-6" / "r1-inputs.json"
MANIFEST = DOC / "A7-analysemanifest-v1.json"
OUT = DOC / "A7-auswertbarkeit-v1.json"
STEP = 14_400_000


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def inspect_data(path, expected):
    assert sha(path) == expected, f"Input hash changed: {path}"
    data = load(path)
    cs, fs = data["candles"], data["flow"]
    assert len(cs) == len(fs)
    assert all(c["ts"] == f["ts"] for c, f in zip(cs, fs))
    assert all(cs[i + 1]["ts"] - cs[i]["ts"] == STEP for i in range(len(cs) - 1))
    assert all(math.isfinite(v) for f in fs for v in f.values() if type(v) in (int, float))
    closed = [i for i, c in enumerate(cs) if c["ts"] + STEP <= data["ende"]]
    assert closed == list(range(len(closed)))
    fields = ["spot_cvd", "fut_cvd", "oi", "oi_btc", "funding", "long_liq", "short_liq", "long_pct"]
    missing_provenance = {
        name: sum(not isinstance(f.get("provenance"), dict)
                  or not isinstance(f["provenance"].get(name), dict)
                  or f["provenance"][name].get("coverage") not in {"observed", "carried", "missing", "stale"}
                  for f in fs[: len(closed)])
        for name in fields
    }
    return {
        "path": str(path), "sha256": sha(path), "start_ms": data["start"],
        "end_exclusive_ms": data["ende"], "bars_total": len(cs),
        "bars_closed": len(closed), "trailing_partial_bars": len(cs) - len(closed),
        "trade_bars_closed": sum(cs[i]["ts"] >= data["start"] for i in closed),
        "missing_field_provenance_closed_bars": missing_provenance,
        "earliest_bar_open_ms": cs[0]["ts"], "latest_closed_bar_open_ms": cs[len(closed) - 1]["ts"],
    }


def main():
    manifest = load(MANIFEST)
    assert manifest["row_counts"]["unique_original_configs"] == 86
    data = {
        "R0": inspect_data(R0, manifest["frozen_data"]["R0_sha256"]),
        "R1": inspect_data(R1, manifest["frozen_data"]["R1_sha256"]),
    }
    a2 = load(DOC / "A2-ABLEITUNG-v1.json")
    a3 = load(DOC / "A3-ABLEITUNG-v1.json")
    assert not a2["derivation"]["historical_return_calculated"]
    assert a3["scope"] == "synthetic offline counterexamples; no historical return measurement"
    rows = []
    for row in manifest["rows"]:
        reasons = [
            "F07/D02: R0/R1 numeric flow lacks observed/available-at time and coverage metadata; "
            "A2 synthetic derivation does not reconstruct the historic prefix",
        ]
        if row["id"] == "V035":
            reasons.append("F02: Short/derivative row has no supported historical instrument, "
                           "funding payment book or causal strategy fills")
        rows.append({
            "id": row["id"], "legacy_original_params_sha256": row["params_sha256_canonical"],
            "R0_corrected_causal": "blocked", "R1_corrected_causal": "blocked",
            "reasons": reasons,
            "legacy_diagnostic": "existing original audit results retained; not a corrected A7 return",
        })
    result = {
        "schema": "a7-eligibility-v1", "manifest_sha256": sha(MANIFEST),
        "base_commit": manifest["base_commit"], "data": data,
        "A2_derivation": "A2-ABLEITUNG-v1.json: contract and synthetic countercases; no historical provenance series",
        "A3_derivation": "A3-ABLEITUNG-v1.json: synthetic countercases; historical market basket unverified",
        "corrected_return_run_allowed": False,
        "blocked_rows": 86, "rows": rows,
        "scope": "Preflight only. No strategy run, portfolio return, model ranking, paired statistic or inferred zero fills.",
        "required_to_unblock": [
            "A separately versioned historical flow derivation with per-field source, observed/available time, age and coverage for every required prefix; no future backfill or assumed observed zeros",
            "For V035, independently sufficient historical instrument, price, funding-payment and causal fill contract; otherwise retain explicit exclusion",
            "Recheck A3 daily completeness and any requested multi-market basket/units before the affected run",
        ],
    }
    encoded = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if OUT.exists():
        assert OUT.read_bytes() == encoded, "Existing eligibility inventory differs"
    else:
        OUT.write_bytes(encoded)
    print(f"A7 preflight: {len(rows)} original rows inventoried, 86 corrected causal runs blocked; sha256 {sha(OUT)}")
    for name, info in data.items():
        print(f"{name}: {info['bars_closed']} closed bars; missing provenance per field: "
              f"{info['missing_field_provenance_closed_bars']}")


if __name__ == "__main__":
    main()
