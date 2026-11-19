"""Single-method runners for the CLI.

Each runner executes one estimation method, prints a compact summary,
and saves its CSV under output/. Used by `popest <method>` subcommands.
"""

from pathlib import Path

import pandas as pd


def _print_header(title: str) -> None:
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


def _save(df: pd.DataFrame, filename: str) -> None:
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    path = out_dir / filename
    df.to_csv(path, index=False)
    print(f"  Saved: {path}")


def water() -> dict:
    from popest.methods.water_budget import estimate, national_summary
    from popest.water import fetch_water_use_2015

    print("Fetching USGS county water use data (2015)...")
    raw = fetch_water_use_2015()
    print(f"  Loaded {len(raw)} county records")
    result = estimate(raw)
    summary = national_summary(result)
    _print_header("WATER BUDGET (2015)")
    print(f"  Counties:  {summary['counties']}")
    print(f"  Central:   {summary['central']:>15,.0f}")
    print(f"  Range:     {summary['low_pop']:,.0f} - {summary['high_pop']:,.0f}")
    print(f"  USGS says: {summary['usgs_official']:>15,.0f}")
    _save(result, "water_budget_2015.csv")
    return summary


def wastewater() -> dict:
    from popest.methods.wastewater import estimate, national_summary
    from popest.wastewater import download_npdes_part1, load_municipal_flows

    flow_df = load_municipal_flows(download_npdes_part1())
    result = estimate(flow_df)
    summary = national_summary(result)
    _print_header("WASTEWATER FLOW")
    print(f"  Counties:  {summary.get('counties', 0)}")
    print(f"  Central:   {summary.get('central', 0):>15,.0f}")
    print(f"  Range:     {summary.get('low', 0):,.0f} - {summary.get('high', 0):,.0f}")
    _save(result, "wastewater_flow.csv")
    return summary


def chemistry() -> dict:
    from popest import dmr
    from popest.methods.wastewater_chemistry import estimate, national_summary

    loads = dmr.facility_loads(dmr.filter_dmr())
    cmap = dmr.facility_county_map()
    muni = dmr.municipal_permit_ids()
    result = estimate(loads, cmap, muni)
    summary = national_summary(result, loads, muni)
    _print_header("WASTEWATER CHEMISTRY (DMR LOADS)")
    print(f"  Counties:      {summary.get('counties', 0)}")
    for key in ("bod", "TSS", "Total N", "Ammonia-N"):
        pop = summary.get(f"{key}_pop")
        if pop:
            n = summary.get(f"{key}_facilities", 0)
            print(f"  {key + ' population':<16} {pop:>15,.0f}"
                  f"  ({n} facilities)")
    _save(result, "wastewater_chemistry.csv")
    return summary


def energy() -> dict:
    from popest.methods.energy import estimate, national_summary

    result = estimate()
    summary = national_summary(result)
    _print_header("ENERGY (ELECTRICITY)")
    print(f"  States:    {summary.get('states', 0)}")
    print(f"  Central:   {summary.get('central', 0):>15,.0f}")
    print(f"  Range:     {summary.get('low', 0):,.0f} - {summary.get('high', 0):,.0f}")
    _save(result, "energy_electricity.csv")
    return summary


def waste() -> dict:
    from popest.methods.waste_food import estimate, summary_table

    results = estimate()
    table = summary_table(results)
    _print_header("WASTE / FOOD / VEHICLES")
    for _, row in table.iterrows():
        print(f"  {row['method']:<12} {row['central']:>15,.0f}  "
              f"({row['low']:,.0f} - {row['high']:,.0f})")
    _save(table, "waste_food_vehicle.csv")
    return results


def healthcare() -> dict:
    from popest.methods.healthcare import estimate, summary_table

    results = estimate()
    table = summary_table(results)
    _print_header("HEALTHCARE UTILIZATION")
    for _, row in table.iterrows():
        print(f"  {row['method']:<12} {row['central']:>15,.0f}  "
              f"({row['low']:,.0f} - {row['high']:,.0f})")
    _save(table, "healthcare.csv")
    return results


def housing() -> dict:
    from popest.methods.housing import estimate, national_summary

    result = estimate()
    summary = national_summary(result)
    _print_header("HOUSING UNITS")
    print(f"  Counties:  {summary.get('counties', 0)}")
    print(f"  Central:   {summary.get('central', 0):>15,.0f}")
    print(f"  Range:     {summary.get('low', 0):,.0f} - {summary.get('high', 0):,.0f}")
    _save(result, "housing.csv")
    return summary


def vitals() -> dict:
    from popest.methods.vitals import estimate

    results = estimate()
    _print_header("VITAL STATISTICS (BIRTHS/DEATHS)")
    for key, val in sorted(results.items()):
        print(f"  {key:<20} {val:>15,.0f}")
    return results


def buildings() -> dict:
    from popest.methods.buildings import estimate, national_summary

    result = estimate()
    summary = national_summary(result)
    _print_header("BUILDING FOOTPRINTS")
    print(f"  States:    {summary.get('states', 0)}")
    print(f"  Buildings: {summary.get('total_buildings', 0):>15,}")
    print(f"  Central:   {summary.get('central', 0):>15,.0f}")
    print(f"  Range:     {summary.get('low', 0):,.0f} - {summary.get('high', 0):,.0f}")
    _save(result, "buildings.csv")
    return summary


def consumption() -> dict:
    from popest.consumption import estimate_consumption

    results = estimate_consumption()
    _print_header("CONSUMPTION (SNAP/WIRELESS/GROCERY)")
    for key, val in sorted(results.items()):
        print(f"  {key:<20} {val:>15,.0f}")
    return results


def irs() -> dict:
    from popest.irs import estimate_from_irs

    results = estimate_from_irs()
    _print_header("IRS TAX FILERS (REAL DATA)")
    if "error" in results:
        print(f"  ERROR: {results['error']}")
        return results
    print(f"  Raw exemptions (N2): {results['raw_exemptions']:>15,}")
    print(f"  Raw returns (N1):    {results['raw_returns']:>15,}")
    for key in ["irs_central", "irs_low", "irs_high"]:
        if key in results:
            print(f"  {key:<20} {results[key]:>15,.0f}")
    print(f"  Source: {results.get('source', 'N/A')}")
    return results


def bls() -> dict:
    from popest.bls import estimate_from_bls

    results = estimate_from_bls()
    _print_header("BLS EMPLOYMENT (REAL DATA)")
    if "error" in results:
        print(f"  ERROR: {results['error']}")
        return results
    print(f"  Total employed: {results['employed']:>15,}")
    for key in ["bls_central", "bls_low", "bls_high"]:
        if key in results:
            print(f"  {key:<20} {results[key]:>15,.0f}")
    print(f"  Source: {results.get('source', 'N/A')}")
    if results.get("disclaimer"):
        print(f"  {results['disclaimer']}")
    return results
