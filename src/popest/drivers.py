"""FHWA licensed driver client.

DL-1C (Highway Statistics 2024): licensed drivers by sex and state.
The national Total row: 239,824,944 licensed drivers in 2024.

Source: data/fhwa/dl1c_2024.xlsx (sheet DL-1C, header row 5, column
'TOTAL DRIVERS (2)', Total row).
"""

from pathlib import Path

import pandas as pd

DL1C_XLSX = Path("data/fhwa/dl1c_2024.xlsx")


def licensed_drivers() -> dict:
    """US total licensed drivers, latest year in the file."""
    if not DL1C_XLSX.exists():
        return {}
    df = pd.read_excel(DL1C_XLSX, header=4)
    drivers_col = df.columns[5]
    tot = df[df.iloc[:, 0].astype(str).str.strip() == "Total"]
    if tot.empty:
        return {}
    value = pd.to_numeric(tot.iloc[0][drivers_col], errors="coerce")
    if pd.isna(value):
        return {}
    year = 2024
    title = pd.read_excel(DL1C_XLSX, header=None, nrows=1).iloc[0, 0]
    for token in str(title).split():
        if token[:4].isdigit():
            year = int(token[:4])
            break
    return {"year": year, "drivers": float(value),
            "source": "data/fhwa/dl1c_2024.xlsx "
                      "(FHWA DL-1C licensed drivers)"}
