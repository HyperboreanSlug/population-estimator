"""USGS National Water Use data client.

Downloads county-level water use data from USGS ScienceBase releases.
Primary source: county-level data for 2015 (DOI: 10.5066/F7TB15V5).
"""

import io
from pathlib import Path

import pandas as pd
import requests

SCIENCEBASE_2015_CSV = (
    "https://www.sciencebase.gov/catalog/file/get/"
    "5af3311be4b0da30c1b245d8"
    "?f=__disk__eb%2F74%2Feb%2Feb74ebb41169c76aaf374990bd5a71cac82604c1"
)

CACHE_DIR = Path("data/usgs")


def _download(url: str, cache_path: Path) -> bytes:
    if cache_path.exists():
        return cache_path.read_bytes()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=300)
    resp.raise_for_status()
    cache_path.write_bytes(resp.content)
    return resp.content


def fetch_water_use_2015(use_cache: bool = True) -> pd.DataFrame:
    """Fetch county-level water use data for 2015 from ScienceBase.

    Returns DataFrame with columns:
        fips, state, county, year,
        ps_pop_thousands, ps_withdrawals_mgal_d,
        dom_pop_thousands, dom_withdrawals_mgal_d,
        dom_per_capita_gpd, total_pop_thousands
    """
    cache_path = CACHE_DIR / "usco2015.csv"
    if use_cache:
        raw = _download(SCIENCEBASE_2015_CSV, cache_path)
    else:
        resp = requests.get(SCIENCEBASE_2015_CSV, timeout=300)
        resp.raise_for_status()
        raw = resp.content

    df = pd.read_csv(io.BytesIO(raw), skiprows=1, dtype=str)
    df.columns = [c.strip() for c in df.columns]

    result = pd.DataFrame()
    result["fips"] = df["FIPS"].str.strip().str.zfill(5)
    result["state"] = df["STATE"].str.strip()
    result["county"] = df["COUNTY"].str.strip()
    result["year"] = 2015

    result["ps_pop_thousands"] = _to_num(df.get("PS-TOPop"))
    result["ps_withdrawals_mgal_d"] = _to_num(df.get("PS-WFrTo"))
    result["dom_pop_thousands"] = _to_num(df.get("DO-SSPop"))
    result["dom_withdrawals_mgal_d"] = _to_num(df.get("DO-WFrTo"))
    result["dom_per_capita_gpd"] = _to_num(df.get("DO-SSPCp"))
    result["total_pop_thousands"] = _to_num(df.get("TP-TotPop"))
    result["ps_dom_deliveries_mgal_d"] = _to_num(df.get("DO-PSDel"))

    result = result[result["fips"].str.len() == 5].copy()
    result = result[~result["fips"].str.startswith("72")].copy()
    return result.reset_index(drop=True)


def _to_num(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype=float)
    cleaned = series.replace("--", "").replace("", "0").str.strip()
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)
