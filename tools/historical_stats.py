"""Design v2 U1, conditional on fixed pair. NOT selection-adjusted inference."""
import numpy as np

DAY = 86_400_000


def daily_pair(basis, candidate):
    if [r['at'] for r in basis['equity']] != [r['at'] for r in candidate['equity']]:
        raise ValueError('Unpaired timestamps')
    times = [r['at'] for r in basis['equity']]
    if any(b-a != DAY//6 for a, b in zip(times, times[1:])):
        raise ValueError('Missing bars')
    indices = [i for i, t in enumerate(times) if t % DAY == 0]
    if len(indices) < 2:
        raise ValueError('At least one complete UTC day required')
    endpoints = np.array([[r['equity'][i]['equity'] for r in (basis, candidate)] for i in indices])
    if not np.isfinite(endpoints).all() or (endpoints <= 0).any():
        raise ValueError('Invalid equity')
    returns = np.log(endpoints[1:]/endpoints[:-1])
    return returns, dict(n=len(returns), start_ms=times[indices[0]], end_ms=times[indices[-1]],
        excluded_first_hours=(times[indices[0]]-basis['equity'][0]['candle_id'])/3600000,
        excluded_last_hours=(times[-1]-times[indices[-1]])/3600000,
        boundary='00:00 close before new open fills')


def stationary_indices(n, length, replicates=20000, seed=20260929):
    if n < 1 or length < 1 or replicates < 1:
        raise ValueError('Invalid bootstrap dimensions')
    rng = np.random.Generator(np.random.PCG64(seed))
    idx = np.empty((replicates, n), dtype=np.int64)
    idx[:, 0] = rng.integers(n, size=replicates)
    for j in range(1, n):
        restart = rng.random(replicates) < 1/length
        fresh = rng.integers(n, size=replicates)
        idx[:, j] = np.where(restart, fresh, (idx[:, j-1]+1) % n)
    return idx


def interval(x, indices):
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all() or indices.shape[1] != len(x):
        raise ValueError('Invalid paired differences')
    mu = float(x.mean())
    # Center first to avoid rounding noise for constant series.
    z = (x-mu)[indices].mean(axis=1)
    q025, q95, q975 = np.quantile(z, [.025, .95, .975], method='linear')
    lo, hi, lower = mu-q975, mu-q025, mu-q95
    n = len(x)
    return dict(n=n, mu=mu, A_days=float(np.expm1(n*mu)),
        mu_interval=[float(lo), float(hi)], lower_mu=float(lower),
        advantage_interval=[float(np.expm1(n*lo)), float(np.expm1(n*hi))],
        lower_advantage=float(np.expm1(n*lower)),
        p_cond=float((1+np.count_nonzero(z >= mu))/(len(z)+1)),
        selection_adjusted=False, power='unknown')


def paired_bootstrap(returns, length, indices=None):
    a = np.asarray(returns, dtype=float)
    if a.ndim != 2 or a.shape[1] != 2:
        raise ValueError('Expected paired basis/candidate columns')
    idx = stationary_indices(len(a), length) if indices is None else indices
    return dict(block_days=length, replicates=len(idx), seed=20260929,
        rng='PCG64', quantile='linear', numpy_version=np.__version__,
        **interval(a[:, 1]-a[:, 0], idx))
