"""Ensemble combination of all methods.

National: precision-style fixed weights (physical/biological methods get
the bulk; census is capped). County: available-method weighted mean with
per-county contributions and range endpoints. State: county rollup.

The census cap follows PLAN.md: census is one input, never the anchor,
capped at 15% of ensemble weight regardless of its internal precision.
"""

import numpy as np
import pandas as pd

METHOD_WEIGHTS = {
    "water": 0.16,
    "wastewater": 0.13,
    "energy": 0.06,
    "msw": 0.05,
    "gasoline": 0.04,
    "vehicles": 0.04,
    "healthcare": 0.06,
    "housing": 0.07,
    "vitals": 0.05,
    "buildings": 0.06,
    "snap": 0.03,
    "wireless": 0.03,
    "grocery": 0.03,
    "irs": 0.08,
    "bls": 0.05,
}

CENSUS_WEIGHT_CAP = 0.15

# wastewater_chem is REPORTED but never ensemble-weighted: its numerator
# (municipal plants that report mass-unit loads) is a reporting subset,
# not a national total, so it is a coverage-limited lower bound.
COUNTY_WEIGHTS = {
    "water": 0.30,
    "wastewater": 0.20,
    "housing": 0.20,
    "census": 0.15,
}


def combine_national(estimates: dict[str, float],
                     census: float | None = None) -> dict:
    """Weighted national combination with the census weight cap."""
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
        census_w = (min(CENSUS_WEIGHT_CAP, 1.0 - total_weight)
                    if total_weight < 1.0 else CENSUS_WEIGHT_CAP)
        weighted_sum += census * census_w
        total_weight += census_w
        contributions["census"] = {"value": census, "weight": census_w}

    if total_weight == 0:
        return {"combined": 0.0, "total_weight": 0.0, "contributions": {}}

    combined = weighted_sum / total_weight
    for m in contributions:
        contributions[m]["weighted_share"] = (
            contributions[m]["weight"] / total_weight)
    return {
        "combined": combined,
        "total_weight": total_weight,
        "contributions": contributions,
    }


def combine_county(method_dfs: dict[str, pd.DataFrame],
                   census_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """County-level ensemble across available methods.

    Args:
        method_dfs: method name -> DataFrame with columns
            [fips, <central>, <low>, <high>] where the three value
            columns are named pop_<method>_{central,low,high}.
        census_df: DataFrame [fips, census_pop_2020] (comparison input,
            capped weight).

    Returns DataFrame indexed by fips with per-method populations, the
    weighted ensemble with renormalization over present methods, range
    endpoints, and per-method weighted-share contributions. Counties
    with no method data keep an estimate of 0 and n_methods 0 (never
    invented).
    """
    frames = []
    for name, df in method_dfs.items():
        if df is None or df.empty:
            continue
        keep = df[[c for c in ["fips", f"pop_{name}_central",
                               f"pop_{name}_low", f"pop_{name}_high"]
                   if c in df.columns]].copy()
        frames.append(keep)
    if census_df is not None and not census_df.empty:
        census_df = census_df.copy()
        census_df["pop_census_high"] = census_df["census_pop"]
        census_df["pop_census_low"] = census_df["census_pop"]
        census_df = census_df.rename(
            columns={"census_pop": "pop_census_central"})
        frames.append(census_df[["fips", "pop_census_central",
                                 "pop_census_low", "pop_census_high"]])

    if not frames:
        return pd.DataFrame(columns=["fips", "ensemble_pop"])

    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(f, on="fips", how="outer")

    # National fallback rows (fips 00000) and stray codes are not
    # counties; drop them so national totals never pose as counties.
    from popest.geo import is_valid_county_fips

    merged = merged[merged["fips"].astype(str).str.zfill(5)
                    .apply(is_valid_county_fips)].copy()
    merged["fips"] = merged["fips"].astype(str).str.zfill(5)

    methods = [m for m in COUNTY_WEIGHTS
               if f"pop_{m}_central" in merged.columns]
    merged["ensemble_pop"] = 0.0
    merged["ensemble_low"] = 0.0
    merged["ensemble_high"] = 0.0
    merged["n_methods"] = 0
    merged["total_w"] = 0.0
    for m in methods:
        central = merged[f"pop_{m}_central"].fillna(0.0)
        low = merged[f"pop_{m}_low"].fillna(0.0)
        high = merged[f"pop_{m}_high"].fillna(0.0)
        has = merged[f"pop_{m}_central"].notna() & (central > 0)
        w = COUNTY_WEIGHTS[m]
        merged["ensemble_pop"] += central * w * has
        merged["ensemble_low"] += low * w * has
        merged["ensemble_high"] += high * w * has
        merged["n_methods"] += has.astype(int)
        merged["total_w"] += w * has

    # contributions are shares of the FINAL weight total, so they sum
    # to 1 wherever at least one method is present
    for m in methods:
        central = merged[f"pop_{m}_central"].fillna(0.0)
        has = merged[f"pop_{m}_central"].notna() & (central > 0)
        w = COUNTY_WEIGHTS[m]
        merged[f"contrib_{m}"] = np.where(
            merged["total_w"] > 0, w * has / merged["total_w"], 0.0)

    valid = merged["total_w"] > 0
    for col in ["ensemble_pop", "ensemble_low", "ensemble_high"]:
        merged[col] = np.where(valid, merged[col] / merged["total_w"], 0.0)

    return merged


def state_rollup(county_df: pd.DataFrame) -> pd.DataFrame:
    """Sum county ensemble values to state totals with coverage counts."""
    if county_df.empty or "fips" not in county_df.columns:
        return pd.DataFrame()
    work = county_df.copy()
    work["state_fips"] = work["fips"].astype(str).str.zfill(5).str[:2]
    has_data = work["n_methods"] > 0
    grouped = work[has_data].groupby("state_fips", as_index=False).agg(
        ensemble_pop=("ensemble_pop", "sum"),
        ensemble_low=("ensemble_low", "sum"),
        ensemble_high=("ensemble_high", "sum"),
        counties_covered=("fips", "count"),
    )
    return grouped
