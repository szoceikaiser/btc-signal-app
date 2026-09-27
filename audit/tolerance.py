"""Isolated single-change counterfactual; production file stays untouched."""
import inspect

def corrected_simulate(module):
    source=inspect.getsource(module.simulate)
    old='                units -= sell'
    assert source.count(old)==1
    source=source.replace(old,old+'\n                if abs(units) < 1e-12:\n                    units = 0.0')
    namespace=dict(module.__dict__)
    exec(compile(source,'<audit-F09-tolerance>','exec'),namespace)
    return namespace['simulate']
