"""Freeze the original A7 comparison family before any new return calculation.

This reads the immutable original audit checkout and the A6 checkout. It never
fetches market data or evaluates a strategy. Re-running must reproduce the
same manifest byte for byte.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT.parent / "audit-work" / "docs" / "audit-2026-09-27"
DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
OUT = DOC / "A7-analysemanifest-v1.json"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main():
    grid_path = AUDIT / "gitter-plan.json"
    structure_paths = sorted((AUDIT / "struktur").glob("S[0-9][0-9][0-9].json"))
    capital_path = AUDIT / "ERGAENZUNGSPLAN.md"
    structure_plan_path = AUDIT / "STRUKTURPLAN.md"
    original_plan_path = AUDIT / "PLAN.md"
    n6_plan_path = ROOT / "docs" / "nach-6" / "plan.json"
    a5_path = DOC / "A5-historical-eligibility-v1.json"
    r1_path = ROOT / "docs" / "nach-6" / "r1-inputs.json"
    grid = read(grid_path)
    n6 = read(n6_plan_path)
    a5 = read(a5_path)
    assert len(grid["rows"]) == 79
    assert len(structure_paths) == 8
    assert len(a5["rows"]) == 86
    assert n6["packages"]["R1"]["input_sha256"] == digest(r1_path)

    rows = []
    seen = {}
    aliases = []
    for source in [*grid["rows"], *(read(p) for p in structure_paths)]:
        row_id = source["id"]
        params = source["params"]
        key = hashlib.sha256(canonical(params).encode("utf-8")).hexdigest()
        if key in seen:
            aliases.append({"id": row_id, "identical_to": seen[key]})
            continue
        seen[key] = row_id
        rows.append({
            "id": row_id,
            "source": "original_grid" if row_id.startswith("V") else "original_structure",
            "groups": source.get("groups", ["E4_structure"]),
            "labels": source.get("labels", [row_id]),
            "params": params,
            "params_sha256_canonical": key,
            "corrected_cvd_policy": "A2_usd_diagnostic" if params["muster_cvd"] == "alt" else "already_usd",
            "f02_status": "blocked_short_derivative" if params["bias_short"] else "spot_model_only",
        })
    assert len(rows) == 86 and aliases == [{"id": "S004", "identical_to": "V000"}]
    assert {r["id"] for r in rows} == {r["id"] for r in a5["rows"]}
    assert all(r["params"] == next(a["params"] for a in a5["rows"] if a["id"] == r["id"])
               for r in rows)

    # Equal original signal bands are descriptive aliases, not independent
    # replications and not guaranteed equal under the corrected A2/A3 model.
    signal_groups = defaultdict(list)
    for row in rows:
        original = AUDIT / ("grid" if row["id"].startswith("V") else "struktur") / f"{row['id']}.json"
        signal_groups[hashlib.sha256(canonical(read(original)["signals"]).encode()).hexdigest()].append(row["id"])
    original_equal_signals = [members for members in signal_groups.values() if len(members) > 1]

    original_costs = grid["costs"]
    assert len(original_costs) == 4
    assert [c["fill"] for c in original_costs] == ["level", "close", "next_open", "delay_4h"]
    assert len(n6["scenarios"]) == 5
    manifest = {
        "schema": "a7-analysis-manifest-v1",
        "stage": "A7",
        "base_commit": "8b6af70b1897e8aefff5552f878297cc0090ef26",
        "original_audit_commit": "ccf2b01c0578346f325261e72445b7375a9ac706",
        "declaration": "Original family fixed before A7 return measurement; no new candidates or outcome-based parameter choice",
        "source_sha256": {
            str(p.relative_to(ROOT.parent)).replace("\\", "/"): digest(p)
            for p in [original_plan_path, capital_path, structure_plan_path, grid_path,
                      *structure_paths, n6_plan_path, a5_path, r1_path,
                      DOC / "A2-ABLEITUNG-v1.json", DOC / "A3-ABLEITUNG-v1.json"]
        },
        "rows": rows,
        "row_counts": {"original_grid": 79, "structure_labels": 8, "identical_parameter_aliases": 1,
                       "unique_original_configs": 86},
        "identical_parameter_aliases": aliases,
        "original_equal_signal_groups": original_equal_signals,
        "equal_signal_scope": "Original audit signal arrays only; no independence claim and no corrected-model equivalence claim",
        "capital_separate": {
            "signal_row": "V000", "deploy_pct": [1.0, 0.6, 0.5],
            "status": "separately preregistered in ERGAENZUNGSPLAN.md; not three new trading configurations",
        },
        "frozen_data": {
            "last_observation_exclusive_ms": 1790683200000,
            "last_observation_exclusive_utc": "2026-09-29T12:00:00Z",
            "R0_sha256": n6["packages"]["R0"]["input_sha256"],
            "R1_sha256": n6["packages"]["R1"]["input_sha256"],
            "R0_R1_originals_immutable": True,
            "A2_A3_derivations": "new versioned artifacts only; original numeric flow without provenance is not proof of historical availability",
        },
        "comparison_lanes": {
            "legacy_diagnostic": {"params": "exact original row params", "costs": original_costs,
                                  "ranking_with_causal": False,
                                  "meaning": "retrospective level/close or historical signal intent only; no executable-order claim"},
            "causal_spot": {"params": "same original row IDs and all original trading parameters; A2 CVD correction applied as a declared technical translation from alt to usd, never chosen by return",
                            "scenarios": n6["scenarios"], "fee": 0.001, "start_cash_usd": 10000,
                            "instrument": "spot_btc_usd", "ranking_with_legacy": False,
                            "unsupported": ["V035"]},
        },
        "prespecified_scenarios": {"basis": "V000", "E42_only": "V004",
                                    "source": "original G1/G2 and fixed Nach-6 R0 pair; other E42 combinations remain their original row IDs"},
        "time_and_risk": {
            "bars": "closed UTC 4h only", "months": "every UTC calendar month including marked partial endpoints",
            "halves": "two separately started halves under original audit definition",
            "thirds": "continuous path and predeclared fresh starts at indices 503/1006 for R0, 507/1014 for R1",
            "risk": "same close-to-close drawdown within a lane; intrabar OHLC range separately marked as bounds",
            "costs": "fees and slippage per scenario; independent lot/cash verification required",
        },
        "paired_statistics": "Only fixed V000/E42 matched daily returns under the original Nach-6 contract; no selection adjustment",
        "inference": "Earlier selection, unknown full search family and reused months remain limits; no new independent sample",
        "preflight_required": True,
        "returns_calculated_at_manifest_creation": False,
    }
    encoded = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if OUT.exists():
        assert OUT.read_bytes() == encoded, "Frozen A7 manifest differs"
    else:
        OUT.write_bytes(encoded)
    print(f"A7 manifest frozen: {len(rows)} unique rows; {len(aliases)} exact alias; "
          f"{len(original_equal_signals)} original equal-signal groups; sha256 {digest(OUT)}")


if __name__ == "__main__":
    main()
