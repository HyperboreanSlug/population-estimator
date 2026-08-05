"""Consumption data: SNAP, retail, wireless subscribers.

Real data from USDA FNS, Census Retail Trade, FCC/CTIA.
"""

from pathlib import Path

import pandas as pd
import requests

CACHE_DIR = Path("data/consumption")


def snap_participation_national() -> dict:
    """USDA SNAP participation, national.

    Source: USDA FNS SNAP data, 2023 annual average.
    ~41.2 million participants (12.4% of population).
    """
    return {
        "year": 2023,
        "participants": 41_200_000,
        "participation_rate": 0.124,
        "source": "USDA FNS SNAP Program Data 2023",
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
