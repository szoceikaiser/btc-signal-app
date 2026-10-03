"""Synthetic checks MUST pass before accessing historical return results."""
import numpy as np
from historical_stats import stationary_indices, paired_bootstrap, interval, daily_pair, DAY


def test_null_and_constant_alternatives():
    idx=stationary_indices(70,14)
    z=interval(np.zeros(70),idx)
    assert z['p_cond']==1 and z['mu_interval']==[0,0]
    for x, p in [(1/1024,1/20001),(-1/1024,1.)]:
        r=interval(np.full(70,x),idx)
        assert r['p_cond']==p and r['mu_interval']==[x,x]


def test_pairing_shared_indices_and_swap():
    t=np.arange(80)
    base=np.sin(t)/100
    a=np.column_stack((base,base+np.cos(t)/1000))
    idx=stationary_indices(80,14)
    r=paired_bootstrap(a,14,idx)
    # Independent explicit per-replicate difference of column means.
    mu=np.mean(a[:,1]-a[:,0])
    z=a[idx,1].mean(axis=1)-a[idx,0].mean(axis=1)-mu
    assert np.allclose(r['mu_interval'],[mu-np.quantile(z,.975),mu-np.quantile(z,.025)],rtol=0,atol=1e-17)
    same=paired_bootstrap(np.column_stack((base,base)),14,idx)
    assert same['mu_interval']==[0,0]
    swapped=paired_bootstrap(a[:,::-1],14,idx)
    assert np.allclose(swapped['mu_interval'],[-r['mu_interval'][1],-r['mu_interval'][0]])


def test_quantile_exact_hand_case_and_tail():
    x=np.array([0.,2.])
    idx=np.array([[0,0],[0,1],[1,0],[1,1]])
    r=interval(x,idx)
    assert np.allclose(r['mu_interval'],[.075,1.925])
    assert abs(r['lower_mu']-.15)<1e-14
    assert r['p_cond']==.4


def test_geometric_dependence_wrap_and_seed():
    idx=stationary_indices(11,14,20000)
    assert np.array_equal(idx,stationary_indices(11,14,20000))
    continued=(idx[:,1:]==(idx[:,:-1]+1)%11).mean()
    assert abs(continued-(1-1/14+1/14/11))<.004
    assert np.any((idx[:,:-1]==10)&(idx[:,1:]==0))
    assert np.max(np.abs(np.bincount(idx[:,0],minlength=11)/20000-1/11))<.012


def test_dependent_vs_iid_and_nonconstant_alternative():
    x=np.repeat([-1.,1.],100)/1000
    a=interval(x,stationary_indices(len(x),1))
    b=interval(x,stationary_indices(len(x),14))
    assert b['mu_interval'][1]-b['mu_interval'][0]>2*(a['mu_interval'][1]-a['mu_interval'][0])
    shifted=interval(x+.01,stationary_indices(len(x),14))
    assert shifted['lower_mu']>0 and shifted['p_cond']==1/20001


def test_day_boundaries_exclude_partial_and_before_fill():
    # starts at 20:00 day 0, finishes 08:00 day 3: exactly two full days.
    ts=list(range(5*DAY//6,3*DAY+DAY//3,DAY//6))
    b={'equity':[dict(candle_id=t,at=t+DAY//6,equity=100.) for t in ts]}
    k={'equity':[dict(candle_id=t,at=t+DAY//6,equity=100.+i) for i,t in enumerate(ts)]}
    a,m=daily_pair(b,k)
    assert m['n']==2 and m['start_ms']==DAY and m['end_ms']==3*DAY
    assert m['excluded_first_hours']==4 and m['excluded_last_hours']==8
    assert np.allclose(a[:,1],[np.log(106/100),np.log(112/106)])
    k['equity'][1]['at']+=1
    try: daily_pair(b,k)
    except ValueError: pass
    else: raise AssertionError('unpaired timestamps accepted')


if __name__=='__main__':
    tests=[fn for name,fn in list(globals().items()) if name.startswith('test_')]
    for fn in tests:
        fn()
        print('PASS',fn.__name__)
    print(len(tests),'synthetic checks passed; numpy',np.__version__)
