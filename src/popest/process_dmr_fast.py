"""Process EPA DMR data efficiently with pandas chunked reading.

Filters for nitrogen/BOD parameters from municipal WWTPs.
Citation: data/epa/npdes_dmrs_fy2024.zip -> NPDES_DMRS_FY2024.csv
"""

import io
import zipfile
from pathlib import Path

import pandas as pd

DATA = Path("data/epa")
DMR_ZIP = DATA / "npdes_dmrs_fy2024.zip"

# Target parameter codes
TARGET_PARAMS = {"00670", "00608", "00310", "00530"}
# 00670 = Total Nitrogen
# 00608 = Ammonia-N
# 00310 = BOD5
# 00530 = TSS

# Per-capita constants (g/person/day)
N_PER_CAPITA = 11.0
BOD_PER_CAPITA = 70.0
GRAMS_PER_LB = 453.592


def process_dmr():
    """Read DMR CSV in chunks, filter for target parameters."""
    print(f"Processing {DMR_ZIP.name}...")
    print(f"  Target parameters: {TARGET_PARAMS}")

    all_matches = []
    total_rows = 0

    with zipfile.ZipFile(DMR_ZIP) as zf:
        with zf.open("NPDES_DMRS_FY2024.csv") as f:
            # Read in chunks using pandas
            reader = pd.read_csv(
                f,
                dtype=str,
                chunksize=500_000,
                usecols=["EXTERNAL_PERMIT_NMBR", "PARAMETER_CODE",
                           "PARAMETER_DESC", "DMR_VALUE_NMBR",
                           "DMR_UNIT_CODE", "DMR_UNIT_DESC",
                           "DMR_VALUE_STANDARD_UNITS", "VALUE_TYPE_CODE",
                           "MONITORING_PERIOD_END_DATE"],
                low_memory=False,
            )

            for chunk in reader:
                total_rows += len(chunk)
                # Filter for target parameters
                mask = chunk["PARAMETER_CODE"].isin(TARGET_PARAMS)
                matches = chunk[mask]
                if len(matches) > 0:
                    all_matches.append(matches)
                if total_rows % 5_000_000 < 500_000:
                    print(f"  {total_rows:,} rows processed, "
                          f"{sum(len(m) for m in all_matches):,} matches...")

    print(f"\n  Total rows: {total_rows:,}")
    if not all_matches:
        print("  No matching records found!")
        return None

    df = pd.concat(all_matches, ignore_index=True)
    print(f"  Matching records: {len(df):,}")
    print(f"\n  Parameter breakdown:")
    print(df["PARAMETER_CODE"].value_counts().to_string())
    print(f"\n  Unit breakdown:")
    print(df["DMR_UNIT_DESC"].value_counts().head(10).to_string())
    print(f"\n  Value type breakdown:")
    print(df["VALUE_TYPE_CODE"].value_counts().to_string())

    # Save filtered data
    out_path = DATA / "dmr_nitrogen_bod_filtered.csv"
    df.to_csv(out_path, index=False)
    print(f"\n  Saved filtered data: {out_path} ({out_path.stat().st_size // 1024} KB)")

    return df


def estimate_population(df: pd.DataFrame) -> dict:
    """Estimate population from pollutant loads.

    DMR values in lbs/day or mg/L need different handling.
    Load (lbs/day) can be directly divided by per-capita contribution.
    Concentration (mg/L) needs flow multiplication.
    """
    results = {}

    # Check what units we have
    for param in TARGET_PARAMS:
        subset = df[df["PARAMETER_CODE"] == param].copy()
        if subset.empty:
            continue

        subset["value"] = pd.to_numeric(subset["DMR_VALUE_NMBR"], errors="coerce")
        subset = subset[subset["value"].notna() & (subset["value"] > 0)]

        if subset.empty:
            continue

        # Get the median value (robust to outliers)
        median_val = subset["value"].median()
        mean_val = subset["value"].mean()
        count = len(subset)

        param_name = subset["PARAMETER_DESC"].iloc[0] if len(subset) > 0 else param
        results[param] = {
            "name": param_name,
            "count": count,
            "median": median_val,
            "mean": mean_val,
            "units": subset["DMR_UNIT_DESC"].mode().iloc[0] if len(subset) > 0 else "unknown",
        }
        print(f"\n  {param} ({param_name}):")
        print(f"    Records: {count:,}")
        print(f"    Median: {median_val:.2f}, Mean: {mean_val:.2f}")
        print(f"    Units: {results[param]['units']}")

    return results


if __name__ == "__main__":
    df = process_dmr()
    if df is not None:
        print("\n" + "=" * 50)
        print("  PARAMETER ANALYSIS")
        print("=" * 50)
        results = estimate_population(df)
