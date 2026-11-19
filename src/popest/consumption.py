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
    """Census MARTS food and beverage store sales (NAICS 445).

    Source: data/census/adv44500.txt (not adjusted, millions of
    dollars). The latest COMPLETE calendar year is used. Falls back to
    the published 2023 literature figure when the file is absent.
    Note: NAICS 445 excludes food-at-home purchases at general
    merchandise stores; the per-capita constant matches this numerator.
    """
    path = Path("data/census/adv44500.txt")
    if path.exists():
        lines = path.read_text().splitlines()
        in_block = False
        years = []
        for l in lines:
            s = l.strip()
            if s == "FOOD & BEVERAGE STORES":
                in_block = True
                continue
            if in_block and s == "SEASONAL FACTORS":
                break
            if in_block and s[:4].isdigit():
                parts = s.split()
                try:
                    vals = [float(v) for v in parts[1:]]
                except ValueError:
                    continue
                years.append((int(parts[0]), vals))
        complete = [(y, sum(v)) for y, v in years if len(v) == 12]
        if complete:
            year, total_millions = max(complete)
            return {
                "year": year,
                "total_dollars": total_millions * 1e6,
                "source": "data/census/adv44500.txt (MARTS NAICS 445, "
                          "not adjusted, complete year)",
            }

    return {
        "year": 2023,
        "total_dollars": 950.0e9,
        "source": "Census Bureau Retail Trade 2023 (file not downloaded)",
    }


def food_expenditure() -> dict:
    """USDA ERS all-purchaser nominal food expenditure, latest year.

    Source: data/usda/food_expenditures.csv. Sums the six nominal
    purchaser columns (household/government/home-production at home;
    household/government/businesses away from home).
    """
    path = Path("data/usda/food_expenditures.csv")
    if not path.exists():
        return {}
    fe = pd.read_csv(path)
    nom = [c for c in fe.columns
           if "constant" not in c.lower() and c != "Year"]
    latest = fe.iloc[-1]
    total_millions = sum(pd.to_numeric(latest[c], errors="coerce")
                         for c in nom)
    if pd.isna(total_millions):
        return {}
    return {
        "year": int(latest["Year"]),
        "total_dollars": float(total_millions) * 1e6,
        "source": "data/usda/food_expenditures.csv "
                  "(ERS food expenditure series, all purchasers)",
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
    total_grocery = grocery["total_dollars"]
    for label, pc in [("central", 2950.0), ("low", 3450.0),
                      ("high", 2550.0)]:
        results[f"grocery_{label}"] = total_grocery / pc

    return results
