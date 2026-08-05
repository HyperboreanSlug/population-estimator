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
    """Download ICIS-NPDES Part 1 ZIP (~332 MB). Returns path to ZIP."""
    cache_path = CACHE_DIR / "npdes_downloads.zip"
    if use_cache and cache_path.exists() and cache_path.stat().st_size > 300_000_000:
        return cache_path
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    print("  Downloading ICIS-NPDES Part 1 (~332 MB)...")
    resp = requests.get(NPDES_PART1_URL, timeout=900, stream=True)
    resp.raise_for_status()
    with open(cache_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
    return cache_path


def load_municipal_flows(zip_path: Path) -> pd.DataFrame:
    """Load municipal WWTP design flows with county FIPS.

    Joins ICIS_PERMITS (design flow) with NPDES_SICS (SIC 4952)
    and ICIS_FACILITIES (county code).
    """
    with zipfile.ZipFile(zip_path) as zf:
        print("  Loading ICIS_PERMITS...")
        with zf.open("ICIS_PERMITS.csv") as f:
            permits = pd.read_csv(f, dtype=str, low_memory=False,
                                  usecols=lambda c: c in [
                                      "ACTIVITY_ID", "EXTERNAL_PERMIT_NMBR",
                                      "TOTAL_DESIGN_FLOW_NMBR",
                                      "ACTUAL_AVERAGE_FLOW_NMBR",
                                      "PERMIT_TYPE_CODE",
                                      "PERMIT_STATUS_CODE",
                                      "MAJOR_MINOR_STATUS_FLAG",
                                  ])

        print("  Loading NPDES_SICS...")
        with zf.open("NPDES_SICS.csv") as f:
            sics = pd.read_csv(f, dtype=str, low_memory=False)

        print("  Loading ICIS_FACILITIES...")
        with zf.open("ICIS_FACILITIES.csv") as f:
            facilities = pd.read_csv(f, dtype=str, low_memory=False,
                                     usecols=lambda c: c in [
                                         "NPDES_ID", "COUNTY_CODE",
                                         "STATE_CODE", "FACILITY_NAME",
                                     ])

    print(f"  Permits: {len(permits)}, SICS: {len(sics)}, Facilities: {len(facilities)}")

    municipal_sics = sics[sics["SIC_CODE"].str.strip() == "4952"].copy()
    print(f"  SIC 4952 (Sewerage) records: {len(municipal_sics)}")

    municipal_ids = set(municipal_sics["NPDES_ID"].str.strip())

    facilities = facilities.copy()
    facilities["NPDES_ID"] = facilities["NPDES_ID"].str.strip()
    muni_fac = facilities[facilities["NPDES_ID"].isin(municipal_ids)].copy()
    print(f"  Municipal facilities matched: {len(muni_fac)}")

    permits["EXTERNAL_PERMIT_NMBR"] = permits["EXTERNAL_PERMIT_NMBR"].str.strip()
    muni_permits = permits[permits["EXTERNAL_PERMIT_NMBR"].isin(municipal_ids)].copy()
    print(f"  Municipal permits matched: {len(muni_permits)}")

    muni_permits["design_flow"] = pd.to_numeric(
        muni_permits["TOTAL_DESIGN_FLOW_NMBR"], errors="coerce"
    ).fillna(0.0)
    muni_permits["actual_flow"] = pd.to_numeric(
        muni_permits["ACTUAL_AVERAGE_FLOW_NMBR"], errors="coerce"
    ).fillna(0.0)

    # ponytail: EPA data has mixed units. Values > 100 are likely gal/day,
    # not MGD. Convert them. Then cap at 2000 MGD (largest US WWTP ~1400).
    mask_gal = muni_permits["design_flow"] > 100.0
    muni_permits.loc[mask_gal, "design_flow"] /= 1_000_000.0
    mask_gal_a = muni_permits["actual_flow"] > 100.0
    muni_permits.loc[mask_gal_a, "actual_flow"] /= 1_000_000.0
    MAX_FLOW_MGD = 2000.0
    muni_permits["design_flow"] = muni_permits["design_flow"].clip(upper=MAX_FLOW_MGD)
    muni_permits["actual_flow"] = muni_permits["actual_flow"].clip(upper=MAX_FLOW_MGD)

    muni_permits = muni_permits[muni_permits["design_flow"] > 0].copy()

    # Deduplicate: multiple permits per facility. Take max flow per NPDES_ID.
    deduped = muni_permits.groupby("EXTERNAL_PERMIT_NMBR", as_index=False).agg(
        design_flow=("design_flow", "max"),
        actual_flow=("actual_flow", "max"),
    )
    print(f"  Unique facilities with design flow > 0: {len(deduped)}")

    merged = deduped.merge(
        muni_fac[["NPDES_ID", "COUNTY_CODE", "STATE_CODE"]],
        left_on="EXTERNAL_PERMIT_NMBR",
        right_on="NPDES_ID",
        how="left",
    )

    from popest.geo import STATE_ABBREV_TO_FIPS
    merged["state_fips"] = merged["STATE_CODE"].str.strip().map(STATE_ABBREV_TO_FIPS)
    county_raw = merged["COUNTY_CODE"].str.strip()
    merged["county_fips"] = county_raw.str[-3:].str.zfill(3)
    merged["fips"] = merged["state_fips"].fillna("") + merged["county_fips"].fillna("")
    merged = merged[merged["fips"].str.len() == 5].copy()
    merged = merged[~merged["fips"].str.startswith("72")].copy()

    result = merged.groupby("fips", as_index=False).agg(
        design_flow_mgd=("design_flow", "sum"),
        actual_flow_mgd=("actual_flow", "sum"),
        n_permits=("EXTERNAL_PERMIT_NMBR", "count"),
    )
    print(f"  Counties with municipal WWTP flow: {len(result)}")
    return result
