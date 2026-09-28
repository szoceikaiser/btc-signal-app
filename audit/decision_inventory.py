"""Complete current parameter registry, old comparison distances and historical evidence index."""
import ast,inspect,json,sys
from pathlib import Path
from inventory import git
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'
sys.path.insert(0,str(ROOT/'engine'))
import main as live
import strategy_core as sc
import backtest as bt

PURPOSE={
'bias_long':('Long-Einstiege erlauben','E8.5'),
'bias_short':('Short-Einstiege erlauben','E8.5/E10; F02'),
'pivot_n':('Bestätigungsweite links/rechts für Hochs und Tiefs','E4'),
'k_atr':('Mindestgröße eines Impulses relativ zur Schwankung','E4'),
'flush_entry':('Einstieg bei Durchstich des GP und bestätigter Kapitulation','E8/E9'),
'tp_ladder':('Zwischenverkäufe vor den Hauptzielen','E8'),
'strict_confirm':('Strengere Kombination von Flow-Bestätigungen','E8.5/E43.6'),
'confluence':('Zusätzliche Tageszonen-Bestätigung','E8.5'),
'conditional_stop':('Bedingtes Halten/Aufstocken unter Invalidierung','E9'),
'buy_ladder':('Mehrere kleinere Käufe innerhalb der Zone','E9.8'),
'release_stale_rest':('Rest bei veralteter Impulsstruktur verkaufen','E9.9/E43.8'),
'trail_stop':('Stop nach Teilverkauf auf Einstand/Pivot nachziehen','E9.10; F03/F04'),
'liq_exit':('An Liquidationsspitze oder historischer Zone teilverkaufen','E9.11/E14'),
'high_exit':('Vor dem nächsten bestätigten Hoch teilverkaufen','E10/E14'),
'liq_entry':('An historischer Liquidationszone aufstocken oder Einstieg filtern','E10/E13'),
'block_unhealthy':('Ungesunden Abverkauf beim Einstieg sperren','E13'),
'muster5_entry':('Muster 5 als zusätzliche Long-Bestätigung','E38'),
'muster5_halten':('Muster 5 beim Halten des Rests berücksichtigen','E38'),
'stop_puffer_pct':('Puffer unter Invalidierung vor Stop','E41'),
'stop_rueckeroberung':('Eine oder drei Kerzen Rückeroberungsfrist','E41'),
'stop_auf_docht':('Stop schon bei Intrabar-Berührung statt Schluss','E41'),
'confirm_t1':('Auch den ersten 0,5-Einstieg bestätigen lassen','E13/E43.6'),
'cooldown_h':('Wartezeit nach Stop','E13/E43.6'),
'min_stop_pct':('Zu nahe anfängliche Stops verhindern','E13'),
'no_flip':('Nach erstem Teilkauf/-verkauf Gegenrichtung derselben Kerze sperren','E18/E25'),
'freeze_targets':('Zielreferenz nach erstem Teilverkauf einfrieren','E18'),
'min_bein_pct':('Zu kleine Referenzimpulse überspringen','E19'),
'bein_wahl':('Jüngstes oder größtes geeignetes Bein wählen','E19'),
'be_im_plus':('Stop auf Einstand, sobald Position zuvor im Plus','E19/E43.8'),
'bein_richtung':('Impuls nur in erlaubter Handelsrichtung wählen','E19/E43.2'),
'widerstand_exit':('Teilverkäufe am GP eines Gegenbeins','E20; F05'),
'rest_halten':('Rest bei Gegenmuster nicht verkaufen','E21/E26/E43.6/E44.5'),
'neustart_mit_rest':('Neuer Einstieg bei noch laufendem Rest','E21/E26'),
'zonen_1d':('Zusätzlicher Einstiegsversuch mit Tagesimpuls','E23/E32.3; F08'),
'zonen_nachziehen':('Offene Kaufzonen bei intakter neuer Struktur aktualisieren','E30'),
'pivot_n_1d':('Eigene Pivotweite für Tageszonen; 0 übernimmt 4h-Wert','E32.3'),
'trend_filter':('Einstieg auf erlaubter Seite der Tages-EMA','E8.5/E33; F08'),
'trend_ema':('Länge der Tages-EMA','E33'),
'ampel_filter':('Einstiegstranche nach Ampel halbieren; Gegenproben','E34'),
'muster_cvd':('Relative Summenstände oder vergleichbare lokale USD-Deltas','E43.3; F06'),
'muster_oi':('OI-Veränderung in USD oder BTC-Kontrakten','E43.4'),
'high_exit_hist':('Pivot-Historie für Verkauf am Hoch begrenzen','E43.5/A5'),
'ausbruch_ruecktest':('E42: nach verkauftem Hoch Ausbruch/Rücktest zurückkaufen','E42/E44.3/E44.5'),
'ruecktest_fenster':('Frist des E42-Rücktests in 4h-Kerzen','E44.3/E44.5'),
'verkauf_faktor':('Alle Teilverkaufstranchen verkleinern','E44.4/E44.5; nur Zweig'),
}

def val(v):return json.dumps(v,ensure_ascii=False)
def main():
    plan=json.loads((OUT/'gitter-plan.json').read_text(encoding='utf-8'))
    cfg=json.loads(git('show',plan['base_main']+':site/data/config.json'))
    hist=json.loads((OUT/'historie.json').read_text(encoding='utf-8'))
    rows=plan['rows'];base=plan['base'];source=(ROOT/'engine/strategy_core.py').read_text(encoding='utf-8').splitlines()
    assert set(PURPOSE)==set(live.EVAL_DEFAULTS)
    registry=[]
    lines=['# Vollständiges Parameter- und Vergleichsverzeichnis','',
        'Die Tabelle enthält alle 45 aktuellen `evaluate`-Parameter. **Code-Default ist nicht Live-Einstellung.** Maßgeblich für die konfigurierte Live-Engine ist `main` 89885adc. Am 28.09. wurde remote bis 97e375b geprüft: seit der eingefrorenen Basis änderten sich nur `state.json` und `signals.json`, nicht der Code oder die Konfiguration. Eine tatsächlich manuell ausgeführte Order folgt daraus nicht.',
        '', 'Implementierung: [strategy_core.evaluate](../../engine/strategy_core.py#L1655), Durchreichung [main.EVAL_DEFAULTS/eval_params](../../engine/main.py#L331), historische Definitionen und Datenstände in [ENTSCHEIDUNGEN.md](ENTSCHEIDUNGEN.md). Die Test-Suite umfasst alle vorhandenen `test_*.py`; spezifische zusätzliche Gegenproben sind im Abschlussbericht genannt. Einzelgegenprobe = nur dieser Parameter gegen die gemeinsame heutige Basis. Abhängige Einstellungen werden zusätzlich gemeinsam mit ihrem Hauptschalter geprüft.',
        '', '| Parameter | Zweck / Herkunft | Code-Default | effektiv live | neue Einzelprobe(n) |',
        '|---|---|---|---|---|']
    for key,default in live.EVAL_DEFAULTS.items():
        singles=[r['id'] for r in rows if set(r['diff'])=={key}]
        purpose,ref=PURPOSE[key]
        actual=val(base[key]) if key!='verkauf_faktor' else 'nicht implementiert auf main; Faktor effektiv 1'
        registry.append(dict(parameter=key,purpose=purpose,origin=ref,default=default,live=actual,
            single_rows=singles,configuration_present=key in cfg,
            source_lines=[i+1 for i,x in enumerate(source) if key in x]))
        lines.append(f'| `{key}` | {purpose}; {ref} | `{val(default)}` | {actual} | {", ".join(singles) or "keine abweichende Einzelzeile"} |')
    lines += ['', '`verkauf_faktor` existiert auf E44.4/E44.5, nicht auf main. Der neutrale Faktor 1 wurde unabhängig gegen den eingefrorenen main-Code geprüft: identische Signale. `muster5_*`, `stop_puffer_pct`, `stop_auf_docht`, `strict_confirm`, `confluence` und `pivot_n_1d` können auch über ihren Code-Default wirksam ausgeschaltet sein, wenn kein eigener Schlüssel in `config.json` steht.',
        '', '## Weitere Schalter und feste Größen','',
        '| Einstellung | tatsächlich / Default | Zweck und Beleg | Auditstatus |','|---|---|---|---|',
        '| `vorschau_telegram` | true / true | Vorschau-Versand, E17; main.run_engine | Format-/Persistenztests; kein realer Versand im Audit |',
        '| `plan_telegram` | true / true | Versand geänderter Positionspläne, E20 | F10/F13: Planstop und Zustellung fehlerhaft |',
        '| `flush_wache` | true / true | Laufende Kerze beobachten, nur Warnung | Nicht mit abgeschlossenem Einstiegssignal verwechseln; kein Renditeschalter |',
        '| Chart `planMarken` | pro Browser, standardmäßig an | E24: localStorage; zeichnet state.plan | Code geprüft; keine echte Benutzer-Browsersitzung geprüft |',
        '| `deploy_pct` | nur Backtest, 1,0; historische Werte 0,6/0,5 | Anteil des verfügbaren Kapitals je Positionsbeginn, E10 | Kein Live-Ausführungsbuch. Ergänzende Kapitalprobe separat dokumentiert; keine Optimierung |',
        '| Mehrbörsen-Spot, Futures-CVD, OI, Funding, Liquidationen | nicht live umgeschaltet | E37-Abruf-/Vergleichswege in coinalyze.py/backtest.py; keine gleichnamigen live EVAL-Schalter | Alte Rohantworten fehlen; F14/F15 und Datenverfügbarkeit begrenzen Schlussfolgerungen |',
        '| Coinalyze versus Kraken-OI | hängt von verfügbarem API-Key/Antwort ab | main.fetch_market_data; mit erfolgreichem Coinalyze-OI dessen Zeitreihe, sonst Kraken-Snapshots | Konfigurationsdatei allein beweist die tatsächliche Datenquelle eines vergangenen Laufs nicht |',
        '| Futures-CVD vorhanden / Ersatzweg | Laufzeitentscheidung bei fehlenden Daten | E16; kein gewöhnlicher Konfigurationsschalter | Haupttranskript verlangt Trennung; heutige CVD-Gegenproben ersetzen keinen ursprünglichen Datenvergleich |',
        '| STH-Kostenbasis | Anzeige; zwei Anbieter, unterschiedlich definiert/verzögert | E40; main.sth_kostenbasis | Kein Einstiegsfilter; historische Veröffentlichung nicht rekonstruiert |',
        '| Makro-KI, MVRV-Z, Regime-Shorts E44.6 | nicht gebaut | E8.5/E29/E44-Plan | Keine nachträglich behauptete Wirksamkeitsmessung; E44.6 hier nicht umgesetzt |',
        '| `be_nach_aufstockung` | auf ausdrücklichen Nutzerwunsch zurückgenommen | E28; nie öffentlich live | Kein bestehender Schalter; kein Anlass zur eigenmächtigen Wiedereinführung |',
        '', 'Feste Strategiegrößen (zusätzlich zu den Schaltern, nicht alle empirisch kalibriert):','',
        '| Konstante | Wert |','|---|---|']
    const_names=('BEIN_PIVOTS','SPOT_FENSTER','OF_FENSTER','OF_FLACH_ANTEIL','AMPEL_TRANCHE','TRANCHEN','MAX_DIP_BUYS','DIP_FLOOR_PCT','DIP_TRANCHE','MAX_BUY_RUNGS','BUY_LADDER_TRANCHE','LADDER_FACTORS','LADDER_TRANCHE','MAX_LIQ_EXITS','LIQ_SPIKE_MULT','LIQ_LOOKBACK','LIQ_ZONE_TOL','LIQ_ZONE_MIN_MULT','MAX_WIDERSTAND_EXITS','MAX_HIGH_EXITS','HIGH_EXIT_TOL','HIGH_EXIT_LIVE_KERZEN','MAX_LIQ_ENTRIES','LIQ_ENTRY_TRANCHE','RUECKTEST_FENSTER','RUECKTEST_TOL','RUECKKAUF_TRANCHE')
    for key in const_names:lines.append(f'| `{key}` | `{val(getattr(sc,key))}` |')
    lines+=['', 'Weitere fest kodierte Mustergrenzen stehen in `classify_pattern` (u. a. starke Preisbewegung 4 %, halbe Schwelle 2 %, OI +3/−5 % sowie −2/−1 % in weiteren Mustern, Funding 0,0001), ATR als einfacher 14-Kerzen-Mittelwert, grundlegende Impuls-Untergrenze 3 % alternativ zum ATR-Kriterium. Diese Zahlen sind keine vollständig aus dem Transkript belegten Regeln. Die neuen Messungen variieren sie nicht nachträglich.',
        '', '## Jede bestehende Gitterzeile: Entfernung zur heutigen Basis','',
        'Diese Tabelle rekonstruiert **alle 85 bestehenden Code-Konfigurationen**, unabhängig davon, ob ihr Name noch „LIVE“ enthält. Änderungen werden aus den effektiven Parametern berechnet. Mehrere Unterschiede sind keine Einzelgegenprobe. Der heutige 79-Zeilen-Audit übernimmt die alten Parameterwerte, setzt sie aber auf dieselbe Basis; er ist deshalb ausdrücklich keine Reproduktion des alten Laufs.',
        '', '| alte Gitterzeile | Anzahl Unterschiede | wirkliche Unterschiede zu heute |','|---|---:|---|']
    old=[]
    for r in bt.GRID:
        dif={k:r[k] for k in bt.EVAL_KEYS if r[k]!=base[k]}
        if r.get('deploy_pct',1)!=1:dif['deploy_pct']=r['deploy_pct']
        old.append(dict(label=r['label'],diff= dif,parameters=r))
        lines.append(f'| {r["label"]} | {len(dif)} | {", ".join(f"{k}={val(v)}" for k,v in dif.items()) or "identisch"} |')
    (OUT/'PARAMETER.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'parameter-verzeichnis.json').write_text(json.dumps(dict(parameters=registry,old_grid=old),ensure_ascii=False,indent=2),encoding='utf-8')
    ix=['# Historische Belegstände','',
        f'{len(hist["reports"])} verschiedene Versionen von BACKTEST.md und {len(hist["configurations"])} Änderungen der Konfigurationsdatei wurden aus allen lokal verfügbaren Git-Refs inventarisiert. Jeder Bericht einschließlich sämtlicher Tabellenzellen ist in [historie.json](historie.json) gespeichert. Der Commit hier ist der erste gefundene Beleg dieses Dateiblobs, nicht automatisch die exakte Checkout-SHA des damaligen Rechenprozesses.',
        '', '**Reproduktionsgrenze:** Ohne die damaligen vollständigen Eingaben sind diese Berichte Beleg eines berichteten Ergebnisses, kein unabhängiger Renditenachweis. Neuabruf heutiger Marktdaten wäre kein Replay. Im über GitHub erreichbaren Artefaktbestand lagen am Auditzeitpunkt neben Pages nur die zwei E44.5-Artefakte; die vollständigen älteren Inputstände wurden nicht gefunden.',
        '', '| Berichtdatum laut Git | Beleg-Commit | Fenster / Erstellungszeit im Bericht |','|---|---|---|']
    for r in hist['reports']:
        header=' / '.join(s.replace('|','/') for s in r['header'][:4] if s and not s.startswith('#'))
        ix.append(f'| {r["date"]} | [{r["commit"][:10]}](https://github.com/szoceikaiser/btc-signal-app/blob/{r["commit"]}/BACKTEST.md) | {header} |')
    ix+=['','## Alle Konfigurationsstände','', '| Datum | Commit | Änderung laut Commit |','|---|---|---|']
    for r in hist['configurations']:
        ix.append(f'| {r["date"]} | [{r["commit"][:10]}](https://github.com/szoceikaiser/btc-signal-app/blob/{r["commit"]}/site/data/config.json) | {r["subject"].replace("|","/")} |')
    (OUT/'HISTORISCHE-BELEGE.md').write_text('\n'.join(ix)+'\n',encoding='utf-8')
    print('Registry',len(registry),'old grid',len(old),'historical reports',len(hist['reports']))

if __name__=='__main__':main()
