"""Extract real numbers from IRS SOI and other downloaded data."""

import json
from pathlib import Path

import pandas as pd

DATA = Path("data")


def extract_irs():
    """Extract national totals from IRS SOI ZIP data."""
    irs = DATA / "irs" / "soi_zip_2022.csv"
    print(f"Reading IRS SOI ({irs.stat().st_size // (1024*1024)} MB)...")
    df = pd.read_csv(irs, usecols=["STATEFIPS", "zipcode", "agi_stub", "N1", "N2"])
    print(f"  Rows: {len(df):,}")
    total_returns = df["N1"].sum()
    total_exemptions = df["N2"].sum()
    n_states = df["STATEFIPS"].nunique()
    n_zips = df["zipcode"].nunique()
    print(f"  Total returns filed (N1): {total_returns:,.0f}")
    print(f"  Total exemptions (N2): {total_exemptions:,.0f}")
    print(f"  States: {n_states}")
    print(f"  ZIP codes: {n_zips:,}")
    print(f"  Source: data/irs/soi_zip_2022.csv, fields N1, N2")
    return {"returns": total_returns, "exemptions": total_exemptions}


def extract_census_pep():
    """Extract Census PEP national estimate."""
    pep = DATA / "census" / "pep_us.json"
    if not pep.exists():
        pep = DATA / "census" / "pep_api_response.json"
    if not pep.exists():
        print("  No Census PEP file found")
        return None
    content = pep.read_text()
    try:
        data = json.loads(content)
        print(f"  Census PEP response: {data}")
        return data
    except json.JSONDecodeError:
        print(f"  Census PEP file not valid JSON: {content[:200]}")
        return None


def extract_eia_electricity():
    """Extract EIA electricity sales data."""
    eia = DATA / "eia" / "electricity_sales.xlsx"
    if not eia.exists():
        print("  No EIA electricity file")
        return None
    try:
        df = pd.read_excel(eia, sheet_name=None)
        print(f"  EIA sheets: {list(df.keys())[:5]}")
        for name, sheet in list(df.items())[:2]:
            print(f"  Sheet '{name}': {sheet.shape}")
            print(f"    Columns: {list(sheet.columns)[:8]}")
        return df
    except Exception as e:
        print(f"  EIA parse error: {e}")
        return None


def extract_bls():
    """Extract BLS employment data."""
    employed = DATA / "bls" / "total_employed.json"
    labor = DATA / "bls" / "labor_force.json"
    results = {}
    for name, path in [("employed", employed), ("labor_force", labor)]:
        if path.exists():
            data = json.loads(path.read_text())
            series = data.get("Results", {}).get("series", [])
            if series:
                pts = series[0].get("data", [])[:3]
                vals = [(p["year"], p["period"], p["value"]) for p in pts]
                results[name] = vals
                print(f"  BLS {name}: {vals}")
    return results


def extract_epa_msw():
    """Extract EPA MSW tonnage from downloaded HTML."""
    import re
    msw = DATA / "epa" / "msw_national_overview.html"
    if not msw.exists():
        msw = DATA / "epa" / "msw_overview.html"
    if not msw.exists():
        print("  No EPA MSW file")
        return None
    content = msw.read_text(errors="replace")
    matches = re.findall(r"([\d,.]+)\s*million\s*(?:short\s*)?tons", content, re.I)
    if matches:
        print(f"  EPA MSW figures (million tons): {matches[:10]}")
        return matches
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("  EXTRACTING REAL DATA FROM DOWNLOADED FILES")
    print("=" * 60)

    print("\n[1] IRS SOI Tax Data (TY2022):")
    irs_data = extract_irs()

    print("\n[2] Census PEP:")
    extract_census_pep()

    print("\n[3] EIA Electricity Sales:")
    extract_eia_electricity()

    print("\n[4] BLS Employment:")
    extract_bls()

    print("\n[5] EPA MSW:")
    extract_epa_msw()

    print("\n" + "=" * 60)
    print("  KEY REAL DATA POINTS")
    print("=" * 60)
    if irs_data:
        print(f"  IRS returns filed: {irs_data['returns']:,.0f}")
        print(f"  IRS exemptions:    {irs_data['exemptions']:,.0f}")
