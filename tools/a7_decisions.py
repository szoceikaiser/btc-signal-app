"""Index every documented old decision and its contemporary comparison basis."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "audit-work" / "docs" / "audit-2026-09-27"
OUT = ROOT / "docs" / "audit-nacharbeit-2026-10" / "A7-M01-M02-zuordnung-v1.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(path, start, expected):
    lines = path.read_text(encoding="utf-8").splitlines()
    begin = next(i for i, line in enumerate(lines) if line.startswith(start))
    rows = []
    active = False
    for i in range(begin + 1, len(lines)):
        line = lines[i]
        if line.startswith("|"):
            active = True
            parts = [x.strip() for x in line.strip().strip("|").split("|")]
            if parts[0].startswith("---") or parts[0] in {"Etappe / Zweck", "alte Gitterzeile"}:
                continue
            rows.append((i + 1, parts))
        elif active:
            break
    assert len(rows) == expected, (path, len(rows))
    return rows


def main():
    chronology = SOURCE / "ENTSCHEIDUNGEN.md"
    parameters = SOURCE / "PARAMETER.md"
    search = ROOT / "docs" / "nach-6" / "search-inventory.json"
    decisions = []
    decision_lines = [
        (i, [x.strip() for x in line.strip().strip("|").split("|")])
        for i, line in enumerate(chronology.read_text(encoding="utf-8").splitlines(), 1)
        if line.startswith("| E") and not line.startswith("| Etappe")
    ]
    assert len(decision_lines) == 76
    for line, cells in decision_lines:
        assert len(cells) == 4, (line, cells)
        decisions.append({
            "stage_and_choice": cells[0],
            "contemporary_basis_and_window": cells[1],
            "original_observation": cells[2],
            "original_decision_and_audit_limit": cells[3],
            "source": "audit-work/docs/audit-2026-09-27/ENTSCHEIDUNGEN.md",
            "line": line,
            "same_as_current_basis_claim": False,
        })
    old_rows = []
    for line, cells in table(parameters, "## Jede bestehende Gitterzeile", 85):
        assert len(cells) == 3, (line, cells)
        old_rows.append({"original_label": cells[0], "differences_to_current": int(cells[1]),
                         "effective_differences": cells[2],
                         "source": "audit-work/docs/audit-2026-09-27/PARAMETER.md", "line": line})
    assert [sum(row["differences_to_current"] == n for row in old_rows) for n in (0, 1)] == [1, 23]
    assert sum(row["differences_to_current"] >= 2 for row in old_rows) == 61
    earlier = json.loads(search.read_text(encoding="utf-8"))
    assert earlier["complete_family"] is False
    result = {
        "schema": "a7-decision-basis-v1",
        "scope": "Index of the original audit chronology and the 85 old code rows; original decisions are not rerun or silently mapped to current V000",
        "source_sha256": {"ENTSCHEIDUNGEN.md": sha(chronology), "PARAMETER.md": sha(parameters),
                          "search-inventory.json": sha(search)},
        "decision_count": len(decisions), "decisions": decisions,
        "old_code_rows_count": len(old_rows), "old_code_rows": old_rows,
        "old_code_row_distance": {"identical": 1, "one_change": 23, "multiple_changes": 61},
        "M02": {
            "previously_indexed_versioned_entries": earlier["distinct_versioned_entries"],
            "complete_search_family": False,
            "search_family_source": "docs/nach-6/search-inventory.json",
            "reused_data": True,
            "halves_and_months_unseen_validation": False,
            "selection_adjusted_p_value": None,
            "independent_new_sample": False,
            "claim": "Historical comparisons are conditional diagnostics, not a selection-corrected significance test or proof of future performance",
        },
    }
    encoded = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if OUT.exists():
        assert OUT.read_bytes() == encoded, "Existing M01/M02 index differs"
    else:
        OUT.write_bytes(encoded)
    print(f"M01: {len(decisions)} documented decision rows, {len(old_rows)} old code rows; "
          f"M02 complete search family: no; sha256 {sha(OUT)}")


if __name__ == "__main__":
    main()
