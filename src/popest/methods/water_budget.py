"""Method A: Water Budget population estimate.

Uses USGS county-level public supply and domestic self-supplied
withdrawal data. Applies independent per-capita constants to derive
population, then compares to USGS's own population figures.

P = (PS_withdrawals × residential_fraction) / per_capita_ps
  + dom_withdrawals / per_capita_domestic
"""

import numpy as np
import pandas as pd

from popest.constants import (
    GAL_PER_MGAL,
    WATER_USE_DOMESTIC_SELF_SUPPLIED,
    WATER_USE_PUBLIC_SUPPLY_TOTAL,
)
from popest.geo import is_valid_county_fips


def estimate(df: pd.DataFrame) -> pd.DataFrame:
    """Produce county-level population estimates from water use.

    Input: DataFrame from water.fetch_water_use_2015()
    Returns DataFrame with population estimates and comparisons.
    """
    work = df[df["fips"].apply(is_valid_county_fips)].copy()

    for label, ps_pc, dom_pc in [
        ("central", WATER_USE_PUBLIC_SUPPLY_TOTAL.central,
         WATER_USE_DOMESTIC_SELF_SUPPLIED.central),
        ("low_pop", WATER_USE_PUBLIC_SUPPLY_TOTAL.high,
         WATER_USE_DOMESTIC_SELF_SUPPLIED.high),
        ("high_pop", WATER_USE_PUBLIC_SUPPLY_TOTAL.low,
         WATER_USE_DOMESTIC_SELF_SUPPLIED.low),
    ]:
        ps_gal = work["ps_withdrawals_mgal_d"] * GAL_PER_MGAL
        dom_gal = work["dom_withdrawals_mgal_d"] * GAL_PER_MGAL
        pop_ps = ps_gal / ps_pc
        pop_dom = dom_gal / dom_pc
        work[f"pop_{label}"] = pop_ps + pop_dom

    work["pop_usgs"] = (
        work["ps_pop_thousands"] + work["dom_pop_thousands"]
    ) * 1000.0

    work["usgs_implied_ps_gpcd"] = np.where(
        work["ps_pop_thousands"] > 0,
        (work["ps_withdrawals_mgal_d"] * GAL_PER_MGAL)
        / (work["ps_pop_thousands"] * 1000.0),
        0.0,
    )

    cols = [
        "fips", "state", "county", "year",
        "pop_central", "pop_low_pop", "pop_high_pop", "pop_usgs",
        "ps_withdrawals_mgal_d", "dom_withdrawals_mgal_d",
        "usgs_implied_ps_gpcd",
    ]
    return work[cols].reset_index(drop=True)


def national_summary(df: pd.DataFrame) -> dict:
    """Sum county estimates to national totals."""
    if df.empty:
        return {}
    return {
        "counties": len(df),
        "central": float(df["pop_central"].sum()),
        "low_pop": float(df["pop_low_pop"].sum()),
        "high_pop": float(df["pop_high_pop"].sum()),
        "usgs_official": float(df["pop_usgs"].sum()),
        "total_ps_mgal_d": float(df["ps_withdrawals_mgal_d"].sum()),
        "total_dom_mgal_d": float(df["dom_withdrawals_mgal_d"].sum()),
        "avg_usgs_implied_gpcd": float(
            df.loc[df["usgs_implied_ps_gpcd"] > 0, "usgs_implied_ps_gpcd"].mean()
        ),
    }
