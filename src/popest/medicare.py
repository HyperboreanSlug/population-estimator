"""CMS Medicare enrollment data client.

Medicare Monthly Enrollment dataset (public CSV on data.cms.gov).
Aged beneficiaries (AGED_TOT_BENES) are a near-complete count of the
65+ population, backing out total population via the published aged
share and Medicare enrollment rate.

Some local resolvers block cms.gov (NXDOMAIN while the host is live
via public DNS). When that happens, set POP_EST_SOCKS_PROXY to a SOCKS
proxy (for example an SSH dynamic forward to a resolver that works):

    POP_EST_SOCKS_PROXY=socks5h://127.0.0.1:1080 popest run

socks5h resolves the hostname at the proxy, so local DNS blocks do not
apply. requests needs the PySocks extra for this.
"""

import os
from pathlib import Path

import pandas as pd
import requests

MEDICARE_CSV_URL = (
    "https://data.cms.gov/data-api/v1/dataset/"
    "d7fabe1e-d19b-4333-9eff-e80e0643f2fd/data.csv"
)
CACHE = Path("data/cms/medicare_monthly_enrollment.csv")
MEDICARE_ENROLLMENT_RATE = 0.97  # CMS: ~97% of 65+ enrolled


def _proxies() -> dict | None:
    proxy = os.environ.get("POP_EST_SOCKS_PROXY", "").strip()
    if not proxy:
        return None
    return {"https": proxy, "http": proxy}


def county_aged_beneficiaries() -> pd.DataFrame:
    """County-level aged Medicare beneficiaries, latest month.

    Returns DataFrame [fips, aged_benes] from BENE_GEO_LVL == "County"
    rows. Requires the enrollment CSV (155 MB).
    """
    path = download_medicare_csv()
    df = pd.read_csv(path, dtype=str, low_memory=False,
                     usecols=["YEAR", "MONTH", "BENE_GEO_LVL",
                              "BENE_FIPS_CD", "AGED_TOT_BENES"])
    df = df[df["BENE_GEO_LVL"] == "County"].copy()
    if df.empty:
        return pd.DataFrame(columns=["fips", "aged_benes"])
    df = df[df["MONTH"].isin(MONTH_ORDER)].copy()
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")
    df = df.dropna(subset=["YEAR"])
    latest_year = int(df["YEAR"].max())
    df = df[df["YEAR"] == latest_year]
    df["month_idx"] = df["MONTH"].map(MONTH_ORDER)
    latest_month = int(df["month_idx"].max())
    df = df[df["month_idx"] == latest_month]

    out = pd.DataFrame({
        "fips": df["BENE_FIPS_CD"].astype(str).str.zfill(5),
        "aged_benes": pd.to_numeric(df["AGED_TOT_BENES"],
                                    errors="coerce"),
    }).dropna()
    out = out.groupby("fips", as_index=False)["aged_benes"].sum()
    return out[out["fips"].str.len() == 5]


def download_medicare_csv() -> Path:
    if CACHE.exists() and CACHE.stat().st_size > 100:
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(
        MEDICARE_CSV_URL, timeout=900, stream=True,
        headers={"User-Agent": "population-estimator/0.1"},
        proxies=_proxies())
    resp.raise_for_status()
    with open(CACHE, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
    return CACHE


MONTH_ORDER = {name: i for i, name in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}


def national_aged_beneficiaries() -> dict:
    """Latest national aged Medicare beneficiaries.

    The MONTH column holds month names; annual "Year" rows are skipped.
    Returns {year, month, month_name, aged_benes, total_benes, source}.
    """
    path = download_medicare_csv()
    df = pd.read_csv(path, dtype=str, low_memory=False)
    df = df[df["BENE_GEO_LVL"] == "National"].copy()
    if df.empty:
        raise RuntimeError("no national rows in Medicare enrollment CSV")

    df = df[df["MONTH"].isin(MONTH_ORDER)].copy()
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")
    df = df.dropna(subset=["YEAR"])
    latest_year = int(df["YEAR"].max())
    df = df[df["YEAR"] == latest_year]
    df["month_idx"] = df["MONTH"].map(MONTH_ORDER)
    row = df.loc[df["month_idx"].idxmax()]

    month_idx = int(row["month_idx"])
    month_name = row["MONTH"]
    return {
        "year": latest_year,
        "month": month_idx,
        "month_name": month_name,
        "aged_benes": float(row["AGED_TOT_BENES"]),
        "total_benes": float(row["TOT_BENES"]),
        "source": "data.cms.gov Medicare Monthly Enrollment "
                  "(data/cms/medicare_monthly_enrollment.csv)",
    }
