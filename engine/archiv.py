"""E44.1 (26.09.2026): Coinalyze-Archiv, damit das Backtest-Fenster waechst statt wandert.

Coinalyze liefert nur rund 1.500 bis 2.000 4h-Werte. Aeltere loescht es taeglich. Das
Backtest-Fenster beginnt an der ersten OI-Kerze (`eff_start` in backtest.py) und rueckt
deshalb jeden Tag nach vorn: im Juli ab 18.11.2025, am 26.09.2026 ab 18.01.2026. Jede
Messung arbeitet damit auf einem anderen, nie laengeren Zeitraum.

Dieses Modul speichert die Reihen, die der Backtest benutzt, in eine Datei im Repo und
mischt sie bei jedem Abruf mit den frischen Werten. Neue Werte ueberschreiben alte zum
selben Zeitpunkt (Coinalyze darf nachkorrigieren), alte Zeitpunkte bleiben erhalten.
Gespeichert werden nur ABGESCHLOSSENE 4h-Kerzen - eine laufende Kerze haette noch keinen
endgueltigen Wert.

Aufruf (taeglich ueber .github/workflows/archiv.yml): python3 archiv.py
Die Live-Engine (main.py) benutzt dieses Modul bewusst NICHT.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import coinalyze

KERZE_MS = 4 * 3600 * 1000
PFAD = Path(__file__).resolve().parent.parent / "site" / "data" / "archiv" / "coinalyze_4h.json"
REIHEN = ("oi", "liq", "fut", "ls")
# Abrufzeitraum fuer den taeglichen Lauf: grosszuegig, Coinalyze kappt ohnehin selbst.
ABRUF_TAGE = 400


def nur_abgeschlossen(karte: dict, jetzt_ms: int) -> dict:
    """Nur Kerzen, deren 4h-Zeitraum vorbei ist (Open-Time + 4h <= jetzt)."""
    return {ts: v for ts, v in karte.items() if ts + KERZE_MS <= jetzt_ms}


def zusammen(alt: dict, neu: dict) -> dict:
    """Archiv und frische Werte mischen. Neu gewinnt, alte Zeitpunkte bleiben."""
    out = dict(alt or {})
    out.update(neu or {})
    return out


def laden(pfad: Path = PFAD) -> dict:
    """{Reihe: {ts_ms: Wert}}. Fehlende oder leere Datei ist kein Fehler."""
    try:
        roh = json.loads(Path(pfad).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {r: {} for r in REIHEN}
    out = {}
    for r in REIHEN:
        werte = roh.get(r) or {}
        # JSON kennt keine Tupel: Liquidationen (long, short) kommen als Liste zurueck.
        out[r] = {int(ts): (tuple(v) if isinstance(v, list) else v)
                  for ts, v in werte.items()}
    return out


def speichern(archiv: dict, pfad: Path = PFAD) -> None:
    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    daten = {r: {str(ts): (list(v) if isinstance(v, tuple) else v)
                 for ts, v in sorted((archiv.get(r) or {}).items())}
             for r in REIHEN}
    pfad.write_text(json.dumps(daten, separators=(",", ":")), encoding="utf-8")


def mit_archiv(frisch: dict, archiv: dict) -> dict:
    """Frische Reihen {Reihe: karte} mit dem Archiv mischen (fuer den Backtest)."""
    return {r: zusammen(archiv.get(r, {}), frisch.get(r, {})) for r in REIHEN}


def abrufen(api_key: str, jetzt_ms: int) -> dict:
    """Die vier Reihen frisch von Coinalyze, nur abgeschlossene Kerzen. Eine Reihe, die
    scheitert, bleibt leer - das Archiv behaelt dann einfach seinen alten Stand."""
    frm = jetzt_ms // 1000 - ABRUF_TAGE * 86400
    to = jetzt_ms // 1000
    holer = {"oi": coinalyze.oi_by_ts, "liq": coinalyze.liquidations_by_ts,
             "fut": coinalyze.fut_delta_by_ts, "ls": coinalyze.long_short_by_ts}
    out = {}
    for r, hole in holer.items():
        try:
            out[r] = nur_abgeschlossen(hole(api_key, frm=frm, to=to), jetzt_ms)
        except Exception as exc:  # noqa: BLE001
            print(f"Archiv: {r} nicht abrufbar ({exc}) - alter Stand bleibt.")
            out[r] = {}
    return out


def main() -> int:
    api_key = os.environ.get("COINALYZE_API_KEY", "")
    if not api_key:
        print("Archiv: kein COINALYZE_API_KEY - nichts zu tun.")
        return 0
    jetzt = int(time.time() * 1000)
    archiv = laden()
    frisch = abrufen(api_key, jetzt)
    neu = mit_archiv(frisch, archiv)
    speichern(neu)
    for r in REIHEN:
        ts = sorted(neu[r])
        von = time.strftime("%d.%m.%Y", time.gmtime(ts[0] / 1000)) if ts else "-"
        print(f"Archiv {r}: {len(archiv[r])} -> {len(neu[r])} Punkte, ab {von}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
