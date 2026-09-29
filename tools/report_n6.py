"""Render every fixed result; no selection, tuning or inference recomputation."""
import csv
import gzip
import json
from pathlib import Path
from historical_analysis import ROOT,DOC,dump,utc,near


def cycles(result):
    out=[];current=None
    for e in result['ledger']:
        if e['status']!='filled':continue
        if current is None and e['before']['btc']==0 and e['after']['btc']>0:
            current=dict(start=e['fill_at'],capital=e['before']['cash'],fees=0.,fills=0)
        if current:
            current['fees']+=e['fee'];current['fills']+=1
            if e['after']['btc']==0:
                current.update(end=e['fill_at'],closed=True,pnl=e['after']['cash']-current['capital'])
                out.append(current);current=None
    if current:
        current.update(end=result['equity'][-1]['at'],closed=False,pnl=result['ende']-current['capital'])
        out.append(current)
    near(sum(c['pnl'] for c in out),result['ende']-10000.)
    return out


def main():
    report=['# Historische Auswertung nach Etappe 6','',
        'Basis `05208cecce8d5a0e856a1ea56984b209f403ccd6`. Nur das festgelegte Paar Basis/E42-12; keine Optimierung. Live unverändert.','',
        'R0 endet am 27.09.2026 um 08:29:08.840 UTC (letzter Close 08:00). R1 endet fest am 29.09.2026 um 12:00 UTC. ',
        'R1 ergänzt 13 abgeschlossene Kerzen; die 2.480 abgeschlossenen R0-Kerzen einschließlich Warmup sind feldgenau gleich. Die damalige laufende R0-Kerze bleibt im Original erhalten, war dort ausgeschlossen und wird nur in R1 als später abgeschlossene neue Kerze verwendet.','',
        'Daten, Parameter, Statistik und Ausführung wurden vor der Auswertung fixiert (erster Plan Commit `6462e08`, erhalten als `plan-v1.json`). Ein i+2-Frischstart traf einen numerischen Überverkauf um 1,7347e-18 BTC. Planversion 2 dokumentiert die isolierte Rundungskorrektur (höchstens 8 ULP des Spitzenbestands); materielle Überverkäufe bleiben gesperrt. Alle 60 Fälle wurden danach neu gerechnet. Analyse nach Datenkenntnis, keine historische Präregistrierung. ',
        '30 kausale Läufe je Paket: zwei Zeilen × fünf Szenarien × ursprünglicher Start und zwei feste Frischstarts. Alle 60 mit unabhängiger Kandidaten-/Losbuchführung und Decimal-Restkosten geprüft.','',
        '| Fall | Fill | Slippage je Seite | Gebühr je Seite |','|---|---|---:|---:|',
        '| S0 | nächstes Open | 0 % | 0,1 % |','| S1 (Hauptfall) | nächstes Open | 0,1 % | 0,1 % |',
        '| S2 | nächstes Open | 0,5 % | 0,1 % |','| S3 | Open i+2 | 0,1 % | 0,1 % |','| S4 | Open i+2 | 0,5 % | 0,1 % |','']
    allcycles=[];period_csv=[]
    brief=[]
    for package in ['R0','R1']:
        data=json.loads((DOC/package/'results.json').read_text(encoding='utf-8'))
        full=[x for x in data['results'] if x['start_index']==0]
        main=next(x for x in full if x['scenario']=='S1')
        brief.append(dict(package=package,**main['comparison'],basis=main['rows'][0]['ende'],candidate=main['rows'][1]['ende'],U1=main['U1'][0]))
        report += [f'## {package}: vollständiger Pfad','',
            '| Fall | Basis USD | E42 USD | E42 − Basis USD | relativer Vorteil % | historische Dominanz |',
            '|---|---:|---:|---:|---:|---|']
        for x in full:
            b,k=x['rows'];c=x['comparison']
            report.append(f"| {x['scenario']} | {b['ende']:.2f} | {k['ende']:.2f} | {c['delta_usd']:+.2f} | {100*c['A_window']:+.4f} | {c['dominance']} |")
        report+=['','Dominanz gilt ausschließlich für Endwert, Schluss-DD und obere Intrabar-Grenze in diesem historischen Modell. Toleranzen: 0,01 USD / 1e-8 Prozentpunkte.','',
            '| Fall / Zeile | Gebühren USD | Cash USD | BTC | Restkosten USD | Exposition Ende % | Mittel % | DD Schluss % | DD untere % | DD obere % | Fills |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for x in full:
            for name,r in zip(['Basis','E42'],x['rows']):
                report.append(f"| {x['scenario']} {name} | {r['fees']:.2f} | {r['cash']:.2f} | {r['btc']:.8f} | {r['cost_basis']:.2f} | {r['final_exposure_pct']:.2f} | {r['verification']['avg_exposure_pct']:.2f} | {r['dd_close_pct']:.4f} | {r['dd_intrabar_lower_pct']:.4f} | {r['dd_intrabar_upper_pct']:.4f} | {r['verification']['fills']} |")
        report+=['','Startwert 10.000 USD, keine Schlussliquidation. Exposition: BTC-Marktwert / Vermögen; Mittel über 4h-Closes. Risikopeaks der Hauptausgabe laufen durchgehend weiter. Intrabar sind Grenzen, keine gemessenen Preisreihenfolgen.','',f'### {package}: bedingte Unsicherheit','',
            '| Fall | Block Tage | n | A_days % | Basic 95-%-Intervall % | einseitige 95-%-Untergrenze % | p_cond |',
            '|---|---:|---:|---:|---|---:|---:|']
        for x in full:
            for u in x['U1']:
                lo,hi=u['advantage_interval']
                report.append(f"| {x['scenario']} | {u['block_days']} | {u['n']} | {100*u['A_days']:+.4f} | [{100*lo:+.4f}, {100*hi:+.4f}] | {100*u['lower_advantage']:+.4f} | {u['p_cond']:.6f} |")
        span=main['daily_span']
        report += ['',f"UTC-Tagesbereich: {utc(span['start_ms'])} bis {utc(span['end_ms'])}; {span['n']} volle Tage. Ausgeschlossen: {span['excluded_first_hours']:g} Stunden am Anfang, {span['excluded_last_hours']:g} am Ende. Diese Randintervalle bleiben vollständig im Portfoliobericht. Tagesgrenzen sind Close vor neuem Open-Fill.",'',
            'Stationärer gepaarter Bootstrap: 20.000 Replikate, PCG64/20260929, NumPy 2.3.5, lineare Quantile. 14 Tage Hauptfall; 7/28 vollständig sensitiv. Alle Szenarien verwenden bei gleicher Tageszahl dieselben Zufallsindizes. ',
            'Intervalle und p-Werte sind nur bedingt auf das feste Paar. Frühere Auswahl nicht bereinigt; Power unbekannt. Schwache Abhängigkeit/Stationarität sind Annahmen, durch Regimewechsel und lange Haltephasen begrenzt. Renditeresampling erzeugt keine neuen OHLC-/Strategiepfade und keine DD-Verteilung.','',
            f'### {package}: alle Monate und Drittel, fortlaufendes Portfolio','',
            'Beiträge sind USD-Veränderungen im fortlaufenden Konto. Abschnitts-DD beginnt hier ausdrücklich am Abschnittsanfang und ist nur Zusatzdiagnostik; die Haupt-DD oben bleibt unverändert. Vollständige Gebühren/Bestände/Exposition und alle drei Abschnitts-DD je Zeile in `periods.csv` und `results.json`.','',
            '| Fall | Abschnitt UTC | Basis Beitrag USD | E42 Beitrag USD | Differenz USD | Basis Rendite % | E42 Rendite % | Basis Abschnitts-DD % | E42 Abschnitts-DD % |',
            '|---|---|---:|---:|---:|---:|---:|---:|---:|']
        for x in full:
            b,k=x['rows']
            for pb,pk in zip(b['periods'],k['periods']):
                label=pb['label']+(' (Teilmonat)' if pb['partial_month'] else '') if pb['kind']=='month' else 'Drittel '+pb['label']
                report.append(f"| {x['scenario']} | {label} | {pb['usd_contribution']:+.2f} | {pk['usd_contribution']:+.2f} | {pk['usd_contribution']-pb['usd_contribution']:+.2f} | {pb['return_pct']:+.3f} | {pk['return_pct']:+.3f} | {pb['section_dd_pct'][0]:.3f} | {pk['section_dd_pct'][0]:.3f} |")
        report+=['',f'### {package}: Frischstarts an beiden Drittelgrenzen','',
            'Jeweils bis zum Paketende, vorheriger Marktdatenpräfix als Warmup, 10.000 USD, null BTC, keine geerbten Absichten/Peaks. Bekannte Daten, keine unabhängigen Bestätigungsfenster.','',
            '| Start UTC | Fall | Basis USD | E42 USD | Differenz USD | Dominanz | Basis DD Schluss / obere % | E42 DD Schluss / obere % |',
            '|---|---|---:|---:|---:|---|---|---|']
        for x in data['results']:
            for name,r in zip(['Basis','E42'],x['rows']):
                for p in r['periods']:
                    row=dict(package=package,start_index=x['start_index'],scenario=x['scenario'],row=name,**p)
                    row['start_utc']=utc(row['start_ms']);row['end_utc']=utc(row['end_ms'])
                    row['dd_close_section'],row['dd_lower_section'],row['dd_upper_section']=row.pop('section_dd_pct')
                    period_csv.append(row)
            if x['start_index']==0:continue
            b,k=x['rows'];c=x['comparison']
            report.append(f"| {utc(b['start_ms'])} | {x['scenario']} | {b['ende']:.2f} | {k['ende']:.2f} | {c['delta_usd']:+.2f} | {c['dominance']} | {b['dd_close_pct']:.3f} / {b['dd_intrabar_upper_pct']:.3f} | {k['dd_close_pct']:.3f} / {k['dd_intrabar_upper_pct']:.3f} |")
        report+=['','Vollständige Cash/BTC/Restkosten/Gebühren/Exposition, Monats-/Drittelstände und größte Risikoepisoden auch für jeden Frischstart: Paket-`results.json` und `periods.csv`.','']
        ledgers=json.loads(gzip.decompress((DOC/package/'ledgers.json.gz').read_bytes()))
        for row in ledgers:
            allcycles.append(dict(package=package,start_index=row['start_index'],scenario=row['scenario'],row=row['row'],cycles=cycles(row['result'])))
        report += [f'### {package}: Zeitstabilität und Konzentration','']
        for x in full:
            diffs=[pk['usd_contribution']-pb['usd_contribution'] for pb,pk in zip(x['rows'][0]['periods'],x['rows'][1]['periods']) if pb['kind']=='month']
            report.append(f"- {x['scenario']}: {sum(d>0 for d in diffs)} positive, {sum(d<0 for d in diffs)} negative, {sum(d==0 for d in diffs)} unveränderte Monatsbeiträge; größte Monatsdifferenz {min(diffs):+.2f} bis {max(diffs):+.2f} USD.")
        report+=['','Alle Positionszyklen mit Gewinn/Verlust, Gebühren, Zeitraum und Schlussstatus stehen in `cycles.json`; unterschiedliche Zyklen sind nicht automatisch paarbar.','']
    dump(DOC/'cycles.json',allcycles)
    dump(DOC/'summary.json',brief)
    with open(DOC/'periods.csv','w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(period_csv[0]));writer.writeheader();writer.writerows(period_csv)
    report += ['## Belege, Datenqualität und Grenzen','',
        'Rohdaten/Verfügbarkeit: `data-manifest.json` hält die erste Archivprüfung fest (damals R1 unvollständig). Nach ausdrücklicher Freigabe von GitHub-Läufen wurde der getrennte Einmallauf mit dem vorhandenen Coinalyze-Secret ausgeführt; `r1-manifest.json` ist der ergänzte maßgebliche Paketbeleg. ',
        '[GitHub-Datenlauf 36592684701](https://github.com/szoceikaiser/btc-signal-app/actions/runs/36592684701) enthält ausschließlich historische Marktdaten-GETs; alle Rohantworten und Hashes sind gesichert. Der abweichende Workflowname löst Pages nicht aus, Tokenrechte nur lesend, keine Telegram-Zugangsdaten.','',
        'OHLC/Spot-CVD: Binance Vision BTCUSDT; Futures-CVD/OI/Liquidationen/Long-Anteil: Coinalyze BTCUSDT_PERP.A (Binance, kein Börsenaggregat); Funding: Kraken PF_XBTUSD, stündlicher relativer Satz ×8 gemäß unverändertem Altmodell. Funding ist Eingabe der Strategie, kein Spot-Funding-Cashflow. Rohwerte nach Stichtag werden nicht als frühere Werte verwendet. ',
        'R0-Warmup bleibt exakt, einschließlich vorhandener Defaults/fortgeschriebener Werte vor dem Handelsstart. Keine neue Interpolation. Der Überlappungscheck bestätigt die letzte abgeschlossene R0-Kerze; er beweist nicht Revisionsfreiheit der gesamten älteren Historie.','',
        'Erste hier belegbare R1-Version stammt vom späteren GET im GitHub-Lauf; rechtzeitige damalige Veröffentlichung bleibt unbekannt. R0 fehlt die vollständige ursprüngliche API-Rohantwort/Vintage-Kette. Das erlaubt einen bedingten historischen Modellvergleich, keinen Beleg erreichbarer Live-Fills; auch i+2 beweist keine ausreichende reale Liefer-/Menschen-/Brokerlatenz.','',
        '`search-inventory.json`: E43-Kontrollauswahl, E44-Kombinationen, Audit und Korrekturen lesend inventarisiert; versionierte Konfigurationen mit Code-/Datenhash dedupliziert. Frühere Gesamtfamilie unvollständig. **U2/Auswahlbereinigung nicht belegt.** Kein Reality-Check/SPA berechnet, keine zusätzlichen Suchalternativen neu gemessen und keine Mischung alter Signalbänder mit V1-Renditen.','',
        'Statistikgrundlage: [Politis & Romano, The Stationary Bootstrap](https://doi.org/10.1080/01621459.1994.10476870). Die schwache Stationaritäts-/Abhängigkeitsannahme ist hier keine bewiesene Eigenschaft. Keine persönliche Nutzenhürde oder absolute Risikotoleranz angenommen.','',
        '741 reguläre Tests (728 alte unverändert +13 neu), sechs synthetische Statistik-Testgruppen und 15 neue gezielte Schutzproben. Erhalten: F17 16, F13 16, Etappe 4 23, 3b 19, D01 6, F09 3. Protokolle in `checks/`. Unabhängige Rechnung übernimmt ausgewählte Kandidaten bzw. ausgeführte Mengen; sie bestätigt Buchführung, nicht Strategieauswahl oder historische Verfügbarkeit.','',
        'Live-Engine, Konfiguration, site, Versandliste, alte Ausführungs-/Positions-/Checkpointformate und Verträge unverändert. Nur eigener Zweig; kein main-Merge/Push, keine Orders oder Nachrichten. V1-Fills simuliert, historische Signalbänder Diagnostik, manueller Bestand unbekannt. F13-ID bleibt lokale Identität; uncertain blockiert, kein Reset/erneuter Versand bestätigter oder unklarer Nachrichten, keine Exactly-once-Zusage. Ephemerer Runnerverlust vor Git-Persistenz bleibt offen. V2/Shorts/E41.6 getrennt. **Kein Live-Go.**','',
        'Exakter Remote-HEAD, CI, Bundle/ZIP-Hashes, vollständiger Restore, Test-/Schutzproben und identische unabhängige Neuberechnung stehen nach Abschluss in `audit-backups/nach-6-abschluss-<SHA>/ABSCHLUSS.json`. Weitere Arbeit nur separat.','']
    (DOC/'BERICHT.md').write_text('\n'.join(report),encoding='utf-8')
    print(json.dumps(brief,indent=2))


if __name__=='__main__':main()
