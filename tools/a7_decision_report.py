"""Carry every original M01 decision against its recorded contemporary basis."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"


def safe(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def main():
    mapping = json.loads((DOC / "A7-M01-M02-zuordnung-v1.json").read_text(encoding="utf-8"))
    assert mapping["decision_count"] == len(mapping["decisions"]) == 76
    assert len(mapping["old_code_rows"]) == 85
    assert mapping["old_code_row_distance"] == {"identical": 1, "one_change": 23,
                                                 "multiple_changes": 61}
    m02 = mapping["M02"]
    assert m02["previously_indexed_versioned_entries"] == 94
    assert not m02["complete_search_family"] and m02["reused_data"]
    lines = ["# A7 – M01/M02: damalige Vergleichsbasis und Inferenzgrenze", "",
        "Der Originalbefund M01 (`audit-work/docs/audit-2026-09-27/BERICHT.md:172`)",
        "betrifft wechselnde LIVE-Basen. Von 85 alten Codezeilen ist eine mit der",
        "heutigen Basis identisch, 23 unterscheiden sich in einem Parameter, 61 in",
        "mehreren. Jede der folgenden 76 dokumentierten Entscheidungen wird daher",
        "nur mit ihrer **damals genannten Basis und ihrem Fenster** gelesen. Die",
        "Originalbeobachtung und ihre damalige Grenze bleiben erhalten; eine neue",
        "R0/R1-Rendite auf V000 ersetzt keine fehlenden früheren Eingaben oder",
        "Parameterstände. Die Zeilen sind eine Chronik, keine 76 unabhängigen Tests.",
        "", "| Entscheidung | Damalige Basis / Fenster | Originalbeobachtung | Beurteilung und Grenze | Originalzeile |",
        "|---|---|---|---|---:|"]
    for item in mapping["decisions"]:
        assert item["same_as_current_basis_claim"] is False
        lines.append("| " + " | ".join(safe(item[k]) for k in (
            "stage_and_choice", "contemporary_basis_and_window", "original_observation",
            "original_decision_and_audit_limit")) + f' | {item["line"]} |')
    lines += ["", "## M02", "",
        "Der Originalbefund (`audit-work/docs/audit-2026-09-27/BERICHT.md:173,257–268`)",
        "beschreibt wiederholte Entwicklung auf denselben Monaten. Das vorhandene",
        "`docs/nach-6/search-inventory.json` weist mindestens 94 versionierte",
        "Sucheinträge nach, bezeichnet die vollständige Suchfamilie aber ausdrücklich",
        "als unbekannt. Die Hälften, Monate, fortlaufenden Drittel und Frischstarts",
        "in A7 sind beschreibende Stabilitätsdiagnosen auf wiederverwendeten Daten.",
        "Die gepaarte V000/V004-Statistik gilt nur für dieses vorab festgelegte Paar",
        "und vollständige UTC-Tage. Es gibt keinen auswahlbereinigten p-Wert, keine",
        "künstliche Zahl unabhängiger Kandidaten und keine neue externe Stichprobe.",
        "Weder eine bessere Einzelzeile noch ein enges bedingtes Intervall beweist",
        "eine künftig handelbare Überrendite. Furkan-Quellen, Forschung und alte",
        "Themenberichte bleiben als Originalquellen erhalten; A7 ergänzt ihre",
        "historische Aussage mit dem neuen Modellvertrag.", ""]
    dest = DOC / "A7-M01-M02-BEWERTUNG.md"
    raw = ("\n".join(lines).rstrip()+"\n").encode("utf-8")
    if dest.exists():
        assert dest.read_bytes() == raw
    else:
        dest.write_bytes(raw)
    print("M01 76 contemporary decisions, M02 inference limit recorded")


if __name__ == "__main__":
    main()
