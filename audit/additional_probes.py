"""No real network, credentials or production writes: data and delivery probes."""
import contextlib,io,json,os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'
sys.path.insert(0,str(ROOT/'engine'))
import main as live
import strategy_core as sc
import telegram_notify as tg
import coinalyze as cz

def main():
    result={}
    values,report=cz._summiere_vollstaendig({'A':{0:10.,1:11.}},['A','B'],[], 'USD')
    assert values=={0:10.,1:11.} and report['ohne_antwort']==['B']
    result['F14_missing_entire_market']=dict(requested=['A','B'],values=values,report=report,
        expected_for_claimed_all_market_rule={})
    selected,excluded=cz._nach_denominierung({
        'a':dict(symbol='BTC-denominated',denominierung='BTC',summe_v=1000),
        'b':dict(symbol='USD-denominated',denominierung='USD',summe_v=2000)})
    assert selected==['USD-denominated']
    result['F15_incomparable_volume_units']=dict(selected=selected,excluded=excluded,
        btc_volume=1000,usd_volume=2000,example_price_usd=60000,
        independent_dollar_volumes=[60000000,2000])
    warm=[sc.Candle(0,100,101,99,100),sc.Candle(14400000,120,121,119,120),
          sc.Candle(28800000,90,91,89,90)]
    measured=sc.atr(warm,14)
    assert measured==2.0
    result['F16_atr_short_history']=dict(production=measured,independent_true_ranges=[21,31],
        independent_atr=26,scope='len(candles)<=period; live standard long warm-up not affected')
    result['D02_missing_flow_confirmation']=dict(
        neutral_zero_funding_allows_long=sc.confirm_ok(sc.Pattern.NEUTRAL,[sc.FlowPoint(0,0,0,1,0)],True),
        scope='Missing values use the same zero as true neutral observations; this can satisfy the OR entry confirmation')
    c=sc.Candle(14400000,100,101,99,100)
    sig=sc.Signal(c.ts,sc.SignalType.KAUF_1,100,25,'audit only')
    def evaluate(cs,fs,pos,**kw):
        pos.last_signal_ts=cs[-1].ts
        return [sig]
    # The real send_telegram is replaced, and a separate network sentinel is in force.
    with tempfile.TemporaryDirectory(prefix='btc-audit-outbox-') as temp:
        directory=Path(temp)
        (directory/'config.json').write_text(json.dumps(dict(plan_telegram=False,vorschau_telegram=False)))
        with patch.dict(os.environ,{'TELEGRAM_BOT_TOKEN':'AUDIT_FAKE','TELEGRAM_CHAT_ID':'AUDIT_FAKE'}), \
             patch.object(tg,'send_telegram',return_value=False) as sender, \
             patch.object(tg.urllib.request,'urlopen',side_effect=AssertionError('network forbidden')), \
             patch.object(live,'evaluate',side_effect=evaluate), \
             patch.object(live,'positions_plan',return_value={}), \
             patch.object(live,'widerstand_marken',return_value=[]), \
             patch.object(live,'zonen_vorschau',return_value=None), \
             contextlib.redirect_stdout(io.StringIO()):
            first=live.run_engine(fetch=lambda old:([c],[],[]),data_dir=directory)
            calls_first=sender.call_count
            second=live.run_engine(fetch=lambda old:([c],[],[]),data_dir=directory)
            calls_second=sender.call_count-calls_first
        state=json.loads((directory/'state.json').read_text())
        result['F13_failed_delivery_not_retried']=dict(first_signal_count=len(first),
            first_attempts=calls_first,retry_signal_count=len(second),retry_attempts=calls_second,
            persisted_last_signal_ts=state['last_signal_ts'],all_send_attempts_returned=False)
        assert len(first)==1 and calls_first==1 and second==[] and calls_second==0
    # Independent causality test catches a deliberately premature pivot detector.
    cs=[sc.Candle(i*14400000,95,110 if i==10 else 100,90,95) for i in range(20)]
    def causal(detector):
        for end in range(1,len(cs)+1):
            assert all(p.idx<=end-5-1 for p in detector(cs[:end],5))
    causal(sc.find_pivots)
    def premature(candles,n):
        return [sc.Pivot(10,cs[10].ts,110,'H')] if len(candles)>=11 else []
    try:causal(premature)
    except AssertionError:result['P04_future_pivot_sabotage']='CAUGHT'
    else:raise AssertionError('Pivot sabotage survived')
    (OUT/'weitere-gegenproben.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
