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


def test_uebergeordneter_trend_steht_in_den_nachrichten():
    """E33-B: Der Trend gehoert an den ANFANG der Lage - er setzt den Rahmen.
    Furkans Reihenfolge (Transkript 19:16): "uebergeordnet erstmal ein Bias ... dann
    gehe ich rein, schaue mir vor allem die Orderflow Daten an"."""
    from telegram_notify import format_plan, format_vorschau
    lage = {"trend": "unter",
            "trend_text": "Uebergeordnet: Kurs 77.279 $ unter EMA200 (79.140 $)",
            "struktur": "intakt",
            "struktur_text": "Struktur intakt - hoeheres Tief 76.264 $, hoeheres Hoch 82.300 $",
            "spot": "schwach",
            "spot_text": "Spot-Nachfrage schwach (Verkaufsdruck haelt an)"}
    plan = {"richtung": "LONG", "anteil_pct": 65, "einstand": 78807.0, "kurs": 77279.0,
            "stop": {"preis": 75546.0, "grund": "Invalidierung"}, "lage": lage}
    txt = format_plan(plan)
    assert "Uebergeordnet" in txt and "EMA200" in txt
    # Reihenfolge: Trend vor Struktur vor Spot
    assert txt.index("Uebergeordnet") < txt.index("Struktur intakt") < txt.index("Spot-Nachfrage")

    vs = {"richtung": "LONG", "impuls_start": 76264.0, "impuls_ende": 82300.0,
          "level_05": 79282.0, "gp_lower": 78377.0, "gp_upper": 78570.0,
          "level_0786": 77556.0, "invalidation": 76264.0, "lage": lage}
    assert "Uebergeordnet" in format_vorschau(vs, 1789000000000)

    # Fehlt die Trendangabe (zu wenig Historie), bleibt der Rest der Lage stehen
    ohne = {k: v for k, v in lage.items() if not k.startswith("trend")}
    plan2 = dict(plan); plan2["lage"] = ohne
    t2 = format_plan(plan2)
    assert "Uebergeordnet" not in t2 and "Spot-Nachfrage schwach" in t2


def test_ampel_steht_in_den_nachrichten_mit_dem_schlusssatz():
    """E34: Die Ampel fasst zusammen - und sagt im selben Atemzug, dass sie nichts tut.

    Der Schlusssatz ist der wichtigste Teil. Er muss IMMER dastehen, auch bei GUENSTIG,
    damit niemand aus der Zeile eine Handlungsanweisung liest, die keine Messung deckt.
    """
    from telegram_notify import format_plan, format_vorschau
    from strategy_core import ampel, AMPEL_SCHLUSSSATZ
    lage = {"trend": "unter", "trend_text": "Uebergeordnet: Kurs unter EMA200",
            "struktur": "intakt", "struktur_text": "Struktur intakt",
            "spot": "nachgelassen", "spot_text": "Spot-Nachfrage nachgelassen",
            "muster": "UNGESUNDER_ABVERKAUF", "muster_text": "ungesunder Abverkauf"}
    plan = {"richtung": "LONG", "anteil_pct": 65, "einstand": 78807.0, "kurs": 77279.0,
            "stop": {"preis": 75546.0, "grund": "Invalidierung"},
            "lage": lage, "ampel": ampel(lage)}
    txt = format_plan(plan)
    # Seit E38 (21.09.2026) zaehlt Muster 5 NEUTRAL: 1 dafuer (Struktur), 2 dagegen
    # (Trend, Spot) - also "1 von 3" statt vorher "1 von 4".
    assert "Ampel (fuer LONG): UNGUENSTIG" in txt and "1 von 3" in txt
    assert "dafuer:  Struktur" in txt and "Spot-Nachfrage" in txt
    assert AMPEL_SCHLUSSSATZ in txt
    # die Ampel steht UNTER der Lage, nicht davor
    assert txt.index("Lage:") < txt.index("Ampel (")

    vs = {"richtung": "LONG", "impuls_start": 76264.0, "impuls_ende": 82300.0,
          "level_05": 79282.0, "gp_lower": 78377.0, "gp_upper": 78570.0,
          "level_0786": 77556.0, "invalidation": 76264.0,
          "lage": lage, "ampel": ampel(lage)}
    assert "Ampel (fuer LONG): UNGUENSTIG" in format_vorschau(vs, 1789000000000)

    # auch bei GUENSTIG - gerade dann - steht der Schlusssatz dabei
    gut = {"trend": "ueber", "trend_text": "Uebergeordnet: Kurs ueber EMA200",
           "struktur": "intakt", "struktur_text": "Struktur intakt",
           "spot": "stabil", "spot_text": "Spot-Nachfrage stabil",
           "muster": "GESUNDER_TREND", "muster_text": "gesunder Trend"}
    plan2 = dict(plan); plan2["lage"] = gut; plan2["ampel"] = ampel(gut)
    gut_txt = format_plan(plan2)
    assert "Ampel (fuer LONG): GUENSTIG" in gut_txt and AMPEL_SCHLUSSSATZ in gut_txt
    assert "dagegen" not in gut_txt, "ohne Gegenargumente keine leere Zeile"

    # ohne Ampel (zu duenne Lage) faellt der Block ganz weg, statt leer dazustehen
    ohne = dict(plan); ohne.pop("ampel")
    assert "Ampel" not in format_plan(ohne)


def _lage_m5():
    from strategy_core import MUSTER_KLARTEXT, MUSTER_HINWEIS
    return {"trend": "ueber", "trend_text": "Uebergeordnet: Kurs ueber EMA200",
            "spot": "schwach", "spot_text": "Spot-Nachfrage schwach",
            "muster": "UNGESUNDER_ABVERKAUF",
            "muster_text": MUSTER_KLARTEXT["UNGESUNDER_ABVERKAUF"],
            "muster_hinweis": MUSTER_HINWEIS["UNGESUNDER_ABVERKAUF"]}


def test_lage_abruf_zeigt_muster_5_mit_hinweis_und_handytauglich():
    """E38 (Kaiser 21.09.2026): Im Abruf steht, was passiert, und darunter, was danach
    gemessen wurde - jede Zeile unter der Handybreite."""
    from telegram_notify import format_lage
    l = {"kurs": 76000.0, "bein": None, "orderflow": [], "fenster_h": 48,
         "lage": _lage_m5(), "ampel": None}
    txt = format_lage(l, 1_700_000_000_000)
    assert "Short-Wetten" in txt and "Gegenbewegung" in txt
    assert txt.index("Short-Wetten") < txt.index("Gegenbewegung")
    zu_lang = [z for z in txt.splitlines() if len(z) > 38]
    assert not zu_lang, zu_lang


def test_plan_und_vorschau_zeigen_muster_5_umbrochen_mit_hinweis():
    """Plan und Vorschau behalten ihr Format - nur die Muster-Zeilen werden umbrochen,
    weil der neue Text sonst eine Zeile von gut 110 Zeichen waere."""
    from telegram_notify import _lage_zeilen
    zeilen = _lage_zeilen(_lage_m5())
    text = "\n".join(zeilen)
    assert "Short-Wetten" in text and "Gegenbewegung" in text
    muster = [z for z in zeilen if "Muster:" in z or "Wetten" in z or "Liquidation" in z]
    assert muster and all(len(z) <= 38 for z in muster), muster
    # Ein Wort bleibt ganz - "Short-" am Zeilenende und "Wetten" darunter war der
    # erste Entwurf, und er las sich wie ein Tippfehler.
    assert not any(z.rstrip().endswith("-") for z in zeilen), zeilen
    # die uebrigen Zeilen bleiben unveraendert im gewohnten Format
    assert "Lage:  Uebergeordnet: Kurs ueber EMA200" in zeilen


# ------------------------------------------ E41: Rueckeroberungs-Regel live (21.09.2026)

def _e41_m(art="wartet", lang=True, noch=1):
    if art == "wartet":
        marke = 97608.0 if lang else 102000.0
        return {"art": "wartet", "ts": 1_768_766_400_000, "lang": lang, "marke": marke,
                "kurs": 97400.0 if lang else 102204.0, "kerze_nr": 1, "von": noch,
                "noch": noch, "boden": marke * (0.95 if lang else 1.05)}
    return {"art": "zurueck", "ts": 1_768_766_400_000, "kurs": 98500.0, "marke": 97608.0,
            "lang": lang}


def test_stop_wartet_nachricht_sagt_was_passiert_und_was_als_naechstes():
    from telegram_notify import format_stop_rueckeroberung
    txt = format_stop_rueckeroberung(_e41_m())
    assert txt.startswith("⏳ STOP WARTET")
    assert "BTC 97.400 $" in txt
    einzeilig = " ".join(txt.split())
    assert "Kerzenschluss 0,2 % unter der Invalidierung 97.608 $." in einzeilig
    assert "Schliesst die naechste Kerze wieder ueber 97.608 $, hat die Marke gehalten." in einzeilig
    assert "Sonst kommt der Stop." in einzeilig
    assert "Bis dahin kein Nachkauf." in einzeilig


def test_stop_wartet_nennt_den_harten_boden_nur_wenn_er_noch_zaehlt():
    """Bei EINER Kerze Wartezeit stoppt die naechste Kerze unter der Marke ohnehin - der
    harte Boden waere dort eine Zahl ohne Bedeutung, die verwirrt."""
    from telegram_notify import format_stop_rueckeroberung
    assert "92.728" not in format_stop_rueckeroberung(_e41_m(noch=1))
    drei = " ".join(format_stop_rueckeroberung(_e41_m(noch=3)).split())
    assert "Schluss unter 92.728 $: sofort Stop." in drei
    assert "eine der naechsten 3 Kerzen" in drei


def test_marke_zurueckerobert_nachricht():
    from telegram_notify import format_stop_rueckeroberung
    txt = " ".join(format_stop_rueckeroberung(_e41_m("zurueck")).split())
    assert "MARKE ZURUECKEROBERT" in txt
    assert "Schluss wieder ueber 97.608 $." in txt
    assert "naechste Kerzenschluss unter 97.608 $ loest den Stop sofort aus" in txt


def test_e41_nachrichten_short_spiegelbildlich():
    from telegram_notify import format_stop_rueckeroberung
    txt = " ".join(format_stop_rueckeroberung(_e41_m(lang=False)).split())
    assert "0,2 % ueber der Invalidierung 102.000 $" in txt
    assert "wieder unter 102.000 $" in txt
    z = " ".join(format_stop_rueckeroberung({**_e41_m("zurueck"), "lang": False}).split())
    assert "Schluss wieder unter 97.608 $." in z and "Kerzenschluss ueber 97.608 $" in z


def test_e41_nachrichten_sind_handybreit():
    from telegram_notify import ZEILE_MAX, format_stop_rueckeroberung
    for m in (_e41_m(), _e41_m(noch=3), _e41_m("zurueck"), _e41_m(lang=False)):
        txt = format_stop_rueckeroberung(m)
        zu_lang = [z for z in txt.splitlines() if len(z) > ZEILE_MAX]
        assert not zu_lang, zu_lang


def _e41_plan(**stop):
    return {"richtung": "LONG", "anteil_pct": 40, "einstand": 99000.0, "kurs": 98000.0,
            "stop": {"preis": 97608.0, "grund": "Invalidierung", **stop}}


def test_plan_stop_zeile_folgt_der_rueckeroberungs_regel():
    """Der Plan sagt "diese Preise kannst du hinterlegen". Stuende dort weiter "Stop bei
    Kerzenschluss darunter", widerspraeche er der Engine."""
    from telegram_notify import format_plan
    alt = format_plan(_e41_plan())
    assert "Stop 97.608 $ — Invalidierung, bei Kerzenschluss darunter" in alt
    neu = format_plan(_e41_plan(rueckeroberung=1, boden=92727.6, geprueft=False, wartet=0))
    assert ("Stop 97.608 $ — Invalidierung. Ein Kerzenschluss darunter loest noch nicht "
            "aus: Stop erst, wenn auch die naechste Kerze darunter schliesst — ab "
            "92.728 $ sofort") in neu
    assert "bei Kerzenschluss darunter" not in neu and "Achtung" not in neu


def test_plan_warnt_wenn_die_engine_gerade_wartet():
    from telegram_notify import format_plan
    txt = format_plan(_e41_plan(rueckeroberung=1, boden=92727.6, geprueft=False, wartet=1))
    assert "Achtung: Die letzte Kerze schloss schon darunter" in txt


def test_plan_nennt_die_gepruefte_marke():
    from telegram_notify import format_plan
    txt = format_plan(_e41_plan(rueckeroberung=1, boden=92727.6, geprueft=True, wartet=0))
    assert "schon einmal zurueckerobert: naechster Kerzenschluss darunter = Stop" in txt
    assert "loest noch nicht aus" not in txt


# ----------------------------- E40: STH-Kostenbasis als Zeile im Lage-Abruf (21.09.2026)

def _lage_mit_sth(kurs, sth):
    return {"kurs": kurs, "bein": None, "orderflow": [], "fenster_h": 48,
            "lage": None, "ampel": None, "sth": sth}


def test_lage_abruf_zeigt_die_sth_kostenbasis_mit_abstand_und_stand():
    from telegram_notify import format_lage
    sth = {"wert": 71262.19, "datum": "2026-09-14", "quelle": "bitview.space"}
    txt = format_lage(_lage_mit_sth(76000.0, sth), 1_700_000_000_000)
    zeilen = txt.splitlines()
    assert "STH-Kostenbasis: 71.262 $" in zeilen
    assert "Kurs 6,6 % darueber" in zeilen
    einzeilig = " ".join(txt.split())
    assert "Stand 14.09.2026" in einzeilig and "Nur Anzeige, keine Regel." in einzeilig
    unter = format_lage(_lage_mit_sth(70000.0, sth), 1_700_000_000_000)
    assert "Kurs 1,8 % darunter" in unter.splitlines()


def test_lage_abruf_ohne_sth_hat_keine_leere_zeile_dafuer():
    from telegram_notify import format_lage
    for sth in (None, {}, {"wert": 0, "datum": "2026-09-14"}):
        assert "STH" not in format_lage(_lage_mit_sth(76000.0, sth), 1_700_000_000_000)


def test_sth_zeile_ist_handybreit():
    from telegram_notify import ZEILE_MAX, format_lage
    sth = {"wert": 171262.19, "datum": "2026-09-14", "quelle": "bitview.space"}
    txt = format_lage(_lage_mit_sth(176000.0, sth), 1_700_000_000_000)
    zu_lang = [z for z in txt.splitlines() if len(z) > ZEILE_MAX]
    assert not zu_lang, zu_lang
