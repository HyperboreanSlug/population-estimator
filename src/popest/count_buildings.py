"""Count buildings in downloaded GeoJSON files and extract DHS/CBP numbers."""

import json
import re
import zipfile
from pathlib import Path

DATA = Path("data")


def count_buildings():
    """Count building features in each state GeoJSON ZIP."""
    print("=" * 60)
    print("  BUILDING FOOTPRINT COUNTS (from downloaded GeoJSON)")
    print("=" * 60)

    buildings_dir = DATA / "buildings"
    total = 0
    results = {}

    for zf_path in sorted(buildings_dir.glob("*.geojson.zip")):
        state = zf_path.stem.replace(".geojson", "")
        print(f"  Counting {state}...", end=" ", flush=True)
        try:
            with zipfile.ZipFile(zf_path) as zf:
                names = zf.namelist()
                geojson_name = names[0]
                count = 0
                with zf.open(geojson_name) as f:
                    # Count "Feature" occurrences in chunks
                    buffer = b""
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        buffer += chunk
                        count += buffer.count(b'"type": "Feature"')
                        count += buffer.count(b'"type":"Feature"')
                        buffer = buffer[-50:]
                results[state] = count
                total += count
                print(f"{count:,} buildings")
        except Exception as e:
            print(f"ERROR: {e}")
            results[state] = 0

    print(f"\n  TOTAL (5 states): {total:,}")
    print(f"  Source: data/buildings/*.geojson.zip (Microsoft USBuildingFootprints)")
    return results


def extract_dhs():
    """Extract immigration numbers from DHS yearbook tables."""
    print("\n" + "=" * 60)
    print("  DHS YEARBOOK 2023 - KEY FIGURES")
    print("=" * 60)

    # Table 1: Persons Obtaining Legal Permanent Resident Status
    t1 = DATA / "dhs" / "yearbook_2023_table1.html"
    if t1.exists():
        content = t1.read_text(errors="replace")
        # Look for total LPR number
        nums = re.findall(r"([\d,]{6,})", content)
        if nums:
            print(f"  Table 1 (LPR): large numbers found: {nums[:5]}")
            print(f"  Source: data/dhs/yearbook_2023_table1.html")

    # Table 2: Naturalizations
    t2 = DATA / "dhs" / "yearbook_2023_table2.html"
    if t2.exists():
        content = t2.read_text(errors="replace")
        nums = re.findall(r"([\d,]{6,})", content)
        if nums:
            print(f"  Table 2 (Naturalizations): {nums[:5]}")

    # Table 3: Nonimmigrant admissions
    t3 = DATA / "dhs" / "yearbook_2023_table3.html"
    if t3.exists():
        content = t3.read_text(errors="replace")
        nums = re.findall(r"([\d,]{6,})", content)
        if nums:
            print(f"  Table 3 (Nonimmigrants): {nums[:5]}")


def extract_cbp():
    """Extract CBP encounter numbers."""
    print("\n" + "=" * 60)
    print("  CBP ENCOUNTERS - KEY FIGURES")
    print("=" * 60)

    cbp = DATA / "cbp" / "encounters.html"
    if cbp.exists():
        content = cbp.read_text(errors="replace")
        # Look for FY totals
        fy_matches = re.findall(r"FY\s*(\d{4})[^<]*?([\d,]{6,})", content)
        if fy_matches:
            for fy, num in fy_matches[:5]:
                print(f"  FY{fy}: {num}")
        # Look for monthly/annual totals
        nums = re.findall(r"([\d,]{7,})", content)
        if nums:
            print(f"  Large numbers in page: {nums[:8]}")
        print(f"  Source: data/cbp/encounters.html")


def extract_epa_cwns():
    """Extract EPA CWNS 2022 capacity data."""
    print("\n" + "=" * 60)
    print("  EPA CWNS 2022 - KEY FIGURES")
    print("=" * 60)

    cwns = DATA / "epa" / "cwns_2022_report.html"
    if cwns.exists():
        content = cwns.read_text(errors="replace")
        # Look for billion/million dollar figures
        dollars = re.findall(r"\$\s*([\d,.]+)\s*(billion|million)", content, re.I)
        if dollars:
            print(f"  Dollar figures: {dollars[:5]}")
        # Look for capacity figures
        cap = re.findall(r"([\d,.]+)\s*(?:billion|million)\s*gallons", content, re.I)
        if cap:
            print(f"  Capacity: {cap[:5]}")
        # Look for population served
        pop = re.findall(r"([\d,.]+)\s*million\s*(?:people|persons|population)", content, re.I)
        if pop:
            print(f"  Population served: {pop[:5]}")
        print(f"  Source: data/epa/cwns_2022_report.html")


if __name__ == "__main__":
    count_buildings()
    extract_dhs()
    extract_cbp()
    extract_epa_cwns()
