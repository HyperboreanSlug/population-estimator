"""Download ALL remaining sources not yet attempted.

Full status echo. Verbose HTTP errors. Progress for large files.
"""

import time
from pathlib import Path

import requests

DATA = Path("data")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
}
TIMEOUT = 300


def _dl(url: str, dest: Path, label: str, max_mb: int = 0) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 100:
        print(f"  [CACHED] {label} ({dest.stat().st_size // 1024} KB)")
        return True

    print(f"  [GET] {label}")
    print(f"        {url[:100]}")
    start = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if resp.status_code != 200:
            print(f"  [FAIL] HTTP {resp.status_code} ({time.time()-start:.1f}s)")
            print(f"         Server: {resp.headers.get('Server', 'N/A')}")
            print(f"         Body: {resp.text[:200]}")
            return False

        total = int(resp.headers.get("content-length", 0))
        if max_mb and total > max_mb * 1024 * 1024:
            print(f"  [SKIP] File too large: {total // (1024*1024)} MB (limit {max_mb} MB)")
            return False

        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=512 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 5_000_000:
                    pct = downloaded / total * 100
                    elapsed = time.time() - start
                    rate = downloaded / elapsed / (1024 * 1024) if elapsed > 0 else 0
                    print(f"\r        {downloaded//(1024*1024)}/{total//(1024*1024)} MB ({pct:.0f}%) {rate:.1f} MB/s", end="", flush=True)
        if total > 5_000_000:
            print()

        size = dest.stat().st_size
        print(f"  [OK] {size // 1024} KB in {time.time()-start:.1f}s")
        return size > 100

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


def download_all_remaining():
    print("=" * 60)
    print("  DOWNLOADING ALL REMAINING SOURCES")
    print("=" * 60)
    results = {}

    # === EPA NPDES DMR (pollutant loads - nitrogen, BOD, ammonia) ===
    print("\n--- EPA NPDES DMR (wastewater chemistry) ---")
    results["epa_dmr_fy2024"] = _dl(
        "https://echo.epa.gov/files/echodownloads/npdes_dmrs_fy2024.zip",
        DATA / "epa" / "npdes_dmrs_fy2024.zip",
        "EPA DMR FY2024 (612 MB)",
    )
    results["epa_dmr_fy2023"] = _dl(
        "https://echo.epa.gov/files/echodownloads/npdes_dmrs_fy2023.zip",
        DATA / "epa" / "npdes_dmrs_fy2023.zip",
        "EPA DMR FY2023 (596 MB)",
    )
    results["epa_npdes_part2"] = _dl(
        "https://echo.epa.gov/files/echodownloads/npdes_eff_downloads.zip",
        DATA / "epa" / "npdes_eff_downloads.zip",
        "EPA NPDES Part 2 effluent (2.5 GB)",
        max_mb=3000,
    )
    results["epa_npdes_limits"] = _dl(
        "https://echo.epa.gov/files/echodownloads/npdes_limits.zip",
        DATA / "epa" / "npdes_limits.zip",
        "EPA NPDES permit limits (459 MB)",
    )

    # === CDC via data.cdc.gov (Socrata API) ===
    print("\n--- CDC via data.cdc.gov API ---")
    results["cdc_births_api"] = _dl(
        "https://data.cdc.gov/api/views/vx9v-mkgr/rows.csv?accessType=DOWNLOAD",
        DATA / "cdc" / "births_data.csv",
        "CDC births via data.cdc.gov",
    )
    results["cdc_deaths_api"] = _dl(
        "https://data.cdc.gov/api/views/76vk-y2ir/rows.csv?accessType=DOWNLOAD",
        DATA / "cdc" / "deaths_data.csv",
        "CDC deaths via data.cdc.gov",
    )
    results["cdc_hospital_api"] = _dl(
        "https://data.cdc.gov/api/views/g62h-syeh/rows.csv?accessType=DOWNLOAD",
        DATA / "cdc" / "hospital_data.csv",
        "CDC hospital data via data.cdc.gov",
    )
    results["cdc_wonder_natality"] = _dl(
        "https://data.cdc.gov/api/views/n8mc-b4w4/rows.csv?accessType=DOWNLOAD",
        DATA / "cdc" / "natality.csv",
        "CDC natality via data.cdc.gov",
    )

    # === USDA via alternative endpoints ===
    print("\n--- USDA alternative endpoints ---")
    results["usda_snap_api"] = _dl(
        "https://data.usda.gov/api/catalog/search?q=SNAP+participation",
        DATA / "usda" / "snap_search.json",
        "USDA SNAP via data.usda.gov",
    )
    results["usda_food_api"] = _dl(
        "https://data.usda.gov/api/catalog/search?q=food+availability+per+capita",
        DATA / "usda" / "food_search.json",
        "USDA food via data.usda.gov",
    )
    results["usda_nass_api"] = _dl(
        "https://quickstats.nass.usda.gov/api/api_GET/?key=DEMO&commodity_desc=CORN&year=2022&agg_level_desc=NATIONAL&format=CSV",
        DATA / "usda" / "nass_test.csv",
        "USDA NASS Quick Stats",
    )

    # === Geospatial: WorldPop ===
    print("\n--- WorldPop population rasters ---")
    results["worldpop_usa"] = _dl(
        "https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/USA/usa_ppp_2020_constrained.tif",
        DATA / "geospatial" / "worldpop_usa_2020.tif",
        "WorldPop USA 2020 constrained",
        max_mb=500,
    )
    results["worldpop_usa_unconstrained"] = _dl(
        "https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/USA/usa_ppp_2020_UNconstrained.tif",
        DATA / "geospatial" / "worldpop_usa_2020_unconstrained.tif",
        "WorldPop USA 2020 unconstrained",
        max_mb=500,
    )

    # === Geospatial: NASA VIIRS ===
    print("\n--- NASA VIIRS nighttime lights ---")
    results["viirs"] = _dl(
        "https://eogdata.mines.edu/nighttime_light/annual/v10/2022/vcmsl_v10_c202201_global_vcmsl_v10_c202201_750m.tif",
        DATA / "geospatial" / "viirs_2022.tif",
        "NASA VIIRS 2022 annual",
        max_mb=200,
    )
    results["viirs_usa"] = _dl(
        "https://eogdata.mines.edu/nighttime_light/annual/v10/2022/vcmsl_v10_c202201_750m.tif",
        DATA / "geospatial" / "viirs_2022_alt.tif",
        "NASA VIIRS 2022 alt URL",
        max_mb=200,
    )

    # === Meta Data for Good ===
    print("\n--- Meta Data for Good ---")
    results["meta_pop"] = _dl(
        "https://data.humdata.org/dataset/united-states-high-resolution-population-density",
        DATA / "geospatial" / "meta_hdx_page.html",
        "Meta population via HDX page",
    )

    # === USPS ===
    print("\n--- USPS delivery data ---")
    results["usps"] = _dl(
        "https://www.usps.com/nationalpremieraccounts/findzipcodes.htm",
        DATA / "usps" / "zipcodes_page.html",
        "USPS ZIP codes page",
    )
    results["usps_county"] = _dl(
        "https://www.unitedstateszipcodes.org/county/",
        DATA / "usps" / "county_zip_list.html",
        "USPS county ZIP listing",
    )

    # === Pharmacy data ===
    print("\n--- Pharmacy dispensing ---")
    results["pharmacy_cdc"] = _dl(
        "https://data.cdc.gov/api/views/bi63-tpyu/rows.csv?accessType=DOWNLOAD",
        DATA / "pharmacy" / "cdc_pharmacy.csv",
        "CDC pharmacy data",
    )
    results["pharmacy_ims"] = _dl(
        "https://www.iqvia.com/insights/the-iqvia-institute/reports-and-publications",
        DATA / "pharmacy" / "iqvia_page.html",
        "IQVIA reports page",
    )

    # === EIA total energy ===
    print("\n--- EIA total energy ---")
    results["eia_total"] = _dl(
        "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T01.01",
        DATA / "eia" / "total_energy_monthly.csv",
        "EIA total energy monthly CSV",
    )
    results["eia_state_total"] = _dl(
        "https://www.eia.gov/state/seds/seds-technical-notes-complete.php",
        DATA / "eia" / "seds_state_total.html",
        "EIA SEDS state total",
    )

    # === Census retail trade ===
    print("\n--- Census retail trade ---")
    results["census_retail_api"] = _dl(
        "https://api.census.gov/data/2022/cps/basic/dec?get=PEEDUCA&for=us",
        DATA / "census" / "retail_api_attempt.json",
        "Census retail API attempt",
    )
    results["census_retail_page"] = _dl(
        "https://www.census.gov/retail/index.html",
        DATA / "census" / "retail_index.html",
        "Census retail index page",
    )

    # === CMS Medicare actual data ===
    print("\n--- CMS Medicare actual data ---")
    results["cms_enrollment_csv"] = _dl(
        "https://data.cms.gov/data-files/api/dataset/medicare-enrollment/enrollment-by-county/data?limit=10000",
        DATA / "cms" / "medicare_enrollment_data.csv",
        "CMS Medicare enrollment data",
    )
    results["cms_summary"] = _dl(
        "https://data.cms.gov/data-files/api/dataset/medicare-enrollment/enrollment-by-county/meta",
        DATA / "cms" / "medicare_meta.json",
        "CMS Medicare metadata",
    )

    # === NCES enrollment actual data ===
    print("\n--- NCES enrollment data ---")
    results["nces_api"] = _dl(
        "https://nces.ed.gov/ccd/Data/txt/nflc01a.txt",
        DATA / "nces" / "nflc01a.txt",
        "NCES enrollment text file",
    )
    results["nces_api2"] = _dl(
        "https://nces.ed.gov/ccd/Data/zip/nflc01a.zip",
        DATA / "nces" / "nflc01a.zip",
        "NCES enrollment ZIP",
    )
    results["nces_api3"] = _dl(
        "https://nces.ed.gov/ccd/Data/txt/pccd01a.txt",
        DATA / "nces" / "pccd01a.txt",
        "NCES CCD directory",
    )

    # === State water quality ===
    print("\n--- State water quality ---")
    results["state_water"] = _dl(
        "https://www.epa.gov/waterdata/water-quality-data",
        DATA / "epa" / "water_quality_data_page.html",
        "EPA water quality data page",
    )
    results["epa_wqx"] = _dl(
        "https://www.epa.gov/waterdata/storage-and-retrieval-store",
        DATA / "epa" / "storet_page.html",
        "EPA STORET page",
    )

    # === EPA NPDES outfalls ===
    print("\n--- EPA NPDES outfalls ---")
    results["epa_outfalls"] = _dl(
        "https://echo.epa.gov/files/echodownloads/npdes_outfalls_layer.zip",
        DATA / "epa" / "npdes_outfalls.zip",
        "EPA NPDES outfalls (50 MB)",
    )

    # === ECHO Exporter (all facilities) ===
    print("\n--- ECHO Exporter ---")
    results["echo_exporter"] = _dl(
        "https://echo.epa.gov/files/echodownloads/echo_exporter.zip",
        DATA / "epa" / "echo_exporter.zip",
        "ECHO Exporter (392 MB)",
    )

    # === SUMMARY ===
    print("\n" + "=" * 60)
    print("  FINAL RESULTS")
    print("=" * 60)
    ok = sum(1 for v in results.values() if v)
    fail = sum(1 for v in results.values() if not v)
    for k, v in sorted(results.items()):
        print(f"  [{'OK' if v else 'FAIL'}] {k}")
    print(f"\n  {ok} OK, {fail} FAILED out of {len(results)}")


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    download_all_remaining()
