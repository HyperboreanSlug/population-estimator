"""Canonical manifest-driven data downloader.

One entry point for every external source: `popest download` (core files
needed by the estimation pipeline) and `popest download --all` (the full
exploration catalog from PLAN.md tiers 1-5).

Per-file status echo on the command line. Full HTTP error passthrough on
failure (status, server header, body head). Progress line for large files.
Files are cached: a path that exists with content is not re-downloaded.

URLs merged from the former download_* family of one-off scripts.
"""

import time
from pathlib import Path

import requests

DATA = Path("data")
TIMEOUT = 300
HEADERS = {
    "User-Agent": "population-estimator/0.1 (open-data research client)",
    "Accept": "*/*",
}


def _download(url: str, dest: Path, label: str, max_mb: int = 0) -> bool:
    """Fetch one URL to dest with status echo. Returns True on success."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 100:
        print(f"  [CACHED] {label} ({dest.stat().st_size // 1024} KB)")
        return True

    print(f"  [GET] {label}")
    print(f"        {url[:110]}")
    start = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if resp.status_code != 200:
            print(f"  [FAIL] HTTP {resp.status_code} ({time.time() - start:.1f}s)")
            print(f"         Server: {resp.headers.get('Server', 'N/A')}")
            print(f"         Body: {resp.text[:300]!r}")
            return False

        total = int(resp.headers.get("content-length", 0))
        if max_mb and total > max_mb * 1024 * 1024:
            print(f"  [SKIP] {total // (1024 * 1024)} MB exceeds {max_mb} MB limit")
            resp.close()
            return False

        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 512):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 5_000_000:
                    elapsed = time.time() - start
                    rate = downloaded / elapsed / (1024 * 1024) if elapsed else 0
                    print(f"\r        {downloaded // (1024 * 1024)}/{total // (1024 * 1024)}"
                          f" MB ({downloaded / total * 100:.0f}%) {rate:.1f} MB/s",
                          end="", flush=True)
        if total > 5_000_000:
            print()
        size = dest.stat().st_size
        print(f"  [OK] {size // 1024} KB in {time.time() - start:.1f}s")
        return size > 100

    except requests.exceptions.SSLError as e:
        print(f"  [FAIL] SSL: {str(e)[:200]}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"  [FAIL] Connection: {str(e)[:200]}")
        return False
    except requests.exceptions.Timeout:
        print(f"  [FAIL] Timeout after {TIMEOUT}s: {label}")
        return False
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {str(e)[:200]}")
        return False


# (key, url, relative path under data/, label, max_mb)
CORE_SOURCES = [
    ("usgs_water_2015",
     "https://www.sciencebase.gov/catalog/file/get/5af3311be4b0da30c1b245d8"
     "?f=__disk__eb%2F74%2Feb%2Feb74ebb41169c76aaf374990bd5a71cac82604c1",
     "usgs/usco2015.csv", "USGS county water use 2015", 0),
    ("npdes_part1",
     "https://echo.epa.gov/files/echodownloads/npdes_downloads.zip",
     "epa/npdes_downloads.zip", "EPA ICIS-NPDES permits+facilities (332 MB)", 0),
    ("npdes_dmr_fy2024",
     "https://echo.epa.gov/files/echodownloads/npdes_dmrs_fy2024.zip",
     "epa/npdes_dmrs_fy2024.zip", "EPA DMR pollutant loads FY2024 (612 MB)", 0),
    ("irs_soi_2022",
     "https://www.irs.gov/pub/irs-soi/22zpallagi.csv",
     "irs/soi_zip_2022.csv", "IRS SOI ZIP aggregates TY2022 (206 MB)", 0),
    ("bls_employed",
     "https://api.bls.gov/publicAPI/v2/timeseries/data/LNS12000000",
     "bls/total_employed.json", "BLS employment (LNS12000000)", 0),
    ("bls_labor_force",
     "https://api.bls.gov/publicAPI/v2/timeseries/data/LNS11000000",
     "bls/labor_force.json", "BLS labor force (LNS11000000)", 0),
    ("eia_total_energy",
     "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T01.01",
     "eia/total_energy_monthly.csv", "EIA total energy monthly CSV", 0),
    ("eia_gasoline_weekly",
     "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=WGFUPUS2&f=W",
     "eia/gasoline_weekly.csv", "EIA weekly gasoline product supplied", 0),
    ("epa_msw",
     "https://www.epa.gov/facts-and-figures-about-materials-waste-and-recycling/"
     "national-overview-facts-and-figures-materials",
     "epa/msw_national_overview.html", "EPA MSW national overview", 0),
    ("census_pep_counties_2024",
     "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/"
     "counties/totals/co-est2024-alldata.csv",
     "census/co-est2024-alldata.csv",
     "Census PEP county totals 2020-2024 (keyless comparison)", 0),
]

EXTENDED_SOURCES = [
    ("npdes_dmr_fy2023",
     "https://echo.epa.gov/files/echodownloads/npdes_dmrs_fy2023.zip",
     "epa/npdes_dmrs_fy2023.zip", "EPA DMR FY2023 (596 MB)", 0),
    ("npdes_part2",
     "https://echo.epa.gov/files/echodownloads/npdes_eff_downloads.zip",
     "epa/npdes_eff_downloads.zip", "EPA NPDES effluent part 2 (2.5 GB)", 3000),
    ("npdes_limits",
     "https://echo.epa.gov/files/echodownloads/npdes_limits.zip",
     "epa/npdes_limits.zip", "EPA NPDES permit limits (459 MB)", 0),
    ("npdes_outfalls",
     "https://echo.epa.gov/files/echodownloads/npdes_outfalls_layer.zip",
     "epa/npdes_outfalls.zip", "EPA NPDES outfalls layer (50 MB)", 0),
    ("echo_exporter",
     "https://echo.epa.gov/files/echodownloads/echo_exporter.zip",
     "epa/echo_exporter.zip", "ECHO Exporter all facilities (392 MB)", 0),
    ("epa_cwns_report",
     "https://www.epa.gov/cwns/clean-watersheds-needs-survey-cwns-2022-report-and-data",
     "epa/cwns_2022_report.html", "EPA CWNS 2022 report", 0),
    ("epa_cwns_past",
     "https://www.epa.gov/cwns/clean-watersheds-needs-survey-cwns-past-reports-and-data",
     "epa/cwns_past.html", "EPA CWNS past reports", 0),
    ("epa_msw_2018_pdf",
     "https://www.epa.gov/system/files/documents/2024-02/facts-and-figures-2018.pdf",
     "epa/facts-and-figures-2018.pdf", "EPA MSW facts and figures 2018 PDF", 0),
    ("cdc_natality",
     "https://data.cdc.gov/api/views/n8mc-b4w4/rows.csv?accessType=DOWNLOAD",
     "cdc/natality.csv", "CDC natality (data.cdc.gov)", 0),
    ("cdc_deaths",
     "https://data.cdc.gov/api/views/76vk-y2ir/rows.csv?accessType=DOWNLOAD",
     "cdc/deaths_data.csv", "CDC deaths (data.cdc.gov)", 0),
    ("cdc_hospital_utilization",
     "https://data.cdc.gov/api/views/g62h-syeh/rows.csv?accessType=DOWNLOAD",
     "cdc/hospital_data.csv", "CDC hospital utilization", 0),
    ("cdc_births_vsrr",
     "https://www.cdc.gov/nchs/data/vsrr/vsrr028-2024.pdf",
     "cdc/births_final.pdf", "CDC births final report VSRR", 0),
    ("cdc_deaths_vsrr",
     "https://www.cdc.gov/nchs/data/vsrr/vsrr029.pdf",
     "cdc/deaths_final.pdf", "CDC deaths final report VSRR", 0),
    ("cdc_hus_hospital",
     "https://www.cdc.gov/nchs/data/hus/2023/table086.pdf",
     "cdc/hospital_utilization_2023.pdf", "CDC NCHS hospital utilization table", 0),
    ("ahrq_hcup_2021",
     "https://hcup-us.ahrq.gov/reports/statbriefs/sb295-Hospital-Stays-2021.pdf",
     "ahrq/hcup_hospital_stays_2021.pdf", "AHRQ HCUP hospital stays 2021", 0),
    ("usda_snap_summary",
     "https://www.fns.usda.gov/sites/default/files/resource-files/SNAPsummary-10.xlsx",
     "usda/SNAPsummary.xlsx", "USDA FNS SNAP summary XLSX", 0),
    ("usda_snap_page",
     "https://www.fns.usda.gov/pd/supplemental-nutrition-assistance-program-snap",
     "usda/snap_page.html", "USDA FNS SNAP data page", 0),
    ("usda_food_availability",
     "https://www.ers.usda.gov/webdocs/DataFiles/48747/FoodAvailability.xls",
     "usda/FoodAvailability.xls", "USDA ERS food availability XLS", 0),
    ("census_retail_current",
     "https://www.census.gov/retail/marts/marts_current.xlsx",
     "census/retail_trade_current.xlsx", "Census retail trade current XLSX", 0),
    ("cms_medicare_county",
     "https://data.cms.gov/api/views/xubh-q36u/rows.csv?accessType=DOWNLOAD",
     "cms/medicare_by_county.csv", "CMS Medicare enrollment by county", 0),
    ("nces_digest_203_10",
     "https://nces.ed.gov/programs/digest/d23/tables/dt23_203.10.asp",
     "nces/digest_enrollment.html", "NCES digest enrollment 203.10", 0),
    ("dhs_yearbook_index",
     "https://ohss.dhs.gov/topics/immigration/yearbook/2023",
     "dhs/yearbook_2023_index.html", "DHS yearbook 2023 index", 0),
    ("dhs_yearbook_table01",
     "https://ohss.dhs.gov/sites/default/files/statistics/yearbook/2023/Table01.pdf",
     "dhs/yearbook_2023_table01.pdf", "DHS yearbook Table 1 (LPRs)", 0),
    ("cbp_encounters",
     "https://www.cbp.gov/newsroom/stats/southwest-land-border-encounters",
     "cbp/encounters.html", "CBP southwest land border encounters", 0),
    ("fhwa_vehicles_mv1",
     "https://www.fhwa.dot.gov/policyinformation/statistics/2022/pdf/mv1.pdf",
     "fhwa/mv1_2022.pdf", "FHWA vehicle registrations MV-1 2022", 0),
    ("fcc_subscriptions",
     "https://opendata.fcc.gov/api/views/53w8-7wzi/rows.csv?accessType=DOWNLOAD",
     "fcc/wireless_subscriptions.csv", "FCC wireless subscriptions CSV", 0),
    ("ctia_survey_page",
     "https://www.ctia.org/news/ctia-year-end-survey-results",
     "ctia/wireless_survey.html", "CTIA year-end survey page", 0),
    ("ms_buildings_readme",
     "https://raw.githubusercontent.com/microsoft/USBuildingFootprints/main/README.md",
     "buildings/ms_footprints_readme.md", "MS Building Footprints README", 0),
    ("worldpop_2020",
     "https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/USA/"
     "usa_ppp_2020_constrained.tif",
     "geospatial/worldpop_usa_2020.tif", "WorldPop USA 2020 constrained", 500),
    ("viirs_2022",
     "https://eogdata.mines.edu/nighttime_light/annual/v10/2022/"
     "vcmsl_v10_c202201_750m.tif",
     "geospatial/viirs_2022.tif", "NASA VIIRS nighttime lights 2022", 200),
]

# State GeoJSON archives (large). Source: MS USBuildingFootprints v2
# legacy blob storage; keys are state names as used in file names.
BUILDING_STATES = ["California", "Texas", "Florida", "NewYork", "Pennsylvania"]


def _run_manifest(manifest: list, include_buildings: bool = False) -> dict:
    results = {}
    for key, url, rel, label, max_mb in manifest:
        results[key] = _download(url, DATA / rel, label, max_mb)

    if include_buildings:
        for state in BUILDING_STATES:
            url = f"https://minedbuildings.z5.web.core.windows.net/legacy/usbuildings-v2/{state}.geojson.zip"
            results[f"bldg_{state}"] = _download(
                url, DATA / f"buildings/{state}.geojson.zip",
                f"MS building footprints {state}", 0)

    ok = sum(1 for v in results.values() if v)
    print(f"\n  {ok} OK, {len(results) - ok} FAILED out of {len(results)}")
    return results


def download_core() -> dict:
    """Fetch the files the estimation pipeline reads. ~1.2 GB total."""
    print("=" * 60)
    print("  CORE DATA (required by popest run)")
    print("=" * 60)
    return _run_manifest(CORE_SOURCES)


def download_all() -> dict:
    """Core plus the full PLAN.md tier 1-5 exploration catalog."""
    print("=" * 60)
    print("  FULL CATALOG (core + tiers 1-5, several GB)")
    print("=" * 60)
    results = _run_manifest(CORE_SOURCES)
    print()
    results.update(_run_manifest(EXTENDED_SOURCES, include_buildings=True))
    return results


if __name__ == "__main__":
    download_core()
