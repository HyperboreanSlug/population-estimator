"""Retry failed downloads with corrected URLs."""

import io
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path("data")
TIMEOUT = 120
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) population-estimator/0.1"}


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


def retry_all():
    results = {}

    print("Retrying failed sources with corrected URLs...\n")

    # EIA electricity - use SEDS complete data file
    print("[1] EIA electricity (SEDS)...")
    try:
        r = _get("https://www.eia.gov/state/seds/seds-technical-notes-complete.php")
        _save(DATA_DIR / "eia" / "seds_notes.html", r.content)
        results["eia_electricity"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        try:
            r = _get("https://api.eia.gov/v2/energy-by-state/data/?frequency=annual&data[0]=value&facets[series][]=ELECB&start=2022&end=2022")
            _save(DATA_DIR / "eia" / "elec_by_state.json", r.content)
            results["eia_electricity"] = f"OK API {len(r.content)//1024}KB"
        except Exception as e2:
            results["eia_electricity"] = f"FAIL: {e2}"

    # EIA petroleum - monthly supply
    print("[2] EIA petroleum...")
    try:
        r = _get("https://www.eia.gov/petroleum/supply/monthly/xlsstp/mc12.xlsx")
        _save(DATA_DIR / "eia" / "petroleum_monthly.xlsx", r.content)
        results["eia_petroleum"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        try:
            r = _get("https://www.eia.gov/dnav/pet/pet_cons_pdst_dc_nus_epm0_pta_mbbl_a.htm")
            _save(DATA_DIR / "eia" / "petroleum_consumption.html", r.content)
            results["eia_petroleum"] = f"OK html {len(r.content)//1024}KB"
        except Exception as e2:
            results["eia_petroleum"] = f"FAIL: {e2}"

    # USDA ERS food availability
    print("[3] USDA ERS food...")
    try:
        r = _get("https://www.ers.usda.gov/data-products/food-availability-per-capita-data-system/")
        _save(DATA_DIR / "usda" / "food_availability_landing.html", r.content)
        results["usda_ers_food"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["usda_ers_food"] = f"FAIL: {e}"

    # USDA FNS SNAP
    print("[4] USDA FNS SNAP...")
    try:
        r = _get("https://www.fns.usda.gov/pd/supplemental-nutrition-assistance-program-snap")
        _save(DATA_DIR / "usda" / "snap_landing.html", r.content)
        results["usda_snap"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        try:
            r = _get("https://www.fns.usda.gov/sites/default/files/resource-files/SNAPsummary-10.xlsx")
            _save(DATA_DIR / "usda" / "snap_summary.xlsx", r.content)
            results["usda_snap"] = f"OK xlsx {len(r.content)//1024}KB"
        except Exception as e2:
            results["usda_snap"] = f"FAIL: {e2}"

    # EPA MSW
    print("[5] EPA MSW...")
    try:
        r = _get("https://www.epa.gov/facts-and-figures-about-materials-waste-and-recycling/national-overview-facts-and-figures-materials")
        _save(DATA_DIR / "epa" / "msw_overview.html", r.content)
        results["epa_msw"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["epa_msw"] = f"FAIL: {e}"

    # Census PEP
    print("[6] Census PEP...")
    try:
        r = _get("https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/national/totals/nst-est2024-alldata.csv")
        _save(DATA_DIR / "census" / "pep_national_2024.csv", r.content)
        results["census_pep"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        try:
            r = _get("https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/national/totals/nst-est2023-alldata.csv")
            _save(DATA_DIR / "census" / "pep_national_2023.csv", r.content)
            results["census_pep"] = f"OK 2023 {len(r.content)//1024}KB"
        except Exception as e2:
            results["census_pep"] = f"FAIL: {e2}"

    # DHS immigration
    print("[7] DHS immigration...")
    try:
        r = _get("https://www.dhs.gov/immigration-statistics/yearbook")
        _save(DATA_DIR / "dhs" / "yearbook_landing.html", r.content)
        results["dhs_immigration"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["dhs_immigration"] = f"FAIL: {e}"

    # BLS - verify non-empty
    print("[8] BLS employment (retry)...")
    try:
        r = _get("https://api.bls.gov/publicAPI/v2/timeseries/data/LNS12300000")
        _save(DATA_DIR / "bls" / "unemployment_national.json", r.content)
        results["bls_employment"] = f"OK {len(r.content)//1024}KB"
    except Exception as e:
        results["bls_employment"] = f"FAIL: {e}"

    print("\n" + "=" * 50)
    for k, v in results.items():
        print(f"  {k:<25} {v}")
    print("=" * 50)


if __name__ == "__main__":
    retry_all()
