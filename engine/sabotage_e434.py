"""Sabotage-Probe fuer E43.4 (Open Interest in Kontrakten statt Dollar, Schalter
muster_oi), 26.09.2026.

Befund A3 der Gesamtpruefung (docs/PRUEFUNG-2026-09-26-GESAMT.md). Jede Zeile hier ist
ein Fehler, den man beim Bauen wirklich machen koennte - und der entweder den Befund
still wieder verdecken (die Muster lesen doch wieder Dollar), eine OI-Bewegung erfinden
(aufgefuellte Dollar-Werte durch einen neuen Kurs geteilt) oder Live und Backtest
auseinanderlaufen lassen wuerde.

Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Nie mitten im Lauf
abbrechen - die verfaelschte Datei wird erst am Ende jeder Sabotage wiederhergestellt.
Aufruf: python3 sabotage_e434.py
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    # --- die Rechnung in strategy_core ------------------------------------------------
    ("btc faellt still auf Dollar zurueck", "strategy_core.py",
     '    if muster_oi == "btc":\n        a, b = f[0].oi_btc, f[-1].oi_btc',
     '    if muster_oi == "BTC":\n        a, b = f[0].oi_btc, f[-1].oi_btc'),
    ("classify_pattern ignoriert muster_oi", "strategy_core.py",
     "    oi_chg = oi_aenderung(f, muster_oi)", "    oi_chg = oi_aenderung(f)"),
    ("Leer-Waechter fehlt (keine Kontrakt-Reihe -> Division durch null)", "strategy_core.py",
     "        return (b - a) / a if a and b else 0.0", "        return (b - a) / a"),
    ("usd rechnet im Randfall anders als vor E43.4", "strategy_core.py",
     "    return (f[-1].oi - f[0].oi) / f[0].oi if f[0].oi else 0.0",
     "    return (f[-1].oi - f[0].oi) / f[0].oi if f[0].oi and f[-1].oi else 0.0"),
    ("oi_in_btc: ein Kurs fuer alle Punkte", "strategy_core.py",
     "    return {ts: v / kurs[ts] for ts, v in oi_usd.items() if kurs.get(ts)}",
     "    return {ts: v / kurs[min(kurs)] for ts, v in oi_usd.items() if kurs.get(ts)}"),
    ("oi_in_btc: Punkt ohne Kerze bekommt einen Ersatzkurs", "strategy_core.py",
     "    return {ts: v / kurs[ts] for ts, v in oi_usd.items() if kurs.get(ts)}",
     "    return {ts: v / kurs.get(ts, 60000.0) for ts, v in oi_usd.items()}"),
    ("oi_in_btc multipliziert statt zu teilen", "strategy_core.py",
     "    return {ts: v / kurs[ts] for ts, v in oi_usd.items() if kurs.get(ts)}",
     "    return {ts: v * kurs[ts] for ts, v in oi_usd.items() if kurs.get(ts)}"),
    ("Muster 4 liest weiter Dollar", "strategy_core.py",
     "        if spot_turning and (oi_chg <= -oi_wipeout_pct or long_liq_spike):",
     "        if spot_turning and (oi_aenderung(f) <= -oi_wipeout_pct or long_liq_spike):"),
    ("Muster 5 liest weiter Dollar", "strategy_core.py",
     "    if (price_chg <= -sharp_move_pct / 2 and spot < 0 and oi_chg >= -0.01",
     "    if (price_chg <= -sharp_move_pct / 2 and spot < 0 and oi_aenderung(f) >= -0.01"),
    ("Muster 3 liest weiter Dollar", "strategy_core.py",
     "    if price_chg >= sharp_move_pct / 2 and (oi_chg <= -0.02 or short_liq_spike):",
     "    if price_chg >= sharp_move_pct / 2 and (oi_aenderung(f) <= -0.02 or short_liq_spike):"),
    ("Muster 2 liest weiter Dollar", "strategy_core.py",
     "        if (price_chg > 0 and cvd_pump and oi_chg >= 0.03",
     "        if (price_chg > 0 and cvd_pump and oi_aenderung(f) >= 0.03"),
    ("Muster 1 liest weiter Dollar", "strategy_core.py",
     "            and 0 <= oi_chg <= 0.10):",
     "            and 0 <= oi_aenderung(f) <= 0.10):"),
    ("evaluate reicht muster_oi nicht an classify_pattern weiter", "strategy_core.py",
     "                               muster_oi=muster_oi) if flow else Pattern.NEUTRAL",
     '                               muster_oi="usd") if flow else Pattern.NEUTRAL'),
    # --- Datenweg Backtest ----------------------------------------------------------
    ("Backtest fuellt Dollar auf und teilt dann durch den Kurs (naiver Weg)", "backtest.py",
     "                              latest_leq(btc_pairs, ts, first_btc)))",
     "                              (oi_val / float(k[4]) if oi_pairs else 0.0)))"),
    ("Backtest rechnet mit dem Eroeffnungs- statt dem Schlusskurs", "backtest.py",
     "oi_in_btc(oi_map, {int(k[0]): float(k[4]) for k in raw})",
     "oi_in_btc(oi_map, {int(k[0]): float(k[1]) for k in raw})"),
    ("Backtest ohne OI-Daten erfindet eine Kontrakt-Reihe (1.0 durch den Kurs)",
     "backtest.py",
     "        if oi_map else []\n    first_btc",
     "        if oi_map else sorted(oi_in_btc({int(k[0]): 1.0 for k in raw},\n"
     "                                        {int(k[0]): float(k[4]) for k in raw}).items())\n"
     "    first_btc"),
    # --- Datenweg live --------------------------------------------------------------
    ("Live fuellt Dollar auf und teilt dann durch den Kurs (naiver Weg)", "main.py",
     "                              _latest_leq(btc_pairs, c_ts, default=first_btc)))",
     "                              (oi_val / float(k[4]) if use_cz else 0.0)))"),
    ("Live rechnet mit dem Kurs der Folgekerze", "main.py",
     "    kurs = {int(k[0]): float(k[4]) for k in spot_raw if int(k[6]) <= now_ms}",
     "    kurs = {int(k[0]) - CANDLE_MS: float(k[4]) for k in spot_raw if int(k[6]) <= now_ms}"),
    ("Kraken-Rueckfall teilt doch durch den Kurs", "main.py",
     "                                 kurs).items()) if use_cz else []",
     "                                 kurs).items()) if use_cz else "
     "sorted(oi_in_btc(dict(oi_pairs), kurs).items())"),
    # --- Verdrahtung Konfig, Anzeige, Gitter -----------------------------------------
    ("muster_oi fehlt in EVAL_DEFAULTS", "main.py",
     '    "muster_oi": "usd",\n}', "}"),
    ("btc still als Vorgabe (live eingeschaltet ohne Messung)", "main.py",
     '    "muster_oi": "usd",', '    "muster_oi": "btc",'),
    ("Anzeige rechnet das OI anders als der Handel", "main.py",
     'muster_oi=par["muster_oi"])\n'
     '                         if flow else None,\n'
     '                         trend_period=par.get("trend_ema", 200))\n'
     '    # E34: die Ampel',
     'muster_oi="usd")\n'
     '                         if flow else None,\n'
     '                         trend_period=par.get("trend_ema", 200))\n'
     '    # E34: die Ampel'),
    ("config.json schaltet btc ohne Go ein", "../site/data/config.json",
     ' "muster_oi": "usd",', ' "muster_oi": "btc",'),
    ("muster_oi fehlt in EVAL_KEYS (Zeile laeuft still mit usd)", "backtest.py",
     '"muster_cvd", "muster_oi")', '"muster_cvd")'),
    ("Gitterzeile misst nichts (usd statt btc)", "backtest.py",
     'bein_richtung="bias", muster_oi="btc"),', 'bein_richtung="bias", muster_oi="usd"),'),
    ("Gitterzeile mit zweitem Unterschied (muster_cvd)", "backtest.py",
     'bein_richtung="bias", muster_oi="btc"),',
     'bein_richtung="bias", muster_cvd="usd", muster_oi="btc"),'),
    # --- Entscheidungsregel, Vorprobe, Bericht --------------------------------------
    ("Regel: eine Haelfte genuegt", "backtest.py",
     "    beide = (btc[\"h1\"] - live[\"h1\"] >= E434_RAUSCHGRENZE\n"
     "             and btc[\"h2\"] - live[\"h2\"] >= E434_RAUSCHGRENZE)",
     "    beide = (btc[\"h1\"] - live[\"h1\"] >= E434_RAUSCHGRENZE\n"
     "             or btc[\"h2\"] - live[\"h2\"] >= E434_RAUSCHGRENZE)"),
    ("Regel: 'besser' ohne Rauschgrenze", "backtest.py",
     "    beide = (btc[\"h1\"] - live[\"h1\"] >= E434_RAUSCHGRENZE",
     "    beide = (btc[\"h1\"] - live[\"h1\"] > 0"),
    ("Regel: Rueckgang falsch herum", "backtest.py",
     '    dd_ok = btc["dd"] >= live["dd"] - E434_DD_TOLERANZ',
     '    dd_ok = btc["dd"] <= live["dd"] - E434_DD_TOLERANZ'),
    ("Regel: Rueckgang zaehlt nicht", "backtest.py",
     '    return {"beide_haelften_besser": beide, "rueckgang_ok": dd_ok,\n'
     '            "einschalten": beide and dd_ok}\n\n\ndef e434_umklassifiziert',
     '    return {"beide_haelften_besser": beide, "rueckgang_ok": dd_ok,\n'
     '            "einschalten": beide}\n\n\ndef e434_umklassifiziert'),
    ("Vorprobe vergleicht usd mit usd", "backtest.py",
     '        b = classify_pattern(cs, fl, muster_oi="btc")',
     '        b = classify_pattern(cs, fl, muster_oi="usd")'),
    ("Vorprobe: Kontrakt-Spalte zaehlt Dollar", "backtest.py",
     '            z["btc"] += oi_ok(o_btc)', '            z["btc"] += oi_ok(o_usd)'),
    ("Vorprobe: jede Kerze zaehlt als echter OI-Punkt", "backtest.py",
     '        out["oi_kerzen"] += c.ts in oi_ts', '        out["oi_kerzen"] += 1'),
    ("Vorprobe bekommt die OI-Punkte nicht", "backtest.py",
     "e434_umklassifiziert(candles, flow, eff_start, oi_map)",
     "e434_umklassifiziert(candles, flow, eff_start)"),
    ("Bericht urteilt ohne echten OI-Punkt", "backtest.py",
     '    if not umkl["oi_kerzen"] or not umkl["verschieden"]:',
     '    if not umkl["verschieden"]:'),
    ("Bericht urteilt ohne umklassifizierte Kerze", "backtest.py",
     '    if not umkl["oi_kerzen"] or not umkl["verschieden"]:',
     '    if not umkl["oi_kerzen"]:'),
    ("Bericht-Abschnitt nicht verdrahtet", "backtest.py",
     'lambda: e434_abschnitt(results, halves, panel_cfg["label"], _e434),',
     'lambda: [],'),
]

def lauf():
    shutil.rmtree(ENG / "__pycache__", ignore_errors=True)
    umg = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run([sys.executable, "run_tests.py"], cwd=ENG, env=umg,
                       capture_output=True, text=True, timeout=600)
    letzte = [z for z in r.stdout.splitlines() if "passed" in z]
    return (letzte[-1] if letzte else "?"), r.stdout


signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError()))
ungefangen = []
for name, datei, alt, neu in SABOTAGEN:
    pfad = ENG / datei
    orig = pfad.read_text(encoding="utf-8")
    if alt not in orig:
        print(f"!! VORLAGE NICHT GEFUNDEN: {name}")
        ungefangen.append(name + " [Vorlage fehlt]")
        continue
    signal.alarm(700)
    try:
        pfad.write_text(orig.replace(alt, neu, 1), encoding="utf-8")
        zeile, voll = lauf()
        rot = [z.split("::")[-1] for z in voll.splitlines() if z.startswith("FAIL")]
        if rot:
            print(f"OK  {name}\n    -> {zeile}  | {', '.join(rot[:3])}")
        else:
            print(f"!!! UNGEFANGEN: {name}\n    -> {zeile}")
            ungefangen.append(name)
    finally:
        pfad.write_text(orig, encoding="utf-8")
        signal.alarm(0)

print("\n" + "=" * 60)
zeile, _ = lauf()
print("nach Wiederherstellung:", zeile)
print("ungefangen:", ungefangen or "keine")
