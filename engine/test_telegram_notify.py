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


def test_alle_signaltypen_haben_style():
    for st in SignalType:
        assert st.name in STYLE, f"STYLE fehlt fuer {st.name}"


def test_send_signals_dry_run_ohne_netz():
    msgs = send_signals([KAUF2, STOP], dry_run=True)
    assert len(msgs) == 2 and all(isinstance(m, str) and m for m in msgs)
