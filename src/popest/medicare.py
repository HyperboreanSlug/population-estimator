"""CMS Medicare enrollment data client.

Medicare Monthly Enrollment dataset (public CSV on data.cms.gov).
Aged beneficiaries (AGED_TOT_BENES) are a near-complete count of the
65+ population, backing out total population via the published aged
share and Medicare enrollment rate.

NOTE: cms.gov does not resolve through some local resolvers (verified
NXDOMAIN on this machine while the host itself is live via public DNS).
The client reports the honest error and the voice drops; no DNS
bypasses are performed here.
"""

from pathlib import Path

import pandas as pd
import requests

MEDICARE_CSV_URL = (
    "https://data.cms.gov/data-api/v1/dataset/"
    "d7fabe1e-d19b-4333-9eff-e80e0643f2fd/data.csv"
)
CACHE = Path("data/cms/medicare_monthly_enrollment.csv")
MEDICARE_ENROLLMENT_RATE = 0.97  # CMS: ~97% of 65+ enrolled


def download_medicare_csv() -> Path:
    if CACHE.exists() and CACHE.stat().st_size > 100:
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(
        MEDICARE_CSV_URL, timeout=900, stream=True,
        headers={"User-Agent": "population-estimator/0.1"})
    resp.raise_for_status()
    with open(CACHE, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
    return CACHE


def national_aged_beneficiaries() -> dict:
    """Latest national aged Medicare beneficiaries.

    Returns {year, month, aged_benes, total_benes, source}.
    """
    path = download_medicare_csv()
    df = pd.read_csv(path, dtype=str, low_memory=False)
    df = df[df["BENE_GEO_LVL"] == "National"].copy()
    if df.empty:
        raise RuntimeError("no national rows in Medicare enrollment CSV")

    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")
    df = df.dropna(subset=["YEAR"])
    latest_year = int(df["YEAR"].max())
    df = df[df["YEAR"] == latest_year]
    months = pd.to_numeric(df["MONTH"], errors="coerce")
    latest_month = int(months.max())
    row = df[months == latest_month].iloc[0]

    return {
        "year": latest_year,
        "month": latest_month,
        "aged_benes": float(row["AGED_TOT_BENES"]),
        "total_benes": float(row["TOT_BENES"]),
        "source": "data.cms.gov Medicare Monthly Enrollment "
                  "(data/cms/medicare_monthly_enrollment.csv)",
    }
