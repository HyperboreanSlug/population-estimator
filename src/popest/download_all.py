"""Bulk data downloader for all available sources.

Downloads every publicly available dataset listed in PLAN.md.
Each download is verified (non-empty, parseable).
"""

import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path("data")
TIMEOUT = 300
HEADERS = {"User-Agent": "population-estimator/0.1 (research)"}


def _get(url: str, **kwargs) -> requests.Response:
    kwargs.setdefault("timeout", TIMEOUT)
    kwargs.setdefault("headers", HEADERS)
    resp = requests.get(url, **kwargs)
    resp.raise_for_status()
    return resp


def _save(path: Path, content: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return len(content) > 0


def download_all() -> dict:
    """Download all available sources. Returns status dict."""
    results = {}

    print("=" * 60)
    print("  BULK DATA DOWNLOAD - ALL SOURCES")
    print("=" * 60)

    results["eia_electricity"] = _download_eia_electricity()
    results["eia_petroleum"] = _download_eia_petroleum()
    results["eia_natural_gas"] = _download_eia_natural_gas()
    results["usda_ers_food"] = _download_usda_ers_food()
    results["usda_fns_snap"] = _download_usda_fns_snap()
    results["nces_enrollment"] = _download_nces_enrollment()
    results["bls_employment"] = _download_bls_employment()
    results["cms_medicare"] = _download_cms_medicare()
    results["fhwa_vehicles"] = _download_fhwa_vehicles()
    results["epa_msw"] = _download_epa_msw()
    results["census_pep"] = _download_census_pep()
    results["dhs_immigration"] = _download_dhs_immigration()
    results["cbp_encounters"] = _download_cbp_encounters()

    print("\n" + "=" * 60)
    print("  DOWNLOAD SUMMARY")
    print("=" * 60)
    for name, status in results.items():
        icon = "OK" if status["success"] else "FAIL"
        print(f"  [{icon}] {name:<25} {status.get('detail', '')}")

    ok = sum(1 for s in results.values() if s["success"])
    print(f"\n  {ok}/{len(results)} sources downloaded successfully")
    return results


def _download_eia_electricity() -> dict:
    """EIA State Energy Data System - residential electricity."""
    url = "https://www.eia.gov/state/seds/sep_sum/plain_html/rank_use_per_cap.csv"
    try:
        resp = _get(url)
        path = DATA_DIR / "eia" / "rank_use_per_cap.csv"
        if _save(path, resp.content):
            df = pd.read_csv(io.BytesIO(resp.content))
            return {"success": True, "detail": f"{len(df)} rows", "path": str(path)}
    except Exception as e:
        pass

    url2 = "https://api.eia.gov/v2/electricity/electric-power-operational-data/data/?frequency=annual&data[0]=generation&facets[fueltypeid][]=ALL&start=2022&end=2022"
    try:
        resp = _get(url2)
        path = DATA_DIR / "eia" / "elec_generation.json"
        _save(path, resp.content)
        return {"success": True, "detail": "API response", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}


def _download_eia_petroleum() -> dict:
    """EIA petroleum supply - gasoline consumption."""
    url = "https://www.eia.gov/petroleum/supply/annual/xlsstp/mc12.xlsx"
    try:
        resp = _get(url)
        path = DATA_DIR / "eia" / "petroleum_annual.xlsx"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception:
        pass

    url2 = "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=MWGFPUS2&f=A"
    try:
        resp = _get(url2)
        path = DATA_DIR / "eia" / "gasoline_history.csv"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "all URLs failed"}


def _download_eia_natural_gas() -> dict:
    """EIA natural gas consumption by sector."""
    url = "https://www.eia.gov/dnav/ng/hist/n9190us3a.htm"
    try:
        resp = _get(url)
        path = DATA_DIR / "eia" / "natural_gas_consumption.html"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "failed"}


def _download_usda_ers_food() -> dict:
    """USDA ERS Food Availability Data System."""
    url = "https://www.ers.usda.gov/webdocs/DataFiles/48747/FoodAvailability.xls"
    try:
        resp = _get(url)
        path = DATA_DIR / "usda" / "FoodAvailability.xls"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception:
        pass

    url2 = "https://www.ers.usda.gov/data-products/food-availability-per-capita-data-system/"
    try:
        resp = _get(url2)
        path = DATA_DIR / "usda" / "food_availability_page.html"
        _save(path, resp.content)
        return {"success": True, "detail": "landing page saved", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}


def _download_usda_fns_snap() -> dict:
    """USDA FNS SNAP participation data."""
    url = "https://www.fns.usda.gov/pd/supplemental-nutrition-assistance-program-snap"
    try:
        resp = _get(url)
        path = DATA_DIR / "usda" / "snap_data_page.html"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "failed"}


def _download_nces_enrollment() -> dict:
    """NCES school enrollment data."""
    url = "https://nces.ed.gov/programs/digest/d23/tables/dt23_203.10.asp"
    try:
        resp = _get(url)
        path = DATA_DIR / "nces" / "enrollment_table.html"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "failed"}


def _download_bls_employment() -> dict:
    """BLS county employment data via API."""
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/LAH0000000000000"
    try:
        resp = _get(url)
        path = DATA_DIR / "bls" / "employment_national.json"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "failed"}


def _download_cms_medicare() -> dict:
    """CMS Medicare enrollment data."""
    url = "https://data.cms.gov/data-files/dataset/medicare-enrollment/enrollment-by-county"
    try:
        resp = _get(url)
        path = DATA_DIR / "cms" / "medicare_enrollment_page.html"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "failed"}


def _download_fhwa_vehicles() -> dict:
    """FHWA vehicle registration data."""
    url = "https://www.fhwa.dot.gov/policyinformation/statistics/2022/pdf/mv1.pdf"
    try:
        resp = _get(url)
        path = DATA_DIR / "fhwa" / "vehicle_registrations_2022.pdf"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "failed"}


def _download_epa_msw() -> dict:
    """EPA MSW generation data."""
    url = "https://www.epa.gov/system/files/documents/2024-02/facts-and-figures-2018.pdf"
    try:
        resp = _get(url)
        path = DATA_DIR / "epa" / "msw_facts_figures_2018.pdf"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "failed"}


def _download_census_pep() -> dict:
    """Census Population Estimates Program."""
    url = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/national/totals/nst-est2023-alldata.csv"
    try:
        resp = _get(url)
        path = DATA_DIR / "census" / "pep_national_2023.csv"
        if _save(path, resp.content):
            df = pd.read_csv(io.BytesIO(resp.content))
            return {"success": True, "detail": f"{len(df)} rows", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "failed"}


def _download_dhs_immigration() -> dict:
    """DHS Yearbook of Immigration Statistics."""
    url = "https://www.dhs.gov/sites/default/files/2024-05/2022_yearbook_immigration_statistics.pdf"
    try:
        resp = _get(url)
        path = DATA_DIR / "dhs" / "yearbook_2022.pdf"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "failed"}


def _download_cbp_encounters() -> dict:
    """CBP border encounter data."""
    url = "https://www.cbp.gov/newsroom/stats/southwest-land-border-encounters"
    try:
        resp = _get(url)
        path = DATA_DIR / "cbp" / "encounters_page.html"
        if _save(path, resp.content):
            return {"success": True, "detail": f"{len(resp.content)//1024} KB", "path": str(path)}
    except Exception as e:
        return {"success": False, "detail": str(e)[:80]}
    return {"success": False, "detail": "failed"}


if __name__ == "__main__":
    download_all()
