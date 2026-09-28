"""Readable complete E42 episode/lot journal and a static portfolio figure."""
import json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'

def stamp(ms):
    return datetime.fromtimestamp(ms/1000,timezone.utc).strftime('%d.%m. %H:%M') if ms is not None else '—'
def n(x):return f'{x:,.2f}'.replace(',',' ').replace('.',',')

def main():
    d=json.loads((OUT/'e42-faelle.json').read_text(encoding='utf-8'))
    p=d['portfolio'];counts=d['counts']
    names={'gescheitert':'Schluss unter Marke','gekauft':'Rückkauf','ohne_kauf':'gehalten, kein Kauf',
           'ersetzt':'durch neue Beobachtung ersetzt','verfallen':'Frist abgelaufen',
           'ausbruch':'Ausbruch','ruecktest':'Rücktest gehalten'}
    lines=['# E42: vollständige Fallanalyse','',
        '**Ergebnis:** Ein gehaltener Rücktest ist eine vergangene Preisbedingung, keine Zusage für den nächsten Kurs. Im gespeicherten Lauf ergeben 16 tatsächliche Rückkauf-Signale sechs positive und zehn negative Rückkauf-Lose. Zusammen verdienen diese Lose nach den modellierten Gebühren 13,45 USD. Trotzdem endet das Gesamtportfolio 71,53 USD unter der Vergleichsstrategie ohne E42.',
        '', '## Basis, Zeit und Zählung','',
        'Original-E44.5-Eingaben und Signale, Code 68e15ae (Engine identisch mit e2b0051). Die Originalsignale wurden mit instrumentierter Zustandsmaschine exakt rekonstruiert. Die nachstehende Losrechnung korrigiert ausschließlich F09 (winzige verbleibende BTC-Reste) durch unabhängige Buchführung. Sie enthält zunächst auch die ursprüngliche unvollständige Schlusskerze, um den gespeicherten Lauf zu erklären. Die getrennte gemeinsame Messung in [KOMBINATIONEN.md](KOMBINATIONEN.md) entfernt diese Kerze.',
        '', 'Alle Tabellenzeiten sind **UTC 2026, Beginn der 4h-Kerze**. Das Schluss-Signal ist frühestens vier Stunden später bekannt, zuzüglich Abruf- und Versandverzögerung. Ein historischer Tabellenpreis ist keine belegte Broker-Ausführung. Gebühren 0,1 % je Kauf/Verkauf, kein Spread/Funding im ursprünglichen Modell. Teilverkäufe werden proportional auf alle offenen Kauf-Lose verteilt; ein Rückkauf-Stop verkauft nur Rückkauf-Lose. Sämtliche Rückkäufe dieses Laufs sind vor dessen Ende geschlossen.',
        '', f'**{counts["observations"]} Beobachtungen → {counts["breakouts"]} Ausbruchsereignisse → {counts["buys"]} Rückkäufe.** Beobachtung = Startzeit plus Marke. Ausbruchsereignis = neuer Schluss jenseits der Marke, während noch kein Ausbruch aktiv ist; nach Scheitern kann ein neuer Ausbruch derselben Beobachtung beginnen. Wiederholte Kerzen eines laufenden Ausbruchs werden nicht neu gezählt. Es gab 18 Ausbruchsereignisse mit mindestens einem gehaltenen Rücktest und 19 entsprechende Kerzen. Zwei gehaltene Ereignisse führten nicht zum Kauf: B004 blieb wegen vollem Planbestand gesperrt; bei B016 verhinderte ein Teilverkauf derselben Kerze den Kauf durch no_flip, danach brach die Marke. Die Endzustände sind gegenseitig ausschließend:',
        '', '| Endzustand | Anzahl |','|---|---:|']
    for k,v in counts['terminal'].items():lines.append(f'| {names.get(k,k)} | {v} |')
    lines += ['', '18/33 wäre **keine belastbare Erfolgsquote**: gehalten beschreibt nur die Rücktest-Kerze; Ersetzen und Fristablauf sind andere Endzustände. Die 57 Beobachtungen, 33 Ausbrüche und 19 Rücktest-Kerzen dürfen nicht zusammen in einen gemeinsamen Nenner wandern. Auch 6/16 profitable Lose sind bei abhängigen Marktereignissen kein belastbarer Schätzer künftiger Trefferwahrscheinlichkeit.',
        '', '## Rückkauf-Lose: vollständig','',
        '| Ereignis | Kaufkerze UTC | Marke USD | Modellpreis USD | eingesetzte USD | gekaufte BTC | Gebühren USD | Nettoergebnis USD | Ergebnis auf Einsatz % |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for l in d['lots']:
        lines.append(f'| {l["episode"]} | {stamp(l["ts"])} | {n(l["mark"])} | {n(l["price"])} | {n(l["spent"])} | {l["units"]:.8f} | {n(l["fees"])} | {n(l["pnl"])} | {n(l["return_pct"])} |')
    lines+=['', 'Alle Käufe tragen eine angeforderte Tranche von 25 %; die absoluten Einsätze unterscheiden sich durch Wiederanlage, vorhandenes Cash und den ursprünglichen Zyklus-Bezugsbetrag. 25 % ist deshalb weder immer ein Viertel des momentanen Portfoliowerts noch ein Viertel des freien Cash. Kosten sind im Nettoergebnis bereits enthalten.',
            '', '### Sämtliche Teilverkäufe und Stops je Rückkauf','',
            '| Los | Verkaufkerze UTC | Verkaufstyp | BTC dieses Loses | Preis USD | Erlös nach Gebühr USD | anteiliger Kaufaufwand USD | Nettoanteil USD |',
            '|---|---|---|---:|---:|---:|---:|---:|']
    for l in d['lots']:
        for e in l['exits']:
            lines.append(f'| {l["episode"]} | {stamp(e["ts"])} | {e["type"]} | {e["units"]:.8f} | {n(e["price"])} | {n(e["received"])} | {n(e["cost"])} | {n(e["pnl"])} |')
    lines+=['','## Warum gehalten später Verlust machen kann','']
    l=next(l for l in d['lots'] if l['episode']=='B031')
    ep=next(e for e in d['episodes'] if e['id']==l['episode'])
    e=l['exits'][-1]
    lines.append(f'**B031, 27. August:** Nach dem Ausbruch vom {stamp(ep["breakout"])} hält die Rücktest-Kerze {stamp(l["ts"])} die Marke {n(l["mark"])} USD. Gekauft wird zum Schluss {n(l["price"])} USD für {n(l["spent"])} USD. Später verkauft {e["type"]} am {stamp(e["ts"])} zu {n(e["price"])} USD. Ergebnis {n(l["pnl"])} USD nach {n(l["fees"])} USD Gebühren. Der Rücktest war zum damaligen Schluss regelkonform; der spätere Kursverlauf erfüllt diese Bedingung nicht erneut. Das ist kein Widerspruch.')
    l=next(l for l in d['lots'] if l['episode']=='B003')
    lines+=['',f'**B003, 13. Februar:** Der Rückkauf kostet {n(l["price"])} USD je BTC. Der spätere Verkauf „TEILVERKAUF_LADDER“ zu {n(l["exits"][0]["price"])} USD liegt für dieses neue Los bereits unter seinem Kaufpreis. Die Bezeichnung Teilgewinn bezieht sich auf die Ziele der Gesamtposition, nicht zwangsläufig auf jeden später hinzugekauften Anteil. Zusammen mit dem Teil-Stop verliert dieses Los {n(l["pnl"])} USD. Eine Zählung aller „Teilgewinne“ als gewonnene Rückkäufe wäre falsch.',
        '', '## Gewinn eines Teils gegenüber dem Gesamtportfolio','',
        '| Buchung | USD bei 10 000 USD Startkapital |','|---|---:|',
        f'| E42 aus: Endwert | {n(p["base_end"])} |',f'| E42 an: Endwert | {n(p["e42_end"])} |',
        f'| Unterschied E42 minus aus | {n(p["difference"])} |',f'| Direkte Nettoergebnisse aller Rückkauf-Lose | {n(p["direct_rk_pnl"])} |',
        f'| Unterschied der übrigen Lose | {n(p["other_lots_difference"])} |',
        f'| Gesamte Gebühren E42 aus / an | {n(p["baseline_fees"])} / {n(p["e42_fees"])} |',
        '', 'Der zweite Effekt entsteht durch das veränderte verfügbare Cash, den Bestand und nachfolgende Signal-/Verkaufsfolgen. Die Zahl −84,98 USD ist eine exakte buchhalterische Zerlegung des Ergebnisunterschieds. Sie ist **keine getrennt identifizierte kausale Schätzung**, wie viel allein Cash-Bindung, ein bestimmter Kauf oder ein geänderter Stop verursacht. Gebühren nicht nochmals abziehen: Sie stecken bereits in den Losergebnissen.',
        '', 'Ein konkreter Gewinnfall ist **B027, 20. August**: dieses Los verdient 126,65 USD über fünf Verkäufe. Daraus folgt nicht, dass das gesamte E42-Paket den Pfad ohne E42 schlägt. Bei gleichem Kapital konkurrieren die zusätzlich gebundenen Mittel mit späteren Einstiegen; die Gesamtstrategie wird deshalb mit ihrem vollständigen alternativen Pfad verglichen. Ein sauberer Einzelfall-Nachweis „gerade B027 verursachte den späteren Minderertrag“ ist durch diese Zerlegung allein nicht gegeben und wird hier nicht behauptet.',
        '', '![Portfoliopfad mit und ohne E42](e42-portfoliopfad.png)',
        '', '## Alle 33 eindeutigen Ausbruchsereignisse','',
        '| ID / Beobachtung | Marke USD | Ausbruch UTC | erster gehaltener Rücktest UTC | Rücktest-Kerzen | Ende UTC | endgültiger Status |',
        '|---|---:|---|---|---:|---|---|']
    for e in d['episodes']:
        why=('; '+str(e['block_reason'])) if e.get('block_reason') else ''
        lines.append(f'| {e["id"]} / {e["observation"]} | {n(e["mark"])} | {stamp(e["breakout"])} | {stamp(e["first_retest"])} | {len(e["retest_bars"])} | {stamp(e["end"])} | {names.get(e["terminal"],e["terminal"])}{why} |')
    lines+=['', '## Alle 57 Beobachtungen, einschließlich solcher ohne Ausbruch','',
            '| ID | Beginn UTC | Marke USD | Ereignisse in Zeitfolge | Ende UTC | Ende der Beobachtung |',
            '|---|---|---:|---|---|---|']
    for o in d['observations']:
        events='; '.join(f'{names.get(e["type"],e["type"])} {stamp(e["ts"])}' for e in o['events']) or 'kein Ausbruch/Rücktest'
        lines.append(f'| {o["id"]} | {stamp(o["start"])} | {n(o["mark"])} | {events} | {stamp(o.get("end"))} | {o["end_reason"]} |')
    lines+=['', '## Unsicherheit und Reproduktion','',
        'Auf der bereinigten gemeinsamen Datenbasis liegt E42 allein bei +35,42 % gegenüber +36,13 %. Paarweise Block-Neuziehung der 4h-Portfoliorenditen (2 000 Ziehungen, feste Startzahl 270926) ergibt für den Renditeunterschied ein 95-%-Perzentilband von ungefähr −6,08 bis +6,15 Prozentpunkten bei 7-Tage-Blöcken und −5,53 bis +5,88 bei 28-Tage-Blöcken. Diese bedingten Sensitivitätsbänder sind wegen derselben oft verwendeten Historie, weniger langer Zeitblöcke und nicht neu berechneter Signalsuche keine Zukunfts-Garantie und kein exakter Signifikanztest.',
        '', 'Die Schlussfolgerung lautet: **kein belastbarer Nachweis eines Mehrertrags durch E42; zugleich kein belastbarer Beweis, dass gehaltene Rücktests grundsätzlich nutzlos wären.** Das vorab getestete Zusammenspiel mit ausgeschaltetem Verkauf am alten Hoch verdient eine neue, unabhängige Prüfung erst nach Fehlerkorrektur. Es besteht die Audit-Kombinationsregel hier nicht.',
        '', 'Nachstellen: `python audit/e42_cases.py`, danach `python audit/e42_report.py`. Maschinenlesbare vollständige Zustandsübergänge, Nachrichtengründe und beide Portfoliopfade stehen in [e42-faelle.json](e42-faelle.json). Präfix der Originalsignale bleibt unverändert; `audit_episode` ist nur eine Audit-Zuordnung. Kosten-/Zeitvarianten und Zeitabschnitte: [KOMBINATIONEN.md](KOMBINATIONEN.md), [unsicherheit.json](unsicherheit.json).']
    (OUT/'E42.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    from reportlab.graphics.shapes import Drawing,String,Rect
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics import renderPDF,renderSVG
    from reportlab.lib.colors import HexColor,white
    import pypdfium2
    drawing=Drawing(820,490)
    drawing.add(Rect(0,0,820,490,fillColor=white,strokeColor=None))
    drawing.add(String(65,461,'E42: vollständige alternative Portfoliopfade',fontName='Helvetica-Bold',fontSize=17))
    drawing.add(String(65,440,'Portfoliowert in USD · 10 000 USD Startkapital',fontSize=10))
    paths=d['portfolio_paths']
    xs=[x['ts']/86400000 for x in paths['e42']]
    def chart(data,y,height,lo,hi):
        plot=LinePlot();plot.x=65;plot.y=y;plot.width=715;plot.height=height
        plot.data=data
        plot.xValueAxis.valueMin=min(xs);plot.xValueAxis.valueMax=max(xs)
        plot.xValueAxis.labelTextFormat=lambda x:datetime.fromtimestamp(x*86400,timezone.utc).strftime('%d.%m.')
        plot.yValueAxis.valueMin=lo;plot.yValueAxis.valueMax=hi
        plot.xValueAxis.labels.fontSize=9;plot.yValueAxis.labels.fontSize=9
        plot.lines.strokeWidth=.9
        drawing.add(plot)
        return plot
    a=[x['equity'] for x in paths['baseline']];b=[x['equity'] for x in paths['e42']]
    top=chart([list(zip(xs,a)),list(zip(xs,b))],228,188,9000,14500)
    top.lines[0].strokeColor=HexColor('#253e72');top.lines[1].strokeColor=HexColor('#da7026')
    drawing.add(String(620,440,'E42 aus',fillColor=HexColor('#253e72'),fontSize=11))
    drawing.add(String(712,440,'E42 an',fillColor=HexColor('#da7026'),fontSize=11))
    delta=[v-u for u,v in zip(a,b)]
    bottom=chart([list(zip(xs,delta)),[(min(xs),0),(max(xs),0)]],66,108,-400,400)
    bottom.lines[0].strokeColor=HexColor('#654b8e');bottom.lines[1].strokeColor=HexColor('#777777')
    bottom.lines[1].strokeWidth=.45
    drawing.add(String(65,190,'Unterschied E42 minus aus in USD',fontSize=10))
    drawing.add(String(65,18,'2026 · historische Level-Ausführung · 0,1 % Gebühr · F09 korrigiert',fontSize=10))
    renderSVG.drawToFile(drawing,str(OUT/'e42-portfoliopfad.svg'))
    # Standard chart renderer + PDFium rasterization, no manually painted chart.
    pdf=pypdfium2.PdfDocument(renderPDF.drawToString(drawing))
    pdf[0].render(scale=2).to_pil().save(OUT/'e42-portfoliopfad.png')
    print('E42 report: 57 observations, 33 episodes, 16 lots; complete exits and figure written')

if __name__=='__main__':main()
