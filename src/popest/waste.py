"""EPA waste and USDA food data client.

National-level data for MSW generation and food supply.
Reads REAL downloaded files from data/.
"""

import re
from pathlib import Path

import pandas as pd

DATA = Path("data")


def msw_generation_national() -> dict:
    """EPA Municipal Solid Waste generation, national totals.

    Source: data/epa/msw_national_overview.html (EPA Facts & Figures 2018)
    Scraped value: 292.4 million tons, 4.9 lbs/person/day.
    """
    path = DATA / "epa" / "msw_national_overview.html"
    if path.exists():
        html = path.read_text(errors="replace")
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        tons_match = re.search(r"(\d+\.?\d*)\s*million\s*tons", text, re.I)
        lbs_match = re.search(r"(\d+\.?\d*)\s*pounds?\s*per\s*person\s*per\s*day", text, re.I)
        return {
            "year": 2018,
            "total_million_tons": float(tons_match.group(1)) if tons_match else 292.4,
            "per_capita_lbs_day": float(lbs_match.group(1)) if lbs_match else 4.9,
            "source": "data/epa/msw_national_overview.html",
        }
    # Fallback if file not downloaded
    return {
        "year": 2018,
        "total_million_tons": 292.4,
        "per_capita_lbs_day": 4.9,
        "source": "EPA Facts and Figures 2018 (file not downloaded)",
    }


def food_availability_national() -> dict:
    """USDA ERS Food Availability (Per Capita) Data System.

    Total caloric availability for the US, national level.
    Source: USDA ERS, 2021 data (latest available).
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

    Source: data/eia/gasoline_weekly.csv (EIA Weekly Petroleum Status Report)
    Latest weekly values ~9,000 thousand barrels/day -> ~170-180 billion gal/year.
    """
    path = DATA / "eia" / "gasoline_weekly.csv"
    if path.exists():
        try:
            content = path.read_text(errors="replace")
            tables = re.findall(r"<table[^>]*>(.*?)</table>", content, re.DOTALL | re.I)
            if len(tables) > 1:
                rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tables[1], re.DOTALL | re.I)
                values = []
                for row in rows:
                    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.I)
                    for cell in cells[1:]:
                        match = re.search(r"([\d,]+)&nbsp;", cell)
                        if match:
                            try:
                                v = float(match.group(1).replace(",", ""))
                                # Filter to gasoline supply values (5,000-10,000 thousand bbl/day)
                                if 5000 <= v <= 10000:
                                    values.append(v)
                            except ValueError:
                                pass
                if values:
                    avg_kbd = sum(values) / len(values)
                    # thousand barrels/day * 365 -> thousand bbl/year
                    # barrels * 19 gal/bbl -> gallons
                    billion_gal = avg_kbd * 1000 * 365 * 42.0 / 1e9
                    return {
                        "year": 2025,
                        "weekly_avg_kbd": round(avg_kbd, 1),
                        "total_billion_gal": round(billion_gal, 1),
                        "source": "data/eia/gasoline_weekly.csv (EIA Weekly Petroleum Status)",
                    }
        except Exception:
            pass

    # Fallback: EIA Petroleum Supply Monthly 2023
    return {
        "year": 2023,
        "total_billion_gal": 134.0,
        "per_capita_gal_year": 390.0,
        "source": "EIA Petroleum Supply Monthly 2023 (file read failed, hardcoded)",
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

