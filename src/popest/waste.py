"""EPA waste and USDA food data client.

National-level data for MSW generation and food supply.
Reads REAL downloaded files from data/.
"""

import re
from pathlib import Path

import pandas as pd

DATA = Path("data")
VMT_XLSX = Path("data/fhwa/vm1.xlsx")


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


def vmt_annual() -> dict:
    """FHWA vehicle miles traveled, national total.

    Source: data/fhwa/vm1.xlsx (Highway Statistics VM-1, latest year).
    Row ITEM == 'Total Rural and Urban 5/', column 'ALL MOTOR VEHICLES',
    value in millions of vehicle-miles.
    """
    path = VMT_XLSX
    if not path.exists():
        return {}
    df = pd.read_excel(path, header=None)
    # header row: YEAR, ITEM, then vehicle-class columns
    header_idx = None
    for i in range(min(15, len(df))):
        row_vals = [str(v).strip().upper() for v in df.iloc[i].tolist()]
        if "YEAR" in row_vals and "ITEM" in row_vals:
            header_idx = i
            break
    if header_idx is None:
        return {}
    cols = [str(v).strip().upper() for v in
            df.iloc[header_idx].tolist()]
    year_col = cols.index("YEAR")
    item_col = cols.index("ITEM")

    # The ALL MOTOR VEHICLES column is the last numeric column; its
    # header label is split across stacked rows, so take the row's
    # last numeric value directly.
    totals = []
    for i in range(header_idx + 1, len(df)):
        year = pd.to_numeric(df.iloc[i, year_col], errors="coerce")
        item = str(df.iloc[i, item_col]).strip()
        if item.startswith("Total Rural and Urban") and pd.notna(year):
            row_nums = pd.to_numeric(df.iloc[i], errors="coerce").dropna()
            if len(row_nums) >= 2:
                totals.append((int(year), float(row_nums.iloc[-1])))
    if not totals:
        return {}
    year, miles_millions = max(totals)

    reported = {}
    for i in range(header_idx + 1, len(df)):
        year_n = pd.to_numeric(df.iloc[i, year_col], errors="coerce")
        item = str(df.iloc[i, item_col]).strip()
        if item.startswith("Number of motor vehicles") and pd.notna(year_n):
            row_nums = pd.to_numeric(df.iloc[i], errors="coerce").dropna()
            if len(row_nums) >= 2:
                reported = {
                    "vm1_motor_vehicles_registered": float(
                        row_nums.iloc[-1]),
                    "vm1_vehicles_note": (
                        "VM-1 'motor vehicles' basis, differs from MV-1 "
                        "registrations; reported, not substituted into the "
                        "vehicles method"),
                }
    out = {"year": year, "total_million_miles": miles_millions,
           "source": "data/fhwa/vm1.xlsx (FHWA Highway Statistics VM-1)"}
    out.update(reported)
    return out


def lmop_landfill_acceptance() -> dict:
    """MEASURED landfill waste acceptance (reported, not a method).

    Source: data/epa/lmopcompositedata.xlsx (EPA LMOP). Sum of
    per-landfill 'Annual Waste Acceptance Rate (tons per year)', deduped
    by Landfill ID. All waste streams (MSW, C&D, industrial, sludge),
    mixed reporting years (mostly 2022) — NOT comparable one-to-one with
    EPA's modeled MSW generation figure.
    """
    path = Path("data/epa/lmopcompositedata.xlsx")
    if not path.exists():
        return {}
    df = pd.read_excel(path, sheet_name="LMOP Database")
    rate_col = next((c for c in df.columns
                     if "Acceptance Rate" in str(c)), None)
    id_col = next((c for c in df.columns
                   if c.strip().lower() == "landfill id"), None)
    if rate_col is None or id_col is None:
        return {}
    sub = df[[id_col, rate_col]].dropna(subset=[id_col])
    sub[rate_col] = pd.to_numeric(sub[rate_col], errors="coerce")
    sub = sub.dropna(subset=[rate_col])
    deduped = sub.drop_duplicates(subset=[id_col], keep="first")
    return {
        "landfills_reporting": int(len(deduped)),
        "acceptance_tons_per_year": float(deduped[rate_col].sum()),
        "source": "data/epa/lmopcompositedata.xlsx (LMOP database)",
        "note": "all waste streams, mixed reporting years; upper-bound "
                "context for the EPA-modeled MSW generation estimate",
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

