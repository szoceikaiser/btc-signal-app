"""Reference ledger must catch erroneous fees, funding and quantities."""
from copy import deepcopy
from decimal import Decimal as D
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'engine'))
from execution_perp_offline import PerpBook, HOUR
from a8_perp_reference import verify


def main():
    book=PerpBook('1000','0.001')
    opening=dict(id='open',ts=0,type='KAUF_1',action='entry_t1',tranche_pct=50)
    closing=dict(id='close',ts=4*HOUR,type='VERKAUF_REST',action='rest_pattern',tranche_pct=100)
    book.fill(opening,4*HOUR,100,100)['event']['audit_order']=opening
    for t in range(5*HOUR,9*HOUR,HOUR): book.payment(t-HOUR,t,D('.1'),100)
    book.fill(closing,8*HOUR,100,100)['event']['audit_order']=closing
    result=dict(book=book,end_at=8*HOUR)
    args=dict(start=4*HOUR,marks={t:100 for t in range(4*HOUR,9*HOUR,HOUR)},
              trade_opens={4*HOUR:100,8*HOUR:100},
              rates={t:D('.1') for t in range(4*HOUR,8*HOUR,HOUR)},assumed={},capital='1000')
    assert verify(result,**args)['passed']
    for index,field in ((0,'fee'),(1,'amount'),(-1,'qty')):
        broken=deepcopy(result)
        e=broken['book'].events[index]
        e[field]=str(D(e[field])+D(1))
        try: verify(broken,**args)
        except AssertionError: pass
        else: raise AssertionError('Independent reference missed '+field)
    print('A8 reference: valid hand ledger and 3 corruptions detected')


if __name__=='__main__': main()
