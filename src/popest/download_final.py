"""Final retry: alternative URLs for blocked/failed sources."""

import io
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path("data")
TIMEOUT = 60
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _get(url, **kw):
    kw.setdefault("timeout", TIMEOUT)
    kw.setdefault("headers", HEADERS)
    r = requests.get(url, **kw)
    r.raise_for_status()
    return r


def _save(path: Path, content: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return len(content) > 100


def final_retry():
    results = {}

    # USDA via NASS Quick Stats API (different domain)
    print("[1] USDA NASS Quick Stats API...")
    try:
        r = _get("https://quickstats.nass.usda.gov/api/api_GET/?key=DEMO&commodity_desc=CORN&year=2022&statisticcat_desc=AREA+HARVESTED&agg_level_desc=NATIONAL&format=CSV")
        _save(DATA_DIR / "usda" / "nass_demo.csv", r.content)
        results["usda_nass"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["usda_nass"] = f"FAIL: {str(e)[:60]}"

    # USDA food data via data.usda.gov
    print("[2] data.usda.gov...")
    try:
        r = _get("https://data.usda.gov/api/catalog/search?q=food+availability")
        _save(DATA_DIR / "usda" / "data_usda_search.json", r.content)
        results["usda_data_portal"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["usda_data_portal"] = f"FAIL: {str(e)[:60]}"

    # Census PEP via API (no key needed for basic)
    print("[3] Census PEP via API...")
    try:
        r = _get("https://api.census.gov/data/2023/pep/population?get=NAME,POP&for=us:1")
        _save(DATA_DIR / "census" / "pep_api_response.json", r.content)
        results["census_pep_api"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["census_pep_api"] = f"FAIL: {str(e)[:60]}"

    # Census PEP direct file - try 2024 vintage
    print("[4] Census PEP direct file...")
    urls = [
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/national/totals/nst-est2024-alldata.csv",
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/national/totals/nst-est2024-allData.csv",
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/national/totals/nst-est2023-alldata.csv",
    ]
    for url in urls:
        try:
            r = _get(url)
            _save(DATA_DIR / "census" / "pep_national.csv", r.content)
            results["census_pep_file"] = f"OK {len(r.content)//1024}KB from {url.split('/')[-1]}"
            break
        except Exception:
            continue
    else:
        results["census_pep_file"] = "FAIL: all URLs 404"

    # EIA petroleum - try annual review
    print("[5] EIA petroleum annual...")
    urls = [
        "https://www.eia.gov/petroleum/annual/xlsstp/mc12.xlsx",
        "https://www.eia.gov/petroleum/supply/annual/xlsstp/mc12.xlsx",
        "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=MWGFPUS2&f=A",
    ]
    for url in urls:
        try:
            r = _get(url, timeout=90)
            ext = ".xlsx" if "xlsx" in url else ".csv"
            _save(DATA_DIR / "eia" / f"petroleum_annual{ext}", r.content)
            results["eia_petroleum"] = f"OK {len(r.content)//1024}KB"
            break
        except Exception:
            continue
    else:
        results["eia_petroleum"] = "FAIL: all URLs failed"

    # EPA Clean Watersheds Needs Survey
    print("[6] EPA Clean Watersheds Needs Survey...")
    try:
        r = _get("https://www.epa.gov/cwns/clean-watersheds-needs-survey-cwns")
        _save(DATA_DIR / "epa" / "cwns_landing.html", r.content)
        results["epa_cwns"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["epa_cwns"] = f"FAIL: {str(e)[:60]}"

    # CDC WONDER births - direct API
    print("[7] CDC WONDER births API...")
    try:
        r = _get("https://wonder.cdc.gov/controller/datarequest/D66", timeout=30)
        _save(DATA_DIR / "cdc" / "wonder_d66_page.html", r.content)
        results["cdc_wonder"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["cdc_wonder"] = f"FAIL: {str(e)[:60]}"

    # NCES enrollment - try direct data file
    print("[8] NCES enrollment data file...")
    try:
        r = _get("https://nces.ed.gov/ccd/Data/txt/nflc01a.txt")
        _save(DATA_DIR / "nces" / "enrollment_raw.txt", r.content)
        results["nces_data"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["nces_data"] = f"FAIL: {str(e)[:60]}"

    # CMS Medicare - try data.cms.gov API
    print("[9] CMS Medicare data API...")
    try:
        r = _get("https://data.cms.gov/data-files/api/dataset/medicare-enrollment")
        _save(DATA_DIR / "cms" / "medicare_api.json", r.content)
        results["cms_api"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["cms_api"] = f"FAIL: {str(e)[:60]}"

    print("\n" + "=" * 50)
    for k, v in results.items():
        print(f"  {k:<25} {v}")
    print("=" * 50)


if __name__ == "__main__":
    final_retry()
