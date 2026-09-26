"""Sabotage-Probe fuer E41 (Stop mit Puffer / Rueckeroberung / Docht, 21.09.2026) -
neu gefasst nach dem Umschalten am selben Tag: Rueckeroberung live, Ausschalt-Regel,
Telegram-Meldungen.

Projektregel: Ein Test, den keine Sabotage rot faerbt, prueft nichts. Jede Zeile hier
ist ein Fehler, den man beim Bauen wirklich machen koennte — und der die Engine still
anders handeln liesse, statt zu krachen.
"""
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ENG = Path(__file__).resolve().parent

SABOTAGEN = [
    # --- Kaisers Regel ---------------------------------------------------------------
    ("Rueckeroberung: Stop kommt nie (Zaehler laeuft nicht)", "strategy_core.py",
     '    pos.stop_wartet += 1\n    pos.stop_wartet_inv = inv',
     '    pos.stop_wartet_inv = inv'),
    ("Rueckeroberung stoppt eine Kerze zu frueh", "strategy_core.py",
     '    if pos.stop_wartet > rueckeroberung:',
     '    if pos.stop_wartet >= rueckeroberung:'),
    ("Zurueckeroberte Marke wird nicht als geprueft gefuehrt", "strategy_core.py",
     '            pos.stop_geprueft = inv              # zurueckerobert -> Marke ist geprueft',
     '            pass'),
    ("Geprueft wird ignoriert (zweite Schonfrist)", "strategy_core.py",
     '    if pos.stop_geprueft == inv:\n        return True, cur.close, ("Kerzenschluss',
     '    if False:\n        return True, cur.close, ("Kerzenschluss'),
    ("Harter Boden faellt weg", "strategy_core.py",
     '    if jenseits(cur.close, DIP_FLOOR_PCT):',
     '    if False:'),
    ("Neue Marke erbt das Warten der alten", "strategy_core.py",
     '    if pos.stop_wartet and pos.stop_wartet_inv != inv:\n        pos.stop_wartet = 0',
     '    if False:\n        pos.stop_wartet = 0'),
    ("Rueckeroberung gilt nur fuer Long", "strategy_core.py",
     '        return preis > inv * (1 + abstand)',
     '        return False'),
    # --- Puffer und Docht --------------------------------------------------------------
    ("Puffer wird ignoriert", "strategy_core.py",
     '    unter = jenseits(cur.close, puffer_pct)',
     '    unter = jenseits(cur.close, 0.0)'),
    ("Docht-Stop zum Schlusskurs (geschoent)", "strategy_core.py",
     '            fill = min(cur.open, inv) if long_side else max(cur.open, inv)',
     '            fill = cur.close'),
    ("Docht-Stop bei Luecke zum Stopkurs statt zum Eroeffnungskurs", "strategy_core.py",
     '            fill = min(cur.open, inv) if long_side else max(cur.open, inv)',
     '            fill = inv'),
    # --- Einbindung in evaluate --------------------------------------------------------
    ("E41 greift auch beim nachgezogenen Stop", "strategy_core.py",
     '        if trail_note in ("", "Invalidierung") and (\n                stop_puffer_pct > 0',
     '        if True and (\n                stop_puffer_pct > 0'),
    ("Waehrend des Wartens wird nachgekauft", "strategy_core.py",
     '        if _e41_sperre:\n            return False\n        return not (no_flip',
     '        if False:\n            return False\n        return not (no_flip'),
    ("In der Kerze der Rueckeroberung wird nachgekauft", "strategy_core.py",
     '            _e41_sperre = _wartete or pos.stop_wartet > 0',
     '            _e41_sperre = pos.stop_wartet > 0'),
    ("Nachkauf nach Rueckeroberung zum teuren Levelpreis", "strategy_core.py",
     '                    if pos.stop_geprueft is not None:\n                        preis_nk = (min(',
     '                    if False:\n                        preis_nk = (min('),
    ("Preiskorrektur gilt auch ohne E41 (Live-Zahlen aendern sich)", "strategy_core.py",
     '                    if pos.stop_geprueft is not None:\n                        preis_nk = (min(',
     '                    if True:\n                        preis_nk = (min('),
    ("Stop-Grund aus E41 geht verloren", "strategy_core.py",
     '            elif stop_grund:\n                reason = stop_grund',
     '            elif False:\n                reason = stop_grund'),
    ("Stop-Preis aus E41 geht verloren", "strategy_core.py",
     '            signals.append(Signal(cur.ts, st, stop_preis, 100, reason))',
     '            signals.append(Signal(cur.ts, st, cur.close, 100, reason))'),
    ("Reset vergisst die Merker", "strategy_core.py",
     '    pos.stop_wartet = 0\n    pos.stop_wartet_inv = None\n    pos.stop_geprueft = None\n',
     ''),
    # --- Live-Engine -------------------------------------------------------------------
    ("Live-Engine speichert das Warten nicht", "main.py",
     '         "stop_wartet": pos.stop_wartet, "stop_wartet_inv": pos.stop_wartet_inv,',
     '         "stop_wartet_inv": pos.stop_wartet_inv,'),
    ("Live-Engine liest das Warten nicht", "main.py",
     '    pos.stop_geprueft = d.get("stop_geprueft")',
     '    pos.stop_geprueft = None'),
    ("Live-Engine reicht die Schalter nicht durch", "main.py",
     '    "stop_puffer_pct": 0.0, "stop_rueckeroberung": 0, "stop_auf_docht": False,',
     '    "stop_puffer_pct": 0.0, "stop_auf_docht": False,'),
    # --- Backtest nach dem Umschalten (21.09.2026) ----------------------------------------
    ("Schalter fehlt in EVAL_KEYS", "backtest.py",
     '             "stop_puffer_pct", "stop_rueckeroberung", "stop_auf_docht",',
     '             "stop_puffer_pct", "stop_auf_docht",'),
    ("Panel bleibt beim alten Stop stehen", "backtest.py",
     '      stop_rueckeroberung=1),\n    # E32.3',
     '      stop_rueckeroberung=0),\n    # E32.3'),
    ("Alter Stop misst in Wahrheit live", "backtest.py",
     'stop_rueckeroberung=0,\n      bein_richtung="bias"),',
     'stop_rueckeroberung=1,\n      bein_richtung="bias"),'),
    ("B3 misst in Wahrheit B1", "backtest.py",
     'stop_rueckeroberung=3,\n      bein_richtung="bias"),',
     'stop_rueckeroberung=1,\n      bein_richtung="bias"),'),
    ("Ohne-Flush-Zeile wandert nicht mit", "backtest.py",
     'no_flip=True, neustart_mit_rest=True,\n      zonen_nachziehen=True, stop_rueckeroberung=1, bein_richtung="bias"),',
     'no_flip=True, neustart_mit_rest=True,\n      zonen_nachziehen=True, bein_richtung="bias"),'),
    ("Eine Ampel-Zeile wandert nicht mit", "backtest.py",
     'stop_rueckeroberung=1,\n      bein_richtung="bias", ampel_filter="klein"),',
     '\n      bein_richtung="bias", ampel_filter="klein"),'),
    ("Eine Trendfilter-Zeile wandert nicht mit", "backtest.py",
     'stop_rueckeroberung=1,\n      trend_filter=True, trend_ema=200),',
     '\n      trend_filter=True, trend_ema=200),'),
    ("Eine Muster-5-Zeile wandert nicht mit", "backtest.py",
     'stop_rueckeroberung=1,\n      bein_richtung="bias", muster5_entry=True),',
     '\n      bein_richtung="bias", muster5_entry=True),'),
    ("Ausschalten: ohne Rauschgrenze", "backtest.py",
     '    klar_besser = (alt["h1"] - live["h1"] >= E41_RAUSCHGRENZE\n'
     '                   and alt["h2"] - live["h2"] >= E41_RAUSCHGRENZE)',
     '    klar_besser = (alt["h1"] - live["h1"] > 0\n'
     '                   and alt["h2"] - live["h2"] > 0)'),
    ("Ausschalten: eine Haelfte reicht", "backtest.py",
     '                   and alt["h2"] - live["h2"] >= E41_RAUSCHGRENZE)',
     '                   or alt["h2"] - live["h2"] >= E41_RAUSCHGRENZE)'),
    ("Ausschalten: Rueckgangsgrenze falsch herum", "backtest.py",
     '    zu_tief = live["dd"] < alt["dd"] - E41_DD_TOLERANZ',
     '    zu_tief = live["dd"] > alt["dd"] - E41_DD_TOLERANZ'),
    ("Ausschalten: Rueckgang zaehlt nicht", "backtest.py",
     '            "ausschalten": klar_besser or zu_tief}',
     '            "ausschalten": klar_besser}'),
    ("Ausschalten: 'greift nicht' wird zum Ausschaltgrund", "backtest.py",
     '            "ausschalten": klar_besser or zu_tief}',
     '            "ausschalten": klar_besser or zu_tief or live["stops"] >= alt["stops"]}'),
    ("Bericht meldet AUSSCHALTEN nie", "backtest.py",
     '    if u["ausschalten"]:\n        z.append("- **AUSSCHALTEN.**',
     '    if False:\n        z.append("- **AUSSCHALTEN.**'),
    ("Ueberstimmung vom 23.09.2026 wird verschwiegen", "backtest.py",
     '        z.append("- " + E41_UEBERSTIMMT)',
     '        pass'),
    ("Ueberstimmung ersetzt die Ausschalt-Meldung", "backtest.py",
     '        z.append("- **AUSSCHALTEN.** In `site/data/config.json` `stop_rueckeroberung` auf 0 "',
     '        z.append("- " + E41_UEBERSTIMMT)\n        z.append("- (frueher) In `site/data/config.json` `stop_rueckeroberung` auf 0 "'),
    ("Bericht verschweigt, dass die Regel nicht greift", "backtest.py",
     '    if not u["greift"]:',
     '    if False:'),
    ("Liste: Wiedereinstieg des alten Stops fehlt", "backtest.py",
     '        if w is not None and (n is None or w["ts"] <= n["ts"]):',
     '        if False:'),
    ("Liste: Wiedereinstieg auch nach dem Live-Ausstieg", "backtest.py",
     '        if w is not None and (n is None or w["ts"] <= n["ts"]):',
     '        if w is not None:'),
    ("Liste: 'gleich gestoppt' fehlt", "backtest.py",
     '        if s["ts"] in lv:\n            z.append(kopf + "live gleich gestoppt")\n            continue',
     '        if False:\n            z.append(kopf + "live gleich gestoppt")\n            continue'),
    ("E41 misst gegen die beste Variante statt gegen live", "backtest.py",
     '        lambda: e41_abschnitt(results, halves, panel_cfg["label"]),',
     '        lambda: e41_abschnitt(results, halves, best_cfg["label"]),'),
    # --- Live-Meldungen (Telegram) --------------------------------------------------------
    ("Live-Engine sendet die Wartemeldung nicht", "main.py",
     '    for m in e41_meldungen:\n        send_text(format_stop_rueckeroberung(m), dry_run=dry_run)',
     '    for m in []:\n        send_text(format_stop_rueckeroberung(m), dry_run=dry_run)'),
    ("Wartemeldung kommt erst nach dem Stop", "main.py",
     '    for m in e41_meldungen:\n        send_text(format_stop_rueckeroberung(m), dry_run=dry_run)\n'
     '    if new_signals:\n        send_signals(new_signals, dry_run=dry_run)\n',
     '    if new_signals:\n        send_signals(new_signals, dry_run=dry_run)\n'
     '    for m in e41_meldungen:\n        send_text(format_stop_rueckeroberung(m), dry_run=dry_run)\n'),
    ("Meldung erkennt das Warten nicht", "main.py",
     '    if pos.stop_wartet > wartete_vorher and pos.stop_wartet_inv:',
     '    if False:'),
    ("Meldung auch in der Stop-Kerze", "main.py",
     '    if any(s.type in (SignalType.STOPLOSS, SignalType.SHORT_STOPLOSS) for s in sigs):\n        return None',
     '    if False:\n        return None'),
    ("Rueckeroberung wird nicht gemeldet", "main.py",
     '        return {"art": "zurueck",',
     '        return None and {"art": "zurueck",'),
    ("Rueckeroberung auch fuer eine andere Marke", "main.py",
     '            and (marke_vorher is None or pos.stop_geprueft == marke_vorher)):',
     '            and True):'),
    ("Meldung zaehlt die Kerzen nicht herunter", "main.py",
     '                "noch": rueckeroberung - pos.stop_wartet + 1,',
     '                "noch": rueckeroberung,'),
    ("Harter Boden auf der falschen Seite", "main.py",
     '                "boden": marke * (1 - DIP_FLOOR_PCT) if lang else marke * (1 + DIP_FLOOR_PCT)}',
     '                "boden": marke * (1 + DIP_FLOOR_PCT) if lang else marke * (1 - DIP_FLOOR_PCT)}'),
    ("Plan verspricht die Schonfrist auch beim nachgezogenen Stop", "main.py",
     '    if n > 0 and grund == "Invalidierung":',
     '    if n > 0:'),
    ("Plan kennt die gepruefte Marke nicht", "main.py",
     '            "geprueft": pos.stop_geprueft == stop,',
     '            "geprueft": False,'),
    ("Nachricht: unter und ueber vertauscht", "telegram_notify.py",
     '    seite, gegen = ("unter", "ueber") if lang else ("ueber", "unter")\n    marke = _fmt_usd(m["marke"])',
     '    seite, gegen = ("ueber", "unter") if lang else ("unter", "ueber")\n    marke = _fmt_usd(m["marke"])'),
    ("Nachricht: harter Boden auch bei einer Kerze", "telegram_notify.py",
     '        if noch > 1:',
     '        if True:'),
    ("Nachricht: Nachkaufsperre wird verschwiegen", "telegram_notify.py",
     '        zeilen += _umbruch("- Bis dahin kein Nachkauf.")',
     '        pass'),
    ("Plan-Nachricht: alte Stop-Zeile trotz Regel", "telegram_notify.py",
     '    elif st.get("rueckeroberung"):',
     '    elif False:'),
    ("Plan-Nachricht: Warten wird nicht angezeigt", "telegram_notify.py",
     '        if st.get("wartet"):',
     '        if False:'),
    ("Plan-Nachricht: gepruefte Marke wird nicht genannt", "telegram_notify.py",
     '    if st.get("rueckeroberung") and st.get("geprueft"):',
     '    if False:'),
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
