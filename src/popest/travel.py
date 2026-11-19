"""Travel and library data clients.

- FAA commercial enplanements (CY2025, per-airport xlsx, summed).
- NTD unlinked passenger trips (Socrata annual filter; latest complete
  year 2024 - 2025 rows exist but remain under revision).
- IMLS Public Libraries Survey FY2023: annual visits and registered
  borrowers (9,252 outlets/administrative entities).

Sources:
    data/faa/enplanements_cy2025.xlsx
    data/dot/ntd_annual_trips.csv
    data/imls/pls_fy2023_csv.zip -> CSV/PLS_FY23_AE_pud23i.csv
"""

import zipfile
from pathlib import Path

import pandas as pd

FAA_XLSX = Path("data/faa/enplanements_cy2025.xlsx")
NTD_CSV = Path("data/dot/ntd_annual_trips.csv")
IMLS_ZIP = Path("data/imls/pls_fy2023_csv.zip")

NTD_COMPLETE_YEAR = 2024  # 2025 annual rows exist but are revised


def enplanements() -> dict:
    """US commercial enplanements, latest calendar year."""
    if not FAA_XLSX.exists():
        return {}
    fa = pd.read_excel(FAA_XLSX)
    col = next(c for c in fa.columns if "Enplanements" in str(c))
    total = pd.to_numeric(fa[col], errors="coerce").sum()
    year = int(str(col).split()[1])
    return {"year": year, "total": float(total),
            "source": f"data/faa/enplanements_cy{year}.xlsx "
                      f"(FAA commercial service airports)"}


def transit_trips(year: int = NTD_COMPLETE_YEAR) -> dict:
    """NTD annual unlinked passenger trips for the given year."""
    if not NTD_CSV.exists():
        return {}
    ntd = pd.read_csv(NTD_CSV)
    sub = ntd[ntd["report_year"] == year]
    if sub.empty:
        return {}
    total = pd.to_numeric(sub["unlinked_passenger_trips_upt"],
                          errors="coerce").sum()
    return {"year": year, "total": float(total),
            "source": "data/dot/ntd_annual_trips.csv "
                      "(NTD Service by Mode, Annual Total)"}


def library_survey() -> dict:
    """IMLS Public Libraries Survey totals, latest FY in the zip."""
    if not IMLS_ZIP.exists():
        return {}
    with zipfile.ZipFile(IMLS_ZIP) as zf:
        member = next(n for n in zf.namelist()
                      if n.endswith(".csv") and "AE" in n)
        with zf.open(member) as f:
            lib = pd.read_csv(f, low_memory=False,
                              usecols=["VISITS", "REGBOR", "POPU_LSA"])
    visits = pd.to_numeric(lib["VISITS"], errors="coerce").sum()
    regbor = pd.to_numeric(lib["REGBOR"], errors="coerce").sum()
    fiscal_year = 2023  # pls_fy2023 file name
    return {
        "fiscal_year": fiscal_year,
        "visits": float(visits),
        "registered_borrowers": float(regbor),
        "source": "data/imls/pls_fy2023_csv.zip (IMLS PLS FY2023)",
    }
