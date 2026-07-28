"""EPA NPDES wastewater data client.

Downloads ICIS-NPDES facility data from EPA ECHO bulk downloads.
Uses design/permitted flow from municipal WWTPs to estimate population.
"""

import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

NPDES_PART1_URL = "https://echo.epa.gov/files/echodownloads/npdes_downloads.zip"
CACHE_DIR = Path("data/epa")


def download_npdes_part1(use_cache: bool = True) -> Path:
    """Download ICIS-NPDES Part 1 ZIP (301 MB). Returns path to ZIP."""
    cache_path = CACHE_DIR / "npdes_downloads.zip"
    if use_cache and cache_path.exists():
        return cache_path
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    print("  Downloading ICIS-NPDES Part 1 (~301 MB)...")
    resp = requests.get(NPDES_PART1_URL, timeout=600, stream=True)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(cache_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded / total * 100
                print(f"\r  {downloaded // (1024*1024)} MB / {total // (1024*1024)} MB ({pct:.0f}%)", end="", flush=True)
    print()
    return cache_path


def load_npdes_facilities(zip_path: Path) -> pd.DataFrame:
    """Extract and load facility/permit data from NPDES ZIP."""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        fac_file = _find_file(names, ["PROGRAM", "facility", "FACILITY"])
        permit_file = _find_file(names, ["PERMIT", "permit"])

        if fac_file:
            with zf.open(fac_file) as f:
                fac_df = pd.read_csv(f, dtype=str, low_memory=False)
        else:
            fac_df = pd.DataFrame()

        if permit_file:
            with zf.open(permit_file) as f:
                permit_df = pd.read_csv(f, dtype=str, low_memory=False)
        else:
            permit_df = pd.DataFrame()

    return fac_df, permit_df, names


def _find_file(names: list[str], keywords: list[str]) -> str | None:
    for name in names:
        upper = name.upper()
        if upper.endswith(".CSV") or upper.endswith(".TXT"):
            for kw in keywords:
                if kw in upper:
                    return name
    return None


def extract_municipal_wwtps(
    fac_df: pd.DataFrame,
    permit_df: pd.DataFrame,
) -> pd.DataFrame:
    """Filter for municipal wastewater treatment plants.

    Identifies facilities with SIC 4952 (Sewerage Systems) or
    NAICS 221320 (Sewage Treatment Facilities).
    """
    result = fac_df.copy()

    sic_col = _find_col(result, ["SIC", "PRIMARY_SIC", "SIC_CODE"])
    naics_col = _find_col(result, ["NAICS", "PRIMARY_NAICS", "NAICS_CODE"])

    mask = pd.Series(False, index=result.index)
    if sic_col:
        mask |= result[sic_col].astype(str).str.strip() == "4952"
    if naics_col:
        mask |= result[naics_col].astype(str).str.strip() == "221320"

    if not mask.any() and permit_df is not None and not permit_df.empty:
        return _extract_from_permits(permit_df)

    return result[mask].copy()


def _extract_from_permits(permit_df: pd.DataFrame) -> pd.DataFrame:
    """Fallback: identify municipal WWTPs from permit data."""
    result = permit_df.copy()
    type_col = _find_col(result, ["PERMIT_TYPE", "TYPE", "FACILITY_TYPE"])
    if type_col:
        mask = result[type_col].astype(str).str.contains(
            "MUNICIPAL|POTW|SEWAGE|WWTP|WASTEWATER",
            case=False, na=False,
        )
        return result[mask].copy()
    return result


def get_design_flow(wwtp_df: pd.DataFrame, permit_df: pd.DataFrame) -> pd.DataFrame:
    """Extract design flow (MGD) for municipal WWTPs."""
    flow_col = _find_col(permit_df, [
        "DESIGN_FLOW", "PERMITTED_FLOW", "FLOW", "AVG_FLOW",
        "DESIGN_FLOW_MGD", "PERMIT_FLOW",
    ])
    if flow_col is None:
        return pd.DataFrame(columns=["fips", "design_flow_mgd"])

    result = permit_df.copy()
    result["design_flow_mgd"] = pd.to_numeric(
        result[flow_col].replace("--", "").replace("", "0"),
        errors="coerce",
    ).fillna(0.0)

    fips_col = _find_col(result, ["COUNTY_FIPS", "FIPS", "COUNTY_CODE"])
    state_col = _find_col(result, ["STATE_FIPS", "STATE", "STATE_CODE"])

    if fips_col and state_col:
        result["fips"] = (
            result[state_col].astype(str).str.strip().str.zfill(2)
            + result[fips_col].astype(str).str.strip().str.zfill(3)
        )
    else:
        result["fips"] = "00000"

    result = result[result["design_flow_mgd"] > 0]
    return result[["fips", "design_flow_mgd"]].copy()


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols_upper = {c.upper(): c for c in df.columns}
    for cand in candidates:
        if cand.upper() in cols_upper:
            return cols_upper[cand.upper()]
    for cand in candidates:
        for col_u, col in cols_upper.items():
            if cand in col_u:
                return col
    return None
