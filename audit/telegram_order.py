"""Reach E41 waiting + partial sale in the SAME candle; no real Telegram calls."""
import contextlib,inspect,io,json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'
sys.path.insert(0,str(ROOT/'engine'))
import main as live
import strategy_core as sc

def scenario(mutated=False):
    z=sc.fib_zones(sc.Impulse(sc.Pivot(0,0,80,'L'),sc.Pivot(1,14400000,160,'H')))
    p=sc.Position(direction='LONG',state=sc.PosState.CORE,zones=z,retrace_extreme=100,
        entry_ref=110,entry_pct=75,bestand_pct=75,last_signal_ts=14400000)
    c=sc.Candle(28800000,120,170,79,79.5)
    cfg=dict(plan_telegram=False,vorschau_telegram=False,stop_rueckeroberung=1,
        buy_ladder=False,trail_stop=False,high_exit='off',bias_short=False,rest_halten=True)
    events=[]
    def send_text(text,**kw):events.append('E41_WARTET' if 'WARTET' in text else 'TEXT')
    def send_signals(sigs,**kw):events.extend(s['type'] for s in sigs)
    with patch.object(live,'send_text',side_effect=send_text), \
         patch.object(live,'send_signals',side_effect=send_signals), \
         patch.object(live.urllib.request,'urlopen',side_effect=AssertionError('network forbidden')), \
         contextlib.redirect_stdout(io.StringIO()):
        function=live.run_engine
        if mutated:
            source=inspect.getsource(function)
            part='        if m41:\n            send_text(format_stop_rueckeroberung(m41), dry_run=dry_run)\n'
            assert source.count(part)==1
            source=source.replace(part,'').replace('            send_signals(sigs, dry_run=dry_run)\n',
                '            send_signals(sigs, dry_run=dry_run)\n'+part)
            namespace=dict(vars(live));exec(compile(source,'<isolated order mutation>','exec'),namespace)
            function=namespace['run_engine']
        with tempfile.TemporaryDirectory(prefix='btc-audit-order-') as temp:
            dest=Path(temp)
            (dest/'config.json').write_text(json.dumps(cfg))
            (dest/'state.json').write_text(json.dumps(live.pos_to_state(p)))
            signals=function(fetch=lambda old:([c],[],[]),data_dir=dest)
    return events,signals

def main():
    good,sigs=scenario()
    bad,_=scenario(True)
    assert 'E41_WARTET' in good and 'TEILVERKAUF_LADDER' in good,(good,sigs)
    assert good.index('E41_WARTET')<good.index('TEILVERKAUF_LADDER')
    assert bad.index('E41_WARTET')>bad.index('TEILVERKAUF_LADDER')
    result=dict(current=good,mutated=bad,signals=sigs,
        finding='Existing 607-test suite misses this ordering mutation. Independent reached-case check catches it.',
        production_behavior='Correct on this case; missing regression coverage, not a current ordering defect')
    (OUT/'telegram-reihenfolge.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
