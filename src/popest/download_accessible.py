"""Download remaining accessible sources found in page links.

Targets: EPA CWNS 2022 data, DHS yearbook tables, MS Building Footprints.
Full status echo per file. Verbose HTTP errors.
"""

import time
from pathlib import Path

import requests

DATA = Path("data")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
}
TIMEOUT = 120


def _dl(url: str, dest: Path, label: str) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 100:
        print(f"  [CACHED] {label} ({dest.stat().st_size // 1024} KB)")
        return True

    print(f"  [GET] {label}")
    start = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if resp.status_code != 200:
            print(f"  [FAIL] HTTP {resp.status_code}")
            print(f"         Server: {resp.headers.get('Server', 'N/A')}")
            print(f"         Body: {resp.text[:200]}")
            return False

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=256 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 2_000_000:
                    pct = downloaded / total * 100
                    elapsed = time.time() - start
                    rate = downloaded / elapsed / 1024 if elapsed > 0 else 0
                    print(f"\r        {downloaded//1024}/{total//1024} KB ({pct:.0f}%) {rate:.0f} KB/s", end="", flush=True)
        if total > 2_000_000:
            print()

        size = dest.stat().st_size
        print(f"  [OK] {size // 1024} KB in {time.time()-start:.1f}s")
        return size > 100

    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {str(e)[:200]}")
        return False


def download_accessible():
    print("=" * 60)
    print("  DOWNLOADING ACCESSIBLE SOURCES (from page links)")
    print("=" * 60)
    results = {}

    # EPA CWNS 2022 report and data
    print("\n--- EPA CWNS 2022 ---")
    results["cwns_2022"] = _dl(
        "https://www.epa.gov/cwns/clean-watersheds-needs-survey-cwns-2022-report-and-data",
        DATA / "epa" / "cwns_2022_report.html",
        "EPA CWNS 2022 report page",
    )

    # DHS Yearbook 2023 tables
    print("\n--- DHS Yearbook 2023 Tables ---")
    for i in range(1, 8):
        results[f"dhs_table{i}"] = _dl(
            f"https://ohss.dhs.gov/topics/immigration/yearbook/2023/table{i}",
            DATA / "dhs" / f"yearbook_2023_table{i}.html",
            f"DHS Yearbook 2023 Table {i}",
        )

    # MS Building Footprints - download a few key states
    print("\n--- MS Building Footprints (sample states) ---")
    base = "https://minedbuildings.z5.web.core.windows.net/legacy/usbuildings-v2"
    states = ["California", "Texas", "Florida", "NewYork", "Pennsylvania"]
    for state in states:
        results[f"bldg_{state}"] = _dl(
            f"{base}/{state}.geojson.zip",
            DATA / "buildings" / f"{state}.geojson.zip",
            f"MS Buildings: {state}",
        )

    # EPA CWNS past reports
    print("\n--- EPA CWNS Past Reports ---")
    results["cwns_past"] = _dl(
        "https://www.epa.gov/cwns/clean-watersheds-needs-survey-cwns-past-reports-and-data",
        DATA / "epa" / "cwns_past_reports.html",
        "EPA CWNS past reports page",
    )

    # NCES - try the CCD data page
    print("\n--- NCES CCD ---")
    results["nces_ccd"] = _dl(
        "https://nces.ed.gov/ccd/drf.asp",
        DATA / "nces" / "ccd_drf.html",
        "NCES CCD data files page",
    )

    # Census retail - try alternative URL
    print("\n--- Census Retail Alternative ---")
    results["census_retail2"] = _dl(
        "https://www.census.gov/retail/marts.html",
        DATA / "census" / "retail_marts.html",
        "Census retail MARTS page",
    )

    # AHRQ HCUP - try the main reports page
    print("\n--- AHRQ HCUP ---")
    results["ahrq_reports"] = _dl(
        "https://hcup-us.ahrq.gov/reports/statbriefs.jsp",
        DATA / "ahrq" / "statbriefs_page.html",
        "AHRQ stat briefs page",
    )

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    ok = sum(1 for v in results.values() if v)
    for k, v in sorted(results.items()):
        print(f"  [{'OK' if v else 'FAIL'}] {k}")
    print(f"\n  {ok}/{len(results)} downloaded")


if __name__ == "__main__":
    download_accessible()
