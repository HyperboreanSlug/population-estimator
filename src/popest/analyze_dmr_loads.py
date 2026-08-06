"""Analyze DMR load data and compute wastewater chemistry population."""

import pandas as pd
from pathlib import Path

DATA = Path("data/epa")

# Per-capita constants (g/person/day)
N_PER_CAPITA = 11.0
BOD_PER_CAPITA = 70.0
TSS_PER_CAPITA = 12.0
GRAMS_PER_LB = 453.592
GRAMS_PER_KG = 1000.0


def analyze_loads():
    df = pd.read_csv(DATA / "dmr_nitrogen_bod_filtered.csv", dtype=str)
    print(f"Total filtered records: {len(df):,}")

    # Filter for load units (mass/time, not concentration)
    load_units = {"lb/d", "kg/d", "lb/yr", "lb/mo", "lb/wk"}
    loads = df[df["DMR_UNIT_DESC"].isin(load_units)].copy()
    print(f"Load-based records (lb/d, kg/d, etc): {len(loads):,}")
    print()

    loads["value"] = pd.to_numeric(loads["DMR_VALUE_NMBR"], errors="coerce")
    loads = loads[loads["value"] > 0]

    print("Load records by parameter:")
    for param in sorted(loads["PARAMETER_CODE"].unique()):
        subset = loads[loads["PARAMETER_CODE"] == param]
        desc = subset["PARAMETER_DESC"].iloc[0]
        unit = subset["DMR_UNIT_DESC"].mode().iloc[0]
        total = subset["value"].sum()
        n_facilities = subset["EXTERNAL_PERMIT_NMBR"].nunique()
        print(f"  {param} ({desc})")
        print(f"    Records: {len(subset):,}, Facilities: {n_facilities:,}")
        print(f"    Sum: {total:,.1f} {unit}")
        print()

    # Compute population from BOD loads (lb/d)
    bod = loads[(loads["PARAMETER_CODE"] == "00310") & (loads["DMR_UNIT_DESC"] == "lb/d")]
    if not bod.empty:
        # Sum unique facility loads (take max per facility to avoid double-counting)
        bod_by_fac = bod.groupby("EXTERNAL_PERMIT_NMBR")["value"].max()
        total_bod_lb_d = bod_by_fac.sum()
        total_bod_g_d = total_bod_lb_d * GRAMS_PER_LB
        pop_bod = total_bod_g_d / BOD_PER_CAPITA
        print(f"BOD5 population estimate:")
        print(f"  Facilities reporting BOD lb/d: {len(bod_by_fac):,}")
        print(f"  Total BOD load: {total_bod_lb_d:,.0f} lb/d = {total_bod_g_d:,.0f} g/d")
        print(f"  Per-capita: {BOD_PER_CAPITA} g/person/day")
        print(f"  Population: {pop_bod:,.0f}")
        print(f"  Source: data/epa/dmr_nitrogen_bod_filtered.csv (from npdes_dmrs_fy2024.zip)")
        print()

    # TSS loads
    tss = loads[(loads["PARAMETER_CODE"] == "00530") & (loads["DMR_UNIT_DESC"] == "lb/d")]
    if not tss.empty:
        tss_by_fac = tss.groupby("EXTERNAL_PERMIT_NMBR")["value"].max()
        total_tss_lb_d = tss_by_fac.sum()
        total_tss_g_d = total_tss_lb_d * GRAMS_PER_LB
        pop_tss = total_tss_g_d / TSS_PER_CAPITA
        print(f"TSS population estimate:")
        print(f"  Facilities reporting TSS lb/d: {len(tss_by_fac):,}")
        print(f"  Total TSS load: {total_tss_lb_d:,.0f} lb/d = {total_tss_g_d:,.0f} g/d")
        print(f"  Per-capita: {TSS_PER_CAPITA} g/person/day")
        print(f"  Population: {pop_tss:,.0f}")
        print()

    # Also check concentration-based data for BOD
    # If we have BOD in mg/L, we can estimate load from typical flow
    bod_conc = df[(df["PARAMETER_CODE"] == "00310") & (df["DMR_UNIT_DESC"] == "mg/L")]
    if not bod_conc.empty:
        bod_conc_val = pd.to_numeric(bod_conc["DMR_VALUE_NMBR"], errors="coerce")
        bod_conc_val = bod_conc_val[(bod_conc_val > 0) & (bod_conc_val < 1000)]
        median_bod_mg_l = bod_conc_val.median()
        print(f"BOD5 concentration data:")
        print(f"  Records: {len(bod_conc_val):,}")
        print(f"  Median concentration: {median_bod_mg_l:.1f} mg/L")
        print(f"  (Typical raw sewage: 200-300 mg/L, treated effluent: 5-30 mg/L)")
        print()

    return {"bod_pop": pop_bod if not bod.empty else 0,
            "tss_pop": pop_tss if not tss.empty else 0}


if __name__ == "__main__":
    analyze_loads()
