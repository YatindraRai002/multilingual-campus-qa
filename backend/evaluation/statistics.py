from __future__ import annotations

import math
import random


def percentile(values: list[float], quantile: float):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered)-1)*quantile
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high]-ordered[low])*(position-low)


def bootstrap_ci(values: list[float], *, seed=42, samples=1000, scale=100):
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    estimates = [sum(rng.choices(values, k=len(values)))/len(values)*scale for _ in range(samples)]
    return {"lower": percentile(estimates, 0.025), "upper": percentile(estimates, 0.975),
            "level": 0.95, "method": "percentile_bootstrap", "resamples": samples, "seed": seed,
            "resampling_unit": "response", "limitation": "Responses sharing a source document may be correlated."}


def ratio_bootstrap(pairs: list[tuple[float,float]], *, seed=42, samples=1000, scale=100, resampling_unit="response"):
    if len(pairs) < 2 or sum(p[1] for p in pairs) == 0:
        return None
    rng, estimates = random.Random(seed), []
    for _ in range(samples):
        selected = rng.choices(pairs, k=len(pairs))
        denominator = sum(p[1] for p in selected)
        if denominator:
            estimates.append(sum(p[0] for p in selected)/denominator*scale)
    return {"lower": percentile(estimates, .025), "upper": percentile(estimates, .975),
            "level": .95, "method": f"{resampling_unit}_clustered_ratio_bootstrap", "resamples": samples,
            "valid_resamples": len(estimates), "seed": seed, "resampling_unit": resampling_unit}
