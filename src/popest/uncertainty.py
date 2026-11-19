"""Bootstrap uncertainty for the national ensemble.

Per PLAN.md Phase 6: resample per-capita rates within their published
ranges and recombine. Each estimation method has the form

    pop = total / const   ('inverse': water, wastewater, energy, ...)
    pop = total * const   ('direct': housing, buildings, occupancy x size)

where the per-capita constant moves inside a published range [c_lo, c_hi].
The method's population endpoints are exactly

    pop_high = total / c_lo,   pop_low = total / c_hi   (inverse)
    pop_low  = total * c_lo,   pop_high = total * c_hi  (direct)

so sampling the constant uniformly and recomputing the population needs
only (pop_low, pop_high, form): with k = pop_high/pop_lo and v ~ U(0,1),

    inverse: pop = pop_low * k / (1 + (k - 1) v)
    direct:  pop = pop_low * (1 + (k - 1) v)

For multi-constant methods (water budget uses separate public-supply and
domestic constants) the endpoints combine both extremes; this sampler
walks the joint range along its diagonal rather than co-sampling the two
constants independently, which slightly narrows the tail. Single-
constant methods are sampled exactly.
"""

import numpy as np

from popest.ensemble import CENSUS_WEIGHT_CAP, METHOD_WEIGHTS

N_DRAWS_DEFAULT = 1000
SEED = 13


def bootstrap_national(methods: dict[str, dict], census: float,
                       n_draws: int = N_DRAWS_DEFAULT,
                       seed: int = SEED) -> dict:
    """Resample per-capita constants and recombine the ensemble.

    Args:
        methods: name -> {'central', 'low', 'high', 'form'} where form is
            'inverse' or 'direct' (default 'inverse').
        census: census comparison count (fixed value, capped weight).

    Returns dict with combined, lower_90, upper_90, n_draws.
    """
    rng = np.random.default_rng(seed)
    names = sorted(m for m in methods
                   if methods[m].get("central", 0) > 0
                   and methods[m].get("low", 0) > 0
                   and methods[m].get("high", 0) > 0)
    if not names:
        return {"combined": 0.0, "lower_90": 0.0, "upper_90": 0.0,
                "n_draws": 0}

    draws = np.empty((n_draws, len(names)))
    weights = np.empty(len(names))
    for j, name in enumerate(names):
        m = methods[name]
        low, high = float(m["low"]), float(m["high"])
        k = high / low if low > 0 else 1.0
        v = rng.uniform(0.0, 1.0, n_draws)
        if m.get("form", "inverse") == "direct":
            draws[:, j] = low * (1.0 + (k - 1.0) * v)
        else:
            draws[:, j] = low * k / (1.0 + (k - 1.0) * v)
        weights[j] = METHOD_WEIGHTS.get(name, 0.05)

    weighted = draws * weights
    wsum = weights.sum()
    if census > 0:
        census_w = (min(CENSUS_WEIGHT_CAP, 1.0 - wsum)
                    if wsum < 1.0 else CENSUS_WEIGHT_CAP)
        weighted = weighted.sum(axis=1) + census * census_w
        wsum = wsum + census_w
    else:
        weighted = weighted.sum(axis=1)

    combined = weighted / wsum
    return {
        "combined": float(np.mean(combined)),
        "lower_90": float(np.percentile(combined, 5)),
        "upper_90": float(np.percentile(combined, 95)),
        "n_draws": n_draws,
    }
