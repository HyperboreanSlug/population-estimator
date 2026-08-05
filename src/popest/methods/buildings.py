"""Method: Building footprints population estimate.

P = Total_Buildings × Residential_Fraction × Occupancy × Persons_per_Household

Uses REAL downloaded GeoJSON data. See popest.buildings for source.
"""

import pandas as pd

from popest.buildings import estimate_from_buildings, get_building_counts


def estimate() -> pd.DataFrame:
    """State-level population from building footprint counts."""
    results = estimate_from_buildings()
    counts = get_building_counts()

    rows = []
    for state, count in counts["downloaded_states"].items():
        rows.append({
            "state": state,
            "buildings": count,
            "pop_buildings_central": count * 0.72 * 0.87 * 2.6,
            "pop_buildings_low": count * 0.78 * 0.90 * 2.4,
            "pop_buildings_high": count * 0.66 * 0.84 * 2.8,
        })
    return pd.DataFrame(rows)


def national_summary(df: pd.DataFrame) -> dict:
    results = estimate_from_buildings()
    return {
        "states": len(df),
        "total_buildings": results["national_total_buildings"],
        "central": results["buildings_central"],
        "low": results["buildings_low"],
        "high": results["buildings_high"],
    }
