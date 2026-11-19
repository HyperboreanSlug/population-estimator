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
SB_XLSX = Path("data/usda/school_breakfast_summary.xlsx")


def school_breakfast() -> dict:
    """School Breakfast Program total participation (millions, FY).

    Source: data/usda/school_breakfast_summary.xlsx (header row 2,
    'Total Participation' column, values in millions).
    """
    if not SB_XLSX.exists():
        return {}
    df = pd.read_excel(SB_XLSX, header=2)
    df = df.rename(columns=lambda c: str(c).strip())
    part_col = next((c for c in df.columns
                    if c.lower().startswith("total\nparticipation")
                    or "total participation" in c.lower().replace("\n", " ")),
                    None)
    fy_col = df.columns[0]
    if part_col is None:
        return {}
    work = df[[fy_col, part_col]].copy()
    work[fy_col] = work[fy_col].astype(str).str.replace(
        "\xa0", "", regex=False).str.strip()
    work[part_col] = pd.to_numeric(work[part_col], errors="coerce")
    work = work[work[fy_col].str.match(r"^\d{4}$")].dropna(subset=[part_col])
    if work.empty:
        return {}
    latest = work.iloc[-1]
    return {"year": int(latest[fy_col]),
            "participation_millions": float(latest[part_col]),
            "source": "data/usda/school_breakfast_summary.xlsx"}


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


def higher_ed_enrollment() -> dict:
    """Total fall enrollment in degree-granting institutions.

    Source: data/nces/tabn303.10.xlsx (NCES Digest table 303.10).
    Column 1 is total enrollment; the latest year row is used.
    """
    path = Path("data/nces/tabn303.10.xlsx")
    if not path.exists():
        return {}
    ip = pd.read_excel(path, header=None)
    rows = []
    for i in range(len(ip)):
        yr = str(ip.iloc[i, 0]).strip()
        v = pd.to_numeric(ip.iloc[i, 1], errors="coerce")
        if pd.notna(v) and yr[:4].isdigit() and len(yr) >= 4:
            rows.append((int(yr[:4]), float(v)))
    if not rows:
        return {}
    year, total = max(rows)
    return {"year": year, "enrollment": total,
            "source": "data/nces/tabn303.10.xlsx "
                      "(NCES Digest 303.10, degree-granting)"}


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
