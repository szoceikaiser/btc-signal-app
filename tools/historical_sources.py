"""Read-only local/archive inventory and bounded public historical GET requests.

No broker, credentials, live engine, workflow dispatch or strategy evaluation.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/nach-6'
BASE = '05208cecce8d5a0e856a1ea56984b209f403ccd6'
ARCHIVE = 'site/data/archiv/coinalyze_4h.json'
STEP = 14400000
CUTOFF = 1790683200000  # 2026-09-29 12:00 UTC


def sha(raw): return hashlib.sha256(raw).hexdigest()
def git(*args): return subprocess.check_output(['git', '-c', 'safe.directory='+ROOT.as_posix(), *args], cwd=ROOT)
def dump(p, obj): p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    rawdir = OUT/'sources'
    rawdir.mkdir(exist_ok=True)
    source = ROOT.parent/'audit-backups/6-abschluss-05208ce/eingefrorene-inputs/eingaben.json'
    raw = source.read_bytes()
    assert sha(raw) == 'ce749958a3ab1679f5cfee303ee58e37cc93d42eeee35f28d7f954d0cb1dcd7a'
    d = json.loads(raw)
    closed = [c for c in d['candles'] if c['ts']+STEP <= d['ende']]
    needed = list(range(closed[-1]['ts']+STEP, CUTOFF, STEP))
    local = []
    for line in git('worktree', 'list', '--porcelain').decode().splitlines():
        if line.startswith('worktree '):
            path = Path(line[9:])
            local.append(dict(path=str(path), status=subprocess.check_output(
                ['git','-c','safe.directory='+path.as_posix(),'status','--porcelain'], cwd=path).decode()))
    versions = []
    for commit in git('log','--all','--format=%H','--',ARCHIVE).decode().splitlines():
        blob = git('show',commit+':'+ARCHIVE)
        a = json.loads(blob)
        (rawdir/('archive-'+commit[:12]+'.json')).write_bytes(blob)
        versions.append(dict(commit=commit, sha256=sha(blob),
            committed_at=git('show','-s','--format=%cI',commit).decode().strip(),
            fields={k:dict(count=len(v), first=min(map(int,v)), last=max(map(int,v)),
                missing_extension=[t for t in needed if str(t) not in v]) for k,v in a.items()}))
    attempts = []
    urls = {
        'remote-main': 'https://api.github.com/repos/szoceikaiser/btc-signal-app/branches/main',
        'binance-extension': 'https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=4h&startTime='+str(needed[0])+'&endTime='+str(CUTOFF-1)+'&limit=1000',
    }
    def get(name, url):
        at = datetime.now(timezone.utc).isoformat()
        record = dict(name=name, url=url, retrieved_at=at)
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'btc-historical-audit','Accept':'application/json'})
            with urllib.request.urlopen(req, timeout=25) as response:
                blob = response.read()
                record.update(status=response.status, sha256=sha(blob))
            (rawdir/(name+'.json')).write_bytes(blob)
            value = json.loads(blob)
        except urllib.error.HTTPError as e:
            blob = e.read()
            (rawdir/(name+'-error.txt')).write_bytes(blob)
            record.update(status=e.code, sha256=sha(blob))
            value = None
        except urllib.error.URLError:
            # A sandbox/network failure must be retried with explicit escalation.
            raise
        attempts.append(record)
        return value
    remote = get('remote-main', urls['remote-main'])
    if remote:
        commit = remote['commit']['sha']
        a = get('remote-archive', 'https://raw.githubusercontent.com/szoceikaiser/btc-signal-app/'+commit+'/'+ARCHIVE)
        if a:
            versions.append(dict(commit=commit, source='remote exact SHA, data only',
                sha256=attempts[-1]['sha256'], retrieved_at=attempts[-1]['retrieved_at'],
                fields={k:dict(count=len(v), first=min(map(int,v)), last=max(map(int,v)),
                    missing_extension=[t for t in needed if str(t) not in v]) for k,v in a.items()}))
    extension = get('binance-extension', urls['binance-extension'])
    # No reconstruction from unrelated live rolling histories or partial bars.
    fields = {
        'candles.ts/open/high/low/close':'Binance Vision BTCUSDT spot 4h kline open timestamp; OHLC fields 1..4',
        'flow.spot_cvd':'Same Binance kline: cumulative sum 2*taker_buy_quote_volume - quote_volume (USD)',
        'flow.fut_cvd':'Coinalyze BTCUSDT_PERP.A Binance perp, cumulative taker BTC delta',
        'flow.oi':'Coinalyze BTCUSDT_PERP.A open interest converted to USD',
        'flow.oi_btc':'flow.oi divided by same bar close, legacy fallback/carry behavior',
        'flow.long_liq/short_liq':'Coinalyze BTCUSDT_PERP.A liquidations in USD',
        'flow.long_pct':'Coinalyze BTCUSDT_PERP.A long-short-ratio, long percent',
        'flow.funding':'Legacy fetch_funding_8h source/fallback requires provenance; last timestamp <= bar close',
    }
    manifest = dict(base=BASE, r0_sha256=sha(raw), r0_generated=d['erzeugt'],
        r0_cutoff=d['ende'], r0_first=closed[0]['ts'], r0_closed_bars=len(closed),
        r0_field_prefix_sha256=sha(json.dumps(dict(candles=closed,flow=d['flow'][:len(closed)]),sort_keys=True).encode()),
        r0_unfinished_excluded=d['candles'][-1]['ts'], r1_cutoff=CUTOFF,
        needed_bar_open_ms=needed, needed_bars=len(needed), archives=versions, requests=attempts,
        coinalyze_key_available=bool(os.environ.get('COINALYZE_API_KEY')),
        fields={k:dict(source_transform=v, first_provable_version='frozen file generated '+d['erzeugt'],
            availability_at_historical_close='unknown/idealized', vintage='original API responses not preserved in R0; later archives may revise') for k,v in fields.items()},
        r1_complete=False, r1_measured=False,
        status='Review inventory and missing required fields before any R1 assembly',
        local_worktrees=local)
    dump(OUT/'data-manifest.json', manifest)
    print(json.dumps(dict(needed_bars=len(needed), archives=[dict(commit=v['commit'],missing={k:len(f['missing_extension']) for k,f in v['fields'].items()}) for v in versions], requests=attempts),indent=2))


if __name__ == '__main__': main()
