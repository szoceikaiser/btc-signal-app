"""Build a complete A7 result index from immutable per-run evidence."""

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import socket

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
RUN = DOC / "A7-runs"
LEGACY = DOC / "A7-legacy"
SCENARIOS = [f"S{i}" for i in range(5)]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"file": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path)}


def blocked(*_args, **_kwargs):
    raise AssertionError("A7 result report has no network access")


def diff(before, after):
    a, b = Counter(tuple(x) for x in before), Counter(tuple(x) for x in after)
    return {"removed": sum((a-b).values()), "added": sum((b-a).values()),
            "first_removed": list(next(iter(sorted((a-b).elements())), ())) or None,
            "first_added": list(next(iter(sorted((b-a).elements())), ())) or None}


def months(detail):
    return {p["label"]: p for p in detail["periods"] if p["kind"] == "month"}


def thirds(detail):
    return {p["label"]: p for p in detail["periods"] if p["kind"] == "third"}


def leave_one_out(a, b):
    am, bm = a["months"], b["months"]
    assert am.keys() == bm.keys()
    return {omit: 100*(math.prod(1+v["return_pct"]/100 for k, v in am.items()
                                   if k != omit) -
                       math.prod(1+v["return_pct"]/100 for k, v in bm.items()
                                   if k != omit)) for omit in am}


def compact_run(path):
    obj = read(path)
    assert obj["independent_account_verified"] and not obj["historical_api_as_of_proven"]
    d = obj["detail"]
    assert months(d) and len(thirds(d)) == 3
    return {"source": ref(path), "start_ms": obj["start_ms"],
            "cutoff_ms": obj["cutoff_ms"], "end_usd": d["ende"],
            "return_pct": d["rendite_pct"], "dd_close_pct": d["dd_close_pct"],
            "dd_intrabar_range_pct": [d["dd_intrabar_lower_pct"],
                                      d["dd_intrabar_upper_pct"]],
            "fees_usd": d["fees"], "fills": d["verification"]["fills"],
            "avg_exposure_pct": d["verification"]["avg_exposure_pct"],
            "cash_usd": d["cash"], "btc": d["btc"], "cost_basis_usd": d["cost_basis"],
            "unfilled_end_of_data": d["unfilled_end_of_data"],
            "independent_zero_dust": d["verification"].get("independent_zero_dust", []),
            "months": months(d), "thirds": thirds(d),
            "signal_count": len(obj["signal_events"]),
            "signal_event_sha256": obj["signal_event_sha256"],
            "result_sha256": d["result_sha256"], "independent_account_verified": True}


def main():
    socket.socket.connect = socket.create_connection = blocked
    design_path = DOC / "A7-analysemanifest-v1.json"
    eligibility_path = DOC / "A7-auswertbarkeit-v2.json"
    design, gate = read(design_path), read(eligibility_path)
    assert gate["manifest_sha256"] == sha(design_path)
    assert gate["eligible_conditional_spot"] == 85 and gate["blocked_F02"] == 1
    assert len(design["rows"]) == 86
    all_rows = {}
    causal_event_changes = defaultdict(list)
    legacy_event_changes = []
    intermediate_changes = defaultdict(list)
    for row in design["rows"]:
        rid = row["id"]
        if rid == "V035":
            all_rows[rid] = {"status": "blocked_F02", "returns": None,
                "reason": "missing historical derivative instrument, complete funding payments, marks and causal short fills"}
            continue
        package_results = {}
        for package in ("R0", "R1"):
            causal = {s: compact_run(RUN / f"{package}-{s}-{rid}.json")
                      for s in SCENARIOS}
            halves = {h: compact_run(RUN / f"{package}-S0-{rid}-{h}.json")
                      for h in ("half1", "half2")}
            legacy_path = LEGACY / f"{package}-{rid}.json"
            old = read(legacy_path)
            assert old["id"] == rid and len(old["cases"]) == 4
            assert old["flow_sha256"] == gate["flow_data_sha256"]
            assert old["design_sha256"] == sha(design_path)
            legacy = {case["case"]["fill"]: {"case": case["case"],
                       "end_usd": case["account"]["end"],
                       "return_pct": case["account"]["return_pct"],
                       "dd_close_pct": -case["account"]["dd_close_pct"],
                       "fees_usd": case["account"]["fees"],
                       "fills": case["account"]["orders"],
                       "avg_exposure_pct": case["account"]["avg_exposure_pct"],
                       "month_ends": case["account"]["month_ends"]}
                      for case in old["cases"]}
            old_halves_path = DOC / "A7-legacy-halves" / f"{package}-{rid}.json"
            old_halves = read(old_halves_path)
            assert old_halves["id"] == rid and old_halves["package"] == package
            assert len(old_halves["halves"]) == 2
            assert old_halves["flow_sha256"] == gate["flow_data_sha256"]
            assert old_halves["design_sha256"] == sha(design_path)
            causal_events = read(RUN / f"{package}-S0-{rid}.json")["signal_events"]
            event_change = diff(old["signal_events"], causal_events)
            causal_event_changes[package].append(event_change)
            original_difference = old["differences_to_original_R0"]
            if package == "R0":
                legacy_event_changes.append(original_difference)
                intermediate_path = DOC / "A7-events-R0" / f"{rid}.json"
                intermediate = read(intermediate_path)
                assert intermediate["id"] == rid
                for key in ("old_audit_to_current_numeric_alt",
                            "current_numeric_alt_to_modeled_alt",
                            "modeled_alt_to_corrected_cvd"):
                    intermediate_changes[key].append(intermediate[key])
            base = compact_run(RUN / f"{package}-S0-V000.json")
            base_halves = {h: compact_run(RUN / f"{package}-S0-V000-{h}.json")
                           for h in ("half1", "half2")}
            half_delta = {h: halves[h]["return_pct"]-base_halves[h]["return_pct"]
                          for h in halves}
            loo = leave_one_out(causal["S0"], base)
            package_results[package] = {"causal": causal, "halves_S0": halves,
                "legacy_diagnostic": {"source": ref(legacy_path), "cases": legacy,
                    "halves_source": ref(old_halves_path),
                    "level_fresh_halves": old_halves["halves"],
                    "historical_execution_claim": False},
                "event_change_legacy_to_causal_S0": event_change,
                "event_change_original_to_corrected_legacy": original_difference,
                "intermediate_event_attribution_R0": ref(intermediate_path)
                    if package == "R0" else None,
                "comparison_to_V000_S0": {
                    "return_delta_pp": causal["S0"]["return_pct"]-base["return_pct"],
                    "dd_close_delta_pp": causal["S0"]["dd_close_pct"]-base["dd_close_pct"],
                    "half_return_delta_pp": half_delta,
                    "leave_one_month_out_advantage_pp": loo,
                    "min_leave_one_month_out_pp": min(loo.values())}}
        all_rows[rid] = {"status": "eligible_conditional_spot_model",
                         "groups": row["groups"], "source": row["source"],
                         "params_sha256": row["params_sha256_canonical"],
                         "packages": package_results}
    capital = {p: {s: {k: compact_run(RUN / f"{p}-{s}-V000-{k}.json")
                           for k in ("capital06", "capital05")}
                   for s in SCENARIOS} for p in ("R0", "R1")}
    fresh = {p: {s: {k: {rid: compact_run(RUN / f"{p}-{s}-{rid}-{k}.json")
                               for rid in ("V000", "V004")}
                           for k in ("fresh1", "fresh2")}
                   for s in SCENARIOS} for p in ("R0", "R1")}
    paired_path = DOC / "A7-paired-statistics-v1.json"
    paired = read(paired_path)
    assert len(paired["results"]) == 10 and all(x["previous_N6_U1_identical"]
                                                 for x in paired["results"])
    intermediate_path = DOC / "A7-intermediate-A2-S0-v1.json"
    intermediate_effect = read(intermediate_path)
    assert len(intermediate_effect["results"]) == 4
    assert all(all(stage["independent_book_verified"] for stage in
                   row["outcomes"].values()) for row in intermediate_effect["results"])
    summary = {"schema": "a7-complete-model-result-index-v1", "stage": "A7",
               "historical_api_as_of_proven": False,
               "design": ref(design_path), "eligibility": ref(eligibility_path),
               "flow_sha256": gate["flow_data_sha256"],
               "causal_spot_configuration_count": 85,
               "blocked_derivative_configuration_count": 1,
               "legacy_and_causal_ranked_together": False,
               "selection_adjusted": False,
               "identical_alias": {"S004": "V000"},
               "rows": all_rows, "capital": capital, "fresh_starts": fresh,
               "legacy_capital": ref(DOC / "A7-legacy-capital-v1.json"),
               "buyhold_description": ref(DOC / "A7-buyhold-v1.json"),
               "paired_statistics": ref(paired_path),
               "intermediate_A2_effect": ref(intermediate_path),
               "event_change_counts": {
                   "original_to_corrected_legacy_R0_rows_changed": sum(bool(x["added"] or x["removed"])
                                                               for x in legacy_event_changes),
                   "legacy_to_causal_R0_rows_changed": sum(bool(x["added"] or x["removed"])
                                                           for x in causal_event_changes["R0"]),
                   "legacy_to_causal_R1_rows_changed": sum(bool(x["added"] or x["removed"])
                                                           for x in causal_event_changes["R1"]),
                   "intermediate_R0_rows_changed": {k: sum(bool(x["added"] or x["removed"])
                                                         for x in v)
                                                    for k, v in intermediate_changes.items()}}}
    out = DOC / "A7-resultindex-v1.json"
    raw = (json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if out.exists():
        assert out.read_bytes() == raw
    else:
        out.write_bytes(raw)
    lines = ["# A7 – Vollständiger Index der bedingten Offline-Modellrechnungen", "",
        "85 zulässige Spotkonfigurationen, V035 gesperrt. S004 ist V000. R0/R1,",
        "fünf kausale S0–S4-Szenarien, vier getrennte alte Diagnosefälle, zwei",
        "alte Level- und kausale S0-Frischstart-Hälften je Spotzeile, zwei Drittel-Frischstarts für",
        "V000/V004 je Szenario und die Kapitalquoten 1,0/0,6/0,5 sind indexiert.",
        "Jede Einzeldatei enthält Monate, fortlaufende Drittel, Kosten, Bestand,",
        "Risiko, Signale und den unabhängigen Buchabgleich. Vollständige Zahlen und",
        "Dateihashes stehen in `A7-resultindex-v1.json`.", "",
        "Die alte Level-/Schlussdiagnose beweist keine zuvor liegenden Orders. Die",
        "kausalen V1/i+2-Reihen sind idealisierte Spotmodelle. Beide Familien",
        "werden nicht in eine gemeinsame Rangliste gesetzt. Damalige API-Verfügbarkeit",
        "und reale Fills sind nicht belegt. Hälften/Monate sind wiederverwendete Daten.", ""]
    for package in ("R0", "R1"):
        lines += [f"## {package}: kausaler Spotvergleich", "",
            "| ID | S0 % | S1 % | S2 % | S3 % | S4 % | H1/H2 S0 % | DD S0 % | Gebühren S0 USD | min. ohne Monat pp |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for row in design["rows"]:
            rid = row["id"]
            if rid == "V035":
                lines.append("| V035 | gesperrt F02 | | | | | | | | |")
                continue
            data = all_rows[rid]["packages"][package]
            causal, halves = data["causal"], data["halves_S0"]
            values = [f'{causal[s]["return_pct"]:.2f}' for s in SCENARIOS]
            lines.append(f'| {rid} | ' + " | ".join(values) +
                f' | {halves["half1"]["return_pct"]:.2f}/{halves["half2"]["return_pct"]:.2f}'
                f' | {causal["S0"]["dd_close_pct"]:.2f} | {causal["S0"]["fees_usd"]:.2f}'
                f' | {data["comparison_to_V000_S0"]["min_leave_one_month_out_pp"]:+.2f} |')
        lines += ["", "Alte vier Diagnosefälle je Zeile und Monat: `A7-legacy/` und",
                  "`A7-resultindex-v1.json`; keine Mischung mit der Tabelle oben.", ""]
    lines += ["## Inferenz- und Datenvertrag", "",
        "Gepaarte Statistik gilt ausschließlich für V000/V004 auf vollständigen",
        "UTC-Tagen im Nach-6-Vertrag (`A7-paired-statistics-v1.json`). Sie ist",
        "nicht auswahlbereinigt. M01 ordnet die 76 dokumentierten Entscheidungen",
        "ihren jeweiligen damaligen Basen und Fenstern zu; M02 hält die unbekannte",
        "vollständige Suchfamilie und die wiederverwendeten Monate fest.", ""]
    md = DOC / "A7-ERGEBNISSE-v1.md"
    md_raw = ("\n".join(lines).rstrip() + "\n").encode()
    if md.exists():
        assert md.read_bytes() == md_raw
    else:
        md.write_bytes(md_raw)
    print("A7 result index", len(all_rows), "rows, 85 conditional spot,",
          "10 pair statistics, all files accounted for")


if __name__ == "__main__":
    main()
