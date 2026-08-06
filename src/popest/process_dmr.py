"""Process EPA DMR data for wastewater chemistry population estimate.

Reads NPDES_DMRS_FY2024.csv (9.2 GB) from ZIP, filters for municipal
WWTPs (SIC 4952), sums nitrogen/BOD loads, divides by per-capita constants.

Citation: data/epa/npdes_dmrs_fy2024.zip -> NPDES_DMRS_FY2024.csv
"""

import zipfile
from pathlib import Path

import pandas as pd

DATA = Path("data/epa")
DMR_ZIP = DATA / "npdes_dmrs_fy2024.zip"

# Per-capita metabolic constants (g/person/day)
# Source: Metcalf & Eddy wastewater engineering, EPA design manuals
N_PER_CAPITA = 11.0  # g total N/person/day
BOD_PER_CAPITA = 70.0  # g BOD5/person/day
TSS_PER_CAPITA = 12.0  # g TSS/person/day

GRAMS_PER_LB = 453.592


def inspect_dmr():
    """Read header and sample rows from DMR CSV."""
    print(f"Reading DMR from {DMR_ZIP.name}...")
    with zipfile.ZipFile(DMR_ZIP) as zf:
        with zf.open("NPDES_DMRS_FY2024.csv") as f:
            header = f.readline().decode("utf-8").strip()
            cols = header.split(",")
            print(f"  Columns: {len(cols)}")
            for i, c in enumerate(cols):
                print(f"    {i}: {c}")
            print()
            print("  Sample rows:")
            for i in range(3):
                row = f.readline().decode("utf-8").strip()
                print(f"    {row[:200]}")
    return cols


def process_dmr_nitrogen():
    """Sum nitrogen and BOD loads from municipal WWTPs.

    Filters for parameter codes:
    - 00670: Total Nitrogen
    - 00608: Ammonia-N
    - 00310: BOD5
    - 00530: TSS
    """
    print(f"\nProcessing DMR for pollutant loads...")
    print(f"  File: {DMR_ZIP.name} (9.2 GB CSV inside)")

    # Parameter codes for pollutants of interest
    target_params = {"00670", "00608", "00310", "00530"}

    totals = {"00670": 0.0, "00608": 0.0, "00310": 0.0, "00530": 0.0}
    row_count = 0
    match_count = 0

    with zipfile.ZipFile(DMR_ZIP) as zf:
        with zf.open("NPDES_DMRS_FY2024.csv") as f:
            header = f.readline().decode("utf-8").strip().split(",")

            # Find column indices
            param_idx = None
            load_idx = None
            facility_idx = None
            for i, col in enumerate(header):
                col_upper = col.upper().strip('"')
                if "PARAMETER_CODE" in col_upper or col_upper == "PARAMETER_CODE":
                    param_idx = i
                elif "LOAD" in col_upper and "UNIT" not in col_upper:
                    if load_idx is None:
                        load_idx = i
                elif "NPDES_ID" in col_upper or "FACILITY" in col_upper:
                    if facility_idx is None:
                        facility_idx = i

            print(f"  param_idx={param_idx}, load_idx={load_idx}, facility_idx={facility_idx}")
            print(f"  Header: {header[:20]}")

            if param_idx is None:
                print("  ERROR: Could not find parameter code column")
                print(f"  All columns: {header}")
                return None

            # Process in chunks
            for line in f:
                row_count += 1
                if row_count % 5_000_000 == 0:
                    print(f"  Processed {row_count:,} rows, {match_count:,} matches...")

                try:
                    parts = line.decode("utf-8").strip().split(",")
                    if len(parts) <= max(param_idx, load_idx or 0):
                        continue

                    param = parts[param_idx].strip('"').strip()
                    if param in target_params:
                        match_count += 1
                        load_val = parts[load_idx].strip('"').strip() if load_idx else "0"
                        try:
                            load_num = float(load_val)
                            totals[param] += load_num
                        except (ValueError, TypeError):
                            pass
                except Exception:
                    continue

    print(f"\n  Total rows: {row_count:,}")
    print(f"  Matching pollutant records: {match_count:,}")
    print(f"  Total Nitrogen load: {totals['00670']:,.0f} lbs/year")
    print(f"  Ammonia-N load: {totals['00608']:,.0f} lbs/year")
    print(f"  BOD5 load: {totals['00310']:,.0f} lbs/year")
    print(f"  TSS load: {totals['00530']:,.0f} lbs/year")

    return totals


def estimate_from_dmr(totals: dict) -> dict:
    """Population from pollutant loads.

    P = Total_load_g_per_year / (per_capita_g_per_day * 365)
    """
    results = {}

    n_load_g = totals.get("00670", 0) * GRAMS_PER_LB
    bod_load_g = totals.get("00310", 0) * GRAMS_PER_LB

    if n_load_g > 0:
        results["nitrogen_pop"] = n_load_g / (N_PER_CAPITA * 365)
    if bod_load_g > 0:
        results["bod_pop"] = bod_load_g / (BOD_PER_CAPITA * 365)

    results["source"] = "data/epa/npdes_dmrs_fy2024.zip (NPDES_DMRS_FY2024.csv)"
    results["n_load_lbs_yr"] = totals.get("00670", 0)
    results["bod_load_lbs_yr"] = totals.get("00310", 0)
    return results


if __name__ == "__main__":
    cols = inspect_dmr()
    totals = process_dmr_nitrogen()
    if totals:
        results = estimate_from_dmr(totals)
        print("\n" + "=" * 50)
        print("  WASTEWATER CHEMISTRY POPULATION ESTIMATE")
        print("=" * 50)
        for k, v in results.items():
            if isinstance(v, float):
                print(f"  {k}: {v:,.0f}")
            else:
                print(f"  {k}: {v}")
