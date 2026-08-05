"""Phase 6: Ensemble combination of all methods.

Precision-weighted combination with census capped at 15%.
Physical/biological methods get 85% of weight.
"""

import numpy as np
import pandas as pd


METHOD_WEIGHTS = {
    "water": 0.18,
    "wastewater": 0.15,
    "energy": 0.07,
    "msw": 0.05,
    "gasoline": 0.05,
    "vehicles": 0.04,
    "healthcare": 0.07,
    "housing": 0.08,
    "vitals": 0.06,
    "buildings": 0.08,
    "snap": 0.03,
    "wireless": 0.04,
    "grocery": 0.04,
    "irs": 0.06,
}

CENSUS_WEIGHT_CAP = 0.15


def combine_national(estimates: dict[str, float], census: float | None = None) -> dict:
    """Combine national-level estimates from all methods.

    Args:
        estimates: dict mapping method name -> central estimate
        census: census official count (capped at 15% weight)

    Returns dict with combined estimate and metadata.
    """
    weighted_sum = 0.0
    total_weight = 0.0
    contributions = {}

    for method, value in estimates.items():
        if value <= 0:
            continue
        w = METHOD_WEIGHTS.get(method, 0.05)
        weighted_sum += value * w
        total_weight += w
        contributions[method] = {"value": value, "weight": w}

    if census and census > 0:
        census_w = min(CENSUS_WEIGHT_CAP, 1.0 - total_weight) if total_weight < 1.0 else CENSUS_WEIGHT_CAP
        weighted_sum += census * census_w
        total_weight += census_w
        contributions["census"] = {"value": census, "weight": census_w}

    if total_weight == 0:
        return {"combined": 0, "contributions": {}}

    combined = weighted_sum / total_weight

    for m in contributions:
        contributions[m]["weighted_share"] = contributions[m]["weight"] / total_weight

    return {
        "combined": combined,
        "total_weight": total_weight,
        "contributions": contributions,
    }


def combine_county(
    water_df: pd.DataFrame | None,
    wastewater_df: pd.DataFrame | None,
    housing_df: pd.DataFrame | None,
    census_df: pd.DataFrame | None,
) -> pd.DataFrame:
    """Combine county-level estimates into final ensemble.

    Merges all county-level methods and produces weighted average.
    """
    frames = []
    if water_df is not None and not water_df.empty:
        frames.append(water_df[["fips", "pop_water_central"]].rename(
            columns={"pop_water_central": "water"}))
    if wastewater_df is not None and not wastewater_df.empty:
        frames.append(wastewater_df[["fips", "pop_ww_central"]].rename(
            columns={"pop_ww_central": "wastewater"}))
    if housing_df is not None and not housing_df.empty:
        frames.append(housing_df[["fips", "pop_housing_central"]].rename(
            columns={"pop_housing_central": "housing"}))
    if census_df is not None and not census_df.empty:
        frames.append(census_df[["fips", "census_pop_2020"]].rename(
            columns={"census_pop_2020": "census"}))

    if not frames:
        return pd.DataFrame(columns=["fips", "ensemble_pop"])

    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(f, on="fips", how="outer")

    weights = {"water": 0.30, "wastewater": 0.25, "housing": 0.30, "census": 0.15}

    merged["ensemble_pop"] = 0.0
    merged["total_w"] = 0.0
    for method, w in weights.items():
        if method in merged.columns:
            vals = merged[method].fillna(0)
            has_data = merged[method].notna() & (merged[method] > 0)
            merged["ensemble_pop"] += vals * w * has_data
            merged["total_w"] += w * has_data

    merged["ensemble_pop"] = np.where(
        merged["total_w"] > 0,
        merged["ensemble_pop"] / merged["total_w"],
        0.0,
    )

    return merged[["fips", "ensemble_pop"]].copy()
