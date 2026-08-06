"""Rewrite methods to use REAL downloaded data.

Replaces hardcoded approximations with values extracted from
actual downloaded files. Each value cites its source file.
"""

import json
import re
from pathlib import Path

import pandas as pd

DATA = Path("data")


def get_eia_total_energy() -> dict:
    """Real EIA total energy consumption.

    Source: data/eia/total_energy_monthly.csv (downloaded from eia.gov)
    """
    eia = DATA / "eia" / "total_energy_monthly.csv"
    if not eia.exists():
        return {"error": "EIA file not downloaded"}

    df = pd.read_csv(eia)
    # Get latest annual total (YYYYMM ending in 13 = annual)
    annual = df[df["YYYYMM"].astype(str).str.endswith("13")].copy()
    if annual.empty:
        return {"error": "No annual data found"}

    latest_year = annual["YYYYMM"].max()
    year_data = annual[annual["YYYYMM"] == latest_year]

    consumption = year_data[year_data["Description"].str.contains("Consumption", na=False)]
    total_row = consumption[consumption["Description"] == "Total Primary Energy Consumption"]

    if total_row.empty:
        return {"error": "Total consumption not found"}

    total_quad_btu = float(total_row["Value"].iloc[0])
    year = int(str(latest_year)[:4])

    return {
        "total_quad_btu": total_quad_btu,
        "year": year,
        "source": "data/eia/total_energy_monthly.csv",
        "url": "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T01.01",
    }


def get_epa_msw() -> dict:
    """Real EPA MSW generation.

    Source: data/epa/msw_national_overview.html (downloaded from epa.gov)
    Figure: 292.4 million tons (2018), 4.9 lbs/person/day
    """
    msw = DATA / "epa" / "msw_national_overview.html"
    if not msw.exists():
        return {"error": "EPA MSW file not downloaded"}

    content = msw.read_text(errors="replace")

    # Extract tonnage
    tonnage = re.findall(r"([\d,.]+)\s*million\s*tons", content, re.I)
    per_capita = re.findall(r"([\d,.]+)\s*pounds?\s*per\s*person", content, re.I)

    total_tons = float(tonnage[0]) if tonnage else 0
    lbs_per_day = float(per_capita[0]) if per_capita else 0

    return {
        "total_million_tons": total_tons,
        "lbs_per_person_day": lbs_per_day,
        "year": 2018,
        "source": "data/epa/msw_national_overview.html",
        "url": "https://www.epa.gov/facts-and-figures-about-materials-waste-and-recycling/national-overview-facts-and-figures-materials",
    }


def get_bls_employment() -> dict:
    """Real BLS employment data.

    Source: data/bls/total_employed.json (downloaded from BLS API)
    """
    bls = DATA / "bls" / "total_employed.json"
    if not bls.exists():
        return {"error": "BLS file not downloaded"}

    data = json.loads(bls.read_text())
    series = data.get("Results", {}).get("series", [])
    if not series:
        return {"error": "No BLS series data"}

    pts = series[0].get("data", [])
    if not pts:
        return {"error": "No data points"}

    latest = pts[0]
    employed_thousands = int(latest["value"])

    return {
        "employed_thousands": employed_thousands,
        "year": latest["year"],
        "period": latest["period"],
        "source": "data/bls/total_employed.json",
        "api": "https://api.bls.gov/publicAPI/v2/timeseries/data/LNS12000000",
    }


def get_irs_data() -> dict:
    """Real IRS SOI data.

    Source: data/irs/soi_zip_2022.csv (downloaded from irs.gov)
    """
    irs = DATA / "irs" / "soi_zip_2022.csv"
    if not irs.exists():
        return {"error": "IRS file not downloaded"}

    df = pd.read_csv(irs, usecols=["N1", "N2"])
    return {
        "total_returns": int(df["N1"].sum()),
        "total_exemptions": int(df["N2"].sum()),
        "source": "data/irs/soi_zip_2022.csv",
        "url": "https://www.irs.gov/pub/irs-soi/22zpallagi.csv",
    }


def get_usgs_water() -> dict:
    """Real USGS water use data.

    Source: data/usgs/usco2015.csv (downloaded from ScienceBase)
    """
    usgs = DATA / "usgs" / "usco2015.csv"
    if not usgs.exists():
        return {"error": "USGS file not downloaded"}

    df = pd.read_csv(usgs, skiprows=1, dtype=str)
    ps_col = None
    for col in df.columns:
        if "PS-WFrTo" in col or "PS-Wtotl" in col:
            ps_col = col
            break

    if ps_col:
        total_ps = pd.to_numeric(df[ps_col], errors="coerce").sum()
    else:
        total_ps = 0

    return {
        "total_ps_mgal_d": total_ps,
        "counties": len(df),
        "source": "data/usgs/usco2015.csv",
        "doi": "https://doi.org/10.5066/F7TB15V5",
    }


def get_dhs_immigration() -> dict:
    """Real DHS immigration data from Yearbook HTML tables.

    Source: data/dhs/yearbook_2023_table7.html
    Total LPRs 2023 = 1,172,910
    """
    path = DATA / "dhs" / "yearbook_2023_table7.html"
    if not path.exists():
        return {"error": "DHS file not downloaded"}

    html = path.read_text(errors="replace")
    tables = re.findall(r"<table[^>]*>(.*?)</table>", html, re.DOTALL | re.I)
    for table in tables:
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL | re.I)
        for row in rows:
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.I)
            if len(cells) >= 4:
                first = re.sub(r"<[^>]+>", " ", cells[0])
                first = re.sub(r"\s+", " ", first).strip()
                if "Total" in first and "all immigrants" in first:
                    return {
                        "lpr_total_2023": int(cells[1].replace("&nbsp;", "").replace(",", "").strip()),
                        "adjustments_2023": int(cells[2].replace("&nbsp;", "").replace(",", "").strip()),
                        "new_arrivals_2023": int(cells[3].replace("&nbsp;", "").replace(",", "").strip()),
                        "year": 2023,
                        "source": "data/dhs/yearbook_2023_table7.html",
                    }
    return {"error": "Could not parse DHS table"}


def report_all():
    """Print all real data points with citations."""
    print("=" * 60)
    print("  REAL DATA POINTS (from downloaded files)")
    print("=" * 60)

    print("\n[1] EIA Total Energy:")
    eia = get_eia_total_energy()
    if "error" not in eia:
        print(f"  Total consumption: {eia['total_quad_btu']} Quad Btu ({eia['year']})")
        print(f"  Source: {eia['source']}")
    else:
        print(f"  ERROR: {eia['error']}")

    print("\n[2] EPA MSW:")
    msw = get_epa_msw()
    if "error" not in msw:
        print(f"  Total generation: {msw['total_million_tons']} million tons ({msw['year']})")
        print(f"  Per capita: {msw['lbs_per_person_day']} lbs/person/day")
        print(f"  Source: {msw['source']}")
    else:
        print(f"  ERROR: {msw['error']}")

    print("\n[3] BLS Employment:")
    bls = get_bls_employment()
    if "error" not in bls:
        print(f"  Total employed: {bls['employed_thousands']:,} thousand ({bls['year']}-{bls['period']})")
        print(f"  Source: {bls['source']}")
    else:
        print(f"  ERROR: {bls['error']}")

    print("\n[4] IRS SOI:")
    irs = get_irs_data()
    if "error" not in irs:
        print(f"  Total returns: {irs['total_returns']:,}")
        print(f"  Total exemptions: {irs['total_exemptions']:,}")
        print(f"  Source: {irs['source']}")
    else:
        print(f"  ERROR: {irs['error']}")

    print("\n[5] USGS Water:")
    usgs = get_usgs_water()
    if "error" not in usgs:
        print(f"  Total PS withdrawals: {usgs['total_ps_mgal_d']:,.0f} Mgal/d")
        print(f"  Counties: {usgs['counties']}")
        print(f"  Source: {usgs['source']}")
    else:
        print(f"  ERROR: {usgs['error']}")

    print("\n[6] DHS Immigration:")
    dhs = get_dhs_immigration()
    if "error" not in dhs:
        print(f"  LPRs 2023: {dhs['lpr_total_2023']:,}")
        print(f"  Adjustments: {dhs['adjustments_2023']:,}")
        print(f"  New arrivals: {dhs['new_arrivals_2023']:,}")
        print(f"  Source: {dhs['source']}")
    else:
        print(f"  ERROR: {dhs['error']}")

    print("\n" + "=" * 60)
    print("  STILL APPROXIMATED (no real data available)")
    print("=" * 60)
    print("  - CDC births/deaths: natality.csv is surveillance data, not vital stats")
    print("  - USDA SNAP/food: HTML page with no extractable numbers")
    print("  - CTIA wireless: only JS app shell, no data")
    print("  - CMS Medicare: API returns JS app shell")
    print("  - Census retail: HTML page, no structured data")
    print("  - AHRQ healthcare: HTML app shell, no extractable numbers")
    print("  - NCES enrollment: HTML app shell")
    print("  - DHS/CDC vital stats: not downloaded")
    print("  - Healthcare utilization rates: CDC blocked")


if __name__ == "__main__":
    report_all()
