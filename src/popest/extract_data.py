"""Extract real numbers from downloaded data files."""

import json
from pathlib import Path

DATA = Path("data")


def check_all():
    print("=" * 60)
    print("  EXTRACTING REAL DATA FROM DOWNLOADED FILES")
    print("=" * 60)

    # BLS unemployment
    print("\n[1] BLS Unemployment:")
    bls = DATA / "bls" / "unemployment_national.json"
    if bls.exists():
        try:
            data = json.loads(bls.read_text())
            series = data.get("Results", {}).get("series", [])
            if series:
                pts = series[0].get("data", [])[:5]
                for p in pts:
                    print(f"  {p.get('year')}-{p.get('period')}: {p.get('value')}%")
        except Exception as e:
            print(f"  Parse error: {e}")

    # EIA rank_use_per_cap.csv - check if it's actually CSV
    print("\n[2] EIA rank_use_per_cap.csv:")
    eia = DATA / "eia" / "rank_use_per_cap.csv"
    if eia.exists():
        content = eia.read_text(errors="replace")[:500]
        if content.startswith("<"):
            print("  NOT CSV - got HTML page instead")
        else:
            lines = content.split("\n")[:5]
            for l in lines:
                print(f"  {l[:100]}")

    # USGS water data - verify it's the real thing
    print("\n[3] USGS Water Use 2015:")
    usgs = DATA / "usgs" / "usco2015.csv"
    if usgs.exists():
        import pandas as pd
        df = pd.read_csv(usgs, skiprows=1, dtype=str, nrows=5)
        print(f"  Columns: {list(df.columns)[:10]}")
        print(f"  First row FIPS: {df.iloc[0].get('FIPS', 'N/A')}")
        full = pd.read_csv(usgs, skiprows=1, dtype=str)
        print(f"  Total rows: {len(full)}")

    # EPA NPDES zip - check contents
    print("\n[4] EPA NPDES ZIP:")
    npdes = DATA / "epa" / "npdes_downloads.zip"
    if npdes.exists():
        import zipfile
        with zipfile.ZipFile(npdes) as zf:
            names = zf.namelist()
            print(f"  Files: {len(names)}")
            for n in names[:5]:
                info = zf.getinfo(n)
                print(f"    {n} ({info.file_size // 1024} KB)")

    # CBP encounters - extract numbers from HTML
    print("\n[5] CBP Encounters page:")
    cbp = DATA / "cbp" / "encounters_page.html"
    if cbp.exists():
        content = cbp.read_text(errors="replace")
        # Look for numeric patterns
        import re
        numbers = re.findall(r"[\d,]{6,}", content)
        if numbers:
            print(f"  Found {len(numbers)} large numbers in page")
            for n in numbers[:5]:
                print(f"    {n}")

    # NCES enrollment
    print("\n[6] NCES Enrollment:")
    nces = DATA / "nces" / "enrollment_table.html"
    if nces.exists():
        content = nces.read_text(errors="replace")
        import re
        # Look for enrollment numbers
        matches = re.findall(r"([\d,]{7,})", content)
        if matches:
            print(f"  Found {len(matches)} large numbers")
            for m in matches[:5]:
                print(f"    {m}")

    # EPA MSW
    print("\n[7] EPA MSW Overview:")
    msw = DATA / "epa" / "msw_overview.html"
    if msw.exists():
        content = msw.read_text(errors="replace")
        import re
        matches = re.findall(r"([\d,.]+)\s*(?:million|billion)\s*(?:tons|short tons)", content, re.I)
        if matches:
            print(f"  Found tonnage figures: {matches[:5]}")
        else:
            print("  No tonnage figures found in HTML")

    # FHWA PDF - just confirm it exists
    print("\n[8] FHWA Vehicle Registrations PDF:")
    fhwa = DATA / "fhwa" / "vehicle_registrations_2022.pdf"
    if fhwa.exists():
        print(f"  File size: {fhwa.stat().st_size // 1024} KB")
        print("  (PDF - need pdfplumber/PyPDF2 to extract tables)")


if __name__ == "__main__":
    check_all()
