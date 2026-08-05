"""BLS employment data client.

Uses REAL downloaded data from data/bls/*.json (BLS public API).
Source: https://api.bls.gov/publicAPI/v2/timeseries/data/
"""

import json
from pathlib import Path

DATA_DIR = Path("data/bls")


def load_bls_data() -> dict:
    """Load BLS employment data from downloaded JSON files.

    Citation: data/bls/total_employed.json (series LNS12000000)
              data/bls/labor_force.json (series LNS11000000)
    """
    results = {}

    employed_file = DATA_DIR / "total_employed.json"
    if employed_file.exists():
        data = json.loads(employed_file.read_text())
        series = data.get("Results", {}).get("series", [])
        if series:
            pts = series[0].get("data", [])[:3]
            results["total_employed_thousands"] = [
                {"year": p["year"], "period": p["period"], "value": int(p["value"])}
                for p in pts
            ]

    labor_file = DATA_DIR / "labor_force.json"
    if labor_file.exists():
        data = json.loads(labor_file.read_text())
        series = data.get("Results", {}).get("series", [])
        if series:
            pts = series[0].get("data", [])[:3]
            results["labor_force_thousands"] = [
                {"year": p["year"], "period": p["period"], "value": int(p["value"])}
                for p in pts
            ]

    results["source"] = "data/bls/total_employed.json, data/bls/labor_force.json"
    results["api"] = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    return results


def estimate_from_bls() -> dict:
    """Population estimate from BLS employment data.

    P = Total_Employed / Employment_Rate
    Employment-population ratio ~59-60% (from downloaded BLS data).
    """
    bls = load_bls_data()
    if not bls.get("total_employed_thousands"):
        return {"error": "BLS data not downloaded"}

    employed_k = bls["total_employed_thousands"][0]["value"]
    employed = employed_k * 1000

    results = {}
    # APPROXIMATED: employment-population ratio range from BLS historical data
    for label, emp_rate in [("central", 0.595), ("low", 0.62), ("high", 0.57)]:
        results[f"bls_{label}"] = employed / emp_rate

    results["source"] = bls["source"]
    results["employed"] = employed
    results["disclaimer"] = (
        "APPROXIMATED: employment-population ratio (0.57-0.62) is an estimate. "
        "Employed count is real from BLS API."
    )
    return results
