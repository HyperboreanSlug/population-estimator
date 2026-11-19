"""Census data client (comparison input, capped at 15% ensemble weight).

Two sources:
- 2020 Decennial P.L. 94-171 county counts. The API requires a key for
  the county endpoint (keyless requests return an HTML error page);
  supply one via config/sources.local.yaml or the --api-key flag. Falls
  back to the published national total.
- Census PEP Vintage 2024 county file (PLAN.md source #27): a bulk CSV
  needing no key, with POPESTIMATE2020-2024 per county. This is the
  default county-level comparison voice and the census value for the
  target year.
"""

from pathlib import Path

import pandas as pd
import requests

CENSUS_API_BASE = "https://api.census.gov/data"
PEP_COUNTY_CSV = Path("data/census/co-est2024-alldata.csv")
PEP_YEARS = [2020, 2021, 2022, 2023, 2024]

CENSUS_2020_NATIONAL = {
    "total_population": 331_449_281,
    "total_housing_units": 140_498_736,
    "source": "2020 Decennial Census P.L. 94-171",
}

TIMEOUT = 120


def fetch_census_pep_counties(year: int = 2024) -> dict:
    """County-level Census PEP population estimates (no key required).

    Returns {counties: DataFrame[fips, county_name, census_pop],
             national: float, year_used: int} or an empty-result dict
    when the PEP CSV has not been downloaded. The nearest available
    estimate year is used when the target year is outside 2020-2024.
    """
    if not PEP_COUNTY_CSV.exists():
        return {"counties": pd.DataFrame(), "national": 0.0,
                "year_used": None}

    year_used = min(PEP_YEARS, key=lambda y: abs(y - year))
    df = pd.read_csv(PEP_COUNTY_CSV, dtype={"STATE": str, "COUNTY": str},
                     encoding="latin-1", low_memory=False)
    df = df[df["SUMLEV"] == 50].copy()
    df["fips"] = df["STATE"].str.zfill(2) + df["COUNTY"].str.zfill(3)
    df = df[~df["fips"].str.startswith("72")].copy()
    df = df.rename(columns={
        f"POPESTIMATE{year_used}": "census_pop",
        "CTYNAME": "county_name",
    })
    national = float(df["census_pop"].sum())
    return {
        "counties": df[["fips", "county_name", "census_pop"]],
        "national": national,
        "year_used": year_used,
    }


def _fetch_pl(variable: str, value_col: str, api_key: str | None) -> pd.DataFrame:
    """Fetch a 2020 PL variable by county. Returns county rows or None."""
    url = f"{CENSUS_API_BASE}/2020/dec/pl?get=NAME,{variable}&for=county:*"
    if api_key:
        url += f"&key={api_key}"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return pd.DataFrame()

    headers, rows = data[0], data[1:]
    df = pd.DataFrame(rows, columns=headers)
    df[value_col] = pd.to_numeric(df[variable], errors="coerce")
    df["fips"] = df["state"] + df["county"]
    df = df[~df["fips"].str.startswith("72")].copy()
    df = df.rename(columns={"NAME": "county_name"})
    return df[["fips", "county_name", value_col]].reset_index(drop=True)


def fetch_census_population_2020(api_key: str | None = None) -> pd.DataFrame:
    """County-level 2020 census population; national fallback row."""
    df = _fetch_pl("P1_001N", "census_pop_2020", api_key)
    if not df.empty:
        return df
    return pd.DataFrame([{
        "fips": "00000",
        "county_name": "UNITED STATES (national total)",
        "census_pop_2020": CENSUS_2020_NATIONAL["total_population"],
    }])


def fetch_census_housing_2020(api_key: str | None = None) -> pd.DataFrame:
    """County-level 2020 census housing units; national fallback row."""
    df = _fetch_pl("H1_001N", "housing_units_2020", api_key)
    if not df.empty:
        return df
    return pd.DataFrame([{
        "fips": "00000",
        "housing_units_2020": CENSUS_2020_NATIONAL["total_housing_units"],
    }])
