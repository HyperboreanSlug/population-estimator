"""Method D: Waste and food population estimates.

National-level estimates from MSW generation, food supply,
gasoline consumption, and vehicle registrations.
"""

import pandas as pd

from popest.constants import (
    CALORIC_NEED,
    GASOLINE_USE,
    MSW_GENERATION,
    VEHICLES_PER_ADULT,
)
from popest.waste import (
    food_availability_national,
    gasoline_consumption_national,
    msw_generation_national,
    vehicle_registrations_national,
)


def estimate() -> dict:
    """Produce national population estimates from waste/food/energy proxies.

    Returns dict with estimates from each sub-method.
    """
    results = {}

    msw = msw_generation_national()
    total_lbs_year = msw["total_million_tons"] * 1e6 * 2000.0
    for label, pc in [("central", MSW_GENERATION.central),
                      ("low", MSW_GENERATION.high),
                      ("high", MSW_GENERATION.low)]:
        results[f"msw_{label}"] = total_lbs_year / (pc * 365.0)

    food = food_availability_national()
    if food["total_billion_kcal_day"]:
        for label, pc in [("central", CALORIC_NEED.central),
                          ("low", CALORIC_NEED.high),
                          ("high", CALORIC_NEED.low)]:
            results[f"food_{label}"] = (food["total_billion_kcal_day"] * 1e9) / pc

    gas = gasoline_consumption_national()
    total_gal = gas["total_billion_gal"] * 1e9
    for label, pc in [("central", GASOLINE_USE.central),
                      ("low", GASOLINE_USE.high),
                      ("high", GASOLINE_USE.low)]:
        results[f"gasoline_{label}"] = total_gal / pc

    veh = vehicle_registrations_national()
    total_vehicles = veh["total_million_vehicles"] * 1e6
    adult_share = 0.78
    for label, pc in [("central", VEHICLES_PER_ADULT.central),
                      ("low", VEHICLES_PER_ADULT.high),
                      ("high", VEHICLES_PER_ADULT.low)]:
        adults = total_vehicles / pc
        results[f"vehicles_{label}"] = adults / adult_share

    return results


def summary_table(results: dict) -> pd.DataFrame:
    """Format results as a readable table."""
    rows = []
    methods = set(k.rsplit("_", 1)[0] for k in results)
    for method in sorted(methods):
        row = {"method": method}
        for label in ["central", "low", "high"]:
            key = f"{method}_{label}"
            row[label] = results.get(key, 0)
        rows.append(row)
    return pd.DataFrame(rows)
