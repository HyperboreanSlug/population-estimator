"""Utility meter-count clients.

Physical dwelling counts independent of census housing units:
- residential electricity customers (meters) from the EIA-861 annual
  file. Retail-choice customers appear under BOTH their delivery
  utility (Bundled/Delivery rows) and their energy retailer (Energy
  rows); only Bundled+Delivery are summed to avoid double counting.
  2024: 143,144,185 meters.
- residential natural gas consumers from the EIA dnav BIFF8 workbook.
  2024: 73,719,064 customers.

Sources:
    data/eia/f8612024.zip -> Sales_Ult_Cust_2024.xlsx (sheet States)
    data/eia/gas_residential_customers.xls (sheet Data 1, series
    NA1501_NUS_8 and state equivalents; requires xlrd)
"""

import zipfile
from pathlib import Path

import pandas as pd

EIA861_ZIP = Path("data/eia/f8612024.zip")
GAS_XLS = Path("data/eia/gas_residential_customers.xls")


def residential_electricity_meters() -> pd.DataFrame:
    """Residential electricity customers by state (Bundled+Delivery).

    Returns DataFrame [state, meters]. Sum is the national meter count.
    """
    if not EIA861_ZIP.exists():
        return pd.DataFrame(columns=["state", "meters"])

    with zipfile.ZipFile(EIA861_ZIP) as zf:
        member = next(n for n in zf.namelist()
                      if n.startswith("Sales_Ult_Cust_2")
                      and n.endswith(".xlsx"))
        with zf.open(member) as f:
            df = pd.read_excel(f, sheet_name="States", header=2)

    df["meters"] = pd.to_numeric(df["Count"], errors="coerce").fillna(0)
    df["svc"] = df["Service Type"].astype(str).str.strip()
    df["state"] = df["State"].astype(str).str.strip()
    # Energy rows are the same customers counted by their energy
    # retailer; the delivery utility already reports them.
    keep = df[df["svc"].isin(["Bundled", "Delivery"])]
    grouped = keep.groupby("state", as_index=False)["meters"].sum()
    return grouped


def residential_gas_customers() -> dict:
    """US residential natural gas consumers, latest year.

    The BIFF8 workbook: row 1 holds source keys (US series ends with
    _NUS_8), row 2 series names, column A dates from row 3.
    """
    if not GAS_XLS.exists():
        return {}
    g = pd.read_excel(GAS_XLS, sheet_name="Data 1", header=None)
    us_col = None
    for j in range(1, g.shape[1]):
        if str(g.iloc[1, j]).strip().endswith("_NUS_8"):
            us_col = j
            break
    if us_col is None:
        return {}
    vals = pd.to_numeric(g.iloc[3:, us_col], errors="coerce")
    dates = g.iloc[3:, 0]
    pairs = [(d, v) for d, v in zip(dates, vals) if pd.notna(v)]
    if not pairs:
        return {}
    latest_date, latest_val = pairs[-1]
    return {
        "year": int(str(latest_date)[:4]),
        "customers": float(latest_val),
        "source": "data/eia/gas_residential_customers.xls "
                  "(EIA dnav residential consumers, _NUS_8 series)",
    }
