"""Method: community water system coverage population estimate.

P = CWS_Population_Served / CWS_Coverage_Fraction

Utilities report estimated population served per community water
system. Summed nationally this counts people on piped community water
(~85% of the population per USGS); the remainder is on domestic wells.
"""

import pandas as pd

from popest.constants import CWS_COVERAGE_FRACTION
from popest.sdwis import cws_population_served


def estimate() -> dict:
    """National population from CWS population served."""
    served = cws_population_served()
    if served.empty:
        return {}
    total = float(served["pop_served"].sum())

    results = {}
    # low population: high coverage fraction (more of the total is
    # already counted); high population: low coverage fraction
    for label, frac in [
        ("central", CWS_COVERAGE_FRACTION.central),
        ("low", CWS_COVERAGE_FRACTION.high),
        ("high", CWS_COVERAGE_FRACTION.low),
    ]:
        results[f"sdwis_{label}"] = total / frac

    results["cws_pop_served"] = total
    results["n_systems"] = int(served["n_systems"].sum())
    return results


def national_summary(results: dict) -> dict:
    return {
        "cws_pop_served": results.get("cws_pop_served", 0.0),
        "n_systems": results.get("n_systems", 0),
        "central": results.get("sdwis_central", 0.0),
    }
