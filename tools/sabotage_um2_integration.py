"""Synthetic mutation coverage of every new case; isolated copies, never engine writes."""
import sys
sys.dont_write_bytecode=True
import json,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DRIVER=r'''
import sys,json,socket,importlib
sys.dont_write_bytecode=True
sys.path.insert(0,sys.argv[1])
def deny(*a,**k):raise RuntimeError('Synthetic mutation process: network denied')
socket.socket.connect=socket.socket.connect_ex=socket.socket.sendto=deny
socket.create_connection=socket.getaddrinfo=deny
out=[]
for spec in json.loads(sys.argv[2]):
    parts=spec.split(':');mod=importlib.import_module(parts[0])
    try:
        if len(parts)==3:getattr(mod,parts[1])(parts[2]).debug()
        else:getattr(mod,parts[1])()
    except (AssertionError,ValueError,TypeError,IndexError,KeyError,StopIteration) as e:
        out.append(dict(case=spec,caught=True,error=type(e).__name__))
    else:out.append(dict(case=spec,caught=False))
print(json.dumps(out))
'''
def run(folder,cases):
    r=subprocess.run([sys.executable,'-X','utf8','-B','-c',DRIVER,str(folder),json.dumps(cases)],capture_output=True,text=True,encoding='utf-8')
    assert r.returncode==0,(r.stdout,r.stderr)
    return json.loads(r.stdout)
def main(output):
    output=Path(output).resolve();assert not output.exists()
    output.mkdir(parents=True)
    sys.path.insert(0,str(ROOT/'engine'))
    import test_um2_native as n,test_um2_causal as c,test_cash_observable as b,unittest
    cases=[f'test_um2_native:{cls.__name__}:{name}' for cls in (n.Gates,n.M5Tests)
           for name in unittest.defaultTestLoader.getTestCaseNames(cls)]
    cases += [f'{mod.__name__}:{name}' for mod in (c,b) for name in dir(mod) if name.startswith('test_')]
    assert len(cases)==34
    assert not any(x['caught'] for x in run(ROOT/'engine',cases))
    faults=[
        ('unknown_accepted','liquidation_evidence.py','    return not unknown','    return True'),
        ('all_liquidation_confirmations_lost','liquidation_evidence.py',
         'def known(points, fields, reason, side, decision_at):','def known(points, fields, reason, side, decision_at):\n    return False'),
        ('observed_zero_lost','flow_contract.py','return math.isfinite(value) and value >= 0','return math.isfinite(value) and value > 0'),
        ('blanket_unknown_neutral','strategy_core.py','    c, f = candles[-window:], flow[-window:]',
         '    c, f = candles[-window:], flow[-window:]\n    if not all(__import__("flow_contract").liquidation_usable(p,"long_liq") for p in f): return Pattern.NEUTRAL'),
        ('invisible_buy_executed','execution_v1.py','if quantity <= 0 or self.units + quantity == self.units:','if False:'),
        ('real_small_buy_blocked','execution_v1.py','if quantity <= 0 or self.units + quantity == self.units:','if True:'),
        ('warmup_traded','execution_v1.py','        if c.ts<start_ms:','        if False:'),
        ('confirm_prefix_extended','execution_v1.py','sc._evaluate(self.candles, self.flow, result, **self.params,',
         'sc._evaluate(self.candles + [self.candles[-1]], self.flow, result, **self.params,'),
        ('diagnostic_context_not_restored','liquidation_evidence.py','        _events.reset(token)','        pass'),
        ('side_provenance_assumed_valid','flow_contract.py','def liquidation_usable(point, field):',
         'def liquidation_usable(point, field):\n    return True'),
    ]
    remaining=set(cases);coverage={};results=[]
    for label,file,old,new in faults:
        folder=output/label;folder.mkdir()
        for p in (ROOT/'engine').glob('*.py'):shutil.copyfile(p,folder/p.name)
        p=folder/file;s=p.read_text(encoding='utf-8');assert s.count(old)==1,(label,s.count(old))
        p.write_text(s.replace(old,new),encoding='utf-8')
        rows=run(folder,sorted(remaining))
        caught=[x['case'] for x in rows if x['caught']]
        for case in caught:coverage[case]=label
        remaining-=set(caught)
        results.append(dict(fault=label,cases_checked=len(rows),caught=caught))
    assert not remaining,sorted(remaining)
    proof=dict(passed=True,new_cases=34,all_baselines_passed=True,all_new_cases_killed=True,
        coverage=coverage,faults=results,historical_strategy_runs=0,
        note='Each mutation uses separately copied engine/test source; only synthetic cases run. No native engine function is replaced in the integration working tree.')
    (output/'RESULT.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':main(sys.argv[1])
