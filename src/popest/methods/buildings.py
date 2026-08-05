"""Method: Building footprints population estimate.

P = Total_Buildings × Residential_Fraction × Occupancy × Persons_per_Household
"""

import pandas as pd

from popest.buildings import fetch_building_counts_by_state

RESIDENTIAL_FRACTION = 0.72
OCCUPANCY_RATE = 0.87
PERSONS_PER_HOUSEHOLD = 2.6


def estimate() -> pd.DataFrame:
    """State-level population from building footprint counts."""
    counts = fetch_building_counts_by_state()
    if counts.empty:
        return pd.DataFrame()

    for label, res_frac, occ, pph in [
        ("central", RESIDENTIAL_FRACTION, OCCUPANCY_RATE, PERSONS_PER_HOUSEHOLD),
        ("low", 0.78, 0.90, 2.4),
        ("high", 0.66, 0.84, 2.8),
    ]:
        counts[f"pop_buildings_{label}"] = (
            counts["buildings"] * res_frac * occ * pph
        )

    return counts


def national_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    return {
        "states": len(df),
        "total_buildings": int(df["buildings"].sum()),
        "central": float(df["pop_buildings_central"].sum()),
        "low": float(df["pop_buildings_low"].sum()),
        "high": float(df["pop_buildings_high"].sum()),
    }
