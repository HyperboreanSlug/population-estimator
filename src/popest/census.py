"""Phase 4: Housing and census data client.

Fetches census housing units and population for comparison.
Falls back to hardcoded national totals if no API key.
"""

import pandas as pd
import requests

CENSUS_API_BASE = "https://api.census.gov/data"

CENSUS_2020_NATIONAL = {
    "total_population": 331_449_281,
    "total_housing_units": 140_498_736,
    "source": "2020 Decennial Census P.L. 94-171",
}


def fetch_census_population_2020(api_key: str | None = None) -> pd.DataFrame:
    """Fetch 2020 decennial census population by county."""
    if not api_key:
        return pd.DataFrame([{
            "fips": "00000",
            "county_name": "UNITED STATES (national total)",
            "census_pop_2020": CENSUS_2020_NATIONAL["total_population"],
        }])

    url = (
        f"{CENSUS_API_BASE}/2020/dec/pl"
        f"?get=NAME,P1_001N&for=county:*&key={api_key}"
    )
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    headers = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=headers)
    df["P1_001N"] = pd.to_numeric(df["P1_001N"], errors="coerce")
    df["fips"] = df["state"] + df["county"]
    df = df.rename(columns={"P1_001N": "census_pop_2020", "NAME": "county_name"})
    df = df[~df["fips"].str.startswith("72")].copy()
    return df[["fips", "county_name", "census_pop_2020"]].reset_index(drop=True)


def fetch_census_housing_2020(api_key: str | None = None) -> pd.DataFrame:
    """Fetch 2020 census housing units by county."""
    if not api_key:
        return pd.DataFrame([{
            "fips": "00000",
            "housing_units_2020": CENSUS_2020_NATIONAL["total_housing_units"],
        }])

    url = (
        f"{CENSUS_API_BASE}/2020/dec/pl"
        f"?get=NAME,H1_001N&for=county:*&key={api_key}"
    )
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    headers = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=headers)
    df["H1_001N"] = pd.to_numeric(df["H1_001N"], errors="coerce")
    df["fips"] = df["state"] + df["county"]
    df = df.rename(columns={"H1_001N": "housing_units_2020"})
    df = df[~df["fips"].str.startswith("72")].copy()
    return df[["fips", "housing_units_2020"]].reset_index(drop=True)
