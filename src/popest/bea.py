"""BEA personal income client.

CAINC1 (Personal Income Summary) from the BEA regional zip. The United
States row (GeoFIPS 00000) holds national totals: LineCode 1 = personal
income (thousands), LineCode 2 = population (BEA uses census-based
estimates: the file's 2024 population is 340,110,988), LineCode 3 =
per-capita income.

The population voice divides total income by an independent per-capita
constant; using BEA's own LineCode 2 or LineCode 3 would be circular
(census denominators throughout).
"""

import zipfile
from pathlib import Path

import pandas as pd

CAINC1_ZIP = Path("data/bea/CAINC1.zip")
US_MEMBER = "CAINC1_US_1969_2024.csv"


def national_personal_income() -> dict:
    """US total personal income, latest year in the file."""
    if not CAINC1_ZIP.exists():
        return {}
    with zipfile.ZipFile(CAINC1_ZIP) as zf:
        with zf.open(US_MEMBER) as f:
            df = pd.read_csv(f, dtype=str)
    us = df[df["GeoFIPS"].astype(str).str.strip().str.strip('"') == "00000"]
    income = us[us["LineCode"].astype(str).str.strip() == "1"]
    if income.empty:
        return {}
    row = income.iloc[0]
    year = int(row.index[-1])
    value_thousands = pd.to_numeric(row.iloc[-1], errors="coerce")
    if pd.isna(value_thousands):
        return {}
    return {
        "year": year,
        "total_income": float(value_thousands) * 1000.0,
        "source": "data/bea/CAINC1.zip (CAINC1 US row, personal income)",
    }
