"""Method C: Energy consumption population estimate.

P = Residential_kWh_Sold / Per_Capita_Residential_kWh

State-level estimate using EIA residential electricity sales.
"""

import pandas as pd

from popest.constants import ELECTRICITY_RESIDENTIAL
from popest.energy import fetch_natural_gas_residential, fetch_residential_electricity_state
from popest.geo import STATE_ABBREV_TO_FIPS


def estimate(api_key: str | None = None) -> pd.DataFrame:
    """Produce state-level population estimates from energy consumption.

    Returns DataFrame with columns:
        state, year, pop_elec_central, pop_elec_low, pop_elec_high
    """
    elec = fetch_residential_electricity_state(api_key)
    if elec.empty:
        return pd.DataFrame()

    for label, kwh_pc in [
        ("central", ELECTRICITY_RESIDENTIAL.central),
        ("low", ELECTRICITY_RESIDENTIAL.high),
        ("high", ELECTRICITY_RESIDENTIAL.low),
    ]:
        bkwh = elec["residential_bkwh"]
        elec[f"pop_elec_{label}"] = (bkwh * 1e9) / kwh_pc

    result = elec[["state", "year", "pop_elec_central", "pop_elec_low", "pop_elec_high"]].copy()
    result["state_fips"] = result["state"].map(STATE_ABBREV_TO_FIPS)
    return result


def national_summary(df: pd.DataFrame) -> dict:
    """Sum state estimates to national totals."""
    if df.empty:
        return {}
    return {
        "states": len(df),
        "central": float(df["pop_elec_central"].sum()),
        "low": float(df["pop_elec_low"].sum()),
        "high": float(df["pop_elec_high"].sum()),
        "total_residential_bkwh": float(df["residential_bkwh"].sum()) if "residential_bkwh" in df.columns else 0,
    }
