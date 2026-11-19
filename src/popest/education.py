"""Education and child-nutrition data client.

Public K-12 enrollment from the NCES Common Core of Data (state
education agency nonfiscal membership file, 2024-25), plus NSLP and WIC
participation from USDA FNS.

Sources (downloaded via `popest download`):
    data/nces/ccd_sea_052_2425.zip
        -> ccd_sea_052_2425_l_1a_073025.csv (STUDENT_COUNT)
    data/usda/nslp_fy_participation.xlsx (NSLP, FY series)
    data/usda/wic_monthly.xlsx (WIC, FY series)
"""

import zipfile
from pathlib import Path

import pandas as pd

NCES_ZIP = Path("data/nces/ccd_sea_052_2425.zip")
NSLP_XLSX = Path("data/usda/nslp_fy_participation.xlsx")
WIC_XLSX = Path("data/usda/wic_monthly.xlsx")


def public_enrollment() -> pd.DataFrame:
    """State-level public K-12 enrollment, 2024-25.

    Returns DataFrame [state, state_name, enrollment] using the
    "Education Unit Total" rows of the CCD membership file.
    """
    if not NCES_ZIP.exists():
        return pd.DataFrame(columns=["state", "state_name", "enrollment"])

    with zipfile.ZipFile(NCES_ZIP) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".csv"))
        with zf.open(name) as f:
            df = pd.read_csv(f, dtype=str, low_memory=False)

    df["STUDENT_COUNT"] = pd.to_numeric(df["STUDENT_COUNT"],
                                        errors="coerce").fillna(0)
    totals = df[df["TOTAL_INDICATOR"].str.strip()
                == "Education Unit Total"].copy()
    totals = totals.groupby(["ST", "STATENAME"], as_index=False)[
        "STUDENT_COUNT"].sum()
    return totals.rename(columns={
        "ST": "state", "STATENAME": "state_name",
        "STUDENT_COUNT": "enrollment"})


def _read_fy_xlsx(path: Path, fy_col: str, value_col: str) -> dict:
    """Read a small FNS XLSX: latest FY row for one value column."""
    if not path.exists():
        return {}
    header = pd.read_excel(path, header=2)
    header = header.rename(columns=lambda c: str(c).strip())
    for col in header.columns:
        if col.lower().startswith(fy_col.lower()[:6]):
            header = header.rename(columns={col: "fy"})
            break
    header = header.rename(columns={value_col: "value"})
    if "fy" not in header.columns or "value" not in header.columns:
        return {}
    header["fy"] = header["fy"].astype(str).str.replace(
        "FY ", "", regex=False).str.strip()
    rows = header[["fy", "value"]].dropna()
    rows = rows[rows["fy"].str.match(r"^\d{4}$")]
    if rows.empty:
        return {}
    latest = rows.sort_values("fy").iloc[-1]
    return {"year": int(latest["fy"]), "value": float(latest["value"])}


def nslp_participation() -> dict:
    """National School Lunch Program average daily participation."""
    return _read_fy_xlsx(NSLP_XLSX, "Fiscal Year", "FY 2025")


def wic_participation() -> dict:
    """WIC total participants (FY)."""
    return _read_fy_xlsx(WIC_XLSX, "Fiscal Year", "Total Particpants")
