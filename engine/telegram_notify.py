"""Telegram-Benachrichtigungen (E5).

Nur Standardbibliothek (urllib) — laeuft ohne Zusatzpakete auf GitHub Actions.
Token/Chat-ID kommen aus Umgebungsvariablen (GitHub Secrets):
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
Dry-Run (ohne Netz, fuer Tests/lokal): send_signals(..., dry_run=True).
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Emoji + Kurzcode je Signaltyp (Kurzcode erscheint auch im Chart als Marker-Text)
STYLE = {
    "KAUF_1":           ("\U0001F7E2", "K1"),   # gruener Kreis
    "KAUF_2":           ("\U0001F7E2", "K2"),
    "NACHKAUF":         ("➕", "NK"),        # plus
    "TEILVERKAUF_LADDER": ("\U0001F7E1", "TVL"),  # gelber Kreis (Leiter-Zwischenstufe)
    "TEILVERKAUF_1":    ("\U0001F7E0", "TV1"),  # oranger Kreis
    "TEILVERKAUF_2":    ("\U0001F7E0", "TV2"),
    "VERKAUF_REST":     ("\U0001F534", "V"),    # roter Kreis
    "STOPLOSS":         ("\U0001F6D1", "SL"),   # Stoppschild
    "WARNUNG":          ("⚠️", "W"),
    "SHORT_1":          ("\U0001F53B", "S1"),   # rotes Dreieck runter
    "SHORT_2":          ("\U0001F53B", "S2"),
    "SHORT_NACHLEGEN":  ("➖", "SNK"),
    "SHORT_TP_LADDER":  ("\U0001F7E1", "STPL"), # gelber Kreis (Leiter-Zwischenstufe)
    "SHORT_TP_1":       ("\U0001F7E3", "STP1"), # lila Kreis
    "SHORT_TP_2":       ("\U0001F7E3", "STP2"),
    "SHORT_COVER_REST": ("\U0001F534", "SC"),
    "SHORT_STOPLOSS":   ("\U0001F6D1", "SSL"),
    # Kein Signal, sondern eine Ankuendigung (2026-07-29, Kaisers Anforderung):
    "VORSCHAU":         ("\U0001F4CD", "VOR"),  # Stecknadel
}


def format_vorschau(z: dict, ts_ms: int) -> str:
    """Ankuendigungs-Nachricht: WO die naechsten Einstiege lauern — BEVOR es soweit ist.

    WARUM (Kaisers Befund 2026-07-29): Ein Kaufsignal am 0.5-Level oder im Golden Pocket
    entsteht, weil das TIEF einer 4h-Kerze das Level beruehrt hat. Dieses Tief kann in
    Stunde 2 gelegen haben — zum Kerzenschluss steht der Kurs oft schon wieder darueber.
    Wer erst auf die Signal-Nachricht reagiert, findet den genannten Preis dann nicht mehr
    am Markt. Der einzige verlaessliche Weg ist eine Limit-Order, die vorher dort liegt
    (Furkan im Video: "da koennte man dann schon erste Order platzieren").

    Diese Nachricht liefert genau die Zahlen dafuer. Sie wird NICHT bei jedem Lauf
    verschickt, sondern nur, wenn sich die Struktur aendert — sonst waere es Laerm.
    """
    lang = z.get("richtung") == "LONG"
    emoji, _ = STYLE["VORSCHAU"]
    lines = [
        f"{emoji} VORSCHAU — noch KEIN Trigger, nur zur Vorbereitung",
        "",
        f"Neue Struktur erkannt: {'Aufwaerts' if lang else 'Abwaerts'}-Impuls "
        f"{_fmt_usd(z['impuls_start'])} -> {_fmt_usd(z['impuls_ende'])}",
        "",
        f"Hier wuerde {'gekauft' if lang else 'geshortet'}:",
        f"  0.5-Level        {_fmt_usd(z['level_05'])}   (erste Teilposition)",
        f"  Golden Pocket    {_fmt_usd(z['gp_lower'])} - {_fmt_usd(z['gp_upper'])}   (Kern)",
        f"  0.786-Zone       {_fmt_usd(z['level_0786'])}   (Nachkauf)",
        "",
        f"Ungueltig ab       {_fmt_usd(z['invalidation'])}   (dort liegt der Stop)",
    ]
    if z.get("abstand_pct") is not None:
        a = z["abstand_pct"]
        lines.append(f"Abstand Golden Pocket -> Stop: {a:.1f} %"
                     + ("" if a >= 2 else "  ⚠️ unter 2 % — die Engine steigt hier NICHT ein"))
    lines += [
        "",
        _fmt_ts(ts_ms),
        "— Diese Preise kannst du JETZT als Limit-Order hinterlegen. Die Engine meldet "
        "sich erst, wenn der Kurs sie beruehrt hat — dann ist der Preis oft schon weg.",
    ]
    return "\n".join(lines)


def _fmt_usd(x: float) -> str:
    return f"{x:,.0f} $".replace(",", ".")


def _fmt_ts(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.strftime("%d.%m.%Y %H:%M UTC")


def format_signal(sig: dict) -> str:
    """Erzeugt die Telegram-Nachricht fuer ein Signal-Dict (Signal.to_dict())."""
    emoji, _code = STYLE.get(sig["type"], ("\U0001F514", "?"))
    lines = []
    if sig.get("tag") == "FLUSH":
        lines.append("⚠️ AGGRESSIVER FLUSH-EINSTIEG (Kapitulation) — "
                     "DEINE Entscheidung, kein Standard-Signal!")
    lines.append(f"{emoji} {sig['label']}")
    lines.append(f"BTC {_fmt_usd(sig['price'])}")
    if sig.get("tranche_pct"):
        lines.append(f"Tranche: {sig['tranche_pct']} % der Position")
    if sig.get("stop_ref"):
        lines.append(f"Stop-Referenz: {_fmt_usd(sig['stop_ref'])}")
    lines.append(f"Grund: {sig['reason']}")
    lines.append(_fmt_ts(sig["ts"]))
    lines.append("— Kein Trade-Auto-Pilot: Order selbst pruefen und platzieren.")
    return "\n".join(lines)


def send_telegram(text: str, token: str, chat_id: str, timeout: int = 15) -> bool:
    """Sendet eine Nachricht ueber die Telegram-Bot-API. True bei Erfolg."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        with urllib.request.urlopen(url, data=data, timeout=timeout) as resp:
            return json.loads(resp.read().decode()).get("ok", False)
    except Exception as exc:  # noqa: BLE001 — Actions-Log soll den Fehler zeigen
        print(f"Telegram-Fehler: {exc}")
        return False


def send_signals(signals: list[dict], dry_run: bool = False) -> list[str]:
    """Formatiert und sendet alle Signale. Gibt die Nachrichtentexte zurueck.

    Bei dry_run=True (oder fehlendem Token) wird nur formatiert, nichts gesendet.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    messages = [format_signal(s) for s in signals]
    if dry_run or not token or not chat_id:
        for m in messages:
            print("[DRY-RUN]\n" + m + "\n")
        return messages
    for m in messages:
        send_telegram(m, token, chat_id)
    return messages


def send_vorschau(z: dict, ts_ms: int, dry_run: bool = False) -> str:
    """Sendet die Vorschau-Ankuendigung (siehe format_vorschau)."""
    text = format_vorschau(z, ts_ms)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if dry_run or not token or not chat_id:
        print("[DRY-RUN]\n" + text + "\n")
    else:
        send_telegram(text, token, chat_id)
    return text
