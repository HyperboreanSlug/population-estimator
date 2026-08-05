"""IRS Statistics of Income (SOI) data client.

Uses REAL downloaded data from data/irs/soi_zip_2022.csv (206 MB).
Source: https://www.irs.gov/pub/irs-soi/22zpallagi.csv
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/irs")
SOI_FILE = DATA_DIR / "soi_zip_2022.csv"


def load_soi_summary() -> dict:
    """Load national totals from downloaded IRS SOI data.

    Citation: data/irs/soi_zip_2022.csv, fields N1 (returns), N2 (exemptions).
    Downloaded from: https://www.irs.gov/pub/irs-soi/22zpallagi.csv
    """
    if not SOI_FILE.exists():
        return {"error": "SOI file not downloaded. Run: python -m popest.download_comprehensive"}

    df = pd.read_csv(SOI_FILE, usecols=["STATEFIPS", "zipcode", "N1", "N2"])
    total_returns = int(df["N1"].sum())
    total_exemptions = int(df["N2"].sum())
    n_states = int(df["STATEFIPS"].nunique())
    n_zips = int(df["zipcode"].nunique())

    return {
        "year": 2022,
        "total_returns_filed": total_returns,
        "total_exemptions": total_exemptions,
        "states": n_states,
        "zip_codes": n_zips,
        "source": "data/irs/soi_zip_2022.csv (fields N1, N2)",
        "url": "https://www.irs.gov/pub/irs-soi/22zpallagi.csv",
    }


def estimate_from_irs() -> dict:
    """Population estimate from IRS data.

    Total exemptions (N2) counts filer + spouse + all dependents.
    This is the closest IRS proxy to total population.
    Non-filers (undocumented, homeless, very low income) are added.
    """
    soi = load_soi_summary()
    if "error" in soi:
        return {"error": soi["error"]}

    exemptions = soi["total_exemptions"]
    results = {}

    # Non-filer adjustment: estimated 8-18% of population doesn't file
    for label, nonfiler_rate in [("central", 0.12), ("low", 0.18), ("high", 0.08)]:
        results[f"irs_{label}"] = exemptions / (1.0 - nonfiler_rate)

    results["source"] = soi["source"]
    results["raw_exemptions"] = exemptions
    results["raw_returns"] = soi["total_returns_filed"]
    return results
