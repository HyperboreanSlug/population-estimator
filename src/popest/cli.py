"""CLI entry point for population estimator."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="popest",
        description="Multi-source US population estimation",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("water", help="Water budget method")
    sub.add_parser("wastewater", help="Wastewater flow method")
    sub.add_parser("energy", help="Energy consumption method")
    sub.add_parser("waste", help="Waste/food/vehicle methods")
    sub.add_parser("healthcare", help="Healthcare utilization method")
    sub.add_parser("housing", help="Housing unit method")
    sub.add_parser("vitals", help="Births/deaths vital statistics")
    sub.add_parser("buildings", help="Building footprints method")
    sub.add_parser("consumption", help="SNAP/wireless/grocery method")
    sub.add_parser("irs", help="IRS tax filer method")
    sub.add_parser("bls", help="BLS employment method")
    sub.add_parser("ensemble", help="Full ensemble (all methods)")
    sub.add_parser("sensitivity", help="Sensitivity analysis")
    sub.add_parser("download", help="Download all data sources")
    sub.add_parser("verify", help="Verify downloaded data")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    dispatch = {
        "water": _run_water,
        "wastewater": _run_wastewater,
        "energy": _run_energy,
        "waste": _run_waste,
        "healthcare": _run_healthcare,
        "housing": _run_housing,
        "vitals": _run_vitals,
        "buildings": _run_buildings,
        "consumption": _run_consumption,
        "irs": _run_irs,
        "bls": _run_bls,
        "ensemble": _run_ensemble,
        "sensitivity": _run_sensitivity,
        "download": _run_download,
        "verify": _run_verify,
    }
    dispatch[args.command]()


def _run_water():
    from popest.water import fetch_water_use_2015
    from popest.methods.water_budget import estimate, national_summary

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


def _run_wastewater():
    from popest.wastewater import download_npdes_part1, load_municipal_flows
    from popest.methods.wastewater import estimate, national_summary

    zip_path = download_npdes_part1()
    flow_df = load_municipal_flows(zip_path)
    result = estimate(flow_df)
    summary = national_summary(result)
    _print_header("WASTEWATER FLOW")
    print(f"  Counties:  {summary.get('counties', 0)}")
    print(f"  Central:   {summary.get('central', 0):>15,.0f}")
    print(f"  Range:     {summary.get('low', 0):,.0f} - {summary.get('high', 0):,.0f}")
    _save(result, "wastewater_flow.csv")
    return summary


def _run_energy():
    from popest.methods.energy import estimate, national_summary

    result = estimate()
    summary = national_summary(result)
    _print_header("ENERGY (ELECTRICITY)")
    print(f"  States:    {summary.get('states', 0)}")
    print(f"  Central:   {summary.get('central', 0):>15,.0f}")
    print(f"  Range:     {summary.get('low', 0):,.0f} - {summary.get('high', 0):,.0f}")
    _save(result, "energy_electricity.csv")
    return summary


def _run_waste():
    from popest.methods.waste_food import estimate, summary_table

    results = estimate()
    table = summary_table(results)
    _print_header("WASTE / FOOD / VEHICLES")
    for _, row in table.iterrows():
        print(f"  {row['method']:<12} {row['central']:>15,.0f}  "
              f"({row['low']:,.0f} - {row['high']:,.0f})")
    _save(table, "waste_food_vehicle.csv")
    return results


def _run_healthcare():
    from popest.methods.healthcare import estimate, summary_table

    results = estimate()
    table = summary_table(results)
    _print_header("HEALTHCARE UTILIZATION")
    for _, row in table.iterrows():
        print(f"  {row['method']:<12} {row['central']:>15,.0f}  "
              f"({row['low']:,.0f} - {row['high']:,.0f})")
    _save(table, "healthcare.csv")
    return results


def _run_housing():
    from popest.methods.housing import estimate, national_summary

    result = estimate()
    summary = national_summary(result)
    _print_header("HOUSING UNITS")
    print(f"  Counties:  {summary.get('counties', 0)}")
    print(f"  Central:   {summary.get('central', 0):>15,.0f}")
    print(f"  Range:     {summary.get('low', 0):,.0f} - {summary.get('high', 0):,.0f}")
    _save(result, "housing.csv")
    return summary


def _run_vitals():
    from popest.methods.vitals import estimate

    results = estimate()
    _print_header("VITAL STATISTICS (BIRTHS/DEATHS)")
    for key, val in sorted(results.items()):
        print(f"  {key:<20} {val:>15,.0f}")
    return results


def _run_buildings():
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


def _run_consumption():
    from popest.consumption import estimate_consumption

    results = estimate_consumption()
    _print_header("CONSUMPTION (SNAP/WIRELESS/GROCERY)")
    for key, val in sorted(results.items()):
        print(f"  {key:<20} {val:>15,.0f}")
    return results


def _run_irs():
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


def _run_bls():
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


def _run_download():
    from popest.download_comprehensive import download_remaining
    download_remaining()


def _run_verify():
    from popest.verify_downloads import verify_all
    verify_all()


def _run_ensemble():
    from popest.ensemble import combine_national
    from popest.discrepancy import discrepancy_report
    from popest.census import fetch_census_population_2020

    print("=" * 60)
    print("  FULL ENSEMBLE - ALL METHODS")
    print("=" * 60)

    estimates = {}

    print("\n[1/7] Water budget...")
    try:
        s = _run_water()
        estimates["water"] = s["central"]
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[2/7] Wastewater...")
    try:
        s = _run_wastewater()
        estimates["wastewater"] = s["central"]
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[3/7] Energy...")
    try:
        s = _run_energy()
        estimates["energy"] = s["central"]
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[4/7] Waste/vehicles...")
    try:
        r = _run_waste()
        estimates["msw"] = r.get("msw_central", 0)
        estimates["gasoline"] = r.get("gasoline_central", 0)
        estimates["vehicles"] = r.get("vehicles_central", 0)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[5/7] Healthcare...")
    try:
        r = _run_healthcare()
        estimates["healthcare"] = r.get("er_central", 0)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[6/7] Housing...")
    try:
        s = _run_housing()
        estimates["housing"] = s["central"]
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[7/11] Vitals...")
    try:
        r = _run_vitals()
        estimates["vitals"] = r.get("births_central", 0)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[8/11] Buildings...")
    try:
        s = _run_buildings()
        estimates["buildings"] = s["central"]
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[9/11] Consumption...")
    try:
        r = _run_consumption()
        estimates["snap"] = r.get("snap_central", 0)
        estimates["wireless"] = r.get("wireless_central", 0)
        estimates["grocery"] = r.get("grocery_central", 0)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[10/12] IRS...")
    try:
        r = _run_irs()
        estimates["irs"] = r.get("irs_central", 0)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[11/12] BLS...")
    try:
        r = _run_bls()
        estimates["bls"] = r.get("bls_central", 0)
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[12/12] Census (for comparison)...")
    census_pop = 0
    try:
        census_df = fetch_census_population_2020()
        census_pop = float(census_df["census_pop_2020"].sum())
        print(f"  Census 2020: {census_pop:,.0f}")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n" + "=" * 60)
    print("  ENSEMBLE RESULT")
    print("=" * 60)

    result = combine_national(estimates, census_pop)
    print(f"\n  Combined estimate: {result['combined']:>15,.0f}")
    if census_pop > 0:
        ratio = result["combined"] / census_pop
        print(f"  Census 2020:       {census_pop:>15,.0f}")
        print(f"  Ratio to census:    {ratio:.3f}")

    print(f"\n  Method contributions:")
    for m, info in sorted(result["contributions"].items(),
                          key=lambda x: -x[1]["value"]):
        print(f"    {m:<12} {info['value']:>15,.0f}  (w={info['weighted_share']:.2f})")

    if census_pop > 0:
        print(f"\n  DISCREPANCY REPORT:")
        disc = discrepancy_report(estimates, census_pop)
        for _, row in disc.iterrows():
            sign = "+" if row["pct_above_census"] >= 0 else ""
            print(f"    {row['method']:<12} {row['estimate']:>13,.0f}  "
                  f"{sign}{row['pct_above_census']:.1f}% vs census")
        _save(disc, "discrepancy_report.csv")

    return result


def _run_sensitivity():
    from popest.sensitivity import sensitivity_table

    table = sensitivity_table()
    _print_header("SENSITIVITY ANALYSIS")
    print(f"  {'Parameter':<28} {'Low':>8} {'Central':>8} {'High':>8}  {'Ratio':>6}")
    print(f"  {'-'*28} {'-'*8} {'-'*8} {'-'*8}  {'-'*6}")
    for _, row in table.iterrows():
        print(f"  {row['parameter']:<28} {row['low']:>8.1f} "
              f"{row['central']:>8.1f} {row['high']:>8.1f}  "
              f"{row['range_ratio']:>5.2f}x")
    print(f"\n  Higher ratio = more sensitive to assumption choice.")
    _save(table, "sensitivity.csv")


def _print_header(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def _save(df, filename: str):
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    path = out_dir / filename
    df.to_csv(path, index=False)
    print(f"  Saved: {path}")


if __name__ == "__main__":
    main()
