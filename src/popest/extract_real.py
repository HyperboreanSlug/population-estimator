"""Extract real numbers from downloaded HTML/PDF files and additional API calls."""

import json
import re
from pathlib import Path

import pandas as pd
import requests

DATA = Path("data")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def extract_and_download():
    results = {}

    # 1. EPA MSW - extract tonnage from HTML
    print("[1] EPA MSW tonnage from downloaded HTML...")
    msw = DATA / "epa" / "msw_overview.html"
    if msw.exists():
        content = msw.read_text(errors="replace")
        # Look for "292.4 million tons" pattern
        matches = re.findall(r"([\d,.]+)\s*million\s*(?:short\s*)?tons", content, re.I)
        if matches:
            results["epa_msw_million_tons"] = matches
            print(f"  Found: {matches}")
        # Also look for generation figures
        gen = re.findall(r"(?:generated|generation)[^<]*?([\d,.]+)\s*million", content, re.I)
        if gen:
            results["epa_msw_generation"] = gen
            print(f"  Generation figures: {gen}")

    # 2. NCES enrollment - extract from HTML
    print("\n[2] NCES enrollment from downloaded HTML...")
    nces = DATA / "nces" / "enrollment_table.html"
    if nces.exists():
        content = nces.read_text(errors="replace")
        # Look for table data with enrollment numbers
        # NCES tables typically have numbers like 49,900 (thousands)
        matches = re.findall(r"([\d,]{5,9})", content)
        large = [m for m in matches if len(m.replace(",", "")) >= 7]
        if large:
            results["nces_large_numbers"] = large[:10]
            print(f"  Large numbers found: {large[:10]}")
        # Try to find the specific enrollment figure
        enroll = re.findall(r"(?:enrollment|total)[^<]*?([\d,]+)", content, re.I)
        if enroll:
            results["nces_enrollment_mentions"] = enroll[:5]
            print(f"  Enrollment mentions: {enroll[:5]}")

    # 3. BLS - get total employment (not just ratio)
    print("\n[3] BLS total employment via API...")
    try:
        # LNS12000000 = total employed (thousands)
        r = requests.get(
            "https://api.bls.gov/publicAPI/v2/timeseries/data/LNS12000000",
            headers=HEADERS, timeout=30,
        )
        data = r.json()
        series = data.get("Results", {}).get("series", [])
        if series:
            pts = series[0].get("data", [])[:3]
            employed = [(p["year"], p["period"], p["value"]) for p in pts]
            results["bls_total_employed_thousands"] = employed
            print(f"  Total employed (thousands): {employed}")
            # Save
            (DATA / "bls").mkdir(parents=True, exist_ok=True)
            (DATA / "bls" / "total_employed.json").write_text(json.dumps(data, indent=2))
    except Exception as e:
        print(f"  FAIL: {e}")

    # 4. BLS labor force
    print("\n[4] BLS labor force via API...")
    try:
        # LNS11000000 = civilian labor force (thousands)
        r = requests.get(
            "https://api.bls.gov/publicAPI/v2/timeseries/data/LNS11000000",
            headers=HEADERS, timeout=30,
        )
        data = r.json()
        series = data.get("Results", {}).get("series", [])
        if series:
            pts = series[0].get("data", [])[:3]
            labor = [(p["year"], p["period"], p["value"]) for p in pts]
            results["bls_labor_force_thousands"] = labor
            print(f"  Labor force (thousands): {labor}")
            (DATA / "bls" / "labor_force.json").write_text(json.dumps(data, indent=2))
    except Exception as e:
        print(f"  FAIL: {e}")

    # 5. Census PEP - try without key (some endpoints allow it)
    print("\n[5] Census PEP national estimate...")
    try:
        r = requests.get(
            "https://api.census.gov/data/2023/pep/population?get=NAME,POP&for=us:1",
            headers=HEADERS, timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            results["census_pep_2023"] = data
            print(f"  PEP response: {data}")
            (DATA / "census").mkdir(parents=True, exist_ok=True)
            (DATA / "census" / "pep_2023_us.json").write_text(json.dumps(data))
        else:
            print(f"  Status {r.status_code}: needs API key")
    except Exception as e:
        print(f"  FAIL: {e}")

    # 6. CBP encounters - extract actual numbers
    print("\n[6] CBP encounter numbers from HTML...")
    cbp = DATA / "cbp" / "encounters_page.html"
    if cbp.exists():
        content = cbp.read_text(errors="replace")
        # Look for FY2023/2024 encounter totals
        fy_matches = re.findall(r"FY\s*(\d{4})[^<]*?([\d,]{6,})", content)
        if fy_matches:
            results["cbp_fy_encounters"] = fy_matches[:5]
            print(f"  FY encounters: {fy_matches[:5]}")
        # Look for monthly totals
        monthly = re.findall(r"([\d,]{6,9})", content)
        if monthly:
            results["cbp_large_numbers"] = monthly[:10]
            print(f"  Large numbers: {monthly[:10]}")

    # 7. EIA - try the open data API without key for basic info
    print("\n[7] EIA total electricity generation...")
    try:
        # Try the EIA open data endpoint
        r = requests.get(
            "https://api.eia.gov/v2/electricity/electric-power-operational-data/data/"
            "?frequency=annual&data[0]=generation&facets[fueltypeid][]=ALL"
            "&facets[fueltypeid][]=COW&facets[stateDescription][]=US"
            "&start=2022&end=2023&sort[0][column]=period&sort[0][direction]=desc",
            headers=HEADERS, timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            results["eia_generation"] = data.get("response", {}).get("data", [])[:3]
            print(f"  Generation data: {results['eia_generation']}")
        else:
            print(f"  Status {r.status_code} (likely needs API key)")
    except Exception as e:
        print(f"  FAIL: {e}")

    # 8. DHS immigration - extract from landing page
    print("\n[8] DHS yearbook data from landing page...")
    dhs = DATA / "dhs" / "yearbook_landing.html"
    if dhs.exists():
        content = dhs.read_text(errors="replace")
        # Look for links to actual data tables
        links = re.findall(r'href="([^"]*(?:yearbook|statistics|data)[^"]*)"', content, re.I)
        if links:
            results["dhs_data_links"] = links[:10]
            print(f"  Data links found: {len(links)}")
            for l in links[:5]:
                print(f"    {l}")

    print("\n" + "=" * 50)
    print("  EXTRACTION SUMMARY")
    print("=" * 50)
    for k, v in results.items():
        print(f"  {k}: {str(v)[:100]}")

    return results


if __name__ == "__main__":
    extract_and_download()
