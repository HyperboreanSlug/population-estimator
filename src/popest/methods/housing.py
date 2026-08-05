"""Method G: Housing unit population estimate.

P = Housing_Units × Occupancy_Rate × Persons_per_Household + Group_Quarters
"""

import pandas as pd

from popest.census import fetch_census_housing_2020, fetch_census_population_2020

OCCUPANCY_RATE = 0.87
PERSONS_PER_HOUSEHOLD = 2.6
GQ_FRACTION = 0.025


def estimate(api_key: str | None = None) -> pd.DataFrame:
    """Produce county-level population estimates from housing units."""
    housing = fetch_census_housing_2020(api_key)
    if housing.empty:
        return pd.DataFrame()

    for label, occ, pph in [
        ("central", OCCUPANCY_RATE, PERSONS_PER_HOUSEHOLD),
        ("low", 0.90, 2.4),
        ("high", 0.84, 2.8),
    ]:
        housing[f"pop_housing_{label}"] = (
            housing["housing_units_2020"] * occ * pph
        )

    housing["gq_estimate"] = housing["housing_units_2020"] * GQ_FRACTION
    for label in ["central", "low", "high"]:
        housing[f"pop_housing_{label}"] += housing["gq_estimate"]

    cols = ["fips", "pop_housing_central", "pop_housing_low", "pop_housing_high"]
    return housing[cols].reset_index(drop=True)


def national_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    return {
        "counties": len(df),
        "central": float(df["pop_housing_central"].sum()),
        "low": float(df["pop_housing_low"].sum()),
        "high": float(df["pop_housing_high"].sum()),
    }
