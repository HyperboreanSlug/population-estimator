"""Comprehensive download script - all remaining sources.

Echoes per-file status. Full HTTP error passthrough on failure.
Progress timer for large downloads.
"""

import json
import re
import sys
import time
from pathlib import Path

import requests

DATA = Path("data")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) population-estimator/0.1"}
TIMEOUT = 120


def _download(url: str, dest: Path, label: str) -> bool:
    """Download with full status echo and error passthrough."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 100:
        print(f"  [CACHED] {label}: {dest.name} ({dest.stat().st_size // 1024} KB)")
        return True

    print(f"  [GET] {label}: {url[:80]}...")
    start = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        elapsed = time.time() - start

        if resp.status_code != 200:
            body = resp.text[:500] if resp.text else "(empty)"
            print(f"  [FAIL] {label}: HTTP {resp.status_code} ({elapsed:.1f}s)")
            print(f"         Headers: {dict(list(resp.headers.items())[:5])}")
            print(f"         Body: {body[:200]}")
            return False

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 256):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 1_000_000:
                    pct = downloaded / total * 100
                    elapsed = time.time() - start
                    rate = downloaded / elapsed / 1024 if elapsed > 0 else 0
                    print(f"\r  [DL] {label}: {downloaded//1024}/{total//1024} KB "
                          f"({pct:.0f}%) {rate:.0f} KB/s", end="", flush=True)

        elapsed = time.time() - start
        size = dest.stat().st_size
        if total > 1_000_000:
            print()
        print(f"  [OK] {label}: {size // 1024} KB in {elapsed:.1f}s")
        return size > 100

    except requests.exceptions.ConnectionError as e:
        print(f"  [FAIL] {label}: ConnectionError: {str(e)[:150]}")
        return False
    except requests.exceptions.Timeout:
        print(f"  [FAIL] {label}: Timeout after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"  [FAIL] {label}: {type(e).__name__}: {str(e)[:150]}")
        return False


def download_remaining():
    print("=" * 60)
    print("  COMPREHENSIVE DOWNLOAD - ALL REMAINING SOURCES")
    print("=" * 60)

    results = {}

    # --- TIER 1: PHYSICAL ---

    print("\n--- TIER 1: PHYSICAL INFRASTRUCTURE ---")

    # EIA SEDS complete data (state energy)
    results["eia_seds"] = _download(
        "https://www.eia.gov/state/seds/seds-technical-notes-complete.php",
        DATA / "eia" / "seds_complete.html",
        "EIA SEDS complete",
    )

    # EIA electricity sales by sector (annual)
    results["eia_elec_sales"] = _download(
        "https://www.eia.gov/electricity/sales_revenue_price/xls/electricity_sales.xlsx",
        DATA / "eia" / "electricity_sales.xlsx",
        "EIA electricity sales",
    )

    # EIA natural gas consumption
    results["eia_gas"] = _download(
        "https://www.eia.gov/dnav/ng/hist/n9190us3a.htm",
        DATA / "eia" / "nat_gas_consumption.html",
        "EIA natural gas",
    )

    # EPA Clean Watersheds Needs Survey
    results["epa_cwns"] = _download(
        "https://www.epa.gov/cwns/clean-watersheds-needs-survey-cwns",
        DATA / "epa" / "cwns.html",
        "EPA CWNS",
    )

    # EPA MSW facts and figures
    results["epa_msw"] = _download(
        "https://www.epa.gov/facts-and-figures-about-materials-waste-and-recycling/national-overview-facts-and-figures-materials",
        DATA / "epa" / "msw_national_overview.html",
        "EPA MSW overview",
    )

    # --- TIER 2: HEALTHCARE ---

    print("\n--- TIER 2: HEALTHCARE ---")

    # CDC NCHS hospital data
    results["cdc_hospital"] = _download(
        "https://www.cdc.gov/nchs/data/hus/2023/table086.pdf",
        DATA / "cdc" / "hospital_utilization_2023.pdf",
        "CDC NCHS hospital utilization",
    )

    # AHRQ HCUP
    results["ahrq_hcup"] = _download(
        "https://hcup-us.ahrq.gov/reports/statbriefs/sb295-Hospital-Stays-2021.pdf",
        DATA / "ahrq" / "hcup_hospital_stays_2021.pdf",
        "AHRQ HCUP hospital stays",
    )

    # CDC births final data
    results["cdc_births"] = _download(
        "https://www.cdc.gov/nchs/data/vsrr/vsrr028.pdf",
        DATA / "cdc" / "births_final_2022.pdf",
        "CDC births final report",
    )

    # CDC deaths
    results["cdc_deaths"] = _download(
        "https://www.cdc.gov/nchs/data/vsrr/vsrr029.pdf",
        DATA / "cdc" / "deaths_final_2022.pdf",
        "CDC deaths final report",
    )

    # --- TIER 3: CONSUMPTION ---

    print("\n--- TIER 3: CONSUMPTION ---")

    # Census retail trade food sales
    results["census_retail"] = _download(
        "https://www.census.gov/retail/marts/marts_current.xlsx",
        DATA / "census" / "retail_trade_current.xlsx",
        "Census retail trade",
    )

    # CTIA wireless data
    results["ctia_wireless"] = _download(
        "https://www.ctia.org/news/ctia-year-end-survey-results",
        DATA / "ctia" / "wireless_survey.html",
        "CTIA wireless survey",
    )

    # --- TIER 4: ADMINISTRATIVE ---

    print("\n--- TIER 4: ADMINISTRATIVE ---")

    # IRS SOI ZIP data (large CSV)
    results["irs_soi"] = _download(
        "https://www.irs.gov/pub/irs-soi/22zpallagi.csv",
        DATA / "irs" / "soi_zip_2022.csv",
        "IRS SOI ZIP data (TY2022)",
    )

    # DHS yearbook via ohss.dhs.gov
    results["dhs_yearbook"] = _download(
        "https://ohss.dhs.gov/topics/immigration/yearbook",
        DATA / "dhs" / "yearbook_page.html",
        "DHS yearbook page",
    )

    # DHS yearbook table 1 (total LPR)
    results["dhs_table1"] = _download(
        "https://ohss.dhs.gov/sites/default/files/statistics/yearbook/2023/Table01.pdf",
        DATA / "dhs" / "yearbook_2023_table01.pdf",
        "DHS yearbook Table 1",
    )

    # CBP encounters data
    results["cbp_data"] = _download(
        "https://www.cbp.gov/newsroom/stats/southwest-land-border-encounters",
        DATA / "cbp" / "encounters.html",
        "CBP encounters page",
    )

    # Census PEP via API (try without key)
    results["census_pep"] = _download(
        "https://api.census.gov/data/2023/pep/population?get=NAME,POP&for=us:1",
        DATA / "census" / "pep_us.json",
        "Census PEP API",
    )

    # NCES enrollment data file
    results["nces_enroll"] = _download(
        "https://nces.ed.gov/ccd/Data/txt/nflc01a.txt",
        DATA / "nces" / "enrollment_raw.txt",
        "NCES enrollment data",
    )

    # NCES digest table
    results["nces_digest"] = _download(
        "https://nces.ed.gov/programs/digest/d23/tables/dt23_203.10.asp",
        DATA / "nces" / "digest_enrollment.html",
        "NCES digest table 203.10",
    )

    # CMS Medicare enrollment
    results["cms_medicare"] = _download(
        "https://data.cms.gov/data-files/dataset/medicare-enrollment/enrollment-by-county/data",
        DATA / "cms" / "medicare_by_county.csv",
        "CMS Medicare by county",
    )

    # --- TIER 5: GEOSPATIAL ---

    print("\n--- TIER 5: GEOSPATIAL ---")

    # Microsoft building footprints summary
    results["ms_buildings"] = _download(
        "https://raw.githubusercontent.com/microsoft/USBuildingFootprints/main/README.md",
        DATA / "buildings" / "ms_footprints_readme.md",
        "MS Building Footprints README",
    )

    # --- SUMMARY ---

    print("\n" + "=" * 60)
    print("  FINAL DOWNLOAD SUMMARY")
    print("=" * 60)
    ok = sum(1 for v in results.values() if v)
    fail = sum(1 for v in results.values() if not v)
    for name, status in sorted(results.items()):
        icon = "OK  " if status else "FAIL"
        print(f"  [{icon}] {name}")
    print(f"\n  Total: {ok} OK, {fail} FAILED out of {len(results)}")
    return results


if __name__ == "__main__":
    download_remaining()
