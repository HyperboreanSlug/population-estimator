"""Method B: Wastewater flow population estimate.

P = Total_Municipal_WWTP_Design_Flow / Per_Capita_Wastewater_Flow

Uses EPA NPDES permitted/design flow for municipal wastewater
treatment plants. Design flow represents the capacity engineered
for the population served.
"""

import pandas as pd

from popest.constants import MGD_TO_GAL_DAY, WASTEWATER_FLOW
from popest.geo import is_valid_county_fips


def estimate(flow_df: pd.DataFrame) -> pd.DataFrame:
    """Produce county-level population estimates from WWTP design flow.

    Input: DataFrame with columns [fips, design_flow_mgd]
    Returns DataFrame with population estimates.
    """
    if flow_df.empty:
        return pd.DataFrame(
            columns=["fips", "pop_ww_central", "pop_ww_low", "pop_ww_high"]
        )

    grouped = flow_df.groupby("fips", as_index=False)["design_flow_mgd"].sum()
    grouped = grouped[grouped["fips"].apply(is_valid_county_fips)].copy()

    for label, pc in [
        ("central", WASTEWATER_FLOW.central),
        ("low", WASTEWATER_FLOW.high),
        ("high", WASTEWATER_FLOW.low),
    ]:
        gal_day = grouped["design_flow_mgd"] * MGD_TO_GAL_DAY
        grouped[f"pop_ww_{label}"] = gal_day / pc

    return grouped[["fips", "pop_ww_central", "pop_ww_low", "pop_ww_high"]].reset_index(drop=True)


def national_summary(df: pd.DataFrame) -> dict:
    """Sum county estimates to national totals."""
    if df.empty:
        return {}
    return {
        "counties": len(df),
        "central": float(df["pop_ww_central"].sum()),
        "low": float(df["pop_ww_low"].sum()),
        "high": float(df["pop_ww_high"].sum()),
    }
