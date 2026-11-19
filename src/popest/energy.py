"""EIA SEDS energy data client.

State-level residential electricity and natural gas consumption from the
EIA State Energy Data System complete file.

Series (SEDS MSN codes):
    ESRCP = electricity sales to ultimate customers, residential
            sector, million kWh
    NGRCP = natural gas delivered to the residential sector,
            million cubic feet

Source file: data/eia/Complete_SEDS.csv (downloaded via
https://www.eia.gov/state/seds/CDF/Complete_SEDS.csv, Vintage 2024F).
"""

from pathlib import Path

import pandas as pd

SEDS_COMPLETE = Path("data/eia/Complete_SEDS.csv")

ELEC_SERIES = "ESRCP"
GAS_SERIES = "NGRCP"

NON_STATE_CODES = {"US", "X3", "X5"}


def total_primary_energy() -> dict:
    """Total US primary energy consumption, latest annual.

    Source: data/eia/total_energy_monthly.csv (EIA MER Table 1.1).
    Annual rows have YYYYMM ending in 13.
    """
    path = Path("data/eia/total_energy_monthly.csv")
    if not path.exists():
        return {}
    df = pd.read_csv(path, dtype={"YYYYMM": str})
    annual = df[df["YYYYMM"].str.endswith("13")].copy()
    if annual.empty:
        return {}
    latest = annual["YYYYMM"].max()
    cons = annual[(annual["YYYYMM"] == latest)
                  & annual["Description"].str.contains(
                      "Total Primary Energy Consumption", na=False)]
    if cons.empty:
        return {}
    return {
        "year": int(latest[:4]),
        "quad_btu": float(cons["Value"].iloc[0]),
        "source": "data/eia/total_energy_monthly.csv (MER Table 1.1, "
                  "Total Primary Energy Consumption, annual)",
    }


def _fetch_series(msn: str, year: int | None,
                  value_col: str) -> pd.DataFrame:
    """Read one SEDS series per state. Returns [state, year, value]."""
    if not SEDS_COMPLETE.exists():
        return pd.DataFrame(columns=["state", "year", value_col])

    df = pd.read_csv(SEDS_COMPLETE, low_memory=False,
                     usecols=["MSN", "StateCode", "Year", "Data"])
    sub = df[(df["MSN"] == msn) & (~df["StateCode"].isin(NON_STATE_CODES))]
    sub = sub.copy()
    if year is None:
        year = int(sub["Year"].max())
    sub = sub[sub["Year"] == year]
    if sub.empty:
        return pd.DataFrame(columns=["state", "year", value_col])

    out = pd.DataFrame({
        "state": sub["StateCode"].str.strip(),
        "year": year,
        value_col: pd.to_numeric(sub["Data"], errors="coerce"),
    })
    return out.dropna(subset=[value_col]).reset_index(drop=True)


def fetch_residential_electricity_state(year: int | None = None) -> pd.DataFrame:
    """State-level residential electricity consumption (billion kWh).

    ESRCP is in million kWh; converted here to billion kWh.
    """
    df = _fetch_series(ELEC_SERIES, year, "residential_bkwh")
    if not df.empty:
        df["residential_bkwh"] = df["residential_bkwh"] / 1000.0
    return df


def fetch_natural_gas_residential(year: int | None = None) -> pd.DataFrame:
    """State-level residential natural gas consumption (billion cubic feet).

    NGRCP is in million cubic feet; converted here to billion cubic feet.
    """
    df = _fetch_series(GAS_SERIES, year, "residential_bcf")
    if not df.empty:
        df["residential_bcf"] = df["residential_bcf"] / 1000.0
    return df
