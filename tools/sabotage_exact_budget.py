"""Isolated synthetic budget mutation coverage, no historical strategy runs."""
import sys,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main(output):
    out=Path(output).resolve();out.mkdir(exist_ok=False)
    sys.path.insert(0,str(ROOT/'engine'))
    import test_exact_budget as tests
    cases=[n for n in dir(tests) if n.startswith('test_')]
    driver="import sys,json;sys.dont_write_bytecode=True;sys.path.insert(0,sys.argv[1]);import test_exact_budget as t;out=[]\nfor n in json.loads(sys.argv[2]):\n try:getattr(t,n)()\n except Exception as e:out.append(dict(case=n,caught=True,error=type(e).__name__))\n else:out.append(dict(case=n,caught=False))\nprint(json.dumps(out))"
    def run(folder,names):
        p=subprocess.run([sys.executable,'-X','utf8','-B','-c',driver,str(folder),json.dumps(names)],capture_output=True,text=True,encoding='utf8')
        assert p.returncode==0,p.stderr
        return json.loads(p.stdout)
    assert not any(x['caught'] for x in run(ROOT/'engine',cases))
    faults=[
        ('partial_hidden_by_float','execution_v1.py',"partial=buy and amount_exact<Fraction(o['requested_exact'])",'partial=fraction<1'),
        ('binary_budget','exact_money.py','value = self.alloc * decimal(pct) / 100','value = decimal(float(self.alloc) * float(pct) / 100)'),
        ('small_cash_erased','exact_money.py','self.initial = self.cash = decimal(capital)','self.initial = self.cash = decimal(capital) if float(capital)>1e-6 else Fraction(0)'),
        ('all_reservations_released','exact_money.py',"del self.pending[order['id']]",'self.pending.clear()'),
        ('sale_fee_not_charged','exact_money.py','self.cash += net','self.cash += gross'),
        ('old_book_version_accepted','execution_v1.py',"state.get('version') != 2","state.get('version') not in (1, 2)"),
        ('pending_not_consumed','exact_money.py',"del self.pending[order['id']]",'pass  # faulty repeatable reservation'),
        ('delayed_old_semantics_accepted','execution_delayed.py',"or resume_state['execution_semantics']!=v.EXECUTION_SEMANTICS",'or False'),
    ]
    uncovered=set(cases);rows=[];coverage={}
    for name,file,old,new in faults:
        folder=out/name;folder.mkdir()
        for p in (ROOT/'engine').glob('*.py'):shutil.copyfile(p,folder/p.name)
        p=folder/file;s=p.read_text(encoding='utf8');assert s.count(old)==1,(name,s.count(old))
        p.write_text(s.replace(old,new),encoding='utf8')
        result=run(folder,cases);caught=[x['case'] for x in result if x['caught']]
        assert caught,name
        for case in caught:coverage.setdefault(case,[]).append(name)
        uncovered-=set(caught);rows.append(dict(fault=name,caught=caught))
    assert not uncovered,uncovered
    result=dict(passed=True,cases=cases,coverage=coverage,faults=rows,historical_strategy_starts=0)
    (out/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
if __name__=='__main__':main(sys.argv[1])
