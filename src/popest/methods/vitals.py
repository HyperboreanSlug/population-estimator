"""Method: Vital statistics population estimate.

P = Total_Births / Crude_Birth_Rate
P = Total_Deaths / Crude_Death_Rate
"""

import pandas as pd

from popest.vitals import national_births_2022, national_deaths_2022

BIRTH_RATE_CENTRAL = 11.0
BIRTH_RATE_LOW = 9.5
BIRTH_RATE_HIGH = 13.0

DEATH_RATE_CENTRAL = 10.0
DEATH_RATE_LOW = 8.5
DEATH_RATE_HIGH = 12.0


def estimate() -> dict:
    """National population from vital statistics."""
    births = national_births_2022()
    deaths = national_deaths_2022()
    results = {}

    for label, rate in [("central", BIRTH_RATE_CENTRAL),
                        ("low", BIRTH_RATE_HIGH),
                        ("high", BIRTH_RATE_LOW)]:
        results[f"births_{label}"] = births / (rate / 1000.0)

    for label, rate in [("central", DEATH_RATE_CENTRAL),
                        ("low", DEATH_RATE_HIGH),
                        ("high", DEATH_RATE_LOW)]:
        results[f"deaths_{label}"] = deaths / (rate / 1000.0)

    return results
