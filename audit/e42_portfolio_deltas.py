"""Compare actual non-rebuy order intents and funded quantities in both portfolio paths."""
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from book import account, BUY, SELL

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'

def main():
    raw=json.loads((ROOT/'docs/e445/eingaben.json').read_text())
    saved=json.loads((ROOT/'docs/e445/signale.json').read_text())
    cs=[SimpleNamespace(**c) for c in raw['candles']]
    names={'baseline':'LIVE-heute +Bein in Handelsrichtung','e42':'LIVE-heute +E42'}
    books={k:account(saved[name],cs,raw['start']) for k,name in names.items()}
    def indexed(which):
        counts=Counter();out={}
        ss=saved[names[which]]
        for f in books[which]['fills']:
            s=ss[f['signal']]
            if s['type'] in ('RUECKKAUF','RUECKKAUF_STOP'): continue
            identity=(s['ts'],s['type'],s['price'],s['tranche_pct'])
            counts[identity]+=1
            out[(*identity,counts[identity])]=dict(signal=s,fill=f)
        return out
    base,new=indexed('baseline'),indexed('e42')
    changed=[]
    for key in sorted(base.keys() & new.keys()):
        a,b=base[key],new[key]
        if abs(a['fill']['nominal']-b['fill']['nominal'])>.01:
            changed.append(dict(ts=key[0],type=key[1],price=key[2],tranche_pct=key[3],
                                baseline=a['fill'],e42=b['fill']))
    result=dict(description='Original inputs; F09 independent ledger. Accounting difference, not isolated causal attribution. Non-rebuy means standard signal TYPE only; a standard STOPLOSS can still close only rebuy units.',
                added_non_rebuy=[new[k] for k in sorted(new.keys()-base.keys())],
                removed_non_rebuy=[base[k] for k in sorted(base.keys()-new.keys())],
                matched_orders_different_size=changed)
    (OUT/'e42-portfolio-unterschiede.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Added non-rebuy',len(result['added_non_rebuy']),'removed',len(result['removed_non_rebuy']),
          'matched different size',len(changed))
    for r in changed:
        if r['type'] in BUY and 1773400000000<r['ts']<1774300000000:
            print(json.dumps(r,ensure_ascii=False))
    for kind in ('added_non_rebuy','removed_non_rebuy'):
        print(kind,json.dumps(result[kind][:2],ensure_ascii=False))

if __name__=='__main__': main()
