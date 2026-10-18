"""One-shot historical market GETs; no engine, broker accounts or Telegram.
Only Coinalyze credentials enter this step, never logs or output artifacts.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import urllib.request
import urllib.parse

START=1790481600
END=1790683200


def main():
    out=Path('historical-raw')
    out.mkdir(exist_ok=False)
    key=os.environ.get('COINALYZE_API_KEY')
    if not key:raise SystemExit('Required Coinalyze key unavailable')
    metadata=[]
    def get(name,url,headers=None):
        at=datetime.now(timezone.utc).isoformat()
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'btc-historical-audit',**(headers or {})})
            with urllib.request.urlopen(req,timeout=45) as r:
                raw=r.read();status=r.status
            json.loads(raw)
        except Exception:
            raise SystemExit('Historical GET failed: '+name) from None
        if key.encode() in raw:raise SystemExit('Unexpected secret in response')
        (out/(name+'.json')).write_bytes(raw)
        metadata.append(dict(name=name,url=url,retrieved_at=at,status=status,
            sha256=hashlib.sha256(raw).hexdigest()))
    params=dict(symbols='BTCUSDT_PERP.A',interval='4hour',
                **{'from':START,'to':END},convert_to_usd='true')
    for endpoint in ['open-interest-history','liquidation-history','ohlcv-history','long-short-ratio-history']:
        get(endpoint,'https://api.coinalyze.net/v1/'+endpoint+'?'+urllib.parse.urlencode(params),{'api_key':key})
    get('spot','https://data-api.binance.vision/api/v3/klines?'+urllib.parse.urlencode(
        dict(symbol='BTCUSDT',interval='4h',startTime=START*1000,endTime=END*1000-1,limit=1000)))
    get('funding','https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol=PF_XBTUSD')
    (out/'manifest.json').write_text(json.dumps(dict(start=START,end=END,
        run_id=os.environ.get('GITHUB_RUN_ID'),commit=os.environ.get('GITHUB_SHA'),
        sources=metadata),indent=2),encoding='utf-8')
    print('Historical market data acquired; hashes saved. No strategy run or live writes.')


if __name__=='__main__':main()
