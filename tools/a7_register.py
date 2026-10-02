"""Carry all 22 findings through the A7 preflight without closing A7."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs" / "audit-nacharbeit-2026-10" / "REGISTER.json"


def main():
    obj = json.loads(PATH.read_text(encoding="utf-8"))
    rows = obj["findings"]
    assert len(rows) == 22 and len({row["id"] for row in rows}) == 22
    if obj["stage"] == "A6":
        obj["a6_base_commit"] = obj["base_commit"]
    obj["stage"] = "A7_in_progress"
    obj["base_commit"] = "8b6af70b1897e8aefff5552f878297cc0090ef26"
    note = ("A7 preflight at A6 base: 86 fixed rows inventoried; corrected R0/R1 "
            "return runs blocked because numeric flow lacks A2 field provenance. "
            "No new historical return or A7 closure claimed. See A7-auswertbarkeit-v1.json.")
    for row in rows:
        row["a7_preflight"] = note
        if row["id"] == "M01":
            row["status"] = "A7 alte Entscheidungen und ihre damaligen Basen indexiert; Neuberechnung offen"
            row["evidence"] = "A7-M01-M02-zuordnung-v1.json; A7-BERICHT.md"
            row["remaining_limit"] = ("76 dokumentierte Entscheidungszeilen und 85 alte Codezeilen zugeordnet; "
                                      "nicht jede alte Rohbasis rekonstruierbar; keine Übertragung auf V000.")
        elif row["id"] == "M02":
            row["status"] = "A7 Inferenzgrenze fortgeschrieben; Neuberechnung offen"
            row["evidence"] = "A7-M01-M02-zuordnung-v1.json; A7-BERICHT.md; docs/nach-6/search-inventory.json"
            row["remaining_limit"] = ("Frühere Suche unvollständig bekannt, Daten wiederverwendet; "
                                      "keine Auswahlkorrektur, unabhängige Stichprobe oder Signifikanzbehauptung.")
    obj["a7_stage_complete"] = False
    obj["a7_base_commit"] = "8b6af70b1897e8aefff5552f878297cc0090ef26"
    obj["a7_preflight_evidence"] = ["A7-analysemanifest-v1.json", "A7-auswertbarkeit-v1.json",
                                    "A7-M01-M02-zuordnung-v1.json", "A7-BERICHT.md"]
    PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("A7 register: 22 IDs carried, M01/M02 partial, A7 incomplete")


if __name__ == "__main__":
    main()
