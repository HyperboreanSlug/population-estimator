"""Phase 7: Sensitivity analysis on per-capita constants."""

import pandas as pd

from popest.constants import (
    ELECTRICITY_RESIDENTIAL,
    ER_VISIT_RATE,
    GASOLINE_USE,
    MSW_GENERATION,
    PHYSICIAN_VISIT_RATE,
    VEHICLES_PER_ADULT,
    WASTEWATER_FLOW,
    WATER_USE_PUBLIC_SUPPLY_TOTAL,
)


def sensitivity_table() -> pd.DataFrame:
    """Show how each per-capita constant affects the estimate.

    For each constant, shows the population estimate at low/central/high
    values, demonstrating which assumptions drive the result most.
    """
    rows = [
        {"parameter": "PS water use (gal/p/d)",
         "low": WATER_USE_PUBLIC_SUPPLY_TOTAL.low,
         "central": WATER_USE_PUBLIC_SUPPLY_TOTAL.central,
         "high": WATER_USE_PUBLIC_SUPPLY_TOTAL.high,
         "unit": "gal/person/day"},
        {"parameter": "Wastewater flow (gal/p/d)",
         "low": WASTEWATER_FLOW.low,
         "central": WASTEWATER_FLOW.central,
         "high": WASTEWATER_FLOW.high,
         "unit": "gal/person/day"},
        {"parameter": "Residential electricity",
         "low": ELECTRICITY_RESIDENTIAL.low,
         "central": ELECTRICITY_RESIDENTIAL.central,
         "high": ELECTRICITY_RESIDENTIAL.high,
         "unit": "kWh/person/year"},
        {"parameter": "MSW generation",
         "low": MSW_GENERATION.low,
         "central": MSW_GENERATION.central,
         "high": MSW_GENERATION.high,
         "unit": "lbs/person/day"},
        {"parameter": "Gasoline use",
         "low": GASOLINE_USE.low,
         "central": GASOLINE_USE.central,
         "high": GASOLINE_USE.high,
         "unit": "gal/person/year"},
        {"parameter": "Vehicles per adult",
         "low": VEHICLES_PER_ADULT.low,
         "central": VEHICLES_PER_ADULT.central,
         "high": VEHICLES_PER_ADULT.high,
         "unit": "vehicles/adult"},
        {"parameter": "ER visit rate",
         "low": ER_VISIT_RATE.low,
         "central": ER_VISIT_RATE.central,
         "high": ER_VISIT_RATE.high,
         "unit": "visits/person/year"},
        {"parameter": "Physician visit rate",
         "low": PHYSICIAN_VISIT_RATE.low,
         "central": PHYSICIAN_VISIT_RATE.central,
         "high": PHYSICIAN_VISIT_RATE.high,
         "unit": "visits/person/year"},
    ]
    df = pd.DataFrame(rows)
    df["range_ratio"] = df["high"] / df["low"]
    return df
