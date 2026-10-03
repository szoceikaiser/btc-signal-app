"""Review modeled A7 source coverage before any historical return run."""

import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original = load(DOC / "A7-analysemanifest-v1.json")
    source = load(DOC / "A7-flow-modeled-manifest-v2.json")
    data_path = DOC / "A7-flow-modeled-v2.json.gz"
    assert source["compressed_sha256"] == sha(data_path)
    data = json.loads(gzip.decompress(data_path.read_bytes()))
    assert source["all_bars"] == len(data["flow"]) == len(data["candles"]) == 2493
    assert source["active_bars"] == 1522
    assert source["numeric_differences_against_R1"] == {}
    for c, f in zip(data["candles"], data["flow"]):
        assert c["ts"] == f["ts"]
        for field, meta in f["provenance"].items():
            assert meta["historical_api_as_of_proven"] is False
            assert meta["decision_ts"] == c["ts"] + 14_400_000
            if meta["coverage"] in {"observed", "carried"}:
                assert meta["available_ts"] <= meta["decision_ts"]
                assert meta["age_ms"] <= 28_800_000 or field not in {"oi", "oi_btc", "funding"}
            elif meta["coverage"] == "missing":
                assert meta["sample_ts"] is None
    assert len(source["missing_active_times"]["long_liq"]) == 4
    assert len(source["missing_active_times"]["short_liq"]) == 4
    assert all(not source["missing_active_times"][field] for field in
               ("spot_cvd", "fut_cvd", "oi", "oi_btc", "funding", "long_pct"))
    rows = []
    for row in original["rows"]:
        blocked = row["id"] == "V035"
        rows.append({"id": row["id"], "status": "blocked_F02" if blocked else "eligible_conditional_spot_model",
                     "input": "A7-flow-modeled-v2.json.gz", "historical_api_as_of_proven": False,
                     "original_params_sha256": row["params_sha256_canonical"],
                     "effective_cvd": "usd" if row["params"]["muster_cvd"] == "alt" else row["params"]["muster_cvd"],
                     "scope": "modelled A2 availability; no real as-of or execution claim" if not blocked
                              else "historical derivative funding/instrument/fills absent"})
    assert len(rows) == 86 and sum(r["status"] == "eligible_conditional_spot_model" for r in rows) == 85
    output = {"schema": "a7-eligibility-v2", "revises": "A7-auswertbarkeit-v1.json",
              "reason_for_revision": "Frozen Coinalyze archive and full Kraken hourly funding source inspected; A2 modelled availability can be derived without inventing absent numeric observations",
              "manifest_sha256": sha(DOC / "A7-analysemanifest-v1.json"),
              "flow_manifest_sha256": sha(DOC / "A7-flow-modeled-manifest-v2.json"),
              "flow_data_sha256": sha(data_path),
              "eligible_conditional_spot": 85, "blocked_F02": 1,
              "historical_api_as_of_proven": False,
              "legacy_level_model_ranked_with_causal": False,
              "active_missing_liquidation_bars": source["missing_active_times"]["long_liq"],
              "rows": rows, "returns_calculated": False}
    path = DOC / "A7-auswertbarkeit-v2.json"
    encoded = (json.dumps(output, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if path.exists():
        assert path.read_bytes() == encoded
    else:
        path.write_bytes(encoded)
    print("A7 v2 preflight: 85 conditional spot rows eligible, V035 blocked; frozen pre-run gate;",
          sha(path))


if __name__ == "__main__":
    main()
