"""Sabotage-Probe fuer E43.5 (Test "mehr Historie" erreicht Muster 2) und E43.3
(Muster 2 in Dollar, Schalter muster_cvd), 26.09.2026.

Befunde A2 und A4 der Gesamtpruefung (docs/PRUEFUNG-2026-09-26-GESAMT.md). Jede Zeile
hier ist ein Fehler, den man beim Bauen wirklich machen koennte - und der entweder den
Befund still wieder verdecken oder die neue Rechnung still falsch machen wuerde.

Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Nie mitten im Lauf
abbrechen - die verfaelschte Datei wird erst am Ende jeder Sabotage wiederhergestellt.
Aufruf: python3 sabotage_e433.py
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    # --- E43.5: der Test selbst -------------------------------------------------------
    ("Test schneidet wieder EINE vorgerechnete Summe aus", "test_strategy_core.py",
     "    for i in range(aus, bis):\n        sd, fd, oi, fu = roh[i]\n"
     "        spot += sd\n        fut += fd\n"
     "        out.append(FlowPoint(kerzen[i].ts, spot, fut, oi, fu))",
     "    for i in range(0, bis):\n        sd, fd, oi, fu = roh[i]\n"
     "        spot += sd\n        fut += fd\n        if i >= aus:\n"
     "            out.append(FlowPoint(kerzen[i].ts, spot, fut, oi, fu))"),
    ("Szenario ohne Pump-Phase", "test_strategy_core.py",
     "PUMP_ZYKLUS, PUMP_AB, PUMP_BIS = 36, 20, 32",
     "PUMP_ZYKLUS, PUMP_AB, PUMP_BIS = 36, 20, 20"),
    ("Szenario mit zu schwachem OI-Anstieg (wie der alte Test)", "test_strategy_core.py",
     "        oi = 1e9 * (1 + 0.006 * (min(ph, PUMP_BIS - 1)",
     "        oi = 1e9 * (1 + 0.0006 * (min(ph, PUMP_BIS - 1)"),
    # --- E43.5: der Code, den der Befund-Test festhaelt -------------------------------
    ("_slope ohne Division (alt rechnet nicht mehr wie bisher)", "strategy_core.py",
     "    return (vals[-1] - vals[0]) / abs(vals[0])",
     "    return (vals[-1] - vals[0])"),
    ("Muster 2 unerreichbar (OI-Schwelle zehnfach)", "strategy_core.py",
     "        if (price_chg > 0 and cvd_pump and oi_chg >= 0.03",
     "        if (price_chg > 0 and cvd_pump and oi_chg >= 0.3"),
    # --- E43.3: die neue Rechnung in strategy_core -----------------------------------
    ("usd rechnet das Futures-Delta nicht in Dollar um (bleibt BTC)", "strategy_core.py",
     "        fut += (p.fut_cvd - vorher.fut_cvd) * k",
     "        fut += (p.fut_cvd - vorher.fut_cvd)"),
    ("usd nimmt einen Kurs fuer das ganze Fenster", "strategy_core.py",
     "        fut += (p.fut_cvd - vorher.fut_cvd) * k",
     "        fut += (p.fut_cvd - vorher.fut_cvd) * c[0].close"),
    ("usd summiert den kumulierten Stand statt des Deltas", "strategy_core.py",
     "        fut += (p.fut_cvd - vorher.fut_cvd) * k",
     "        fut += p.fut_cvd * k"),
    ("usd nimmt beim Spot doch wieder den Stand am Fensteranfang", "strategy_core.py",
     "    return f[-1].spot_cvd - f[0].spot_cvd, fut",
     "    return (f[-1].spot_cvd - f[0].spot_cvd) / abs(f[0].spot_cvd or 1), fut"),
    ("fehlende Kerze wird mit Ersatzkurs gerechnet", "strategy_core.py",
     "        k = kurs.get(p.ts)\n        if k is None:\n            return None",
     "        k = kurs.get(p.ts, 60000.0)\n        if k is None:\n            return None"),
    ("Vergleich falsch herum", "strategy_core.py",
     "            cvd_pump = d is not None and d[1] > 0 and d[0] <= d[1] / 3",
     "            cvd_pump = d is not None and d[1] > 0 and d[0] >= d[1] / 3"),
    ("Faktor 3 vergessen", "strategy_core.py",
     "            cvd_pump = d is not None and d[1] > 0 and d[0] <= d[1] / 3",
     "            cvd_pump = d is not None and d[1] > 0 and d[0] <= d[1]"),
    ("'Futures steigt' fehlt bei usd", "strategy_core.py",
     "            cvd_pump = d is not None and d[1] > 0 and d[0] <= d[1] / 3",
     "            cvd_pump = d is not None and d[0] <= d[1] / 3"),
    ("usd faellt still auf die alte Rechnung zurueck", "strategy_core.py",
     '        if muster_cvd == "usd":\n            # E43.3',
     '        if muster_cvd == "USD":\n            # E43.3'),
    ("evaluate reicht muster_cvd nicht an classify_pattern weiter", "strategy_core.py",
     "    pattern = classify_pattern(candles, flow, muster_cvd=muster_cvd,\n",
     "    pattern = classify_pattern(candles, flow,\n"),
    # --- E43.3: Verdrahtung Backtest, Konfig, Anzeige --------------------------------
    ("muster_cvd fehlt in EVAL_KEYS (Zeile laeuft still mit alt)", "backtest.py",
     '"ampel_filter", "muster_cvd", "muster_oi")', '"ampel_filter", "muster_oi")'),
    ("Gitterzeile misst nichts (alt statt usd)", "backtest.py",
     'bein_richtung="bias", muster_cvd="usd"),', 'bein_richtung="bias", muster_cvd="alt"),'),
    ("Gitterzeile mit zweitem Unterschied (alter Stop)", "backtest.py",
     'stop_rueckeroberung=1,\n      bein_richtung="bias", muster_cvd="usd"),',
     'stop_rueckeroberung=0,\n      bein_richtung="bias", muster_cvd="usd"),'),
    ("usd still als Vorgabe (live eingeschaltet ohne Messung)", "main.py",
     '    "muster_cvd": "alt",', '    "muster_cvd": "usd",'),
    ("Anzeige rechnet Muster 2 anders als der Handel", "main.py",
     'pattern=classify_pattern(candles, flow, muster_cvd=par["muster_cvd"],\n'
     '                                                  muster_oi=par["muster_oi"])\n'
     '                         if flow else None,\n'
     '                         trend_period=par.get("trend_ema", 200))\n'
     '    # E34: die Ampel',
     'pattern=classify_pattern(candles, flow,\n'
     '                                                  muster_oi=par["muster_oi"])\n'
     '                         if flow else None,\n'
     '                         trend_period=par.get("trend_ema", 200))\n'
     '    # E34: die Ampel'),
    ("config.json schaltet usd ohne Go ein", "../site/data/config.json",
     ' "muster_cvd": "alt",', ' "muster_cvd": "usd",'),
    # --- E43.3: Entscheidungsregel und Vorprobe im Bericht ---------------------------
    ("Regel: eine Haelfte genuegt", "backtest.py",
     "    beide = (usd[\"h1\"] - live[\"h1\"] >= E433_RAUSCHGRENZE\n"
     "             and usd[\"h2\"] - live[\"h2\"] >= E433_RAUSCHGRENZE)",
     "    beide = (usd[\"h1\"] - live[\"h1\"] >= E433_RAUSCHGRENZE\n"
     "             or usd[\"h2\"] - live[\"h2\"] >= E433_RAUSCHGRENZE)"),
    ("Regel: 'besser' ohne Rauschgrenze", "backtest.py",
     "    beide = (usd[\"h1\"] - live[\"h1\"] >= E433_RAUSCHGRENZE",
     "    beide = (usd[\"h1\"] - live[\"h1\"] > 0"),
    ("Regel: Rueckgang falsch herum", "backtest.py",
     '    dd_ok = usd["dd"] >= live["dd"] - E433_DD_TOLERANZ',
     '    dd_ok = usd["dd"] <= live["dd"] - E433_DD_TOLERANZ'),
    ("Regel: Rueckgang zaehlt nicht", "backtest.py",
     '            "einschalten": beide and dd_ok}',
     '            "einschalten": beide}'),
    ("Vorprobe: Live-Stand wird nicht abgezogen", "backtest.py",
     "        fl_live = [replace(p, spot_cvd=p.spot_cvd - off_s, fut_cvd=p.fut_cvd - off_f)",
     "        fl_live = [replace(p, spot_cvd=p.spot_cvd, fut_cvd=p.fut_cvd)"),
    ("Vorprobe: nicht nachstellbare Kerzen zaehlen als live gleich", "backtest.py",
     "        if i_s < 0:\n            continue\n        off_s",
     "        if i_s < 0:\n            i_s = i_f = 0\n        off_s"),
    ("Bericht urteilt auch ohne umklassifizierte Kerze", "backtest.py",
     '    if not umkl["verschieden"]:', '    if False:'),
    ("Bericht-Abschnitt nicht verdrahtet", "backtest.py",
     'lambda: e433_abschnitt(results, halves, panel_cfg["label"], _umkl),',
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
