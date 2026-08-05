"""IRS Statistics of Income (SOI) data client.

Tax filer counts and dependents as population proxy.
"""

from pathlib import Path

import pandas as pd
import requests

CACHE_DIR = Path("data/irs")

IRS_SOI_URL = "https://www.irs.gov/pub/irs-soi/22zpallagi.csv"


def fetch_irs_soi_zip(use_cache: bool = True) -> pd.DataFrame:
    """Download IRS SOI ZIP code data (TY2022).

    Contains: number of returns, exemptions, dependents by ZIP.
    ~150M returns filed. Each return has filer + spouse + dependents.
    """
    cache_path = CACHE_DIR / "irs_soi_2022.csv"
    if use_cache and cache_path.exists():
        return pd.read_csv(cache_path, dtype=str, low_memory=False)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print("  Downloading IRS SOI ZIP data (~50 MB)...")
    try:
        resp = requests.get(IRS_SOI_URL, timeout=300, stream=True)
        resp.raise_for_status()
        with open(cache_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
        return pd.read_csv(cache_path, dtype=str, low_memory=False)
    except Exception as e:
        print(f"  Download failed: {e}")
        return pd.DataFrame()


def irs_national_summary() -> dict:
    """National IRS filing statistics, TY2022.

    Source: IRS SOI Tax Stats.
    Total individual returns filed: ~153M
    Total exemptions claimed: ~330M (filers + spouses + dependents)
    """
    return {
        "year": 2022,
        "total_returns_filed": 153_000_000,
        "total_exemptions": 330_000_000,
        "filing_rate_adults": 0.82,
        "source": "IRS SOI Tax Stats TY2022",
    }


def estimate_from_irs() -> dict:
    """Population estimate from IRS data.

    Total exemptions ≈ population covered by tax system.
    Add estimated non-filers (undocumented, homeless, very low income).
    """
    irs = irs_national_summary()
    results = {}

    exemptions = irs["total_exemptions"]
    for label, nonfiler_add in [("central", 0.12), ("low", 0.18), ("high", 0.08)]:
        results[f"irs_{label}"] = exemptions * (1 + nonfiler_add)

    return results
