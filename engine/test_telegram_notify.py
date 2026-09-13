"""Tests fuer die Telegram-Formate (E5) — komplett offline (dry_run)."""

from strategy_core import Signal, SignalType
from telegram_notify import STYLE, format_signal, send_signals

KAUF2 = Signal(ts=1767830400000, type=SignalType.KAUF_2, price=89563.6,
               tranche_pct=50, reason="Golden Pocket 89294-89564 + Bestaetigung (CAPITULATION_RESET)",
               stop_ref=86348.7).to_dict()

STOP = Signal(ts=1770076800000, type=SignalType.STOPLOSS, price=74600.0,
              tranche_pct=100, reason="Kerzenschluss unter Invalidierung 78741").to_dict()


def test_format_kauf2_enthaelt_alle_bausteine():
    msg = format_signal(KAUF2)
    assert "KAUF 2" in msg
    assert "89.564 $" in msg                       # deutsches Tausenderformat
    assert "Tranche: 50 %" in msg
    assert "Stop-Referenz: 86.349 $" in msg
    assert "Golden Pocket" in msg
    assert "08.01.2026" in msg                     # Datum aus ts (UTC)
    assert "selbst pruefen" in msg                 # Sicherheits-Fusszeile


def test_format_stoploss():
    msg = format_signal(STOP)
    assert "STOPLOSS" in msg and "74.600 $" in msg
    assert "Stop-Referenz" not in msg              # Stop hat keine Stop-Referenz


def test_flush_signal_wird_markiert():
    flush = dict(KAUF2)
    flush["tag"] = "FLUSH"
    msg = format_signal(flush)
    assert "AGGRESSIVER FLUSH-EINSTIEG" in msg and "DEINE Entscheidung" in msg
    # Normale Signale ohne tag bekommen die Warnung nicht
    assert "AGGRESSIVER FLUSH" not in format_signal(KAUF2)


def test_alle_signaltypen_haben_style():
    for st in SignalType:
        assert st.name in STYLE, f"STYLE fehlt fuer {st.name}"


def test_send_signals_dry_run_ohne_netz():
    msgs = send_signals([KAUF2, STOP], dry_run=True)
    assert len(msgs) == 2 and all(isinstance(m, str) and m for m in msgs)


def test_lage_erscheint_in_plan_und_vorschau():
    """E32: Die Lage muss in BEIDEN Nachrichten stehen - das sind die, nach denen
    Kaiser die Limit-Orders setzt. Ohne Lage-Angabe darf kein leerer Block entstehen."""
    from telegram_notify import format_plan, format_vorschau
    lage = {"struktur": "intakt",
            "struktur_text": "Struktur intakt - hoeheres Tief 76.264 $, hoeheres Hoch 82.300 $",
            "spot": "nachgelassen",
            "spot_text": "Spot-Nachfrage nachgelassen (die Nachfrage hat gedreht)",
            "muster": "UNGESUNDER_ABVERKAUF",
            "muster_text": "ungesunder Abverkauf (der Dip wird nicht gekauft)"}
    plan = {"richtung": "LONG", "anteil_pct": 65, "einstand": 78807.0, "kurs": 79793.0,
            "stop": {"preis": 75546.0, "grund": "Invalidierung"}, "lage": lage}
    txt = format_plan(plan)
    assert "Lage:" in txt
    assert "Struktur intakt" in txt
    assert "Spot-Nachfrage nachgelassen" in txt
    assert "Muster: ungesunder Abverkauf" in txt

    vs = {"richtung": "LONG", "impuls_start": 76264.0, "impuls_ende": 82300.0,
          "level_05": 79282.0, "gp_lower": 78377.0, "gp_upper": 78570.0,
          "level_0786": 77556.0, "invalidation": 76264.0, "lage": lage}
    txt = format_vorschau(vs, 1789000000000)
    assert "Lage:" in txt and "Spot-Nachfrage nachgelassen" in txt

    # Ohne Lage: kein Block, keine leere Zeile zu viel
    plan_ohne = dict(plan); plan_ohne.pop("lage")
    assert "Lage:" not in format_plan(plan_ohne)
    vs_ohne = dict(vs); vs_ohne["lage"] = None
    assert "Lage:" not in format_vorschau(vs_ohne, 1789000000000)


def test_vorschau_nennt_das_bein_nicht_doppelt():
    """Bei "neu" (kein offener Trade) steht das Bein schon in der Kopfzeile der
    Vorschau - die Lage darf es nicht ein zweites Mal nennen."""
    from telegram_notify import format_vorschau
    vs = {"richtung": "LONG", "impuls_start": 76264.0, "impuls_ende": 82300.0,
          "level_05": 79282.0, "gp_lower": 78377.0, "gp_upper": 78570.0,
          "level_0786": 77556.0, "invalidation": 76264.0,
          "lage": {"struktur": "neu",
                   "struktur_text": "Aktuelles Bein 76.264 $ -> 82.300 $",
                   "spot": "stabil", "spot_text": "Spot-Nachfrage stabil (Nachfrage traegt)"}}
    txt = format_vorschau(vs, 1789000000000)
    assert "Aktuelles Bein" not in txt
    assert "Spot-Nachfrage stabil" in txt      # der Rest der Lage bleibt
