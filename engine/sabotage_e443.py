"""Sabotage-Probe fuer E44.3 (E42 "Ausbruch mit Ruecktest"), 27.09.2026.

Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Jede Zeile hier ist
ein Fehler, den man beim Bauen wirklich machen koennte - und der die Engine still anders
handeln liesse, statt zu krachen. Nie mitten im Lauf abbrechen: die verfaelschte Datei
wird erst am Ende jeder Sabotage wiederhergestellt.
Aufruf: python3 sabotage_e443.py   (am besten mit Protokoll: ... > sabotage_e443.log)
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    # --- die Regel selbst (ruecktest_schritt) ----------------------------------------
    ("Ausbruch schon beim Docht", "strategy_core.py",
     "        jenseits, diesseits = cur.close > marke, cur.close < marke",
     "        jenseits, diesseits = cur.high > marke, cur.close < marke"),
    ("Schluss unter der Marke zaehlt doch als Ruecktest", "strategy_core.py",
     '    if diesseits:\n        return "gescheitert"',
     '    if False:\n        return "gescheitert"'),
    ("Zone ohne die 0,5 %", "strategy_core.py",
     "        beruehrt = cur.low <= marke * (1 + RUECKTEST_TOL)",
     "        beruehrt = cur.low <= marke"),
    ("Fenster eine Kerze zu lang", "strategy_core.py",
     '    return "verfallen" if seit >= fenster else ""',
     '    return ""'),
    ("Fenster eine Kerze zu kurz", "strategy_core.py",
     '    if seit > fenster:\n        return "verfallen"',
     '    if seit >= fenster:\n        return "verfallen"'),
    ("Short-Seite rechnet wie Long", "strategy_core.py",
     "        jenseits, diesseits = cur.close < marke, cur.close > marke",
     "        jenseits, diesseits = cur.close > marke, cur.close < marke"),
    ("Ausbruchskerze zaehlt als Ruecktest", "strategy_core.py",
     '        return "ausbruch" if jenseits else ""',
     '        return ("ruecktest" if beruehrt else "ausbruch") if jenseits else ""'),
    ("kerzen_seit zaehlt die Ausbruchskerze mit", "strategy_core.py",
     "        if candles[-k].ts == ts:\n            return k - 1",
     "        if candles[-k].ts == ts:\n            return k"),
    # --- Einbindung in evaluate -----------------------------------------------------
    ("Verkaufskerze wird schon als Fenster bewertet", "strategy_core.py",
     "    if pos.e42_marke is not None and pos.e42_start_ts != cur.ts:",
     "    if pos.e42_marke is not None:"),
    ("Gescheiterter Ausbruch bleibt stehen", "strategy_core.py",
     "            pos.e42_ausbruch_ts = -1                     # auf einen neuen Ausbruch warten",
     "            pass"),
    ("Stop beendet die Beobachtung nicht", "strategy_core.py",
     "            _e42_ende()                      # E44.3: nach einem Stop wird nicht beobachtet",
     "            pass"),
    ("Kein Rest-Verkauf startet eine Beobachtung", "strategy_core.py",
     "                    # E44.3: Rest-Verkauf (kein Stop) -> naechstes Pivot jenseits beobachten\n"
     "                    signals[-1].reason += _e42_beobachten(",
     "                    # E44.3: Rest-Verkauf (kein Stop) -> naechstes Pivot jenseits beobachten\n"
     "                    signals[-1].reason += '' and _e42_beobachten("),
    ("Beobachtung auch auf eine schon gekaufte Marke", "strategy_core.py",
     "        if not ausbruch_ruecktest or marke is None or marke == pos.e42_gekauft:",
     "        if not ausbruch_ruecktest or marke is None:"),
    ("Kaufen trotz voller Investition", "strategy_core.py",
     "            elif bestand_nach(_bestand_start, signals) >= 100:",
     "            elif False:"),
    ("Zweiter Rueckkauf auf dieselbe Marke", "strategy_core.py",
     "            elif _m == pos.e42_gekauft:",
     "            elif False:"),
    ("Aus FLAT ohne passendes Bein gekauft", "strategy_core.py",
     "            elif _flat and (imp is None or imp.up != _lang):",
     "            elif _flat and imp is None:"),
    ("Rueckkauf zum Markenpreis statt zum Schluss", "strategy_core.py",
     "                    cur.ts, rt, cur.close, RUECKKAUF_TRANCHE,",
     "                    cur.ts, rt, _m, RUECKKAUF_TRANCHE,"),
    ("Aus FLAT: Ziele nicht vom Ruecktest-Extrem", "strategy_core.py",
     "                    pos.retrace_extreme = cur.low if _lang else cur.high\n"
     "                rt = SignalType.RUECKKAUF",
     "                    pos.retrace_extreme = imp.start.price\n"
     "                rt = SignalType.RUECKKAUF"),
    ("Beobachtung laeuft nach dem Rueckkauf weiter", "strategy_core.py",
     "                pos.e42_gekauft = _m\n                _e42_ende()",
     "                pos.e42_gekauft = _m"),
    ("Rueckkauf zaehlt in den Einstand (Stop der Position wandert)", "strategy_core.py",
     "        if s.type in _ENTRY_TYPES and s.tranche_pct > 0:",
     "        if (s.type in _ENTRY_TYPES or s.type in _RUECKKAUF_TYPES) and s.tranche_pct > 0:"),
    ("Bestand wird nicht fortgeschrieben", "strategy_core.py",
     "    pos.bestand_pct = bestand_nach(_bestand_start, signals)\n",
     ""),
    ("no_flip sieht den Stop des Teils nicht", "strategy_core.py",
     "        return not (no_flip and any(x.type in _TEILVERKAUF_TYPES\n"
     "                                    or x.type in _RUECKKAUF_STOP_TYPES for x in signals))",
     "        return not (no_flip and any(x.type in _TEILVERKAUF_TYPES for x in signals))"),
    # --- der Stop des Rueckkauf-Teils ------------------------------------------------
    ("Stop des Teils verkauft die ganze Position", "strategy_core.py",
     "        elif _teil_stop and pos.entry_pct == 0:",
     "        elif _teil_stop:"),
    ("Stop des Teils ohne Rueckeroberungs-Regel", "strategy_core.py",
     "    hit, _preis, grund = stop_entscheidung(m, cur, marke, lang,\n"
     "                                           rueckeroberung=rueckeroberung)",
     "    hit, _preis, grund = stop_entscheidung(m, cur, marke, lang,\n"
     "                                           rueckeroberung=0)"),
    ("Merker des Teils werden nicht zurueckgeschrieben", "strategy_core.py",
     "    pos.e42_teil_wartet, pos.e42_teil_wartet_inv, pos.e42_teil_geprueft = \\\n"
     "        m.stop_wartet, m.stop_wartet_inv, m.stop_geprueft",
     "    pass"),
    ("Aus FLAT: Stop des Teils laesst eine leere Position stehen", "strategy_core.py",
     "                                  + _teil_grund))\n            _reset_position(pos)",
     "                                  + _teil_grund))\n            pass"),
    ("Reset vergisst den Rueckkauf-Teil", "strategy_core.py",
     "    pos.e42_teil_marke = None\n    pos.e42_teil_wartet = 0\n",
     "    pos.e42_teil_wartet = 0\n"),
    # --- Live-Engine (main.py) --------------------------------------------------------
    ("Live-Engine speichert das Warten des Teils nicht", "main.py",
     '         "e42_teil_wartet": pos.e42_teil_wartet,\n', ""),
    ("Live-Engine liest den Ausbruch nicht", "main.py",
     '    pos.e42_ausbruch_ts = int(d.get("e42_ausbruch_ts", -1))',
     "    pos.e42_ausbruch_ts = -1"),
    ("Live-Engine speichert die gekaufte Marke nicht", "main.py",
     '         "e42_gekauft": pos.e42_gekauft, ', "         "),
    ("Live-Engine speichert den Bestand nicht", "main.py",
     '         "bestand_pct": pos.bestand_pct,\n', ""),
    ("Altbestand ohne Bestand gilt als leer", "main.py",
     'int(d.get("bestand_pct", min(100, pos.entry_pct or 0)) or 0)',
     'int(d.get("bestand_pct", 0) or 0)'),
    ("E42-Meldungen werden nicht gesendet", "main.py",
     "        for m in m42:\n            send_text(format_ruecktest(m), dry_run=dry_run)\n",
     ""),
    ("Signale wieder gesammelt nach allen Meldungen", "main.py",
     "        if sigs:\n            send_signals(sigs, dry_run=dry_run)\n",
     "    for _a, _b, sigs in pakete:\n        if sigs:\n            send_signals(sigs, dry_run=dry_run)\n"),
    ("Plan nennt den Stop des Teils nicht", "main.py",
     '        plan["rueckkauf_teil"] = teil\n', ""),
    ("Plan meldet sich nicht, wenn der Teil dazukommt", "main.py",
     '            out.append(("rueckkauf-stop", (p["rueckkauf_teil"]["marke"],)))',
     "            pass"),
    # --- Backtest-Abrechnung -----------------------------------------------------------
    ("Rueckkauf wird nicht gebucht", "backtest.py",
     '        if t in ("KAUF_1", "KAUF_2", "NACHKAUF", "RUECKKAUF"):',
     '        if t in ("KAUF_1", "KAUF_2", "NACHKAUF"):'),
    ("Stop des Teils verkauft einen Anteil am Hoechstbestand", "backtest.py",
     "                sell = min(units, rk_units)",
     "                sell = min(units, LADDER_TRANCHE / 100.0 * peak_units)"),
    ("Teilverkaeufe nehmen den Teil nicht anteilig mit", "backtest.py",
     "                rk_units *= (units - sell) / units",
     "                pass"),
    ("Short-Rueckteil wird nicht gefuehrt", "backtest.py",
     "                rk_s_units += new_units",
     "                pass"),
    ("Gegengeschaeft kennt den Stop des Teils nicht", "backtest.py",
     '              "RUECKKAUF_STOP", "SHORT_RUECKTEST_STOP"}',
     "              }"),
    # --- Telegram ----------------------------------------------------------------------
    ("Ausbruchs-Meldung nennt das Fenster falsch", "telegram_notify.py",
     '        zeilen += _umbruch(f"Kommt der Kurs in den naechsten {n} Kerzen ({_dauer(n)}) bis "',
     '        zeilen += _umbruch(f"Kommt der Kurs in den naechsten {n} Kerzen ({_dauer(n + 1)}) bis "'),
]


def lauf():
    shutil.rmtree(ENG / "__pycache__", ignore_errors=True)
    umg = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run([sys.executable, "run_tests.py"], cwd=ENG, env=umg,
                       capture_output=True, text=True, timeout=600)
    letzte = [z for z in r.stdout.splitlines() if "passed" in z]
    return (letzte[-1] if letzte else "? (Absturz beim Import)"), r.stdout + r.stderr


signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError()))
ungefangen = []
for name, datei, alt, neu in SABOTAGEN:
    pfad = ENG / datei
    orig = pfad.read_text(encoding="utf-8")
    if alt not in orig:
        print(f"!! VORLAGE NICHT GEFUNDEN: {name}", flush=True)
        ungefangen.append(name + " [Vorlage fehlt]")
        continue
    signal.alarm(700)
    try:
        pfad.write_text(orig.replace(alt, neu, 1), encoding="utf-8")
        zeile, voll = lauf()
        rot = [z.split("::")[-1] for z in voll.splitlines() if z.startswith("FAIL")]
        if rot or "passed" not in zeile:
            print(f"OK  {name}\n    -> {zeile}  | {', '.join(rot[:3])}", flush=True)
        else:
            print(f"!!! UNGEFANGEN: {name}\n    -> {zeile}", flush=True)
            ungefangen.append(name)
    finally:
        pfad.write_text(orig, encoding="utf-8")
        signal.alarm(0)

print("\n" + "=" * 60)
zeile, _ = lauf()
print("nach Wiederherstellung:", zeile)
print(f"Sabotagen: {len(SABOTAGEN)}, gefangen: {len(SABOTAGEN) - len(ungefangen)}")
print("ungefangen:", ungefangen or "keine")
