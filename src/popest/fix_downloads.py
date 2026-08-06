"""Fix broken downloads with corrected URLs.

Targets: EIA SEDS/petroleum, CMS Medicare, Census retail,
CTIA/FCC wireless, CDC natality (correct view ID).
Full status echo. Verbose errors.
"""

import json
import time
from pathlib import Path

import requests

DATA = Path("data")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
}
TIMEOUT = 120


def _dl(url: str, dest: Path, label: str) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 500:
        print(f"  [CACHED] {label} ({dest.stat().st_size // 1024} KB)")
        return True

    print(f"  [GET] {label}")
    print(f"        {url[:110]}")
    start = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if resp.status_code != 200:
            print(f"  [FAIL] HTTP {resp.status_code} ({time.time()-start:.1f}s)")
            print(f"         Server: {resp.headers.get('Server', 'N/A')}")
            print(f"         Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
            print(f"         Body: {resp.text[:200]}")
            return False

        ct = resp.headers.get("Content-Type", "")
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=256 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 5_000_000:
                    pct = downloaded / total * 100
                    print(f"\r        {downloaded//(1024*1024)}/{total//(1024*1024)} MB ({pct:.0f}%)", end="", flush=True)
        if total > 5_000_000:
            print()

        size = dest.stat().st_size
        print(f"  [OK] {size // 1024} KB in {time.time()-start:.1f}s (type: {ct[:40]})")
        return size > 500

    except requests.exceptions.SSLError as e:
        print(f"  [FAIL] SSL: {str(e)[:150]}")
        try:
            import urllib3
            urllib3.disable_warnings()
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            if resp.status_code == 200:
                dest.write_bytes(resp.content)
                print(f"  [OK] (no SSL verify) {len(resp.content)//1024} KB")
                return True
        except Exception as e2:
            print(f"  [FAIL] Retry: {str(e2)[:100]}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"  [FAIL] Connection: {str(e)[:150]}")
        return False
    except requests.exceptions.Timeout:
        print(f"  [FAIL] Timeout ({TIMEOUT}s)")
        return False
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {str(e)[:150]}")
        return False


def fix_all():
    print("=" * 60)
    print("  FIXING BROKEN DOWNLOADS")
    print("=" * 60)
    results = {}

    # === 1. EIA SEDS per-capita energy (correct CSV endpoint) ===
    print("\n--- EIA SEDS per-capita (was HTML, need CSV) ---")
    # Try the actual data download endpoint
    results["eia_seds_csv"] = _dl(
        "https://www.eia.gov/state/seds/seds-data-complete.php?sid=US",
        DATA / "eia" / "seds_data_complete_us.html",
        "EIA SEDS complete data US",
    )
    # Try the API endpoint for state energy
    results["eia_api_state"] = _dl(
        "https://api.eia.gov/v2/state-energy/data/?frequency=annual&data[0]=value&facets[series][]=ETCBC&start=2022&end=2022",
        DATA / "eia" / "state_energy_api.json",
        "EIA state energy API (no key)",
    )
    # Try direct SEDS CSV download
    results["eia_seds_download"] = _dl(
        "https://www.eia.gov/state/seds/seds-technical-notes-complete.php",
        DATA / "eia" / "seds_notes_v2.html",
        "EIA SEDS notes",
    )

    # === 2. EIA petroleum/gasoline (was 404) ===
    print("\n--- EIA Petroleum/Gasoline (was 404) ---")
    results["eia_petrol_hist"] = _dl(
        "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=MWGFPUS2&f=A",
        DATA / "eia" / "gasoline_history_v2.csv",
        "EIA gasoline history (annual)",
    )
    results["eia_petrol_supply"] = _dl(
        "https://www.eia.gov/petroleum/supply/annual/xlsstp/mc12.xlsx",
        DATA / "eia" / "petrol_supply_annual.xlsx",
        "EIA petroleum supply annual XLSX",
    )
    results["eia_petrol_weekly"] = _dl(
        "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=WGFUPUS2&f=W",
        DATA / "eia" / "gasoline_weekly.csv",
        "EIA gasoline weekly",
    )

    # === 3. CMS Medicare (was JS shell) ===
    print("\n--- CMS Medicare (was JS app shell) ---")
    # Try the Socrata-style API that data.cms.gov uses
    results["cms_socrata"] = _dl(
        "https://data.cms.gov/api/views/ke7f-2gxm/rows.csv?accessType=DOWNLOAD",
        DATA / "cms" / "medicare_enrollment_socrata.csv",
        "CMS Medicare via Socrata API",
    )
    # Try the data-files API with different endpoint
    results["cms_api_v2"] = _dl(
        "https://data.cms.gov/data-files/api/dataset/medicare-enrollment/enrollment-by-county/data",
        DATA / "cms" / "medicare_enrollment_v2.json",
        "CMS Medicare data-files API",
    )
    # Try the provider data
    results["cms_provider"] = _dl(
        "https://data.cms.gov/api/views/xubh-q36u/rows.csv?accessType=DOWNLOAD",
        DATA / "cms" / "cms_provider_data.csv",
        "CMS provider data",
    )

    # === 4. Census retail trade (was HTML, no data) ===
    print("\n--- Census Retail Trade (was HTML) ---")
    # Try the Census API for retail trade
    results["census_retail_api"] = _dl(
        "https://api.census.gov/data/2022/cps/basic/dec?get=PEEDUCA&for=us",
        DATA / "census" / "retail_api_v2.json",
        "Census retail API attempt",
    )
    # Try the economic census
    results["census_eco"] = _dl(
        "https://api.census.gov/data/2017/ecn/basic?get=EMP,PAYANN&for=us&NAICS2017=445",
        DATA / "census" / "retail_economic.json",
        "Census economic retail (NAICS 445)",
    )
    # Try the monthly retail trade report
    results["census_marts"] = _dl(
        "https://www.census.gov/retail/marts/marts_current.html",
        DATA / "census" / "retail_marts_v2.html",
        "Census MARTS current",
    )

    # === 5. FCC/CTIA wireless (was redirect) ===
    print("\n--- FCC Wireless (CTIA was redirect) ---")
    results["fcc_wireless"] = _dl(
        "https://www.fcc.gov/reports-research/reports/wireless-competition-reports",
        DATA / "fcc" / "wireless_competition.html",
        "FCC wireless competition reports",
    )
    results["fcc_data"] = _dl(
        "https://opendata.fcc.gov/api/views/53w8-7wzi/rows.csv?accessType=DOWNLOAD",
        DATA / "fcc" / "fcc_broadband.csv",
        "FCC broadband data (Socrata)",
    )
    results["ctia_retry"] = _dl(
        "https://www.ctia.org/the-wireless-industry/state-of-the-wireless-industry",
        DATA / "ctia" / "state_of_wireless.html",
        "CTIA state of wireless",
    )

    # === 6. CDC natality (wrong view ID last time) ===
    print("\n--- CDC Natality (was wrong dataset) ---")
    # Search for the correct natality dataset on data.cdc.gov
    results["cdc_search"] = _dl(
        "https://data.cdc.gov/api/catalog/search?q=natality&limit=5",
        DATA / "cdc" / "natality_search.json",
        "CDC natality catalog search",
    )
    # Try known natality view IDs
    results["cdc_natality_v2"] = _dl(
        "https://data.cdc.gov/api/views/n8mc-b4w4/rows.csv?accessType=DOWNLOAD&$limit=100",
        DATA / "cdc" / "natality_v2.csv",
        "CDC natality view n8mc-b4w4",
    )
    results["cdc_natality_v3"] = _dl(
        "https://data.cdc.gov/api/views/vx9v-mkgr/rows.csv?accessType=DOWNLOAD&$limit=100",
        DATA / "cdc" / "natality_v3.csv",
        "CDC natality view vx9v-mkgr",
    )
    # Try CDC WONDER alternative
    results["cdc_wonder_alt"] = _dl(
        "https://wonder.cdc.gov/controller/datarequest/D66",
        DATA / "cdc" / "wonder_d66.html",
        "CDC WONDER D66 page",
    )

    # === 7. EIA electricity by state (bulk download) ===
    print("\n--- EIA Electricity by State (bulk) ---")
    results["eia_elec_state"] = _dl(
        "https://www.eia.gov/electricity/data/state/xls/annual_state_emissions.xlsx",
        DATA / "eia" / "state_emissions.xlsx",
        "EIA state emissions XLSX",
    )
    results["eia_elec_sales2"] = _dl(
        "https://www.eia.gov/electricity/sales_revenue_price/xls/electricity_sales.xlsx",
        DATA / "eia" / "electricity_sales_v2.xlsx",
        "EIA electricity sales XLSX",
    )

    # === SUMMARY ===
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    ok = sum(1 for v in results.values() if v)
    fail = sum(1 for v in results.values() if not v)
    for k, v in sorted(results.items()):
        print(f"  [{'OK' if v else 'FAIL'}] {k}")
    print(f"\n  {ok} OK, {fail} FAILED out of {len(results)}")


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    fix_all()
