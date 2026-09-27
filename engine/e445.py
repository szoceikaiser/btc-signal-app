"""E44.5: festgelegtes Gitter messen, keine Live-Dateien oder Nachrichten schreiben.

python e445.py: Messung auf GitHub (Secret bleibt dort). --replay DATEI:
dieselbe Messung auf dem gesicherten Eingabestand wiederholen, ohne Netzwerk.
"""
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import sys

import backtest as bt
from strategy_core import Candle, FlowPoint


def regel(live, var, haupt=False):
    """Plan Abschnitt 8, negative DD-Werte; Monatsprobe wie E44.2."""
    grenze = 1.0 if haupt else 2.0
    h1 = round(var["h1"] - live["h1"], 2)
    h2 = round(var["h2"] - live["h2"], 2)
    dd = round(var["dd"] - live["dd"], 2)
    lm, vm = live["monate"], var["monate"]
    vollstaendig = (len(lm) >= 2 and len(lm) == len(vm)
                    and len({m["monat"] for m in lm}) == len(lm)
                    and len({m["monat"] for m in vm}) == len(vm)
                    and {m["monat"] for m in lm} == {m["monat"] for m in vm})
    mp = bt.monats_probe(lm, vm)
    bestanden = h1 >= grenze and h2 >= grenze and dd >= -1.0 and vollstaendig and mp["haelt"]
    return dict(h1=h1, h2=h2, dd=dd, grenze=grenze, monats_probe=mp,
                vollstaendig=vollstaendig, bestanden=bool(bestanden))


def auswerten(results, halves):
    voll = {r[0]["label"]: r for r in results}
    halb = {h[0]["label"]: h for h in halves}
    labels = [c["label"] for c in bt.E445_GRID]
    if any(l not in voll or l not in halb for l in labels):
        raise ValueError("Kein Urteil: E44.5-Gitter oder Fensterhaelfte unvollstaendig")
    def kz(l):
        return dict(h1=halb[l][1]["rendite_pct"], h2=halb[l][2]["rendite_pct"],
                    dd=voll[l][3]["max_drawdown_pct"], monate=voll[l][3]["monate"])
    basis = next(c["label"] for c in bt.E445_GRID if c["panel"])
    live = kz(basis)
    zeilen = []
    for cfg in bt.E445_GRID:
        label = cfg["label"]
        rolle = ("Basis" if label == basis else "Robustheit" if label == bt.E445_ROBUST
                 else "Hauptzeile" if label == bt.E445_HAUPT else "Erklaerung")
        urteil = None if rolle in ("Basis", "Robustheit") else regel(live, kz(label), rolle == "Hauptzeile")
        rk = [s for s in voll[label][1] if s["type"] in ("RUECKKAUF", "SHORT_RUECKTEST")]
        alter = [s["beobachtung_kerzen"] for s in rk if "beobachtung_kerzen" in s]
        zeilen.append(dict(label=label, rolle=rolle, params={k: cfg[k] for k in bt.EVAL_KEYS},
                           rendite=voll[label][3]["rendite_pct"], **kz(label), urteil=urteil,
                           signale=len(voll[label][1]), rueckkaeufe=len(rk),
                           alter_gemessen=len(alter), alte_marken=sum(a > 12 for a in alter),
                           max_alter=max(alter, default=0),
                           beteiligung=voll[label][3].get("beteiligung")))
    # Alle sechs Flaechen des Wuerfels, mit benannter Basis (auch bei aktivem dritten Hebel).
    ww = []
    for bl, al, cl, abl, ka, kb in bt.e442_vierergruppen(bt.E445_GRID[:8]):
        werte = [voll[l][3]["rendite_pct"] for l in (bl, al, cl, abl)]
        ww.append(dict(basis=bl, a=ka, b=kb, ab=abl,
                       voll=bt.e442_wechselwirkung(*werte),
                       h1=bt.e442_wechselwirkung(*[kz(l)["h1"] for l in (bl, al, cl, abl)]),
                       h2=bt.e442_wechselwirkung(*[kz(l)["h2"] for l in (bl, al, cl, abl)])))
    return dict(zeilen=zeilen, wechselwirkungen=ww)


def bericht(messung):
    z = ["# E44.5 — Kombinationsgitter", "", "**Nur Messung auf dem Arbeitszweig. Keine Aktivierung, kein Merge-Go.**", "",
         "K1 = E42, K2 = Verkauf-Faktor 0.67, K3 = Rest halten. Acht Ecken plus K1 mit 6 statt 12 Kerzen.",
         "Hauptzeile: beide Haelften mindestens +1 Punkt. Erklaerungszeilen: mindestens +2 Punkte.",
         "Dazu hoechstens 1 Punkt tieferer Rueckgang und positiver Vorsprung ohne jeden einzelnen Monat.",
         "Monatsprobe: Summe der Monatsdifferenzen (E44.2, nicht verkettet). Robustheit entscheidet nichts.", "",
         "| Variante | Rolle | Rendite % | H1 % | H2 % | Rueckgang % | Delta H1 | Delta H2 | ohne besten Monat | Regel |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in messung["zeilen"]:
        u = r["urteil"]
        ende = (f"{u['h1']:+.2f} | {u['h2']:+.2f} | {u['monats_probe']['min_ohne_einen']:+.2f} | "
                + ("erfuellt" if u["bestanden"] else "nicht erfuellt")) if u else "— | — | — | keine Entscheidung"
        z.append(f"| {r['label']} | {r['rolle']} | {r['rendite']:+.2f} | {r['h1']:+.2f} | {r['h2']:+.2f} | {r['dd']:.2f} | {ende} |")
    z += ["", "## Wechselwirkungen", "", "(A+B) - A - B + Basis; positiv = zusammen besser als die Summe.", "",
          "| Basis | A | B | Vollfenster | H1 | H2 |", "|---|---|---|---:|---:|---:|"]
    for w in messung["wechselwirkungen"]:
        z.append(f"| {w['basis']} | {w['a']} | {w['b']} | {w['voll']:+.2f} | {w['h1']:+.2f} | {w['h2']:+.2f} |")
    z += ["", "## Alter der beobachteten Marken", "",
          "Alter seit Beginn der Beobachtung beim Verkauf, nicht seit Entstehung des Pivots. Alte Marke hier: mehr als 12 Vierstundenkerzen (2 Tage). Nur Diagnose, kein neuer Filter.", "",
          "| Variante | Rueckkaeufe | Alter erfasst | davon alte Marken | Maximum Kerzen |", "|---|---:|---:|---:|---:|"]
    for r in messung["zeilen"]:
        if r["params"]["ausbruch_ruecktest"]:
            z.append(f"| {r['label']} | {r['rueckkaeufe']} | {r['alter_gemessen']} | {r['alte_marken']} | {r['max_alter']} |")
    z += ["", "Bei bestandener Erklaerungszeile bleibt die inhaltliche Einordnung erforderlich; keine automatische Auswahl des Gitter-Siegers.",
          "Ausschalt-Regel bei spaeterem Go: alte Zeile in beiden Haelften mindestens +1 Punkt besser ODER neuer Rueckgang mehr als 1 Punkt tiefer. Alte Zeile bleibt Gegenprobe.",
          "Datenbegrenzung: ein Markt, historisches Fenster; keine Aussage ueber kuenftige Rendite."]
    return "\n".join(z) + "\n"


def messen(candles, flow, start, ende):
    results, halves = [], []
    mitte = start + (ende - start) // 2
    for cfg in bt.E445_GRID:
        sig = bt.run_backtest(candles, flow, cfg, start_ms=start, diagnose_e445=True)
        p = bt.simulate(sig, candles, start_ms=start)
        _, p1 = bt.run_half(candles, flow, cfg, start, end_ms=mitte)
        _, p2 = bt.run_half(candles, flow, cfg, mitte)
        if p1 is None or p2 is None:
            raise ValueError("Leere Fensterhaelfte")
        results.append((cfg, sig, {}, p))
        halves.append((cfg, p1, p2))
        print(f"{cfg['label']}: {p['rendite_pct']:+.2f} %, H1 {p1['rendite_pct']:+.2f}, H2 {p2['rendite_pct']:+.2f}", flush=True)
    return auswerten(results, halves), results


def main():
    ziel = bt.ROOT / "docs/e445"
    ziel.mkdir(exist_ok=True)
    if len(sys.argv) == 3 and sys.argv[1] == "--replay":
        daten = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        cs = [Candle(**x) for x in daten["candles"]]
        fl = [FlowPoint(**x) for x in daten["flow"]]
    else:
        key = os.environ["COINALYZE_API_KEY"]
        raw = bt.fetch_candles_range(bt.WARMUP_MS, bt.END_MS)
        funding = bt.fetch_funding_8h()
        zeit = dict(frm=bt.WARMUP_MS // 1000, to=bt.END_MS // 1000)
        oi = bt.coinalyze.oi_by_ts(key, **zeit)
        liq = bt.coinalyze.liquidations_by_ts(key, **zeit)
        fut = bt.coinalyze.fut_delta_by_ts(key, **zeit)
        ls = bt.coinalyze.long_short_by_ts(key, **zeit)
        oi, liq, fut, ls, info = bt.archiv_mischen(oi, liq, fut, ls, bt.archiv.laden())
        if not all((raw, funding, oi, liq, fut, ls)):
            raise ValueError("Unvollstaendige Daten: keine Ersatzmessung mit neutralen Reihen")
        cs, fl = bt.build_series(raw, funding, oi, liq, fut, ls)
        daten = dict(start=max(bt.START_MS, min(oi)), ende=bt.END_MS,
                     erzeugt=datetime.now(timezone.utc).isoformat(), archiv=info,
                     punkte=dict(kerzen=len(raw), funding=len(funding), oi=len(oi), liq=len(liq), fut=len(fut), ls=len(ls)),
                     candles=[asdict(c) for c in cs], flow=[asdict(f) for f in fl])
    (ziel / "eingaben.json").write_text(json.dumps(daten), encoding="utf-8")
    messung, results = messen(cs, fl, daten["start"], daten["ende"])
    messung["daten"] = {k: v for k, v in daten.items() if k not in ("candles", "flow")}
    (ziel / "ergebnis.json").write_text(json.dumps(messung, ensure_ascii=False, indent=2), encoding="utf-8")
    (ziel / "signale.json").write_text(json.dumps({r[0]["label"]: r[1] for r in results}, ensure_ascii=False), encoding="utf-8")
    (ziel / "BERICHT.md").write_text(bericht(messung), encoding="utf-8")


if __name__ == "__main__":
    main()
