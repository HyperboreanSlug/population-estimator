"""Method: Vital statistics population estimate.

P = Total_Births / Crude_Birth_Rate
P = Total_Deaths / Crude_Death_Rate

Birth and death counts for the target year come from the Census PEP
county file (NCHS vital records, Census-vintage adjustments). Rates are
published per-capita constants.
"""

import pandas as pd

from popest.vitals import national_births, national_deaths

BIRTH_RATE_CENTRAL = 11.0
BIRTH_RATE_LOW = 9.5
BIRTH_RATE_HIGH = 13.0

DEATH_RATE_CENTRAL = 10.0
DEATH_RATE_LOW = 8.5
DEATH_RATE_HIGH = 12.0


def estimate(year: int = 2024) -> dict:
    """National population from vital statistics for the target year."""
    b = national_births(year)
    d = national_deaths(year)
    results = {}

    for label, rate in [("central", BIRTH_RATE_CENTRAL),
                        ("low", BIRTH_RATE_HIGH),
                        ("high", BIRTH_RATE_LOW)]:
        results[f"births_{label}"] = b["count"] / (rate / 1000.0)

    for label, rate in [("central", DEATH_RATE_CENTRAL),
                        ("low", DEATH_RATE_HIGH),
                        ("high", DEATH_RATE_LOW)]:
        results[f"deaths_{label}"] = d["count"] / (rate / 1000.0)

    results["births_count"] = b["count"]
    results["deaths_count"] = d["count"]
    results["births_source"] = b["source"]
    results["deaths_source"] = d["source"]
    results["year"] = b["year"]
    return results
