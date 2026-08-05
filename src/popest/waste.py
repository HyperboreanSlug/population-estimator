"""EPA waste and USDA food data client.

National-level data for MSW generation and food supply.
These are national totals used for cross-checking.
"""

from pathlib import Path

import pandas as pd

CACHE_DIR = Path("data/waste")


def msw_generation_national() -> dict:
    """EPA Municipal Solid Waste generation, national totals.

    Source: EPA "Advancing Sustainable Materials Management:
    Facts and Figures 2018" (latest comprehensive report).

    Returns dict with total generation in million tons/year.
    """
    return {
        "year": 2018,
        "total_million_tons": 292.4,
        "per_capita_lbs_day": 4.9,
        "source": "EPA Facts and Figures 2018",
    }


def food_availability_national() -> dict:
    """USDA ERS Food Availability (Per Capita) Data System.

    Total caloric availability for the US, national level.
    Source: USDA ERS, 2021 data (latest available).

    Returns dict with total daily calories available.
    """
    return {
        "year": 2021,
        "per_capita_kcal_day": 3315,
        "total_billion_kcal_day": None,
        "source": "USDA ERS Food Availability Data System",
        "note": "3315 kcal/capita/day is availability, not consumption. "
                "Includes food waste (~30-40%). Adjusted per-capita need ~2200.",
    }


def gasoline_consumption_national() -> dict:
    """EIA US gasoline consumption, national total.

    Source: EIA Petroleum Supply Monthly, 2023.
    Total US motor gasoline supplied: ~134 billion gallons/year.
    """
    return {
        "year": 2023,
        "total_billion_gal": 134.0,
        "per_capita_gal_year": 390.0,
        "source": "EIA Petroleum Supply Monthly 2023",
    }


def vehicle_registrations_national() -> dict:
    """FHWA vehicle registrations, national total.

    Source: FHWA Highway Statistics 2022.
    Total registered vehicles: ~283 million.
    """
    return {
        "year": 2022,
        "total_million_vehicles": 283.4,
        "vehicles_per_capita": 0.85,
        "source": "FHWA Highway Statistics 2022",
    }
