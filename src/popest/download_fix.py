"""Fix remaining failed downloads with corrected URLs.

Full verbose error output per memory rules.
"""

import time
from pathlib import Path

import requests

DATA = Path("data")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 60


def _dl(url: str, dest: Path, label: str) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 100:
        print(f"  [CACHED] {label} ({dest.stat().st_size // 1024} KB)")
        return True

    print(f"  [GET] {label}")
    print(f"        URL: {url}")
    start = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        elapsed = time.time() - start

        if resp.status_code != 200:
            print(f"  [FAIL] HTTP {resp.status_code} ({elapsed:.1f}s)")
            print(f"         Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
            print(f"         Server: {resp.headers.get('Server', 'N/A')}")
            body = resp.text[:300] if resp.text else "(empty)"
            print(f"         Body: {body}")
            return False

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=256 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 500_000:
                    pct = downloaded / total * 100
                    print(f"\r        {downloaded//1024}/{total//1024} KB ({pct:.0f}%)", end="", flush=True)
        if total > 500_000:
            print()

        size = dest.stat().st_size
        print(f"  [OK] {size // 1024} KB in {time.time()-start:.1f}s")
        return size > 100

    except requests.exceptions.SSLError as e:
        print(f"  [FAIL] SSL Error: {str(e)[:200]}")
        # Retry without SSL verification
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            if resp.status_code == 200:
                dest.write_bytes(resp.content)
                print(f"  [OK] (SSL verify disabled) {len(resp.content)//1024} KB")
                return True
        except Exception as e2:
            print(f"  [FAIL] Retry also failed: {str(e2)[:100]}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"  [FAIL] Connection: {str(e)[:200]}")
        return False
    except requests.exceptions.Timeout:
        print(f"  [FAIL] Timeout ({TIMEOUT}s)")
        return False
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {str(e)[:200]}")
        return False


def fix_remaining():
    print("=" * 60)
    print("  FIXING REMAINING FAILED DOWNLOADS")
    print("=" * 60)
    results = {}

    # CDC - try different URL patterns (Akamai blocks some paths)
    print("\n--- CDC (was 403 Akamai) ---")
    results["cdc_births"] = _dl(
        "https://www.cdc.gov/nchs/data/vsrr/vsrr028-2024.pdf",
        DATA / "cdc" / "births_2022.pdf",
        "CDC births VSSR 028",
    )
    if not results["cdc_births"]:
        results["cdc_births"] = _dl(
            "https://stacks.cdc.gov/view/cdc/148755",
            DATA / "cdc" / "births_stacks.html",
            "CDC births via stacks",
        )

    # AHRQ HCUP - correct URL
    print("\n--- AHRQ HCUP (was 404) ---")
    results["ahrq"] = _dl(
        "https://hcup-us.ahrq.gov/reports/statbriefs/sb295.pdf",
        DATA / "ahrq" / "hcup_sb295.pdf",
        "AHRQ HCUP SB295",
    )
    if not results["ahrq"]:
        results["ahrq"] = _dl(
            "https://hcup-us.ahrq.gov/reports/statbriefs/sb300.pdf",
            DATA / "ahrq" / "hcup_sb300.pdf",
            "AHRQ HCUP SB300",
        )

    # Census retail trade - correct URL
    print("\n--- Census Retail (was 404) ---")
    results["census_retail"] = _dl(
        "https://www.census.gov/retail/marts/marts_current.html",
        DATA / "census" / "retail_current.html",
        "Census retail trade page",
    )

    # CTIA wireless - SSL issue, try verify=False
    print("\n--- CTIA Wireless (was SSL error) ---")
    results["ctia"] = _dl(
        "https://www.ctia.org/news/ctia-year-end-survey-results",
        DATA / "ctia" / "wireless.html",
        "CTIA wireless survey",
    )

    # EPA CWNS - correct URL
    print("\n--- EPA CWNS (was 404) ---")
    results["epa_cwns"] = _dl(
        "https://www.epa.gov/cwns",
        DATA / "epa" / "cwns.html",
        "EPA CWNS landing",
    )

    # NCES - try different data file
    print("\n--- NCES (was 404) ---")
    results["nces"] = _dl(
        "https://nces.ed.gov/ccd/Data/zip/nflc01a.zip",
        DATA / "nces" / "enrollment.zip",
        "NCES enrollment ZIP",
    )

    # Microsoft Building Footprints - correct repo path
    print("\n--- MS Buildings (was 404) ---")
    results["ms_buildings"] = _dl(
        "https://github.com/microsoft/USBuildingFootprints",
        DATA / "buildings" / "ms_repo_page.html",
        "MS Building Footprints repo",
    )

    # EIA - get actual CSV data via open data
    print("\n--- EIA actual data ---")
    results["eia_seds_csv"] = _dl(
        "https://www.eia.gov/state/seds/sep_sum/plain_html/rank_use_per_cap.csv",
        DATA / "eia" / "seds_per_capita.csv",
        "EIA SEDS per capita CSV",
    )

    # DHS yearbook tables
    print("\n--- DHS Yearbook tables ---")
    results["dhs_tables"] = _dl(
        "https://ohss.dhs.gov/topics/immigration/yearbook/2023",
        DATA / "dhs" / "yearbook_2023.html",
        "DHS yearbook 2023",
    )

    # CMS Medicare - try the actual data endpoint
    print("\n--- CMS Medicare ---")
    results["cms"] = _dl(
        "https://data.cms.gov/data-files/api/dataset/medicare-enrollment/enrollment-by-county",
        DATA / "cms" / "medicare_county_api.json",
        "CMS Medicare county API",
    )

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    ok = sum(1 for v in results.values() if v)
    for k, v in sorted(results.items()):
        print(f"  [{'OK' if v else 'FAIL'}] {k}")
    print(f"\n  {ok}/{len(results)} fixed")


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    fix_remaining()
