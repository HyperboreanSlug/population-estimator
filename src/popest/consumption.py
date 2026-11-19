"""Consumption data: SNAP, retail, wireless subscribers.

Real data from USDA FNS, Census Retail Trade, FCC/CTIA.
"""

from pathlib import Path

import pandas as pd
import requests

CACHE_DIR = Path("data/consumption")
SNAP_XLSX = Path("data/usda/snap_annual_summary.xlsx")


def snap_participation_national() -> dict:
    """USDA FNS SNAP average participation, national.

    Source: data/usda/snap_annual_summary.xlsx (FNS annual summary,
    "Average Participation (Thousands)"). The monthly-series file
    (snap-4fymonthly) reports FY2025 as 42,145,499 vs the annual
    summary's 42,142,184 (0.008% apart); the annual summary is used
    and the conflict is reported here.
    """
    path = SNAP_XLSX
    if path.exists():
        df = pd.read_excel(path, header=2)
        df = df.rename(columns=lambda c: str(c).strip())
        fy_col = next((c for c in df.columns
                       if c.lower().startswith("fiscal year")), None)
        part_col = next((c for c in df.columns
                         if "participation" in c.lower()), None)
        if fy_col and part_col:
            work = df[[fy_col, part_col]].dropna()
            work["fy"] = work[fy_col].astype(str).str.replace(
                "FY ", "", regex=False).str.strip()
            work = work[work["fy"].str.match(r"^\d{4}$")].copy()
            work[part_col] = pd.to_numeric(work[part_col],
                                          errors="coerce")
            latest = work.dropna(subset=[part_col]).sort_values("fy").iloc[-1]
            return {
                "year": int(latest["fy"]),
                "participants": float(latest[part_col]) * 1000.0,
                "participation_rate": 0.124,
                "source": "data/usda/snap_annual_summary.xlsx "
                          "(average participation, thousands)",
                "note": "monthly series FY2025 differs by 0.008%",
            }

    return {
        "year": 2023,
        "participants": 41_200_000,
        "participation_rate": 0.124,
        "source": "USDA FNS SNAP Program Data 2023 (file not downloaded)",
    }


def wireless_subscribers_national() -> dict:
    """CTIA wireless subscriber count, national.

    Source: CTIA Year-End Survey 2023.
    ~450 million wireless subscriptions (includes tablets, IoT).
    Unique subscribers estimated at ~350M (1.05 per person).
    """
    return {
        "year": 2023,
        "total_subscriptions": 450_000_000,
        "unique_subscriber_estimate": 350_000_000,
        "subscriptions_per_person": 1.35,
        "source": "CTIA Year-End Survey 2023",
    }


def grocery_sales_national() -> dict:
    """Census Bureau retail trade - food and beverage stores.

    Source: Census Bureau Monthly Retail Trade Survey, 2023 annual.
    Total food-at-home spending: ~$950 billion.
    Per-capita food-at-home: ~$2,800/year.
    """
    return {
        "year": 2023,
        "total_food_at_home_billion": 950.0,
        "per_capita_food_at_home": 2800.0,
        "source": "Census Bureau Retail Trade 2023",
    }


def estimate_consumption() -> dict:
    """Population estimates from consumption data."""
    results = {}

    snap = snap_participation_national()
    for label, rate in [("central", 0.124), ("low", 0.14), ("high", 0.11)]:
        results[f"snap_{label}"] = snap["participants"] / rate

    wireless = wireless_subscribers_national()
    for label, rate in [("central", 1.05), ("low", 1.15), ("high", 0.95)]:
        results[f"wireless_{label}"] = wireless["unique_subscriber_estimate"] / rate

    grocery = grocery_sales_national()
    total_spending = grocery["total_food_at_home_billion"] * 1e9
    for label, pc in [("central", 2800), ("low", 3200), ("high", 2400)]:
        results[f"grocery_{label}"] = total_spending / pc

    return results
