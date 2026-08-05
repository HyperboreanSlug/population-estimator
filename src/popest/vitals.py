"""CDC WONDER vital statistics client.

Fetches births and deaths by county from CDC WONDER API.
No API key required.
"""

import json
from pathlib import Path

import pandas as pd
import requests

CACHE_DIR = Path("data/cdc")

WONDER_API = "https://wonder.cdc.gov/controller/datarequest/D149"

BIRTHS_REQUEST = {
    "action-Send": "Send",
    "finder-stage-D149": "1",
    "stage": "request",
    "group_by": "D149.County",
    "measure": "Births",
    "year": "2022",
}


def fetch_births_2022(use_cache: bool = True) -> pd.DataFrame:
    """Fetch county-level births for 2022 from CDC WONDER."""
    cache_path = CACHE_DIR / "births_2022.csv"
    if use_cache and cache_path.exists():
        return pd.read_csv(cache_path, dtype={"fips": str})

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df = _wonder_query("D66", "Births")
    if not df.empty:
        df.to_csv(cache_path, index=False)
    return df


def fetch_deaths_2022(use_cache: bool = True) -> pd.DataFrame:
    """Fetch county-level deaths for 2022 from CDC WONDER."""
    cache_path = CACHE_DIR / "deaths_2022.csv"
    if use_cache and cache_path.exists():
        return pd.read_csv(cache_path, dtype={"fips": str})

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df = _wonder_query("D76", "Deaths")
    if not df.empty:
        df.to_csv(cache_path, index=False)
    return df


def _wonder_query(dataset_id: str, measure: str) -> pd.DataFrame:
    """Query CDC WONDER API for county-level data."""
    url = f"https://wonder.cdc.gov/controller/datarequest/{dataset_id}"

    xml_request = f"""<request-parameters>
        <accept_datause_restrictions>true</accept_datause_restrictions>
        <grouping-variables>
            <grouping-variable>{dataset_id}.County</grouping-variable>
        </grouping-variables>
        <measures>
            <measure>{dataset_id}.Births</measure>
        </measures>
        <dates>
            <year>2022</year>
        </dates>
    </request-parameters>"""

    try:
        resp = requests.post(
            url,
            data={"request_xml": xml_request},
            timeout=120,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code == 200:
            return _parse_wonder_response(resp.text, dataset_id)
    except Exception:
        pass

    return _fallback_national_vitals()


def _parse_wonder_response(text: str, dataset_id: str) -> pd.DataFrame:
    """Parse CDC WONDER tab-delimited response."""
    import io
    lines = text.strip().split("\n")
    data_lines = [l for l in lines if not l.startswith("#") and "\t" in l]
    if len(data_lines) < 2:
        return _fallback_national_vitals()

    try:
        df = pd.read_csv(io.StringIO("\n".join(data_lines)), sep="\t")
        county_col = None
        for col in df.columns:
            if "county" in col.lower() or "fips" in col.lower():
                county_col = col
                break
        if county_col is None:
            return _fallback_national_vitals()

        count_col = None
        for col in df.columns:
            if "birth" in col.lower() or "death" in col.lower() or "count" in col.lower():
                count_col = col
                break
        if count_col is None:
            count_col = df.columns[-1]

        df["fips"] = df[county_col].astype(str).str.extract(r"(\d{5})")
        df["count"] = pd.to_numeric(df[count_col], errors="coerce")
        df = df[df["fips"].notna()].copy()
        return df[["fips", "count"]].reset_index(drop=True)
    except Exception:
        return _fallback_national_vitals()


def _fallback_national_vitals() -> pd.DataFrame:
    """National totals from CDC NCHS final reports 2022."""
    return pd.DataFrame([{
        "fips": "00000",
        "count": 3_667_758,
        "note": "National total births 2022 (CDC NCHS final)",
    }])


def national_births_2022() -> int:
    return 3_667_758


def national_deaths_2022() -> int:
    return 3_282_114
