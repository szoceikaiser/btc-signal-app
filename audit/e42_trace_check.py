"""Independent runtime trace of nested observation creation/end, including same-bar replacements."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/audit-2026-09-27'
sys.path.insert(0, str(ROOT / 'engine'))
import strategy_core as sc

def trace():
    raw = json.loads((ROOT / 'docs/e445/eingaben.json').read_text())
    cs = [sc.Candle(**x) for x in raw['candles']]
    fl = [sc.FlowPoint(**x) for x in raw['flow']]
    results = json.loads((ROOT / 'docs/e445/ergebnis.json').read_text())
    cfg = next(x['params'] for x in results['zeilen'] if x['rolle'] == 'Hauptzeile')
    pos = sc.Position()
    rows = []
    all_signals = []
    calls = []
    def profile(frame, event, value):
        if event != 'return' or frame.f_globals is not sc.__dict__:
            return
        name = frame.f_code.co_name
        if name == '_e42_beobachten' and value:
            calls.append(dict(kind='begin', mark=pos.e42_marke,
                              start=pos.e42_start_ts, breakout=pos.e42_ausbruch_ts))
        elif name == '_e42_ende':
            calls.append(dict(kind='end'))
        elif name == 'ruecktest_schritt' and value:
            calls.append(dict(kind='step', result=value,
                              mark=frame.f_locals['marke'], start=pos.e42_start_ts))
    prior = sys.getprofile()
    try:
        sys.setprofile(profile)
        for i, c in enumerate(cs):
            if c.ts < raw['start']:
                pos.last_signal_ts = c.ts
                continue
            calls = []
            signals = [s.to_dict() for s in sc.evaluate(cs[:i+1], fl[:i+1], pos, **cfg)]
            all_signals.extend(signals)
            if calls or signals or pos.e42_meldungen:
                rows.append(dict(ts=c.ts, calls=calls, signals=signals,
                                 messages=pos.e42_meldungen,
                                 final_mark=pos.e42_marke, final_start=pos.e42_start_ts))
    finally:
        sys.setprofile(prior)
    saved = json.loads((ROOT / 'docs/e445/signale.json').read_text())['LIVE-heute +E42']
    clean = lambda ss: [{k:v for k,v in s.items() if k != 'beobachtung_kerzen'} for s in ss]
    assert clean(all_signals) == clean(saved)
    current = None
    observations = {}
    for row in rows:
        for c in row['calls']:
            if c['kind'] == 'begin':
                key = f'{c["start"]}:{c["mark"]}'
                if current is not None and current != key:
                    observations[current].update(end=row['ts'], end_reason='neue_beobachtung')
                observations.setdefault(key, dict(key=key, start=c['start'], mark=c['mark']))
                current = key
            elif c['kind'] == 'end':
                if current is not None:
                    observations[current].update(end=row['ts'], end_reason='beobachtung_beendet')
                current = None
        expected = f'{row["final_start"]}:{row["final_mark"]}' if row['final_mark'] is not None else None
        assert current == expected, (row['ts'], current, expected)
    if current is not None:
        observations[current]['end_reason'] = 'am_datenende_offen'
    result = dict(description='Runtime profile of actual nested begin/end calls; no production edits',
                  input_sha256=hashlib.sha256((ROOT/'docs/e445/eingaben.json').read_bytes()).hexdigest(),
                  engine_sha256=hashlib.sha256((ROOT/'engine/strategy_core.py').read_bytes()).hexdigest(),
                  signals_exact=True, observations=list(observations.values()), timeline=rows)
    (OUT / 'e42-ablaufkontrolle.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    old = json.loads((OUT / 'e42-faelle.json').read_text())
    prior_obs = {f'{o["start"]}:{o["mark"]}':o for o in old['observations']}
    print('Runtime observations', len(observations), 'prior', len(prior_obs))
    print('Previously missing:', list(observations.keys() - prior_obs.keys()))
    for key, o in observations.items():
        p = prior_obs.get(key)
        if p and (o.get('end'), o['end_reason']) != (p.get('end'), p['end_reason']):
            print('Changed:', p['id'], p.get('end'), p['end_reason'], '->', o.get('end'), o['end_reason'])

if __name__ == '__main__':
    trace()
