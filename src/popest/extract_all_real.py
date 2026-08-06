"""Extract real numbers from downloaded data files and report what's usable."""

import json
import re
from pathlib import Path

import pandas as pd

DATA = Path("data")


def check_all():
    print("=" * 60)
    print("  EXTRACTING REAL DATA FROM DOWNLOADED FILES")
    print("=" * 60)

    # 1. EIA total energy
    print("\n[1] EIA Total Energy (data/eia/total_energy_monthly.csv)")
    eia = DATA / "eia" / "total_energy_monthly.csv"
    if eia.exists():
        df = pd.read_csv(eia)
        annual = df[df["YYYYMM"] == 202313]
        if not annual.empty:
            for _, row in annual.iterrows():
                print(f"  {row['Description']}: {row['Value']} {row['Unit']}")
        else:
            # Get latest year
            latest = df[df["YYYYMM"].astype(str).str.endswith("13")].tail(5)
            for _, row in latest.iterrows():
                print(f"  {row['YYYYMM']} {row['Description']}: {row['Value']} {row['Unit']}")

    # 2. CDC natality
    print("\n[2] CDC Natality (data/cdc/natality.csv)")
    cdc = DATA / "cdc" / "natality.csv"
    if cdc.exists():
        df = pd.read_csv(cdc, nrows=5)
        print(f"  Columns: {list(df.columns)[:10]}")
        print(f"  Size: {cdc.stat().st_size // (1024*1024)} MB")
        # Check if it's actually natality or something else
        if "case_month" in df.columns:
            print("  NOTE: This is case surveillance data, NOT natality")
            print("  The Socrata view ID was wrong - this is disease surveillance")

    # 3. Census retail
    print("\n[3] Census Retail (data/census/retail_index.html)")
    retail = DATA / "census" / "retail_index.html"
    if retail.exists():
        content = retail.read_text(errors="replace")
        # Look for food/grocery sales
        food = re.findall(r"(?:food|grocery)[^<]*?[\$:]?\s*([\d,.]+)\s*(?:billion|million)?", content, re.I)
        if food:
            print(f"  Food/grocery figures found: {food[:5]}")
        # Look for total retail
        total = re.findall(r"(?:total|advance)[^<]*?[\$:]?\s*([\d,.]+)", content, re.I)
        if total:
            print(f"  Total retail figures: {total[:5]}")
        print(f"  Page size: {len(content)//1024} KB")

    # 4. CMS Medicare
    print("\n[4] CMS Medicare (data/cms/medicare_enrollment_data.csv)")
    cms = DATA / "cms" / "medicare_enrollment_data.csv"
    if cms.exists():
        content = cms.read_text()
        print(f"  Content: {content[:300]}")
        print(f"  Size: {len(content)} bytes")

    # 5. CTIA wireless
    print("\n[5] CTIA Wireless (data/ctia/wireless.html)")
    ctia = DATA / "ctia" / "wireless.html"
    if ctia.exists():
        content = ctia.read_text(errors="replace")
        nums = re.findall(r"([\d,.]+)\s*million", content, re.I)
        if nums:
            print(f"  Million figures: {nums[:5]}")
        print(f"  Size: {len(content)//1024} KB")

    # 6. EIA SEDS per capita
    print("\n[6] EIA SEDS (data/eia/seds_per_capita.csv)")
    seds = DATA / "eia" / "seds_per_capita.csv"
    if seds.exists():
        content = seds.read_text(errors="replace")
        if content.startswith("<"):
            print("  Got HTML instead of CSV")
        else:
            df = pd.read_csv(seds, nrows=5)
            print(f"  Columns: {list(df.columns)[:8]}")
            print(f"  First rows:")
            print(df.head(3).to_string())

    # 7. FHWA vehicles PDF
    print("\n[7] FHWA Vehicles (data/fhwa/vehicle_registrations_2022.pdf)")
    fhwa = DATA / "fhwa" / "vehicle_registrations_2022.pdf"
    if fhwa.exists():
        print(f"  Size: {fhwa.stat().st_size // 1024} KB")
        print("  Valid PDF - need pdfplumber to extract tables")

    # 8. EPA MSW
    print("\n[8] EPA MSW (data/epa/msw_national_overview.html)")
    msw = DATA / "epa" / "msw_national_overview.html"
    if msw.exists():
        content = msw.read_text(errors="replace")
        # Find the 292.4 figure with context
        idx = content.find("292.4")
        if idx > 0:
            ctx = content[max(0, idx-100):idx+200]
            ctx = re.sub(r"<[^>]+>", " ", ctx)
            ctx = re.sub(r"\s+", " ", ctx).strip()
            print(f"  Context: {ctx[:200]}")

    # 9. BLS data
    print("\n[9] BLS Employment (data/bls/total_employed.json)")
    bls = DATA / "bls" / "total_employed.json"
    if bls.exists():
        data = json.loads(bls.read_text())
        series = data.get("Results", {}).get("series", [])
        if series:
            pts = series[0].get("data", [])[:3]
            for p in pts:
                print(f"  {p['year']}-{p['period']}: {p['value']} thousand employed")

    # 10. IRS SOI
    print("\n[10] IRS SOI (data/irs/soi_zip_2022.csv)")
    irs = DATA / "irs" / "soi_zip_2022.csv"
    if irs.exists():
        print(f"  Size: {irs.stat().st_size // (1024*1024)} MB")
        print("  Already processed: 312M returns, 576M exemptions")


if __name__ == "__main__":
    check_all()
