"""EPA DMR (Discharge Monitoring Report) processing client.

Filters the EPA NPDES DMR bulk zip for human-waste load parameters and
reduces them to per-facility loads in lb/day. This is the data behind
Method B (wastewater chemistry): monitored pollutant mass leaving
municipal treatment plants, divided by per-capita metabolic contributions.

Parameters (ICIS-NPDES codes):
    00310 = BOD5          00530 = TSS
    00608 = Ammonia-N     00670 = Total Nitrogen

Source zip: data/epa/npdes_dmrs_fy2024.zip -> NPDES_DMRS_FY2024.csv
County crosswalk: data/epa/npdes_downloads.zip -> ICIS_FACILITIES.csv
"""

import zipfile
from pathlib import Path

import pandas as pd

DATA = Path("data/epa")
DMR_ZIP = DATA / "npdes_dmrs_fy2024.zip"
FACILITIES_ZIP = DATA / "npdes_downloads.zip"

TARGET_PARAMS = {"00310", "00530", "00608", "00670"}

LOAD_UNITS = {"lb/d", "kg/d", "lb/yr", "lb/mo", "lb/wk"}

PARAM_NAMES = {
    "00310": "BOD5",
    "00530": "TSS",
    "00608": "Ammonia-N",
    "00670": "Total N",
}


def filter_dmr(zip_path: Path = DMR_ZIP) -> pd.DataFrame:
    """Chunk-read the DMR CSV, keep target parameters only.

    Returns DataFrame of matching records and caches it at
    data/epa/dmr_filtered_fy2024.csv (the zip holds millions of rows).
    """
    cache = DATA / "dmr_filtered_fy2024.csv"
    if cache.exists():
        df = pd.read_csv(cache, dtype=str, low_memory=False)
        print(f"  [CACHED] filtered DMR records: {len(df):,}")
        return df

    usecols = [
        "EXTERNAL_PERMIT_NMBR", "PARAMETER_CODE", "PARAMETER_DESC",
        "DMR_VALUE_NMBR", "DMR_UNIT_CODE", "DMR_UNIT_DESC",
        "VALUE_TYPE_CODE", "MONITORING_PERIOD_END_DATE",
    ]
    print(f"  Filtering {zip_path.name} for parameters {sorted(TARGET_PARAMS)}...")
    matches = []
    total = 0
    with zipfile.ZipFile(zip_path) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as f:
            for chunk in pd.read_csv(f, dtype=str, chunksize=500_000,
                                     usecols=usecols, low_memory=False):
                total += len(chunk)
                hits = chunk[chunk["PARAMETER_CODE"].isin(TARGET_PARAMS)]
                if len(hits):
                    matches.append(hits)
                if total % 5_000_000 < 500_000:
                    kept = sum(len(m) for m in matches)
                    print(f"    {total:,} rows scanned, {kept:,} matches")

    if not matches:
        raise RuntimeError("No target-parameter records found in DMR zip")

    df = pd.concat(matches, ignore_index=True)
    print(f"  Total rows: {total:,}, matching: {len(df):,}")
    df.to_csv(cache, index=False)
    print(f"  Saved {cache} ({cache.stat().st_size // (1024 * 1024)} MB)")
    return df


def facility_loads(df: pd.DataFrame) -> pd.DataFrame:
    """Per-facility BOD5/TSS/N/ammonia loads in lb/day.

    Load units are converted: kg/d * 2.20462, lb/yr / 365, lb/mo / 30.44,
    lb/wk / 7. Per facility takes the mean of reported load values, then
    the max across that facility's parameters rows is NOT summed; each
    parameter is its own column.
    """
    unit_to_lbd = {
        "lb/d": 1.0,
        "kg/d": 2.20462,
        "lb/yr": 1.0 / 365.0,
        "lb/mo": 1.0 / 30.44,
        "lb/wk": 1.0 / 7.0,
    }
    loads = df[df["DMR_UNIT_DESC"].isin(unit_to_lbd)].copy()
    loads["value"] = pd.to_numeric(loads["DMR_VALUE_NMBR"], errors="coerce")
    loads = loads[loads["value"] > 0]
    loads["lb_d"] = loads["value"] * loads["DMR_UNIT_DESC"].map(unit_to_lbd)

    out = loads.pivot_table(
        index="EXTERNAL_PERMIT_NMBR", columns="PARAMETER_CODE",
        values="lb_d", aggfunc="mean",
    )
    out.columns = [f"{PARAM_NAMES[c]}_lb_d" for c in out.columns]
    out = out.reset_index().rename(columns={"index": "EXTERNAL_PERMIT_NMBR"})
    return out


def municipal_permit_ids(zip_path: Path = FACILITIES_ZIP) -> set[str]:
    """Permit IDs with SIC 4952 (sewerage systems): municipal WWTPs.

    Industrial dischargers are excluded so human-waste per-capita math is
    not inflated by process wastewater.
    """
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open("NPDES_SICS.csv") as f:
            sics = pd.read_csv(f, dtype=str, low_memory=False)
    muni = sics[sics["SIC_CODE"].str.strip() == "4952"]
    return set(muni["NPDES_ID"].str.strip())


def facility_county_map(zip_path: Path = FACILITIES_ZIP) -> pd.DataFrame:
    """Permit number -> county FIPS from ICIS_FACILITIES.

    Returns DataFrame [EXTERNAL_PERMIT_NMBR, fips]. FIPS values that do
    not form a valid 5-digit county code are dropped.
    """
    from popest.geo import STATE_ABBREV_TO_FIPS, is_valid_county_fips

    with zipfile.ZipFile(zip_path) as zf:
        with zf.open("ICIS_FACILITIES.csv") as f:
            fac = pd.read_csv(f, dtype=str, low_memory=False,
                              usecols=lambda c: c in [
                                  "NPDES_ID", "COUNTY_CODE", "STATE_CODE",
                              ])
    fac = fac.dropna(subset=["NPDES_ID", "STATE_CODE"]).copy()
    fac["NPDES_ID"] = fac["NPDES_ID"].str.strip()
    fac["state_fips"] = fac["STATE_CODE"].str.strip().map(STATE_ABBREV_TO_FIPS)
    fac["county_fips"] = fac["COUNTY_CODE"].str.strip().str[-3:].str.zfill(3)
    fac["fips"] = fac["state_fips"].fillna("") + fac["county_fips"].fillna("")
    fac = fac[fac["fips"].str.len() == 5]
    fac = fac[fac["fips"].apply(is_valid_county_fips)]
    return (fac[["NPDES_ID", "fips"]]
            .drop_duplicates(subset=["NPDES_ID"], keep="first")
            .rename(columns={"NPDES_ID": "EXTERNAL_PERMIT_NMBR"}))
