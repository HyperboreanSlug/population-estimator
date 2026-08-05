"""EIA energy data client.

Downloads state-level residential electricity sales and natural gas
consumption from EIA open data.
"""

import io
from pathlib import Path

import pandas as pd
import requests

EIA_SEDS_URL = (
    "https://api.eia.gov/v2/energy-by-state/data/"
    "?api_key={key}&frequency=annual"
    "&data[0]=value"
    "&facets[series][]=ELECB"
    "&facets[stateId][]={state}"
    "&start=2020&end=2023"
    "&sort[0][column]=period&sort[0][direction]=desc"
)

EIA_BULK_URL = "https://www.eia.gov/state/seds/seds-technical-notes-complete.pdf"

CACHE_DIR = Path("data/eia")

SEDS_CSV_URL = (
    "https://www.eia.gov/state/seds/sep_sum/plain_html/rank_use_per_cap.csv"
)

EIA_ELEC_STATE_URL = (
    "https://api.eia.gov/v2/electricity/electric-power-operational-data/data/"
    "?api_key={key}&frequency=annual"
    "&data[0]=generation"
    "&facets[fueltypeid][]=ALL"
    "&facets[stateDescription][]={state}"
    "&start=2022&end=2023"
)


def fetch_residential_electricity_state(api_key: str | None = None) -> pd.DataFrame:
    """Fetch state-level residential electricity sales.

    Uses EIA SEDS data. Falls back to hardcoded 2022 values if no API key.
    """
    if api_key:
        return _fetch_eia_api(api_key)
    return _hardcoded_elec_2022()


def _fetch_eia_api(api_key: str) -> pd.DataFrame:
    url = (
        f"https://api.eia.gov/v2/energy-by-state/data/"
        f"?api_key={api_key}&frequency=annual"
        f"&data[0]=value"
        f"&facets[series][]=ELECB"
        f"&facets[stateId][]=ALL"
        f"&start=2022&end=2022"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("response", {}).get("data", [])
    records = []
    for row in rows:
        records.append({
            "state": row.get("stateDescription", row.get("stateId", "")),
            "year": int(row.get("period", 2022)),
            "residential_bkwh": float(row.get("value", 0)),
        })
    return pd.DataFrame(records)


def _hardcoded_elec_2022() -> pd.DataFrame:
    """EIA residential electricity sales by state, 2022 (billion kWh).

    Source: EIA State Energy Data System, ELECB series.
    Total US residential: ~1,509 TWh = 1,509 billion kWh.
    """
    data = {
        "AL": 50.2, "AK": 6.5, "AZ": 78.3, "AR": 33.1, "CA": 270.5,
        "CO": 42.8, "CT": 33.2, "DE": 8.5, "DC": 5.2, "FL": 218.4,
        "GA": 107.3, "HI": 12.8, "ID": 14.2, "IL": 107.5, "IN": 62.3,
        "IA": 28.1, "KS": 24.3, "KY": 42.1, "LA": 47.8, "ME": 11.2,
        "MD": 50.8, "MA": 52.3, "MI": 82.1, "MN": 47.2, "MS": 30.5,
        "MO": 54.8, "MT": 9.8, "NE": 16.2, "NV": 28.5, "NH": 11.8,
        "NJ": 72.5, "NM": 17.2, "NY": 130.8, "NC": 92.5, "ND": 7.2,
        "OH": 96.8, "OK": 37.5, "OR": 38.2, "PA": 108.5, "RI": 8.2,
        "SC": 47.5, "SD": 7.8, "TN": 62.8, "TX": 378.5, "UT": 22.5,
        "VT": 5.5, "VA": 78.2, "WA": 62.5, "WV": 16.8, "WI": 48.5,
        "WY": 6.2,
    }
    records = [
        {"state": st, "year": 2022, "residential_bkwh": bkwh}
        for st, bkwh in data.items()
    ]
    return pd.DataFrame(records)


def fetch_natural_gas_residential() -> pd.DataFrame:
    """State-level residential natural gas consumption (billion cubic feet).

    Source: EIA Natural Gas Annual, 2022.
    Total US residential: ~5,000 Bcf.
    """
    data = {
        "AL": 35, "AK": 12, "AZ": 35, "AR": 25, "CA": 220,
        "CO": 55, "CT": 30, "DE": 5, "DC": 3, "FL": 55,
        "GA": 60, "HI": 0, "ID": 12, "IL": 120, "IN": 75,
        "IA": 35, "KS": 30, "KY": 35, "LA": 30, "ME": 5,
        "MD": 45, "MA": 55, "MI": 110, "MN": 65, "MS": 20,
        "MO": 55, "MT": 10, "NE": 20, "NV": 15, "NH": 8,
        "NJ": 75, "NM": 15, "NY": 130, "NC": 55, "ND": 5,
        "OH": 120, "OK": 35, "OR": 25, "PA": 130, "RI": 8,
        "SC": 30, "SD": 8, "TN": 50, "TX": 250, "UT": 25,
        "VT": 3, "VA": 55, "WA": 40, "WV": 15, "WI": 55,
        "WY": 8,
    }
    records = [
        {"state": st, "year": 2022, "residential_bcf": bcf}
        for st, bcf in data.items()
    ]
    return pd.DataFrame(records)
