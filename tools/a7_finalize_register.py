"""Carry every audit ID into the completed A7 result assessment."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
PATH = DOC / "REGISTER.json"

ASSESSMENTS = {
    "F01": "Schluss- und Intrabar-Risikobänder je Spotlauf ausgewiesen; Intrabar-Reihenfolge bleibt unbekannt.",
    "F02": "Synthetische Margin-/Fundingbuchung geprüft; V035 bleibt ohne historischen Derivatvertrag, vollständige Zahlungen, Markpreise und kausale Short-Fills gesperrt.",
    "F03": "Monotone Stopkorrektur in der 792er-Regression erhalten; keine allgemeine Aussage zu echten Fills.",
    "F04": "Losgewichteter Einstand erhalten; Kosten, Lose und Monatsbestände jedes kausalen A7-Laufs unabhängig abgeglichen.",
    "F05": "Bisherige Persistenzkorrektur in Regression erhalten; Widerstandsausstieg nicht aktiviert.",
    "F06": "Korrigiertes CVD entfernt nach Verfügbarkeitsmodellierung nur eine V075-Warnung; S0-Bilanzwirkung R0/R1 je 0 USD.",
    "F07": "Modellierte Verfügbarkeit entfernt zwei V050-Nachkäufe; S0-Endwert steigt um 159,461596 USD in R0 und 159,018561 USD in R1. Damalige API-Verfügbarkeit unbewiesen.",
    "F08": "Vertrag geschlossener UTC-Tage erhalten; keine unbelegte historische Mehrmarkt-Tagesreihe erzeugt.",
    "F09": "Restbehandlung erhalten; begrenzte Gleitkomma-Losrundung korrigiert, echter Oversell abgewiesen und Gegenbuch abgeglichen.",
    "F10": "Gemeinsamer Stop-Resolver in Regression erhalten; keine neue Live-Planbehauptung.",
    "F11": "Typisierte Boolean-Korrektur in Regression erhalten; eingefrorene A7-Parameter bestehen Manifestprüfung.",
    "F12": "Alte Level-/Schlussdiagnosen getrennt von kausalen V1/i+2-Spotkonten ausgewiesen; keine Behauptung realer Orders.",
    "F13": "Simulierter A4-Outboxstatus erhalten; A7 sendete keine Telegram-Nachricht und änderte keine Bereitstellung.",
    "F14": "Vollständigkeitsprüfung des Marktkorbs erhalten; keine unbelegte historische Korbreihe eingesetzt.",
    "F15": "USD-Einheitenprüfung erhalten; keine unbelegte historische Mehrmarkt-Volumenrangliste eingesetzt.",
    "F16": "ATR-Kurzvorlaufkorrektur in Regression erhalten; A7 verwendete eingefrorene Parameter.",
    "F17": "Bisherige Chart-Ereignisidentität erhalten; A7 änderte keine Chartanzeige.",
    "D01": "R0/R1 verwenden eingefrorene abgeschlossene 4h-Eingaben und gespeicherte Grenzen; historische API-Zeitpunkte unbewiesen.",
    "D02": "Vier aktive Liquidationspunkte bleiben missing; kein Ersatz durch neutrale Null. V050-Zwischenwirkung gemeinsam mit A2-Verfügbarkeit gemessen.",
    "M01": "76 Entscheidungen an damaligen Basen/Fenstern beurteilt, 85 alte Codezeilen inventarisiert; fehlende frühe Basen nicht durch V000 ersetzt.",
    "M02": "Bedingte Paar-/Stabilitätsdiagnosen abgeschlossen; mindestens 94 dokumentierte Suchen, unbekannte vollständige Familie und wiederverwendete Monate bleiben ohne Auswahlbereinigung.",
    "T01": "A6-Fallzuordnung erhalten; 792 aktuelle Enginetests bestanden, einschließlich gezielter Rundungsfälle, ohne Live-Aktivierung.",
}


def main():
    obj = json.loads(PATH.read_text(encoding="utf-8"))
    rows = obj["findings"]
    assert len(rows) == 22 and {r["id"] for r in rows} == set(ASSESSMENTS)
    for row in rows:
        rid = row["id"]
        row["a7_assessment"] = ASSESSMENTS[rid]
        row["a7_evidence"] = ["A7-ABSCHLUSSBERICHT.md", "A7-resultindex-v1.json"]
        row["next_stage"] = "A8 Gesamtabnahme"
    by_id = {row["id"]: row for row in rows}
    by_id["F02"]["status"] = "A5 Offline-Buch geprüft; A7 V035 historisch gesperrt"
    by_id["M01"]["status"] = "A7 historische Basen und bedingte neue Modellvergleiche bewertet"
    by_id["M02"]["status"] = "A7 Inferenzgrenze und bedingte Statistik vollständig eingeordnet"
    obj["stage"] = "A7_complete"
    obj["a7_stage_complete"] = True
    obj["a7_completion_evidence"] = [
        "A7-ABSCHLUSSBERICHT.md", "A7-resultindex-v1.json",
        "A7-ERGEBNISSE-v1.md", "A7-paired-statistics-v1.json",
        "A7-intermediate-A2-S0-v1.json", "A7-M01-M02-BEWERTUNG.md",
        "A7-engine-tests.log"]
    obj["a7_preflight_v2"]["status"] = (
        "Frozen pre-return eligibility: 85 conditional spot model rows; V035 blocked F02")
    obj["a7_targeted_R1_S0"]["status"] = (
        "First fixed V000/V004 pair, independently checked; expanded A7 evidence in completion index")
    PATH.write_bytes((json.dumps(obj, indent=2, ensure_ascii=False)+"\n").encode("utf-8"))
    markdown = DOC / "REGISTER.md"
    body = markdown.read_text(encoding="utf-8")
    body = body.replace("Stand: A7-Zwischenstand auf Basis", "Stand: A7-Fachauswertung abgeschlossen auf Basis", 1)
    body = body.replace("A7 ist **nicht abgeschlossen**.",
                        "A7 ist fachlich abgeschlossen; CI und Sicherung siehe Übergabe.", 1)
    appendix = """
## A7-Abschlussfortschreibung

Alle 22 Register-IDs sind in `REGISTER.json` mit `a7_assessment` und
`a7_evidence` fortgeführt. M01 ist mit 76 damaligen Entscheidungsbasen
bewertet; M02 hält mindestens 94 dokumentierte Suchen, die unbekannte
vollständige Suchfamilie und die wiederverwendeten Monate als Grenze fest.
Die alte v1-Sperrmatrix und der R1/S0-Paarlauf oben sind ausdrücklich
historische A7-Zwischenstände; die spätere v2-Modellfreigabe und vollständigen
bedingten Resultate stehen im [A7-Abschlussbericht](A7-ABSCHLUSSBERICHT.md)
und [Ergebnisindex](A7-resultindex-v1.json). 85 Spotzeilen sind bedingt
ausgewertet; V035 bleibt nach fachlicher F02-Prüfung ohne historische Rendite.
Die A7-Buch- und Engineregression bestand lokal mit 792/0; die endgültige
CI-/Bundle-/Restore-SHA steht nur in der nach Commit erzeugten Übergabe.
Es gibt keine Live- oder Aktivierungsfreigabe durch A7. Nächster Schritt
ist ausschließlich A8-Gesamtabnahme.
"""
    appendix += "\n| ID | A7-Fortschreibung | Verbleibende Grenze |\n|---|---|---|\n"
    for row in rows:
        appendix += (f"| {row['id']} | {row['a7_assessment']} | "
                     f"{row['remaining_limit']} |\n")
    marker = "## A7-Abschlussfortschreibung"
    if marker in body:
        body = body.split(marker, 1)[0]
    markdown.write_bytes((body.rstrip()+"\n"+appendix).encode("utf-8"))
    print("REGISTER", len(rows), "IDs advanced to A7")


if __name__ == "__main__":
    main()
