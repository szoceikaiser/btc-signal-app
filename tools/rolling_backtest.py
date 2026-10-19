"""Manual C05 replay. Read market/archive inputs; write only a separate report.

The unchanged accepted Core20D supplies parsing, UM2 gates and exact-budget V1.
No live state, Telegram, repository writes or parameter search are used here.
"""
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

STEP = 14_400_000
DAY = 86_400_000
CORE = '20d755a4332fb32aeab08b1973b650eeae10f31e'
CONFIG = '3efe8a17330c228a75fe879d4e7c7ed0cade766e4a07ca0c05832b88aa3d282b'
PARAMS = 'a99be30ae26a753f9734fbe2d67ac49f33e090a691904336421742f92420f787'
FIELDS = ('oi', 'liq', 'fut', 'ls')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def utc(ts):
    return datetime.fromtimestamp(ts / 1000, timezone.utc).isoformat()


def window(now_ms):
    if type(now_ms) is not int or now_ms < 366 * DAY:
        raise ValueError('Invalid UTC cutoff')
    end = now_ms // STEP * STEP
    # Technical EMA warmup only; never included in profit or the 365-day period.
    start = end - 365 * DAY
    return start - 200 * STEP, start, end


def series(raw, start, end):
    """Validate every value; select only completed 4h observations in range."""
    result = {}
    for key, value in raw.items():
        ts = int(key)
        if str(ts) != str(key) or ts % STEP:
            raise ValueError('Invalid archive timestamp')
        values = value if isinstance(value, (list, tuple)) else [value]
        if not all(type(v) in (int, float) and math.isfinite(v) for v in values):
            raise ValueError('Invalid archive number')
        if start <= ts and ts + STEP <= end:
            result[ts] = tuple(value) if isinstance(value, list) else value
    return result


def merge(archive, fresh, start, end):
    result, coverage = {}, {}
    for field in FIELDS:
        old = series(archive[field], start, end)
        new = series(fresh.get(field, {}), start, end)
        combined = {**old, **new}
        if field == 'liq' and any(not isinstance(v, tuple) or len(v) != 2 or min(v) < 0
                                  for v in combined.values()):
            raise ValueError('Invalid liquidation observation')
        if field != 'liq' and any(type(v) not in (int, float) for v in combined.values()):
            raise ValueError('Invalid scalar observation')
        if field == 'oi' and any(v < 0 for v in combined.values()):
            raise ValueError('Invalid open interest')
        result[field] = combined
        coverage[field] = dict(archived=len(old), fresh=len(new),
                               archive_only=len(old.keys() - new.keys()), merged=len(combined))
    return result, coverage


def validate_prices(raw, load_start, start, end):
    by_ts = {}
    for row in raw:
        ts = int(row[0])
        if not load_start <= ts or ts + STEP > end:
            continue
        if ts % STEP or ts in by_ts:
            raise ValueError('Duplicate or unaligned price candle')
        values = [float(row[i]) for i in (1, 2, 3, 4, 7, 10)]
        if not all(math.isfinite(v) and v >= 0 for v in values):
            raise ValueError('Invalid price/volume')
        o, h, low, c = values[:4]
        if min(o, h, low, c) <= 0 or not low <= min(o, c) <= max(o, c) <= h:
            raise ValueError('Invalid OHLC')
        by_ts[ts] = row
    rows = [by_ts[t] for t in sorted(by_ts)]
    if (not rows or int(rows[0][0]) != load_start or int(rows[-1][0]) != end - STEP
            or len(rows) != (end - load_start) // STEP):
        raise ValueError('Price history incomplete; current closed candle required')
    return rows


def bind_core(path):
    path = Path(path).resolve()
    actual = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain'], text=True)
    if actual != CORE or dirty:
        raise ValueError('Clean accepted Core20D required')
    sys.path.insert(0, str(path / 'engine'))
    import backtest
    import production_contract
    if Path(backtest.__file__).resolve() != path / 'engine/backtest.py':
        raise ValueError('Foreign engine import')
    return backtest, production_contract


def report_markdown(r):
    result = r['result']
    lines = ['# C05-Backtest – aktueller manueller Lauf', '',
             f"Stand: {utc(r['observed_ms'])}",
             f"Messfenster: **{utc(r['start_ms'])} bis {utc(r['end_ms'])}** (UTC).",
             'Maximal 365 Tage; nur vollständig abgeschlossene 4h-Kerzen.',
             'Wenn OI erst später vorliegt, ist das tatsächliche Messfenster kürzer.',
             '200 zusätzliche Kerzen dienen ausschließlich dem technischen Vorlauf.', '',
             f"10.000 USD ohne Anfangsbestand → **{result['ende']:,.2f} USD** "
             f"(**{result['rendite_pct']:+.2f} %**).",
             f"Gebühren: {result['fees']:,.2f} USD; offene BTC im Endwert enthalten.",
             'Modell S0: 0,1 % je Ausführung, nächstes 4h-Open, kein Slippage-Aufschlag.',
             'Dies ist eine historische Modellrechnung, keine echte Kontorendite.', '',
             '## Datenabdeckung', '',
             '| Coinalyze-Reihe | Archiv | Frisch | Nur Archiv | Zusammengeführt |',
             '|---|---:|---:|---:|---:|']
    for field, c in r['archive_coverage'].items():
        lines.append(f"| {field} | {c['archived']} | {c['fresh']} | {c['archive_only']} | {c['merged']} |")
    lines += ['', 'Alle vorhandenen Archivwerte im angeforderten Fenster werden eingelesen; '
              'frische Werte ersetzen Überschneidungen. Gezählt einschließlich separat ausgewiesenem Vorlauf.',
              'Fehlende Messungen werden nicht erfunden. Die unveränderten Missing-Gates der Engine gelten.',
              '', '| Messwert im tatsächlichen Messfenster | Abdeckung |', '|---|---|']
    for name, counts in r['flow_coverage'].items():
        lines.append(f"| {name} | " + ', '.join(f'{k}: {v}' for k, v in counts.items()) + ' |')
    lines += ['', f"Datenstatus: **{r['data_status']}**.",
              *[f'- {warning}' for warning in r['warnings']], '',
              '## Abgrenzung', '',
              'Keine Live-Position übernommen, keine Orders oder Telegram-Nachrichten versandt, '
              'keine Strategieparameter ausgewählt oder geändert. Die fest veröffentlichte '
              'C05-Referenz auf der Webseite bleibt ein eigener historischer Bericht.', '',
              f"Core: `{r['core_sha']}`; Konfiguration: `{r['config_sha256']}`.",
              f"Eingabedatensatz: `{r['inputs_sha256']}`. Vollständige Eingaben, Buchungen und "
              'Datenabdeckung liegen im Artefakt dieses Laufs.']
    return '\n'.join(lines) + '\n'


def execute(core, archive_path, out, now_ms=None):
    bt, contract = bind_core(core)
    now = int(time.time() * 1000) if now_ms is None else now_ms
    load_start, requested_start, end = window(now)
    config = contract.effective_config(json.loads(os.environ['REVIEWED_CONFIG_JSON']))
    if contract.digest(config) != CONFIG:
        raise ValueError('C05 runtime configuration differs')
    candidate = json.loads((Path(core) / 'docs/um2-engine-integration/candidates/C05-UM2.inactive.json').read_bytes())
    params = candidate['params']
    if digest(params) != PARAMS or any(config.get(k) != v for k, v in params.items()):
        raise ValueError('C05 strategy parameters differ')
    archive_bytes = Path(archive_path).read_bytes()
    archive = json.loads(archive_bytes)
    if not isinstance(archive, dict) or set(archive) != set(FIELDS):
        raise ValueError('Missing or malformed Coinalyze archive')
    raw = validate_prices(bt.fetch_candles_range(load_start, end), load_start, requested_start, end)
    warnings, fresh = [], {}
    key = os.environ.get('COINALYZE_API_KEY', '')
    import coinalyze
    for field, fetch in zip(FIELDS, (coinalyze.oi_by_ts, coinalyze.liquidations_by_ts,
                                    coinalyze.fut_delta_by_ts, coinalyze.long_short_by_ts)):
        try:
            if not key:
                raise ValueError('No configured key')
            fresh[field] = fetch(key, frm=load_start // 1000, to=end // 1000)
        except Exception:
            warnings.append(f'Frischer Coinalyze-Abruf {field} nicht verfügbar; vorhandenes Archiv verwendet.')
            fresh[field] = {}
    merged, coverage = merge(archive, fresh, load_start, end)
    oi_in_window = [t for t in merged['oi'] if requested_start <= t < end]
    if not oi_in_window:
        raise ValueError('No observed OI in requested window; no fictitious neutral backtest')
    start = max(requested_start, min(oi_in_window))
    try:
        funding = [(t, v) for t, v in bt.fetch_funding_8h() if load_start <= t <= end]
    except Exception:
        warnings.append('Kraken-Funding nicht verfügbar; fehlende Abdeckung ausdrücklich markiert.')
        funding = []
    candles, flow = bt.build_series(raw, funding, merged['oi'], merged['liq'], merged['fut'],
                                    merged['ls'], end_ms=end)
    flow_coverage = {}
    for f in flow:
        if f.ts >= start:
            for field, meta in f.provenance.items():
                flow_coverage.setdefault(field, Counter())[meta['coverage']] += 1
    if start > requested_start:
        warnings.append('Das OI-Archiv beginnt später als die 365-Tage-Grenze; kürzeres Messfenster.')
    incomplete = any(counts.get('missing', 0) or counts.get('stale', 0) for counts in flow_coverage.values())
    if incomplete:
        warnings.append('Messlücken vorhanden; Modellrechnung mit ausgewiesenen Missing-Gates, keine lückenlose Datenhistorie.')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    inputs = dict(observed_ms=now, load_start_ms=load_start, requested_start_ms=requested_start,
                  start_ms=start, end_ms=end, config=config, params=params, price_candles=raw,
                  funding=funding, coinalyze=merged)
    input_bytes = canonical(inputs)
    (out / 'inputs.json').write_bytes(input_bytes)
    # One fixed configuration and cost scenario; no variants, no search.
    from liquidation_evidence import collect_events
    with collect_events() as events:
        result = bt.run_execution(candles, flow, params, start_ms=start, end_ms=end,
                                  fee=.001, slippage=0., start_capital=10000.)
    if (not math.isclose(result['ende'], result['cash'] + result['btc'] * candles[-1].close,
                         abs_tol=1e-8) or result['reserved_cash'] or result['reserved_btc']):
        raise ValueError('Final accounting differs')
    report = dict(schema='btc-c05-rolling-backtest-v1', core_sha=CORE, config_sha256=CONFIG,
                  strategy_sha256=PARAMS, observed_ms=now, requested_start_ms=requested_start,
                  start_ms=start, end_ms=end, max_days=365, warmup_candles=200,
                  archive_sha256=hashlib.sha256(archive_bytes).hexdigest(),
                  inputs_sha256=hashlib.sha256(input_bytes).hexdigest(), archive_coverage=coverage,
                  flow_coverage=flow_coverage, data_status='mit Messlücken' if incomplete else 'vollständig',
                  warnings=warnings, result=result, missing_gate_events=events, is_live_account=False)
    (out / 'report.json').write_bytes(canonical(report))
    (out / 'BACKTEST.md').write_text(report_markdown(report), encoding='utf-8')
    print(f"C05 bis {utc(end)}; {utc(start)}; {report['data_status']}; Bericht: {out / 'BACKTEST.md'}")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for field in ('core', 'archive', 'out'):
        p.add_argument('--' + field, required=True)
    args = p.parse_args()
    execute(args.core, args.archive, args.out)
